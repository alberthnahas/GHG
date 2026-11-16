#!/usr/bin/env python3
"""Analysis of the three-driver transport test (a160): GDAS1, ERA5, GFS 0.25, 2025.

operator   per completed run: the a128 operator row (surface sensitivity by
           province group, CH4 prior terms, hotspot fire exposure), plus
           land sensitivity, local-inventory fossil CO2 (a131 fields, no
           boundary needed), fire CO in ppb (a130 per-tower slope on
           fireexp_total, one slope for every driver), the driver's own PBL
           depth and terrain at the tower at 06 UTC, and the HYSPLIT-diagnosed
           mixed-layer depth (hyts_std, KMIXD=3 as in the footprints).
analyse    driver differences at receptor, monthly and annual scale against
           the GDAS1 seed-noise floor; comparison with observed monthly
           afternoon enhancements (block bootstrap by week); PBL relation;
           transport uncertainty; cost; two figures.

All tables go to outputs/hysplit/driver_test_2025/.  Times are UTC.
"""
from __future__ import annotations

import argparse
import warnings
import json
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G
import a127_hysplit_2025_2026 as H
import a160_driver_test_2025 as A

OUT = A.OUT
ROWS = OUT / "operator_rows.csv"
FIG = OUT / "figures"
GROUPS = ["JAMBI", "SUMATERA SELATAN", "RIAU", "SUMATERA BARAT", "OTHER_IDN", "OUTSIDE"]
DRV = ["gdas1", "era5", "gfs0p25"]
NAME = {"gdas1": "GDAS1 1°", "era5": "ERA5 0.25°", "gfs0p25": "GFS 0.25°"}
COLOR = {"gdas1": "#0072B2", "era5": "#D55E00", "gfs0p25": "#009E73"}      # Okabe-Ito
MARK = {"gdas1": "o", "era5": "s", "gfs0p25": "^"}
RNG = np.random.default_rng(20251)
FIRE_PARAMS = G.OUT / "jambi2026" / "hysplit2025_2026" / "fire_parameters.csv"     # a130


def T():
    import a84_bkt_jmb_two_receptor as mod
    return mod


# ------------------------------------------------------------------ helpers
@lru_cache(maxsize=2)
def land_mask(code: str) -> np.ndarray:
    path = OUT / f"land_mask_{code.lower()}.npy"
    if path.exists():
        return np.load(path)
    import geopandas as gpd
    lat, lon = T().receptor_grid(code)
    assets = G.ROOT.parent / ".assets"
    idn = gpd.read_file(assets / "indonesia_38prov.geojson")[["geometry"]]
    world = gpd.read_file(assets / "world_without_idn.shp")[["geometry"]].to_crs(idn.crs)
    land = pd.concat([idn, world], ignore_index=True)
    land["geometry"] = land.geometry.make_valid()
    glat, glon = np.meshgrid(lat, lon, indexing="ij")
    pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(glon.ravel(), glat.ravel()), crs=idn.crs)
    j = gpd.sjoin(pts, land, how="left", predicate="within")
    hit = ~j.index_right.isna()
    m = hit.groupby(level=0).any().reindex(range(len(pts))).fillna(False).to_numpy().reshape(glat.shape)
    np.save(path, m)
    return m


@lru_cache(maxsize=1)
def fire_slope() -> dict:
    p = pd.read_csv(FIRE_PARAMS)
    return dict(zip(p.station, p.slope_ppb))


@lru_cache(maxsize=2)
def fossil_field(code: str) -> np.ndarray:
    import a131_co2_local_operator as C
    fos, _, cover = C.local_fields(code)
    return np.where(cover, fos, C.edgar_mean(code, 2025))


def met_surface(driver: str, code: str, stamp: pd.Timestamp) -> dict:
    mod = T()
    if driver == "gdas1":
        import a37_bkt_footprint as m
        s = mod.native_surface(code, H.MET / m.gdas1_week_name(stamp.normalize()), stamp)
    else:
        from bkt_arl import ARLReader
        path = A.met_paths(driver, stamp)[-1]
        r = ARLReader(path)
        _, lat, lon, _ = mod.STATIONS[code]
        s = {v: r.point(stamp, v, 0, lat, lon, "nearest") for v in ("PBLH", "SHGT", "SHTF")}
    return {"pblh_met_m": s.get("PBLH"), "terrain_m": s.get("SHGT"), "shtf_wm2": s.get("SHTF", np.nan)}


