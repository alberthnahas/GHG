#!/usr/bin/env python3
"""Maps for the operational inversion report.

A tower inversion is a spatial argument. Where the air came from, which land it
crossed, where the inventory was rescaled and which provinces the network can
constrain are all claims about position, and a table cannot carry them.

  M01  mean surface footprint at each tower, with the provinces it crosses
  M02  what localising the methane inventory changed, and where
  M03  the land-use proxy: drained peat and fire over peat
  M04  the share of each tower's methane signal each province carries
  M05  where the peatland methane reaching Jambi comes from
  M06  districts carrying the signal, against the sensitivity that sees them

Everything is drawn from the spatial operator files, which already hold the
seed-mean time-summed footprint and the gridded prior contribution of every
component at every receptor, so no footprint is re-read here.

Context layers are the shared Indonesian assets: the 38-province boundary for
the study area and the high-resolution world layer outside it. Geographic
coordinates are used because the claim is about position on the archipelago, and
no distance is read off these maps.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, TwoSlopeNorm
import numpy as np
import pandas as pd
import xarray as xr

import a84_bkt_jmb_two_receptor as T
import a110_attribution as A

ASSETS = Path("/run/media/workstation-llm/HDD2/.assets")
OUT = T.ROOT / "outputs/operational/figures"
INVENTORY = T.ROOT / "outputs/inventory"
LAND, STUDY, WATER = "#D2D2D2", "#F7F7F5", "#FFFFFF"
BOUNDARY, FOCAL, MUTED, MARK = "#4A4A4A", "#1A1A1A", "#6B6B6B", "#D55E00"
TRANSPORT = (92., 126., -12., 8.)        # the domain the 120-hour footprints actually reach
ARCHIPELAGO = (94., 142., -12., 8.)
WESTERN = (94., 120., -8., 7.)           # Sumatra, Kalimantan and Java, where the peat is
SUMATRA = (94.5, 108., -7., 7.)
_CACHE: dict[str, object] = {}


def canvas(extent, title: str, subtitle: str, note: str, panels: int = 1, width: float = 10.0,
           colorbar: bool = True):
    """A figure whose panel boxes already have the map's aspect ratio.

    Laying the panels out in inches rather than in figure fractions is what keeps
    an equal-aspect map from leaving a band of white space: the box is built to
    the shape the data needs instead of the data being fitted into a box chosen
    first. The note is wrapped before the figure exists, so its height is part of
    the layout and a long caveat cannot run off the bottom edge.
    """
    import textwrap
    ratio = (extent[1] - extent[0]) / (extent[3] - extent[2])
    left, right, gap = .78, .30, .40
    panel_w = (width - left - right - gap * (panels - 1)) / panels
    panel_h = panel_w / ratio
    wrapped = textwrap.fill(note, width=int((width - left - right) * 15.5))
    top, bar = 1.05, (.80 if colorbar else .18)
    note_in = .30 + .125 * (wrapped.count("\n") + 1)
    height = top + panel_h + bar + note_in
    fig = plt.figure(figsize=(width, height))
    axes = [fig.add_axes([(left + k * (panel_w + gap)) / width, (note_in + bar) / height,
                          panel_w / width, panel_h / height]) for k in range(panels)]
    y = (note_in + .34) / height
    if colorbar == "each":
        cax = [fig.add_axes([ax.get_position().x0, y, ax.get_position().width, .17 / height]) for ax in axes]
    elif colorbar:
        cax = fig.add_axes([left / width, y, (width - left - right) / width, .17 / height])
    else:
        cax = None
    x = left / width
    fig.text(x, 1 - .28 / height, title, fontsize=12.5, weight="bold", va="top", color=FOCAL)
    fig.text(x, 1 - .60 / height, subtitle, fontsize=8.4, va="top", color=MUTED)
    fig.text(x, (note_in - .16) / height, wrapped, fontsize=6.7, color=MUTED, va="top", linespacing=1.45)
    return fig, axes, cax


def layer(name: str):
    """A shared context layer, with self-intersecting rings repaired in memory.

    Five of the 38 province polygons and two districts are invalid as stored. An
    invalid ring renders as a wedge of fill reaching far outside the polygon,
    which on these maps appeared as pale streaks across the Malay Peninsula. The
    repair is in memory only: the shared assets are not rewritten, and the count
    is printed so the fix stays visible rather than silent.
    """
    import geopandas as gpd
    if name not in _CACHE:
        path = {"world": ASSETS / "world_without_idn.shp",
                "provinces": ASSETS / "indonesia_38prov.geojson",
                "districts": ASSETS / "indonesia_kabkota_38prov.geojson"}[name]
        frame = gpd.read_file(path)
        broken = int((~frame.is_valid).sum())
        if broken:
            frame = frame.assign(geometry=frame.geometry.make_valid())
            print(f"  repaired {broken} invalid geometries in {path.name} (in memory only)", flush=True)
        _CACHE[name] = frame
    return _CACHE[name]


def context(ax, extent=ARCHIPELAGO, provinces=True):
    """Quiet base: neighbouring land grey, study area off-white, boundaries thin."""
    ax.set_facecolor(WATER)
    layer("world").plot(ax=ax, facecolor=LAND, edgecolor="#B5B5B5", linewidth=.3, zorder=1, rasterized=True)
    if provinces:
        layer("provinces").plot(ax=ax, facecolor=STUDY, edgecolor=BOUNDARY, linewidth=.35, zorder=2, rasterized=True)
    ax.set_xlim(extent[0], extent[1]); ax.set_ylim(extent[2], extent[3])
    step = 10 if extent[1] - extent[0] > 25 else 4
    ax.set_xticks(np.arange(np.ceil(extent[0] / step) * step, extent[1] + .01, step))
    ax.set_yticks(np.arange(np.ceil(extent[2] / (step / 2)) * (step / 2), extent[3] + .01, step / 2))
    ax.set_xticklabels([f"{v:.0f}°E" for v in ax.get_xticks()], fontsize=7)
    ax.set_yticklabels([f"{abs(v):.0f}°{'N' if v >= 0 else 'S'}" for v in ax.get_yticks()], fontsize=7)
    ax.grid(True, linestyle=":", linewidth=.35, color="#C9C9C9", zorder=3)
    for spine in ax.spines.values():
        spine.set_linewidth(.6); spine.set_color(BOUNDARY)
    ax.set_aspect("equal", adjustable="box")


def towers(ax, labels=True, only=None):
    for code in ("BKT", "JMB"):
        if only and code != only:
            continue
        name, lat, lon, _ = T.STATIONS[code]
        ax.plot(lon, lat, marker="^", ms=7, color=MARK, markeredgecolor="white",
                markeredgewidth=.8, zorder=12, linestyle="none")
        if labels:
            ax.annotate(name, (lon, lat), xytext=(7, 4), textcoords="offset points",
                        fontsize=7.5, weight="bold", color=FOCAL, zorder=12,
                        path_effects=[pe.withStroke(linewidth=2.2, foreground="white")])


def panel_note(ax, text: str):
    ax.text(.982, .028, text, transform=ax.transAxes, fontsize=6.8, family="monospace",
            ha="right", va="bottom", zorder=13,
            bbox=dict(boxstyle="round,pad=0.32", facecolor="#FFFDF5", edgecolor="#D8D3C4", linewidth=.5))


def title_of(ax, index: int, text: str):
    ax.set_title(f"({'abcd'[index]}) {text}", fontsize=8.8, loc="left", color=FOCAL, pad=4)


def colorbar(fig, cax, mesh, label: str, **kwargs):
    from matplotlib.ticker import LogFormatterSciNotation, LogLocator
    bar = fig.colorbar(mesh, cax=cax, orientation="horizontal", **kwargs)
    bar.set_label(label, fontsize=7.4, labelpad=2)
    bar.ax.tick_params(labelsize=6.8, length=2.5, pad=1.5)
    bar.ax.tick_params(which="minor", labelsize=6.0, length=1.5)
    if getattr(bar.norm, "vmin", None) and bar.ax.get_xscale() == "log":
        # a range under one decade labels every minor tick and the labels collide
        bar.ax.xaxis.set_minor_locator(LogLocator(base=10., subs=(2., 5.)))
        bar.ax.xaxis.set_minor_formatter(LogFormatterSciNotation(minor_thresholds=(2., .6)))
    return bar


def save(fig, number: int, stem: str):
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"map_M{number:02d}_{stem}.{ext}", dpi=300, facecolor="white")
    plt.close(fig)
    print(f"  -> outputs/operational/figures/map_M{number:02d}_{stem}.png", flush=True)


# ------------------------------------------------------- the spatial operator

def operator(code: str):
    """Screened receptors of one station: mean footprint, mean component fields, grid."""
    keep = A.screened()
    with A.spatial(code) as ds:
        index = A.receptor_selection(ds, code, keep)
        lat, lon = ds.lat.values, ds.lon.values
        footprint = ds.footprint.isel(receptor=index).values.mean(axis=0)
        parts = {str(c): ds.prior_contribution.isel(receptor=index).sel(component=c).values.mean(axis=0)
                 for c in ds.component.values}
    return footprint, parts, lat, lon, len(index)


def m01_footprints():
    fig, axes, cax = canvas(TRANSPORT, "Where the towers see",
          "Mean 120-hour HYSPLIT-STILT surface footprint over the screened receptors, November to December 2023",
          "Cells below the 60th percentile of positive sensitivity are masked so the pattern stays readable, and each panel states "
          "how much of the sensitivity the coloured area carries. Both towers draw on the same two arms, one reaching southeast "
          "along the Sumatran coast toward Java and the Indian Ocean and one northeast across the Malacca Strait, which is why "
          "their signals are correlated and why the second tower adds less than its distance from the first would suggest. A "
          "footprint is transport sensitivity, not emission and not attribution. Geographic coordinates on "
          "WGS84; context from the shared 38-province layer and the high-resolution world layer.",
                            panels=2, width=10.4)
    for k, (ax, code) in enumerate(zip(axes, ("BKT", "JMB"))):
        footprint, _, lat, lon, used = operator(code)
        context(ax, TRANSPORT)
        positive = footprint[footprint > 0]
        floor = float(np.percentile(positive, 60))
        mesh = ax.pcolormesh(lon, lat, np.ma.masked_where(footprint <= floor, footprint),
                             norm=LogNorm(vmin=floor, vmax=float(footprint.max())),
                             cmap="magma_r", shading="nearest", zorder=5, rasterized=True, alpha=.9)
        towers(ax, only=code)
        share = footprint[footprint > floor].sum() / footprint.sum()
        panel_note(ax, f"{used} receptors\n{100 * share:.0f}% of sensitivity shown")
        title_of(ax, k, T.STATIONS[code][0])
    colorbar(fig, cax, mesh, "mean surface sensitivity (ppm per \u00b5mol m\u207b\u00b2 s\u207b\u00b9), logarithmic")
    save(fig, 1, "footprints")


def m02_inventory_change():
    with xr.open_dataset(INVENTORY / "local_inventory_ch4_2022_provincial.nc") as ds:
        local = sum(ds[v].values for v in ds.data_vars if not v.startswith("FOLU_"))
        lat, lon = ds.lat.values, ds.lon.values
    reference = A.edgar_total("CH4", 2022, lat, lon)
    # only cells the localisation could act on are comparable. Outside Indonesia the
    # localised field is the global one unchanged, so the ratio is one by construction,
    # and leaving it drawn put EDGAR's shipping lanes across the Malacca Strait on the
    # map as apparent agreement
    inside = np.zeros((len(lat), len(lon)), dtype=bool)
    for mask in A.region_masks(lat, lon, ASSETS / "indonesia_38prov.geojson",
                               ("provinsi", "PROVINSI", "name")).values():
        inside |= mask
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(inside & (reference > reference.max() * 1e-6), local / reference, np.nan)
    fig, axes, cax = canvas(ARCHIPELAGO, "Where the reported inventory disagrees with the global one",
          "Indonesian methane, 2022: national totals reported to the UNFCCC, allocated to provinces by facility location",
          "Blue is where the country reports less than the global inventory assumes, red where it reports more, white is agreement. "
          "The scale diverges about one and is clipped at three. Cells with negligible global emission are masked. Within a province "
          "the gridded pattern is unchanged and only its magnitude is set by the reported total, so provincial boundaries are "
          "visible by construction and are not themselves a result. Only cells whose centre falls inside a province are drawn, "
          "because outside Indonesia the localised field is the global one unchanged and the ratio would be one by "
          "construction. The deep blue across Sumatra and Kalimantan is the fugitive sector, which the country reports at a "
          "ninth of the global inventory's figure.",
                            panels=1, width=10.0)
    ax = axes[0]
    context(ax, ARCHIPELAGO)
    mesh = ax.pcolormesh(lon, lat, np.ma.masked_invalid(ratio),
                         norm=TwoSlopeNorm(vmin=0., vcenter=1., vmax=3.),
                         cmap="RdBu_r", shading="nearest", zorder=5, rasterized=True, alpha=.95)
    towers(ax)
    colorbar(fig, cax, mesh, "reported provincial inventory divided by the global gridded inventory",
             extend="max", ticks=[0, .5, 1, 2, 3])
    save(fig, 2, "inventory_change")


def m03_folu():
    with xr.open_dataset(INVENTORY / "folu_proxy_indonesia.nc") as ds:
        fields = {"drained peat": ds.peat_drainage.values, "fire over peat": ds.peat_fire.values}
        peat = ds.peat.values.astype(bool)
        lat, lon = ds.lat.values, ds.lon.values
    fig, axes, caxes = canvas(WESTERN, "The land-use term the global inventory does not carry",
          f"Peat drainage weighted by land cover, and burned carbon over peat; {int(peat.sum())} peat cells at a quarter degree",
          "A pattern, not a flux: the magnitude comes from the reported national total, because published drained-peat emission "
          "factors span a factor of ten (Murdiyarso and others, PNAS 2024, 8.13 to 80.77 Mg CO₂ per hectare per year). Peat extent "
          "from the Indonesian peatland layer, land cover from MODIS MCD12C1, burned carbon from GFED 5.1. A cell counts as peat "
          "when its centre falls inside the peatland polygon, which under-resolves narrow coastal domes. Drainage and fire do not "
          "coincide: the eastern Sumatran and Kalimantan lowlands carry the drainage, while the fire pattern is patchier and "
          "follows the burning year.",
                              panels=2, width=10.4, colorbar="each")
    for k, (ax, (label, values)) in enumerate(zip(axes, fields.items())):
        context(ax, WESTERN)
        positive = values[values > 0]
        mesh = ax.pcolormesh(lon, lat, np.ma.masked_where(values <= 0, values),
                             norm=LogNorm(vmin=max(float(positive.min()), float(positive.max()) * 1e-4),
                                          vmax=float(positive.max())),
                             cmap="YlOrBr" if k == 0 else "OrRd", shading="nearest", zorder=5, rasterized=True)
        colorbar(fig, caxes[k], mesh, f"share of the national {label} total, logarithmic")
        towers(ax, labels=False)
        panel_note(ax, f"{int((values > 0).sum())} emitting cells")
        title_of(ax, k, label)
    save(fig, 3, "folu_proxy")


def m04_province_influence():
    table = pd.read_csv(T.ROOT / "outputs/operational/attribution_provinces.csv")
    provinces = layer("provinces")
    column = next(c for c in ("provinsi", "PROVINSI", "name") if c in provinces.columns)
    fig, axes, cax = canvas(SUMATRA, "Which provinces the towers can constrain",
          "Provincial emission weighted by the mean footprint, methane, anthropogenic and natural terms together",
          "This is why the inventory is allocated provincially rather than nationally: a national factor corrects everywhere, and "
          "between them these two towers draw almost all of their modelled signal from four provinces. Sumatra is shown because no "
          "province outside it reaches one percent at either tower. The towers are not redundant but they are not independent "
          "either: Bukit Kototabang draws almost three quarters of its signal from its own province, while Jambi spreads across "
          "Jambi, South Sumatra and Riau, and Riau is common to both. Neither sees Java, Kalimantan or anything east of them.",
                            panels=2, width=8.6)
    for k, (ax, code) in enumerate(zip(axes, ("BKT", "JMB"))):
        share = table[table.station.eq(code)].set_index("region").share_percent
        merged = provinces.assign(percent=provinces[column].map(share))
        context(ax, SUMATRA)
        merged[merged.percent.notna()].plot(ax=ax, column="percent", cmap="YlGnBu", vmin=0, vmax=75,
                                            edgecolor=BOUNDARY, linewidth=.4, zorder=6, rasterized=True)
        towers(ax, labels=False)
        panel_note(ax, "\n".join(f"{n.title():<17s}{v:5.1f}%" for n, v in share.nlargest(4).items()))
        title_of(ax, k, T.STATIONS[code][0])
    colorbar(fig, cax, plt.cm.ScalarMappable(norm=plt.Normalize(0, 75), cmap="YlGnBu"),
             "share of the tower's modelled methane source signal (%)", extend="max")
    save(fig, 4, "province_influence")


def m05_peat_signal():
    """Where the peatland methane arriving at Jambi is emitted."""
    footprint, parts, lat, lon, used = operator("JMB")
    peat = A.peat_on(lat, lon)
    signal = parts["anthro_near"] + parts["anthro_far"] + parts["wetlands"] + parts["fire"]
    on_peat = np.where(peat & (signal > 0), signal, np.nan)
    fig, axes, caxes = canvas(SUMATRA, "Peatland carries a quarter of the methane arriving at Jambi",
          f"Screened afternoon receptors, {used} at Jambi, with the global gridded inventory and the LPJ wetland prior",
          "Three routes are separated because they are three processes with three different answers: biological emission from peat "
          "swamp, which the wetland prior carries; fire over peat; and anthropogenic emission sitting on drained peatland, mostly "
          "agriculture and waste. Indonesia reports no methane from drained organic soils, so that route reaches the model through "
          "the inventory and the wetland term rather than through a land-use category. A prior contribution is what the model says "
          "should arrive, not a measured flux.",
                              panels=2, width=9.2, colorbar="each")
    fig.delaxes(caxes[1])
    cax = caxes[0]
    ax = axes[0]
    context(ax, SUMATRA)
    positive = on_peat[np.isfinite(on_peat)]
    mesh = ax.pcolormesh(lon, lat, np.ma.masked_invalid(on_peat),
                         norm=LogNorm(vmin=float(np.percentile(positive, 20)), vmax=float(positive.max())),
                         cmap="viridis_r", shading="nearest", zorder=5, rasterized=True)
    towers(ax, labels=False)
    colorbar(fig, cax, mesh, "methane from this cell, emitted on peat (ppb), logarithmic")
    title_of(ax, 0, "Emitted on peat, as seen at Jambi")
    panel_note(ax, f"{np.nansum(on_peat):5.1f} ppb on peat\n{signal.sum():5.1f} ppb in total")

    routes = pd.read_csv(T.ROOT / "outputs/operational/attribution_peat.csv")
    block = routes[routes.station.eq("JMB") & ~routes.quantity.str.contains("peat routes|footprint")]
    ax = axes[1]
    order = block.sort_values("over_peat_mean", ascending=True)
    y = np.arange(len(order))
    ax.barh(y, order.total_mean, .6, color="#C9D6D2", zorder=2)
    ax.barh(y, order.over_peat_mean, .6, color="#2C7C68", zorder=3)
    for k, row in enumerate(order.itertuples()):
        ax.text(row.total_mean * 1.15, k, f"{row.peat_share_percent:.0f}% on peat", fontsize=6.6,
                va="center", color=MUTED)
    labels = {"anthropogenic": "inventory", "wetlands": "wetland", "fire": "fire",
              "FOLU_land_use_fire": "land-use fire"}
    ax.set_yticks(y, [labels.get(q, q) for q in order.quantity], fontsize=7.4)
    ax.set_xlabel("mean contribution at Jambi (ppb)", fontsize=7.4, labelpad=2)
    ax.set_xscale("log"); ax.set_xlim(.05, 900); ax.tick_params(labelsize=6.8)
    ax.spines[["top", "right"]].set_visible(False)
    title_of(ax, 1, "Peat and total, by route")
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=c, label=l) for c, l in
                       (("#2C7C68", "emitted on peat"), ("#C9D6D2", "all land"))],
              fontsize=6.5, frameon=False, loc="lower right")
    save(fig, 5, "peat_signal")


def m06_districts():
    table = pd.read_csv(T.ROOT / "outputs/operational/attribution_districts.csv")
    districts = layer("districts")
    column = next(c for c in ("kabupaten", "kabkota", "KABKOT", "name") if c in districts.columns)
    fig, axes, cax = canvas(SUMATRA, "The signal is concentrated in a handful of districts",
          "District emission weighted by the mean footprint, methane, 2022 global gridded inventory",
          "Districts are shown because the concentration is the point, not because the inversion resolves them: a quarter-degree "
          "footprint cell is larger than most Indonesian districts, so these shares attribute the prior and do not estimate "
          "emission per district. Muara Enim carries 8% of the Bukit Kototabang signal from 0.02% of its footprint sensitivity, "
          "which says how concentrated the gridded inventory is in the South Sumatran coal basin, and where an error in it would "
          "matter most to these towers.",
                            panels=2, width=8.6)
    for k, (ax, code) in enumerate(zip(axes, ("BKT", "JMB"))):
        share = table[table.station.eq(code)].set_index("region").share_percent
        merged = districts.assign(percent=districts[column].map(share))
        context(ax, SUMATRA, provinces=False)
        layer("provinces").plot(ax=ax, facecolor=STUDY, edgecolor="none", zorder=2, rasterized=True)
        merged[merged.percent.notna()].plot(ax=ax, column="percent", cmap="YlOrRd", vmin=0, vmax=15,
                                            edgecolor="#9A9A9A", linewidth=.15, zorder=6, rasterized=True)
        layer("provinces").boundary.plot(ax=ax, edgecolor=BOUNDARY, linewidth=.45, zorder=8)
        towers(ax, labels=False)
        panel_note(ax, "\n".join(f"{n.title():<16s}{v:5.1f}%" for n, v in share.nlargest(4).items()))
        title_of(ax, k, T.STATIONS[code][0])
    colorbar(fig, cax, plt.cm.ScalarMappable(norm=plt.Normalize(0, 15), cmap="YlOrRd"),
             "share of the tower's modelled methane source signal (%)", extend="max")
    save(fig, 6, "districts")


MAPS = {"footprints": m01_footprints, "inventory": m02_inventory_change, "folu": m03_folu,
        "provinces": m04_province_influence, "peat": m05_peat_signal, "districts": m06_districts}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("maps", nargs="*", choices=sorted(MAPS), default=[])
    chosen = parser.parse_args().maps
    for name in (chosen or MAPS):
        print(f"== {name}", flush=True)
        MAPS[name]()
