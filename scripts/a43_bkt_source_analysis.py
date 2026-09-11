#!/usr/bin/env python3
"""GFS/GDAS transport comparison and conservative, prior-flux convolution."""
from __future__ import annotations
import argparse
import json
import re
import subprocess
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
from shapely import box

import a37_bkt_footprint as model
import a38_bkt_footprint_report as context
from a39_bkt_refinement import read_run, diagnostics, MEMBERS, STAMP, select_bandwidth
from bkt_footprint_spatial import cell_area_km2, regrid_coefficients, indonesia_boundaries

ROOT = model.ROOT
OUT = ROOT / "outputs/hysplit/gfs/analysis"
TABLES = OUT / "tables"
MW = {"CO2": 44.0095, "CH4": 16.0425, "CO": 28.0101}  # g mol-1


def save_nc(data: xr.Dataset, path: Path) -> None:
    data.attrs.update(Conventions="CF-1.8", crs="EPSG:4326")
    for axis, name, unit in (("lat", "latitude", "degrees_north"), ("lon", "longitude", "degrees_east")):
        if axis in data.coords: data[axis].attrs.update(standard_name=name, units=unit)
    data.to_netcdf(path, engine="h5netcdf", encoding={
        k: {"zlib": True, "complevel": 4} for k in data.data_vars})


def transport() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    (OUT / "figures").mkdir(exist_ok=True)
    results, fields, metas = [], {}, {}
    for driver, base in (("GFS", "gfs"), ("GDAS", "refinement")):
        for member in (*MEMBERS, "n10000_height60"):
            field, meta = read_run(ROOT / "outputs/hysplit" / base / member / STAMP)
            key = f"{driver}_{member}"
            fields[key], metas[key] = field, meta
            results.append(dict(run=key, driver=driver, member=member,
                actual_particles=meta["actual_particles"], height_m=meta["configuration"]["receptor_height_m_agl"],
                **diagnostics(field, meta)))
        mean = xr.concat([fields[f"{driver}_{m}"] for m in MEMBERS], dim="member").mean("member")
        mean.attrs.update(units="ppm / (umol m-2 s-1)",
                          normalization="Mean over emitted particles; arithmetic mean of three seeds",
                          cell_interpretation="Discrete source-cell and source-hour integrated coefficient")
        fields[driver] = mean
        results.append(dict(run=driver, driver=driver, member="ensemble", height_m=30,
                            **diagnostics(mean, metas[f"{driver}_{MEMBERS[0]}"])))
        save_nc(mean.to_dataset(name="footprint_sensitivity"), OUT / f"{driver}_ensemble.nc")
    table = pd.DataFrame(results)
    table.to_csv(TABLES / "transport_summary.csv", index=False)
    edge_rows=[]
    for key, f in fields.items():
        edge = np.zeros(f.shape[1:], dtype=bool)
        edge[[0,-1],:] = True; edge[:,[0,-1]] = True
        edge_rows.append(dict(run=key,edge_share_percent=100*float(f.sum("time").values[edge].sum())/float(f.sum()),
                              interpretation="Regional-domain diagnostic, not a bound on omitted external influence"))
    pd.DataFrame(edge_rows).to_csv(TABLES/"output_domain_edge.csv",index=False)
    coarse_lat = model.grid_coordinates(-.202, 20, 1)
    coarse_lon = model.grid_coordinates(100.318, 30, 1)
    maps = {}
    for key in ("GFS", "GDAS"):
        f = fields[key]
        v = regrid_coefficients(f.sum("time").values, f.lat.values, f.lon.values, coarse_lat, coarse_lon)
        if not np.isclose(v.sum(), float(f.sum()), rtol=1e-10): raise ValueError("Lost remapped sensitivity")
        maps[key] = v/v.sum()
    sigma, bandwidth = select_bandwidth([fields[f"GFS_{m}"].sum("time").values for m in MEMBERS],
                                        cell_area_km2(fields["GFS"].lat.values, fields["GFS"].lon.values))
    bandwidth.to_csv(TABLES / "bandwidth_selection.csv", index=False)
    comparison = dict(shape_tv_1deg_percent=50*np.abs(maps["GFS"]-maps["GDAS"]).sum(),
                      total_change_percent=100*(float(fields["GFS"].sum()/fields["GDAS"].sum())-1),
                      gaussian_sigma_cells=sigma)
    pd.DataFrame([comparison]).to_csv(TABLES / "driver_comparison.csv", index=False)
    temporal = []
    for key in ("GFS", "GDAS"):
        f = fields[key]
        for t, w in zip(f.time.values, f.sum(("lat", "lon")).values):
            temporal.append(dict(driver=key, source_time_utc=pd.Timestamp(t),
                                 lag_hours=(pd.Timestamp("2019-09-26T01:00")-pd.Timestamp(t)).total_seconds()/3600,
                                 sensitivity=w, share_percent=100*w/float(f.sum())))
    pd.DataFrame(temporal).to_csv(TABLES / "lag_by_driver.csv", index=False)
    context.observation_context(metas[f"GFS_{MEMBERS[0]}"], TABLES, OUT / "figures")
    (OUT / "transport_metadata.json").write_text(json.dumps(comparison, indent=2)+"\n")
    print(table.to_string(index=False), flush=True)


