from __future__ import annotations
import sys, unittest
from pathlib import Path

import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import a98_episode_transport as E  # noqa: E402
import ghg_common as G  # noqa: E402


class RegistryTests(unittest.TestCase):
    def test_every_archived_station_has_an_inlet_height(self) -> None:
        self.assertEqual(set(G.STATIONS), set(E.INLET_HEIGHT_M))
        for code in G.STATIONS:
            self.assertIn(code, E.INLET_SOURCE, f"{code} has a height but no record of where it came from")
            self.assertGreater(E.INLET_HEIGHT_M[code], 0.)

    def test_config_carries_the_station_position_and_its_own_inlet(self) -> None:
        for code in G.STATIONS:
            name, lat, lon, elevation, inlet = E.station(code)
            cfg = E.config(code, seed=-10)
            self.assertAlmostEqual(cfg.receptor_lat, lat)
            self.assertAlmostEqual(cfg.receptor_lon, lon)
            self.assertAlmostEqual(cfg.station_elevation_m_msl, elevation)
            self.assertAlmostEqual(cfg.receptor_height_m_agl, inlet)
            self.assertEqual(cfg.seed, -10)

    def test_the_supplied_heights_are_the_ones_used(self) -> None:
        self.assertEqual(E.INLET_HEIGHT_M["KMY"], 30.)
        self.assertEqual(E.INLET_HEIGHT_M["PLU"], 30.)
        self.assertEqual(E.INLET_HEIGHT_M["SRG"], 30.)
        self.assertEqual(E.INLET_HEIGHT_M["BKT"], 100.)
        self.assertEqual(E.INLET_HEIGHT_M["JMB"], 100.)

    def test_an_unknown_station_is_refused_rather_than_guessed(self) -> None:
        with self.assertRaises(KeyError):
            E.station("XXX")

    def test_ensemble_settings_match_the_published_campaigns(self) -> None:
        cfg = E.config("SRG")
        reference = E.T.base_config("BKT", 0)
        for field in ("particles", "hours_back", "grid_spacing_deg", "grid_span_lat_deg", "grid_span_lon_deg"):
            self.assertEqual(getattr(cfg, field), getattr(reference, field))


class PlanningTests(unittest.TestCase):
    def planned(self):
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()):       # the plan prints for operators, not for tests
            return E.plan(["JMB"], pd.Timestamp("2023-12-12"), pd.Timestamp("2023-12-13"), "unit_test", "afternoon", 14)

    def test_meteorology_days_reach_back_the_full_trajectory(self) -> None:
        stamps = [pd.Timestamp("2015-10-07T06:00"), pd.Timestamp("2015-10-09T06:00")]
        days = E.meteorology_days(stamps)
        self.assertEqual(days[-1], pd.Timestamp("2015-10-09"))
        self.assertEqual(days[0], pd.Timestamp("2015-10-02"))      # 120 h before the first receptor
        self.assertEqual(len(days), 8)

    def test_no_stamps_means_no_meteorology(self) -> None:
        self.assertEqual(len(E.meteorology_days([])), 0)

    def test_afternoon_selection_keeps_only_well_mixed_hours(self) -> None:
        stamps = E.receptor_hours("BKT", "2023-12-12", "2023-12-14", "afternoon")
        self.assertTrue(stamps)
        for stamp in stamps:
            solar = (stamp.hour + E.station("BKT")[2] / 15) % 24
            self.assertGreaterEqual(solar, E.AFTERNOON_SOLAR[0])
            self.assertLess(solar, E.AFTERNOON_SOLAR[1])
        self.assertGreater(len(E.receptor_hours("BKT", "2023-12-12", "2023-12-14", "all")), len(stamps))

    def test_receptors_require_an_observation(self) -> None:
        """A window before the station existed yields nothing, rather than empty runs."""
        self.assertEqual(E.receptor_hours("JMB", "2019-01-01", "2019-01-03", "all"), [])

    def test_plan_costs_scale_with_what_is_missing(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as scratch:        # never overwrite the working plan
            original, E.PLAN = E.PLAN, Path(scratch) / "plan.csv"
            try:
                table = self.planned()
            finally:
                E.PLAN = original
        self.assertEqual(len(table), 1)
        row = table.iloc[0]
        self.assertEqual(row.runs, row.receptors * len(E.SEEDS))
        self.assertEqual(row.inlet_height_m, 100.)
        expected_gb = round(row.meteorology_days_missing * E.MET_MB_PER_DAY / 1024, 1)
        self.assertAlmostEqual(row.download_gb, expected_gb, places=6)
        self.assertGreater(row.run_hours, 0)

    def test_run_directories_separate_station_seed_and_hour(self) -> None:
        stamp = pd.Timestamp("2015-10-07T06:00")
        a = E.run_dir("lbl", "BKT", 0, stamp)
        b = E.run_dir("lbl", "BKT", -10, stamp)
        c = E.run_dir("lbl", "KMY", 0, stamp)
        self.assertNotEqual(a, b); self.assertNotEqual(a, c)
        self.assertIn("20151007T0600Z", a.name)

    def test_meteorology_paths_cover_the_whole_trajectory(self) -> None:
        paths = E.met_paths("lbl", pd.Timestamp("2015-10-07T06:00"))
        self.assertEqual(len(paths), 6)                      # 120 h back plus the receptor day
        self.assertTrue(all(p.parent.name == "episode_lbl" for p in paths))

    def test_stages_needing_a_plan_refuse_without_one(self) -> None:
        with self.assertRaises((FileNotFoundError, ValueError)):
            E.load_plan("a_label_that_was_never_planned")


if __name__ == "__main__":
    unittest.main()
