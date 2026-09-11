<!-- SECTION: INVERSION_SUMMARY -->
The multi-week methane inversion uses {{I_N}} retained receptor hours from 9 September to 6 October 2019, with {{I_TRAIN}} hours for fitting and {{I_TEST}} withheld. It estimates four positive emission multipliers and two background adjustments, conditional on five-day GFS/HYSPLIT-STILT transport and NOAA CarbonTracker-CH₄ boundary fields. The anthropogenic multiplier within 500 km is {{I_NEAR}} and that beyond 500 km within the modeled domain is {{I_FAR}} (posterior medians and 95% credible intervals). Withheld prediction RMSE is {{I_RMSE}} ppb, compared with {{I_ADJ_RMSE}} ppb for a background-adjusted inventory baseline. {{I_SKILL_SENTENCE}} These are conditional inverse estimates, not independently verified regional emission totals.

<!-- SECTION: INVERSION_SCOPE -->
A complementary experiment asks whether the BKT methane time series can constrain broad emission adjustments after accounting for boundary methane and natural exchange. It spans 9 September–6 October 2019 inclusive, with receptors at 06:00 and 18:00 UTC (13:00 and 01:00 WIB). This fixed schedule samples contrasting mountain boundary-layer regimes without selecting hours for their agreement with a model. The inverse state is deliberately low-dimensional: anthropogenic emissions within and beyond 500 km of BKT, wetlands, non-crop fires, and a background offset and trend. Grid cells are assigned by their center's WGS 84 geodesic distance, so the regional partition retains the transport grid's finite spatial resolution. It does not retrieve separate emissions for each province, sector, facility or grid cell. The five-day inversion footprint uses a wider domain, approximately 76.3°–124.3° E and 18.2° S–17.8° N; quantities outside it are unrepresented rather than assumed absent.

<!-- SECTION: INVERSION_METHODS -->
### Multi-week methane observations and source priors

The inversion period contains {{I_VALID}} valid hourly methane measurements out of {{I_EXPECTED}} expected hours ({{I_VALID_PERCENT}}% coverage). Of {{I_SCHEDULED}} scheduled receptor hours, {{I_OBS_N}} have valid measurements and {{I_MISSING_RECEPTORS}} are unavailable; missing hours remain gaps. Every fourth calendar day was designated for withholding before fitting. The transport-retention screen described below excludes {{I_EXCLUDED}} observation-valid receptors ({{I_EXCLUDED_PERCENT}}%), leaving {{I_N}} receptor hours: {{I_TRAIN}} fitting and {{I_TEST}} withheld. Available flags are respected; observations are not removed because of large model residuals. Co-located NOAA flask samples on the CH₄ X2004A scale provide {{I_FLASK_N}} comparisons in the study period. Flask-minus-in-situ differences range from {{I_FLASK_MIN}} to {{I_FLASK_MAX}} ppb, with mean {{I_FLASK_MEAN}} ppb. These sparse comparisons support consistency at sampled times, but do not establish the complete hourly calibration or representativeness uncertainty.

EDGAR September and October 2019 monthly fluxes supply the anthropogenic prior. LPJ-EOSIM wetland methane driven by MERRA-2 supplies corresponding monthly natural emissions, using the GEOS-Chem distributed LPJ-MERRA2 product [10]. Daily GFED5.1 supplies fires [5]. The fixed auxiliary budget includes CAMS termite emissions (monthly 2000 climatological proxy), a scaled geological seep field, and MeMo soil uptake (1990–2009 monthly climatology); these are not contemporaneous 2019 measurements [11, 12]. The MeMo field is already distributed in kg CH₄ m⁻² s⁻¹; the original publication's supplementary-unit corrigendum is respected. All fields are conservatively area-averaged to the transport grid, with explicit sign and mass-to-molar conversion. Lakes, reservoirs and ocean exchange are not separately resolved; omitted or misplaced exchange remains structural uncertainty.

