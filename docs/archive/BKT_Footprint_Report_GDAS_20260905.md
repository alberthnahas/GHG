# Greenhouse-gas footprint at Bukit Kototabang

Analysis date: 5 September 2026

## Scientific summary

The Bukit Kototabang (BKT) footprint has been recalculated using three seeded HYSPLIT-STILT runs, each containing 10,020 actual particles, on a 0.1° output grid. The calculation covers the 72 hours ending on 26 September 2019 at 01:00 UTC (08:00 Western Indonesian Time, WIB). The revised Figure 3 uses a continuous display surface and the established Indonesian provincial boundaries. Its smooth appearance is supported by more particle sampling and an explicitly tested display method; the driving meteorology remains NOAA GDAS1 at 1° resolution.

The ensemble-mean footprint places 69.4% of total sensitivity southeast of BKT and beyond 25 km from the receptor. Another 19.4% lies within 25 km, where direction is especially sensitive to grid placement. The sensitivity-weighted median distance is 229 km and the median backward lag is 32 hours. Across the three seeds, the southeast share ranges from 69.3% to 69.6%; this range describes numerical sampling variability under one meteorological realization.

A controlled test identified a normalization issue in the first implementation: requesting 500 particles actually released 540. Native gridded sensitivities were normalized by the requested count. Correcting each run by the ratio of requested to emitted particles removes that dependence; the original absolute coefficient scale was about 8% too high. Geographic and lag percentages within a single run are unchanged by this uniform correction. All revised results use the corrected coefficients.

The cross-seed test selects zero additional Gaussian blur. Selection uses the ability of two seeded runs to reproduce a third, held-out run; every tested positive bandwidth worsens this criterion. The smooth map therefore combines the finer-grid ensemble with linear display interpolation and continuous contours, preserving the reproducible near-receptor structure. The reconstructed surface conserves total sensitivity to numerical precision. All quantitative regional and lag summaries use the unsmoothed ensemble mean. The product supports regional transport interpretation; it does not yet quantify the contributions of fire, fossil fuel, ecosystems, wetlands or agriculture to the observed gases.

## Scientific question and evidence

The question is where and when surface fluxes could influence the selected hourly BKT observation under the modeled transport. A second question is how sensitive that answer is to particle sampling, output-grid spacing, receptor height and map reconstruction. These are numerical robustness questions. They are not a statistical test of a particular emission source, and no emission inventory is fitted to this selected event.

The model is the Hybrid Single-Particle Lagrangian Integrated Trajectory model with the Stochastic Time-Inverted Lagrangian Transport configuration (HYSPLIT-STILT). Its documented configuration links backward particle residence in the lower planetary boundary layer (PBL) to surface-flux sensitivity [1, 2]. The same passive-transport operator can subsequently be paired with different gas-specific flux fields. It is not three independently evaluated gas concentration simulations.

The NOAA Global Data Assimilation System one-degree (GDAS1) archive supplies three-hourly meteorological analyses. The previously acquired weekly file spans the full backward window. Its byte count and SHA-256 checksum are verified before analysis. Holding this input fixed isolates the effects of numerical sampling and display choices. Finer output sampling cannot resolve atmospheric circulations or terrain absent from the meteorological input [3].

### BKT observation and quality control

The observation is loaded through the project's harmonized BKT interface, including its historical WIB-to-UTC correction and species-specific units. The receptor record passes all three project suspect flags. These are archive-level screens; they do not replace traceable calibration or instrument uncertainty. The symmetric ±7-day context contains 335 valid observations out of 337 expected hours for each gas. Missing hours remain gaps in the chart.

**Table 1. Receptor-hour measurements and local context.** Medians and percentile ranks describe the ±7-day valid-hour sample, not atmospheric background or source enhancement. CO is included as a contextual tracer.

| Gas | Receptor value | Context median | Percentile rank |
| --- | --- | --- | --- |
| CO₂ | 437.09 ppm | 419.60 ppm | 84.0% |
| CH₄ | 1,922.06 ppb | 1,903.62 ppb | 72.4% |
| CO | 531.15 ppb | 429.52 ppb | 69.4% |

