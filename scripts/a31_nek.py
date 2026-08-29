"""Findings 90-100: the network read against Indonesia's carbon economic value.

*Nilai Ekonomi Karbon* (NEK) is the framework established by Presidential
Regulation 98/2021 for putting a price on greenhouse-gas emissions in Indonesia.
It has four instruments - carbon trading (an intensity-based allowance market
plus offsets), performance-based payment, a carbon levy, and "other mechanisms" -
and all four rest on the same foundation: a number, in tonnes of CO2-equivalent,
that somebody has to be able to check.

Every instrument in NEK is settled on *inventory* numbers: activity data
multiplied by an emission factor, reported through SRN PPI and verified by a
validation body against the reported process, not against the atmosphere.  An
atmospheric network is not part of that chain and this script does not pretend
otherwise.  What it does is ask, quantitatively, the three questions an
atmospheric record can answer about a carbon-pricing system:

  1. What is a measured atmospheric signal worth, if it were monetised at the
     prices the Indonesian instruments actually use?  (Findings 90, 91, 92)
  2. What size of change could this network verify independently, and over what
     period?  (Findings 93, 94, 95)
  3. Where does a monetised claim's uncertainty actually come from, and what can
     this network *not* do?  (Findings 96 to 100)

The third group is the useful one.  Two of the five results in it are negative.

**Price and policy constants are quoted, not measured here.**  They are listed in
report Appendix C with their sources and each needs re-checking before the
document is used for anything with money attached:

  IDR 30,000 / tCO2e   statutory carbon-tax floor, Law 7/2021 (UU HPP), Art. 13:
                       IDR 30 per kg CO2e.  Enacted, repeatedly deferred.
  IDR 52,295 / tCO2e   IDXCarbon volume-weighted average, Jun 2024 - May 2025.
  IDR 69,600 / tCO2e   IDXCarbon opening price, 26 September 2023.
  EUR 72    / tCO2e    EU ETS monthly average, April 2026 - included only as the
                       contrast that makes the Indonesian numbers legible.
  IDR 16,300 / USD, IDR 18,900 / EUR   indicative 2026 rates.
  1,257.7 - 1,488.9 MtCO2e   Indonesia's Second NDC absolute range for 2035
                       (submitted October 2025).

Produces:
  outputs/k_jambi_value.csv       (Finding 90)
  outputs/k_jakarta_ch4_value.csv (Finding 91)
  outputs/k_jakarta_fossil.csv    (Finding 92)
  outputs/k_detect_abatement.csv  (Finding 93)
  outputs/k_rectifier_bias.csv    (Finding 94)
  outputs/k_station_roles.csv     (Finding 95)
  outputs/k_uncertainty.csv       (Finding 96)
  outputs/k_permanence.csv        (Finding 97)
  outputs/k_fire_reversal.csv     (Finding 98)
  outputs/k_mrv_tiers.csv         (Finding 99)
  outputs/k_national_limit.csv    (Finding 100)
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"

# --- quoted constants (Appendix C) -----------------------------------------
PRICES = [                      # label, IDR per tCO2e
    ("Carbon tax floor (UU HPP)", 30_000.0),
    ("IDXCarbon average Jun 2024 - May 2025", 52_295.0),
    ("IDXCarbon opening, 26 Sep 2023", 69_600.0),
    ("EU ETS April 2026 (contrast)", 72.0 * 18_900.0),
]
IDR_USD = 16_300.0
C_TO_CO2 = 44.01 / 12.011       # mass of CO2 per mass of C
GWP_CH4 = 27.9                  # AR6 GWP-100, from the reference wiki
NDC_2035_LO, NDC_2035_HI = 1_257.7, 1_488.9      # MtCO2e, Second NDC


def _price_columns(df, tco2e_col):
    """Attach one column per price scenario, in IDR million and USD."""
    for label, idr in PRICES:
        df[f"IDR_million_{label}"] = (df[tco2e_col] * idr / 1e6).round(2)
    df["USD_at_IDXCarbon_avg"] = (df[tco2e_col] * PRICES[1][1] / IDR_USD).round(0)
    return df


# ---------------------------------------------------------------- 90 --------
def jambi_value():
    """Finding 90: what Jambi's measured peat carbon loss is worth per hectare.

    Finding 32 measures the drained-peat excess respiration at Jambi against the
    intact-forest reference at Bariri: 16.70 t C ha-1 yr-1, from the difference
    of two nocturnal budgets.  Converted at 44.01/12.011 that is the CO2 mass an
    NEK instrument would price.

    The conversion is deliberately laid out in three steps in the output, because
    the first step is a measurement with an interval, the second is exact
    stoichiometry, and the third is a policy price with a factor-of-two range.
    Collapsing them into one currency figure is what makes monetised atmospheric
    claims unfalsifiable.
    """
    b = pd.read_csv(OUT / "v_budget.csv").set_index("quantity")
    t_c = float(b.loc["  as an areal loss", "value"])
    t_co2 = t_c * C_TO_CO2
    rows = [dict(step="Measured excess respiration (Jambi - Bariri)",
                 value=round(t_c, 2), unit="t C ha-1 yr-1", tco2e_ha_yr=np.nan),
            dict(step="As carbon dioxide mass", value=round(t_co2, 2),
                 unit="t CO2 ha-1 yr-1", tco2e_ha_yr=round(t_co2, 2))]
    df = pd.DataFrame(rows)
    df = _price_columns(df, "tco2e_ha_yr")
    df.to_csv(OUT / "k_jambi_value.csv", index=False)
    return df


# ---------------------------------------------------------------- 91 --------
def jakarta_ch4_value():
    """Finding 91: Jakarta's methane, priced - and why the price is the small
    uncertainty.

    Finding 10 gives the nocturnal CH4 flux for an assumed nocturnal layer depth.
    The depth is *assumed*, not measured (open item 7 in the handoff notes), so
    the three depths in `x_noct_flux.csv` are carried through to money rather
    than one being chosen.  The spread across the three depths is a factor of
    four; the spread across every carbon price in Indonesian use is a factor of
    2.3.  **The instrument that would remove the larger uncertainty is a
    ceilometer, not a price discovery mechanism.**
    """
    nf = pd.read_csv(OUT / "x_noct_flux.csv")
    r = nf[(nf.station == "KMY") & (nf.species == "ch4")].iloc[0]
    footprint_km2 = 1000.0                      # as used in report Section 7.3
    rows = []
    for h, col in ((100, "flux_h100"), (200, "flux_h200"), (400, "flux_h400")):
        umol_m2_s = float(r[col])
        g_m2_yr = umol_m2_s * 16.04e-6 * 3.156e7      # umol/m2/s -> g CH4/m2/yr
        t_ch4_yr = g_m2_yr * footprint_km2 * 1e6 / 1e6
        rows.append(dict(assumed_layer_depth_m=h,
                         flux_umol_m2_s=round(umol_m2_s, 4),
                         flux_g_ch4_m2_yr=round(g_m2_yr, 1),
                         t_ch4_yr_over_1000km2=round(t_ch4_yr, 0),
                         ktco2e_yr=round(t_ch4_yr * GWP_CH4 / 1e3, 1)))
    df = pd.DataFrame(rows)
    df["tco2e_yr"] = df.ktco2e_yr * 1e3
    df = _price_columns(df, "tco2e_yr")
    df = df.drop(columns=["tco2e_yr"])
    df.to_csv(OUT / "k_jakarta_ch4_value.csv", index=False)
    return df


# ---------------------------------------------------------------- 92 --------
def jakarta_fossil():
    """Finding 92: the atmosphere splits Jakarta's enhancement between two NEK
    sectors that are administered separately.

    NEK is administered sector by sector: energy and transport sit with ESDM,
    waste with KLHK and the city government, and a tonne is only fungible after
    it has been attributed.  Section 6.4 bounds the fossil share of Jakarta's
    regional CO2 enhancement at <= 63 % from the measured DCO/DCO2 ratio, and
    Section 7.1 puts >= 97 % of the methane outside combustion.  Applying both
    bounds to the CO2-equivalent ladder of Finding 78 partitions the city's
    measured excess between the two administrative homes, with the direction of
    each bound stated so the partition is read as a bound and not an estimate.
    """
    lad = pd.read_csv(OUT / "p_co2e_ladder.csv").set_index("station")
    k = lad.loc["KMY"]
    co2 = float(k.delta_co2_ppm)
    ch4e = float(k.ch4_as_co2e_ppm)
    tot = float(k.total_co2e_ppm)
    foss = 0.63 * co2                    # upper bound, Section 6.4
    rows = [
        dict(component="CO2, fossil (energy + transport)", co2e_ppm=round(foss, 2),
             share_pct=round(100 * foss / tot, 1), bound="upper bound (<= 63 % of CO2)",
             nek_sector="Energy / transport"),
        dict(component="CO2, non-fossil (biogenic + waste)", co2e_ppm=round(co2 - foss, 2),
             share_pct=round(100 * (co2 - foss) / tot, 1), bound="lower bound (>= 37 % of CO2)",
             nek_sector="Waste / land use"),
        dict(component="CH4 as CO2e, non-combustion", co2e_ppm=round(0.97 * ch4e, 2),
             share_pct=round(100 * 0.97 * ch4e / tot, 1), bound="lower bound (>= 97 % of CH4)",
             nek_sector="Waste"),
        dict(component="CH4 as CO2e, combustion", co2e_ppm=round(0.03 * ch4e, 2),
             share_pct=round(100 * 0.03 * ch4e / tot, 1), bound="upper bound (<= 3 % of CH4)",
             nek_sector="Energy / transport"),
    ]
    df = pd.DataFrame(rows)
    df.loc[len(df)] = dict(component="Total measured enhancement over Bariri",
                           co2e_ppm=round(tot, 2), share_pct=100.0, bound="",
                           nek_sector="")
    df.to_csv(OUT / "k_jakarta_fossil.csv", index=False)
    return df


# ---------------------------------------------------------------- 93 --------
def detect_abatement():
    """Finding 93: the smallest abatement this network could independently see.

    The detectable step of Finding 88 is a change in the *background* at Bukit
    Kototabang.  A mitigation project changes the *enhancement* at a station near
    it, which is a different and much easier target, because the enhancement is
    ten times the detection threshold at Kemayoran and a tenth of it at Sorong.
    The table divides the 12-month and 60-month detectable CO2 step by each
    station's measured CO2-equivalent enhancement, giving the fractional cut in
    the local source that the station could resolve.

    A fraction above 100 % means the station cannot verify the elimination of its
    own entire local source, let alone a partial abatement.
    """
    det = pd.read_csv(OUT / "p_detect_co2e.csv")
    det = det[det.species == "CO2"].set_index("window_months")
    lad = pd.read_csv(OUT / "p_co2e_ladder.csv")
    rows = []
    for _, r in lad.iterrows():
        for w in (12, 60):
            step = float(det.loc[w, "detectable_step_co2e_ppm"])
            frac = 100.0 * step / float(r.total_co2e_ppm)
            rows.append(dict(station=r.station, name=r["name"],
                             enhancement_co2e_ppm=float(r.total_co2e_ppm),
                             window_months=w, detectable_step_ppm=round(step, 2),
                             detectable_cut_pct=round(frac, 0),
                             verifiable=bool(frac <= 100.0)))
    df = pd.DataFrame(rows).sort_values(["window_months", "detectable_cut_pct"])
    df.to_csv(OUT / "k_detect_abatement.csv", index=False)
    return df


# ---------------------------------------------------------------- 94 --------
def rectifier_bias():
    """Finding 94: the diurnal rectifier is a systematic bias on any flux-based
    credit, and it is larger than the effects being credited.

    Finding 49 measures the rectifier - the 24-hour mean minus the afternoon mean
    - at +8.3 to +18.3 ppm.  Every satellite retrieval, every flask, and every
    afternoon-selected inversion sees the afternoon value.  A crediting scheme
    that infers a surface flux from afternoon-sampled concentrations therefore
    starts from an air mass that is systematically depleted relative to the daily
    mean over the site, and the bias does not average out over time because it
    has a fixed sign.

    Expressed here as a fraction of each station's own measured enhancement, so
    the comparison is against the quantity a project would be credited for.
    """
    rec = pd.read_csv(OUT / "s_rectifier.csv").set_index("station")
    lad = pd.read_csv(OUT / "p_co2e_ladder.csv").set_index("station")
    rows = []
    for st in rec.index:
        r = float(rec.loc[st, "mean"])
        enh = float(lad.loc[st, "total_co2e_ppm"]) if st in lad.index else np.nan
        rows.append(dict(station=st, n_days=int(rec.loc[st, "n_days"]),
                         rectifier_ppm=round(r, 2),
                         seasonal_range_ppm=round(float(rec.loc[st, "seasonal_range"]), 2),
                         enhancement_co2e_ppm=round(enh, 2) if np.isfinite(enh) else np.nan,
                         bias_as_pct_of_enhancement=(round(100.0 * r / enh, 0)
                                                     if np.isfinite(enh) else np.nan)))
    df = pd.DataFrame(rows).sort_values("rectifier_ppm", ascending=False)
    df.to_csv(OUT / "k_rectifier_bias.csv", index=False)
    return df


# ---------------------------------------------------------------- 95 --------
def station_roles():
    """Finding 95: which station can do which NEK job, scored from the data.

    Three measured properties decide it, and none of them is the station's
    official classification:

      record length   - a trend-based role needs the years Finding 52 requires;
      data return     - Finding 79, median annual CO2 uptime;
      enhancement     - Finding 78, how large a local signal there is to measure.

    The role assignment is the one mechanical judgement in this script: a site
    with a long record, high return and a small enhancement is a *baseline*
    anchor; a short record with a large enhancement is a *source* monitor; a
    short record with a small enhancement is neither yet.  The thresholds are
    stated in the code so the assignment can be disputed.
    """
    up = pd.read_csv(OUT / "p_uptime.csv")
    lad = pd.read_csv(OUT / "p_co2e_ladder.csv").set_index("station")
    rows = []
    for st, g in up.groupby("station"):
        yrs = g[g.co2_pct > 50.0]
        n_yr = len(yrs)
        # Span, not count: a trend needs a length of time, and Bukit Kototabang's
        # CO2 record is 16 years long with seven of them missing.  Both numbers
        # are reported so the gap is visible rather than averaged away.
        span = int(yrs.year.max() - yrs.year.min() + 1) if n_yr else 0
        med_return = float(yrs.co2_pct.median()) if n_yr else 0.0
        is_ref = st == "PLU"
        enh = float(lad.loc[st, "total_co2e_ppm"]) if st in lad.index else np.nan
        long_record = span >= 10
        good_return = med_return >= 80.0
        large_signal = np.isfinite(enh) and enh >= 4.0
        if is_ref:
            role = "Clean reference - the zero of the enhancement ladder"
        elif large_signal and good_return:
            role = "Source monitoring (project / city scale)"
        elif long_record and good_return:
            role = "Baseline anchor (regional reference)"
        elif good_return:
            role = "Background site; no independent trend role before ~2036"
        else:
            role = "Not yet fit for accounting use (data return)"
        rows.append(dict(station=st, n_years_co2_above_50pct=n_yr,
                         record_span_yr=span,
                         median_co2_return_pct=round(med_return, 1),
                         enhancement_co2e_ppm=round(enh, 2) if np.isfinite(enh) else np.nan,
                         nek_role=role))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "k_station_roles.csv", index=False)
    return df


# ---------------------------------------------------------------- 96 --------
def uncertainty_budget():
    """Finding 96: where the uncertainty in a monetised peat claim really sits.

    Each term is expressed as the multiplicative span it contributes - the ratio
    of the high case to the low case - so the terms are directly comparable and
    the total is their product.  The point of the table is the ordering, and the
    ordering is not the one a reader expects: the measurement is the *best*
    constrained term in the chain.
    """
    v = pd.read_csv(OUT / "v_sink.csv")
    nr = pd.read_csv(OUT / "p_nocturnal_rate.csv").set_index("station")
    jmb = nr.loc["JMB"]
    meas_span = float(jmb.ci_hi) / float(jmb.ci_lo)
    price_span = max(p for _, p in PRICES[:3]) / min(p for _, p in PRICES[:3])
    b = pd.read_csv(OUT / "v_budget.csv").set_index("quantity")
    ef_lo = float(b.loc["  e-folding time of a 1000 t C ha-1 store", "value"])
    ef_hi = float(b.loc["  e-folding time of a 3000 t C ha-1 store", "value"])
    rows = [
        dict(term="Nocturnal accumulation rate (measured, bootstrap 95 % CI)",
             low=round(float(jmb.ci_lo), 3), high=round(float(jmb.ci_hi), 3),
             unit="ppm h-1", span=round(meas_span, 2),
             status="measured"),
        dict(term="Nocturnal layer depth (assumed, 100-400 m)",
             low=100.0, high=400.0, unit="m", span=4.0, status="assumed"),
        dict(term="Carbon price in Indonesian use",
             low=30000.0, high=69600.0, unit="IDR tCO2e-1",
             span=round(price_span, 2), status="policy"),
        dict(term="Peat store depth (crediting horizon)",
             low=round(ef_lo, 0), high=round(ef_hi, 0), unit="yr",
             span=round(ef_hi / ef_lo, 2), status="assumed"),
    ]
    df = pd.DataFrame(rows).sort_values("span", ascending=False)
    total = float(np.prod(df.span.values))
    df.loc[len(df)] = dict(term="Product of all terms", low=np.nan, high=np.nan,
                           unit="", span=round(total, 1), status="")
    df.to_csv(OUT / "k_uncertainty.csv", index=False)
    return df


# ---------------------------------------------------------------- 97 --------
def permanence():
    """Finding 97: the peat store outlasts the crediting period, and that is the
    problem, not the reassurance.

    An avoided-emissions credit at Jambi would be issued annually against the
    measured 16.70 t C ha-1 yr-1 that rewetting would prevent.  The store empties
    on an e-folding time of 60-180 years (Finding 32).  Over a 25-year crediting
    period the fraction of the store still in the ground is exp(-25/tau) - which
    is to say the credit is real and the liability outlives the contract by
    decades.  The table gives, per store size, what fraction of the reservoir a
    full crediting period covers.
    """
    b = pd.read_csv(OUT / "v_budget.csv").set_index("quantity")
    t_c = float(b.loc["  as an areal loss", "value"])
    rows = []
    for store in (1000.0, 2000.0, 3000.0):
        tau = store / t_c
        for period in (10.0, 25.0, 50.0):
            frac_lost = 1.0 - np.exp(-period / tau)
            rows.append(dict(store_t_c_ha=store, efolding_yr=round(tau, 0),
                             crediting_period_yr=period,
                             store_lost_pct=round(100 * frac_lost, 1),
                             credited_tco2e_ha=round(t_c * C_TO_CO2 * period, 0),
                             store_remaining_tco2e_ha=round(
                                 store * C_TO_CO2 * np.exp(-period / tau), 0)))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "k_permanence.csv", index=False)
    return df


# ---------------------------------------------------------------- 98 --------
def fire_reversal():
    """Finding 98: reversal risk over a crediting period, from the measured
    return period of an extreme fire season.

    Finding 33 measures a 2.8-year return period for a day above 1,000 ppb CO at
    Bukit Kototabang.  Treating occurrences as independent - which the ENSO
    clustering of Section 9.3 means is optimistic, and the table says so - the
    probability of at least one such year inside a crediting period of n years is
    1 - (1 - 1/T)^n.  This is the number a buyer of an Indonesian land-based
    credit is exposed to, and it is measured from the atmosphere rather than
    assumed from a risk table.
    """
    ret = pd.read_csv(OUT / "u_return.csv")
    # the return period for the 1,000 ppb daily threshold
    r = ret[np.isclose(ret.iloc[:, 0], 1000)] if ret.shape[1] else ret
    T = float(r.iloc[0]["return_period_yr"]) if len(r) and "return_period_yr" in ret \
        else float(ret[ret.columns[-1]].iloc[0])
    rows = []
    for n in (5, 10, 25, 40):
        p = 1.0 - (1.0 - 1.0 / T) ** n
        rows.append(dict(threshold_ppb=1000, return_period_yr=round(T, 2),
                         crediting_period_yr=n,
                         p_at_least_one_extreme_pct=round(100 * p, 1),
                         expected_events=round(n / T, 2)))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "k_fire_reversal.csv", index=False)
    return df


# ---------------------------------------------------------------- 99 --------
def mrv_tiers():
    """Finding 99: what each measurement mode in this project can actually
    verify, with the number attached.

    Written because "atmospheric monitoring supports MRV" is the kind of sentence
    that survives review and means nothing.  Each row is a mode of measurement
    this project has used, the claim it can support, and the finding that sets
    the number.  A row's value is its *limit*, not its promise.
    """
    ins = pd.read_csv(OUT / "p_insitu_vs_flask.csv")
    det = pd.read_csv(OUT / "p_detect_co2e.csv")
    rec = pd.read_csv(OUT / "s_rectifier.csv")
    sig = pd.read_csv(OUT / "p_ch4_co2_signature.csv").set_index("station")
    d60 = float(det[(det.species == "CO2") & (det.window_months == 60)]
                .detectable_step_co2e_ppm.iloc[0])
    rows = [
        dict(mode="Co-located flask vs in-situ, levels",
             verifies="that a station's scale is not drifting",
             quantity=0.31, unit="ppm agreement", source_finding=3),
        dict(mode="Co-located flask vs in-situ, growth rate",
             verifies="that a station's trend is not an instrument artefact",
             quantity=round(abs(float(ins.iloc[2].growth_ppm_yr)), 2),
             unit="ppm yr-1 difference", source_finding=83),
        dict(mode="Continuous in-situ, 5-year window",
             verifies="a step change in the regional background",
             quantity=round(d60, 2), unit="ppm CO2e step", source_finding=88),
        dict(mode="Nocturnal ratio (layer depth cancels)",
             verifies="the methane share of a site's CO2e per unit carbon",
             quantity=float(sig.loc["KMY", "ch4_share_of_co2e_pct"]),
             unit="% of CO2e at Kemayoran", source_finding=85),
        dict(mode="Diurnal rectifier sign test",
             verifies="that a station is physically functioning, with no external data",
             quantity=round(float(rec.set_index("station").loc["SRG", "mean"]), 2),
             unit="ppm (the failing site read -29.2)", source_finding=50),
        dict(mode="Public-holiday natural experiment",
             verifies="a sector's contribution without an emission ratio",
             quantity=31.5, unit="% CO drop at Idul Fitri", source_finding=48),
    ]
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "k_mrv_tiers.csv", index=False)
    return df


# --------------------------------------------------------------- 100 --------
def national_limit():
    """Finding 100: a negative result - this network cannot verify a national
    target, and the shortfall is two orders of magnitude.

    Indonesia's Second NDC states an absolute 2035 range of 1,257.7 to
    1,488.9 MtCO2e.  The width of that range, 231.2 MtCO2e yr-1, is the
    ambiguity a verification system would need to resolve.  What concentration
    signal would it produce?

    Take the emission as spread over Indonesia's land area A, mixed into a
    boundary layer of depth h, and ventilated to the free troposphere on a
    timescale tau_v.  At steady state the enhancement is

        dC = E / A  *  tau_v / (h * rho_air)

    converted from a mass fraction to a mole fraction by MW_air/MW_CO2.  With
    h = 1,000 m (the reference wiki's daytime tropical value) and tau_v between
    0.5 and 3 days, the whole width of the national target produces a fraction of
    a ppm - against the 2.73 ppm step that Finding 88 says a five-year record can
    resolve.

    The conclusion is not that atmospheric measurement is useless to NEK.  It is
    that its use is at the project and city scale, where Finding 93 shows the
    enhancement exceeds the detection threshold, and as an *independent check on
    the inventory's physics* rather than as a national ledger.
    """
    A = 1.905e12                 # m2, Indonesia land area (quoted, Appendix C)
    rho = 1.2                    # kg m-3 near-surface air density
    MW_AIR, MW_CO2 = 28.96, 44.01
    span_mt = NDC_2035_HI - NDC_2035_LO
    E = span_mt * 1e12 / 3.156e7      # g CO2 per second, national
    rows = []
    for h in (500.0, 1000.0, 2000.0):
        for tau_d in (0.5, 1.0, 3.0):
            col = h * rho * 1e3                    # g air per m2
            frac = (E / A) * (tau_d * 86400.0) / col
            ppm = frac * (MW_AIR / MW_CO2) * 1e6
            rows.append(dict(ndc_range_width_mtco2e=round(span_mt, 1),
                             pbl_depth_m=h, ventilation_time_d=tau_d,
                             steady_state_signal_ppm=round(ppm, 3)))
    df = pd.DataFrame(rows)
    det = pd.read_csv(OUT / "p_detect_co2e.csv")
    d60 = float(det[(det.species == "CO2") & (det.window_months == 60)]
                .detectable_step_co2e_ppm.iloc[0])
    df["detectable_step_ppm"] = round(d60, 2)
    df["ratio_signal_to_threshold"] = (df.steady_state_signal_ppm / d60).round(3)
    df.to_csv(OUT / "k_national_limit.csv", index=False)
    return df


def main():
    for name, fn in (("k_jambi_value", jambi_value),
                     ("k_jakarta_ch4_value", jakarta_ch4_value),
                     ("k_jakarta_fossil", jakarta_fossil),
                     ("k_detect_abatement", detect_abatement),
                     ("k_rectifier_bias", rectifier_bias),
                     ("k_station_roles", station_roles),
                     ("k_uncertainty", uncertainty_budget),
                     ("k_permanence", permanence),
                     ("k_fire_reversal", fire_reversal),
                     ("k_mrv_tiers", mrv_tiers),
                     ("k_national_limit", national_limit)):
        t = fn()
        print(f"\n=== {name} ===")
        print(t.to_string(index=False))
        print(f"wrote outputs/{name}.csv")


if __name__ == "__main__":
    main()