Agricultural burning is retained in EDGAR and removed from GFED methane to reduce double counting. Monthly GFED cropland carbon is converted using the provider's agricultural emission factors: {{I_FIRE_EF}} g CH₄ kg⁻¹ dry matter and {{I_C_EF}} g C kg⁻¹ dry matter. The resulting cell-specific crop fraction is applied to each day's total fire methane. This assumes crop burning shares the cell's total-fire daily profile; it is not a directly observed daily crop partition. A sensitivity fit retains the overlapping crop term to assess the effect of this choice. All emissions are represented as surface release; fire plume rise and elevated industrial injection are not independently specified.

### Five-day transport and endpoint boundary methane

Each base receptor releases particles backward for 120 h at 30 m above model ground. The requested 500 particles result in {{I_PARTICLES}} actual emitted particles under the model's release schedule; coefficients are normalized to the actual count. This lower count supports a multi-receptor design, with adequacy assessed at preselected 2,000-particle benchmarks rather than assumed from the higher-count single-hour case. Time-resolved, unsmoothed surface sensitivities are multiplied by the matched fluxes. The GFS driver retains 0.25° spacing, three-hourly fields and 55 hybrid levels. STILT mixing-depth settings follow the documented modified-Richardson-number configuration with a 250 m minimum. The GFS archive lacks the Grell convective mass-flux fields required by the selected convective redistribution option; deep-convective transport is therefore not independently resolved by that option. This is a material tropical transport limitation, not remedied by plotting at finer spacing.

NOAA CarbonTracker-CH₄ CT-CH₄-2025 supplies global three-dimensional background mole fractions at backward particle endpoints [9]. Its 3° longitude × 2° latitude fields contain 25 atmospheric layers at three-hour intervals. Equal particle-probability weights are used, not the accumulated footprint diagnostic mass. Endpoint heights above ground are converted to mean-sea-level heights using GFS terrain. Methane and layer-boundary heights are interpolated horizontally; methane is then interpolated vertically between layer centers, clamping values below the lowest center and reporting their frequency. The sampled background is the particle mean. The ±500 m endpoint-height tests assess vertical sampling sensitivity. Only runs retaining at least 95% of emitted particles at the endpoint are used; {{I_EXCLUDED}} receptor hours fail this transport criterion.

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

<!-- SECTION: INVERSION_RESULTS -->
### Methane observation coverage and prior concentration budget

The multi-week experiment retains {{I_N}} receptor hours, covering both daytime and nighttime conditions (Figure 13). The four flask comparisons differ from in-situ values by at most {{I_FLASK_ABSMAX}} ppb; their small number prevents extending this agreement to every hourly record. The anthropogenic prior and the mean transport sensitivity have distinct geographic structures (Figure 14): a high-emission cell matters to BKT only where transport provides sensitivity to it.

![Methane receptor selection and flask comparisons.]({{IFIG}}/figure_13_inversion_observations.png)

**Figure 13.** BKT hourly methane and the fixed twice-daily receptor selection, 9 September–6 October 2019. Filled circles enter fitting; open squares are withheld; crosses identify transport-ineligible receptor hours. Gaps remain unfilled. The lower panel shows NOAA flask-minus-in-situ methane at co-located sampled hours, in ppb. These comparisons assess sampled consistency, not a complete calibration uncertainty budget.

![Anthropogenic methane prior and mean transport sensitivity.]({{IFIG}}/figure_14_inversion_support.png)

