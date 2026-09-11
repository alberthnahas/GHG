# BKT domain-correction and concentration-budget extension

Status: completed and accepted, 9 September 2026. This plan covers only the
full-ensemble domain correction and the representative duration/domain methane
budget experiment. It does not refit an inversion or select transport settings
from concentration residuals.

## Questions

1. Across every completed 120-hour BKT receptor run from 9 September through
   6 October 2019, how does the widened meteorological and footprint domain
   change particle retention and surface-flux sensitivity?
2. Did the original 95% retention screen preferentially retain particular
   model near-surface wind regimes, WIB clock periods, calendar months, or
   observed CO2, CH4 and CO concentrations?
3. For representative receptors, do the methane surface-flux contribution,
   CarbonTracker-CH4 endpoint background and their sum stabilize together as
   backward duration and domain increase?

September and early October are calendar subsets of one short 2019 period;
their contrast is not interpreted as a seasonal climatology. Wind regimes are
defined from GFS 10 m winds at the BKT grid cell and are model forcing, not a
station wind observation.

## Frozen design

- Full ensemble: the 52 completed receptor hours already inventoried in
  `baseline_completeness.csv`. The corrected run uses the same quarter-degree
  GFS product and baseline transport physics, a meteorological crop of
  50-160 degrees E and 40 degrees S-30 degrees N, and a 60 by 100 degree
  footprint grid. No gas value selects or excludes a corrected run.
- Selection groups: original endpoint retention at or above 95% versus the
  previously excluded group below 95%. Comparisons include the two scheduled
  WIB clock periods, September versus 1-6 October, GFS near-surface wind
  sector/regime, and harmonized quality-controlled CO2, CH4 and CO loaded via
  `ghg_common.load_station`.
- Decomposition: first compare original and corrected transport on the same
  originally retained hours; then compare corrected results on all 52 hours
  with corrected results on that fixed retained subset. The first step is a
  paired transport/domain change. The second is a recovered-hour sample-
  composition change. Three-day circular block resampling over receptor dates
  describes short-record sampling uncertainty without treating the 52 serial
  hours as independent.
- Representative budget receptors, declared before their concentration-budget
  results are inspected: 13 September 2019 at 06:00 UTC and 14 September at
  18:00 UTC (previously excluded day/night cases in different GFS wind
  quadrants); 23 September at 06:00 UTC and 24 September at 18:00 UTC
  (previously retained day/night cases in the other two wind quadrants); and
  the severe-loss 6 October 06:00 UTC anchor. Selection uses clock period,
  model wind quadrant and original transport retention, not gas concentration.
  This small diagnostic set is neither random nor seasonally representative.
- Convergence matrix: 72, 120 and 168 hours for both original and widened
  domains at each representative receptor. Track integrated sensitivity,
  component surface contributions, net prior surface contribution, equal-
  particle endpoint background, endpoint spread, retained particles and total
  prior modeled methane. Duration increments must report surface, background
  and total changes separately because component cancellation is not evidence
  of convergence.

## Inputs and provenance

Use verified existing global EDGAR v8.0 and natural methane inventories,
GFED5.1 daily/monthly data with a newly provenance-recorded wide subset where
needed, CarbonTracker-CH4 2025 daily three-dimensional fields, GFS ARL daily
files and HYSPLIT 5.4.2. Preserve raw observations and prior model runs. All
new model runs and analysis products go under
`outputs/hysplit/domain_budget_extension/`.

## Execution controls and acceptance

- At most two concurrent NOAA extraction requests and four model workers.
- Every acquired file must have recorded bounds, byte count and SHA-256; every
  model directory must have a completion receipt and output checksums.
- A completed wide run must reconcile emitted, active and inactive endpoint
  particles; sensitivity must be finite, nonnegative, chronologically complete
  and normalized by the actual emitted count.
- Source grids must completely cover each footprint grid and retain explicit
  units. Soil uptake is subtracted; cropland fire is not double-counted with
  monthly agriculture. Endpoint interpolation and vertical support flags are
  retained.
- Every quantitative report claim must trace to a generated CSV. Focused tests,
  independent arithmetic spot checks, the four project verification gates,
  `git diff --check`, and an all-page readable-scale review of the exact final
  PDF are required before completion.

## Scope boundaries

The experiment is prior-budget and transport sensitivity work, not a new
emission inversion, an independent-background audit, a new mixing factorial,
or an observational campaign. CarbonTracker assimilates BKT, the flux fields
are inventory/model products, and the representative matrix is small. Results
can diagnose numerical/sample dependence but cannot validate atmospheric
accuracy, independently identify emissions, or generalize seasonally.

## Completion record

- [x] Widened-domain 120-hour calculations completed for all 52 receptors.
- [x] Original/widened 72-, 120-, and 168-hour matrix completed for all five
  pre-declared representative receptors (30 scenarios).
- [x] Generated CSV evidence, bilingual figures, reproducibility guide, and
  report appendix integrated into the canonical Markdown and PDF.
- [x] Independent validator passed 392 checks; nine focused tests passed.
- [x] All four repository verification gates passed after the final layout
  changes; `git diff --check` passed without altering unrelated user work.
- [x] Exact 59-page final PDF visually reviewed at readable scale and recorded
  in `docs/BKT_DOMAIN_BUDGET_QA.md` with its SHA-256 checksum.
