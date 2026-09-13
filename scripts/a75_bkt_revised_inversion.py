#!/usr/bin/env python3
"""Methane inversion rerun on the revised transport ensemble (a74).

Builds the source-response operator from the three-seed, 2,000-particle,
widened-domain ensemble means, then refits the same four-component positive
Bayesian inversion as ``a49`` with identical priors, working covariance and
holdout split, so the change attributable to the transport revision is
isolated.  Two predeclared variants are fitted afterwards:

* ``tuned``      - transport-error fraction chosen so the training reduced
  chi-square (full covariance, whitened residuals at the posterior mode) is
  one, instead of the fixed 50 %.
* ``nearfield``  - anthropogenic emissions split at 50 km and 500 km (five
  source components) with the tuned covariance.

Outputs: ``outputs/hysplit/revision/inversion``.  Nothing in the original
inversion directory is modified.  Estimates remain conditional on GFS
transport without convective redistribution.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from pyproj import Geod
from scipy.stats import norm

from functools import lru_cache
from scipy.interpolate import RegularGridInterpolator

import a37_bkt_footprint as model
import a49_bkt_methane_inversion as inv
import a71_domain_budget_extension as ext
import a74_bkt_simulation_revision as rev
import a76_bkt_era5_driver as era
from a43_bkt_source_analysis import save_nc
from bkt_arl import ARLReader
from bkt_methane_inverse import InverseProblem, chain_diagnostics, correlated_error

ROOT = model.ROOT
OUT = ROOT / "outputs/hysplit/revision/inversion"
TABLES = OUT / "tables"
ORIGINAL = ROOT / "outputs/hysplit/inversion"
DRIVERS = {
    # run root, met file for a UTC day, output tree
    "gfs": dict(runs=rev.RUNS, met=lambda day: rev.WIDE_MET / f"{day:%Y%m%d}_gfs0p25", out=ROOT / "outputs/hysplit/revision/inversion"),
    "era5": dict(runs=era.RUNS, met=era.arl_path, out=ROOT / "outputs/hysplit/era5/inversion"),
}
DRIVER = "gfs"
GROUP = "ensemble"
COMPONENTS = inv.COMPONENTS
NEAR_COMPONENTS = ["anthro_within50", "anthro_50_500", "anthro_far", "wetlands", "fire"]


def redirect(out: Path) -> None:
    """Point the a49 stages at this output tree; the code path is unchanged."""
    global OUT, TABLES
    OUT, TABLES = out, out / "tables"
    inv.OUT, inv.TABLES = out, out / "tables"


def component_maps(field: xr.DataArray, monthly: xr.Dataset, fire: xr.Dataset) -> dict[str, np.ndarray]:
    month = xr.DataArray(pd.DatetimeIndex(field.time.values).to_period("M").to_timestamp(), dims="time")
    day = xr.DataArray(pd.DatetimeIndex(field.time.values).normalize(), dims="time")
    maps = {str(s): np.sum(field.values * monthly.flux.sel(source=s).sel(month=month).values, axis=0) * 1000
            for s in monthly.source.values}
    maps["noncrop_fire"] = np.sum(field.values * fire.noncrop_fire_flux.sel(day=day).values, axis=0) * 1000
    maps["crop_fire"] = np.sum(field.values * fire.crop_fire_flux.sel(day=day).values, axis=0) * 1000
    return maps


def member_dirs(stamp: pd.Timestamp) -> list[Path]:
    return [DRIVERS[DRIVER]["runs"] / f"{GROUP}_s{seed}" / f"bkt_{stamp:%Y%m%dT%H%MZ}" for seed in rev.SEEDS]


@lru_cache(maxsize=64)
def reader(path: str) -> ARLReader:
    return ARLReader(Path(path))


def endpoint_background(active: pd.DataFrame, stamp: pd.Timestamp, met_path: Path, height_shift: float = 0.) -> dict[str, float]:
    """Equal-weight CarbonTracker-CH4 at active endpoints; terrain from the driver's own ARL file."""
    arl = reader(str(met_path.resolve()))
    terrain = arl.field(stamp, "SHGT", 0)
    ground = RegularGridInterpolator((arl.lat, arl.lon), terrain)(active[["latitude", "longitude"]].to_numpy())
    height = active.height.to_numpy(float) + ground + height_shift
    path = ROOT / "data/bkt_sources/inversion/carbontracker" / f"CTCH4_2025.molefrac_glb3x2_{stamp:%Y-%m-%d}.nc"
    provenance = path.with_suffix(path.suffix + ".json")
    if not provenance.exists() or model.sha256_file(path) != json.loads(provenance.read_text())["sha256"]:
        raise ValueError(f"Unverified CarbonTracker boundary: {path}")
    with xr.open_dataset(path) as data:
        if data.ch4.attrs.get("units") != "nanomole mole-1" or data.gph.attrs.get("units") != "meters":
            raise ValueError("CarbonTracker units differ from expected CH4/height convention")
        sample = data.sel(time=stamp)[["ch4", "gph"]].interp(
            latitude=xr.DataArray(active.latitude.to_numpy(), dims="particle"),
            longitude=xr.DataArray(active.longitude.to_numpy(), dims="particle")).load()
    bounds = sample.gph.transpose("particle", "boundary").values
    centers = (bounds[:, :-1] + bounds[:, 1:]) / 2
    values = sample.ch4.transpose("particle", "level").values
    if not np.isfinite(bounds).all() or not np.isfinite(values).all() or (np.diff(bounds, axis=1) <= 0).any():
        raise ValueError("Invalid CarbonTracker vertical support")
    methane = np.asarray([np.interp(z, h, c) for z, h, c in zip(height, centers, values)])
    return dict(background_ppb=float(methane.mean()), endpoint_background_sd_ppb=float(methane.std()),
                endpoint_below_lowest_midlevel_percent=float(100 * (height < centers[:, 0]).mean()))


