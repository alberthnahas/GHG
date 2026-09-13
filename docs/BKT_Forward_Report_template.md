# Greenhouse-gas source influence at Bukit Kototabang: the 26 September 2019 case

## Scientific summary

Atmospheric transport connects the Bukit Kototabang (BKT) greenhouse-gas record to spatially distributed surface exchange across Sumatra and its surroundings. For the receptor record timestamped 26 September 2019 at 01:00 UTC (08:00 Western Indonesian Time, WIB), the observations are {{OBS_CO2}} ppm carbon dioxide (CO₂), {{OBS_CH4}} ppb methane (CH₄), and {{OBS_CO}} ppb carbon monoxide (CO). These are measured mole fractions, not source-specific enhancements.

A three-member HYSPLIT-STILT ensemble driven by quarter-degree Global Forecast System (GFS) meteorology assigns {{GFS_SE}}% of its 72-hour surface-flux sensitivity to the southeast sector beyond 25 km from BKT and {{GFS_NEAR}}% to the area within 25 km. The sensitivity-weighted median source distance is {{GFS_DISTANCE}} km and median backward age is {{GFS_LAG}} h. Relative to a matched one-degree Global Data Assimilation System (GDAS) ensemble, integrated sensitivity changes by {{TOTAL_CHANGE}}%, and the normalized regional spatial distributions differ by {{SHAPE_TV}}% total variation on a common one-degree grid. These are meteorological-driver sensitivities, not estimates of predictive accuracy.

Convolution with September 2019 anthropogenic fluxes from the Emissions Database for Global Atmospheric Research (EDGAR v8.0) gives surface-release-equivalent enhancements of {{ANTH_CO2}} ppm CO₂ and {{ANTH_CH4}} ppb CH₄ under GFS transport. The largest modeled sector contributions are {{TOP_CO2}} for CO₂ and {{TOP_CH4}} for CH₄. Separately, daily Global Fire Emissions Database (GFED5.1) fluxes give {{FIRE_CO2}} ppm CO₂, {{FIRE_CH4}} ppb CH₄ and {{FIRE_CO}} ppb CO in a surface-release fire scenario. These estimates are inventory-conditioned model results, not measured contributions or emission inversions.

{{CO_BUDGET_NOTICE}}


Extending the same receptor hour to five days on a widened domain, with 10,020 particles per member, raises the integrated surface sensitivity from {{F_OLD_TOTAL}} to {{F_NEW_TOTAL}} ppm per (µmol m⁻² s⁻¹) with no sensitivity left on the domain edge, and {{F_NEW_OLDEST24}}% of it arriving in the oldest 24 h. The anthropogenic enhancements are unchanged within {{F_ANTH_CHANGE_CH4}}% for CH₄ and {{F_ANTH_CHANGE_CO2}}% for CO₂, whereas the methane fire enhancement rises by {{F_FIRE_CH4_GAIN}}%. The same case under hourly ERA5 meteorology gives {{F_ERA5_RATIO}} times the GFS sensitivity, and its fire-CO lower bound alone reaches {{F_FIRE_CO_LOWER_ERA5}}% of the observed CO. The surface-release fire scenario is therefore incompatible with the observation under either driver once the full five-day influence is counted; the driver difference is the dominant transport uncertainty.

The principal implication is that source interpretation at BKT must account jointly for transport, source distribution and emission timing. Meteorological representation, unresolved mountain circulation, vertical release assumptions, ecosystem exchange and background concentrations remain material uncertainties. The analysis does not establish a complete concentration budget, responsibility of an individual facility, or operational model skill.

## 1. Scientific question and scope

This study asks which surface regions and source categories could contribute to a selected BKT observation, how that inference depends on the meteorological driver, and which uncertainties prevent stronger attribution. The approach combines a backward particle-transport calculation with independently compiled emission inventories. A footprint is a sensitivity of receptor mole fraction to surface flux; an emission inventory estimates the flux itself. Their product estimates a contribution conditional on both datasets and the model assumptions [1, 2].

BKT is a mountain receptor at 0.202° S, 100.318° E, with station elevation 864.5 m above mean sea level. The inlet is represented at 30 m above local model ground. This distinction matters because model terrain is a spatial average, while an inlet samples a particular site. A separate 60 m release scenario tests height dependence; it does not represent a second observed inlet.

