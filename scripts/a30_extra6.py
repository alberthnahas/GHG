"""Findings 78-89: what the network measures when it is asked policy questions.

This pass was written to support Part VI (the carbon economic value, *Nilai
Ekonomi Karbon*).  Everything a carbon-pricing instrument needs from an
atmospheric network is one of three things: a signal converted into the currency
of the accounting system (CO2-equivalent), a statement about how reliably the
station delivers data, or a statement about what size of change the station could
see at all.  None of those existed in this project as separate results; they were
implicit in a dozen findings written for atmospheric readers.

Nothing here introduces new raw data.  Six of the twelve are re-expressions of
existing measurements in a different unit or a different aggregation, and they
say so; the value they add is that a policy reader does not have to do the
conversion, and the conversion is then verifiable.  Where a result restates an
existing finding, the docstring names it.

GWP-100 values are AR6 and come from the local atmospheric-science reference
wiki (`wiki/concepts/global-warming-potential.md`): CH4 27.9, N2O 273,
SF6 25,200.  They are quoted, not measured here, and are listed in report
Appendix C.

Produces:
  outputs/p_co2e_ladder.csv        (Finding 78)
  outputs/p_uptime.csv             (Finding 79)
  outputs/p_clean_fraction.csv     (Finding 80)
  outputs/p_species_coupling.csv   (Finding 81)
  outputs/p_persistence.csv        (Finding 82)
  outputs/p_insitu_vs_flask.csv    (Finding 83)
  outputs/p_nocturnal_rate.csv     (Finding 84)
  outputs/p_ch4_co2_signature.csv  (Finding 85)
  outputs/p_kmy_weekend_co2e.csv   (Finding 86)
  outputs/p_global_coupling.csv    (Finding 87)
  outputs/p_detect_co2e.csv        (Finding 88)
  outputs/p_amplitude_stability.csv (Finding 89)
"""
from pathlib import Path

import numpy as np
import pandas as pd

import ghg_common as G
import noaa_flask as NF

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"

# AR6 GWP-100, from the reference wiki.  Quoted, not measured (Appendix C).
GWP100 = {"co2": 1.0, "ch4": 27.9, "n2o": 273.0, "sf6": 25200.0}
# Molar masses, g/mol - needed to turn a mixing-ratio difference into a mass one.
MW = {"co2": 44.01, "ch4": 16.04, "co": 28.01, "n2o": 44.01, "sf6": 146.06}
MW_AIR = 28.96


def _afternoon(d):
    return d[(d.hour_local >= 12) & (d.hour_local <= 16)]


def _monthly_bg(d, sp):
    s = G.clean(d, sp).dropna(subset=[sp])
    s = _afternoon(s)
    m = s.groupby(s.time_local.dt.to_period("M"))[sp].quantile(0.20)
    m.index = m.index.to_timestamp()
    return m


def _lag1(x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)] - np.nanmean(x)
    if len(x) < 5:
        return 0.0
    return float(np.corrcoef(x[:-1], x[1:])[0, 1])


