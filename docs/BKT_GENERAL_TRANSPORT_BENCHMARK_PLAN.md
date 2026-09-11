# General HYSPLIT-STILT transport benchmark

Status: complete for the bounded benchmark, 6 September 2026. Domain,
mixing/receptor, convection and observation-based evaluation were executed.
No baseline configuration was replaced and no emission inversion was rerun.
Atmospheric superiority remains unestablished; see
`BKT_TRANSPORT_BENCHMARK_QA.md` and the reproducibility companion.

## Execution checkpoint

- Baseline endpoint inventory and an hourly-dump severe-loss rerun are complete.
  The rerun reproduces the original footprint exactly; additional diagnostics
  did not alter the transport. Last-active locations and the model warning
  support eastern meteorological-boundary loss, not disappearance at zero
  latitude/longitude (those are inactive-record placeholders).
- Four frozen three-day controls are complete and all retain their particles.
  Their first three days reproduce the corresponding original five-day runs
  exactly. The original additional two days contribute materially, so the
  shorter duration is a bounded sensitivity experiment, not a replacement.
- Six one-factor perturbations across the same four anchors are complete.
  No concentration data selected scenarios or settings.
- Expanded same-resolution meteorology and both domain contrasts are complete.
  All 16,704 shared meteorological fields agree within packing precision, not
  bit identity. Expanded meteorology restores severe-case retention to 100%;
  the wider output grid captures additional sensitivity while preserving
  shared cell-hour coefficients exactly. Five-day temporal convergence is
  not established.
- NOAA IGRA acquisition and parsing are complete. Pressure-matched forcing
  comparisons are complete with nearest-cell, historical-position and plus/
  minus one-hour sampling sensitivities. Pekanbaru's pressure-level support is
  too sparse for a second validation claim. Padang provides the principal check.
  Temperature and wind have different valid sample counts; retain both.
- Fixed-site mixing-depth diagnostics are complete using the installed
  diagnostic executable. Its default turbulence time scales differ from the
  footprint run; use its mixing-depth series as a diagnostic, not a second
  full-physics simulation or observational truth.
- The integrated report, comparative QA and all-page final rendered review
  are complete. All four repository gates passed.
- Two additional control-seed replicates at every frozen anchor are complete.
  This numerical control was declared before the full perturbation results
  were complete. Its sampling variation is reported alongside the physics
  contrasts; it does not select a setting or supply confidence intervals for
  every perturbation.

## Scientific question and scope

Which correctable numerical, domain and subgrid-representation limitations
affect the passive surface-flux transport operator at Bukit Kototabang (BKT),
and which proposed changes have observational support? Improved numerical
completeness is distinct from improved atmospheric accuracy. Do not optimize
transport against methane residuals or rerun the methane inversion here.

Use the existing September–October 2019 experiment as a controlled benchmark,
not a climatology. Keep raw observations, previous runs and report findings
intact. Use public existing meteorology; no WRF simulation, cloud upload,
provider message, commit or destructive cleanup. Store new runs separately in
`outputs/hysplit/benchmark/`. Retain acquisition provenance and exact executed
settings. Existing scripts and tests are the reproducibility interface; a new
notebook would duplicate the maintained workflow.

## Execution and acceptance criteria

1. Domain completeness: reconcile emitted, active and inactive particles for
   all baseline receptor hours. Inspect model messages and sample trajectories
   before attributing losses. Select diagnostic anchors on transport evidence,
   never gas residuals. Test an expanded same-resolution GFS crop on a severe
   loss case; compare shared-domain meteorological values and footprint totals.
   Retain at least 95% of emitted particles at the backward endpoint as the
   existing operational screening threshold, not proof of domain convergence.
   Check the remaining edge and oldest-time sensitivity. Distinguish output
   grid truncation, meteorological boundary exits and other terminations.
