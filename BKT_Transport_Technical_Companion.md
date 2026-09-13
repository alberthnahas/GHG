# Transport technical companion for the Bukit Kototabang source studies

## Purpose and scope

This companion documents the numerical and meteorological basis of the two Bukit Kototabang (BKT) source studies: the 26 September 2019 forward source-influence case and the September–October 2019 methane inversion. It records what the HYSPLIT-STILT transport operator does and does not resolve, how its numerical completeness was established, how two meteorological drivers compare, and which configuration tests were run. Nothing here attributes methane or carbon dioxide to a source; the scientific results are in the two reports.

The companion has five parts. Section 1 describes the 2026 simulation revision that supplies the transport ensembles used by both reports. Section 2 documents the ERA5 driver and its comparison with GFS. Sections 3 and 4 retain the gas-independent transport benchmark and the full-ensemble domain correction that motivated the revision. Section 5 records the screen of a finer regional reanalysis that did not pass conversion.

## 1. Simulation revision campaign

The revision replaced the single-seed, 540-particle, regional-domain transport ensemble of the original inversion with the configuration in Table 1. Every run uses HYSPLIT 5.4.2 in STILT mode with the settings of the original studies: modified Richardson-number mixing depth with a 250 m minimum, Hanna turbulence, a variable Lagrangian timescale, a 30 m release above model ground unless stated, and hourly output on a 0.25° accumulation grid. Coefficients are normalized to the actual emitted count. Every run also records a fixed 1,000 m concentration layer above the STILT surface layer; the surface layer is bit-identical with and without it.

**Table 1. Simulation revision campaign.** GFS quarter-degree meteorology, 50°–160° E, 40° S–30° N; 60° by 100° footprint grid; 120 h backward. Run time is the median wall-clock minutes per run on a shared workstation.

| Receptors | Seeds | Requested particles | Release (m AGL) | Runs | Run time (min) |
| --- | --- | --- | --- | --- | --- |
| 05, 07 and 08 UTC on 28 days | 1 | 2,000 | 30 | 84 | 87 |
| 52 twice-daily inversion receptors | 3 (0, −10, −20) | 2,000 | 30 | 156 | 80 |
| 26 Sep 2019 01:00 UTC forward case | 3 | 10,000 | 30 | 3 | 406 |
| 26 Sep 2019 01:00 UTC forward case | 1 | 10,000 | 80 | 1 | 408 |
| 4 benchmark anchors | 3 | 2,000 | 80 | 12 | 81 |

All 256 runs completed and every run retained 100% of its particles at 120 h. The seed coefficient of variation of integrated sensitivity across the 52 inversion receptors has median 1.4% and maximum 4.2% (Figure 1a). On the original domain, 25 of the 52 hours had lost more than 5% of their particles; on the widened domain none does (Figure 1b).

![Numerical spread and particle retention.](outputs/hysplit/revision/figures/figure_R01_numerics_retention.png)

**Figure 1.** Seed coefficient of variation of integrated surface sensitivity for each of the 52 inversion receptor hours (a), and particle retention at 120 h on the original and widened meteorological domains (b).

**Table 2. Seed spread across the three-member ensembles.** Coefficient of variation of integrated surface sensitivity across seeds, and the range of the within-50 km share, summarized over receptors.

| Family | Receptors | Median seed CV (%) | Maximum seed CV (%) | Median within-50 km range (points) |
| --- | --- | --- | --- | --- |
| Inversion receptors, 30 m | 52 | 1.43 | 4.19 | 0.71 |
| Forward case, 30 m | 1 | 0.53 | 0.53 | 0.28 |
| Anchors, 80 m | 4 | 1.17 | 1.70 | 0.53 |

The 80 m release places the inlet at its true altitude above the nearest GFS grid-cell terrain of 816 m. At the four benchmark anchors it changes integrated sensitivity by a median factor of 0.960 (range 0.930–1.052) with a cell-level spatial difference of 22%, comparable to the seed-to-seed spatial difference of the benchmark controls (Figure 2a, Table 3). Release height is a few-percent effect at this station and does not need to be carried as a separate uncertainty term.

**Table 3. Terrain-matched release at the benchmark anchors.** Ratio of integrated sensitivity at 80 m to 30 m release and the cell-level absolute difference, per seed.

| Receptor (UTC) | Seed | Ratio 80 m / 30 m | Spatial difference (%) |
| --- | --- | --- | --- |
| 09 Sep 2019 06:00 | 0 | 0.956 | 20.2 |
| 09 Sep 2019 06:00 | -10 | 0.988 | 19.8 |
| 09 Sep 2019 06:00 | -20 | 0.972 | 18.8 |
| 09 Sep 2019 18:00 | 0 | 0.930 | 18.5 |
| 09 Sep 2019 18:00 | -10 | 0.950 | 19.1 |
| 09 Sep 2019 18:00 | -20 | 0.948 | 18.2 |
| 23 Sep 2019 06:00 | 0 | 0.986 | 27.8 |
| 23 Sep 2019 06:00 | -10 | 1.052 | 30.3 |
| 23 Sep 2019 06:00 | -20 | 0.964 | 25.7 |
| 23 Sep 2019 18:00 | 0 | 0.957 | 23.4 |
| 23 Sep 2019 18:00 | -10 | 0.996 | 23.8 |
| 23 Sep 2019 18:00 | -20 | 0.954 | 23.7 |

