# Carbon dioxide seen from two Sumatran towers: Bukit Kototabang and Jambi

## Scientific summary

Bukit Kototabang (BKT) observes carbon dioxide at 865 m in the highlands of western Sumatra; Jambi observes it on the eastern lowland at 25 m above sea level. This report asks what a two-receptor transport inversion can constrain about Sumatran carbon dioxide, using the same HYSPLIT-STILT ensemble, the same towers and the same window as the companion methane study, with the inputs that carbon dioxide requires: EDGAR_2025_GHG fossil emissions, CarbonTracker CT-NRT.v2025-1 ocean, fire and biosphere fluxes, and a CT-NRT endpoint background. Both inlets are taken at 100 m above ground. The analysis covers 24 November to 31 December 2023 and 1 October to 31 December 2024, giving 69 usable afternoon dates at BKT and 66 at Jambi, from 636 five-day runs.

Carbon dioxide cannot use the night hours that methane uses. At 01 WIB the towers see +20 and +45 ppm above background under a model mixing depth of about 43 m, while the prior gives +5.9 and +7.0 ppm. A quarter-degree footprint cannot resolve the shallow nocturnal layer these observations sit in, so the inversion uses 12 to 14 WIB means only, screened for carbon-dioxide-only spikes and for a modelled mixing depth of at least 300 m.

The optimized CarbonTracker biosphere flux cannot serve as the prior for this window. From 25 November to 1 December 2023 it releases carbon dioxide by day and takes it up at night over 37% of Sumatran land cells, including both tower cells. A diagnostic prior built here from downward shortwave radiation, air temperature and MODIS vegetated fraction keeps the correct phase and carries its uptake and respiration as separate, separately scalable terms.

The test any regional inversion has to pass is predicting a day it did not fit better than its own boundary field carrying a fitted offset and trend. Neither tower does. On the combined record the posterior predicts a withheld date worse than the background at both towers, by +0.30 ppm at Bukit Kototabang and +0.42 ppm at Jambi, and the date-block interval excludes zero at Bukit Kototabang. The 2023 result does not reproduce. At Jambi the posterior was 1.07 ppm better than the background over 12 dates in 2023, an interval of -3.77 to +1.26 ppm that never excluded zero; over 54 dates in 2024 the same configuration is 0.68 ppm worse (-0.09 to +1.30). A gain that changes sign when the sample quadruples was a property of the sample, not of the method.

The fire prior is too strong, and taking it out of the fixed baseline helps the background rather than the inversion: the background-only error at Jambi falls by 0.44 ppm when fire is no longer added to it, and the fitted fire multiplier is 0.55 (0.20 to 1.21). With fire scaled, the posterior is still worse than that improved background at Jambi, by +0.67 ppm (+0.04 to +1.32). Raising the BKT release to the true inlet altitude and to 300 m changes the modelled response by at most 5% and the out-of-sample error by at most 0.10 ppm, so the terrain mismatch at the mountain tower is not what limits this inversion. The multipliers reported here are adjustment factors on a diagnostic prior under a stated error model, conditional on parameterized transport and an assumed 100 m inlet at both towers; the skill comparisons, not the multipliers, are this report's result.

## 1. Scientific question and scope

The companion two-receptor methane study established what this pair of towers can and cannot do for a long-lived gas whose Sumatran sources are dominated by surface emissions: the joint fit scales regional priors, and the Jambi night record falls outside a quarter-degree model. Carbon dioxide is the harder case. Its regional signal is dominated by a biosphere that changes sign twice a day, its fossil component is small in this part of Sumatra, and its background varies by more than the enhancement the towers see in the afternoon.

The study asks four questions. Which carbon dioxide observations can a quarter-degree transport model represent at these two towers? Does an inversion of those observations predict carbon dioxide better than the boundary field with a fitted offset and trend, which is the null model any regional inversion must beat? Does the answer differ between the highland and the lowland tower? And does the October to December 2024 overlap, four times the sample, reproduce what 15 dates in 2023 appeared to show?

It does not estimate carbon budgets, separate photosynthesis from respiration as independent fluxes, or attribute enhancements to individual sources. The biosphere multipliers reported here scale a diagnostic prior, not a measured flux.

## 2. Evidence and data quality

### 2.1 Observation windows