def meteorology(home: Path) -> None:
    """Independent native-grid profiles; PBLH is context, not KMIXD=3 model depth."""
    from a41_bkt_gfs import met_paths
    TABLES.mkdir(parents=True,exist_ok=True)
    work=OUT/"meteorological_profiles"
    rows=[]
    for driver,paths in (("GFS",met_paths()),("GDAS",[ROOT/"data/hysplit/met/gdas1.sep19.w4"])):
        for path in paths:
            folder=work/driver/path.name
            folder.mkdir(parents=True,exist_ok=True)
            result=subprocess.run([str(home/"exec/profile"),f"-d{path.parent}/",f"-f{path.name}",
                                   "-y-0.202","-x100.318","-o0","-t3","-n168","-e1","-p1"],
                                   cwd=folder,capture_output=True,text=True,check=True)
            (folder/"extraction.log").write_text(result.stdout+result.stderr)
            text=(folder/"profile_1.txt").read_text()
            for block in text.split("Profile Time:")[1:]:
                lines=block.splitlines()
                vals=list(map(int,lines[0].split()))
                stamp=pd.Timestamp(year=2000+vals[0],month=vals[1],day=vals[2],hour=vals[3],minute=vals[4])
                if not pd.Timestamp("2019-09-23")<=stamp<=pd.Timestamp("2019-09-26T03:00"):continue
                p=next(i for i,line in enumerate(lines) if "2D Fields" in line)
                keys=lines[p+1].split()
                # The legacy Fortran text record may contain padding bytes after its declared fields.
                numbers=list(map(float,lines[p+3].split()[:len(keys)+1]))[1:]
                if len(keys)!=len(numbers):raise ValueError("Native surface-profile schema mismatch")
                values=dict(zip(keys,numbers))
                rows.append(dict(driver=driver,time_utc=stamp,**{k:values.get(k,np.nan) for k in ("PBLH","U10M","V10M","T02M","SHTF","SHGT")}))
    frame=pd.DataFrame(rows).drop_duplicates(["driver","time_utc"]).sort_values(["driver","time_utc"])
    frame.to_csv(TABLES/"meteorological_context.csv",index=False)
    frame.groupby("driver")[["PBLH","SHGT","U10M","V10M"]].agg(["min","median","max"]).to_csv(TABLES/"meteorological_summary.csv")