The afternoon runs at 05, 07 and 08 UTC combine with the 06 UTC ensemble mean into a 12:00–15:00 WIB window mean for each day (Figure 2b). Members of the window differ by a median 3.2% in integrated sensitivity over 26 days, small against the day-to-day range, so a window mean is a stable receptor for a daytime-only inversion design.

![Release height and the afternoon window.](outputs/hysplit/revision/figures/figure_R02_release_height_afternoon_window.png)

**Figure 2.** Sensitivity ratio of the 80 m release to the 30 m release at the four anchors, three seeds each (a), and integrated sensitivity of the 05, 06, 07 and 08 UTC footprints with their 12:00–15:00 WIB window mean for each day of the study period (b).

Convective redistribution is not part of any run. HYSPLIT's Grell option requires convective mass-flux fields that neither the GFS nor the ERA5 archive carries, and the model reports convective mixing inactive in every log; the CAPE-threshold alternative in the benchmark produced no response for the same reason. All footprints in both reports therefore assume no parameterized convective venting, which is a material limitation in equatorial Sumatra.

## 2. Meteorological drivers

### GFS

The principal driver is NOAA's quarter-degree GFS archive in ARL format: three-hourly fields on 55 hybrid levels, concatenated from successive analysis and three-hour forecast cycles, cropped server-side to 50°–160° E, 40° S–30° N [3]. It is a pseudo-analysis rather than a homogeneous reanalysis.

### ERA5

ECMWF ERA5 [20] was obtained from the Copernicus Climate Data Store as hourly GRIB on 16 pressure levels from 1000 to 100 hPa with the surface analysis and accumulated-flux fields that HYSPLIT's converter expects, over 70°–140° E, 25° S–20° N, and converted with NOAA's `era52arl` utility. Two properties of the conversion matter scientifically. First, the pressure-level product gives the lowest layers at 925, 900 and 850 hPa above an 865 m station, coarser near the surface than the hybrid GFS levels. Second, ECMWF's accumulated sensible and latent heat fluxes are positive downward, whereas HYSPLIT's stability calculation takes them positive upward; the converter's stock field map only rescales them, and the sign was corrected in the map used here. With the stock map HYSPLIT received a strongly negative daytime heat flux, treated the daytime boundary layer as stable, and produced 1.3 to 3.8 times the GFS surface sensitivity; that artefact is documented so that it is not repeated, and no result in either report uses those files. The ERA5 footprint grid is 40° by 60°, inside the meteorological box; at the receptors compared below the GFS runs place no sensitivity outside it.

### Driver comparison at matched receptors

**Table 4. GFS and ERA5 footprints at matched receptors.** Three seeds per driver; ratio and spatial difference use the ERA5 grid cells, on which the GFS runs place all of their sensitivity.

| Receptor (UTC) | Case | ERA5/GFS sensitivity (seed range) | Spatial difference (%) | Within 500 km, ERA5 / GFS (%) | Oldest 24 h, ERA5 / GFS (%) |
| --- | --- | --- | --- | --- | --- |
| 09 Sep 2019 06:00 | anchor | 1.43 (1.41–1.46) | 93 | 59 / 65 | 14.4 / 10.3 |
| 09 Sep 2019 18:00 | anchor | 1.84 (1.80–1.86) | 120 | 61 / 74 | 8.2 / 7.5 |
| 23 Sep 2019 06:00 | anchor | 1.18 (1.16–1.21) | 94 | 72 / 47 | 6.2 / 9.8 |
| 23 Sep 2019 18:00 | anchor | 1.21 (1.17–1.24) | 74 | 75 / 66 | 10.2 / 7.6 |
| 26 Sep 2019 01:00 | forward | 1.17 (1.17–1.18) | 106 | 48 / 53 | 17.4 / 9.1 |

At the four inversion anchors and the forward case, with seeds, particle counts, release height and STILT settings matched, ERA5 gives 1.16 to 1.86 times the GFS integrated surface sensitivity, with seed spread below 2% under both drivers. The cell-level absolute difference is 74 to 120% of the GFS total: the two drivers place the footprint in largely different quarter-degree cells even where their regional shares agree. On 9 September 2019 the ERA5 boundary-layer height at BKT peaks at 919 m against 1306 m in GFS, and ERA5's model terrain at the station is 656 m against 816 m; a shallower mixed layer concentrates the same residence time into more surface sensitivity. The comparison quantifies transport uncertainty; it does not establish which driver is closer to the atmosphere, and the profile check in Section 3 applies to GFS only.

## 3. Transport completeness and unresolved mixing uncertainty

**The expanded domain restores particle completeness in the severe-loss case, but no mixing, receptor-height or convection configuration is independently validated as superior.** Endpoint retention increases from 17.2% to 100.0%. The observational check constrains meteorological forcing errors, not the full surface-flux operator.

This benchmark concerns the passive transport operator shared by surface-flux calculations for all three gases. It does not refit emissions, use methane residuals to choose settings, or establish a complete concentration budget. Numerical completeness, sensitivity to assumed physics, and agreement with meteorological observations answer different questions and are assessed separately.

### Domain boundaries and backward duration

Of 52 original five-day receptor runs, 25 failed the existing 95% endpoint-retention screen. In the most severe case, released on 6 October 2019 at 06:00 UTC, only 93 of 540 emitted particles remained active after 120 hours. Hourly records bracket the loss of each inactive particle between its final active location and the next inactive record. All losses were last recorded nearest the eastern meteorological boundary; the model also reported a spatial-domain exit. Inactive coordinates are placeholders, not air parcels arriving at the equator and Greenwich meridian.

