"""Figures 18-19 for the third pass.  Reads a17_extra2.py output."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G
import i18n

INK, MUTED = "#1b1f24", "#6b7280"
MONTHS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]


def _tidy(ax):
    ax.tick_params(colors=MUTED, labelsize=8)
    for s in ax.spines.values():
        s.set_color("#d7dbe0")


# --------------------------------------------------------------------- f18 --
def fig18():
    sev = pd.read_csv(G.OUT / "u_severity.csv")
    ons = pd.read_csv(G.OUT / "u_onset.csv")
    kmy = pd.read_csv(G.OUT / "u_kmy_hourly.csv")
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.3), gridspec_kw=dict(wspace=0.34))

    # (a) peak against duration - the two are not the same ranking
    ax = axes[0]
    ax.scatter(sev.days_over_1000, sev.peak, s=44, c=sev.oni, cmap="RdBu_r",
               vmin=-2, vmax=2, edgecolor="white", linewidth=1.1, zorder=3)
    for _, r in sev.iterrows():
        if r.peak > 1400 or r.days_over_1000 > 5:
            dx = (-8, 3) if int(r.year) == 2015 else (6, 3)
            ax.annotate(str(int(r.year)), (r.days_over_1000, r.peak), xytext=dx,
                        textcoords="offset points", fontsize=8, color=INK,
                        ha="right" if int(r.year) == 2015 else "left")
    sc = ax.collections[0]
    cb = fig.colorbar(sc, ax=ax, pad=0.02)
    cb.set_label("SON ONI (°C)", color=MUTED, fontsize=8)
    cb.ax.tick_params(colors=MUTED, labelsize=7.5)
    cb.outline.set_edgecolor("#d7dbe0")
    ax.set_xlabel("days above 1,000 ppb", color=MUTED)
    ax.set_ylabel("peak daily CO (ppb)", color=MUTED)
    ax.set_title("a  Severity depends on how you measure it", loc="left", color=INK)
    _tidy(ax)

    # (b) the burning season ends when the rains arrive
    ax = axes[1]
    v = ons.dropna(subset=["oni"])
    ax.scatter(v.oni, v.onset_doy, s=46, color=G.COL["BKT"], edgecolor="white",
               linewidth=1.1, zorder=3)
    sl, ic = np.polyfit(v.oni, v.onset_doy, 1)
    xx = np.linspace(v.oni.min(), v.oni.max(), 20)
    ax.plot(xx, sl * xx + ic, color=INK, lw=1.8, zorder=2)
    for _, r in v.iterrows():
        if r.oni > 1 or r.onset_doy > 325:
            ax.annotate(str(int(r.year)), (r.oni, r.onset_doy), xytext=(6, 3),
                        textcoords="offset points", fontsize=8, color=INK)
    ax.annotate(f"{sl:.0f} days later per °C\n$r$ = {v.oni.corr(v.onset_doy):+.2f}",
                (.04, .95), xycoords="axes fraction", va="top", fontsize=8, color=INK)
    ax.set_xlabel("SON Oceanic Niño Index (°C)", color=MUTED)
    ax.set_ylabel("day of year the CO collapses", color=MUTED)
    ax.set_title("b  El Niño delays the rains", loc="left", color=INK)
    _tidy(ax)

    # (c) the two Jakarta ratios run in antiphase.  Both are normalised to their
    # own daily mean so they share one axis: a second y-scale would let the eye
    # read a crossing point that has no meaning.
    ax = axes[2]
    k = kmy.sort_values("hour")
    for col, c, mk, ls, lab in (("co_co2", G.COL["KMY"], "o", "-", "ΔCO/ΔCO$_2$"),
                                ("ch4_co2", G.COL["PLU"], "s", "--", "ΔCH$_4$/ΔCO$_2$")):
        ax.plot(k.hour, k[col] / k[col].mean(), marker=mk, ls=ls, lw=2, ms=6,
                color=c, mec="white", mew=1.1, label=lab)
    ax.axhline(1, color=MUTED, lw=1, zorder=0)
    for h0, h1 in ((6, 9), (17, 21)):
        ax.axvspan(h0, h1, color="#9aa3ad", alpha=0.16, zorder=0)
    ax.annotate("traffic peaks", xy=(19, 1.62), ha="center", fontsize=7.5, color=INK)
    ax.annotate("ΔCO/ΔCO$_2$ spans 10.5–38.0 ppb ppm$^{-1}$\n"
                "ΔCH$_4$/ΔCO$_2$ spans 10.3–16.4",
                (.03, .04), xycoords="axes fraction", fontsize=7.5, color=MUTED)
    ax.set_xticks(range(0, 24, 4))
    ax.set_xlabel("hour (local time)", color=MUTED)
    ax.set_ylabel("ratio, relative to its own daily mean", color=MUTED)
    ax.set_title("c  Jakarta's two ratios, in antiphase", loc="left", color=INK)
    ax.legend(loc="upper center", fontsize=7.5, ncol=2)
    ax.set_ylim(0.5, 1.75)
    _tidy(ax)

    fig.suptitle("Figure 17  Fire severity, the end of the burning season, and Jakarta hour by hour",
                 x=0.008, ha="left", fontsize=11, color=INK, y=1.03)
    fig.savefig(G.FIG / "f17_severity_onset.png")
    plt.close(fig)


# --------------------------------------------------------------------- f19 --
def fig19():
    coh = pd.read_csv(G.OUT / "u_coherence.csv")
    mar = pd.read_csv(G.OUT / "u_marine.csv")
    h2 = pd.read_csv(G.OUT / "u_h2.csv")
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.3), gridspec_kw=dict(wspace=0.34))

    # (a) coherence does not fall with distance
    ax = axes[0]
    for clean, col, mk, lab in ((True, G.COL["BKT"], "o", "both background sites"),
                                (False, G.COL["JMB"], "s", "at least one polluted")):
        s = coh[coh.both_clean == clean]
        ax.plot(s.separation_km, s.r, ls="none", marker=mk, ms=9, color=col,
                mec="white", mew=1.2, label=lab)
    for _, r in coh.iterrows():
        ax.annotate(r.pair, (r.separation_km, r.r), xytext=(0, 9),
                    textcoords="offset points", ha="center", fontsize=7, color=MUTED)
    ax.axhline(0, color=INK, lw=1.1)
    ax.set_xlabel("station separation (km)", color=MUTED)
    ax.set_ylabel("correlation of the monthly anomaly", color=MUTED)
    ax.set_title("a  Coherence follows site type, not distance", loc="left", color=INK)
    ax.legend(loc="lower right", fontsize=7.5)
    ax.set_ylim(-0.45, 0.95)
    _tidy(ax)

    # (b) low in CO2 and high in CO at the same time
    ax = axes[1]
    lab = {"co2": "CO$_2$ (ppm)", "co": "CO (ppb)"}
    x = np.arange(2)
    for k, st in enumerate(("PLU", "SRG")):
        for j, sp in enumerate(("co2", "co")):
            r = mar[(mar.station == st) & (mar.species == sp)]
            if not len(r):
                continue
            r = r.iloc[0]
            ax.bar(j + (k - 0.5) * 0.34, r["diff"], width=0.32, color=G.COL[st],
                   zorder=2, label=G.STATIONS[st][0] if j == 0 else None)
            ax.errorbar(j + (k - 0.5) * 0.34, r["diff"], yerr=1.96 * r.se, fmt="none",
                        ecolor=INK, elinewidth=1, capsize=2)
            ax.annotate(f"{r['diff']:+.1f}", (j + (k - 0.5) * 0.34, r["diff"]),
                        xytext=(0, 5 if r["diff"] > 0 else -13), textcoords="offset points",
                        ha="center", fontsize=8, color=INK)
    ax.axhline(0, color=INK, lw=1.2)
    ax.set_xticks(x)
    ax.set_xticklabels([lab["co2"], lab["co"]])
    ax.set_ylabel("difference from Samoa", color=MUTED)
    ax.set_title("b  A CO$_2$ sink region and a CO source region", loc="left", color=INK)
    ax.legend(loc="upper left", fontsize=7.5)
    ax.margins(y=0.22)
    _tidy(ax)

    # (c) the H2-CO coupling appears when fires burn
    ax = axes[2]
    s = h2.sort_values("month")
    cols = [G.COL["JMB"] if m in (2, 3, 9, 10, 11) else "#9aa3ad" for m in s.month]
    ax.bar(s.month, s.r, width=0.66, color=cols, zorder=2)
    ax.axhline(0, color=INK, lw=1.1)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(MONTHS)
    ax.set_ylabel("correlation of H$_2$ with CO", color=MUTED)
    ax.set_title("c  Hydrogen tracks CO only in the burning months", loc="left", color=INK)
    ax.margins(y=0.16)
    _tidy(ax)

    fig.suptitle("Figure 21  Regional structure: coherence, the marine comparison, and hydrogen",
                 x=0.008, ha="left", fontsize=11, color=INK, y=1.03)
    fig.savefig(G.FIG / "f21_regional.png")
    plt.close(fig)


def main():
    fig18()
    fig19()


if __name__ == "__main__":
    i18n.install(i18n.from_argv())
    G.style()
    main()
    print("wrote f17_severity_onset.png, f21_regional.png")
