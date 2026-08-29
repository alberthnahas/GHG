"""Analyses against the NOAA GML flask record at Bukit Kototabang.

Every other script in this project is internal: it compares the archive with
itself.  This one compares it with an independent instrument, sampled from the
same inlet, analysed in a different laboratory on the WMO scales.  That makes it
the only place where an absolute statement about the in-situ data can be made,
and the only place where a common-mode error is detectable.

  A  flask vs in-situ, raw and corrected time base   -> outputs/z_match.csv
  B  agreement year by year (drift and step search)  -> outputs/z_drift.csv
  C  NOAA QC rejection rates at BKT                  -> outputs/z_qc.csv
  D  flask trends and seasonal cycles, 2004-2025     -> outputs/z_flask_trend.csv
  E  the network's latitudinal structure             -> outputs/z_latitude.csv
  F  SF6 as a transport tracer; seasonal attribution -> outputs/z_sf6.csv
  G  flask-sampled plume ratios incl. H2             -> outputs/z_plume.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G
import noaa_flask as NF

OUT = G.OUT
RNG = np.random.default_rng(20260815)
REF_YEARS = ("2015", "2025")          # window for the hemispheric comparisons


# ---------------------------------------------------------------- A ---------
def match_table(insitu):
    rows = []
    for sp in ("co2", "ch4", "co"):
        for how in ("raw", "corrected"):
            j = NF.match_insitu(insitu, sp, how=how)
            if len(j) < 30:
                continue
            rows.append(dict(species=sp, time_base=how, n=len(j),
                             median=j["diff"].median(), mean=j["diff"].mean(),
                             sd=j["diff"].std(), q25=j["diff"].quantile(.25),
                             q75=j["diff"].quantile(.75), r=j.flask.corr(j.insitu)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- B ---------
def drift_table(insitu):
    """Annual median of (flask - in-situ) on the corrected time base.

    A calibration episode shows up as a year that departs and returns; an
    instrument change shows up as a step that persists.  Both are visible here
    and neither is visible to any internal check."""
    rows = []
    for sp in ("co2", "ch4", "co"):
        j = NF.match_insitu(insitu, sp, how="corrected")
        g = j.groupby(j.index.year).agg(flask=("flask", "median"),
                                        insitu=("insitu", "median"),
                                        diff=("diff", "median"), n=("diff", "size"))
        g = g[g.n >= 8]
        for y, r in g.iterrows():
            rows.append(dict(species=sp, year=int(y), n=int(r.n), flask=r.flask,
                             insitu=r.insitu, diff=r["diff"], ratio=r.flask / r.insitu))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- D ---------
def flask_trends():
    rows = []
    for sp in NF.SPECIES:
        s = NF.events(sp)
        m = s.groupby(s.index.to_period("M")).median()
        m.index = m.index.to_timestamp()
        if len(m) < 60:
            continue
        t = m.index.year + (m.index.dayofyear - 1) / 365.25
        f = G.harmonic_fit(t, m.values, n_harm=3, poly=2)
        sl, lo, hi = G.theil_sen(t, m.values - f["seasonal"])
        seas = pd.Series(f["seasonal"], index=m.index).groupby(m.index.month).mean()
        rows.append(dict(species=sp, unit=NF.UNIT[sp], n_months=len(m),
                         start=str(m.index.min().date()), end=str(m.index.max().date()),
                         trend=sl, lo=lo, hi=hi, amp=seas.max() - seas.min(),
                         month_max=int(seas.idxmax()), month_min=int(seas.idxmin())))
    return pd.DataFrame(rows)


def flask_co_percentiles():
    """Does the CO background move, or only the polluted tail?

    The in-situ record cannot answer this - Section B shows its CO is biased
    before 2019 - but the flask record spans 2004-2025 on one scale."""
    s = NF.events("co")
    y = s.groupby(s.index.year)
    r = pd.DataFrame({"p10": y.quantile(.10), "p50": y.median(),
                      "p90": y.quantile(.90), "n": y.size()})
    r = r[r.n >= 15]
    out = []
    for q in ("p10", "p50", "p90"):
        sl, lo, hi = G.theil_sen(r.index.values.astype(float), r[q].values)
        out.append(dict(percentile=q, mean_ppb=r[q].mean(), trend=sl, lo=lo, hi=hi,
                        n_years=len(r)))
    return pd.DataFrame(out), r


# ---------------------------------------------------------------- E ---------
def latitude_table():
    rows = []
    for sp in NF.SPECIES:
        for st in NF.SITES:
            if not NF.have(sp, st):
                continue
            s = NF.monthly(sp, st)[REF_YEARS[0]:REF_YEARS[1]].dropna()
            if len(s) < 60:
                continue
            t = s.index.year + (s.index.dayofyear - 1) / 365.25
            f = G.harmonic_fit(t, s.values, n_harm=3, poly=2)
            seas = pd.Series(f["seasonal"], index=s.index).groupby(s.index.month).mean()
            rows.append(dict(species=sp, site=st, name=NF.SITES[st][0],
                             lat=NF.SITES[st][1], n_months=len(s), level=s.mean(),
                             amp=seas.max() - seas.min(),
                             month_max=int(seas.idxmax()), month_min=int(seas.idxmin())))
    return pd.DataFrame(rows)


def interhemispheric(lat):
    """NH-minus-SH difference for each species, measured from the network."""
    rows = []
    for sp in NF.SPECIES:
        for n, s in (("brw", "spo"), ("mlo", "smo")):
            if not (NF.have(sp, n) and NF.have(sp, s)):
                continue
            a = NF.monthly(sp, n)[REF_YEARS[0]:REF_YEARS[1]]
            b = NF.monthly(sp, s)[REF_YEARS[0]:REF_YEARS[1]]
            j = pd.concat([a.rename("n"), b.rename("s")], axis=1).dropna()
            rows.append(dict(species=sp, pair=f"{n}-{s}", n_months=len(j),
                             diff=(j.n - j.s).mean(), unit=NF.UNIT[sp]))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- F ---------
def _seasonal_component(s):
    s = s.dropna()
    t = s.index.year + (s.index.dayofyear - 1) / 365.25
    f = G.harmonic_fit(t, s.values, n_harm=3, poly=2)
    return pd.Series(f["seasonal"], index=s.index)


def sf6_attribution():
    """How much of each species' seasonal cycle at BKT is transport?

    SF6 has no chemistry and no local source, so its seasonal cycle at a station
    is pure air-mass alternation.  Regressing another species' seasonal component
    on SF6's gives the observed d(species)/d(SF6).  Comparing that with the same
    ratio measured *between hemispheres* across the network says whether the
    station's cycle is what transport alone would produce, or whether a local
    source is riding on top of it.  No literature value enters.
    """
    ref = interhemispheric(None).set_index(["species", "pair"])["diff"]
    x = _seasonal_component(NF.monthly(NF.INERT, "bkt"))
    rows = []
    for sp in ("ch4", "co2", "co", "n2o"):
        y = _seasonal_component(NF.monthly(sp, "bkt"))
        j = pd.concat([y.rename("y"), x.rename("x")], axis=1).dropna()
        sl = np.polyfit(j.x, j.y, 1)[0]
        r = j.x.corr(j.y)
        se = np.sqrt((1 - r ** 2) / (len(j) - 2)) * j.y.std() / j.x.std()
        for pair in ("mlo-smo", "brw-spo"):
            g = ref.get((sp, pair), np.nan) / ref.get((NF.INERT, pair), np.nan)
            rows.append(dict(species=sp, n=len(j), slope=sl, ci=1.96 * se, r=r,
                             pair=pair, network_gradient=g, ratio=sl / g))
    return pd.DataFrame(rows)


def nh_fraction():
    """Monthly NH air-mass fraction at BKT from SF6 alone, on a Mauna Loa /
    Samoa mixing line.  Values above 1 are meaningful, not an error: they say
    the arriving air is *more* SF6-rich than the mid-Pacific Northern
    Hemisphere, i.e. it carries fresh continental Asian outflow."""
    b, n, s = (NF.monthly(NF.INERT, k) for k in ("bkt", "mlo", "smo"))
    j = pd.concat([b.rename("b"), n.rename("n"), s.rename("s")], axis=1).dropna()["2005":]
    j["f"] = (j.b - j.s) / (j.n - j.s)
    g = j.groupby(j.index.month)["f"].agg(["median", "std", "size"]).reset_index()
    g.columns = ["month", "f_median", "f_sd", "n_years"]
    return g


# ---------------------------------------------------------------- G ---------
def plume_ratios():
    """Species ratios in the flask samples that caught elevated CO.

    SF6 is carried through as a control: a fire emits none, so a method that is
    not manufacturing correlations must return a slope of about zero for it."""
    cols = {sp: NF.events(sp) for sp in NF.SPECIES}
    j = pd.concat([v.rename(k) for k, v in cols.items()], axis=1)
    base = {k: j[k].quantile(.10) for k in j.columns}
    plume = j[j.co > base["co"] + 60]
    rows = []
    for y in ("h2", "ch4", "co2", "n2o", "sf6"):
        k = plume[["co", y]].dropna()
        if len(k) < 40:
            continue
        xv = (k.co - base["co"]).values
        yv = (k[y] - base[y]).values
        sl = np.polyfit(xv, yv, 1)[0]
        bs = [np.polyfit(xv[i], yv[i], 1)[0]
              for i in (RNG.integers(0, len(xv), len(xv)) for _ in range(400))]
        lo, hi = np.percentile(bs, [2.5, 97.5])
        rows.append(dict(species=y, n=len(k), slope=sl, lo=lo, hi=hi,
                         r=np.corrcoef(xv, yv)[0, 1],
                         unit=f"{NF.UNIT[y]} ppb-1", control=(y == "sf6")))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
def main():
    pd.set_option("display.width", 220)
    insitu = pd.read_pickle(OUT / "all.pkl")
    insitu = insitu[insitu.station == "BKT"]

    print("=== calibration scales declared by the flask files ===")
    for sp in NF.SPECIES:
        print(f"   {sp:4s} {NF.scale(sp)}")

    tables = {}
    for name, val in (("z_match", match_table(insitu)),
                      ("z_drift", drift_table(insitu)),
                      ("z_qc", NF.qc_summary()),
                      ("z_flask_trend", flask_trends()),
                      ("z_latitude", latitude_table()),
                      ("z_interhem", interhemispheric(None)),
                      ("z_sf6", sf6_attribution()),
                      ("z_nh_fraction", nh_fraction()),
                      ("z_plume", plume_ratios())):
        val.to_csv(OUT / f"{name}.csv", index=False)
        tables[name] = val
        print(f"\n===== {name} =====")
        print(val.round(3).to_string(index=False))

    trend, per_year = flask_co_percentiles()
    trend.to_csv(OUT / "z_co_percentile_trend.csv", index=False)
    per_year.to_csv(OUT / "z_co_percentile_year.csv")
    print("\n===== z_co_percentile_trend =====")
    print(trend.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