The matched domain test expands the same quarter-degree GFS meteorology from 75–130° E, 20° S–20° N to 50–160° E, 40° S–30° N. Variables, hybrid levels, timestamps and resolution remain unchanged. All 16,704 shared-domain variable–level–time fields agree within the sum of their two packing increments. Some are not bit-identical because the larger extraction is repacked; changes in trajectory detail and shared-grid sensitivity cannot be attributed solely to domain extent. The initial footprint grid is retained for the first contrast; a separate wider footprint grid tests omitted surface sensitivity. These comparisons distinguish different forms of truncation, subject to the stated packing limitation.

**Table 5. Domain-completeness experiment for the 6 October 2019 receptor.** All runs extend 120 hours backward and use the same release, physics and actual-particle normalization. Integrated sensitivity has units ppm per (µmol m⁻² s⁻¹); it is the response to a unit flux in every included cell and hour, not a measured concentration. Edge share is the fraction on the outermost footprint cells.

| Configuration | Active (%) | Sensitivity | Outside old grid (%) | Edge (%) |
| --- | --- | --- | --- | --- |
| Original domains | 17.2 | 3.964 | 0.00 | 0.458 |
| Wider meteorology | 100.0 | 3.870 | 0.00 | 0.429 |
| Both domains wider | 100.0 | 4.325 | 10.51 | 0.000 |

The wider footprint grid places 10.51% of its integrated sensitivity outside the original output grid. Its outermost cells contain 0.000% of sensitivity, and the closest surviving endpoint is 1166 km from the expanded meteorological boundary. The oldest 24 hours still supply 14.7% of five-day sensitivity. On the original output grid, wider meteorology changes integrated sensitivity by -2.4%; this is not a pure domain-effect estimate because the meteorological packing also changes. In contrast, expanding only the output grid preserves every shared cell-hour coefficient exactly. This establishes improved numerical coverage for this case, not five-day temporal convergence, atmospheric accuracy, or completeness of all original receptor runs.

![Domain retention and accumulated sensitivity](outputs/hysplit/benchmark/figures/domain_completeness.png)

**Figure 3.** Particle retention and accumulated surface-flux sensitivity for the 6 October 2019, 06:00 UTC BKT receptor. The denominator is the actual emitted-particle count. Retention is a meteorological-domain diagnostic; accumulated sensitivity additionally depends on the footprint grid and backward duration. GFS-driven HYSPLIT-STILT simulations, with hourly diagnostic records and identical non-domain settings.

Four separate controls at 06:00 and 18:00 UTC on 9 and 23 September retained all emitted particles through 72 hours, with no sensitivity on the outermost footprint cells. Their fields match the corresponding first 72 hours of the original five-day runs exactly. The additional two days supply 15.8–21.8% of the original five-day integrated sensitivity. Thus, three days is a bounded physics-comparison window, not a demonstrated convergence horizon or a recommended shortening of the five-day calculation. Even five-day particle retention cannot establish that older transport is negligible.

### Mixing depth, release height and stochastic sampling

The predeclared contrasts change one assumption at a time: the minimum mixing depth from 250 m to 100 or 50 m; modified-Richardson-number mixing depth to the meteorological model's native depth; receptor height from 30 to 60 m above model ground; and convection treatments including a convective available potential energy (CAPE) threshold. The Richardson-number approach compares thermal stratification with wind shear. Four matched receptor times represent two dates and two clock periods, 13:00 and 01:00 WIB. They are not independent seasonal replicates. Each run actually emits 540 particles; coefficients are normalized to that count. Two further unchanged-physics seed repeats at each time describe finite-particle variation without supplying full uncertainty intervals for every perturbation.

**Table 6. Matched three-day transport sensitivities.** Ratios compare integrated sensitivity with the same-time control. The range spans the four receptor times, not a confidence interval. The spatial absolute-difference measure is the sum of absolute cell differences divided by the control's integrated sensitivity, in percent; it combines changes in magnitude and location. Seed controls describe numerical sampling, not atmospheric uncertainty.

| Contrast | Median ratio | Ratio range | Median spatial difference (%) |
| --- | --- | --- | --- |
| 100 m mixing floor | 1.112 | 0.906–1.472 | 40.4 |
| 50 m mixing floor | 1.059 | 0.826–1.588 | 38.4 |
| Native mixing depth | 0.988 | 0.928–1.034 | 25.0 |
| 60 m receptor | 0.975 | 0.954–1.094 | 26.5 |
| Convection disabled | 1.000 | 1.000–1.000 | 0.0 |
| CAPE threshold: 500 J kg⁻¹ | 1.000 | 1.000–1.000 | 0.0 |
| Unchanged-physics seed repeats | 0.991 | 0.959–1.062 | 23.9 |

The 100 m floor gives sensitivity ratios of 0.91–1.00 at 13:00 WIB and 1.23–1.47 at 01:00 WIB across the two cases in each clock period. The response is not a simple inverse scaling with mixing depth: the floor acts along the entire backward path, changes vertical dispersion and sampling of winds, and changes residence in the surface-sensitive layer. A receptor-height contrast likewise tests model representativeness, not a second observed inlet. Single-seed perturbations and two control-seed repeats characterize sensitivity only; replicated perturbations would be needed for parameter-specific uncertainty. Control-seed ratios span 0.959–1.062, with a median spatial absolute difference of 23.9%. The spatial differences from native mixing depth and receptor height are of a similar scale, whereas the larger nighttime floor responses exceed the observed control-seed variation. This comparison is descriptive, not a significance test.

