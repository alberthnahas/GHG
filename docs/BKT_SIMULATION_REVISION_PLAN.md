# BKT simulation revision (11 September 2026)

Scope: fix the simulation-side weaknesses listed in
`BKT_FOOTPRINT_REVIEW_2026-09-11.md`. The report, operator and inversion are
rebuilt in a later stage; no earlier run directory is modified.

Script: `scripts/a74_bkt_simulation_revision.py` (`list`, `run`, `summarize`).
Outputs: `outputs/hysplit/revision/` (runs, receipts, `ensemble_mean/`,
`tables/`, `summary.json`). Tests: `tests/test_bkt_simulation_revision.py`.

## Shared configuration

- Meteorology: GFS 0.25 degree, 50 to 160 E, 40 S to 30 N daily ARL crops
  (`data/hysplit/gfs0p25/benchmark_wide`, 4 September to 6 October 2019).
- Footprint grid: 0.25 degree, 60 by 100 degree span centred on BKT.
- 120 h backward, STILT settings unchanged from the inversion baseline
  (KMIXD=3, KMIX0=250, KBLT=5, IDSP=2, ICHEM=8, VEGHT=0.5).
- Two concentration layers: the STILT half-PBL surface layer (identical to
  every earlier product) plus a fixed 1,000 m layer recorded in
  `footprint_layers.nc` for injection-height sensitivity. A 6 h test showed
  layer 1 bit-identical with and without the second layer.
- Coefficients are normalized to the actual emitted count in `summarize`.
- Endpoints kept as `PAR_GIS.txt`; the binary `PARDUMP` is deleted after
  conversion.

## Groups

| Group | Receptors | Particles | Seeds | Height | Runs |
|---|---|---|---|---|---|
| ensemble | 52 retained twice-daily hours | 2,000 | 0, -10, -20 | 30 m | 156 |
| terrain_h80 | 4 benchmark anchors | 2,000 | 0, -10, -20 | 80 m | 12 |
| afternoon | 05, 07, 08 UTC on 28 days | 2,000 | 0 | 30 m | 84 |
| forward | 26 Sep 2019 01 UTC | 10,000 | 0, -10, -20 | 30 m | 3 |
| forward_h80 | 26 Sep 2019 01 UTC | 10,000 | 0 | 80 m | 1 |

80 m is 864.5 + 30 minus the nearest GFS cell terrain (816 m), rounded to
10 m. Bilinear terrain at the station is 835 m, so the existing 60 m runs
already bracket the lower end; 80 m is the nearest-cell upper bound.

The afternoon window mean (12:00 to 15:00 WIB) combines the 05, 07 and 08 UTC
single-seed members with the 06 UTC three-seed mean, aligned on backward lag.

## What is not fixed here

Convective redistribution. HYSPLIT prints `Convective mixing - F` for every
configuration tried, including the CAPE threshold test, because the GFS
archive carries no convective-flux fields. The receipt check refuses any run
whose log claims otherwise, so the limitation stays explicit. Fixing it
needs a driver with convective fluxes (WRF via `arw2arl`).

## Expected cost

About 28 min per 2,000-particle 120 h run and 2.5 h per 10,000-particle run
on one core; 256 runs at 12 workers is roughly 12 to 14 h wall clock.

## Progress

2026-09-11: driver extended for extra layers (default CONTROL byte-identical,
all earlier receipts still validate), campaign script and tests written,
6 h smoke test of run, receipt reuse and summary passed. Campaign launched
with `nohup ... run --group all --jobs 12`, log at
`outputs/hysplit/revision/campaign.log`.

First launch stalled: one forward member failed at startup in a race on the
first concurrent pandas index lookup, and the driver's main loop raised while
the pool kept working, so no progress was ever logged. Fixed by building the
observation contexts on the main thread, logging every failed job with its
traceback, and retrying once. Relaunched 13:35 WIB with all 256 runs pending.

## Inversion rerun (queued behind the campaign)

`scripts/a75_bkt_revised_inversion.py` (tests in
`tests/test_bkt_revised_inversion.py`) builds the operator from the 52
three-seed ensemble means on the wide grid using the wide flux inputs already
prepared by `a71`, then runs the unchanged `a49` fit, robustness, synthetic
and budget stages against `outputs/hysplit/revision/inversion`. Run on a
copy of the original operator, the fit reproduces the published posterior
to 1e-13, so any change is attributable to the transport revision.

