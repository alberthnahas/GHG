#!/usr/bin/env python3
"""Figures for the BKT + Jambi CO2 report.

Every panel is drawn from the CSV and NetCDF outputs of a89 (CT-NRT operator and
inversion), a90 (diagnostic biosphere), a91 (scored experiments), a92 (release
heights) and a93 (2024 extension). Written to outputs/hysplit/two_receptor/figures
as figure_C01 to figure_C05 (PNG and PDF).
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.legend_handler import HandlerTuple
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
import xarray as xr

import a84_bkt_jmb_two_receptor as T
import a89_bkt_jmb_co2 as C
import a90_bkt_jmb_co2_improved as I
import a91_bkt_jmb_co2_experiments as X
from a38_bkt_footprint_report import apply_chart_style, BLUE, ORANGE, MUTED

FIG = T.OUT / "figures"
GREEN, GREY, PURPLE = "#009E73", "#8C979D", "#7B5EA7"
COLOR = {"BKT": BLUE, "JMB": ORANGE}


TITLE_CHARS, HIGHLIGHT_CHARS = 78, 132


def head(fig, title: str, highlight: str) -> None:
    """Title and highlight, with the character limits that keep both inside a 7.2 inch page."""
    if len(title) > TITLE_CHARS:
        raise ValueError(f"Title of {len(title)} characters overflows the page: {title}")
    for line in highlight.split("\n"):
        if len(line) > HIGHLIGHT_CHARS:
            raise ValueError(f"Highlight line of {len(line)} characters overflows the page: {line}")
    fig.text(.04, .975, title, fontsize=10.5, weight="bold", va="top")
    fig.text(.04, .922, highlight, fontsize=7, color=MUTED, va="top", linespacing=1.35)


def footer(fig, text: str) -> None:
    fig.text(.04, .015, text, fontsize=6.8, color=MUTED)


def export(fig, number: int, stem: str) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(FIG / f"figure_C{number:02d}_{stem}.{ext}", dpi=300, facecolor="white")
    plt.close(fig)


def period_axis(ax, frame) -> None:
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=3, maxticks=5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.tick_params(labelsize=7)


def gapped(frame: pd.DataFrame, columns: tuple[str, ...], max_gap_days: int = 2) -> pd.DataFrame:
    """Insert a blank row wherever the dates jump, so lines break instead of spanning the gap."""
    frame = frame.sort_values("time_utc").reset_index(drop=True)
    breaks = frame.index[frame.time_utc.diff() > pd.Timedelta(days=max_gap_days)]
    if not len(breaks):
        return frame
    blanks = pd.DataFrame({"time_utc": frame.time_utc[breaks - 1] + pd.Timedelta(hours=12)})
    for column in columns:
        blanks[column] = np.nan
    return pd.concat([frame, blanks]).sort_values("time_utc")


def c01_series(variant: str = "best_all", suffix: str = "_round6") -> None:
    """Observed afternoon CO2 with the background, prior and posterior at both towers."""
    pred = pd.read_csv(T.TABLES / f"co2_experiments{suffix}_predictions.csv", parse_dates=["time_utc"])
    pred = pred[pred.case.eq(variant)]
    periods = sorted(pred.time_utc.dt.year.unique())
    lines = ("prior_ppm", "plain_background_ppm", "posterior_ppm")
    fig = plt.figure(figsize=(7.2, 5.0))
    width = (.90 - .05 * (len(periods) - 1)) / len(periods)
    for row, code in enumerate(("BKT", "JMB")):
        for column, year in enumerate(periods):
            g = pred[pred.station.eq(code) & pred.time_utc.dt.year.eq(year)]
            broken = gapped(g, lines)
            ax = fig.add_axes([.075 + column * (width + .05), .55 - .38 * row, width, .25])
            ax.plot(broken.time_utc, broken.prior_ppm, ":", color=GREY, lw=1, marker=".", ms=2.5)
            ax.plot(broken.time_utc, broken.plain_background_ppm, "--", color=GREEN, lw=1, marker=".", ms=2.5)
            ax.plot(broken.time_utc, broken.posterior_ppm, "-", color=COLOR[code], lw=1.2, marker=".", ms=3)
            ax.plot(g.time_utc, g.observed_ppm, "o", ms=3.5, color="black")
            period_axis(ax, g)
            ax.spines[["top", "right"]].set_visible(False)
            if column == 0:
                ax.set_ylabel("CO₂ (ppm)", fontsize=8)
            ax.set_title(f"({'abcd'[row * len(periods) + column]}) {T.STATIONS[code][0]}, {year}", fontsize=8, loc="left", pad=6)
            if row == 1 and column == 0:
                keys = [Line2D([], [], color=GREY, ls=":", marker=".", ms=3),
                        Line2D([], [], color=GREEN, ls="--", marker=".", ms=3),
                        (Line2D([], [], color=COLOR["BKT"], lw=1.2), Line2D([], [], color=COLOR["JMB"], lw=1.2)),
                        Line2D([], [], color="black", ls="none", marker="o", ms=3.5)]
                ax.legend(keys, ["Prior", "Background only", "Posterior, in the tower colour", "Observed, 12-14 WIB mean"],
                          fontsize=6.6, ncol=4, frameon=False, loc="upper left", bbox_to_anchor=(0, -.26),
                          handler_map={tuple: HandlerTuple(ndivide=None)})
    head(fig, "Afternoon CO₂ at the two towers against the fitted model",
         f"Case {variant.replace('_', ' ')}: diagnostic biosphere, per-tower factors and transport errors, CH₄ covariate. Observations are 12-14 WIB means after\n"
         "the CO₂-only spike screen; hours with a GFS mixing depth below 300 m are excluded. Lines break where no receptor passed the screens.")
    footer(fig, "Source: a91 experiment predictions. Background only is the fitted per-tower offset and trend on the endpoint background.")
    export(fig, 1, "series")


def solar_median(values: np.ndarray, stamps: pd.DatetimeIndex, lon: float) -> pd.Series:
    solar = (stamps.hour + stamps.minute / 60 + lon / 15) % 24
    return pd.DataFrame(dict(solar=np.round(solar).astype(int) % 24, flux=values)).groupby("solar").flux.median()


def c02_biosphere_priors() -> None:
    """CT-NRT optimized biosphere against the diagnostic prior at the two tower cells."""
    with xr.open_dataset(C.INPUTS / "ctnrt_fluxes_box.nc") as ds:
        ctnrt = ds.load()
    with xr.open_dataset(I.INPUTS / "diagnostic_biosphere.nc") as ds:
        diag = ds.load()
    phase = pd.read_csv(T.TABLES / "co2_ctnrt_phase_daily.csv", parse_dates=["date"])
    first, last = pd.Timestamp(C.INVERTED_EPISODE[0]), pd.Timestamp(C.INVERTED_EPISODE[1])
    fig = plt.figure(figsize=(7.2, 4.0))
    for k, code in enumerate(("BKT", "JMB")):
        _, lat, lon, _ = T.STATIONS[code]
        ax = fig.add_axes([.075 + k * .30, .25, .24, .50])
        ct = ctnrt.bio_net.sel(lat=lat, lon=lon, method="nearest")
        ct_stamps = pd.DatetimeIndex(ct.time.values)
        episode = (ct_stamps >= first) & (ct_stamps < last + pd.Timedelta(days=1))
        dg = diag.gpp.sel(lat=lat, lon=lon, method="nearest") + diag.resp.sel(lat=lat, lon=lon, method="nearest")
        curves = ((solar_median(ct.values, ct_stamps, lon), PURPLE, "-", "CT-NRT, whole window"),
                  (solar_median(ct.values[episode], ct_stamps[episode], lon), PURPLE, "--", f"CT-NRT, {first:%d %b} to {last:%d %b}"),
                  (solar_median(dg.values, pd.DatetimeIndex(dg.time.values), lon), GREEN, "-", "Diagnostic prior"))
        for median, color, style, label in curves:
            ax.plot(median.index, median.values, style, marker="o", ms=3, color=color, lw=1.2, label=label)
        ax.axhline(0, color=GREY, lw=.8); ax.set_xticks(range(0, 25, 6))
        ax.set_xlabel("local solar hour", fontsize=7.5); ax.tick_params(labelsize=7)
        if k == 0:
            ax.set_ylabel("Net biosphere flux (µmol m⁻² s⁻¹)", fontsize=7.5)
            fig.legend(*ax.get_legend_handles_labels(), fontsize=6.6, frameon=False, ncol=3,
                       loc="lower left", bbox_to_anchor=(.07, .055))
        ax.set_title(f"({'ab'[k]}) {T.STATIONS[code][0]} cell", fontsize=8, loc="left")
        ax.spines[["top", "right"]].set_visible(False)
    cx = fig.add_axes([.72, .25, .25, .50])
    cx.plot(phase.date, phase.sumatra_inverted_percent, "-", color=PURPLE, lw=1.2, label="Sumatra land cells")
    cx.plot(phase.date, phase.domain_inverted_percent, "-", color=GREY, lw=1, label="Whole domain")
    cx.axvspan(first, last, color=PURPLE, alpha=.10, lw=0)
    period_axis(cx, phase)
    cx.set_ylabel("CT-NRT cells with an inverted\nday-night cycle (%)", fontsize=7.5)
    cx.legend(fontsize=6.3, frameon=False, loc="upper right"); cx.set_title("(c) Inverted phase by day", fontsize=8, loc="left")
    cx.spines[["top", "right"]].set_visible(False)
    window = phase[(phase.date >= first) & (phase.date <= last)]
    head(fig, "One week where the optimized biosphere flux runs backwards",
         f"Medians by local solar hour, 19 November to 31 December 2023. From {first:%d %B} to {last:%d %B} the CT-NRT flux releases\n"
         f"CO₂ by day and takes it up at night over {window.sumatra_inverted_percent.mean():.0f}% of Sumatran land cells, the shaded week in panel (c), and both tower\n"
         "cells are among them. The diagnostic prior is built from sunlight and temperature, so its phase cannot invert.")
    footer(fig, "Sources: CT-NRT.v2025-1 three-hourly optimized biosphere flux; a90 diagnostic prior; a90 daily phase table.")
    export(fig, 2, "biosphere_priors")


def c03_scoreboard(suffix: str = "_round6") -> None:
    """Cross-validated skill by variant with the date-block bootstrap interval."""
    skill = pd.read_csv(T.TABLES / f"co2_experiments{suffix}_skill.csv")
    boot = pd.read_csv(T.TABLES / f"co2_experiments{suffix}_cv_bootstrap.csv").set_index(["variant", "station"])
    cv = skill[skill.scope.eq("leave_one_date_out")]
    variants = [v for v in cv.variant.unique()]
    fig = plt.figure(figsize=(7.2, 4.2))
    ax = fig.add_axes([.30, .38, .30, .40]); bx = fig.add_axes([.68, .38, .29, .40])
    y = np.arange(len(variants))
    for k, code in enumerate(("BKT", "JMB")):
        post = [cv[(cv.variant == v) & (cv.station == code) & (cv.model == "posterior")].rmse_ppm.iloc[0] for v in variants]
        plain = [cv[(cv.variant == v) & (cv.station == code) & (cv.model == "plain_background")].rmse_ppm.iloc[0] for v in variants]
        ax.barh(y + (k - .5) * .38, post, .36, color=COLOR[code], label=f"{code} posterior")
        ax.plot(plain, y + (k - .5) * .38, "|", ms=9, color="black", lw=1.2, label="Background only" if k == 0 else None)
        diff = [boot.loc[(v, code), "rmse_difference_ppm"] for v in variants]
        lo = [boot.loc[(v, code), "ci_lo"] for v in variants]; hi = [boot.loc[(v, code), "ci_hi"] for v in variants]
        bx.errorbar(diff, y + (k - .5) * .38, xerr=[np.array(diff) - np.array(lo), np.array(hi) - np.array(diff)],
                    fmt="o", ms=4, color=COLOR[code], capsize=2, lw=1)
    ax.set_yticks(y, [v.replace("_", " ") for v in variants], fontsize=7); ax.invert_yaxis()
    ax.set_xlabel("Leave-one-date-out RMSE (ppm)", fontsize=7.5); ax.tick_params(labelsize=7)
    fig.legend(*ax.get_legend_handles_labels(), fontsize=6.6, frameon=False, ncol=3, loc="lower left", bbox_to_anchor=(.30, .15))
    ax.set_title("(a) Out-of-sample error", fontsize=8, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    bx.axvline(0, color=GREY, lw=.8); bx.set_yticks(y, [""] * len(y)); bx.invert_yaxis()
    bx.set_xlabel("Posterior minus background (ppm)\n95% date-block bootstrap", fontsize=7.5); bx.tick_params(labelsize=7)
    bx.set_title("(b) Difference and its interval", fontsize=8, loc="left")
    bx.spines[["top", "right"]].set_visible(False)
    head(fig, "Out-of-sample skill by model variant",
         "Each date is left out, the model refitted and that date predicted. A bar left of the black marker beats a background of fitted\n"
         "offset and trend; an interval clear of zero in panel (b) resolves the difference against the sampling of the dates, either way.")
    footer(fig, "Source: a91 experiment skill and bootstrap tables. Dates are resampled whole, so hours of one day stay together.")
    export(fig, 3, "scoreboard")


def c04_daytime_only() -> None:
    """Why only the afternoon receptors are usable: night enhancements, mixing depth, the screen."""
    diurnal = pd.read_csv(T.TABLES / "co2_diurnal_summary.csv")
    screen = pd.read_csv(T.TABLES / "co2_mixing_screen.csv", parse_dates=["time_utc"])
    fig = plt.figure(figsize=(7.2, 4.2))
    ax = fig.add_axes([.07, .34, .24, .42])
    x, labels, observed, observed_sd, prior, colors = np.arange(4), [], [], [], [], []
    for code in ("BKT", "JMB"):
        for hour, name in ((6, "13 WIB"), (18, "01 WIB")):
            row = diurnal[diurnal.station.eq(code) & diurnal.hour.eq(hour)].iloc[0]
            labels.append(f"{code}\n{name}"); colors.append(COLOR[code])
            observed.append(row.enhancement_mean); observed_sd.append(row.enhancement_sd); prior.append(row.prior_mean)
    ax.bar(x - .2, observed, .38, yerr=observed_sd, color=colors, capsize=2, error_kw=dict(lw=.8))
    ax.bar(x + .2, prior, .38, color=GREY)
    ax.axhline(0, color="black", lw=.8); ax.set_xticks(x, labels, fontsize=7)
    ax.set_ylabel("CO₂ above background (ppm)", fontsize=7.5); ax.tick_params(labelsize=7)
    ax.set_title("(a) Observed against prior", fontsize=8, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    bx = fig.add_axes([.40, .34, .18, .42])
    for k, code in enumerate(("BKT", "JMB")):
        values = [diurnal[diurnal.station.eq(code) & diurnal.hour.eq(h)].pblh_median.iloc[0] for h in (6, 18)]
        bars = bx.bar(np.arange(2) + (k - .5) * .38, values, .36, color=COLOR[code])
        bx.bar_label(bars, [f"{v:.0f}" for v in values], fontsize=6.3, padding=2, color=MUTED)
    bx.set_xticks(range(2), ["13 WIB", "01 WIB"], fontsize=7); bx.set_yscale("log"); bx.set_ylim(20, 3000)
    bx.set_ylabel("GFS mixing depth, median (m)", fontsize=7.5); bx.tick_params(labelsize=7)
    bx.set_title("(b) Mixing depth", fontsize=8, loc="left")
    bx.spines[["top", "right"]].set_visible(False)
    cx = fig.add_axes([.68, .34, .29, .42])
    for code in ("BKT", "JMB"):
        g = gapped(screen[screen.station.eq(code)], ("pblh_m",))
        cx.plot(g.time_utc, g.pblh_m, "o-", ms=3.5, lw=.9, color=COLOR[code])
    rejected = screen[~screen.well_mixed]
    cx.plot(rejected.time_utc, rejected.pblh_m, "x", ms=7, color="black", mew=1.4)
    cx.axhline(I.MIN_MIXING_DEPTH_M, ls="--", color=GREY, lw=1)
    cx.text(.02, I.MIN_MIXING_DEPTH_M + 70, f"{I.MIN_MIXING_DEPTH_M:.0f} m screen", fontsize=6.3, color=MUTED,
            transform=cx.get_yaxis_transform())
    period_axis(cx, screen); cx.set_ylabel("Mixing depth at 13 WIB (m)", fontsize=7.5)
    cx.set_title("(c) Afternoon receptors, 2023", fontsize=8, loc="left")
    cx.spines[["top", "right"]].set_visible(False)
    keys = [Patch(color=COLOR["BKT"]), Patch(color=COLOR["JMB"]), Patch(color=GREY),
            Line2D([], [], color="black", ls="none", marker="x", ms=6, mew=1.4)]
    fig.legend(keys, ["Bukit Kototabang", "Jambi", "Prior model", "Rejected by the mixing screen"],
               fontsize=6.6, frameon=False, ncol=4, loc="lower left", bbox_to_anchor=(.07, .12))
    night = diurnal[diurnal.hour.eq(18)]
    head(fig, "Night observations sit outside what a 0.25 degree footprint can carry",
         f"At 01 WIB the towers see {night[night.station.eq('BKT')].enhancement_mean.iloc[0]:.0f} and {night[night.station.eq('JMB')].enhancement_mean.iloc[0]:.0f} ppm above background while the prior gives "
         f"{night[night.station.eq('BKT')].prior_mean.iloc[0]:.1f} and {night[night.station.eq('JMB')].prior_mean.iloc[0]:.1f} ppm, because the GFS\n"
         f"mixing depth collapses to about {night.pblh_median.mean():.0f} m and a 0.25 degree footprint cannot resolve the shallow layer the air actually\n"
         "occupies. The inversion therefore uses 12-14 WIB means only.")
    footer(fig, "Sources: a89 diurnal summary, a90 mixing screen. Error bars are one standard deviation across hours in that group.")
    export(fig, 4, "daytime_only")


def c05_height_and_proxy(suffix: str = "_round5b") -> None:
    """Release height sensitivity at BKT and the CH4 enhancement proxy used for 2024."""
    height = pd.read_csv(T.TABLES / "co2_bkt_height_operator.csv", parse_dates=["time_utc"])
    base = pd.read_csv(T.TABLES / "co2_operator_base.csv", parse_dates=["time_utc"])
    diag = pd.read_csv(T.TABLES / "co2_diagnostic_operator.csv", parse_dates=["time_utc"])
    skill = pd.read_csv(T.TABLES / f"co2_experiments{suffix}_skill.csv")
    boot = pd.read_csv(T.TABLES / f"co2_experiments{suffix}_cv_bootstrap.csv")
    points = pd.read_csv(T.TABLES / "co2_ch4_proxy_points.csv", parse_dates=["time_utc"])
    validation = pd.read_csv(T.TABLES / "co2_ch4_proxy_validation.csv").set_index("station")
    stamps = sorted(height.time_utc.unique())
    at100 = (base[base.station.eq("BKT") & base.time_utc.isin(stamps)].set_index("time_utc")
             .join(diag[diag.station.eq("BKT")].set_index("time_utc")[["gpp_ppm", "resp_ppm"]]))
    fig = plt.figure(figsize=(7.2, 4.2))
    ax = fig.add_axes([.08, .34, .23, .42])
    series = {150: height[height.release_height_m.eq(150)].set_index("time_utc"),
              300: height[height.release_height_m.eq(300)].set_index("time_utc")}
    components = (("sensitivity", GREY, "Total footprint"), ("gpp_ppm", GREEN, "Gross uptake"),
                  ("resp_ppm", PURPLE, "Respiration"), ("fossil_near_ppm", BLUE, "Fossil within 500 km"))
    for k, (name, color, label) in enumerate(components):
        offset = (k - 1.5) * 6
        medians, spread = [], [[], []]
        for h in (150, 300):
            change = (series[h][name] - at100[name]) / at100[name].abs() * 100
            medians.append(change.median())
            spread[0].append(change.median() - change.quantile(.25)); spread[1].append(change.quantile(.75) - change.median())
        ax.errorbar([150 + offset, 300 + offset], medians, yerr=spread, fmt="-o", ms=4, lw=1.1, color=color, capsize=2, label=label)
    ax.axhline(0, color="black", lw=.8); ax.set_xticks((150, 300), ["150 m", "300 m"], fontsize=7)
    ax.set_xlabel("BKT release height above model ground", fontsize=7.5)
    ax.set_ylabel("Change from the 100 m release (%)", fontsize=7.5); ax.tick_params(labelsize=7)
    fig.legend(*ax.get_legend_handles_labels(), fontsize=6.6, frameon=False, ncol=4, loc="lower left", bbox_to_anchor=(.08, .12))
    ax.set_title("(a) Response by release height", fontsize=8, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    bx = fig.add_axes([.41, .34, .21, .42])
    cases = [("best_100", "100 m"), ("best_h150", "150 m"), ("best_h300", "300 m")]
    cv = skill[skill.scope.eq("leave_one_date_out") & skill.station.eq("BKT")]
    post = [cv[cv.variant.eq(v) & cv.model.eq("posterior")].rmse_ppm.iloc[0] for v, _ in cases]
    plain = [cv[cv.variant.eq(v) & cv.model.eq("plain_background")].rmse_ppm.iloc[0] for v, _ in cases]
    bars = bx.bar(np.arange(3), post, .5, color=BLUE)
    bx.bar_label(bars, [f"{v:.2f}" for v in post], fontsize=6.3, padding=2, color=MUTED)
    bx.plot(np.arange(3), plain, "|", ms=16, color="black", mew=1.4)
    bx.annotate("background only", (2.3, plain[2]), fontsize=6.3, color=MUTED, va="center", ha="left")
    bx.set_xticks(range(3), [label for _, label in cases], fontsize=7)
    bx.set_ylim(0, max(post) * 1.25); bx.set_xlim(-.7, 3.5)
    bx.set_ylabel("BKT leave-one-date-out RMSE (ppm)", fontsize=7.5); bx.tick_params(labelsize=7)
    bx.set_title("(b) Skill by height", fontsize=8, loc="left")
    bx.spines[["top", "right"]].set_visible(False)
    cx = fig.add_axes([.72, .34, .25, .42])
    for code in ("BKT", "JMB"):
        g = points[points.station.eq(code)]
        cx.plot(g.proxy_ppb, g.modelled_ppb, "o", ms=3.5, color=COLOR[code], alpha=.85,
                label=f"{code}, ρ = {validation.loc[code, 'spearman']:.2f} (n = {validation.loc[code, 'n']:.0f})")
    limits = [min(points.proxy_ppb.min(), points.modelled_ppb.min()) - 20, max(points.proxy_ppb.max(), points.modelled_ppb.max()) + 20]
    cx.plot(limits, limits, "--", color=GREY, lw=.9); cx.set_xlim(limits); cx.set_ylim(limits)
    cx.set_xlabel("CH₄ proxy: above rolling baseline (ppb)", fontsize=7.5)
    cx.set_ylabel("CH₄ enhancement from the\nboundary field (ppb)", fontsize=7.5); cx.tick_params(labelsize=7)
    cx.legend(fontsize=6.3, frameon=False, loc="upper left"); cx.set_title("(c) The CH₄ covariate on 2023", fontsize=8, loc="left")
    cx.spines[["top", "right"]].set_visible(False)
    difference = boot[boot.variant.isin([v for v, _ in cases]) & boot.station.eq("BKT")]
    head(fig, "Release height moves the BKT response a few percent and the skill not at all",
         f"Paired differences over the {len(stamps)} afternoon receptors, medians with interquartile ranges. Lifting the release from 100 m to the\n"
         f"true inlet altitude (150 m above GFS terrain) and then to 300 m leaves the out-of-sample error within {difference.rmse_difference_ppm.abs().max():.1f} ppm, with every\n"
         "bootstrap interval spanning zero. Panel (c) checks the CH₄ proxy that stands in for the missing 2024 boundary field.")
    footer(fig, "Sources: a92 release-height operator, a89 and a90 operators at 100 m, a91 skill and bootstrap tables, a93 proxy validation.")
    export(fig, 5, "height_and_proxy")


FIGURES = (c01_series, c02_biosphere_priors, c03_scoreboard, c04_daytime_only, c05_height_and_proxy)

if __name__ == "__main__":
    apply_chart_style()
    for figure in FIGURES:
        figure(); print(figure.__name__, flush=True)