The case is an exploratory, single-hour source-influence study, selected from the available simultaneous gas observations. It is not a randomly sampled evaluation period or a regional climatology. The integration covers 23 September 01:00 to 26 September 01:00 UTC, with hourly source intervals. Sources older than this window and air entering from outside it are not represented by the footprint. Conclusions therefore apply to this receptor hour and experimental design.

The forward case's quantitative source influence is restricted to an output domain spanning approximately 85.27°–115.37° E and 10.25° S–9.85° N. Transport uses the larger meteorological domain, but source sensitivities outside the output domain are not retained. Its enhancements and spatial percentages refer to this bounded regional domain; external contributions are unrepresented, not assumed to be zero. A second configuration extends the same receptor hour to 120 h on a 50°–160° E, 40° S–30° N meteorological domain and a 60° by 100° footprint grid, so that the truncation of the 72 h regional case can be quantified rather than assumed small.

## 2. Evidence and data quality

### Meteorological representation

The GFS archive contains quarter-degree meteorological fields at three-hour intervals on 55 hybrid sigma-pressure levels. It concatenates analysis-time and three-hour forecast fields from successive six-hour model cycles; it is a pseudo-analysis rather than a homogeneous retrospective reanalysis [3]. The regional domain extends from 75° to 130° E and 20° S to 20° N, retaining the native horizontal spacing and all available levels. The comparison uses the GDAS one-degree, three-hourly archive with otherwise matched receptor and transport settings.

At the nearest native grid points, GFS terrain is {{GFS_TERRAIN}} m and GDAS terrain is {{GDAS_TERRAIN}} m. GFS therefore represents the station elevation more closely at those points. This comparison does not quantify the terrain interpolation seen by every particle or prove that the finer driver captures local slope and valley winds. Figure 1 places the difference in the context of near-surface winds and native meteorological boundary-layer height.

![Meteorological context near BKT.]({{FIGURES}}/figure_01_meteorology.png)

**Figure 1.** Three-hourly GFS and GDAS meteorological output at the nearest native grid points to BKT over the transport period and its interpolation brackets in September 2019. Panels show native planetary boundary-layer height (m), eastward wind and northward wind (m s⁻¹). Positive wind components point east and north. The native boundary-layer field is diagnostic context: the STILT configuration used here estimates mixing depth from a modified Richardson number rather than directly prescribing this plotted height.

### Receptor measurements

Observations are expressed as dry-air mole fractions: parts per million (ppm) for CO₂ and parts per billion (ppb) for CH₄ and CO. Processing uses UTC consistently; WIB is UTC+7. The selected record passes the available species-specific quality screens. Each gas has {{VALID_HOURS}} valid hours out of {{EXPECTED_HOURS}} expected hours in the symmetric seven-day context on either side of the receptor hour. Missing or flagged measurements are excluded from descriptive statistics and remain visible as gaps.

![BKT gas observations around the receptor hour.]({{FIGURES}}/figure_02_observation_context.png)

**Figure 2.** Hourly BKT CO₂, CH₄ and CO over the seven days before and after 26 September 2019 01:00 UTC. Orange points identify the receptor values, shading marks the backward integration window, and dashed lines show context medians. No interpolation fills measurement gaps. Units are ppm for CO₂ and ppb for CH₄ and CO.

**Table 1. Receptor observations and temporal context.** Context medians and percentile ranks describe the surrounding valid-hour sample. They are not estimates of background concentration, measurement uncertainty or source contribution.

{{OBS_TABLE}}

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

The Hybrid Single-Particle Lagrangian Integrated Trajectory model (HYSPLIT 5.4.2) is configured for Stochastic Time-Inverted Lagrangian Transport (STILT). Particles are released backward over the hour immediately preceding the receptor timestamp. The principal estimate is the arithmetic mean of three distinct seeded runs, each with {{PARTICLES}} emitted particles. A common 0.1° accumulation grid samples particle residence; it is not a claim of 0.1° meteorological resolution.

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

