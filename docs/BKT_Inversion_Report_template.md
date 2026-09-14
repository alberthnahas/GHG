# Regional methane emissions constrained by Bukit Kototabang: a transport-ensemble inversion for September–October 2019

## Scientific summary

Bukit Kototabang (BKT) observes methane at 865 m on the west coast of Sumatra. This report asks whether four weeks of its hourly record can scale regional methane emission priors when transport, boundary values and natural exchange are modeled explicitly. The inversion uses {{R_N}} twice-daily receptor hours between 9 September and 6 October 2019, {{R_TRAIN}} for fitting and {{R_TEST}} withheld before fitting, with five-day HYSPLIT-STILT footprints on a 50°–160° E, 40° S–30° N domain driven by quarter-degree Global Forecast System (GFS) meteorology, three seeds of 2,000 particles per hour, NOAA CarbonTracker-CH₄ boundary values at particle endpoints, and a positive-emission Bayesian fit of four regional multipliers.

The prior model, inventory plus modeled background, over-predicts the observations by {{R_GFS_PRIOR_BIAS}} ppb on average. With the working error covariance of the original design, which assigns half of every prior increment to transport error, the refit on the revised ensemble scales the four components to {{R_BASE_NEAR}}, {{R_BASE_FAR}}, {{R_BASE_WET}} and {{R_BASE_FIRE}} and predicts withheld hours to {{R_BASE_RMSE}} ppb RMSE, worse than a fitted background alone ({{R_BASE_BG_RMSE}} ppb). That covariance is inconsistent with the residuals: its training reduced chi-square is {{R_CHI_FIXED}}. Reducing the transport-error fraction to {{R_TUNED_FRACTION}}, where the reduced chi-square is one, gives multipliers of {{R_TUNED_NEAR}} for anthropogenic emissions within 500 km, {{R_TUNED_FAR}} beyond 500 km, {{R_TUNED_WET}} for wetlands and {{R_TUNED_FIRE}} for non-crop fires (posterior medians with 95% intervals), withheld RMSE {{R_TUNED_RMSE}} ppb against {{R_TUNED_BG_RMSE}} ppb for the background-only baseline, and a withheld bias of {{R_TUNED_BIAS}} ppb. {{R_TUNED_VERDICT}}

Repeating the ensemble with hourly ERA5 meteorology gives {{R_ERA5_N}} usable hours, a prior over-prediction of {{R_ERA5_PRIOR_BIAS}} ppb, multipliers of {{R_ERA5_NEAR}}, {{R_ERA5_FAR}}, {{R_ERA5_WET}} and {{R_ERA5_FIRE}} under its own consistent covariance, and withheld RMSE {{R_ERA5_RMSE}} ppb against {{R_ERA5_BG_RMSE}} ppb for background only. The downward scaling of every prior is robust to the driver; the ability to out-predict a fitted background is not. The estimates remain conditional on parameterized transport without resolved convection, on boundary fields that assimilate BKT, and on fixed within-region source patterns. They are regional adjustment factors under a stated error model, not independently verified emission totals.

## 1. Scientific question and scope

{{INVERSION_SCOPE}}

The design was executed twice. The original transport ensemble used one seed of 540 particles per receptor hour on a 75°–130° E, 20° S–20° N domain, from which 25 hours lost more than 5% of their particles across the boundary and were excluded. The revised ensemble, which supplies the principal results of this report, uses the widened domain, three seeds of 2,000 particles per hour, a second concentration layer to 1,000 m, and retains every particle at every hour. A third ensemble repeats the revised design with ERA5 meteorology. The original results are retained in Section 4.1 because the revision was designed to test them, not to replace them silently.

## 2. Evidence and data quality

### Methane observations, flasks and priors

Section 4.1 reports the observation coverage, the flask comparisons and the prior concentration budget in full, with the original transport ensemble; the same observations, priors and boundary fields feed the revised fits. The anthropogenic prior is the September and October 2019 EDGAR v8.0 monthly flux; wetlands are LPJ-EOSIM driven by MERRA-2; non-crop fires are daily GFED5.1 with agricultural burning removed to avoid double counting with EDGAR; termites, geological seepage and soil uptake are fixed auxiliary fields. Their provenance, unit conversions and known limitations are given in the methods; none is a contemporaneous measurement of the fluxes the receptor actually saw.

## 3. Methods

The original transport, boundary and inversion methods follow. The revised ensemble changes only the transport design and the error-model test described in the final subsection; priors, boundary sampling, the inverse state and the evaluation protocol are unchanged, so that differences in the results are attributable to transport and to the error model.

{{INVERSION_METHODS}}

