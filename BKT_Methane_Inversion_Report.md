# Regional methane emissions constrained by Bukit Kototabang: a transport-ensemble inversion for September–October 2019

## Scientific summary

Bukit Kototabang (BKT) observes methane at 865 m on the west coast of Sumatra. This report asks whether four weeks of its hourly record can scale regional methane emission priors when transport, boundary values and natural exchange are modeled explicitly. The inversion uses 52 twice-daily receptor hours between 9 September and 6 October 2019, 39 for fitting and 13 withheld before fitting, with five-day HYSPLIT-STILT footprints on a 50°–160° E, 40° S–30° N domain driven by quarter-degree Global Forecast System (GFS) meteorology, three seeds of 2,000 particles per hour, NOAA CarbonTracker-CH₄ boundary values at particle endpoints, and a positive-emission Bayesian fit of four regional multipliers.

The prior model, inventory plus modeled background, over-predicts the observations by +76 ppb on average. With the working error covariance of the original design, which assigns half of every prior increment to transport error, the refit on the revised ensemble scales the four components to 0.57, 0.45, 0.58 and 0.71 and predicts withheld hours to 36.2 ppb RMSE, worse than a fitted background alone (28.5 ppb). That covariance is inconsistent with the residuals: its training reduced chi-square is 0.26. Reducing the transport-error fraction to 0.10, where the reduced chi-square is one, gives multipliers of 0.37 (0.15–0.70) for anthropogenic emissions within 500 km, 0.24 (0.10–0.45) beyond 500 km, 0.43 (0.16–0.91) for wetlands and 0.68 (0.39–1.00) for non-crop fires (posterior medians with 95% intervals), withheld RMSE 25.3 ppb against 28.5 ppb for the background-only baseline, and a withheld bias of +6.5 ppb. The anthropogenic and wetland intervals exclude the inventory value; the fire interval reaches it at 1.00.

Repeating the ensemble with hourly ERA5 meteorology gives 49 usable hours, a prior over-prediction of +104 ppb, multipliers of 0.32 (0.12–0.65), 0.29 (0.12–0.57), 0.40 (0.15–0.84) and 0.53 (0.24–0.90) under its own consistent covariance, and withheld RMSE 39.2 ppb against 26.6 ppb for background only. The downward scaling of every prior is robust to the driver; the ability to out-predict a fitted background is not. The estimates remain conditional on parameterized transport without resolved convection, on boundary fields that assimilate BKT, and on fixed within-region source patterns. They are regional adjustment factors under a stated error model, not independently verified emission totals.

## 1. Scientific question and scope

A complementary experiment asks whether the BKT methane time series can constrain broad emission adjustments after accounting for boundary methane and natural exchange. It spans 9 September–6 October 2019 inclusive, with receptors at 06:00 and 18:00 UTC (13:00 and 01:00 WIB). This fixed schedule samples contrasting mountain boundary-layer regimes without selecting hours for their agreement with a model. The inverse state is deliberately low-dimensional: anthropogenic emissions within and beyond 500 km of BKT, wetlands, non-crop fires, and a background offset and trend. Grid cells are assigned by their center's WGS 84 geodesic distance, so the regional partition retains the transport grid's finite spatial resolution. It does not retrieve separate emissions for each province, sector, facility or grid cell. The five-day inversion footprint uses a wider domain, approximately 76.3°–124.3° E and 18.2° S–17.8° N; quantities outside it are unrepresented rather than assumed absent.

The design was executed twice. The original transport ensemble used one seed of 540 particles per receptor hour on a 75°–130° E, 20° S–20° N domain, from which 25 hours lost more than 5% of their particles across the boundary and were excluded. The revised ensemble, which supplies the principal results of this report, uses the widened domain, three seeds of 2,000 particles per hour, a second concentration layer to 1,000 m, and retains every particle at every hour. A third ensemble repeats the revised design with ERA5 meteorology. The original results are retained in Section 4.1 because the revision was designed to test them, not to replace them silently.

## 2. Evidence and data quality

### Methane observations, flasks and priors

Section 4.1 reports the observation coverage, the flask comparisons and the prior concentration budget in full, with the original transport ensemble; the same observations, priors and boundary fields feed the revised fits. The anthropogenic prior is the September and October 2019 EDGAR v8.0 monthly flux; wetlands are LPJ-EOSIM driven by MERRA-2; non-crop fires are daily GFED5.1 with agricultural burning removed to avoid double counting with EDGAR; termites, geological seepage and soil uptake are fixed auxiliary fields. Their provenance, unit conversions and known limitations are given in the methods; none is a contemporaneous measurement of the fluxes the receptor actually saw.

## 3. Methods

The original transport, boundary and inversion methods follow. The revised ensemble changes only the transport design and the error-model test described in the final subsection; priors, boundary sampling, the inverse state and the evaluation protocol are unchanged, so that differences in the results are attributable to transport and to the error model.

### Multi-week methane observations and source priors

The inversion period contains 619 valid hourly methane measurements out of 672 expected hours (92.1% coverage). Of 56 scheduled receptor hours, 52 have valid measurements and 4 are unavailable; missing hours remain gaps. Every fourth calendar day was designated for withholding before fitting. The transport-retention screen described below excludes 25 observation-valid receptors (48.1%), leaving 27 receptor hours: 21 fitting and 6 withheld. Available flags are respected; observations are not removed because of large model residuals. Co-located NOAA flask samples on the CH₄ X2004A scale provide 4 comparisons in the study period. Flask-minus-in-situ differences range from -1.19 to +1.27 ppb, with mean -0.06 ppb. These sparse comparisons support consistency at sampled times, but do not establish the complete hourly calibration or representativeness uncertainty.

EDGAR September and October 2019 monthly fluxes supply the anthropogenic prior. LPJ-EOSIM wetland methane driven by MERRA-2 supplies corresponding monthly natural emissions, using the GEOS-Chem distributed LPJ-MERRA2 product [10]. Daily GFED5.1 supplies fires [5]. The fixed auxiliary budget includes CAMS termite emissions (monthly 2000 climatological proxy), a scaled geological seep field, and MeMo soil uptake (1990–2009 monthly climatology); these are not contemporaneous 2019 measurements [11, 12]. The MeMo field is already distributed in kg CH₄ m⁻² s⁻¹; the original publication's supplementary-unit corrigendum is respected. All fields are conservatively area-averaged to the transport grid, with explicit sign and mass-to-molar conversion. Lakes, reservoirs and ocean exchange are not separately resolved; omitted or misplaced exchange remains structural uncertainty.

