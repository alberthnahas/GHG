"""All report figures."""
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import ghg_common as g
import i18n

g.style()
df = pd.read_pickle(g.OUT / "all.pkl")
raw = pd.concat([g._load_raw(c).assign(code=c) for c in g.ORDER], ignore_index=True)
SP = {"co2": ("CO$_2$", "ppm"), "ch4": ("CH$_4$", "ppb"), "co": ("CO", "ppb")}
NAME = {c: g.STATIONS[c][0] for c in g.ORDER}


def label_last(ax, x, y, c, dx=6):
    ax.annotate(c, (x, y), xytext=(dx, 0), textcoords="offset points",
                color=g.COL[c], fontsize=8, fontweight="bold", va="center")


def spread_labels(ax, items, x, dx=6, minsep=0.062):
    """Place right-edge series labels, pushed apart so they never overlap.
    `items` = [(code, y_data), ...]; minsep is in axes fraction."""
    lo, hi = ax.get_ylim()
    it = sorted(items, key=lambda p: p[1])
    ys = [(v - lo) / (hi - lo) for _, v in it]
    for i in range(1, len(ys)):
        ys[i] = max(ys[i], ys[i - 1] + minsep)
    over = ys[-1] - (1 - minsep / 2)
    if over > 0:
        ys = [y - over for y in ys]
    for (c, _), yf in zip(it, ys):
        ax.annotate(c, (x, lo + yf * (hi - lo)), xytext=(dx, 0),
                    textcoords="offset points", color=g.COL[c], fontsize=8,
                    fontweight="bold", va="center", annotation_clip=False)


# ---------------------------------------------------------------- F1 coverage
def f1():
    fig = plt.figure(figsize=(10, 5.8))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.05, 1], hspace=.55, wspace=.18)
    ax = fig.add_subplot(gs[0, :])
    for i, c in enumerate(g.ORDER):
        s = df[df.station == c]
        for j, sp in enumerate(["co2", "ch4", "co"]):
            t = s.loc[s[sp].notna(), "time_local"]
            if not len(t):
                continue
            yy = i + 0.26 - j * 0.26
            ax.plot(t, np.full(len(t), yy), "|", color=g.COL[c],
                    alpha=[1, .72, .45][j], ms=4.2, mew=0.5)
    for i in range(5):
        for j, sp in enumerate(["CO$_2$", "CH$_4$", "CO"]):
            ax.annotate(sp, (0.0, i + .26 - j * .26), xycoords=("axes fraction", "data"),
                        xytext=(-3, 0), textcoords="offset points", ha="right",
                        va="center", fontsize=6.2, color="#52514e")
    ax.set_yticks(range(5))
    ax.set_yticklabels([f"{c}  {NAME[c]}" for c in g.ORDER], fontsize=8, fontweight="bold")
    ax.tick_params(axis="y", which="major", pad=22, length=0)
    for i, c in enumerate(g.ORDER):
        ax.get_yticklabels()[i].set_color(g.COL[c])
    ax.set_ylim(-0.55, 4.55)
    ax.set_xlim(pd.Timestamp("2001-01-01"), pd.Timestamp("2026-12-31"))
    ax.set_title("a  Hourly data availability by station and species")
    ax.grid(axis="y", alpha=0)

    # b, c: the time-base diagnostic, before and after
    for k, (which, ttl) in enumerate([("raw", "b  As archived — sites 7–9 h out of phase"),
                                      ("fix", "c  Converted to local time — aligned")]):
        ax = fig.add_subplot(gs[1, k])
        for c in g.ORDER:
            if which == "raw":
                r = raw[raw.code == c]
                v = pd.to_numeric(r["co2d"].fillna(r.get("co2")), errors="coerce")
                m = pd.DataFrame({"h": r["hour"].values, "v": v.values}).dropna().groupby("h").v.median()
            else:
                s = df[df.station == c]
                m = s.groupby("hour_local").co2.median()
            m = m - m.mean()
            ax.plot(m.index, m.values, ls=g.LS[c], color=g.COL[c], lw=1.8,
                    marker=g.MRK[c], ms=3.2, label=c)
            ax.plot([m.values.argmin()], [m.values.min()], "o", ms=9, mfc="none",
                    mec=g.COL[c], mew=1.4)
        ax.axvspan(12, 16, color="#0b0b0b", alpha=.06, lw=0)
        ax.set_xlim(-0.5, 23.5); ax.set_xticks(range(0, 24, 6))
        ax.set_xlabel("hour of day" + ("  (as archived)" if which == "raw" else "  (local time)"))
        ax.set_ylim(-24, 30)
        ax.set_title(ttl, fontsize=9)
        if k == 0:
            ax.set_ylabel("CO$_2$ anomaly (ppm)")
            ax.legend(ncol=5, fontsize=7, loc="upper center", columnspacing=.9,
                      handlelength=1.6)
        else:
            ax.annotate("well-mixed\nafternoon", (14, 26), ha="center", va="top",
                        fontsize=7, color="#52514e")
            ax.annotate("○ = daily minimum", (23, -22), ha="right", fontsize=7,
                        color="#52514e")
    fig.savefig(g.FIG / "f1_coverage_timebase.png")
    plt.close(fig)