def mixdepth(driver: str, code: str, stamp: pd.Timestamp) -> float:
    """HYSPLIT-diagnosed mixed-layer depth at the receptor (hyts_std, 1 h, same KMIXD/KMIX0)."""
    import a37_bkt_footprint as m
    mod = T()
    _, lat, lon, _ = mod.STATIONS[code]
    work = OUT / "mixdepth" / driver / f"{code.lower()}_{stamp:%Y%m%dT%H%MZ}"
    if (work / "tdump").exists():
        return parse_tdump(work / "tdump")
    work.mkdir(parents=True, exist_ok=True)
    if driver == "gdas1":
        paths = [H.MET / m.gdas1_week_name(stamp.normalize())]
    else:
        paths = A.met_paths(driver, stamp)[-1:]
    opts = m.TransportOptions()
    ctl = [f"{stamp:%y %m %d %H}", "1", f"{lat:.6f} {lon:.6f} {mod.INLET_HEIGHT_M:.1f}", "-1", "0", "16500.0",
           str(len(paths))]
    for p in paths:
        ctl += [f"{p.parent.resolve()}/", p.name]
    ctl += [f"{work.resolve()}/", "tdump"]
    (work / "CONTROL").write_text("\n".join(ctl) + "\n")
    (work / "SETUP.CFG").write_text(f"&SETUP\n KMIXD = {opts.mixing_depth_method},\n KMIX0 = {opts.minimum_mixing_depth_m},\n"
                                    " TM_MIXD = 1,\n TM_TERR = 1,\n TM_PRES = 1,\n/\n")
    (work / "ASCDATA.CFG").write_text(m.ascdata_text(mod.HYSPLIT_HOME))
    subprocess.run([str(mod.HYSPLIT_HOME / "exec/hyts_std")], cwd=work, capture_output=True, text=True, check=True)
    return parse_tdump(work / "tdump")


def parse_tdump(path: Path) -> float:
    lines = path.read_text().splitlines()
    k = next(i for i, l in enumerate(lines) if "PRESSURE" in l)
    names = lines[k].split()[1:]
    row = lines[k + 1].split()
    vals = dict(zip(names, row[12:12 + len(names)]))
    if float(row[8]) != 0.0:
        raise ValueError(f"first tdump row is not age 0: {path}")
    return float(vals["MIXDEPTH"])


def safe_active(original):
    def f(directory, meta, actual):
        try:
            return original(directory, meta, actual)
        except ValueError:
            pts = pd.read_csv(directory / "PAR_GIS.txt", skipinitialspace=True)
            pts.columns = pts.columns.str.strip()
            return pts.loc[pts.PGRD.gt(0)].drop_duplicates("NSORT") if "NSORT" in pts else pts.iloc[:0]
    return f


# ---------------------------------------------------------------- operator
def operator() -> None:
    import a128_footprint_operator_2025_2026 as O
    mod = T()
    t = A.receptors()
    old = pd.read_csv(ROWS, parse_dates=["time_utc"]) if ROWS.exists() else pd.DataFrame(columns=["driver", "seed", "station", "time_utc"])
    have = set(zip(old.driver, old.seed.astype(int), old.station, old.time_utc))
    todo = []
    for r in t.itertuples():
        for d in DRV:
            todo.append((d, 0, r.station, r.time_utc))
        if r.seed_noise:
            todo.append(("gdas1", A.SEED2, r.station, r.time_utc))
    rows = []
    original_run_dir, original_active = H.run_dir, mod.ext.active_endpoints
    mod.ext.active_endpoints = safe_active(original_active)
    try:
        for d, seed, code, stamp in todo:
            if (d, seed, code, stamp) in have:
                continue
            directory = A.run_dir(d, code, stamp, seed)
            if not (directory / "completion_receipt.json").exists():
                continue
            H.run_dir = lambda c, s, _d=directory: _d
            row, _ = O.one(code, stamp)
            row.pop("PBLH", None); row.pop("pblh_error", None)       # GDAS1-only inside a128; replaced below
            field, meta, actual = mod.ext.read_footprint(directory)
            tot = field.values.sum(axis=0)
            row.update(driver=d, seed=seed, sens_land=float((tot * land_mask(code)).sum()),
                       co2_fossil_ppm=float((tot * fossil_field(code)).sum()),
                       co_fire_ppb=float(fire_slope()[code] * row["fireexp_total"]),
                       runtime_s=json.loads((directory / "completion_receipt.json").read_text())["model_runtime_seconds"])
            row.update(met_surface(d, code, stamp))
            try:
                row["mixdepth_hysplit_m"] = mixdepth(d, code, stamp)
            except Exception as e:  # noqa: BLE001 - recorded
                row["mixdepth_hysplit_m"] = np.nan; row["mixdepth_error"] = repr(e)[:200]
            rows.append(row)
            if len(rows) % 20 == 0:
                print(f"{len(rows)} new rows", flush=True)
                _save(old, rows)
    finally:
        H.run_dir, mod.ext.active_endpoints = original_run_dir, original_active
    _save(old, rows)
    print(f"operator rows: {len(old) + len(rows)} ({len(rows)} new)")