![Matched transport sensitivities](outputs/hysplit/benchmark/figures/physics_sensitivity.png)

**Figure 4.** Integrated-sensitivity ratios under one-factor transport perturbations at BKT on 9 and 23 September 2019 (UTC dates). Legend dates and times are in WIB; the nighttime releases therefore fall on 10 and 24 September locally. Each marker represents a matched receptor time; the reference value of one denotes no change. Control-seed ranges provide context for finite-particle variation. These are model responses, not demonstrated improvements in transport skill.

A fixed-site model diagnostic with a 50 m floor places mixing depth below 250 m at 100.0% of the sampled 17:00–07:00 WIB clock-period times under the modified-Richardson-number method. The diagnosis uses three-hourly meteorology over 9 September–6 October and includes 112 such samples. It explains why the imposed floor can matter, especially during shallow nocturnal mixing. It is not an observed boundary-layer height and uses different turbulence time-scale assumptions from the full footprint calculation. Lowering the floor is therefore a physically motivated sensitivity test, not a validated correction for mountain-valley exchange.

### Convection compatibility and executed response

The original requested Grell treatment requires convective flux fields that are absent from the inspected GFS archive. The archive also lacks a supplied convective available potential energy (CAPE) field. The alternative positive threshold requests profile-derived CAPE and enhanced cloud-layer redistribution above 500 J kg⁻¹ [17]. Disabling the original requested convection option produces exactly the same cell-hour footprint coefficients at all four receptor times. The positive CAPE-threshold experiment also produces no cell-hour response in these cases; this does not establish whether the threshold was reached. The model explicitly disables its WRF-specific vertical interpolation for these non-WRF inputs. A requested option is not evidence that its associated physics was active; conversely, a null contrast does not establish that real atmospheric convection was absent.

### Observation-based evaluation and its independence limits

Public Integrated Global Radiosonde Archive (IGRA) version 2.2 records were matched to GFS at their observation locations and nominal UTC times over 9 September–6 October 2019 [18, 19]. Standard levels of 925, 850, 700, 500 and 300 hPa were used where present. Meteorological wind direction was converted to eastward and northward components. Model fields were sampled bilinearly and interpolated in log pressure using the archived pressure variable, without vertical extrapolation. Missing and provider-rejected values remain unavailable; they were not removed because of model disagreement.

For wind, the vector root-mean-square error (RMSE) is the square root of the mean of $(u_m-u_o)^2+(v_m-v_o)^2$, first averaged across available levels within each sounding, then across soundings within a day and across days. Here, $u$ and $v$ are the eastward and northward wind components in m s⁻¹; subscripts $m$ and $o$ denote model and observation. Temperature uses the corresponding scalar squared error. This equal-day estimator prevents vertical sampling density from creating false replication. The 95% intervals use 3,000 circular moving-block resamples of three consecutive daily summaries. They describe sampling variability in this period, not all observational and model uncertainty.

**Table 7. GFS forcing agreement with Padang profiles.** Errors are model minus observation. Wind and temperature have different valid sounding counts. Confidence intervals use three-day blocks and do not establish assimilation independence.

| Metric | Estimate | 95% interval | Soundings |
| --- | --- | --- | --- |
| Eastward-wind bias (m s⁻¹) | -0.12 | -0.37–0.17 | 59 |
| Northward-wind bias (m s⁻¹) | 0.25 | 0.09–0.42 | 59 |
| Wind-vector RMSE (m s⁻¹) | 2.77 | 2.17–3.56 | 59 |
| Temperature bias (K) | 0.06 | -0.04–0.15 | 54 |
| Temperature RMSE (K) | 0.69 | 0.62–0.75 | 54 |

![Profile evaluation across pressure levels](outputs/hysplit/benchmark/figures/profile_evaluation.png)

**Figure 5.** Pressure-resolved wind-vector RMSE and temperature bias for the Padang observation-based check, 9 September–6 October 2019. Available-level results are compared with the subset having complete five-level wind-and-temperature profiles. Each pressure-level estimate gives equal weight to daily summaries; whiskers are pointwise 95% intervals from three-day block resampling, not simultaneous intervals across levels. Lines connect diagnostic levels, not additional observations. Aggregate uncertainty and sounding counts are reported in Table 7. Neither this coastal profile nor its model counterpart is treated as a direct BKT mixing-depth measurement.

Nearest-cell, historical-position and one-hour timing alternatives give wind-vector RMSE values of 2.78–2.92 m s⁻¹, compared with 2.77 m s⁻¹ for the primary sampling. Restricting to 53 complete five-level wind-and-temperature profiles lowers wind-vector RMSE to 2.26 m s⁻¹. This coverage sensitivity is larger than the tested small collocation changes and prevents treating the aggregate as invariant to sampling. The wind-only profile on 15 September at 06:00 UTC contributes 31.6% of the aggregate wind mean-square error. Its large mismatch persists under the collocation alternatives. It remains in the primary estimate: missing temperature and model disagreement are not sufficient grounds to reject its winds. Pekanbaru contributes only 4 selected pressure-level wind pairs on 2 days and no paired temperature; its results are retained but cannot support a second-station performance claim. IGRA fixed-station coordinates reflect the latest inventory rather than a reconstructed historical launch location [19]. Historical-position and one-hour timing perturbations therefore test representativeness rather than silently assuming exact collocation. Balloon drift and level-dependent ascent time remain unresolved.

