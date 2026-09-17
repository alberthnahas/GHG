#!/usr/bin/env python3
"""Transport driver for any station and any episode: plan, fetch, run, convolve.

The monitor (a97) finds episodes from the observations alone. This attaches
transport to them, for any station in the archive, at its own inlet height.

Two directions, both from the same ensemble:
  backward   the footprint itself: where the air at the tower came from, and how
             much surface sensitivity sits in each cell;
  forward    that footprint convolved with a flux field, which predicts the
             enhancement the tower should have seen. This is the operator the
             inversions use (a84, a89), so a forward prediction here and an
             inversion there rest on the same transport.

Nothing runs by accident. `plan` touches no network and no model: it turns a
station and a window into the list of receptor hours, the meteorology days they
need, and what those cost in gigabytes and hours. Fetch and run act only on a
plan that already exists.

Costs are measured from this project's own campaigns, not assumed: the wide crop
is 457 MB per day (43 GB for the 94 days of the 2024 campaign), NOAA server-side
extraction runs about 4 minutes per day when the queue is responsive, and a
120 h backward run of 2,000 particles takes a median of 59 minutes (252 runs).

Stages
  plan        receptor hours, meteorology days and their cost; writes the plan
  fetch-met   NOAA READY crop for the planned days, resumable, one day at a time
  run         the HYSPLIT ensemble for the planned receptors, resumable
  influence   footprint diagnostics per receptor, and a flux convolution when a
              flux field is supplied
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, replace
import json
from pathlib import Path
import shutil
import time
import traceback

import numpy as np
import pandas as pd

import a37_bkt_footprint as model
import a71_domain_budget_extension as ext
import a84_bkt_jmb_two_receptor as T
import ghg_common as G

ROOT = T.ROOT
OUT = ROOT / "outputs/operational"
MET_ROOT = ROOT / "data/hysplit/gfs0p25"
RUN_ROOT = ROOT / "outputs/hysplit/episodes"
INLET_HEIGHT_M = {"BKT": 100., "JMB": 100., "KMY": 30., "PLU": 30., "SRG": 30.}
INLET_SOURCE = {"BKT": "tower measurement height supplied for the two-receptor study",
                "JMB": "tower measurement height supplied for the two-receptor study",
                "KMY": "supplied 2026-09-17", "PLU": "supplied 2026-09-17", "SRG": "supplied 2026-09-17"}
SEEDS = T.SEEDS
HOURS_BACK = T.HOURS_BACK
AFTERNOON_SOLAR = (12., 16.)
MET_MB_PER_DAY, MET_MINUTES_PER_DAY, RUN_MINUTES = 457., 4., 59.
PLAN = OUT / "transport_plan.csv"


def station(code: str) -> tuple[str, float, float, float, float]:
    """Name, latitude, longitude, elevation and inlet height for one station."""
    if code not in G.STATIONS:
        raise KeyError(f"Unknown station {code}; the archive has {sorted(G.STATIONS)}")
    if code not in INLET_HEIGHT_M:
        raise KeyError(f"No inlet height recorded for {code}; add it to INLET_HEIGHT_M before planning runs")
    name, _, lat, lon, elevation, _, _ = G.STATIONS[code]
    return name, float(lat), float(lon), float(elevation), INLET_HEIGHT_M[code]


def config(code: str, seed: int = 0) -> model.FootprintConfig:
    """The a84 ensemble settings, at this station's own position and inlet height."""
    _, lat, lon, elevation, inlet = station(code)
    return replace(T.base_config("BKT", seed), receptor_lat=lat, receptor_lon=lon,
                   station_elevation_m_msl=elevation, receptor_height_m_agl=inlet)


def met_dir(label: str) -> Path:
    return MET_ROOT / f"episode_{label}"


def run_dir(label: str, code: str, seed: int, stamp: pd.Timestamp) -> Path:
    return RUN_ROOT / label / f"{code.lower()}_s{seed}" / f"{code.lower()}_{stamp:%Y%m%dT%H%MZ}"


def receptor_hours(code: str, first: pd.Timestamp, last: pd.Timestamp, hours: str = "afternoon") -> list[pd.Timestamp]:
    """Hours to simulate inside a window, with the observation present.

    Nights are offered but not the default: a quarter-degree model cannot carry
    the shallow nocturnal layer these towers sit in (a89), so a night receptor
    produces a footprint the observation will not test.
    """
    _, _, lon, _, _ = station(code)
    record = G.apply_flags(G.load_station(code)).set_index("time_utc").sort_index()
    index = pd.date_range(pd.Timestamp(first).floor("h"), pd.Timestamp(last).ceil("h"), freq="h")
    present = record.reindex(index)
    solar = (index.hour + index.minute / 60 + lon / 15) % 24
    keep = present[["co2", "ch4", "co"]].notna().any(axis=1).to_numpy() if len(present) else np.zeros(len(index), bool)
    if hours == "afternoon":
        keep &= (solar >= AFTERNOON_SOLAR[0]) & (solar < AFTERNOON_SOLAR[1])
    elif hours != "all":
        raise ValueError("hours must be 'afternoon' or 'all'")
    return list(index[keep])