def matching_flux(flux: np.ndarray, lat: np.ndarray, lon: np.ndarray,
                  target_lat: np.ndarray, target_lon: np.ndarray) -> np.ndarray:
    """Area-average a piecewise-constant flux onto receptor footprint cells."""
    if not np.isfinite(flux).all() or np.any(flux < 0):
        raise ValueError("Inventory contains missing, nonfinite or negative emission flux")
    for coordinates in (lat,lon,target_lat,target_lon):
        spacing=np.diff(coordinates)
        if len(spacing)==0 or not np.isfinite(coordinates).all() or (spacing<=0).any() or not np.allclose(spacing,spacing[0]):
            raise ValueError("Conservative flux remapping requires regular increasing coordinates")
    for source_axis, target_axis in ((lat,target_lat),(lon,target_lon)):
        source_half=(source_axis[1]-source_axis[0])/2
        target_half=(target_axis[1]-target_axis[0])/2
        if (target_axis[0]-target_half < source_axis[0]-source_half-1e-9 or
                target_axis[-1]+target_half > source_axis[-1]+source_half+1e-9):
            raise ValueError("Inventory coverage does not contain the complete target grid")
    return regrid_coefficients(flux*cell_area_km2(lat, lon), lat, lon, target_lat, target_lon)/cell_area_km2(target_lat,target_lon)


def edgar_fluxes(target_lat, target_lon):
    paths = sorted((ROOT / "data/bkt_sources/edgar_v8").glob("*_2019.nc"))
    if len(paths) != 16: raise ValueError(f"Incomplete EDGAR acquisition: {len(paths)} of 16 sectors")
    quality = []
    for path in paths:
        gas = path.stem.split("_")[0]
        sector = "_".join(path.stem.split("_")[1:-1])
        with xr.open_dataset(path) as ds:
            if ds.fluxes.attrs["units"] != "kg m-2 s-1" or ds.fluxes.attrs["substance"] != gas:
                raise ValueError("EDGAR units/species mismatch")
            sub = ds.fluxes.sel(time="2019-09-15", lat=slice(-11,11), lon=slice(84,117)).load()
            flux = sub.values.astype(float)*1e9/MW[gas]
            quality.append(dict(dataset="EDGAR v8.0", gas=gas, sector=sector,
                                source_period="September 2019 monthly mean", input_unit="kg m-2 s-1",
                                lat_count=sub.sizes["lat"], lon_count=sub.sizes["lon"],
                                missing_cells=int((~np.isfinite(flux)).sum()), negative_cells=int((flux<0).sum()),
                                minimum_umol_m2_s=float(flux.min()), maximum_umol_m2_s=float(flux.max())))
            yield gas, sector, matching_flux(flux, sub.lat.values, sub.lon.values, target_lat, target_lon), quality[-1]


def prepare_inventory():
    """Validate all source inputs independently of the transport execution."""
    TABLES.mkdir(parents=True,exist_ok=True)
    lat=model.grid_coordinates(-.202,20,.1)
    lon=model.grid_coordinates(100.318,30,.1)
    names,fluxes,rows=[],[],[]
    for gas,sector,flux,quality in edgar_fluxes(lat,lon):
        names.append(f"{gas}_{sector}");fluxes.append(flux);rows.append(quality)
    ds=xr.Dataset({"surface_flux":(("source","lat","lon"),np.asarray(fluxes))},
                  coords={"source":names,"lat":lat,"lon":lon})
    ds.surface_flux.attrs["units"]="umol m-2 s-1"
    ds.attrs["source_period"]="September 2019 mean; surface-release-equivalent inventory input"
    save_nc(ds,OUT/"matched_EDGAR_inputs.nc")
    pd.DataFrame(rows).to_csv(TABLES/"source_quality.csv",index=False)
    print(pd.DataFrame(rows).to_string(index=False),flush=True)


