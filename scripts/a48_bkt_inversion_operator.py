"""Unit-checked methane source responses and endpoint-sampled background."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
from scipy.interpolate import RegularGridInterpolator
from pyproj import Geod
import a37_bkt_footprint as model
from a39_bkt_refinement import actual_particles
from a43_bkt_source_analysis import matching_flux,save_nc,MW
from a46_bkt_inversion_transport import OUT,RECEPTORS
from bkt_footprint_spatial import cell_area_km2
import ghg_common as G
import noaa_flask as NF

ROOT=model.ROOT
DATA=ROOT/"data/bkt_sources"
TABLES=OUT/"tables"
LAT=model.grid_coordinates(-.202,36,.25)
LON=model.grid_coordinates(100.318,48,.25)
MONTHS=pd.to_datetime(["2019-09-01","2019-10-01"])


def remap(value,lat,lon):
    yi=np.argsort(lat);xi=np.argsort(lon)
    return matching_flux(np.asarray(value)[np.ix_(yi,xi)],np.asarray(lat)[yi],np.asarray(lon)[xi],LAT,LON)


def prepare():
    TABLES.mkdir(parents=True,exist_ok=True)
    fields=[];names=[];quality=[]
    inputs=[(p,"fluxes",p.stem.removesuffix("_2019")) for p in sorted((DATA/"edgar_v8").glob("CH4_*_2019.nc"))]
    inputs += [(DATA/"inversion"/folder/name,var,label) for folder,name,var,label in (
        ("wetlands","LPJ_MERRA2_2019_0.5x0.5.nc","emis_ch4","wetlands"),
        ("soil","MeMo_CH4uptake_Climatology.nc","CH4uptake","soil_uptake"),
        ("termites","CAMS-GLOB-TERM_v1.1_methane_2000.nc","CH4","termites"),
        ("geological","Etiope_CH4GeologicalEmis_ScaledToHmiel.1x1.nc","emi_ch4","geological"))]
    if len(inputs)!=12: raise ValueError("Incomplete anthropogenic/natural inventory list")
    for path,var,label in inputs:
        if not path.with_suffix(".nc.json").exists(): raise ValueError(f"Unverified source: {path.name}")
        with xr.open_dataset(path) as ds:
            source=ds[var].sortby("lat").sortby("lon")
            if source.attrs["units"].replace(" ","") not in ("kgm-2s-1","kg/m2/s"):
                raise ValueError("Source must be kg methane per square metre per second")
            monthly=[]
            for month in MONTHS:
                select=source.isel(time=0) if source.sizes["time"]==1 else source.isel(time=month.month-1)
                sub=select.sel(lat=slice(-19,19),lon=slice(75,126)).load()
                values=sub.values.astype(float)
                quality.append(dict(source=label,month=str(month.date()),source_time=str(select.time.values),
                    input_unit=source.attrs["units"],cells=values.size,missing=int((~np.isfinite(values)).sum()),
                    negative=int((values<0).sum()),minimum=float(np.nanmin(values)),maximum=float(np.nanmax(values))))
                monthly.append(remap(values*1e9/MW["CH4"],sub.lat.values,sub.lon.values))
            fields.append(monthly);names.append(label)
    ds=xr.Dataset({"flux":(("source","month","lat","lon"),np.asarray(fields))},
        coords={"source":names,"month":MONTHS,"lat":LAT,"lon":LON})
    ds.flux.attrs.update(units="umol m-2 s-1",comment="Soil uptake is a positive magnitude; subtract in the concentration budget")
    save_nc(ds,OUT/"monthly_prior_fluxes.nc")
    pd.DataFrame(quality).to_csv(TABLES/"inversion_input_quality.csv",index=False)
    print("Monthly flux inputs verified and remapped",flush=True)


def prepare_fire():
    import h5py
    ecosystem=DATA/"gfed51/GFED5.1_ecosystem_2019.nc"
    if not ecosystem.with_suffix(".nc.json").exists(): raise ValueError("Ecosystem file not verified")
    with np.load(DATA/"gfed51/GFED51_201909_10_monthly_inversion.npz") as month:
        lat,lon=month["lat"],month["lon"]
        total_monthly=month["CH4"]
    with h5py.File(ecosystem) as f:
        yi=np.flatnonzero((f["lat"][:]>=-19)&(f["lat"][:]<=19))
        xi=np.flatnonzero((f["lon"][:]>=75)&(f["lon"][:]<=126))
        if not np.array_equal(lat,f["lat"][:][yi]) or not np.array_equal(lon,f["lon"][:][xi]):
            raise ValueError("GFED ecosystem/daily coordinates differ")
        carbon=f["carbon_emissions_partitioning/C_14_Cropland"][8:10,yi[0]:yi[-1]+1,xi[0]:xi[-1]+1]
    # Provider GFED5 factors (paper Table 6 rounded): preserve its exact values.
    # Monthly crop methane is distributed using the cell's all-fire daily profile.
    factors=pd.read_csv(DATA/"gfed51/GFED5_emission_factors.txt",sep=r"\s+",comment="#",header=None,index_col=0)
    ch4ef=float(factors.loc["CH4"].iloc[-1]);cef=float(factors.loc["C"].iloc[-1])
    crop_monthly=carbon*(ch4ef/cef)
    fraction=np.divide(crop_monthly,total_monthly,out=np.zeros_like(crop_monthly),where=total_monthly>0)
    if np.max(fraction)>1.01: raise ValueError("Crop methane exceeds monthly total beyond EF rounding")
    fraction=np.clip(fraction,0,1)
    times=[];allfire=[];crop=[]
    for filename in ("GFED51_20190902_30_inversion.npz","GFED51_20191001_06_inversion.npz"):
        with np.load(DATA/"gfed51"/filename) as data:
            stamps=pd.Timestamp("1800-01-01")+pd.to_timedelta(data["time"],unit="h")
            if not np.array_equal(lat,data["lat"]) or not np.array_equal(lon,data["lon"]): raise ValueError("GFED grid mismatch")
            # Native area formula uses sorted axes; restore source orientation afterward.
            sorted_area=cell_area_km2(np.sort(lat),np.sort(lon))*1e6
            area=sorted_area[np.ix_(np.argsort(np.argsort(lat)),np.argsort(np.argsort(lon)))]
            for t,emission in zip(stamps,data["CH4"]):
                if not np.isfinite(emission).all() or (emission<0).any(): raise ValueError("Invalid daily fire mass")
                flux=emission/area/86400*1e6/MW["CH4"]
                allfire.append(remap(flux,lat,lon))
                crop.append(remap(flux*fraction[t.month-9],lat,lon));times.append(t.normalize())
    ds=xr.Dataset({"all_fire_flux":(("day","lat","lon"),np.asarray(allfire)),
                   "crop_fire_flux":(("day","lat","lon"),np.asarray(crop))},
                  coords={"day":times,"lat":LAT,"lon":LON})
    ds["noncrop_fire_flux"]=ds.all_fire_flux-ds.crop_fire_flux
    for name in ds.data_vars:ds[name].attrs["units"]="umol m-2 s-1"
    ds.attrs["crop_partition_assumption"]=f"Monthly ecosystem crop carbon times {ch4ef}/{cef} g CH4/g C; cell-specific total-fire daily allocation"
    save_nc(ds,OUT/"daily_fire_prior_fluxes.nc")
    pd.DataFrame([dict(agriculture_ch4_g_per_kg_dm=ch4ef,agriculture_carbon_fraction=cef/1000,
        maximum_uncapped_crop_fraction=float(np.max(np.divide(crop_monthly,total_monthly,out=np.zeros_like(crop_monthly),where=total_monthly>0))),
        rounding_clipped_cells=int((crop_monthly>total_monthly).sum()))]).to_csv(TABLES/"fire_overlap_assumptions.csv",index=False)
    print("Daily non-crop methane fire fluxes prepared",flush=True)


def arl_surface(path,variable,hour):
    """S141 difference decoding without interpolation or unit conversion.

    Preserve raw subprecision residuals instead of rounding them to zero.
    Nonphysical negative PBL-height diagnostics are explicitly flagged at QA
    and omitted from height scatterplots, never from concentration inference.
    """
    nx,ny,nrecords=221,161,349;size=nx*ny+50
    with path.open("rb") as f:
        for r in range(1,19):
            f.seek((hour//3*nrecords+r)*size);header=f.read(50).decode()
            if header[14:18]!=variable:continue
            exponent=int(header[18:22]);first=float(header[36:50])
            delta=(np.frombuffer(f.read(nx*ny),dtype=np.uint8).astype(float).reshape(ny,nx)-127)*2.**(exponent-7)
            # Every row starts from the preceding row's first decoded value.
            starts=np.r_[first,first+np.cumsum(delta[:-1,0])]
            result=np.cumsum(delta,axis=1)+starts[:,None]
            return result,float(header[22:36])
    raise ValueError(f"ARL surface variable not found: {variable}")


def active_endpoints(points):
    """PGRD=0 records are inactive placeholders, not geographical endpoints."""
    active=points.loc[points.PGRD.gt(0)].copy()
    if active.empty:raise ValueError("No active particles remain at the backward endpoint")
    if not active.latitude.between(-20,20).all() or not active.longitude.between(75,130).all():
        raise ValueError("Active endpoint lies outside the supplied meteorological domain")
    return active


def boundary_samples(directory,meta,height_shift=0.):
    config=meta["configuration"]
    stamp=pd.Timestamp(meta["observation"]["time_utc"]).tz_localize(None)-pd.Timedelta(hours=config["hours_back"])
    points=pd.read_csv(directory/"PAR_GIS.txt",skipinitialspace=True)
    points.columns=points.columns.str.strip()
    raw=points.time.str.replace(r"\s+","",regex=True)
    parsed=pd.to_datetime(raw,format="%m/%d/%y%H:%M")
    if not parsed.eq(stamp).all():raise ValueError("Endpoint dump time does not match integration endpoint")
    # Equal probability particles, not accumulated FOOT diagnostic mass weights.
    if points.NSORT.duplicated().any():raise ValueError("Duplicate endpoint particles")
    expected=meta.get("actual_particles")
    if expected is not None and len(points)!=expected:
        raise ValueError("Incomplete particle dump: active plus inactive records do not match emitted count")
    points=active_endpoints(points)
    met=ROOT/"data/hysplit/gfs0p25/regional"/f"{stamp:%Y%m%d}_gfs0p25"
    terrain,_=arl_surface(met,"SHGT",stamp.hour)
    ground=RegularGridInterpolator((np.arange(161)*.25-20,np.arange(221)*.25+75),terrain)(points[["latitude","longitude"]].values)
    heights=points.height.to_numpy()+ground+height_shift
    filename=DATA/"inversion/carbontracker"/f"CTCH4_2025.molefrac_glb3x2_{stamp:%Y-%m-%d}.nc"
    if not filename.with_suffix(".nc.json").exists():raise ValueError("Unverified/missing boundary field")
    with xr.open_dataset(filename) as ds:
        if ds.ch4.attrs["units"]!="nanomole mole-1" or ds.gph.attrs["units"]!="meters":raise ValueError("Background units differ")
        sub=ds.sel(time=stamp)
        sampled=sub[["ch4","gph"]].interp(latitude=xr.DataArray(points.latitude.values,dims="particle"),
            longitude=xr.DataArray(points.longitude.values,dims="particle")).load()
    bounds=sampled.gph.transpose("particle","boundary").values
    centers=(bounds[:,:-1]+bounds[:,1:])/2
    values=sampled.ch4.transpose("particle","level").values
    if not np.isfinite(bounds).all() or not np.isfinite(values).all() or (np.diff(bounds,axis=1)<=0).any():raise ValueError("Invalid boundary profiles")
    methane=np.array([np.interp(z,h,c) for z,h,c in zip(heights,centers,values)])
    points["terrain_m_msl"]=ground;points["height_m_msl"]=heights;points["background_ppb"]=methane
    points["below_lowest_midlevel"]=heights<centers[:,0]
    return points


def read_footprint(directory):
    meta=json.loads((directory/"run_metadata.json").read_text())
    with xr.open_dataset(directory/"footprint.nc") as ds:f=ds.footprint_sensitivity.astype(float).load()
    cfg=meta["configuration"]
    n=actual_particles((directory/"MESSAGE").read_text())
    if f.sizes["time"]!=cfg["hours_back"] or not np.isfinite(f).all() or float(f.min())<0:
        raise ValueError("Invalid footprint field")
    stamp=pd.Timestamp(meta["observation"]["time_utc"]).tz_localize(None)
    expected=pd.date_range(stamp-pd.Timedelta(hours=cfg["hours_back"]),stamp-pd.Timedelta(hours=1),freq="h")
    if not np.array_equal(f.time.values,expected.values):raise ValueError("Footprint source-hour chronology differs from receptor/window")
    if not np.allclose(f.lat.values,LAT,rtol=0,atol=1e-9) or not np.allclose(f.lon.values,LON,rtol=0,atol=1e-9):
        raise ValueError("Footprint and flux grids differ")
    meta["actual_particles"]=n
    return f*(cfg["particles"]/n),meta


def observation_quality():
    TABLES.mkdir(parents=True,exist_ok=True)
    d=G.apply_flags(G.load_station("BKT"))
    period=d[d.time_utc.between("2019-09-09","2019-10-06T23:00")]
    selected=pd.read_csv(OUT/"receptor_selection.csv")
    j=NF.match_insitu(d,"ch4").loc["2019-09-09":"2019-10-06"]
    j.to_csv(TABLES/"inversion_flask_pairs.csv",index_label="time_utc")
    year=NF.match_insitu(d,"ch4").loc["2019"]
    year.to_csv(TABLES/"inversion_flask_pairs_2019.csv",index_label="time_utc")
    rows=[dict(scope="study_period",expected_hours=28*24,available_rows=len(period),
        valid_ch4=int(period.ch4.notna().sum()),duplicate_hours=int(period.time_utc.duplicated().sum()),
        suspect_ch4=int(period.suspect_ch4.sum()),scheduled_receptors=len(selected),
        retained_receptors=int(selected.retained.sum()),holdout=int((selected.retained&selected.holdout).sum()))]
    pd.DataFrame(rows).to_csv(TABLES/"inversion_observation_quality.csv",index=False)
    pd.DataFrame([dict(scope=label,n=len(frame),flask_minus_insitu_mean_ppb=frame["diff"].mean(),
        median_ppb=frame["diff"].median(),sd_ppb=frame["diff"].std(),minimum_ppb=frame["diff"].min(),
        maximum_ppb=frame["diff"].max(),scale=NF.scale("ch4")) for label,frame in (("study_period",j),("2019",year))]).to_csv(TABLES/"inversion_flask_summary.csv",index=False)


def natural_global_audit():
    """Whole-product mass sanity checks, distinct from regional prior totals."""
    rows=[]
    for folder,filename,var in (("soil","MeMo_CH4uptake_Climatology.nc","CH4uptake"),
        ("geological","Etiope_CH4GeologicalEmis_ScaledToHmiel.1x1.nc","emi_ch4"),
        ("termites","CAMS-GLOB-TERM_v1.1_methane_2000.nc","CH4"),
        ("wetlands","LPJ_MERRA2_2019_0.5x0.5.nc","emis_ch4")):
        with xr.open_dataset(DATA/"inversion"/folder/filename) as ds:
            field=ds[var].sortby("lat").sortby("lon").load()
            area=cell_area_km2(field.lat.values,field.lon.values)*1e6
            seconds=(np.array([365]) if field.sizes["time"]==1 else field.time.dt.days_in_month.values)*86400
            mass=float((field.values*seconds[:,None,None]*area[None,:,:]).sum()/1e9)
            rows.append(dict(source=folder,global_annual_magnitude_Tg_CH4=mass,
                temporal_basis="Static annualized 365-day field" if len(seconds)==1 else "Native twelve monthly intervals",
                units="kg CH4 m-2 s-1",sign_in_budget="negative" if folder=="soil" else "positive"))
    pd.DataFrame(rows).to_csv(TABLES/"natural_source_global_audit.csv",index=False)


def responses(group="base",allow_partial=False):
    """Convolve unsmoothed, cell/hour-integrated footprints with source fluxes."""
    TABLES.mkdir(parents=True,exist_ok=True)
    with xr.open_dataset(OUT/"monthly_prior_fluxes.nc") as ds:monthly=ds.load()
    with xr.open_dataset(OUT/"daily_fire_prior_fluxes.nc") as ds:fire=ds.load()
    lat,lon=np.meshgrid(LAT,LON,indexing="ij")
    _,_,distance=Geod(ellps="WGS84").inv(np.full(lon.shape,100.318),np.full(lat.shape,-.202),lon,lat)
    near=distance<=500000
    edge=np.zeros(near.shape,bool);edge[[0,-1],:]=True;edge[:,[0,-1]]=True
    selection=pd.read_csv(OUT/"receptor_selection.csv",parse_dates=["time_utc"])
    wanted=selection.loc[selection.retained,"time_utc"]
    directories=[OUT/"runs"/group/f"bkt_{s:%Y%m%dT%H%MZ}" for s in wanted]
    if group!="base":directories=sorted((OUT/"runs"/group).glob("bkt_*"))
    rows=[];sectors=[];endpoint_rows=[];lag_rows=[];spatial=[];support=[]
    for directory in directories:
        if not (directory/"run_metadata.json").exists():
            if allow_partial:continue
            raise ValueError(f"Missing transport: {directory.name}")
        field,meta=read_footprint(directory)
        if not np.allclose(field.lat,LAT) or not np.allclose(field.lon,LON):raise ValueError("Footprint/flux grid mismatch")
        stamp=pd.Timestamp(meta["observation"]["time_utc"]).tz_localize(None)
        points=boundary_samples(directory,meta)
        point_plus=boundary_samples(directory,meta,500.)
        point_minus=boundary_samples(directory,meta,-500.)
        points.to_csv(directory/"boundary_samples.csv",index=False)
        survival=len(points)/meta["actual_particles"]
        response={};component_maps={}
        for source in monthly.source.values:
            flux=monthly.flux.sel(source=source)
            selected=flux.sel(month=xr.DataArray(pd.DatetimeIndex(field.time.values).to_period("M").to_timestamp(),dims="time"))
            values=np.sum(field.values*selected.values,axis=0)*1000
            response[str(source)]=float(values.sum());component_maps[str(source)]=values
            sectors.append(dict(group=group,time_utc=stamp,source=source,prior_enhancement_ppb=float(values.sum())))
        selected=fire.sel(day=xr.DataArray(pd.DatetimeIndex(field.time.values).normalize(),dims="time"))
        fire_map=np.sum(field.values*selected.noncrop_fire_flux.values,axis=0)*1000
        crop_map=np.sum(field.values*selected.crop_fire_flux.values,axis=0)*1000
        anthropogenic=np.sum([v for k,v in component_maps.items() if k.startswith("CH4_")],axis=0)
        total=float(field.sum());agg=field.sum("time").values
        lag=(stamp-pd.DatetimeIndex(field.time.values)).total_seconds()/3600
        hourly=field.sum(("lat","lon")).values
        for h,w in zip(lag,hourly):lag_rows.append(dict(group=group,time_utc=stamp,lag_hours=h,sensitivity=w))
        met=ROOT/"data/hysplit/gfs0p25/regional"/f"{stamp:%Y%m%d}_gfs0p25"
        met_values={}
        for variable in ("PBLH","SHGT","U10M","V10M","T02M"):
            native,_=arl_surface(met,variable,stamp.hour)
            # Native nearest cell mirrors NOAA profile, distinct from endpoint bilinear interpolation.
            met_values[variable]=float(native[round((-.202+20)/.25),round((100.318-75)/.25)])
        rows.append(dict(group=group,time_utc=stamp,anthro_near_ppb=anthropogenic[near].sum(),
            anthro_far_ppb=anthropogenic[~near].sum(),wetlands_ppb=response["wetlands"],fire_ppb=fire_map.sum(),
            crop_overlap_ppb=crop_map.sum(),termites_ppb=response["termites"],geological_ppb=response["geological"],
            soil_uptake_ppb=response["soil_uptake"],background_ppb=points.background_ppb.mean(),
            background_height_plus500_ppb=point_plus.background_ppb.mean(),background_height_minus500_ppb=point_minus.background_ppb.mean(),
            endpoint_sd_ppb=points.background_ppb.std(),endpoint_count=len(points),emitted_particles=meta["actual_particles"],
            endpoint_survival_fraction=survival,endpoint_below_midlevel_percent=100*points.below_lowest_midlevel.mean(),
            transport_usable=survival>=.95,sensitivity=total,within500_sensitivity_percent=100*agg[near].sum()/total,
            oldest24h_sensitivity_percent=100*hourly[lag>meta["configuration"]["hours_back"]-24].sum()/total,
            edge_sensitivity_percent=100*agg[edge].sum()/total,**met_values))
        component_stack=np.stack([anthropogenic*near,anthropogenic*~near,component_maps["wetlands"],fire_map])
        spatial.append(component_stack);support.append(agg)
        endpoint_rows.append(points.assign(receptor_utc=stamp).drop(columns=["time"]))
        print(f"Source and background operator: {stamp}",flush=True)
    if not rows:raise ValueError("No verified operator rows")
    frame=pd.DataFrame(rows).sort_values("time_utc")
    frame=frame.merge(selection[["time_utc","ch4","co","co2","holdout"]],on="time_utc",validate="one_to_one")
    frame.to_csv(TABLES/f"operator_{group}.csv",index=False)
    pd.DataFrame(sectors).to_csv(TABLES/f"sector_responses_{group}.csv",index=False)
    pd.DataFrame(lag_rows).to_csv(TABLES/f"lag_responses_{group}.csv",index=False)
    pd.concat(endpoint_rows).to_csv(OUT/f"endpoints_{group}.csv.gz",index=False,compression="gzip")
    ds=xr.Dataset({"prior_contribution":(("receptor","component","lat","lon"),np.asarray(spatial)),
        "footprint":(("receptor","lat","lon"),np.asarray(support)),"distance_km":(("lat","lon"),distance/1000)},
        coords={"receptor":[r["time_utc"] for r in rows],"component":["anthro_near","anthro_far","wetlands","fire"],"lat":LAT,"lon":LON})
    ds.prior_contribution.attrs["units"]="ppb";ds.footprint.attrs["units"]="ppm / (umol m-2 s-1)"
    save_nc(ds,OUT/f"spatial_operator_{group}.nc")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("stage",choices=["prepare","fire","observations","responses","natural-audit"])
    p.add_argument("--group",default="base");p.add_argument("--allow-partial",action="store_true")
    args=p.parse_args()
    if args.stage=="responses":responses(args.group,args.allow_partial)
    else:{"prepare":prepare,"fire":prepare_fire,"observations":observation_quality,"natural-audit":natural_global_audit}[args.stage]()
