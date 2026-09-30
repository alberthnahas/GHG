#!/usr/bin/env python3
"""Figures for the operational inversion report.

Drawn from the outputs of a99 (readiness, skill, error budget), a100 (the
localisation ledger), a102 (the prior audit) and a104 (the biosphere prior).
Written to outputs/operational/figures as figure_O01 to figure_O04.
"""
from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import a84_bkt_jmb_two_receptor as T
from a38_bkt_footprint_report import apply_chart_style, BLUE, ORANGE, MUTED

OUT = T.ROOT / "outputs/operational"
FIG = OUT / "figures"
GREEN, GREY, PURPLE, RED = "#009E73", "#8C979D", "#7B5EA7", "#C1442E"
COLOR = {"BKT": BLUE, "JMB": ORANGE}
TITLE_CHARS, HIGHLIGHT_CHARS = 78, 132
# the labels are chemistry, so they carry subscripts; DejaVu Sans has the glyphs
GAS = {"co2": "CO\u2082", "ch4": "CH\u2084"}


def head(fig, title: str, highlight: str) -> None:
    if len(title) > TITLE_CHARS:
        raise ValueError(f"Title of {len(title)} characters overflows: {title}")
    for line in highlight.split("\n"):
        if len(line) > HIGHLIGHT_CHARS:
            raise ValueError(f"Highlight line of {len(line)} characters overflows: {line}")
    fig.text(.04, .975, title, fontsize=10.5, weight="bold", va="top")
    fig.text(.04, .922, highlight, fontsize=7, color=MUTED, va="top", linespacing=1.35)


def footer(fig, text: str) -> None:
    fig.text(.04, .015, text, fontsize=6.8, color=MUTED)


