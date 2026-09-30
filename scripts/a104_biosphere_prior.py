#!/usr/bin/env python3
"""A biosphere prior that takes from each source what it is good at.

The audit says the terrestrial biosphere carries 95% of the modelled carbon
dioxide signal at these towers, so it, not the emission inventory, is what
limits that gas. Two sources exist and each fails differently:

  CarbonTracker CT-NRT is assimilated, so its magnitude, spatial pattern and
    seasonality carry real information. Its sub-daily phase inverts for a week
    of this window over both tower cells, releasing carbon by day and taking it
    up at night, which no inversion can use.

  the diagnostic prior follows sunlight and temperature, so its phase cannot
    invert. Its amplitude is wrong: the inversion scales it to between 0.20 and
    0.42, meaning it overstates the afternoon drawdown by two to five times.

A daily mean is insensitive to the phase error, and a diurnal shape is
insensitive to the magnitude error. So the hybrid takes the daily mean and the
diurnal amplitude from CarbonTracker, and the diurnal shape from the diagnostic
model:

    NEE(t) = daily mean from CT-NRT
             + diagnostic shape, rescaled to the CT-NRT diurnal amplitude

The amplitude is measured only on days when CT-NRT's own phase is correct, so a
week of inverted flux cannot contaminate it. By construction the result has the
CarbonTracker daily mean exactly, a phase that cannot invert, and an amplitude
that no longer comes from an uncalibrated light-use assumption.

What this does not fix: the prior is still not a measured flux, and no water or
nutrient limitation enters except through whatever CarbonTracker assimilated.

Stages
  build       write the hybrid prior and its validation report
  compare     the three priors at the tower cells, by local solar hour
"""
from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd
import xarray as xr

import a84_bkt_jmb_two_receptor as T
import a89_bkt_jmb_co2 as C
import a90_bkt_jmb_co2_improved as I

INPUTS = I.INPUTS
OUT = T.ROOT / "outputs/operational"
AMPLITUDE_LIMITS = (0.05, 3.0)      # how far the CT-NRT amplitude may rescale the diagnostic shape
MIN_PHASE_DAYS = 3                  # fewer correct days than this and the cell keeps the diagnostic amplitude


def local_solar_hour(stamps: pd.DatetimeIndex, lon: np.ndarray) -> np.ndarray:
    return (stamps.hour.to_numpy()[:, None] + lon[None, :] / 15.0) % 24


def phase_is_correct(nee: np.ndarray, solar: np.ndarray) -> np.ndarray:
    """True where the day's strongest uptake falls in daylight, which is what a real biosphere does."""
    daytime = (solar >= 9) & (solar <= 15)
    night = (solar < 4) | (solar > 20)
    with np.errstate(invalid="ignore"):
        day_mean = np.where(daytime, nee, np.nan)
        night_mean = np.where(night, nee, np.nan)
        return np.nanmean(day_mean, axis=0) < np.nanmean(night_mean, axis=0)