**Figure 14.** Period-weighted EDGAR anthropogenic methane flux and mean five-day BKT sensitivity for transport-eligible receptor hours. Flux is in µmol m⁻² s⁻¹; sensitivity density is ppm per (µmol m⁻² s⁻¹) per km². Both color scales are logarithmic. The star marks BKT and the dashed circle marks the 500 km geodesic partition. Sensitivity display uses Gaussian smoothing with standard deviation one 0.25° cell and fourfold interpolation, conserving its integral; inversion coefficients remain unsmoothed. The lower color threshold omits {{I_DISPLAY_HIDDEN}}% of integrated display sensitivity, and {{I_DISPLAY_OUTSIDE}}% lies outside the map frame; these quantities are not additive because they overlap. Flux-color extensions denote values outside the displayed range; zero flux is transparent. Indonesia uses the established provincial GeoJSON and surrounding countries use full-resolution geoBoundaries.

The endpoint background ranges from {{I_BG_MIN}} to {{I_BG_MAX}} ppb across the retained hours. Median prior increments are {{I_K_NEAR}} ppb from anthropogenic emissions within 500 km, {{I_K_FAR}} ppb from farther anthropogenic emissions, {{I_K_WET}} ppb from wetlands and {{I_K_FIRE}} ppb from non-crop fires. These are prior-model contributions, not measured source fractions (Figure 15). Across all receptor hours, the unadjusted inventory-plus-background prediction has bias {{I_PRIOR_BIAS}} ppb and RMSE {{I_PRIOR_RMSE}} ppb. A mismatch can arise from source magnitude, source timing, transport or boundary error; its sign alone does not identify the responsible component.

![Background and prior source increments.]({{IFIG}}/figure_15_inversion_components.png)

**Figure 15.** Observed methane, particle-endpoint CarbonTracker background, and the unadjusted concentration budget at the selected BKT hours. The lower panel separates four positive prior source increments and the negative soil-uptake contribution. Fixed termite and geological terms are included in the upper budget but not the positive stack. Units are ppb. Monthly anthropogenic and wetland patterns, daily non-crop fire fluxes, and five-day GFS/HYSPLIT-STILT sensitivities determine these prior increments.

### Information content and posterior emission adjustments

The source-response matrix contains correlated spatial and temporal information (Figure 16). The sum of local prior-whitened information fractions is {{I_INFO}} across the six fitted parameters; it is not a count of resolved emission pixels. The strongest absolute off-diagonal source-response correlation is {{I_CORR}}. Distinguishing components requires differences in their transport-weighted time series, not merely different inventory labels.

![Source-response correlations and information modes.]({{IFIG}}/figure_16_inversion_information.png)

**Figure 16.** Pearson correlations among training-hour prior source responses and local prior-whitened information fractions for the six-parameter inverse state. If $s_j$ is a singular value of the whitened local Jacobian, the plotted fraction is $s_j^2/(1+s_j^2)$. The matrix describes response similarity without a significance test; the mode plot includes background parameters and does not establish spatial resolution.

**Table 7. Methane inverse parameters.** Emission multipliers are dimensionless; background offset is in ppb and trend in ppb per 28 days. Medians and 95% credible intervals come from the sampled posterior. The variance reduction is in the fitted parameter space (log space for emissions), relative to its stated prior; negative values indicate increased variance.

{{I_PARAMETER_TABLE}}

{{I_PARAMETER_INTERPRETATION}} The strongest posterior parameter correlation is {{I_POST_CORR}} between {{I_POST_CORR_PAIR}} (log multipliers for emissions, linear background terms). This quantifies dependence among fitted quantities rather than a causal relation between sources. The maximum chain diagnostic is {{I_RHAT}} and minimum effective sample size is {{I_ESS}}, satisfying the declared numerical sampling criteria. Successful sampling establishes computational convergence for this model, not the correctness of transport or emission attribution.

![Prior and posterior methane emission multipliers.]({{IFIG}}/figure_17_inversion_posterior.png)

**Figure 17.** Prior and posterior emission intervals for the four-component methane state. Emission multipliers use a logarithmic axis; unity is the inventory reference. Lower panels show fitted background adjustments. Dots are posterior medians and colored intervals are equal-tailed 95% credible intervals from MCMC. Their interpretation is conditional on the response matrix, fixed source patterns and working covariance.

