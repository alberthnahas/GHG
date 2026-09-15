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