The two towers overlap in two periods of the harmonized hourly archive. The 2023 period is the window used by the methane study, 24 November to 31 December 2023. The 2024 period, 1 October to 31 December 2024, is larger and was added to this study because carbon dioxide, unlike methane, needs no CarbonTracker-CH₄ boundary field: CT-NRT.v2025-1 covers both periods, and EDGAR_2025_GHG supplies fossil carbon dioxide for 2023 and 2024 (Table 1).

**Table 1. Joint afternoon receptors by period.** A joint receptor date has a valid, unflagged carbon dioxide record at both towers at 06 UTC. Usable counts are after the transport, observation and mixing screens of Section 2.3. Runs are HYSPLIT-STILT members, seeds included.

| Period | Joint dates | Withheld | Usable at BKT | Usable at Jambi | Runs |
| --- | --- | --- | --- | --- | --- |
| 24 November to 31 December 2023 | 21 | 5 | 15 | 12 | 294 |
| 1 October to 31 December 2024 | 63 | 15 | 54 | 54 | 252 |

Every fourth joint date was withheld before fitting. Withholding complete dates, rather than hours, keeps correlated error within a day out of the evaluation.

### 2.2 Which hours the model can carry

At both towers the afternoon and the night are different measurement problems (Figure 1, Table 2). At 13 WIB the modelled mixing depth is 673 m at BKT and 987 m at Jambi, the observed enhancement is within a few ppm of zero, and the prior is of the same size. At 01 WIB the modelled mixing depth collapses to about 43 m at both towers, the observed enhancement rises to +20 ppm at BKT and +45 ppm at Jambi, and the prior explains +5.9 and +7.0 ppm of it. The shortfall is not a flux error that a multiplier can absorb; it is a layer the model does not resolve. Night hours are therefore excluded from every fit in this report, at both towers.

![Day and night at the two towers.](outputs/hysplit/two_receptor/figures/figure_C04_daytime_only.png)

**Figure 1.** Observed carbon dioxide enhancement against the prior at 13 and 01 WIB (a), median modelled mixing depth at the same hours (b), and the mixing depth of every afternoon receptor in 2023 with the 300 m screen (c). Error bars in (a) are one standard deviation across hours.

**Table 2. Observed enhancement and model boundary layer by receptor and hour.** Mixing depth is the native GFS value in the receptor cell; enhancement is the observation minus the endpoint background; prior is the sum of the CarbonTracker-prior components. 2023 window, hours that pass the transport screen.

| Receptor | Hour | n | Mixing depth, median (m) | Enhancement, mean ± sd (ppm) | Prior (ppm) | Background (ppm) |
| --- | --- | --- | --- | --- | --- | --- |
| Bukit Kototabang | 06 UTC (13 WIB) | 16 | 673 | -2.7 ± 3.4 | +1.5 | 421.4 |
| Bukit Kototabang | 18 UTC (01 WIB) | 25 | 43 | +20.1 ± 8.6 | +5.9 | 421.2 |
| Jambi | 06 UTC (13 WIB) | 12 | 987 | -2.4 ± 4.5 | +4.7 | 422.3 |
| Jambi | 18 UTC (01 WIB) | 21 | 43 | +45.0 ± 14.8 | +7.0 | 422.7 |

### 2.3 Screens

Four screens stand between the archive and the fit. The observation is the mean of the valid 12 to 14 WIB hours, which suppresses single-hour variability that no quarter-degree model reproduces. A carbon-dioxide-only spike screen removes hours where carbon dioxide departs from its neighbours while methane and carbon monoxide do not, the signature of a local plume too small to model: 2 of 75 testable hours are flagged, the larger being 79 ppm at Jambi on 26 November 2023, an hour on which methane moved by -3 ppb and carbon monoxide by +0 ppb. A transport screen keeps only receptor hours where every seed retains at least 95% of its particles at 120 h. A mixing screen removes afternoon hours whose modelled mixing depth is below 300 m, where the model's own diagnosis says the afternoon boundary layer has not developed (Table 3).

**Table 3. Afternoon receptors surviving each screen.** The observation stage removes dates with no valid 12 to 14 WIB hour and dates whose only hours were flagged as carbon-dioxide-only spikes.

| Stage | 2023, BKT | 2023, JMB | 2024, BKT | 2024, JMB |
| --- | --- | --- | --- | --- |
| Declared afternoon receptors | 21 | 21 | 63 | 63 |
| Particle retention at least 95% | 16 | 13 | 60 | 58 |
| Afternoon mean available after the spike screen | 16 | 12 | 60 | 58 |
| Mixing depth at least 300 m | 15 | 12 | 54 | 54 |

## 3. Methods

### 3.1 Transport ensemble

