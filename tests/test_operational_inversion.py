from __future__ import annotations
import sys, unittest
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import a99_operational_inversion as V  # noqa: E402


def frame(n=24, station="BKT", start="2024-10-01", count=None):
    index = pd.date_range(start, periods=n, freq="D")
    rng = np.random.default_rng(0)
    table = pd.DataFrame(dict(
        station=station, time_utc=index, bin=index,
        anthro_near_ppb=rng.uniform(5, 40, n), anthro_far_ppb=rng.uniform(1, 5, n),
        wetlands_ppb=rng.uniform(2, 20, n), fire_ppb=rng.uniform(0, 1, n),
        base=1850. + rng.normal(0, 2, n), ensemble_sd=rng.uniform(1, 4, n)))
    table["observed"] = table.base + table.anthro_near_ppb + table.anthro_far_ppb + table.wetlands_ppb + table.fire_ppb
    table["count"] = 1 if count is None else count
    return table


class AggregationTests(unittest.TestCase):
    def test_a_bin_holding_one_receptor_is_not_a_mean(self) -> None:
        f = frame(n=10)
        f["time_utc"] = pd.date_range("2024-10-01", periods=10, freq="10D")   # one per month at most
        out = V.aggregate(f, V.CH4, "monthly")
        self.assertTrue((out["count"] >= 2).all())

    def test_averaging_reduces_the_transport_spread_by_root_n(self) -> None:
        f = frame(n=20)
        f["ensemble_sd"] = 4.0
        out = V.aggregate(f, V.CH4, "weekly")
        expected = 4.0 / np.sqrt(out["count"].to_numpy())
        self.assertTrue(np.allclose(out.ensemble_sd.to_numpy(), expected))

    def test_daily_scale_keeps_every_receptor(self) -> None:
        f = frame(n=12)
        self.assertEqual(len(V.aggregate(f, V.CH4, "daily")), 12)


class CovarianceTests(unittest.TestCase):
    def test_independent_error_averages_down_within_a_bin(self) -> None:
        """A bin mean of four receptors carries a quarter of the independent variance."""
        one, four = frame(n=6, count=1), frame(n=6, count=4)
        r1 = V.covariance(one, V.CH4, kappa=0.)      # transport off, isolate the independent part
        r4 = V.covariance(four, V.CH4, kappa=0.)
        independent1 = np.diag(r1) - V.CH4.background ** 2
        independent4 = np.diag(r4) - V.CH4.background ** 2
        self.assertTrue(np.allclose(independent4, independent1 / 4))

    def test_the_background_term_does_not_average_away(self) -> None:
        one, four = frame(n=6, count=1), frame(n=6, count=4)
        off1 = V.covariance(one, V.CH4, 0.)[0, 1]
        off4 = V.covariance(four, V.CH4, 0.)[0, 1]
        self.assertAlmostEqual(off1, off4, places=9)
        self.assertGreater(off1, 0.)

    def test_transport_error_follows_the_measured_spread(self) -> None:
        f = frame(n=5)
        f["ensemble_sd"] = [1., 2., 3., 4., 5.]
        r = V.covariance(f, V.CH4, kappa=2.)
        transport = np.diag(r) - V.CH4.background ** 2 - (V.CH4.measurement ** 2 + V.CH4.local ** 2)
        self.assertTrue(np.allclose(np.sqrt(transport), 2. * np.array([1., 2., 3., 4., 5.])))


class DiagnosticTests(unittest.TestCase):
    def test_degrees_of_freedom_are_zero_when_the_data_say_nothing(self) -> None:
        fit = dict(nsource=3, prior_sd=np.array([1., 1., 1., 5.]),
                   posterior_cov=np.diag([1., 1., 1., 25.]), chi=1.0,
                   names=["a", "b", "c", "offset"])
        diag = V.diagnostics(fit)
        self.assertAlmostEqual(diag["degrees_of_freedom"], 0.0, places=9)
        self.assertEqual(diag["informed_parameters"], 0)

    def test_degrees_of_freedom_count_the_parameters_the_data_pinned(self) -> None:
        fit = dict(nsource=2, prior_sd=np.array([1., 1., 5.]),
                   posterior_cov=np.diag([0.0, 1.0, 25.]), chi=1.0, names=["a", "b", "offset"])
        diag = V.diagnostics(fit)
        self.assertAlmostEqual(diag["degrees_of_freedom"], 1.0, places=9)
        self.assertEqual(diag["informed_parameters"], 1)


