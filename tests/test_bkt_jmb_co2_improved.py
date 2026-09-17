from __future__ import annotations
import sys, unittest
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import a90_bkt_jmb_co2_improved as I  # noqa: E402


class RadiationTests(unittest.TestCase):
    def test_deaccumulation_recovers_three_hour_means(self) -> None:
        stamps = pd.date_range("2023-12-01T00:00", periods=5, freq="3h")    # 00 03 06 09 12
        true = np.array([np.nan, 100., 500., 300., 50.])                    # means ending at each stamp
        stored = np.array([7., 100., (100 + 500) / 2, 300., (300 + 50) / 2])  # 3 h at 03, 09; 6 h at 06, 12
        out = I.deaccumulate(stored[:, None, None], stamps)[:, 0, 0]
        self.assertTrue(np.isnan(out[0]))
        self.assertTrue(np.allclose(out[1:], true[1:]))

    def test_interval_and_temperature_indexing(self) -> None:
        hours = pd.to_datetime(["2023-12-01T05:00", "2023-12-01T06:00", "2023-12-01T23:00"])
        self.assertEqual(list(I.interval_end(hours)), list(pd.to_datetime(["2023-12-01T06:00", "2023-12-01T09:00", "2023-12-02T00:00"])))
        stamps = pd.date_range("2023-12-01T00:00", periods=10, freq="3h")
        i0, i1, w1 = I.temperature_weights(hours[:2], stamps)
        self.assertEqual((list(i0), list(i1)), ([1, 2], [2, 3]))
        self.assertTrue(np.allclose(w1, [2.5 / 3, .5 / 3]))


class BiosphereTests(unittest.TestCase):
    def test_fraction_on_grid(self) -> None:
        src_lat = np.arange(-.225, .25, .05); src_lon = np.arange(100.025, 100.5, .05)   # 10 x 10 cells, 0.05 degree
        mask = np.zeros((10, 10)); mask[:, :5] = 1
        lat = np.array([-.125, .125]); lon = np.array([100.125, 100.375])
        frac = I.fraction_on_grid(mask, src_lat, src_lon, lat, lon)
        self.assertTrue(np.allclose(frac, [[1, 0], [1, 0]], atol=1e-9))

    def test_uptake_and_respiration_balance_with_correct_phase(self) -> None:
        stamps = pd.date_range("2023-12-01T03:00", periods=16, freq="3h")
        rng = np.random.default_rng(1)
        sw = np.clip(np.sin((np.arange(16) % 8) / 8 * 2 * np.pi), 0, None)[:, None, None] * 600 * rng.uniform(.5, 1, (1, 2, 3))
        temp = 297 + 3 * np.sin((np.arange(16) % 8) / 8 * 2 * np.pi)[:, None, None] * np.ones((1, 2, 3))
        veg = np.array([[1., .5, 0.], [1., 1., .2]])
        gpp, resp = I.biosphere_fields(sw, temp, veg)
        self.assertTrue((gpp <= 0).all() and (resp >= 0).all())
        self.assertTrue(np.allclose(gpp.mean(axis=0) + resp.mean(axis=0), 0, atol=1e-9))
        self.assertTrue(np.allclose(resp.mean(axis=0), veg * I.GPP_REF_UMOL))
        self.assertTrue(np.all(gpp[sw[:, 0, 0] == 0][:, 0, 0] == 0))

    def test_saturating_light_and_q10_variants_stay_balanced(self) -> None:
        sw = np.array([0., 200., 800., 400., 0., 0.])[:, None, None] * np.ones((1, 1, 2))
        temp = np.array([295., 300., 303., 301., 297., 296.])[:, None, None] * np.ones((1, 1, 2))
        veg = np.array([[1., .6]])
        linear, _ = I.biosphere_fields(sw, temp, veg)
        saturating, resp2 = I.biosphere_fields(sw, temp, veg, q10=2.0, k_light=250.)
        self.assertTrue(np.allclose(saturating.mean(axis=0) + resp2.mean(axis=0), 0, atol=1e-9))
        self.assertLess(saturating[2, 0, 0] / saturating[1, 0, 0], linear[2, 0, 0] / linear[1, 0, 0])   # flatter midday peak
        self.assertGreater(resp2[2, 0, 0] / resp2[0, 0, 0], 1.0)

    def test_hourly_spike_flag_spares_clean_neighbours(self) -> None:
        index = pd.date_range("2023-11-26T03:00", periods=7, freq="h")     # Jambi, 26 November 2023
        record = pd.DataFrame(dict(co2=[423.04, 422.88, 419.28, 509.83, 443.15, 423.16, 418.77],
                                   ch4=[2010., 1974, 1944, 1942, 1946, 1963, 2008], co=[220., 199, 180, 189, 198, 205, 237]), index=index)
        flags = I.hourly_spikes(record)
        self.assertTrue(flags.iloc[3] and flags.iloc[4])      # 06 and 07 UTC
        self.assertFalse(flags.iloc[2])                        # 05 UTC is clean

if __name__ == "__main__":
    unittest.main()
