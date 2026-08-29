"""Sampling-design analysis for the Bukit Kototabang 100-m tower valve sequencer.

The station is moving from a single 30-m inlet to a three-level tower (30 / 70 /
100 m).  This module answers the four quantitative questions that decide the
sequencer schedule, and writes one CSV per question:

  sq_diurnal.csv     where in the day the vertical information actually sits
  sq_structure.csv   how fast the signal changes, and what a short slice costs
  sq_subsample.csv   what 3-hourly sampling does to a monthly mean (the WDCGG
                     continuity question)
  sq_diurnal_bias.csv  what 3-hourly sampling does to the diurnal composite
  sq_offset.csv      the timing artefact each candidate frame puts into a
                     vertical gradient - this is what picks the frame
  sq_flush.csv       line volumes and purge times - the engineering constraint
  sq_budget.csv      the resulting hourly time budget

Everything atmospheric is measured from the existing BKT 30-m record, which is
the only inlet the archive contains.  `sq_flush` is deterministic geometry, not
a measurement.

Usage:  a36_sequencer.py
"""
import numpy as np
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G

OUT = G.OUT
SPECIES = ("co2", "ch4", "co")
UNIT = {"co2": "ppm", "ch4": "ppb", "co": "ppb"}

# The CO record before 2019 is biased high by 10-41 ppb (landmine 4).  A
# constant bias cancels in a diurnal *anomaly*, but not in anything absolute,
# so CO is restricted to 2019+ throughout rather than case by case.
CO_FROM = 2019


def bkt():
    d = G.apply_flags(G.load_station("BKT"))
    return d


def _series(d, sp):
    """Usable rows for species `sp`, as a clean local-time indexed series."""
    x = G.clean(d, sp)
    if sp == "co":
        x = x[x.year >= CO_FROM]
    s = x.set_index("time_local")[sp].dropna()
    return s[~s.index.duplicated()]


# --------------------------------------------------------------------------
# 1.  Diurnal composite.  Anomalies from the same day's mean, so a trend or a
#     seasonal cycle cannot leak into the shape.
def diurnal(d):
    rows = []
    for sp in SPECIES:
        s = _series(d, sp)
        f = s.to_frame("v")
        f["date"] = f.index.normalize()
        f["hour"] = f.index.hour
        # a day needs >= 18 hours to contribute, otherwise the daily mean is
        # itself a biased reference and the anomaly inherits that bias
        n = f.groupby("date")["v"].transform("count")
        f = f[n >= 18]
        f["anom"] = f["v"] - f.groupby("date")["v"].transform("mean")
        # DJF/JJA split: the west-Sumatran double rainfall maximum means the
        # meaningful contrast here is season-of-convection, kept simple
        f["season"] = np.where(f.index.month.isin([12, 1, 2]), "DJF",
                      np.where(f.index.month.isin([6, 7, 8]), "JJA", "other"))
        for season in ("all", "DJF", "JJA"):
            g = f if season == "all" else f[f.season == season]
            for h, gg in g.groupby("hour"):
                rows.append(dict(species=sp, unit=UNIT[sp], season=season, hour=h,
                                 n=len(gg), mean_anom=gg.anom.mean(),
                                 sd=gg.anom.std(), p25=gg.anom.quantile(.25),
                                 p75=gg.anom.quantile(.75)))
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "sq_diurnal.csv", index=False)
    return out


# --------------------------------------------------------------------------
# 2.  Structure function.  D(tau) = < (x(t+tau) - x(t))^2 > over lags the hourly
#     archive resolves (1-6 h), fitted as D = A tau^(2H) and extrapolated below
#     1 h.  The extrapolation is the only way this archive can say anything
#     about a sub-hourly slice, and it is flagged as such everywhere it is used.
def structure(d):
    rows, fits = [], []
    for sp in SPECIES:
        s = _series(d, sp)
        s = s.reindex(pd.date_range(s.index.min(), s.index.max(), freq="h"))
        v = s.to_numpy()
        lags = np.arange(1, 7)
        D = []
        for L in lags:
            dd = v[L:] - v[:-L]
            dd = dd[np.isfinite(dd)]
            D.append(np.mean(dd ** 2))
            rows.append(dict(species=sp, unit=UNIT[sp], lag_h=float(L),
                             n_pairs=len(dd), D=float(D[-1]),
                             rms_diff=float(np.sqrt(D[-1])), source="measured"))
        D = np.asarray(D)
        # log-log straight line: log D = log A + 2H log tau
        b, a = np.polyfit(np.log(lags), np.log(D), 1)
        A, H = float(np.exp(a)), float(b / 2)
        for tau in (1 / 12, 1 / 6, 0.25, 0.5):        # 5, 10, 15, 30 min
            Dt = A * tau ** (2 * H)
            rows.append(dict(species=sp, unit=UNIT[sp], lag_h=tau, n_pairs=0,
                             D=float(Dt), rms_diff=float(np.sqrt(Dt)),
                             source="extrapolated"))
        # rms departure of a single instant from the hour centre ~ sqrt(D(0.5h))/sqrt(2)
        sigma_rep = float(np.sqrt(A * 0.5 ** (2 * H)) / np.sqrt(2))
        fits.append(dict(species=sp, unit=UNIT[sp], A=A, H=H,
                         r2=float(np.corrcoef(np.log(lags), np.log(D))[0, 1] ** 2),
                         sigma_rep_30min=sigma_rep))
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "sq_structure.csv", index=False)
    pd.DataFrame(fits).to_csv(OUT / "sq_structure_fit.csv", index=False)
    return out, pd.DataFrame(fits)