### Withheld prediction and residual evidence

The posterior withheld RMSE is {{I_RMSE}} ppb, compared with {{I_RAW_TEST_RMSE}} ppb for raw inventories, {{I_BG_RMSE}} ppb for the fitted background-only model and {{I_ADJ_RMSE}} ppb for background-adjusted inventories (Table 8; Figure 18). {{I_SKILL_SENTENCE}} The nominal 95% marginal prediction envelope contains {{I_COVERAGE}}% of withheld concentrations. Its median withheld width is {{I_ENVELOPE_WIDTH}} ppb, compared with {{I_PARAMETER_WIDTH}} ppb for parameter-only intervals. Coverage must be considered alongside these widths and the small evaluation sample; a broad envelope can cover observations without precise emission information.

**Table 8. Methane concentration evaluation.** The split was specified before fitting; n is the number of receptor hours. Bias is predicted minus observed methane; MAE and RMSE are in ppb. Pearson r and R² are dimensionless; negative R² means squared errors exceed the squared departures of observations from their evaluation-sample mean. These are conditional concentration diagnostics, not errors against independently measured emissions.

{{I_EVALUATION_TABLE}}

![Methane predictions and withheld comparisons.]({{IFIG}}/figure_18_inversion_predictions.png)

**Figure 18.** Training-only posterior predictions for all retained BKT receptor hours, with 95% model-mean intervals and nominal 95% marginal mismatch-augmented envelopes. Open squares identify withheld observations. The lower panels compare withheld predicted and observed methane and RMSE against three baselines. The outer envelope does not condition correlated errors on training residuals and is not a fully conditional Gaussian forecast. CarbonTracker's assimilation of BKT limits strict independence.

Residuals span {{I_RES_MIN}} to {{I_RES_MAX}} ppb (observed minus posterior median). Their time evolution and relation to native GFS boundary-layer height and endpoint background are shown in Figure 19. Daytime residual RMSE is {{I_DAY_RMSE}} ppb and nighttime RMSE is {{I_NIGHT_RMSE}} ppb over the full retained sample; these descriptive regime diagnostics mix fitted and withheld hours. A residual association with boundary-layer height cannot by itself identify a mixing-depth bias, because emissions and meteorology co-vary.

![Posterior residual diagnostics.]({{IFIG}}/figure_19_inversion_residuals.png)

**Figure 19.** Methane residual time series, distributions by fit/withheld split, and relationships with native GFS planetary boundary-layer height and endpoint background, 9 September–6 October 2019. Residuals are observed minus the training-only posterior median, in ppb. The native GFS boundary-layer height is meteorological context rather than the STILT-computed mixing depth. The height scatter omits {{I_PBL_NEGATIVE}} nonphysical negative decoded heights whose magnitudes fall within their archive records' packing-precision scale; the corresponding concentrations remain in the inversion and other panels. No observations were removed on the basis of these residuals.

### Robustness and recoverability

Across the stated non-base assumption tests, posterior-mode anthropogenic multipliers range from {{I_NEAR_SENS}} within 500 km and {{I_FAR_SENS}} farther away (Figure 20). These scenario extrema have no assigned probability. In leave-one-week-out fits with a 24 h buffer, posterior RMSE ranges from {{I_WEEK_RANGE}} ppb and is lower than the background-adjusted inventory in {{I_WEEK_WINS}} of four held weeks, but lower than the background-only baseline in only {{I_WEEK_BG_WINS}} of four. The four weekly evaluation samples contain {{I_WEEK_COUNTS}} receptor hours, respectively. These highly unequal counts reflect transport screening; a week with one retained hour supplies only a single-error diagnostic, not evidence of general weekly skill. Buffered exclusions test temporal dependence but remain a single-site, single-season evaluation.

![Methane inversion sensitivity to assumptions.]({{IFIG}}/figure_20_inversion_sensitivity.png)

