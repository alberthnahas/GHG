"""Auditable domain and meteorological diagnostics for transport benchmarks."""
from __future__ import annotations

import argparse
import json
import re
import subprocess

import numpy as np
import pandas as pd
import xarray as xr

from a64_transport_benchmark import OUT, ROOT, WIDE, BOUNDS, HOME
from a37_bkt_footprint import sha256_file
from a39_bkt_refinement import actual_particles
from bkt_arl import GFSReader


def ledger(name: str) -> None:
    directory = next((OUT/'runs'/name).glob('bkt_*'))
    meta = json.loads((directory/'run_metadata.json').read_text())
    anchor = pd.Timestamp(meta['observation']['time_utc']).tz_localize(None)
    data = pd.read_csv(directory/'PAR_GIS.txt',skipinitialspace=True)
    data.columns = data.columns.str.strip()
    def timestamp(raw):
        month,day,year,hour,minute = map(int,re.findall(r'\d+',raw))
        return pd.Timestamp(year=2000+year,month=month,day=day,hour=hour,minute=minute)
    data['time_utc'] = data.time.map(timestamp)
    data['lag_hours'] = (anchor-data.time_utc).dt.total_seconds()/3600
    emitted = actual_particles((directory/'MESSAGE').read_text())
    rows, losses = [], []
    bounds = BOUNDS if 'wide' in name else (75,-20,130,20)
    west,south,east,north = bounds
    for lag, group in data.groupby('lag_hours',sort=True):
        if len(group)!=emitted or group.NSORT.duplicated().any():
            raise ValueError('Incomplete particle ledger')
        active = group.PGRD>0
        rows.append(dict(scenario=name,lag_hours=lag,emitted=emitted,
                         active=int(active.sum()),retained_percent=100*active.mean()))
    for particle,group in data.groupby('NSORT'):
        group=group.sort_values('lag_hours')
        active=group.PGRD>0
        if (np.diff(active.astype(int))>0).any():
            raise ValueError('Inactive particle subsequently reactivated')
        if active.all(): continue
        last=group[active].iloc[-1]
        first=group[~active].iloc[0]
        lat,lon=float(last.latitude),float(last.longitude)
        # Spherical great-circle distance to meridians/parallels; sufficient
        # to classify the nearest boundary, not a reconstructed crossing.
        distances=np.array([6371*np.arcsin(abs(np.cos(np.deg2rad(lat))*np.sin(np.deg2rad(lon-west)))),
            6371*np.deg2rad(abs(lat-south)),
            6371*np.arcsin(abs(np.cos(np.deg2rad(lat))*np.sin(np.deg2rad(east-lon)))),
            6371*np.deg2rad(abs(north-lat))])
        nearest=int(np.argmin(distances))
        losses.append(dict(scenario=name,particle=int(particle),last_active_lag_hours=last.lag_hours,
            first_inactive_lag_hours=first.lag_hours,last_latitude=lat,last_longitude=lon,
            last_height_m_agl=last.height,nearest_boundary=['west','south','east','north'][nearest],
            distance_to_boundary_km=distances[nearest]))
    tables=OUT/'tables';tables.mkdir(exist_ok=True,parents=True)
    pd.DataFrame(rows).to_csv(tables/f'{name}_retention.csv',index=False)
    pd.DataFrame(losses,columns=['scenario','particle','last_active_lag_hours','first_inactive_lag_hours',
        'last_latitude','last_longitude','last_height_m_agl','nearest_boundary','distance_to_boundary_km']).to_csv(
            tables/f'{name}_loss_brackets.csv',index=False)
    print(pd.DataFrame(rows).iloc[[0,-1]].to_string(index=False))
    if losses:
        print(pd.DataFrame(losses).groupby('nearest_boundary').distance_to_boundary_km.agg(['size','min','median','max']).to_string())


