from __future__ import annotations
import sys, unittest
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import a75_bkt_revised_inversion as R  # noqa: E402
import a49_bkt_methane_inversion as inv  # noqa: E402

ORIGINAL = ROOT / "outputs/hysplit/inversion/tables/operator_base.csv"


@unittest.skipUnless(ORIGINAL.exists(), "original operator not built")
class ChiSquareTests(unittest.TestCase):
    def setUp(self) -> None:
        frame = pd.read_csv(ORIGINAL, parse_dates=["time_utc"])
        self.frame = frame[frame.transport_usable].reset_index(drop=True)
        self.train = (~self.frame.holdout).to_numpy()

    def test_fixed_covariance_is_oversized_and_scan_is_monotone(self) -> None:
        p, *_ = inv.problem(self.frame, self.train)
        chi = R.reduced_chi_square(p, int(self.train.sum()))
        self.assertLess(chi, 0.7)  # the published covariance leaves whitened residuals well under one
        tuned, table = R.chi_square_scan(self.frame, self.train)
        self.assertTrue((np.diff(table.reduced_chi_square) <= 1e-9).all())
        self.assertTrue(0.05 <= tuned <= 0.5)
        self.assertEqual(int(table.selected.sum()), 1 if tuned in table.transport_fraction.values else 0)


class ComponentMapTests(unittest.TestCase):
    def test_component_maps_scale_linearly(self) -> None:
        times = pd.date_range("2019-09-30T22:00", periods=3, freq="h")
        lat = np.array([-.5, 0.]); lon = np.array([100., 100.5])
        field = xr.DataArray(np.ones((3, 2, 2)), coords={"time": times, "lat": lat, "lon": lon}, dims=("time", "lat", "lon"))
        months = pd.to_datetime(["2019-09-01", "2019-10-01"])
        monthly = xr.Dataset({"flux": (("source", "month", "lat", "lon"), np.array([[np.full((2, 2), 1.), np.full((2, 2), 2.)]]))},
                             coords={"source": ["CH4_WASTE"], "month": months, "lat": lat, "lon": lon})
        days = pd.to_datetime(["2019-09-30", "2019-10-01"])
        fire = xr.Dataset({"noncrop_fire_flux": (("day", "lat", "lon"), np.zeros((2, 2, 2))),
                           "crop_fire_flux": (("day", "lat", "lon"), np.ones((2, 2, 2)))},
                          coords={"day": days, "lat": lat, "lon": lon})
        maps = R.component_maps(field, monthly, fire)
        # two hours in September (flux 1) and one in October (flux 2) per cell, times 1000 ppb/ppm
        self.assertTrue(np.allclose(maps["CH4_WASTE"], 4000.))
        self.assertTrue(np.allclose(maps["crop_fire"], 3000.)); self.assertTrue(np.allclose(maps["noncrop_fire"], 0.))


if __name__ == "__main__":
    unittest.main()