# ---------------------------------------------------------------- F2 diurnal
def f2():
    """Shape and magnitude are separated: the amplitudes span two orders of
    magnitude, so putting them on one linear axis would erase four of five sites
    and a log axis would distort the shape."""
    fig = plt.figure(figsize=(10.5, 5.4))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.35, 1], hspace=.5, wspace=.22)
    amp = {}
    for j, sp in enumerate(["co2", "ch4", "co"]):
        ax = fig.add_subplot(gs[0, j])
        for c in g.ORDER:
            m = df[df.station == c].groupby("hour_local")[sp].median()
            a = m.max() - m.min()
            amp[(sp, c)] = a
            ax.plot(m.index, (m - m.mean()) / a, ls=g.LS[c], color=g.COL[c],
                    lw=1.8, marker=g.MRK[c], ms=3, label=c)
        ax.axhline(0, color="#52514e", lw=.7, alpha=.5)
        ax.axvspan(12, 16, color="#0b0b0b", alpha=.05, lw=0)
        ax.set_xlim(0, 23); ax.set_xticks(range(0, 24, 6))
        ax.set_ylim(-.72, .72)
        ax.set_xlabel("hour (local time)")
        ax.set_title(f"{SP[sp][0]}")
        if j == 0:
            ax.set_ylabel("normalised anomaly\n(fraction of own amplitude)")
            ax.legend(ncol=2, loc="lower left", fontsize=7)

    ax = fig.add_subplot(gs[1, :])
    x = np.arange(3); w = .16
    for i, c in enumerate(g.ORDER):
        v = [amp[(sp, c)] for sp in ["co2", "ch4", "co"]]
        ax.bar(x + (i - 2) * w, v, w * .88, color=g.COL[c], label=c,
               edgecolor="#fcfcfb", lw=1.2)
        for xi, vi in zip(x + (i - 2) * w, v):
            ax.annotate(f"{vi:.0f}" if vi >= 10 else f"{vi:.1f}", (xi, vi),
                        xytext=(0, 2), textcoords="offset points", ha="center",
                        fontsize=6.5, color=g.COL[c], fontweight="bold")
    ax.set_yscale("log"); ax.set_ylim(1, 1500)
    ax.set_xticks(x)
    ax.set_xticklabels(["CO$_2$  (ppm)", "CH$_4$  (ppb)", "CO  (ppb)"])
    ax.set_ylabel("diurnal peak-to-peak\namplitude (log scale)")
    ax.legend(ncol=5, fontsize=7.5, loc="upper left", columnspacing=1)
    fig.suptitle("Median diurnal composite: shape (top) and magnitude (bottom) shown separately",
                 fontsize=9.5, y=.98)
    fig.savefig(g.FIG / "f6_diurnal.png")
    plt.close(fig)
    pd.Series(amp).unstack(0).to_csv(g.OUT / "diurnal_amplitude.csv")


