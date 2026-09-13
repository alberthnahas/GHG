"""Validate the BARRA audit, not the readiness of BARRA meteorology for transport."""
import hashlib
import json
import netCDF4
import numpy as np
import pandas as pd
from a54_bkt_barra_quality import ROOT, DEFAULT


def validate():
    out=ROOT/"outputs/hysplit/barra/quality"
    quality=pd.read_csv(out/"field_quality.csv").set_index("variable")
    scope=pd.read_csv(out/"scope.csv").iloc[0]
    checks=[]
    def check(condition,label):
        if not condition:raise ValueError(label)
        checks.append({"check":label,"status":"passed"})
    expected={"ps","orog",*(f"{v}{p}" for v in ("ua","va","wa","ta","hus","zg") for p in (850,925)),
              *(f"ta{h}m" for h in (50,100,150,200,250,1500))}
    check(set(quality.index)==expected,"All selected fields present; no partial audit")
    with netCDF4.Dataset(DEFAULT/"ps.nc") as ds:
        ps=np.asarray(ds["ps"][:])/100
        lat=np.asarray(ds["lat"][:]);lon=np.asarray(ds["lon"][:])
    check(ps.shape==(int(scope.time_count),int(scope.lat_count),int(scope.lon_count)),"Scope dimensions match input")
    check(np.isfinite(ps).all(),"Surface pressure complete")
    check(np.allclose(np.diff(lat),scope.grid_spacing_deg) and np.allclose(np.diff(lon),scope.grid_spacing_deg),"Native grid spacing")
    for name in sorted(expected):
        path=DEFAULT/f"{name}.nc"
        receipt=json.loads(path.with_suffix(".json").read_text())
        check(hashlib.sha256(path.read_bytes()).hexdigest()==receipt["sha256"],f"Subset integrity {name}")
        with netCDF4.Dataset(path) as ds:
            field=np.asarray(np.ma.filled(ds[name][:],np.nan),dtype=float)
            if name not in {"ps","orog"} and not name.endswith("m"):
                level=float(ds["pressure"][:])
                for margin in (1,10):
                    eligible=np.flatnonzero((ps-level).ravel()>margin)
                    nmissing=int(np.count_nonzero(~np.isfinite(field.ravel()[eligible])))
                    check(nmissing==quality.loc[name,f"aboveground_missing_margin{margin}hpa"],f"Independent gap count {name}, margin {margin}")
                    check(len(eligible)==quality.loc[name,f"aboveground_n_margin{margin}hpa"],f"Independent denominator {name}, margin {margin}")
                if name.startswith("wa"):check(ds[name].standard_name=="upward_air_velocity" and ds[name].units=="m s-1",f"Vertical velocity convention {name}")
    native=pd.read_csv(out/"native_confirmation.csv")
    check(len(native)==3 and native.confirmed.all(),"Original packed-field confirmation recorded")
    check(native.native_packed_value.eq(native.native_fill_value).all(),"Native values really are fill codes")
    check((native.surface_pressure_hpa-native.pressure_level_hpa>10).all(),"Native examples exceed rounding margin")
    check(quality.loc["wa925","aboveground_missing_margin10hpa"]>0,"Reported conversion stop supported")
    profile=pd.read_csv(out/"bkt_profile.csv")
    check(profile[profile.variable.eq("wa925")].value.isna().all(),"BKT local below-ground level remains missing")
    from a55_bkt_barra_report import build_barra_sections
    section=build_barra_sections()["BARRA_APPENDIX"]
    check("{{" not in section,"All appendix numbers resolved")
    import re
    strip=lambda text:re.sub(r"\b(Figure|Table)s? \d+","\\1 N",text)  # the companion renumbers figures and tables by order
    body=strip(section.split("\n",1)[1])
    check(body in strip((ROOT/"BKT_Transport_Technical_Companion.md").read_text()),"Audited appendix integrated in the transport companion without divergence")
    result={"status":"passed","checks":len(checks),"meteorology_conversion_ready":False,
            "scope":"Audit integrity and numerical consistency only; transport comparison not performed",
            "reason":"Above-surface missing fields require an explicitly validated reconstruction or additional source data"}
    pd.DataFrame(checks).to_csv(out/"validation_checks.csv",index=False)
    (out/"validation.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    return result


if __name__=="__main__":validate()
