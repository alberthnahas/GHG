"""Analysis pass 4: Flask pair reproducibility, SF6 transport lag, vertical gradients,

hydrogen climatology, Bariri/Sorong regional baselines, Jakarta rush-hour dynamics,
N2O ENSO null test, N2O decadal acceleration across latitudes, and drained peat
seasonal respiration amplification (Findings 58–67).

Produces:
  outputs/t_flask_pairs.csv
  outputs/t_sf6_lag.csv
  outputs/t_vertical_gradients.csv
  outputs/t_h2_seasonality.csv
  outputs/t_plu_vs_bkt.csv
  outputs/t_srg_marine.csv
  outputs/t_kmy_diurnal_rush.csv
  outputs/t_n2o_enso_neff.csv
  outputs/t_n2o_acceleration.csv
  outputs/t_jmb_seasonal_respiration.csv
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import scipy.stats as stats

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import ghg_common as G
import noaa_flask as F

OUT = ROOT / "outputs"


def to_decyear(dt_index):
    return dt_index.year + (dt_index.dayofyear - 1) / 365.25


def analyze_flask_pairs():
    """Finding 58: Intra-pair reproducibility and single-flask measurement uncertainty."""
    rows = []
    for sp in F.SPECIES:
        f = ROOT / "noaa_flask" / f"{sp}_bkt_surface-flask_1_ccgg_event.txt"
        if not f.exists():
            continue
        lines = F._rows(f)
        df = pd.DataFrame([ln.split() for ln in lines[1:]], columns=lines[0].split())
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df["t"] = pd.to_datetime(df["datetime"], format="ISO8601", utc=True).dt.tz_localize(None)
        df_qc = df[df.qcflag.str[0] == "."].copy()
        grp = df_qc.groupby(df_qc.t.dt.floor("h"))["value"].agg(["count", "min", "max", "mean"])
        pairs = grp[grp["count"] == 2].copy()
        pairs["diff"] = (pairs["max"] - pairs["min"]).abs()
        med = pairs["diff"].median()
        mean = pairs["diff"].mean()
        p95 = pairs["diff"].quantile(0.95)
        # sigma of a single flask from the paired differences.
        #
        # Two wrong ways to do this were tried here first.  `pairs["diff"]` is
        # |x1 - x2|, a *folded* variable, so neither its mean nor its standard
        # deviation is the standard deviation of the signed difference d:
        #   E|d|     = sigma_d * sqrt(2/pi)   = 0.798 sigma_d
        #   sd(|d|)  = sigma_d * sqrt(1-2/pi) = 0.603 sigma_d
        # Dividing either by sqrt(2) understates sigma_single (= sigma_d/sqrt2)
        # by 20 % and 40 % respectively.
        #
        # The second moment survives the fold exactly, because d^2 == |d|^2, so
        # sigma_d = RMS(|d|) with no distributional assumption at all.
        rms = np.sqrt((pairs["diff"] ** 2).mean())
        std_pair = rms / np.sqrt(2)
        # A few bad pairs inflate the second moment for CH4 and N2O, whose
        # RMS/mean ratio reaches 1.54 against the 1.253 a normal d would give.
        # The median of a half-normal is 0.6745 sigma, so this is the same
        # quantity read off a statistic the outliers cannot move.  Where the two
        # disagree they bracket the answer.
        robust = (pairs["diff"].median() / 0.6745) / np.sqrt(2)
        shape = rms / pairs["diff"].mean()
        rows.append({
            "species": sp.upper(),
            "unit": F.UNIT[sp],
            "n_pairs": len(pairs),
            "median_pair_diff": round(med, 4),
            "mean_pair_diff": round(mean, 4),
            "p95_pair_diff": round(p95, 4),
            "single_flask_sigma": round(std_pair, 4),
            "single_flask_sigma_robust": round(robust, 4),
            "rms_over_mean": round(shape, 3)
        })
    df_out = pd.DataFrame(rows)
    df_out.to_csv(OUT / "t_flask_pairs.csv", index=False)
    return df_out


def analyze_sf6_lag():
    """Finding 59: SF6 interhemispheric transport lag clock."""
    sites = ["brw", "mlo", "kum", "bkt", "smo", "spo"]
    sf6_m = {s: F.monthly("sf6", s) for s in sites}
    df = pd.DataFrame(sf6_m).dropna()
    t_bkt = to_decyear(df.index)
    trend_bkt, lo_bkt, hi_bkt = G.theil_sen(t_bkt, df["bkt"].values)
    
    rows = []
    for s in sites:
        mean_val = df[s].mean()
        diff_brw = mean_val - df["brw"].mean()
        diff_spo = mean_val - df["spo"].mean()
        t_s = to_decyear(df.index)
        trend, lo, hi = G.theil_sen(t_s, df[s].values)
        lag_brw = (df["brw"].mean() - mean_val) / (trend / 12.0)
        lead_spo = (mean_val - df["spo"].mean()) / (trend / 12.0)
        rows.append({
            "site": s.upper(),
            "name": F.SITES[s][0],
            "lat": F.SITES[s][1],
            "elev_m": F.SITES[s][3],
            "mean_sf6_ppt": round(mean_val, 3),
            "diff_from_brw_ppt": round(diff_brw, 3),
            "lag_from_brw_months": round(lag_brw, 1),
            "lead_over_spo_months": round(lead_spo, 1),
            "growth_ppt_yr": round(trend, 4),
            "growth_ci_lo": round(lo, 4),
            "growth_ci_hi": round(hi, 4)
        })
    df_out = pd.DataFrame(rows)
    df_out.to_csv(OUT / "t_sf6_lag.csv", index=False)
    return df_out


def analyze_vertical_gradients():
    """Finding 60: Free troposphere vs marine boundary layer vertical gradient at 19.5N."""
    rows = []
    for sp in ["co2", "ch4", "co", "n2o", "sf6"]:
        mlo = F.monthly(sp, "mlo").dropna()
        kum = F.monthly(sp, "kum").dropna()
        bkt = F.monthly(sp, "bkt").dropna()
        common = mlo.to_frame("mlo").join(kum.to_frame("kum")).join(bkt.to_frame("bkt")).dropna()
        diff_vert = common["mlo"] - common["kum"]
        diff_bkt_kum = common["bkt"] - common["kum"]
        diff_bkt_mlo = common["bkt"] - common["mlo"]
        ttest = stats.ttest_rel(common["mlo"], common["kum"])
        rows.append({
            "species": sp.upper(),
            "unit": F.UNIT[sp],
            "n_months": len(common),
            "mlo_mean": round(common["mlo"].mean(), 3),
            "kum_mean": round(common["kum"].mean(), 3),
            "mlo_minus_kum_mean": round(diff_vert.mean(), 3),
            "mlo_minus_kum_std": round(diff_vert.std(), 3),
            "p_value": ttest.pvalue,
            "bkt_minus_kum_mean": round(diff_bkt_kum.mean(), 3),
            "bkt_minus_mlo_mean": round(diff_bkt_mlo.mean(), 3)
        })
    df_out = pd.DataFrame(rows)
    df_out.to_csv(OUT / "t_vertical_gradients.csv", index=False)
    return df_out


def analyze_h2_seasonality():
    """Finding 61: Climatological seasonal cycle of flask H2 at BKT."""
    h2_m = F.monthly("h2", "bkt").dropna()
    t_h2 = to_decyear(h2_m.index)
    h_fit = G.harmonic_fit(t_h2, h2_m.values, n_harm=2, poly=1)
    h2_trend, h2_lo, h2_hi = G.theil_sen(t_h2, h2_m.values)
    mean_val = h2_m.mean()
    
    rows = []
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for m_i in range(1, 13):
        vals = h2_m[h2_m.index.month == m_i]
        rows.append({
            "month": m_i,
            "month_name": month_names[m_i - 1],
            "n_samples": len(vals),
            "mean_ppb": round(vals.mean(), 2),
            "std_ppb": round(vals.std(), 2),
            "anomaly_ppb": round(vals.mean() - mean_val, 2)
        })
    df_out = pd.DataFrame(rows)
    df_out.to_csv(OUT / "t_h2_seasonality.csv", index=False)
    return df_out, h2_trend, h2_lo, h2_hi, h_fit


def analyze_plu_vs_bkt(all_df):
    """Finding 62: Bariri (PLU montane rainforest) vs BKT afternoon baseline contrast."""
    rows = []
    plu_clean = G.clean(all_df[all_df["station"] == "PLU"], "co2")
    bkt_clean = G.clean(all_df[all_df["station"] == "BKT"], "co2")
    plu_aft = plu_clean[(plu_clean["hour_local"] >= 12) & (plu_clean["hour_local"] <= 16)]
    bkt_aft = bkt_clean[(bkt_clean["hour_local"] >= 12) & (bkt_clean["hour_local"] <= 16)]
    
    for sp in ["co2", "ch4", "co"]:
        plu_m = plu_aft.set_index("time_local")[sp].resample("MS").quantile(0.20)
        bkt_m = bkt_aft.set_index("time_local")[sp].resample("MS").quantile(0.20)
        ov = plu_m.to_frame("PLU").join(bkt_m.to_frame("BKT")).dropna()
        diff = ov["PLU"] - ov["BKT"]
        r, p = stats.pearsonr(ov["PLU"], ov["BKT"])
        rows.append({
            "species": sp.upper(),
            "unit": "ppm" if sp == "co2" else "ppb",
            "n_months": len(ov),
            "plu_mean_q20": round(ov["PLU"].mean(), 2),
            "bkt_mean_q20": round(ov["BKT"].mean(), 2),
            "diff_plu_minus_bkt": round(diff.mean(), 2),
            "diff_std": round(diff.std(), 2),
            "pearson_r": round(r, 3),
            "p_value": p
        })
    df_out = pd.DataFrame(rows)
    df_out.to_csv(OUT / "t_plu_vs_bkt.csv", index=False)
    return df_out


def analyze_srg_marine(all_df):
    """Finding 63: Clean Sorong (SRG post-Jun 2023) vs NOAA Pacific marine baseline."""
    srg_clean = all_df[(all_df["station"] == "SRG") & (all_df["time_local"] >= "2023-06-01")]
    srg_aft = srg_clean[(srg_clean["hour_local"] >= 12) & (srg_clean["hour_local"] <= 16)]
    rows = []
    for sp in ["co2", "ch4", "co"]:
        srg_m = srg_aft.set_index("time_local")[sp].resample("MS").median().dropna()
        smo_m = F.monthly(sp, "smo").dropna()
        kum_m = F.monthly(sp, "kum").dropna()
        ov_smo = srg_m.to_frame("SRG").join(smo_m.to_frame("SMO")).dropna()
        ov_kum = srg_m.to_frame("SRG").join(kum_m.to_frame("KUM")).dropna()
        diff_smo = ov_smo["SRG"] - ov_smo["SMO"]
        diff_kum = ov_kum["SRG"] - ov_kum["KUM"]
        rows.append({
            "species": sp.upper(),
            "unit": "ppm" if sp == "co2" else "ppb",
            "n_months": len(ov_smo),
            "srg_median_mean": round(srg_m.loc[ov_smo.index].mean(), 2),
            "smo_mean": round(ov_smo["SMO"].mean(), 2),
            "diff_srg_minus_smo": round(diff_smo.mean(), 2),
            "diff_srg_minus_smo_std": round(diff_smo.std(), 2),
            "kum_mean": round(ov_kum["KUM"].mean(), 2),
            "diff_srg_minus_kum": round(diff_kum.mean(), 2),
            "diff_srg_minus_kum_std": round(diff_kum.std(), 2)
        })
    df_out = pd.DataFrame(rows)
    df_out.to_csv(OUT / "t_srg_marine.csv", index=False)
    return df_out


def analyze_kmy_diurnal_rush(all_df):
    """Finding 64: Kemayoran weekday vs weekend diurnal rush-hour dynamics."""
    kmy_df = all_df[all_df["station"] == "KMY"].copy()
    kmy_df["dow"] = kmy_df["time_local"].dt.dayofweek
    kmy_df["is_weekend"] = kmy_df["dow"] >= 5
    rows = []
    for sp in ["co", "co2", "ch4"]:
        wkday = kmy_df[~kmy_df["is_weekend"]].groupby("hour_local")[sp].median()
        wkend = kmy_df[kmy_df["is_weekend"]].groupby("hour_local")[sp].median()
        wkday_amp = wkday.max() - wkday.min()
        wkend_amp = wkend.max() - wkend.min()
        m_drop = ((wkend.loc[7] - wkday.loc[7]) / wkday.loc[7]) * 100
        e_drop = ((wkend.loc[20] - wkday.loc[20]) / wkday.loc[20]) * 100
        rows.append({
            "species": sp.upper(),
            "unit": "ppm" if sp == "co2" else "ppb",
            "weekday_min": round(wkday.min(), 1),
            "weekday_max": round(wkday.max(), 1),
            "weekday_amp": round(wkday_amp, 1),
            "weekend_min": round(wkend.min(), 1),
            "weekend_max": round(wkend.max(), 1),
            "weekend_amp": round(wkend_amp, 1),
            "amp_ratio_wkday_wkend": round(wkday_amp / wkend_amp, 2),
            "rush_0700_wkday": round(wkday.loc[7], 1),
            "rush_0700_wkend": round(wkend.loc[7], 1),
            "rush_0700_pct_change": round(m_drop, 1),
            "peak_2000_wkday": round(wkday.loc[20], 1),
            "peak_2000_wkend": round(wkend.loc[20], 1),
            "peak_2000_pct_change": round(e_drop, 1)
        })
    df_out = pd.DataFrame(rows)
    df_out.to_csv(OUT / "t_kmy_diurnal_rush.csv", index=False)
    return df_out


def analyze_n2o_enso_neff():
    """Finding 65: N2O growth rate anomaly vs ONI and Bartlett effective sample size correction."""
    n2o_m = F.monthly("n2o", "bkt").dropna()
    s_n2o = n2o_m.reindex(pd.date_range(n2o_m.index.min(), n2o_m.index.max(), freq="MS")).interpolate(limit=2)
    gr_n2o = s_n2o.rolling(7, min_periods=5, center=True).mean().diff(12)
    
    oni = pd.read_csv(ROOT / "data" / "oni.ascii.txt", sep=r"\s+", header=0)
    oni["date"] = pd.to_datetime(oni["YR"].astype(str) + "-" + oni["SEAS"].map({
        "DJF": "01", "JFM": "02", "FMA": "03", "MAM": "04", "AMJ": "05", "MJJ": "06",
        "JJA": "07", "JAS": "08", "ASO": "09", "SON": "10", "OND": "11", "NDJ": "12"
    }) + "-01")
    oni_s = oni.set_index("date")["ANOM"]
    df = gr_n2o.to_frame("gr").join(oni_s.to_frame("oni")).dropna()
    r, p_nom = stats.pearsonr(df["gr"], df["oni"])
    r1 = df["gr"].autocorr(1)
    r2 = df["oni"].autocorr(1)
    neff = len(df) * (1 - r1 * r2) / (1 + r1 * r2)
    t_stat = r * np.sqrt(neff - 2) / np.sqrt(1 - r**2)
    p_eff = 2 * (1 - stats.t.cdf(abs(t_stat), df=max(1, neff - 2)))
    
    df_out = pd.DataFrame([{
        "species": "N2O",
        "n_months": len(df),
        "pearson_r": round(r, 3),
        "r1_lag1": round(r1, 3),
        "r2_lag1": round(r2, 3),
        "n_eff": round(neff, 1),
        "p_nominal": p_nom,
        "p_effective": round(p_eff, 4),
        "is_significant_95": bool(p_eff < 0.05)
    }])
    df_out.to_csv(OUT / "t_n2o_enso_neff.csv", index=False)
    return df_out


def analyze_n2o_acceleration():
    """Finding 66: Decadal N2O acceleration across latitudes."""
    sites = ["brw", "mlo", "bkt", "smo", "spo"]
    rows = []
    for s in sites:
        m = F.monthly("n2o", s).dropna()
        m1 = m[(m.index >= "2004-01-01") & (m.index <= "2013-12-31")]
        m2 = m[(m.index >= "2014-01-01") & (m.index <= "2024-12-31")]
        t1_num = to_decyear(m1.index)
        t2_num = to_decyear(m2.index)
        t1, l1, h1 = G.theil_sen(t1_num, m1.values)
        t2, l2, h2 = G.theil_sen(t2_num, m2.values)
        rows.append({
            "site": s.upper(),
            "name": F.SITES[s][0],
            "lat": F.SITES[s][1],
            "trend_2004_2013": round(t1, 3),
            "ci_lo_2004": round(l1, 3),
            "ci_hi_2004": round(h1, 3),
            "trend_2014_2024": round(t2, 3),
            "ci_lo_2014": round(l2, 3),
            "ci_hi_2014": round(h2, 3),
            "acceleration_jump": round(t2 - t1, 3)
        })
    df_out = pd.DataFrame(rows)
    df_out.to_csv(OUT / "t_n2o_acceleration.csv", index=False)
    return df_out


def analyze_jmb_seasonal_respiration(all_df):
    """Finding 67: Drained peatland dry-season respiration amplification at Jambi vs Bariri."""
    jmb_clean = G.clean(all_df[all_df["station"] == "JMB"], "co2")
    plu_clean = G.clean(all_df[all_df["station"] == "PLU"], "co2")
    jmb_clean["month"] = jmb_clean["time_local"].dt.month
    plu_clean["month"] = plu_clean["time_local"].dt.month
    
    j_wet = jmb_clean[jmb_clean["month"].isin([11, 12, 1, 2, 3, 4])].groupby("hour_local")["co2"].median()
    j_dry = jmb_clean[jmb_clean["month"].isin([6, 7, 8, 9])].groupby("hour_local")["co2"].median()
    p_wet = plu_clean[plu_clean["month"].isin([11, 12, 1, 2, 3, 4])].groupby("hour_local")["co2"].median()
    p_dry = plu_clean[plu_clean["month"].isin([6, 7, 8, 9])].groupby("hour_local")["co2"].median()
    
    rows = [
        {
            "station": "JMB",
            "setting": "Drained peatland / plantation",
            "wet_season_min_ppm": round(j_wet.min(), 1),
            "wet_season_max_ppm": round(j_wet.max(), 1),
            "wet_season_amp_ppm": round(j_wet.max() - j_wet.min(), 1),
            "dry_season_min_ppm": round(j_dry.min(), 1),
            "dry_season_max_ppm": round(j_dry.max(), 1),
            "dry_season_amp_ppm": round(j_dry.max() - j_dry.min(), 1),
            "dry_to_wet_ratio": round((j_dry.max() - j_dry.min()) / (j_wet.max() - j_wet.min()), 2)
        },
        {
            "station": "PLU",
            "setting": "Montane primary rainforest",
            "wet_season_min_ppm": round(p_wet.min(), 1),
            "wet_season_max_ppm": round(p_wet.max(), 1),
            "wet_season_amp_ppm": round(p_wet.max() - p_wet.min(), 1),
            "dry_season_min_ppm": round(p_dry.min(), 1),
            "dry_season_max_ppm": round(p_dry.max(), 1),
            "dry_season_amp_ppm": round(p_dry.max() - p_dry.min(), 1),
            "dry_to_wet_ratio": round((p_dry.max() - p_dry.min()) / (p_wet.max() - p_wet.min()), 2)
        }
    ]
    df_out = pd.DataFrame(rows)
    df_out.to_csv(OUT / "t_jmb_seasonal_respiration.csv", index=False)
    return df_out


def main():
    print("Loading all.pkl...")
    all_df = G.load_all()
    print("1. Analyzing flask pairs (Finding 58)...")
    print(analyze_flask_pairs())
    print("\n2. Analyzing SF6 transport lag (Finding 59)...")
    print(analyze_sf6_lag())
    print("\n3. Analyzing vertical gradients (Finding 60)...")
    print(analyze_vertical_gradients())
    print("\n4. Analyzing H2 seasonality (Finding 61)...")
    h2_df, tr, lo, hi, _ = analyze_h2_seasonality()
    print(h2_df)
    print("\n5. Analyzing Bariri vs BKT (Finding 62)...")
    print(analyze_plu_vs_bkt(all_df))
    print("\n6. Analyzing Sorong marine baseline (Finding 63)...")
    print(analyze_srg_marine(all_df))
    print("\n7. Analyzing Kemayoran diurnal rush hour (Finding 64)...")
    print(analyze_kmy_diurnal_rush(all_df))
    print("\n8. Analyzing N2O ENSO Neff (Finding 65)...")
    print(analyze_n2o_enso_neff())
    print("\n9. Analyzing N2O decadal acceleration (Finding 66)...")
    print(analyze_n2o_acceleration())
    print("\n10. Analyzing Jambi peatland seasonal respiration (Finding 67)...")
    print(analyze_jmb_seasonal_respiration(all_df))
    print("\na26_extra4 complete. All 10 CSV tables written to outputs/.")


if __name__ == "__main__":
    main()