def meteorology_days(stamps: list[pd.Timestamp]) -> pd.DatetimeIndex:
    if not stamps:
        return pd.DatetimeIndex([])
    first = min(stamps) - pd.Timedelta(hours=HOURS_BACK)
    return pd.date_range(first.normalize(), max(stamps).normalize(), freq="D")


def episode_window(rank: int | None, station_code: str | None) -> tuple[str, str, pd.Timestamp, pd.Timestamp]:
    """Pick an episode from the a97 catalogue by strength, optionally at one station."""
    path = OUT / "episodes.csv"
    if not path.exists():
        raise FileNotFoundError(f"Run the a97 monitor first: {path}")
    table = pd.read_csv(path, parse_dates=["start", "end"])
    if station_code:
        table = table[table.station.eq(station_code)]
    if table.empty:
        raise ValueError("No episodes match that station")
    table = table.sort_values("peak_co_enhancement_ppb", ascending=False).reset_index(drop=True)
    row = table.iloc[(rank or 1) - 1]
    label = f"{row.station.lower()}_{row.start:%Y%m%d}"
    return label, str(row.station), row.start, row.end


def plan(codes: list[str], first: pd.Timestamp, last: pd.Timestamp, label: str, hours: str, workers: int) -> pd.DataFrame:
    rows, notes = [], []
    for code in codes:
        stamps = receptor_hours(code, first, last, hours)
        if not stamps:
            # an empty plan has to say why: silence here would look like a broken tool
            everything = receptor_hours(code, first, last, "all")
            if not everything:
                notes.append(f"{code}: no observed hour in this window, so there is nothing to simulate")
            else:
                notes.append(f"{code}: {len(everything)} observed hours, none of them between "
                             f"{AFTERNOON_SOLAR[0]:.0f} and {AFTERNOON_SOLAR[1]:.0f} local solar. This window is nocturnal; "
                             "rerun with --hours all if you want it, knowing a quarter-degree model cannot carry the "
                             "shallow night layer (a89)")
        days = meteorology_days(stamps)
        rows.append(dict(label=label, station=code, inlet_height_m=INLET_HEIGHT_M[code], inlet_source=INLET_SOURCE[code],
                         window_start=first, window_end=last, hours=hours, receptors=len(stamps),
                         seeds=len(SEEDS), runs=len(stamps) * len(SEEDS),
                         meteorology_days=len(days),
                         meteorology_from=days[0] if len(days) else pd.NaT, meteorology_to=days[-1] if len(days) else pd.NaT))
    table = pd.DataFrame(rows)
    shared = sorted({day for code in codes for day in meteorology_days(receptor_hours(code, first, last, hours))})
    already = sum(1 for day in shared if (met_dir(label) / f"{day:%Y%m%d}_gfs0p25.json").exists())
    missing = len(shared) - already
    table["shared_meteorology_days"] = len(shared)
    table["meteorology_days_missing"] = missing
    table["download_gb"] = round(missing * MET_MB_PER_DAY / 1024, 1)
    table["download_hours"] = round(missing * MET_MINUTES_PER_DAY / 60, 1)
    table["run_hours"] = round(table.runs.sum() * RUN_MINUTES / 60 / max(workers, 1), 1)
    OUT.mkdir(parents=True, exist_ok=True)
    table.to_csv(PLAN, index=False)
    print(table[["label", "station", "inlet_height_m", "receptors", "runs", "meteorology_days"]].to_string(index=False), flush=True)
    for note in notes:
        print(f"note: {note}", flush=True)
    print(f"\nshared meteorology days {len(shared)}, of which {missing} are not on disk"
          f"\nestimated download {table.download_gb.iloc[0]:.1f} GB over about {table.download_hours.iloc[0]:.1f} h"
          f"\nestimated model time {table.run_hours.iloc[0]:.1f} h on {workers} workers"
          f"\nplan written to {PLAN}", flush=True)
    return table


def load_plan(label: str) -> pd.DataFrame:
    if not PLAN.exists():
        raise FileNotFoundError(f"Run the plan stage first: {PLAN}")
    table = pd.read_csv(PLAN, parse_dates=["window_start", "window_end", "meteorology_from", "meteorology_to"])
    table = table[table.label.eq(label)]
    if table.empty:
        raise ValueError(f"No plan for {label}; run the plan stage for it")
    return table


