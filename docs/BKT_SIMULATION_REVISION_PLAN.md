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

2026-09-12 21:07 WIB: campaign complete, 256/256 runs, no failures, 100 %
retention everywhere; `summarize` written to `outputs/hysplit/revision/tables`.
Revised inversion (`a75 all`) completed earlier the same day; tuned covariance
(transport fraction 0.10) gives withheld RMSE 25.3 ppb versus 28.5 ppb
background-only, multipliers 0.37 / 0.24 / 0.43 / 0.68, three of four
intervals excluding unity (fires reach 1.00). Completion email sent.
ERA5 fetch started automatically; CDS transfer rate at start about 66 kB/s.

2026-09-13: CDS transfer from this site fell to about 5 kB/s per stream
(route congestion; NOAA S3 and Google's ARCO-ERA5 mirror were no better,
the latter 0.04 MB/s for a regional slice because its chunks are global).
ERA5 request cut to 70-140 E, 25-S to 20 N and 16 pressure levels, still
hourly; ERA5 footprint grid 40 by 60 degrees to stay inside it. The eight
wide-area surface files already fetched were moved to
`data/hysplit/era5/superseded_wide/`. Fetch restarted with six streams.
Same day, later: the workstation's WiFi link runs at about 12 MB/s abroad
against 0.3 MB/s on the LAN default route. `a76 fetch --interface wlp0s20f3`
pins the CDS transfers to the WiFi device (SO_BINDTODEVICE, no routing
change). Fetch restarted that way with four streams.

### ERA5 flux-sign defect (13 September 2026)

First ERA5 anchor runs gave 1.3 to 3.8 times the GFS surface sensitivity
with seed noise under 2 %, largest at 13:00 WIB, unchanged when HYSPLIT used
ERA5's own boundary-layer height instead of the Richardson diagnosis. Cause:
ECMWF accumulated sensible and latent heat fluxes are positive downward;
the stock `era52arl` field map only divides by 3600, so HYSPLIT received
about -170 W m-2 at midday and treated the daytime boundary layer as stable.
Fix: negate `sshf` and `slhf` in the converter map (`a76` CFG). The affected
ARL files, runs and comparison tables are kept under `*_v1_flux_sign_bug`
directories; all 15 days are reconverted and the 15 cases rerun
(`outputs/hysplit/era5/rerun_v2.log`). The 18-day fetch in progress converts
with the corrected map automatically.

Corrected ERA5 anchor comparison (`a79`, `outputs/hysplit/era5/tables`):
ERA5/GFS integrated sensitivity 1.17 to 1.84, cell-level spatial difference
74 to 120 % of total, seed CV under 1.5 %; ERA5 midday PBLH at BKT 919 m vs
GFS 1306 m. `bkt_arl.ARLReader` (generic, tested against `GFSReader` and the
ERA5 file) and `a75 --driver era5` added; ERA5 operator verified on the four
anchors and the GFS path reproduces the revision operator exactly. ERA5
inversion queued behind the 156-run ensemble
(`outputs/hysplit/era5/inversion.log`).

## Reporting stage executed (13 September 2026)

- `scripts/a81_bkt_revision_figures.py`: six revision figures (numerics and
  retention, release height and afternoon window, extended forward case,
  driver maps, inversion update, withheld evaluation).
- `scripts/a83_bkt_forward_extension_sources.py`: EDGAR and GFED convolution
  on the 120 h widened GFS and ERA5 forward footprints and the 1,000 m layer;
  CO2 and CO fire are lower bounds (local GFED extracts cover those gases only
  for 23 to 26 September on the regional box). A wide-box three-gas extraction
  for 21 to 26 September would complete them.
- `scripts/a82_bkt_reports.py` builds three reports from
  `docs/BKT_Forward_Report_template.md`, `docs/BKT_Inversion_Report_template.md`
  and `docs/BKT_Transport_Companion_template.md`, reusing the token builders of
  a45, a51, a55, a69 and a73 and renumbering figures and tables by order of
  appearance. Outputs: `BKT_Forward_Source_Influence_Report.md` (29 pages),
  `BKT_Methane_Inversion_Report.md` (29 pages),
  `BKT_Transport_Technical_Companion.md` (20 pages). The combined 59-page
  report is archived as
  `docs/archive/BKT_HYSPLIT_STILT_Footprint_Report_combined_20260913.md`.
