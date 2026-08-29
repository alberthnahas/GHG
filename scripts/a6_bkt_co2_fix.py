"""Derive a correction for the residual CO2 offsets in the Bukit Kototabang record.

Strategy — entirely internal to the data, no external reference series:

  1. Build a reference model of what BKT CO2 *should* be doing: a quadratic
     trend plus three annual harmonics, fitted ONLY to months that pass a
     robustness screen, using an iterative reweighting so that the offending
     months cannot drag the fit toward themselves.
  2. The monthly residual from that model is the candidate offset.
  3. Accept an offset only where it is (a) large compared with the residual
     scatter of the good months, and (b) NOT accompanied by a matching
     excursion in CH4 and CO, which are independent of the CO2 calibration
     but share the same air mass.  Criterion (b) is what separates an
     instrument problem from real atmospheric variability.
  4. Apply the offsets, then validate against Palu/Bariri over the overlap.
"""
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import ghg_common as g
import i18n

i18n.install(i18n.from_argv())

g.style()
df = pd.read_pickle(g.OUT / "all.pkl")
b = df[df.station == "BKT"]


def monthly(s, sp, q=.20, minn=20):
    a = s[s.hour_local.between(12, 16)]
    m = a.groupby([a.year, a.month])[sp].quantile(q)
    n = a.groupby([a.year, a.month])[sp].count()
    m = m[n >= minn].dropna()
    t = np.array([y + (mo - .5) / 12 for y, mo in m.index])
    return t, m.values, list(m.index)


def robust_model(t, y, n_iter=8):
    """Trend + 3 harmonics, fitted with iterative Tukey biweight reweighting.

    Fitted separately either side of the 2014-2018 instrument gap, because a
    single polynomial cannot span it without the gap itself steering the fit.
    """
    pred = np.full(len(t), np.nan)
    for seg in [(t < 2016), (t >= 2016)]:
        ts, ys = t[seg], y[seg]
        w = np.ones(len(ts))
        for _ in range(n_iter):
            X = np.column_stack(
                [np.ones_like(ts), ts - ts.mean(), (ts - ts.mean()) ** 2]
                + [f(2 * np.pi * k * ts) for k in (1, 2, 3) for f in (np.sin, np.cos)])
            W = np.sqrt(w)[:, None]
            beta, *_ = np.linalg.lstsq(X * W, ys * np.sqrt(w), rcond=None)
            r = ys - X @ beta
            s = 1.4826 * np.median(np.abs(r - np.median(r))) or 1.0
            u = np.clip(r / (6 * s), -1, 1)
            w = (1 - u ** 2) ** 2
        pred[seg] = X @ beta
    return pred


# ---------------------------------------------------------------- 1-2: residuals
t, y, idx = monthly(b, "co2")
pred = robust_model(t, y)
res = y - pred
sd = 1.4826 * np.median(np.abs(res - np.median(res)))

# companion species, normalised to their own robust scatter, on the same months
comp = {}
for sp in ("ch4", "co"):
    ts, ys, ids = monthly(b, sp)
    ps = robust_model(ts, ys)
    rs = ys - ps
    ss = 1.4826 * np.median(np.abs(rs - np.median(rs)))
    comp[sp] = pd.Series(rs / ss, index=pd.MultiIndex.from_tuples(ids))

R = pd.DataFrame({"t": t, "co2": y, "model": pred, "resid": res, "z_co2": res / sd},
                 index=pd.MultiIndex.from_tuples(idx))
for sp in ("ch4", "co"):
    R["z_" + sp] = comp[sp]

# ---------------------------------------------------------------- 3: classify
# CO2 and CH4 are measured by the same CRDS analyser; CO is a separate channel.
# The pattern across the three residuals therefore identifies the fault:
#   CO2 anomalous, CH4 and CO normal   -> CO2 calibration.      correctable
#   CO2 and CH4 anomalous, CO normal   -> analyser-wide fault.  reject
#   CO2 and CO anomalous               -> real air mass (fire). leave alone
Z_HIT, Z_OK = 3.0, 2.0


def classify(r):
    if abs(r.z_co2) <= Z_HIT:
        return "ok"
    if abs(r.z_co) > Z_OK:
        return "atmospheric"
    if abs(r.z_ch4) > Z_OK:
        return "analyser"
    return "co2_cal"


R["cls"] = R.apply(classify, axis=1)
# absorb marginal months (|z|>2) adjacent to an accepted episode of the same sign
for _ in range(3):
    prev, nxt = R.cls.shift(1), R.cls.shift(-1)
    sgn = np.sign(R.resid)
    grow = ((R.cls == "ok") & (R.z_co2.abs() > 2.0) & (R.z_ch4.abs() < Z_OK)
            & (R.z_co.abs() < Z_OK)
            & (((prev == "co2_cal") & (sgn == np.sign(R.resid.shift(1))))
               | ((nxt == "co2_cal") & (sgn == np.sign(R.resid.shift(-1))))))
    R.loc[grow, "cls"] = "co2_cal"

