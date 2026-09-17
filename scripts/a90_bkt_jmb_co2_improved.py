#!/usr/bin/env python3
"""Improved CO2 model for the BKT + Jambi two-receptor inversion (builds on a89).

Two changes, each tested separately against the a89 daytime model:

1. An independent diagnostic biosphere prior instead of the CT-NRT optimized
   flux, which assimilates BKT flasks and has an inverted day-night cycle over
   both tower cells from 25 November to 1 December 2023. Gross uptake follows
   GFS downward shortwave radiation, ecosystem respiration follows GFS 2 m
   temperature with Q10 = 1.5 (the global value in the CarbonTracker
   documentation), on vegetated land from MODIS MCD12C1 2019 IGBP classes.
   A declared scale of 3,000 g C m-2 yr-1 on a fully vegetated cell sets the
   magnitude; uptake and respiration balance over the window in every cell.
   The inversion scales uptake and respiration separately.

   GFS ARL DSWF alternates 3 h means (stamps 03, 09, 15, 21 UTC) and 6 h means
   (00, 06, 12, 18 UTC) over the preceding interval; the 3 h mean ending at a
   6-hourly stamp is 2 v(t) - v(t - 3 h). The build fails if de-accumulated
   night radiation is not near zero.

2. Afternoon observation means: each 06 UTC (13 WIB) receptor uses the mean of
   the valid 05, 06 and 07 UTC hours (at least two), after an hourly CO2-only
   spike screen against the median of the four neighbouring hours, instead of
   the single 06 UTC hour.

Stages
  biosphere     build the diagnostic biosphere prior on the GFS 0.25 degree grid
  observations  afternoon CO2 means with the hourly spike screen
  operator      hourly footprint convolution with the diagnostic prior
  inversion     fits: CT-NRT and diagnostic biosphere, 1 h and 3 h observations
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
import xarray as xr

import a71_domain_budget_extension as ext
import a84_bkt_jmb_two_receptor as T
import a89_bkt_jmb_co2 as C
from a43_bkt_source_analysis import save_nc
from bkt_arl import ARLReader

TABLES = T.TABLES
INPUTS = C.INPUTS
LANDCOVER = T.ROOT / "data/bkt_sources/landcover/MCD12C1_2019_IGBP_majority_0p05deg.tif"
VEGETATED_CLASSES = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14)   # IGBP; 0 water, 13 urban, 15 snow, 16 barren
GPP_REF_GC_M2_YR = 3000.
GPP_REF_UMOL = GPP_REF_GC_M2_YR / 12.011 / (365.25 * 86400) * 1e6   # umol CO2 m-2 s-1
Q10 = 1.5
AFTERNOON_HOURS_UTC = (5, 6, 7)
MIN_MIXING_DEPTH_M = 300.   # well-mixed screen: native GFS mixing depth at the receptor cell
DIAG = ["fossil_near", "fossil_far", "gpp", "resp"]
NAMES = {"fossil_near": "Fossil ≤500 km", "fossil_far": "Fossil >500 km", "gpp": "Gross uptake", "resp": "Ecosystem respiration",
         "bio_day": "CT-NRT biosphere, daytime", "bio_night": "CT-NRT biosphere, nighttime"}


# ------------------------------------------------------------------ helpers

def deaccumulate(values: np.ndarray, stamps: pd.DatetimeIndex) -> np.ndarray:
    """3 h interval means ending at each stamp from alternating 3 h and 6 h GFS means."""
    out = np.full(values.shape, np.nan, dtype=float)
    for i, stamp in enumerate(stamps):
        if stamp.hour % 6 == 3:
            out[i] = values[i]
        elif i > 0 and stamps[i - 1] == stamp - pd.Timedelta(hours=3):
            out[i] = 2 * values[i] - values[i - 1]
    return out


def interval_end(hours) -> pd.DatetimeIndex:
    """End stamp of the 3 h radiation interval containing each footprint hour start."""
    return pd.DatetimeIndex(hours).floor("3h") + pd.Timedelta(hours=3)


def temperature_weights(hours, stamps: pd.DatetimeIndex) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Linear interpolation at the hour midpoint between the bracketing 3-hourly stamps."""
    mid = pd.DatetimeIndex(hours) + pd.Timedelta(minutes=30)
    lower = mid.floor("3h")
    i0 = stamps.get_indexer(lower); i1 = stamps.get_indexer(lower + pd.Timedelta(hours=3))
    w1 = ((mid - lower) / pd.Timedelta(hours=3)).to_numpy(float)
    return i0, i1, w1