- `validate_bkt_gfs_report.py`, `validate_bkt_barra.py`, `verify_all.sh` and
  `a14_latex.py` updated for the three documents.

2026-09-14: the wide-box three-gas GFED extract for 21 to 26 September
(`GFED51_20190921_26_wide.npz`, fetched over WiFi in 40 s with
`bkt_gfed_transfer.py --subset --interface`) completes the extended forward
case: GFS 120 h fire CO 738 ppb (139 % of observed), ERA5 1031 ppb (194 %),
fire CO2 3.80 and 5.52 ppm; methane agrees bit for bit with the earlier
methane-only extract. Lower-bound wording removed from the forward report.

## Two-receptor extension: BKT and Jambi (planned 14 September 2026)

The user asked for a run using both BKT and Jambi (JMB) data, with both inlets
taken as 100 m above ground. `scripts/a84_bkt_jmb_two_receptor.py` implements
it; `outputs/hysplit/two_receptor/tables/window_scan.csv` records the window
choice.

- Joint window: 24 November to 31 December 2023, receptors at 06 and 18 UTC.
  49 joint valid hours (21 at 06 UTC, 28 at 18 UTC), 12 held out as complete
  days (every fourth joint day). December 2024 has 60 joint hours but no
  CarbonTracker-CH4 boundary (the 2025 release ends in 2023) and no LPJ
  wetlands for 2024, so it is documented and not run.
- Runs: 2 receptors x 49 hours x 3 seeds x 2000 particles, 120 h backward,
  wide 60 x 100 degree grid centred on each receptor, 1,000 m extra layer,
  294 runs. Run directories `outputs/hysplit/two_receptor/runs/<code>_s<seed>/`.
- Meteorology: GFS 0.25 degree wide crop (50 to 160 E, 40 S to 30 N) for
  19 November to 31 December 2023 through the NOAA READY extraction,
  43 daily files of about 346 MB (about 15 GB) into
  `data/hysplit/gfs0p25/two_receptor_wide/`.
- Priors: EDGAR v8.0 monthly 2022 (latest year; proxy for 2023), LPJ-MERRA2
  wetlands 2023, climatological termites, geological and soil sinks, fire from
  the CarbonTracker-CH4 2025 pyrogenic monthly posterior (GFED5.1 daily ends in
  2022; no cropland partition). Flux grids are built per receptor because the
  footprint grid is centred on each receptor.
- Boundary: CarbonTracker-CH4 2025 daily mole fractions at 120 h endpoints,
  43 files of 36 MB.
- Inversion: shared four-component multipliers with per-station offset and
  trend nuisance terms; block covariance (correlated within a station,
  independent between stations); tuned transport fraction by reduced
  chi-square; cases joint, bkt_only, jmb_only, bkt_to_jmb and jmb_to_bkt
  (cross-site prediction).

Downloads wait for the user's authorization (about 19 GB in total).

2026-09-15: two-receptor campaign complete (294 runs, 19.2 h, no failures),
operator, inversion (nine cases including Jambi-night screening and a
fuel-exploitation sector split), figures T01 to T04 (`a85`), dataset availability probe (`a87`) and the
report `BKT_JMB_Two_Receptor_Report.md` built by `a86`. Headline: Jambi 18 UTC hours are
out-of-model (mixing depth 35 m, enhancement 220 ppb); screened joint
multipliers 0.29 near, 0.56 far, 0.40 wetlands; fuel exploitation 0.32.
Dataset check: EDGAR_2025_GHG covers 2023 and 2024; CT-NRT.v2025-1 is CO2
only; no CarbonTracker-CH4 release reaches 2024, so December 2024 remains
blocked for methane.

2026-09-15: peatland and wet-versus-dry tests added to the two-receptor
report as Section 5 (`scripts/a88_jambi_peat_tests.py`, figure T05). Peat map
`GHG_INDONESIA/indonesia_peatlands.json` (1,277 polygons, no attributes):
Jambi 4.2 km from peat, 29% peat within 25 km; night enhancement does not
follow peat exposure; a uniform peat flux term is unconstrained and does not
explain nights. Full-record nocturnal test reproduces Finding 85 (524 nights,
3.04): dry-season CO2 build-up faster and resolved; CH4 build-up and ratio
lower but unresolved, with dry 2024 and dry 2025 at opposite extremes.