print(f"Robust residual scatter of the CO2 monthly baseline: sigma = {sd:.2f} ppm")
print(R.cls.value_counts().to_string(), "\n")
print("All months with |z_CO2| > 3, and what the companion channels say")
print(f"{'month':10s}{'CO2 obs':>9s}{'model':>9s}{'resid':>8s}{'z_CO2':>7s}{'z_CH4':>7s}{'z_CO':>7s}  diagnosis")
for k, r in R[R.cls != "ok"].iterrows():
    print(f"{k[0]}-{k[1]:02d}  {r.co2:9.1f}{r.model:9.1f}{r.resid:+8.1f}"
          f"{r.z_co2:+7.1f}{r.z_ch4:+7.1f}{r.z_co:+7.1f}  {r.cls}")

# ---------------------------------------------------------------- episodes
# group contiguous same-class, same-sign months
key = R.cls + "|" + np.sign(R.resid).astype(int).astype(str)
R["ep"] = (key != key.shift()).cumsum()
episodes, rejects = [], []
for _, gp in R[R.cls != "ok"].groupby("ep"):
    rec = dict(start=f"{gp.index[0][0]}-{gp.index[0][1]:02d}",
               end=f"{gp.index[-1][0]}-{gp.index[-1][1]:02d}",
               months=len(gp), cls=gp.cls.iloc[0],
               offset=gp.resid.mean(),
               se=gp.resid.std(ddof=1) / np.sqrt(len(gp)) if len(gp) > 1 else sd)
    (episodes if rec["cls"] == "co2_cal" else rejects).append(rec)
E = pd.DataFrame(episodes)
E.to_csv(g.OUT / "bkt_co2_offsets.csv", index=False)
print("\nCORRECTABLE - subtract `offset` from every CO2 value in the window")
print(E.round(2).to_string(index=False))
if rejects:
    print("\nNOT correctable - reject these CO2 (and CH4) data outright")
    print(pd.DataFrame(rejects).round(2).to_string(index=False))

# ---------------------------------------------------------------- 4: apply + validate
corr = b[["time_local", "co2"]].copy().set_index("time_local").co2
for e in episodes:
    lo = pd.Timestamp(e["start"] + "-01")
    hi = pd.Timestamp(e["end"] + "-01") + pd.offsets.MonthBegin(1)
    m = (corr.index >= lo) & (corr.index < hi)
    corr[m] = corr[m] - e["offset"]
# analyser-fault months are not recoverable - drop them
for e in rejects:
    if e["cls"] != "analyser":
        continue
    lo = pd.Timestamp(e["start"] + "-01")
    hi = pd.Timestamp(e["end"] + "-01") + pd.offsets.MonthBegin(1)
    corr[(corr.index >= lo) & (corr.index < hi)] = np.nan

bc = b.copy()
bc["co2_corr"] = corr.values
bc.to_pickle(g.OUT / "bkt_co2_corrected.pkl")
tc, yc, idc = monthly(bc, "co2_corr")
resc = yc - robust_model(tc, yc)

keep = np.array([k not in {(2013, 10), (2013, 11)} for k in idx])
print(f"\nMonthly residual, months retained in both versions (n={keep.sum()}):")
print(f"  before correction: {np.sqrt(np.mean(res[keep]**2)):5.2f} ppm RMS,"
      f"  |max| {np.abs(res[keep]).max():5.2f}")
print(f"  after  correction: {np.sqrt(np.mean(resc**2)):5.2f} ppm RMS,"
      f"  |max| {np.abs(resc).max():5.2f}")

mk = np.array([yy * 12 + mm for yy, mm in idc])
d = np.abs(np.diff(yc))[np.diff(mk) == 1]
mk0 = np.array([yy * 12 + mm for yy, mm in idx])
d0 = np.abs(np.diff(y))[np.diff(mk0) == 1]
print(f"  largest month-to-month step: {d0.max():.2f} ppm before -> {d.max():.2f} ppm after"
      f"   (rest of the network: p90 2.0-3.7, max 3.1-6.5)")

from scipy.stats import theilslopes
print()
for lab, tt, vv in [("as archived", t, y), ("corrected  ", tc, yc)]:
    for a, z, nm in [(2019, 2026, "2019-2024"), (2009, 2014, "2009-2013")]:
        k = (tt >= a) & (tt < z)
        if k.sum() < 24:
            continue
        f = g.harmonic_fit(tt[k], vv[k], 3, 1)
        sl, ic, lo, hi = theilslopes(vv[k] - f["seasonal"], tt[k], .95)
        print(f"  BKT CO2 growth {nm}, {lab}: {sl:+.2f} [{lo:+.2f},{hi:+.2f}] ppm/yr")

# independent cross-check against Bariri over the overlap
tp, yp, idp = monthly(df[df.station == "PLU"], "co2")
mp = dict(zip([yy * 12 + mm for yy, mm in idp], yp))
ov = [(k, v) for k, v in zip(mk, yc) if k in mp]
diff = np.array([v - mp[k] for k, v in ov])
tov = np.array([k / 12 for k, _ in ov])
sl, _, lo, hi = theilslopes(diff, tov, .95)
print(f"\nIndependent check - BKT(corrected) minus Bariri, {len(diff)} overlapping months:")
print(f"  mean offset {diff.mean():+.2f} ppm (sd {diff.std():.2f}),"
      f" relative drift {sl:+.2f} [{lo:+.2f},{hi:+.2f}] ppm/yr")
