# Greenhouse-gas source influence and methane emission inversion at Bukit Kototabang

## Scientific summary

Atmospheric transport connects the Bukit Kototabang (BKT) greenhouse-gas record to spatially distributed surface exchange across Sumatra and its surroundings. For the receptor record timestamped 26 September 2019 at 01:00 UTC (08:00 Western Indonesian Time, WIB), the observations are 437.09 ppm carbon dioxide (CO₂), 1,922.06 ppb methane (CH₄), and 531.15 ppb carbon monoxide (CO). These are measured mole fractions, not source-specific enhancements.

A three-member HYSPLIT-STILT ensemble driven by quarter-degree Global Forecast System (GFS) meteorology assigns 60.3% of its 72-hour surface-flux sensitivity to the southeast sector beyond 25 km from BKT and 21.4% to the area within 25 km. The sensitivity-weighted median source distance is 278 km and median backward age is 32 h. Relative to a matched one-degree Global Data Assimilation System (GDAS) ensemble, integrated sensitivity changes by -27.0%, and the normalized regional spatial distributions differ by 43.9% total variation on a common one-degree grid. These are meteorological-driver sensitivities, not estimates of predictive accuracy.

Convolution with September 2019 anthropogenic fluxes from the Emissions Database for Global Atmospheric Research (EDGAR v8.0) gives surface-release-equivalent enhancements of 1.045 ppm CO₂ and 48.464 ppb CH₄ under GFS transport. The largest modeled sector contributions are transport for CO₂ and agriculture for CH₄. Separately, daily Global Fire Emissions Database (GFED5.1) fluxes give 2.595 ppm CO₂, 42.861 ppb CH₄ and 508.887 ppb CO in a surface-release fire scenario. These estimates are inventory-conditioned model results, not measured contributions or emission inversions.

The GDAS fire-only CO estimate (1,023.2 ppb) exceeds the observed total, whereas GFS fire CO consumes 95.8% of that total. This budget constraint exposes strong scenario dependence; it does not validate the GFS fire estimate.

The multi-week methane inversion uses 27 retained receptor hours from 9 September to 6 October 2019, with 21 hours for fitting and 6 withheld. It estimates four positive emission multipliers and two background adjustments, conditional on five-day GFS/HYSPLIT-STILT transport and NOAA CarbonTracker-CH₄ boundary fields. The anthropogenic multiplier within 500 km is 0.58 (0.20–1.33) and that beyond 500 km within the modeled domain is 0.51 (0.18–1.10) (posterior medians and 95% credible intervals). Withheld prediction RMSE is 47.6 ppb, compared with 86.0 ppb for a background-adjusted inventory baseline. Emission fitting improves the withheld point-prediction RMSE relative to the adjusted-inventory baseline, but this finite conditional comparison does not establish independently validated emissions. The simpler fitted background-only model performs better (40.0 ppb RMSE); source fitting therefore does not demonstrate incremental predictive value over that baseline. These are conditional inverse estimates, not independently verified regional emission totals.

A follow-up screen of finer-grid BARRA-R2 meteorology found missing pressure-level fields above the supplied model surface. Conversion was stopped before unvalidated gap filling; no BARRA transport comparison or revised inversion is claimed. The BARRA appendix documents the bounded audit and requirements for resuming it.

A gas-independent transport benchmark identifies incomplete particle retention in 25 of 52 original five-day runs. The severe-case expanded-domain test raises retention from 17.2% to 100.0%. Mixing and receptor tests expose configuration sensitivity; an observation-based profile check does not independently validate any replacement. The transport appendix separates these findings from atmospheric accuracy and leaves the inversion unchanged. The full-ensemble correction increases the 95% particle-retention pass count from 27 to 52 of 52 receptor hours. On the matched retained hours, the mean net prior surface-methane term changes by -5.38 ppb; recovered hours have mean observed CH₄ -28.36 ppb relative to retained hours. A pre-declared five-case matrix shows that surface, endpoint-background and combined duration responses must be assessed separately; no prospective tolerance supports a binary convergence claim, and the inversion remains unchanged.

The principal implication is that source interpretation at BKT must account jointly for transport, source distribution and emission timing. Meteorological representation, unresolved mountain circulation, vertical release assumptions, ecosystem exchange and background concentrations remain material uncertainties. The analysis does not establish a complete concentration budget, responsibility of an individual facility, or operational model skill.

## 1. Scientific question and scope

This study asks which surface regions and source categories could contribute to a selected BKT observation, how that inference depends on the meteorological driver, and which uncertainties prevent stronger attribution. The approach combines a backward particle-transport calculation with independently compiled emission inventories. A footprint is a sensitivity of receptor mole fraction to surface flux; an emission inventory estimates the flux itself. Their product estimates a contribution conditional on both datasets and the model assumptions [1, 2].

BKT is a mountain receptor at 0.202° S, 100.318° E, with station elevation 864.5 m above mean sea level. The inlet is represented at 30 m above local model ground. This distinction matters because model terrain is a spatial average, while an inlet samples a particular site. A separate 60 m release scenario tests height dependence; it does not represent a second observed inlet.

The case is an exploratory, single-hour source-influence study, selected from the available simultaneous gas observations. It is not a randomly sampled evaluation period or a regional climatology. The integration covers 23 September 01:00 to 26 September 01:00 UTC, with hourly source intervals. Sources older than this window and air entering from outside it are not represented by the footprint. Conclusions therefore apply to this receptor hour and experimental design.

The forward case's quantitative source influence is restricted to an output domain spanning approximately 85.27°–115.37° E and 10.25° S–9.85° N. Transport uses the larger meteorological domain, but source sensitivities outside the output domain are not retained. Its enhancements and spatial percentages refer to this bounded regional domain; external contributions are unrepresented, not assumed to be zero.

A complementary experiment asks whether the BKT methane time series can constrain broad emission adjustments after accounting for boundary methane and natural exchange. It spans 9 September–6 October 2019 inclusive, with receptors at 06:00 and 18:00 UTC (13:00 and 01:00 WIB). This fixed schedule samples contrasting mountain boundary-layer regimes without selecting hours for their agreement with a model. The inverse state is deliberately low-dimensional: anthropogenic emissions within and beyond 500 km of BKT, wetlands, non-crop fires, and a background offset and trend. Grid cells are assigned by their center's WGS 84 geodesic distance, so the regional partition retains the transport grid's finite spatial resolution. It does not retrieve separate emissions for each province, sector, facility or grid cell. The five-day inversion footprint uses a wider domain, approximately 76.3°–124.3° E and 18.2° S–17.8° N; quantities outside it are unrepresented rather than assumed absent.

## 2. Evidence and data quality

### Meteorological representation

The GFS archive contains quarter-degree meteorological fields at three-hour intervals on 55 hybrid sigma-pressure levels. It concatenates analysis-time and three-hour forecast fields from successive six-hour model cycles; it is a pseudo-analysis rather than a homogeneous retrospective reanalysis [3]. The regional domain extends from 75° to 130° E and 20° S to 20° N, retaining the native horizontal spacing and all available levels. The comparison uses the GDAS one-degree, three-hourly archive with otherwise matched receptor and transport settings.

At the nearest native grid points, GFS terrain is 816 m and GDAS terrain is 407 m. GFS therefore represents the station elevation more closely at those points. This comparison does not quantify the terrain interpolation seen by every particle or prove that the finer driver captures local slope and valley winds. Figure 1 places the difference in the context of near-surface winds and native meteorological boundary-layer height.

![Meteorological context near BKT.](outputs/hysplit/gfs/analysis/figures/figure_01_meteorology.png)

**Figure 1.** Three-hourly GFS and GDAS meteorological output at the nearest native grid points to BKT over the transport period and its interpolation brackets in September 2019. Panels show native planetary boundary-layer height (m), eastward wind and northward wind (m s⁻¹). Positive wind components point east and north. The native boundary-layer field is diagnostic context: the STILT configuration used here estimates mixing depth from a modified Richardson number rather than directly prescribing this plotted height.

### Receptor measurements

Observations are expressed as dry-air mole fractions: parts per million (ppm) for CO₂ and parts per billion (ppb) for CH₄ and CO. Processing uses UTC consistently; WIB is UTC+7. The selected record passes the available species-specific quality screens. Each gas has 335 valid hours out of 337 expected hours in the symmetric seven-day context on either side of the receptor hour. Missing or flagged measurements are excluded from descriptive statistics and remain visible as gaps.

![BKT gas observations around the receptor hour.](outputs/hysplit/gfs/analysis/figures/figure_02_observation_context.png)

**Figure 2.** Hourly BKT CO₂, CH₄ and CO over the seven days before and after 26 September 2019 01:00 UTC. Orange points identify the receptor values, shading marks the backward integration window, and dashed lines show context medians. No interpolation fills measurement gaps. Units are ppm for CO₂ and ppb for CH₄ and CO.

**Table 1. Receptor observations and temporal context.** Context medians and percentile ranks describe the surrounding valid-hour sample. They are not estimates of background concentration, measurement uncertainty or source contribution.

| Gas | Receptor value | Context median | Percentile rank |
| --- | --- | --- | --- |
| CO₂ | 437.09 ppm | 419.60 ppm | 84.0% |
| CH₄ | 1,922.06 ppb | 1,903.62 ppb | 72.4% |
| CO | 531.15 ppb | 429.52 ppb | 69.4% |

The available quality flags are screening evidence, not a substitute for a traceable calibration uncertainty budget. The exact relationship between the timestamp and the instrument's averaging interval has not been independently established; this creates temporal representativeness uncertainty when matching the modeled one-hour release window to the observation.

### Emission inventories and geographic context

EDGAR v8.0 supplies monthly, 0.1° anthropogenic CO₂ and CH₄ flux densities. The September 2019 fields are used without fitting their magnitudes to the BKT measurements. Eight broad sector groups are retained for each gas: agriculture, buildings, fuel exploitation, industrial combustion, industrial processes, power industry, transport and waste. Monthly profiles cannot reproduce the specific operating schedules, day-to-day variability or hourly activity of individual sources [4].