### Revised transport ensemble, error-model consistency and driver sensitivity

Each of the {{R_N}} receptor hours was rerun for 120 h on the 50°–160° E, 40° S–30° N meteorological crop with a 60° by 100° footprint grid and three seeds of 2,000 requested particles. Coefficients are normalized to the actual emitted count and averaged across seeds; the seed spread supplies a direct estimate of finite-particle noise in every prior increment. All hours retain 100% of their particles at 120 h, so the 95% retention screen no longer removes any receptor. A fixed concentration layer to 1,000 m is recorded alongside the STILT surface layer for later injection-height tests; it is not used in the fit.

The working error covariance of the original design assigned 50% of each hour's total prior increment to correlated transport error. Whether that magnitude is consistent with the data is testable: at the posterior mode, the whitened data residuals of a consistent Gaussian model have a reduced chi-square near one. The transport fraction was therefore scanned from 0.05 to 1.0 with all other covariance terms fixed, and the fraction at which the training reduced chi-square equals one was adopted as the tuned covariance. Because the fraction is chosen on the fitting hours, the withheld evaluation remains the independent test of the tuned fit. A five-component variant splits the within-500 km anthropogenic term at 50 km, to expose how much of the near-region constraint rests on the few inventory cells around the station.

The ERA5 ensemble repeats the revised design with hourly ECMWF ERA5 pressure-level meteorology (16 levels, 70°–140° E, 25° S–20° N) converted to HYSPLIT format with the ECMWF turbulent heat fluxes mapped to HYSPLIT's upward-positive convention; the ERA5 footprint grid is 40° by 60°. Its operator, covariance scan and fits use the same code path.

## 4. Results

### 4.1 Results with the original transport ensemble

{{INVERSION_RESULTS_DEMOTED}}

### 4.2 The revised transport ensemble

The revised ensemble changes the operator in two ways. First, it restores the {{R_RESTORED}} receptor hours that the original domain had excluded, so the fit uses {{R_N}} hours instead of {{I_N}}; the restored hours are mostly in October and carry lower methane. Second, it removes numerical noise: the seed standard deviation of the prior increment is {{R_SEED_NEAR_SD}} ppb for the near anthropogenic term and {{R_SEED_FAR_SD}} ppb for the far term (medians over receptors), against seed-induced changes of up to {{R_OLD_SEED_MAX}}% in the original single-seed anchors. The prior over-prediction is essentially unchanged at {{R_GFS_PRIOR_BIAS}} ppb. Transport noise was not the reason the original inversion could not separate sources from background.

{{R_BASE_TABLE}}

Refitting with the original 50% covariance moves the multipliers little (Table 101). The withheld RMSE of the inversion falls to {{R_BASE_RMSE}} ppb, but so does every baseline, and the fitted background alone still predicts the {{R_TEST}} withheld hours better ({{R_BASE_BG_RMSE}} ppb). More hours and less noise do not, by themselves, give the observations more say.

### 4.3 Error-model consistency and the tuned fit

The reason is the error model. With the 50% transport fraction the training reduced chi-square at the posterior mode is {{R_CHI_FIXED}}: the covariance is about four times too large in variance, the likelihood is correspondingly weak, and the posterior stays close to the prior. Figure 101 shows the scan; the reduced chi-square reaches one at a transport fraction of {{R_TUNED_FRACTION}} under GFS.

![Error-model consistency and posterior intervals.]({{RFIGURES}}/figure_R05_inversion_update.png)

**Figure 101.** Training reduced chi-square against the transport-error fraction for the GFS and ERA5 ensembles (a), and posterior medians with 95% credible intervals for the published fit, the revised ensemble with the fixed covariance, the revised ensemble with the tuned covariance, the ERA5 ensemble with its tuned covariance, and the near-field split (b).

{{R_TUNED_TABLE}}

With the tuned covariance the posterior moves decisively away from the prior (Table 102). Anthropogenic emissions within 500 km scale to {{R_TUNED_NEAR}}, those beyond 500 km to {{R_TUNED_FAR}}, wetlands to {{R_TUNED_WET}} and non-crop fires to {{R_TUNED_FIRE}}. {{R_TUNED_VERDICT}} The withheld RMSE is {{R_TUNED_RMSE}} ppb against {{R_TUNED_BG_RMSE}} ppb for the background-only baseline and {{R_TUNED_ADJ_RMSE}} ppb for the inventory with a fitted background, and the withheld bias is {{R_TUNED_BIAS}} ppb. The tuned fit is the first configuration in this study in which source scaling adds predictive value over a fitted background on hours the fit never saw.

![Tuned fit and withheld evaluation.]({{RFIGURES}}/figure_R06_withheld_evaluation.png)

