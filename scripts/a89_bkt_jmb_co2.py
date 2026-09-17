#!/usr/bin/env python3
"""Two-receptor (BKT + Jambi) CO2 inversion on the a84 transport ensemble.

The 294 HYSPLIT-STILT runs of a84 are species independent: the same hourly
footprints are convolved here with CO2 inputs for 24 November to 31 December
2023, both inlets at 100 m above ground.

Inputs
  CarbonTracker CT-NRT.v2025-1 three-hourly 1 degree fluxes: optimized
    biosphere (bio_flux_opt) and ocean (ocn_flux_opt), imposed fire
    (fire_flux_imp) and fossil (fossil_flux_imp, comparison only).
  CarbonTracker CT-NRT.v2025-1 3 x 2 degree CO2 mole fractions for the
    endpoint background at 120 h.
  EDGAR_2025_GHG monthly fossil CO2 fluxes for November and December 2023,
    eight sectors, as the fossil prior.

State
  Positive multipliers on fossil CO2 within 500 km of the observing tower,
  fossil CO2 beyond 500 km, and the CT-NRT net biosphere exchange split by
  the local solar time of each grid cell into daytime (06-18) and nighttime
  terms. The biosphere responses are signed; a positive multiplier scales
  whatever CT-NRT prescribes. The split is by time, not by sign, because the
  CT-NRT optimized flux has an inverted day-night cycle on some days. Ocean
  and fire are fixed; per-tower offset and trend.

Stages
  plan       metadata-only list of the files to download, with sizes
  fetch      download (needs authorization); curl pinned to --interface
  prepare    fossil fields on each tower grid; CT-NRT fluxes on a 1 degree box
  operator   hourly footprint convolution, endpoint background, seed spread
  inversion  signed Bayesian fits by case, withheld evaluation, diagnostics
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import subprocess
import urllib.request
import zipfile

import numpy as np
import pandas as pd
import xarray as xr
from pyproj import Geod
from scipy.interpolate import RegularGridInterpolator
from scipy.linalg import solve_triangular

import a42_bkt_sources as src
import a71_domain_budget_extension as ext
import a84_bkt_jmb_two_receptor as T
from a43_bkt_source_analysis import MW, save_nc
from bkt_methane_inverse import InverseProblem, chain_diagnostics

ROOT = T.ROOT
TABLES = T.TABLES
INPUTS = T.OUT / "inputs_co2"
INVERSION = T.OUT / "inversion_co2"
NRT_BASE = "https://gml.noaa.gov/aftp/products/carbontracker/co2/CT-NRT.v2025-1"
NRT_DIR = ROOT / "data/bkt_sources/carbontracker_nrt"
EDGAR_DIR = ROOT / "data/bkt_sources/edgar_2025"
EDGAR_URL = "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/EDGAR_2025_GHG/monthly/CO2/bkl_{s}/bkl_{s}_flx_nc.zip"
SECTORS = ("AGRICULTURE", "BUILDINGS", "FUEL_EXPLOITATION", "IND_COMBUSTION", "IND_PROCESSES", "POWER_INDUSTRY", "TRANSPORT", "WASTE")
YEAR = 2023
MONTHS = pd.to_datetime(["2023-11-01", "2023-12-01"])
FLUX_DAYS = T.MET_DAYS
COMPONENTS = ["fossil_near", "fossil_far", "bio_day", "bio_night"]
NAMES = {"fossil_near": "Fossil ≤500 km", "fossil_far": "Fossil >500 km", "bio_day": "Biosphere, daytime", "bio_night": "Biosphere, nighttime"}
DAY_SOLAR_HOURS = (6., 18.)
INVERTED_EPISODE = (pd.Timestamp("2023-11-25"), pd.Timestamp("2023-12-01T23:59"))
# Working covariance in ppm: declared allowances, not measured errors.
MEASUREMENT_PPM, LOCAL_DAY_PPM, LOCAL_NIGHT_PPM, BACKGROUND_PPM = .2, 2., 5., 1.
OFFSET_PRIOR_PPM, TREND_PRIOR_PPM, MULTIPLIER_PRIOR_FACTOR = 3., 1., 2.
BOX = dict(lat=(-33., 31.), lon=(49., 155.))  # 1 degree box containing both tower grids
GEOD = Geod(ellps="WGS84")


# ------------------------------------------------------------------ helpers

def boundary_days() -> list[pd.Timestamp]:
    stamps = T.retained_stamps()
    return sorted({(s - pd.Timedelta(hours=T.HOURS_BACK)).normalize() for s in stamps})


def flux_file(day: pd.Timestamp) -> tuple[str, Path]:
    name = f"CT-NRT.v2025-1.flux1x1.{day:%Y%m%d}.nc"
    return f"{NRT_BASE}/fluxes/three-hourly/{name}", NRT_DIR / "fluxes" / name


def molefrac_file(day: pd.Timestamp) -> tuple[str, Path]:
    name = f"CT-NRT.v2025-1.molefrac_glb3x2_{day:%Y-%m-%d}.nc"
    return f"{NRT_BASE}/molefractions/co2_total/{name}", NRT_DIR / "molefractions" / name


def edgar_file(sector: str) -> Path:
    return EDGAR_DIR / f"CO2_{sector}_{YEAR}.nc"


def three_hour_center(times) -> pd.DatetimeIndex:
    """CT-NRT 3-hourly means are stamped at the interval center (01:30, 04:30, ...)."""
    return pd.DatetimeIndex(times).floor("3h") + pd.Timedelta(minutes=90)


def split_nee(nee: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Net biosphere flux into a nonnegative release and a nonnegative uptake magnitude."""
    return np.clip(nee, 0, None), np.clip(-nee, 0, None)


