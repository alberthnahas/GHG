#!/usr/bin/env python3
"""Expand canonical Markdown narrative with computed BKT refinement evidence."""
from __future__ import annotations
import json
from pathlib import Path
import re

import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"outputs/hysplit/refinement/analysis"
TEMPLATE=ROOT/"docs/BKT_Footprint_Report_template.md"
DESTINATION=ROOT/"BKT_HYSPLIT_STILT_Footprint_Report.md"


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    return "\n".join(["| "+" | ".join(headers)+" |",
                       "| "+" | ".join("---" for _ in headers)+" |"]+
                      ["| "+" | ".join(map(str,row))+" |" for row in rows])


def build_report() -> tuple[str,dict]:
    metrics=json.loads((OUT/"metrics.json").read_text())
    summary=pd.read_csv(OUT/"tables/experiment_summary.csv",index_col="run")
    spread=pd.read_csv(OUT/"tables/seed_spread.csv",index_col="metric")
    bandwidth=pd.read_csv(OUT/"tables/bandwidth_cross_validation.csv")
    smoothing=pd.read_csv(OUT/"tables/smoothing_sensitivity.csv")
    obs=pd.read_csv(OUT/"tables/observation_context_summary.csv")
    central=summary.loc["ensemble_mean"]
    sigma=metrics["sigma_cells"]
    if sigma != 0:
        raise ValueError("The narrative describes a zero-bandwidth result; review it before rebuilding")
    boundary=metrics["map"]["boundary"]
    tokens={
        "ACTUAL_N":f"{metrics['actual_particles_per_member'][0]:,}",
        "SE_SHARE":f"{central.se_beyond25_share_percent:.1f}",
        "NEAR_SHARE":f"{central.within25_share_percent:.1f}",
        "MEDIAN_DISTANCE":f"{central.median_distance_km:.0f}",
        "MEDIAN_LAG":f"{central.median_lag_hours:.0f}",
        "P90_LAG":f"{central.p90_lag_hours:.0f}",
        "SE_MIN":f"{spread.loc['se_beyond25_share_percent','minimum']:.1f}",
        "SE_MAX":f"{spread.loc['se_beyond25_share_percent','maximum']:.1f}",
        "TOTAL_MIN":f"{spread.loc['sensitivity_sum','minimum']:.3f}",
        "TOTAL_MAX":f"{spread.loc['sensitivity_sum','maximum']:.3f}",
        "SIGMA_CELLS":f"{sigma:g}","SIGMA_DEG":f"{sigma*.1:g}",
        "SIGMA_KM":f"{sigma*.1*111.195:.1f}",
        "VALID_HOURS":str(int(obs.valid_hours.iloc[0])),
        "EXPECTED_HOURS":str(int(obs.expected_hours.iloc[0])),
        "NATIVE_RATIO":f"{metrics['controlled_probes']['native_ratio_500_over_540']:.5f}",
        "NORM_ERROR":f"{100*metrics['controlled_probes']['corrected_l1_relative_error']:.3f}",
        "HIDDEN_SHARE":f"{metrics['map']['share_below_display_threshold_percent']:.3f}",
        "OUTSIDE_SHARE":f"{metrics['map']['share_outside_map_extent_percent']:.3f}",
        "PROVINCES":str(boundary["feature_count"]),
        "INVALID_GEOMETRIES":str(boundary["invalid_geometries_repaired_in_memory"]),
        "LAG_RECENT":f"{central.share_1_24h_percent:.1f}",
        "LAG_MIDDLE":f"{central.share_25_48h_percent:.1f}",
        "LAG_OLD":f"{central.share_49_72h_percent:.1f}",
        "HEIGHT_TOTAL_CHANGE":f"{summary.loc['n10000_height60','total_change_percent_vs_seed0']:+.2f}",
        "GRID_TOTAL_CHANGE":f"{summary.loc['n10000_coarse','total_change_percent_vs_seed0']:.3f}",
        "GRID_TV":f"{summary.loc['n10000_coarse','shape_tv_1deg_percent_vs_seed0']:.2f}",
        "MET_BYTES":f"{metrics['met_provenance']['bytes']:,}",
        "MET_SHA":metrics["met_provenance"]["sha256"],
        "BOUNDARY_SHA":boundary["sha256"],
        "REDISTRIBUTION":f"{smoothing.loc[smoothing.sigma_cells.eq(sigma),'l1_redistribution_percent'].iloc[0]:.2f}",
        "FIGURES":"outputs/hysplit/refinement/analysis/figures",
    }
    tokens["OBS_TABLE"]=markdown_table(
        ["Gas","Receptor value","Context median","Percentile rank"],
        [[r.species,f"{r.receptor_value:,.2f} {r.unit}",f"{r.median:,.2f} {r.unit}",
          f"{r.percentile_rank:.1f}%"] for r in obs.itertuples()])
    names={"original":"Original pilot","n2000_s0":"2,000 requested",
           "n10000_s0":"10,000 seed A","n10000_sm10":"10,000 seed B",
           "n10000_sm20":"10,000 seed C","n10000_coarse":"Coarse-grid test",
           "n10000_height60":"Height scenario"}
    tokens["EXPERIMENT_TABLE"]=markdown_table(
        ["Experiment","Actual particles","Seed","Grid; height"],
        [[label,f"{int(summary.loc[key,'actual_particles']):,}",str(int(summary.loc[key,'seed'])),
          f"{summary.loc[key,'grid_spacing_deg']:g}°; {summary.loc[key,'height_m_agl']:g} m"]
         for key,label in names.items()])
    base=float(bandwidth.loc[bandwidth.sigma_cells.eq(0),"mean_risk"].iloc[0])
    tokens["BANDWIDTH_TABLE"]=markdown_table(
        ["Width (cells)","Width (degrees)","Risk change (× 10⁻⁶)","Selected"],
        [[f"{r.sigma_cells:g}",f"{r.sigma_degrees:g}",f"{(r.mean_risk-base)*1e6:.3f}",
          "Yes" if r.selected else "No"] for r in bandwidth.itertuples()])
    tokens["CENTRAL_TABLE"]=markdown_table(["Diagnostic","Value"],[
        ["Integrated sensitivity [ppm / (µmol m⁻² s⁻¹)]",f"{central.sensitivity_sum:.3f}"],
        ["SE beyond 25 km (% of total)",f"{central.se_beyond25_share_percent:.1f}"],
        ["Within 25 km (%)",f"{central.within25_share_percent:.1f}"],
        ["Within 100 km (%)",f"{central.within100_share_percent:.1f}"],
        ["Within 250 km (%)",f"{central.within250_share_percent:.1f}"],
        ["Sensitivity-weighted median distance (km)",f"{central.median_distance_km:.0f}"],
        ["90th-percentile distance (km)",f"{central.p90_distance_km:.0f}"],
        ["Median backward lag (h)",f"{central.median_lag_hours:.0f}"],
        ["90th-percentile backward lag (h)",f"{central.p90_lag_hours:.0f}"],
    ])
    tokens["COMPARISON_TABLE"]=markdown_table(
        ["Experiment","Total change (%)","Regional shape variation (%)"],
        [[label,f"{summary.loc[key,'total_change_percent_vs_seed0']:+.2f}",
          f"{summary.loc[key,'shape_tv_1deg_percent_vs_seed0']:.2f}"]
         for key,label in names.items() if key!="n10000_s0"])
    template=TEMPLATE.read_text()
    required=set(re.findall(r"\{\{([A-Z0-9_]+)\}\}",template))
    if required-tokens.keys(): raise ValueError(f"Missing report fields: {required-tokens.keys()}")
    text=re.sub(r"\{\{([A-Z0-9_]+)\}\}",lambda m:tokens[m[1]],template)
    if "{{" in text: raise ValueError("Unresolved report placeholders")
    return text,tokens


if __name__=="__main__":
    text,tokens=build_report()
    DESTINATION.write_text(text,encoding="utf-8")
    (OUT/"report_values.json").write_text(json.dumps(tokens,indent=2)+"\n")
    print(f"Wrote {DESTINATION.name}: {len(text.split()):,} words")
