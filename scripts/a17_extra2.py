"""Findings 33-43: severity, phenology, hour-resolved sources, and regional structure.

A third pass over the same two records, asking questions the first two did not.
Several of the results here are negative, and they are reported because the
hypotheses are natural ones that this archive can actually settle.

  A  fire severity by peak, duration and burden      -> outputs/u_severity.csv
  B  monsoon onset from the CO collapse              -> outputs/u_onset.csv
  C  Jakarta's emission ratios hour by hour          -> outputs/u_kmy_hourly.csv
  D  the Maritime Continent against marine air       -> outputs/u_marine.csv
  E  inter-station coherence against separation      -> outputs/u_coherence.csv
  F  how long a CO anomaly remembers itself          -> outputs/u_memory.csv
  G  N2O: transport and a regional residual          -> outputs/u_n2o.csv
  H  the H2-CO coupling through the year             -> outputs/u_h2.csv
  I  wet against dry season diurnal amplitude        -> outputs/u_amp_season.csv
  J  null results: fire vs growth, 20-year trends    -> outputs/u_nulls.csv
"""
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G
import noaa_flask as NF

OUT = G.OUT
# NOAA CPC Oceanic Nino Index, Sep-Oct-Nov season, matching the fire season.
ONI = {2001: -0.2, 2002: 1.2, 2003: 0.4, 2004: 0.7, 2005: -0.2, 2006: 0.9,
       2007: -1.3, 2008: -0.3, 2009: 0.8, 2010: -1.5, 2011: -0.8, 2012: 0.3,
       2013: -0.2, 2014: 0.5, 2015: 2.4, 2016: -0.7, 2017: -0.5, 2018: 0.8,
       2019: 0.3, 2020: -1.2, 2021: -0.8, 2022: -0.9, 2023: 1.8, 2024: 0.1}


def bkt_daily(d, sp="co"):
    return d[d.station == "BKT"].set_index("time_local")[sp].resample("D").median()


# ---------------------------------------------------------------- A ---------
def severity(d):
    """Three severity measures per fire year, and a Gumbel return period.

    Peak, duration and burden are not the same thing, and a record that is
    ranked by one is not ranked by the others.  Absolute values before 2019
    carry the CO bias of Section 4.3, but at 1,000-4,000 ppb a 10-40 ppb offset
    is under 4 % and does not affect the ranking.
    """
    day = bkt_daily(d)
    rows = []
    for y, g in day.groupby(day.index.year):
        if g.notna().sum() < 250 or y > 2024:
            continue
        rows.append(dict(year=int(y), peak=g.max(), days_over_500=int((g > 500).sum()),
                         days_over_1000=int((g > 1000).sum()),
                         burden=float(g.sum() / 1000), oni=ONI.get(int(y), np.nan)))
    r = pd.DataFrame(rows)
    # Gumbel by method of moments on the annual maxima
    x = r.peak.values
    beta = x.std(ddof=1) * np.sqrt(6) / np.pi
    loc = x.mean() - 0.5772 * beta
    r.attrs["gumbel"] = (loc, beta)
    ret = []
    for level in (500, 1000, 2000, x.max()):
        p = np.exp(-np.exp(-(level - loc) / beta))
        ret.append(dict(level_ppb=level, return_period_yr=1 / (1 - p)))
    return r, pd.DataFrame(ret), loc, beta


