#!/usr/bin/env python3
"""Footprint operator for the 2025-2026 HYSPLIT campaign (a127).

For every completed run at Jambi (JMB) and Bukit Kototabang (BKT) this convolves
the hourly HYSPLIT-STILT surface sensitivity with:

* daily NASA FIRMS high-confidence hotspots gridded on the footprint grid, by
  province group (Jambi, Sumatera Selatan, Riau, Sumatera Barat, other land,
  outside Indonesia) and by peat (mapped peat fraction of the cell): the fire
  exposure, in hotspot x (ppm per umol m-2 s-1);
* the CH4 prior of the two-receptor study for the same calendar month:
  EDGAR v8 2022 monthly anthropogenic (8 sectors), LPJ-MERRA2 2023 wetlands,
  termites, geological, MeMo soil uptake, each also split on peat;
* the sensitivity itself, by province group.

It also records the transport screens the earlier campaign used: terminal
endpoint survival and GDAS1 boundary-layer depth at the tower at 06 UTC.

Observations: afternoon means (05-07 UTC, at least two valid hours) of CO, CH4
and CO2 from outputs/all_2026.pkl (a120).  BKT CO2 carries the flask-anchored
+3.62 ppm (a120.BKT_CO2_FLASK_OFFSET) so that it sits on the scale of the old
archive and the NOAA flasks.

Writes outputs/hysplit/two_receptor/tables/footprint_operator_2025_2026.csv and
mean footprint and fire-contribution maps per window and tower (npz).
"""
from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G
import a127_hysplit_2025_2026 as H
from a120_obs2026 import BKT_CO2_FLASK_OFFSET

TABLES = H.TABLES
INPUTS = H.OUT / "inputs_2025_2026"
HOTSPOT = G.ROOT.parent / "HOTSPOT" / "archived_hotspot_idn.csv"
PROV = G.ROOT.parent / ".assets" / "indonesia_38prov.geojson"
GROUPS = ["JAMBI", "SUMATERA SELATAN", "RIAU", "SUMATERA BARAT", "OTHER_IDN", "OUTSIDE"]
ANTHRO = ["CH4_AGRICULTURE", "CH4_BUILDINGS", "CH4_FUEL_EXPLOITATION", "CH4_IND_COMBUSTION",
          "CH4_IND_PROCESSES", "CH4_POWER_INDUSTRY", "CH4_TRANSPORT", "CH4_WASTE"]


def T():
    import a84_bkt_jmb_two_receptor as mod
    return mod


@lru_cache(maxsize=2)
def grid(code):
    return T().receptor_grid(code)


@lru_cache(maxsize=2)
def province_index(code):
    """Cell-centre group index on the tower grid (disjoint by construction)."""
    import geopandas as gpd
    lat, lon = grid(code)
    p = gpd.read_file(PROV)
    p["geometry"] = p.geometry.make_valid()
    col = [c for c in p.columns if p[c].astype(str).str.upper().str.contains("JAMBI").any()][0]
    p["NAME"] = p[col].astype(str).str.upper().str.strip()
    glat, glon = np.meshgrid(lat, lon, indexing="ij")
    pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(glon.ravel(), glat.ravel()), crs=p.crs)
    j = gpd.sjoin(pts, p[["NAME", "geometry"]], how="left", predicate="within")
    j = j[~j.index.duplicated()]
    name = j["NAME"].reindex(range(len(pts))).fillna("OUTSIDE").values
    grp = np.where(np.isin(name, GROUPS[:4]), name, np.where(name == "OUTSIDE", "OUTSIDE", "OTHER_IDN"))
    return np.array([GROUPS.index(g) for g in grp]).reshape(glat.shape)


@lru_cache(maxsize=2)
def near_mask(code):
    from pyproj import Geod
    lat, lon = grid(code)
    glat, glon = np.meshgrid(lat, lon, indexing="ij")
    _, rlat, rlon, _ = T().STATIONS[code]
    _, _, d = Geod(ellps="WGS84").inv(np.full(glon.shape, rlon), np.full(glat.shape, rlat), glon, glat)
    return d / 1000 <= 500


DEMO_GRID = G.ROOT / "demo" / "data" / "demo_grids.js"


@lru_cache(maxsize=1)
def demo_grid():
    import json as _j
    t = DEMO_GRID.read_text()
    return _j.loads(t[t.index("{"):t.rindex("}") + 1])["grid"]