All analysis uses unsmoothed coefficients. Maps show continuous, linearly reconstructed surfaces, with sensitivity divided by cell area where a density is displayed. The footprint's Gaussian display width is selected by leaving one seed out and testing the other two against its unsmoothed field. The selected width is {{SIGMA}} native cells. Linear interpolation is performed before logarithmic color mapping, preserves nonnegativity, and is renormalized to preserve the full-domain sensitivity integral. It changes display representation, not meteorological resolution or the inventory convolution.

For the principal footprint map, {{HIDDEN}}% of the display integral is below the plotted color range and {{OUTSIDE}}% is outside the frame. Unthresholded coefficients remain the basis of every table. Continuous contours do not imply precisely known footprint edges. The numerical checks assess conservation, time coverage, unit conversions and seed variability; they are not independent atmospheric validation.

The GFS ensemble retains {{GFS_EDGE}}% of its regional sensitivity in the outermost output-grid cells, at the eastern boundary. The footprint therefore has a truncated eastern tail. This edge share is not an upper bound on sensitivity or emissions beyond the domain. A wider-domain experiment is necessary before claiming complete regional source capture; the present convolution remains a contribution estimate for the stated bounded domain.

The selected regional inventory arrays contain no missing cells. Uncolored inventory areas indicate zero or values below the displayed positive range, not missing data; low values remain in the convolution. Logarithmic scales reveal spatial variation across orders of magnitude and are not used to transform the flux values themselves.

## 4. Results

### Regional footprint and dependence on meteorology

The GFS ensemble has integrated sensitivity {{GFS_TOTAL}} ppm per (µmol m⁻² s⁻¹). Its median influence distance is {{GFS_DISTANCE}} km, and {{GFS_WITHIN250}}% of sensitivity lies within 250 km. The southeast share beyond 25 km is {{GFS_SE}}%, with a three-seed range of {{GFS_SE_MIN}}–{{GFS_SE_MAX}}%. Near-receptor sensitivity remains important: {{GFS_NEAR}}% lies within 25 km, where unresolved site circulation is particularly relevant.

**Table 3. Transport diagnostics for matched ensembles.** Integrated sensitivity is in ppm per (µmol m⁻² s⁻¹). Distance and age are sensitivity-weighted, not particle-count medians. Percentages refer to the full modeled footprint.

{{TRANSPORT_TABLE}}

![GFS ensemble footprint at BKT.]({{FIGURES}}/figure_03_footprint.png)

**Figure 3.** Ensemble-mean 72-hour GFS-driven BKT surface-flux footprint ending on 26 September 2019 at 01:00 UTC. Colors show time-integrated sensitivity density in ppm per (µmol m⁻² s⁻¹) per km² on a logarithmic scale. The star marks the 30 m AGL receptor. The continuous display uses linear interpolation and the stated cross-seed-selected kernel; numerical summaries and flux convolution use the unsmoothed field. Ocean sensitivity is retained because atmospheric transport is not confined to land.

The GDAS ensemble gives {{GDAS_TOTAL}} integrated sensitivity, compared with {{GFS_TOTAL}} under GFS. The {{SHAPE_TV}}% regional total-variation difference describes redistribution after normalizing each field to unit sum on a common one-degree grid. It separates a change in geographic pattern from the {{TOTAL_CHANGE}}% change in overall sensitivity. Neither metric identifies which driver is closer to the true atmospheric transport.

![Matched meteorological-driver comparison.]({{FIGURES}}/figure_04_driver_maps.png)

**Figure 4.** GDAS- and GFS-driven ensemble footprints for the same BKT receptor and 72-hour window. Both panels show sensitivity density with identical geographic extent and logarithmic color limits, and linear display reconstruction without an additional Gaussian kernel. Meteorological model, native grid and vertical representation differ; all receptor and particle settings are matched.

The mapped contrast is spatial as well as numerical. GDAS concentrates its strongest regional sensitivity over southern Sumatra, while GFS produces more extended eastward and northeastward branches over surrounding seas in addition to its Sumatran influence. The larger GFS sensitivity-weighted distance in Table 3 is consistent with that pattern. A weak but extensive branch can increase the distance distribution without supplying a correspondingly large anthropogenic contribution, because the flux field is highly nonuniform.