The observations were not used to tune this benchmark, but possible assimilation into GFS has not been excluded. This is an observation-based forcing check, not demonstrably assimilation-independent validation. No co-located BKT turbulence, mixing-depth or tracer-release observations were available to select the mixing or receptor-height configuration. Small mean wind bias also cannot exclude substantial trajectory displacement, especially when errors are temporally correlated.

### Decision and remaining evidence

Prioritize meteorological and footprint-domain completeness before interpreting five-day flux contributions. Apply the expanded-domain check across the full receptor ensemble before rebuilding an inversion operator. Keep the existing baseline settings unchanged while carrying mixing-depth, receptor-height and convection alternatives as explicit model sensitivities. Do not choose a setting solely because it reduces a gas residual or increases integrated sensitivity.

The next atmospheric validation requires co-located wind and stability profiles or boundary-layer observations across day and night, plus documented assimilation status or withheld observations for genuinely independent forcing evaluation. Replicated perturbation ensembles and further domain/duration expansion are needed before translating sensitivity changes into transport-error bounds. The present findings do not justify a revised emission inversion or a claim that a particular mixing or convection setting is more accurate.


<!-- pdf-pagebreak -->

## 4. Full-ensemble domain correction and prior methane-budget convergence

**The widened configuration raises the number of transport-complete receptor hours from 27 to 52 of 52, with median wide-domain particle retention of 100.0%.** For the 27 matched hours, the mean net prior surface-methane contribution changes by -5.38 ppb (-3.7% relative to the original retained-hour mean). This corrects numerical coverage but does not establish atmospheric accuracy or justify refitting the inversion.

The extension reruns all 52 available twice-daily receptors from 9 September to 6 October 2019 with a 50°–160° E, 40° S–30° N meteorological crop and a 60° by 100° footprint grid [3]. It preserves the original five-day transport physics and actual-emitted-particle normalization. This is a matched correction configuration, not a pure domain perturbation: the larger meteorological extraction is repacked, so small shared-field differences accompany the removal of boundary truncation. No gas value selected a rerun, and no inversion was refitted.

![Full-ensemble particle retention and surface-flux sensitivity under the original and widened domains.](outputs/hysplit/domain_budget_extension/figures/domain_ensemble.png)

**Figure 6.** Original and widened-domain diagnostics for 52 BKT receptors, 9 September–6 October 2019. Panel (a) shows the active fraction of the actual emitted particles; the horizontal line is the pre-existing 95% eligibility screen. Panel (b) compares integrated surface-flux sensitivity for the same receptor hour. Color denotes whether the original run passed that screen. Values are forward-model diagnostics, not measures of atmospheric accuracy.

The paired and sample-composition terms answer different questions. For a metric $X$, the reported total change is decomposed exactly as

$$
\overline{X}_{\mathrm{wide,all}}-\overline{X}_{\mathrm{original,retained}}
=\left(\overline{X}_{\mathrm{wide,retained}}-\overline{X}_{\mathrm{original,retained}}\right)
+\left(\overline{X}_{\mathrm{wide,all}}-\overline{X}_{\mathrm{wide,retained}}\right).
$$

The first term is a same-hour paired configuration change. The second is the composition change from recovering hours that the original domain excluded. Pointwise 95% intervals use 5,000 circular three-day block resamples of receptor dates; they describe short-record sampling variability and are not atmospheric-model uncertainty.

**Table 8. Original-to-wide decomposition across the 52-hour BKT ensemble.**

| Metric | Same-hour change (95% interval) | Recovered-hour composition (95% interval) | Total change (95% interval) |
| --- | --- | --- | --- |
| Integrated sensitivity [ppm / (µmol m⁻² s⁻¹)] | -0.030 (-0.107 to 0.072) | +0.080 (-0.782 to 0.745) | +0.051 (-0.830 to 0.744) |
| Net prior surface CH₄ (ppb) | -5.38 (-19.49 to 9.25) | -3.49 (-21.74 to 21.40) | -8.88 (-37.32 to 26.35) |
| Endpoint background CH₄ (ppb) | -0.29 (-0.87 to 0.30) | -7.38 (-16.35 to -2.15) | -7.66 (-16.36 to -2.35) |
| Combined prior CH₄ (ppb) | -5.67 (-20.06 to 8.85) | -10.87 (-28.20 to 13.86) | -16.54 (-42.83 to 17.09) |

### Selection pattern in the observed gases

Relative to originally retained hours, CO₂ is 1.49 ppm lower (interval includes zero) in recovered hours, CH₄ is 28.36 ppb lower (interval excludes zero) in recovered hours, and CO is 264.13 ppb lower (interval includes zero) in recovered hours. These block-resampled contrasts quantify which observations the original transport screen omitted; they do not attribute the gas differences to transport or any source.

![Observed BKT gas concentrations in hours retained and excluded by the original transport-domain screen.](outputs/hysplit/domain_budget_extension/figures/selection_concentrations.png)

**Figure 7.** Quality-controlled BKT CO₂, CH₄ and CO for hours retained by the original 95% particle screen and hours recovered by widening the transport domain. Points are observed concentrations; boxes show medians and interquartile ranges. The grouping is determined by modeled particle retention, not concentration. Differences therefore diagnose sample composition and do not imply that widening a domain changes an observation or that transport loss causes the concentration contrast.

**Table 9. Observed concentration difference between recovered and originally retained hours.**

| Observed gas | Retained mean | Recovered mean | Recovered minus retained | 95% interval |
| --- | --- | --- | --- | --- |
| CO₂ (ppm) | 420.41 | 418.92 | -1.49 | -9.42 to 4.74 |
| CH₄ (ppb) | 1918.07 | 1889.70 | -28.36 | -52.50 to -2.32 |
| CO (ppb) | 570.74 | 306.61 | -264.13 | -533.41 to 11.02 |