def sources() -> None:
    with xr.open_dataset(OUT / "GFS_ensemble.nc") as ds:
        mean = ds.footprint_sensitivity.load()
    lat, lon = mean.lat.values, mean.lon.values
    fields = {}
    for driver, base in (("GFS", "gfs"), ("GDAS", "refinement")):
        for member in (*MEMBERS, "n10000_height60"):
            fields[f"{driver}_{member}"], _ = read_run(ROOT / "outputs/hysplit" / base / member / STAMP)
    rows, quality, flux_arrays, keys = [], [], [], []
    maps, lag_rows = {}, []
    for gas, sector, flux, qa in edgar_fluxes(lat, lon):
        key = f"{gas}_{sector}"
        keys.append(key); flux_arrays.append(flux); quality.append(qa)
        factor = 1 if gas == "CO2" else 1000
        for run, field in fields.items():
            value = float((field.values*flux[None,:,:]).sum())*factor
            rows.append(dict(run=run, gas=gas, sector=sector, family="EDGAR", enhancement=value,
                             unit="ppm" if gas=="CO2" else "ppb"))
        maps[key] = mean.sum("time").values*flux*factor
        for t, value in zip(mean.time.values, (mean.values*flux[None,:,:]).sum(axis=(1,2))*factor):
            lag_rows.append(dict(gas=gas, source=sector, source_time_utc=pd.Timestamp(t), enhancement=value))
    flux_ds = xr.Dataset({"surface_flux":(("source","lat","lon"),np.asarray(flux_arrays)),
                          "enhancement":(("source","lat","lon"),np.asarray([maps[k]/(1 if k.startswith("CO2_") else 1000) for k in keys]))},
                         coords={"source":keys,"lat":lat,"lon":lon})
    flux_ds.surface_flux.attrs["units"] = "umol m-2 s-1"
    flux_ds.enhancement.attrs.update(units="1e-6",long_name="Mole-fraction enhancement in ppm for every gas",
                                     presentation="CH4 is multiplied by 1000 for ppb in tables and figures")
    save_nc(flux_ds, OUT / "EDGAR_convolution.nc")
    pd.DataFrame(rows).to_csv(TABLES / "source_contributions.csv", index=False)
    pd.DataFrame(quality).to_csv(TABLES / "source_quality.csv", index=False)
    pd.DataFrame(lag_rows).to_csv(TABLES / "source_lags.csv", index=False)
    worked=[]
    for gas in ("CO2","CH4"):
        names=[s for s in keys if s.startswith(gas+"_")]
        name=max(names,key=lambda s:maps[s].max())
        iy,ix=np.unravel_index(np.argmax(maps[name]),maps[name].shape)
        f=float(mean.sum("time").values[iy,ix]);e=float(flux_arrays[keys.index(name)][iy,ix])
        worked.append(dict(gas=gas,source=name,lat=float(lat[iy]),lon=float(lon[ix]),
                           sensitivity=f,flux_umol_m2_s=e,ppm=f*e,
                           reported_contribution=float(maps[name][iy,ix]),conversion_to_report_unit=1 if gas=="CO2" else 1000))
    pd.DataFrame(worked).to_csv(TABLES/"worked_convolution.csv",index=False)
    province_attribution(flux_ds, mean)
    fire_sources(mean, fields)
    print(pd.DataFrame(rows).groupby(["gas","sector"]).enhancement.mean().to_string(), flush=True)


