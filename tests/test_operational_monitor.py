from __future__ import annotations
import sys, unittest
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import a96_cross_validated_scoring as S  # noqa: E402
import a97_operational_monitor as M  # noqa: E402

TABLES = ROOT / "outputs/hysplit/two_receptor/tables"


class RatioTests(unittest.TestCase):
    def test_theil_sen_recovers_a_known_slope(self) -> None:
        x = np.arange(20.)
        self.assertAlmostEqual(M.theil_sen(x, 2.5 * x + 7), 2.5, places=9)

    def test_ratio_interval_brackets_the_slope_and_survives_an_outlier(self) -> None:
        rng = np.random.default_rng(3)
        x = rng.uniform(1, 40, 40)
        y = 60 * x + rng.normal(0, 20, 40)
        slope, lo, hi = M.ratio(x, y)
        self.assertLess(lo, slope); self.assertLess(slope, hi)
        self.assertLess(abs(slope - 60), 10)
        spoiled = M.ratio(np.r_[x, 500.], np.r_[y, 0.])[0]     # one bad hour
        self.assertLess(abs(spoiled - slope), 5)

    def test_ratio_refuses_too_few_hours(self) -> None:
        self.assertTrue(all(np.isnan(v) for v in M.ratio(np.arange(3.), np.arange(3.))))

    def test_classification_boundaries(self) -> None:
        self.assertEqual(M.classify(80.), "combustion, biomass-burning like")
        self.assertEqual(M.classify(25.), "combustion, mixed or urban like")
        self.assertEqual(M.classify(2.), "little combustion signature")
        self.assertEqual(M.classify(float("nan")), "not determined")


class BaselineTests(unittest.TestCase):
    def daily(self, years: int, value: float = 100.) -> pd.Series:
        index = pd.date_range("2018-01-01", periods=365 * years, freq="D")
        return pd.Series(value + 10 * np.sin(np.arange(len(index)) / 365 * 2 * np.pi), index=index)

    def test_climatology_needs_several_years(self) -> None:
        self.assertIsNone(M.climatology(self.daily(2)))
        seasonal = M.climatology(self.daily(4))
        self.assertIsNotNone(seasonal)
        self.assertEqual(len(seasonal), 365)
        self.assertTrue(seasonal.notna().all())

    def test_climatology_ignores_a_single_smoky_season(self) -> None:
        """The reason the climatological baseline exists: one bad year must not become the background."""
        daily = self.daily(5)
        smoky = (daily.index.year == 2020) & (daily.index.month.isin((9, 10)))
        daily[smoky] += 700.
        seasonal = M.climatology(daily)
        october = seasonal.loc[275:300].median()
        june = seasonal.loc[152:180].median()
        self.assertLess(october - june, 60.)          # the smoke did not lift the October level
        rolling = daily.rolling(30, center=True, min_periods=5).quantile(M.BASELINE_QUANTILE)
        self.assertGreater(rolling[smoky].median() - october, 300.)   # the rolling baseline did follow it


