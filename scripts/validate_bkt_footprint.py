#!/usr/bin/env python3
"""Validate scientific and file-integrity invariants for a BKT footprint run."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "ghg-matplotlib"))

import numpy as np
import pandas as pd
from PIL import Image
import xarray as xr


ROOT = Path(__file__).resolve().parent.parent
REQUIRED = (
    "CONTROL", "SETUP.CFG", "MESSAGE", "cdump", "footprint_hourly.csv.gz",
    "footprint_aggregate.csv", "footprint.nc", "run_metadata.json",
    "bkt_hysplit_stilt_footprint.png", "bkt_hysplit_stilt_footprint.pdf",
    "map_metadata.json",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(run_dir: Path, skip_checksum: bool = False) -> dict[str, object]:
    failures: list[str] = []
    for name in REQUIRED:
        path = run_dir / name
        if not path.is_file() or path.stat().st_size == 0:
            failures.append(f"missing or empty {name}")

    metadata = json.loads((run_dir / "run_metadata.json").read_text(encoding="utf-8"))
    config = metadata["configuration"]
    receptor = pd.Timestamp(metadata["observation"]["time_utc"]).tz_localize(None)
    hours_back = int(config["hours_back"])
    interval = int(config["output_interval_hours"])
    expected_times = pd.date_range(
        receptor - pd.Timedelta(hours=hours_back),
        receptor - pd.Timedelta(hours=interval),
        freq=f"{interval}h",
    )

    hourly = pd.read_csv(run_dir / "footprint_hourly.csv.gz", parse_dates=["time_utc"])
    aggregate = pd.read_csv(run_dir / "footprint_aggregate.csv")
    values = hourly["footprint_sensitivity"].to_numpy()
    if hourly.empty or not np.isfinite(values).all() or (values < 0).any() or values.sum() <= 0:
        failures.append("hourly footprint must be nonempty, finite, non-negative and positive in sum")
    observed_times = pd.DatetimeIndex(sorted(hourly.time_utc.unique()))
    if not observed_times.equals(expected_times):
        failures.append("hourly footprint does not cover every expected backward interval")
    expected_lags = np.arange(interval, hours_back + 1, interval, dtype=float)
    if not np.array_equal(np.sort(hourly.lag_hours.unique()), expected_lags):
        failures.append("lag-hour coverage is incomplete")

    with xr.open_dataset(run_dir / "footprint.nc", engine="h5netcdf") as dataset:
        expected_sizes = {"time": len(expected_times),
                          "lat": round(config["grid_span_lat_deg"] / config["grid_spacing_deg"]) + 1,
                          "lon": round(config["grid_span_lon_deg"] / config["grid_spacing_deg"]) + 1}
        if dict(dataset.sizes) != expected_sizes:
            failures.append(f"unexpected NetCDF dimensions: {dict(dataset.sizes)}")
        if dataset.footprint_sensitivity.attrs.get("units") != "ppm / (umol m-2 s-1)":
            failures.append("NetCDF footprint units are missing or incorrect")
        netcdf_total = float(dataset.footprint_sensitivity.sum())
        domain = {
            "lat_min": float(dataset.lat.min()), "lat_max": float(dataset.lat.max()),
            "lon_min": float(dataset.lon.min()), "lon_max": float(dataset.lon.max()),
        }
    hourly_total = float(values.sum())
    aggregate_total = float(aggregate.sensitivity_sum.sum())
    if not (np.isclose(hourly_total, aggregate_total, rtol=2e-12)
            and np.isclose(hourly_total, netcdf_total, rtol=2e-6)):
        failures.append("hourly, aggregate and NetCDF sensitivity totals do not reconcile")
    edge = (
        hourly.LAT.eq(domain["lat_min"]) | hourly.LAT.eq(domain["lat_max"])
        | hourly.LON.eq(domain["lon_min"]) | hourly.LON.eq(domain["lon_max"])
    )
    if edge.any():
        failures.append("positive footprint reaches an output-domain edge")

    setup = (run_dir / "SETUP.CFG").read_text(encoding="ascii")
    message = (run_dir / "MESSAGE").read_text(encoding="utf-8", errors="replace")
    for marker in ("ICHEM = 8", "IDSP = 2", "KBLT = 5", "KMIXD = 3"):
        if marker not in setup:
            failures.append(f"missing STILT setting {marker}")
    for marker in ("Mixed layer depth -  T", "Convective mixing -  T",
                   "STILT emulation mixed layer fraction for concentration grid"):
        if marker not in message:
            failures.append(f"HYSPLIT did not confirm {marker}")
    if "FATAL" in message.upper():
        failures.append("HYSPLIT MESSAGE contains FATAL")

    met_checks: list[dict[str, object]] = []
    for met_name in metadata["meteorology_files"]:
        met_path = Path(met_name)
        provenance_path = ROOT / "data" / "hysplit" / "provenance" / f"{met_path.name}.json"
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        item = {
            "filename": met_path.name,
            "bytes_match": met_path.stat().st_size == int(provenance["bytes"]),
            "sha256_match": None if skip_checksum else sha256_file(met_path) == provenance["sha256"],
        }
        if not item["bytes_match"] or item["sha256_match"] is False:
            failures.append(f"meteorology integrity check failed for {met_path.name}")
        met_checks.append(item)

    with Image.open(run_dir / "bkt_hysplit_stilt_footprint.png") as image:
        png_pixels = list(image.size)
    if png_pixels != [3000, 2250]:
        failures.append(f"unexpected PNG dimensions: {png_pixels}")
    map_metadata = json.loads((run_dir / "map_metadata.json").read_text(encoding="utf-8"))
    if map_metadata.get("normalization") != "logarithmic":
        failures.append("map normalization was not recorded as logarithmic")

    result = {
        "status": "passed" if not failures else "failed",
        "failures": failures,
        "receptor_time_utc": metadata["observation"]["time_utc"],
        "hourly_periods": len(observed_times),
        "time_min_utc": observed_times.min().isoformat(),
        "time_max_utc": observed_times.max().isoformat(),
        "nonzero_cell_hours": int(len(hourly)),
        "nonzero_grid_cells": int(len(aggregate)),
        "footprint_sensitivity_sum": hourly_total,
        "footprint_units": "ppm / (umol m-2 s-1)",
        "domain": domain,
        "positive_extent": {
            "lat_min": float(hourly.LAT.min()), "lat_max": float(hourly.LAT.max()),
            "lon_min": float(hourly.LON.min()), "lon_max": float(hourly.LON.max()),
        },
        "meteorology_integrity": met_checks,
        "png_pixels": png_pixels,
    }
    (run_dir / "validation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if failures:
        raise RuntimeError("; ".join(failures))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--skip-checksum", action="store_true")
    args = parser.parse_args()
    result = validate(args.run_dir, args.skip_checksum)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
