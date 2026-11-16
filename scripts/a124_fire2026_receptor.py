"""2026 burning season at Jambi and Bukit Kototabang: where the smoke came from.

A screening-level source-receptor inversion for carbon monoxide, built only from
what exists for 2026.  The CO2/CH4 inversion cannot be run for 2026: its
boundary and prior fields end in 2023 (CH4) and 2024 (CO2), and no HYSPLIT
meteorology is staged for 2026.  Carbon monoxide is the combustion tracer the
operational model already uses for episodes, and fire is what changed in 2026.

Transport: kinematic two-dimensional back trajectories in GFS 0.25 degree
analysis winds (a123), 850 and 925 hPa, nine start points per level (station and
eight neighbours 0.15 degree away), released at 06 UTC (13 WIB), 72 h back,
15 min Heun steps, linear in time and space.  This is NOT HYSPLIT: no vertical
motion, no turbulence, no boundary-layer depth.  It locates the upwind sector;
it does not compute a footprint in ppm per flux.

Exposure: for every trajectory point, NASA FIRMS high-confidence hotspots of the
same and the previous UTC day within a Gaussian kernel (sigma 20 km), weighted by
the step length and by exp(-age / 36 h) for dilution, averaged over members and
summed per province (cell-free: each hotspot is labelled by point-in-polygon in
the 38-province asset).  Units: hotspot-hours, a relative index.

Observation: afternoon mean CO, 05-09 UTC (12-16 WIB), at least three hours.

Inversion: y = b + sum_p a_p E_p, a_p >= 0, for (i) one common scale over all
provinces and (ii) separate scales for Jambi, Sumatera Selatan, Riau and the
rest.  Skill: leave-one-week-out RMSE against two nulls, the intercept alone
(no fire information) and the same model fed raw hotspot counts in the four
provinces without any wind (does the transport add anything?).  Intervals:
week-block bootstrap.  Attribution shares are a_p E_p over the fitted fire term,
on the days above the station's median exposure.
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from scipy.interpolate import RegularGridInterpolator
from scipy.optimize import nnls

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G

# Sensitivity runs: FIRE_SIGMA_KM, FIRE_TAU_H, FIRE_HOURS_BACK, FIRE_LEVELS ("850,925") and
# FIRE_TAG; a tagged run writes to fire2026/sens_<tag>/ and never overwrites the base run.
TAG = os.environ.get("FIRE_TAG", "")
OUT = G.OUT / "jambi2026" / "fire2026" / (f"sens_{TAG}" if TAG else "")
OUT.mkdir(parents=True, exist_ok=True)
WIND = sorted((G.ROOT / "data" / "gfs_wind_2026").glob("gfs_wind_850_925_*.nc"))[-1]
HOTSPOT = G.ROOT.parent / "HOTSPOT" / "archived_hotspot_idn.csv"
PROV = G.ROOT.parent / ".assets" / "indonesia_38prov.geojson"

DAYS = pd.date_range("2026-08-01", "2026-10-07", freq="D")
HOURS_BACK = int(os.environ.get("FIRE_HOURS_BACK", 72))
DT_MIN = 15
SIGMA_KM = float(os.environ.get("FIRE_SIGMA_KM", 20.0))
AGE_TAU_H = float(os.environ.get("FIRE_TAU_H", 36.0))
LEVELS = tuple(int(x) for x in os.environ.get("FIRE_LEVELS", "850,925").split(","))
GROUPS = ["JAMBI", "SUMATERA SELATAN", "RIAU"]
STATIONS = ["JMB", "BKT"]
RNG = np.random.default_rng(20261008)


# ------------------------------------------------------------------ inputs ---
def winds():
    ds = xr.open_dataset(WIND)
    lev = "isobaricInhPa" if "isobaricInhPa" in ds.dims else "pressure_level"
    t = (pd.to_datetime(ds.valid_time.values) - pd.Timestamp("2026-01-01")) / pd.Timedelta(hours=1)
    lat = ds.latitude.values[::-1]
    lon = ds.longitude.values
    interp = {}
    for p in (850, 925):
        u = ds.u.sel({lev: p}).values[:, ::-1, :]
        v = ds.v.sel({lev: p}).values[:, ::-1, :]
        interp[p] = (RegularGridInterpolator((t.values, lat, lon), u, bounds_error=False, fill_value=np.nan),
                     RegularGridInterpolator((t.values, lat, lon), v, bounds_error=False, fill_value=np.nan))
    return interp, (t.min(), t.max())


def hotspots():
    import geopandas as gpd
    h = pd.read_csv(HOTSPOT)
    h = h[(h.year == 2026) & h.month.between(7, 10) & h.lat.between(-10, 10) & h.lon.between(90, 125)].copy()
    h["date"] = pd.to_datetime(dict(year=h.year, month=h.month, day=h.day))
    prov = gpd.read_file(PROV)
    name_col = [c for c in prov.columns if prov[c].astype(str).str.upper().str.contains("JAMBI").any()][0]
    prov["NAME"] = prov[name_col].astype(str).str.upper().str.strip()
    prov["geometry"] = prov.geometry.make_valid()
    pts = gpd.GeoDataFrame(h, geometry=gpd.points_from_xy(h.lon, h.lat), crs=prov.crs)
    j = gpd.sjoin(pts, prov[["NAME", "geometry"]], how="left", predicate="within")
    j = j[~j.index.duplicated()]
    h["province"] = j["NAME"].fillna("OUTSIDE").values
    h["group"] = np.where(h.province.isin(GROUPS), h.province, "OTHER")
    return h.reset_index(drop=True)


def observations():
    d = pd.read_pickle(G.OUT / "all_2026.pkl")
    d = d[d.station.isin(STATIONS) & d.time_utc.dt.hour.between(5, 9)]
    g = d.groupby(["station", d.time_utc.dt.normalize()]).co.agg(["mean", "count"]).reset_index()
    g = g[g["count"] >= 3].rename(columns={"time_utc": "day", "mean": "co"})
    return g[["station", "day", "co"]]


# -------------------------------------------------------------- transport ---
def trajectories(interp, lat0, lon0, t0_hours):
    """Members x steps arrays of lat, lon, age (h).  Heun integration backward."""
    starts = [(lat0, lon0)] + [(lat0 + 0.15 * np.sin(a), lon0 + 0.15 * np.cos(a))
                               for a in np.linspace(0, 2 * np.pi, 8, endpoint=False)]
    n = int(HOURS_BACK * 60 / DT_MIN)
    dt = -DT_MIN * 60.0
    out_lat, out_lon = [], []
    for p in LEVELS:
        fu, fv = interp[p]
        lat = np.array([s[0] for s in starts], float)
        lon = np.array([s[1] for s in starts], float)
        L, O = [lat.copy()], [lon.copy()]
        t = t0_hours
        for _ in range(n):
            def vel(la, lo, tt):
                pts = np.column_stack([np.full_like(la, tt), la, lo])
                return fu(pts), fv(pts)
            u1, v1 = vel(lat, lon, t)
            la1 = lat + v1 * dt / 111_000.0
            lo1 = lon + u1 * dt / (111_000.0 * np.cos(np.radians(lat)))
            u2, v2 = vel(la1, lo1, t + dt / 3600)
            lat = lat + 0.5 * (v1 + v2) * dt / 111_000.0
            lon = lon + 0.5 * (u1 + u2) * dt / (111_000.0 * np.cos(np.radians(lat)))
            t += dt / 3600
            L.append(lat.copy()); O.append(lon.copy())
        out_lat.append(np.array(L).T); out_lon.append(np.array(O).T)
    lat = np.vstack(out_lat); lon = np.vstack(out_lon)
    age = np.arange(lat.shape[1]) * DT_MIN / 60.0
    return lat, lon, age


def exposure(lat, lon, age, t0, hs):
    """Hotspot-hours per group, averaged over members."""
    res = {g: 0.0 for g in GROUPS + ["OTHER"]}
    ok = np.isfinite(lat) & np.isfinite(lon)
    w_age = np.exp(-age / AGE_TAU_H) * DT_MIN / 60.0
    times = t0 - pd.to_timedelta(age, unit="h")
    for day in pd.unique(times.normalize()):
        sel = (times.normalize() == day)
        cand = hs[(hs.date == day) | (hs.date == day - pd.Timedelta(days=1))]
        if cand.empty:
            continue
        la, lo = lat[:, sel], lon[:, sel]
        m = ok[:, sel]
        w = np.broadcast_to(w_age[sel], la.shape)
        P = np.column_stack([la[m], lo[m], w[m]])
        if not len(P):
            continue
        dy = (cand.lat.values[None, :] - P[:, :1]) * 111.0
        dx = (cand.lon.values[None, :] - P[:, 1:2]) * 111.0 * np.cos(np.radians(P[:, :1]))
        k = np.exp(-(dx ** 2 + dy ** 2) / (2 * SIGMA_KM ** 2)) * P[:, 2:3]
        contrib = k.sum(axis=0)
        for g in res:
            res[g] += float(contrib[cand.group.values == g].sum())
    n_members = lat.shape[0]
    return {g: v / n_members for g, v in res.items()}


def density(lat, lon, age, grid):
    """Age-weighted residence on a 0.25 degree grid, for the maps."""
    w = np.broadcast_to(np.exp(-age / AGE_TAU_H), lat.shape)
    m = np.isfinite(lat) & np.isfinite(lon)
    H, _, _ = np.histogram2d(lat[m], lon[m], bins=grid, weights=w[m])
    return H / lat.shape[0]


# -------------------------------------------------------------- inversion ---
def fit(X, y):
    """Free intercept, nonnegative slopes."""
    xm, ym = X.mean(axis=0), y.mean()
    if X.shape[1] == 0:
        return ym, np.zeros(0)
    a, _ = nnls(X - xm, y - ym)
    return ym - xm @ a, a


def cv(df, cols, weeks):
    pred = np.full(len(df), np.nan)
    for wk in np.unique(weeks):
        test = weeks == wk
        b, a = fit(df.loc[~test, cols].values, df.co.values[~test])
        pred[test] = b + df.loc[test, cols].values @ a
    return pred


def evaluate(df, station):
    weeks = df.day.dt.to_period("W-SUN").astype(str).values
    models = {"null_intercept": [], "hotspot_count_no_wind": ["n_" + g for g in GROUPS],
              "exposure_common": ["E_total"], "exposure_by_province": ["E_" + g for g in GROUPS + ["OTHER"]]}
    preds = {m: cv(df, c, weeks) for m, c in models.items()}
    rows = []
    labels = np.unique(weeks)
    idx = [np.flatnonzero(weeks == l) for l in labels]
    W = RNG.multinomial(len(idx), np.repeat(1 / len(idx), len(idx)), size=4000)
    cnt = np.array([len(i) for i in idx]); den = W @ cnt
    for m, p in preds.items():
        e = p - df.co.values
        row = dict(station=station, model=m, n=len(df), weeks=len(labels), rmse=float(np.sqrt(np.mean(e ** 2))),
                   r2_cv=float(1 - np.sum(e ** 2) / np.sum((df.co - df.co.mean()) ** 2)))
        for base in ("null_intercept", "hotspot_count_no_wind"):
            eb = preds[base] - df.co.values
            s = np.array([np.sum(e[i] ** 2) for i in idx]); sb = np.array([np.sum(eb[i] ** 2) for i in idx])
            d = np.sqrt((W @ s) / den) - np.sqrt((W @ sb) / den)
            row[f"delta_vs_{base}"] = row["rmse"] - float(np.sqrt(np.mean(eb ** 2)))
            row[f"lo_vs_{base}"], row[f"hi_vs_{base}"] = np.quantile(d, [.025, .975])
        rows.append(row)
    # full fits and bootstrap of parameters and attribution
    params = []
    for m in ("exposure_common", "exposure_by_province"):
        cols = models[m]
        b, a = fit(df[cols].values, df.co.values)
        boots = []
        for k in range(1000):
            pick = np.concatenate([idx[i] for i in RNG.integers(0, len(idx), len(idx))])
            bb, aa = fit(df[cols].values[pick], df.co.values[pick])
            boots.append(np.r_[bb, aa])
        boots = np.array(boots)
        for j, name in enumerate(["intercept"] + cols):
            params.append(dict(station=station, model=m, parameter=name, value=float(np.r_[b, a][j]),
                               lo=float(np.quantile(boots[:, j], .025)), hi=float(np.quantile(boots[:, j], .975))))
    # attribution on high-exposure days, common scale (the robust one)
    b, a = fit(df[["E_total"]].values, df.co.values)
    hi = df[df.E_total >= df.E_total.median()]
    share = {g: float((hi["E_" + g]).sum() / hi.E_total.sum()) for g in GROUPS + ["OTHER"]}
    boots = []
    for k in range(1000):
        pick = np.concatenate([idx[i] for i in RNG.integers(0, len(idx), len(idx))])
        h = df.iloc[pick]; h = h[h.E_total >= h.E_total.median()]
        boots.append([h["E_" + g].sum() / h.E_total.sum() for g in GROUPS + ["OTHER"]])
    boots = np.array(boots)
    attrib = [dict(station=station, group=g, share=share[g], lo=float(np.quantile(boots[:, i], .025)),
                   hi=float(np.quantile(boots[:, i], .975)),
                   fire_co_ppb_mean_high_days=float(a[0] * hi["E_" + g].mean()))
              for i, g in enumerate(GROUPS + ["OTHER"])]
    pred = pd.DataFrame({"station": station, "day": df.day, "observed": df.co, **{m: p for m, p in preds.items()}})
    return rows, params, attrib, pred


def geometry(hs):
    """Where each province's Aug-Sep hotspots lie as seen from each tower, and the
    925 hPa wind at the tower over the same months.  Bearings are 'towards the fire'."""
    ds = xr.open_dataset(WIND)
    lev = "isobaricInhPa" if "isobaricInhPa" in ds.dims else "pressure_level"
    h = hs[hs.date.dt.month.isin([8, 9])]
    sectors = ["U", "TL", "T", "Tg", "S", "BD", "B", "BL"]   # N, NE, E, SE, S, SW, W, NW
    rows, wind = [], []
    for st in STATIONS:
        lat0, lon0 = G.STATIONS[st][2], G.STATIONS[st][3]
        for g in GROUPS:
            q = h[h.group == g]
            dy = (q.lat.values - lat0) * 111.0
            dx = (q.lon.values - lon0) * 111.0 * np.cos(np.radians(lat0))
            b = (np.degrees(np.arctan2(dx, dy)) + 360) % 360
            sec = np.array(sectors)[((b + 22.5) // 45).astype(int) % 8]
            r = dict(station=st, group=g, hotspots=len(q), median_distance_km=float(np.median(np.hypot(dx, dy))))
            r.update({f"frac_{k}": float((sec == k).mean()) for k in sectors})
            rows.append(r)
        w = ds.sel(latitude=lat0, longitude=lon0, method="nearest").sel({lev: 925})
        t = pd.to_datetime(w.valid_time.values)
        m = t.month.isin([8, 9])
        u, v = w.u.values[m], w.v.values[m]
        wind.append(dict(station=st, level_hpa=925, n=int(m.sum()),
                         vector_mean_from_deg=float((np.degrees(np.arctan2(-u.mean(), -v.mean())) + 360) % 360),
                         median_from_deg=float(np.median((np.degrees(np.arctan2(-u, -v)) + 360) % 360)),
                         mean_speed_ms=float(np.hypot(u, v).mean())))
    pd.DataFrame(rows).to_csv(OUT / "hotspot_geometry.csv", index=False)
    pd.DataFrame(wind).to_csv(OUT / "wind_aug_sep.csv", index=False)


def main():
    if "--geometry-only" in sys.argv:
        geometry(hotspots())
        return
    interp, (tmin, tmax) = winds()
    hs = hotspots()
    geometry(hs)
    hs.groupby(["group", hs.date.dt.month]).size().unstack(0).to_csv(OUT / "hotspots_by_group_month.csv")
    obs = observations()
    st_xy = {s: (G.STATIONS[s][2], G.STATIONS[s][3]) for s in STATIONS}
    lat_edges = np.arange(-10, 10.001, 0.25); lon_edges = np.arange(90, 125.001, 0.25)
    rows = []
    dens = {}
    for s in STATIONS:
        for day in DAYS:
            t0 = day + pd.Timedelta(hours=6)
            th = (t0 - pd.Timestamp("2026-01-01")) / pd.Timedelta(hours=1)
            if th - HOURS_BACK < tmin or th > tmax:
                continue
            lat, lon, age = trajectories(interp, *st_xy[s], th)
            e = exposure(lat, lon, age, t0, hs)
            dens[(s, day)] = density(lat, lon, age, (lat_edges, lon_edges))
            r = dict(station=s, day=day, valid_member_frac=float(np.isfinite(lat[:, -1]).mean()),
                     **{"E_" + g: v for g, v in e.items()})
            same = hs[(hs.date == day) | (hs.date == day - pd.Timedelta(days=1))]
            r.update({"n_" + g: int((same.group == g).sum()) for g in GROUPS})
            rows.append(r)
        print(s, "trajectories done", flush=True)
    ex = pd.DataFrame(rows)
    ex["E_total"] = ex[["E_" + g for g in GROUPS + ["OTHER"]]].sum(axis=1)
    ex.to_csv(OUT / "daily_exposure.csv", index=False)
    np.savez_compressed(OUT / "trajectory_density.npz", lat_edges=lat_edges, lon_edges=lon_edges,
                        keys=np.array([f"{s}|{d:%Y-%m-%d}" for s, d in dens]), dens=np.array(list(dens.values())))
    allrows, allpar, allatt, allpred = [], [], [], []
    for s in STATIONS:
        df = ex[ex.station == s].merge(obs[obs.station == s], on=["station", "day"]).dropna().reset_index(drop=True)
        r, p, a, pr = evaluate(df, s)
        allrows += r; allpar += p; allatt += a; allpred.append(pr)
    sk = pd.DataFrame(allrows); sk.to_csv(OUT / "skill.csv", index=False)
    pa = pd.DataFrame(allpar); pa.to_csv(OUT / "parameters.csv", index=False)
    at = pd.DataFrame(allatt); at.to_csv(OUT / "attribution.csv", index=False)
    pd.concat(allpred).to_csv(OUT / "cv_predictions.csv", index=False)
    json.dump(dict(wind=str(WIND), hotspots=str(HOTSPOT), provinces=str(PROV), days=[str(DAYS[0].date()), str(DAYS[-1].date())],
                   hours_back=HOURS_BACK, dt_min=DT_MIN, sigma_km=SIGMA_KM, age_tau_h=AGE_TAU_H, release_utc="06",
                   levels_hpa=list(LEVELS), members=9 * len(LEVELS), created="2026-10-08"),
              open(OUT / "provenance.json", "w"), indent=1)
    pd.set_option("display.width", 220)
    print(sk.round(3).to_string(index=False)); print(pa.round(3).to_string(index=False)); print(at.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
