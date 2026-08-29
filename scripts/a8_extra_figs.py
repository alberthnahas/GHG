"""Figures 10-12 for the addendum.  Reads the CSVs written by a7_extra.py.

Palette, markers and line styles come from ghg_common, which carries the
CVD-validated categorical set used by the first-pass figures - identity is never
carried by colour alone, and no panel uses two y-scales.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G
import i18n

INK, MUTED = "#1b1f24", "#6b7280"
SPNAME = {"co2": "CO$_2$", "ch4": "CH$_4$", "co": "CO"}
UNIT = {"co2": "ppm", "ch4": "ppb", "co": "ppb"}


def _tidy(ax):
    ax.tick_params(colors=MUTED, labelsize=8)
    for s in ax.spines.values():
        s.set_color("#d7dbe0")


# --------------------------------------------------------------------- f10 --
def fig10():
    w = pd.read_csv(G.OUT / "x_weekly.csv")
    lad = pd.read_csv(G.OUT / "x_ladder.csv")
    fig = plt.figure(figsize=(12.4, 4.4))
    gs = fig.add_gridspec(1, 4, width_ratios=[1.6, 1, 1, 1], wspace=0.5)

    # (a) every weekday test in the network, on one normalised axis
    ax = fig.add_subplot(gs[0, 0])
    w = w.sort_values(["species", "station"]).reset_index(drop=True)
    y = np.arange(len(w))[::-1]
    for i, r in w.iterrows():
        c = G.COL[r.station]
        ax.plot([r.lo, r.hi], [y[i], y[i]], color=c, lw=2,
                alpha=1.0 if r.significant else 0.35, solid_capstyle="round")
        ax.plot(r.delta, y[i], marker=G.MRK[r.station], ms=6, color=c,
                mec="white", mew=1.2, alpha=1.0 if r.significant else 0.45)
    ax.axvline(0, color=MUTED, lw=1, zorder=0)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{r.station}  {SPNAME[r.species]}" for _, r in w.iterrows()], fontsize=7.5)
    ax.set_xlabel("Sunday − weekday  (ppm / ppb)", color=MUTED)
    ax.set_title("a  Sunday − weekday, all 15 tests", loc="left", color=INK)
    sig = w[w.significant].index[0]
    ax.annotate("the one significant test\nin the whole network",
                xy=(w.loc[sig, "delta"], y[sig]), xytext=(14, -34), textcoords="offset points",
                fontsize=7.5, color=INK, ha="left",
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.set_xlim(-72, 40)
    _tidy(ax)

    # (b-d) regional enhancement over the Bariri forest reference, one panel per
    # species because the three scales differ by an order of magnitude.
    order = ["SRG", "BKT", "JMB", "KMY"]
    for k, sp in enumerate(("co2", "ch4", "co")):
        ax = fig.add_subplot(gs[0, k + 1])
        s = lad[lad.species == sp].set_index("station").loc[order]
        yy = np.arange(len(order))[::-1]
        ax.barh(yy, s.delta, height=0.55, color=[G.COL[i] for i in order], zorder=2)
        ax.errorbar(s.delta, yy, xerr=1.96 * s.se, fmt="none", ecolor=INK, elinewidth=1, capsize=2)
        ax.axvline(0, color=MUTED, lw=1)
        ax.set_yticks(yy)
        ax.set_yticklabels(order, fontsize=8)
        for v, e, yv in zip(s.delta, 1.96 * s.se, yy):
            ax.annotate(f"{v:+.0f}" if abs(v) >= 10 else f"{v:+.1f}",
                        (v + np.sign(v) * e, yv), xytext=(5 if v > 0 else -5, 0),
                        textcoords="offset points", va="center",
                        ha="left" if v > 0 else "right", fontsize=7.5, color=INK)
        ax.set_xlabel(UNIT[sp], color=MUTED)
        ax.set_title(f"{'bcd'[k]}  Δ{SPNAME[sp]} vs Bariri", loc="left", color=INK)
        ax.margins(x=0.38)
        _tidy(ax)

    fig.suptitle("Figure 10  The weekly-cycle detection limit, and the regional enhancement ladder",
                 x=0.008, ha="left", fontsize=11, color=INK, y=1.04)
    fig.savefig(G.FIG / "f10_weekly_ladder.png")
    plt.close(fig)


# --------------------------------------------------------------------- f11 --
def fig11():
    f = pd.read_csv(G.OUT / "x_noct_flux.csv")
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.2), gridspec_kw=dict(wspace=0.3))

    order = ["PLU", "SRG", "BKT", "KMY", "JMB"]
    s = f[f.species == "co2"].set_index("station").loc[order]
    x = np.arange(len(order))

    ax = axes[0]
    ax.bar(x, s.rate, width=0.55, color=[G.COL[i] for i in order], zorder=2)
    ax.errorbar(x, s.rate, yerr=[s.rate - s.q25, s.q75 - s.rate], fmt="none",
                ecolor=INK, elinewidth=1, capsize=3)
    for xi, v, top, n in zip(x, s.rate, s.q75, s.n_coherent):
        ax.annotate(f"{v:.1f}\nn={n}", (xi, top), xytext=(0, 7), textcoords="offset points",
                    ha="center", fontsize=7.5, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels(order)
    ax.set_ylabel("CO$_2$ accumulation rate (ppm h$^{-1}$)", color=MUTED)
    ax.set_title("a  Nocturnal build-up on well-stratified nights", loc="left", color=INK)
    ax.margins(y=0.3)
    _tidy(ax)

    # Height is the unmeasured quantity, so it is drawn as a range rather than
    # hidden inside a single number.
    ax = axes[1]
    for i, st in enumerate(order):
        r = s.loc[st]
        ax.plot([i, i], [r.flux_h100, r.flux_h400], color=G.COL[st], lw=6,
                solid_capstyle="round", alpha=0.35, zorder=2)
        ax.plot(i, r.flux_h200, marker=G.MRK[st], ms=8, color=G.COL[st],
                mec="white", mew=1.4, zorder=3)
        ax.annotate(f"{r.flux_h200:.1f}", (i, r.flux_h200), xytext=(10, 0),
                    textcoords="offset points", va="center", fontsize=8, color=INK)
    ax.axhspan(4, 8, color="#9aa3ad", alpha=0.16, zorder=0)
    ax.annotate("published range for tropical\nforest ecosystem respiration",
                xy=(-0.42, 8), xytext=(0, 5), textcoords="offset points",
                fontsize=7.5, color=MUTED, ha="left")
    ax.set_xticks(np.arange(len(order)))
    ax.set_xticklabels(order)
    ax.set_ylabel("implied surface flux (µmol m$^{-2}$ s$^{-1}$)", color=MUTED)
    ax.set_title("b  Flux it implies for a 100–400 m stable layer", loc="left", color=INK)
    ax.margins(x=0.14, y=0.2)
    _tidy(ax)

    fig.suptitle("Figure 12  The nocturnal boundary layer as a flux chamber",
                 x=0.008, ha="left", fontsize=11, color=INK, y=1.02)
    fig.savefig(G.FIG / "f12_nocturnal_flux.png")
    plt.close(fig)


# --------------------------------------------------------------------- f12 --
def fig12():
    g = pd.read_csv(G.OUT / "x_growth_anom.csv")
    fr = pd.read_csv(G.OUT / "x_fire_ratio.csv")
    dc = pd.read_csv(G.OUT / "x_co_decay.csv")
    fig, axes = plt.subplots(1, 3, figsize=(12.8, 4.3), gridspec_kw=dict(wspace=0.32))

    # (a) CO2 growth anomaly - two independent stations, same El Nino excursion
    ax = axes[0]
    for st in ("BKT", "PLU"):
        s = g[(g.station == st) & (g.species == "co2")].sort_values("year")
        # NaN-fill the missing years so the line breaks at the record gaps
        # instead of drawing a segment across them.
        s = s.set_index("year").reindex(range(int(s.year.min()), int(s.year.max()) + 1)).reset_index()
        ax.plot(s.year, s.growth, marker=G.MRK[st], ls=G.LS[st], lw=2, ms=8,
                color=G.COL[st], mec="white", mew=1.2, label=G.STATIONS[st][0])
    ax.axvspan(2022.6, 2023.6, color="#9aa3ad", alpha=0.16, zorder=0)
    ax.annotate("2023 El Niño", xy=(2023.0, 4.3), xytext=(0, 10), textcoords="offset points",
                ha="center", fontsize=8, color=INK)
    ax.set_ylabel("CO$_2$ growth (ppm yr$^{-1}$)", color=MUTED)
    ax.set_title("a  Interannual CO$_2$ growth anomaly", loc="left", color=INK)
    ax.legend(loc="upper left", fontsize=8)
    ax.set_ylim(-0.8, 5.6)
    ax.axhline(0, color=MUTED, lw=1, zorder=0)
    _tidy(ax)

    # (b) plume dCH4/dCO, every burning window BKT had both species
    ax = axes[1]
    lab = fr.year.astype(str) + " " + fr.window.str[0]
    x = np.arange(len(fr))
    fire = fr.ratio < 0.15
    ax.errorbar(x[~fire.values], fr.ratio[~fire], yerr=[(fr.ratio - fr.lo)[~fire], (fr.hi - fr.ratio)[~fire]],
                fmt=G.MRK["BKT"], ms=6, color=G.COL["BKT"], mec="white", mew=1,
                elinewidth=1, capsize=2, label="regional biogenic CH$_4$")
    ax.errorbar(x[fire.values], fr.ratio[fire], yerr=[(fr.ratio - fr.lo)[fire], (fr.hi - fr.ratio)[fire]],
                fmt="*", ms=14, color=G.COL["JMB"], mec="white", mew=1,
                elinewidth=1, capsize=2, label="peat-fire plume")
    ax.axhspan(0.06, 0.10, color=G.COL["JMB"], alpha=0.16, zorder=0)
    ax.annotate("published Indonesian peat range 0.06–0.10", xy=(len(fr) - 0.4, 0.10),
                xytext=(0, 5), textcoords="offset points", fontsize=7.5, color=INK, ha="right")
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(lab, fontsize=7, rotation=90)
    ax.set_ylabel("ΔCH$_4$/ΔCO (ppb ppb$^{-1}$)", color=MUTED)
    ax.set_title("b  Fire season vs normal, in one ratio", loc="left", color=INK)
    ax.legend(loc="lower left", fontsize=7.5)
    _tidy(ax)

    # (c) how fast the CO enhancement relaxes after each event
    ax = axes[2]
    dc = dc.sort_values("peak_enh")
    ax.plot(dc.peak_enh, dc.tau_days, ls="none", marker=G.MRK["BKT"], ms=9,
            color=G.COL["BKT"], mec="white", mew=1.3)
    for _, r in dc.iterrows():
        ax.annotate(str(int(r.year)), (r.peak_enh, r.tau_days), xytext=(7, 4),
                    textcoords="offset points", fontsize=8, color=INK)
    ax.axhspan(30, 90, color="#9aa3ad", alpha=0.16, zorder=0)
    ax.annotate("chemical lifetime of CO against OH", xy=(135, 87), fontsize=7.5,
                color=MUTED, va="top")
    ax.set_xscale("log")
    ax.set_xticks([200, 400, 800, 1600])
    ax.set_xticklabels(["200", "400", "800", "1600"])
    ax.set_xlabel("peak CO enhancement (ppb)", color=MUTED)
    ax.set_ylabel("e-folding relaxation time (days)", color=MUTED)
    ax.set_title("c  Plumes clear before OH can act", loc="left", color=INK)
    ax.set_ylim(0, 95)
    _tidy(ax)

    fig.suptitle("Figure 16  Growth anomalies, fire fingerprints and plume clearance at Bukit Kototabang",
                 x=0.008, ha="left", fontsize=11, color=INK, y=1.03)
    fig.savefig(G.FIG / "f16_growth_fire.png")
    plt.close(fig)


def main():
    fig10()
    fig11()
    fig12()


if __name__ == "__main__":
    i18n.install(i18n.from_argv())
    G.style()
    main()
    print("wrote f10_weekly_ladder.png, f12_nocturnal_flux.png, f16_growth_fire.png")
