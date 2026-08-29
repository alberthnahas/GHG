"""Figure 17 - carbon source and sink.  Reads a15_carbon.py output."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G
import i18n

INK, MUTED = "#1b1f24", "#6b7280"


def _tidy(ax):
    ax.tick_params(colors=MUTED, labelsize=8)
    for s in ax.spines.values():
        s.set_color("#d7dbe0")


def fig17():
    sink = pd.read_csv(G.OUT / "v_sink.csv")
    ratio = pd.read_csv(G.OUT / "v_ratio.csv")
    bud = pd.read_csv(G.OUT / "v_budget.csv").set_index("quantity")
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.3), gridspec_kw=dict(wspace=0.34))

    # (a) the extra CO2 loss, one estimate per tracer, paired by morning
    ax = axes[0]
    order = ["PLU", "BKT", "JMB", "KMY"]
    x = np.arange(len(order))
    for k, (tr, off, mk) in enumerate((("ch4", -0.13, "o"), ("co", +0.13, "s"))):
        s = sink[sink.tracer == tr].set_index("station")
        xs, ys, los, his = [], [], [], []
        for i, st in enumerate(order):
            if st not in s.index:
                continue
            xs.append(i + off)
            ys.append(s.loc[st, "diff"])
            los.append(s.loc[st, "diff"] - s.loc[st, "lo"])
            his.append(s.loc[st, "hi"] - s.loc[st, "diff"])
        ax.errorbar(xs, ys, yerr=[los, his], fmt=mk, ms=7, lw=0, elinewidth=1.4,
                    capsize=3, color=G.COL["BKT"] if tr == "ch4" else G.COL["JMB"],
                    mec="white", mew=1.1,
                    label=("vs CH$_4$" if tr == "ch4" else "vs CO"))
    ax.axhline(0, color=INK, lw=1.2)
    ax.axhspan(-0.15, 0, color=G.COL["SRG"], alpha=0.10, zorder=0)
    ax.annotate("net daytime source", xy=(3.42, -0.10), fontsize=7.5, color=MUTED, ha="right")
    ax.annotate("net daytime sink", xy=(-0.42, 0.165), fontsize=7.5, color=MUTED)
    ax.set_xticks(x)
    ax.set_xticklabels(order)
    ax.set_ylabel("extra CO$_2$ loss rate (h$^{-1}$)", color=MUTED)
    ax.set_title("a  CO$_2$ removed beyond dilution", loc="left", color=INK)
    ax.legend(loc="upper right", fontsize=8)
    ax.set_ylim(-0.16, 0.20)
    _tidy(ax)

    # (b) the excess ratio falling through the morning at a forested site, flat
    # at the drained-peat site
    ax = axes[1]
    r = ratio[(ratio.tracer == "ch4") & (ratio.phase == "day")]
    for st in ("PLU", "BKT", "JMB", "KMY"):
        s = r[r.station == st].sort_values("step")
        if not len(s):
            continue
        ax.plot(s.step, s.ratio / s.ratio.iloc[0], marker=G.MRK[st], ls=G.LS[st],
                lw=2, ms=6, color=G.COL[st], mec="white", mew=1.1,
                label=G.STATIONS[st][0])
    ax.axhline(1, color=MUTED, lw=1, zorder=0)
    ax.set_xlabel("hour (local time)", color=MUTED)
    ax.set_ylabel("ΔCO$_2$/ΔCH$_4$, relative to dawn", color=MUTED)
    ax.set_title("b  The nocturnal store, drawn down", loc="left", color=INK)
    ax.legend(loc="lower left", fontsize=7.5)
    _tidy(ax)

    # (c) the station's own growth rate, in carbon-budget units
    ax = axes[2]
    acc = bud.loc["implied atmospheric accumulation", "value"]
    anom = bud.loc["  as a carbon flux", "value"]
    items = [("total emissions", 11.1, "#9aa3ad"),
             ("ocean sink", 2.9, "#9aa3ad"),
             ("land sink", 3.2, "#9aa3ad"),
             ("accumulation, this record", acc, G.COL["BKT"]),
             ("2023 El Niño", anom, G.COL["JMB"])]
    xs = np.arange(len(items))
    ax.bar(xs, [v for _, v, _ in items], width=0.6,
           color=[c for _, _, c in items], zorder=2)
    for xi, (_, v, _) in zip(xs, items):
        ax.annotate(f"{v:.1f}", (xi, v), xytext=(0, 4), textcoords="offset points",
                    ha="center", fontsize=8, color=INK)
    ax.set_xticks(xs)
    ax.set_xticklabels([n for n, _, _ in items], fontsize=7.5, rotation=32,
                       ha="right", rotation_mode="anchor")
    ax.set_ylabel("Pg C yr$^{-1}$", color=MUTED)
    ax.set_title("c  The same numbers as a carbon budget", loc="left", color=INK)
    ax.margins(y=0.18)
    _tidy(ax)

    fig.suptitle("Figure 7  Carbon source and sink: what the tracers separate, and what it is worth",
                 x=0.008, ha="left", fontsize=11, color=INK, y=1.03)
    fig.savefig(G.FIG / "f7_carbon.png")
    plt.close(fig)


def main():
    fig17()


if __name__ == "__main__":
    i18n.install(i18n.from_argv())
    G.style()
    main()
    print("wrote f7_carbon.png")
