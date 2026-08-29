"""Second-pass analyses: findings 8-14 of the addendum.

Everything here uses the time-base-corrected, unit-harmonised frame written by
the first pass (outputs/all.pkl).  Nothing re-derives the QC.

  A  weekly-cycle detection across the whole network   -> outputs/x_weekly.csv
  B  nocturnal boundary-layer budget -> surface flux    -> outputs/x_noct_flux.csv
  C  growth-rate anomaly series (ENSO / CH4 surge)      -> outputs/x_growth_anom.csv
  D  afternoon-background ladder referenced to Bariri   -> outputs/x_ladder.csv
  E  seasonal amplitude with block-bootstrap CI         -> outputs/x_seasonal_ci.csv
  F  fire-season dCH4/dCO fingerprint, every season     -> outputs/x_fire_ratio.csv
  G  post-episode CO relaxation timescale               -> outputs/x_co_decay.csv
  H  spectral partition of the 24-yr BKT CO record      -> printed
  I  radiative-forcing accounting                       -> outputs/x_forcing.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import signal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G

OUT = G.OUT
RNG = np.random.default_rng(20260814)

# Air molar density at each station, from the barometric law with a 8.4 km
# scale height and T = 293 K.  Used to turn a ppm h-1 accumulation rate into a
# surface flux.
T_AIR = 293.0


def air_density(elev_m):
    p = 1013.25 * np.exp(-elev_m / 8400.0) * 100.0     # Pa
    return p / (8.314 * T_AIR)                          # mol m-3


# ---------------------------------------------------------------- A ---------
def weekly_cycle(d):
    """Sunday-minus-weekday contrast for every station x species.

    The anomaly is taken against the (calendar-month, hour-of-day) median, so
    the diurnal and seasonal cycles cannot leak into the weekday contrast.  Days
    are the resampling unit and medians are the statistic, because the hourly
    distributions at Kemayoran are heavily plume-skewed.
    """
    rows = []
    for st, g in d.groupby("station"):
        for sp in ("co2", "ch4", "co"):
            gg = g[np.isfinite(g[sp])]
            if len(gg) < 2000:
                continue
            med = gg.groupby(["month", "hour_local"])[sp].transform("median")
            t = pd.concat([(gg[sp] - med).rename("a"), gg[["date", "dow"]]], axis=1)
            daily = t.groupby(["date", "dow"])["a"].median().reset_index()
            s = daily[daily.dow == 6]["a"].values
            w = daily[daily.dow.isin([0, 1, 2, 3, 4])]["a"].values
            pt = np.median(s) - np.median(w)
            bs = np.array([np.median(RNG.choice(s, len(s))) - np.median(RNG.choice(w, len(w)))
                           for _ in range(3000)])
            lo, hi = np.percentile(bs, [2.5, 97.5])
            rows.append(dict(station=st, species=sp, n_sundays=len(s), delta=pt,
                             lo=lo, hi=hi, pct=100 * pt / gg[sp].median(),
                             significant=bool(lo > 0 or hi < 0)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- B ---------
def nocturnal_flux(d):
    """Nightly accumulation rate in the stable layer, and the flux it implies.

    Within the nocturnal boundary layer the surface flux F, the layer depth h
    and the observed rate of rise are related by  F = (dC/dt) * n_air * h,
    provided the layer is not being ventilated.  Nights are kept only when the
    rise is monotone enough (r > 0.7 against time), which selects the calm,
    well-stratified nights the assumption actually holds on.  h is not measured
    here, so the flux is quoted for a 100-400 m bracket.
    """
    d = d.copy()
    d["night_date"] = (d.time_local - pd.Timedelta(hours=12)).dt.normalize()
    night = d[(d.hour_local >= 19) | (d.hour_local <= 4)]
    rows = []
    for st, g in night.groupby("station"):
        per_sp = {sp: [] for sp in ("co2", "ch4", "co")}
        for _, n in g.groupby("night_date"):
            n = n.sort_values("time_local")
            h = (n.time_local - n.time_local.iloc[0]).dt.total_seconds().values / 3600.0
            for sp in per_sp:
                m = np.isfinite(n[sp]).values
                if m.sum() < 6 or np.ptp(h[m]) < 5:
                    continue
                x, y = h[m], n[sp].values[m]
                if y.std() == 0:
                    continue
                per_sp[sp].append((np.polyfit(x, y, 1)[0], np.corrcoef(x, y)[0, 1]))
        dens = air_density(G.STATIONS[st][4])
        for sp, v in per_sp.items():
            if not v:
                continue
            v = pd.DataFrame(v, columns=["rate", "r"])
            good = v[v.r > 0.7]
            if len(good) < 20:
                continue
            rec = dict(station=st, species=sp, n_nights=len(v), n_coherent=len(good),
                       rate=good.rate.median(), q25=good.rate.quantile(.25),
                       q75=good.rate.quantile(.75))
            # ppm h-1 for CO2, ppb h-1 for CH4/CO -> mol m-2 s-1 -> umol m-2 s-1
            scale = 1e-6 if sp == "co2" else 1e-9
            for h_m in (100, 200, 400):
                rec[f"flux_h{h_m}"] = rec["rate"] * scale * dens * h_m / 3600.0 * 1e6
            rows.append(rec)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- C ---------
def monthly_background(g, sp, q=0.20, min_hours=20):
    g = g[(g.hour_local >= 12) & (g.hour_local <= 16) &
          np.isfinite(g[sp]) & (~g["suspect_" + sp])]
    b = g.groupby(g.time_local.dt.to_period("M"))[sp].quantile(q)
    n = g.groupby(g.time_local.dt.to_period("M"))[sp].size()
    b = b[n >= min_hours]
    b.index = b.index.to_timestamp()
    return b


def growth_anomaly(d):
    """Year-by-year growth rate as a 12-month difference of the deseasonalised
    background.  This resolves interannual growth *anomalies*, which a single
    Theil-Sen slope over the whole period averages away."""
    rows = []
    for st in ("BKT", "PLU"):
        g = d[d.station == st]
        for sp in ("co2", "ch4", "co"):
            s = monthly_background(g, sp)
            if len(s) < 30:
                continue
            t = s.index.year + (s.index.month - 0.5) / 12
            f = G.harmonic_fit(t, s.values, n_harm=3, poly=2)
            des = pd.Series(s.values - f["seasonal"], index=s.index)
            # Reindex onto a complete monthly axis first.  Without this the
            # rolling window steps straight across a data gap or a flagged
            # period and reports the level difference either side of it as a
            # year's growth - which is how BKT 2013 and 2019 came out at +10
            # and +11 ppm yr-1 on the first pass.
            des = des.reindex(pd.date_range(des.index.min(), des.index.max(), freq="MS"))
            # Single missing months are routine and are bridged; anything longer
            # stays NaN and kills the window that would have straddled it.
            des = des.interpolate(limit=2, limit_area="inside")
            gr = des.rolling(13, center=True).apply(lambda x: x.iloc[-1] - x.iloc[0], raw=False)
            ann = gr.groupby(gr.index.year).agg(["mean", "count"]).dropna()
            for y, r in ann.iterrows():
                if r["count"] >= 6:          # at least half the year resolved
                    rows.append(dict(station=st, species=sp, year=int(y),
                                     growth=r["mean"], n_months=int(r["count"])))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- D ---------
def background_ladder(d):
    """Every station's afternoon background minus Bariri's, month-matched.

    Afternoon 20th-percentile air is regionally representative, so these
    differences are the *regional* enhancement of each site over the network's
    clean forest reference - not a local plume statistic."""
    ref = {sp: monthly_background(d[d.station == "PLU"], sp) for sp in ("co2", "ch4", "co")}
    rows = []
    for st in ("BKT", "SRG", "JMB", "KMY"):
        for sp in ("co2", "ch4", "co"):
            s = monthly_background(d[d.station == st], sp)
            j = pd.concat([s.rename("a"), ref[sp].rename("b")], axis=1).dropna()
            if len(j) < 12:
                continue
            diff = j.a - j.b
            rows.append(dict(station=st, species=sp, n_months=len(diff),
                             delta=diff.mean(), se=diff.std(ddof=1) / np.sqrt(len(diff))))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- E ---------
def _amplitude(t, y):
    f = G.harmonic_fit(t, y, 3, 2)
    mon = np.round((t % 1) * 12 + 0.5).astype(int)
    s = pd.Series(f["seasonal"], index=mon).groupby(level=0).mean()
    return s.max() - s.min()


def seasonal_ci(d, n_boot=400):
    """Peak-to-peak seasonal amplitude, with whole calendar years as the
    bootstrap block so the CI carries the interannual, not the month-to-month,
    uncertainty."""
    rows = []
    for sp in ("co2", "ch4"):
        for st in G.ORDER:
            s = monthly_background(d[d.station == st], sp)
            if len(s) < 24:
                continue
            t = s.index.year + (s.index.month - 0.5) / 12
            a0 = _amplitude(t, s.values)
            yrs = np.unique(s.index.year)
            bs = []
            for _ in range(n_boot):
                tt, yy = [], []
                for k, y in enumerate(RNG.choice(yrs, len(yrs))):
                    m = s.index.year == y
                    tt.append(t[m] - y + yrs[k])
                    yy.append(s.values[m])
                try:
                    bs.append(_amplitude(np.concatenate(tt), np.concatenate(yy)))
                except Exception:
                    pass
            lo, hi = np.percentile(bs, [2.5, 97.5])
            mon = pd.Series(G.harmonic_fit(t, s.values, 3, 2)["seasonal"],
                            index=np.round((t % 1) * 12 + 0.5).astype(int)).groupby(level=0).mean()
            rows.append(dict(station=st, species=sp, lon=G.STATIONS[st][3], amp=a0,
                             lo=lo, hi=hi, month_max=int(mon.idxmax()),
                             month_min=int(mon.idxmin()), n_years=len(yrs)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- F ---------
def fire_ratio(d):
    """Plume dCH4/dCO for every burning window BKT had both species running.

    Enhancements are taken over the season's own 10th percentile and restricted
    to hours more than 50 ppb above it, so the slope is a plume ratio rather
    than a regression through the background scatter."""
    b = d[d.station == "BKT"].set_index("time_local").sort_index()
    rows = []
    for yr in range(2009, 2025):
        for m0, m1, tag in ((8, 11, "Aug-Oct"), (2, 4, "Feb-Mar")):
            s = b[(b.index.year == yr) & (b.index.month >= m0) &
                  (b.index.month < m1)][["co", "ch4"]].dropna()
            if len(s) < 200:
                continue
            base_co, base_ch4 = s.co.quantile(.10), s.ch4.quantile(.10)
            p = s[s.co > base_co + 50]
            if len(p) < 80:
                continue
            x = (p.co - base_co).values
            y = (p.ch4 - base_ch4).values
            sl = np.polyfit(x, y, 1)[0]
            bs = [np.polyfit(x[i], y[i], 1)[0]
                  for i in (RNG.integers(0, len(x), len(x)) for _ in range(300))]
            lo, hi = np.percentile(bs, [2.5, 97.5])
            rows.append(dict(year=yr, window=tag, n=len(p), co_p95=s.co.quantile(.95),
                             ratio=sl, lo=lo, hi=hi, r=np.corrcoef(x, y)[0, 1]))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- G ---------
DECAY_WINDOWS = {2002: ("2002-10-01", "2002-12-01"), 2006: ("2006-10-15", "2006-12-15"),
                 2015: ("2015-10-20", "2015-12-20"), 2019: ("2019-09-25", "2019-11-25"),
                 2023: ("2023-10-05", "2023-12-05")}


def co_decay(d):
    """e-folding time of the CO enhancement on the falling limb of each event.

    Compared against the ~1-3 month chemical lifetime of CO against OH, this
    separates 'the fires stopped and the air was flushed' from 'the CO was
    oxidised away'."""
    b = d[d.station == "BKT"].set_index("time_local").sort_index()
    co = b["co"].resample("D").median()
    rows = []
    for yr, (p0, p1) in DECAY_WINDOWS.items():
        s = co[p0:p1].dropna()
        if len(s) < 25:
            continue
        base = co[co.index.year == yr].quantile(.10)
        e = (s - base).clip(lower=1)
        x = (s.index - s.index[0]).days.values.astype(float)
        k = np.polyfit(x, np.log(e.values), 1)[0]
        rows.append(dict(year=yr, peak_enh=e.iloc[0], base=base, tau_days=-1 / k,
                         r=np.corrcoef(x, np.log(e.values))[0, 1], n_days=len(s)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- H ---------
BANDS = [(2, 10, "2-10 d  synoptic"), (10, 20, "10-20 d"),
         (20, 90, "20-90 d  intraseasonal (MJO band)"),
         (90, 400, "90-400 d  seasonal"), (400, 4000, ">400 d  interannual")]


def co_spectrum(d):
    """Where the variance of the 24-year BKT CO record actually sits."""
    b = d[d.station == "BKT"].set_index("time_local").sort_index()
    co = b["co"].resample("D").median()["2001-08-01":"2024-12-31"]
    x = np.log(co.clip(lower=20)).interpolate(limit=10).dropna()
    t = x.index.dayofyear.values
    X = np.column_stack([np.ones(len(x)), np.arange(len(x))] +
                        [f(2 * np.pi * k * t / 365.25) for k in (1, 2, 3) for f in (np.sin, np.cos)])
    r = x.values - X @ np.linalg.lstsq(X, x.values, rcond=None)[0]
    f, P = signal.welch(r, fs=1.0, nperseg=2048, noverlap=1024)
    per, P = 1 / f[1:], P[1:]
    return [(lab, 100 * P[(per >= a) & (per < c)].sum() / P.sum()) for a, c, lab in BANDS]


# ---------------------------------------------------------------- I ---------
CH4_INDIRECT = 1.43   # AR6: O3 + stratospheric H2O add ~43% to CH4's band forcing


def dF_co2(dC, C):
    return 5.35 * np.log((C + dC) / C)


def dF_ch4(dM, M):
    return 0.036 * (np.sqrt(M + dM) - np.sqrt(M))


def forcing(ladder):
    """Radiative forcing of (a) each site's regional enhancement over Bariri and
    (b) the measured growth rates.  Simplified band expressions, linearised for
    perturbations this small."""
    rows = []
    piv = ladder.pivot(index="station", columns="species", values="delta")
    for st, r in piv.iterrows():
        a, b = dF_co2(r.co2, 416.0), dF_ch4(r.ch4, 1970.0)
        rows.append(dict(kind="enhancement over Bariri", label=st, co2_mW=a * 1e3,
                         ch4_mW=b * CH4_INDIRECT * 1e3,
                         ch4_share_pct=100 * b * CH4_INDIRECT / (a + b * CH4_INDIRECT)))
    for lab, g_co2, g_ch4 in (("BKT 2019-2024", 2.28, 12.84), ("PLU 2021-2026", 2.86, 8.35)):
        a, b = dF_co2(g_co2, 415.0), dF_ch4(g_ch4, 1930.0)
        rows.append(dict(kind="forcing accrual per year", label=lab, co2_mW=a * 1e3,
                         ch4_mW=b * CH4_INDIRECT * 1e3,
                         ch4_share_pct=100 * b * CH4_INDIRECT / (a + b * CH4_INDIRECT)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
def main():
    d = pd.read_pickle(OUT / "all.pkl")
    pd.set_option("display.width", 200)

    jobs = [("x_weekly", weekly_cycle), ("x_noct_flux", nocturnal_flux),
            ("x_growth_anom", growth_anomaly), ("x_ladder", background_ladder),
            ("x_seasonal_ci", seasonal_ci), ("x_fire_ratio", fire_ratio),
            ("x_co_decay", co_decay)]
    tables = {}
    for name, fn in jobs:
        t = fn(d)
        t.to_csv(OUT / f"{name}.csv", index=False)
        tables[name] = t
        print(f"\n===== {name} =====")
        print(t.round(3).to_string(index=False))

    print("\n===== BKT CO variance by period band =====")
    for lab, pct in co_spectrum(d):
        print(f"  {lab:34s} {pct:5.1f} %")

    f = forcing(tables["x_ladder"])
    f.to_csv(OUT / "x_forcing.csv", index=False)
    print("\n===== x_forcing (mW m-2, and mW m-2 yr-1) =====")
    print(f.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
