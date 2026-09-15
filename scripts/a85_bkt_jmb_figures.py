#!/usr/bin/env python3
"""Figures for the BKT + Jambi two-receptor experiment (a84).

Every panel is drawn from the CSV and NetCDF outputs of a84 in
outputs/hysplit/two_receptor. Written to outputs/hysplit/two_receptor/figures
as figure_T01 to figure_T04 (PNG and PDF).
"""
from __future__ import annotations
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patheffects as path_effects
from matplotlib.colors import LogNorm
from matplotlib.ticker import LogFormatterMathtext
import numpy as np
import pandas as pd
import xarray as xr
import cartopy.crs as ccrs
from pyproj import Geod
from shapely.geometry import box
from a38_bkt_footprint_report import apply_chart_style, BLUE, ORANGE, MUTED
from a50_bkt_inversion_figures import map_geometry
from bkt_footprint_spatial import display_surface
import a84_bkt_jmb_two_receptor as T

OUT = T.OUT
FIG = OUT / "figures"
GREEN, SKY, GREY, PURPLE = "#009E73", "#56B4E9", "#8C979D", "#7B5EA7"
COLOR = {"BKT": BLUE, "JMB": ORANGE}
NAMES = {"anthro_near": "Anthropogenic ≤500 km", "anthro_far": "Anthropogenic >500 km", "wetlands": "Wetlands",
         "fire": "Fires", "fuel_near": "Fuel exploitation ≤500 km", "other_near": "Other anthropogenic ≤500 km"}


def head(fig, title: str, highlight: str) -> None:
    fig.text(.04, .975, title, fontsize=10.5, weight="bold", va="top")
    fig.text(.04, .922, highlight, fontsize=7, color=MUTED, va="top", linespacing=1.35)


def footer(fig, text: str) -> None:
    fig.text(.04, .015, text, fontsize=6.8, color=MUTED)


