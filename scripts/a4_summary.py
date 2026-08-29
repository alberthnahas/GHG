"""Station summary table for the report."""
import numpy as np, pandas as pd, ghg_common as g
df = pd.read_pickle(g.OUT / "all.pkl")
rows = []
for c in g.ORDER:
    s = df[df.station == c]
    nm, reg, lat, lon, el, setg, off = g.STATIONS[c]
    span = (s.time_local.max() - s.time_local.min()).total_seconds() / 3600 + 1
    r = dict(code=c, station=nm, region=reg, setting=setg,
             lat=lat, lon=lon, elev_m=el, tz=f"UTC+{off}",
             start=s.time_local.min().date(), end=s.time_local.max().date(),
             hours=len(s), completeness=100 * len(s) / span)
    for sp in ("co2", "ch4", "co"):
        cl = g.clean(s, sp)
        aft = cl[cl.hour_local.between(12, 16)][sp]
        r[f"{sp}_bg"] = aft.quantile(.20)
        r[f"{sp}_med"] = s[sp].median()
        r[f"{sp}_p99"] = s[sp].quantile(.99)
        r[f"{sp}_max"] = s[sp].max()
    rows.append(r)
T = pd.DataFrame(rows)
T.to_csv(g.OUT / "station_summary.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
print(T.round(1).to_string(index=False))