Agricultural burning is retained in EDGAR and removed from GFED methane to reduce double counting. Monthly GFED cropland carbon is converted using the provider's agricultural emission factors: 2.142 g CH₄ kg⁻¹ dry matter and 419.4 g C kg⁻¹ dry matter. The resulting cell-specific crop fraction is applied to each day's total fire methane. This assumes crop burning shares the cell's total-fire daily profile; it is not a directly observed daily crop partition. A sensitivity fit retains the overlapping crop term to assess the effect of this choice. All emissions are represented as surface release; fire plume rise and elevated industrial injection are not independently specified.

### Five-day transport and endpoint boundary methane

Each base receptor releases particles backward for 120 h at 30 m above model ground. The requested 500 particles result in 540 actual emitted particles under the model's release schedule; coefficients are normalized to the actual count. This lower count supports a multi-receptor design, with adequacy assessed at preselected 2,000-particle benchmarks rather than assumed from the higher-count single-hour case. Time-resolved, unsmoothed surface sensitivities are multiplied by the matched fluxes. The GFS driver retains 0.25° spacing, three-hourly fields and 55 hybrid levels. STILT mixing-depth settings follow the documented modified-Richardson-number configuration with a 250 m minimum. The GFS archive lacks the Grell convective mass-flux fields required by the selected convective redistribution option; deep-convective transport is therefore not independently resolved by that option. This is a material tropical transport limitation, not remedied by plotting at finer spacing.

NOAA CarbonTracker-CH₄ CT-CH₄-2025 supplies global three-dimensional background mole fractions at backward particle endpoints [9]. Its 3° longitude × 2° latitude fields contain 25 atmospheric layers at three-hour intervals. Equal particle-probability weights are used, not the accumulated footprint diagnostic mass. Endpoint heights above ground are converted to mean-sea-level heights using GFS terrain. Methane and layer-boundary heights are interpolated horizontally; methane is then interpolated vertically between layer centers, clamping values below the lowest center and reporting their frequency. The sampled background is the particle mean. The ±500 m endpoint-height tests assess vertical sampling sensitivity. Only runs retaining at least 95% of emitted particles at the endpoint are used; 25 receptor hours fail this transport criterion.

CarbonTracker assimilates observations at BKT, including daytime in-situ and flask data. It is thus a physically informed boundary estimate, not a fully independent validation dataset. Withheld BKT concentrations are not used by the regional optimizer, but information can already be present in the global boundary analysis. Independence claims are restricted accordingly. The background is not estimated as the local minimum or by subtracting the same inventory contribution being tested.

### Positive-emission Bayesian inversion

For receptor hour $i$, the concentration model is

$$
c_i=b_i+\beta_0+\beta_1\tau_i+\sum_{k=1}^{4}K_{ik}\exp(\theta_k)+a_i+\epsilon_i.
$$

Here $c_i$ and $b_i$ are observed and endpoint-background methane in ppb; $\tau_i$ is elapsed time from 23 September divided by 28 days; $K_{ik}$ is the prior source increment in ppb; $\alpha_k=\exp(\theta_k)$ is a dimensionless positive emission multiplier; and $a_i$ is the fixed termite plus geological contribution minus soil uptake. Each $K_{ik}$ is a sum of unsmoothed hourly footprint coefficients times molar flux, multiplied by 1,000 to convert ppm to ppb. No extra cell-area or hour-duration factor is applied because the footprint coefficients already integrate their cell and source interval. The Gaussian residual $\boldsymbol\epsilon$ has covariance $\mathbf R$ in ppb².

The four independent log multipliers have prior $\theta_k\sim N(0,[\ln 2]^2)$. Thus unity is the prior median, not the prior mean. Background priors are $\beta_0\sim N(0,20^2)$ ppb and $\beta_1\sim N(0,10^2)$ ppb per 28 days. The fitted posterior is proportional to the multivariate Gaussian likelihood times these priors. Working mismatch covariance combines independent 5 ppb measurement/calibration allowance; 20 ppb daytime or 40 ppb nighttime representativeness; 50% of each receptor's total prior source increment, correlated exponentially over 24 h; and 10 ppb boundary variability, correlated over 72 h. An additional diagonal allowance equals the squared sum of absolute auxiliary-source contributions. These values are explicit working assumptions, informed by published transport-error approaches and methane inversion practice, not BKT-derived uncertainty estimates [8, 13].

Four random-walk Metropolis Markov chain Monte Carlo (MCMC) chains sample the nonlinear posterior in log-emission space. Each chain retains 12,000 draws after 6,000 burn-in iterations, with three sampling steps between saved draws; proposal-scale adaptation stops after burn-in. The random seed is 20190909. Rank-normalized split convergence statistics and effective sample sizes diagnose sampling; acceptance requires maximum $\hat R\leq1.01$ and minimum effective sample size of 1,000. Reported emission intervals are equal-tailed 95% posterior credible intervals, conditional on the model and priors. They do not include all structural uncertainty. Prior-whitened local singular values and posterior correlations assess how many parameter combinations the measurements inform, without treating mapped pixels as independent retrievals.

### Evaluation, sensitivity and synthetic recovery

Evaluation compares the training-only posterior with unadjusted inventories, a fitted background-only baseline, and an inventory baseline with the same fitted background offset and trend. RMSE, bias, mean absolute error (MAE), correlation and coefficient of determination are reported separately for fitting and withheld hours. No residual correction is trained on withheld measurements. Nominal 95% marginal prediction envelopes add fresh draws of the stated mismatch to parameter-based predictions; they do not condition correlated errors on fitting-data residuals. Their coverage is a descriptive diagnostic, not a fully conditioned Gaussian forecast or a calibration claim. Intervals on model-mean concentrations include parameter uncertainty only. Four additional leave-one-week-out fits exclude a 24 h buffer around each held week, reducing immediate temporal dependence but not establishing an independent atmospheric network.

