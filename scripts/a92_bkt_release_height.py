#!/usr/bin/env python3
"""BKT release-height sensitivity for the daytime CO2 model.

The a84 ensemble releases BKT particles 100 m above GFS model ground. The GFS
0.25 degree terrain in the BKT receptor cell is 816 m, the station is at
864.5 m and the inlet is taken at 100 m, so the modeled release sits about
48 m below the true inlet altitude, on a smoothed mountain. This campaign
reruns the BKT 06 UTC (13 WIB) receptors used by the daytime CO2 experiments
(transport usable at 100 m, afternoon observation mean, GFS mixing depth at
least 300 m) at

  150 m above model ground: the true inlet altitude (964.5 m) over GFS terrain;
  300 m above model ground: a release well above the smoothed surface.

Settings are otherwise identical to a84: HYSPLIT 5.4.2 STILT, 120 h backward,
three seeds of 2,000 particles, GFS 0.25 wide crop, 60 x 100 degree grid,
1,000 m extra layer.

Stages
  run        HYSPLIT campaign (resumable, receipts per run)
  operator   CO2 operator for the new BKT runs: EDGAR fossil, CT-NRT ocean, fire and
             endpoint background, diagnostic biosphere, particle retention
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, replace
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import time
import traceback

import numpy as np
import pandas as pd
import xarray as xr
from pyproj import Geod

import a71_domain_budget_extension as ext
import a84_bkt_jmb_two_receptor as T
import a89_bkt_jmb_co2 as C
import a90_bkt_jmb_co2_improved as I

HEIGHTS_M = (150., 300.)
RUNS = T.OUT / "runs_bkt_height"
TABLES = T.TABLES
RETENTION_SCREEN = .95


def stamps() -> list[pd.Timestamp]:
    import a91_bkt_jmb_co2_experiments as X
    frame = X.receptor_frame("")
    return sorted(frame.loc[frame.station.eq("BKT"), "time_utc"])


def config(height: float, seed: int):
    return replace(T.base_config("BKT", seed), receptor_height_m_agl=float(height))


def run_dir(height: float, seed: int, stamp: pd.Timestamp) -> Path:
    return RUNS / f"bkt_h{int(height)}_s{seed}" / f"bkt_{stamp:%Y%m%dT%H%MZ}"


def ensure_run(height: float, seed: int, stamp: pd.Timestamp, context: dict) -> float:
    cfg = config(height, seed)
    directory = run_dir(height, seed, stamp)
    if (directory / "completion_receipt.json").exists():
        if json.loads((directory / "completion_receipt.json").read_text())["configuration"] != asdict(cfg):
            raise ValueError(f"Existing receipt has different settings: {directory}")
        return 0.
    if directory.exists():
        shutil.rmtree(directory)
    started = time.monotonic()
    T.model.run_footprint(stamp, T.MET, directory.parent, T.HYSPLIT_HOME, cfg, False, meteorology_paths=T.met_paths(stamp),
                          transport=T.model.TransportOptions(), observation_context=context, extra_levels_m=T.EXTRA_LEVELS_M)
    T.model.run_checked([str(T.HYSPLIT_HOME / "exec/par2asc"), "-iPARDUMP", "-oendpoints.txt", "-vendpoint_times.txt", "-a1"], directory, "endpoints")
    (directory / "PARDUMP").unlink()
    elapsed = time.monotonic() - started
    record = T.receipt(directory, "BKT", stamp, cfg, elapsed)
    record.update(release_height_m_agl=float(height), campaign="a92 BKT release-height sensitivity")
    (directory / "completion_receipt.json").write_text(json.dumps(record, indent=2) + "\n")
    return elapsed


def run(workers: int, attempts: int = 2) -> None:
    if not (T.HYSPLIT_HOME / "exec/hycs_std").exists():
        raise FileNotFoundError(f"HYSPLIT not found at {T.HYSPLIT_HOME}")
    observations = {"BKT": T.station_frame("BKT")}
    jobs = [(h, seed, s) for h in sorted(HEIGHTS_M, reverse=True) for seed in T.SEEDS for s in stamps()]   # 300 m first
    contexts = {s: {**T.observation_context(observations, "BKT", s), "release_height_note": "a92 release-height sensitivity"} for s in stamps()}
    started = time.monotonic(); failures = {}
    for attempt in range(1, attempts + 1):
        pending = [j for j in jobs if not (run_dir(*j) / "completion_receipt.json").exists()]
        print(f"attempt {attempt}: {len(jobs)} runs declared, {len(pending)} pending, {workers} workers", flush=True)
        if not pending:
            break
        failures = {}; done = 0
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(ensure_run, h, seed, s, contexts[s]): (h, seed, s) for h, seed, s in pending}
            for future in as_completed(futures):
                h, seed, s = futures[future]; done += 1
                try:
                    elapsed = future.result()
                except Exception:  # noqa: BLE001 - logged and retried
                    failures[(h, seed, s)] = traceback.format_exc()
                    print(f"[{done}/{len(pending)}] FAILED h{int(h)} s{seed} {s:%Y-%m-%dT%HZ}\n{failures[(h, seed, s)]}", flush=True)
                    continue
                print(f"[{done}/{len(pending)}] h{int(h)} s{seed} {s:%Y-%m-%dT%HZ} {elapsed/60:.1f} min (campaign {(time.monotonic()-started)/3600:.2f} h)", flush=True)
    if failures:
        raise RuntimeError(f"{len(failures)} runs failed after {attempts} attempts")
    print("release-height campaign complete", flush=True)


def operator() -> None:
    """CO2 operator columns for the BKT runs at each release height, matching co2_operator_base and the diagnostic operator."""
    lat, lon = T.receptor_grid("BKT")
    with xr.open_dataset(C.INPUTS / "bkt_fossil_monthly.nc") as ds:
        fossil = ds.load()
    with xr.open_dataset(C.INPUTS / "ctnrt_fluxes_box.nc") as ds:
        box = ds.load()
    with xr.open_dataset(I.INPUTS / "diagnostic_biosphere.nc") as ds:
        gpp = ds.gpp.values; resp = ds.resp.values; blat, blon = ds.lat.values, ds.lon.values
        bio_stamps = pd.DatetimeIndex(ds.time.values)
    centers = pd.DatetimeIndex(box.time.values)
    m_lat_box, m_lon_box = C.overlap_matrix(lat, box.lat.values, True), C.overlap_matrix(lon, box.lon.values)
    m_lat_bio, m_lon_bio = C.overlap_matrix(lat, blat, True).astype(np.float32), C.overlap_matrix(lon, blon).astype(np.float32)
    glat, glon = np.meshgrid(lat, lon, indexing="ij")
    _, rlat, rlon, _ = T.STATIONS["BKT"]
    _, _, distance = Geod(ellps="WGS84").inv(np.full(glon.shape, rlon), np.full(glat.shape, rlat), glon, glat)
    near = distance / 1000 <= 500
    total_fossil = fossil.flux.sum("sector")
    rows = []
    for height in HEIGHTS_M:
        if not all((run_dir(height, seed, s) / "completion_receipt.json").exists() for seed in T.SEEDS for s in stamps()):
            print(f"h{int(height)}: runs incomplete, skipped", flush=True)
            continue
        for stamp in stamps():
            members = []
            for seed in T.SEEDS:
                directory = run_dir(height, seed, stamp)
                if not (directory / "completion_receipt.json").exists():
                    raise FileNotFoundError(f"Run incomplete: {directory}")
                field, meta, actual = ext.read_footprint(directory)
                hours = pd.DatetimeIndex(field.time.values); values = field.values
                row = dict(seed=seed, sensitivity=float(values.sum()))
                months = hours.to_period("M").to_timestamp()
                near_ppm = far_ppm = 0.
                for month in pd.unique(months):
                    contribution = values[months == month].sum(axis=0) * total_fossil.sel(month=month).values
                    near_ppm += contribution[near].sum(); far_ppm += contribution[~near].sum()
                row.update(fossil_near_ppm=near_ppm, fossil_far_ppm=far_ppm)
                coarse = C.aggregate(values, m_lat_box, m_lon_box)
                index = centers.get_indexer(C.three_hour_center(hours))
                for name in ("ocean", "fire", "bio_day", "bio_night"):
                    row[f"{name}_ppm"] = float(np.einsum("hij,hij->", coarse, box[name].values[index]))
                fine = C.aggregate(values.astype(np.float32), m_lat_bio, m_lon_bio)
                idx = bio_stamps.get_indexer(I.interval_end(hours)); i0, i1, w1 = I.temperature_weights(hours, bio_stamps)
                resp_h = (1 - w1)[:, None, None] * resp[i0] + w1[:, None, None] * resp[i1]
                row.update(gpp_ppm=float(np.einsum("hij,hij->", fine, gpp[idx])), resp_ppm=float(np.einsum("hij,hij->", fine, resp_h)))
                active = ext.active_endpoints(directory, meta, actual)
                end = stamp - pd.Timedelta(hours=meta["configuration"]["hours_back"])
                row.update(C.endpoint_background(active, end, T.MET / f"{end:%Y%m%d}_gfs0p25"))
                row.update(retention=len(active) / actual)
                members.append(row)
            m = pd.DataFrame(members)
            numeric = [c for c in m.columns if c.endswith("_ppm") or c == "sensitivity"]
            out = dict(station="BKT", time_utc=stamp, release_height_m=height, **m[numeric].mean().to_dict(),
                       gpp_ppm_seed_sd=float(m.gpp_ppm.std(ddof=1)), resp_ppm_seed_sd=float(m.resp_ppm.std(ddof=1)),
                       endpoint_survival_fraction=float(m.retention.min()), transport_usable=bool((m.retention >= RETENTION_SCREEN).all()))
            rows.append(out)
            print(f"h{int(height)} {stamp:%Y-%m-%d}: gpp {out['gpp_ppm']:.1f} resp {out['resp_ppm']:.1f} fossil {out['fossil_near_ppm']:.2f} "
                  f"bg {out['background_ppm']:.2f} retention {out['endpoint_survival_fraction']:.3f}", flush=True)
    pd.DataFrame(rows).to_csv(TABLES / "co2_bkt_height_operator.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["run", "operator"])
    parser.add_argument("--workers", type=int, default=12)
    a = parser.parse_args()
    run(a.workers) if a.stage == "run" else operator()


if __name__ == "__main__":
    main()
