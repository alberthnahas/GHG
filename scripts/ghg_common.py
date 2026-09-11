"""Shared loading / QC / units harmonisation for the Picarro G2401 hourly GHG files."""
import json
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"
OUT = ROOT / "outputs"

# code -> (pretty name, region, lat, lon, elev_m, setting, utc_offset_of_local_civil_time)
STATIONS = {
    "BKT": ("Bukit Kototabang", "West Sumatra",  -0.202, 100.318, 864.5, "Remote mountain (GAW Global)", 7),
    "JMB": ("Jambi",            "Jambi, Sumatra", -1.611, 103.649,  25.0, "Lowland peat / plantation", 7),
    "KMY": ("Kemayoran",        "Jakarta",        -6.155, 106.850,   8.0, "Megacity urban core",       7),
    # PLU is the Bariri site inside Lore Lindu National Park, ~60 km SE of Palu
    # city - montane primary rainforest, not an urban site.  Coordinates and
    # elevation below are approximate and should be confirmed against the
    # station record before publication.
    "PLU": ("Bariri, Lore Lindu", "Central Sulawesi", -1.20, 120.03, 1400.0,
            "Montane rainforest (GAW Regional)", 8),
    "SRG": ("Sorong",           "Southwest Papua", -0.862, 131.288,  10.0, "Coastal small city",        9),
}
ORDER = ["BKT", "JMB", "KMY", "PLU", "SRG"]

# Categorical palette, fixed slot order, validated with the dataviz validator on the
# adjacent pairlist in both light and dark mode (worst CVD dE 9.2 light / 9.4 dark;
# worst normal-vision dE 27.6 / 22.5).  Aqua is < 3:1 on the light surface, so every
# figure using it also carries a direct label or a table (the "relief rule").
COL = {"BKT": "#2a78d6", "JMB": "#eb6834", "KMY": "#1baf7a",
       "PLU": "#4a3aa7", "SRG": "#e34948"}
# Secondary (non-colour) encoding, always paired with COL.
MRK = {"BKT": "o", "JMB": "s", "KMY": "^", "PLU": "D", "SRG": "v"}
LS = {"BKT": "-", "JMB": "--", "KMY": "-.", "PLU": (0, (3, 1, 1, 1)), "SRG": ":"}

# Physically plausible envelopes.  Deliberately wide: real urban plumes are extreme.
LIM = {"co2": (340.0, 3000.0),      # ppm
       "ch4": (1600.0, 15000.0),    # ppb
       "co":  (-30.0, 6000.0)}      # ppb


# Periods excluded from baseline / trend / seasonal work because the monthly
# baseline moves by far more than the atmosphere can (>5 ppm CO2 month-to-month,
# or all three species dropping together).  Hourly data are kept and flagged, not
# deleted, so episode analysis can still use them.  (station, species-or-'all',
# start, end-exclusive, reason)
SUSPECT = [
    ("BKT", "co2", "2013-10-01", "2013-12-01", "CO2 baseline drops 20 ppm then recovers; CH4/CO unaffected"),
    ("BKT", "co2", "2020-12-01", "2021-07-01", "+11 ppm step then -15 ppm excursion; not mirrored in CH4/CO"),
    ("SRG", "all", "2021-09-01", "2023-06-01", "CO2 baseline 15-50 ppm above the post-2023 level; CO up to 233 ppb"),
    ("SRG", "all", "2023-03-01", "2023-04-01", "CO2, CH4 and CO all collapse together (CO ~2 ppb) - zero-air fault"),
]


def apply_flags(df):
    """Add a boolean `suspect` column; return df."""
    df["suspect"] = False
    for st, sp, t0, t1, _ in SUSPECT:
        m = (df.station == st) & (df.time_local >= t0) & (df.time_local < t1)
        if sp == "all":
            df.loc[m, "suspect"] = True
        else:
            df.loc[m, "suspect_" + sp] = True
    for sp in ("co2", "ch4", "co"):
        c = "suspect_" + sp
        if c not in df:
            df[c] = False
        df[c] = df[c].astype(object).where(df[c].notna(), False).astype(bool) | df["suspect"]
    return df


def clean(df, sp):
    """Rows usable for baseline/trend/seasonal analysis of species `sp`."""
    return df[~df["suspect_" + sp]]


def _load_raw(code):
    f = ROOT / f"grk_hourly_{code.lower()}.json"
    with f.open(encoding="utf-8") as handle:
        df = pd.DataFrame(json.load(handle))
    df["station"] = code
    return df


