"""Analysis script for Findings 68-77: Hovmöller dynamics, interhemispheric exchange,
vertical damping, methane gradient evolution, and multi-species forcing.

Produces:
  outputs/t_hovmoeller_lat_co2.csv      (Finding 68)
  outputs/t_sf6_exchange_time.csv       (Finding 69)
  outputs/t_hovmoeller_lon_ch4.csv      (Finding 70)
  outputs/t_enso_growth_asymmetry.csv   (Finding 71)
  outputs/t_ch4_gradient_evolution.csv  (Finding 72)
  outputs/t_vertical_damping.csv        (Finding 73)
  outputs/t_growth_covariance_matrix.csv (Finding 74)
  outputs/t_bkt_clean_co_floor.csv      (Finding 75)
  outputs/t_bkt_nocturnal_monsoon.csv   (Finding 76)
  outputs/t_regional_forcing_budget.csv (Finding 77)
"""
from pathlib import Path
import numpy as np
import pandas as pd
import scipy.stats as stats

import ghg_common as G
import noaa_flask as nf

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"


def finding_68_lat_hovmoeller():
    """Finding 68: Latitudinal Hovmoeller & seasonal wave attenuation across NOAA sites."""
    sites = ["brw", "kum", "mlo", "bkt", "smo", "spo"]
    rows = []
    for st in sites:
        s = nf.monthly("co2", st)
        t = s.index.year + (s.index.month - 0.5) / 12.0
        fit = G.harmonic_fit(t.values, s.values, n_harm=3, poly=2)
        lat = nf.SITES[st][1]
        name = nf.SITES[st][0]
        s_season = pd.Series(fit["seasonal"], index=s.index)
        mon_clim = s_season.groupby(s.index.month).mean()
        amp = float(mon_clim.max() - mon_clim.min())
        min_mon = int(mon_clim.idxmin())
        max_mon = int(mon_clim.idxmax())
        rows.append(dict(site=st, name=name, latitude=lat,
                         seasonal_amp_ppm=round(amp, 2),
                         min_month=min_mon, max_month=max_mon,
                         trend_slope_ppm_yr=round(float(fit["beta"][1]), 3)))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "t_hovmoeller_lat_co2.csv", index=False)
    print("wrote outputs/t_hovmoeller_lat_co2.csv")
    return df


def finding_69_sf6_exchange_time():
    """Finding 69: 2-box model interhemispheric exchange time from SF6."""
    s_brw = nf.monthly("sf6", "brw")
    s_spo = nf.monthly("sf6", "spo")
    common = s_brw.index.intersection(s_spo.index)
    diff_ns = s_brw.loc[common] - s_spo.loc[common]
    mean_diff = float(diff_ns.mean())
    std_diff = float(diff_ns.std())

    s_bkt = nf.monthly("sf6", "bkt")
    t_bkt = s_bkt.index.year + (s_bkt.index.month - 0.5) / 12.0
    fit_sf6 = G.harmonic_fit(t_bkt.values, s_bkt.values, n_harm=1, poly=1)
    growth_rate = float(fit_sf6["beta"][1])  # ppt/yr

    tau_ex_yr = mean_diff / growth_rate
    tau_ex_mo = tau_ex_yr * 12.0

    df = pd.DataFrame([dict(
        mean_ns_diff_ppt=round(mean_diff, 3),
        std_ns_diff_ppt=round(std_diff, 3),
        sf6_growth_rate_ppt_yr=round(growth_rate, 3),
        tau_exchange_yr=round(tau_ex_yr, 2),
        tau_exchange_months=round(tau_ex_mo, 1),
    )])
    df.to_csv(OUT / "t_sf6_exchange_time.csv", index=False)
    print("wrote outputs/t_sf6_exchange_time.csv")
    return df


