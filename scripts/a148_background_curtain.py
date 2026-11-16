#!/usr/bin/env python3
"""One background method per gas for 2004 to Nov 2026: the NOAA MBL curtain at endpoint latitude.

Method (same in every year)
  b(t, receptor) = mean over active terminal endpoints p of MBL(t_end, sin(lat_p))
where MBL is the NOAA GML Greenhouse Gas Marine Boundary Layer surface reference
(CO2 X2019, CH4 X2004A; 41 sine-latitude bins, 48 steps per year; a146), linear
in time and sine of latitude, and t_end is receptor time minus 120 h.

After the reference ends (2026-01-01) the curtain is extended per latitude bin:
  MBL_ext(t, phi) = H_phi(t) + delta(t)
  H_phi    quadratic trend + 4 harmonics fitted to the last 5 years of that bin;
  delta(t) = G(t) - H_G(t), the departure of NOAA's monthly global surface mean
             (co2_mm_gl / ch4_mm_gl, a146) from the same fit to that series, so the
             2026 growth follows the observed global mean.  Past the last global
             month (CO2 Jul 2026, CH4 Jun 2026) delta is held at its last-3-month mean.
The choice of variant (trend only / global anchor) is made by the hindcast in
a149, which replays the same construction with cutoffs 2015 to 2025.

For dates without a footprint the same curtain is sampled with the station's
calendar-month endpoint latitude climatology (all footprint runs, a147):
``background(gas, when, station)``.  Passing ``latitudes`` samples a given
endpoint set instead.

Outputs (outputs/background/)
  endpoint_latitude_climatology.csv  station x month weights on the 41 MBL bins
  mbl_curtain_receptors.csv          every receptor with a footprint (2019, 2023, 2024, 2025-Sep 2026)
  background_operator_rows.csv       the same values keyed to each operator table row
  background_monthly_2004_2026.csv   general function, monthly, BKT and JMB
"""
from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data/bkt_sources/background"
OUT = ROOT / "outputs/background"
TABLES = ROOT / "outputs/hysplit/two_receptor/tables"
GASES = {"co2": "ppm", "ch4": "ppb"}
SINLAT = np.round(np.arange(-1, 1.0001, 0.05), 2)
GLOBAL_FILE = {"co2": "co2_mm_gl.txt", "ch4": "ch4_mm_gl.txt"}
OPERATOR_TABLES = {"footprint_operator_2025_2026.csv": "ch4", "co2_operator_base.csv": "co2",
                   "co2_operator_base_2024.csv": "co2", "co2_operator_2025.csv": "co2", "operator_base.csv": "ch4"}
STATION_LAT = {"BKT": -0.202, "JMB": -1.611}


# ------------------------------------------------------------------ time helpers
def decyear(t) -> np.ndarray:
    t = pd.DatetimeIndex(pd.to_datetime(t))
    start = pd.to_datetime(t.year.astype(str) + "-01-01")
    end = pd.to_datetime((t.year + 1).astype(str) + "-01-01")
    return np.asarray(t.year + (t - start) / (end - start), float)


def from_decyear(x) -> pd.DatetimeIndex:
    x = np.asarray(x, float)
    year = np.floor(x + 1e-9).astype(int)
    start = pd.to_datetime([f"{y}-01-01" for y in year])
    end = pd.to_datetime([f"{y + 1}-01-01" for y in year])
    return pd.DatetimeIndex(start + (end - start) * (x - year))


