"""Multi-receptor GFS transport acquisition and endpoint-enabled pilot runs."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import fcntl
import json
from pathlib import Path
import time
import pandas as pd
import a37_bkt_footprint as model
import a41_bkt_gfs as gfs
import ghg_common as G

ROOT = model.ROOT
OUT = ROOT / "outputs/hysplit/inversion"
HYSPLIT_HOME = ROOT.parent / "AQ/tools/hysplit.v5.4.2_UbuntuOS20.04.6LTS"
DATES = pd.date_range("2019-09-02", "2019-10-06")
RECEPTORS = [d + pd.Timedelta(hours=h) for d in pd.date_range("2019-09-09", "2019-10-06") for h in (6,18)]


def acquire():
    def one(day):
        for attempt in range(3):
            try:
                gfs.regional_extract(dates=[str(day.date())])
                gfs.audit_arl(gfs.MET / "regional" / f"{day:%Y%m%d}_gfs0p25")
                return
            except Exception as exc:
                print(f"Retry {day.date()}: {type(exc).__name__}: {exc}", flush=True)
                if attempt == 2: raise
                time.sleep(5)
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(one,DATES))


def run_one(stamp, cfg, name):
    directory=OUT / "runs" / name / f"bkt_{stamp:%Y%m%dT%H%MZ}"
    if (directory / "run_metadata.json").exists():
        meta=json.loads((directory/"run_metadata.json").read_text())
        from dataclasses import asdict
        if meta["configuration"] != asdict(cfg): raise ValueError("Existing run configuration differs")
        if (directory/"PAR_GIS.txt").exists(): return directory
        model.run_checked([str(HYSPLIT_HOME/"exec/par2asc"),"-iPARDUMP","-oendpoints.txt","-vendpoint_times.txt","-a1"],directory,"endpoints")
        return directory
    paths=[gfs.MET / "regional" / f"{d:%Y%m%d}_gfs0p25" for d in pd.date_range(
        (stamp-pd.Timedelta(hours=cfg.hours_back)).normalize(),stamp.normalize())]
    result=model.run_footprint(stamp,gfs.MET,OUT/"runs"/name,HYSPLIT_HOME,cfg,False,meteorology_paths=paths)
    model.run_checked([str(HYSPLIT_HOME/"exec/par2asc"),"-iPARDUMP","-oendpoints.txt","-vendpoint_times.txt","-a1"],result,"endpoints")
    return result


def run(short=False):
    cfg=model.FootprintConfig(meteorology_label=gfs.LABEL, particles=500,
        hours_back=120,grid_spacing_deg=.25,grid_span_lat_deg=36,
        grid_span_lon_deg=48,particle_diagnostic_variables=0,save_endpoints=True)
    if short:
        print(run_one(pd.Timestamp("2019-09-26T06:00"),replace(cfg,hours_back=6),"endpoint_test"),flush=True)
        return
    observations=G.apply_flags(G.load_station("BKT")).set_index("time_utc").reindex(RECEPTORS)
    observations.index.name="time_utc"
    observations["scheduled"]=True
    observations["retained"]=observations.ch4.notna() & ~observations.suspect_ch4.fillna(True)
    observations["holdout"]=[i//2 % 4 == 3 for i in range(len(RECEPTORS))]
    OUT.mkdir(parents=True,exist_ok=True)
    observations.to_csv(OUT/"receptor_selection.csv")
    pending=list(observations.index[observations.retained])
    with ThreadPoolExecutor(max_workers=4) as pool:
        running={}
        while pending or running:
            for stamp in pending[:]:
                needed=[gfs.MET/"regional"/f"{d:%Y%m%d}_gfs0p25.audit.json" for d in pd.date_range(
                    (stamp-pd.Timedelta(hours=cfg.hours_back)).normalize(),stamp.normalize())]
                if len(running)<4 and all(p.exists() for p in needed):
                    running[pool.submit(run_one,stamp,cfg,"base")]=stamp
                    pending.remove(stamp)
            for future in list(running):
                if future.done():
                    print(f"Complete {future.result().name}",flush=True)
                    del running[future]
            if pending or running: time.sleep(10)


def sensitivities():
    """Preselected contrasting dates; bounded two-worker diagnostic ensemble."""
    base=model.FootprintConfig(meteorology_label=gfs.LABEL,particles=500,hours_back=120,
        grid_spacing_deg=.25,grid_span_lat_deg=36,grid_span_lon_deg=48,
        particle_diagnostic_variables=0,save_endpoints=True)
    anchors=pd.to_datetime(["2019-09-09T06:00","2019-09-16T18:00","2019-09-23T06:00","2019-09-30T18:00"])
    jobs=[]
    for i,stamp in enumerate(anchors):
        jobs.extend([(stamp,replace(base,seed=-10),"seed_m10"),(stamp,replace(base,receptor_height_m_agl=60),"height60")])
        if i in (0,2):
            jobs.extend([(stamp,replace(base,particles=2000),"n2000"),
                (stamp,replace(base,hours_back=72),"window72"),(stamp,replace(base,hours_back=168),"window168")])
    with ThreadPoolExecutor(max_workers=2) as pool:
        active={}
        while jobs or active:
            for job in jobs[:]:
                stamp,cfg,name=job
                needed=[gfs.MET/"regional"/f"{d:%Y%m%d}_gfs0p25.audit.json" for d in pd.date_range(
                    (stamp-pd.Timedelta(hours=cfg.hours_back)).normalize(),stamp.normalize())]
                if len(active)<2 and all(p.exists() for p in needed):
                    active[pool.submit(run_one,*job)]=job;jobs.remove(job)
            for future in list(active):
                if future.done():print(f"Sensitivity complete {future.result()}",flush=True);del active[future]
            if jobs or active:time.sleep(10)


def accelerate():
    """Compute ready late-period receptors independently of the chronological pool.

    Separate directories prevent concurrent writes. A completed result is linked
    atomically into the base tree only if the main worker has not started it.
    If both pools reach the same receptor, preserve both and use the base result.
    """
    base=model.FootprintConfig(meteorology_label=gfs.LABEL,particles=500,hours_back=120,
        grid_spacing_deg=.25,grid_span_lat_deg=36,grid_span_lon_deg=48,
        particle_diagnostic_variables=0,save_endpoints=True)
    selection=pd.read_csv(OUT/"receptor_selection.csv",parse_dates=["time_utc"])
    pending=list(selection.loc[selection.retained,"time_utc"].sort_values(ascending=False))
    with ThreadPoolExecutor(max_workers=4) as pool:
        active={}
        while pending or active:
            for stamp in pending[:]:
                target=OUT/"runs/base"/f"bkt_{stamp:%Y%m%dT%H%MZ}"
                if target.exists():pending.remove(stamp);continue
                needed=[gfs.MET/"regional"/f"{d:%Y%m%d}_gfs0p25.audit.json" for d in pd.date_range(
                    (stamp-pd.Timedelta(hours=120)).normalize(),stamp.normalize())]
                if len(active)<4 and all(p.exists() for p in needed):
                    active[pool.submit(run_one,stamp,base,"accelerated")]=target;pending.remove(stamp)
            for future in list(active):
                if future.done():
                    result=future.result();target=active.pop(future)
                    try:target.symlink_to(result,target_is_directory=True)
                    except FileExistsError:print(f"Base already active; preserved alternate {result.name}",flush=True)
                    else:print(f"Completed base receptor from auxiliary pool: {result.name}",flush=True)
            if pending or active:time.sleep(10)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage",choices=["fetch","test","run","sensitivities","accelerate"])
    a=p.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/f"{a.stage}.lock").open("w") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if a.stage=="fetch":acquire()
        elif a.stage=="accelerate":accelerate()
        elif a.stage=="sensitivities":sensitivities()
        else:run(a.stage=="test")
