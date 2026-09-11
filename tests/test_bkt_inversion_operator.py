import sys
from pathlib import Path
import unittest
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from a48_bkt_inversion_operator import arl_surface,active_endpoints,ROOT
from a43_bkt_source_analysis import matching_flux,MW
from bkt_footprint_spatial import sensitivity_support_mask


class InversionOperatorTests(unittest.TestCase):
    def test_native_terrain_agrees_with_noaa_profile(self):
        path=ROOT/"data/hysplit/gfs0p25/regional/20190923_gfs0p25"
        if not path.exists():self.skipTest("Native verification fixture unavailable")
        grid,precision=arl_surface(path,"SHGT",0)
        # Independently extracted NOAA profile for the nearest BKT native cell.
        self.assertEqual(grid[79,101],816.)
        self.assertGreater(precision,0)
        self.assertTrue(np.isfinite(grid).all())

    def test_constant_flux_conservative_remap(self):
        source=np.arange(-2,2.1,.5);target=np.arange(-1,1.1,.25)
        result=matching_flux(np.full((len(source),len(source)),.003),source,source,target,target)
        np.testing.assert_allclose(result,.003,atol=1e-14)

    def test_footprint_units(self):
        # 2 ppm/(umol m-2 s-1) times 0.003 umol m-2 s-1 = 6 ppb.
        self.assertAlmostEqual(2*.003*1000,6.)
        # One umol CH4 m-2 s-1 for a day over 1 km2 is 1.386072 Mg.
        mass_Gg=1*86400*1e6*MW["CH4"]*1e-15
        self.assertAlmostEqual(mass_Gg,.001386072)

    def test_particle_timestamp(self):
        raw=pd.Series([" 9/26/19  0: 0"," 9/26/19  0: 0"])
        parsed=pd.to_datetime(raw.str.replace(r"\s+","",regex=True),format="%m/%d/%y%H:%M")
        self.assertTrue(parsed.eq(pd.Timestamp("2019-09-26")).all())

    def test_inactive_particle_placeholder_is_not_an_endpoint(self):
        points=pd.DataFrame(dict(PGRD=[0,1],latitude=[0,-5],longitude=[0,110],NSORT=[1,2]))
        active=active_endpoints(points)
        self.assertEqual(active.NSORT.tolist(),[2])
        with self.assertRaises(ValueError):active_endpoints(points.iloc[:1])

    def test_support_mask_retains_threshold_ties(self):
        field=np.array([[5.,2.,2.,1.]])
        mask=sensitivity_support_mask(field,.8)
        np.testing.assert_array_equal(mask,[[True,True,True,False]])
        self.assertGreaterEqual(field[mask].sum()/field.sum(),.8)
        with self.assertRaises(ValueError):sensitivity_support_mask(np.zeros((2,2)))

if __name__=="__main__":unittest.main()