def solar_day_mask(times, lon: np.ndarray) -> np.ndarray:
    """(time, lon) mask of 3-hourly interval centers falling in local solar daytime."""
    t = pd.DatetimeIndex(times)
    solar = (t.hour.values[:, None] + t.minute.values[:, None] / 60 + np.asarray(lon)[None, :] / 15) % 24
    return (solar >= DAY_SOLAR_HOURS[0]) & (solar < DAY_SOLAR_HOURS[1])


def overlap_matrix(source: np.ndarray, target: np.ndarray, latitude: bool = False) -> np.ndarray:
    """Fraction of each source cell falling in each target cell (target x source); as bkt_footprint_spatial."""
    ds, dt = np.diff(source)[0], np.diff(target)[0]
    left = np.maximum(target[:, None] - dt / 2, source[None, :] - ds / 2)
    right = np.minimum(target[:, None] + dt / 2, source[None, :] + ds / 2)
    if latitude:
        widths = np.sin(np.deg2rad(right)) - np.sin(np.deg2rad(left))
        denominator = np.sin(np.deg2rad(source + ds / 2)) - np.sin(np.deg2rad(source - ds / 2))
    else:
        widths, denominator = right - left, ds
    return np.maximum(widths, 0) / denominator


def aggregate(field: np.ndarray, m_lat: np.ndarray, m_lon: np.ndarray) -> np.ndarray:
    """Cell-integrated footprint coefficients (hours, lat, lon) onto a coarser grid."""
    return np.einsum("ij,hjk,lk->hil", m_lat, field, m_lon, optimize=True)


class SignedInverseProblem(InverseProblem):
    """InverseProblem with signed response columns (uptake enters with a negative sign)."""

    def __post_init__(self):
        self.response = np.asarray(self.response, float)
        self.background_design = np.asarray(self.background_design, float)
        self.enhancement = np.asarray(self.enhancement, float)
        self.error_covariance = np.asarray(self.error_covariance, float)
        self.prior_sd = np.asarray(self.prior_sd, float)
        self.nsource = self.response.shape[1]
        self.ndim = self.nsource + self.background_design.shape[1]
        n = len(self.enhancement)
        if self.response.shape[0] != n or self.background_design.shape[0] != n:
            raise ValueError("Observation dimensions differ")
        if self.error_covariance.shape != (n, n) or self.prior_sd.shape != (self.ndim,):
            raise ValueError("Covariance/prior dimensions differ")
        for array in (self.response, self.background_design, self.enhancement, self.error_covariance, self.prior_sd):
            if not np.isfinite(array).all():
                raise ValueError("Nonfinite inversion input")
        if (self.prior_sd <= 0).any() or not np.allclose(self.error_covariance, self.error_covariance.T):
            raise ValueError("Invalid prior or covariance")
        self.chol = np.linalg.cholesky(self.error_covariance)
        self.kw = solve_triangular(self.chol, self.response, lower=True)
        self.bw = solve_triangular(self.chol, self.background_design, lower=True)
        self.yw = solve_triangular(self.chol, self.enhancement, lower=True)


# ------------------------------------------------------------------ download

def head_size(url: str) -> int:
    with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=60) as r:
        return int(r.headers["Content-Length"])


def plan(interface: str | None) -> pd.DataFrame:
    if interface:
        T.bind_interface(interface)
    jobs = [("CT-NRT three-hourly fluxes", *flux_file(d)) for d in FLUX_DAYS]
    jobs += [("CT-NRT CO2 mole fractions", *molefrac_file(d)) for d in boundary_days()]
    with ThreadPoolExecutor(max_workers=6) as pool:
        sizes = list(pool.map(lambda j: head_size(j[1]), jobs))
    rows = [dict(product=p, url=u, path=str(path.relative_to(ROOT)), bytes=b, present=path.exists() and path.with_suffix(path.suffix + ".json").exists())
            for (p, u, path), b in zip(jobs, sizes)]
    for sector in SECTORS:
        remote = src.RangeReader(EDGAR_URL.format(s=sector))
        with zipfile.ZipFile(remote) as z:
            member = [m for m in z.infolist() if f"_CO2_{YEAR}_" in m.filename]
        if len(member) != 1:
            raise ValueError(f"Unexpected EDGAR members for {sector}: {[m.filename for m in member]}")
        rows.append(dict(product="EDGAR_2025_GHG monthly CO2 (range read)", url=EDGAR_URL.format(s=sector), path=str(edgar_file(sector).relative_to(ROOT)),
                         bytes=member[0].compress_size, present=edgar_file(sector).with_suffix(".nc.json").exists()))
    table = pd.DataFrame(rows)
    TABLES.mkdir(parents=True, exist_ok=True)
    table.to_csv(TABLES / "co2_download_plan.csv", index=False)
    summary = table.groupby("product").agg(files=("url", "size"), megabytes=("bytes", lambda b: round(b.sum() / 1e6)), present=("present", "sum"))
    print(summary.to_string()); print("total MB", round(table.bytes.sum() / 1e6))
    return table