def fetch_met(label: str, interface: str | None = None, passes: int = 6, pause_s: int = 60) -> None:
    """NOAA READY crop, one day at a time, resumable through its job files."""
    import a41_bkt_gfs_driver as gfs
    table = load_plan(label)
    first, last = table.window_start.min(), table.window_end.max()
    days = meteorology_days([pd.Timestamp(first), pd.Timestamp(last)])
    directory = met_dir(label)
    directory.mkdir(parents=True, exist_ok=True)
    if interface:
        T.bind_interface(interface)
    for attempt in range(1, passes + 1):
        pending = [d for d in days if not (directory / f"{d:%Y%m%d}_gfs0p25.json").exists()]
        print(f"pass {attempt}: {len(pending)} of {len(days)} days pending", flush=True)
        if not pending:
            break
        for day in pending:
            try:
                gfs.regional_extract(dates=[f"{day:%Y-%m-%d}"], bounds=ext.WIDE_BOUNDS, directory=directory)
            except Exception as error:  # noqa: BLE001 - transient NOAA errors are retried on the next pass
                print(f"  {day:%Y-%m-%d} failed: {type(error).__name__}: {error}", flush=True)
                time.sleep(pause_s)
    missing = [d for d in days if not (directory / f"{d:%Y%m%d}_gfs0p25.json").exists()]
    if missing:
        raise FileNotFoundError(f"Meteorology incomplete after {passes} passes: {len(missing)} days")
    print(f"meteorology complete: {len(days)} days in {directory}", flush=True)


def met_paths(label: str, stamp: pd.Timestamp) -> list[Path]:
    days = pd.date_range((stamp - pd.Timedelta(hours=HOURS_BACK)).normalize(), stamp.normalize(), freq="D")
    return [met_dir(label) / f"{day:%Y%m%d}_gfs0p25.gbl" for day in days]


def ensure_run(label: str, code: str, seed: int, stamp: pd.Timestamp, context: dict) -> float:
    cfg = config(code, seed)
    directory = run_dir(label, code, seed, stamp)
    receipt = directory / "completion_receipt.json"
    if receipt.exists():
        if json.loads(receipt.read_text())["configuration"] != asdict(cfg):
            raise ValueError(f"Existing receipt has different settings: {directory}")
        return 0.
    if directory.exists():
        shutil.rmtree(directory)
    started = time.monotonic()
    model.run_footprint(stamp, met_dir(label), directory.parent, T.HYSPLIT_HOME, cfg, False,
                        meteorology_paths=met_paths(label, stamp), transport=model.TransportOptions(),
                        observation_context=context, extra_levels_m=T.EXTRA_LEVELS_M)
    model.run_checked([str(T.HYSPLIT_HOME / "exec/par2asc"), "-iPARDUMP", "-oendpoints.txt",
                       "-vendpoint_times.txt", "-a1"], directory, "endpoints")
    (directory / "PARDUMP").unlink(missing_ok=True)
    elapsed = time.monotonic() - started
    record = T.receipt(directory, code, stamp, cfg, elapsed)
    record.update(campaign=f"a98 episode transport {label}", inlet_height_m=INLET_HEIGHT_M[code],
                  inlet_source=INLET_SOURCE[code])
    receipt.write_text(json.dumps(record, indent=2) + "\n")
    return elapsed


def run(label: str, workers: int = 12, attempts: int = 2) -> None:
    if not (T.HYSPLIT_HOME / "exec/hycs_std").exists():
        raise FileNotFoundError(f"HYSPLIT not found at {T.HYSPLIT_HOME}")
    table = load_plan(label)
    jobs, contexts = [], {}
    for row in table.itertuples():
        stamps = receptor_hours(row.station, row.window_start, row.window_end, row.hours)
        observations = {row.station: T.station_frame(row.station)}
        for stamp in stamps:
            contexts[(row.station, stamp)] = T.observation_context(observations, row.station, stamp)
            jobs += [(row.station, seed, stamp) for seed in SEEDS]
    started = time.monotonic(); failures = {}
    for attempt in range(1, attempts + 1):
        pending = [j for j in jobs if not (run_dir(label, *j) / "completion_receipt.json").exists()]
        print(f"attempt {attempt}: {len(jobs)} runs declared, {len(pending)} pending, {workers} workers", flush=True)
        if not pending:
            break
        failures = {}; done = 0
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(ensure_run, label, code, seed, stamp, contexts[(code, stamp)]): (code, seed, stamp)
                       for code, seed, stamp in pending}
            for future in as_completed(futures):
                code, seed, stamp = futures[future]; done += 1
                try:
                    elapsed = future.result()
                except Exception:  # noqa: BLE001 - logged and retried
                    failures[(code, seed, stamp)] = traceback.format_exc()
                    print(f"[{done}/{len(pending)}] FAILED {code} s{seed} {stamp:%Y-%m-%dT%HZ}\n{failures[(code, seed, stamp)]}", flush=True)
                    continue
                print(f"[{done}/{len(pending)}] {code} s{seed} {stamp:%Y-%m-%dT%HZ} {elapsed/60:.1f} min "
                      f"(campaign {(time.monotonic()-started)/3600:.2f} h)", flush=True)
    if failures:
        raise RuntimeError(f"{len(failures)} runs failed after {attempts} attempts")
    print(f"episode campaign complete: {label}", flush=True)