### Transport age and robustness

Half the GFS sensitivity accumulates within {{GFS_LAG}} h backward and 90% within {{GFS_P90LAG}} h. The earliest and latest source intervals contribute unequally. Consequently, an emission inventory averaged over the entire window can yield a different enhancement from a temporally resolved inventory even when its total emissions are similar.

![Transport distance and age.]({{FIGURES}}/figure_05_lag_distance.png)

**Figure 5.** Cumulative shares of unsmoothed ensemble sensitivity by backward lag (h) and great-circle distance (km) for GFS and GDAS. The horizontal reference marks 50%. Curves refer to the finite 72-hour experiment; the distance panel displays the first 1,000 km, not necessarily the whole support.

The GFS 60 m release changes integrated sensitivity by {{HEIGHT_CHANGE}}% relative to the 30 m run with the same seed. The three 30 m seeds span {{GFS_TOTAL_MIN}}–{{GFS_TOTAL_MAX}} in integrated sensitivity. This comparison separates a release-height scenario from stochastic sampling. It does not cover uncertainty in mixing-depth parameterization, meteorological winds or measurement representativeness.

![Seed and release-height sensitivity.]({{FIGURES}}/figure_06_robustness.png)

**Figure 6.** Integrated sensitivity and southeast sensitivity beyond 25 km for the two meteorological drivers. Blue points show three seeds at 30 m AGL; orange diamonds show the paired 60 m scenario. All runs use the same emitted-particle normalization. The spread is an experimental range, not a confidence interval.

### Anthropogenic source sectors

Under the EDGAR/GFS surface-release assumptions, the modeled CO₂ enhancement is {{ANTH_CO2}} ppm and CH₄ enhancement is {{ANTH_CH4}} ppb. Sector ordering is gas-specific: {{TOP_CO2}} supplies the largest CO₂ contribution, while {{TOP_CH4}} supplies the largest CH₄ contribution. A large source outside sensitive transport regions can contribute less than a smaller source close to, or strongly connected with, the receptor.

The leading sectors account for {{TOP_SHARE_CO2}}% of the modeled anthropogenic CO₂ contribution and {{TOP_SHARE_CH4}}% of CH₄, respectively. These shares describe this receptor's inventory-weighted mixture, not the composition of Indonesian national emissions. In particular, a broad transport-sector aggregate does not identify a specific road, vessel or aircraft source.

Using the same flux inventory with GDAS instead gives {{ANTH_GDAS_CO2}} ppm CO₂ and {{ANTH_GDAS_CH4}} ppb CH₄. The GFS values differ by {{ANTH_DRIVER_CO2}}% and {{ANTH_DRIVER_CH4}}%, respectively. These gas-specific changes reflect both overall sensitivity and its relocation relative to the source fields. Within GFS, raising the receptor from 30 to 60 m changes the paired-seed anthropogenic CO₂ and CH₄ contributions by {{ANTH_HEIGHT_CO2}}% and {{ANTH_HEIGHT_CH4}}%. Driver and height dependence therefore need evaluation at the source-contribution level, not only through total footprint sensitivity.

**Table 4. GFS-driven anthropogenic sector contributions.** Values are three-seed means; ranges describe numerical seed variability only. Each gas uses its own unit. Sector estimates assume surface release and September-mean activity.

{{SECTOR_TABLE}}

![Anthropogenic sector contributions.]({{FIGURES}}/figure_07_sectors.png)

**Figure 7.** EDGAR v8.0 sector-weighted enhancements at BKT for the receptor hour, using September 2019 monthly fluxes and three GFS footprints. Bars show means and whiskers show minimum–maximum seed values. Scales differ between CO₂ (ppm) and CH₄ (ppb). These are conditional model contributions, not emissions inferred from the observations.

![Regional anthropogenic inventories.]({{FIGURES}}/figure_08_inventory.png)

**Figure 8.** September 2019 EDGAR anthropogenic CO₂ and CH₄ flux densities around Sumatra, conservatively matched to the analysis grid and summed across the eight sector groups. Units are µmol m⁻² s⁻¹, with gas-specific logarithmic scales. Spatial gradients reflect inventory allocation, not local measurements.

