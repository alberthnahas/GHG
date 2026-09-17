#!/usr/bin/env python3
"""Scored improvement experiments for the daytime CO2 model (builds on a89 and a90).

Every variant uses the same receptors (06 UTC, transport usable, 12-14 WIB
observation mean, GFS mixing depth at least 300 m), the same withheld days and
the same fit, and is scored the same way:
  skill over all daytime hours, per tower: posterior, nuisance-only and
    plain background (offset and trend) RMSE and correlation;
  withheld-day RMSE per tower;
  transfer: multipliers fitted on BKT alone, scored on every Jambi hour.

Variants
  reference        a90 diag_3h_mixed: diagnostic biosphere, transport error scaled
                   by the sum of component magnitudes
  net_error        transport error scaled by |net modeled signal|, floor 1 ppm
  ch4_covariate    per-tower coefficient on the CH4 model residual at the same hour
                   (CH4 observation minus the a84 joint_screened_sector posterior),
                   Gaussian prior 0 +/- 0.1 ppm per ppb: shared transport error
  ch4_net          both of the above
  saturating_light gross uptake saturating as sw / (sw + 250 W m-2)
  q10_2            respiration Q10 = 2.0
  tower_biosphere  separate uptake and respiration factors for each tower, with the CH4 covariate
  bkt_wide_prior   as tower_biosphere with a factor-of-5 prior on the BKT biosphere factors
  bkt_no_local     as tower_biosphere with BKT biosphere exchange within 25 km removed
  bkt_local_split  as tower_biosphere with a separate net factor for BKT exchange within 25 km
  bkt_no_biosphere biosphere factors for Jambi only; BKT uses background, fossil and the CH4 covariate
  ch4_enhancement  as tower_biosphere with the CH4 enhancement (observation minus endpoint background) as covariate
  best_100         per-tower biosphere factors, per-tower transport fractions, CH4 residual covariate at Jambi and
                   CH4 enhancement covariate at BKT
  best_100_bkt_background  as best_100 with no BKT biosphere terms (valid now that fractions are per tower)
  best_h150, best_h300     as best_100 with BKT footprints released 150 m or 300 m above model ground (a92)
  best_2023_proxy, best_2024, best_all   the best configuration on the 2023 window, the 2024 window (a93) and both,
                   with the CH4 enhancement proxy as covariate at both towers so the periods are treated alike
  best_all_periods as best_all with an offset and trend fitted separately in each period, so no straight line
                   is extrapolated across the ten-month gap between them
  best_all_fire    as best_all with the CT-NRT fire term scaled by its own multiplier instead of held fixed in
                   the baseline, which matters only in the 2024 window: the 2023 window has no fire signal

Cross-validation: every variant is also scored by leave-one-date-out MAP fits
(both towers on a date withheld together, transport fraction fixed at the
full-fit value), which gives about twenty out-of-sample hours per tower.
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
from scipy.linalg import solve_triangular

import a84_bkt_jmb_two_receptor as T
import a89_bkt_jmb_co2 as C
import a90_bkt_jmb_co2_improved as I
from bkt_methane_inverse import chain_diagnostics

TABLES = T.TABLES
BIOSPHERE_VARIANTS = {"_saturating": dict(q10=I.Q10, k_light=250.), "_q10_2": dict(q10=2.0, k_light=None)}
CH4_COVARIATE_PRIOR = .1          # ppm CO2 per ppb CH4
NET_ERROR_FLOOR_PPM = 1.
SCAN = (.05, .1, .15, .2, .25, .3, .4, .5, .6, .8, 1.0)
TOWER_BIO = ["fossil_near", "fossil_far", "gpp_BKT", "resp_BKT", "gpp_JMB", "resp_JMB"]
LOCAL_RADIUS_KM = 25.
COMPONENT_SETS = {"diag": I.DIAG, "tower": TOWER_BIO, "tower_fire": TOWER_BIO + ["fire"],
                  "jmb_biosphere_fire": ["fossil_near", "fossil_far", "gpp_JMB", "resp_JMB", "fire"],
                  "no_local": ["fossil_near", "fossil_far", "gpp_BKTfar", "resp_BKTfar", "gpp_JMB", "resp_JMB"],
                  "local_split": ["fossil_near", "fossil_far", "bio_BKTnear", "gpp_BKTfar", "resp_BKTfar", "gpp_JMB", "resp_JMB"],
                  "jmb_biosphere": ["fossil_near", "fossil_far", "gpp_JMB", "resp_JMB"]}
VARIANTS = [  # label, biosphere file suffix, covariance, covariates, component set, prior factors
    ("reference", "", "sum", [], "diag", {}), ("net_error", "", "net", [], "diag", {}),
    ("ch4_covariate", "", "sum", ["ch4_residual_ppb"], "diag", {}), ("ch4_net", "", "net", ["ch4_residual_ppb"], "diag", {}),
    ("saturating_light", "_saturating", "sum", [], "diag", {}), ("q10_2", "_q10_2", "sum", [], "diag", {}),
    ("tower_biosphere", "", "sum", ["ch4_residual_ppb"], "tower", {}),
    ("bkt_wide_prior", "", "sum", ["ch4_residual_ppb"], "tower", {"gpp_BKT": 5., "resp_BKT": 5.}),
    ("bkt_no_local", "", "sum", ["ch4_residual_ppb"], "no_local", {}),
    ("bkt_local_split", "", "sum", ["ch4_residual_ppb"], "local_split", {}),
    ("bkt_no_biosphere", "", "sum", ["ch4_residual_ppb"], "jmb_biosphere", {}),
    ("ch4_enhancement", "", "sum", ["ch4_enhancement_ppb"], "tower", {})]
ROUND3 = ("tower_biosphere", "bkt_wide_prior", "bkt_no_local", "bkt_local_split")
ROUND4 = ("tower_biosphere", "bkt_no_biosphere", "ch4_enhancement")
BEST_COVARIATES = ["ch4_residual_ppb@JMB", "ch4_enhancement_ppb@BKT"]
PROXY_COVARIATES = ["ch4_proxy_ppb@JMB", "ch4_proxy_ppb@BKT"]
OPTIONS = {  # label: per-tower transport fractions, BKT release height (None = a84 100 m runs)
    "best_100": dict(per_tower=True, bkt_height=None), "best_100_bkt_background": dict(per_tower=True, bkt_height=None),
    "best_h150": dict(per_tower=True, bkt_height=150.), "best_h300": dict(per_tower=True, bkt_height=300.),
    "best_h150_bkt_background": dict(per_tower=True, bkt_height=150.), "best_h300_bkt_background": dict(per_tower=True, bkt_height=300.)}
VARIANTS += [("best_100", "", "sum", BEST_COVARIATES, "tower", {}), ("best_100_bkt_background", "", "sum", BEST_COVARIATES, "jmb_biosphere", {}),
             ("best_h150", "", "sum", BEST_COVARIATES, "tower", {}), ("best_h300", "", "sum", BEST_COVARIATES, "tower", {}),
             ("best_h150_bkt_background", "", "sum", BEST_COVARIATES, "jmb_biosphere", {}),
             ("best_h300_bkt_background", "", "sum", BEST_COVARIATES, "jmb_biosphere", {})]
VARIANTS += [("best_2023_proxy", "", "sum", PROXY_COVARIATES, "tower", {}), ("best_2024", "", "sum", PROXY_COVARIATES, "tower", {}),
             ("best_all", "", "sum", PROXY_COVARIATES, "tower", {}),
             ("best_2023_proxy_bkt_background", "", "sum", PROXY_COVARIATES, "jmb_biosphere", {}),
             ("best_2024_bkt_background", "", "sum", PROXY_COVARIATES, "jmb_biosphere", {}),
             ("best_all_bkt_background", "", "sum", PROXY_COVARIATES, "jmb_biosphere", {})]
VARIANTS += [("best_2024_fire", "", "sum", PROXY_COVARIATES, "tower_fire", {}),
             ("best_all_fire", "", "sum", PROXY_COVARIATES, "tower_fire", {}),
             ("best_all_fire_bkt_background", "", "sum", PROXY_COVARIATES, "jmb_biosphere_fire", {})]
OPTIONS.update({"best_2024_fire": dict(per_tower=True, period="2024"), "best_all_fire": dict(per_tower=True, period="all"),
                "best_all_fire_bkt_background": dict(per_tower=True, period="all")})
VARIANTS += [("best_all_periods", "", "sum", PROXY_COVARIATES, "tower", {}),
             ("best_all_periods_bkt_background", "", "sum", PROXY_COVARIATES, "jmb_biosphere", {})]
OPTIONS.update({"best_all_periods": dict(per_tower=True, period="all", per_period=True),
                "best_all_periods_bkt_background": dict(per_tower=True, period="all", per_period=True)})
OPTIONS.update({"best_2023_proxy": dict(per_tower=True, period="2023"), "best_2024": dict(per_tower=True, period="2024"),
                "best_all": dict(per_tower=True, period="all"), "best_2023_proxy_bkt_background": dict(per_tower=True, period="2023"),
                "best_2024_bkt_background": dict(per_tower=True, period="2024"), "best_all_bkt_background": dict(per_tower=True, period="all")})
ROUND6 = ("best_2023_proxy", "best_2024", "best_all", "best_2023_proxy_bkt_background", "best_2024_bkt_background", "best_all_bkt_background")
ROUND7 = ("best_all", "best_all_periods", "best_all_bkt_background", "best_all_periods_bkt_background")
ROUND8 = ("best_2024", "best_2024_fire", "best_all", "best_all_fire", "best_all_fire_bkt_background")
ROUND5A = ("best_100", "best_100_bkt_background")
ROUND5B = ("best_100", "best_100_bkt_background", "best_h150", "best_h300", "best_h150_bkt_background", "best_h300_bkt_background")
HEIGHT_COLUMNS = ["fossil_near_ppm", "fossil_far_ppm", "ocean_ppm", "fire_ppm", "bio_day_ppm", "bio_night_ppm", "gpp_ppm", "resp_ppm",
                  "background_ppm", "endpoint_survival_fraction", "transport_usable"]


def build_variants() -> None:
    for variant, settings in BIOSPHERE_VARIANTS.items():
        I.build_biosphere(variant, **settings)
        I.operator(variant)


def ch4_proxy(frame: pd.DataFrame) -> np.ndarray:
    """CH4 above the tower's own rolling clean-air baseline; defined for both windows (a93)."""
    import a93_bkt_jmb_co2_2024 as E
    import ghg_common as G
    values = np.full(len(frame), np.nan)
    for code in frame.station.unique():
        rows = frame.station.eq(code).to_numpy()
        record = G.apply_flags(G.load_station(code)).set_index("time_utc").sort_index()
        span = pd.date_range(frame.time_utc.min() - pd.Timedelta(days=E.CH4_BASELINE_DAYS),
                             frame.time_utc.max() + pd.Timedelta(days=E.CH4_BASELINE_DAYS), freq="h")
        proxy = E.ch4_enhancement_proxy(record.reindex(span), span)
        values[rows] = proxy.reindex(frame.loc[rows, "time_utc"]).to_numpy()
    return values