# ------------------------------------------------------------------ inputs
@lru_cache(None)
def read_mbl(gas: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Decimal-year times, values (t, 41) and 1-sigma uncertainty (t, 41)."""
    path = DATA / "mbl" / f"{gas}_GHGreference_surface_2000_2025.txt"
    head = [ln for ln in path.read_text().splitlines() if ln.startswith("# Sine of latitude steps")]
    steps = np.asarray(head[0].split(":")[1].split(), float)
    if not np.allclose(steps, SINLAT):
        raise ValueError("MBL sine-latitude grid differs from the expected 41 steps")
    rows = np.loadtxt(path, comments="#")
    t, values, unc = rows[:, 0], rows[:, 1::2], rows[:, 2::2]
    if values.shape[1] != 41 or not np.isfinite(values).all():
        raise ValueError("Unexpected MBL table")
    return t, values, unc


@lru_cache(None)
def read_global(gas: str) -> pd.Series:
    """NOAA monthly global surface mean, indexed by decimal year (mid month)."""
    rows = np.loadtxt(DATA / "trends" / GLOBAL_FILE[gas], comments="#")
    return pd.Series(rows[:, 3], index=rows[:, 2], name=f"{gas}_global")


def basis(t: np.ndarray, t0: float, poly: int = 2, harmonics: int = 4) -> np.ndarray:
    x = np.asarray(t, float) - t0
    cols = [x ** k for k in range(poly + 1)]
    for k in range(1, harmonics + 1):
        cols += [np.sin(2 * np.pi * k * x), np.cos(2 * np.pi * k * x)]
    return np.column_stack(cols)


# ------------------------------------------------------------------ curtain
class Curtain:
    """MBL surface reference, extended past ``cutoff`` by the per-bin fit plus a global anchor.

    cutoff         decimal year after which MBL values are not used (default: end of reference)
    variant        'global_anchor' (default) or 'trend_only'
    global_until   last decimal year of the global monthly mean that may be used
                   (default: everything in the file); the hindcast passes earlier values
    """

    def __init__(self, gas: str, cutoff: float | None = None, variant: str = "global_anchor",
                 global_until: float | None = None, window: float = 5.0, poly: int = 2, harmonics: int = 4,
                 horizon: float = 2027.0):
        t, values, unc = read_mbl(gas)
        self.gas, self.variant = gas, variant
        self.cutoff = float(t[-1]) if cutoff is None else float(cutoff)
        keep = t <= self.cutoff + 1e-9
        tt, vv, uu = t[keep], values[keep], unc[keep]
        step = 1 / 48
        future = np.arange(tt[-1] + step, horizon + 1e-9, step)
        self.extension_start = float(tt[-1])
        if len(future):
            fit = (tt > self.cutoff - window)
            X = basis(tt[fit], self.cutoff, poly, harmonics)
            coef, *_ = np.linalg.lstsq(X, vv[fit], rcond=None)
            Xf = basis(future, self.cutoff, poly, harmonics)
            ext = Xf @ coef
            # residual of each bin's fit over the last 6 weeks: persisted so the curtain is continuous
            recent = tt > self.cutoff - 6 / 52
            resid = (vv[recent] - basis(tt[recent], self.cutoff, poly, harmonics) @ coef).mean(axis=0)
            self.delta = np.zeros(len(future))
            self.global_last = np.nan
            if variant in ("trend_resid", "global_anchor"):
                ext = ext + resid[None, :]
            if variant == "global_anchor":
                g = read_global(gas)
                g = g[g.index <= (global_until if global_until is not None else np.inf)]
                gfit = g[(g.index > self.cutoff - window) & (g.index <= self.cutoff)]
                gc, *_ = np.linalg.lstsq(basis(gfit.index.values, self.cutoff, poly, harmonics), gfit.values, rcond=None)
                d_all = g.values - basis(g.index.values, self.cutoff, poly, harmonics) @ gc
                d0 = float(d_all[(g.index > self.cutoff - 2 / 12) & (g.index <= self.cutoff)].mean())
                after = g.index.values > self.cutoff
                if after.any():
                    d = d_all[after] - d0
                    xs = np.r_[self.cutoff, g.index.values[after]]
                    ys = np.r_[0.0, d]
                    # change in the global anomaly since the cutoff; held at its last-3-month mean
                    self.delta = np.where(future <= xs[-1], np.interp(future, xs, ys), float(d[-3:].mean()))
                    self.global_last = float(xs[-1])
            ext = ext + self.delta[:, None]
            # extension uncertainty grows from the last reference value; set by the a149 hindcast
            tt, vv = np.r_[tt, future], np.vstack([vv, ext])
            uu = np.vstack([uu, np.repeat(uu[-1:], len(future), axis=0)])
        self.t, self.values, self.unc = tt, vv, uu

    def profile(self, when) -> tuple[np.ndarray, np.ndarray]:
        """Curtain (41 bins) at each time in ``when``: arrays (n, 41)."""
        x = decyear(when)
        if (x < self.t[0]).any() or (x > self.t[-1]).any():
            raise ValueError("Requested time outside the curtain")
        i = np.clip(np.searchsorted(self.t, x) - 1, 0, len(self.t) - 2)
        w = ((x - self.t[i]) / (self.t[i + 1] - self.t[i]))[:, None]
        return (1 - w) * self.values[i] + w * self.values[i + 1], (1 - w) * self.unc[i] + w * self.unc[i + 1]

    def at(self, when, latitude) -> np.ndarray:
        """Curtain at (time, latitude) pairs."""
        prof, _ = self.profile(when)
        s = np.sin(np.radians(np.asarray(latitude, float)))
        return np.asarray([np.interp(si, SINLAT, p) for si, p in zip(np.atleast_1d(s), prof)])


@lru_cache(None)
def curtain(gas: str) -> Curtain:
    return Curtain(gas)


# ------------------------------------------------------------------ endpoint climatology
def bin_weights(latitudes: np.ndarray) -> np.ndarray:
    """Linear-interpolation weights of each latitude on the 41 sine bins (sum to 1)."""
    s = np.clip(np.sin(np.radians(np.asarray(latitudes, float))), -1, 1)
    j = np.clip(np.searchsorted(SINLAT, s) - 1, 0, 39)
    f = (s - SINLAT[j]) / 0.05
    w = np.zeros(41)
    np.add.at(w, j, 1 - f)
    np.add.at(w, j + 1, f)
    return w / w.sum()


@lru_cache(None)
def endpoints() -> pd.DataFrame:
    return pd.read_csv(OUT / "endpoints_terminal.csv.gz", parse_dates=["time_utc", "endpoint_utc"], dtype={"campaign": str})


@lru_cache(None)
def climatology() -> pd.DataFrame:
    """Station x calendar-month endpoint weights; every receptor counts once (seeds averaged)."""
    path = OUT / "endpoint_latitude_climatology.csv"
    if path.exists():
        return pd.read_csv(path)
    pts = endpoints()
    rows = []
    for (station, month), g in pts.groupby([pts.station, pts.time_utc.dt.month]):
        per = [bin_weights(r.latitude.values) for _, r in g.groupby(["campaign", "time_utc"])]
        w = np.mean(per, axis=0)
        rows.append(dict(station=station, month=month, receptors=len(per), **{f"w{k:02d}": v for k, v in enumerate(w)}))
    table = pd.DataFrame(rows)
    table.to_csv(path, index=False, float_format="%.6f")
    return table


def background(gas: str, when, station: str | None = None, latitudes=None, curtain_obj: Curtain | None = None) -> np.ndarray:
    """Background for any date(s) 2000 to 2026.

    latitudes given: mean of the curtain over those endpoint latitudes at each time
                     (one array of latitudes shared by all times).
    station given:   the station's calendar-month endpoint climatology (a147 runs).
    """
    c = curtain_obj or curtain(gas)
    when = pd.DatetimeIndex(pd.to_datetime(np.atleast_1d(when)))
    prof, _ = c.profile(when)
    if latitudes is not None:
        return prof @ bin_weights(latitudes)
    clim = climatology()
    table = clim[clim.station == station].set_index("month")
    if table.empty:
        raise ValueError(f"No endpoint climatology for {station}")
    w = table.loc[when.month, [f"w{k:02d}" for k in range(41)]].to_numpy()
    return (prof * w).sum(axis=1)


# ------------------------------------------------------------------ receptor sampling
def receptor_values() -> pd.DataFrame:
    pts = endpoints()
    rec = pd.read_csv(OUT / "endpoint_receptors.csv", parse_dates=["time_utc", "endpoint_utc"], dtype={"campaign": str})
    curt = {g: curtain(g) for g in GASES}
    rows = []
    for (campaign, station, seed, stamp), g in pts.groupby(["campaign", "station", "seed", "time_utc"]):
        end = g.endpoint_utc.iloc[0]
        row = dict(campaign=campaign, station=station, seed=seed, time_utc=stamp, endpoint_utc=end)
        w = bin_weights(g.latitude.values)
        for gas, c in curt.items():
            prof, unc = c.profile([end])
            vals = np.interp(np.sin(np.radians(g.latitude.values)), SINLAT, prof[0])
            row[f"{gas}_mbl_endpoint"] = float(vals.mean())
            row[f"{gas}_mbl_endpoint_sd"] = float(vals.std())
            row[f"{gas}_mbl_unc"] = float(unc[0] @ w)
            row[f"{gas}_mbl_station_lat"] = float(np.interp(np.sin(np.radians(STATION_LAT[station])), SINLAT, prof[0]))
            row[f"{gas}_mbl_climatology"] = float(background(gas, [end], station)[0])
            row[f"{gas}_extended"] = bool(decyear([end])[0] > c.extension_start + 1e-9)
        if "ct_ch4_ppb" in g and g.ct_ch4_ppb.notna().any():
            row["ct_ch4_from_endpoints"] = float(g.ct_ch4_ppb.mean())
        rows.append(row)
    per_seed = pd.DataFrame(rows).merge(rec, on=["campaign", "station", "seed", "time_utc", "endpoint_utc"], validate="one_to_one")
    numeric = [c for c in per_seed.columns if c not in ("campaign", "station", "seed", "time_utc", "endpoint_utc")]
    agg = per_seed.groupby(["campaign", "station", "time_utc", "endpoint_utc"])[numeric].mean()
    agg["members"] = per_seed.groupby(["campaign", "station", "time_utc", "endpoint_utc"]).size()
    for gas in GASES:
        agg[f"{gas}_mbl_seed_sd"] = per_seed.groupby(["campaign", "station", "time_utc", "endpoint_utc"])[f"{gas}_mbl_endpoint"].std()
        agg[f"{gas}_extended"] = agg[f"{gas}_extended"].astype(bool)
    return agg.reset_index()


def operator_rows(rec: pd.DataFrame) -> pd.DataFrame:
    """Key the curtain to every row of the existing operator tables (read-only), with their CT values."""
    out = []
    for name, gas in OPERATOR_TABLES.items():
        t = pd.read_csv(TABLES / name, parse_dates=["time_utc"])
        ct_col = {"co2": "background_ppm", "ch4": "background_ppb"}[gas]
        keep = ["station", "time_utc"] + ([ct_col] if ct_col in t else [])
        t = t[keep].rename(columns={ct_col: "ct_background"})
        campaigns = {"footprint_operator_2025_2026.csv": "2025_2026", "co2_operator_2025.csv": "2025_2026",
                     "co2_operator_base.csv": "2023", "operator_base.csv": "2023", "co2_operator_base_2024.csv": "2024"}
        m = t.merge(rec[rec.campaign == campaigns[name]], on=["station", "time_utc"], how="left", validate="one_to_one")
        m.insert(0, "operator_table", name)
        m["ct_gas"] = gas if "ct_background" in t else ""
        out.append(m)
    table = pd.concat(out, ignore_index=True)
    missing = table.co2_mbl_endpoint.isna().sum()
    if missing:
        raise ValueError(f"{missing} operator rows have no endpoint set")
    return table


def monthly_series() -> pd.DataFrame:
    months = pd.date_range("2004-01-01", "2026-11-01", freq="MS")
    rows = []
    for station in STATION_LAT:
        days = pd.date_range("2004-01-01", "2026-11-30", freq="D")
        frame = pd.DataFrame({"time_utc": days})
        for gas in GASES:
            frame[gas] = background(gas, days, station)
        frame["month"] = frame.time_utc.dt.to_period("M").dt.to_timestamp()
        m = frame.groupby("month")[list(GASES)].mean().reindex(months)
        for gas in GASES:
            c = curtain(gas)
            ext = decyear(m.index + pd.Timedelta(days=14)) > c.extension_start
            rows.append(pd.DataFrame(dict(station=station, month=m.index, gas=gas, background=m[gas].values,
                                          unit=GASES[gas], extended=ext)))
    return pd.concat(rows, ignore_index=True)


def main() -> None:
    climatology()
    rec = receptor_values()
    rec.to_csv(OUT / "mbl_curtain_receptors.csv", index=False, float_format="%.4f")
    ops = operator_rows(rec)
    ops.to_csv(OUT / "background_operator_rows.csv", index=False, float_format="%.4f")
    monthly = monthly_series()
    monthly.to_csv(OUT / "background_monthly_2004_2026.csv", index=False, float_format="%.4f")
    for gas in GASES:
        c = curtain(gas)
        print(gas, "reference ends", from_decyear([c.extension_start])[0], "global anchor through",
              from_decyear([c.global_last])[0] if np.isfinite(getattr(c, "global_last", np.nan)) else "none", flush=True)
    print(rec.groupby(["campaign", "station"])[["co2_mbl_endpoint", "ch4_mbl_endpoint", "co2_extended"]].mean().to_string())
    print(ops.groupby("operator_table").size().to_string())


if __name__ == "__main__":
    sys.exit(main())