**Figure 20.** Anthropogenic emission adjustments under alternative background, covariance, prior, auxiliary-source, crop-overlap and daytime-sampling assumptions. Shading is the base-case sampled 95% credible interval; points are separately optimized modes in log-emission parameter space, transformed to multipliers. Both axes are logarithmic. Scenario spread is not a credible interval, and crossing the inventory reference indicates sensitivity to assumptions rather than a change in observed emissions.

**Table 9. Transport and boundary sensitivity at preselected anchors.** Changes are relative to the base run at the same receptor hour. Source-increment change includes the four optimized positive source components before fitting. Background differences are evaluated only where both runs retain at least 95% of particles; otherwise they are not evaluable. In low-retention runs, integrated source sensitivity is truncated by domain exits and is not a complete-duration convergence test. This table does not establish convergence for all receptor hours or all atmospheric regimes.

{{I_TRANSPORT_TABLE}}

The base-run endpoint retention ranges from {{I_RETENTION}}%; {{I_EXCLUDED}} otherwise observation-valid receptors fail the 95% retention criterion. This transport-only screening can favor circulation regimes that remain inside the supplied meteorological domain, so the selected hours are not a uniform representation of the full period. Across all sampled active endpoints, {{I_BELOW}}% lie below the lowest CarbonTracker layer center. Shifting endpoint heights by ±500 m changes the mean background at eligible receptors by up to {{I_HEIGHT_BG}} ppb. The oldest 24 h supplies {{I_OLDEST}}% of each eligible footprint's integrated sensitivity, indicating how much sensitivity remains near the finite-window limit. An endpoint boundary accounts for incoming methane but does not correct biased regional transport. The outermost output-cell share reaches {{I_EDGE_MAX}}%; an edge diagnostic alone cannot prove that no external source influence was omitted.

Matched-operator synthetic recovery and deliberately perturbed recovery are compared in Figure 21 and Table 10. {{I_RECOVERY_SENTENCE}} These experiments test the estimator under specified synthetic truths and errors; they are not independent validation of the real emission estimates.

**Table 10. Synthetic methane recovery.** Each scenario uses 200 noise realizations and the stated four-component synthetic truth. Bias and RMSE are in multiplier units. Coverage is the fraction of local approximate 95% intervals containing the synthetic truth; real-data credible intervals use MCMC instead.

{{I_RECOVERY_TABLE}}

![Synthetic inversion recovery and interval coverage.]({{IFIG}}/figure_21_inversion_recovery.png)

**Figure 21.** Distribution of recovered multipliers under matched and perturbed response/background scenarios. Boxes show medians and interquartile ranges; whiskers extend to the most extreme values within 1.5 interquartile ranges, with farther points omitted from display only. Diamonds mark synthetic truth. The lower panel shows local-interval coverage, with 95% as a reference. The experiment uses the actual selected receptor geometry but simulated concentrations.

### Conditional regional emission totals and spatial support

Applying the posterior multipliers to the fixed prior patterns gives the 28-day regional totals in Table 11. These totals inherit the prior's spatial allocation—including weakly sampled cells within each region—and should not be interpreted as independently measured Sumatra-wide or national totals. Only {{I_FAR_MASS_SUPPORT}}% of the distant region's anthropogenic prior mass lies in the cells containing 90% of aggregate surface sensitivity; extending its fitted multiplier to the full distant region is therefore a prior-pattern extrapolation. Sector-specific values are conditional reallocations under the shared anthropogenic multiplier, not separate sector retrievals. The adjustment map in Figure 22 deliberately displays only that transport-support mask, without inventing pixel-scale inversion detail.

**Table 11. Conditional methane emissions, 9 September–6 October 2019.** Values are Gg CH₄ over 28 days, not annualized rates. Posterior intervals propagate multiplier uncertainty only. The last column is the fraction of prior mass in cells containing 90% of aggregate surface sensitivity, not a fraction of independently retrieved emissions. The distant region is limited to the modeled domain; wetlands and non-crop fires share their respective multiplier across both regions.

