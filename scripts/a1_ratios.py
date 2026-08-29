"""Source fingerprinting from nocturnal-accumulation enhancement ratios.

Method: within each individual night (18:00-08:00 local) the nocturnal boundary
layer acts as an accumulation chamber over a fixed footprint.  Species emitted by
a common source then co-vary linearly, and the regression slope of that night is
the *emission ratio* of the surface source mix, independent of dilution and of the
background level.  Nights are retained only when the fit is tight (r^2 >= 0.7,
>= 6 hours, and a real CO2 build-up), which is the usual quality gate.
The population of nightly slopes is then summarised by its median and IQR.
"""
import numpy as np, pandas as pd, ghg_common as g

df = pd.read_pickle(g.OUT / "all.pkl")
MINPTS, R2MIN, MINRANGE = 6, 0.70, 5.0     # hours, r^2, ppm CO2 build-up


def night_id(s):
    """Label 18:00-08:00 blocks by the date the night started."""
    t = s.time_local
    return (t - pd.Timedelta(hours=12)).dt.normalize()


def nightly_slopes(s, xc, yc):
    out = []
    for nid, gp in s.groupby(night_id(s)):
        gp = gp[gp.hour_local.isin([18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6, 7, 8])]
        x, y = gp[xc].to_numpy(float), gp[yc].to_numpy(float)
        m = np.isfinite(x) & np.isfinite(y)
        x, y = x[m], y[m]
        if len(x) < MINPTS or np.ptp(x) < (MINRANGE if xc == "co2" else 0):
            continue
        r = np.corrcoef(x, y)[0, 1]
        if not np.isfinite(r) or r ** 2 < R2MIN:
            continue
        sl = np.polyfit(x, y, 1)[0]
        out.append((nid, sl, r ** 2, len(x), np.ptp(x), np.ptp(y)))
    return pd.DataFrame(out, columns=["night", "slope", "r2", "n", "dx", "dy"])


PAIRS = [("co2", "co", "ΔCO/ΔCO₂", "ppb ppm⁻¹"),
         ("co2", "ch4", "ΔCH₄/ΔCO₂", "ppb ppm⁻¹"),
         ("co", "ch4", "ΔCH₄/ΔCO", "ppb ppb⁻¹")]

rows, keep = [], {}
for c, s in df.groupby("station"):
    s = s.sort_values("time_local")
    nights_total = night_id(s).nunique()
    for xc, yc, lab, unit in PAIRS:
        R = nightly_slopes(s, xc, yc)
        keep[(c, lab)] = R
        if len(R) < 15:
            continue
        rows.append(dict(station=c, ratio=lab, unit=unit,
                         median=R.slope.median(), q25=R.slope.quantile(.25),
                         q75=R.slope.quantile(.75),
                         se=R.slope.std() / np.sqrt(len(R)),
                         n_nights=len(R), nights_total=nights_total,
                         pct_nights=100 * len(R) / nights_total))

T = pd.DataFrame(rows)
T.to_csv(g.OUT / "nightly_emission_ratios.csv", index=False)
pd.to_pickle(keep, g.OUT / "nightly_slopes.pkl")

pd.set_option("display.width", 220)
print(T.round(3).to_string(index=False))
print("\nmedian slope pivot:")
print(T.pivot_table(index="station", columns="ratio", values="median").round(2).to_string())
print("\n% of nights passing the r2>=0.7 coupling test:")
print(T.pivot_table(index="station", columns="ratio", values="pct_nights").round(1).to_string())
