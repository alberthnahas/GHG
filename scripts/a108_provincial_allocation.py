#!/usr/bin/env python3
"""Put the reported national totals onto provinces, using real facility locations.

SIGN-SMART reports at national, provincial and district level, and its database
needs an account. Indonesia's reported national totals are public through its
UNFCCC submissions. What is missing is the split between provinces, and a
national factor applied to a global gridded pattern cannot supply it: it spreads
a correction evenly over places the towers cannot see.

Climate TRACE publishes asset-level emissions with coordinates. Only carbon
dioxide equivalent is exposed per asset, which is no obstacle here, because
within one sector the equivalent is proportional to the gas: the assets are used
for the provincial share, never for the magnitude. The magnitude stays the
reported national total.

    provincial total = reported national total x this province's share of the
                       sector's assets

The result is a provincial export in the same contract the localisation engine
already takes, so the engine's mass conservation, refusals and ledger apply
unchanged.

Stages
  shares      assign assets to provinces and write the sector shares
  export      turn a national export into a provincial one
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ASSETS = Path("/run/media/workstation-llm/HDD2/.assets/indonesia_38prov.geojson")
DISTRICTS = Path("/run/media/workstation-llm/HDD2/.assets/indonesia_kabkota_38prov.geojson")
TRACE = ROOT / "data/bkt_sources/climatetrace/idn_assets_2022.json"
OUT = ROOT / "outputs/inventory"

# Climate TRACE sector -> IPCC category used by the crosswalk
SECTOR_TO_IPCC = {
    "electricity-generation": "1A", "other-energy-use": "1A", "road-transportation": "1A",
    "domestic-aviation": "1A", "domestic-shipping": "1A", "railways": "1A",
    "food-beverage-tobacco": "1A", "other-manufacturing": "1A", "pulp-and-paper": "1A",
    "textiles-leather-apparel": "1A", "wood-and-wood-products": "1A",
    "oil-and-gas-production": "1B", "oil-and-gas-refining": "1B", "oil-and-gas-transport": "1B",
    "coal-mining": "1B", "other-fossil-fuel-operations": "1B",
    "cement": "2", "steel": "2", "aluminum": "2", "chemicals": "2", "petrochemicals": "2",
    "solid-waste-disposal": "4", "domestic-wastewater-treatment": "4",
    "industrial-wastewater-treatment": "4", "solid-waste-incineration": "4", "wastewater-treatment-and-discharge": "4",
    "rice-cultivation": "3C", "cropland-fires": "3C", "synthetic-fertilizer-application": "3C",
    "enteric-fermentation-cattle-operation": "3A", "manure-management-cattle-operation": "3A",
    "enteric-fermentation-other": "3A", "manure-management-other": "3A",
    "forest-land-clearing": "3B2", "forest-land-degradation": "3B2", "forest-land-fires": "3B2",
    "shrubgrass-fires": "3B2", "wetland-fires": "3B1", "net-wetland": "3B1",
    "crop-residues": "3C", "enteric-fermentation-cattle-pasture": "3A",
    "domestic-wastewater-treatment-and-discharge": "4", "industrial-wastewater-treatment-and-discharge": "4",
    "bauxite-mining": "2", "copper-mining": "2", "glass": "2", "iron-mining": "2", "lime": "2",
    "other-mining-quarrying": "2", "other-chemicals": "2", "sand-quarrying": "2", "rock-quarrying": "2",
}


def province_of(lon: np.ndarray, lat: np.ndarray, districts: bool = False) -> np.ndarray:
    import geopandas as gpd
    frame = gpd.read_file(DISTRICTS if districts else ASSETS)
    candidates = ("kabupaten", "kabkota", "KABKOTA", "nama", "name") if districts else ("provinsi", "PROVINSI", "name")
    column = next(c for c in candidates if c in frame.columns)
    points = gpd.GeoDataFrame(geometry=gpd.points_from_xy(lon, lat), crs=frame.crs)
    joined = gpd.sjoin(points, frame[[column, "geometry"]], how="left", predicate="within")
    return joined[~joined.index.duplicated()][column].to_numpy()


def shares() -> pd.DataFrame:
    if not TRACE.exists():
        raise FileNotFoundError(f"Asset file missing: {TRACE}")
    assets = pd.DataFrame(json.loads(TRACE.read_text()))
    assets = assets.dropna(subset=["lat", "lon", "co2e_100yr"])
    assets = assets[assets.co2e_100yr > 0]
    assets["ipcc_code"] = assets.sector.map(SECTOR_TO_IPCC)
    unmapped = sorted(set(assets.loc[assets.ipcc_code.isna(), "sector"]))
    assets = assets.dropna(subset=["ipcc_code"])
    assets["province"] = province_of(assets.lon.to_numpy(), assets.lat.to_numpy())
    offshore = int(assets.province.isna().sum())
    assets = assets.dropna(subset=["province"])
    table = (assets.groupby(["ipcc_code", "province"], as_index=False).co2e_100yr.sum())
    table["share"] = table.groupby("ipcc_code").co2e_100yr.transform(lambda v: v / v.sum())
    OUT.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUT / "provincial_shares.csv", index=False)
    print(f"{len(assets)} located assets over {table.province.nunique()} provinces, "
          f"{offshore} offshore or outside a province and dropped", flush=True)
    if unmapped:
        print(f"sectors with no IPCC mapping, excluded: {unmapped[:6]}", flush=True)
    for code in sorted(table.ipcc_code.unique()):
        top = table[table.ipcc_code.eq(code)].nlargest(3, "share")
        summary = ", ".join(f"{r.province.title()} {100 * r.share:.0f}%" for r in top.itertuples())
        print(f"  {code:4s} {summary}", flush=True)
    return table


def district_shares() -> pd.DataFrame:
    """The same allocation one level down, as an inventory product.

    The towers cannot resolve a district: the footprint grid is a quarter degree,
    about 28 km, and most districts are smaller than one cell. This table is
    therefore written for the inventory, not consumed by the inversion, which
    takes the provincial split.
    """
    assets = pd.DataFrame(json.loads(TRACE.read_text()))
    assets = assets.dropna(subset=["lat", "lon", "co2e_100yr"])
    assets = assets[assets.co2e_100yr > 0]
    assets["ipcc_code"] = assets.sector.map(SECTOR_TO_IPCC)
    assets = assets.dropna(subset=["ipcc_code"])
    assets["district"] = province_of(assets.lon.to_numpy(), assets.lat.to_numpy(), districts=True)
    located = assets.dropna(subset=["district"])
    table = located.groupby(["ipcc_code", "district"], as_index=False).co2e_100yr.sum()
    table["share"] = table.groupby("ipcc_code").co2e_100yr.transform(lambda v: v / v.sum())
    OUT.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUT / "district_shares.csv", index=False)
    print(f"{len(located)} assets located in {table.district.nunique()} districts across "
          f"{table.ipcc_code.nunique()} categories -> {OUT / 'district_shares.csv'}", flush=True)
    print("  the inversion consumes the provincial split: a quarter-degree footprint cannot resolve a district", flush=True)
    return table


def export(national: Path, destination: Path) -> pd.DataFrame:
    """Split a national export across provinces by the asset shares."""
    table = pd.read_csv(OUT / "provincial_shares.csv") if (OUT / "provincial_shares.csv").exists() else shares()
    rows = []
    for row in pd.read_csv(national).itertuples():
        split = table[table.ipcc_code.eq(row.ipcc_code)]
        if split.empty:
            rows.append({c: getattr(row, c) for c in pd.read_csv(national).columns})   # keep it national
            continue
        for part in split.itertuples():
            entry = {c: getattr(row, c) for c in pd.read_csv(national).columns}
            entry.update(region_level="province", region_name=part.province,
                         value=float(row.value) * float(part.share),
                         source=f"{row.source}; provincial share from Climate TRACE assets")
            rows.append(entry)
    out = pd.DataFrame(rows)
    out.to_csv(destination, index=False)
    national_total = pd.read_csv(national).value.sum()
    print(f"wrote {destination}: {len(out)} rows, total {out.value.sum():.1f} against the national {national_total:.1f}",
          flush=True)
    if abs(out.value.sum() - national_total) > 1e-6 * max(1.0, national_total):
        raise AssertionError("the provincial split does not conserve the national total")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["shares", "districts", "export"])
    parser.add_argument("--national", type=Path)
    parser.add_argument("--out", type=Path)
    a = parser.parse_args()
    if a.stage == "shares":
        shares()
    elif a.stage == "districts":
        district_shares()
    else:
        export(a.national, a.out or a.national.with_name(a.national.stem + "_provincial.csv"))


if __name__ == "__main__":
    main()
