#!/usr/bin/env python3
"""Inventory convolution for the extended 26 September 2019 forward case.

Applies the September 2019 EDGAR v8.0 sector fluxes and GFED5.1 daily fire
fluxes to the 120 h widened-domain footprints (GFS three-seed mean, its
1,000 m layer, and the ERA5 three-seed mean), and recomputes the published
72 h regional case on the same code path as a consistency check.

Local GFED extracts cover methane fire on the wide grid for the whole window,
but CO2 and CO fire only for 23 to 26 September on the regional box; those
two gases are therefore reported as lower bounds for the extended case.
Outputs: outputs/hysplit/revision/tables/forward_extension_*.csv.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import a43_bkt_source_analysis as src
import a74_bkt_simulation_revision as rev
import a76_bkt_era5_driver as era
from bkt_footprint_spatial import cell_area_km2

ROOT = rev.ROOT
TABLES = ROOT / "outputs/hysplit/revision/tables"
LABELS = {"AGRICULTURE": "Agriculture", "BUILDINGS": "Buildings", "FUEL_EXPLOITATION": "Fuel exploitation",
          "IND_COMBUSTION": "Industrial combustion", "IND_PROCESSES": "Industrial processes",
          "POWER_INDUSTRY": "Power industry", "TRANSPORT": "Transport", "WASTE": "Waste"}


def fields() -> dict[str, xr.DataArray]:
    with xr.open_dataset(ROOT / "outputs/hysplit/gfs/analysis/GFS_ensemble.nc") as ds:
        old = ds.footprint_sensitivity.load()
    with xr.open_dataset(ROOT / "outputs/hysplit/revision/ensemble_mean/forward_bkt_20190926T0100Z.nc", engine="h5netcdf") as ds:
        new = ds.layer_sensitivity.load()
    members = []
    for seed in rev.SEEDS:
        f, _ = rev.read_layers(era.RUNS / f"forward_s{seed}" / f"bkt_{rev.FORWARD_CASE:%Y%m%dT%H%MZ}")
        members.append(f.sel(layer=1))
    return {"GFS_72h_regional": old, "GFS_120h_wide": new.sel(layer=1, drop=True),
            "GFS_120h_wide_1000m_layer": new.sel(layer=2, drop=True), "ERA5_120h": xr.concat(members, dim="m").mean("m")}


def gfed_hourly(field: xr.DataArray, gas: str) -> tuple[np.ndarray, str]:
    """Daily GFED mass -> flux on the footprint grid for every source hour; returns (hourly, coverage)."""
    days = pd.DatetimeIndex(field.time.values).normalize()
    if gas == "CH4" and field.lon.values[0] < 84:
        path = ROOT / "data/bkt_sources/gfed51/GFED51_20190904_30_wide.npz"; coverage = "complete"
    elif field.lon.values[0] < 84:
        path = ROOT / "data/bkt_sources/gfed51/GFED51_20190923_26_region.npz"; coverage = "lower bound: 23-26 Sep, 84-117E 11S-11N only"
    else:
        path = ROOT / "data/bkt_sources/gfed51/GFED51_20190923_26_region.npz"; coverage = "complete"
    meta = json.loads(path.with_suffix(".npz.json").read_text())
    with np.load(path) as s:
        lat, lon = s["lat"], s["lon"]; y, x = np.argsort(lat), np.argsort(lon); lat, lon = lat[y], lon[x]
        dates = (pd.Timestamp("1800-01-01") + pd.to_timedelta(s["time"], unit="h")).normalize()
        mass = s[gas][:, y, :][:, :, x].astype(float)
    if meta["units"][gas] != f"g {gas} per day":
        raise ValueError("Unexpected GFED units")
    flux = mass / (cell_area_km2(lat, lon) * 1e6)[None] / 86400 * 1e6 / src.MW[gas]
    tl, tn = field.lat.values, field.lon.values
    inside = (tl >= lat[0]) & (tl <= lat[-1]); jnside = (tn >= lon[0]) & (tn <= lon[-1])
    sub_lat, sub_lon = tl[inside], tn[jnside]
    matched = {d: src.matching_flux(day, lat, lon, sub_lat, sub_lon) for d, day in zip(dates, flux)}
    hourly = np.zeros((len(days), len(tl), len(tn)))
    for k, d in enumerate(days):
        if d in matched:
            hourly[k][np.ix_(inside, jnside)] = matched[d]
    if coverage == "complete" and not all(d in matched for d in days.unique()):
        coverage = f"lower bound: {sum(d in matched for d in days.unique())} of {len(days.unique())} days"
    return hourly, coverage


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    obs = pd.read_csv(ROOT / "outputs/hysplit/gfs/analysis/tables/observation_context_summary.csv").set_index("species")
    observed_co = float(obs.loc["CO", "receptor_value"])
    sector_rows, fire_rows, summary = [], [], []
    for case, field in fields().items():
        lat, lon = field.lat.values, field.lon.values
        wide = lon[0] < 84
        bounds = (-31, 31, 49, 152) if wide else (-11, 11, 84, 117)
        agg = field.sum("time").values
        totals = {"CO2": 0., "CH4": 0.}
        for gas, sector, flux, _ in src.edgar_fluxes(lat, lon, bounds):
            value = float((agg * flux).sum()) * (1 if gas == "CO2" else 1000)
            totals[gas] += value
            sector_rows.append(dict(case=case, gas=gas, sector=LABELS[sector], enhancement=value, unit="ppm" if gas == "CO2" else "ppb"))
        fire = {}
        for gas in ("CO2", "CH4", "CO"):
            hourly, coverage = gfed_hourly(field, gas)
            value = float((field.values * hourly).sum()) * (1 if gas == "CO2" else 1000)
            fire[gas] = value
            fire_rows.append(dict(case=case, gas=gas, enhancement=value, unit="ppm" if gas == "CO2" else "ppb", coverage=coverage))
        summary.append(dict(case=case, hours=int(field.sizes["time"]), integrated_sensitivity=float(field.sum()),
            anthropogenic_co2_ppm=totals["CO2"], anthropogenic_ch4_ppb=totals["CH4"], fire_co2_ppm=fire["CO2"],
            fire_ch4_ppb=fire["CH4"], fire_co_ppb=fire["CO"], observed_co_ppb=observed_co,
            fire_co_to_observed_percent=100 * fire["CO"] / observed_co))
        print(f"{case:28s} anthro CO2 {totals['CO2']:.3f} ppm CH4 {totals['CH4']:.1f} ppb | fire CO2 {fire['CO2']:.2f} CH4 {fire['CH4']:.1f} CO {fire['CO']:.0f} ppb ({100 * fire['CO'] / observed_co:.0f}% of observed)", flush=True)
    pd.DataFrame(sector_rows).to_csv(TABLES / "forward_extension_sectors.csv", index=False)
    pd.DataFrame(fire_rows).to_csv(TABLES / "forward_extension_fire.csv", index=False)
    pd.DataFrame(summary).to_csv(TABLES / "forward_extension_summary.csv", index=False)
    # Consistency of the recomputed 72 h case with the published tables.
    published = pd.read_csv(ROOT / "outputs/hysplit/gfs/analysis/tables/fire_contributions.csv")
    pub = published[published.run.str.startswith("GFS_") & ~published.run.str.contains("height")].groupby("gas").enhancement.mean()
    mine = pd.DataFrame(fire_rows).query("case == 'GFS_72h_regional'").set_index("gas").enhancement
    for gas in ("CO2", "CH4", "CO"):
        if not np.isclose(mine[gas], pub[gas], rtol=1e-6):
            raise ValueError(f"Recomputed 72 h fire {gas} {mine[gas]} differs from published {pub[gas]}")
    print("72 h regional case reproduces the published fire contributions", flush=True)


if __name__ == "__main__":
    main()