def frame_2024() -> pd.DataFrame:
    base = pd.read_csv(TABLES / "co2_operator_base_2024.csv", parse_dates=["time_utc"])
    obs = pd.read_csv(TABLES / "co2_afternoon_observations_2024.csv", parse_dates=["time_utc"])
    return base.merge(obs, on=["station", "time_utc"], validate="one_to_one")


def receptor_frame(variant: str = "", bkt_height: float | None = None, period: str = "2023") -> pd.DataFrame:
    base = pd.read_csv(TABLES / "co2_operator_base.csv", parse_dates=["time_utc"])
    diag = pd.read_csv(TABLES / f"co2_diagnostic_operator{variant}.csv", parse_dates=["time_utc"])
    obs = pd.read_csv(TABLES / "co2_afternoon_observations.csv", parse_dates=["time_utc"])
    ch4 = pd.read_csv(TABLES / "inversion_predictions.csv", parse_dates=["time_utc"]).query("case == 'joint_screened_sector'")
    ch4 = ch4.assign(ch4_residual_ppb=ch4.observed_ppb - ch4.posterior_median_ppb,
                     ch4_enhancement_ppb=ch4.observed_ppb - ch4.background_ppb)[["station", "time_utc", "ch4_residual_ppb", "ch4_enhancement_ppb"]]
    f = (base.merge(diag, on=["station", "time_utc"], validate="one_to_one").merge(obs, on=["station", "time_utc"], validate="one_to_one")
         .merge(ch4, on=["station", "time_utc"], how="left", validate="one_to_one"))
    if bkt_height is not None:
        height = pd.read_csv(TABLES / "co2_bkt_height_operator.csv", parse_dates=["time_utc"])
        height = height[height.release_height_m.eq(bkt_height)].set_index("time_utc")
        if height.empty:
            raise FileNotFoundError(f"No a92 operator rows for BKT at {bkt_height} m")
        bkt = f.station.eq("BKT")
        f = f[~bkt | f.time_utc.isin(height.index)].copy()
        rows = f.station.eq("BKT")
        for column in HEIGHT_COLUMNS:
            f.loc[rows, column] = height.loc[f.loc[rows, "time_utc"], column].to_numpy()
        f["transport_usable"] = f.transport_usable.astype(bool)
    f = f[f.transport_usable & f.time_utc.dt.hour.eq(6) & f.co2_afternoon_mean.notna() & (f.PBLH >= I.MIN_MIXING_DEPTH_M)]
    if f.ch4_residual_ppb.isna().any():
        raise ValueError("CH4 residual missing for a CO2 receptor")
    f = f.assign(period="2023")
    if period in ("2024", "all"):
        later = frame_2024()
        later = later[later.transport_usable & later.co2_afternoon_mean.notna() & (later.PBLH >= I.MIN_MIXING_DEPTH_M)].assign(period="2024")
        shared = [c for c in f.columns if c in later.columns]
        f = later[shared].copy() if period == "2024" else pd.concat([f[shared], later[shared]], ignore_index=True)
    f = f.sort_values(["station", "time_utc"]).reset_index(drop=True)
    f["ch4_proxy_ppb"] = ch4_proxy(f)
    if f.ch4_proxy_ppb.isna().any():
        raise ValueError("CH4 proxy missing for a CO2 receptor")
    for code in ("BKT", "JMB"):
        member = f.station.eq(code).astype(float)
        f[f"gpp_{code}_ppm"] = f.gpp_ppm * member
        f[f"resp_{code}_ppm"] = f.resp_ppm * member
    local = TABLES / f"co2_diagnostic_operator_local{int(LOCAL_RADIUS_KM)}.csv"
    if variant == "" and bkt_height is None and local.exists():
        # left join: the local-radius operator covers the 2023 receptors only, and an
        # inner join would silently drop every 2024 receptor from the frame
        receptors = len(f)
        f = f.merge(pd.read_csv(local, parse_dates=["time_utc"]), on=["station", "time_utc"], how="left", validate="one_to_one")
        if len(f) != receptors:
            raise ValueError(f"local operator merge changed the receptor count: {receptors} to {len(f)}")
        bkt = f.station.eq("BKT").astype(float)
        f["gpp_BKTfar_ppm"] = (f.gpp_ppm - f.gpp_near_ppm) * bkt
        f["resp_BKTfar_ppm"] = (f.resp_ppm - f.resp_near_ppm) * bkt
        f["bio_BKTnear_ppm"] = (f.gpp_near_ppm + f.resp_near_ppm) * bkt
    return f


