# Carbon dioxide seen from two Sumatran towers: Bukit Kototabang and Jambi

## Scientific summary

Bukit Kototabang (BKT) observes carbon dioxide at 865 m in the highlands of western Sumatra; Jambi observes it on the eastern lowland at 25 m above sea level. This report asks what a two-receptor transport inversion can constrain about Sumatran carbon dioxide, using the same HYSPLIT-STILT ensemble, the same towers and the same window as the companion methane study, with the inputs that carbon dioxide requires: EDGAR_2025_GHG fossil emissions, CarbonTracker CT-NRT.v2025-1 ocean, fire and biosphere fluxes, and a CT-NRT endpoint background. Both inlets are taken at 100 m above ground. The analysis covers {{C_WINDOW_2023}} and {{C_WINDOW_2024}}, giving {{C_DATES_BKT}} usable afternoon dates at BKT and {{C_DATES_JMB}} at Jambi, from {{C_RUNS}} five-day runs.

Carbon dioxide cannot use the night hours that methane uses. At 01 WIB the towers see {{C_BKT_18_ENH}} and {{C_JMB_18_ENH}} ppm above background under a model mixing depth of about {{C_NIGHT_PBLH}} m, while the prior gives {{C_BKT_18_PRIOR}} and {{C_JMB_18_PRIOR}} ppm. A quarter-degree footprint cannot resolve the shallow nocturnal layer these observations sit in, so the inversion uses 12 to 14 WIB means only, screened for carbon-dioxide-only spikes and for a modelled mixing depth of at least {{C_MIN_PBLH}} m.

The optimized CarbonTracker biosphere flux cannot serve as the prior for this window. From {{C_INVERTED_FIRST}} to {{C_INVERTED_LAST}} it releases carbon dioxide by day and takes it up at night over {{C_INVERTED_PERCENT}}% of Sumatran land cells, including both tower cells. A diagnostic prior built here from downward shortwave radiation, air temperature and MODIS vegetated fraction keeps the correct phase and carries its uptake and respiration as separate, separately scalable terms.

The test any regional inversion has to pass is predicting a day it did not fit better than its own boundary field carrying a fitted offset and trend. {{C_SKILL_VERDICT}} {{C_2024_VERDICT}}

{{C_FIRE_VERDICT}} {{C_HEIGHT_VERDICT}} The multipliers reported here are adjustment factors on a diagnostic prior under a stated error model, conditional on parameterized transport and an assumed 100 m inlet at both towers; the skill comparisons, not the multipliers, are this report's result.

## 1. Scientific question and scope

The companion two-receptor methane study established what this pair of towers can and cannot do for a long-lived gas whose Sumatran sources are dominated by surface emissions: the joint fit scales regional priors, and the Jambi night record falls outside a quarter-degree model. Carbon dioxide is the harder case. Its regional signal is dominated by a biosphere that changes sign twice a day, its fossil component is small in this part of Sumatra, and its background varies by more than the enhancement the towers see in the afternoon.

The study asks four questions. Which carbon dioxide observations can a quarter-degree transport model represent at these two towers? Does an inversion of those observations predict carbon dioxide better than the boundary field with a fitted offset and trend, which is the null model any regional inversion must beat? Does the answer differ between the highland and the lowland tower? And does the October to December 2024 overlap, four times the sample, reproduce what {{C_DATES_2023}} dates in 2023 appeared to show?

It does not estimate carbon budgets, separate photosynthesis from respiration as independent fluxes, or attribute enhancements to individual sources. The biosphere multipliers reported here scale a diagnostic prior, not a measured flux.

## 2. Evidence and data quality

### 2.1 Observation windows

The two towers overlap in two periods of the harmonized hourly archive. The 2023 period is the window used by the methane study, {{C_WINDOW_2023}}. The 2024 period, {{C_WINDOW_2024}}, is larger and was added to this study because carbon dioxide, unlike methane, needs no CarbonTracker-CH₄ boundary field: CT-NRT.v2025-1 covers both periods, and EDGAR_2025_GHG supplies fossil carbon dioxide for 2023 and 2024 (Table 1).

{{C_WINDOW_TABLE}}

Every fourth joint date was withheld before fitting. Withholding complete dates, rather than hours, keeps correlated error within a day out of the evaluation.

### 2.2 Which hours the model can carry

