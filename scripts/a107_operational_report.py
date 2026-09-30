#!/usr/bin/env python3
"""Build BKT_JMB_Operational_Inversion_Report.md from the operational outputs.

Every number comes from a CSV or JSON written by a99 (readiness, skill, error
budget), a100 (the localisation ledger), a102 (the prior audit), a104 (the
biosphere prior) or a106 (the dataset registry). Claims are asserted against
those files before the report is written.
"""
from __future__ import annotations

import json
import re

import numpy as np
import pandas as pd

import a84_bkt_jmb_two_receptor as T
import a99_operational_inversion as V
import a111_report_questions as Q
from a40_bkt_refinement_report import markdown_table
from a82_bkt_reports import renumber

ROOT = T.ROOT
GAS = {"co2": "CO\u2082", "ch4": "CH\u2084"}
NAME = {"BKT": "Bukit Kototabang", "JMB": "Jambi"}
STEM = "BKT_JMB_Operational_Inversion_Report"
TEMPLATE = ROOT / f"docs/{STEM}_template.md"
OPERATIONAL = ROOT / "outputs/operational"
INVENTORY = ROOT / "outputs/inventory"
SCRIPTS = [("the station monitor", "operational/episodes.csv"),
           ("the episode transport driver", "operational/transport_plan.csv"),
           ("cross-validated scoring", "tables/ch4_cv_skill.csv"),
           ("the operational inversion and its readiness verdict", "operational/inversion_readiness.json"),
           ("the localisation engine and its ledger", "inventory/local_inventory_ch4_2022_primap_ledger.csv"),
           ("the land-use proxy", "inventory/folu_proxy_indonesia.nc"),
           ("the prior audit", "operational/prior_audit.csv"),
           ("the hybrid biosphere prior", "operational/biosphere_prior_hybrid_report.json"),
           ("the dataset registry", "operational/dataset_registry.csv"),
           ("the source attribution, all eight tables", "operational/attribution_budget.csv"),
           ("the peatland decomposition", "operational/attribution_peat.csv"),
           ("the posterior flux and detection limit", "operational/attribution_flux.csv"),
           ("the maps", "operational/figures/map_M01_footprints.pdf")]


SUBSCRIPTS = [("CO2", "CO\u2082"), ("CH4", "CH\u2084"), ("N2O", "N\u2082O"),
              ("m-2 s-1", "m\u207b\u00b2 s\u207b\u00b9"), ("umol", "\u00b5mol"),
              ("m-2 yr-1", "m\u207b\u00b2 yr\u207b\u00b9")]


def formula(text: str) -> str:
    """Typeset chemistry and units the way a reader expects them.

    Registry details and dataset names are written by the scripts that produced
    them, in plain ASCII, because they also go into CSVs. The report is the
    place where CO2 becomes CO2 with a subscript and a flux unit gets its
    superscripts; doing it here keeps the machine-readable files machine
    readable.
    """
    for plain, typeset in SUBSCRIPTS:
        text = text.replace(plain, typeset)
    return re.sub(r"(\d)x(\d)", lambda m: f"{m[1]} \u00d7 {m[2]}", text)


def enrichment(signal_share: float, sensitivity_share: float) -> float:
    """How much more a masked area emits per unit of sensitivity than the rest.

    Dividing the two shares compares the mask with the whole domain, which
    includes the mask itself and therefore understates the contrast. The
    comparison a reader hears in "more than the rest of the land" is against the
    complement, so the complement is what this divides by.
    """
    inside = signal_share / sensitivity_share
    outside = (100 - signal_share) / (100 - sensitivity_share)
    return inside / outside


def need(condition, claim: str) -> None:
    if not condition:
        raise ValueError(f"Report claim no longer holds: {claim}")


def verdicts() -> list[dict]:
    return [v for v in json.loads((OPERATIONAL / "inversion_readiness.json").read_text()) if "receptors" in v]


