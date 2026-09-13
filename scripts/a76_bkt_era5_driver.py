#!/usr/bin/env python3
"""ERA5 as a bounded alternative HYSPLIT-STILT driver for BKT.

Stages
  fetch    - download hourly ERA5 pressure-level and single-level GRIB from the
             Copernicus Climate Data Store (one request per day and dataset,
             resumable, SHA-256 provenance), 50-160E / 40S-30N at 0.25 degree.
  convert  - run NOAA's ``era52arl`` (HYSPLIT 5.4.2) per day into ARL files.
  check    - parse ARL index headers and run a 6 h HYSPLIT probe.
  run      - the four benchmark anchors (three seeds) and the 26 September
             forward case (three seeds, 10,000 particles) with the same
             receptor, grid, layers and STILT settings as the GFS revision.

Limits: the converter reads pressure levels only (not the 137 model levels),
so near-surface vertical resolution is coarser than the 55-level GFS hybrid
archive; ERA5 carries no convective mass fluxes, so convection stays off.
Credentials are read by the CDS client from its own configuration; this
script never handles them.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

import numpy as np
import pandas as pd

import a37_bkt_footprint as model
import a74_bkt_simulation_revision as rev
import ghg_common as G
from a39_bkt_refinement import actual_particles

ROOT = model.ROOT
DATA = ROOT / "data/hysplit/era5"
GRIB = DATA / "grib"
ARL = DATA / "arl"
LIB = DATA / "lib"
OUT = ROOT / "outputs/hysplit/era5"
RUNS = OUT / "runs"
HYSPLIT_HOME = rev.HYSPLIT_HOME
AREA = [20, 70, -25, 140]  # N, W, S, E. Smaller than the wide GFS crop: the CDS route from this
# site runs at tens of kB/s, so volume is the binding constraint (13 September 2026).
LEVELS = [1000, 950, 925, 900, 850, 800, 750, 700, 600, 500, 400, 300, 250, 200, 150, 100]
CASES = list(rev.ANCHORS) + [rev.FORWARD_CASE]
LABEL = "ECMWF ERA5 reanalysis, 0.25 degree, hourly, 16 pressure levels, 70-140E 25S-20N, ARL format via era52arl"
PRESSURE_VARS = ["geopotential", "temperature", "u_component_of_wind", "v_component_of_wind",
                 "vertical_velocity", "relative_humidity"]
SURFACE_ANALYSIS_VARS = ["2m_temperature", "10m_u_component_of_wind", "10m_v_component_of_wind",
                         "total_cloud_cover", "surface_pressure", "2m_dewpoint_temperature",
                         "boundary_layer_height", "convective_available_potential_energy",
                         "geopotential", "friction_velocity"]
SURFACE_FORECAST_VARS = ["total_precipitation", "surface_sensible_heat_flux",
                         "surface_solar_radiation_downwards", "surface_latent_heat_flux"]
# ECMWF accumulated surface fluxes (sshf, slhf) are positive DOWNWARD in J m-2
# per hour; HYSPLIT's SHTF and LTHF are positive UPWARD in W m-2. The stock
# era52arl map only divides by 3600, which hands HYSPLIT a strongly negative
# daytime heat flux and a spuriously stable boundary layer (found 13 September
# 2026: 1.3 to 3.8 times the GFS surface sensitivity at the anchors). The sign
# is flipped here for both turbulent heat fluxes; radiation (ssrd) stays positive.
CFG = """&SETUP
 numatm = 6,
 atmgrb = 'z','t','u','v','w','r',
 atmcat =      129 ,   130 ,    131 ,   132 ,   135 ,    157 ,
 atmnum =      129 ,   130 ,    131 ,   132 ,   135 ,    157 ,
 atmcnv =     0.102 ,  1.0 ,   1.0 ,   1.0 ,  0.01,   1.0 ,
 atmarl = 'HGTS','TEMP','UWND','VWND','WWND','RELH',
 numsfc = 14,
 sfcgrb = '2t','10v','10u','tcc','sp','2d','blh','cape','z','tp','sshf','ssrd','slhf','zust',
 sfccat =   167,   166,  165,  164, 134, 168, 159, 59,  129, 228, 146, 169, 147, 3
 sfcnum =   167,   166,  165,  164, 134, 168, 159, 59,  129, 228, 146, 169, 147, 3
 sfccnv =   1.0, 1.0, 1.0,  1.0, 0.01 ,1.0, 1.0, 1.0 ,0.102, 1.0, -0.00028, 0.00028, -0.00028, 1.0
 sfcarl = 'T02M','V10M','U10M','TCLD','PRSS','DP2M','PBLH','CAPE','SHGT','TPP1','SHTF','DSWF','LTHF','USTR',
 numlev = %d
 plev = %s