# ---------------------------------------------------------------- B ---------
def onset(d):
    """The date the burning season ends, read off the CO record.

    The monsoon extinguishes the fires, so the collapse of CO from its dry-season
    level is a marker for the onset of the rains - one that needs no rain gauge.
    Defined as the first day after 1 September on which the 10-day running median
    falls below that year's own median.
    """
    day = bkt_daily(d)
    rows = []
    for y, g in day.groupby(day.index.year):
        if y > 2024:
            continue
        s = g[f"{y}-09-01":f"{y}-12-31"].dropna()
        if len(s) < 60:
            continue
        below = s.rolling(10).median() < g.dropna().median()
        idx = np.where(below.values)[0]
        if not len(idx):
            continue
        rows.append(dict(year=int(y), onset_doy=int(s.index[idx[0]].dayofyear),
                         oni=ONI.get(int(y), np.nan)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- C ---------
def kmy_hourly(d):
    """Kemayoran's emission ratios as a function of hour.

    Enhancements are taken over each calendar month's own 5th percentile, so the
    slow seasonal drift of the background cannot masquerade as a diurnal cycle.
    """
    k = d[d.station == "KMY"].copy()
    per = k.time_local.dt.to_period("M")
    for sp in ("co", "co2", "ch4"):
        k["d" + sp] = k[sp] - k.groupby(per)[sp].transform(lambda s: s.quantile(.05))
    rows = []
    for h, g in k.groupby("hour_local"):
        g = g[(g.dco2 > 3) & np.isfinite(g.dco) & np.isfinite(g.dch4)]
        if len(g) < 120:
            continue
        rows.append(dict(hour=int(h), n=len(g),
                         co_co2=float((g.dco / g.dco2).median()),
                         ch4_co2=float((g.dch4 / g.dco2).median())))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- D ---------
def marine(d):
    """The two clean Indonesian sites against tropical Southern-Hemisphere marine air."""
    aft = d[(d.hour_local >= 12) & (d.hour_local <= 16)]
    rows = []
    for st in ("PLU", "SRG"):
        for sp, stat in (("co2", "median"), ("co", "q20")):
            g = aft[(aft.station == st) & np.isfinite(aft[sp]) & (~aft["suspect_" + sp])]
            per = g.time_local.dt.to_period("M")
            s = g.groupby(per)[sp].median() if stat == "median" else g.groupby(per)[sp].quantile(.20)
            s = s[s.index >= pd.Period("2023-06")]
            s.index = s.index.to_timestamp()
            j = pd.concat([s.rename("st"), NF.monthly(sp, "smo").rename("smo")], axis=1).dropna()
            if len(j) < 10:
                continue
            diff = j.st - j.smo
            rows.append(dict(station=st, species=sp, statistic=stat, n_months=len(j),
                             diff=diff.mean(), se=diff.std(ddof=1) / np.sqrt(len(j))))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- E ---------
def coherence(d):
    """Does the monthly background anomaly correlate between stations?

    The trend and season are removed with a centred 13-month mean, leaving the
    month-to-month anomaly - which is the part that a shared regional air mass
    would synchronise.
    """
    aft = d[(d.hour_local >= 12) & (d.hour_local <= 16)]
    bg = {}
    for st in G.ORDER:
        g = aft[(aft.station == st) & np.isfinite(aft.co2) & (~aft.suspect_co2)]
        per = g.time_local.dt.to_period("M")
        s, n = g.groupby(per)["co2"].quantile(.20), g.groupby(per)["co2"].size()
        bg[st] = s[n >= 20]
    B = pd.DataFrame(bg)
    A = B.apply(lambda c: c - c.rolling(13, center=True, min_periods=7).mean())
    rows = []
    for a, b in itertools.combinations(G.ORDER, 2):
        j = A[[a, b]].dropna()
        if len(j) < 12:
            continue
        la1, lo1, la2, lo2 = (np.radians(G.STATIONS[a][2]), np.radians(G.STATIONS[a][3]),
                              np.radians(G.STATIONS[b][2]), np.radians(G.STATIONS[b][3]))
        km = 6371 * np.arccos(np.clip(np.sin(la1) * np.sin(la2) +
                                      np.cos(la1) * np.cos(la2) * np.cos(lo1 - lo2), -1, 1))
        clean = {a, b} <= {"BKT", "PLU", "SRG"}
        rows.append(dict(pair=f"{a}-{b}", r=float(j[a].corr(j[b])), n_months=len(j),
                         separation_km=km, both_clean=clean))
    return pd.DataFrame(rows).sort_values("separation_km")


# ---------------------------------------------------------------- F ---------
def memory(d, max_lag=40):
    rows = []
    for st in ("BKT", "PLU"):
        s = d[d.station == st].set_index("time_local")["co"].resample("D").median()
        a = np.log(s.clip(lower=20)).dropna()
        a = (a - a.rolling(365, center=True, min_periods=180).mean()).dropna()
        ac = [a.autocorr(lag=L) for L in range(max_lag + 1)]
        e = next((L for L, v in enumerate(ac) if v < 1 / np.e), np.nan)
        rows.append(dict(station=st, n_days=len(a), r_lag1=ac[1], r_lag7=ac[7],
                         efolding_days=e))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- G, H -----
def _seasonal(sp, site="bkt"):
    s = NF.monthly(sp, site).dropna()
    t = s.index.year + (s.index.dayofyear - 1) / 365.25
    return pd.Series(G.harmonic_fit(t, s.values, 3, 2)["seasonal"], index=s.index)


def n2o(d):
    ref = pd.read_csv(OUT / "z_interhem.csv")
    g = {r.species: float(r["diff"]) for _, r in ref[ref.pair == "mlo-smo"].iterrows()}
    j = pd.concat([_seasonal("n2o").rename("obs"), _seasonal("sf6").rename("sf6")],
                  axis=1).dropna()
    j["transport"] = (g["n2o"] / g["sf6"]) * j.sf6
    j["local"] = j.obs - j.transport
    mo = j.groupby(j.index.month)[["obs", "transport", "local"]].mean().reset_index()
    mo.columns = ["month", "observed", "transport", "local"]
    lvl = NF.monthly("n2o", "bkt")["2015":"2025"].mean()
    levels = [dict(month=0, observed=lvl, transport=np.nan, local=np.nan)]
    for s2 in ("mlo", "smo", "brw", "spo"):
        levels.append(dict(month=-1, observed=lvl - NF.monthly("n2o", s2)["2015":"2025"].mean(),
                           transport=np.nan, local=np.nan))
    return mo


def h2_coupling():
    h2, co = NF.events("h2"), NF.events("co")
    j = pd.concat([h2.rename("h2"), co.rename("co")], axis=1).dropna()
    rows = [dict(month=int(m), n=len(g), r=float(g.h2.corr(g.co)))
            for m, g in j.groupby(j.index.month) if len(g) >= 20]
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- I, J -----
def amp_season(d):
    rows = []
    for st in G.ORDER:
        g = d[(d.station == st) & np.isfinite(d.co2)]
        out = {}
        for lab, mo in (("DJF", [12, 1, 2]), ("JJA", [6, 7, 8])):
            h = g[g.month.isin(mo)].groupby("hour_local")["co2"].median()
            out[lab] = float(h.max() - h.min()) if h.notna().sum() > 20 else np.nan
        if np.isfinite(out["DJF"]) and np.isfinite(out["JJA"]):
            rows.append(dict(station=st, elev_m=G.STATIONS[st][4], djf=out["DJF"],
                             jja=out["JJA"], jja_over_djf=out["JJA"] / out["DJF"]))
    return pd.DataFrame(rows)


def nulls(d):
    """Hypotheses this archive can settle, and settles in the negative."""
    rows = []
    day = bkt_daily(d)
    fire = day.groupby(day.index.year).apply(lambda g: (g > 500).sum())
    s = NF.events("co2")
    m = s.groupby(s.index.to_period("M")).median()
    m.index = m.index.to_timestamp()
    t = (m.index.year + (m.index.dayofyear - 1) / 365.25).values
    des = pd.Series(m.values - G.harmonic_fit(t, m.values, 3, 2)["seasonal"], index=m.index)
    des = des.reindex(pd.date_range(des.index.min(), des.index.max(), freq="MS"))
    des = des.interpolate(limit=2, limit_area="inside")
    gr = des.rolling(7, center=True, min_periods=5).mean().diff(12)
    gann = gr.groupby(gr.index.year).mean().dropna()
    for lab, series in (("same year", gann), ("following year", gann.shift(-1))):
        j = pd.concat([fire.rename("fire"), series.rename("g")], axis=1).dropna()
        j = j[j.index <= 2024]
        rows.append(dict(hypothesis=f"BKT fire days predict CO2 growth, {lab}",
                         statistic="pearson r", value=float(j.fire.corr(j.g)), n=len(j),
                         verdict="not supported"))

    for sp in ("co2", "ch4", "co"):
        ev = NF.events(sp)
        mm = ev.groupby(ev.index.to_period("M")).median()
        mm.index = mm.index.to_timestamp()
        amps = []
        for y, gg in mm.groupby(mm.index.year):
            if len(gg) < 10:
                continue
            tt = (gg.index.year + (gg.index.dayofyear - 1) / 365.25).values
            X = np.column_stack([np.ones(len(tt)), tt - tt.mean(),
                                 np.sin(2 * np.pi * tt), np.cos(2 * np.pi * tt)])
            b = np.linalg.lstsq(X, gg.values, rcond=None)[0]
            amps.append((y, 2 * np.hypot(b[2], b[3])))
        a = pd.DataFrame(amps, columns=["year", "amp"])
        sl, lo, hi = G.theil_sen(a.year.values.astype(float), a.amp.values)
        rows.append(dict(hypothesis=f"{sp} seasonal amplitude is trending at BKT",
                         statistic="Theil-Sen slope", value=sl, n=len(a),
                         verdict="not supported" if lo * hi <= 0 else "supported"))

    b, n, s2 = (NF.monthly("sf6", k) for k in ("bkt", "mlo", "smo"))
    j = pd.concat([b.rename("b"), n.rename("n"), s2.rename("s")], axis=1).dropna()["2005":]
    j["f"] = (j.b - j.s) / (j.n - j.s)
    for lab, months in (("DJF", [12, 1, 2]), ("JJA", [6, 7, 8])):
        sub = j[j.index.month.isin(months)]
        ann = sub.groupby(sub.index.year)["f"].mean()
        sl, lo, hi = G.theil_sen(ann.index.values.astype(float), ann.values)
        rows.append(dict(hypothesis=f"the {lab} cross-equatorial reach is changing",
                         statistic="Theil-Sen slope", value=sl, n=len(ann),
                         verdict="not supported" if lo * hi <= 0 else "supported"))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
def main():
    pd.set_option("display.width", 220)
    d = pd.read_pickle(OUT / "all.pkl")

    sev, ret, loc, beta = severity(d)
    ons = onset(d)
    tables = {"u_severity": sev, "u_return": ret, "u_onset": ons,
              "u_kmy_hourly": kmy_hourly(d), "u_marine": marine(d),
              "u_coherence": coherence(d), "u_memory": memory(d),
              "u_n2o": n2o(d), "u_h2": h2_coupling(),
              "u_amp_season": amp_season(d), "u_nulls": nulls(d)}
    for name, t in tables.items():
        t.to_csv(OUT / f"{name}.csv", index=False)
        print(f"\n===== {name} =====")
        print(t.round(3).to_string(index=False))

    print(f"\n  Gumbel fit to the annual maxima: location {loc:.0f} ppb, scale {beta:.0f} ppb")
    v = ons.dropna()
    print(f"  onset: mean DOY {ons.onset_doy.mean():.0f}, sd {ons.onset_doy.std():.0f} d; "
          f"corr with ONI {v.onset_doy.corr(v.oni):+.2f}, "
          f"{np.polyfit(v.oni, v.onset_doy, 1)[0]:.0f} d per degC")


if __name__ == "__main__":
    main()