The EDGAR CO₂ component used here represents fossil and industrial sources, including relevant agricultural process emissions; its separately reported short-cycle biogenic CO₂ component is not included. Thus, the anthropogenic CO₂ estimate in this report is not an exhaustive estimate of all human-associated combustion, especially biofuel use. EDGAR and GFED are historical inventory estimates, not direct measurements of the receptor's contributing fluxes.

GFED5.1 supplies daily 0.25° landscape-fire emissions. The calculation uses the relevant September 2019 days and the reported mass of each gas per cell per day, converted to flux density. Daily mass is distributed uniformly over the corresponding UTC calendar day; no unverified hourly fire profile is imposed. The data's daily date labels are used to identify the emission day. Fire emissions depend on estimated burned area, fuel consumption and emission factors, with uncertainty distinct from transport uncertainty [5].

**Table 2. Evidence coverage and interpretation.** A finer source grid does not independently improve the meteorological information content.

| Evidence | Spatial / temporal support | Use | Principal limitation |
|---|---|---|---|
| BKT gas observations | Point inlet; hourly | Receptor and temporal context | Calibration uncertainty and exact averaging-window alignment |
| GFS meteorology | 0.25°; three-hourly; 55 atmospheric levels | Principal transport driver | Terrain and convection remain parameterized |
| GDAS meteorology | 1°; three-hourly | Matched transport comparison | Coarse terrain and circulation |
| EDGAR v8.0 | 0.1°; September 2019 mean | Anthropogenic sector scenarios | Monthly timing and vertical release approximation |
| GFED5.1 | 0.25°; daily | Landscape-fire scenarios | Emission factors, daily timing and plume injection |
| Indonesian provincial boundaries | Detailed polygon geometry | Fractional provincial summaries | Boundary vintage is not a verified 2019 reconstruction |
| geoBoundaries gbOpen | Full-resolution country polygons | Neighboring-country context | Mixed source dates and country-specific licensing |

Indonesian maps and provincial calculations use the established 38-province geometry in WGS 84. Neighboring countries use the full-resolution geoBoundaries gbOpen product, with country-specific source and license attribution [6]. Boundaries are geographic context, not atmospheric barriers. Present-day administrative subdivisions should not be interpreted as a verified historical boundary reconstruction. Missing source coverage is not silently replaced with zero emissions.

## 3. Methods

### Backward transport and surface sensitivity

The Hybrid Single-Particle Lagrangian Integrated Trajectory model (HYSPLIT 5.4.2) is configured for Stochastic Time-Inverted Lagrangian Transport (STILT). Particles are released backward over the hour immediately preceding the receptor timestamp. The principal estimate is the arithmetic mean of three distinct seeded runs, each with 10,020 emitted particles. A common 0.1° accumulation grid samples particle residence; it is not a claim of 0.1° meteorological resolution.

The configuration uses mass-consistent dispersion, Hanna turbulence and a variable Lagrangian timescale. Mixing depth is diagnosed using the modified Richardson-number method, with a minimum of 250 m. Surface sensitivity is accumulated from residence in the lower half of the mixed layer. Thus, near-surface sensitivity depends on modeled stability and the minimum-depth assumption as well as horizontal wind. Default vertical interpolation appropriate to the supplied global meteorology is used. The available archive lacks the Grell convective-flux fields required for that optional redistribution scheme; explicit Grell convective redistribution is not established for these runs [1, 7].

The transport operator treats all three gases as passive tracers over the integration window. No chemical production, loss or deposition is simulated. Gas-specific differences arise from the flux inventory and molar conversion, not separate atmospheric chemistry calculations; this assumption also limits interpretation of the CO scenario.

All coefficients are normalized to the number of particles actually emitted. A seed range measures finite-particle variability conditional on a given meteorology and parameter set. It is neither a confidence interval for the atmosphere nor an estimate of inventory error. The two meteorological ensembles share receptor time, release window, height, particle count, accumulation grid and dispersion settings. Changing the driver also changes the meteorological model and vertical representation; the comparison does not isolate horizontal grid spacing alone.

### Flux convolution and dimensional consistency

For gas-specific surface fluxes, the modeled enhancement is

$$
\Delta c_g(t_r)=\sum_m\sum_i\sum_j f_{ijm}(t_r)\,E_{g,ijm}.
$$

Here $t_r$ is receptor time; $i,j$ identify spatial cells; $m$ identifies the hourly source interval; $f$ is the emitted-particle-normalized footprint in ppm per (µmol m⁻² s⁻¹); and $E_g$ is the flux density of gas $g$, in µmol m⁻² s⁻¹. The result is ppm; CH₄ and CO are multiplied by 1,000 for presentation in ppb. Each coefficient already includes source-cell and source-interval sensitivity. No additional cell-area or hour-length multiplier is applied to this discrete sum.

For EDGAR flux density $q_g$ in kg m⁻² s⁻¹,

$$
E_g=q_g\frac{10^9}{M_g},
$$

where $M_g$ is molecular mass in g mol⁻¹. For GFED daily cell mass $Q_g$ in g day⁻¹ and cell area $A$ in m²,

$$
E_g=\frac{Q_g}{A\,86400}\frac{10^6}{M_g}.
$$

Cell areas use spherical latitude strips, and source fields are conservatively area-averaged onto the footprint grid. This respects the offset between inventory and receptor-centered grid cells. It assumes uniform flux within each source cell and does not reconstruct sub-grid sources. Calculating the convolution after remapping flux and, independently, after remapping the integrated sensitivity provides an algebraic consistency check.

The surface-flux operator does not represent stack rise or elevated aircraft and fire injection explicitly. Sector results are therefore termed *surface-release-equivalent enhancements*. They can identify source classes deserving further analysis, but do not establish the actual impact of a power station, flight corridor or fire plume at the inlet.

### Spatial summaries, display and uncertainty tests

Distances and bearings are calculated for grid-cell centers by great-circle geometry, rather than from individual source locations within each cell. The southeast sector spans bearings 112.5°–157.5°; directional comparisons exclude the area within 25 km, where grid placement strongly affects bearing. Provincial contributions use fractional grid-cell overlap with polygons in an equal-area projection, not assignment of every coastal cell to its center's province. Areas claimed by multiple provincial polygons are excluded from every province's allocation and retained as unassigned influence. These summaries allocate modeled influence geographically; they do not estimate provincial emissions from the observations.

All analysis uses unsmoothed coefficients. Maps show continuous, linearly reconstructed surfaces, with sensitivity divided by cell area where a density is displayed. The footprint's Gaussian display width is selected by leaving one seed out and testing the other two against its unsmoothed field. The selected width is 0 native cells. Linear interpolation is performed before logarithmic color mapping, preserves nonnegativity, and is renormalized to preserve the full-domain sensitivity integral. It changes display representation, not meteorological resolution or the inventory convolution.

For the principal footprint map, 0.099% of the display integral is below the plotted color range and 1.093% is outside the frame. Unthresholded coefficients remain the basis of every table. Continuous contours do not imply precisely known footprint edges. The numerical checks assess conservation, time coverage, unit conversions and seed variability; they are not independent atmospheric validation.

The GFS ensemble retains 0.026% of its regional sensitivity in the outermost output-grid cells, at the eastern boundary. The footprint therefore has a truncated eastern tail. This edge share is not an upper bound on sensitivity or emissions beyond the domain. A wider-domain experiment is necessary before claiming complete regional source capture; the present convolution remains a contribution estimate for the stated bounded domain.

The selected regional inventory arrays contain no missing cells. Uncolored inventory areas indicate zero or values below the displayed positive range, not missing data; low values remain in the convolution. Logarithmic scales reveal spatial variation across orders of magnitude and are not used to transform the flux values themselves.

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

## 4. Results

### Regional footprint and dependence on meteorology

The GFS ensemble has integrated sensitivity 8.293 ppm per (µmol m⁻² s⁻¹). Its median influence distance is 278 km, and 47.7% of sensitivity lies within 250 km. The southeast share beyond 25 km is 60.3%, with a three-seed range of 60.1–60.6%. Near-receptor sensitivity remains important: 21.4% lies within 25 km, where unresolved site circulation is particularly relevant.

**Table 3. Transport diagnostics for matched ensembles.** Integrated sensitivity is in ppm per (µmol m⁻² s⁻¹). Distance and age are sensitivity-weighted, not particle-count medians. Percentages refer to the full modeled footprint.

| Diagnostic | GDAS ensemble | GFS ensemble |
| --- | --- | --- |
| Integrated sensitivity | 11.364 | 8.293 |
| Within 25 km (%) | 19.4 | 21.4 |
| Within 100 km (%) | 31.0 | 31.4 |
| Within 250 km (%) | 57.1 | 47.7 |
| Southeast beyond 25 km (%) | 69.4 | 60.3 |
| Median distance (km) | 229 | 278 |
| 90th-percentile distance (km) | 456 | 935 |
| Median age (h) | 32 | 32 |
| 90th-percentile age (h) | 60 | 61 |

![GFS ensemble footprint at BKT.](outputs/hysplit/gfs/analysis/figures/figure_03_footprint.png)

**Figure 3.** Ensemble-mean 72-hour GFS-driven BKT surface-flux footprint ending on 26 September 2019 at 01:00 UTC. Colors show time-integrated sensitivity density in ppm per (µmol m⁻² s⁻¹) per km² on a logarithmic scale. The star marks the 30 m AGL receptor. The continuous display uses linear interpolation and the stated cross-seed-selected kernel; numerical summaries and flux convolution use the unsmoothed field. Ocean sensitivity is retained because atmospheric transport is not confined to land.

The GDAS ensemble gives 11.364 integrated sensitivity, compared with 8.293 under GFS. The 43.9% regional total-variation difference describes redistribution after normalizing each field to unit sum on a common one-degree grid. It separates a change in geographic pattern from the -27.0% change in overall sensitivity. Neither metric identifies which driver is closer to the true atmospheric transport.