![Anthropogenic source-weighted influence.]({{FIGURES}}/figure_09_source_influence.png)

**Figure 9.** Geographic distribution of EDGAR-weighted GFS contributions to the selected BKT hour. Displayed contribution densities are ppm CO₂ km⁻² and ppb CH₄ km⁻². The maps combine flux magnitude with transport sensitivity; they are distinct from both the inventory maps and the transport-only footprint. Linear display reconstruction is not used for quantitative aggregation.

### Provincial source geography

The largest modeled Indonesian provincial contribution is {{PROV_CO2}} for anthropogenic CO₂ and {{PROV_CH4}} for anthropogenic CH₄. Table 5 summarizes the largest contributors within each gas. Provincial ranking describes the overlap of inventory flux and transport sensitivity. It is not a ranking of provincial total emissions, mitigation performance, or legally attributable responsibility.

Overlapping boundary claims account for {{AMBIGUOUS_CO2}}% of the full-domain anthropogenic CO₂ contribution and {{AMBIGUOUS_CH4}}% of CH₄. These portions are left unassigned, independently of offshore and foreign contributions. The map retains the supplied geometry; quantitative totals do not count overlapping areas twice.

**Table 5. Largest Indonesian provincial anthropogenic contributions.** Five leading provinces are reported for each gas. Values use fractional boundary overlap; offshore, foreign and multiply claimed areas are not reassigned to a province.

{{PROVINCE_TABLE}}

![Provincial source contributions.]({{FIGURES}}/figure_10_provinces.png)

**Figure 10.** Eight largest Indonesian provincial EDGAR-weighted contributions under the GFS ensemble for the selected receptor hour. Current detailed provincial geometry supplies geographic context. Fractional overlap is calculated in equal-area coordinates; scales differ for CO₂ and CH₄.

### Landscape-fire influence and emission timing

The GFED/GFS surface-release scenario produces {{FIRE_CO2}} ppm CO₂, {{FIRE_CH4}} ppb CH₄ and {{FIRE_CO}} ppb CO. These are modeled fire contributions over the source window, conditional on the daily inventory and transport. The CO observation provides useful combustion context, but co-elevation of CO and greenhouse gases alone cannot distinguish landscape fires from other combustion sources.

{{CO_COMPATIBILITY}}

The GFS fire scenario is equivalent to {{GFS_FIRE_CO_PERCENT}}% of measured CO and leaves only {{GFS_CO_REMAINDER}} ppb for background and other passive CO contributions. This remainder is a conditional budget residual, not an independent background estimate. Under GDAS, fire-only CO reaches {{GDAS_FIRE_CO}} ppb and exceeds the {{OBS_CO}} ppb total observation. With passive transport and nonnegative background, the GDAS fire scenario cannot form a consistent concentration budget. Emission magnitude, vertical injection, transport and neglected chemical loss are competing explanations; the comparison does not establish that GFS is correct.

**Table 6. Fire scenarios and meteorological dependence.** Entries are seed means and ranges. Fire emissions are not combined with EDGAR in this table because source overlap and differing release assumptions must be resolved before constructing a joint budget.

{{FIRE_TABLE}}

![Landscape-fire source influence.]({{FIGURES}}/figure_11_fire_map.png)

**Figure 11.** GFED5.1 daily fire emissions weighted by the GFS ensemble footprint for 23–26 September 2019. Contribution density uses ppm CO₂ km⁻² or ppb CH₄ km⁻² and gas-specific logarithmic scales. The calculation treats fire emissions as a surface flux distributed uniformly over each UTC day; plume injection and sub-daily fire behavior are unresolved.

![Timing of modeled fire contributions.]({{FIGURES}}/figure_12_fire_timing.png)

**Figure 12.** GFS/GFED contributions grouped by source date for CO₂, CH₄ and CO. The 72 hourly source intervals contain 23 hours on 23 September, 24 hours on each of 24 and 25 September, and one hour on 26 September. Bar heights combine these unequal sampled durations, daily emissions and transport sensitivity; they are not daily regional emission totals.

