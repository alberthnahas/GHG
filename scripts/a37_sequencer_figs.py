"""Figures for the 100-m tower sequencer specification.  Reads a36_sequencer.py.

Writes figures/sq1-sq3.  Deliberately outside the report's fNN numbering: this
is a standalone engineering specification, not a report finding, and mixing the
two namespaces is how orphan figures happen (landmine 16).

Bilingual: registered in i18n's audit list, so `--lang id` writes `<name>_id.png`
for the Indonesian slide deck.  Follow the house pattern in `__main__` -
`i18n.install`, not `set_lang`, or the Indonesian labels overwrite the English
figures.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G
import i18n

INK, MUTED = "#1b1f24", "#6b7280"
WARM, COOL, GREY = "#c0392b", "#1f6f8b", "#b8c0c8"
LEVCOL = {"30 m": "#eb6834", "70 m": "#1baf7a", "100 m": "#2a78d6"}
PRETTY = {"co2": "CO$_2$", "ch4": "CH$_4$", "co": "CO"}


def _tidy(ax):
    ax.tick_params(colors=MUTED, labelsize=8)
    for s in ax.spines.values():
        s.set_color("#d7dbe0")


# --------------------------------------------------------------------- sq1 --
def sq1():
    """Where in the day the vertical information sits."""
    d = pd.read_csv(G.OUT / "sq_diurnal.csv")
    fig, axes = plt.subplots(1, 3, figsize=(13.6, 4.5),
                             gridspec_kw=dict(wspace=0.42))

    # (a) CO2 diurnal composite, all months, with the interquartile envelope
    ax = axes[0]
    a = d[(d.species == "co2") & (d.season == "all")].sort_values("hour")
    ax.fill_between(a.hour, a.p25, a.p75, color=COOL, alpha=0.18, lw=0)
    ax.plot(a.hour, a.mean_anom, color=COOL, lw=2.0, zorder=3)
    for s, ls in (("DJF", "--"), ("JJA", ":")):
        b = d[(d.species == "co2") & (d.season == s)].sort_values("hour")
        ax.plot(b.hour, b.mean_anom, color=INK, lw=1.1, ls=ls, label=s)
    ax.axhline(0, color=INK, lw=0.8)
    ax.axvspan(0, 8, color=GREY, alpha=0.25, lw=0)
    ax.axvspan(20, 23, color=GREY, alpha=0.25, lw=0)
    ax.annotate("stable / drainage", (4, a.p75.max() * 0.92), ha="center",
                fontsize=8.5, color=MUTED)
    ax.annotate("convective", (14, a.p75.max() * 0.92), ha="center",
                fontsize=8.5, color=MUTED)
    ax.legend(frameon=False, fontsize=8.5, loc="lower right")
    ax.set_xlim(0, 23)
    ax.set_xticks(range(0, 24, 4))
    ax.set_xlabel("Hour of day (local time)", color=MUTED)
    ax.set_ylabel("CO$_2$ anomaly from daily mean (ppm)", color=MUTED)
    ax.set_title("a  The signal is nocturnal, in every season", loc="left",
                 color=INK, fontsize=10)
    _tidy(ax)

    # (b) CH4 and CO, on their own axes
    ax = axes[1]
    a = d[(d.species == "ch4") & (d.season == "all")].sort_values("hour")
    ax.plot(a.hour, a.mean_anom, color="#4a3aa7", lw=2.0, label="CH$_4$ (ppb)")
    ax2 = ax.twinx()
    b = d[(d.species == "co") & (d.season == "all")].sort_values("hour")
    ax2.plot(b.hour, b.mean_anom, color=WARM, lw=2.0, ls="--", label="CO (ppb)")
    ax.axhline(0, color=INK, lw=0.8)
    ax.set_xlim(0, 23)
    ax.set_xticks(range(0, 24, 4))
    ax.set_xlabel("Hour of day (local time)", color=MUTED)
    ax.set_ylabel("CH$_4$ anomaly (ppb)", color="#4a3aa7")
    ax2.set_ylabel("CO anomaly (ppb)", color=WARM, labelpad=1)
    ax2.tick_params(colors=MUTED, labelsize=8)
    for s in ax2.spines.values():
        s.set_color("#d7dbe0")
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, frameon=False, fontsize=8.5, loc="lower right")
    ax.set_title("b  CH$_4$ and CO peak in the same window", loc="left",
                 color=INK, fontsize=10)
    _tidy(ax)

    # (c) hour-to-hour spread: how much a level moves within an hour
    ax = axes[2]
    for sp, col in (("co2", COOL), ("ch4", "#4a3aa7"), ("co", WARM)):
        a = d[(d.species == sp) & (d.season == "all")].sort_values("hour")
        ax.plot(a.hour, a.sd / a.sd.mean(), color=col, lw=1.8,
                label=PRETTY[sp])
    ax.axhline(1, color=INK, lw=0.8, ls=":")
    ax.set_xlim(0, 23)
    ax.set_xticks(range(0, 24, 4))
    ax.set_xlabel("Hour of day (local time)", color=MUTED)
    ax.set_ylabel("Spread / its 24-h mean", color=MUTED)
    ax.legend(frameon=False, fontsize=8.5)
    ax.set_title("c  Variability peaks at the morning transition", loc="left",
                 color=INK, fontsize=10)
    _tidy(ax)

    fig.suptitle("Figure SQ1  The diurnal cycle at Bukit Kototabang, 30-m inlet, "
                 "and what it demands of a sampling schedule",
                 x=0.008, ha="left", y=1.03, fontsize=11.5, color=INK)
    fig.savefig(G.FIG / "sq1_diurnal_demand.png")
    plt.close(fig)


# --------------------------------------------------------------------- sq2 --
def sq2():
    """The three quantitative arguments for the hourly frame."""
    st = pd.read_csv(G.OUT / "sq_structure.csv")
    sub = pd.read_csv(G.OUT / "sq_subsample.csv")
    db = pd.read_csv(G.OUT / "sq_diurnal_bias.csv")
    off = pd.read_csv(G.OUT / "sq_offset.csv")
    fig, axes = plt.subplots(1, 3, figsize=(13.6, 4.5),
                             gridspec_kw=dict(wspace=0.46))

    # (a) structure function, measured and extrapolated
    ax = axes[0]
    for sp, col in (("co2", COOL), ("ch4", "#4a3aa7"), ("co", WARM)):
        m = st[(st.species == sp) & (st.source == "measured")].sort_values("lag_h")
        e = st[(st.species == sp) & (st.source == "extrapolated")].sort_values("lag_h")
        ax.plot(m.lag_h, m.rms_diff, "o-", color=col, lw=1.8, ms=4,
                label=PRETTY[sp])
        ax.plot(e.lag_h, e.rms_diff, ":", color=col, lw=1.4)
        ax.plot(e.lag_h, e.rms_diff, "o", color=col, ms=3, mfc="white")
    ax.axvspan(0.05, 1.0, color=GREY, alpha=0.22, lw=0)
    ax.annotate("extrapolated\n(no sub-hourly data)", (0.12, 1.1), fontsize=8,
                color=MUTED, va="bottom")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Lag (hours)", color=MUTED)
    ax.set_ylabel("RMS change over the lag (ppm / ppb)", color=MUTED)
    ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    ax.set_title("a  How fast the air changes", loc="left", color=INK, fontsize=10)
    _tidy(ax)

    # (b) 3-hourly sampling: monthly-mean error and diurnal-amplitude loss
    ax = axes[1]
    sp_order = ["co2", "ch4", "co"]
    x = np.arange(len(sp_order))
    rms = [sub[(sub.species == s) & (sub.scheme == "3-hourly")].rms_error.mean()
           for s in sp_order]
    amp = [-db[db.species == s].amp_error_pct.mean() for s in sp_order]
    ax.bar(x - 0.19, rms, width=0.36, color=GREY, zorder=3,
           label="Monthly-mean RMS error (ppm / ppb)")
    ax2 = ax.twinx()
    ax2.bar(x + 0.19, amp, width=0.36, color=WARM, zorder=3,
            label="Diurnal amplitude lost (%)")
    for i, v in enumerate(rms):
        ax.annotate(f"{v:.2f}", (i - 0.19, v), xytext=(0, 3),
                    textcoords="offset points", ha="center", fontsize=8, color=INK)
    for i, v in enumerate(amp):
        ax2.annotate(f"{v:.0f}%", (i + 0.19, v), xytext=(0, 3),
                     textcoords="offset points", ha="center", fontsize=8, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels([PRETTY[s] for s in sp_order], fontsize=9.5, color=INK)
    ax.set_ylabel("Monthly-mean RMS error", color=MUTED)
    ax2.set_ylabel("Diurnal amplitude lost (%)", color=WARM)
    ax2.set_ylim(0, max(amp) * 1.45)
    ax.set_ylim(0, max(rms) * 1.45)
    ax2.tick_params(colors=MUTED, labelsize=8)
    for s in ax2.spines.values():
        s.set_color("#d7dbe0")
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, frameon=False, fontsize=8, loc="upper left")
    ax.set_title("b  What 3-hourly sampling costs", loc="left", color=INK,
                 fontsize=10)
    _tidy(ax)

    # (c) the timing artefact, sequential vs bracketed
    ax = axes[2]
    pairs = ["30 m vs 100 m", "70 m vs 100 m"]
    y = np.arange(len(pairs))
    for k, (frame, col) in enumerate((("sequential", GREY), ("bracketed", COOL))):
        v = [off[(off.frame == frame) & (off.pair == p) &
                 (off.species == "co2")].rms_artefact.iloc[0] for p in pairs]
        ax.barh(y + (k - 0.5) * 0.36, v, height=0.34, color=col, zorder=3,
                label=frame)
        for i, vv in enumerate(v):
            ax.annotate(f"{vv:.2f}", (vv, y[i] + (k - 0.5) * 0.36), xytext=(4, 0),
                        textcoords="offset points", va="center", fontsize=8,
                        color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels(["", ""])
    ax.set_ylim(-0.55, len(pairs) - 0.15)
    for i, p_ in enumerate(pairs):
        ax.annotate(p_, (0.06, y[i] + 0.40), fontsize=9, color=INK)
    ax.set_xlabel("Spurious CO$_2$ gradient from timing alone (ppm)", color=MUTED)
    ax.set_xlim(0, 5.0)
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    ax.set_title("c  Bracketing removes most of it", loc="left", color=INK,
                 fontsize=10)
    _tidy(ax)

    fig.suptitle("Figure SQ2  The three measurements that fix the schedule",
                 x=0.008, ha="left", y=1.03, fontsize=11.5, color=INK)
    fig.savefig(G.FIG / "sq2_design_evidence.png")
    plt.close(fig)


# --------------------------------------------------------------------- sq3 --
def sq3():
    """The frame itself, and the flush constraint behind its discard windows."""
    fr = pd.read_csv(G.OUT / "sq_frame.csv")
    fl = pd.read_csv(G.OUT / "sq_flush.csv")
    fig, axes = plt.subplots(1, 3, figsize=(13.6, 4.5),
                             gridspec_kw=dict(wspace=0.40,
                                              width_ratios=[1.7, 1, 1]))

    # (a) the valve timing frame as a gantt strip
    ax = axes[0]
    ypos = {"100 m": 2, "70 m": 1, "30 m": 0}
    for r in fr.itertuples():
        y = ypos[r.level]
        solid = r.status == "valid"
        ax.barh(y, r.minutes, left=r.minute_start, height=0.52,
                color=LEVCOL[r.level] if solid else "white",
                edgecolor=LEVCOL[r.level],
                hatch=None if solid else "////", lw=1.2, zorder=3)
        if r.minutes >= 5:
            ax.annotate(f"{r.minutes}", (r.minute_start + r.minutes / 2, y),
                        ha="center", va="center", fontsize=8,
                        color="white" if solid else LEVCOL[r.level],
                        fontweight="bold" if solid else "normal")
    ax.set_yticks(list(ypos.values()))
    ax.set_yticklabels(list(ypos.keys()), fontsize=10, color=INK)
    ax.set_xlim(0, 60)
    ax.set_xticks(range(0, 61, 10))
    ax.set_xlabel("Minutes past the hour (UTC)", color=MUTED)
    ax.legend(handles=[Patch(facecolor=GREY, label="valid, archived"),
                       Patch(facecolor="white", edgecolor=INK, hatch="////",
                             label="purge, discarded")],
              frameon=False, fontsize=8.5, loc="upper center", ncol=2,
              bbox_to_anchor=(0.5, -0.20))
    ax.set_title("a  The hourly frame, repeated every hour of every day",
                 loc="left", color=INK, fontsize=10)
    _tidy(ax)

    # (b) flush decay for the 100-m line at each candidate flow
    ax = axes[1]
    t = np.linspace(0, 8, 400)
    for q, col in zip((0.4, 2.0, 5.0, 10.0),
                      (WARM, "#d98a2b", COOL, "#1baf7a")):
        tau = fl[(fl.level_m == 100) & (fl.flow_slpm == q)].tau_min.iloc[0]
        ax.plot(t, 100 * np.exp(-t / tau), color=col, lw=1.8,
                label=f"{q:g} slpm")
    ax.axhline(1, color=INK, lw=0.9, ls=":")
    ax.axvline(3, color=INK, lw=0.9, ls="--")
    ax.annotate("1 % residual", (0.15, 1.35), ha="left", fontsize=8, color=MUTED)
    ax.annotate("3-min purge", (3.2, 0.05), fontsize=8, color=MUTED)
    ax.set_yscale("log")
    ax.set_ylim(0.02, 130)
    ax.set_xlim(0, 8)
    ax.set_xlabel("Time after valve switch (min)", color=MUTED)
    ax.set_ylabel("Residual of the previous level (%)", color=MUTED)
    ax.legend(frameon=False, fontsize=8.5, title="bypass flow",
              title_fontsize=8.5, loc="upper right")
    ax.set_title("b  A bypass pump makes 3 min work", loc="left",
                 color=INK, fontsize=10)
    _tidy(ax)

    # (c) purge time to 1 % against level, per flow
    ax = axes[2]
    for q, col in zip((0.4, 2.0, 5.0, 10.0),
                      (WARM, "#d98a2b", COOL, "#1baf7a")):
        s = fl[fl.flow_slpm == q].sort_values("level_m")
        ax.plot(s.level_m, s.t_99pct_min, "o-", color=col, lw=1.8, ms=4,
                label=f"{q:g} slpm")
    ax.axhline(3, color=INK, lw=1.0, ls="--")
    ax.annotate("adopted purge window", (31, 3.3), fontsize=8, color=MUTED)
    ax.set_xticks([30, 70, 100])
    ax.set_xlabel("Inlet height (m)", color=MUTED)
    ax.set_ylabel("Time to 1 % residual (min)", color=MUTED)
    ax.legend(frameon=False, fontsize=8.5)
    ax.set_title("c  Purge scales with length", loc="left", color=INK,
                 fontsize=10)
    _tidy(ax)

    fig.suptitle("Figure SQ3  The adopted frame and the flush constraint that "
                 "sets its purge windows", x=0.008, ha="left", y=1.03,
                 fontsize=11.5, color=INK)
    fig.savefig(G.FIG / "sq3_frame_and_flush.png")
    plt.close(fig)


def main():
    sq1()
    sq2()
    sq3()
    print("wrote sq1-sq3 to", G.FIG)


if __name__ == "__main__":
    i18n.install(i18n.from_argv())
    G.style()
    main()