def audit_wide() -> None:
    rows=[]; fields=[]
    for day in pd.date_range('2019-10-01','2019-10-06'):
        filename=f'{day:%Y%m%d}_gfs0p25'
        wide=GFSReader(WIDE/filename)
        base=GFSReader(ROOT/'data/hysplit/gfs0p25/regional'/filename)
        if (wide.lon[0],wide.lat[0],wide.lon[-1],wide.lat[-1])!=BOUNDS:
            raise ValueError('Expanded grid bounds differ')
        y=int(round((base.lat[0]-wide.lat[0])/.25))
        x=int(round((base.lon[0]-wide.lon[0])/.25))
        # All variable/level records at every timestamp, not sampled fields.
        maximum_scaled=0.; nonzero=0; checked=0
        for stamp,var,level in base.records:
            if var=='INDX':continue
            a=base.field(stamp,var,level)
            b=wide.field(stamp,var,level)[y:y+base.ny,x:x+base.nx]
            difference=float(np.max(np.abs(a-b)))
            # Provider repacks a larger crop using its own field-dependent
            # exponent. Compare within the sum of the two quantization steps.
            ha=base.records[(stamp,var,level)][1]; hb=wide.records[(stamp,var,level)][1]
            tolerance=2.**(int(ha[18:22])-7)+2.**(int(hb[18:22])-7)
            scaled=difference/tolerance
            maximum_scaled=max(maximum_scaled,scaled);nonzero+=difference>1.e-8;checked+=1
            fields.append(dict(date_utc=str(day.date()),time_utc=stamp.isoformat()+'Z',variable=var,
                level=level,maximum_absolute_difference=difference,packing_tolerance=tolerance,
                maximum_difference_over_tolerance=scaled))
            if difference>tolerance*1.001+1.e-7:
                raise ValueError(f'Shared-domain meteorology changed: {filename} {stamp} {var} {level}: {difference}')
        rows.append(dict(date_utc=str(day.date()),nx=wide.nx,ny=wide.ny,nz=wide.nz,
            west=wide.lon[0],east=wide.lon[-1],south=wide.lat[0],north=wide.lat[-1],spacing_deg=.25,
            n_times=len(wide.times),n_fields_compared=checked,n_nonidentical_fields=nonzero,
            maximum_difference_over_packing_tolerance=maximum_scaled,sha256=sha256_file(WIDE/filename)))
    pd.DataFrame(fields).to_csv(OUT/'tables/wide_meteorology_field_comparison.csv',index=False)
    pd.DataFrame(rows).to_csv(OUT/'tables/wide_meteorology_audit.csv',index=False)
    print(pd.DataFrame(rows).to_string(index=False))


def footprint(directory):
    meta=json.loads((directory/'run_metadata.json').read_text())
    n=actual_particles((directory/'MESSAGE').read_text())
    with xr.open_dataset(directory/'footprint.nc') as ds:
        field=ds.footprint_sensitivity.astype(float).load()*meta['configuration']['particles']/n
    if not np.isfinite(field).all() or float(field.min())<0:
        raise ValueError('Invalid footprint')
    return field,meta,n


def summarize_runs():
    rows=[];contrasts=[]
    for marker in sorted((OUT/'runs').glob('*/*/benchmark_complete.json')):
        directory=marker.parent;name=directory.parent.name
        if name.startswith('probe'):continue
        field,meta,n=footprint(directory)
        points=pd.read_csv(directory/'PAR_GIS.txt',skipinitialspace=True)
        points.columns=points.columns.str.strip()
        final=points[points.time==points.time.iloc[-1]]
        if len(final)!=n or final.NSORT.duplicated().any():raise ValueError('Incomplete endpoint ledger')
        stamp=pd.Timestamp(meta['observation']['time_utc']).tz_localize(None)
        lag=(stamp-pd.DatetimeIndex(field.time.values)).total_seconds()/3600
        hourly=field.sum(('lat','lon')).values;total=float(hourly.sum())
        agg=field.sum('time').values
        edge=np.zeros(agg.shape,dtype=bool);edge[[0,-1],:]=True;edge[:,[0,-1]]=True
        row=dict(scenario=name,time_utc=stamp.isoformat()+'Z',hours_back=meta['configuration']['hours_back'],
            emitted=n,active=int((final.PGRD>0).sum()),retained_percent=100*(final.PGRD>0).mean(),
            normalized_sensitivity=total,oldest24h_percent=100*hourly[lag>lag.max()-24].sum()/total,
            output_edge_percent=100*agg[edge].sum()/total,runtime_seconds=meta['model_runtime_seconds'],
            footprint_sha256=sha256_file(directory/'footprint.nc'))
        rows.append(row)
        control=OUT/'runs'/'control'/directory.name
        if name not in ('control','loss_control','loss_wide','loss_wide_output') and (control/'benchmark_complete.json').exists():
            reference,_,_=footprint(control)
            if not field.coords.equals(reference.coords):raise ValueError('Unmatched scenario coordinates')
            a=reference.sum('time').values;b=agg
            contrasts.append(dict(scenario=name,time_utc=row['time_utc'],hour_wib=(stamp.hour+7)%24,
                sensitivity_ratio=total/float(reference.sum()),
                relative_l1_percent=100*np.abs(b-a).sum()/a.sum(),
                spatial_correlation=np.corrcoef(a.ravel(),b.ravel())[0,1],
                maximum_cell_hour_difference=float(np.max(np.abs(field.values-reference.values))),
                max_absolute_cell_difference=float(np.abs(b-a).max()),retained_percent=row['retained_percent']))
    pd.DataFrame(rows).to_csv(OUT/'tables/benchmark_run_summary.csv',index=False)
    pd.DataFrame(contrasts).to_csv(OUT/'tables/physics_contrasts.csv',index=False)
    if contrasts:
        pd.DataFrame(contrasts).groupby('scenario').agg(n=('sensitivity_ratio','size'),
            ratio_min=('sensitivity_ratio','min'),ratio_median=('sensitivity_ratio','median'),
            ratio_max=('sensitivity_ratio','max'),l1_median_percent=('relative_l1_percent','median'),
            minimum_retained_percent=('retained_percent','min')).to_csv(OUT/'tables/physics_summary.csv')
    print(pd.DataFrame(rows).drop(columns=['footprint_sha256']).to_string(index=False))