def local_operator(radius_km: float = LOCAL_RADIUS_KM) -> None:
    """Diagnostic-biosphere contribution from cells within radius_km of each tower."""
    import xarray as xr
    from pyproj import Geod
    import a71_domain_budget_extension as ext
    base = pd.read_csv(TABLES / "co2_operator_base.csv", parse_dates=["time_utc"])
    with xr.open_dataset(I.INPUTS / "diagnostic_biosphere.nc") as ds:
        gpp = ds.gpp.values; resp = ds.resp.values; blat = ds.lat.values; blon = ds.lon.values
        stamps = pd.DatetimeIndex(ds.time.values)
    rows = []
    for code in T.STATIONS:
        lat, lon = T.receptor_grid(code)
        _, rlat, rlon, _ = T.STATIONS[code]
        glat, glon = np.meshgrid(blat, blon, indexing="ij")
        _, _, dist = Geod(ellps="WGS84").inv(np.full(glon.shape, rlon), np.full(glat.shape, rlat), glon, glat)
        near = dist / 1000 <= radius_km
        rows_i = np.flatnonzero(near.any(axis=1)); cols_j = np.flatnonzero(near.any(axis=0))
        m_lat = C.overlap_matrix(lat, blat, True)[rows_i]; m_lon = C.overlap_matrix(lon, blon)[cols_j]
        mask = near[np.ix_(rows_i, cols_j)]
        for stamp in sorted(base.loc[base.station.eq(code), "time_utc"]):
            members = []
            for seed in T.SEEDS:
                field, meta, actual = ext.read_footprint(T.run_dir(code, seed, stamp))
                hours = pd.DatetimeIndex(field.time.values)
                coarse = C.aggregate(field.values, m_lat, m_lon) * mask[None]
                idx = stamps.get_indexer(I.interval_end(hours)); i0, i1, w1 = I.temperature_weights(hours, stamps)
                g = gpp[np.ix_(idx, rows_i, cols_j)]
                r = (1 - w1)[:, None, None] * resp[np.ix_(i0, rows_i, cols_j)] + w1[:, None, None] * resp[np.ix_(i1, rows_i, cols_j)]
                members.append((float((coarse * g).sum()), float((coarse * r).sum())))
            m = np.asarray(members)
            rows.append(dict(station=code, time_utc=stamp, gpp_near_ppm=m[:, 0].mean(), resp_near_ppm=m[:, 1].mean()))
        print(f"local {radius_km:.0f} km operator {code} done: {int(near.sum())} cells", flush=True)
    pd.DataFrame(rows).to_csv(TABLES / f"co2_diagnostic_operator_local{int(radius_km)}.csv", index=False)