class VerdictTests(unittest.TestCase):
    def table(self, lo, hi):
        return pd.DataFrame([dict(station="BKT", ci_lo=lo, ci_hi=hi, rmse_difference=(lo + hi) / 2)])

    def good(self):
        return dict(degrees_of_freedom=2.0, reduced_chi_square=1.0, informed_parameters=2, uncertainty_ratio={})

    def test_too_few_bins_is_unresolved_whatever_the_interval_says(self) -> None:
        """The guard against the mistake this project already made twice."""
        result = V.verdict(V.CO2, "monthly", 5, self.good(), self.table(-3.0, -0.5))
        self.assertIn("unresolved", result["status"])
        self.assertFalse(result["gates"]["enough_independent_bins"])

    def test_beating_the_null_with_enough_bins_is_operational(self) -> None:
        result = V.verdict(V.CO2, "weekly", 20, self.good(), self.table(-1.5, -0.2))
        self.assertEqual(result["status"], "operational")
        self.assertEqual(result["better_at"], ["BKT"])

    def test_informed_but_not_better_is_diagnostic(self) -> None:
        result = V.verdict(V.CO2, "daily", 40, self.good(), self.table(-0.2, 0.6))
        self.assertTrue(result["status"].startswith("diagnostic"))

    def test_uninformative_data_cannot_be_operational(self) -> None:
        weak = dict(degrees_of_freedom=0.2, reduced_chi_square=1.0, informed_parameters=0, uncertainty_ratio={})
        result = V.verdict(V.CO2, "daily", 40, weak, self.table(-1.0, -0.4))
        self.assertNotEqual(result["status"], "operational")

    def test_an_inconsistent_chi_square_blocks_the_verdict(self) -> None:
        bad = dict(degrees_of_freedom=2.0, reduced_chi_square=9.0, informed_parameters=2, uncertainty_ratio={})
        result = V.verdict(V.CO2, "weekly", 20, bad, self.table(-1.5, -0.2))
        self.assertFalse(result["gates"]["chi_square_consistent"])
        self.assertNotEqual(result["status"], "operational")


class GasTests(unittest.TestCase):
    def test_both_gases_are_configured_and_scored_the_same_way(self) -> None:
        self.assertEqual(set(V.GASES), {"co2", "ch4"})
        for gas in V.GASES.values():
            self.assertTrue(gas.components and gas.unit and gas.observed)
            self.assertGreater(gas.multiplier_factor, 1.)

    def test_the_biosphere_pair_is_rotated_into_net_and_contrast(self) -> None:
        """Gross uptake and respiration correlate above 0.9; the net is what the data see."""
        self.assertIn("bio_net_BKT", V.CO2.components)
        self.assertIn("bio_net_JMB", V.CO2.components)
        self.assertNotIn("gpp_BKT", V.CO2.components)

    def test_design_puts_the_unconstrained_contrast_under_a_tight_prior(self) -> None:
        f = frame(n=8)
        f["bio_contrast_BKT_ppm"] = np.linspace(-1, 1, 8)
        gas = V.Gas("t", "ppm", "observed", {"anthro_near": "anthro_near_ppb"}, 0.2, 2., 1., 2., 3., 1.)
        _, b, _, names, sd = V.design(f, gas)
        self.assertIn("bio_contrast_BKT", names)
        self.assertAlmostEqual(sd[names.index("bio_contrast_BKT")], V.CONTRAST_PRIOR)


if __name__ == "__main__":
    unittest.main()
