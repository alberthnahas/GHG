#!/usr/bin/env python3
"""Acquire meteorology and run a HYSPLIT-STILT footprint for BKT.

The gridded result is a source-receptor sensitivity field. It is not an
emission estimate, a source attribution, or a modeled absolute concentration.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

import ghg_common as G


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MET_DIR = ROOT / "data" / "hysplit" / "met"
DEFAULT_PROVENANCE_DIR = ROOT / "data" / "hysplit" / "provenance"
DEFAULT_OUTPUT_ROOT = ROOT / "outputs" / "hysplit"
NOAA_GDAS1_ROOT = "https://noaa-oar-arl-hysplit-pds.s3.amazonaws.com/gdas1"
GDAS1_NAME = re.compile(r"^gdas1\.([a-z]{3})(\d{2})\.w([1-5])$")


@dataclass(frozen=True)
class FootprintConfig:
    meteorology_label: str = "NOAA NCEP GDAS1 analysis, 1 degree, ARL format"
    receptor_lat: float = -0.202
    receptor_lon: float = 100.318
    station_elevation_m_msl: float = 864.5
    receptor_height_m_agl: float = 30.0
    hours_back: int = 72
    particles: int = 500
    grid_spacing_deg: float = 0.25
    grid_span_lat_deg: float = 20.0
    grid_span_lon_deg: float = 30.0
    pbl_fraction: float = 0.5
    output_interval_hours: int = 1
    seed: int = 0
    particle_diagnostic_variables: int = 20
    save_endpoints: bool = False


@dataclass(frozen=True)
class TransportOptions:
    """Explicit benchmark options; omitted options preserve the legacy setup.

    These are hypotheses to test, not calibrated physics. Repeated particle
    dumps retain inactive records for domain-completeness accounting.
    """
    minimum_mixing_depth_m: int = 250
    mixing_depth_method: int = 3
    convection: float = -2.0
    wrf_vertical_interpolation: bool = True
    dump_interval_hours: int = 0

    def __post_init__(self) -> None:
        if type(self.minimum_mixing_depth_m) is not int or self.minimum_mixing_depth_m <= 0:
            raise ValueError("minimum mixing depth must be a positive integer")
        if type(self.mixing_depth_method) is not int or self.mixing_depth_method not in (0, 1, 2, 3):
            raise ValueError("unsupported mixing-depth method")
        if (isinstance(self.convection, bool) or not isinstance(self.convection, (int, float))
                or not np.isfinite(self.convection)
                or (self.convection <= 0 and self.convection not in (-1, -2, -3))):
            raise ValueError("convection must be -1, -2, -3 or positive CAPE threshold")
        if type(self.dump_interval_hours) is not int or self.dump_interval_hours < 0:
            raise ValueError("dump interval must be a nonnegative integer")
        if type(self.wrf_vertical_interpolation) is not bool:
            raise ValueError("WRF vertical interpolation must be boolean")


def parse_utc(value: str) -> pd.Timestamp:
    """Parse an ISO-like timestamp and return a timezone-naive UTC hour."""
    stamp = pd.Timestamp(value)
    if stamp.tzinfo is not None:
        stamp = stamp.tz_convert("UTC").tz_localize(None)
    if stamp != stamp.floor("h"):
        raise ValueError("receptor time must be exactly on an hourly boundary")
    return stamp


def gdas1_week_name(day: pd.Timestamp) -> str:
    """Return NOAA's GDAS1 weekly archive name for a UTC date."""
    week = min(5, (day.day - 1) // 7 + 1)
    return f"gdas1.{day:%b%y}.w{week}".lower()


def required_met_names(receptor_utc: pd.Timestamp, hours_back: int) -> list[str]:
    if hours_back <= 0:
        raise ValueError("hours_back must be positive")
    start = receptor_utc - pd.Timedelta(hours=hours_back)
    days = pd.date_range(start.normalize(), receptor_utc.normalize(), freq="1D")
    return list(dict.fromkeys(gdas1_week_name(day) for day in days))


def gdas1_url(name: str) -> str:
    match = GDAS1_NAME.fullmatch(name)
    if not match:
        raise ValueError(f"not a GDAS1 weekly filename: {name}")
    _, yy, _ = match.groups()
    year = 2000 + int(yy)
    return f"{NOAA_GDAS1_ROOT}/{year}/{name}"


def sha256_file(path: Path, chunk_bytes: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_bytes), b""):
            digest.update(chunk)
    return digest.hexdigest()


