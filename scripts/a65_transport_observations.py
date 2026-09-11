"""Acquire and parse bounded IGRA evidence for the general transport benchmark."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import subprocess
import zipfile

import numpy as np
import pandas as pd

from a37_bkt_footprint import ROOT, sha256_file

DATA = ROOT/"data/hysplit/benchmark_observations"
TABLES = ROOT/"outputs/hysplit/benchmark/tables"
BASE = "https://www.ncei.noaa.gov/pub/data/igra/"
STATIONS = ("IDM00096163","IDM00096109")
START = pd.Timestamp("2019-09-09")
END = pd.Timestamp("2019-10-07")
RESOURCES = {
    "igra2-station-list.txt":"igra2-station-list.txt",
    "igra2-data-format.txt":"data/igra2-data-format.txt",
    "igra2-readme.txt":"igra2-readme.txt",
    "igra2-metadata.txt":"history/igra2-metadata.txt",
    "igra2-metadata-readme.txt":"history/igra2-metadata-readme.txt",
    **{s+"-data.txt.zip":"data/data-por/"+s+"-data.txt.zip" for s in STATIONS},
}


def acquire_one(item: tuple[str,str]) -> None:
    name, route = item
    target = DATA/name
    receipt = target.with_name(name+".json")
    if target.exists():
        if not receipt.exists() or json.loads(receipt.read_text())["sha256"] != sha256_file(target):
            raise ValueError(f"Existing observation source lacks matching provenance: {target}")
        return
    part = target.with_name(name+".part")
    subprocess.run(["curl","-fL","--retry","2","--connect-timeout","20",
        "--max-time","1800","--continue-at","-","--max-filesize",str(128*1024**2),
        "-o",str(part),BASE+route],check=True)
    if name.endswith(".zip"):
        with zipfile.ZipFile(part) as archive:
            if archive.testzip() is not None:
                raise ValueError("IGRA archive CRC check failed")
    part.rename(target)
    receipt.write_text(json.dumps(dict(source_url=BASE+route,sha256=sha256_file(target),
        bytes=target.stat().st_size,retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
        provider="NOAA NCEI",dataset="IGRA 2.2"),indent=2)+"\n")


def parse_value(raw: str, scale: float=1.) -> float:
    value = int(raw)
    return float("nan") if value in (-9999,-8888) else value*scale


def parse_level(line: str) -> dict:
    result = dict(level_type=int(line[0]),surface=line[1]=="1",
        pressure_hpa=parse_value(line[9:15],.01),pressure_flag=line[15],
        geopotential_m_msl=parse_value(line[16:21]),height_flag=line[21],
        temperature_c=parse_value(line[22:27],.1),temperature_flag=line[27],
        rh_percent=parse_value(line[28:33],.1),
        wind_direction_deg=parse_value(line[40:45]),wind_speed_ms=parse_value(line[46:51],.1))
    for name,a,b in (('temperature',22,27),('wind_direction',40,45),('wind_speed',46,51)):
        value=int(line[a:b])
        result[name+'_status']='qc_removed' if value==-8888 else 'source_missing' if value==-9999 else 'retained'
    direction,speed = result["wind_direction_deg"],result["wind_speed_ms"]
    # Meteorological direction is where wind comes from, clockwise from north.
    valid = np.isfinite(direction) and 0 <= direction <= 360 and np.isfinite(speed) and speed >= 0
    result["u_ms"] = -speed*np.sin(np.deg2rad(direction)) if valid else np.nan
    result["v_ms"] = -speed*np.cos(np.deg2rad(direction)) if valid else np.nan
    return result


def parse() -> None:
    rows, headers = [], []
    for station in STATIONS:
        source = DATA/(station+"-data.txt.zip")
        with zipfile.ZipFile(source) as archive:
            names = archive.namelist()
            if names != [station+"-data.txt"]:
                raise ValueError("Unexpected IGRA archive member")
            with io.TextIOWrapper(archive.open(names[0]),encoding="ascii") as stream:
                for line in stream:
                    if not line.startswith("#"):
                        raise ValueError("Expected IGRA sounding header")
                    year,month,day,hour = [int(line[a:b]) for a,b in ((13,17),(18,20),(21,23),(24,26))]
                    count = int(line[32:36])
                    date = pd.Timestamp(year=year,month=month,day=day)
                    selected = START <= date < END
                    keep = selected and hour != 99
                    meta = dict(station=station,date_utc=str(date.date()),nominal_hour=hour,
                        release_hhmm=line[27:31],latitude=int(line[55:62])/1e4,
                        longitude=int(line[63:71])/1e4,p_source=line[37:45].strip(),
                        np_source=line[46:54].strip(),n_reported_levels=count,
                        time_utc=(date+pd.Timedelta(hours=hour)).isoformat()+"Z" if keep else "",
                        usable_nominal_time=keep)
                    if selected: headers.append(meta)
                    for _ in range(count):
                        datum = next(stream)
                        if keep:
                            rows.append({**meta,**parse_level(datum)})
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise ValueError("No soundings found within benchmark interval")
    TABLES.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(headers).to_csv(TABLES/"igra_soundings.csv",index=False)
    frame.to_csv(TABLES/"igra_levels.csv",index=False)
    quality=[]
    for station,group in frame.groupby('station'):
        for variable in ('temperature','wind_direction','wind_speed'):
            counts=group[variable+'_status'].value_counts()
            for status in ('retained','source_missing','qc_removed'):
                count=int(counts.get(status,0))
                quality.append(dict(station=station,variable=variable,status=status,
                    n=count,denominator=len(group),percent=100*count/len(group)))
    pd.DataFrame(quality).to_csv(TABLES/'igra_quality_counts.csv',index=False)
    hist = [line for line in (DATA/"igra2-metadata.txt").read_text().splitlines() if line[:11] in STATIONS]
    pd.DataFrame([dict(station=l[:11],year=l[84:88],event=l[100:119].strip(),
        latitude=l[51:60].strip(),longitude=l[63:72].strip(),elevation=l[75:81].strip(),
        reference=l[210:235].strip(),raw_record=l) for l in hist]).to_csv(TABLES/"igra_station_history.csv",index=False)
    summary = []
    for station, group in frame.groupby("station"):
        standard = group[group.level_type==1]
        summary.append(dict(station=station,n_soundings=group.time_utc.nunique(),
            n_levels=len(group),n_standard_levels=len(standard),
            n_standard_valid_winds=int(standard.u_ms.notna().sum()),
            first_utc=group.time_utc.min(),last_utc=group.time_utc.max(),
            location_note="IGRA coordinates are latest station location, not reconstructed historical launch positions",
            independence_note="Observational comparison; assimilation by GFS has not been excluded"))
    pd.DataFrame(summary).to_csv(TABLES/"igra_coverage.csv",index=False)
    print(pd.DataFrame(summary).to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage",choices=["fetch","parse"])
    args = parser.parse_args()
    if args.stage == "fetch":
        DATA.mkdir(parents=True,exist_ok=True)
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(acquire_one,RESOURCES.items()))
    else:
        parse()
