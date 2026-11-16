#!/usr/bin/env python3
"""Exact localized CH4 operators on stored hourly footprints; no model rerun.

The annual inventory ledger supplies spatial factors, not annual replacement
fluxes: EDGAR's monthly temporal pattern is retained. Only Indonesian cells
are rescaled, independently by sector and region. Foreign cells remain unity.
All generated files live in a separate revised run, preserving the benchmark.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr
from shapely import make_valid

import a71_domain_budget_extension as E
import a84_bkt_jmb_two_receptor as T
import a100_local_inventory as L
import ghg_common as G

OUT = T.ROOT / "outputs/operational/revised"
ASSET = T.ROOT.parent / ".assets/indonesia_38prov.geojson"
LABELS = ("EDGAR", "primap", "provincial")
MIN_PBLH = 300.0


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def region_masks(lat: np.ndarray, lon: np.ndarray) -> tuple[dict[str, np.ndarray], dict]:
    """Shared provincial geometry, repaired only in memory; exclusive cells."""
    regions = gpd.read_file(ASSET).to_crs(4326)
    column = next(c for c in ("provinsi", "PROVINSI", "WADMPR", "name", "NAME_1") if c in regions)
    invalid = ~regions.geometry.is_valid
    regions.loc[invalid, "geometry"] = regions.loc[invalid, "geometry"].map(make_valid)
    yy, xx = np.meshgrid(lat, lon, indexing="ij")
    points = gpd.GeoDataFrame(geometry=gpd.points_from_xy(xx.ravel(), yy.ravel()), crs=4326)
    joined = gpd.sjoin(points, regions[[column, "geometry"]], how="left", predicate="within")
    overlap_cells = int(joined.index[joined.index.duplicated()].nunique())
    # Shared administrative assets contain a few overlapping cells. Retain the
    # first source feature, as the original inventory ledger did; record the
    # tie break explicitly, and assign no point to two provinces.
    joined = joined.sort_values("index_right", kind="stable").sort_index(kind="stable")
    joined = joined[~joined.index.duplicated()]
    labels = joined[column].fillna("").astype(str).str.upper().to_numpy().reshape(yy.shape)
    return {name: labels == name for name in np.unique(labels) if name}, dict(
        repaired_geometries=int(invalid.sum()), overlap_cells=overlap_cells,
        tie_break="first feature in immutable shared asset; exclusive cell-centre assignment")


def factor_grid(ledger: pd.DataFrame, sector: str, masks: dict[str, np.ndarray]) -> np.ndarray:
    """One outside Indonesia; one factor per covered sector/region inside."""
    shape = next(iter(masks.values())).shape
    out = np.ones(shape)
    indonesia = np.logical_or.reduce(list(masks.values()))
    groups = ledger[ledger.edgar_sectors.str.split(";").apply(lambda s: sector in s)]
    if groups.empty:
        raise ValueError(f"No ledger factor for {sector}")
    assigned = np.zeros(shape, bool)
    for row in groups.itertuples():
        mask = indonesia if row.region_level == "national" else masks.get(str(row.region).upper())
        if mask is None:
            raise ValueError(f"Ledger region not on the receptor grid: {row.region}")
        if (assigned & mask).any() or not np.isfinite(row.factor) or row.factor < 0:
            raise ValueError(f"Invalid or overlapping factor for {sector}/{row.region}")
        out[mask] = row.factor
        assigned |= mask
    # The existing provincial ledger covers asset-bearing provinces only for
    # several sectors. Match its explicit mixed-source field: retain EDGAR in
    # uncovered provinces, never infer zero emissions from an absent asset.
    # This is a mixed prior, not a fully conserved provincial reported total.
    return out


def convolve_months(field: xr.DataArray, monthly: xr.DataArray) -> np.ndarray:
    """ppb maps from ppm/(umol m-2 s-1) times umol CH4 m-2 s-1.

    Grouping hourly sensitivities by footprint month is exactly equivalent to
    hour-by-hour multiplication for fluxes constant within each month. The
    factor 1000 converts ppm to ppb, not a mass conversion.
    """
    months = pd.DatetimeIndex(field.time.values).to_period("M").to_timestamp()
    result = np.zeros((monthly.sizes["source"], field.sizes["lat"], field.sizes["lon"]))
    for month in months.unique():
        sensitivity = field.values[months == month].sum(axis=0)
        result += monthly.sel(month=month).transpose("source", "lat", "lon").values * sensitivity * 1000
    return result


def afternoon_observations(frame: pd.DataFrame) -> pd.DataFrame:
    """Harmonized, instrument-flagged CH4; >=2 of 05/06/07 UTC hours.

    No residual-dependent outlier removal. Return count and spread as evidence
    of representativeness; the mixing-depth criterion is applied separately.
    """
    result = frame.copy()
    for station, group in result.groupby("station"):
        record = G.apply_flags(G.load_station(station)).set_index("time_utc").sort_index()
        if record.index.duplicated().any():
            raise ValueError(f"Duplicate harmonized hours: {station}")
        for index, row in group.iterrows():
            hours = pd.date_range(row.time_utc - pd.Timedelta(hours=1), periods=3, freq="h")
            values = record.ch4.reindex(hours).dropna()
            result.loc[index, "observed"] = values.mean() if len(values) >= 2 else np.nan
            result.loc[index, "observation_hours"] = len(values)
            result.loc[index, "observation_sd"] = values.std() if len(values) >= 2 else np.nan
    return result


def screened() -> pd.DataFrame:
    base = pd.read_csv(T.TABLES / "operator_base.csv", parse_dates=["time_utc"])
    base["eligible"] = base.transport_usable & base.time_utc.dt.hour.eq(6) & base.PBLH.ge(MIN_PBLH)
    return afternoon_observations(base[base.eligible].copy()).dropna(subset=["observed"])


def localized_monthly(monthly: xr.DataArray, code: str) -> tuple[dict[str, xr.DataArray], list[dict], dict]:
    """Apply factors on native EDGAR cells, then conservative area remapping.

    Multiplication and remapping do not commute at provincial/coastal borders.
    Scaling the quarter-degree receptor cells directly would misallocate those
    cells. Native monthly fluxes are preserved, not replaced by annual means.
    """
    anthrop = [str(s) for s in monthly.source.values if str(s).startswith("CH4_")]
    target_lat, target_lon = monthly.lat.values, monthly.lon.values
    ledgers = {label: pd.read_csv(T.ROOT / f"outputs/inventory/local_inventory_ch4_2022_{label}_ledger.csv").query("pattern == 'EDGAR'") for label in LABELS[1:]}
    rebuilt = {label: [] for label in LABELS}
    mass = {}
    masks = None
    repairs = {}
    for source in anthrop:
        path = T.SOURCES / f"edgar_v8/{source}_{T.EDGAR_YEAR}.nc"
        with xr.open_dataset(path) as ds:
            raw = ds.fluxes.sel(lat=slice(target_lat[0] - .5, target_lat[-1] + .5),
                               lon=slice(target_lon[0] - .5, target_lon[-1] + .5)).load()
        if raw.attrs.get("units", "").replace(" ", "") != "kgm-2s-1":
            raise ValueError(f"Unexpected native EDGAR unit: {source}")
        if masks is None:
            masks, repairs = region_masks(raw.lat.values, raw.lon.values)
        area = L.cell_area(raw.lat.values, raw.lon.values)
        annual = raw.mean("time").values * area * L.SECONDS_PER_YEAR
        for label in LABELS:
            factors = np.ones_like(annual) if label == "EDGAR" else factor_grid(ledgers[label], source[4:], masks)
            values = []
            for month in pd.DatetimeIndex(monthly.month.values):
                # Retain the prepared input's float32 unit-conversion order so
                # the unscaled reconstruction is bitwise comparable; spatial
                # factors then act in float64 before conservative remapping.
                flux = (raw.isel(time=month.month - 1).values * 1e9 / T.MW["CH4"]) * factors
                values.append(E.remap_nonnegative(flux, raw.lat.values, raw.lon.values, target_lat, target_lon))
            rebuilt[label].append(values)
            if label != "EDGAR":
                for row in ledgers[label].itertuples():
                    if source[4:] not in row.edgar_sectors.split(";"):
                        continue
                    mask = np.logical_or.reduce(list(masks.values())) if row.region_level == "national" else masks[row.region.upper()]
                    key = (label, row.region, row.edgar_sectors)
                    entry = mass.setdefault(key, dict(station_grid=code, inventory=label, region=row.region,
                                                      sectors=row.edgar_sectors, reported_kg=float(row.reported_kg), applied_kg=0.))
                    entry["applied_kg"] += float((annual * factors)[mask].sum())
    result = {}
    for label in LABELS:
        result[label] = xr.DataArray(np.asarray(rebuilt[label]), dims=("source", "month", "lat", "lon"),
                                    coords=dict(source=anthrop, month=monthly.month.values, lat=target_lat, lon=target_lon),
                                    attrs=dict(units="umol m-2 s-1", localization_grid="native EDGAR 0.1 degree"))
    original = monthly.sel(source=anthrop).transpose("source", "month", "lat", "lon").values
    if not np.allclose(result["EDGAR"].values, original, atol=1e-12, rtol=1e-10):
        raise ValueError("Native reconstruction does not match the prepared EDGAR monthly input")
    rows = list(mass.values())
    for row in rows:
        row["relative_mass_error"] = (row["applied_kg"] - row["reported_kg"]) / max(1., row["reported_kg"])
    return result, rows, repairs


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    keep = screened()
    keep.to_csv(OUT / "ch4_receptors.csv", index=False)
    rows, repairs, mass_audits = [], {}, []
    for code, group in keep.groupby("station"):
        with xr.open_dataset(T.INPUTS / f"{code.lower()}_monthly_flux.nc") as ds:
            monthly = ds.flux.load()
        localized, mass_audit, repairs[code] = localized_monthly(monthly, code)
        mass_audits.extend(mass_audit)
        _, rlat, rlon, _ = T.STATIONS[code]
        yy, xx = np.meshgrid(monthly.lat.values, monthly.lon.values, indexing="ij")
        _, _, distance = T.GEOD.inv(np.full(xx.shape, rlon), np.full(yy.shape, rlat), xx, yy)
        near = distance <= 500_000
        sources = [str(s) for s in localized["EDGAR"].source.values]
        for stamp in group.time_utc:
            for seed in T.SEEDS:
                directory = T.run_dir(code, seed, stamp)
                field, _, _ = E.read_footprint(directory)
                if not np.array_equal(field.lat, monthly.lat) or not np.array_equal(field.lon, monthly.lon):
                    raise ValueError(f"Footprint/flux grid mismatch: {code}/{stamp}/{seed}")
                for label in LABELS:
                    maps = convolve_months(field, localized[label])
                    for i, source in enumerate(sources):
                        rows.append(dict(station=code, time_utc=stamp, seed=seed, inventory=label, source=source,
                                         near_ppb=float(maps[i][near].sum()), far_ppb=float(maps[i][~near].sum())))
                del field, maps
            print(f"exact CH4 response {code} {stamp:%Y-%m-%d}", flush=True)
    sectors = pd.DataFrame(rows)
    sectors.to_csv(OUT / "ch4_sector_members.csv", index=False)
    members = sectors.groupby(["station", "time_utc", "inventory", "seed"], as_index=False)[["near_ppb", "far_ppb"]].sum()
    members["total_ppb"] = members.near_ppb + members.far_ppb
    responses = members.groupby(["station", "time_utc", "inventory"]).agg(
        anthro_near_ppb=("near_ppb", "mean"), anthro_far_ppb=("far_ppb", "mean"),
        anthro_near_ppb_seed_sd=("near_ppb", "std"), anthro_far_ppb_seed_sd=("far_ppb", "std"),
        anthro_total_seed_sd=("total_ppb", "std")).reset_index()
    benchmark = keep.merge(responses[responses.inventory.eq("EDGAR")], on=["station", "time_utc"], suffixes=("_old", "_exact"))
    discrepancy = max(float(np.abs(benchmark[f"anthro_{band}_ppb_old"] - benchmark[f"anthro_{band}_ppb_exact"]).max()) for band in ("near", "far"))
    if discrepancy > 1e-8:
        raise ValueError(f"Original operator reconstruction failed: {discrepancy}")
    responses.to_csv(OUT / "ch4_exact_responses.csv", index=False)
    pd.DataFrame(mass_audits).to_csv(OUT / "native_ledger_mass_audit.csv", index=False)
    receipt = dict(shared_asset_sha256=sha256(ASSET), geometry_audit=repairs,
                   original_operator_max_abs_error_ppb=discrepancy, receptor_count=len(keep),
                   monthly_units=monthly.attrs.get("units"), foreign_cells="unchanged", month_boundaries="footprint hour",
                   uncovered_provincial_cells="EDGAR retained; not inferred zero; mixed proxy prior",
                   factors_applied_before_remapping=True, native_grid="0.1 degree",
                   ledgers={label: sha256(T.ROOT / f"outputs/inventory/local_inventory_ch4_2022_{label}_ledger.csv") for label in LABELS[1:]})
    (OUT / "response_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    build()