# ------------------------------------------------- F3 nightly-ratio fingerprint
def f3():
    K = pd.read_pickle(g.OUT / "nightly_slopes.pkl")
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.9),
                             gridspec_kw=dict(width_ratios=[1.25, 1]))
    ax = axes[0]
    for i, c in enumerate(g.ORDER):
        R = K[(c, "ΔCO/ΔCO₂")]
        if len(R) < 15:
            continue
        v = R.slope.values
        ax.scatter(np.full(len(v), i) + np.random.default_rng(1).normal(0, .07, len(v)),
                   v, s=7, color=g.COL[c], alpha=.35, lw=0, marker=g.MRK[c])
        q = np.percentile(v, [25, 50, 75])
        ax.plot([i - .3, i + .3], [q[1]] * 2, color="#0b0b0b", lw=2, zorder=5)
        ax.plot([i, i], q[[0, 2]], color="#0b0b0b", lw=1, zorder=5)
        ax.annotate(f"{q[1]:.2f}\nn={len(v)}", (i, q[1]), xytext=(0, 9),
                    textcoords="offset points", ha="center", fontsize=7.5,
                    fontweight="bold", color="#0b0b0b")
    for y, lab, col in [(100, "smouldering peat / biomass burning  (60–200)", "#eb6834"),
                        (8, "efficient fossil combustion  (3–15)", "#4a3aa7")]:
        ax.axhline(y, color=col, lw=1, ls=":", alpha=.8)
        ax.annotate(lab, (-0.45, y), fontsize=7, color=col, ha="left", va="bottom")
    ax.set_yscale("symlog", linthresh=1)
    ax.set_xticks(range(5)); ax.set_xticklabels([f"{c}\n{NAME[c]}" for c in g.ORDER], fontsize=7.5)
    ax.set_ylabel("ΔCO/ΔCO$_2$  (ppb ppm$^{-1}$)"); ax.set_xlim(-0.55, 4.55)
    ax.set_title("a  Nightly emission ratio — one point per tightly-coupled night")

    ax = axes[1]
    T = pd.read_csv(g.OUT / "nightly_emission_ratios.csv")
    p = T.pivot_table(index="station", columns="ratio", values="pct_nights").reindex(g.ORDER)
    x = np.arange(5); w = 0.27
    hatch = ["", "///", "..."]
    for k, col in enumerate(p.columns):
        ax.bar(x + (k - 1) * w, p[col].values, w * 0.92, label=col,
               color=[g.COL[c] for c in g.ORDER], alpha=[1, .75, .5][k],
               hatch=hatch[k], edgecolor="#fcfcfb", lw=1.2)
    ax.set_xticks(x); ax.set_xticklabels(g.ORDER, fontsize=8)
    ax.set_ylabel("% of nights with $r^2 \\geq 0.7$")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor="#8a8a86", hatch=h, edgecolor="#fcfcfb", label=l)
                       for h, l in zip(hatch, p.columns)],
              fontsize=7, loc="upper left", title="colour = station", title_fontsize=7)
    ax.set_title("b  How often the species are co-emitted")
    fig.tight_layout()
    fig.savefig(g.FIG / "f8_fingerprint.png")
    plt.close(fig)