# ---------------------------------------------------------------- 78 --------
def co2e_ladder():
    """Finding 78: the enhancement ladder in the currency of carbon accounting.

    Section 11.1 reports each station's afternoon background minus Bariri's in
    ppm and ppb.  Those units answer an atmospheric question.  A carbon-pricing
    instrument counts CO2-equivalent, so the same three differences are converted
    to a CO2-equivalent mixing-ratio excess:

        dCO2e = dCO2 + GWP_CH4 * dCH4 * (MW_CH4/MW_CO2) ... no.

    The conversion that is actually correct on a *mixing ratio* is simpler than
    a mass conversion, because GWP is defined per unit mass but a mixing-ratio
    difference is per unit mole.  A mole of CH4 and a mole of CO2 occupy the same
    volume, so the mass ratio between a 1 ppb CH4 excess and a 1 ppm CO2 excess
    is (16.04/44.01) * 1e-3.  Hence

        dCO2e[ppm] = dCO2 + dCH4[ppb] * 1e-3 * (MW_CH4/MW_CO2) * GWP_CH4.

    CO carries no GWP in the Paris accounting framework (it is an indirect
    forcer only) and is therefore reported alongside but not summed - stating
    that explicitly is half the point of the table.

    This is a re-expression of Finding 36's ladder, not a new measurement.
    """
    lad = pd.read_csv(OUT / "x_ladder.csv")
    piv = lad.pivot(index="station", columns="species", values="delta")
    sep = lad.pivot(index="station", columns="species", values="se")
    rows = []
    for st in ("BKT", "SRG", "JMB", "KMY"):
        if st not in piv.index:
            continue
        d_co2 = float(piv.loc[st, "co2"])
        d_ch4 = float(piv.loc[st, "ch4"])
        ch4_e = d_ch4 * 1e-3 * (MW["ch4"] / MW["co2"]) * GWP100["ch4"]
        tot = d_co2 + ch4_e
        # errors propagate in quadrature; the two backgrounds are independent
        e_co2 = float(sep.loc[st, "co2"])
        e_ch4 = float(sep.loc[st, "ch4"]) * 1e-3 * (MW["ch4"] / MW["co2"]) * GWP100["ch4"]
        rows.append(dict(
            station=st, name=G.STATIONS[st][0],
            delta_co2_ppm=round(d_co2, 2),
            delta_ch4_ppb=round(d_ch4, 1),
            ch4_as_co2e_ppm=round(ch4_e, 2),
            total_co2e_ppm=round(tot, 2),
            se_co2e_ppm=round(float(np.hypot(e_co2, e_ch4)), 2),
            ch4_share_pct=round(100.0 * ch4_e / tot, 1),
            delta_co_ppb_not_counted=round(float(piv.loc[st, "co"]), 1),
        ))
    df = pd.DataFrame(rows).sort_values("total_co2e_ppm")
    df.to_csv(OUT / "p_co2e_ladder.csv", index=False)
    return df


# ---------------------------------------------------------------- 79 --------
def uptime(d):
    """Finding 79: data return, per station-year, on the three core species.

    An MRV system buys continuity, not peak precision: a station delivering
    60 % of its hours cannot support an annual mass balance however good those
    hours are.  Uptime is hours with a finite value divided by the hours in the
    station's own coverage window that year, so a station that started in
    November is not penalised for the ten months before it existed.
    """
    rows = []
    for st in G.ORDER:
        s = d[d.station == st]
        for y, g in s.groupby("year"):
            t0, t1 = g.time_local.min(), g.time_local.max()
            possible = (t1 - t0) / pd.Timedelta(hours=1) + 1
            rows.append(dict(
                station=st, year=int(y), possible_hours=int(possible),
                co2_pct=round(100.0 * g.co2.notna().sum() / possible, 1),
                ch4_pct=round(100.0 * g.ch4.notna().sum() / possible, 1),
                co_pct=round(100.0 * g.co.notna().sum() / possible, 1),
            ))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "p_uptime.csv", index=False)
    return df


# ---------------------------------------------------------------- 80 --------
def clean_fraction(d):
    """Finding 80: how much of each record is background air - and why that does
    not tell you what kind of site it is.

    The hypothesis this was written to test is the obvious one: that a station's
    usefulness as a *baseline* site can be read off the fraction of its record
    that is background air, so a siting decision for a carbon-accounting network
    could be made from the data alone.  It fails.  The metric
    is the fraction of *all* hours within 2 ppm of the site's own 30-day
    afternoon 20th-percentile CO2 background - i.e. how often the site sees air
    that carries no detectable local addition.  The baseline is built from
    afternoon hours only (landmine: the two baselines are not interchangeable)
    and then applied to the whole day, so the night, when local emissions
    accumulate, is counted rather than excluded.  The afternoon-only fraction is
    reported beside it, because the difference between the two columns is the
    whole of the discrimination: the megacity and the montane rainforest differ
    by 1.3 points on all hours, which is nothing, and the ranking on the
    all-hours column puts the rainforest *last*.  What separates the sites is the
    afternoon selection, not the site.
    """
    rows = []
    for st in G.ORDER:
        s = G.clean(d[d.station == st], "co2").dropna(subset=["co2"]).copy()
        if len(s) < 500:
            continue
        aft = _afternoon(s).set_index("time_local")["co2"].sort_index()
        bg = aft.rolling("30D", min_periods=12).quantile(0.20)
        s = s.sort_values("time_local")
        b = pd.merge_asof(s[["time_local", "co2"]], bg.rename("bg").reset_index(),
                          on="time_local", direction="nearest",
                          tolerance=pd.Timedelta("15D"))
        b["hour_local"] = s.hour_local.values
        a = b.dropna(subset=["bg"])
        exc = a.co2 - a.bg
        exc_aft = exc[a.hour_local.between(12, 16)]
        rows.append(dict(
            station=st, name=G.STATIONS[st][0], n_hours=len(a),
            median_excess_ppm=round(float(exc.median()), 2),
            p90_excess_ppm=round(float(exc.quantile(0.90)), 2),
            clean_fraction_pct=round(100.0 * float((exc < 2.0).mean()), 1),
            clean_fraction_afternoon_pct=round(100.0 * float((exc_aft < 2.0).mean()), 1),
        ))
    df = pd.DataFrame(rows).sort_values("clean_fraction_pct", ascending=False)
    df.to_csv(OUT / "p_clean_fraction.csv", index=False)
    return df


