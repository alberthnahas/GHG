"""Pressure-matched radiosonde check of GFS forcing, with date-block intervals."""
from __future__ import annotations

from functools import lru_cache
import json

import numpy as np
import pandas as pd

from a37_bkt_footprint import ROOT, sha256_file
from a65_transport_observations import TABLES
from bkt_arl import GFSReader, pressure_interpolate

MET=ROOT/'data/hysplit/gfs0p25/regional'
PRESSURES=(925.,850.,700.,500.,300.)
OLD_POSITIONS={'IDM00096163':(-.883,100.350),'IDM00096109':(.467,101.450)}


@lru_cache(maxsize=4)
def reader(date: str) -> GFSReader:
    return GFSReader(MET/(date+'_gfs0p25'))


def profile_at(stamp,lat,lon,method):
    lower=stamp.floor('3h');upper=stamp.ceil('3h')
    a=reader(lower.strftime('%Y%m%d')).profile(lower,lat,lon,method)
    if lower==upper:return a
    b=reader(upper.strftime('%Y%m%d')).profile(upper,lat,lon,method)
    f=(stamp-lower).total_seconds()/(upper-lower).total_seconds()
    # Interpolate each hybrid-level state in time before log-pressure matching.
    return a*(1-f)+b*f


def match() -> pd.DataFrame:
    data=pd.read_csv(TABLES/'igra_levels.csv',keep_default_na=False,na_values=[''])
    data=data[(data.level_type==1)&data.pressure_hpa.isin(PRESSURES)]
    if data.duplicated(['station','time_utc','pressure_hpa']).any():
        raise ValueError('Duplicate standard pressure levels')
    rows=[]
    for (station,time),group in data.groupby(['station','time_utc']):
        stamp=pd.Timestamp(time).tz_localize(None)
        first=group.iloc[0]
        nominal=(float(first.latitude),float(first.longitude))
        # The release date is not supplied. Test a symmetric time displacement,
        # rather than inventing dates from an ambiguous HHMM field.
        cases=[('primary',stamp,*nominal,'bilinear'),
               ('nearest',stamp,*nominal,'nearest'),
               ('historical_position',stamp,*OLD_POSITIONS[station],'bilinear'),
               ('time_minus_1h',stamp-pd.Timedelta(hours=1),*nominal,'bilinear'),
               ('time_plus_1h',stamp+pd.Timedelta(hours=1),*nominal,'bilinear')]
        for case,when,lat,lon,method in cases:
            try: profile=profile_at(when,lat,lon,method)
            except FileNotFoundError:
                if case=='primary':raise
                continue
            for _,observed in group.iterrows():
                p=observed.pressure_hpa
                row=dict(station=station,time_utc=time,date_utc=stamp.strftime('%Y-%m-%d'),
                    nominal_hour=stamp.hour,scenario=case,pressure_hpa=p,latitude=lat,longitude=lon,
                    model_time_utc=when.isoformat()+'Z',n_model_levels=len(profile))
                for variable,source,target,offset in [('u','u_ms','UWND',0),('v','v_ms','VWND',0),
                                                    ('temperature','temperature_c','TEMP',-273.15)]:
                    row[variable+'_observed']=observed[source]
                    row[variable+'_model']=pressure_interpolate(profile,p,target)+offset
                    row[variable+'_error']=row[variable+'_model']-row[variable+'_observed']
                row['wind_vector_squared_error']=row['u_error']**2+row['v_error']**2
                rows.append(row)
        print(f'Matched {station} {time}',flush=True)
    result=pd.DataFrame(rows)
    result=with_complete_profile_control(result)
    result.to_csv(TABLES/'profile_matches.csv',index=False)
    files=sorted(MET.glob('2019*_gfs0p25'))
    pd.DataFrame([dict(file=p.name,sha256=sha256_file(p)) for p in files]).to_csv(
        TABLES/'profile_meteorology_provenance.csv',index=False)
    return result


def with_complete_profile_control(data):
    data=data[data.scenario!='complete_profiles'].copy()
    primary=data[data.scenario=='primary']
    complete=primary.groupby(['station','time_utc']).filter(lambda g:len(g)==5 and
        g[['u_error','v_error','temperature_error']].notna().all().all()).copy()
    complete['scenario']='complete_profiles'
    return pd.concat([data,complete],ignore_index=True)