# ---------------------------------------------------------- F4 BKT CO / ENSO
def f4():
    b = df[df.station == "BKT"].set_index("time_local").sort_index()
    ann = pd.read_csv(g.OUT / "bkt_annual_co.csv", index_col=0)
    fig, axes = plt.subplots(2, 1, figsize=(10, 5.4), sharex=True,
                             gridspec_kw=dict(height_ratios=[2.1, 1], hspace=0.16))
    ax = axes[0]
    m = b.co.resample("MS")
    hi, med, lo = m.quantile(.95), m.median(), m.quantile(.10)
    ax.fill_between(hi.index, lo, hi, color=g.COL["BKT"], alpha=.18, lw=0,
                    label="10th\u201395th percentile of hourly values")
    ax.plot(med.index, med, color=g.COL["BKT"], lw=1.1, label="monthly median")
    ax.plot(lo.index, lo, color="#0b0b0b", lw=1, ls="--", label="10th pct (regional background)")
    ax.set_yscale("log")
    ax.set_ylim(38, 6000)
    ax.set_ylabel("CO (ppb)")
    ax.annotate("Oct 2015 \u2014 median 1493 ppb,\n95th pct 3685 ppb:\n17\u00d7 the record background;\n75% of the month above 1000 ppb",
                (pd.Timestamp("2015-10-01"), 3685),
                xytext=(-14, -2), textcoords="offset points", fontsize=7.5,
                color="#0b0b0b", ha="right", va="top",
                arrowprops=dict(arrowstyle="-", lw=.8, color="#52514e"))
    for yr, lab in [(2002, "2002"), (2006, "2006"), (2019, "2019"), (2023, "2023")]:
        v = hi.loc[f"{yr}-10-01"] if f"{yr}-10-01" in hi.index.astype(str).tolist() else None
        pk = hi[f"{yr}-01-01":f"{yr}-12-31"]
        if len(pk.dropna()):
            ax.annotate(lab, (pk.idxmax(), pk.max()), xytext=(0, 4),
                        textcoords="offset points", ha="center", fontsize=6.5,
                        color="#52514e")
    ax.legend(loc="lower left", ncol=3, fontsize=7.5)
    ax.set_title("a  Carbon monoxide at Bukit Kototabang, 2001\u20132024 (log scale)")

    ax = axes[1]
    o = ann.oni_son.dropna()
    xs = [pd.Timestamp(f"{int(y)}-10-01") for y in o.index]
    ax.bar(xs, o.values, width=250, color=np.where(o.values > 0, "#e34948", "#2a78d6"),
           edgecolor="#fcfcfb", lw=.8)
    ax.axhline(0, color="#52514e", lw=.8)
    ax.set_ylabel("ONI, Sep\u2013Nov (\u00b0C)")
    ax.set_xlim(pd.Timestamp("2001-01-01"), pd.Timestamp("2025-06-30"))
    ax.set_title("b  El Ni\u00f1o (red) / La Ni\u00f1a (blue) state of the burning season", fontsize=9)
    ax.annotate("Spearman $\\rho$ = +0.49 between the SON ONI\nand the annual 95th-percentile CO  (n = 23)",
                (.015, .06), xycoords="axes fraction", ha="left", va="bottom",
                fontsize=7.5, color="#0b0b0b")
    for yr in (2002, 2015, 2023):
        ax.annotate(str(yr), (pd.Timestamp(f"{yr}-10-01"), o.loc[yr]), xytext=(0, 3),
                    textcoords="offset points", ha="center", fontsize=7, color="#0b0b0b")
    fig.savefig(g.FIG / "f14_bkt_co_enso.png")
    plt.close(fig)