Robustness tests vary background offset and prior width, emission prior width, transport-error magnitude and correlation time, representativeness allowance, auxiliary sources, crop overlap, and daytime-only fitting. A reduced-state fit imposes one shared anthropogenic multiplier on both regions to test dependence on regional separation. A geological-source test reverses the distributed field's global scaling from 37.5 to 1.6 Tg yr⁻¹, reflecting the difference between its gridded inventory and radiocarbon-based constraint [12]. These use posterior modes with local Gauss–Newton interval approximations; their spread is a sensitivity range, not another probability interval. Transport checks at preselected receptor hours vary random seed, particle count, release height and backward duration. Comparisons are limited to these anchors and do not certify convergence at every receptor.

Synthetic tests use the actual response matrix, known multipliers (1.5, 0.7, 1.2 and 0.6), and 200 correlated-noise realizations per scenario. A matched-operator scenario tests recoverability under the assumed model. A second scenario introduces coherent 30% source-response perturbations and an unmodeled 15 ppb nonlinear boundary signal. Recovery bias, RMSE and local-interval coverage diagnose regularization and vulnerability to model error; these synthetic truths are not estimates of actual emissions.

### Revised transport ensemble, error-model consistency and driver sensitivity

Each of the 52 receptor hours was rerun for 120 h on the 50°–160° E, 40° S–30° N meteorological crop with a 60° by 100° footprint grid and three seeds of 2,000 requested particles. Coefficients are normalized to the actual emitted count and averaged across seeds; the seed spread supplies a direct estimate of finite-particle noise in every prior increment. All hours retain 100% of their particles at 120 h, so the 95% retention screen no longer removes any receptor. A fixed concentration layer to 1,000 m is recorded alongside the STILT surface layer for later injection-height tests; it is not used in the fit.

The working error covariance of the original design assigned 50% of each hour's total prior increment to correlated transport error. Whether that magnitude is consistent with the data is testable: at the posterior mode, the whitened data residuals of a consistent Gaussian model have a reduced chi-square near one. The transport fraction was therefore scanned from 0.05 to 1.0 with all other covariance terms fixed, and the fraction at which the training reduced chi-square equals one was adopted as the tuned covariance. Because the fraction is chosen on the fitting hours, the withheld evaluation remains the independent test of the tuned fit. A five-component variant splits the within-500 km anthropogenic term at 50 km, to expose how much of the near-region constraint rests on the few inventory cells around the station.

The ERA5 ensemble repeats the revised design with hourly ECMWF ERA5 pressure-level meteorology (16 levels, 70°–140° E, 25° S–20° N) converted to HYSPLIT format with the ECMWF turbulent heat fluxes mapped to HYSPLIT's upward-positive convention; the ERA5 footprint grid is 40° by 60°. Its operator, covariance scan and fits use the same code path.

## 4. Results

### 4.1 Results with the original transport ensemble

### Methane observation coverage and prior concentration budget

The multi-week experiment retains 27 receptor hours, covering both daytime and nighttime conditions (Figure 1). The four flask comparisons differ from in-situ values by at most 1.27 ppb; their small number prevents extending this agreement to every hourly record. The anthropogenic prior and the mean transport sensitivity have distinct geographic structures (Figure 2): a high-emission cell matters to BKT only where transport provides sensitivity to it.

![Methane receptor selection and flask comparisons.](outputs/hysplit/inversion/figures/figure_13_inversion_observations.png)

**Figure 1.** BKT hourly methane and the fixed twice-daily receptor selection, 9 September–6 October 2019. Filled circles enter fitting; open squares are withheld; crosses identify transport-ineligible receptor hours. Gaps remain unfilled. The lower panel shows NOAA flask-minus-in-situ methane at co-located sampled hours, in ppb. These comparisons assess sampled consistency, not a complete calibration uncertainty budget.

![Anthropogenic methane prior and mean transport sensitivity.](outputs/hysplit/inversion/figures/figure_14_inversion_support.png)

**Figure 2.** Period-weighted EDGAR anthropogenic methane flux and mean five-day BKT sensitivity for transport-eligible receptor hours. Flux is in µmol m⁻² s⁻¹; sensitivity density is ppm per (µmol m⁻² s⁻¹) per km². Both color scales are logarithmic. The star marks BKT and the dashed circle marks the 500 km geodesic partition. Sensitivity display uses Gaussian smoothing with standard deviation one 0.25° cell and fourfold interpolation, conserving its integral; inversion coefficients remain unsmoothed. The lower color threshold omits 1.00% of integrated display sensitivity, and 6.7% lies outside the map frame; these quantities are not additive because they overlap. Flux-color extensions denote values outside the displayed range; zero flux is transparent. Indonesia uses the established provincial GeoJSON and surrounding countries use full-resolution geoBoundaries.

The endpoint background ranges from 1826.8 to 1904.7 ppb across the retained hours. Median prior increments are 39.4 ppb from anthropogenic emissions within 500 km, 16.1 ppb from farther anthropogenic emissions, 20.9 ppb from wetlands and 20.3 ppb from non-crop fires. These are prior-model contributions, not measured source fractions (Figure 3). Across all receptor hours, the unadjusted inventory-plus-background prediction has bias 79.1 ppb and RMSE 101.0 ppb. A mismatch can arise from source magnitude, source timing, transport or boundary error; its sign alone does not identify the responsible component.

![Background and prior source increments.](outputs/hysplit/inversion/figures/figure_15_inversion_components.png)

**Figure 3.** Observed methane, particle-endpoint CarbonTracker background, and the unadjusted concentration budget at the selected BKT hours. The lower panel separates four positive prior source increments and the negative soil-uptake contribution. Fixed termite and geological terms are included in the upper budget but not the positive stack. Units are ppb. Monthly anthropogenic and wetland patterns, daily non-crop fire fluxes, and five-day GFS/HYSPLIT-STILT sensitivities determine these prior increments.

#### Information content and posterior emission adjustments

The source-response matrix contains correlated spatial and temporal information (Figure 4). The sum of local prior-whitened information fractions is 1.97 across the six fitted parameters; it is not a count of resolved emission pixels. The strongest absolute off-diagonal source-response correlation is 0.55. Distinguishing components requires differences in their transport-weighted time series, not merely different inventory labels.

![Source-response correlations and information modes.](outputs/hysplit/inversion/figures/figure_16_inversion_information.png)

