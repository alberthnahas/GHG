"""Acquire published methane background and natural-source fields with provenance."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pandas as pd
import subprocess
import xarray as xr
import a37_bkt_footprint as model
from a42_bkt_sources import provenance

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/bkt_sources/inversion"
CTBASE="https://gml.noaa.gov/aftp/products/carbontracker/ch4/CT-CH4-2025/molefractions"
WETURL="https://gmao.gsfc.nasa.gov/media/gmaoftp/lott/CH4/wetlands/NASA_GSFC.ch4_wetlands.v22.x720_y360.t12.2019.nc"
HEMCO="https://geos-chem.s3.amazonaws.com/HEMCO/CH4"
AUXILIARY={
    "wetlands":"v2025-09/LPJ_MERRA2/LPJ_MERRA2_2019_0.5x0.5.nc",
    "soil":"v2019-10/MeMo_SoilAbs/MeMo_CH4uptake_Climatology.nc",
    "termites":"v2026-02/CAMS_Termites/CAMS-GLOB-TERM_v1.1_methane_2000.nc",
    "geological":"v2020-04/Seeps/Etiope_CH4GeologicalEmis_ScaledToHmiel.1x1.nc",
}

def fetch(url,folder):
    path=DATA/folder/url.rsplit("/",1)[1]
    path.parent.mkdir(parents=True,exist_ok=True)
    if not (path.exists() and path.with_suffix(path.suffix+".json").exists()):
        if "gmao.gsfc.nasa.gov" in url:
            # NASA endpoint returns the full response even for a nonzero Range.
            # Use a fresh bounded transfer, then validate before replacing our partial download.
            temporary=path.with_suffix(".full-download")
            subprocess.run(["curl","--fail","--location","--retry","3","--max-time","600","--output",str(temporary),url],check=True)
            with xr.open_dataset(temporary) as ds:
                if not ds.data_vars: raise ValueError("Empty NASA dataset")
            temporary.replace(path)
            partial=path.with_name(path.name+".aria2")
            if partial.exists(): partial.rename(path.with_name(path.name+".abandoned-aria2"))
        else: model.download_file(url,path)
        provenance(path,url)
    return path

def main(stage):
    if stage=="auxiliary":
        for folder,relative in AUXILIARY.items():
            print(fetch(HEMCO+"/"+relative,folder),flush=True)
    elif stage=="test":
        print(fetch(WETURL,"wetlands"),flush=True)
        print(fetch(CTBASE+"/2019/09/CTCH4_2025.molefrac_glb3x2_2019-09-04.nc","carbontracker"),flush=True)
    else:
        # Daily files also cover the receptor dates for a boundary-only baseline.
        dates=pd.date_range("2019-09-02","2019-10-06")
        urls=[CTBASE+f"/{d:%Y/%m}/CTCH4_2025.molefrac_glb3x2_{d:%Y-%m-%d}.nc" for d in dates]
        with ThreadPoolExecutor(max_workers=2) as pool:
            for path in pool.map(lambda u:fetch(u,"carbontracker"),urls):print(path.name,flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage",choices=["test","all","auxiliary"])
    main(p.parse_args().stage)