# ------------------------------------------------------------- F5 seasonality
def f5():
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.4))
    tab = {}
    for ax, sp in zip(axes, ["ch4", "co", "co2"]):
        aft = g.clean(df, sp)
        aft = aft[aft.hour_local.between(12, 16)]
        ends = []
        for c in g.ORDER:
            s = aft[aft.station == c]
            m = s.groupby([s.year, s.month])[sp].quantile(.2).dropna()
            if len(m) < 24:
                continue
            t = np.array([y + (mo - .5) / 12 for y, mo in m.index])
            f = g.harmonic_fit(t, m.values, n_harm=3, poly=2)
            an = pd.Series(f["y"] - f["trend"]).groupby([mo for _, mo in m.index]).mean()
            an = an - an.mean()
            ax.plot(an.index, an.values, ls=g.LS[c], color=g.COL[c], lw=1.9,
                    marker=g.MRK[c], ms=3.5, label=c)
            ends.append((c, an.values[-1]))
            tab[(sp, c)] = an
        ax.axhline(0, color="#52514e", lw=.7, alpha=.6)
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(list("JFMAMJJASOND"), fontsize=7)
        ax.set_xlim(.6, 13.2)
        ax.set_title(f"{SP[sp][0]} ({SP[sp][1]})")
        ax.set_xlabel("month")
        spread_labels(ax, ends, 12)
    axes[0].set_ylim(-52, 52)
    axes[0].axvspan(.6, 3.5, color="#2a78d6", alpha=.07, lw=0)
    axes[0].axvspan(5.5, 10.5, color="#eb6834", alpha=.07, lw=0)
    axes[0].annotate("NW monsoon\nN-hemisphere air", (2.05, .02), xycoords=("data", "axes fraction"),
                    ha="center", va="bottom", fontsize=6.5, color="#2a78d6")
    axes[0].annotate("SE monsoon\nS-hemisphere air", (8, .02), xycoords=("data", "axes fraction"),
                    ha="center", va="bottom", fontsize=6.5, color="#eb6834")
    axes[0].legend(fontsize=7, loc="upper right", ncol=2, columnspacing=.8,
                   handlelength=1.5)
    fig.suptitle("Detrended seasonal cycle of the regional background (afternoon 20th percentile)",
                 fontsize=9.5, y=1.03)
    fig.tight_layout()
    fig.savefig(g.FIG / "f18_seasonal.png")
    plt.close(fig)
    pd.DataFrame({k: v for k, v in tab.items()}).round(1).to_csv(g.OUT / "seasonal_anomaly.csv")


# ------------------------------------------------------------------ F6 trends
def f6():
    fig = plt.figure(figsize=(10.5, 5.6))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.3, 1], hspace=.42, wspace=.22)
    for j, sp in enumerate(["co2", "ch4"]):
        ax = fig.add_subplot(gs[0, j])
        aft = g.clean(df, sp)
        aft = aft[aft.hour_local.between(12, 16)]
        ends = []
        for c in g.ORDER:
            s = aft[aft.station == c]
            m = s.groupby([s.year, s.month])[sp].quantile(.2)
            n = s.groupby([s.year, s.month])[sp].count()
            m = m[n >= 20].dropna()
            if len(m) < 12:
                continue
            t = np.array([y + (mo - .5) / 12 for y, mo in m.index])
            v = m.values.astype(float)
            # break the line across gaps longer than two months
            gap = np.where(np.diff(t) > 2.5 / 12)[0]
            t = np.insert(t, gap + 1, np.nan); v = np.insert(v, gap + 1, np.nan)
            ax.plot(t, v, ls=g.LS[c], color=g.COL[c], lw=1.3,
                    marker=g.MRK[c], ms=2.4, label=c)
            ends.append((c, v[~np.isnan(v)][-1]))
        for st, ssp, t0, t1, _ in g.SUSPECT:
            if ssp in (sp, "all"):
                a, b = [pd.Timestamp(x).year + (pd.Timestamp(x).month - 1) / 12 for x in (t0, t1)]
                ax.axvspan(a, b, color="#e34948", alpha=.13, lw=0)
        ax.set_xlabel("year"); ax.set_ylabel(f"{SP[sp][0]} ({SP[sp][1]})")
        ax.set_xlim(2009.3, 2027.4)
        ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(3))
        ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: f"{int(v)}"))
        ax.set_title(f"{SP[sp][0]} regional background  (afternoon 20th percentile)", fontsize=9)
        spread_labels(ax, ends, 2026.4, dx=2)
        if j == 0:
            ax.legend(fontsize=7, loc="upper left", ncol=2, columnspacing=.8, handlelength=1.5)
            ax.annotate("red bands = periods\nexcluded as instrumentally\nsuspect (Table 2)",
                        (.97, .06), xycoords="axes fraction", fontsize=7,
                        color="#e34948", ha="right", va="bottom")

    T = pd.read_csv(g.OUT / "trends.csv")
    for j, (sp, unit) in enumerate([("co2", "ppm yr$^{-1}$"), ("ch4", "ppb yr$^{-1}$")]):
        ax = fig.add_subplot(gs[1, j])
        t = T[T.species == sp].reset_index(drop=True)
        x = np.arange(len(t))
        ax.bar(x, t.trend, .6, yerr=(t.trend - t.lo, t.hi - t.trend),
               color=[g.COL[c] for c in t.station], edgecolor="#fcfcfb", lw=1.2,
               error_kw=dict(ecolor="#0b0b0b", lw=1, capsize=2.5))
        for xi, v, h in zip(x, t.trend, t.hi):
            ax.annotate(f"{v:+.2f}", (xi, h), xytext=(0, 3), textcoords="offset points",
                        ha="center", fontsize=7.5, fontweight="bold", color="#0b0b0b")
        ax.set_xticks(x)
        ax.set_xticklabels([f"{r.station}\n{r.segment}" for r in t.itertuples()], fontsize=7)
        ax.set_ylabel(f"{SP[sp][0]} growth rate\n({unit})")
        ax.set_ylim(0, t.hi.max() * 1.3)
        ax.set_title("Theil\u2013Sen growth rate of the seasonally-adjusted "
                     "background (95% CI)" if j == 0 else " ", fontsize=8.5, loc="left")
    fig.savefig(g.FIG / "f22_trends.png")
    plt.close(fig)


