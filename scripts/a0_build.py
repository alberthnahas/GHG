"""Build the cached hourly frame that every other script reads.

`outputs/all.pkl` is the single input to the whole pipeline: the five raw JSON
files loaded, unit-harmonised, range-gated, time-base corrected and
suspect-period flagged, as one tidy frame of 242,411 station-hours.  It takes
about a second to rebuild, so it is a cache for convenience rather than a
checkpoint - delete it freely and re-run this.

Also writes `outputs/station_hours.csv`, a small coverage summary that is handy
for checking a rebuild did what you expected.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G


def main():
    G.OUT.mkdir(parents=True, exist_ok=True)
    G.FIG.mkdir(parents=True, exist_ok=True)

    d = G.load_all()
    out = G.OUT / "all.pkl"
    d.to_pickle(out)
    print(f"wrote {out.relative_to(G.ROOT)}  {d.shape[0]:,} rows x {d.shape[1]} cols")

    rows = []
    for st, g in d.groupby("station"):
        span_h = (g.time_local.max() - g.time_local.min()).total_seconds() / 3600 + 1
        rows.append(dict(
            station=st, name=G.STATIONS[st][0],
            start=str(g.time_local.min()), end=str(g.time_local.max()),
            hours=len(g), coverage_pct=100 * len(g) / span_h,
            co2=int(np.isfinite(g.co2).sum()), ch4=int(np.isfinite(g.ch4).sum()),
            co=int(np.isfinite(g.co).sum()),
            flagged_co2=int(g.suspect_co2.sum()), flagged_all=int(g.suspect.sum())))
    s = pd.DataFrame(rows)
    s.to_csv(G.OUT / "station_hours.csv", index=False)
    pd.set_option("display.width", 200)
    print(s.round(1).to_string(index=False))


if __name__ == "__main__":
    main()