def to_demo(field, code):
    """Tower-grid field onto the demo display grid, rescaled so its total over the crop is kept."""
    g = demo_grid()
    lat, lon = grid(code)
    la = g["lat0"] + np.arange(g["ny"]) * g["dlat"]
    lo = g["lon0"] + np.arange(g["nx"]) * g["dlon"]
    i = np.clip(np.round((la - lat[0]) / (lat[1] - lat[0])).astype(int), 0, len(lat) - 1)
    k = np.clip(np.round((lo - lon[0]) / (lon[1] - lon[0])).astype(int), 0, len(lon) - 1)
    return field[np.ix_(i, k)].astype(np.float32)


@lru_cache(maxsize=2)
def peat(code):
    with xr.open_dataset(T().INPUTS / f"peat_fraction_{code.lower()}.nc") as ds:
        return ds.peat_fraction.values.astype(float)


@lru_cache(maxsize=2)
def ch4_prior(code):
    """Twelve calendar months of the two-receptor CH4 prior on this tower's grid (cached)."""
    INPUTS.mkdir(parents=True, exist_ok=True)
    path = INPUTS / f"{code.lower()}_ch4_monthly_climatology.nc"
    if not path.exists():
        mod = T()
        saved = mod.MONTHS
        mod.MONTHS = pd.date_range("2023-01-01", periods=12, freq="MS")
        try:
            ds = mod.monthly_inputs(*grid(code))
        finally:
            mod.MONTHS = saved
        ds.attrs["note"] = "EDGAR v8 2022 monthly and LPJ-MERRA2 2023 monthly, used by calendar month for 2025-2026"
        ds.to_netcdf(path)
    with xr.open_dataset(path) as ds:
        return ds.load()


LOCAL_CH4 = G.OUT / "inventory" / "local_inventory_ch4_2022_provincial.nc"
LOCAL_SECTORS = ["AGRICULTURE", "BUILDINGS", "FUEL_EXPLOITATION", "IND_COMBUSTION", "IND_PROCESSES",
                 "POWER_INDUSTRY", "TRANSPORT", "WASTE"]      # FOLU_3B2 left out: fire enters through hotspots


@lru_cache(maxsize=2)
def local_ch4(code):
    """Local anthropogenic CH4 (Indonesia's reported national totals split to provinces, a100/a108) on the
    tower grid, umol m-2 s-1, annual.  Cells outside the inventory domain take EDGAR (handled by the caller)."""
    lat, lon = grid(code)
    with xr.open_dataset(LOCAL_CH4) as ds:
        kg = sum(ds[s_].values for s_ in LOCAL_SECTORS)          # kg yr-1 per 0.1 degree cell
        la, lo = ds.lat.values, ds.lon.values
    glat, glon = np.meshgrid(la, lo, indexing="ij")
    i = np.round((glat - lat[0]) / (lat[1] - lat[0])).astype(int)
    k = np.round((glon - lon[0]) / (lon[1] - lon[0])).astype(int)
    ok = (i >= 0) & (i < len(lat)) & (k >= 0) & (k < len(lon)) & np.isfinite(kg)
    out = np.zeros((len(lat), len(lon)))
    np.add.at(out, (i[ok], k[ok]), kg[ok])
    cover = np.zeros_like(out, bool)
    cover[i[ok], k[ok]] = True
    area = (0.25 * 111_320.0) ** 2 * np.cos(np.radians(lat))[:, None]
    flux = out * 1000.0 / 16.04 / (365.25 * 86400) * 1e6 / area
    with xr.open_dataset(LOCAL_CH4) as ds:
        fk = ds["FUEL_EXPLOITATION"].values
    fuel = np.zeros_like(out)
    okf = ok & np.isfinite(fk)
    np.add.at(fuel, (i[okf], k[okf]), fk[okf])
    return flux, cover, fuel * 1000.0 / 16.04 / (365.25 * 86400) * 1e6 / area


@lru_cache(maxsize=1)
def hotspots():
    h = pd.read_csv(HOTSPOT)
    h = h[(h.year >= 2025)].copy()
    h["date"] = pd.to_datetime(dict(year=h.year, month=h.month, day=h.day))
    return h


@lru_cache(maxsize=4)
def hotspot_grid(code, first, last):
    """Daily hotspot counts on the tower grid, days first..last (strings)."""
    lat, lon = grid(code)
    d = pd.date_range(first, last, freq="D")
    h = hotspots()
    h = h[(h.date >= d[0]) & (h.date <= d[-1])]
    dlat, dlon = lat[1] - lat[0], lon[1] - lon[0]
    i = np.round((h.lat.values - lat[0]) / dlat).astype(int)
    k = np.round((h.lon.values - lon[0]) / dlon).astype(int)
    ok = (i >= 0) & (i < len(lat)) & (k >= 0) & (k < len(lon))
    out = np.zeros((len(d), len(lat), len(lon)), np.float32)
    di = (h.date.values[ok] - d[0].to_datetime64()) // np.timedelta64(1, "D")
    np.add.at(out, (di.astype(int), i[ok], k[ok]), 1)
    return d, out


