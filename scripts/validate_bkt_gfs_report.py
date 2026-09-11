#!/usr/bin/env python3
"""Validate GFS model, source convolution, report provenance and rendered artifact."""
from __future__ import annotations
from decimal import Decimal
import hashlib
import json
import re
import subprocess
import numpy as np
import pandas as pd
import xarray as xr
from PIL import Image
from a43_bkt_source_analysis import OUT, TABLES, ROOT, MW, matching_flux
from a39_bkt_refinement import read_run, MEMBERS, STAMP
from a41_bkt_gfs import met_paths, audit_arl
from a45_bkt_gfs_report import build_report
from bkt_footprint_spatial import regrid_coefficients


def require(condition, label):
    if not condition: raise ValueError(label)


def validate():
    checks=[]
    def check(condition,label):
        require(condition,label);checks.append(dict(check=label,status="passed"))
    for path in met_paths():
        audit_arl(path)
        record=json.loads(path.with_name(path.name+".json").read_text())
        check(hashlib.sha256(path.read_bytes()).hexdigest()==record["sha256"],f"GFS integrity {path.name}")
    fields=[]
    expected_times=pd.date_range("2019-09-23T01:00","2019-09-26T00:00",freq="h")
    for member in (*MEMBERS,"n10000_height60"):
        folder=ROOT/"outputs/hysplit/gfs"/member/STAMP
        field,meta=read_run(folder)
        check(np.array_equal(field.time.values,expected_times.values),f"Complete source-hour coverage {member}")
        check(meta["actual_particles"]==10020,f"Emitted count {member}")
        text=(folder/"MESSAGE").read_text()
        check("GFSQ" in text and "FATAL" not in text.upper(),f"Native GFS completion {member}")
        raw=pd.read_csv(folder/"footprint_aggregate.csv")
        check(np.isclose(raw.sensitivity_sum.sum()*10000/10020,float(field.sum()),rtol=2e-6),f"Native CSV/NetCDF reconciliation {member}")
        if member in MEMBERS: fields.append(field.values)
    with xr.open_dataset(OUT/"GFS_ensemble.nc") as ds: mean=ds.footprint_sensitivity.load()
    check(np.allclose(np.mean(fields,axis=0),mean.values,rtol=1e-12,atol=1e-14),"Corrected three-seed mean")
    check(not np.array_equal(fields[0],fields[1]),"Seeds are distinct")
    display=pd.read_csv(TABLES/"display_integrity.csv").iloc[0]
    check(np.isclose(display.raw_sum,display.display_integral,rtol=1e-10),"Display integral conserved")
    edge=pd.read_csv(TABLES/"output_domain_edge.csv")
    check(len(edge)==10 and edge.edge_share_percent.between(0,100).all(),
          "Output-domain edge influence quantified without claiming complete capture")
    geography=json.loads((OUT/"cartographic_provenance.json").read_text())
    from pathlib import Path
    boundary=geography["indonesia"]
    check(boundary["feature_count"]==38 and hashlib.sha256(Path(boundary["asset"]).read_bytes()).hexdigest()==boundary["sha256"],
          "Established Indonesian boundary asset unchanged")
    check(len(geography["neighbors"])==8,"Detailed neighboring-country provenance retained")
    quality=pd.read_csv(TABLES/"source_quality.csv")
    check(len(quality)==16 and quality.missing_cells.eq(0).all() and quality.negative_cells.eq(0).all(),"Complete nonnegative EDGAR sector coverage")
    fq=pd.read_csv(TABLES/"fire_quality.csv")
    check(len(fq)==3 and fq.missing_cells.eq(0).all() and fq.negative_cells.eq(0).all(),"GFED source coverage and values")
    with xr.open_dataset(OUT/"EDGAR_convolution.nc") as ds: anth=ds.load()
    rows=pd.read_csv(TABLES/"source_contributions.csv")
    gfs=rows[rows.run.str.startswith("GFS_")&~rows.run.str.contains("height")].groupby(["gas","sector"]).enhancement.mean()
    for name in anth.source.values:
        gas,sector=name.split("_",1)
        factor=1 if gas=="CO2" else 1000
        direct=float((mean.sum("time")*anth.surface_flux.sel(source=name)).sum())*factor
        check(np.isclose(direct,gfs.loc[(gas,sector)],rtol=1e-10),f"EDGAR convolution {name}")
        check(np.isclose(float(anth.enhancement.sel(source=name).sum())*factor,direct,rtol=1e-10),f"EDGAR contribution-map sum {name}")
    # Real-data independent regridding order for one inventory sector.
    path=ROOT/"data/bkt_sources/edgar_v8/CH4_AGRICULTURE_2019.nc"
    with xr.open_dataset(path) as ds:
        source=ds.fluxes.sel(time="2019-09-15",lat=slice(-11,11),lon=slice(84,117)).load()
    remapped=regrid_coefficients(mean.sum("time").values,mean.lat.values,mean.lon.values,source.lat.values,source.lon.values)
    independent=float((remapped*source.values*1e9/MW["CH4"]).sum())*1000
    check(np.isclose(independent,gfs.loc[("CH4","AGRICULTURE")],rtol=1e-7),"Real-data adjoint convolution agrees")
    worked=pd.read_csv(TABLES/"worked_convolution.csv",dtype=str)
    for row in worked.itertuples():
        value=Decimal(row.sensitivity)*Decimal(row.flux_umol_m2_s)*Decimal(row.conversion_to_report_unit)
        check(np.isclose(float(value),float(row.reported_contribution),rtol=1e-12),f"Decimal worked product {row.gas}")
    with xr.open_dataset(OUT/"GFED_convolution.nc") as ds: fire=ds.load()
    fr=pd.read_csv(TABLES/"fire_contributions.csv")
    fs=fr[fr.run.str.startswith("GFS_")&~fr.run.str.contains("height")].groupby("gas").enhancement.mean()
    for gas in fire.gas.values:
        direct=float((mean*fire.surface_flux.sel(gas=gas)).sum())*(1 if gas=="CO2" else 1000)
        check(np.isclose(direct,fs.loc[gas],rtol=1e-10),f"Fire convolution {gas}")
        check(np.isclose(float(fire.enhancement.sel(gas=gas).sum())*(1 if gas=="CO2" else 1000),direct,rtol=1e-10),f"Fire map sum {gas}")
    check(anth.enhancement.attrs["units"]=="1e-6" and fire.enhancement.attrs["units"]=="1e-6",
          "NetCDF enhancement uses one consistent unit across gases")
    budget=pd.read_csv(TABLES/"partial_CO_budget.csv")
    for row in budget.itertuples():
        expected_co=fr[fr.run.str.startswith(row.driver+"_")&~fr.run.str.contains("height")&fr.gas.eq("CO")].enhancement.mean()
        check(np.isclose(row.modeled_fire_co_ppb,expected_co,rtol=1e-12) and
              np.isclose(row.remaining_co_ppb,row.observed_co_ppb-expected_co,rtol=1e-12),
              f"Conditional passive-CO budget arithmetic {row.driver}")
    provinces=pd.read_csv(TABLES/"province_coverage.csv")
    check((provinces.assigned_share_percent<=100.001).all() and (provinces.assigned_share_percent>=0).all(),"Provincial accounting bounded")
    check((provinces.ambiguous_boundary_enhancement>=0).all() and
          (provinces.ambiguous_boundary_enhancement<=provinces.outside_or_unassigned+1e-9).all(),
          "Ambiguous boundaries retained within unassigned influence")
    expected,tokens=build_report()
    markdown=(ROOT/"BKT_HYSPLIT_STILT_Footprint_Report.md").read_text()
    check(markdown==expected,"Canonical report matches evidence and narrative template")
    for pattern in (r"revised Figure",r"WIB.to.UTC correction",r"debugg",r"interrupted attempt",r"first implementation",r"scripts/",r"/run/media/",r"SHA.256"):
        check(re.search(pattern,markdown,re.I) is None,f"Scientific narrative excludes {pattern}")
    pdf=ROOT/"outputs/BKT_HYSPLIT_STILT_Footprint_Report.pdf"
    info=subprocess.check_output(["pdfinfo",str(pdf)],text=True)
    pages=int(re.search(r"Pages:\s+(\d+)",info)[1])
    check("A4" in info,"PDF uses A4 pages")
    text=subprocess.check_output(["pdftotext",str(pdf),"-"],text=True)
    layout=subprocess.check_output(["pdftotext","-layout",str(pdf),"-"],text=True)
    results_pages=[page for page in layout.split("\f") if re.search(r"(?m)^\s*4\. Results\s*$",page)]
    check(len(results_pages)==1 and "Regional footprint and dependence on meteorology" in results_pages[0]
          and "The GFS ensemble has integrated sensitivity" in results_pages[0],
          "Results heading stays with its subsection and substantive findings")
    for number in range(1,26):check(f"Figure {number}." in text,f"PDF figure {number}")
    for number in range(1,21):check(f"Table {number}." in text,f"PDF table {number}")
    check("{{" not in text and "[REPORT" not in text,"No unresolved PDF template tokens")
    log=(ROOT/"outputs/latex/BKT_HYSPLIT_STILT_Footprint_Report.log").read_text()
    check(not any(p in log for p in ("Overfull","Undefined control sequence","Missing character","Fatal error")),"Clean scientific PDF typesetting")
    figs=list((OUT/"figures").glob("figure_*.png"))
    check(len(figs)==12,"Twelve reproducible scientific figures")
    from a46_bkt_inversion_transport import OUT as INVERSE_OUT
    inverse_figs=list((INVERSE_OUT/"figures").glob("figure_*.png"))
    check(len(inverse_figs)==10,"Ten reproducible inversion figures")
    figs+=inverse_figs
    from a64_transport_benchmark import OUT as BENCHMARK_OUT
    benchmark_figs=[BENCHMARK_OUT/"figures"/(name+".png") for name in
                   ("domain_completeness","physics_sensitivity","profile_evaluation")]
    check(all(path.exists() for path in benchmark_figs),"Three reproducible general-transport figures")
    figs+=benchmark_figs
    for path in figs:
        with Image.open(path) as im:check(im.width>=2100 and im.height>=1100,f"Publication raster size {path.stem}")
        check(path.with_suffix(".pdf").is_file(),f"Vector companion {path.stem}")
    from validate_bkt_inversion import validate as validate_inverse
    validate_inverse()
    check(json.loads((INVERSE_OUT/"inversion_validation.json").read_text())["status"]=="passed","Inversion scientific and provenance gates pass")
    from validate_bkt_barra import validate as validate_barra
    check(validate_barra()["status"]=="passed","BARRA feasibility audit is reproducible; not a meteorology-readiness claim")
    from validate_transport_benchmark import validate as validate_transport
    check(validate_transport()["status"]=="passed","General transport benchmark accounting and provenance pass")
    result=dict(status="passed",checks=len(checks),pages=pages,figures=25,tables=20,
                scope="Numerical consistency and artifact QA; not independent atmospheric validation")
    pd.DataFrame(checks).to_csv(TABLES/"validation_checks.csv",index=False)
    (OUT/"validation.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__=="__main__":validate()
