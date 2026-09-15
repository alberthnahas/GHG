#!/usr/bin/env python3
"""Peatland tests on the BKT + Jambi two-receptor inversion (a84).

peat    Rasterize GHG_INDONESIA/indonesia_peatlands.json (1,277 polygons, no
        attributes, provenance not recorded in the file) to peat area fraction
        on each tower's 0.25 degree footprint grid; compute the peat-weighted
        sensitivity of every receptor hour; test whether Jambi night methane
        and the unexplained night residual follow peat exposure; refit the
        inversion with a peat flux term.
season  Wet versus dry season nocturnal CH4:CO2 accumulation ratio at Jambi
        (added separately).

Outputs in outputs/hysplit/two_receptor/tables/peat_*.csv and inputs/peat_fraction_*.nc.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import geopandas as gpd
from rasterio import features
from rasterio.transform import from_origin
from shapely.geometry import shape
from scipy.stats import spearmanr
import a84_bkt_jmb_two_receptor as T
from bkt_methane_inverse import InverseProblem, chain_diagnostics

PEAT = T.ROOT / "GHG_INDONESIA/indonesia_peatlands.json"
F_REF = 0.01          # umol m-2 s-1 = 10 nmol m-2 s-1; prior median peat flux over mapped peat
PEAT_PRIOR_FACTOR = 10.
SUB = 20              # raster pixels per 0.25 degree cell edge


def peat_geometries() -> gpd.GeoSeries:
    data = json.loads(PEAT.read_text())
    if data.get("type") != "GeometryCollection":
        raise ValueError("Unexpected peat file structure")
    g = gpd.GeoSeries([shape(x) for x in data["geometries"]], crs="EPSG:4326")
    return g.buffer(0)  # repairs the self-intersecting polygons


def peat_fraction(code: str, geoms: gpd.GeoSeries) -> xr.DataArray:
    lat, lon = T.receptor_grid(code)
    res = .25 / SUB
    transform = from_origin(lon[0] - .125, lat[-1] + .125, res, res)
    raster = features.rasterize(((g, 1) for g in geoms), out_shape=(len(lat) * SUB, len(lon) * SUB),
                                transform=transform, fill=0, dtype="uint8")
    frac = raster.reshape(len(lat), SUB, len(lon), SUB).mean(axis=(1, 3))[::-1]  # north-up to ascending latitude
    da = xr.DataArray(frac, coords={"lat": lat, "lon": lon}, dims=("lat", "lon"), name="peat_fraction")
    da.attrs.update(units="1", source=str(PEAT.relative_to(T.ROOT)), method=f"{SUB}x{SUB} subcell rasterization")
    return da


def peat_operator() -> pd.DataFrame:
    geoms = peat_geometries()
    rows = []
    for code in T.STATIONS:
        frac = peat_fraction(code, geoms)
        frac.to_netcdf(T.INPUTS / f"peat_fraction_{code.lower()}.nc")
        with xr.open_dataset(T.INVERSION / f"spatial_operator_{code.lower()}.nc") as ds:
            fp = ds.footprint.load(); dist = ds.distance_km.values
        if not (np.allclose(fp.lat, frac.lat) and np.allclose(fp.lon, frac.lon)):
            raise ValueError("Peat fraction and footprint grids differ")
        _, rlat, rlon, _ = T.STATIONS[code]
        area_check = float((frac * T.ext.cell_area_km2(frac.lat.values, frac.lon.values)).sum()) if hasattr(T.ext, "cell_area_km2") else np.nan
        for i, stamp in enumerate(fp.receptor.values):
            f = fp.isel(receptor=i).values
            w = f * frac.values
            rows.append(dict(station=code, time_utc=pd.Timestamp(stamp), peat_sensitivity=w.sum(),
                             peat_sensitivity_50km=w[dist <= 50].sum(), peat_sensitivity_500km=w[dist <= 500].sum(),
                             peat_share_percent=100 * w.sum() / f.sum(),
                             peat_ppb=w.sum() * F_REF * 1000, peat_mapped_area_km2=area_check))
        print(code, "peat area on grid km2", round(area_check), flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(T.TABLES / "peat_operator.csv", index=False)
    return out


def proximity() -> pd.DataFrame:
    """Peat share of land within fixed radii of each tower, in a local UTM projection."""
    from shapely.geometry import Point
    from shapely.ops import unary_union
    geoms = peat_geometries()
    rows = []
    for code, epsg in (("JMB", 32748), ("BKT", 32747)):
        _, lat, lon, _ = T.STATIONS[code]
        near = geoms.cx[lon - 3:lon + 3, lat - 3:lat + 3].to_crs(epsg)
        union = unary_union(list(near.buffer(0)))
        tower = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326").to_crs(epsg).iloc[0]
        row = dict(station=code, inside_peat=bool(union.contains(tower)), nearest_peat_km=union.distance(tower) / 1000)
        for radius in (10, 25, 50, 100, 200):
            disc = tower.buffer(radius * 1000, resolution=64)
            row[f"peat_share_{radius}km_percent"] = 100 * disc.intersection(union).area / disc.area
        rows.append(row)
    total = gpd.GeoSeries(list(geoms), crs="EPSG:4326").to_crs("EPSG:6933").area.sum() / 1e6
    out = pd.DataFrame(rows).assign(polygons=len(geoms), mapped_peat_area_km2=total)
    out.to_csv(T.TABLES / "peat_proximity.csv", index=False)
    print(out.round(2).to_string(index=False))
    return out


def frame_with_peat() -> pd.DataFrame:
    op = pd.read_csv(T.TABLES / "operator_base.csv", parse_dates=["time_utc"])
    peat = pd.read_csv(T.TABLES / "peat_operator.csv", parse_dates=["time_utc"])
    op = op.merge(peat, on=["station", "time_utc"], validate="one_to_one")
    sec = (pd.read_csv(T.TABLES / "sector_responses_base.csv", parse_dates=["time_utc"])
           .groupby(["station", "time_utc", "source"]).prior_enhancement_ppb.mean().unstack("source").reset_index())
    op = op.merge(sec, on=["station", "time_utc"])
    pred = pd.read_csv(T.TABLES / "inversion_predictions.csv", parse_dates=["time_utc"]).query("case == 'joint_screened_sector'")
    op = op.merge(pred[["station", "time_utc", "posterior_median_ppb"]], on=["station", "time_utc"], how="left")
    op["hour"] = op.time_utc.dt.hour
    op["enhancement_ppb"] = op.ch4 - op.background_ppb
    op["residual_ppb"] = op.ch4 - op.posterior_median_ppb
    op["sensitivity_50km"] = op.sensitivity * op.within50_sensitivity_percent / 100
    return op


def diagnostics(op: pd.DataFrame) -> None:
    u = op[op.transport_usable]
    summary = u.groupby(["station", "hour"]).agg(n=("ch4", "size"), peat_share_percent=("peat_share_percent", "mean"),
        peat_sensitivity=("peat_sensitivity", "mean"), peat_sensitivity_50km=("peat_sensitivity_50km", "mean"),
        peat_ppb_at_10nmol=("peat_ppb", "mean"), enhancement_ppb=("enhancement_ppb", "mean"), residual_ppb=("residual_ppb", "mean")).reset_index()
    summary.to_csv(T.TABLES / "peat_summary_by_hour.csv", index=False)
    rows = []
    for (code, hour), g in u.groupby(["station", "hour"]):
        for target in ("enhancement_ppb", "residual_ppb"):
            for driver in ("peat_sensitivity", "peat_sensitivity_50km", "peat_share_percent", "sensitivity", "sensitivity_50km",
                           "CH4_FUEL_EXPLOITATION", "wetlands"):
                ok = g[[target, driver]].dropna()
                rho = spearmanr(ok[target], ok[driver]).statistic if len(ok) >= 6 else np.nan
                rows.append(dict(station=code, hour_utc=hour, target=target, driver=driver, n=len(ok), spearman=rho))
    pd.DataFrame(rows).to_csv(T.TABLES / "peat_correlations.csv", index=False)
    col = []
    for code, g in u.groupby("station"):
        for other in ("fuel_near_ppb", "other_near_ppb", "anthro_far_ppb", "wetlands_ppb", "sensitivity"):
            col.append(dict(station=code, pair=f"peat_ppb~{other}", spearman=spearmanr(g.peat_ppb, g[other]).statistic, n=len(g)))
    pd.DataFrame(col).to_csv(T.TABLES / "peat_collinearity.csv", index=False)
    print(summary.round(2).to_string(index=False))
    c = pd.DataFrame(rows); print(c[(c.station == "JMB")].pivot_table(index=["driver"], columns=["hour_utc", "target"], values="spearman").round(2).to_string())
    print(pd.DataFrame(col).round(2).to_string(index=False))


def fit(label, frame, train, evaluate, components, factors):
    k, b, base, names = T.design(frame, components)
    y = frame.ch4.to_numpy() - base
    sd = np.r_[np.log(factors), np.tile([20., 10.], b.shape[1] // 2)]
    scan = []
    for t in (.05, .1, .15, .2, .25, .3, .4, .5, .6, .8, 1.0):
        p = InverseProblem(k[train], b[train], y[train], T.covariance(frame, k, t)[np.ix_(train, train)], sd)
        scan.append((t, T.r75.reduced_chi_square(p, int(train.sum()))))
    chi = np.array([c for _, c in scan]); ts = np.array([t for t, _ in scan])
    transport = float(ts[0] if chi.max() < 1 else ts[-1] if chi.min() > 1 else np.interp(1.0, chi[::-1], ts[::-1]))
    r = T.covariance(frame, k, transport)
    p = InverseProblem(k[train], b[train], y[train], r[np.ix_(train, train)], sd)
    p.fit()
    chains, _ = p.sample()
    rh, ess = chain_diagnostics(chains)
    if np.max(rh) > 1.01 or np.min(ess) < 1000:
        raise RuntimeError(f"{label}: convergence inadequate Rhat={rh} ESS={ess}")
    samples = chains.reshape(-1, p.ndim); ns = k.shape[1]
    params = []
    for j, name in enumerate(components + names):
        v = np.exp(samples[:, j]) if j < ns else samples[:, j]
        q = np.quantile(v, [.025, .5, .975])
        row = dict(case=label, parameter=name, median=q[1], q025=q[0], q975=q[2], transport_fraction=transport,
                   variance_reduction_percent=100 * (1 - np.var(samples[:, j]) / sd[j] ** 2), rhat=rh[j], ess=ess[j])
        if name == "peat":
            row.update(flux_nmol_m2_s_median=q[1] * F_REF * 1000, flux_nmol_m2_s_q025=q[0] * F_REF * 1000, flux_nmol_m2_s_q975=q[2] * F_REF * 1000)
        params.append(row)
    corr = np.corrcoef(samples[:, :ns].T)
    if "peat" in components:
        i = components.index("peat")
        for j, name in enumerate(components):
            if j != i:
                params.append(dict(case=label, parameter=f"posterior_corr_peat_{name}", median=corr[i, j]))
    pred = base[None, :] + np.exp(samples[:, :ns]) @ k.T + samples[:, ns:] @ b.T
    median = np.median(pred, axis=0)
    night = frame.station.eq("JMB").to_numpy() & frame.time_utc.dt.hour.eq(18).to_numpy()
    evals = []
    for split, m in (("training", train), ("evaluation", evaluate), ("jmb_18utc_all", night)):
        for code in ("BKT", "JMB"):
            mm = m & frame.station.eq(code).to_numpy()
            if mm.sum() >= 3:
                err = median[mm] - frame.ch4.to_numpy()[mm]
                evals.append(dict(case=label, split=split, station=code, n=int(mm.sum()), bias_ppb=err.mean(),
                                  rmse_ppb=float(np.sqrt(np.mean(err ** 2))), transport_fraction=transport))
    return params, evals


def peat_inversion(op: pd.DataFrame) -> None:
    frame = op[op.transport_usable].reset_index(drop=True)
    holdout = frame.holdout.to_numpy(bool)
    jmb = frame.station.eq("JMB").to_numpy()
    night = jmb & frame.time_utc.dt.hour.eq(18).to_numpy()
    sec = T.SECTOR_COMPONENTS
    f2 = [2.] * len(sec)
    cases = [
        ("screened_sector", ~holdout & ~night, holdout & ~night, sec, f2),
        ("screened_sector_peat", ~holdout & ~night, holdout & ~night, sec + ["peat"], f2 + [PEAT_PRIOR_FACTOR]),
        ("all_hours_sector_peat", ~holdout, holdout, sec + ["peat"], f2 + [PEAT_PRIOR_FACTOR]),
        ("jmb_all_hours_peat", jmb & ~holdout, jmb & holdout, T.COMPONENTS + ["peat"], [2.] * 4 + [PEAT_PRIOR_FACTOR]),
    ]
    params, evals = [], []
    for case in cases:
        p, e = fit(case[0], frame, *case[1:]); params += p; evals += e
        print(case[0], "done", flush=True)
    pd.DataFrame(params).to_csv(T.TABLES / "peat_inversion_parameters.csv", index=False)
    pd.DataFrame(evals).to_csv(T.TABLES / "peat_inversion_evaluation.csv", index=False)
    P = pd.DataFrame(params)
    print(P[~P.parameter.str.startswith(("offset", "trend"))][["case", "parameter", "median", "q025", "q975", "transport_fraction",
          "variance_reduction_percent", "flux_nmol_m2_s_median", "flux_nmol_m2_s_q025", "flux_nmol_m2_s_q975"]].round(3).to_string(index=False))
    print(pd.DataFrame(evals).round(1).to_string(index=False))


# ------------------------------------------------------------------ season

NIGHT_HOURS = [20, 21, 22, 23, 0, 1, 2]
SEASONS = {"main": {"wet": [11, 12, 1, 2, 3, 4], "dry": [5, 6, 7, 8, 9, 10]},
           "core": {"wet": [12, 1, 2, 3], "dry": [6, 7, 8, 9]}}


def nightly_rates(code: str = "JMB") -> pd.DataFrame:
    """Per-night slopes exactly as a30_extra6.ch4_co2_signature (Finding 85), plus CO."""
    import ghg_common as G
    d = G.load_all()
    st = d[d.station == code].dropna(subset=["co2", "ch4"]).copy()
    night = st[st.hour_local.isin(NIGHT_HOURS)]
    night = night.assign(nid=(night.time_local - pd.Timedelta(hours=12)).dt.normalize())
    rows = []
    for nid, g in night.groupby("nid"):
        if len(g) < 5:
            continue
        x = np.arange(len(g))
        a = np.polyfit(x, g.co2.values, 1)[0]; b = np.polyfit(x, g.ch4.values, 1)[0]
        gc = g.dropna(subset=["co"])
        c = np.polyfit(np.arange(len(gc)), gc.co.values, 1)[0] if len(gc) >= 5 else np.nan
        rows.append(dict(station=code, night=nid, hours=len(g), co2_rate_ppm_h=a, ch4_rate_ppb_h=b, co_rate_ppb_h=c,
                         accumulating=a > 0.2, ratio_ppb_per_ppm=b / a if a > 0.2 else np.nan,
                         suspect_hours=int(g[["suspect_co2", "suspect_ch4"]].any(axis=1).sum())))
    out = pd.DataFrame(rows)
    out["month"] = out.night.dt.month
    return out


def block_median(values: pd.Series, weeks: pd.Series, rng, reps: int = 5000) -> np.ndarray:
    frame = pd.DataFrame(dict(v=values.to_numpy(), w=weeks.to_numpy())).dropna()
    groups = [g.v.to_numpy() for _, g in frame.groupby("w")]
    idx = rng.integers(0, len(groups), size=(reps, len(groups)))
    return np.array([np.median(np.concatenate([groups[i] for i in row])) for row in idx])


def season_test() -> None:
    rng = np.random.default_rng(20260915)
    nights = nightly_rates("JMB")
    nights["week"] = nights.night.dt.to_period("W").astype(str)
    acc = nights[nights.accumulating]
    check = pd.read_csv(T.ROOT / "outputs/p_ch4_co2_signature.csv").set_index("station").loc["JMB"]
    reproduced = dict(n=len(acc), median=round(float(acc.ratio_ppb_per_ppm.median()), 2))
    print("reproduction of Finding 85:", reproduced, "published:", int(check.n_nights), float(check.ch4_per_co2_ppb_ppm), flush=True)
    if reproduced["n"] != int(check.n_nights) or abs(reproduced["median"] - float(check.ch4_per_co2_ppb_ppm)) > .005:
        raise ValueError("Nightly ratio does not reproduce the published Jambi signature")
    nights.to_csv(T.TABLES / "jambi_night_rates.csv", index=False)
    rows, diffs = [], []
    for definition, split in SEASONS.items():
        boots = {}
        for season, months in split.items():
            g = nights[nights.month.isin(months)]; ga = g[g.accumulating]
            rec = dict(definition=definition, season=season, months="-".join(map(str, months)),
                       nights=len(g), accumulating_nights=len(ga), weeks=ga.week.nunique(),
                       accumulating_percent=100 * len(ga) / len(g))
            for col, subset in (("ratio_ppb_per_ppm", ga), ("ch4_rate_ppb_h", ga), ("co2_rate_ppm_h", ga), ("co_rate_ppb_h", ga),
                                ("ch4_rate_ppb_h_all_nights", g), ("co2_rate_ppm_h_all_nights", g)):
                src = col.replace("_all_nights", "")
                b = block_median(subset[src], subset.week, rng)
                boots[(season, col)] = b
                rec.update({f"{col}_median": float(subset[src].median()), f"{col}_ci_lo": float(np.percentile(b, 2.5)),
                            f"{col}_ci_hi": float(np.percentile(b, 97.5))})
            rec["ratio_iqr_lo"] = float(ga.ratio_ppb_per_ppm.quantile(.25)); rec["ratio_iqr_hi"] = float(ga.ratio_ppb_per_ppm.quantile(.75))
            rows.append(rec)
        for col in ("ratio_ppb_per_ppm", "ch4_rate_ppb_h", "co2_rate_ppm_h", "co_rate_ppb_h", "ch4_rate_ppb_h_all_nights", "co2_rate_ppm_h_all_nights"):
            dist = boots[("dry", col)] - boots[("wet", col)]
            wet = [r for r in rows if r["definition"] == definition and r["season"] == "wet"][0][f"{col}_median"]
            dry = [r for r in rows if r["definition"] == definition and r["season"] == "dry"][0][f"{col}_median"]
            diffs.append(dict(definition=definition, quantity=col, wet_median=wet, dry_median=dry, dry_minus_wet=dry - wet,
                              ci_lo=float(np.percentile(dist, 2.5)), ci_hi=float(np.percentile(dist, 97.5)),
                              fraction_dry_above_wet=float((dist > 0).mean())))
    summary = pd.DataFrame(rows); difference = pd.DataFrame(diffs)
    summary.to_csv(T.TABLES / "jambi_night_season_summary.csv", index=False)
    difference.to_csv(T.TABLES / "jambi_night_season_difference.csv", index=False)
    # consistency across individual seasons
    nights["season_label"] = [("dry %d" % n.year) if n.month in SEASONS["main"]["dry"] else
                              ("wet %d/%02d" % ((n.year, (n.year + 1) % 100) if n.month >= 11 else (n.year - 1, n.year % 100)))
                              for n in nights.night]
    acc = nights[nights.accumulating]
    by = nights.groupby("season_label").agg(nights=("night", "size"), first=("night", "min"), last=("night", "max"))
    by = by.join(acc.groupby("season_label").agg(accumulating=("night", "size"), ratio_median=("ratio_ppb_per_ppm", "median"),
                 ch4_rate_median=("ch4_rate_ppb_h", "median"), co2_rate_median=("co2_rate_ppm_h", "median"), co_rate_median=("co_rate_ppb_h", "median")))
    by = by.sort_values("first").reset_index()
    by.to_csv(T.TABLES / "jambi_night_season_by_year.csv", index=False)
    monthly = acc.groupby("month").agg(nights=("night", "size"), ratio_median=("ratio_ppb_per_ppm", "median"),
                                       ch4_rate_median=("ch4_rate_ppb_h", "median"), co2_rate_median=("co2_rate_ppm_h", "median"),
                                       co_rate_median=("co_rate_ppb_h", "median")).reset_index()
    monthly.to_csv(T.TABLES / "jambi_night_monthly.csv", index=False)
    # second method: within-night regression slopes of a1_ratios (r2 >= 0.7), same seasons
    slopes = pd.read_pickle(T.ROOT / "outputs/nightly_slopes.pkl")[("JMB", "ΔCH₄/ΔCO₂")].copy()
    slopes["night"] = pd.to_datetime(slopes.night); slopes["month"] = slopes.night.dt.month
    slopes["week"] = slopes.night.dt.to_period("W").astype(str)
    alt = []
    for definition, split in SEASONS.items():
        b = {}
        for season, months in split.items():
            g = slopes[slopes.month.isin(months)]
            b[season] = block_median(g.slope, g.week, rng)
            alt.append(dict(method="a1 within-night regression slope", definition=definition, season=season, nights=len(g),
                            median=float(g.slope.median()), ci_lo=float(np.percentile(b[season], 2.5)), ci_hi=float(np.percentile(b[season], 97.5))))
        dist = b["dry"] - b["wet"]
        alt.append(dict(method="a1 within-night regression slope", definition=definition, season="dry_minus_wet", nights=np.nan,
                        median=float(np.median(dist)), ci_lo=float(np.percentile(dist, 2.5)), ci_hi=float(np.percentile(dist, 97.5))))
    pd.DataFrame(alt).to_csv(T.TABLES / "jambi_night_season_alt_method.csv", index=False)
    pd.set_option("display.width", 250)
    cols = ["definition", "season", "nights", "accumulating_nights", "weeks", "ratio_ppb_per_ppm_median", "ratio_ppb_per_ppm_ci_lo", "ratio_ppb_per_ppm_ci_hi",
            "ch4_rate_ppb_h_median", "co2_rate_ppm_h_median", "co_rate_ppb_h_median", "ch4_rate_ppb_h_all_nights_median", "co2_rate_ppm_h_all_nights_median"]
    print(summary[cols].round(2).to_string(index=False))
    print(difference.round(3).to_string(index=False))
    print(by.round(2).to_string(index=False))
    print(monthly.round(2).to_string(index=False))
    print(pd.DataFrame(alt).round(2).to_string(index=False))


def main(stage: str) -> None:
    if stage in ("peat", "all"):
        peat_operator()
        op = frame_with_peat()
        diagnostics(op)
        peat_inversion(op)
    if stage in ("proximity", "all"):
        proximity()
    if stage in ("season", "all"):
        season_test()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["peat", "proximity", "season", "all"])
    main(parser.parse_args().stage)
