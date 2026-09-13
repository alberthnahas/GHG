#!/usr/bin/env python3
"""Figures for the September 2026 BKT simulation revision and driver comparison.

Every panel is drawn from CSV or NetCDF outputs of a74 (campaign), a75 (revised
and ERA5 inversions), a76 (ERA5 runs) and a79 (driver comparison). Written to
outputs/hysplit/revision/figures as figure_R01 to figure_R06 (PNG and PDF).
"""
from __future__ import annotations
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import LogNorm
from matplotlib.ticker import LogFormatterMathtext, NullFormatter
import numpy as np
import pandas as pd
import xarray as xr
import a50_bkt_inversion_figures as F
from a38_bkt_footprint_report import apply_chart_style, BLUE, ORANGE, MUTED
from bkt_footprint_spatial import display_surface, cell_area_km2
import a74_bkt_simulation_revision as rev
import a76_bkt_era5_driver as era

ROOT = rev.ROOT
REV = ROOT / "outputs/hysplit/revision"
FIG = REV / "figures"
GREEN, SKY, GREY = "#009E73", "#56B4E9", "#8C979D"
NAMES = ["Anthropogenic ≤500 km", "Anthropogenic >500 km", "Wetlands", "Non-crop fires"]


def head(fig, title: str, highlight: str) -> None:
    fig.text(.04, .975, title, fontsize=10.5, weight="bold", va="top")
    fig.text(.04, .922, highlight, fontsize=7, color=MUTED, va="top", linespacing=1.35)


def footer(fig, text: str) -> None:
    fig.text(.04, .015, text, fontsize=6.8, color=MUTED)


