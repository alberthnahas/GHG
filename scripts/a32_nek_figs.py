"""Figures 27-28: the carbon economic value (Findings 90-100).

Two figures, each carrying one argument that a table makes less well.

f28 puts the *uncertainty* of a monetised claim beside its value, because the
finding is that the measurement is the small term and a table of four spans does
not show a factor of four against a factor of 1.18 as forcefully as a log axis.

f27 puts detectability and signal on the same axis at two scales - station and
nation - because Findings 93 and 100 are the same comparison two orders of
magnitude apart, and that is the whole point of them.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G
import i18n

OUT = G.ROOT / "outputs"
INK, MUTED = "#1b1f24", "#6b7280"
WARM, COOL, GREY = "#c0392b", "#1f6f8b", "#b8c0c8"


def _tidy(ax):
    ax.tick_params(colors=MUTED, labelsize=8)
    for s in ax.spines.values():
        s.set_color("#d7dbe0")


# --------------------------------------------------------------------- f28 --
def fig28_value():
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.2),
                             gridspec_kw=dict(wspace=0.34))

    # --- (a) the peat, priced ------------------------------------------------
    ax = axes[0]
    v = pd.read_csv(OUT / "k_jambi_value.csv")
    row = v.iloc[1]
    cols = [c for c in v.columns if c.startswith("IDR_million_")]
    labels = [c.replace("IDR_million_", "") for c in cols]
    short = [i18n.t("Carbon tax floor"), i18n.t("IDXCarbon average"),
             i18n.t("IDXCarbon opening"), i18n.t("EU ETS (contrast)")]
    vals = [float(row[c]) for c in cols]
    colours = [COOL, COOL, COOL, GREY]
    bars = ax.barh(range(len(vals)), vals, color=colours, height=0.62)
    ax.set_yticks(range(len(vals)))
    ax.set_yticklabels(short, fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xscale("log")
    for i, val in enumerate(vals):
        # the EU ETS bar runs to the right edge of the log axis, so its label
        # goes inside; the others would be unreadable inside a short bar
        inside = val > 10
        ax.text(val * (0.85 if inside else 1.12), i, f"{val:,.2f}",
                va="center", ha="right" if inside else "left", fontsize=8,
                color="#20262c" if inside else INK)
    ax.set_xlabel(i18n.t("IDR million per hectare per year (log scale)"), color=MUTED)
    ax.set_title(i18n.t("a  Jambi peat loss, priced"),
                 loc="left", color=INK, fontsize=10)
    ax.set_xlim(1.0, vals[-1] * 6)
    _tidy(ax)

    # --- (b) uncertainty budget ---------------------------------------------
    ax = axes[1]
    u = pd.read_csv(OUT / "k_uncertainty.csv")
    u = u[u.status != ""].dropna(subset=["low"])
    names = {"assumed": i18n.t("assumed"), "policy": i18n.t("policy"),
             "measured": i18n.t("measured")}
    short_terms = [i18n.t("Nocturnal layer depth"), i18n.t("Peat store depth"),
                   i18n.t("Carbon price"), i18n.t("Accumulation rate")]
    cmap = {"assumed": WARM, "policy": "#b8860b", "measured": COOL}
    spans = u.span.values
    cols = [cmap[s] for s in u.status]
    bars = ax.barh(range(len(spans)), spans, color=cols, height=0.62)
    ax.set_yticks(range(len(spans)))
    ax.set_yticklabels(short_terms, fontsize=8.5)
    ax.invert_yaxis()
    ax.axvline(1.0, color=MUTED, lw=0.8)
    for i, val in enumerate(spans):
        ax.text(val + 0.08, i, f"×{val:.2f}", va="center", fontsize=8, color=INK)
    ax.set_xlim(0, max(spans) * 1.35)
    ax.set_xlabel(i18n.t("multiplicative span, high case / low case"), color=MUTED)
    ax.set_title(i18n.t("b  Where the uncertainty is"),
                 loc="left", color=INK, fontsize=10)
    handles = [plt.Rectangle((0, 0), 1, 1, color=cmap[k]) for k in ("assumed", "policy", "measured")]
    ax.legend(handles, [names[k] for k in ("assumed", "policy", "measured")],
              loc="lower right", fontsize=8)
    _tidy(ax)

    # --- (c) Jakarta methane vs assumed depth --------------------------------
    ax = axes[2]
    j = pd.read_csv(OUT / "k_jakarta_ch4_value.csv")
    price_col = [c for c in j.columns if "IDXCarbon average" in c][0]
    x = j.assumed_layer_depth_m.values
    y = j[price_col].values / 1e3          # IDR billion
    ax.plot(x, y, marker="o", color=WARM, lw=1.6)
    for xi, yi in zip(x, y):
        ax.annotate(f"{yi:,.0f}", (xi, yi), textcoords="offset points",
                    xytext=(6, -10), fontsize=8, color=INK)
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"{int(v)}" for v in x])
    ax.set_xlim(60, 440)
    ax.set_xlabel(i18n.t("assumed nocturnal layer depth (m)"), color=MUTED)
    ax.set_ylabel(i18n.t("IDR billion per year"), color=MUTED)
    ax.set_title(i18n.t("c  Jakarta's methane vs assumed depth"),
                 loc="left", color=INK, fontsize=10)
    _tidy(ax)

    fig.suptitle(i18n.t("Figure 28  What a measured signal is worth, and where its uncertainty comes from"),
                 x=0.008, ha="left", fontsize=11, color=INK, y=1.03)
    fig.savefig(G.FIG / "f28_nek_value.png")
    plt.close(fig)


# --------------------------------------------------------------------- f27 --
def fig27_detectability():
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.4),
                             gridspec_kw=dict(wspace=0.26, width_ratios=[1.25, 1.0]))

    # --- (a) station scale ---------------------------------------------------
    ax = axes[0]
    d = pd.read_csv(OUT / "k_detect_abatement.csv")
    order = ["KMY", "JMB", "BKT", "SRG"]
    xs = np.arange(len(order))
    enh = [float(d[d.station == s].enhancement_co2e_ppm.iloc[0]) for s in order]
    ax.bar(xs, enh, width=0.56, color=COOL, label=i18n.t("measured enhancement over Bariri"))
    step12 = float(d[d.window_months == 12].detectable_step_ppm.iloc[0])
    step60 = float(d[d.window_months == 60].detectable_step_ppm.iloc[0])
    ax.axhline(step12, color=WARM, lw=1.4, ls="--",
               label=i18n.t("detectable step, 12 months"))
    ax.axhline(step60, color=WARM, lw=1.4, ls=":",
               label=i18n.t("detectable step, 60 months"))
    for x, e, s in zip(xs, enh, order):
        cut = float(d[(d.station == s) & (d.window_months == 60)].detectable_cut_pct.iloc[0])
        # clear the 60-month line, which two of the four bars sit below
        ax.text(x, max(e, step60) + 0.45, f"{cut:.0f}%", ha="center",
                fontsize=8.5, color=INK)
    ax.set_xticks(xs)
    ax.set_xticklabels([G.STATIONS[s][0] for s in order], fontsize=8.5)
    ax.set_ylim(0, 13.2)
    ax.set_ylabel(i18n.t("ppm CO$_2$-equivalent"), color=MUTED)
    ax.set_title(i18n.t("a  Station scale: the cut a five-year record could verify"),
                 loc="left", color=INK, fontsize=10)
    ax.legend(fontsize=8, loc="upper right")
    _tidy(ax)

    # --- (b) national scale --------------------------------------------------
    ax = axes[1]
    n = pd.read_csv(OUT / "k_national_limit.csv")
    thr = float(n.detectable_step_ppm.iloc[0])
    for tau, mk in zip(sorted(n.ventilation_time_d.unique()), ("o", "s", "^")):
        g = n[n.ventilation_time_d == tau].sort_values("pbl_depth_m")
        ax.plot(g.pbl_depth_m, g.steady_state_signal_ppm, marker=mk, lw=1.4,
                label=f"τ = {tau:g} " + i18n.t("d"))
    ax.axhline(thr, color=WARM, lw=1.6,
               label=i18n.t("what the record can resolve (5 yr)"))
    ax.set_yscale("log")
    ax.set_ylim(0.03, 6.0)
    ax.set_xticks([500, 1000, 2000])
    ax.set_xticklabels(["500", "1000", "2000"])
    ax.set_xlim(300, 2200)
    ax.set_xlabel(i18n.t("boundary-layer depth (m)"), color=MUTED)
    ax.set_ylabel(i18n.t("ppm CO$_2$"), color=MUTED)
    ax.set_title(i18n.t("b  National scale: the whole width of the 2035 NDC range"),
                 loc="left", color=INK, fontsize=10)
    ax.legend(fontsize=8, loc="lower left")
    _tidy(ax)

    fig.suptitle(i18n.t("Figure 27  What the network can verify, at two scales"),
                 x=0.008, ha="left", fontsize=11, color=INK, y=1.03)
    fig.savefig(G.FIG / "f27_nek_detectability.png")
    plt.close(fig)


def main():
    fig27_detectability()
    fig28_value()


if __name__ == "__main__":
    # install(), not set_lang(): install() also patches savefig so a non-default
    # language writes <name>_id.png.
    i18n.install(i18n.from_argv())
    G.style()
    main()
    print("wrote f27_nek_detectability.png, f28_nek_value.png")