def curl(url: str, path: Path, interface: str | None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.with_suffix(path.suffix + ".json").exists():
        return path
    part = path.with_suffix(path.suffix + ".part")
    command = ["curl", "-fL", "--retry", "4", "--retry-delay", "5", "-C", "-", "-o", str(part), url]
    if interface:
        command[1:1] = ["--interface", interface]
    subprocess.run(command, check=True)
    if part.stat().st_size != head_size(url):
        raise ValueError(f"Incomplete download: {path.name}")
    part.replace(path)
    src.provenance(path, url, provider="NOAA Global Monitoring Laboratory", dataset="CarbonTracker CT-NRT.v2025-1")
    return path


def fetch(interface: str | None, workers: int = 3) -> None:
    if interface:
        T.bind_interface(interface)  # python range reads (EDGAR); curl is pinned separately
    jobs = [flux_file(d) for d in FLUX_DAYS] + [molefrac_file(d) for d in boundary_days()]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for path in pool.map(lambda j: curl(j[0], j[1], interface), jobs):
            print("acquired", path.name, flush=True)
    EDGAR_DIR.mkdir(parents=True, exist_ok=True)
    for sector in SECTORS:
        target = edgar_file(sector)
        if target.exists() and target.with_suffix(".nc.json").exists():
            continue
        url = EDGAR_URL.format(s=sector)
        remote = src.RangeReader(url)
        with zipfile.ZipFile(remote) as archive:
            names = [n for n in archive.namelist() if f"_CO2_{YEAR}_" in n and n.endswith(".nc")]
            if len(names) != 1:
                raise ValueError(f"Unexpected {YEAR} members: {names}")
            info = archive.getinfo(names[0])
            target.write_bytes(archive.read(names[0]))
        with xr.open_dataset(target) as ds:
            variables = {k: ds[k].attrs.get("units", "") for k in ds.data_vars}
        src.provenance(target, url, provider="European Commission JRC / IEA-EDGAR", dataset="EDGAR_2025_GHG monthly CO2 fluxes",
                       gas="CO2", sector=sector, year=YEAR, archive_member=names[0], archive_crc32=info.CRC,
                       archive_etag=remote.etag, transferred_bytes=remote.downloaded, variables=variables)
        print(f"acquired {target.name}: variables {variables}", flush=True)


# ------------------------------------------------------------------ inputs

def edgar_variable(ds: xr.Dataset) -> str:
    candidates = [k for k in ds.data_vars if ds[k].attrs.get("units", "").replace(" ", "") in ("kgm-2s-1", "kg/m2/s")]
    if len(candidates) != 1:
        raise ValueError(f"EDGAR flux variable not identified: {[(k, ds[k].attrs.get('units')) for k in ds.data_vars]}")
    return candidates[0]


def fossil_fields(code: str) -> xr.Dataset:
    lat, lon = T.receptor_grid(code)
    fields = []
    for sector in SECTORS:
        path = edgar_file(sector)
        if not path.with_suffix(".nc.json").exists():
            raise FileNotFoundError(f"Run fetch first: {path}")
        with xr.open_dataset(path) as ds:
            flux = ds[edgar_variable(ds)].sortby("lat").sortby("lon")
            if flux.sizes.get("time", 1) != 12:
                raise ValueError(f"Expected twelve monthly EDGAR fields: {path}")
            months = []
            for month in MONTHS:
                sub = flux.isel(time=month.month - 1).sel(lat=slice(lat[0] - .5, lat[-1] + .5), lon=slice(lon[0] - .5, lon[-1] + .5)).load()
                months.append(ext.remap_nonnegative(sub.values * 1e9 / MW["CO2"], sub.lat.values, sub.lon.values, lat, lon))
        fields.append(months)
    out = xr.Dataset({"flux": (("sector", "month", "lat", "lon"), np.asarray(fields))},
                     coords={"sector": list(SECTORS), "month": MONTHS, "lat": lat, "lon": lon})
    out.flux.attrs["units"] = "umol m-2 s-1"
    return out


def nrt_box() -> xr.Dataset:
    parts = []
    for day in FLUX_DAYS:
        url, path = flux_file(day)
        if not path.with_suffix(path.suffix + ".json").exists():
            raise FileNotFoundError(f"Run fetch first: {path}")
        with xr.open_dataset(path) as ds:
            ds = ds.rename(latitude="lat", longitude="lon").sortby("lat").sortby("lon")
            for name in ("bio_flux_opt", "ocn_flux_opt", "fire_flux_imp", "fossil_flux_imp"):
                if ds[name].attrs.get("units") != "mol m-2 s-1":
                    raise ValueError(f"Unexpected CT-NRT unit for {name}")
            parts.append(ds[["bio_flux_opt", "ocn_flux_opt", "fire_flux_imp", "fossil_flux_imp"]]
                         .sel(lat=slice(*BOX["lat"]), lon=slice(*BOX["lon"])).load() * 1e6)  # mol -> umol m-2 s-1
    box = xr.concat(parts, dim="time")
    expected = pd.date_range(FLUX_DAYS[0] + pd.Timedelta(minutes=90), FLUX_DAYS[-1] + pd.Timedelta(hours=22, minutes=30), freq="3h")
    if not np.array_equal(pd.DatetimeIndex(box.time.values), expected):
        raise ValueError("CT-NRT flux record is not a continuous 3-hourly series")
    release, uptake = split_nee(box.bio_flux_opt.values)
    day = solar_day_mask(box.time.values, box.lon.values)[:, None, :]
    net = box.bio_flux_opt.values
    out = xr.Dataset({"bio_release": (("time", "lat", "lon"), release), "bio_uptake": (("time", "lat", "lon"), uptake),
                      "bio_day": (("time", "lat", "lon"), np.where(day, net, 0.)), "bio_night": (("time", "lat", "lon"), np.where(day, 0., net)),
                      "ocean": box.ocn_flux_opt, "fire": box.fire_flux_imp, "fossil_ctnrt": box.fossil_flux_imp, "bio_net": box.bio_flux_opt},
                     coords={"time": box.time, "lat": box.lat, "lon": box.lon})
    for name in out.data_vars:
        out[name].attrs["units"] = "umol m-2 s-1"
    return out


def prepare() -> None:
    INPUTS.mkdir(parents=True, exist_ok=True)
    for code in T.STATIONS:
        save_nc(fossil_fields(code), INPUTS / f"{code.lower()}_fossil_monthly.nc")
        print("fossil fields", code, flush=True)
    box = nrt_box()
    save_nc(box, INPUTS / "ctnrt_fluxes_box.nc")
    print("CT-NRT flux box written", flush=True)
    phase_diagnostics(box)


def phase_diagnostics(box: xr.Dataset) -> pd.DataFrame:
    """Daily share of land cells whose CT-NRT biosphere flux is higher by day than by night (inverted cycle)."""
    nee = box.bio_net.values; t = pd.DatetimeIndex(box.time.values); lat, lon = box.lat.values, box.lon.values
    day = solar_day_mask(t, lon)
    land = np.abs(nee).max(axis=0) > .05
    sumatra = land & (lat[:, None] >= -6) & (lat[:, None] <= 6) & (lon[None, :] >= 95) & (lon[None, :] <= 106)
    rows = []
    for date in t.normalize().unique():
        sel = t.normalize() == date
        d = np.nanmean(np.where(day[sel][:, None, :], nee[sel], np.nan), axis=0)
        n = np.nanmean(np.where(~day[sel][:, None, :], nee[sel], np.nan), axis=0)
        inverted = d > n
        row = dict(date=date, domain_land_cells=int(land.sum()), domain_inverted_percent=100 * (inverted & land).sum() / land.sum(),
                   sumatra_land_cells=int(sumatra.sum()), sumatra_inverted_percent=100 * (inverted & sumatra).sum() / sumatra.sum())
        for code, (la, lo) in (("bkt", (-.5, 100.5)), ("jmb", (-1.5, 103.5))):
            i, j = np.argmin(abs(lat - la)), np.argmin(abs(lon - lo))
            row.update({f"{code}_cell_day_umol": d[i, j], f"{code}_cell_night_umol": n[i, j]})
        rows.append(row)
    table = pd.DataFrame(rows)
    table.to_csv(TABLES / "co2_ctnrt_phase_daily.csv", index=False)
    print(table[table.domain_inverted_percent > 10].round(2).to_string(index=False), flush=True)
    return table


# ------------------------------------------------------------------ operator

def endpoint_background(active: pd.DataFrame, stamp: pd.Timestamp, met_path: Path) -> dict[str, float]:
    arl = T.reader(str(met_path.resolve()))
    terrain = arl.field(stamp, "SHGT", 0)
    ground = RegularGridInterpolator((arl.lat, arl.lon), terrain)(active[["latitude", "longitude"]].to_numpy())
    height = active.height.to_numpy(float) + ground
    url, path = molefrac_file(stamp.normalize())
    record = path.with_suffix(path.suffix + ".json")
    if not record.exists() or T.model.sha256_file(path) != json.loads(record.read_text())["sha256"]:
        raise ValueError(f"Unverified CT-NRT boundary: {path}")
    center = three_hour_center([stamp])[0]
    with xr.open_dataset(path) as data:
        if data.co2.attrs.get("units") != "micromol mol-1" or data.gph.attrs.get("units") != "m":
            raise ValueError("CT-NRT units differ from the expected CO2/height convention")
        sample = data.sel(time=center)[["co2", "gph"]].interp(
            latitude=xr.DataArray(active.latitude.to_numpy(), dims="particle"),
            longitude=xr.DataArray(active.longitude.to_numpy(), dims="particle")).load()
    bounds = sample.gph.transpose("particle", "boundary").values
    centers = (bounds[:, :-1] + bounds[:, 1:]) / 2
    values = sample.co2.transpose("particle", "level").values
    if not np.isfinite(bounds).all() or not np.isfinite(values).all() or (np.diff(bounds, axis=1) <= 0).any():
        raise ValueError("Invalid CT-NRT vertical support")
    co2 = np.asarray([np.interp(z, h, c) for z, h, c in zip(height, centers, values)])
    return dict(background_ppm=float(co2.mean()), endpoint_sd_ppm=float(co2.std()))


def operator(allow_partial: bool = False, limit: int = 0) -> None:
    INVERSION.mkdir(parents=True, exist_ok=True)
    base = pd.read_csv(TABLES / "operator_base.csv", parse_dates=["time_utc"])
    with xr.open_dataset(INPUTS / "ctnrt_fluxes_box.nc") as ds:
        box = ds.load()
    centers = pd.DatetimeIndex(box.time.values)
    rows, sectors = [], []
    for code in T.STATIONS:
        lat, lon = T.receptor_grid(code)
        with xr.open_dataset(INPUTS / f"{code.lower()}_fossil_monthly.nc") as ds:
            fossil = ds.load()
        m_lat, m_lon = overlap_matrix(lat, box.lat.values, True), overlap_matrix(lon, box.lon.values)
        if not (np.allclose(m_lat.sum(axis=0), 1) and np.allclose(m_lon.sum(axis=0), 1)):
            raise ValueError("The CT-NRT box does not contain the footprint grid")
        glat, glon = np.meshgrid(lat, lon, indexing="ij")
        _, rlat, rlon, _ = T.STATIONS[code]
        _, _, distance = GEOD.inv(np.full(glon.shape, rlon), np.full(glat.shape, rlat), glon, glat)
        near = distance / 1000 <= 500
        stamps = sorted(base.loc[base.station.eq(code), "time_utc"])
        if limit:
            stamps = stamps[:limit]
        for stamp in stamps:
            dirs = [d for d in (T.run_dir(code, seed, stamp) for seed in T.SEEDS) if (d / "completion_receipt.json").exists()]
            if len(dirs) != len(T.SEEDS) and not (allow_partial and len(dirs) >= 2):
                raise FileNotFoundError(f"Ensemble incomplete for {code} {stamp}")
            members = []
            for directory in dirs:
                field, meta, actual = ext.read_footprint(directory)
                hours = pd.DatetimeIndex(field.time.values)
                values = field.values
                row = dict(seed=meta["configuration"]["seed"], sensitivity=float(values.sum()))
                month_of = hours.to_period("M").to_timestamp()
                fossil_total = fossil.flux.sum("sector")
                near_ppm = far_ppm = 0.
                for month in pd.unique(month_of):
                    integrated = values[month_of == month].sum(axis=0)
                    contribution = integrated * fossil_total.sel(month=month).values
                    near_ppm += contribution[near].sum(); far_ppm += contribution[~near].sum()
                    for sector in SECTORS:
                        sectors.append(dict(station=code, time_utc=stamp, seed=row["seed"], sector=sector,
                                            ppm=float((integrated * fossil.flux.sel(sector=sector, month=month).values).sum())))
                row.update(fossil_near_ppm=near_ppm, fossil_far_ppm=far_ppm)
                coarse = aggregate(values, m_lat, m_lon)
                index = centers.get_indexer(three_hour_center(hours))
                if (index < 0).any():
                    raise ValueError(f"Footprint hours outside the CT-NRT flux record: {code} {stamp}")
                for name in ("bio_day", "bio_night", "bio_release", "bio_uptake", "ocean", "fire", "fossil_ctnrt", "bio_net"):
                    row[f"{name}_ppm"] = float(np.einsum("hij,hij->", coarse, box[name].values[index]))
                active = ext.active_endpoints(directory, meta, actual)
                end = stamp - pd.Timedelta(hours=meta["configuration"]["hours_back"])
                row.update(endpoint_background(active, end, T.MET / f"{end:%Y%m%d}_gfs0p25"))
                members.append(row)
            m = pd.DataFrame(members)
            numeric = [c for c in m.columns if c.endswith("_ppm") or c == "sensitivity"]
            out = dict(station=code, time_utc=stamp, members=len(m), **m[numeric].mean().to_dict())
            out.update({f"{c}_seed_sd": float(m[c].std(ddof=1)) for c in ("fossil_near_ppm", "bio_day_ppm", "bio_night_ppm", "background_ppm")})
            rows.append(out)
            print(f"co2 operator {code} {stamp}: fossil {out['fossil_near_ppm'] + out['fossil_far_ppm']:.2f} bio day {out['bio_day_ppm']:.2f} "
                  f"night {out['bio_night_ppm']:.2f} bg {out['background_ppm']:.2f}", flush=True)
    frame = pd.DataFrame(rows).merge(
        base[["station", "time_utc", "co2", "ch4", "holdout", "transport_usable", "endpoint_survival_fraction", "PBLH", "SHGT", "U10M", "V10M"]],
        on=["station", "time_utc"], validate="one_to_one")
    frame.to_csv(TABLES / "co2_operator_base.csv", index=False)
    pd.DataFrame(sectors).groupby(["station", "time_utc", "sector"]).ppm.mean().reset_index().to_csv(TABLES / "co2_sector_responses.csv", index=False)


# ------------------------------------------------------------------ inversion

SPIKE_CO2_PPM, SPIKE_TRACER_PPB = 20., 20.


def spike_screen(frame: pd.DataFrame) -> pd.DataFrame:
    """Flag isolated one-hour CO2 spikes with no matching CH4 or CO change.

    Departure is the value minus the mean of the hours before and after. A
    receptor hour is flagged when |dCO2| exceeds 20 ppm while |dCH4| and |dCO|
    stay below 20 ppb: a CO2-only jump of that size in one hour is not an
    air-mass change. Hours without both neighbours are not flagged.
    """
    import ghg_common as G
    rows = []
    for code in frame.station.unique():
        record = G.apply_flags(G.load_station(code)).set_index("time_utc").sort_index()
        for stamp in frame.loc[frame.station.eq(code), "time_utc"]:
            window = record.reindex([stamp - pd.Timedelta(hours=1), stamp, stamp + pd.Timedelta(hours=1)])
            dep = {sp: window[sp].iloc[1] - window[sp].iloc[[0, 2]].mean() for sp in ("co2", "ch4", "co")}
            testable = window[["co2", "ch4", "co"]].notna().all().all()
            flagged = bool(testable and abs(dep["co2"]) > SPIKE_CO2_PPM and abs(dep["ch4"]) < SPIKE_TRACER_PPB and abs(dep["co"]) < SPIKE_TRACER_PPB)
            rows.append(dict(station=code, time_utc=stamp, testable=bool(testable), co2_departure_ppm=dep["co2"],
                             ch4_departure_ppb=dep["ch4"], co_departure_ppb=dep["co"], co2_only_spike=flagged))
    table = pd.DataFrame(rows)
    table.to_csv(TABLES / "co2_spike_screen.csv", index=False)
    print("CO2-only spikes flagged:", table[table.co2_only_spike][["station", "time_utc", "co2_departure_ppm", "ch4_departure_ppb", "co_departure_ppb"]].round(1).to_string(index=False), flush=True)
    return table


def design(frame: pd.DataFrame, components: list[str] | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    midpoint = T.WINDOW[0] + (T.WINDOW[1] - T.WINDOW[0]) / 2
    columns, names = [], []
    for code in sorted(frame.station.unique()):
        member = frame.station.eq(code).to_numpy().astype(float)
        columns += [member, member * (frame.time_utc - midpoint).dt.total_seconds().to_numpy() / (28 * 86400)]
        names += [f"offset_{code}", f"trend_{code}"]
    k = frame[[c + "_ppm" for c in (components or COMPONENTS)]].to_numpy()
    base = (frame.background_ppm + frame.ocean_ppm + frame.fire_ppm).to_numpy()
    return k, np.column_stack(columns), base, names


def covariance(frame: pd.DataFrame, k: np.ndarray, transport: float) -> np.ndarray:
    """Block covariance in ppm: correlated within a tower, independent between towers."""
    n = len(frame)
    r = np.zeros((n, n))
    hours = frame.time_utc.to_numpy(dtype="datetime64[s]").astype("int64") / 3600
    for code in frame.station.unique():
        m = frame.station.eq(code).to_numpy()
        lag = np.abs(hours[m][:, None] - hours[m][None, :])
        local = np.where(frame.time_utc[m].dt.hour.eq(18), LOCAL_NIGHT_PPM, LOCAL_DAY_PPM)
        scale = transport * np.abs(k[m]).sum(axis=1)
        block = np.diag(MEASUREMENT_PPM ** 2 + local ** 2) + np.outer(scale, scale) * np.exp(-lag / 24) + BACKGROUND_PPM ** 2 * np.exp(-lag / 72)
        r[np.ix_(m, m)] = block
    r += np.diag((frame.ocean_ppm.abs() + frame.fire_ppm.abs()).to_numpy() ** 2)
    return r


def reduced_chi_square(p: InverseProblem, ntrain: int) -> float:
    theta, _, _ = p.fit()
    res = p.residual(theta)[:ntrain]
    return float(res @ res / ntrain)


def metrics(observed, predicted) -> dict:
    o, p = np.asarray(observed, float), np.asarray(predicted, float)
    e = p - o
    return dict(n=len(o), bias_ppm=float(e.mean()), rmse_ppm=float(np.sqrt(np.mean(e ** 2))),
                correlation=float(np.corrcoef(o, p)[0, 1]) if len(o) > 2 and np.std(p) > 0 else np.nan)


def fit(label: str, frame: pd.DataFrame, train: np.ndarray, evaluate: np.ndarray,
        components: list[str] | None = None, obs: str = "co2") -> dict:
    components = components or COMPONENTS
    k, b, base, names = design(frame, components)
    y = frame[obs].to_numpy() - base
    sd = np.r_[np.repeat(np.log(MULTIPLIER_PRIOR_FACTOR), k.shape[1]), np.tile([OFFSET_PRIOR_PPM, TREND_PRIOR_PPM], b.shape[1] // 2)]
    scan = []
    for t in (.05, .1, .15, .2, .25, .3, .4, .5, .6, .8, 1.0):
        p = SignedInverseProblem(k[train], b[train], y[train], covariance(frame, k, t)[np.ix_(train, train)], sd)
        scan.append(dict(case=label, transport_fraction=t, reduced_chi_square=reduced_chi_square(p, int(train.sum()))))
    chi = np.array([s["reduced_chi_square"] for s in scan]); ts = np.array([s["transport_fraction"] for s in scan])
    transport = float(ts[0] if chi.max() < 1 else ts[-1] if chi.min() > 1 else np.interp(1.0, chi[::-1], ts[::-1]))
    r = covariance(frame, k, transport)
    p = SignedInverseProblem(k[train], b[train], y[train], r[np.ix_(train, train)], sd)
    p.fit()
    for draws, thin in ((12000, 3), (48000, 12)):  # one retry with longer chains before rejecting the fit
        chains, _ = p.sample(draws=draws, thin=thin)
        rh, ess = chain_diagnostics(chains)
        if np.max(rh) <= 1.01 and np.min(ess) >= 1000:
            break
        print(f"{label}: Rhat max {np.max(rh):.4f}, ESS min {np.min(ess):.0f} with {draws} draws", flush=True)
    else:
        raise RuntimeError(f"{label}: convergence inadequate Rhat={rh} ESS={ess}")
    samples = chains.reshape(-1, p.ndim); ns = k.shape[1]
    params = []
    for j, name in enumerate(components + names):
        v = np.exp(samples[:, j]) if j < ns else samples[:, j]
        q = np.quantile(v, [.025, .5, .975])
        params.append(dict(case=label, parameter=name, median=q[1], q025=q[0], q975=q[2], transport_fraction=transport,
                           probability_above_prior=float((v > 1).mean()) if j < ns else np.nan,
                           variance_reduction_percent=100 * (1 - np.var(samples[:, j]) / sd[j] ** 2), rhat=rh[j], ess=ess[j]))
    pred = base[None, :] + np.exp(samples[:, :ns]) @ k.T + samples[:, ns:] @ b.T
    median = np.median(pred, axis=0)
    chol = np.linalg.cholesky(r[np.ix_(train, train)])
    bw = solve_triangular(chol, b[train], lower=True); yw = solve_triangular(chol, y[train], lower=True)
    beta = np.linalg.solve(bw.T @ bw + np.diag(1 / sd[ns:] ** 2), bw.T @ yw)
    background_only = base + b @ beta
    prior = base + k.sum(axis=1)
    evals = []
    for split, mask in (("training", train), ("evaluation", evaluate)):
        for code in frame.station.unique():
            mm = mask & frame.station.eq(code).to_numpy()
            if mm.sum() >= 3:
                for model, values in (("posterior", median), ("background_only", background_only), ("prior", prior)):
                    evals.append(dict(case=label, split=split, station=code, model=model, transport_fraction=transport,
                                      **metrics(frame[obs].to_numpy()[mm], values[mm])))
    predictions = pd.DataFrame(dict(case=label, station=frame.station, time_utc=frame.time_utc, training=train, evaluation=evaluate,
                                    observed_ppm=frame[obs], posterior_median_ppm=median, posterior_q025_ppm=np.quantile(pred, .025, axis=0),
                                    posterior_q975_ppm=np.quantile(pred, .975, axis=0), prior_ppm=prior, background_only_ppm=background_only,
                                    background_ppm=frame.background_ppm, mismatch_sd_ppm=np.sqrt(np.diag(r))))
    return dict(params=params, evals=evals, predictions=predictions, scan=scan)


def inversion() -> None:
    frame = pd.read_csv(TABLES / "co2_operator_base.csv", parse_dates=["time_utc"])
    frame = frame[frame.transport_usable & frame.co2.notna()].reset_index(drop=True)
    spikes = spike_screen(frame)
    frame = frame.merge(spikes[["station", "time_utc", "co2_only_spike"]], on=["station", "time_utc"], validate="one_to_one")
    frame = frame[~frame.co2_only_spike].reset_index(drop=True)
    holdout = frame.holdout.to_numpy(bool)
    bkt, jmb = frame.station.eq("BKT").to_numpy(), frame.station.eq("JMB").to_numpy()
    day = frame.time_utc.dt.hour.eq(6).to_numpy()
    jmb_night = jmb & ~day
    cases = [("bkt_only", bkt & ~holdout, bkt & holdout), ("jmb_only", jmb & ~holdout, jmb & holdout),
             ("joint", ~holdout, holdout), ("joint_daytime", day & ~holdout, day & holdout),
             ("joint_screened", ~holdout & ~jmb_night, holdout & ~jmb_night), ("bkt_to_jmb_day", bkt & ~holdout, jmb & day)]
    # CT-NRT biosphere cycle is inverted over both tower cells from 25 November to 1 December 2023
    # (co2_ctnrt_phase_daily.csv); receptors whose 120 h footprint reaches that episode are dropped here.
    clear = ~frame.time_utc.between(INVERTED_EPISODE[0], INVERTED_EPISODE[1] + pd.Timedelta(hours=T.HOURS_BACK)).to_numpy()
    cases.append(("joint_screened_no_inverted", ~holdout & ~jmb_night & clear, holdout & ~jmb_night & clear))
    results = []
    for label, train, evaluate in cases:
        if train.sum() < 10:
            print(f"skip {label}: {int(train.sum())} training hours", flush=True)
            continue
        results.append(fit(label, frame, train, evaluate))
        print(label, "transport fraction", results[-1]["params"][0]["transport_fraction"], flush=True)
    pd.DataFrame([p for r in results for p in r["params"]]).to_csv(TABLES / "co2_inversion_parameters.csv", index=False)
    pd.DataFrame([e for r in results for e in r["evals"]]).to_csv(TABLES / "co2_inversion_evaluation.csv", index=False)
    pd.concat([r["predictions"] for r in results]).to_csv(TABLES / "co2_inversion_predictions.csv", index=False)
    pd.DataFrame([s for r in results for s in r["scan"]]).to_csv(TABLES / "co2_transport_error_scan.csv", index=False)
    frame["hour"] = frame.time_utc.dt.hour
    frame["enhancement_ppm"] = frame.co2 - frame.background_ppm
    frame["prior_ppm"] = frame[[c + "_ppm" for c in COMPONENTS]].to_numpy().sum(axis=1) + frame.ocean_ppm + frame.fire_ppm
    diurnal = frame.groupby(["station", "hour"]).agg(n=("co2", "size"), enhancement_mean=("enhancement_ppm", "mean"), enhancement_sd=("enhancement_ppm", "std"),
        prior_mean=("prior_ppm", "mean"), fossil_near_mean=("fossil_near_ppm", "mean"), fossil_far_mean=("fossil_far_ppm", "mean"),
        bio_day_mean=("bio_day_ppm", "mean"), bio_night_mean=("bio_night_ppm", "mean"), background_mean=("background_ppm", "mean"),
        pblh_median=("PBLH", "median")).reset_index()
    diurnal.to_csv(TABLES / "co2_diurnal_summary.csv", index=False)
    pd.set_option("display.width", 250)
    print(diurnal.round(2).to_string(index=False))
    P = pd.DataFrame([p for r in results for p in r["params"]])
    print(P[P.parameter.isin(COMPONENTS)][["case", "parameter", "median", "q025", "q975", "transport_fraction", "variance_reduction_percent"]].round(3).to_string(index=False))
    E = pd.DataFrame([e for r in results for e in r["evals"]])
    print(E[E.split.eq("evaluation")].pivot_table(index=["case", "station"], columns="model", values="rmse_ppm").round(2).to_string())


def diagnostics() -> None:
    """Daytime fit robustness: leave-one-out MAP multipliers and skill over all daytime hours."""
    frame = pd.read_csv(TABLES / "co2_operator_base.csv", parse_dates=["time_utc"])
    frame = frame[frame.transport_usable & frame.co2.notna()].reset_index(drop=True)
    spikes = pd.read_csv(TABLES / "co2_spike_screen.csv", parse_dates=["time_utc"])
    frame = frame.merge(spikes[["station", "time_utc", "co2_only_spike"]], on=["station", "time_utc"], validate="one_to_one")
    frame = frame[~frame.co2_only_spike].reset_index(drop=True)
    train = frame.time_utc.dt.hour.eq(6).to_numpy() & ~frame.holdout.to_numpy(bool)
    k, b, base, names = design(frame); y = frame.co2.to_numpy() - base
    sd = np.r_[np.repeat(np.log(MULTIPLIER_PRIOR_FACTOR), k.shape[1]), np.tile([OFFSET_PRIOR_PPM, TREND_PRIOR_PPM], b.shape[1] // 2)]
    transport = pd.read_csv(TABLES / "co2_inversion_parameters.csv").query("case == 'joint_daytime'").transport_fraction.iloc[0]
    r = covariance(frame, k, transport)
    def mapfit(mask):
        problem = SignedInverseProblem(k[mask], b[mask], y[mask], r[np.ix_(mask, mask)], sd)
        theta, _, _ = problem.fit()
        return np.exp(theta[:k.shape[1]])
    rows = [dict(dropped="none", **dict(zip(COMPONENTS, mapfit(train))))]
    for i in np.flatnonzero(train):
        mask = train.copy(); mask[i] = False
        rows.append(dict(dropped=f"{frame.station[i]} {frame.time_utc[i]:%Y-%m-%dT%H}", **dict(zip(COMPONENTS, mapfit(mask)))))
    pd.DataFrame(rows).to_csv(TABLES / "co2_daytime_leave_one_out.csv", index=False)
    pred = pd.read_csv(TABLES / "co2_inversion_predictions.csv", parse_dates=["time_utc"])
    d = pred[pred.case.eq("joint_daytime") & pred.time_utc.dt.hour.eq(6)]
    skill = []
    for code, g in d.groupby("station"):
        for model, col in (("posterior", "posterior_median_ppm"), ("background_only", "background_only_ppm"), ("prior", "prior_ppm")):
            e = g[col] - g.observed_ppm
            skill.append(dict(station=code, model=model, n=len(g), rmse_ppm=float(np.sqrt((e ** 2).mean())), bias_ppm=float(e.mean()),
                              correlation=float(np.corrcoef(g.observed_ppm, g[col])[0, 1])))
    pd.DataFrame(skill).to_csv(TABLES / "co2_daytime_skill.csv", index=False)
    loo = pd.DataFrame(rows[1:])
    print("leave-one-out ranges:", {c: (round(loo[c].min(), 2), round(loo[c].max(), 2)) for c in COMPONENTS})
    print(pd.DataFrame(skill).round(2).to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["plan", "fetch", "prepare", "operator", "inversion", "diagnostics", "all"])
    parser.add_argument("--interface", default=None)
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    a = parser.parse_args()
    if a.stage == "plan":
        plan(a.interface)
    elif a.stage == "fetch":
        fetch(a.interface)
    elif a.stage == "prepare":
        prepare()
    elif a.stage == "operator":
        operator(a.allow_partial, a.limit)
    elif a.stage == "inversion":
        inversion()
    elif a.stage == "diagnostics":
        diagnostics()
    else:
        prepare(); operator(a.allow_partial, a.limit); inversion(); diagnostics()


if __name__ == "__main__":
    main()
