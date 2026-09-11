# BKT methane inversion execution plan

## Scientific contract

Question: which broad regional methane emission adjustments are supported by
the BKT observation series, conditional on transport, background and source
assumptions? Estimate low-dimensional regional multipliers, not an independent
emission for every grid cell or economic sector. Preserve the existing forward
source-influence case and integrate inversion methods, results and limitations
into the same canonical scientific Markdown/LaTeX/PDF report.

Initial experiment: 9 September through 6 October 2019 (28 days), receptor
hours 06 and 18 UTC, chosen before inspecting concentration outcomes. These
sample contrasting daytime/nighttime mountain conditions. Flagged/missing
measurements are unavailable, not zeros. Base transport: GFS 0.25 degrees,
120-hour backward integrations, 500 particles initially with convergence tests,
30 m AGL, 0.25-degree accumulation over a wider 48 by 36 degree regional grid.
Use representative 72/168-hour, height and particle/seed sensitivities; revise
scope only with recorded scientific reasons. Preserve particle endpoints for
boundary sampling. Inspect outer-grid and meteorological-domain losses.

Withhold every fourth day as contiguous full-day evaluation blocks, fixed
before fitting. Assess correlated errors and do not call neighboring hours
independent. Compare with unadjusted inventory and background-only models.
Synthetic recovery tests must include perturbed background and transport, not
only identical-model perfect recovery. Aggregate unidentifiable components.
Null results and prior-dominated estimates are valid outputs.

## Inputs and assumptions

Acquire minimum GFS archive crops, three-dimensional NOAA CarbonTracker-CH4
background fields, a documented wetland inventory, and daily fire methane.
Reuse EDGAR 2019 monthly files and established Indonesian/foreign boundaries.
Check absolute observational consistency against co-located NOAA flask data
where available. Record input versions, units, coordinates, times, QC, domain,
checksums and licensing. Audit whether the global background assimilates BKT.

If an input is inaccessible, use a traceable literature-based approximation
only where scientifically defensible, label it as an assumption rather than
observed data, and test plausible alternatives. Instrument calibration records
cannot be fabricated or replaced by another site's published precision.
Do not hide a missing source class by assigning its flux to zero or force a
concentration budget to close. Check inventory fire/agriculture overlap.

## Stages and acceptance

- [x] Inspect existing workflow, observations, source access and scientific references.
- [x] Acquire/audit inputs and benchmark endpoint-enabled model integration (35 GFS and 35 CT daily files verified; natural/fire inputs acquired; endpoint and first higher-particle benchmark passed).
- [x] Complete multi-week footprints and transport/convergence diagnostics (52 base receptors; 14 sensitivity experiments).
- [x] Build unit-checked prior source contributions and boundary concentrations.
- [x] Complete recoverability, posterior inference, held-out and sensitivity tests.
- [x] Integrate results, equations, captions, sources and uncertainty in the existing report.
- [x] Verify scientific calculations, all repository gates and every rendered final page (183 numerical/provenance checks, 38 regression tests, four repository gates, and all 44 physical pages of the exact final PDF; see `BKT_METHANE_INVERSION_QA.md`).

### Transport eligibility audit

Endpoint ASCII dumps retain inactive particles with PGRD=0 and placeholder
coordinates (0,0). These are not valid geographical endpoints. The operator
filters PGRD>0 before background interpolation and computes survival against
the actual emitted count, not the number of ASCII rows. A focused regression
test prevents placeholder reuse. The predeclared 95% survival screen remains
unchanged and is independent of concentration residuals. Report every excluded
receptor and its retention. If fewer than 20 fitting or six withheld hours
survive, expand meteorological coverage before fitting rather than relaxing the
screen. Retention-based sampling may favor particular circulation regimes;
the report must not claim the resulting sample represents all hours uniformly.

All 35 CarbonTracker daily files are acquired and verified. Natural-source
inputs include a documented processed MeMo field; its integrated climatological
sink is approximately 33.63 Tg/year, consistent with its published magnitude.
The GEOS-Chem conversion explicitly corrects the original supplemental carbon/
methane-unit labeling. Geological sensitivity additionally reverses the
provider's 37.5-to-1.6 Tg/year scaling, not merely a factor-two auxiliary test.

Resource budget: available 52 GiB memory and 1.6 TiB storage. Use four base
model workers plus two sensitivity workers, with a bounded four-worker auxiliary
pool for ready late-period receptors (at most ten of 16 local CPUs), two concurrent provider extraction jobs, resumable local runs
and an initial small test. Estimate full runtime from the live benchmark before
scaling. No publication, upload, commit, raw-data deletion or unrelated edits.

The auxiliary pool uses separate directories and atomically links completed
identical-configuration runs into the base tree only if its receptor has not
started there. Concurrent results never overwrite one another; any duplicate
is preserved and the original base directory remains authoritative.

## Report and chart contract

Audience: technical/scientific. The requested existing Markdown/PDF surface
overrides analytics plugin defaults; no parallel web report. Summary, scope,
definitions, dedicated inversion methods, evidence-led results, robustness,
limitations and next research questions supply the technical-report roles.

Plan complementary figures, populated only by verified outputs: observation
coverage/time series; regional prior and footprint-support maps; background and
prior components; source-response correlation/information matrices; synthetic
recovery intervals; prior/posterior emission intervals; held-out predictions
and residuals; sensitivity forest plots; posterior spatial adjustments with
unconstrained areas distinguished. Every visual gets adjacent interpretation.
Use the established blue/orange scientific style, explicit units and uncertainty,
semantic chemical labels, 300 dpi PNG and PDF exports. Indonesia uses the shared
38-province GeoJSON unchanged; foreign boundaries retain detailed geoBoundaries.
No map implies facility attribution or spatial detail unsupported by inversion.