Each receptor hour is simulated at both towers with HYSPLIT 5.4.2 in STILT mode, 120 h backward, with three random seeds of 2,000 requested particles in 2023 and two in 2024, driven by the NOAA GFS quarter-degree archive cropped server-side to 50° to 160° E and 40° S to 30° N. Footprints are written hourly on a 0.25° grid spanning 60° of latitude and 100° of longitude centred on each tower, normalized by the number of particles actually emitted and averaged across seeds. A separate campaign repeats the BKT afternoon receptors with the release raised to 150 m and to 300 m above model ground (Section 4.5).

### 3.2 Priors and boundary

Fossil emissions are EDGAR_2025_GHG monthly carbon dioxide for the month of each receptor hour, split into the part within 500 km of the observing tower and the part beyond. Ocean exchange and fire emissions are the CT-NRT.v2025-1 three-hourly fields. The background of each receptor hour is the CT-NRT.v2025-1 mole fraction sampled at the position and height of every retained particle at 120 h, with height above model terrain converted to altitude, averaged with equal weight.

The biosphere is the difficult term, and Section 4.2 shows why the optimized CT-NRT flux cannot supply it here. The prior used instead is diagnostic. Gross uptake in each cell is proportional to de-accumulated GFS downward shortwave radiation times the MODIS MCD12C1 vegetated fraction, scaled so that a fully vegetated cell takes up 3,000 gC m⁻² yr⁻¹; respiration follows a Q10 of 1.5 about the cell's own mean temperature, and is scaled so that uptake and respiration balance in each cell over the window. Uptake and respiration enter the inversion as two separate response columns, so the fit can scale the daytime sink and the night-time source independently, and at each tower separately.

### 3.3 Inversion

Each observation is modelled as the endpoint background, plus fixed ocean and fire terms, plus the sum of prior increments each scaled by its own multiplier, plus a per-tower offset and linear trend. Fossil multipliers are positive with log-normal priors; the biosphere response columns are signed, because uptake reduces the mole fraction, so the inversion uses a signed formulation in which a positive multiplier scales a negative column. Nuisance covariates enter as unconstrained Gaussian terms.

The error covariance for each tower combines a 0.2 ppm measurement allowance, a local mismatch of 2 ppm by day, a background term of 1 ppm with 72 h correlation, and a transport error equal to a fraction of the hour's total prior increment with 24 h correlation. That fraction is tuned separately for each tower to a training reduced chi-square of one, because a single shared fraction is set by whichever tower fits worst and then inflates the other tower's errors until nothing can be resolved there. Errors are correlated within a tower and independent between towers. Posteriors are sampled by Markov chain Monte Carlo and accepted only with R-hat at most 1.01 and an effective sample size of at least 1,000 for every parameter.

### 3.4 Cases and evaluation

The variants compared here differ in four ways: which biosphere prior supplies the response columns, whether biosphere multipliers are shared between the towers or fitted per tower, which nuisance covariates are admitted, and which period is fitted (Table 4). The covariates tested at each tower are the endpoint background itself, the methane enhancement above the tower's own rolling clean-air baseline, and the methane residual from the companion inversion; the methane terms are proxies for local, poorly modelled surface influence that carbon dioxide shares with methane but the carbon dioxide prior does not contain.

**Table 4. Model variants compared.** Every variant uses the same receptors, the same withheld dates, the same diagnostic biosphere prior and the same fitting and scoring machinery; only the columns below differ.

| Variant | Biosphere terms | Covariates | Period fitted | BKT release | Transport error |
| --- | --- | --- | --- | --- | --- |
| 2023, both biosphere towers | Uptake and respiration at each tower | CH₄ proxy at JMB, CH₄ proxy at BKT | 2023 | 100 m | per tower |
| 2024, both biosphere towers | Uptake and respiration at each tower | CH₄ proxy at JMB, CH₄ proxy at BKT | 2024 | 100 m | per tower |
| Both periods, both biosphere towers | Uptake and respiration at each tower | CH₄ proxy at JMB, CH₄ proxy at BKT | 2023 and 2024 | 100 m | per tower |
| 2023, Jambi biosphere only | Uptake and respiration at Jambi only | CH₄ proxy at JMB, CH₄ proxy at BKT | 2023 | 100 m | per tower |
| 2024, Jambi biosphere only | Uptake and respiration at Jambi only | CH₄ proxy at JMB, CH₄ proxy at BKT | 2024 | 100 m | per tower |
| Both periods, Jambi biosphere only | Uptake and respiration at Jambi only | CH₄ proxy at JMB, CH₄ proxy at BKT | 2023 and 2024 | 100 m | per tower |

