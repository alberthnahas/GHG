from __future__ import annotations
import sys, unittest
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import a89_bkt_jmb_co2 as C  # noqa: E402
import a84_bkt_jmb_two_receptor as T  # noqa: E402


class HelperTests(unittest.TestCase):
    def test_three_hour_centers_match_ct_nrt_stamps(self) -> None:
        hours = pd.to_datetime(["2023-12-01T00:00", "2023-12-01T02:00", "2023-12-01T03:00", "2023-12-01T05:00", "2023-12-01T23:00"])
        expected = pd.to_datetime(["2023-12-01T01:30", "2023-12-01T01:30", "2023-12-01T04:30", "2023-12-01T04:30", "2023-12-01T22:30"])
        self.assertTrue(np.array_equal(C.three_hour_center(hours), expected))

    def test_nee_split_conserves_net_flux(self) -> None:
        nee = np.array([[-3., 0., 2.5], [1e-9, -1e-9, 4.]])
        release, uptake = C.split_nee(nee)
        self.assertTrue((release >= 0).all() and (uptake >= 0).all())
        self.assertTrue(np.allclose(release - uptake, nee))
        self.assertTrue(((release == 0) | (uptake == 0)).all())

    def test_solar_day_mask_follows_longitude(self) -> None:
        times = pd.to_datetime(["2023-11-27T04:30", "2023-11-27T13:30"])
        mask = C.solar_day_mask(times, np.array([100.5, -60.5]))
        self.assertTrue(mask[0, 0] and not mask[1, 0])      # 11:12 and 20:12 local solar time at 100.5 E
        self.assertTrue(not mask[0, 1] and mask[1, 1])      # 00:28 and 09:28 local solar time at 60.5 W

    def test_aggregation_conserves_footprint_mass(self) -> None:
        lat, lon = T.receptor_grid("JMB")
        box_lat = np.arange(C.BOX["lat"][0] + .5, C.BOX["lat"][1], 1.)
        box_lon = np.arange(C.BOX["lon"][0] + .5, C.BOX["lon"][1], 1.)
        m_lat, m_lon = C.overlap_matrix(lat, box_lat, True), C.overlap_matrix(lon, box_lon)
        field = np.random.default_rng(3).random((3, len(lat), len(lon)))
        coarse = C.aggregate(field, m_lat, m_lon)
        self.assertTrue(np.allclose(coarse.sum(axis=(1, 2)), field.sum(axis=(1, 2)), rtol=1e-10))


class InversionTests(unittest.TestCase):
    def frame(self, n: int = 20) -> pd.DataFrame:
        rng = np.random.default_rng(7)
        rows = []
        for code in ("BKT", "JMB"):
            times = pd.date_range("2023-12-01T06:00", periods=n, freq="12h")
            rows.append(pd.DataFrame(dict(station=code, time_utc=times, fossil_near_ppm=rng.uniform(1, 6, n), fossil_far_ppm=rng.uniform(.5, 2, n),
                bio_day_ppm=-rng.uniform(1, 10, n), bio_night_ppm=rng.uniform(2, 15, n), ocean_ppm=-.05, fire_ppm=.1,
                background_ppm=420 + rng.normal(0, .5, n))))
        return pd.concat(rows, ignore_index=True)

    def test_covariance_is_block_diagonal_and_positive_definite(self) -> None:
        frame = self.frame()
        k, b, base, names = C.design(frame)
        self.assertTrue((k[:, 2] <= 0).all() and (k[:, [0, 1, 3]] >= 0).all())  # daytime biosphere enters with its own sign
        r = C.covariance(frame, k, .3)
        bkt, jmb = frame.station.eq("BKT").to_numpy(), frame.station.eq("JMB").to_numpy()
        self.assertTrue((r[np.ix_(bkt, jmb)] == 0).all())
        self.assertTrue(np.allclose(r, r.T) and (np.linalg.eigvalsh(r) > 0).all())

    def test_signed_problem_recovers_known_multipliers(self) -> None:
        frame = self.frame(40)
        k, b, base, names = C.design(frame)
        truth = np.array([.7, 1.3, 1.4, .8])
        beta = np.array([1.5, -.4, -1., .3])
        y = k @ truth + b @ beta
        sd = np.r_[np.repeat(np.log(20.), 4), np.tile([5., 5.], 2)]
        p = C.SignedInverseProblem(k, b, y, np.eye(len(y)) * 1e-4, sd)
        center, _, _ = p.fit()
        self.assertTrue(np.allclose(np.exp(center[:4]), truth, rtol=.02), np.exp(center[:4]))
        self.assertTrue(np.allclose(center[4:], beta, atol=.05))


if __name__ == "__main__":
    unittest.main()
