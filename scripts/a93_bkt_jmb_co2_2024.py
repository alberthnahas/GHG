#!/usr/bin/env python3
"""October to December 2024 extension of the BKT + Jambi daytime CO2 analysis.

The joint record ends on 31 December 2024 (the BKT archive stops there), and
the 2024 overlap adds 63 afternoon days to the 21 of November and December
2023. Methane cannot be extended: CarbonTracker-CH4 and LPJ-MERRA2 both stop
at the end of 2023. CO2 can: CT-NRT.v2025-1 fluxes and mole fractions run to
31 December 2024 and EDGAR_2025_GHG has 2024.

Receptors are the 06 UTC (13 WIB) hours with valid CO2 at both towers, both
inlets at 100 m, two seeds of 2,000 particles (the third seed changes the
daytime biosphere increment by 0.3 ppm out of about 30). Everything else
follows a84 and a89: 120 h backward, GFS 0.25 wide crop, 60 x 100 degree grid.

Stages
  select        receptor table for the 2024 window
  fetch-met     NOAA READY wide crop, 26 September to 31 December 2024
  fetch-inputs  CT-NRT three-hourly fluxes and CO2 boundary, EDGAR 2024 fossil CO2
  prepare       fossil fields per tower, CT-NRT flux box, diagnostic biosphere for 2024
  observations  afternoon CO2 means and the CH4 enhancement proxy (no CT-CH4 boundary for 2024)
  run           HYSPLIT campaign, both towers, two seeds
  operator      CO2 operator rows matching the 2023 tables
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import zipfile

import numpy as np
import pandas as pd

import a41_bkt_gfs as gfs
import a42_bkt_sources as src
import a71_domain_budget_extension as ext
import a84_bkt_jmb_two_receptor as T
import a89_bkt_jmb_co2 as C
import a90_bkt_jmb_co2_improved as I
import ghg_common as G
from a43_bkt_source_analysis import MW

YEAR = 2024
WINDOW = (pd.Timestamp("2024-10-01"), pd.Timestamp("2024-12-31T23:00"))
RECEPTOR_HOUR_UTC = 6
SEEDS = (0, -10)
MET = T.ROOT / "data/hysplit/gfs0p25/two_receptor_wide_2024"
RUNS = T.OUT / "runs_2024"
TABLES = T.TABLES
EDGAR_URL = C.EDGAR_URL
SECTORS = C.SECTORS


def receptors() -> pd.DataFrame:
    """Joint 13 WIB receptor hours: valid, unflagged CO2 at both towers."""
    index = pd.date_range(WINDOW[0], WINDOW[1], freq="h")
    index = index[index.hour == RECEPTOR_HOUR_UTC]
    frames = []
    for code in T.STATIONS:
        record = G.apply_flags(G.load_station(code)).set_index("time_utc").sort_index().reindex(index)
        frames.append(pd.DataFrame(dict(time_utc=index, station=code, co2=record.co2.values, ch4=record.ch4.values, co=record.co.values,
                                        valid=(record.co2.notna() & ~record.suspect_co2.eq(True)).values)))
    table = pd.concat(frames, ignore_index=True)
    joint = table.groupby("time_utc").valid.all()
    table["joint"] = table.time_utc.map(joint)
    table = table[table.joint].copy()
    days = sorted({t.normalize() for t in table.time_utc})
    held = {d for i, d in enumerate(days) if i % 4 == 3}
    table["holdout"] = table.time_utc.dt.normalize().isin(held)
    return table.reset_index(drop=True)


def stamps() -> list[pd.Timestamp]:
    return sorted(set(receptors().time_utc))


def met_days() -> pd.DatetimeIndex:
    first = min(stamps()) - pd.Timedelta(hours=T.HOURS_BACK)
    return pd.date_range(first.normalize(), max(stamps()).normalize(), freq="D")


def met_paths(stamp: pd.Timestamp) -> list[Path]:
    days = pd.date_range((stamp - pd.Timedelta(hours=T.HOURS_BACK)).normalize(), stamp.normalize(), freq="D")
    return [MET / f"{day:%Y%m%d}_gfs0p25" for day in days]


def boundary_days() -> list[pd.Timestamp]:
    return sorted({(s - pd.Timedelta(hours=T.HOURS_BACK)).normalize() for s in stamps()})


def edgar_file(sector: str) -> Path:
    return C.EDGAR_DIR / f"CO2_{sector}_{YEAR}.nc"


def select() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    table = receptors()
    table.to_csv(TABLES / "co2_receptor_selection_2024.csv", index=False)
    days = met_days()
    summary = dict(window=f"{WINDOW[0]:%Y-%m-%d} to {WINDOW[1]:%Y-%m-%d}", joint_receptors=int(table.time_utc.nunique()),
                   holdout_days=int(table.loc[table.holdout, "time_utc"].dt.normalize().nunique()),
                   meteorology_days=len(days), meteorology_from=f"{days[0]:%Y-%m-%d}", meteorology_to=f"{days[-1]:%Y-%m-%d}",
                   boundary_days=len(boundary_days()), runs=int(table.time_utc.nunique()) * len(T.STATIONS) * len(SEEDS))
    (TABLES / "co2_selection_summary_2024.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)


def fetch_met(interface: str | None, passes: int = 6, pause_s: int = 60) -> None:
    """NOAA READY crop, one day at a time.

    The extraction is resumable through its job files, and a single SSL or
    timeout error at ready.noaa.gov must not end the whole transfer, so each day
    is retried across several passes before the stage gives up.
    """
    import time
    if interface:
        T.bind_interface(interface)
    MET.mkdir(parents=True, exist_ok=True)
    days = met_days()
    for attempt in range(1, passes + 1):
        pending = [d for d in days if not (MET / f"{d:%Y%m%d}_gfs0p25.json").exists()]
        print(f"pass {attempt}: {len(pending)} of {len(days)} days pending", flush=True)
        if not pending:
            break
        for day in pending:
            try:
                gfs.regional_extract(dates=[f"{day:%Y-%m-%d}"], bounds=ext.WIDE_BOUNDS, directory=MET)
            except Exception as error:  # noqa: BLE001 - transient NOAA errors are retried on the next pass
                print(f"  {day:%Y-%m-%d} failed: {type(error).__name__}: {error}", flush=True)
                time.sleep(pause_s)
    missing = [d for d in days if not (MET / f"{d:%Y%m%d}_gfs0p25.json").exists()]
    if missing:
        raise FileNotFoundError(f"Meteorology incomplete after {passes} passes: {len(missing)} days")
    print(f"meteorology complete: {len(days)} days", flush=True)


def fetch_edgar() -> None:
    C.EDGAR_DIR.mkdir(parents=True, exist_ok=True)
    for sector in SECTORS:
        target = edgar_file(sector)
        if target.exists() and target.with_suffix(".nc.json").exists():
            continue
        url = EDGAR_URL.format(s=sector)
        remote = src.RangeReader(url)
        with zipfile.ZipFile(remote) as archive:
            names = [n for n in archive.namelist() if f"_CO2_{YEAR}_" in n and n.endswith(".nc")]
            if len(names) != 1:
                raise ValueError(f"Unexpected {YEAR} members: {names}")
            info = archive.getinfo(names[0])
            target.write_bytes(archive.read(names[0]))
        import xarray as xr
        with xr.open_dataset(target) as ds:
            variables = {k: ds[k].attrs.get("units", "") for k in ds.data_vars}
        src.provenance(target, url, provider="European Commission JRC / IEA-EDGAR", dataset="EDGAR_2025_GHG monthly CO2 fluxes",
                       gas="CO2", sector=sector, year=YEAR, archive_member=names[0], archive_crc32=info.CRC,
                       archive_etag=remote.etag, transferred_bytes=remote.downloaded, variables=variables)
        print(f"acquired {target.name}: variables {variables}", flush=True)


def fetch_inputs(interface: str | None, workers: int = 3) -> None:
    if interface:
        T.bind_interface(interface)
    jobs = [C.flux_file(d) for d in met_days()] + [C.molefrac_file(d) for d in boundary_days()]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for path in pool.map(lambda j: C.curl(j[0], j[1], interface), jobs):
            print("acquired", path.name, flush=True)
    fetch_edgar()
    print("CO2 inputs complete", flush=True)


# ------------------------------------------------------------------ inputs

def flux_months() -> pd.DatetimeIndex:
    """Every month the footprints touch, tails included.

    A receptor on 4 October reaches back to 29 September, so the monthly fossil
    fields must cover September as well as the receptor months themselves.
    """
    return pd.to_datetime(sorted(met_days().to_period("M").unique().to_timestamp()))

CH4_BASELINE_DAYS = 30
CH4_BASELINE_QUANTILE = .1


def fossil_fields(code: str):
    import xarray as xr
    lat, lon = T.receptor_grid(code)
    months_wanted = flux_months()
    fields = []
    for sector in SECTORS:
        path = edgar_file(sector)
        if not path.with_suffix(".nc.json").exists():
            raise FileNotFoundError(f"Run fetch-inputs first: {path}")
        with xr.open_dataset(path) as ds:
            flux = ds[C.edgar_variable(ds)].sortby("lat").sortby("lon")
            months = []
            for month in months_wanted:
                sub = flux.isel(time=month.month - 1).sel(lat=slice(lat[0] - .5, lat[-1] + .5), lon=slice(lon[0] - .5, lon[-1] + .5)).load()
                months.append(ext.remap_nonnegative(sub.values * 1e9 / MW["CO2"], sub.lat.values, sub.lon.values, lat, lon))
        fields.append(months)
    out = xr.Dataset({"flux": (("sector", "month", "lat", "lon"), np.asarray(fields))},
                     coords={"sector": list(SECTORS), "month": months_wanted, "lat": lat, "lon": lon})
    out.flux.attrs["units"] = "umol m-2 s-1"
    return out


def nrt_box():
    import xarray as xr
    parts = []
    for day in met_days():
        url, path = C.flux_file(day)
        if not path.with_suffix(path.suffix + ".json").exists():
            raise FileNotFoundError(f"Run fetch-inputs first: {path}")
        with xr.open_dataset(path) as ds:
            ds = ds.rename(latitude="lat", longitude="lon").sortby("lat").sortby("lon")
            parts.append(ds[["bio_flux_opt", "ocn_flux_opt", "fire_flux_imp", "fossil_flux_imp"]]
                         .sel(lat=slice(*C.BOX["lat"]), lon=slice(*C.BOX["lon"])).load() * 1e6)
    box = xr.concat(parts, dim="time")
    expected = pd.date_range(met_days()[0] + pd.Timedelta(minutes=90), met_days()[-1] + pd.Timedelta(hours=22, minutes=30), freq="3h")
    if not np.array_equal(pd.DatetimeIndex(box.time.values), expected):
        raise ValueError("CT-NRT 2024 flux record is not a continuous 3-hourly series")
    release, uptake = C.split_nee(box.bio_flux_opt.values)
    day = C.solar_day_mask(box.time.values, box.lon.values)[:, None, :]
    net = box.bio_flux_opt.values
    out = xr.Dataset({"bio_release": (("time", "lat", "lon"), release), "bio_uptake": (("time", "lat", "lon"), uptake),
                      "bio_day": (("time", "lat", "lon"), np.where(day, net, 0.)), "bio_night": (("time", "lat", "lon"), np.where(day, 0., net)),
                      "ocean": box.ocn_flux_opt, "fire": box.fire_flux_imp, "fossil_ctnrt": box.fossil_flux_imp, "bio_net": box.bio_flux_opt},
                     coords={"time": box.time, "lat": box.lat, "lon": box.lon})
    for name in out.data_vars:
        out[name].attrs["units"] = "umol m-2 s-1"
    return out


def prepare() -> None:
    from a43_bkt_source_analysis import save_nc
    C.INPUTS.mkdir(parents=True, exist_ok=True)
    for code in T.STATIONS:
        save_nc(fossil_fields(code), C.INPUTS / f"{code.lower()}_fossil_monthly_2024.nc")
        print("fossil fields", code, flush=True)
    save_nc(nrt_box(), C.INPUTS / "ctnrt_fluxes_box_2024.nc")
    print("CT-NRT flux box written", flush=True)
    I.build_biosphere("_2024", days=met_days(), met_dir=MET)


# ------------------------------------------------------------ observations

def ch4_enhancement_proxy(record: pd.DataFrame, index: pd.DatetimeIndex) -> pd.Series:
    """CH4 above a rolling baseline: no CT-CH4 boundary exists for 2024.

    The baseline is the 10th percentile of the tower's own afternoon CH4 over a
    centered 30-day window, so the proxy measures how far a given afternoon sits
    above the tower's recent clean air rather than above a modeled boundary.
    """
    afternoon = record.loc[record.index.hour.isin(I.AFTERNOON_HOURS_UTC), "ch4"]
    daily = afternoon.groupby(afternoon.index.normalize()).median()
    baseline = daily.rolling(CH4_BASELINE_DAYS, center=True, min_periods=5).quantile(CH4_BASELINE_QUANTILE)
    return pd.Series(record.loc[index, "ch4"].to_numpy() - baseline.reindex(index.normalize()).to_numpy(), index=index)


def observations() -> pd.DataFrame:
    rows = []
    for code in T.STATIONS:
        raw = G.apply_flags(G.load_station(code)).set_index("time_utc").sort_index()
        index = pd.date_range(WINDOW[0] - pd.Timedelta(days=CH4_BASELINE_DAYS), WINDOW[1] + pd.Timedelta(days=CH4_BASELINE_DAYS), freq="h")
        record = raw.reindex(index)
        spike = I.hourly_spikes(record)
        valid = record.co2.notna() & ~record.suspect_co2.eq(True) & ~spike
        proxy = ch4_enhancement_proxy(record, index)
        for stamp in stamps():
            hours = [stamp.normalize() + pd.Timedelta(hours=h) for h in I.AFTERNOON_HOURS_UTC]
            ok = [h for h in hours if valid.get(h, False)]
            rows.append(dict(station=code, time_utc=stamp, co2_1h=record.co2.get(stamp), co2_1h_spike=bool(spike.get(stamp, False)),
                             afternoon_valid_hours=len(ok), co2_afternoon_mean=float(record.co2[ok].mean()) if len(ok) >= 2 else np.nan,
                             afternoon_spikes=int(sum(bool(spike.get(h, False)) for h in hours)),
                             ch4_enhancement_proxy_ppb=float(proxy.get(stamp, np.nan))))
    table = pd.DataFrame(rows)
    table.to_csv(TABLES / "co2_afternoon_observations_2024.csv", index=False)
    print(table.groupby("station").agg(receptors=("time_utc", "size"), with_mean=("co2_afternoon_mean", lambda s: int(s.notna().sum())),
                                       spike_hours=("afternoon_spikes", "sum")).to_string(), flush=True)
    return table


def validate_proxy() -> pd.DataFrame:
    """Check the CH4 proxy against the CT-CH4 based enhancement on the 2023 receptors."""
    from scipy.stats import spearmanr
    ch4 = pd.read_csv(TABLES / "inversion_predictions.csv", parse_dates=["time_utc"]).query("case == 'joint_screened_sector'")
    ch4 = ch4.assign(modelled=ch4.observed_ppb - ch4.background_ppb)
    rows, pairs = [], []
    for code in T.STATIONS:
        raw = G.apply_flags(G.load_station(code)).set_index("time_utc").sort_index()
        index = pd.date_range("2023-10-20", "2024-01-31", freq="h")
        proxy = ch4_enhancement_proxy(raw.reindex(index), index)
        g = ch4[ch4.station.eq(code)].assign(proxy=lambda d: proxy.reindex(d.time_utc).to_numpy()).dropna(subset=["proxy"])
        rows.append(dict(station=code, n=len(g), spearman=float(spearmanr(g.modelled, g.proxy).statistic),
                         mean_modelled_ppb=float(g.modelled.mean()), mean_proxy_ppb=float(g.proxy.mean())))
        pairs.append(g[["station", "time_utc", "modelled", "proxy"]].rename(columns=dict(modelled="modelled_ppb", proxy="proxy_ppb")))
    pd.concat(pairs).sort_values(["station", "time_utc"]).to_csv(TABLES / "co2_ch4_proxy_points.csv", index=False)
    table = pd.DataFrame(rows)
    table.to_csv(TABLES / "co2_ch4_proxy_validation.csv", index=False)
    print(table.round(2).to_string(index=False), flush=True)
    return table


# ------------------------------------------------------------------ campaign

def run_dir(code: str, seed: int, stamp: pd.Timestamp) -> Path:
    return RUNS / f"{code.lower()}_s{seed}" / f"bkt_{stamp:%Y%m%dT%H%MZ}"


def receipt(directory: Path, code: str, stamp: pd.Timestamp, cfg, runtime: float | None) -> dict:
    """As a84.receipt, against this window's meteorology directory."""
    from dataclasses import asdict
    from datetime import datetime, timezone
    required = ("footprint.nc", "footprint_layers.nc", "PAR_GIS.txt", "MESSAGE", "CONTROL", "SETUP.CFG", "run_metadata.json")
    missing = [f for f in required if not (directory / f).is_file()]
    if missing:
        raise FileNotFoundError(f"Incomplete run {directory}: {missing}")
    meta = json.loads((directory / "run_metadata.json").read_text())
    if meta["configuration"] != asdict(cfg):
        raise ValueError(f"Configuration mismatch: {directory}")
    paths = met_paths(stamp)
    if meta["meteorology_files"] != [str(p.resolve()) for p in paths]:
        raise ValueError(f"Meteorology mismatch: {directory}")
    if (directory / "CONTROL").read_text() != T.model.control_text(stamp, paths, directory, cfg, T.EXTRA_LEVELS_M):
        raise ValueError(f"CONTROL does not encode the declared run: {directory}")
    actual = ext.actual_particles((directory / "MESSAGE").read_text(errors="replace"))
    if actual < cfg.particles:
        raise ValueError(f"Fewer particles emitted than requested: {directory}")
    return dict(station=code, receptor_utc=stamp.isoformat() + "Z", configuration=asdict(cfg), window="2024-10 to 2024-12",
                transport_options=asdict(T.model.TransportOptions()), extra_levels_m=list(T.EXTRA_LEVELS_M),
                meteorology_files=meta["meteorology_files"], actual_emitted_particles=actual,
                model_runtime_seconds=runtime if runtime is not None else meta.get("model_runtime_seconds"),
                hysplit_version_line=meta.get("hysplit_version_line"),
                output_sha256={f: T.model.sha256_file(directory / f) for f in required[:4]},
                created_at_utc=datetime.now(timezone.utc).isoformat())


