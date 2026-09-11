# Reproduce the BKT domain and prior-budget extension

This companion covers the 52-receptor widened-domain correction and the
five-receptor domain/duration methane-budget matrix. It generates forward
transport and prior-budget diagnostics only. It does not call the methane
inversion fitter, update posterior parameters, or replace the existing
inversion operator.

## Environment and execution order

```bash
export BKT_PYTHON=/run/media/workstation-llm/HDD2/.venv/bin/python

"$BKT_PYTHON" scripts/a71_domain_budget_extension.py fetch-met
"$BKT_PYTHON" scripts/a71_domain_budget_extension.py fetch-flux
"$BKT_PYTHON" scripts/a71_domain_budget_extension.py prepare-flux
"$BKT_PYTHON" scripts/a71_domain_budget_extension.py run-full
"$BKT_PYTHON" scripts/a71_domain_budget_extension.py run-convergence
"$BKT_PYTHON" scripts/a71_domain_budget_extension.py analyze-full
"$BKT_PYTHON" scripts/a71_domain_budget_extension.py analyze-convergence
"$BKT_PYTHON" scripts/a72_domain_budget_figures.py
"$BKT_PYTHON" scripts/a72_domain_budget_figures.py --lang id
"$BKT_PYTHON" scripts/a45_bkt_gfs_report.py
"$BKT_PYTHON" scripts/validate_domain_budget_extension.py
"$BKT_PYTHON" -m unittest tests.test_bkt_domain_budget_extension
"$BKT_PYTHON" scripts/a14_latex.py BKT_HYSPLIT_STILT_Footprint_Report
```

The acquisition stage uses no more than two simultaneous NOAA extraction
requests. Forward runs use at most four workers. Each stage is restartable:
completed model outputs are reused only after configuration, meteorology paths
and output checksums reconcile. Partial runs are preserved for diagnosis and
are not overwritten silently.

## Frozen design

- The full ensemble contains the 52 available receptor hours in the existing
  twice-daily 9 September–6 October 2019 schedule.
- Original retention is defined before rerunning as at least 95% of actual
  emitted particles at the five-day endpoint.
- The widened meteorological crop is 50°–160° E and 40° S–30° N. Its output
  grid is 60° latitude by 100° longitude, centered on BKT at 0.25° spacing.
- Representative receptors are 13 September 06:00, 14 September 18:00,
  23 September 06:00, 24 September 18:00, and 6 October 06:00 UTC. Both domains
  are evaluated at 72, 120, and 168 hours.
- The representative cases were frozen using original retention, WIB clock
  period and model 10 m wind quadrant. Gas residuals and convergence results
  did not select cases or settings.

## Calculation contracts

Footprint coefficients are normalized by the actual emitted-particle count,
not the requested particle count or surviving endpoint count. The active
endpoint fraction is an independent completeness diagnostic.

For each reported variable, the full-ensemble change is

```text
wide_all - original_retained
  = (wide_retained - original_retained)
  + (wide_all - wide_retained).
```

The first term is a paired configuration change. The second is recovered-hour
sample composition. Intervals use 5,000 circular three-day block resamples of
receptor dates with seed 20260909.

The methane surface term adds EDGAR anthropogenic, wetland, termite,
geological, and non-crop-fire contributions and subtracts the positive soil
uptake magnitude. Cropland fire is removed from the GFED all-fire term to avoid
overlap with monthly agricultural methane. The endpoint background is the
equal-particle mean of CarbonTracker-CH4 sampled at the terminal active
particle locations and heights above dynamically read GFS terrain. Surface,
background, and their sum are retained separately because cancellation in the
sum is not convergence of both components.

## Provenance and outputs

Acquisition and run receipts are under
`outputs/hysplit/domain_budget_extension/receipts/`; each includes source paths,
bounds or run configuration, byte counts where applicable, and SHA-256 values.
Prepared source grids, model runs, CSV evidence tables, figures, and validation
records remain in separate subdirectories below the same extension root.

`full_receptor_budget.csv` is the row-level basis for full-ensemble claims.
`design_contract.csv` records the fixed dates, domains, durations, particle
request, retention threshold, and block-resampling settings cited in prose.
`full_domain_decomposition.csv`, `observed_sample_difference.csv`, and
`selection_strata.csv` contain the selection analysis. `convergence_matrix.csv`
and `convergence_changes.csv` retain every representative scenario and
duration increment. The independent validator re-computes particle fractions,
decomposition identities, observed-group differences, and surface-plus-
background closure from those lower-level records.

## Interpretation limits

The wider meteorology is a separately packed extraction, so the matched result
is the effect of the complete correction configuration rather than a purely
geometric domain derivative. CarbonTracker-CH4 assimilates BKT observations
and is not independent validation. Flux fields are prior inventories or model
products. The representative matrix is small and purposively stratified.
Therefore the outputs diagnose truncation, sample selection, and numerical
stability; they do not identify source emissions, validate atmospheric
accuracy, establish seasonal behavior, or support an inversion refit.