def _save(old, rows):
    out = pd.concat([old, pd.DataFrame(rows)], ignore_index=True) if len(old) else pd.DataFrame(rows)
    out.sort_values(["driver", "seed", "station", "time_utc"]).to_csv(ROWS, index=False)


# ---------------------------------------------------------------- analysis
POS = {"sens_land": "land surface sensitivity (ppm per umol m-2 s-1)",
       "sensitivity": "total surface sensitivity",
       "ch4_model_ppb": "CH4 prior enhancement, local anthropogenic + LPJ wetlands + other natural (ppb)",
       "ch4_edgar_ppb": "CH4 prior enhancement with EDGAR anthropogenic (ppb)",
       "co_fire_ppb": "fire CO, a130 slope x hotspot exposure (ppb)",
       "co2_fossil_ppm": "local-inventory fossil CO2 (ppm)"}
SHARES = [f"share_{g}" for g in GROUPS]


def load() -> pd.DataFrame:
    r = pd.read_csv(ROWS, parse_dates=["time_utc"])
    r["ch4_model_ppb"] = r.ch4_local_ppb + r.ch4_wetlands_ppb + r.ch4_natural_other_ppb
    r["ch4_edgar_ppb"] = r.ch4_anthro_ppb + r.ch4_wetlands_ppb + r.ch4_natural_other_ppb
    for g in GROUPS:
        r[f"share_{g}"] = 100 * r[f"sens_{g}"] / r.sensitivity
    r["month"] = r.time_utc.dt.month
    return r


def wide(r: pd.DataFrame, metric: str) -> pd.DataFrame:
    s = r[r.seed == 0].pivot_table(index=["station", "time_utc"], columns="driver", values=metric)
    return s.dropna()


def seed_pairs(r: pd.DataFrame, metric: str) -> pd.DataFrame:
    g = r[r.driver == "gdas1"].pivot_table(index=["station", "time_utc"], columns="seed", values=metric)
    return g.dropna()


def stat_pair(a: np.ndarray, b: np.ndarray, share: bool) -> dict:
    """b relative to a."""
    out = dict(n=len(a), pearson_r=float(np.corrcoef(a, b)[0, 1]) if len(a) > 2 else np.nan,
               spearman_r=float(pd.Series(a).corr(pd.Series(b), method="spearman")) if len(a) > 2 else np.nan)
    if share:
        d = b - a
        out.update(mean_diff_pp=float(d.mean()), sd_diff_pp=float(d.std(ddof=1)), mean_abs_diff_pp=float(np.abs(d).mean()))
    else:
        ok = (a > MINPOS) & (b > MINPOS)
        lr = np.log(b[ok] / a[ok])
        out["n_ratio"] = int(ok.sum())
        if ok.sum() < 3:
            return out
        out.update(median_ratio=float(np.exp(np.median(lr))), ratio_p10=float(np.exp(np.quantile(lr, .1))),
                   ratio_p90=float(np.exp(np.quantile(lr, .9))), sd_log_ratio=float(lr.std(ddof=1)),
                   rms_log_ratio=float(np.sqrt(np.mean(lr ** 2))))
    return out


MINPOS = 1e-3       # ratios only where both values exceed this (fire CO is zero outside fire weeks)
PAIRS = [("gdas1", "era5"), ("gdas1", "gfs0p25"), ("era5", "gfs0p25")]