![Matched meteorological-driver comparison.](outputs/hysplit/gfs/analysis/figures/figure_04_driver_maps.png)

**Figure 4.** GDAS- and GFS-driven ensemble footprints for the same BKT receptor and 72-hour window. Both panels show sensitivity density with identical geographic extent and logarithmic color limits, and linear display reconstruction without an additional Gaussian kernel. Meteorological model, native grid and vertical representation differ; all receptor and particle settings are matched.

The mapped contrast is spatial as well as numerical. GDAS concentrates its strongest regional sensitivity over southern Sumatra, while GFS produces more extended eastward and northeastward branches over surrounding seas in addition to its Sumatran influence. The larger GFS sensitivity-weighted distance in Table 3 is consistent with that pattern. A weak but extensive branch can increase the distance distribution without supplying a correspondingly large anthropogenic contribution, because the flux field is highly nonuniform.

### Transport age and robustness

Half the GFS sensitivity accumulates within 32 h backward and 90% within 61 h. The earliest and latest source intervals contribute unequally. Consequently, an emission inventory averaged over the entire window can yield a different enhancement from a temporally resolved inventory even when its total emissions are similar.

![Transport distance and age.](outputs/hysplit/gfs/analysis/figures/figure_05_lag_distance.png)

**Figure 5.** Cumulative shares of unsmoothed ensemble sensitivity by backward lag (h) and great-circle distance (km) for GFS and GDAS. The horizontal reference marks 50%. Curves refer to the finite 72-hour experiment; the distance panel displays the first 1,000 km, not necessarily the whole support.

The GFS 60 m release changes integrated sensitivity by -2.0% relative to the 30 m run with the same seed. The three 30 m seeds span 8.278–8.319 in integrated sensitivity. This comparison separates a release-height scenario from stochastic sampling. It does not cover uncertainty in mixing-depth parameterization, meteorological winds or measurement representativeness.

![Seed and release-height sensitivity.](outputs/hysplit/gfs/analysis/figures/figure_06_robustness.png)

**Figure 6.** Integrated sensitivity and southeast sensitivity beyond 25 km for the two meteorological drivers. Blue points show three seeds at 30 m AGL; orange diamonds show the paired 60 m scenario. All runs use the same emitted-particle normalization. The spread is an experimental range, not a confidence interval.

### Anthropogenic source sectors

Under the EDGAR/GFS surface-release assumptions, the modeled CO₂ enhancement is 1.045 ppm and CH₄ enhancement is 48.464 ppb. Sector ordering is gas-specific: transport supplies the largest CO₂ contribution, while agriculture supplies the largest CH₄ contribution. A large source outside sensitive transport regions can contribute less than a smaller source close to, or strongly connected with, the receptor.

The leading sectors account for 66.7% of the modeled anthropogenic CO₂ contribution and 59.3% of CH₄, respectively. These shares describe this receptor's inventory-weighted mixture, not the composition of Indonesian national emissions. In particular, a broad transport-sector aggregate does not identify a specific road, vessel or aircraft source.

Using the same flux inventory with GDAS instead gives 2.703 ppm CO₂ and 73.525 ppb CH₄. The GFS values differ by -61.4% and -34.1%, respectively. These gas-specific changes reflect both overall sensitivity and its relocation relative to the source fields. Within GFS, raising the receptor from 30 to 60 m changes the paired-seed anthropogenic CO₂ and CH₄ contributions by -1.8% and -2.6%. Driver and height dependence therefore need evaluation at the source-contribution level, not only through total footprint sensitivity.

**Table 4. GFS-driven anthropogenic sector contributions.** Values are three-seed means; ranges describe numerical seed variability only. Each gas uses its own unit. Sector estimates assume surface release and September-mean activity.

| Gas / unit | Sector | Mean | Seed range |
| --- | --- | --- | --- |
| CO₂ (ppm) | Transport | 0.6965 | 0.6942–0.6987 |
| CO₂ (ppm) | Buildings | 0.1049 | 0.1045–0.1052 |
| CO₂ (ppm) | Industrial combustion | 0.0651 | 0.0641–0.0656 |
| CO₂ (ppm) | Industrial processes | 0.0558 | 0.0545–0.0566 |
| CO₂ (ppm) | Power industry | 0.0453 | 0.0423–0.0472 |
| CO₂ (ppm) | Agriculture | 0.0385 | 0.0384–0.0385 |
| CO₂ (ppm) | Fuel exploitation | 0.0384 | 0.0373–0.0390 |
| CO₂ (ppm) | Waste | 0.0001 | 0.0001–0.0001 |
| CH₄ (ppb) | Agriculture | 28.7582 | 28.5781–28.8643 |
| CH₄ (ppb) | Fuel exploitation | 12.7264 | 12.1049–13.9137 |
| CH₄ (ppb) | Waste | 4.5057 | 4.4844–4.5337 |
| CH₄ (ppb) | Buildings | 2.0598 | 2.0520–2.0651 |
| CH₄ (ppb) | Transport | 0.3862 | 0.3847–0.3876 |
| CH₄ (ppb) | Industrial combustion | 0.0207 | 0.0205–0.0208 |
| CH₄ (ppb) | Power industry | 0.0040 | 0.0039–0.0040 |
| CH₄ (ppb) | Industrial processes | 0.0032 | 0.0031–0.0032 |

![Anthropogenic sector contributions.](outputs/hysplit/gfs/analysis/figures/figure_07_sectors.png)

**Figure 7.** EDGAR v8.0 sector-weighted enhancements at BKT for the receptor hour, using September 2019 monthly fluxes and three GFS footprints. Bars show means and whiskers show minimum–maximum seed values. Scales differ between CO₂ (ppm) and CH₄ (ppb). These are conditional model contributions, not emissions inferred from the observations.

![Regional anthropogenic inventories.](outputs/hysplit/gfs/analysis/figures/figure_08_inventory.png)

**Figure 8.** September 2019 EDGAR anthropogenic CO₂ and CH₄ flux densities around Sumatra, conservatively matched to the analysis grid and summed across the eight sector groups. Units are µmol m⁻² s⁻¹, with gas-specific logarithmic scales. Spatial gradients reflect inventory allocation, not local measurements.

![Anthropogenic source-weighted influence.](outputs/hysplit/gfs/analysis/figures/figure_09_source_influence.png)

**Figure 9.** Geographic distribution of EDGAR-weighted GFS contributions to the selected BKT hour. Displayed contribution densities are ppm CO₂ km⁻² and ppb CH₄ km⁻². The maps combine flux magnitude with transport sensitivity; they are distinct from both the inventory maps and the transport-only footprint. Linear display reconstruction is not used for quantitative aggregation.

### Provincial source geography

The largest modeled Indonesian provincial contribution is Sumatera Barat for anthropogenic CO₂ and Sumatera Barat for anthropogenic CH₄. Table 5 summarizes the largest contributors within each gas. Provincial ranking describes the overlap of inventory flux and transport sensitivity. It is not a ranking of provincial total emissions, mitigation performance, or legally attributable responsibility.

Overlapping boundary claims account for 0.002% of the full-domain anthropogenic CO₂ contribution and 0.016% of CH₄. These portions are left unassigned, independently of offshore and foreign contributions. The map retains the supplied geometry; quantitative totals do not count overlapping areas twice.

**Table 5. Largest Indonesian provincial anthropogenic contributions.** Five leading provinces are reported for each gas. Values use fractional boundary overlap; offshore, foreign and multiply claimed areas are not reassigned to a province.

| Gas / unit | Province | Contribution |
| --- | --- | --- |
| CO₂ (ppm) | Sumatera Barat | 0.5992 |
| CO₂ (ppm) | Sumatera Selatan | 0.2107 |
| CO₂ (ppm) | Jambi | 0.1683 |
| CO₂ (ppm) | Riau | 0.0312 |
| CO₂ (ppm) | Kepulauan Bangka Belitung | 0.0134 |
| CH₄ (ppb) | Sumatera Barat | 27.4392 |
| CH₄ (ppb) | Sumatera Selatan | 10.0877 |
| CH₄ (ppb) | Jambi | 9.7102 |
| CH₄ (ppb) | Riau | 0.9127 |
| CH₄ (ppb) | Kepulauan Bangka Belitung | 0.0775 |

![Provincial source contributions.](outputs/hysplit/gfs/analysis/figures/figure_10_provinces.png)

**Figure 10.** Eight largest Indonesian provincial EDGAR-weighted contributions under the GFS ensemble for the selected receptor hour. Current detailed provincial geometry supplies geographic context. Fractional overlap is calculated in equal-area coordinates; scales differ for CO₂ and CH₄.

### Landscape-fire influence and emission timing

The GFED/GFS surface-release scenario produces 2.595 ppm CO₂, 42.861 ppb CH₄ and 508.887 ppb CO. These are modeled fire contributions over the source window, conditional on the daily inventory and transport. The CO observation provides useful combustion context, but co-elevation of CO and greenhouse gases alone cannot distinguish landscape fires from other combustion sources.

The fire-only CO increment is smaller than total observed CO. This necessary magnitude check does not validate the fire contribution: unmodeled background and other combustion sources remain, and several combinations of flux and transport can produce a similar increment.

The GFS fire scenario is equivalent to 95.8% of measured CO and leaves only 22.3 ppb for background and other passive CO contributions. This remainder is a conditional budget residual, not an independent background estimate. Under GDAS, fire-only CO reaches 1,023.2 ppb and exceeds the 531.15 ppb total observation. With passive transport and nonnegative background, the GDAS fire scenario cannot form a consistent concentration budget. Emission magnitude, vertical injection, transport and neglected chemical loss are competing explanations; the comparison does not establish that GFS is correct.

**Table 6. Fire scenarios and meteorological dependence.** Entries are seed means and ranges. Fire emissions are not combined with EDGAR in this table because source overlap and differing release assumptions must be resolved before constructing a joint budget.