def duration_and_dump_check():
    rows=[]
    for directory in sorted((OUT/'runs/control').glob('bkt_*')):
        if not (directory/'benchmark_complete.json').exists():continue
        short,meta,n=footprint(directory)
        original=ROOT/'outputs/hysplit/inversion/runs/base'/directory.name
        full,_,_=footprint(original)
        matched=full.sel(time=short.time)
        difference=float(np.max(np.abs(short.values-matched.values)))
        rows.append(dict(time_utc=meta['observation']['time_utc'],
            sensitivity_72h=float(short.sum()),sensitivity_120h=float(full.sum()),
            beyond72h_percent=100*(float(full.sum())-float(matched.sum()))/float(full.sum()),
            maximum_matched_cell_hour_difference=difference,
            comparison='Same 72h interval; original 120h run versus shorter run with periodic dumps'))
    pd.DataFrame(rows).to_csv(OUT/'tables/duration_sensitivity.csv',index=False)
    target=OUT/'runs/loss_control/bkt_20191006T0600Z'
    new,_,_=footprint(target)
    old,_,_=footprint(ROOT/'outputs/hysplit/inversion/runs/base'/target.name)
    pd.DataFrame([dict(maximum_cell_hour_difference=float(np.max(np.abs(new.values-old.values))),
        normalized_sensitivity_original=float(old.sum()),normalized_sensitivity_repeated_dumps=float(new.sum()),
        original_sha256=sha256_file(ROOT/'outputs/hysplit/inversion/runs/base'/target.name/'footprint.nc'),
        diagnostic_sha256=sha256_file(target/'footprint.nc'))]).to_csv(OUT/'tables/dump_invariance.csv',index=False)
    print(pd.DataFrame(rows).to_string(index=False))


def native_profile_check():
    target=OUT/'native_profile_check';target.mkdir(parents=True,exist_ok=True)
    met=ROOT/'data/hysplit/gfs0p25/regional'
    with (target/'profile.log').open('w') as stream:
        subprocess.run([str(HOME/'exec/profile'),f'-d{met}/','-f20190909_gfs0p25',
            '-y-0.883','-x100.35','-o0','-t3','-n1','-e1'],cwd=target,
            stdout=stream,stderr=subprocess.STDOUT,check=True,timeout=60)
    lines=(target/'profile.txt').read_text().splitlines()
    start=next(i for i,line in enumerate(lines) if '3D Fields' in line)+3
    values=np.asarray([list(map(float,line.split())) for line in lines[start:start+55]])
    reader=GFSReader(met/'20190909_gfs0p25')
    native=reader.profile(pd.Timestamp('2019-09-09'),-.883,100.35,'nearest')
    rows=[]
    for var,column,offset,display_tolerance in [('TEMP',1,-273.15,.02),('UWND',2,0,.006),
            ('VWND',3,0,.006),('RELH',5,0,.006),('PRES',6,0,.51)]:
        for i in range(55):
            header=reader.records[(pd.Timestamp('2019-09-09'),var,i+1)][1]
            tolerance=max(display_tolerance,2.**(int(header[18:22])-7))
            value=native.iloc[i][var]+offset;reference=values[i,column]
            passed=abs(value-reference)<=tolerance
            rows.append(dict(level=i+1,variable=var,reader_value=value,noaa_profile_value=reference,
                tolerance=tolerance,passed=passed,
                note='Comparison allows field packing and native display precision; evaluation uses 273.15 K offset'))
    frame=pd.DataFrame(rows)
    frame.to_csv(OUT/'tables/native_profile_reader_check.csv',index=False)
    if not frame.passed.all():raise ValueError(frame[~frame.passed].to_string(index=False))
    print(f'Passed {len(frame)} native profile comparisons')