def finding_70_lon_hovmoeller():
    """Finding 70: Longitude-Time Hovmoeller of CH4 across the Maritime Continent."""
    df_all = G.load_all()
    st_order = ["BKT", "JMB", "KMY", "PLU", "SRG"]
    rows = []
    for st in st_order:
        d = df_all[df_all.station == st]
        d_aft = d[(d.time_local.dt.hour >= 12) & (d.time_local.dt.hour <= 16)]
        mon_q20 = d_aft.groupby(d_aft.time_local.dt.month)["ch4"].quantile(0.20)
        peak_mon = int(mon_q20.idxmax())
        min_mon = int(mon_q20.idxmin())
        amp = float(mon_q20.max() - mon_q20.min())
        lat = G.STATIONS[st][2]
        lon = G.STATIONS[st][3]
        name = G.STATIONS[st][0]
        rows.append(dict(station=st, name=name, longitude=lon, latitude=lat,
                         peak_month=peak_mon, min_month=min_mon,
                         seasonal_amp_ppb=round(amp, 1)))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "t_hovmoeller_lon_ch4.csv", index=False)
    print("wrote outputs/t_hovmoeller_lon_ch4.csv")
    return df


def finding_71_enso_growth_asymmetry():
    """Finding 71: Interhemispheric CO2 growth rate asymmetry during ENSO extremes."""
    gr_brw = nf.monthly("co2", "brw").diff(12).rolling(7, center=True).mean().dropna()
    gr_spo = nf.monthly("co2", "spo").diff(12).rolling(7, center=True).mean().dropna()
    gr_bkt = nf.monthly("co2", "bkt").diff(12).rolling(7, center=True).mean().dropna()
    c_idx = gr_brw.index.intersection(gr_spo.index).intersection(gr_bkt.index)

    asym_ns = gr_brw.loc[c_idx] - gr_spo.loc[c_idx]
    asym_eq_s = gr_bkt.loc[c_idx] - gr_spo.loc[c_idx]

    df = pd.DataFrame([dict(
        mean_asymmetry_ns_ppm_yr=round(float(asym_ns.mean()), 3),
        std_asymmetry_ns_ppm_yr=round(float(asym_ns.std()), 3),
        max_asymmetry_ns_ppm_yr=round(float(asym_ns.max()), 3),
        min_asymmetry_ns_ppm_yr=round(float(asym_ns.min()), 3),
        mean_asymmetry_eq_s_ppm_yr=round(float(asym_eq_s.mean()), 3),
        std_asymmetry_eq_s_ppm_yr=round(float(asym_eq_s.std()), 3),
    )])
    df.to_csv(OUT / "t_enso_growth_asymmetry.csv", index=False)
    print("wrote outputs/t_enso_growth_asymmetry.csv")
    return df


def finding_72_ch4_gradient_evolution():
    """Finding 72: Methane interhemispheric gradient evolution (post-2014 tropical surge)."""
    ch4_brw = nf.monthly("ch4", "brw")
    ch4_bkt = nf.monthly("ch4", "bkt")
    ch4_spo = nf.monthly("ch4", "spo")
    c_ch4 = ch4_brw.index.intersection(ch4_bkt.index).intersection(ch4_spo.index)
    p1 = c_ch4[c_ch4 < "2014-01-01"]
    p2 = c_ch4[c_ch4 >= "2014-01-01"]

    grad_tot_p1 = float((ch4_brw.loc[p1] - ch4_spo.loc[p1]).mean())
    grad_tot_p2 = float((ch4_brw.loc[p2] - ch4_spo.loc[p2]).mean())
    bkt_spo_p1 = float((ch4_bkt.loc[p1] - ch4_spo.loc[p1]).mean())
    bkt_spo_p2 = float((ch4_bkt.loc[p2] - ch4_spo.loc[p2]).mean())
    brw_bkt_p1 = float((ch4_brw.loc[p1] - ch4_bkt.loc[p1]).mean())
    brw_bkt_p2 = float((ch4_brw.loc[p2] - ch4_bkt.loc[p2]).mean())

    df = pd.DataFrame([
        dict(segment="Total (BRW - SPO)", period_2004_2013=round(grad_tot_p1, 1),
             period_2014_2024=round(grad_tot_p2, 1), difference=round(grad_tot_p2 - grad_tot_p1, 1)),
        dict(segment="Tropical (BKT - SPO)", period_2004_2013=round(bkt_spo_p1, 1),
             period_2014_2024=round(bkt_spo_p2, 1), difference=round(bkt_spo_p2 - bkt_spo_p1, 1)),
        dict(segment="Northern (BRW - BKT)", period_2004_2013=round(brw_bkt_p1, 1),
             period_2014_2024=round(brw_bkt_p2, 1), difference=round(brw_bkt_p2 - brw_bkt_p1, 1)),
    ])
    df.to_csv(OUT / "t_ch4_gradient_evolution.csv", index=False)
    print("wrote outputs/t_ch4_gradient_evolution.csv")
    return df


