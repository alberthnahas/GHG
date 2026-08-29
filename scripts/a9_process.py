"""Process-level analyses of the in-situ network.

Boundary-layer, respiration and transport diagnostics that need the hourly data
and nothing else.  Absolute-scale questions are NOT answered here - they need an
external reference, which is what a11_flask.py brings in.  The one comparison
against an outside number that remains in this module (part A) is retained only
so that its failure is on the record: it is superseded by a11 and is discussed
as a corrected result in the report.

  A  scale comparison against a published global mean (SUPERSEDED by a11)
                                                           -> outputs/y_scale.csv
  B  morning boundary-layer erosion timescale               -> outputs/y_morning.csv
  C  seasonality of nocturnal ecosystem respiration         -> outputs/y_resp_season.csv
  D  first-harmonic phase of the CH4 seasonal cycle         -> outputs/y_ch4_phase.csv
  E  CO2 seasonal amplitude vs the Mauna Loa/South Pole pair -> printed
  F  fossil bound on Jakarta's CO2 enhancement              -> printed
  G  CO afternoon level vs the hemispheric brackets          -> outputs/y_co_levels.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G

OUT = G.OUT

# --- external numbers used below -------------------------------------------
# These are quoted published values, not measurements made in this project, and
# every one of them needs tracing to a primary source before publication.  Where
# an equivalent quantity can be MEASURED from the NOAA flask network instead, it
# is - see a11_flask.py, which supersedes the global-mean comparison in part A.
CO2_GLOBAL, CO2_GLOBAL_MONTH = 427.35, "2025-12"   # ppm, quoted global monthly mean
CH4_GLOBAL, CH4_GLOBAL_MONTH = 1946.47, "2025-10"  # ppb, quoted global monthly mean
MLO_AMP, SPO_AMP = 15.0, 3.0        # ppm; SUPERSEDED - a11 measures 6.9 and 1.3
GPP_GLOBAL, ER_GLOBAL = 120e15, 118e15             # g C yr-1, quoted
LAND_AREA = 1.3e14                                 # m2, ice-free land
CO_SH, CO_NH_WINTER, CO_GLOBAL = (50, 70), (150, 200), (80, 100)   # ppb, quoted

GC_PER_YR = 12.011 * 3.156e7 / 1e6      # umol m-2 s-1 -> g C m-2 yr-1


def afternoon(d):
    return d[(d.hour_local >= 12) & (d.hour_local <= 16)]


# ---------------------------------------------------------------- A ---------
def scale_check(d):
    """Compare the afternoon well-mixed median against the global monthly mean.

    Two forms are reported.  The *direct* form takes the station's median in the
    same month as the reference value and needs no extrapolation at all.  The
    *adjusted* form growth-corrects every month of the record to the reference
    date, which is more precise but only trustworthy over a short span - over a
    fifteen-year record the answer becomes a function of the assumed growth rate
    rather than of the data, which is why BKT's is reported across a range.
    """
    a = afternoon(d)
    rows = []
    for st in G.ORDER:
        for sp, ref, month, growth in (("co2", CO2_GLOBAL, CO2_GLOBAL_MONTH, (2.0, 2.4, 2.86, 3.2)),
                                       ("ch4", CH4_GLOBAL, CH4_GLOBAL_MONTH, (6.0, 9.0, 13.0))):
            g = a[(a.station == st) & np.isfinite(a[sp]) & (~a["suspect_" + sp])]
            if len(g) < 500:
                continue
            direct = g[g.time_local.dt.to_period("M") == pd.Period(month)][sp]
            m = g.groupby(g.time_local.dt.to_period("M"))[sp].agg(["median", "size"])
            m = m[m["size"] >= 60]
            if len(m) < 12:
                continue
            t = m.index.to_timestamp()
            dt = (pd.Timestamp(month + "-15") - t).days / 365.25
            adj = {f"adj_g{gr}": float(np.median(m["median"].values + gr * dt)) - ref for gr in growth}
            rows.append(dict(station=st, species=sp, ref=ref, ref_month=month,
                             n_months=len(m), span_yr=float(dt.max() - dt.min()),
                             direct=float(direct.median()) if len(direct) >= 20 else np.nan,
                             direct_offset=float(direct.median()) - ref if len(direct) >= 20 else np.nan,
                             **adj))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- B ---------
def morning_erosion(d):
    """e-folding time of the morning CO2 collapse, 07:00-12:00 local.

    As the convective layer deepens it dilutes the nocturnal store toward the
    afternoon value; the decay constant is a direct measure of how fast the
    surface decouples from its own emissions.  Published values put the
    turbulent mixing timescale at 'hours' - this measures it."""
    rows = []
    for st, g in d.groupby("station"):
        taus = []
        for _, dd in g.groupby("date"):
            m = dd[(dd.hour_local >= 7) & (dd.hour_local <= 12)][["hour_local", "co2"]].dropna()
            floor = dd[(dd.hour_local >= 13) & (dd.hour_local <= 16)]["co2"].min()
            if len(m) < 5 or not np.isfinite(floor):
                continue
            e = m.co2.values - floor
            if e[0] < 5 or (e <= 0.5).any():
                continue
            x = m.hour_local.values.astype(float)
            k = np.polyfit(x, np.log(e), 1)[0]
            if k < 0 and np.corrcoef(x, np.log(e))[0, 1] < -0.9:
                taus.append(-1 / k)
        if len(taus) >= 100:
            t = np.array(taus)
            rows.append(dict(station=st, n_days=len(t), tau_h=np.median(t),
                             q25=np.percentile(t, 25), q75=np.percentile(t, 75)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- C ---------
def respiration_season(d):
    """Month-by-month nocturnal CO2 accumulation rate.

    The *phase* of this cycle discriminates two soil regimes that the annual
    mean cannot.  Respiration in an intact, water-limited soil rises with
    wetness; respiration in a drained peat rises with dryness, because lowering
    the water table lets oxygen into stored carbon that anoxia had protected."""
    d = d.copy()
    d["night_date"] = (d.time_local - pd.Timedelta(hours=12)).dt.normalize()
    night = d[(d.hour_local >= 19) | (d.hour_local <= 4)]
    rows = []
    for st, g in night.groupby("station"):
        rec = []
        for nd, n in g.groupby("night_date"):
            n = n.sort_values("time_local")
            h = (n.time_local - n.time_local.iloc[0]).dt.total_seconds().values / 3600
            m = np.isfinite(n["co2"]).values
            if m.sum() < 6 or np.ptp(h[m]) < 5:
                continue
            x, y = h[m], n["co2"].values[m]
            if y.std() == 0:
                continue
            if np.corrcoef(x, y)[0, 1] > 0.7:
                rec.append((nd.month, np.polyfit(x, y, 1)[0]))
        if len(rec) < 100:
            continue
        v = pd.DataFrame(rec, columns=["month", "rate"])
        mo = v.groupby("month")["rate"].agg(["median", "size"])
        mo = mo[mo["size"] >= 8]
        if len(mo) < 8:
            continue
        for mth, r in mo.iterrows():
            rows.append(dict(station=st, month=int(mth), rate=r["median"], n=int(r["size"])))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- D ---------
def monthly_background(g, sp, q=0.20):
    g = g[(g.hour_local >= 12) & (g.hour_local <= 16) &
          np.isfinite(g[sp]) & (~g["suspect_" + sp])]
    b = g.groupby(g.time_local.dt.to_period("M"))[sp].quantile(q)
    n = g.groupby(g.time_local.dt.to_period("M"))[sp].size()
    b = b[n >= 20]
    b.index = b.index.to_timestamp()
    return b


def ch4_phase(d):
    """Day of year of the first-harmonic maximum of the CH4 seasonal cycle.

    Finding 6 rests on the seasonal *amplitude* declining eastward.  Phase is an
    independent property of the same cycle, so if the transport interpretation
    is right the maximum should also arrive progressively later eastward."""
    rows = []
    for st in G.ORDER:
        s = monthly_background(d[d.station == st], "ch4")
        if len(s) < 24:
            continue
        t = s.index.year + (s.index.month - 0.5) / 12
        f = G.harmonic_fit(t, s.values, n_harm=3, poly=2)
        sin1, cos1 = f["beta"][3], f["beta"][4]     # poly=2 -> beta[0:3] trend
        doy = ((np.arctan2(sin1, cos1) / (2 * np.pi)) % 1) * 365.25
        rows.append(dict(station=st, lon=G.STATIONS[st][3], lat=G.STATIONS[st][2],
                         amp1=2 * np.hypot(sin1, cos1), doy_max=doy,
                         date_max=str((pd.Timestamp("2025-01-01") +
                                       pd.Timedelta(days=doy - 1)).strftime("%d %b")),
                         n_months=len(s)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- G ---------
def co_levels(d):
    a = afternoon(d)
    a = a[a.time_local >= "2023-06-01"]      # after Sorong's usable record starts
    rows = []
    for st in G.ORDER:
        g = a[(a.station == st) & np.isfinite(a.co) & (~a.suspect_co)]
        if len(g) < 500:
            continue
        rows.append(dict(station=st, lon=G.STATIONS[st][3], n=len(g),
                         p10=g.co.quantile(.10), p50=g.co.median(), p90=g.co.quantile(.90)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
def main():
    d = pd.read_pickle(OUT / "all.pkl")
    pd.set_option("display.width", 220)

    for name, fn in (("y_scale", scale_check), ("y_morning", morning_erosion),
                     ("y_resp_season", respiration_season), ("y_ch4_phase", ch4_phase),
                     ("y_co_levels", co_levels)):
        t = fn(d)
        t.to_csv(OUT / f"{name}.csv", index=False)
        print(f"\n===== {name} =====")
        print(t.round(3).to_string(index=False))

    print("\n===== E. CO2 seasonal amplitude against the Mauna Loa / South Pole pair =====")
    print(f"   quoted (SUPERSEDED - see a11): ~{MLO_AMP:.0f} ppm Mauna Loa, ~{SPO_AMP:.0f} ppm South Pole")
    se = pd.read_csv(OUT / "x_seasonal_ci.csv")
    for _, r in se[se.species == "co2"].iterrows():
        print(f"   {r.station} lat={G.STATIONS[r.station][2]:6.2f}  amp={r.amp:5.2f} ppm "
              f"[{r.lo:.2f},{r.hi:.2f}]  = {100 * r.amp / MLO_AMP:3.0f}% of Mauna Loa")

    print("\n===== D2. respiration annualised, against the land-carbon benchmarks =====")
    print(f"   quoted: global GPP {GPP_GLOBAL/1e15:.0f}, ER {ER_GLOBAL/1e15:.0f} Pg C yr-1 "
          f"-> land-mean ER {ER_GLOBAL/LAND_AREA:.0f} g C m-2 yr-1")
    nf = pd.read_csv(OUT / "x_noct_flux.csv")
    nf = nf[nf.species == "co2"].set_index("station")
    for st in ("PLU", "SRG", "BKT", "KMY", "JMB"):
        print(f"   {st}: {nf.loc[st, 'flux_h200'] * GC_PER_YR:5.0f} g C m-2 yr-1 "
              f"(h=100 {nf.loc[st, 'flux_h100'] * GC_PER_YR:.0f}, h=400 {nf.loc[st, 'flux_h400'] * GC_PER_YR:.0f})")

    print("\n===== F. fossil bound on Jakarta's regional CO2 enhancement =====")
    lad = pd.read_csv(OUT / "x_ladder.csv").set_index(["station", "species"])
    dco, dco2 = lad.loc[("KMY", "co"), "delta"], lad.loc[("KMY", "co2"), "delta"]
    for R, lab in ((23.5, "measured nightly median - a LOWER bound on the true combustion ratio"),
                   (30.9, "upper quartile of the nightly ratios"),
                   (15.0, "top of the efficient-fleet literature band")):
        print(f"   R={R:5.1f} ppb ppm-1 ({lab}): ffCO2 = {dco/R:4.1f} ppm "
              f"= {100*dco/R/dco2:3.0f}% of the {dco2:.1f} ppm enhancement")

    print("\n===== G2. CO against quoted hemispheric brackets =====")
    print(f"   quoted: SH surface {CO_SH[0]}-{CO_SH[1]}, global mean {CO_GLOBAL[0]}-{CO_GLOBAL[1]}, "
          f"NH winter {CO_NH_WINTER[0]}-{CO_NH_WINTER[1]} ppb")


if __name__ == "__main__":
    main()
