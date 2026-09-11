"""Extract model-diagnosed mixing depths without treating them as observations."""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import pandas as pd
from a64_transport_benchmark import OUT, HOME, configuration
from a37_bkt_footprint import ascdata_text, control_text
from a41_bkt_gfs import MET


def run(hours: int=6):
    start=pd.Timestamp('2019-09-09T06:00')
    cfg=configuration(hours)
    paths=[MET/'regional'/f'{d:%Y%m%d}_gfs0p25' for d in pd.date_range(
        (start-pd.Timedelta(hours=hours)).normalize(),start.normalize())]
    target=OUT/'mixing_diagnostics'/f'probe_{hours}h'
    target.mkdir(parents=True,exist_ok=True)
    (target/'CONTROL').write_text(control_text(start,paths,target,cfg))
    (target/'ASCDATA.CFG').write_text(ascdata_text(HOME))
    with (target/'vmixing.log').open('w') as stream:
        subprocess.run([str(HOME/'exec/vmixing'),'-s1','-t5','-d3','-l50'],cwd=target,
                       stdout=stream,stderr=subprocess.STDOUT,check=True,timeout=120)
    print(target)


def series():
    rows=[]
    for day in pd.date_range('2019-09-09','2019-10-06'):
        for method in (0,3):
            target=OUT/'mixing_diagnostics'/f'{day:%Y%m%d}_method{method}'
            target.mkdir(parents=True,exist_ok=True)
            cfg=configuration(21)
            # vmixing uses forward absolute duration. Supply an explicit
            # positive duration and only the standard meteorological CONTROL.
            text=control_text(day,[MET/'regional'/f'{day:%Y%m%d}_gfs0p25'],target,cfg)
            lines=text.splitlines();lines[3]='21'
            (target/'CONTROL').write_text('\n'.join(lines[:9])+'\n')
            (target/'ASCDATA.CFG').write_text(ascdata_text(HOME))
            with (target/'vmixing.log').open('w') as stream:
                subprocess.run([str(HOME/'exec/vmixing'),'-s1','-t5',f'-d{method}','-l50'],cwd=target,
                    stdout=stream,stderr=subprocess.STDOUT,check=True,timeout=120)
            records=(target/'STABILITY.txt').read_text().splitlines()[3:]
            if len(records)!=8:raise ValueError('Incomplete mixing diagnostic day')
            for line in records:
                values=line.split()
                year,month,date,hour,minute=map(int,values[1:6])
                stamp=pd.Timestamp(year=2000+year,month=month,day=date,hour=hour,minute=minute)
                if stamp.normalize()!=day:raise ValueError('Mixing diagnostic chronology differs')
                zi=float(values[7])
                rows.append(dict(time_utc=stamp.isoformat()+'Z',method=method,hour_wib=(hour+7)%24,
                    mixing_depth_m=zi,minimum_m=50,below100=zi<100,below250=zi<250))
            print(f'Completed mixing diagnosis {day.date()} method {method}',flush=True)
    frame=pd.DataFrame(rows)
    frame.to_csv(OUT/'tables/mixing_depth_series.csv',index=False)
    frame['period']=frame.hour_wib.map(lambda h:'day_07_17_WIB' if 7<=h<17 else 'night_17_07_WIB')
    summary=frame.groupby(['method','period']).agg(n=('mixing_depth_m','size'),
        minimum_m=('mixing_depth_m','min'),median_m=('mixing_depth_m','median'),
        below100_percent=('below100',lambda x:100*x.mean()),below250_percent=('below250',lambda x:100*x.mean()))
    summary.to_csv(OUT/'tables/mixing_depth_summary.csv')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hours',type=int,default=6)
    parser.add_argument('--series',action='store_true')
    args=parser.parse_args()
    series() if args.series else run(args.hours)