**Figure 4.** Pearson correlations among training-hour prior source responses and local prior-whitened information fractions for the six-parameter inverse state. If $s_j$ is a singular value of the whitened local Jacobian, the plotted fraction is $s_j^2/(1+s_j^2)$. The matrix describes response similarity without a significance test; the mode plot includes background parameters and does not establish spatial resolution.

**Table 1. Methane inverse parameters.** Emission multipliers are dimensionless; background offset is in ppb and trend in ppb per 28 days. Medians and 95% credible intervals come from the sampled posterior. The variance reduction is in the fitted parameter space (log space for emissions), relative to its stated prior; negative values indicate increased variance.

| Parameter | Prior median | Posterior median (95%) | Variance reduction (%) |
| --- | --- | --- | --- |
| Anthropogenic ≤500 km | 1.0 | 0.58 (0.20–1.33) | 48.8 |
| Anthropogenic >500 km | 1.0 | 0.51 (0.18–1.10) | 55.3 |
| Wetlands | 1.0 | 0.64 (0.20–1.56) | 43.0 |
| Non-crop fires | 1.0 | 0.76 (0.27–1.57) | 56.5 |
| Background offset | 0.0 | -3.80 (-32.87–24.60) | 45.8 |
| Background trend | 0.0 | -1.17 (-20.29–18.24) | 3.9 |

The 95% interval for anthropogenic ≤500 km includes unity. The 95% interval for anthropogenic >500 km includes unity. The 95% interval for wetlands includes unity. The 95% interval for non-crop fires includes unity. The strongest posterior parameter correlation is -0.22 between non-crop fires and background offset (log multipliers for emissions, linear background terms). This quantifies dependence among fitted quantities rather than a causal relation between sources. The maximum chain diagnostic is 1.001 and minimum effective sample size is 5,727, satisfying the declared numerical sampling criteria. Successful sampling establishes computational convergence for this model, not the correctness of transport or emission attribution.

![Prior and posterior methane emission multipliers.](outputs/hysplit/inversion/figures/figure_17_inversion_posterior.png)

**Figure 5.** Prior and posterior emission intervals for the four-component methane state. Emission multipliers use a logarithmic axis; unity is the inventory reference. Lower panels show fitted background adjustments. Dots are posterior medians and colored intervals are equal-tailed 95% credible intervals from MCMC. Their interpretation is conditional on the response matrix, fixed source patterns and working covariance.

#### Withheld prediction and residual evidence

The posterior withheld RMSE is 47.6 ppb, compared with 98.7 ppb for raw inventories, 40.0 ppb for the fitted background-only model and 86.0 ppb for background-adjusted inventories (Table 2; Figure 6). Emission fitting improves the withheld point-prediction RMSE relative to the adjusted-inventory baseline, but this finite conditional comparison does not establish independently validated emissions. The simpler fitted background-only model performs better (40.0 ppb RMSE); source fitting therefore does not demonstrate incremental predictive value over that baseline. The nominal 95% marginal prediction envelope contains 100.0% of withheld concentrations. Its median withheld width is 299.2 ppb, compared with 91.3 ppb for parameter-only intervals. Coverage must be considered alongside these widths and the small evaluation sample; a broad envelope can cover observations without precise emission information.

**Table 2. Methane concentration evaluation.** The split was specified before fitting; n is the number of receptor hours. Bias is predicted minus observed methane; MAE and RMSE are in ppb. Pearson r and R² are dimensionless; negative R² means squared errors exceed the squared departures of observations from their evaluation-sample mean. These are conditional concentration diagnostics, not errors against independently measured emissions.

| Split | n | Model | Bias | MAE | RMSE | r | R² |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Fit | 21 | Raw inventory | +80.0 | 80.7 | 101.7 | 0.45 | -6.21 |
| Fit | 21 | Background only | -43.5 | 47.2 | 61.5 | -0.05 | -1.63 |
| Fit | 21 | Adjusted inventory | +62.6 | 66.9 | 88.7 | 0.45 | -4.48 |
| Fit | 21 | Inversion | +24.7 | 40.2 | 48.5 | 0.50 | -0.64 |
| Withheld | 6 | Raw inventory | +75.9 | 76.6 | 98.7 | 0.41 | -16.12 |
| Withheld | 6 | Background only | -34.1 | 34.8 | 40.0 | 0.58 | -1.81 |
| Withheld | 6 | Adjusted inventory | +58.5 | 68.8 | 86.0 | 0.41 | -12.00 |
| Withheld | 6 | Inversion | +25.4 | 40.9 | 47.6 | 0.49 | -2.99 |

![Methane predictions and withheld comparisons.](outputs/hysplit/inversion/figures/figure_18_inversion_predictions.png)

**Figure 6.** Training-only posterior predictions for all retained BKT receptor hours, with 95% model-mean intervals and nominal 95% marginal mismatch-augmented envelopes. Open squares identify withheld observations. The lower panels compare withheld predicted and observed methane and RMSE against three baselines. The outer envelope does not condition correlated errors on training residuals and is not a fully conditional Gaussian forecast. CarbonTracker's assimilation of BKT limits strict independence.

Residuals span -97.0 to +53.3 ppb (observed minus posterior median). Their time evolution and relation to native GFS boundary-layer height and endpoint background are shown in Figure 7. Daytime residual RMSE is 53.6 ppb and nighttime RMSE is 43.6 ppb over the full retained sample; these descriptive regime diagnostics mix fitted and withheld hours. A residual association with boundary-layer height cannot by itself identify a mixing-depth bias, because emissions and meteorology co-vary.

![Posterior residual diagnostics.](outputs/hysplit/inversion/figures/figure_19_inversion_residuals.png)

**Figure 7.** Methane residual time series, distributions by fit/withheld split, and relationships with native GFS planetary boundary-layer height and endpoint background, 9 September–6 October 2019. Residuals are observed minus the training-only posterior median, in ppb. The native GFS boundary-layer height is meteorological context rather than the STILT-computed mixing depth. The height scatter omits 2 nonphysical negative decoded heights whose magnitudes fall within their archive records' packing-precision scale; the corresponding concentrations remain in the inversion and other panels. No observations were removed on the basis of these residuals.

#### Robustness and recoverability

