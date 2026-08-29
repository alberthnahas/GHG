"""Figures for the Jambi presentation.  Written to Jambi/figures/.

Jambi is the one station in the network whose surface is losing carbon rather
than cycling it, so these figures are built to show that specifically: what the
site looks like hour by hour, how its respiration runs opposite to an intact
forest's, and where it sits against the other four stations.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G
import i18n

OUTDIR = G.ROOT / "Jambi" / "figures"
INK, MUTED = "#1b1f24", "#6b7280"
JMB, PLU = G.COL["JMB"], G.COL["PLU"]
MONTHS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]


def _tidy(ax):
    ax.tick_params(colors=MUTED, labelsize=8)
    for s in ax.spines.values():
        s.set_color("#d7dbe0")


# --------------------------------------------------------------------- j1 ---
def fig_signature(d):
    """What the site looks like: three species, one day."""
    j = d[d.station == "JMB"]
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.2), gridspec_kw=dict(wspace=0.32))

    # (a) the three diurnal cycles, each on its own scale via normalisation
    ax = axes[0]
    for sp, col, mk, ls, lab in (("co2", JMB, "o", "-", "CO$_2$"),
                                 ("ch4", G.COL["PLU"], "s", "--", "CH$_4$"),
                                 ("co", G.COL["KMY"], "^", "-.", "CO")):
        h = j.groupby("hour_local")[sp].median()
        ax.plot(h.index, (h - h.min()) / (h.max() - h.min()), marker=mk, ls=ls, lw=2,
                ms=5, color=col, mec="white", mew=1, label=lab)
    ax.axvspan(12, 16, color="#9aa3ad", alpha=0.16, zorder=0)
    ax.annotate("well-mixed\nafternoon", xy=(14, 0.90), ha="center", fontsize=7.5, color=INK)
    ax.set_xticks(range(0, 24, 4))
    ax.set_xlabel("hour (local time)", color=MUTED)
    ax.set_ylabel("normalised to each species' own range", color=MUTED)
    ax.set_title("a  CO peaks in the evening, not at dawn", loc="left", color=INK)
    ax.legend(loc="lower left", fontsize=8)
    _tidy(ax)

    # (b) how often each species pair is actually co-emitted
    ax = axes[1]
    r = pd.read_csv(G.OUT / "nightly_emission_ratios.csv")
    r = r[r.station.isin(["JMB", "PLU"])]
    pairs = ["ΔCO/ΔCO₂", "ΔCH₄/ΔCO₂", "ΔCH₄/ΔCO"]
    x = np.arange(len(pairs))
    for k, (st, col) in enumerate((("JMB", JMB), ("PLU", PLU))):
        v = [float(r[(r.station == st) & (r.ratio == p)].pct_nights.iloc[0])
             if len(r[(r.station == st) & (r.ratio == p)]) else np.nan for p in pairs]
        ax.bar(x + (k - 0.5) * 0.36, v, width=0.34, color=col, zorder=2,
               label=G.STATIONS[st][0])
        for xi, vi in zip(x + (k - 0.5) * 0.36, v):
            if np.isfinite(vi):
                ax.annotate(f"{vi:.0f} %", (xi, vi), xytext=(0, 4),
                            textcoords="offset points", ha="center", fontsize=8, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels(pairs, fontsize=9)
    ax.set_ylabel("nights passing the coupling test (%)", color=MUTED)
    ax.set_title("b  Coupled to methane, not combustion", loc="left", color=INK)
    ax.legend(loc="upper left", fontsize=8)
    ax.margins(y=0.22)
    _tidy(ax)

    # (c) the antiphase: the finding, in one panel
    ax = axes[2]
    y = pd.read_csv(G.OUT / "y_resp_season.csv")
    for st, col, mk, ls in (("JMB", JMB, "s", "--"), ("PLU", PLU, "D", "-.")):
        s = y[y.station == st].sort_values("month")
        ax.plot(s.month, s.rate / s.rate.mean(), marker=mk, ls=ls, lw=2.2, ms=7,
                color=col, mec="white", mew=1.2, label=G.STATIONS[st][0])
    ax.axhline(1, color=MUTED, lw=1, zorder=0)
    ax.axvspan(8.5, 10.5, color="#9aa3ad", alpha=0.18, zorder=0)
    ax.annotate("driest months", xy=(9.5, 1.47), ha="center", fontsize=7.5, color=INK)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(MONTHS)
    ax.set_ylabel("nocturnal CO$_2$ build-up / annual mean", color=MUTED)
    ax.set_title("c  A dry-season respiration peak", loc="left", color=INK)
    ax.legend(loc="lower left", fontsize=8)
    ax.set_ylim(0.55, 1.58)
    _tidy(ax)

    fig.suptitle("Figure J1  Jambi's signature: an hour, a night, and a year",
                 x=0.008, ha="left", fontsize=11, color=INK, y=1.03)
    fig.savefig(OUTDIR / "j1_signature.png")
    plt.close(fig)


# --------------------------------------------------------------------- j2 ---
def fig_context():
    """Jambi against the other four stations."""
    lad = pd.read_csv(G.OUT / "x_ladder.csv")
    forc = pd.read_csv(G.OUT / "x_forcing.csv")
    nf = pd.read_csv(G.OUT / "x_noct_flux.csv")
    nf = nf[nf.species == "co2"].set_index("station")
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.2), gridspec_kw=dict(wspace=0.34))

    # (a) the regional ladder, with Jambi picked out
    ax = axes[0]
    order = ["SRG", "BKT", "JMB", "KMY"]
    sp_lab = {"co2": "ΔCO$_2$ (ppm)", "ch4": "ΔCH$_4$ (ppb)", "co": "ΔCO (ppb)"}
    x = np.arange(3)
    for k, st in enumerate(order):
        vals, errs = [], []
        for sp in ("co2", "ch4", "co"):
            r = lad[(lad.station == st) & (lad.species == sp)].iloc[0]
            # each species on its own scale, as a fraction of Kemayoran's value
            ref = lad[(lad.station == "KMY") & (lad.species == sp)].delta.iloc[0]
            vals.append(r.delta / ref)
            errs.append(1.96 * r.se / ref)
        w = 0.2
        ax.bar(x + (k - 1.5) * w, vals, width=w * 0.9,
               color=JMB if st == "JMB" else G.COL[st], alpha=1.0 if st == "JMB" else 0.55,
               zorder=2, label=G.STATIONS[st][0])
        ax.errorbar(x + (k - 1.5) * w, vals, yerr=errs, fmt="none", ecolor=INK,
                    elinewidth=0.9, capsize=2)
    ax.axhline(0, color=INK, lw=1.1)
    ax.set_xticks(x)
    ax.set_xticklabels([sp_lab[s] for s in ("co2", "ch4", "co")], fontsize=9)
    ax.set_ylabel("enhancement over Bariri, relative to Jakarta", color=MUTED)
    ax.set_title("a  Two-thirds of a megacity, in methane", loc="left", color=INK)
    ax.legend(loc="upper left", fontsize=7.5, ncol=2)
    ax.margins(y=0.20)
    _tidy(ax)

    # (b) methane's share of the local greenhouse forcing
    ax = axes[1]
    f = forc[forc.kind == "enhancement over Bariri"].set_index("label")
    order2 = ["SRG", "BKT", "KMY", "JMB"]
    y = np.arange(len(order2))[::-1]
    share = [f.loc[s, "ch4_share_pct"] for s in order2]
    ax.barh(y, share, height=0.55,
            color=[JMB if s == "JMB" else "#9aa3ad" for s in order2], zorder=2)
    ax.axvline(20, color=INK, lw=1.4, ls="--")
    ax.annotate("global budget: 20 %", xy=(20.8, 3.52), fontsize=8, color=INK, va="bottom")
    for yi, v in zip(y, share):
        ax.annotate(f"{v:.0f} %", (v, yi), xytext=(5, 0), textcoords="offset points",
                    va="center", fontsize=8.5, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels([G.STATIONS[s][0] for s in order2], fontsize=8.5)
    ax.set_xlabel("methane's share of the local greenhouse forcing", color=MUTED)
    ax.set_title("b  The most methane-heavy site", loc="left", color=INK)
    ax.margins(x=0.22)
    ax.set_ylim(-0.6, 3.9)
    _tidy(ax)

    # (c) the carbon clock
    ax = axes[2]
    gc = 12.011 * 3.156e7 / 1e6
    jmb, plu = nf.loc["JMB", "flux_h200"] * gc, nf.loc["PLU", "flux_h200"] * gc
    ax.bar([0], [plu], width=0.5, color="#9aa3ad", zorder=2,
           label="what an intact forest respires")
    ax.bar([1], [plu], width=0.5, color="#9aa3ad", zorder=2)
    ax.bar([1], [jmb - plu], bottom=[plu], width=0.5, color=JMB, zorder=3,
           label="the excess, attributable to drainage")
    for xi, v in ((0, plu), (1, jmb)):
        ax.annotate(f"{v:,.0f}", (xi, v), xytext=(0, 5), textcoords="offset points",
                    ha="center", fontsize=9, color=INK)
    ax.annotate(f"{jmb-plu:,.0f} g C m$^{{-2}}$ yr$^{{-1}}$\n"
                f"= {(jmb-plu)/100:.1f} t C ha$^{{-1}}$ yr$^{{-1}}$\n"
                f"a 60–180 year clock",
                (1.30, (plu + jmb) / 2), fontsize=8.5, color=INK, va="center")
    ax.legend(loc="upper left", fontsize=7.5)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Bariri\nintact rainforest", "Jambi\ndrained peat"], fontsize=9)
    ax.set_ylabel("annualised nocturnal respiration (g C m$^{-2}$ yr$^{-1}$)", color=MUTED)
    ax.set_title("c  Twice an intact forest's respiration", loc="left", color=INK)
    ax.set_xlim(-0.6, 2.3)
    ax.margins(y=0.18)
    _tidy(ax)

    fig.suptitle("Figure J2  Jambi against the other four stations",
                 x=0.008, ha="left", fontsize=11, color=INK, y=1.03)
    fig.savefig(OUTDIR / "j2_context.png")
    plt.close(fig)


# --------------------------------------------------------------------- j3 ---
def fig_record(d):
    """The two years of record, species by species."""
    j = d[d.station == "JMB"].set_index("time_local").sort_index()
    fig, axes = plt.subplots(3, 1, figsize=(13.2, 5.6), sharex=True,
                             gridspec_kw=dict(hspace=0.18))
    spec = (("co2", "CO$_2$ (ppm)", JMB), ("ch4", "CH$_4$ (ppb)", G.COL["PLU"]),
            ("co", "CO (ppb)", G.COL["KMY"]))
    for ax, (sp, lab, col) in zip(axes, spec):
        m = j[sp].resample("MS")
        lo, mid, hi = m.quantile(.10), m.median(), m.quantile(.90)
        n = m.size()
        keep = n >= 200
        ax.fill_between(lo.index[keep], lo[keep], hi[keep], color=col, alpha=0.20,
                        lw=0, label="10th–90th percentile of hourly values")
        ax.plot(mid.index[keep], mid[keep], lw=2.2, color=col, label="monthly median")
        b = j[(j.hour_local >= 12) & (j.hour_local <= 16)][sp].resample("MS").quantile(.20)
        ax.plot(b.index[keep], b[keep], lw=1.6, ls="--", color=INK,
                label="afternoon background (20th percentile)")
        ax.set_ylabel(lab, color=MUTED)
        _tidy(ax)
        if sp == "co2":
            ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.02),
                      fontsize=8, ncol=3, borderaxespad=0)
    axes[-1].set_xlabel("", color=MUTED)
    fig.suptitle("Figure J3  Two years at Jambi: the range, the median, and the background",
                 x=0.008, ha="left", fontsize=11, color=INK, y=0.985)
    fig.savefig(OUTDIR / "j3_record.png")
    plt.close(fig)


# --------------------------------------------------------------------- j4 ---
def fig_methane(d):
    """Jambi's methane, against the network."""
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.2), gridspec_kw=dict(wspace=0.32))

    # (a) how fast methane accumulates at night, everywhere
    ax = axes[0]
    nf = pd.read_csv(G.OUT / "x_noct_flux.csv")
    nf = nf[nf.species == "ch4"].set_index("station")
    order = ["PLU", "SRG", "BKT", "JMB", "KMY"]
    x = np.arange(len(order))
    vals = [nf.loc[s, "rate"] for s in order]
    ax.bar(x, vals, width=0.55,
           color=[JMB if s == "JMB" else G.COL[s] for s in order],
           alpha=1.0, zorder=2)
    ax.errorbar(x, vals, yerr=[[nf.loc[s, "rate"] - nf.loc[s, "q25"] for s in order],
                               [nf.loc[s, "q75"] - nf.loc[s, "rate"] for s in order]],
                fmt="none", ecolor=INK, elinewidth=1, capsize=3)
    for xi, v, s_ in zip(x, vals, order):
        ax.annotate(f"{v:.1f}", (xi, nf.loc[s_, "q75"]), xytext=(0, 6),
                    textcoords="offset points", ha="center", fontsize=8.5, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels(order)
    ax.set_ylabel("nocturnal CH$_4$ build-up (ppb h$^{-1}$)", color=MUTED)
    ax.set_title("a  Second only to a megacity", loc="left", color=INK)
    ax.margins(y=0.20)
    _tidy(ax)

    # (b) the distribution of hourly methane
    ax = axes[1]
    for st in ("PLU", "BKT", "JMB", "KMY"):
        s = d[(d.station == st)]["ch4"].dropna()
        s = s[(s > 1700) & (s < 3200)]
        ax.hist(s, bins=70, density=True, histtype="step", lw=2.2,
                color=JMB if st == "JMB" else G.COL[st],
                alpha=1.0 if st == "JMB" else 0.75, label=G.STATIONS[st][0])
    ax.set_xlabel("hourly CH$_4$ (ppb)", color=MUTED)
    ax.set_ylabel("density", color=MUTED)
    ax.set_title("b  A distribution shifted, not just tailed", loc="left", color=INK)
    ax.legend(loc="upper right", fontsize=7.5)
    _tidy(ax)

    # (c) the ratio that separates a peatland from a city
    ax = axes[2]
    r = pd.read_csv(G.OUT / "nightly_emission_ratios.csv")
    r = r[r.ratio == "ΔCH₄/ΔCO₂"].set_index("station")
    order2 = ["PLU", "SRG", "BKT", "JMB", "KMY"]
    x = np.arange(len(order2))
    v = [r.loc[s, "median"] for s in order2]
    ax.bar(x, v, width=0.55, color=[JMB if s == "JMB" else G.COL[s] for s in order2], zorder=2)
    ax.errorbar(x, v, yerr=[[r.loc[s, "median"] - r.loc[s, "q25"] for s in order2],
                            [r.loc[s, "q75"] - r.loc[s, "median"] for s in order2]],
                fmt="none", ecolor=INK, elinewidth=1, capsize=3)
    for xi, vi, s_ in zip(x, v, order2):
        ax.annotate(f"{vi:.1f}", (xi, r.loc[s_, "q75"]), xytext=(0, 6),
                    textcoords="offset points", ha="center", fontsize=8.5, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels(order2)
    ax.set_ylabel("nightly ΔCH$_4$/ΔCO$_2$ (ppb ppm$^{-1}$)", color=MUTED)
    ax.set_title("c  Methane per unit of CO$_2$, at night", loc="left", color=INK)
    ax.margins(y=0.22)
    _tidy(ax)

    fig.suptitle("Figure J4  Jambi's methane against the network",
                 x=0.008, ha="left", fontsize=11, color=INK, y=1.03)
    fig.savefig(OUTDIR / "j4_methane.png")
    plt.close(fig)


# --------------------------------------------------------------------- j5 ---
def fig_fire(d):
    """Jambi's respiration and the haze 500 km downwind."""
    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.2), gridspec_kw=dict(wspace=0.30))
    y = pd.read_csv(G.OUT / "y_resp_season.csv")
    jr = y[y.station == "JMB"].set_index("month")["rate"]
    b = d[d.station == "BKT"]
    bco = b.groupby("month")["co"].median()

    ax = axes[0]
    ax.plot(jr.index, jr / jr.mean(), marker="s", ls="--", lw=2.2, ms=7, color=JMB,
            mec="white", mew=1.2, label="Jambi nocturnal respiration")
    ax.plot(bco.index, bco / bco.mean(), marker="o", ls="-", lw=2.2, ms=7,
            color=G.COL["BKT"], mec="white", mew=1.2,
            label="Bukit Kototabang CO, 500 km downwind")
    ax.axhline(1, color=MUTED, lw=1, zorder=0)
    for m0, m1, lab in ((1.5, 3.5, "Riau\nland clearing"), (8.5, 10.5, "South Sumatra\nand Jambi peat")):
        ax.axvspan(m0, m1, color="#9aa3ad", alpha=0.16, zorder=0)
        ax.annotate(lab, xy=((m0 + m1) / 2, 1.52), ha="center", fontsize=7.5, color=INK)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(MONTHS)
    ax.set_ylabel("relative to each series' own annual mean", color=MUTED)
    ax.set_title("a  Only the second burning window is Jambi's", loc="left", color=INK)
    ax.legend(loc="lower left", fontsize=7.5)
    ax.set_ylim(0.55, 1.68)
    _tidy(ax)

    ax = axes[1]
    ax.scatter(jr.values, bco.values, s=52, c=jr.index, cmap="twilight",
               edgecolor="white", linewidth=1.1, zorder=3)
    for m in jr.index:
        ax.annotate(MONTHS[m - 1], (jr[m], bco[m]), xytext=(7, 3),
                    textcoords="offset points", fontsize=8, color=INK)
    sub = [m for m in jr.index if m in (6, 7, 8, 9, 10, 11)]
    sl, ic = np.polyfit(jr[sub], bco[sub], 1)
    xx = np.linspace(min(jr[sub]), max(jr[sub]), 20)
    ax.plot(xx, sl * xx + ic, color=INK, lw=1.8, zorder=2)
    ax.annotate(f"June–November only\n$r$ = {np.corrcoef(jr[sub], bco[sub])[0,1]:+.2f}",
                (.04, .95), xycoords="axes fraction", va="top", fontsize=8.5, color=INK)
    ax.set_xlabel("Jambi nocturnal respiration (ppm h$^{-1}$)", color=MUTED)
    ax.set_ylabel("Bukit Kototabang median CO (ppb)", color=MUTED)
    ax.set_title("b  In the peat season, the two move together", loc="left", color=INK)
    _tidy(ax)

    fig.suptitle("Figure J5  One water table, seen twice",
                 x=0.009, ha="left", fontsize=11, color=INK, y=1.03)
    fig.savefig(OUTDIR / "j5_fire.png")
    plt.close(fig)


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    d = pd.read_pickle(G.OUT / "all.pkl")
    fig_signature(d)
    fig_context()
    fig_record(d)
    fig_methane(d)
    fig_fire(d)
    print(f"wrote 5 figures to {OUTDIR.relative_to(G.ROOT)}/")


if __name__ == "__main__":
    i18n.install(i18n.from_argv())
    G.style()
    main()
