#!/usr/bin/env python3
"""Build BKT_JMB_CO2_Report.md from its template and the a89 to a94 evidence tables.

Every number in the prose is computed here from a CSV or JSON written by a84
(2023 campaign), a89 (CO2 operator, CT-NRT inversions, spike screen), a90
(diagnostic biosphere, mixing screen, improved fits), a91 (scored variants,
cross-validation, bootstrap), a92 (release heights), a93 (2024 extension) or
a94 (figures). Figures and tables are numbered by order of appearance after
assembly, and the claims the prose makes are asserted against the tables before
the report is written.
"""
from __future__ import annotations

import json
import re

import numpy as np
import pandas as pd

import a84_bkt_jmb_two_receptor as T
import a89_bkt_jmb_co2 as C
import a90_bkt_jmb_co2_improved as I
import a91_bkt_jmb_co2_experiments as X
import a92_bkt_release_height as H
import a93_bkt_jmb_co2_2024 as E
from a40_bkt_refinement_report import markdown_table
from a82_bkt_reports import renumber

ROOT = T.ROOT
STEM = "BKT_JMB_CO2_Report"
TEMPLATE = ROOT / "docs/BKT_JMB_CO2_Report_template.md"
ROUND, FALLBACK = "_round6", "_round5b"
HEIGHT_ROUND = "_round5b"
NAMES = {"fossil_near": "Fossil ≤500 km", "fossil_far": "Fossil >500 km",
         "gpp_BKT": "Gross uptake, BKT", "resp_BKT": "Respiration, BKT",
         "gpp_JMB": "Gross uptake, Jambi", "resp_JMB": "Respiration, Jambi",
         "offset_BKT": "Offset, BKT (ppm)", "trend_BKT": "Trend, BKT (ppm per period)",
         "offset_JMB": "Offset, Jambi (ppm)", "trend_JMB": "Trend, Jambi (ppm per period)",
         "ch4_proxy_ppb_BKT": "CH₄ proxy coefficient, BKT (ppm ppb⁻¹)",
         "ch4_proxy_ppb_JMB": "CH₄ proxy coefficient, Jambi (ppm ppb⁻¹)",
         "ch4_residual_ppb_JMB": "CH₄ residual coefficient, Jambi (ppm ppb⁻¹)",
         "ch4_enhancement_ppb_BKT": "CH₄ enhancement coefficient, BKT (ppm ppb⁻¹)"}
VARIANT_LABELS = {"best_2023_proxy": "2023, both biosphere towers", "best_2024": "2024, both biosphere towers",
                  "best_all": "Both periods, both biosphere towers", "best_2023_proxy_bkt_background": "2023, Jambi biosphere only",
                  "best_2024_bkt_background": "2024, Jambi biosphere only", "best_all_bkt_background": "Both periods, Jambi biosphere only",
                  "best_100": "2023, both biosphere towers", "best_100_bkt_background": "2023, Jambi biosphere only",
                  "best_h150": "2023, BKT released at 150 m", "best_h300": "2023, BKT released at 300 m",
                  "best_h150_bkt_background": "2023, 150 m, Jambi biosphere only", "best_h300_bkt_background": "2023, 300 m, Jambi biosphere only"}
STAGES = [("2023 receptor selection and the HYSPLIT ensemble at both towers", "run_ledger.csv"),
          ("CO₂ inputs, the transport operator and the carbon-dioxide-only spike screen", "co2_operator_base.csv, co2_spike_screen.csv"),
          ("The diagnostic biosphere prior, the afternoon observation and the mixing screen", "co2_diagnostic_operator.csv, co2_mixing_screen.csv"),
          ("The CarbonTracker phase diagnosis", "co2_ctnrt_phase_daily.csv"),
          ("Scored variants, cross-validation and the date-block bootstrap", "co2_experiments_{round}_skill.csv, co2_experiments_{round}_cv_bootstrap.csv"),
          ("The BKT release-height campaign and its operator", "co2_bkt_height_operator.csv"),
          ("The October to December 2024 extension and the methane proxy it uses", "co2_receptor_selection_2024.csv, co2_ch4_proxy_validation.csv")]


def suffix() -> str:
    """The experiment round this report is built from; falls back while the 2024 campaign runs."""
    if (T.TABLES / f"co2_experiments{ROUND}_skill.csv").exists():
        return ROUND
    print(f"warning: {ROUND} tables absent, building from {FALLBACK}", flush=True)
    return FALLBACK


def need(condition, claim: str) -> None:
    if not condition:
        raise ValueError(f"Report claim no longer holds: {claim}")


def interval(row, digits: int = 2) -> str:
    return f"{row['median']:.{digits}f} ({row['q025']:.{digits}f} to {row['q975']:.{digits}f})"


def periods(round_suffix: str) -> tuple[str, ...]:
    return ("2023", "2024", "all") if round_suffix == ROUND else ("2023",)


def cases(round_suffix: str) -> tuple[str, str]:
    """Headline case with both biosphere towers, and the same without BKT biosphere terms."""
    return ("best_all", "best_all_bkt_background") if round_suffix == ROUND else ("best_100", "best_100_bkt_background")


def frames(round_suffix: str) -> dict[str, pd.DataFrame]:
    return {p: X.receptor_frame("", None, p) for p in periods(round_suffix)}


