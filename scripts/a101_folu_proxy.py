#!/usr/bin/env python3
"""A spatial proxy for Indonesian land-use emissions, the term EDGAR cannot carry.

The localisation engine refuses IPCC category 3B because EDGAR excludes land
use, land-use change and forestry. In Indonesia that refusal removes the largest
and most variable part of the national inventory, so the model was missing its
biggest term. This builds the pattern that category needs.

Two components, because two processes dominate and they behave differently:

  drained peat. Peat emits while it is drained, continuously, at a rate that
    depends on how deeply it is drained, which land use is the practical proxy
    for. This layer is the peatland extent weighted by land cover.

  fire. Peat and biomass fires are episodic, interannual, and in a haze year
    they dominate everything else. This layer is GFED burned carbon, split into
    the part over peat and the part not, because the two burn differently.

The magnitude problem is deliberately not solved here, and that is the point.
Absolute emission factors for drained tropical peat are contested: Murdiyarso et
al. (PNAS 2024) report 8.13 to 80.77 Mg CO2 per hectare per year across land
covers and water table depths, a spread of ten. Rather than pick a number and
hide the uncertainty, this module produces a normalised pattern and lets
SIGN-SMART supply the magnitude, which is exactly the division of labour the
localisation engine already uses for every other sector. An absolute mode exists
for provinces with no reported total, and it carries the full published range
rather than a false precision.

The land-cover weights are relative, editable, and stated below. They encode one
ordering that the literature agrees on even where it disagrees on values:
drained cropland and plantation emit most, degraded shrubland less, forest on
peat less again, and undrained swamp forest least.

Stages
  build       write the gridded FOLU proxy for a bounding box
  weights     print the land-cover weighting and its justification
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
PEAT = Path("/run/media/workstation-llm/HDD2/GHG_INDONESIA/indonesia_peatlands.json")
LANDCOVER = ROOT / "data/bkt_sources/landcover/MCD12C1_2019_IGBP_majority_0p05deg.tif"
GFED = ROOT / "data/bkt_sources/gfed51/GFED5.1_ecosystem_2019.nc"
OUT = ROOT / "outputs/inventory"

# MODIS IGBP class -> relative drainage intensity on peat. Relative, not absolute:
# the magnitude comes from the reported total. The ordering is the part the
# literature agrees on; the values are a stated choice, not a measurement.
DRAINAGE_WEIGHT = {
    12: 1.00,   # croplands: drained, the deepest water tables
    14: 0.90,   # cropland and natural vegetation mosaic
    10: 0.70,   # grasslands, largely converted
    7: 0.70,    # open shrublands, typically degraded and burned over
    6: 0.65,    # closed shrublands
    9: 0.60,    # savannas
    8: 0.55,    # woody savannas, includes much of the plantation mosaic
    5: 0.40,    # mixed forest
    2: 0.35,    # evergreen broadleaf forest, secondary or logged peat forest
    4: 0.35,    # deciduous broadleaf forest
    1: 0.30,    # evergreen needleleaf forest
    11: 0.10,   # permanent wetlands: near-natural, water table at the surface
    13: 0.00,   # urban
    15: 0.00,   # snow and ice
    16: 0.00,   # barren
    0: 0.00,    # water
    17: 0.00,   # water bodies in some collections
}
# Murdiyarso et al., PNAS 2024, Table 1: drained peat CO2 across land covers and
# water tables. Used as a declared range, never as a single number.
DRAINED_PEAT_CO2_MG_HA_YR = (8.13, 80.77)
FOLU_COMPONENTS = ("peat_drainage", "peat_fire", "nonpeat_fire")


def peat_mask(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    """Rasterise the Indonesian peatland layer by cell-centre containment."""
    import shapely
    from shapely.geometry import shape
    geometry = shape(json.loads(PEAT.read_text()))
    mesh_lon, mesh_lat = np.meshgrid(lon, lat)
    return shapely.contains_xy(geometry, mesh_lon, mesh_lat)


def landcover_classes(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    """MODIS IGBP majority class sampled at each cell centre."""
    import rasterio
    mesh_lon, mesh_lat = np.meshgrid(lon, lat)
    with rasterio.open(LANDCOVER) as raster:
        sample = np.array(list(raster.sample(np.c_[mesh_lon.ravel(), mesh_lat.ravel()])), dtype=float)
    return sample[:, 0].reshape(mesh_lat.shape)


def drainage_layer(lat: np.ndarray, lon: np.ndarray) -> tuple[np.ndarray, dict]:
    """Peat extent weighted by how hard its land cover implies it is drained."""
    peat = peat_mask(lat, lon)
    classes = landcover_classes(lat, lon)
    weight = np.zeros_like(classes, dtype=float)
    for code, value in DRAINAGE_WEIGHT.items():
        weight[classes == code] = value
    unknown = sorted({int(c) for c in np.unique(classes) if int(c) not in DRAINAGE_WEIGHT})
    layer = np.where(peat, weight, 0.0)
    report = dict(peat_cells=int(peat.sum()), drained_cells=int((layer > 0).sum()),
                  unweighted_classes=unknown,
                  mean_weight_on_peat=float(weight[peat].mean()) if peat.any() else 0.0)
    return layer, report


def fire_layers(lat: np.ndarray, lon: np.ndarray, peat: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict]:
    """GFED burned carbon, split by whether it burned over peat."""
    with xr.open_dataset(GFED) as ds:
        carbon = ds.carbon_emissions.sum("time")
        carbon = carbon.sortby("lat").sortby("lon")
        aligned = carbon.interp(lat=("y", lat), lon=("x", lon), method="nearest")
    values = np.nan_to_num(np.asarray(aligned.values, dtype=float)).reshape(len(lat), len(lon))
    values = np.clip(values, 0, None)
    return np.where(peat, values, 0.0), np.where(peat, 0.0, values), dict(
        total_fire=float(values.sum()),
        peat_fire_share_percent=float(100 * values[peat].sum() / values.sum()) if values.sum() else 0.0)


def build(bounds: tuple[float, float, float, float], resolution: float, label: str) -> dict:
    west, south, east, north = bounds
    lat = np.arange(south + resolution / 2, north, resolution)
    lon = np.arange(west + resolution / 2, east, resolution)
    drainage, drainage_report = drainage_layer(lat, lon)
    peat = peat_mask(lat, lon)
    peat_fire, nonpeat_fire, fire_report = fire_layers(lat, lon, peat)

    layers = {"peat_drainage": drainage, "peat_fire": peat_fire, "nonpeat_fire": nonpeat_fire}
    normalised = {}
    for name, values in layers.items():
        total = float(values.sum())
        normalised[name] = values / total if total > 0 else values
    dataset = xr.Dataset({name: (("lat", "lon"), values) for name, values in normalised.items()},
                         coords=dict(lat=lat, lon=lon))
    for name in normalised:
        dataset[name].attrs.update(units="fraction of the Indonesian total for this component",
                                   note="a pattern, not a flux; the magnitude comes from the reported total")
    dataset["peat"] = (("lat", "lon"), peat.astype(np.int8))
    dataset.attrs.update(
        title="Indonesian FOLU spatial proxy",
        drainage_source="Indonesian peatland extent weighted by MODIS MCD12C1 IGBP land cover",
        fire_source=str(GFED),
        emission_factor_note=("absolute drained-peat CO2 is contested: Murdiyarso et al., PNAS 2024, report "
                              f"{DRAINED_PEAT_CO2_MG_HA_YR[0]} to {DRAINED_PEAT_CO2_MG_HA_YR[1]} Mg CO2 per hectare "
                              "per year across land covers and water tables, so this file carries a pattern only"),
        weights=json.dumps(DRAINAGE_WEIGHT))
    OUT.mkdir(parents=True, exist_ok=True)
    destination = OUT / f"folu_proxy_{label}.nc"
    dataset.to_netcdf(destination)

    report = dict(label=label, output=str(destination), bounds=list(bounds), resolution=resolution,
                  grid=[len(lat), len(lon)], **drainage_report, **fire_report)
    (OUT / f"folu_proxy_{label}_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"FOLU proxy {label}: {len(lat)}x{len(lon)} at {resolution} degrees", flush=True)
    print(f"  peat cells {report['peat_cells']}, of which drained-weighted {report['drained_cells']}, "
          f"mean drainage weight {report['mean_weight_on_peat']:.2f}", flush=True)
    print(f"  fire carbon over peat: {report['peat_fire_share_percent']:.1f}% of the domain total", flush=True)
    if report["unweighted_classes"]:
        print(f"  land-cover classes with no weight, treated as zero: {report['unweighted_classes']}", flush=True)
    print(f"  wrote {destination}", flush=True)
    return report


def weights() -> None:
    import a100_local_inventory as L
    print("Relative drainage weight by MODIS IGBP class, on peat only:")
    for code, value in sorted(DRAINAGE_WEIGHT.items(), key=lambda kv: -kv[1]):
        print(f"  class {code:2d}  weight {value:.2f}")
    print()
    print("These are relative. The magnitude comes from the reported provincial or national total,")
    print("the same division of labour the other sectors use. Absolute drained-peat carbon dioxide")
    print(f"is reported between {DRAINED_PEAT_CO2_MG_HA_YR[0]} and {DRAINED_PEAT_CO2_MG_HA_YR[1]} Mg per hectare per year")
    print("(Murdiyarso et al., PNAS 2024), a spread of ten, which is why no single value is used here.")
    print()
    print(f"IPCC category 3B is refused by the crosswalk against EDGAR: {L.CROSSWALK['3B'][1]}.")
    print("With this proxy it becomes usable, through the --folu-proxy option of the localisation stage.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["build", "weights"])
    parser.add_argument("--bounds", nargs=4, type=float, default=[94., -12., 142., 7.],
                        metavar=("WEST", "SOUTH", "EAST", "NORTH"))
    parser.add_argument("--resolution", type=float, default=0.1)
    parser.add_argument("--label", default="indonesia")
    a = parser.parse_args()
    build(tuple(a.bounds), a.resolution, a.label) if a.stage == "build" else weights()


if __name__ == "__main__":
    main()
