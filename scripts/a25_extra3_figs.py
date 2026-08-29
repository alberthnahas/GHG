"""Figures 21-22 for the third pass.  Reads a24_extra3.py output."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G
import i18n

INK, MUTED = "#1b1f24", "#6b7280"
WARM, COOL, GREY = "#c0392b", "#1f6f8b", "#b8c0c8"
SPECIES = {"co": "CO", "co2": "CO$_2$", "ch4": "CH$_4$"}


def _tidy(ax):
    ax.tick_params(colors=MUTED, labelsize=8)
    for s in ax.spines.values():
        s.set_color("#d7dbe0")


# --------------------------------------------------------------------- f21 --
def fig21():
    rec = pd.read_csv(G.OUT / "s_rectifier.csv")
    qc = pd.read_csv(G.OUT / "s_qc.csv")
    eid = pd.read_csv(G.OUT / "s_eid.csv")
    fig, axes = plt.subplots(1, 3, figsize=(13.6, 4.5),
                             gridspec_kw=dict(wspace=0.30))

    # (a) the rectifier at each station, with its seasonal range
    ax = axes[0]
    r = rec.sort_values("mean")
    y = np.arange(len(r))
    ax.barh(y, r["mean"], height=0.5, color=COOL, zorder=3)
    ax.hlines(y, r.min_month_mean, r.max_month_mean, color=INK, lw=1.4, zorder=4)
    for i, row in enumerate(r.itertuples()):
        ax.annotate(f"{row.mean:+.1f}", (row.max_month_mean, i), xytext=(6, 0),
                    textcoords="offset points", fontsize=8.5, color=INK, va="center")
    ax.axvline(0, color=INK, lw=1.0)
    ax.set_yticks(y)
    ax.set_yticklabels(r.station, fontsize=9.5, color=INK)
    ax.set_xlim(min(r.min_month_mean.min() * 1.1, -2), r.max_month_mean.max() * 1.30)
    ax.set_xlabel(i18n.t("24-hour mean − afternoon mean (ppm)"), color=MUTED)
    ax.set_title(i18n.t("a  Afternoon sampling understates CO$_2$"),
                 loc="left", color=INK, fontsize=10)
    _tidy(ax)

    # (b) the same statistic as a QC test, grouped by station so the two
    # periods sit side by side and the axis needs one label per station
    ax = axes[1]
    stations = sorted(qc.station.unique())
    periods = ["before 2023-06", "from 2023-06"]
    wid = 0.36
    for k, per in enumerate(periods):
        sub = qc[qc.period == per].set_index("station").reindex(stations)
        pos = np.arange(len(stations)) + (k - 0.5) * wid
        cols = [WARM if ph is False else (COOL if k else GREY)
                for ph in sub.physical]
        ax.bar(pos, sub["mean"].fillna(0), width=wid, color=cols, zorder=3,
               label=i18n.t(per))
        for xp, row in zip(pos, sub.itertuples()):
            if row.physical is False:
                ax.annotate(i18n.t("physically\nimpossible"), (xp, row.mean),
                            xytext=(0, -8), textcoords="offset points",
                            ha="center", va="top", fontsize=8.5, color=WARM)
    ax.axhline(0, color=INK, lw=1.1, zorder=4)
    ax.set_xticks(np.arange(len(stations)))
    ax.set_xticklabels(stations, fontsize=9.5, color=INK)
    ax.set_ylim(-38, 24)
    ax.set_ylabel(i18n.t("rectifier (ppm)"), color=MUTED)
    ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    ax.set_title(i18n.t("b  A negative rectifier flags bad data"),
                 loc="left", color=INK, fontsize=10)
    _tidy(ax)

    # (c) Idul Fitri: what stops and what does not
    ax = axes[2]
    order = ["rush 06-09", "all hours", "night 20-04"]
    sp_order = ["co", "co2", "ch4"]
    wid = 0.26
    for k, sp in enumerate(sp_order):
        sub = eid[eid.species == sp].set_index("window").reindex(order)
        pos = np.arange(len(order)) + (k - 1) * wid
        cols = [WARM if p < 0.05 else GREY for p in sub.p]
        ax.bar(pos, sub.change_pct, width=wid, color=cols, zorder=3)
        for xp, v, p in zip(pos, sub.change_pct, sub.p):
            if p < 0.05:
                ax.annotate(f"{v:.0f} %", (xp, v), xytext=(0, -13),
                            textcoords="offset points", ha="center",
                            fontsize=8.5, color=WARM)
        ax.bar([], [], color=GREY, label=i18n.t(SPECIES[sp]))
    ax.axhline(0, color=INK, lw=1.1, zorder=4)
    ax.set_xticks(np.arange(len(order)))
    ax.set_xticklabels([i18n.t(o) for o in order], fontsize=8.5, color=INK)
    ax.set_ylabel(i18n.t("change during Idul Fitri (%)"), color=MUTED)
    ax.set_ylim(-38, 9)
    for k, sp in enumerate(sp_order):
        ax.annotate(i18n.t(SPECIES[sp]), ((k - 1) * wid, 3.0), ha="center",
                    fontsize=8.5, color=MUTED)
    ax.set_title(i18n.t("c  The city empties; only CO notices"),
                 loc="left", color=INK, fontsize=10)
    _tidy(ax)

    fig.suptitle(i18n.t("Figure 4  The diurnal rectifier, and a week when Jakarta "
                        "stopped driving"),
                 x=0.008, ha="left", fontsize=11, color=INK, y=1.03)
    fig.savefig(G.FIG / "f4_rectifier_eid.png")
    plt.close(fig)


# --------------------------------------------------------------------- f22 --
def fig22():
    det = pd.read_csv(G.OUT / "s_detect.csv")
    smp = pd.read_csv(G.OUT / "s_sampling.csv")
    dof = pd.read_csv(G.OUT / "s_dof.csv")
    fig, axes = plt.subplots(1, 3, figsize=(13.6, 4.5),
                             gridspec_kw=dict(wspace=0.32))

    # (a) years of record before a trend is detectable
    ax = axes[0]
    d = det.sort_values("years_to_detect")
    y = np.arange(len(d))
    ax.barh(y, d.years_to_detect, height=0.55, color=COOL, zorder=3)
    for i, row in enumerate(d.itertuples()):
        ax.annotate(f"{row.years_to_detect:.1f} " + i18n.t("yr"),
                    (row.years_to_detect, i), xytext=(6, 0),
                    textcoords="offset points", fontsize=8.5, color=INK, va="center")
    ax.axvline(21, color=WARM, lw=1.4, ls="--", zorder=4)
    ax.annotate(i18n.t("length of the\nflask record"), (21, 1.1),
                xytext=(-7, 0), textcoords="offset points", ha="right",
                fontsize=8.5, color=WARM, va="center")
    ax.set_yticks(y)
    ax.set_yticklabels([i18n.t(s.upper()) for s in d.species], fontsize=9.5, color=INK)
    ax.set_xlim(0, max(d.years_to_detect.max(), 21) * 1.22)
    ax.set_xlabel(i18n.t("years of record needed"), color=MUTED)
    ax.set_title(i18n.t("a  How long before a trend is real"),
                 loc="left", color=INK, fontsize=10)
    _tidy(ax)

    # (b) what a discrete sampling programme loses
    ax = axes[1]
    x = np.arange(len(smp))
    ax.bar(x, smp.mean_abs_error, width=0.5, color=COOL, zorder=3)
    ax.errorbar(x, smp.mean_abs_error, yerr=smp.sd_across_phases, fmt="none",
                ecolor=INK, elinewidth=1.2, capsize=4, zorder=4)
    for xi, v, e in zip(x, smp.mean_abs_error, smp.sd_across_phases):
        ax.annotate(f"{v:.2f}", (xi, v + e), xytext=(0, 7),
                    textcoords="offset points", ha="center", fontsize=9, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels([i18n.t(f) for f in smp.frequency], fontsize=9, color=INK)
    ax.set_ylabel(i18n.t("error in the monthly mean (ppm)"), color=MUTED)
    ax.set_ylim(0, smp.mean_abs_error.max() * 1.32)
    ax.set_title(i18n.t("b  What discrete sampling costs"),
                 loc="left", color=INK, fontsize=10)
    _tidy(ax)

    # (c) the effective sample size, by family
    ax = axes[2]
    d = dof.copy()
    y = np.arange(len(d))
    ax.barh(y, d.n, height=0.55, color=GREY, zorder=2, label=i18n.t("months or years used"))
    ax.barh(y, d.n_eff, height=0.30, color=WARM, zorder=3,
            label=i18n.t("independent observations"))
    for i, row in enumerate(d.itertuples()):
        ax.annotate(f"{row.n_eff:.0f}", (row.n_eff, i), xytext=(5, 0),
                    textcoords="offset points", fontsize=8.5,
                    color=WARM, va="center")
    ax.set_yticks(y)
    ax.set_yticklabels([i18n.t(t) for t in d.test], fontsize=8.5, color=INK)
    ax.invert_yaxis()
    ax.set_xscale("log")
    ax.set_xlim(2, 1500)
    ax.set_xlabel(i18n.t("sample size (log scale)"), color=MUTED)
    ax.legend(frameon=False, fontsize=8.5, loc="upper right",
              bbox_to_anchor=(1.02, -0.13), ncol=2, handlelength=1.2)
    ax.set_title(i18n.t("c  How much of n is really there"),
                 loc="left", color=INK, fontsize=10)
    _tidy(ax)

    fig.suptitle(i18n.t("Figure 26  What this network can and cannot detect"),
                 x=0.008, ha="left", fontsize=11, color=INK, y=1.03)
    fig.savefig(G.FIG / "f26_detection.png")
    plt.close(fig)


def main():
    fig21()
    fig22()


if __name__ == "__main__":
    i18n.install(i18n.from_argv())
    G.style()
    main()
    print("wrote f4_rectifier_eid.png, f26_detection.png")