Calendar-month, WIB clock-period and GFS 10 m wind strata are reported as short-record diagnostics rather than seasonal or observational meteorology. Original retention was 12/26 (46.2%) for 07:00–17:59 WIB and 15/26 (57.7%) for 18:00–06:59 WIB; 26/39 (66.7%) in September and 1/13 (7.7%) during 1–6 October; and 13/26 (50.0%) under eastward versus 14/26 (53.8%) under westward modeled 10 m flow. The pronounced calendar imbalance means that the recovered-minus-retained gas contrasts are temporally confounded; the block intervals describe sampling variability but do not adjust for temporal evolution.

### Surface contribution and endpoint-background convergence

The 120-to-168-hour increment is smaller than the 72-to-120-hour increment in original surface 5/5, original background 4/5, original combined 3/5, widened surface 5/5, widened background 4/5, widened combined 4/5 representative comparisons. Opposing surface and background changes reduce the combined increment in 14 of 20 domain–duration–receptor contrasts. For the widened 24 September 18:00 UTC case, a +27.31 ppb surface increment and -27.02 ppb background increment leave only +0.29 ppb in the combined term; this is component cancellation, not joint convergence. In the severe 6 October 06:00 UTC case, the combined increment falls from +13.76 ppb in the original domain to +1.55 ppb when widened, while the corresponding background increment falls from +13.62 to +1.46 ppb. Because no prospective tolerance defines negligible change, these results describe stabilization tendencies rather than declaring convergence or atmospheric accuracy.

![Representative methane surface, endpoint-background and combined prior-budget responses by domain and duration.](outputs/hysplit/domain_budget_extension/figures/budget_convergence.png)

**Figure 8.** Prior methane-budget components for five pre-declared BKT receptor hours at 72, 120 and 168 hours backward. Thin lines are individual receptors and thick lines are cross-case medians; blue denotes the original domain and orange the widened domain. Surface contribution combines prior anthropogenic, wetland, termite, geological and non-crop-fire methane, less the positive soil-uptake magnitude [4, 5]. Background is the equal-particle mean CarbonTracker-CH4 value at active trajectory endpoints [9]. The sum can appear stable when its components offset, so the three panels must be read together. These representative cases were selected by clock period, model wind quadrant and original retention—not gas residual—and are not a random or seasonally representative sample.

**Table 10. Absolute duration increments across the five representative methane-budget cases.**

| Domain | Component | Absolute 72–120 h median (range), ppb | Absolute 120–168 h median (range), ppb | Later increment smaller |
| --- | --- | --- | --- | --- |
| Original | Surface | 12.79 (1.38–29.08) | 2.48 (0.13–15.93) | 5/5 |
| Original | Background | 13.63 (0.74–64.05) | 2.85 (1.76–15.64) | 4/5 |
| Original | Combined | 4.90 (0.64–34.97) | 2.99 (0.29–13.76) | 3/5 |
| Widened | Surface | 11.47 (1.44–29.47) | 1.27 (0.03–27.31) | 5/5 |
| Widened | Background | 12.14 (0.36–62.81) | 1.46 (1.26–27.02) | 4/5 |
| Widened | Combined | 2.95 (0.67–33.55) | 1.55 (0.29–2.53) | 4/5 |

CarbonTracker-CH4 assimilates BKT observations, so its endpoint mean is a physically informed boundary estimate rather than an independent test of the BKT record. The source fields are prior inventories or models, and the small convergence matrix tests numerical sensitivity only. Accordingly, this extension can identify domain truncation, selection effects and component instability; it cannot validate atmospheric accuracy, attribute measured methane to a source, or support a revised emissions inversion.


## 5. Finer-grid meteorology did not pass the conversion screen

**Decision: retain the existing GFS inversion; no BARRA-driven transport or emission update is reported.** A follow-up screen examined the public Bureau of Meteorology Atmospheric high-resolution Regional Reanalysis for Australia, version 2, deterministic product (BARRA-R2). Its native 0.11° horizontal grid covers BKT, but a finer horizontal grid does not establish better transport accuracy [14]. The screen identified missing pressure-level fields in cells where those levels are above the supplied model surface. Direct conversion to HYSPLIT input was therefore stopped before filling or extrapolating those values.

### Scope and a reproducible missing-data test

The inspected subset covers 94.97°–104.98° E and 4.95° S–4.95° N on 9 September 2019, 00:00–12:00 UTC, inclusive: 13 hourly timestamps on a 91 by 92 grid. This is a bounded conversion screen, not a monthly data-quality estimate or a transport-skill evaluation. Native latitude–longitude coordinates and timestamps were matched across variables. Surface pressure was converted explicitly from Pa to hPa; vertical velocity was verified as upward-positive in m s⁻¹. Packed fill values and nonfinite subset values were retained as missing, never interpreted as zero.

A pressure level $p$ was classified as clearly above the local surface when $p_s > p + \Delta p$, where $p_s$ is supplied surface pressure and the main diagnostic uses $\Delta p=1$ hPa. Pressure decreases with height. The margin separates the result from tiny pressure-rounding differences; a second calculation with $\Delta p=10$ hPa tests that sensitivity. This is a consistency check against the supplied pressure field, not an independent observation of terrain height.