def fraction_on_grid(mask: np.ndarray, src_lat: np.ndarray, src_lon: np.ndarray, lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    """Area-weighted mean of a 0/1 mask on a coarser regular grid (ascending axes)."""
    m_lat, m_lon = C.overlap_matrix(src_lat, lat, True), C.overlap_matrix(src_lon, lon)
    hits = m_lat @ mask.astype(float) @ m_lon.T
    total = m_lat @ np.ones(mask.shape) @ m_lon.T
    return np.divide(hits, total, out=np.zeros_like(hits), where=total > 0)


def biosphere_fields(sw: np.ndarray, temperature_k: np.ndarray, vegetated: np.ndarray,
                     q10: float = Q10, k_light: float | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Gross uptake (negative) and respiration (positive), balanced over the time axis in every cell.

    Uptake is linear in shortwave radiation, or saturating as sw / (sw + k_light) when k_light is given.
    """
    scale = vegetated * GPP_REF_UMOL
    light = sw if k_light is None else sw / (sw + k_light)
    light_mean = light.mean(axis=0)
    gpp = -scale[None] * np.divide(light, light_mean[None], out=np.zeros_like(light), where=light_mean[None] > 0)
    q = q10 ** ((temperature_k - temperature_k.mean(axis=0)[None]) / 10)
    resp = scale[None] * q / q.mean(axis=0)[None]
    return gpp, resp


def solar_hour(stamps: pd.DatetimeIndex, lon: np.ndarray, offset_hours: float = 0.) -> np.ndarray:
    t = stamps + pd.Timedelta(hours=offset_hours)
    return (t.hour.values[:, None] + t.minute.values[:, None] / 60 + lon[None, :] / 15) % 24


# ------------------------------------------------------------------ biosphere

def build_biosphere(variant: str = "", q10: float = Q10, k_light: float | None = None,
                    days=None, met_dir=None) -> None:
    INPUTS.mkdir(parents=True, exist_ok=True)
    stamps, dswf, t2m, lat, lon = [], [], [], None, None
    for day in (C.FLUX_DAYS if days is None else days):
        reader = ARLReader((T.MET if met_dir is None else met_dir) / f"{day:%Y%m%d}_gfs0p25")
        lat, lon = reader.lat, reader.lon
        for stamp in reader.times:
            stamps.append(stamp)
            dswf.append(reader.field(stamp, "DSWF", 0).astype(np.float32))
            t2m.append(reader.field(stamp, "T02M", 0).astype(np.float32))
    stamps = pd.DatetimeIndex(stamps)
    if not (np.diff(stamps.asi8) == 3 * 3600 * 10 ** 9).all():
        raise ValueError("GFS stamps are not a continuous 3-hourly series")
    sw = np.clip(deaccumulate(np.asarray(dswf), stamps), 0, None)
    temperature = np.asarray(t2m, dtype=float)
    keep = ~np.isnan(sw).any(axis=(1, 2))   # the first stamp has no predecessor
    stamps, sw, temperature = stamps[keep], sw[keep], temperature[keep]
    with rasterio.open(LANDCOVER) as src:
        window = src.window(lon[0] - 1, lat[0] - 1, lon[-1] + 1, lat[-1] + 1)
        classes = src.read(1, window=window)
        transform = src.window_transform(window)
    src_lon = transform.c + (np.arange(classes.shape[1]) + .5) * transform.a
    src_lat = transform.f + (np.arange(classes.shape[0]) + .5) * transform.e
    order = np.argsort(src_lat)
    vegetated_mask = np.isin(classes, VEGETATED_CLASSES)[order]
    vegetated = fraction_on_grid(vegetated_mask, src_lat[order], src_lon, lat, lon)
    # interval center solar time for radiation; land cells only
    land = vegetated > .5
    solar = solar_hour(stamps, lon, -1.5)[:, None, :].repeat(len(lat), axis=1)
    night = (solar >= 20) | (solar < 4)
    night_sw = float(sw[night & land[None]].mean()); day_sw = float(sw[(solar >= 10) & (solar < 14) & land[None]].mean())
    print(f"de-accumulated DSWF over vegetated land: night {night_sw:.2f} W m-2, 10-14 local solar {day_sw:.1f} W m-2", flush=True)
    if night_sw > 5 or day_sw < 150:
        raise ValueError("De-accumulated radiation does not follow the solar cycle; the averaging assumption is wrong")
    gpp, resp = biosphere_fields(sw, temperature, vegetated, q10, k_light)
    imbalance = float(np.abs(gpp.mean(axis=0) + resp.mean(axis=0)).max())
    if imbalance > 1e-6 * GPP_REF_UMOL:
        raise ValueError(f"Uptake and respiration do not balance: {imbalance}")
    ds = xr.Dataset({"gpp": (("time", "lat", "lon"), gpp.astype(np.float32)), "resp": (("time", "lat", "lon"), resp.astype(np.float32)),
                     "vegetated_fraction": (("lat", "lon"), vegetated.astype(np.float32))},
                    coords={"time": stamps, "lat": lat, "lon": lon})
    ds.gpp.attrs.update(units="umol m-2 s-1", meaning="mean over the 3 h interval ending at the time stamp; negative is uptake")
    ds.resp.attrs.update(units="umol m-2 s-1", meaning="at the time stamp; interpolate linearly to intermediate hours")
    ds.attrs.update(gpp_ref_gC_m2_yr=GPP_REF_GC_M2_YR, q10=q10, k_light_W_m2=str(k_light), landcover="MODIS MCD12C1 2019 IGBP majority", meteorology="GFS 0.25 ARL DSWF and T02M")
    ds.to_netcdf(INPUTS / f"diagnostic_biosphere{variant}.nc", encoding={v: {"zlib": True, "complevel": 4} for v in ("gpp", "resp")})
    rows = [dict(quantity="de-accumulated DSWF, vegetated land, local solar night (W m-2)", value=night_sw),
            dict(quantity="de-accumulated DSWF, vegetated land, 10-14 local solar (W m-2)", value=day_sw),
            dict(quantity="gross uptake scale on a fully vegetated cell (umol m-2 s-1)", value=GPP_REF_UMOL),
            dict(quantity="maximum window-mean imbalance (umol m-2 s-1)", value=imbalance)]
    for code in T.STATIONS:
        _, la, lo, _ = T.STATIONS[code]
        i, j = np.argmin(abs(lat - la)), np.argmin(abs(lon - lo))
        cell_solar = solar_hour(stamps, np.array([lon[j]]), -1.5)[:, 0]
        nee = gpp[:, i, j] + np.interp(np.arange(len(stamps)) - .5, np.arange(len(stamps)), resp[:, i, j])
        rows += [dict(quantity=f"{code} cell vegetated fraction", value=float(vegetated[i, j])),
                 dict(quantity=f"{code} cell mean NEE 10-14 local solar (umol m-2 s-1)", value=float(nee[(cell_solar >= 10) & (cell_solar < 14)].mean())),
                 dict(quantity=f"{code} cell mean NEE 20-04 local solar (umol m-2 s-1)", value=float(nee[(cell_solar >= 20) | (cell_solar < 4)].mean()))]
    pd.DataFrame(rows).to_csv(TABLES / f"co2_diagnostic_biosphere_summary{variant}.csv", index=False)
    print(pd.DataFrame(rows).round(3).to_string(index=False), flush=True)


# ------------------------------------------------------------------ observations

def hourly_spikes(record: pd.DataFrame) -> pd.Series:
    """Hourly CO2-only spike flag on a continuous hourly index.

    Departure is the value minus the median of the four neighbouring hours
    (t-2, t-1, t+1, t+2; at least three present), so one spike does not flag its
    clean neighbours. Flagged when |dCO2| > 20 ppm while |dCH4| and |dCO| < 20 ppb.
    """
    dep, enough = {}, []
    for sp in ("co2", "ch4", "co"):
        neighbours = pd.concat([record[sp].shift(s) for s in (2, 1, -1, -2)], axis=1)
        dep[sp] = record[sp] - neighbours.median(axis=1, skipna=True)
        enough.append(record[sp].notna() & (neighbours.notna().sum(axis=1) >= 3))
    testable = enough[0] & enough[1] & enough[2]
    return testable & (dep["co2"].abs() > C.SPIKE_CO2_PPM) & (dep["ch4"].abs() < C.SPIKE_TRACER_PPB) & (dep["co"].abs() < C.SPIKE_TRACER_PPB)


def observations() -> pd.DataFrame:
    import ghg_common as G
    base = pd.read_csv(TABLES / "co2_operator_base.csv", parse_dates=["time_utc"])
    rows = []
    for code in T.STATIONS:
        raw = G.apply_flags(G.load_station(code)).set_index("time_utc").sort_index()
        index = pd.date_range(T.WINDOW[0] - pd.Timedelta(days=1), T.WINDOW[1] + pd.Timedelta(days=1), freq="h")
        record = raw.reindex(index)
        spike = hourly_spikes(record)
        valid = record.co2.notna() & ~record.suspect_co2.eq(True) & ~spike
        for stamp in base.loc[base.station.eq(code), "time_utc"]:
            row = dict(station=code, time_utc=stamp, co2_1h=record.co2.get(stamp), co2_1h_spike=bool(spike.get(stamp, False)))
            if stamp.hour == 6:
                hours = [stamp.normalize() + pd.Timedelta(hours=h) for h in AFTERNOON_HOURS_UTC]
                ok = [h for h in hours if valid.get(h, False)]
                row.update(afternoon_valid_hours=len(ok), co2_afternoon_mean=float(record.co2[ok].mean()) if len(ok) >= 2 else np.nan,
                           afternoon_spikes=int(sum(bool(spike.get(h, False)) for h in hours)))
            rows.append(row)
    table = pd.DataFrame(rows)
    table.to_csv(TABLES / "co2_afternoon_observations.csv", index=False)
    day = table[table.time_utc.dt.hour.eq(6)]
    print(day.groupby("station").agg(receptors=("time_utc", "size"), with_mean=("co2_afternoon_mean", lambda s: int(s.notna().sum())),
                                      spike_hours=("afternoon_spikes", "sum")).to_string(), flush=True)
    return table


# ------------------------------------------------------------------ operator

def operator(variant: str = "") -> None:
    base = pd.read_csv(TABLES / "co2_operator_base.csv", parse_dates=["time_utc"])
    with xr.open_dataset(INPUTS / f"diagnostic_biosphere{variant}.nc") as ds:
        gpp = ds.gpp.values; resp = ds.resp.values; blat = ds.lat.values; blon = ds.lon.values
        stamps = pd.DatetimeIndex(ds.time.values)
    rows = []
    for code in T.STATIONS:
        lat, lon = T.receptor_grid(code)
        m_lat, m_lon = C.overlap_matrix(lat, blat, True), C.overlap_matrix(lon, blon)
        if not (np.allclose(m_lat.sum(axis=0), 1) and np.allclose(m_lon.sum(axis=0), 1)):
            raise ValueError("The GFS grid does not contain the footprint grid")
        for stamp in sorted(base.loc[base.station.eq(code), "time_utc"]):
            members = []
            for seed in T.SEEDS:
                directory = T.run_dir(code, seed, stamp)
                field, meta, actual = ext.read_footprint(directory)
                hours = pd.DatetimeIndex(field.time.values)
                coarse = C.aggregate(field.values.astype(np.float32), m_lat.astype(np.float32), m_lon.astype(np.float32))
                idx = stamps.get_indexer(interval_end(hours))
                i0, i1, w1 = temperature_weights(hours, stamps)
                if (idx < 0).any() or (i0 < 0).any() or (i1 < 0).any():
                    raise ValueError(f"Footprint hours outside the biosphere prior: {code} {stamp}")
                resp_h = (1 - w1)[:, None, None] * resp[i0] + w1[:, None, None] * resp[i1]
                members.append(dict(seed=seed, gpp_ppm=float(np.einsum("hij,hij->", coarse, gpp[idx])),
                                    resp_ppm=float(np.einsum("hij,hij->", coarse, resp_h))))
            m = pd.DataFrame(members)
            rows.append(dict(station=code, time_utc=stamp, gpp_ppm=m.gpp_ppm.mean(), resp_ppm=m.resp_ppm.mean(),
                             gpp_ppm_seed_sd=m.gpp_ppm.std(ddof=1), resp_ppm_seed_sd=m.resp_ppm.std(ddof=1)))
        print(f"diagnostic biosphere operator {code} done", flush=True)
    pd.DataFrame(rows).to_csv(TABLES / f"co2_diagnostic_operator{variant}.csv", index=False)


# ------------------------------------------------------------------ inversion

def skill(label: str, predictions: pd.DataFrame) -> list[dict]:
    rows = []
    for code, g in predictions.groupby("station"):
        for model, col in (("posterior", "posterior_median_ppm"), ("background_only", "background_only_ppm"), ("prior", "prior_ppm")):
            e = g[col] - g.observed_ppm
            rows.append(dict(case=label, station=code, model=model, n=len(g), rmse_ppm=float(np.sqrt((e ** 2).mean())), bias_ppm=float(e.mean()),
                             correlation=float(np.corrcoef(g.observed_ppm, g[col])[0, 1]) if g[col].std() > 0 else np.nan))
    return rows


def leave_one_out(frame: pd.DataFrame, train: np.ndarray, components: list[str], obs: str, transport: float) -> pd.DataFrame:
    k, b, base, names = C.design(frame, components)
    y = frame[obs].to_numpy() - base
    sd = np.r_[np.repeat(np.log(C.MULTIPLIER_PRIOR_FACTOR), k.shape[1]), np.tile([C.OFFSET_PRIOR_PPM, C.TREND_PRIOR_PPM], b.shape[1] // 2)]
    r = C.covariance(frame, k, transport)
    def mapfit(mask):
        theta, _, _ = C.SignedInverseProblem(k[mask], b[mask], y[mask], r[np.ix_(mask, mask)], sd).fit()
        return np.exp(theta[:k.shape[1]])
    rows = [dict(dropped="none", **dict(zip(components, mapfit(train))))]
    for i in np.flatnonzero(train):
        mask = train.copy(); mask[i] = False
        rows.append(dict(dropped=f"{frame.station[i]} {frame.time_utc[i]:%Y-%m-%dT%H}", **dict(zip(components, mapfit(mask)))))
    return pd.DataFrame(rows)


def inversion() -> None:
    base = pd.read_csv(TABLES / "co2_operator_base.csv", parse_dates=["time_utc"])
    diag = pd.read_csv(TABLES / "co2_diagnostic_operator.csv", parse_dates=["time_utc"])
    obs = pd.read_csv(TABLES / "co2_afternoon_observations.csv", parse_dates=["time_utc"])
    frame = base.merge(diag, on=["station", "time_utc"], validate="one_to_one").merge(obs, on=["station", "time_utc"], validate="one_to_one")
    frame = frame[frame.transport_usable & frame.time_utc.dt.hour.eq(6)].reset_index(drop=True)
    one_hour = frame[frame.co2.notna() & ~frame.co2_1h_spike].reset_index(drop=True)
    three_hour = frame[frame.co2_afternoon_mean.notna()].reset_index(drop=True)
    mixed = three_hour[three_hour.PBLH >= MIN_MIXING_DEPTH_M].reset_index(drop=True)
    pd.DataFrame(dict(station=three_hour.station, time_utc=three_hour.time_utc, pblh_m=three_hour.PBLH,
                      well_mixed=three_hour.PBLH >= MIN_MIXING_DEPTH_M)).to_csv(TABLES / "co2_mixing_screen.csv", index=False)
    print("receptors below the mixing-depth screen:", three_hour.loc[three_hour.PBLH < MIN_MIXING_DEPTH_M, ["station", "time_utc", "PBLH"]].to_string(index=False), flush=True)
    def masks(f, kind):
        hold = f.holdout.to_numpy(bool); bkt = f.station.eq("BKT").to_numpy(); jmb = ~bkt
        return {"joint": (~hold, hold), "bkt_only": (bkt & ~hold, bkt & hold), "jmb_only": (jmb & ~hold, jmb & hold),
                "bkt_to_jmb": (bkt & ~hold, jmb)}[kind]
    cases = [("ctnrt_1h", one_hour, C.COMPONENTS, "co2", "joint"), ("ctnrt_3h", three_hour, C.COMPONENTS, "co2_afternoon_mean", "joint"),
             ("diag_1h", one_hour, DIAG, "co2", "joint"), ("diag_3h", three_hour, DIAG, "co2_afternoon_mean", "joint"),
             ("diag_3h_bkt_only", three_hour, DIAG, "co2_afternoon_mean", "bkt_only"), ("diag_3h_jmb_only", three_hour, DIAG, "co2_afternoon_mean", "jmb_only"),
             ("diag_3h_bkt_to_jmb", three_hour, DIAG, "co2_afternoon_mean", "bkt_to_jmb"),
             ("ctnrt_3h_mixed", mixed, C.COMPONENTS, "co2_afternoon_mean", "joint"), ("diag_3h_mixed", mixed, DIAG, "co2_afternoon_mean", "joint"),
             ("diag_3h_mixed_bkt_only", mixed, DIAG, "co2_afternoon_mean", "bkt_only"), ("diag_3h_mixed_bkt_to_jmb", mixed, DIAG, "co2_afternoon_mean", "bkt_to_jmb")]
    params, evals, skills, preds, loo = [], [], [], [], None
    for label, f, components, column, kind in cases:
        train, evaluate = masks(f, kind)
        if train.sum() < 8:
            print(f"skip {label}: {int(train.sum())} training hours", flush=True); continue
        result = C.fit(label, f, train, evaluate, components, column)
        params += result["params"]; evals += result["evals"]; preds.append(result["predictions"])
        skills += skill(label, result["predictions"] if kind != "bkt_to_jmb" else result["predictions"][f.station.eq("JMB").to_numpy()])
        if kind == "bkt_only":
            skills[:] = [row for row in skills if not (row["case"] == label and row["station"] == "JMB")]
        print(label, "training hours", int(train.sum()), "transport fraction", round(result["params"][0]["transport_fraction"], 3), flush=True)
        if label == "diag_3h":
            loo = leave_one_out(f, train, components, column, result["params"][0]["transport_fraction"])
    pd.DataFrame(params).to_csv(TABLES / "co2_improved_parameters.csv", index=False)
    pd.DataFrame(evals).to_csv(TABLES / "co2_improved_evaluation.csv", index=False)
    pd.DataFrame(skills).to_csv(TABLES / "co2_improved_skill.csv", index=False)
    pd.concat(preds).to_csv(TABLES / "co2_improved_predictions.csv", index=False)
    loo.to_csv(TABLES / "co2_improved_leave_one_out.csv", index=False)
    pd.set_option("display.width", 250)
    P = pd.DataFrame(params)
    print(P[~P.parameter.str.startswith(("offset", "trend"))][["case", "parameter", "median", "q025", "q975", "variance_reduction_percent"]].round(3).to_string(index=False))
    print(pd.DataFrame(skills).pivot_table(index=["case", "station"], columns="model", values=["rmse_ppm", "correlation"]).round(2).to_string())
    E = pd.DataFrame(evals)
    print(E[E.split.eq("evaluation")].pivot_table(index=["case", "station"], columns="model", values="rmse_ppm").round(2).to_string())
    print("leave-one-out ranges diag_3h:", {c: (round(loo[c][1:].min(), 2), round(loo[c][1:].max(), 2)) for c in DIAG})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["biosphere", "observations", "operator", "inversion", "all"])
    stage = parser.parse_args().stage
    for name, fn in (("biosphere", build_biosphere), ("observations", observations), ("operator", operator), ("inversion", inversion)):
        if stage in (name, "all"):
            fn()


if __name__ == "__main__":
    main()
