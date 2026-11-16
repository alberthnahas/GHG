#!/usr/bin/env python3
"""Validate the a148 MBL curtain against CarbonTracker, CAMS, NOAA sites and the BKT tower.

Sections (all read-only on existing outputs; new files in outputs/background/)
  receptors  curtain at the active endpoints vs the CarbonTracker boundary already in the
             operator tables (CO2: CT-NRT.v2025-1 Nov-Dec 2023 and Oct-Dec 2024, CT2026 2025;
             CH4: CT-CH4-2025 Nov-Dec 2023), plus BKT Sep-Oct 2019 (CT-CH4-2025 per particle,
             and CT2022 CO2 sampled here at the same endpoints, as a89.endpoint_background but
             with the CarbonTracker surface height instead of ARL terrain)
  inflow     CarbonTracker fields on disk, no footprints: each field sampled at the station's
             calendar-month endpoint cloud (3000 terminal endpoints drawn from all a147 runs),
             compared with the curtain at the same latitudes and time; 2019 to 2025 (CO2),
             2019 to 2023 (CH4)
  release    CT2026 vs CT-NRT.v2025-1 on the same days of 2024 over the inflow regions
  hindcast   the 2026 extension replayed with cutoffs 1 Jan 2015 to 1 Jan 2025, global
             mean available to Jul (CO2) or Jun (CH4) of the target year, as in Nov 2026
  cams       CAMS global GHG forecast (15th of each month, 00 UTC, lead 0) at the same
             endpoint clouds, 2024-03 to 2026-11, vs the curtain (2026 = extension)
  tower      BKT afternoon (12-16 LT) monthly 10th percentile and NOAA BKT flask monthly
             means vs the general function at BKT
  figures    one 300 dpi PNG per gas
Times UTC.  Differences are always curtain minus comparison.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import a148_background_curtain as B  # noqa: E402

ROOT = B.ROOT
OUT = B.OUT
SRC = ROOT / "data/bkt_sources"
BG = SRC / "background"
POOL_N = 3000
RNG = np.random.default_rng(20261115)
MW_AIR, MW = 28.9644, {"co2": 44.0095, "ch4": 16.0425}
SCALE = {"co2": 1e6, "ch4": 1e9}
GLOBAL_LAG = {"co2": 7 / 12, "ch4": 6 / 12}  # months of the target year with a global mean, as of Nov 2026


# ------------------------------------------------------------------ CT sampling
def ct_sample(path: Path, gas: str, when: pd.Timestamp | None, lat, lon, agl) -> np.ndarray:
    """CarbonTracker value at particles; height above the model surface (gph lower boundary)."""
    with xr.open_dataset(path) as d:
        if d.sizes["time"] > 1:
            d = d.sel(time=when, method="nearest")
        else:
            d = d.isel(time=0)
        s = d[[gas, "gph"]].interp(latitude=xr.DataArray(lat, dims="p"), longitude=xr.DataArray(lon, dims="p")).load()
    bounds = s.gph.transpose("p", "boundary").values
    centers = (bounds[:, :-1] + bounds[:, 1:]) / 2
    values = s[gas].transpose("p", "level").values
    z = bounds[:, 0] + agl
    return np.asarray([np.interp(zi, h, c) for zi, h, c in zip(z, centers, values)])


def pool(station: str, month: int) -> pd.DataFrame:
    pts = B.endpoints()
    p = pts[(pts.station == station) & (pts.time_utc.dt.month == month)]
    return p.iloc[RNG.choice(len(p), size=min(POOL_N, len(p)), replace=False)]


# ------------------------------------------------------------------ receptors
def receptors() -> pd.DataFrame:
    ops = pd.read_csv(OUT / "background_operator_rows.csv", parse_dates=["time_utc", "endpoint_utc"], dtype={"campaign": str})
    ops = ops[ops.ct_gas.isin(["co2", "ch4"])].copy()
    labels = {"co2_operator_base.csv": "CT-NRT.v2025-1", "co2_operator_base_2024.csv": "CT-NRT.v2025-1",
              "co2_operator_2025.csv": "CT2026", "operator_base.csv": "CT-CH4-2025"}
    rows = [pd.DataFrame(dict(gas=ops.ct_gas, station=ops.station, time_utc=ops.time_utc, period=ops.campaign,
                              ct_release=ops.operator_table.map(labels), ct=ops.ct_background,
                              curtain=np.where(ops.ct_gas == "co2", ops.co2_mbl_endpoint, ops.ch4_mbl_endpoint),
                              curtain_climatology=np.where(ops.ct_gas == "co2", ops.co2_mbl_climatology, ops.ch4_mbl_climatology),
                              above3km_fraction=ops.above3km_fraction, south_fraction=ops.south_fraction,
                              lat_mean=ops.lat_mean, lon_mean=ops.lon_mean))]
    rec = pd.read_csv(OUT / "mbl_curtain_receptors.csv", parse_dates=["time_utc", "endpoint_utc"], dtype={"campaign": str})
    r19 = rec[rec.campaign == "2019"]
    rows.append(pd.DataFrame(dict(gas="ch4", station="BKT", time_utc=r19.time_utc, period="2019", ct_release="CT-CH4-2025",
                                  ct=r19.ct_ch4_from_endpoints, curtain=r19.ch4_mbl_endpoint, curtain_climatology=r19.ch4_mbl_climatology,
                                  above3km_fraction=r19.above3km_fraction, south_fraction=r19.south_fraction,
                                  lat_mean=r19.lat_mean, lon_mean=r19.lon_mean)))
    pts = B.endpoints()
    p19 = pts[pts.campaign == "2019"]
    co2_19 = []
    for stamp, g in p19.groupby("time_utc"):
        end = g.endpoint_utc.iloc[0]
        path = SRC / "inversion/carbontracker_co2" / f"CT2022.molefrac_glb3x2_{end:%Y-%m-%d}.nc"
        if not path.exists():
            continue
        ct = ct_sample(path, "co2", end, g.latitude.values, g.longitude.values, g.height_agl_m.values)
        rr = r19[r19.time_utc == stamp].iloc[0]
        co2_19.append(dict(gas="co2", station="BKT", time_utc=stamp, period="2019", ct_release="CT2022", ct=float(ct.mean()),
                           curtain=rr.co2_mbl_endpoint, curtain_climatology=rr.co2_mbl_climatology,
                           above3km_fraction=rr.above3km_fraction, south_fraction=rr.south_fraction,
                           lat_mean=rr.lat_mean, lon_mean=rr.lon_mean))
    rows.append(pd.DataFrame(co2_19))
    table = pd.concat(rows, ignore_index=True)
    table["diff"] = table.curtain - table.ct
    table["diff_climatology"] = table.curtain_climatology - table.ct
    table.to_csv(OUT / "validation_receptor_rows.csv", index=False, float_format="%.4f")
    stats = []
    for (gas, period, release, station), g in table.groupby(["gas", "period", "ct_release", "station"]):
        stats.append(summary(g, gas=gas, period=period, ct_release=release, station=station))
    for (gas, station), g in table.groupby(["gas", "station"]):
        stats.append(summary(g, gas=gas, period="all", ct_release="all", station=station))
    s = pd.DataFrame(stats)
    s.to_csv(OUT / "validation_receptor_stats.csv", index=False, float_format="%.4f")
    monthly = table.assign(month=table.time_utc.dt.to_period("M").astype(str)).groupby(
        ["gas", "station", "ct_release", "month"]).agg(n=("diff", "size"), curtain=("curtain", "mean"), ct=("ct", "mean"),
                                                       diff=("diff", "mean"), diff_sd=("diff", "std")).reset_index()
    monthly.to_csv(OUT / "validation_receptor_monthly.csv", index=False, float_format="%.4f")
    print(s.to_string(), flush=True)
    return table


def summary(g: pd.DataFrame, col: str = "diff", **keys) -> dict:
    d = g[col]
    out = dict(**keys, n=len(g), bias=d.mean(), sd=d.std(), rmse=float(np.sqrt((d ** 2).mean())),
               r=float(np.corrcoef(g.curtain, g.ct)[0, 1]) if len(g) > 2 else np.nan,
               ct_sd=g.ct.std(), curtain_sd=g.curtain.std())
    if "diff_climatology" in g:
        out.update(bias_climatology=g.diff_climatology.mean(), sd_climatology=g.diff_climatology.std())
    if len(g) > 10 and "above3km_fraction" in g:
        X = np.column_stack([np.ones(len(g)), g.above3km_fraction, g.south_fraction])
        coef, *_ = np.linalg.lstsq(X, d.values, rcond=None)
        out.update(slope_above3km=coef[1], slope_south_fraction=coef[2])
    return out


# ------------------------------------------------------------------ inflow
def ct_fields() -> list[tuple[str, str, Path, pd.Timestamp]]:
    """(gas, release, path, time) for CarbonTracker fields on disk, thinned to limit CPU."""
    out = []
    for p in sorted((BG / "ct_nrt_monthly").glob("*.nc")):
        out.append(("co2", "CT-NRT.v2025-1 monthly", p, pd.Timestamp(p.stem.split("_")[-1] + "-16")))
    def daily(glob, gas, release, every, hour="6h"):
        files = sorted(glob)
        for p in files[::every]:
            day = pd.Timestamp(p.stem.split("_")[-1])
            out.append((gas, release, p, day + pd.Timedelta(hour)))
    daily((SRC / "carbontracker_nrt/molefractions").glob("CT-NRT.v2025-1.molefrac_glb3x2_*.nc"), "co2", "CT-NRT.v2025-1 daily", 3)
    daily((SRC / "carbontracker_ct2026/molefractions").glob("CT2026.molefrac_glb3x2_*.nc"), "co2", "CT2026 daily", 3)
    daily((BG / "ct2026_sample").glob("*.nc"), "co2", "CT2026 daily", 1)
    daily((SRC / "inversion/carbontracker_co2").glob("*.nc"), "co2", "CT2022 daily", 3)
    daily((SRC / "inversion/carbontracker").glob("CTCH4_2025*.nc"), "ch4", "CT-CH4-2025 daily", 3)
    daily((BG / "ctch4_sample").glob("*.nc"), "ch4", "CT-CH4-2025 daily", 1)
    return out


def inflow() -> pd.DataFrame:
    pools = {(s, m): pool(s, m) for s in B.STATION_LAT for m in range(1, 13)}
    rows = []
    for gas, release, path, when in ct_fields():
        for station in B.STATION_LAT:
            p = pools[(station, when.month)]
            ct = ct_sample(path, gas, when, p.latitude.values, p.longitude.values, p.height_agl_m.values)
            curt = float(B.background(gas, [when], latitudes=p.latitude.values)[0])
            rows.append(dict(gas=gas, ct_release=release, station=station, time=when, ct=float(ct.mean()),
                             curtain=curt, diff=curt - float(ct.mean()), file=path.name))
        print(gas, release, when.date(), f"{rows[-1]['diff']:.2f}", flush=True)
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "validation_inflow_ct.csv", index=False, float_format="%.4f")
    s = table.groupby(["gas", "ct_release", "station"]).agg(n=("diff", "size"), first=("time", "min"), last=("time", "max"),
                                                            bias=("diff", "mean"), sd=("diff", "std")).reset_index()
    s.to_csv(OUT / "validation_inflow_ct_stats.csv", index=False, float_format="%.4f")
    print(s.to_string(), flush=True)
    return table


def release() -> pd.DataFrame:
    regions = {"South China Sea 5-15N 105-120E": (5, 15, 105, 120), "N Indian Ocean 0-10N 70-90E": (0, 10, 70, 90),
               "S Indian Ocean 15-5S 70-100E": (-15, -5, 70, 100), "W Pacific 5-15N 150-180E": (5, 15, 150, 180),
               "Sumatra 6S-6N 95-106E": (-6, 6, 95, 106)}
    rows = []
    nrt_dir = SRC / "carbontracker_nrt/molefractions"
    for p in sorted((BG / "ct2026_sample").glob("*.nc")):
        day = pd.Timestamp(p.stem.split("_")[-1])
        q = BG / "ct_nrt_monthly" / f"CT-NRT.v2025-1.molefrac_glb3x2_{day:%Y-%m}.nc"
        daily = nrt_dir / f"CT-NRT.v2025-1.molefrac_glb3x2_{day:%Y-%m-%d}.nc"
        with xr.open_dataset(p) as a:
            new = a.co2.isel(level=slice(0, 8)).mean("time").load()
        refs = [("CT-NRT monthly mean", q)] + ([("CT-NRT same day", daily)] if daily.exists() else [])
        for label, path in refs:
            if not path.exists():
                continue
            with xr.open_dataset(path) as b:
                old = b.co2.isel(level=slice(0, 8)).mean("time").load()
            for name, (la, lb, oa, ob) in regions.items():
                box = dict(latitude=slice(la, lb), longitude=slice(oa, ob))
                rows.append(dict(day=day.date(), reference=label, region=name,
                                 ct2026_ppm=float(new.sel(**box).mean()), ctnrt_ppm=float(old.sel(**box).mean()),
                                 ct2026_minus_ctnrt_ppm=float(new.sel(**box).mean() - old.sel(**box).mean())))
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "ct_release_comparison.csv", index=False, float_format="%.3f")
    print(table.to_string(), flush=True)
    return table


# ------------------------------------------------------------------ hindcast
def hindcast() -> pd.DataFrame:
    rows = []
    days = None
    for gas in B.GASES:
        final = B.curtain(gas)
        for year in range(2015, 2026):
            cutoff = float(year)
            for variant in ("trend_only", "trend_resid", "global_anchor"):
                c = B.Curtain(gas, cutoff=cutoff, variant=variant, global_until=year + GLOBAL_LAG[gas])
                days = pd.date_range(f"{year}-01-04", f"{year}-11-30", freq="7D")
                for station in B.STATION_LAT:
                    est = B.background(gas, days, station, curtain_obj=c)
                    ref = B.background(gas, days, station, curtain_obj=final)
                    rows.append(pd.DataFrame(dict(gas=gas, year=year, variant=variant, station=station, time=days,
                                                  lead_month=days.month, error=est - ref)))
    table = pd.concat(rows, ignore_index=True)
    table.to_csv(OUT / "hindcast_extension_weekly.csv", index=False, float_format="%.4f")
    s = table.groupby(["gas", "variant", "station", "lead_month"]).error.agg(
        bias="mean", sd="std", rmse=lambda e: float(np.sqrt((e ** 2).mean()))).reset_index()
    s.to_csv(OUT / "hindcast_extension_by_lead.csv", index=False, float_format="%.4f")
    y = table.groupby(["gas", "variant", "year"]).error.agg(bias="mean", rmse=lambda e: float(np.sqrt((e ** 2).mean()))).reset_index()
    y.to_csv(OUT / "hindcast_extension_by_year.csv", index=False, float_format="%.4f")
    tot = table.groupby(["gas", "variant"]).error.agg(bias="mean", sd="std", rmse=lambda e: float(np.sqrt((e ** 2).mean())),
                                                       max_abs=lambda e: float(e.abs().max())).reset_index()
    tot.to_csv(OUT / "hindcast_extension_summary.csv", index=False, float_format="%.4f")
    print(tot.to_string(), flush=True)
    return table


# ------------------------------------------------------------------ cams
def cams() -> pd.DataFrame:
    files = sorted((BG / "cams_ghg_forecast").glob("*.grib"))
    rows = []
    for path in files:
        day = pd.Timestamp(path.name.split("_")[3][:8])
        when = day  # 00 UTC analysis time, lead 0
        ds = xr.open_dataset(path, engine="cfgrib", backend_kwargs=dict(indexpath=""))
        for station in B.STATION_LAT:
            p = pool(station, day.month)
            lev = np.where(p.height_agl_m.values < 1500, 950, 700)
            for gas in B.GASES:
                field = ds[gas] * SCALE[gas] * MW_AIR / MW[gas]
                vals = np.empty(len(p))
                for L in (950, 700):
                    m = lev == L
                    if m.any():
                        vals[m] = field.sel(isobaricInhPa=L).interp(latitude=xr.DataArray(p.latitude.values[m], dims="p"),
                                                                     longitude=xr.DataArray(p.longitude.values[m], dims="p")).values
                curt = float(B.background(gas, [when], latitudes=p.latitude.values)[0])
                c = B.curtain(gas)
                rows.append(dict(gas=gas, station=station, time=when, cams=float(np.nanmean(vals)), curtain=curt,
                                 diff=curt - float(np.nanmean(vals)), curtain_extended=bool(B.decyear([when])[0] > c.extension_start)))
        ds.close()
    table = pd.DataFrame(rows)
    if table.empty:
        print("no CAMS files", flush=True)
        return table
    table.to_csv(OUT / "validation_cams_forecast.csv", index=False, float_format="%.4f")
    s = table.groupby(["gas", "station", "curtain_extended"]).agg(n=("diff", "size"), bias=("diff", "mean"), sd=("diff", "std")).reset_index()
    # same-calendar-month comparison: 2026 months against the same months of 2025 (reference final)
    t = table.assign(year=table.time.dt.year, month=table.time.dt.month)
    piv = t.pivot_table(index=["gas", "station", "month"], columns="year", values="diff")
    if 2025 in piv and 2026 in piv:
        piv["d2026_minus_d2025"] = piv[2026] - piv[2025]
        piv.reset_index().to_csv(OUT / "validation_cams_same_month.csv", index=False, float_format="%.4f")
        print(piv.round(2).to_string(), flush=True)
    s.to_csv(OUT / "validation_cams_stats.csv", index=False, float_format="%.4f")
    print(s.to_string(), flush=True)
    return table


# ------------------------------------------------------------------ tower
def tower() -> pd.DataFrame:
    import noaa_flask as F
    from a120_obs2026 import BKT_CO2_FLASK_OFFSET
    old = pd.read_pickle(ROOT / "outputs/all.pkl")
    new = pd.read_pickle(ROOT / "outputs/all_2026.pkl")
    old = old[(old.station == "BKT") & (old.time_utc < "2025-01-01")]
    new = new[(new.station == "BKT") & (new.time_utc >= "2025-01-01")].copy()
    new["co2"] = new.co2 + BKT_CO2_FLASK_OFFSET  # a120: the new export is offset from the NOAA flasks
    obs = pd.concat([old, new], ignore_index=True)
    obs = obs[obs.hour_local.between(12, 16)]
    rows = []
    months = pd.date_range("2004-01-01", "2026-11-01", freq="MS")
    curt = pd.read_csv(OUT / "background_monthly_2004_2026.csv", parse_dates=["month"])
    curt = curt[curt.station == "BKT"].pivot(index="month", columns="gas", values="background")
    for gas in B.GASES:
        x = obs[~obs[f"suspect_{gas}"].astype(bool)].dropna(subset=[gas])
        x = x.assign(month=x.time_utc.dt.to_period("M").dt.to_timestamp())
        g = x.groupby("month")[gas].agg(p10=lambda v: np.percentile(v, 10), hours="size")
        g = g[g.hours >= 60]
        flask = F.monthly(gas, "bkt")
        flask.index = flask.index.to_period("M").to_timestamp()
        frame = pd.DataFrame(index=months)
        frame["curtain"] = curt[gas]
        frame["tower_p10_afternoon"] = g.p10
        frame["tower_hours"] = g.hours
        frame["flask_monthly"] = flask
        frame["gas"] = gas
        rows.append(frame.rename_axis("month").reset_index())
    table = pd.concat(rows, ignore_index=True)
    table.to_csv(OUT / "validation_tower_flask_monthly.csv", index=False, float_format="%.4f")
    stats = []
    for gas, t in table.groupby("gas"):
        for label, col in (("BKT afternoon P10", "tower_p10_afternoon"), ("BKT NOAA flask monthly", "flask_monthly")):
            for period, (a, b) in {"2004-2013": ("2004", "2013-12"), "2019-2026": ("2019", "2026-11"), "all": ("2004", "2026-11")}.items():
                u = t[(t.month >= a) & (t.month <= pd.Timestamp(b) + pd.offsets.MonthEnd(0))].dropna(subset=[col, "curtain"])
                if len(u) < 6:
                    continue
                d = u.curtain - u[col]
                # seasonal structure: correlation of detrended monthly values (12-month running mean removed)
                da = (u.set_index("month").curtain - u.set_index("month").curtain.rolling(13, center=True, min_periods=7).mean())
                db = (u.set_index("month")[col] - u.set_index("month")[col].rolling(13, center=True, min_periods=7).mean())
                ok = da.notna() & db.notna()
                stats.append(dict(gas=gas, comparison=label, period=period, months=len(u), bias=d.mean(), sd=d.std(),
                                  detrended_r=float(np.corrcoef(da[ok], db[ok])[0, 1]) if ok.sum() > 6 else np.nan,
                                  bias_trend_per_year=float(np.polyfit(B.decyear(u.month), d, 1)[0])))
    s = pd.DataFrame(stats)
    s.to_csv(OUT / "validation_tower_flask_stats.csv", index=False, float_format="%.4f")
    print(s.to_string(), flush=True)
    return table


def correction() -> pd.DataFrame:
    """Optional fixed seasonal offset: CT minus curtain at the endpoint cloud, as mean + 2 harmonics of day of year.

    Fitted per station on one CarbonTracker release (CO2: CT-NRT.v2025-1 monthly 2021-2024; CH4: CT-CH4-2025
    2019-2023 days) and scored at receptor level on rows not used in the fit.  The same offset applies
    to every year, so it does not break year-to-year consistency; it only moves the curtain toward one
    CarbonTracker release's seasonal inflow structure.
    """
    inf = pd.read_csv(OUT / "validation_inflow_ct.csv", parse_dates=["time"])
    rec = pd.read_csv(OUT / "validation_receptor_rows.csv", parse_dates=["time_utc"])
    train = {"co2": "CT-NRT.v2025-1 monthly", "ch4": "CT-CH4-2025 daily"}
    coef_rows, score = [], []
    for gas, release in train.items():
        for station in B.STATION_LAT:
            u = inf[(inf.gas == gas) & (inf.ct_release == release) & (inf.station == station)]
            if gas == "ch4":
                u = u[u.time.dt.year < 2023]  # hold Nov-Dec 2023 out for the receptor test
            X = B.basis(B.decyear(u.time) % 1, 0, poly=0, harmonics=2)
            coef, *_ = np.linalg.lstsq(X, -u["diff"].values, rcond=None)
            coef_rows.append(dict(gas=gas, station=station, trained_on=release, n=len(u), first=u.time.min(), last=u.time.max(),
                                  **{f"c{k}": v for k, v in enumerate(coef)}))
            r = rec[(rec.gas == gas) & (rec.station == station)]
            off = B.basis(B.decyear(r.time_utc) % 1, 0, poly=0, harmonics=2) @ coef
            for (release_r, period), g in r.assign(adj=r["diff"].values + off).groupby(["ct_release", "period"]):
                score.append(dict(gas=gas, station=station, test_release=release_r, period=period, n=len(g),
                                  bias_raw=g["diff"].mean(), sd_raw=g["diff"].std(),
                                  rmse_raw=float(np.sqrt((g["diff"] ** 2).mean())),
                                  bias_adjusted=g.adj.mean(), sd_adjusted=g.adj.std(),
                                  rmse_adjusted=float(np.sqrt((g.adj ** 2).mean())),
                                  same_release_and_period_as_fit=bool((gas == "co2" and release_r == "CT-NRT.v2025-1")
                                                                      or (gas == "ch4" and g.time_utc.dt.year.max() < 2023))))
    c = pd.DataFrame(coef_rows)
    c.to_csv(OUT / "seasonal_offset_coefficients.csv", index=False, float_format="%.5f")
    s = pd.DataFrame(score)
    s.to_csv(OUT / "seasonal_offset_receptor_scores.csv", index=False, float_format="%.4f")
    print(c.round(3).to_string()); print(s.round(2).to_string(), flush=True)
    return s


def growth() -> pd.DataFrame:
    """Year-over-year change by calendar month: curtain vs BKT tower afternoon P10 (independent of the MBL).

    The tower carries regional signals, so only the change from one year to the next is compared;
    BKT CO2 2025 and 2026 both come from the new export with the same a120 offset, so it cancels.
    """
    t = pd.read_csv(OUT / "validation_tower_flask_monthly.csv", parse_dates=["month"])
    rows = []
    for gas, g in t.groupby("gas"):
        g = g.set_index("month")
        for y in (2020, 2021, 2022, 2023, 2024, 2025, 2026):
            for m in range(1, 13):
                a, b = pd.Timestamp(y, m, 1), pd.Timestamp(y - 1, m, 1)
                if a not in g.index or b not in g.index:
                    continue
                rows.append(dict(gas=gas, year=y, month=m, curtain_change=g.curtain[a] - g.curtain[b],
                                 tower_change=g.tower_p10_afternoon[a] - g.tower_p10_afternoon[b]))
    table = pd.DataFrame(rows).dropna()
    table["curtain_minus_tower"] = table.curtain_change - table.tower_change
    table.to_csv(OUT / "validation_growth_yoy.csv", index=False, float_format="%.4f")
    s = table.groupby(["gas", "year"]).agg(months=("month", "size"), curtain_change=("curtain_change", "mean"),
                                           tower_change=("tower_change", "mean"), diff_mean=("curtain_minus_tower", "mean"),
                                           diff_sd=("curtain_minus_tower", "std")).reset_index()
    s.to_csv(OUT / "validation_growth_yoy_stats.csv", index=False, float_format="%.4f")
    print(s.round(2).to_string(), flush=True)
    return table


# ------------------------------------------------------------------ figures
def figures() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import ghg_common as G
    G.style()
    rec = pd.read_csv(OUT / "validation_receptor_rows.csv", parse_dates=["time_utc"])
    inf = pd.read_csv(OUT / "validation_inflow_ct.csv", parse_dates=["time"])
    hc = pd.read_csv(OUT / "hindcast_extension_by_lead.csv")
    mon = pd.read_csv(OUT / "background_monthly_2004_2026.csv", parse_dates=["month"])
    tw = pd.read_csv(OUT / "validation_tower_flask_monthly.csv", parse_dates=["month"])
    camsf = OUT / "validation_cams_forecast.csv"
    cams_t = pd.read_csv(camsf, parse_dates=["time"]) if camsf.exists() else pd.DataFrame()
    unit = B.GASES
    name = {"co2": "CO$_2$", "ch4": "CH$_4$"}
    for gas in B.GASES:
        fig, ax = plt.subplots(2, 2, figsize=(13, 8.6))
        a = ax[0, 0]
        for st in B.STATION_LAT:
            m = mon[(mon.gas == gas) & (mon.station == st)]
            a.plot(m.month, m.background, color=G.COL[st], ls=G.LS[st], lw=1.2, label=f"MBL curtain, {st} endpoint climatology")
        t = tw[tw.gas == gas]
        a.plot(t.month, t.flask_monthly, ".", color="0.35", ms=3, label="NOAA BKT flask, monthly")
        a.plot(t.month, t.tower_p10_afternoon, "x", color="0.6", ms=3, label="BKT tower, afternoon P10")
        ext = mon[(mon.gas == gas) & mon.extended]
        if len(ext):
            a.axvspan(ext.month.min(), ext.month.max() + pd.offsets.MonthEnd(0), color="0.9", zorder=0)
            a.text(ext.month.min(), a.get_ylim()[0], " extension", va="bottom", fontsize=8, color="0.3")
        a.set_title(f"(a) {name[gas]} background 2004 to Nov 2026")
        a.set_ylabel(f"{name[gas]} ({unit[gas]})")
        a.legend(fontsize=7, loc="upper left")
        a = ax[0, 1]
        r = rec[rec.gas == gas]
        for st in B.STATION_LAT:
            u = r[r.station == st]
            a.scatter(u.ct, u.curtain, s=9, color=G.COL[st], marker=G.MRK[st], alpha=.7, label=f"{st} (n={len(u)})")
        lim = [min(r.ct.min(), r.curtain.min()), max(r.ct.max(), r.curtain.max())]
        a.plot(lim, lim, color="0.4", lw=.8)
        a.set_xlabel(f"CarbonTracker boundary at endpoints ({unit[gas]})")
        a.set_ylabel(f"MBL curtain at endpoints ({unit[gas]})")
        rel = ", ".join(sorted(r.ct_release.unique()))
        a.set_title(f"(b) Receptor level: {rel}", fontsize=9)
        a.legend(fontsize=7)
        a = ax[1, 0]
        f = inf[inf.gas == gas]
        styles = {"CT-NRT.v2025-1 monthly": "o", "CT-NRT.v2025-1 daily": "s", "CT2026 daily": "^", "CT2022 daily": "D",
                  "CT-CH4-2025 daily": "o"}
        for (relname, st), u in f.groupby(["ct_release", "station"]):
            a.plot(u.time, u["diff"], styles.get(relname, "o"), ms=3.5, color=G.COL[st], alpha=.75,
                   mfc="none" if st == "JMB" else G.COL[st], label=f"{relname}, {st}")
        if len(cams_t):
            for st in B.STATION_LAT:
                u = cams_t[(cams_t.gas == gas) & (cams_t.station == st)]
                a.plot(u.time, u["diff"], "-", lw=.9, color=G.COL[st], ls=G.LS[st], alpha=.9, label=f"CAMS GHG forecast, {st}")
        a.axhline(0, color="0.4", lw=.7)
        a.set_title("(c) Curtain minus model at the month's endpoint cloud (no footprint)", fontsize=9)
        a.set_ylabel(f"difference ({unit[gas]})")
        a.legend(fontsize=6, ncol=2)
        a = ax[1, 1]
        for variant, ls in (("trend_only", ":"), ("trend_resid", "--"), ("global_anchor", "-")):
            for st in B.STATION_LAT:
                u = hc[(hc.gas == gas) & (hc.variant == variant) & (hc.station == st)]
                a.plot(u.lead_month, u.rmse, ls=ls, color=G.COL[st], marker=G.MRK[st], ms=3, label=f"{variant}, {st}")
        a.set_xlabel("month of the extended year (cutoff 1 Jan)")
        a.set_ylabel(f"hindcast RMSE ({unit[gas]})")
        a.set_title("(d) Extension skill, cutoffs 2015 to 2025", fontsize=9)
        a.legend(fontsize=6, ncol=2)
        fig.suptitle(f"{name[gas]} background from the NOAA MBL curtain at HYSPLIT-STILT endpoint latitudes", fontsize=11)
        fig.tight_layout()
        fig.savefig(OUT / f"background_{gas}_validation.png", dpi=300)
        plt.close(fig)
        print("figure", gas, flush=True)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("stages", nargs="*", default=["receptors", "release", "inflow", "hindcast", "cams", "tower", "growth", "correction", "figures"])
    a = p.parse_args()
    fn = dict(receptors=receptors, release=release, inflow=inflow, hindcast=hindcast, cams=cams, tower=tower, growth=growth, correction=correction, figures=figures)
    for s in a.stages:
        fn[s]()


if __name__ == "__main__":
    main()
