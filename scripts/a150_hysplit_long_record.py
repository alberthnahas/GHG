#!/usr/bin/env python3
"""HYSPLIT-STILT footprints for the whole BKT and JMB tower record (a150).

Fills every month that has afternoon tower measurements with footprints made
with the configuration of the 2025-2026 campaign (a127): hycs_std ICHEM=8, 2000
particles, 120 h backward, 0.25 degree output over 60 x 100 degrees, 100 m
inlet, seed 0, GDAS1 1 degree, receptor 06 UTC.  The model call, configuration
and receipt are a127's; only windows, paths and tables are this module's.

Receptor rule
  A station-day is valid when at least two of its 05, 06, 07 UTC hours hold a
  non-suspect CO2 value, or at least two hold a non-suspect CH4 value (a127
  used CO2 only; the CH4 arm keeps the months where only CO2 is flagged, BKT
  Oct-Nov 2013 and Dec 2020-Jun 2021, and the a127 rule is kept as a column).
  Receptors sit on a fixed every-second-day calendar grid anchored at
  2025-01-01, the grid of the a127 2025 runs, so both towers share dates.  A
  station-month with valid days but no valid grid day gets its valid off-grid
  days instead (column on_grid = False), so no measured month is left empty.

Time bases: 2009-2013 BKT comes from outputs/all.pkl (loader-corrected UTC;
the raw archive is WIB before 2021); 2018 onward from the October 2026
re-export (a120) merged with the DBKU download of 2026-11-14 for the hours the
re-export does not have, read through a120.load_station_2026 unchanged.

Phases (run in order, each verified before the next)
  p1  2026-01 to 2026-07 and 2026-10 to 2026-11, both towers
  p2  JMB 2023-11 to 2024-12, BKT 2018-11 to 2024-12
  p3  BKT 2009-10 to 2013-12

Stages
  obs        merge the DBKU download, valid-day table
  select     receptor table
  plan       GDAS1 weeks, remote sizes, projected hours (writes plan_phases.csv)
  campaign   download + run + verify, all phases chained (the unattended job)
  repro      rerun one 2025 receptor and compare with the a127 footprint
  verify     verification table for a phase (or --first N of it)
  status     progress per phase, tower and month (prints; STATUS.md by campaign)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import traceback
from collections import Counter
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G  # noqa: E402
import a120_obs2026 as A120  # noqa: E402
import a127_hysplit_2025_2026 as H  # noqa: E402

ROOT = G.ROOT
LR = G.OUT / "hysplit" / "long_record"
RUNS = LR / "runs"
REPRO = LR / "repro"
TABLES = LR / "tables"
OBSDIR = LR / "obs"
LOGS = LR / "logs"
STATE = LR / "state.json"
STATUS_MD = LR / "STATUS.md"
STOP = LR / "STOP"
MET = ROOT / "data/hysplit/gdas1_long"
MET_2526 = H.MET                       # read in place through symlinks, never written
READY = H.READY
HOURS_BACK = H.HOURS_BACK
SEED = H.SEED
STATIONS = ("BKT", "JMB")
GRID_EPOCH = pd.Timestamp("2025-01-01")
GRID_STEP = 2
MAX_WORKERS = 9
FETCH_WORKERS = 4
MET_LIMIT_BYTES = 450e9
FREE_FLOOR_BYTES = 400e9
RUN_BYTES = 4.6e6                      # 2.2 GB / 503 a127 runs
REPRO_RECEPTOR = ("BKT", pd.Timestamp("2025-01-03T06:00"))
GATE_FIRST = 10
DBKU = {"BKT": Path("/run/media/workstation-llm/HDD2/AQ/data/dbku/grk/grk/jam/1013_KOTOTABANG/2026.csv"),
        "JMB": Path("/run/media/workstation-llm/HDD2/AQ/data/dbku/grk/grk/jam/4011_JAMBI/2026.csv")}
REEXPORT = {c: ROOT / "obs" / f"grk_hourly_avg_{c.lower()}.csv" for c in STATIONS}
PHASES = {
    "p1": [("BKT", "2026-01-01", "2026-07-31"), ("JMB", "2026-01-01", "2026-07-31"),
           ("BKT", "2026-10-01", "2026-11-30"), ("JMB", "2026-10-01", "2026-11-30")],
    "p2": [("JMB", "2023-11-01", "2024-12-31"), ("BKT", "2018-11-01", "2024-12-31")],
    "p3": [("BKT", "2009-10-01", "2013-12-31")],
}
PHASE_ORDER = ("p1", "p2", "p3")
VALS = ["RATA_co", "RATA_co2", "RATA_ch4", "RATA_co2d", "RATA_ch4d", "RATA_h2o"]
LAUNCHER = ROOT / "scripts/a151_long_record_launch.sh"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def wib(ts: str | pd.Timestamp | None = None) -> str:
    t = pd.Timestamp(ts) if ts is not None else pd.Timestamp.now(tz="UTC")
    if t.tzinfo is None:
        t = t.tz_localize("UTC")
    return t.tz_convert("Asia/Jakarta").strftime("%Y-%m-%d %H:%M WIB")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, obj) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1, default=str) + "\n")
    tmp.replace(path)


def model():
    import a37_bkt_footprint as m
    return m


# ---------------------------------------------------------------- observations
def merge_dbku() -> pd.DataFrame:
    """Re-export plus the DBKU hours it does not have, raw format, a120 file names."""
    OBSDIR.mkdir(parents=True, exist_ok=True)
    key = ["TANGGAL", "JAM"]
    checks, prov = [], dict(created_utc=now(), inputs=[])
    for code in STATIONS:
        old = pd.read_csv(REEXPORT[code], dtype=str)
        new = pd.read_csv(DBKU[code], dtype=str)
        if list(old.columns) != list(new.columns):
            raise SystemExit(f"{code}: columns differ {list(old.columns)} vs {list(new.columns)}")
        j = old.drop_duplicates(key).merge(new.drop_duplicates(key), on=key, suffixes=("_old", "_new"))
        same = np.ones(len(j), bool)
        for c in VALS:
            x, y = pd.to_numeric(j[c + "_old"], errors="coerce"), pd.to_numeric(j[c + "_new"], errors="coerce")
            same &= ((x == y) | (x.isna() & y.isna())).to_numpy()
        only_new = new[~new.set_index(key).index.isin(old.set_index(key).index)]
        merged = pd.concat([old, only_new], ignore_index=True)
        t = pd.to_datetime(merged.TANGGAL) + pd.to_timedelta(merged.JAM.astype(int), unit="h")
        merged = merged.iloc[np.argsort(t.to_numpy(), kind="stable")]
        merged.to_csv(OBSDIR / f"grk_hourly_avg_{code.lower()}.csv", index=False)
        tn = pd.to_datetime(only_new.TANGGAL) + pd.to_timedelta(only_new.JAM.astype(int), unit="h")
        checks.append(dict(station=code, reexport_rows=len(old), dbku_rows=len(new), shared_hours=len(j),
                           shared_identical_numeric=int(same.sum()), hours_added=len(only_new),
                           added_first=str(tn.min()), added_last=str(tn.max()), merged_rows=len(merged)))
        for p in (REEXPORT[code], DBKU[code]):
            prov["inputs"].append(dict(path=str(p), bytes=p.stat().st_size, sha256=sha256(p)))
    c = pd.DataFrame(checks)
    c.to_csv(OBSDIR / "merge_check.csv", index=False)
    write_json(OBSDIR / "provenance.json", prov)
    if (c.shared_identical_numeric != c.shared_hours).any():
        print("WARNING: shared hours differ between re-export and DBKU; re-export kept", flush=True)
    return c


def hourly() -> pd.DataFrame:
    A120.OBS = OBSDIR                                  # loader unchanged, pointed at the merged files
    new = G.apply_flags(pd.concat([A120.load_station_2026(c) for c in STATIONS], ignore_index=True))
    new["source"] = "a120 re-export + DBKU 2026-11-14"
    old = pd.read_pickle(G.OUT / "all.pkl")
    old = old[(old.station == "BKT") & (old.time_utc < "2014-01-01")].copy()
    old["source"] = "outputs/all.pkl (ghg_common.load_station)"
    cols = ["station", "time_utc", "co2", "ch4", "suspect_co2", "suspect_ch4", "source"]
    return pd.concat([old[cols], new[cols]], ignore_index=True)


def valid_days() -> pd.DataFrame:
    d = hourly()
    a = d[d.time_utc.dt.hour.isin([5, 6, 7])].copy()
    a["day"] = a.time_utc.dt.normalize()
    a["co2_ok"] = a.co2.notna() & ~a.suspect_co2
    a["ch4_ok"] = a.ch4.notna() & ~a.suspect_ch4
    g = a.groupby(["station", "day"]).agg(co2_hours=("co2_ok", "sum"), ch4_hours=("ch4_ok", "sum"),
                                          source=("source", "first")).reset_index()
    g["valid"] = (g.co2_hours >= 2) | (g.ch4_hours >= 2)
    g["a127_rule"] = g.co2_hours >= 2
    g = g[g.valid].reset_index(drop=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    g.to_csv(TABLES / "afternoon_valid_days.csv", index=False)
    return g


def stage_obs() -> None:
    print(merge_dbku().T.to_string(), flush=True)
    g = valid_days()
    print(g.groupby(["station", g.day.dt.year]).size().unstack(0).to_string(), flush=True)


# ------------------------------------------------------------------- receptors
def on_grid(days: pd.Series) -> pd.Series:
    return ((days - GRID_EPOCH).dt.days % GRID_STEP) == 0


def select() -> pd.DataFrame:
    g = pd.read_csv(TABLES / "afternoon_valid_days.csv", parse_dates=["day"])
    g["on_grid"] = on_grid(g.day)
    rows = []
    for ph in PHASE_ORDER:
        for st, a, b in PHASES[ph]:
            v = g[(g.station == st) & (g.day >= a) & (g.day <= b)].copy()
            v["month"] = v.day.dt.to_period("M")
            keep = v[v.on_grid]
            empty = set(v.month) - set(keep.month)
            fill = v[~v.on_grid & v.month.isin(empty)]
            rows.append(pd.concat([keep, fill]).assign(phase=ph))
    t = pd.concat(rows, ignore_index=True)
    t["time_utc"] = t.day + pd.Timedelta(hours=6)
    t = t.drop_duplicates(["station", "time_utc"]).sort_values(["phase", "time_utc", "station"])
    t = t[["phase", "station", "time_utc", "on_grid", "co2_hours", "ch4_hours", "a127_rule", "source"]]
    t.to_csv(TABLES / "receptors_long_record.csv", index=False)
    print(t.groupby(["phase", "station", t.time_utc.dt.year]).size().rename("receptors").to_string(), flush=True)
    print("off-grid fills:", int((~t.on_grid).sum()), flush=True)
    return t


def receptors() -> pd.DataFrame:
    return pd.read_csv(TABLES / "receptors_long_record.csv", parse_dates=["time_utc"])


# ----------------------------------------------------------------- meteorology
def weeks_for(stamp: pd.Timestamp) -> list[str]:
    return model().required_met_names(stamp, HOURS_BACK)


def existing_2526() -> dict[str, dict]:
    man = json.loads((MET_2526 / "manifest.json").read_text())
    return {f["file"]: f for f in man["files"]}


def head(name: str) -> dict:
    out = subprocess.run(["curl", "-sI", "--max-time", "60", f"{READY}/{name}"],
                         capture_output=True, text=True).stdout
    r = dict(file=name, http=None, bytes=np.nan, last_modified="", checked_utc=now())
    for line in out.splitlines():
        low = line.lower()
        if low.startswith("http/"):
            r["http"] = int(line.split()[1])
        elif low.startswith("content-length:"):
            r["bytes"] = int(line.split()[1])
        elif low.startswith("last-modified:"):
            r["last_modified"] = line.split(":", 1)[1].strip()
    if r["http"] != 200:
        r["bytes"] = np.nan
    return r


def receipt_path(name: str) -> Path:
    return MET / f"{name}.receipt.json"


def link_existing() -> int:
    """Symlink the a127 weeks into MET with a receipt carrying their manifest SHA-256."""
    MET.mkdir(parents=True, exist_ok=True)
    n = 0
    for name, f in existing_2526().items():
        src, dst = MET_2526 / name, MET / name
        if receipt_path(name).exists():
            continue
        if src.stat().st_size != f["bytes"]:
            raise RuntimeError(f"{src} size differs from its manifest")
        if not dst.exists():
            dst.symlink_to(src)
        write_json(receipt_path(name), dict(file=name, bytes=f["bytes"], sha256=f["sha256"], source=f["source"],
                                            linked_from=str(src), manifest=str(MET_2526 / "manifest.json"),
                                            sha256_note="from the a127 manifest; size checked, not rehashed",
                                            linked_utc=now()))
        n += 1
    return n


def plan(refresh: bool = False) -> pd.DataFrame:
    t = receptors()
    have = existing_2526()
    weeks = []
    for ph in PHASE_ORDER:
        seen = set()
        for s in t[t.phase == ph].time_utc:
            for w in weeks_for(s):
                if w not in seen:
                    seen.add(w)
                    weeks.append(dict(phase=ph, file=w))
    w = pd.DataFrame(weeks)
    w["first_phase"] = ~w.duplicated("file")
    sizes_path = TABLES / "met_remote_sizes.csv"
    cached = pd.read_csv(sizes_path) if sizes_path.exists() and not refresh else pd.DataFrame(columns=["file"])
    need = [f for f in w.file.unique() if f not in set(cached.file) and f not in have]
    if need:
        with ThreadPoolExecutor(8) as pool:
            got = pd.DataFrame(list(pool.map(head, need)))
        cached = pd.concat([cached, got], ignore_index=True).drop_duplicates("file", keep="last")
        cached.to_csv(sizes_path, index=False)
    w = w.merge(cached[["file", "http", "bytes", "last_modified"]], on="file", how="left")
    w["linked"] = w.file.isin(list(have))
    w.loc[w.linked, "bytes"] = w.loc[w.linked, "file"].map(lambda f: have[f]["bytes"])
    w.loc[w.linked, "http"] = 200
    w.to_csv(TABLES / "met_weeks.csv", index=False)
    ref = reference_2025()
    rt = ref.groupby("station").runtime_s.mean()
    rows = []
    for ph in PHASE_ORDER:
        r = t[t.phase == ph]
        x = w[(w.phase == ph)]
        new = x[x.first_phase & ~x.linked]
        rows.append(dict(phase=ph, receptors=len(r), receptors_BKT=int((r.station == "BKT").sum()),
                         receptors_JMB=int((r.station == "JMB").sum()), off_grid=int((~r.on_grid).sum()),
                         weeks_needed=len(x), weeks_linked=int(x.linked.sum()),
                         weeks_new=int(len(new)), weeks_unpublished=int((new.http != 200).sum()),
                         download_GB=float(new.bytes.sum() / 1e9),
                         run_hours_at_9_workers=float(sum(rt[s] for s in r.station) / 3600 / MAX_WORKERS),
                         first=str(r.time_utc.min()), last=str(r.time_utc.max())))
    p = pd.DataFrame(rows)
    p.to_csv(TABLES / "plan_phases.csv", index=False)
    unpub = w[(w.http != 200) & ~w.linked].file.unique().tolist()
    print(p.to_string(index=False), flush=True)
    print("unpublished or missing on READY:", unpub, flush=True)
    return p


def reference_2025() -> pd.DataFrame:
    """Footprint sums, runtimes and month of the a127 runs (read only)."""
    path = TABLES / "reference_2025.csv"
    if path.exists():
        return pd.read_csv(path, parse_dates=["time_utc"])
    t = pd.read_csv(H.TABLES / "receptors_2025_2026.csv", parse_dates=["time_utc"])
    op = pd.read_csv(H.TABLES / "footprint_operator_2025_2026.csv", parse_dates=["time_utc"])
    surv = op.set_index(["station", "time_utc"]).endpoint_survival_fraction
    rows = []
    for r in t.itertuples():
        d = H.run_dir(r.station, r.time_utc)
        if not (d / "completion_receipt.json").exists():
            continue
        meta = json.loads((d / "run_metadata.json").read_text())
        rec = json.loads((d / "completion_receipt.json").read_text())
        rows.append(dict(station=r.station, time_utc=r.time_utc, window=r.window,
                         footprint_sum=meta["footprint_sensitivity_sum"], runtime_s=rec["model_runtime_seconds"],
                         actual=rec["actual_emitted_particles"],
                         survival=float(surv.get((r.station, r.time_utc), np.nan))))
    ref = pd.DataFrame(rows)
    ref.to_csv(path, index=False)
    return ref


# --------------------------------------------------------------------- runs
def run_dir(code: str, stamp: pd.Timestamp, root: Path = RUNS) -> Path:
    return root / f"{code.lower()}_s{SEED}" / f"bkt_{stamp:%Y%m%dT%H%MZ}"


def done(code: str, stamp: pd.Timestamp, root: Path = RUNS) -> bool:
    return (run_dir(code, stamp, root) / "completion_receipt.json").exists()


def ensure_run(code: str, stamp: pd.Timestamp, root: Path = RUNS, purpose: str = "") -> float:
    """a127.ensure_run with this module's directories and an explicit met path list.

    The explicit list is what a37 builds itself (same names, same order); passing
    it only lowers a37's size floor from 100 MB to 1 MB, which the one-day w5
    weeks of leap Februaries need.  Completeness is checked here by receipt.
    """
    import a84_bkt_jmb_two_receptor as T
    m = T.model
    cfg = H.config(code)
    directory = run_dir(code, stamp, root)
    if (directory / "completion_receipt.json").exists():
        return 0.0
    names = weeks_for(stamp)
    missing = [n for n in names if not receipt_path(n).exists()]
    if missing:
        raise FileNotFoundError(f"meteorology without receipt: {missing}")
    if directory.exists():
        shutil.rmtree(directory)
    started = time.monotonic()
    context = {"station": code, "time_utc": stamp.isoformat() + "Z", "inlet_height_m_agl": T.INLET_HEIGHT_M,
               "purpose": purpose or "long-record extension (a150); gas values do not select runs beyond data availability"}
    m.run_footprint(stamp, MET, directory.parent, T.HYSPLIT_HOME, cfg, False,
                    meteorology_paths=[MET / n for n in names],
                    transport=m.TransportOptions(), observation_context=context,
                    extra_levels_m=T.EXTRA_LEVELS_M)
    m.run_checked([str(T.HYSPLIT_HOME / "exec/par2asc"), "-iPARDUMP", "-oendpoints.txt",
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
                   created_at_utc=pd.Timestamp.utcnow().isoformat(), script="a150_hysplit_long_record.py")
    (directory / "completion_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return elapsed


# ---------------------------------------------------------------- verification
def par_gis_times(col: pd.Series) -> pd.Series:
    """PAR_GIS.txt time column 'mm/dd/yy hh:mm' with HYSPLIT's blank-padded fields.

    a71.active_endpoints strips every blank and parses '%m/%d/%y%H:%M'.  Before
    2010 HYSPLIT prints the year as one blank-padded digit ('10/25/ 9  6: 0'),
    so the stripped string '10/25/96:0' fails.  Here each field is read as a
    number, so 2009 and 2025 parse alike.
    """
    f = col.astype(str).str.extract(r"^\s*(\d+)/\s*(\d+)/\s*(\d+)\s+(\d+):\s*(\d+)")
    if f.isna().any().any():
        raise ValueError(f"unparsed PAR_GIS time: {col[f.isna().any(axis=1)].iloc[0]!r}")
    f = f.astype(int)
    return pd.to_datetime(dict(year=2000 + f[2], month=f[0], day=f[1], hour=f[3], minute=f[4]))


def active_endpoints(directory: Path, meta: dict, actual: int) -> pd.DataFrame:
    """a71.active_endpoints with a year-safe time parser (same selection and checks)."""
    import a71_domain_budget_extension as ext
    points = pd.read_csv(directory / "PAR_GIS.txt", skipinitialspace=True)
    points.columns = points.columns.str.strip()
    points["endpoint_utc"] = par_gis_times(points.time)
    expected = ext.utc_stamp(meta["observation"]["time_utc"]) - pd.Timedelta(hours=meta["configuration"]["hours_back"])
    points = points.loc[points.endpoint_utc.eq(expected)].copy()
    if len(points) != actual or points.NSORT.duplicated().any():
        raise ValueError(f"Incomplete terminal endpoint particle accounting: {directory}")
    active = points.loc[points.PGRD.gt(0)].copy()
    if active.empty:
        raise ValueError(f"No active endpoint particles: {directory}")
    return active


def check_run(code: str, stamp: pd.Timestamp, ref: pd.DataFrame, root: Path = RUNS) -> dict:
    try:
        return _check_run(code, stamp, ref, root)
    except Exception as e:  # noqa: BLE001 - a broken run is a failed check, not a crash
        return dict(station=code, time_utc=stamp, files_ok=False, ok=False, error=f"{type(e).__name__}: {e}")


def _check_run(code: str, stamp: pd.Timestamp, ref: pd.DataFrame, root: Path = RUNS) -> dict:
    import a84_bkt_jmb_two_receptor as T
    d = run_dir(code, stamp, root)
    row = dict(station=code, time_utc=stamp, dir=str(d))
    files = ["completion_receipt.json", "run_metadata.json", "footprint.nc", "footprint_layers.nc",
             "footprint_hourly.csv.gz", "endpoints.txt", "PAR_GIS.txt", "cdump", "MESSAGE"]
    row["files_ok"] = all((d / f).exists() and (d / f).stat().st_size > 0 for f in files)
    if not row["files_ok"]:
        return row
    rec = json.loads((d / "completion_receipt.json").read_text())
    meta = json.loads((d / "run_metadata.json").read_text())
    row["config_ok"] = rec["configuration"] == asdict(H.config(code))
    row["actual"] = rec["actual_emitted_particles"]
    row["runtime_min"] = rec["model_runtime_seconds"] / 60
    row["footprint_sum"] = meta["footprint_sensitivity_sum"]
    row["survival"] = len(active_endpoints(d, meta, rec["actual_emitted_particles"])) / rec["actual_emitted_particles"]
    m = stamp.month
    near = ref[(ref.station == code) & (((ref.time_utc.dt.month - m) % 12).isin([0, 1, 11]))]
    row["ref_n"] = len(near)
    row["ref_min"], row["ref_median"], row["ref_max"] = near.footprint_sum.min(), near.footprint_sum.median(), near.footprint_sum.max()
    row["ref_survival_min"] = near.survival.min()
    row["in_range"] = bool(row["ref_min"] <= row["footprint_sum"] <= row["ref_max"])
    row["in_loose_range"] = bool(0.5 * row["ref_min"] <= row["footprint_sum"] <= 2 * row["ref_max"])
    row["survival_ok"] = bool(row["survival"] >= min(0.95, row["ref_survival_min"]))
    row["ok"] = bool(row["files_ok"] and row["config_ok"] and row["actual"] >= 2000
                     and row["in_loose_range"] and row["survival_ok"])
    return row


def verify(phase: str, first: int = 0, write: bool = True) -> pd.DataFrame:
    t = receptors()
    t = t[t.phase == phase].sort_values(["time_utc", "station"])
    if first:
        t = t.head(first)
    ref = reference_2025()
    rows = [check_run(r.station, r.time_utc, ref) if done(r.station, r.time_utc)
            else dict(station=r.station, time_utc=r.time_utc, files_ok=False, ok=False, missing=True)
            for r in t.itertuples()]
    v = pd.DataFrame(rows)
    if write:
        v.to_csv(TABLES / f"verify_{phase}{'_first%d' % first if first else ''}.csv", index=False)
    return v


def repro() -> dict:
    """Rerun one a127 receptor through this module and compare with the existing footprint."""
    import xarray as xr
    code, stamp = REPRO_RECEPTOR
    ensure_run(code, stamp, REPRO, purpose="a150 reproduction of an a127 receptor")
    a, b = H.run_dir(code, stamp), run_dir(code, stamp, REPRO)
    out = dict(station=code, receptor_utc=str(stamp), a127_dir=str(a), a150_dir=str(b), checked_utc=now())
    for f in ("cdump", "endpoints.txt", "PAR_GIS.txt", "footprint_hourly.csv.gz", "footprint.txt"):
        out[f"identical_{f}"] = sha256(a / f) == sha256(b / f)
    for f in ("footprint.nc", "footprint_layers.nc"):
        x, y = xr.open_dataset(a / f), xr.open_dataset(b / f)
        for v in x.data_vars:
            if x[v].dtype.kind != "f":
                continue
            dx = np.abs(x[v].values - y[v].values)
            out[f"{f}:{v}:max_abs_diff"] = float(np.nanmax(dx))
            out[f"{f}:{v}:max_value"] = float(np.nanmax(np.abs(x[v].values)))
        x.close(), y.close()
    ma = json.loads((a / "run_metadata.json").read_text())["footprint_sensitivity_sum"]
    mb = json.loads((b / "run_metadata.json").read_text())["footprint_sensitivity_sum"]
    out["sum_a127"], out["sum_a150"] = ma, mb
    out["control_diff_lines"] = [(p, q) for p, q in zip((a / "CONTROL").read_text().splitlines(),
                                                        (b / "CONTROL").read_text().splitlines()) if p != q]
    out["setup_identical"] = (a / "SETUP.CFG").read_text() == (b / "SETUP.CFG").read_text()
    diffs = [v for k, v in out.items() if k.endswith("max_abs_diff")]
    out["match"] = bool(out["identical_cdump"] or (max(diffs) <= 1e-6 * max(
        v for k, v in out.items() if k.endswith("max_value")) and np.isclose(ma, mb, rtol=1e-6)))
    write_json(TABLES / "repro_check.json", out)
    return out


# ------------------------------------------------------------- campaign state
class State:
    def __init__(self):
        self.lock = threading.Lock()
        self.d = json.loads(STATE.read_text()) if STATE.exists() else {}
        self.d.setdefault("phases", {p: dict(state="planned") for p in PHASE_ORDER})
        self.d.setdefault("met", {})
        self.d.setdefault("fetch_log", [])
        self.d.setdefault("failed_runs", {})

    def save(self):
        with self.lock:
            write_json(STATE, self.d)

    def set(self, *keys, value):
        with self.lock:
            node = self.d
            for k in keys[:-1]:
                node = node.setdefault(k, {})
            node[keys[-1]] = value
        self.save()


def free_bytes() -> int:
    return shutil.disk_usage(ROOT).free


def downloaded_bytes() -> int:
    return sum(p.stat().st_size for p in MET.glob("gdas1.*") if p.is_file() and not p.is_symlink()
               and not p.name.endswith((".json", ".part", ".tmp")))


def fetch_week(name: str, st: State) -> str:
    rp = receipt_path(name)
    if rp.exists():
        return "ready"
    h = head(name)
    if h["http"] != 200:
        st.set("met", name, value=dict(status="unpublished", http=h["http"], checked_utc=h["checked_utc"]))
        return "unpublished"
    size = int(h["bytes"])
    if free_bytes() - size < FREE_FLOOR_BYTES:
        st.set("met", name, value=dict(status="held_space"))
        return "held_space"
    part, target = MET / f"{name}.part", MET / name
    t0 = time.monotonic()
    start_bytes = part.stat().st_size if part.exists() else 0
    for attempt in range(6):
        if part.exists() and part.stat().st_size == size:
            break
        subprocess.run(["curl", "-s", "-f", "-C", "-", "--retry", "5", "--retry-delay", "20", "--max-time", "7200",
                        "-o", str(part), f"{READY}/{name}"])
        if not (part.exists() and part.stat().st_size == size):
            time.sleep(15)
    if not (part.exists() and part.stat().st_size == size):
        got = part.stat().st_size if part.exists() else 0
        st.set("met", name, value=dict(status="failed", bytes=got, expected=size))
        return "failed"
    seconds = time.monotonic() - t0
    digest = sha256(part)
    part.replace(target)
    rec = dict(file=name, bytes=size, sha256=digest, source=f"{READY}/{name}", last_modified=h["last_modified"],
               downloaded_utc=now(), transfer_seconds=round(seconds, 1), resumed_from_bytes=start_bytes)
    write_json(rp, rec)
    with st.lock:
        st.d["fetch_log"].append(dict(file=name, bytes=size, seconds=round(seconds, 1), done_utc=rec["downloaded_utc"]))
        st.d["met"][name] = dict(status="ready")
    st.save()
    return "ready"


def write_manifest() -> None:
    files = [json.loads(p.read_text()) for p in sorted(MET.glob("*.receipt.json"))]
    write_json(MET / "manifest.json", dict(updated_utc=now(), note="one receipt per week; linked weeks are a127 files read in place",
                                           files=files))


def phase_weeks(ph: str, t: pd.DataFrame) -> list[str]:
    out = []
    for s in t[t.phase == ph].sort_values("time_utc").time_utc:
        out += [w for w in weeks_for(s) if w not in out]
    return out


def space_check(ph: str, t: pd.DataFrame, st: State) -> tuple[bool, dict]:
    sizes = pd.read_csv(TABLES / "met_remote_sizes.csv").set_index("file").bytes
    weeks = [w for w in phase_weeks(ph, t) if not receipt_path(w).exists()]
    remaining = float(np.nansum([sizes.get(w, np.nan) for w in weeks]))
    runs = int(sum(not done(r.station, r.time_utc) for r in t[t.phase == ph].itertuples()))
    total_new = downloaded_bytes() + remaining
    free_after = free_bytes() - remaining - runs * RUN_BYTES
    ok = total_new <= MET_LIMIT_BYTES and free_after >= FREE_FLOOR_BYTES
    info = dict(checked_utc=now(), remaining_download_GB=remaining / 1e9, new_met_total_GB=total_new / 1e9,
                free_GB_now=free_bytes() / 1e9, free_GB_after=free_after / 1e9, ok=ok)
    st.set("phases", ph, "space_check", value=info)
    return ok, info


def downloader(st: State, t: pd.DataFrame, gate_weeks: list[str], stop_evt: threading.Event) -> None:
    order = [("gate", gate_weeks)] + [(ph, phase_weeks(ph, t)) for ph in PHASE_ORDER]
    for ph, weeks in order:
        if ph != "gate":
            if ph != "p1":
                while st.d.get("gate", {}).get("state") not in ("passed", "failed") and not stop_evt.is_set():
                    time.sleep(30)
                if st.d.get("gate", {}).get("state") != "passed":
                    return
            ok, info = space_check(ph, t, st)
            if not ok:
                st.set("phases", ph, "met_state", value="halted: space or 450 GB limit")
                print(f"downloader: {ph} halted by space check {info}", flush=True)
                return
            st.set("phases", ph, "met_state", value="downloading")
        todo = [w for w in weeks if not receipt_path(w).exists()]
        t0 = time.monotonic()
        nbytes = 0
        with ThreadPoolExecutor(FETCH_WORKERS) as pool:
            futures = {pool.submit(fetch_week, w, st): w for w in todo}
            for f in futures:
                w = futures[f]
                try:
                    s = f.result()
                except Exception:  # noqa: BLE001
                    s = "error"
                    print(f"downloader: {w} error\n{traceback.format_exc()}", flush=True)
                if s == "ready" and not (MET / w).is_symlink():
                    nbytes += (MET / w).stat().st_size
                print(f"met {w}: {s}", flush=True)
                if stop_evt.is_set() or STOP.exists():
                    pool.shutdown(wait=True, cancel_futures=True)
                    return
        wall = time.monotonic() - t0
        if nbytes:
            with st.lock:
                st.d.setdefault("fetch_batches", []).append(dict(batch=ph, bytes=nbytes, wall_seconds=round(wall, 1),
                                                                 MB_per_s=round(nbytes / wall / 1e6, 2), done_utc=now()))
            st.save()
        write_manifest()
        if ph != "gate":
            st.set("phases", ph, "met_state", value="done")
    st.set("met_state", value="all phases fetched")


def week_status(w: str, st: State) -> str:
    if receipt_path(w).exists():
        return "ready"
    return st.d["met"].get(w, {}).get("status", "pending")


def run_jobs(jobs: list[tuple], workers: int, st: State, label: str, met_done) -> dict:
    """Run (fn, code, stamp) jobs as their meteorology arrives; up to three attempts each."""
    pending = list(jobs)
    running = {}
    attempts = Counter()
    result = dict(done=0, failed=[], deferred=[])
    last_status = 0.0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        while pending or running:
            stopping = STOP.exists()
            if not stopping:
                for job in list(pending):
                    if len(running) >= workers:
                        break
                    _, code, stamp, root = job
                    ws = [week_status(w, st) for w in weeks_for(stamp)]
                    if all(s == "ready" for s in ws):
                        pending.remove(job)
                        running[pool.submit(job[0], code, stamp, root)] = job
            if not running:
                if stopping:
                    break
                blocked = [j for j in pending if any(week_status(w, st) in ("unpublished", "failed", "held_space")
                                                     for w in weeks_for(j[2]))]
                if met_done() and pending:
                    result["deferred"] += [(j[1], str(j[2])) for j in pending]
                    break
                if blocked and len(blocked) == len(pending) and met_done():
                    result["deferred"] += [(j[1], str(j[2])) for j in pending]
                    break
                time.sleep(30)
                continue
            fin, _ = wait(list(running), timeout=60, return_when=FIRST_COMPLETED)
            for f in fin:
                job = running.pop(f)
                _, code, stamp, root = job
                try:
                    e = f.result()
                    result["done"] += 1
                    print(f"[{label}] {code} {stamp:%Y-%m-%dT%HZ} {e/60:.1f} min", flush=True)
                except Exception:  # noqa: BLE001 - logged and retried
                    attempts[(code, stamp)] += 1
                    tb = traceback.format_exc()
                    print(f"[{label}] FAILED {code} {stamp:%Y-%m-%dT%HZ} attempt {attempts[(code, stamp)]}\n{tb}", flush=True)
                    if attempts[(code, stamp)] < 3:
                        pending.append(job)
                    else:
                        result["failed"].append((code, str(stamp)))
                        st.set("failed_runs", f"{code} {stamp:%Y-%m-%dT%HZ}", value=tb.strip().splitlines()[-1])
            if time.monotonic() - last_status > 120:
                write_status(st)
                last_status = time.monotonic()
    write_status(st)
    return result


def smoke_recheck(st: State, t: pd.DataFrame) -> bool:
    """Re-run the check of the 2009 smoke receptor and record the result in the gate state."""
    r = t[t.phase == "p3"].sort_values(["time_utc", "station"]).iloc[0]
    sm = check_run(r.station, r.time_utc, reference_2025()) if done(r.station, r.time_utc) else dict(ok=False)
    pd.DataFrame([sm]).to_csv(TABLES / "verify_p3_smoke.csv", index=False)
    with st.lock:
        st.d["gate"]["p3_smoke_ok"] = bool(sm.get("ok"))
        st.d["gate"]["p3_smoke_rechecked_utc"] = now()
    st.save()
    return bool(sm.get("ok"))


def gate(st: State, t: pd.DataFrame, workers: int, gate_met_done) -> bool:
    if st.d.get("gate", {}).get("state") == "passed":
        if not st.d["gate"].get("p3_smoke_ok"):
            smoke_recheck(st, t)
        return True
    p1 = t[t.phase == "p1"].sort_values(["time_utc", "station"]).head(GATE_FIRST)
    smoke = t[t.phase == "p3"].sort_values(["time_utc", "station"]).head(1)
    jobs = [(ensure_run, r.station, r.time_utc, RUNS) for r in p1.itertuples()]
    jobs.append((lambda c, s, root: (repro(), 0.0)[1], REPRO_RECEPTOR[0], REPRO_RECEPTOR[1], REPRO))
    jobs += [(ensure_run, r.station, r.time_utc, RUNS) for r in smoke.itertuples()]
    st.set("gate", value=dict(state="running", started_utc=now()))
    res = run_jobs(jobs, workers, st, "gate", gate_met_done)
    v = verify("p1", first=GATE_FIRST)
    rp = json.loads((TABLES / "repro_check.json").read_text()) if (TABLES / "repro_check.json").exists() else {}
    sm = None
    if len(smoke):
        r = smoke.iloc[0]
        sm = check_run(r.station, r.time_utc, reference_2025()) if done(r.station, r.time_utc) else dict(ok=False)
        pd.DataFrame([sm]).to_csv(TABLES / "verify_p3_smoke.csv", index=False)
    passed = bool(len(v) == GATE_FIRST and v.ok.all() and rp.get("match", False))
    st.set("gate", value=dict(state="passed" if passed else "failed", finished_utc=now(),
                              first10_ok=int(v.ok.sum()), first10_in_strict_range=int(v.get("in_range", pd.Series(dtype=bool)).fillna(False).sum()),
                              repro_match=rp.get("match"), p3_smoke_ok=bool(sm and sm.get("ok")),
                              failed=res["failed"], deferred=res["deferred"]))
    return passed


def phase_verdict(ph: str, st: State, res: dict) -> bool:
    v = verify(ph)
    n = len(v)
    missing = int((~v.files_ok).sum())
    deferred = len(res.get("deferred", []))
    bad = int((v.files_ok & ~v.ok).sum())
    ok = (missing - deferred) <= 0.02 * n and bad <= 0.05 * n
    st.set("phases", ph, "verify", value=dict(receptors=n, complete=int(v.files_ok.sum()), missing=missing,
                                             deferred=deferred, flagged=bad, ok=bool(ok), checked_utc=now()))
    return ok


def campaign(workers: int) -> None:
    workers = min(workers, MAX_WORKERS)
    LR.mkdir(parents=True, exist_ok=True)
    st = State()
    st.d["pid"] = os.getpid()
    st.d["started_utc"] = now()
    st.d["workers"] = workers
    st.d["state"] = "running"
    for ph in PHASE_ORDER:                  # met states of an earlier process are stale
        st.d["phases"][ph]["met_state"] = "planned"
    st.save()
    t = receptors()
    link_existing()
    write_manifest()
    p1 = t[t.phase == "p1"].sort_values(["time_utc", "station"]).head(GATE_FIRST)
    smoke = t[t.phase == "p3"].sort_values(["time_utc", "station"]).head(1)
    gate_weeks = []
    for s in list(p1.time_utc) + list(smoke.time_utc) + [REPRO_RECEPTOR[1]]:
        gate_weeks += [w for w in weeks_for(s) if w not in gate_weeks]
    met_state = {}
    stop_evt = threading.Event()

    def dl():
        try:
            downloader(st, t, gate_weeks, stop_evt)
        finally:
            met_state["all_done"] = True

    th = threading.Thread(target=dl, daemon=True)
    th.start()

    def gate_done():
        return all(receipt_path(w).exists() or week_status(w, st) in ("unpublished", "failed") for w in gate_weeks) \
            or met_state.get("all_done", False)
    write_status(st)
    if not gate(st, t, workers, gate_done):
        st.set("state", value="halted at the first-10 gate; see tables/verify_p1_first10.csv and repro_check.json")
        stop_evt.set()
        write_status(st)
        return
    write_status(st)
    deferred_all = []
    for ph in PHASE_ORDER:
        if STOP.exists():
            break
        if ph == "p3" and not st.d["gate"].get("p3_smoke_ok"):
            st.set("phases", ph, "state", value="held: the 2009 smoke run failed")
            break
        while st.d["phases"][ph].get("met_state") in (None, "planned") and not met_state.get("all_done"):
            time.sleep(30)
        if str(st.d["phases"][ph].get("met_state", "")).startswith("halted"):
            st.set("phases", ph, "state", value="halted before start: space or 450 GB limit")
            break
        st.set("phases", ph, "state", value="running")
        st.set("phases", ph, "started_utc", value=now())
        jobs = [(ensure_run, r.station, r.time_utc, RUNS) for r in t[t.phase == ph].sort_values(["time_utc", "station"]).itertuples()]
        res = run_jobs(jobs, workers, st, ph,
                       lambda ph=ph: st.d["phases"][ph].get("met_state") == "done" or met_state.get("all_done", False))
        if STOP.exists():
            st.set("phases", ph, "state", value="stopped by STOP file")
            break
        deferred_all += res["deferred"]
        ok = phase_verdict(ph, st, res)
        st.set("phases", ph, "state", value="verified" if ok else "failed verification")
        st.set("phases", ph, "finished_utc", value=now())
        write_status(st)
        if not ok:
            break
    # tail: receptors whose GDAS1 week was not yet published when their phase ran
    if deferred_all and not STOP.exists():
        st.set("tail", value=dict(state="waiting for GDAS1", receptors=len(deferred_all), started_utc=now()))
        deadline = time.monotonic() + 48 * 3600
        while time.monotonic() < deadline and not STOP.exists():
            need = sorted({w for c, s in deferred_all for w in weeks_for(pd.Timestamp(s)) if not receipt_path(w).exists()})
            for w in need:
                fetch_week(w, st)
            if all(receipt_path(w).exists() for w in need):
                break
            write_status(st)
            time.sleep(1800)
        write_manifest()
        jobs = [(ensure_run, c, pd.Timestamp(s), RUNS) for c, s in deferred_all]
        res = run_jobs(jobs, workers, st, "tail", lambda: True)
        st.set("tail", value=dict(state="finished", done=res["done"], failed=res["failed"], still_deferred=res["deferred"],
                                  finished_utc=now()))
    stop_evt.set()
    st.set("state", value="finished" if not STOP.exists() else "stopped by STOP file")
    st.set("finished_utc", value=now())
    write_status(st)


# ------------------------------------------------------------------- status
def progress() -> pd.DataFrame:
    t = receptors()
    t["done"] = [done(r.station, r.time_utc) for r in t.itertuples()]
    t["year"], t["month"] = t.time_utc.dt.year, t.time_utc.dt.month
    return t


def progress_table(t: pd.DataFrame) -> str:
    g = t.groupby(["phase", "station", "year", "month"]).done.agg(["sum", "size"])
    g["cell"] = g["sum"].astype(str) + "/" + g["size"].astype(str)
    p = g.cell.unstack("month").fillna("")
    p.columns = [pd.Timestamp(2000, int(c), 1).strftime("%b") for c in p.columns]
    tot = t.groupby(["phase", "station", "year"]).done.agg(["sum", "size"])
    p["total"] = tot["sum"].astype(str) + "/" + tot["size"].astype(str)
    p = p.reset_index()
    head_ = "| " + " | ".join(p.columns) + " |"
    sep = "|" + "---|" * len(p.columns)
    return "\n".join([head_, sep] + ["| " + " | ".join(str(x) for x in r) + " |" for r in p.itertuples(index=False)])


def write_status(st: State | None = None) -> None:
    if st:
        with st.lock:
            d = json.loads(json.dumps(st.d, default=str))
    else:
        d = json.loads(STATE.read_text()) if STATE.exists() else {}
    t = progress()
    pid = d.get("pid")
    alive = bool(pid) and Path(f"/proc/{pid}").exists()
    plan_ = pd.read_csv(TABLES / "plan_phases.csv") if (TABLES / "plan_phases.csv").exists() else None
    batches = d.get("fetch_batches", [])
    flog = d.get("fetch_log", [])
    rate = (sum(b["bytes"] for b in batches) / sum(b["wall_seconds"] for b in batches) / 1e6) if batches else None
    per_file = (np.median([f["bytes"] / max(f["seconds"], 1) / 1e6 for f in flog])) if flog else None
    last_week = max((json.loads(p.read_text()).get("file") for p in MET.glob("gdas1.*26.w*.receipt.json")),
                    key=lambda n: (pd.Timestamp(datetime.strptime(n.split(".")[1][:5], "%b%y")), n), default=None)
    runs_done = t[t.done]
    rts = []
    for r in runs_done.tail(60).itertuples():
        try:
            rts.append(json.loads((run_dir(r.station, r.time_utc) / "completion_receipt.json").read_text())["model_runtime_seconds"])
        except Exception:  # noqa: BLE001
            pass
    mean_rt = float(np.mean(rts)) if rts else 12.6 * 60
    remaining = int((~t.done).sum())
    eta_h = remaining * mean_rt / 3600 / max(d.get("workers", MAX_WORKERS), 1)
    lines = [
        "# Long-record HYSPLIT campaign (a150)", "",
        f"Updated {now()} UTC ({wib()}). Overall state: **{d.get('state', 'running' if alive else 'not running')}**.", "",
        f"- PID: `{pid}` ({'alive' if alive else 'not running'}); started {d.get('started_utc')} UTC; workers {d.get('workers')} at nice 19",
        f"- Log: `outputs/hysplit/long_record/logs/campaign.log`",
        f"- Resume (idempotent; finished runs and weeks are skipped by receipt): `bash scripts/a151_long_record_launch.sh`",
        "- Stop cleanly: `touch outputs/hysplit/long_record/STOP` (running HYSPLIT jobs finish, nothing new starts); "
        "remove the file before resuming",
        "- Progress: `/run/media/workstation-llm/HDD2/.venv/bin/python scripts/a150_hysplit_long_record.py status`",
        f"- Done {int(t.done.sum())} of {len(t)} receptors; mean runtime of recent runs {mean_rt/60:.1f} min; "
        f"remaining about {eta_h:.1f} h at {d.get('workers', MAX_WORKERS)} workers (finish near "
        f"{wib(pd.Timestamp.now(tz='UTC') + pd.Timedelta(hours=eta_h))}, excluding meteorology waits)",
        f"- GDAS1: last 2026 week on disk `{last_week}`; aggregate download rate "
        f"{'%.1f MB/s' % rate if rate else 'not yet measured'}; median single transfer "
        f"{'%.1f MB/s' % per_file if per_file else 'n/a'}; new meteorology on disk {downloaded_bytes()/1e9:.1f} GB; "
        f"free on HDD2 {free_bytes()/1e9:.0f} GB", "",
        "## Rules", "",
        "Receptor 06 UTC; valid day = at least two non-suspect 05-07 UTC hours of CO2 or of CH4; "
        "every second day on the grid anchored at 2025-01-01 (the a127 grid); a measured station-month without a valid "
        "grid day takes its off-grid valid days. Configuration = a127 (hycs_std ICHEM=8, 2000 particles, 120 h, 0.25 degree, "
        "60 x 100 degree grid, 100 m inlet, seed 0, GDAS1). Phases chain p1, p2, p3; each must pass verification "
        "(tables/verify_<phase>.csv) before the next starts. Space gate per phase: new meteorology at most 450 GB, "
        "free space after the phase at least 400 GB.", "",
        "## Plan", "",
    ]
    if plan_ is not None:
        lines += ["| " + " | ".join(plan_.columns) + " |", "|" + "---|" * len(plan_.columns)]
        lines += ["| " + " | ".join(f"{x:.1f}" if isinstance(x, float) else str(x) for x in r) + " |" for r in plan_.itertuples(index=False)]
        lines.append("")
    g = d.get("gate", {})
    lines += ["## Gate and phases", "",
              f"- First-10 gate: {g.get('state', 'not started')}; first 10 ok {g.get('first10_ok')}, "
              f"in strict 2025 seasonal range {g.get('first10_in_strict_range')}; reproduction match {g.get('repro_match')}; "
              f"2009 smoke run ok {g.get('p3_smoke_ok')}"]
    for ph in PHASE_ORDER:
        x = d.get("phases", {}).get(ph, {})
        lines.append(f"- {ph}: state {x.get('state', 'planned')}; meteorology {x.get('met_state', 'not started')}; "
                     f"space check {x.get('space_check')}; verification {x.get('verify')}")
    if d.get("tail"):
        lines.append(f"- tail (unpublished GDAS1 weeks): {d['tail']}")
    if d.get("failed_runs"):
        lines += ["", "Failed runs (three attempts): " + "; ".join(f"{k}: {v}" for k, v in d["failed_runs"].items())]
    unpub = sorted(k for k, v in d.get("met", {}).items() if v.get("status") != "ready")
    if unpub:
        lines.append(f"- Weeks not ready: {', '.join(f'{k} ({d['met'][k].get('status')})' for k in unpub)}")
    lines += ["", "## Done / planned per phase, tower and month", "", progress_table(t), ""]
    tmp = STATUS_MD.with_suffix(".tmp")
    tmp.write_text("\n".join(lines))
    tmp.replace(STATUS_MD)


def status() -> None:
    t = progress()
    print(t.groupby(["phase", "station", "year"]).done.agg(["sum", "size"]).to_string())
    if STATE.exists():
        d = json.loads(STATE.read_text())
        print("state:", d.get("state"), "| gate:", d.get("gate", {}).get("state"),
              "| phases:", {p: v.get("state") for p, v in d.get("phases", {}).items()})


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("stage", choices=["obs", "select", "plan", "campaign", "repro", "verify", "status", "check"])
    p.add_argument("--station")
    p.add_argument("--time")
    p.add_argument("--workers", type=int, default=MAX_WORKERS)
    p.add_argument("--phase", default="p1")
    p.add_argument("--first", type=int, default=0)
    p.add_argument("--refresh", action="store_true")
    a = p.parse_args()
    LOGS.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    if a.stage == "obs":
        stage_obs()
    elif a.stage == "select":
        select()
    elif a.stage == "plan":
        plan(a.refresh)
    elif a.stage == "campaign":
        campaign(a.workers)
    elif a.stage == "repro":
        print(json.dumps(repro(), indent=1, default=str))
    elif a.stage == "check":                       # one run, read only
        print(pd.Series(check_run(a.station, pd.Timestamp(a.time), reference_2025())).to_string())
    elif a.stage == "verify":
        print(verify(a.phase, a.first).to_string())
    else:
        status()


if __name__ == "__main__":
    main()