Final handoff: inspect every full-size page of the final rebuilt PDF, including
all table continuations/captions, headings, equations, figure labels and page
transitions. Record per-page review and final PDF checksum. Machine gates and
thumbnail sheets do not substitute for this review.

## Completed inference and interpretation

All 52 observation-valid receptors have complete operators. The unchanged 95%
endpoint-retention screen excludes 25, leaving 21 fitting and six withheld
hours. Four MCMC chains pass the specified diagnostic thresholds (maximum
R-hat 1.0014; minimum ESS 5,727). Anthropogenic posterior median multipliers
are 0.58 within 500 km and 0.51 farther away; all four source intervals include
unity. Withheld RMSE is 47.6 ppb, versus 86.0 ppb for background-adjusted
inventories and 40.0 ppb for the fitted background-only baseline. Therefore
the experiment does not establish incremental skill over that simpler
baseline or verified regional emission corrections. Weekly test counts are
3, 14, 9 and 1; the last is only a single-error diagnostic.

All 19 assumption scenarios, four buffered weekly exclusions and 400 synthetic
realizations are retained. Conditional sector/region masses and the fraction
of prior emissions within the 90% transport-support mask are calculated.
The independent numerical/provenance validator passes 183 checks. The
scientific regression suite passes 38 tests. All four repository gates pass.
Every physical page (1–44) of the final PDF was rendered and visually reviewed
at readable scale after the final layout changes. The final checksum and
review coverage are recorded in `BKT_METHANE_INVERSION_QA.md`.

The raw S141 decoder retains subprecision residuals; three native PBL-height
diagnostics are slightly negative, all smaller in magnitude than their record's
packing precision. NOAA's profile utility reports zero for the independently
checked 21 September 18 UTC case. These are not physical negative mixing
heights. Two occur among eligible receptors and are omitted only from the
height-scatter diagnostic, with raw values and flags preserved in CSV. The
concentration inversion is unchanged and does not use these PBL diagnostics.

## Pre-fit specification and input audit

Before any posterior fit: use four positive lognormal source multipliers for
anthropogenic emissions within 500 km geodesic distance of BKT, anthropogenic
emissions farther away within the model domain, wetlands and non-crop fires.
All have prior log mean zero and log SD ln(2). A multiplier of one is the prior
median, not its mean. Two Gaussian background terms have SDs 20 ppb (offset)
and 10 ppb per 28 days (trend). This is a deliberately small, exploratory
state, not province- or facility-specific emission retrieval.

Working mismatch covariance: independent 5 ppb measurement/calibration
allowance plus 20/40 ppb day/night representativeness terms; 50% of the prior
source enhancement with a 24-hour exponential transport correlation; 10 ppb
background variability with a 72-hour correlation. These are explicit working
assumptions, informed by the scale and structure of published methane inversions,
not measured BKT uncertainties. Test alternative strengths. Fixed termite,
geological and soil terms receive an additional 100% combined-magnitude
uncertainty allowance. Persistent offset/trend are fitted separately.

Observation audit CSV: 619 available/valid hourly records of 672 expected,
52 retained of 56 scheduled receptor hours, 39 fit and 13 fixed holdout hours.
Four contemporaneous NOAA flask pairs agree closely; these are not enough to
characterize all instrumental errors. No model-disagreement observation filter.
Exclude simulations with fewer than 95% of emitted particles surviving to the
saved endpoint; disclose counts and test sensitivity to this threshold.

NASA's original LPJ-wsl HTTP transfer repeatedly truncated and did not support
resumption. Use the accessible, source-documented GEOS-Chem LPJ-MERRA2/LPJ-EOSIM
2019 monthly field instead (East et al. 2024), retaining provenance. MeMo soil
uptake and CAMS termite climatologies are explicitly climatological assumptions;
the scaled geological field is static. Do not claim a complete natural methane
budget: lakes/reservoirs and ocean exchange are not individually constrained.

GFED crop methane is reconstructed from its own crop-carbon partition and
provider emission-factor table, then removed from daily total-fire methane.
The monthly crop fraction is applied to each cell's total-fire daily profile;
test retaining the overlap as an alternate scenario. This preserves EDGAR
agricultural burning and avoids intentional double counting in the base case.

CT-CH4-2025 documentation Table 4 confirms daytime BKT flask and in-situ
assimilation. Therefore the background is not fully independent of BKT and the
held-out local-hour evaluation is conditional. Do not describe it as independent
network validation. Endpoint background is sampled equally over particles,
not weighted by the accumulated FOOT mass diagnostic. Convert endpoint AGL to
MSL using the decoded GFS terrain and sample CT layer-center heights.

After benchmarking two full 120-hour integrations at about 6.5 minutes each,
start two additional sensitivity workers within local CPU/memory capacity.
Preselected sensitivity anchors: 9 Sep 06 UTC, 16 Sep 18 UTC, 23 Sep 06 UTC,
30 Sep 18 UTC. All four test a second seed and 60 m height. The two daytime
anchors also test 2,000 requested particles and 72/168-hour windows. These
tests diagnose sampled numerical/transport sensitivity; they do not establish
convergence or accuracy of every receptor hour.