![Architecture of the revised BKT transport workflow.](outputs/hysplit/refinement/analysis/figures/figure_01_workflow.png)

**Figure 1.** BKT footprint workflow for 26 September 2019 01:00 UTC. The modeled transport stage now comprises three seeded runs. Surface-flux convolution and background evaluation remain subsequent scientific stages. PBL denotes planetary boundary layer.

![BKT hourly measurement context.](outputs/hysplit/refinement/analysis/figures/figure_02_observation_context.png)

**Figure 2.** Hourly CO₂, CH₄ and CO at BKT over the ±7-day context around 26 September 2019 01:00 UTC. Orange points identify the receptor values, orange shading marks the 72-hour backward window, and dashed lines show context medians. Blank intervals are missing or flagged values; no gap interpolation is applied. Units are ppm for CO₂ and ppb for CH₄ and CO.

## Model design and experimental controls

The observed inlet is represented at 30 m above ground level (AGL), at 0.202° S, 100.318° E. Station elevation, 864.5 m above mean sea level, is metadata and is not added to the AGL release height. Particles are released over the first backward hour, from 01:00 toward 00:00 UTC, preserving the original configuration. The observation timestamp anchors that release window; the precise averaging-window convention of the underlying instrument archive has not been independently established here.

**Table 2. Physical and numerical configuration shared by the experiments unless stated otherwise.** A fine output grid samples modeled particle positions more densely; it does not change the meteorological driver.

| Item | Configuration | Scientific role |
|---|---|---|
| Transport version | HYSPLIT 5.4.2 | Same executable across runs |
| Meteorology | NOAA GDAS1, 1°, 3-hourly | Regional mean winds and mixing inputs |
| Backward duration | 72 h | 23 September 01:00 to 26 September 01:00 UTC |
| Receptor | 30 m AGL; 60 m sensitivity test | Release-height dependence |
| Output grids | 0.1°; paired 0.25° test | Particle accumulation and spatial representation |
| Output domain | 20° latitude × 30° longitude, centered on BKT | Avoid loss of modeled support at grid edges |
| STILT options | `ICHEM=8`, `IDSP=2`, `KBLT=5`, `KMIXD=3` | Mixing-ratio output and specified dispersion physics |
| Mixing layer | Lower 50% of modeled PBL; minimum PBL 250 m | Surface-influence criterion |
| Turbulence | `KRAND=2`, `VSCALES=-1`, `NTURB=0` | Turbulence active with fixed seeds |
| Convection | `CAPEMIN=-2` | Grell mode requested; activity depends on meteorological fields |
| Gridded output | Hourly, `CMASS=1` | Native STILT summation; count correction applied afterward |

The runtime reports its fallback to default vertical interpolation for GDAS rather than the WRF-specific option. This behavior is documented rather than inferred from requested settings alone. The log's convection flag confirms configuration availability; it does not independently validate convective transport or prove that a particular convective event occurred.

The principal ensemble uses seeds 0, −10 and −20. The 2,000-versus-10,000 comparison changes particle sampling on the same 0.1° grid. The 0.25° experiment holds requested count, seed and receptor height fixed. The 60 m experiment holds count, seed and grid fixed and represents a sensitivity scenario, not another measured inlet. Requested counts are retained for reproduction, while actual counts are parsed from the model logs.

**Table 3. Completed transport experiments.** All principal runs cover 72 h with the same GDAS1 file. The original run is retained for comparison; the ensemble is an arithmetic mean, not a single 30,000-particle simulation.

| Experiment | Actual particles | Seed | Grid; height |
| --- | --- | --- | --- |
| Original pilot | 540 | 0 | 0.25°; 30 m |
| 2,000 requested | 2,040 | 0 | 0.1°; 30 m |
| 10,000 seed A | 10,020 | 0 | 0.1°; 30 m |
| 10,000 seed B | 10,020 | -10 | 0.1°; 30 m |
| 10,000 seed C | 10,020 | -20 | 0.1°; 30 m |
| Coarse-grid test | 10,020 | 0 | 0.25°; 30 m |
| Height scenario | 10,020 | 0 | 0.1°; 60 m |

