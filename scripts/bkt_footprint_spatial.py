"""Conservative display smoothing and established Indonesian boundary assets.

Raw footprints are cell-integrated flux sensitivities. Divide by spherical
cell area ONLY for comparable cartographic density; analysis uses original
coefficients. Display smoothing is not an adaptive STILT particle estimator.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter, zoom

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOUNDARY = ROOT.parent / ".assets" / "indonesia_38prov.geojson"


def cell_area_km2(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    """Spherical cell areas for regular geographic center coordinates."""
    dy, dx = float(np.diff(lat)[0]), float(np.diff(lon)[0])
    strips = 6371.0088**2 * np.deg2rad(dx) * (
        np.sin(np.deg2rad(lat + dy / 2)) - np.sin(np.deg2rad(lat - dy / 2)))
    return np.broadcast_to(strips[:, None], (len(lat), len(lon))).copy()


def smooth_coefficients(field: np.ndarray, sigma_cells: float) -> np.ndarray:
    """Positive Gaussian display kernel; preserve total sensitivity exactly."""
    if sigma_cells < 0 or not np.isfinite(field).all() or np.any(field < 0):
        raise ValueError("Expected finite nonnegative coefficients and bandwidth")
    if sigma_cells == 0:
        return field.astype(float).copy()
    result = gaussian_filter(field.astype(float), sigma_cells, mode="constant",
                             cval=0.0, truncate=4.0)
    if field.sum() > 0:
        result *= field.sum() / result.sum()
    return result


def regrid_coefficients(field: np.ndarray, source_lat: np.ndarray,
                        source_lon: np.ndarray, target_lat: np.ndarray,
                        target_lon: np.ndarray) -> np.ndarray:
    """Conservative rectangular overlap, with spherical latitude strip areas.

    Input/output are cell-integrated coefficients; uniform sensitivity density
    within each source cell is the explicit remapping assumption.
    """
    def overlaps(source, target, latitude=False):
        ds, dt = np.diff(source)[0], np.diff(target)[0]
        left = np.maximum(target[:, None]-dt/2, source[None, :]-ds/2)
        right = np.minimum(target[:, None]+dt/2, source[None, :]+ds/2)
        if latitude:
            widths = np.sin(np.deg2rad(right))-np.sin(np.deg2rad(left))
            denominator = np.sin(np.deg2rad(source+ds/2))-np.sin(np.deg2rad(source-ds/2))
        else:
            widths, denominator = right-left, ds
        return np.maximum(widths, 0)/denominator
    return overlaps(source_lat, target_lat, True) @ field @ overlaps(source_lon, target_lon).T


def display_surface(field: np.ndarray, lat: np.ndarray, lon: np.ndarray,
                    sigma_cells: float, factor: int = 4) -> tuple:
    """Interpolate linear coefficients, then apply the log color transform.

    Factor changes display pixels only. Area renormalization after resampling
    conserves the domain integral without using cubic overshoots or log-data
    interpolation. All zero input remains zero.
    """
    smoothed = smooth_coefficients(field, sigma_cells)
    density = smoothed / cell_area_km2(lat, lon)
    high = zoom(density, factor, order=1, mode="nearest", prefilter=False)
    high_lat = np.linspace(lat[0], lat[-1], high.shape[0])
    high_lon = np.linspace(lon[0], lon[-1], high.shape[1])
    area = cell_area_km2(high_lat, high_lon)
    integral = float((high * area).sum())
    if integral > 0:
        high *= field.sum() / integral
    return high_lat, high_lon, high


def sensitivity_support_mask(field,share=.9):
    """Cells containing at least a specified share of integrated sensitivity.

    Includes all ties at the threshold. This is transport support, not a map of
    independently constrained emissions or a posterior spatial resolution.
    """
    field=np.asarray(field,float)
    if not 0<share<=1 or not np.isfinite(field).all() or (field<0).any() or field.sum()<=0:
        raise ValueError("Invalid sensitivity field/share")
    ordered=np.sort(field.ravel())[::-1]
    index=min(np.searchsorted(np.cumsum(ordered),share*ordered.sum()),len(ordered)-1)
    return field>=ordered[index]


def indonesia_boundaries(path: Path | None = None) -> tuple:
    import geopandas as gpd
    from shapely import make_valid
    path = path or Path(os.environ.get("INDONESIA_GEOJSON", DEFAULT_BOUNDARY))
    frame = gpd.read_file(path)
    if frame.crs is None or frame.empty or frame.geometry.is_empty.any():
        raise ValueError("Indonesia boundary CRS or geometries missing")
    original_crs = str(frame.crs)
    frame = frame.to_crs("EPSG:4326")
    invalid = ~frame.geometry.is_valid
    frame.loc[invalid, "geometry"] = frame.loc[invalid, "geometry"].map(make_valid)
    if not frame.geometry.is_valid.all():
        raise ValueError("Indonesia geometry repair failed")
    return frame, {
        "asset": str(path.resolve()),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "source_crs": original_crs, "display_crs": "EPSG:4326",
        "feature_count": len(frame), "invalid_geometries_repaired_in_memory": int(invalid.sum()),
        "repair_method": "shapely.make_valid; original asset unchanged",
        "provenance_limit": "User-established provincial asset; publication vintage not supplied",
    }


def detailed_neighbors(countries=("MYS", "SGP", "THA", "BRN", "VNM", "KHM", "MMR", "PHL")):
    """Load full-resolution, independently sourced context; never replace Indonesia."""
    import geopandas as gpd
    from shapely import make_valid
    import json
    import pyogrio
    geometries, records = [], []
    directory = ROOT / "data/bkt_sources/boundaries"
    for iso in countries:
        path = directory / f"geoBoundaries-{iso}-ADM0.geojson"
        # Full-resolution Australia is one large feature, above GDAL's default
        # GeoJSON object limit. Increase the bounded reader limit, not simplify
        # or replace the supplied scientific boundary geometry.
        old_limit=pyogrio.get_gdal_config_option("OGR_GEOJSON_MAX_OBJ_SIZE")
        try:
            pyogrio.set_gdal_config_options({"OGR_GEOJSON_MAX_OBJ_SIZE":512})
            frame = gpd.read_file(path,engine="pyogrio").to_crs("EPSG:4326")
        finally:pyogrio.set_gdal_config_options({"OGR_GEOJSON_MAX_OBJ_SIZE":old_limit})
        frame.geometry = frame.geometry.map(make_valid)
        if not frame.geometry.is_valid.all(): raise ValueError(f"Invalid boundary: {iso}")
        geometries.extend(frame.geometry)
        records.append(json.loads(path.with_suffix(".geojson.json").read_text()))
    return geometries, records


def basemap(ax, provinces, detailed: bool = False) -> None:
    import cartopy.crs as ccrs
    import cartopy.io.shapereader as shp
    crs = ccrs.PlateCarree()
    ax.set_facecolor("#EAF3F7")
    if detailed:
        neighbors, _ = detailed_neighbors()
    else:
        countries = shp.Reader(shp.natural_earth("110m", "cultural", "admin_0_countries"))
        neighbors = [record.geometry for record in countries.records()
                     if record.attributes.get("ADM0_A3") != "IDN"
                     and record.geometry.bounds[2] > 90 and record.geometry.bounds[0] < 145
                     and record.geometry.bounds[3] > -15 and record.geometry.bounds[1] < 15]
    ax.add_geometries(neighbors, crs, facecolor="#E4E4E1", edgecolor="#777777",
                      linewidth=0.45, zorder=0)
    if detailed:
        ax.add_geometries(neighbors, crs, facecolor="none", edgecolor="#555F63",
                          linewidth=0.45, zorder=4)
    ax.add_geometries(provinces.geometry, crs, facecolor="#F8F7F2", edgecolor="none", zorder=1)


def boundary_lines(ax, provinces) -> None:
    import cartopy.crs as ccrs
    ax.add_geometries(provinces.geometry, ccrs.PlateCarree(), facecolor="none",
                      edgecolor="#555F63", linewidth=0.45, zorder=4)
