#!/usr/bin/env python3
"""Source attribution for the two-receptor inversion: what the towers actually see.

The readiness campaign (a99) answers whether the inversion can be trusted as a
predictor. It does not answer the questions a greenhouse gas monitoring
programme is funded to answer: how much of the methane arriving at Jambi comes
off peatland, which sector dominates, how far away the sources are, how old the
air is, which province or district carries the signal, and what emission the
posterior implies. Those are answerable from the operator that has already been
built, and they do not depend on the inversion beating its null.

Everything here is a diagnostic of the forward operator and its posterior, not a
validated flux estimate. The distinction matters and is carried in every table.

The arithmetic rests on one identity. A mole-fraction footprint stored in
ppm per umol m-2 s-1 is numerically the same number as ppb per nmol m-2 s-1, so
a methane flux expressed in nmol m-2 s-1 convolves straight to ppb and a carbon
dioxide flux in umol m-2 s-1 convolves straight to ppm. The spatial operator
files hold the seed-mean, time-summed footprint at every receptor together with
the gridded prior contribution of each component, so no footprint needs to be
re-read to answer a spatial question.

Stages
  budget     component budget at each tower, both gases
  peat       the peatland question, decomposed
  space      distance bands, provinces and districts
  age        how old the air carrying the signal is
  flux       posterior multipliers as implied emission, and the detection limit
  records    observed and modelled statistics over the record
  all        every stage in order
"""
from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd
import xarray as xr

import a84_bkt_jmb_two_receptor as T
import a99_operational_inversion as INV

ASSETS = __import__("pathlib").Path("/run/media/workstation-llm/HDD2/.assets")
DISTRICTS = ASSETS / "indonesia_kabkota_38prov.geojson"
TABLES = T.TABLES
OUT = T.ROOT / "outputs/operational"
INVENTORY = T.ROOT / "outputs/inventory"
SECONDS_PER_YEAR = 365.25 * 86400
MOLAR_MASS = {"CH4": 0.016043, "CO2": 0.044009}          # kg per mole
NAME = {"BKT": "Bukit Kototabang", "JMB": "Jambi"}
DISTANCE_BANDS = [(0, 50), (50, 200), (200, 500), (500, 1000), (1000, 1e9)]
AGE_BANDS = [(0, 6), (6, 24), (24, 48), (48, 72), (72, 120)]


def write(table: pd.DataFrame, stem: str) -> pd.DataFrame:
    OUT.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUT / f"attribution_{stem}.csv", index=False)
    print(f"  -> outputs/operational/attribution_{stem}.csv  ({len(table)} rows)", flush=True)
    return table


# ------------------------------------------------------------- the receptors

def screened() -> pd.DataFrame:
    """The methane receptors the inversion actually fits, so attribution matches it."""
    frame = INV.ch4_frame()
    return frame[["station", "time_utc"]].copy()


def spatial(code: str) -> xr.Dataset:
    path = T.OUT / "inversion" / f"spatial_operator_{code.lower()}.nc"
    if not path.exists():
        raise FileNotFoundError(f"{path} is missing; run a84 operator first")
    return xr.open_dataset(path)


def receptor_selection(dataset: xr.Dataset, code: str, keep: pd.DataFrame) -> np.ndarray:
    """Index of the receptors in a spatial operator that the inversion also uses."""
    wanted = set(pd.to_datetime(keep.loc[keep.station.eq(code), "time_utc"]))
    stamps = pd.to_datetime(dataset.receptor.values)
    index = np.array([i for i, s in enumerate(stamps) if s in wanted], dtype=int)
    if index.size == 0:
        raise ValueError(f"No screened receptors in the {code} spatial operator")
    return index


# ------------------------------------------------------------ static fields