**Figure 102.** Observed methane and the tuned GFS posterior with its 95% model-mean interval at all {{R_N}} receptor hours, withheld hours marked (a), and withheld RMSE by model for the published fit, the revised GFS ensemble and the ERA5 ensemble (b).

{{R_EVAL_TABLE}}

### 4.4 The near field

Splitting the within-500 km term at 50 km gives {{R_NEAR50}} for the cells within 50 km of the station and {{R_50_500}} for the 50–500 km ring, with the far, wetland and fire terms essentially unchanged and the withheld RMSE {{R_NEAR_RMSE}} ppb. The within-50 km interval includes unity: the cells that dominate the near-region prior are the ones the observations constrain least, because a single receptor cannot distinguish a local source from a local transport error. The regional downward scaling rests on the 50–500 km ring and on the far term, not on the receptor cells.

### 4.5 Sensitivity to the meteorological driver

Under ERA5 meteorology the prior over-prediction grows to {{R_ERA5_PRIOR_BIAS}} ppb, because ERA5's shallower daytime boundary layer at BKT and its hourly winds put {{F_ERA5_RATIO_MIN}} to {{F_ERA5_RATIO_MAX}} times the GFS sensitivity at the surface (companion report), and {{R_ERA5_EXCLUDED}} hours lose more than 5% of their particles on the smaller ERA5 domain. Its consistent transport fraction is {{R_ERA5_FRACTION}}, twice the GFS value. The tuned ERA5 multipliers, {{R_ERA5_NEAR}}, {{R_ERA5_FAR}}, {{R_ERA5_WET}} and {{R_ERA5_FIRE}}, overlap the GFS intervals almost entirely, so the conclusion that every prior is too high by a factor of two to four does not depend on the driver. The predictive result does: the tuned ERA5 fit has withheld RMSE {{R_ERA5_RMSE}} ppb against {{R_ERA5_BG_RMSE}} ppb for background only and a withheld bias of {{R_ERA5_BIAS}} ppb.

{{R_ERA5_TABLE}}

The two drivers therefore bracket what a single station can deliver. Their disagreement in surface sensitivity, a factor of {{F_ERA5_RATIO_MIN}} to {{F_ERA5_RATIO_MAX}} at matched receptors with seed noise below 2%, is the transport uncertainty that the covariance must represent, and it is larger than the interval width of either posterior.

### 4.6 Conditional regional totals

{{R_BUDGET_TABLE}}

Applying the tuned GFS multipliers to the fixed prior patterns gives the 28-day totals in Table 105. They inherit the prior's spatial allocation within each region and the 50°–160° E domain of the far term; only {{R_FAR_SUPPORT}}% of the distant anthropogenic prior mass lies in cells that carry 90% of the aggregate sensitivity, so extending its multiplier to the whole distant region is a prior-pattern extrapolation. Sector shares within each region are inherited from EDGAR and are not separately retrieved.

## 5. Discussion

Three results carry the scientific weight. First, the prior model over-predicts methane at BKT by {{R_GFS_PRIOR_BIAS}} ppb under GFS and {{R_ERA5_PRIOR_BIAS}} ppb under ERA5, with numerical noise below 1 ppb in the near term. Second, once the error model is made consistent with the residuals, the observations scale every component down by a factor of two to four with intervals that exclude the inventory value for the anthropogenic and wetland terms and reach it for fires, and this holds under both drivers. Third, only under GFS does the scaled model out-predict a fitted background on withheld hours.

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

{{INVERSION_REFERENCES}}

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

{{INVERSION_APPENDIX}}

### Synthetic recovery on the revised ensemble

{{R_RECOVERY_TABLE}}

The synthetic tests use the revised response matrix with the fixed 50% covariance, known multipliers of 1.5, 0.7, 1.2 and 0.6, and 200 correlated-noise realizations per scenario, as in the original design. They test recoverability under the assumed model and under coherent 30% source-response perturbations with an unmodeled 15 ppb boundary signal; they are not validation of the real estimates.

**Table 107. Terms used in this report.**

| Term | Meaning |
|---|---|
| Prior increment | Modeled methane enhancement from one source component with its multiplier at unity |
| Emission multiplier | Dimensionless factor applied to a fixed prior pattern; unity reproduces the inventory |
| Reduced chi-square | Mean squared whitened residual at the posterior mode; one indicates a covariance consistent with the residuals |
| Transport-error fraction | Share of each hour's prior increment treated as correlated transport error in the working covariance |
| Withheld hours | Receptor hours designated before fitting and never used by the optimizer |
| Credible interval | Equal-tailed posterior probability interval, conditional on the model and priors |