### Normalization correction and independent check

Two additional six-hour simulations requested 500 and 540 particles while emitting the same 540 particles. Their native integrated coefficients differed by a factor of 1.07998. Multiplying the first by 500/540 reconciled the fields to 0.015% relative L₁ difference. This controlled result supports correcting the count-rounding effect before comparing absolute sensitivities. Small residual differences are consistent with finite output precision and model arithmetic; exact trajectory identity between the count settings is not assumed.

The correction is

$$
f^{\mathrm{corrected}}_{ijm}=f^{\mathrm{native}}_{ijm}\frac{N_{\mathrm{requested}}}{N_{\mathrm{emitted}}}.
$$

Here the two particle counts are dimensionless, and the native and corrected footprint coefficients retain units of ppm per (µmol m⁻² s⁻¹). Subscripts identify longitude cell, latitude cell and backward time interval. The correction is applied to derived fields while native model output is preserved. It does not change each run's relative geographic or lag shares.

A separate six-hour test disabled optional particle diagnostic variables. The resulting gridded NetCDF values were bitwise identical to the corresponding diagnostic-enabled run. This output-only option was used for the restarted height scenario; the interrupted attempt is excluded from every result.

## Footprint analysis and smooth-map method

### Quantitative footprint definition

For temporally matched surface-flux densities, the receptor enhancement is

$$
\Delta c(t_r)=\sum_m\sum_i\sum_j f^{\mathrm{corrected}}_{ijm}(t_r) E_{ijm}.
$$

The left-hand side is an enhancement in ppm, receptor time is denoted by the subscripted time, and the flux term is in µmol m⁻² s⁻¹. Each footprint coefficient already represents sensitivity integrated over its source cell and output interval. Do not multiply these coefficients by grid-cell area or another hour-length factor when applying this discrete convolution. Gas-specific fluxes and a separately justified background are still required to predict absolute mole fractions.

The ensemble mean is calculated cell by cell and hour by hour after particle-count correction. Spatial percentages sum unsmoothed coefficients over the indicated cells and divide by the domain total. Distances and bearings are great-circle calculations on a sphere of radius 6,371.0088 km. Grid-cell centers determine regional membership. A common 25 km near-receptor zone is used for cross-grid direction comparisons to avoid treating a changing receptor-cell size as a change in upwind direction.

Temporal percentiles are sensitivity-weighted quantiles across the 72 hourly output bins. Seed ranges are descriptive minima and maxima from three runs. They are not confidence intervals and do not include meteorological, turbulence-scheme, measurement or flux-inventory uncertainty.

### Continuous display reconstruction

Fasoli et al. [4] showed that Gaussian particle kernels can reduce spatial sampling noise in STILT footprints, while excessive smoothing can erase modeled structure. The present implementation uses a simpler, explicitly distinct method: a fixed Gaussian kernel applied to an already gridded field for display. It does not reproduce the adaptive, time-dependent particle estimator in that paper.

Candidate Gaussian widths are 0, 0.35, 0.5, 0.75, 1, 1.5, 2 and 3 native grid cells. For each candidate, the mean of two seeded runs is smoothed and compared with the third unsmoothed run. The procedure rotates through all three held-out runs. Selection minimizes area-integrated quadratic prediction risk, omitting the target-only term that is constant across bandwidths:

$$
R(h)=\frac{1}{3}\sum_{r=1}^{3}\sum_{ij}
\frac{\left(\widetilde f^{(-r)}_{ij,h}\right)^2-
2\widetilde f^{(-r)}_{ij,h}f^{(r)}_{ij}}{A_{ij}}.
$$

The Gaussian width is denoted by the bandwidth, the superscript identifies the held-out seed, the tilde marks the smoothed training mean, and cell area is in km². Each spatial coefficient is summed over the backward period. Division by area converts the squared-coefficient sum into an integrated density loss. The native held-out target is never smoothed, preventing the criterion from automatically favoring agreement between two overly blurred fields. This is internal selection for numerical reproducibility, not independent atmospheric validation.

**Table 4. Candidate bandwidth performance.** Risk is reported relative to the no-kernel candidate; lower values are preferred. A negative difference indicates better agreement with held-out seeded fields under this criterion.