def load_station(code):
    """Return a tidy hourly dataframe in harmonised units.

    Units in the source files are NOT consistent between stations:
      BKT  -> CO and CH4 already in ppb, CO2 in ppm, only dry-air fields present.
      others -> CO and CH4 in ppm, CO2 in ppm, wet and dry fields present.
    Everything below is ppm for CO2 and ppb for CH4/CO.
    """
    df = _load_raw(code)
    for c in ("co2", "ch4", "co2d", "ch4d", "co"):
        if c not in df:
            df[c] = np.nan
        df[c] = pd.to_numeric(df[c], errors="coerce")

    if code == "BKT":
        ch4 = df["ch4d"]                      # already ppb
        co = df["co"]                         # already ppb
        co2 = df["co2d"]
    else:
        ch4 = df["ch4d"].fillna(df["ch4"]) * 1000.0
        co = df["co"] * 1000.0
        co2 = df["co2d"].fillna(df["co2"])

    out = pd.DataFrame({"station": code, "co2": co2, "ch4": ch4, "co": co})
    ts = pd.to_datetime(df["date"]) + pd.to_timedelta(df["hour"], unit="h")
    out["time"] = ts

    # --- QC -----------------------------------------------------------------
    for c, (lo, hi) in LIM.items():
        out.loc[(out[c] < lo) | (out[c] > hi), c] = np.nan

    out = out.dropna(subset=["co2", "ch4", "co"], how="all")
    out = out.drop_duplicates(subset=["time"]).sort_values("time").reset_index(drop=True)

    # --- time base ----------------------------------------------------------
    # The archive is NOT internally consistent (see report, Finding 1):
    #   JMB / KMY / PLU / SRG  -> UTC throughout.
    #   BKT                    -> local time (WIB) up to 2020-12-31, then
    #                             UTC from 2021-01-01.  The switch is a clean
    #                             one-month break: the diurnal harmonic phase of
    #                             CO2 jumps from 3.6 h (Dec 2020) to 20.2 h
    #                             (Jan 2021), i.e. exactly the -7 h WIB offset.
    # Everything is converted to local time here.
    utc_off = STATIONS[code][6]
    BKT_UTC_FROM = pd.Timestamp("2021-01-01")
    if code == "BKT":
        shift = np.where(out["time"] >= BKT_UTC_FROM, utc_off, 0)
        out["time_local"] = out["time"] + pd.to_timedelta(shift, unit="h")
    else:
        out["time_local"] = out["time"] + pd.Timedelta(hours=utc_off)
    out["time_utc"] = out["time_local"] - pd.Timedelta(hours=utc_off)

    tl = out["time_local"]
    out["utc_offset"] = utc_off
    out["hour_local"] = tl.dt.hour
    out["year"] = tl.dt.year
    out["month"] = tl.dt.month
    out["date"] = tl.dt.normalize()
    out["dow"] = tl.dt.dayofweek                        # 0 = Monday
    out["doy"] = tl.dt.dayofyear
    out["decyear"] = out["year"] + (tl.dt.dayofyear - 1 + tl.dt.hour / 24.0) / \
        np.where(tl.dt.is_leap_year, 366.0, 365.0)
    return out


def load_all():
    return apply_flags(pd.concat([load_station(c) for c in ORDER], ignore_index=True))


# --------------------------------------------------------------------------
def harmonic_fit(t, y, n_harm=3, poly=2):
    """Least-squares polynomial trend + n annual harmonics.  t in decimal years.

    Returns dict with coefficients, fitted series, the smooth trend (poly part)
    and the seasonal part.
    """
    m = np.isfinite(t) & np.isfinite(y)
    t, y = np.asarray(t)[m], np.asarray(y)[m]
    t0 = t.mean()
    cols = [np.ones_like(t)] + [(t - t0) ** k for k in range(1, poly + 1)]
    for k in range(1, n_harm + 1):
        cols += [np.sin(2 * np.pi * k * t), np.cos(2 * np.pi * k * t)]
    X = np.column_stack(cols)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    fit = X @ beta
    trend = X[:, :poly + 1] @ beta[:poly + 1]
    resid = y - fit
    # growth rate = derivative of the polynomial part at each t
    growth = sum(k * beta[k] * (t - t0) ** (k - 1) for k in range(1, poly + 1))
    return dict(t=t, y=y, beta=beta, fit=fit, trend=trend, seasonal=fit - trend,
                resid=resid, growth=growth, rmse=float(np.sqrt(np.mean(resid ** 2))),
                r2=float(1 - resid.var() / y.var()))


def baseline_percentile(df, col, window="30D", q=0.10):
    """Rolling-percentile background: the qth percentile of a moving window.

    Standard practice for polluted continental sites where a full REBS/robust
    baseline is overkill.  Returns a series aligned to df.index.
    """
    s = df.set_index("time")[col]
    return s.rolling(window, min_periods=24).quantile(q).reindex(s.index)


def theil_sen(x, y):
    from scipy.stats import theilslopes
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 10:
        return np.nan, np.nan, np.nan
    sl, ic, lo, hi = theilslopes(np.asarray(y)[m], np.asarray(x)[m], 0.95)
    return sl, lo, hi


def style():
    import matplotlib as mpl
    mpl.rcParams.update({
        "figure.dpi": 130, "savefig.dpi": 160, "savefig.bbox": "tight",
        "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "600",
        "axes.labelsize": 9, "axes.grid": True, "grid.alpha": 0.25,
        "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
        "legend.frameon": False, "legend.fontsize": 8,
        "axes.prop_cycle": mpl.cycler(color=list(COL.values())),
        "figure.facecolor": "white", "axes.facecolor": "white",
    })