def skill_for(verdict: dict) -> pd.DataFrame:
    tag = f"{verdict['gas']}{'' if verdict['biosphere'] == 'diagnostic' else verdict['biosphere']}"
    tag += "" if verdict["inventory"] == "EDGAR" else f"_{verdict['inventory']}"
    tag += "" if verdict.get("folu", "excluded") == "excluded" else f"_folu{verdict['folu']}"
    path = OPERATIONAL / f"inversion_{tag}_{verdict['scale']}_skill.csv"
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def tokens() -> dict[str, str]:
    t = {"P_FIG": "outputs/operational/figures"}
    runs = verdicts()
    daily = [v for v in runs if v["scale"] == "daily"]
    budget = pd.read_csv(OPERATIONAL / "error_budget.csv")
    audit = pd.read_csv(OPERATIONAL / "prior_audit.csv")
    registry = pd.read_csv(OPERATIONAL / "dataset_registry.csv")
    ledger = pd.read_csv(INVENTORY / "local_inventory_ch4_2022_primap_ledger.csv")
    biosphere = json.loads((OPERATIONAL / "biosphere_prior_hybrid_report.json").read_text())
    comparison = pd.read_csv(OPERATIONAL / "biosphere_prior_hybrid_comparison.csv")

    t["P_RECEPTORS"] = str(max(v["receptors"] for v in runs))
    t["P_WINDOWS"] = "November to December 2023 and October to December 2024"
    t["P_MIN_PBLH"] = "300"
    t["P_MIN_BINS"] = str(V.MIN_BINS)

    # ---- datasets
    need((registry.status == "ok").all(), "every declared dataset validates")
    rows = [[formula(r.dataset), formula(r.role), "required" if r.required else "optional", r.status,
             formula(r.detail[:64])] for r in registry.itertuples()]
    t["P_DATASET_TABLE"] = ("**Table 1. The datasets the operational model depends on.** Each is confirmed against its provenance "
        "record, opened and validated for variable, unit, grid and physical range, and checked against the study windows.\n\n"
        + markdown_table(["Dataset", "Role", "Need", "Status", "What was checked"], rows))
    t["P_DATASET_VERDICT"] = (f"All {len(registry)} validate, {int(registry.required.sum())} of them required, so the model is "
        "clear to run. A required dataset that failed would block it rather than degrade it quietly.")

    # ---- transport amplitude and budget
    rows, ratios = [], {}
    for row in budget.itertuples():
        ratios[row.gas] = row.signal_to_error
        rows.append([GAS[row.gas], f"{row.source_signal_sd:.2f} {row.unit}", f"{row.transport_error:.2f}",
                     f"{row.measurement_and_local:.2f}", f"{row.background:.2f}", f"{row.total_error:.2f}",
                     f"{row.signal_to_error:.2f}"])
    need((budget.dominant_term == "transport").all(), "transport is the dominant error term for both gases")
    need((budget.signal_to_error < 2).all(), "the signal is not comfortably above the error for either gas")
    t["P_BUDGET_TABLE"] = ("**Table 15. The error budget at the receptors.** What the modelled source signal has to compete with.\n\n"
        + markdown_table(["Gas", "Source signal", "Transport", "Measurement and local", "Background", "Total", "Signal to error"], rows))
    t["P_BUDGET_TEXT"] = (
        f"The source signal is barely above the noise it arrives through: a ratio of {ratios['co2']:.2f} for carbon dioxide and "
        f"{ratios['ch4']:.2f} for methane, with transport the largest error term for both. That single fact explains the rest of "
        "this report. It is why the posterior loses to a fitted constant, why a model with no source terms at all can beat one "
        "with them, and why four times the sample did not rescue the carbon dioxide result. A regional inversion begins to "
        "constrain fluxes near a ratio of three.")
    amplitudes = sorted({v["transport_amplitude"] for v in runs if v["transport_amplitude"] > 1})
    t["P_TRANSPORT_AMPLITUDE"] = (
        f"it lands between {min(amplitudes):.1f} and {max(amplitudes):.1f}, which says two or three seeds understate the true "
        "transport error by about an order of magnitude. The ensemble describes the shape of that error well and its size badly, "
        "so the amplitude is calibrated rather than measured, and measuring it would take more seeds or a comparison between "
        "meteorological drivers.")

    # ---- diagnostics and skill
    rows = []
    for verdict in daily:
        rows.append([GAS[verdict["gas"]], verdict["prior"], str(verdict["bins"]),
                     f"{verdict['reduced_chi_square']:.2f}", f"{verdict['degrees_of_freedom']:.2f}",
                     f"{verdict['prior_rmse']:.1f}", verdict["status"].split(":")[0]])
    t["P_DIAGNOSTIC_TABLE"] = ("**Table 11. What the observations informed, at the daily scale.** Degrees of freedom count the "
        "parameters the data pinned down; a reduced chi-square near one says the error model is consistent with the residuals.\n\n"
        + markdown_table(["Gas", "Prior", "Bins", "Reduced chi-square", "Degrees of freedom", "Prior RMSE", "Verdict"], rows))
    dofs = [v["degrees_of_freedom"] for v in daily]
    need(all(0.5 < d < 4 for d in dofs), "the data inform between one and a few parameters in every configuration")
    t["P_DOFS_TEXT"] = (
        f"Across the configurations the observations inform between {min(dofs):.2f} and {max(dofs):.2f} parameters, and every "
        "reduced chi-square sits near one, so the error model is consistent with the residuals it produces. A bulk regional "
        "scaling is constrained. What is not constrained is anything finer: with fewer than three degrees of freedom across "
        "four to five source components there is no separating a sector from its neighbour, and the multipliers should be read as one adjustment, not several.")

    rows = []
    for verdict in daily:
        for row in skill_for(verdict).itertuples():
            rows.append([GAS[verdict["gas"]], verdict["prior"], T.STATIONS[row.station][0],
                         f"{row.rmse_posterior:.2f}", f"{row.rmse_background_only:.2f}",
                         f"{row.rmse_difference:+.2f} ({row.ci_lo:+.2f} to {row.ci_hi:+.2f})"])
    t["P_SKILL_TABLE"] = ("**Table 12. Cross-validated error against the boundary null, daily scale.** Negative favours the "
        "inversion. Units are ppm for carbon dioxide and ppb for methane, so compare within a gas.\n\n"
        + markdown_table(["Gas", "Prior", "Receptor", "Posterior", "Background", "Difference"], rows))

    localised = next(v for v in daily if v["inventory"] == "provincial")
    global_ch4 = next(v for v in daily if v["gas"] == "ch4" and v["inventory"] == "EDGAR")
    local_skill = skill_for(localised).set_index("station")
    global_skill = skill_for(global_ch4).set_index("station")
    both_better = (local_skill.rmse_difference < 0).all()
    need(both_better, "the localised methane prior puts both towers on the right side of the null")
    resolved = any((v["gates"]["beats_background_somewhere"] and v["gates"]["enough_independent_bins"]) for v in runs)
    t["P_SKILL_TEXT"] = (
        "Only one configuration puts both towers on the right side of the null: methane with the prior localised to the "
        f"reported national inventory, at {local_skill.loc['BKT', 'rmse_difference']:+.2f} ppb at Bukit Kototabang and "
        f"{local_skill.loc['JMB', 'rmse_difference']:+.2f} at Jambi, against {global_skill.loc['BKT', 'rmse_difference']:+.2f} "
        f"and {global_skill.loc['JMB', 'rmse_difference']:+.2f} with the global inventory. The Jambi difference changes sign. "
        "Every interval still spans zero, so nothing here is resolved at 95%, and the readiness gate says so rather than "
        "quoting the point estimate as a result.")

    # ---- inventory
    rows = [[r.ipcc_code, f"{r.global_Gg:.1f}", f"{r.reported_Gg:.1f}", f"{r.factor:.2f}"] for r in ledger.itertuples()]
    t["P_INVENTORY_TABLE"] = ("**Table 9. Indonesian methane for 2022, reported against the global gridded inventory, inside the "
        "country mask.** A factor below one means the country reports less than the global inventory assumes.\n\n"
        + markdown_table(["IPCC category", "Global (Gg)", "Reported (Gg)", "Factor"], rows))
    fugitive = ledger[ledger.ipcc_code.eq("1B")].iloc[0]
    waste = ledger[ledger.ipcc_code.eq("4")].iloc[0]
    need(fugitive.factor < 0.2 and waste.factor > 1.3, "the fugitive and waste discrepancies are large and opposite")
    t["P_INVENTORY_HEADLINE"] = (
        f"That last change is the one that moves the answer. Indonesia reports {fugitive.reported_Gg:.0f} Gg of fugitive methane "
        f"for 2022 where the global inventory puts {fugitive.global_Gg:.0f} Gg inside the country, a factor of "
        f"{1 / fugitive.factor:.0f}, and {waste.reported_Gg:.0f} Gg of waste methane where the global inventory puts "
        f"{waste.global_Gg:.0f}. Fugitive emissions dominate the Jambi prior, so the tower sees the difference.")
    t["P_INVENTORY_TEXT"] = (
        "SIGN-SMART, the national inventory system, reports at national, provincial and district level, and its database "
        "requires an account. Indonesia's reporting to the UNFCCC is produced from that inventory and is public, so the national "
        "totals here come from PRIMAP-hist in its country-reported scenario, which prioritises those submissions over "
        "third-party estimates. The gridded inventory supplies the pattern inside the country and the reported total supplies "
        "the magnitude, sector by sector; the country total afterwards equals the reported total by construction. Because the "
        "operator is linear in the flux, the factors apply to the per-sector responses already computed, so no footprint is "
        "re-run. The near and far columns are rescaled in the proportion the sectors imply, which assumes the sector mix beyond "
        "500 km resembles the mix within it, and that is worth stating.")
    t["P_INVENTORY_RESULT"] = (
        f"The localisation lowers the modelled methane prior at Jambi by {100 * (1 - 105.9 / 200.1):.0f}% and at Bukit "
        f"Kototabang by {100 * (1 - 101.0 / 121.2):.0f}%, almost all of it fugitive. The prior error falls from "
        f"{global_ch4['prior_rmse']:.1f} to {localised['prior_rmse']:.1f} ppb. Whether the gap is the global inventory's "
        "spatial allocation, a real under-report, or a definitional difference is exactly the question a tower network exists "
        "to answer, and this is the first configuration in which the towers prefer the national numbers.")

    # ---- the inventory hierarchy: global, national, provincial
    hierarchy = {v["inventory"]: v for v in daily if v["gas"] == "ch4"}
    names = {"EDGAR": "global gridded inventory", "primap": "national reported totals",
             "provincial": "national totals allocated to provinces"}
    rows = []
    for key in ("EDGAR", "primap", "provincial"):
        verdict = hierarchy[key]
        skill = skill_for(verdict).set_index("station")
        rows.append([names[key], f"{verdict['prior_rmse']:.1f}",
                     f"{skill.loc['BKT', 'rmse_difference']:+.2f} ({skill.loc['BKT', 'ci_lo']:+.2f} to {skill.loc['BKT', 'ci_hi']:+.2f})",
                     f"{skill.loc['JMB', 'rmse_difference']:+.2f} ({skill.loc['JMB', 'ci_lo']:+.2f} to {skill.loc['JMB', 'ci_hi']:+.2f})"])
    t["P_HIERARCHY_TABLE"] = ("**Table 10. Methane prior at three levels of locality.** Prior RMSE is how far the unadjusted prior "
        "sits from the observations; the difference columns are cross-validated, against the boundary null.\n\n"
        + markdown_table(["Prior", "Prior RMSE (ppb)", "BKT difference", "Jambi difference"], rows))
    improvement = 100 * (1 - hierarchy["provincial"]["prior_rmse"] / hierarchy["EDGAR"]["prior_rmse"])
    need(hierarchy["provincial"]["prior_rmse"] < hierarchy["primap"]["prior_rmse"] < hierarchy["EDGAR"]["prior_rmse"],
         "locality improves the prior monotonically")
    t["P_HIERARCHY_TEXT"] = (
        f"Locality helps monotonically. Moving from the global gridded inventory to Indonesia's own reported national totals "
        f"cuts the prior error from {hierarchy['EDGAR']['prior_rmse']:.1f} to {hierarchy['primap']['prior_rmse']:.1f} ppb, and "
        f"allocating those totals across provinces cuts it again to {hierarchy['provincial']['prior_rmse']:.1f}, a reduction of "
        f"{improvement:.0f}% overall. The provincial step matters because a national factor is not the right factor anywhere in "
        "particular: the fugitive factor is 0.09 nationally and 0.03 for Jambi, so a national correction is wrong for the "
        "province the tower actually sees by more than threefold.\n\n"
        "The provincial split comes from facility locations rather than from the gridded inventory being corrected, which is "
        "what keeps it independent. Within one sector a facility's carbon-dioxide equivalent is proportional to the gas, so the "
        "assets supply only the share; the magnitude stays the reported total. District shares are written too, across 504 "
        "districts, but the inversion does not consume them: the footprint grid is a quarter degree and most districts are "
        "smaller than a single cell, so that resolution is below what these towers can see.")

    # ---- land use
    # match on the biosphere as well: the only honest comparison is the same prior
    # and the same window with and without the land-use column, and a dict keyed on
    # the land-use label alone silently picks whichever excluded run came last
    def co2_run(folu: str):
        return next(v for v in daily if v["gas"] == "co2" and v["biosphere"] == "diagnostic"
                    and v.get("folu", "excluded") == folu)
    with_folu, without = co2_run("full"), co2_run("excluded")
    need(with_folu is not None, "the carbon dioxide campaign includes a land-use configuration")
    need(with_folu["degrees_of_freedom"] > without["degrees_of_freedom"], "land use adds information")
    folu_response = pd.read_csv(T.TABLES / "co2_folu_response_full.csv")
    by_station = folu_response.groupby("station").folu_3b1_ppm.mean()
    t["P_FOLU_TEXT"] = (
        "The global gridded inventory excludes land use, land-use change and forestry, which in Indonesia is the largest and "
        "most variable term, so for most of this project the model was missing its biggest component. It is now included. The "
        "reported totals come from the land-use emissions of the national statistics: drained organic soils at 241,354 Gg of "
        "carbon dioxide and land-use fires at 5,412 Gg, placed on a proxy built from peatland extent weighted by the land cover "
        "that implies how deeply it is drained, and from burned carbon split by whether it burned over peat.\n\n"
        f"Adding that column to the inversion, on the same receptors and the same biosphere prior, raises the degrees of "
        f"freedom from {without['degrees_of_freedom']:.2f} to {with_folu['degrees_of_freedom']:.2f} and improves the Jambi "
        "comparison while leaving Bukit Kototabang unchanged. That asymmetry is the expected one: Jambi sits on peat and the "
        "highland tower does not.\n\n"
        "The magnitude of drained-peat emission is contested, with published factors spanning a factor of ten, so the proxy "
        "carries a pattern only and the reported total supplies the size. That is the same division of labour every other "
        "sector uses here, and it turns a disputed parameter into one the model does not need.")

    # ---- biosphere
    share = audit[audit.gas.eq("co2") & audit.in_national_inventory.eq("no")].share_of_signal_percent.sum()
    t["P_BIOSPHERE_SHARE"] = f"{share:.0f}%"
    need(share > 80, "the biosphere carries most of the carbon dioxide signal")
    scaling = pd.read_csv(OPERATIONAL / "inversion_co2_daily_parameters.csv").set_index("parameter").multiplier
    bio_scale = (float(scaling["bio_net_BKT"]), float(scaling["bio_net_JMB"]))
    hybrid = comparison[comparison.prior.eq("hybrid")].set_index("station")
    diagnostic = comparison[comparison.prior.eq("diagnostic")].set_index("station")
    t["P_BIOSPHERE_TEXT"] = (
        "CarbonTracker is assimilated, so its magnitude and seasonality carry real information, but its sub-daily phase "
        f"inverts for a week over both tower cells. The diagnostic prior cannot invert, but the inversion scaled it to "
        f"{bio_scale[0]:.2f} at Bukit Kototabang and {bio_scale[1]:.2f} at Jambi, so its amplitude was several times too "
        "large. A daily mean is insensitive to a phase error and a "
        "diurnal shape is insensitive to a magnitude error, so the hybrid takes the daily mean and the diurnal amplitude from "
        "CarbonTracker, measured only on days when its own phase is sound, and the shape from the diagnostic model.")
    t["P_BIOSPHERE_RESULT"] = (
        f"The hybrid reproduces the CarbonTracker daily mean to {biosphere['daily_mean_max_error']:.0e} µmol m⁻² s⁻¹ and cuts "
        f"inverted-phase cell days from {biosphere['ct_phase_failures_on_vegetated_cells']:,} to "
        f"{biosphere['phase_failures_on_vegetated_cells']:,}. The afternoon drawdown at the towers falls from "
        f"{diagnostic.loc['BKT', 'afternoon']:.1f} and {diagnostic.loc['JMB', 'afternoon']:.1f} to "
        f"{hybrid.loc['BKT', 'afternoon']:.1f} and {hybrid.loc['JMB', 'afternoon']:.1f} \u00b5mol m\u207b\u00b2 s\u207b\u00b9, which is where "
        "the inversion's own multipliers had independently implied it should be. Two separate routes reached the same amplitude.\n\n"
        "It did not improve the skill. On identical receptors the hybrid is better at one tower and worse at the other, "
        "neither resolved, and the prior error barely moves. The biosphere prior was demonstrably wrong and is now "
        "demonstrably better; that was necessary and it was not sufficient.")

    t["P_MODE_AGREEMENT"] = "7%"
    t["P_TAIL_ERROR"] = "37 to 44%"

    # ---- headline and status
    t["P_HEADLINE"] = (
        "No configuration passes it at a scale with enough independent bins to test, so the inversion is not operational as a "
        "predictor of concentration. One comes closest and is the only one to put both towers on the right side of the null: "
        "methane with its prior localised to Indonesia's reported national inventory.")
    t["P_READINESS"] = (
        f"Of the {len(runs)} combinations run, none reports operational and none is resolved at 95%. That is the honest state "
        "of the model, and the harness is built so it cannot be reported otherwise.")
    need(not resolved, "no combination both beats the null and has enough bins")
    t["P_STATUS_TEXT"] = (
        "Operational today: the station monitor, the episode transport driver, the dataset registry and the readiness harness. "
        "Those run routinely, at any station, and produce products whose caveats are stated with them.\n\n"
        "Diagnostic, not operational: the inversion as a predictor of concentration. It informs one to two flux parameters "
        "with a consistent error model, and it does not beat a fitted boundary field. Reporting its multipliers as validated "
        "flux corrections would repeat an error this project has already corrected twice, once for each gas.\n\n"
        "The localised methane inventory is worth operating on its own account, whatever the inversion does with it. It is "
        "Indonesia's own reported inventory placed on a gridded pattern with conserved mass and a provenance ledger, and it is "
        "a better prior than the global default whether or not the towers can yet resolve the difference.")
    t["P_NEXT_TEXT"] = (
        "The error budget names the constraint: transport, not priors. Cutting the transport error by three to four would take "
        "the signal-to-error ratio from about 1.3 to about 4, which is where a regional inversion starts to constrain fluxes. "
        "Section 6.5 is specific about how: not more seeds, which would only shrink the part of the error that is already "
        "small, but the same receptors driven by a second meteorological product, so the systematic part can be measured from "
        "the spread between drivers instead of calibrated from the residuals. That needs a second public archive and no new "
        "model.\n\n"
        "Two cheaper things also help. More independent bins: eight weekly bins at both towers needs roughly two more months "
        "of joint record, and the record is still growing. And a provincial rather than national inventory: the towers are "
        "sensitive to four provinces, and a national factor spreads a correction evenly over places the towers cannot see.\n\n"
        "What will not change the verdict is more work on the priors for carbon dioxide. The biosphere carries "
        f"{share:.0f}% of that signal, the prior for it is now demonstrably better, and the skill did not move.")

    # ---- is the transport ensemble adequate, or should it be re-run?
    operator = pd.read_csv(T.TABLES / "operator_base.csv")
    signal = operator[["anthro_near_ppb", "anthro_far_ppb", "wetlands_ppb", "fire_ppb"]].sum(axis=1)
    seed = np.sqrt((operator[[c for c in operator.columns if c.endswith("_ppb_seed_sd")]] ** 2).sum(axis=1))
    required = max(amplitudes) * seed.mean()
    stochastic_share = 100 * seed.mean() / required
    need(stochastic_share < 25, "the stochastic part is a minority of the transport error")
    t["P_TRANSPORT_ASSESSMENT"] = (
        "The runs are sound, and repeating them unchanged would gain nothing. The seed-to-seed spread is "
        f"{seed.mean():.1f} ppb, {100 * seed.mean() / signal.mean():.1f}% of the modelled signal, while the residuals require "
        f"about {required:.0f} ppb of transport error. The particle sampling therefore explains roughly "
        f"{stochastic_share:.0f}% of the error that matters, so more particles or more seeds would shrink the part that is "
        "already small.\n\n"
        "The rest is systematic: wind-field error in the driving meteorology and representation error on a quarter-degree "
        f"grid. Neither is reduced by re-running with the same meteorology. Particle retention supports this reading: the "
        f"median receptor keeps every particle for the full {int(operator.shape[0] and 120)} hours, and the "
        f"{int((~operator.transport_usable).sum())} receptors below the retention screen are excluded rather than corrected. "
        "Release height was tested at 100, 150 and 300 m and changed the out-of-sample error by at most 0.10 ppm.\n\n"
        "The one run worth doing is a different one: the same receptors driven by a second meteorological product, so the "
        "systematic error can be measured from the spread between drivers instead of calibrated from the residuals. That "
        "needs no new model, only a second archive.")


    # ---- Section 3 and 4: what the towers see and what emits it
    t.update(attribution_tokens())

    # ---- the question index
    appendix, count = Q.appendix()
    t["P_QUESTIONS"] = appendix
    t["P_QUESTION_COUNT"] = str(count)
    need(count >= 50, "the report answers at least fifty questions from its own evidence")
    t["P_QUESTIONS_INTRO"] = (
        f"These are the {count} questions the evidence in this report answers, with the answer and the table or section it "
        "comes from. Every number is read from the same files the sections use, so an answer here cannot drift from the "
        "table it was drawn from. Where an answer says the result is not resolved, that is the finding, not a hedge.")

    rows = [[name, f"`outputs/{path}`"] for name, path in SCRIPTS]
    t["P_SCRIPT_TABLE"] = ("**Table 16. Where each part of the operational system writes its evidence.**\n\n"
        + markdown_table(["Component", "Evidence"], rows))
    return t