/
"""


def needed_days(period: str = "cases") -> pd.DatetimeIndex:
    """'cases': anchors plus forward case (15 days); 'full': the whole inversion
    period with its five-day spin-back, 4 September to 6 October 2019 (33 days)."""
    if period == "full":
        return pd.date_range("2019-09-04", "2019-10-06", freq="D")
    days: set[pd.Timestamp] = set()
    for stamp in CASES:
        days.update(pd.date_range((stamp - pd.Timedelta(hours=rev.HOURS_BACK)).normalize(), stamp.normalize(), freq="D"))
    return pd.DatetimeIndex(sorted(days))


def sha256(path: Path) -> str:
    return model.sha256_file(path)


def grib_path(day: pd.Timestamp, kind: str) -> Path:
    return GRIB / f"{day:%Y%m%d}_{kind}.grib"


def request(kind: str, day: pd.Timestamp) -> tuple[str, dict]:
    common = {"product_type": ["reanalysis"], "year": f"{day:%Y}", "month": f"{day:%m}", "day": f"{day:%d}",
              "time": [f"{h:02d}:00" for h in range(24)], "area": AREA, "grid": [0.25, 0.25],
              "data_format": "grib", "download_format": "unarchived"}
    if kind == "pl":
        return "reanalysis-era5-pressure-levels", {**common, "variable": PRESSURE_VARS,
                                                   "pressure_level": [str(p) for p in LEVELS]}
    if kind == "sfc":
        return "reanalysis-era5-single-levels", {**common, "variable": SURFACE_ANALYSIS_VARS}
    if kind == "fc":
        return "reanalysis-era5-single-levels", {**common, "variable": SURFACE_FORECAST_VARS}
    raise ValueError(kind)


def bind_interface(device: str) -> None:
    """Pin every new TCP connection of this process to one network device.

    The workstation has a LAN default route (about 0.3 MB/s abroad) and a
    WiFi link (about 12 MB/s). SO_BINDTODEVICE selects the device without
    touching the routing table and needs no privileges on this kernel.
    """
    import socket
    original = socket.socket.connect

    def connect(self, address):
        if self.family == socket.AF_INET and self.type == socket.SOCK_STREAM:
            self.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, device.encode())
        return original(self, address)
    socket.socket.connect = connect
    print(f"TCP connections bound to {device}", flush=True)


def fetch(workers: int = 2, period: str = "cases", interface: str | None = None) -> None:
    import cdsapi
    if interface:
        bind_interface(interface)
    GRIB.mkdir(parents=True, exist_ok=True)
    client = cdsapi.Client(quiet=True)
    days = needed_days(period)
    jobs = [(kind, day) for day in days for kind in ("pl", "sfc", "fc")
            if not grib_path(day, kind).with_suffix(".grib.json").exists()]
    print(f"{len(jobs)} CDS requests pending for {len(days)} days ({period})", flush=True)

    def one(item: tuple[str, pd.Timestamp]) -> str:
        kind, day = item
        target = grib_path(day, kind)
        dataset, body = request(kind, day)
        started = time.monotonic()
        partial = target.with_suffix(".grib.part")
        client.retrieve(dataset, body, str(partial))
        if not partial.is_file() or partial.stat().st_size < 1_000_000:
            raise RuntimeError(f"CDS delivered an implausibly small file: {partial}")
        partial.replace(target)
        record = dict(dataset=dataset, request=body, provider="Copernicus Climate Data Store, ECMWF ERA5",
                      filename=target.name, bytes=target.stat().st_size, sha256=sha256(target),
                      retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
                      seconds=time.monotonic() - started, licence="CC-BY-4.0 (Copernicus C3S)")
        target.with_suffix(".grib.json").write_text(json.dumps(record, indent=2) + "\n")
        return f"{target.name} {target.stat().st_size/1e6:.0f} MB in {record['seconds']/60:.1f} min"

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(one, item): item for item in jobs}
        for future in as_completed(futures):
            try:
                print(future.result(), flush=True)
            except Exception as error:  # noqa: BLE001
                print(f"FAILED {futures[future]}: {error!r}", flush=True)
    missing = [(k, d) for d in days for k in ("pl", "sfc", "fc") if not grib_path(d, k).with_suffix(".grib.json").exists()]
    if missing:
        raise RuntimeError(f"{len(missing)} requests still missing; rerun fetch")
    print("fetch complete", flush=True)


def library_dir() -> Path:
    """Versioned eccodes names the NOAA binary was linked against."""
    LIB.mkdir(parents=True, exist_ok=True)
    for name in ("libeccodes_f90.so", "libeccodes.so"):
        link = LIB / f"{name}.0"
        if not link.exists():
            source = Path("/usr/local/lib") / name
            if not source.exists():
                raise FileNotFoundError(source)
            link.symlink_to(source)
    return LIB


def arl_path(day: pd.Timestamp) -> Path:
    return ARL / f"{day:%Y%m%d}_era5"


def convert(days: pd.DatetimeIndex | None = None) -> None:
    ARL.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "LD_LIBRARY_PATH": f"{library_dir()}:/usr/local/lib:" + os.environ.get("LD_LIBRARY_PATH", "")}
    for day in (days if days is not None else needed_days()):
        target = arl_path(day)
        if target.with_suffix(".json").exists():
            continue
        work = ARL / f"work_{day:%Y%m%d}"
        shutil.rmtree(work, ignore_errors=True); work.mkdir(parents=True)
        (work / "era52arl.cfg").write_text(CFG % (len(LEVELS), ", ".join(str(p) for p in LEVELS)))
        for kind, name in (("pl", "DATA.GRIB"), ("sfc", "SFC.GRIB"), ("fc", "SFC2.GRIB")):
            source = grib_path(day, kind)
            if sha256(source) != json.loads(source.with_suffix(".grib.json").read_text())["sha256"]:
                raise ValueError(f"GRIB checksum mismatch: {source}")
            (work / name).symlink_to(source.resolve())
        command = [str(HYSPLIT_HOME / "exec/era52arl"), "-dera52arl.cfg", "-iDATA.GRIB", "-aSFC.GRIB",
                   "-fSFC2.GRIB", "-oDATA.ARL"]
        result = subprocess.run(command, cwd=work, env=env, text=True, capture_output=True)
        (work / "era52arl.log").write_text(result.stdout + "\n--- stderr ---\n" + result.stderr)
        output = work / "DATA.ARL"
        if result.returncode != 0 or not output.is_file() or output.stat().st_size < 10_000_000:
            raise RuntimeError(f"era52arl failed for {day:%Y-%m-%d}; see {work / 'era52arl.log'}")
        output.replace(target)
        header = arl_header(target)
        record = dict(day_utc=str(day.date()), converter="era52arl (HYSPLIT 5.4.2 data2arl)", cfg=CFG % (len(LEVELS), LEVELS),
                      flux_sign="sshf and slhf negated to HYSPLIT upward-positive convention",
                      inputs={k: json.loads(grib_path(day, k).with_suffix(".grib.json").read_text())["sha256"] for k in ("pl", "sfc", "fc")},
                      bytes=target.stat().st_size, sha256=sha256(target), header=header,
                      created_at_utc=datetime.now(timezone.utc).isoformat())
        target.with_suffix(".json").write_text(json.dumps(record, indent=2, default=str) + "\n")
        shutil.copyfile(work / "era52arl.log", target.with_suffix(".log"))
        shutil.rmtree(work)
        print(f"converted {target.name}: {header}", flush=True)


def arl_header(path: Path) -> dict:
    with path.open("rb") as stream:
        label = stream.read(50).decode("ascii", "replace")
        index = stream.read(108).decode("ascii", "replace")
    if label[14:18] != "INDX":
        raise ValueError(f"not an ARL index record: {path}")
    nx, ny, nz = (int(index[93 + i * 3:96 + i * 3]) for i in range(3))
    grid = [float(index[9 + i * 7:16 + i * 7]) for i in range(12)]
    record = nx * ny + 50
    return dict(model=index[:4], nx=nx, ny=ny, nz=nz, spacing=grid[2:4], corner_lat_lon=grid[9:11],
                record_bytes=record, records=path.stat().st_size / record,
                whole_records=(path.stat().st_size % record == 0))


def check() -> None:
    for day in needed_days():
        h = arl_header(arl_path(day))
        if not h["whole_records"] or h["nz"] != len(LEVELS) + 1 or h["spacing"] != [.25, .25]:
            raise ValueError(f"ARL structure unexpected for {day:%Y-%m-%d}: {h}")
    probe = OUT / "probe"
    shutil.rmtree(probe, ignore_errors=True)
    stamp = pd.Timestamp("2019-09-23T06:00")
    cfg = replace(rev.base_config(500, 30.0, 0), meteorology_label=LABEL, hours_back=6, **GRID)
    ctx = {"station": "BKT", "time_utc": stamp.isoformat() + "Z", "purpose": "ERA5 driver probe"}
    directory = model.run_footprint(stamp, ARL, probe, HYSPLIT_HOME, cfg, False,
        meteorology_paths=[arl_path(stamp.normalize())], transport=model.TransportOptions(),
        observation_context=ctx, extra_levels_m=rev.EXTRA_LEVELS_M)
    message = (directory / "MESSAGE").read_text(errors="replace")
    warnings = (directory / "WARNING").read_text(errors="replace") if (directory / "WARNING").exists() else ""
    meta = json.loads((directory / "run_metadata.json").read_text())
    print(f"probe ok: sensitivity {meta['footprint_sensitivity_sum']:.4f}, particles {actual_particles(message)}, "
          f"warnings: {warnings.strip()[:300] or 'none'}", flush=True)


GRID = dict(grid_span_lat_deg=40, grid_span_lon_deg=60)  # inside the 70-140E / 25S-20N meteorology


def jobs(group: str = "cases") -> list[tuple[str, pd.Timestamp, model.FootprintConfig]]:
    items = []
    if group == "cases":
        for seed in rev.SEEDS:
            items.append((f"forward_s{seed}", rev.FORWARD_CASE, replace(rev.base_config(10000, 30.0, seed), meteorology_label=LABEL, **GRID)))
        for seed in rev.SEEDS:
            for stamp in rev.ANCHORS:
                items.append((f"anchor_s{seed}", stamp, replace(rev.base_config(2000, 30.0, seed), meteorology_label=LABEL, **GRID)))
    elif group == "ensemble":
        for seed in rev.SEEDS:
            for stamp in rev.retained_receptors():
                items.append((f"ensemble_s{seed}", stamp, replace(rev.base_config(2000, 30.0, seed), meteorology_label=LABEL, **GRID)))
    else:
        raise ValueError(group)
    return items


def met_paths(stamp: pd.Timestamp) -> list[Path]:
    return [arl_path(d) for d in pd.date_range((stamp - pd.Timedelta(hours=rev.HOURS_BACK)).normalize(), stamp.normalize(), freq="D")]


def ensure_run(name: str, stamp: pd.Timestamp, cfg: model.FootprintConfig, context: dict) -> tuple[Path, float]:
    directory = RUNS / name / f"bkt_{stamp:%Y%m%dT%H%MZ}"
    if (directory / "completion_receipt.json").exists():
        return directory, 0.0
    shutil.rmtree(directory, ignore_errors=True)
    paths = met_paths(stamp)
    for path in paths:
        if sha256(path) != json.loads(path.with_suffix(".json").read_text())["sha256"]:
            raise ValueError(f"ARL checksum mismatch: {path}")
    started = time.monotonic()
    model.run_footprint(stamp, ARL, directory.parent, HYSPLIT_HOME, cfg, False, meteorology_paths=paths,
        transport=model.TransportOptions(), observation_context=context, extra_levels_m=rev.EXTRA_LEVELS_M)
    model.run_checked([str(HYSPLIT_HOME / "exec/par2asc"), "-iPARDUMP", "-oendpoints.txt", "-vendpoint_times.txt", "-a1"],
                      directory, "endpoints")
    (directory / "PARDUMP").unlink()
    elapsed = time.monotonic() - started
    message = (directory / "MESSAGE").read_text(errors="replace")
    actual = actual_particles(message)
    if actual < cfg.particles:
        raise ValueError(f"Fewer particles emitted than requested: {directory}")
    if (directory / "CONTROL").read_text() != model.control_text(stamp, paths, directory, cfg, rev.EXTRA_LEVELS_M):
        raise ValueError(f"CONTROL mismatch: {directory}")
    record = dict(group=name, receptor_utc=stamp.isoformat() + "Z", configuration=asdict(cfg),
        transport_options=asdict(model.TransportOptions()), extra_levels_m=list(rev.EXTRA_LEVELS_M),
        meteorology_files=[str(p.resolve()) for p in paths], meteorology_sha256={p.name: sha256(p) for p in paths},
        actual_emitted_particles=actual, model_runtime_seconds=elapsed,
        convective_mixing_flag_true="Convective mixing -  T" in message,
        output_sha256={n: sha256(directory / n) for n in ("footprint.nc", "footprint_layers.nc", "PAR_GIS.txt", "MESSAGE")},
        created_at_utc=datetime.now(timezone.utc).isoformat())
    (directory / "completion_receipt.json").write_text(json.dumps(record, indent=2) + "\n")
    return directory, elapsed


def run(workers: int, group: str = "cases") -> None:
    import traceback
    observations = G.apply_flags(G.load_station("BKT")).set_index("time_utc")
    items = jobs(group)
    contexts = {s: rev.observation_context(observations, s) for _, s, _ in items}
    pending = [j for j in items if not (RUNS / j[0] / f"bkt_{j[1]:%Y%m%dT%H%MZ}" / "completion_receipt.json").exists()]
    print(f"{len(items)} ERA5 runs declared, {len(pending)} pending", flush=True)
    failures = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(ensure_run, n, s, c, contexts[s]): (n, s) for n, s, c in pending}
        for k, future in enumerate(as_completed(futures), 1):
            name, stamp = futures[future]
            try:
                _, elapsed = future.result()
                print(f"[{k}/{len(pending)}] {name} {stamp:%Y-%m-%dT%HZ} {elapsed/60:.1f} min", flush=True)
            except Exception:  # noqa: BLE001
                failures += 1
                print(f"[{k}/{len(pending)}] FAILED {name} {stamp:%Y-%m-%dT%HZ}\n{traceback.format_exc()}", flush=True)
    if failures:
        raise RuntimeError(f"{failures} ERA5 runs failed")
    print("ERA5 runs complete", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["days", "fetch", "convert", "check", "run"])
    parser.add_argument("--jobs", type=int, default=6)
    parser.add_argument("--period", default="cases", choices=["cases", "full"])
    parser.add_argument("--group", default="cases", choices=["cases", "ensemble"])
    parser.add_argument("--workers", type=int, default=6, help="parallel CDS transfers")
    parser.add_argument("--interface", default=None, help="network device to pin the transfers to (for example wlp0s20f3)")
    args = parser.parse_args()
    if args.stage == "days":
        print("\n".join(str(d.date()) for d in needed_days(args.period)))
    elif args.stage == "fetch":
        fetch(workers=args.workers, period=args.period, interface=args.interface)
    elif args.stage == "convert":
        convert(needed_days(args.period))
    elif args.stage == "check":
        check()
    else:
        run(args.jobs, args.group)
