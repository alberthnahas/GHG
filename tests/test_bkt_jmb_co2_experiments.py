from __future__ import annotations
import sys, unittest
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import a91_bkt_jmb_co2_experiments as X  # noqa: E402
import a90_bkt_jmb_co2_improved as I  # noqa: E402


def frame(n: int = 12) -> pd.DataFrame:
    rng = np.random.default_rng(5)
    rows = []
    for code in ("BKT", "JMB"):
        times = pd.date_range("2023-12-01T06:00", periods=n, freq="1D")
        rows.append(pd.DataFrame(dict(station=code, time_utc=times, fossil_near_ppm=rng.uniform(.5, 2, n), fossil_far_ppm=rng.uniform(.1, .5, n),
            gpp_ppm=-rng.uniform(20, 40, n), resp_ppm=rng.uniform(20, 40, n), ocean_ppm=0., fire_ppm=0., background_ppm=421.,
            ch4_residual_ppb=rng.normal(0, 30, n))))
    return pd.concat(rows, ignore_index=True)


class ExperimentTests(unittest.TestCase):
    def test_covariate_columns_are_per_tower_with_their_own_prior(self) -> None:
        f = frame()
        k, b, base, names, sd, plain = X.nuisance_design(f, I.DIAG, ["ch4_residual_ppb"])
        self.assertEqual(plain, 4)
        self.assertEqual(names[-2:], ["ch4_residual_ppb_BKT", "ch4_residual_ppb_JMB"])
        self.assertEqual(b.shape[1], 6); self.assertEqual(len(sd), 6)
        self.assertTrue(np.allclose(sd[-2:], X.CH4_COVARIATE_PRIOR))
        jmb = f.station.eq("JMB").to_numpy()
        self.assertTrue((b[jmb, 4] == 0).all() and np.allclose(b[jmb, 5], f.ch4_residual_ppb[jmb]))

    def test_cross_validation_predicts_every_hour_out_of_sample(self) -> None:
        f = frame(8)
        f["co2_afternoon_mean"] = 421. + 0.9 * (f.gpp_ppm + f.resp_ppm) * 0.4 + f.fossil_near_ppm + np.random.default_rng(2).normal(0, .3, len(f))
        f["time_utc"] = pd.to_datetime(f.time_utc)
        rows = X.cross_validate("synthetic", f, I.DIAG, X.C.covariance, [], .2)
        self.assertEqual({r["station"] for r in rows}, {"BKT", "JMB"})
        self.assertTrue(all(r["n"] == 8 and np.isfinite(r["rmse_ppm"]) for r in rows))

    def test_station_specific_covariates_and_per_tower_covariance(self) -> None:
        f = frame()
        f["ch4_enhancement_ppb"] = f.ch4_residual_ppb + 40
        k, b, base, names, sd, plain = X.nuisance_design(f, I.DIAG, ["ch4_residual_ppb@JMB", "ch4_enhancement_ppb@BKT"])
        self.assertEqual(names[-2:], ["ch4_residual_ppb_JMB", "ch4_enhancement_ppb_BKT"])
        bkt = f.station.eq("BKT").to_numpy()
        self.assertTrue((b[bkt, 4] == 0).all() and (b[~bkt, 5] == 0).all())
        cov = X.per_tower_covariance(X.C.covariance, {"BKT": .05, "JMB": .8})
        r = cov(f, k)
        self.assertTrue((r[np.ix_(bkt, ~bkt)] == 0).all())
        self.assertTrue(np.allclose(r[np.ix_(bkt, bkt)], X.C.covariance(f[bkt].reset_index(drop=True), k[bkt], .05)))
        self.assertEqual(X.crossing([.1, .5, 1.], [3., 1., .4]), .5)

    def test_net_covariance_uses_net_signal_with_floor(self) -> None:
        f = frame()
        k, *_ = X.nuisance_design(f, I.DIAG, [])
        r = X.net_covariance(f, k, .5)
        self.assertTrue(np.allclose(r, r.T) and (np.linalg.eigvalsh(r) > 0).all())
        bkt, jmb = f.station.eq("BKT").to_numpy(), f.station.eq("JMB").to_numpy()
        self.assertTrue((r[np.ix_(bkt, jmb)] == 0).all())


class PeriodNuisanceTests(unittest.TestCase):
    def frame(self) -> pd.DataFrame:
        rows = []
        for period, start in (("2023", "2023-12-01"), ("2024", "2024-11-01")):
            for code in ("BKT", "JMB"):
                for day in range(4):
                    rows.append(dict(station=code, period=period, time_utc=pd.Timestamp(start) + pd.Timedelta(days=day)))
        return pd.DataFrame(rows)

    def test_each_period_gets_its_own_offset_and_centred_trend(self) -> None:
        b, names = X.period_nuisance(self.frame())
        self.assertEqual(names, ["offset_BKT_2023", "trend_BKT_2023", "offset_BKT_2024", "trend_BKT_2024",
                                 "offset_JMB_2023", "trend_JMB_2023", "offset_JMB_2024", "trend_JMB_2024"])
        for j, name in enumerate(names):
            if name.startswith("offset"):
                self.assertEqual(b[:, j].sum(), 4)            # one period at one tower
            else:
                inside = b[:, j][b[:, j - 1] > 0]
                self.assertAlmostEqual(float(inside.mean()), 0., places=12)   # centred on its own period
                self.assertLess(abs(inside).max(), .1)                        # days, not months, from the centre
        self.assertTrue(((b[:, 0] > 0) & (b[:, 2] > 0)).sum() == 0)           # periods do not overlap

    def test_single_period_frame_keeps_the_original_design(self) -> None:
        one = self.frame().query("period == '2023'").reset_index(drop=True)
        one = one.assign(**{f"{c}_ppm": 1. for c in X.TOWER_BIO}, background_ppm=420., ocean_ppm=0., fire_ppm=0.,
                         ch4_proxy_ppb=1.)
        plain = X.nuisance_design(one, X.TOWER_BIO, [])
        with_flag = X.nuisance_design(one, X.TOWER_BIO, [], per_period=True)
        self.assertTrue(np.array_equal(plain[1], with_flag[1]))
        self.assertEqual(plain[3], with_flag[3])

    def test_round7_pairs_each_variant_with_its_per_period_twin(self) -> None:
        self.assertEqual(X.ROUND7, ("best_all", "best_all_periods", "best_all_bkt_background", "best_all_periods_bkt_background"))
        for name in X.ROUND7:
            self.assertIn(name, X.OPTIONS)
            self.assertEqual(X.OPTIONS[name]["period"], "all")
        self.assertTrue(all(X.OPTIONS[n].get("per_period") for n in X.ROUND7 if "periods" in n))
        self.assertFalse(any(X.OPTIONS[n].get("per_period") for n in X.ROUND7 if "periods" not in n))


if __name__ == "__main__":
    unittest.main()
