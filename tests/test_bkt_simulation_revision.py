from __future__ import annotations
import sys, tempfile, unittest
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import a37_bkt_footprint as F  # noqa: E402
import a74_bkt_simulation_revision as R  # noqa: E402


class LayeredControlTests(unittest.TestCase):
    def test_default_control_unchanged(self) -> None:
        receptor = pd.Timestamp("2019-09-26T01:00"); cfg = F.FootprintConfig(); met = [Path("/tmp/met/x")]
        self.assertEqual(F.control_text(receptor, met, Path("/tmp/run"), cfg),
                         F.control_text(receptor, met, Path("/tmp/run"), cfg, ()))
        self.assertIn("\ncdump\n1\n50\n", F.control_text(receptor, met, Path("/tmp/run"), cfg))

    def test_extra_levels_added_above_stilt_layer(self) -> None:
        text = F.control_text(pd.Timestamp("2019-09-26T01:00"), [Path("/tmp/met/x")], Path("/tmp/run"),
                              F.FootprintConfig(), (1000, 2000))
        self.assertIn("\ncdump\n3\n50 1000 2000\n", text)
        for bad in ((0,), (40,), (2000, 1000), (1000.0,)):
            with self.assertRaises(ValueError):
                F.control_text(pd.Timestamp("2019-09-26T01:00"), [Path("/tmp/met/x")], Path("/tmp/run"),
                               F.FootprintConfig(), bad)

    def test_layer_parser_and_netcdf(self) -> None:
        content = ("YEAR, MO, DA, HR,     LAT,      LON,  FOOT00548,  FOOT01000\n"
                   "2019,  9, 26,  0, -0.2020, 100.3180, 0.5, 0.25\n"
                   "2019,  9, 25, 23, -0.2020, 100.5680, 0.0, 0.75\n")
        receptor = pd.Timestamp("2019-09-26T01:00")
        cfg = F.FootprintConfig(hours_back=6, grid_span_lat_deg=2, grid_span_lon_deg=2)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "footprint.txt"; path.write_text(content)
            frame, columns = F.parse_ascii_layers(path, receptor, 2)
            self.assertEqual(columns, ["FOOT00548", "FOOT01000"])
            self.assertEqual(frame.footprint_sensitivity.tolist(), [0.0, 0.5])
            with self.assertRaises(RuntimeError):
                F.parse_ascii_layers(path, receptor, 1)
            ds = F.write_layer_netcdf(frame, Path(d) / "layers.nc", receptor, cfg, (1000,), columns)
            self.assertEqual(ds.layer_sensitivity.shape, (2, 6, 9, 9))
            self.assertAlmostEqual(float(ds.layer_sensitivity.sel(layer=1).sum()), 0.5)
            self.assertAlmostEqual(float(ds.layer_sensitivity.sel(layer=2).sum()), 1.0)
            single = F.write_netcdf(frame[frame.footprint_sensitivity > 0], Path(d) / "s.nc", receptor, cfg, {"time_utc": "x"})
            self.assertTrue(np.array_equal(single.footprint_sensitivity.values, ds.layer_sensitivity.sel(layer=1).values))


class CampaignTests(unittest.TestCase):
    def test_terrain_height_derivation(self) -> None:
        self.assertEqual(R.TERRAIN_MATCHED_HEIGHT_M, round((864.5 + 30 - R.NEAREST_GFS_TERRAIN_M) / 10) * 10)

    def test_job_counts_and_settings(self) -> None:
        counts = {}
        for name, stamp, cfg in R.jobs("all"):
            counts[name.rsplit("_s", 1)[0]] = counts.get(name.rsplit("_s", 1)[0], 0) + 1
            self.assertEqual(cfg.hours_back, 120); self.assertTrue(cfg.save_endpoints)
            self.assertEqual((cfg.grid_span_lat_deg, cfg.grid_span_lon_deg), (60, 100))
        self.assertEqual(counts["ensemble"], 156); self.assertEqual(counts["terrain_h80"], 12)
        self.assertEqual(counts["afternoon"], 84); self.assertEqual(counts["forward"], 3)
        self.assertEqual(counts["forward_h80"], 1)
        self.assertEqual(R.jobs("all")[0][2].particles, 10000)

    def test_met_paths_cover_window(self) -> None:
        paths = R.met_paths(pd.Timestamp("2019-09-09T06:00"))
        self.assertEqual([p.name for p in paths][0], "20190904_gfs0p25")
        self.assertEqual(len(paths), 6)


if __name__ == "__main__":
    unittest.main()
