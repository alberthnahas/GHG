"""Figures 14-16 - the NOAA flask comparison and the 22-year trend analyses.

Reads a11_flask.py and a13_trends_enso.py output."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G
import noaa_flask as NF
import i18n

INK, MUTED = "#1b1f24", "#6b7280"
ACC = G.COL["BKT"]
WARN = G.COL["JMB"]


def _tidy(ax):
    ax.tick_params(colors=MUTED, labelsize=8)
    for s in ax.spines.values():
        s.set_color("#d7dbe0")


# --------------------------------------------------------------------- f14 --
def fig14(insitu):
    fig, axes = plt.subplots(1, 3, figsize=(13.0, 4.2), gridspec_kw=dict(wspace=0.34))

    # (a) the time-base test: same flasks, same in-situ record, two conventions
    ax = axes[0]
    for how, col, mk, lab in (("raw", WARN, "s", "raw timestamps"),
                              ("corrected", ACC, "o", "corrected")):
        j = NF.match_insitu(insitu, "co2", how=how)
        ax.plot(j.insitu, j.flask, ls="none", marker=mk, ms=4, alpha=0.55,
                color=col, mec="none", label=lab)
    lim = (378, 428)
    ax.plot(lim, lim, color=INK, lw=1.2, ls="--", zorder=0)
    ax.set_xlim(*lim)
    ax.set_ylim(*lim)
    ax.set_aspect("equal")
    ax.set_xlabel("in-situ CO$_2$ (ppm)", color=MUTED)
    ax.set_ylabel("flask CO$_2$ (ppm)", color=MUTED)
    ax.set_title("a  Flask vs in-situ CO$_2$, matched hour", loc="left", color=INK)
    ax.legend(loc="upper left", fontsize=8)
    _tidy(ax)

    # (b) CO: a step, not a drift - the pre-2019 instrument reads high
    ax = axes[1]
    d = pd.read_csv(G.OUT / "z_drift.csv")
    s = d[d.species == "co"].sort_values("year")
    pre = s[s.year < 2019]
    post = s[s.year >= 2019]
    ax.bar(pre.year, pre["diff"], width=0.7, color=WARN, zorder=2)
    ax.bar(post.year, post["diff"], width=0.7, color=ACC, zorder=2)
    ax.axhline(0, color=INK, lw=1.2)
    ax.axvline(2018.5, color=MUTED, lw=1.2, ls=":")
    ax.annotate("instrument change", xy=(2018.2, -33), ha="right", fontsize=7.5, color=INK)
    ax.set_ylabel("flask − in-situ (ppb)", color=MUTED)
    ax.set_title("b  The same comparison for CO", loc="left", color=INK)
    _tidy(ax)

    # (c) methane's seasonal cycle against an inert tracer's
    ax = axes[2]

    def seas(sp):
        s = NF.monthly(sp, "bkt").dropna()
        t = s.index.year + (s.index.dayofyear - 1) / 365.25
        return pd.Series(G.harmonic_fit(t, s.values, 3, 2)["seasonal"], index=s.index)

    j = pd.concat([seas("ch4").rename("y"), seas("sf6").rename("x")], axis=1).dropna()
    sc = ax.scatter(j.x, j.y, c=j.index.month, cmap="twilight", s=16, zorder=3)
    sl, ic = np.polyfit(j.x, j.y, 1)
    xx = np.linspace(j.x.min(), j.x.max(), 50)
    ax.plot(xx, sl * xx + ic, color=INK, lw=1.8, zorder=4)
    ref = pd.read_csv(G.OUT / "z_sf6.csv")
    ref = ref[(ref.species == "ch4") & (ref.pair == "mlo-smo")].iloc[0]
    ax.annotate(f"slope {sl:.0f} ppb ppt$^{{-1}}$\n$r$ = {j.x.corr(j.y):.2f}\n"
                f"network NH−SH ratio {ref.network_gradient:.0f}",
                (.04, .96), xycoords="axes fraction", va="top", fontsize=8, color=INK)
    cb = fig.colorbar(sc, ax=ax, pad=0.02, ticks=[1, 4, 7, 10])
    cb.ax.set_yticklabels(["Jan", "Apr", "Jul", "Oct"], fontsize=7.5)
    cb.ax.tick_params(colors=MUTED)
    cb.outline.set_edgecolor("#d7dbe0")
    ax.set_xlabel("SF$_6$ seasonal anomaly (ppt)", color=MUTED)
    ax.set_ylabel("CH$_4$ seasonal anomaly (ppb)", color=MUTED)
    ax.set_title("c  CH$_4$ tracks an inert tracer", loc="left", color=INK)
    _tidy(ax)

    fig.suptitle("Figure 2  What an independent instrument says about the archive",
                 x=0.008, ha="left", fontsize=11, color=INK, y=1.03)
    fig.savefig(G.FIG / "f2_flask_validation.png")
    plt.close(fig)


# --------------------------------------------------------------------- f15 --
def fig15():
    lat = pd.read_csv(G.OUT / "z_latitude.csv")
    fig, axes = plt.subplots(1, 3, figsize=(13.0, 4.2), gridspec_kw=dict(wspace=0.34))

    # (a) CO2 by latitude - the Maritime Continent sits below every other site
    ax = axes[0]
    s = lat[lat.species == "co2"].sort_values("lat")
    for _, r in s.iterrows():
        hit = r.site == "bkt"
        ax.plot(r.lat, r.level, marker="D" if hit else "o", ms=11 if hit else 8,
                color=ACC if hit else MUTED, mec="white", mew=1.3, zorder=3)
        dx, dy = {"bkt": (0, 13), "kum": (12, 2), "mlo": (-12, -4),
                  "brw": (0, -15), "smo": (0, -15), "spo": (6, -15)}[r.site]
        ax.annotate(r.site.upper(), (r.lat, r.level), xytext=(dx, dy),
                    textcoords="offset points", fontsize=8, color=INK,
                    ha="center" if dx == 0 else ("left" if dx > 0 else "right"),
                    weight="600" if hit else "normal")
    ax.plot(s.lat, s.level, color=MUTED, lw=1, ls=":", zorder=1)
    ax.set_xlabel("station latitude (°N)", color=MUTED)
    ax.set_ylabel("mean CO$_2$ 2015–2025 (ppm)", color=MUTED)
    ax.set_title("a  Bukit Kototabang is a CO$_2$ minimum", loc="left", color=INK)
    ax.margins(y=0.25)
    _tidy(ax)

    # (b) SF6 seasonal amplitude - inert, so this is transport and nothing else
    ax = axes[1]
    s = lat[lat.species == "sf6"].sort_values("amp")
    y = np.arange(len(s))
    ax.barh(y, s.amp, height=0.6, color=[ACC if k == "bkt" else "#9aa3ad" for k in s.site], zorder=2)
    for yi, v in zip(y, s.amp):
        ax.annotate(f"{v:.2f}", (v, yi), xytext=(4, 0), textcoords="offset points",
                    va="center", fontsize=8, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels([k.upper() for k in s.site], fontsize=8)
    ax.set_xlabel("SF$_6$ seasonal amplitude (ppt)", color=MUTED)
    ax.set_title("b  SF$_6$ seasonal amplitude by site", loc="left", color=INK)
    ax.margins(x=0.18)
    _tidy(ax)

    # (c) flask CO percentiles - background flat, polluted tail falling
    ax = axes[2]
    per = pd.read_csv(G.OUT / "z_co_percentile_year.csv", index_col=0)
    tr = pd.read_csv(G.OUT / "z_co_percentile_trend.csv").set_index("percentile")
    for q, col, mk, ls in (("p90", WARN, "s", "--"), ("p50", ACC, "o", "-"),
                           ("p10", G.COL["PLU"], "D", ":")):
        ax.plot(per.index, per[q], marker=mk, ls=ls, lw=2, ms=6, color=col,
                mec="white", mew=1, label=f"{q}  {tr.loc[q,'trend']:+.2f} ppb yr$^{{-1}}$")
    ax.set_ylabel("CO (ppb)", color=MUTED)
    ax.set_xlabel("year", color=MUTED)
    ax.set_title("c  Flask CO percentiles, 2004–2025", loc="left", color=INK)
    ax.legend(loc="upper right", fontsize=7.5, ncol=1)
    ax.margins(y=0.18)
    _tidy(ax)

    fig.suptitle("Figure 3  Bukit Kototabang inside the global flask network",
                 x=0.008, ha="left", fontsize=11, color=INK, y=1.03)
    fig.savefig(G.FIG / "f3_flask_network.png")
    plt.close(fig)


# --------------------------------------------------------------------- f16 --
def fig16():
    acc = pd.read_csv(G.OUT / "w_accel.csv")
    dec = pd.read_csv(G.OUT / "w_decadal.csv")
    grad = pd.read_csv(G.OUT / "w_gradient.csv")
    part = pd.read_csv(G.OUT / "w_co_partition.csv")
    fig, axes = plt.subplots(1, 3, figsize=(13.0, 4.3), gridspec_kw=dict(wspace=0.36))

    # (a) decadal growth, each species normalised by its 2004-2013 rate, so six
    # quantities in five different units share one axis honestly
    ax = axes[0]
    # CO is excluded here: its trend is negative, so a ratio of two negative
    # slopes would read as "acceleration" when it means a slowing decline.
    order = ["co2", "ch4", "n2o", "sf6"]
    lab = {"co2": "CO$_2$", "ch4": "CH$_4$", "n2o": "N$_2$O", "sf6": "SF$_6$", "co": "CO"}
    x = np.arange(len(order))
    early, late = [], []
    for sp in order:
        d = dec[dec.species == sp].set_index("period")
        e = d.iloc[0].trend
        early.append(1.0)
        late.append(d.iloc[1].trend / e)
    ax.bar(x - 0.19, early, width=0.36, color="#9aa3ad", zorder=2, label="2004–2013")
    ax.bar(x + 0.19, late, width=0.36, color=ACC, zorder=2, label="2014–2025")
    for xi, v, sp in zip(x, late, order):
        ax.annotate(f"×{v:.2f}", (xi + 0.19, v), xytext=(0, 4), textcoords="offset points",
                    ha="center", fontsize=8, color=INK)
    ax.axhline(1, color=INK, lw=1.1)
    ax.set_xticks(x)
    ax.set_xticklabels([lab[s] for s in order])
    ax.set_ylabel("growth rate / its 2004–2013 value", color=MUTED)
    ax.set_title("a  Growth is accelerating, methane most", loc="left", color=INK)
    ax.set_ylim(0, 3.0)
    ax.legend(loc="upper right", fontsize=8)
    ax.margins(y=0.22)
    _tidy(ax)

    # (b) is the north-south difference widening or closing?
    ax = axes[1]
    g = grad.set_index("species")
    order2 = ["co2", "ch4", "sf6", "n2o", "co"]
    pct = [100 * g.loc[s, "trend"] / g.loc[s, "mean_gradient"] for s in order2]
    y = np.arange(len(order2))[::-1]
    cols = [ACC if v > 0 else WARN for v in pct]
    ax.barh(y, pct, height=0.55, color=cols, zorder=2)
    ax.axvline(0, color=INK, lw=1.2)
    for yi, v, sp in zip(y, pct, order2):
        sig = "" if g.loc[sp, "significant"] else "  (ns)"
        ax.annotate(f"{v:+.2f} %/yr{sig}", (v, yi), xytext=(5 if v > 0 else -5, 0),
                    textcoords="offset points", va="center",
                    ha="left" if v > 0 else "right", fontsize=7.5, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels([lab[s] for s in order2])
    ax.set_xlabel("change in the Barrow − South Pole difference", color=MUTED)
    ax.set_title("b  Only CO's hemispheric gap is closing", loc="left", color=INK)
    ax.margins(x=0.42)
    _tidy(ax)

    # (c) how much of BKT's CO seasonal cycle is imported
    ax = axes[2]
    m = part.month
    ax.plot(m, part.observed, marker="o", lw=2, ms=6, color=INK, mec="white", mew=1,
            label="observed")
    ax.plot(m, part.transport, marker="s", ls="--", lw=2, ms=6, color=ACC, mec="white",
            mew=1, label="transport (from SF$_6$)")
    ax.plot(m, part.local, marker="^", ls="-.", lw=2, ms=6, color=WARN, mec="white",
            mew=1, label="local emission")
    ax.axhline(0, color=MUTED, lw=1, zorder=0)
    for mm in (2, 9):
        ax.axvline(mm, color="#9aa3ad", lw=6, alpha=0.22, zorder=0)
    ax.annotate("the two burning seasons", xy=(5.5, 27), fontsize=7.5, color=INK, ha="center")
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"])
    ax.set_ylabel("CO seasonal anomaly (ppb)", color=MUTED)
    ax.set_title("c  Half the CO cycle is emitted nearby", loc="left", color=INK)
    ax.legend(loc="lower right", fontsize=7.5)
    _tidy(ax)

    fig.suptitle("Figure 24  Twenty-two years: acceleration, hemispheric gradients, and what CO's cycle is made of",
                 x=0.008, ha="left", fontsize=11, color=INK, y=1.03)
    fig.savefig(G.FIG / "f24_trends_gradients.png")
    plt.close(fig)


def main():
    ins = pd.read_pickle(G.OUT / "all.pkl")
    fig14(ins[ins.station == "BKT"])
    fig15()
    fig16()


if __name__ == "__main__":
    i18n.install(i18n.from_argv())
    G.style()
    main()
    print("wrote f2_flask_validation.png, f3_flask_network.png, f24_trends_gradients.png")