def ensure_run(code: str, seed: int, stamp: pd.Timestamp, context: dict) -> float:
    import shutil, time
    from dataclasses import asdict
    cfg = T.base_config(code, seed)
    directory = run_dir(code, seed, stamp)
    if (directory / "completion_receipt.json").exists():
        if json.loads((directory / "completion_receipt.json").read_text())["configuration"] != asdict(cfg):
            raise ValueError(f"Existing receipt has different settings: {directory}")
        return 0.
    if directory.exists():
        shutil.rmtree(directory)
    started = time.monotonic()
    T.model.run_footprint(stamp, MET, directory.parent, T.HYSPLIT_HOME, cfg, False, meteorology_paths=met_paths(stamp),
                          transport=T.model.TransportOptions(), observation_context=context, extra_levels_m=T.EXTRA_LEVELS_M)
    T.model.run_checked([str(T.HYSPLIT_HOME / "exec/par2asc"), "-iPARDUMP", "-oendpoints.txt", "-vendpoint_times.txt", "-a1"], directory, "endpoints")
    (directory / "PARDUMP").unlink()
    elapsed = time.monotonic() - started
    (directory / "completion_receipt.json").write_text(json.dumps(receipt(directory, code, stamp, cfg, elapsed), indent=2) + "\n")
    return elapsed