At both towers the afternoon and the night are different measurement problems (Figure 1, Table 2). At 13 WIB the modelled mixing depth is {{C_BKT_06_PBLH}} m at BKT and {{C_JMB_06_PBLH}} m at Jambi, the observed enhancement is within a few ppm of zero, and the prior is of the same size. At 01 WIB the modelled mixing depth collapses to about {{C_NIGHT_PBLH}} m at both towers, the observed enhancement rises to {{C_BKT_18_ENH}} ppm at BKT and {{C_JMB_18_ENH}} ppm at Jambi, and the prior explains {{C_BKT_18_PRIOR}} and {{C_JMB_18_PRIOR}} ppm of it. The shortfall is not a flux error that a multiplier can absorb; it is a layer the model does not resolve. Night hours are therefore excluded from every fit in this report, at both towers.

![Day and night at the two towers.]({{C_FIG}}/figure_C04_daytime_only.png)

**Figure 1.** Observed carbon dioxide enhancement against the prior at 13 and 01 WIB (a), median modelled mixing depth at the same hours (b), and the mixing depth of every afternoon receptor in 2023 with the {{C_MIN_PBLH}} m screen (c). Error bars in (a) are one standard deviation across hours.

{{C_DIURNAL_TABLE}}

### 2.3 Screens

Four screens stand between the archive and the fit. The observation is the mean of the valid 12 to 14 WIB hours, which suppresses single-hour variability that no quarter-degree model reproduces. A carbon-dioxide-only spike screen removes hours where carbon dioxide departs from its neighbours while methane and carbon monoxide do not, the signature of a local plume too small to model: {{C_SPIKE_HOURS}} of {{C_SPIKE_TESTABLE}} testable hours are flagged, the larger being {{C_SPIKE_SIZE}} ppm at Jambi on {{C_SPIKE_DATE}}, an hour on which methane moved by {{C_SPIKE_CH4}} ppb and carbon monoxide by {{C_SPIKE_CO}} ppb. A transport screen keeps only receptor hours where every seed retains at least 95% of its particles at 120 h. A mixing screen removes afternoon hours whose modelled mixing depth is below {{C_MIN_PBLH}} m, where the model's own diagnosis says the afternoon boundary layer has not developed (Table 3).

{{C_SCREEN_TABLE}}

## 3. Methods

### 3.1 Transport ensemble

Each receptor hour is simulated at both towers with HYSPLIT 5.4.2 in STILT mode, 120 h backward, with {{C_SEEDS_2023}} random seeds of 2,000 requested particles in 2023 and {{C_SEEDS_2024}} in 2024, driven by the NOAA GFS quarter-degree archive cropped server-side to 50° to 160° E and 40° S to 30° N. Footprints are written hourly on a 0.25° grid spanning 60° of latitude and 100° of longitude centred on each tower, normalized by the number of particles actually emitted and averaged across seeds. A separate campaign repeats the BKT afternoon receptors with the release raised to 150 m and to 300 m above model ground (Section 4.5).

### 3.2 Priors and boundary

Fossil emissions are EDGAR_2025_GHG monthly carbon dioxide for the month of each receptor hour, split into the part within 500 km of the observing tower and the part beyond. Ocean exchange and fire emissions are the CT-NRT.v2025-1 three-hourly fields. The background of each receptor hour is the CT-NRT.v2025-1 mole fraction sampled at the position and height of every retained particle at 120 h, with height above model terrain converted to altitude, averaged with equal weight.

The biosphere is the difficult term, and Section 4.2 shows why the optimized CT-NRT flux cannot supply it here. The prior used instead is diagnostic. Gross uptake in each cell is proportional to de-accumulated GFS downward shortwave radiation times the MODIS MCD12C1 vegetated fraction, scaled so that a fully vegetated cell takes up {{C_GPP_SCALE}} gC m⁻² yr⁻¹; respiration follows a Q10 of {{C_Q10}} about the cell's own mean temperature, and is scaled so that uptake and respiration balance in each cell over the window. Uptake and respiration enter the inversion as two separate response columns, so the fit can scale the daytime sink and the night-time source independently, and at each tower separately.

### 3.3 Inversion

Each observation is modelled as the endpoint background, plus fixed ocean and fire terms, plus the sum of prior increments each scaled by its own multiplier, plus a per-tower offset and linear trend. Fossil multipliers are positive with log-normal priors; the biosphere response columns are signed, because uptake reduces the mole fraction, so the inversion uses a signed formulation in which a positive multiplier scales a negative column. Nuisance covariates enter as unconstrained Gaussian terms.

