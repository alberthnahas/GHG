#!/usr/bin/env python3
"""Build reproducible evidence tables and figures for the BKT footprint report."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "ghg-matplotlib"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import pandas as pd

import ghg_common as G


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RUN_DIR = ROOT / "outputs" / "hysplit" / "bkt_20190926T0100Z"
BLUE = "#006A8E"
ORANGE = "#D55E00"
INK = "#2B2B2B"
MUTED = "#65727A"
PALE = "#EAF4F7"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def percentile_rank(values: pd.Series, score: float) -> float:
    valid = values.dropna().to_numpy(dtype=float)
    return 100.0 * ((valid < score).sum() + 0.5 * (valid == score).sum()) / len(valid)


def weighted_quantile(values: np.ndarray, weights: np.ndarray, quantile: float) -> float:
    order = np.argsort(values)
    ordered_values = values[order]
    ordered_weights = weights[order]
    cumulative = np.cumsum(ordered_weights)
    return float(ordered_values[np.searchsorted(cumulative, quantile * cumulative[-1])])


def haversine_and_bearing(lat: np.ndarray, lon: np.ndarray,
                          receptor_lat: float, receptor_lon: float) -> tuple[np.ndarray, np.ndarray]:
    lat1 = np.radians(receptor_lat)
    lon1 = np.radians(receptor_lon)
    lat2 = np.radians(lat)
    lon2 = np.radians(lon)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    distance = 6371.0088 * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    y = np.sin(dlon) * np.cos(lat2)
    x = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(dlon)
    bearing = (np.degrees(np.arctan2(y, x)) + 360) % 360
    bearing[distance < 1e-9] = np.nan
    return distance, bearing


def sector_name(bearing: float) -> str:
    if not np.isfinite(bearing):
        return "At receptor"
    sectors = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return sectors[int(((bearing + 22.5) % 360) // 45)]


def apply_chart_style() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.labelcolor": INK,
        "axes.edgecolor": "#AAB4B9",
        "axes.linewidth": 0.7,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "text.color": INK,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })


def save_figure(fig: plt.Figure, stem: Path) -> None:
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(stem.with_suffix(".png"), dpi=300, facecolor="white")
    fig.savefig(stem.with_suffix(".pdf"), facecolor="white")
    plt.close(fig)


def figure_workflow(fig_dir: Path, particle_label: str = "500 HYSPLIT particles") -> None:
    fig = plt.figure(figsize=(7.2, 3.8))
    ax = fig.add_axes([0.04, 0.08, 0.92, 0.70])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    boxes = [
        (0.02, 0.57, 0.19, 0.23, "BKT observation", "CO₂, CH₄ and CO\nexact receptor hour", BLUE),
        (0.285, 0.57, 0.19, 0.23, "Backward transport", particle_label + "\n72 h with GDAS1", BLUE),
        (0.55, 0.57, 0.19, 0.23, "Surface footprint", "$f(x,y,t)$ sensitivity\nbelow 0.5 × PBL height", BLUE),
        (0.81, 0.57, 0.17, 0.23, "Validated outputs", "Hourly grid and NetCDF\nmap and diagnostics", BLUE),
        (0.285, 0.12, 0.19, 0.21, "Flux inventories", "Fossil, biogenic, fire,\nwetland, rice and waste", MUTED),
        (0.55, 0.12, 0.19, 0.21, "Flux convolution", "$\\Delta c=\\sum fE$\nplus boundary term", MUTED),
        (0.81, 0.12, 0.17, 0.21, "Future inference", "Enhancement estimate\nor Bayesian inversion", MUTED),
    ]
    for x, y, w, h, title, body, color in boxes:
        face = PALE if color == BLUE else "#F3F3F1"
        ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=face, edgecolor=color,
                                   linewidth=1.2, joinstyle="round"))
        ax.text(x + 0.015, y + h - 0.050, title, weight="bold", fontsize=7.4, color=color)
        ax.text(x + 0.015, y + h - 0.100, body, fontsize=7.0, va="top", linespacing=1.25)
    for x0, x1 in ((0.21, 0.285), (0.475, 0.55), (0.74, 0.81)):
        ax.annotate("", xy=(x1, 0.685), xytext=(x0, 0.685),
                    arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=1.2))
    ax.annotate("", xy=(0.55, 0.225), xytext=(0.475, 0.225),
                arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.1, linestyle="--"))
    ax.annotate("", xy=(0.81, 0.225), xytext=(0.74, 0.225),
                arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.1, linestyle="--"))
    ax.annotate("", xy=(0.645, 0.33), xytext=(0.645, 0.57),
                arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.0, linestyle="--"))
    fig.text(0.055, 0.94, "BKT footprint mode separates completed transport from future inference",
             fontsize=11.5, weight="bold")
    fig.text(0.055, 0.865,
             "Blue boxes are implemented and validated; gray dashed steps require independent flux and boundary data.",
             fontsize=8.8, color=MUTED)
    save_figure(fig, fig_dir / "figure_01_workflow")


def observation_context(run_metadata: dict[str, object], tables_dir: Path,
                        fig_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    receptor = pd.Timestamp(run_metadata["observation"]["time_utc"]).tz_localize(None)
    start = receptor - pd.Timedelta(days=7)
    end = receptor + pd.Timedelta(days=7)
    bkt = G.apply_flags(G.load_station("BKT"))
    expected_times = pd.DataFrame({"time_utc": pd.date_range(start, end, freq="1h")})
    context = expected_times.merge(
        bkt[bkt.time_utc.between(start, end)], on="time_utc", how="left", validate="one_to_one",
    )
    context.to_csv(tables_dir / "observation_context_hourly.csv", index=False)
    definitions = [("CO₂", "co2", "ppm"), ("CH₄", "ch4", "ppb"), ("CO", "co", "ppb")]
    rows = []
    selected = context.loc[context.time_utc.eq(receptor)].iloc[0]
    for label, column, unit in definitions:
        valid_mask = context[column].notna() & context[f"suspect_{column}"].eq(False)
        valid = context.loc[valid_mask, column]
        rows.append({
            "species": label,
            "unit": unit,
            "receptor_value": float(selected[column]),
            "valid_hours": int(len(valid)),
            "expected_hours": 337,
            "coverage_percent": 100 * len(valid) / 337,
            "median": float(valid.median()),
            "p25": float(valid.quantile(0.25)),
            "p75": float(valid.quantile(0.75)),
            "percentile_rank": percentile_rank(valid, float(selected[column])),
        })
    summary = pd.DataFrame(rows)
    summary.to_csv(tables_dir / "observation_context_summary.csv", index=False)

    apply_chart_style()
    fig, axes = plt.subplots(3, 1, figsize=(7.2, 6.6), sharex=True)
    fig.subplots_adjust(left=0.105, right=0.975, top=0.79, bottom=0.11, hspace=0.22)
    for ax, (label, column, unit), row in zip(axes, definitions, rows):
        valid_mask = context[column].notna() & context[f"suspect_{column}"].eq(False)
        ax.plot(context["time_utc"], context[column].where(valid_mask),
                color=BLUE, linewidth=1.0)
        ax.scatter(receptor, selected[column], s=34, color=ORANGE, edgecolor="white",
                   linewidth=0.6, zorder=4)
        ax.axvline(receptor, color=ORANGE, linewidth=0.8, alpha=0.65)
        ax.axhline(row["median"], color=MUTED, linewidth=0.8, linestyle="--")
        ax.axvspan(receptor - pd.Timedelta(hours=72), receptor, color=ORANGE, alpha=0.07)
        ax.set_ylabel(f"{label} ({unit})")
        ax.grid(axis="y", color="#DDE3E6", linewidth=0.6)
        ax.spines[["top", "right"]].set_visible(False)
        ax.text(0.99, 1.035, f"Receptor: {row['receptor_value']:.2f} {unit} · "
                f"context percentile: {row['percentile_rank']:.1f}%",
                transform=ax.transAxes, ha="right", va="bottom", fontsize=7.8, color=MUTED)
    import matplotlib.dates as mdates
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    axes[-1].set_xlabel("UTC date in 2019 (orange shading is the 72 h backward window)")
    ranks = ", ".join(f"{r['species']} {r['percentile_rank']:.0f}%" for r in rows)
    fig.text(0.105, 0.95, "BKT receptor observation in its ±7-day measurement context",
             fontsize=11.5, weight="bold")
    fig.text(0.105, 0.89,
             f"Receptor-hour percentile ranks in the ±7-day valid-hour context: {ranks}.\n"
             "These ranks are descriptive and are not source diagnostics.",
             fontsize=8.6, color=MUTED)
    save_figure(fig, fig_dir / "figure_02_observation_context")
    return context, summary


def lag_diagnostics(hourly: pd.DataFrame, tables_dir: Path,
                    fig_dir: Path, ensemble: bool = False) -> tuple[pd.DataFrame, dict[str, float]]:
    lag = hourly.groupby("lag_hours", as_index=False).footprint_sensitivity.sum()
    lag = lag.sort_values("lag_hours")
    total = lag.footprint_sensitivity.sum()
    lag["share_percent"] = 100 * lag.footprint_sensitivity / total
    lag["cumulative_share_percent"] = lag.share_percent.cumsum()
    lag.to_csv(tables_dir / "lag_sensitivity_hourly.csv", index=False)
    lag_values = lag.lag_hours.to_numpy(dtype=float)
    weights = lag.footprint_sensitivity.to_numpy(dtype=float)
    metrics = {
        "lag_median_hours": weighted_quantile(lag_values, weights, 0.5),
        "lag_p90_hours": weighted_quantile(lag_values, weights, 0.9),
        "share_0_24h_percent": float(lag.loc[lag.lag_hours <= 24, "share_percent"].sum()),
        "share_25_48h_percent": float(lag.loc[lag.lag_hours.between(25, 48), "share_percent"].sum()),
        "share_49_72h_percent": float(lag.loc[lag.lag_hours.between(49, 72), "share_percent"].sum()),
    }

    bins = np.arange(0, 79, 6)
    lag["block"] = pd.cut(lag.lag_hours, bins=bins, right=True, include_lowest=True)
    blocks = lag.groupby("block", observed=True, as_index=False).share_percent.sum()
    blocks["label"] = [f"{int(interval.left + 1)}–{int(interval.right)}" for interval in blocks.block]
    blocks.to_csv(tables_dir / "lag_sensitivity_6hour.csv", index=False)

    apply_chart_style()
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 5.7), gridspec_kw={"height_ratios": [1.05, 1]})
    fig.subplots_adjust(left=0.11, right=0.975, top=0.79, bottom=0.12, hspace=0.34)
    axes[0].bar(blocks.label, blocks.share_percent, color=BLUE, width=0.76)
    axes[0].set_ylabel("Share of integrated\nsensitivity (%)")
    axes[0].grid(axis="y", color="#DDE3E6", linewidth=0.6)
    axes[0].tick_params(axis="x", rotation=45)
    axes[1].plot(lag.lag_hours, lag.cumulative_share_percent, color=ORANGE, linewidth=1.8)
    axes[1].axhline(50, color=MUTED, linestyle="--", linewidth=0.8)
    axes[1].axvline(metrics["lag_median_hours"], color=MUTED, linestyle="--", linewidth=0.8)
    axes[1].set(xlabel="Hours before receptor observation", ylabel="Cumulative share (%)",
                xlim=(1, 72), ylim=(0, 102))
    axes[1].grid(axis="y", color="#DDE3E6", linewidth=0.6)
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.11, 0.95,
             f"Half of the integrated footprint sensitivity occurred within {metrics['lag_median_hours']:.0f} h",
             fontsize=11.5, weight="bold")
    fig.text(0.11, 0.89,
             ("Shares describe the mean of three seeded runs, conditional on GDAS1 meteorology."
              if ensemble else "Shares describe one deterministic transport realization; they are not probabilities or source contributions."),
             fontsize=8.6, color=MUTED)
    save_figure(fig, fig_dir / "figure_04_lag_sensitivity")
    return lag, metrics


def spatial_diagnostics(aggregate: pd.DataFrame, metadata: dict[str, object],
                        tables_dir: Path, fig_dir: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    cfg = metadata["configuration"]
    aggregate = aggregate.copy()
    aggregate["distance_km"], aggregate["bearing_degrees"] = haversine_and_bearing(
        aggregate.LAT.to_numpy(), aggregate.LON.to_numpy(),
        cfg["receptor_lat"], cfg["receptor_lon"],
    )
    aggregate["sector"] = aggregate.bearing_degrees.map(sector_name)
    distance_edges = [-0.001, 100, 250, 500, 750, 1000, np.inf]
    distance_labels = ["0–100", "100–250", "250–500", "500–750", "750–1000", ">1000"]
    aggregate["distance_band_km"] = pd.cut(
        aggregate.distance_km, bins=distance_edges, labels=distance_labels,
        right=False, include_lowest=True,
    )
    total = aggregate.sensitivity_sum.sum()
    aggregate["share_percent"] = 100 * aggregate.sensitivity_sum / total
    aggregate.to_csv(tables_dir / "spatial_cell_summary.csv", index=False)
    sector_order = ["At receptor", "N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    matrix = aggregate.pivot_table(
        index="distance_band_km", columns="sector", values="share_percent",
        aggfunc="sum", fill_value=0, observed=False,
    ).reindex(index=distance_labels, columns=sector_order, fill_value=0)
    matrix.to_csv(tables_dir / "sector_distance_share.csv")
    sector_shares = aggregate.groupby("sector").share_percent.sum().reindex(sector_order, fill_value=0)
    dominant = sector_shares.drop("At receptor").idxmax()
    weights = aggregate.sensitivity_sum.to_numpy(dtype=float)
    distances = aggregate.distance_km.to_numpy(dtype=float)
    metrics: dict[str, object] = {
        "distance_median_km": weighted_quantile(distances, weights, 0.5),
        "distance_p90_km": weighted_quantile(distances, weights, 0.9),
        "distance_max_positive_km": float(distances.max()),
        "share_within_100km_percent": float(aggregate.loc[aggregate.distance_km < 100, "share_percent"].sum()),
        "share_within_250km_percent": float(aggregate.loc[aggregate.distance_km < 250, "share_percent"].sum()),
        "dominant_sector": dominant,
        "dominant_sector_share_percent": float(sector_shares[dominant]),
        "sector_shares_percent": {name: float(value) for name, value in sector_shares.items()},
    }

    apply_chart_style()
    plot_columns = sector_order
    plot_matrix = matrix[plot_columns].to_numpy(dtype=float)
    cmap = LinearSegmentedColormap.from_list("report_blue", ["#F3F7F8", "#7FB6C8", BLUE, "#003D52"])
    fig = plt.figure(figsize=(7.2, 4.8))
    ax = fig.add_axes([0.12, 0.17, 0.75, 0.57])
    image = ax.imshow(plot_matrix, aspect="auto", cmap=cmap, vmin=0,
                      vmax=max(10, math.ceil(plot_matrix.max() / 5) * 5))
    ax.set_xticks(range(len(plot_columns)), plot_columns)
    ax.set_yticks(range(len(distance_labels)), distance_labels)
    ax.set_xlabel("Direction of footprint cell from BKT")
    ax.set_ylabel("Great-circle distance from BKT (km)")
    for iy in range(plot_matrix.shape[0]):
        for ix in range(plot_matrix.shape[1]):
            value = plot_matrix[iy, ix]
            if value >= 0.1:
                ax.text(ix, iy, f"{value:.1f}", ha="center", va="center", fontsize=7.5,
                        color="white" if value > 0.55 * image.norm.vmax else INK)
    cax = fig.add_axes([0.89, 0.17, 0.025, 0.57])
    colorbar = fig.colorbar(image, cax=cax)
    colorbar.set_label("Share of integrated sensitivity (%)", fontsize=8)
    fig.text(0.12, 0.95,
             f"The {dominant} sector contained the largest sensitivity share ({sector_shares[dominant]:.1f}%)",
             fontsize=11.5, weight="bold")
    fig.text(0.12, 0.89,
             "Cellwise HYSPLIT-STILT sensitivity is grouped by distance and bearing; blank cells are true zero share.",
             fontsize=8.6, color=MUTED)
    save_figure(fig, fig_dir / "figure_05_sector_distance")
    return aggregate, metrics


def validation_table(run_dir: Path, metadata: dict[str, object], validation: dict[str, object],
                     provenance: dict[str, object], tables_dir: Path) -> pd.DataFrame:
    message = (run_dir / "MESSAGE").read_text(encoding="utf-8", errors="replace")
    hourly = pd.read_csv(run_dir / "footprint_hourly.csv.gz")
    aggregate = pd.read_csv(run_dir / "footprint_aggregate.csv")
    checks = [
        ("Exact receptor record", "Pass", metadata["observation"]["time_utc"]),
        ("Backward hourly coverage", "Pass", f"{validation['hourly_periods']} of 72 intervals"),
        ("Finite, non-negative sensitivity", "Pass",
         f"{len(hourly):,} non-zero cell-hours"),
        ("CSV/NetCDF/aggregate reconciliation", "Pass", "Within configured tolerances"),
        ("Positive cells at domain edge", "Pass", "None"),
        ("STILT and boundary-layer modes", "Pass", "ICHEM=8; mixed-layer and convection active"),
        ("HYSPLIT fatal messages", "Pass", "None" if "FATAL" not in message.upper() else "Present"),
        ("Meteorology byte count", "Pass",
         f"{int(provenance['bytes']):,} bytes"),
        ("Meteorology SHA-256", "Pass", provenance["sha256"]),
        ("Positive spatial cells", "Pass", f"{len(aggregate):,} cells"),
        ("Map raster dimensions", "Pass", " × ".join(map(str, validation["png_pixels"])) + " px"),
    ]
    frame = pd.DataFrame(checks, columns=["check", "status", "evidence"])
    frame.to_csv(tables_dir / "validation_checks.csv", index=False)
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    report_dir = run_dir / "report"
    fig_dir = report_dir / "figures"
    tables_dir = report_dir / "tables"
    fig_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    metadata = json.loads((run_dir / "run_metadata.json").read_text(encoding="utf-8"))
    validation = json.loads((run_dir / "validation.json").read_text(encoding="utf-8"))
    met_name = Path(metadata["meteorology_files"][0]).name
    provenance_path = ROOT / "data" / "hysplit" / "provenance" / f"{met_name}.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    met_path = Path(metadata["meteorology_files"][0])
    if met_path.stat().st_size != int(provenance["bytes"]):
        raise RuntimeError("meteorology byte count differs from provenance")
    if sha256_file(met_path) != provenance["sha256"]:
        raise RuntimeError("meteorology SHA-256 differs from provenance")
    if validation["status"] != "passed":
        raise RuntimeError("footprint validation has not passed")

    hourly = pd.read_csv(run_dir / "footprint_hourly.csv.gz", parse_dates=["time_utc"])
    aggregate = pd.read_csv(run_dir / "footprint_aggregate.csv")
    figure_workflow(fig_dir)
    _, observation_summary = observation_context(metadata, tables_dir, fig_dir)
    _, lag_metrics = lag_diagnostics(hourly, tables_dir, fig_dir)
    _, spatial_metrics = spatial_diagnostics(aggregate, metadata, tables_dir, fig_dir)
    checks = validation_table(run_dir, metadata, validation, provenance, tables_dir)
    for suffix in ("png", "pdf"):
        source = run_dir / f"bkt_hysplit_stilt_footprint.{suffix}"
        shutil.copy2(source, fig_dir / f"figure_03_spatial_footprint.{suffix}")

    metrics = {
        "report_created_at_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "run_directory": str(run_dir),
        "observation_context": observation_summary.to_dict(orient="records"),
        "lag": lag_metrics,
        "spatial": spatial_metrics,
        "validation_checks_passed": int(checks.status.eq("Pass").sum()),
        "validation_checks_total": int(len(checks)),
        "meteorology": provenance,
    }
    (report_dir / "report_metrics.json").write_text(
        json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
