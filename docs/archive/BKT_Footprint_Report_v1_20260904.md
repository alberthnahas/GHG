# Greenhouse-gas footprint at Bukit Kototabang

**Subtitle:** A validated 72-hour receptor-oriented transport pilot using NOAA GDAS1 meteorology  
**Domain:** Bukit Kototabang receptor and modeled upstream sensitivity over southern Sumatra and adjacent seas  
**Study period:** Receptor at 26 September 2019 01:00 UTC (08:00 WIB); backward window 23 September 2019 01:00 UTC to 26 September 2019 01:00 UTC  
**Data status:** Quality-controlled BKT observations; experimental transport footprint  
Analysis date: 4 September 2026

## Scientific summary

This study implements and tests a greenhouse-gas footprint mode for the Bukit Kototabang (BKT) station using the Hybrid Single-Particle Lagrangian Integrated Trajectory model in its Stochastic Time-Inverted Lagrangian Transport (HYSPLIT-STILT) configuration. The calculation answers a source-receptor question: **which surface locations and prior hours could influence a specified BKT measurement under the modeled meteorology?** It does not estimate emissions, identify individual sources, or calculate the total atmospheric mixing ratio.

The pilot receptor hour was 26 September 2019 01:00 UTC (08:00 WIB), when the harmonized BKT record contained 437.09 ppm carbon dioxide (CO₂), 1,922.06 ppb methane (CH₄), and 531.15 ppb carbon monoxide (CO). Within a symmetric ±7-day context containing 335 valid hours out of 337 expected hours, these measurements occupied the 84.0th, 72.4th, and 69.4th percentiles, respectively. The observed values define the receptor context but do not scale the transport footprint.

The 72-hour backward calculation used 500 particles and National Oceanic and Atmospheric Administration (NOAA) National Centers for Environmental Prediction Global Data Assimilation System one-degree (GDAS1) meteorology. Of the integrated footprint sensitivity, 71.4% occurred southeast of BKT, 10.2% south, 3.6% east, and 14.9% in the receptor grid cell. The sensitivity-weighted median distance was 224 km; 57.7% occurred within 250 km and 90% within 456 km. Positive sensitivity extended to 1,081 km, but the most distant cells contributed little.

Temporally, 39.0% of integrated sensitivity occurred during the most recent 24 hours, 36.3% during hours 25–48, and 24.7% during hours 49–72. The sensitivity-weighted median lag was 32 hours and the 90th-percentile lag was 60 hours. These shares characterize one deterministic transport realization. They are not probabilities and they are not fractions of measured CO₂, CH₄, or CO attributable to geographic sectors.

All 11 focused integrity checks passed, including hourly coverage, finite non-negative sensitivity, agreement among CSV and NetCDF representations, absence of positive cells on the grid edge, confirmation of the STILT and boundary-layer options in the model log, absence of fatal model messages, and byte-level plus SHA-256 verification of the meteorological file. The result is suitable as a reproducible transport pilot. Quantitative greenhouse-gas enhancement or inversion requires flux inventories, boundary conditions, repeated receptor hours, transport ensembles, and uncertainty propagation.

> **Decision-relevant finding.** The implemented mode can reproducibly map modeled upstream surface influence for an exact BKT greenhouse-gas observation. The present pilot supports a southeast-oriented transport interpretation for one hour, but it does not support source attribution or emission estimation.

## Scientific question and scope

The primary question is:

> For the BKT observation at 26 September 2019 01:00 UTC, where and when did the modeled air parcels interact with the lower planetary boundary layer during the preceding 72 hours?

The target quantity is a gridded footprint: the sensitivity of receptor mixing ratio to a unit surface flux in a particular grid cell and time interval. The calculation is receptor-oriented: particles are released at BKT and integrated backward through analyzed meteorology.

The pilot is designed to establish transport capability, file contracts, provenance, and validation. It is not designed to distinguish fossil-fuel, biospheric, wetland, agricultural, waste, or fire fluxes. No surface-flux inventory or lateral boundary field is included. Consequently, the scientific interpretation is limited to modeled transport sensitivity.

