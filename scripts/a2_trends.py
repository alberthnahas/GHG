"""Baseline extraction, growth rates and the 24-year Bukit Kototabang CO record."""
import numpy as np, pandas as pd, ghg_common as g
from scipy.stats import theilslopes

df = pd.read_pickle(g.OUT / "all.pkl")


def monthly_baseline(s, sp, q=0.20):
    """Monthly baseline = qth percentile of the well-mixed afternoon hours.
    Afternoon selection removes the nocturnal local-source bias; the low
    percentile removes advected plumes, leaving the regional background."""
    a = g.clean(s, sp)
    a = a[a.hour_local.between(12, 16)]
    m = a.groupby([a.year, a.month])[sp].quantile(q)
    nn = a.groupby([a.year, a.month])[sp].count()
    m = m[nn >= 20].dropna()                      # require >=20 valid afternoon hours
    t = np.array([y + (mo - .5) / 12 for y, mo in m.index])
    return t, m.values


def growth(t, y, poly=1):
    f = g.harmonic_fit(t, y, n_harm=3, poly=poly)
    res = y - f["seasonal"]
    sl, ic, lo, hi = theilslopes(res, t, 0.95)
    return sl, lo, hi, f


rows = []
for c, s in df.groupby("station"):
    for sp in ("co2", "ch4", "co"):
        t, y = monthly_baseline(s, sp)
        if len(t) < 30:
            continue
        segs = [("full", np.ones(len(t), bool))]
        if c == "BKT":   # instrument gap 2014-2018: report each segment separately
            segs += [("pre-gap", (t < 2014)), ("post-gap", (t >= 2019))]
        for name, m in segs:
            if m.sum() < 24:
                continue
            sl, lo, hi, f = growth(t[m], y[m])
            label = name if name == "full" else f"{int(t[m].min())}\u2013{int(t[m].max())}"
            rows.append(dict(station=c, species=sp, segment=label, n=int(m.sum()),
                             t0=t[m].min(), t1=t[m].max(), trend=sl, lo=lo, hi=hi,
                             mean=y[m].mean()))
T = pd.DataFrame(rows)
T.to_csv(g.OUT / "trends.csv", index=False)
pd.set_option("display.width", 200)
print(T.round(3).to_string(index=False))

# --- BKT annual CO statistics vs ENSO ------------------------------------
b = df[df.station == "BKT"]
ann = b.groupby("year").agg(n=("co", "count"),
                            co_bg=("co", lambda x: x.quantile(.10)),
                            co_med=("co", "median"),
                            co_p95=("co", lambda x: x.quantile(.95)),
                            co_max=("co", "max"))
ann = ann[ann.n > 2000]
# NOAA CPC Oceanic Nino Index, Sep-Oct-Nov season (the Indonesian fire season)
ONI_SON = {2001: -0.2, 2002: 1.2, 2003: 0.4, 2004: 0.7, 2005: -0.2, 2006: 0.9,
           2007: -1.3, 2008: -0.3, 2009: 0.8, 2010: -1.5, 2011: -0.8, 2012: 0.3,
           2013: -0.2, 2014: 0.5, 2015: 2.4, 2016: -0.7, 2017: -0.5, 2018: 0.8,
           2019: 0.3, 2020: -1.2, 2021: -0.8, 2022: -0.9, 2023: 1.8, 2024: 0.1}
ann["oni_son"] = pd.Series(ONI_SON)
ann.to_csv(g.OUT / "bkt_annual_co.csv")
print("\nBKT annual CO (ppb) and SON Ocean Nino Index")
print(ann.round(1).to_string())

v = ann.dropna(subset=["oni_son"])
for col in ("co_bg", "co_med", "co_p95", "co_max"):
    r = np.corrcoef(v.oni_son, v[col])[0, 1]
    rs = pd.Series(v.oni_son).corr(pd.Series(v[col].values, index=v.index), method="spearman")
    print(f"  corr(ONI_SON, {col:7s}) pearson r={r:+.3f}  spearman={rs:+.3f}  n={len(v)}")

# CO background trend on the fire-free background percentile
t, y = monthly_baseline(b, "co", q=0.10)
sl, lo, hi, _ = growth(t, y)
print(f"\nBKT background CO (10th pct afternoon) trend {t.min():.1f}-{t.max():.1f}: "
      f"{sl:+.2f} [{lo:+.2f},{hi:+.2f}] ppb/yr  ({100*sl/y.mean():+.2f} %/yr of the {y.mean():.0f} ppb mean)")

# --- BKT vs PLU over their common window ---------------------------------
W = (2021.75, 2025.0)
cmp_rows = []
for sp in ("co2", "ch4", "co"):
    for c in ("BKT", "PLU"):
        t, y = monthly_baseline(df[df.station == c], sp)
        k = (t >= W[0]) & (t < W[1])
        if k.sum() < 20:
            continue
        sl, lo, hi, f = growth(t[k], y[k])
        cmp_rows.append(dict(species=sp, station=c, n=int(k.sum()), trend=sl, lo=lo, hi=hi,
                             level_2023=float(np.interp(2023.0, t[k], f["trend"]))))
C = pd.DataFrame(cmp_rows)
C.to_csv(g.OUT / "bkt_vs_plu.csv", index=False)
print(f"\nCommon window {W[0]}-{W[1]}: Bukit Kototabang vs Palu")
print(C.round(2).to_string(index=False))