2. Mixing/receptor: retain the original setup as control; expose explicit,
   validated options without changing default behavior. Test bounded lower
   mixing-depth limits, model-native versus diagnosed mixing depth where
   supported, and receptor heights. Use matched times, winds, particle counts,
   seeds and grids; report assumptions and actual emitted-count normalization.
   Evaluate daytime/nighttime separately. No setting is selected just because
   it fits gas concentration better.
3. Convection: verify input-field compatibility and executed model behavior.
   Compare the current requested Grell option with disabled convection, then
   a supported CAPE-based sensitivity only after checking backward-mode
   compatibility. Clearly distinguish unresolved convection from absent
   convection. Preserve diagnostics and report a null response if present.
4. Independent evaluation: discover local observations first, then acquire
   the minimum relevant public radiosonde records if needed. Verify station
   history, time basis, units, vertical support and quality flags. Match at
   the observation site/time, not by treating a coastal sounding as a BKT
   mountain profile. Compare wind components and temperature on common levels,
   summarize by sounding (not independent levels), and use date-blocked
   uncertainty where sample support permits. Soundings potentially assimilated
   by GFS are observational checks independent of this benchmark's tuning, not
   demonstrably assimilation-independent validation. If local turbulence,
   mixing-depth or tracer-release data are absent, state exactly what remains
   unvalidated; do not substitute gas fit for transport truth.

Start with small diagnostic runs. Bound concurrent model runs to at most four
and downloads to two; estimate scaling from measured runtime before expansion.
Preserve every completed scenario and failure. Freeze the scenario list before
comparative results are examined. If a material design change is necessary,
record the reason and distinguish exploratory additions from planned tests.

## Deliverable and validation contract

Chart map (static Matplotlib embedded in the existing scientific LaTeX PDF;
the established domain-specific report contract takes precedence over generic
inline-widget/HTML defaults and generic neutral-title guidance):

| Figure | Question and family | Evidence and encoding | QA target |
|---|---|---|---|
| Domain completeness | Lag evolution; two aligned line panels | Hourly retention and cumulative normalized sensitivity; original versus wider met/output domains; blue/orange/neutral with distinct line styles | Vector PDF and 300 dpi PNG at A4 report width, then exact integrated PDF |
| Physics sensitivity | Matched comparisons; dot plot | Ratio to same-time control for six perturbations, with four identified receptor times and separate seed-repeat context; blue/orange plus marker shape | Exact report-size labels, reference at one, no implied confidence intervals |
| Profile evaluation | Pressure profiles; two aligned diagnostic panels | Wind-vector RMSE and temperature bias at five measured standard levels; paired sample counts in tables; blue plus neutral zero reference | No fabricated vertical observations; readable pressure ticks and units |

Plots use the scientific-chart-standard finding/highlight hierarchy, bounded
scientific claims, and no decorative branding. Data-analytics visualization
guidance supplies chart contracts and final-context QA, not a replacement app.

Integrate the benchmark findings into the existing scientific Markdown/PDF
report, preserving earlier sections. Technical summary, scope/definitions,
experimental design, evidence, robustness, limitations and remaining questions
are covered by the integrated section and technical reproducibility document.
The user's established scientific report workflow supersedes generic analytics
MCP/HTML/Sites defaults; no separate analytical app is requested.

Validate input/output metadata, normalization, termination accounting and
numerical invariants; independently spot-check key calculations. Add focused
tests for changed behavior, run `scripts/verify_all.sh`, review the diff, and
visually inspect every page of the exact final PDF. Mechanical success cannot
establish improved atmospheric transport or resolve missing observational
constraints. Record both scientific and software/visual QA outcomes.

## Instruction audit

The root `AGENTS.md` and the user's replacement instructions were read. No
additional instruction files were found in scripts/docs/tests. The referenced
`.claude/skills/ghg-analysis/` directory is absent; the available instructions
control. The checkout is a dirty Git repository despite older documentation.
Unrelated changes, including the OCO analysis, are outside this task.