![Workflow separating the completed transport calculation from future flux convolution and inversion.](outputs/hysplit/bkt_20190926T0100Z/report/figures/figure_01_workflow.png)

**Figure 1.** Architecture of the BKT footprint mode. Blue boxes identify components implemented and validated in this pilot. Gray boxes identify subsequent analysis stages requiring independently evaluated flux inventories and boundary conditions. PBL means planetary boundary layer.

## Evidence base and data quality

**Table 1. Evidence used in the pilot.** Periods are inclusive and expressed in Coordinated Universal Time (UTC). Valid-hour counts apply to the observation-context window rather than the complete BKT archive.

| Evidence | Variables, role and units | Resolution | Period and population | Quality and provenance |
|---|---|---|---|---|
| BKT hourly observations | Receptor-context CO₂ (ppm), CH₄ (ppb) and CO (ppb) | 1 h | 19 September–3 October 2019; 335 of 337 hours per gas | Harmonized station loader; project range and suspect-period flags |
| NOAA NCEP GDAS1 | Meteorological fields used by HYSPLIT in native units | 1°; 3 h | 22–28 September 2019; one weekly ARL file | Official HYSPLIT-ready archive; byte count and SHA-256 verified |
| HYSPLIT-STILT output | Surface-flux sensitivity in ppm per (µmol m⁻² s⁻¹) | 0.25° output; 1 h | 72 backward intervals; 4331 non-zero cell-hours in 432 cells | HYSPLIT 5.4.2 logs, CSV, NetCDF and independent reconciliation |
| Run configuration and logs | Receptor, model options, integrity checks and warnings | Per run | Complete pilot execution; 11 of 11 checks passed | Machine-readable metadata and validation record |

### BKT observation handling

The BKT measurement was read through the project’s harmonized loader, which corrects the station-specific time basis and preserves the established gas units. The exact receptor hour was required to exist once and to contain all three gases. At that hour all project-level suspect flags were false. Station elevation (864.5 m above mean sea level) was retained as metadata, whereas the particle release was specified at the inlet height of 30 m above ground level (AGL). Adding station elevation to the AGL release would have double-counted terrain height.

For descriptive context, each receptor value was ranked among quality-controlled hourly observations from seven days before to seven days after the receptor time. Missing hours remained missing; they were not interpolated. The percentile rank used mid-ranks for ties. These percentiles describe the local measurement distribution and are not evidence that the gases shared a source.

**Table 2. BKT receptor-hour measurements relative to the ±7-day context.** Interquartile range is the 25th–75th percentile of valid hourly data. Coverage was 99.4% for each gas.

| Gas | Receptor value | Context median | Context interquartile range | Receptor percentile | Valid hours |
|---|---:|---:|---:|---:|---:|
| CO₂ | 437.09 ppm | 419.60 ppm | 412.28–431.65 ppm | 84.0% | 335 |
| CH₄ | 1,922.06 ppb | 1,903.62 ppb | 1,888.30–1,925.40 ppb | 72.4% | 335 |
| CO | 531.15 ppb | 429.52 ppb | 324.25–587.35 ppb | 69.4% | 335 |

![BKT CO2, CH4 and CO observations over the 14-day context window.](outputs/hysplit/bkt_20190926T0100Z/report/figures/figure_02_observation_context.png)

**Figure 2.** Hourly BKT CO₂, CH₄ and CO surrounding the receptor observation, 19 September–3 October 2019 UTC. Orange points and vertical lines mark the receptor hour; orange shading marks the 72-hour backward calculation window. Dashed horizontal lines are gas-specific medians over the displayed valid-hour context. Missing observations are retained as gaps. Data source: quality-controlled BKT hourly measurements processed with the project’s station-specific time and unit corrections.

## Transport model and footprint method

### Model configuration

HYSPLIT is a Lagrangian particle transport and dispersion system developed by NOAA’s Air Resources Laboratory [1]. The STILT configuration was developed for receptor-oriented trace-gas applications [2]. NOAA documents the `ICHEM=8` setting as a mode that outputs mixing-ratio sensitivity and permits the first concentration layer to vary with boundary-layer depth [3].

