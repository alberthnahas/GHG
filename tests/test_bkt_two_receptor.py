from __future__ import annotations
import sys, unittest
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import a84_bkt_jmb_two_receptor as T  # noqa: E402
import a71_domain_budget_extension as ext  # noqa: E402
import a88_jambi_peat_tests as P  # noqa: E402


def synthetic_frame(n: int = 24) -> pd.DataFrame:
    rng = np.random.default_rng(1)
    rows = []
    for code in ("BKT", "JMB"):
        times = pd.date_range("2023-12-01T06:00", periods=n, freq="12h")
        rows.append(pd.DataFrame(dict(station=code, time_utc=times,
            anthro_near_ppb=rng.uniform(5, 40, n), anthro_far_ppb=rng.uniform(2, 10, n), wetlands_ppb=rng.uniform(1, 20, n),
            fire_ppb=rng.uniform(0, 3, n), fuel_near_ppb=rng.uniform(0, 5, n), termites_ppb=.5, geological_ppb=.3, soil_uptake_ppb=.2,
            background_ppb=1900 + rng.normal(0, 5, n), ch4=1950 + rng.normal(0, 20, n))))
    frame = pd.concat(rows, ignore_index=True)
    frame["other_near_ppb"] = frame.anthro_near_ppb - frame.fuel_near_ppb
    return frame


class DesignTests(unittest.TestCase):
    def test_station_nuisance_columns_and_block_covariance(self) -> None:
        frame = synthetic_frame()
        k, b, base, names = T.design(frame)
        self.assertEqual(names, ["offset_BKT", "trend_BKT", "offset_JMB", "trend_JMB"])
        self.assertEqual(k.shape, (48, 4)); self.assertEqual(b.shape, (48, 4))
        self.assertTrue(np.array_equal(b[:, 0], frame.station.eq("BKT")))
        self.assertTrue((b[frame.station.eq("BKT"), 2:] == 0).all())
        r = T.covariance(frame, k, .2)
        bkt, jmb = frame.station.eq("BKT").to_numpy(), frame.station.eq("JMB").to_numpy()
        self.assertTrue((r[np.ix_(bkt, jmb)] == 0).all())
        self.assertTrue(np.allclose(r, r.T)); self.assertTrue((np.linalg.eigvalsh(r) > 0).all())

    def test_sector_design_reconstructs_the_near_field(self) -> None:
        frame = synthetic_frame()
        k, b, base, names = T.design(frame, T.SECTOR_COMPONENTS)
        self.assertEqual(k.shape[1], 5)
        self.assertTrue(np.allclose(k[:, 0] + k[:, 1], frame.anthro_near_ppb))
        k4, b4, base4, _ = T.design(frame)
        self.assertTrue(np.allclose(base, base4)); self.assertTrue(np.array_equal(b, b4))

    def test_selection_window_is_the_2023_joint_window(self) -> None:
        self.assertEqual((T.WINDOW[0].year, T.WINDOW[1].year), (2023, 2023))
        self.assertEqual(T.INLET_HEIGHT_M, 100.0)
        self.assertTrue(T.MET_DAYS[0] <= T.WINDOW[0] - pd.Timedelta(hours=T.HOURS_BACK))
        for code in T.STATIONS:
            cfg = T.base_config(code, -10)
            self.assertEqual((cfg.receptor_lat, cfg.receptor_lon), T.STATIONS[code][1:3])
            self.assertEqual(cfg.receptor_height_m_agl, 100.0); self.assertEqual(cfg.seed, -10)
        self.assertNotEqual(T.run_dir("BKT", 0, T.WINDOW[0]), T.run_dir("JMB", 0, T.WINDOW[0]))


class PeatTests(unittest.TestCase):
    def test_one_cell_polygon_rasterizes_to_one_cell(self) -> None:
        import geopandas as gpd
        from shapely.geometry import box
        lat, lon = T.receptor_grid("JMB")
        i, j = 120, 200
        cell = gpd.GeoSeries([box(lon[j] - .125, lat[i] - .125, lon[j] + .125, lat[i] + .125)], crs="EPSG:4326")
        frac = P.peat_fraction("JMB", cell)
        self.assertAlmostEqual(float(frac.isel(lat=i, lon=j)), 1.0, places=6)
        self.assertAlmostEqual(float(frac.sum()), 1.0, places=6)

    def test_block_median_of_identical_weeks(self) -> None:
        values = pd.Series([1., 2., 3., 1., 2., 3.]); weeks = pd.Series(["a", "a", "a", "b", "b", "b"])
        boot = P.block_median(values, weeks, np.random.default_rng(0), reps=50)
        self.assertTrue(np.allclose(boot, 2.0))


@unittest.skipUnless((ROOT / "data/bkt_sources/edgar_v8/CH4_WASTE_2019.nc").exists(), "2019 sources absent")
class PriorTests(unittest.TestCase):
    def test_monthly_inputs_reproduce_the_2019_builder_on_a_small_grid(self) -> None:
        lat = np.arange(-2., 1.01, .25); lon = np.arange(99., 105.01, .25)
        saved = (T.EDGAR_YEAR, T.LPJ_YEAR, T.MONTHS)
        try:
            T.EDGAR_YEAR, T.LPJ_YEAR = 2019, 2019
            T.MONTHS = pd.to_datetime(["2019-09-01", "2019-10-01"])
            ours = T.monthly_inputs(lat, lon)
        finally:
            T.EDGAR_YEAR, T.LPJ_YEAR, T.MONTHS = saved
        theirs = ext.monthly_inputs(lat, lon)
        self.assertEqual(list(ours.source.values), list(theirs.source.values))
        self.assertTrue(np.allclose(ours.flux.values, theirs.flux.values))

    def test_fire_inputs_convert_carbontracker_units(self) -> None:
        lat = np.arange(-2., 1.01, .25); lon = np.arange(99., 105.01, .25)
        saved = (T.LPJ_YEAR, T.MET_DAYS)
        try:
            T.LPJ_YEAR = 2019
            T.MET_DAYS = pd.date_range("2019-09-20", "2019-09-22", freq="D")
            fire = T.fire_inputs(lat, lon)
        finally:
            T.LPJ_YEAR, T.MET_DAYS = saved
        self.assertEqual(fire.sizes["day"], 9)
        self.assertTrue((fire.crop_fire_flux.values == 0).all())
        self.assertTrue((fire.noncrop_fire_flux.values >= 0).all())
        self.assertLess(float(fire.all_fire_flux.max()), 1.0)  # umol m-2 s-1; 2019 Sumatra fires are large but bounded


if __name__ == "__main__":
    unittest.main()
