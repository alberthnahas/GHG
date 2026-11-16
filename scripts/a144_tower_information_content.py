#!/usr/bin/env python3
"""What the two towers can and cannot constrain: a linear Gaussian design study for methane.

The report leaves two questions open (Appendix A, Q57 and Q60): how many source
parameters the observations inform independently, and how large an emission
change the network could detect. Both are questions about the information in
the network, not about a fitted answer, so they are answered here by a design
calculation on the operator that already exists. No transport is run.

Population. The 2025-2026 HYSPLIT-STILT campaign (a127, one seed, GDAS1, 06 UTC,
120 h back) is the only methane population that spans a full year at both
towers. Its receptors are screened exactly as a130 screens them (endpoint
survival at least 0.95, GDAS1 boundary layer at least 300 m, a valid afternoon
CH4 mean), giving 263 receptors at BKT and 213 at Jambi.

Jacobian. Every footprint is re-read and convolved, by emission month, with the
same prior fields a128 uses (the provincial reported inventory inside its
domain, EDGAR v8 outside it, LPJ-MERRA2 wetlands split on the mapped peat
fraction, and FIRMS hotspots on the footprint day). The prior contribution is
kept per province and per source class, so one table serves both partitions.
The per-receptor totals are checked against the a128 operator columns.

Observation error. The error is the measured model-data mismatch of the a130
methane model, which has exactly the nuisance structure used here (one
background intercept per tower per month): its leave-one-week-out residuals
are reproduced and their RMS is the error standard deviation. Their temporal
correlation is confined to the tower-week: pairs in the same week correlate
(about 0.23), pairs at the same lag in different weeks and consecutive weekly
means do not. The error covariance is therefore a week block (a common error
within a tower-week plus white noise, independent between weeks), with the
within-week share set so that the model reproduces the observed spread of weekly
mean residuals. An exponential in time with the length that matches that spread
was used first; it implies a correlation of about 0.27 between consecutive weekly
means that the residuals do not show, so it is kept only as a comparison variant
(suffix _exp).

Other operator tables were checked and not pooled: the 2023 table is 18 UTC
(01 WIB, night) receptors, and the 2024 table is a CO2 campaign run on GFS
0.25 degree meteorology with a two-seed ensemble, so neither shares this
population's transport or measured mismatch. CO2 is not attempted: no operator
splits CO2 by province or class, and the biosphere flux needs hourly convolution
of a flux that changes sign, which a monthly scaling-factor state does not fit.

Stages
  operator   per-receptor prior contribution by province, class and emission month
  errors     reproduce the a130 cross-validated residuals and fit the error model
  design     posterior covariance, averaging kernels, aggregation and detectability
  figures    annual uncertainty-reduction map and the degrees-of-freedom chart
             (300 dpi PNG in outputs/information_content/)

Detectability is the smallest sustained change in an aggregate emission that the
observations alone would separate from zero at 2 sigma: 2 / sqrt(1/posterior
variance - 1/prior variance), the prior's own information removed. It is a design
calculation under the stated error model.
  all        every stage in order
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G                                   # noqa: E402
import a127_hysplit_2025_2026 as H                       # noqa: E402
import a128_footprint_operator_2025_2026 as M            # noqa: E402

OUT = G.OUT / "information_content"
TABLES = H.TABLES
STATIONS = ("BKT", "JMB")
MW_CH4 = 16.04
CELL = 0.25 * 111_320.0                                  # m, as a128
ENERGY = ["BUILDINGS", "FUEL_EXPLOITATION", "IND_COMBUSTION", "IND_PROCESSES", "POWER_INDUSTRY", "TRANSPORT"]
CLASSES = ["wetland_peat", "wetland_mineral", "agriculture", "energy_industry", "waste", "fire"]
CLASS_LABEL = {"wetland_peat": "Wetland on peat", "wetland_mineral": "Wetland off peat",
               "agriculture": "Agriculture", "energy_industry": "Energy and industry",
               "waste": "Waste", "fire": "Fire (hotspots)"}
OUTSIDE = "OUTSIDE"
REST = "REST OF INDONESIA"
SUMATRA = ["ACEH", "SUMATERA UTARA", "SUMATERA BARAT", "RIAU", "KEPULAUAN RIAU", "JAMBI", "BENGKULU",
           "SUMATERA SELATAN", "KEPULAUAN BANGKA BELITUNG", "LAMPUNG"]
KEEP_PPB = 1.0          # a province is resolved separately if its mean prior signal reaches this at either tower
THRESHOLD = 0.5         # uncertainty reduction that counts as "established"
YEAR = 2025
SEASONS = {"JFM": [1, 2, 3], "AMJ": [4, 5, 6], "JAS": [7, 8, 9], "OND": [10, 11, 12]}


# ======================================================== operator (Jacobian)

@lru_cache(maxsize=2)
def region_index(code: str) -> tuple[np.ndarray, list[str]]:
    """Cell-centre province of every footprint cell, exactly as a128.province_index assigns it."""
    import geopandas as gpd
    lat, lon = M.grid(code)
    p = gpd.read_file(M.PROV)
    p["geometry"] = p.geometry.make_valid()
    col = [c for c in p.columns if p[c].astype(str).str.upper().str.contains("JAMBI").any()][0]
    p["NAME"] = p[col].astype(str).str.upper().str.strip()
    glat, glon = np.meshgrid(lat, lon, indexing="ij")
    pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(glon.ravel(), glat.ravel()), crs=p.crs)
    j = gpd.sjoin(pts, p[["NAME", "geometry"]], how="left", predicate="within")
    j = j[~j.index.duplicated()]
    name = j["NAME"].reindex(range(len(pts))).fillna(OUTSIDE).values
    names = sorted(p.NAME.unique()) + [OUTSIDE]
    lookup = {n: i for i, n in enumerate(names)}
    return np.array([lookup[n] for n in name]).reshape(glat.shape), names


@lru_cache(maxsize=2)
def local_sectors(code: str):
    """The a128 local inventory regridding, kept per sector instead of summed (umol m-2 s-1)."""
    lat, lon = M.grid(code)
    with xr.open_dataset(M.LOCAL_CH4) as ds:
        raw = {s: ds[s].values for s in M.LOCAL_SECTORS}
        la, lo = ds.lat.values, ds.lon.values
    total = sum(raw.values())
    glat, glon = np.meshgrid(la, lo, indexing="ij")
    i = np.round((glat - lat[0]) / (lat[1] - lat[0])).astype(int)
    k = np.round((glon - lon[0]) / (lon[1] - lon[0])).astype(int)
    ok = (i >= 0) & (i < len(lat)) & (k >= 0) & (k < len(lon)) & np.isfinite(total)
    cover = np.zeros((len(lat), len(lon)), bool)
    cover[i[ok], k[ok]] = True
    area = CELL ** 2 * np.cos(np.radians(lat))[:, None]
    out = {}
    for s, v in raw.items():
        grid = np.zeros((len(lat), len(lon)))
        np.add.at(grid, (i[ok], k[ok]), v[ok])
        out[s] = grid * 1000.0 / MW_CH4 / (365.25 * 86400) * 1e6 / area
    reference, ref_cover, _ = M.local_ch4(code)
    if not (np.allclose(sum(out.values()), reference, rtol=1e-10, atol=0) and np.array_equal(cover, ref_cover)):
        raise AssertionError("per-sector local inventory does not reproduce a128.local_ch4")
    return out, cover


@lru_cache(maxsize=2)
def class_fields(code: str) -> np.ndarray:
    """(12 calendar months, 5 non-fire classes, lat, lon) prior flux in umol m-2 s-1."""
    prior = M.ch4_prior(code)
    flux = prior.flux.values
    src = [str(s) for s in prior.source.values]
    loc, cover = local_sectors(code)
    pf = M.peat(code)
    out = np.zeros((12, 5) + pf.shape)
    for m in range(12):
        edgar = {s: flux[src.index(f"CH4_{s}"), m] for s in M.LOCAL_SECTORS}
        wet = flux[src.index("wetlands"), m]
        out[m, 0] = wet * pf
        out[m, 1] = wet * (1 - pf)
        out[m, 2] = np.where(cover, loc["AGRICULTURE"], edgar["AGRICULTURE"])
        out[m, 3] = np.where(cover, sum(loc[s] for s in ENERGY), sum(edgar[s] for s in ENERGY))
        out[m, 4] = np.where(cover, loc["WASTE"], edgar["WASTE"])
    return out


def receptor_rows(code: str, stamp: pd.Timestamp) -> list[dict]:
    """Prior contribution (ppb) by emission month, class and province for one receptor."""
    field, _, _ = M.T().ext.read_footprint(H.run_dir(code, stamp))
    f = field.values
    hours = pd.DatetimeIndex(field.time.values)
    ridx, names = region_index(code)
    flat = ridx.ravel()
    nr = len(names)
    fields = class_fields(code)
    first = hours[0].normalize() - pd.Timedelta(days=1)
    days, hg = M.hotspot_grid(code, str(first.date()), str(stamp.normalize().date()))
    di = ((hours.normalize() - days[0]) // pd.Timedelta(days=1)).astype(int)
    period = hours.to_period("M")
    rows = []
    for p in pd.unique(period):
        sel = np.flatnonzero(period == p)
        fm = f[sel].sum(axis=0)
        fire = sum(f[t] * hg[di[t]] for t in sel)
        cal = p.month - 1
        values = {c: np.bincount(flat, weights=(fm * fields[cal, k]).ravel(), minlength=nr) * 1000.0
                  for k, c in enumerate(CLASSES[:5])}
        values["fire_exposure"] = np.bincount(flat, weights=fire.ravel(), minlength=nr)
        values["sensitivity"] = np.bincount(flat, weights=fm.ravel(), minlength=nr)
        for r, name in enumerate(names):
            row = dict(station=code, time_utc=stamp, emission_month=str(p), region=name)
            row.update({k: float(v[r]) for k, v in values.items()})
            rows.append(row)
    return rows


def operator() -> pd.DataFrame:
    sel = pd.read_csv(TABLES / "footprint_operator_2025_2026.csv", parse_dates=["time_utc"])
    path = OUT / "a144_receptor_contributions.csv"
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for n, r in enumerate(sel.itertuples(), 1):
        rows += receptor_rows(r.station, r.time_utc)
        if n % 50 == 0:
            print(f"  {n} of {len(sel)} receptors", flush=True)
    table = pd.DataFrame(rows)
    table.to_csv(path, index=False)
    print(f"wrote {path}: {len(table)} rows", flush=True)
    check_operator(table, sel)
    prior_mass()
    return table


def check_operator(table: pd.DataFrame, sel: pd.DataFrame) -> pd.DataFrame:
    """Per-receptor totals against the a128 columns the same fields produced."""
    tot = table.groupby(["station", "time_utc"]).agg(
        local=("agriculture", "sum"), energy=("energy_industry", "sum"), waste=("waste", "sum"),
        wet_peat=("wetland_peat", "sum"), wet_min=("wetland_mineral", "sum"),
        fire=("fire_exposure", "sum"), sens=("sensitivity", "sum")).reset_index()
    tot["anthro"] = tot.local + tot.energy + tot.waste
    tot["wet"] = tot.wet_peat + tot.wet_min
    m = tot.merge(sel, on=["station", "time_utc"], validate="one_to_one")
    _, names = region_index("BKT")
    groups = {g: [g] for g in M.GROUPS[:4]}
    groups["OUTSIDE"] = [OUTSIDE]
    by = table.groupby(["station", "time_utc", "region"])[["agriculture", "energy_industry", "waste"]].sum().sum(axis=1)
    by = by.unstack("region").fillna(0.0)
    rows = []
    for ours, theirs in (("anthro", "ch4_local_ppb"), ("wet", "ch4_wetlands_ppb"), ("wet_peat", "ch4_wetlands_peat_ppb"),
                         ("fire", "fireexp_total"), ("sens", "sensitivity")):
        rel = np.abs(m[ours] - m[theirs]) / np.maximum(np.abs(m[theirs]), 1e-12)
        rows.append(dict(quantity=theirs, receptors=len(m), max_relative_difference=float(rel.max())))
    other = [n for n in names if n not in M.GROUPS[:4] and n != OUTSIDE]
    idx = m.set_index(["station", "time_utc"])
    for g in M.GROUPS:
        cols = groups.get(g, other)
        ours = by[[c for c in cols if c in by.columns]].sum(axis=1).reindex(idx.index)
        rel = np.abs(ours - idx[f"ch4_local_{g}"]) / np.maximum(np.abs(idx[f"ch4_local_{g}"]), 1e-9)
        rows.append(dict(quantity=f"ch4_local_{g}", receptors=len(m), max_relative_difference=float(np.nanmax(rel))))
    check = pd.DataFrame(rows)
    check.to_csv(OUT / "a144_operator_check.csv", index=False)
    print(check.to_string(index=False), flush=True)
    if (check.max_relative_difference > 1e-6).any():
        raise AssertionError("the re-derived operator does not reproduce a128")
    return check


def fire_flux_per_hotspot() -> float:
    """Nominal CH4 flux carried by one hotspot-day in its 0.25 degree cell (umol m-2 s-1).

    The 2025-2026 operator has no fire CH4 inventory; fire enters through FIRMS
    hotspots. The magnitude per hotspot is taken as the mean of the two a130
    posterior estimates. It is a nominal scale, so the fire prior has a size; it
    is not an independent inventory, and the fractional results for fire inherit it.
    """
    post = pd.read_csv(G.OUT / "jambi2026" / "hysplit2025_2026" / "ch4_posterior.csv")
    return float(post.loc[post.parameter.eq("fire_per_hotspot"), "posterior"].mean())


def prior_mass() -> pd.DataFrame:
    """Prior emission by province, class and month (Gg CH4), on each tower grid."""
    months = pd.period_range("2024-12", "2026-09", freq="M")
    phi = fire_flux_per_hotspot()
    rows = []
    for code in STATIONS:
        lat, lon = M.grid(code)
        ridx, names = region_index(code)
        area = CELL ** 2 * np.cos(np.radians(lat))[:, None] * np.ones((1, len(lon)))
        fields = class_fields(code)
        h = M.hotspots()
        i = np.round((h.lat.values - lat[0]) / (lat[1] - lat[0])).astype(int)
        k = np.round((h.lon.values - lon[0]) / (lon[1] - lon[0])).astype(int)
        ok = (i >= 0) & (i < len(lat)) & (k >= 0) & (k < len(lon))
        hp = pd.DataFrame(dict(region=ridx[i[ok], k[ok]], area=area[i[ok], k[ok]],
                               month=h.date.values[ok])).assign(month=lambda d: pd.DatetimeIndex(d.month).to_period("M"))
        for p in months:
            seconds = p.days_in_month * 86400.0
            for c in range(5):
                gg = np.bincount(ridx.ravel(), weights=(fields[p.month - 1, c] * area).ravel(), minlength=len(names))
                gg = gg * seconds * 1e-6 * MW_CH4 * 1e-9
                for r, name in enumerate(names):
                    rows.append(dict(grid=code, month=str(p), region=name, cls=CLASSES[c], prior_gg=float(gg[r])))
            q = hp[hp.month == p]
            gg = np.bincount(q.region, weights=q.area * phi * 86400.0 * 1e-6 * MW_CH4 * 1e-9, minlength=len(names))
            cnt = np.bincount(q.region, minlength=len(names))
            for r, name in enumerate(names):
                rows.append(dict(grid=code, month=str(p), region=name, cls="fire", prior_gg=float(gg[r]),
                                 hotspots=int(cnt[r])))
    table = pd.DataFrame(rows)
    table["fire_flux_per_hotspot_umol_m2_s"] = phi
    table.to_csv(OUT / "a144_prior_mass.csv", index=False)
    wide = table[table.region.ne(OUTSIDE)].groupby(["grid", "cls"]).prior_gg.sum().unstack("grid")
    print("prior mass inside Indonesia, Gg over the 22 months, by grid:\n" + wide.round(1).to_string(), flush=True)
    return table


# ========================================================= observation error

def screened() -> pd.DataFrame:
    """The a130 methane population: usable transport and a valid afternoon mean."""
    import a130_hysplit_results_2025_2026 as P
    f = P.frame()
    return f[f.usable & f.ch4_obs.notna()].reset_index(drop=True)


def errors() -> pd.DataFrame:
    """Reproduce the a130 leave-one-week-out methane residuals and fit the error model.

    The a130 model (monthly intercept per tower, Gaussian multipliers on the
    local anthropogenic, wetland and fire responses, error scaled to a reduced
    chi-square of one) is the existing project model with the same nuisance
    structure as this design. Its out-of-sample residual is therefore the
    measured mismatch the design has to live with. It is a conservative choice:
    part of that residual is the source error that the prior term represents.
    """
    f = screened()
    f["month"] = f.time_utc.dt.to_period("M").astype(str)
    rows, resid = [], []
    for st in ("JMB", "BKT"):
        df = f[f.station == st].reset_index(drop=True)
        y = df.ch4_obs.to_numpy()
        months = sorted(df.month.unique())
        S = np.column_stack([(df.month == m).to_numpy(float) for m in months])
        K = df[["ch4_local_ppb", "ch4_wetlands_ppb", "fireexp_total"]].to_numpy(float).copy()
        K[:, 2] *= 1000.0
        prior_mean, prior_sd = np.array([1.0, 1.0, 0.0]), np.array([0.5, 0.5, 1.0])

        def solve(tr, sigma):
            A = np.column_stack([K[tr], S[tr]])
            mu = np.r_[prior_mean, np.full(S.shape[1], np.median(y[tr]))]
            sd = np.r_[prior_sd, np.full(S.shape[1], 1e4)]
            Pinv = np.diag(1 / sd ** 2)
            cov = np.linalg.inv(A.T @ A / sigma ** 2 + Pinv)
            return cov @ (A.T @ y[tr] / sigma ** 2 + Pinv @ mu), cov

        sigma = np.std(y - np.array([np.median(y[df.month == m]) for m in df.month]))
        for _ in range(5):
            th, cov = solve(np.ones(len(df), bool), sigma)
            X = np.column_stack([K, S])
            res = y - X @ th
            dofs = len(df) - np.trace(X @ cov @ X.T / sigma ** 2)
            sigma = float(np.sqrt(np.sum(res ** 2) / max(dofs, 1)))
        pred = np.full(len(df), np.nan)
        for wk in df.week.unique():
            te = (df.week == wk).to_numpy()
            thk, _ = solve(~te, sigma)
            pred[te] = np.column_stack([K, S])[te] @ thk
        e = y - pred
        resid.append(pd.DataFrame(dict(station=st, time_utc=df.time_utc, week=df.week, month=df.month,
                                       observed=y, predicted=pred, residual=e)))
        rows.append(dict(station=st, receptors=len(df), weeks=int(df.week.nunique()),
                         cv_rmse_ppb=float(np.sqrt(np.mean(e ** 2))), in_sample_sigma_ppb=sigma,
                         residual_mean_ppb=float(e.mean())))
    resid = pd.concat(resid, ignore_index=True)
    resid.to_csv(OUT / "a144_cv_residuals.csv", index=False)
    model = pd.DataFrame(rows)
    published = pd.read_csv(G.OUT / "jambi2026" / "hysplit2025_2026" / "ch4_skill.csv").set_index("station")
    model["a130_published_rmse_ppb"] = model.station.map(published.rmse)
    if not np.allclose(model.cv_rmse_ppb, model.a130_published_rmse_ppb, rtol=1e-9):
        raise AssertionError("cross-validated residuals do not reproduce a130 ch4_skill.csv")
    # temporal correlation of the residuals: receptors are at 06 UTC, so lags are whole days
    acf, fits = [], []
    for st in ("JMB", "BKT"):
        g = resid[resid.station == st].sort_values("time_utc")
        day = (g.time_utc - pd.Timestamp("2025-01-01")).dt.days.to_numpy()
        e = g.residual.to_numpy() - g.residual.mean()
        lag = np.abs(day[:, None] - day[None, :])
        prod = e[:, None] * e[None, :]
        var = float(np.mean(e ** 2))
        for d in range(1, 15):
            m = lag == d
            n = int(m.sum() // 2)
            acf.append(dict(station=st, lag_days=d, pairs=n, correlation=float(prod[m].mean() / var) if n else np.nan))
        a = pd.DataFrame([r for r in acf if r["station"] == st])
        use = a[(a.lag_days <= 7) & (a.pairs >= 10)]
        grid = np.linspace(0.05, 20, 4000)
        loss = [np.sum(use.pairs * (use.correlation - np.exp(-use.lag_days / t)) ** 2) for t in grid]
        tau_lag = float(grid[int(np.argmin(loss))])
        # The lag fit uses one- to seven-day pairs and misses the weaker tail, so check it
        # against what the design actually consumes: the spread of weekly mean residuals.
        weeks = [w for _, w in g.groupby("week")]
        wd = [(w.time_utc - pd.Timestamp("2025-01-01")).dt.days.to_numpy() for w in weeks]
        obs_rms = float(np.sqrt(np.mean([w.residual.mean() ** 2 for w in weeks])))

        def weekly_rms(t):
            return float(np.sqrt(np.mean([var * np.exp(-np.abs(d[:, None] - d[None, :]) / t).mean() for d in wd])))
        scan = np.linspace(0.05, 30, 1200)
        rms = np.array([weekly_rms(t) for t in scan])
        tau_week = float(scan[int(np.argmin(np.abs(rms - obs_rms)))])
        # correlation between consecutive weekly means. The data put it near zero; the
        # exponential with the weekly-spread length (inherited model) puts it near 0.27,
        # which is why the design now uses the week-block model below.
        wm = g.assign(wk=g.week).groupby("wk", sort=False).residual.mean()
        wk_corr = float(np.corrcoef(wm.values[:-1], wm.values[1:])[0, 1])
        tau_used = max(tau_lag, tau_week)
        day_all = day
        W = np.zeros((len(weeks), len(g)))
        pos = {t: i for i, t in enumerate(g.time_utc)}
        for k, w in enumerate(weeks):
            W[k, [pos[t] for t in w.time_utc]] = 1.0 / len(w)
        S = W @ (var * np.exp(-np.abs(day_all[:, None] - day_all[None, :]) / tau_used)) @ W.T
        sdw = np.sqrt(np.diag(S))
        exp_consec = float(np.mean(np.diag(S / np.outer(sdw, sdw), 1)))
        # Week-block model: R_ij = s^2 [(1 - c) delta_ij + c * same_week_ij], zero across weeks.
        # c is set so the model reproduces the observed spread of weekly mean residuals,
        # which is the quantity the weekly design consumes.
        sd = float(np.sqrt(np.mean(g.residual.to_numpy() ** 2)))
        inv_n = float(np.mean([1.0 / len(w) for w in weeks]))
        c_block = float(np.clip((obs_rms ** 2 / sd ** 2 - inv_n) / (1.0 - inv_n), 0.0, 1.0))
        wk = g.week.to_numpy()
        same = (wk[:, None] == wk[None, :]) & ~np.eye(len(g), dtype=bool)
        diffw = (wk[:, None] != wk[None, :])
        lagm = np.abs(day_all[:, None] - day_all[None, :])
        fits.append(dict(station=st, correlation_length_lagfit_days=tau_lag,
                         correlation_length_days=tau_used,
                         correlation_length_rule="larger of the lag fit and the weekly-spread match (inherited exponential, comparison only)",
                         lag1_correlation=float(a.correlation.iloc[0]), lag2_correlation=float(a.correlation.iloc[1]),
                         same_week_pair_correlation=float(prod[same].mean() / var),
                         different_week_lag1to6_correlation=float(prod[diffw & (lagm <= 6) & (lagm >= 1)].mean() / var),
                         weekly_mean_rms_observed_ppb=obs_rms,
                         weekly_mean_rms_predicted_lagfit_ppb=weekly_rms(tau_lag),
                         weekly_mean_rms_predicted_used_ppb=weekly_rms(tau_used),
                         weekly_mean_rms_if_independent_ppb=float(np.sqrt(np.mean([var / len(w) for w in weeks]))),
                         consecutive_week_correlation=wk_corr,
                         consecutive_week_correlation_exponential_model=exp_consec,
                         week_block_correlation=c_block,
                         week_block_white_sd_ppb=sd * np.sqrt(1 - c_block),
                         week_block_weekly_sd_ppb=float(np.sqrt(np.mean([sd ** 2 * ((1 - c_block) / len(w) + c_block)
                                                                          for w in weeks]))),
                         error_model_used="week block: common error within a tower-week, independent between weeks"))
    pd.DataFrame(acf).to_csv(OUT / "a144_residual_autocorrelation.csv", index=False)
    model = model.merge(pd.DataFrame(fits), on="station")
    # the 2023 population, for comparison only: past-only replay of the selected predictor
    replay = pd.read_csv(G.OUT / "operational" / "revised" / "validation_skill.csv") \
        if (G.OUT / "operational" / "revised" / "validation_skill.csv").exists() else pd.DataFrame()
    if len(replay):
        r = replay[(replay.gas == "ch4") & (replay.protocol == "past_only") & (replay.model == "selected")]
        model["past_only_2023_rmse_ppb"] = model.station.map(r.set_index("station").rmse)
    model.to_csv(OUT / "a144_error_model.csv", index=False)
    print(model.round(3).to_string(index=False), flush=True)
    return model


# ==================================================================== design

def load_design_inputs():
    contrib = pd.read_csv(OUT / "a144_receptor_contributions.csv", parse_dates=["time_utc"])
    keep = screened()[["station", "time_utc", "ch4_obs", "week"]]
    contrib = contrib.merge(keep[["station", "time_utc"]], on=["station", "time_utc"])
    contrib["fire"] = contrib.fire_exposure * 1000.0 * fire_flux_per_hotspot()
    mass = pd.read_csv(OUT / "a144_prior_mass.csv")
    model = pd.read_csv(OUT / "a144_error_model.csv").set_index("station")
    return contrib, keep, mass, model


def provinces_kept(contrib: pd.DataFrame) -> list[str]:
    total = contrib.assign(all=contrib[CLASSES].sum(axis=1))
    per = total.groupby(["station", "time_utc", "region"])["all"].sum().groupby(["station", "region"]).mean()
    keep = sorted({r for (s, r), v in per.items() if v >= KEEP_PPB and r != OUTSIDE})
    return keep


def partition(contrib: pd.DataFrame, mass: pd.DataFrame, kind: str, kept: list[str]):
    """Long tables of the Jacobian (ppb per unit scaling) and prior mass (Gg) per state element."""
    c = contrib.copy()
    m = mass[mass.grid.eq("BKT")].copy()          # provinces lie inside both grids; OUTSIDE is grid-specific
    if kind == "province":
        lump = lambda r: r if (r in kept or r == OUTSIDE) else REST
        c["element"] = c.region.map(lump)
        c["value"] = c[CLASSES].sum(axis=1)
        m["element"] = m.region.map(lump)
        names = kept + [REST, OUTSIDE]
    else:
        # source classes inside Sumatra, where the towers look; the rest of Indonesia and
        # everything outside it are one element each, all classes together, so that a
        # class factor is not silently applied to South Asian rice or Bornean peat
        place = lambda r: "S" if r in SUMATRA else (OUTSIDE if r == OUTSIDE else REST)
        c = c.melt(id_vars=["station", "time_utc", "emission_month", "region"], value_vars=CLASSES,
                   var_name="cls", value_name="value")
        c["element"] = [k if place(r) == "S" else place(r) for k, r in zip(c.cls, c.region)]
        m["element"] = [k if place(r) == "S" else place(r) for k, r in zip(m.cls, m.region)]
        names = list(CLASSES) + [REST, OUTSIDE]
    jac = c.groupby(["station", "time_utc", "element", "emission_month"]).value.sum().reset_index()
    prior = m.groupby(["element", "month"]).prior_gg.sum()
    return jac, prior, names


def time_block(month: str, resolution: str) -> str:
    p = pd.Period(month, "M")
    if resolution == "month":
        return month
    if resolution == "season":
        q = (p.month - 1) // 3
        return f"{p.year}-{list(SEASONS)[q]}"
    return str(p.year)


def build(jac, prior, names, keep, model, resolution="month", obs="weekly", rmodel="block"):
    """Matrices for one partition at one state time resolution."""
    receptors = keep.sort_values(["station", "time_utc"]).reset_index(drop=True)
    rindex = {(s, t): i for i, (s, t) in enumerate(zip(receptors.station, receptors.time_utc))}
    j = jac.copy()
    j["block"] = j.emission_month.map(lambda m: time_block(m, resolution))
    blocks = sorted(j.block.unique())
    state = [(n, b) for n in names for b in blocks]
    sindex = {s: i for i, s in enumerate(state)}
    Hs = np.zeros((len(receptors), len(state)))
    rows = j.apply(lambda r: rindex[(r.station, r.time_utc)], axis=1).to_numpy()
    cols = np.array([sindex[(e, b)] for e, b in zip(j.element, j.block)])
    np.add.at(Hs, (rows, cols), j.value.to_numpy())
    # one background per tower per receptor month
    receptors["rmonth"] = receptors.time_utc.dt.to_period("M").astype(str)
    nuis = sorted(set(zip(receptors.station, receptors.rmonth)))
    Hn = np.zeros((len(receptors), len(nuis)))
    for i, key in enumerate(zip(receptors.station, receptors.rmonth)):
        Hn[i, nuis.index(key)] = 1.0
    # receptor-level error, independent between towers. "block" (used): a common error
    # within a tower-week plus white noise, zero across weeks, as the residuals show.
    # "exp" (inherited, comparison only): exponential in time with the weekly-spread length.
    day = (receptors.time_utc - pd.Timestamp("2025-01-01")).dt.days.to_numpy()
    R = np.zeros((len(receptors), len(receptors)))
    for st in STATIONS:
        mk = receptors.station.eq(st).to_numpy()
        sd = model.loc[st, "cv_rmse_ppb"]
        if rmodel == "exp":
            tau = model.loc[st, "correlation_length_days"]
            lag = np.abs(day[mk][:, None] - day[mk][None, :])
            R[np.ix_(mk, mk)] = sd ** 2 * np.exp(-lag / tau)
        else:
            c = model.loc[st, "week_block_correlation"]
            wk = receptors.week.to_numpy()[mk]
            R[np.ix_(mk, mk)] = sd ** 2 * ((1 - c) * np.eye(mk.sum()) + c * (wk[:, None] == wk[None, :]))
    if obs == "weekly":
        groups = list(receptors.groupby(["station", "week"]).indices.values())
        W = np.zeros((len(groups), len(receptors)))
        for g, idx in enumerate(groups):
            W[g, idx] = 1.0 / len(idx)
        Hs, Hn, R = W @ Hs, W @ Hn, W @ R @ W.T
    # prior mass per state element, for absolute units
    pm = prior.reset_index()
    pm["block"] = pm.month.map(lambda m: time_block(m, resolution))
    pm = pm.groupby(["element", "block"]).prior_gg.sum()
    mass = np.array([pm.get((n, b), 0.0) for n, b in state])
    months_in = j.groupby("block").emission_month.nunique()
    return dict(Hs=Hs, Hn=Hn, R=R, state=state, blocks=blocks, nuisance=nuis, mass=mass,
                n_obs=Hs.shape[0], months_in=months_in)


def prior_cov(state, frac, temporal):
    """Scaling-factor prior: frac per element and block, optionally correlated 3 months in time."""
    n = len(state)
    B = np.eye(n) * frac ** 2
    if temporal:
        for a in range(n):
            for b in range(n):
                if a != b and state[a][0] == state[b][0]:
                    ma, mb = pd.Period(state[a][1][:7], "M"), pd.Period(state[b][1][:7], "M")
                    B[a, b] = frac ** 2 * np.exp(-abs((ma - mb).n) / 3.0)
    return B


def posterior(d, frac, temporal, r_scale, bg_sd):
    Hs, Hn = d["Hs"], d["Hn"]
    Hfull = np.hstack([Hs, Hn])
    Bs = prior_cov(d["state"], frac, temporal)
    B = np.zeros((Hfull.shape[1],) * 2)
    ns = Hs.shape[1]
    B[:ns, :ns] = Bs
    B[ns:, ns:] = np.eye(Hn.shape[1]) * bg_sd ** 2
    Rinv = np.linalg.inv(d["R"] * r_scale)
    Binv = np.linalg.inv(B)
    A = np.linalg.inv(Hfull.T @ Rinv @ Hfull + Binv)
    As, Bss = A[:ns, :ns], B[:ns, :ns]
    kernel = np.eye(ns) - As @ np.linalg.inv(Bss)          # source block, nuisance marginalised
    return As, Bss, kernel


# r_scale multiplies the error covariance R: 2 is "R doubled", 4 is the error standard deviation doubled
VARIANTS = [dict(name=f"R{rs:g}_B{int(fr * 100)}{'_t3' if tc else ''}{'' if bg >= 1e3 else '_bg20'}",
                 r_scale=rs, frac=fr, temporal=tc, bg_sd=bg, rmodel="block")
            for rs in (1.0, 2.0, 4.0) for fr in (0.3, 0.5, 1.0) for tc in (False, True) for bg in (1e4, 20.0)]
# the inherited exponential error model, kept only to show what replacing it changed
VARIANTS += [dict(name=f"R{rs:g}_B50_exp", r_scale=rs, frac=0.5, temporal=False, bg_sd=1e4, rmodel="exp")
             for rs in (1.0, 2.0)]
CENTRAL = "R1_B50"
# the variants whose aggregates and group search are written; every variant gets element and DOFS rows
KEY = {CENTRAL, "R2_B50", "R4_B50", "R1_B30", "R1_B100", "R1_B50_t3", "R1_B50_bg20", "R2_B30", "R2_B100",
       "R2_B50_t3", "R4_B30", "R4_B100", "R4_B50_t3", "R1_B50_exp"}
RECEPTOR_LEVEL = (CENTRAL, "R2_B50", "R4_B50", "R1_B50_exp")


def check_posterior(d) -> None:
    """Independent route to the central posterior: eliminate the free backgrounds by projection.

    With a flat background prior, the source posterior precision is
    Hs' [R^-1 - R^-1 Hn (Hn' R^-1 Hn)^-1 Hn' R^-1] Hs + B^-1. The 1e4 ppb background
    prior in posterior() approximates flat, so the two must agree closely.
    """
    Hs, Hn, R = d["Hs"], d["Hn"], d["R"]
    Ri = np.linalg.inv(R)
    P = Ri - Ri @ Hn @ np.linalg.solve(Hn.T @ Ri @ Hn, Hn.T @ Ri)
    Bs = prior_cov(d["state"], 0.5, False)
    A_proj = np.linalg.inv(Hs.T @ P @ Hs + np.linalg.inv(Bs))
    As, _, _ = posterior(d, 0.5, False, 1.0, 1e4)
    rel = float(np.max(np.abs(np.sqrt(np.diag(As)) / np.sqrt(np.diag(A_proj)) - 1)))
    print(f"  posterior check (projection vs joint inversion): max relative sd difference {rel:.2e}", flush=True)
    if rel > 1e-5:
        raise AssertionError("posterior does not match the projection solution")


def aggregate(As, Bs, d, members: list[str], months: list[str]):
    """Prior and posterior variance (Gg^2) of the emission summed over members and months."""
    g = np.array([d["mass"][i] if (e in members and b in months) else 0.0 for i, (e, b) in enumerate(d["state"])])
    prior, post = float(g @ Bs @ g), float(g @ As @ g)
    return float(g.sum()), prior, post


def periods(d) -> dict[str, dict[str, list[str]]]:
    months = [b for b in d["blocks"] if b.startswith(str(YEAR))]
    return {"month": {m: [m] for m in months},
            "season": {f"{YEAR}-{s}": [f"{YEAR}-{k:02d}" for k in v] for s, v in SEASONS.items()},
            "year": {str(YEAR): months}}


def detect(mass, prior, post):
    info = 1.0 / post - 1.0 / prior if post > 0 and prior > 0 else 0.0
    if info <= 1e-12 / max(prior, 1e-30):
        return np.inf
    return 2.0 / np.sqrt(info)


def design() -> None:
    contrib, keep, mass, model = load_design_inputs()
    kept = provinces_kept(contrib)
    print(f"provinces resolved separately (mean prior signal >= {KEEP_PPB} ppb at a tower): {kept}", flush=True)
    counts = keep.assign(month=keep.time_utc.dt.to_period("M").astype(str)).groupby(["station", "month"]).agg(
        receptors=("time_utc", "size"), weeks=("week", "nunique")).reset_index()
    allr = pd.read_csv(TABLES / "footprint_operator_2025_2026.csv", parse_dates=["time_utc"])
    allr["month"] = allr.time_utc.dt.to_period("M").astype(str)
    allr["has_ch4"] = allr.ch4_obs.notna()
    allr["transport_ok"] = (allr.endpoint_survival_fraction >= 0.95) & (allr.PBLH >= 300)
    base = allr.groupby(["station", "month"]).agg(footprints=("time_utc", "size"), with_ch4_obs=("has_ch4", "sum"),
                                                   transport_ok=("transport_ok", "sum")).reset_index()
    counts = base.merge(counts, on=["station", "month"], how="left").fillna({"receptors": 0, "weeks": 0})
    counts.insert(0, "gas", "CH4")
    counts.to_csv(OUT / "a144_receptor_counts.csv", index=False)
    # mean prior signal per element, the size of what the towers have to see
    sig_rows = []
    elem_rows, agg_rows, dof_rows, corr_rows = [], [], [], []
    for kind in ("province", "class"):
        jac, prior, names = partition(contrib, mass, kind, kept)
        s = jac.groupby(["station", "time_utc", "element"]).value.sum().groupby(["station", "element"]).mean()
        sig_rows += [dict(partition=kind, station=st, element=e, mean_prior_signal_ppb=float(v)) for (st, e), v in s.items()]
        mats = {}
        for rmodel in ("block", "exp"):
            for resolution in ("month", "season", "year"):
                for obs in ("weekly", "receptor"):
                    mats[(resolution, obs, rmodel)] = build(jac, prior, names, keep, model, resolution, obs, rmodel)
        check_posterior(mats[("month", "weekly", "block")])
        for v in VARIANTS:
            for (resolution, obs, rmodel), d in mats.items():
                if rmodel != v["rmodel"]:
                    continue
                if obs == "receptor" and v["name"] not in RECEPTOR_LEVEL:
                    continue
                if resolution != "month" and v["temporal"]:
                    continue
                As, Bs, K = posterior(d, v["frac"], v["temporal"], v["r_scale"], v["bg_sd"])
                inyear = np.array([b.startswith(str(YEAR)) for _, b in d["state"]])
                dof_rows.append(dict(partition=kind, variant=v["name"], error_model=v["rmodel"], r_scale=v["r_scale"],
                                     prior_fraction=v["frac"], temporal_3month=v["temporal"],
                                     background_sd_ppb=v["bg_sd"], resolution=resolution, obs=obs,
                                     n_obs=d["n_obs"], n_state=len(d["state"]),
                                     dofs_all=float(np.trace(K)), dofs_2025=float(np.trace(K[np.ix_(inyear, inyear)])),
                                     parameters_2025=int(inyear.sum())))
                if resolution != "month" or obs != "weekly":
                    continue
                psd, bsd = np.sqrt(np.diag(As)), np.sqrt(np.diag(Bs))
                for i, (e, b) in enumerate(d["state"]):
                    elem_rows.append(dict(partition=kind, variant=v["name"], element=e, month=b,
                                          prior_gg=d["mass"][i], prior_sd=bsd[i], posterior_sd=psd[i],
                                          uncertainty_reduction=1 - psd[i] / bsd[i], averaging_kernel=K[i, i]))
                if v["name"] not in KEY:
                    continue
                # aggregates: every element alone, every subset for the coarsest-necessary search
                per = periods(d)
                for ptype, labels in per.items():
                    for label, months in labels.items():
                        C = np.zeros((len(names), len(names))); P = np.zeros_like(C); tot = np.zeros(len(names))
                        g = np.zeros((len(names), len(d["state"])))
                        for i, (e, b) in enumerate(d["state"]):
                            if b in months:
                                g[names.index(e), i] = d["mass"][i]
                        C, P, tot = g @ As @ g.T, g @ Bs @ g.T, g.sum(axis=1)
                        n_months = len(months)
                        subsets = [s for k in range(1, len(names) + 1) for s in itertools.combinations(range(len(names)), k)]
                        if kind == "province":
                            subsets = [s for s in subsets if len(s) <= 4 or len(s) >= len(names) - 2] + []
                        for sub in subsets:
                            x = np.zeros(len(names)); x[list(sub)] = 1
                            prv, pst, ms = float(x @ P @ x), float(x @ C @ x), float(x @ tot)
                            if prv <= 0:
                                continue
                            dd = detect(ms, prv, pst)
                            agg_rows.append(dict(partition=kind, variant=v["name"], members="+".join(names[i] for i in sub),
                                                 n_members=len(sub), period_type=ptype, period=label, n_months=n_months,
                                                 prior_gg=ms, prior_sd_gg=np.sqrt(prv), posterior_sd_gg=np.sqrt(pst),
                                                 uncertainty_reduction=1 - np.sqrt(pst / prv),
                                                 detectable_2sigma_gg=dd, detectable_2sigma_gg_per_month=dd / n_months,
                                                 detectable_2sigma_fraction=dd / ms if ms > 0 else np.inf))
                        if v["name"] == CENTRAL and ptype in ("year", "month"):
                            sd = np.sqrt(np.diag(C))
                            R = C / np.outer(sd, sd)
                            for a in range(len(names)):
                                for b in range(len(names)):
                                    corr_rows.append(dict(partition=kind, period_type=ptype, period=label,
                                                          element_a=names[a], element_b=names[b],
                                                          posterior_correlation=float(R[a, b])))
        print(f"{kind}: {len(names)} elements; done", flush=True)
    pd.DataFrame(sig_rows).to_csv(OUT / "a144_prior_signal.csv", index=False)
    em = pd.DataFrame(elem_rows)
    em.to_csv(OUT / "a144_element_month.csv", index=False)
    # where the degrees of freedom sit: averaging-kernel diagonal summed over the 2025 months
    em[em.month.str.startswith(str(YEAR))].groupby(["partition", "variant", "element"]).agg(
        dofs_2025=("averaging_kernel", "sum"), months=("month", "size"),
        median_monthly_uncertainty_reduction=("uncertainty_reduction", "median"),
        max_monthly_uncertainty_reduction=("uncertainty_reduction", "max")).reset_index() \
        .to_csv(OUT / "a144_dofs_by_element.csv", index=False)
    pd.DataFrame(dof_rows).to_csv(OUT / "a144_dofs.csv", index=False)
    corr = pd.DataFrame(corr_rows)
    yearly = corr[corr.period_type.eq("year")]
    monthly = corr[corr.period_type.eq("month")].groupby(["partition", "element_a", "element_b"]).posterior_correlation \
        .median().reset_index().assign(period_type="month", period="median of 2025 months")
    pd.concat([yearly, monthly], ignore_index=True).to_csv(OUT / "a144_posterior_correlation.csv", index=False)
    agg = pd.DataFrame(agg_rows)
    agg.to_csv(OUT / "a144_aggregates.csv", index=False)
    summarise(agg)


def summarise(agg: pd.DataFrame) -> None:
    """Per element and group: month and season as medians over 2025, year as 2025."""
    def collapse(g):
        return pd.Series(dict(uncertainty_reduction=g.uncertainty_reduction.median(),
                              ur_min=g.uncertainty_reduction.min(), ur_max=g.uncertainty_reduction.max(),
                              periods_reaching=int((g.uncertainty_reduction >= THRESHOLD).sum()), periods=len(g),
                              prior_gg_per_month=(g.prior_gg / g.n_months).median(),
                              detectable_2sigma_gg_per_month=g.detectable_2sigma_gg_per_month.median(),
                              detectable_2sigma_fraction=g.detectable_2sigma_fraction.median()))
    s = agg.groupby(["partition", "variant", "members", "n_members", "period_type"]).apply(collapse, include_groups=False)
    s = s.reset_index()
    s.to_csv(OUT / "a144_summary.csv", index=False)
    # coarsest-necessary: the smallest groups whose median period reaches the threshold
    rows = []
    for (kind, var, ptype), g in s.groupby(["partition", "variant", "period_type"]):
        ok = g[g.uncertainty_reduction >= THRESHOLD]
        if ok.empty:
            rows.append(dict(partition=kind, variant=var, period_type=ptype, smallest_n=np.nan,
                             members="none reaches the threshold", uncertainty_reduction=g.uncertainty_reduction.max(),
                             note="largest reduction of any group shown"))
            continue
        n = ok.n_members.min()
        for r in ok[ok.n_members == n].nlargest(3, "uncertainty_reduction").itertuples():
            rows.append(dict(partition=kind, variant=var, period_type=ptype, smallest_n=int(n), members=r.members,
                             uncertainty_reduction=r.uncertainty_reduction,
                             detectable_2sigma_fraction=r.detectable_2sigma_fraction,
                             detectable_2sigma_gg_per_month=r.detectable_2sigma_gg_per_month, note=""))
    pd.DataFrame(rows).to_csv(OUT / "a144_coarsest_groups.csv", index=False)
    central = s[(s.variant == CENTRAL) & (s.n_members == 1)]
    pd.set_option("display.width", 250)
    print(central.pivot_table(index=["partition", "members"], columns="period_type",
                              values="uncertainty_reduction").round(3).to_string(), flush=True)
    print(pd.DataFrame(rows).query("variant == @CENTRAL").round(3).to_string(index=False), flush=True)


# =================================================================== figures

NE10 = Path("/usr/share/magics/10m")           # Natural Earth 1:10m, neighbouring-country context only
MAP_EXTENT = (94.5, 108.0, -7.0, 7.0)          # a109 SUMATRA frame, centred on the island


def sha256(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def figures() -> None:
    import warnings
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.patheffects as pe
    import matplotlib.pyplot as plt
    import geopandas as gpd
    from matplotlib.colors import BoundaryNorm, ListedColormap
    from shapely.geometry import box
    import a109_operational_maps as MAP
    s = pd.read_csv(OUT / "a144_summary.csv")
    counts = pd.read_csv(OUT / "a144_receptor_counts.csv")
    model = pd.read_csv(OUT / "a144_error_model.csv").set_index("station")
    n_rec = counts.groupby("station").receptors.sum().astype(int)
    year = s[(s.partition == "province") & (s.period_type == "year") & (s.n_members == 1)]
    # Indonesia from the shared project asset, repaired in memory only
    prov = gpd.read_file(M.PROV)
    broken = int((~prov.is_valid).sum())
    prov["geometry"] = prov.geometry.make_valid()
    prov["NAME"] = prov["provinsi"].astype(str).str.upper().str.strip()
    frame = box(MAP_EXTENT[0] - 1, MAP_EXTENT[2] - 1, MAP_EXTENT[1] + 1, MAP_EXTENT[3] + 1)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        land = gpd.read_file(NE10 / "ne_10m_land.shp")
        borders = gpd.read_file(NE10 / "ne_10m_admin_0_boundary_lines_land.shp")
    land = gpd.clip(land.assign(geometry=land.geometry.make_valid()), frame)
    idn = prov.clip(frame).geometry.union_all().buffer(0.02)
    neighbours = land.assign(geometry=land.geometry.difference(idn))
    neighbours = neighbours[~neighbours.is_empty]
    borders = gpd.clip(borders, frame)
    missing = sorted(set(year.members) - set(prov.NAME) - {REST, OUTSIDE})
    if missing:
        raise AssertionError(f"provinces in the design but not in the asset: {missing}")
    pd.DataFrame([dict(asset=str(M.PROV), sha256=sha256(M.PROV), invalid_geometries_repaired_in_memory=broken),
                  dict(asset=str(NE10 / "ne_10m_land.shp"), sha256=sha256(NE10 / "ne_10m_land.shp"),
                       invalid_geometries_repaired_in_memory=0),
                  dict(asset=str(NE10 / "ne_10m_admin_0_boundary_lines_land.shp"),
                       sha256=sha256(NE10 / "ne_10m_admin_0_boundary_lines_land.shp"),
                       invalid_geometries_repaired_in_memory=0)]) \
        .to_csv(OUT / "a144_figure_assets.csv", index=False)
    print(f"  repaired {broken} invalid province geometries (in memory only)", flush=True)

    panels = [(CENTRAL, "Measured mismatch error (central)"), ("R2_B50", "Error covariance R doubled")]
    edges = [0, .01, .02, .05, .1, .15, .2, .3, .5, 1.0]
    cmap = ListedColormap(matplotlib.colormaps["viridis"](np.linspace(.08, .97, len(edges) - 1)))
    norm = BoundaryNorm(edges, cmap.N)
    note = (f"Uncertainty reduction is 1 minus posterior over prior standard deviation of the province's 2025 methane "
            f"emission, all sources together. Linear Gaussian design on the 2025-2026 GDAS1 HYSPLIT-STILT footprints: "
            f"50% prior per province and month, uncorrelated; one free background per tower and month; weekly means of "
            f"{n_rec['BKT']} BKT and {n_rec['JMB']} Jambi afternoon (06 UTC) receptors; observation error from the "
            f"measured leave-one-week-out mismatch ({model.loc['BKT', 'cv_rmse_ppb']:.1f} ppb BKT, "
            f"{model.loc['JMB', 'cv_rmse_ppb']:.1f} ppb Jambi per receptor; weekly means "
            f"{model.loc['BKT', 'weekly_mean_rms_observed_ppb']:.1f} and {model.loc['JMB', 'weekly_mean_rms_observed_ppb']:.1f} ppb, "
            f"independent between weeks). Hatched provinces carry under {KEEP_PPB:g} ppb mean prior signal at both towers "
            f"and are one lumped element (value in the box). No province reaches 0.5. "
            f"A design calculation under the stated error model, not a measured detection.")
    fig, axes, cax = MAP.canvas(MAP_EXTENT, "A year of tower data narrows provincial methane emissions only slightly",
                                "Uncertainty reduction of each province's 2025 methane emission, Bukit Kototabang and "
                                "Jambi towers together", note, panels=2, width=10.0)
    for k, (ax, (var, title)) in enumerate(zip(axes, panels)):
        ax.set_facecolor(MAP.WATER)
        neighbours.plot(ax=ax, facecolor=MAP.LAND, edgecolor="#9A9A9A", linewidth=.3, zorder=1, rasterized=True)
        borders.plot(ax=ax, color="#9A9A9A", linewidth=.35, zorder=1.5)
        v = year[year.variant == var].set_index("members").uncertainty_reduction
        p = prov.assign(ur=prov.NAME.map(v))
        p[p.ur.isna()].plot(ax=ax, facecolor=MAP.STUDY, edgecolor=MAP.BOUNDARY, hatch="////", linewidth=.3, zorder=2)
        p[p.ur.notna()].plot(ax=ax, column="ur", cmap=cmap, norm=norm, edgecolor="#4A4A4A", linewidth=.35, zorder=4)
        ax.set_xlim(MAP_EXTENT[0], MAP_EXTENT[1]); ax.set_ylim(MAP_EXTENT[2], MAP_EXTENT[3])
        ax.set_xticks(np.arange(96, MAP_EXTENT[1] + .01, 4))
        ax.set_yticks(np.arange(-6, MAP_EXTENT[3] + .01, 2))
        ax.set_xticklabels([f"{t:.0f}°E" for t in ax.get_xticks()], fontsize=7)
        ax.set_yticklabels([f"{abs(t):.0f}°{'N' if t >= 0 else 'S'}" for t in ax.get_yticks()], fontsize=7)
        ax.grid(True, linestyle=":", linewidth=.35, color="#C9C9C9", zorder=3)
        ax.set_aspect("equal", adjustable="box")
        for r in p[p.ur.notna()].itertuples():
            clipped = r.geometry.intersection(box(*np.array(MAP_EXTENT)[[0, 2, 1, 3]]))
            if clipped.is_empty or clipped.area < 0.15:
                continue
            pt = clipped.representative_point()
            ax.annotate(f"{r.ur:.3f}", (pt.x, pt.y), ha="center", va="center", fontsize=6.6, color="#1A1A1A",
                        zorder=11, path_effects=[pe.withStroke(linewidth=2, foreground="white")])
        MAP.towers(ax, labels=(k == 0))
        MAP.title_of(ax, k, title)
        MAP.panel_note(ax, f"lumped rest of Indonesia {float(v.get(REST, np.nan)):.3f}\n"
                           f"outside Indonesia       {float(v.get(OUTSIDE, np.nan)):.3f}")
    sm = matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap)
    bar = fig.colorbar(sm, cax=cax, orientation="horizontal", ticks=edges, spacing="uniform")
    bar.set_label("Uncertainty reduction of the annual provincial emission (0 = prior only, 1 = fully determined; "
                  "0.5 is the threshold for an established total)", fontsize=7.4)
    bar.ax.tick_params(labelsize=6.8)
    out = OUT / "a144_ur_province_map.png"
    fig.savefig(out, dpi=300, facecolor="white")
    plt.close(fig)
    print(f"  -> {out}", flush=True)

    # degrees of freedom for signal by partition and state time resolution
    d = pd.read_csv(OUT / "a144_dofs.csv")
    d = d[d.obs == "weekly"]
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    res = ["month", "season", "year"]
    label = {"month": "Monthly state\n(12 per element)", "season": "Seasonal state\n(4 per element)",
             "year": "Annual state\n(1 per element)"}
    colours = {"province": "#0F6E8C", "class": "#C26A1B"}
    width = .36
    for j, kind in enumerate(("province", "class")):
        def pick(var):
            return d[(d.partition == kind) & (d.variant == var)].set_index("resolution").reindex(res)
        c, r2, r4 = pick(CENTRAL), pick("R2_B50"), pick("R4_B50")
        b30, b100 = pick("R1_B30"), pick("R1_B100")
        x = np.arange(3) + (j - .5) * width
        n_el = int(c.parameters_2025.loc["year"])
        ax.bar(x, c.dofs_2025, width=width * .92, color=colours[kind], zorder=2,
               label=f"{'Provinces' if kind == 'province' else 'Source classes'} ({n_el} elements), central")
        ax.vlines(x, b30.dofs_2025, b100.dofs_2025, color="#6B6B6B", linewidth=1.0, zorder=4,
                  label="Prior 30% to 100%" if j == 0 else None)
        ax.scatter(x, r2.dofs_2025, marker="o", s=22, facecolor="white", edgecolor="#1A1A1A", zorder=5,
                   label="R doubled" if j == 0 else None)
        ax.scatter(x, r4.dofs_2025, marker="_", s=200, color="#1A1A1A", zorder=5,
                   label="R x4 (error sd doubled)" if j == 0 else None)
        for xi, val, n, top in zip(x, c.dofs_2025, c.parameters_2025, b100.dofs_2025):
            ax.annotate(f"{val:.1f}\nof {n}", (xi, max(val, top)), xytext=(0, 3), textcoords="offset points",
                        ha="center", va="bottom", fontsize=7.2)
    ax.set_xticks(np.arange(3), [label[r] for r in res], fontsize=8)
    ax.set_ylabel("Degrees of freedom for signal, 2025 parameters", fontsize=8.5)
    dof_c = float(d[(d.partition == "province") & (d.variant == CENTRAL) & (d.resolution == "month")].dofs_2025.iloc[0])
    fig.suptitle(f"A year of tower data holds about {dof_c:.0f} independent pieces of methane emission information",
                 fontsize=9.5, x=.02, ha="left", weight="bold")
    ax.set_title(f"CH₄, weekly means at BKT and Jambi, 50% prior, measured mismatch error, free monthly background "
                 f"per tower; {n_rec.sum()} receptors", fontsize=7.2, color="#6B6B6B", loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=7.5)
    ax.legend(fontsize=7.0, frameon=False, loc="upper right")
    ax.set_ylim(0, d[d.variant.isin([CENTRAL, "R1_B100"])].dofs_2025.max() * 1.3)
    ax.grid(axis="y", linestyle=":", linewidth=.4, color="#C9C9C9", zorder=0)
    fig.tight_layout()
    out = OUT / "a144_dofs_by_partition.png"
    fig.savefig(out, dpi=300, facecolor="white")
    plt.close(fig)
    print(f"  -> {out}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["operator", "errors", "design", "figures", "all"])
    a = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if a.stage in ("operator", "all"):
        operator()
    if a.stage in ("errors", "all"):
        errors()
    if a.stage in ("design", "all"):
        design()
    if a.stage in ("figures", "all"):
        figures()


if __name__ == "__main__":
    main()
