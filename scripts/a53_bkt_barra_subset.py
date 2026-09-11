"""Acquire small native BARRA subsets through public NCI server-side selection."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

import netCDF4
import numpy as np
import requests

from a52_bkt_barra_audit import ROOT, objects


def fetch(variable: str, frequency: str, start: str, end: str,
          bounds: tuple[float,float,float,float]) -> Path:
    """Download one variable with native grid and time sampling, without resampling."""
    month=start[:7].replace("-","")
    if end[:7]!=start[:7]: raise ValueError("Split requests at month boundaries")
    tag=start.replace(":","").replace("-","")+"_"+end.replace(":","").replace("-","")
    directory=ROOT/"data/hysplit/barra_r2/subsets"/tag
    directory.mkdir(parents=True,exist_ok=True)
    destination=directory/f"{variable}.nc"
    record=destination.with_suffix(".json")
    request_identity={"variable":variable,"frequency":frequency,"start":start,"end":end,"bounds":list(bounds)}
    if destination.exists() and record.exists():
        prior=json.loads(record.read_text())
        if prior["request"]!=request_identity: raise ValueError("Existing subset has different request")
        if hashlib.sha256(destination.read_bytes()).hexdigest()!=prior["sha256"]:
            raise ValueError("Existing subset checksum differs")
        return destination
    candidates=objects(variable,frequency,month)
    if not candidates: raise ValueError(f"No object: {variable} {frequency} {month}")
    selected=sorted(candidates,key=lambda row:row["key"])[-1]
    url="https://thredds.nci.org.au/thredds/ncss/grid/ob53/"+selected["key"]
    west,east,south,north=bounds
    params={"var":variable,"west":west,"east":east,"south":south,"north":north,
            "horizStride":1,"accept":"netcdf4"}
    if frequency!="fx": params.update(time_start=start,time_end=end,timeStride=1)
    started=time.monotonic()
    with requests.get(url,params=params,timeout=(20,120),stream=True) as response:
        response.raise_for_status()
        temporary=destination.with_suffix(".part")
        size=0
        with temporary.open("wb") as output:
            for chunk in response.iter_content(1024*1024):
                size+=len(chunk)
                if size>256*1024*1024: raise RuntimeError("Single-variable subset exceeded 256 MiB bound")
                output.write(chunk)
        with netCDF4.Dataset(temporary) as ds:
            if variable not in ds.variables: raise ValueError("Returned subset missing requested field")
            if not np.all(np.diff(ds["lat"][:])>0) or not np.all(np.diff(ds["lon"][:])>0):
                raise ValueError("Unexpected coordinate orientation")
            if "time" in ds.variables:
                times=ds["time"]
                decoded=netCDF4.num2date(times[:],times.units,times.calendar)
                coverage=[str(decoded[0]),str(decoded[-1])]
            else: coverage=[]
        temporary.replace(destination)
        receipt={"request":request_identity,"selected":selected,"subset_url":response.url,
            "retrieved_utc":datetime.now(timezone.utc).isoformat(),"elapsed_seconds":time.monotonic()-started,
            "bytes":size,"sha256":hashlib.sha256(destination.read_bytes()).hexdigest(),"coverage":coverage}
        record.write_text(json.dumps(receipt,indent=2)+"\n")
        print(json.dumps({"variable":variable,"bytes":size,"seconds":receipt["elapsed_seconds"],
                          "coverage":coverage}),flush=True)
        return destination


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("variables",nargs="+")
    p.add_argument("--start",default="2019-09-09T00:00:00Z")
    p.add_argument("--end",default="2019-09-09T12:00:00Z")
    p.add_argument("--bounds",type=float,nargs=4,default=[95,105,-5,5],metavar=("WEST","EAST","SOUTH","NORTH"))
    p.add_argument("--frequency",choices=["1hr","3hr","fx"],default="1hr")
    a=p.parse_args()
    for variable in a.variables: fetch(variable,a.frequency,a.start,a.end,tuple(a.bounds))
