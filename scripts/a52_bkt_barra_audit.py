"""Bounded anonymous BARRA-R2 archive and NetCDF feasibility audit.

Reads selected native metadata and small server-side samples, never the full archive.
Outputs preserve object identity, metadata and a small BKT profile sample.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import requests
import netCDF4

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://bom-opendata-climate.s3.amazonaws.com"
PREFIX = "BARRA2/output/reanalysis/AUS-11/BOM/ERA5/historical/hres/BARRA-R2/v1/"
NS = {"s": "http://s3.amazonaws.com/doc/2006-03-01/"}


def objects(variable: str, frequency: str, month: str) -> list[dict]:
    """List all versions for one variable/month, with pagination."""
    params = {"list-type": "2", "prefix": f"{PREFIX}{frequency}/{variable}/"}
    result = []
    while True:
        response = requests.get(BASE, params=params, timeout=45)
        response.raise_for_status()
        xml = ET.fromstring(response.content)
        for item in xml.findall("s:Contents", NS):
            key = item.findtext("s:Key", namespaces=NS)
            if key.endswith(f"_{month}-{month}.nc") or frequency == "fx":
                result.append({"key": key, "size_bytes": int(item.findtext("s:Size", namespaces=NS)),
                               "etag": item.findtext("s:ETag", namespaces=NS),
                               "modified": item.findtext("s:LastModified", namespaces=NS)})
        if xml.findtext("s:IsTruncated", namespaces=NS) == "false":
            return result
        params["continuation-token"] = xml.findtext("s:NextContinuationToken", namespaces=NS)


def native(value):
    if isinstance(value, bytes): return value.decode()
    if isinstance(value, np.ndarray): return value.tolist()
    if isinstance(value, np.generic): return value.item()
    return value


def inspect(item: dict, variable: str) -> dict:
    """Use NCI server-side subsetting, avoiding large compressed S3 chunks."""
    url = "https://thredds.nci.org.au/thredds/dodsC/ob53/" + item["key"]
    with netCDF4.Dataset(url) as ds:
        ds.set_auto_maskandscale(False)
        meta={"url":url,"attributes":{k:native(ds.getncattr(k)) for k in ds.ncattrs()},
              "variables":{k:{"dimensions":list(v.dimensions),"shape":list(v.shape),
                  "attrs":{a:native(v.getncattr(a)) for a in v.ncattrs()}} for k,v in ds.variables.items()}}
        lat=np.asarray(ds["lat"][:]);lon=np.asarray(ds["lon"][:])
        iy=int(np.argmin(abs(lat+.202)));ix=int(np.argmin(abs(lon-100.318)))
        meta["grid"]={"lat_min":float(lat.min()),"lat_max":float(lat.max()),
            "lon_min":float(lon.min()),"lon_max":float(lon.max()),
            "bkt_lat":float(lat[iy]),"bkt_lon":float(lon[ix])}
        field=ds[variable]
        selection=tuple(slice(iy-1,iy+2) if d=="lat" else slice(ix-1,ix+2) if d=="lon"
                        else slice(0,1) for d in field.dimensions)
        meta["sample_packed"]=native(np.asarray(field[selection]))
        if "time" in ds.variables:
            meta["time_first_last"]=[float(ds["time"][0]),float(ds["time"][-1])]
        return meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("variable")
    parser.add_argument("--frequency", default="1hr", choices=["1hr","3hr","fx"])
    parser.add_argument("--month",default="201909")
    args=parser.parse_args()
    candidates=objects(args.variable,args.frequency,args.month)
    if not candidates: raise RuntimeError("No public object matches requested variable/month")
    selected=sorted(candidates,key=lambda r:r["key"])[-1]
    result={"retrieved_utc":datetime.now(timezone.utc).isoformat(),"candidates":candidates,
            "selected":selected,"metadata":inspect(selected,args.variable)}
    destination=ROOT/"outputs/hysplit/barra/audit"
    destination.mkdir(parents=True,exist_ok=True)
    path=destination/f"{args.variable}_{args.frequency}_{args.month}.json"
    path.write_text(json.dumps(result,indent=2,default=native)+"\n")
    print(path,flush=True)
    print(json.dumps({"selected":selected,"grid":result["metadata"]["grid"],
        "field":result["metadata"]["variables"][args.variable],
        "sample_packed":result["metadata"]["sample_packed"]},default=native),flush=True)


if __name__=="__main__": main()
