"""What the network can and cannot detect, and three signals nobody had asked for.

This pass is mostly about the *instrument* rather than the atmosphere: how much
of a signal a discrete sampling programme recovers, how long a record must run
before a trend is real, and how many independent observations a 215-month
correlation actually contains.  Two of the four are corrections to claims this
report already makes.

  A  the diurnal rectifier, per station and per month  -> outputs/s_rectifier.csv
  B  the rectifier as a QC test, split at the SRG
     cutover the report found by another route         -> outputs/s_qc.csv
  C  Idul Fitri as a mobility experiment at Kemayoran  -> outputs/s_eid.csv
  D  effective sample size for the report's own
     correlations, and which survive it                -> outputs/s_dof.csv
  E  time-to-detect a trend, and the error a discrete
     sampling programme makes                          -> outputs/s_detect.csv, s_sampling.csv
  F  growth-anomaly covariance, H2 trend, the N2O
     seasonal partition, the widening BKT-SPO gap      -> outputs/s_cov.csv, s_species.csv

**The rectifier is the useful one.** Over land the nocturnal boundary layer
always accumulates surface emissions, so a station's 24-hour mean CO2 must
exceed its afternoon mean.  The difference is a positive number at every honest
surface site, which makes a *negative* rectifier a physical impossibility and
therefore a data-quality test that needs no reference site, no flask programme
and no external instrument - a station can run it on its own record.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G
import noaa_flask as NF
import a13_trends_enso as A13

OUT = G.OUT
RNG = np.random.default_rng(20260817)

AFT = (12, 16)          # the well-mixed afternoon window used throughout the report
SRG_CUTOVER = "2023-06-01"
# Idul Fitri (1 Syawal) in Indonesia.  Only 2024 and 2025 fall inside Kemayoran's
# record; 2023 has 762 station-hours and none of them in April.
EID = {2024: "2024-04-10", 2025: "2025-03-31"}


def _load():
    d = pd.read_pickle(OUT / "all.pkl")
    return {st: g.set_index("time_local") for st, g in d.groupby("station")}


def _rectifier(g, species="co2"):
    """Daily (24-hour mean − afternoon mean), on days that have both.

    Restricting to days with both statistics matters: a day sampled only at
    night would otherwise create a rectifier out of missing data."""
    allh = g[species].resample("D").mean()
    aft = g[species][(g.index.hour >= AFT[0]) & (g.index.hour <= AFT[1])].resample("D").mean()
    ok = allh.notna() & aft.notna()
    return (allh - aft)[ok]


# ---------------------------------------------------------------- A, B ------
def rectifier(stations):
    """The rectifier's magnitude at each station, on data that passes B.

    Sorong before the cutover is excluded here: its rectifier is negative, which
    means the data are wrong, and averaging a physically impossible period into a
    physical statistic would report neither.  The defect itself is the subject of
    ``rectifier_qc`` below, which keeps the period in and is the whole point."""
    rows = []
    for st, g in stations.items():
        r = _rectifier(g)
        if st == "SRG":
            r = r[r.index >= SRG_CUTOVER]
        if len(r) < 300:
            continue
        bym = r.groupby(r.index.month).mean()
        rows.append(dict(station=st, n_days=len(r), mean=r.mean(), median=r.median(),
                         month_min=int(bym.idxmin()), min_month_mean=bym.min(),
                         month_max=int(bym.idxmax()), max_month_mean=bym.max(),
                         seasonal_range=bym.max() - bym.min(),
                         pct_negative=100 * (r < 0).mean()))
    return pd.DataFrame(rows).sort_values("mean")


def rectifier_qc(stations):
    """The same statistic split at the date the report flags Sorong on.

    The split date is *not* fitted here - it comes from Section 15.4, which
    reached it from baseline continuity.  That makes this an independent test of
    the same boundary rather than a circular one."""
    rows = []
    for st, g in stations.items():
        r = _rectifier(g)
        for lab, sel in (("before 2023-06", r[r.index < SRG_CUTOVER]),
                         ("from 2023-06", r[r.index >= SRG_CUTOVER])):
            if len(sel) < 60:
                continue
            rows.append(dict(station=st, period=lab, n_days=len(sel), mean=sel.mean(),
                             pct_negative=100 * (sel < 0).mean(),
                             physical=bool(sel.mean() > 0 and (sel < 0).mean() < 0.10)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- C ---------
def eid(stations, n_perm=20000):
    """Idul Fitri as a natural experiment on Jakarta's traffic.

    Millions leave the city for a week (*mudik*), so vehicle activity collapses
    while everything else - landfill, wastewater, the regional background -
    carries on.  Any species that drops is traffic; any species that does not is
    not.  That is a direct test of Findings 8 and 9, which reached the same
    conclusion from emission ratios alone.

    Each year's days are divided by that year's own control median before
    pooling, so the two years contribute equally and no absolute level enters.
    The window runs from two days before to five after: *mudik* departure begins
    before the holiday and the return is staggered over the following week.
    """
    k = stations["KMY"]
    rows = []
    for how, sel in (("rush 06-09", lambda s: s[(s.index.hour >= 6) & (s.index.hour <= 9)]),
                     ("all hours", lambda s: s),
                     ("night 20-04", lambda s: s[(s.index.hour >= 20) | (s.index.hour <= 4)])):
        for sp in ("co", "co2", "ch4"):
            day = sel(k[sp]).resample("D").median()
            hol, ctl = [], []
            for y, e in EID.items():
                e = pd.Timestamp(e)
                h = day[(day.index >= e - pd.Timedelta(days=2))
                        & (day.index <= e + pd.Timedelta(days=5))].dropna()
                c = day[((day.index >= e - pd.Timedelta(days=28)) & (day.index < e - pd.Timedelta(days=7)))
                        | ((day.index > e + pd.Timedelta(days=10)) & (day.index <= e + pd.Timedelta(days=31)))].dropna()
                if len(h) < 4 or len(c) < 15:
                    continue
                hol.append(h.values / c.median())
                ctl.append(c.values / c.median())
            if not hol:
                continue
            hr, cr = np.concatenate(hol), np.concatenate(ctl)
            obs = np.median(hr) - np.median(cr)
            pool = np.concatenate([hr, cr])
            nh = len(hr)
            null = np.array([np.median(p[:nh]) - np.median(p[nh:])
                             for p in (RNG.permutation(pool) for _ in range(n_perm))])
            rows.append(dict(window=how, species=sp, n_holiday=nh, n_control=len(cr),
                             ratio=np.median(hr), change_pct=100 * obs,
                             p=float((np.abs(null) >= abs(obs)).mean())))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- D ---------
def _lag1(x):
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    x = x - x.mean()
    return float(np.sum(x[1:] * x[:-1]) / np.sum(x * x))


def _neff(x, y):
    """Bartlett's effective sample size for a correlation between two
    autocorrelated series: n(1-r1 r2)/(1+r1 r2)."""
    n = min(len(x), len(y))
    r1, r2 = _lag1(x), _lag1(y)
    return max(n * (1 - r1 * r2) / (1 + r1 * r2), 3.0)


def _p(r, n):
    t = r * np.sqrt(max(n - 2, 1) / max(1 - r * r, 1e-12))
    return float(2 * stats.t.sf(abs(t), max(n - 2, 1)))


def dof():
    """How many independent observations the report's correlations really have.

    Two families are tested.  The *monthly* ENSO sensitivities of Section 12.5
    use a growth rate built from a 7-month-smoothed series, which is smooth by
    construction; the *annual* fire and onset results of Section 9.8 use one
    value per year.  The correction should bite hard on the first and not at all
    on the second, and that is the finding.
    """
    rows = []
    oni = A13.load_oni()
    best = pd.read_csv(OUT / "w_enso.csv")
    for _, row in best[best.best].iterrows():
        sp, lag = row.species, int(row.lag_months)
        d = A13.deseasonalised(sp)
        d = d.reindex(pd.date_range(d.index.min(), d.index.max(), freq="MS"))
        d = d.interpolate(limit=2, limit_area="inside")
        gr = d.rolling(7, center=True, min_periods=5).mean().diff(12)
        j = pd.concat([gr.rename("g"), oni.shift(lag).rename("o")], axis=1).dropna()
        r = j.g.corr(j.o)
        slope = np.polyfit(j.o, j.g, 1)[0]
        n, ne = len(j), _neff(j.g.values, j.o.values)
        f = j.g.std() / j.o.std()
        rows.append(dict(family="monthly growth vs ONI", test=f"{sp} lag {lag}",
                         r=r, slope=slope, n=n, n_eff=ne,
                         ci_reported=1.96 * np.sqrt((1 - r * r) / (n - 2)) * f,
                         ci_corrected=1.96 * np.sqrt((1 - r * r) / (ne - 2)) * f,
                         p_reported=_p(r, n), p_corrected=_p(r, ne),
                         survives=bool(_p(r, ne) < 0.05)))

    sev = pd.read_csv(OUT / "u_severity.csv")
    ons = pd.read_csv(OUT / "u_onset.csv")
    for name, x, y in (("peak CO", sev.oni.values, sev.peak.values),
                       ("days over 1000", sev.oni.values, sev.days_over_1000.values),
                       ("monsoon onset", ons.oni.values, ons.onset_doy.values)):
        r = float(np.corrcoef(x, y)[0, 1])
        n, ne = len(x), _neff(x, y)
        rows.append(dict(family="annual vs SON ONI", test=name, r=r, slope=np.nan,
                         n=n, n_eff=ne, ci_reported=np.nan, ci_corrected=np.nan,
                         p_reported=_p(r, n), p_corrected=_p(r, ne),
                         survives=bool(_p(r, ne) < 0.05)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- E ---------
def detection():
    """Weatherhead's time-to-detect, for the three species with long records.

    n* = [3.3 sigma_N / |omega| * sqrt((1+phi)/(1-phi))]^(2/3)

    where sigma_N is the residual noise about the fitted trend-plus-seasonal
    model, omega the trend per unit time and phi the residual lag-1
    autocorrelation.  It answers the question a station manager actually has:
    how many years before this record can show its own trend is real."""
    rows = []
    trend = pd.read_csv(OUT / "w_accel.csv").set_index("species")
    for sp in ("co2", "ch4", "co", "n2o", "sf6"):
        if sp not in trend.index:
            continue
        omega = trend.loc[sp, "growth_midpoint"] / 12.0          # per month
        s = NF.events(sp, "bkt")
        m = s.groupby(s.index.to_period("M")).median()
        m.index = m.index.to_timestamp()
        t = (m.index.year + (m.index.dayofyear - 1) / 365.25).values
        resid = m.values - G.harmonic_fit(t, m.values, n_harm=3, poly=2)["fit"]
        phi, sd = _lag1(resid), float(np.nanstd(resid))
        n_star = (3.3 * sd / abs(omega) * np.sqrt((1 + phi) / (1 - phi))) ** (2 / 3)
        rows.append(dict(species=sp, unit=NF.UNIT[sp],
                         trend_per_yr=trend.loc[sp, "growth_midpoint"],
                         residual_sd=sd, phi=phi,
                         months_to_detect=n_star, years_to_detect=n_star / 12))
    return pd.DataFrame(rows)


def sampling(stations, n_trial=200):
    """What a discrete sampling programme recovers from a continuous record.

    The continuous afternoon record at Bukit Kototabang is subsampled at flask
    frequencies - one afternoon hour every 7, 14 or 30 days - and the monthly
    mean rebuilt from those samples is compared with the monthly mean of the
    whole record.  Repeating over random sampling phases separates the error of
    the *method* from the luck of the calendar."""
    g = stations["BKT"]
    aft = g["co2"][(g.index.hour >= AFT[0]) & (g.index.hour <= AFT[1])].dropna()
    aft = aft[aft.index.year >= 2010]
    truth = aft.resample("MS").mean().dropna()
    rows = []
    for per, label in ((7, "weekly"), (14, "fortnightly"), (30, "monthly")):
        errs = []
        for _ in range(n_trial):
            days = pd.Series(aft.index.normalize().unique()).sort_values()
            off = RNG.integers(0, per)
            keep = set(days.iloc[off::per])
            samp = aft[[d in keep for d in aft.index.normalize()]]
            samp = samp.groupby(samp.index.normalize()).apply(
                lambda s: s.iloc[RNG.integers(0, len(s))])
            m = samp.resample("MS").mean().reindex(truth.index)
            errs.append(float((m - truth).abs().mean()))
        rows.append(dict(frequency=label, interval_days=per,
                         mean_abs_error=float(np.nanmean(errs)),
                         sd_across_phases=float(np.nanstd(errs))))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- F ---------
def _desea(sp, site="bkt"):
    s = NF.events(sp, site)
    m = s.groupby(s.index.to_period("M")).median()
    m.index = m.index.to_timestamp()
    t = (m.index.year + (m.index.dayofyear - 1) / 365.25).values
    return pd.Series(m.values - G.harmonic_fit(t, m.values, n_harm=3, poly=2)["seasonal"],
                     index=m.index)


def covariance():
    """Which species' growth anomalies move together.

    A shared driver should show up as a correlation between growth-rate
    anomalies.  The 12-month centred difference is used *unsmoothed* here, so
    the series keeps its month-to-month independence and the effective sample
    size stays close to n - the opposite choice from Section 12.5, and made
    deliberately because this test is about covariance rather than about the
    shape of the ENSO response."""
    gr = {}
    for sp in ("co2", "ch4", "co", "n2o", "sf6"):
        s = _desea(sp)
        s = s.reindex(pd.date_range(s.index.min(), s.index.max(), freq="MS")).interpolate(limit=2)
        gr[sp] = s.shift(-6) - s.shift(6)
    g = pd.DataFrame(gr).dropna()
    rows = []
    cols = list(g.columns)
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            r = float(g[a].corr(g[b]))
            ne = _neff(g[a].values, g[b].values)
            rows.append(dict(pair=f"{a}-{b}", r=r, n=len(g), n_eff=ne,
                             p=_p(r, ne), significant=bool(_p(r, ne) < 0.05)))
    return pd.DataFrame(rows).sort_values("r", ascending=False)


def species_extras():
    """Three single-species results: the hydrogen trend, the nitrous-oxide
    seasonal partition, and whether the Maritime Continent's CO2 deficit against
    each reference site is changing."""
    rows = []

    h = _desea("h2")
    t = (h.index.year + h.index.month / 12).values
    sl, lo, hi = G.theil_sen(t, h.values)
    level = float(NF.events("h2", "bkt").median())
    rows.append(dict(kind="h2 trend", label="BKT 2009-2024", value=sl, lo=lo, hi=hi,
                     extra=100 * sl / level, note="ppb/yr; extra = %/yr of the median"))

    # the seasonal cycle of each species regressed on SF6's, which is inert:
    # R^2 is the share of the seasonal cycle that transport explains
    def seas(sp):
        s = NF.events(sp, "bkt")
        m = s.groupby(s.index.to_period("M")).median()
        m.index = m.index.to_timestamp()
        t = (m.index.year + (m.index.dayofyear - 1) / 365.25).values
        f = G.harmonic_fit(t, m.values, n_harm=3, poly=2)
        return pd.Series(f["seasonal"], index=m.index).groupby(lambda x: x.month).mean()

    sf6 = seas("sf6")
    for sp in ("ch4", "n2o", "co2", "co"):
        s = seas(sp)
        r = float(np.corrcoef(s.values, sf6.values)[0, 1])
        rows.append(dict(kind="seasonal cycle vs SF6", label=sp, value=r, lo=np.nan,
                         hi=np.nan, extra=100 * r * r,
                         note="r; extra = R^2 %, the share transport explains"))

    for ref in ("mlo", "spo", "smo", "kum"):
        a, b = NF.monthly("co2", "bkt"), NF.monthly("co2", ref)
        j = pd.concat([a.rename("bkt"), b.rename("ref")], axis=1).dropna()
        j = j[j.index.year >= 2005]
        diff = j.bkt - j.ref
        t = (diff.index.year + (diff.index.dayofyear - 1) / 365.25).values
        f = G.harmonic_fit(t, diff.values, n_harm=3, poly=1)
        sl, lo, hi = G.theil_sen(t, diff.values - f["seasonal"])
        rows.append(dict(kind="CO2 deficit trend", label=f"BKT-{ref.upper()}",
                         value=sl * 10, lo=lo * 10, hi=hi * 10, extra=diff.mean(),
                         note="ppm/decade; extra = mean difference, ppm"))
    return pd.DataFrame(rows)


def main():
    st = _load()
    tables = {"s_rectifier": rectifier(st), "s_qc": rectifier_qc(st), "s_eid": eid(st),
              "s_dof": dof(), "s_detect": detection(), "s_sampling": sampling(st),
              "s_cov": covariance(), "s_species": species_extras()}
    for name, t in tables.items():
        t.to_csv(OUT / f"{name}.csv", index=False)
        print(f"\n===== {name} =====")
        print(t.to_string(index=False))
    return tables


if __name__ == "__main__":
    main()