# ------------------------------------------------------------- F7 Jakarta week
def f7():
    k = df[df.station == "KMY"].copy()
    fig = plt.figure(figsize=(10.5, 3.6))
    gs = fig.add_gridspec(1, 4, width_ratios=[1.5, 1, 1, 1], wspace=.42)

    ax = fig.add_subplot(gs[0, 0])
    base = k[k.hour_local.between(12, 16)].co.quantile(.05)
    for sel, lab, col, ls in [(k.dow < 5, "Mon–Fri", "#1baf7a", "-"),
                              (k.dow == 6, "Sunday", "#4a3aa7", "--")]:
        m = k[sel].groupby("hour_local").co.median() - base
        ax.plot(m.index, m.values, ls=ls, color=col, lw=2.1, marker="o" if ls == "-" else "D",
                ms=3.2, label=lab)
    wk = k[k.dow < 5].groupby("hour_local").co.median()
    su = k[k.dow == 6].groupby("hour_local").co.median()
    ax.fill_between(wk.index, su - base, wk - base, color="#1baf7a", alpha=.15, lw=0)
    h = int((wk - su).idxmax())
    ax.annotate(f"07:00 rush-hour peak is\n{100*(wk[h]-su[h])/(wk[h]-base):.0f}% lower on Sundays",
                (h, wk[h] - base), xytext=(20, -22), textcoords="offset points",
                fontsize=7.5, color="#0b0b0b",
                arrowprops=dict(arrowstyle="-", lw=.8, color="#52514e"))
    ax.set_xlim(0, 23); ax.set_xticks(range(0, 24, 6))
    ax.set_xlabel("hour (local time)")
    ax.set_ylabel("CO enhancement (ppb)")
    ax.legend(fontsize=8, loc="center right")
    ax.set_title("a  CO: traffic has a weekly cycle", fontsize=9)

    days = ["M", "T", "W", "T", "F", "S", "S"]
    for j, sp in enumerate(["co", "ch4", "co2"]):
        ax = fig.add_subplot(gs[0, j + 1])
        base = k[k.hour_local.between(12, 16)][sp].quantile(.05)
        m = k.groupby("dow")[sp].median() - base
        ref = m[:5].mean()
        ax.bar(range(7), m.values, .74,
               color=["#1baf7a"] * 5 + ["#93ddc4"] * 2,
               hatch=[""] * 5 + ["///", "///"], edgecolor="#fcfcfb", lw=1.2)
        ax.axhline(ref, color="#0b0b0b", lw=1, ls="--")
        pct = 100 * (m[6] - ref) / ref
        ax.annotate(f"Sun\n{pct:+.1f}%", (6, m[6]), xytext=(0, 5),
                    textcoords="offset points", ha="center", fontsize=8,
                    fontweight="bold", color="#0b0b0b")
        ax.set_xticks(range(7)); ax.set_xticklabels(days, fontsize=7)
        ax.set_ylabel(f"{SP[sp][0]} ({SP[sp][1]})")
        ax.set_ylim(0, m.max() * 1.45)
        ax.set_title(f"{'bcd'[j]}  {SP[sp][0]}", fontsize=9)
    fig.suptitle("Kemayoran, Jakarta — the weekly cycle separates traffic from waste "
                 "(dashed line = Mon–Fri mean; hatched = weekend)", fontsize=9.5, y=1.04)
    fig.savefig(g.FIG / "f9_jakarta_week.png")
    plt.close(fig)