def scale_tables(r: pd.DataFrame):
    metrics = list(POS) + SHARES
    rec, mon, ann, noise = [], [], [], {}
    for metric in metrics:
        share = metric.startswith("share_")
        for st in ["BKT", "JMB", "both"]:
            sp = seed_pairs(r, metric)
            if st != "both":
                sp = sp.loc[st]
            nf = stat_pair(sp[0].to_numpy(), sp[A.SEED2].to_numpy(), share)
            noise[(metric, st)] = nf
            rec.append(dict(metric=metric, station=st, pair="gdas1 seed 0 vs seed -10 (noise floor)", **nf))
            w = wide(r, metric)
            if st != "both":
                w = w.loc[[st]]
            for a, b in PAIRS:
                rec.append(dict(metric=metric, station=st, pair=f"{b} vs {a}", **stat_pair(w[a].to_numpy(), w[b].to_numpy(), share)))
        for st in ["BKT", "JMB"]:
            w = wide(r, metric).loc[st]
            m = w.groupby(w.index.month).agg(["mean", "size"])
            nmon = m[("gdas1", "size")]
            nf = noise[(metric, st)]
            key = "sd_diff_pp" if share else "sd_log_ratio"
            floor_m = float(np.sqrt(np.mean(nf.get(key, np.nan) ** 2 / nmon)))
            floor_a = float(nf.get(key, np.nan) / np.sqrt(len(w)))
            for a, b in PAIRS:
                ma, mb = m[(a, "mean")].to_numpy(), m[(b, "mean")].to_numpy()
                row = dict(metric=metric, station=st, pair=f"{b} vs {a}", months=len(ma),
                           pearson_r_monthly=float(np.corrcoef(ma, mb)[0, 1]))
                if share:
                    d = mb - ma
                    row.update(mean_diff_pp=float(d.mean()), rms_diff_pp=float(np.sqrt(np.mean(d ** 2))),
                               max_abs_diff_pp=float(np.abs(d).max()), noise_floor_rms_pp=floor_m)
                else:
                    okm = (ma > MINPOS) & (mb > MINPOS)
                    lr = np.log(mb[okm] / ma[okm])
                    row["months_ratio"] = int(okm.sum())
                    if okm.sum() >= 2:
                        row.update(median_ratio=float(np.exp(np.median(lr))), min_ratio=float(np.exp(lr.min())),
                                   max_ratio=float(np.exp(lr.max())), rms_log_ratio=float(np.sqrt(np.mean(lr ** 2))),
                                   sd_log_ratio_after_annual_bias=float(lr.std(ddof=1)))
                    row["noise_floor_rms_log"] = floor_m
                mon.append(row)
                A_, B_ = w[a].mean(), w[b].mean()
                arow = dict(metric=metric, station=st, pair=f"{b} vs {a}", receptors=len(w))
                if share:
                    arow.update(annual_a=A_, annual_b=B_, diff_pp=B_ - A_, noise_floor_pp=floor_a)
                else:
                    arow.update(annual_a=A_, annual_b=B_, ratio=B_ / A_, log_ratio=float(np.log(B_ / A_)),
                                noise_floor_log=floor_a)
                ann.append(arow)
    return pd.DataFrame(rec), pd.DataFrame(mon), pd.DataFrame(ann), noise


def monthly_means(r: pd.DataFrame) -> pd.DataFrame:
    cols = list(POS) + SHARES + ["pblh_met_m", "mixdepth_hysplit_m", "terrain_m"]
    m = r[r.seed == 0].groupby(["station", "driver", "month"])[cols].mean()
    m["receptors"] = r[r.seed == 0].groupby(["station", "driver", "month"]).size()
    return m.reset_index()


def transport_uncertainty(r: pd.DataFrame, noise: dict) -> pd.DataFrame:
    rows = []
    for metric in POS:
        for st in ["BKT", "JMB"]:
            w = wide(r, metric).loc[st]
            m = w.groupby(w.index.month).mean()
            n = w.groupby(w.index.month).size()
            keep = (m[DRV] > MINPOS).all(axis=1)
            if metric == "co_fire_ppb":
                keep &= m.gdas1 >= 1.0                                   # months with a fire signal only
            m, n = m[keep], n[keep]
            lm = np.log(m[DRV])
            var_between = lm.var(axis=1, ddof=1)                       # per month, across the three drivers
            s_run2 = noise[(metric, st)].get("sd_log_ratio", np.nan) ** 2 / 2       # one run's log noise variance
            excess = np.clip(var_between - s_run2 / n, 0, None)
            u_month = float(np.sqrt(excess.mean()))
            lr_g = np.log(m.gfs0p25 / m.gdas1); lr_e = np.log(m.era5 / m.gdas1)
            rows.append(dict(metric=metric, station=st, months_used=int(keep.sum()),
                             transport_sd_percent_monthly=100 * (np.exp(u_month) - 1),
                             raw_between_driver_sd_percent=100 * (np.exp(float(np.sqrt(var_between.mean()))) - 1),
                             particle_noise_sd_percent_monthly=100 * (np.exp(float(np.sqrt((s_run2 / n).mean()))) - 1),
                             annual_between_driver_sd_percent=100 * (np.exp(float(np.log(w[DRV].mean()).std(ddof=1))) - 1),
                             max_monthly_ratio_spread=float(np.exp((lm.max(axis=1) - lm.min(axis=1)).max())),
                             era5_over_gdas1_monthly_rms_percent=100 * (np.exp(float(np.sqrt((lr_e ** 2).mean()))) - 1),
                             gfs_over_gdas1_monthly_rms_percent=100 * (np.exp(float(np.sqrt((lr_g ** 2).mean()))) - 1)))
    return pd.DataFrame(rows)