Every variant is scored three ways. Withheld dates give an honest but small test. All-daytime residuals give the in-sample fit. Leave-one-date-out cross-validation refits the model without each date and predicts that date, which uses every date once as a test and is the primary measure here. The comparison is always against the same null: the endpoint background with a fitted per-tower offset and trend and no source terms. Because dates are few and their errors are correlated within a day, the difference in cross-validated RMSE is bootstrapped by resampling whole dates, 5,000 times.

## 4. Results

### 4.1 The afternoon signal is small

Over the afternoon receptors the observed carbon dioxide sits within a few ppm of the CT-NRT background, and the prior increments are of the same size as the residual the inversion has to explain (Table 5). The mean prior increments at the afternoon receptors are -23.8 ppm of gross uptake and 21.4 ppm of respiration at BKT, -21.7 and 22.4 ppm at Jambi, against fossil increments of 0.57 and 1.33 ppm. The two biosphere terms nearly cancel, so the quantity the data constrain is the small difference between two large opposing terms, and the fossil term is an order of magnitude smaller than either.

**Table 5. Mean modelled contribution at the fitted afternoon receptors, ppm.** Uptake is negative by convention. Ocean is fixed, and so is fire in every case except the variant of Section 4.6; the background is the CT-NRT mole fraction sampled at the particle endpoints.

| Component | BKT | Jambi |
| --- | --- | --- |
| Gross uptake (diagnostic prior) | -23.77 | -21.68 |
| Respiration (diagnostic prior) | 21.42 | 22.42 |
| Fossil, EDGAR_2025_GHG | 0.57 | 1.33 |
| Ocean, CT-NRT | 0.018 | 0.004 |
| Fire, CT-NRT | 0.116 | 0.847 |
| Endpoint background, CT-NRT | 423.8 | 424.0 |
| Observed afternoon mean | 419.5 | 422.3 |

### 4.2 The optimized biosphere flux runs backwards

The CT-NRT.v2025-1 optimized biosphere flux inverts its daily cycle for a week of this window (Figure 2). From 25 November to 1 December 2023 it releases carbon dioxide during the local day and takes it up at night over 37% of Sumatran land cells, and both tower cells are among them. Over the whole window the same field has the ordinary phase, so the fault is episodic rather than systematic, but an inversion cannot use a prior whose sign is wrong for a quarter of its data and right for the rest.

![Optimized and diagnostic biosphere priors.](outputs/hysplit/two_receptor/figures/figure_C02_biosphere_priors.png)

**Figure 2.** Net biosphere flux by local solar hour at the BKT cell (a) and the Jambi cell (b), for the CT-NRT optimized flux over the whole window, the same flux during the inverted week, and the diagnostic prior; and the share of CarbonTracker land cells with an inverted day-night cycle on each day (c).

The diagnostic prior replaces it. Its phase follows sunlight, so it cannot invert, and its two halves are separately scalable, so an error in either is absorbed by a multiplier rather than by the offset. Fitting the two cases side by side, the diagnostic prior lowers the daytime error at Jambi from 5.67 to 3.63 ppm, and at BKT from 4.23 to 4.05 ppm, on the same receptors and the same screens.

### 4.3 Posterior multipliers

The headline cases and their posteriors are in Table 6.

**Table 6. Posterior parameters of the two headline cases.** Medians with 95% credible intervals. Multipliers are dimensionless and unity reproduces the prior; offsets, trends and covariate coefficients are in the units given.

| Parameter | Both periods, both biosphere towers | Both periods, Jambi biosphere only |
| --- | --- | --- |
| Fossil ≤500 km | 0.59 (0.20 to 1.37) | 0.57 (0.19 to 1.27) |
| Fossil >500 km | 0.82 (0.25 to 2.18) | 0.82 (0.24 to 2.19) |
| Gross uptake, BKT | 0.21 (0.11 to 0.34) | not fitted |
| Respiration, BKT | 0.20 (0.11 to 0.32) | not fitted |
| Gross uptake, Jambi | 0.42 (0.20 to 0.71) | 0.42 (0.20 to 0.71) |
| Respiration, Jambi | 0.32 (0.14 to 0.58) | 0.32 (0.15 to 0.58) |
| Offset, BKT (ppm) | -2.20 (-4.74 to 0.30) | -2.46 (-4.16 to -0.73) |
| Trend, BKT (ppm per period) | -0.25 (-0.43 to -0.06) | -0.27 (-0.41 to -0.12) |
| Offset, Jambi (ppm) | -1.44 (-5.25 to 2.49) | -1.41 (-5.25 to 2.52) |
| Trend, Jambi (ppm per period) | -0.05 (-0.35 to 0.26) | -0.05 (-0.36 to 0.26) |
| CH₄ proxy coefficient, BKT (ppm ppb⁻¹) | 0.026 (-0.006 to 0.059) | 0.014 (-0.010 to 0.039) |
| CH₄ proxy coefficient, Jambi (ppm ppb⁻¹) | 0.024 (-0.018 to 0.068) | 0.025 (-0.018 to 0.067) |