| Width (cells) | Width (degrees) | Risk change (× 10⁻⁶) | Selected |
| --- | --- | --- | --- |
| 0 | 0 | 0.000 | Yes |
| 0.35 | 0.035 | 37.504 | No |
| 0.5 | 0.05 | 1281.023 | No |
| 0.75 | 0.075 | 4379.949 | No |
| 1 | 0.1 | 6220.413 | No |
| 1.5 | 0.15 | 8391.090 | No |
| 2 | 0.2 | 9604.518 | No |
| 3 | 0.3 | 10861.977 | No |

The selected width is 0°: no Gaussian kernel is applied to the final map. Every positive candidate increases cross-seed prediction risk. This result is consistent with a stable, concentrated near-receptor feature being blurred by a global kernel; it does not establish that remote low-density portions contain no sampling noise. For the tested positive candidates, east–west kernel width varies with latitude, so these are angular display kernels, not isotropic physical diffusion operators.

The final display field is linearly interpolated at four times the native sample density and rendered with continuous filled contours before applying logarithmic colors. Coefficients and display density remain nonnegative, and the area integral is conserved by renormalization. Interpolation redistributes display values across cell boundaries and can produce positive values beside originally zero cells; those values are not additional modeled particle samples. No cubic interpolation or interpolation in logarithmic data space is used.

For map comparison, corrected cell coefficients are divided by spherical cell area. The resulting sensitivity density has units of ppm per (µmol m⁻² s⁻¹) per km². Integrating this density over area recovers the coefficient total. This definition makes color values comparable between 0.25° and 0.1° grids. Figure 3 displays density; regional tables use integrated coefficients. The color scale spans 10⁻⁷ to 0.03 in those density units; 0.045% of the display integral falls below its visible lower limit, and 0.001% lies outside the map frame. The underlying unthresholded field remains available.

### Indonesian geographic context

All Indonesian land and province outlines in the revised maps use the user's established provincial GeoJSON asset. It contains 38 features in WGS 84 coordinates. 5 invalid geometries were repaired in memory with a documented validity operation; the original asset was not edited. The file checksum is retained in map metadata. The asset's publication vintage is not supplied, so its administrative detail is context rather than a verified reconstruction of 2019 boundaries. Natural Earth supplies only neighboring countries, excluding Indonesia.

## Results

### Revised spatial influence and comparison with the first map

Figure 3 shows the updated central footprint. Its strongest regional influence extends southeastward from BKT across Sumatra, with weaker offshore sensitivity. The map describes modeled transport pathways and relative sensitivity to hypothetical surface fluxes. Visible ocean cells are retained because atmospheric transport is not constrained by the coastline. A smoother edge is not evidence that transport is known precisely at that edge.

![Continuous ensemble-mean BKT footprint using the established Indonesia GeoJSON.](outputs/hysplit/refinement/analysis/figures/figure_03_spatial_footprint.png)

**Figure 3.** Continuous display of the corrected, time-integrated ensemble-mean HYSPLIT-STILT footprint for BKT, 26 September 2019 01:00 UTC, with a 72-hour backward window. The three runs each emitted 10,020 particles. Color encodes surface-flux sensitivity per km² using the stated logarithmic scale. Display reconstruction uses a Gaussian width of 0° and linear interpolation; quantitative results use the unsmoothed 0.1° coefficients. The star marks BKT at 30 m AGL. Indonesian boundaries use the established provincial GeoJSON. NOAA GDAS1 meteorology remains 1°.

**Table 5. Unsmoothed ensemble-mean footprint diagnostics.** Geographic shares use cell-center assignment; the near-receptor zone is reported separately for consistent directional interpretation.

| Diagnostic | Value |
| --- | --- |
| Integrated sensitivity [ppm / (µmol m⁻² s⁻¹)] | 11.364 |
| SE beyond 25 km (% of total) | 69.4 |
| Within 25 km (%) | 19.4 |
| Within 100 km (%) | 31.0 |
| Within 250 km (%) | 57.1 |
| Sensitivity-weighted median distance (km) | 229 |
| 90th-percentile distance (km) | 456 |
| Median backward lag (h) | 32 |
| 90th-percentile backward lag (h) | 60 |