{{I_BUDGET_TABLE}}

Within 500 km, {{I_LEADING_SECTORS}} together account for {{I_LEADING_SECTOR_SHARE}}% of the anthropogenic inventory total. Table 12 translates the common regional multiplier into sector allocations. Because the inversion does not estimate separate sector multipliers, their shares remain fixed to EDGAR: agreement or disagreement with BKT cannot identify which of these sectors is individually biased.

**Table 12. Conditional anthropogenic sector allocation within 500 km of BKT.** Emissions are Gg CH₄ over 9 September–6 October 2019. Parentheses contain 95% intervals propagated from the shared regional multiplier. Sector shares are inherited from the inventory, not measured or independently inferred. Rounded shares may not sum exactly to 100%.

{{I_SECTOR_TABLE}}

![Regional emission adjustments and particle endpoints.]({{IFIG}}/figure_22_inversion_geography.png)

**Figure 22.** Anthropogenic posterior-median multipliers in the two prescribed regions and five-day backward endpoint locations. Adjustment colors are masked outside cells containing 90% of aggregate footprint sensitivity; uncolored areas are weakly sampled, not zero-emission areas. The 500 km partition is geodesic. Endpoint colors indicate height in km above mean sea level; deterministic thinning is for display only and all retained endpoints enter background sampling. Boundaries use the established Indonesian GeoJSON and full-resolution geoBoundaries; the map is not a province- or facility-level retrieval.

<!-- SECTION: INVERSION_DISCUSSION -->
### What the methane inversion establishes—and what remains conditional

The methane experiment implements an observation-constrained inverse calculation rather than merely overlaying an inventory with a footprint. Its defensible inference is an update to a small set of regional source multipliers under explicit transport, background, natural-flux and error assumptions. {{I_DISCUSSION_RESULT}} An improvement over raw inventories is insufficient on its own: the background-adjusted baseline tests whether emission adjustment adds predictive value beyond changing the boundary level and trend.

The posterior uncertainty is narrower than the full scientific uncertainty problem. A single mountain receptor can observe different combinations of sources over time, but correlated response patterns, weak footprints and compensating background adjustments can leave individual categories poorly determined. Published wetland-model analyses identify rice–wetland separation as difficult in South Asia [10]; this single-station inversion does not independently verify that land-use partition. Fixed within-region patterns transfer any estimated scaling to cells and sectors that may receive little direct observational sensitivity. The maps and conditional totals therefore do not support regulatory responsibility, individual-source attribution or verified mitigation accounting.

Three structural limits deserve particular weight. First, CT-CH₄-2025 assimilates BKT, so this is a regional inversion conditional on an observation-informed global boundary, not an independent replication. Second, quarter-degree GFS cannot resolve all terrain-driven circulation or tropical convective exchange, and sparse transport sensitivity anchors cannot establish full operator accuracy. Third, wetland, soil, termite and geological fields have model or climatological dependence; unresolved inland-water exchange, spatial allocation and source-height errors can be absorbed into another component's multiplier. Methane is treated as passive over five days; neglected chemical loss is an additional approximation rather than evidence that methane has no atmospheric sink.

The strongest next tests are a boundary product excluding BKT (or a leave-BKT-out global analysis), independent wind and mixing-layer observations, additional receptor sites, and multi-season replication with alternative natural-flux and transport realizations. These would test whether regional adjustments persist when the principal sources of compensating error change. The present system is an experimental inversion workflow, not an operationally validated emissions service.

<!-- SECTION: INVERSION_CONCLUSION -->
The multi-week methane calculation produces a reproducible, positive-emission Bayesian inversion with explicit boundary conditions, natural exchange, held-out concentration checks, synthetic recovery and sensitivity analysis. {{I_SKILL_SENTENCE}} Its emission estimates are conditional regional adjustments, with uncertainty from the fitted posterior distinguished from structural sensitivity. Independent boundary and meteorological evidence, additional receptors and seasonal replication are needed before interpreting these results as verified regional emission totals.

