#!/usr/bin/env python3
"""Expand the scientific narrative exclusively from computed evidence tables."""
from __future__ import annotations
import json
import hashlib
import importlib.metadata
from pathlib import Path
import re
import sys
import pandas as pd
from a43_bkt_source_analysis import ROOT, OUT, TABLES
from a40_bkt_refinement_report import markdown_table

LABELS={"AGRICULTURE":"Agriculture","BUILDINGS":"Buildings","FUEL_EXPLOITATION":"Fuel exploitation",
        "IND_COMBUSTION":"Industrial combustion","IND_PROCESSES":"Industrial processes",
        "POWER_INDUSTRY":"Power industry","TRANSPORT":"Transport","WASTE":"Waste"}


def build_report(write=True):
    obs=pd.read_csv(TABLES/"observation_context_summary.csv").set_index("species")
    transport=pd.read_csv(TABLES/"transport_summary.csv").set_index("run")
    comp=pd.read_csv(TABLES/"driver_comparison.csv").iloc[0]
    met=pd.read_csv(TABLES/"meteorological_context.csv")
    seeds=transport[(transport.driver=="GFS")&transport.member.isin(("n10000_s0","n10000_sm10","n10000_sm20"))]
    anth=pd.read_csv(TABLES/"source_contributions.csv")
    fire=pd.read_csv(TABLES/"fire_contributions.csv")
    provinces=pd.read_csv(TABLES/"province_contributions.csv")
    coverage=pd.read_csv(TABLES/"province_coverage.csv").set_index("gas")
    edge=pd.read_csv(TABLES/"output_domain_edge.csv").set_index("run")
    budget=pd.read_csv(TABLES/"partial_CO_budget.csv").set_index("driver")
    daily=pd.read_csv(TABLES/"fire_daily_contribution.csv")
    daily_co2=daily[daily.gas.eq("CO2")]
    display=pd.read_csv(TABLES/"display_integrity.csv").iloc[0]
    selected=anth[anth.run.str.startswith("GFS_")&~anth.run.str.contains("height")]
    sectors=selected.groupby(["gas","sector"]).enhancement.agg(["mean","min","max"])
    totals=selected.groupby(["gas","run"]).enhancement.sum().groupby("gas").agg(["mean","min","max"])
    fire_gfs=fire[fire.run.str.startswith("GFS_")&~fire.run.str.contains("height")]
    fsum=fire_gfs.groupby("gas").enhancement.agg(["mean","min","max"])
    central=transport.loc["GFS"]
    tokens={"FIGURES":"outputs/hysplit/gfs/analysis/figures",
            "GFS_EDGE":f"{edge.loc['GFS','edge_share_percent']:.3f}",
            "GDAS_FIRE_CO":f"{budget.loc['GDAS','modeled_fire_co_ppb']:,.1f}",
            "GFS_CO_REMAINDER":f"{budget.loc['GFS','remaining_co_ppb']:.1f}",
            "GFS_FIRE_CO_PERCENT":f"{budget.loc['GFS','fire_to_observed_co_percent']:.1f}",
            "FIRE_FIRST_DAY_SHARE":f"{100*daily_co2.loc[daily_co2.day.eq('23 Sep'),'enhancement'].sum()/daily_co2.enhancement.sum():.1f}",
            "OBS_CO2":f"{obs.loc['CO₂','receptor_value']:.2f}",
            "OBS_CH4":f"{obs.loc['CH₄','receptor_value']:,.2f}",
            "OBS_CO":f"{obs.loc['CO','receptor_value']:.2f}",
            "VALID_HOURS":str(int(obs.valid_hours.iloc[0])),"EXPECTED_HOURS":str(int(obs.expected_hours.iloc[0])),
            "GFS_SE":f"{central.se_beyond25_share_percent:.1f}",
            "GFS_NEAR":f"{central.within25_share_percent:.1f}",
            "GFS_DISTANCE":f"{central.median_distance_km:.0f}",
            "GFS_LAG":f"{central.median_lag_hours:.0f}",
            "GFS_P90LAG":f"{central.p90_lag_hours:.0f}",
            "GFS_TOTAL":f"{central.sensitivity_sum:.3f}",
            "GDAS_TOTAL":f"{transport.loc['GDAS','sensitivity_sum']:.3f}",
            "GFS_WITHIN250":f"{central.within250_share_percent:.1f}",
            "GFS_SE_MIN":f"{seeds.se_beyond25_share_percent.min():.1f}",
            "GFS_SE_MAX":f"{seeds.se_beyond25_share_percent.max():.1f}",
            "GFS_TOTAL_MIN":f"{seeds.sensitivity_sum.min():.3f}",
            "GFS_TOTAL_MAX":f"{seeds.sensitivity_sum.max():.3f}",
            "TOTAL_CHANGE":f"{comp.total_change_percent:+.1f}",
            "SHAPE_TV":f"{comp.shape_tv_1deg_percent:.1f}",
            "PARTICLES":f"{int(seeds.actual_particles.iloc[0]):,}",
            "GFS_TERRAIN":f"{met.loc[met.driver.eq('GFS'),'SHGT'].median():.0f}",
            "GDAS_TERRAIN":f"{met.loc[met.driver.eq('GDAS'),'SHGT'].median():.0f}",
            "HEIGHT_CHANGE":f"{100*(transport.loc['GFS_n10000_height60','sensitivity_sum']/transport.loc['GFS_n10000_s0','sensitivity_sum']-1):+.1f}",
            "SIGMA":f"{comp.gaussian_sigma_cells:g}",
            "HIDDEN":f"{display.below_color_scale_percent:.3f}",
            "OUTSIDE":f"{display.outside_frame_percent:.3f}"}
    for gas in ("CO2","CH4"):
        tokens[f"ANTH_{gas}"]=f"{totals.loc[gas,'mean']:.3f}"
        tokens[f"TOP_{gas}"]=LABELS[sectors.loc[gas,'mean'].idxmax()].lower()
        tokens[f"TOP_SHARE_{gas}"]=f"{100*sectors.loc[gas,'mean'].max()/totals.loc[gas,'mean']:.1f}"
        tokens[f"PROV_{gas}"]=str(provinces[provinces.gas.eq(gas)].nlargest(1,"enhancement").province.iloc[0]).title()
        tokens[f"AMBIGUOUS_{gas}"]=f"{coverage.loc[gas,'ambiguous_boundary_share_percent']:.3f}"
        by_run=anth[anth.gas.eq(gas)].groupby("run").enhancement.sum()
        gdas=by_run[by_run.index.str.startswith("GDAS_")&~by_run.index.str.contains("height")].mean()
        tokens[f"ANTH_GDAS_{gas}"]=f"{gdas:.3f}"
        tokens[f"ANTH_DRIVER_{gas}"]=f"{100*(totals.loc[gas,'mean']/gdas-1):+.1f}"
        tokens[f"ANTH_HEIGHT_{gas}"]=f"{100*(by_run.loc['GFS_n10000_height60']/by_run.loc['GFS_n10000_s0']-1):+.1f}"
    for gas in ("CO2","CH4","CO"):
        tokens[f"FIRE_{gas}"]=f"{fsum.loc[gas,'mean']:.3f}"
    modeled_co=float(fsum.loc["CO","mean"])
    observed_co=float(obs.loc["CO","receptor_value"])
    tokens["CO_BUDGET_NOTICE"]=(
        "The fire-only CO estimate exceeds the total observed CO. Under passive transport and a "
        "nonnegative background, this is a material model–observation incompatibility and prevents "
        "a consistent concentration budget with this configuration."
        if modeled_co>observed_co else
        f"The GDAS fire-only CO estimate ({budget.loc['GDAS','modeled_fire_co_ppb']:,.1f} ppb) exceeds the observed total, "
        f"whereas GFS fire CO consumes {budget.loc['GFS','fire_to_observed_co_percent']:.1f}% of that total. "
        "This budget constraint exposes strong scenario dependence; it does not validate the GFS fire estimate.")
    tokens["CO_COMPATIBILITY"]=(
        f"The modeled fire-only CO increment ({modeled_co:.1f} ppb) exceeds the total observed CO "
        f"({observed_co:.2f} ppb). Under the assumed passive transport and a nonnegative background, "
        "these cannot form a consistent concentration budget. This is a material model–observation "
        "incompatibility, not evidence that fires supplied more than all observed CO. Emission "
        "magnitude, source injection height, transport, timing and neglected chemical loss require "
        "independent evaluation before quantitative fire attribution."
        if modeled_co>observed_co else
        "The fire-only CO increment is smaller than total observed CO. This necessary magnitude "
        "check does not validate the fire contribution: unmodeled background and other combustion "
        "sources remain, and several combinations of flux and transport can produce a similar increment.")
    fire_time=fire_gfs[fire_gfs.gas.eq("CO2")]
    tokens["FIRE_TIME_CHANGE"]=f"{100*(fire_time.window_mean_enhancement.mean()/fire_time.enhancement.mean()-1):+.1f}"
    tokens["OBS_TABLE"]=markdown_table(["Gas","Receptor value","Context median","Percentile rank"],
        [[gas,f"{r.receptor_value:,.2f} {r.unit}",f"{r['median']:,.2f} {r.unit}",f"{r.percentile_rank:.1f}%"] for gas,r in obs.iterrows()])
    metrics=[("Integrated sensitivity","sensitivity_sum",3),("Within 25 km (%)","within25_share_percent",1),
             ("Within 100 km (%)","within100_share_percent",1),("Within 250 km (%)","within250_share_percent",1),
             ("Southeast beyond 25 km (%)","se_beyond25_share_percent",1),
             ("Median distance (km)","median_distance_km",0),("90th-percentile distance (km)","p90_distance_km",0),
             ("Median age (h)","median_lag_hours",0),("90th-percentile age (h)","p90_lag_hours",0)]
    tokens["TRANSPORT_TABLE"]=markdown_table(["Diagnostic","GDAS ensemble","GFS ensemble"],
         [[label,f"{transport.loc['GDAS',key]:.{precision}f}",f"{transport.loc['GFS',key]:.{precision}f}"] for label,key,precision in metrics])
    rows=[]
    for gas in ("CO2","CH4"):
        for sector,r in sectors.loc[gas].sort_values("mean",ascending=False).iterrows():
            rows.append(["CO₂ (ppm)" if gas=="CO2" else "CH₄ (ppb)",LABELS[sector],f"{r['mean']:.4f}",f"{r['min']:.4f}–{r['max']:.4f}"])
    tokens["SECTOR_TABLE"]=markdown_table(["Gas / unit","Sector","Mean","Seed range"],rows)
    rows=[]
    for gas in ("CO2","CH4"):
        for r in provinces[provinces.gas.eq(gas)].nlargest(5,"enhancement").itertuples():
            rows.append(["CO₂ (ppm)" if gas=="CO2" else "CH₄ (ppb)",str(r.province).title(),f"{r.enhancement:.4f}"])
    tokens["PROVINCE_TABLE"]=markdown_table(["Gas / unit","Province","Contribution"],rows)
    rows=[]
    for driver in ("GDAS","GFS"):
        sub=fire[fire.run.str.startswith(driver+"_")&~fire.run.str.contains("height")]
        for gas,r in sub.groupby("gas").enhancement.agg(["mean","min","max"]).iterrows():
            rows.append([driver,{"CO2":"CO₂ (ppm)","CH4":"CH₄ (ppb)","CO":"CO (ppb)"}[gas],f"{r['mean']:.3f}",f"{r['min']:.3f}–{r['max']:.3f}"])
    tokens["FIRE_TABLE"]=markdown_table(["Driver","Gas / unit","Mean","Seed range"],rows)
    worked=pd.read_csv(TABLES/"worked_convolution.csv")
    tokens["WORKED_TABLE"]=markdown_table(["Gas / unit","Cell (° N, ° E)","Sensitivity","Flux (µmol m⁻² s⁻¹)","Contribution"],
        [["CO₂ (ppm)" if r.gas=="CO2" else "CH₄ (ppb)",f"{r.lat:.3f}, {r.lon:.3f}",f"{r.sensitivity:.5f}",f"{r.flux_umol_m2_s:.5f}",f"{r.reported_contribution:.5f}"] for r in worked.itertuples()])
    from a51_bkt_inversion_report import build_inversion_sections
    tokens.update(build_inversion_sections())
    from a55_bkt_barra_report import build_barra_sections
    tokens.update(build_barra_sections())
    from a69_transport_benchmark_report import build_transport_sections
    tokens.update(build_transport_sections())
    template=(ROOT/"docs/BKT_GFS_Report_template.md").read_text()
    required=set(re.findall(r"\{\{([A-Z0-9_]+)\}\}",template))
    if required-tokens.keys():raise ValueError(f"Missing report tokens: {required-tokens.keys()}")
    text=re.sub(r"\{\{([A-Z0-9_]+)\}\}",lambda m:tokens[m[1]],template)
    return text,tokens