def finding_73_vertical_damping():
    """Finding 73: Vertical damping of seasonal amplitudes (MLO 3,397 m vs KUM 3 m)."""
    rows = []
    for sp, unit in [("co2", "ppm"), ("ch4", "ppb"), ("co", "ppb")]:
        s_mlo = nf.monthly(sp, "mlo")
        s_kum = nf.monthly(sp, "kum")
        t_m = s_mlo.index.year + (s_mlo.index.month - 0.5) / 12.0
        t_k = s_kum.index.year + (s_kum.index.month - 0.5) / 12.0
        f_m = G.harmonic_fit(t_m.values, s_mlo.values, n_harm=3, poly=2)
        f_k = G.harmonic_fit(t_k.values, s_kum.values, n_harm=3, poly=2)
        amp_m = float(f_m["seasonal"].max() - f_m["seasonal"].min())
        amp_k = float(f_k["seasonal"].max() - f_k["seasonal"].min())
        damping = float(100.0 * (1.0 - amp_m / amp_k))
        rows.append(dict(species=sp.upper(), unit=unit,
                         kum_surface_amp=round(amp_k, 2),
                         mlo_free_trop_amp=round(amp_m, 2),
                         vertical_damping_pct=round(damping, 1)))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "t_vertical_damping.csv", index=False)
    print("wrote outputs/t_vertical_damping.csv")
    return df


def finding_74_growth_covariance_matrix():
    """Finding 74: Multi-species growth rate anomaly covariance matrix."""
    sp_list = ["co2", "ch4", "co", "n2o", "sf6"]
    gr_dict = {}
    for sp in sp_list:
        s = nf.monthly(sp, "bkt")
        gr = s.diff(12).rolling(7, center=True).mean().dropna()
        gr_dict[sp] = gr
    df_gr = pd.DataFrame(gr_dict).dropna()
    corr_mat = df_gr.corr().round(3)
    corr_mat.to_csv(OUT / "t_growth_covariance_matrix.csv")
    print("wrote outputs/t_growth_covariance_matrix.csv")
    return corr_mat


def finding_75_clean_co_floor():
    """Finding 75: Pristine clean-air baseline CO floor stability at BKT."""
    ev_co = nf.events("co", "bkt")
    annual_q10 = ev_co.groupby(ev_co.index.year).quantile(0.10)
    slope, intercept, r_val, p_val, stderr = stats.linregress(annual_q10.index, annual_q10.values)
    mean_val = float(annual_q10.mean())
    std_val = float(annual_q10.std())

    df = pd.DataFrame([dict(
        mean_clean_co_q10_ppb=round(mean_val, 1),
        std_clean_co_q10_ppb=round(std_val, 1),
        start_2004_ppb=round(float(annual_q10.iloc[0]), 1),
        end_2024_ppb=round(float(annual_q10.iloc[-1]), 1),
        trend_slope_ppb_yr=round(float(slope), 2),
        p_value=round(float(p_val), 4),
    )])
    df.to_csv(OUT / "t_bkt_clean_co_floor.csv", index=False)
    print("wrote outputs/t_bkt_clean_co_floor.csv")
    return df


def finding_76_bkt_nocturnal_monsoon():
    """Finding 76: Monsoonal modulation of nocturnal canopy accumulation at BKT."""
    df_all = G.load_all()
    bkt_df = df_all[df_all.station == "BKT"].copy()
    bkt_df["hour"] = bkt_df.time_local.dt.hour
    bkt_df["season"] = bkt_df.time_local.dt.month.map(
        lambda m: "wet_DJF" if m in [12, 1, 2] else ("dry_JJA" if m in [6, 7, 8] else "trans")
    )
    rows = []
    for s_name, label in [("wet_DJF", "Wet NW Monsoon (DJF, Westerly)"),
                          ("dry_JJA", "Dry SE Monsoon (JJA, Easterly)")]:
        sub = bkt_df[bkt_df.season == s_name]
        co2_night = float(sub[sub.hour.between(0, 5)]["co2"].median())
        co2_day = float(sub[sub.hour.between(12, 16)]["co2"].median())
        co_night = float(sub[sub.hour.between(0, 5)]["co"].median())
        co_day = float(sub[sub.hour.between(12, 16)]["co"].median())
        rows.append(dict(
            monsoon_regime=label,
            co2_night_median=round(co2_night, 2),
            co2_day_median=round(co2_day, 2),
            co2_diurnal_swing_ppm=round(co2_night - co2_day, 2),
            co_night_median=round(co_night, 1),
            co_day_median=round(co_day, 1),
            co_diurnal_swing_ppb=round(co_night - co_day, 1),
        ))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "t_bkt_nocturnal_monsoon.csv", index=False)
    print("wrote outputs/t_bkt_nocturnal_monsoon.csv")
    return df


