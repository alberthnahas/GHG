"""Protect missing-value and pressure-sign decisions in the BARRA gate."""
import sys
from pathlib import Path
import unittest
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from a54_bkt_barra_quality import aboveground_gaps, values


class TestBarraGate(unittest.TestCase):
    def test_aboveground_pressure_sign_and_margin(self):
        above,gaps=aboveground_gaps([np.nan]*4,[900,925,926,927],925,1)
        np.testing.assert_array_equal(above,[False,False,False,True])
        np.testing.assert_array_equal(gaps,above)

    def test_mask_nan_infinity_and_valid_zero(self):
        data=np.ma.array([1,np.nan,np.inf,0],mask=[True,False,False,False])
        _,gaps=aboveground_gaps(data,[1000]*4,925)
        np.testing.assert_array_equal(gaps,[True,True,True,False])

    def test_missing_pressure_rejected(self):
        with self.assertRaises(ValueError):aboveground_gaps([1],[np.nan],925)

    def test_shape_mismatch_rejected(self):
        with self.assertRaises(ValueError):aboveground_gaps([1,2],[1000],925)

    def test_negative_margin_rejected(self):
        with self.assertRaises(ValueError):aboveground_gaps([1],[1000],925,-1)

    def test_packed_mask_and_ncss_nan_preserved(self):
        packed=np.ma.array([0,1,2],mask=[False,True,False])
        result=values(packed)
        self.assertEqual(result[0],0)
        self.assertTrue(np.isnan(result[1]))
        self.assertEqual(result[2],2)
        self.assertTrue(np.isnan(values(np.array([np.nan]))[0]))


if __name__=="__main__":unittest.main()