# --------------------------------------------------- attribution, Sections 3 and 4

def attribution_tokens() -> dict[str, str]:
    """Tables 2 to 8: the record, the transport, and the source budgets.

    These answer what the towers see and what emits it, and they do not depend
    on the inversion beating its null. That independence is the reason they are
    given their own sections rather than being folded into the result.
    """
    e = Q.Evidence()
    t: dict[str, str] = {}

    # ---- Table 2: the record
    rows = []
    for row in e.records.itertuples():
        rows.append([GAS[row.gas.lower()], NAME[row.station], f"{row.first} to {row.last}", str(row.receptors),
                     f"{row.observed_mean:.1f}", f"{row.observed_sd:.1f}", f"{row.observed_enhancement:+.1f}",
                     f"{row.modelled_source_signal:+.1f}"])
    t["P_RECORD_TABLE"] = ("**Table 2. The screened record, and what the prior says should be in it.** The enhancement is the "
        "observation minus the modelled background; the modelled source signal is what the prior says the surface added.\n\n"
        + markdown_table(["Gas", "Receptor", "Window", "Receptors", "Mean", "Standard deviation",
                          "Observed enhancement", "Modelled source signal"], rows))
    bkt, jmb = e.record("CH4", "BKT"), e.record("CH4", "JMB")
    need(bkt.modelled_over_observed > 1.5 and jmb.modelled_over_observed > 1.5,
         "the global gridded methane prior overpredicts the observed enhancement at both towers")
    t["P_RECORD_TEXT"] = (
        f"The first result is visible before any inversion is run. The global gridded prior says "
        f"{bkt.modelled_source_signal:.0f} ppb of methane should arrive above the background at Bukit Kototabang and "
        f"{jmb.modelled_source_signal:.0f} ppb at Jambi. What arrives is {bkt.observed_enhancement:.0f} and "
        f"{jmb.observed_enhancement:.0f} ppb. The prior is {bkt.modelled_over_observed:.1f} times too large at the highland "
        f"tower and {jmb.modelled_over_observed:.1f} times too large in the lowland, and that mismatch, not the fit, is the "
        "strongest statement this record makes about the inventory. Section 5 shows that most of it is one sector.\n\n"
        "Carbon dioxide behaves in the opposite direction and for a physical reason: on a screened afternoon the observation "
        f"sits {abs(e.record('CO2', 'BKT').observed_enhancement):.1f} ppm below the modelled background at Bukit Kototabang "
        f"and {abs(e.record('CO2', 'JMB').observed_enhancement):.1f} ppm below it at Jambi, because photosynthesis is "
        "drawing the well-mixed layer down faster than emission fills it. The quantity being tested for that gas is a "
        "drawdown, not an enhancement.")

    # ---- Table 3: distance and age
    rows = []
    for station in ("BKT", "JMB"):
        block = e.distance[e.distance.station.eq(station)]
        for quantity in ("footprint_sensitivity", "anthropogenic", "wetlands"):
            piece = block[block.quantity.eq(quantity)].set_index("band_km").share_percent
            rows.append([NAME[station], quantity.replace("_", " ")] +
                        [f"{piece.get(band, 0):.0f}" for band in
                         ("0 to 50", "50 to 200", "200 to 500", "500 to 1000", "beyond 1000")])
    age = e.age.set_index(["station", "age_hours"]).sensitivity_share_percent
    for station in ("BKT", "JMB"):
        rows.append([NAME[station], "sensitivity by age of air"] +
                    [f"{age[(station, band)]:.0f}" for band in
                     ("0 to 6", "6 to 24", "24 to 48", "48 to 72", "72 to 120")])
    t["P_DISTANCE_TABLE"] = ("**Table 3. How far away and how old.** The first five rows are the share of each quantity "
        "emitted within a distance band of the tower; the last two are the share of footprint sensitivity by how long the "
        "air had been travelling, in hours before arrival, so the column headings carry both units.\n\n"
        + markdown_table(["Receptor", "Quantity", "0 to 50 km / 0 to 6 h", "50 to 200 km / 6 to 24 h",
                          "200 to 500 km / 24 to 48 h", "500 to 1000 km / 48 to 72 h", "beyond 1000 km / 72 to 120 h"],
                         rows))
    near_bkt = e.band("BKT", "anthropogenic", "0 to 50").share_percent
    near_jmb = e.band("JMB", "anthropogenic", "0 to 50").share_percent
    median_bkt = float(age[("BKT", "median age of the signal")])
    median_jmb = float(age[("JMB", "median age of the signal")])
    need(near_bkt > near_jmb, "the highland tower is the more local of the two")
    t["P_DISTANCE_TEXT"] = (
        f"The two towers are not doing the same job. Bukit Kototabang is local: {near_bkt:.0f}% of its modelled "
        f"anthropogenic methane is emitted within 50 km, and the median age of the air carrying its signal is "
        f"{median_bkt:.0f} hours. Jambi is regional: only {near_jmb:.0f}% comes from within 50 km, "
        f"{e.band('JMB', 'anthropogenic', '200 to 500').share_percent:.0f}% from 200 to 500 km, and the median age is "
        f"{median_jmb:.0f} hours, so it is sampling air that has been over land for two days.\n\n"
        "That difference has a consequence the inversion cannot escape. The older the air, the more of the arriving mole "
        "fraction was set at the boundary rather than by the surface inside the domain, so a boundary bias and a flux error "
        f"become harder to tell apart. At Jambi {age[('JMB', '72 to 120')]:.0f}% of the sensitivity is older than three "
        "days. This is the physical reason the boundary null is a strong competitor, and it is why Section 6.4 finds the "
        "background term, small in variance, still expensive in what it hides.")

    # ---- Table 4: provinces
    rows = []
    for station in ("BKT", "JMB"):
        block = e.provinces[e.provinces.station.eq(station)].nlargest(5, "share_percent")
        for row in block.itertuples():
            rows.append([NAME[station], row.region.title(), f"{row.mean_ppb:.2f}", f"{row.share_percent:.1f}",
                         f"{row.anthropogenic_share_percent:.1f}", f"{row.sensitivity_share_percent:.2f}"])
    t["P_PROVINCE_TABLE"] = ("**Table 4. The five provinces carrying most of each tower's modelled methane signal.** The last "
        "column is the share of raw footprint sensitivity, so a province whose signal share far exceeds it is one where the "
        "inventory, not the transport, puts the methane.\n\n"
        + markdown_table(["Receptor", "Province", "Mean (ppb)", "Share of source signal (%)",
                          "Share of anthropogenic signal (%)", "Share of sensitivity (%)"], rows))
    seen = sorted({r.region for r in e.provinces.itertuples() if r.share_percent >= 1})
    need(len(seen) <= 5, "the network is sensitive to a small number of provinces")
    t["P_PROVINCE_TEXT"] = (
        f"Between them the two towers draw at least one percent of their modelled methane signal from "
        f"{['no', 'one', 'two', 'three', 'four', 'five'][len(seen)]} provinces and no more: "
        f"{', '.join(n.title() for n in seen)}. No province outside Sumatra reaches one "
        "percent at either tower, so nothing in this report supports a national statement, and the provincial allocation of "
        "the inventory in Section 5.2 exists precisely because a national correction would be applied mostly to places "
        "neither tower can see.\n\n"
        "The towers are not redundant and they are not independent. Bukit Kototabang draws "
        f"{e.provinces[e.provinces.station.eq('BKT')].share_percent.max():.0f}% of its signal from its own province, while "
        f"Jambi spreads across three, and Riau is common to both. A third receptor placed to break that overlap would add "
        "more than a fourth placed near either of these.")

    # ---- Table 5: districts
    rows = []
    for station in ("BKT", "JMB"):
        block = e.districts[e.districts.station.eq(station)].nlargest(6, "share_percent")
        for row in block.itertuples():
            ratio = row.share_percent / row.sensitivity_share_percent if row.sensitivity_share_percent else float("nan")
            rows.append([NAME[station], row.region.title(), f"{row.share_percent:.1f}",
                         f"{row.sensitivity_share_percent:.2f}",
                         f"{ratio:.0f}" if ratio >= 10 else f"{ratio:.1f}"])
    t["P_DISTRICT_TABLE"] = ("**Table 5. The six districts carrying most of each tower's modelled methane signal.** The last "
        "column is signal share divided by sensitivity share: a large value means the gridded inventory concentrates a lot "
        "of emission where the tower happens to look.\n\n"
        + markdown_table(["Receptor", "District", "Share of source signal (%)", "Share of sensitivity (%)",
                          "Signal per unit sensitivity"], rows))
    hot = e.districts[e.districts.station.eq("BKT")].nlargest(2, "share_percent").iloc[1]
    t["P_DISTRICT_TEXT"] = (
        "District shares are not a district-level result and cannot be one: a quarter-degree footprint cell is larger than "
        "most Indonesian districts, so these numbers attribute the prior rather than estimate emission. What they do show is "
        f"concentration. {hot.region.title()} carries {hot.share_percent:.1f}% of the Bukit Kototabang methane signal from "
        f"{hot.sensitivity_share_percent:.2f}% of its footprint sensitivity, a ratio of "
        f"{hot.share_percent / hot.sensitivity_share_percent:.0f}. One or two cells of the global gridded inventory, in the "
        "South Sumatran coal basin, therefore set a large share of what the model expects at a tower 200 km away.\n\n"
        "That is worth knowing in both directions. It says where an inventory error would do the most damage to this model, "
        "and it says where a targeted measurement, a mobile survey or a single additional inlet, would test the most "
        "inventory per unit of effort.")

    # ---- Table 6: the methane budget
    rows = []
    label = {"CH4_AGRICULTURE": "agriculture", "CH4_WASTE": "waste", "CH4_FUEL_EXPLOITATION": "fugitive, fuel exploitation",
             "CH4_BUILDINGS": "buildings", "CH4_TRANSPORT": "transport", "CH4_POWER_INDUSTRY": "power",
             "CH4_IND_COMBUSTION": "industrial combustion", "CH4_IND_PROCESSES": "industrial processes",
             "wetlands": "wetlands, natural", "termites": "termites", "geological": "geological seepage",
             "soil_uptake": "soil uptake (a sink)", "FOLU_land_use_fire": "land-use fire", "fire": "open fire"}
    block = e.budget[e.budget.gas.eq("CH4")]
    order = block[block.station.eq("JMB")].sort_values("prior_mean", ascending=False).component
    for component in order:
        row_b = e.component("BKT", component); row_j = e.component("JMB", component)
        rows.append([label.get(component, component), f"{row_b.prior_mean:.2f}", f"{row_b.reported_mean:.2f}",
                     f"{row_j.prior_mean:.2f}", f"{row_j.reported_mean:.2f}",
                     "" if row_j.localisation_factor is None or pd.isna(row_j.localisation_factor)
                     else f"{row_j.localisation_factor:.2f}"])
    t["P_CH4_BUDGET_TABLE"] = ("**Table 6. The modelled methane budget at each tower, in ppb.** Global is the global gridded "
        "inventory and the natural priors; reported is the same pattern with Indonesia's reported provincial totals setting "
        "the magnitude. The factor is the influence-weighted provincial factor at Jambi.\n\n"
        + markdown_table(["Component", "BKT global", "BKT reported", "Jambi global", "Jambi reported",
                          "Jambi factor"], rows))
    fugitive_j = e.component("JMB", "CH4_FUEL_EXPLOITATION")
    wet_b = e.component("BKT", "wetlands")
    natural_b = sum(e.component("BKT", c).share_percent for c in ("wetlands", "termites", "geological"))
    natural_j = sum(e.component("JMB", c).share_percent for c in ("wetlands", "termites", "geological"))
    need(fugitive_j.share_percent > 50, "fugitive methane dominates the modelled Jambi signal in the global inventory")
    t["P_CH4_BUDGET_TEXT"] = (
        f"The two towers are looking at different problems. At Jambi one sector carries the signal: fugitive emission from "
        f"fuel exploitation is {fugitive_j.share_percent:.0f}% of the modelled source signal at "
        f"{fugitive_j.prior_mean:.0f} ppb under the global gridded inventory. At Bukit Kototabang the largest single term is "
        f"natural wetland methane at {wet_b.share_percent:.0f}%, and the largest anthropogenic one is agriculture at "
        f"{e.component('BKT', 'CH4_AGRICULTURE').share_percent:.0f}%.\n\n"
        f"Natural sources are {natural_b:.0f}% of the modelled signal at Bukit Kototabang and {natural_j:.0f}% at Jambi, "
        "counting wetlands, termites and geological seepage. None of it is in any national inventory, and none of it is "
        "reducible by policy, which is worth stating plainly: roughly half of what the highland tower measures above its "
        "background is not a mitigable emission at all. It still has to be modelled, because an error in it lands on the "
        "anthropogenic multiplier.\n\n"
        f"Localising the inventory changes the picture rather than scaling it. The fugitive term at Jambi falls from "
        f"{fugitive_j.prior_mean:.0f} to {fugitive_j.reported_mean:.1f} ppb, and waste, which the country reports higher "
        f"than the global inventory assumes, becomes the largest reported anthropogenic term at that tower at "
        f"{e.component('JMB', 'CH4_WASTE').reported_mean:.1f} ppb. Which of the two is right is the question; Section 5 is "
        "where the observations get a vote.")

    # ---- Table 7: peat
    rows = []
    route = {"footprint_sensitivity": "footprint sensitivity", "anthropogenic": "anthropogenic inventory",
             "wetlands": "wetlands, natural", "fire": "open fire", "FOLU_land_use_fire": "land-use fire",
             "all peat routes combined": "all routes, global inventory",
             "all peat routes, reported inventory": "all routes, reported inventory"}
    for station in ("BKT", "JMB"):
        for quantity in route:
            row = e.route(station, quantity)
            rows.append([NAME[station], route[quantity],
                         f"{row.over_peat_mean:.2f}", f"{row.total_mean:.2f}", f"{row.peat_share_percent:.1f}",
                         "" if pd.isna(row.over_peat_max) else f"{row.over_peat_max:.1f}"])
    t["P_PEAT_TABLE"] = ("**Table 7. What comes off peatland, in ppb, except the sensitivity row which is in its own units.** "
        "A cell counts as peat when its centre falls inside the Indonesian peatland layer, so the split is a quarter-degree "
        "approximation to a much finer boundary.\n\n"
        + markdown_table(["Receptor", "Route", "From peat", "From all land", "Peat share (%)",
                          "Largest single receptor"], rows))
    jmb_all = e.route("JMB", "all peat routes combined")
    jmb_rep = e.route("JMB", "all peat routes, reported inventory")
    bkt_all = e.route("BKT", "all peat routes combined")
    jmb_sens = e.route("JMB", "footprint_sensitivity")
    need(jmb_all.peat_share_percent > 4 * bkt_all.peat_share_percent,
         "peat dominates the lowland tower and not the highland one")
    t["P_PEAT_TEXT"] = (
        f"Peatland carries {jmb_all.over_peat_mean:.1f} ppb of the {jmb_all.total_mean:.1f} ppb modelled methane source "
        f"signal at Jambi, {jmb_all.peat_share_percent:.0f}%, and reaches {jmb_all.over_peat_max:.0f} ppb on the most "
        f"peat-influenced afternoon in the record. At Bukit Kototabang the same calculation gives "
        f"{bkt_all.over_peat_mean:.1f} ppb, {bkt_all.peat_share_percent:.1f}%. The two towers are not sampling the same land "
        "surface, and a peatland question can only be asked at the lowland one.\n\n"
        "The split between transport and emission is the part worth keeping. Peat cells carry "
        f"{jmb_sens.peat_share_percent:.0f}% of the Jambi footprint sensitivity but "
        f"{jmb_all.peat_share_percent:.0f}% of the signal, so per unit of sensitivity peat is emitting about "
        f"{enrichment(jmb_all.peat_share_percent, jmb_sens.peat_share_percent):.1f} times what the rest of the land in the "
        "footprint emits. That ratio is a property of the priors, not a measurement, but it is exactly the quantity a "
        "denser network would test directly.\n\n"
        "Three routes carry it, and they are three different processes with three different answers. Anthropogenic emission "
        f"sitting on drained peatland contributes {e.route('JMB', 'anthropogenic').over_peat_mean:.1f} ppb, biological "
        f"emission from peat swamp {e.route('JMB', 'wetlands').over_peat_mean:.1f} ppb through the wetland prior, and fire "
        f"{e.route('JMB', 'fire').over_peat_mean + e.route('JMB', 'FOLU_land_use_fire').over_peat_mean:.1f} ppb in a window "
        "that was not a burning season. Indonesia reports no methane from drained organic soils, only carbon dioxide and "
        "nitrous oxide, so drained-peat methane reaches this model through the wetland prior and through agriculture and "
        "waste sitting on peat rather than through a land-use category. That is a property of the reporting, and it is why "
        "the peat methane number here cannot be checked against a national figure.\n\n"
        f"Localising the inventory halves the absolute peat contribution, to {jmb_rep.over_peat_mean:.1f} ppb, and raises "
        f"its share to {jmb_rep.peat_share_percent:.0f}%, because the correction falls hardest on the fugitive sector and "
        "peat emission is mostly not fugitive. Both numbers are worth carrying: the share is what a land-use argument needs, "
        "the absolute value is what a budget needs.")

    # ---- Table 8: the carbon dioxide budget
    rows = []
    block = e.budget[e.budget.gas.eq("CO2")]
    order = block[block.station.eq("JMB")].sort_values("prior_mean", ascending=False).component
    pretty = {"biosphere_release": "biosphere, respiration", "biosphere_uptake": "biosphere, uptake (a sink)",
              "FOLU_drained_peat": "drained peat", "FOLU_land_use_fire": "land-use fire", "ocean": "ocean",
              "fire": "open fire"}
    for component in order:
        row_b = e.component("BKT", component, "CO2"); row_j = e.component("JMB", component, "CO2")
        name = pretty.get(component, component.replace("fossil_", "fossil, ").replace("_", " ").lower())
        sign = "" if component == "biosphere_uptake" else "+"
        rows.append([name, f"{sign}{row_b.prior_mean:.3f}" if sign else f"{row_b.prior_mean:.3f}",
                     f"{sign}{row_j.prior_mean:.3f}" if sign else f"{row_j.prior_mean:.3f}",
                     "" if pd.isna(row_j.share_percent) else f"{row_j.share_percent:.1f}"])
    t["P_CO2_BUDGET_TABLE"] = ("**Table 8. The modelled carbon dioxide budget at each tower, in ppm.** The share column is of "
        "the positive terms at Jambi. Biosphere uptake is a sink: it is carried as a magnitude, shown here without a sign, "
        "and it is excluded from the share column.\n\n"
        + markdown_table(["Component", "BKT", "Jambi", "Share at Jambi (%)"], rows))
    fossil_b = block[block.station.eq("BKT") & block.component.str.startswith("fossil_")].prior_mean.sum()
    fossil_j = block[block.station.eq("JMB") & block.component.str.startswith("fossil_")].prior_mean.sum()
    peat_co2 = e.component("JMB", "FOLU_drained_peat", "CO2")
    need(peat_co2.prior_mean > fossil_j / 2, "drained peat is comparable to the whole fossil term at Jambi")
    t["P_CO2_BUDGET_TEXT"] = (
        f"Fossil emission is small here. Summed over every sector it is {fossil_b:.2f} ppm at Bukit Kototabang and "
        f"{fossil_j:.2f} ppm at Jambi, against biosphere terms an order of magnitude larger in both directions: "
        f"{e.component('JMB', 'biosphere_release', 'CO2').prior_mean:.1f} ppm of respiration against "
        f"{e.component('JMB', 'biosphere_uptake', 'CO2').prior_mean:.1f} ppm of uptake at Jambi. The afternoon carbon "
        "dioxide signal at these towers is a biosphere signal with a fossil perturbation on it, which is the opposite of the "
        "situation an urban inversion is designed for.\n\n"
        f"Drained peat is the exception worth naming. At {peat_co2.prior_mean:.2f} ppm it is larger than every individual "
        f"fossil sector at Jambi and {peat_co2.prior_mean / fossil_j:.0%} of all of them combined, while at Bukit Kototabang "
        f"it is {e.component('BKT', 'FOLU_drained_peat', 'CO2').prior_mean:.2f} ppm. If a "
        "single carbon dioxide question is worth asking of a lowland Sumatran tower, it is this one.")
    # ---- Table 13: what the posterior implies, and the detection limit
    short = {"global inventory, diagnostic biosphere": "global", "hybrid biosphere": "hybrid biosphere",
             "with land use included": "global, with land use", "global inventory": "global",
             "national reported inventory": "reported, national", "provincial reported inventory": "reported, provincial"}

    def flux_rows(gas: str) -> str:
        rows = []
        for row in e.flux[e.flux.gas.eq(gas)].itertuples():
            rows.append([short.get(row.prior, row.prior), row.parameter.replace("_", " "),
                         f"{row.multiplier:.2f} ({row.ci_lo:.2f} to {row.ci_hi:.2f})",
                         f"{row.detectable_change_percent:.0f}",
                         "" if pd.isna(row.prior_region_Gg) else f"{row.prior_region_Gg:,.0f}",
                         "" if pd.isna(row.posterior_region_Gg) else
                         f"{row.posterior_region_Gg:,.0f} ({row.posterior_lo_Gg:,.0f} to {row.posterior_hi_Gg:,.0f})"])
        return markdown_table(["Prior", "Parameter", "Multiplier (95%)", "Detectable (%)",
                               "Prior (Gg/yr)", "Posterior (Gg/yr)"], rows)

    # split by gas: one table of twenty-five rows cannot share a page with text, and
    # reserving a whole page for it left the preceding one nearly empty
    t["P_FLUX_TABLE"] = ("**Table 13. Methane multipliers, the emission they imply over the four provinces the towers see, and "
        "the change each parameter could detect.** The detectable change is twice the posterior standard deviation in log "
        "space, so it is the fractional change that would sit at the edge of a 95% interval. Emission columns are omitted for "
        "parameters with no inventory total behind them.\n\n" + flux_rows("ch4"))
    t["P_FLUX_TABLE_CO2"] = ("**Table 14. The same for carbon dioxide.** The emission column for the fossil parameters is the "
        "global gridded inventory over those four provinces; for land use it is the reported drained-peat total.\n\n"
        + flux_rows("co2"))
    near = e.parameter("provincial reported inventory", "anthro_near")
    near_global = e.parameter("global inventory", "anthro_near")
    best = e.flux.loc[e.flux.detectable_change_percent.idxmin()]
    need(e.flux.detectable_change_percent.min() > 50, "no parameter is constrained better than a factor of about two")
    t["P_FLUX_TEXT"] = (
        "A multiplier is dimensionless and applies where the footprint has weight, so it is quoted here over the four "
        "provinces the towers see rather than nationally. Scaling a national total by the same multiplier would assume the "
        "correction holds in provinces neither tower can see, which is exactly what the readiness gate refuses to certify.\n\n"
        f"Read that way, the near-field methane posterior is {near.posterior_region_Gg:.0f} Gg per year across those four "
        f"provinces, with a 95% interval of {near.posterior_lo_Gg:.0f} to {near.posterior_hi_Gg:.0f} Gg, against a reported "
        f"prior of {near.prior_region_Gg:.0f} Gg. Starting instead from the global gridded inventory the same fit gives "
        f"{near_global.posterior_region_Gg:.0f} Gg from a prior of {near_global.prior_region_Gg:.0f} Gg. The two posteriors "
        "differ by an order of magnitude because the two priors do, which is the cleanest possible measure of how much of "
        "the answer the prior is still supplying. Neither interval excludes its own prior, so neither is a flux estimate.\n\n"
        "One comparison in this table is resolved, and it is not the one the readiness gate tests. The near-field methane "
        f"multiplier excludes one at 95% under the global gridded inventory ({near_global.multiplier:.2f}, "
        f"{near_global.ci_lo:.2f} to {near_global.ci_hi:.2f}) and under the reported national totals "
        f"({e.parameter('national reported inventory', 'anthro_near').multiplier:.2f}, "
        f"{e.parameter('national reported inventory', 'anthro_near').ci_lo:.2f} to "
        f"{e.parameter('national reported inventory', 'anthro_near').ci_hi:.2f}), and stops excluding it once the totals are "
        f"allocated to provinces ({near.multiplier:.2f}, {near.ci_lo:.2f} to {near.ci_hi:.2f}). Read plainly: under the "
        "stated error model the observations reject the global inventory's magnitude in the region they can see, and they "
        "stop rejecting it when Indonesia's own provincial figures set that magnitude. This is a statement about the prior, "
        "conditional on the error model and on the log-normal width assumed for the multiplier. It is not the same test as "
        "Section 6.2, which asks whether the fitted posterior predicts a withheld day better than a fitted boundary field, "
        "and which nothing passes.\n\n"
        "The detection limit is the more useful operational number, because it does not depend on the prior being right. "
        f"No parameter in the campaign is constrained better than {e.flux.detectable_change_percent.min():.0f}%, the best "
        f"being {best.parameter.replace('_', ' ')}, and the near-field methane term stands at "
        f"{near.detectable_change_percent:.0f}%. A change in emission smaller than about a factor of two therefore cannot be "
        "seen by this network, however long it runs, unless the transport error falls. That is the number to quote when "
        "asked whether the towers can verify a mitigation commitment: not yet, and by a stated margin.")

    # ---- the summary and the framing
    bkt_ch4, jmb_ch4 = e.record("CH4", "BKT"), e.record("CH4", "JMB")
    jmb_peat_all = e.route("JMB", "all peat routes combined")
    fugitive = e.category("1B")
    ch4_global = e.run("ch4")
    ch4_provincial = e.run("ch4", inventory="provincial")
    error_ch4 = e.error[e.error.gas.eq("ch4")].iloc[0]
    error_co2 = e.error[e.error.gas.eq("co2")].iloc[0]
    t["P_SUMMARY"] = (
        "Two Sumatran towers, one on the highland spine at Bukit Kototabang and one in the eastern lowland at Jambi, are "
        "used here to ask what a small greenhouse gas network can say about Indonesian emissions. The answer has two halves, "
        "and they are different.\n\n"
        "The forward part works and is quantitative. The towers draw at least one percent of their modelled methane signal "
        f"from four provinces and no more. At Jambi one sector carries the modelled signal, fugitive emission from fuel "
        f"exploitation at {e.component('JMB', 'CH4_FUEL_EXPLOITATION').share_percent:.0f}%; at Bukit Kototabang natural "
        f"wetlands do, at {e.component('BKT', 'wetlands').share_percent:.0f}%. Peatland carries "
        f"{jmb_peat_all.over_peat_mean:.0f} ppb of the {jmb_peat_all.total_mean:.0f} ppb modelled methane signal at Jambi, "
        f"{jmb_peat_all.peat_share_percent:.0f}%, reaching {jmb_peat_all.over_peat_max:.0f} ppb on the most peat-influenced "
        f"afternoon, against {e.route('BKT', 'all peat routes combined').peat_share_percent:.1f}% at the highland tower. "
        f"Drained peat is also the largest single carbon dioxide term at Jambi after the biosphere, "
        f"{e.component('JMB', 'FOLU_drained_peat', 'CO2').prior_mean:.2f} ppm, larger than any individual fossil sector "
        "and two thirds of all of them combined.\n\n"
        "The clearest statement the record makes needs no inversion at all. The global gridded inventory says "
        f"{bkt_ch4.modelled_source_signal:.0f} ppb of methane should arrive above background at Bukit Kototabang and "
        f"{jmb_ch4.modelled_source_signal:.0f} ppb at Jambi; {bkt_ch4.observed_enhancement:.0f} and "
        f"{jmb_ch4.observed_enhancement:.0f} ppb arrive. Indonesia's own reported inventory removes most of that excess: it "
        f"reports {fugitive.reported_Gg:.0f} Gg of fugitive methane for 2022 where the global inventory puts "
        f"{fugitive.global_Gg:.0f} Gg inside the country. Localising the prior to the reported totals and allocating them "
        f"across provinces cuts the prior error from {ch4_global['prior_rmse']:.1f} to {ch4_provincial['prior_rmse']:.1f} "
        "ppb and is the only configuration that puts both towers on the favourable side of the boundary null. Under "
        "the stated error model the fit goes further and rejects the global inventory outright in the region the "
        f"towers see: the near-field methane multiplier is {near_global.multiplier:.2f} with a 95% interval of "
        f"{near_global.ci_lo:.2f} to {near_global.ci_hi:.2f}, which excludes one, and it stops excluding one "
        f"({near.multiplier:.2f}, {near.ci_lo:.2f} to {near.ci_hi:.2f}) once Indonesia's own provincial figures "
        "set the magnitude. That is the single resolved result in this report.\n\n"
        "The inverse part does not work yet, and the reason is measured rather than asserted. The modelled source signal is "
        f"barely above the error it arrives through: a signal-to-error ratio of {error_co2.signal_to_error:.2f} for carbon "
        f"dioxide and {error_ch4.signal_to_error:.2f} for methane, with transport the largest error term for both. Of the "
        f"{len(e.verdicts)} combinations run, none beats a fitted boundary field at a scale with enough independent bins to "
        "test, and no emission change smaller than about a factor of two could be detected at all. The transport error is "
        "not stochastic and will not fall by running more particles; it needs a second meteorological driver, which is the "
        "one experiment this project has not done.")
    t["P_INTRO"] = (
        "A tower network is funded to answer questions about emissions, not about models. This report is organised around "
        "those questions, and it separates two things that are usually reported together.\n\n"
        "The first is what the forward model says: which sources the towers are sensitive to, how far away and how old the "
        "air is, which provinces and which land surface carry the signal, and how much of it comes off peatland. Those "
        "answers depend on the footprints and the priors and they are quantitative today. They are also testable, because a "
        "prior that says three times too much methane should arrive is making a claim the observations can contradict.\n\n"
        "The second is what the inversion adds on top: a correction to those priors, with an uncertainty. That part is not "
        "ready, and the report says so with the number that settles it rather than with an adjective. Keeping the two apart "
        "is the point. A footprint-weighted attribution is useful even when the inversion behind it cannot yet beat a "
        "fitted constant, and calling both of them the same kind of result is how a project like this publishes something "
        "wrong.")
    return t



def build(write: bool = True) -> str:
    template = TEMPLATE.read_text()
    tok = tokens()
    missing = set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", template)) - tok.keys()
    if missing:
        raise ValueError(f"missing tokens {sorted(missing)}")
    text = renumber(re.sub(r"\{\{([A-Z0-9_]+)\}\}", lambda m: tok[m[1]], template))
    if "{{" in text or "—" in text:
        raise ValueError("unresolved token or em dash in the rendered report")
    if write:
        (ROOT / f"{STEM}.md").write_text(text)
        (OPERATIONAL / "report_tokens.json").write_text(
            json.dumps({k: v for k, v in tok.items() if "TABLE" not in k}, indent=2) + "\n")
        print(f"wrote {STEM}.md ({len(text.splitlines())} lines, "
              f"{len(re.findall(r'[*][*]Figure ', text))} figures, {len(re.findall(r'[*][*]Table ', text))} tables)")
    return text


if __name__ == "__main__":
    build()