def net_covariance(frame: pd.DataFrame, k: np.ndarray, transport: float) -> np.ndarray:
    r = C.covariance(frame, np.zeros_like(k), transport)   # measurement, local and background terms
    hours = frame.time_utc.to_numpy(dtype="datetime64[s]").astype("int64") / 3600
    for code in frame.station.unique():
        m = frame.station.eq(code).to_numpy()
        lag = np.abs(hours[m][:, None] - hours[m][None, :])
        scale = transport * np.maximum(np.abs(k[m].sum(axis=1)), NET_ERROR_FLOOR_PPM)
        r[np.ix_(m, m)] += np.outer(scale, scale) * np.exp(-lag / 24)
    return r


def period_nuisance(frame: pd.DataFrame):
    """Offset and trend for each station and period, every trend centred on its own period.

    The a89 design measures the trend from the midpoint of the 2023 window, which
    puts an October 2024 receptor about 13 prior standard deviations along that
    line. Across a ten-month gap one straight line is not a meaningful parameter,
    so a frame that spans both periods gets its own offset and trend in each.
    """
    columns, names = [], []
    for code in sorted(frame.station.unique()):
        for period in sorted(frame.period.unique()):
            member = (frame.station.eq(code) & frame.period.eq(period)).to_numpy()
            if not member.any():
                continue
            inside = frame.time_utc[member]
            midpoint = inside.min() + (inside.max() - inside.min()) / 2
            weight = member.astype(float)
            columns += [weight, weight * (frame.time_utc - midpoint).dt.total_seconds().to_numpy() / (28 * 86400)]
            names += [f"offset_{code}_{period}", f"trend_{code}_{period}"]
    return np.column_stack(columns), names


