# Bukit Kototabang HYSPLIT-STILT footprint mode

## Revision of 5 September 2026

Use `a39_bkt_refinement.py` for the revised experiment and analysis, and
`a40_bkt_refinement_report.py` for the comprehensive report. Revised numerical
outputs are under `outputs/hysplit/refinement/analysis/`. The original pilot
below is retained as historical documentation.

The correction is material for absolute coefficients: native HYSPLIT output
divides by requested NUMPAR, whereas one-minute release rounding can emit more
particles. A paired 500/540-requested, 540-actual experiment demonstrates the
effect. Revised derived coefficients and maps multiply by requested/actual.
Within-run normalized geographic and lag shares are unaffected. All revised
Indonesian boundaries use the established shared provincial GeoJSON.

## Result and intended use

This workflow converts an exact hourly Bukit Kototabang (BKT) greenhouse-gas
measurement time into a backward surface-flux sensitivity field. The field
answers: **where and when would a unit surface flux have the greatest modeled
influence on the receptor mixing ratio?** It does not identify an emitting
facility, prove biomass-burning influence, or calculate absolute CO2 or CH4.

The implemented pilot ends at 2019-09-26 01:00 UTC (08:00 WIB). The harmonised
BKT record at that hour is 437.09 ppm CO2, 1922.06 ppb CH4 and 531.15 ppb CO;
all three values pass the project-level range and suspect-period flags. These
values provide receptor context only and do not scale the footprint.

## Model configuration

| Item | Pilot setting |
|---|---|
| Receptor | BKT, -0.202 degrees, 100.318 degrees |
| Station elevation | 864.5 m above mean sea level (metadata) |
| Receptor inlet | 30 m above ground level |
| Backward duration | 72 h |
| Meteorology | NOAA NCEP GDAS1 analysis, 1 degree, 3-hourly |
| Particles | 500, deterministic seed |
| Output grid | 0.25 degrees, 20 by 30 degree span |
| Surface-influence layer | lower 50% of modeled planetary boundary layer |
| HYSPLIT options | ICHEM=8, IDSP=2, KBLT=5, KMIXD=3, VSCALES=-1 |
| Convective mixing | Grell flux mode requested (`CAPEMIN=-2`) but inactive: the archive has no convective-flux fields and `MESSAGE` reports `Convective mixing - F` (corrected 11 September 2026) |

NOAA documents `ICHEM=8` as the HYSPLIT-STILT mode that combines mixing-ratio
output with a boundary-layer-dependent first concentration layer. NOAA gives
the footprint unit as ppm per micromole per square metre per second and defines
it from particle residence time in the lower boundary layer. See the
[official STILT configuration](https://www.ready.noaa.gov/documents/Tutorial/html/stilt_setup.html),
[advanced HYSPLIT discussion](https://www.ready.noaa.gov/hysplitusersguide/S441.htm),
and [GDAS1 archive description](https://hysplit2.arl.noaa.gov/archives.php).
The scientific basis is Lin et al. (2003),
doi:[10.1029/2002JD003161](https://doi.org/10.1029/2002JD003161).

The 0.25 degree output grid is a particle-accumulation grid, not the effective
meteorological resolution. The 1 degree GDAS1 driver cannot resolve the steep
BKT terrain, local valley circulations, or fine land-sea-breeze structure.

## Reproduce

```bash
python3 scripts/a37_bkt_footprint.py fetch \
  --receptor-utc 2019-09-26T01:00:00 --hours-back 72

python3 scripts/a37_bkt_footprint.py run \
  --receptor-utc 2019-09-26T01:00:00 --hours-back 72 \
  --hysplit-home /path/to/hysplit

python3 scripts/plot_bkt_footprint.py \
  outputs/hysplit/bkt_20190926T0100Z

python3 scripts/validate_bkt_footprint.py \
  outputs/hysplit/bkt_20190926T0100Z
```

Meteorology is not committed. The fetch step is resumable and writes a tracked
JSON record containing the official URL, exact byte size, retrieval time and
SHA-256 checksum. Generated model outputs remain under the already ignored
`outputs/` tree.

## Output contract

- `footprint_hourly.csv.gz`: non-zero cell-hour sensitivities with UTC and lag.
- `footprint.nc`: complete time-latitude-longitude sensitivity cube, including
  true zero cells and coordinate/units metadata.
- `footprint_aggregate.csv`: sensitivity summed over the backward window.
- `run_metadata.json`: receptor observation, configuration and summary values.
- `bkt_hysplit_stilt_footprint.png` and `.pdf`: static scientific map.
- `validation.json`: time, domain, arithmetic, model-mode, meteorology-integrity
  and rendering checks.

## Next scientific stage

For CO2, convolve each hourly footprint with temporally matched fossil-fuel,
fire and net ecosystem exchange fluxes; add a separately estimated lateral
boundary/background term. For CH4, use sector-specific fossil-fuel, wetland,
rice, waste and fire inventories. Before inference, test particle count,
backward duration, receptor height, boundary-layer scheme and higher-resolution
meteorology. Multiple BKT hours and a transport-error model are required for a
Bayesian inversion.