Across the stated non-base assumption tests, posterior-mode anthropogenic multipliers range from 0.48 to 0.76 within 500 km and 0.42 to 0.69 farther away (Figure 8). These scenario extrema have no assigned probability. In leave-one-week-out fits with a 24 h buffer, posterior RMSE ranges from 28.6 to 72.8 ppb and is lower than the background-adjusted inventory in 4 of four held weeks, but lower than the background-only baseline in only 1 of four. The four weekly evaluation samples contain 3, 14, 9, 1 receptor hours, respectively. These highly unequal counts reflect transport screening; a week with one retained hour supplies only a single-error diagnostic, not evidence of general weekly skill. Buffered exclusions test temporal dependence but remain a single-site, single-season evaluation.

![Methane inversion sensitivity to assumptions.](outputs/hysplit/inversion/figures/figure_20_inversion_sensitivity.png)

**Figure 8.** Anthropogenic emission adjustments under alternative background, covariance, prior, auxiliary-source, crop-overlap and daytime-sampling assumptions. Shading is the base-case sampled 95% credible interval; points are separately optimized modes in log-emission parameter space, transformed to multipliers. Both axes are logarithmic. Scenario spread is not a credible interval, and crossing the inventory reference indicates sensitivity to assumptions rather than a change in observed emissions.

**Table 3. Transport and boundary sensitivity at preselected anchors.** Changes are relative to the base run at the same receptor hour. Source-increment change includes the four optimized positive source components before fitting. Background differences are evaluated only where both runs retain at least 95% of particles; otherwise they are not evaluable. In low-retention runs, integrated source sensitivity is truncated by domain exits and is not a complete-duration convergence test. This table does not establish convergence for all receptor hours or all atmospheric regimes.

| Test (anchors) | Sensitivity change (%) | Source change (%) | Background change (ppb) | Retention (%) |
| --- | --- | --- | --- | --- |
| Alternate seed (4) | +0.6 to +5.5 | -17.9 to +10.8 | -4.5 to +0.7 | 96.1 to 100.0 |
| 60 m release (4) | +0.3 to +8.8 | -2.3 to +40.7 | -3.8 to +0.2 | 97.0 to 100.0 |
| 2,000 requested particles (2) | -3.8 to +2.8 | -7.2 to +16.4 | -2.2 to +0.7 | 99.0 to 100.0 |
| 72 h window (2) | -21.8 to -20.2 | -36.1 to -15.9 | +20.2 to +25.6 | 100.0 to 100.0 |
| 168 h window (2) | +8.0 to +13.6 | +1.8 to +20.5 | Not evaluable | 72.2 to 87.0 |

The base-run endpoint retention ranges from 17.2 to 100.0%; 25 otherwise observation-valid receptors fail the 95% retention criterion. This transport-only screening can favor circulation regimes that remain inside the supplied meteorological domain, so the selected hours are not a uniform representation of the full period. Across all sampled active endpoints, 1.75% lie below the lowest CarbonTracker layer center. Shifting endpoint heights by ±500 m changes the mean background at eligible receptors by up to 22.2 ppb. The oldest 24 h supplies 3.0 to 11.2% of each eligible footprint's integrated sensitivity, indicating how much sensitivity remains near the finite-window limit. An endpoint boundary accounts for incoming methane but does not correct biased regional transport. The outermost output-cell share reaches 0.132%; an edge diagnostic alone cannot prove that no external source influence was omitted.

Matched-operator synthetic recovery and deliberately perturbed recovery are compared in Figure 9 and Table 4. Across components, matched-operator local-interval coverage ranges from 89.5 to 98.0%, compared with 90.0 to 96.0% under the perturbed scenario. Shrinkage toward prior values and imperfect recovery must be considered when interpreting source-specific estimates. These experiments test the estimator under specified synthetic truths and errors; they are not independent validation of the real emission estimates.

**Table 4. Synthetic methane recovery.** Each scenario uses 200 noise realizations and the stated four-component synthetic truth. Bias and RMSE are in multiplier units. Coverage is the fraction of local approximate 95% intervals containing the synthetic truth; real-data credible intervals use MCMC instead.

| Scenario / component | Bias | RMSE | Coverage (%) |
| --- | --- | --- | --- |
| Matched / Anthropogenic ≤500 km | -0.17 | 0.46 | 97.5 |
| Matched / Anthropogenic >500 km | +0.17 | 0.30 | 95.0 |
| Matched / Wetlands | +0.02 | 0.42 | 98.0 |
| Matched / Non-crop fires | +0.28 | 0.39 | 89.5 |
| Perturbed / Anthropogenic ≤500 km | -0.14 | 0.51 | 96.0 |
| Perturbed / Anthropogenic >500 km | +0.19 | 0.34 | 91.0 |
| Perturbed / Wetlands | +0.08 | 0.53 | 94.0 |
| Perturbed / Non-crop fires | +0.25 | 0.39 | 90.0 |

![Synthetic inversion recovery and interval coverage.](outputs/hysplit/inversion/figures/figure_21_inversion_recovery.png)

**Figure 9.** Distribution of recovered multipliers under matched and perturbed response/background scenarios. Boxes show medians and interquartile ranges; whiskers extend to the most extreme values within 1.5 interquartile ranges, with farther points omitted from display only. Diamonds mark synthetic truth. The lower panel shows local-interval coverage, with 95% as a reference. The experiment uses the actual selected receptor geometry but simulated concentrations.

#### Conditional regional emission totals and spatial support

Applying the posterior multipliers to the fixed prior patterns gives the 28-day regional totals in Table 5. These totals inherit the prior's spatial allocation—including weakly sampled cells within each region—and should not be interpreted as independently measured Sumatra-wide or national totals. Only 18.9% of the distant region's anthropogenic prior mass lies in the cells containing 90% of aggregate surface sensitivity; extending its fitted multiplier to the full distant region is therefore a prior-pattern extrapolation. Sector-specific values are conditional reallocations under the shared anthropogenic multiplier, not separate sector retrievals. The adjustment map in Figure 10 deliberately displays only that transport-support mask, without inventing pixel-scale inversion detail.

