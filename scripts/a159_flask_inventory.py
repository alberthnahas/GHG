#!/usr/bin/env python3
"""BKT NOAA flask inventory 2004-2018 for a possible flask-receptor footprint phase (a159, no runs).

Counts sampling events (flask pairs averaged at the same UTC hour, noaa_flask.events)
per year with CO2, with CH4 and with both, QC-passed and all, plus their UTC hours.
Writes outputs/hysplit/long_record/tables/flask_bkt_2004_2018.csv and
flask_bkt_hours_2004_2018.csv.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ghg_common as G  # noqa: E402
import noaa_flask as NF  # noqa: E402

OUT = G.OUT / "hysplit" / "long_record" / "tables"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows, hours = [], []
    for qc in (True, False):
        co2, ch4 = NF.events("co2", qc=qc), NF.events("ch4", qc=qc)
        both = co2.index.intersection(ch4.index)
        for y in range(2004, 2019):
            sel = lambda idx: idx[(idx.year == y)]
            c, m, b = sel(co2.index), sel(ch4.index), sel(both)
            rows.append(dict(qc_passed_only=qc, year=y, events_co2=len(c), events_ch4=len(m), events_both=len(b),
                             days_both=len(pd.Index(b.normalize()).unique()),
                             utc_hours_both=" ".join(f"{h:02d}:{n}" for h, n in pd.Series(b.hour).value_counts().sort_index().items())))
        b = both[(both.year >= 2004) & (both.year <= 2018)]
        h = pd.Series(b.hour).value_counts().sort_index()
        hours += [dict(qc_passed_only=qc, utc_hour=int(k), events_both=int(v)) for k, v in h.items()]
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "flask_bkt_2004_2018.csv", index=False)
    pd.DataFrame(hours).to_csv(OUT / "flask_bkt_hours_2004_2018.csv", index=False)
    print(t.to_string(index=False))
    print(pd.DataFrame(hours).to_string(index=False))


if __name__ == "__main__":
    main()