2026-09-15: CO2 two-receptor inversion (`scripts/a89_bkt_jmb_co2.py`, tables
`outputs/hysplit/two_receptor/tables/co2_*.csv`) on the same 294 footprints.
Inputs: CT-NRT.v2025-1 three-hourly fluxes and CO2 boundary, EDGAR_2025_GHG
monthly fossil CO2 for 2023 (2.7 GB, authorized). Biosphere split by local
solar time into daytime and nighttime terms because the CT-NRT optimized flux
has an inverted day-night cycle over both tower cells from 25 November to
1 December. A CO2-only spike screen removes two Jambi hours; the 26 November
13 WIB spike (+79 ppm, CH4 and CO flat) alone drove a far-fossil factor of 56.
Findings: night CO2 is outside the model at both towers (observed +20 ppm at
BKT and +45 ppm at Jambi against priors of 6 and 7 ppm), and every fit with
night hours pushes the transport fraction to its cap. The daytime-only fit is
consistent (fraction 0.27), fossil factors are unconstrained, and biosphere
factors are 0.42 and 0.34 and stable under leave-one-out, but the posterior
has no skill (correlation near zero) and fits all daytime hours worse than
the background alone. Not committed.

2026-09-15: improved CO2 model (`scripts/a90_bkt_jmb_co2_improved.py`, tables
`co2_improved_*.csv`, `co2_diagnostic_biosphere_summary.csv`,
`co2_afternoon_observations.csv`, `co2_mixing_screen.csv`). Three changes,
tested separately on daytime receptors: (1) an independent diagnostic
biosphere prior from GFS de-accumulated shortwave (uptake) and 2 m temperature
with Q10 1.5 (respiration) on MODIS vegetated land, declared scale 3,000 g C
m-2 yr-1, balanced per cell; (2) 12-14 WIB observation means with a
neighbour-median CO2-only spike screen; (3) a well-mixed screen dropping
receptors with GFS mixing depth below 300 m (one BKT hour). Best case
diag_3h_mixed: Jambi daytime RMSE 3.63 ppm against 4.47 for background only
(correlation 0.47; 0.07 with the original CT-NRT model); BKT 4.05 against
3.35, still no skill. BKT-only factors predict Jambi better than its
background (4.37 against 5.05 ppm). Uptake and respiration factors 0.37 and
0.35 of the declared scale; fossil still unconstrained. Not committed.

2026-09-15: CO2 improvement experiments (`scripts/a91_bkt_jmb_co2_experiments.py`,
tables `co2_experiments*_skill.csv`, `*_parameters.csv`,
`co2_diagnostic_operator_local25.csv`). All variants on the same 27 daytime
receptors, scored by leave-one-date-out cross-validation (about 20 hours per
tower) as well as withheld days and transfer. Rounds: net-signal transport
error, CH4-residual covariate, saturating light, Q10 2, per-tower biosphere
factors, BKT wide prior, BKT local 25 km removal and split, BKT without
biosphere terms, CH4-enhancement covariate.
Out-of-sample result. Jambi: every biosphere variant beats the background;
best is per-tower biosphere factors with the CH4-residual covariate, RMSE 3.45
ppm against 4.72 (correlation 0.61; covariate 0.084 ppm per ppb, 0.015 to
0.157). BKT: no biosphere variant beats the background (4.4 to 5.2 against
3.56); local 25 km treatments do not help; BKT uptake and respiration shrink
to about 0.15 under a wide prior. The only BKT gain is the CH4-enhancement
covariate without biosphere terms, 3.24 against 3.56 (0.032 ppm per ppb,
-0.006 to 0.068). The BKT-without-biosphere joint fit is invalid as designed:
one shared transport fraction hits its cap and inflates Jambi errors. Not
committed.

2026-09-15: per-tower transport fractions and tower-specific covariates
(`a91` rounds 5a and 5b). With one fraction per tower, dropping BKT biosphere
terms no longer inflates Jambi errors. Leave-one-date-out RMSE, 100 m runs:
Jambi biosphere factors with the CH4-residual covariate 3.42 ppm against 4.72
background (correlation 0.62); BKT background with the CH4-enhancement
covariate and no biosphere terms 3.39 against 3.63 (correlation 0.27; 0.035
ppm per ppb, 0.004 to 0.065). BKT with its biosphere terms still 4.63. BKT
release-height campaign (`scripts/a92_bkt_release_height.py`, runs in
`outputs/hysplit/two_receptor/runs_bkt_height/`): the 15 scored BKT daytime
receptors at 150 m and 300 m above GFS ground, three seeds, 90 runs on 14
workers, started 15 September; round 5b scores the heights when it finishes.