def influence(label: str, flux: Path | None = None, variable: str | None = None) -> None:
    """Footprint diagnostics per receptor, and the forward convolution when a flux field is given."""
    import xarray as xr
    from pyproj import Geod
    table = load_plan(label)
    rows = []
    field = None
    if flux is not None:
        with xr.open_dataset(flux) as ds:
            field = ds[variable or list(ds.data_vars)[0]].load()
    for row in table.itertuples():
        code = row.station
        _, lat0, lon0, _, _ = station(code)
        for stamp in receptor_hours(code, row.window_start, row.window_end, row.hours):
            members = []
            for seed in SEEDS:
                directory = run_dir(label, code, seed, stamp)
                if not (directory / "completion_receipt.json").exists():
                    raise FileNotFoundError(f"Run incomplete: {directory}")
                footprint, meta, actual = ext.read_footprint(directory)
                values = footprint.values.sum(axis=0)
                grid_lat, grid_lon = footprint.lat.values, footprint.lon.values
                mesh_lat, mesh_lon = np.meshgrid(grid_lat, grid_lon, indexing="ij")
                _, _, distance = Geod(ellps="WGS84").inv(np.full(mesh_lon.shape, lon0), np.full(mesh_lat.shape, lat0),
                                                         mesh_lon, mesh_lat)
                distance /= 1000.
                total = float(values.sum())
                entry = dict(station=code, time_utc=stamp, seed=seed, sensitivity=total,
                             within_50km_percent=100 * float(values[distance <= 50].sum()) / total if total else np.nan,
                             within_500km_percent=100 * float(values[distance <= 500].sum()) / total if total else np.nan,
                             endpoint_survival_fraction=len(ext.active_endpoints(directory, meta, actual)) / actual)
                if field is not None:
                    aligned = field.interp(lat=("cell", mesh_lat.ravel()), lon=("cell", mesh_lon.ravel())).values.reshape(values.shape)
                    entry["predicted_enhancement"] = float(np.nansum(values * aligned))
                members.append(entry)
            frame = pd.DataFrame(members)
            numeric = [c for c in frame.columns if c not in ("station", "time_utc", "seed")]
            rows.append(dict(station=code, time_utc=stamp, members=len(frame), **frame[numeric].mean().to_dict(),
                             sensitivity_seed_sd=float(frame.sensitivity.std(ddof=1)) if len(frame) > 1 else np.nan))
    out = pd.DataFrame(rows)
    destination = OUT / f"influence_{label}.csv"
    out.to_csv(destination, index=False)
    print(f"wrote {len(out)} receptors to {destination}", flush=True)
    if len(out):
        print(out.round(3).to_string(index=False), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["plan", "fetch-met", "run", "influence"])
    parser.add_argument("--stations", nargs="*", default=["BKT"], help="station codes to simulate")
    parser.add_argument("--window", nargs=2, metavar=("START", "END"), help="explicit UTC window")
    parser.add_argument("--episode-rank", type=int, help="take the nth strongest episode from the a97 catalogue")
    parser.add_argument("--episode-station", help="restrict the episode search to one station")
    parser.add_argument("--label", help="campaign label; derived from the episode when omitted")
    parser.add_argument("--hours", choices=["afternoon", "all"], default="afternoon")
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--interface", help="bind downloads to one network interface")
    parser.add_argument("--flux", type=Path, help="flux field to convolve with the footprints")
    parser.add_argument("--variable", help="variable within the flux field")
    a = parser.parse_args()

    if a.stage == "plan":
        if a.window:
            first, last = pd.Timestamp(a.window[0]), pd.Timestamp(a.window[1])
            label = a.label or f"{'_'.join(c.lower() for c in a.stations)}_{first:%Y%m%d}"
            codes = a.stations
        else:
            label, code, first, last = episode_window(a.episode_rank, a.episode_station)
            label = a.label or label
            codes = a.stations if a.stations != ["BKT"] else [code]
        plan(codes, first, last, label, a.hours, a.workers)
        return
    label = a.label
    if not label:
        raise SystemExit("--label is required for fetch-met, run and influence")
    if a.stage == "fetch-met":
        fetch_met(label, a.interface)
    elif a.stage == "run":
        run(label, a.workers)
    else:
        influence(label, a.flux, a.variable)


if __name__ == "__main__":
    main()
