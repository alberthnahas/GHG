#!/usr/bin/env python3
"""Terminal (120 h) particle endpoints for every BKT and JMB receptor with a footprint.

A background curtain is sampled where the particles are when the backward run
ends, exactly as a84/a89/a129 sample CarbonTracker.  This script gathers the
active terminal endpoints (PGRD > 0 at receptor time minus hours_back, the
a71.active_endpoints accounting) from the existing HYSPLIT-STILT runs, so that
any candidate background can be sampled without rerunning transport.

Campaigns read (read-only):
  2019      BKT Sep-Oct 2019 single receptor campaign: outputs/hysplit/inversion/endpoints_base.csv.gz
            (already holds the CarbonTracker-CH4 2025 value per particle)
  2023      two_receptor/runs        Nov-Dec 2023, GFS 0.25, three seeds
  2024      two_receptor/runs_2024   Oct-Dec 2024, GFS 0.25, two seeds
  2025_2026 two_receptor/runs_2025_2026  2025 to Sep 2026, GDAS1, one seed

Output (new folder, nothing existing is touched):
  outputs/background/endpoints_terminal.csv.gz   one row per active endpoint
  outputs/background/endpoint_receptors.csv      one row per receptor and seed:
      counts, endpoint time, mean/sd latitude, longitude, height, fraction south of the equator
No network, no HYSPLIT.  Times UTC.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import a71_domain_budget_extension as ext  # noqa: E402
from a39_bkt_refinement import actual_particles  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TWO = ROOT / "outputs/hysplit/two_receptor"
OUT = ROOT / "outputs/background"
CAMPAIGNS = {"2023": TWO / "runs", "2024": TWO / "runs_2024", "2025_2026": TWO / "runs_2025_2026"}


def gather() -> tuple[pd.DataFrame, pd.DataFrame]:
    points, receptors = [], []
    for campaign, root in CAMPAIGNS.items():
        for member in sorted(root.iterdir()):
            station, seed = member.name.split("_s")
            for directory in sorted(member.iterdir()):
                if not (directory / "completion_receipt.json").exists():
                    continue
                meta = json.loads((directory / "run_metadata.json").read_text())
                actual = actual_particles((directory / "MESSAGE").read_text())
                active = ext.active_endpoints(directory, meta, actual)
                stamp = pd.Timestamp(meta["observation"]["time_utc"]).tz_localize(None)
                end = stamp - pd.Timedelta(hours=meta["configuration"]["hours_back"])
                frame = pd.DataFrame(dict(campaign=campaign, station=station.upper(), seed=int(seed), time_utc=stamp,
                                          endpoint_utc=end, latitude=active.latitude.to_numpy(np.float32),
                                          longitude=active.longitude.to_numpy(np.float32),
                                          height_agl_m=active.height.to_numpy(np.float32)))
                points.append(frame)
                receptors.append(dict(campaign=campaign, station=station.upper(), seed=int(seed), time_utc=stamp,
                                      endpoint_utc=end, emitted=actual, active=len(active)))
        print(campaign, len(receptors), flush=True)
    # 2019 BKT campaign: endpoints already extracted by the a46-a49 chain, heights given above sea level.
    old = pd.read_csv(ROOT / "outputs/hysplit/inversion/endpoints_base.csv.gz", parse_dates=["receptor_utc"])
    old = old[old.PGRD > 0]
    frame = pd.DataFrame(dict(campaign="2019", station="BKT", seed=0, time_utc=old.receptor_utc,
                              endpoint_utc=old.receptor_utc - pd.Timedelta(hours=120),
                              latitude=old.latitude.astype(np.float32), longitude=old.longitude.astype(np.float32),
                              height_agl_m=(old.height_m_msl - old.terrain_m_msl).astype(np.float32),
                              ct_ch4_ppb=old.background_ppb.astype(np.float32)))
    points.append(frame)
    for stamp, g in frame.groupby("time_utc"):
        receptors.append(dict(campaign="2019", station="BKT", seed=0, time_utc=stamp,
                              endpoint_utc=stamp - pd.Timedelta(hours=120), emitted=np.nan, active=len(g)))
    pts = pd.concat(points, ignore_index=True)
    rec = pd.DataFrame(receptors)
    stats = pts.groupby(["campaign", "station", "seed", "time_utc"]).agg(
        lat_mean=("latitude", "mean"), lat_sd=("latitude", "std"), lon_mean=("longitude", "mean"),
        height_mean_m=("height_agl_m", "mean"), south_fraction=("latitude", lambda x: float((x < 0).mean())),
        above3km_fraction=("height_agl_m", lambda x: float((x > 3000).mean()))).reset_index()
    rec = rec.merge(stats, on=["campaign", "station", "seed", "time_utc"], validate="one_to_one")
    return pts, rec


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    pts, rec = gather()
    pts.to_csv(OUT / "endpoints_terminal.csv.gz", index=False, float_format="%.3f")
    rec.to_csv(OUT / "endpoint_receptors.csv", index=False, float_format="%.4f")
    print(rec.groupby(["campaign", "station"]).agg(receptors=("time_utc", "nunique"), runs=("seed", "size"),
                                                    lat=("lat_mean", "mean"), south=("south_fraction", "mean")).to_string())


if __name__ == "__main__":
    main()