The fossil multipliers are close to their priors with intervals spanning an order of magnitude, which is the expected result for a term worth 0.57 ppm at BKT and 1.33 ppm at Jambi, against a biosphere difference many times larger. The contrast with the all-hours fits is instructive: fitting the night hours as well drives the Jambi-only fossil multipliers to 9.7 (5.8 to 13.7) and 19.6 (7.9 to 29.4), the inversion's only way to manufacture the tens of ppm the nights show, and a second reason to treat those hours as outside the model rather than as evidence about emissions. A biosphere prior with no water or nutrient limitation should overstate the amplitude of the afternoon drawdown the towers actually see, and the fit says it does. All four biosphere multipliers sit below unity, and 4 of 4 exclude unity at 95%: gross uptake, BKT 0.21 (0.11 to 0.34); respiration, BKT 0.20 (0.11 to 0.32); gross uptake, Jambi 0.42 (0.20 to 0.71); respiration, Jambi 0.32 (0.14 to 0.58).

### 4.4 Skill against the background

The test that matters is whether any of this predicts carbon dioxide better than the boundary field with a fitted offset and trend (Figure 3, Figure 4, Table 7).

![Afternoon series at both towers.](outputs/hysplit/two_receptor/figures/figure_C01_series.png)

**Figure 3.** Observed afternoon carbon dioxide at the two towers with the prior, the background-only model and the posterior of the headline case, by period. Lines break where no receptor passed the screens.

![Out-of-sample skill by variant.](outputs/hysplit/two_receptor/figures/figure_C03_scoreboard.png)

**Figure 4.** Leave-one-date-out RMSE by variant and tower against the background-only null (a), and the difference with its 95% date-block bootstrap interval (b).

**Table 7. Root mean square error in ppm, posterior against the background-only null.** Each cell is posterior / background with the number of scored hours. All daytime is in sample; withheld dates were never fitted; leave one date out refits the model without each date and predicts it.

| Variant | Receptor | All daytime | Withheld dates | Leave one date out |
| --- | --- | --- | --- | --- |
| 2023, both biosphere towers | Bukit Kototabang | 3.78 / 3.35 (n=15) | 2.19 / 4.07 (n=3) | 4.68 / 3.54 (n=15) |
| 2023, both biosphere towers | Jambi | 2.83 / 4.44 (n=12) | 3.23 / 2.93 (n=3) | 3.65 / 4.72 (n=12) |
| 2024, both biosphere towers | Bukit Kototabang | 2.84 / 2.38 (n=54) | 3.00 / 1.73 (n=14) | 2.87 / 2.44 (n=54) |
| 2024, both biosphere towers | Jambi | 5.78 / 5.50 (n=54) | 3.38 / 3.24 (n=13) | 6.25 / 5.56 (n=54) |
| Both periods, both biosphere towers | Bukit Kototabang | 2.91 / 2.62 (n=69) | 2.94 / 2.22 (n=17) | 3.00 / 2.70 (n=69) |
| Both periods, both biosphere towers | Jambi | 5.45 / 5.32 (n=66) | 2.95 / 3.15 (n=16) | 5.82 / 5.40 (n=66) |
| 2023, Jambi biosphere only | Bukit Kototabang | 3.28 / 3.41 (n=15) | 4.31 / 4.47 (n=3) | 3.61 / 3.63 (n=15) |
| 2023, Jambi biosphere only | Jambi | 2.77 / 4.44 (n=12) | 2.95 / 2.93 (n=3) | 3.60 / 4.72 (n=12) |
| 2024, Jambi biosphere only | Bukit Kototabang | 2.38 / 2.37 (n=54) | 1.68 / 1.76 (n=14) | 2.54 / 2.43 (n=54) |
| 2024, Jambi biosphere only | Jambi | 5.78 / 5.50 (n=54) | 3.36 / 3.24 (n=13) | 6.26 / 5.56 (n=54) |
| Both periods, Jambi biosphere only | Bukit Kototabang | 2.61 / 2.63 (n=69) | 2.32 / 2.29 (n=17) | 2.75 / 2.71 (n=69) |
| Both periods, Jambi biosphere only | Jambi | 5.44 / 5.32 (n=66) | 2.94 / 3.15 (n=16) | 5.82 / 5.40 (n=66) |

