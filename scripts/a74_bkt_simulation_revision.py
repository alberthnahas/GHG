#!/usr/bin/env python3
"""Revised BKT HYSPLIT-STILT simulation campaign (11 September 2026).

Fixes the simulation-side weaknesses identified in
``docs/BKT_FOOTPRINT_REVIEW_2026-09-11.md`` without touching any earlier run:

* ``ensemble``  - the 52 twice-daily inversion receptors rerun on the widened
  50-160E / 40S-30N meteorology and 60 x 100 degree footprint grid, 120 h
  backward, 2,000 requested particles, three seeds each (numerical noise).
* ``terrain``   - the four benchmark anchors released at 80 m above model
  ground, three seeds each. 80 m places the inlet at its true altitude above
  the nearest GFS grid-cell terrain (864.5 + 30 - 816 m); the existing 30 m
  and 60 m runs bracket the bilinear-terrain equivalent.
* ``afternoon`` - 05, 07 and 08 UTC (12:00, 14:00, 15:00 WIB) on every day of
  the study period, so that a 12:00-15:00 WIB well-mixed window mean can be
  formed together with the 06 UTC ensemble members.
* ``forward``   - the 26 September 2019 01:00 UTC case rerun for 120 h on the
  widened domain with 10,000 requested particles, three seeds, plus one 80 m
  member.

Every run also records a fixed 1,000 m concentration layer above the STILT
surface layer (``footprint_layers.nc``) for later injection-height tests.
Layer 1 is bit-identical to ``footprint.nc``.  Convective redistribution is
not fixed here: the GFS archive carries no convective fluxes and HYSPLIT
reports ``Convective mixing - F`` for every configuration tried.

Outputs live under ``outputs/hysplit/revision``.  No gas value selects a run.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, replace
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import time

import numpy as np
import pandas as pd
import xarray as xr

import a37_bkt_footprint as model
import a41_bkt_gfs as gfs
import ghg_common as G
from a39_bkt_refinement import actual_particles

ROOT = model.ROOT
OUT = ROOT / "outputs/hysplit/revision"
RUNS = OUT / "runs"
TABLES = OUT / "tables"
MEAN = OUT / "ensemble_mean"
WIDE_MET = ROOT / "data/hysplit/gfs0p25/benchmark_wide"
HYSPLIT_HOME = ROOT.parent / "AQ/tools/hysplit.v5.4.2_UbuntuOS20.04.6LTS"
RECEPTOR_SELECTION = ROOT / "outputs/hysplit/inversion/receptor_selection.csv"
STUDY_DAYS = pd.date_range("2019-09-09", "2019-10-06", freq="D")
ANCHORS = tuple(pd.to_datetime(["2019-09-09T06:00", "2019-09-09T18:00",
                                "2019-09-23T06:00", "2019-09-23T18:00"]))
FORWARD_CASE = pd.Timestamp("2019-09-26T01:00")
SEEDS = (0, -10, -20)
AFTERNOON_HOURS_UTC = (5, 7, 8)
EXTRA_LEVELS_M = (1000,)
HOURS_BACK = 120
NEAREST_GFS_TERRAIN_M = 816.0
TERRAIN_MATCHED_HEIGHT_M = 80.0  # round(864.5 + 30 - 816) to the nearest 10 m


def base_config(particles: int = 2000, height: float = 30.0, seed: int = 0) -> model.FootprintConfig:
    return model.FootprintConfig(meteorology_label=gfs.LABEL, particles=particles,
        receptor_height_m_agl=height, hours_back=HOURS_BACK, seed=seed,
        grid_spacing_deg=.25, grid_span_lat_deg=60, grid_span_lon_deg=100,
        particle_diagnostic_variables=0, save_endpoints=True)


def met_paths(stamp: pd.Timestamp) -> list[Path]:
    days = pd.date_range((stamp - pd.Timedelta(hours=HOURS_BACK)).normalize(), stamp.normalize(), freq="D")
    return [WIDE_MET / f"{day:%Y%m%d}_gfs0p25" for day in days]


def retained_receptors() -> list[pd.Timestamp]:
    frame = pd.read_csv(RECEPTOR_SELECTION, parse_dates=["time_utc"])
    stamps = sorted(frame.loc[frame.retained, "time_utc"])
    if len(stamps) != 52:
        raise ValueError("Frozen inversion selection must contain 52 retained receptors")
    return stamps


def jobs(group: str) -> list[tuple[str, pd.Timestamp, model.FootprintConfig]]:
    """Predeclared job list; the order puts the longest runs first."""
    items: list[tuple[str, pd.Timestamp, model.FootprintConfig]] = []
    if group in ("forward", "all"):
        for seed in SEEDS:
            items.append((f"forward_s{seed}", FORWARD_CASE, base_config(10000, 30.0, seed)))
        items.append(("forward_h80_s0", FORWARD_CASE, base_config(10000, TERRAIN_MATCHED_HEIGHT_M, 0)))
    if group in ("ensemble", "all"):
        for seed in SEEDS:
            for stamp in retained_receptors():
                items.append((f"ensemble_s{seed}", stamp, base_config(2000, 30.0, seed)))
    if group in ("terrain", "all"):
        for seed in SEEDS:
            for stamp in ANCHORS:
                items.append((f"terrain_h80_s{seed}", stamp, base_config(2000, TERRAIN_MATCHED_HEIGHT_M, seed)))
    if group in ("afternoon", "all"):
        for day in STUDY_DAYS:
            for hour in AFTERNOON_HOURS_UTC:
                items.append(("afternoon_s0", day + pd.Timedelta(hours=hour), base_config(2000, 30.0, 0)))
    if not items:
        raise ValueError(f"Unknown group: {group}")
    return items


def run_dir(name: str, stamp: pd.Timestamp) -> Path:
    return RUNS / name / f"bkt_{stamp:%Y%m%dT%H%MZ}"


def observation_context(observations: pd.DataFrame, stamp: pd.Timestamp) -> dict[str, object]:
    context: dict[str, object] = {"station": "BKT", "station_name": "Bukit Kototabang",
        "time_utc": stamp.isoformat() + "Z",
        "purpose": "Predeclared simulation revision; gas values do not select runs"}
    if stamp in observations.index:
        row = observations.loc[stamp]
        context.update({k: (None if pd.isna(row[k]) else float(row[k])) for k in ("co2", "ch4", "co")})
        context.update({k: bool(row[k]) for k in ("suspect_co2", "suspect_ch4", "suspect_co")})
    else:
        context.update({"co2": None, "ch4": None, "co": None})
    return context


def receipt(directory: Path, name: str, stamp: pd.Timestamp, cfg: model.FootprintConfig,
            runtime: float | None) -> dict:
    required = ("footprint.nc", "footprint_layers.nc", "PAR_GIS.txt", "MESSAGE", "CONTROL", "SETUP.CFG",
                "run_metadata.json")
    missing = [p for p in required if not (directory / p).is_file()]
    if missing:
        raise FileNotFoundError(f"Incomplete run {directory}: {missing}")
    meta = json.loads((directory / "run_metadata.json").read_text())
    if meta["configuration"] != asdict(cfg):
        raise ValueError(f"Configuration mismatch: {directory}")
    if meta.get("extra_levels_m") != list(EXTRA_LEVELS_M):
        raise ValueError(f"Layer request mismatch: {directory}")
    paths = met_paths(stamp)
    if meta["meteorology_files"] != [str(p.resolve()) for p in paths]:
        raise ValueError(f"Meteorology mismatch: {directory}")
    if (directory / "CONTROL").read_text() != model.control_text(stamp, paths, directory, cfg, EXTRA_LEVELS_M):
        raise ValueError(f"CONTROL does not encode the declared run: {directory}")
    if (directory / "SETUP.CFG").read_text() != model.setup_text(cfg, model.TransportOptions()):
        raise ValueError(f"SETUP.CFG does not encode the declared run: {directory}")
    message = (directory / "MESSAGE").read_text(errors="replace")
    if "Convective mixing -  T" in message:
        raise ValueError("Unexpected convective mixing flag; the archive carries no convective fluxes")
    actual = actual_particles(message)
    if actual < cfg.particles:
        raise ValueError(f"Fewer particles emitted than requested: {directory}")
    return dict(group=name, receptor_utc=stamp.isoformat() + "Z", configuration=asdict(cfg),
        transport_options=asdict(model.TransportOptions()), extra_levels_m=list(EXTRA_LEVELS_M),
        meteorology_files=meta["meteorology_files"], actual_emitted_particles=actual,
        model_runtime_seconds=runtime if runtime is not None else meta.get("model_runtime_seconds"),
        hysplit_version_line=meta.get("hysplit_version_line"),
        output_sha256={p: model.sha256_file(directory / p) for p in required[:4]},
        created_at_utc=datetime.now(timezone.utc).isoformat())


def ensure_run(name: str, stamp: pd.Timestamp, cfg: model.FootprintConfig,
               context: dict[str, object]) -> tuple[Path, float]:
    directory = run_dir(name, stamp)
    if (directory / "completion_receipt.json").exists():
        stored = json.loads((directory / "completion_receipt.json").read_text())
        if stored["configuration"] != asdict(cfg):
            raise ValueError(f"Existing receipt has different settings: {directory}")
        return directory, 0.0
    if directory.exists():
        # An interrupted run of this campaign has no scientific value; rebuild it.
        if (directory / "run_metadata.json").exists() and (directory / "PARDUMP").is_file() \
                and (directory / "footprint_layers.nc").is_file():
            if not (directory / "PAR_GIS.txt").is_file():
                model.run_checked([str(HYSPLIT_HOME / "exec/par2asc"), "-iPARDUMP", "-oendpoints.txt",
                                   "-vendpoint_times.txt", "-a1"], directory, "endpoints")
            record = receipt(directory, name, stamp, cfg, None)
            (directory / "completion_receipt.json").write_text(json.dumps(record, indent=2) + "\n")
            return directory, 0.0
        shutil.rmtree(directory)
    started = time.monotonic()
    model.run_footprint(stamp, WIDE_MET, directory.parent, HYSPLIT_HOME, cfg, False,
        meteorology_paths=met_paths(stamp), transport=model.TransportOptions(),
        observation_context=context, extra_levels_m=EXTRA_LEVELS_M)
    model.run_checked([str(HYSPLIT_HOME / "exec/par2asc"), "-iPARDUMP", "-oendpoints.txt",
                       "-vendpoint_times.txt", "-a1"], directory, "endpoints")
    (directory / "PARDUMP").unlink()  # PAR_GIS.txt retains the endpoints; the binary dump is large
    elapsed = time.monotonic() - started
    record = receipt(directory, name, stamp, cfg, elapsed)
    (directory / "completion_receipt.json").write_text(json.dumps(record, indent=2) + "\n")
    return directory, elapsed


def run(group: str, workers: int, attempts: int = 2) -> None:
    import traceback
    if not (HYSPLIT_HOME / "exec/hycs_std").exists():
        raise FileNotFoundError(f"HYSPLIT not found at {HYSPLIT_HOME}")
    observations = G.apply_flags(G.load_station("BKT")).set_index("time_utc")
    items = jobs(group)
    # Contexts are built on the main thread: concurrent first-time pandas index
    # lookups from a dozen workers are not safe.
    contexts = {s: observation_context(observations, s) for _, s, _ in items}
    started = time.monotonic()
    failures: dict[tuple[str, pd.Timestamp], str] = {}
    for attempt in range(1, attempts + 1):
        pending = [(n, s, c) for n, s, c in items if not (run_dir(n, s) / "completion_receipt.json").exists()]
        print(f"attempt {attempt}: {len(items)} runs declared, {len(pending)} pending, {workers} workers", flush=True)
        if not pending:
            break
        failures = {}
        done = 0
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(ensure_run, n, s, c, contexts[s]): (n, s) for n, s, c in pending}
            for future in as_completed(futures):
                name, stamp = futures[future]
                done += 1
                try:
                    _, elapsed = future.result()
                except Exception:  # noqa: BLE001 - logged and retried, never silent
                    failures[(name, stamp)] = traceback.format_exc()
                    print(f"[{done}/{len(pending)}] FAILED {name} {stamp:%Y-%m-%dT%HZ}\n{failures[(name, stamp)]}", flush=True)
                    continue
                print(f"[{done}/{len(pending)}] {name} {stamp:%Y-%m-%dT%HZ} {elapsed/60:.1f} min "
                      f"(campaign {(time.monotonic()-started)/3600:.2f} h)", flush=True)
    if failures:
        raise RuntimeError(f"{len(failures)} runs failed after {attempts} attempts: "
                           + ", ".join(f"{n} {s:%Y-%m-%dT%HZ}" for n, s in failures))
    print("campaign complete", flush=True)


# ---------------------------------------------------------------- summaries

def haversine_km(lat: np.ndarray, lon: np.ndarray, lat0: float, lon0: float) -> np.ndarray:
    p1, p2 = np.radians(lat), np.radians(lat0)
    dl = np.radians(lon - lon0)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * 6371.0088 * np.arcsin(np.sqrt(a))


def read_layers(directory: Path) -> tuple[xr.DataArray, dict]:
    """Layered field normalized to the actual emitted particle count."""
    meta = json.loads((directory / "run_metadata.json").read_text())
    rec = json.loads((directory / "completion_receipt.json").read_text())
    with xr.open_dataset(directory / "footprint_layers.nc", engine="h5netcdf") as ds:
        layers = ds.layer_sensitivity.astype("float64").load()
    with xr.open_dataset(directory / "footprint.nc", engine="h5netcdf") as ds:
        surface = ds.footprint_sensitivity.astype("float64").load()
    if not np.array_equal(layers.sel(layer=1).values, surface.values):
        raise ValueError(f"Layer 1 differs from footprint.nc: {directory}")
    if int(layers.sizes["time"]) != HOURS_BACK or not np.isfinite(layers).all() or float(layers.min()) < 0:
        raise ValueError(f"Invalid layered footprint: {directory}")
    factor = meta["configuration"]["particles"] / rec["actual_emitted_particles"]
    layers = layers * factor
    layers.attrs.update(particle_normalization_factor=factor,
                        normalization="native coefficient times requested/actual emitted count")
    meta["receipt"] = rec
    return layers, meta


def endpoint_retention(directory: Path, actual: int) -> tuple[float, int]:
    points = pd.read_csv(directory / "PAR_GIS.txt", skipinitialspace=True)
    points.columns = points.columns.str.strip()
    if len(points) != actual:
        raise ValueError(f"Endpoint record count differs from emitted count: {directory}")
    active = int(points.PGRD.gt(0).sum())
    return active / actual, active


def diagnostics(field: xr.DataArray, cfg: dict) -> dict:
    surface = field.sel(layer=1)
    aggregate = surface.sum("time").values
    total = float(aggregate.sum())
    lat, lon = np.meshgrid(field.lat.values, field.lon.values, indexing="ij")
    distance = haversine_km(lat, lon, cfg["receptor_lat"], cfg["receptor_lon"])
    hourly = surface.sum(("lat", "lon")).values  # chronological, oldest first
    edge = np.zeros(aggregate.shape, bool); edge[[0, -1], :] = True; edge[:, [0, -1]] = True
    out = dict(sensitivity=total,
        layer2_sensitivity=float(field.sel(layer=2).sum()) if 2 in field.layer.values else np.nan,
        within25_percent=100 * aggregate[distance < 25].sum() / total,
        within50_percent=100 * aggregate[distance < 50].sum() / total,
        within500_percent=100 * aggregate[distance < 500].sum() / total,
        oldest24h_percent=100 * hourly[:24].sum() / total,
        edge_percent=100 * aggregate[edge].sum() / total,
        receptor_cell_percent=100 * aggregate[np.unravel_index(distance.argmin(), distance.shape)] / total)
    return out


def summarize() -> None:
    TABLES.mkdir(parents=True, exist_ok=True); MEAN.mkdir(parents=True, exist_ok=True)
    rows = []
    fields: dict[tuple[str, pd.Timestamp], xr.DataArray] = {}
    for directory in sorted(RUNS.glob("*/bkt_*")):
        if not (directory / "completion_receipt.json").exists():
            continue
        field, meta = read_layers(directory)
        cfg = meta["configuration"]; rec = meta["receipt"]
        stamp = pd.Timestamp(meta["observation"]["time_utc"]).tz_localize(None)
        retention, active = endpoint_retention(directory, rec["actual_emitted_particles"])
        rows.append(dict(group=directory.parent.name, receptor_utc=stamp, seed=cfg["seed"],
            requested_particles=cfg["particles"], actual_particles=rec["actual_emitted_particles"],
            height_m_agl=cfg["receptor_height_m_agl"], hours_back=cfg["hours_back"],
            runtime_minutes=(rec.get("model_runtime_seconds") or np.nan) / 60,
            endpoint_retention=retention, active_endpoints=active,
            **diagnostics(field, cfg)))
        fields[(directory.parent.name, stamp)] = field
    if not rows:
        raise ValueError("No completed revision runs to summarize")
    ledger = pd.DataFrame(rows).sort_values(["group", "receptor_utc"])
    ledger.to_csv(TABLES / "run_ledger.csv", index=False)

    # Seed ensembles: per-receptor mean field and cross-seed spread.
    spread_rows = []
    for family in ("ensemble", "terrain_h80", "forward"):
        keys = sorted({s for g, s in fields if g.startswith(f"{family}_s")})
        for stamp in keys:
            members = [fields[(g, s)] for g, s in fields if g.startswith(f"{family}_s") and s == stamp]
            if len(members) < 2:
                continue
            if any(np.array_equal(members[0].values, m.values) for m in members[1:]):
                raise ValueError(f"Seed members are identical for {family} {stamp}")
            mean = xr.concat(members, dim="member").mean("member")
            mean.attrs.update(members[0].attrs, ensemble_members=len(members),
                comment="Arithmetic mean of seeded runs, each normalized to its actual emitted count")
            mean.to_dataset(name="layer_sensitivity").to_netcdf(
                MEAN / f"{family}_bkt_{stamp:%Y%m%dT%H%MZ}.nc", engine="h5netcdf",
                encoding={"layer_sensitivity": {"zlib": True, "complevel": 4}})
            totals = np.array([float(m.sel(layer=1).sum()) for m in members])
            near = np.array([100 * float(m.sel(layer=1).sum("time").where(
                haversine_km(*np.meshgrid(m.lat.values, m.lon.values, indexing="ij"), -.202, 100.318) < 50).sum())
                / float(m.sel(layer=1).sum()) for m in members])
            spread_rows.append(dict(family=family, receptor_utc=stamp, members=len(members),
                sensitivity_mean=totals.mean(), sensitivity_cv_percent=100 * totals.std(ddof=1) / totals.mean(),
                sensitivity_range_percent=100 * (totals.max() - totals.min()) / totals.mean(),
                within50_mean_percent=near.mean(), within50_range_points=near.max() - near.min(),
                ensemble_mean_sensitivity=float(mean.sel(layer=1).sum())))
    pd.DataFrame(spread_rows).to_csv(TABLES / "seed_spread.csv", index=False)

    # Afternoon 12:00-15:00 WIB window: 05/07/08 UTC single-seed runs plus the 06 UTC ensemble mean.
    window_rows = []
    for day in STUDY_DAYS:
        parts = [fields[k] for k in fields if k[0] == "afternoon_s0" and k[1].normalize() == day]
        six = MEAN / f"ensemble_bkt_{day + pd.Timedelta(hours=6):%Y%m%dT%H%MZ}.nc"
        if six.exists():
            with xr.open_dataset(six, engine="h5netcdf") as ds:
                parts.append(ds.layer_sensitivity.load())
        if len(parts) != 4:
            continue
        # Hours differ per member; align on backward lag so the window mean is lag-resolved.
        aligned = [p.assign_coords(time=np.arange(HOURS_BACK, 0, -1)).rename(time="lag_hours") for p in parts]
        window = xr.concat(aligned, dim="member").mean("member")
        window.attrs.update(comment="Mean of 05, 06, 07 and 08 UTC footprints for this day, lag-resolved",
                            members="05Z seed0; 06Z three-seed mean; 07Z seed0; 08Z seed0")
        window.to_dataset(name="layer_sensitivity").to_netcdf(
            MEAN / f"afternoon_window_bkt_{day:%Y%m%d}.nc", engine="h5netcdf",
            encoding={"layer_sensitivity": {"zlib": True, "complevel": 4}})
        window_rows.append(dict(day_utc=day.date(), members=4,
            window_sensitivity=float(window.sel(layer=1).sum()),
            member_sensitivity_cv_percent=100 * np.std([float(p.sel(layer=1).sum()) for p in parts], ddof=1)
            / np.mean([float(p.sel(layer=1).sum()) for p in parts])))
    pd.DataFrame(window_rows).to_csv(TABLES / "afternoon_window.csv", index=False)

    # Terrain-matched release versus the 30 m ensemble at the same seeds.
    terrain_rows = []
    for stamp in ANCHORS:
        for seed in SEEDS:
            low, high = fields.get((f"ensemble_s{seed}", stamp)), fields.get((f"terrain_h80_s{seed}", stamp))
            if low is None or high is None:
                continue
            terrain_rows.append(dict(receptor_utc=stamp, seed=seed,
                sensitivity_30m=float(low.sel(layer=1).sum()), sensitivity_80m=float(high.sel(layer=1).sum()),
                ratio_80_over_30=float(high.sel(layer=1).sum() / low.sel(layer=1).sum()),
                spatial_abs_difference_percent=100 * float(np.abs(high.sel(layer=1).sum("time")
                    - low.sel(layer=1).sum("time")).sum() / low.sel(layer=1).sum())))
    pd.DataFrame(terrain_rows).to_csv(TABLES / "terrain_height.csv", index=False)

    summary = dict(runs=len(ledger), groups=ledger.groupby("group").size().to_dict(),
        retention_min=float(ledger.endpoint_retention.min()),
        retention_below_95=int((ledger.endpoint_retention < .95).sum()),
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        convection_note="Convective mixing flag is F in every run; not a fix of convective transport")
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["run", "summarize", "list"])
    parser.add_argument("--group", default="all", choices=["all", "ensemble", "terrain", "afternoon", "forward"])
    parser.add_argument("--jobs", type=int, default=10)
    args = parser.parse_args()
    if args.stage == "list":
        for name, stamp, cfg in jobs(args.group):
            print(name, stamp, cfg.particles, cfg.receptor_height_m_agl, cfg.seed)
    elif args.stage == "run":
        if not 1 <= args.jobs <= 14:
            parser.error("jobs must be between 1 and 14")
        run(args.group, args.jobs)
    else:
        summarize()
