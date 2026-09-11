#!/usr/bin/env python3
"""Domain-completeness and prior-methane-budget extension for BKT.

This module deliberately has no inference stage.  It writes only beneath
``outputs/hysplit/domain_budget_extension`` (except for provider-provenanced
wide GFS/GFED inputs), keeps the original runs immutable, and makes the
original-versus-wide comparison explicit rather than treating recovered
particles as a normalization denominator.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, replace
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Iterable

import numpy as np
import pandas as pd
import xarray as xr
from scipy.interpolate import RegularGridInterpolator

import a37_bkt_footprint as model
import a41_bkt_gfs as gfs
import ghg_common as G
from a39_bkt_refinement import actual_particles
from a43_bkt_source_analysis import MW, matching_flux, save_nc
from bkt_arl import GFSReader
from bkt_footprint_spatial import cell_area_km2

ROOT = model.ROOT
OUT = ROOT / "outputs/hysplit/domain_budget_extension"
RUNS = OUT / "runs"
TABLES = OUT / "tables"
INPUTS = OUT / "inputs"
RECEIPTS = OUT / "receipts"
WIDE_MET = ROOT / "data/hysplit/gfs0p25/benchmark_wide"
ORIGINAL_MET = ROOT / "data/hysplit/gfs0p25/regional"
HYSPLIT_HOME = ROOT.parent / "AQ/tools/hysplit.v5.4.2_UbuntuOS20.04.6LTS"
WIDE_BOUNDS = (50.0, -40.0, 160.0, 30.0)
ORIGINAL_BOUNDS = (75.0, -20.0, 130.0, 20.0)
FULL_DATES = pd.date_range("2019-09-04", "2019-10-06", freq="D")
RECEPTOR_SELECTION = ROOT / "outputs/hysplit/inversion/receptor_selection.csv"
BASE_RUNS = ROOT / "outputs/hysplit/inversion/runs/base"
BENCHMARK_WIDE_120 = ROOT / "outputs/hysplit/benchmark/runs/loss_wide_output/bkt_20191006T0600Z"
REPRESENTATIVES = tuple(pd.to_datetime([
    "2019-09-13T06:00", "2019-09-14T18:00", "2019-09-23T06:00",
    "2019-09-24T18:00", "2019-10-06T06:00",
]))
DURATIONS = (72, 120, 168)
DOMAINS = ("original", "wide")
SEED = 20260909


def sha256(path: Path) -> str:
    return model.sha256_file(path)


@lru_cache(maxsize=96)
def cached_gfs_reader(path: str) -> GFSReader:
    """Cache immutable daily ARL indexes while keeping field reads on demand."""
    return GFSReader(Path(path))


def utc_stamp(value: object) -> pd.Timestamp:
    return model.parse_utc(str(value))


def target_grid(domain: str) -> tuple[np.ndarray, np.ndarray]:
    if domain == "original":
        return model.grid_coordinates(-0.202, 36, .25), model.grid_coordinates(100.318, 48, .25)
    if domain == "wide":
        return model.grid_coordinates(-0.202, 60, .25), model.grid_coordinates(100.318, 100, .25)
    raise ValueError(f"Unknown domain: {domain}")


def domain_met(domain: str) -> Path:
    if domain == "original":
        return ORIGINAL_MET
    if domain == "wide":
        return WIDE_MET
    raise ValueError(f"Unknown domain: {domain}")


def run_name(domain: str, hours: int, stamp: pd.Timestamp) -> Path:
    return RUNS / f"{domain}{hours}" / f"bkt_{stamp:%Y%m%dT%H%MZ}"


def complete_selection() -> pd.DataFrame:
    """Frozen 52-hour selection, loaded only through the harmonised loader."""
    scheduled = pd.read_csv(RECEPTOR_SELECTION, parse_dates=["time_utc"])
    fresh = G.apply_flags(G.load_station("BKT")).set_index("time_utc")
    frame = scheduled.loc[scheduled.retained].copy().set_index("time_utc")
    columns = ["co2", "ch4", "co", "time_local", "hour_local", "month", "suspect_co2", "suspect_ch4", "suspect_co"]
    joined = frame.join(fresh[columns], how="left", rsuffix="_loaded")
    for name in ("co2", "ch4", "co", "time_local", "hour_local", "month"):
        loaded = f"{name}_loaded"
        if loaded in joined:
            if joined[loaded].isna().any():
                raise ValueError(f"Harmonised BKT observation missing after selection: {name}")
            joined[name] = joined[loaded]
    joined = joined.reset_index().sort_values("time_utc").reset_index(drop=True)
    if len(joined) != 52 or joined.time_utc.duplicated().any():
        raise ValueError("Frozen full ensemble is not exactly 52 unique retained receptors")
    if joined[["co2", "ch4", "co"]].isna().any().any():
        raise ValueError("Selected observations must have all three harmonised gases")
    return joined


def run_config(hours: int, domain: str) -> model.FootprintConfig:
    lat_span, lon_span = (36, 48) if domain == "original" else (60, 100)
    return model.FootprintConfig(meteorology_label=gfs.LABEL, particles=500,
        hours_back=hours, grid_spacing_deg=.25, grid_span_lat_deg=lat_span,
        grid_span_lon_deg=lon_span, particle_diagnostic_variables=0, save_endpoints=True)


def met_paths(stamp: pd.Timestamp, hours: int, domain: str) -> list[Path]:
    return [domain_met(domain) / f"{day:%Y%m%d}_gfs0p25" for day in pd.date_range(
        (stamp - pd.Timedelta(hours=hours)).normalize(), stamp.normalize(), freq="D")]


def run_receipt(directory: Path, cfg: model.FootprintConfig, opts: model.TransportOptions,
                paths: list[Path], stamp: pd.Timestamp, *, reused: bool = False) -> dict:
    required = ("footprint.nc", "PAR_GIS.txt", "MESSAGE", "SETUP.CFG", "CONTROL", "run_metadata.json")
    missing = [p for p in required if not (directory / p).is_file()]
    if missing:
        raise FileNotFoundError(f"Incomplete model run {directory}: {missing}")
    meta = json.loads((directory / "run_metadata.json").read_text())
    actual = actual_particles((directory / "MESSAGE").read_text())
    if meta["configuration"] != asdict(cfg):
        raise ValueError(f"Configuration mismatch: {directory}")
    if utc_stamp(meta["observation"]["time_utc"]) != utc_stamp(stamp):
        raise ValueError(f"Receptor timestamp mismatch: {directory}")
    expected_paths = [str(path.resolve()) for path in paths]
    actual_paths = [str(Path(path).resolve()) for path in meta.get("meteorology_files", [])]
    if actual_paths != expected_paths:
        raise ValueError(f"Meteorology-file identity mismatch: {directory}")
    actual_options = meta.get("transport_options", asdict(opts))
    if not reused and actual_options != asdict(opts):
        raise ValueError(f"Transport-option mismatch: {directory}")
    try:
        recorded_options = model.TransportOptions(**actual_options)
    except TypeError as error:
        raise ValueError(f"Invalid recorded transport options: {directory}") from error
    if (directory / "SETUP.CFG").read_text() != model.setup_text(cfg, recorded_options):
        raise ValueError(f"SETUP.CFG does not encode recorded options: {directory}")
    if (directory / "CONTROL").read_text() != model.control_text(utc_stamp(stamp), paths, directory, cfg):
        raise ValueError(f"CONTROL does not encode expected receptor and forcing: {directory}")
    record = dict(created_at_utc=datetime.now(timezone.utc).isoformat(), reused_external_run=reused,
        source_run=str(directory.resolve()), configuration=asdict(cfg), transport_options=actual_options,
        meteorology_files=expected_paths, actual_emitted_particles=actual,
        output_sha256={name: sha256(directory / name) for name in required[:-1]})
    return record


def resolve_existing(domain: str, hours: int, stamp: pd.Timestamp) -> Path | None:
    if domain == "original" and hours == 120:
        path = BASE_RUNS / f"bkt_{stamp:%Y%m%dT%H%MZ}"
        return path if (path / "run_metadata.json").exists() else None
    if domain == "wide" and hours == 120 and stamp == pd.Timestamp("2019-10-06T06:00"):
        return BENCHMARK_WIDE_120 if (BENCHMARK_WIDE_120 / "run_metadata.json").exists() else None
    return None


def completed_run(domain: str, hours: int, stamp: pd.Timestamp) -> Path:
    """Resolve an already-completed scenario; analysis must never launch a model."""
    cfg, opts, paths = run_config(hours, domain), model.TransportOptions(), met_paths(stamp, hours, domain)
    external = resolve_existing(domain, hours, stamp)
    if external is not None:
        run_receipt(external, cfg, opts, paths, stamp, reused=True)
        return external
    target = run_name(domain, hours, stamp)
    if (target / "completion_receipt.json").exists():
        current = run_receipt(target, cfg, opts, paths, stamp)
        stored = json.loads((target / "completion_receipt.json").read_text())
        for key in ("source_run", "configuration", "transport_options", "meteorology_files",
                    "actual_emitted_particles", "output_sha256"):
            if stored.get(key) != current[key]:
                raise ValueError(f"Completion receipt mismatch for {key}: {target}")
        return target
    raise FileNotFoundError(f"Required completed scenario is absent: {target}")


def ensure_run(domain: str, hours: int, stamp: pd.Timestamp) -> Path:
    """Run one immutable scenario, or return a verified frozen predecessor."""
    cfg, opts = run_config(hours, domain), model.TransportOptions()
    target = run_name(domain, hours, stamp)
    paths = met_paths(stamp, hours, domain)
    existing = resolve_existing(domain, hours, stamp)
    if existing is not None:
        receipt = run_receipt(existing, cfg, opts, paths, stamp, reused=True)
        RECEIPTS.mkdir(parents=True, exist_ok=True)
        (RECEIPTS / f"{domain}{hours}_{stamp:%Y%m%dT%H%MZ}.json").write_text(json.dumps(receipt, indent=2) + "\n")
        return existing
    if (target / "completion_receipt.json").exists():
        current = run_receipt(target, cfg, opts, paths, stamp)
        receipt = json.loads((target / "completion_receipt.json").read_text())
        for key in ("source_run", "configuration", "transport_options", "meteorology_files",
                    "actual_emitted_particles", "output_sha256"):
            if receipt.get(key) != current[key]:
                raise ValueError(f"Completion receipt mismatch for {key}: {target}")
        return target
    if (target / "run_metadata.json").exists():
        # A completed HYSPLIT/footprint conversion interrupted only before the
        # endpoint text conversion is safely resumable.  Anything earlier is
        # retained for diagnosis instead of being overwritten.
        meta = json.loads((target / "run_metadata.json").read_text())
        if meta.get("configuration") != asdict(cfg) or meta.get("meteorology_files") != [str(p.resolve()) for p in paths]:
            raise ValueError(f"Partial extension run has different settings: {target}")
        if not (target / "footprint.nc").is_file() or not (target / "PARDUMP").is_file():
            raise RuntimeError(f"Partial model run requires diagnosis; not overwritten: {target}")
        if not (target / "PAR_GIS.txt").is_file():
            model.run_checked([str(HYSPLIT_HOME / "exec/par2asc"), "-iPARDUMP", "-oendpoints.txt",
                               "-vendpoint_times.txt", "-a1"], target, "endpoints")
        receipt = run_receipt(target, cfg, opts, paths, stamp)
        (target / "completion_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        return target
    context = {"station": "BKT", "time_utc": stamp.isoformat() + "Z",
               "purpose": "Frozen domain/duration experiment; gas values do not select scenarios"}
    directory = model.run_footprint(stamp, domain_met(domain), target.parent, HYSPLIT_HOME, cfg, False,
        meteorology_paths=paths, transport=opts, observation_context=context)
    model.run_checked([str(HYSPLIT_HOME / "exec/par2asc"), "-iPARDUMP", "-oendpoints.txt",
                       "-vendpoint_times.txt", "-a1"], directory, "endpoints")
    receipt = run_receipt(directory, cfg, opts, paths, stamp)
    (directory / "completion_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return directory


def fetch_met() -> None:
    """Acquire only missing 50–160E/40S–30N daily ARL crops, two at a time."""
    WIDE_MET.mkdir(parents=True, exist_ok=True)
    def one(day: pd.Timestamp) -> dict:
        gfs.regional_extract(dates=[str(day.date())], bounds=WIDE_BOUNDS, directory=WIDE_MET)
        path = WIDE_MET / f"{day:%Y%m%d}_gfs0p25"
        provenance = json.loads(path.with_name(path.name + ".json").read_text())
        if provenance.get("requested_bounds") != list(WIDE_BOUNDS):
            raise ValueError(f"Wide GFS bounds mismatch: {path}")
        reader = GFSReader(path)
        if not (np.isclose(reader.lat[0], -40) and np.isclose(reader.lat[-1], 30)
                and np.isclose(reader.lon[0], 50) and np.isclose(reader.lon[-1], 160)):
            raise ValueError(f"Wide GFS coordinates mismatch: {path}")
        if sha256(path) != provenance["sha256"]:
            raise ValueError(f"Wide GFS checksum mismatch: {path}")
        return dict(date_utc=str(day.date()), path=str(path.resolve()), bytes=path.stat().st_size,
                    sha256=provenance["sha256"], bounds=provenance["requested_bounds"])
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(one, FULL_DATES))
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    (RECEIPTS / "wide_meteorology.json").write_text(json.dumps(rows, indent=2) + "\n")


def wide_gfed_paths() -> dict[str, Path]:
    root = ROOT / "data/bkt_sources/gfed51"
    return {
        "daily_sep": root / "GFED51_20190904_30_wide.npz",
        "daily_oct": root / "GFED51_20191001_06_wide.npz",
        "monthly": root / "GFED51_201909_10_monthly_wide.npz",
    }


def fetch_flux() -> None:
    """Fetch the minimal wide GFED CH4 subsets through the existing safe transfer."""
    paths = wide_gfed_paths()
    commands = [
        ("GFED5/GFED5.1/Daily/GFED5.1_daily_2019-09.nc", 4, 30, paths["daily_sep"]),
        ("GFED5/GFED5.1/Daily/GFED5.1_daily_2019-10.nc", 1, 6, paths["daily_oct"]),
        ("GFED5/GFED5.1/Monthly/GFED5.1_monthly_2019.nc", 9, 10, paths["monthly"]),
    ]
    for remote, start, end, output in commands:
        if output.exists() and output.with_suffix(output.suffix + ".json").exists():
            continue
        subprocess.run(["/usr/bin/python3", str(ROOT / "scripts/bkt_gfed_transfer.py"), remote, "--fast", "--subset",
            "--day-start", str(start), "--day-end", str(end), "--bounds", "50", "-40", "160", "30",
            "--gases", "CH4", "--output", str(output)], check=True)
    rows = []
    for name, path in paths.items():
        meta = json.loads(path.with_suffix(path.suffix + ".json").read_text())
        if meta.get("bounds") != list(WIDE_BOUNDS) or sha256(path) != meta["sha256"]:
            raise ValueError(f"GFED provenance mismatch: {path}")
        rows.append(dict(name=name, path=str(path.resolve()), sha256=meta["sha256"], bounds=meta["bounds"], bytes=path.stat().st_size))
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    (RECEIPTS / "wide_gfed.json").write_text(json.dumps(rows, indent=2) + "\n")


def remap_nonnegative(values: np.ndarray, lat: np.ndarray, lon: np.ndarray,
                      target_lat: np.ndarray, target_lon: np.ndarray) -> np.ndarray:
    yi, xi = np.argsort(lat), np.argsort(lon)
    return matching_flux(np.asarray(values)[np.ix_(yi, xi)], np.asarray(lat)[yi], np.asarray(lon)[xi], target_lat, target_lon)


def monthly_inputs(target_lat: np.ndarray, target_lon: np.ndarray) -> xr.Dataset:
    data = ROOT / "data/bkt_sources"
    sources: list[tuple[Path, str, str]] = [(p, "fluxes", p.stem.removesuffix("_2019"))
        for p in sorted((data / "edgar_v8").glob("CH4_*_2019.nc"))]
    sources += [(data / "inversion" / folder / name, variable, label) for folder, name, variable, label in (
        ("wetlands", "LPJ_MERRA2_2019_0.5x0.5.nc", "emis_ch4", "wetlands"),
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
            for month in (pd.Timestamp("2019-09-01"), pd.Timestamp("2019-10-01")):
                selected = source.isel(time=0) if source.sizes["time"] == 1 else source.isel(time=month.month - 1)
                # The raw inventories are global; select a small halo around target cells.
                sub = selected.sel(lat=slice(target_lat[0] - .5, target_lat[-1] + .5),
                                   lon=slice(target_lon[0] - .5, target_lon[-1] + .5)).load()
                values.append(remap_nonnegative(sub.values * 1e9 / MW["CH4"], sub.lat.values, sub.lon.values,
                    target_lat, target_lon))
            fields.append(values); labels.append(label)
    result = xr.Dataset({"flux": (("source", "month", "lat", "lon"), np.asarray(fields))},
        coords={"source": labels, "month": pd.to_datetime(["2019-09-01", "2019-10-01"]),
                "lat": target_lat, "lon": target_lon})
    result.flux.attrs["units"] = "umol m-2 s-1"
    result.attrs["soil_sign"] = "soil_uptake is a positive magnitude and is subtracted only in net budgets"
    return result


def fire_inputs(target_lat: np.ndarray, target_lon: np.ndarray) -> xr.Dataset:
    paths = wide_gfed_paths()
    for path in paths.values():
        if not path.with_suffix(path.suffix + ".json").exists():
            raise FileNotFoundError(f"Run fetch-flux before prepare-flux: {path}")
    ecosystem = ROOT / "data/bkt_sources/gfed51/GFED5.1_ecosystem_2019.nc"
    if not ecosystem.with_suffix(ecosystem.suffix + ".json").exists():
        raise ValueError("Unverified GFED ecosystem file")
    with np.load(paths["monthly"]) as monthly:
        lat, lon, total = monthly["lat"], monthly["lon"], monthly["CH4"]
    import h5py
    with h5py.File(ecosystem) as source:
        yi = np.flatnonzero((source["lat"][:] >= WIDE_BOUNDS[1]) & (source["lat"][:] <= WIDE_BOUNDS[3]))
        xi = np.flatnonzero((source["lon"][:] >= WIDE_BOUNDS[0]) & (source["lon"][:] <= WIDE_BOUNDS[2]))
        if not np.array_equal(lat, source["lat"][:][yi]) or not np.array_equal(lon, source["lon"][:][xi]):
            raise ValueError("Wide GFED ecosystem and monthly grids differ")
        carbon = source["carbon_emissions_partitioning/C_14_Cropland"][8:10, yi[0]:yi[-1] + 1, xi[0]:xi[-1] + 1]
    factors = pd.read_csv(ROOT / "data/bkt_sources/gfed51/GFED5_emission_factors.txt", sep=r"\s+", comment="#", header=None, index_col=0)
    ratio = float(factors.loc["CH4"].iloc[-1]) / float(factors.loc["C"].iloc[-1])
    fraction = np.clip(np.divide(carbon * ratio, total, out=np.zeros_like(total), where=total > 0), 0, 1)
    sorted_area = cell_area_km2(np.sort(lat), np.sort(lon)) * 1e6
    area = sorted_area[np.ix_(np.argsort(np.argsort(lat)), np.argsort(np.argsort(lon)))]
    times, all_fire, crop_fire = [], [], []
    for key in ("daily_sep", "daily_oct"):
        with np.load(paths[key]) as daily:
            if not np.array_equal(lat, daily["lat"]) or not np.array_equal(lon, daily["lon"]):
                raise ValueError("Wide GFED daily grid differs from monthly grid")
            stamps = pd.Timestamp("1800-01-01") + pd.to_timedelta(daily["time"], unit="h")
            for stamp, emission in zip(stamps, daily["CH4"]):
                if not np.isfinite(emission).all() or (emission < 0).any():
                    raise ValueError("Invalid wide GFED daily CH4 mass")
                flux = emission / area / 86400 * 1e6 / MW["CH4"]
                month_index = stamp.month - 9
                all_fire.append(remap_nonnegative(flux, lat, lon, target_lat, target_lon))
                crop_fire.append(remap_nonnegative(flux * fraction[month_index], lat, lon, target_lat, target_lon))
                times.append(stamp.normalize())
    result = xr.Dataset({
        "all_fire_flux": (("day", "lat", "lon"), np.asarray(all_fire)),
        "crop_fire_flux": (("day", "lat", "lon"), np.asarray(crop_fire)),
    }, coords={"day": times, "lat": target_lat, "lon": target_lon})
    result["noncrop_fire_flux"] = result.all_fire_flux - result.crop_fire_flux
    if float(result.noncrop_fire_flux.min()) < -1e-12:
        raise ValueError("Non-crop fire becomes negative")
    for name in result.data_vars:
        result[name].attrs["units"] = "umol m-2 s-1"
    result.attrs["crop_overlap"] = "Cropland methane is removed from all-fire CH4; it is not double counted with monthly agriculture."
    return result


def prepare_flux() -> None:
    INPUTS.mkdir(parents=True, exist_ok=True)
    for domain in DOMAINS:
        lat, lon = target_grid(domain)
        monthly = monthly_inputs(lat, lon)
        fire = fire_inputs(lat, lon)
        save_nc(monthly, INPUTS / f"{domain}_monthly_flux.nc")
        save_nc(fire, INPUTS / f"{domain}_daily_fire_flux.nc")
        receipt = dict(domain=domain, lat_count=len(lat), lon_count=len(lon), bounds=[float(lon[0]), float(lat[0]), float(lon[-1]), float(lat[-1])],
            monthly_sha256=sha256(INPUTS / f"{domain}_monthly_flux.nc"), fire_sha256=sha256(INPUTS / f"{domain}_daily_fire_flux.nc"))
        (RECEIPTS / f"{domain}_flux.json").write_text(json.dumps(receipt, indent=2) + "\n")


def run_full() -> None:
    selection = complete_selection()
    jobs = [("wide", 120, utc_stamp(stamp)) for stamp in selection.time_utc]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(ensure_run, *job): job for job in jobs}
        for future in as_completed(futures):
            print(f"completed {future.result()}", flush=True)


def convergence_jobs() -> list[tuple[str, int, pd.Timestamp]]:
    return [(domain, hours, stamp) for stamp in REPRESENTATIVES for domain in DOMAINS for hours in DURATIONS]


def run_convergence() -> None:
    # Reuse original/wide 120 h scenarios; create only the complementary durations.
    jobs = [(domain, hours, stamp) for domain, hours, stamp in convergence_jobs() if hours != 120]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(ensure_run, *job): job for job in jobs}
        for future in as_completed(futures):
            print(f"completed {future.result()}", flush=True)
    # Materialise completion receipts for both reused 120 h cells too.
    for stamp in REPRESENTATIVES:
        ensure_run("original", 120, stamp)
        ensure_run("wide", 120, stamp)


def read_footprint(directory: Path) -> tuple[xr.DataArray, dict, int]:
    meta = json.loads((directory / "run_metadata.json").read_text())
    with xr.open_dataset(directory / "footprint.nc") as data:
        field = data.footprint_sensitivity.astype(float).load()
    actual = actual_particles((directory / "MESSAGE").read_text())
    cfg = meta["configuration"]
    stamp = utc_stamp(meta["observation"]["time_utc"])
    expected = pd.date_range(stamp - pd.Timedelta(hours=cfg["hours_back"]), stamp - pd.Timedelta(hours=1), freq="h")
    if field.sizes["time"] != cfg["hours_back"] or not np.array_equal(field.time.values, expected.values):
        raise ValueError(f"Footprint chronology differs from configuration: {directory}")
    if not np.isfinite(field).all() or float(field.min()) < 0:
        raise ValueError(f"Invalid footprint: {directory}")
    return field * (cfg["particles"] / actual), meta, actual


def active_endpoints(directory: Path, meta: dict, actual: int) -> pd.DataFrame:
    points = pd.read_csv(directory / "PAR_GIS.txt", skipinitialspace=True)
    points.columns = points.columns.str.strip()
    raw = points.time.astype(str).str.replace(r"\s+", "", regex=True)
    points["endpoint_utc"] = pd.to_datetime(raw, format="%m/%d/%y%H:%M")
    expected = utc_stamp(meta["observation"]["time_utc"]) - pd.Timedelta(hours=meta["configuration"]["hours_back"])
    # Some frozen benchmark runs deliberately saved hourly particle dumps.
    # Select the configured terminal time before enforcing one row per emitted
    # particle; otherwise those valid runs appear to over-count endpoints.
    points = points.loc[points.endpoint_utc.eq(expected)].copy()
    if len(points) != actual or points.NSORT.duplicated().any():
        raise ValueError(f"Incomplete terminal endpoint particle accounting: {directory}")
    active = points.loc[points.PGRD.gt(0)].copy()
    if active.empty:
        raise ValueError(f"No active endpoint particles: {directory}")
    return active


def sample_native_surface(met_path: Path, stamp: pd.Timestamp) -> dict[str, float]:
    reader = cached_gfs_reader(str(met_path.resolve()))
    return {name: reader.point(stamp, name, 0, -.202, 100.318, "nearest")
            for name in ("PBLH", "SHGT", "U10M", "V10M", "T02M")}


def endpoint_background(active: pd.DataFrame, stamp: pd.Timestamp, met_path: Path) -> dict[str, float]:
    reader = cached_gfs_reader(str(met_path.resolve()))
    terrain = reader.field(stamp, "SHGT", 0)
    ground = RegularGridInterpolator((reader.lat, reader.lon), terrain)(active[["latitude", "longitude"]].to_numpy())
    height = active.height.to_numpy(float) + ground
    path = ROOT / "data/bkt_sources/inversion/carbontracker" / f"CTCH4_2025.molefrac_glb3x2_{stamp:%Y-%m-%d}.nc"
    provenance = path.with_suffix(path.suffix + ".json")
    if not provenance.exists() or sha256(path) != json.loads(provenance.read_text())["sha256"]:
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


def surface_budget(field: xr.DataArray, domain: str) -> dict[str, float]:
    with xr.open_dataset(INPUTS / f"{domain}_monthly_flux.nc") as data:
        monthly = data.load()
    with xr.open_dataset(INPUTS / f"{domain}_daily_fire_flux.nc") as data:
        fire = data.load()
    if not np.array_equal(field.lat.values, monthly.lat.values) or not np.array_equal(field.lon.values, monthly.lon.values):
        raise ValueError("Footprint/monthly source grids differ")
    stamp = pd.Timestamp(field.time.values[-1]) + pd.Timedelta(hours=1)
    month = xr.DataArray(pd.DatetimeIndex(field.time.values).to_period("M").to_timestamp(), dims="time")
    selected = monthly.flux.sel(month=month)
    response = {str(source): float((field.values * selected.sel(source=source).values).sum() * 1000)
                for source in monthly.source.values}
    day = xr.DataArray(pd.DatetimeIndex(field.time.values).normalize(), dims="time")
    noncrop = float((field.values * fire.noncrop_fire_flux.sel(day=day).values).sum() * 1000)
    anthro = sum(value for name, value in response.items() if name.startswith("CH4_"))
    net = anthro + response["wetlands"] + response["termites"] + response["geological"] - response["soil_uptake"] + noncrop
    return dict(anthro_ppb=anthro, wetlands_ppb=response["wetlands"], termites_ppb=response["termites"],
                geological_ppb=response["geological"], soil_uptake_ppb=response["soil_uptake"],
                noncrop_fire_ppb=noncrop, net_surface_ppb=net)


def wind_labels(u: float, v: float) -> dict[str, str]:
    if not np.isfinite(u) or not np.isfinite(v):
        raise ValueError("Nonfinite 10 m wind")
    if u == 0 and v == 0:
        quadrant = "calm"
    elif u >= 0 and v >= 0:
        quadrant = "U+V+_toward_NE"
    elif u < 0 and v >= 0:
        quadrant = "U-V+_toward_NW"
    elif u < 0 and v < 0:
        quadrant = "U-V-_toward_SW"
    else:
        quadrant = "U+V-_toward_SE"
    return {"wind_toward_quadrant": quadrant, "zonal_regime": "eastward" if u >= 0 else "westward"}


def wib_labels(stamp: pd.Timestamp) -> dict[str, object]:
    local = stamp + pd.Timedelta(hours=7)
    return {"time_wib": local, "wib_hour": int(local.hour),
            "wib_clock": "day_07_17" if 7 <= local.hour < 18 else "night_18_06",
            "wib_month": local.strftime("%Y-%m")}


def run_budget(directory: Path, domain: str, expected_stamp: pd.Timestamp | None = None,
               expected_hours: int | None = None) -> dict[str, object]:
    field, meta, actual = read_footprint(directory)
    stamp = utc_stamp(meta["observation"]["time_utc"])
    if expected_stamp is not None and stamp != utc_stamp(expected_stamp):
        raise ValueError(f"Budget receptor identity mismatch: {directory}")
    if expected_hours is not None and meta["configuration"]["hours_back"] != expected_hours:
        raise ValueError(f"Budget duration identity mismatch: {directory}")
    active = active_endpoints(directory, meta, actual)
    endpoint_stamp = stamp - pd.Timedelta(hours=meta["configuration"]["hours_back"])
    surface = surface_budget(field, domain)
    background = endpoint_background(active, endpoint_stamp, domain_met(domain) / f"{endpoint_stamp:%Y%m%d}_gfs0p25")
    native = sample_native_surface(domain_met(domain) / f"{stamp:%Y%m%d}_gfs0p25", stamp)
    lag = (stamp - pd.DatetimeIndex(field.time.values)).total_seconds() / 3600
    hourly = field.sum(("lat", "lon")).values
    aggregate = field.sum("time").values
    edge = np.zeros(aggregate.shape, bool); edge[[0, -1], :] = True; edge[:, [0, -1]] = True
    return dict(time_utc=stamp, endpoint_time_utc=endpoint_stamp, domain=domain,
        hours_back=int(meta["configuration"]["hours_back"]), emitted_particles=actual, active_particles=len(active),
        retention_fraction=len(active) / actual, sensitivity=float(field.sum()),
        oldest24h_sensitivity_percent=float(100 * hourly[lag > meta["configuration"]["hours_back"] - 24].sum() / float(field.sum())),
        edge_sensitivity_percent=float(100 * aggregate[edge].sum() / float(field.sum())), **surface, **background, **native,
        total_prior_ppb=surface["net_surface_ppb"] + background["background_ppb"], **wind_labels(native["U10M"], native["V10M"]),
        source_run=str(directory.resolve()), footprint_sha256=sha256(directory / "footprint.nc"))


def circular_block_indices(days: Iterable[object], *, replicates: int = 5000, block_days: int = 3,
                           seed: int = SEED) -> np.ndarray:
    unique = np.asarray(sorted(pd.to_datetime(pd.Index(days)).normalize().unique()), dtype="datetime64[ns]")
    if len(unique) == 0 or block_days <= 0 or replicates <= 0:
        raise ValueError("Need positive circular-block dimensions and at least one date")
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, len(unique), size=(replicates, int(np.ceil(len(unique) / block_days))))
    blocks = (starts[:, :, None] + np.arange(block_days)) % len(unique)
    return blocks.reshape(replicates, -1)[:, :len(unique)]


def decomposition(frame: pd.DataFrame, metric: str, *, replicates: int = 5000, seed: int = SEED) -> dict[str, float]:
    required = {"original_retained", f"narrow_{metric}", f"wide_{metric}", "date_utc"}
    if not required.issubset(frame):
        raise ValueError(f"Decomposition lacks columns: {required - set(frame)}")
    retained = frame.original_retained.astype(bool)
    if retained.sum() == 0:
        raise ValueError("No originally retained records")
    def calculate(sample: pd.DataFrame) -> tuple[float, float, float, float]:
        keep = sample.original_retained.astype(bool)
        same = (sample.loc[keep, f"wide_{metric}"] - sample.loc[keep, f"narrow_{metric}"]).mean()
        recovered = sample[f"wide_{metric}"].mean() - sample.loc[keep, f"wide_{metric}"].mean()
        total = sample[f"wide_{metric}"].mean() - sample.loc[keep, f"narrow_{metric}"].mean()
        return same, recovered, total, same + recovered - total
    same, recovered, total, closure = calculate(frame)
    dates = pd.to_datetime(frame.date_utc).dt.normalize()
    unique = np.asarray(sorted(dates.unique()))
    indexes = circular_block_indices(unique, replicates=replicates, seed=seed)
    lookup = {day: frame.loc[dates.eq(day)] for day in unique}
    draws = []
    for picked in indexes:
        sample = pd.concat([lookup[unique[j]] for j in picked], ignore_index=True)
        if sample.original_retained.astype(bool).any():
            draws.append(calculate(sample)[:3])
    if len(draws) < max(1, int(.9 * replicates)):
        raise ValueError("Too few valid block-bootstrap draws contain originally retained hours")
    draws = np.asarray(draws)
    quantiles = np.quantile(draws, [.025, .975], axis=0)
    return dict(metric=metric, n_all=len(frame), n_original_retained=int(retained.sum()), n_recovered=int((~retained).sum()),
        same_hour_change=same, recovered_hour_composition_change=recovered, total_change=total, closure_error=closure,
        same_hour_ci025=quantiles[0, 0], same_hour_ci975=quantiles[1, 0],
        recovered_ci025=quantiles[0, 1], recovered_ci975=quantiles[1, 1],
        total_ci025=quantiles[0, 2], total_ci975=quantiles[1, 2], block_days=3, replicates=replicates, seed=seed)


def observed_difference(frame: pd.DataFrame, species: str, *, replicates: int = 5000, seed: int = SEED) -> dict[str, float]:
    retained = frame.original_retained.astype(bool)
    if retained.all() or not retained.any():
        raise ValueError("Observed comparison requires both retained and recovered hours")
    value = frame.loc[~retained, species].mean() - frame.loc[retained, species].mean()
    dates = pd.to_datetime(frame.date_utc).dt.normalize(); unique = np.asarray(sorted(dates.unique()))
    indexes = circular_block_indices(unique, replicates=replicates, seed=seed)
    lookup = {day: frame.loc[dates.eq(day)] for day in unique}; draws = []
    for picked in indexes:
        sample = pd.concat([lookup[unique[j]] for j in picked], ignore_index=True)
        keep = sample.original_retained.astype(bool)
        if keep.any() and (~keep).any():
            draws.append(sample.loc[~keep, species].mean() - sample.loc[keep, species].mean())
    if len(draws) < max(1, int(.9 * replicates)):
        raise ValueError("Too few valid block-bootstrap draws contain both comparison groups")
    low, high = np.quantile(draws, [.025, .975])
    return dict(species=species, n_all=len(frame), n_original_retained=int(retained.sum()),
        n_recovered=int((~retained).sum()), retained_mean=float(frame.loc[retained, species].mean()),
        recovered_mean=float(frame.loc[~retained, species].mean()),
        retained_median=float(frame.loc[retained, species].median()),
        recovered_median=float(frame.loc[~retained, species].median()),
        recovered_minus_retained=value,
        ci025=low, ci975=high, block_days=3, replicates=replicates, seed=seed,
        interpretation="Recovered-minus-retained observed concentration; transport widening does not change observations.")


def analyze_full() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    selection = complete_selection().set_index("time_utc")
    rows = []
    for stamp in selection.index:
        stamp = utc_stamp(stamp)
        narrow = run_budget(completed_run("original", 120, stamp), "original", stamp, 120)
        wide = run_budget(completed_run("wide", 120, stamp), "wide", stamp, 120)
        row = dict(time_utc=stamp, date_utc=stamp.normalize(), original_retained=narrow["retention_fraction"] >= .95,
            co2=float(selection.loc[stamp, "co2"]), ch4=float(selection.loc[stamp, "ch4"]), co=float(selection.loc[stamp, "co"]),
            **wib_labels(stamp))
        for key, value in narrow.items():
            if isinstance(value, (int, float, np.number)): row[f"narrow_{key}"] = value
        for key, value in wide.items():
            if isinstance(value, (int, float, np.number)): row[f"wide_{key}"] = value
        row.update(narrow_source_run=narrow["source_run"],wide_source_run=wide["source_run"],
                   narrow_footprint_sha256=narrow["footprint_sha256"],wide_footprint_sha256=wide["footprint_sha256"])
        row.update(wind_labels(narrow["U10M"], narrow["V10M"]))
        rows.append(row)
    frame = pd.DataFrame(rows).sort_values("time_utc")
    if len(frame) != 52 or frame.time_utc.duplicated().any():
        raise ValueError("Full extension table must contain all 52 unique receptors")
    frame.to_csv(TABLES / "full_receptor_budget.csv", index=False)
    metrics = ("sensitivity", "net_surface_ppb", "background_ppb", "total_prior_ppb")
    result = pd.DataFrame([decomposition(frame, metric) for metric in metrics])
    if not np.allclose(result.closure_error, 0, atol=1e-12):
        raise ValueError("Domain decomposition does not close")
    result.to_csv(TABLES / "full_domain_decomposition.csv", index=False)
    pd.DataFrame([observed_difference(frame, species) for species in ("co2", "ch4", "co")]).to_csv(
        TABLES / "observed_sample_difference.csv", index=False)
    strata = []
    for dimension in ("wib_clock", "wib_month", "wind_toward_quadrant", "zonal_regime"):
        for label, group in frame.groupby(dimension, dropna=False):
            keep=group.original_retained.astype(bool)
            strata.append(dict(dimension=dimension, stratum=label, n_all=len(group),
                n_original_retained=int(group.original_retained.sum()), n_recovered=int((~group.original_retained).sum()),
                original_retained_percent=float(100 * group.original_retained.mean()),
                co2_mean_ppm=group.co2.mean(), ch4_mean_ppb=group.ch4.mean(), co_mean_ppb=group.co.mean(),
                retained_co2_mean_ppm=group.loc[keep,"co2"].mean(),recovered_co2_mean_ppm=group.loc[~keep,"co2"].mean(),
                retained_ch4_mean_ppb=group.loc[keep,"ch4"].mean(),recovered_ch4_mean_ppb=group.loc[~keep,"ch4"].mean(),
                retained_co_mean_ppb=group.loc[keep,"co"].mean(),recovered_co_mean_ppb=group.loc[~keep,"co"].mean(),
                narrow_retention_median=group.narrow_retention_fraction.median()))
    pd.DataFrame(strata).to_csv(TABLES / "selection_strata.csv", index=False)
    contract = [
        ("full_ensemble_first_time_utc", frame.time_utc.min().isoformat(), "UTC timestamp"),
        ("full_ensemble_last_time_utc", frame.time_utc.max().isoformat(), "UTC timestamp"),
        ("full_ensemble_receptors", len(frame), "receptor hours"),
        ("requested_particles_per_run", run_config(120, "wide").particles, "particles"),
        ("full_ensemble_backward_duration", 120, "hours"),
        ("original_retention_threshold", .95, "fraction"),
        ("original_meteorology_west", ORIGINAL_BOUNDS[0], "degrees east"),
        ("original_meteorology_south", ORIGINAL_BOUNDS[1], "degrees north"),
        ("original_meteorology_east", ORIGINAL_BOUNDS[2], "degrees east"),
        ("original_meteorology_north", ORIGINAL_BOUNDS[3], "degrees north"),
        ("wide_meteorology_west", WIDE_BOUNDS[0], "degrees east"),
        ("wide_meteorology_south", WIDE_BOUNDS[1], "degrees north"),
        ("wide_meteorology_east", WIDE_BOUNDS[2], "degrees east"),
        ("wide_meteorology_north", WIDE_BOUNDS[3], "degrees north"),
        ("original_output_latitude_span", 36, "degrees"),
        ("original_output_longitude_span", 48, "degrees"),
        ("wide_output_latitude_span", 60, "degrees"),
        ("wide_output_longitude_span", 100, "degrees"),
        ("output_grid_spacing", .25, "degrees"),
        ("block_bootstrap_block_length", 3, "days"),
        ("block_bootstrap_replicates", 5000, "replicates"),
        ("block_bootstrap_seed", SEED, "integer seed"),
        ("representative_receptors", len(REPRESENTATIVES), "receptor hours"),
        ("convergence_backward_durations", ",".join(map(str, DURATIONS)), "hours"),
        ("convergence_domains", ",".join(DOMAINS), "labels"),
    ]
    pd.DataFrame(contract, columns=["parameter", "value", "units_or_format"]).to_csv(
        TABLES / "design_contract.csv", index=False)


def analyze_convergence() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    rows = []
    for stamp in REPRESENTATIVES:
        for domain, hours in ((d, h) for d in DOMAINS for h in DURATIONS):
            directory = completed_run(domain, hours, stamp)
            rows.append(run_budget(directory, domain, stamp, hours))
    frame = pd.DataFrame(rows).sort_values(["time_utc", "domain", "hours_back"])
    if len(frame) != len(REPRESENTATIVES) * len(DOMAINS) * len(DURATIONS):
        raise ValueError("Convergence matrix is incomplete")
    frame.to_csv(TABLES / "convergence_matrix.csv", index=False)
    changes = []
    metrics = ("net_surface_ppb", "background_ppb", "total_prior_ppb", "sensitivity")
    for stamp, group in frame.groupby("time_utc"):
        pivot = group.set_index(["domain", "hours_back"])
        for metric in metrics:
            for low, high in ((72, 120), (120, 168)):
                original = pivot.loc[("original", high), metric] - pivot.loc[("original", low), metric]
                wide = pivot.loc[("wide", high), metric] - pivot.loc[("wide", low), metric]
                changes.append(dict(time_utc=stamp, metric=metric, comparison=f"{low}_to_{high}h",
                    original_duration_change=original, wide_duration_change=wide,
                    domain_duration_interaction=wide - original,
                    original_domain_change_high=pivot.loc[("wide", high), metric] - pivot.loc[("original", high), metric],
                    wide_domain_change_low=pivot.loc[("wide", low), metric] - pivot.loc[("original", low), metric]))
    pd.DataFrame(changes).to_csv(TABLES / "convergence_changes.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["fetch-met", "fetch-flux", "prepare-flux", "run-full", "run-convergence", "analyze-full", "analyze-convergence"])
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True); RECEIPTS.mkdir(parents=True, exist_ok=True)
    {"fetch-met": fetch_met, "fetch-flux": fetch_flux, "prepare-flux": prepare_flux,
     "run-full": run_full, "run-convergence": run_convergence, "analyze-full": analyze_full,
     "analyze-convergence": analyze_convergence}[args.stage]()


if __name__ == "__main__":
    main()