Figure 4 retains the distance-by-direction decomposition, including the native receptor cell. That receptor-cell category is a grid-dependent diagnostic; comparisons between grid spacings should use the fixed-radius quantities in Tables 5 and 6 instead.

![Direction and distance decomposition of the revised footprint.](outputs/hysplit/refinement/analysis/figures/figure_05_sector_distance.png)

**Figure 4.** Percentage of corrected ensemble-mean sensitivity by distance band and bearing from BKT for the 72-hour window ending 26 September 2019 01:00 UTC. Values use raw 0.1° cell centers and spherical distances. “At receptor” identifies the native cell centered on BKT. Unlabelled cells contribute less than the displayed annotation threshold; the source table distinguishes small positive values from true zero.

### Temporal influence

The most recent 24 hours contain 38.2% of the sensitivity, hours 25–48 contain 37.2%, and hours 49–72 contain 24.6%. Half the total occurs within 32 hours and 90% within 60 hours. These percentages describe the finite modeled backward window. They do not prove that earlier fluxes or lateral boundary conditions are negligible.

![Temporal sensitivity and cumulative backward lag.](outputs/hysplit/refinement/analysis/figures/figure_04_lag_sensitivity.png)

**Figure 5.** Six-hour sensitivity shares and cumulative hourly sensitivity of the corrected ensemble-mean BKT footprint. The receptor is 26 September 2019 01:00 UTC. Dashed lines mark the median lag. Percentages use the complete 72-hour coefficient total; they are descriptive weights rather than probabilities of source attribution.

### Numerical reproducibility and structural sensitivity

The three seeded runs produce southeast-beyond-25-km shares of 69.3–69.6% and total sensitivities of 11.333–11.409 ppm per (µmol m⁻² s⁻¹). The grid, particle-count and height contrasts are kept separate from this seed range. Table 6 compares normalized spatial patterns after conservative area-overlap remapping to a common 1° diagnostic grid. This metric removes output-cell-size differences from the comparison while retaining regional displacement.

**Table 6. Changes relative to the 10,000-requested-particle, seed-0, 30 m, 0.1° run.** Total variation is half the sum of absolute differences between normalized common-grid coefficients, expressed as a percentage; zero means identical regional shape. It is not a fraction of the observed gases explained by the model.

| Experiment | Total change (%) | Regional shape variation (%) |
| --- | --- | --- |
| Original pilot | -1.24 | 2.83 |
| 2,000 requested | -0.88 | 1.16 |
| 10,000 seed B | -0.67 | 0.68 |
| 10,000 seed C | -0.52 | 0.78 |
| Coarse-grid test | -0.00 | 1.42 |
| Height scenario | -2.59 | 1.95 |

The -2.59% change in integrated sensitivity for the 60 m scenario illustrates the dependence on how the station inlet is represented. The 0.25° grid contrast changes the total by -0.004% and the common-grid shape by 1.42%. These comparisons evaluate implementation and representation choices under GDAS1. They cannot establish model accuracy in BKT's mountainous terrain.

![Original and revised footprint maps using matched geographic context and colors.](outputs/hysplit/refinement/analysis/figures/figure_06_before_after.png)

**Figure 6.** Original 0.25° gridded footprint and revised smooth ensemble display for the same BKT receptor and backward window. Both panels apply the emitted-particle normalization correction and display sensitivity density with identical map extent, geographic assets and color limits. The original field remains unsmoothed to expose its sampling grid. The revised panel combines three 0.1° runs and the selected display reconstruction.

![Numerical sensitivity experiments and bandwidth selection.](outputs/hysplit/refinement/analysis/figures/figure_07_robustness.png)

**Figure 7.** Upper panel: southeast sensitivity beyond 25 km for the six reruns. A–C denote distinct random seeds; “coarse” changes only the output grid and “60 m” changes only release height. Lower panel: cross-seed quadratic risk relative to no Gaussian kernel, with the selected bandwidth marked. Lower risk supports display reproducibility within these simulations, not independent transport skill.