def export(fig, number: int, stem: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(FIG / f"figure_R{number:02d}_{stem}.{ext}", dpi=300, facecolor="white")
    plt.close(fig)


def haversine(lat, lon):
    return rev.haversine_km(*np.meshgrid(lat, lon, indexing="ij"), -.202, 100.318)


def cumulative_curves(field: xr.DataArray):
    """Cumulative sensitivity share by backward lag (h) and by distance (km)."""
    hourly = field.sum(("lat", "lon")).values[::-1]  # most recent first
    lag = np.arange(1, len(hourly) + 1)
    agg = field.sum("time").values; d = haversine(field.lat.values, field.lon.values)
    order = np.argsort(d.ravel()); w = agg.ravel()[order]
    return lag, np.cumsum(hourly) / hourly.sum(), d.ravel()[order], np.cumsum(w) / w.sum()


def era5_mean(stamp: pd.Timestamp, group: str) -> xr.DataArray:
    members = []
    for seed in rev.SEEDS:
        f, _ = rev.read_layers(era.RUNS / f"{group}_s{seed}" / f"bkt_{stamp:%Y%m%dT%H%MZ}")
        members.append(f.sel(layer=1))
    return xr.concat(members, dim="m").mean("m")


def r01_numerics():
    ledger = pd.read_csv(REV / "tables/run_ledger.csv", parse_dates=["receptor_utc"])
    spread = pd.read_csv(REV / "tables/seed_spread.csv", parse_dates=["receptor_utc"]).query("family == 'ensemble'")
    old = pd.read_csv(ROOT / "outputs/hysplit/inversion/tables/transport_sensitivity_comparison.csv").query("group == 'seed_m10'")
    comp = pd.read_csv(REV / "inversion/tables/operator_comparison.csv", parse_dates=["time_utc"])
    fig = plt.figure(figsize=(7.2, 3.8)); ax = fig.add_axes([.08, .16, .40, .56]); bx = fig.add_axes([.60, .16, .36, .56])
    ax.plot(spread.receptor_utc, spread.sensitivity_cv_percent, "o", ms=3.5, color=BLUE, label="Revision: 3 seeds × 2,000 particles")
    ax.axhline(np.abs(old.sensitivity_change_percent).mean(), color=ORANGE, lw=1.2, ls="--",
               label=f"Published 540-particle seed test, mean |change| {np.abs(old.sensitivity_change_percent).mean():.1f}%")
    ax.set_ylabel("Seed CV of integrated sensitivity (%)"); F.time_axis(ax); ax.set_ylim(0, None)
    ax.legend(fontsize=6.5, loc="upper left", frameon=False); ax.set_title("(a) Numerical spread per receptor hour", fontsize=9)
    bx.scatter(100 * comp.retention_old, 100 * comp.retention_new, s=14, color=np.where(comp.originally_usable, BLUE, ORANGE))
    bx.axvline(95, color=GREY, lw=.8, ls=":"); bx.set_xlabel("Original domain retention (%)"); bx.set_ylabel("Widened domain retention (%)")
    bx.set_title("(b) Particle retention, 52 receptors", fontsize=9); bx.set_ylim(94, 101)
    bx.text(20, 96, "orange: failed the 95 % screen\nin the original domain", fontsize=6.5, color=ORANGE)
    for a in (ax, bx): a.spines[["top", "right"]].set_visible(False); a.tick_params(labelsize=7.5)
    head(fig, "Seed noise is now below 2 % and no receptor loses particles",
           f"Median seed CV {spread.sensitivity_cv_percent.median():.1f}% (max {spread.sensitivity_cv_percent.max():.1f}%). Widened-domain retention 100 % at all\n"
           f"52 hours; {int((comp.retention_old < .95).sum())} hours had failed the 95 % screen on the original domain.")
    footer(fig, "GFS/HYSPLIT-STILT, 120 h, 50–160° E, 40° S–30° N. Seed CV is finite-particle variability, conditional on one meteorology.")
    export(fig, 1, "numerics_retention")


def r02_height_window():
    terrain = pd.read_csv(REV / "tables/terrain_height.csv", parse_dates=["receptor_utc"])
    ledger = pd.read_csv(REV / "tables/run_ledger.csv", parse_dates=["receptor_utc"])
    spread = pd.read_csv(REV / "tables/seed_spread.csv", parse_dates=["receptor_utc"]).query("family == 'ensemble'")
    window = pd.read_csv(REV / "tables/afternoon_window.csv", parse_dates=["day_utc"])
    fig = plt.figure(figsize=(7.2, 3.8)); ax = fig.add_axes([.08, .18, .26, .54]); bx = fig.add_axes([.47, .18, .50, .54])
    labels = [f"{s:%d %b %H}Z" for s in sorted(terrain.receptor_utc.unique())]
    for i, (stamp, g) in enumerate(terrain.groupby("receptor_utc")):
        ax.plot([i] * len(g), g.ratio_80_over_30, "o", color=BLUE, ms=4)
    ax.axhline(1, color=GREY, lw=.8); ax.set_xticks(range(4), labels, fontsize=7, rotation=20)
    ax.set_ylabel("Sensitivity, 80 m release / 30 m release"); ax.set_title("(a) Terrain-matched release, 3 seeds each", fontsize=9)
    aft = ledger[ledger.group == "afternoon_s0"].copy(); aft["hour"] = aft.receptor_utc.dt.hour; aft["day"] = aft.receptor_utc.dt.normalize()
    six = spread.assign(day=spread.receptor_utc.dt.normalize(), hour=spread.receptor_utc.dt.hour).query("hour == 6")[["day", "hour", "sensitivity_mean"]].rename(columns={"sensitivity_mean": "sensitivity"})
    both = pd.concat([aft[["day", "hour", "sensitivity"]], six]).sort_values(["day", "hour"])
    for hour, marker, color in ((5, "v", SKY), (6, "o", BLUE), (7, "^", GREEN), (8, "s", ORANGE)):
        sub = both[both.hour == hour]; bx.plot(sub.day, sub.sensitivity, marker, ms=3.5, color=color, ls="none", label=f"{hour:02d} UTC ({hour + 7:02d} WIB)")
    bx.plot(window.day_utc, window.window_sensitivity, "-", color="#333", lw=1.2, label="12–15 WIB window mean")
    bx.set_ylabel("Integrated sensitivity"); F.time_axis(bx); bx.legend(fontsize=6.5, ncol=3, frameon=False, loc="upper left")
    bx.set_title("(b) Afternoon hours and the window mean", fontsize=9)
    for a in (ax, bx): a.spines[["top", "right"]].set_visible(False); a.tick_params(labelsize=7.5)
    head(fig, "Release height is a few-percent effect; the afternoon window is stable",
           f"80 m / 30 m sensitivity ratio median {terrain.ratio_80_over_30.median():.2f} (range {terrain.ratio_80_over_30.min():.2f}–{terrain.ratio_80_over_30.max():.2f}).\n"
           f"Members of the 12–15 WIB window differ by {window.member_sensitivity_cv_percent.median():.1f}% (median CV) over {len(window)} days.")
    footer(fig, "80 m puts the inlet at its true altitude above the nearest GFS cell terrain (816 m); 30 m is the inlet height above local ground.")
    export(fig, 2, "release_height_afternoon_window")


def r03_forward_extension():
    with xr.open_dataset(ROOT / "outputs/hysplit/gfs/analysis/GFS_ensemble.nc") as ds: old = ds.footprint_sensitivity.load()
    with xr.open_dataset(REV / "ensemble_mean/forward_bkt_20190926T0100Z.nc", engine="h5netcdf") as ds: new = ds.layer_sensitivity.load()
    e5 = era5_mean(rev.FORWARD_CASE, "forward")
    fig = plt.figure(figsize=(7.2, 5.8))
    ax = fig.add_axes([.08, .64, .38, .19]); bx = fig.add_axes([.58, .64, .38, .19])
    for field, label, color in ((old, "GFS 72 h, regional domain (published)", GREY), (new.sel(layer=1), "GFS 120 h, widened domain", BLUE), (e5, "ERA5 120 h", ORANGE)):
        lag, cl, dist, cd = cumulative_curves(field)
        ax.plot(lag, 100 * cl, color=color, lw=1.4, label=label); bx.plot(dist, 100 * cd, color=color, lw=1.4)
    ax.set_xlabel("Backward lag (h)"); ax.set_ylabel("Cumulative share (%)"); ax.set_xlim(0, 120); ax.legend(fontsize=6.5, frameon=False, loc="lower right")
    bx.set_xlabel("Distance from BKT (km)"); bx.set_xlim(0, 1500); bx.set_ylabel("Cumulative share (%)")
    ax.set_title("(a) Sensitivity by backward lag", fontsize=9); bx.set_title("(b) Sensitivity by distance", fontsize=9)
    for a in (ax, bx): a.spines[["top", "right"]].set_visible(False); a.tick_params(labelsize=7.5); a.axhline(50, color=GREY, lw=.6, ls=":")
    F.OUT = ROOT / "outputs/hysplit/revision"
    for k, (layer, title, left) in enumerate(((1, "(c) Surface layer (½ PBL)", .06), (2, "(d) Fixed layer to 1,000 m", .55))):
        mx = F.map_axis(fig, [left, .15, .40, .33], extent=(94, 115, -9, 9))
        f = new.sel(layer=layer).sum("time"); y, x, den = display_surface(f.values, f.lat.values, f.lon.values, 0, 2)
        mesh = mx.contourf(x, y, np.ma.masked_less_equal(den, 0), levels=np.geomspace(1e-7, .03, 60), norm=LogNorm(1e-7, .03), cmap="YlOrRd", extend="max", zorder=2)
        mx.set_title(f"{title}: {float(f.sum()):.1f} total", fontsize=8.5)
    cb = fig.colorbar(mesh, cax=fig.add_axes([.35, .085, .30, .013]), orientation="horizontal"); cb.set_ticks(np.logspace(-7, -2, 6)); cb.formatter = LogFormatterMathtext(); cb.update_ticks()
    cb.set_label("Sensitivity density [ppm / (µmol m⁻² s⁻¹) / km²]", fontsize=6.5, labelpad=1); cb.ax.tick_params(labelsize=6.5)
    head(fig, "Five days on the widened domain recover a third more influence",
           f"26 September 2019 01:00 UTC. Integrated surface sensitivity {float(old.sum()):.2f} (72 h regional, published),\n"
           f"{float(new.sel(layer=1).sum()):.2f} (120 h widened, GFS) and {float(e5.sum()):.2f} (ERA5). Panel (d): response to a flux released into the 1,000 m layer.")
    footer(fig, "Three-seed means, 10,020 particles per member. Maps: GFS 120 h, linear display reconstruction; totals from the unsmoothed field.")
    export(fig, 3, "forward_extension")


def r04_driver_maps():
    stamp = pd.Timestamp("2019-09-09T06:00")
    with xr.open_dataset(REV / f"ensemble_mean/ensemble_bkt_{stamp:%Y%m%dT%H%MZ}.nc", engine="h5netcdf") as ds: gfs = ds.layer_sensitivity.sel(layer=1).load()
    e5 = era5_mean(stamp, "anchor")
    summary = pd.read_csv(era.OUT / "tables/driver_comparison_summary.csv", parse_dates=["receptor_utc"])
    fig = plt.figure(figsize=(7.2, 4.1)); F.OUT = ROOT / "outputs/hysplit/era5"
    for k, (field, title, left) in enumerate(((gfs, "(a) GFS", .07), (e5, "(b) ERA5", .40))):
        mx = F.map_axis(fig, [left, .27, .29, .46], extent=(94, 115, -9, 9))
        f = field.sum("time"); y, x, den = display_surface(f.values, f.lat.values, f.lon.values, 0, 2)
        mesh = mx.contourf(x, y, np.ma.masked_less_equal(den, 0), levels=np.geomspace(1e-7, .03, 60), norm=LogNorm(1e-7, .03), cmap="YlOrRd", extend="max", zorder=2)
        mx.set_title(f"{title}: total {float(f.sum()):.2f}", fontsize=8.5)
    cb = fig.colorbar(mesh, cax=fig.add_axes([.12, .13, .50, .015]), orientation="horizontal"); cb.set_ticks(np.logspace(-7, -2, 6)); cb.formatter = LogFormatterMathtext(); cb.update_ticks(); cb.ax.tick_params(labelsize=7)
    cb.set_label("Sensitivity density [ppm / (µmol m⁻² s⁻¹) / km²]", fontsize=6.5, labelpad=1)
    cx = fig.add_axes([.78, .30, .19, .43])
    labels = [f"{r.receptor_utc:%d %b %H}Z" if r.case == "anchor" else "26 Sep 01Z\n(forward)" for r in summary.itertuples()]
    cx.errorbar(range(len(summary)), summary.ratio_mean, yerr=[summary.ratio_mean - summary.ratio_min, summary.ratio_max - summary.ratio_mean], fmt="o", color=BLUE, ms=4, capsize=2)
    cx.axhline(1, color=GREY, lw=.8); cx.set_xticks(range(len(summary)), labels, fontsize=6.5, rotation=35, ha="right"); cx.set_ylabel("ERA5 / GFS integrated sensitivity", fontsize=8)
    cx.set_title("(c) Ratio, 3 seeds each", fontsize=8.5); cx.spines[["top", "right"]].set_visible(False); cx.tick_params(labelsize=7.5)
    head(fig, "ERA5 moves the footprint and adds surface sensitivity",
           f"Maps: 9 September 2019 06:00 UTC, 120 h, three-seed means. Across five cases the ERA5/GFS ratio is\n"
           f"{summary.ratio_min.min():.2f}–{summary.ratio_max.max():.2f} and the cell-level spatial difference {summary.spatial_diff_mean.min():.0f}–{summary.spatial_diff_mean.max():.0f}% of the GFS total.")
    footer(fig, "ERA5: hourly, 16 pressure levels, 70–140° E. GFS: 3-hourly, 55 hybrid levels, 50–160° E. Same receptor, seeds, particles and STILT settings.")
    export(fig, 4, "driver_maps")


def posterior_sets():
    pub = pd.read_csv(ROOT / "outputs/hysplit/inversion/tables/posterior_parameters.csv").set_index("parameter")
    base = pd.read_csv(REV / "inversion/tables/posterior_parameters.csv").set_index("parameter")
    var = pd.read_csv(REV / "inversion/tables/variant_parameters.csv")
    e5 = pd.read_csv(era.OUT / "inversion/tables/variant_parameters.csv")
    sets = [("Published (27 h, 540 particles)", pub, GREY), ("Revised ensemble, fixed covariance", base, SKY),
            ("Revised, tuned covariance", var[var.case == "tuned"].set_index("parameter"), BLUE),
            ("ERA5, tuned covariance", e5[e5.case == "tuned"].set_index("parameter"), ORANGE)]
    return sets, var[var.case == "nearfield_tuned"].set_index("parameter")


def r05_inversion_update():
    sets, near = posterior_sets()
    scan = pd.read_csv(REV / "inversion/tables/transport_error_scan.csv"); scan5 = pd.read_csv(era.OUT / "inversion/tables/transport_error_scan.csv")
    tuned = json.load(open(REV / "inversion/variants.json"))["tuned_transport_fraction"]; tuned5 = json.load(open(era.OUT / "inversion/variants.json"))["tuned_transport_fraction"]
    fig = plt.figure(figsize=(7.2, 4.6)); ax = fig.add_axes([.08, .26, .26, .52]); bx = fig.add_axes([.52, .26, .45, .52])
    ax.plot(scan.transport_fraction, scan.reduced_chi_square, "o-", color=BLUE, ms=3.5, label=f"GFS, tuned {tuned:.2f}")
    ax.plot(scan5.transport_fraction, scan5.reduced_chi_square, "s-", color=ORANGE, ms=3.5, label=f"ERA5, tuned {tuned5:.2f}")
    ax.axhline(1, color=GREY, lw=.8, ls="--"); ax.axvline(.5, color=GREY, lw=.8, ls=":"); ax.text(.52, 1.15, "published\n50 %", fontsize=6.5, color=GREY)
    ax.set_xlabel("Transport-error fraction of prior increment"); ax.set_ylabel("Training reduced χ²"); ax.legend(fontsize=6.5, frameon=False)
    ax.set_title("(a) Error-model consistency", fontsize=9)
    keys = ["anthro_near", "anthro_far", "wetlands", "fire"]; n = len(sets)
    for j, (label, table, color) in enumerate(sets):
        for i, key in enumerate(keys):
            y = i + (j - (n - 1) / 2) * .17
            bx.plot([table.loc[key, "q025"], table.loc[key, "q975"]], [y, y], color=color, lw=2 if j else 1.4, solid_capstyle="butt")
            bx.plot(table.loc[key, "median"], y, "o", color=color, ms=4, label=label if i == 0 else None)
    y = 0 - (n + 1) / 2 * .17 - .05
    for key, lab in (("anthro_within50", "≤50 km"), ("anthro_50_500", "50–500 km")):
        bx.plot([near.loc[key, "q025"], near.loc[key, "q975"]], [y, y], color=GREEN, lw=1.6); bx.plot(near.loc[key, "median"], y, "D", color=GREEN, ms=3.5, label="Near-field split, tuned" if key == "anthro_within50" else None)
        bx.text(near.loc[key, "q975"] * 1.08, y, lab, fontsize=6, color=GREEN, va="center"); y -= .17
    bx.axvline(1, color="#555", ls="--", lw=.8); bx.set_xscale("log"); bx.set_yticks(range(4), NAMES, fontsize=7.5); bx.invert_yaxis(); bx.set_ylim(3.6, -1.1)
    bx.set_xticks([.1, .25, .5, 1, 2], ["0.1", "0.25", "0.5", "1", "2"]); bx.xaxis.set_minor_formatter(NullFormatter()); bx.set_xlabel("Emission multiplier (inventory = 1, log scale)")
    bx.legend(fontsize=6.3, loc="upper center", bbox_to_anchor=(.5, -.20), ncol=2, frameon=False, handlelength=1.5); bx.set_title("(b) Posterior 95 % intervals", fontsize=9)
    for a in (ax, bx): a.spines[["top", "right"]].set_visible(False); a.tick_params(labelsize=7.5)
    t = sets[2][1]
    head(fig, "With a consistent error model, priors scale down by two to four",
           f"Tuned GFS fit: anthropogenic ≤500 km {t.loc['anthro_near','median']:.2f} ({t.loc['anthro_near','q025']:.2f}–{t.loc['anthro_near','q975']:.2f}), >500 km {t.loc['anthro_far','median']:.2f},\n"
           f"wetlands {t.loc['wetlands','median']:.2f}, non-crop fires {t.loc['fire','median']:.2f} (upper bound {t.loc['fire','q975']:.2f}).")
    footer(fig, "Published: 27 hours, 540 particles, original domain. Revised and ERA5: 52 and 49 hours, 3 × 2,000 particles. Conditional on driver, priors and error model.")
    export(fig, 5, "inversion_update")


def r06_withheld():
    ev = pd.read_csv(REV / "inversion/tables/inversion_evaluation.csv").query("split == 'heldout'").set_index("model")
    ve = pd.read_csv(REV / "inversion/tables/variant_evaluation.csv").query("split == 'heldout'").set_index("case")
    ev5 = pd.read_csv(era.OUT / "inversion/tables/inversion_evaluation.csv").query("split == 'heldout'").set_index("model")
    ve5 = pd.read_csv(era.OUT / "inversion/tables/variant_evaluation.csv").query("split == 'heldout'").set_index("case")
    pub = pd.read_csv(ROOT / "outputs/hysplit/inversion/tables/inversion_evaluation.csv").query("split == 'heldout'").set_index("model")
    pred = pd.read_csv(REV / "inversion/tables/variant_predictions.csv", parse_dates=["time_utc"]).query("case == 'tuned'")
    fig = plt.figure(figsize=(7.2, 4.6)); ax = fig.add_axes([.08, .56, .88, .24]); bx = fig.add_axes([.24, .12, .72, .27])
    ax.plot(pred.time_utc, pred.observed_ppb, ".", color="#222", ms=4, label="Observed")
    ax.fill_between(pred.time_utc, pred.posterior_q025_ppb, pred.posterior_q975_ppb, color=BLUE, alpha=.2, label="95 % model mean, tuned")
    ax.plot(pred.time_utc, pred.posterior_median_ppb, "-", color=BLUE, lw=1.1, label="Posterior median")
    held = pred[pred.holdout]; ax.scatter(held.time_utc, held.observed_ppb, facecolors="none", edgecolors=ORANGE, marker="s", s=26, label="Withheld", zorder=6)
    ax.set_ylabel("CH₄ (ppb)"); F.time_axis(ax); ax.legend(fontsize=6.5, ncol=4, frameon=False, loc="upper left"); ax.set_title("(a) Tuned GFS fit against all 52 receptor hours", fontsize=9)
    rows = [("Raw inventory", pub.loc["inventory", "rmse_ppb"], ev.loc["inventory", "rmse_ppb"], ev5.loc["inventory", "rmse_ppb"]),
            ("Inventory + fitted background", pub.loc["background_adjusted_inventory", "rmse_ppb"], ev.loc["background_adjusted_inventory", "rmse_ppb"], ev5.loc["background_adjusted_inventory", "rmse_ppb"]),
            ("Inversion, fixed covariance", pub.loc["posterior", "rmse_ppb"], ev.loc["posterior", "rmse_ppb"], ev5.loc["posterior", "rmse_ppb"]),
            ("Inversion, tuned covariance", np.nan, ve.loc["tuned", "rmse_ppb"], ve5.loc["tuned", "rmse_ppb"]),
            ("Background only", pub.loc["background_only", "rmse_ppb"], ev.loc["background_only", "rmse_ppb"], ev5.loc["background_only", "rmse_ppb"])]
    y = np.arange(len(rows)); w = .26
    for k, (label, color) in enumerate((("Published", GREY), ("Revised GFS", BLUE), ("ERA5", ORANGE))):
        vals = [r[k + 1] for r in rows]; bx.barh(y + (k - 1) * w, vals, height=w, color=color, label=label)
        for yy, v in zip(y + (k - 1) * w, vals):
            if np.isfinite(v): bx.text(v + 1, yy, f"{v:.0f}", va="center", fontsize=6)
    bx.set_yticks(y, [r[0] for r in rows], fontsize=7); bx.invert_yaxis(); bx.set_xlabel("Withheld RMSE (ppb)"); bx.legend(fontsize=6.5, frameon=False, loc="lower right")
    bx.set_title("(b) Withheld-hour error by model and driver", fontsize=9)
    for a in (ax, bx): a.spines[["top", "right"]].set_visible(False); a.tick_params(labelsize=7.5)
    head(fig, "Only the tuned GFS fit beats the background-only baseline",
           f"Withheld RMSE: tuned GFS {ve.loc['tuned','rmse_ppb']:.1f} ppb versus background-only {ve.loc['tuned_background_only','rmse_ppb']:.1f}; tuned ERA5 {ve5.loc['tuned','rmse_ppb']:.1f} versus {ve5.loc['tuned_background_only','rmse_ppb']:.1f}.\n"
           "Published fit: 6 withheld hours; revised fits: 13.")
    footer(fig, "Withheld hours fixed before fitting (every fourth calendar day). Usable hours: published 27; revised GFS 52; ERA5 49.")
    export(fig, 6, "withheld_evaluation")


if __name__ == "__main__":
    apply_chart_style()
    for fn in (r01_numerics, r02_height_window, r03_forward_extension, r04_driver_maps, r05_inversion_update, r06_withheld):
        fn(); print("wrote", fn.__name__)