def afternoon_obs():
    d = pd.read_pickle(G.OUT / "all_2026.pkl")
    d = d[d.station.isin(H.STATIONS) & d.time_utc.dt.hour.isin([5, 6, 7])].copy()
    d.loc[d.station.eq("BKT"), "co2"] += BKT_CO2_FLASK_OFFSET
    rows = []
    for (st, day), g in d.groupby(["station", d.time_utc.dt.normalize()]):
        r = dict(station=st, time_utc=day + pd.Timedelta(hours=6))
        for sp in ("co2", "ch4", "co"):
            v = g.loc[~g["suspect_" + sp], sp].dropna()
            r[f"{sp}_obs"] = v.mean() if len(v) >= 2 else np.nan
            r[f"{sp}_hours"] = len(v)
        rows.append(r)
    return pd.DataFrame(rows)


def one(code, stamp, keep_maps=False):
    mod = T()
    ext = mod.ext
    directory = H.run_dir(code, stamp)
    field, meta, actual = ext.read_footprint(directory)
    f = field.values                                   # (120, lat, lon), ppm per umol m-2 s-1
    hours = pd.DatetimeIndex(field.time.values)
    tot = f.sum(axis=0)
    pidx = province_index(code)
    pf = peat(code)
    row = dict(station=code, time_utc=stamp, sensitivity=float(tot.sum()))
    for gi, g in enumerate(GROUPS):
        row[f"sens_{g}"] = float(tot[pidx == gi].sum())
    # fire exposure
    first = hours[0].normalize() - pd.Timedelta(days=1)
    days, hg = hotspot_grid(code, str(first.date()), str(stamp.normalize().date()))
    di = ((hours.normalize() - days[0]) // pd.Timedelta(days=1)).astype(int)
    fire_map = np.zeros_like(tot)
    fire_map2 = np.zeros_like(tot)          # same and previous UTC day: smouldering persists
    for t in range(len(hours)):
        fire_map += f[t] * hg[di[t]]
        fire_map2 += f[t] * (hg[di[t]] + hg[di[t] - 1])
    for gi, g in enumerate(GROUPS):
        row[f"fireexp_{g}"] = float(fire_map[pidx == gi].sum())
    row["fireexp_total"] = float(fire_map.sum())
    row["fireexp_peat"] = float((fire_map * pf).sum())
    row["fireexp2_total"] = float(fire_map2.sum())
    row["fireexp2_peat"] = float((fire_map2 * pf).sum())
    for gi, g in enumerate(GROUPS):
        row[f"fireexp2_{g}"] = float(fire_map2[pidx == gi].sum())
    row["hotspots_window"] = int(hg.sum())
    # CH4 prior, ppb, by calendar month of each footprint hour
    pr = ch4_prior(code)
    flux = pr.flux.values                              # (source, 12, lat, lon)
    src = list(pr.source.values)
    months = hours.month.values - 1
    per_month = np.zeros((12,) + tot.shape)
    for m in np.unique(months):
        per_month[m] = f[months == m].sum(axis=0)
    anth = sum(flux[src.index(s)] for s in ANTHRO)     # (12, lat, lon)

    def conv(F, w=None):
        w = 1.0 if w is None else w
        return float(sum((per_month[m] * F[m] * w).sum() for m in np.unique(months)) * 1000.0)
    row["ch4_anthro_ppb"] = conv(anth)
    row["ch4_anthro_peat_ppb"] = conv(anth, pf)
    row["ch4_wetlands_ppb"] = conv(flux[src.index("wetlands")])
    row["ch4_wetlands_peat_ppb"] = conv(flux[src.index("wetlands")], pf)
    loc, cover, locfuel = local_ch4(code)
    loc12 = np.where(cover[None], loc[None], anth)                # local inside its domain, EDGAR outside
    row["ch4_local_ppb"] = conv(loc12)
    row["ch4_local_peat_ppb"] = conv(loc12, pf)
    for gi, g in enumerate(GROUPS):
        row[f"ch4_local_{g}"] = conv(loc12, (pidx == gi).astype(float))
    # within / beyond 500 km of the tower and the fuel-exploitation sector, as the 2023 demo state vector
    near = (near_mask(code)).astype(float)
    fuel12 = flux[src.index("CH4_FUEL_EXPLOITATION")]
    lfuel12 = np.where(cover[None], locfuel[None], fuel12)
    for tag, A, Fu in (("local", loc12, lfuel12), ("edgar", anth, fuel12)):
        row[f"{tag}_near_ppb"] = conv(A, near)
        row[f"{tag}_far_ppb"] = conv(A, 1 - near)
        row[f"{tag}_fuel_near_ppb"] = conv(Fu, near)
        row[f"{tag}_other_near_ppb"] = row[f"{tag}_near_ppb"] - row[f"{tag}_fuel_near_ppb"]
    row["within500_sensitivity_percent"] = float(100 * (tot * near).sum() / tot.sum())
    row["ch4_natural_other_ppb"] = conv(flux[src.index("termites")] + flux[src.index("geological")]) - conv(flux[src.index("soil_uptake")])
    for gi, g in enumerate(GROUPS):
        mask = (pidx == gi).astype(float)
        row[f"ch4_anthro_{g}"] = conv(anth, mask)
        row[f"ch4_wetlands_{g}"] = conv(flux[src.index("wetlands")], mask)
    # transport screens
    active = ext.active_endpoints(directory, meta, actual)
    row["endpoint_survival_fraction"] = len(active) / actual
    import a37_bkt_footprint as model
    week = H.MET / model.gdas1_week_name(stamp.normalize())
    try:
        surf = mod.native_surface(code, week, stamp)
        row["PBLH"] = surf.get("PBLH")
    except Exception as e:  # noqa: BLE001 - recorded, screened later
        row["PBLH"] = np.nan
        row["pblh_error"] = type(e).__name__
    maps = (tot.astype(np.float32), fire_map.astype(np.float32), to_demo(tot, code)) if keep_maps else None
    return row, maps


def main():
    sel = pd.read_csv(TABLES / "receptors_2025_2026.csv", parse_dates=["time_utc"])
    done = [(r.window, r.station, r.time_utc) for r in sel.itertuples()
            if (H.run_dir(r.station, r.time_utc) / "completion_receipt.json").exists()]
    print(f"{len(done)} of {len(sel)} runs complete", flush=True)
    path = TABLES / "footprint_operator_2025_2026.csv"
    old = pd.read_csv(path, parse_dates=["time_utc"]) if path.exists() else pd.DataFrame()
    have = set(zip(old.station, old.time_utc)) if len(old) else set()
    rows, mapsum, demo_fp = [], {}, {}
    for w, st, s in done:
        if (st, s) in have:
            continue
        r, maps = one(st, s, keep_maps=True)
        r["window"] = w
        rows.append(r)
        key = (w, st)
        a, b, n = mapsum.get(key, (0, 0, 0))
        mapsum[key] = (a + maps[0], b + maps[1], n + 1)
        demo_fp[f"{st}|{s:%Y-%m-%dT%H:%MZ}"] = maps[2]
        if len(rows) % 20 == 0:
            print(f"  {len(rows)} new rows", flush=True)
    new = pd.DataFrame(rows)
    out = pd.concat([old, new], ignore_index=True) if len(old) else new
    obs = afternoon_obs()
    out = out.drop(columns=[c for c in out.columns if c.endswith("_obs") or c.endswith("_hours")], errors="ignore")
    out = out.merge(obs, on=["station", "time_utc"], how="left")
    out.sort_values(["station", "time_utc"]).to_csv(path, index=False)
    # running sums of maps, merged with any previous ones
    mp = TABLES / "footprint_maps_2025_2026.npz"
    prev = dict(np.load(mp, allow_pickle=True)) if mp.exists() else {}
    for (w, st), (a, b, n) in mapsum.items():
        k = f"{w}|{st}"
        if f"{k}|sens" in prev:
            prev[f"{k}|sens"] = prev[f"{k}|sens"] + a
            prev[f"{k}|fire"] = prev[f"{k}|fire"] + b
            prev[f"{k}|n"] = prev[f"{k}|n"] + n
        else:
            prev[f"{k}|sens"], prev[f"{k}|fire"], prev[f"{k}|n"] = a, b, np.array(n)
    for st in H.STATIONS:
        lat, lon = grid(st)
        prev[f"{st}|lat"], prev[f"{st}|lon"] = lat, lon
    np.savez_compressed(mp, **prev)
    dp = TABLES / "footprints_demo_grid_2025_2026.npz"
    prevd = dict(np.load(dp)) if dp.exists() else {}
    prevd.update(demo_fp)
    np.savez_compressed(dp, **prevd)
    print(f"wrote {len(out)} rows ({len(new)} new)", flush=True)


if __name__ == "__main__":
    main()