# --------------------------------------------------------- observations
def observed(r: pd.DataFrame) -> pd.DataFrame:
    import a128_footprint_operator_2025_2026 as O
    obs = O.afternoon_obs()
    obs = obs[obs.time_utc.dt.year == 2025].copy()
    obs["month"] = obs.time_utc.dt.month
    for gas in ("ch4", "co", "co2"):
        base = obs.groupby(["station", "month"])[f"{gas}_obs"].quantile(0.10).rename(f"{gas}_base")
        obs = obs.merge(base.reset_index(), on=["station", "month"], how="left")
        obs[f"{gas}_enh_obs"] = obs[f"{gas}_obs"] - obs[f"{gas}_base"]
    return obs


GAS = {"ch4": "ch4_model_ppb", "co": "co_fire_ppb", "co2": "co2_fossil_ppm"}


def obs_comparison(r: pd.DataFrame, reps: int = 4000):
    obs = observed(r)
    rows, monthly = [], []
    s0 = r[r.seed == 0]
    for st in ["BKT", "JMB"]:
        for gas, col in GAS.items():
            w = s0[s0.station == st].pivot_table(index="time_utc", columns="driver", values=col).dropna()
            o = obs[obs.station == st].set_index("time_utc")[f"{gas}_enh_obs"]
            d = w.join(o.rename("obs"), how="inner").dropna()
            d["month"] = d.index.month
            d["week"] = d.index.isocalendar().week.to_numpy()
            mm = d.groupby("month")[DRV + ["obs"]].mean()
            mm["n"] = d.groupby("month").size()
            for mo, x in mm.iterrows():
                monthly.append(dict(station=st, gas=gas, month=mo, observed_enhancement=x.obs, receptors=int(x.n),
                                    **{f"model_{k}": x[k] for k in DRV}))
            # block bootstrap by ISO week, paired across drivers
            weeks = np.unique(d.week)
            idx = {k: np.flatnonzero(d.week.to_numpy() == k) for k in weeks}
            X = d[DRV].to_numpy(); y = d.obs.to_numpy(); months = d.month.to_numpy()
            boot = np.full((reps, len(DRV)), np.nan)
            for b in range(reps):
                pick = np.concatenate([idx[k] for k in RNG.choice(weeks, len(weeks))])
                dfb = pd.DataFrame(np.column_stack([X[pick], y[pick]]), columns=DRV + ["obs"])
                dfb["month"] = months[pick]
                g = dfb.groupby("month").mean()
                if len(g) >= 6:
                    boot[b] = [np.corrcoef(g[k], g.obs)[0, 1] for k in DRV]
            for i, k in enumerate(DRV):
                rr = float(np.corrcoef(mm[k], mm.obs)[0, 1])
                diff = boot[:, i] - boot[:, 0]
                rd = float(np.corrcoef(d[k], d.obs)[0, 1])
                rows.append(dict(station=st, gas=gas, driver=k, receptors=len(d), weeks=len(weeks), months=len(mm),
                                 r_monthly=rr, r_lo=float(np.nanquantile(boot[:, i], .025)),
                                 r_hi=float(np.nanquantile(boot[:, i], .975)),
                                 r_minus_gdas1=rr - float(np.corrcoef(mm.gdas1, mm.obs)[0, 1]),
                                 diff_lo=float(np.nanquantile(diff, .025)), diff_hi=float(np.nanquantile(diff, .975)),
                                 r_receptor=rd, mean_model=float(d[k].mean()), mean_observed=float(d.obs.mean()),
                                 model_over_observed=float(d[k].mean() / d.obs.mean())))
    return pd.DataFrame(rows), pd.DataFrame(monthly)