**Table 3. HYSPLIT-STILT pilot configuration.** Heights are above ground level unless explicitly identified as mean sea level.

| Component | Pilot setting | Interpretation |
|---|---:|---|
| Receptor latitude, longitude | 0.202° S, 100.318° E | BKT station coordinates |
| Station elevation | 864.5 m MSL | Metadata; not added to particle height |
| Receptor height | 30 m AGL | Existing BKT inlet |
| Backward duration | 72 h | 23 September 01:00 to 26 September 01:00 UTC |
| Particle ensemble | 500 | Deterministic random seed; sampling sensitivity not yet tested |
| Meteorology | NOAA NCEP GDAS1 | 1° analysis at 3-hour intervals |
| Output grid | 0.25° | Particle-accumulation grid, not meteorological resolution |
| Footprint layer | Lower 50% of modeled PBL | Surface-influence criterion documented for STILT mode |
| Dispersion settings | `ICHEM=8`, `IDSP=2`, `KBLT=5`, `KMIXD=3`, `VSCALES=-1` | STILT mixing-ratio mode with mass-consistent dispersion and specified turbulence/mixing options |
| Convection | Grell flux mode, `CAPEMIN=-2` | Confirmed active in the model message log |
| Output interval | 1 h | 72 temporally resolved footprint fields |

The model output grid is finer than the driving meteorology. This improves the spatial sampling of particle residence time, but it does not resolve meteorological structures below the approximately one-degree GDAS1 scale.

### Footprint interpretation

For an externally supplied surface-flux field, the modeled contribution to a receptor enhancement can be written as

$$
\Delta c(t_r)=\sum_m\sum_i\sum_j f_{ijm}(t_r)E_{ijm},
$$

where the left-hand side is the modeled enhancement at receptor time, the footprint term is HYSPLIT-STILT sensitivity in ppm per (µmol m⁻² s⁻¹), and the final term is a temporally and spatially matched surface flux in µmol m⁻² s⁻¹. A total modeled mole fraction would additionally require an independently defined boundary or background term. This pilot calculates footprint sensitivity but does not supply surface fluxes or the boundary term.

For diagnostic subset (k), the reported integrated-sensitivity share is

$$
S_k=100\times\frac{\sum_{(i,j,m)\in k}f_{ijm}}{\sum_{i,j,m}f_{ijm}}.
$$

The resulting share is dimensionless and sums to 100% across a complete, mutually exclusive partition. It is useful for describing the geometry and timing of the footprint. It is not a source-contribution percentage because no emissions are multiplied by the sensitivity.

### Meteorological acquisition and integrity

The minimum meteorological input for the pilot was the official weekly GDAS1 file covering 22–28 September 2019 [4]. The acquired file contained 598,888,640 bytes. Its SHA-256 checksum was `319a1acd675e3ab5564d04d9071776787441b275c58f7a8cb68c0f31295eb073`. HYSPLIT’s meteorological-file inspection confirmed global one-degree coverage, three-hourly fields, 24 vertical levels, and the presence of boundary-layer and surface variables needed by the configured calculation.

## Results

### The pilot footprint was concentrated southeast of BKT

Positive footprint sensitivity occupied 432 output cells and extended from 0.202° S to 6.702° S and from 100.318° E to 109.568° E. The sensitivity-weighted centroid was 1.589° S, 101.681° E. The receptor grid cell contained 14.9% of the integrated sensitivity, reflecting strong near-receptor residence in the lower modeled boundary layer. Outside that cell, the southeast sector dominated.

![Spatial HYSPLIT-STILT footprint for the BKT receptor hour.](outputs/hysplit/bkt_20190926T0100Z/report/figures/figure_03_spatial_footprint.png)

**Figure 3.** HYSPLIT-STILT surface-flux sensitivity accumulated over the 72 hours ending at BKT on 26 September 2019 01:00 UTC. The receptor is 30 m AGL. Colors use a logarithmic scale spanning the 10th–99.5th percentiles of positive cells. Meteorology: NOAA NCEP GDAS1 analysis at 1° resolution; output grid: 0.25°. The map shows modeled upstream influence, not emissions, source attribution, or total greenhouse-gas concentration. Display coordinates use WGS 84 longitude and latitude.