# ---------------------------------------------------------------- 81 --------
def species_coupling(d):
    """Finding 81: hourly CO2-CH4-CO coupling separates the source types.

    Correlations are computed on hourly *anomalies* from each species' own
    30-day 20th-percentile background, so a shared seasonal cycle cannot create
    the correlation; what is left is co-variation at the timescale of individual
    air masses, which is the timescale on which sources are co-located.
    Spearman is reported alongside Pearson because urban plume distributions are
    strongly skewed.
    """
    from scipy.stats import spearmanr
    rows = []
    for st in G.ORDER:
        s = d[d.station == st].dropna(subset=["co2", "ch4", "co"]).copy()
        if len(s) < 1000:
            continue
        for sp in ("co2", "ch4", "co"):
            s["a_" + sp] = s[sp].values - G.baseline_percentile(s, sp, "30D", 0.20).values
        s = s.dropna(subset=["a_co2", "a_ch4", "a_co"])
        for x, y in (("co2", "ch4"), ("co2", "co"), ("ch4", "co")):
            r = float(np.corrcoef(s["a_" + x], s["a_" + y])[0, 1])
            rho = float(spearmanr(s["a_" + x], s["a_" + y]).statistic)
            rows.append(dict(station=st, pair=f"{x.upper()}-{y.upper()}",
                             n_hours=len(s), pearson_r=round(r, 3),
                             spearman_rho=round(rho, 3)))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "p_species_coupling.csv", index=False)
    return df


# ---------------------------------------------------------------- 82 --------
def persistence():
    """Finding 82: how long an anomaly at Bukit Kototabang remembers itself.

    The e-folding time of the autocorrelation function of monthly flask
    anomalies (residual about a fitted trend-plus-seasonal model).  For a species
    with no local source this is a transport memory; for one with a local source
    it is the memory of the source.  The ordering is the diagnostic: a species
    whose persistence exceeds its transport memory is being reloaded locally.

    Finding 38 gives the same quantity for CO alone at daily resolution (19 d).
    This is the monthly, all-species version, and the two are not the same
    statistic - a point the report makes explicitly rather than reconciling
    numbers that measure different things.
    """
    rows = []
    for sp in NF.SPECIES:
        if not NF.have(sp, "bkt"):
            continue
        s = NF.monthly(sp, "bkt")
        t = (s.index.year + (s.index.month - 0.5) / 12.0).values
        resid = s.values - G.harmonic_fit(t, s.values, n_harm=3, poly=2)["fit"]
        ac = [1.0]
        for k in range(1, 25):
            a, b = resid[:-k], resid[k:]
            ac.append(float(np.corrcoef(a, b)[0, 1]))
        ac = np.array(ac)
        below = np.where(ac < 1 / np.e)[0]
        tau = float(below[0]) if len(below) else np.nan
        if len(below) and below[0] > 0:
            k = below[0]
            tau = k - 1 + (ac[k - 1] - 1 / np.e) / (ac[k - 1] - ac[k])
        rows.append(dict(species=sp.upper(), unit=NF.UNIT[sp], n_months=len(s),
                         lag1_autocorr=round(float(ac[1]), 3),
                         efolding_months=round(tau, 1),
                         residual_sd=round(float(np.nanstd(resid)), 3)))
    df = pd.DataFrame(rows).sort_values("efolding_months", ascending=False)
    df.to_csv(OUT / "p_persistence.csv", index=False)
    return df