def export(fig, number: int, stem: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(FIG / f"figure_T{number:02d}_{stem}.{ext}", dpi=300, facecolor="white")
    plt.close(fig)


def time_axis(ax):
    ax.set_xlim(T.WINDOW[0] - pd.Timedelta(hours=12), T.WINDOW[1] + pd.Timedelta(hours=12))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.tick_params(labelsize=7.5)


def map_axis(fig, rect, extent=(94, 115, -9, 9)):
    provinces, _, neighbors, _ = map_geometry()
    ax = fig.add_axes(rect, projection=ccrs.PlateCarree()); ax.set_extent(extent)
    ax.set_facecolor("#EAF3F7"); ax.set_rasterization_zorder(3)
    clip = box(extent[0] - .5, extent[2] - .5, extent[1] + .5, extent[3] + .5)
    for geometries, face in ((neighbors, "#E5E5E1"), (provinces.geometry, "#F8F7F2")):
        visible = [g.intersection(clip) for g in geometries if g.intersects(clip)]
        ax.add_geometries(visible, ccrs.PlateCarree(), facecolor=face, edgecolor="none", zorder=0)
        ax.add_geometries(visible, ccrs.PlateCarree(), facecolor="none", edgecolor="#697276", lw=.35, zorder=4)
    g = ax.gridlines(draw_labels=True, linewidth=.3, linestyle="--", alpha=.35)
    g.top_labels = g.right_labels = False; g.xlabel_style = g.ylabel_style = {"size": 7}
    for code, (name, lat, lon, _) in T.STATIONS.items():
        ax.plot(lon, lat, "*", ms=9, color=COLOR[code], markeredgecolor="white", zorder=8)
        ax.text(lon + .5, lat + .4, code, fontsize=7, weight="bold", color=COLOR[code], zorder=9,
                path_effects=[path_effects.withStroke(linewidth=2, foreground="white")])
    return ax


def circle(ax, code):
    _, lat, lon, _ = T.STATIONS[code]
    az = np.linspace(0, 360, 361)
    x, y, _ = Geod(ellps="WGS84").fwd(np.full(361, lon), np.full(361, lat), az, np.full(361, 500000))
    line = ax.plot(x, y, ls="--", color="#333", lw=.7, zorder=5)[0]
    line.set_path_effects([path_effects.withStroke(linewidth=1.6, foreground="white")])


def t01_footprints():
    op = pd.read_csv(T.TABLES / "operator_base.csv", parse_dates=["time_utc"])
    fig = plt.figure(figsize=(7.2, 4.6))
    for k, (code, left) in enumerate((("BKT", .05), ("JMB", .38))):
        with xr.open_dataset(T.INVERSION / f"spatial_operator_{code.lower()}.nc") as ds:
            f = ds.footprint.mean("receptor").load()
        mx = map_axis(fig, [left, .30, .30, .48]); circle(mx, code)
        y, x, den = display_surface(f.values, f.lat.values, f.lon.values, 0, 2)
        mesh = mx.contourf(x, y, np.ma.masked_less_equal(den, 0), levels=np.geomspace(1e-7, .03, 60), norm=LogNorm(1e-7, .03), cmap="YlOrRd", extend="max", zorder=2)
        sub = op[op.station.eq(code)]
        mx.set_title(f"({'ab'[k]}) {T.STATIONS[code][0]}: mean of {len(sub)} hours, total {float(f.sum()):.1f}\n"
                     f"within 500 km {sub.within500_sensitivity_percent.mean():.0f}%, within 50 km {sub.within50_sensitivity_percent.mean():.0f}%", fontsize=7.5)
    cb = fig.colorbar(mesh, cax=fig.add_axes([.10, .16, .52, .015]), orientation="horizontal"); cb.set_ticks(np.logspace(-7, -2, 6)); cb.formatter = LogFormatterMathtext(); cb.update_ticks(); cb.ax.tick_params(labelsize=7)
    cb.set_label("Sensitivity density [ppm / (µmol m⁻² s⁻¹) / km²]", fontsize=6.5, labelpad=1)
    cx = fig.add_axes([.75, .30, .22, .48])
    for code in T.STATIONS:
        sub = op[op.station.eq(code)]
        cx.plot(sub.time_utc, sub.endpoint_survival_fraction, "o", ms=3, color=COLOR[code], label=code)
    cx.axhline(.95, color=GREY, lw=.8, ls="--"); cx.set_ylabel("Endpoint retention (fraction)", fontsize=8)
    cx.set_ylim(.55, 1.02); time_axis(cx); cx.xaxis.set_major_locator(mdates.DayLocator(bymonthday=(1, 15))); cx.legend(fontsize=7, frameon=False, loc="lower left")
    cx.set_title(f"(c) Retention, 95% screen\nusable {op[op.station.eq('BKT')].transport_usable.mean()*100:.0f}% BKT, {op[op.station.eq('JMB')].transport_usable.mean()*100:.0f}% JMB", fontsize=7.5)
    cx.spines[["top", "right"]].set_visible(False)
    bkt, jmb = op[op.station.eq("BKT")], op[op.station.eq("JMB")]
    head(fig, "Two receptors at 100 m: Jambi samples the lowland, Kototabang the highlands",
         f"Three-seed ensemble means, 120 h backward, GFS 0.25°, 24 Nov to 31 Dec 2023, 06 and 18 UTC. Mean integrated sensitivity {bkt.sensitivity.mean():.1f} (BKT) and\n"
         f"{jmb.sensitivity.mean():.1f} (JMB) ppm per µmol m⁻² s⁻¹. Late-December particles leave the wide domain within 120 h.")
    footer(fig, "Dashed circles: 500 km. Retention below 0.95 in any seed excludes the hour from fitting. Source: a84 operator_base.csv, spatial_operator_*.nc.")
    export(fig, 1, "footprints")


def t02_series():
    pred = pd.read_csv(T.TABLES / "inversion_predictions.csv", parse_dates=["time_utc"])
    pred = pred[pred.case.eq("joint_screened")]
    fig = plt.figure(figsize=(7.2, 5.4))
    for k, code in enumerate(("BKT", "JMB")):
        ax = fig.add_axes([.08, .52 - .36 * k, .89, .28])
        s = pred[pred.station.eq(code)].sort_values("time_utc")
        ax.fill_between(s.time_utc, s.posterior_q025_ppb, s.posterior_q975_ppb, color=COLOR[code], alpha=.18, lw=0, label="Posterior 95%")
        ax.plot(s.time_utc, s.posterior_median_ppb, "-", color=COLOR[code], lw=1.1, label="Posterior median")
        ax.plot(s.time_utc, s.prior_inventory_ppb, ":", color=GREY, lw=1, label="Prior inventory")
        ax.plot(s.time_utc, s.background_ppb, "--", color=GREEN, lw=.9, label="Endpoint background")
        fit = s[s.training]; held = s[s.evaluation]; other = s[~s.training & ~s.evaluation]
        ax.plot(fit.time_utc, fit.observed_ppb, "o", ms=3.5, color="black", label="Observed, fitted")
        ax.plot(held.time_utc, held.observed_ppb, "o", ms=4.5, mfc="white", color="black", label="Observed, withheld")
        if len(other):
            ax.plot(other.time_utc, other.observed_ppb, "x", ms=4, color=PURPLE, label="Observed, excluded (JMB 18 UTC)")
        ax.set_ylabel("CH₄ (ppb)", fontsize=8); time_axis(ax); ax.spines[["top", "right"]].set_visible(False)
        ax.set_title(f"({'ab'[k]}) {T.STATIONS[code][0]} ({code})", fontsize=8.5, loc="left")
        if k == 1:
            ax.legend(fontsize=6.3, ncol=4, frameon=False, loc="upper left", bbox_to_anchor=(0, -.20))
    ev = pd.read_csv(T.TABLES / "inversion_evaluation.csv")
    e = ev[ev.split.eq("evaluation")].set_index(["case", "station"]).rmse_ppb
    head(fig, "Joint fit on screened hours tracks both sites; Jambi nights stay outside the model",
         f"Case joint_screened: shared multipliers, per-site offset and trend, Jambi 18 UTC hours excluded. Withheld-day RMSE {e['joint_screened','BKT']:.0f} ppb at BKT\n"
         f"(background-only {e['joint_screened_background_only','BKT']:.0f}) and {e['joint_screened','JMB']:.0f} ppb at JMB (background-only {e['joint_screened_background_only','JMB']:.0f}). Transport-screened hours are not plotted.")
    fig.text(.04, .005, "Source: a84 inversion_predictions.csv and inversion_evaluation.csv. Posterior band: parameter uncertainty only.", fontsize=6.8, color=MUTED)
    export(fig, 2, "series")


def t03_multipliers():
    par = pd.read_csv(T.TABLES / "inversion_parameters.csv")
    ev = pd.read_csv(T.TABLES / "inversion_evaluation.csv")
    cases = [("bkt_only", "BKT only"), ("jmb_only", "JMB only, all hours"), ("joint", "Joint, all hours"),
             ("joint_screened", "Joint, JMB nights excluded"), ("joint_screened_sector", "Joint screened, sector split")]
    fig = plt.figure(figsize=(7.2, 4.8))
    ax = fig.add_axes([.08, .30, .55, .50])
    params = ["anthro_near", "fuel_near", "other_near", "anthro_far", "wetlands", "fire"]
    width = .15
    for j, (case, label) in enumerate(cases):
        s = par[par.case.eq(case)].set_index("parameter")
        xs, med, lo, hi = [], [], [], []
        for i, name in enumerate(params):
            if name in s.index:
                xs.append(i + (j - 2) * width); med.append(s.loc[name, "median"]); lo.append(s.loc[name, "q025"]); hi.append(s.loc[name, "q975"])
        med, lo, hi = map(np.asarray, (med, lo, hi))
        ax.errorbar(xs, med, yerr=[med - lo, hi - med], fmt="o", ms=3.5, capsize=2, lw=1, label=label,
                    color=[BLUE, ORANGE, GREY, GREEN, PURPLE][j])
    ax.axhline(1, color="black", lw=.7); ax.set_yscale("log"); ax.set_ylim(.08, 8)
    ax.set_xticks(range(len(params)), ["Anthro.\n≤500 km", "Fuel expl.\n≤500 km", "Other anthro.\n≤500 km", "Anthro.\n>500 km", "Wetlands", "Fires"], fontsize=6.5)
    ax.set_ylabel("Posterior multiplier (median, 95%)", fontsize=8)
    ax.legend(fontsize=6.3, frameon=False, loc="upper center", bbox_to_anchor=(.5, -.17), ncol=3)
    ax.set_title("(a) Emission multipliers by case", fontsize=8.5, loc="left"); ax.spines[["top", "right"]].set_visible(False); ax.tick_params(labelsize=7.5)
    bx = fig.add_axes([.70, .30, .27, .50])
    rows = []
    for case, label in (("joint_screened", "Posterior"), ("joint_screened_background_only", "Background only"), ("joint_screened_prior_inventory", "Prior inventory")):
        for code in ("BKT", "JMB"):
            r = ev[ev.case.eq(case) & ev.station.eq(code) & ev.split.eq("evaluation")].iloc[0]
            rows.append(dict(model=label, station=code, rmse=r.rmse_ppb, n=int(r.n)))
    rows = pd.DataFrame(rows)
    for k, code in enumerate(("BKT", "JMB")):
        s = rows[rows.station.eq(code)]
        bx.bar(np.arange(3) + (k - .5) * .38, s.rmse, .36, color=COLOR[code], label=f"{code} ({s.n.iloc[0]} withheld h)")
    bx.set_xticks(range(3), ["Posterior", "Background\nonly", "Prior\ninventory"], fontsize=6.8); bx.set_ylabel("Withheld RMSE (ppb)", fontsize=8)
    bx.legend(fontsize=6.3, frameon=False); bx.set_title("(b) Withheld days, joint screened", fontsize=8.5, loc="left")
    bx.spines[["top", "right"]].set_visible(False); bx.tick_params(labelsize=7.5)
    sc = par[par.case.eq("joint_screened_sector")].set_index("parameter")
    head(fig, "Fuel exploitation near Jambi scales to a third of inventory",
         f"Sector split (joint, screened): fuel exploitation ≤500 km {sc.loc['fuel_near','median']:.2f} ({sc.loc['fuel_near','q025']:.2f}–{sc.loc['fuel_near','q975']:.2f}), other anthropogenic ≤500 km "
         f"{sc.loc['other_near','median']:.2f} ({sc.loc['other_near','q025']:.2f}–{sc.loc['other_near','q975']:.2f}),\nwetlands {sc.loc['wetlands','median']:.2f} ({sc.loc['wetlands','q025']:.2f}–{sc.loc['wetlands','q975']:.2f}). "
         f"Fitting Jambi nights pushes the transport error to its ceiling and the multipliers toward the prior.")
    footer(fig, "Priors: EDGAR v8.0 2022, LPJ-MERRA2 2023, CarbonTracker-CH4 2025 pyrogenic; log-normal prior factor 2. Source: a84 inversion tables.")
    export(fig, 3, "multipliers")


def t04_jambi_nights():
    op = pd.read_csv(T.TABLES / "operator_base.csv", parse_dates=["time_utc"])
    op["enh"] = op.ch4 - op.background_ppb; op["hour"] = op.time_utc.dt.hour
    op["wind"] = np.hypot(op.U10M, op.V10M)
    op = op[op.transport_usable]  # the hours the inversion can use; matches the report tables
    fig = plt.figure(figsize=(7.2, 3.9))
    for k, (code, left) in enumerate((("BKT", .08), ("JMB", .57))):
        ax = fig.add_axes([left, .19, .38, .52])
        s = op[op.station.eq(code)]
        for hour, marker, label in ((6, "o", "06 UTC (13 WIB)"), (18, "s", "18 UTC (01 WIB)")):
            q = s[s.hour.eq(hour)]
            ax.scatter(np.clip(q.PBLH, 10, None), q.enh, s=22, marker=marker, color=COLOR[code], alpha=.85 if hour == 6 else .5,
                       edgecolor="white", lw=.4, label=f"{label}: mean {q.enh.mean():.0f} ppb")
        ax.set_xscale("log"); ax.set_xlabel("GFS mixing depth at receptor (m, floored at 10)", fontsize=7.5)
        ax.set_ylabel("Observed minus endpoint background (ppb)", fontsize=7.5)
        ax.set_title(f"({'ab'[k]}) {T.STATIONS[code][0]}", fontsize=8.5, loc="left"); ax.legend(fontsize=6.3, frameon=False, loc="upper right")
        ax.spines[["top", "right"]].set_visible(False); ax.tick_params(labelsize=7.5); ax.axhline(0, color=GREY, lw=.6)
    j = op[op.station.eq("JMB")]
    head(fig, "Jambi night enhancements form under a collapsed boundary layer",
         f"At 18 UTC the GFS mixing depth at Jambi is {j[j.hour.eq(18)].PBLH.median():.0f} m (median) with 10 m wind {j[j.hour.eq(18)].wind.median():.1f} m s⁻¹; enhancements reach {j.enh.max():.0f} ppb.\n"
         f"At 06 UTC the depth is {j[j.hour.eq(6)].PBLH.median():.0f} m and the enhancement {j[j.hour.eq(6)].enh.mean():.0f} ± {j[j.hour.eq(6)].enh.std():.0f} ppb, against a prior of {(j[j.hour.eq(6)].anthro_near_ppb + j[j.hour.eq(6)].anthro_far_ppb + j[j.hour.eq(6)].wetlands_ppb + j[j.hour.eq(6)].fire_ppb).mean():.0f} ppb.\n"
         f"At BKT the model mixing depth also collapses at 18 UTC ({op[op.station.eq('BKT') & op.hour.eq(18)].PBLH.median():.0f} m median), but the enhancement averages {op[op.station.eq('BKT') & op.hour.eq(18)].enh.mean():.0f} ppb.")
    footer(fig, "Hours passing the retention screen. Native GFS mixing depth and wind in the receptor cell; CarbonTracker-CH4 2025 endpoint background.")
    export(fig, 4, "jambi_nights")


def t05_peat_season():
    from scipy.stats import spearmanr
    op = pd.read_csv(T.TABLES / "operator_base.csv", parse_dates=["time_utc"])
    peat = pd.read_csv(T.TABLES / "peat_operator.csv", parse_dates=["time_utc"])
    op = op.merge(peat, on=["station", "time_utc"]); op["hour"] = op.time_utc.dt.hour; op["enh"] = op.ch4 - op.background_ppb
    jm = op[op.station.eq("JMB") & op.transport_usable]
    diff = pd.read_csv(T.TABLES / "jambi_night_season_difference.csv")
    prox = pd.read_csv(T.TABLES / "peat_proximity.csv").set_index("station")
    with xr.open_dataset(T.INPUTS / "peat_fraction_jmb.nc") as ds:
        frac = ds.peat_fraction.load()
    with xr.open_dataset(T.INVERSION / "spatial_operator_jmb.nc") as ds:
        fp = ds.footprint.sel(receptor=jm[jm.hour.eq(18)].time_utc.values).mean("receptor").load()
    fig = plt.figure(figsize=(7.2, 4.5))
    extent = (101.4, 106.4, -4.3, 0.9)
    mx = map_axis(fig, [.04, .25, .30, .55], extent=extent)
    for text in list(mx.texts):  # map_axis labels both towers; drop any outside this extent
        x, y = text.get_position()
        if not (extent[0] <= x <= extent[1] and extent[2] <= y <= extent[3]):
            text.remove()
    sub = frac.sel(lat=slice(extent[2] - .5, extent[3] + .5), lon=slice(extent[0] - .5, extent[1] + .5))
    mesh = mx.pcolormesh(sub.lon, sub.lat, np.ma.masked_less_equal(sub.values, 0), cmap="Greens", vmin=0, vmax=1, shading="nearest", zorder=1, transform=ccrs.PlateCarree())
    vals = np.sort(fp.values.ravel())[::-1]; cum = np.cumsum(vals) / vals.sum()
    levels = sorted({float(vals[np.searchsorted(cum, q)]) for q in (.5, .8)})
    cs = mx.contour(fp.lon, fp.lat, fp.values, levels=levels, colors=[ORANGE], linewidths=[1.2, .7][:len(levels)], zorder=6, transform=ccrs.PlateCarree())
    _, lat, lon, _ = T.STATIONS["JMB"]
    az = np.linspace(0, 360, 181)
    for radius in (25, 50):
        x, y, _ = Geod(ellps="WGS84").fwd(np.full(181, lon), np.full(181, lat), az, np.full(181, radius * 1000))
        mx.plot(x, y, ls=":", color="#333", lw=.7, zorder=7, transform=ccrs.PlateCarree())
    mx.set_title("(a) Mapped peat fraction and the\nJambi 18 UTC footprint (50%, 80% of mass)", fontsize=7.5)
    cb = fig.colorbar(mesh, cax=fig.add_axes([.07, .135, .24, .015]), orientation="horizontal"); cb.ax.tick_params(labelsize=6.5)
    cb.set_label("Peat area fraction of 0.25° cell", fontsize=6.5, labelpad=1)
    from matplotlib.lines import Line2D
    ax = fig.add_axes([.42, .25, .25, .55])
    handles = []
    for hour, marker, label in ((6, "o", "06 UTC"), (18, "s", "18 UTC")):
        q = jm[jm.hour.eq(hour)]
        rho = spearmanr(q.peat_sensitivity, q.enh).statistic
        alpha = .9 if hour == 6 else .5
        ax.scatter(q.peat_sensitivity, q.enh, s=20, marker=marker, color=ORANGE, alpha=alpha, edgecolor="white", lw=.4)
        handles.append(Line2D([], [], ls="none", marker=marker, ms=5, color=ORANGE, alpha=alpha, label=f"{label}, n={len(q)}, rank r={rho:+.2f}"))
    ax.set_xlabel("Peat-weighted sensitivity\n(ppm per µmol m⁻² s⁻¹)", fontsize=7.5); ax.set_ylabel("Observed enhancement (ppb)", fontsize=7.5)
    ax.set_ylim(-20, max(jm.enh.max() * 1.22, 100))  # headroom so the legend sits above every point
    ax.legend(handles=handles, fontsize=6.3, frameon=False, loc="upper right", borderaxespad=.1); ax.tick_params(labelsize=7)
    ax.set_title("(b) Jambi enhancement vs peat exposure", fontsize=7.5, loc="left"); ax.spines[["top", "right"]].set_visible(False)
    bx = fig.add_axes([.78, .25, .20, .55])
    labels = {"co2_rate_ppm_h": "CO₂ rate", "ch4_rate_ppb_h": "CH₄ rate", "ratio_ppb_per_ppm": "CH₄:CO₂"}
    for k, (definition, offset, marker) in enumerate((("main", -.12, "o"), ("core", .12, "D"))):
        d = diff[diff.definition.eq(definition)].set_index("quantity")
        for i, q in enumerate(labels):
            r = d.loc[q]; w = abs(r.wet_median)
            y = i + offset
            bx.errorbar(100 * r.dry_minus_wet / w, y, xerr=[[100 * (r.dry_minus_wet - r.ci_lo) / w], [100 * (r.ci_hi - r.dry_minus_wet) / w]],
                        fmt=marker, color=[BLUE, GREEN][k], ms=4, capsize=2, lw=1, label=("Nov–Apr vs May–Oct" if definition == "main" else "Dec–Mar vs Jun–Sep") if i == 0 else None)
    bx.axvline(0, color=GREY, lw=.8); bx.set_yticks(range(3), list(labels.values()), fontsize=7); bx.set_ylim(2.4, -.4)
    bx.set_xlabel("Dry minus wet\n(% of wet-season median)", fontsize=7.5); bx.tick_params(labelsize=7)
    # centered in the empty band between the CO2 and CH4 rows (data y = 0.5 on the inverted 2.4 to -0.4 axis)
    bx.legend(fontsize=5.8, frameon=False, loc="center", bbox_to_anchor=(.5, (2.4 - .5) / 2.8), handlelength=1.2, borderaxespad=0)
    bx.set_title("(c) Night build-up, dry vs wet", fontsize=7.5, loc="left"); bx.spines[["top", "right"]].set_visible(False)
    main = diff[diff.definition.eq("main")].set_index("quantity")
    head(fig, "Jambi sits among peat, but its night methane does not follow peat",
         f"Mapped peat lies {prox.loc['JMB', 'nearest_peat_km']:.1f} km from the Jambi tower and covers {prox.loc['JMB', 'peat_share_25km_percent']:.0f}% of the land within 25 km. Night CO₂ build-up rises in the dry season\n"
         f"({main.loc['co2_rate_ppm_h', 'wet_median']:.2f} to {main.loc['co2_rate_ppm_h', 'dry_median']:.2f} ppm h⁻¹); the methane build-up and the CH₄:CO₂ ratio change by amounts the 2023–2025 record cannot resolve.")
    footer(fig, "Peat polygons: GHG_INDONESIA peatland layer, source not recorded. Season test: nights 2023–2025, week-block bootstrap. Source: a88 tables.")
    export(fig, 5, "peat_season")


if __name__ == "__main__":
    apply_chart_style()
    for f in (t01_footprints, t02_series, t03_multipliers, t04_jambi_nights, t05_peat_season):
        f(); print(f.__name__, flush=True)