**Table 4. Spatial distribution of integrated footprint sensitivity.** Sector bearings describe the location of each footprint cell relative to BKT. The receptor-cell category has no directional bearing.

| Diagnostic | Result |
|---|---:|
| Receptor grid-cell share | 14.9% |
| East-sector share | 3.6% |
| Southeast-sector share | 71.4% |
| South-sector share | 10.2% |
| Sensitivity-weighted median distance | 224 km |
| Share within 100 km | 30.8% |
| Share within 250 km | 57.7% |
| Sensitivity-weighted 90th-percentile distance | 456 km |
| Maximum distance of a positive cell | 1,081 km |

![Heatmap of integrated footprint sensitivity by distance and direction from BKT.](outputs/hysplit/bkt_20190926T0100Z/report/figures/figure_05_sector_distance.png)

**Figure 4.** Percentage of integrated HYSPLIT-STILT sensitivity by great-circle distance and direction from BKT. Values are cellwise sensitivity shares summed across the 72-hour window. Blank cells have zero share at the displayed precision. The receptor cell is separated from directional sectors. These percentages describe modeled transport geometry and must not be interpreted as emission-sector or geographic source contributions.

### Half of integrated sensitivity occurred within 32 hours

The footprint was not confined to the latest meteorological day. The most recent 24 hours contributed 39.0% of integrated sensitivity, hours 25–48 contributed 36.3%, and hours 49–72 contributed 24.7%. The sensitivity-weighted median lag was 32 hours, while 90% accumulated within 60 hours. Thus, shortening the backward window to 24 hours would omit 61.0% of the integrated sensitivity in this realization; shortening it to 48 hours would omit 24.7%.

![Lag-resolved integrated footprint sensitivity.](outputs/hysplit/bkt_20190926T0100Z/report/figures/figure_04_lag_sensitivity.png)

**Figure 5.** Temporal distribution of the BKT footprint. The upper panel shows sensitivity summed within consecutive six-hour lag blocks. The lower panel shows cumulative sensitivity from the most recent hour backward, with the 50% crossing at 32 hours. Values describe one deterministic 500-particle run. No ensemble uncertainty is represented.

### The receptor observations were elevated but not exceptional within the local context

All three receptor values exceeded their ±7-day medians. CO₂ had the highest percentile rank at 84.0%, followed by CH₄ at 72.4% and CO at 69.4%. These non-identical ranks and the rapidly changing surrounding record caution against treating the three gases as a single emission signal. The transport footprint is identical for passive tracers released at the same receptor time and height, but flux distributions, backgrounds, sinks, and measurement uncertainties differ by gas.

## Quality assurance and validation

The validation was designed to test the entire chain rather than only successful model termination. It covered receptor data, meteorological integrity, model configuration, temporal and spatial completeness, numerical representation, and rendered outputs.

**Table 5. Focused validation results.** “Pass” indicates the check was executed on the pilot artifacts.

| Check | Result | Evidence |
|---|---|---|
| Exact harmonized receptor record | Pass | One complete BKT hour at 26 September 2019 01:00 UTC |
| Backward hourly coverage | Pass | 72 of 72 expected intervals |
| Finite, non-negative sensitivity | Pass | 4331 non-zero cell-hours; no negative or non-finite values |
| CSV, aggregate CSV and NetCDF agreement | Pass | Totals reconciled within configured floating-point tolerances |
| Output-domain containment | Pass | No positive footprint cells on a domain edge |
| STILT and boundary-layer options | Pass | Required settings present; mixed-layer and convection modes confirmed in log |
| Fatal HYSPLIT messages | Pass | None |
| Meteorology size | Pass | 598,888,640 bytes |
| Meteorology checksum | Pass | SHA-256 matched the acquisition record |
| Spatial population | Pass | 432 positive cells |
| Map rendering | Pass | 3000 × 2250 px PNG plus one-page vector PDF |

