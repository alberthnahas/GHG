"""Configuration regressions for the tracer-independent transport benchmark."""
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from a37_bkt_footprint import FootprintConfig, TransportOptions, setup_text
from bkt_arl import unpack, pressure_interpolate
from a65_transport_observations import parse_value
from a70_transport_benchmark_figures import receptor_label


class TransportConfigurationTest(unittest.TestCase):
    def test_legacy_defaults_preserved(self):
        text = setup_text(FootprintConfig())
        for line in (" KMIX0 = 250,", " KMIXD = 3,", " CAPEMIN = -2.0,",
                     " WVERT = .TRUE.,", " NDUMP = 0,", " NCYCL = 1,"):
            self.assertIn(line, text)

    def test_explicit_defaults_identical(self):
        cfg = FootprintConfig(save_endpoints=True)
        self.assertEqual(setup_text(cfg), setup_text(cfg, TransportOptions()))
        self.assertIn(" NDUMP = 72,", setup_text(cfg))
        self.assertIn(" NCYCL = 0,", setup_text(cfg))

    def test_controlled_override_and_dumps(self):
        text = setup_text(FootprintConfig(save_endpoints=True), TransportOptions(
            minimum_mixing_depth_m=50, convection=-1, dump_interval_hours=6))
        for line in (" KMIX0 = 50,", " CAPEMIN = -1.0,", " NDUMP = 6,", " NCYCL = 6,"):
            self.assertIn(line, text)
        self.assertIn(" IDSP = 2,", text)

    def test_invalid_options_rejected(self):
        for kwargs in ({"minimum_mixing_depth_m":0}, {"convection":0},
                       {"convection":float("nan")}, {"mixing_depth_method":9},
                       {"dump_interval_hours":-1}):
            with self.assertRaises(ValueError):
                TransportOptions(**kwargs)
        with self.assertRaises(ValueError):
            setup_text(FootprintConfig(), TransportOptions(dump_interval_hours=1))

    def test_namelist_types_and_final_dump_guard(self):
        for kwargs in ({'minimum_mixing_depth_m':float('nan')}, {'minimum_mixing_depth_m':50.5},
                       {'minimum_mixing_depth_m':True}, {'mixing_depth_method':0.0},
                       {'dump_interval_hours':float('inf')}, {'dump_interval_hours':2.5},
                       {'wrf_vertical_interpolation':'false'}, {'convection':True}):
            with self.assertRaises(ValueError):TransportOptions(**kwargs)
        with self.assertRaises(ValueError):
            setup_text(FootprintConfig(save_endpoints=True),TransportOptions(dump_interval_hours=5))
        self.assertIn(' CAPEMIN = 0.01,',setup_text(FootprintConfig(),TransportOptions(convection=.01)))


class MeteorologicalReaderTest(unittest.TestCase):
    def test_local_calendar_rollover(self):
        self.assertEqual(receptor_label('2019-09-09T18:00:00Z'),'10 Sep, 01:00 WIB')
        self.assertEqual(receptor_label('2019-09-09T06:00:00Z'),'9 Sep, 13:00 WIB')

    def test_difference_packing_row_restarts(self):
        packed=np.array([[127,128,125],[129,128,126]],dtype=np.uint8)
        np.testing.assert_allclose(unpack(packed,7,10.),[[10,11,9],[12,13,12]])

    def test_log_pressure_and_no_extrapolation(self):
        profile=pd.DataFrame({'PRES':[1000.,500.],'TEMP':[300.,260.]})
        self.assertAlmostEqual(pressure_interpolate(profile,np.sqrt(500000),'TEMP'),280.)
        self.assertTrue(np.isnan(pressure_interpolate(profile,1010,'TEMP')))

    def test_igra_missing_and_scaling(self):
        self.assertTrue(np.isnan(parse_value('-8888')))
        self.assertTrue(np.isnan(parse_value('-9999')))
        self.assertAlmostEqual(parse_value('123',.1),12.3)


if __name__ == "__main__":
    unittest.main()
