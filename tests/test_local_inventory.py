from __future__ import annotations
import sys, unittest, tempfile
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import a100_local_inventory as L  # noqa: E402

BOUNDS = (98., -3., 105., 1.)          # Sumatra, small enough to rasterise in a test
GAS, YEAR, SECTOR = "CO2", 2023, "POWER_INDUSTRY"


def edgar_province_totals(provinces):
    """What the global inventory already holds in each province, in Gg per year."""
    field = L.subset(L.sector_field(GAS, SECTOR, YEAR), BOUNDS)
    lat, lon = field.lat.values, field.lon.values
    annual = field.mean("time").values * L.cell_area(lat, lon) * L.SECONDS_PER_YEAR
    masks, _ = L.province_masks(lat, lon)
    return {p: float(annual[masks[p]].sum()) / 1e6 for p in provinces}, annual, masks


def export_csv(directory: Path, totals: dict, unit="Gg", gwp=None, code="1A1", level="province") -> Path:
    rows = [dict(region_level=level, region_name=name, ipcc_code=code, sector_name="Energy industries",
                 gas=GAS, year=YEAR, value=value, unit=unit, source="self-consistency test", gwp=gwp)
            for name, value in totals.items()]
    path = directory / "export.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


class ContractTests(unittest.TestCase):
    def test_missing_columns_are_refused(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "bad.csv"
            pd.DataFrame([dict(region_name="JAMBI", value=1.0)]).to_csv(path, index=False)
            with self.assertRaises(ValueError) as caught:
                L.read_export(path)
            self.assertIn("missing required columns", str(caught.exception))

    def test_land_use_is_refused_rather_than_spread_over_power_stations(self) -> None:
        """FOLU has no EDGAR pattern; in Indonesia it is the largest term, so this must fail loudly."""
        with tempfile.TemporaryDirectory() as d:
            path = export_csv(Path(d), {"JAMBI": 100.}, code="3B")
            with self.assertRaises(ValueError) as caught:
                L.read_export(path)
            self.assertIn("no EDGAR counterpart", str(caught.exception))

    def test_co2_equivalent_without_a_stated_gwp_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = export_csv(Path(d), {"JAMBI": 100.}, unit="Gg CO2e", gwp=None)
            with self.assertRaises(ValueError) as caught:
                L.read_export(path)
            self.assertIn("global warming potential", str(caught.exception))

    def test_co2_equivalent_converts_with_the_stated_gwp(self) -> None:
        row = pd.Series(dict(value=280., unit="Gg CO2e", gwp=28.))
        self.assertAlmostEqual(L.to_kilograms(row), 10. * 1e6)
        self.assertAlmostEqual(L.to_kilograms(pd.Series(dict(value=10., unit="Gg", gwp=np.nan))), 10. * 1e6)

    def test_negative_totals_are_refused(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = export_csv(Path(d), {"JAMBI": -5.})
            with self.assertRaises(ValueError):
                L.read_export(path)

    def test_unknown_category_is_refused_rather_than_guessed(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = export_csv(Path(d), {"JAMBI": 5.}, code="9Z")
            with self.assertRaises(ValueError) as caught:
                L.read_export(path)
            self.assertIn("No crosswalk", str(caught.exception))

    def test_province_names_match_regardless_of_case(self) -> None:
        masks = {"SUMATERA BARAT": np.ones((2, 2), bool), "JAMBI": np.ones((2, 2), bool)}
        self.assertEqual(L.resolve_region("Sumatera Barat", masks), "SUMATERA BARAT")
        self.assertEqual(L.resolve_region("jambi", masks), "JAMBI")
        self.assertIsNone(L.resolve_region("Selangor", masks))


class EngineTests(unittest.TestCase):
    """Validated against the one case where the answer is known exactly."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.provinces = ["JAMBI", "SUMATERA BARAT"]
        cls.totals, cls.annual, cls.masks = edgar_province_totals(cls.provinces)

    def test_reporting_the_global_totals_changes_nothing(self) -> None:
        """Feed EDGAR its own provincial totals: every factor must be one and the grid must not move."""
        with tempfile.TemporaryDirectory() as d:
            path = export_csv(Path(d), self.totals)
            import xarray as xr
            summary = L.localise(path, GAS, YEAR, BOUNDS, "identity")
            ledger = pd.read_csv(L.OUT / f"local_inventory_co2_{YEAR}_identity_ledger.csv")
            self.assertEqual(len(ledger), len(self.provinces))
            self.assertTrue(np.allclose(ledger.factor, 1.0, atol=1e-9), f"factors {list(ledger.factor)}")
            with xr.open_dataset(summary["output"]) as ds:
                self.assertTrue(np.allclose(ds[SECTOR].values, self.annual, rtol=1e-9))

    def test_a_reported_total_becomes_the_province_total(self) -> None:
        """Halve one province and double another: each province must hold exactly what was reported."""
        wanted = {"JAMBI": self.totals["JAMBI"] * 0.5, "SUMATERA BARAT": self.totals["SUMATERA BARAT"] * 2.0}
        with tempfile.TemporaryDirectory() as d:
            import xarray as xr
            summary = L.localise(export_csv(Path(d), wanted), GAS, YEAR, BOUNDS, "scaled")
            with xr.open_dataset(summary["output"]) as ds:
                grid = ds[SECTOR].values
            for province, target in wanted.items():
                self.assertAlmostEqual(grid[self.masks[province]].sum() / 1e6, target, places=6)
            ledger = pd.read_csv(L.OUT / f"local_inventory_co2_{YEAR}_scaled_ledger.csv").set_index("region")
            self.assertAlmostEqual(float(ledger.loc["JAMBI", "factor"]), 0.5, places=9)
            self.assertAlmostEqual(float(ledger.loc["SUMATERA BARAT", "factor"]), 2.0, places=9)

    def test_cells_outside_the_declared_provinces_are_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            import xarray as xr
            summary = L.localise(export_csv(Path(d), {"JAMBI": self.totals["JAMBI"] * 3.0}), GAS, YEAR, BOUNDS, "one")
            with xr.open_dataset(summary["output"]) as ds:
                grid = ds[SECTOR].values
            outside = ~self.masks["JAMBI"]
            self.assertTrue(np.allclose(grid[outside], self.annual[outside], rtol=1e-9))

    def test_an_unknown_province_is_refused_and_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = export_csv(Path(d), {"JAMBI": self.totals["JAMBI"], "SELANGOR": 10.})
            L.localise(path, GAS, YEAR, BOUNDS, "refuse")
            refusals = pd.read_csv(L.OUT / f"local_inventory_co2_{YEAR}_refuse_refusals.csv")
            self.assertEqual(len(refusals), 1)
            self.assertEqual(refusals.region.iloc[0], "SELANGOR")


if __name__ == "__main__":
    unittest.main()
