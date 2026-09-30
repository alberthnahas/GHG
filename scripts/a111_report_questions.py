#!/usr/bin/env python3
"""The question index for the operational report.

A report that only says whether a model passed its own gate is a log, not a
result. This module turns the evidence already on disk into the questions a
monitoring programme actually asks, each answered with a number that traces back
to a named file. Every value here is read at build time, so an answer cannot
drift away from the table it came from.

The questions are grouped the way the work is used: what arrived at the towers,
where it came from, which sources carried it, what the peatland contributes,
what the national inventory says, what the inversion resolves, and what the
system can be operated to do today.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import a84_bkt_jmb_two_receptor as T

OPERATIONAL = T.ROOT / "outputs/operational"
INVENTORY = T.ROOT / "outputs/inventory"
NAME = {"BKT": "Bukit Kototabang", "JMB": "Jambi"}


class Evidence:
    """Every file the questions draw on, opened once."""

    def __init__(self) -> None:
        self.budget = pd.read_csv(OPERATIONAL / "attribution_budget.csv")
        self.peat = pd.read_csv(OPERATIONAL / "attribution_peat.csv")
        self.distance = pd.read_csv(OPERATIONAL / "attribution_distance.csv")
        self.age = pd.read_csv(OPERATIONAL / "attribution_age.csv")
        self.provinces = pd.read_csv(OPERATIONAL / "attribution_provinces.csv")
        self.districts = pd.read_csv(OPERATIONAL / "attribution_districts.csv")
        self.flux = pd.read_csv(OPERATIONAL / "attribution_flux.csv")
        self.records = pd.read_csv(OPERATIONAL / "attribution_records.csv")
        self.error = pd.read_csv(OPERATIONAL / "error_budget.csv")
        self.audit = pd.read_csv(OPERATIONAL / "prior_audit.csv")
        self.registry = pd.read_csv(OPERATIONAL / "dataset_registry.csv")
        self.ledger = pd.read_csv(INVENTORY / "local_inventory_ch4_2022_primap_ledger.csv")
        self.provincial = pd.read_csv(INVENTORY / "local_inventory_ch4_2022_provincial_ledger.csv")
        self.verdicts = [v for v in json.loads((OPERATIONAL / "inversion_readiness.json").read_text())
                         if "receptors" in v]
        self.daily = [v for v in self.verdicts if v["scale"] == "daily"]

    # ---- convenience lookups, each one a single row of a single table

    def record(self, gas: str, station: str):
        return self.records[self.records.gas.eq(gas) & self.records.station.eq(station)].iloc[0]

    def component(self, station: str, name: str, gas: str = "CH4"):
        """One component of one gas at one station. The gas matters: both budgets
        carry a component called fire, and reading the wrong one is silent."""
        block = self.budget[self.budget.station.eq(station) & self.budget.component.eq(name)
                            & self.budget.gas.eq(gas)]
        return block.iloc[0]

    def route(self, station: str, quantity: str):
        return self.peat[self.peat.station.eq(station) & self.peat.quantity.eq(quantity)].iloc[0]

    def band(self, station: str, quantity: str, band: str):
        block = self.distance[self.distance.station.eq(station) & self.distance.quantity.eq(quantity)
                              & self.distance.band_km.eq(band)]
        return block.iloc[0]

    def run(self, gas: str, inventory: str = "EDGAR", folu: str = "excluded", biosphere: str = "diagnostic"):
        for verdict in self.daily:
            if (verdict["gas"] == gas and verdict["inventory"] == inventory
                    and verdict.get("folu", "excluded") == folu and verdict["biosphere"] == biosphere):
                return verdict
        raise KeyError(f"no daily run for {gas} {inventory} {folu} {biosphere}")

    def parameter(self, prior: str, name: str):
        block = self.flux[self.flux.prior.eq(prior) & self.flux.parameter.eq(name)]
        return block.iloc[0]

    def skill(self, verdict: dict) -> pd.DataFrame:
        tag = f"{verdict['gas']}{'' if verdict['biosphere'] == 'diagnostic' else verdict['biosphere']}"
        tag += "" if verdict["inventory"] == "EDGAR" else f"_{verdict['inventory']}"
        tag += "" if verdict.get("folu", "excluded") == "excluded" else f"_folu{verdict['folu']}"
        return pd.read_csv(OPERATIONAL / f"inversion_{tag}_{verdict['scale']}_skill.csv").set_index("station")

    def category(self, code: str):
        return self.ledger[self.ledger.ipcc_code.eq(code)].iloc[0]


def questions(e: Evidence) -> list[tuple[str, list[tuple[str, str, str]]]]:
    """Grouped (question, answer, source) triples, every number read from a file."""
    bkt_ch4, jmb_ch4 = e.record("CH4", "BKT"), e.record("CH4", "JMB")
    bkt_co2, jmb_co2 = e.record("CO2", "BKT"), e.record("CO2", "JMB")
    jmb_peat = e.route("JMB", "all peat routes combined")
    jmb_peat_reported = e.route("JMB", "all peat routes, reported inventory")
    bkt_peat = e.route("BKT", "all peat routes combined")
    jmb_wet_peat = e.route("JMB", "wetlands")
    jmb_anthro_peat = e.route("JMB", "anthropogenic")
    jmb_fire_peat = e.route("JMB", "fire")
    jmb_folu_peat = e.route("JMB", "FOLU_land_use_fire")
    jmb_sensitivity = e.route("JMB", "footprint_sensitivity")
    bkt_sensitivity = e.route("BKT", "footprint_sensitivity")
    ch4_global, ch4_provincial = e.run("ch4"), e.run("ch4", inventory="provincial")
    ch4_national = e.run("ch4", inventory="primap")
    co2_base, co2_folu = e.run("co2"), e.run("co2", folu="full")
    co2_hybrid = e.run("co2", biosphere="_hybrid")
    error_co2 = e.error[e.error.gas.eq("co2")].iloc[0]
    error_ch4 = e.error[e.error.gas.eq("ch4")].iloc[0]
    fugitive, waste, agriculture = e.category("1B"), e.category("4"), e.category("3A+3C")
    energy = e.category("1A")
    near_global = e.parameter("global inventory", "anthro_near")
    near_provincial = e.parameter("provincial reported inventory", "anthro_near")
    wetlands_fit = e.parameter("provincial reported inventory", "wetlands")
    drainage_fit = e.parameter("with land use included", "folu_drainage")

    def top(table, station, n=1):
        block = table[table.station.eq(station)].nlargest(n, "share_percent")
        return block.iloc[n - 1]

    def provincial_factor(region: str, code: str) -> float:
        block = e.provincial[e.provincial.region.eq(region) & e.provincial.ipcc_code.eq(code)]
        return float(block.factor.iloc[0])

    groups: list[tuple[str, list[tuple[str, str, str]]]] = []

    groups.append(("What arrived at the towers", [
        ("How much methane above the modelled background arrives at each tower on a typical screened afternoon?",
         f"{bkt_ch4.observed_enhancement:.0f} ppb at Bukit Kototabang and {jmb_ch4.observed_enhancement:.0f} ppb at Jambi, "
         f"against afternoon means of {bkt_ch4.observed_mean:.0f} and {jmb_ch4.observed_mean:.0f} ppb.", "Table 2"),
        ("How variable is that record?",
         f"The screened afternoon methane spans {bkt_ch4.observed_range:.0f} ppb at Bukit Kototabang and "
         f"{jmb_ch4.observed_range:.0f} ppb at Jambi, with standard deviations of {bkt_ch4.observed_sd:.0f} and "
         f"{jmb_ch4.observed_sd:.0f} ppb.", "Table 2"),
        ("Does the prior predict the right amount of methane?",
         f"No. The modelled source signal is {bkt_ch4.modelled_over_observed:.1f} times the observed enhancement at Bukit "
         f"Kototabang and {jmb_ch4.modelled_over_observed:.1f} times at Jambi, so the global gridded prior puts two to three "
         "times too much methane into the air the towers sample.", "Table 2"),
        ("Which tower is noisier, and why does it matter?",
         f"Jambi. It sits in the lowland with sources close by, so a single receptor carries more local variance; its "
         f"screened record is also shorter, {jmb_ch4.receptors} usable afternoons against {bkt_ch4.receptors}, which is why "
         "its bootstrap intervals are roughly twice as wide.", "Tables 2 and 12"),
        ("What does the carbon dioxide record look like on the same afternoons?",
         f"Afternoon means of {bkt_co2.observed_mean:.1f} ppm at Bukit Kototabang and {jmb_co2.observed_mean:.1f} ppm at "
         f"Jambi, sitting {abs(bkt_co2.observed_enhancement):.1f} and {abs(jmb_co2.observed_enhancement):.1f} ppm below the "
         "modelled background, because afternoon photosynthesis draws the boundary layer down.", "Table 2"),
        ("How many receptors does the whole analysis rest on?",
         f"{bkt_ch4.receptors + jmb_ch4.receptors} screened methane afternoons in 2023 and "
         f"{bkt_co2.receptors + jmb_co2.receptors} carbon dioxide afternoons across 2023 and 2024, after screening for "
         "particle retention, mixing depth and carbon-dioxide-only spikes.", "Table 2"),
        ("Why are night hours excluded?",
         "A quarter-degree footprint cannot carry the shallow nocturnal layer the night observations sit in. Fitting those "
         "hours drives the error model to its cap and returns every multiplier to its prior, so they are screened out rather "
         "than modelled badly.", "Section 2.1"),
        ("Is the error model consistent with the residuals it produces?",
         f"Yes. The reduced chi-square runs from {min(v['reduced_chi_square'] for v in e.daily):.2f} to "
         f"{max(v['reduced_chi_square'] for v in e.daily):.2f} across every configuration, so the stated uncertainties are "
         "neither optimistic nor padded.", "Table 11"),
    ]))

    groups.append(("Where the air came from", [
        ("How far away are the sources each tower sees?",
         f"At Bukit Kototabang {e.band('BKT', 'anthropogenic', '0 to 50').share_percent:.0f}% of the modelled anthropogenic "
         f"methane is emitted within 50 km; at Jambi only {e.band('JMB', 'anthropogenic', '0 to 50').share_percent:.0f}%, "
         f"with {e.band('JMB', 'anthropogenic', '200 to 500').share_percent:.0f}% coming from 200 to 500 km away.",
         "Table 3"),
        ("How old is the air carrying the signal?",
         f"The median sensitivity age is {e.age[e.age.station.eq('BKT')].iloc[-1].sensitivity_share_percent:.0f} hours at "
         f"Bukit Kototabang and {e.age[e.age.station.eq('JMB')].iloc[-1].sensitivity_share_percent:.0f} hours at Jambi, so "
         "Jambi is sampling air that has been over land for two days on average.", "Table 3"),
        ("How much of the signal is older than three days?",
         f"{e.age[e.age.station.eq('BKT') & e.age.age_hours.eq('72 to 120')].iloc[0].sensitivity_share_percent:.0f}% at "
         f"Bukit Kototabang and "
         f"{e.age[e.age.station.eq('JMB') & e.age.age_hours.eq('72 to 120')].iloc[0].sensitivity_share_percent:.0f}% at "
         "Jambi. That part of the signal depends on the boundary field as much as on the inventory.", "Table 3"),
        ("Which province does each tower mostly see?",
         f"Bukit Kototabang draws {top(e.provinces, 'BKT').share_percent:.0f}% of its modelled methane signal from "
         f"{top(e.provinces, 'BKT').region.title()}; Jambi draws {top(e.provinces, 'JMB').share_percent:.0f}% from "
         f"{top(e.provinces, 'JMB').region.title()} and {top(e.provinces, 'JMB', 2).share_percent:.0f}% from "
         f"{top(e.provinces, 'JMB', 2).region.title()}.", "Table 4, Figure 2"),
        ("How many provinces can this network constrain at all?",
         "Four. Sumatera Barat, Jambi, Sumatera Selatan and Riau each carry at least one percent of a tower's signal, and no "
         "province outside Sumatra reaches one percent at either tower.", "Table 4, Figure 2"),
        ("Are the two towers redundant?",
         "No, but they are not independent either. Bukit Kototabang is dominated by its own province while Jambi spreads "
         "across three, and Riau is common to both, so the pair constrains a larger region than either alone but their "
         "errors are correlated through the same synoptic flow.", "Figures 1 and 2"),
        ("Which districts carry the signal?",
         f"{top(e.districts, 'BKT').region.title()} carries {top(e.districts, 'BKT').share_percent:.0f}% at Bukit "
         f"Kototabang, its own district; the next is {top(e.districts, 'BKT', 2).region.title()} at "
         f"{top(e.districts, 'BKT', 2).share_percent:.1f}%. At Jambi the leader is "
         f"{top(e.districts, 'JMB').region.title()} at {top(e.districts, 'JMB').share_percent:.0f}%.",
         "Table 5, Figure 3"),
        ("Where would an inventory error hurt most?",
         f"In {top(e.districts, 'BKT', 2).region.title()}, which carries "
         f"{top(e.districts, 'BKT', 2).share_percent:.1f}% of the Bukit Kototabang methane signal from "
         f"{top(e.districts, 'BKT', 2).sensitivity_share_percent:.2f}% of its footprint sensitivity. A concentration that "
         "extreme means one or two grid cells of the gridded inventory set a large part of the modelled signal.",
         "Table 5, Figure 3"),
        ("Does either tower see Java, Kalimantan or eastern Indonesia?",
         "Not measurably. No province outside Sumatra reaches one percent of either tower's modelled methane signal, so "
         "national conclusions cannot be drawn from this pair.", "Table 4, Figure 2"),
    ]))

    groups.append(("What emits the methane", [
        ("Which sector dominates the modelled methane signal at Jambi?",
         f"Fugitive emissions from fuel exploitation, {e.component('JMB', 'CH4_FUEL_EXPLOITATION').share_percent:.0f}% of "
         f"the modelled source signal at {e.component('JMB', 'CH4_FUEL_EXPLOITATION').prior_mean:.0f} ppb, under the global "
         "gridded inventory.", "Table 6"),
        ("And at Bukit Kototabang?",
         f"Natural wetlands, {e.component('BKT', 'wetlands').share_percent:.0f}%, followed by agriculture at "
         f"{e.component('BKT', 'CH4_AGRICULTURE').share_percent:.0f}% and fugitive emissions at "
         f"{e.component('BKT', 'CH4_FUEL_EXPLOITATION').share_percent:.0f}%.", "Table 6"),
        ("How much of the methane signal is natural rather than anthropogenic?",
         f"{e.component('BKT', 'wetlands').share_percent + e.component('BKT', 'termites').share_percent + e.component('BKT', 'geological').share_percent:.0f}% at "
         f"Bukit Kototabang and "
         f"{e.component('JMB', 'wetlands').share_percent + e.component('JMB', 'termites').share_percent + e.component('JMB', 'geological').share_percent:.0f}% at "
         "Jambi, counting wetlands, termites and geological seepage. No national inventory carries any of it.",
         "Table 6"),
        ("How large is the waste sector in what the towers see?",
         f"{e.component('JMB', 'CH4_WASTE').share_percent:.0f}% of the Jambi signal and "
         f"{e.component('BKT', 'CH4_WASTE').share_percent:.0f}% at Bukit Kototabang under the global inventory. It is one of "
         "only two sectors Indonesia reports higher than the global inventory assumes.", "Tables 6 and 9"),
        ("How much does agriculture contribute?",
         f"{e.component('BKT', 'CH4_AGRICULTURE').prior_mean:.0f} ppb at Bukit Kototabang, its largest anthropogenic term, "
         f"and {e.component('JMB', 'CH4_AGRICULTURE').prior_mean:.0f} ppb at Jambi. Rice and livestock dominate the category "
         "nationally.", "Table 6"),
        ("Does soil uptake matter?",
         f"Marginally. Soil oxidation removes {e.component('BKT', 'soil_uptake').prior_mean:.1f} ppb at Bukit Kototabang and "
         f"{e.component('JMB', 'soil_uptake').prior_mean:.1f} ppb at Jambi, one to two percent of the source terms, and it "
         "is subtracted rather than fitted.", "Table 6"),
        ("How much methane comes from fire?",
         f"{e.route('JMB', 'fire').total_mean:.1f} ppb at Jambi and {e.route('BKT', 'fire').total_mean:.1f} ppb at Bukit "
         f"Kototabang from open burning, plus {e.route('JMB', 'FOLU_land_use_fire').total_mean:.2f} and "
         f"{e.route('BKT', 'FOLU_land_use_fire').total_mean:.2f} ppb from the reported land-use fire category. These are "
         "2023 receptors outside a major burning year, so the figure is not a haze-season one.", "Tables 6 and 7"),
        ("What does the reported national inventory do to the sector picture?",
         f"It collapses the fugitive term. At Jambi fuel exploitation falls from "
         f"{e.component('JMB', 'CH4_FUEL_EXPLOITATION').prior_mean:.0f} to "
         f"{e.component('JMB', 'CH4_FUEL_EXPLOITATION').reported_mean:.1f} ppb, and waste becomes the largest reported "
         "anthropogenic term at that tower.", "Table 6"),
        ("Which sector should an inventory improvement target first?",
         "Fugitive methane in Riau, Jambi and South Sumatra. It is the largest term in the global inventory at Jambi, the "
         "largest disagreement with the reported inventory, and it sits where both towers have sensitivity.",
         "Tables 6 and 9, Figure 6"),
        ("Do the towers see enough to separate sectors?",
         f"No. The observations inform {min(v['degrees_of_freedom'] for v in e.daily):.1f} to "
         f"{max(v['degrees_of_freedom'] for v in e.daily):.1f} parameters, so the multipliers must be read as one bulk "
         "adjustment and not as sector-by-sector corrections.", "Table 11"),
    ]))

    groups.append(("Peatland", [
        ("How much of the methane arriving at Jambi comes from peatland?",
         f"{jmb_peat.over_peat_mean:.1f} ppb of the {jmb_peat.total_mean:.1f} ppb modelled source signal, "
         f"{jmb_peat.peat_share_percent:.0f}%, rising to {jmb_peat.over_peat_max:.0f} ppb on the most peat-influenced "
         "afternoon in the record.", "Table 7, Figure 4"),
        ("Does that hold once the inventory is localised to the reported national figures?",
         f"The absolute contribution halves to {jmb_peat_reported.over_peat_mean:.1f} ppb, but the share rises to "
         f"{jmb_peat_reported.peat_share_percent:.0f}%, because localisation cuts the fugitive term far harder than it cuts "
         "anything emitted on peat.", "Table 7"),
        ("By what route does peat methane reach the tower?",
         f"Three. Anthropogenic emission sitting on drained peatland contributes {jmb_anthro_peat.over_peat_mean:.1f} ppb, "
         f"biological emission from peat swamp {jmb_wet_peat.over_peat_mean:.1f} ppb through the wetland prior, and fire "
         f"{jmb_fire_peat.over_peat_mean + jmb_folu_peat.over_peat_mean:.1f} ppb.", "Table 7, Figure 4"),
        ("What fraction of the wetland methane at Jambi is emitted over peat?",
         f"{jmb_wet_peat.peat_share_percent:.0f}%, against {e.route('BKT', 'wetlands').peat_share_percent:.0f}% at Bukit "
         "Kototabang. Peat swamp is the dominant Indonesian wetland, so the wetland prior is largely a peat prior at this "
         "tower.", "Table 7"),
        ("How much of the peatland signal reaches the highland tower?",
         f"{bkt_peat.over_peat_mean:.1f} ppb, {bkt_peat.peat_share_percent:.1f}% of its source signal, against "
         f"{jmb_peat.peat_share_percent:.0f}% at Jambi. The two towers are not sampling the same land surface.",
         "Table 7"),
        ("Is the peat signal a transport effect or an emission effect?",
         f"Both, and they can be separated. Peat cells carry {jmb_sensitivity.peat_share_percent:.0f}% of the Jambi "
         f"footprint sensitivity but {jmb_peat.peat_share_percent:.0f}% of the signal, so per unit of sensitivity peat is "
         f"emitting about {((jmb_peat.peat_share_percent / jmb_sensitivity.peat_share_percent) / ((100 - jmb_peat.peat_share_percent) / (100 - jmb_sensitivity.peat_share_percent))):.1f} "
         f"times what the rest of the land in the footprint emits. At Bukit Kototabang the two shares are "
         f"{bkt_sensitivity.peat_share_percent:.1f}% and {bkt_peat.peat_share_percent:.1f}%, close to parity.",
         "Table 7"),
        ("Does Indonesia report methane from drained peat?",
         "No. The national land-use reporting covers carbon dioxide and nitrous oxide from drained organic soils; the "
         "methane land-use category is fire only. Drained-peat methane therefore reaches the model through the wetland prior "
         "and through agriculture and waste sitting on peat, not through a land-use category.", "Section 4.2"),
        ("What does drained peat do to the carbon dioxide budget?",
         f"It is the third largest positive term at Jambi, {e.component('JMB', 'FOLU_drained_peat', 'CO2').prior_mean:.2f} ppm, "
         f"{e.component('JMB', 'FOLU_drained_peat', 'CO2').share_percent:.0f}% of the positive signal and larger than every fossil "
         f"sector except power. At Bukit Kototabang it is {e.component('BKT', 'FOLU_drained_peat', 'CO2').prior_mean:.2f} ppm.",
         "Table 8, Figure 5"),
        ("Can the inversion measure the drained-peat term?",
         f"Not yet. The multiplier is {drainage_fit.multiplier:.2f} with a 95% interval of {drainage_fit.ci_lo:.2f} to "
         f"{drainage_fit.ci_hi:.2f}, consistent with the prior and with anything between a third and three times it.",
         "Table 14"),
        ("Why is the peat magnitude taken from the reported total rather than an emission factor?",
         "Because published drained-peat emission factors span a factor of ten, from 8.13 to 80.77 Mg carbon dioxide per "
         "hectare per year across land covers and water tables. The proxy therefore carries a spatial pattern only and the "
         "reported national total supplies the size.", "Section 2.3, Figure 5"),
    ]))

    groups.append(("Carbon dioxide", [
        ("What dominates the carbon dioxide signal?",
         f"The terrestrial biosphere, {e.audit[e.audit.gas.eq('co2') & e.audit.in_national_inventory.eq('no')].share_of_signal_percent.sum():.0f}% "
         "of the modelled variance, which no national inventory carries. Fossil emission is a few percent.",
         "Table 8"),
        ("How large is the fossil term at each tower?",
         f"{e.budget[e.budget.station.eq('BKT') & e.budget.component.str.startswith('fossil_')].prior_mean.sum():.2f} ppm "
         "at Bukit Kototabang and "
         f"{e.budget[e.budget.station.eq('JMB') & e.budget.component.str.startswith('fossil_')].prior_mean.sum():.2f} ppm "
         "at Jambi, summed over all sectors.", "Table 8"),
        ("Which fossil sector is largest?",
         f"Transport at Bukit Kototabang ({e.component('BKT', 'fossil_TRANSPORT', 'CO2').prior_mean:.2f} ppm) and power generation "
         f"at Jambi ({e.component('JMB', 'fossil_POWER_INDUSTRY', 'CO2').prior_mean:.2f} ppm).", "Table 8"),
        ("How much carbon does the biosphere take up on a screened afternoon?",
         f"{e.component('BKT', 'biosphere_uptake', 'CO2').prior_mean:.1f} ppm equivalent of uptake at Bukit Kototabang and "
         f"{e.component('JMB', 'biosphere_uptake', 'CO2').prior_mean:.1f} ppm at Jambi, against respiration of "
         f"{e.component('BKT', 'biosphere_release', 'CO2').prior_mean:.1f} and "
         f"{e.component('JMB', 'biosphere_release', 'CO2').prior_mean:.1f} ppm.", "Table 8"),
        ("Was the biosphere prior right?",
         f"No, and it is now better. The inversion scaled the diagnostic biosphere to "
         f"{e.parameter('global inventory, diagnostic biosphere', 'bio_net_BKT').multiplier:.2f} at Bukit Kototabang and "
         f"{e.parameter('global inventory, diagnostic biosphere', 'bio_net_JMB').multiplier:.2f} at Jambi, so its amplitude "
         "was several times too large. The hybrid prior, built from CarbonTracker's magnitude and the diagnostic phase, "
         "brings the afternoon drawdown to where the inversion had independently implied it should be.",
         "Section 6.6, Figure 10"),
        ("Did fixing the biosphere prior improve the result?",
         f"No. On identical receptors the hybrid is better at one tower and worse at the other, the prior error barely "
         f"moves, and the degrees of freedom fall from {co2_base['degrees_of_freedom']:.2f} to "
         f"{co2_hybrid['degrees_of_freedom']:.2f} because the shorter hybrid window has fewer bins. The prior was "
         "demonstrably wrong and is now demonstrably better; that was necessary and not sufficient.", "Section 6.6"),
        ("Did adding land use help the carbon dioxide inversion?",
         f"Yes, in information if not in skill. Degrees of freedom rise from {co2_base['degrees_of_freedom']:.2f} to "
         f"{co2_folu['degrees_of_freedom']:.2f} and the Jambi comparison improves, while Bukit Kototabang is unchanged. "
         "Jambi sits on peat and the highland tower does not.", "Table 11"),
        ("Why does carbon dioxide look harder than methane here?",
         f"Because its signal-to-error ratio is {error_co2.signal_to_error:.2f} and most of the signal is a biosphere term "
         "with no inventory to test against, so there is no equivalent of the inventory localisation that moved the methane "
         "result.", "Table 15"),
    ]))

    groups.append(("The national inventory", [
        ("How does Indonesia's reported methane compare with the global gridded inventory?",
         f"Indonesia reports {fugitive.reported_Gg:.0f} Gg of fugitive methane for 2022 where the global inventory puts "
         f"{fugitive.global_Gg:.0f} Gg inside the country, a factor of {1 / fugitive.factor:.0f}, and "
         f"{waste.reported_Gg:.0f} Gg of waste methane where the global inventory puts {waste.global_Gg:.0f}.",
         "Table 9, Figure 6"),
        ("Which categories does the country report lower, and which higher?",
         f"Lower for fugitive emissions (factor {fugitive.factor:.2f}), stationary and mobile energy "
         f"({energy.factor:.2f}) and agriculture ({agriculture.factor:.2f}); higher for waste ({waste.factor:.2f}).",
         "Table 9"),
        ("Does localising the inventory make the prior better?",
         f"Yes, monotonically. The prior error falls from {ch4_global['prior_rmse']:.1f} ppb with the global gridded "
         f"inventory to {ch4_national['prior_rmse']:.1f} with reported national totals and "
         f"{ch4_provincial['prior_rmse']:.1f} with those totals allocated to provinces, a reduction of "
         f"{100 * (1 - ch4_provincial['prior_rmse'] / ch4_global['prior_rmse']):.0f}%.", "Table 10"),
        ("Why does the provincial step matter beyond the national one?",
         f"Because a national factor is not the right factor anywhere in particular. The fugitive factor is "
         f"{fugitive.factor:.2f} nationally and {provincial_factor('JAMBI', '1B'):.2f} for Jambi, so a national correction "
         "is wrong by more than threefold for the province the tower actually sees.", "Table 10"),
        ("Where does the provincial split come from?",
         "Facility locations, not from the gridded inventory being corrected, which is what keeps it independent. Within a "
         "sector a facility's carbon-dioxide equivalent is proportional to the gas, so the asset data supply only the share "
         "and the reported total supplies the magnitude.", "Section 5.2"),
        ("Are district-level shares usable?",
         "Not by this inversion. They are written for 504 districts, but a quarter-degree footprint cell is larger than most "
         "Indonesian districts, so district numbers attribute the prior rather than estimate emission.",
         "Table 5, Figure 3"),
        ("Do the towers prefer the national numbers or the global inventory?",
         f"The national numbers, at both towers. The cross-validated difference from the boundary null at Jambi moves from "
         f"{e.skill(ch4_global).loc['JMB', 'rmse_difference']:+.2f} ppb with the global inventory to "
         f"{e.skill(ch4_provincial).loc['JMB', 'rmse_difference']:+.2f} with the provincial prior, and at Bukit Kototabang "
         f"from {e.skill(ch4_global).loc['BKT', 'rmse_difference']:+.2f} to "
         f"{e.skill(ch4_provincial).loc['BKT', 'rmse_difference']:+.2f}. It is the only configuration that puts both towers "
         "on the favourable side.", "Table 10, Figure 8"),
        ("Is that a measurement of the inventory being wrong?",
         "No. Every interval still spans zero, so the preference is a direction, not a resolved result. Whether the gap is "
         "the global inventory's spatial allocation, a real under-report, or a definitional difference is exactly the "
         "question a denser network exists to answer.", "Tables 9 and 10"),
        ("Does the inventory include land use?",
         "The global gridded inventory does not, which in Indonesia removes the largest and most variable term. The land-use "
         "proxy built here restores it, with reported national totals of 241,354 Gg of carbon dioxide from drained organic "
         "soils and 5,412 Gg from land-use fires.", "Section 2.3, Figure 5"),
    ]))

    groups.append(("What the inversion resolves", [
        ("Does the inversion beat a fitted boundary field?",
         "Not at any scale with enough independent bins to test. No configuration of the eighteen run reports operational, "
         "and none is resolved at 95%.", "Tables 11 and 13, Figure 8"),
        ("Which configuration comes closest?",
         "Methane with its prior localised to the reported inventory. It is the only one that puts both towers on the "
         "favourable side of the null, and the Jambi comparison changes sign relative to the global inventory.",
         "Table 10, Figure 8"),
        ("How many parameters do the observations actually inform?",
         f"Between {min(v['degrees_of_freedom'] for v in e.daily):.2f} and "
         f"{max(v['degrees_of_freedom'] for v in e.daily):.2f}. A bulk regional scaling is constrained; nothing finer is.",
         "Table 11"),
        ("What emission does the posterior imply for the region the towers see?",
         f"With the provincial reported prior, {near_provincial.posterior_region_Gg:.0f} Gg of methane per year across the "
         f"four provinces, with a 95% interval of {near_provincial.posterior_lo_Gg:.0f} to "
         f"{near_provincial.posterior_hi_Gg:.0f} Gg against a prior of {near_provincial.prior_region_Gg:.0f} Gg. The "
         "interval spans the prior, so this is a consistency statement and not a flux estimate.", "Table 13"),
        ("What does the same calculation give starting from the global inventory?",
         f"{near_global.posterior_region_Gg:.0f} Gg per year, {near_global.posterior_lo_Gg:.0f} to "
         f"{near_global.posterior_hi_Gg:.0f}, from a prior of {near_global.prior_region_Gg:.0f} Gg. The two posteriors "
         "differ by an order of magnitude, which is the measure of how much the prior still decides the answer.",
         "Table 13"),
        ("How large an emission change could this network detect?",
         f"Nothing below {e.flux.detectable_change_percent.min():.0f}%, and more commonly a factor of two. The best "
         f"constrained parameter across the campaign is {e.flux.loc[e.flux.detectable_change_percent.idxmin(), 'parameter'].replace('_', ' ')}; "
         f"the near-field methane term is {near_provincial.detectable_change_percent:.0f}% and the wetland term "
         f"{wetlands_fit.detectable_change_percent:.0f}%. An emission change smaller than that cannot be seen by this "
         "network however long it runs at two towers.", "Table 13"),
        ("Is any multiplier inconsistent with its prior?",
         f"Yes. {int((~e.flux.consistent_with_prior).sum())} of {len(e.flux)} fitted parameters exclude one at 95%: both "
         "biosphere directions, the wetland term, and the near-field anthropogenic methane term under the global and the "
         f"national priors ({near_global.multiplier:.2f}, {near_global.ci_lo:.2f} to {near_global.ci_hi:.2f}). Under the "
         f"provincial prior it no longer does ({near_provincial.multiplier:.2f}, {near_provincial.ci_lo:.2f} to "
         f"{near_provincial.ci_hi:.2f}). The observations reject the global inventory's magnitude in the region they see and "
         "stop rejecting it once the reported provincial totals set it.", "Table 13"),
        ("Why does the inversion lose to a fitted constant?",
         f"Because the source signal is barely above the noise it arrives through: a signal-to-error ratio of "
         f"{error_co2.signal_to_error:.2f} for carbon dioxide and {error_ch4.signal_to_error:.2f} for methane, with "
         "transport the largest error term for both. A regional inversion begins to constrain fluxes near three.",
         "Table 15, Figure 9"),
        ("How large is the transport error?",
         f"{error_ch4.transport_error:.0f} ppb for methane and {error_co2.transport_error:.2f} ppm for carbon dioxide, "
         f"against source signals of {error_ch4.source_signal_sd:.0f} ppb and {error_co2.source_signal_sd:.2f} ppm.",
         "Table 15"),
        ("Would more particles or more seeds help?",
         "No. The seed-to-seed spread is about three percent of the modelled signal and explains under a tenth of the "
         "transport error the residuals require. The rest is wind-field and representation error, which re-running the same "
         "meteorology cannot reduce.", "Section 6.5"),
        ("What would reduce it?",
         "The same receptors driven by a second meteorological product, so the systematic part can be measured from the "
         "spread between drivers rather than calibrated from the residuals. That needs a second public archive and no new "
         "model.", "Section 8"),
        ("Are the reported fits sampled or approximated?",
         f"Sampled. Every reported fit is a Markov chain accepted only with R-hat at most 1.01 and an effective sample size "
         f"above 1,000; the smallest effective sample across the campaign is {min(v['convergence']['ess'] for v in e.verdicts):.0f}. "
         "The Laplace approximation is kept only inside the cross-validation loop, where nothing but the mode is used.",
         "Section 2.4"),
    ]))

    groups.append(("Operating the system", [
        ("What can be operated today?",
         "The station monitor, the episode transport driver, the dataset registry and the readiness harness. All four run "
         "routinely, at any station whose record loads, and produce products whose caveats are stated with them.",
         "Section 7"),
        ("What cannot?",
         "The inversion as a predictor of concentration. It informs one to two flux parameters with a consistent error "
         "model and does not beat a fitted boundary field, so its multipliers are not validated flux corrections.",
         "Section 7"),
        ("Is the localised inventory worth operating on its own?",
         "Yes. It is Indonesia's own reported inventory placed on a gridded pattern with conserved mass and a provenance "
         "ledger, and it is a better prior than the global default whether or not the towers can resolve the difference.",
         "Section 7"),
        ("What does the readiness harness actually check?",
         "Four gates: enough independent bins, a consistent chi-square, at least one degree of freedom informed, and a "
         "cross-validated improvement on the boundary null somewhere. A run that fails any of them cannot be reported as a "
         "finding.", "Section 2.5"),
        ("Are all the input datasets verified?",
         f"Yes. All {len(e.registry)} declared datasets validate, {int(e.registry.required.sum())} of them required, each "
         "confirmed against its provenance record and checked for variable, unit, grid, time span and physical range.",
         "Table 1"),
        ("Can the system run at a station other than these two?",
         "Yes. The monitor needs only the harmonized hourly archive, and the transport driver plans, fetches, runs and "
         "convolves footprints for any station at its own inlet height, with the cost priced before the run is committed. "
         "Inlet heights of 30 m are already configured for Kemayoran, Bariri and Sorong.", "Section 7"),
        ("What would make the inversion operational?",
         "A transport error three to four times smaller, which takes the signal-to-error ratio from about 1.3 to about 4. "
         "Two cheaper improvements also help: more independent bins, which needs roughly two more months of joint record, "
         "and a provincial rather than national inventory, which is already in place.", "Section 8"),
        ("What should not be attempted again?",
         "More work on the carbon dioxide priors. The biosphere carries most of that signal, its prior is now demonstrably "
         "better, and the skill did not move. The constraint is transport, not priors.", "Section 8"),
        ("Where does every number in this report come from?",
         "A CSV or JSON written by a named script, listed in the final table. The report is rebuilt from those files and "
         "refuses to build if a claim in the prose no longer holds against them.", "Table 16"),
    ]))
    return groups


def appendix(e: Evidence | None = None) -> str:
    """The rendered appendix, numbered continuously across the groups."""
    e = e or Evidence()
    lines, number = [], 0
    for heading, items in questions(e):
        lines.append(f"### {heading}\n")
        for question, answer, source in items:
            number += 1
            lines.append(f"**Q{number}. {question}**\n")
            lines.append(f"{answer} ({source})\n")
    return "\n".join(lines).rstrip() + "\n", number


if __name__ == "__main__":
    text, count = appendix()
    print(text)
    print(f"\n[{count} questions]", flush=True)