def run(workers: int, attempts: int = 2) -> None:
    import time, traceback
    from concurrent.futures import as_completed
    if not (T.HYSPLIT_HOME / "exec/hycs_std").exists():
        raise FileNotFoundError(f"HYSPLIT not found at {T.HYSPLIT_HOME}")
    missing = [d for d in met_days() if not (MET / f"{d:%Y%m%d}_gfs0p25.json").exists()]
    if missing:
        raise FileNotFoundError(f"Meteorology incomplete; run fetch-met first: {len(missing)} days")
    observations = {code: T.station_frame(code) for code in T.STATIONS}
    jobs = [(code, seed, s) for code in T.STATIONS for seed in SEEDS for s in stamps()]
    contexts = {(code, s): T.observation_context(observations, code, s) for code in T.STATIONS for s in stamps()}
    started = time.monotonic(); failures = {}
    for attempt in range(1, attempts + 1):
        pending = [j for j in jobs if not (run_dir(*j) / "completion_receipt.json").exists()]
        print(f"attempt {attempt}: {len(jobs)} runs declared, {len(pending)} pending, {workers} workers", flush=True)
        if not pending:
            break
        failures = {}; done = 0
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(ensure_run, c, seed, s, contexts[(c, s)]): (c, seed, s) for c, seed, s in pending}
            for future in as_completed(futures):
                code, seed, s = futures[future]; done += 1
                try:
                    elapsed = future.result()
                except Exception:  # noqa: BLE001 - logged and retried
                    failures[(code, seed, s)] = traceback.format_exc()
                    print(f"[{done}/{len(pending)}] FAILED {code} s{seed} {s:%Y-%m-%dT%HZ}\n{failures[(code, seed, s)]}", flush=True)
                    continue
                print(f"[{done}/{len(pending)}] {code} s{seed} {s:%Y-%m-%dT%HZ} {elapsed/60:.1f} min (campaign {(time.monotonic()-started)/3600:.2f} h)", flush=True)
    if failures:
        raise RuntimeError(f"{len(failures)} runs failed after {attempts} attempts")
    print("2024 campaign complete", flush=True)


