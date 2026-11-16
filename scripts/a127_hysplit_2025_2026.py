#!/usr/bin/env python3
"""HYSPLIT-STILT footprints at Bukit Kototabang and Jambi for 2025 and 2026.

Extends the two-receptor transport (a84/a93) into the period of the October
2026 re-export (a120).  Same model as before (hycs_std ICHEM=8, 2000 particles,
120 h backward, 0.25 degree output over 60 x 100 degrees, 100 m inlet), one
seed, with one change forced by bandwidth: the driver is GDAS1 (1 degree,
3-hourly, NOAA ARL weekly files, about 0.6 GB a week) rather than the GFS 0.25
READY crop (0.46 GB a day, a 3.3 GB global file otherwise).  The driver change
is recorded in every receipt and the inversion carries it as its own period.

Windows (receptor 06 UTC = 13 WIB, a tower is run when it has at least two
valid 05-07 UTC CO2 hours that day)
  fire26  2026-08-01 to 2026-09-30, daily  (GDAS1 is published to 30 Sep 2026)
  fire25  2025-08-01 to 2025-10-31, daily
  co2_25  the rest of 2025, every second day  (CarbonTracker CT2026 ends 2025-12-31)

Stages
  fetch-met   GDAS1 weekly files, four parallel resumable transfers, manifest with SHA-256
  select      receptor table
  run         HYSPLIT campaign
  status      progress table
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G

ROOT = G.ROOT
MET = ROOT / "data/hysplit/gdas1_2025_2026"
OUT = ROOT / "outputs/hysplit/two_receptor"
RUNS = OUT / "runs_2025_2026"
TABLES = OUT / "tables"
READY = "https://www.ready.noaa.gov/data/archives/gdas1"
HOURS_BACK = 120
SEED = 0
WINDOWS = {
    "fire26": (pd.Timestamp("2026-08-01"), pd.Timestamp("2026-09-30"), 1),
    "fire25": (pd.Timestamp("2025-08-01"), pd.Timestamp("2025-10-31"), 1),
    "co2_25": (pd.Timestamp("2025-01-01"), pd.Timestamp("2025-12-31"), 2),
}
PRIORITY = ("fire26", "fire25", "co2_25")
STATIONS = ("JMB", "BKT")


# --------------------------------------------------------------- meteorology
def week_name(day: pd.Timestamp) -> str:
    import a37_bkt_footprint as model
    return model.gdas1_week_name(day)


def window_days(name: str) -> pd.DatetimeIndex:
    a, b, step = WINDOWS[name]
    days = pd.date_range(a, b, freq="D")
    return days[::step] if step > 1 else days


def met_names_for(days) -> list[str]:
    names = []
    for d in days:
        for x in pd.date_range(d - pd.Timedelta(hours=HOURS_BACK), d + pd.Timedelta(hours=6), freq="D"):
            names.append(week_name(x.normalize()))
    return list(dict.fromkeys(names))


def wanted_met() -> list[str]:
    names = []
    for w in PRIORITY:
        names += [n for n in met_names_for(window_days(w)) if n not in names]
    return names


def remote_size(name: str) -> int:
    out = subprocess.run(["curl", "-sI", "--max-time", "60", f"{READY}/{name}"], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.lower().startswith("content-length:"):
            return int(line.split()[1])
    raise RuntimeError(f"no Content-Length for {name}")


def fetch_one(name: str) -> tuple[str, str]:
    target = MET / name
    size = remote_size(name)
    for attempt in range(6):
        if target.exists() and target.stat().st_size == size:
            (MET / f"{name}.complete").write_text(str(size))
            return name, "ok"
        subprocess.run(["curl", "-s", "-C", "-", "--retry", "5", "--max-time", "7200", "-o", str(target), f"{READY}/{name}"])
        time.sleep(5)
    return name, f"incomplete {target.stat().st_size if target.exists() else 0} of {size}"


def fetch_met(workers: int = 4) -> None:
    MET.mkdir(parents=True, exist_ok=True)
    names = wanted_met()
    print(f"{len(names)} weekly files wanted", flush=True)
    status = {}
    with ThreadPoolExecutor(workers) as pool:
        futures = {pool.submit(fetch_one, n): n for n in names}
        for f in as_completed(futures):
            n, s = f.result()
            status[n] = s
            print(f"{n}: {s} ({len(status)}/{len(names)})", flush=True)
    manifest = []
    for n in names:
        p = MET / n
        if status.get(n) == "ok":
            h = hashlib.sha256()
            with p.open("rb") as fh:
                for chunk in iter(lambda: fh.read(8 << 20), b""):
                    h.update(chunk)
            manifest.append(dict(file=n, bytes=p.stat().st_size, sha256=h.hexdigest(), source=f"{READY}/{n}"))
    (MET / "manifest.json").write_text(json.dumps(dict(created_utc=pd.Timestamp.utcnow().isoformat(),
                                                       files=manifest, failed={k: v for k, v in status.items() if v != "ok"}), indent=1))
    bad = [k for k, v in status.items() if v != "ok"]
    if bad:
        raise RuntimeError(f"incomplete: {bad}")


def met_ready(stamp: pd.Timestamp) -> bool:
    import a37_bkt_footprint as model
    names = model.required_met_names(stamp, HOURS_BACK)
    man = MET / "manifest.json"
    done = {f["file"] for f in json.loads(man.read_text())["files"]} if man.exists() else set()
    if all(n in done for n in names):
        return True
    # during the transfer: a file is usable once its size matches the server's
    return all((MET / n).exists() and (MET / f"{n}.complete").exists() for n in names)


# ------------------------------------------------------------------ receptors
def afternoon_valid() -> pd.DataFrame:
    d = pd.read_pickle(G.OUT / "all_2026.pkl")
    d = d[d.station.isin(STATIONS) & d.time_utc.dt.hour.isin([5, 6, 7]) & d.co2.notna() & ~d.suspect_co2]
    g = d.groupby(["station", d.time_utc.dt.normalize()]).co2.size().rename("valid_hours").reset_index()
    return g.rename(columns={"time_utc": "day"})


def select() -> pd.DataFrame:
    valid = afternoon_valid()
    rows = []
    for w in PRIORITY:
        for day in window_days(w):
            for st in STATIONS:
                v = valid[(valid.station == st) & (valid.day == day)]
                if len(v) and int(v.valid_hours.iloc[0]) >= 2:
                    rows.append(dict(window=w, station=st, time_utc=day + pd.Timedelta(hours=6)))
    t = pd.DataFrame(rows).drop_duplicates(["station", "time_utc"])
    TABLES.mkdir(parents=True, exist_ok=True)
    t.to_csv(TABLES / "receptors_2025_2026.csv", index=False)
    print(t.groupby(["window", "station"]).size().unstack(), flush=True)
    return t


# ------------------------------------------------------------------- runs
def config(code: str):
    import a84_bkt_jmb_two_receptor as T
    cfg = T.base_config(code, SEED)
    return cfg.__class__(**{**asdict(cfg), "meteorology_label": "NOAA NCEP GDAS1 analysis, 1 degree, ARL format"})


def run_dir(code: str, stamp: pd.Timestamp) -> Path:
    return RUNS / f"{code.lower()}_s{SEED}" / f"bkt_{stamp:%Y%m%dT%H%MZ}"


def ensure_run(code: str, stamp: pd.Timestamp) -> float:
    import shutil
    import a84_bkt_jmb_two_receptor as T
    model = T.model
    cfg = config(code)
    directory = run_dir(code, stamp)
    if (directory / "completion_receipt.json").exists():
        return 0.0
    if directory.exists():
        shutil.rmtree(directory)
    started = time.monotonic()
    context = {"station": code, "time_utc": stamp.isoformat() + "Z", "inlet_height_m_agl": T.INLET_HEIGHT_M,
               "purpose": "2025-2026 extension; gas values do not select runs beyond data availability"}
    model.run_footprint(stamp, MET, directory.parent, T.HYSPLIT_HOME, cfg, False,
                        transport=model.TransportOptions(), observation_context=context,
                        extra_levels_m=T.EXTRA_LEVELS_M)
    model.run_checked([str(T.HYSPLIT_HOME / "exec/par2asc"), "-iPARDUMP", "-oendpoints.txt",
                       "-vendpoint_times.txt", "-a1"], directory, "endpoints")
    (directory / "PARDUMP").unlink()
    elapsed = time.monotonic() - started
    meta = json.loads((directory / "run_metadata.json").read_text())
    actual = T.ext.actual_particles((directory / "MESSAGE").read_text(errors="replace"))
    if actual < cfg.particles:
        raise ValueError(f"Fewer particles emitted than requested: {directory}")
    receipt = dict(station=code, receptor_utc=stamp.isoformat() + "Z", configuration=asdict(cfg),
                   meteorology_files=meta["meteorology_files"], actual_emitted_particles=actual,
                   model_runtime_seconds=elapsed, hysplit_version_line=meta.get("hysplit_version_line"),
                   created_at_utc=pd.Timestamp.utcnow().isoformat())
    (directory / "completion_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return elapsed


def run(workers: int, only: str | None = None, limit: int = 0) -> None:
    import traceback
    t = pd.read_csv(TABLES / "receptors_2025_2026.csv", parse_dates=["time_utc"])
    if only:
        t = t[t.window == only]
    t["prio"] = t.window.map({w: i for i, w in enumerate(PRIORITY)})
    t = t.sort_values(["prio", "time_utc", "station"])
    jobs = [(r.station, r.time_utc) for r in t.itertuples()]
    if limit:
        jobs = jobs[:limit]
    started = time.monotonic()
    pending = list(jobs)
    rounds = 0
    while pending and rounds < 200:
        rounds += 1
        runnable = [j for j in pending if not (run_dir(*j) / "completion_receipt.json").exists() and met_ready(j[1])]
        done_now = [j for j in pending if (run_dir(*j) / "completion_receipt.json").exists()]
        pending = [j for j in pending if j not in done_now]
        if not runnable:
            if not pending:
                break
            print(f"waiting for meteorology: {len(pending)} runs pending", flush=True)
            time.sleep(300)
            continue
        print(f"round {rounds}: {len(runnable)} runnable of {len(pending)} pending, {workers} workers", flush=True)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(ensure_run, c, s): (c, s) for c, s in runnable}
            for k, f in enumerate(as_completed(futures), 1):
                c, s = futures[f]
                try:
                    e = f.result()
                    print(f"[{k}/{len(runnable)}] {c} {s:%Y-%m-%dT%HZ} {e/60:.1f} min "
                          f"(campaign {(time.monotonic()-started)/3600:.2f} h)", flush=True)
                except Exception:  # noqa: BLE001 - logged, retried next round
                    print(f"[{k}/{len(runnable)}] FAILED {c} {s:%Y-%m-%dT%HZ}\n{traceback.format_exc()}", flush=True)
        pending = [j for j in pending if not (run_dir(*j) / "completion_receipt.json").exists()]
    print(f"campaign finished: {len(jobs) - len(pending)} of {len(jobs)} complete", flush=True)


def status() -> None:
    t = pd.read_csv(TABLES / "receptors_2025_2026.csv", parse_dates=["time_utc"])
    t["done"] = [(run_dir(r.station, r.time_utc) / "completion_receipt.json").exists() for r in t.itertuples()]
    print(t.groupby(["window", "station"]).done.agg(["sum", "size"]).to_string())


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("stage", choices=["fetch-met", "select", "run", "status"])
    p.add_argument("--workers", type=int, default=12)
    p.add_argument("--only")
    p.add_argument("--limit", type=int, default=0)
    a = p.parse_args()
    if a.stage == "fetch-met":
        fetch_met(min(a.workers, 4))
    elif a.stage == "select":
        select()
    elif a.stage == "run":
        run(a.workers, a.only, a.limit)
    else:
        status()


if __name__ == "__main__":
    main()