The model emitted a notice that GDAS is not an Advanced Research Weather Research and Forecasting (ARW) dataset and therefore used HYSPLIT’s default vertical interpolation rather than ARW-specific interpolation. This is expected for GDAS input and is not a fatal condition. The model log confirmed active mixed-layer depth and convective mixing calculations.

## Discussion

### Physical interpretation

The southeast-oriented footprint is consistent with air parcels approaching BKT from lower-latitude and eastern sectors during this single modeled period. Strong sensitivity close to the receptor is physically plausible because particles in the lower modeled boundary layer accumulate residence time near the release location. The broad tail toward southern Sumatra and adjacent seas indicates that regional surface fluxes could matter under this transport realization.

The map does not establish that any specific place emitted CO₂, CH₄, or CO. A location with high sensitivity can contribute little when its actual surface flux is small, while a lower-sensitivity location can matter when its flux is large. Furthermore, oceanic and terrestrial cells have different plausible flux magnitudes and signs, especially for CO₂. Scientific attribution therefore requires a flux-weighted footprint, not footprint sensitivity alone.

### Competing explanations for the receptor concentrations

The measured mixing ratios may reflect combinations of background variability, local ecosystem exchange, boundary-layer depth, regional anthropogenic emissions, wetlands, agriculture, biomass burning, or measurement-scale influences. The present design cannot distinguish these mechanisms. CO can provide combustion context, but co-elevation does not prove fire influence; CH₄ and CO₂ have additional sources and different lifetimes. The percentile comparison also depends on diurnal and synoptic variability in the chosen ±7-day window.

### Representativeness and operational value

The workflow is operationally useful because it accepts an exact BKT hour, identifies the minimum GDAS1 files, produces machine-readable hourly sensitivities, records provenance, and fails on incomplete or invalid outputs. It can therefore be repeated for a sequence of observations. However, one pilot hour is not representative of a season, an episode, or the climatological BKT footprint. A footprint library stratified by season, local time, boundary-layer regime, and meteorological flow would be needed for broader interpretation.

## Limitations and robustness

1. **Single receptor hour.** No temporal replication or meteorological regime comparison is available.
2. **Deterministic particle ensemble.** The 500-particle run has no particle-count sensitivity or stochastic ensemble. Monte Carlo sampling error is therefore unquantified.
3. **Coarse meteorology.** One-degree GDAS1 cannot resolve BKT’s steep terrain, local valley circulations, or fine land–sea-breeze structure. The 0.25° output grid does not add meteorological resolution.
4. **Boundary-layer uncertainty.** Footprint magnitude depends on modeled mixing-layer depth and the lower-50% surface-influence criterion. Stable nocturnal conditions and deep convection can be difficult to represent.
5. **No flux convolution.** Without temporally resolved CO₂ and CH₄ flux fields, sensitivity shares are not concentration contributions.
6. **No boundary condition.** The model does not supply the atmospheric background needed for absolute CO₂ or CH₄ mole fractions.
7. **No chemistry or sinks.** The pilot treats the footprint as passive transport. This is appropriate for regional CO₂ and CH₄ transport over 72 hours as a first approximation, but gas-specific processes and biospheric uptake are absent.
8. **No formal transport error.** Meteorological, turbulence, receptor-height, and representation errors are not propagated. Transport error can materially affect tracer inversions [5].
9. **Sector and distance shares are descriptive.** They are calculated from footprint sensitivity without emissions and do not identify economic sectors or administrative source regions.

The numerical output is internally robust to representation: CSV, aggregate CSV and NetCDF totals agree. Scientific robustness to alternative transport configurations remains untested. The result should therefore be described as **validated computationally but provisional scientifically**.

## Conclusions and implications

The BKT footprint mode is implemented and reproducible. For the 26 September 2019 01:00 UTC pilot, the modeled lower-boundary-layer sensitivity was concentrated southeast of BKT, with a median lag of 32 hours and a median distance of 224 km. These diagnostics provide a defensible transport screen for selecting upstream flux fields and designing subsequent analyses.