The error covariance for each tower combines a {{C_MEAS_PPM}} ppm measurement allowance, a local mismatch of {{C_LOCAL_DAY_PPM}} ppm by day, a background term of {{C_BG_PPM}} ppm with 72 h correlation, and a transport error equal to a fraction of the hour's total prior increment with 24 h correlation. That fraction is tuned separately for each tower to a training reduced chi-square of one, because a single shared fraction is set by whichever tower fits worst and then inflates the other tower's errors until nothing can be resolved there. Errors are correlated within a tower and independent between towers. Posteriors are sampled by Markov chain Monte Carlo and accepted only with R-hat at most 1.01 and an effective sample size of at least 1,000 for every parameter.

### 3.4 Cases and evaluation

The variants compared here differ in four ways: which biosphere prior supplies the response columns, whether biosphere multipliers are shared between the towers or fitted per tower, which nuisance covariates are admitted, and which period is fitted (Table 4). The covariates tested at each tower are the endpoint background itself, the methane enhancement above the tower's own rolling clean-air baseline, and the methane residual from the companion inversion; the methane terms are proxies for local, poorly modelled surface influence that carbon dioxide shares with methane but the carbon dioxide prior does not contain.

{{C_VARIANT_TABLE}}

Every variant is scored three ways. Withheld dates give an honest but small test. All-daytime residuals give the in-sample fit. Leave-one-date-out cross-validation refits the model without each date and predicts that date, which uses every date once as a test and is the primary measure here. The comparison is always against the same null: the endpoint background with a fitted per-tower offset and trend and no source terms. Because dates are few and their errors are correlated within a day, the difference in cross-validated RMSE is bootstrapped by resampling whole dates, {{C_BOOT_REPS}} times.

## 4. Results

### 4.1 The afternoon signal is small

Over the afternoon receptors the observed carbon dioxide sits within a few ppm of the CT-NRT background, and the prior increments are of the same size as the residual the inversion has to explain (Table 5). The mean prior increments at the afternoon receptors are {{C_BKT_GPP}} ppm of gross uptake and {{C_BKT_RESP}} ppm of respiration at BKT, {{C_JMB_GPP}} and {{C_JMB_RESP}} ppm at Jambi, against fossil increments of {{C_BKT_FOSSIL}} and {{C_JMB_FOSSIL}} ppm. The two biosphere terms nearly cancel, so the quantity the data constrain is the small difference between two large opposing terms, and the fossil term is an order of magnitude smaller than either.

{{C_PRIOR_TABLE}}

### 4.2 The optimized biosphere flux runs backwards

The CT-NRT.v2025-1 optimized biosphere flux inverts its daily cycle for a week of this window (Figure 2). From {{C_INVERTED_FIRST}} to {{C_INVERTED_LAST}} it releases carbon dioxide during the local day and takes it up at night over {{C_INVERTED_PERCENT}}% of Sumatran land cells, and both tower cells are among them. Over the whole window the same field has the ordinary phase, so the fault is episodic rather than systematic, but an inversion cannot use a prior whose sign is wrong for a quarter of its data and right for the rest.

![Optimized and diagnostic biosphere priors.]({{C_FIG}}/figure_C02_biosphere_priors.png)

**Figure 2.** Net biosphere flux by local solar hour at the BKT cell (a) and the Jambi cell (b), for the CT-NRT optimized flux over the whole window, the same flux during the inverted week, and the diagnostic prior; and the share of CarbonTracker land cells with an inverted day-night cycle on each day (c).

The diagnostic prior replaces it. Its phase follows sunlight, so it cannot invert, and its two halves are separately scalable, so an error in either is absorbed by a multiplier rather than by the offset. Fitting the two cases side by side, the diagnostic prior {{C_PRIOR_VERDICT}}

### 4.3 Posterior multipliers

The headline cases and their posteriors are in Table 6.

{{C_PARAM_TABLE}}

The fossil multipliers are close to their priors with intervals spanning an order of magnitude, which is the expected result for a term worth {{C_BKT_FOSSIL}} ppm at BKT and {{C_JMB_FOSSIL}} ppm at Jambi, against a biosphere difference many times larger. The contrast with the all-hours fits is instructive: fitting the night hours as well drives the Jambi-only fossil multipliers to {{C_NIGHT_FOSSIL_NEAR}} and {{C_NIGHT_FOSSIL_FAR}}, the inversion's only way to manufacture the tens of ppm the nights show, and a second reason to treat those hours as outside the model rather than as evidence about emissions. A biosphere prior with no water or nutrient limitation should overstate the amplitude of the afternoon drawdown the towers actually see, and the fit says it does. {{C_BIO_VERDICT}}

