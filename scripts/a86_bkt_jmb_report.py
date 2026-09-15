#!/usr/bin/env python3
"""Build BKT_JMB_Two_Receptor_Report.md from its template and the a84/a87 evidence tables.

Every number in the prose is computed here from a CSV or JSON written by a84
(campaign, operator, inversion), a85 (figures), a87 (dataset availability) or
a88 (peatland and wet-versus-dry tests);
the 2019 comparison values come from the a75 revised inversion. Figures and
tables are numbered by order of appearance after assembly.
"""
from __future__ import annotations
import json
import re
import numpy as np
import pandas as pd
import a84_bkt_jmb_two_receptor as T
from a40_bkt_refinement_report import markdown_table
from a82_bkt_reports import renumber

ROOT = T.ROOT
STEM = "BKT_JMB_Two_Receptor_Report"
TEMPLATE = ROOT / "docs/BKT_JMB_Two_Receptor_Report_template.md"
REV2019 = ROOT / "outputs/hysplit/revision/inversion/tables/variant_parameters.csv"
NAMES = {"anthro_near": "Anthropogenic ≤500 km", "anthro_far": "Anthropogenic >500 km", "wetlands": "Wetlands", "fire": "Fires",
         "fuel_near": "Fuel exploitation ≤500 km", "other_near": "Other anthropogenic ≤500 km"}
CASES = {"bkt_only": "BKT only", "jmb_only": "Jambi only, all hours", "joint": "Joint, all hours",
         "joint_screened": "Joint, Jambi 18 UTC excluded", "joint_screened_sector": "Joint screened, sector split"}
SOURCE_LABELS = {"CH4_FUEL_EXPLOITATION": "EDGAR fuel exploitation", "CH4_AGRICULTURE": "EDGAR agriculture", "CH4_WASTE": "EDGAR waste",
                 "CH4_BUILDINGS": "EDGAR buildings", "wetlands": "LPJ-MERRA2 wetlands", "termites": "Termites (fixed)",
                 "geological": "Geological seepage (fixed)", "soil_uptake": "Soil uptake (fixed, subtracted)"}


def interval(row, digits: int = 2) -> str:
    return f"{row['median']:.{digits}f} ({row['q025']:.{digits}f}–{row['q975']:.{digits}f})"


