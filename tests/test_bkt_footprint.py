from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import a37_bkt_footprint as F  # noqa: E402


class BktFootprintTests(unittest.TestCase):
    def test_week_names_and_boundary(self) -> None:
        self.assertEqual(F.gdas1_week_name(pd.Timestamp("2019-09-26")), "gdas1.sep19.w4")
        names = F.required_met_names(pd.Timestamp("2019-09-29T01:00"), 48)
        self.assertEqual(names, ["gdas1.sep19.w4", "gdas1.sep19.w5"])

    def test_gdas_url(self) -> None:
        self.assertEqual(
            F.gdas1_url("gdas1.sep19.w4"),
            "https://noaa-oar-arl-hysplit-pds.s3.amazonaws.com/gdas1/2019/gdas1.sep19.w4",
        )
        with self.assertRaises(ValueError):
            F.gdas1_url("../../secret")

    def test_control_and_stilt_configuration(self) -> None:
        receptor = pd.Timestamp("2019-09-26T01:00")
        config = F.FootprintConfig()
        met = Path("/tmp/met/gdas1.sep19.w4")
        text = F.control_text(receptor, [met], Path("/tmp/run"), config)
        self.assertIn("19 09 26 01\n1\n-0.202000 100.318000 30.0\n-72\n", text)
        self.assertIn("\n50\n19 09 26 01 00\n19 09 23 01 00\n0 01 00\n", text)
        setup = F.setup_text(config)
        for setting in ("ICHEM = 8", "IDSP = 2", "KBLT = 5", "KMIXD = 3",
                        "VSCALES = -1.0", "CAPEMIN = -2.0", "OUTDT = -1"):
            self.assertIn(setting, setup)

    def test_exact_observation_is_harmonised(self) -> None:
        obs = F.observation_at(pd.Timestamp("2019-09-26T01:00"))
        self.assertEqual(obs["time_local_wib"], "2019-09-26T08:00:00")
        self.assertAlmostEqual(obs["co2_ppm"], 437.09, places=2)
        self.assertAlmostEqual(obs["ch4_ppb"], 1922.06, places=2)
        self.assertAlmostEqual(obs["co_ppb"], 531.15, places=2)

    def test_parse_ascii_rejects_negative_sensitivity(self) -> None:
        content = (
            "YEAR, MO, DA, HR, LAT, LON, FOOT00050\n"
            "2019, 9, 26, 0, -0.2020, 100.3180, -1.0E-12\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "footprint.txt"
            path.write_text(content, encoding="ascii")
            with self.assertRaisesRegex(RuntimeError, "negative"):
                F.parse_ascii_footprint(path, pd.Timestamp("2019-09-26T01:00"))

    def test_hourly_grid_covers_backward_intervals(self) -> None:
        frame = pd.DataFrame({
            "time_utc": [pd.Timestamp("2019-09-25T19:00"), pd.Timestamp("2019-09-26T00:00")],
            "lag_hours": [6.0, 1.0],
            "LAT": [-0.202, -0.202],
            "LON": [100.318, 100.318],
            "footprint_sensitivity": [1.0, 2.0],
        })
        config = F.FootprintConfig(hours_back=6, grid_span_lat_deg=2,
                                   grid_span_lon_deg=2)
        obs = {"time_utc": "2019-09-26T01:00:00Z"}
        with tempfile.TemporaryDirectory() as directory:
            dataset = F.write_netcdf(
                frame, Path(directory) / "footprint.nc",
                pd.Timestamp("2019-09-26T01:00"), config, obs,
            )
            self.assertEqual(len(dataset.time), 6)
            self.assertEqual(str(dataset.time.min().values)[:13], "2019-09-25T19")
            self.assertEqual(str(dataset.time.max().values)[:13], "2019-09-26T00")
            self.assertAlmostEqual(float(dataset.footprint_sensitivity.sum()), 3.0)


if __name__ == "__main__":
    unittest.main()