# ---------------------------------------------------------------- 83 --------
def insitu_vs_flask(d):
    """Finding 83: the in-situ and flask growth rates at the same site agree.

    Two fully independent measurement systems at Bukit Kototabang - a continuous
    analyser run by BMKG and weekly glass flasks analysed at NOAA GML - are
    reduced to an annual growth rate by the same method and compared.  This is
    the strongest verification statement the network can make, because it is
    co-located: no transport assumption enters.  Finding 3 compares *levels*;
    this compares *trends*, which is what a crediting scheme would rely on.

    The in-situ series is restricted to 2021 onward, after the analyser change
    and after the last flagged CO2 episode, so the comparison is not carrying a
    known instrumental step (landmine: the 2020-12 to 2021-07 episode).
    """
    ins = _monthly_bg(d[d.station == "BKT"], "co2")
    ins = ins[ins.index >= "2021-07-01"]
    fl = NF.monthly("co2", "bkt")
    fl = fl[(fl.index >= ins.index.min()) & (fl.index <= ins.index.max())]
    rows = []
    for label, s in (("in-situ afternoon q20", ins), ("NOAA flask monthly mean", fl)):
        t = (s.index.year + (s.index.month - 0.5) / 12.0).values
        sl, lo, hi = G.theil_sen(t, s.values)
        rows.append(dict(series=label, n_months=len(s),
                         start=str(s.index.min().date()), end=str(s.index.max().date()),
                         growth_ppm_yr=round(float(sl), 3),
                         ci_lo=round(float(lo), 3), ci_hi=round(float(hi), 3)))
    diff = rows[0]["growth_ppm_yr"] - rows[1]["growth_ppm_yr"]
    rows.append(dict(series="difference (in-situ - flask)", n_months=np.nan,
                     start="", end="", growth_ppm_yr=round(diff, 3),
                     ci_lo=np.nan, ci_hi=np.nan))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "p_insitu_vs_flask.csv", index=False)
    return df


# ---------------------------------------------------------------- 84 --------
def nocturnal_rate(d):
    """Finding 84: the nocturnal accumulation rate, with an interval on it.

    Section 7.3 turns this rate into a flux by assuming a mixing depth.  The rate
    itself is measured and the depth is not, so they are separated here: the
    table gives the measured quantity with a bootstrap interval over *nights*,
    and the depth-dependent flux stays in Finding 10 where its assumption is
    stated.  Any monetised claim must inherit the interval on the rate and the
    factor-of-two on the depth separately.
    """
    rng = np.random.default_rng(11)
    rows = []
    for st in G.ORDER:
        s = d[d.station == st].dropna(subset=["co2"]).copy()
        night = s[s.hour_local.isin([20, 21, 22, 23, 0, 1, 2])]
        if len(night) < 200:
            continue
        # per-night slope of CO2 against hour, on nights with >= 5 of the 7 hours
        night = night.assign(nid=(night.time_local - pd.Timedelta(hours=12)).dt.normalize())
        rates = []
        for _, g in night.groupby("nid"):
            if len(g) < 5:
                continue
            h = ((g.time_local - g.time_local.min()) / pd.Timedelta(hours=1)).values
            rates.append(float(np.polyfit(h, g.co2.values, 1)[0]))
        rates = np.array(rates)
        if len(rates) < 50:
            continue
        boot = [np.median(rng.choice(rates, len(rates), replace=True)) for _ in range(600)]
        rows.append(dict(
            station=st, name=G.STATIONS[st][0], n_nights=len(rates),
            median_rate_ppm_h=round(float(np.median(rates)), 3),
            ci_lo=round(float(np.percentile(boot, 2.5)), 3),
            ci_hi=round(float(np.percentile(boot, 97.5)), 3),
            pct_nights_positive=round(100.0 * float((rates > 0).mean()), 1),
        ))
    df = pd.DataFrame(rows).sort_values("median_rate_ppm_h", ascending=False)
    df.to_csv(OUT / "p_nocturnal_rate.csv", index=False)
    return df