The footprint does not explain the measured 437.09 ppm CO₂, 1,922.06 ppb CH₄, or 531.15 ppb CO by itself. It establishes the transport operator needed for that task. The next scientific threshold is not another map; it is a validated convolution of the hourly footprint with gas-specific fluxes and boundary conditions, followed by comparison against observed enhancements and an explicit transport-error model.

## Recommended next actions

**Table 6. Staged development from pilot footprint to inversion.** The order prevents unvalidated flux or transport assumptions from being hidden inside an inversion.

| Stage | Required evidence or data | Main output | Acceptance criterion |
|---|---|---|---|
| 1. Transport sensitivity | Repeat 100, 500, 1000 and 2500 particles; test 24, 48, 72 and 120 h windows | Particle and duration sensitivity report | Stable spatial/temporal summaries within declared tolerance |
| 2. Meteorological sensitivity | Higher-resolution meteorology and alternative PBL/turbulence settings | Transport ensemble | Major footprint sectors and arrival times characterized with spread |
| 3. CO₂ flux convolution | Fossil-fuel prior, net ecosystem exchange, fire CO₂ and ocean flux | Modeled CO₂ enhancement components | Units, temporal matching, cell areas and signs independently verified |
| 4. CH₄ flux convolution | Fossil, wetland, rice, livestock, waste and fire CH₄ priors | Modeled CH₄ enhancement components | Sector definitions and inventory uncertainties documented |
| 5. Boundary conditions | Regional CO₂ and CH₄ mole-fraction fields or upwind observations | Total modeled mole fraction | Background method validated independently of local flux fitting |
| 6. Multi-hour evaluation | Repeated BKT observations across seasons and local times | Observed–modeled diagnostics | Bias, MAE, RMSE, correlation and regime-specific failure modes reported |
| 7. Inversion | Prior fluxes, observation errors, transport covariance and boundary uncertainty | Posterior flux estimates | Holdout evaluation, sensitivity tests and posterior uncertainty reported |

The minimum next experiment should repeat this receptor hour with multiple particle counts and at least one higher-resolution meteorological driver. Flux acquisition should begin only after the transport ensemble defines the domain and temporal window needed for each inventory.

## References

