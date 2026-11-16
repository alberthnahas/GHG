"""Loader for the October 2026 re-export of the five-station hourly archive.

Source: obs/grk_hourly_avg_<code>.csv (downloaded by Alberth, 8 October 2026).
Columns: TANGGAL, JAM, STASIUN, RATA_co, RATA_co2, RATA_ch4, RATA_co2d, RATA_ch4d,
RATA_h2o.  Written to outputs/all_2026.pkl with the same schema as outputs/all.pkl
so the existing analysis code can read either.

What was verified against the previous archive (grk_hourly_*.json) before use:

* JMB, KMY, PLU, SRG: every overlapping hour is identical at the same stamp
  (JMB 14,486 of 14,486; PLU 99.96 %), so the stamps are UTC as before and CO
  and CH4 are in ppm, as before.  The new files only add hours after the old
  archive ended (JMB: 2025-12-03 -> 2026-10-07).
* BKT is a different product.  It starts 2018-11-08 rather than 2001, every
  species is in ppm (the old file had CH4 and CO in ppb), and the stamps are
  UTC throughout: the afternoon CO2 minimum falls at 07 UTC in 2019 and 2020 as
  well as afterwards, where the old file needed the WIB->UTC correction before
  2021.  Its CO2 reads 3.4-4.0 ppm below the old archive on the same hours
  (r = 0.994), and 3.6 ppm below the NOAA flasks (median flask minus in-situ,
  n = 217, 2019-2025), where the old archive agreed with them to 0.1 ppm.  CH4
  and CO agree with the flasks to within about 1 and 4 ppb.  So the BKT CO2
  calibration scale of this export is offset; BKT_CO2_FLASK_OFFSET carries the
  flask-anchored correction, applied only where an absolute BKT CO2 level is
  needed (the inversion) and always reported when it is.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G

OBS = G.ROOT / "obs"
EXPORT_DATE = "2026-10-08"

# Median NOAA flask minus new-export in-situ CO2 at BKT, matched hours 2019-2025
# (n = 217).  Recomputed by flask_offsets() and written to obs2026_flask_check.csv.
BKT_CO2_FLASK_OFFSET = 3.62


def load_station_2026(code):
    """Hourly frame in harmonised units, same columns as ghg_common.load_station."""
    raw = pd.read_csv(OBS / f"grk_hourly_avg_{code.lower()}.csv")
    co2 = pd.to_numeric(raw["RATA_co2d"], errors="coerce").fillna(
        pd.to_numeric(raw["RATA_co2"], errors="coerce"))
    ch4 = pd.to_numeric(raw["RATA_ch4d"], errors="coerce").fillna(
        pd.to_numeric(raw["RATA_ch4"], errors="coerce")) * 1000.0
    co = pd.to_numeric(raw["RATA_co"], errors="coerce") * 1000.0
    out = pd.DataFrame({"station": code, "co2": co2, "ch4": ch4, "co": co})
    out["time"] = pd.to_datetime(raw["TANGGAL"]) + pd.to_timedelta(raw["JAM"], unit="h")

    for c, (lo, hi) in G.LIM.items():
        out.loc[(out[c] < lo) | (out[c] > hi), c] = np.nan
    out = out.dropna(subset=["co2", "ch4", "co"], how="all")
    out = out.drop_duplicates(subset=["time"]).sort_values("time").reset_index(drop=True)

    utc_off = G.STATIONS[code][6]
    out["time_utc"] = out["time"]                       # UTC throughout, all five
    out["time_local"] = out["time_utc"] + pd.Timedelta(hours=utc_off)
    tl = out["time_local"]
    out["utc_offset"] = utc_off
    out["hour_local"] = tl.dt.hour
    out["year"] = tl.dt.year
    out["month"] = tl.dt.month
    out["date"] = tl.dt.normalize()
    out["dow"] = tl.dt.dayofweek
    out["doy"] = tl.dt.dayofyear
    out["decyear"] = out["year"] + (tl.dt.dayofyear - 1 + tl.dt.hour / 24.0) / \
        np.where(tl.dt.is_leap_year, 366.0, 365.0)
    return out


def load_all_2026():
    return G.apply_flags(pd.concat([load_station_2026(c) for c in G.ORDER],
                                   ignore_index=True))


def overlap_check():
    """Agreement with the previous archive on shared hours, per station and species."""
    rows = []
    for code in G.ORDER:
        old = G.load_station(code).drop_duplicates("time_utc").set_index("time_utc")
        new = load_station_2026(code).set_index("time_utc")
        for sp in ("co2", "ch4", "co"):
            j = pd.concat([old[sp].rename("old"), new[sp].rename("new")], axis=1).dropna()
            d = j.new - j.old
            rows.append(dict(station=code, species=sp, n_shared=len(j),
                             identical_frac=float(np.isclose(j.new, j.old, atol=1e-3).mean()) if len(j) else np.nan,
                             median_new_minus_old=float(d.median()) if len(j) else np.nan,
                             r=float(np.corrcoef(j.new, j.old)[0, 1]) if len(j) > 2 else np.nan,
                             old_last=str(old.index.max()), new_last=str(new.index.max()),
                             new_hours_after_old=int((new.index > old.index.max()).sum())))
    return pd.DataFrame(rows)


def flask_offsets():
    import noaa_flask as nf
    new = load_station_2026("BKT").set_index("time_utc")
    rows = []
    for sp in ("co2", "ch4", "co"):
        fl = nf.events(sp)
        j = pd.concat([fl.rename("flask"), new[sp].rename("insitu")], axis=1,
                      join="inner").dropna()
        j = j[j.index >= "2019-01-01"]
        d = j.flask - j.insitu
        rows.append(dict(station="BKT", species=sp, n=len(j),
                         median_flask_minus_insitu=float(d.median()),
                         iqr_lo=float(d.quantile(0.25)), iqr_hi=float(d.quantile(0.75)),
                         r=float(np.corrcoef(j.flask, j.insitu)[0, 1]),
                         first=str(j.index.min()), last=str(j.index.max())))
    return pd.DataFrame(rows)


def main():
    d = load_all_2026()
    d.to_pickle(G.OUT / "all_2026.pkl")
    ov = overlap_check()
    ov.to_csv(G.OUT / "obs2026_overlap_check.csv", index=False)
    fo = flask_offsets()
    fo.to_csv(G.OUT / "obs2026_flask_check.csv", index=False)
    print(ov.to_string(index=False))
    print(fo.to_string(index=False))
    print(d.groupby("station").time_utc.agg(["min", "max", "size"]))


if __name__ == "__main__":
    main()
