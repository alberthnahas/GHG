"""Carbon source and sink: separating biology from dilution, and a budget frame.

Two questions the earlier passes did not ask.

**Is the surface under each station a net carbon sink or source during the day?**
The morning CO2 decline mixes two things - the growing mixed layer diluting the
nocturnal store, and photosynthesis removing CO2 outright - and a single species
cannot separate them.  CH4 and CO can: neither has a photosynthetic sink, so
their morning decline measures dilution alone.  Whatever extra loss CO2 shows on
the *same morning* is biological.

**What do the measured growth rates mean in carbon-budget units?**  A ppm is
converted to Pg C from first principles, so the station's own record can be put
beside global emissions and sinks.

  A  paired morning decay rates, CO2 against each tracer -> outputs/v_sink.csv
  B  the CO2/tracer excess ratio through the day         -> outputs/v_ratio.csv
  C  the same ratio through the night (the null test)    -> outputs/v_nulltest.csv
  D  budget conversions                                  -> outputs/v_budget.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G

OUT = G.OUT
RNG = np.random.default_rng(20260815)

# Minimum nocturnal excess a species must show for that morning to be usable.
THR = {"co2": 5.0, "ch4": 15.0, "co": 10.0}
MORNING = (7, 12)
AFTERNOON = (13, 16)

# --- carbon-budget reference values ----------------------------------------
# The ppm -> Pg C factor is derived here rather than quoted: it follows from the
# mass of the atmosphere and the molar masses alone.
M_ATM_KG = 5.148e18        # mass of the atmosphere
M_AIR = 28.96              # g/mol, dry air
M_C = 12.011               # g/mol
PPM_TO_PGC = (M_ATM_KG * 1e3 / M_AIR) * 1e-6 * M_C / 1e15

# Global Carbon Budget terms, quoted; see the report's Appendix C.
GCB = dict(fossil=10.1, land_use=1.0, total_emissions=11.1,
           ocean_sink=2.9, land_sink=3.2, atmospheric_growth=5.9)


# ---------------------------------------------------------------- A ---------
def _tau(dd, sp):
    """e-folding time of one morning's decline toward that day's afternoon floor."""
    m = dd[(dd.hour_local >= MORNING[0]) & (dd.hour_local <= MORNING[1])][["hour_local", sp]].dropna()
    floor = dd[(dd.hour_local >= AFTERNOON[0]) & (dd.hour_local <= AFTERNOON[1])][sp].min()
    if len(m) < 5 or not np.isfinite(floor):
        return np.nan
    e = m[sp].values - floor
    if e[0] < THR[sp] or (e <= 0.5).any():
        return np.nan
    x = m.hour_local.values.astype(float)
    y = np.log(e)
    k = np.polyfit(x, y, 1)[0]
    if k >= 0 or np.corrcoef(x, y)[0, 1] > -0.9:
        return np.nan
    return -1 / k


def sink_rates(d, n_boot=2000):
    """Extra first-order CO2 loss, measured against a tracer on the same morning.

    The comparison has to be *paired*.  Taking the median tau of CO2 over all its
    usable days and the median tau of CH4 over all of its own usable days
    compares two different populations of mornings, and the two tracers then
    disagree by more than the effect being measured.  Restricting to mornings
    where both species pass the gates removes that.
    """
    rows = []
    for st, g in d.groupby("station"):
        for tr in ("ch4", "co"):
            pairs = []
            for _, dd in g.groupby("date"):
                a, b = _tau(dd, "co2"), _tau(dd, tr)
                if np.isfinite(a) and np.isfinite(b):
                    pairs.append((1 / a, 1 / b))
            if len(pairs) < 60:
                continue
            p = np.array(pairs)
            diff = p[:, 0] - p[:, 1]
            bs = np.array([np.median(RNG.choice(diff, len(diff))) for _ in range(n_boot)])
            lo, hi = np.percentile(bs, [2.5, 97.5])
            k_co2 = np.median(p[:, 0])
            rows.append(dict(station=st, tracer=tr, n_days=len(p), k_co2=k_co2,
                             k_tracer=np.median(p[:, 1]), diff=np.median(diff),
                             lo=lo, hi=hi, pct_of_decline=100 * np.median(diff) / k_co2,
                             significant=bool(lo * hi > 0)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- B, C -----
def _excess_ratio(d, hours, night=False, tracer="ch4"):
    """Median CO2-excess / tracer-excess by hour, one curve per station."""
    d = d.copy()
    if night:
        d["grp"] = (d.time_local - pd.Timedelta(hours=12)).dt.normalize()
    else:
        d["grp"] = d.date
    rows = []
    for st, g in d.groupby("station"):
        curves = []
        for _, dd in g.groupby("grp"):
            aft = dd[(dd.hour_local >= AFTERNOON[0]) & (dd.hour_local <= AFTERNOON[1])]
            if len(aft) < 3:
                continue
            c0, m0 = aft.co2.min(), aft[tracer].min()
            if not (np.isfinite(c0) and np.isfinite(m0)):
                continue
            w = dd[dd.hour_local.isin(hours)].sort_values("time_local")[["hour_local", "co2", tracer]].dropna()
            if len(w) < 7:
                continue
            dC, dM = w.co2 - c0, w[tracer] - m0
            if dC.iloc[0] < 8 or dM.iloc[0] < 8:
                continue
            r = (dC / dM).values
            if np.all(np.isfinite(r)):
                curves.append(pd.Series(r, index=(np.arange(len(r)) if night
                                                  else w.hour_local.values)))
        if len(curves) < 40:
            continue
        med = pd.DataFrame(curves).median()
        for k, v in med.items():
            rows.append(dict(station=st, tracer=tracer, step=int(k), ratio=v,
                             n_days=len(curves), phase="night" if night else "day"))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- D ---------
def budget():
    fl = pd.read_csv(OUT / "z_flask_trend.csv").set_index("species")
    dec = pd.read_csv(OUT / "w_decadal.csv")
    dec = dec[dec.species == "co2"].set_index("period")["trend"]
    ga = pd.read_csv(OUT / "x_growth_anom.csv")
    ga = ga[(ga.species == "co2") & (ga.station == "PLU")].set_index("year")["growth"]

    g = fl.loc["co2", "trend"]
    rows = [dict(quantity="ppm -> Pg C conversion factor", value=PPM_TO_PGC, unit="Pg C ppm-1",
                 note="derived from the mass of the atmosphere and molar masses"),
            dict(quantity="BKT flask CO2 growth 2004-2025", value=g, unit="ppm yr-1", note=""),
            dict(quantity="implied atmospheric accumulation", value=g * PPM_TO_PGC,
                 unit="Pg C yr-1", note="= growth x conversion factor"),
            dict(quantity="airborne fraction", value=100 * g * PPM_TO_PGC / GCB["total_emissions"],
                 unit="%", note=f"against total emissions {GCB['total_emissions']} Pg C yr-1")]
    for period in dec.index:
        rows.append(dict(quantity=f"accumulation, {period}", value=dec[period] * PPM_TO_PGC,
                         unit="Pg C yr-1", note=f"from {dec[period]:.2f} ppm yr-1"))
    if 2023 in ga.index:
        base = ga.drop(2023).mean()
        anom = ga[2023] - base
        rows.append(dict(quantity="2023 El Nino growth anomaly (Bariri)", value=anom,
                         unit="ppm yr-1", note=f"{ga[2023]:.2f} against {base:.2f} in other years"))
        rows.append(dict(quantity="  as a carbon flux", value=anom * PPM_TO_PGC, unit="Pg C yr-1",
                         note=f"compare the global land sink, {GCB['land_sink']} Pg C yr-1"))

    nf = pd.read_csv(OUT / "x_noct_flux.csv")
    nf = nf[nf.species == "co2"].set_index("station")
    gc = M_C * 3.156e7 / 1e6                       # umol m-2 s-1 -> g C m-2 yr-1
    excess = (nf.loc["JMB", "flux_h200"] - nf.loc["PLU", "flux_h200"]) * gc
    rows.append(dict(quantity="Jambi minus Bariri respiration", value=excess,
                     unit="g C m-2 yr-1", note="the drained-peat excess"))
    rows.append(dict(quantity="  as an areal loss", value=excess / 100, unit="t C ha-1 yr-1", note=""))
    for store in (1000, 2000, 3000):
        rows.append(dict(quantity=f"  e-folding time of a {store} t C ha-1 store",
                         value=store / (excess / 100), unit="yr", note=""))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
def main():
    pd.set_option("display.width", 220)
    d = pd.read_pickle(OUT / "all.pkl")

    tables = {
        "v_sink": sink_rates(d),
        "v_ratio": pd.concat([_excess_ratio(d, list(range(5, 14)), tracer=t)
                              for t in ("ch4", "co")], ignore_index=True),
        "v_nulltest": _excess_ratio(d, [19, 20, 21, 22, 23, 0, 1, 2, 3, 4], night=True),
        "v_budget": budget(),
    }
    for name, t in tables.items():
        t.to_csv(OUT / f"{name}.csv", index=False)
        print(f"\n===== {name} =====")
        print(t.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
