# BKT footprint revision: numerical stability and continuous mapping

## Authorized scope and fixed evidence

Redo the 2019-09-26 01:00 UTC, 72-hour BKT case, analysis and comprehensive
report. Preserve the original pilot as a comparison. Use the established
HDD2 `.assets/indonesia_38prov.geojson` for every Indonesian map boundary.
Retain verified GDAS1 meteorology to isolate particle/grid effects; its 1-degree
terrain and meteorological limitations remain. No flux attribution is implied.

## Experiments and acceptance criteria

- [x] Rerun 2,000 and 10,000 particles at 0.1 degrees; repeat 10,000 with
  three fixed distinct seeds, and a paired 0.25-degree grid test.
- [x] Test 60 m AGL as a receptor-height sensitivity, retaining 30 m as the
  observed inlet. This is a structural sensitivity, not another observation.
- [x] Confirm emitted particle count, runtime, seeds, settings, complete
  hourly fields, finite nonnegative values, checksums and grid reconciliation.
- [x] Diagnose requested-count normalization using paired 6-hour runs requesting
  500 and 540 particles (both emit 540). Retain native outputs and apply the
  empirically verified requested/actual factor in derived analysis and maps.
- [x] Average three independent realizations for the revised central field.
  Report seed ranges separately from height, grid and particle-count effects.
- [x] Select a fixed Gaussian display bandwidth using leave-one-seed-out
  quadratic risk. Preserve raw hourly sensitivities for analysis/convolution;
  report bandwidth sensitivity and mass conservation explicitly.
- [x] Render smooth continuous surfaces using the user-approved GeoJSON,
  including validation of geometry, coordinates and content checksum.
- [x] Regenerate analysis, source tables, comparison charts and canonical
  Markdown/LaTeX/PDF with numerical and visual QA and all repository gates.

## Scientific basis and limitations

NOAA documents ICHEM=8, mass-consistent STILT dispersion and seed control.
Fasoli et al. (2018), doi:10.5194/gmd-11-2813-2018, demonstrates Gaussian
particle-kernel estimation and warns that excessive smoothing removes modeled
structure. Here a fixed-bandwidth gridded display reconstruction is tested;
it is not the paper's adaptive per-particle estimator. Smoothing cannot provide
meteorological detail absent from GDAS1. Seed spread quantifies only numerical
sampling variability conditional on this meteorology and configuration.

## Progress

2026-09-05: Located the exact provincial GeoJSON and verified original model
configuration. Runtime overrides CMASS to 1 in STILT mode; make that setting
explicit in new runs. Original pilot retained at its existing run directory.

The 2,000-requested-particle run completed and passed numerical validation.
All five larger runs also completed. A six-hour output-diagnostic test produced
bitwise-identical gridded fields with IVMAX=0. One interrupted height attempt
is preserved separately and excluded; its replacement uses this verified
output-only option. Native arrays are retained and corrected analysis is
written separately. Native count rounding is now explicitly audited.

Final evidence: six complete 72-hour reruns, three six-hour controls, 11 unit
tests, 30 independently reconstructed ensemble cell-hours, and four repository
gates passed. The 18-page PDF contains seven figures and seven tables; all pages
were rendered and inspected, with detailed equation/map checks. No overfull
boxes, missing glyphs or stray table headers remain. Display integral
11.363546492091363 matches raw ensemble total 11.36354649209136.

Cross-seed selection favored zero Gaussian bandwidth. This null result is
retained: the final map uses a finer-grid ensemble, linear display interpolation
and continuous contours, not arbitrary extra blur. Southeast beyond 25 km is
69.4% (seed range 69.3–69.6%); these are conditional numerical results.

Follow-up read-only feasibility check: NOAA's public GFS quarter-degree archive
lists all four daily files for 23–26 September 2019, each 2,898,905,680 bytes
(11.596 GB total). The archive uses 3-hour output and hybrid vertical levels.
No finer-meteorology download or simulation was started in response to the
user's question about available options; GFS 0.25 degrees is the direct next
comparison, with nested WRF a separate higher-resolution research stage.
