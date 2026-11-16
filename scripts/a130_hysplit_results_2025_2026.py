#!/usr/bin/env python3
"""Results of the 2025-2026 HYSPLIT campaign at Jambi and Bukit Kototabang.

Three products, each tested on weeks it was not fitted to:

fire   Carbon monoxide in the two burning seasons (Aug-Oct 2025, Aug-Sep 2026).
       CO = season intercept + a * (HYSPLIT footprint x daily hotspots), a >= 0.
       a converts to a CO emission per detected hotspot (cell area x time), so
       the province totals follow.  Compared with: no fire information; daily
       hotspot counts in Jambi, Sumatera Selatan and Riau without any wind; the
       two-dimensional trajectory index (a124) on the 2026 days they share.
ch4    Methane at both towers over every 2025-2026 receptor, with the local
       anthropogenic inventory (Indonesia's reported national totals split to
       provinces, a100/a108) and, as the comparison, EDGAR v8.  CH4 = monthly
       intercept + m_anthro * anthropogenic + m_wet * wetlands + f * fire
       exposure, Gaussian priors on the multipliers (1 +- 0.5), so the result is
       a posterior multiplier with an interval; peat contributions follow from
       the peat-split operator columns.  No CarbonTracker-CH4 boundary exists
       after 2023, so the monthly intercept carries the background.
co2    The a113 inversion scored on 2023-2024 alone and on 2023-2025 with the
       a129 rows (CT2026 boundary), same candidates, folds and bootstrap.

Screens: endpoint survival >= 0.95 and GDAS1 PBLH >= 300 m at the tower at 06 UTC,
as in the earlier campaign.

Usage: a130_hysplit_results_2025_2026.py fire|ch4|co2|all
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import nnls

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G
import a127_hysplit_2025_2026 as H

TABLES = H.TABLES
OUT = G.OUT / "jambi2026" / "hysplit2025_2026"
OUT.mkdir(parents=True, exist_ok=True)
GROUPS = ["JAMBI", "SUMATERA SELATAN", "RIAU", "SUMATERA BARAT", "OTHER_IDN", "OUTSIDE"]
RNG = np.random.default_rng(20261008)
CELL_M2 = (0.25 * 111_320.0) ** 2          # times cos(lat) per row below
MW_CO = 28.01


def frame():
    f = pd.read_csv(TABLES / "footprint_operator_2025_2026.csv", parse_dates=["time_utc"])
    f["usable"] = (f.endpoint_survival_fraction >= 0.95) & (f.PBLH >= 300)
    f["season"] = f.time_utc.dt.year.astype(str)
    f["week"] = f.time_utc.dt.to_period("W-SUN").astype(str)
    return f


def week_bootstrap_rmse(err, err_base, weeks, reps=4000):
    labels = np.unique(weeks)
    idx = [np.flatnonzero(weeks == l) for l in labels]
    W = RNG.multinomial(len(idx), np.repeat(1 / len(idx), len(idx)), size=reps)
    cnt = np.array([len(i) for i in idx]); den = W @ cnt
    s = np.array([np.sum(err[i] ** 2) for i in idx]); sb = np.array([np.sum(err_base[i] ** 2) for i in idx])
    d = np.sqrt((W @ s) / den) - np.sqrt((W @ sb) / den)
    return np.quantile(d, [.025, .975])


# ---------------------------------------------------------------------- fire
def design(df, cols, seasons):
    X = df[cols].to_numpy(float)
    S = np.column_stack([(df.season == s).to_numpy(float) for s in seasons])
    return X, S


def fit_nn(X, S, y):
    """Season intercepts free, slopes nonnegative: project out intercepts then NNLS."""
    P = S @ np.linalg.pinv(S)
    Xr, yr = X - P @ X, y - P @ y
    a = nnls(Xr, yr)[0] if X.shape[1] else np.zeros(0)
    b = np.linalg.lstsq(S, y - X @ a, rcond=None)[0]
    return a, b


def cv(df, cols, seasons):
    pred = np.full(len(df), np.nan)
    for wk in df.week.unique():
        te = (df.week == wk).to_numpy()
        X, S = design(df, cols, seasons)
        a, b = fit_nn(X[~te], S[~te], df.co_obs.to_numpy()[~te])
        pred[te] = X[te] @ a + S[te] @ b
    return pred


def fire():
    f = frame()
    f = f[f.window.isin(["fire25", "fire26"]) & f.usable & f.co_obs.notna()].reset_index(drop=True)
    hs = pd.read_csv(G.ROOT.parent / "HOTSPOT" / "archived_hotspot_idn.csv")
    hs["date"] = pd.to_datetime(dict(year=hs.year, month=hs.month, day=hs.day))
    import a124_fire2026_receptor as A
    hsg = A.hotspots() if False else None   # (2026 only; the count null is rebuilt here for both seasons)
    import geopandas as gpd
    prov = gpd.read_file(A.PROV); prov["geometry"] = prov.geometry.make_valid()
    col = [c for c in prov.columns if prov[c].astype(str).str.upper().str.contains("JAMBI").any()][0]
    prov["NAME"] = prov[col].astype(str).str.upper().str.strip()
    h = hs[(hs.year >= 2025) & hs.lat.between(-6, 3) & hs.lon.between(98, 107)].copy()
    pts = gpd.GeoDataFrame(h, geometry=gpd.points_from_xy(h.lon, h.lat), crs=prov.crs)
    j = gpd.sjoin(pts, prov[["NAME", "geometry"]], how="left", predicate="within")
    h["province"] = j[~j.index.duplicated()]["NAME"].values
    for g in ["JAMBI", "SUMATERA SELATAN", "RIAU"]:
        c = h[h.province == g].groupby("date").size()
        f[f"n_{g}"] = [int(c.get(d, 0) + c.get(d - pd.Timedelta(days=1), 0)) for d in f.time_utc.dt.normalize()]
    rows, preds, pars, att = [], [], [], []
    for st in H.STATIONS:
        df = f[f.station == st].reset_index(drop=True)
        seasons = sorted(df.season.unique())
        models = {"null_intercept": [], "hotspot_count_no_wind": [f"n_{g}" for g in ["JAMBI", "SUMATERA SELATAN", "RIAU"]],
                  "hysplit_common": ["fireexp_total"],
                  "hysplit_2day": ["fireexp2_total"],
                  "hysplit_2day_peat_split": ["fireexp2_peat", "fireexp2_nonpeat"],
                  "hysplit_by_province": [f"fireexp_{g}" for g in ["JAMBI", "SUMATERA SELATAN", "RIAU"]] + ["fireexp_rest"]}
        df["fireexp2_nonpeat"] = df.fireexp2_total - df.fireexp2_peat
        df["fireexp_rest"] = df.fireexp_total - df[[f"fireexp_{g}" for g in ["JAMBI", "SUMATERA SELATAN", "RIAU"]]].sum(axis=1)
        P = {m: cv(df, c, seasons) for m, c in models.items()}
        # the 2-D trajectory index, on the 2026 days it covers
        tr = pd.read_csv(G.OUT / "jambi2026" / "fire2026" / "daily_exposure.csv", parse_dates=["day"])
        tr = tr[tr.station == st][["day", "E_total"]]
        df = df.assign(day=df.time_utc.dt.normalize()).merge(tr, on="day", how="left")
        y, weeks = df.co_obs.to_numpy(), df.week.to_numpy()
        for m, p in P.items():
            e = p - y
            r = dict(station=st, model=m, sample="both seasons", n=len(df), weeks=len(np.unique(weeks)),
                     rmse=float(np.sqrt(np.mean(e ** 2))), r2_cv=float(1 - np.sum(e ** 2) / np.sum((y - y.mean()) ** 2)))
            for base in ("null_intercept", "hotspot_count_no_wind"):
                eb = P[base] - y
                r[f"delta_vs_{base}"] = r["rmse"] - float(np.sqrt(np.mean(eb ** 2)))
                r[f"lo_vs_{base}"], r[f"hi_vs_{base}"] = week_bootstrap_rmse(e, eb, weeks)
            rows.append(r)
        # 2026-only comparison including the 2-D model
        d26 = df[(df.season == "2026") & df.E_total.notna()].reset_index(drop=True)
        if len(d26) > 10:
            p2d = cv(d26.assign(season="2026"), ["E_total"], ["2026"])
            ph = cv(d26.assign(season="2026"), ["fireexp_total"], ["2026"])
            p0 = cv(d26.assign(season="2026"), [], ["2026"])
            pc = cv(d26.assign(season="2026"), [f"n_{g}" for g in ["JAMBI", "SUMATERA SELATAN", "RIAU"]], ["2026"])
            y2, w2 = d26.co_obs.to_numpy(), d26.week.to_numpy()
            for m, p in (("null_intercept", p0), ("hotspot_count_no_wind", pc), ("trajectory_2d", p2d),
                         ("hysplit_common", ph)):
                e = p - y2
                r = dict(station=st, model=m, sample="2026 shared days", n=len(d26), weeks=len(np.unique(w2)),
                         rmse=float(np.sqrt(np.mean(e ** 2))), r2_cv=float(1 - np.sum(e ** 2) / np.sum((y2 - y2.mean()) ** 2)))
                eb = p2d - y2
                r["delta_vs_trajectory_2d"] = r["rmse"] - float(np.sqrt(np.mean(eb ** 2)))
                r["lo_vs_trajectory_2d"], r["hi_vs_trajectory_2d"] = week_bootstrap_rmse(e, eb, w2)
                rows.append(r)
        # full fit, bootstrap by week: slope -> emission per hotspot; attribution
        X, S = design(df, ["fireexp_total"], seasons)
        a, b = fit_nn(X, S, y)
        lat = np.radians(G.STATIONS[st][2])
        labels = np.unique(weeks); idx = [np.flatnonzero(weeks == l) for l in labels]
        boot = []
        for k in range(2000):
            pick = np.concatenate([idx[i] for i in RNG.integers(0, len(idx), len(idx))])
            boot.append(fit_nn(X[pick], S[pick], y[pick])[0][0])
        boot = np.array(boot)
        # slope is ppb per (hotspot * ppm per umol m-2 s-1) = 1000 x flux per hotspot in umol m-2 s-1
        def t_per_day(slope):
            return slope / 1000.0 * CELL_M2 * np.cos(lat) * 86400 * MW_CO * 1e-6 / 1e6
        pars.append(dict(station=st, slope_ppb=float(a[0]), slope_lo=float(np.quantile(boot, .025)),
                         slope_hi=float(np.quantile(boot, .975)), co_t_per_hotspot_day=float(t_per_day(a[0])),
                         co_t_lo=float(t_per_day(np.quantile(boot, .025))), co_t_hi=float(t_per_day(np.quantile(boot, .975))),
                         **{f"intercept_{s}": float(v) for s, v in zip(seasons, b)}))
        for s in seasons:
            q = df[df.season == s]
            hi = q[q.fireexp_total >= q.fireexp_total.median()]
            shares = {g: float(hi[f"fireexp_{g}"].sum() / hi.fireexp_total.sum()) for g in GROUPS}
            bs = []
            qw = hi.week.to_numpy(); lab = np.unique(qw); ix = [np.flatnonzero(qw == l) for l in lab]
            for k in range(2000):
                pk = np.concatenate([ix[i] for i in RNG.integers(0, len(ix), len(ix))])
                hh = hi.iloc[pk]
                bs.append([hh[f"fireexp_{g}"].sum() / hh.fireexp_total.sum() for g in GROUPS])
            bs = np.array(bs)
            for gi, g in enumerate(GROUPS):
                att.append(dict(station=st, season=s, group=g, share=shares[g], lo=float(np.quantile(bs[:, gi], .025)),
                                hi=float(np.quantile(bs[:, gi], .975)), n_days=len(hi),
                                fire_co_ppb_mean=float(a[0] * q[f"fireexp_{g}"].mean()),
                                peat_share=float(hi.fireexp_peat.sum() / hi.fireexp_total.sum()) if g == "JAMBI" else np.nan))
        preds.append(pd.DataFrame({"station": st, "time_utc": df.time_utc, "season": df.season, "observed": df.co_obs,
                                   **{m: p for m, p in P.items()}}))
    sk = pd.DataFrame(rows); sk.to_csv(OUT / "fire_skill.csv", index=False)
    pa = pd.DataFrame(pars); pa.to_csv(OUT / "fire_parameters.csv", index=False)
    at = pd.DataFrame(att); at.to_csv(OUT / "fire_attribution.csv", index=False)
    pd.concat(preds).to_csv(OUT / "fire_cv_predictions.csv", index=False)
    # province CO totals Aug-Sep 2026 and Aug-Sep 2025 from the Jambi-tower slope (the better-constrained one)
    tot = []
    for s, (d0, d1) in {"2025": ("2025-08-01", "2025-09-30"), "2026": ("2026-08-01", "2026-09-30")}.items():
        q = h[(h.date >= d0) & (h.date <= d1)]
        for g in ["JAMBI", "SUMATERA SELATAN", "RIAU"]:
            nh = int((q.province == g).sum())
            for st in H.STATIONS:
                pr = pa[pa.station == st].iloc[0]
                tot.append(dict(season=s, province=g, hotspots=nh, from_station=st,
                                co_kt=nh * pr.co_t_per_hotspot_day / 1000, co_kt_lo=nh * pr.co_t_lo / 1000,
                                co_kt_hi=nh * pr.co_t_hi / 1000))
    pd.DataFrame(tot).to_csv(OUT / "fire_province_co_totals.csv", index=False)
    pd.set_option("display.width", 220)
    print(sk.round(3).to_string(index=False)); print(pa.round(3).to_string(index=False))
    print(at[at.share > 0.01].round(3).to_string(index=False))
    print(pd.DataFrame(tot).round(1).to_string(index=False))


# ----------------------------------------------------------------------- ch4
def ch4(prior="local"):
    """prior: local (Indonesia's reported totals split to provinces, a100/a108) or edgar (EDGAR v8 2022)."""
    col = "ch4_local" if prior == "local" else "ch4_anthro"
    f = frame()
    f = f[f.usable & f.ch4_obs.notna()].reset_index(drop=True)
    f["month"] = f.time_utc.dt.to_period("M").astype(str)
    rows, posts, budget = [], [], []
    for st in H.STATIONS:
        df = f[f.station == st].reset_index(drop=True)
        y = df.ch4_obs.to_numpy()
        months = sorted(df.month.unique())
        S = np.column_stack([(df.month == m).to_numpy(float) for m in months])
        K = df[[f"{col}_ppb", "ch4_wetlands_ppb", "fireexp_total"]].to_numpy(float)
        K = K.copy(); K[:, 2] = K[:, 2] * 1000.0          # fire: ppb per (hotspot x umol m-2 s-1)
        prior_mean = np.array([1.0, 1.0, 0.0])
        prior_sd = np.array([0.5, 0.5, 1.0])               # fire flux per hotspot: weak, in umol m-2 s-1

        def solve(tr, sigma):
            # Gaussian: theta = [multipliers..., intercepts...], intercepts flat (sd 1e4)
            A = np.column_stack([K[tr], S[tr]])
            mu = np.r_[prior_mean, np.full(S.shape[1], np.median(y[tr]))]
            sd = np.r_[prior_sd, np.full(S.shape[1], 1e4)]
            Pinv = np.diag(1 / sd ** 2)
            Hm = A.T @ A / sigma ** 2 + Pinv
            cov = np.linalg.inv(Hm)
            th = cov @ (A.T @ y[tr] / sigma ** 2 + Pinv @ mu)
            return th, cov

        sigma = np.std(y - np.array([np.median(y[df.month == m]) for m in df.month]))
        for _ in range(5):                                  # error scale to reduced chi-square of one
            th, cov = solve(np.ones(len(df), bool), sigma)
            res = y - np.column_stack([K, S]) @ th
            dofs = len(df) - np.trace(np.column_stack([K, S]) @ cov @ np.column_stack([K, S]).T / sigma ** 2)
            sigma = float(np.sqrt(np.sum(res ** 2) / max(dofs, 1)))
        th, cov = solve(np.ones(len(df), bool), sigma)
        ratio = np.sqrt(np.diag(cov)[:3]) / prior_sd
        for i, name in enumerate(["anthropogenic", "wetlands", "fire_per_hotspot"]):
            posts.append(dict(station=st, parameter=name, prior=prior_mean[i], prior_sd=prior_sd[i], posterior=float(th[i]),
                              lo=float(th[i] - 1.96 * np.sqrt(cov[i, i])), hi=float(th[i] + 1.96 * np.sqrt(cov[i, i])),
                              posterior_over_prior_sd=float(ratio[i]), n=len(df), sigma_ppb=sigma))
        # cross-validated skill against month intercepts alone
        pred, pred0 = np.full(len(df), np.nan), np.full(len(df), np.nan)
        for wk in df.week.unique():
            te = (df.week == wk).to_numpy()
            thk, _ = solve(~te, sigma)
            pred[te] = np.column_stack([K, S])[te] @ thk
            for m in df.month[te].unique():
                mm = te & (df.month == m).to_numpy()
                tr_m = (~te) & (df.month == m).to_numpy()
                pred0[mm] = np.median(y[tr_m]) if tr_m.any() else np.median(y[~te])
        e, e0 = pred - y, pred0 - y
        lo, hi = week_bootstrap_rmse(e, e0, df.week.to_numpy())
        rows.append(dict(station=st, n=len(df), weeks=df.week.nunique(), rmse=float(np.sqrt(np.mean(e ** 2))),
                         rmse_null=float(np.sqrt(np.mean(e0 ** 2))), delta=float(np.sqrt(np.mean(e ** 2)) - np.sqrt(np.mean(e0 ** 2))),
                         lo=float(lo), hi=float(hi)))
        # posterior budget by season, with peat
        for season, q in df.groupby(df.window.map({"fire25": "musim kebakaran 2025", "fire26": "musim kebakaran 2026",
                                                    "co2_25": "2025 di luar musim kebakaran"})):
            budget.append(dict(station=st, period=season, n=len(q),
                               anthro_prior=q[f"{col}_ppb"].mean(), wetlands_prior=q.ch4_wetlands_ppb.mean(),
                               anthro_post=th[0] * q[f"{col}_ppb"].mean(), wetlands_post=th[1] * q.ch4_wetlands_ppb.mean(),
                               fire_post=th[2] * 1000 * q.fireexp_total.mean(),
                               peat_post=th[0] * q[f"{col}_peat_ppb"].mean() + th[1] * q.ch4_wetlands_peat_ppb.mean()
                               + th[2] * 1000 * q.fireexp_peat.mean(),
                               **{f"anthro_{g}": th[0] * q[f"{col}_{g}"].mean() for g in GROUPS},
                               **{f"wetlands_{g}": th[1] * q[f"ch4_wetlands_{g}"].mean() for g in GROUPS}))
    sfx = "" if prior == "local" else "_edgar"
    pd.DataFrame(rows).to_csv(OUT / f"ch4_skill{sfx}.csv", index=False)
    pd.DataFrame(posts).to_csv(OUT / f"ch4_posterior{sfx}.csv", index=False)
    pd.DataFrame(budget).to_csv(OUT / f"ch4_budget{sfx}.csv", index=False)
    pd.set_option("display.width", 220)
    for t in (rows, posts, budget):
        print(pd.DataFrame(t).round(3).to_string(index=False))


# ----------------------------------------------------------------------- co2
def co2():
    import a113_operational_service as S
    base = S.frames()["co2"]
    new = pd.read_csv(TABLES / "co2_operator_2025.csv", parse_dates=["time_utc"])
    new = new[new.transport_usable & new.time_utc.dt.hour.eq(6) & new.PBLH.ge(300) & new.co2_afternoon_mean.notna()].copy()
    new["observed"] = new.co2_afternoon_mean
    new["base"] = new.background_ppm + new.ocean_ppm + new.fire_ppm
    for c in ["gpp_ppm_seed_sd", "resp_ppm_seed_sd", "fossil_near_ppm_seed_sd", "background_ppm_seed_sd"]:
        new[c] = np.nan
    imputed = base[base.period == "2024"].groupby("station").ensemble_sd.median()
    new["ensemble_sd"] = new.station.map(imputed)
    new["seed_terms_available"] = 0
    new["seed_terms_imputed"] = True
    for code in ("BKT", "JMB"):
        member = new.station.eq(code).to_numpy(float)
        new[f"bio_net_{code}_ppm"] = (new.gpp_ppm + new.resp_ppm) * member
        new[f"bio_contrast_{code}_ppm"] = (new.gpp_ppm - new.resp_ppm) * member
    new["gas"], new["period"] = "co2", "2025"
    new["source_total"] = new.fossil_near_ppm + new.fossil_far_ppm + new.gpp_ppm + new.resp_ppm
    cols = [c for c in base.columns if c in new.columns]
    both = pd.concat([base, new[cols]], ignore_index=True).sort_values(["station", "time_utc"]).reset_index(drop=True)
    print("rows", base.groupby("station").size().to_dict(), "->", both.groupby("station").size().to_dict(), flush=True)
    # local inventory: Indonesia's reported fossil totals (a100) and peat drainage FOLU 3B1 (a101), from a131
    loc = pd.read_csv(TABLES / "co2_local_terms.csv", parse_dates=["time_utc"])
    local = both.merge(loc[["station", "time_utc", "local_fossil_ppm", "peat_drainage_ppm"]],
                       on=["station", "time_utc"], how="inner", validate="one_to_one")
    print("local rows", len(local), "of", len(both), flush=True)
    local["fossil_near_ppm"], local["fossil_far_ppm"] = local.local_fossil_ppm, 0.0
    local["folu_3b1_ppm"] = local.peat_drainage_ppm
    local["source_total"] = local.fossil_near_ppm + local.gpp_ppm + local.resp_ppm + local.folu_3b1_ppm
    local = local.drop(columns=["local_fossil_ppm", "peat_drainage_ppm"]).sort_values(["station", "time_utc"])
    preds, fits = [], []
    for name, fr in (("2023-2024", base), ("2023-2025", both), ("2023-2025 lokal", local)):
        for prospective in (False, True):
            p, _ = S.evaluate(fr.reset_index(drop=True), "co2", prospective)
            p["scenario"] = name
            preds.append(p)
        full = np.ones(len(fr), bool)
        winner, _ = S.select(fr.reset_index(drop=True), "co2", full)
        diag = S.fit_predict(fr.reset_index(drop=True), "co2", S.CANDIDATES[4], full)
        ns = len(diag["source_names"])
        sd = np.sqrt(np.diag(diag["posterior_cov"])[:ns])
        lo_ = np.exp(diag["theta"][:ns] - 1.96 * sd); hi_ = np.exp(diag["theta"][:ns] + 1.96 * sd)
        fits.append(dict(scenario=name, selected_model=winner.name, source_dofs=float(diag["source_dofs"]),
                         multipliers_lo=json.dumps(dict(zip(diag["source_names"], np.round(lo_, 3).tolist()))),
                         multipliers_hi=json.dumps(dict(zip(diag["source_names"], np.round(hi_, 3).tolist()))),
                         reduced_chi2=float(diag["chi"]), n=len(fr),
                         multipliers=json.dumps(dict(zip(diag["source_names"], np.round(np.exp(diag["theta"][:ns]), 3).tolist()))),
                         posterior_sd_log=json.dumps(dict(zip(diag["source_names"], np.round(sd, 3).tolist())))))
        print(fits[-1], flush=True)
    pred = pd.concat(preds, ignore_index=True)
    pred.to_csv(OUT / "co2_validation_predictions.csv", index=False)
    sk = pd.concat([S.score(g.drop(columns="scenario")).assign(scenario=s) for s, g in pred.groupby("scenario")],
                   ignore_index=True)
    sk.to_csv(OUT / "co2_validation_skill.csv", index=False)
    pd.DataFrame(fits).to_csv(OUT / "co2_fit_diagnostics.csv", index=False)
    new.to_csv(OUT / "co2_frame_2025.csv", index=False)
    cols = ["scenario", "protocol", "station", "n", "weeks", "rmse", "delta_boundary_state", "lo_boundary_state",
            "hi_boundary_state", "delta_boundary_offset", "lo_boundary_offset", "hi_boundary_offset", "coverage95"]
    print(sk[sk.model.eq("selected")][cols].round(2).to_string(index=False))


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("fire", "all"):
        fire()
    if what in ("ch4", "all"):
        ch4("local")
        ch4("edgar")
    if what in ("co2", "all"):
        co2()
