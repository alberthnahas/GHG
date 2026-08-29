"""Findings 101-120: information content, robustness and network design.

This pass asks what can be learned without adding an external meteorological
model.  The analyses use paired observations, internal differences and
resampling by day or year.  They deliberately separate three questions that are
often conflated: whether a pattern is physically present, whether it is robust
to an analyst's baseline choice, and whether the observing system samples it
often enough to support an annual statement.

Every output is a CSV because prose is not the archive.  The functions are
small enough that the calculation behind each new finding can be audited in
isolation.  Raw JSON is never opened here; `outputs/all.pkl` is the sole hourly
input and is rebuilt by a0 before a full pipeline run.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

import ghg_common as G

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
SPECIES = ("co2", "ch4", "co")


def _save(df, name):
    df.to_csv(OUT / name, index=False)
    print(f"\n{name}\n", df.to_string(index=False))
    return df


def _paired(d, st, cols):
    x = d[d.station == st].copy()
    for c in cols:
        x = G.clean(x, c)
    return x.dropna(subset=list(cols))


def _daily_hysteresis(d, pair):
    """Signed polygon area of each complete daily tracer loop.

    Both axes are standardised within day, so the area measures timing rather
    than units or plume magnitude.  A day needs at least 18 distinct hours and
    all four six-hour quadrants; the bootstrap unit is therefore already a day.
    """
    xname, yname = pair
    rows = []
    for st in G.ORDER:
        x = _paired(d, st, pair)
        for day, g in x.groupby("date"):
            h = g.groupby("hour_local")[[xname, yname]].median().sort_index()
            if len(h) < 18 or len(set((h.index // 6).astype(int))) < 4:
                continue
            z = (h - h.mean()) / h.std(ddof=0)
            if not np.isfinite(z.values).all():
                continue
            xx, yy = z[xname].values, z[yname].values
            area = 0.5 * np.sum(xx * np.roll(yy, -1) - np.roll(xx, -1) * yy)
            rows.append(dict(station=st, date=day, signed_area=area))
    return pd.DataFrame(rows)


def hysteresis(d):
    rows = []
    for pair in (("co2", "ch4"), ("co2", "co")):
        z = _daily_hysteresis(d, pair)
        for st, g in z.groupby("station"):
            med = float(g.signed_area.median())
            rng = np.random.default_rng(101 + sum(map(ord, st + pair[1])))
            boots = [rng.choice(g.signed_area.values, len(g), replace=True).mean()
                     for _ in range(2000)]
            rows.append(dict(station=st, pair=f"{pair[0]}-{pair[1]}", n_days=len(g),
                             median_signed_area=round(med, 3),
                             mean_signed_area=round(float(g.signed_area.mean()), 3),
                             ci_low=round(float(np.quantile(boots, .025)), 3),
                             ci_high=round(float(np.quantile(boots, .975)), 3),
                             clockwise_fraction_pct=round(100 * float((g.signed_area < 0).mean()), 1)))
    return _save(pd.DataFrame(rows), "q_hysteresis.csv")


def hysteresis_season(d):
    z = _daily_hysteresis(d, ("co2", "ch4"))
    z["month"] = pd.to_datetime(z.date).dt.month
    z["season"] = np.where(z.month.isin([11, 12, 1, 2, 3, 4]), "wet_Nov-Apr", "dry_May-Oct")
    out = z.groupby(["station", "season"]).signed_area.agg(n_days="size", median="median", mean="mean").reset_index()
    out[["median", "mean"]] = out[["median", "mean"]].round(3)
    return _save(out, "q_hysteresis_season.csv")


def daynight_coupling(d):
    rows = []
    for st in G.ORDER:
        x = _paired(d, st, SPECIES)
        for period, mask in (("night_00-05", x.hour_local <= 5), ("afternoon_12-16", x.hour_local.between(12, 16))):
            g = x[mask]
            for a, b in (("co2", "ch4"), ("co2", "co"), ("ch4", "co")):
                rows.append(dict(station=st, period=period, pair=f"{a}-{b}", n_hours=len(g),
                                 pearson_r=round(float(g[a].corr(g[b])), 3),
                                 spearman_rho=round(float(spearmanr(g[a], g[b]).statistic), 3)))
    return _save(pd.DataFrame(rows), "q_daynight_coupling.csv")


def baseline_quantiles(d):
    rows = []
    for st in G.ORDER:
        x = d[d.station == st]
        for sp in SPECIES:
            g = G.clean(x, sp).dropna(subset=[sp])
            g = g[g.hour_local.between(12, 16)]
            vals = {q: float(g[sp].quantile(q)) for q in (.10, .20, .30)}
            rows.append(dict(station=st, species=sp, n_hours=len(g), q10=round(vals[.10], 3),
                             q20=round(vals[.20], 3), q30=round(vals[.30], 3),
                             q30_minus_q10=round(vals[.30]-vals[.10], 3)))
    return _save(pd.DataFrame(rows), "q_baseline_quantile.csv")


def afternoon_windows(d):
    rows = []
    for st in G.ORDER:
        x = d[d.station == st]
        for sp in SPECIES:
            g = G.clean(x, sp).dropna(subset=[sp])
            vals = {}
            for label, lo, hi in (("11-15", 11, 15), ("12-16", 12, 16), ("13-17", 13, 17)):
                vals[label] = float(g[g.hour_local.between(lo, hi)][sp].quantile(.20))
            rows.append(dict(station=st, species=sp, **{f"q20_{k}": round(v, 3) for k,v in vals.items()},
                             max_window_spread=round(max(vals.values())-min(vals.values()), 3)))
    return _save(pd.DataFrame(rows), "q_afternoon_window.csv")


def reference_sensitivity(d):
    rows = []
    # Compare like with like: all five stations overlap in 2023-2024.  Using
    # each station's full record would alias the secular trend into the ladder.
    dd = d[d.year.isin([2023, 2024])]
    for sp in SPECIES:
        lev = {}
        for st in G.ORDER:
            x = G.clean(dd[dd.station == st], sp).dropna(subset=[sp])
            lev[st] = float(x[x.hour_local.between(12, 16)][sp].quantile(.20))
        for ref in G.ORDER:
            order = sorted(G.ORDER, key=lambda s: lev[s]-lev[ref])
            for rank, st in enumerate(order, 1):
                rows.append(dict(species=sp, reference=ref, station=st, rank=rank,
                                 delta=round(lev[st]-lev[ref], 3)))
    return _save(pd.DataFrame(rows), "q_reference_sensitivity.csv")


def annual_rank_stability(d):
    rows = []
    for sp in SPECIES:
        yearly = {}
        for st in G.ORDER:
            x = G.clean(d[d.station == st], sp).dropna(subset=[sp])
            a = x[x.hour_local.between(12, 16)].groupby("year")[sp].quantile(.20)
            yearly[st] = a
        common_years = sorted(set.intersection(*[set(s.index) for s in yearly.values()]))
        for y in common_years:
            order = sorted(G.ORDER, key=lambda st: yearly[st].loc[y])
            for rank, st in enumerate(order, 1):
                rows.append(dict(species=sp, year=y, station=st, rank=rank,
                                 q20=round(float(yearly[st].loc[y]), 3)))
    return _save(pd.DataFrame(rows), "q_annual_rank.csv")


def uptime_gain():
    u = pd.read_csv(OUT / "p_uptime.csv")
    rows = []
    for st in G.ORDER:
        g = u[u.station == st]
        for sp in SPECIES:
            current = float(g[f"{sp}_pct"].median())
            for gain in (5, 10, 20):
                improved = min(100., current + gain)
                # Independent information scales approximately with valid n;
                # a mean/step standard error therefore scales as sqrt(n0/n1).
                factor = np.sqrt(current / improved) if current > 0 else np.nan
                rows.append(dict(station=st, species=sp, current_return_pct=round(current, 1),
                                 gain_points=gain, improved_return_pct=round(improved, 1),
                                 detection_threshold_factor=round(float(factor), 3),
                                 threshold_reduction_pct=round(100*(1-factor), 1)))
    return _save(pd.DataFrame(rows), "q_uptime_gain.csv")


def outage_seasonality(d):
    rows = []
    for st in G.ORDER:
        raw = d[d.station == st].sort_values("time_local").set_index("time_local")
        ix = pd.date_range(raw.index.min().floor("h"), raw.index.max().ceil("h"), freq="h")
        x = raw[list(SPECIES)].reindex(ix)
        x["month"] = x.index.month
        for sp in SPECIES:
            for m, g in x.groupby("month"):
                rows.append(dict(station=st, species=sp, month=int(m), n_expected=len(g),
                                 return_pct=round(100*float(g[sp].notna().mean()), 1)))
    return _save(pd.DataFrame(rows), "q_outage_season.csv")


def longest_gaps(d):
    rows = []
    for st in G.ORDER:
        x = d[d.station == st].sort_values("time_local")
        for sp in SPECIES:
            t = x.loc[x[sp].notna(), "time_local"].drop_duplicates().sort_values()
            gap = t.diff().dt.total_seconds().div(3600).sub(1)
            i = gap.idxmax()
            rows.append(dict(station=st, species=sp, longest_missing_hours=int(max(0, gap.loc[i])),
                             first_valid_after_gap=str(t.loc[i])))
    return _save(pd.DataFrame(rows), "q_longest_gap.csv")


def joint_return(d):
    rows = []
    for st in G.ORDER:
        x = d[d.station == st]
        any_pct = 100*x[list(SPECIES)].notna().any(axis=1).mean()
        all_pct = 100*x[list(SPECIES)].notna().all(axis=1).mean()
        rows.append(dict(station=st, n_station_hours=len(x), any_species_pct=round(any_pct,1),
                         all_three_pct=round(all_pct,1), pairing_penalty_points=round(any_pct-all_pct,1)))
    return _save(pd.DataFrame(rows), "q_joint_return.csv")


def complete_months(d):
    rows = []
    for st in G.ORDER:
        raw = d[d.station == st].sort_values("time_local").set_index("time_local")
        ix = pd.date_range(raw.index.min().floor("h"), raw.index.max().ceil("h"), freq="h")
        x = raw[list(SPECIES)].reindex(ix)
        x["period"] = x.index.to_period("M")
        for sp in SPECIES:
            r = x.groupby("period")[sp].apply(lambda s: 100*s.notna().mean())
            rows.append(dict(station=st, species=sp, n_months=len(r),
                             months_ge_50pct=int((r>=50).sum()), months_ge_80pct=int((r>=80).sum()),
                             median_monthly_return_pct=round(float(r.median()),1)))
    return _save(pd.DataFrame(rows), "q_complete_months.csv")


def weekday_network(d):
    rows = []
    for st in G.ORDER:
        x = d[(d.station == st) & d.hour_local.between(6, 10)]
        for sp in SPECIES:
            g = G.clean(x, sp).dropna(subset=[sp])
            daily = g.groupby(["date", "dow"])[sp].median().reset_index()
            wd = daily[daily.dow < 5][sp]; we = daily[daily.dow >= 5][sp]
            rng = np.random.default_rng(113 + sum(map(ord, st+sp)))
            boot = [rng.choice(wd, len(wd), True).mean()-rng.choice(we, len(we), True).mean() for _ in range(2000)]
            rows.append(dict(station=st, species=sp, n_weekday=len(wd), n_weekend=len(we),
                             weekday_minus_weekend=round(float(wd.median()-we.median()),3),
                             ci_low=round(float(np.quantile(boot,.025)),3), ci_high=round(float(np.quantile(boot,.975)),3)))
    return _save(pd.DataFrame(rows), "q_weekday_network.csv")


def rush_fingerprint(d):
    rows = []
    for st in G.ORDER:
        x = _paired(d, st, SPECIES)
        levels={}
        for period, lo, hi in (("rush_06-09",6,9),("midday_12-15",12,15),("night_00-03",0,3)):
            g=x[x.hour_local.between(lo,hi)]
            levels[period]=(len(g), float(g.co2.median()), float(g.ch4.median()), float(g.co.median()))
        _, b2, b4, bc = levels["midday_12-15"]
        for period in ("rush_06-09", "night_00-03"):
            n, co2, ch4, co = levels[period]
            d2, d4, dc = co2-b2, ch4-b4, co-bc
            rows.append(dict(station=st,period=f"{period}_minus_midday",n_hours=n,
                             delta_co2=round(d2,2),delta_ch4=round(d4,1),delta_co=round(dc,1),
                             delta_co_per_delta_co2=round(dc/d2,2) if abs(d2)>.01 else np.nan,
                             delta_ch4_per_delta_co2=round(d4/d2,2) if abs(d2)>.01 else np.nan))
    return _save(pd.DataFrame(rows), "q_rush_fingerprint.csv")


def seasonal_diurnal_ratio(d):
    rows=[]
    for st in G.ORDER:
        x=d[d.station==st]
        for season, months in (("wet_Nov-Apr",[11,12,1,2,3,4]),("dry_May-Oct",[5,6,7,8,9,10])):
            g=x[x.month.isin(months)]
            amps={}
            for sp in SPECIES:
                q=G.clean(g,sp).dropna(subset=[sp]).groupby("hour_local")[sp].median()
                amps[sp]=float(q.max()-q.min())
            rows.append(dict(station=st,season=season,co2_amp=round(amps['co2'],2),ch4_amp=round(amps['ch4'],1),
                             co_amp=round(amps['co'],1),ch4_ppb_per_co2_ppm=round(amps['ch4']/amps['co2'],2),
                             co_ppb_per_co2_ppm=round(amps['co']/amps['co2'],2)))
    return _save(pd.DataFrame(rows), "q_seasonal_diurnal.csv")


def extreme_clusters(d):
    rows=[]
    for st in G.ORDER:
        x=d[d.station==st]
        for sp in SPECIES:
            g=G.clean(x,sp).dropna(subset=[sp]).set_index("time_local")[sp]
            thr=float(g.quantile(.99)); hit=g[g>=thr]
            if hit.empty: continue
            cluster=(hit.index.to_series().diff()>pd.Timedelta("48h")).cumsum()
            sizes=hit.groupby(cluster).size()
            spans=hit.groupby(cluster).apply(lambda z:(z.index.max()-z.index.min())/pd.Timedelta(hours=1)+1)
            rows.append(dict(station=st,species=sp,threshold=round(thr,2),n_extreme_hours=len(hit),n_clusters=len(sizes),
                             median_cluster_hours=round(float(spans.median()),1),max_cluster_hours=round(float(spans.max()),1)))
    return _save(pd.DataFrame(rows), "q_extreme_clusters.csv")


def event_decay(d):
    rows=[]
    for st in G.ORDER:
        x=d[d.station==st].copy()
        x["day"]=x.time_local.dt.normalize()
        daily=x.groupby("day")[list(SPECIES)].median()
        for sp in SPECIES:
            s=daily[sp].dropna()
            bg=s.rolling(31,center=True,min_periods=15).quantile(.20)
            an=(s-bg).dropna(); thr=an.quantile(.95); peaks=an[an>=thr]
            vals=[]
            for t,v in peaks.items():
                if t+pd.Timedelta(days=3) in an.index and v>0:
                    vals.append(float(an.loc[t+pd.Timedelta(days=3)]/v))
            rows.append(dict(station=st,species=sp,n_events=len(vals),p95=round(float(thr),2),
                             median_day3_fraction=round(float(np.median(vals)),3) if vals else np.nan))
    return _save(pd.DataFrame(rows), "q_event_decay.csv")


def threshold_sensitivity(d):
    rows=[]
    for st in G.ORDER:
        x=d[d.station==st]
        for sp in SPECIES:
            g=G.clean(x,sp).dropna(subset=[sp])[sp]
            for q in (.95,.975,.99,.995):
                thr=float(g.quantile(q)); rows.append(dict(station=st,species=sp,quantile=q,threshold=round(thr,2),
                                                           exceedance_hours=int((g>=thr).sum())))
    return _save(pd.DataFrame(rows), "q_threshold_sensitivity.csv")


def common_mode(d):
    rows=[]
    daily={}
    for st in G.ORDER:
        x=d[(d.station==st)&d.hour_local.between(12,16)]
        daily[st]={}
        for sp in SPECIES:
            s=G.clean(x,sp).groupby("date")[sp].median().dropna()
            daily[st][sp]=s-s.rolling(31,center=True,min_periods=10).median()
    for sp in SPECIES:
        for i,a in enumerate(G.ORDER):
            for b in G.ORDER[i+1:]:
                z=pd.concat([daily[a][sp],daily[b][sp]],axis=1).dropna(); z.columns=[a,b]
                rows.append(dict(species=sp,station_a=a,station_b=b,n_days=len(z),
                                 pearson_r=round(float(z[a].corr(z[b])),3) if len(z)>5 else np.nan,
                                 spearman_rho=round(float(spearmanr(z[a],z[b]).statistic),3) if len(z)>5 else np.nan))
    return _save(pd.DataFrame(rows), "q_common_mode.csv")


def redundancy(d):
    """Leave-one-station prediction from the median anomaly of other stations."""
    rows=[]
    for sp in SPECIES:
        tab=[]
        for st in G.ORDER:
            x=d[(d.station==st)&d.hour_local.between(12,16)]
            s=G.clean(x,sp).groupby("date")[sp].median().dropna()
            a=s-s.rolling(31,center=True,min_periods=10).median(); tab.append(a.rename(st))
        z=pd.concat(tab,axis=1)
        for st in G.ORDER:
            g=pd.concat([z[st],z.drop(columns=st).median(axis=1)],axis=1).dropna(); g.columns=['obs','network']
            rmse=float(np.sqrt(np.mean((g.obs-g.network)**2)))
            rows.append(dict(species=sp,station=st,n_days=len(g),network_r=round(float(g.obs.corr(g.network)),3),
                             prediction_rmse=round(rmse,3),local_sd=round(float(g.obs.std()),3),
                             rmse_over_local_sd=round(rmse/float(g.obs.std()),3)))
    return _save(pd.DataFrame(rows), "q_redundancy.csv")


def main():
    d=pd.read_pickle(OUT/"all.pkl")
    hysteresis(d); hysteresis_season(d); daynight_coupling(d); baseline_quantiles(d)
    afternoon_windows(d); reference_sensitivity(d); annual_rank_stability(d); uptime_gain()
    outage_seasonality(d); longest_gaps(d); joint_return(d); complete_months(d)
    weekday_network(d); rush_fingerprint(d); seasonal_diurnal_ratio(d); extreme_clusters(d)
    event_decay(d); threshold_sensitivity(d); common_mode(d); redundancy(d)


if __name__ == "__main__":
    main()
