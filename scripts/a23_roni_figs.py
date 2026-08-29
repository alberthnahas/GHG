"""Figure 20 - ENSO in a warming ocean.  Reads a22_roni.py output."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G
import i18n

INK, MUTED = "#1b1f24", "#6b7280"
WARM, COOL = "#c0392b", "#1f6f8b"


def _tidy(ax):
    ax.tick_params(colors=MUTED, labelsize=8)
    for s in ax.spines.values():
        s.set_color("#d7dbe0")


def fig20():
    df = pd.read_pickle(G.OUT / "roni.pkl")
    warm = pd.read_csv(G.OUT / "r_warming.csv")
    flip = pd.read_csv(G.OUT / "r_flip.csv")
    tcr = pd.read_csv(G.OUT / "r_tcr.csv")

    fig, axes = plt.subplots(1, 3, figsize=(13.6, 4.5),
                             gridspec_kw=dict(wspace=0.26))

    # (a) the warming RONI removes, with the three trend windows drawn on it
    ax = axes[0]
    t = df.index.year + df.index.month / 12
    ax.plot(t, df.warm, color="#b8c0c8", lw=0.9, zorder=2)
    ax.plot(t, pd.Series(df.warm.values).rolling(61, center=True,
            min_periods=20).mean().values, color=INK, lw=1.8, zorder=3)
    for (lo, hi), row in zip(((1950, 2025), (1980, 2025), (2000, 2025)),
                             warm.itertuples()):
        seg = np.array([lo, hi])
        mid = df.warm[(df.index.year >= lo) & (df.index.year <= hi)].median()
        y = row.trend_per_decade / 10 * (seg - np.mean(seg)) + mid
        ax.plot(seg, y, color=WARM, lw=2.2, zorder=4)
        ax.annotate(f"{row.trend_per_decade:+.2f} °C/" + i18n.t("decade"),
                    (hi, y[1]), xytext=(4, 0), textcoords="offset points",
                    fontsize=8, color=WARM, va="center")
    ax.axhline(0, color=MUTED, lw=0.8, ls=":")
    ax.set_xlim(1948, 2038)
    ax.set_ylabel(i18n.t("tropical-mean SST anomaly (°C)"), color=MUTED)
    ax.set_title(i18n.t("a  What RONI subtracts is the warming"),
                 loc="left", color=INK, fontsize=10)
    _tidy(ax)

    # (b) the seasons whose label depends on the index, against what BKT saw
    ax = axes[1]
    obs = flip.dropna(subset=["bkt_peak_ppb"])
    y = np.arange(len(obs))
    xmax = obs.bkt_peak_ppb.max() * 1.30
    ax.barh(y, obs.bkt_peak_ppb, height=0.34, color="#b8c0c8", zorder=2)
    for i, r in enumerate(obs.itertuples()):
        ax.annotate(f"{r.bkt_peak_ppb:,.0f} ppb", (r.bkt_peak_ppb, i),
                    xytext=(5, 0), textcoords="offset points",
                    fontsize=8.5, color=INK, va="center")
        # the two labels sit above the bar rather than in the tick column, so
        # the axis stays as wide as the data
        ax.text(xmax * 0.012, i - 0.30,
                f"ONI {r.oni:+.2f} → {i18n.t(r.c_oni)}      "
                f"RONI {r.roni:+.2f} → {i18n.t(r.c_roni)}",
                fontsize=8, color=MUTED, va="center")
    ax.set_yticks(y)
    ax.set_yticklabels([str(int(r.year)) for r in obs.itertuples()],
                       fontsize=9.5, color=INK)
    ax.invert_yaxis()
    ax.set_xlim(0, xmax)
    ax.set_ylim(len(obs) - 0.45, -0.62)
    ax.set_xlabel(i18n.t("peak daily-median CO at BKT (ppb)"), color=MUTED)
    ax.set_title(i18n.t("b  Where they disagree, ONI matched the fires"),
                 loc="left", color=INK, fontsize=10)
    _tidy(ax)

    # (c) the closure: SST warming against the forcing-implied warming
    ax = axes[2]
    obs_rate = warm[warm.period == "2000-2025"].iloc[0]
    labels, vals, los, his, cols = [], [], [], [], []
    labels.append(i18n.t("observed\ntropical SST"))
    vals.append(obs_rate.trend_per_decade)
    los.append(obs_rate.lo)
    his.append(obs_rate.hi)
    cols.append(COOL)
    for r in tcr.itertuples():
        labels.append(i18n.t("implied by") + f"\n{r.site.split()[0]}")
        vals.append(r.degC_per_decade_best)
        los.append(r.degC_per_decade_lo)
        his.append(r.degC_per_decade_hi)
        cols.append(WARM)
    x = np.arange(len(vals))
    ax.bar(x, vals, width=0.55, color=cols, zorder=2)
    ax.errorbar(x, vals, yerr=[np.array(vals) - np.array(los),
                               np.array(his) - np.array(vals)],
                fmt="none", ecolor=INK, elinewidth=1.2, capsize=4, zorder=3)
    for xi, v, h in zip(x, vals, his):        # above the whisker, not the bar
        ax.annotate(f"{v:+.2f}", (xi, h), xytext=(0, 6),
                    textcoords="offset points", ha="center",
                    fontsize=9, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8, color=INK)
    ax.set_ylabel("°C / " + i18n.t("decade"), color=MUTED)
    ax.set_ylim(0, max(his) * 1.22)
    ax.set_xlabel(i18n.t("2000–2025 SST trend, and the forcing accrual"),
                  color=MUTED, fontsize=8.5)
    ax.set_title(i18n.t("c  Two records, one rate"),
                 loc="left", color=INK, fontsize=10)
    _tidy(ax)

    fig.suptitle(i18n.t("Figure 25  ENSO in a warming ocean, and the warming this "
                        "network implies"),
                 x=0.008, ha="left", fontsize=11, color=INK, y=1.03)
    fig.savefig(G.FIG / "f25_roni_warming.png")
    plt.close(fig)


def main():
    fig20()


if __name__ == "__main__":
    i18n.install(i18n.from_argv())
    G.style()
    main()
    print("wrote f25_roni_warming.png")