**Table 11. Missing BARRA-R2 pressure-level data above the supplied surface.** Counts are cell–timestamp pairs, not independent statistical samples. Each row applies separately to all six inspected fields: eastward wind, northward wind, upward air velocity, temperature, specific humidity and geopotential height. The main denominator includes only cells satisfying the 1 hPa pressure-margin criterion. The last column repeats the gap count using the stricter 10 hPa margin.

| Level (hPa) | Above-ground pairs | Missing pairs | Missing (%) | Gaps: 10 hPa margin |
| --- | --- | --- | --- | --- |
| 925 | 102,794 | 1,982 | 1.93 | 1,360 |
| 850 | 108,228 | 308 | 0.28 | 115 |

The gaps persist under the stricter pressure margin, so small pressure-rounding differences cannot explain them. Direct reads of native packed values independently confirmed 3 selected missing-field examples and their surface pressures, including a 925 hPa gap at 979.44 hPa surface pressure. These checks establish that the selected gaps were not introduced by the subset's unpacking. The provider documents pressure-level masking and other post-processing limitations [15]; the exact origin of the above-surface mask extent was not established here. Possible interpolation effects should not be described as a confirmed processing defect without further evidence.

### Near-surface information exists, but it is not a validated replacement driver

At the nearest BKT grid cell (0.22° S, 100.36° E), BARRA terrain is 1,007 m above mean sea level and surface pressure spans 899.8–902.9 hPa in the inspected interval. The 925 hPa fields are below ground and missing at this cell; that local absence is physically expected. The next inspected pressure level, 850 hPa, has geopotential height about 497–521 m above model terrain. This height difference is approximate because geopotential height and geometric terrain height are not identical vertical measures.

Supplemental temperature fields at heights above ground provide additional information near the surface; these were inspected rather than assuming that pressure-level spacing represents all publicly available temperature information. However, they do not by themselves reconstruct the missing common wind, temperature, humidity and vertical-motion profiles. HYSPLIT's documentation emphasizes adequate low-level resolution and near-surface stability information [16]. The existing STILT experiment estimates mixing depth from a modified Richardson number, making unvalidated profile reconstruction consequential for surface-flux sensitivity.

**Required next evidence.** Obtain provider guidance or complete compatible model-level fields, or define and independently validate a terrain-aware reconstruction that preserves valid data and explicitly tests the affected regions. Then verify ARL packing, vertical profiles and regional boundary transfers before a matched particle experiment. Simply filling gaps with zero, silently extrapolating across terrain, or rerunning the emission inversion would not satisfy this conversion screen. This finding does not show that BARRA-R2 is generally unusable or less accurate than GFS; it explains why no transport comparison or improved emission estimate follows from this audit.


<!-- pdf-pagebreak -->

## References