Neither tower does. On the combined record the posterior predicts a withheld date worse than the background at both towers, by +0.30 ppm at Bukit Kototabang and +0.42 ppm at Jambi, and the date-block interval excludes zero at Bukit Kototabang.

The ordering is the same in sample and out, and it is not an artefact of the covariates: the nuisance-only model, which keeps the offset, trend and methane covariate but drops every source term, predicts better than the full posterior at both towers, by 0.35 ppm at Bukit Kototabang and 0.55 ppm at Jambi. Scaling the prior increments adds variance to the prediction without adding information about the observation.

Resampling whole dates gives the interval on each of those differences (Table 8).

**Table 8. Cross-validated RMSE difference, posterior minus background, with 5,000 date-block bootstrap replicates.** Negative means the posterior predicts better. The last column is the share of replicates in which it does.

| Variant | Receptor | Dates | Difference (ppm) | 95% interval | Share better |
| --- | --- | --- | --- | --- | --- |
| 2023, both biosphere towers | Bukit Kototabang | 15 | +1.14 | -0.99 to +3.05 | 0.15 |
| 2023, both biosphere towers | Jambi | 12 | -1.07 | -3.77 to +1.26 | 0.73 |
| 2024, both biosphere towers | Bukit Kototabang | 54 | +0.43 | +0.18 to +0.75 | 0.00 |
| 2024, both biosphere towers | Jambi | 54 | +0.68 | -0.09 to +1.30 | 0.05 |
| Both periods, both biosphere towers | Bukit Kototabang | 69 | +0.30 | +0.03 to +0.57 | 0.01 |
| Both periods, both biosphere towers | Jambi | 66 | +0.42 | -0.16 to +0.95 | 0.07 |
| 2023, Jambi biosphere only | Bukit Kototabang | 15 | -0.02 | -0.57 to +0.62 | 0.53 |
| 2023, Jambi biosphere only | Jambi | 12 | -1.12 | -3.89 to +1.20 | 0.75 |
| 2024, Jambi biosphere only | Bukit Kototabang | 54 | +0.11 | -0.04 to +0.24 | 0.08 |
| 2024, Jambi biosphere only | Jambi | 54 | +0.69 | -0.09 to +1.33 | 0.05 |
| Both periods, Jambi biosphere only | Bukit Kototabang | 69 | +0.04 | -0.12 to +0.20 | 0.34 |
| Both periods, Jambi biosphere only | Jambi | 66 | +0.42 | -0.14 to +0.97 | 0.07 |

The difference is resolved at Bukit Kototabang: +0.30 ppm, 95% interval +0.03 to +0.57, over 69 dates. In 2023 alone no interval excluded zero in either direction, which is what a sample of 15 dates can say.

### 4.5 Does the larger sample reproduce the 2023 result?

Adding 1 October to 31 December 2024 takes the usable sample from 15 dates to 69. The 2024 period has no CarbonTracker-CH₄ boundary field, so the methane covariate is the enhancement above each tower's own rolling clean-air baseline rather than the modelled enhancement; on the 2023 receptors the two agree with a Spearman correlation of 0.80 at BKT and 0.98 at Jambi (Figure 5c), and the 2023 fit is repeated with the proxy so the two periods are treated alike.

At Bukit Kototabang the cross-validated error is 4.68 against 3.54 ppm in 2023; 2.87 against 2.44 ppm in 2024; 3.00 against 2.70 ppm in both periods together.

At Jambi the cross-validated error is 3.65 against 4.72 ppm in 2023; 6.25 against 5.56 ppm in 2024; 5.82 against 5.40 ppm in both periods together.

The 2023 result does not reproduce. At Jambi the posterior was 1.07 ppm better than the background over 12 dates in 2023, an interval of -3.77 to +1.26 ppm that never excluded zero; over 54 dates in 2024 the same configuration is 0.68 ppm worse (-0.09 to +1.30). A gain that changes sign when the sample quadruples was a property of the sample, not of the method.