# --------------------------------------------------------------------------
# 3.  The subsampling experiment.  Rebuild the monthly means from a 3-hourly
#     subsample at each of the 8 possible clock offsets and compare with the
#     monthly mean of the full hourly record.  This is the direct test of
#     whether a 3-hourly 30-m schedule can continue the WDCGG series.
def subsample(d):
    rows = []
    for sp in SPECIES:
        s = _series(d, sp)
        f = s.to_frame("v")
        f["hour"] = f.index.hour
        f["ym"] = f.index.to_period("M")
        full = f.groupby("ym")["v"].agg(["mean", "count"])
        full = full[full["count"] >= 24 * 20]          # >= 20 complete-day-equivalents
        for off in range(3):
            g = f[f.hour % 3 == off]
            sub = g.groupby("ym")["v"].mean()
            j = full.join(sub.rename("sub"), how="inner").dropna()
            dlt = j["sub"] - j["mean"]
            rows.append(dict(species=sp, unit=UNIT[sp], scheme="3-hourly",
                             offset_h=off, n_months=len(j),
                             mean_bias=float(dlt.mean()),
                             rms_error=float(np.sqrt((dlt ** 2).mean())),
                             max_abs_error=float(dlt.abs().max()),
                             months_over_0p1=int((dlt.abs() > 0.1).sum())))
        # the hourly frame: every hour is sampled, only for 5 of its 60 minutes.
        # At hourly resolution that is indistinguishable from the full record,
        # so its monthly-mean error is zero by construction and the residual
        # error is the within-hour term from sq_structure, not a sampling term.
        rows.append(dict(species=sp, unit=UNIT[sp], scheme="hourly-frame",
                         offset_h=0, n_months=len(full), mean_bias=0.0,
                         rms_error=0.0, max_abs_error=0.0, months_over_0p1=0))
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "sq_subsample.csv", index=False)
    return out


# --------------------------------------------------------------------------
# 4.  What 3-hourly sampling does to the diurnal composite itself - the
#     quantity a vertical-gradient study is built on.
def diurnal_bias(d):
    rows = []
    for sp in SPECIES:
        s = _series(d, sp)
        f = s.to_frame("v")
        f["hour"] = f.index.hour
        f["date"] = f.index.normalize()
        n = f.groupby("date")["v"].transform("count")
        f = f[n >= 18]
        f["anom"] = f["v"] - f.groupby("date")["v"].transform("mean")
        ref = f.groupby("hour")["anom"].mean()
        amp_full = float(ref.max() - ref.min())
        for off in range(3):
            g = f[f.hour % 3 == off]
            # daily mean now estimated from the 8 sampled hours only
            g = g.copy()
            g["anom_sub"] = g["v"] - g.groupby("date")["v"].transform("mean")
            sub = g.groupby("hour")["anom_sub"].mean()
            amp_sub = float(sub.max() - sub.min())
            rows.append(dict(species=sp, unit=UNIT[sp], offset_h=off,
                             hours_resolved=len(sub), amp_full=amp_full,
                             amp_sub=amp_sub,
                             amp_error_pct=100 * (amp_sub - amp_full) / amp_full))
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "sq_diurnal_bias.csv", index=False)
    return out


