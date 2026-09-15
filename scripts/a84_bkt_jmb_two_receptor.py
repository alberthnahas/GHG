#!/usr/bin/env python3
"""Two-receptor (BKT + JMB) HYSPLIT-STILT campaign and joint methane inversion.

The joint window is the period where both Bukit Kototabang (BKT) and Jambi
(JMB) have valid hourly methane and every inversion input exists on its own
year: CarbonTracker-CH4 2025 boundary mole fractions (through 2023), LPJ-MERRA2
wetlands (through 2023) and GFS 0.25 degree ARL meteorology. That window is
24 November to 31 December 2023. December 2024 has more joint hours but no
CarbonTracker boundary, so it is documented in the window scan and not run.

Both receptors are released at 100 m above ground (tower inlet assumption
given by the user on 2026-09-14). Runs reuse the revised campaign settings:
120 h backward, 2000 particles, three seeds, wide 60 x 100 degree footprint
grid centred on each receptor, 1000 m extra concentration layer.

Stages
  select        joint receptor table and window scan (no network)
  fetch-met     NOAA READY wide crop of GFS 0.25 for 19 Nov to 31 Dec 2023
  fetch-inputs  CarbonTracker boundary and fluxes, LPJ 2023, EDGAR 2022
  prepare-flux  per-receptor monthly and fire prior fields
  run           HYSPLIT campaign (resumable; receipts per run)
  operator      per-receptor ensemble-mean operator tables
  inversion     single-site, joint, and cross-site fits
  summarize     footprint overlap and campaign ledger
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime, timezone
from functools import lru_cache
import json
from pathlib import Path
import shutil
import time
import zipfile

import numpy as np
import pandas as pd
import xarray as xr
from pyproj import Geod
from scipy.interpolate import RegularGridInterpolator

import a37_bkt_footprint as model
import a41_bkt_gfs as gfs
import a42_bkt_sources as src
import a71_domain_budget_extension as ext
import a74_bkt_simulation_revision as rev
import a75_bkt_revised_inversion as r75
import ghg_common as G
from a43_bkt_source_analysis import MW, save_nc
from a76_bkt_era5_driver import bind_interface
from bkt_arl import ARLReader
from bkt_methane_inverse import InverseProblem, chain_diagnostics, correlated_error

ROOT = model.ROOT
OUT = ROOT / "outputs/hysplit/two_receptor"
RUNS = OUT / "runs"
TABLES = OUT / "tables"
INPUTS = OUT / "inputs"
INVERSION = OUT / "inversion"
MET = ROOT / "data/hysplit/gfs0p25/two_receptor_wide"
SOURCES = ROOT / "data/bkt_sources"
HYSPLIT_HOME = rev.HYSPLIT_HOME
STATIONS = {  # code: (name, lat, lon, elevation m MSL)
    "BKT": ("Bukit Kototabang", -0.202, 100.318, 864.5),
    "JMB": ("Jambi", -1.611, 103.649, 25.0),
}
INLET_HEIGHT_M = 100.0
RECEPTOR_HOURS_UTC = (6, 18)
WINDOW = (pd.Timestamp("2023-11-24"), pd.Timestamp("2023-12-31T23:00"))
MET_DAYS = pd.date_range("2023-11-19", "2023-12-31", freq="D")
MONTHS = pd.to_datetime(["2023-11-01", "2023-12-01"])
CANDIDATE_WINDOWS = (("2023-11-24", "2023-12-31"), ("2023-12-01", "2023-12-31"),
                     ("2024-10-01", "2024-12-31"), ("2024-11-26", "2024-12-31"), ("2024-12-01", "2024-12-31"))
SEEDS = rev.SEEDS
PARTICLES = 2000
HOURS_BACK = rev.HOURS_BACK
EXTRA_LEVELS_M = rev.EXTRA_LEVELS_M
CT_BASE = "https://gml.noaa.gov/aftp/products/carbontracker/ch4/CT-CH4-2025"
HEMCO = "https://geos-chem.s3.amazonaws.com/HEMCO/CH4"
EDGAR_YEAR = 2022
LPJ_YEAR = 2023
COMPONENTS = ["anthro_near", "anthro_far", "wetlands", "fire"]
SECTOR_COMPONENTS = ["fuel_near", "other_near", "anthro_far", "wetlands", "fire"]
GEOD = Geod(ellps="WGS84")


# ------------------------------------------------------------------ selection

def station_frame(code: str) -> pd.DataFrame:
    frame = G.apply_flags(G.load_station(code)).set_index("time_utc").sort_index()
    if frame.index.duplicated().any():
        raise ValueError(f"Duplicate hours in {code}")
    return frame


def window_scan(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for start, end in CANDIDATE_WINDOWS:
        idx = pd.date_range(start, end + " 23:00", freq="h")
        idx = idx[idx.hour.isin(RECEPTOR_HOURS_UTC)]
        valid = {c: frames[c].ch4.reindex(idx).notna() & ~frames[c].suspect_ch4.reindex(idx).eq(True) for c in STATIONS}
        joint = valid["BKT"] & valid["JMB"]
        rows.append(dict(window_start=start, window_end=end, scheduled_hours=len(idx),
            bkt_valid=int(valid["BKT"].sum()), jmb_valid=int(valid["JMB"].sum()), joint_valid=int(joint.sum()),
            joint_percent=100 * joint.mean(),
            carbontracker_boundary=pd.Timestamp(end).year <= 2023, lpj_wetlands=pd.Timestamp(end).year <= 2023,
            gfs0p25_archive=True,
            selected=(start, end) == (f"{WINDOW[0]:%Y-%m-%d}", f"{WINDOW[1]:%Y-%m-%d}")))
    return pd.DataFrame(rows)


def select() -> pd.DataFrame:
    TABLES.mkdir(parents=True, exist_ok=True)
    frames = {c: station_frame(c) for c in STATIONS}
    window_scan(frames).to_csv(TABLES / "window_scan.csv", index=False)
    idx = pd.date_range(WINDOW[0], WINDOW[1], freq="h")
    idx = idx[idx.hour.isin(RECEPTOR_HOURS_UTC)]
    rows = []
    for code, frame in frames.items():
        sub = frame.reindex(idx)
        rows.append(pd.DataFrame(dict(time_utc=idx, station=code, ch4=sub.ch4.values, co=sub.co.values, co2=sub.co2.values,
            suspect_ch4=sub.suspect_ch4.eq(True).values,
            valid=(sub.ch4.notna() & ~sub.suspect_ch4.eq(True)).values)))
    table = pd.concat(rows, ignore_index=True)
    joint = table.groupby("time_utc").valid.all()
    table["joint"] = table.time_utc.map(joint)
    table["retained"] = table.joint
    # Complete-day holdout: every fourth joint day is withheld from fitting.
    days = sorted({t.normalize() for t in table.loc[table.retained, "time_utc"]})
    held = {d for i, d in enumerate(days) if i % 4 == 3}
    table["holdout"] = table.retained & table.time_utc.dt.normalize().isin(held)
    table.to_csv(TABLES / "receptor_selection.csv", index=False)
    summary = dict(window_start=WINDOW[0].isoformat(), window_end=WINDOW[1].isoformat(), scheduled_hours=len(idx),
        joint_hours=int(joint.sum()), holdout_hours=int((table.holdout & table.station.eq("BKT")).sum()),
        runs=int(joint.sum()) * len(STATIONS) * len(SEEDS), inlet_height_m_agl=INLET_HEIGHT_M,
        **{f"{c.lower()}_valid_hours": int(table.loc[table.station.eq(c), "valid"].sum()) for c in STATIONS})
    (TABLES / "selection_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)
    return table


def retained_stamps() -> list[pd.Timestamp]:
    table = pd.read_csv(TABLES / "receptor_selection.csv", parse_dates=["time_utc"])
    return sorted(set(table.loc[table.retained, "time_utc"]))


# ------------------------------------------------------------ acquisition

def fetch_met(interface: str | None = None) -> None:
    """NOAA READY server-side crop on the wide box used by the revised campaign."""
    if interface:
        bind_interface(interface)
    MET.mkdir(parents=True, exist_ok=True)
    gfs.regional_extract(dates=[f"{d:%Y-%m-%d}" for d in MET_DAYS], bounds=ext.WIDE_BOUNDS, directory=MET)
    missing = [d for d in MET_DAYS if not (MET / f"{d:%Y%m%d}_gfs0p25.json").exists()]
    if missing:
        raise FileNotFoundError(f"Meteorology incomplete: {missing}")


def fetch_url(url: str, path: Path, **extra) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.with_suffix(path.suffix + ".json").exists():
        return path
    model.download_file(url, path)
    src.provenance(path, url, **extra)
    return path


def edgar_year(year: int) -> None:
    """One EDGAR v8.0 monthly year per CH4 sector through HTTP range reads."""
    directory = SOURCES / "edgar_v8"
    page = (directory / "source_page.html").read_text()
    import re
    urls = sorted(set(re.findall(r'https://jeodpp[^"\s<>]+/monthly/CH4/[^"\s<>]+_flx_nc.zip', page)))
    if len(urls) != 8:
        raise ValueError(f"Expected 8 monthly CH4 sectors, found {len(urls)}")
    for url in urls:
        sector = url.rsplit("/", 1)[1].replace("_flx_nc.zip", "")
        target = directory / f"CH4_{sector}_{year}.nc"
        if target.exists() and target.with_suffix(".nc.json").exists():
            continue
        remote = src.RangeReader(url)
        with zipfile.ZipFile(remote) as archive:
            names = [n for n in archive.namelist() if f"_{year}_" in n and n.endswith(".nc")]
            if len(names) != 1:
                raise ValueError(f"Unexpected {year} members: {names}")
            info = archive.getinfo(names[0])
            target.write_bytes(archive.read(names[0]))
        src.provenance(target, url, provider="European Commission JRC / IEA-EDGAR", dataset="EDGAR v8.0 monthly fluxes",
                       gas="CH4", sector=sector, year=year, archive_member=names[0], archive_crc32=info.CRC,
                       archive_etag=remote.etag, archive_bytes=remote.size, transferred_bytes=remote.downloaded)
        print(f"Acquired {target.name}: {remote.downloaded/1e6:.1f} MB transferred", flush=True)


def fetch_inputs(interface: str | None = None, workers: int = 3) -> None:
    if interface:
        bind_interface(interface)
    days = pd.date_range(MET_DAYS[0], MET_DAYS[-1], freq="D")
    jobs = [(f"{CT_BASE}/molefractions/{d:%Y/%m}/CTCH4_2025.molefrac_glb3x2_{d:%Y-%m-%d}.nc",
             SOURCES / "inversion/carbontracker" / f"CTCH4_2025.molefrac_glb3x2_{d:%Y-%m-%d}.nc") for d in days]
    jobs.append((f"{CT_BASE}/fluxes/CTCH4_methane_emis_{LPJ_YEAR}.nc", SOURCES / "inversion/ctch4_fluxes" / f"CTCH4_methane_emis_{LPJ_YEAR}.nc"))
    jobs.append((f"{HEMCO}/v2025-09/LPJ_MERRA2/LPJ_MERRA2_{LPJ_YEAR}_0.5x0.5.nc", SOURCES / "inversion/wetlands" / f"LPJ_MERRA2_{LPJ_YEAR}_0.5x0.5.nc"))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for path in pool.map(lambda j: fetch_url(*j), jobs):
            print(path.name, flush=True)
    edgar_year(EDGAR_YEAR)


# --------------------------------------------------------------- priors

def receptor_grid(code: str) -> tuple[np.ndarray, np.ndarray]:
    cfg = base_config(code)
    return (model.grid_coordinates(cfg.receptor_lat, cfg.grid_span_lat_deg, cfg.grid_spacing_deg),
            model.grid_coordinates(cfg.receptor_lon, cfg.grid_span_lon_deg, cfg.grid_spacing_deg))


def monthly_inputs(target_lat: np.ndarray, target_lon: np.ndarray) -> xr.Dataset:
    """EDGAR (proxy year), LPJ wetlands (own year) and climatological natural sources."""
    sources = [(p, "fluxes", p.stem.removesuffix(f"_{EDGAR_YEAR}"))
               for p in sorted((SOURCES / "edgar_v8").glob(f"CH4_*_{EDGAR_YEAR}.nc"))]
    sources += [(SOURCES / "inversion" / folder / name, variable, label) for folder, name, variable, label in (
        ("wetlands", f"LPJ_MERRA2_{LPJ_YEAR}_0.5x0.5.nc", "emis_ch4", "wetlands"),
        ("soil", "MeMo_CH4uptake_Climatology.nc", "CH4uptake", "soil_uptake"),
        ("termites", "CAMS-GLOB-TERM_v1.1_methane_2000.nc", "CH4", "termites"),
        ("geological", "Etiope_CH4GeologicalEmis_ScaledToHmiel.1x1.nc", "emi_ch4", "geological"))]
    if len(sources) != 12:
        raise ValueError("Expected eight EDGAR plus four natural methane sources")
    fields, labels = [], []
    for path, variable, label in sources:
        if not path.with_suffix(path.suffix + ".json").exists():
            raise ValueError(f"Unverified source field: {path}")
        with xr.open_dataset(path) as ds:
            source = ds[variable].sortby("lat").sortby("lon")
            if source.attrs.get("units", "").replace(" ", "") not in ("kgm-2s-1", "kg/m2/s"):
                raise ValueError(f"Unexpected methane flux unit: {path}")
            values = []
            for month in MONTHS:
                selected = source.isel(time=0) if source.sizes["time"] == 1 else source.isel(time=month.month - 1)
                sub = selected.sel(lat=slice(target_lat[0] - .5, target_lat[-1] + .5),
                                   lon=slice(target_lon[0] - .5, target_lon[-1] + .5)).load()
                values.append(ext.remap_nonnegative(sub.values * 1e9 / MW["CH4"], sub.lat.values, sub.lon.values,
                                                    target_lat, target_lon))
            fields.append(values); labels.append(label)
    result = xr.Dataset({"flux": (("source", "month", "lat", "lon"), np.asarray(fields))},
                        coords={"source": labels, "month": MONTHS, "lat": target_lat, "lon": target_lon})
    result.flux.attrs["units"] = "umol m-2 s-1"
    result.attrs["edgar_year"] = f"EDGAR v8.0 {EDGAR_YEAR} monthly fluxes used as the anthropogenic prior for {MONTHS[0].year}"
    result.attrs["soil_sign"] = "soil_uptake is a positive magnitude and is subtracted only in net budgets"
    return result


def fire_inputs(target_lat: np.ndarray, target_lon: np.ndarray) -> xr.Dataset:
    """CarbonTracker-CH4 2025 pyrogenic posterior flux (1 degree, monthly) held constant within each month.

    GFED5.1 daily files end in December 2022, so the fire prior for late 2023 is
    the CarbonTracker pyrogenic category. No cropland partition is available;
    crop_fire_flux is zero and noncrop_fire_flux carries all fire methane.
    """
    path = SOURCES / "inversion/ctch4_fluxes" / f"CTCH4_methane_emis_{LPJ_YEAR}.nc"
    if not path.with_suffix(path.suffix + ".json").exists():
        raise FileNotFoundError(f"Run fetch-inputs first: {path}")
    with xr.open_dataset(path) as ds:
        if ds.pyrogenic.attrs.get("units") != "g m-2 year-1":
            raise ValueError("CarbonTracker pyrogenic flux unit differs from g m-2 year-1")
        pyro = ds.pyrogenic.rename(latitude="lat", longitude="lon").sortby("lat").sortby("lon").load()
    days = pd.date_range(MET_DAYS[0] - pd.Timedelta(days=HOURS_BACK // 24 + 1), MET_DAYS[-1], freq="D")
    all_fire = []
    for day in days:
        field = pyro.isel(time=day.month - 1)
        sub = field.sel(lat=slice(target_lat[0] - 1, target_lat[-1] + 1), lon=slice(target_lon[0] - 1, target_lon[-1] + 1))
        flux = np.clip(sub.values, 0, None) / (365.25 * 86400) * 1e6 / MW["CH4"]  # g m-2 yr-1 -> umol m-2 s-1
        all_fire.append(ext.remap_nonnegative(flux, sub.lat.values, sub.lon.values, target_lat, target_lon))
    result = xr.Dataset({"all_fire_flux": (("day", "lat", "lon"), np.asarray(all_fire)),
                         "crop_fire_flux": (("day", "lat", "lon"), np.zeros((len(days), len(target_lat), len(target_lon))))},
                        coords={"day": days, "lat": target_lat, "lon": target_lon})
    result["noncrop_fire_flux"] = result.all_fire_flux - result.crop_fire_flux
    for name in result.data_vars:
        result[name].attrs["units"] = "umol m-2 s-1"
    result.attrs["source"] = f"CarbonTracker-CH4 2025 pyrogenic monthly flux {LPJ_YEAR}; no cropland partition"
    return result


def prepare_flux() -> None:
    INPUTS.mkdir(parents=True, exist_ok=True)
    receipts = {}
    for code in STATIONS:
        lat, lon = receptor_grid(code)
        monthly, fire = monthly_inputs(lat, lon), fire_inputs(lat, lon)
        save_nc(monthly, INPUTS / f"{code.lower()}_monthly_flux.nc")
        save_nc(fire, INPUTS / f"{code.lower()}_daily_fire_flux.nc")
        receipts[code] = dict(monthly_sha256=ext.sha256(INPUTS / f"{code.lower()}_monthly_flux.nc"),
                              fire_sha256=ext.sha256(INPUTS / f"{code.lower()}_daily_fire_flux.nc"),
                              grid=dict(lat0=float(lat[0]), lat1=float(lat[-1]), lon0=float(lon[0]), lon1=float(lon[-1])))
        print(f"{code}: monthly sources {list(monthly.source.values)}; fire days {fire.sizes['day']}", flush=True)
    (INPUTS / "flux_receipt.json").write_text(json.dumps(receipts, indent=2) + "\n")


# ------------------------------------------------------------------ runs

def base_config(code: str, seed: int = 0) -> model.FootprintConfig:
    name, lat, lon, elevation = STATIONS[code]
    return model.FootprintConfig(meteorology_label=gfs.LABEL, receptor_lat=lat, receptor_lon=lon,
        station_elevation_m_msl=elevation, receptor_height_m_agl=INLET_HEIGHT_M, hours_back=HOURS_BACK,
        particles=PARTICLES, seed=seed, grid_spacing_deg=.25, grid_span_lat_deg=60, grid_span_lon_deg=100,
        particle_diagnostic_variables=0, save_endpoints=True)


def met_paths(stamp: pd.Timestamp) -> list[Path]:
    days = pd.date_range((stamp - pd.Timedelta(hours=HOURS_BACK)).normalize(), stamp.normalize(), freq="D")
    return [MET / f"{day:%Y%m%d}_gfs0p25" for day in days]


def run_dir(code: str, seed: int, stamp: pd.Timestamp) -> Path:
    # a37 names every run directory bkt_<stamp>; the parent directory carries the station.
    return RUNS / f"{code.lower()}_s{seed}" / f"bkt_{stamp:%Y%m%dT%H%MZ}"


def jobs() -> list[tuple[str, int, pd.Timestamp]]:
    return [(code, seed, stamp) for seed in SEEDS for stamp in retained_stamps() for code in STATIONS]


def observation_context(observations: dict[str, pd.DataFrame], code: str, stamp: pd.Timestamp) -> dict[str, object]:
    context: dict[str, object] = {"station": code, "station_name": STATIONS[code][0],
        "time_utc": stamp.isoformat() + "Z", "inlet_height_m_agl": INLET_HEIGHT_M,
        "purpose": "Two-receptor joint window; gas values do not select runs"}
    frame = observations[code]
    if stamp in frame.index:
        row = frame.loc[stamp]
        context.update({k: (None if pd.isna(row[k]) else float(row[k])) for k in ("co2", "ch4", "co")})
        context.update({k: bool(row[k]) for k in ("suspect_co2", "suspect_ch4", "suspect_co")})
    else:
        context.update({"co2": None, "ch4": None, "co": None})
    return context


def receipt(directory: Path, code: str, stamp: pd.Timestamp, cfg: model.FootprintConfig, runtime: float | None) -> dict:
    required = ("footprint.nc", "footprint_layers.nc", "PAR_GIS.txt", "MESSAGE", "CONTROL", "SETUP.CFG", "run_metadata.json")
    missing = [p for p in required if not (directory / p).is_file()]
    if missing:
        raise FileNotFoundError(f"Incomplete run {directory}: {missing}")
    meta = json.loads((directory / "run_metadata.json").read_text())
    if meta["configuration"] != asdict(cfg):
        raise ValueError(f"Configuration mismatch: {directory}")
    paths = met_paths(stamp)
    if meta["meteorology_files"] != [str(p.resolve()) for p in paths]:
        raise ValueError(f"Meteorology mismatch: {directory}")
    if (directory / "CONTROL").read_text() != model.control_text(stamp, paths, directory, cfg, EXTRA_LEVELS_M):
        raise ValueError(f"CONTROL does not encode the declared run: {directory}")
    message = (directory / "MESSAGE").read_text(errors="replace")
    actual = ext.actual_particles(message)
    if actual < cfg.particles:
        raise ValueError(f"Fewer particles emitted than requested: {directory}")
    return dict(station=code, receptor_utc=stamp.isoformat() + "Z", configuration=asdict(cfg),
        transport_options=asdict(model.TransportOptions()), extra_levels_m=list(EXTRA_LEVELS_M),
        meteorology_files=meta["meteorology_files"], actual_emitted_particles=actual,
        model_runtime_seconds=runtime if runtime is not None else meta.get("model_runtime_seconds"),
        hysplit_version_line=meta.get("hysplit_version_line"),
        output_sha256={p: model.sha256_file(directory / p) for p in required[:4]},
        created_at_utc=datetime.now(timezone.utc).isoformat())


def ensure_run(code: str, seed: int, stamp: pd.Timestamp, context: dict[str, object]) -> tuple[Path, float]:
    cfg = base_config(code, seed)
    directory = run_dir(code, seed, stamp)
    if (directory / "completion_receipt.json").exists():
        stored = json.loads((directory / "completion_receipt.json").read_text())
        if stored["configuration"] != asdict(cfg):
            raise ValueError(f"Existing receipt has different settings: {directory}")
        return directory, 0.0
    if directory.exists():
        shutil.rmtree(directory)
    started = time.monotonic()
    model.run_footprint(stamp, MET, directory.parent, HYSPLIT_HOME, cfg, False, meteorology_paths=met_paths(stamp),
        transport=model.TransportOptions(), observation_context=context, extra_levels_m=EXTRA_LEVELS_M)
    model.run_checked([str(HYSPLIT_HOME / "exec/par2asc"), "-iPARDUMP", "-oendpoints.txt", "-vendpoint_times.txt", "-a1"],
                      directory, "endpoints")
    (directory / "PARDUMP").unlink()
    elapsed = time.monotonic() - started
    (directory / "completion_receipt.json").write_text(json.dumps(receipt(directory, code, stamp, cfg, elapsed), indent=2) + "\n")
    return directory, elapsed


def run(workers: int, attempts: int = 2) -> None:
    import traceback
    if not (HYSPLIT_HOME / "exec/hycs_std").exists():
        raise FileNotFoundError(f"HYSPLIT not found at {HYSPLIT_HOME}")
    missing = [d for d in MET_DAYS if not (MET / f"{d:%Y%m%d}_gfs0p25.json").exists()]
    if missing:
        raise FileNotFoundError(f"Meteorology incomplete; run fetch-met first: {len(missing)} days")
    observations = {c: station_frame(c) for c in STATIONS}
    items = jobs()
    contexts = {(c, s): observation_context(observations, c, s) for c, _, s in items}
    started = time.monotonic()
    failures: dict[tuple, str] = {}
    for attempt in range(1, attempts + 1):
        pending = [j for j in items if not (run_dir(*j) / "completion_receipt.json").exists()]
        print(f"attempt {attempt}: {len(items)} runs declared, {len(pending)} pending, {workers} workers", flush=True)
        if not pending:
            break
        failures = {}
        done = 0
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(ensure_run, c, seed, s, contexts[(c, s)]): (c, seed, s) for c, seed, s in pending}
            for future in as_completed(futures):
                code, seed, stamp = futures[future]
                done += 1
                try:
                    _, elapsed = future.result()
                except Exception:  # noqa: BLE001 - logged and retried
                    failures[(code, seed, stamp)] = traceback.format_exc()
                    print(f"[{done}/{len(pending)}] FAILED {code} s{seed} {stamp:%Y-%m-%dT%HZ}\n{failures[(code, seed, stamp)]}", flush=True)
                    continue
                print(f"[{done}/{len(pending)}] {code} s{seed} {stamp:%Y-%m-%dT%HZ} {elapsed/60:.1f} min "
                      f"(campaign {(time.monotonic()-started)/3600:.2f} h)", flush=True)
    if failures:
        raise RuntimeError(f"{len(failures)} runs failed after {attempts} attempts")
    print("campaign complete", flush=True)


# -------------------------------------------------------------- operator

@lru_cache(maxsize=64)
def reader(path: str) -> ARLReader:
    return ARLReader(Path(path))


def endpoint_background(active: pd.DataFrame, stamp: pd.Timestamp, met_path: Path, height_shift: float = 0.) -> dict[str, float]:
    arl = reader(str(met_path.resolve()))
    terrain = arl.field(stamp, "SHGT", 0)
    ground = RegularGridInterpolator((arl.lat, arl.lon), terrain)(active[["latitude", "longitude"]].to_numpy())
    height = active.height.to_numpy(float) + ground + height_shift
    path = SOURCES / "inversion/carbontracker" / f"CTCH4_2025.molefrac_glb3x2_{stamp:%Y-%m-%d}.nc"
    provenance = path.with_suffix(path.suffix + ".json")
    if not provenance.exists() or model.sha256_file(path) != json.loads(provenance.read_text())["sha256"]:
        raise ValueError(f"Unverified CarbonTracker boundary: {path}")
    with xr.open_dataset(path) as data:
        if data.ch4.attrs.get("units") != "nanomole mole-1" or data.gph.attrs.get("units") != "meters":
            raise ValueError("CarbonTracker units differ from expected CH4/height convention")
        sample = data.sel(time=stamp)[["ch4", "gph"]].interp(
            latitude=xr.DataArray(active.latitude.to_numpy(), dims="particle"),
            longitude=xr.DataArray(active.longitude.to_numpy(), dims="particle")).load()
    bounds = sample.gph.transpose("particle", "boundary").values
    centers = (bounds[:, :-1] + bounds[:, 1:]) / 2
    values = sample.ch4.transpose("particle", "level").values
    if not np.isfinite(bounds).all() or not np.isfinite(values).all() or (np.diff(bounds, axis=1) <= 0).any():
        raise ValueError("Invalid CarbonTracker vertical support")
    methane = np.asarray([np.interp(z, h, c) for z, h, c in zip(height, centers, values)])
    return dict(background_ppb=float(methane.mean()), endpoint_background_sd_ppb=float(methane.std()),
                endpoint_below_lowest_midlevel_percent=float(100 * (height < centers[:, 0]).mean()))


def native_surface(code: str, met_path: Path, stamp: pd.Timestamp) -> dict[str, float]:
    arl = reader(str(met_path.resolve()))
    _, lat, lon, _ = STATIONS[code]
    return {name: arl.point(stamp, name, 0, lat, lon, "nearest") for name in ("PBLH", "SHGT", "U10M", "V10M", "T02M")}


def operator(allow_partial: bool = False, limit: int = 0) -> None:
    INVERSION.mkdir(parents=True, exist_ok=True)
    selection = pd.read_csv(TABLES / "receptor_selection.csv", parse_dates=["time_utc"])
    wanted = retained_stamps()
    if limit:
        wanted = wanted[:limit]
    rows, sectors, lag_rows, spatial = [], [], [], {}
    for code in STATIONS:
        with xr.open_dataset(INPUTS / f"{code.lower()}_monthly_flux.nc") as ds:
            monthly = ds.load()
        with xr.open_dataset(INPUTS / f"{code.lower()}_daily_fire_flux.nc") as ds:
            fire = ds.load()
        _, rlat, rlon, _ = STATIONS[code]
        lat, lon = np.meshgrid(monthly.lat.values, monthly.lon.values, indexing="ij")
        _, _, distance = GEOD.inv(np.full(lon.shape, rlon), np.full(lat.shape, rlat), lon, lat)
        distance /= 1000
        near, near50 = distance <= 500, distance <= 50
        receptor_cell = np.unravel_index(distance.argmin(), distance.shape)
        edge = np.zeros(near.shape, bool); edge[[0, -1], :] = True; edge[:, [0, -1]] = True
        maps_out, support = [], []
        for stamp in wanted:
            dirs = [run_dir(code, seed, stamp) for seed in SEEDS]
            dirs = [d for d in dirs if (d / "completion_receipt.json").exists()]
            if len(dirs) != len(SEEDS):
                if allow_partial and len(dirs) >= 2:
                    print(f"partial ensemble for {code} {stamp}: {len(dirs)} members", flush=True)
                elif allow_partial:
                    continue
                else:
                    raise FileNotFoundError(f"Ensemble incomplete for {code} {stamp}: {len(dirs)} of {len(SEEDS)}")
            member_rows, fields = [], []
            for directory in dirs:
                field, meta, actual = ext.read_footprint(directory)
                if not np.array_equal(field.lat.values, monthly.lat.values) or not np.array_equal(field.lon.values, monthly.lon.values):
                    raise ValueError(f"Footprint grid differs from the {code} flux grid")
                fields.append(field)
                active = ext.active_endpoints(directory, meta, actual)
                end = stamp - pd.Timedelta(hours=meta["configuration"]["hours_back"])
                met_end = MET / f"{end:%Y%m%d}_gfs0p25"
                background = endpoint_background(active, end, met_end)
                maps = r75.component_maps(field, monthly, fire)
                anthro = sum(v for k, v in maps.items() if k.startswith("CH4_"))
                member_rows.append(dict(seed=meta["configuration"]["seed"], emitted=actual, active=len(active),
                    anthro_near_ppb=anthro[near].sum(), anthro_far_ppb=anthro[~near].sum(),
                    anthro_within50_ppb=anthro[near50].sum(), anthro_50_500_ppb=anthro[near & ~near50].sum(),
                    anthro_receptor_cell_ppb=anthro[receptor_cell],
                    fuel_near_ppb=maps["CH4_FUEL_EXPLOITATION"][near].sum(),
                    other_near_ppb=(anthro - maps["CH4_FUEL_EXPLOITATION"])[near].sum(),
                    wetlands_ppb=maps["wetlands"].sum(), fire_ppb=maps["noncrop_fire"].sum(), crop_overlap_ppb=maps["crop_fire"].sum(),
                    termites_ppb=maps["termites"].sum(), geological_ppb=maps["geological"].sum(), soil_uptake_ppb=maps["soil_uptake"].sum(),
                    background_ppb=background["background_ppb"], endpoint_sd_ppb=background["endpoint_background_sd_ppb"],
                    endpoint_below_midlevel_percent=background["endpoint_below_lowest_midlevel_percent"],
                    sensitivity=float(field.sum())))
                for s in monthly.source.values:
                    sectors.append(dict(station=code, time_utc=stamp, seed=meta["configuration"]["seed"], source=str(s),
                                        prior_enhancement_ppb=float(maps[str(s)].sum())))
            members = pd.DataFrame(member_rows)
            mean = xr.concat(fields, dim="member").mean("member")
            maps = r75.component_maps(mean, monthly, fire)
            anthro = sum(v for k, v in maps.items() if k.startswith("CH4_"))
            agg = mean.sum("time").values; total = float(agg.sum())
            hourly = mean.sum(("lat", "lon")).values
            lag = (stamp - pd.DatetimeIndex(mean.time.values)).total_seconds() / 3600
            lag_rows += [dict(station=code, time_utc=stamp, lag_hours=h, sensitivity=w) for h, w in zip(lag, hourly)]
            numeric = [c for c in members.columns if c.endswith("_ppb") or c == "sensitivity"]
            row = dict(station=code, time_utc=stamp, members=len(members), **members[numeric].mean().to_dict())
            row.update({f"{c}_seed_sd": float(members[c].std(ddof=1)) for c in
                        ("anthro_near_ppb", "anthro_far_ppb", "wetlands_ppb", "fire_ppb", "background_ppb", "sensitivity")})
            retention = members.active / members.emitted
            row.update(endpoint_count=int(members.active.sum()), emitted_particles=int(members.emitted.sum()),
                endpoint_survival_fraction=float(retention.min()), transport_usable=bool((retention >= .95).all()),
                within500_sensitivity_percent=100 * agg[near].sum() / total, within50_sensitivity_percent=100 * agg[near50].sum() / total,
                receptor_cell_sensitivity_percent=100 * agg[receptor_cell] / total,
                oldest24h_sensitivity_percent=100 * hourly[lag > mean.sizes["time"] - 24].sum() / total,
                edge_sensitivity_percent=100 * agg[edge].sum() / total,
                **native_surface(code, MET / f"{stamp:%Y%m%d}_gfs0p25", stamp))
            rows.append(row)
            maps_out.append(np.stack([anthro * near, anthro * ~near, maps["wetlands"], maps["noncrop_fire"]])); support.append(agg)
            print(f"operator {code} {stamp}: near {row['anthro_near_ppb']:.1f} far {row['anthro_far_ppb']:.1f} "
                  f"wet {row['wetlands_ppb']:.1f} bg {row['background_ppb']:.1f} retention {retention.min():.3f}", flush=True)
        if maps_out:
            stamps = [r["time_utc"] for r in rows if r["station"] == code]
            ds = xr.Dataset({"prior_contribution": (("receptor", "component", "lat", "lon"), np.asarray(maps_out)),
                             "footprint": (("receptor", "lat", "lon"), np.asarray(support)),
                             "distance_km": (("lat", "lon"), distance)},
                            coords={"receptor": stamps, "component": COMPONENTS, "lat": monthly.lat.values, "lon": monthly.lon.values})
            ds.prior_contribution.attrs["units"] = "ppb"; ds.footprint.attrs["units"] = "ppm / (umol m-2 s-1)"
            save_nc(ds, INVERSION / f"spatial_operator_{code.lower()}.nc")
    if not rows:
        raise ValueError("No ensemble receptors available")
    frame = pd.DataFrame(rows).sort_values(["station", "time_utc"])
    frame = frame.merge(selection[["station", "time_utc", "ch4", "co", "co2", "holdout"]], on=["station", "time_utc"], validate="one_to_one")
    frame.to_csv(TABLES / "operator_base.csv", index=False)
    pd.DataFrame(sectors).to_csv(TABLES / "sector_responses_base.csv", index=False)
    pd.DataFrame(lag_rows).to_csv(TABLES / "lag_responses_base.csv", index=False)


# ------------------------------------------------------------- inversion

def design(frame: pd.DataFrame, components: list[str] = COMPONENTS) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    """Per-station offset and trend nuisance columns; the trend is per 28 days from the window midpoint."""
    codes = sorted(frame.station.unique())
    midpoint = WINDOW[0] + (WINDOW[1] - WINDOW[0]) / 2
    columns, names = [], []
    for code in codes:
        member = frame.station.eq(code).to_numpy().astype(float)
        columns += [member, member * (frame.time_utc - midpoint).dt.total_seconds().to_numpy() / (28 * 86400)]
        names += [f"offset_{code}", f"trend_{code}"]
    k = frame[[c + "_ppb" for c in components]].to_numpy()
    fixed = (frame.termites_ppb + frame.geological_ppb - frame.soil_uptake_ppb).to_numpy()
    base = frame.background_ppb.to_numpy() + fixed
    return k, np.column_stack(columns), base, names


def covariance(frame: pd.DataFrame, k: np.ndarray, transport: float) -> np.ndarray:
    """Block covariance: correlated errors within a station, independent between stations."""
    r = np.zeros((len(frame), len(frame)))
    for code in frame.station.unique():
        m = frame.station.eq(code).to_numpy()
        r[np.ix_(m, m)] = correlated_error(frame.time_utc[m], k[m].sum(axis=1), frame.time_utc[m].dt.hour.eq(18), transport_fraction=transport)
    r += np.diag((frame.termites_ppb + frame.geological_ppb + frame.soil_uptake_ppb).to_numpy() ** 2)
    return r


def fit(label: str, frame: pd.DataFrame, train: np.ndarray, evaluate: np.ndarray, transport: float | None = None,
        components: list[str] = COMPONENTS) -> dict:
    k, b, base, names = design(frame, components)
    y = frame.ch4.to_numpy() - base
    sd = np.r_[np.repeat(np.log(2.), k.shape[1]), np.tile([20., 10.], b.shape[1] // 2)]
    if transport is None:
        scan = []
        for t in (.05, .1, .15, .2, .25, .3, .4, .5, .6, .8, 1.0):
            p = InverseProblem(k[train], b[train], y[train], covariance(frame, k, t)[np.ix_(train, train)], sd)
            scan.append((t, r75.reduced_chi_square(p, int(train.sum()))))
        chi = np.array([c for _, c in scan]); ts = np.array([t for t, _ in scan])
        transport = float(ts[0] if chi.max() < 1 else ts[-1] if chi.min() > 1 else np.interp(1.0, chi[::-1], ts[::-1]))
    r = covariance(frame, k, transport)
    p = InverseProblem(k[train], b[train], y[train], r[np.ix_(train, train)], sd)
    center, _, _ = p.fit()
    chains, accept = p.sample()
    rh, ess = chain_diagnostics(chains)
    if np.max(rh) > 1.01 or np.min(ess) < 1000:
        raise RuntimeError(f"{label}: convergence inadequate Rhat={rh} ESS={ess}")
    samples = chains.reshape(-1, p.ndim); ns = k.shape[1]
    rows = []
    for j, name in enumerate(components + names):
        v = np.exp(samples[:, j]) if j < ns else samples[:, j]
        q = np.quantile(v, [.025, .5, .975])
        rows.append(dict(case=label, parameter=name, posterior_mean=v.mean(), q025=q[0], median=q[1], q975=q[2],
            probability_above_inventory=float((v > 1).mean()) if j < ns else np.nan,
            variance_reduction_percent=100 * (1 - np.var(samples[:, j]) / sd[j] ** 2), rhat=rh[j], ess=ess[j]))
    pred = base[None, :] + np.exp(samples[:, :ns]) @ k.T + samples[:, ns:] @ b.T
    median = np.quantile(pred, .5, axis=0)
    chi = r75.reduced_chi_square(p, int(train.sum()))
    evaluation = []
    for split, m in (("training", train), ("evaluation", evaluate)):
        for code in frame.station.unique():
            mm = m & frame.station.eq(code).to_numpy()
            if mm.sum() >= 3:
                evaluation.append(dict(case=label, split=split, station=code, transport_fraction=transport,
                    reduced_chi_square_training=chi, **r75.inv.metrics(frame.ch4[mm], median[mm])))
                # background-only comparison: fitted nuisance terms only, no source scaling
                bg = _background_only(frame, train, k, b, base, r)
                evaluation.append(dict(case=f"{label}_background_only", split=split, station=code, transport_fraction=transport,
                    reduced_chi_square_training=np.nan, **r75.inv.metrics(frame.ch4[mm], bg[mm])))
                prior = base + k.sum(axis=1)
                evaluation.append(dict(case=f"{label}_prior_inventory", split=split, station=code, transport_fraction=transport,
                    reduced_chi_square_training=np.nan, **r75.inv.metrics(frame.ch4[mm], prior[mm])))
    predictions = pd.DataFrame(dict(case=label, station=frame.station, time_utc=frame.time_utc, training=train, evaluation=evaluate,
        observed_ppb=frame.ch4, posterior_median_ppb=median, posterior_q025_ppb=np.quantile(pred, .025, axis=0),
        posterior_q975_ppb=np.quantile(pred, .975, axis=0), prior_inventory_ppb=base + k.sum(axis=1),
        background_ppb=frame.background_ppb, mismatch_sd_ppb=np.sqrt(np.diag(r))))
    return dict(parameters=rows, evaluation=evaluation, predictions=predictions, transport=transport)


def _background_only(frame, train, k, b, base, r):
    from scipy.linalg import solve_triangular
    target = frame.ch4.to_numpy() - base
    chol = np.linalg.cholesky(r[np.ix_(train, train)])
    bw = solve_triangular(chol, b[train], lower=True); yw = solve_triangular(chol, target[train], lower=True)
    prior = np.tile([1 / 20.**2, 1 / 10.**2], b.shape[1] // 2)
    beta = np.linalg.solve(bw.T @ bw + np.diag(prior), bw.T @ yw)
    return base + b @ beta


def inversion() -> None:
    frame = pd.read_csv(TABLES / "operator_base.csv", parse_dates=["time_utc"])
    excluded = frame[~frame.transport_usable]
    excluded.to_csv(TABLES / "transport_exclusions.csv", index=False)
    frame = frame[frame.transport_usable].reset_index(drop=True)
    holdout = frame.holdout.to_numpy(bool)
    bkt, jmb = frame.station.eq("BKT").to_numpy(), frame.station.eq("JMB").to_numpy()
    # Jambi 18 UTC (01 WIB) hours are calm lowland nights (10 m wind near zero, mixing depth
    # near zero in GFS); their enhancement is not represented by a 0.25 degree transport
    # model, so the screened cases exclude them from fitting and report them separately.
    jmb_night = jmb & frame.time_utc.dt.hour.eq(18).to_numpy()
    cases = [("joint", ~holdout, holdout, COMPONENTS),
             ("bkt_only", bkt & ~holdout, bkt & holdout, COMPONENTS),
             ("jmb_only", jmb & ~holdout, jmb & holdout, COMPONENTS),
             ("bkt_to_jmb", bkt & ~holdout, jmb, COMPONENTS),
             ("jmb_to_bkt", jmb & ~holdout, bkt, COMPONENTS),
             ("joint_screened", ~holdout & ~jmb_night, holdout & ~jmb_night, COMPONENTS),
             ("joint_screened_sector", ~holdout & ~jmb_night, holdout & ~jmb_night, SECTOR_COMPONENTS),
             ("jmb_day", jmb & ~jmb_night & ~holdout, jmb & ~jmb_night & holdout, COMPONENTS),
             ("bkt_to_jmb_day", bkt & ~holdout, jmb & ~jmb_night, COMPONENTS)]
    if not np.allclose(frame.fuel_near_ppb + frame.other_near_ppb, frame.anthro_near_ppb):
        raise ValueError("Fuel-exploitation split does not reconstruct the within-500 km component")
    results = []
    for label, train, evaluate, components in cases:
        if train.sum() < 12:
            print(f"skip {label}: {train.sum()} training hours", flush=True); continue
        # All rows are kept so cross-site predictions exist; the design carries per-station nuisance columns.
        results.append(fit(label, frame, train, evaluate, components=components))
        print(label, "transport fraction", results[-1]["transport"], flush=True)
    predictions = pd.concat([v["predictions"] for v in results])
    predictions["hour_utc"] = predictions.time_utc.dt.hour
    predictions["residual_ppb"] = predictions.observed_ppb - predictions.posterior_median_ppb
    predictions["observed_enhancement_ppb"] = predictions.observed_ppb - predictions.background_ppb
    predictions["prior_enhancement_ppb"] = predictions.prior_inventory_ppb - predictions.background_ppb
    by_hour = predictions.groupby(["case", "station", "hour_utc"]).agg(n=("residual_ppb", "size"),
        observed_enhancement_mean_ppb=("observed_enhancement_ppb", "mean"), observed_enhancement_sd_ppb=("observed_enhancement_ppb", "std"),
        prior_enhancement_mean_ppb=("prior_enhancement_ppb", "mean"), residual_mean_ppb=("residual_ppb", "mean"),
        residual_rmse_ppb=("residual_ppb", lambda r: float(np.sqrt(np.mean(r ** 2)))), mismatch_sd_ppb=("mismatch_sd_ppb", "mean")).reset_index()
    by_hour.to_csv(TABLES / "residual_by_hour.csv", index=False)
    predictions.to_csv(TABLES / "inversion_predictions.csv", index=False)
    pd.DataFrame([r for v in results for r in v["parameters"]]).to_csv(TABLES / "inversion_parameters.csv", index=False)
    pd.DataFrame([r for v in results for r in v["evaluation"]]).to_csv(TABLES / "inversion_evaluation.csv", index=False)
    print(pd.DataFrame([r for v in results for r in v["parameters"]]).to_string(index=False), flush=True)


# -------------------------------------------------------------- summary

def summarize() -> None:
    rows = []
    for code, seed, stamp in jobs():
        d = run_dir(code, seed, stamp)
        if (d / "completion_receipt.json").exists():
            rec = json.loads((d / "completion_receipt.json").read_text())
            rows.append(dict(station=code, seed=seed, time_utc=stamp, emitted=rec["actual_emitted_particles"],
                             runtime_min=(rec["model_runtime_seconds"] or np.nan) / 60, complete=True))
        else:
            rows.append(dict(station=code, seed=seed, time_utc=stamp, emitted=np.nan, runtime_min=np.nan, complete=False))
    ledger = pd.DataFrame(rows)
    ledger.to_csv(TABLES / "run_ledger.csv", index=False)
    print(ledger.groupby("station").complete.agg(completed="sum", declared="count"), flush=True)
    paths = {c: INVERSION / f"spatial_operator_{c.lower()}.nc" for c in STATIONS}
    if all(p.exists() for p in paths.values()):
        fields = {}
        for code, path in paths.items():
            with xr.open_dataset(path) as ds:
                fields[code] = ds.footprint.mean("receptor").load()
        common_lat = np.intersect1d(fields["BKT"].lat.values.round(4), fields["JMB"].lat.values.round(4))
        # Grids are offset by the receptor separation; compare on the coarser 1 degree box means.
        overlap = []
        for code, f in fields.items():
            coarse = f.coarsen(lat=4, lon=4, boundary="trim").sum()
            overlap.append(coarse.rename(f"footprint_{code.lower()}"))
        pd.DataFrame(dict(station=list(fields), total_mean_sensitivity=[float(f.sum()) for f in fields.values()],
                          common_lat_rows=len(common_lat))).to_csv(TABLES / "footprint_summary.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["select", "fetch-met", "fetch-inputs", "prepare-flux", "run", "operator", "inversion", "summarize", "all"])
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--interface", default=None, help="network device for downloads, e.g. wlp0s20f3")
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    stages = {"select": select, "fetch-met": lambda: fetch_met(args.interface), "fetch-inputs": lambda: fetch_inputs(args.interface),
              "prepare-flux": prepare_flux, "run": lambda: run(args.workers), "operator": lambda: operator(args.allow_partial, args.limit),
              "inversion": inversion, "summarize": summarize}
    if args.stage == "all":
        for name in ("select", "fetch-met", "fetch-inputs", "prepare-flux", "run", "operator", "inversion", "summarize"):
            stages[name]()
    else:
        stages[args.stage]()


if __name__ == "__main__":
    main()