def nuisance_design(frame: pd.DataFrame, components: list[str], covariates: list[str], per_period: bool = False):
    k, b, base, names = C.design(frame, components)
    stations = sorted(frame.station.unique())
    sd = list(np.tile([C.OFFSET_PRIOR_PPM, C.TREND_PRIOR_PPM], len(stations)))
    if per_period and "period" in frame.columns and frame.period.nunique() > 1:
        b, names = period_nuisance(frame)
        sd = list(np.tile([C.OFFSET_PRIOR_PPM, C.TREND_PRIOR_PPM], len(names) // 2))
    if "fire" in components:
        base = base - frame.fire_ppm.to_numpy()   # a89 folds fire into the baseline; a scaled fire term takes it back out
    plain = b.shape[1]
    columns = [b]
    for covariate in covariates:
        column, _, only = covariate.partition("@")   # "name@BKT" restricts the covariate to one tower
        for code in stations:
            if only and code != only:
                continue
            columns.append((frame.station.eq(code).to_numpy() * frame[column].to_numpy())[:, None])
            names.append(f"{column}_{code}"); sd.append(CH4_COVARIATE_PRIOR)
    return k, np.hstack(columns), base, names, np.asarray(sd), plain


def ridge(bmat, y, r, sd, mask):
    chol = np.linalg.cholesky(r[np.ix_(mask, mask)])
    bw = solve_triangular(chol, bmat[mask], lower=True); yw = solve_triangular(chol, y[mask], lower=True)
    return np.linalg.solve(bw.T @ bw + np.diag(1 / sd ** 2), bw.T @ yw)


def prior_sd(components: list[str], prior_factors: dict | None) -> np.ndarray:
    factors = prior_factors or {}
    return np.log([factors.get(c, C.MULTIPLIER_PRIOR_FACTOR) for c in components])


def per_tower_covariance(base_fn, fractions: dict):
    """Block covariance with a separate transport fraction for each tower (towers are independent)."""
    def covariance(frame, k, _unused=None):
        r = np.zeros((len(frame), len(frame)))
        for code, fraction in fractions.items():
            m = frame.station.eq(code).to_numpy()
            if m.any():
                r[np.ix_(m, m)] = base_fn(frame[m].reset_index(drop=True), k[m], fraction)
        return r
    return covariance


def crossing(ts, chi) -> float:
    ts, chi = np.asarray(ts), np.asarray(chi)
    return float(ts[0] if chi.max() < 1 else ts[-1] if chi.min() > 1 else np.interp(1.0, chi[::-1], ts[::-1]))


def tune_per_tower(frame, k, b, y, sd, train, base_fn, passes: int = 3) -> dict:
    stations = list(dict.fromkeys(frame.station))
    if not all(np.diff(np.flatnonzero(frame.station.eq(code))).max(initial=1) == 1 for code in stations):
        raise ValueError("Per-tower tuning needs rows grouped by tower")
    fractions = {code: .3 for code in stations}
    trained = frame.station.to_numpy()[train]
    for _ in range(passes):
        for code in stations:
            chis = []
            for t in SCAN:
                trial = {**fractions, code: t}
                r = per_tower_covariance(base_fn, trial)(frame, k)
                p = C.SignedInverseProblem(k[train], b[train], y[train], r[np.ix_(train, train)], sd)
                theta, _, _ = p.fit()
                res = p.residual(theta)[:int(train.sum())][trained == code]
                chis.append(float(res @ res / len(res)))
            fractions[code] = crossing(SCAN, chis)
    return fractions


def fit_general(label: str, frame: pd.DataFrame, train: np.ndarray, evaluate: np.ndarray, components: list[str],
                covariance_fn, covariates: list[str], prior_factors: dict | None = None, per_tower: bool = False,
                per_period: bool = False) -> dict:
    k, b, base, names, nuisance_sd, plain = nuisance_design(frame, components, covariates, per_period)
    obs = frame.co2_afternoon_mean.to_numpy()
    y = obs - base
    sd = np.r_[prior_sd(components, prior_factors), nuisance_sd]
    if per_tower:
        fractions = tune_per_tower(frame, k, b, y, sd, train, covariance_fn)
        covariance_fn = per_tower_covariance(covariance_fn, fractions)
        transport = float(np.mean(list(fractions.values())))
    else:
        chi = []
        for t in SCAN:
            p = C.SignedInverseProblem(k[train], b[train], y[train], covariance_fn(frame, k, t)[np.ix_(train, train)], sd)
            chi.append(C.reduced_chi_square(p, int(train.sum())))
        transport = crossing(SCAN, chi)
        fractions = {code: transport for code in frame.station.unique()}
    r = covariance_fn(frame, k, transport)
    p = C.SignedInverseProblem(k[train], b[train], y[train], r[np.ix_(train, train)], sd)
    p.fit()
    for draws, thin in ((12000, 3), (48000, 12)):
        chains, _ = p.sample(draws=draws, thin=thin)
        rh, ess = chain_diagnostics(chains)
        if np.max(rh) <= 1.01 and np.min(ess) >= 1000:
            break
    else:
        raise RuntimeError(f"{label}: convergence inadequate Rhat={rh} ESS={ess}")
    samples = chains.reshape(-1, p.ndim); ns = k.shape[1]
    params = []
    for j, name in enumerate(components + names):
        v = np.exp(samples[:, j]) if j < ns else samples[:, j]
        q = np.quantile(v, [.025, .5, .975])
        params.append(dict(case=label, parameter=name, median=q[1], q025=q[0], q975=q[2], transport_fraction=transport,
                           **{f"transport_{code}": v for code, v in fractions.items()}, rhat=rh[j], ess=ess[j]))
    posterior = np.median(base[None, :] + np.exp(samples[:, :ns]) @ k.T + samples[:, ns:] @ b.T, axis=0)
    models = {"posterior": posterior,
              "nuisance_only": base + b @ ridge(b, y, r, nuisance_sd, train),
              "plain_background": base + b[:, :plain] @ ridge(b[:, :plain], y, r, nuisance_sd[:plain], train),
              "prior": base + k.sum(axis=1)}
    predictions = pd.DataFrame(dict(case=label, station=frame.station, time_utc=frame.time_utc, training=train, evaluation=evaluate,
                                    observed_ppm=obs, **{f"{m}_ppm": v for m, v in models.items()}))
    return dict(params=params, predictions=predictions, transport=transport, fractions=fractions, covariance_fn=covariance_fn)


def cross_validate(label: str, frame: pd.DataFrame, components: list[str], covariance_fn, covariates: list[str], transport: float,
                   prior_factors: dict | None = None, per_period: bool = False) -> list[dict]:
    """Leave-one-date-out MAP predictions for the posterior, nuisance-only and plain background models."""
    k, b, base, names, nuisance_sd, plain = nuisance_design(frame, components, covariates, per_period)
    obs = frame.co2_afternoon_mean.to_numpy(); y = obs - base
    sd = np.r_[prior_sd(components, prior_factors), nuisance_sd]
    r = covariance_fn(frame, k, transport)
    dates = frame.time_utc.dt.normalize().to_numpy()
    pred = {m: np.full(len(frame), np.nan) for m in ("posterior", "nuisance_only", "plain_background")}
    for date in np.unique(dates):
        test = dates == date; train = ~test
        theta, _, _ = C.SignedInverseProblem(k[train], b[train], y[train], r[np.ix_(train, train)], sd).fit()
        ns = k.shape[1]
        pred["posterior"][test] = base[test] + k[test] @ np.exp(theta[:ns]) + b[test] @ theta[ns:]
        pred["nuisance_only"][test] = base[test] + b[test] @ ridge(b, y, r, nuisance_sd, train)
        pred["plain_background"][test] = base[test] + b[test, :plain] @ ridge(b[:, :plain], y, r, nuisance_sd[:plain], train)
    rows = []
    for code in frame.station.unique():
        m = frame.station.eq(code).to_numpy()
        for model, values in pred.items():
            e = values[m] - obs[m]
            rows.append(dict(variant=label, station=code, scope="leave_one_date_out", model=model, n=int(m.sum()),
                             rmse_ppm=float(np.sqrt(np.mean(e ** 2))), correlation=float(np.corrcoef(obs[m], values[m])[0, 1])))
    CV_PREDICTIONS.append(pd.DataFrame(dict(variant=label, station=frame.station, time_utc=frame.time_utc, observed_ppm=obs,
                                            **{f"{m}_ppm": v for m, v in pred.items()})))
    return rows


CV_PREDICTIONS: list[pd.DataFrame] = []
BOOTSTRAP_SEED, BOOTSTRAP_REPS = 20260915, 5000


def cv_difference_bootstrap(predictions: pd.DataFrame) -> pd.DataFrame:
    """Paired bootstrap over dates of the cross-validated RMSE difference, posterior minus plain background.

    Dates are resampled whole, so hours on the same day stay together; the number
    of distinct dates is the effective sample size reported with each interval.
    """
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    rows = []
    for (variant, code), g in predictions.groupby(["variant", "station"]):
        g = g.assign(date=g.time_utc.dt.normalize())
        dates = g.date.unique()
        e_post = (g.posterior_ppm - g.observed_ppm).to_numpy(); e_plain = (g.plain_background_ppm - g.observed_ppm).to_numpy()
        index = [np.flatnonzero(g.date.to_numpy() == d) for d in dates]
        diffs = np.empty(BOOTSTRAP_REPS)
        for i in range(BOOTSTRAP_REPS):
            take = np.concatenate([index[j] for j in rng.integers(0, len(dates), len(dates))])
            diffs[i] = np.sqrt(np.mean(e_post[take] ** 2)) - np.sqrt(np.mean(e_plain[take] ** 2))
        observed = np.sqrt(np.mean(e_post ** 2)) - np.sqrt(np.mean(e_plain ** 2))
        rows.append(dict(variant=variant, station=code, hours=len(g), dates=len(dates), rmse_difference_ppm=float(observed),
                         ci_lo=float(np.percentile(diffs, 2.5)), ci_hi=float(np.percentile(diffs, 97.5)),
                         fraction_posterior_better=float((diffs < 0).mean())))
    return pd.DataFrame(rows)


def score(result: dict, label: str, stations=("BKT", "JMB"), split_mask_name: str | None = None) -> list[dict]:
    rows = []
    pred = result["predictions"]
    for code in stations:
        for scope, mask in (("all_daytime", pred.station.eq(code)), ("withheld", pred.station.eq(code) & pred.evaluation & ~pred.training)):
            g = pred[mask]
            if len(g) < 3:
                continue
            for model in ("posterior", "nuisance_only", "plain_background", "prior"):
                e = g[f"{model}_ppm"] - g.observed_ppm
                rows.append(dict(variant=label, station=code, scope=scope, model=model, n=len(g), rmse_ppm=float(np.sqrt((e ** 2).mean())),
                                 correlation=float(np.corrcoef(g.observed_ppm, g[f"{model}_ppm"])[0, 1]) if g[f"{model}_ppm"].std() > 0 else np.nan))
    return rows


def experiments(names: tuple[str, ...] | None = None, suffix: str = "") -> None:
    covariances = {"sum": C.covariance, "net": net_covariance}
    params, scores, preds = [], [], []
    for label, variant, cov_name, covariates, component_set, prior_factors in VARIANTS:
        if names and label not in names:
            continue
        option = OPTIONS.get(label, {})
        f = receptor_frame(variant, option.get("bkt_height"), option.get("period", "2023"))
        hold = f.holdout.to_numpy(bool); bkt = f.station.eq("BKT").to_numpy(); jmb = ~bkt
        components = COMPONENT_SETS[component_set]; covariance_fn = covariances[cov_name]
        per_period = option.get("per_period", False)
        joint = fit_general(label, f, ~hold, hold, components, covariance_fn, covariates, prior_factors,
                            option.get("per_tower", False), per_period)
        params += joint["params"]; preds.append(joint["predictions"])
        scores += score(joint, label)
        scores += cross_validate(label, f, components, joint["covariance_fn"], covariates, joint["transport"], prior_factors, per_period)
        transfer = {"transport": np.nan}
        if component_set == "diag":   # tower-specific sets have Jambi factors a BKT-only fit cannot inform
            transfer = fit_general(f"{label}_bkt_to_jmb", f, bkt & ~hold, jmb, components, covariance_fn, covariates, prior_factors)
            params += transfer["params"]; preds.append(transfer["predictions"])
            scores += [row for row in score(transfer, f"{label}_bkt_to_jmb", stations=("JMB",)) if row["scope"] == "all_daytime"]
        print(f"{label}: receptors {len(f)} (BKT {int(f.station.eq('BKT').sum())}), transport fractions "
              f"{ {c: round(v, 3) for c, v in joint['fractions'].items()} } (transfer {transfer['transport']:.3f})", flush=True)
    P = pd.DataFrame(params); S = pd.DataFrame(scores)
    P.to_csv(TABLES / f"co2_experiments{suffix}_parameters.csv", index=False)
    cvp = pd.concat(CV_PREDICTIONS[-len([v for v in VARIANTS if not names or v[0] in names]):])
    cvp.to_csv(TABLES / f"co2_experiments{suffix}_cv_predictions.csv", index=False)
    boot = cv_difference_bootstrap(cvp)
    boot.to_csv(TABLES / f"co2_experiments{suffix}_cv_bootstrap.csv", index=False)
    print(boot.round(3).to_string(index=False), flush=True)
    S.to_csv(TABLES / f"co2_experiments{suffix}_skill.csv", index=False)
    pd.concat(preds).to_csv(TABLES / f"co2_experiments{suffix}_predictions.csv", index=False)
    pd.set_option("display.width", 250)
    cv = S[S.scope.eq("leave_one_date_out")].pivot_table(index=["variant", "station"], columns="model", values=["rmse_ppm", "correlation"])
    print(cv.round(2).to_string())
    keep = P[~P.parameter.str.startswith(("offset", "trend")) & ~P.case.str.endswith("bkt_to_jmb")]
    print(keep[["case", "parameter", "median", "q025", "q975"]].round(3).to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["build-variants", "experiments", "local-operator", "round3", "round4", "round5a", "round5b",
                                          "round6", "round7", "round8", "all"])
    stage = parser.parse_args().stage
    if stage in ("build-variants", "all"):
        build_variants()
    if stage in ("local-operator", "all"):
        local_operator()
    if stage in ("experiments", "all"):
        experiments()
    if stage == "round3":
        experiments(ROUND3, "_round3")
    if stage == "round4":
        experiments(ROUND4, "_round4")
    if stage == "round5a":
        experiments(ROUND5A, "_round5a")
    if stage == "round5b":
        experiments(ROUND5B, "_round5b")
    if stage == "round6":
        experiments(ROUND6, "_round6")
    if stage == "round7":
        experiments(ROUND7, "_round7")
    if stage == "round8":
        experiments(ROUND8, "_round8")


if __name__ == "__main__":
    main()