def remote_size(url: str) -> int:
    request = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(request, timeout=60) as response:
        value = response.headers.get("Content-Length")
    if value is None:
        raise RuntimeError(f"server did not report Content-Length for {url}")
    return int(value)


def download_file(url: str, destination: Path) -> None:
    """Download with resume support, preferring aria2c and then curl."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if shutil.which("aria2c"):
        command = [
            "aria2c", "--continue=true", "--max-connection-per-server=8",
            "--split=8", "--min-split-size=8M", "--file-allocation=none",
            f"--dir={destination.parent}", f"--out={destination.name}", url,
        ]
    elif shutil.which("curl"):
        command = ["curl", "-fL", "--retry", "3", "--continue-at", "-",
                   "--output", str(destination), url]
    else:
        raise RuntimeError("meteorology download requires aria2c or curl")
    subprocess.run(command, check=True)


def write_provenance(path: Path, url: str, expected_bytes: int, destination: Path) -> Path:
    if not destination.is_file() or destination.stat().st_size != expected_bytes:
        got = destination.stat().st_size if destination.exists() else 0
        raise RuntimeError(f"incomplete meteorology file: {got} of {expected_bytes} bytes")
    record = {
        "dataset": "NCEP GDAS one-degree analysis in HYSPLIT ARL format",
        "provider": "NOAA Air Resources Laboratory",
        "source_url": url,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "filename": destination.name,
        "bytes": expected_bytes,
        "sha256": sha256_file(destination),
        "temporal_convention": "UTC",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return path


def fetch_meteorology(receptor_utc: pd.Timestamp, hours_back: int, met_dir: Path,
                      provenance_dir: Path) -> list[Path]:
    paths: list[Path] = []
    for name in required_met_names(receptor_utc, hours_back):
        url = gdas1_url(name)
        expected = remote_size(url)
        destination = met_dir / name
        aria_control = destination.with_name(destination.name + ".aria2")
        if (not destination.is_file() or destination.stat().st_size != expected
                or aria_control.exists()):
            download_file(url, destination)
        provenance = provenance_dir / f"{name}.json"
        write_provenance(provenance, url, expected, destination)
        paths.append(destination)
        print(f"verified {destination} ({expected:,} bytes)")
    return paths


def observation_at(receptor_utc: pd.Timestamp) -> dict[str, object]:
    """Return the exact harmonised BKT hourly record used as receptor context."""
    bkt = G.apply_flags(G.load_station("BKT"))
    rows = bkt[bkt["time_utc"].eq(receptor_utc)]
    if len(rows) != 1:
        raise RuntimeError(f"expected one BKT record at {receptor_utc}, found {len(rows)}")
    row = rows.iloc[0]
    if row[["co2", "ch4", "co"]].isna().any():
        raise RuntimeError("selected BKT receptor hour does not have complete CO2/CH4/CO")
    return {
        "station": "BKT",
        "station_name": "Bukit Kototabang",
        "time_utc": receptor_utc.isoformat() + "Z",
        "time_local_wib": pd.Timestamp(row.time_local).isoformat(),
        "co2_ppm": float(row.co2),
        "ch4_ppb": float(row.ch4),
        "co_ppb": float(row.co),
        "suspect_co2": bool(row.suspect_co2),
        "suspect_ch4": bool(row.suspect_ch4),
        "suspect_co": bool(row.suspect_co),
    }


def resolve_hysplit_home(value: Path | None) -> Path:
    if value is None:
        env = os.environ.get("HYSPLIT_HOME")
        if not env:
            raise RuntimeError("set HYSPLIT_HOME or pass --hysplit-home")
        value = Path(env)
    home = value.expanduser().resolve()
    for relative in ("exec/hycs_std", "exec/con2asc", "bdyfiles"):
        if not (home / relative).exists():
            raise FileNotFoundError(f"HYSPLIT installation lacks {relative}: {home}")
    return home


def ascdata_text(hysplit_home: Path) -> str:
    return (
        "-90.0  -180.0\n"
        "1.0     1.0\n"
        "180     360\n"
        "2\n"
        "0.2\n"
        f"'{(hysplit_home / 'bdyfiles').resolve()}/'\n"
    )


def control_text(receptor_utc: pd.Timestamp, met_paths: list[Path], run_dir: Path,
                 config: FootprintConfig, extra_levels_m: tuple[int, ...] = ()) -> str:
    """CONTROL text; ``extra_levels_m`` adds fixed concentration layers above the
    STILT PBL-fraction layer (HYSPLIT leaves that first layer unaffected).
    The default produces byte-identical text to earlier runs."""
    stop = receptor_utc - pd.Timedelta(hours=config.hours_back)
    levels = [str(int(round(config.pbl_fraction * 100)))]
    for level in extra_levels_m:
        if type(level) is not int or level <= 0 or level <= int(levels[-1]):
            raise ValueError("extra concentration levels must be increasing positive integers in metres")
        levels.append(str(level))
    records = [
        f"{receptor_utc:%y %m %d %H}",
        "1",
        f"{config.receptor_lat:.6f} {config.receptor_lon:.6f} {config.receptor_height_m_agl:.1f}",
        f"{-config.hours_back}",
        "0",
        "16500.0",
        str(len(met_paths)),
    ]
    for path in met_paths:
        records.extend([f"{path.parent.resolve()}/", path.name])
    records.extend([
        "1",
        "FOOT",
        "1.0",
        "1.0",
        f"{receptor_utc:%y %m %d %H} 00",
        "1",
        f"{config.receptor_lat:.6f} {config.receptor_lon:.6f}",
        f"{config.grid_spacing_deg:.4f} {config.grid_spacing_deg:.4f}",
        f"{config.grid_span_lat_deg:.4f} {config.grid_span_lon_deg:.4f}",
        f"{run_dir.resolve()}/",
        "cdump",
        str(len(levels)),
        " ".join(levels),
        f"{receptor_utc:%y %m %d %H} 00",
        f"{stop:%y %m %d %H} 00",
        f"0 {config.output_interval_hours:02d} 00",
        "1",
        "0.0 0.0 0.0",
        "0.0 0.0 0.0 0.0 0.0",
        "0.0 0.0 0.0",
        "0.0",
        "0.0",
    ])
    return "\n".join(records) + "\n"


def setup_text(config: FootprintConfig, transport: TransportOptions | None = None) -> str:
    options = transport or TransportOptions()
    if options.dump_interval_hours and not config.save_endpoints:
        raise ValueError("repeated dumps require save_endpoints")
    if options.dump_interval_hours and config.hours_back % options.dump_interval_hours:
        raise ValueError("dump interval must divide the run duration so the final endpoint is retained")
    return (
        "&SETUP\n"
        " INITD = 0,\n"
        " KPUFF = 0,\n"
        f" NUMPAR = {config.particles},\n"
        f" MAXPAR = {max(config.particles * 2, 100_000)},\n"
        f" KHMAX = {config.hours_back},\n"
        " ICHEM = 8,\n"
        " IDSP = 2,\n"
        " KBLT = 5,\n"
        f" KMIXD = {options.mixing_depth_method},\n"
        f" KMIX0 = {options.minimum_mixing_depth_m},\n"
        " VSCALES = -1.0,\n"
        f" CAPEMIN = {float(options.convection)},\n"
        f" WVERT = {'.TRUE.' if options.wrf_vertical_interpolation else '.FALSE.'},\n"
        " K10M = 1,\n"
        " KRAND = 2,\n"
        f" SEED = {config.seed},\n"
        " NINIT = 1,\n"
        f" NDUMP = {(options.dump_interval_hours or config.hours_back) if config.save_endpoints else 0},\n"
        f" NCYCL = {options.dump_interval_hours if config.save_endpoints else 1},\n"
        " OUTDT = -1,\n"
        f" IVMAX = {config.particle_diagnostic_variables},\n"
        f" VEGHT = {config.pbl_fraction:.3f},\n"
        " CPACK = 1,\n"
        " CMASS = 1,\n"
        "/\n"
    )


def run_checked(command: list[str], cwd: Path, log_stem: str) -> None:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    (cwd / f"{log_stem}.stdout.log").write_text(result.stdout, encoding="utf-8")
    (cwd / f"{log_stem}.stderr.log").write_text(result.stderr, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"{' '.join(command)} failed with exit code {result.returncode}")


def parse_ascii_layers(path: Path, receptor_utc: pd.Timestamp,
                       expected_layers: int) -> tuple[pd.DataFrame, list[str]]:
    """Parse con2asc output with one FOOT column per concentration layer.

    The first FOOT column is the STILT PBL-fraction surface layer; later
    columns are the fixed layers requested through ``extra_levels_m``.
    """
    frame = pd.read_csv(path, skipinitialspace=True)
    frame.columns = frame.columns.str.strip()
    required = {"YEAR", "MO", "DA", "HR", "LAT", "LON"}
    if not required.issubset(frame.columns):
        raise RuntimeError(f"unexpected con2asc schema: {frame.columns.tolist()}")
    value_columns = [name for name in frame.columns if name.startswith("FOOT")]
    if len(value_columns) != expected_layers:
        raise RuntimeError(f"expected {expected_layers} FOOT columns, found {value_columns}")
    frame["time_utc"] = pd.to_datetime(dict(
        year=frame.YEAR, month=frame.MO, day=frame.DA, hour=frame.HR,
    ))
    frame["lag_hours"] = (receptor_utc - frame["time_utc"]).dt.total_seconds() / 3600.0
    layers = []
    for index, column in enumerate(value_columns):
        name = "footprint_sensitivity" if index == 0 else f"layer{index + 1}_sensitivity"
        values = pd.to_numeric(frame[column], errors="coerce")
        if values.isna().any():
            raise RuntimeError("non-numeric footprint values found")
        if (values < 0).any():
            raise RuntimeError("negative footprint sensitivity found")
        if not np.isfinite(values).all():
            raise RuntimeError("non-finite footprint sensitivity found")
        frame[name] = values
        layers.append(name)
    keep = ["time_utc", "lag_hours", "LAT", "LON", *layers]
    return frame[keep].sort_values(keep[:4]).reset_index(drop=True), value_columns


def parse_ascii_footprint(path: Path, receptor_utc: pd.Timestamp) -> tuple[pd.DataFrame, str]:
    frame = pd.read_csv(path, skipinitialspace=True)
    frame.columns = frame.columns.str.strip()
    required = {"YEAR", "MO", "DA", "HR", "LAT", "LON"}
    if not required.issubset(frame.columns):
        raise RuntimeError(f"unexpected con2asc schema: {frame.columns.tolist()}")
    value_columns = [name for name in frame.columns if name.startswith("FOOT")]
    if len(value_columns) != 1:
        raise RuntimeError(f"expected one FOOT column, found {value_columns}")
    frame["time_utc"] = pd.to_datetime(dict(
        year=frame.YEAR, month=frame.MO, day=frame.DA, hour=frame.HR,
    ))
    frame["lag_hours"] = (receptor_utc - frame["time_utc"]).dt.total_seconds() / 3600.0
    frame["footprint_sensitivity"] = pd.to_numeric(frame[value_columns[0]], errors="coerce")
    if frame["footprint_sensitivity"].isna().any():
        raise RuntimeError("non-numeric footprint values found")
    if (frame["footprint_sensitivity"] < 0).any():
        raise RuntimeError("negative footprint sensitivity found")
    if not np.isfinite(frame["footprint_sensitivity"]).all():
        raise RuntimeError("non-finite footprint sensitivity found")
    keep = ["time_utc", "lag_hours", "LAT", "LON", "footprint_sensitivity"]
    return frame[keep].sort_values(keep[:-1]).reset_index(drop=True), value_columns[0]


def grid_coordinates(center: float, span: float, spacing: float) -> np.ndarray:
    count = int(round(span / spacing)) + 1
    return center - span / 2 + np.arange(count) * spacing


def write_netcdf(frame: pd.DataFrame, path: Path, receptor_utc: pd.Timestamp,
                 config: FootprintConfig, observation: dict[str, object]) -> xr.Dataset:
    times = pd.date_range(
        receptor_utc - pd.Timedelta(hours=config.hours_back),
        receptor_utc - pd.Timedelta(hours=config.output_interval_hours),
        freq=f"{config.output_interval_hours}h",
    )
    lat = grid_coordinates(config.receptor_lat, config.grid_span_lat_deg,
                           config.grid_spacing_deg)
    lon = grid_coordinates(config.receptor_lon, config.grid_span_lon_deg,
                           config.grid_spacing_deg)
    data = np.zeros((len(times), len(lat), len(lon)), dtype=np.float32)
    time_index = {value: idx for idx, value in enumerate(times)}
    for row in frame.itertuples(index=False):
        if row.time_utc not in time_index:
            raise RuntimeError(f"footprint timestamp outside expected periods: {row.time_utc}")
        iy = int(round((row.LAT - lat[0]) / config.grid_spacing_deg))
        ix = int(round((row.LON - lon[0]) / config.grid_spacing_deg))
        if not (0 <= iy < len(lat) and 0 <= ix < len(lon)):
            raise RuntimeError(f"footprint coordinate outside configured grid: {row.LAT}, {row.LON}")
        if not (np.isclose(lat[iy], row.LAT, atol=1e-4)
                and np.isclose(lon[ix], row.LON, atol=1e-4)):
            raise RuntimeError(f"footprint coordinate is off grid: {row.LAT}, {row.LON}")
        data[time_index[row.time_utc], iy, ix] += row.footprint_sensitivity
    dataset = xr.Dataset(
        data_vars={"footprint_sensitivity": (("time", "lat", "lon"), data)},
        coords={"time": times, "lat": lat, "lon": lon},
        attrs={
            "title": "BKT HYSPLIT-STILT backward surface-flux footprint",
            "station": "Bukit Kototabang (BKT)",
            "receptor_time_utc": observation["time_utc"],
            "receptor_height_m_agl": config.receptor_height_m_agl,
            "station_elevation_m_msl": config.station_elevation_m_msl,
            "meteorology": config.meteorology_label,
            "model_mode": "HYSPLIT ICHEM=8 with STILT dispersion",
            "crs": "EPSG:4326",
            "disclaimer": "Sensitivity field only; not emissions, attribution, or total concentration.",
        },
    )
    dataset["lat"].attrs.update({"standard_name": "latitude", "units": "degrees_north"})
    dataset["lon"].attrs.update({"standard_name": "longitude", "units": "degrees_east"})
    dataset["time"].attrs.update({"standard_name": "time"})
    dataset["footprint_sensitivity"].attrs.update({
        "long_name": "surface flux influence on receptor mixing ratio",
        "units": "ppm / (umol m-2 s-1)",
        "cell_methods": "time: mean (interval: 1 hour)",
        "comment": "HYSPLIT-STILT sensitivity for particles below half the modeled PBL.",
        "normalization": "Native requested-NUMPAR normalization; revised a39 analysis applies requested/actual emitted count",
    })
    dataset.to_netcdf(path, engine="h5netcdf", encoding={"footprint_sensitivity": {
        "zlib": True, "complevel": 4, "dtype": "float32",
    }})
    return dataset


def write_layer_netcdf(frame: pd.DataFrame, path: Path, receptor_utc: pd.Timestamp,
                       config: FootprintConfig, extra_levels_m: tuple[int, ...],
                       raw_columns: list[str]) -> xr.Dataset:
    """Multi-layer companion to ``write_netcdf``; layer 1 equals footprint.nc."""
    times = pd.date_range(
        receptor_utc - pd.Timedelta(hours=config.hours_back),
        receptor_utc - pd.Timedelta(hours=config.output_interval_hours),
        freq=f"{config.output_interval_hours}h",
    )
    lat = grid_coordinates(config.receptor_lat, config.grid_span_lat_deg, config.grid_spacing_deg)
    lon = grid_coordinates(config.receptor_lon, config.grid_span_lon_deg, config.grid_spacing_deg)
    layers = [name for name in frame.columns if name.endswith("_sensitivity")]
    data = np.zeros((len(layers), len(times), len(lat), len(lon)), dtype=np.float32)
    time_index = {value: idx for idx, value in enumerate(times)}
    for row in frame.itertuples(index=False):
        if row.time_utc not in time_index:
            raise RuntimeError(f"footprint timestamp outside expected periods: {row.time_utc}")
        iy = int(round((row.LAT - lat[0]) / config.grid_spacing_deg))
        ix = int(round((row.LON - lon[0]) / config.grid_spacing_deg))
        if not (0 <= iy < len(lat) and 0 <= ix < len(lon)):
            raise RuntimeError(f"footprint coordinate outside configured grid: {row.LAT}, {row.LON}")
        for k, name in enumerate(layers):
            data[k, time_index[row.time_utc], iy, ix] += getattr(row, name)
    tops = [f"{config.pbl_fraction:g} x PBL", *[f"{level} m AGL" for level in extra_levels_m]]
    dataset = xr.Dataset(
        data_vars={"layer_sensitivity": (("layer", "time", "lat", "lon"), data)},
        coords={"layer": np.arange(1, len(layers) + 1), "time": times, "lat": lat, "lon": lon,
                "layer_top": ("layer", tops), "con2asc_column": ("layer", raw_columns)},
        attrs={
            "title": "BKT HYSPLIT-STILT backward footprint by concentration layer",
            "receptor_time_utc": receptor_utc.isoformat() + "Z",
            "crs": "EPSG:4326",
            "comment": ("Layer 1 is the STILT surface layer (identical to footprint.nc). "
                        "Higher layers span from the previous layer top to the stated height; "
                        "their values are the receptor mixing-ratio sensitivity to a unit flux "
                        "released uniformly within that layer. Native requested-NUMPAR "
                        "normalization, as in footprint.nc."),
        },
    )
    dataset["layer_sensitivity"].attrs.update({"units": "ppm / (umol m-2 s-1)"})
    dataset.to_netcdf(path, engine="h5netcdf", encoding={"layer_sensitivity": {
        "zlib": True, "complevel": 4, "dtype": "float32",
    }})
    return dataset


def run_footprint(receptor_utc: pd.Timestamp, met_dir: Path, output_root: Path,
                  hysplit_home: Path, config: FootprintConfig, force: bool,
                  meteorology_paths: list[Path] | None = None,
                  transport: TransportOptions | None = None,
                  observation_context: dict[str, object] | None = None,
                  extra_levels_m: tuple[int, ...] = ()) -> Path:
    met_paths = meteorology_paths or [met_dir / name for name in required_met_names(receptor_utc, config.hours_back)]
    incomplete = [path for path in met_paths if (
        not path.is_file() or path.stat().st_size < (1_000_000 if meteorology_paths else 100_000_000)
        or path.with_name(path.name + ".aria2").exists()
    )]
    if incomplete:
        raise FileNotFoundError(f"missing or incomplete meteorology: {incomplete}")
    observation = observation_context if observation_context is not None else observation_at(receptor_utc)
    if parse_utc(str(observation["time_utc"])) != receptor_utc:
        raise ValueError("observation context and receptor time differ")
    run_dir = output_root / f"bkt_{receptor_utc:%Y%m%dT%H%MZ}"
    run_dir.mkdir(parents=True, exist_ok=True)
    generated = [
        "CONTROL", "SETUP.CFG", "ASCDATA.CFG", "cdump", "footprint.txt",
        "footprint_hourly.csv.gz", "footprint_aggregate.csv", "footprint.nc",
        "run_metadata.json", "hysplit.stdout.log", "hysplit.stderr.log",
        "con2asc.stdout.log", "con2asc.stderr.log", "MESSAGE", "WARNING",
        "VMSDIST", "PARDUMP", "PARTICLE_STILT.DAT", "CONC.CFG", "MAPTEXT.CFG",
        "fm_param.txt", "footprint_layers.nc", "bkt_hysplit_stilt_footprint.png",
        "bkt_hysplit_stilt_footprint.pdf", "map_metadata.json", "validation.json",
    ]
    present = [run_dir / name for name in generated if (run_dir / name).exists()]
    if present and not force:
        raise FileExistsError(f"run directory already contains outputs; use --force: {run_dir}")
    if force:
        for path in present:
            path.unlink()

    (run_dir / "CONTROL").write_text(
        control_text(receptor_utc, met_paths, run_dir, config, extra_levels_m), encoding="ascii")
    (run_dir / "SETUP.CFG").write_text(setup_text(config, transport), encoding="ascii")
    (run_dir / "ASCDATA.CFG").write_text(ascdata_text(hysplit_home), encoding="ascii")
    # HYSPLIT 5.4.2 writes PARTICLE_STILT.DAT at every one-minute STILT step
    # even with OUTDT < 0. Discard that optional diagnostic stream explicitly;
    # otherwise it can exceed the gridded footprint by orders of magnitude.
    particle_stream = run_dir / "PARTICLE_STILT.DAT"
    if os.name != "posix":
        raise RuntimeError("safe suppression of PARTICLE_STILT.DAT requires a POSIX system")
    particle_stream.symlink_to(os.devnull)
    model_start = time.monotonic()
    run_checked([str(hysplit_home / "exec" / "hycs_std")], run_dir, "hysplit")
    model_seconds = time.monotonic() - model_start
    cdump = run_dir / "cdump"
    if not cdump.is_file() or cdump.stat().st_size == 0:
        raise RuntimeError("HYSPLIT produced no concentration/footprint dump")
    message = (run_dir / "MESSAGE").read_text(encoding="utf-8", errors="replace")
    if "FATAL" in message.upper():
        raise RuntimeError("HYSPLIT MESSAGE contains a fatal error")
    run_checked([
        str(hysplit_home / "exec" / "con2asc"), "-icdump", "-ofootprint",
        "-d", "-s", "-x",
    ], run_dir, "con2asc")
    if extra_levels_m:
        layered, raw_columns = parse_ascii_layers(run_dir / "footprint.txt", receptor_utc,
                                                  1 + len(extra_levels_m))
        raw_column = raw_columns[0]
        write_layer_netcdf(layered, run_dir / "footprint_layers.nc", receptor_utc, config,
                           extra_levels_m, raw_columns)
        frame = layered[layered["footprint_sensitivity"] > 0][
            ["time_utc", "lag_hours", "LAT", "LON", "footprint_sensitivity"]].reset_index(drop=True)
    else:
        frame, raw_column = parse_ascii_footprint(run_dir / "footprint.txt", receptor_utc)
    if frame.empty or frame["footprint_sensitivity"].sum() <= 0:
        raise RuntimeError("HYSPLIT-STILT footprint is empty")
    frame.to_csv(run_dir / "footprint_hourly.csv.gz", index=False, compression="gzip")
    aggregate = frame.groupby(["LAT", "LON"], as_index=False).agg(
        sensitivity_sum=("footprint_sensitivity", "sum"),
        nonzero_hours=("footprint_sensitivity", lambda values: int((values > 0).sum())),
        first_time_utc=("time_utc", "min"),
        last_time_utc=("time_utc", "max"),
    )
    aggregate.to_csv(run_dir / "footprint_aggregate.csv", index=False)
    dataset = write_netcdf(frame, run_dir / "footprint.nc", receptor_utc, config, observation)
    csv_total = float(frame["footprint_sensitivity"].sum())
    netcdf_total = float(dataset["footprint_sensitivity"].sum())
    if not np.isclose(csv_total, netcdf_total, rtol=2e-6, atol=0.0):
        raise RuntimeError(f"CSV/NetCDF total mismatch: {csv_total} vs {netcdf_total}")
    metadata = {
        "observation": observation,
        "configuration": asdict(config),
        **({"transport_options": asdict(transport)} if transport is not None else {}),
        "model_runtime_seconds": model_seconds,
        "executable_sha256": sha256_file(hysplit_home / "exec" / "hycs_std"),
        "normalization_note": ("Native gridded output divides by requested NUMPAR. "
                               "Revised analysis multiplies by requested/actual emitted count; "
                               "see controlled normalization experiment in a39_bkt_refinement.py."),
        "meteorology_files": [str(path.resolve()) for path in met_paths],
        "hysplit_version_line": next(
            (line.strip() for line in message.splitlines() if "HYSPLIT version:" in line),
            "unknown",
        ),
        "raw_con2asc_value_column": raw_column,
        **({"extra_levels_m": list(extra_levels_m),
            "layer_note": ("footprint.nc holds the STILT PBL-fraction surface layer only; "
                           "footprint_layers.nc adds the fixed upper layers, whose values are "
                           "receptor sensitivity to a flux released uniformly into that layer")}
           if extra_levels_m else {}),
        "nonzero_cell_hours": int(len(frame)),
        "nonzero_grid_cells": int(len(aggregate)),
        "footprint_sensitivity_sum": csv_total,
        "footprint_units": "ppm / (umol m-2 s-1)",
        "sensitivity_weighted_centroid_lat": float(np.average(
            aggregate["LAT"], weights=aggregate["sensitivity_sum"])),
        "sensitivity_weighted_centroid_lon": float(np.average(
            aggregate["LON"], weights=aggregate["sensitivity_sum"])),
        "maximum_cell_lat": float(aggregate.loc[aggregate["sensitivity_sum"].idxmax(), "LAT"]),
        "maximum_cell_lon": float(aggregate.loc[aggregate["sensitivity_sum"].idxmax(), "LON"]),
        "maximum_cell_sensitivity_sum": float(aggregate["sensitivity_sum"].max()),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "interpretation_limit": "Sensitivity only; not emissions, attribution, or total concentration.",
    }
    (run_dir / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"footprint complete: {run_dir}")
    return run_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("fetch", "run"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--receptor-utc", default="2019-09-26T01:00:00")
        sub.add_argument("--hours-back", type=int, default=72)
        sub.add_argument("--met-dir", type=Path, default=DEFAULT_MET_DIR)
        if command == "fetch":
            sub.add_argument("--provenance-dir", type=Path, default=DEFAULT_PROVENANCE_DIR)
        else:
            sub.add_argument("--hysplit-home", type=Path)
            sub.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
            sub.add_argument("--receptor-height-m-agl", type=float, default=30.0)
            sub.add_argument("--particles", type=int, default=500)
            sub.add_argument("--seed", type=int, default=0)
            sub.add_argument("--particle-diagnostic-variables", type=int, choices=[0,20], default=20)
            sub.add_argument("--grid-spacing-deg", type=float, default=0.25)
            sub.add_argument("--grid-span-lat-deg", type=float, default=20.0)
            sub.add_argument("--grid-span-lon-deg", type=float, default=30.0)
            sub.add_argument("--force", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    receptor = parse_utc(args.receptor_utc)
    if args.command == "fetch":
        fetch_meteorology(receptor, args.hours_back, args.met_dir, args.provenance_dir)
        return
    config = FootprintConfig(
        receptor_height_m_agl=args.receptor_height_m_agl,
        hours_back=args.hours_back,
        particles=args.particles,
        seed=args.seed,
        particle_diagnostic_variables=args.particle_diagnostic_variables,
        grid_spacing_deg=args.grid_spacing_deg,
        grid_span_lat_deg=args.grid_span_lat_deg,
        grid_span_lon_deg=args.grid_span_lon_deg,
    )
    run_footprint(receptor, args.met_dir, args.output_root,
                  resolve_hysplit_home(args.hysplit_home), config, args.force)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