**Table 5. Conditional methane emissions, 9 September–6 October 2019.** Values are Gg CH₄ over 28 days, not annualized rates. Posterior intervals propagate multiplier uncertainty only. The last column is the fraction of prior mass in cells containing 90% of aggregate surface sensitivity, not a fraction of independently retrieved emissions. The distant region is limited to the modeled domain; wetlands and non-crop fires share their respective multiplier across both regions.

| Region / component | Prior (Gg) | Posterior median (95%) (Gg) | Prior in support (%) |
| --- | --- | --- | --- |
| ≤500 km / anthropogenic | 143.9 | 83.8 (28.1–191.8) | 49.6 |
| ≤500 km / wetlands | 73.1 | 46.5 (14.9–113.8) | 42.5 |
| ≤500 km / noncrop fire | 165.6 | 126.3 (44.3–259.5) | 92.8 |
| >500 km / anthropogenic | 3,308.0 | 1,681.3 (600.3–3,629.0) | 18.9 |
| >500 km / wetlands | 862.6 | 549.1 (176.3–1,342.8) | 0.8 |
| >500 km / noncrop fire | 982.3 | 749.2 (262.6–1,539.1) | 17.9 |

Within 500 km, waste and fuel exploitation together account for 77.4% of the anthropogenic inventory total. Table 6 translates the common regional multiplier into sector allocations. Because the inversion does not estimate separate sector multipliers, their shares remain fixed to EDGAR: agreement or disagreement with BKT cannot identify which of these sectors is individually biased.

**Table 6. Conditional anthropogenic sector allocation within 500 km of BKT.** Emissions are Gg CH₄ over 9 September–6 October 2019. Parentheses contain 95% intervals propagated from the shared regional multiplier. Sector shares are inherited from the inventory, not measured or independently inferred. Rounded shares may not sum exactly to 100%.

| Sector ≤500 km | Prior (Gg) | Prior share (%) | Conditional posterior (Gg) |
| --- | --- | --- | --- |
| Waste | 61.84 | 43.0 | 36.01 (12.08–82.40) |
| Fuel exploitation | 49.60 | 34.5 | 28.88 (9.69–66.09) |
| Agriculture | 27.91 | 19.4 | 16.25 (5.45–37.19) |
| Buildings | 2.16 | 1.5 | 1.26 (0.42–2.88) |
| Transport | 1.27 | 0.9 | 0.74 (0.25–1.69) |
| Industrial processes | 0.51 | 0.4 | 0.29 (0.10–0.67) |
| Industrial combustion | 0.31 | 0.2 | 0.18 (0.06–0.42) |
| Power industry | 0.31 | 0.2 | 0.18 (0.06–0.41) |

![Regional emission adjustments and particle endpoints.](outputs/hysplit/inversion/figures/figure_22_inversion_geography.png)

**Figure 10.** Anthropogenic posterior-median multipliers in the two prescribed regions and five-day backward endpoint locations. Adjustment colors are masked outside cells containing 90% of aggregate footprint sensitivity; uncolored areas are weakly sampled, not zero-emission areas. The 500 km partition is geodesic. Endpoint colors indicate height in km above mean sea level; deterministic thinning is for display only and all retained endpoints enter background sampling. Boundaries use the established Indonesian GeoJSON and full-resolution geoBoundaries; the map is not a province- or facility-level retrieval.

### 4.2 The revised transport ensemble

The revised ensemble changes the operator in two ways. First, it restores the 25 receptor hours that the original domain had excluded, so the fit uses 52 hours instead of 27; the restored hours are mostly in October and carry lower methane. Second, it removes numerical noise: the seed standard deviation of the prior increment is 0.9 ppb for the near anthropogenic term and 6.8 ppb for the far term (medians over receptors), against seed-induced changes of up to 18% in the original single-seed anchors. The prior over-prediction is essentially unchanged at +76 ppb. Transport noise was not the reason the original inversion could not separate sources from background.

**Table 7. Posterior multipliers with the original working covariance: published fit and revised transport ensemble.** Medians with 95% credible intervals; the published fit used 27 receptor hours and 540 particles, the revised ensemble 52 hours and three seeds of 2,000 particles.

| Parameter | Published | Revised ensemble |
| --- | --- | --- |
| Anthropogenic ≤500 km | 0.58 (0.20–1.33) | 0.57 (0.19–1.25) |
| Anthropogenic >500 km | 0.51 (0.18–1.10) | 0.45 (0.17–0.97) |
| Wetlands | 0.64 (0.20–1.56) | 0.58 (0.19–1.31) |
| Non-crop fires | 0.76 (0.27–1.57) | 0.71 (0.26–1.42) |
| Background offset (ppb) | -3.80 (-32.87–24.60) | 0.02 (-27.44–26.24) |
| Background trend (ppb / 28 d) | -1.17 (-20.29–18.24) | -0.64 (-19.84–18.61) |

Refitting with the original 50% covariance moves the multipliers little (Table 7). The withheld RMSE of the inversion falls to 36.2 ppb, but so does every baseline, and the fitted background alone still predicts the 13 withheld hours better (28.5 ppb). More hours and less noise do not, by themselves, give the observations more say.

### 4.3 Error-model consistency and the tuned fit

The reason is the error model. With the 50% transport fraction the training reduced chi-square at the posterior mode is 0.26: the covariance is about four times too large in variance, the likelihood is correspondingly weak, and the posterior stays close to the prior. Figure 11 shows the scan; the reduced chi-square reaches one at a transport fraction of 0.10 under GFS.

![Error-model consistency and posterior intervals.](outputs/hysplit/revision/figures/figure_R05_inversion_update.png)

**Figure 11.** Training reduced chi-square against the transport-error fraction for the GFS and ERA5 ensembles (a), and posterior medians with 95% credible intervals for the published fit, the revised ensemble with the fixed covariance, the revised ensemble with the tuned covariance, the ERA5 ensemble with its tuned covariance, and the near-field split (b).

**Table 8. Posterior multipliers with the tuned covariance, revised GFS ensemble.** Transport-error fraction 0.10 (training reduced chi-square 1.0). Variance reduction is in the fitted parameter space relative to the prior.

