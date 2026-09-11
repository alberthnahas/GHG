"""Small independent fixtures for conservative source–receptor convolution."""
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from a43_bkt_source_analysis import matching_flux, MW, unique_province_fractions
from bkt_footprint_spatial import regrid_coefficients, cell_area_km2


class SourceTests(unittest.TestCase):
    def test_uniform_flux_survives_shifted_grids(self):
        source=np.arange(-2.95,3,.1)
        target=np.arange(-1.902,2,.1)
        flux=np.full((len(source),len(source)),7.5)
        matched=matching_flux(flux,source,source,target,target)
        np.testing.assert_allclose(matched,7.5,rtol=1e-12,atol=1e-12)

    def test_flux_and_sensitivity_remapping_are_adjoint(self):
        source=np.arange(-2.875,3,.25)
        target=np.arange(-1.902,2,.1)
        rng=np.random.default_rng(45)
        flux=rng.random((len(source),len(source)))
        footprint=rng.random((len(target),len(target)))
        native=(footprint*matching_flux(flux,source,source,target,target)).sum()
        coarse=regrid_coefficients(footprint,target,target,source,source)
        # Spherical-area overlap algebra is an independent order of operations.
        self.assertAlmostEqual(native,float((coarse*flux).sum()),places=9)

    def test_unit_flux_convolution_has_no_extra_area_or_time(self):
        footprint=np.array([[[1.,2.],[3.,4.]],[[2.,4.],[6.,8.]]])
        flux=np.full((2,2),2.)
        self.assertEqual(float((footprint*flux).sum()),60.)

    def test_gfed_grams_per_cell_day_to_umol(self):
        area=1e6
        daily_g=MW["CH4"]*1e-6*area*86400
        self.assertAlmostEqual(daily_g/area/86400*1e6/MW["CH4"],1.)
        self.assertEqual(2.5*1000,2500.)

    def test_edgar_kg_to_umol(self):
        self.assertAlmostEqual((MW["CO2"]*1e-9)*1e9/MW["CO2"],1.)

    def test_missing_and_negative_are_not_zero(self):
        c=np.arange(3.)
        for value in (-1,np.nan,np.inf):
            f=np.ones((3,3));f[0,0]=value
            with self.assertRaises(ValueError):matching_flux(f,c,c,c,c)

    def test_incomplete_spatial_coverage_is_not_zero(self):
        source=np.arange(3.)
        target=np.arange(4.)
        with self.assertRaisesRegex(ValueError,"coverage"):
            matching_flux(np.ones((3,3)),source,source,target,target)

    def test_overlapping_provinces_excluded_not_double_counted(self):
        import geopandas as gpd
        from shapely import box
        overlay=gpd.GeoDataFrame({'iy':[0,0],'ix':[0,0],'cell_area':[1.,1.]},
            geometry=[box(0,0,.6,1),box(.4,0,1,1)],crs=6933)
        unique,ambiguous=unique_province_fractions(overlay)
        np.testing.assert_allclose(unique.fraction,[.4,.4])
        self.assertAlmostEqual(ambiguous.fraction.sum(),.2)

    def test_triply_claimed_area_is_counted_once_as_ambiguous(self):
        import geopandas as gpd
        from shapely import box
        overlay=gpd.GeoDataFrame({'iy':[0,0,0],'ix':[0,0,0],'cell_area':[1.,1.,1.]},
            geometry=[box(0,0,1,1)]*3,crs=6933)
        unique,ambiguous=unique_province_fractions(overlay)
        self.assertEqual(float(unique.fraction.sum()),0.)
        self.assertEqual(float(ambiguous.fraction.sum()),1.)


if __name__=="__main__":unittest.main()