def nmol_field(path, variable: str, gas: str, lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    """A kilograms-per-year-per-cell inventory field on a target grid, as flux."""
    with xr.open_dataset(path) as ds:
        values = ds[variable].load()
        src_lat, src_lon = ds.lat.values, ds.lon.values
    dlat, dlon = float(np.diff(src_lat).mean()), float(np.diff(src_lon).mean())
    edges = np.deg2rad(np.r_[src_lat - dlat / 2, src_lat[-1] + dlat / 2])
    band = 6371008.8 ** 2 * np.abs(np.diff(np.sin(edges))) * np.deg2rad(dlon)
    area = np.repeat(band[:, None], len(src_lon), axis=1)
    scale = 1e9 if gas == "CH4" else 1e6                 # nmol for ppb, umol for ppm
    flux = values.values / area / SECONDS_PER_YEAR / MOLAR_MASS[gas] * scale
    field = xr.DataArray(flux, coords=dict(lat=src_lat, lon=src_lon), dims=("lat", "lon"))
    aligned = field.interp(lat=("y", lat), lon=("x", lon), method="nearest")
    return np.nan_to_num(np.asarray(aligned.values, dtype=float)).reshape(len(lat), len(lon))


def peat_on(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    import a101_folu_proxy as F
    return F.peat_mask(lat, lon)


def region_masks(lat: np.ndarray, lon: np.ndarray, path, column_candidates) -> dict[str, np.ndarray]:
    """Cell-centre containment, so a border cell belongs to exactly one region."""
    import geopandas as gpd
    frame = gpd.read_file(path)
    column = next(c for c in column_candidates if c in frame.columns)
    mesh_lon, mesh_lat = np.meshgrid(lon, lat)
    points = gpd.GeoDataFrame(geometry=gpd.points_from_xy(mesh_lon.ravel(), mesh_lat.ravel()), crs=frame.crs)
    joined = gpd.sjoin(points, frame[[column, "geometry"]], how="left", predicate="within")
    joined = joined[~joined.index.duplicated()]
    labels = joined[column].to_numpy().reshape(mesh_lat.shape)
    return {str(n): labels == n for n in pd.unique(labels.ravel()) if isinstance(n, str)}


# ------------------------------------------------------------------ budget

def budget() -> pd.DataFrame:
    """What each source component contributes at each tower, in the observed unit."""
    keep = screened()
    rows = []

    sectors = pd.read_csv(TABLES / "sector_responses_base.csv", parse_dates=["time_utc"])
    sectors = sectors.merge(keep, on=["station", "time_utc"])
    sectors = sectors.groupby(["station", "time_utc", "source"], as_index=False).prior_enhancement_ppb.mean()
    ledger = pd.read_csv(INVENTORY / "local_inventory_ch4_2022_provincial_ledger.csv")
    weights = pd.read_csv(INVENTORY / "province_influence_ch4_2022.csv")
    factor = {}
    for station in weights.station.unique():
        share = weights[weights.station.eq(station)].set_index("province").percent / 100.0
        for edgar, group in ledger[ledger.pattern.eq("EDGAR")].groupby("edgar_sectors"):
            per_region = group.set_index("region").factor
            common = share.index.intersection(per_region.index)
            if common.empty:
                continue
            effective = float((share[common] * per_region[common]).sum() / share[common].sum())
            for sector in str(edgar).split(";"):
                factor[(station, f"CH4_{sector}")] = effective

    folu = folu_response()
    for code in ("BKT", "JMB"):
        block = sectors[sectors.station.eq(code)]
        per_source = block.groupby("source").prior_enhancement_ppb.agg(["mean", "std", "max"])
        total = float(per_source["mean"].drop(index=["soil_uptake"], errors="ignore").sum())
        total += float(folu.loc[folu.station.eq(code), "folu_3b2_ppb"].mean())
        for source, row in per_source.iterrows():
            scale = factor.get((code, source), 1.0)
            rows.append(dict(station=code, gas="CH4", unit="ppb", component=source,
                             prior_mean=round(row["mean"], 3), prior_sd=round(float(row["std"]), 3),
                             prior_max=round(row["max"], 3),
                             reported_mean=round(row["mean"] * scale, 3),
                             localisation_factor=round(scale, 4) if source.startswith("CH4_") else None,
                             share_percent=round(100 * row["mean"] / total, 2) if source != "soil_uptake" else None))
        mean_folu = float(folu.loc[folu.station.eq(code), "folu_3b2_ppb"].mean())
        rows.append(dict(station=code, gas="CH4", unit="ppb", component="FOLU_land_use_fire",
                         prior_mean=round(mean_folu, 3),
                         prior_sd=round(float(folu.loc[folu.station.eq(code), "folu_3b2_ppb"].std()), 3),
                         prior_max=round(float(folu.loc[folu.station.eq(code), "folu_3b2_ppb"].max()), 3),
                         reported_mean=round(mean_folu, 3), localisation_factor=1.0,
                         share_percent=round(100 * mean_folu / total, 2)))

    co2_sectors = pd.read_csv(TABLES / "co2_sector_responses.csv", parse_dates=["time_utc"])
    co2_base = pd.read_csv(TABLES / "co2_operator_base.csv", parse_dates=["time_utc"])
    co2_folu = pd.read_csv(TABLES / "co2_folu_response_full.csv", parse_dates=["time_utc"])
    for code in ("BKT", "JMB"):
        block = co2_sectors[co2_sectors.station.eq(code)]
        base = co2_base[co2_base.station.eq(code)]
        folu_block = co2_folu[co2_folu.station.eq(code)]
        pieces = {f"fossil_{s}": g.ppm for s, g in block.groupby("sector")}
        pieces["biosphere_uptake"] = base.bio_uptake_ppm
        pieces["biosphere_release"] = base.bio_release_ppm
        pieces["ocean"] = base.ocean_ppm
        pieces["fire"] = base.fire_ppm
        pieces["FOLU_drained_peat"] = folu_block.folu_3b1_ppm
        pieces["FOLU_land_use_fire"] = folu_block.folu_3b2_ppm
        positive = sum(float(v.mean()) for k, v in pieces.items() if k != "biosphere_uptake")
        for name, values in pieces.items():
            mean = float(values.mean())
            rows.append(dict(station=code, gas="CO2", unit="ppm", component=name,
                             prior_mean=round(mean, 4), prior_sd=round(float(values.std()), 4),
                             prior_max=round(float(values.max()), 4), reported_mean=round(mean, 4),
                             localisation_factor=None,
                             share_percent=round(100 * mean / positive, 2) if name != "biosphere_uptake" else None))
    return write(pd.DataFrame(rows), "budget")


def folu_response() -> pd.DataFrame:
    """Land-use methane at each receptor, convolved from the localised FOLU field.

    The reported Indonesian FOLU methane is land-use fire only. Drained organic
    soils are reported for carbon dioxide and nitrous oxide, not methane, so
    drained peat enters the methane budget through the wetland term and through
    whatever agricultural and waste emission sits on peat, not through a
    land-use fire category. That is a property of the national reporting, not an
    omission here, and the peat stage separates the three routes.
    """
    destination = TABLES / "ch4_folu_response_provincial.csv"
    if destination.exists():
        return pd.read_csv(destination, parse_dates=["time_utc"])
    keep = screened()
    rows = []
    for code in ("BKT", "JMB"):
        with spatial(code) as ds:
            index = receptor_selection(ds, code, keep)
            lat, lon = ds.lat.values, ds.lon.values
            field = nmol_field(INVENTORY / "local_inventory_ch4_2022_provincial.nc", "FOLU_3B2", "CH4", lat, lon)
            footprints = ds.footprint.isel(receptor=index).values
            stamps = pd.to_datetime(ds.receptor.values)[index]
        for stamp, footprint in zip(stamps, footprints):
            rows.append(dict(station=code, time_utc=stamp, folu_3b2_ppb=float((footprint * field).sum())))
    table = pd.DataFrame(rows)
    table.to_csv(destination, index=False)
    return table


# -------------------------------------------------------------------- peat

def peat() -> pd.DataFrame:
    """The peatland question: how much of each tower's signal comes off peat.

    Three routes are separated because they are three different processes with
    three different mitigation answers. Natural and rewetted peat swamp emits
    methane biologically and is carried by the wetland prior. Peat fire is
    episodic and is carried by the fire and land-use terms. Anthropogenic
    emission sitting on drained peatland, mostly agriculture and waste, is
    carried by the inventory. A cell is counted as peat if its centre falls
    inside the Indonesian peatland layer, so the count is a quarter-degree
    approximation to a much finer boundary and is stated as such.
    """
    keep = screened()
    ratio = localisation_ratio()
    rows = []
    for code in ("BKT", "JMB"):
        with spatial(code) as ds:
            index = receptor_selection(ds, code, keep)
            lat, lon = ds.lat.values, ds.lon.values
            mask = peat_on(lat, lon)
            footprints = ds.footprint.isel(receptor=index).values
            contributions = {str(c): ds.prior_contribution.isel(receptor=index).sel(component=c).values
                             for c in ds.component.values}
            folu_field = nmol_field(INVENTORY / "local_inventory_ch4_2022_provincial.nc", "FOLU_3B2", "CH4", lat, lon)
            stamps = pd.to_datetime(ds.receptor.values)[index]
        contributions["FOLU_land_use_fire"] = footprints * folu_field
        anthropogenic = contributions["anthro_near"] + contributions["anthro_far"]
        axes = (1, 2)
        sensitivity = footprints.sum(axis=axes)
        totals = {"footprint_sensitivity": footprints, "anthropogenic": anthropogenic,
                  "wetlands": contributions["wetlands"], "fire": contributions["fire"],
                  "FOLU_land_use_fire": contributions["FOLU_land_use_fire"]}
        source_total = (anthropogenic + contributions["wetlands"] + contributions["fire"] +
                        contributions["FOLU_land_use_fire"]).sum(axis=axes)
        for name, field in totals.items():
            on_peat = field[:, mask].sum(axis=1)
            everywhere = field.sum(axis=axes)
            with np.errstate(invalid="ignore", divide="ignore"):
                share = np.where(everywhere > 0, 100 * on_peat / everywhere, np.nan)
            rows.append(dict(station=code, quantity=name,
                             unit="ppm per umol m-2 s-1" if name == "footprint_sensitivity" else "ppb",
                             over_peat_mean=round(float(np.nanmean(on_peat)), 4),
                             over_peat_sd=round(float(np.nanstd(on_peat, ddof=1)), 4),
                             over_peat_max=round(float(np.nanmax(on_peat)), 4),
                             total_mean=round(float(np.nanmean(everywhere)), 4),
                             peat_share_percent=round(float(np.nanmean(share)), 2),
                             share_of_source_signal_percent=round(
                                 float(np.nanmean(100 * on_peat / source_total)), 2)
                             if name != "footprint_sensitivity" else None,
                             receptors=int(len(index)), peat_cells=int(mask.sum())))
        peat_signal = sum(field[:, mask].sum(axis=1) for name, field in totals.items()
                          if name != "footprint_sensitivity")
        rows.append(dict(station=code, quantity="all peat routes combined", unit="ppb",
                         over_peat_mean=round(float(peat_signal.mean()), 4),
                         over_peat_sd=round(float(peat_signal.std(ddof=1)), 4),
                         over_peat_max=round(float(peat_signal.max()), 4),
                         total_mean=round(float(source_total.mean()), 4),
                         peat_share_percent=round(float(100 * peat_signal.mean() / source_total.mean()), 2),
                         share_of_source_signal_percent=round(float(np.mean(100 * peat_signal / source_total)), 2),
                         receptors=int(len(index)), peat_cells=int(mask.sum())))
        # the same decomposition on the reported inventory, which is nine times smaller
        # in the fugitive sector; the anthropogenic term is rescaled by the station
        # ratio the inversion itself uses, so the wetland and fire terms are untouched
        scaled_anthro = anthropogenic[:, mask].sum(axis=1) * ratio[code]
        reported_peat = (scaled_anthro + contributions["wetlands"][:, mask].sum(axis=1) +
                         contributions["fire"][:, mask].sum(axis=1) +
                         contributions["FOLU_land_use_fire"][:, mask].sum(axis=1))
        reported_total = (anthropogenic.sum(axis=axes) * ratio[code] + contributions["wetlands"].sum(axis=axes) +
                          contributions["fire"].sum(axis=axes) +
                          contributions["FOLU_land_use_fire"].sum(axis=axes))
        rows.append(dict(station=code, quantity="all peat routes, reported inventory", unit="ppb",
                         over_peat_mean=round(float(reported_peat.mean()), 4),
                         over_peat_sd=round(float(reported_peat.std(ddof=1)), 4),
                         over_peat_max=round(float(reported_peat.max()), 4),
                         total_mean=round(float(reported_total.mean()), 4),
                         peat_share_percent=round(float(100 * reported_peat.mean() / reported_total.mean()), 2),
                         share_of_source_signal_percent=round(float(np.mean(100 * reported_peat / reported_total)), 2),
                         receptors=int(len(index)), peat_cells=int(mask.sum())))
        _ = sensitivity, stamps
    return write(pd.DataFrame(rows), "peat")


def localisation_ratio() -> dict[str, float]:
    """How far localising the inventory moves the anthropogenic response at each tower."""
    table = pd.read_csv(OUT / "attribution_budget.csv")
    block = table[table.gas.eq("CH4") & table.component.str.startswith("CH4_")]
    return {code: float(g.reported_mean.sum() / g.prior_mean.sum()) for code, g in block.groupby("station")}


# ------------------------------------------------------------------- space

def space() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Where the signal comes from: distance band, province, district."""
    keep = screened()
    distance_rows, province_rows, district_rows = [], [], []
    for code in ("BKT", "JMB"):
        with spatial(code) as ds:
            index = receptor_selection(ds, code, keep)
            lat, lon = ds.lat.values, ds.lon.values
            distance = ds.distance_km.values
            footprints = ds.footprint.isel(receptor=index).values
            components = {str(c): ds.prior_contribution.isel(receptor=index).sel(component=c).values
                          for c in ds.component.values}
        anthropogenic = components["anthro_near"] + components["anthro_far"]
        fields = {"footprint_sensitivity": footprints, "anthropogenic": anthropogenic,
                  "wetlands": components["wetlands"], "fire": components["fire"]}
        for name, field in fields.items():
            everywhere = field.sum(axis=(1, 2))
            for lo, hi in DISTANCE_BANDS:
                band = (distance >= lo) & (distance < hi)
                inside = field[:, band].sum(axis=1)
                distance_rows.append(dict(station=code, quantity=name,
                                          band_km=f"{lo:.0f} to {hi:.0f}" if hi < 1e8 else "beyond 1000",
                                          mean=round(float(inside.mean()), 4),
                                          share_percent=round(float(100 * inside.mean() / everywhere.mean()), 2)))
        for label, path, candidates, sink in (
                ("province", ASSETS / "indonesia_38prov.geojson", ("provinsi", "PROVINSI", "name"), province_rows),
                ("district", DISTRICTS, ("kabupaten", "kabkota", "KABKOT", "name"), district_rows)):
            masks = region_masks(lat, lon, path, candidates)
            signal = anthropogenic + components["wetlands"] + components["fire"]
            everywhere = signal.sum(axis=(1, 2)).mean()
            anthro_everywhere = anthropogenic.sum(axis=(1, 2)).mean()
            for region, mask in masks.items():
                value = float(signal[:, mask].sum(axis=1).mean())
                if value <= 0:
                    continue
                sink.append(dict(station=code, level=label, region=region,
                                 mean_ppb=round(value, 4),
                                 share_percent=round(100 * value / everywhere, 3),
                                 anthropogenic_share_percent=round(
                                     float(100 * anthropogenic[:, mask].sum(axis=1).mean() / anthro_everywhere), 3),
                                 sensitivity_share_percent=round(
                                     float(100 * footprints[:, mask].sum(axis=1).mean() /
                                           footprints.sum(axis=(1, 2)).mean()), 3)))
    distances = write(pd.DataFrame(distance_rows), "distance")
    provinces = pd.DataFrame(province_rows).sort_values(["station", "share_percent"], ascending=[True, False])
    districts = pd.DataFrame(district_rows).sort_values(["station", "share_percent"], ascending=[True, False])
    return distances, write(provinces, "provinces"), write(districts, "districts")


# --------------------------------------------------------------------- age

def age() -> pd.DataFrame:
    """How old the air carrying the signal is, from the per-hour footprint sum."""
    keep = screened()
    lag = pd.read_csv(TABLES / "lag_responses_base.csv", parse_dates=["time_utc"])
    lag = lag.merge(keep, on=["station", "time_utc"])
    rows = []
    for code, block in lag.groupby("station"):
        total = block.groupby("time_utc").sensitivity.sum()
        for lo, hi in AGE_BANDS:
            band = block[(block.lag_hours >= lo) & (block.lag_hours < hi)]
            per_receptor = band.groupby("time_utc").sensitivity.sum().reindex(total.index).fillna(0.0)
            rows.append(dict(station=code, age_hours=f"{lo} to {hi}",
                             sensitivity_share_percent=round(float(100 * (per_receptor / total).mean()), 2)))
        median = block.groupby("time_utc").apply(
            lambda g: float(np.interp(0.5, np.cumsum(g.sort_values("lag_hours").sensitivity) /
                                      g.sensitivity.sum(), g.sort_values("lag_hours").lag_hours)),
            include_groups=False)
        rows.append(dict(station=code, age_hours="median age of the signal",
                         sensitivity_share_percent=round(float(median.mean()), 2)))
    return write(pd.DataFrame(rows), "age")


# -------------------------------------------------------------------- flux

SEEN_PROVINCES = 1.0        # a province carrying at least this percent of a tower's signal


def edgar_total(gas: str, year: int, lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    """The global gridded inventory summed over the crosswalked sectors, kg per year per cell."""
    import a100_local_inventory as L
    sectors = sorted({s for code in ("1A", "1B", "2", "3A", "4") for s in L.CROSSWALK[code][0]})
    available = [s for s in sectors if (L.EDGAR[gas] / f"{gas}_{s}_{year}.nc").exists()]
    area = L.cell_area(lat, lon)
    total = np.zeros((len(lat), len(lon)))
    for sector in available:
        field = L.subset(L.sector_field(gas, sector, year), (lon[0], lat[0], lon[-1], lat[-1]))
        total = total + field.mean("time").values * area * SECONDS_PER_YEAR
    return total


def seen_region(lat: np.ndarray, lon: np.ndarray) -> tuple[np.ndarray, list[str]]:
    """The provinces either tower draws at least one percent of its signal from.

    A multiplier constrains the emission the footprint actually weighs, so this
    is the region a posterior number may be quoted over. Scaling a national
    total by the same multiplier would assume the correction holds in provinces
    neither tower can see, which is the assumption the readiness gate refuses.
    """
    table = pd.read_csv(OUT / "attribution_provinces.csv")
    names = sorted(set(table.loc[table.share_percent >= SEEN_PROVINCES, "region"]))
    masks = region_masks(lat, lon, ASSETS / "indonesia_38prov.geojson", ("provinsi", "PROVINSI", "name"))
    mask = np.zeros((len(lat), len(lon)), dtype=bool)
    for name in names:
        if name in masks:
            mask |= masks[name]
    return mask, names


def flux() -> pd.DataFrame:
    """Posterior multipliers read as emission over the region the towers weigh.

    A multiplier is dimensionless and applies to the prior where the footprint
    has weight, so it is quoted over the provinces the towers see rather than
    nationally. The detection limit is the more useful operational number,
    because it says how large an emission change the present network could see
    at all, independently of whether the prior is right.
    """
    with xr.open_dataset(INVENTORY / "local_inventory_ch4_2022_provincial.nc") as ds:
        lat, lon = ds.lat.values, ds.lon.values
        localised = sum(ds[v].values for v in ds.data_vars if not v.startswith("FOLU_"))
        folu_ch4 = ds.FOLU_3B2.values
    mask, names = seen_region(lat, lon)
    ch4_anthro_global = edgar_total("CH4", 2022, lat, lon)[mask].sum() / 1e6
    ch4_anthro_reported = localised[mask].sum() / 1e6
    ch4_folu = folu_ch4[mask].sum() / 1e6
    co2_anthro = edgar_total("CO2", 2023, lat, lon)[mask].sum() / 1e6
    # the full carbon dioxide localisation, which is the one the inversion's land-use
    # response was built from; the folu-labelled file is a small test export
    with xr.open_dataset(INVENTORY / "local_inventory_co2_2023_full.nc") as ds:
        co2_folu = float(ds.FOLU_3B1.values[mask].sum()) / 1e6
    region = {
        ("ch4", "EDGAR", "anthro"): ch4_anthro_global, ("ch4", "reported", "anthro"): ch4_anthro_reported,
        ("ch4", "EDGAR", "folu"): ch4_folu, ("ch4", "reported", "folu"): ch4_folu,
        ("co2", "EDGAR", "anthro"): co2_anthro, ("co2", "reported", "anthro"): co2_anthro,
        ("co2", "EDGAR", "folu"): co2_folu, ("co2", "reported", "folu"): co2_folu,
    }
    print(f"  provinces the towers see: {', '.join(n.title() for n in names)}", flush=True)
    rows = []
    verdicts = json.loads((OUT / "inversion_readiness.json").read_text())
    for verdict in verdicts:
        if "receptors" not in verdict or verdict["scale"] != "daily":
            continue
        tag = f"{verdict['gas']}{verdict['biosphere'] if verdict['biosphere'] != 'diagnostic' else ''}"
        tag += f"_{verdict['inventory']}" if verdict["inventory"] != "EDGAR" else ""
        tag += f"_folu{verdict['folu']}" if verdict.get("folu", "excluded") != "excluded" else ""
        path = OUT / f"inversion_{tag}_daily_parameters.csv"
        if not path.exists():
            continue
        inventory = "reported" if verdict["inventory"] != "EDGAR" else "EDGAR"
        for row in pd.read_csv(path).itertuples():
            sd_log = (np.log(row.q975) - np.log(row.q025)) / (2 * 1.959964)
            kind = ("folu" if "folu" in row.parameter or "drainage" in row.parameter
                    else "anthro" if row.parameter.startswith(("anthro", "fossil")) else None)
            total = region.get((verdict["gas"], inventory, kind)) if kind else None
            rows.append(dict(gas=verdict["gas"], prior=verdict["prior"], parameter=row.parameter,
                             multiplier=round(row.multiplier, 3),
                             ci_lo=round(row.q025, 3), ci_hi=round(row.q975, 3),
                             uncertainty_ratio=round(row.uncertainty_ratio, 3),
                             consistent_with_prior=bool(row.q025 <= 1.0 <= row.q975),
                             detectable_change_percent=round(2 * sd_log * 100, 1),
                             prior_region_Gg=round(total, 1) if total else None,
                             posterior_region_Gg=round(total * row.multiplier, 1) if total else None,
                             posterior_lo_Gg=round(total * row.q025, 1) if total else None,
                             posterior_hi_Gg=round(total * row.q975, 1) if total else None))
    return write(pd.DataFrame(rows), "flux")


# ----------------------------------------------------------------- records

def records() -> pd.DataFrame:
    """Observed and modelled statistics, so the reader can size the problem."""
    rows = []
    ch4 = INV.ch4_frame()
    ch4_components = ["anthro_near_ppb", "anthro_far_ppb", "wetlands_ppb", "fire_ppb"]
    for code, block in ch4.groupby("station"):
        modelled = block[ch4_components].sum(axis=1)
        rows.append(dict(gas="CH4", unit="ppb", station=code, receptors=len(block),
                         first=str(block.time_utc.min().date()), last=str(block.time_utc.max().date()),
                         observed_mean=round(float(block.observed.mean()), 1),
                         observed_sd=round(float(block.observed.std()), 1),
                         observed_range=round(float(block.observed.max() - block.observed.min()), 1),
                         background_mean=round(float(block.base.mean()), 1),
                         observed_enhancement=round(float((block.observed - block.base).mean()), 1),
                         modelled_source_signal=round(float(modelled.mean()), 1),
                         modelled_over_observed=round(float(modelled.mean() / (block.observed - block.base).mean()), 2)
                         if (block.observed - block.base).mean() != 0 else None))
    saved = INV.BIOSPHERE, INV.FOLU_LABEL
    INV.BIOSPHERE, INV.FOLU_LABEL = "", "full"
    try:
        co2 = INV.co2_frame()
    finally:
        INV.BIOSPHERE, INV.FOLU_LABEL = saved
    co2_components = ["fossil_near_ppm", "fossil_far_ppm", "bio_net_BKT_ppm", "bio_net_JMB_ppm", "folu_3b1_ppm"]
    for code, block in co2.groupby("station"):
        modelled = block[[c for c in co2_components if c in block.columns]].sum(axis=1)
        rows.append(dict(gas="CO2", unit="ppm", station=code, receptors=len(block),
                         first=str(block.time_utc.min().date()), last=str(block.time_utc.max().date()),
                         observed_mean=round(float(block.observed.mean()), 2),
                         observed_sd=round(float(block.observed.std()), 2),
                         observed_range=round(float(block.observed.max() - block.observed.min()), 2),
                         background_mean=round(float(block.base.mean()), 2),
                         observed_enhancement=round(float((block.observed - block.base).mean()), 2),
                         modelled_source_signal=round(float(modelled.mean()), 2),
                         modelled_over_observed=round(float(modelled.mean() / (block.observed - block.base).mean()), 2)
                         if (block.observed - block.base).mean() != 0 else None))
    return write(pd.DataFrame(rows), "records")


STAGES = {"budget": budget, "peat": peat, "space": space, "age": age, "flux": flux, "records": records}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", nargs="?", default="all", choices=sorted(STAGES) + ["all"])
    chosen = parser.parse_args().stage
    for name in (STAGES if chosen == "all" else [chosen]):
        print(f"== {name}", flush=True)
        STAGES[name]()