def tokens() -> dict[str, str]:
    t: dict[str, str] = {"J_FIG": "outputs/hysplit/two_receptor/figures"}
    sel = json.loads((T.TABLES / "selection_summary.json").read_text())
    scan = pd.read_csv(T.TABLES / "window_scan.csv")
    ledger = pd.read_csv(T.TABLES / "run_ledger.csv")
    op = pd.read_csv(T.TABLES / "operator_base.csv", parse_dates=["time_utc"])
    sec = pd.read_csv(T.TABLES / "sector_responses_base.csv", parse_dates=["time_utc"])
    par = pd.read_csv(T.TABLES / "inversion_parameters.csv")
    ev = pd.read_csv(T.TABLES / "inversion_evaluation.csv")
    data = pd.read_csv(T.TABLES / "dataset_availability.csv")
    old = pd.read_csv(REV2019).query("case == 'tuned'").set_index("parameter")

    # ---- window and campaign
    t.update(J_SCHED=str(sel["scheduled_hours"]), J_JOINT=str(sel["joint_hours"]), J_HELD=str(sel["holdout_hours"]),
             J_BKT_VALID=str(sel["bkt_valid_hours"]), J_JMB_VALID=str(sel["jmb_valid_hours"]), J_RUNS=str(len(ledger)),
             J_COMPLETE=str(int(ledger.complete.sum())), J_RUNTIME=f"{ledger.runtime_min.median():.0f}",
             J_WALL=f"{ledger.runtime_min.sum() / 60 / 12:.0f}")
    if int(ledger.complete.sum()) != len(ledger):
        raise ValueError("Campaign ledger is incomplete")
    rows = [[f"{r.window_start} to {r.window_end}", str(r.scheduled_hours), str(r.bkt_valid), str(r.jmb_valid),
             f"{r.joint_valid} ({r.joint_percent:.0f}%)", "yes" if r.carbontracker_boundary else "no", "yes" if r.selected else ""]
            for r in scan.itertuples()]
    t["J_WINDOW_TABLE"] = ("**Table 1. Candidate joint windows at 06 and 18 UTC.** Valid means a methane value not flagged suspect. "
        "The boundary column records whether CarbonTracker-CH₄ 2025 mole fractions and LPJ-MERRA2 wetlands exist for the window.\n\n"
        + markdown_table(["Window", "Scheduled hours", "BKT valid", "Jambi valid", "Joint valid", "Boundary and wetlands", "Used"], rows))
    best = scan.loc[scan.joint_valid.idxmax()]
    t.update(J_BEST_WINDOW=f"{best.window_start} to {best.window_end}", J_BEST_JOINT=str(int(best.joint_valid)))

    # ---- operator
    op["enh"] = op.ch4 - op.background_ppb; op["hour"] = op.time_utc.dt.hour; op["wind"] = np.hypot(op.U10M, op.V10M)
    rows = []
    for code in ("BKT", "JMB"):
        s = op[op.station.eq(code)]; u = s[s.transport_usable]
        excluded = s[~s.transport_usable]
        t[f"J_{code}_USABLE"] = str(len(u)); t[f"J_{code}_EXCL"] = str(len(excluded))
        t[f"J_{code}_SENS"] = f"{s.sensitivity.mean():.1f}"; t[f"J_{code}_W500"] = f"{s.within500_sensitivity_percent.mean():.0f}"
        t[f"J_{code}_W50"] = f"{s.within50_sensitivity_percent.mean():.0f}"
        rows.append([T.STATIONS[code][0], f"{len(u)} of {len(s)}", f"{int((~u.holdout).sum())} / {int(u.holdout.sum())}",
                     f"{s.sensitivity.mean():.1f}", f"{s.within500_sensitivity_percent.mean():.0f}", f"{s.within50_sensitivity_percent.mean():.0f}",
                     f"{u.background_ppb.mean():.0f}", f"{u.enh.mean():.0f}"])
    t["J_OPERATOR_TABLE"] = ("**Table 2. Transport and operator summary by receptor.** Sensitivity is the three-seed mean integrated footprint in ppm per µmol m⁻² s⁻¹ over all 49 hours; background and enhancement are means over hours that pass the 95% particle-retention screen.\n\n"
        + markdown_table(["Receptor", "Usable hours", "Fitted / withheld", "Sensitivity", "Within 500 km (%)", "Within 50 km (%)", "Background (ppb)", "Observed enhancement (ppb)"], rows))
    for code in ("BKT", "JMB"):
        t[f"J_{code}_SHGT"] = f"{op[op.station.eq(code)].SHGT.median():.0f}"
    exc = op[~op.transport_usable]
    t["J_EXCL_LATE"] = str(int((exc.time_utc >= "2023-12-20").sum())); t["J_EXCL_ALL"] = str(len(exc))
    t["J_RET_MIN"] = f"{op.endpoint_survival_fraction.min():.2f}"

    # ---- prior source mix over usable hours
    usable = op.loc[op.transport_usable, ["station", "time_utc"]]
    mix = sec.merge(usable, on=["station", "time_utc"]).groupby(["station", "source"]).prior_enhancement_ppb.mean().unstack(0)
    fire = op[op.transport_usable].groupby("station").fire_ppb.mean()
    rows = [[SOURCE_LABELS[k], f"{mix.loc[k, 'BKT']:.1f}", f"{mix.loc[k, 'JMB']:.1f}"] for k in SOURCE_LABELS]
    rows.append(["CarbonTracker-CH₄ pyrogenic", f"{fire['BKT']:.1f}", f"{fire['JMB']:.1f}"])
    t["J_SOURCE_TABLE"] = ("**Table 3. Mean prior enhancement by source, ppb, over usable receptor hours.** Three-seed ensemble means; minor EDGAR sectors (industry, power, transport) are below 0.5 ppb at both receptors and are omitted from the table but not from the fit.\n\n"
        + markdown_table(["Source", "BKT", "Jambi"], rows))
    t.update(J_JMB_FUEL=f"{mix.loc['CH4_FUEL_EXPLOITATION', 'JMB']:.0f}", J_BKT_FUEL=f"{mix.loc['CH4_FUEL_EXPLOITATION', 'BKT']:.0f}",
             J_BKT_WET=f"{mix.loc['wetlands', 'BKT']:.0f}", J_JMB_WET=f"{mix.loc['wetlands', 'JMB']:.0f}",
             J_BKT_AGRI=f"{mix.loc['CH4_AGRICULTURE', 'BKT']:.0f}")

    # ---- diurnal contrast
    rows = []
    for code in ("BKT", "JMB"):
        for hour, wib in ((6, "13"), (18, "01")):
            s = op[op.station.eq(code) & op.hour.eq(hour) & op.transport_usable]
            prior = (s.anthro_near_ppb + s.anthro_far_ppb + s.wetlands_ppb + s.fire_ppb).mean()
            key = f"J_{code}_{hour:02d}"
            t.update({f"{key}_PBLH": f"{s.PBLH.median():.0f}", f"{key}_WIND": f"{s.wind.median():.1f}", f"{key}_ENH": f"{s.enh.mean():.0f}",
                      f"{key}_SD": f"{s.enh.std():.0f}", f"{key}_MAX": f"{s.enh.max():.0f}", f"{key}_PRIOR": f"{prior:.0f}", f"{key}_N": str(len(s))})
            rows.append([T.STATIONS[code][0], f"{hour:02d} UTC ({wib} WIB)", str(len(s)), f"{s.PBLH.median():.0f}", f"{s.wind.median():.1f}",
                         f"{s.enh.mean():.0f} ± {s.enh.std():.0f}", f"{s.enh.max():.0f}", f"{prior:.0f}"])
    t["J_DIURNAL_TABLE"] = ("**Table 4. Observed enhancement and model boundary layer by receptor and hour, usable hours.** Mixing depth and 10 m wind are native GFS values in the receptor cell; enhancement is observation minus endpoint background; prior is the sum of the four fitted components.\n\n"
        + markdown_table(["Receptor", "Hour", "n", "Mixing depth, median (m)", "10 m wind, median (m s⁻¹)", "Enhancement, mean ± sd (ppb)", "Maximum (ppb)", "Prior (ppb)"], rows))

    # ---- posterior multipliers
    frac = ev.groupby("case").transport_fraction.first()
    rows = []
    for case, label in CASES.items():
        s = par[par.case.eq(case)].set_index("parameter")
        near = (f"fuel {interval(s.loc['fuel_near'])}; other {interval(s.loc['other_near'])}" if "fuel_near" in s.index
                else interval(s.loc["anthro_near"]))
        rows.append([label, f"{int(ev[ev.case.eq(case) & ev.split.eq('training')].n.sum())}", f"{frac[case]:.2f}", near,
                     interval(s.loc["anthro_far"]), interval(s.loc["wetlands"]), interval(s.loc["fire"])])
    t["J_PARAM_TABLE"] = ("**Table 5. Posterior emission multipliers by inversion case.** Posterior medians with 95% credible intervals; unity reproduces the prior. Near field is anthropogenic emission within 500 km of the observing tower and far field beyond 500 km; the sector split reports fuel exploitation and all other near-field sectors separately. Fitted hours count both towers. The transport-error fraction is tuned for a training reduced chi-square of one and capped at 1.0.\n\n"
        + markdown_table(["Case", "Fitted hours", "Transport fraction", "Near field", "Far field", "Wetlands", "Fires"], rows))
    S = {c: par[par.case.eq(c)].set_index("parameter") for c in CASES}
    t.update(J_FRAC_BKT=f"{frac['bkt_only']:.2f}", J_FRAC_JMB=f"{frac['jmb_only']:.2f}", J_FRAC_JOINT=f"{frac['joint']:.2f}", J_FRAC_SCREENED=f"{frac['joint_screened']:.2f}")
    for case, short in (("bkt_only", "B"), ("joint", "A"), ("joint_screened", "S")):
        for p, k in (("anthro_near", "NEAR"), ("anthro_far", "FAR"), ("wetlands", "WET"), ("fire", "FIRE")):
            t[f"J_{short}_{k}"] = interval(S[case].loc[p])
    for p, k in (("fuel_near", "FUEL"), ("other_near", "OTHER"), ("anthro_far", "FAR"), ("wetlands", "WET"), ("fire", "FIRE")):
        t[f"J_SEC_{k}"] = interval(S["joint_screened_sector"].loc[p])
    t["J_SEC_OTHER_P"] = f"{S['joint_screened_sector'].loc['other_near', 'probability_above_inventory']:.2f}"
    pf = S['joint_screened_sector'].loc['fuel_near', 'probability_above_inventory']
    t["J_SEC_FUEL_P"] = "below 0.001" if pf < .001 else f"{pf:.3f}"
    for p, k in (("anthro_near", "NEAR"), ("anthro_far", "FAR"), ("wetlands", "WET")):
        t[f"J_2019_{k}"] = interval(old.loc[p])
    overlap = all(max(S["bkt_only"].loc[p, "q025"], old.loc[p, "q025"]) <= min(S["bkt_only"].loc[p, "q975"], old.loc[p, "q975"])
                  for p in ("anthro_near", "anthro_far", "wetlands"))
    below = all(S["bkt_only"].loc[p, "median"] < 1 and old.loc[p, "median"] < 1 for p in ("anthro_near", "anthro_far", "wetlands"))
    t["J_2019_VERDICT"] = ("All three medians are below unity in both periods and each pair of 95% intervals overlaps." if overlap and below else
                           "All three medians are below unity in both periods, but not every pair of 95% intervals overlaps." if below else
                           "The two periods do not agree in direction for every component.")
    t["J_FIRE_PRIOR"] = f"{op[op.transport_usable].fire_ppb.mean():.1f}"

    # ---- evaluation
    def e(case, station, split="evaluation"):
        return ev[ev.case.eq(case) & ev.station.eq(station) & ev.split.eq(split)].iloc[0]
    rows = []
    for case, station, label in (("bkt_only", "BKT", "BKT only"), ("joint", "BKT", "Joint, all hours"), ("joint", "JMB", "Joint, all hours"),
                                 ("joint_screened", "BKT", "Joint, Jambi 18 UTC excluded"), ("joint_screened", "JMB", "Joint, Jambi 18 UTC excluded"),
                                 ("joint_screened_sector", "BKT", "Joint screened, sector split"), ("joint_screened_sector", "JMB", "Joint screened, sector split"),
                                 ("bkt_to_jmb_day", "JMB", "BKT-only multipliers, Jambi 06 UTC hours")):
        p, b, i = e(case, station), e(case + "_background_only", station), e(case + "_prior_inventory", station)
        rows.append([label, T.STATIONS[station][0], str(int(p.n)), f"{p.rmse_ppb:.1f} ({p.bias_ppb:+.1f})",
                     f"{b.rmse_ppb:.1f} ({b.bias_ppb:+.1f})", f"{i.rmse_ppb:.1f} ({i.bias_ppb:+.1f})"])
    t["J_EVAL_TABLE"] = ("**Table 6. Evaluation on hours the fit did not use: RMSE in ppb with mean bias in parentheses.** Withheld hours are complete days fixed before fitting; the last row applies multipliers fitted at BKT alone to every usable Jambi 06 UTC hour. Background only refits the per-receptor offset and trend with source multipliers at zero; prior inventory uses unit multipliers.\n\n"
        + markdown_table(["Case", "Evaluated at", "n", "Posterior", "Background only", "Prior inventory"], rows))
    sb, sbb = e("joint_screened", "BKT"), e("joint_screened_background_only", "BKT")
    sj, sjb = e("joint_screened", "JMB"), e("joint_screened_background_only", "JMB")
    tr, trb, tri = e("bkt_to_jmb_day", "JMB"), e("bkt_to_jmb_day_background_only", "JMB"), e("bkt_to_jmb_day_prior_inventory", "JMB")
    ab, abb = e("joint", "BKT"), e("joint_background_only", "BKT")
    t.update(J_SB_RMSE=f"{sb.rmse_ppb:.1f}", J_SB_BG=f"{sbb.rmse_ppb:.1f}", J_SJ_RMSE=f"{sj.rmse_ppb:.1f}", J_SJ_BG=f"{sjb.rmse_ppb:.1f}",
             J_SJ_N=str(int(sj.n)), J_SB_N=str(int(sb.n)), J_AB_RMSE=f"{ab.rmse_ppb:.1f}", J_AB_BG=f"{abb.rmse_ppb:.1f}",
             J_TR_N=str(int(tr.n)), J_TR_RMSE=f"{tr.rmse_ppb:.1f}", J_TR_BG=f"{trb.rmse_ppb:.1f}", J_TR_PRIOR=f"{tri.rmse_ppb:.1f}",
             J_TR_BIAS=f"{tr.bias_ppb:+.0f}", J_TR_BG_BIAS=f"{trb.bias_ppb:+.0f}", J_TR_PRIOR_BIAS=f"{tri.bias_ppb:+.0f}")
    both = sb.rmse_ppb < sbb.rmse_ppb and sj.rmse_ppb < sjb.rmse_ppb
    t["J_SCREENED_VERDICT"] = ("The screened joint fit predicts the withheld days better than a refitted background at both receptors." if both else
                               "The screened joint fit does not beat a refitted background at both receptors.")
    t["J_TRANSFER_VERDICT"] = ("Transferred multipliers remove most of the prior over-prediction but do not predict Jambi better than its endpoint background without a fitted Jambi offset: "
                               f"RMSE {tr.rmse_ppb:.1f} against {trb.rmse_ppb:.1f} ppb." if tr.rmse_ppb >= trb.rmse_ppb else
                               f"Transferred multipliers predict Jambi better than its endpoint background without a fitted Jambi offset: RMSE {tr.rmse_ppb:.1f} against {trb.rmse_ppb:.1f} ppb.")

    # ---- dataset availability
    def iso(v):
        v = str(v)
        return f"{v[:4]}-{v[4:6]}-{v[6:]}" if re.fullmatch(r"\d{8}", v) else v
    def sym(v): return str(v).replace("CH4", "CH₄").replace("CO2", "CO₂")
    rows = []
    for r in data.itertuples():
        period = (f"{iso(r.first)} to {iso(r.last)}" if pd.notna(r.first) and pd.notna(r.last) else
                  f"through {iso(r.last)}" if pd.notna(r.last) else "daily files, checked by year")
        rows.append([sym(r.product), sym(r.species), r.role, period, "yes" if r.covers_2023 else "no", "yes" if r.covers_2024 else "no"])
    t["J_DATA_TABLE"] = (f"**Table 7. Coverage of candidate input products, checked {data.checked_utc.iloc[0]}.** Directory listings, HTTP headers, zip central directories and netCDF headers only; no data arrays were transferred. A product covers a December when it contains that month.\n\n"
        + markdown_table(["Product", "Species", "Role", "Available period", "Covers Dec 2023", "Covers Dec 2024"], rows))
    d = data.set_index("product")
    edgar = d.loc["EDGAR_2025_GHG monthly CH4 fluxes"]; nrt = d.loc["CarbonTracker CT-NRT.v2025-1 molefractions"]
    ct25 = d.loc["CarbonTracker-CH4 2025 molefractions (used)"]; ct23 = d.loc["CarbonTracker-CH4 2023 molefractions"]
    t.update(J_EDGAR25_LAST=str(edgar["last"]), J_EDGAR25_MB=f"{edgar.transfer_mb_2023:.0f}", J_NRT_FIRST=str(nrt["first"]), J_NRT_LAST=str(nrt["last"]),
             J_NRT_CH4=str("methane variable present: True" in nrt.note), J_CT25_LAST=str(ct25["last"]), J_CT23_LAST=str(ct23["last"]),
             J_LEGACY_LAST=iso(d.loc["CarbonTracker-CH4 unversioned legacy tree", "last"]), J_EDGARV8_LAST=str(d.loc["EDGAR v8.0 monthly CH4 fluxes (used)", "last"]))
    if t["J_NRT_CH4"] != "False":
        raise ValueError("CT-NRT now reports a methane variable; revise the dataset section")
    return t


