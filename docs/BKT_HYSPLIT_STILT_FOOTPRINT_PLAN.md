# BKT HYSPLIT-STILT footprint implementation plan

## Objective

Implement a reproducible backward footprint mode for hourly greenhouse-gas
measurements at Bukit Kototabang (BKT). The first validated case is the complete
CO2/CH4/CO observation at 2019-09-26 01:00 UTC (08:00 WIB), during the 2019
haze period.

## Scientific scope

- Receptor: BKT at -0.202 degrees latitude, 100.318 degrees longitude and a
  30 m above-ground inlet. The station elevation (864.5 m above mean sea level)
  is metadata, not added to the HYSPLIT AGL release height.
- Transport: 72 h backward HYSPLIT-STILT calculation driven by NOAA GDAS1
  analysis meteorology.
- Footprint: concentration sensitivity to an upstream surface flux, not an
  emission estimate, source attribution, or total atmospheric mixing ratio.
- Pilot resolution: 1 degree meteorology and a 0.25 degree output grid. The
  finer output grid samples particles more finely but does not create finer
  meteorological information.
- Particle ensemble: 500, a commonly used STILT baseline for hourly receptor
  footprints. Particle-count sensitivity remains required before inversion.

## Acceptance criteria

- [x] Read BKT measurements through `ghg_common.load_station`; never read the
  raw JSON directly.
- [x] Determine and document the minimum official NOAA meteorological input.
- [x] Add resumable acquisition with byte-size and SHA-256 provenance.
- [x] Generate explicit `CONTROL`, `SETUP.CFG`, and `ASCDATA.CFG` files.
- [x] Use HYSPLIT-STILT settings and deterministic particle dispersion.
- [x] Export hourly CSV, gridded NetCDF, aggregate CSV, run metadata, PNG and
  PDF outputs.
- [x] Execute the pilot against the complete NOAA file and inspect model logs.
- [x] Verify temporal coverage, non-negative finite sensitivity, output units,
  receptor metadata, and map rendering.
- [x] Run focused unit tests and the repository verification gates.
- [x] Produce a comprehensive canonical Markdown report and publication-ready
  A4 PDF with five figures, evidence tables, explicit uncertainty and a
  reproducibility appendix.
- [x] Add automated report validation covering evidence-table reconciliation,
  figure resolution, PDF metadata, A4 pagination, extracted section text and
  LaTeX warnings.

## Validation strategy

1. Confirm NOAA file byte size, SHA-256 and HYSPLIT time coverage.
2. Require the exact receptor hour to exist in the harmonised BKT record.
3. Fail on incomplete model files, HYSPLIT fatal messages, empty footprints,
   invalid timestamps, negative sensitivities, or values outside the grid.
4. Independently reconcile hourly CSV totals, aggregate CSV totals and NetCDF
   totals within floating-point tolerance.
5. Render the map at full size and thumbnail size; check coordinates, units,
   extent, color normalization and caveat language.

## Deferred work

This pilot does not ingest surface-flux inventories, estimate CO2 or CH4
enhancements, construct boundary/background fields, quantify transport error,
or perform an inversion. Those steps require separately validated flux products
and an ensemble or higher-resolution meteorological sensitivity study.
