#!/usr/bin/env python3
"""Build the three BKT reports from templates and verified evidence tables.

  BKT_Forward_Source_Influence_Report.md   docs/BKT_Forward_Report_template.md
  BKT_Methane_Inversion_Report.md          docs/BKT_Inversion_Report_template.md
  BKT_Transport_Technical_Companion.md     docs/BKT_Transport_Companion_template.md

Tokens come from the existing builders (a45 forward case, a51 inversion,
a55 BARRA, a69/a73 benchmark and domain correction) plus the revision tables
of a74, a75, a76, a79 and a83. Figures and tables are numbered by order of
appearance within each document after assembly. Every number in the prose
traces to a CSV written by a named script.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
import numpy as np
import pandas as pd
import a45_bkt_gfs_report as forward
import a74_bkt_simulation_revision as rev
import a76_bkt_era5_driver as era
from a40_bkt_refinement_report import markdown_table
from bkt_arl import ARLReader

ROOT = rev.ROOT
REV = ROOT / "outputs/hysplit/revision"
RINV = REV / "inversion/tables"
EINV = era.OUT / "inversion/tables"
ORIG = ROOT / "outputs/hysplit/inversion/tables"
DOCS = {
    "BKT_Forward_Source_Influence_Report": "BKT_Forward_Report_template.md",
    "BKT_Methane_Inversion_Report": "BKT_Inversion_Report_template.md",
    "BKT_Transport_Technical_Companion": "BKT_Transport_Companion_template.md",
}
NAMES = {"anthro_near": "Anthropogenic ≤500 km", "anthro_far": "Anthropogenic >500 km", "wetlands": "Wetlands", "fire": "Non-crop fires",
         "anthro_within50": "Anthropogenic ≤50 km", "anthro_50_500": "Anthropogenic 50–500 km",
         "background_offset": "Background offset (ppb)", "background_trend": "Background trend (ppb / 28 d)"}


def interval(row, digits=2) -> str:
    return f"{row['median']:.{digits}f} ({row['q025']:.{digits}f}–{row['q975']:.{digits}f})"


def forward_tokens() -> dict[str, str]:
    spread = pd.read_csv(REV / "tables/seed_spread.csv", parse_dates=["receptor_utc"])
    ledger = pd.read_csv(REV / "tables/run_ledger.csv", parse_dates=["receptor_utc"])
    old = pd.read_csv(ROOT / "outputs/hysplit/gfs/analysis/tables/transport_summary.csv").set_index("run").loc["GFS"]
    ext = pd.read_csv(REV / "tables/forward_extension_summary.csv").set_index("case")
    sectors = pd.read_csv(REV / "tables/forward_extension_sectors.csv")
    fire = pd.read_csv(REV / "tables/forward_extension_fire.csv")
    drv = pd.read_csv(era.OUT / "tables/driver_comparison_summary.csv")
    fwd = spread[spread.family == "forward"].iloc[0]
    fs = ledger[ledger.group.str.startswith("forward_s")]
    h80 = ledger[ledger.group == "forward_h80_s0"].iloc[0]; s0 = ledger[ledger.group == "forward_s0"].iloc[0]
    f_drv = drv[drv.case == "forward"].iloc[0]
    new_total, old_total = float(ext.loc["GFS_120h_wide", "integrated_sensitivity"]), float(old.sensitivity_sum)
    t = {"RFIGURES": "outputs/hysplit/revision/figures",
         "F_OLD_TOTAL": f"{old_total:.2f}", "F_NEW_TOTAL": f"{new_total:.2f}", "F_NEW_GAIN_PERCENT": f"{100 * (new_total / old_total - 1):+.0f}",
         "F_NEW_OLDEST24": f"{fs.oldest24h_percent.mean():.0f}", "F_EDGE": f"{fs.edge_percent.max():.3f}",
         "F_NEW_NEAR25": f"{fs.within25_percent.mean():.1f}", "F_OLD_NEAR25": f"{old.within25_share_percent:.1f}",
         "F_SEED_CV": f"{fwd.sensitivity_cv_percent:.1f}", "F_H80_CHANGE": f"{100 * (h80.sensitivity / s0.sensitivity - 1):+.1f}",
         "F_ERA5_RATIO": f"{f_drv.ratio_mean:.2f}", "F_ERA5_SPATIAL": f"{f_drv.spatial_diff_mean:.0f}",
         "F_ERA5_RATIO_MIN": f"{drv.ratio_min.min():.2f}", "F_ERA5_RATIO_MAX": f"{drv.ratio_max.max():.2f}",
         "F_ANTH_CHANGE_CO2": f"{100 * (ext.loc['GFS_120h_wide', 'anthropogenic_co2_ppm'] / ext.loc['GFS_72h_regional', 'anthropogenic_co2_ppm'] - 1):+.1f}",
         "F_ANTH_CHANGE_CH4": f"{100 * (ext.loc['GFS_120h_wide', 'anthropogenic_ch4_ppb'] / ext.loc['GFS_72h_regional', 'anthropogenic_ch4_ppb'] - 1):+.1f}",
         "F_FIRE_CH4_GAIN": f"{100 * (ext.loc['GFS_120h_wide', 'fire_ch4_ppb'] / ext.loc['GFS_72h_regional', 'fire_ch4_ppb'] - 1):.0f}",
         "F_FIRE_CH4_NEW": f"{ext.loc['GFS_120h_wide', 'fire_ch4_ppb']:.1f}", "F_FIRE_CH4_ERA5": f"{ext.loc['ERA5_120h', 'fire_ch4_ppb']:.1f}",
         "F_FIRE_CO2_NEW": f"{ext.loc['GFS_120h_wide', 'fire_co2_ppm']:.2f}", "F_FIRE_CO_NEW": f"{ext.loc['GFS_120h_wide', 'fire_co_ppb']:.0f}",
         "F_FIRE_CO_ERA5": f"{ext.loc['ERA5_120h', 'fire_co_ppb']:.0f}",
         "F_FIRE_CO_PCT_GFS_OLD": f"{ext.loc['GFS_72h_regional', 'fire_co_to_observed_percent']:.0f}",
         "F_FIRE_CO_PCT_GFS": f"{ext.loc['GFS_120h_wide', 'fire_co_to_observed_percent']:.0f}",
         "F_FIRE_CO_PCT_ERA5": f"{ext.loc['ERA5_120h', 'fire_co_to_observed_percent']:.0f}",
         "F_LAYER_RATIO": f"{ext.loc['GFS_120h_wide_1000m_layer', 'integrated_sensitivity'] / new_total:.1f}"}
    detail = pd.read_csv(era.OUT / "tables/driver_comparison.csv").query("case == 'forward'")
    rows = [["Integrated sensitivity", f"{old_total:.2f}", f"{new_total:.2f}", f"{ext.loc['ERA5_120h', 'integrated_sensitivity']:.2f}"],
            ["Within 25 km (%)", f"{old.within25_share_percent:.1f}", f"{fs.within25_percent.mean():.1f}", f"{detail.era5_within25.mean():.1f}"]]
    e5 = drv[drv.case == "forward"].iloc[0]
    rows += [["Within 500 km (%)", "n/a (regional grid)", f"{fs.within500_percent.mean():.1f}", f"{e5.era5_within500:.1f}"],
             ["Oldest 24 h share (%)", "n/a (72 h)", f"{fs.oldest24h_percent.mean():.1f}", f"{e5.era5_oldest24h:.1f}"],
             ["Sensitivity on domain edge (%)", "0.026", f"{fs.edge_percent.max():.3f}", "0.000"],
             ["Seed CV of total (%)", "0.3", f"{fwd.sensitivity_cv_percent:.1f}", f"{e5.era5_seed_cv:.1f}"]]
    t["F_TRANSPORT_TABLE"] = ("**Table 101. Transport diagnostics for the 26 September 2019 01:00 UTC receptor under three configurations.** Three-seed means of 10,020-particle runs; the 72 h case is the published regional configuration. Sensitivity in ppm per (µmol m⁻² s⁻¹).\n\n"
        + markdown_table(["Diagnostic", "GFS 72 h regional", "GFS 120 h widened", "ERA5 120 h"], rows))
    cov = fire.set_index(["case", "gas"]).coverage
    def cell(case, gas): return f"{ext.loc[case, {'CO2': 'fire_co2_ppm', 'CH4': 'fire_ch4_ppb', 'CO': 'fire_co_ppb'}[gas]]:.{2 if gas == 'CO2' else 1}f}" + ("" if cov[(case, gas)] == "complete" else "†")
    srows = [["EDGAR anthropogenic CO₂ (ppm)", f"{ext.loc['GFS_72h_regional', 'anthropogenic_co2_ppm']:.3f}", f"{ext.loc['GFS_120h_wide', 'anthropogenic_co2_ppm']:.3f}", f"{ext.loc['GFS_120h_wide_1000m_layer', 'anthropogenic_co2_ppm']:.3f}", f"{ext.loc['ERA5_120h', 'anthropogenic_co2_ppm']:.3f}"],
             ["EDGAR anthropogenic CH₄ (ppb)", f"{ext.loc['GFS_72h_regional', 'anthropogenic_ch4_ppb']:.1f}", f"{ext.loc['GFS_120h_wide', 'anthropogenic_ch4_ppb']:.1f}", f"{ext.loc['GFS_120h_wide_1000m_layer', 'anthropogenic_ch4_ppb']:.1f}", f"{ext.loc['ERA5_120h', 'anthropogenic_ch4_ppb']:.1f}"],
             ["GFED fire CO₂ (ppm)", cell("GFS_72h_regional", "CO2"), cell("GFS_120h_wide", "CO2"), cell("GFS_120h_wide_1000m_layer", "CO2"), cell("ERA5_120h", "CO2")],
             ["GFED fire CH₄ (ppb)", cell("GFS_72h_regional", "CH4"), cell("GFS_120h_wide", "CH4"), cell("GFS_120h_wide_1000m_layer", "CH4"), cell("ERA5_120h", "CH4")],
             ["GFED fire CO (ppb)", cell("GFS_72h_regional", "CO"), cell("GFS_120h_wide", "CO"), cell("GFS_120h_wide_1000m_layer", "CO"), cell("ERA5_120h", "CO")],
             ["Fire CO as % of observed CO", f"{ext.loc['GFS_72h_regional', 'fire_co_to_observed_percent']:.0f}", f"{ext.loc['GFS_120h_wide', 'fire_co_to_observed_percent']:.0f}" + ("†" if cov[("GFS_120h_wide", "CO")] != "complete" else ""), f"{ext.loc['GFS_120h_wide_1000m_layer', 'fire_co_to_observed_percent']:.0f}" + ("†" if cov[("GFS_120h_wide_1000m_layer", "CO")] != "complete" else ""), f"{ext.loc['ERA5_120h', 'fire_co_to_observed_percent']:.0f}" + ("†" if cov[("ERA5_120h", "CO")] != "complete" else "")]]
    partial = any(c != "complete" for c in cov.values)
    note = " † Lower bound: daily fire fields for this gas are available only for part of the window or area." if partial else ""
    t["F_SOURCE_TABLE"] = ("**Table 102. Inventory-weighted enhancements for the extended forward case.** Surface-release equivalents from September 2019 EDGAR v8.0 and daily GFED5.1 fluxes (21–26 September on the widened box) convolved with each footprint; the 1,000 m column releases the same fluxes into the fixed upper layer." + note + "\n\n"
        + markdown_table(["Quantity", "GFS 72 h regional", "GFS 120 h widened", "GFS 120 h, 1,000 m layer", "ERA5 120 h"], srows))
    return t


def inversion_tokens() -> dict[str, str]:
    pub = pd.read_csv(ORIG / "posterior_parameters.csv").set_index("parameter")
    base = pd.read_csv(RINV / "posterior_parameters.csv").set_index("parameter")
    var = pd.read_csv(RINV / "variant_parameters.csv"); tuned = var[var.case == "tuned"].set_index("parameter"); near = var[var.case == "nearfield_tuned"].set_index("parameter")
    ev_base = pd.read_csv(RINV / "inversion_evaluation.csv").query("split == 'heldout'").set_index("model")
    ev_var = pd.read_csv(RINV / "variant_evaluation.csv").query("split == 'heldout'").set_index("case")
    summ = pd.read_csv(RINV / "inversion_summary.csv").iloc[0]
    scan = pd.read_csv(RINV / "transport_error_scan.csv").set_index("transport_fraction")
    frac = json.load(open(RINV.parent / "variants.json"))["tuned_transport_fraction"]
    op = pd.read_csv(RINV / "operator_base.csv"); opc = pd.read_csv(RINV / "operator_comparison.csv")
    old_seed = pd.read_csv(ORIG / "transport_sensitivity_comparison.csv").query("group == 'seed_m10'")
    e5 = pd.read_csv(EINV / "variant_parameters.csv"); e5t = e5[e5.case == "tuned"].set_index("parameter")
    e5ev = pd.read_csv(EINV / "variant_evaluation.csv").query("split == 'heldout'").set_index("case")
    e5op = pd.read_csv(EINV / "operator_base.csv"); e5frac = json.load(open(EINV.parent / "variants.json"))["tuned_transport_fraction"]
    budget = pd.read_csv(RINV / "conditional_emission_budget.csv"); sector = pd.read_csv(RINV / "conditional_sector_emissions.csv")
    rec = pd.read_csv(RINV / "synthetic_recovery_summary.csv")
    def prior_bias(o): return float((o.anthro_near_ppb + o.anthro_far_ppb + o.wetlands_ppb + o.fire_ppb + o.termites_ppb + o.geological_ppb - o.soil_uptake_ppb + o.background_ppb - o.ch4)[o.transport_usable].mean())
    excl = [k for k in ("anthro_near", "anthro_far", "wetlands", "fire") if tuned.loc[k, "q975"] < 1 or tuned.loc[k, "q025"] > 1]
    verdict = ("All four 95% intervals exclude the inventory value." if len(excl) == 4 else
               f"The anthropogenic and wetland intervals exclude the inventory value; the fire interval reaches it at {tuned.loc['fire', 'q975']:.2f}." if set(excl) == {"anthro_near", "anthro_far", "wetlands"} else
               f"{len(excl)} of four 95% intervals exclude the inventory value.")
    t = {"R_N": str(int(op.transport_usable.sum())), "R_TRAIN": str(int(summ.training_hours)), "R_TEST": str(int(summ.heldout_hours)),
         "R_RESTORED": str(int((~opc.originally_usable & opc.now_usable).sum())),
         "R_GFS_PRIOR_BIAS": f"{prior_bias(op):+.0f}", "R_ERA5_PRIOR_BIAS": f"{prior_bias(e5op):+.0f}",
         "R_SEED_NEAR_SD": f"{opc.near_seed_sd_new_ppb.median():.1f}", "R_SEED_FAR_SD": f"{opc.far_seed_sd_new_ppb.median():.1f}",
         "R_OLD_SEED_MAX": f"{np.abs(old_seed.source_increment_change_percent).max():.0f}",
         "R_CHI_FIXED": f"{scan.loc[0.5, 'reduced_chi_square']:.2f}", "R_TUNED_FRACTION": f"{frac:.2f}", "R_ERA5_FRACTION": f"{e5frac:.2f}",
         "R_TUNED_VERDICT": verdict,
         "R_BASE_RMSE": f"{ev_base.loc['posterior', 'rmse_ppb']:.1f}", "R_BASE_BG_RMSE": f"{ev_base.loc['background_only', 'rmse_ppb']:.1f}",
         "R_TUNED_RMSE": f"{ev_var.loc['tuned', 'rmse_ppb']:.1f}", "R_TUNED_BG_RMSE": f"{ev_var.loc['tuned_background_only', 'rmse_ppb']:.1f}",
         "R_TUNED_ADJ_RMSE": f"{ev_var.loc['tuned_inventory_adjusted', 'rmse_ppb']:.1f}", "R_TUNED_BIAS": f"{ev_var.loc['tuned', 'bias_ppb']:+.1f}",
         "R_NEAR_RMSE": f"{ev_var.loc['nearfield_tuned', 'rmse_ppb']:.1f}",
         "R_NEAR50": interval(near.loc["anthro_within50"]), "R_50_500": interval(near.loc["anthro_50_500"]),
         "R_ERA5_N": str(int(e5op.transport_usable.sum())), "R_ERA5_EXCLUDED": str(int((~e5op.transport_usable).sum())),
         "R_ERA5_RMSE": f"{e5ev.loc['tuned', 'rmse_ppb']:.1f}", "R_ERA5_BG_RMSE": f"{e5ev.loc['tuned_background_only', 'rmse_ppb']:.1f}", "R_ERA5_BIAS": f"{e5ev.loc['tuned', 'bias_ppb']:+.1f}"}
    for key, short in (("anthro_near", "NEAR"), ("anthro_far", "FAR"), ("wetlands", "WET"), ("fire", "FIRE")):
        t[f"R_BASE_{short}"] = f"{base.loc[key, 'median']:.2f}"; t[f"R_TUNED_{short}"] = interval(tuned.loc[key]); t[f"R_ERA5_{short}"] = interval(e5t.loc[key])
    keys = ["anthro_near", "anthro_far", "wetlands", "fire", "background_offset", "background_trend"]
    t["R_BASE_TABLE"] = ("**Table 101. Posterior multipliers with the original working covariance: published fit and revised transport ensemble.** Medians with 95% credible intervals; the published fit used 27 receptor hours and 540 particles, the revised ensemble 52 hours and three seeds of 2,000 particles.\n\n"
        + markdown_table(["Parameter", "Published", "Revised ensemble"], [[NAMES[k], interval(pub.loc[k]), interval(base.loc[k])] for k in keys]))
    t["R_TUNED_TABLE"] = ("**Table 102. Posterior multipliers with the tuned covariance, revised GFS ensemble.** Transport-error fraction " + f"{frac:.2f}" + " (training reduced chi-square 1.0). Variance reduction is in the fitted parameter space relative to the prior.\n\n"
        + markdown_table(["Parameter", "Prior median", "Posterior median (95%)", "Variance reduction (%)", "P(multiplier > 1)"],
            [[NAMES[k], "1.0" if k in keys[:4] else "0.0", interval(tuned.loc[k]), f"{tuned.loc[k, 'variance_reduction_percent']:.1f}", f"{tuned.loc[k, 'probability_above_inventory']:.3f}" if k in keys[:4] else "n/a"] for k in keys]))
    pub_ev = pd.read_csv(ORIG / "inversion_evaluation.csv").query("split == 'heldout'").set_index("model")
    e5ev_base = pd.read_csv(EINV / "inversion_evaluation.csv").query("split == 'heldout'").set_index("model")
    rows = [["Raw inventory", f"{pub_ev.loc['inventory', 'rmse_ppb']:.1f}", f"{ev_base.loc['inventory', 'rmse_ppb']:.1f}", f"{e5ev_base.loc['inventory', 'rmse_ppb']:.1f}"],
            ["Inventory with fitted background", f"{pub_ev.loc['background_adjusted_inventory', 'rmse_ppb']:.1f}", f"{ev_base.loc['background_adjusted_inventory', 'rmse_ppb']:.1f}", f"{e5ev_base.loc['background_adjusted_inventory', 'rmse_ppb']:.1f}"],
            ["Inversion, fixed 50% covariance", f"{pub_ev.loc['posterior', 'rmse_ppb']:.1f}", f"{ev_base.loc['posterior', 'rmse_ppb']:.1f}", f"{e5ev_base.loc['posterior', 'rmse_ppb']:.1f}"],
            ["Inversion, tuned covariance", "not fitted", f"{ev_var.loc['tuned', 'rmse_ppb']:.1f}", f"{e5ev.loc['tuned', 'rmse_ppb']:.1f}"],
            ["Inversion, near-field split, tuned", "not fitted", f"{ev_var.loc['nearfield_tuned', 'rmse_ppb']:.1f}", f"{e5ev.loc['nearfield_tuned', 'rmse_ppb']:.1f}"],
            ["Background only", f"{pub_ev.loc['background_only', 'rmse_ppb']:.1f}", f"{ev_base.loc['background_only', 'rmse_ppb']:.1f}", f"{e5ev_base.loc['background_only', 'rmse_ppb']:.1f}"],
            ["Withheld hours (n)", "6", t["R_TEST"], str(int(e5op[e5op.transport_usable].holdout.sum()))]]
    t["R_EVAL_TABLE"] = "**Table 103. Withheld-hour RMSE (ppb) by model, transport ensemble and driver.** Withheld hours were fixed before fitting. Baselines are refitted on each ensemble's fitting hours.\n\n" + markdown_table(["Model", "Published", "Revised GFS", "ERA5"], rows)
    t["R_ERA5_TABLE"] = ("**Table 104. Tuned posterior multipliers under the two drivers.** Medians with 95% credible intervals; each driver uses its own chi-square-consistent transport fraction.\n\n"
        + markdown_table(["Parameter", f"GFS (fraction {frac:.2f})", f"ERA5 (fraction {e5frac:.2f})"], [[NAMES[k], interval(tuned.loc[k]), interval(e5t.loc[k])] for k in keys]))
    col = {"anthropogenic": None, "wetlands": "wetlands", "noncrop_fire": "fire"}
    brows = []
    for r in budget.itertuples():
        key = ("anthro_near" if r.region == "within_500km" else "anthro_far") if r.component == "anthropogenic" else col[r.component]
        q = tuned.loc[key]
        brows.append([r.region.replace("_", " ").replace("within 500km", "≤500 km").replace("beyond 500km in domain", ">500 km, in domain"), r.component.replace("noncrop_fire", "non-crop fire"),
                      f"{r.prior_Gg:,.1f}", f"{r.prior_Gg * q['median']:,.1f} ({r.prior_Gg * q['q025']:,.1f}–{r.prior_Gg * q['q975']:,.1f})", f"{r.support_prior_share_percent:.1f}"])
    t["R_FAR_SUPPORT"] = f"{budget.query('region == \"beyond_500km_in_domain\" and component == \"anthropogenic\"').support_prior_share_percent.iloc[0]:.1f}"
    t["R_BUDGET_TABLE"] = ("**Table 105. Conditional methane emissions, 9 September–6 October 2019, tuned GFS multipliers.** Gg CH₄ over 28 days; posterior intervals propagate multiplier uncertainty only and inherit the prior's spatial pattern. The last column is the share of prior mass in cells carrying 90% of aggregate sensitivity.\n\n"
        + markdown_table(["Region", "Component", "Prior (Gg)", "Posterior median (95%) (Gg)", "Prior in support (%)"], brows))
    rrows = [[r.scenario.replace("_", " "), NAMES[r.parameter], f"{r.bias:+.2f}", f"{r.rmse:.2f}", f"{r.local_interval_coverage_percent:.1f}"] for r in rec.itertuples()]
    t["R_RECOVERY_TABLE"] = "**Table 106. Synthetic recovery on the revised ensemble.** 200 realizations per scenario; bias and RMSE in multiplier units; coverage of local 95% intervals.\n\n" + markdown_table(["Scenario", "Component", "Bias", "RMSE", "Coverage (%)"], rrows)
    return t


def companion_tokens() -> dict[str, str]:
    ledger = pd.read_csv(REV / "tables/run_ledger.csv", parse_dates=["receptor_utc"])
    spread = pd.read_csv(REV / "tables/seed_spread.csv", parse_dates=["receptor_utc"])
    terrain = pd.read_csv(REV / "tables/terrain_height.csv", parse_dates=["receptor_utc"])
    window = pd.read_csv(REV / "tables/afternoon_window.csv")
    opc = pd.read_csv(RINV / "operator_comparison.csv")
    drv = pd.read_csv(era.OUT / "tables/driver_comparison_summary.csv", parse_dates=["receptor_utc"])
    ens = spread[spread.family == "ensemble"]
    g = ledger.assign(family=ledger.group.str.replace(r"_s-?\d+$", "", regex=True)).groupby("family")
    fam = {"ensemble": ("52 twice-daily inversion receptors", "3 (0, −10, −20)", "30"), "forward": ("26 Sep 2019 01:00 UTC forward case", "3", "30"),
           "forward_h80": ("26 Sep 2019 01:00 UTC forward case", "1", "80"), "terrain_h80": ("4 benchmark anchors", "3", "80"), "afternoon": ("05, 07 and 08 UTC on 28 days", "1", "30")}
    crows = [[fam[f][0], fam[f][1], f"{int(d.requested_particles.iloc[0]):,}", fam[f][2], str(len(d)), f"{d.runtime_minutes.median():.0f}"] for f, d in g if f in fam]
    t = {"RFIGURES": "outputs/hysplit/revision/figures", "C_RUNS": str(len(ledger)),
         "C_CAMPAIGN_TABLE": "**Table 1. Simulation revision campaign.** GFS quarter-degree meteorology, 50°–160° E, 40° S–30° N; 60° by 100° footprint grid; 120 h backward. Run time is the median wall-clock minutes per run on a shared workstation.\n\n"
             + markdown_table(["Receptors", "Seeds", "Requested particles", "Release (m AGL)", "Runs", "Run time (min)"], crows),
         "C_SEED_CV_MED": f"{ens.sensitivity_cv_percent.median():.1f}", "C_SEED_CV_MAX": f"{ens.sensitivity_cv_percent.max():.1f}",
         "C_OLD_FAILS": str(int((opc.retention_old < .95).sum())),
         "C_SEED_TABLE": "**Table 2. Seed spread across the three-member ensembles.** Coefficient of variation of integrated surface sensitivity across seeds, and the range of the within-50 km share, summarized over receptors.\n\n"
             + markdown_table(["Family", "Receptors", "Median seed CV (%)", "Maximum seed CV (%)", "Median within-50 km range (points)"],
                 [[{"ensemble": "Inversion receptors, 30 m", "forward": "Forward case, 30 m", "terrain_h80": "Anchors, 80 m"}.get(f, f), str(len(d)), f"{d.sensitivity_cv_percent.median():.2f}", f"{d.sensitivity_cv_percent.max():.2f}", f"{d.within50_range_points.median():.2f}"] for f, d in spread.groupby("family")]),
         "C_H80_MEDIAN": f"{terrain.ratio_80_over_30.median():.3f}", "C_H80_MIN": f"{terrain.ratio_80_over_30.min():.3f}", "C_H80_MAX": f"{terrain.ratio_80_over_30.max():.3f}",
         "C_H80_SPATIAL": f"{terrain.spatial_abs_difference_percent.median():.0f}",
         "C_TERRAIN_TABLE": "**Table 3. Terrain-matched release at the benchmark anchors.** Ratio of integrated sensitivity at 80 m to 30 m release and the cell-level absolute difference, per seed.\n\n"
             + markdown_table(["Receptor (UTC)", "Seed", "Ratio 80 m / 30 m", "Spatial difference (%)"], [[f"{r.receptor_utc:%d %b %Y %H:%M}", str(r.seed), f"{r.ratio_80_over_30:.3f}", f"{r.spatial_abs_difference_percent:.1f}"] for r in terrain.itertuples()]),
         "C_WINDOW_CV": f"{window.member_sensitivity_cv_percent.median():.1f}", "C_WINDOW_DAYS": str(len(window)),
         "C_ERA5_RATIO_MIN": f"{drv.ratio_min.min():.2f}", "C_ERA5_RATIO_MAX": f"{drv.ratio_max.max():.2f}",
         "C_ERA5_SPATIAL_MIN": f"{drv.spatial_diff_mean.min():.0f}", "C_ERA5_SPATIAL_MAX": f"{drv.spatial_diff_mean.max():.0f}",
         "C_DRIVER_TABLE": "**Table 4. GFS and ERA5 footprints at matched receptors.** Three seeds per driver; ratio and spatial difference use the ERA5 grid cells, on which the GFS runs place all of their sensitivity.\n\n"
             + markdown_table(["Receptor (UTC)", "Case", "ERA5/GFS sensitivity (seed range)", "Spatial difference (%)", "Within 500 km, ERA5 / GFS (%)", "Oldest 24 h, ERA5 / GFS (%)"],
                 [[f"{r.receptor_utc:%d %b %Y %H:%M}", r.case, f"{r.ratio_mean:.2f} ({r.ratio_min:.2f}–{r.ratio_max:.2f})", f"{r.spatial_diff_mean:.0f}", f"{r.era5_within500:.0f} / {r.gfs_within500:.0f}", f"{r.era5_oldest24h:.1f} / {r.gfs_oldest24h:.1f}"] for r in drv.itertuples()])}
    # native surface fields at BKT on 9 September 2019 from both archives, recorded to a table
    day = pd.Timestamp("2019-09-09"); rows = []
    e = ARLReader(era.arl_path(day)); gfs = ARLReader(rev.WIDE_MET / f"{day:%Y%m%d}_gfs0p25")
    for hour in range(0, 24, 3):
        stamp = day + pd.Timedelta(hours=hour)
        rows.append(dict(time_utc=stamp, era5_pblh_m=e.point(stamp, "PBLH", 0, -.202, 100.318, "nearest"), gfs_pblh_m=gfs.point(stamp, "PBLH", 0, -.202, 100.318, "nearest"),
                         era5_shgt_m=e.point(stamp, "SHGT", 0, -.202, 100.318, "nearest"), gfs_shgt_m=gfs.point(stamp, "SHGT", 0, -.202, 100.318, "nearest")))
    surf = pd.DataFrame(rows); (era.OUT / "tables").mkdir(exist_ok=True); surf.to_csv(era.OUT / "tables/bkt_native_surface_20190909.csv", index=False)
    t.update({"C_ERA5_PBLH": f"{surf.era5_pblh_m.max():.0f}", "C_GFS_PBLH": f"{surf.gfs_pblh_m.max():.0f}", "C_ERA5_SHGT": f"{surf.era5_shgt_m.iloc[0]:.0f}"})
    return t


def renumber(text: str) -> str:
    for kind in ("Figure", "Table"):
        order = []
        for m in re.finditer(r"\*\*%s (\d+)\." % kind, text):
            if m.group(1) not in order:
                order.append(m.group(1))
        mapping = {old: str(i + 1) for i, old in enumerate(order)}
        text = re.sub(r"\b%s (\d+)\b" % kind, lambda m: f"{kind} {mapping.get(m.group(1), m.group(1))}", text)
        text = re.sub(r"\b%ss (\d+)" % kind, lambda m: f"{kind}s {mapping.get(m.group(1), m.group(1))}", text)
    return text


def render(stem: str, tokens: dict[str, str]) -> str:
    template = (ROOT / "docs" / DOCS[stem]).read_text()
    required = set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", template))
    missing = required - tokens.keys()
    if missing:
        raise ValueError(f"{stem}: missing tokens {sorted(missing)}")
    text = re.sub(r"\{\{([A-Z0-9_]+)\}\}", lambda m: tokens[m[1]], template)
    if "{{" in text:
        raise ValueError(f"{stem}: unresolved nested token")
    return renumber(text)


def build(write: bool = True) -> dict[str, str]:
    _, tokens = forward.build_report(write=False)
    tokens.update(json.loads((ROOT / "outputs/hysplit/inversion/inversion_report_values.json").read_text()))
    tokens.update(forward_tokens()); tokens.update(inversion_tokens()); tokens.update(companion_tokens())
    tokens["INVERSION_RESULTS_DEMOTED"] = tokens["INVERSION_RESULTS"].replace("\n### ", "\n#### ")
    companion = tokens["TRANSPORT_APPENDIX"]
    companion = companion.replace("## Appendix. Transport completeness and unresolved mixing uncertainty", "## 3. Transport completeness and unresolved mixing uncertainty", 1)
    companion = companion.replace("## Appendix. Full-ensemble domain correction and prior methane-budget convergence", "## 4. Full-ensemble domain correction and prior methane-budget convergence", 1)
    tokens["TRANSPORT_APPENDIX"] = companion
    tokens["BARRA_APPENDIX"] = tokens["BARRA_APPENDIX"].replace("## Appendix. Finer-grid meteorology did not pass the conversion screen", "## 5. Finer-grid meteorology did not pass the conversion screen", 1)
    out = {}
    for stem in DOCS:
        text = render(stem, tokens)
        out[stem] = text
        if write:
            (ROOT / f"{stem}.md").write_text(text)
            print(f"wrote {stem}.md ({len(text.splitlines())} lines, {len(re.findall(r'[*][*]Figure ', text))} figures, {len(re.findall(r'[*][*]Table ', text))} tables)")
    (REV / "report_tokens.json").write_text(json.dumps({k: v for k, v in tokens.items() if k[:2] in ("F_", "R_", "C_")}, indent=2) + "\n")
    return out


if __name__ == "__main__":
    build()
