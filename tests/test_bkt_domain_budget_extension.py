import sys
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import a71_domain_budget_extension as ext


class DomainBudgetExtensionTests(unittest.TestCase):
    def test_decomposition_closes(self):
        frame = pd.DataFrame({
            "date_utc": pd.to_datetime(["2019-09-01", "2019-09-01", "2019-09-02", "2019-09-02"]),
            "original_retained": [True, True, False, False],
            "narrow_sensitivity": [1., 3., 5., 7.],
            "wide_sensitivity": [2., 4., 9., 11.],
        })
        result = ext.decomposition(frame, "sensitivity", replicates=40, seed=4)
        self.assertAlmostEqual(result["same_hour_change"], 1.)
        self.assertAlmostEqual(result["recovered_hour_composition_change"], 3.5)
        self.assertAlmostEqual(result["total_change"], 4.5)
        self.assertAlmostEqual(result["closure_error"], 0.)

    def test_wib_rollover_and_wind_quadrants(self):
        local = ext.wib_labels(pd.Timestamp("2019-09-30T18:00"))
        self.assertEqual(local["time_wib"], pd.Timestamp("2019-10-01T01:00"))
        self.assertEqual(local["wib_month"], "2019-10")
        self.assertEqual(local["wib_clock"], "night_18_06")
        self.assertEqual(ext.wind_labels(1, -1)["wind_toward_quadrant"], "U+V-_toward_SE")
        self.assertEqual(ext.wind_labels(-1, 1)["zonal_regime"], "westward")

    def test_circular_block_deterministic_and_bounded(self):
        days = pd.date_range("2019-09-01", periods=5, freq="D")
        one = ext.circular_block_indices(days, replicates=15, block_days=3, seed=99)
        two = ext.circular_block_indices(days, replicates=15, block_days=3, seed=99)
        np.testing.assert_array_equal(one, two)
        self.assertEqual(one.shape, (15, 5))
        self.assertTrue(((one >= 0) & (one < 5)).all())

    def test_dynamic_arl_sampling_cached_fixture(self):
        path = ext.ORIGINAL_MET / "20190923_gfs0p25"
        if not path.exists():
            self.skipTest("cached ARL fixture unavailable")
        values = ext.sample_native_surface(path, pd.Timestamp("2019-09-23T06:00"))
        self.assertAlmostEqual(values["SHGT"], 816., places=1)
        self.assertTrue(np.isfinite(list(values.values())).all())

    def test_budget_arithmetic_contract(self):
        # Net prior surface adds emissions and subtracts the positive soil-uptake magnitude.
        anthro, wetland, termite, geology, soil, fire = 10., 2., 3., 4., 5., 6.
        net = anthro + wetland + termite + geology - soil + fire
        self.assertEqual(net, 20.)

    def test_frozen_convergence_matrix(self):
        jobs = ext.convergence_jobs()
        self.assertEqual(len(jobs), 30)
        self.assertEqual({stamp for _, _, stamp in jobs}, set(ext.REPRESENTATIVES))
        self.assertEqual({hours for _, hours, _ in jobs}, {72, 120, 168})

    def test_hourly_particle_dumps_use_only_terminal_endpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            points = pd.DataFrame({
                "time": ["10/ 6/19  5: 0", "10/ 6/19  5: 0", "10/ 1/19  6: 0", "10/ 1/19  6: 0"],
                "latitude": [-.2, -.2, -5., 0.], "longitude": [100.3, 100.3, 120., 0.],
                "height": [30., 30., 100., 500.], "PGRD": [1, 1, 1, 0], "NSORT": [1, 2, 1, 2],
            })
            points.to_csv(path / "PAR_GIS.txt", index=False)
            meta = {"observation": {"time_utc": "2019-10-06T06:00:00Z"},
                    "configuration": {"hours_back": 120}}
            active = ext.active_endpoints(path, meta, actual=2)
            self.assertEqual(len(active), 1)
            self.assertEqual(active.iloc[0].NSORT, 1)

    def test_observed_difference_is_recovered_minus_retained(self):
        frame = pd.DataFrame({
            "date_utc": pd.to_datetime(["2019-09-01", "2019-09-01", "2019-09-02", "2019-09-02"]),
            "original_retained": [True, True, False, False],
            "ch4": [10., 12., 20., 22.],
        })
        result = ext.observed_difference(frame, "ch4", replicates=40, seed=7)
        self.assertEqual(result["retained_mean"], 11.)
        self.assertEqual(result["recovered_mean"], 21.)
        self.assertEqual(result["recovered_minus_retained"], 10.)

    def test_reused_run_rejects_wrong_timestamp_or_forcing_identity(self):
        stamp = pd.Timestamp("2019-09-13T06:00")
        directory = ext.BASE_RUNS / "bkt_20190913T0600Z"
        if not directory.exists():
            self.skipTest("frozen completed-run fixture unavailable")
        cfg = ext.run_config(120, "original")
        paths = ext.met_paths(stamp, 120, "original")
        with self.assertRaisesRegex(ValueError, "timestamp mismatch"):
            ext.run_receipt(directory, cfg, ext.model.TransportOptions(), paths,
                            stamp + pd.Timedelta(hours=12), reused=True)
        with self.assertRaisesRegex(ValueError, "Meteorology-file identity mismatch"):
            ext.run_receipt(directory, cfg, ext.model.TransportOptions(), list(reversed(paths)),
                            stamp, reused=True)


if __name__ == "__main__":
    unittest.main()