def native_surface(met_path: Path, stamp: pd.Timestamp) -> dict[str, float]:
    arl = reader(str(met_path.resolve()))
    return {name: arl.point(stamp, name, 0, -.202, 100.318, "nearest") for name in ("PBLH", "SHGT", "U10M", "V10M", "T02M")}


def operator(allow_partial: bool = False, limit: int = 0) -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    for name, source in (("monthly_prior_fluxes.nc", ext.INPUTS / "wide_monthly_flux.nc"),
                         ("daily_fire_prior_fluxes.nc", ext.INPUTS / "wide_daily_fire_flux.nc")):
        shutil.copyfile(source, OUT / name)
    with xr.open_dataset(OUT / "monthly_prior_fluxes.nc") as ds:
        monthly = ds.load()
    with xr.open_dataset(OUT / "daily_fire_prior_fluxes.nc") as ds:
        fire = ds.load()
    selection = pd.read_csv(ORIGINAL / "receptor_selection.csv", parse_dates=["time_utc"])
    selection.to_csv(OUT / "receptor_selection.csv", index=False)
    wanted = sorted(selection.loc[selection.retained, "time_utc"])
    if limit:
        wanted = wanted[:limit]
    # The footprint grid may be a subset of the wide flux grid (ERA5 uses 40 x 60 degrees).
    probe = next((d for stamp in wanted for d in member_dirs(stamp) if (d / "footprint.nc").exists()), None)
    if probe is None:
        raise FileNotFoundError("No completed runs for this driver and group")
    with xr.open_dataset(probe / "footprint.nc") as ds:
        glat, glon = ds.lat.values, ds.lon.values
    monthly = monthly.sel(lat=glat, lon=glon, method="nearest"); fire = fire.sel(lat=glat, lon=glon, method="nearest")
    if not np.allclose(monthly.lat.values, glat, atol=1e-6) or not np.allclose(monthly.lon.values, glon, atol=1e-6):
        raise ValueError("Footprint grid is not a subset of the flux grid")
    monthly = monthly.assign_coords(lat=glat, lon=glon); fire = fire.assign_coords(lat=glat, lon=glon)
    monthly.to_netcdf(OUT / "monthly_prior_fluxes.nc"); fire.to_netcdf(OUT / "daily_fire_prior_fluxes.nc")
    lat, lon = np.meshgrid(monthly.lat.values, monthly.lon.values, indexing="ij")
    _, _, distance = Geod(ellps="WGS84").inv(np.full(lon.shape, 100.318), np.full(lat.shape, -.202), lon, lat)
    distance /= 1000
    near, near50 = distance <= 500, distance <= 50
    receptor_cell = np.unravel_index(distance.argmin(), distance.shape)
    edge = np.zeros(near.shape, bool); edge[[0, -1], :] = True; edge[:, [0, -1]] = True
    rows, sectors, spatial, support, endpoints, lag_rows = [], [], [], [], [], []
    for stamp in wanted:
        dirs = [d for d in member_dirs(stamp) if (d / "completion_receipt.json").exists()]
        if len(dirs) != len(rev.SEEDS):
            if allow_partial and len(dirs) >= 2:
                print(f"partial ensemble for {stamp}: {len(dirs)} members", flush=True)
            elif allow_partial:
                continue
            else:
                raise FileNotFoundError(f"Ensemble incomplete for {stamp}: {len(dirs)} of {len(rev.SEEDS)}")
        member_rows, fields = [], []
        for directory in dirs:
            field, meta, actual = ext.read_footprint(directory)
            if not np.array_equal(field.lat.values, monthly.lat.values) or not np.array_equal(field.lon.values, monthly.lon.values):
                raise ValueError("Ensemble footprint grid differs from the wide flux grid")
            fields.append(field)
            active = ext.active_endpoints(directory, meta, actual)
            end = stamp - pd.Timedelta(hours=meta["configuration"]["hours_back"])
            met_end = DRIVERS[DRIVER]["met"](end)
            background = endpoint_background(active, end, met_end)
            up = endpoint_background(active, end, met_end, 500.)
            down = endpoint_background(active, end, met_end, -500.)
            maps = component_maps(field, monthly, fire)
            anthro = sum(v for k, v in maps.items() if k.startswith("CH4_"))
            member_rows.append(dict(seed=meta["configuration"]["seed"], emitted=actual, active=len(active),
                anthro_near_ppb=anthro[near].sum(), anthro_far_ppb=anthro[~near].sum(),
                anthro_within50_ppb=anthro[near50].sum(), anthro_50_500_ppb=anthro[near & ~near50].sum(),
                anthro_receptor_cell_ppb=anthro[receptor_cell],
                wetlands_ppb=maps["wetlands"].sum(), fire_ppb=maps["noncrop_fire"].sum(), crop_overlap_ppb=maps["crop_fire"].sum(),
                termites_ppb=maps["termites"].sum(), geological_ppb=maps["geological"].sum(), soil_uptake_ppb=maps["soil_uptake"].sum(),
                background_ppb=background["background_ppb"], background_height_plus500_ppb=up["background_ppb"],
                background_height_minus500_ppb=down["background_ppb"], endpoint_sd_ppb=background["endpoint_background_sd_ppb"],
                endpoint_below_midlevel_percent=background["endpoint_below_lowest_midlevel_percent"],
                sensitivity=float(field.sum())))
            for s in monthly.source.values:
                sectors.append(dict(group="ensemble", time_utc=stamp, seed=meta["configuration"]["seed"], source=str(s),
                                    prior_enhancement_ppb=float(maps[str(s)].sum())))
            endpoints.append(active.assign(receptor_utc=stamp, seed=meta["configuration"]["seed"]))
        members = pd.DataFrame(member_rows)
        mean = xr.concat(fields, dim="member").mean("member")
        maps = component_maps(mean, monthly, fire)
        anthro = sum(v for k, v in maps.items() if k.startswith("CH4_"))
        agg = mean.sum("time").values; total = float(agg.sum())
        hourly = mean.sum(("lat", "lon")).values
        lag = (stamp - pd.DatetimeIndex(mean.time.values)).total_seconds() / 3600
        for h, w in zip(lag, hourly):
            lag_rows.append(dict(group="ensemble", time_utc=stamp, lag_hours=h, sensitivity=w))
        native = native_surface(DRIVERS[DRIVER]["met"](stamp), stamp)
        numeric = [c for c in members.columns if c.endswith("_ppb") or c == "sensitivity"]
        row = dict(group="ensemble", time_utc=stamp, members=len(members), **members[numeric].mean().to_dict())
        row.update({f"{c}_seed_sd": float(members[c].std(ddof=1)) for c in
                    ("anthro_near_ppb", "anthro_far_ppb", "wetlands_ppb", "fire_ppb", "background_ppb", "sensitivity")})
        retention = members.active / members.emitted
        row.update(endpoint_count=int(members.active.sum()), emitted_particles=int(members.emitted.sum()),
            endpoint_survival_fraction=float(retention.min()), transport_usable=bool((retention >= .95).all()),
            within500_sensitivity_percent=100 * agg[near].sum() / total, within50_sensitivity_percent=100 * agg[near50].sum() / total,
            receptor_cell_sensitivity_percent=100 * agg[receptor_cell] / total,
            oldest24h_sensitivity_percent=100 * hourly[lag > mean.sizes["time"] - 24].sum() / total,
            edge_sensitivity_percent=100 * agg[edge].sum() / total, **native)
        rows.append(row)
        spatial.append(np.stack([anthro * near, anthro * ~near, maps["wetlands"], maps["noncrop_fire"]])); support.append(agg)
        print(f"operator {stamp}: near {row['anthro_near_ppb']:.1f} far {row['anthro_far_ppb']:.1f} "
              f"bg {row['background_ppb']:.1f} retention {retention.min():.3f}", flush=True)
    if not rows:
        raise ValueError("No ensemble receptors available")
    frame = pd.DataFrame(rows).sort_values("time_utc")
    frame = frame.merge(selection[["time_utc", "ch4", "co", "co2", "holdout"]], on="time_utc", validate="one_to_one")
    frame.to_csv(TABLES / "operator_base.csv", index=False)
    pd.DataFrame(sectors).to_csv(TABLES / "sector_responses_base.csv", index=False)
    pd.DataFrame(lag_rows).to_csv(TABLES / "lag_responses_base.csv", index=False)
    pd.concat(endpoints).to_csv(OUT / "endpoints_base.csv.gz", index=False, compression="gzip")
    ds = xr.Dataset({"prior_contribution": (("receptor", "component", "lat", "lon"), np.asarray(spatial)),
                     "footprint": (("receptor", "lat", "lon"), np.asarray(support)),
                     "distance_km": (("lat", "lon"), distance)},
                    coords={"receptor": frame.time_utc.values, "component": COMPONENTS,
                            "lat": monthly.lat.values, "lon": monthly.lon.values})
    ds.prior_contribution.attrs["units"] = "ppb"; ds.footprint.attrs["units"] = "ppm / (umol m-2 s-1)"
    save_nc(ds, OUT / "spatial_operator_base.nc")