## Interpretation, uncertainty and implications

The revised map is appropriate for examining the broad regional footprint and selecting flux datasets for subsequent analysis. The larger ensemble samples more of the stochastic particle distribution and reduces reliance on individual trajectories. The bandwidth test makes a display choice auditable rather than choosing smoothness solely by appearance. Conservation checks ensure that the display does not create additional integrated sensitivity.

Several alternative explanations remain for the elevated observed gases: background variability, local ecosystem exchange, regional fossil emissions, biomass burning, wetlands, agriculture and changes in mixing depth. The archive observations establish receptor context but cannot distinguish these mechanisms through this footprint alone. CO co-elevation is not proof of fire influence, and a transport connection to a place does not establish the flux from that place.

The seed range only characterizes finite-particle variability conditional on the selected driver and configuration. It excludes meteorological error, unresolved terrain, transport-physics choices, timing convention, instrumental error and emission uncertainty. The gridded model still does not resolve local valley flow or hyper-near-field mixing around the inlet. Neither the narrower plotting cells nor a smooth image removes those limitations. Quantitative source estimation must include flux and background uncertainty as well as a transport-error treatment [5].

The conclusions apply to one selected receptor hour. No multi-season performance, emission inversion, causal attribution or independent observed-versus-modeled concentration validation has been completed. The 72-hour cutoff may omit older source influence. Coastlines and provincial borders provide context and do not constrain atmospheric motion. Small-scale contours are a reconstruction for display and should not be used as precise administrative or facility-level influence boundaries.

## Conclusions and next scientific steps

The requested revision now includes new transport simulations, a correction for emitted-particle normalization, an ensemble analysis, particle/grid/height sensitivity tests and a continuously rendered Figure 3 using the established Indonesia GeoJSON. The southeast regional pathway remains the central feature of this event, with its magnitude and numerical sensitivity reported explicitly.

The next scientific priority is to test higher-resolution meteorology and station representation across multiple receptor hours. Then convolve the unsmoothed hourly footprint with temporally matched CO₂ and CH₄ fluxes, estimate background independently, and compare modeled enhancements with observations. An inversion should follow only after those comparisons and an error model are available.

## References