1. NOAA Air Resources Laboratory. *Configuring STILT options in HYSPLIT*. [Official model guidance](https://www.ready.noaa.gov/documents/Tutorial/html/stilt_setup.html).
2. Lin, J. C., et al. (2003). A near-field tool for simulating the upstream influence of atmospheric observations: The Stochastic Time-Inverted Lagrangian Transport (STILT) model. *Journal of Geophysical Research: Atmospheres*, 108(D16), 4493. [doi:10.1029/2002JD003161](https://doi.org/10.1029/2002JD003161).
3. NOAA Air Resources Laboratory. *GFS quarter-degree meteorological archive: data and hybrid-level definitions*. [Archive documentation](https://www.ready.noaa.gov/data/archives/gfs0p25/readme_gfs0p25_info.txt).
4. European Commission Joint Research Centre. *EDGAR v8.0 greenhouse-gas emissions, monthly sectoral fluxes*. [Dataset and methodological documentation](https://edgar.jrc.ec.europa.eu/dataset_ghg80).
5. van der Werf, G. R., et al. (2025). Landscape fire emissions from the 5th version of the Global Fire Emissions Database (GFED5). *Scientific Data*, 12, 1870. [doi:10.1038/s41597-025-06127-w](https://www.nature.com/articles/s41597-025-06127-w). Daily GFED5.1 data and license: [GFED data portal](https://www.globalfiredata.org/data.html).
6. geoBoundaries. *gbOpen boundary data and API*. [Data access, source and license metadata](https://www.geoboundaries.org/api.html). Country polygons retain their individual source licenses; Indonesian boundaries use the established provincial geometry independently of this product.
7. NOAA Air Resources Laboratory. *Turbulence, stability and mixed-layer depth configuration*. [HYSPLIT user guide](https://www.ready.noaa.gov/hysplitusersguide/S625.htm).
8. Lin, J. C., and Gerbig, C. (2005). Accounting for the effect of transport errors on tracer inversions. *Geophysical Research Letters*, 32, L01802. [doi:10.1029/2004GL021127](https://doi.org/10.1029/2004GL021127).

9. NOAA Global Monitoring Laboratory (2025). *CarbonTracker-CH₄ CT-CH₄-2025*: three-dimensional methane mole fractions and assimilation documentation. [Dataset citation and access](https://gml.noaa.gov/ccgg/carbontracker-ch4/carbontracker-ch4-2025/citation.php); [technical documentation](https://gml.noaa.gov/ccgg/carbontracker-ch4/CTCH4_v2025_Website-Documentation.pdf). doi:10.25925/hxks-v755.
10. East, J. D., et al. (2024). Interpreting the Seasonality of Atmospheric Methane. *Geophysical Research Letters*, e2024GL108494. [doi:10.1029/2024GL108494](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2024GL108494). LPJ-MERRA2 wetland fields distributed by the [GEOS-Chem input-data archive](https://geos-chem.s3.amazonaws.com/HEMCO/CH4/v2025-09/LPJ_MERRA2/README).
11. Murguia-Flores, F., et al. (2018). Soil Methanotrophy Model (MeMo v1.0): a process-based model to quantify global uptake of atmospheric methane by soil. *Geoscientific Model Development*, 11, 2009–2032. [doi:10.5194/gmd-11-2009-2018](https://gmd.copernicus.org/articles/11/2009/2018/), with the [2019 supplementary-unit corrigendum](https://gmd.copernicus.org/articles/11/2009/2018/gmd-11-2009-2018-corrigendum.pdf).
12. GEOS-Chem methane input-data archive. Auxiliary methane fields: CAMS-GLOB-TERM v1.1, [MeMo climatology documentation](https://geos-chem.s3.amazonaws.com/HEMCO/CH4/v2019-10/MeMo_SoilAbs/README), and geological methane based on [Etiope et al. (2019), doi:10.5194/essd-11-1-2019](https://essd.copernicus.org/articles/11/1/2019/), scaled in the distributed product to the global constraint of [Hmiel et al. (2020), doi:10.1038/s41586-020-1991-8](https://www.nature.com/articles/s41586-020-1991-8). Product versions, native timestamps and climatological reuse are identified in the methods; these fields are not local observations.
13. Jeong, S., et al. (2013). A multitower measurement network estimate of California's methane emissions. *Journal of Geophysical Research: Atmospheres*, 118, 11339–11351. [doi:10.1002/jgrd.50854](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/jgrd.50854).

CarbonTracker CT-CH₄-2025 results are provided by NOAA GML, Boulder, Colorado, USA, through the CarbonTracker-CH₄ data service. Their use here does not imply NOAA endorsement or independent validation of the regional inversion.

Additional inversion-map boundary attribution: India and Bangladesh derive from geoBoundaries and Wikimedia Commons (CC0 1.0); Sri Lanka and Timor-Leste from © OpenStreetMap contributors and Wambacher (ODbL 1.0); Australia from the Australian Bureau of Statistics (CC BY 4.0). These provider-reported datasets have different source vintages and geometric detail; their use supplies geographic context rather than a uniform historical administrative reconstruction.

14. Bureau of Meteorology (2023). *Bureau of Meteorology Atmospheric high-resolution Regional Reanalysis for Australia, version 2 (BARRA2)*, model realization v1. [Dataset, doi:10.25914/1x6g-2v48](https://doi.org/10.25914/1x6g-2v48); [provider README and citation details](https://bom-opendata-climate.s3.amazonaws.com/BARRA2/README.txt). System description: Su, C.-H., et al. (2025), *The Australian regional atmospheric reanalysis system, version 2 - BARRA2*, Journal of Southern Hemisphere Earth Systems Science, 75, ES25032, [doi:10.1071/ES25032](https://doi.org/10.1071/ES25032). Bibliographic details are supplied by the dataset provider; no unverified paper-specific findings are used here.
15. NCI and Bureau of Meteorology. *Known Issues - BOM BARRA2 (ob53)*. [Provider-maintained data-quality notices](https://opus.nci.org.au/spaces/NDP/pages/264241304/Known+Issues+-+BOM+BARRA2+ob53), accessed 6 September 2026.
16. NOAA Air Resources Laboratory. *Meteorology: ARL data format*. [Required fields, packing and vertical-resolution guidance](https://www.ready.noaa.gov/hysplitusersguide/S141.htm), accessed 6 September 2026.
17. NOAA Air Resources Laboratory. *Variables not set in the graphical interface*. [CAPE, convection, random-seed and near-surface input configuration](https://www.ready.noaa.gov/hysplitusersguide/S640.htm), accessed 6 September 2026.
18. NOAA National Centers for Environmental Information. *Integrated Global Radiosonde Archive, version 2.2*. [Dataset scope, quality control and limitations](https://www.ncei.noaa.gov/products/weather-balloon/integrated-global-radiosonde-archive), accessed 6 September 2026.
19. NOAA National Centers for Environmental Information (2023). *IGRA v2.2 sounding-data format description*. [Time fields, units, quality flags and station-location conventions](https://www.ncei.noaa.gov/pub/data/igra/data/igra2-data-format.txt), dated 19 January 2023, accessed 6 September 2026.

Boundary attribution: Malaysia, Cambodia and Thailand derive from © OpenStreetMap contributors and Wambacher (ODbL 1.0); Myanmar from OpenStreetMap (CC BY-SA 2.0 as stated by the provider); Singapore from the Urban Redevelopment Authority, derived from subnational boundaries (ODbL 1.0); Vietnam from geoBoundaries/Wikipedia (CC BY 4.0); the Philippines from OCHA Philippines and the National Mapping and Resource Information Authority (CC BY 3.0 IGO); Brunei from Wikimedia Commons (public domain). These are provider-reported source licenses, not a claim of uniform official status.
20. Hersbach, H., et al. (2020). The ERA5 global reanalysis. *Quarterly Journal of the Royal Meteorological Society*, 146, 1999–2049. [doi:10.1002/qj.3803](https://doi.org/10.1002/qj.3803).
21. Stein, A. F., et al. (2015). NOAA's HYSPLIT atmospheric transport and dispersion modeling system. *Bulletin of the American Meteorological Society*, 96, 2059–2077. [doi:10.1175/BAMS-D-14-00110.1](https://doi.org/10.1175/BAMS-D-14-00110.1).