def reduced_chi_square(p: InverseProblem, ntrain: int) -> float:
    theta, _, _ = p.fit()
    r = p.residual(theta)[:ntrain]
    return float(r @ r / ntrain)


def chi_square_scan(frame: pd.DataFrame, train: np.ndarray) -> tuple[float, pd.DataFrame]:
    rows = []
    for t in (.05, .1, .15, .2, .25, .3, .4, .5, .6, .8, 1.0):
        p, *_ = inv.problem(frame, train, transport=t)
        rows.append(dict(transport_fraction=t, reduced_chi_square=reduced_chi_square(p, int(train.sum()))))
    table = pd.DataFrame(rows)
    chi = table.reduced_chi_square.values; t = table.transport_fraction.values
    if chi.max() < 1:
        tuned = float(t[0])
    elif chi.min() > 1:
        tuned = float(t[-1])
    else:
        # chi-square decreases monotonically with the fraction; interpolate the crossing.
        tuned = float(np.interp(1.0, chi[::-1], t[::-1]))
    table["selected"] = np.isclose(table.transport_fraction, tuned)
    return tuned, table


def variant_fit(label: str, frame: pd.DataFrame, train: np.ndarray, k: np.ndarray, components: list[str],
                transport: float) -> dict:
    fixed = (frame.termites_ppb + frame.geological_ppb - frame.soil_uptake_ppb).to_numpy()
    b = np.column_stack([np.ones(len(frame)), (frame.time_utc - pd.Timestamp("2019-09-23")).dt.total_seconds() / (28 * 86400)])
    base = frame.background_ppb.to_numpy() + fixed
    y = frame.ch4.to_numpy() - base
    r = correlated_error(frame.time_utc, k.sum(axis=1), frame.time_utc.dt.hour.eq(18), transport_fraction=transport)
    r += np.diag((frame.termites_ppb + frame.geological_ppb + frame.soil_uptake_ppb).to_numpy() ** 2)
    sd = np.r_[np.repeat(np.log(2.), k.shape[1]), 20., 10.]
    p = InverseProblem(k[train], b[train], y[train], r[np.ix_(train, train)], sd)
    center, _, _ = p.fit()
    chains, accept = p.sample()
    rh, ess = chain_diagnostics(chains)
    if np.max(rh) > 1.01 or np.min(ess) < 1000:
        raise RuntimeError(f"{label}: convergence inadequate Rhat={rh} ESS={ess}")
    samples = chains.reshape(-1, p.ndim); ns = k.shape[1]
    names = components + ["background_offset", "background_trend"]
    rows = []
    for j, name in enumerate(names):
        v = np.exp(samples[:, j]) if j < ns else samples[:, j]
        q = np.quantile(v, [.025, .5, .975])
        rows.append(dict(case=label, parameter=name, posterior_mean=v.mean(), q025=q[0], median=q[1], q975=q[2],
            probability_above_inventory=float((v > 1).mean()) if j < ns else np.nan,
            variance_reduction_percent=100 * (1 - np.var(samples[:, j]) / sd[j] ** 2), rhat=rh[j], ess=ess[j]))
    pred = base[None, :] + np.exp(samples[:, :ns]) @ k.T + samples[:, ns:] @ b.T
    median = np.quantile(pred, .5, axis=0)
    chi = reduced_chi_square(p, int(train.sum()))
    evaluation = [dict(case=label, split=s, transport_fraction=transport, reduced_chi_square_training=chi,
                       **inv.metrics(frame.ch4[m], median[m]))
                  for s, m in (("training", train), ("heldout", ~train))]
    for kind in ("background_only", "inventory_adjusted"):
        pred_b = inv.baseline(frame, train, kind)
        evaluation += [dict(case=f"{label}_{kind}", split=s, transport_fraction=transport, reduced_chi_square_training=np.nan,
                            **inv.metrics(frame.ch4[m], pred_b[m])) for s, m in (("training", train), ("heldout", ~train))]
    return dict(parameters=rows, evaluation=evaluation, predictions=pd.DataFrame(dict(
        time_utc=frame.time_utc, holdout=~train, observed_ppb=frame.ch4, posterior_median_ppb=median,
        posterior_q025_ppb=np.quantile(pred, .025, axis=0), posterior_q975_ppb=np.quantile(pred, .975, axis=0),
        mismatch_sd_ppb=np.sqrt(np.diag(r)))).assign(case=label))