# ------------------------------------------------------------------ operator

def operator(allow_partial: bool = False) -> None:
    import xarray as xr
    from pyproj import Geod
    selection = receptors()[["station", "time_utc", "co2", "ch4", "holdout"]].drop_duplicates(["station", "time_utc"])
    with xr.open_dataset(C.INPUTS / "ctnrt_fluxes_box_2024.nc") as ds:
        box = ds.load()
    with xr.open_dataset(I.INPUTS / "diagnostic_biosphere_2024.nc") as ds:
        gpp = ds.gpp.values; resp = ds.resp.values; blat, blon = ds.lat.values, ds.lon.values
        bio_stamps = pd.DatetimeIndex(ds.time.values)
    centers = pd.DatetimeIndex(box.time.values)
    rows = []
    for code in T.STATIONS:
        lat, lon = T.receptor_grid(code)
        with xr.open_dataset(C.INPUTS / f"{code.lower()}_fossil_monthly_2024.nc") as ds:
            fossil = ds.load()
        total_fossil = fossil.flux.sum("sector")
        m_lat_box, m_lon_box = C.overlap_matrix(lat, box.lat.values, True), C.overlap_matrix(lon, box.lon.values)
        m_lat_bio = C.overlap_matrix(lat, blat, True).astype(np.float32); m_lon_bio = C.overlap_matrix(lon, blon).astype(np.float32)
        glat, glon = np.meshgrid(lat, lon, indexing="ij")
        _, rlat, rlon, _ = T.STATIONS[code]
        _, _, distance = Geod(ellps="WGS84").inv(np.full(glon.shape, rlon), np.full(glat.shape, rlat), glon, glat)
        near = distance / 1000 <= 500
        for stamp in stamps():
            dirs = [run_dir(code, seed, stamp) for seed in SEEDS]
            dirs = [d for d in dirs if (d / "completion_receipt.json").exists()]
            if len(dirs) != len(SEEDS):
                if not allow_partial or not dirs:
                    raise FileNotFoundError(f"Ensemble incomplete for {code} {stamp}: {len(dirs)} of {len(SEEDS)}")
            members = []
            for directory in dirs:
                field, meta, actual = ext.read_footprint(directory)
                hours = pd.DatetimeIndex(field.time.values); values = field.values
                row = dict(sensitivity=float(values.sum()))
                months = hours.to_period("M").to_timestamp()
                near_ppm = far_ppm = 0.
                for month in pd.unique(months):
                    contribution = values[months == month].sum(axis=0) * total_fossil.sel(month=month).values
                    near_ppm += contribution[near].sum(); far_ppm += contribution[~near].sum()
                row.update(fossil_near_ppm=near_ppm, fossil_far_ppm=far_ppm)
                coarse = C.aggregate(values, m_lat_box, m_lon_box)
                index = centers.get_indexer(C.three_hour_center(hours))
                if (index < 0).any():
                    raise ValueError(f"Footprint hours outside the CT-NRT record: {code} {stamp}")
                for name in ("ocean", "fire", "bio_day", "bio_night", "fossil_ctnrt", "bio_net"):
                    row[f"{name}_ppm"] = float(np.einsum("hij,hij->", coarse, box[name].values[index]))
                fine = C.aggregate(values.astype(np.float32), m_lat_bio, m_lon_bio)
                idx = bio_stamps.get_indexer(I.interval_end(hours)); i0, i1, w1 = I.temperature_weights(hours, bio_stamps)
                if (idx < 0).any() or (i0 < 0).any() or (i1 < 0).any():
                    raise ValueError(f"Footprint hours outside the biosphere prior: {code} {stamp}")
                resp_h = (1 - w1)[:, None, None] * resp[i0] + w1[:, None, None] * resp[i1]
                row.update(gpp_ppm=float(np.einsum("hij,hij->", fine, gpp[idx])), resp_ppm=float(np.einsum("hij,hij->", fine, resp_h)))
                active = ext.active_endpoints(directory, meta, actual)
                end = stamp - pd.Timedelta(hours=meta["configuration"]["hours_back"])
                row.update(C.endpoint_background(active, end, MET / f"{end:%Y%m%d}_gfs0p25"))
                row.update(retention=len(active) / actual)
                members.append(row)
            m = pd.DataFrame(members)
            numeric = [c for c in m.columns if c.endswith("_ppm") or c == "sensitivity"]
            out = dict(station=code, time_utc=stamp, members=len(m), **m[numeric].mean().to_dict(),
                       gpp_ppm_seed_sd=float(m.gpp_ppm.std(ddof=1)) if len(m) > 1 else np.nan,
                       resp_ppm_seed_sd=float(m.resp_ppm.std(ddof=1)) if len(m) > 1 else np.nan,
                       endpoint_survival_fraction=float(m.retention.min()), transport_usable=bool((m.retention >= .95).all()),
                       **T.native_surface(code, MET / f"{stamp:%Y%m%d}_gfs0p25", stamp))
            rows.append(out)
            print(f"2024 operator {code} {stamp:%Y-%m-%d}: gpp {out['gpp_ppm']:.1f} resp {out['resp_ppm']:.1f} "
                  f"fossil {out['fossil_near_ppm']:.2f} bg {out['background_ppm']:.2f} retention {out['endpoint_survival_fraction']:.3f}", flush=True)
    frame = pd.DataFrame(rows).merge(selection, on=["station", "time_utc"], validate="one_to_one")
    frame.to_csv(TABLES / "co2_operator_base_2024.csv", index=False)
    print(f"wrote {len(frame)} rows; usable {int(frame.transport_usable.sum())}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["select", "fetch-met", "fetch-inputs", "prepare", "observations", "validate-proxy", "run", "operator"])
    parser.add_argument("--workers", type=int, default=14)
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--interface", default=None)
    a = parser.parse_args()
    stages = {"select": select, "fetch-met": lambda: fetch_met(a.interface), "fetch-inputs": lambda: fetch_inputs(a.interface),
              "prepare": prepare, "observations": observations, "validate-proxy": validate_proxy,
              "run": lambda: run(a.workers), "operator": lambda: operator(a.allow_partial)}
    stages[a.stage]()


if __name__ == "__main__":
    main()