ov0 = [(k, v) for k, v in zip(mk0, y) if k in mp]
diff0 = np.array([v - mp[k] for k, v in ov0])
print(f"  same before correction: mean {diff0.mean():+.2f} ppm (sd {diff0.std():.2f})")

# ---------------------------------------------------------------- figure
def brk(t, v, maxgap=2.5 / 12):
    """Insert NaN across data gaps so lines are not drawn through them."""
    t, v = np.asarray(t, float), np.asarray(v, float)
    k = np.where(np.diff(t) > maxgap)[0]
    return np.insert(t, k + 1, np.nan), np.insert(v, k + 1, np.nan)


CLSCOL = {"ok": "#a9b3ac", "co2_cal": "#e34948", "analyser": "#4a3aa7",
          "atmospheric": "#eb6834"}
fig, axes = plt.subplots(2, 1, figsize=(10, 5.6), sharex=True,
                         gridspec_kw=dict(height_ratios=[1.5, 1], hspace=.2))
ax = axes[0]
ax.plot(*brk(t, y), color="#c3c8c4", lw=1.1, marker="o", ms=2.3, label="as archived", zorder=1)
ax.plot(*brk(t, pred), color="#0b0b0b", lw=1, ls="--", label="robust reference model", zorder=2)
ax.plot(*brk(tc, yc), color=g.COL["BKT"], lw=1.5, marker="o", ms=2.6,
        label="after the derived correction", zorder=4)
ax.plot(tp, yp, color=g.COL["PLU"], lw=1.3, ls=(0, (3, 1, 1, 1)), marker="D", ms=2.4,
        label="Bariri, Lore Lindu (independent check)", zorder=3)
for e in episodes + [r for r in rejects if r["cls"] == "analyser"]:
    a = pd.Timestamp(e["start"] + "-01"); z = pd.Timestamp(e["end"] + "-01") + pd.offsets.MonthBegin(1)
    a, z = a.year + (a.month - 1) / 12, z.year + (z.month - 1) / 12
    ax.axvspan(a, z, color=CLSCOL[e["cls"]], alpha=.14, lw=0, zorder=0)
    lab = f"{e['offset']:+.1f} ppm" + ("\nrejected" if e["cls"] == "analyser" else "")
    yy = 366 if e["offset"] > 0 else 371.5
    ax.annotate(lab, ((a + z) / 2, yy), fontsize=7, color=CLSCOL[e["cls"]],
                ha="center", va="bottom")
ax.set_ylabel("CO$_2$ monthly background (ppm)")
ax.set_ylim(360, 432)
ax.legend(fontsize=7.5, loc="upper left", ncol=2)
ax.set_title("a  Bukit Kototabang CO$_2$ — the correction derived from the data itself")

ax = axes[1]
ax.bar(t, res, .075, color=[CLSCOL[c] for c in R.cls], label="as archived", zorder=2)
ax.plot(*brk(tc, resc), color=g.COL["BKT"], lw=1.3, marker="o", ms=2.4,
        label="after correction", zorder=3)
for k in (2, -2):
    ax.axhline(k * sd, color="#52514e", lw=.8, ls=":")
ax.axhline(0, color="#52514e", lw=.8)
ax.set_ylim(-13, 17)
ax.annotate(f"\u00b12\u03c3   (\u03c3 = {sd:.2f} ppm)", (2025.2, 2 * sd), xytext=(0, 3),
            textcoords="offset points", ha="right", fontsize=7, color="#52514e")
ax.annotate("2013-10/11 residual reaches\n\u221221.7 ppm (off scale)",
            (2014.3, -11.5), fontsize=6.5, color=CLSCOL["analyser"], ha="left", va="bottom",
            arrowprops=None)
ax.set_ylabel("residual from the\nreference model (ppm)")
ax.set_xlabel("year")
from matplotlib.patches import Patch
ax.legend(handles=[Patch(facecolor=CLSCOL[c], label=l) for c, l in
                   [("ok", "normal"), ("co2_cal", "CO\u2082 calibration \u2014 correctable"),
                    ("analyser", "analyser fault \u2014 reject"),
                    ("atmospheric", "real (2019 fire haze) \u2014 keep")]]
          + [plt.Line2D([], [], color=g.COL["BKT"], lw=1.3, marker="o", ms=3,
                        label="after correction")],
          fontsize=7, loc="upper left", ncol=3, columnspacing=1)
ax.set_title("b  Diagnosis \u2014 the pattern across CO$_2$, CH$_4$ and CO identifies each fault",
             fontsize=9)
fig.savefig(g.FIG / "f23_bkt_co2_correction.png")
plt.close(fig)
print("\nwrote figures/f23_bkt_co2_correction.png and outputs/bkt_co2_offsets.csv")
