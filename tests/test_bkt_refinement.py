"""Scientific invariants for area-aware display and model comparison."""
import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from bkt_footprint_spatial import cell_area_km2, display_surface, regrid_coefficients, smooth_coefficients
from a39_bkt_refinement import actual_particles, select_bandwidth


class RefinementTests(unittest.TestCase):
    def test_display_conserves_integral_and_is_nonnegative(self):
        field=np.zeros((21,21))
        field[10,10]=3
        field[9,14]=1
        coords=np.arange(21)*.1-1
        lat,lon,density=display_surface(field,coords,coords,1)
        self.assertAlmostEqual(float((density*cell_area_km2(lat,lon)).sum()),4,places=12)
        self.assertTrue((density>=0).all())
        self.assertTrue(np.array_equal(field,smooth_coefficients(field,0)))

    def test_spherical_area_matches_hemisphere(self):
        area=cell_area_km2(np.arange(-89.5,90,1),np.arange(.5,180,1))
        self.assertAlmostEqual(area.sum()/(2*np.pi*6371.0088**2),1,places=12)

    def test_conservative_remapping_preserves_integrated_coefficient(self):
        source=np.arange(-1,1.01,.1)
        target=np.arange(-1,1.01,.5)
        field=np.zeros((len(source),len(source)))
        field[10,10]=7
        field[12,15]=2
        result=regrid_coefficients(field,source,source,target,target)
        self.assertAlmostEqual(result.sum(),9,places=11)
        self.assertTrue((result>=0).all())

    def test_no_smoothing_for_identical_seed_fields(self):
        f=np.zeros((21,21)); f[10,10]=1
        sigma,_=select_bandwidth([f,f,f],np.ones_like(f))
        self.assertEqual(sigma,0)

    def test_invalid_kernel_rejected_and_counts_read(self):
        with self.assertRaises(ValueError): smooth_coefficients(np.array([[-1.]]),1)
        log="NOTICE   main: 1 62974139 167 0.1\nNOTICE   main: 72 62969820 10020 50.0\n"
        self.assertEqual(actual_particles(log),10020)


if __name__=="__main__": unittest.main()