| Driver | Gas / unit | Mean | Seed range |
| --- | --- | --- | --- |
| GDAS | CH₄ (ppb) | 82.918 | 82.314–84.026 |
| GDAS | CO (ppb) | 1023.226 | 1016.439–1036.135 |
| GDAS | CO₂ (ppm) | 6.418 | 6.383–6.475 |
| GFS | CH₄ (ppb) | 42.861 | 41.985–43.648 |
| GFS | CO (ppb) | 508.887 | 498.692–517.712 |
| GFS | CO₂ (ppm) | 2.595 | 2.550–2.624 |

![Landscape-fire source influence.](outputs/hysplit/gfs/analysis/figures/figure_11_fire_map.png)

**Figure 11.** GFED5.1 daily fire emissions weighted by the GFS ensemble footprint for 23–26 September 2019. Contribution density uses ppm CO₂ km⁻² or ppb CH₄ km⁻² and gas-specific logarithmic scales. The calculation treats fire emissions as a surface flux distributed uniformly over each UTC day; plume injection and sub-daily fire behavior are unresolved.

![Timing of modeled fire contributions.](outputs/hysplit/gfs/analysis/figures/figure_12_fire_timing.png)

**Figure 12.** GFS/GFED contributions grouped by source date for CO₂, CH₄ and CO. The 72 hourly source intervals contain 23 hours on 23 September, 24 hours on each of 24 and 25 September, and one hour on 26 September. Bar heights combine these unequal sampled durations, daily emissions and transport sensitivity; they are not daily regional emission totals.

Replacing daily variation with each cell's mean flux across the 72 sampled hours changes the GFS CO₂ fire contribution by +21.7%. This is a timing sensitivity within the available window, not an inventory uncertainty interval. It demonstrates how temporal allocation can affect source influence without changing the transport field.

Source hours on 23 September supply 84.2% of the modeled fire CO₂ increment. The fire-weighted influence is therefore concentrated near the older end of the experiment, even though the transport-only median age is 32 h. This distinction makes the backward-window length particularly consequential for the fire scenario: influence from still earlier emissions is not quantified here.

### Methane observation coverage and prior concentration budget

The multi-week experiment retains 27 receptor hours, covering both daytime and nighttime conditions (Figure 13). The four flask comparisons differ from in-situ values by at most 1.27 ppb; their small number prevents extending this agreement to every hourly record. The anthropogenic prior and the mean transport sensitivity have distinct geographic structures (Figure 14): a high-emission cell matters to BKT only where transport provides sensitivity to it.

![Methane receptor selection and flask comparisons.](outputs/hysplit/inversion/figures/figure_13_inversion_observations.png)

**Figure 13.** BKT hourly methane and the fixed twice-daily receptor selection, 9 September–6 October 2019. Filled circles enter fitting; open squares are withheld; crosses identify transport-ineligible receptor hours. Gaps remain unfilled. The lower panel shows NOAA flask-minus-in-situ methane at co-located sampled hours, in ppb. These comparisons assess sampled consistency, not a complete calibration uncertainty budget.

![Anthropogenic methane prior and mean transport sensitivity.](outputs/hysplit/inversion/figures/figure_14_inversion_support.png)

**Figure 14.** Period-weighted EDGAR anthropogenic methane flux and mean five-day BKT sensitivity for transport-eligible receptor hours. Flux is in µmol m⁻² s⁻¹; sensitivity density is ppm per (µmol m⁻² s⁻¹) per km². Both color scales are logarithmic. The star marks BKT and the dashed circle marks the 500 km geodesic partition. Sensitivity display uses Gaussian smoothing with standard deviation one 0.25° cell and fourfold interpolation, conserving its integral; inversion coefficients remain unsmoothed. The lower color threshold omits 1.00% of integrated display sensitivity, and 6.7% lies outside the map frame; these quantities are not additive because they overlap. Flux-color extensions denote values outside the displayed range; zero flux is transparent. Indonesia uses the established provincial GeoJSON and surrounding countries use full-resolution geoBoundaries.

The endpoint background ranges from 1826.8 to 1904.7 ppb across the retained hours. Median prior increments are 39.4 ppb from anthropogenic emissions within 500 km, 16.1 ppb from farther anthropogenic emissions, 20.9 ppb from wetlands and 20.3 ppb from non-crop fires. These are prior-model contributions, not measured source fractions (Figure 15). Across all receptor hours, the unadjusted inventory-plus-background prediction has bias 79.1 ppb and RMSE 101.0 ppb. A mismatch can arise from source magnitude, source timing, transport or boundary error; its sign alone does not identify the responsible component.

![Background and prior source increments.](outputs/hysplit/inversion/figures/figure_15_inversion_components.png)

**Figure 15.** Observed methane, particle-endpoint CarbonTracker background, and the unadjusted concentration budget at the selected BKT hours. The lower panel separates four positive prior source increments and the negative soil-uptake contribution. Fixed termite and geological terms are included in the upper budget but not the positive stack. Units are ppb. Monthly anthropogenic and wetland patterns, daily non-crop fire fluxes, and five-day GFS/HYSPLIT-STILT sensitivities determine these prior increments.

### Information content and posterior emission adjustments

The source-response matrix contains correlated spatial and temporal information (Figure 16). The sum of local prior-whitened information fractions is 1.97 across the six fitted parameters; it is not a count of resolved emission pixels. The strongest absolute off-diagonal source-response correlation is 0.55. Distinguishing components requires differences in their transport-weighted time series, not merely different inventory labels.

![Source-response correlations and information modes.](outputs/hysplit/inversion/figures/figure_16_inversion_information.png)

**Figure 16.** Pearson correlations among training-hour prior source responses and local prior-whitened information fractions for the six-parameter inverse state. If $s_j$ is a singular value of the whitened local Jacobian, the plotted fraction is $s_j^2/(1+s_j^2)$. The matrix describes response similarity without a significance test; the mode plot includes background parameters and does not establish spatial resolution.

**Table 7. Methane inverse parameters.** Emission multipliers are dimensionless; background offset is in ppb and trend in ppb per 28 days. Medians and 95% credible intervals come from the sampled posterior. The variance reduction is in the fitted parameter space (log space for emissions), relative to its stated prior; negative values indicate increased variance.

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

**Figure 17.** Prior and posterior emission intervals for the four-component methane state. Emission multipliers use a logarithmic axis; unity is the inventory reference. Lower panels show fitted background adjustments. Dots are posterior medians and colored intervals are equal-tailed 95% credible intervals from MCMC. Their interpretation is conditional on the response matrix, fixed source patterns and working covariance.

### Withheld prediction and residual evidence

The posterior withheld RMSE is 47.6 ppb, compared with 98.7 ppb for raw inventories, 40.0 ppb for the fitted background-only model and 86.0 ppb for background-adjusted inventories (Table 8; Figure 18). Emission fitting improves the withheld point-prediction RMSE relative to the adjusted-inventory baseline, but this finite conditional comparison does not establish independently validated emissions. The simpler fitted background-only model performs better (40.0 ppb RMSE); source fitting therefore does not demonstrate incremental predictive value over that baseline. The nominal 95% marginal prediction envelope contains 100.0% of withheld concentrations. Its median withheld width is 299.2 ppb, compared with 91.3 ppb for parameter-only intervals. Coverage must be considered alongside these widths and the small evaluation sample; a broad envelope can cover observations without precise emission information.

**Table 8. Methane concentration evaluation.** The split was specified before fitting; n is the number of receptor hours. Bias is predicted minus observed methane; MAE and RMSE are in ppb. Pearson r and R² are dimensionless; negative R² means squared errors exceed the squared departures of observations from their evaluation-sample mean. These are conditional concentration diagnostics, not errors against independently measured emissions.

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

**Figure 18.** Training-only posterior predictions for all retained BKT receptor hours, with 95% model-mean intervals and nominal 95% marginal mismatch-augmented envelopes. Open squares identify withheld observations. The lower panels compare withheld predicted and observed methane and RMSE against three baselines. The outer envelope does not condition correlated errors on training residuals and is not a fully conditional Gaussian forecast. CarbonTracker's assimilation of BKT limits strict independence.

Residuals span -97.0 to +53.3 ppb (observed minus posterior median). Their time evolution and relation to native GFS boundary-layer height and endpoint background are shown in Figure 19. Daytime residual RMSE is 53.6 ppb and nighttime RMSE is 43.6 ppb over the full retained sample; these descriptive regime diagnostics mix fitted and withheld hours. A residual association with boundary-layer height cannot by itself identify a mixing-depth bias, because emissions and meteorology co-vary.

![Posterior residual diagnostics.](outputs/hysplit/inversion/figures/figure_19_inversion_residuals.png)

**Figure 19.** Methane residual time series, distributions by fit/withheld split, and relationships with native GFS planetary boundary-layer height and endpoint background, 9 September–6 October 2019. Residuals are observed minus the training-only posterior median, in ppb. The native GFS boundary-layer height is meteorological context rather than the STILT-computed mixing depth. The height scatter omits 2 nonphysical negative decoded heights whose magnitudes fall within their archive records' packing-precision scale; the corresponding concentrations remain in the inversion and other panels. No observations were removed on the basis of these residuals.

### Robustness and recoverability

Across the stated non-base assumption tests, posterior-mode anthropogenic multipliers range from 0.48 to 0.76 within 500 km and 0.42 to 0.69 farther away (Figure 20). These scenario extrema have no assigned probability. In leave-one-week-out fits with a 24 h buffer, posterior RMSE ranges from 28.6 to 72.8 ppb and is lower than the background-adjusted inventory in 4 of four held weeks, but lower than the background-only baseline in only 1 of four. The four weekly evaluation samples contain 3, 14, 9, 1 receptor hours, respectively. These highly unequal counts reflect transport screening; a week with one retained hour supplies only a single-error diagnostic, not evidence of general weekly skill. Buffered exclusions test temporal dependence but remain a single-site, single-season evaluation.

![Methane inversion sensitivity to assumptions.](outputs/hysplit/inversion/figures/figure_20_inversion_sensitivity.png)