def pbl_table(r: pd.DataFrame) -> pd.DataFrame:
    rows = []
    s0 = r[r.seed == 0]
    for st in ["BKT", "JMB"]:
        for k in DRV:
            x = s0[(s0.station == st) & (s0.driver == k)]
            row = dict(station=st, driver=k, receptors=len(x),
                       pblh_met_median_m=float(x.pblh_met_m.median()), pblh_met_p10_m=float(x.pblh_met_m.quantile(.1)),
                       pblh_met_p90_m=float(x.pblh_met_m.quantile(.9)),
                       mixdepth_hysplit_median_m=float(x.mixdepth_hysplit_m.median()),
                       mixdepth_hysplit_p10_m=float(x.mixdepth_hysplit_m.quantile(.1)),
                       share_mixdepth_at_floor_percent=float(100 * (x.mixdepth_hysplit_m <= 260).mean()),
                       terrain_at_tower_m=float(x.terrain_m.median()))
            for col in ("ch4_model_ppb", "sens_land"):
                ok = (x[col] > 0) & (x.mixdepth_hysplit_m > 0)
                lx, ly = np.log(x.mixdepth_hysplit_m[ok]), np.log(x[col][ok])
                row[f"{col}_vs_mixdepth_spearman"] = float(x[col].corr(x.mixdepth_hysplit_m, method="spearman"))
                row[f"{col}_vs_mixdepth_loglog_slope"] = float(np.polyfit(lx, ly, 1)[0]) if ok.sum() > 5 else np.nan
                row[f"{col}_vs_pblh_met_spearman"] = float(x[col].corr(x.pblh_met_m, method="spearman"))
            rows.append(row)
        # do the driver differences in enhancement follow the differences in mixing depth?
        for a, b in PAIRS:
            ea = s0[(s0.station == st) & (s0.driver == a)].set_index("time_utc")
            eb = s0[(s0.station == st) & (s0.driver == b)].set_index("time_utc")
            j = ea.join(eb, lsuffix="_a", rsuffix="_b", how="inner")
            ok = (j.ch4_model_ppb_a > 0) & (j.ch4_model_ppb_b > 0) & (j.mixdepth_hysplit_m_a > 0) & (j.mixdepth_hysplit_m_b > 0)
            j = j[ok]
            le = np.log(j.ch4_model_ppb_b / j.ch4_model_ppb_a)
            lm = np.log(j.mixdepth_hysplit_m_b / j.mixdepth_hysplit_m_a)
            lp = np.log(j.pblh_met_m_b.clip(lower=10) / j.pblh_met_m_a.clip(lower=10))
            rows.append(dict(station=st, driver=f"{b} vs {a}", receptors=len(j),
                             ch4_ratio_vs_mixdepth_ratio_r=float(np.corrcoef(le, lm)[0, 1]),
                             ch4_ratio_vs_pblh_met_ratio_r=float(np.corrcoef(le, lp)[0, 1]),
                             median_mixdepth_ratio=float(np.exp(np.median(lm))),
                             median_pblh_met_ratio=float(np.exp(np.median(lp)))))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ figures
def fig_shares(mm: pd.DataFrame, path: Path, title: str, highlight: str) -> None:
    import matplotlib.pyplot as plt
    cols = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D9D9D9"]
    labels = ["Jambi", "Sumatera Selatan", "Riau", "Sumatera Barat", "other Indonesia", "outside Indonesia, incl. sea"]
    fig, axes = plt.subplots(2, 1, figsize=(11, 7.6), sharex=True)
    width = 0.27
    for ax, st in zip(axes, ["BKT", "JMB"]):
        for i, k in enumerate(DRV):
            x = mm[(mm.station == st) & (mm.driver == k)].sort_values("month")
            pos = x.month.to_numpy() + (i - 1) * (width + 0.02)
            bottom = np.zeros(len(x))
            for g, c, lab in zip(GROUPS, cols, labels):
                v = x[f"share_{g}"].to_numpy()
                ax.bar(pos, v, width, bottom=bottom, color=c, edgecolor="white", linewidth=0.3,
                       label=lab if (i == 0 and st == "BKT") else None)
                bottom += v
            for p_ in pos:
                ax.text(p_, 101, {"gdas1": "G", "era5": "E", "gfs0p25": "F"}[k], ha="center", va="bottom", fontsize=6.5, color="#333")
        n = mm[(mm.station == st) & (mm.driver == "gdas1")].receptors
        ax.set_ylim(0, 108)
        ax.set_ylabel("Share of 120 h surface sensitivity (%)", fontsize=9)
        ax.set_title({"BKT": "Bukit Kototabang (BKT)", "JMB": "Jambi (JMB)"}[st] + f", {int(n.min())} to {int(n.max())} receptors per month",
                     loc="left", fontsize=10)
        ax.spines[["top", "right"]].set_visible(False)
    axes[1].set_xticks(range(1, 13))
    axes[1].set_xticklabels(pd.date_range("2025-01-01", periods=12, freq="MS").strftime("%b"))
    axes[1].set_xlabel("Month of 2025; bars per month: G = GDAS1 1°, E = ERA5 0.25°, F = GFS 0.25°", fontsize=9)
    fig.legend(loc="lower center", ncol=6, frameon=False, fontsize=8.5, bbox_to_anchor=(0.5, -0.005))
    fig.text(0.01, 0.985, title, ha="left", va="top", fontsize=12.5, weight="bold")
    fig.text(0.01, 0.948, highlight, ha="left", va="top", fontsize=9.5, color="#333")
    fig.tight_layout(rect=(0, 0.04, 1, 0.9))
    fig.savefig(path, dpi=300)
    fig.savefig(path.with_suffix(".pdf"))
    plt.close(fig)