<!-- SECTION: INVERSION_REFERENCES -->
9. NOAA Global Monitoring Laboratory (2025). *CarbonTracker-CH₄ CT-CH₄-2025*: three-dimensional methane mole fractions and assimilation documentation. [Dataset citation and access](https://gml.noaa.gov/ccgg/carbontracker-ch4/carbontracker-ch4-2025/citation.php); [technical documentation](https://gml.noaa.gov/ccgg/carbontracker-ch4/CTCH4_v2025_Website-Documentation.pdf). doi:10.25925/hxks-v755.
10. East, J. D., et al. (2024). Interpreting the Seasonality of Atmospheric Methane. *Geophysical Research Letters*, e2024GL108494. [doi:10.1029/2024GL108494](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2024GL108494). LPJ-MERRA2 wetland fields distributed by the [GEOS-Chem input-data archive](https://geos-chem.s3.amazonaws.com/HEMCO/CH4/v2025-09/LPJ_MERRA2/README).
11. Murguia-Flores, F., et al. (2018). Soil Methanotrophy Model (MeMo v1.0): a process-based model to quantify global uptake of atmospheric methane by soil. *Geoscientific Model Development*, 11, 2009–2032. [doi:10.5194/gmd-11-2009-2018](https://gmd.copernicus.org/articles/11/2009/2018/), with the [2019 supplementary-unit corrigendum](https://gmd.copernicus.org/articles/11/2009/2018/gmd-11-2009-2018-corrigendum.pdf).
12. GEOS-Chem methane input-data archive. Auxiliary methane fields: CAMS-GLOB-TERM v1.1, [MeMo climatology documentation](https://geos-chem.s3.amazonaws.com/HEMCO/CH4/v2019-10/MeMo_SoilAbs/README), and geological methane based on [Etiope et al. (2019), doi:10.5194/essd-11-1-2019](https://essd.copernicus.org/articles/11/1/2019/), scaled in the distributed product to the global constraint of [Hmiel et al. (2020), doi:10.1038/s41586-020-1991-8](https://www.nature.com/articles/s41586-020-1991-8). Product versions, native timestamps and climatological reuse are identified in the methods; these fields are not local observations.
13. Jeong, S., et al. (2013). A multitower measurement network estimate of California's methane emissions. *Journal of Geophysical Research: Atmospheres*, 118, 11339–11351. [doi:10.1002/jgrd.50854](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/jgrd.50854).

CarbonTracker CT-CH₄-2025 results are provided by NOAA GML, Boulder, Colorado, USA, through the CarbonTracker-CH₄ data service. Their use here does not imply NOAA endorsement or independent validation of the regional inversion.

{{I_BOUNDARY_ATTRIBUTION}}

<!-- SECTION: INVERSION_APPENDIX -->
### Worked methane inverse concentration budget

Table 16 uses the first transport-eligible withheld receptor, {{I_WORKED_DATE}}. Each source term is its prior response multiplied by the posterior **mean** multiplier; the mean background offset and trend are added to endpoint methane and fixed natural exchange. Linearity in the multipliers makes their sum equal to the posterior mean concentration. It need not equal the posterior median plotted elsewhere, because the transformed posterior is asymmetric. No component is adjusted afterward to force agreement with the withheld observation.

**Table 16. Worked inverse methane budget at one withheld receptor.** Values are ppb. Positive source terms add methane; soil uptake enters the fixed auxiliary term with a negative sign. Posterior means are used for this additive identity; two-decimal display precision supports arithmetic inspection rather than implying a 0.01 ppb uncertainty. Rounding can produce a small difference between displayed subtotals and total.

{{I_WORKED_INVERSE_TABLE}}