**Figure 20.** Anthropogenic emission adjustments under alternative background, covariance, prior, auxiliary-source, crop-overlap and daytime-sampling assumptions. Shading is the base-case sampled 95% credible interval; points are separately optimized modes in log-emission parameter space, transformed to multipliers. Both axes are logarithmic. Scenario spread is not a credible interval, and crossing the inventory reference indicates sensitivity to assumptions rather than a change in observed emissions.

**Table 9. Transport and boundary sensitivity at preselected anchors.** Changes are relative to the base run at the same receptor hour. Source-increment change includes the four optimized positive source components before fitting. Background differences are evaluated only where both runs retain at least 95% of particles; otherwise they are not evaluable. In low-retention runs, integrated source sensitivity is truncated by domain exits and is not a complete-duration convergence test. This table does not establish convergence for all receptor hours or all atmospheric regimes.

| Test (anchors) | Sensitivity change (%) | Source change (%) | Background change (ppb) | Retention (%) |
| --- | --- | --- | --- | --- |
| Alternate seed (4) | +0.6 to +5.5 | -17.9 to +10.8 | -4.5 to +0.7 | 96.1 to 100.0 |
| 60 m release (4) | +0.3 to +8.8 | -2.3 to +40.7 | -3.8 to +0.2 | 97.0 to 100.0 |
| 2,000 requested particles (2) | -3.8 to +2.8 | -7.2 to +16.4 | -2.2 to +0.7 | 99.0 to 100.0 |
| 72 h window (2) | -21.8 to -20.2 | -36.1 to -15.9 | +20.2 to +25.6 | 100.0 to 100.0 |
| 168 h window (2) | +8.0 to +13.6 | +1.8 to +20.5 | Not evaluable | 72.2 to 87.0 |

The base-run endpoint retention ranges from 17.2 to 100.0%; 25 otherwise observation-valid receptors fail the 95% retention criterion. This transport-only screening can favor circulation regimes that remain inside the supplied meteorological domain, so the selected hours are not a uniform representation of the full period. Across all sampled active endpoints, 1.75% lie below the lowest CarbonTracker layer center. Shifting endpoint heights by ±500 m changes the mean background at eligible receptors by up to 22.2 ppb. The oldest 24 h supplies 3.0 to 11.2% of each eligible footprint's integrated sensitivity, indicating how much sensitivity remains near the finite-window limit. An endpoint boundary accounts for incoming methane but does not correct biased regional transport. The outermost output-cell share reaches 0.132%; an edge diagnostic alone cannot prove that no external source influence was omitted.

Matched-operator synthetic recovery and deliberately perturbed recovery are compared in Figure 21 and Table 10. Across components, matched-operator local-interval coverage ranges from 89.5 to 98.0%, compared with 90.0 to 96.0% under the perturbed scenario. Shrinkage toward prior values and imperfect recovery must be considered when interpreting source-specific estimates. These experiments test the estimator under specified synthetic truths and errors; they are not independent validation of the real emission estimates.

**Table 10. Synthetic methane recovery.** Each scenario uses 200 noise realizations and the stated four-component synthetic truth. Bias and RMSE are in multiplier units. Coverage is the fraction of local approximate 95% intervals containing the synthetic truth; real-data credible intervals use MCMC instead.

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

**Figure 21.** Distribution of recovered multipliers under matched and perturbed response/background scenarios. Boxes show medians and interquartile ranges; whiskers extend to the most extreme values within 1.5 interquartile ranges, with farther points omitted from display only. Diamonds mark synthetic truth. The lower panel shows local-interval coverage, with 95% as a reference. The experiment uses the actual selected receptor geometry but simulated concentrations.

### Conditional regional emission totals and spatial support

Applying the posterior multipliers to the fixed prior patterns gives the 28-day regional totals in Table 11. These totals inherit the prior's spatial allocation—including weakly sampled cells within each region—and should not be interpreted as independently measured Sumatra-wide or national totals. Only 18.9% of the distant region's anthropogenic prior mass lies in the cells containing 90% of aggregate surface sensitivity; extending its fitted multiplier to the full distant region is therefore a prior-pattern extrapolation. Sector-specific values are conditional reallocations under the shared anthropogenic multiplier, not separate sector retrievals. The adjustment map in Figure 22 deliberately displays only that transport-support mask, without inventing pixel-scale inversion detail.

**Table 11. Conditional methane emissions, 9 September–6 October 2019.** Values are Gg CH₄ over 28 days, not annualized rates. Posterior intervals propagate multiplier uncertainty only. The last column is the fraction of prior mass in cells containing 90% of aggregate surface sensitivity, not a fraction of independently retrieved emissions. The distant region is limited to the modeled domain; wetlands and non-crop fires share their respective multiplier across both regions.

| Region / component | Prior (Gg) | Posterior median (95%) (Gg) | Prior in support (%) |
| --- | --- | --- | --- |
| ≤500 km / anthropogenic | 143.9 | 83.8 (28.1–191.8) | 49.6 |
| ≤500 km / wetlands | 73.1 | 46.5 (14.9–113.8) | 42.5 |
| ≤500 km / noncrop fire | 165.6 | 126.3 (44.3–259.5) | 92.8 |
| >500 km / anthropogenic | 3,308.0 | 1,681.3 (600.3–3,629.0) | 18.9 |
| >500 km / wetlands | 862.6 | 549.1 (176.3–1,342.8) | 0.8 |
| >500 km / noncrop fire | 982.3 | 749.2 (262.6–1,539.1) | 17.9 |

Within 500 km, waste and fuel exploitation together account for 77.4% of the anthropogenic inventory total. Table 12 translates the common regional multiplier into sector allocations. Because the inversion does not estimate separate sector multipliers, their shares remain fixed to EDGAR: agreement or disagreement with BKT cannot identify which of these sectors is individually biased.

**Table 12. Conditional anthropogenic sector allocation within 500 km of BKT.** Emissions are Gg CH₄ over 9 September–6 October 2019. Parentheses contain 95% intervals propagated from the shared regional multiplier. Sector shares are inherited from the inventory, not measured or independently inferred. Rounded shares may not sum exactly to 100%.

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

**Figure 22.** Anthropogenic posterior-median multipliers in the two prescribed regions and five-day backward endpoint locations. Adjustment colors are masked outside cells containing 90% of aggregate footprint sensitivity; uncolored areas are weakly sampled, not zero-emission areas. The 500 km partition is geodesic. Endpoint colors indicate height in km above mean sea level; deterministic thinning is for display only and all retained endpoints enter background sampling. Boundaries use the established Indonesian GeoJSON and full-resolution geoBoundaries; the map is not a province- or facility-level retrieval.

## 5. Discussion and uncertainty

The footprint and source-weighted calculations provide complementary evidence. Transport-only sensitivity identifies where surface exchange can efficiently affect the receptor. Inventory-weighted contributions identify where a specified flux estimate intersects that sensitivity. The gas-specific sector and geographic differences follow from this interaction and should not be read directly from the most intensely colored footprint cells.

The driver comparison cannot be reduced to a uniform change in dilution: the -27.0% change in integrated sensitivity differs from the -61.4% and -34.1% changes in anthropogenic CO₂ and CH₄. Within this experiment, redistribution relative to the source fields therefore materially affects the modeled mixture. The result supports evaluating transport and inventory alignment jointly, rather than selecting meteorology solely because its grid is finer or its total sensitivity is similar.

The closer GFS grid-point elevation to BKT offers a physically relevant reason to examine its performance. However, mountain representativeness also depends on wind direction, vertical shear, stability, convective exchange and the relationship between the inlet and modeled terrain. No independent winds, boundary-layer observations or concentration enhancement series were used to establish that either meteorological driver is superior. Small seed spread cannot compensate for shared meteorological bias [8].

The transport benchmark in the final appendix adds an observation-based GFS profile check and matched mixing tests. It does not compare the two drivers against assimilation-independent observations or validate BKT's local mixing depth; therefore it does not establish which driver or parameterization is more accurate.

A complete mole-fraction budget would require

$$
c_g(t_r)=c_{g,\mathrm{background}}(t_r)+\Delta c_{g,\mathrm{anthropogenic}}+\Delta c_{g,\mathrm{fire}}+\Delta c_{g,\mathrm{ecosystem}}+\Delta c_{g,\mathrm{other}}.
$$

The background term represents air not accounted for by the modeled regional exchange window. The ecosystem term includes net photosynthesis and respiration for CO₂, and natural methane exchange where applicable. These terms are absent from the single-hour forward case; the multi-week methane inversion includes modeled boundary methane and selected natural exchange, with the limitations described below. Subtracting only the partial forward-inventory contributions from the observed mole fraction would not establish a measured background. Comparing that partial sum directly with the absolute observation would likewise not produce a meaningful validation error.

EDGAR agriculture can include agricultural-residue burning, while a landscape-fire inventory can include burning on agricultural land. Without a reconciled partition, adding both CH₄ estimates risks double counting. Fossil CO₂ and landscape-fire CO₂ are more clearly separated conceptually, but the omitted ecosystem and background terms still prevent budget closure. Transport and power-sector surface-release equivalents also require caution because real emissions can enter above the surface layer.

**Table 13. Material uncertainties and consequences.** Numerical checks do not eliminate these scientific uncertainties.

| Uncertainty | Consequence for interpretation | Minimum additional evidence |
|---|---|---|
| Meteorological winds and mountain circulation | Footprint position and dilution may be biased | Independent wind profiles and multiple receptor periods |
| Mixing depth and minimum depth | Near-surface sensitivity can be magnitude-sensitive | Boundary-layer observations and parameter sensitivity |
| Stack and fire injection heights | Surface-release estimates may misrepresent elevated sources | Source-specific vertical profiles or forward dispersion |
| Inventory amount, placement and timing | Sector ranking and enhancement can change | Alternative inventories and regional activity constraints |
| Fire–agriculture overlap | Summation can double count some emissions | Harmonized sector definitions and fire partitions |
| Ecosystem exchange, biofuel CO₂ and background | Absolute concentration budget is incomplete | Independent boundary conditions and missing source/sink fields |
| Single-hour sampling | Results need not generalize by season or regime | Multi-season, independently evaluated receptor ensembles |
| Finite integration window | Older influence is omitted | Longer backward simulations and boundary sensitivity |
| Finite output domain and eastern tail | Source influence beyond the regional domain is unquantified | Wider output-domain simulations and inventory coverage |