# ---------------------------------------------------------------- 85 --------
def ch4_co2_signature(d):
    """Finding 85: the nocturnal CH4:CO2 molar ratio as a source signature.

    Under a shallow nocturnal layer the two species share the same dilution, so
    their ratio of accumulation is the ratio of their surface fluxes and the
    layer depth cancels - the one flux quantity in this project that does not
    inherit the factor-of-two.  Reported in ppb CH4 per ppm CO2 and converted to
    a CO2-equivalent share, which is the form an inventory needs: it says what
    fraction of a site's climate forcing per unit of respired or burnt carbon is
    methane.
    """
    rows = []
    for st in G.ORDER:
        s = d[d.station == st].dropna(subset=["co2", "ch4"]).copy()
        night = s[s.hour_local.isin([20, 21, 22, 23, 0, 1, 2])]
        night = night.assign(nid=(night.time_local - pd.Timedelta(hours=12)).dt.normalize())
        ratios = []
        for _, g in night.groupby("nid"):
            if len(g) < 5:
                continue
            a = np.polyfit(np.arange(len(g)), g.co2.values, 1)[0]
            b = np.polyfit(np.arange(len(g)), g.ch4.values, 1)[0]
            if a > 0.2:                      # only nights that actually accumulate
                ratios.append(b / a)
        if len(ratios) < 50:
            continue
        r = np.array(ratios)
        med = float(np.median(r))
        co2e = med * 1e-3 * (MW["ch4"] / MW["co2"]) * GWP100["ch4"]
        rows.append(dict(station=st, name=G.STATIONS[st][0], n_nights=len(r),
                         ch4_per_co2_ppb_ppm=round(med, 2),
                         iqr_lo=round(float(np.percentile(r, 25)), 2),
                         iqr_hi=round(float(np.percentile(r, 75)), 2),
                         ch4_co2e_per_co2=round(co2e, 3),
                         ch4_share_of_co2e_pct=round(100.0 * co2e / (1.0 + co2e), 1)))
    df = pd.DataFrame(rows).sort_values("ch4_per_co2_ppb_ppm", ascending=False)
    df.to_csv(OUT / "p_ch4_co2_signature.csv", index=False)
    return df


# ---------------------------------------------------------------- 86 --------
def kmy_weekend_co2e(d):
    """Finding 86: Jakarta's weekend signal in CO2-equivalent.

    Finding 64 reports the weekend drop in the CO rush-hour peak, which is a
    tracer statement.  What an emissions inventory wants is the CO2-equivalent
    of the weekday-minus-weekend difference across all three species, because
    that is the quantity a transport-sector measure would be credited against.
    The difference is taken on the 06:00-09:00 rush window against the same
    day's 12:00-16:00 afternoon, so the comparison is internal to each day and
    a seasonal drift cannot enter.
    """
    s = d[d.station == "KMY"].dropna(subset=["co2", "ch4"]).copy()
    rush = s[s.hour_local.between(6, 9)]
    aft = s[s.hour_local.between(12, 16)]
    r = rush.groupby(rush.date)[["co2", "ch4", "co"]].median()
    a = aft.groupby(aft.date)[["co2", "ch4", "co"]].median()
    j = (r - a).dropna()
    j["dow"] = j.index.dayofweek
    rows = []
    for label, mask in (("weekday (Mon-Fri)", j.dow < 5), ("weekend (Sat-Sun)", j.dow >= 5)):
        g = j[mask]
        rows.append(dict(group=label, n_days=len(g),
                         co2_excess_ppm=round(float(g.co2.median()), 2),
                         ch4_excess_ppb=round(float(g.ch4.median()), 1),
                         co_excess_ppb=round(float(g.co.median()), 1)))
    d_co2 = rows[0]["co2_excess_ppm"] - rows[1]["co2_excess_ppm"]
    d_ch4 = rows[0]["ch4_excess_ppb"] - rows[1]["ch4_excess_ppb"]
    d_co = rows[0]["co_excess_ppb"] - rows[1]["co_excess_ppb"]
    co2e = d_co2 + d_ch4 * 1e-3 * (MW["ch4"] / MW["co2"]) * GWP100["ch4"]
    from scipy.stats import mannwhitneyu
    p_co2 = float(mannwhitneyu(j[j.dow < 5].co2.dropna(), j[j.dow >= 5].co2.dropna()).pvalue)
    p_co = float(mannwhitneyu(j[j.dow < 5].co.dropna(), j[j.dow >= 5].co.dropna()).pvalue)
    rows.append(dict(group="weekday - weekend", n_days=np.nan,
                     co2_excess_ppm=round(d_co2, 2), ch4_excess_ppb=round(d_ch4, 1),
                     co_excess_ppb=round(d_co, 1)))
    df = pd.DataFrame(rows)
    df["co2e_ppm"] = [np.nan, np.nan, round(co2e, 2)]
    df["p_co2"] = [np.nan, np.nan, round(p_co2, 4)]
    df["p_co"] = [np.nan, np.nan, round(p_co, 4)]
    df.to_csv(OUT / "p_kmy_weekend_co2e.csv", index=False)
    return df


