#!/usr/bin/env python3
"""Three-panel poster figure for the BKT methane inversion result.

(a) mean five-day receptor sensitivity with the 500 km partition,
(b) prior versus posterior emission multipliers,
(c) withheld-hour RMSE of the inversion against its baselines.

``--source original`` reads outputs/hysplit/inversion (published fit);
``--source revision`` reads outputs/hysplit/revision/inversion (a75 rerun).
Every number on the panel comes from the selected directory's CSV tables.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.ticker import LogFormatterMathtext, NullFormatter
import numpy as np
import pandas as pd
import xarray as xr
import a50_bkt_inversion_figures as F
from a38_bkt_footprint_report import apply_chart_style, BLUE, ORANGE
from bkt_footprint_spatial import display_surface

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {"original": ROOT / "outputs/hysplit/inversion", "revision": ROOT / "outputs/hysplit/revision/inversion"}
OUT = ROOT / "outputs/poster"


def build(source: str) -> Path:
    base = SOURCES[source]; tables = base / "tables"
    F.OUT = base  # map_axis writes its cartographic provenance beside the source
    apply_chart_style()
    operator = pd.read_csv(tables / "operator_base.csv", parse_dates=["time_utc"])
    usable = operator[operator.transport_usable]
    with xr.open_dataset(base / "spatial_operator_base.nc") as d:
        f = d.footprint.sel(receptor=usable.time_utc.values).mean("receptor").load()
    post = pd.read_csv(tables / "posterior_parameters.csv")
    ev = pd.read_csv(tables / "inversion_evaluation.csv").query("split == 'heldout'").set_index("model")
    n_train = int((~usable.holdout).sum()); n_held = int(usable.holdout.sum())

    fig = plt.figure(figsize=(7.2, 3.2))
    ax = F.map_axis(fig, [.04, .22, .29, .52], extent=(94, 112, -8, 8))
    y, x, den = display_surface(f.values, f.lat.values, f.lon.values, 1, 4)
    mesh = ax.contourf(x, y, np.ma.masked_less_equal(den, 0), levels=np.geomspace(1e-7, .01, 60),
                       norm=LogNorm(1e-7, .01), cmap="YlOrRd", extend="max" if den.max() > .01 else "neither", zorder=2)
    cb = fig.colorbar(mesh, cax=fig.add_axes([.07, .115, .23, .022]), orientation="horizontal")
    cb.set_ticks(np.logspace(-7, -2, 6)); cb.formatter = LogFormatterMathtext(); cb.update_ticks()
    cb.set_label("Sensitivity density, ppm / (µmol m⁻² s⁻¹) / km²", fontsize=6.5, labelpad=2); cb.ax.tick_params(labelsize=6.5)
    ax.set_title(f"(a) Mean receptor sensitivity, {len(usable)} hours", fontsize=8)

    bx = fig.add_axes([.48, .19, .20, .52])
    for i, row in post.iloc[:4].iterrows():
        bx.plot([row.prior_q025, row.prior_q975], [i + .12, i + .12], color="#B9C1C5", lw=4.5, label="Prior 95%" if i == 0 else None)
        bx.plot([row.q025, row.q975], [i - .08, i - .08], color=BLUE, lw=2, label="Posterior 95%" if i == 0 else None)
        bx.plot(row["median"], i - .08, "o", color=BLUE, ms=4.5)
    bx.axvline(1, color="#555", ls="--", lw=.8); bx.set_xscale("log"); bx.invert_yaxis()
    bx.set_yticks(range(4), ["Anthropogenic\n≤500 km", "Anthropogenic\n>500 km", "Wetlands", "Non-crop fires"], fontsize=7.5)
    bx.set_xticks([.25, .5, 1, 2, 4], ["0.25", "0.5", "1", "2", "4"]); bx.xaxis.set_minor_formatter(NullFormatter())
    bx.tick_params(axis="x", labelsize=7.5); bx.set_xlabel("Emission multiplier (inventory = 1)", fontsize=8)
    bx.legend(loc="lower left", fontsize=6.5, ncol=2, bbox_to_anchor=(-.02, .99), frameon=False, handlelength=1.6, columnspacing=1)
    bx.set_title("(b) Prior and posterior scaling", fontsize=8, pad=17)

    cx = fig.add_axes([.815, .19, .155, .52])
    names = ["inventory", "background_adjusted_inventory", "posterior", "background_only"]
    labels = ["Inventory", "Inventory +\nbackground", "Inversion", "Background\nonly"]
    values = ev.loc[names, "rmse_ppb"].values
    cx.barh(range(4), values, color=["#ADB6BB", "#88979F", BLUE, ORANGE])
    for i, v in enumerate(values):
        cx.text(v + 2, i, f"{v:.0f}", va="center", fontsize=6.5)
    cx.set_yticks(range(4), labels, fontsize=7); cx.invert_yaxis(); cx.set_xlim(0, values.max() * 1.3)
    cx.tick_params(axis="x", labelsize=7.5); cx.set_xlabel("Withheld RMSE (ppb)", fontsize=8)
    cx.set_title(f"(c) Withheld error, n = {n_held}", fontsize=8, pad=17)
    for a in (bx, cx):
        a.spines[["top", "right"]].set_visible(False)

    near = post.set_index("parameter").loc["anthro_near"]
    fig.text(.04, .97, "A single station tests methane inventories but cannot yet correct them",
             fontsize=9.5, weight="bold", va="top")
    fig.text(.04, .905, f"GFS/HYSPLIT-STILT five-day footprints, {n_train} fitting and {n_held} withheld hours, 9 Sep to 6 Oct 2019.\n"
             f"Anthropogenic ≤500 km multiplier {near['median']:.2f} ({near.q025:.2f} to {near.q975:.2f}); all four 95% intervals include the inventory value.",
             fontsize=6.8, color="#52616A", va="top", linespacing=1.4)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"poster_inversion_{source}.png"
    fig.savefig(path, dpi=260, facecolor="white"); fig.savefig(path.with_suffix(".pdf"), facecolor="white"); plt.close(fig)
    pd.DataFrame([dict(source=source, receptors=len(usable), fitting=n_train, withheld=n_held,
        anthro_near_median=near["median"], anthro_near_q025=near.q025, anthro_near_q975=near.q975,
        **{f"rmse_{k}": ev.loc[k, "rmse_ppb"] for k in names})]).to_csv(OUT / f"poster_inversion_{source}.csv", index=False)
    print(path)
    return path


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", default="original", choices=list(SOURCES))
    build(p.parse_args().source)
