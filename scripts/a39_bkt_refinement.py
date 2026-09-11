#!/usr/bin/env python3
"""Reproducible BKT particle/grid/height experiments and display-bandwidth QA."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
import pandas as pd
import xarray as xr

import a37_bkt_footprint as model
import a38_bkt_footprint_report as report
from bkt_footprint_spatial import (basemap, boundary_lines, cell_area_km2,
                                   display_surface, indonesia_boundaries,
                                   smooth_coefficients, regrid_coefficients)
from plot_bkt_footprint import map_field, render
from validate_bkt_footprint import validate

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "outputs/hysplit/refinement"
OUT = RUNS / "analysis"
STAMP = "bkt_20190926T0100Z"
SPECS = {
    "n2000_s0": (2000, 0.1, 0, 30),
    "n10000_s0": (10000, 0.1, 0, 30),
    "n10000_sm10": (10000, 0.1, -10, 30),
    "n10000_sm20": (10000, 0.1, -20, 30),
    "n10000_coarse": (10000, 0.25, 0, 30),
    "n10000_height60": (10000, 0.1, 0, 60),
}
MEMBERS = ("n10000_s0", "n10000_sm10", "n10000_sm20")


def actual_particles(message: str) -> int:
    matches = re.findall(r"NOTICE\s+main:\s+\d+\s+\d+\s+(\d+)\s+", message)
    if not matches:
        raise ValueError("No particle counts found in model log")
    return max(map(int, matches))


def run_experiments(home: Path, jobs: int) -> None:
    def run(item):
        name, (count, step, seed, height) = item
        directory = RUNS / name / STAMP
        if (directory / "run_metadata.json").exists():
            return
        cfg = model.FootprintConfig(particles=count, grid_spacing_deg=step,
                                     seed=seed, receptor_height_m_agl=height,
                                     hours_back=6 if name.startswith(("normalization_","diagnostic_")) else 72,
                                     particle_diagnostic_variables=0 if name in ("n10000_height60","diagnostic_probe") else 20)
        model.run_footprint(pd.Timestamp("2019-09-26T01:00"), model.DEFAULT_MET_DIR,
                            RUNS / name, home, cfg, False)
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        all_specs={**SPECS,"normalization_n500":(500,.25,0,30),
                   "normalization_n540":(540,.25,0,30),"diagnostic_probe":(500,.25,0,30)}
        list(pool.map(run, all_specs.items()))


def read_run(directory: Path) -> tuple:
    meta = json.loads((directory / "run_metadata.json").read_text())
    with xr.open_dataset(directory / "footprint.nc", engine="h5netcdf") as ds:
        field = ds.footprint_sensitivity.astype("float64").load()
    message = (directory / "MESSAGE").read_text()
    cfg = meta["configuration"]
    if "FATAL" in message.upper() or not re.search(r"CMASS\s*=\s*1", message):
        raise ValueError(f"Invalid STILT run settings: {directory}")
    if int(field.sizes["time"]) != 72 or np.any(field.values < 0) or not np.isfinite(field).all():
        raise ValueError(f"Invalid numerical footprint: {directory}")
    meta["actual_particles"] = actual_particles(message)
    if meta["actual_particles"] < cfg["particles"]:
        raise ValueError("Model did not emit the requested particle ensemble")
    factor=cfg["particles"]/meta["actual_particles"]
    meta["particle_normalization_factor"]=factor
    field=field*factor
    field.attrs.update({"units":"ppm / (umol m-2 s-1)",
                       "particle_normalization_factor":factor,
                       "normalization":"Native HYSPLIT coefficient times requested/actual emitted particle count"})
    return field, meta


def diagnostics(field: xr.DataArray, meta: dict) -> dict:
    cfg = meta["configuration"]
    aggregate = field.sum("time").values
    lat, lon = np.meshgrid(field.lat.values, field.lon.values, indexing="ij")
    distance, bearing = report.haversine_and_bearing(lat, lon, cfg["receptor_lat"], cfg["receptor_lon"])
    weights = aggregate.ravel()
    total = float(weights.sum())
    lag_weights = field.sum(("lat", "lon")).values[::-1]
    ages = np.arange(1, 73)
    far = distance >= 25
    se = far & (bearing >= 112.5) & (bearing < 157.5)
    return {
        "sensitivity_sum": total,
        "se_beyond25_share_percent": float(100*aggregate[se].sum()/total),
        "within25_share_percent": float(100*aggregate[~far].sum()/total),
        "within100_share_percent": float(100*aggregate[distance < 100].sum()/total),
        "within250_share_percent": float(100*aggregate[distance < 250].sum()/total),
        "median_distance_km": report.weighted_quantile(distance.ravel(), weights, .5),
        "p90_distance_km": report.weighted_quantile(distance.ravel(), weights, .9),
        "median_lag_hours": report.weighted_quantile(ages, lag_weights, .5),
        "p90_lag_hours": report.weighted_quantile(ages, lag_weights, .9),
        "share_1_24h_percent": float(100*lag_weights[:24].sum()/total),
        "share_25_48h_percent": float(100*lag_weights[24:48].sum()/total),
        "share_49_72h_percent": float(100*lag_weights[48:].sum()/total),
    }


def select_bandwidth(fields: list[np.ndarray], area: np.ndarray) -> tuple:
    """Leave-one-seed-out integrated quadratic risk, up to constant target norm.

    Held-out raw estimates, not smoothed targets, avoid rewarding blur on both
    sides. Density squared integrated over area = coefficient squared / area.
    Three folds estimate numerical reproducibility, not transport accuracy.
    """
    candidates = [0, .35, .5, .75, 1, 1.5, 2, 3]
    rows = []
    for sigma in candidates:
        scores = []
        for held in range(len(fields)):
            training = np.mean([f for i, f in enumerate(fields) if i != held], axis=0)
            smoothed = smooth_coefficients(training, sigma)
            scores.append(float(((smoothed**2-2*smoothed*fields[held])/area).sum()))
        rows.append({"sigma_cells": sigma, "sigma_degrees": .1*sigma,
                     "fold0_risk": scores[0], "fold1_risk": scores[1], "fold2_risk": scores[2],
                     "mean_risk": float(np.mean(scores))})
    table = pd.DataFrame(rows)
    selected = float(table.loc[table.mean_risk.idxmin(), "sigma_cells"])
    table["selected"] = table.sigma_cells.eq(selected)
    return selected, table


def comparison_map(old: xr.DataArray, mean: xr.DataArray,
                   sigma: float, fig_dir: Path) -> None:
    import cartopy.crs as ccrs
    provinces, _ = indonesia_boundaries()
    fig = plt.figure(figsize=(7.2, 8.2))
    for i, (field, title, smooth) in enumerate([
        (old.sum("time"), "(a) Original: 540 actual particles · 0.25° cells", False),
        (mean.sum("time"), "(b) Revised: three runs · 10,020 particles each · 0.1°", True),
    ]):
        ax = fig.add_axes([.12, .53-i*.39, .77, .32], projection=ccrs.PlateCarree())
        ax.set_extent([98.5,112,-8,2])
        basemap(ax, provinces)
        if smooth:
            lat, lon, density = display_surface(field.values, field.lat.values, field.lon.values, sigma)
            m = ax.contourf(lon,lat,np.ma.masked_less_equal(density,0),levels=np.geomspace(1e-7,3e-2,100),
                            norm=LogNorm(1e-7,3e-2),cmap="YlOrRd",extend="max",
                            transform=ccrs.PlateCarree(), zorder=2)
        else:
            density=field.values/cell_area_km2(field.lat.values,field.lon.values)
            ax.pcolormesh(field.lon,field.lat,np.ma.masked_less(density,1e-7),
                           norm=LogNorm(1e-7,3e-2),cmap="YlOrRd",shading="nearest",zorder=2)
        boundary_lines(ax, provinces)
        ax.plot(100.318,-.202,"*",color="#007A9D",ms=9,zorder=6)
        ax.set_title(title, fontsize=9, loc="left", pad=7)
        gl=ax.gridlines(draw_labels=True,linewidth=.3,alpha=.3)
        gl.top_labels=gl.right_labels=False
        gl.xlabel_style=gl.ylabel_style={"size":8}
    cax=fig.add_axes([.2,.065,.6,.016])
    cb=fig.colorbar(m,cax=cax,orientation="horizontal",ticks=[1e-7,1e-5,1e-3,1e-2])
    cb.set_label("Sensitivity density [ppm / (µmol m⁻² s⁻¹) / km²]",fontsize=8)
    fig.text(.12,.96,"Larger particle ensembles support a smoother footprint map",fontsize=11.5,weight="bold")
    fig.text(.12,.91,"Identical domain, boundary asset, variable and color limits in both panels.\n"
             "GDAS1 meteorology is unchanged; smooth contours do not establish finer transport accuracy.",fontsize=8.5,color=report.MUTED)
    report.save_figure(fig,fig_dir/"figure_06_before_after")


def robustness_plot(table: pd.DataFrame, bandwidth: pd.DataFrame, fig_dir: Path) -> None:
    fig,axes=plt.subplots(2,1,figsize=(7.2,6.0))
    fig.subplots_adjust(left=.13,right=.97,top=.80,bottom=.10,hspace=.55)
    selected=table.loc[list(SPECS)]
    labels=["2k","10k A","10k B","10k C","10k coarse","10k 60 m"]
    axes[0].plot(labels,selected.se_beyond25_share_percent,"o",color=report.BLUE)
    axes[0].set_ylabel("SE sensitivity beyond 25 km\n(% of domain total)")
    axes[0].grid(axis="y",alpha=.25)
    base=bandwidth.loc[bandwidth.sigma_cells.eq(0),"mean_risk"].iloc[0]
    axes[1].plot(bandwidth.sigma_degrees,bandwidth.mean_risk-base,"o-",color=report.ORANGE)
    best=bandwidth[bandwidth.selected].iloc[0]
    axes[1].axvline(best.sigma_degrees,color=report.MUTED,ls="--",lw=.8)
    axes[1].axhline(0,color=report.MUTED,lw=.7)
    axes[1].set(xlabel="Gaussian display bandwidth σ (degrees)",
                ylabel="Cross-seed quadratic risk\n(relative to no kernel)")
    axes[1].ticklabel_format(axis="y",style="sci",scilimits=(0,0))
    for ax in axes: ax.spines[["top","right"]].set_visible(False)
    fig.text(.13,.95,"Numerical sensitivity and display bandwidth are evaluated separately",fontsize=11,weight="bold")
    fig.text(.13,.89,"A–C differ in random seed; coarse and 60 m runs change one setting each.\n"
             "Lower cross-seed risk favors reproducible display structure; it does not validate meteorology.",fontsize=8.5,color=report.MUTED)
    report.save_figure(fig,fig_dir/"figure_07_robustness")


def analyze() -> None:
    figures,tables=OUT/"figures",OUT/"tables"
    figures.mkdir(parents=True,exist_ok=True)
    tables.mkdir(parents=True,exist_ok=True)
    probes=[]
    probe_fields={}
    for name in ("normalization_n500","normalization_n540","diagnostic_probe"):
        directory=RUNS/name/STAMP
        with xr.open_dataset(directory/"footprint.nc",engine="h5netcdf") as ds:
            probe_fields[name]=ds.footprint_sensitivity.values.astype(float)
        metadata=json.loads((directory/"run_metadata.json").read_text())
        count=actual_particles((directory/"MESSAGE").read_text())
        requested=metadata["configuration"]["particles"]
        raw_total=float(probe_fields[name].sum())
        probes.append({"run":name,"requested_particles":requested,"actual_particles":count,
                       "native_total":raw_total,"corrected_total":raw_total*requested/count,
                       "runtime_seconds":metadata["model_runtime_seconds"]})
    probe_table=pd.DataFrame(probes).set_index("run")
    native_ratio=float(probe_table.loc["normalization_n500","native_total"]/
                        probe_table.loc["normalization_n540","native_total"])
    n500=probe_fields["normalization_n500"]*500/540
    n540=probe_fields["normalization_n540"]
    correction_error=float(np.abs(n500-n540).sum()/n540.sum())
    identical_diagnostic=bool(np.array_equal(probe_fields["normalization_n500"],
                                            probe_fields["diagnostic_probe"]))
    if abs(native_ratio-1.08)>.001 or correction_error>.001 or not identical_diagnostic:
        raise ValueError("Controlled normalization/diagnostic-output test failed")
    probe_table.to_csv(tables/"controlled_probes.csv")
    fields,metas={},{}
    for name in SPECS:
        directory=RUNS/name/STAMP
        fields[name],metas[name]=read_run(directory)
        existing=json.loads((directory/"map_metadata.json").read_text()) if (directory/"map_metadata.json").exists() else {}
        if "particle_normalization_factor" not in existing: render(directory)
        validate(directory)
    old,old_meta=read_run(ROOT/"outputs/hysplit"/STAMP)
    mean=xr.concat([fields[k] for k in MEMBERS],dim="member").mean("member")
    mean.attrs.update(fields[MEMBERS[0]].attrs)
    mean.attrs["comment"]="Arithmetic mean of three seeded 10020-particle runs; unsmoothed analysis field"
    mean.attrs["normalization"]="Each native member corrected by requested/actual emitted count before averaging"
    dataset=mean.to_dataset(name="footprint_sensitivity")
    dataset.attrs.update({"Conventions":"CF-1.8","crs":"EPSG:4326",
                         "receptor_time_utc":"2019-09-26T01:00:00Z",
                         "ensemble_members":json.dumps(list(MEMBERS)),
                         "interpretation":"Conditional transport sensitivity, no flux attribution"})
    dataset.to_netcdf(OUT/"ensemble_mean.nc",engine="h5netcdf",encoding={
        "footprint_sensitivity":{"zlib":True,"complevel":4,"dtype":"float64"}})
    hourly=mean.to_dataframe(name="footprint_sensitivity").reset_index()
    hourly=hourly[hourly.footprint_sensitivity>0].rename(columns={"lat":"LAT","lon":"LON","time":"time_utc"})
    hourly["lag_hours"]=(pd.Timestamp("2019-09-26T01:00")-hourly.time_utc).dt.total_seconds()/3600
    hourly.to_csv(OUT/"ensemble_hourly.csv.gz",index=False)
    aggregate=hourly.groupby(["LAT","LON"],as_index=False).footprint_sensitivity.sum().rename(
        columns={"footprint_sensitivity":"sensitivity_sum"})
    aggregate.to_csv(OUT/"ensemble_aggregate.csv",index=False)
    if not np.isclose(hourly.footprint_sensitivity.sum(),float(mean.sum()),rtol=1e-12):
        raise ValueError("Ensemble CSV/NetCDF reconciliation failed")

    rows=[]
    for name,field,meta in [("original",old,old_meta)]+[(k,fields[k],metas[k]) for k in SPECS]:
        cfg=meta["configuration"]
        rows.append(dict(run=name,actual_particles=meta["actual_particles"],
                         requested_particles=cfg["particles"],seed=cfg.get("seed",0),
                         normalization_factor=meta["particle_normalization_factor"],
                         grid_spacing_deg=cfg["grid_spacing_deg"],height_m_agl=cfg["receptor_height_m_agl"],
                         runtime_seconds=meta.get("model_runtime_seconds",np.nan),**diagnostics(field,meta)))
    central=diagnostics(mean,metas[MEMBERS[0]])
    rows.append(dict(run="ensemble_mean",actual_particles=sum(metas[k]["actual_particles"] for k in MEMBERS),
                     requested_particles=30000,grid_spacing_deg=.1,height_m_agl=30,**central))
    summary=pd.DataFrame(rows).set_index("run")
    common_lat=model.grid_coordinates(-.202,20,1.)
    common_lon=model.grid_coordinates(100.318,30,1.)
    common={}
    for name,field in {"original":old,**fields,"ensemble_mean":mean}.items():
        array=field.sum("time").values
        mapped=regrid_coefficients(array,field.lat.values,field.lon.values,common_lat,common_lon)
        if not np.isclose(mapped.sum(),array.sum(),rtol=1e-10):
            raise ValueError("Common-grid conservative rebinning lost sensitivity")
        common[name]=mapped/mapped.sum()
    for name in common:
        summary.loc[name,"shape_tv_1deg_percent_vs_seed0"]=float(
            50*np.abs(common[name]-common["n10000_s0"]).sum())
        summary.loc[name,"total_change_percent_vs_seed0"]=float(
            100*(summary.loc[name,"sensitivity_sum"]/summary.loc["n10000_s0","sensitivity_sum"]-1))
    summary.to_csv(tables/"experiment_summary.csv")
    seeds=summary.loc[list(MEMBERS)]
    spread=pd.DataFrame({"mean":seeds[list(central)].mean(),"minimum":seeds[list(central)].min(),
                         "maximum":seeds[list(central)].max(),"sample_sd":seeds[list(central)].std()})
    spread.to_csv(tables/"seed_spread.csv",index_label="metric")
    fine_aggregate=[fields[k].sum("time").values for k in MEMBERS]
    area=cell_area_km2(mean.lat.values,mean.lon.values)
    sigma,bandwidth=select_bandwidth(fine_aggregate,area)
    bandwidth.to_csv(tables/"bandwidth_cross_validation.csv",index=False)
    if np.array_equal(fine_aggregate[0],fine_aggregate[1]):
        raise ValueError("Seed perturbation did not alter the model output")
    smoothing=[]
    raw=mean.sum("time").values
    for value in bandwidth.sigma_cells:
        sm=smooth_coefficients(raw,value)
        mock=mean.copy(data=np.repeat((sm/72)[None,:,:],72,axis=0))
        item=diagnostics(mock,metas[MEMBERS[0]])
        smoothing.append({"sigma_cells":value,"sum_relative_error":float(sm.sum()/raw.sum()-1),
                          "l1_redistribution_percent":float(50*np.abs(sm-raw).sum()/raw.sum()),
                          **{k:item[k] for k in ("within25_share_percent","within100_share_percent",
                                               "within250_share_percent","se_beyond25_share_percent")}})
    pd.DataFrame(smoothing).to_csv(tables/"smoothing_sensitivity.csv",index=False)

    report.apply_chart_style()
    report.figure_workflow(figures,"3 × 10,020 particles")
    _,observations=report.observation_context(metas[MEMBERS[0]],tables,figures)
    _,lag=report.lag_diagnostics(hourly,tables,figures,ensemble=True)
    _,spatial=report.spatial_diagnostics(aggregate,metas[MEMBERS[0]],tables,figures)
    map_meta=map_field(raw,mean.lat.values,mean.lon.values,metas[MEMBERS[0]],
                       figures/"figure_03_spatial_footprint.png",sigma,
                       "Mean of 3 seeded runs · 10,020 actual particles per run")
    (OUT/"map_metadata.json").write_text(json.dumps(map_meta,indent=2)+"\n")
    dlat,dlon,density=display_surface(raw,mean.lat.values,mean.lon.values,sigma)
    display=xr.Dataset({"display_sensitivity_density":(("lat","lon"),density)},
                         coords={"lat":dlat,"lon":dlon},attrs={
                             "purpose":"DISPLAY ONLY: use ensemble_mean.nc for analysis and convolution",
                             "gaussian_sigma_cells":sigma,"crs":"EPSG:4326"})
    display.display_sensitivity_density.attrs["units"]="ppm / (umol m-2 s-1) / km2"
    display.lat.attrs.update({"standard_name":"latitude","units":"degrees_north"})
    display.lon.attrs.update({"standard_name":"longitude","units":"degrees_east"})
    display.to_netcdf(OUT/"display_surface.nc",engine="h5netcdf",encoding={
        "display_sensitivity_density":{"zlib":True,"complevel":4}})
    comparison_map(old,mean,sigma,figures)
    robustness_plot(summary,bandwidth,figures)
    metrics={"central":central,"lag":lag,"spatial":spatial,"sigma_cells":sigma,
             "observations":observations.to_dict("records"),"map":map_meta,
             "actual_particles_per_member":[metas[k]["actual_particles"] for k in MEMBERS],
             "met_provenance":json.loads((ROOT/"data/hysplit/provenance/gdas1.sep19.w4.json").read_text()),
             "ensemble_members":list(MEMBERS),"status":"numerical_checks_passed"}
    metrics["controlled_probes"]={"native_ratio_500_over_540":native_ratio,
                                 "corrected_l1_relative_error":correction_error,
                                 "diagnostic_disabled_bitwise_identical":identical_diagnostic}
    (OUT/"metrics.json").write_text(json.dumps(metrics,indent=2)+"\n")
    print(summary.to_string())
    print(f"Selected Gaussian sigma: {sigma} cells ({sigma*.1:g} degrees)")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage",choices=["model","analyze"])
    parser.add_argument("--hysplit-home",type=Path)
    parser.add_argument("--jobs",type=int,default=3)
    args=parser.parse_args()
    if args.stage=="model":
        if not 1<=args.jobs<=6: parser.error("jobs must be between 1 and 6")
        run_experiments(model.resolve_hysplit_home(args.hysplit_home),args.jobs)
    else: analyze()