def export(fig, number: int, stem: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(FIG / f"figure_O{number:02d}_{stem}.{ext}", dpi=300, facecolor="white")
    plt.close(fig)


def o01_error_budget() -> None:
    """What the source signal competes with, which explains every other result."""
    budget = pd.read_csv(OUT / "error_budget.csv")
    fig = plt.figure(figsize=(7.2, 3.8))
    for k, row in enumerate(budget.itertuples()):
        ax = fig.add_axes([.09 + k * .48, .30, .36, .46])
        terms = [("transport", row.transport_error, RED), ("measurement\nand local", row.measurement_and_local, GREY),
                 ("background", row.background, PURPLE)]
        bottom = 0.
        for name, value, colour in terms:
            ax.bar(0, value ** 2, .5, bottom=bottom, color=colour, label=name)
            bottom += value ** 2
        ax.bar(1, row.source_signal_sd ** 2, .5, color=GREEN, label="source signal")
        ax.set_xticks([0, 1], ["error", "signal"], fontsize=8)
        ax.set_ylabel(f"variance ({row.unit}²)", fontsize=7.5)
        ax.tick_params(labelsize=7)
        ax.set_title(f"({'ab'[k]}) {GAS[row.gas]}: signal to error {row.signal_to_error:.2f}", fontsize=8, loc="left")
        ax.spines[["top", "right"]].set_visible(False)
        if k == 0:
            ax.legend(fontsize=6.3, frameon=False, loc="upper left", bbox_to_anchor=(0, -.18), ncol=2)
    ratios = ", ".join(f"{GAS[r.gas]} {r.signal_to_error:.2f}" for r in budget.itertuples())
    head(fig, "The source signal is barely above the noise it arrives through",
         f"Variance of the modelled source signal at the receptors against the error it must compete with. Signal to error: {ratios}.\n"
         "Transport is the largest error term for both gases. A regional inversion begins to constrain fluxes near a ratio of three.")
    footer(fig, "Source: a99 error budget. Transport error is the measured ensemble spread times its calibrated amplitude.")
    export(fig, 1, "error_budget")


def o02_inventory() -> None:
    """The reported national inventory against what EDGAR assumes, and what it does at the towers."""
    ledger = pd.read_csv(T.ROOT / "outputs/inventory/local_inventory_ch4_2022_primap_ledger.csv")
    fig = plt.figure(figsize=(7.2, 4.0))
    ax = fig.add_axes([.30, .32, .30, .44])
    order = ledger.sort_values("factor")
    y = np.arange(len(order))
    ax.barh(y, order.factor, .6, color=[RED if f < 1 else GREEN for f in order.factor])
    ax.axvline(1, color="black", lw=.9)
    ax.set_yticks(y, [f"{c} ({g:.0f} to {r:.0f} Gg)" for c, g, r in
                      zip(order.ipcc_code, order.global_Gg, order.reported_Gg)], fontsize=7)
    ax.set_xlabel("reported national total divided by the global inventory", fontsize=7.5)
    ax.set_xscale("log"); ax.tick_params(labelsize=7)
    ax.set_title("(a) Indonesian methane, 2022", fontsize=8, loc="left")
    ax.spines[["top", "right"]].set_visible(False)

    bx = fig.add_axes([.72, .32, .25, .44])
    before = {"BKT": 121.2, "JMB": 200.1}; after = {"BKT": 101.0, "JMB": 105.9}
    x = np.arange(2)
    bx.bar(x - .2, [before[c] for c in ("BKT", "JMB")], .38, color=GREY, label="EDGAR")
    bx.bar(x + .2, [after[c] for c in ("BKT", "JMB")], .38, color=GREEN, label="localised")
    bx.set_xticks(x, ["BKT", "Jambi"], fontsize=7.5); bx.tick_params(labelsize=7)
    bx.set_ylabel("mean modelled prior (ppb)", fontsize=7.5)
    bx.legend(fontsize=6.3, frameon=False)
    bx.set_title("(b) At the towers", fontsize=8, loc="left")
    bx.spines[["top", "right"]].set_visible(False)
    head(fig, "The country reports a ninth of EDGAR's fugitive methane",
         "Indonesia's reported 2022 methane against the global gridded inventory, inside the country mask. Bars left of the line\n"
         "are sectors the country reports lower than EDGAR assumes. Fugitive emissions dominate the Jambi prior, so the tower sees it.")
    footer(fig, "Sources: PRIMAP-hist v2.6.1 HISTCR, which prioritises country-reported submissions; EDGAR v8; a100 ledger.")
    export(fig, 2, "inventory")


def o03_biosphere() -> None:
    """The three carbon dioxide biosphere priors by local solar hour."""
    table = pd.read_csv(OUT / "biosphere_prior_hybrid_comparison.csv")
    fig = plt.figure(figsize=(7.2, 3.6))
    ax = fig.add_axes([.10, .30, .36, .46])
    labels = {"diagnostic": GREY, "hybrid": GREEN, "ct-nrt": PURPLE}
    width = .26
    for k, (prior, colour) in enumerate(labels.items()):
        rows = table[table.prior.eq(prior)]
        ax.bar(np.arange(2) + (k - 1) * width, [float(rows[rows.station.eq(s)].afternoon.iloc[0]) for s in ("BKT", "JMB")],
               width, color=colour, label=prior)
    ax.axhline(0, color="black", lw=.8)
    ax.set_xticks(range(2), ["BKT", "Jambi"], fontsize=7.5)
    ax.set_ylabel("afternoon net flux (µmol m⁻² s⁻¹)", fontsize=7.5); ax.tick_params(labelsize=7)
    ax.legend(fontsize=6.3, frameon=False, loc="lower left")
    ax.set_title("(a) Afternoon drawdown", fontsize=8, loc="left")
    ax.spines[["top", "right"]].set_visible(False)

    bx = fig.add_axes([.60, .30, .36, .46])
    for k, (prior, colour) in enumerate(labels.items()):
        rows = table[table.prior.eq(prior)]
        bx.bar(np.arange(2) + (k - 1) * width, [float(rows[rows.station.eq(s)].amplitude.iloc[0]) for s in ("BKT", "JMB")],
               width, color=colour, label=prior)
    bx.set_xticks(range(2), ["BKT", "Jambi"], fontsize=7.5)
    bx.set_ylabel("diurnal amplitude (µmol m⁻² s⁻¹)", fontsize=7.5); bx.tick_params(labelsize=7)
    bx.set_title("(b) Diurnal amplitude", fontsize=8, loc="left")
    bx.spines[["top", "right"]].set_visible(False)
    head(fig, "The hybrid keeps CarbonTracker's magnitude and the diagnostic phase",
         "CarbonTracker is assimilated but its sub-daily phase inverts for a week over both tower cells; the diagnostic prior cannot\n"
         "invert but its amplitude is two to five times too large. The hybrid takes the daily mean and amplitude from one, the shape\n"
         "from the other. The inversion had independently implied an afternoon drawdown near -3 to -6.")
    footer(fig, "Source: a104 prior comparison at the tower cells, medians by local solar hour.")
    export(fig, 3, "biosphere")


def o04_scoreboard() -> None:
    """Every configuration the operational campaign ran, against the boundary null."""
    verdicts = json.loads((OUT / "inversion_readiness.json").read_text())
    rows = []
    for verdict in verdicts:
        if "receptors" not in verdict:
            continue
        tag = f"{verdict['gas']}{verdict['biosphere'] if verdict['biosphere'] != 'diagnostic' else ''}"
        tag += f"_{verdict['inventory']}" if verdict["inventory"] != "EDGAR" else ""
        tag += f"_folu{verdict['folu']}" if verdict.get("folu", "excluded") != "excluded" else ""
        path = OUT / f"inversion_{tag}_{verdict['scale']}_skill.csv"
        if not path.exists():
            continue
        skill = pd.read_csv(path)
        for row in skill.itertuples():
            rows.append(dict(gas=verdict["gas"], prior=verdict["prior"], scale=verdict["scale"], bins=verdict["bins"],
                             station=row.station, difference=row.rmse_difference, lo=row.ci_lo, hi=row.ci_hi))
    table = pd.DataFrame(rows)
    table = table[table.scale.eq("daily")].reset_index(drop=True)
    fig = plt.figure(figsize=(7.2, 5.0))
    ax = fig.add_axes([.44, .22, .52, .56])
    labels = []
    for index, row in enumerate(table.itertuples()):
        ax.errorbar(row.difference, index, xerr=[[row.difference - row.lo], [row.hi - row.difference]],
                    fmt="o", ms=4.5, color=COLOR[row.station], capsize=2, lw=1.1)
        labels.append(f"{GAS[row.gas]} {row.prior}, {row.station}")
    ax.axvline(0, color="black", lw=.9)
    ax.set_yticks(range(len(table)), labels, fontsize=6.4); ax.invert_yaxis()
    ax.set_xlabel("posterior minus boundary null (ppm for CO₂, ppb for CH₄)\nnegative favours the inversion", fontsize=7.5)
    ax.tick_params(labelsize=7)
    ax.set_title("Daily scale, every configuration", fontsize=8, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    head(fig, "Only the localised methane prior puts both towers on the right side",
         "Cross-validated difference from the boundary null with a 95% date-block interval, at the daily scale. Every interval still\n"
         "spans zero, so nothing is resolved; the methane priors built from Indonesia's own reported inventory are the only ones\n"
         "that put both towers on the favourable side.")
    footer(fig, "Source: a99 readiness campaign. Units differ between gases, so compare within a gas, not across.")
    export(fig, 4, "scoreboard")


FIGURES = (o01_error_budget, o02_inventory, o03_biosphere, o04_scoreboard)

if __name__ == "__main__":
    apply_chart_style()
    for figure in FIGURES:
        figure(); print(figure.__name__, flush=True)