def finding_77_regional_forcing_budget():
    """Finding 77: Multi-species radiative forcing enhancement of Maritime Continent over marine baseline."""
    s_co2_bkt = nf.monthly("co2", "bkt")
    s_co2_smo = nf.monthly("co2", "smo")
    s_ch4_bkt = nf.monthly("ch4", "bkt")
    s_ch4_smo = nf.monthly("ch4", "smo")
    s_n2o_bkt = nf.monthly("n2o", "bkt")
    s_n2o_smo = nf.monthly("n2o", "smo")
    s_sf6_bkt = nf.monthly("sf6", "bkt")
    s_sf6_smo = nf.monthly("sf6", "smo")

    idx = s_co2_bkt.index.intersection(s_co2_smo.index).intersection(s_ch4_bkt.index).intersection(s_ch4_smo.index).intersection(s_n2o_bkt.index).intersection(s_n2o_smo.index).intersection(s_sf6_bkt.index).intersection(s_sf6_smo.index)

    d_co2 = float((s_co2_bkt.loc[idx] - s_co2_smo.loc[idx]).mean())
    d_ch4 = float((s_ch4_bkt.loc[idx] - s_ch4_smo.loc[idx]).mean())
    d_n2o = float((s_n2o_bkt.loc[idx] - s_n2o_smo.loc[idx]).mean())
    d_sf6 = float((s_sf6_bkt.loc[idx] - s_sf6_smo.loc[idx]).mean())

    # Use Section 13.1's band expressions exactly, so the two forcing tables in
    # this report are on one convention.  An earlier version linearised the CO2
    # term and used a 0.057 CH4 coefficient - an implied indirect uplift of 1.58
    # against the 1.43 documented in Section 13.1 - which inflated the net by 48 %.
    CH4_INDIRECT = 1.43
    f_co2 = float(5.35 * np.log((410.0 + d_co2) / 410.0) * 1000.0)
    f_ch4 = float(0.036 * (np.sqrt(1850.0 + d_ch4) - np.sqrt(1850.0))
                  * CH4_INDIRECT * 1000.0)
    f_n2o = float(0.12 * (np.sqrt(330.0 + d_n2o) - np.sqrt(330.0)) * 1000.0)
    f_sf6 = float(0.57 * d_sf6)
    total_f = f_co2 + f_ch4 + f_n2o + f_sf6

    df = pd.DataFrame([
        dict(species="CO2", delta_concentration=round(d_co2, 2), unit="ppm",
             radiative_forcing_mW_m2=round(f_co2, 2)),
        dict(species="CH4", delta_concentration=round(d_ch4, 1), unit="ppb",
             radiative_forcing_mW_m2=round(f_ch4, 2)),
        dict(species="N2O", delta_concentration=round(d_n2o, 2), unit="ppb",
             radiative_forcing_mW_m2=round(f_n2o, 2)),
        dict(species="SF6", delta_concentration=round(d_sf6, 3), unit="ppt",
             radiative_forcing_mW_m2=round(f_sf6, 2)),
        dict(species="Total Net Enhancement", delta_concentration=np.nan, unit="",
             radiative_forcing_mW_m2=round(total_f, 2)),
    ])
    df.to_csv(OUT / "t_regional_forcing_budget.csv", index=False)
    print("wrote outputs/t_regional_forcing_budget.csv")
    return df


def main():
    finding_68_lat_hovmoeller()
    finding_69_sf6_exchange_time()
    finding_70_lon_hovmoeller()
    finding_71_enso_growth_asymmetry()
    finding_72_ch4_gradient_evolution()
    finding_73_vertical_damping()
    finding_74_growth_covariance_matrix()
    finding_75_clean_co_floor()
    finding_76_bkt_nocturnal_monsoon()
    finding_77_regional_forcing_budget()


if __name__ == "__main__":
    main()