Combining two periods ten months apart puts every 2024 receptor about thirteen prior standard deviations along a trend line centred on the 2023 window, which is a strong assumption to carry into the headline number. The combined fit was therefore repeated with an offset and a trend inside each period, so that no straight line spans the gap. It changes nothing that matters: the out-of-sample error moves by +0.06 ppm at Bukit Kototabang and +0.05 ppm at Jambi, and the posterior remains worse than its background at both towers, by +0.34 ppm (+0.07 to +0.62) and +0.49 ppm (-0.05 to +1.00). The result is not an artefact of how the two periods are joined.

### 4.6 The fire term

In 2023 fire contributed nothing at either receptor. In the 2024 window it does: the CT-NRT pyrogenic flux reaches 7.7 ppm at a Jambi receptor and averages 1.0 ppm there, in a term the inversion holds fixed in its baseline rather than scaling. A variant that moves fire out of the baseline and gives it its own multiplier tests whether that fixed term is what the fit is fighting (Table 9).

**Table 9. Fire held fixed against fire scaled.** Leave-one-date-out RMSE in ppm. In the scaled variants the fire term leaves the baseline, so the background column is the boundary field without fire; the difference column is posterior minus background with its 95% date-block bootstrap interval.

| Variant | Receptor | Posterior (ppm) | Background (ppm) | Difference |
| --- | --- | --- | --- | --- |
| 2024, fire held fixed | Bukit Kototabang | 2.87 | 2.44 | +0.43 (+0.17 to +0.74) |
| 2024, fire held fixed | Jambi | 6.25 | 5.56 | +0.68 (-0.09 to +1.29) |
| 2024, fire scaled | Bukit Kototabang | 2.87 | 2.50 | +0.36 (+0.07 to +0.70) |
| 2024, fire scaled | Jambi | 6.05 | 5.00 | +1.05 (+0.35 to +1.72) |
| Both periods, fire held fixed | Bukit Kototabang | 3.00 | 2.70 | +0.30 (+0.03 to +0.58) |
| Both periods, fire held fixed | Jambi | 5.82 | 5.40 | +0.42 (-0.16 to +0.96) |
| Both periods, fire scaled | Bukit Kototabang | 3.00 | 2.75 | +0.25 (-0.02 to +0.55) |
| Both periods, fire scaled | Jambi | 5.63 | 4.96 | +0.67 (+0.04 to +1.32) |
| Both periods, fire scaled, Jambi biosphere only | Bukit Kototabang | 2.75 | 2.75 | -0.00 (-0.20 to +0.18) |
| Both periods, fire scaled, Jambi biosphere only | Jambi | 5.62 | 4.96 | +0.66 (+0.03 to +1.34) |

The fire prior is too strong, and taking it out of the fixed baseline helps the background rather than the inversion: the background-only error at Jambi falls by 0.44 ppm when fire is no longer added to it, and the fitted fire multiplier is 0.55 (0.20 to 1.21). With fire scaled, the posterior is still worse than that improved background at Jambi, by +0.67 ppm (+0.04 to +1.32).

### 4.7 Release height at Bukit Kototabang

The GFS quarter-degree terrain in the BKT receptor cell is 816 m, against a station elevation of 865 m, so a release 100 m above model ground sits about 48 m below the true inlet altitude on a smoothed mountain. Repeating every BKT afternoon receptor with the release at 150 m, the true inlet altitude over GFS terrain, and at 300 m tests whether that mismatch matters (Figure 5, Table 10).

![Release height and the methane covariate.](outputs/hysplit/two_receptor/figures/figure_C05_height_and_proxy.png)

**Figure 5.** Paired change in the modelled response when the BKT release is raised from 100 m (a), out-of-sample error at each release height (b), and the methane enhancement proxy checked against the modelled methane enhancement on the 2023 receptors (c).

**Table 10. BKT release height.** Response changes are medians of the paired per-receptor change from the 100 m release, in percent. The error columns are the leave-one-date-out RMSE and its difference from the background-only null with a 95% date-block bootstrap interval, at BKT, for the 2023 window.

| Release height | Gross uptake (%) | Respiration (%) | Fossil ≤500 km (%) | RMSE (ppm) | Difference from background |
| --- | --- | --- | --- | --- | --- |
| 100 m | +0.0 | +0.0 | +0.0 | 4.63 | +1.09 (-1.20 to +3.14) |
| 150 m | +1.4 | -1.2 | +0.1 | 4.57 | +1.04 (-1.15 to +3.07) |
| 300 m | +4.8 | -2.6 | -1.4 | 4.53 | +1.05 (-1.15 to +3.11) |