def domain_comparison():
    rows=[];curves=[]
    name='bkt_20191006T0600Z'
    original,_,_=footprint(OUT/'runs/loss_control'/name)
    for case in ('loss_control','loss_wide','loss_wide_output'):
        field,meta,n=footprint(OUT/'runs'/case/name)
        shared=field.sel(lat=original.lat,lon=original.lon,method='nearest',tolerance=1.e-5)
        total=float(field.sum());shared_total=float(shared.sum())
        edge=np.zeros((field.sizes['lat'],field.sizes['lon']),dtype=bool)
        edge[[0,-1],:]=True;edge[:,[0,-1]]=True
        points=pd.read_csv(OUT/'runs'/case/name/'PAR_GIS.txt',skipinitialspace=True)
        points.columns=points.columns.str.strip()
        final=points[points.time==points.time.iloc[-1]]
        active=final[final.PGRD>0]
        west,south,east,north=BOUNDS if 'wide' in case else (75,-20,130,20)
        lat=active.latitude.to_numpy();lon=active.longitude.to_numpy()
        distances=np.stack([6371*np.arcsin(abs(np.cos(np.deg2rad(lat))*np.sin(np.deg2rad(lon-west)))),
            6371*np.deg2rad(abs(lat-south)),
            6371*np.arcsin(abs(np.cos(np.deg2rad(lat))*np.sin(np.deg2rad(east-lon)))),
            6371*np.deg2rad(abs(north-lat))])
        rows.append(dict(scenario=case,normalized_sensitivity=total,shared_grid_sensitivity=shared_total,
            shared_grid_change_vs_original_percent=100*(shared_total/float(original.sum())-1),
            outside_original_output_percent=100*(total-shared_total)/total,
            output_edge_percent=100*field.sum('time').values[edge].sum()/total,
            emitted=n,active=len(active),retained_percent=100*len(active)/n,
            minimum_endpoint_boundary_distance_km=float(distances.min()),
            endpoint_east_of_original_met_percent=100*(lon>130).sum()/n,
            endpoint_min_lat=float(lat.min()),endpoint_max_lat=float(lat.max()),
            endpoint_min_lon=float(lon.min()),endpoint_max_lon=float(lon.max())))
        if case=='loss_wide_output':
            narrow,_,_=footprint(OUT/'runs/loss_wide'/name)
            rows[-1]['maximum_shared_cell_hour_difference']=float(np.max(np.abs(narrow.values-shared.values)))
        stamp=pd.Timestamp(meta['observation']['time_utc']).tz_localize(None)
        lag=(stamp-pd.DatetimeIndex(field.time.values)).total_seconds()/3600
        hourly=field.sum(('lat','lon')).values
        for order in np.argsort(lag):
            curves.append(dict(scenario=case,lag_hours=lag[order],hourly_sensitivity=hourly[order]))
    curve=pd.DataFrame(curves).sort_values(['scenario','lag_hours'])
    curve['cumulative_sensitivity']=curve.groupby('scenario').hourly_sensitivity.cumsum()
    curve.to_csv(OUT/'tables/domain_sensitivity_by_lag.csv',index=False)
    pd.DataFrame(rows).to_csv(OUT/'tables/domain_comparison.csv',index=False)
    print(pd.DataFrame(rows).to_string(index=False))


def convection_execution():
    rows=[]
    for case in ('control','convection_off','convection_cape500'):
        for marker in sorted((OUT/'runs'/case).glob('*/benchmark_complete.json')):
            directory=marker.parent;meta=json.loads((directory/'run_metadata.json').read_text())
            message=(directory/'MESSAGE').read_text()
            reported=float(re.search(r'CAPEMIN=\s*([-+0-9.Ee]+)',message)[1])
            if reported!=meta['transport_options']['convection']:raise ValueError('Executed convection setting differs')
            met=GFSReader(meta['meteorology_files'][0])
            atmospheric=sorted({v for _,v,l in met.records if l>0})
            surface=sorted({v for _,v,l in met.records if l==0 and v!='INDX'})
            rows.append(dict(scenario=case,time_utc=meta['observation']['time_utc'],reported_capemin=reported,
                supplied_cape='CAPE' in surface,atmospheric_fields=','.join(atmospheric),surface_fields=','.join(surface),
                wrf_interpolation_disabled='WVERT=.FALSE.' in message,
                interpretation='Requested parameter verified; threshold activation is not recorded by this diagnostic'))
    frame=pd.DataFrame(rows)
    if len(frame)!=12:raise ValueError('Convection execution matrix incomplete')
    frame.to_csv(OUT/'tables/convection_execution.csv',index=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['ledger','audit_wide','summary','duration','native_profile','domain','convection'])
    parser.add_argument('--scenario',default='loss_control')
    args=parser.parse_args()
    if args.stage=='ledger':ledger(args.scenario)
    elif args.stage=='audit_wide':audit_wide()
    elif args.stage=='summary':summarize_runs()
    elif args.stage=='duration':duration_and_dump_check()
    elif args.stage=='native_profile':native_profile_check()
    elif args.stage=='domain':domain_comparison()
    else:convection_execution()
