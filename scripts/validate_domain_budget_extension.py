#!/usr/bin/env python3
"""Independently validate domain-extension accounting, provenance and reporting."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import re
import numpy as np
import pandas as pd
import xarray as xr
from a39_bkt_refinement import actual_particles
from a71_domain_budget_extension import FULL_DATES, INPUTS, OUT, RECEIPTS, TABLES, WIDE_BOUNDS, completed_run, sha256
from a73_domain_budget_report import build_domain_sections


def validate() -> dict[str,object]:
    checks=[]
    def require(condition: bool, label: str) -> None:
        if not condition: raise ValueError(label)
        checks.append({"check":label,"status":"passed"})
    full=pd.read_csv(TABLES/"full_receptor_budget.csv",parse_dates=["time_utc","date_utc"])
    require(len(full)==52 and not full.time_utc.duplicated().any(),"All 52 unique receptors are summarized")
    contract=pd.read_csv(TABLES/"design_contract.csv",dtype=str).set_index("parameter").value
    require(contract["full_ensemble_receptors"]=="52" and
            contract["original_retention_threshold"]=="0.95" and
            contract["wide_meteorology_west"]=="50.0" and contract["wide_meteorology_south"]=="-40.0" and
            contract["wide_meteorology_east"]=="160.0" and contract["wide_meteorology_north"]=="30.0" and
            contract["convergence_backward_durations"]=="72,120,168" and
            contract["representative_receptors"]=="5",
            "Reported design numbers reconcile with the generated design contract")
    require(full[["narrow_sensitivity","wide_sensitivity"]].ge(0).all().all() and
            np.isfinite(full.select_dtypes("number")).all().all(),"Full-ensemble numerical fields are finite and nonnegative where required")
    require((full.narrow_active_particles<=full.narrow_emitted_particles).all() and
            (full.wide_active_particles<=full.wide_emitted_particles).all(),"Active particles do not exceed emitted particles")
    require(np.allclose(full.narrow_retention_fraction,full.narrow_active_particles/full.narrow_emitted_particles) and
            np.allclose(full.wide_retention_fraction,full.wide_active_particles/full.wide_emitted_particles),"Retention fractions reconcile with particle ledgers")
    decomp=pd.read_csv(TABLES/"full_domain_decomposition.csv").set_index("metric")
    retained=full.original_retained.astype(bool)
    for metric,row in decomp.iterrows():
        same=math.fsum((full.loc[retained,f"wide_{metric}"]-full.loc[retained,f"narrow_{metric}"]).tolist())/retained.sum()
        recovered=full[f"wide_{metric}"].mean()-full.loc[retained,f"wide_{metric}"].mean()
        total=full[f"wide_{metric}"].mean()-full.loc[retained,f"narrow_{metric}"].mean()
        require(math.isclose(same,row.same_hour_change,rel_tol=1e-12,abs_tol=1e-12) and
                math.isclose(recovered,row.recovered_hour_composition_change,rel_tol=1e-12,abs_tol=1e-12) and
                math.isclose(total,row.total_change,rel_tol=1e-12,abs_tol=1e-12) and
                math.isclose(same+recovered,total,rel_tol=1e-12,abs_tol=1e-12),f"Independent decomposition arithmetic: {metric}")
    observed=pd.read_csv(TABLES/"observed_sample_difference.csv").set_index("species")
    for gas,row in observed.iterrows():
        difference=full.loc[~retained,gas].mean()-full.loc[retained,gas].mean()
        require(math.isclose(difference,row.recovered_minus_retained,rel_tol=1e-12,abs_tol=1e-12),f"Independent observed-group arithmetic: {gas}")
    convergence=pd.read_csv(TABLES/"convergence_matrix.csv",parse_dates=["time_utc"])
    require(len(convergence)==30 and not convergence.duplicated(["time_utc","domain","hours_back"]).any(),"Complete 5 by 2 by 3 convergence matrix")
    require(np.allclose(convergence.total_prior_ppb,convergence.net_surface_ppb+convergence.background_ppb),"Surface plus endpoint background closes the prior budget")
    require(set(convergence.hours_back)=={72,120,168} and set(convergence.domain)=={"original","wide"},"Frozen durations and domains only")
    changes=pd.read_csv(TABLES/"convergence_changes.csv")
    require(len(changes)==40 and set(changes.comparison)=={"72_to_120h","120_to_168h"},"All convergence increments are reported")
    for row in full.itertuples():
        stamp=pd.Timestamp(row.time_utc)
        expected_narrow=completed_run("original",120,stamp).resolve()
        expected_wide=completed_run("wide",120,stamp).resolve()
        require(Path(row.narrow_source_run).resolve()==expected_narrow and Path(row.wide_source_run).resolve()==expected_wide and
                sha256(expected_narrow/"footprint.nc")==row.narrow_footprint_sha256 and
                sha256(expected_wide/"footprint.nc")==row.wide_footprint_sha256,
                f"Full-table footprint provenance: {pd.Timestamp(row.time_utc):%Y%m%dT%H%MZ}")
    for row in convergence.itertuples():
        expected=completed_run(row.domain,int(row.hours_back),pd.Timestamp(row.time_utc)).resolve()
        require(Path(row.source_run).resolve()==expected and sha256(expected/"footprint.nc")==row.footprint_sha256,
                f"Convergence-run identity: {row.domain}{int(row.hours_back)}/{pd.Timestamp(row.time_utc):%Y%m%dT%H%MZ}")
    for domain in ("original","wide"):
        for suffix in ("monthly","daily_fire"):
            path=INPUTS/f"{domain}_{suffix}_flux.nc"
            receipt=json.loads((RECEIPTS/f"{domain}_flux.json").read_text())
            key="monthly_sha256" if suffix=="monthly" else "fire_sha256"
            require(path.exists() and sha256(path)==receipt[key],f"Prepared flux checksum: {domain} {suffix}")
            with xr.open_dataset(path) as data:
                require(data.attrs.get("crs")=="EPSG:4326" and all(data[v].attrs.get("units")=="umol m-2 s-1" for v in data.data_vars),
                        f"Prepared flux CRS and units: {domain} {suffix}")
    met_receipt=json.loads((RECEIPTS/"wide_meteorology.json").read_text())
    require(len(met_receipt)==len(FULL_DATES)==33,"All 33 daily wide meteorology files are receipted")
    for row in met_receipt:
        path=Path(row["path"])
        require(path.exists() and path.stat().st_size==row["bytes"] and sha256(path)==row["sha256"] and row["bounds"]==list(WIDE_BOUNDS),
                f"Wide meteorology provenance: {path.name}")
    run_paths=(set(map(Path,full.narrow_source_run))|set(map(Path,full.wide_source_run))|
               set(map(Path,convergence.source_run)))
    for directory in sorted(run_paths):
        meta=json.loads((directory/"run_metadata.json").read_text())
        n=actual_particles((directory/"MESSAGE").read_text())
        with xr.open_dataset(directory/"footprint.nc") as data:
            require(data.footprint_sensitivity.sizes["time"]==meta["configuration"]["hours_back"] and
                    bool(np.isfinite(data.footprint_sensitivity).all()) and float(data.footprint_sensitivity.min())>=0,
                    f"Complete finite footprint: {directory.parent.name}/{directory.name}")
        points=pd.read_csv(directory/"PAR_GIS.txt",skipinitialspace=True);points.columns=points.columns.str.strip()
        raw=points.time.astype(str).str.replace(r"\s+","",regex=True)
        points["endpoint_utc"]=pd.to_datetime(raw,format="%m/%d/%y%H:%M")
        expected=pd.Timestamp(meta["observation"]["time_utc"]).tz_localize(None)-pd.Timedelta(hours=meta["configuration"]["hours_back"])
        terminal=points[points.endpoint_utc.eq(expected)]
        require(len(terminal)==n and terminal.NSORT.nunique()==n,f"Terminal endpoint ledger: {directory.parent.name}/{directory.name}")
    values=build_domain_sections()
    appendix=values["DOMAIN_APPENDIX"]
    require("{{" not in appendix,"Domain appendix has no unresolved evidence tokens")
    require("No gas value selected a rerun, and no inversion was refitted" in appendix,"No-inversion-refit boundary is explicit")
    require(not re.search(r"/run/media/|scripts/|SHA.?256",appendix),"Reader narrative excludes internal implementation details")
    require(all((OUT/"figures"/(name+suffix)).exists() for name in ("domain_ensemble","selection_concentrations","budget_convergence") for suffix in (".png",".pdf","_id.png","_id.pdf")),"Three English and Indonesian raster and vector extension figures exist")
    pd.DataFrame(checks).to_csv(TABLES/"validation_checks.csv",index=False)
    result={"status":"passed","checks":len(checks),"full_receptors":len(full),"convergence_scenarios":len(convergence),
        "scope":"Forward transport and prior-budget sensitivity only; no inversion refit or atmospheric validation."}
    (OUT/"validation.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    return result


if __name__=="__main__": validate()
