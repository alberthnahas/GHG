## Appendix. Transport completeness and unresolved mixing uncertainty

{{T_DECISION}}

This benchmark concerns the passive transport operator shared by surface-flux calculations for all three gases. It does not refit emissions, use methane residuals to choose settings, or establish a complete concentration budget. Numerical completeness, sensitivity to assumed physics, and agreement with meteorological observations answer different questions and are assessed separately.

### Domain boundaries and backward duration

Of {{T_BASE_N}} original five-day receptor runs, {{T_BASE_FAIL}} failed the existing 95% endpoint-retention screen. In the most severe case, released on 6 October 2019 at 06:00 UTC, only {{T_LOSS_ACTIVE}} of {{T_EMITTED}} emitted particles remained active after 120 hours. Hourly records bracket the loss of each inactive particle between its final active location and the next inactive record. All losses were last recorded nearest the eastern meteorological boundary; the model also reported a spatial-domain exit. Inactive coordinates are placeholders, not air parcels arriving at the equator and Greenwich meridian.

The matched domain test expands the same quarter-degree GFS meteorology from 75–130° E, 20° S–20° N to 50–160° E, 40° S–30° N. Variables, hybrid levels, timestamps and resolution remain unchanged. {{T_PACKING_NOTICE}} The initial footprint grid is retained for the first contrast; a separate wider footprint grid tests omitted surface sensitivity. These comparisons distinguish different forms of truncation, subject to the stated packing limitation.

**Table 18. Domain-completeness experiment for the 6 October 2019 receptor.** All runs extend 120 hours backward and use the same release, physics and actual-particle normalization. Integrated sensitivity has units ppm per (µmol m⁻² s⁻¹); it is the response to a unit flux in every included cell and hour, not a measured concentration. Edge share is the fraction on the outermost footprint cells.

{{T_DOMAIN_TABLE}}

{{T_DOMAIN_INTERPRETATION}}

![Domain retention and accumulated sensitivity](outputs/hysplit/benchmark/figures/domain_completeness.png)

**Figure 23.** Particle retention and accumulated surface-flux sensitivity for the 6 October 2019, 06:00 UTC BKT receptor. The denominator is the actual emitted-particle count. Retention is a meteorological-domain diagnostic; accumulated sensitivity additionally depends on the footprint grid and backward duration. GFS-driven HYSPLIT-STILT simulations, with hourly diagnostic records and identical non-domain settings.

Four separate controls at 06:00 and 18:00 UTC on 9 and 23 September retained all emitted particles through 72 hours, with no sensitivity on the outermost footprint cells. Their fields match the corresponding first 72 hours of the original five-day runs exactly. The additional two days supply {{T_DURATION_MIN}}–{{T_DURATION_MAX}}% of the original five-day integrated sensitivity. Thus, three days is a bounded physics-comparison window, not a demonstrated convergence horizon or a recommended shortening of the five-day calculation. Even five-day particle retention cannot establish that older transport is negligible.

### Mixing depth, release height and stochastic sampling

The predeclared contrasts change one assumption at a time: the minimum mixing depth from 250 m to 100 or 50 m; modified-Richardson-number mixing depth to the meteorological model's native depth; receptor height from 30 to 60 m above model ground; and convection treatments including a convective available potential energy (CAPE) threshold. The Richardson-number approach compares thermal stratification with wind shear. Four matched receptor times represent two dates and two clock periods, 13:00 and 01:00 WIB. They are not independent seasonal replicates. Each run actually emits {{T_EMITTED}} particles; coefficients are normalized to that count. Two further unchanged-physics seed repeats at each time describe finite-particle variation without supplying full uncertainty intervals for every perturbation.

**Table 19. Matched three-day transport sensitivities.** Ratios compare integrated sensitivity with the same-time control. The range spans the four receptor times, not a confidence interval. The spatial absolute-difference measure is the sum of absolute cell differences divided by the control's integrated sensitivity, in percent; it combines changes in magnitude and location. Seed controls describe numerical sampling, not atmospheric uncertainty.

{{T_PHYSICS_TABLE}}

{{T_MIXING_INTERPRETATION}}

![Matched transport sensitivities](outputs/hysplit/benchmark/figures/physics_sensitivity.png)

**Figure 24.** Integrated-sensitivity ratios under one-factor transport perturbations at BKT on 9 and 23 September 2019 (UTC dates). Legend dates and times are in WIB; the nighttime releases therefore fall on 10 and 24 September locally. Each marker represents a matched receptor time; the reference value of one denotes no change. Control-seed ranges provide context for finite-particle variation. These are model responses, not demonstrated improvements in transport skill.

