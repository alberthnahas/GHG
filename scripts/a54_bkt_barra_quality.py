"""Audit terrain masking and profile support before any BARRA ARL conversion.

Missing includes both CF masks and nonfinite values: NCI NCSS expands packed
fill values to NaN without retaining a _FillValue attribute. This is not zero.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import netCDF4
import numpy as np
import pandas as pd

from a52_bkt_barra_audit import ROOT

DEFAULT=ROOT/"data/hysplit/barra_r2/subsets/20190909T000000Z_20190909T120000Z"


def values(variable):
    return np.ma.asarray(variable[:],dtype=float).filled(np.nan)


def aboveground_gaps(data, surface_pressure_hpa, level_hpa, margin_hpa=1):
    """Use pressure decreasing with height; retain a positive safety margin."""
    if margin_hpa<0: raise ValueError("Pressure margin must be nonnegative")
    field=np.ma.asarray(data,dtype=float).filled(np.nan)
    pressure=np.ma.asarray(surface_pressure_hpa,dtype=float).filled(np.nan)
    if field.shape!=pressure.shape or not np.isfinite(pressure).all():
        raise ValueError("Missing or unmatched surface pressure")
    above=pressure>level_hpa+margin_hpa
    return above,(~np.isfinite(field))&above


def load(path: Path, name: str):
    with netCDF4.Dataset(path) as ds:
        var=ds[name]
        coords={k:values(ds[k]) for k in ("lat","lon","time","pressure","height") if k in ds.variables}
        dates=[]
        if "time" in ds.variables:
            t=ds["time"]
            dates=[str(v) for v in netCDF4.num2date(t[:],t.units,t.calendar)]
        return values(var),coords,var.units,dates


def audit(directory: Path):
    pressure,coords,units,dates=load(directory/"ps.nc","ps")
    if units!="Pa": raise ValueError("Expected surface pressure in Pa")
    pressure=pressure/100 # explicit Pa to hPa conversion
    if not np.isfinite(pressure).all(): raise ValueError("Missing surface pressure")
    terrain,tc,tu,_=load(directory/"orog.nc","orog")
    if tu!="m": raise ValueError("Expected terrain altitude in m")
    for axis in ("lat","lon"): np.testing.assert_allclose(tc[axis],coords[axis],atol=1e-8,rtol=0)
    iy=int(np.argmin(abs(coords["lat"]+.202)));ix=int(np.argmin(abs(coords["lon"]-100.318)))
    rows=[];examples=[];profiles=[];provenance=[]
    for path in sorted(directory.glob("*.nc")):
        name=path.stem
        receipt=json.loads(path.with_suffix(".json").read_text())
        if hashlib.sha256(path.read_bytes()).hexdigest()!=receipt["sha256"]: raise ValueError(f"Checksum changed: {path}")
        provenance.append({"variable":name,"sha256":receipt["sha256"],"url":receipt["subset_url"],
                           "source_key":receipt["selected"]["key"],"source_etag":receipt["selected"]["etag"]})
        data,vc,unit,vd=load(path,name)
        for axis in ("lat","lon"): np.testing.assert_allclose(vc[axis],coords[axis],atol=1e-8,rtol=0)
        if "time" in vc:
            if vd!=dates: raise ValueError(f"Unmatched times: {name}")
        level=float(vc["pressure"]) if "pressure" in vc else np.nan
        missing=~np.isfinite(data)
        row={"variable":name,"unit":unit,"pressure_hpa":level,"n_values":data.size,
             "missing":int(missing.sum()),"missing_percent":100*missing.mean()}
        if np.isfinite(level):
            for tolerance in (0,1,5,10):
                above,gaps=aboveground_gaps(data,pressure,level,tolerance)
                count=int(gaps.sum())
                row[f"aboveground_n_margin{tolerance}hpa"]=int(above.sum())
                row[f"aboveground_missing_margin{tolerance}hpa"]=count
                row[f"aboveground_missing_percent_margin{tolerance}hpa"]=100*count/above.sum()
            row["max_ps_where_missing_hpa"]=float(pressure[missing].max()) if missing.any() else np.nan
            candidates=np.argwhere(missing & (pressure>level+10))
            if len(candidates):
                t,y,x=max(candidates,key=lambda idx:pressure[tuple(idx)])
                examples.append({"variable":name,"time_utc":dates[t],"time_index":int(t),
                    "latitude":float(coords["lat"][y]),"longitude":float(coords["lon"][x]),
                    "subset_y":int(y),"subset_x":int(x),"pressure_level_hpa":level,
                    "surface_pressure_hpa":float(pressure[t,y,x]),"surface_altitude_m":float(terrain[y,x]),
                    "missing":True})
        rows.append(row)
        if data.ndim==3:
            for it,dt in enumerate(dates):
                profiles.append({"variable":name,"time_utc":dt,"value":data[it,iy,ix],"unit":unit,
                    "pressure_hpa":level,"height_m":float(vc["height"]) if "height" in vc else np.nan,
                    "latitude":float(coords["lat"][iy]),"longitude":float(coords["lon"][ix]),
                    "surface_altitude_m":float(terrain[iy,ix])})
    out=ROOT/"outputs/hysplit/barra/quality"
    out.mkdir(parents=True,exist_ok=True)
    frame=pd.DataFrame(rows)
    frame.to_csv(out/"field_quality.csv",index=False)
    pd.DataFrame(examples).to_csv(out/"aboveground_missing_examples.csv",index=False)
    pd.DataFrame(profiles).to_csv(out/"bkt_profile.csv",index=False)
    pd.DataFrame(provenance).to_csv(out/"subset_provenance.csv",index=False)
    pd.DataFrame([{"start_utc":dates[0],"end_utc":dates[-1],"time_count":len(dates),
        "lat_count":len(coords["lat"]),"lon_count":len(coords["lon"]),
        "west":float(coords["lon"].min()),"east":float(coords["lon"].max()),
        "south":float(coords["lat"].min()),"north":float(coords["lat"].max()),
        "grid_spacing_deg":float(np.median(np.diff(coords["lon"]))),
        "bkt_grid_lat":float(coords["lat"][iy]),"bkt_grid_lon":float(coords["lon"][ix]),
        "bkt_terrain_m":float(terrain[iy,ix]),"bkt_ps_min_hpa":float(pressure[:,iy,ix].min()),
        "bkt_ps_max_hpa":float(pressure[:,iy,ix].max())}]).to_csv(out/"scope.csv",index=False)
    print(frame[["variable","n_values","missing","aboveground_missing_margin1hpa"]].to_string(index=False),flush=True)
    return frame


def verify_native(directory: Path):
    """Independently check native packed DAP values at selected NCSS gaps."""
    out=ROOT/"outputs/hysplit/barra/quality"
    examples=pd.read_csv(out/"aboveground_missing_examples.csv")
    examples=examples[examples.variable.isin(["wa925","ta925","wa850"])]
    rows=[]
    for example in examples.itertuples():
        receipt=json.loads((directory/f"{example.variable}.json").read_text())
        url="https://thredds.nci.org.au/thredds/dodsC/ob53/"+receipt["selected"]["key"]
        with netCDF4.Dataset(url) as ds:
            y=int(np.argmin(abs(ds["lat"][:]-example.latitude)))
            x=int(np.argmin(abs(ds["lon"][:]-example.longitude)))
            stamp=pd.Timestamp(example.time_utc).to_pydatetime()
            t=netCDF4.date2index(stamp,ds["time"],select="exact")
            ds.set_auto_maskandscale(False)
            field=ds[example.variable]
            packed=int(field[t,y,x]);fill=int(field.getncattr("_FillValue"))
            if packed!=fill: raise ValueError("Native object does not confirm subset missing value")
        psreceipt=json.loads((directory/"ps.json").read_text())
        psurl="https://thredds.nci.org.au/thredds/dodsC/ob53/"+psreceipt["selected"]["key"]
        with netCDF4.Dataset(psurl) as ds:
            ds.set_auto_maskandscale(False)
            v=ds["ps"]
            packed_ps=int(v[t,y,x])
            pressure=(packed_ps*v.scale_factor+v.add_offset)/100
            np.testing.assert_allclose(pressure,example.surface_pressure_hpa,atol=1e-8,rtol=0)
        rows.append({"variable":example.variable,"time_utc":example.time_utc,
                     "latitude":example.latitude,"longitude":example.longitude,
                     "native_packed_value":packed,"native_fill_value":fill,
                     "native_ps_packed":packed_ps,"surface_pressure_hpa":pressure,
                     "pressure_level_hpa":example.pressure_level_hpa,"confirmed":True})
        print(f"Native packed-value confirmation: {example.variable}",flush=True)
    pd.DataFrame(rows).to_csv(out/"native_confirmation.csv",index=False)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--directory",type=Path,default=DEFAULT)
    p.add_argument("--verify-native",action="store_true")
    args=p.parse_args()
    if args.verify_native: verify_native(args.directory)
    else: audit(args.directory)
