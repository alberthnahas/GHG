"""The attribution tables have to be internally consistent, not merely present.

Each check here is a way one of these tables could be wrong while still looking
plausible: a share that does not add up, a masked subset larger than the whole,
a unit slip of a thousand between nmol and umol, or a component read from the
wrong gas because both budgets carry a row called fire.
"""
import re
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
OPERATIONAL = ROOT / "outputs/operational"


def table(name):
    return pd.read_csv(OPERATIONAL / f"attribution_{name}.csv")


class Attribution(unittest.TestCase):

    def test_distance_bands_partition_each_quantity(self):
        distance = table("distance")
        for (station, quantity), block in distance.groupby(["station", "quantity"]):
            self.assertAlmostEqual(block.share_percent.sum(), 100.0, delta=0.6,
                                   msg=f"{station} {quantity} bands do not partition the total")

    def test_age_bands_partition_the_sensitivity(self):
        age = table("age")
        bands = age[~age.age_hours.str.startswith("median")]
        for station, block in bands.groupby("station"):
            self.assertAlmostEqual(block.sensitivity_share_percent.sum(), 100.0, delta=0.6)

    def test_regions_are_disjoint_and_nearly_complete(self):
        for level in ("provinces", "districts"):
            for station, block in table(level).groupby("station"):
                total = block.share_percent.sum()
                self.assertLessEqual(total, 100.5, f"{level} at {station} double counts")
                self.assertGreater(total, 80.0, f"{level} at {station} loses too much offshore")

    def test_peat_is_a_subset_of_the_whole(self):
        peat = table("peat")
        for row in peat.itertuples():
            self.assertLessEqual(row.over_peat_mean, row.total_mean * 1.0001,
                                 f"{row.station} {row.quantity}: the peat part exceeds the total")
            self.assertGreaterEqual(row.over_peat_max, row.over_peat_mean,
                                    f"{row.station} {row.quantity}: the largest receptor is below the mean")

    def test_peat_routes_sum_to_the_combined_row(self):
        peat = table("peat").set_index(["station", "quantity"])
        routes = ["anthropogenic", "wetlands", "fire", "FOLU_land_use_fire"]
        for station in ("BKT", "JMB"):
            parts = sum(float(peat.loc[(station, route), "over_peat_mean"]) for route in routes)
            combined = float(peat.loc[(station, "all peat routes combined"), "over_peat_mean"])
            self.assertAlmostEqual(parts, combined, delta=0.05 * combined)

    def test_budget_shares_add_up_within_each_gas(self):
        budget = table("budget")
        for (station, gas), block in budget.groupby(["station", "gas"]):
            shares = block.share_percent.dropna()
            self.assertAlmostEqual(shares.sum(), 100.0, delta=0.6, msg=f"{station} {gas}")

    def test_both_gases_carry_a_component_called_fire(self):
        # the reason Evidence.component takes a gas: reading the wrong one is silent
        budget = table("budget")
        names = {gas: set(block.component) for gas, block in budget.groupby("gas")}
        self.assertTrue(names["CH4"] & names["CO2"], "the two budgets share no component name, so the guard is stale")

    def test_methane_response_is_in_parts_per_billion(self):
        # a nmol/umol slip is a factor of a thousand and would leave the totals absurd
        records = table("records").set_index(["gas", "station"])
        for station in ("BKT", "JMB"):
            signal = float(records.loc[("CH4", station), "modelled_source_signal"])
            self.assertTrue(10 < signal < 1000, f"{station} modelled methane signal of {signal} is not ppb-scaled")
            carbon = abs(float(records.loc[("CO2", station), "modelled_source_signal"]))
            self.assertLess(carbon, 100, f"{station} modelled carbon dioxide signal of {carbon} is not ppm-scaled")

    def test_posterior_emission_brackets_are_ordered(self):
        flux = table("flux")
        priced = flux[flux.prior_region_Gg.notna()]
        self.assertTrue(len(priced) >= 6, "no parameter carries an inventory total")
        self.assertTrue((priced.posterior_lo_Gg <= priced.posterior_region_Gg).all())
        self.assertTrue((priced.posterior_region_Gg <= priced.posterior_hi_Gg).all())
        implied = priced.posterior_region_Gg / priced.prior_region_Gg
        self.assertTrue(np.allclose(implied, priced.multiplier, rtol=0.01),
                        "the implied emission is not the prior times the multiplier")

    def test_detection_limit_matches_the_interval(self):
        flux = table("flux")
        # the stored interval is rounded to three decimals and the limit was not, so
        # recomputing from the table agrees to a few tenths of a percent, not exactly
        expected = 2 * (np.log(flux.ci_hi) - np.log(flux.ci_lo)) / (2 * 1.959964) * 100
        self.assertTrue(np.allclose(flux.detectable_change_percent, expected, atol=0.5))

    def test_the_question_index_is_generated_not_typed(self):
        import a111_report_questions as Q
        text, count = Q.appendix()
        self.assertGreaterEqual(count, 50)
        self.assertEqual(text.count("**Q"), count)
        self.assertNotIn("{", text)
        # "Indonesian" and "provenance" contain the letters, so only a bare token counts
        self.assertIsNone(re.search(r"\bnan\b", text))
        self.assertIsNone(re.search(r"\bNone\b", text))


if __name__ == "__main__":
    unittest.main()