def summarize(data: pd.DataFrame) -> None:
    rows=[]
    rng=np.random.default_rng(20260906)
    for (station,case),group in data.groupby(['station','scenario']):
        # First average squared errors within sounding, then across soundings.
        sounding=group.groupby(['date_utc','time_utc']).agg(
            u_bias=('u_error','mean'),v_bias=('v_error','mean'),temperature_bias=('temperature_error','mean'),
            vector_mse=('wind_vector_squared_error','mean'),
            temperature_mse=('temperature_error',lambda x:np.mean(x*x)),
            u_mse=('u_error',lambda x:np.mean(x*x)),v_mse=('v_error',lambda x:np.mean(x*x)))
        daily=sounding.groupby(level='date_utc').mean()
        # Daily blocks preserve shared weather/within-sounding dependence.
        for metric in daily.columns:
            values=daily[metric].dropna().to_numpy()
            n=len(values)
            if not n:continue
            starts=rng.integers(0,n,size=(3000,int(np.ceil(n/3))))
            draws=((starts[:,:,None]+np.arange(3))%n).reshape(3000,-1)[:,:n]
            estimate=values.mean();samples=values[draws].mean(axis=1)
            label=metric
            if metric.endswith('_mse'):
                estimate=np.sqrt(estimate);samples=np.sqrt(samples);label=metric[:-4]+'_rmse'
            lo,hi=np.quantile(samples,[.025,.975]) if n>=10 else (np.nan,np.nan)
            rows.append(dict(station=station,scenario=case,metric=label,value=estimate,
                ci95_low=lo,ci95_high=hi,n_days=n,n_soundings=int(sounding[metric].notna().sum()),
                n_level_pairs=len(group),bootstrap_block_days=3,bootstrap_resamples=3000,
                units='K' if metric.startswith('temperature') else 'm s-1'))
    pd.DataFrame(rows).to_csv(TABLES/'profile_metrics.csv',index=False)
    primary=data[data.scenario=='primary']
    influence=[]
    for station,group in primary.groupby('station'):
        soundings=group.groupby(['date_utc','time_utc']).wind_vector_squared_error.mean().dropna()
        daily=soundings.groupby(level='date_utc').mean()
        total_mse=daily.mean()
        for (date,stamp),mse in soundings.items():
            n_day=int((soundings.index.get_level_values('date_utc')==date).sum())
            contribution=mse/n_day/len(daily)
            remaining=soundings.drop(index=(date,stamp))
            leave_out=np.sqrt(remaining.groupby(level='date_utc').mean().mean())
            influence.append(dict(station=station,time_utc=stamp,sounding_vector_rmse=np.sqrt(mse),
                contribution_to_total_mse_percent=100*contribution/total_mse,
                leave_one_sounding_out_vector_rmse=leave_out,n_same_day_soundings=n_day,
                primary_vector_rmse=np.sqrt(total_mse)))
    pd.DataFrame(influence).to_csv(TABLES/'profile_influence.csv',index=False)
    levels=[]
    for (station,case,p),group in data[data.scenario.isin(['primary','complete_profiles'])].groupby(
            ['station','scenario','pressure_hpa']):
        daily=group.groupby('date_utc')[['u_error','v_error','temperature_error','wind_vector_squared_error']].mean()
        row=dict(station=station,scenario=case,pressure_hpa=p,n_pairs=len(group),
            n_wind_pairs=int(group.wind_vector_squared_error.notna().sum()),
            n_temperature_pairs=int(group.temperature_error.notna().sum()),
            u_bias_ms=daily.u_error.mean(),v_bias_ms=daily.v_error.mean(),
            temperature_bias_k=daily.temperature_error.mean(),
            vector_rmse_ms=np.sqrt(daily.wind_vector_squared_error.mean()))
        for variable,label,root in [('temperature_error','temperature_bias',False),
                                    ('wind_vector_squared_error','vector_rmse',True)]:
            values=daily[variable].dropna().to_numpy();n=len(values)
            if n<10:lo,hi=np.nan,np.nan
            else:
                starts=rng.integers(0,n,size=(3000,int(np.ceil(n/3))))
                draw=((starts[:,:,None]+np.arange(3))%n).reshape(3000,-1)[:,:n]
                estimates=values[draw].mean(axis=1)
                if root:estimates=np.sqrt(estimates)
                lo,hi=np.quantile(estimates,[.025,.975])
            row[label+'_ci95_low']=lo;row[label+'_ci95_high']=hi
        levels.append(row)
    pd.DataFrame(levels).to_csv(TABLES/'profile_by_pressure.csv',index=False)
    print(pd.DataFrame(rows).query("scenario=='primary'").to_string(index=False))


if __name__=='__main__':
    summarize(match())
