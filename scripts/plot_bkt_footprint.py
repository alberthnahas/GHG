#!/usr/bin/env python3
"""Plot BKT footprints with explicit display smoothing and the shared GeoJSON."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
import xarray as xr

from bkt_footprint_spatial import (basemap, boundary_lines, cell_area_km2,
                                   display_surface, indonesia_boundaries)


def map_field(field: np.ndarray, lat: np.ndarray, lon: np.ndarray,
              metadata: dict, output: Path, sigma_cells: float = 0.0,
              ensemble_label: str | None = None,
              limits: tuple[float, float] = (1e-7, 3e-2)) -> dict:
    """Render a continuous density map, keeping original coefficients intact."""
    import cartopy.crs as ccrs
    provinces, boundary_meta = indonesia_boundaries()
    cfg = metadata["configuration"]
    is_gfs = "GFS" in cfg.get("meteorology_label", "")
    met_label = "NOAA GFS meteorology (0.25°)" if is_gfs else "NOAA GDAS1 meteorology (1°)"
    neighbor_label = "geoBoundaries / © OpenStreetMap contributors" if is_gfs else "Natural Earth"
    display_lat, display_lon, density = display_surface(field, lat, lon, sigma_cells)
    vmin, vmax = limits
    fig = plt.figure(figsize=(10, 7.5))
    ax = fig.add_axes([0.075, 0.235, 0.85, 0.63], projection=ccrs.PlateCarree())
    extent = [98.5, 112.0, -8.0, 2.0]
    ax.set_extent(extent)
    basemap(ax, provinces, detailed=is_gfs)
    levels = np.geomspace(vmin, vmax, 100)
    mesh = ax.contourf(display_lon, display_lat, np.ma.masked_less_equal(density, 0), levels=levels,
                       norm=LogNorm(vmin, vmax), cmap="YlOrRd", extend="max",
                       transform=ccrs.PlateCarree(), zorder=2, antialiased=False)
    boundary_lines(ax, provinces)
    ax.plot(cfg["receptor_lon"], cfg["receptor_lat"], marker="*", ms=12,
            color="#007A9D", markeredgecolor="white", markeredgewidth=0.6,
            transform=ccrs.PlateCarree(), zorder=6)
    ax.text(cfg["receptor_lon"]+0.22, cfg["receptor_lat"]+0.35,
            f"BKT · {cfg['receptor_height_m_agl']:g} m AGL",
            ha="left", fontsize=11.5, weight="bold", color="#005D7B",
            transform=ccrs.PlateCarree(), zorder=7)
    ax.text(101.0, -3.8, "SUMATRA", fontsize=11, rotation=-42, color="#59646B",
            transform=ccrs.PlateCarree(), zorder=6)
    ax.text(110.3, -0.7, "KALIMANTAN", fontsize=10, rotation=60, color="#59646B",
            transform=ccrs.PlateCarree(), zorder=6)
    grid = ax.gridlines(draw_labels=True, linewidth=0.4, color="#71818A", alpha=0.4,
                        linestyle="--", x_inline=False, y_inline=False)
    grid.top_labels = grid.right_labels = False
    grid.xlabel_style = grid.ylabel_style = {"size": 12}
    cax = fig.add_axes([0.17, 0.16, 0.66, 0.025])
    cb = fig.colorbar(mesh, cax=cax, orientation="horizontal",
                      ticks=[1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2])
    cb.set_label("Sensitivity density  [ppm / (µmol m⁻² s⁻¹) / km²] · log scale", fontsize=12)
    cb.ax.tick_params(labelsize=11)
    step = float(np.diff(lat)[0])
    fig.text(0.075, 0.96, "Bukit Kototabang: upstream surface-flux footprint",
             fontsize=16, weight="bold", color="#24343D")
    label = ensemble_label or f"{cfg['particles']:,} requested particles"
    fig.text(0.075, 0.932, "23–26 September 2019 · 72 h ending 26 September 01:00 UTC (08:00 WIB)\n"
             f"{label} · {met_label}", fontsize=11, color="#52616A", va="top")
    fig.text(0.075, 0.028,
             f"Raw output: {step:g}°; Gaussian display σ = {sigma_cells*step:.3g}° plus linear interpolation.\n"
             f"Indonesia: provincial GeoJSON; neighbors: {neighbor_label}.\n"
             "WGS 84 · display reconstruction adds no meteorological detail.",
             fontsize=10, color="#52616A")
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=300, facecolor="white")
    fig.savefig(output.with_suffix(".pdf"), facecolor="white")
    plt.close(fig)
    area = cell_area_km2(display_lat, display_lon)
    below = density < vmin
    inside=((display_lat[:,None]>=extent[2]) & (display_lat[:,None]<=extent[3]) &
            (display_lon[None,:]>=extent[0]) & (display_lon[None,:]<=extent[1]))
    return {
        "display_crs": "EPSG:4326", "display_extent_lon_lat": extent,
        "normalization": "logarithmic", "vmin": vmin, "vmax": vmax,
        "variable": "surface-flux sensitivity per square kilometre",
        "units": "ppm / (umol m-2 s-1) / km2",
        "gaussian_sigma_cells": sigma_cells, "gaussian_sigma_degrees": sigma_cells*step,
        "interpolation": "linear coefficients before logarithmic color transform; 4x display sampling",
        "raw_sensitivity_sum": float(field.sum()),
        "display_area_integral": float((density*area).sum()),
        "share_below_display_threshold_percent": float(100*(density*area)[below].sum()/field.sum()),
        "share_outside_map_extent_percent": float(100*(density*area)[~inside].sum()/field.sum()),
        "boundary": boundary_meta, "png_dpi": 300, "png_pixels": [3000, 2250],
    }


def render(run_dir: Path, output: Path | None = None,
           sigma_cells: float = 0.0) -> tuple[Path, Path]:
    metadata = json.loads((run_dir / "run_metadata.json").read_text())
    with xr.open_dataset(run_dir / "footprint.nc", engine="h5netcdf") as ds:
        field = ds.footprint_sensitivity.sum("time").values.astype(float)
        lat, lon = ds.lat.values, ds.lon.values
    log=(run_dir/"MESSAGE").read_text()
    counts=re.findall(r"NOTICE\s+main:\s+\d+\s+\d+\s+(\d+)\s+",log)
    if not counts: raise ValueError("Actual emitted particle count missing")
    actual=max(map(int,counts))
    factor=metadata["configuration"]["particles"]/actual
    field*=factor
    output = output or run_dir / "bkt_hysplit_stilt_footprint.png"
    result = map_field(field, lat, lon, metadata, output, sigma_cells)
    result["particle_normalization_factor"]=factor
    result["actual_emitted_particles"]=actual
    (run_dir / "map_metadata.json").write_text(json.dumps(result, indent=2)+"\n")
    print(f"wrote {output}")
    return output, output.with_suffix(".pdf")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--sigma-cells", type=float, default=0.0)
    args = parser.parse_args()
    render(args.run_dir, args.output, args.sigma_cells)