def variants() -> None:
    frame = inv.load_complete_operator()
    frame = frame[frame.transport_usable].reset_index(drop=True)
    train = (~frame.holdout).to_numpy()
    tuned, scan = chi_square_scan(frame, train)
    scan.to_csv(TABLES / "transport_error_scan.csv", index=False)
    k4 = frame[[c + "_ppb" for c in COMPONENTS]].to_numpy()
    k5 = frame[[c + "_ppb" for c in NEAR_COMPONENTS]].to_numpy()
    if not np.allclose(k5[:, 0] + k5[:, 1], k4[:, 0]):
        raise ValueError("Near-field split does not reconstruct the within-500 km component")
    results = [variant_fit("base_fixed50", frame, train, k4, COMPONENTS, .5),
               variant_fit("tuned", frame, train, k4, COMPONENTS, tuned),
               variant_fit("nearfield_tuned", frame, train, k5, NEAR_COMPONENTS, tuned)]
    pd.DataFrame([r for v in results for r in v["parameters"]]).to_csv(TABLES / "variant_parameters.csv", index=False)
    pd.DataFrame([r for v in results for r in v["evaluation"]]).to_csv(TABLES / "variant_evaluation.csv", index=False)
    pd.concat([v["predictions"] for v in results]).to_csv(TABLES / "variant_predictions.csv", index=False)
    (OUT / "variants.json").write_text(json.dumps(dict(tuned_transport_fraction=tuned,
        note="tuned: training reduced chi-square of one at the posterior mode; nearfield: 50/500 km anthropogenic split"),
        indent=2) + "\n")
    print(pd.DataFrame([r for v in results for r in v["parameters"]]).to_string(index=False), flush=True)


