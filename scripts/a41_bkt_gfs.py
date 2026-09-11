#!/usr/bin/env python3
"""Acquire verified GFS quarter-degree ARL meteorology and run BKT cases."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
import urllib.parse
import urllib.request
import zipfile

import pandas as pd

import a37_bkt_footprint as model

ROOT = model.ROOT
MET = ROOT / "data/hysplit/gfs0p25"
RUNS = ROOT / "outputs/hysplit/gfs"
BASE = "https://noaa-oar-arl-hysplit-pds.s3.amazonaws.com/gfs0p25"
RECEPTOR = model.parse_utc("2019-09-26T01:00:00Z")
LABEL = "NOAA GFS 0.25-degree pseudo-analysis, 3-hourly, hybrid levels, ARL format"


def met_paths(regional: bool = True) -> list[Path]:
    directory = MET / "regional" if regional else MET
    return [directory / f"{day:%Y%m%d}_gfs0p25"
            for day in pd.date_range("2019-09-23", "2019-09-26")]


def regional_extract(date: str | None = None, dates: list[str] | None = None,
                     *, bounds: tuple[float, float, float, float] = (75, -20, 130, 20),
                     directory: Path | None = None) -> None:
    """NOAA server-side ARL crop; full vertical and temporal sampling retained."""
    from bs4 import BeautifulSoup
    base = "https://www.ready.noaa.gov"
    west, south, east, north = bounds
    if not (0 <= west < east <= 360 and -90 <= south < north <= 90):
        raise ValueError("bounds must be west,south,east,north in 0–360 longitude")
    directory = directory or MET / "regional"
    directory.mkdir(parents=True, exist_ok=True)

    def request(route, fields=None):
        data = urllib.parse.urlencode(fields).encode() if fields else None
        with urllib.request.urlopen(base + route, data=data, timeout=60) as r:
            return r.read().decode()

    paths = [directory / f"{pd.Timestamp(d):%Y%m%d}_gfs0p25" for d in dates] if dates else [
        directory / p.name for p in met_paths()]
    for path in paths:
        if date is not None and not path.name.startswith(date): continue
        record_path = path.with_name(path.name + ".json")
        if path.exists() and record_path.exists():
            if json.loads(record_path.read_text())["requested_bounds"] != list(bounds):
                raise ValueError(f"Existing extraction uses different bounds: {path}")
            continue
        job_file = directory / f"{path.name}.job.json"
        if job_file.exists():
            job = json.loads(job_file.read_text())
        else:
            html = request("/ready2-bin/extract/extract1a.pl", dict(
                metdata="GFS0P25", metdatasm="gfs0p25", xtype=1, metfile=path.name))
            form = BeautifulSoup(html, "html.parser").find("form", attrs={"name": "coordsform"})
            if form is None: raise ValueError("NOAA area-selection form missing")
            fields = {i["name"]: i.get("value", "") for i in form.find_all("input") if i.get("name")}
            fields.update(latL=south, lonL=west, latR=north, lonR=east)
            # The confirmation form is part of the provider's extraction workflow.
            confirmation = request(form["action"] + "?" + urllib.parse.urlencode(fields))
            confirmed = BeautifulSoup(confirmation, "html.parser").find("form")
            if confirmed is None: raise ValueError("NOAA extraction confirmation missing")
            fields = {i["name"]: i.get("value", "") for i in confirmed.find_all("input") if i.get("name")}
            submitted = request(confirmed["action"], fields)
            match = re.search(r"results\.pl\?proc=(\d+)", submitted)
            if not match: raise ValueError("NOAA extraction did not return a job")
            job = dict(proc=match[1], selections=fields, source_archive=path.name)
            job_file.write_text(json.dumps(job, indent=2) + "\n")
        for attempt in range(60):
            html = request("/ready2-bin/extract/results.pl?proc=" + job["proc"])
            (directory / f"{path.name}.result.html").write_text(html)
            soup = BeautifulSoup(html, "html.parser")
            links = [urllib.parse.urljoin(base, a["href"]) for a in soup.find_all("a", href=True)
                     if "/extractout/" in a["href"] and a["href"].endswith(".zip")]
            if links:
                print(f"NOAA extraction ready for {path.name}: {links}", flush=True)
                break
            print(f"NOAA regional extraction pending: {path.name}", flush=True)
            time.sleep(30)
        else: raise TimeoutError("NOAA extraction still pending; rerun to resume")
        if len(links) != 1: raise ValueError(f"Ambiguous extracted data links: {links}")
        url = links[0]
        archive_path = path.with_suffix(".zip")
        model.download_file(url, archive_path)
        with zipfile.ZipFile(archive_path) as archive:
            members = [i for i in archive.infolist() if not i.is_dir() and i.file_size > 1000000]
            if len(members) != 1: raise ValueError("Unexpected NOAA extracted archive contents")
            with archive.open(members[0]) as source, path.open("wb") as destination:
                import shutil
                shutil.copyfileobj(source, destination)
        record = dict(dataset=LABEL, provider="NOAA ARL READY regional extraction",
                      source_url=url, source_archive=path.name,
                      extraction=job, requested_bounds=list(bounds),
                      archive_sha256=model.sha256_file(archive_path),
                      archive_member=members[0].filename, archive_crc32=members[0].CRC,
                      filename=path.name, bytes=path.stat().st_size,
                      sha256=model.sha256_file(path),
                      retrieved_at_utc=datetime.now(timezone.utc).isoformat())
        record_path.write_text(json.dumps(record, indent=2) + "\n")
        print(f"Acquired regional {path.name}", flush=True)


def fetch() -> None:
    MET.mkdir(parents=True, exist_ok=True)
    checksum_url = f"{BASE}/listing.md5.txt"
    with urllib.request.urlopen(checksum_url, timeout=60) as response:
        checksum_text = response.read().decode()
    # Preserve the controlling provider listing, not just locally computed hashes.
    (MET / "listing.md5.txt").write_text(checksum_text)
    records = []
    for path in met_paths(regional=False):
        url = f"{BASE}/2019/09/{path.name}"
        expected = model.remote_size(url)
        matching = [line for line in checksum_text.splitlines() if line.rstrip().endswith(path.name)]
        if len(matching) != 1:
            raise ValueError(f"Expected one NOAA checksum for {path.name}: {len(matching)}")
        remote_md5 = matching[0].split()[0]
        if (not path.exists() or path.stat().st_size != expected
                or path.with_name(path.name + ".aria2").exists()):
            model.download_file(url, path)
        md5, sha = hashlib.md5(), hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(16 * 1024**2), b""):
                md5.update(block)
                sha.update(block)
        if path.stat().st_size != expected or md5.hexdigest() != remote_md5:
            raise ValueError(f"NOAA checksum or size mismatch: {path.name}")
        record = dict(dataset=LABEL, provider="NOAA ARL", source_url=url,
                      filename=path.name, bytes=expected, md5=md5.hexdigest(),
                      sha256=sha.hexdigest(), checksum_source=checksum_url,
                      retrieved_at_utc=datetime.now(timezone.utc).isoformat())
        records.append(record)
        (MET / f"{path.name}.json").write_text(json.dumps(record, indent=2) + "\n")
        print(f"Verified {path.name}: {expected:,} bytes and NOAA MD5", flush=True)
    (MET / "provenance.json").write_text(json.dumps(records, indent=2) + "\n")


def run(home: Path, short: bool = False, jobs: int = 3, member: str | None = None) -> None:
    for path in met_paths():
        record = json.loads(path.with_name(path.name + ".json").read_text())
        if path.stat().st_size != record["bytes"]:
            raise ValueError(f"Meteorology size changed: {path.name}")
        if model.sha256_file(path) != record["sha256"]:
            raise ValueError(f"Meteorology checksum changed: {path.name}")
        audit_arl(path)
    config = model.FootprintConfig(meteorology_label=LABEL, particles=10000,
                                  grid_spacing_deg=.1, particle_diagnostic_variables=0)
    specs = {"n10000_s0": config,
             "n10000_sm10": replace(config, seed=-10),
             "n10000_sm20": replace(config, seed=-20),
             "n10000_height60": replace(config, receptor_height_m_agl=60)}
    if short:
        specs = {"short_test": replace(config, particles=500, hours_back=6)}
    if member: specs = {member:specs[member]}

    def one(item: tuple) -> Path:
        import fcntl
        name, cfg = item
        directory = RUNS / name / f"bkt_{RECEPTOR:%Y%m%dT%H%MZ}"
        directory.parent.mkdir(parents=True,exist_ok=True)
        with (directory.parent/".run.lock").open("a") as lock:
            fcntl.flock(lock.fileno(),fcntl.LOCK_EX)
            if (directory / "run_metadata.json").exists():
                print(f"Already complete: {name}", flush=True)
                return directory
            return model.run_footprint(RECEPTOR, MET, RUNS / name, home, cfg, False,
                                       meteorology_paths=met_paths())

    with ThreadPoolExecutor(max_workers=jobs) as pool:
        list(pool.map(one, specs.items()))


def audit_arl(path: Path) -> dict:
    """Validate regional ARL records, 56 levels, variables, dates and 3-hour coverage."""
    nx, ny, records_per_time = 221, 161, 349
    record_size = nx*ny + 50
    if path.stat().st_size != record_size*records_per_time*8:
        raise ValueError(f"Unexpected regional ARL size: {path.name}")
    expected_date = pd.Timestamp(path.name[:8])
    timestamps, groups = [], []
    with path.open("rb") as stream:
        for t in range(8):
            variables = []
            for r in range(records_per_time):
                stream.seek((t*records_per_time+r)*record_size)
                header = stream.read(50).decode("ascii")
                if r == 0:
                    index=stream.read(108).decode("ascii")
                    grid=[float(index[9+i*7:16+i*7]) for i in range(12)]
                    dimensions=[int(index[93+i*3:96+i*3]) for i in range(3)]
                    if (index[:4]!="GFSQ" or dimensions!=[nx,ny,56] or
                            grid[:4]!=[20.,130.,.25,.25] or grid[9:11]!=[-20.,75.] or
                            int(index[102:104])!=4):
                        raise ValueError("GFS regional coordinates or vertical system differ from request")
                stamp = pd.Timestamp(year=2000+int(header[:2]), month=int(header[2:4]),
                                     day=int(header[4:6]), hour=int(header[6:8]))
                if stamp != expected_date+pd.Timedelta(hours=t*3):
                    raise ValueError(f"Unexpected ARL time: {stamp}")
                variables.append(header[14:18])
            if variables[0] != "INDX" or any(variables.count(v) != 55 for v in
                    ("TEMP", "UWND", "VWND", "WWND", "RELH", "PRES")):
                raise ValueError("Incomplete GFS vertical records")
            if not {"PRSS", "PBLH", "SHGT", "U10M", "V10M", "T02M", "SHTF"}.issubset(variables):
                raise ValueError("Missing GFS surface mixing variables")
            timestamps.append(stamp.isoformat())
            groups.append(len(variables))
    record = dict(status="passed", times_utc=timestamps, nx=nx, ny=ny,
                  atmospheric_levels=55, records_per_time=groups,
                  grid_spacing_deg=.25, bounds=[75,-20,130,20])
    path.with_name(path.name + ".audit.json").write_text(json.dumps(record, indent=2)+"\n")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["fetch", "regional", "test", "run"])
    parser.add_argument("--hysplit-home", type=Path)
    parser.add_argument("--jobs", type=int, default=3, choices=[1, 2, 3, 4])
    parser.add_argument("--date", choices=["20190923", "20190924", "20190925", "20190926"])
    parser.add_argument("--member", choices=["n10000_s0","n10000_sm10","n10000_sm20","n10000_height60"])
    args = parser.parse_args()
    if args.stage == "fetch":
        fetch()
    elif args.stage == "regional":
        regional_extract(args.date)
    else:
        run(model.resolve_hysplit_home(args.hysplit_home), args.stage == "test", args.jobs, args.member)
