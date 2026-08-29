"""Long-record analyses that only the 22-year flask series can support.

Everything here needs two decades on one calibration scale, which the in-situ
archive cannot supply for any species (Section 4.3) and can supply for none at
all before 2009.

  A  growth-rate acceleration, all six species        -> outputs/w_accel.csv
  B  decadal growth, split at 2014                    -> outputs/w_decadal.csv
  C  ENSO sensitivity with a lag scan                 -> outputs/w_enso.csv
  D  is the interhemispheric gradient changing?       -> outputs/w_gradient.csv
  E  transport vs local partition of the CO cycle     -> outputs/w_co_partition.csv
  F  plume ratios before and after air-mass removal   -> outputs/w_plume_corrected.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G
import noaa_flask as NF

OUT = G.OUT
ONI_FILE = G.ROOT / "data" / "oni.ascii.txt"
RNG = np.random.default_rng(20260815)
SPLIT = 2014          # the methane growth regime change
REF_PAIR = "mlo-smo"  # tropical NH / tropical SH end members


def load_oni():
    """NOAA CPC Oceanic Nino Index, three-month seasons -> monthly series.

    Each overlapping season is dated to its middle month, which is the
    convention CPC uses when plotting the index."""
    seas = {"DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
            "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12}
    rows = [ln.split() for ln in open(ONI_FILE)][1:]
    s = pd.Series({pd.Timestamp(int(y), seas[k], 1): float(a) for k, y, _, a in rows})
    return s.sort_index()


def deseasonalised(species, site="bkt"):
    """Monthly flask medians with the fitted seasonal cycle removed."""
    s = NF.events(species, site)
    m = s.groupby(s.index.to_period("M")).median()
    m.index = m.index.to_timestamp()
    t = (m.index.year + (m.index.dayofyear - 1) / 365.25).values
    f = G.harmonic_fit(t, m.values, n_harm=3, poly=2)
    return pd.Series(m.values - f["seasonal"], index=m.index)


# ---------------------------------------------------------------- A ---------
def acceleration():
    """Is the growth rate itself increasing?

    Fit  y = c0 + c1(t-t0) + c2(t-t0)^2  to the deseasonalised series.  c1 is the
    growth rate at the midpoint and 2*c2 is the acceleration, with a standard
    error from the usual OLS covariance.  A species whose emissions are rising
    shows c2 > 0; one whose emissions are steady shows c2 = 0 whatever its
    growth rate."""
    rows = []
    for sp in NF.SPECIES:
        d = deseasonalised(sp)
        if len(d) < 80:
            continue
        t = (d.index.year + (d.index.dayofyear - 1) / 365.25).values
        t0 = t.mean()
        X = np.column_stack([np.ones_like(t), t - t0, (t - t0) ** 2])
        b = np.linalg.lstsq(X, d.values, rcond=None)[0]
        resid = d.values - X @ b
        cov = resid.var(ddof=3) * np.linalg.inv(X.T @ X)
        acc, se = 2 * b[2], 2 * np.sqrt(cov[2, 2])
        rows.append(dict(species=sp, unit=NF.UNIT[sp], n_months=len(d),
                         growth_midpoint=b[1], acceleration=acc, ci=1.96 * se,
                         significant=bool(abs(acc) > 1.96 * se)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- B ---------
def decadal():
    rows = []
    for sp in NF.SPECIES:
        d = deseasonalised(sp)
        for lab, a, b in ((f"2004-{SPLIT-1}", "2004", str(SPLIT - 1)),
                          (f"{SPLIT}-2025", str(SPLIT), "2025")):
            w = d[a:b]
            if len(w) < 40:
                continue
            t = (w.index.year + (w.index.dayofyear - 1) / 365.25).values
            sl, lo, hi = G.theil_sen(t, w.values)
            rows.append(dict(species=sp, unit=NF.UNIT[sp], period=lab,
                             n_months=len(w), trend=sl, lo=lo, hi=hi))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- C ---------
def enso(max_lag=15):
    """Growth-rate sensitivity to ENSO, scanning the lag.

    Growth is the 12-month difference of a 7-month-smoothed deseasonalised
    series, so it is defined monthly rather than annually and the lag can be
    resolved.  A positive lag means ONI leads the growth response."""
    oni = load_oni()
    rows = []
    for sp in ("co2", "ch4", "co"):
        d = deseasonalised(sp)
        d = d.reindex(pd.date_range(d.index.min(), d.index.max(), freq="MS"))
        d = d.interpolate(limit=2, limit_area="inside")
        gr = d.rolling(7, center=True, min_periods=5).mean().diff(12)
        for lag in range(max_lag + 1):
            j = pd.concat([gr.rename("g"), oni.shift(lag).rename("o")], axis=1).dropna()
            if len(j) < 60:
                continue
            r = j.g.corr(j.o)
            sl = np.polyfit(j.o, j.g, 1)[0]
            se = np.sqrt((1 - r ** 2) / (len(j) - 2)) * j.g.std() / j.o.std()
            rows.append(dict(species=sp, unit=NF.UNIT[sp], lag_months=lag, n=len(j),
                             r=r, slope=sl, ci=1.96 * se))
    df = pd.DataFrame(rows)
    df["best"] = False
    for sp, g in df.groupby("species"):
        df.loc[g.r.abs().idxmax(), "best"] = True
    return df


# ---------------------------------------------------------------- D ---------
def gradient_trend():
    """Is the north-south difference itself moving?

    A widening gradient means northern emissions are outpacing southern ones; a
    narrowing one means the opposite.  Because both sites are in the same
    network on the same scales, a common calibration drift cancels."""
    rows = []
    for sp in NF.SPECIES:
        if not (NF.have(sp, "brw") and NF.have(sp, "spo")):
            continue
        d = (NF.monthly(sp, "brw") - NF.monthly(sp, "spo")).dropna()
        ann = d.groupby(d.index.year).mean()
        ann = ann[(ann.index >= 2004) & (ann.index <= 2025)]
        if len(ann) < 15:
            continue
        sl, lo, hi = G.theil_sen(ann.index.values.astype(float), ann.values)
        rows.append(dict(species=sp, unit=NF.UNIT[sp], n_years=len(ann),
                         mean_gradient=ann.mean(), trend=sl, lo=lo, hi=hi,
                         significant=bool(lo * hi > 0)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- E ---------
def network_gradients():
    """species-per-SF6 interhemispheric slope, measured from the reference sites."""
    g = {}
    for sp in NF.SPECIES:
        n, s = REF_PAIR.split("-")
        if not (NF.have(sp, n) and NF.have(sp, s)):
            continue
        a = NF.monthly(sp, n)["2015":"2025"]
        b = NF.monthly(sp, s)["2015":"2025"]
        j = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
        g[sp] = (j.a - j.b).mean()
    return g


def _seasonal(sp, site="bkt"):
    s = NF.monthly(sp, site).dropna()
    t = s.index.year + (s.index.dayofyear - 1) / 365.25
    return pd.Series(G.harmonic_fit(t, s.values, 3, 2)["seasonal"], index=s.index)


def co_partition():
    """Split BKT's CO seasonal cycle into a transported part and a local part.

    The transported part is the SF6 seasonal cycle scaled by the measured
    CO-per-SF6 interhemispheric gradient.  Whatever is left is emitted near the
    station, and its seasonal shape should match the burning calendar if the
    interpretation is right."""
    g = network_gradients()
    ratio = g["co"] / g[NF.INERT]
    j = pd.concat([_seasonal("co").rename("obs"),
                   _seasonal(NF.INERT).rename("sf6")], axis=1).dropna()
    j["transport"] = ratio * j.sf6
    j["local"] = j.obs - j.transport
    mo = j.groupby(j.index.month)[["obs", "transport", "local"]].mean().reset_index()
    mo.columns = ["month", "observed", "transport", "local"]
    mo.attrs["ratio"] = ratio
    return mo, ratio


# ---------------------------------------------------------------- F ---------
def plume_corrected():
    """Plume ratios against CO, before and after removing the air mass.

    A flask drawn in a fire plume also arrived in a particular air mass, and at
    this site the two covary strongly - the burning season and the monsoon
    reversal fall in the same months.  Subtracting the SF6-predicted air-mass
    component first separates them.  Without that step the fire signal in CO2 is
    hidden and the one in N2O is spurious."""
    g = network_gradients()
    cols = {sp: NF.events(sp) for sp in NF.SPECIES}
    d = pd.concat([v.rename(k) for k, v in cols.items()], axis=1).dropna(subset=["co", NF.INERT])
    sf6a = d[NF.INERT] - d[NF.INERT].median()
    co_base = d.co.quantile(.10)
    rows = []
    for y in ("h2", "ch4", "n2o", "co2"):
        idx = d[["co", y]].dropna().index
        if len(idx) < 50:
            continue
        variants = [("raw", pd.Series(0.0, index=idx))]
        if y in g:
            variants.append(("air-mass corrected", (g[y] / g[NF.INERT]) * sf6a.loc[idx]))
        for lab, corr in variants:
            yy = d.loc[idx, y] - corr
            yy = yy - yy.quantile(.10)
            xx = d.loc[idx, "co"] - co_base
            m = (xx > 60).values
            if m.sum() < 40:
                continue
            x1, y1 = xx.values[m], yy.values[m]
            sl = np.polyfit(x1, y1, 1)[0]
            bs = [np.polyfit(x1[i], y1[i], 1)[0]
                  for i in (RNG.integers(0, len(x1), len(x1)) for _ in range(400))]
            lo, hi = np.percentile(bs, [2.5, 97.5])
            rows.append(dict(species=y, treatment=lab, n=int(m.sum()), slope=sl,
                             lo=lo, hi=hi, r=np.corrcoef(x1, y1)[0, 1],
                             unit=f"{NF.UNIT[y]} ppb-1"))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
def main():
    pd.set_option("display.width", 220)
    tables = {"w_accel": acceleration(), "w_decadal": decadal(), "w_enso": enso(),
              "w_gradient": gradient_trend(), "w_plume_corrected": plume_corrected()}
    part, ratio = co_partition()
    tables["w_co_partition"] = part

    for name, t in tables.items():
        t.to_csv(OUT / f"{name}.csv", index=False)
        print(f"\n===== {name} =====")
        if name == "w_enso":
            print(t[t.best].round(3).to_string(index=False))
            print("  (full lag scan in the csv)")
        else:
            print(t.round(4).to_string(index=False))

    obs = part.observed.max() - part.observed.min()
    tr = part.transport.max() - part.transport.min()
    loc = part.local.max() - part.local.min()
    print(f"\n  CO seasonal cycle at BKT: observed {obs:.1f} ppb, "
          f"transport {tr:.1f} ({100*tr/obs:.0f} %), local {loc:.1f} ({100*loc/obs:.0f} %); "
          f"local maximum in month {int(part.loc[part.local.idxmax(),'month'])}, "
          f"CO/SF6 gradient {ratio:.1f} ppb ppt-1")


if __name__ == "__main__":
    main()