def comparison() -> None:
    """Old (540-particle, original domain) versus revised operator and posterior."""
    old = pd.read_csv(ORIGINAL / "tables/operator_base.csv", parse_dates=["time_utc"]).set_index("time_utc")
    new = pd.read_csv(TABLES / "operator_base.csv", parse_dates=["time_utc"]).set_index("time_utc")
    rows = []
    for stamp, r in new.iterrows():
        o = old.loc[stamp]
        rows.append(dict(time_utc=stamp, originally_usable=bool(o.transport_usable), now_usable=bool(r.transport_usable),
            **{f"{c}_old_ppb": o[f"{c}_ppb"] for c in COMPONENTS}, **{f"{c}_new_ppb": r[f"{c}_ppb"] for c in COMPONENTS},
            background_old_ppb=o.background_ppb, background_new_ppb=r.background_ppb,
            retention_old=o.endpoint_survival_fraction, retention_new=r.endpoint_survival_fraction,
            near_seed_sd_new_ppb=r.anthro_near_ppb_seed_sd, far_seed_sd_new_ppb=r.anthro_far_ppb_seed_sd))
    pd.DataFrame(rows).to_csv(TABLES / "operator_comparison.csv", index=False)
    parts = []
    for label, path in (("original", ORIGINAL / "tables/posterior_parameters.csv"), ("revised", TABLES / "posterior_parameters.csv")):
        if path.exists():
            parts.append(pd.read_csv(path).assign(case=label))
    pd.concat(parts).to_csv(TABLES / "posterior_comparison.csv", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["operator", "fit", "robustness", "synthetic", "budget", "variants", "comparison", "all"])
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--driver", default="gfs", choices=list(DRIVERS))
    parser.add_argument("--group", default="ensemble", help="run-group prefix (ensemble, or anchor for a test)")
    parser.add_argument("--limit", type=int, default=0, help="process only the first N receptors (testing)")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    DRIVER, GROUP = args.driver, args.group
    redirect(args.out or DRIVERS[DRIVER]["out"])
    stages = {"operator": lambda: operator(args.allow_partial, args.limit), "fit": inv.run, "robustness": inv.robustness,
              "synthetic": inv.synthetic, "budget": inv.emission_budget, "variants": variants, "comparison": comparison}
    for name in (["operator", "fit", "robustness", "synthetic", "budget", "variants", "comparison"] if args.stage == "all" else [args.stage]):
        print(f"== {name}", flush=True); stages[name]()