Two predeclared variants follow: `tuned` scales the transport-error
fraction so the training reduced chi-square is one (the published 50 %
setting gives well under one), and `nearfield_tuned` splits anthropogenic
emissions at 50 km and 500 km. Both are reported as sensitivity fits
alongside the base rerun, not as replacements.

Operator stage was smoke-tested on a 12 h two-seed ensemble (the 6 h test
endpoint fell at 00 UTC, which the CarbonTracker daily files do not contain;
real endpoints are at 06 and 18 UTC).

## ERA5 as an alternative driver

Feasible. HYSPLIT 5.4.2 ships `era52arl` (in `exec/`), which converts ERA5
pressure-level GRIB1 plus surface analysis and forecast GRIB1 into ARL
format using a `era52arl.cfg` field map. The binary here needs the
versioned eccodes names (`libeccodes_f90.so.0`, `libeccodes.so.0`); a
directory with two symlinks to `/usr/local/lib` on `LD_LIBRARY_PATH` is
enough (tested 11 September 2026; the binary then runs and asks for its
GRIB inputs). `cdsapi`, `cfgrib` and a CDS credentials file are present.

Gains: hourly cadence and a true reanalysis instead of the 3-hourly GFS
forecast stitch. Costs: pressure-level ERA5 only (37 levels; the converter
does not read the 137 model levels), so the lowest layers at an 865 m
station are 925 to 850 hPa, coarser near the surface than the 55 hybrid GFS
levels; no convective mass fluxes, so convection stays parameterized off.
Proposed as a bounded driver test on the four anchors and the forward
case, requiring a CDS download of roughly 9 days of 0.25 degree
pressure-level and surface fields over 50 to 160 E, 40 S to 30 N.

### ERA5 queued (authorized 11 September 2026)

`scripts/a76_bkt_era5_driver.py` (`fetch`, `convert`, `check`, `run`; tests in
`tests/test_bkt_era5_driver.py`). `outputs/hysplit/era5/queue_after_campaign.sh`
waits for the campaign driver to exit, then fetches 15 days (4 to 9 and 18 to
26 September 2019) of hourly ERA5 pressure-level (27 levels, 1000 to 100 hPa)
and single-level GRIB over 50 to 160 E, 40 S to 30 N through the CDS client,
converts each day with `era52arl`, parses the ARL headers and runs a 6 h
HYSPLIT probe. Log: `outputs/hysplit/era5/pipeline.log`. The `run` stage
(four anchors and the forward case, three seeds each, same grid, layers and
STILT settings as the GFS revision) is started by hand after the check.
`outputs/hysplit/era5/run_after_check.sh` (queued 11 September) starts the 15
ERA5 runs automatically when the check passes; log `outputs/hysplit/era5/runs.log`.

### Full-period ERA5 and ERA5 ensemble (authorized 11 September 2026)

`outputs/hysplit/era5/full_period_after_ready.sh` waits for the 15-day set
to pass its check, fetches and converts the remaining 18 days (full
4 September to 6 October), waits for the anchor and forward runs, then runs
the 52-receptor three-seed ERA5 ensemble (`a76 run --group ensemble`,
156 runs). Log: `outputs/hysplit/era5/full_pipeline.log`.

Before the ERA5 inversion can be fitted, `a75` needs a general ARL reader
for endpoint terrain and native surface sampling (the current one is
GFS-specific); write it once the first ERA5 ARL file exists.

## Reporting stage (after all simulations)

Figures and tables to generate from the revision outputs, each from a named
script with a CSV behind every number:

- run ledger and retention (52 receptors, original vs wide, GFS vs ERA5)
- seed spread of prior increments: old 540-particle vs new 6,000-particle
- terrain-height sensitivity (30, 60, 80 m) at the anchors
- afternoon window versus 06 UTC single hour (lag-resolved footprints)
- forward case: 72 h regional vs 120 h wide, fire contribution by source
  day, surface layer vs 1,000 m layer (injection sensitivity)
- driver comparison maps and diagnostics: GFS vs ERA5 at the anchors
- inversion: operator comparison, chi-square scan, posterior old vs revised
  vs tuned vs near-field vs ERA5, withheld evaluation per variant

Report structure: split the single 59-page document into
1. BKT source influence for the 26 September 2019 case (forward report),
2. BKT methane inversion September to October 2019 (inversion report, with
   the revision and driver comparison as its results, not appendices),
3. Transport technical companion (benchmark, domain correction, BARRA
   screen, ERA5 driver evaluation, definitions).
Remove repeated boilerplate; lead each summary with findings, then limits.
