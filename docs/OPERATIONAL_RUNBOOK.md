# Operational runbook: background monitoring and episode transport

Two scripts carry the operational work. Neither needs an inversion, because the
inversion does not predict a withheld day better than its own boundary field at
these towers (`BKT_JMB_CO2_Report`, and Section 4.6 of
`BKT_JMB_Two_Receptor_Report`).

## 1. Monitoring, every station, no external data

```bash
python3 scripts/a97_operational_monitor.py all
```

Writes to `outputs/operational/`: `baseline_<CODE>.csv` (hourly value, local and
climatological baselines, enhancement), `episodes.csv` (one row per episode with
tracer ratios and bootstrap intervals), `monthly_summary.csv` (background level,
enhancement distribution, episode counts, and the data coverage beside them).

Runs on the harmonized archive alone, so a new station works the day its record
loads. Add `--stations KMY PLU` to restrict it.

Read `episode_hours_per_1000_observed`, not `episode_hours`: a data gap must
never be read as a quiet month.

## 2. Transport for one episode, any station

Plan first. This touches no network and no model, and prints what the work will
cost before anything is committed:

```bash
python3 scripts/a98_episode_transport.py plan --episode-rank 1 --episode-station BKT --workers 14
```

Or an explicit window, one or several stations:

```bash
python3 scripts/a98_episode_transport.py plan --stations JMB KMY --window 2024-10-05 2024-10-08 --label haze_oct24 --workers 14
```

Then, in order, each acting only on an existing plan:

```bash
python3 scripts/a98_episode_transport.py fetch-met --label bkt_20151007 --interface wlp0s20f3
python3 scripts/a98_episode_transport.py run       --label bkt_20151007 --workers 14
python3 scripts/a98_episode_transport.py influence --label bkt_20151007
```

`influence` adds a forward prediction when given a flux field:

```bash
python3 scripts/a98_episode_transport.py influence --label bkt_20151007 --flux path/to/flux.nc --variable emission
```

Fetch and run are both resumable: fetch retries each day across several passes,
and run skips any receptor that already holds a completion receipt, so an
interrupted campaign continues where it stopped.

## Costs, measured rather than assumed

| Quantity | Measured value | Source |
| --- | --- | --- |
| Meteorology, wide crop | 457 MB per day | 43 GB for the 94 days of the 2024 campaign |
| NOAA server-side extraction | about 4 minutes per day | the same campaign, when the queue is responsive |
| One backward run, 120 h, 2,000 particles | 59 minutes median | 252 runs of the 2024 campaign |

A 5-day episode at one station is roughly 10 days of meteorology (4.5 GB, 40
minutes) and 3 runs per receptor hour.

## Inlet heights

| Station | Inlet | Where it came from |
| --- | --- | --- |
| BKT, JMB | 100 m | supplied for the two-receptor study |
| KMY, PLU, SRG | 30 m | supplied 17 September 2026 |

Release height is recorded in every completion receipt. It matters less than it
looks at BKT: 100, 150 and 300 m change the out-of-sample error there by at most
0.10 ppm (Section 4.7 of the CO2 report).

## What to point it at, and what to avoid

Daytime episodes first. Half the detected episodes are night-dominated, and a
nocturnal enhancement is accumulation under a shallow layer as much as it is a
plume arriving. That layer is exactly what a quarter-degree model cannot carry,
so a night footprint will not be tested by the observation. `plan` refuses to
guess: a window with no afternoon hours produces an empty plan that says why.

The strongest signal in the archive is the October 2015 haze at BKT, hourly CO
reaching 5795 ppb. It is the natural first target, because a transport layer
that cannot attribute that one cannot attribute anything.

## 3. Attribution and maps, once footprints exist

Once a station has a spatial operator file, every question about where its
signal comes from is arithmetic on arrays already written, and nothing has to be
re-run. This is the part to reach for when someone asks what the tower is
measuring rather than whether the inversion works.

```
python3 scripts/a110_attribution.py all         # eight tables, seconds not hours
python3 scripts/a109_operational_maps.py        # six publication maps
python3 scripts/a111_report_questions.py        # the question index, printed
python3 scripts/a107_operational_report.py      # rebuild the report from them
python3 scripts/validate_operational_report.py  # 65 checks against the evidence
```

`a110 all` orders the stages correctly: the peat stage needs the budget, and the
flux stage needs the provincial shares. Run a stage on its own only when the one
it depends on is already current.

What the tables answer, in the order a question usually arrives:

| Question | Table |
| --- | --- |
| what arrives, and does the prior predict it | `attribution_records.csv` |
| how far away and how old the sources are | `attribution_distance.csv`, `attribution_age.csv` |
| which province or district carries the signal | `attribution_provinces.csv`, `attribution_districts.csv` |
| which sector emits it | `attribution_budget.csv` |
| how much comes off peatland | `attribution_peat.csv` |
| what emission the posterior implies, and what could be detected | `attribution_flux.csv` |

The detection limit in the last of those is the number to quote when asked
whether a network can verify a commitment. It does not depend on the prior being
right, only on the posterior width, so it survives every disagreement about the
inventory.
