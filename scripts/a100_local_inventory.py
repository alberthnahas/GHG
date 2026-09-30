#!/usr/bin/env python3
"""Localise a global gridded inventory to Indonesian totals from SIGN-SMART.

SIGN-SMART (Sistem Informasi Gas Rumah Kaca Nasional) is the KLH inventory
system, reported at national, provincial and district level. EDGAR is gridded
but global and generic. Neither alone is what a regional inversion wants: the
prior needs Indonesian totals on a spatial pattern fine enough to convolve with
a footprint.

This module keeps each one for what it is good at. EDGAR supplies the spatial
pattern within a province; SIGN-SMART supplies the magnitude of that province,
sector by sector and gas by gas. The factor is applied inside the province only,
the pattern is untouched, and the province total afterwards equals the reported
total by construction. Every factor is written to a ledger with its source.

Three judgements are built in, and they matter more than the code:

  FOLU is not scalable onto EDGAR. EDGAR excludes land use, land-use change and
    forestry, so there is no EDGAR pattern to carry an Indonesian FOLU total. In
    Indonesia that is the largest and most variable term. The crosswalk refuses
    the mapping rather than silently spreading peat and forest emissions over
    power stations and roads; FOLU needs its own proxy, which is a separate job.

  carbon-dioxide-equivalent is not mass. A total reported in Gg CO2e cannot enter
    a methane prior without a stated global warming potential, and the wrong
    horizon or assessment report is a silent error of tens of percent. The
    contract requires the unit, and a CO2e input requires an explicit gwp column.

  a zero pattern cannot be scaled. If EDGAR puts no emission of that sector in a
    province, no factor can put the reported total there. That province is
    refused and listed, rather than receiving a division by something near zero.

Stages
  template    write the SIGN-SMART submission template and the crosswalk
  localise    apply an export to the gridded inventory, with a ledger
  compare     what changed against the global inventory, per province
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
ASSETS = Path("/run/media/workstation-llm/HDD2/.assets")
PROVINCES = ASSETS / "indonesia_38prov.geojson"
EDGAR = {"CO2": ROOT / "data/bkt_sources/edgar_2025", "CH4": ROOT / "data/bkt_sources/edgar_v8"}
OUT = ROOT / "outputs/inventory"
CONFIG = ROOT / "config"
CONTRACT_COLUMNS = ["region_level", "region_name", "ipcc_code", "sector_name", "gas", "year", "value", "unit", "source"]
FOLU_COMPONENT_NAMES = ("peat_drainage", "peat_fire", "nonpeat_fire")
UNITS = {"Gg": 1e6, "t": 1e3, "kg": 1.0}          # to kilograms of the gas
CO2E_UNITS = {"Gg CO2e": 1e6, "t CO2e": 1e3}
SECONDS_PER_YEAR = 365.25 * 86400

# IPCC 2006 category -> EDGAR sectors that carry the same emissions.
# An empty list means EDGAR has no counterpart and the category is refused.
CROSSWALK = {
    "1A1": (["POWER_INDUSTRY"], "Energy industries"),
    "1A2": (["IND_COMBUSTION"], "Manufacturing industries and construction"),
    "1A3": (["TRANSPORT"], "Transport"),
    "1A4": (["BUILDINGS"], "Other sectors, buildings and small combustion"),
    "1A": (["POWER_INDUSTRY", "IND_COMBUSTION", "TRANSPORT", "BUILDINGS"], "Fuel combustion, all"),
    "1B": (["FUEL_EXPLOITATION"], "Fugitive emissions from fuels"),
    "1": (["POWER_INDUSTRY", "IND_COMBUSTION", "TRANSPORT", "BUILDINGS", "FUEL_EXPLOITATION"], "Energy, all"),
    "2": (["IND_PROCESSES"], "Industrial processes and product use"),
    "3A": (["AGRICULTURE"], "Livestock"),
    "3C": (["AGRICULTURE"], "Aggregate sources on land, agriculture"),
    "3B": ([], "Land, all: EDGAR has no pattern; carried by the FOLU proxy (a101)"),
    "3B1": ([], "Land, peat drainage: carried by the FOLU proxy layer peat_drainage"),
    "3B2": ([], "Land, fire: carried by the FOLU proxy layers peat_fire and nonpeat_fire"),
    "4": (["WASTE"], "Waste"),
}
REFUSED = {code for code, (sectors, _) in CROSSWALK.items() if not sectors}
# FOLU categories carry no EDGAR pattern but do have one of their own (a101).
FOLU_PROXY = {"3B": ("peat_drainage", "peat_fire", "nonpeat_fire"),
              "3B1": ("peat_drainage",),
              "3B2": ("peat_fire", "nonpeat_fire")}
# GWP100 sets, so a total in carbon-dioxide equivalent can be converted with a
# stated horizon instead of being refused outright.
GWP_SETS = {
    "AR6": {"CH4": 27.2, "CH4_FOSSIL": 29.8, "N2O": 273.0},
    "AR5": {"CH4": 28.0, "CH4_FOSSIL": 30.0, "N2O": 265.0},
    "AR4": {"CH4": 25.0, "CH4_FOSSIL": 25.0, "N2O": 298.0},
}


# ------------------------------------------------------------------ inputs

def province_masks(lat: np.ndarray, lon: np.ndarray) -> tuple[dict[str, np.ndarray], list[str]]:
    """Assign every grid cell to at most one province, by where its centre falls.

    Assigning by intersection instead would give a shared border cell to both
    provinces, and a factor applied twice there would break the mass the ledger
    promises. Centre containment makes the masks disjoint by construction, at
    the cost of leaving coastal cells whose centre is offshore unassigned; the
    caller reports how much emission sits in those.
    """
    import geopandas as gpd
    frame = gpd.read_file(PROVINCES)
    name_column = next(c for c in ("provinsi", "PROVINSI", "name", "NAME", "Propinsi") if c in frame.columns)
    mesh_lon, mesh_lat = np.meshgrid(lon, lat)
    points = gpd.GeoDataFrame(geometry=gpd.points_from_xy(mesh_lon.ravel(), mesh_lat.ravel()), crs=frame.crs)
    joined = gpd.sjoin(points, frame[[name_column, "geometry"]], how="left", predicate="within")
    joined = joined[~joined.index.duplicated()]                     # a point on a shared edge goes to one province
    labels = joined[name_column].to_numpy().reshape(mesh_lat.shape)
    masks = {}
    for name in pd.unique(labels.ravel()):
        if isinstance(name, str):
            masks[str(name)] = labels == name
    return masks, sorted(masks)


def resolve_region(name: str, masks: dict[str, np.ndarray]) -> str | None:
    """Match a province name to the boundary asset without depending on the writer's capitalisation.

    The asset spells provinces in upper case; an export will not. Matching on a
    normalised key avoids refusing a correct name over its case or spacing.
    """
    def key(value: str) -> str:
        return "".join(ch for ch in str(value).upper() if ch.isalnum())
    lookup = {key(k): k for k in masks}
    return lookup.get(key(name))


def cell_area(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    """Spherical cell area in square metres, for mass totals."""
    radius = 6371008.8
    dlat = float(np.diff(lat).mean()); dlon = float(np.diff(lon).mean())
    edges = np.deg2rad(np.r_[lat - dlat / 2, lat[-1] + dlat / 2])
    band = radius ** 2 * np.abs(np.diff(np.sin(edges))) * np.deg2rad(dlon)
    return np.repeat(band[:, None], len(lon), axis=1)


def sector_field(gas: str, sector: str, year: int) -> xr.DataArray:
    path = EDGAR[gas] / f"{gas}_{sector}_{year}.nc"
    if not path.exists():
        available = sorted(p.name for p in EDGAR[gas].glob(f"{gas}_{sector}_*.nc"))
        raise FileNotFoundError(f"No gridded {gas} {sector} for {year}. Available: {available}")
    with xr.open_dataset(path) as ds:
        variable = "fluxes" if "fluxes" in ds.data_vars else list(ds.data_vars)[0]
        return ds[variable].load()


def subset(field: xr.DataArray, bounds: tuple[float, float, float, float]) -> xr.DataArray:
    west, south, east, north = bounds
    return field.sel(lat=slice(south, north), lon=slice(west, east))


# ------------------------------------------------------------ the contract

def read_export(path: Path, gwp_set: str | None = None, folu_proxy: Path | None = None) -> pd.DataFrame:
    """Read a SIGN-SMART export and refuse only what cannot be made safe."""
    table = pd.read_csv(path)
    missing = [c for c in CONTRACT_COLUMNS if c not in table.columns]
    if missing:
        raise ValueError(f"Export is missing required columns {missing}. See {CONFIG / 'signsmart_template.csv'}")
    table["ipcc_code"] = table.ipcc_code.astype(str).str.strip().str.upper()
    table["gas"] = table.gas.astype(str).str.strip().str.upper()
    unknown = sorted(set(table.ipcc_code) - set(CROSSWALK))
    if unknown:
        raise ValueError(f"No crosswalk for IPCC categories {unknown}; add them to CROSSWALK with an explicit decision")
    refused = table[table.ipcc_code.isin(REFUSED)]
    if len(refused):
        codes = sorted(set(refused.ipcc_code))
        carried = [c for c in codes if c in FOLU_PROXY]
        if carried and folu_proxy is None:
            raise ValueError(f"Categories {carried} need the FOLU proxy: build it with a101 and pass --folu-proxy. "
                             "They have no EDGAR pattern and must never be scaled onto one.")
        orphan = [c for c in codes if c not in FOLU_PROXY]
        if orphan:
            raise ValueError(f"Categories {orphan} have no pattern at all. {CROSSWALK[orphan[0]][1]}")
    bad = table[~table.unit.isin(list(UNITS) + list(CO2E_UNITS))]
    if len(bad):
        raise ValueError(f"Unsupported units {sorted(set(bad.unit))}; use one of {sorted(UNITS) + sorted(CO2E_UNITS)}")
    equivalent = table[table.unit.isin(CO2E_UNITS)]
    if len(equivalent):
        if "gwp" not in table.columns:
            table["gwp"] = np.nan
        missing = table.unit.isin(CO2E_UNITS) & table.gwp.isna()
        if missing.any():
            if gwp_set is None:
                raise ValueError("A total in carbon-dioxide equivalent needs a global warming potential: give a gwp "
                                 f"column, or choose a stated horizon with --gwp-set from {sorted(GWP_SETS)}. "
                                 "Converting CO2e with an unstated potential is a silent error of tens of percent")
            if gwp_set not in GWP_SETS:
                raise ValueError(f"Unknown gwp set {gwp_set!r}; choose from {sorted(GWP_SETS)}")
            values = GWP_SETS[gwp_set]
            unknown_gas = sorted(set(table.loc[missing, "gas"]) - set(values))
            if unknown_gas:
                raise ValueError(f"{gwp_set} has no potential for {unknown_gas}")
            table.loc[missing, "gwp"] = table.loc[missing, "gas"].map(values)
            table.loc[missing, "source"] = table.loc[missing, "source"].astype(str) + f" (GWP100 {gwp_set})"
    if (table.value < 0).any():
        raise ValueError("Negative totals: a removal cannot be represented by scaling a positive EDGAR pattern")
    return table


def to_kilograms(row) -> float:
    if row.unit in UNITS:
        return float(row.value) * UNITS[row.unit]
    return float(row.value) * CO2E_UNITS[row.unit] / float(row.gwp)


# ------------------------------------------------------------------ stages

def template() -> None:
    CONFIG.mkdir(parents=True, exist_ok=True)
    example = pd.DataFrame([
        dict(region_level="province", region_name="Sumatera Barat", ipcc_code="1A1", sector_name="Energy industries",
             gas="CO2", year=2023, value=np.nan, unit="Gg", source="SIGN-SMART export YYYY-MM-DD", gwp=np.nan),
        dict(region_level="province", region_name="Jambi", ipcc_code="1B", sector_name="Fugitive emissions from fuels",
             gas="CH4", year=2022, value=np.nan, unit="Gg", source="SIGN-SMART export YYYY-MM-DD", gwp=np.nan),
        dict(region_level="national", region_name="Indonesia", ipcc_code="4", sector_name="Waste",
             gas="CH4", year=2022, value=np.nan, unit="Gg CO2e", source="SIGN-SMART export YYYY-MM-DD", gwp=28.0),
    ])
    example.to_csv(CONFIG / "signsmart_template.csv", index=False)
    rows = [dict(ipcc_code=code, description=description, edgar_sectors=";".join(sectors) if sectors else "",
                 usable=bool(sectors)) for code, (sectors, description) in CROSSWALK.items()]
    pd.DataFrame(rows).to_csv(CONFIG / "signsmart_edgar_crosswalk.csv", index=False)
    print(f"wrote {CONFIG / 'signsmart_template.csv'} and {CONFIG / 'signsmart_edgar_crosswalk.csv'}")
    print("Required columns: " + ", ".join(CONTRACT_COLUMNS) + " (plus gwp when the unit is CO2e)")
    print(f"Categories refused by design: {sorted(REFUSED)} ({CROSSWALK['3B'][1]})")


def localise(export: Path, gas: str, year: int, bounds: tuple[float, float, float, float], label: str,
             gwp_set: str | None = None, folu_proxy: Path | None = None, fallback: bool = False) -> dict:
    table = read_export(export, gwp_set, folu_proxy)
    table = table[(table.gas == gas) & (table.year == year) & table.value.notna()]
    if table.empty:
        raise ValueError(f"No filled {gas} rows for {year} in {export}")
    folu_rows = table[table.ipcc_code.isin(FOLU_PROXY)]
    table = table[~table.ipcc_code.isin(FOLU_PROXY)]
    sectors = sorted({s for code in table.ipcc_code for s in CROSSWALK[code][0]})
    if not sectors:
        raise ValueError("This export places nothing on the EDGAR grid; include at least one energy, industry, "
                         "agriculture or waste category alongside any land-use rows")
    fields = {s: subset(sector_field(gas, s, year), bounds) for s in sectors}
    reference = fields[sectors[0]]
    lat, lon = reference.lat.values, reference.lon.values
    area = cell_area(lat, lon)
    masks, names = province_masks(lat, lon)
    annual = {s: f.mean("time").values * area * SECONDS_PER_YEAR for s, f in fields.items()}   # kg per year per cell

    ledger, refusals = [], []
    scaled = {s: np.array(annual[s], dtype=float) for s in sectors}
    applied = {s: np.zeros_like(area, dtype=bool) for s in sectors}
    # Several IPCC categories can share one EDGAR sector: 3A livestock and 3C rice
    # both live in EDGAR AGRICULTURE. Comparing either alone against the whole
    # sector would understate the reported total, so they are summed first.
    table = table.assign(targets=[";".join(CROSSWALK[c][0]) for c in table.ipcc_code])
    grouped = (table.groupby(["region_level", "region_name", "targets"], as_index=False)
               .agg(value=("value", "sum"), unit=("unit", "first"), gwp=("gwp", "first") if "gwp" in table else ("value", "size"),
                    ipcc_code=("ipcc_code", lambda v: "+".join(sorted(set(v)))),
                    source=("source", "first")))
    for row in grouped.itertuples():
        targets = [t for t in row.targets.split(";") if t]
        if row.region_level == "national":
            mask = np.any([masks[n] for n in names], axis=0)
            region = "Indonesia"
        else:
            canonical = resolve_region(row.region_name, masks)
            if canonical is None:
                refusals.append(dict(region=row.region_name, ipcc_code=row.ipcc_code,
                                     reason="region name not found in the 38-province boundary"))
                continue
            mask = masks[canonical]; region = canonical
        model_kg = float(sum(annual[s][mask].sum() for s in targets))
        used_fallback = False
        if model_kg <= 0:
            if not fallback:
                refusals.append(dict(region=region, ipcc_code=row.ipcc_code,
                                     reason="the global inventory puts no emission of this sector here; rerun with "
                                            "--fallback to spread the reported total evenly over the region instead"))
                continue
            # last resort: an even spread over the region, recorded as such. Better than
            # dropping a reported total, worse than a real pattern, and never silent.
            first = targets[0]
            annual[first] = annual[first] + mask * 1.0
            model_kg = float(annual[first][mask].sum())
            used_fallback = True
        overlap = [s for s in targets if applied[s][mask].any()]
        if overlap:
            raise ValueError(f"{region} {row.ipcc_code} would scale {overlap} twice; the export has overlapping categories")
        reported_kg = to_kilograms(row)
        factor = reported_kg / model_kg
        for s in targets:
            scaled[s][mask] = annual[s][mask] * factor
            applied[s][mask] = True
        ledger.append(dict(region_level=row.region_level, region=region, ipcc_code=row.ipcc_code,
                           edgar_sectors=";".join(targets), gas=gas, year=year,
                           reported_kg=reported_kg, global_kg=model_kg, factor=factor, pattern="EDGAR",
                           fallback_even_spread=used_fallback,
                           reported_Gg=reported_kg / 1e6, global_Gg=model_kg / 1e6, source=row.source))

    folu_fields = {}
    if len(folu_rows):
        with xr.open_dataset(folu_proxy) as proxy:
            aligned = proxy.interp(lat=("y", lat), lon=("x", lon), method="nearest")
            available = {name: np.nan_to_num(np.asarray(aligned[name].values, float)).reshape(len(lat), len(lon))
                         for name in FOLU_COMPONENT_NAMES if name in aligned}
        for row in folu_rows.itertuples():
            layers = [name for name in FOLU_PROXY[row.ipcc_code] if name in available]
            if not layers:
                refusals.append(dict(region=row.region_name, ipcc_code=row.ipcc_code,
                                     reason=f"the FOLU proxy has none of {FOLU_PROXY[row.ipcc_code]}"))
                continue
            if row.region_level == "national":
                mask, region = np.ones_like(area, bool), "Indonesia"
            else:
                canonical = resolve_region(row.region_name, masks)
                if canonical is None:
                    refusals.append(dict(region=row.region_name, ipcc_code=row.ipcc_code,
                                         reason="region name not found in the 38-province boundary"))
                    continue
                mask, region = masks[canonical], canonical
            pattern = sum(available[name] for name in layers) * mask
            weight = float(pattern.sum())
            if weight <= 0:
                refusals.append(dict(region=region, ipcc_code=row.ipcc_code,
                                     reason="the FOLU proxy is empty here: no peat and no fire"))
                continue
            reported_kg = to_kilograms(row)
            name = f"FOLU_{row.ipcc_code}"
            folu_fields[name] = folu_fields.get(name, np.zeros_like(area)) + pattern / weight * reported_kg
            ledger.append(dict(region_level=row.region_level, region=region, ipcc_code=row.ipcc_code,
                               edgar_sectors=";".join(layers), gas=gas, year=year,
                               reported_kg=reported_kg, global_kg=float("nan"), factor=float("nan"),
                               pattern="FOLU proxy", fallback_even_spread=False,
                               reported_Gg=reported_kg / 1e6, global_Gg=float("nan"), source=row.source))

    OUT.mkdir(parents=True, exist_ok=True)
    dataset = xr.Dataset({s: (("lat", "lon"), scaled[s]) for s in sectors}
                         | {name: (("lat", "lon"), values) for name, values in folu_fields.items()},
                         coords=dict(lat=lat, lon=lon))
    for s in sectors:
        dataset[s].attrs.update(units="kg year-1 per cell", sector=s,
                                pattern="EDGAR", magnitude="SIGN-SMART where a factor was applied")
    dataset.attrs.update(title=f"Localised {gas} inventory {year}", label=label,
                         pattern_source=str(EDGAR[gas]), totals_source="SIGN-SMART export",
                         note="Factors act inside declared regions only; the gridded pattern is unchanged")
    destination = OUT / f"local_inventory_{gas.lower()}_{year}_{label}.nc"
    dataset.to_netcdf(destination)
    pd.DataFrame(ledger).to_csv(OUT / f"local_inventory_{gas.lower()}_{year}_{label}_ledger.csv", index=False)
    if refusals:
        pd.DataFrame(refusals).to_csv(OUT / f"local_inventory_{gas.lower()}_{year}_{label}_refusals.csv", index=False)

    # conservation: what the ledger promised must be what the grid now holds
    errors = []
    for entry in [e for e in ledger if e["pattern"] == "EDGAR"]:
        mask = np.any([masks[n] for n in names], axis=0) if entry["region"] == "Indonesia" else masks[entry["region"]]
        total = float(sum(scaled[s][mask].sum() for s in entry["edgar_sectors"].split(";")))
        if abs(total - entry["reported_kg"]) > 1e-6 * max(1.0, abs(entry["reported_kg"])):
            errors.append((entry["region"], entry["ipcc_code"], total, entry["reported_kg"]))
    if errors:
        raise AssertionError(f"Mass not conserved for {errors[:3]}")

    assigned = np.any([masks[n] for n in names], axis=0)
    offshore_kg = float(sum(annual[s][~assigned].sum() for s in sectors))
    domain_kg = float(sum(annual[s].sum() for s in sectors))
    summary = dict(gas=gas, year=year, label=label, regions_scaled=len(ledger), refusals=len(refusals),
                   unassigned_percent=round(100 * offshore_kg / domain_kg, 2) if domain_kg else 0.0,
                   sectors=sectors, output=str(destination),
                   global_total_Gg=round(sum(float(annual[s].sum()) for s in sectors) / 1e6, 1),
                   local_total_Gg=round(sum(float(scaled[s].sum()) for s in sectors) / 1e6, 1))
    (OUT / f"local_inventory_{gas.lower()}_{year}_{label}_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"{gas} {year}: {len(ledger)} regions scaled, {len(refusals)} refused; "
          f"domain total {summary['global_total_Gg']} -> {summary['local_total_Gg']} Gg", flush=True)
    if ledger:
        frame = pd.DataFrame(ledger)
        print(frame[["region", "ipcc_code", "global_Gg", "reported_Gg", "factor"]].round(3).to_string(index=False), flush=True)
    if refusals:
        print("refused:", flush=True)
        print(pd.DataFrame(refusals).to_string(index=False), flush=True)
    return summary


def influence(gas: str, year: int, bounds: tuple[float, float, float, float], seed: int = 0) -> pd.DataFrame:
    """Which province's inventory the towers can actually see.

    A provincial total only matters to an inversion in proportion to how much of
    the tower's modelled enhancement comes from that province. This weights each
    province's gridded emission by the mean footprint at each tower, so the
    inventory effort can go where the observations are sensitive.
    """
    import a71_domain_budget_extension as ext
    import a84_bkt_jmb_two_receptor as T
    import a91_bkt_jmb_co2_experiments as X

    sectors = sorted({s for code in ("1A", "1B", "2", "3A", "4") for s in CROSSWALK[code][0]})
    available = [s for s in sectors if (EDGAR[gas] / f"{gas}_{s}_{year}.nc").exists()]
    fields = {s: subset(sector_field(gas, s, year), bounds) for s in available}
    rows = []
    frame = X.receptor_frame("", None, "2023")
    for code in ("BKT", "JMB"):
        stamps = sorted(frame.loc[frame.station.eq(code), "time_utc"])
        total = None
        for stamp in stamps:
            directory = T.RUNS / f"{code.lower()}_s{seed}" / f"bkt_{stamp:%Y%m%dT%H%MZ}"
            if not (directory / "completion_receipt.json").exists():
                continue
            field, _, _ = ext.read_footprint(directory)
            values = field.values.sum(axis=0)
            total = values if total is None else total + values
            grid_lat, grid_lon = field.lat.values, field.lon.values
        if total is None:
            raise FileNotFoundError(f"No footprints for {code}; run the campaign first")
        total /= len(stamps)
        masks, names = province_masks(grid_lat, grid_lon)
        for sector, source in fields.items():
            aligned = source.mean("time").interp(lat=("y", grid_lat), lon=("x", grid_lon))
            # footprint (ppm per umol m-2 s-1) times flux pattern gives the modelled contribution
            contribution = total * np.nan_to_num(aligned.values.reshape(len(grid_lat), len(grid_lon)))
            for name in names:
                share = float(contribution[masks[name]].sum())
                if share > 0:
                    rows.append(dict(station=code, gas=gas, year=year, sector=sector, province=name, contribution=share))
    table = pd.DataFrame(rows)
    if table.empty:
        return table
    table = table.groupby(["station", "province"], as_index=False).contribution.sum()
    table["percent"] = table.groupby("station").contribution.transform(lambda v: 100 * v / v.sum())
    table = table.sort_values(["station", "percent"], ascending=[True, False])
    OUT.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUT / f"province_influence_{gas.lower()}_{year}.csv", index=False)
    for code in table.station.unique():
        top = table[table.station.eq(code)].head(6)
        print(f"{code}: provinces carrying the modelled anthropogenic signal")
        for row in top.itertuples():
            print(f"    {row.province:28s} {row.percent:5.1f}%")
    return table


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["template", "localise", "influence"])
    parser.add_argument("--export", type=Path, help="SIGN-SMART export CSV")
    parser.add_argument("--gas", default="CO2", choices=sorted(EDGAR))
    parser.add_argument("--year", type=int, default=2023)
    parser.add_argument("--label", default="signsmart")
    parser.add_argument("--gwp-set", choices=sorted(GWP_SETS), help="convert CO2e totals with a stated GWP100 horizon")
    parser.add_argument("--folu-proxy", type=Path, help="FOLU pattern from a101, which makes category 3B usable")
    parser.add_argument("--fallback", action="store_true", help="spread a total evenly where the global pattern is empty")
    parser.add_argument("--bounds", nargs=4, type=float, default=[94., -12., 142., 7.],
                        metavar=("WEST", "SOUTH", "EAST", "NORTH"))
    a = parser.parse_args()
    if a.stage == "template":
        template()
    elif a.stage == "influence":
        influence(a.gas, a.year, tuple(a.bounds))
    else:
        if not a.export:
            raise SystemExit("--export is required: the SIGN-SMART totals are not on this machine")
        localise(a.export, a.gas, a.year, tuple(a.bounds), a.label, a.gwp_set, a.folu_proxy, a.fallback)


if __name__ == "__main__":
    main()
