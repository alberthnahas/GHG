# General transport benchmark: reproducibility and interpretation

## Scope and decision

This is a gas-independent, passive HYSPLIT-STILT transport benchmark at Bukit
Kototabang, using the existing 2019 experiment. It does not refit emissions or
promote a replacement physics configuration. The original report and inversion
remain available in the integrated report; new material is the transport
appendix, Figures 23–25 and Tables 18–20.

The severe-loss test establishes a numerical domain problem and demonstrates
better coverage in one case. General atmospheric superiority remains
unestablished. The IGRA comparison is independent of benchmark tuning, but not
demonstrably independent of GFS assimilation. Neither coastal profiles nor
fixed-site model diagnostics validate local BKT mixing depth.

## Design and retained evidence

- Baseline inventory: 52 original five-day runs; no original run is overwritten.
- Domain experiment: 6 October 2019, 06:00 UTC, 120 hours backward. Original
  meteorology covers 75–130° E and 20° S–20° N; expanded meteorology covers
  50–160° E and 40° S–30° N at the same 0.25° resolution. Original output spans
  36° latitude by 48° longitude centered at BKT; expanded output spans 60° by
  100°, on the same receptor-centered grid. Check coordinates in NetCDF before
  interpreting grid-cell extents.
- Physics matrix: 9 and 23 September, 06:00 and 18:00 UTC; 72 hours backward;
  requested 500 particles, actual 540. Control plus six one-factor contrasts:
  minimum mixing depth 100/50 m, native mixing depth, 60 m receptor, convection
  disabled, CAPE threshold 500 J/kg. Baseline minimum is 250 m; receptor is
  30 m AGL; modified-Richardson-number depth is used. Existing defaults are
  unchanged.
- Numerical sampling: two extra control seeds (-10 and -20, following the
  established HYSPLIT convention) at every anchor. These are not uncertainty
  intervals for every perturbation. The full matrix is 39 runs, plus two
  six-hour probes. Full run matrices are `scenario_plan.csv` and
  `sampling_plan.csv` under `outputs/hysplit/benchmark/`.
- Observation check: IGRA 2.2 Padang and Pekanbaru records from 9 September
  through 6 October 2019 inclusive. Pressure matching at 925, 850, 700, 500 and
  300 hPa; no vertical extrapolation. Latest versus historical coordinates,
  nearest versus bilinear sampling, nominal time +/- one hour, complete-profile
  coverage and leave-one-sounding-out influence are retained as diagnostics.

## Run order

Run from the repository root. The existing scientific environment and HYSPLIT
installation are reused; no new environment or meteorological simulation
is required. Commands reuse completed runs only when configuration and output
checksums match. Do not run duplicate commands against the same scenario while
it is already active.

```bash
GHG_PYTHON=/run/media/workstation-llm/HDD2/.venv/bin/python
"$GHG_PYTHON" scripts/a64_transport_benchmark.py inventory
"$GHG_PYTHON" scripts/a64_transport_benchmark.py probe
"$GHG_PYTHON" scripts/a64_transport_benchmark.py loss_control
"$GHG_PYTHON" scripts/a64_transport_benchmark.py fetch_wide --workers 2
"$GHG_PYTHON" scripts/a66_transport_diagnostics.py audit_wide
"$GHG_PYTHON" scripts/a64_transport_benchmark.py loss_wide
"$GHG_PYTHON" scripts/a64_transport_benchmark.py loss_wide_output
"$GHG_PYTHON" scripts/a64_transport_benchmark.py probe_cape500
"$GHG_PYTHON" scripts/a64_transport_benchmark.py physics --workers 4
"$GHG_PYTHON" scripts/a64_transport_benchmark.py sampling --workers 4
"$GHG_PYTHON" scripts/a65_transport_observations.py fetch
"$GHG_PYTHON" scripts/a65_transport_observations.py parse
"$GHG_PYTHON" scripts/a67_transport_profile_evaluation.py
"$GHG_PYTHON" scripts/a68_transport_mixing_diagnostics.py --series
"$GHG_PYTHON" scripts/a66_transport_diagnostics.py native_profile
"$GHG_PYTHON" scripts/a66_transport_diagnostics.py ledger --scenario loss_control
"$GHG_PYTHON" scripts/a66_transport_diagnostics.py ledger --scenario loss_wide
"$GHG_PYTHON" scripts/a66_transport_diagnostics.py ledger --scenario loss_wide_output
"$GHG_PYTHON" scripts/a66_transport_diagnostics.py duration
"$GHG_PYTHON" scripts/a66_transport_diagnostics.py convection
"$GHG_PYTHON" scripts/a66_transport_diagnostics.py domain
"$GHG_PYTHON" scripts/a66_transport_diagnostics.py summary
"$GHG_PYTHON" scripts/a70_transport_benchmark_figures.py
"$GHG_PYTHON" scripts/a69_transport_benchmark_report.py
"$GHG_PYTHON" scripts/a45_bkt_gfs_report.py
"$GHG_PYTHON" scripts/validate_transport_benchmark.py
```

