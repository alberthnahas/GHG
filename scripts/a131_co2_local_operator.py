#!/usr/bin/env python3
"""Local-inventory CO2 terms for every CO2 receptor at BKT and Jambi, 2023-2025.

For each receptor of the CO2 inversion (a113 frames for 2023 and 2024, a129 rows
for 2025) the seed-mean HYSPLIT footprint is convolved with two fields from the
local CO2 inventory outputs/inventory/local_inventory_co2_2023_full.nc (a100):

* local_fossil_ppm: the eight EDGAR sectors rescaled to Indonesia's reported
  2023 national totals (PRIMAP-hist v2.6.1 HISTCR, country-reported), the
  gridded pattern unchanged; outside the inventory domain the period's own EDGAR
  fossil field is used, so only the Indonesian magnitude changes;
* peat_drainage_ppm: FOLU 3B1, drained-peat CO2 on the a101 proxy, which no
  global fossil inventory carries.

Both are annual (2023) and held constant in time; the a113 multipliers absorb
the year-to-year level.  Writes outputs/hysplit/two_receptor/tables/co2_local_terms.csv.
"""
from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G
import a127_hysplit_2025_2026 as H

LOCAL = G.OUT / "inventory" / "local_inventory_co2_2023_full.nc"
FOSSIL = ["AGRICULTURE", "BUILDINGS", "FUEL_EXPLOITATION", "IND_COMBUSTION", "IND_PROCESSES",
          "POWER_INDUSTRY", "TRANSPORT", "WASTE"]
TWO = H.OUT


def T():
    import a84_bkt_jmb_two_receptor as mod
    return mod


@lru_cache(maxsize=4)
def local_fields(code):
    lat, lon = T().receptor_grid(code)
    with xr.open_dataset(LOCAL) as ds:
        fos = sum(ds[s].values for s in FOSSIL)
        peat = ds["FOLU_3B1"].values
        la, lo = ds.lat.values, ds.lon.values
    glat, glon = np.meshgrid(la, lo, indexing="ij")
    i = np.round((glat - lat[0]) / (lat[1] - lat[0])).astype(int)
    k = np.round((glon - lon[0]) / (lon[1] - lon[0])).astype(int)
    ok = (i >= 0) & (i < len(lat)) & (k >= 0) & (k < len(lon))
    out_f, out_p = np.zeros((len(lat), len(lon))), np.zeros((len(lat), len(lon)))
    np.add.at(out_f, (i[ok], k[ok]), np.nan_to_num(fos[ok]))
    np.add.at(out_p, (i[ok], k[ok]), np.nan_to_num(peat[ok]))
    cover = np.zeros_like(out_f, bool)
    cover[i[ok], k[ok]] = True
    area = (0.25 * 111_320.0) ** 2 * np.cos(np.radians(lat))[:, None]
    to_flux = 1000.0 / 44.01 / (365.25 * 86400) * 1e6 / area      # kg yr-1 per cell -> umol m-2 s-1
    return out_f * to_flux, out_p * to_flux, cover


@lru_cache(maxsize=8)
def edgar_mean(code, year):
    import a89_bkt_jmb_co2 as C
    if year == 2023:
        p = C.INPUTS / f"{code.lower()}_fossil_monthly.nc"
    elif year == 2024:
        p = C.INPUTS / f"{code.lower()}_fossil_monthly_2024.nc"
    else:
        p = H.OUT / "inputs_2025_2026" / f"{code.lower()}_fossil_monthly_2025_from2024.nc"
    with xr.open_dataset(p) as ds:
        return ds.flux.sum("sector").mean("month").values


def run_dirs(code, stamp):
    tag = f"bkt_{stamp:%Y%m%dT%H%MZ}"
    if stamp.year == 2023:
        roots = [TWO / "runs" / f"{code.lower()}_s{s}" for s in (0, -10, -20)]
    elif stamp.year == 2024:
        roots = [TWO / "runs_2024" / f"{code.lower()}_s{s}" for s in (0, -10)]
    else:
        roots = [H.RUNS / f"{code.lower()}_s0"]
    return [r / tag for r in roots if (r / tag / "completion_receipt.json").exists()]


def receptors():
    import a113_operational_service as S
    base = S.frames()["co2"][["station", "time_utc"]]
    new = pd.read_csv(H.TABLES / "co2_operator_2025.csv", parse_dates=["time_utc"])[["station", "time_utc"]]
    return pd.concat([base, new], ignore_index=True).drop_duplicates()


def main():
    ext = T().ext
    path = H.TABLES / "co2_local_terms.csv"
    old = pd.read_csv(path, parse_dates=["time_utc"]) if path.exists() else pd.DataFrame(columns=["station", "time_utc"])
    have = set(zip(old.station, old.time_utc))
    rows = []
    for r in receptors().itertuples():
        if (r.station, r.time_utc) in have:
            continue
        dirs = run_dirs(r.station, r.time_utc)
        if not dirs:
            continue
        fos, peat, cover = local_fields(r.station)
        fos = np.where(cover, fos, edgar_mean(r.station, r.time_utc.year))
        vals = []
        for d in dirs:
            field, meta, actual = ext.read_footprint(d)
            tot = field.values.sum(axis=0)
            vals.append(((tot * fos).sum(), (tot * peat).sum()))
        v = np.mean(vals, axis=0)
        rows.append(dict(station=r.station, time_utc=r.time_utc, members=len(dirs),
                         local_fossil_ppm=float(v[0]), peat_drainage_ppm=float(v[1])))
        if len(rows) % 50 == 0:
            print(len(rows), "rows", flush=True)
    out = pd.concat([old, pd.DataFrame(rows)], ignore_index=True)
    out.to_csv(path, index=False)
    print(f"wrote {len(out)} rows ({len(rows)} new)")
    print(out.groupby([out.station, pd.to_datetime(out.time_utc).dt.year])[["local_fossil_ppm", "peat_drainage_ppm"]]
          .median().round(2))


if __name__ == "__main__":
    main()
