from __future__ import annotations
import sys, unittest
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import a101_folu_proxy as F  # noqa: E402
import a102_prior_audit as A  # noqa: E402
import a99_operational_inversion as V  # noqa: E402

PROXY = ROOT / "outputs/inventory/folu_proxy_sumatra.nc"


class WeightTests(unittest.TestCase):
    def test_the_ordering_the_literature_agrees_on(self) -> None:
        """Values are a stated choice; this ordering is the part that is not."""
        w = F.DRAINAGE_WEIGHT
        self.assertGreater(w[12], w[7])        # cropland drains deeper than degraded shrub
        self.assertGreater(w[7], w[2])         # degraded shrub deeper than forest on peat
        self.assertGreater(w[2], w[11])        # forest on peat deeper than near-natural wetland
        self.assertEqual(w[0], 0.0)            # water emits nothing through drainage
        self.assertEqual(w[13], 0.0)           # urban is not drained peat

    def test_weights_are_relative_and_bounded(self) -> None:
        for code, value in F.DRAINAGE_WEIGHT.items():
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0, f"class {code} exceeds the relative scale")

    def test_the_contested_emission_factor_is_carried_as_a_range(self) -> None:
        low, high = F.DRAINED_PEAT_CO2_MG_HA_YR
        self.assertLess(low, high)
        self.assertGreater(high / low, 5)      # the published spread is nearly tenfold, and is not hidden


class ProxyTests(unittest.TestCase):
    @unittest.skipUnless(PROXY.exists(), "proxy not built")
    def test_each_layer_is_a_normalised_pattern(self) -> None:
        import xarray as xr
        with xr.open_dataset(PROXY) as ds:
            for name in F.FOLU_COMPONENTS:
                self.assertIn(name, ds.data_vars)
                values = ds[name].values
                self.assertGreaterEqual(values.min(), 0.0)
                self.assertAlmostEqual(float(values.sum()), 1.0, places=6, msg=f"{name} is not normalised")

    @unittest.skipUnless(PROXY.exists(), "proxy not built")
    def test_peat_fire_and_other_fire_do_not_overlap(self) -> None:
        import xarray as xr
        with xr.open_dataset(PROXY) as ds:
            peat = ds["peat"].values.astype(bool)
            self.assertTrue((ds["peat_fire"].values[~peat] == 0).all())
            self.assertTrue((ds["nonpeat_fire"].values[peat] == 0).all())
            self.assertTrue((ds["peat_drainage"].values[~peat] == 0).all())


class AuditTests(unittest.TestCase):
    def test_the_decomposition_sums_to_the_whole_signal(self) -> None:
        """Covariance shares, not ratios of standard deviations, which would not sum."""
        recommendation = A.audit()
        import pandas as pd
        table = pd.read_csv(A.OUT / "prior_audit.csv")
        for gas in V.GASES:
            share = table[table.gas.eq(gas)].share_of_signal_percent.sum()
            self.assertAlmostEqual(share, 100.0, places=3, msg=f"{gas} shares sum to {share}")
        self.assertIn("co2", recommendation)

    def test_every_component_is_classified_against_a_national_inventory(self) -> None:
        for gas in V.GASES.values():
            for parameter in gas.components:
                self.assertIn(parameter, A.REPORTED, f"{parameter} is not classified")

    def test_the_biosphere_is_not_claimed_to_be_in_a_national_inventory(self) -> None:
        for parameter in ("bio_net_BKT", "bio_net_JMB", "wetlands"):
            self.assertEqual(A.REPORTED[parameter][0], "no")