class EpisodeTests(unittest.TestCase):
    def frame(self, enhancement: np.ndarray) -> pd.DataFrame:
        index = pd.date_range("2024-09-01", periods=len(enhancement), freq="h")
        return pd.DataFrame(dict(time_utc=index, station="TST", solar_hour=(index.hour + 7) % 24,
                                 afternoon=((index.hour + 7) % 24 >= 12) & ((index.hour + 7) % 24 < 16),
                                 co=100 + enhancement, co_baseline_local=100., co_enhancement=enhancement,
                                 co_reference="climatological",
                                 co2=410 + enhancement / 60, co2_enhancement=enhancement / 60,
                                 ch4=1900 + enhancement / 5, ch4_enhancement=enhancement / 5))

    def test_threshold_is_a_robust_scale_not_a_fixed_share(self) -> None:
        quiet = pd.Series(np.r_[np.zeros(500), np.full(10, 400.)])
        smoky = pd.Series(np.r_[np.zeros(250), np.full(260, 400.)])
        self.assertLess(M.episode_threshold(quiet), M.episode_threshold(smoky))
        self.assertGreaterEqual(M.episode_threshold(pd.Series(np.zeros(100))), M.EPISODE_FLOOR["co"])

    def test_one_plume_becomes_one_episode_with_its_ratio(self) -> None:
        enhancement = np.zeros(240)
        enhancement[100:112] = 600. + 120. * np.sin(np.arange(12) / 3)     # a plume varies; a flat one carries no slope
        found = M.find_episodes(self.frame(enhancement), "TST")
        self.assertEqual(len(found), 1)
        self.assertEqual(int(found.hours.iloc[0]), 12)
        self.assertAlmostEqual(found.co_per_co2_ppb_ppm.iloc[0], 60., places=6)
        self.assertLess(found.co_per_co2_ppb_ppm_lo.iloc[0], 60.0000001)
        self.assertGreater(found.co_per_co2_ppb_ppm_hi.iloc[0], 59.9999999)
        self.assertEqual(found.signature.iloc[0], "combustion, biomass-burning like")
        self.assertFalse(bool(found.sustained.iloc[0]))

    def test_a_perfectly_flat_episode_reports_no_ratio_rather_than_a_wrong_one(self) -> None:
        enhancement = np.zeros(240); enhancement[100:112] = 600.
        found = M.find_episodes(self.frame(enhancement), "TST")
        self.assertEqual(len(found), 1)
        self.assertTrue(np.isnan(found.co_per_co2_ppb_ppm.iloc[0]))
        self.assertEqual(found.signature.iloc[0], "not determined")

    def test_a_short_gap_does_not_split_an_episode(self) -> None:
        enhancement = np.zeros(240)
        enhancement[100:106] = 600.; enhancement[108:114] = 600.      # two hours missing in the middle
        self.assertEqual(len(M.find_episodes(self.frame(enhancement), "TST")), 1)

    def test_a_brief_excursion_is_not_an_episode(self) -> None:
        enhancement = np.zeros(240); enhancement[100:102] = 600.
        self.assertEqual(len(M.find_episodes(self.frame(enhancement), "TST")), 0)

    def test_a_long_event_is_flagged_sustained(self) -> None:
        enhancement = np.zeros(240); enhancement[50:150] = 600.
        found = M.find_episodes(self.frame(enhancement), "TST")
        self.assertTrue(bool(found.sustained.iloc[0]))
        self.assertGreaterEqual(int(found.hours.iloc[0]), M.SUSTAINED_HOURS)


class SharedBootstrapTests(unittest.TestCase):
    def test_reproduces_the_published_carbon_dioxide_intervals(self) -> None:
        """a91 delegates its bootstrap here; the published CO2 numbers must not move."""
        for round_name in ("round5b", "round6", "round7", "round8"):
            predictions = TABLES / f"co2_experiments_{round_name}_cv_predictions.csv"
            stored = TABLES / f"co2_experiments_{round_name}_cv_bootstrap.csv"
            if not predictions.exists() or not stored.exists():
                continue
            fresh = S.date_block_bootstrap(pd.read_csv(predictions, parse_dates=["time_utc"]),
                                           "posterior_ppm", "plain_background_ppm", "observed_ppm")
            published = pd.read_csv(stored).sort_values(["variant", "station"]).reset_index(drop=True)
            fresh = fresh.sort_values(["variant", "station"]).reset_index(drop=True)
            self.assertEqual(list(published.variant), list(fresh.variant))
            for column, name in (("rmse_difference_ppm", "rmse_difference"), ("ci_lo", "ci_lo"), ("ci_hi", "ci_hi")):
                self.assertTrue(np.allclose(published[column], fresh[name], atol=1e-10),
                                f"{round_name} {column} moved")

    def test_ridge_recovers_a_known_offset(self) -> None:
        n = 40
        b = np.c_[np.ones(n), np.zeros(n)]
        y = np.full(n, 12.)
        r = np.eye(n)
        beta = S.ridge(b, y, r, np.ones(n, bool), np.array([20., 10.]))
        self.assertLess(abs(beta[0] - 12.), .1)


if __name__ == "__main__":
    unittest.main()