2026-09-15: BKT 300 m release results (`co2_bkt_height_operator.csv`,
`co2_experiments_round5b_h300_*`). All 45 runs completed and all 15 receptors
keep their particles. Relative to 100 m, mean integrated sensitivity falls 3%
(8.60 to 8.35) and modeled uptake 7% (-29.9 to -27.7 ppm). Leave-one-date-out
RMSE at BKT: biosphere model 4.53 against 4.63 at 100 m (background 3.48);
background with the CH4-enhancement covariate 3.36 against 3.39. The GFS
afternoon mixed layer at BKT (median about 760 m) is deeper than either release,
so release height does not limit BKT CO2 skill. Date-block bootstrap: no BKT
or Jambi improvement over background is resolved at 95% with 12 to 15 dates.

2026-09-15: release-height campaign complete (90 of 90 runs, 5.7 h, no
failures) and scored (`co2_experiments_round5b_*`). BKT 150 m: sensitivity
8.58 against 8.60 at 100 m, uptake -29.5 against -29.9 ppm; 300 m: 8.35 and
-27.7. Leave-one-date-out RMSE at BKT, biosphere model: 4.63, 4.57, 4.53 at
100, 150, 300 m (background 3.48 to 3.54); background with CH4-enhancement
covariate: 3.39, 3.38, 3.36 (background 3.56 to 3.63). Jambi unchanged at 3.42
to 3.47 against 4.72. Release height is not the limit on BKT daytime CO2; no
gain over background is resolved at 95% by the date bootstrap. Not committed.

2026-09-17: October to December 2024 CO2 extension complete and scored, and it
reverses the 2023 reading. Campaign `scripts/a93_bkt_jmb_co2_2024.py`: 94 days
of GFS 0.25 ARL (restarted once after SSL failures), CT-NRT and EDGAR 2024
inputs, 63 joint afternoon receptors, 252 runs on 14 workers in 14.0 h with no
failures, 54 usable dates per tower against 15 in 2023. Two faults were found
and fixed on the way: the 2024 fossil months were hardcoded to October through
December while a 120 h back trajectory reaches 29 September, which broke the
operator after the campaign (months now derive from the footprint span); and
`receptor_frame` merged the 25 km local operator with an inner join, silently
dropping every 2024 receptor (now a left join with a row-count guard).

Results (`co2_experiments_round6_*`). The 2023 Jambi gain does not reproduce:
Jambi leave-one-date-out RMSE 6.25 against 5.56 for the background in 2024,
where 2023 gave 3.65 against 4.72; combined 5.82 against 5.40. BKT combined
3.00 against 2.70, and that difference is resolved at 95% by the date-block
bootstrap (+0.30 ppm, +0.03 to +0.57, 69 dates). The nuisance-only model, which
keeps the offset, trend and methane covariate but drops every source term,
beats the full posterior at both towers. The source terms carry no
out-of-sample information at this footprint resolution.

Robustness (`co2_experiments_round7_*`, `co2_experiments_round8_*`). Fitting an
offset and trend inside each period, so no straight line spans the ten-month
gap, moves the out-of-sample error by at most 0.06 ppm and leaves both towers
worse than their background. Scaling the CT-NRT fire term instead of holding it
fixed improves the background at Jambi by 0.44 ppm and fits a fire multiplier of
0.55 (0.20 to 1.21): the fire prior is about twice too strong in the 2024 fire
season, where it reaches 7.7 ppm at a Jambi receptor against nothing in 2023.

Report `BKT_JMB_CO2_Report` written from these tables
(`docs/BKT_JMB_CO2_Report_template.md`, `scripts/a95_bkt_jmb_co2_report.py`,
`scripts/a94_co2_figures.py` figures C01 to C05,
`scripts/validate_bkt_jmb_co2_report.py` with 66 checks, LaTeX entry and a
`verify_all.sh` gate). It states the negative result. Not committed.