# --------------------------------------------------------------------------
# 5.  Flush geometry.  Deterministic, not measured: line volume from the tubing
#     bore, residence time from the flow, and the number of volume exchanges
#     needed for a step change to decay to a given fraction.
#
# A well-mixed volume decays as exp(-t/tau) with tau = V/Q; plug flow in a long
# smooth tube is faster than that, so treating the whole line as well-mixed is
# the conservative choice.
BORE_MM = 4.0                 # 1/4" OD PFA, 4 mm ID
LEVELS = (30, 70, 100)
FLOWS = (0.4, 2.0, 5.0, 10.0)  # slpm.  0.4 = G2401 alone, the rest = bypass pump


def flush():
    rows = []
    area = np.pi * (BORE_MM / 2000.0) ** 2            # m^2
    for L in LEVELS:
        vol_L = area * L * 1000.0                     # litres
        for Q in FLOWS:
            tau = vol_L / Q                           # minutes per volume
            rows.append(dict(level_m=L, bore_mm=BORE_MM, volume_L=vol_L,
                             flow_slpm=Q, tau_min=tau,
                             t_90pct_min=tau * np.log(10),
                             t_99pct_min=tau * np.log(100),
                             t_99p9pct_min=tau * np.log(1000)))
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "sq_flush.csv", index=False)
    return out


# --------------------------------------------------------------------------
# 6.  The resulting hourly budget.
# Two candidate frames.  "sequential" is the obvious one - lowest level first,
# then up.  "bracketed" puts the two short slices near the middle of the hour
# and splits the 100-m block around them, so the levels are compared at nearly
# the same clock time.  sq_offset.csv is what decides between them.
FRAMES = {
    "sequential": [(0, 3, "30 m", "discard"), (3, 8, "30 m", "valid"),
                   (8, 11, "70 m", "discard"), (11, 16, "70 m", "valid"),
                   (16, 19, "100 m", "discard"), (19, 60, "100 m", "valid")],
    "bracketed": [(0, 19, "100 m", "valid"),
                  (19, 22, "30 m", "discard"), (22, 27, "30 m", "valid"),
                  (27, 30, "70 m", "discard"), (30, 35, "70 m", "valid"),
                  (35, 38, "100 m", "discard"), (38, 60, "100 m", "valid")],
}
FRAME = FRAMES["bracketed"]


def _centroids(frame):
    """Valid-time centroid of each level, in minutes past the hour."""
    out = {}
    for lev in ("30 m", "70 m", "100 m"):
        seg = [(a, b) for a, b, l, k in frame if l == lev and k == "valid"]
        w = sum(b - a for a, b in seg)
        out[lev] = sum((a + b) / 2 * (b - a) for a, b in seg) / w
    return out


def offset_cost(fit):
    """The timing artefact in a vertical gradient.

    Two levels sampled dt apart during a ramp differ by the atmosphere's own
    change over dt as well as by any real gradient.  sq_structure_fit gives that
    change directly: rms = sqrt(A * (dt/60)^(2H)).
    """
    rows = []
    for name, frame in FRAMES.items():
        c = _centroids(frame)
        for pair in (("30 m", "100 m"), ("70 m", "100 m"), ("30 m", "70 m")):
            dt = abs(c[pair[0]] - c[pair[1]])
            for _, f in fit.iterrows():
                rows.append(dict(frame=name, pair=f"{pair[0]} vs {pair[1]}",
                                 dt_min=dt, species=f.species, unit=f.unit,
                                 rms_artefact=float(np.sqrt(f.A * (dt / 60.0) ** (2 * f.H)))))
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "sq_offset.csv", index=False)
    return out


def budget():
    rows = []
    for t0, t1, lev, kind in FRAME:
        rows.append(dict(minute_start=t0, minute_end=t1, level=lev, status=kind,
                         minutes=t1 - t0))
    b = pd.DataFrame(rows)
    valid = b[b.status == "valid"].groupby("level")["minutes"].sum()
    tot = float(valid.sum())
    summ = pd.DataFrame(dict(level=valid.index, valid_min_per_hour=valid.values,
                             share_of_valid_pct=100 * valid.values / tot,
                             valid_h_per_day=24 * valid.values / 60.0,
                             samples_per_day=24))
    b.to_csv(OUT / "sq_frame.csv", index=False)
    summ.to_csv(OUT / "sq_budget.csv", index=False)
    return b, summ


def main():
    d = bkt()
    diurnal(d)
    _, fit = structure(d)
    subsample(d)
    diurnal_bias(d)
    offset_cost(fit)
    flush()
    budget()
    print("wrote sq_*.csv to", OUT)


if __name__ == "__main__":
    main()
