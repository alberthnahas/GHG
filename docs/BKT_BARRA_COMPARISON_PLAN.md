# BKT BARRA-R2 transport feasibility and matched comparison

Status: bounded feasibility screen complete; direct ARL conversion and matched
transport comparison stopped at the missing-data gate (2026-09-06). Report QA
is complete; see `BKT_BARRA_QA.md`. No BARRA transport calculation or inversion
rerun was made.

## Authorized scope

Use existing public meteorology, not a new WRF simulation. Validate a BARRA-R2
input before comparing it with the existing GFS HYSPLIT-STILT calculation.
Retain the existing inversion and integrated report; rerun the inversion only
if the meteorological conversion and transport checks justify it. Do not upload,
commit, or replace prior results.

## Stages and acceptance criteria

1. Identify exact September 2019 public objects, versions, units, grid, time
   sampling and pressure/height levels. Inspect actual NetCDF metadata and
   small subsets; preserve source identities and known issues.
2. Benchmark bounded subsetting before bulk acquisition. Prefer public
   THREDDS or HTTP range reads; avoid downloading full multi-decade archives.
3. Establish a physically defensible ARL conversion, including surface
   pressure, terrain, near-surface stability, humidity and vertical velocity.
   Never silently fill masked above-ground data or represent missing values
   as zero. Validate packing by round-trip comparison and NOAA profile output.
4. Validate regional boundary handling and vertical-coordinate compatibility
   with the existing GFS outer grid before a multi-day run. Retain identical
   receptor times, heights, seeds, particle settings and footprint grid.
5. Start with a short receptor test, then the preselected September transport
   anchors used in the existing sensitivity analysis. Compare endpoint
   retention, vertical profiles and surface transport sensitivity. A finer
   grid alone does not establish better transport accuracy.
6. Integrate verified findings into the existing scientific report, preserving
   previous results and clearly labeling the comparison as a sensitivity test.
   Run applicable numerical checks, all report gates, and final-build visual QA.

## Stop conditions

Stop before transport if required public fields cannot be obtained, conversion
would require unsupported physical assumptions, or boundary handling fails.
Record the concrete evidence and minimum additional requirement. Do not claim
a transport comparison or inversion improvement from archive inspection alone.

## Current evidence

- Public anonymous S3 archive listing and README are accessible.
- Public NCI OPeNDAP and NetCDF subset services provide the selected September
  2019 files without login. Source keys, advertised S3 ETags, exact NCI request
  URLs, native metadata and downloaded-subset SHA-256 values are recorded.
- Inspected 20 fields on 13 hourly timestamps, 9 September 2019 00:00–12:00 UTC,
  at the native grid. Requested 95–105 E, 5 S–5 N; returned grid coordinates are
  94.97–104.98 E and 4.95 S–4.95 N (91 by 92 cells).
- All six inspected pressure-level families have above-surface missing values:
  1,982/102,794 eligible cell-times at 925 hPa and 308/108,228 at 850 hPa, using
  surface pressure greater than level pressure plus 1 hPa. Gaps persist with a
  10 hPa margin. Missing includes CF masks and NaNs, not only explicit masks.
- Three original packed-field examples and their decoded surface pressures
  independently confirm the selected subset gaps. The precise cause of the
  mask extent was not established; do not call it a confirmed provider defect.
- Supplemental temperature fields at 50, 100, 150, 200, 250 and 1500 m were also
  inspected. They do not independently reconstruct the missing common fields.
- NCI warns of masked pressure-level and selected height-level fields,
  regional boundary artefacts, and some humidity anomalies. These must be tested
  for the requested period rather than hidden by interpolation.

## Decision and remaining dependency

The no-unvalidated-gap-filling acceptance criterion was not met. Stop before
packing or simulating: an ARL converter and a matched transport comparison have
not been implemented or validated. This is a workflow-readiness decision, not a
finding that BARRA is generally unusable or less accurate than GFS. Do not rerun
the inverse problem using an unvalidated reconstruction.

Resuming requires provider guidance/compatible model-level data, or an explicit
decision to develop and validate a terrain-aware reconstruction as a separate
methodological experiment. Do not silently fill missing values with zero or
drop affected levels to force a run. No provider message has been sent.

Audit products: `outputs/hysplit/barra/quality/`; acquisition and validation
commands: `docs/BKT_BARRA_REPRODUCIBILITY.md`. The integrated scientific appendix
is generated from these CSVs; no separate scientific report was created.

Primary documentation: https://opus.nci.org.au/spaces/NDP/pages/264241166/BOM+BARRA2+ob53
and its linked Known Issues page. Archive:
https://bom-opendata-climate.s3.amazonaws.com/BARRA2/README.txt