The single-hour forward results are suitable for research screening and prioritizing source datasets, not for regulatory attribution or an operational emission estimate. A single selected hour cannot constrain the many spatial and sectoral unknowns independently. The multi-week inversion supplies an explicit low-dimensional estimation experiment; it does not remove these limits by increasing the number of plotted cells.

### What the methane inversion establishes—and what remains conditional

The methane experiment implements an observation-constrained inverse calculation rather than merely overlaying an inventory with a footprint. Its defensible inference is an update to a small set of regional source multipliers under explicit transport, background, natural-flux and error assumptions. The 95% interval for anthropogenic ≤500 km includes unity. The 95% interval for anthropogenic >500 km includes unity. The 95% interval for wetlands includes unity. The 95% interval for non-crop fires includes unity. Emission fitting improves the withheld point-prediction RMSE relative to the adjusted-inventory baseline, but this finite conditional comparison does not establish independently validated emissions. The simpler fitted background-only model performs better (40.0 ppb RMSE); source fitting therefore does not demonstrate incremental predictive value over that baseline. An improvement over raw inventories is insufficient on its own: the background-adjusted baseline tests whether emission adjustment adds predictive value beyond changing the boundary level and trend.

The posterior uncertainty is narrower than the full scientific uncertainty problem. A single mountain receptor can observe different combinations of sources over time, but correlated response patterns, weak footprints and compensating background adjustments can leave individual categories poorly determined. Published wetland-model analyses identify rice–wetland separation as difficult in South Asia [10]; this single-station inversion does not independently verify that land-use partition. Fixed within-region patterns transfer any estimated scaling to cells and sectors that may receive little direct observational sensitivity. The maps and conditional totals therefore do not support regulatory responsibility, individual-source attribution or verified mitigation accounting.

Three structural limits deserve particular weight. First, CT-CH₄-2025 assimilates BKT, so this is a regional inversion conditional on an observation-informed global boundary, not an independent replication. Second, quarter-degree GFS cannot resolve all terrain-driven circulation or tropical convective exchange, and sparse transport sensitivity anchors cannot establish full operator accuracy. Third, wetland, soil, termite and geological fields have model or climatological dependence; unresolved inland-water exchange, spatial allocation and source-height errors can be absorbed into another component's multiplier. Methane is treated as passive over five days; neglected chemical loss is an additional approximation rather than evidence that methane has no atmospheric sink.

The strongest next tests are a boundary product excluding BKT (or a leave-BKT-out global analysis), independent wind and mixing-layer observations, additional receptor sites, and multi-season replication with alternative natural-flux and transport realizations. These would test whether regional adjustments persist when the principal sources of compensating error change. The present system is an experimental inversion workflow, not an operationally validated emissions service.

<!-- pdf-pagebreak -->

## 6. Conclusions

For the selected BKT observation, the GFS-driven footprint quantifies the distribution of surface-flux sensitivity in space and backward time. Matched GDAS calculations show that the result depends materially on the meteorological representation, while seeded and height experiments characterize narrower components of numerical and receptor uncertainty.

EDGAR and GFED provide explicit, gas-specific source scenarios. The anthropogenic sector and provincial rankings are conditional on inventory fluxes and modeled transport, and daily fire allocation changes the predicted influence. These products go beyond a pathway map, but do not constitute observational source attribution or a closed atmospheric greenhouse-gas budget.

The multi-week methane calculation produces a reproducible, positive-emission Bayesian inversion with explicit boundary conditions, natural exchange, held-out concentration checks, synthetic recovery and sensitivity analysis. Emission fitting improves the withheld point-prediction RMSE relative to the adjusted-inventory baseline, but this finite conditional comparison does not establish independently validated emissions. The simpler fitted background-only model performs better (40.0 ppb RMSE); source fitting therefore does not demonstrate incremental predictive value over that baseline. Its emission estimates are conditional regional adjustments, with uncertainty from the fitted posterior distinguished from structural sensitivity. Independent boundary and meteorological evidence, additional receptors and seasonal replication are needed before interpreting these results as verified regional emission totals.

The general transport benchmark demonstrates that domain truncation can be corrected numerically in a severe-loss case, while mixing-depth and receptor-height choices remain scientifically unvalidated. These conclusions apply across passive surface-flux calculations rather than to methane alone. Expanded ensemble coverage and independent local transport constraints are required before interpreting a revised inversion; no emission estimate is updated here.

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

<!-- pdf-pagebreak -->

## Appendix. Definitions and numerical interpretation

**Table 14. Terms used in this report.**

| Term | Meaning |
|---|---|
| Mole fraction | Number of molecules of a gas relative to dry-air molecules |
| Footprint | Receptor sensitivity to a distributed surface flux |
| Flux density | Emission or uptake per surface area per time |
| Enhancement | Modeled increment associated with specified fluxes, excluding background |
| PBL | Planetary boundary layer: the lower atmosphere strongly influenced by the surface |
| AGL | Height above local ground, distinct from elevation above mean sea level |
| Seed range | Finite-particle spread under repeated stochastic simulations with fixed physics |
| Total variation | Half the absolute difference between two normalized spatial distributions |
| Surface-release equivalent | Contribution calculated by treating inventory emissions as surface flux |
| Prior | Source or parameter distribution specified before fitting the receptor observations |
| Posterior | Parameter distribution after combining the stated prior and observational likelihood |
| Credible interval | Probability interval conditional on the Bayesian model and assumptions |
| Predictive interval | Interval including both parameter uncertainty and stated model–observation mismatch |
| Identifiability | Ability of available observations to distinguish parameter combinations |
| MCMC | Markov chain Monte Carlo: numerical sampling of the posterior distribution |

Spatial total variation is calculated as $\frac{1}{2}\sum_{ij}|p_{ij}-q_{ij}|$, where each field is conservatively aggregated onto the same grid and normalized to sum to one. A zero value indicates identical normalized distributions; a value of one indicates nonoverlapping support. Reported percentages multiply this quantity by 100. This is a distributional comparison, not a skill score.

Seed-wise flux convolutions are computed before forming means and ranges. Monthly anthropogenic fields remain constant through the source window; daily fire fields change at the assumed calendar-day boundaries. Provincial fractions are applied to the contribution field, rather than multiplying a province's total emissions by an average footprint. This preserves the spatial relationship between source intensity and sensitivity within the analysis resolution.

The conservation checks independently reconcile gridded coefficients and tabulated totals, compare equivalent orders of conservative remapping and convolution, and verify that continuous map reconstruction preserves the domain integral. These tests establish numerical consistency within the model design. Scientific accuracy additionally requires the independent evaluation described in the discussion.

**Table 15. Worked cell-level convolution examples.** Each row selects one strongly contributing anthropogenic source cell. Sensitivity is summed across the 72 source intervals and multiplied by that cell's matched September-mean flux. The product is ppm; the methane row additionally uses 1,000 ppb per ppm. Values are illustrative parts of the actual gridded calculation, not separate observed sources.

| Gas / unit | Cell (° N, ° E) | Sensitivity | Flux (µmol m⁻² s⁻¹) | Contribution |
| --- | --- | --- | --- | --- |
| CO₂ (ppm) | -0.202, 100.318 | 0.57619 | 0.22986 | 0.13244 |
| CH₄ (ppb) | -0.202, 100.418 | 0.51110 | 0.00903 | 4.61648 |

### Worked methane inverse concentration budget

Table 16 uses the first transport-eligible withheld receptor, 16 September 2019 at 06:00 UTC. Each source term is its prior response multiplied by the posterior **mean** multiplier; the mean background offset and trend are added to endpoint methane and fixed natural exchange. Linearity in the multipliers makes their sum equal to the posterior mean concentration. It need not equal the posterior median plotted elsewhere, because the transformed posterior is asymmetric. No component is adjusted afterward to force agreement with the withheld observation.

**Table 16. Worked inverse methane budget at one withheld receptor.** Values are ppb. Positive source terms add methane; soil uptake enters the fixed auxiliary term with a negative sign. Posterior means are used for this additive identity; two-decimal display precision supports arithmetic inspection rather than implying a 0.01 ppb uncertainty. Rounding can produce a small difference between displayed subtotals and total.

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

## Appendix. Finer-grid meteorology did not pass the conversion screen

**Decision: retain the existing GFS inversion; no BARRA-driven transport or emission update is reported.** A follow-up screen examined the public Bureau of Meteorology Atmospheric high-resolution Regional Reanalysis for Australia, version 2, deterministic product (BARRA-R2). Its native 0.11° horizontal grid covers BKT, but a finer horizontal grid does not establish better transport accuracy [14]. The screen identified missing pressure-level fields in cells where those levels are above the supplied model surface. Direct conversion to HYSPLIT input was therefore stopped before filling or extrapolating those values.

### Scope and a reproducible missing-data test

The inspected subset covers 94.97°–104.98° E and 4.95° S–4.95° N on 9 September 2019, 00:00–12:00 UTC, inclusive: 13 hourly timestamps on a 91 by 92 grid. This is a bounded conversion screen, not a monthly data-quality estimate or a transport-skill evaluation. Native latitude–longitude coordinates and timestamps were matched across variables. Surface pressure was converted explicitly from Pa to hPa; vertical velocity was verified as upward-positive in m s⁻¹. Packed fill values and nonfinite subset values were retained as missing, never interpreted as zero.

A pressure level $p$ was classified as clearly above the local surface when $p_s > p + \Delta p$, where $p_s$ is supplied surface pressure and the main diagnostic uses $\Delta p=1$ hPa. Pressure decreases with height. The margin separates the result from tiny pressure-rounding differences; a second calculation with $\Delta p=10$ hPa tests that sensitivity. This is a consistency check against the supplied pressure field, not an independent observation of terrain height.