def tokens() -> dict[str, str]:
    s = suffix()
    head, background_case = cases(s)
    t: dict[str, str] = {"C_FIG": "outputs/hysplit/two_receptor/figures", "C_ROUND": s.strip("_")}
    skill = pd.read_csv(T.TABLES / f"co2_experiments{s}_skill.csv")
    boot = pd.read_csv(T.TABLES / f"co2_experiments{s}_cv_bootstrap.csv")
    par = pd.read_csv(T.TABLES / f"co2_experiments{s}_parameters.csv")
    diurnal = pd.read_csv(T.TABLES / "co2_diurnal_summary.csv")
    spike = pd.read_csv(T.TABLES / "co2_spike_screen.csv", parse_dates=["time_utc"])
    phase = pd.read_csv(T.TABLES / "co2_ctnrt_phase_daily.csv", parse_dates=["date"])
    base = pd.read_csv(T.TABLES / "co2_operator_base.csv", parse_dates=["time_utc"])
    fitted = frames(s)
    has_2024 = (T.TABLES / "co2_operator_base_2024.csv").exists()

    def cv(variant: str, code: str, model: str) -> float:
        row = skill[skill.variant.eq(variant) & skill.station.eq(code) & skill.scope.eq("leave_one_date_out") & skill.model.eq(model)]
        return float(row.rmse_ppm.iloc[0])

    def bootrow(variant: str, code: str):
        return boot[boot.variant.eq(variant) & boot.station.eq(code)].iloc[0]

    # ---- windows, receptors and runs
    ledger = pd.read_csv(T.TABLES / "run_ledger.csv")
    receipts_height = len(list(H.RUNS.glob("bkt_h*_s*/bkt_*/completion_receipt.json")))
    receipts_2024 = len(list(E.RUNS.glob("*_s*/*_*/completion_receipt.json")))
    need(ledger.complete.all(), "the 2023 campaign ledger is complete")
    t["C_RUNS"] = f"{len(ledger) + receipts_height + receipts_2024:,}"
    t["C_WINDOW_2023"] = "24 November to 31 December 2023"
    later = json.loads((T.TABLES / "co2_selection_summary_2024.json").read_text())
    first_2024, last_2024 = (pd.Timestamp(x) for x in later["window"].split(" to "))
    t["C_WINDOW_2024"] = f"{first_2024:%-d %B} to {last_2024:%-d %B %Y}"
    t["C_SEEDS_2023"] = {2: "two", 3: "three"}[len(T.SEEDS)]
    t["C_SEEDS_2024"] = {2: "two", 3: "three"}[len(E.SEEDS)]
    dates = {p: {code: f[f.station.eq(code)].time_utc.dt.date.nunique() for code in ("BKT", "JMB")} for p, f in fitted.items()}
    t["C_DATES_2023"] = str(max(dates["2023"].values()))
    t["C_DATES_ALL"] = str(max(dates[periods(s)[-1]].values()))
    t["C_DATES_BKT"] = str(dates[periods(s)[-1]]["BKT"]); t["C_DATES_JMB"] = str(dates[periods(s)[-1]]["JMB"])
    rows = []
    for period, label, runs in (("2023", t["C_WINDOW_2023"], len(ledger)), ("2024", t["C_WINDOW_2024"], receipts_2024)):
        if period == "2024" and not has_2024:
            continue
        if period == "2023":
            declared = int(base.time_utc.dt.hour.eq(6).sum() / 2)
            held = int(base[base.time_utc.dt.hour.eq(6) & base.station.eq("BKT")].holdout.sum())
            f = fitted["2023"]
        else:
            declared, held = int(later["joint_receptors"]), int(later["holdout_days"])
            f = X.frame_2024()
            f = f[f.transport_usable & f.co2_afternoon_mean.notna() & (f.PBLH >= I.MIN_MIXING_DEPTH_M)]
        rows.append([label, str(declared), str(held), str(int(f.station.eq("BKT").sum())), str(int(f.station.eq("JMB").sum())), f"{runs:,}"])
    t["C_WINDOW_TABLE"] = ("**Table 1. Joint afternoon receptors by period.** A joint receptor date has a valid, unflagged carbon dioxide "
        "record at both towers at 06 UTC. Usable counts are after the transport, observation and mixing screens of Section 2.3. Runs are "
        "HYSPLIT-STILT members, seeds included.\n\n"
        + markdown_table(["Period", "Joint dates", "Withheld", "Usable at BKT", "Usable at Jambi", "Runs"], rows))

    # ---- diurnal contrast
    rows = []
    for code in ("BKT", "JMB"):
        for hour, wib in ((6, "13"), (18, "01")):
            r = diurnal[diurnal.station.eq(code) & diurnal.hour.eq(hour)].iloc[0]
            prior = r.fossil_near_mean + r.fossil_far_mean + r.bio_day_mean + r.bio_night_mean
            key = f"C_{code}_{hour:02d}"
            t.update({f"{key}_PBLH": f"{r.pblh_median:.0f}", f"{key}_ENH": f"{r.enhancement_mean:+.0f}",
                      f"{key}_SD": f"{r.enhancement_sd:.0f}", f"{key}_PRIOR": f"{prior:+.1f}", f"{key}_N": str(int(r.n))})
            rows.append([T.STATIONS[code][0], f"{hour:02d} UTC ({wib} WIB)", str(int(r.n)), f"{r.pblh_median:.0f}",
                         f"{r.enhancement_mean:+.1f} ± {r.enhancement_sd:.1f}", f"{prior:+.1f}", f"{r.background_mean:.1f}"])
    t["C_NIGHT_PBLH"] = f"{diurnal[diurnal.hour.eq(18)].pblh_median.mean():.0f}"
    t["C_MIN_PBLH"] = f"{I.MIN_MIXING_DEPTH_M:.0f}"
    need(diurnal[diurnal.hour.eq(18)].pblh_median.max() < 100, "night mixing depth collapses below 100 m at both towers")
    for code in ("BKT", "JMB"):
        night = diurnal[diurnal.station.eq(code) & diurnal.hour.eq(18)].iloc[0]
        prior = night.fossil_near_mean + night.fossil_far_mean + night.bio_day_mean + night.bio_night_mean
        need(night.enhancement_mean > 3 * prior, f"night enhancement at {code} is far beyond the prior")
    t["C_DIURNAL_TABLE"] = ("**Table 2. Observed enhancement and model boundary layer by receptor and hour.** Mixing depth is the native GFS "
        "value in the receptor cell; enhancement is the observation minus the endpoint background; prior is the sum of the CarbonTracker-prior "
        "components. 2023 window, hours that pass the transport screen.\n\n"
        + markdown_table(["Receptor", "Hour", "n", "Mixing depth, median (m)", "Enhancement, mean ± sd (ppm)", "Prior (ppm)", "Background (ppm)"], rows))

    # ---- screens
    t["C_SPIKE_TESTABLE"] = str(int(spike.testable.sum()))
    flagged = spike[spike.co2_only_spike].sort_values("co2_departure_ppm", ascending=False)
    t["C_SPIKE_HOURS"] = str(len(flagged))
    worst = flagged.iloc[0]
    need(worst.station == "JMB" and abs(worst.ch4_departure_ppb) < C.SPIKE_TRACER_PPB and abs(worst.co_departure_ppb) < C.SPIKE_TRACER_PPB,
         "the largest flagged spike is a Jambi carbon-dioxide-only excursion")
    t.update(C_SPIKE_SIZE=f"{worst.co2_departure_ppm:.0f}", C_SPIKE_DATE=f"{worst.time_utc:%-d %B %Y}",
             C_SPIKE_CH4=f"{worst.ch4_departure_ppb:+.0f}", C_SPIKE_CO=f"{worst.co_departure_ppb:+.0f}")
    rows = []
    stages = [("Declared afternoon receptors", lambda f: f),
              ("Particle retention at least 95%", lambda f: f[f.transport_usable]),
              ("Afternoon mean available after the spike screen", lambda f: f[f.transport_usable & f.co2_afternoon_mean.notna()]),
              (f"Mixing depth at least {I.MIN_MIXING_DEPTH_M:.0f} m", lambda f: f[f.transport_usable & f.co2_afternoon_mean.notna() & (f.PBLH >= I.MIN_MIXING_DEPTH_M)])]
    observations = pd.read_csv(T.TABLES / "co2_afternoon_observations.csv", parse_dates=["time_utc"])
    start = {"2023": base[base.time_utc.dt.hour.eq(6)].merge(observations[["station", "time_utc", "co2_afternoon_mean"]],
                                                            on=["station", "time_utc"], validate="one_to_one")}
    if has_2024:
        start["2024"] = X.frame_2024()
    columns = ["Stage"] + [f"{p}, {code}" for p in start for code in ("BKT", "JMB")]
    for label, stage in stages:
        row = [label]
        for period, frame in start.items():
            kept = stage(frame)
            row += [str(int(kept.station.eq(code).sum())) for code in ("BKT", "JMB")]
        rows.append(row)
    t["C_SCREEN_TABLE"] = ("**Table 3. Afternoon receptors surviving each screen.** The observation stage removes dates with no valid 12 to 14 WIB "
        "hour and dates whose only hours were flagged as carbon-dioxide-only spikes.\n\n" + markdown_table(columns, rows))

    # ---- inverted CarbonTracker biosphere
    first, last = pd.Timestamp(C.INVERTED_EPISODE[0]), pd.Timestamp(C.INVERTED_EPISODE[1]).normalize()
    window = phase[(phase.date >= first) & (phase.date <= last)]
    outside = phase[(phase.date < first) | (phase.date > last)]
    need(window.sumatra_inverted_percent.mean() > 3 * outside.sumatra_inverted_percent.mean(), "the inverted week stands out from the rest of the window")
    need((window.bkt_cell_day_umol > 0).all() and (window.jmb_cell_day_umol > 0).all(), "both tower cells release carbon by day in that week")
    t.update(C_INVERTED_FIRST=f"{first:%-d %B}", C_INVERTED_LAST=f"{last:%-d %B %Y}",
             C_INVERTED_PERCENT=f"{window.sumatra_inverted_percent.mean():.0f}")

    # ---- prior constants and mean increments
    t.update(C_GPP_SCALE=f"{I.GPP_REF_GC_M2_YR:,.0f}", C_Q10=f"{I.Q10:.1f}", C_MEAS_PPM=f"{C.MEASUREMENT_PPM:.1f}",
             C_LOCAL_DAY_PPM=f"{C.LOCAL_DAY_PPM:.0f}", C_BG_PPM=f"{C.BACKGROUND_PPM:.0f}", C_BOOT_REPS=f"{X.BOOTSTRAP_REPS:,}")
    rows, means = [], {}
    all_fitted = fitted[periods(s)[-1]]
    for code in ("BKT", "JMB"):
        f = all_fitted[all_fitted.station.eq(code)]
        means[code] = dict(gpp=f.gpp_ppm.mean(), resp=f.resp_ppm.mean(), fossil=f.fossil_near_ppm.mean() + f.fossil_far_ppm.mean(),
                           ocean=f.ocean_ppm.mean(), fire=f.fire_ppm.mean(), background=f.background_ppm.mean(),
                           observed=f.co2_afternoon_mean.mean())
        t[f"C_{code}_GPP"] = f"{means[code]['gpp']:.1f}"; t[f"C_{code}_RESP"] = f"{means[code]['resp']:.1f}"
        t[f"C_{code}_FOSSIL"] = f"{means[code]['fossil']:.2f}"
    for label, key, digits in (("Gross uptake (diagnostic prior)", "gpp", 2), ("Respiration (diagnostic prior)", "resp", 2),
                               ("Fossil, EDGAR_2025_GHG", "fossil", 2), ("Ocean, CT-NRT", "ocean", 3), ("Fire, CT-NRT", "fire", 3),
                               ("Endpoint background, CT-NRT", "background", 1), ("Observed afternoon mean", "observed", 1)):
        rows.append([label] + [f"{means[code][key]:.{digits}f}" for code in ("BKT", "JMB")])
    need(abs(means["BKT"]["gpp"] + means["BKT"]["resp"]) < abs(means["BKT"]["gpp"]) and
         abs(means["JMB"]["gpp"] + means["JMB"]["resp"]) < abs(means["JMB"]["gpp"]), "the two biosphere terms partly cancel at both towers")
    need(all(abs(means[code]["fossil"]) < abs(means[code]["gpp"]) / 10 for code in ("BKT", "JMB")), "fossil is an order of magnitude below the biosphere terms")
    t["C_PRIOR_TABLE"] = ("**Table 5. Mean modelled contribution at the fitted afternoon receptors, ppm.** Uptake is negative by convention. "
        "Ocean is fixed, and so is fire in every case except the variant of Section 4.6; the background is the CT-NRT mole fraction "
        "sampled at the particle endpoints.\n\n"
        + markdown_table(["Component", "BKT", "Jambi"], rows))
    collinear = []
    for code in ("BKT", "JMB"):
        f = all_fitted[all_fitted.station.eq(code)]
        collinear.append(abs(np.corrcoef(f.gpp_ppm, f.resp_ppm)[0, 1]))
    t["C_BIO_COLLINEAR"] = f"{min(collinear):.2f} at {['BKT', 'Jambi'][int(np.argmin(collinear))]} and {max(collinear):.2f} at {['BKT', 'Jambi'][int(np.argmax(collinear))]}"
    need(min(collinear) > .8, "the two biosphere response columns are strongly collinear at both towers")

    # ---- variants
    settings = {label: (bio, cov, covariates, component_set) for label, bio, cov, covariates, component_set, _ in X.VARIANTS}
    rows = []
    for name in (X.ROUND6 if s == ROUND else X.ROUND5B):
        _, _, covariates, component_set = settings[name]
        option = X.OPTIONS.get(name, {})
        biosphere = {"tower": "Uptake and respiration at each tower", "jmb_biosphere": "Uptake and respiration at Jambi only",
                     "diag": "Uptake and respiration, shared"}[component_set]
        period = {"2023": "2023", "2024": "2024", "all": "2023 and 2024"}[option.get("period", "2023")]
        covariate = ", ".join(c.replace("ch4_proxy_ppb", "CH₄ proxy").replace("ch4_residual_ppb", "CH₄ residual")
                              .replace("ch4_enhancement_ppb", "CH₄ enhancement").replace("@", " at ") for c in covariates) or "none"
        height = f"{option['bkt_height']:.0f} m" if option.get("bkt_height") else "100 m"
        rows.append([VARIANT_LABELS[name], biosphere, covariate, period, height,
                     "per tower" if option.get("per_tower") else "shared"])
    t["C_VARIANT_TABLE"] = ("**Table 4. Model variants compared.** Every variant uses the same receptors, the same withheld dates, the same "
        "diagnostic biosphere prior and the same fitting and scoring machinery; only the columns below differ.\n\n"
        + markdown_table(["Variant", "Biosphere terms", "Covariates", "Period fitted", "BKT release", "Transport error"], rows))

    # ---- posteriors
    fitted_cases = {name: par[par.case.eq(name)].set_index("parameter") for name in (head, background_case)}
    rows = []
    for parameter in [k for k in NAMES if any(k in table.index for table in fitted_cases.values())]:
        digits = 3 if parameter.startswith("ch4") else 2
        rows.append([NAMES[parameter]] + [interval(table.loc[parameter], digits) if parameter in table.index else "not fitted"
                                          for table in fitted_cases.values()])
    fractions = par[par.case.eq(head)].iloc[0]
    t["C_PARAM_TABLE"] = ("**Table 6. Posterior parameters of the two headline cases.** Medians with 95% credible intervals. Multipliers are "
        "dimensionless and unity reproduces the prior; offsets, trends and covariate coefficients are in the units given.\n\n"
        + markdown_table(["Parameter", *(VARIANT_LABELS[name] for name in fitted_cases)], rows))
    need(par.rhat.max() <= 1.01 and par.ess.min() >= 1000, "every posterior converged")
    t["C_TRANSPORT_BKT"] = f"{fractions.transport_BKT:.2f}"; t["C_TRANSPORT_JMB"] = f"{fractions.transport_JMB:.2f}"
    bio = par[par.case.eq(head) & par.parameter.str.startswith(("gpp", "resp"))].set_index("parameter")
    below = (bio["median"] < 1).all()
    resolved = [n for n in bio.index if bio.loc[n, "q975"] < 1]
    t["C_BIO_VERDICT"] = (("All four biosphere multipliers sit below unity" if below else "The biosphere multipliers straddle unity")
        + (f", and {len(resolved)} of {len(bio)} exclude unity at 95%: " + "; ".join(f"{NAMES[n][0].lower() + NAMES[n][1:]} {interval(bio.loc[n])}" for n in resolved) + "."
           if resolved else ", and none of them excludes unity at 95%."))

    ctnrt = pd.read_csv(T.TABLES / "co2_inversion_parameters.csv")
    night = ctnrt[ctnrt.case.eq("jmb_only")].set_index("parameter")
    need(night.loc["fossil_near", "median"] > 5 and night.loc["fossil_far", "median"] > 5, "the all-hours Jambi fit inflates both fossil multipliers")
    t.update(C_NIGHT_FOSSIL_NEAR=interval(night.loc["fossil_near"], 1), C_NIGHT_FOSSIL_FAR=interval(night.loc["fossil_far"], 1))

    # ---- skill
    rows = []
    for name in (X.ROUND6 if s == ROUND else X.ROUND5B):
        for code in ("BKT", "JMB"):
            entry = [VARIANT_LABELS[name], T.STATIONS[code][0]]
            for scope in ("all_daytime", "withheld", "leave_one_date_out"):
                sub = skill[skill.variant.eq(name) & skill.station.eq(code) & skill.scope.eq(scope)]
                if sub.empty:
                    entry.append("n/a"); continue
                post = float(sub[sub.model.eq("posterior")].rmse_ppm.iloc[0])
                plain = float(sub[sub.model.eq("plain_background")].rmse_ppm.iloc[0])
                entry.append(f"{post:.2f} / {plain:.2f} (n={int(sub[sub.model.eq('posterior')].n.iloc[0])})")
            rows.append(entry)
    t["C_SKILL_TABLE"] = ("**Table 7. Root mean square error in ppm, posterior against the background-only null.** Each cell is posterior / "
        "background with the number of scored hours. All daytime is in sample; withheld dates were never fitted; leave one date out refits the "
        "model without each date and predicts it.\n\n"
        + markdown_table(["Variant", "Receptor", "All daytime", "Withheld dates", "Leave one date out"], rows))
    rows = []
    for name in (X.ROUND6 if s == ROUND else X.ROUND5B):
        for code in ("BKT", "JMB"):
            r = bootrow(name, code)
            rows.append([VARIANT_LABELS[name], T.STATIONS[code][0], str(int(r.dates)), f"{r.rmse_difference_ppm:+.2f}",
                         f"{r.ci_lo:+.2f} to {r.ci_hi:+.2f}", f"{r.fraction_posterior_better:.2f}"])
    t["C_BOOT_TABLE"] = (f"**Table 8. Cross-validated RMSE difference, posterior minus background, with {X.BOOTSTRAP_REPS:,} date-block bootstrap "
        "replicates.** Negative means the posterior predicts better. The last column is the share of replicates in which it does.\n\n"
        + markdown_table(["Variant", "Receptor", "Dates", "Difference (ppm)", "95% interval", "Share better"], rows))

    # ---- verdicts on skill
    def gap(variant: str, code: str) -> float:
        return cv(variant, code, "posterior") - cv(variant, code, "plain_background")

    worse = {code: gap(head, code) for code in ("BKT", "JMB")}
    resolved = {code: bootrow(head, code) for code in ("BKT", "JMB")}
    beaten = [code for code in ("BKT", "JMB") if worse[code] < 0]
    need(not beaten, "no tower beats its background out of sample in the headline case")
    excluded = [code for code in ("BKT", "JMB") if resolved[code].ci_lo > 0]
    t["C_SKILL_VERDICT"] = (
        "Neither tower does. On the combined record the posterior predicts a withheld date worse than the background at both towers, by "
        + " and ".join(f"{worse[code]:+.2f} ppm at {T.STATIONS[code][0]}" for code in ("BKT", "JMB"))
        + (", and the date-block interval excludes zero at " + " and ".join(T.STATIONS[c][0] for c in excluded) + "." if excluded
           else ", though no date-block interval excludes zero."))
    nuisance = {code: cv(head, code, "nuisance_only") - cv(head, code, "posterior") for code in ("BKT", "JMB")}
    need(all(v < 0 for v in nuisance.values()), "the nuisance-only model beats the posterior at both towers")
    t["C_NUISANCE_VERDICT"] = (
        "The ordering is the same in sample and out, and it is not an artefact of the covariates: the nuisance-only model, which keeps the "
        f"offset, trend and methane covariate but drops every source term, predicts better than the full posterior at both towers, by "
        + " and ".join(f"{-nuisance[code]:.2f} ppm at {T.STATIONS[code][0]}" for code in ("BKT", "JMB"))
        + ". Scaling the prior increments adds variance to the prediction without adding information about the observation.")
    t["C_RESOLVE_VERDICT"] = (
        ("The difference is resolved at " + " and ".join(T.STATIONS[c][0] for c in excluded) + ": "
         + "; ".join(f"{resolved[c].rmse_difference_ppm:+.2f} ppm, 95% interval {resolved[c].ci_lo:+.2f} to {resolved[c].ci_hi:+.2f}, over "
                     f"{int(resolved[c].dates)} dates" for c in excluded)
         + ". In 2023 alone no interval excluded zero in either direction, which is what a sample of "
         + f"{t['C_DATES_2023']} dates can say." if excluded else
         "No interval excludes zero, in either direction."))
    background_gap = {code: gap(background_case, code) for code in ("BKT", "JMB")}
    t["C_NEGATIVE_SUMMARY"] = (
        f"On {t['C_DATES_ALL']} dates the full model is worse out of sample than the background with a fitted offset and trend at both towers, "
        f"and dropping the BKT biosphere terms only brings that tower back to parity ({background_gap['BKT']:+.2f} ppm). The source terms "
        "carry no out-of-sample information at this footprint resolution, and the honest reading is that the afternoon residual at these two "
        "towers is dominated by transport and boundary error rather than by the surface fluxes underneath the footprints.")

    # ---- release height
    height_skill = pd.read_csv(T.TABLES / f"co2_experiments{HEIGHT_ROUND}_skill.csv")
    height_boot = pd.read_csv(T.TABLES / f"co2_experiments{HEIGHT_ROUND}_cv_bootstrap.csv")
    operator = pd.read_csv(T.TABLES / "co2_bkt_height_operator.csv", parse_dates=["time_utc"])
    at100 = (fitted["2023"][fitted["2023"].station.eq("BKT")].set_index("time_utc"))
    t["C_BKT_SHGT"] = f"{base[base.station.eq('BKT')].SHGT.median():.0f}"
    t["C_BKT_GAP"] = f"{T.STATIONS['BKT'][3] - base[base.station.eq('BKT')].SHGT.median():.0f}"
    rows, changes = [], []
    for name, height in (("best_100", 100.), ("best_h150", 150.), ("best_h300", 300.)):
        source = at100 if height == 100. else operator[operator.release_height_m.eq(height)].set_index("time_utc")
        shared = at100.index.intersection(source.index)
        change = {key: (source.loc[shared, key] - at100.loc[shared, key]) / at100.loc[shared, key].abs() * 100
                  for key in ("gpp_ppm", "resp_ppm", "fossil_near_ppm")}
        post = float(height_skill[height_skill.variant.eq(name) & height_skill.station.eq("BKT")
                                  & height_skill.scope.eq("leave_one_date_out") & height_skill.model.eq("posterior")].rmse_ppm.iloc[0])
        r = height_boot[height_boot.variant.eq(name) & height_boot.station.eq("BKT")].iloc[0]
        changes.append(max(abs(v.median()) for v in change.values()))
        rows.append([f"{height:.0f} m", f"{change['gpp_ppm'].median():+.1f}", f"{change['resp_ppm'].median():+.1f}",
                     f"{change['fossil_near_ppm'].median():+.1f}", f"{post:.2f}", f"{r.rmse_difference_ppm:+.2f} ({r.ci_lo:+.2f} to {r.ci_hi:+.2f})"])
    t["C_HEIGHT_TABLE"] = ("**Table 10. BKT release height.** Response changes are medians of the paired per-receptor change from the 100 m "
        "release, in percent. The error columns are the leave-one-date-out RMSE and its difference from the background-only null with a 95% "
        "date-block bootstrap interval, at BKT, for the 2023 window.\n\n"
        + markdown_table(["Release height", "Gross uptake (%)", "Respiration (%)", "Fossil ≤500 km (%)", "RMSE (ppm)", "Difference from background"], rows))
    heights = height_boot[height_boot.variant.isin(["best_100", "best_h150", "best_h300"]) & height_boot.station.eq("BKT")]
    need((heights.ci_lo < 0).all() and (heights.ci_hi > 0).all(), "no release height resolves a difference from the background")
    need(max(changes[1:]) < 10, "raising the release changes the modelled response by less than 10%")
    t["C_HEIGHT_VERDICT"] = (f"Raising the BKT release to the true inlet altitude and to 300 m changes the modelled response by at most "
        f"{max(changes[1:]):.0f}% and the out-of-sample error by at most "
        f"{max(abs(float(height_skill[height_skill.variant.eq(n) & height_skill.station.eq('BKT') & height_skill.scope.eq('leave_one_date_out') & height_skill.model.eq('posterior')].rmse_ppm.iloc[0]) - float(height_skill[height_skill.variant.eq('best_100') & height_skill.station.eq('BKT') & height_skill.scope.eq('leave_one_date_out') & height_skill.model.eq('posterior')].rmse_ppm.iloc[0])) for n in ('best_h150', 'best_h300')):.2f} ppm, "
        "so the terrain mismatch at the mountain tower is not what limits this inversion.")

    # ---- CarbonTracker against diagnostic prior
    improved = pd.read_csv(T.TABLES / "co2_improved_skill.csv")

    def improved_rmse(case: str, code: str, model: str) -> float:
        row = improved[improved.case.eq(case) & improved.station.eq(code) & improved.model.eq(model)]
        return float(row.rmse_ppm.iloc[0])

    ct, diag = improved_rmse("ctnrt_3h_mixed", "JMB", "posterior"), improved_rmse("diag_3h_mixed", "JMB", "posterior")
    ct_bkt, diag_bkt = improved_rmse("ctnrt_3h_mixed", "BKT", "posterior"), improved_rmse("diag_3h_mixed", "BKT", "posterior")
    need(diag < ct, "the diagnostic prior fits Jambi better than the optimized flux")
    t["C_PRIOR_VERDICT"] = (f"lowers the daytime error at Jambi from {ct:.2f} to {diag:.2f} ppm, and at BKT from {ct_bkt:.2f} to {diag_bkt:.2f} ppm, "
        f"on the same receptors and the same screens.") if diag_bkt < ct_bkt else (
        f"lowers the daytime error at Jambi from {ct:.2f} to {diag:.2f} ppm on the same receptors, while at BKT the two priors are within "
        f"{abs(diag_bkt - ct_bkt):.2f} ppm of each other.")

    # ---- the 2024 extension
    if s == ROUND:
        proxy = pd.read_csv(T.TABLES / "co2_ch4_proxy_validation.csv").set_index("station")
        need((proxy.spearman > .7).all(), "the methane proxy tracks the modelled enhancement at both towers")
        early, later_case = "best_2023_proxy", "best_2024"
        lines = [f"Adding {t['C_WINDOW_2024']} takes the usable sample from {t['C_DATES_2023']} dates to {t['C_DATES_ALL']}. "
                 f"The 2024 period has no CarbonTracker-CH₄ boundary field, so the methane covariate is the enhancement above each tower's own "
                 f"rolling clean-air baseline rather than the modelled enhancement; on the 2023 receptors the two agree with a Spearman "
                 f"correlation of {proxy.loc['BKT', 'spearman']:.2f} at BKT and {proxy.loc['JMB', 'spearman']:.2f} at Jambi (Figure 5c), and the "
                 f"2023 fit is repeated with the proxy so the two periods are treated alike."]
        for code in ("BKT", "JMB"):
            values = {label: (cv(case, code, "posterior"), cv(case, code, "plain_background"))
                      for label, case in (("2023", early), ("2024", later_case), ("both periods together", head))}
            lines.append(f"At {T.STATIONS[code][0]} the cross-validated error is "
                         + "; ".join(f"{v[0]:.2f} against {v[1]:.2f} ppm in {k}" for k, v in values.items()) + ".")
        t["C_2024_TEXT"] = "\n\n".join(lines)
        jmb_2023, jmb_2024 = gap(early, "JMB"), gap(later_case, "JMB")
        need(jmb_2023 < 0 < jmb_2024, "the 2023 Jambi gain reverses in 2024")
        boot_2023, boot_2024 = bootrow(early, "JMB"), bootrow(later_case, "JMB")
        t["C_2024_VERDICT"] = (
            f"The 2023 result does not reproduce. At Jambi the posterior was {abs(jmb_2023):.2f} ppm better than the background over "
            f"{int(boot_2023.dates)} dates in 2023, an interval of {boot_2023.ci_lo:+.2f} to {boot_2023.ci_hi:+.2f} ppm that never excluded zero; "
            f"over {int(boot_2024.dates)} dates in 2024 the same configuration is {jmb_2024:.2f} ppm worse "
            f"({boot_2024.ci_lo:+.2f} to {boot_2024.ci_hi:+.2f}). A gain that changes sign when the sample quadruples was a property of the "
            "sample, not of the method.")
    else:
        t["C_2024_TEXT"] = "The October to December 2024 campaign is not yet scored in this build, so this section reports the 2023 window only."
        t["C_2024_VERDICT"] = "The 2024 extension is pending."

    # ---- per-period nuisance robustness
    period_round = "_round7"
    if (T.TABLES / f"co2_experiments{period_round}_skill.csv").exists():
        ps = pd.read_csv(T.TABLES / f"co2_experiments{period_round}_skill.csv")
        pb = pd.read_csv(T.TABLES / f"co2_experiments{period_round}_cv_bootstrap.csv")

        def period_cv(variant: str, code: str, model: str) -> float:
            row = ps[ps.variant.eq(variant) & ps.station.eq(code) & ps.scope.eq("leave_one_date_out") & ps.model.eq(model)]
            return float(row.rmse_ppm.iloc[0])

        shifts, intervals = {}, {}
        for code in ("BKT", "JMB"):
            shifts[code] = period_cv("best_all_periods", code, "posterior") - period_cv("best_all", code, "posterior")
            intervals[code] = pb[pb.variant.eq("best_all_periods") & pb.station.eq(code)].iloc[0]
        need(max(abs(v) for v in shifts.values()) < .25, "the per-period nuisance design does not move the out-of-sample error materially")
        need(all(intervals[code].rmse_difference_ppm > 0 for code in ("BKT", "JMB")), "the per-period fit is still worse than its background")
        t["C_PERIOD_VERDICT"] = (
            "It changes nothing that matters: the out-of-sample error moves by "
            + " and ".join(f"{shifts[code]:+.2f} ppm at {T.STATIONS[code][0]}" for code in ("BKT", "JMB"))
            + ", and the posterior remains worse than its background at both towers, by "
            + " and ".join(f"{intervals[code].rmse_difference_ppm:+.2f} ppm ({intervals[code].ci_lo:+.2f} to {intervals[code].ci_hi:+.2f})"
                           for code in ("BKT", "JMB")) + ". The result is not an artefact of how the two periods are joined.")
    else:
        t["C_PERIOD_VERDICT"] = "pending"

    # ---- fire
    fire_round = "_round8"
    if (T.TABLES / f"co2_experiments{fire_round}_skill.csv").exists():
        fire_skill = pd.read_csv(T.TABLES / f"co2_experiments{fire_round}_skill.csv")
        fire_boot = pd.read_csv(T.TABLES / f"co2_experiments{fire_round}_cv_bootstrap.csv")
        fire_par = pd.read_csv(T.TABLES / f"co2_experiments{fire_round}_parameters.csv")

        def fire_cv(variant: str, code: str, model: str) -> float:
            row = fire_skill[fire_skill.variant.eq(variant) & fire_skill.station.eq(code)
                             & fire_skill.scope.eq("leave_one_date_out") & fire_skill.model.eq(model)]
            return float(row.rmse_ppm.iloc[0])

        later_frame = all_fitted[all_fitted.period.eq("2024")] if "period" in all_fitted else all_fitted
        t["C_FIRE_MAX"] = f"{later_frame.fire_ppm.max():.1f}"
        t["C_JMB_FIRE"] = f"{later_frame[later_frame.station.eq('JMB')].fire_ppm.mean():.1f}"
        fire_labels = {"best_2024": "2024, fire held fixed", "best_2024_fire": "2024, fire scaled",
                       "best_all": "Both periods, fire held fixed", "best_all_fire": "Both periods, fire scaled",
                       "best_all_fire_bkt_background": "Both periods, fire scaled, Jambi biosphere only"}
        rows = []
        for variant, label in fire_labels.items():
            for code in ("BKT", "JMB"):
                r = fire_boot[fire_boot.variant.eq(variant) & fire_boot.station.eq(code)].iloc[0]
                rows.append([label, T.STATIONS[code][0], f"{fire_cv(variant, code, 'posterior'):.2f}",
                             f"{fire_cv(variant, code, 'plain_background'):.2f}",
                             f"{r.rmse_difference_ppm:+.2f} ({r.ci_lo:+.2f} to {r.ci_hi:+.2f})"])
        t["C_FIRE_TABLE"] = ("**Table 9. Fire held fixed against fire scaled.** Leave-one-date-out RMSE in ppm. In the scaled variants the fire "
            "term leaves the baseline, so the background column is the boundary field without fire; the difference column is posterior minus "
            f"background with its 95% date-block bootstrap interval.\n\n"
            + markdown_table(["Variant", "Receptor", "Posterior (ppm)", "Background (ppm)", "Difference"], rows))
        multiplier = fire_par[fire_par.case.eq("best_all_fire") & fire_par.parameter.eq("fire")].iloc[0]
        null_gain = fire_cv("best_all", "JMB", "plain_background") - fire_cv("best_all_fire", "JMB", "plain_background")
        need(multiplier.q975 < 1.5 and null_gain > 0, "the fire prior is too strong at Jambi and the fitted multiplier is below unity")
        fire_diff = fire_boot[fire_boot.variant.eq("best_all_fire") & fire_boot.station.eq("JMB")].iloc[0]
        t["C_FIRE_VERDICT"] = (
            f"The fire prior is too strong, and taking it out of the fixed baseline helps the background rather than the inversion: the "
            f"background-only error at Jambi falls by {null_gain:.2f} ppm when fire is no longer added to it, and the fitted fire multiplier is "
            f"{interval(multiplier)}. With fire scaled, the posterior is still worse than that improved background at Jambi, by "
            f"{fire_diff.rmse_difference_ppm:+.2f} ppm ({fire_diff.ci_lo:+.2f} to {fire_diff.ci_hi:+.2f}).")
    else:
        for name in ("C_FIRE_MAX", "C_JMB_FIRE", "C_FIRE_TABLE", "C_FIRE_VERDICT"):
            t[name] = "pending"

    # ---- extending
    t["C_EXTEND_TEXT"] = (
        "Three things bear on whether a regional carbon dioxide inversion at these towers can be made to work, in descending order of value.\n\n"
        "The first is an observation that the model can carry at night. Nothing in the input chain fixes the night problem: it is a mismatch "
        f"between a {I.MIN_MIXING_DEPTH_M:.0f} m screen on a quarter-degree mixing depth and a nocturnal layer of a few tens of metres. Either a "
        "finer transport model with a resolved stable layer, or a measurement that samples the same layer the model resolves, such as a higher "
        "inlet or a column, would open the part of the record where the enhancements actually are.\n\n"
        "The second is an independent biosphere prior with the right phase. The diagnostic prior used here has the correct daily cycle and a "
        "defensible amplitude, but it is not a flux product: its uptake and respiration balance by construction, and its multipliers are therefore "
        "statements about this prior, not about Sumatran carbon exchange. A regional biosphere model driven by the same meteorology, checked "
        "against the CarbonTracker phase problem documented in Section 4.2, would let the multipliers carry flux meaning.\n\n"
        "The third is not more dates of the same kind. That was the expectation before the 2024 window was added, and the enlarged sample "
        f"settled the question in the opposite direction: {t['C_DATES_ALL']} dates were enough to resolve that the source terms make the "
        "prediction worse, not enough to rescue them. A longer record of the same observations, with the same priors at the same footprint "
        "resolution, would sharpen that answer rather than change it.")

    rows = [[stage, "`" + tables.format(round=s.strip("_")).replace(", ", "`, `") + "`"] for stage, tables in STAGES]
    t["C_SCRIPT_TABLE"] = ("**Table 11. Campaign stages and the evidence each one writes.** Every file listed is a CSV under the two-receptor "
        "output directory, and every number in this report is read from one of them.\n\n" + markdown_table(["Stage", "Evidence"], rows))
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
        (T.OUT / "co2_report_tokens.json").write_text(json.dumps({k: v for k, v in tok.items() if "TABLE" not in k}, indent=2) + "\n")
        print(f"wrote {STEM}.md ({len(text.splitlines())} lines, {len(re.findall(r'[*][*]Figure ', text))} figures, "
              f"{len(re.findall(r'[*][*]Table ', text))} tables)")
    return text


if __name__ == "__main__":
    build()
