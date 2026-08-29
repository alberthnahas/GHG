"""Figures 23-24 for the fourth pass.  Reads a26_extra4.py output."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G
import i18n

INK, MUTED = "#1b1f24", "#6b7280"
WARM, COOL, GREY = "#c0392b", "#1f6f8b", "#b8c0c8"


def _tidy(ax):
    ax.tick_params(colors=MUTED, labelsize=8)
    for s in ax.spines.values():
        s.set_color("#d7dbe0")


# --------------------------------------------------------------------- f23 --
def fig23():
    pairs = pd.read_csv(G.OUT / "t_flask_pairs.csv")
    sf6 = pd.read_csv(G.OUT / "t_sf6_lag.csv")
    vert = pd.read_csv(G.OUT / "t_vertical_gradients.csv")

    fig, axes = plt.subplots(1, 3, figsize=(13.6, 4.5),
                             gridspec_kw=dict(wspace=0.32))

    # (a) NOAA flask pair measurement precision
    ax = axes[0]
    p = pairs.copy()
    y = np.arange(len(p))
    # Normalized error: single flask sigma as % of median pair diff or absolute bar
    ax.barh(y - 0.15, p.median_pair_diff, height=0.3, color=COOL, zorder=3, label=i18n.t("median |diff|"))
    ax.barh(y + 0.15, p.p95_pair_diff, height=0.3, color=GREY, zorder=3, label=i18n.t("95th percentile"))
    for i, row in enumerate(p.itertuples()):
        lbl = f"{row.median_pair_diff:.3g} {row.unit}"
        ax.annotate(lbl, (row.p95_pair_diff, i + 0.15), xytext=(5, 0),
                    textcoords="offset points", fontsize=8, color=INK, va="center")
    SPECIES_LBL = {"CO2": "CO$_2$", "CH4": "CH$_4$", "CO": "CO", "N2O": "N$_2$O", "SF6": "SF$_6$", "H2": "H$_2$"}
    ax.set_yticks(y)
    ax.set_yticklabels([SPECIES_LBL.get(s, s) for s in p.species], fontsize=9.5, color=INK)
    ax.set_xlabel(i18n.t("pair difference (|flask 1 − flask 2|)"), color=MUTED)
    ax.set_xlim(0, max(p.p95_pair_diff) * 1.35)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_title(i18n.t("a  Flask pair agreement at Bukit Kototabang"),
                 loc="left", color=INK, fontsize=10)
    _tidy(ax)

    # (b) SF6 interhemispheric transport clock
    ax = axes[1]
    s = sf6.sort_values("lat", ascending=False)
    y = np.arange(len(s))
    ax.barh(y, s.lag_from_brw_months, height=0.55, color=COOL, zorder=3)
    for i, row in enumerate(s.itertuples()):
        ax.annotate(f"{row.lag_from_brw_months:.1f} " + i18n.t("mo"),
                    (row.lag_from_brw_months, i), xytext=(6, 0),
                    textcoords="offset points", fontsize=8.5, color=INK, va="center")
    ax.set_yticks(y)
    site_labels = [f"{row.site} ({row.lat:+.0f}°)" for row in s.itertuples()]
    ax.set_yticklabels(site_labels, fontsize=9, color=INK)
    ax.set_xlim(0, max(s.lag_from_brw_months) * 1.25)
    ax.set_xlabel(i18n.t("transport lag behind Arctic (months)"), color=MUTED)
    ax.set_title(i18n.t("b  SF$_6$ as an interhemispheric clock"),
                 loc="left", color=INK, fontsize=10)
    _tidy(ax)

    # (c) Vertical gradient: MLO (3397 m) vs KUM (3 m)
    ax = axes[2]
    v = vert[vert.species.isin(["CO2", "CH4", "CO", "N2O", "SF6"])].copy()
    # Normalize diff by std to show standardized vertical separation
    v["z_score"] = v["mlo_minus_kum_mean"] / v["mlo_minus_kum_std"]
    y = np.arange(len(v))
    cols = [WARM if z > 0 else COOL for z in v.z_score]
    ax.barh(y, v.z_score, height=0.55, color=cols, zorder=3)
    ax.axvline(0, color=INK, lw=1.0)
    for i, row in enumerate(v.itertuples()):
        lbl = f"{row.mlo_minus_kum_mean:+.2f} {row.unit}"
        x_pos = max(0, row.z_score) if row.z_score > 0 else min(0, row.z_score)
        align = "left" if row.z_score > 0 else "right"
        x_off = 5 if row.z_score > 0 else -5
        ax.annotate(lbl, (x_pos, i), xytext=(x_off, 0), textcoords="offset points",
                    ha=align, va="center", fontsize=8, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels(v.species, fontsize=9.5, color=INK)
    ax.set_xlim(min(v.z_score) * 1.35, max(v.z_score) * 1.35 + 0.5)
    ax.set_xlabel(i18n.t("standardized vertical difference (MLO − KUM)"), color=MUTED)
    ax.set_title(i18n.t("c  Free troposphere vs boundary layer (19.5°N)"),
                 loc="left", color=INK, fontsize=10)
    _tidy(ax)

    fig.suptitle(i18n.t("Figure 5  Flask reproducibility, interhemispheric transport lag, "
                        "and vertical stratification"),
                 x=0.008, ha="left", fontsize=11, color=INK, y=1.03)
    fig.savefig(G.FIG / "f5_flask_pairs_sf6_vert.png")
    plt.close(fig)


# --------------------------------------------------------------------- f24 --
def fig24():
    kmy = pd.read_csv(G.OUT / "t_kmy_diurnal_rush.csv")
    h2 = pd.read_csv(G.OUT / "t_h2_seasonality.csv")
    n2o_acc = pd.read_csv(G.OUT / "t_n2o_acceleration.csv")
    all_df = G.load_all()
    kmy_df = all_df[all_df["station"] == "KMY"].copy()
    kmy_df["dow"] = kmy_df["time_local"].dt.dayofweek
    kmy_df["is_weekend"] = kmy_df["dow"] >= 5

    fig, axes = plt.subplots(1, 3, figsize=(13.6, 4.5),
                             gridspec_kw=dict(wspace=0.32))

    # (a) Jakarta CO rush hour: weekday vs weekend
    ax = axes[0]
    wkday_co = kmy_df[~kmy_df["is_weekend"]].groupby("hour_local")["co"].median()
    wkend_co = kmy_df[kmy_df["is_weekend"]].groupby("hour_local")["co"].median()
    hours = np.arange(24)
    ax.plot(hours, wkday_co, color=WARM, lw=2.0, label=i18n.t("weekday"))
    ax.plot(hours, wkend_co, color=COOL, lw=2.0, ls="--", label=i18n.t("weekend"))
    ax.axvspan(6, 9, color=GREY, alpha=0.2, label=i18n.t("morning rush"))
    ax.set_xticks(np.arange(0, 25, 4))
    ax.set_xlabel(i18n.t("local hour (WIB)"), color=MUTED)
    ax.set_ylabel(i18n.t("median CO (ppb)"), color=MUTED)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    ax.set_title(i18n.t("a  Jakarta CO drops 24% on weekend mornings"),
                 loc="left", color=INK, fontsize=10)
    _tidy(ax)

    # (b) Equatorial H2 bimodal seasonal climatology
    ax = axes[1]
    m_num = h2.month.values
    ax.plot(m_num, h2.mean_ppb, color=COOL, marker="o", lw=1.8, zorder=3)
    ax.fill_between(m_num, h2.mean_ppb - h2.std_ppb, h2.mean_ppb + h2.std_ppb,
                    color=COOL, alpha=0.15, zorder=2)
    ax.axhline(h2.mean_ppb.mean(), color=INK, lw=0.9, ls=":", zorder=1)
    ax.set_xticks(np.arange(1, 13))
    ax.set_xticklabels([i18n.t(name) for name in h2.month_name], fontsize=7.5, color=INK)
    ax.set_ylabel(i18n.t("H$_2$ mole fraction (ppb)"), color=MUTED)
    ax.annotate(i18n.t("fire peak"), (10, h2.loc[h2.month == 10, "mean_ppb"].values[0]),
                xytext=(0, 10), textcoords="offset points", ha="center", fontsize=8, color=WARM)
    ax.annotate(i18n.t("soil sink min"), (6, h2.loc[h2.month == 6, "mean_ppb"].values[0]),
                xytext=(0, -14), textcoords="offset points", ha="center", fontsize=8, color=COOL)
    ax.set_title(i18n.t("b  Bimodal equatorial H$_2$ seasonal cycle"),
                 loc="left", color=INK, fontsize=10)
    _tidy(ax)

    # (c) Uniform decadal N2O acceleration across latitudes
    ax = axes[2]
    n_sorted = n2o_acc.sort_values("lat", ascending=False)
    y = np.arange(len(n_sorted))
    ax.barh(y - 0.15, n_sorted.trend_2004_2013, height=0.28, color=COOL, label="2004–2013")
    ax.barh(y + 0.15, n_sorted.trend_2014_2024, height=0.28, color=WARM, label="2014–2024")
    for i, row in enumerate(n_sorted.itertuples()):
        ax.annotate(f"+{row.acceleration_jump:.3f}", (row.trend_2014_2024, i + 0.15),
                    xytext=(5, 0), textcoords="offset points", fontsize=8, color=WARM, va="center")
    ax.set_yticks(y)
    site_labels = [f"{row.site} ({row.lat:+.0f}°)" for row in n_sorted.itertuples()]
    ax.set_yticklabels(site_labels, fontsize=9, color=INK)
    ax.set_xlim(0, max(n_sorted.trend_2014_2024) * 1.25)
    ax.set_xlabel(i18n.t("N$_2$O growth rate (ppb yr⁻¹)"), color=MUTED)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_title(i18n.t("c  Global uniform N$_2$O acceleration (+0.23 ppb yr⁻¹)"),
                 loc="left", color=INK, fontsize=10)
    _tidy(ax)

    fig.suptitle(i18n.t("Figure 11  Jakarta rush-hour fingerprint, equatorial H$_2$ seasonality, "
                        "and global N$_2$O acceleration"),
                 x=0.008, ha="left", fontsize=11, color=INK, y=1.03)
    fig.savefig(G.FIG / "f11_regional_diurnal_n2o.png")
    plt.close(fig)


def main():
    fig23()
    fig24()


if __name__ == "__main__":
    i18n.install(i18n.from_argv())
    G.style()
    main()
    print("wrote f5_flask_pairs_sf6_vert.png, f11_regional_diurnal_n2o.png")
