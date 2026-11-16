#!/usr/bin/env python3
"""Three-driver transport test for 2025: GDAS1 1 degree, ERA5 0.25 degree, GFS 0.25 degree.

Question: does the choice of global meteorological driver for HYSPLIT-STILT
change what the inversion sees at the scale it works at (monthly means,
province groups)?  The 2025 GDAS1 footprints of a127 are the reference; a
subset of their receptors is rerun with ERA5 and GFS 0.25 with the identical
configuration (hycs_std ICHEM=8, 2000 particles, 120 h backward, 0.25 degree
output on the 60 x 100 degree tower grid, 100 m inlet, seed 0, 06 UTC), and
20 receptors are rerun with GDAS1 and a second seed (-10, the project's second
seed) as the particle-noise floor.

Meteorology domain for ERA5 and GFS: the a76 box, 70-140E, 25S-20N.  The GDAS1
reference footprints put 0.26 percent of their 120 h surface sensitivity (mean
over 39 sampled receptors, maximum 6.4 percent) outside that box, so the box
is wide enough for the province-scale question; particles that leave it end.
ERA5 uses the a76 request (16 pressure levels 1000-100 hPa, hourly, 0.25 degree)
and the a76 era52arl table with the corrected heat-flux sign.  GFS 0.25 is the
NOAA READY server-side crop of the 3-hourly hybrid-level ARL archive (a41).

Stages
  select        receptor table (every third 2025 receptor per tower, at least
                four per month) and the 20 seed-noise receptors
  probe         one day of each driver: sizes and times, then the estimate
  fetch-era5    CDS requests (cdsapi only) and era52arl conversion, chronological
  fetch-gfs     READY crops, chronological
  run           HYSPLIT jobs as their meteorology arrives (<= 4 workers)
  operator      a128 operator (and a131 fossil CO2) on every driver's footprints
  status        progress table into STATUS.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, FIRST_COMPLETED
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G
import a127_hysplit_2025_2026 as H

ROOT = G.ROOT
OUT = G.OUT / "hysplit" / "driver_test_2025"
RUNS = OUT / "runs"
ERA5 = ROOT / "data/hysplit/era5_2025"
ERA5_GRIB = ERA5 / "grib"
ERA5_ARL = ERA5 / "arl"
GFS = ROOT / "data/hysplit/gfs0p25_2025"
BOX = (70.0, -25.0, 140.0, 20.0)            # W, S, E, N; = a76 AREA [20, 70, -25, 140]
DRIVERS = ("gdas1", "era5", "gfs0p25")
SEED2 = -10
HOURS_BACK = H.HOURS_BACK
LABELS = {
    "gdas1": "NOAA NCEP GDAS1 analysis, 1 degree, ARL format",
    "era5": "ECMWF ERA5 reanalysis, 0.25 degree, hourly, 16 pressure levels, 70-140E 25S-20N, ARL format via era52arl",
    "gfs0p25": "NOAA GFS 0.25-degree pseudo-analysis, 3-hourly, hybrid levels, READY crop 70-140E 25S-20N, ARL format",
}
MAX_WORKERS = 4
A127_RUN_DIR = H.run_dir          # bound at import so later monkeypatching of a127 cannot redirect it


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(16 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def log(msg: str) -> None:
    print(f"{pd.Timestamp.now(tz='UTC'):%Y-%m-%dT%H:%M:%SZ} {msg}", flush=True)


# ------------------------------------------------------------------ selection
def select() -> pd.DataFrame:
    base = pd.read_csv(H.TABLES / "receptors_2025_2026.csv", parse_dates=["time_utc"])
    base = base[base.time_utc.dt.year == 2025]
    base = base[[(H.run_dir(r.station, r.time_utc) / "completion_receipt.json").exists() for r in base.itertuples()]]
    rows = []
    for st in H.STATIONS:
        b = base[base.station == st].sort_values("time_utc").reset_index(drop=True)
        chosen = set(b.index[::3])
        added = set()
        for m in range(1, 13):
            inm = b.index[b.time_utc.dt.month == m]
            have = [i for i in inm if i in chosen]
            rest = [i for i in inm if i not in chosen]
            while len(have) < 4 and rest:
                # the remaining date farthest from the dates already chosen in that month
                pick = max(rest, key=lambda i: min([abs((b.time_utc[i] - b.time_utc[j]).days) for j in have] or [99]))
                have.append(pick); rest.remove(pick); chosen.add(pick); added.add(pick)
        for i in sorted(chosen):
            rows.append(dict(station=st, time_utc=b.time_utc[i], window=b.window[i], added_thin_month=i in added))
    t = pd.DataFrame(rows).sort_values(["time_utc", "station"]).reset_index(drop=True)
    t["seed_noise"] = False
    for st in H.STATIONS:
        idx = t.index[t.station == st]
        pick = idx[np.round(np.linspace(0, len(idx) - 1, 10)).astype(int)]
        t.loc[pick, "seed_noise"] = True
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "receptors.csv", index=False)
    print(t.groupby(["station", t.time_utc.dt.month]).size().unstack().to_string())
    print(t.groupby("station").agg(n=("time_utc", "size"), added=("added_thin_month", "sum"), seed=("seed_noise", "sum")))
    days = met_days(t)
    print(f"{len(days)} meteorology days, {days[0].date()} to {days[-1].date()}")
    return t


def receptors() -> pd.DataFrame:
    return pd.read_csv(OUT / "receptors.csv", parse_dates=["time_utc"])


def stamp_days(stamp: pd.Timestamp) -> pd.DatetimeIndex:
    return pd.date_range((stamp - pd.Timedelta(hours=HOURS_BACK)).normalize(), stamp.normalize(), freq="D")


def met_days(t: pd.DataFrame | None = None) -> pd.DatetimeIndex:
    t = receptors() if t is None else t
    days = set()
    for s in sorted(t.time_utc.unique()):
        days.update(stamp_days(pd.Timestamp(s)))
    return pd.DatetimeIndex(sorted(days))


# ------------------------------------------------------------------- ERA5
def era5_mod():
    """a76 with its paths redirected to this campaign (in this process only)."""
    import a76_bkt_era5_driver as A
    A.GRIB, A.ARL = ERA5_GRIB, ERA5_ARL
    return A


def era5_grib(day, kind) -> Path:
    return ERA5_GRIB / f"{day:%Y%m%d}_{kind}.grib"


def era5_arl(day) -> Path:
    return ERA5_ARL / f"{day:%Y%m%d}_era5"


def era5_fetch_day_kind(client, day, kind) -> dict:
    A = era5_mod()
    target = era5_grib(day, kind)
    rec = target.with_suffix(".grib.json")
    if rec.exists():
        return json.loads(rec.read_text())
    dataset, body = A.request(kind, day)
    if body["area"] != [BOX[3], BOX[0], BOX[1], BOX[2]] or body["grid"] != [0.25, 0.25]:
        raise ValueError("ERA5 request differs from the declared box or grid")
    started = time.monotonic()
    partial = target.with_suffix(".grib.part")
    result = client.retrieve(dataset, body)
    location = getattr(result, "location", None)
    result.download(str(partial))
    if not partial.is_file() or partial.stat().st_size < 1_000_000:
        raise RuntimeError(f"CDS delivered an implausibly small file: {partial}")
    partial.replace(target)
    record = dict(dataset=dataset, request=body, provider="Copernicus Climate Data Store, ECMWF ERA5",
                  api="cdsapi (credentials read by the client from its own configuration)",
                  api_url=getattr(client, "url", None), download_url=location,
                  filename=target.name, bytes=target.stat().st_size, sha256=sha256(target),
                  retrieved_at_utc=now(), seconds=time.monotonic() - started, licence="CC-BY-4.0 (Copernicus C3S)")
    rec.write_text(json.dumps(record, indent=2) + "\n")
    return record


def era5_convert(day) -> None:
    A = era5_mod()
    target = era5_arl(day)
    if target.with_suffix(".json").exists():
        return
    A.convert(pd.DatetimeIndex([day]))
    meta = json.loads(target.with_suffix(".json").read_text())
    if "-0.00028" not in meta["cfg"] or "negated" not in meta["flux_sign"]:
        raise ValueError(f"ERA5 conversion without the heat-flux sign fix: {target}")


def fetch_era5(workers: int, interface: str | None, days: pd.DatetimeIndex | None = None) -> None:
    import cdsapi
    A = era5_mod()
    if interface:
        A.bind_interface(interface)
    ERA5_GRIB.mkdir(parents=True, exist_ok=True); ERA5_ARL.mkdir(parents=True, exist_ok=True)
    client = cdsapi.Client(quiet=True, progress=False)
    days = met_days() if days is None else days
    jobs = [(d, k) for d in days for k in ("pl", "sfc", "fc") if not era5_grib(d, k).with_suffix(".grib.json").exists()]
    log(f"ERA5: {len(days)} days, {len(jobs)} CDS requests pending, {workers} parallel")
    for d in days:                                   # days already complete but not converted
        if all(era5_grib(d, k).with_suffix(".grib.json").exists() for k in ("pl", "sfc", "fc")):
            era5_convert(d)
    pending_days = {d: 3 - sum(era5_grib(d, k).with_suffix(".grib.json").exists() for k in ("pl", "sfc", "fc")) for d in days}
    failed = []
    with ThreadPoolExecutor(workers) as pool:
        futs = {pool.submit(era5_fetch_day_kind, client, d, k): (d, k) for d, k in jobs}
        for f in as_completed(futs):
            d, k = futs[f]
            try:
                r = f.result()
                log(f"ERA5 {d:%Y-%m-%d} {k}: {r['bytes']/1e6:.0f} MB in {r['seconds']/60:.1f} min")
                pending_days[d] -= 1
                if pending_days[d] == 0:
                    era5_convert(d)
                    log(f"ERA5 {d:%Y-%m-%d} converted")
            except Exception as e:  # noqa: BLE001 - recorded, rerun resumes
                failed.append((d, k)); log(f"ERA5 FAILED {d:%Y-%m-%d} {k}: {e!r}")
    log(f"ERA5 fetch pass finished, {len(failed)} failed")
    if failed:
        raise RuntimeError(f"{len(failed)} ERA5 requests failed; rerun fetch-era5 to resume")


# -------------------------------------------------------------------- GFS
def gfs_path(day) -> Path:
    return GFS / f"{day:%Y%m%d}_gfs0p25"


def fetch_gfs(workers: int, days: pd.DatetimeIndex | None = None) -> None:
    import a41_bkt_gfs as gfs
    GFS.mkdir(parents=True, exist_ok=True)
    days = met_days() if days is None else days
    todo = [d for d in days if not gfs_path(d).with_name(gfs_path(d).name + ".json").exists()]
    log(f"GFS: {len(days)} days, {len(todo)} pending, {workers} parallel")

    def one(d):
        started = time.monotonic()
        gfs.regional_extract(dates=[str(d.date())], bounds=BOX, directory=GFS)
        rec_path = gfs_path(d).with_name(gfs_path(d).name + ".json")
        rec = json.loads(rec_path.read_text())
        if "seconds" not in rec:
            rec["seconds"] = time.monotonic() - started
            z = gfs_path(d).with_suffix(".zip")
            rec["archive_bytes"] = z.stat().st_size if z.exists() else None
            rec_path.write_text(json.dumps(rec, indent=2) + "\n")
        return rec

    failed = []
    with ThreadPoolExecutor(workers) as pool:
        futs = {pool.submit(one, d): d for d in todo}
        for f in as_completed(futs):
            d = futs[f]
            try:
                r = f.result()
                log(f"GFS {d:%Y-%m-%d}: {r['bytes']/1e6:.0f} MB ARL in {r['seconds']/60:.1f} min")
            except Exception as e:  # noqa: BLE001
                failed.append(d); log(f"GFS FAILED {d:%Y-%m-%d}: {e!r}")
    log(f"GFS fetch pass finished, {len(failed)} failed")
    if failed:
        raise RuntimeError(f"{len(failed)} GFS days failed; rerun fetch-gfs to resume")


# --------------------------------------------------------------- HYSPLIT
def model():
    import a37_bkt_footprint as m
    return m


def config(driver: str, code: str, seed: int):
    import a84_bkt_jmb_two_receptor as T
    cfg = T.base_config(code, seed)
    return cfg.__class__(**{**asdict(cfg), "meteorology_label": LABELS[driver]})


def run_dir(driver: str, code: str, stamp: pd.Timestamp, seed: int = 0) -> Path:
    if driver == "gdas1" and seed == 0:
        return A127_RUN_DIR(code, stamp)                    # the a127 reference run, reused read-only
    return RUNS / f"{driver}" / f"{code.lower()}_s{seed}" / f"bkt_{stamp:%Y%m%dT%H%MZ}"


def met_paths(driver: str, stamp: pd.Timestamp) -> list[Path]:
    if driver == "era5":
        return [era5_arl(d) for d in stamp_days(stamp)]
    if driver == "gfs0p25":
        return [gfs_path(d) for d in stamp_days(stamp)]
    return [H.MET / n for n in model().required_met_names(stamp, HOURS_BACK)]


def met_record(driver: str, path: Path) -> Path:
    return path.with_suffix(".json") if driver == "era5" else path.with_name(path.name + ".json")


def met_ready(driver: str, stamp: pd.Timestamp) -> bool:
    if driver == "gdas1":
        return H.met_ready(stamp)
    return all(met_record(driver, p).exists() for p in met_paths(driver, stamp))


def jobs() -> list[tuple[str, str, pd.Timestamp, int]]:
    t = receptors()
    out = []
    for r in t.itertuples():
        out.append(("era5", r.station, r.time_utc, 0))
        out.append(("gfs0p25", r.station, r.time_utc, 0))
        if r.seed_noise:
            out.append(("gdas1", r.station, r.time_utc, SEED2))
    return out


def done(job) -> bool:
    d, c, s, seed = job
    return (run_dir(d, c, s, seed) / "completion_receipt.json").exists()


def ensure_run(driver: str, code: str, stamp: pd.Timestamp, seed: int) -> float:
    import a84_bkt_jmb_two_receptor as T
    m = model()
    cfg = config(driver, code, seed)
    directory = run_dir(driver, code, stamp, seed)
    if (directory / "completion_receipt.json").exists():
        return 0.0
    if directory.exists():
        shutil.rmtree(directory)                            # a partial run of this campaign
    paths = met_paths(driver, stamp)
    met_sha = {}
    if driver != "gdas1":
        for p in paths:
            rec = json.loads(met_record(driver, p).read_text())
            got = sha256(p)
            if got != rec["sha256"]:
                raise ValueError(f"meteorology checksum mismatch: {p}")
            met_sha[p.name] = got
    started = time.monotonic()
    context = {"station": code, "time_utc": stamp.isoformat() + "Z", "inlet_height_m_agl": T.INLET_HEIGHT_M,
               "purpose": f"a160 three-driver test 2025, driver {driver}, seed {seed}"}
    m.run_footprint(stamp, H.MET, directory.parent, T.HYSPLIT_HOME, cfg, False,
                    meteorology_paths=None if driver == "gdas1" else paths,
                    transport=m.TransportOptions(), observation_context=context, extra_levels_m=T.EXTRA_LEVELS_M)
    m.run_checked([str(T.HYSPLIT_HOME / "exec/par2asc"), "-iPARDUMP", "-oendpoints.txt",
                   "-vendpoint_times.txt", "-a1"], directory, "endpoints")
    (directory / "PARDUMP").unlink()
    elapsed = time.monotonic() - started
    meta = json.loads((directory / "run_metadata.json").read_text())
    message = (directory / "MESSAGE").read_text(errors="replace")
    actual = T.ext.actual_particles(message)
    if actual < cfg.particles:
        raise ValueError(f"Fewer particles emitted than requested: {directory}")
    if (directory / "CONTROL").read_text() != m.control_text(stamp, paths, directory, cfg, T.EXTRA_LEVELS_M):
        raise ValueError(f"CONTROL mismatch: {directory}")
    receipt = dict(driver=driver, station=code, receptor_utc=stamp.isoformat() + "Z", configuration=asdict(cfg),
                   transport_options=asdict(m.TransportOptions()), extra_levels_m=list(T.EXTRA_LEVELS_M),
                   meteorology_files=meta["meteorology_files"], meteorology_sha256=met_sha or "GDAS1 a127 manifest",
                   actual_emitted_particles=actual, model_runtime_seconds=elapsed,
                   hysplit_version_line=meta.get("hysplit_version_line"),
                   output_sha256={n: sha256(directory / n) for n in ("footprint.nc", "footprint_layers.nc", "MESSAGE")},
                   created_at_utc=now())
    (directory / "completion_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return elapsed


def run(workers: int, limit: int = 0) -> None:
    workers = min(workers, MAX_WORKERS)
    t = receptors()
    order = {s: i for i, s in enumerate(sorted(t.time_utc.unique()))}
    allj = sorted(jobs(), key=lambda j: (order[np.datetime64(j[2])], j[0], j[1]))
    if limit:
        allj = allj[:limit]
    pending = [j for j in allj if not done(j)]
    failures: dict = {}
    log(f"run: {len(allj)} jobs, {len(pending)} pending, {workers} workers")
    started = time.monotonic()
    with ThreadPoolExecutor(workers) as pool:
        inflight = {}
        while pending or inflight:
            free = workers - len(inflight)
            ready = [j for j in pending if j not in inflight.values() and failures.get(j, 0) < 3 and met_ready(j[0], j[2])]
            for j in ready[:free]:
                inflight[pool.submit(ensure_run, *j)] = j
            if not inflight:
                if all(failures.get(j, 0) >= 3 for j in pending):
                    break
                time.sleep(300)
                continue
            finished, _ = wait(list(inflight), timeout=300, return_when=FIRST_COMPLETED)
            for f in finished:
                j = inflight.pop(f)
                try:
                    e = f.result()
                    pending.remove(j)
                    log(f"done {j[0]} {j[1]} {j[2]:%Y-%m-%dT%HZ} s{j[3]} {e/60:.1f} min "
                        f"({len(allj)-len(pending)}/{len(allj)}, campaign {(time.monotonic()-started)/3600:.2f} h)")
                except Exception:  # noqa: BLE001 - logged and retried up to three times
                    failures[j] = failures.get(j, 0) + 1
                    log(f"FAILED {j} attempt {failures[j]}\n{traceback.format_exc()}")
    log(f"run finished: {len(allj)-len(pending)} of {len(allj)} complete, {len(pending)} not done")


# ------------------------------------------------------------------ status
def status() -> str:
    t = receptors()
    lines = []
    for drv, seed in (("gdas1", 0), ("era5", 0), ("gfs0p25", 0), ("gdas1", SEED2)):
        sub = t if not (drv == "gdas1" and seed == SEED2) else t[t.seed_noise]
        n = sum((run_dir(drv, r.station, r.time_utc, seed) / "completion_receipt.json").exists() for r in sub.itertuples())
        lines.append(f"| {drv} seed {seed} | {n} | {len(sub)} |")
    days = met_days()
    e = sum(era5_arl(d).with_suffix(".json").exists() for d in days)
    g = sum(gfs_path(d).with_name(gfs_path(d).name + ".json").exists() for d in days)
    gb_e = sum(json.loads(era5_grib(d, k).with_suffix(".grib.json").read_text())["bytes"]
               for d in days for k in ("pl", "sfc", "fc") if era5_grib(d, k).with_suffix(".grib.json").exists()) / 1e9
    gb_g = sum((json.loads(gfs_path(d).with_name(gfs_path(d).name + ".json").read_text()).get("archive_bytes") or 0)
               for d in days if gfs_path(d).with_name(gfs_path(d).name + ".json").exists()) / 1e9
    text = ("| runs | complete | declared |\n|---|---|---|\n" + "\n".join(lines) +
            f"\n\nMeteorology days ready: ERA5 {e} of {len(days)} ({gb_e:.1f} GB GRIB downloaded), "
            f"GFS 0.25 {g} of {len(days)} ({gb_g:.1f} GB zip downloaded).\n")
    print(text)
    (OUT / "progress.md").write_text(f"Progress at {now()}\n\n{text}")
    return text


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("stage", choices=["select", "fetch-era5", "fetch-gfs", "run", "status", "days"])
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--interface", default=None)
    p.add_argument("--first", type=int, default=0, help="only the first N meteorology days")
    p.add_argument("--limit", type=int, default=0)
    a = p.parse_args()
    days = met_days()[: a.first] if a.first else None
    if a.stage == "select":
        select()
    elif a.stage == "fetch-era5":
        fetch_era5(a.workers, a.interface, days)
    elif a.stage == "fetch-gfs":
        fetch_gfs(a.workers, days)
    elif a.stage == "run":
        run(a.workers, a.limit)
    elif a.stage == "days":
        print("\n".join(str(d.date()) for d in met_days()))
    else:
        status()


if __name__ == "__main__":
    main()
