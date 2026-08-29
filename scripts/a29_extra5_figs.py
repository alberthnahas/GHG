"""Figures 25-26 for the fifth pass (Hovmöller diagrams & transport dynamics)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import griddata

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G
import noaa_flask as nf
import i18n

INK, MUTED = "#1b1f24", "#6b7280"
WARM, COOL, GREY = "#c0392b", "#1f6f8b", "#b8c0c8"


def _tidy(ax):
    ax.tick_params(colors=MUTED, labelsize=8)
    for s in ax.spines.values():
        s.set_color("#d7dbe0")


# --------------------------------------------------------------------- f25 --
def fig25():
    """Figure 25: Latitudinal & Longitudinal Hovmöller diagrams for CO2 and CH4."""
    fig, axes = plt.subplots(1, 3, figsize=(13.6, 4.5),
                             gridspec_kw=dict(wspace=0.30))

    sites = ["brw", "kum", "bkt", "smo", "spo"]
    lats = [nf.SITES[s][1] for s in sites]

    # --- (a) Global CO2 Latitude vs Time Hovmöller
    ax = axes[0]
    dfs = {s: nf.monthly("co2", s) for s in sites}
    idx = dfs["brw"].index
    for s in sites[1:]:
        idx = idx.intersection(dfs[s].index)
    idx = idx[idx >= "2004-01-01"]
    
    t_years = idx.year + (idx.month - 0.5) / 12.0
    pts = []
    vals = []
    for s, lat in zip(sites, lats):
        series = dfs[s].loc[idx].values
        for t, v in zip(t_years, series):
            pts.append((t, lat))
            vals.append(v)
    pts = np.array(pts)
    vals = np.array(vals)

    grid_t, grid_lat = np.meshgrid(np.linspace(2004, 2025, 200), np.linspace(-90, 71.3, 100))
    grid_co2 = griddata(pts, vals, (grid_t, grid_lat), method="linear")

    im1 = ax.contourf(grid_t, grid_lat, grid_co2, levels=14, cmap="viridis", zorder=2)
    cs1 = ax.contour(grid_t, grid_lat, grid_co2, levels=7, colors="white", alpha=0.4, linewidths=0.7, zorder=3)
    ax.clabel(cs1, inline=True, fontsize=7, fmt="%.0f")
    for lat in lats:
        ax.axhline(lat, color="white", lw=0.5, ls="--", alpha=0.3, zorder=4)
    ax.set_yticks(lats)
    ax.set_yticklabels([f"{lat:+.0f}°" for lat in lats], fontsize=8.5)
    ax.set_xlabel(i18n.t("year"), color=MUTED)
    ax.set_ylabel(i18n.t("latitude"), color=MUTED)
    cb1 = fig.colorbar(im1, ax=ax, orientation="horizontal", pad=0.18, aspect=24)
    cb1.set_label(i18n.t("CO$_2$ mixing ratio (ppm)"), fontsize=8, color=MUTED)
    cb1.ax.tick_params(labelsize=7.5, colors=MUTED)
    ax.set_title(i18n.t("a  Global CO$_2$ latitudinal propagation"), loc="left", color=INK, fontsize=10)
    _tidy(ax)

    # --- (b) Global CH4 Latitude vs Time Hovmöller
    ax = axes[1]
    dfs_ch4 = {s: nf.monthly("ch4", s) for s in sites}
    idx_ch4 = dfs_ch4["brw"].index
    for s in sites[1:]:
        idx_ch4 = idx_ch4.intersection(dfs_ch4[s].index)
    idx_ch4 = idx_ch4[idx_ch4 >= "2004-01-01"]
    t_years_ch4 = idx_ch4.year + (idx_ch4.month - 0.5) / 12.0

    pts_ch4, vals_ch4 = [], []
    for s, lat in zip(sites, lats):
        series = dfs_ch4[s].loc[idx_ch4].values
        for t, v in zip(t_years_ch4, series):
            pts_ch4.append((t, lat))
            vals_ch4.append(v)
    pts_ch4 = np.array(pts_ch4)
    vals_ch4 = np.array(vals_ch4)
    grid_ch4 = griddata(pts_ch4, vals_ch4, (grid_t, grid_lat), method="linear")

    im2 = ax.contourf(grid_t, grid_lat, grid_ch4, levels=14, cmap="magma", zorder=2)
    cs2 = ax.contour(grid_t, grid_lat, grid_ch4, levels=7, colors="white", alpha=0.4, linewidths=0.7, zorder=3)
    ax.clabel(cs2, inline=True, fontsize=7, fmt="%.0f")
    for lat in lats:
        ax.axhline(lat, color="white", lw=0.5, ls="--", alpha=0.3, zorder=4)
    ax.set_yticks(lats)
    ax.set_yticklabels([f"{lat:+.0f}°" for lat in lats], fontsize=8.5)
    ax.set_xlabel(i18n.t("year"), color=MUTED)
    cb2 = fig.colorbar(im2, ax=ax, orientation="horizontal", pad=0.18, aspect=24)
    cb2.set_label(i18n.t("CH$_4$ mixing ratio (ppb)"), fontsize=8, color=MUTED)
    cb2.ax.tick_params(labelsize=7.5, colors=MUTED)
    ax.set_title(i18n.t("b  Global CH$_4$ gradient & post-2014 surge"), loc="left", color=INK, fontsize=10)
    _tidy(ax)

    # --- (c) Maritime Continent Longitude vs Month Hovmöller
    ax = axes[2]
    df_all = G.load_all()
    st_order = ["BKT", "JMB", "KMY", "PLU", "SRG"]
    lons = [G.STATIONS[st][3] for st in st_order]
    
    pts_lon, vals_lon = [], []
    for st, lon in zip(st_order, lons):
        d = df_all[df_all.station == st]
        d_aft = d[(d.time_local.dt.hour >= 12) & (d.time_local.dt.hour <= 16)]
        mon_q20 = d_aft.groupby(d_aft.time_local.dt.month)["ch4"].quantile(0.20)
        # Normalize relative to annual median
        norm_val = mon_q20 - mon_q20.median()
        for m, v in norm_val.items():
            pts_lon.append((m, lon))
            vals_lon.append(v)
            # duplicate month 1 and 12 for wrapping
            pts_lon.append((m - 12, lon))
            vals_lon.append(v)
            pts_lon.append((m + 12, lon))
            vals_lon.append(v)

    grid_m, grid_lons = np.meshgrid(np.linspace(1, 12, 100), np.linspace(100.3, 131.3, 80))
    grid_reg = griddata(np.array(pts_lon), np.array(vals_lon), (grid_m, grid_lons), method="cubic")

    im3 = ax.contourf(grid_m, grid_lons, grid_reg, levels=12, cmap="PuOr_r", zorder=2)
    cs3 = ax.contour(grid_m, grid_lons, grid_reg, levels=6, colors="black", alpha=0.3, linewidths=0.7, zorder=3)
    ax.clabel(cs3, inline=True, fontsize=7, fmt="%+.0f")
    for lon in lons:
        ax.axhline(lon, color="grey", lw=0.5, ls=":", alpha=0.5, zorder=4)
    ax.set_yticks(lons)
    ax.set_yticklabels([f"{st} ({lon:.1f}°E)" for st, lon in zip(st_order, lons)], fontsize=8.5)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"], fontsize=8)
    ax.set_xlabel(i18n.t("month of year"), color=MUTED)
    ax.set_ylabel(i18n.t("longitude (°E)"), color=MUTED)
    cb3 = fig.colorbar(im3, ax=ax, orientation="horizontal", pad=0.18, aspect=24)
    cb3.set_label(i18n.t("CH$_4$ anomaly from median (ppb)"), fontsize=8, color=MUTED)
    cb3.ax.tick_params(labelsize=7.5, colors=MUTED)
    ax.set_title(i18n.t("c  Maritime Continent CH$_4$ zonal wave"), loc="left", color=INK, fontsize=10)
    _tidy(ax)

    fig.suptitle(i18n.t("Figure 19  Hovmöller dynamics: Global latitudinal wave propagation and trans-archipelago monsoon migration"),
                 x=0.008, ha="left", fontsize=11, color=INK, y=1.03)
    fig.savefig(G.FIG / "f19_hovmoeller_lat_lon.png")
    plt.close(fig)


# --------------------------------------------------------------------- f26 --
def fig26():
    """Figure 20: SF6 interhemispheric mixing, vertical damping, and regional forcing balance."""
    fig, axes = plt.subplots(1, 3, figsize=(13.6, 4.5),
                             gridspec_kw=dict(wspace=0.32))

    # --- (a) SF6 interhemispheric difference and exchange timescale
    ax = axes[0]
    s_brw = nf.monthly("sf6", "brw")
    s_bkt = nf.monthly("sf6", "bkt")
    s_spo = nf.monthly("sf6", "spo")
    common = s_brw.index.intersection(s_bkt.index).intersection(s_spo.index)
    t = common.year + (common.month - 0.5) / 12.0

    ax.plot(t, s_brw.loc[common], color=WARM, lw=1.5, label=i18n.t("Barrow (71°N)"))
    ax.plot(t, s_bkt.loc[common], color=COOL, lw=1.8, label=i18n.t("Bukit Kototabang (0°S)"))
    ax.plot(t, s_spo.loc[common], color="#27ae60", lw=1.5, label=i18n.t("South Pole (90°S)"))
    ax.fill_between(t, s_spo.loc[common], s_brw.loc[common], color=GREY, alpha=0.25, zorder=1)

    diff_ns = (s_brw.loc[common] - s_spo.loc[common]).mean()
    # tau follows from the two numbers plotted; hardcoding it let the panel show
    # a tau that did not divide the difference beside it
    t_dec = common.year + (common.dayofyear - 1) / 365.25
    growth = G.theil_sen(t_dec, s_spo.loc[common].values)[0]
    tau = diff_ns / growth
    ax.text(2005.5, 10.5,
            f"$\\Delta C_{{NS}} = {diff_ns:.3f}$ ppt\n"
            f"$\\tau_{{ex}} = {tau:.2f}$ yr ({tau * 12:.1f} mo)",
            fontsize=8.5, color=INK, bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#d7dbe0", alpha=0.9))

    ax.set_ylabel(i18n.t("SF$_6$ mixing ratio (ppt)"), color=MUTED)
    ax.set_xlabel(i18n.t("year"), color=MUTED)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.set_title(i18n.t("a  SF$_6$ interhemispheric mixing clock"), loc="left", color=INK, fontsize=10)
    _tidy(ax)

    # --- (b) Vertical damping of seasonal amplitudes (MLO 3397 m vs KUM 3 m)
    ax = axes[1]
    vert_df = pd.read_csv(G.OUT / "t_vertical_damping.csv")
    y = np.arange(len(vert_df))
    
    ax.barh(y - 0.15, vert_df.kum_surface_amp, height=0.3, color=WARM, zorder=3, label=i18n.t("KUM surface (3 m)"))
    ax.barh(y + 0.15, vert_df.mlo_free_trop_amp, height=0.3, color=COOL, zorder=3, label=i18n.t("MLO free trop (3397 m)"))

    for i, row in enumerate(vert_df.itertuples()):
        lbl = f"−{row.vertical_damping_pct:.1f}% " + i18n.t("aloft")
        ax.annotate(lbl, (max(row.kum_surface_amp, row.mlo_free_trop_amp), i),
                    xytext=(6, 0), textcoords="offset points", fontsize=8.5, color=INK, va="center")

    SPECIES_LBL = {"CO2": "CO$_2$ (ppm)", "CH4": "CH$_4$ (ppb)", "CO": "CO (ppb)"}
    ax.set_yticks(y)
    ax.set_yticklabels([SPECIES_LBL.get(s, s) for s in vert_df.species], fontsize=9, color=INK)
    ax.set_xlabel(i18n.t("peak-to-peak seasonal amplitude"), color=MUTED)
    ax.set_xlim(0, max(vert_df.kum_surface_amp) * 1.35)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_title(i18n.t("b  Vertical damping of seasonal cycle (19.5°N)"), loc="left", color=INK, fontsize=10)
    _tidy(ax)

    # --- (c) Multi-species radiative forcing budget of BKT over Samoa (SMO)
    ax = axes[2]
    f_df = pd.read_csv(G.OUT / "t_regional_forcing_budget.csv")
    f_items = f_df[f_df.species != "Total Net Enhancement"].copy()
    
    y_f = np.arange(len(f_items))
    cols = [WARM if f > 0 else COOL for f in f_items.radiative_forcing_mW_m2]
    ax.barh(y_f, f_items.radiative_forcing_mW_m2, height=0.55, color=cols, zorder=3)
    ax.axvline(0, color=INK, lw=1.0)
    
    for i, row in enumerate(f_items.itertuples()):
        lbl = f"{row.radiative_forcing_mW_m2:+.1f} mW m$^{{-2}}$\n({row.delta_concentration:+.1f} {row.unit})"
        align = "left" if row.radiative_forcing_mW_m2 > 0 else "right"
        x_off = 5 if row.radiative_forcing_mW_m2 > 0 else -5
        ax.annotate(lbl, (row.radiative_forcing_mW_m2, i), xytext=(x_off, 0),
                    textcoords="offset points", ha=align, va="center", fontsize=7.5, color=INK)
    
    tot_f = float(f_df[f_df.species == "Total Net Enhancement"]["radiative_forcing_mW_m2"].iloc[0])
    ax.axvline(tot_f, color="#e67e22", lw=1.5, ls="--", zorder=4)
    ax.text(tot_f + 2, -0.3, f"Net: {tot_f:+.2f} mW m$^{{-2}}$", color="#e67e22", fontsize=8.5, fontweight="bold")

    ax.set_yticks(y_f)
    SPECIES_CLEAN = {"CO2": "CO$_2$", "CH4": "CH$_4$", "N2O": "N$_2$O", "SF6": "SF$_6$"}
    ax.set_yticklabels([SPECIES_CLEAN.get(s, s) for s in f_items.species], fontsize=9, color=INK)
    ax.set_xlabel(i18n.t("radiative forcing anomaly (mW m$^{-2}$)"), color=MUTED)
    ax.set_xlim(-55, 65)
    ax.set_title(i18n.t("c  Regional forcing anomaly over marine air"), loc="left", color=INK, fontsize=10)
    _tidy(ax)

    fig.suptitle(i18n.t("Figure 20  Transport timescale, vertical damping, and regional radiative forcing balance"),
                 x=0.008, ha="left", fontsize=11, color=INK, y=1.03)
    fig.savefig(G.FIG / "f20_hovmoeller_transport_forcing.png")
    plt.close(fig)


def main():
    fig25()
    fig26()


if __name__ == "__main__":
    # install(), not set_lang(): install() also patches savefig so a non-default
    # language writes <name>_id.png.  set_lang() alone translates the strings
    # and then overwrites the English file with them.
    i18n.install(i18n.from_argv())
    G.style()
    main()
    print("wrote f19_hovmoeller_seasonal.png, f20_hovmoeller_transport_forcing.png")