Replacing daily variation with each cell's mean flux across the 72 sampled hours changes the GFS CO₂ fire contribution by {{FIRE_TIME_CHANGE}}%. This is a timing sensitivity within the available window, not an inventory uncertainty interval. It demonstrates how temporal allocation can affect source influence without changing the transport field.

Source hours on 23 September supply {{FIRE_FIRST_DAY_SHARE}}% of the modeled fire CO₂ increment. The fire-weighted influence is therefore concentrated near the older end of the experiment, even though the transport-only median age is {{GFS_LAG}} h. This distinction makes the backward-window length particularly consequential for the fire scenario; the extended case below quantifies it.

### Extended five-day case and meteorological-driver sensitivity

The published 72 h regional configuration truncates influence in two ways: sources older than three days are not represented, and sensitivity carried beyond the regional output grid is lost. Rerunning the same receptor hour for 120 h on the widened domain, with three seeds of 10,020 particles each, resolves both. Integrated surface sensitivity rises from {{F_OLD_TOTAL}} to {{F_NEW_TOTAL}} ({{F_NEW_GAIN_PERCENT}}%), {{F_NEW_OLDEST24}}% of the five-day total arrives in the oldest 24 h, and {{F_EDGE}}% lies on the outermost cells. The near field loses relative weight: {{F_NEW_NEAR25}}% of sensitivity now lies within 25 km, against {{F_OLD_NEAR25}}% in the 72 h case. Seed spread is {{F_SEED_CV}}% of the total. Raising the release to 80 m, which places the inlet at its true altitude above the nearest GFS grid-cell terrain, changes the total by {{F_H80_CHANGE}}%.

{{F_TRANSPORT_TABLE}}

![Extended forward case.]({{RFIGURES}}/figure_R03_forward_extension.png)

**Figure 101.** Cumulative surface sensitivity by backward lag and by distance for the published 72 h regional case, the 120 h widened GFS case and the 120 h ERA5 case, with the GFS surface-layer and 1,000 m-layer fields. The upper layer gives the receptor response to a unit flux released uniformly into that layer, the quantity needed for elevated fire injection.

The same footprints were convolved with the inventories. Anthropogenic enhancements change by {{F_ANTH_CHANGE_CO2}}% for CO₂ and {{F_ANTH_CHANGE_CH4}}% for CH₄, because the added sensitivity falls mostly over sea and sparsely emitting land. Methane fire rises by {{F_FIRE_CH4_GAIN}}% to {{F_FIRE_CH4_NEW}} ppb with the complete wide-grid fire field. Daily CO₂ and CO fire fields are held locally only for 23–26 September on the regional box, so for those two gases the extended case yields lower bounds that equal the 72 h values; scaling by the methane gain would put GFS fire CO near {{F_FIRE_CO_SCALED_GFS}} ppb against the observed {{OBS_CO}} ppb. Emission into the 1,000 m layer multiplies every contribution by about {{F_LAYER_RATIO}}, so an elevated fire injection does not relieve the over-closure; it deepens it.

{{F_SOURCE_TABLE}}

Under hourly ERA5 meteorology the five-day sensitivity is {{F_ERA5_RATIO}} times the GFS value and the footprint is placed in largely different cells ({{F_ERA5_SPATIAL}}% cell-level absolute difference). Its methane fire enhancement is {{F_FIRE_CH4_ERA5}} ppb and its fire-CO lower bound {{F_FIRE_CO_LOWER_ERA5}}% of the observation. Across the four inversion anchors and this case, ERA5 gives {{F_ERA5_RATIO_MIN}} to {{F_ERA5_RATIO_MAX}} times the GFS sensitivity with seed spread below 2%, a structural difference traceable to ERA5's shallower midday boundary layer at BKT and its hourly winds; which driver is closer to the atmosphere is not established by this comparison.

![Driver comparison.]({{RFIGURES}}/figure_R04_driver_maps.png)

**Figure 102.** GFS and ERA5 five-day footprints for the 9 September 2019 06:00 UTC anchor (three-seed means) and the ERA5 to GFS sensitivity ratio at the four anchors and the forward case.

## 5. Discussion and uncertainty

