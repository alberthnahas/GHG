"""Run a bounded, tracer-independent HYSPLIT-STILT transport benchmark."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, replace
import json
from pathlib import Path
import re

import numpy as np
import pandas as pd

import a37_bkt_footprint as model
import a41_bkt_gfs as gfs
from a39_bkt_refinement import actual_particles

ROOT = model.ROOT
OUT = ROOT / "outputs/hysplit/benchmark"
HOME = ROOT.parent / "AQ/tools/hysplit.v5.4.2_UbuntuOS20.04.6LTS"
WIDE = gfs.MET / "benchmark_wide"
BOUNDS = (50, -40, 160, 30)
ANCHORS = tuple(pd.to_datetime(["2019-09-09T06:00", "2019-09-09T18:00",
                               "2019-09-23T06:00", "2019-09-23T18:00"]))
LOSS_ANCHOR = pd.Timestamp("2019-10-06T06:00")


def configuration(hours: int = 72) -> model.FootprintConfig:
    return model.FootprintConfig(meteorology_label=gfs.LABEL, particles=500,
        hours_back=hours, grid_spacing_deg=.25, grid_span_lat_deg=36,
        grid_span_lon_deg=48, particle_diagnostic_variables=0, save_endpoints=True)


def scenarios() -> dict[str, tuple[model.FootprintConfig, model.TransportOptions]]:
    """Predeclared one-factor contrasts, not concentration-based tuning."""
    cfg = configuration()
    opts = model.TransportOptions(dump_interval_hours=6)
    return {
        "control": (cfg, opts),
        "mix100": (cfg, replace(opts, minimum_mixing_depth_m=100)),
        "mix50": (cfg, replace(opts, minimum_mixing_depth_m=50)),
        "mix_native": (cfg, replace(opts, mixing_depth_method=0)),
        "height60": (replace(cfg, receptor_height_m_agl=60), opts),
        "convection_off": (cfg, replace(opts, convection=-1)),
        "convection_cape500": (cfg, replace(opts, convection=500)),
    }


def inventory() -> None:
    """Reconcile original endpoint status without inferring a lost location."""
    rows = []
    for directory in sorted((ROOT / "outputs/hysplit/inversion/runs/base").glob("bkt_*")):
        meta = json.loads((directory / "run_metadata.json").read_text())
        points = pd.read_csv(directory / "PAR_GIS.txt", skipinitialspace=True)
        points.columns = points.columns.str.strip()
        message = (directory / "MESSAGE").read_text()
        emitted = actual_particles(message)
        if len(points) != emitted or points.NSORT.duplicated().any():
            raise ValueError(f"Incomplete or duplicate particle ledger: {directory}")
        active = points.PGRD > 0
        if not points.loc[active, "latitude"].between(-20, 20).all() or not points.loc[active, "longitude"].between(75, 130).all():
            raise ValueError("Active baseline endpoints lie outside meteorological bounds")
        rows.append(dict(time_utc=meta["observation"]["time_utc"], emitted=emitted,
            active=int(active.sum()), inactive=int((~active).sum()),
            retained_percent=float(active.mean()*100), pass95=bool(active.mean() >= .95),
            runtime_seconds=meta["model_runtime_seconds"],
            endpoint_file_sha256=model.sha256_file(directory/"PAR_GIS.txt"),
            message_sha256=model.sha256_file(directory/"MESSAGE"),
            source_run=str(directory.relative_to(ROOT)),
            limitation="Inactive PGRD=0 coordinates are placeholders; loss location/time not retained"))
    frame = pd.DataFrame(rows)
    if frame.empty or frame.time_utc.duplicated().any():
        raise ValueError("Empty or duplicate baseline inventory")
    (OUT / "tables").mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT / "tables/baseline_completeness.csv", index=False)
    pd.DataFrame([dict(n_runs=len(frame), n_fail95=int((~frame.pass95).sum()),
        min_retained_percent=frame.retained_percent.min(),
        median_runtime_seconds=frame.runtime_seconds.median())]).to_csv(
            OUT/"tables/baseline_summary.csv", index=False)
    print(frame[["time_utc", "retained_percent"]].sort_values("retained_percent").head(6).to_string(index=False))


def run_one(stamp: pd.Timestamp, name: str, cfg: model.FootprintConfig,
            opts: model.TransportOptions, met_dir: Path) -> Path:
    target = OUT / "runs" / name / f"bkt_{stamp:%Y%m%dT%H%MZ}"
    paths = [met_dir / f"{d:%Y%m%d}_gfs0p25" for d in pd.date_range(
        (stamp-pd.Timedelta(hours=cfg.hours_back)).normalize(), stamp.normalize())]
    marker = target/"benchmark_complete.json"
    if marker.exists():
        saved = json.loads(marker.read_text())
        expected = dict(configuration=asdict(cfg), transport_options=asdict(opts),
                        meteorology_files=[str(p.resolve()) for p in paths])
        if any(saved[k] != value for k, value in expected.items()):
            raise ValueError(f"Existing benchmark configuration differs: {target}")
        for filename, digest in saved["output_sha256"].items():
            if model.sha256_file(target/filename) != digest:
                raise ValueError(f"Completed benchmark output changed: {target/filename}")
        return target
    if (target/"run_metadata.json").exists():
        meta = json.loads((target/"run_metadata.json").read_text())
        if (meta["configuration"] != asdict(cfg) or meta.get("transport_options") != asdict(opts)
                or meta['meteorology_files'] != [str(p.resolve()) for p in paths]):
            raise ValueError("Refusing to reuse different benchmark settings")
    else:
        target = model.run_footprint(stamp, met_dir, OUT/"runs"/name, HOME, cfg, False,
            meteorology_paths=paths, transport=opts,
            observation_context={"station":"BKT", "time_utc":stamp.isoformat()+"Z",
                "purpose":"Transport benchmark; gas values do not select scenarios"})
    model.run_checked([str(HOME/"exec/par2asc"), "-iPARDUMP", "-oendpoints.txt",
                       "-vendpoint_times.txt", "-a1"], target, "endpoints")
    meta = json.loads((target/"run_metadata.json").read_text())
    receipt = {k:meta[k] for k in ("configuration", "transport_options", "meteorology_files")}
    receipt["output_sha256"] = {name:model.sha256_file(target/name) for name in
                               ("footprint.nc", "PAR_GIS.txt", "MESSAGE", "SETUP.CFG", "CONTROL")}
    receipt["executable_sha256"] = model.sha256_file(HOME/"exec/hycs_std")
    marker.write_text(json.dumps(receipt, indent=2)+"\n")
    return target


def run_jobs(jobs: list[tuple], workers: int) -> None:
    with ThreadPoolExecutor(max_workers=workers) as pool:
        pending = {pool.submit(run_one, *job): job for job in jobs}
        for future in as_completed(pending):
            print(f"Completed {future.result()}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["inventory", "probe", "probe_cape500", "loss_control", "fetch_wide", "loss_wide", "loss_wide_output", "physics", "sampling"])
    parser.add_argument("--workers", type=int, choices=[1,2,3,4], default=2)
    parser.add_argument("--scenario", choices=list(scenarios()))
    parser.add_argument("--exclude",choices=list(scenarios()),action='append',default=[])
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.stage == "inventory":
        inventory()
    elif args.stage == "fetch_wide":
        days = list(pd.date_range("2019-10-01", "2019-10-06"))
        with ThreadPoolExecutor(max_workers=min(2,args.workers)) as pool:
            list(pool.map(lambda day: gfs.regional_extract(dates=[str(day.date())], bounds=BOUNDS, directory=WIDE), days))
    elif args.stage in ("loss_control", "loss_wide", "loss_wide_output"):
        met = WIDE if 'wide' in args.stage else gfs.MET/"regional"
        cfg=configuration(120)
        if args.stage=='loss_wide_output':
            cfg=replace(cfg,grid_span_lat_deg=60,grid_span_lon_deg=100)
        run_jobs([(LOSS_ANCHOR,args.stage,cfg,model.TransportOptions(dump_interval_hours=1),met)], 1)
    elif args.stage in ('probe','probe_cape500'):
        opts=model.TransportOptions(dump_interval_hours=1,convection=500 if args.stage=='probe_cape500' else -2)
        run_jobs([(ANCHORS[0],args.stage,configuration(6),opts,gfs.MET/"regional")],1)
    elif args.stage=='sampling':
        jobs=[(stamp,f'control_seedm{abs(seed)}',replace(configuration(),seed=seed),
               model.TransportOptions(dump_interval_hours=6),gfs.MET/'regional')
              for seed in (-10,-20) for stamp in ANCHORS]
        pd.DataFrame([dict(scenario=n,time_utc=s.isoformat()+'Z',**asdict(c),**asdict(o))
            for s,n,c,o,_ in jobs]).to_csv(OUT/'sampling_plan.csv',index=False)
        run_jobs(jobs,args.workers)
    else:
        choices = scenarios()
        plan = [(stamp,name,cfg,opts,gfs.MET/"regional") for name,(cfg,opts) in choices.items() for stamp in ANCHORS]
        pd.DataFrame([dict(scenario=n,time_utc=s.isoformat()+"Z",**asdict(c),**asdict(o))
                      for s,n,c,o,_ in plan]).to_csv(OUT/"scenario_plan.csv",index=False)
        if args.scenario:
            choices = {args.scenario:choices[args.scenario]}
        choices={name:value for name,value in choices.items() if name not in args.exclude}
        jobs = [(stamp,name,cfg,opts,gfs.MET/"regional") for name,(cfg,opts) in choices.items() for stamp in ANCHORS]
        run_jobs(jobs,args.workers)


if __name__ == "__main__":
    main()