# ---------------------------------------------------------------- 87 --------
def global_coupling():
    """Finding 87: how much of the site's growth rate is the planet's.

    The annual CO2 growth rate at Bukit Kototabang is regressed on the mean of
    Barrow and South Pole - a two-point global proxy that contains no tropical
    station and so cannot share a regional signal with BKT by construction.  The
    slope near unity and the residual scatter together say what a national
    inventory could ever hope to see in this record: only the residual is local.

    Annual values, one per year, so the Bartlett problem of Finding 51 does not
    arise (lag-1 of the annual series is reported to show it).
    """
    def annual_growth(site):
        """Annual mean from complete years only.

        A year missing three months of a 6.9 ppm seasonal cycle has an annual
        mean biased by more than the growth rate being measured, and the flask
        record has such years.  Requiring 12 months costs a few years and
        removes an artefact that otherwise destroys the correlation entirely -
        on the unfiltered series the regression returns r = -0.04.
        """
        s = NF.monthly("co2", site)
        g = s.groupby(s.index.year)
        y = g.mean()[g.size() == 12]
        d = y.diff()
        return d[np.isin(y.index - 1, y.index)].dropna()

    from scipy.stats import linregress
    brw, spo = annual_growth("brw"), annual_growth("spo")
    rows = []
    # Mauna Loa and Samoa are run through the identical pipeline as controls.
    # If the method were broken, they would fail too; they do not, which is what
    # makes the Bukit Kototabang result a statement about the record rather than
    # about the analysis.
    for site in ("bkt", "mlo", "smo"):
        y = annual_growth(site)
        idx = y.index.intersection(brw.index).intersection(spo.index)
        glob = (brw.loc[idx] + spo.loc[idx]) / 2.0
        y = y.loc[idx]
        lr = linregress(glob.values, y.values)
        resid = y.values - (lr.intercept + lr.slope * glob.values)
        rows.append(dict(
            site=site.upper(), name=NF.SITES[site][0],
            n_years=len(idx), first_year=int(idx.min()), last_year=int(idx.max()),
            slope=round(float(lr.slope), 3), intercept_ppm_yr=round(float(lr.intercept), 3),
            r=round(float(lr.rvalue), 3), p_value=round(float(lr.pvalue), 4),
            residual_sd_ppm_yr=round(float(np.std(resid, ddof=2)), 3),
            variance_explained_pct=round(100.0 * float(lr.rvalue) ** 2, 1),
            residual_lag1=round(_lag1(resid), 3),
        ))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "p_global_coupling.csv", index=False)
    return df


