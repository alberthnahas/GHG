# BKT general transport benchmark: final QA

Reviewed on 6 September 2026. The bounded benchmark is complete; this is not
certification of atmospheric transport accuracy or operational readiness.

## Exact delivered report

- File: `outputs/BKT_HYSPLIT_STILT_Footprint_Report.pdf`
- SHA-256: `b5890be48bc85e8fd31b78574d90dfcfc24b373b5980a31e00c780a462e9c429`
- Size: 27,522,252 bytes; 53 physical A4 pages; 25 figures and 20 tables.
- Every physical page, 1–53, was rendered with Poppler at 130 dpi and visually
  inspected individually. Text, equations, tables, figures, captions, legends
  and pagination were checked. No clipping or overlapping content remained.
- Final Figure 24 explicitly labels the 18 UTC receptors as 10/24 September
  at 01:00 WIB. The earlier visual review caught the calendar rollover error;
  only presentation labels were wrong, not simulated UTC times. A regression
  test now covers the conversion. The corrected rebuild was reviewed in full.
- Scientific-report and scientific-chart skills shaped the integrated appendix,
  finding/highlight figures and separation of sensitivity from validated skill;
  the PDF skill required review of the exact final build.

## Software and numerical verification

- The four focused footprint/refinement/GFS/transport test modules passed:
  29 tests, including default preservation, input guards, ARL unpacking,
  pressure interpolation, IGRA missing values and WIB calendar conversion.
- Benchmark validation passed 1,193 checks, including run receipts, particle
  accounting, normalization, source provenance, independent RMSE arithmetic,
  coefficient-level comparisons and report/figure evidence checks.
- All four repository gates passed in the final calendar-corrected rebuild:
  document consistency, figure translations, PDF compilation/layout and deck
  rendering. Final execution log: `/tmp/bkt-benchmark-calendar-final-gates.log`.
  Existing decks were mechanically checked at 58, 23 and 20 slides; they were
  not part of this report's manual page review.
- Native pressure-profile decoding was compared with 275 values from the
  installed NOAA profile utility within packing/display tolerances.
- All 16,704 common-domain meteorological fields passed the sum-of-packing-
  increments tolerance. Repacking is explicitly disclosed, not called exact.
- The hourly-dump baseline rerun reproduced the original footprint exactly;
  four 72-hour controls reproduced the first 72 hours of the original runs.
  Expanded-output shared cell-hour coefficients were identical.

## Separate scientific reasoning review

Tables 18–20, Figures 23–25 and their prose were reconciled to benchmark CSVs.
Particle retention was independently checked as 93/540 = 17.22% versus
540/540 = 100%. Wider-output sensitivity outside the old grid is 10.51%;
the oldest 24 hours supply 14.7%, preventing a temporal-convergence claim.
The severe-case diagnosis is not generalized to all 25 failed receptors.

Mixing-floor, receptor-height and native-mixing responses were compared with
unchanged-physics seed repeats. The larger nighttime floor responses exceed
the observed seed variation but are not a significance test or validation.
The fixed-site mixing diagnostic is not a measured BKT boundary-layer height.
Both convection contrasts were null at the coefficient level; missing Grell
inputs and unrecorded CAPE activation prevent an atmospheric absence claim.

The Padang wind-vector RMSE is 2.77 m/s (three-day-block 95% interval
2.17–3.56), based on 59 wind soundings over the study period. Complete-profile
restriction lowers it to 2.26 m/s; the influential wind-only sounding remains
in the primary result. Sampling and historical-position alternatives, unequal
temperature coverage and sparse Pekanbaru support are disclosed. Possible GFS
assimilation, balloon drift and absent local BKT turbulence/tracer observations
prevent describing this as fully independent transport validation.

## Preserved scope and remaining evidence

No original observations were altered, no configuration was promoted, and no
inversion, commit, push or institutional-data upload was performed. Existing
unrelated dirty-worktree changes were preserved. Reproduction commands and
CSV provenance are in `BKT_TRANSPORT_BENCHMARK_REPRODUCIBILITY.md`.

Before revising an inversion: extend domain-completeness checks across the
full receptor ensemble, assess longer-duration tails, replicate perturbations
and obtain local wind/stability or boundary-layer observations with documented
assimilation independence. These are scientific follow-up requirements, not
claims that this bounded benchmark validated a replacement configuration.