1. NOAA Air Resources Laboratory. *Configuring STILT options in HYSPLIT*. [Official configuration guide](https://www.ready.noaa.gov/documents/Tutorial/html/stilt_setup.html). Accessed 5 September 2026.
2. Lin, J. C., Gerbig, C., Wofsy, S. C., Andrews, A. E., Daube, B. C., Davis, K. J., and Grainger, C. A. (2003). A near-field tool for simulating the upstream influence of atmospheric observations: The Stochastic Time-Inverted Lagrangian Transport (STILT) model. *Journal of Geophysical Research: Atmospheres*, 108(D16), 4493. [doi:10.1029/2002JD003161](https://doi.org/10.1029/2002JD003161).
3. NOAA Air Resources Laboratory. *Meteorological data archives: GDAS one-degree archive*. [Archive description](https://hysplit2.arl.noaa.gov/archives.php). Accessed 5 September 2026.
4. Fasoli, B., Lin, J. C., Bowling, D. R., Mitchell, L., and Mendoza, D. (2018). Simulating atmospheric tracer concentrations for spatially distributed receptors: updates to the Stochastic Time-Inverted Lagrangian Transport model's R interface (STILT-R version 2). *Geoscientific Model Development*, 11, 2813–2824. [doi:10.5194/gmd-11-2813-2018](https://gmd.copernicus.org/articles/11/2813/2018/).
5. Lin, J. C., and Gerbig, C. (2005). Accounting for the effect of transport errors on tracer inversions. *Geophysical Research Letters*, 32, L01802. [doi:10.1029/2004GL021127](https://doi.org/10.1029/2004GL021127).
6. NOAA Air Resources Laboratory. *Variables not set in the graphical interface*: random seeds and particle diagnostic output. [HYSPLIT user guide](https://www.ready.noaa.gov/hysplitusersguide/S640.htm). Accessed 5 September 2026.

## Technical methods and quality assurance

### Input provenance and output contracts

The analysis uses `ghg_common.load_station("BKT")` with project flag application and does not parse the raw archive directly. UTC is used internally; WIB is UTC+7. Longitudes use the −180° to 180° convention. Native model files and the original report are retained separately from revised derived products.

Meteorological input: `data/hysplit/met/gdas1.sep19.w4`, 598,888,640 bytes, SHA-256 `319a1acd675e3ab5564d04d9071776787441b275c58f7a8cb68c0f31295eb073`. Its provider, source URL and retrieval time are preserved in the corresponding provenance record. The Indonesian boundary is `.assets/indonesia_38prov.geojson` in the shared HDD2 asset directory, with SHA-256 `95b33f62c93c83206f7d4cc573d55142b721738de6a7f32790dde2092cd4082b`. An `INDONESIA_GEOJSON` environment override is available; maps fail if the selected boundary asset is missing rather than substituting another Indonesian geometry.

**Table 7. Reproducible analysis products.** Paths below are relative to `outputs/hysplit/refinement/analysis`. All quantitative headline values trace to these machine-readable outputs.

| Product | Purpose |
|---|---|
| `ensemble_mean.nc` | Corrected, unsmoothed hourly ensemble coefficients |
| `ensemble_hourly.csv.gz` | Positive cell-hour coefficients and UTC lag |
| `ensemble_aggregate.csv` | Time-integrated coefficients by cell |
| `display_surface.nc` | Reconstructed density for display only |
| `tables/experiment_summary.csv` | Actual counts, settings and each run's diagnostics |
| `tables/seed_spread.csv` | Three-seed ranges and descriptive standard deviations |
| `tables/bandwidth_cross_validation.csv` | Candidate and fold-level display selection scores |
| `tables/smoothing_sensitivity.csv` | Conservation and redistribution by bandwidth |
| `tables/controlled_probes.csv` | Normalization and output-diagnostic controls |
| `tables/observation_context_summary.csv` | Observation, coverage, quantiles and ranks |
| `tables/lag_sensitivity_hourly.csv` | Hourly and cumulative sensitivity shares |
| `tables/sector_distance_share.csv` | Native-grid direction-by-distance decomposition |
| `map_metadata.json` | Boundary provenance, display units and reconstruction |

### Validation criteria and results

Each native run is checked for complete expected hourly coverage, nonnegative finite values, CSV/NetCDF/aggregate reconciliation, positive sensitivity away from domain edges, model settings, fatal log messages and the meteorological checksum. Corrected ensemble coefficients are reconciled independently across tabular and NetCDF representations. Conservative remapping and display reconstruction are tested with synthetic point fields and spherical-area identities. Distinct seeded fields are required to differ.

The selected Gaussian stage redistributes 0.00% of the integrated coefficient weight across native cells, measured as half the L₁ difference from the unsmoothed mean: this is zero because no kernel is selected. Linear display interpolation still changes the rendered surface and is not included in this native-cell redistribution diagnostic. No display-derived regional statistic replaces the raw analysis. The unthresholded display area integral and raw total agree within relative tolerance 10⁻¹⁰.

The automated checks establish numerical consistency and reproducibility within the stated experiment. They do not validate atmospheric transport against independent concentration data. The final PDF is compiled with vector figure companions, checked for typesetting errors, extracted to text and rendered for visual inspection. Repository document, translation, PDF and slide gates are also required before delivery.

### Reproduction

Use the shared HDD2 Python environment. The model stage skips completed runs and refuses to overwrite partial outputs. The main report is expanded from the Markdown narrative template and generated tables; LaTeX remains a build artifact.

```bash
# Set HYSPLIT_HOME to the installed model directory first.
python scripts/a39_bkt_refinement.py model --jobs 3
python scripts/a39_bkt_refinement.py analyze
python scripts/a40_bkt_refinement_report.py
python scripts/a14_latex.py BKT_HYSPLIT_STILT_Footprint_Report
python scripts/validate_bkt_footprint_report.py --refinement
python -m unittest tests.test_bkt_footprint tests.test_bkt_refinement
bash scripts/verify_all.sh
```