# ---------------------------------------------------------------- 88 --------
def detect_co2e():
    """Finding 88: the detection threshold expressed as a CO2-equivalent step.

    Finding 52 answers "how long until a trend is real".  The complementary
    question, and the one an accounting scheme asks, is "how large a step change
    could this record see at all".  A two-sided test at 95 % with 80 % power on a
    monthly series with lag-1 autocorrelation phi needs a step of

        delta = (1.96 + 0.84) * sigma * sqrt(2/n_eff),   n_eff = n(1-phi)/(1+phi)

    over each of two n-month windows.  The result is reported per species and
    then converted to CO2-equivalent so the six are comparable.
    """
    rows = []
    for sp in NF.SPECIES:
        if not NF.have(sp, "bkt"):
            continue
        s = NF.monthly(sp, "bkt")
        t = (s.index.year + (s.index.month - 0.5) / 12.0).values
        resid = s.values - G.harmonic_fit(t, s.values, n_harm=3, poly=2)["fit"]
        phi, sd = _lag1(resid), float(np.nanstd(resid))
        for n in (12, 60):
            n_eff = n * (1 - phi) / (1 + phi)
            delta = (1.96 + 0.84) * sd * np.sqrt(2.0 / n_eff)
            if sp in GWP100:
                unit_ppm = {"co2": 1.0, "ch4": 1e-3, "n2o": 1e-3, "sf6": 1e-6}[sp]
                co2e = delta * unit_ppm * (MW[sp] / MW["co2"]) * GWP100[sp]
            else:
                co2e = np.nan
            rows.append(dict(species=sp.upper(), unit=NF.UNIT[sp], window_months=n,
                             residual_sd=round(sd, 3), phi=round(phi, 3),
                             n_eff=round(float(n_eff), 1),
                             detectable_step=round(float(delta), 4),
                             detectable_step_co2e_ppm=(round(float(co2e), 4)
                                                       if np.isfinite(co2e) else np.nan)))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "p_detect_co2e.csv", index=False)
    return df


# ---------------------------------------------------------------- 89 --------
def amplitude_stability():
    """Finding 89: is the seasonal amplitude at Bukit Kototabang stable enough
    to serve as a reference?

    A baseline station used for accounting must be stationary in the properties
    the accounting depends on.  The peak-to-peak amplitude of the CO2 seasonal
    cycle is fitted year by year on the flask record and tested for a trend.
    Finding 43 already reports no trend in the seasonal amplitude; this gives the
    year-to-year *scatter*, which is the number a user needs, and states the two
    are the same test seen from two sides rather than independent confirmation.
    """
    rows = []
    for sp in ("co2", "ch4"):
        s = NF.monthly(sp, "bkt")
        amps, years = [], []
        for y, g in s.groupby(s.index.year):
            if len(g) < 12:
                continue
            amps.append(float(g.max() - g.min()))
            years.append(int(y))
        amps, years = np.array(amps), np.array(years)
        sl, lo, hi = G.theil_sen(years.astype(float), amps)
        rows.append(dict(species=sp.upper(), unit=NF.UNIT[sp], n_years=len(amps),
                         mean_amplitude=round(float(amps.mean()), 2),
                         sd_amplitude=round(float(amps.std(ddof=1)), 2),
                         cv_pct=round(100.0 * float(amps.std(ddof=1) / amps.mean()), 1),
                         trend_per_yr=round(float(sl), 4),
                         ci_lo=round(float(lo), 4), ci_hi=round(float(hi), 4),
                         significant=bool(lo * hi > 0)))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "p_amplitude_stability.csv", index=False)
    return df


def main():
    d = G.load_all()
    for name, fn in (("p_co2e_ladder", lambda: co2e_ladder()),
                     ("p_uptime", lambda: uptime(d)),
                     ("p_clean_fraction", lambda: clean_fraction(d)),
                     ("p_species_coupling", lambda: species_coupling(d)),
                     ("p_persistence", lambda: persistence()),
                     ("p_insitu_vs_flask", lambda: insitu_vs_flask(d)),
                     ("p_nocturnal_rate", lambda: nocturnal_rate(d)),
                     ("p_ch4_co2_signature", lambda: ch4_co2_signature(d)),
                     ("p_kmy_weekend_co2e", lambda: kmy_weekend_co2e(d)),
                     ("p_global_coupling", lambda: global_coupling()),
                     ("p_detect_co2e", lambda: detect_co2e()),
                     ("p_amplitude_stability", lambda: amplitude_stability())):
        t = fn()
        print(f"\n=== {name} ===")
        print(t.to_string(index=False))
        print(f"wrote outputs/{name}.csv")


if __name__ == "__main__":
    main()