def fig_obs(mo: pd.DataFrame, comp: pd.DataFrame, path: Path, title: str, highlight: str) -> None:
    import matplotlib.pyplot as plt
    gases = [("ch4", "CH$_4$", "ppb", "prior: local anthropogenic, wetlands, other natural"),
             ("co", "CO", "ppb", "prior: fire only (hotspot exposure)"),
             ("co2", "CO$_2$", "ppm", "prior: fossil only")]
    fig, axes = plt.subplots(2, 3, figsize=(12.5, 8.2))
    for i, st in enumerate(["BKT", "JMB"]):
        for j, (gas, lab, unit, what) in enumerate(gases):
            ax = axes[i, j]
            x = mo[(mo.station == st) & (mo.gas == gas)]
            for k in DRV:
                c = comp[(comp.station == st) & (comp.gas == gas) & (comp.driver == k)].iloc[0]
                ax.plot(x.observed_enhancement, x[f"model_{k}"], MARK[k], color=COLOR[k], ms=5, alpha=0.85, mfc="none" if k == "gdas1" else COLOR[k],
                        label=f"{NAME[k]}: r = {c.r_monthly:.2f} ({c.r_lo:.2f} to {c.r_hi:.2f})")
            ax.set_xlabel(f"Observed {lab} enhancement ({unit})", fontsize=9)
            ax.set_ylabel(f"Modelled {lab} enhancement ({unit})", fontsize=9)
            ax.set_title(f"{st}, {lab}; {what}", loc="left", fontsize=8.5)
            ax.legend(fontsize=7, frameon=False, loc="upper left")
            ax.tick_params(labelsize=8)
            ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.99, title, ha="left", va="top", fontsize=12.5, weight="bold")
    fig.text(0.01, 0.955, highlight, ha="left", va="top", fontsize=9.5, color="#333")
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(path, dpi=300)
    fig.savefig(path.with_suffix(".pdf"))
    plt.close(fig)