# --------------------------------------------------------------- F8 2019 haze
def f8():
    b = df[df.station == "BKT"].set_index("time_local").sort_index()
    ep = b["2019-08-15":"2019-11-05"]
    cl = b["2019-07-01":"2019-08-14"][["co", "ch4"]].quantile(.10)
    fig = plt.figure(figsize=(10, 4.4))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.75, 1], hspace=.35, wspace=.28)
    for i, sp in enumerate(["co", "ch4"]):
        ax = fig.add_subplot(gs[i, 0])
        ax.plot(ep.index, ep[sp], color=g.COL["BKT"], lw=.7)
        ax.axhline(cl[sp], color="#0b0b0b", lw=1, ls="--")
        ax.annotate("pre-fire background", (ep.index[5], cl[sp]), xytext=(0, 6),
                    textcoords="offset points", fontsize=7, color="#0b0b0b",
                    bbox=dict(fc="#fcfcfb", ec="none", pad=1))
        ax.set_ylabel(f"{SP[sp][0]} ({SP[sp][1]})")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
        if i == 0:
            ax.set_title("a  Sumatra peat-fire haze reaching Bukit Kototabang, 2019")

    ax = fig.add_subplot(gs[:, 1])
    d = ep[["co", "ch4"]].dropna()
    d = d[d.co > cl.co]
    ax.scatter(d.co, d.ch4, s=8, color=g.COL["BKT"], alpha=.3, lw=0)
    sl, ic = np.polyfit(d.co, d.ch4, 1)
    r = np.corrcoef(d.co, d.ch4)[0, 1]
    rng = np.random.default_rng(0)
    bs = [np.polyfit(d.co.values[i], d.ch4.values[i], 1)[0]
          for i in (rng.integers(0, len(d), len(d)) for _ in range(400))]
    lo, hi = np.percentile(bs, [2.5, 97.5])
    xx = np.linspace(d.co.min(), d.co.max(), 100)
    ax.plot(xx, sl * xx + ic, color="#0b0b0b", lw=1.8, zorder=5)
    ax.annotate(f"ΔCH$_4$/ΔCO = {sl:.3f}\n[{lo:.3f}, {hi:.3f}] ppb ppb$^{{-1}}$\n"
                f"$r$ = {r:.2f},  n = {len(d)}\n\n"
                f"reported emission ratio for\nIndonesian peat: 0.06–0.10",
                (.04, .96), xycoords="axes fraction", va="top", fontsize=7.5)
    ax.set_xlabel("CO (ppb)"); ax.set_ylabel("CH$_4$ (ppb)")
    ax.set_title("b  Plume emission ratio")
    fig.savefig(g.FIG / "f15_2019_haze.png")
    plt.close(fig)


def main():
    for fn in (f1, f2, f3, f4, f5, f6, f7, f8):
        fn()
        print("ok", fn.__name__)


if __name__ == "__main__":
    i18n.install(i18n.from_argv())
    main()
