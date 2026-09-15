#!/usr/bin/env python3
"""Build BKT_JMB_Two_Receptor_Report.md from its template and the a84/a87 evidence tables.

Every number in the prose is computed here from a CSV or JSON written by a84
(campaign, operator, inversion), a85 (figures) or a87 (dataset availability);
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


def build(write: bool = True) -> str:
    template = TEMPLATE.read_text()
    tok = tokens()
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
