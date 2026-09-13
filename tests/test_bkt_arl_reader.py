from __future__ import annotations
import sys, unittest
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from bkt_arl import ARLReader, GFSReader  # noqa: E402

GFS = ROOT / "data/hysplit/gfs0p25/regional/20190909_gfs0p25"
ERA5 = ROOT / "data/hysplit/era5/arl/20190909_era5"


class ARLReaderTests(unittest.TestCase):
    @unittest.skipUnless(GFS.exists(), "GFS file absent")
    def test_generic_reader_matches_gfs_reader(self) -> None:
        g, a = GFSReader(GFS), ARLReader(GFS)
        self.assertEqual((a.nx, a.ny, a.nz), (g.nx, g.ny, g.nz)); self.assertEqual(a.records_per_time, g.records_per_time)
        t = pd.Timestamp("2019-09-09T06:00")
        for var in ("SHGT", "PBLH", "T02M"):
            self.assertAlmostEqual(a.point(t, var, 0, -.202, 100.318, "nearest"), g.point(t, var, 0, -.202, 100.318, "nearest"), places=6)
        self.assertTrue(np.array_equal(a.field(t, "TEMP", 5), g.field(t, "TEMP", 5)))

    @unittest.skipUnless(ERA5.exists(), "ERA5 file absent")
    def test_era5_file(self) -> None:
        a = ARLReader(ERA5)
        self.assertEqual(a.model, "ERA5"); self.assertEqual((a.nx, a.ny, a.nz), (281, 181, 17))
        self.assertEqual(len(a.times), 24); self.assertEqual(a.records_per_time, 128)
        self.assertEqual(a.levels[0][1][:3], ["T02M", "V10M", "U10M"]); self.assertEqual(a.levels[1][0], 1000.0)
        t = pd.Timestamp("2019-09-09T06:00")
        self.assertTrue(600 < a.point(t, "SHGT", 0, -.202, 100.318, "nearest") < 900)
        self.assertTrue(0 < a.point(t, "PBLH", 0, -.202, 100.318, "nearest") < 3000)
        self.assertGreater(a.point(t, "SHTF", 0, -.202, 100.318, "nearest"), 0)  # upward-positive after the sign fix


if __name__ == "__main__":
    unittest.main()