def build(label: str = "hybrid") -> dict:
    with xr.open_dataset(INPUTS / "diagnostic_biosphere.nc") as ds:
        diagnostic = ds.load()
    with xr.open_dataset(C.INPUTS / "ctnrt_fluxes_box.nc") as ds:
        ctnrt = ds.bio_net.load()

    lat, lon = diagnostic.lat.values, diagnostic.lon.values
    stamps = pd.DatetimeIndex(diagnostic.time.values)
    gpp, resp = diagnostic.gpp.values, diagnostic.resp.values
    native = gpp + resp

    # CT-NRT onto the diagnostic grid and clock. It is a one-degree field, so nearest
    # is honest in space; its stamps sit at interval centres and there is one more of
    # them, so the time axis is matched by nearest rather than assumed to line up.
    coarse = (ctnrt.interp(lat=("lat", lat), lon=("lon", lon), method="nearest", kwargs=dict(fill_value=None))
              .sel(time=diagnostic.time, method="nearest")
              .transpose("time", "lat", "lon").values)
    coarse = np.where(np.isfinite(coarse), coarse, 0.0)
    if coarse.shape != gpp.shape:
        raise ValueError(f"CarbonTracker did not align onto the diagnostic grid: {coarse.shape} against {gpp.shape}")

    days = stamps.normalize()
    unique_days = pd.DatetimeIndex(pd.unique(days))
    solar_by_day, ct_mean, ct_amplitude, diag_amplitude, correct = [], [], [], [], []
    for day in unique_days:
        rows = days == day
        solar = local_solar_hour(stamps[rows], lon)                      # hours x lon
        solar_full = np.repeat(solar[:, None, :], len(lat), axis=1)      # hours x lat x lon
        ct_day, diag_day = coarse[rows], native[rows]
        ct_mean.append(ct_day.mean(axis=0))
        ct_amplitude.append(ct_day.max(axis=0) - ct_day.min(axis=0))
        diag_amplitude.append(diag_day.max(axis=0) - diag_day.min(axis=0))
        correct.append(phase_is_correct(ct_day, solar_full))
        solar_by_day.append(solar_full)
    ct_mean = np.array(ct_mean); ct_amplitude = np.array(ct_amplitude)
    diag_amplitude = np.array(diag_amplitude); correct = np.array(correct)

    # amplitude from CT-NRT, measured only where its own phase is sound
    usable = correct & (diag_amplitude > 1e-9)
    ratio = np.where(usable, ct_amplitude / np.where(diag_amplitude > 1e-9, diag_amplitude, 1.0), np.nan)
    with np.errstate(invalid="ignore"):
        scale = np.nanmedian(ratio, axis=0)
    enough = np.sum(usable, axis=0) >= MIN_PHASE_DAYS
    scale = np.where(enough & np.isfinite(scale), scale, 1.0)
    scale = np.clip(scale, *AMPLITUDE_LIMITS)

    # rescale the diagnostic shape, then set each day's mean to the CarbonTracker mean
    gpp_h = gpp * scale[None, :, :]
    resp_h = resp * scale[None, :, :]
    hybrid = gpp_h + resp_h
    for index, day in enumerate(unique_days):
        rows = days == day
        offset = ct_mean[index] - hybrid[rows].mean(axis=0)
        resp_h[rows] += offset[None, :, :]
    # respiration must not go negative; any deficit moves into uptake, which may
    deficit = np.clip(resp_h, None, 0.0)
    resp_h = resp_h - deficit
    gpp_h = gpp_h + deficit

    dataset = xr.Dataset(
        dict(gpp=(("time", "lat", "lon"), gpp_h.astype(np.float32)),
             resp=(("time", "lat", "lon"), resp_h.astype(np.float32)),
             amplitude_scale=(("lat", "lon"), scale.astype(np.float32)),
             vegetated_fraction=diagnostic.vegetated_fraction),
        coords=dict(time=diagnostic.time, lat=diagnostic.lat, lon=diagnostic.lon))
    for name in ("gpp", "resp"):
        dataset[name].attrs.update(units="umol m-2 s-1")
    dataset.attrs.update(
        title="Hybrid biosphere prior",
        daily_mean="CarbonTracker CT-NRT.v2025-1 bio_flux_opt, which is assimilated",
        diurnal_shape="diagnostic: shortwave-driven uptake, Q10 respiration, so the phase cannot invert",
        diurnal_amplitude="CT-NRT, measured only on days when its own phase is correct",
        note="the daily mean is CarbonTracker's by construction; the phase is the diagnostic model's")
    destination = INPUTS / f"diagnostic_biosphere_{label}.nc"
    dataset.to_netcdf(destination)

    # validation: the three properties the construction promises
    combined = gpp_h + resp_h
    daily_error, phase_failures = [], 0
    for index, day in enumerate(unique_days):
        rows = days == day
        daily_error.append(np.abs(combined[rows].mean(axis=0) - ct_mean[index]).max())
        solar = np.repeat(local_solar_hour(stamps[rows], lon)[:, None, :], len(lat), axis=1)
        vegetated = diagnostic.vegetated_fraction.values > 0.2
        ok = phase_is_correct(combined[rows], solar)
        phase_failures += int((~ok & vegetated).sum())
    report = dict(
        label=label, output=str(destination),
        daily_mean_max_error=float(np.max(daily_error)),
        phase_failures_on_vegetated_cells=phase_failures,
        ct_phase_failures_on_vegetated_cells=int(((~correct) & (diagnostic.vegetated_fraction.values > 0.2)).sum()),
        amplitude_scale_median=float(np.median(scale)),
        amplitude_scale_range=[float(scale.min()), float(scale.max())],
        cells_keeping_diagnostic_amplitude=int((~enough).sum()))
    (OUT / f"biosphere_prior_{label}_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"hybrid biosphere written to {destination}", flush=True)
    print(f"  daily mean reproduces CarbonTracker to {report['daily_mean_max_error']:.2e} umol m-2 s-1", flush=True)
    print(f"  inverted-phase cell days: CT-NRT {report['ct_phase_failures_on_vegetated_cells']}, "
          f"hybrid {report['phase_failures_on_vegetated_cells']}", flush=True)
    print(f"  amplitude rescaling: median {report['amplitude_scale_median']:.2f}, "
          f"range {report['amplitude_scale_range'][0]:.2f} to {report['amplitude_scale_range'][1]:.2f}, "
          f"{report['cells_keeping_diagnostic_amplitude']} cells kept the diagnostic amplitude", flush=True)
    return report


def compare(label: str = "hybrid") -> pd.DataFrame:
    """The three priors at the tower cells, by local solar hour."""
    sources = {}
    with xr.open_dataset(INPUTS / "diagnostic_biosphere.nc") as ds:
        sources["diagnostic"] = (ds.gpp + ds.resp).load()
    with xr.open_dataset(INPUTS / f"diagnostic_biosphere_{label}.nc") as ds:
        sources[label] = (ds.gpp + ds.resp).load()
    with xr.open_dataset(C.INPUTS / "ctnrt_fluxes_box.nc") as ds:
        sources["ct-nrt"] = ds.bio_net.load()
    rows = []
    for code in ("BKT", "JMB"):
        _, lat, lon, _ = T.STATIONS[code]
        for name, field in sources.items():
            point = field.sel(lat=lat, lon=lon, method="nearest")
            stamps = pd.DatetimeIndex(point.time.values)
            solar = ((stamps.hour + lon / 15) % 24).astype(int)
            frame = pd.DataFrame(dict(solar=solar, value=point.values))
            median = frame.groupby("solar").value.median()
            rows.append(dict(station=code, prior=name,
                             afternoon=float(median.reindex(range(12, 16)).mean()),
                             night=float(median.reindex([22, 23, 0, 1, 2]).mean()),
                             amplitude=float(median.max() - median.min())))
    table = pd.DataFrame(rows)
    table.to_csv(OUT / f"biosphere_prior_{label}_comparison.csv", index=False)
    print(table.round(2).to_string(index=False), flush=True)
    return table


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["build", "compare"])
    parser.add_argument("--label", default="hybrid")
    a = parser.parse_args()
    build(a.label) if a.stage == "build" else compare(a.label)


if __name__ == "__main__":
    main()