### 4.4 Skill against the background

The test that matters is whether any of this predicts carbon dioxide better than the boundary field with a fitted offset and trend (Figure 3, Figure 4, Table 7).

![Afternoon series at both towers.]({{C_FIG}}/figure_C01_series.png)

**Figure 3.** Observed afternoon carbon dioxide at the two towers with the prior, the background-only model and the posterior of the headline case, by period. Lines break where no receptor passed the screens.

![Out-of-sample skill by variant.]({{C_FIG}}/figure_C03_scoreboard.png)

**Figure 4.** Leave-one-date-out RMSE by variant and tower against the background-only null (a), and the difference with its 95% date-block bootstrap interval (b).

{{C_SKILL_TABLE}}

{{C_SKILL_VERDICT}}

{{C_NUISANCE_VERDICT}}

Resampling whole dates gives the interval on each of those differences (Table 8).

{{C_BOOT_TABLE}}

{{C_RESOLVE_VERDICT}}

### 4.5 Does the larger sample reproduce the 2023 result?

{{C_2024_TEXT}}

{{C_2024_VERDICT}}

Combining two periods ten months apart puts every 2024 receptor about thirteen prior standard deviations along a trend line centred on the 2023 window, which is a strong assumption to carry into the headline number. The combined fit was therefore repeated with an offset and a trend inside each period, so that no straight line spans the gap. {{C_PERIOD_VERDICT}}

### 4.6 The fire term

In 2023 fire contributed nothing at either receptor. In the 2024 window it does: the CT-NRT pyrogenic flux reaches {{C_FIRE_MAX}} ppm at a Jambi receptor and averages {{C_JMB_FIRE}} ppm there, in a term the inversion holds fixed in its baseline rather than scaling. A variant that moves fire out of the baseline and gives it its own multiplier tests whether that fixed term is what the fit is fighting (Table 9).

{{C_FIRE_TABLE}}

{{C_FIRE_VERDICT}}

### 4.7 Release height at Bukit Kototabang

The GFS quarter-degree terrain in the BKT receptor cell is {{C_BKT_SHGT}} m, against a station elevation of 865 m, so a release 100 m above model ground sits about {{C_BKT_GAP}} m below the true inlet altitude on a smoothed mountain. Repeating every BKT afternoon receptor with the release at 150 m, the true inlet altitude over GFS terrain, and at 300 m tests whether that mismatch matters (Figure 5, Table 10).

![Release height and the methane covariate.]({{C_FIG}}/figure_C05_height_and_proxy.png)

**Figure 5.** Paired change in the modelled response when the BKT release is raised from 100 m (a), out-of-sample error at each release height (b), and the methane enhancement proxy checked against the modelled methane enhancement on the 2023 receptors (c).

{{C_HEIGHT_TABLE}}

{{C_HEIGHT_VERDICT}}

## 5. What this does and does not show

This study answers its first question and returns a negative answer to the second.

It establishes which carbon dioxide observations at these towers are usable at all: the afternoon, screened, at both towers, and nothing at night. It establishes that the optimized CarbonTracker biosphere flux cannot serve as the prior for this window, and that a diagnostic prior with the right phase can be built from routine meteorology instead. It bounds the amplitude of that prior against the observations, through multipliers well below unity at both towers, and it bounds the CT-NRT fire term, which the fit scales down by about a factor of two.

What it does not do is predict carbon dioxide better than its own boundary field. {{C_NEGATIVE_SUMMARY}}

Three things follow. The inversion does not constrain fossil emissions: the fossil increments are about a ppm at the receptor, an order of magnitude below either biosphere term, and their multipliers return their priors. It does not separate photosynthesis from respiration, because in the afternoon the two response columns move together, correlating at {{C_BIO_COLLINEAR}}, so the data constrain their difference and not the pair. And the multipliers below unity are a statement about the prior's amplitude rather than evidence that the scaled prior describes the flux: a model can be drawn toward the observations in sample and still predict a withheld day worse than a fitted constant does.

## 6. Extending the analysis

{{C_EXTEND_TEXT}}

## 7. Reproducing this

Every number in this report is written into a CSV under `outputs/hysplit/two_receptor/tables` by the stage that computes it, and the report is assembled from those files rather than from prose (Table 11). The report is rebuilt and revalidated against the same tables on every change, and the tests covering the operator, the biosphere construction, the spike screen and the cross-validation machinery run with the project test suite.

{{C_SCRIPT_TABLE}}