1. Stein, A. F., Draxler, R. R., Rolph, G. D., Stunder, B. J. B., Cohen, M. D., and Ngan, F. (2015). NOAA’s HYSPLIT atmospheric transport and dispersion modeling system. *Bulletin of the American Meteorological Society*, 96, 2059–2077. [https://doi.org/10.1175/BAMS-D-14-00110.1](https://doi.org/10.1175/BAMS-D-14-00110.1)
2. Lin, J. C., Gerbig, C., Wofsy, S. C., Andrews, A. E., Daube, B. C., Davis, K. J., and Grainger, C. A. (2003). A near-field tool for simulating the upstream influence of atmospheric observations: The Stochastic Time-Inverted Lagrangian Transport (STILT) model. *Journal of Geophysical Research: Atmospheres*, 108(D16), 4493. [https://doi.org/10.1029/2002JD003161](https://doi.org/10.1029/2002JD003161)
3. NOAA Air Resources Laboratory. Configuring STILT options in HYSPLIT. HYSPLIT Tutorial and User’s Guide. Accessed 4 September 2026. [NOAA STILT configuration](https://www.ready.noaa.gov/documents/Tutorial/html/stilt_setup.html)
4. NOAA Air Resources Laboratory. Meteorological data archives: GDAS one-degree archive. Accessed 4 September 2026. [NOAA meteorological archives](https://hysplit2.arl.noaa.gov/archives.php)
5. Lin, J. C., and Gerbig, C. (2005). Accounting for the effect of transport errors on tracer inversions. *Geophysical Research Letters*, 32, L01802. [https://doi.org/10.1029/2004GL021127](https://doi.org/10.1029/2004GL021127)

## Technical methods and quality assurance

### Input datasets and provenance

The immutable scientific observation source remains the project’s BKT hourly archive. The analysis accesses it only through `ghg_common.load_station("BKT")` followed by the project’s flag application, thereby preserving the BKT timestamp correction and station-specific units.

The meteorological source was NOAA’s HYSPLIT-ready weekly GDAS1 archive object `gdas1.sep19.w4`. The acquisition record stores the official URL, retrieval time, exact byte count and SHA-256 checksum. The 599 MB meteorological binary is deliberately excluded from version control; its small provenance record is retained.

### Generated analytical tables

Every numerical result in this report traces to a machine-readable table produced by the report-analysis script:

| Analytical table | Purpose |
|---|---|
| `observation_context_hourly.csv` | Complete expected hourly timeline with explicit missing rows |
| `observation_context_summary.csv` | Receptor values, coverage, quantiles and percentile ranks |
| `lag_sensitivity_hourly.csv` | Hourly sensitivity totals, shares and cumulative shares |
| `lag_sensitivity_6hour.csv` | Six-hour blocks used in Figure 5 |
| `spatial_cell_summary.csv` | Cell sensitivity, distance, bearing, sector and share |
| `sector_distance_share.csv` | Distance-by-direction matrix used in Figure 4 |
| `validation_checks.csv` | Focused end-to-end validation evidence |
| `report_metrics.json` | Compact record of report headline values and provenance |

### Preprocessing and quality control

Observation times are stored internally in UTC. The selected receptor time is also reported as 08:00 Western Indonesian Time (WIB; UTC+7). No observation was interpolated. Gas-specific suspect flags were respected independently. The 14-day contextual population contains 335 valid measurements from 337 expected hours for every displayed gas.

Footprint ASCII output was parsed into a sparse non-zero cell-hour table and a complete time–latitude–longitude NetCDF cube containing explicit zero cells. Coordinates are WGS 84 longitude and latitude. The NetCDF sensitivity variable is stored as compressed 32-bit floating point after comparison with the 64-bit CSV total. The accepted relative tolerance for CSV-to-NetCDF reconciliation was 0.000002.

Great-circle distances use an Earth radius of 6371.0088 km. Direction sectors are eight 45° bins centered on north, northeast, east, southeast, south, southwest, west and northwest. The exact receptor grid cell is separated because its bearing is undefined. Weighted quantiles sort cells or hours by distance or lag and identify the value at which cumulative sensitivity reaches the requested fraction.

### Model execution safeguards

The run directory contains explicit `CONTROL`, `SETUP.CFG` and `ASCDATA.CFG` files. The workflow refuses incomplete meteorological files, partial downloads, duplicate output directories unless forced, empty model dumps, fatal log entries, unexpected output schemas, negative or non-finite sensitivities, timestamps outside the requested window, and coordinates outside the configured grid.

HYSPLIT 5.4.2 writes an optional minute-scale particle diagnostic even when the documented output interval requests suppression. The workflow redirects that optional stream to the null device on POSIX systems to prevent an unnecessary multi-gigabyte file while retaining the gridded footprint, particle dump, message log and configuration.

### Reproducibility

The pilot can be reproduced from the project root with:

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

python3 scripts/a38_bkt_footprint_report.py

python3 scripts/a14_latex.py BKT_HYSPLIT_STILT_Footprint_Report
```

The analysis environment used Python 3.14.4, NumPy 2.4.4, pandas 2.3.3, xarray 2025.1.1, h5netcdf 1.8.1, Matplotlib 3.10.8 and Cartopy 0.25.0. Transport used HYSPLIT 5.4.2. Raster figures were exported at 300 dpi and vector PDF counterparts were generated.

### Independent and rendered checks

The footprint validator independently reconstructed the 72 expected UTC intervals; reconciled sensitivity totals across three representations; verified finite, non-negative values; checked domain edges; parsed the HYSPLIT configuration and message log; recomputed the meteorological checksum; and checked rendered map dimensions. The report figures were inspected at full resolution and thumbnail scale. The final PDF was compiled from this Markdown source, checked for missing sections and unresolved template markers, rendered page by page, and inspected for clipping, unreadable tables, missing glyphs and inconsistent scientific notation.
