#!/usr/bin/env python3
"""GFS versus ERA5 HYSPLIT-STILT footprints at matched receptors.

Compares the ERA5 anchor and forward runs (a76) with their GFS revision
twins (a74): same receptor, seed, particle count, release height, STILT
settings and 120 h window. The ERA5 footprint grid (40 x 60 degrees) is a
subset of the GFS grid (60 x 100), so spatial differences are evaluated on
the ERA5 cells, and the GFS share outside those cells is reported.
Writes outputs/hysplit/era5/tables/driver_comparison.csv and a per-anchor
summary. Differences are driver sensitivities, not accuracy statements.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import a74_bkt_simulation_revision as rev
import a76_bkt_era5_driver as era

ROOT = rev.ROOT
TABLES = era.OUT / "tables"


def load(directory: Path) -> tuple[xr.DataArray, dict]:
    field, meta = rev.read_layers(directory)
    return field.sel(layer=1), meta


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    rows = []
    pairs = [(f"anchor_s{s}", f"ensemble_s{s}", stamp) for s in rev.SEEDS for stamp in rev.ANCHORS]
    pairs += [(f"forward_s{s}", f"forward_s{s}", rev.FORWARD_CASE) for s in rev.SEEDS]
    for era_group, gfs_group, stamp in pairs:
        e_dir = era.RUNS / era_group / f"bkt_{stamp:%Y%m%dT%H%MZ}"
        g_dir = rev.run_dir(gfs_group, stamp)
        if not (e_dir / "completion_receipt.json").exists() or not (g_dir / "completion_receipt.json").exists():
            continue
        e, em = load(e_dir); g, gm = load(g_dir)
        g_sub = g.sel(lat=e.lat, lon=e.lon)
        if not np.allclose(g_sub.lat, e.lat) or not np.allclose(g_sub.lon, e.lon):
            raise ValueError("ERA5 grid is not a subset of the GFS grid")
        ea, ga, gfull = e.sum("time").values, g_sub.sum("time").values, float(g.sum())
        d_e = rev.diagnostics(e.expand_dims(layer=[1]), em["configuration"])
        d_g = rev.diagnostics(g.expand_dims(layer=[1]), gm["configuration"])
        rows.append(dict(receptor_utc=stamp, seed=em["configuration"]["seed"], case="forward" if "forward" in era_group else "anchor",
            particles=em["receipt"]["actual_emitted_particles"],
            era5_sensitivity=float(ea.sum()), gfs_sensitivity=gfull, gfs_outside_era5_grid_percent=100 * (1 - ga.sum() / gfull),
            ratio_era5_over_gfs=float(ea.sum() / gfull),
            spatial_abs_difference_percent=100 * float(np.abs(ea - ga).sum() / ga.sum()),
            era5_within25=d_e["within25_percent"], gfs_within25=d_g["within25_percent"],
            era5_within500=d_e["within500_percent"], gfs_within500=d_g["within500_percent"],
            era5_oldest24h=d_e["oldest24h_percent"], gfs_oldest24h=d_g["oldest24h_percent"],
            era5_runtime_min=em["receipt"]["model_runtime_seconds"] / 60, gfs_runtime_min=(gm["receipt"].get("model_runtime_seconds") or np.nan) / 60))
    table = pd.DataFrame(rows).sort_values(["case", "receptor_utc", "seed"])
    table.to_csv(TABLES / "driver_comparison.csv", index=False)
    summary = table.groupby(["case", "receptor_utc"]).agg(
        ratio_mean=("ratio_era5_over_gfs", "mean"), ratio_min=("ratio_era5_over_gfs", "min"), ratio_max=("ratio_era5_over_gfs", "max"),
        spatial_diff_mean=("spatial_abs_difference_percent", "mean"),
        era5_within500=("era5_within500", "mean"), gfs_within500=("gfs_within500", "mean"),
        era5_oldest24h=("era5_oldest24h", "mean"), gfs_oldest24h=("gfs_oldest24h", "mean"),
        gfs_outside_grid=("gfs_outside_era5_grid_percent", "mean"),
        era5_seed_cv=("era5_sensitivity", lambda v: 100 * v.std(ddof=1) / v.mean()),
        gfs_seed_cv=("gfs_sensitivity", lambda v: 100 * v.std(ddof=1) / v.mean())).reset_index()
    summary.to_csv(TABLES / "driver_comparison_summary.csv", index=False)
    print(summary.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