Full repository gates remain `bash scripts/verify_all.sh`. This workstation's
legacy gate tools use an existing compatibility launcher for system Python and
the bundled slide-rendering Python, plus the existing temporary PyMuPDF and
Tectonic cache locations. The verified invocation is:

```bash
env PATH=/tmp/ghg-python-bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    PYTHONPATH=/tmp/ghg-verify-deps XDG_CACHE_HOME=/tmp/ghg-tectonic-cache \
    GHG_SCIENTIFIC_PYTHON=/run/media/workstation-llm/HDD2/.venv/bin/python \
    bash scripts/verify_all.sh
```

Those temporary compatibility paths are environment-specific, not portable
scientific dependencies. Verify that they still exist before reuse; use the
repository's documented tool environment on another machine. No system or
shared-environment packages were changed during this benchmark.

## Important numerical definitions

- Native footprint coefficients divide by the requested particle count. As in
  the established workflow, analysis multiplies by requested/actual emitted
  count. Do not divide by the surviving endpoint count: this would renormalize
  away domain losses.
- Inactive `PGRD=0` records retain placeholder coordinates. Loss brackets use
  the last active and first inactive hourly records for each particle ID.
  Boundary distances are spherical great-circle distances, not degrees treated
  as distance. They locate the nearest edge, not an exact crossing point.
- Meteorological repacking changes some shared values. Every field is compared
  within the sum of its two packing increments; do not call the wider inputs
  bit-identical. The expanded-output-only contrast uses exactly the same wider
  meteorology and preserves shared footprint coefficients exactly.
- `bkt_arl.py` uses the archived pressure field for log-pressure interpolation.
  The leading pressure label printed by the NOAA profile utility differs from
  that field and is not substituted for it. Comparisons against the utility
  allow packing/display precision. Printed small winds and humidity near
  saturation can differ within that tolerance; scientific Celsius conversion
  uses 273.15 K.
- Error summaries average within sounding, then within date, then across
  dates. Three-day circular moving blocks preserve short-range weather
  dependence. Reported intervals do not include all model/measurement errors.
  Sparse Pekanbaru samples have no interval. The large wind-only mismatch is
  retained; it is not removed because the model disagrees.
- The fixed-site `vmixing` diagnostic uses forward positive duration and
  reports eight three-hourly samples per day. Its turbulence time-scale defaults
  differ from the footprint setup; it provides a mixing-depth diagnostic, not
  a second complete footprint simulation or observational truth.
- Executed namelists confirm requested CAPE thresholds. They do not record
  threshold activation. The absent Grell flux fields, null coefficient
  contrasts and explicitly disabled WRF-specific interpolation are retained
  in `convection_execution.csv` and original messages.

## Provenance and QA locations

Inputs are under `data/hysplit/gfs0p25/benchmark_wide/` and
`data/hysplit/benchmark_observations/`, with provider URLs, acquisition times,
byte counts and SHA-256 receipts. Original meteorology remains under
`data/hysplit/gfs0p25/regional/`. Each benchmark run retains control/namelist
files, messages, particle records, footprint fields, configuration metadata
and output checksums.

`outputs/hysplit/benchmark/tables/` contains baseline accounting, loss brackets,
meteorological overlap checks, normalized run summaries, physics contrasts,
duration sensitivity, observation matches, quality counts, profile metrics,
influence diagnostics and validation checks. Figure specifications are under
`outputs/hysplit/benchmark/figures/`. The integrated software manifest is
`outputs/hysplit/gfs/analysis/software_manifest.json`.

Final PDF checksum, reviewed page coverage, numerical spot checks and gate
results are recorded separately in `docs/BKT_TRANSPORT_BENCHMARK_QA.md`.
