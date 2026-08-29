"""ENSO in a warming ocean: RONI vs ONI, and the warming this network implies.

The Oceanic Nino Index measures Nino3.4 sea-surface temperature against a
30-year climatology.  As the whole tropical ocean warms, that absolute anomaly
drifts upward for reasons that have nothing to do with ENSO, so CPC also
publishes the *Relative* ONI, which subtracts the tropical-mean (20 N-20 S) SST
anomaly.  RONI therefore isolates the ENSO signal; the difference ONI - RONI is
the tropical-mean warming that RONI removed.

That gives three things this report did not previously have:

  A  the tropical-mean SST warming, measured as ONI - RONI  -> outputs/r_warming.csv
  B  which index better predicts this network's signals     -> outputs/r_skill.csv
  C  the seasons whose ENSO classification depends on the
     choice of index, and what BKT actually observed in them -> outputs/r_flip.csv
  D  the warming rate implied by the measured forcing accrual,
     converted with the AR6 transient climate response       -> outputs/r_tcr.csv

D is the closure test.  A and D are independent measurements - one an SST index,
one a greenhouse-gas mixing ratio measured at Bariri and Bukit Kototabang - and
the only thing connecting them is TCR.  If they agree, the chain from emissions
to forcing to temperature is being observed end to end within this network.

A caveat that matters for A: the ONI's base period is a 30-year climatology
updated every five years, which by construction removes most of the long-term
trend.  The residual trend in ONI - RONI is therefore a *lower bound* on
tropical SST warming - it is the part that outran the base-period updates.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G

OUT = G.OUT
ONI_FILE = G.ROOT / "data" / "oni.ascii.txt"
RONI_FILE = G.ROOT / "data" / "roni.ascii.txt"

SEASONS = {"DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
           "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12}

# AR6 WGI Ch.7: TCR best estimate 1.8 C, likely range 1.4-2.2 C per doubling.
TCR = (1.8, 1.4, 2.2)
F2X = 5.35 * np.log(2.0)     # W m-2 for a CO2 doubling, same band expression
                             # used for the accrual in Section 13
FIRE_SEASON = 10             # SON - the index season aligned with the burning peak


def _read(path, col):
    """CPC ascii: SEAS YR TOTAL ANOM (oni) or SEAS YR ANOM (roni)."""
    rows = [ln.split() for ln in open(path)][1:]
    s = pd.Series({pd.Timestamp(int(r[1]), SEASONS[r[0]], 1): float(r[col])
                   for r in rows})
    return s.sort_index()


def indices():
    oni, roni = _read(ONI_FILE, 3), _read(RONI_FILE, 2)
    df = pd.concat([oni.rename("oni"), roni.rename("roni")], axis=1).dropna()
    df["warm"] = df.oni - df.roni      # the tropical-mean anomaly RONI removes
    return df


# ---------------------------------------------------------------- A ---------
def warming(df):
    """Theil-Sen trend of the tropical-mean SST anomaly over three windows.

    Three windows rather than one because the whole point is that the rate is
    not constant; a single trend over 1950-2026 would average the pre-1975
    plateau into the recent decades and understate both."""
    rows = []
    for lo, hi in ((1950, 2026), (1980, 2026), (2000, 2026)):
        s = df.warm[(df.index.year >= lo) & (df.index.year < hi)]
        t = (s.index.year + s.index.month / 12).values
        sl, l, h = G.theil_sen(t, s.values)
        rows.append(dict(period=f"{lo}-{hi - 1}", n_months=len(s),
                         trend_per_decade=sl * 10, lo=l * 10, hi=h * 10))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- B ---------
def bkt_fire_metrics():
    """Per-year daily-median CO statistics at Bukit Kototabang.

    Daily medians rather than hourly, so a single bad hour cannot create a fire
    season, and years with fewer than 250 days are dropped."""
    d = pd.read_pickle(OUT / "all.pkl")
    b = d[d.station == "BKT"].set_index("time_local")
    day = b["co"].resample("D").median()
    rows = {}
    for y, g in day.groupby(day.index.year):
        if g.notna().sum() < 250 or y > 2024:
            continue
        rows[y] = dict(peak=g.max(), d1000=int((g > 1000).sum()),
                       p95=g.quantile(0.95), median=g.median())
    return pd.DataFrame(rows).T


def skill(df, fire):
    """Correlate each index against the fire metrics, Pearson and Spearman.

    Spearman as well as Pearson because the fire metrics are strongly
    right-skewed - one season dominates the peak - and a rank correlation
    answers 'does a warmer Nino3.4 mean a worse season' without letting 2015
    set the slope on its own."""
    son = df[df.index.month == FIRE_SEASON].copy()
    son.index = son.index.year
    j = pd.concat([fire, son], axis=1).dropna()
    rows = []
    for m in ("peak", "d1000", "p95", "median"):
        rows.append(dict(metric=m, n=len(j),
                         r_oni=j.oni.corr(j[m]), r_roni=j.roni.corr(j[m]),
                         rho_oni=j.oni.corr(j[m], method="spearman"),
                         rho_roni=j.roni.corr(j[m], method="spearman"),
                         r_warmterm=j.warm.corr(j[m])))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- C ---------
def classify(v):
    return "El Niño" if v >= 0.5 else ("La Niña" if v <= -0.5 else "neutral")


def flips(df, fire):
    """Seasons whose ENSO label changes between the two indices.

    The classification, not the correlation, is where the choice of index bites:
    an operational fire warning keyed to 'an El Nino has been declared' fires or
    does not fire on this label."""
    son = df[df.index.month == FIRE_SEASON].copy()
    son.index = son.index.year
    son["c_oni"] = son.oni.map(classify)
    son["c_roni"] = son.roni.map(classify)
    f = son[son.c_oni != son.c_roni].copy()
    f["bkt_peak_ppb"] = [fire.peak.get(y, np.nan) for y in f.index]
    f["bkt_days_over_1000"] = [fire.d1000.get(y, np.nan) for y in f.index]
    return f.reset_index(names="year")


# ---------------------------------------------------------------- D ---------
def tcr_closure():
    """Convert the measured forcing accrual into an implied warming rate.

    lambda = TCR / F_2x is the transient warming per unit forcing.  Multiplying
    the accrual rate this network measures by lambda gives the warming rate the
    measured greenhouse growth commits the planet to - no climate model, just
    two mixing-ratio trends and one assessed sensitivity."""
    acc = pd.read_csv(OUT / "x_forcing.csv")
    acc = acc[acc.kind == "forcing accrual per year"]
    rows = []
    for _, r in acc.iterrows():
        total = r.co2_mW + r.ch4_mW
        d = dict(site=r.label, accrual_mW_per_yr=total)
        for tcr, key in zip(TCR, ("best", "lo", "hi")):
            d[f"degC_per_decade_{key}"] = total * 1e-3 * (tcr / F2X) * 10
        rows.append(d)
    return pd.DataFrame(rows)


def main():
    df = indices()
    fire = bkt_fire_metrics()
    tables = {"r_warming": warming(df), "r_skill": skill(df, fire),
              "r_flip": flips(df, fire), "r_tcr": tcr_closure()}
    for name, t in tables.items():
        t.to_csv(OUT / f"{name}.csv", index=False)
        print(f"\n===== {name} =====")
        print(t.to_string(index=False))
    df.to_pickle(OUT / "roni.pkl")
    return tables


if __name__ == "__main__":
    main()