def fire_sources(mean, fields):
    path=ROOT/"data/bkt_sources/gfed51/GFED51_20190923_26_region.npz"
    meta=json.loads(path.with_suffix(".npz.json").read_text())
    with np.load(path) as source:
        lat,lon=source["lat"],source["lon"]
        y,x=np.argsort(lat),np.argsort(lon)
        lat,lon=lat[y],lon[x]
        dates=pd.Timestamp("1800-01-01")+pd.to_timedelta(source["time"],unit="h")
        days=dates.normalize()
        if list(days)!=list(pd.date_range("2019-09-23","2019-09-26")):
            raise ValueError(f"Unexpected GFED dates: {dates}")
        arrays={gas:source[gas][:,y,:][:,:,x] for gas in ("CO2","CH4","CO")}
    native_area=cell_area_km2(lat,lon)*1e6
    rows,maps,fluxes,temporal,checks=[],[],[],[],[]
    for gas,mass in arrays.items():
        if meta["units"][gas] != f"g {gas} per day": raise ValueError("Unexpected GFED units")
        daily_flux=mass.astype(float)/native_area[None,:,:]/86400*1e6/MW[gas]
        matched=np.stack([matching_flux(day,lat,lon,mean.lat.values,mean.lon.values) for day in daily_flux])
        hourly=np.stack([matched[days.get_loc(pd.Timestamp(t).normalize())] for t in mean.time.values])
        factor=1 if gas=="CO2" else 1000
        for run,field in fields.items():
            value=float((field.values*hourly).sum())*factor
            flat=float((field.values*hourly.mean(axis=0)[None,:,:]).sum())*factor
            rows.append(dict(run=run,gas=gas,sector="Landscape fire",family="GFED",enhancement=value,
                             window_mean_enhancement=flat,unit="ppm" if gas=="CO2" else "ppb"))
        maps.append((mean.values*hourly).sum(axis=0)*factor)
        fluxes.append(hourly)
        for t,value in zip(mean.time.values,(mean.values*hourly).sum(axis=(1,2))*factor):
            temporal.append(dict(gas=gas,source_time_utc=pd.Timestamp(t),enhancement=value))
        checks.append(dict(dataset="GFED5.1",gas=gas,input_units=meta["units"][gas],
                           missing_cells=int((~np.isfinite(daily_flux)).sum()),negative_cells=int((daily_flux<0).sum()),
                           maximum_umol_m2_s=float(daily_flux.max())))
    pd.DataFrame(rows).to_csv(TABLES/"fire_contributions.csv",index=False)
    obs=pd.read_csv(TABLES/"observation_context_summary.csv").set_index("species")
    observed_co=float(obs.loc["CO","receptor_value"])
    budget=[]
    fire_table=pd.DataFrame(rows)
    for driver in ("GFS","GDAS"):
        subset=fire_table[fire_table.run.str.startswith(driver+"_")&~fire_table.run.str.contains("height")&fire_table.gas.eq("CO")]
        modeled=float(subset.enhancement.mean())
        budget.append(dict(driver=driver,observed_co_ppb=observed_co,modeled_fire_co_ppb=modeled,
                           remaining_co_ppb=observed_co-modeled,
                           fire_to_observed_co_percent=100*modeled/observed_co,
                           interpretation="Necessary passive-CO budget check; remainder is not an independently estimated background"))
    pd.DataFrame(budget).to_csv(TABLES/"partial_CO_budget.csv",index=False)
    pd.DataFrame(temporal).to_csv(TABLES/"fire_lags.csv",index=False)
    pd.DataFrame(checks).to_csv(TABLES/"fire_quality.csv",index=False)
    ds=xr.Dataset({"surface_flux":(("gas","time","lat","lon"),np.asarray(fluxes)),
                   "enhancement":(("gas","lat","lon"),np.asarray([m/(1 if g=="CO2" else 1000) for g,m in zip(arrays,maps)]))},
                  coords={"gas":list(arrays),"time":mean.time.values,"lat":mean.lat.values,"lon":mean.lon.values})
    ds.surface_flux.attrs["units"]="umol m-2 s-1"
    ds.enhancement.attrs.update(units="1e-6",long_name="Mole-fraction enhancement in ppm for every gas",
                                presentation="CH4 and CO are multiplied by 1000 for ppb in tables and figures")
    ds.attrs["interpretation"]="Separate fire scenario; do not sum with EDGAR CH4 without resolving agricultural-burning overlap"
    save_nc(ds,OUT/"GFED_convolution.nc")


def unique_province_fractions(overlay):
    """Exclude multiply claimed polygon areas instead of arbitrarily choosing an owner."""
    from itertools import combinations
    from shapely import union_all
    result=overlay.copy()
    result["fraction"]=result.area/result.cell_area
    ambiguous=[]
    for (iy,ix),group in result.groupby(["iy","ix"]):
        intersections=[a.intersection(b) for a,b in combinations(group.geometry,2)]
        intersections=[g for g in intersections if g.area>0]
        if not intersections:continue
        disputed=union_all(intersections)
        area=float(group.cell_area.iloc[0])
        ambiguous.append(dict(iy=iy,ix=ix,fraction=disputed.area/area))
        for index,row in group.iterrows():
            result.at[index,"fraction"]=row.geometry.difference(disputed).area/area
    return result,pd.DataFrame(ambiguous,columns=["iy","ix","fraction"])