Raising the BKT release to the true inlet altitude and to 300 m changes the modelled response by at most 5% and the out-of-sample error by at most 0.10 ppm, so the terrain mismatch at the mountain tower is not what limits this inversion.

## 5. What this does and does not show

This study answers its first question and returns a negative answer to the second.

It establishes which carbon dioxide observations at these towers are usable at all: the afternoon, screened, at both towers, and nothing at night. It establishes that the optimized CarbonTracker biosphere flux cannot serve as the prior for this window, and that a diagnostic prior with the right phase can be built from routine meteorology instead. It bounds the amplitude of that prior against the observations, through multipliers well below unity at both towers, and it bounds the CT-NRT fire term, which the fit scales down by about a factor of two.

What it does not do is predict carbon dioxide better than its own boundary field. On 69 dates the full model is worse out of sample than the background with a fitted offset and trend at both towers, and dropping the BKT biosphere terms only brings that tower back to parity (+0.04 ppm). The source terms carry no out-of-sample information at this footprint resolution, and the honest reading is that the afternoon residual at these two towers is dominated by transport and boundary error rather than by the surface fluxes underneath the footprints.

Three things follow. The inversion does not constrain fossil emissions: the fossil increments are about a ppm at the receptor, an order of magnitude below either biosphere term, and their multipliers return their priors. It does not separate photosynthesis from respiration, because in the afternoon the two response columns move together, correlating at 0.91 at Jambi and 0.92 at BKT, so the data constrain their difference and not the pair. And the multipliers below unity are a statement about the prior's amplitude rather than evidence that the scaled prior describes the flux: a model can be drawn toward the observations in sample and still predict a withheld day worse than a fitted constant does.

## 6. Extending the analysis

Three things bear on whether a regional carbon dioxide inversion at these towers can be made to work, in descending order of value.

The first is an observation that the model can carry at night. Nothing in the input chain fixes the night problem: it is a mismatch between a 300 m screen on a quarter-degree mixing depth and a nocturnal layer of a few tens of metres. Either a finer transport model with a resolved stable layer, or a measurement that samples the same layer the model resolves, such as a higher inlet or a column, would open the part of the record where the enhancements actually are.

The second is an independent biosphere prior with the right phase. The diagnostic prior used here has the correct daily cycle and a defensible amplitude, but it is not a flux product: its uptake and respiration balance by construction, and its multipliers are therefore statements about this prior, not about Sumatran carbon exchange. A regional biosphere model driven by the same meteorology, checked against the CarbonTracker phase problem documented in Section 4.2, would let the multipliers carry flux meaning.

The third is not more dates of the same kind. That was the expectation before the 2024 window was added, and the enlarged sample settled the question in the opposite direction: 69 dates were enough to resolve that the source terms make the prediction worse, not enough to rescue them. A longer record of the same observations, with the same priors at the same footprint resolution, would sharpen that answer rather than change it.

## 7. Reproducing this

Every number in this report is written into a CSV under `outputs/hysplit/two_receptor/tables` by the stage that computes it, and the report is assembled from those files rather than from prose (Table 11). The report is rebuilt and revalidated against the same tables on every change, and the tests covering the operator, the biosphere construction, the spike screen and the cross-validation machinery run with the project test suite.

**Table 11. Campaign stages and the evidence each one writes.** Every file listed is a CSV under the two-receptor output directory, and every number in this report is read from one of them.

| Stage | Evidence |
| --- | --- |
| 2023 receptor selection and the HYSPLIT ensemble at both towers | `run_ledger.csv` |
| CO₂ inputs, the transport operator and the carbon-dioxide-only spike screen | `co2_operator_base.csv`, `co2_spike_screen.csv` |
| The diagnostic biosphere prior, the afternoon observation and the mixing screen | `co2_diagnostic_operator.csv`, `co2_mixing_screen.csv` |
| The CarbonTracker phase diagnosis | `co2_ctnrt_phase_daily.csv` |
| Scored variants, cross-validation and the date-block bootstrap | `co2_experiments_round6_skill.csv`, `co2_experiments_round6_cv_bootstrap.csv` |
| The BKT release-height campaign and its operator | `co2_bkt_height_operator.csv` |
| The October to December 2024 extension and the methane proxy it uses | `co2_receptor_selection_2024.csv`, `co2_ch4_proxy_validation.csv` |
