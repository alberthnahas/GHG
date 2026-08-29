"""Figure 13 - process diagnostics.  Reads a9_process.py and a11_flask.py output."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G
import i18n
import noaa_flask as NF


def _flask_amp(site):
    """Seasonal amplitude measured from the NOAA flask record, not quoted."""
    lat = pd.read_csv(G.OUT / "z_latitude.csv")
    r = lat[(lat.species == "co2") & (lat.site == site)]
    return float(r.amp.iloc[0])

INK, MUTED = "#1b1f24", "#6b7280"
MONTHS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]


def _tidy(ax):
    ax.tick_params(colors=MUTED, labelsize=8)
    for s in ax.spines.values():
        s.set_color("#d7dbe0")


def fig13():
    sc = pd.read_csv(G.OUT / "y_scale.csv")
    rs = pd.read_csv(G.OUT / "y_resp_season.csv")
    se = pd.read_csv(G.OUT / "x_seasonal_ci.csv")
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.2), gridspec_kw=dict(wspace=0.38))

    # (a) each site's afternoon CO2 referenced to the flask-anchored BKT record.
    # The earlier version of this panel compared against a quoted global mean and
    # concluded the network was 5-9 ppm low; a11_flask.py showed that conclusion
    # was wrong, so the reference here is the one measurement that is demonstrably
    # on the WMO scale - BKT's own co-located flasks.
    ax = axes[0]
    lad = pd.read_csv(G.OUT / "x_ladder.csv")
    d = pd.read_csv(G.OUT / "z_drift.csv")
    anchor = d[(d.species == "co2") & (d.year >= 2019)]["diff"].median()
    # the shaded band is how well BKT agrees with its own NOAA flasks
    s = lad[lad.species == "co2"].copy()
    # Bariri is the reference the ladder is built on, so it enters at zero.
    s = pd.concat([s, pd.DataFrame([dict(station="PLU", species="co2", delta=0.0,
                                         se=0.0, n_months=0)])], ignore_index=True)
    s = s.sort_values("delta")
    x = np.arange(len(s))
    ax.bar(x, s.delta, width=0.55, color=[G.COL[i] for i in s.station], zorder=2)
    ax.errorbar(x, s.delta, yerr=1.96 * s.se, fmt="none", ecolor=INK,
                elinewidth=1, capsize=2)
    ax.axhline(0, color=INK, lw=1.2)
    ax.axhspan(-abs(anchor) - 0.5, abs(anchor) + 0.5, color="#9aa3ad", alpha=0.18, zorder=0)
    for xi, v, st in zip(x, s.delta, s.station):
        ax.annotate(f"{v:+.1f}", (xi, v), xytext=(0, -13 if v < 0 else 5),
                    textcoords="offset points", ha="center", fontsize=8, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels(s.station)
    ax.set_ylabel("afternoon background − Bariri (ppm)", color=MUTED)
    ax.set_title("a  CO$_2$ referenced to the flask-anchored site", loc="left", color=INK)
    ax.margins(y=0.25)
    _tidy(ax)

    # (b) the phase of nocturnal respiration: intact soil vs drained peat
    ax = axes[1]
    for st in ("PLU", "JMB"):
        v = rs[rs.station == st].sort_values("month")
        n = v.rate / v.rate.mean()
        ax.plot(v.month, n, marker=G.MRK[st], ls=G.LS[st], lw=2, ms=7, color=G.COL[st],
                mec="white", mew=1.1, label=G.STATIONS[st][0])
    ax.axhline(1, color=MUTED, lw=1, zorder=0)
    ax.axvspan(7.5, 10.5, color="#9aa3ad", alpha=0.16, zorder=0)
    ax.annotate("Sumatran dry season", xy=(9, 1.44), ha="center", fontsize=7.5, color=INK)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(MONTHS)
    ax.set_ylabel("nocturnal CO$_2$ build-up / annual mean", color=MUTED)
    ax.set_title("b  Respiration phase, normalised", loc="left", color=INK)
    ax.legend(loc="lower left", fontsize=7.5)
    ax.set_ylim(0.5, 1.55)
    _tidy(ax)

    # (c) where the equatorial amplitude sits between Mauna Loa and the South Pole
    ax = axes[2]
    s = se[se.species == "co2"].copy()
    s["lat"] = [G.STATIONS[i][2] for i in s.station]
    ax.errorbar(s.lat, s.amp, yerr=[s.amp - s.lo, s.hi - s.amp], fmt="none",
                ecolor=MUTED, elinewidth=1, capsize=2, zorder=2)
    for _, r in s.iterrows():
        ax.plot(r.lat, r.amp, marker=G.MRK[r.station], ms=9, color=G.COL[r.station],
                mec="white", mew=1.3, zorder=3)
        dx, dy = {"KMY": (8, -4), "JMB": (9, -2), "PLU": (9, -9),
                  "SRG": (-8, 6), "BKT": (8, 2)}[r.station]
        ax.annotate(r.station, (r.lat, r.amp), xytext=(dx, dy), textcoords="offset points",
                    fontsize=7.5, color=INK, ha="right" if dx < 0 else "left")
    mlo, spo = _flask_amp("mlo"), _flask_amp("spo")
    ax.axhline(mlo, color=INK, lw=1.4, ls="--")
    ax.annotate(f"Mauna Loa, 19 °N   {mlo:.1f} ppm", xy=(-6.8, mlo), xytext=(0, 5),
                textcoords="offset points", fontsize=8, color=INK)
    ax.axhline(spo, color=INK, lw=1.4, ls=":")
    ax.annotate(f"South Pole   {spo:.1f} ppm", xy=(-6.8, spo), xytext=(0, -14),
                textcoords="offset points", fontsize=8, color=INK)
    ax.set_xlabel("station latitude (°N)", color=MUTED)
    ax.set_ylabel("CO$_2$ seasonal amplitude (ppm)", color=MUTED)
    ax.set_title("c  Amplitude vs Mauna Loa and the pole", loc="left", color=INK)
    ax.set_ylim(0, 11)
    ax.set_xlim(-7, 1.2)
    _tidy(ax)

    fig.suptitle("Figure 13  Inter-station CO$_2$, respiration phase, and seasonal amplitude",
                 x=0.008, ha="left", fontsize=11, color=INK, y=1.03)
    fig.savefig(G.FIG / "f13_external_checks.png")
    plt.close(fig)


def main():
    fig13()


if __name__ == "__main__":
    i18n.install(i18n.from_argv())
    G.style()
    main()
    print("wrote f13_external_checks.png")
