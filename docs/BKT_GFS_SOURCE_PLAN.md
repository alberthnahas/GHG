# BKT GFS meteorology and source-influence extension

## Scope and acceptance

Keep the 26 September 2019 01:00 UTC receptor, 72-hour window, observed
30 m AGL inlet and unsmoothed 0.1-degree analysis grid. Compare three GFS
0.25-degree seeded runs with the existing GDAS1 ensemble; test release height
separately. Preserve previous model outputs and report versions.

Acquire the four NOAA GFS daily ARL files, verify remote checksums where
available, local SHA-256, headers, complete temporal coverage and variables.
Use the same validated particle-count correction and avoid conflating changes
in meteorological model, vertical coordinates and resolution with resolution
alone. Budget roughly 12 GB for meteorology plus bounded inventory subsets;
use at most four local model workers after a successful short test. Live
resource inspection found 16 CPUs and 52 GiB available memory; the independent
height scenario can run alongside the three seeds without resource pressure.

Investigate 2019 EDGAR CO2/CH4 anthropogenic fluxes and sector information,
GFED fire emissions with daily scaling if accessible, and suitable geographical
source context. Convolve only compatible surface-flux fields; explicitly label
monthly-average and surface-release assumptions, omitted fluxes/background,
inventory overlap and any unavailable data. Never infer facility responsibility
or complete source attribution from geographical overlap. Raw observations
remain immutable and are read through the harmonized station loader.

## Report and visual contract

Technical audience; continue the established canonical Markdown/LaTeX/PDF
scientific report rather than introducing a parallel app or HTML delivery.
Organize the report around scientific findings, methods, interpretation and
uncertainty. Keep development chronology, local repairs and figure revision
history in separate technical records. Report emitted-count normalization as
a method, and GFS/GDAS differences as a meteorological sensitivity experiment.
Technical summary, scope/definitions, model design, results, limitations,
recommendations and open questions map to the technical report skill roles.

Planned evidence: GFS footprint map; matched GFS/GDAS maps and distribution comparison;
lag/distance cumulative curves; seed and height comparisons; inventory maps;
source-weighted influence maps; gas/sector and province rankings; observation
context and source-data coverage/assumption tables. Add only plots supported
by real evidence. Use common scales for matched maps, explicit log units,
zero-origin magnitude bars, blue/orange comparison lines with distinct styles,
and publication-sized static PNG/PDF exports. Captions and adjacent prose
state period, units, method and interpretation boundary.

Indonesia always uses the established provincial GeoJSON. Inspect the shared
world-without-Indonesia asset for improved neighboring-country geometry;
otherwise obtain a documented high-resolution boundary product. Do not edit
shared assets. Record source, geometry repair, CRS and checksums.

## Validation and progress

- [x] GFS acquisition, integrity and coverage checks
- [x] Short model test and full ensemble/height runs
- [x] Compatible source data acquired, checked and conservatively matched
- [x] Independent convolution/unit checks and numerical/structural sensitivity
- [x] High-resolution maps, expanded report, complete rendering QA
- [x] Focused tests and all four repository gates

2026-09-05: inspected prior outputs, repository changes, station data traps,
shared assets and scientific skills. Previous report and raw runs remain valid
historical comparison products. Emission-source evidence availability is under
investigation; no complete concentration closure is promised in advance.

2026-09-05 14:06 WIB: regional GFS acquisition and all four header/record audits
passed; the short HYSPLIT integration passed. Four full runs are active (three
seeds plus release-height scenario). All sixteen EDGAR sector-year inputs and
the three-gas, four-day GFED regional subset are acquired; source coordinates,
units and nonnegative/finite coverage passed checks. Seventeen focused tests
passed. Scientific narrative and separate technical companion are drafted;
the scientific-report skill now explicitly excludes development chronology.
Final source calculations, report expansion, rendering and repository gates
remain pending completion of the model runs.

2026-09-05 final verification: all four full GFS runs and source calculations
completed. The scientific report contains 26 A4 pages, 12 figures and 9 tables;
all pages were rendered and visually reviewed. The printed page 9 Results
heading now shares its page with the subsection, findings and Table 3; a
regression check protects this layout. Twenty focused unit tests and 133
dedicated numerical/report checks passed. The final uninterrupted repository
verification returned four gates passed, zero failed, including zero overfull
boxes and zero stray table headers. No scientific arrays were changed by the
pagination fix.

The GFS ensemble has 60.3% of its bounded-domain sensitivity southeast of BKT
beyond 25 km. EDGAR/GFS surface-release-equivalent enhancements are 1.045 ppm
CO2 and 48.46 ppb CH4; these are not measured source attribution. GFED/GFS
fire CO is 95.8% of observed total CO, while the GDAS fire-only estimate exceeds
observed total CO, an important unresolved budget constraint. The GFS field
reaches the eastern output boundary: its 0.026% outer-cell sensitivity is not
a bound on omitted influence farther east. Background, ecosystem fluxes and
outside-domain influence remain unresolved. The report states these limits;
no complete concentration closure or operational validation is claimed.