| Parameter | Prior median | Posterior median (95%) | Variance reduction (%) | P(multiplier > 1) |
| --- | --- | --- | --- | --- |
| Anthropogenic ≤500 km | 1.0 | 0.37 (0.15–0.70) | 68.1 | 0.000 |
| Anthropogenic >500 km | 1.0 | 0.24 (0.10–0.45) | 69.4 | 0.000 |
| Wetlands | 1.0 | 0.43 (0.16–0.91) | 58.1 | 0.010 |
| Non-crop fires | 1.0 | 0.68 (0.39–1.00) | 87.9 | 0.025 |
| Background offset (ppb) | 0.0 | 4.54 (-15.13–23.34) | 76.0 | n/a |
| Background trend (ppb / 28 d) | 0.0 | -5.13 (-22.94–13.02) | 16.0 | n/a |

With the tuned covariance the posterior moves decisively away from the prior (Table 8). Anthropogenic emissions within 500 km scale to 0.37 (0.15–0.70), those beyond 500 km to 0.24 (0.10–0.45), wetlands to 0.43 (0.16–0.91) and non-crop fires to 0.68 (0.39–1.00). The anthropogenic and wetland intervals exclude the inventory value; the fire interval reaches it at 1.00. The withheld RMSE is 25.3 ppb against 28.5 ppb for the background-only baseline and 68.2 ppb for the inventory with a fitted background, and the withheld bias is +6.5 ppb. The tuned fit is the first configuration in this study in which source scaling adds predictive value over a fitted background on hours the fit never saw.

![Tuned fit and withheld evaluation.](outputs/hysplit/revision/figures/figure_R06_withheld_evaluation.png)

**Figure 12.** Observed methane and the tuned GFS posterior with its 95% model-mean interval at all 52 receptor hours, withheld hours marked (a), and withheld RMSE by model for the published fit, the revised GFS ensemble and the ERA5 ensemble (b).

**Table 9. Withheld-hour RMSE (ppb) by model, transport ensemble and driver.** Withheld hours were fixed before fitting. Baselines are refitted on each ensemble's fitting hours.

| Model | Published | Revised GFS | ERA5 |
| --- | --- | --- | --- |
| Raw inventory | 98.7 | 84.3 | 139.1 |
| Inventory with fitted background | 86.0 | 68.2 | 128.2 |
| Inversion, fixed 50% covariance | 47.6 | 36.2 | 60.3 |
| Inversion, tuned covariance | not fitted | 25.3 | 39.2 |
| Inversion, near-field split, tuned | not fitted | 25.4 | 41.9 |
| Background only | 40.0 | 28.5 | 26.6 |
| Withheld hours (n) | 6 | 13 | 12 |

### 4.4 The near field

Splitting the within-500 km term at 50 km gives 0.52 (0.18–1.18) for the cells within 50 km of the station and 0.41 (0.16–0.78) for the 50–500 km ring, with the far, wetland and fire terms essentially unchanged and the withheld RMSE 25.4 ppb. The within-50 km interval includes unity: the cells that dominate the near-region prior are the ones the observations constrain least, because a single receptor cannot distinguish a local source from a local transport error. The regional downward scaling rests on the 50–500 km ring and on the far term, not on the receptor cells.

### 4.5 Sensitivity to the meteorological driver

Under ERA5 meteorology the prior over-prediction grows to +104 ppb, because ERA5's shallower daytime boundary layer at BKT and its hourly winds put 1.16 to 1.86 times the GFS sensitivity at the surface (companion report), and 3 hours lose more than 5% of their particles on the smaller ERA5 domain. Its consistent transport fraction is 0.20, twice the GFS value. The tuned ERA5 multipliers, 0.32 (0.12–0.65), 0.29 (0.12–0.57), 0.40 (0.15–0.84) and 0.53 (0.24–0.90), overlap the GFS intervals almost entirely, so the conclusion that every prior is too high by a factor of two to four does not depend on the driver. The predictive result does: the tuned ERA5 fit has withheld RMSE 39.2 ppb against 26.6 ppb for background only and a withheld bias of +18.9 ppb.

**Table 10. Tuned posterior multipliers under the two drivers.** Medians with 95% credible intervals; each driver uses its own chi-square-consistent transport fraction.

| Parameter | GFS (fraction 0.10) | ERA5 (fraction 0.20) |
| --- | --- | --- |
| Anthropogenic ≤500 km | 0.37 (0.15–0.70) | 0.32 (0.12–0.65) |
| Anthropogenic >500 km | 0.24 (0.10–0.45) | 0.29 (0.12–0.57) |
| Wetlands | 0.43 (0.16–0.91) | 0.40 (0.15–0.84) |
| Non-crop fires | 0.68 (0.39–1.00) | 0.53 (0.24–0.90) |
| Background offset (ppb) | 4.54 (-15.13–23.34) | 5.78 (-15.33–26.42) |
| Background trend (ppb / 28 d) | -5.13 (-22.94–13.02) | -1.65 (-20.44–16.89) |

The two drivers therefore bracket what a single station can deliver. Their disagreement in surface sensitivity, a factor of 1.16 to 1.86 at matched receptors with seed noise below 2%, is the transport uncertainty that the covariance must represent, and it is larger than the interval width of either posterior.

### 4.6 Conditional regional totals

**Table 11. Conditional methane emissions, 9 September–6 October 2019, tuned GFS multipliers.** Gg CH₄ over 28 days; posterior intervals propagate multiplier uncertainty only and inherit the prior's spatial pattern. The last column is the share of prior mass in cells carrying 90% of aggregate sensitivity.

| Region | Component | Prior (Gg) | Posterior median (95%) (Gg) | Prior in support (%) |
| --- | --- | --- | --- | --- |
| ≤500 km | anthropogenic | 143.9 | 53.3 (21.9–101.2) | 37.5 |
| ≤500 km | wetlands | 73.1 | 31.6 (11.6–66.4) | 41.1 |
| ≤500 km | non-crop fire | 165.6 | 112.2 (64.4–165.7) | 92.5 |
| >500 km, in domain | anthropogenic | 8,334.5 | 1,989.8 (843.9–3,744.2) | 7.7 |
| >500 km, in domain | wetlands | 3,404.4 | 1,471.4 (540.1–3,094.6) | 0.2 |
| >500 km, in domain | non-crop fire | 1,040.7 | 705.0 (404.7–1,041.0) | 16.7 |