# ---------------------------------------------------------------- costs
def costs(r: pd.DataFrame) -> pd.DataFrame:
    """Download volume and wall time per year of record, and HYSPLIT CPU time per receptor.

    Wall time is first-to-last retrieval over the campaign (parallel transfers, CDS queue as it was on
    15-16 November 2026).  CPU time is the median runtime of the runs made in this campaign, all under the
    same contention (4 of ours plus up to 8 other HYSPLIT workers on 16 cores): GDAS1 from the seed -10 runs.
    """
    import re
    days = A.met_days()
    e = [json.loads(A.era5_grib(d, k).with_suffix(".grib.json").read_text()) for d in days for k in ("pl", "sfc", "fc")
         if A.era5_grib(d, k).with_suffix(".grib.json").exists()]
    ea = [json.loads(A.era5_arl(d).with_suffix(".json").read_text())["bytes"] for d in days if A.era5_arl(d).with_suffix(".json").exists()]
    g = [json.loads(A.gfs_path(d).with_name(A.gfs_path(d).name + ".json").read_text()) for d in days
         if A.gfs_path(d).with_name(A.gfs_path(d).name + ".json").exists()]
    gd = json.loads((H.MET / "manifest.json").read_text())["files"]
    gd25 = [f for f in gd if re.search(r"[a-z]{3}25\.w\d$", f["file"])]
    def wall_h_per_day(times, n):
        t = pd.to_datetime(times)
        return (t.max() - t.min()).total_seconds() / 3600 / max(n - 1, 1)
    run = r.groupby(["driver", "seed"]).runtime_s.median() / 3600
    ne = len({x["filename"][:8] for x in e if x["filename"].endswith("pl.grib")})
    gb25 = sum(f["bytes"] for f in gd25) / 1e9           # the 2025 weekly files hold exactly one year
    rows = [dict(driver="gdas1", download_gb_per_year=gb25, stored_gb_per_year=gb25,
                 files_2025=len(gd25), cpu_hours_per_receptor=run.get(("gdas1", A.SEED2)),
                 download_wall_hours_per_year=np.nan,
                 archive="NOAA READY gdas1 weekly files, global 1 degree, 2005 onward; GDAS model upgrades over the record")]
    rows.append(dict(driver="era5", download_gb_per_year=sum(x["bytes"] for x in e) / 1e9 / ne * 365,
                     stored_gb_per_year=(sum(x["bytes"] for x in e) / 1e9 / ne + np.mean(ea) / 1e9) * 365,
                     files_2025=ne, cpu_hours_per_receptor=run.get(("era5", 0)),
                     download_wall_hours_per_year=wall_h_per_day([x["retrieved_at_utc"] for x in e], ne) * 365,
                     archive="Copernicus CDS ERA5, 1940 onward, one frozen system"))
    rows.append(dict(driver="gfs0p25", download_gb_per_year=np.mean([x.get("archive_bytes") or x["bytes"] for x in g]) / 1e9 * 365,
                     stored_gb_per_year=np.mean([x["bytes"] + (x.get("archive_bytes") or 0) for x in g]) / 1e9 * 365,
                     files_2025=len(g), cpu_hours_per_receptor=run.get(("gfs0p25", 0)),
                     download_wall_hours_per_year=wall_h_per_day([x["retrieved_at_utc"] for x in g], len(g)) * 365,
                     archive="NOAA READY gfs0p25 crop, 13 June 2019 onward only"))
    c = pd.DataFrame(rows)
    c["cpu_hours_per_year_2_towers_daily"] = c.cpu_hours_per_receptor * 2 * 365
    return c


def analyse() -> None:
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    warnings.filterwarnings("ignore", message=".*constant.*")
    r = load()
    FIG.mkdir(parents=True, exist_ok=True)
    rec, mon, ann, noise = scale_tables(r)
    rec.to_csv(OUT / "diff_receptor_scale.csv", index=False)
    mon.to_csv(OUT / "diff_monthly_scale.csv", index=False)
    ann.to_csv(OUT / "diff_annual_scale.csv", index=False)
    mm = monthly_means(r); mm.to_csv(OUT / "monthly_means.csv", index=False)
    tu = transport_uncertainty(r, noise); tu.to_csv(OUT / "transport_uncertainty.csv", index=False)
    comp, mo = obs_comparison(r)
    comp.to_csv(OUT / "obs_comparison.csv", index=False); mo.to_csv(OUT / "obs_comparison_monthly.csv", index=False)
    pb = pbl_table(r); pb.to_csv(OUT / "pbl_mixing.csv", index=False)
    co = costs(r); co.to_csv(OUT / "cost.csv", index=False)
    sh = mon[mon.metric.str.startswith("share_") & mon.pair.str.endswith("vs gdas1")]
    fig_shares(mm, FIG / "driver_monthly_province_share.png",
               "Driver choice moves monthly province shares by several percentage points",
               f"Monthly mean share of 2025 surface sensitivity per province group. Largest monthly difference from GDAS1: "
               f"{sh.max_abs_diff_pp.max():.0f} percentage points; particle noise (second seed) below "
               f"{sh.noise_floor_rms_pp.max():.1f} points.\nSame HYSPLIT-STILT settings and seed for all drivers; "
               "ERA5 and GFS meteorology cropped to 70 to 140°E, 25°S to 20°N.")
    fig_obs(mo, comp, FIG / "driver_modelled_vs_observed_monthly.png",
            "No driver tracks the observed monthly enhancement better within the uncertainty",
            "Monthly means 2025 on receptor days. Observed: afternoon (05 to 07 UTC) mean minus the month's 10th percentile. "
            "Modelled: footprint times prior inventory.\nr across months; brackets are 95% block-bootstrap intervals "
            "(weeks resampled). The model and observed baselines differ, so slopes and offsets are not biases.")
    cov = r.groupby(["driver", "seed", "station"]).size().unstack()
    cov.to_csv(OUT / "coverage.csv")
    print(cov.to_string())
    pd.set_option("display.width", 220)
    print(tu.round(1).to_string())


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("stage", choices=["operator", "analyse"])
    a = p.parse_args()
    operator() if a.stage == "operator" else analyse()