**Table 17. Missing BARRA-R2 pressure-level data above the supplied surface.** Counts are cell–timestamp pairs, not independent statistical samples. Each row applies separately to all six inspected fields: eastward wind, northward wind, upward air velocity, temperature, specific humidity and geopotential height. The main denominator includes only cells satisfying the 1 hPa pressure-margin criterion. The last column repeats the gap count using the stricter 10 hPa margin.

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

## Appendix. Transport completeness and unresolved mixing uncertainty

**The expanded domain restores particle completeness in the severe-loss case, but no mixing, receptor-height or convection configuration is independently validated as superior.** Endpoint retention increases from 17.2% to 100.0%. The observational check constrains meteorological forcing errors, not the full surface-flux operator.

This benchmark concerns the passive transport operator shared by surface-flux calculations for all three gases. It does not refit emissions, use methane residuals to choose settings, or establish a complete concentration budget. Numerical completeness, sensitivity to assumed physics, and agreement with meteorological observations answer different questions and are assessed separately.

### Domain boundaries and backward duration

Of 52 original five-day receptor runs, 25 failed the existing 95% endpoint-retention screen. In the most severe case, released on 6 October 2019 at 06:00 UTC, only 93 of 540 emitted particles remained active after 120 hours. Hourly records bracket the loss of each inactive particle between its final active location and the next inactive record. All losses were last recorded nearest the eastern meteorological boundary; the model also reported a spatial-domain exit. Inactive coordinates are placeholders, not air parcels arriving at the equator and Greenwich meridian.

The matched domain test expands the same quarter-degree GFS meteorology from 75–130° E, 20° S–20° N to 50–160° E, 40° S–30° N. Variables, hybrid levels, timestamps and resolution remain unchanged. All 16,704 shared-domain variable–level–time fields agree within the sum of their two packing increments. Some are not bit-identical because the larger extraction is repacked; changes in trajectory detail and shared-grid sensitivity cannot be attributed solely to domain extent. The initial footprint grid is retained for the first contrast; a separate wider footprint grid tests omitted surface sensitivity. These comparisons distinguish different forms of truncation, subject to the stated packing limitation.

**Table 18. Domain-completeness experiment for the 6 October 2019 receptor.** All runs extend 120 hours backward and use the same release, physics and actual-particle normalization. Integrated sensitivity has units ppm per (µmol m⁻² s⁻¹); it is the response to a unit flux in every included cell and hour, not a measured concentration. Edge share is the fraction on the outermost footprint cells.

| Configuration | Active (%) | Sensitivity | Outside old grid (%) | Edge (%) |
| --- | --- | --- | --- | --- |
| Original domains | 17.2 | 3.964 | 0.00 | 0.458 |
| Wider meteorology | 100.0 | 3.870 | 0.00 | 0.429 |
| Both domains wider | 100.0 | 4.325 | 10.51 | 0.000 |

The wider footprint grid places 10.51% of its integrated sensitivity outside the original output grid. Its outermost cells contain 0.000% of sensitivity, and the closest surviving endpoint is 1166 km from the expanded meteorological boundary. The oldest 24 hours still supply 14.7% of five-day sensitivity. On the original output grid, wider meteorology changes integrated sensitivity by -2.4%; this is not a pure domain-effect estimate because the meteorological packing also changes. In contrast, expanding only the output grid preserves every shared cell-hour coefficient exactly. This establishes improved numerical coverage for this case, not five-day temporal convergence, atmospheric accuracy, or completeness of all original receptor runs.

![Domain retention and accumulated sensitivity](outputs/hysplit/benchmark/figures/domain_completeness.png)

**Figure 23.** Particle retention and accumulated surface-flux sensitivity for the 6 October 2019, 06:00 UTC BKT receptor. The denominator is the actual emitted-particle count. Retention is a meteorological-domain diagnostic; accumulated sensitivity additionally depends on the footprint grid and backward duration. GFS-driven HYSPLIT-STILT simulations, with hourly diagnostic records and identical non-domain settings.

Four separate controls at 06:00 and 18:00 UTC on 9 and 23 September retained all emitted particles through 72 hours, with no sensitivity on the outermost footprint cells. Their fields match the corresponding first 72 hours of the original five-day runs exactly. The additional two days supply 15.8–21.8% of the original five-day integrated sensitivity. Thus, three days is a bounded physics-comparison window, not a demonstrated convergence horizon or a recommended shortening of the five-day calculation. Even five-day particle retention cannot establish that older transport is negligible.

### Mixing depth, release height and stochastic sampling

The predeclared contrasts change one assumption at a time: the minimum mixing depth from 250 m to 100 or 50 m; modified-Richardson-number mixing depth to the meteorological model's native depth; receptor height from 30 to 60 m above model ground; and convection treatments including a convective available potential energy (CAPE) threshold. The Richardson-number approach compares thermal stratification with wind shear. Four matched receptor times represent two dates and two clock periods, 13:00 and 01:00 WIB. They are not independent seasonal replicates. Each run actually emits 540 particles; coefficients are normalized to that count. Two further unchanged-physics seed repeats at each time describe finite-particle variation without supplying full uncertainty intervals for every perturbation.

**Table 19. Matched three-day transport sensitivities.** Ratios compare integrated sensitivity with the same-time control. The range spans the four receptor times, not a confidence interval. The spatial absolute-difference measure is the sum of absolute cell differences divided by the control's integrated sensitivity, in percent; it combines changes in magnitude and location. Seed controls describe numerical sampling, not atmospheric uncertainty.

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

**Figure 24.** Integrated-sensitivity ratios under one-factor transport perturbations at BKT on 9 and 23 September 2019 (UTC dates). Legend dates and times are in WIB; the nighttime releases therefore fall on 10 and 24 September locally. Each marker represents a matched receptor time; the reference value of one denotes no change. Control-seed ranges provide context for finite-particle variation. These are model responses, not demonstrated improvements in transport skill.

A fixed-site model diagnostic with a 50 m floor places mixing depth below 250 m at 100.0% of the sampled 17:00–07:00 WIB clock-period times under the modified-Richardson-number method. The diagnosis uses three-hourly meteorology over 9 September–6 October and includes 112 such samples. It explains why the imposed floor can matter, especially during shallow nocturnal mixing. It is not an observed boundary-layer height and uses different turbulence time-scale assumptions from the full footprint calculation. Lowering the floor is therefore a physically motivated sensitivity test, not a validated correction for mountain-valley exchange.

### Convection compatibility and executed response

The original requested Grell treatment requires convective flux fields that are absent from the inspected GFS archive. The archive also lacks a supplied convective available potential energy (CAPE) field. The alternative positive threshold requests profile-derived CAPE and enhanced cloud-layer redistribution above 500 J kg⁻¹ [17]. Disabling the original requested convection option produces exactly the same cell-hour footprint coefficients at all four receptor times. The positive CAPE-threshold experiment also produces no cell-hour response in these cases; this does not establish whether the threshold was reached. The model explicitly disables its WRF-specific vertical interpolation for these non-WRF inputs. A requested option is not evidence that its associated physics was active; conversely, a null contrast does not establish that real atmospheric convection was absent.

### Observation-based evaluation and its independence limits

Public Integrated Global Radiosonde Archive (IGRA) version 2.2 records were matched to GFS at their observation locations and nominal UTC times over 9 September–6 October 2019 [18, 19]. Standard levels of 925, 850, 700, 500 and 300 hPa were used where present. Meteorological wind direction was converted to eastward and northward components. Model fields were sampled bilinearly and interpolated in log pressure using the archived pressure variable, without vertical extrapolation. Missing and provider-rejected values remain unavailable; they were not removed because of model disagreement.

For wind, the vector root-mean-square error (RMSE) is the square root of the mean of $(u_m-u_o)^2+(v_m-v_o)^2$, first averaged across available levels within each sounding, then across soundings within a day and across days. Here, $u$ and $v$ are the eastward and northward wind components in m s⁻¹; subscripts $m$ and $o$ denote model and observation. Temperature uses the corresponding scalar squared error. This equal-day estimator prevents vertical sampling density from creating false replication. The 95% intervals use 3,000 circular moving-block resamples of three consecutive daily summaries. They describe sampling variability in this period, not all observational and model uncertainty.

**Table 20. GFS forcing agreement with Padang profiles.** Errors are model minus observation. Wind and temperature have different valid sounding counts. Confidence intervals use three-day blocks and do not establish assimilation independence.

| Metric | Estimate | 95% interval | Soundings |
| --- | --- | --- | --- |
| Eastward-wind bias (m s⁻¹) | -0.12 | -0.37–0.17 | 59 |
| Northward-wind bias (m s⁻¹) | 0.25 | 0.09–0.42 | 59 |
| Wind-vector RMSE (m s⁻¹) | 2.77 | 2.17–3.56 | 59 |
| Temperature bias (K) | 0.06 | -0.04–0.15 | 54 |
| Temperature RMSE (K) | 0.69 | 0.62–0.75 | 54 |

![Profile evaluation across pressure levels](outputs/hysplit/benchmark/figures/profile_evaluation.png)

**Figure 25.** Pressure-resolved wind-vector RMSE and temperature bias for the Padang observation-based check, 9 September–6 October 2019. Available-level results are compared with the subset having complete five-level wind-and-temperature profiles. Each pressure-level estimate gives equal weight to daily summaries; whiskers are pointwise 95% intervals from three-day block resampling, not simultaneous intervals across levels. Lines connect diagnostic levels, not additional observations. Aggregate uncertainty and sounding counts are reported in Table 20. Neither this coastal profile nor its model counterpart is treated as a direct BKT mixing-depth measurement.