def peat_tokens() -> dict[str, str]:
    """Peatland and wet-versus-dry tests (a88). Each prose claim is checked against its table."""
    import a88_jambi_peat_tests as P
    t: dict[str, str] = {}
    def need(condition, claim):
        if not condition:
            raise ValueError(f"Peat section claim no longer holds: {claim}")
    prox = pd.read_csv(T.TABLES / "peat_proximity.csv").set_index("station")
    t.update(J_PEAT_POLYS=f"{int(prox.polygons.iloc[0]):,}", J_PEAT_AREA=f"{round(float(prox.mapped_peat_area_km2.iloc[0]), -3):,.0f}",
             J_JMB_PEAT_KM=f"{prox.loc['JMB', 'nearest_peat_km']:.1f}", J_JMB_PEAT10=f"{prox.loc['JMB', 'peat_share_10km_percent']:.0f}",
             J_JMB_PEAT25=f"{prox.loc['JMB', 'peat_share_25km_percent']:.0f}", J_JMB_PEAT50=f"{prox.loc['JMB', 'peat_share_50km_percent']:.0f}",
             J_BKT_PEAT_KM=f"{prox.loc['BKT', 'nearest_peat_km']:.0f}", J_BKT_PEAT100=f"{prox.loc['BKT', 'peat_share_100km_percent']:.1f}")
    need(not prox.loc["JMB", "inside_peat"] and prox.loc["JMB", "peat_share_25km_percent"] > 5 * prox.loc["BKT", "peat_share_100km_percent"], "Jambi is a peat site, BKT is not")
    hour = pd.read_csv(T.TABLES / "peat_summary_by_hour.csv").set_index(["station", "hour"])
    t.update(J_PEAT_SHARE_JMB_06=f"{hour.loc[('JMB', 6), 'peat_share_percent']:.0f}", J_PEAT_SHARE_JMB_18=f"{hour.loc[('JMB', 18), 'peat_share_percent']:.0f}",
             J_PEAT50_RATIO=f"{hour.loc[('JMB', 18), 'peat_sensitivity_50km'] / hour.loc[('JMB', 6), 'peat_sensitivity_50km']:.1f}")
    need(hour.loc[("JMB", 18), "peat_share_percent"] > hour.loc[("JMB", 6), "peat_share_percent"], "night samples more peat")
    cor = pd.read_csv(T.TABLES / "peat_correlations.csv").set_index(["station", "hour_utc", "target", "driver"])
    def r(hour_utc, target, driver): return cor.loc[("JMB", hour_utc, target, driver)]
    t.update(J_PEAT_N18=str(int(r(18, "enhancement_ppb", "peat_sensitivity").n)), J_PEAT_R18=f"{r(18, 'enhancement_ppb', 'peat_sensitivity').spearman:+.2f}",
             J_PEAT50_R18=f"{r(18, 'enhancement_ppb', 'peat_sensitivity_50km').spearman:+.2f}", J_PEAT_RES_R18=f"{r(18, 'residual_ppb', 'peat_sensitivity').spearman:+.2f}",
             J_PEAT_R06=f"{r(6, 'enhancement_ppb', 'peat_sensitivity').spearman:+.2f}", J_PEAT_N06=str(int(r(6, "enhancement_ppb", "peat_sensitivity").n)))
    need(r(18, "enhancement_ppb", "peat_sensitivity").spearman < .2 and r(18, "enhancement_ppb", "peat_sensitivity_50km").spearman < .2, "night enhancement does not rise with peat")
    need(r(18, "residual_ppb", "peat_sensitivity").spearman <= .1 and r(6, "enhancement_ppb", "peat_sensitivity").spearman < .2, "no positive peat relationship")
    col = pd.read_csv(T.TABLES / "peat_collinearity.csv").set_index(["station", "pair"])
    t["J_PEAT_WET_R"] = f"{col.loc[('JMB', 'peat_ppb~wetlands_ppb'), 'spearman']:.2f}"
    need(col.loc[("JMB", "peat_ppb~wetlands_ppb"), "spearman"] > .6, "peat and wetland responses overlap")
    t.update(J_PEAT_FREF=f"{P.F_REF * 1000:.0f}", J_PEAT_FACTOR=f"{P.PEAT_PRIOR_FACTOR:.0f}")
    par = pd.read_csv(T.TABLES / "peat_inversion_parameters.csv"); ev = pd.read_csv(T.TABLES / "peat_inversion_evaluation.csv")
    def prow(case, name): return par[par.case.eq(case) & par.parameter.eq(name)].iloc[0]
    def flux(case):
        q = prow(case, "peat"); return f"{q.flux_nmol_m2_s_median:.1f} (95% interval {q.flux_nmol_m2_s_q025:.2f}–{q.flux_nmol_m2_s_q975:.1f})"
    def erow(case, split): return ev[ev.case.eq(case) & ev.split.eq(split) & ev.station.eq("JMB")].iloc[0]
    prior = P.F_REF * 1000
    scr, allh = prow("screened_sector_peat", "peat"), prow("all_hours_sector_peat", "peat")
    t.update(J_PEAT_SCR_FLUX=flux("screened_sector_peat"), J_PEAT_ALL_FLUX=flux("all_hours_sector_peat"),
             J_PEAT_ALL_FRAC=f"{allh.transport_fraction:.2f}", J_PEAT_ALL_NIGHT_RMSE=f"{erow('all_hours_sector_peat', 'jmb_18utc_all').rmse_ppb:.0f}")
    need(scr.flux_nmol_m2_s_median < prior and scr.flux_nmol_m2_s_q975 / scr.flux_nmol_m2_s_q025 > 100, "screened peat flux below prior and wide")
    need(allh.transport_fraction >= .95 and abs(allh.flux_nmol_m2_s_median / prior - 1) < .25, "all-hours fit stays at cap and returns prior")
    for name in ("fuel_near", "other_near", "wetlands"):
        need(abs(prow("screened_sector_peat", name)["median"] - prow("screened_sector", name)["median"]) < .05, f"{name} unchanged by peat")
    need(abs(erow("screened_sector_peat", "evaluation").rmse_ppb - erow("screened_sector", "evaluation").rmse_ppb) < 5, "withheld error unchanged by peat")
    need(par.dropna(subset=["rhat"]).rhat.max() <= 1.01 and par.dropna(subset=["ess"]).ess.min() >= 1000, "peat fits converged")
    labels = {"screened_sector": "Jambi 18 UTC excluded, no peat", "screened_sector_peat": "Jambi 18 UTC excluded, with peat",
              "all_hours_sector_peat": "All hours, with peat", "jmb_all_hours_peat": "Jambi only, all hours, with peat"}
    rows = []
    for case, label in labels.items():
        c = par[par.case.eq(case)].set_index("parameter")
        near = (f"fuel {interval(c.loc['fuel_near'])}; other {interval(c.loc['other_near'])}" if "fuel_near" in c.index else interval(c.loc["anthro_near"]))
        peat = (f"{c.loc['peat', 'flux_nmol_m2_s_median']:.1f} ({c.loc['peat', 'flux_nmol_m2_s_q025']:.2f}–{c.loc['peat', 'flux_nmol_m2_s_q975']:.1f})"
                if "peat" in c.index else "not included")
        held, night = erow(case, "evaluation"), erow(case, "jmb_18utc_all")
        rows.append([label, f"{c.transport_fraction.dropna().iloc[0]:.2f}", peat, near, interval(c.loc["wetlands"]),
                     f"{held.rmse_ppb:.1f} (n={int(held.n)})", f"{night.rmse_ppb:.0f} ({night.bias_ppb:+.0f})"])
    t["J_PEAT_TABLE"] = ("**Table 9. Inversion with a uniform methane flux over mapped peat.** Posterior medians with 95% credible intervals; peat flux in nmol m⁻² s⁻¹. The Jambi withheld RMSE is on withheld days used by each case; the 18 UTC column is RMSE with mean bias (model minus observation) over every usable Jambi 18 UTC hour, in ppb. The Jambi-only case has no sector split.\n\n"
        + markdown_table(["Case", "Transport fraction", "Peat flux", "Near field", "Wetlands", "Jambi withheld RMSE (ppb)", "Jambi 18 UTC RMSE (bias)"], rows))
    # ---- seasons
    sig = pd.read_csv(T.ROOT / "outputs/p_ch4_co2_signature.csv").set_index("station").loc["JMB"]
    nights = pd.read_csv(T.TABLES / "jambi_night_rates.csv", parse_dates=["night"])
    need(int(nights.accumulating.sum()) == int(sig.n_nights), "nightly method reproduces the published count")
    t.update(J_F85_RATIO=f"{sig.ch4_per_co2_ppb_ppm:.2f}", J_F85_NIGHTS=str(int(sig.n_nights)),
             J_SEASON_FIRST=f"{nights.night.min():%-d %B %Y}", J_SEASON_LAST=f"{nights.night.max():%-d %B %Y}")
    summ = pd.read_csv(T.TABLES / "jambi_night_season_summary.csv").set_index(["definition", "season"])
    diff = pd.read_csv(T.TABLES / "jambi_night_season_difference.csv").set_index(["definition", "quantity"])
    def di(definition, q, digits):
        x = diff.loc[(definition, q)]; return f"{x.dry_minus_wet:+.{digits}f}, 95% interval {x.ci_lo:.{digits}f} to {x.ci_hi:.{digits}f}"
    t.update(J_CO2_WET=f"{summ.loc[('main', 'wet'), 'co2_rate_ppm_h_median']:.2f}", J_CO2_DRY=f"{summ.loc[('main', 'dry'), 'co2_rate_ppm_h_median']:.2f}",
             J_CH4_WET=f"{summ.loc[('main', 'wet'), 'ch4_rate_ppb_h_median']:.1f}", J_CH4_DRY=f"{summ.loc[('main', 'dry'), 'ch4_rate_ppb_h_median']:.1f}",
             J_RATIO_WET=f"{summ.loc[('main', 'wet'), 'ratio_ppb_per_ppm_median']:.2f}", J_RATIO_DRY=f"{summ.loc[('main', 'dry'), 'ratio_ppb_per_ppm_median']:.2f}",
             J_CO2_DIFF=di("main", "co2_rate_ppm_h", 2), J_CO2_DIFF_CORE=di("core", "co2_rate_ppm_h", 2),
             J_CH4_DIFF=di("main", "ch4_rate_ppb_h", 1), J_RATIO_DIFF=di("main", "ratio_ppb_per_ppm", 2),
             J_WET_NIGHTS=str(int(summ.loc[("main", "wet"), "accumulating_nights"])), J_DRY_NIGHTS=str(int(summ.loc[("main", "dry"), "accumulating_nights"])),
             J_WET_WEEKS=str(int(summ.loc[("main", "wet"), "weeks"])), J_DRY_WEEKS=str(int(summ.loc[("main", "dry"), "weeks"])))
    for d in ("main", "core"):
        need(diff.loc[(d, "co2_rate_ppm_h"), "ci_lo"] > 0, f"CO2 dry-season rise resolved ({d})")
    for q in ("ch4_rate_ppb_h", "ratio_ppb_per_ppm"):
        x = diff.loc[("main", q)]; need(x.dry_minus_wet < 0 and x.ci_lo < 0 < x.ci_hi, f"{q} lower when dry but unresolved")
    names = {"co2_rate_ppm_h": ("CO₂ build-up (ppm h⁻¹)", 2), "ch4_rate_ppb_h": ("CH₄ build-up (ppb h⁻¹)", 1), "ratio_ppb_per_ppm": ("CH₄:CO₂ ratio (ppb ppm⁻¹)", 2)}
    rows = []
    for q, (label, dg) in names.items():
        w, dr = summ.loc[("main", "wet")], summ.loc[("main", "dry")]
        cell = lambda row: f"{row[q + '_median']:.{dg}f} ({row[q + '_ci_lo']:.{dg}f} to {row[q + '_ci_hi']:.{dg}f})"
        m, c = diff.loc[("main", q)], diff.loc[("core", q)]
        rows.append([label, cell(w), cell(dr), f"{m.dry_minus_wet:+.{dg}f} ({m.ci_lo:.{dg}f} to {m.ci_hi:.{dg}f})",
                     f"{c.dry_minus_wet:+.{dg}f} ({c.ci_lo:.{dg}f} to {c.ci_hi:.{dg}f})"])
    t["J_SEASON_TABLE"] = (f"**Table 10. Nocturnal build-up at Jambi by season, full record.** Medians over nights on which CO₂ rises by more than 0.2 ppm per hour ({t['J_WET_NIGHTS']} wet-season nights in {t['J_WET_WEEKS']} weeks, {t['J_DRY_NIGHTS']} dry-season nights in {t['J_DRY_WEEKS']} weeks), with 95% week-block bootstrap intervals. Wet is November–April and dry May–October; the core columns compare December–March with June–September.\n\n"
        + markdown_table(["Quantity", "Wet, median (95%)", "Dry, median (95%)", "Dry minus wet (95%)", "Core dry minus wet (95%)"], rows))
    by = pd.read_csv(T.TABLES / "jambi_night_season_by_year.csv", parse_dates=["first", "last"])
    full = by[by.accumulating >= 50]
    need(full.loc[full.ratio_median.idxmin(), "season_label"] == "dry 2024" and full.loc[full.ratio_median.idxmax(), "season_label"] == "dry 2025", "dry seasons are the extremes")
    need(full.loc[full.ch4_rate_median.idxmin(), "season_label"] == "dry 2024" and full.loc[full.ch4_rate_median.idxmax(), "season_label"] == "dry 2025", "dry seasons are the methane extremes")
    rows = [[r.season_label.replace("wet", "Wet").replace("dry", "Dry"), f"{r.first:%-d %b %Y} to {r.last:%-d %b %Y}", str(int(r.accumulating)),
             f"{r.ratio_median:.2f}", f"{r.ch4_rate_median:.1f}", f"{r.co2_rate_median:.2f}"] for r in full.itertuples()]
    t["J_SEASON_YEAR_TABLE"] = ("**Table 11. Nocturnal build-up at Jambi by individual season.** Medians over accumulating nights; the incomplete 2025/26 wet season is omitted.\n\n"
        + markdown_table(["Season", "Nights from", "Accumulating nights", "CH₄:CO₂ (ppb ppm⁻¹)", "CH₄ build-up (ppb h⁻¹)", "CO₂ build-up (ppm h⁻¹)"], rows))
    alt = pd.read_csv(T.TABLES / "jambi_night_season_alt_method.csv").set_index(["definition", "season"]).loc[("main", "dry_minus_wet")]
    need(alt["median"] > 0 and alt.ci_lo < 0 < alt.ci_hi, "second method opposite in sign and unresolved")
    t["J_ALT_DIFF"] = f"{alt['median']:+.2f}, 95% interval {alt.ci_lo:.2f} to {alt.ci_hi:.2f}"
    return t


def build(write: bool = True) -> str:
    template = TEMPLATE.read_text()
    tok = tokens()
    tok.update(peat_tokens())
    missing = set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", template)) - tok.keys()
    if missing:
        raise ValueError(f"missing tokens {sorted(missing)}")
    text = renumber(re.sub(r"\{\{([A-Z0-9_]+)\}\}", lambda m: tok[m[1]], template))
    if "{{" in text or "—" in text:
        raise ValueError("unresolved token or em dash in rendered report")
    if write:
        (ROOT / f"{STEM}.md").write_text(text)
        (T.OUT / "report_tokens.json").write_text(json.dumps({k: v for k, v in tok.items() if "TABLE" not in k}, indent=2) + "\n")
        print(f"wrote {STEM}.md ({len(text.splitlines())} lines, {len(re.findall(r'[*][*]Figure ', text))} figures, {len(re.findall(r'[*][*]Table ', text))} tables)")
    return text


if __name__ == "__main__":
    build()
