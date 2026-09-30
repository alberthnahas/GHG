from __future__ import annotations
import sys, unittest
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import a104_biosphere_prior as B  # noqa: E402
import a99_operational_inversion as V  # noqa: E402

HYBRID = ROOT / "outputs/hysplit/two_receptor/inputs_co2/diagnostic_biosphere_hybrid.nc"
REPORT = ROOT / "outputs/operational/biosphere_prior_hybrid_report.json"


class PhaseTests(unittest.TestCase):
    def test_a_normal_biosphere_passes_the_phase_test(self) -> None:
        """Uptake at midday, release at night."""
        solar = np.tile(np.arange(0, 24, 3)[:, None], (1, 4)).astype(float)
        nee = np.where((solar >= 9) & (solar <= 15), -10.0, 2.0)
        self.assertTrue(B.phase_is_correct(nee, solar).all())

    def test_an_inverted_biosphere_fails_it(self) -> None:
        """The documented CarbonTracker defect: carbon released by day, taken up at night."""
        solar = np.tile(np.arange(0, 24, 3)[:, None], (1, 4)).astype(float)
        nee = np.where((solar >= 9) & (solar <= 15), 10.0, -2.0)
        self.assertFalse(B.phase_is_correct(nee, solar).any())

    def test_local_solar_hour_follows_longitude(self) -> None:
        stamps = pd.DatetimeIndex(["2023-12-01T06:00"])
        solar = B.local_solar_hour(stamps, np.array([105.0]))       # seven hours ahead of UTC
        self.assertAlmostEqual(float(solar[0, 0]), 13.0, places=6)


class ConstructionTests(unittest.TestCase):
    @unittest.skipUnless(REPORT.exists(), "hybrid not built")
    def test_the_daily_mean_is_carbontrackers_by_construction(self) -> None:
        import json
        report = json.loads(REPORT.read_text())
        self.assertLess(report["daily_mean_max_error"], 1e-9)

    @unittest.skipUnless(REPORT.exists(), "hybrid not built")
    def test_the_phase_defect_is_removed_not_merely_reduced(self) -> None:
        import json
        report = json.loads(REPORT.read_text())
        self.assertLess(report["phase_failures_on_vegetated_cells"],
                        report["ct_phase_failures_on_vegetated_cells"] / 100)

    @unittest.skipUnless(HYBRID.exists(), "hybrid not built")
    def test_uptake_stays_negative_and_respiration_positive(self) -> None:
        import xarray as xr
        with xr.open_dataset(HYBRID) as ds:
            self.assertLessEqual(float(ds.gpp.max()), 1e-6)
            self.assertGreaterEqual(float(ds.resp.min()), -1e-6)

    @unittest.skipUnless(HYBRID.exists(), "hybrid not built")
    def test_the_amplitude_rescaling_is_bounded_as_declared(self) -> None:
        import xarray as xr
        with xr.open_dataset(HYBRID) as ds:
            scale = ds.amplitude_scale.values
        self.assertGreaterEqual(float(scale.min()), B.AMPLITUDE_LIMITS[0] - 1e-9)
        self.assertLessEqual(float(scale.max()), B.AMPLITUDE_LIMITS[1] + 1e-9)


class BudgetTests(unittest.TestCase):
    def test_the_budget_names_the_dominant_term_for_both_gases(self) -> None:
        table = V.error_budget()
        self.assertEqual(set(table.gas), {"co2", "ch4"})
        for row in table.itertuples():
            self.assertGreater(row.total_error, 0)
            terms = {"transport": row.transport_error, "measurement and local": row.measurement_and_local,
                     "background": row.background}
            self.assertEqual(row.dominant_term, max(terms, key=terms.get))

    def test_the_budget_is_written_for_a_deployment_to_read(self) -> None:
        V.error_budget()
        self.assertTrue((V.OUT / "error_budget.csv").exists())