def province_attribution(flux_ds, footprint):
    """Fractional cell/polygon overlap in equal-area CRS; current boundaries are context."""
    import geopandas as gpd
    provinces, metadata = indonesia_boundaries()
    name = next(k for k in ("PROVINSI", "provinsi", "NAME_1", "PROV", "name") if k in provinces)
    lat, lon = footprint.lat.values, footprint.lon.values
    support = footprint.sum("time").values > 0
    iy, ix = np.where(support)
    cells = gpd.GeoDataFrame({"iy":iy,"ix":ix}, geometry=[box(lon[x]-.05,lat[y]-.05,lon[x]+.05,lat[y]+.05) for y,x in zip(iy,ix)], crs="EPSG:4326").to_crs("EPSG:6933")
    cells["cell_area"] = cells.area
    overlay = gpd.overlay(cells, provinces[[name,"geometry"]].to_crs("EPSG:6933"), how="intersection", keep_geom_type=False)
    overlay,ambiguous=unique_province_fractions(overlay)
    fractions=overlay.groupby(["iy","ix"]).fraction.sum()
    if (fractions>1.0001).any():raise ValueError("Provincial polygons materially overlap within a source cell")
    rows = []
    for province, group in overlay.groupby(name):
        y,x,fraction = group.iy.to_numpy(int),group.ix.to_numpy(int),group.fraction.to_numpy()
        sensitivity = float((footprint.sum("time").values[y,x]*fraction).sum())
        for gas in ("CO2", "CH4"):
            total_map = flux_ds.enhancement.sel(source=[s for s in flux_ds.source.values if s.startswith(gas+"_")]).sum("source").values*(1 if gas=="CO2" else 1000)
            rows.append(dict(province=province, gas=gas, enhancement=float((total_map[y,x]*fraction).sum()),
                             unit="ppm" if gas=="CO2" else "ppb", sensitivity=sensitivity))
    frame=pd.DataFrame(rows)
    frame.to_csv(TABLES / "province_contributions.csv", index=False)
    coverage=[]
    for gas in ("CO2","CH4"):
        total_map=flux_ds.enhancement.sel(source=[s for s in flux_ds.source.values if s.startswith(gas+"_")]).sum("source").values*(1 if gas=="CO2" else 1000)
        total=float(total_map.sum())
        assigned=float(frame.loc[frame.gas.eq(gas),"enhancement"].sum())
        disputed=float((total_map[ambiguous.iy.to_numpy(int),ambiguous.ix.to_numpy(int)]*ambiguous.fraction.to_numpy()).sum())
        coverage.append(dict(gas=gas,all_domain_enhancement=total,assigned_indonesia=assigned,
                             ambiguous_boundary_enhancement=disputed,
                             ambiguous_boundary_share_percent=100*disputed/total,
                             outside_or_unassigned=total-assigned,assigned_share_percent=100*assigned/total))
    pd.DataFrame(coverage).to_csv(TABLES/"province_coverage.csv",index=False)
    ambiguous.to_csv(TABLES/"province_ambiguous_cells.csv",index=False)
    metadata["quantitative_overlap_rule"]="Multiply claimed polygon area excluded from all provincial allocations; original map geometry unchanged"
    (OUT / "boundary_metadata.json").write_text(json.dumps(metadata, indent=2)+"\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage", choices=["transport", "sources", "meteorology", "inventory"])
    p.add_argument("--hysplit-home",type=Path)
    a = p.parse_args()
    if a.stage=="inventory":prepare_inventory()
    elif a.stage=="meteorology":meteorology(model.resolve_hysplit_home(a.hysplit_home))
    else:transport() if a.stage=="transport" else sources()
