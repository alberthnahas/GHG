from __future__ import annotations
import sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import a76_bkt_era5_driver as E  # noqa: E402

WIDE = ROOT / "data/hysplit/gfs0p25/benchmark_wide/20190923_gfs0p25"


class Era5DriverTests(unittest.TestCase):
    def test_days_cover_anchor_and_forward_windows(self) -> None:
        days = [str(d.date()) for d in E.needed_days()]
        self.assertEqual(len(days), 15)
        self.assertEqual(days[0], "2019-09-04"); self.assertEqual(days[-1], "2019-09-26")
        self.assertNotIn("2019-09-12", days)

    def test_requests_and_jobs(self) -> None:
        dataset, body = E.request("pl", E.needed_days()[0])
        self.assertEqual(dataset, "reanalysis-era5-pressure-levels")
        self.assertEqual(len(body["pressure_level"]), 16); self.assertEqual(len(body["time"]), 24)
        self.assertEqual(body["area"], [20, 70, -25, 140])
        self.assertEqual(len(E.jobs()), 15)
        self.assertTrue(all(cfg.meteorology_label == E.LABEL for _, _, cfg in E.jobs()))
        self.assertTrue(all((cfg.grid_span_lat_deg, cfg.grid_span_lon_deg) == (40, 60) for _, _, cfg in E.jobs()))
        self.assertIn("plev = 1000, 950", E.CFG % (16, ", ".join(map(str, E.LEVELS))))

    @unittest.skipUnless(WIDE.exists(), "wide GFS archive not present")
    def test_arl_header_parser_on_gfs(self) -> None:
        h = E.arl_header(WIDE)
        self.assertEqual(h["model"], "GFSQ"); self.assertEqual(h["spacing"], [.25, .25])
        self.assertTrue(h["whole_records"]); self.assertEqual(h["nz"], 56)


if __name__ == "__main__":
    unittest.main()