if __name__=="__main__":
    text,tokens=build_report()
    if write:
        (ROOT/"BKT_HYSPLIT_STILT_Footprint_Report.md").write_text(text)
    (OUT/"report_values.json").write_text(json.dumps(tokens,indent=2)+"\n")
    scripts=["a37_bkt_footprint.py","a38_bkt_footprint_report.py","a39_bkt_refinement.py",
             "a41_bkt_gfs.py","a42_bkt_sources.py","a43_bkt_source_analysis.py",
             "a44_bkt_gfs_figures.py","a45_bkt_gfs_report.py","bkt_footprint_spatial.py",
             "bkt_gfed_transfer.py","validate_bkt_gfs_report.py","ghg_common.py","a14_latex.py",
             "a46_bkt_inversion_transport.py","a47_bkt_inversion_inputs.py","a48_bkt_inversion_operator.py",
             "a49_bkt_methane_inversion.py","a50_bkt_inversion_figures.py","a51_bkt_inversion_report.py","bkt_methane_inverse.py",
             "validate_bkt_inversion.py","a52_bkt_barra_audit.py","a53_bkt_barra_subset.py",
             "a54_bkt_barra_quality.py","a55_bkt_barra_report.py","validate_bkt_barra.py",
             "a64_transport_benchmark.py","a65_transport_observations.py","a66_transport_diagnostics.py",
             "a67_transport_profile_evaluation.py","a68_transport_mixing_diagnostics.py",
             "a69_transport_benchmark_report.py","a70_transport_benchmark_figures.py","bkt_arl.py",
             "validate_transport_benchmark.py","a71_domain_budget_extension.py",
             "a72_domain_budget_figures.py","a73_domain_budget_report.py",
             "validate_domain_budget_extension.py"]
    manifest={"python":sys.version,
              "packages":{name:importlib.metadata.version(name) for name in
                          ("numpy","scipy","pandas","xarray","h5netcdf","h5py","matplotlib","cartopy","shapely","geopandas","pyogrio","pyproj")},
              "source_sha256":{name:hashlib.sha256((ROOT/"scripts"/name).read_bytes()).hexdigest() for name in scripts},
              "report_sha256":hashlib.sha256(text.encode()).hexdigest()}
    (OUT/"software_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(f"Scientific report: {len(text.split()):,} words")