Nearest-cell, historical-position and one-hour timing alternatives give wind-vector RMSE values of 2.78–2.92 m s⁻¹, compared with 2.77 m s⁻¹ for the primary sampling. Restricting to 53 complete five-level wind-and-temperature profiles lowers wind-vector RMSE to 2.26 m s⁻¹. This coverage sensitivity is larger than the tested small collocation changes and prevents treating the aggregate as invariant to sampling. The wind-only profile on 15 September at 06:00 UTC contributes 31.6% of the aggregate wind mean-square error. Its large mismatch persists under the collocation alternatives. It remains in the primary estimate: missing temperature and model disagreement are not sufficient grounds to reject its winds. Pekanbaru contributes only 4 selected pressure-level wind pairs on 2 days and no paired temperature; its results are retained but cannot support a second-station performance claim. IGRA fixed-station coordinates reflect the latest inventory rather than a reconstructed historical launch location [19]. Historical-position and one-hour timing perturbations therefore test representativeness rather than silently assuming exact collocation. Balloon drift and level-dependent ascent time remain unresolved.

The observations were not used to tune this benchmark, but possible assimilation into GFS has not been excluded. This is an observation-based forcing check, not demonstrably assimilation-independent validation. No co-located BKT turbulence, mixing-depth or tracer-release observations were available to select the mixing or receptor-height configuration. Small mean wind bias also cannot exclude substantial trajectory displacement, especially when errors are temporally correlated.

### Decision and remaining evidence

Prioritize meteorological and footprint-domain completeness before interpreting five-day flux contributions. Apply the expanded-domain check across the full receptor ensemble before rebuilding an inversion operator. Keep the existing baseline settings unchanged while carrying mixing-depth, receptor-height and convection alternatives as explicit model sensitivities. Do not choose a setting solely because it reduces a gas residual or increases integrated sensitivity.

The next atmospheric validation requires co-located wind and stability profiles or boundary-layer observations across day and night, plus documented assimilation status or withheld observations for genuinely independent forcing evaluation. Replicated perturbation ensembles and further domain/duration expansion are needed before translating sensitivity changes into transport-error bounds. The present findings do not justify a revised emission inversion or a claim that a particular mixing or convection setting is more accurate.


<!-- pdf-pagebreak -->

## Appendix. Full-ensemble domain correction and prior methane-budget convergence

**The widened configuration raises the number of transport-complete receptor hours from 27 to 52 of 52, with median wide-domain particle retention of 100.0%.** For the 27 matched hours, the mean net prior surface-methane contribution changes by -5.38 ppb (-3.7% relative to the original retained-hour mean). This corrects numerical coverage but does not establish atmospheric accuracy or justify refitting the inversion.

The extension reruns all 52 available twice-daily receptors from 9 September to 6 October 2019 with a 50°–160° E, 40° S–30° N meteorological crop and a 60° by 100° footprint grid [3]. It preserves the original five-day transport physics and actual-emitted-particle normalization. This is a matched correction configuration, not a pure domain perturbation: the larger meteorological extraction is repacked, so small shared-field differences accompany the removal of boundary truncation. No gas value selected a rerun, and no inversion was refitted.

![Full-ensemble particle retention and surface-flux sensitivity under the original and widened domains.](outputs/hysplit/domain_budget_extension/figures/domain_ensemble.png)

**Figure 26.** Original and widened-domain diagnostics for 52 BKT receptors, 9 September–6 October 2019. Panel (a) shows the active fraction of the actual emitted particles; the horizontal line is the pre-existing 95% eligibility screen. Panel (b) compares integrated surface-flux sensitivity for the same receptor hour. Color denotes whether the original run passed that screen. Values are forward-model diagnostics, not measures of atmospheric accuracy.

The paired and sample-composition terms answer different questions. For a metric $X$, the reported total change is decomposed exactly as

$$
\overline{X}_{\mathrm{wide,all}}-\overline{X}_{\mathrm{original,retained}}
=\left(\overline{X}_{\mathrm{wide,retained}}-\overline{X}_{\mathrm{original,retained}}\right)
+\left(\overline{X}_{\mathrm{wide,all}}-\overline{X}_{\mathrm{wide,retained}}\right).
$$

The first term is a same-hour paired configuration change. The second is the composition change from recovering hours that the original domain excluded. Pointwise 95% intervals use 5,000 circular three-day block resamples of receptor dates; they describe short-record sampling variability and are not atmospheric-model uncertainty.

**Table 21. Original-to-wide decomposition across the 52-hour BKT ensemble.**

| Metric | Same-hour change (95% interval) | Recovered-hour composition (95% interval) | Total change (95% interval) |
| --- | --- | --- | --- |
| Integrated sensitivity [ppm / (µmol m⁻² s⁻¹)] | -0.030 (-0.107 to 0.072) | +0.080 (-0.782 to 0.745) | +0.051 (-0.830 to 0.744) |
| Net prior surface CH₄ (ppb) | -5.38 (-19.49 to 9.25) | -3.49 (-21.74 to 21.40) | -8.88 (-37.32 to 26.35) |
| Endpoint background CH₄ (ppb) | -0.29 (-0.87 to 0.30) | -7.38 (-16.35 to -2.15) | -7.66 (-16.36 to -2.35) |
| Combined prior CH₄ (ppb) | -5.67 (-20.06 to 8.85) | -10.87 (-28.20 to 13.86) | -16.54 (-42.83 to 17.09) |

### Selection pattern in the observed gases

Relative to originally retained hours, CO₂ is 1.49 ppm lower (interval includes zero) in recovered hours, CH₄ is 28.36 ppb lower (interval excludes zero) in recovered hours, and CO is 264.13 ppb lower (interval includes zero) in recovered hours. These block-resampled contrasts quantify which observations the original transport screen omitted; they do not attribute the gas differences to transport or any source.

![Observed BKT gas concentrations in hours retained and excluded by the original transport-domain screen.](outputs/hysplit/domain_budget_extension/figures/selection_concentrations.png)

**Figure 27.** Quality-controlled BKT CO₂, CH₄ and CO for hours retained by the original 95% particle screen and hours recovered by widening the transport domain. Points are observed concentrations; boxes show medians and interquartile ranges. The grouping is determined by modeled particle retention, not concentration. Differences therefore diagnose sample composition and do not imply that widening a domain changes an observation or that transport loss causes the concentration contrast.

**Table 22. Observed concentration difference between recovered and originally retained hours.**

| Observed gas | Retained mean | Recovered mean | Recovered minus retained | 95% interval |
| --- | --- | --- | --- | --- |
| CO₂ (ppm) | 420.41 | 418.92 | -1.49 | -9.42 to 4.74 |
| CH₄ (ppb) | 1918.07 | 1889.70 | -28.36 | -52.50 to -2.32 |
| CO (ppb) | 570.74 | 306.61 | -264.13 | -533.41 to 11.02 |

Calendar-month, WIB clock-period and GFS 10 m wind strata are reported as short-record diagnostics rather than seasonal or observational meteorology. Original retention was 12/26 (46.2%) for 07:00–17:59 WIB and 15/26 (57.7%) for 18:00–06:59 WIB; 26/39 (66.7%) in September and 1/13 (7.7%) during 1–6 October; and 13/26 (50.0%) under eastward versus 14/26 (53.8%) under westward modeled 10 m flow. The pronounced calendar imbalance means that the recovered-minus-retained gas contrasts are temporally confounded; the block intervals describe sampling variability but do not adjust for temporal evolution.

### Surface contribution and endpoint-background convergence

The 120-to-168-hour increment is smaller than the 72-to-120-hour increment in original surface 5/5, original background 4/5, original combined 3/5, widened surface 5/5, widened background 4/5, widened combined 4/5 representative comparisons. Opposing surface and background changes reduce the combined increment in 14 of 20 domain–duration–receptor contrasts. For the widened 24 September 18:00 UTC case, a +27.31 ppb surface increment and -27.02 ppb background increment leave only +0.29 ppb in the combined term; this is component cancellation, not joint convergence. In the severe 6 October 06:00 UTC case, the combined increment falls from +13.76 ppb in the original domain to +1.55 ppb when widened, while the corresponding background increment falls from +13.62 to +1.46 ppb. Because no prospective tolerance defines negligible change, these results describe stabilization tendencies rather than declaring convergence or atmospheric accuracy.

![Representative methane surface, endpoint-background and combined prior-budget responses by domain and duration.](outputs/hysplit/domain_budget_extension/figures/budget_convergence.png)

**Figure 28.** Prior methane-budget components for five pre-declared BKT receptor hours at 72, 120 and 168 hours backward. Thin lines are individual receptors and thick lines are cross-case medians; blue denotes the original domain and orange the widened domain. Surface contribution combines prior anthropogenic, wetland, termite, geological and non-crop-fire methane, less the positive soil-uptake magnitude [4, 5]. Background is the equal-particle mean CarbonTracker-CH4 value at active trajectory endpoints [9]. The sum can appear stable when its components offset, so the three panels must be read together. These representative cases were selected by clock period, model wind quadrant and original retention—not gas residual—and are not a random or seasonally representative sample.

**Table 23. Absolute duration increments across the five representative methane-budget cases.**

| Domain | Component | Absolute 72–120 h median (range), ppb | Absolute 120–168 h median (range), ppb | Later increment smaller |
| --- | --- | --- | --- | --- |
| Original | Surface | 12.79 (1.38–29.08) | 2.48 (0.13–15.93) | 5/5 |
| Original | Background | 13.63 (0.74–64.05) | 2.85 (1.76–15.64) | 4/5 |
| Original | Combined | 4.90 (0.64–34.97) | 2.99 (0.29–13.76) | 3/5 |
| Widened | Surface | 11.47 (1.44–29.47) | 1.27 (0.03–27.31) | 5/5 |
| Widened | Background | 12.14 (0.36–62.81) | 1.46 (1.26–27.02) | 4/5 |
| Widened | Combined | 2.95 (0.67–33.55) | 1.55 (0.29–2.53) | 4/5 |

CarbonTracker-CH4 assimilates BKT observations, so its endpoint mean is a physically informed boundary estimate rather than an independent test of the BKT record. The source fields are prior inventories or models, and the small convergence matrix tests numerical sensitivity only. Accordingly, this extension can identify domain truncation, selection effects and component instability; it cannot validate atmospheric accuracy, attribute measured methane to a source, or support a revised emissions inversion.