A fixed-site model diagnostic with a 50 m floor places mixing depth below 250 m at {{T_NIGHT_FLOOR}}% of the sampled 17:00–07:00 WIB clock-period times under the modified-Richardson-number method. The diagnosis uses three-hourly meteorology over 9 September–6 October and includes {{T_NIGHT_N}} such samples. It explains why the imposed floor can matter, especially during shallow nocturnal mixing. It is not an observed boundary-layer height and uses different turbulence time-scale assumptions from the full footprint calculation. Lowering the floor is therefore a physically motivated sensitivity test, not a validated correction for mountain-valley exchange.

### Convection compatibility and executed response

The original requested Grell treatment requires convective flux fields that are absent from the inspected GFS archive. The archive also lacks a supplied convective available potential energy (CAPE) field. The alternative positive threshold requests profile-derived CAPE and enhanced cloud-layer redistribution above 500 J kg⁻¹ [17]. {{T_CONVECTION_INTERPRETATION}} The model explicitly disables its WRF-specific vertical interpolation for these non-WRF inputs. A requested option is not evidence that its associated physics was active; conversely, a null contrast does not establish that real atmospheric convection was absent.

### Observation-based evaluation and its independence limits

Public Integrated Global Radiosonde Archive (IGRA) version 2.2 records were matched to GFS at their observation locations and nominal UTC times over 9 September–6 October 2019 [18, 19]. Standard levels of 925, 850, 700, 500 and 300 hPa were used where present. Meteorological wind direction was converted to eastward and northward components. Model fields were sampled bilinearly and interpolated in log pressure using the archived pressure variable, without vertical extrapolation. Missing and provider-rejected values remain unavailable; they were not removed because of model disagreement.

For wind, the vector root-mean-square error (RMSE) is the square root of the mean of $(u_m-u_o)^2+(v_m-v_o)^2$, first averaged across available levels within each sounding, then across soundings within a day and across days. Here, $u$ and $v$ are the eastward and northward wind components in m s⁻¹; subscripts $m$ and $o$ denote model and observation. Temperature uses the corresponding scalar squared error. This equal-day estimator prevents vertical sampling density from creating false replication. The 95% intervals use 3,000 circular moving-block resamples of three consecutive daily summaries. They describe sampling variability in this period, not all observational and model uncertainty.

**Table 20. GFS forcing agreement with Padang profiles.** Errors are model minus observation. Wind and temperature have different valid sounding counts. Confidence intervals use three-day blocks and do not establish assimilation independence.

{{T_PROFILE_TABLE}}

![Profile evaluation across pressure levels](outputs/hysplit/benchmark/figures/profile_evaluation.png)

**Figure 25.** Pressure-resolved wind-vector RMSE and temperature bias for the Padang observation-based check, 9 September–6 October 2019. Available-level results are compared with the subset having complete five-level wind-and-temperature profiles. Each pressure-level estimate gives equal weight to daily summaries; whiskers are pointwise 95% intervals from three-day block resampling, not simultaneous intervals across levels. Lines connect diagnostic levels, not additional observations. Aggregate uncertainty and sounding counts are reported in Table 20. Neither this coastal profile nor its model counterpart is treated as a direct BKT mixing-depth measurement.

{{T_PROFILE_SENSITIVITY}} Pekanbaru contributes only {{T_PEKA_PAIRS}} selected pressure-level wind pairs on {{T_PEKA_DAYS}} days and no paired temperature; its results are retained but cannot support a second-station performance claim. IGRA fixed-station coordinates reflect the latest inventory rather than a reconstructed historical launch location [19]. Historical-position and one-hour timing perturbations therefore test representativeness rather than silently assuming exact collocation. Balloon drift and level-dependent ascent time remain unresolved.

The observations were not used to tune this benchmark, but possible assimilation into GFS has not been excluded. This is an observation-based forcing check, not demonstrably assimilation-independent validation. No co-located BKT turbulence, mixing-depth or tracer-release observations were available to select the mixing or receptor-height configuration. Small mean wind bias also cannot exclude substantial trajectory displacement, especially when errors are temporally correlated.

### Decision and remaining evidence

{{T_RECOMMENDATION}}

The next atmospheric validation requires co-located wind and stability profiles or boundary-layer observations across day and night, plus documented assimilation status or withheld observations for genuinely independent forcing evaluation. Replicated perturbation ensembles and further domain/duration expansion are needed before translating sensitivity changes into transport-error bounds. The present findings do not justify a revised emission inversion or a claim that a particular mixing or convection setting is more accurate.