Applying the tuned GFS multipliers to the fixed prior patterns gives the 28-day totals in Table 11. They inherit the prior's spatial allocation within each region and the 50°–160° E domain of the far term; only 7.7% of the distant anthropogenic prior mass lies in cells that carry 90% of the aggregate sensitivity, so extending its multiplier to the whole distant region is a prior-pattern extrapolation. Sector shares within each region are inherited from EDGAR and are not separately retrieved.

## 5. Discussion

Three results carry the scientific weight. First, the prior model over-predicts methane at BKT by +76 ppb under GFS and +104 ppb under ERA5, with numerical noise below 1 ppb in the near term. Second, once the error model is made consistent with the residuals, the observations scale every component down by a factor of two to four with intervals that exclude the inventory value for the anthropogenic and wetland terms and reach it for fires, and this holds under both drivers. Third, only under GFS does the scaled model out-predict a fitted background on withheld hours.

The second result is a statement about the priors as placed and timed, not about national emissions. EDGAR allocates monthly totals with proxies; LPJ-EOSIM wetland methane in Sumatran peatlands during a strong dry season is a model estimate; GFED fire methane depends on burned area and emission factors. Any of these can be biased high at this receptor in this month without being biased in the national total, and the near-field split shows that the receptor cells themselves are not where the constraint comes from. The result is best read as an observational test that the priors fail in this region and season, with the size of the failure quantified under two transport drivers.

The third result identifies what limits the method. The chi-square scan shows the original covariance was not an estimate of transport error but a wide guard; replacing it with a consistent value is legitimate because the withheld evaluation remains independent, but it also makes the fit sensitive to the driver's own biases. ERA5's larger and differently placed sensitivity yields larger residuals at the same observations, a larger consistent covariance, and no predictive gain. The driver disagreement is the dominant transport uncertainty and it is not represented by either posterior interval.

Structural limits remain as stated for the original design: CarbonTracker-CH₄ assimilates BKT, so the boundary is not fully independent; convective redistribution is absent from both drivers; auxiliary natural fields are climatological; source-height errors and unresolved inland-water exchange can be absorbed by another component's multiplier. Methane is passive over five days. None of these is removed by more particles or more receptor hours.

## 6. Conclusions

The revised transport ensemble removes numerical noise and domain truncation as explanations for the original inversion's weakness and identifies the working error covariance as the cause. Under a covariance consistent with the residuals, four weeks of BKT methane scale the EDGAR, wetland-model and fire priors down by a factor of two to four in September–October 2019 under both GFS and ERA5 transport, and the GFS fit predicts withheld hours better than a fitted background. The scaling is conditional on the priors' spatial patterns, on parameterized transport without resolved convection, and on an assimilating boundary product; the driver disagreement in surface sensitivity is the largest remaining transport uncertainty. A second receptor, a boundary product that withholds BKT, and a transport driver with resolved convection are the additions most likely to turn this conditional scaling into a verified regional estimate.

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

<!-- pdf-pagebreak -->

## Appendix. Worked budget, recovery tests and definitions

### Worked methane inverse concentration budget

Table 12 uses the first transport-eligible withheld receptor, 16 September 2019 at 06:00 UTC. Each source term is its prior response multiplied by the posterior **mean** multiplier; the mean background offset and trend are added to endpoint methane and fixed natural exchange. Linearity in the multipliers makes their sum equal to the posterior mean concentration. It need not equal the posterior median plotted elsewhere, because the transformed posterior is asymmetric. No component is adjusted afterward to force agreement with the withheld observation.

**Table 12. Worked inverse methane budget at one withheld receptor.** Values are ppb. Positive source terms add methane; soil uptake enters the fixed auxiliary term with a negative sign. Posterior means are used for this additive identity; two-decimal display precision supports arithmetic inspection rather than implying a 0.01 ppb uncertainty. Rounding can produce a small difference between displayed subtotals and total.

| Budget term | CH₄ (ppb) |
| --- | --- |
| Endpoint background | 1,839.21 |
| Background offset and trend | -3.57 |
| Fixed termites + geology − soil | 1.49 |
| Anthropogenic ≤500 km | 9.79 |
| Anthropogenic >500 km | 8.70 |
| Wetlands | 9.04 |
| Non-crop fires | 2.52 |
| Posterior mean concentration | 1,867.19 |
| Observed concentration | 1,882.74 |
| Observed minus posterior mean | 15.55 |

### Synthetic recovery on the revised ensemble

**Table 13. Synthetic recovery on the revised ensemble.** 200 realizations per scenario; bias and RMSE in multiplier units; coverage of local 95% intervals.

| Scenario | Component | Bias | RMSE | Coverage (%) |
| --- | --- | --- | --- | --- |
| matched operator | Anthropogenic ≤500 km | -0.12 | 0.42 | 97.5 |
| matched operator | Anthropogenic >500 km | +0.16 | 0.30 | 92.5 |
| matched operator | Wetlands | +0.00 | 0.39 | 97.0 |
| matched operator | Non-crop fires | +0.21 | 0.31 | 91.0 |
| transport and background perturbed | Anthropogenic ≤500 km | -0.08 | 0.58 | 92.0 |
| transport and background perturbed | Anthropogenic >500 km | +0.16 | 0.32 | 92.0 |
| transport and background perturbed | Wetlands | +0.03 | 0.49 | 94.0 |
| transport and background perturbed | Non-crop fires | +0.25 | 0.36 | 87.5 |

The synthetic tests use the revised response matrix with the fixed 50% covariance, known multipliers of 1.5, 0.7, 1.2 and 0.6, and 200 correlated-noise realizations per scenario, as in the original design. They test recoverability under the assumed model and under coherent 30% source-response perturbations with an unmodeled 15 ppb boundary signal; they are not validation of the real estimates.

**Table 14. Terms used in this report.**

| Term | Meaning |
|---|---|
| Prior increment | Modeled methane enhancement from one source component with its multiplier at unity |
| Emission multiplier | Dimensionless factor applied to a fixed prior pattern; unity reproduces the inventory |
| Reduced chi-square | Mean squared whitened residual at the posterior mode; one indicates a covariance consistent with the residuals |
| Transport-error fraction | Share of each hour's prior increment treated as correlated transport error in the working covariance |
| Withheld hours | Receptor hours designated before fitting and never used by the optimizer |
| Credible interval | Equal-tailed posterior probability interval, conditional on the model and priors |