The footprint and source-weighted calculations provide complementary evidence. Transport-only sensitivity identifies where surface exchange can efficiently affect the receptor. Inventory-weighted contributions identify where a specified flux estimate intersects that sensitivity. The gas-specific sector and geographic differences follow from this interaction and should not be read directly from the most intensely colored footprint cells.

The GDAS comparison cannot be reduced to a uniform change in dilution: the {{TOTAL_CHANGE}}% change in integrated sensitivity differs from the {{ANTH_DRIVER_CO2}}% and {{ANTH_DRIVER_CH4}}% changes in anthropogenic CO₂ and CH₄. Within this experiment, redistribution relative to the source fields therefore materially affects the modeled mixture. The result supports evaluating transport and inventory alignment jointly, rather than selecting meteorology solely because its grid is finer or its total sensitivity is similar.

The ERA5 comparison sharpens the same point: two operational-quality drivers on the same receptor and settings differ by a factor of {{F_ERA5_RATIO_MIN}} to {{F_ERA5_RATIO_MAX}} in surface sensitivity and place the footprint in different cells, so single-driver enhancements carry at least that much transport uncertainty. The closer GFS grid-point elevation to BKT offers a physically relevant reason to examine its performance. However, mountain representativeness also depends on wind direction, vertical shear, stability, convective exchange and the relationship between the inlet and modeled terrain. No independent winds, boundary-layer observations or concentration enhancement series were used to establish that either meteorological driver is superior. Small seed spread cannot compensate for shared meteorological bias [8].


A complete mole-fraction budget would require

$$
c_g(t_r)=c_{g,\mathrm{background}}(t_r)+\Delta c_{g,\mathrm{anthropogenic}}+\Delta c_{g,\mathrm{fire}}+\Delta c_{g,\mathrm{ecosystem}}+\Delta c_{g,\mathrm{other}}.
$$

The background term represents air not accounted for by the modeled regional exchange window. The ecosystem term includes net photosynthesis and respiration for CO₂, and natural methane exchange where applicable. These terms are absent from the single-hour forward case; the companion methane-inversion report supplies modeled boundary methane and natural exchange for the multi-week experiment. Subtracting only the partial forward-inventory contributions from the observed mole fraction would not establish a measured background. Comparing that partial sum directly with the absolute observation would likewise not produce a meaningful validation error.

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

<!-- pdf-pagebreak -->

## 6. Conclusions

For the selected BKT observation, the GFS-driven footprint quantifies the distribution of surface-flux sensitivity in space and backward time. Matched GDAS calculations show that the result depends materially on the meteorological representation, while seeded and height experiments characterize narrower components of numerical and receptor uncertainty.

EDGAR and GFED provide explicit, gas-specific source scenarios. The anthropogenic sector and provincial rankings are conditional on inventory fluxes and modeled transport, and daily fire allocation changes the predicted influence. These products go beyond a pathway map, but do not constitute observational source attribution or a closed atmospheric greenhouse-gas budget.

The five-day widened configuration shows that the 72 h regional case understated fire influence: the methane fire enhancement rises by {{F_FIRE_CH4_GAIN}}%, and the surface-release fire-CO scenario exceeds the observed CO under GFS by the same scaling and under ERA5 even on a lower bound. Elevated injection worsens rather than relieves this. The fire inventory, its vertical release, or the transport must therefore be wrong in a way that a single receptor hour cannot resolve. The ERA5 and GFS drivers differ by a factor of {{F_ERA5_RATIO_MIN}} to {{F_ERA5_RATIO_MAX}} in surface sensitivity; that spread, not the seed spread, is the transport uncertainty to carry forward.


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

9. Hersbach, H., et al. (2020). The ERA5 global reanalysis. *Quarterly Journal of the Royal Meteorological Society*, 146, 1999–2049. [doi:10.1002/qj.3803](https://doi.org/10.1002/qj.3803).
10. Stein, A. F., et al. (2015). NOAA's HYSPLIT atmospheric transport and dispersion modeling system. *Bulletin of the American Meteorological Society*, 96, 2059–2077. [doi:10.1175/BAMS-D-14-00110.1](https://doi.org/10.1175/BAMS-D-14-00110.1).

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

{{WORKED_TABLE}}

<!-- pdf-pagebreak -->
