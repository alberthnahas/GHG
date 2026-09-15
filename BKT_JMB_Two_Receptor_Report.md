# Methane emissions seen from two Sumatran towers: Bukit Kototabang and Jambi, November–December 2023

## Scientific summary

Bukit Kototabang (BKT) observes methane at 865 m in the highlands of western Sumatra; Jambi observes it on the eastern Sumatran lowland at 25 m above sea level. This report asks whether the two records, inverted together, constrain the same regional methane emissions, and what a lowland tower adds to a highland one. The only window in which both towers have valid methane and every model input exists for its own year is 24 November to 31 December 2023. It gives 49 joint twice-daily receptor hours, of which 12 fall on withheld days. Both inlets are taken at 100 m above ground. The transport operator comes from 294 five-day HYSPLIT-STILT runs driven by quarter-degree GFS meteorology, three seeds of 2,000 particles at every receptor hour.

The Jambi night record cannot be used as it stands. At 18 UTC (01 WIB) the observed enhancement at Jambi averages 220 ± 111 ppb under a model mixing depth of 39 m, and fitting those hours drives the transport-error fraction to its cap of 1.00, which returns every multiplier toward the prior. With Jambi 18 UTC hours excluded, the joint fit scales anthropogenic emissions within 500 km of either tower to 0.29 (0.12–0.56), those beyond 500 km to 0.56 (0.21–1.12) and wetlands to 0.40 (0.16–0.76) (posterior medians with 95% intervals). Separating the EDGAR fuel-exploitation sector gives 0.32 (0.12–0.63) for fuel exploitation and 0.48 (0.17–1.06) for all other anthropogenic sources within 500 km. The screened joint fit predicts the withheld days better than a refitted background at both receptors. The withheld RMSE is 34.1 ppb at BKT and 32.1 ppb at Jambi, against 42.1 and 36.9 ppb for the refitted background; the Jambi comparison rests on 3 withheld hours.

The BKT-only fit for December 2023 (0.46 (0.16–0.99), 0.59 (0.21–1.24), 0.38 (0.14–0.78)) and the September 2019 BKT inversion agree in direction: All three medians are below unity in both periods and each pair of 95% intervals overlaps. The EDGAR_2025_GHG release supplies monthly methane fluxes for 2023 and 2024 and would remove the proxy inventory year used here. CarbonTracker CT-NRT.v2025-1 is a carbon dioxide product and supplies no methane boundary, and no CarbonTracker-CH₄ release reaches 2024, so the larger October–December 2024 overlap cannot yet be inverted with the same boundary treatment. All results are regional adjustment factors under a stated error model, conditional on parameterized transport and the assumed inlet heights.

## 1. Scientific question and scope

The September 2019 BKT inversion showed that one highland tower can scale regional methane priors when the transport error model is consistent with the residuals. A single receptor cannot, however, separate a source near the tower from a transport error near the tower, and BKT sits above much of the lowland where Sumatran methane is emitted. A second tower on the lowland should sample different air, see different sources, and test whether one set of emission multipliers explains both records.

The study asks three questions. Do BKT and Jambi constrain the same emission multipliers? Which Jambi hours can a quarter-degree transport model represent? Which input products would allow the analysis to be extended beyond December 2023? It does not estimate emission totals, resolve individual facilities, or attribute enhancements to single sources.

## 2. Evidence and data quality

### 2.1 Joint observation window

BKT and Jambi overlap in two periods of the harmonized hourly archive: late 2023, and October to December 2024 (Table 1). A receptor hour is usable only when both towers have a valid, unflagged methane value at 06 or 18 UTC, the hours used by the earlier BKT inversion. The 2024 overlap is larger, with 127 joint hours from 2024-10-01 to 2024-12-31, but the CarbonTracker-CH₄ boundary product and the LPJ-MERRA2 wetland product both end in 2023 (Section 5). The analysis therefore uses 24 November to 31 December 2023: 76 scheduled hours, 66 valid at BKT, 56 valid at Jambi and 49 valid at both.

**Table 1. Candidate joint windows at 06 and 18 UTC.** Valid means a methane value not flagged suspect. The boundary column records whether CarbonTracker-CH₄ 2025 mole fractions and LPJ-MERRA2 wetlands exist for the window.

| Window | Scheduled hours | BKT valid | Jambi valid | Joint valid | Boundary and wetlands | Used |
| --- | --- | --- | --- | --- | --- | --- |
| 2023-11-24 to 2023-12-31 | 76 | 66 | 56 | 49 (64%) | yes | yes |
| 2023-12-01 to 2023-12-31 | 62 | 57 | 43 | 41 (66%) | yes |  |
| 2024-10-01 to 2024-12-31 | 184 | 160 | 146 | 127 (69%) | no |  |
| 2024-11-26 to 2024-12-31 | 72 | 72 | 70 | 70 (97%) | no |  |
| 2024-12-01 to 2024-12-31 | 62 | 62 | 60 | 60 (97%) | no |  |

Every fourth joint day was withheld before fitting, which gives 12 withheld receptor hours at each tower before transport screening. Withholding complete days keeps the diurnal pair together and limits leakage of correlated error from fitted into withheld hours.

### 2.2 Inlet heights and observation handling

Both receptors are released at 100 m above model ground. This is the tower measurement height supplied for both stations and is treated as an assumption; the inlet heights were not independently verified in this study. The model ground in the receptor cell is 816 m at BKT and 16 m at Jambi, against station elevations of 865 m and 25 m, so the modeled BKT release sits about 50 m lower above sea level than the true inlet. Observations are the harmonized hourly methane records in ppb with the project's suspect flags applied; flagged hours are treated as missing. The concentration values play no part in selecting receptor hours.

## 3. Methods

### 3.1 Transport ensemble

Each of the 49 joint hours was simulated at both towers with HYSPLIT 5.4.2 in STILT mode, 120 h backward, with three random seeds of 2,000 requested particles, the configuration of the revised BKT ensemble. Meteorology is the NOAA GFS quarter-degree archive in ARL format, cropped server-side to 50°–160° E and 40° S–30° N, for 19 November to 31 December 2023. Footprints are written hourly on a 0.25° grid spanning 60° of latitude and 100° of longitude centered on each tower, normalized by the actual number of emitted particles and averaged across seeds. The campaign completed all 294 runs, with a median run time of 46 min.

A receptor hour is used only when every seed retains at least 95% of its particles inside the domain at 120 h. Particles lost earlier leave both their surface sensitivity and their endpoint background unsampled, so a partly emptied footprint would bias the source and background terms together.

### 3.2 Priors and boundary

The anthropogenic prior is EDGAR v8.0 monthly methane flux for November and December 2022, the latest year of that release, applied to 2023 as a proxy. Wetlands are LPJ-MERRA2 monthly fluxes for 2023. Fires are the CarbonTracker-CH₄ 2025 pyrogenic flux for November and December 2023, held constant within each month, because the daily GFED5.1 record used for 2019 ends in 2022. That product has no cropland partition, so all fire methane enters the fire component. Termite emissions, geological seepage and soil uptake are fixed climatological fields; their modeled enhancements are added to the baseline, and their squared magnitudes are added to the error variance. All flux fields are remapped to each tower's footprint grid.

The background of each receptor hour is CarbonTracker-CH₄ 2025 mole fraction sampled at the position and height of every retained particle at 120 h, with height above model terrain converted to altitude, and averaged with equal weight. CarbonTracker-CH₄ 2025 assimilates the BKT flask and in situ records; Jambi does not appear among its assimilated sites [8]. The BKT background is therefore not independent of the BKT observations, while the Jambi background is.

### 3.3 Two-receptor inversion

Each observation is modeled as background plus fixed natural terms, plus the sum of four prior increments each scaled by a positive multiplier, plus a per-tower offset and linear trend. The four components are anthropogenic emissions within 500 km of the observing tower, anthropogenic emissions beyond 500 km, wetlands and fires. The multipliers are shared by both towers, so a component near Jambi and the same component near BKT are scaled by one factor. The offset and trend are separate for each tower, which absorbs a coherent boundary bias at either site without forcing it onto the sources.

Multipliers have log-normal priors with a factor-of-two standard deviation; offsets and trends have Gaussian priors of 20 ppb and 10 ppb per 28 days. The error covariance for each tower combines a 5 ppb measurement allowance, a local mismatch of 20 ppb by day and 40 ppb by night, a transport error equal to a fixed fraction of the hour's total prior increment with 24 h correlation, and a 10 ppb background term with 72 h correlation. Errors are independent between towers. The transport fraction is chosen, for each case, as the value in a scan from 0.05 to 1.0 at which the training reduced chi-square equals one at the posterior mode; where no value in the scan reaches one, the fraction is set to the cap. Posteriors are sampled by Markov chain Monte Carlo and accepted only with R-hat at most 1.01 and an effective sample size of at least 1,000 for every parameter.

A five-component variant separates the EDGAR fuel-exploitation sector within 500 km from all other anthropogenic sources within 500 km, because fuel exploitation dominates the Jambi prior (Section 4.2).

### 3.4 Cases and evaluation

Five fits use different training hours: BKT only; Jambi only, all hours; both towers, all hours; both towers with Jambi 18 UTC hours excluded; and the last with the sector split. Each fit is evaluated on the withheld days it did not use. A transfer test applies the BKT-only multipliers to every usable Jambi 06 UTC hour, none of which entered that fit. Two baselines are refitted on the same training hours: the background with its fitted offset and trend but no source increments, and the prior inventory with unit multipliers.

## 4. Results

### 4.1 Footprints and transport completeness

The two towers sample different air (Figure 1). BKT places 74% of its mean surface sensitivity within 500 km and 32% within 50 km, concentrated along the western highlands and coast. Jambi places 55% within 500 km and 14% within 50 km, centered on the eastern lowland. Both footprints carry a long tail to the northeast. Mean integrated sensitivity is 10.2 and 11.2 ppm per µmol m⁻² s⁻¹.

![Mean footprints and particle retention.](outputs/hysplit/two_receptor/figures/figure_T01_footprints.png)

**Figure 1.** Three-seed mean surface footprints over all receptor hours for BKT (a) and Jambi (b), with 500 km circles, and the minimum fraction of particles retained at 120 h across seeds for every receptor hour (c). Hours below the dashed 0.95 line are excluded from fitting.

Unlike the September 2019 BKT ensemble, in which every hour kept all of its particles, this window loses particles across the domain boundary. 8 BKT hours and 14 Jambi hours fail the retention screen, all 22 of them on or after 20 December, and the lowest retention is 0.55. Late December is therefore under-represented in the fit (Table 2).

**Table 2. Transport and operator summary by receptor.** Sensitivity is the three-seed mean integrated footprint in ppm per µmol m⁻² s⁻¹ over all 49 hours; background and enhancement are means over hours that pass the 95% particle-retention screen.

| Receptor | Usable hours | Fitted / withheld | Sensitivity | Within 500 km (%) | Within 50 km (%) | Background (ppb) | Observed enhancement (ppb) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Bukit Kototabang | 41 of 49 | 32 / 9 | 10.2 | 74 | 32 | 1927 | 60 |
| Jambi | 35 of 49 | 27 / 8 | 11.2 | 55 | 14 | 1959 | 157 |

### 4.2 Prior source mix at the two towers

The prior sees two different source regions (Table 3). At BKT the largest modeled increments are wetlands (58 ppb) and agriculture (32 ppb). At Jambi the EDGAR fuel-exploitation sector contributes 118 ppb on average, against 16 ppb at BKT, and exceeds every other source at that tower. Fire contributes about 1.4 ppb on average across both towers in this window, too little for the data to constrain the fire multiplier.

**Table 3. Mean prior enhancement by source, ppb, over usable receptor hours.** Three-seed ensemble means; minor EDGAR sectors (industry, power, transport) are below 0.5 ppb at both receptors and are omitted from the table but not from the fit.

| Source | BKT | Jambi |
| --- | --- | --- |
| EDGAR fuel exploitation | 16.5 | 117.7 |
| EDGAR agriculture | 32.4 | 11.2 |
| EDGAR waste | 5.4 | 24.1 |
| EDGAR buildings | 1.1 | 1.4 |
| LPJ-MERRA2 wetlands | 57.6 | 37.8 |
| Termites (fixed) | 5.4 | 5.9 |
| Geological seepage (fixed) | 0.5 | 0.2 |
| Soil uptake (fixed, subtracted) | 1.9 | 1.3 |
| CarbonTracker-CH₄ pyrogenic | 1.7 | 1.2 |

### 4.3 Jambi night hours

The two towers respond differently to the night boundary layer (Table 4, Figure 2). At Jambi the median model mixing depth falls from 959 m at 06 UTC to 39 m at 18 UTC, and the observed enhancement rises from 50 ± 32 ppb to 220 ± 111 ppb, with a maximum of 529 ppb. At BKT the model mixing depth also collapses at night, to 43 m, but the enhancement changes only from 52 to 65 ppb.

**Table 4. Observed enhancement and model boundary layer by receptor and hour, usable hours.** Mixing depth and 10 m wind are native GFS values in the receptor cell; enhancement is observation minus endpoint background; prior is the sum of the four fitted components.

| Receptor | Hour | n | Mixing depth, median (m) | 10 m wind, median (m s⁻¹) | Enhancement, mean ± sd (ppb) | Maximum (ppb) | Prior (ppb) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Bukit Kototabang | 06 UTC (13 WIB) | 16 | 673 | 1.2 | 52 ± 42 | 128 | 85 |
| Bukit Kototabang | 18 UTC (01 WIB) | 25 | 43 | 0.4 | 65 ± 37 | 152 | 135 |
| Jambi | 06 UTC (13 WIB) | 13 | 959 | 1.4 | 50 ± 32 | 104 | 147 |
| Jambi | 18 UTC (01 WIB) | 22 | 39 | 1.0 | 220 ± 111 | 529 | 221 |

![Enhancement against model mixing depth.](outputs/hysplit/two_receptor/figures/figure_T04_jambi_nights.png)

**Figure 2.** Observed enhancement above the endpoint background against the native GFS mixing depth in the receptor cell, at 06 UTC and 18 UTC, for BKT (a) and Jambi (b), over hours that pass the retention screen. Mixing depths are floored at 10 m for the logarithmic axis.

The Jambi night standard deviation of 111 ppb is well above the 40 ppb night mismatch allowed by the error model, and the modeled increments do not reproduce it. When those hours are fitted, the reduced chi-square of the Jambi-only and joint fits stays above one even at the largest transport fraction scanned, so the fraction is set to its cap of 1.00 and the likelihood is flattened for both towers. A quarter-degree driver with a three-hourly boundary layer is unlikely to represent an accumulation that forms within tens of meters of a lowland surface, whatever its source. Jambi 18 UTC hours are therefore excluded from the screened cases and treated as an out-of-model class rather than as evidence about emissions.

### 4.4 Emission multipliers

The multipliers depend on which Jambi hours are fitted (Table 5, Figure 3). The BKT-only fit scales the three constrained components to 0.46 (0.16–0.99), 0.59 (0.21–1.24) and 0.38 (0.14–0.78), with a transport fraction of 0.34. Adding all Jambi hours moves every multiplier back toward unity (0.82 (0.32–1.50), 0.98 (0.28–2.47), 0.56 (0.19–1.26)) and widens the intervals. Excluding Jambi 18 UTC hours restores a consistent covariance, with a transport fraction of 0.28, and gives 0.29 (0.12–0.56) for anthropogenic emissions within 500 km, 0.56 (0.21–1.12) beyond 500 km and 0.40 (0.16–0.76) for wetlands. Fires remain at the prior (0.96 (0.25–3.64)).

**Table 5. Posterior emission multipliers by inversion case.** Posterior medians with 95% credible intervals; unity reproduces the prior. Near field is anthropogenic emission within 500 km of the observing tower and far field beyond 500 km; the sector split reports fuel exploitation and all other near-field sectors separately. Fitted hours count both towers. The transport-error fraction is tuned for a training reduced chi-square of one and capped at 1.0.

| Case | Fitted hours | Transport fraction | Near field | Far field | Wetlands | Fires |
| --- | --- | --- | --- | --- | --- | --- |
| BKT only | 32 | 0.34 | 0.46 (0.16–0.99) | 0.59 (0.21–1.24) | 0.38 (0.14–0.78) | 0.95 (0.25–3.56) |
| Jambi only, all hours | 27 | 1.00 | 0.85 (0.31–1.61) | 1.40 (0.32–5.25) | 0.90 (0.26–2.50) | 1.00 (0.26–3.98) |
| Joint, all hours | 59 | 1.00 | 0.82 (0.32–1.50) | 0.98 (0.28–2.47) | 0.56 (0.19–1.26) | 1.00 (0.26–3.93) |
| Joint, Jambi 18 UTC excluded | 42 | 0.28 | 0.29 (0.12–0.56) | 0.56 (0.21–1.12) | 0.40 (0.16–0.76) | 0.96 (0.25–3.64) |
| Joint screened, sector split | 42 | 0.29 | fuel 0.32 (0.12–0.63); other 0.48 (0.17–1.06) | 0.57 (0.21–1.13) | 0.36 (0.14–0.72) | 0.97 (0.25–3.59) |

![Multipliers by case and withheld error.](outputs/hysplit/two_receptor/figures/figure_T03_multipliers.png)

**Figure 3.** Posterior multipliers with 95% credible intervals for each inversion case on a logarithmic axis (a), and withheld-day RMSE of the screened joint posterior against the refitted background and the prior inventory at each tower (b).

The sector split shows where the near-field reduction sits. Fuel exploitation within 500 km scales to 0.32 (0.12–0.63), with a posterior probability of exceeding the inventory below 0.001. All other anthropogenic sources within 500 km scale to 0.48 (0.17–1.06); their median is below unity but the interval reaches it, and the probability of exceeding the inventory is 0.04. Wetlands (0.36 (0.14–0.72)) and the far anthropogenic term (0.57 (0.21–1.13)) are almost unchanged by the split.

The September 2019 BKT inversion gave 0.37 (0.15–0.70), 0.24 (0.10–0.45) and 0.43 (0.16–0.91) for the same three components. All three medians are below unity in both periods and each pair of 95% intervals overlaps. The two periods differ in season, inventory year and fire regime, so the agreement is consistent with a persistent over-estimate in the priors but does not establish one.

### 4.5 Prediction on hours the fit did not use

The screened joint fit predicts the withheld days better than a refitted background at both receptors. The screened joint posterior predicts the withheld days with RMSE 34.1 ppb at BKT (9 hours) and 32.1 ppb at Jambi (3 hours), against 42.1 and 36.9 ppb for the refitted background (Table 6, Figure 4). Fitting all Jambi hours raises the BKT withheld RMSE to 45.3 ppb, against 50.1 ppb for the background refitted under that fit's covariance.

**Table 6. Evaluation on hours the fit did not use: RMSE in ppb with mean bias in parentheses.** Withheld hours are complete days fixed before fitting; the last row applies multipliers fitted at BKT alone to every usable Jambi 06 UTC hour. Background only refits the per-receptor offset and trend with source multipliers at zero; prior inventory uses unit multipliers.

| Case | Evaluated at | n | Posterior | Background only | Prior inventory |
| --- | --- | --- | --- | --- | --- |
| BKT only | Bukit Kototabang | 9 | 34.5 (+7.1) | 42.7 (-18.2) | 61.5 (+48.4) |
| Joint, all hours | Bukit Kototabang | 9 | 45.3 (+28.4) | 50.1 (-32.2) | 61.5 (+48.4) |
| Joint, all hours | Jambi | 8 | 138.0 (-11.4) | 168.0 (-107.4) | 137.8 (+3.8) |
| Joint, Jambi 18 UTC excluded | Bukit Kototabang | 9 | 34.1 (+3.0) | 42.1 (-16.6) | 61.5 (+48.4) |
| Joint, Jambi 18 UTC excluded | Jambi | 3 | 32.1 (+12.0) | 36.9 (-11.0) | 88.7 (+87.9) |
| Joint screened, sector split | Bukit Kototabang | 9 | 34.0 (+5.6) | 42.2 (-17.0) | 61.5 (+48.4) |
| Joint screened, sector split | Jambi | 3 | 33.2 (+15.3) | 37.1 (-11.5) | 88.7 (+87.9) |
| BKT-only multipliers, Jambi 06 UTC hours | Jambi | 13 | 56.5 (+23.0) | 56.2 (-46.9) | 140.8 (+100.3) |

The transfer test is the stricter one, because the Jambi hours are predicted by multipliers fitted at BKT alone, without a fitted Jambi offset. The prior inventory over-predicts those 13 Jambi 06 UTC hours by +100 ppb with RMSE 140.8 ppb; the transferred multipliers reduce the bias to +23 ppb. Transferred multipliers remove most of the prior over-prediction but do not predict Jambi better than its endpoint background without a fitted Jambi offset: RMSE 56.5 against 56.2 ppb. The endpoint background alone under-predicts by -47 ppb yet has almost the same RMSE, so the transferred source increments correct the mean level at Jambi without reducing its hour-to-hour scatter.

![Observed and modeled methane at both towers.](outputs/hysplit/two_receptor/figures/figure_T02_series.png)

**Figure 4.** Observed methane with the screened joint posterior median and 95% parameter interval, the prior inventory and the endpoint background at BKT (a) and Jambi (b), for hours that pass the retention screen. Filled circles were fitted, open circles were withheld, and crosses mark Jambi 18 UTC hours excluded from fitting.

## 5. Input products for extending the analysis

The October–December 2024 overlap would more than double the joint record. Three candidate products were checked against the inputs this design requires (Table 7).

**Table 7. Coverage of candidate input products, checked 2026-09-15.** Directory listings, HTTP headers, zip central directories and netCDF headers only; no data arrays were transferred. A product covers a December when it contains that month.

| Product | Species | Role | Available period | Covers Dec 2023 | Covers Dec 2024 |
| --- | --- | --- | --- | --- | --- |
| EDGAR v8.0 monthly CH₄ fluxes (used) | CH₄ | anthropogenic prior | 2000 to 2022 | no | no |
| EDGAR_2025_GHG monthly CH₄ fluxes | CH₄ | anthropogenic prior | 2000 to 2024 | yes | yes |
| CarbonTracker CT-NRT.v2025-1 molefractions | CO₂ | boundary mole fractions | 2021-01-01 to 2024-12-31 | yes | yes |
| CarbonTracker-CH₄ 2023 molefractions | CH₄ | boundary mole fractions | 1998 to 2021-12-31 | no | no |
| CarbonTracker-CH₄ 2025 molefractions (used) | CH₄ | boundary mole fractions | 1998 to 2023-12-31 | yes | no |
| CarbonTracker-CH₄ unversioned legacy tree | CH₄ | boundary mole fractions | 2000-01-01 to 2010-12-31 | no | no |
| CarbonTracker-CH₄ 2025 fluxes (fire prior used) | CH₄ | fire prior | 1998 to 2023 | yes | no |
| LPJ-MERRA2 wetlands, HEMCO v2025-09 (used) | CH₄ | wetland prior | through 2023 | yes | no |
| NOAA GFS 0.25 ARL archive (used) | none | meteorology | daily files, checked by year | yes | yes |

**EDGAR_2025_GHG.** The release provides monthly methane fluxes for the same eight sectors as EDGAR v8.0 through 2024 [7]. Each year can be extracted from the sector archives by range reads, about 439 MB of compressed transfer per year. It would replace the 2022 proxy with 2023 fluxes for this window and supply 2024 for the next. Only the archive directories were read; variable names and units must be confirmed on extraction before the fields replace EDGAR v8.0.

**CarbonTracker CT-NRT.v2025-1.** The near-real-time release provides global 3° by 2° carbon dioxide mole fractions on 34 levels every three hours from 2021-01-01 to 2024-12-31, in the same layout as the CT2022 files already sampled by this project [9]. It can supply endpoint carbon dioxide backgrounds for both windows. It carries no methane field and cannot replace the methane boundary.

**CarbonTracker-CH₄.** The 2025 release, used here, ends on 2023-12-31; the 2023 release ends on 2021-12-31, and the unversioned tree ends on 2010-12-31 [8]. No release covers 2024. A December 2024 methane inversion therefore still needs a methane boundary, a 2024 wetland field (LPJ-MERRA2 is listed through 2023) and a 2024 fire field. Until a methane reanalysis covering 2024 is identified and checked, the only option within this design would be to drop the modeled boundary and let per-tower offsets and trends carry the background, which weakens the separation of sources from background that this report depends on.

## 6. Interpretation and limitations

A lowland tower adds information about emissions only through the hours a transport model can represent. With Jambi daytime hours alone, one set of multipliers explains both towers better than a refitted background, the near-field anthropogenic reduction is clearest in the fuel-exploitation sector, and the wetland multiplier is similar in the BKT-only fit, the screened joint fit and the 2019 BKT inversion. Jambi night hours, the most striking part of its record, are outside the model, and fitting them flattens the likelihood for both records.

The main limitations follow.

- The inlet height of 100 m at both towers is an assumption. A lower Jambi inlet would likely sit deeper in the night layer and increase the mismatch.
- The Jambi evaluation rests on 3 withheld daytime hours, and all 22 transport-screened hours fall after 20 December.
- The anthropogenic prior is a proxy year, the fire prior is monthly, and fire is not constrained in December.
- The boundary assimilates BKT but not Jambi, so the two backgrounds are not equally independent of the observations they explain.
- Convective transport is parameterized by the driver's mixing depth only; the archive carries no convective fluxes.
- Multipliers scale fixed spatial patterns. A multiplier below one can reflect a misplaced source as well as an over-estimated one.

## References

1. NOAA Air Resources Laboratory. *Configuring STILT options in HYSPLIT*. [Official model guidance](https://www.ready.noaa.gov/documents/Tutorial/html/stilt_setup.html).
2. Lin, J. C., et al. (2003). A near-field tool for simulating the upstream influence of atmospheric observations: The Stochastic Time-Inverted Lagrangian Transport (STILT) model. *Journal of Geophysical Research: Atmospheres*, 108(D16), 4493. [doi:10.1029/2002JD003161](https://doi.org/10.1029/2002JD003161).
3. NOAA Air Resources Laboratory. *GFS quarter-degree meteorological archive: data and hybrid-level definitions*. [Archive documentation](https://www.ready.noaa.gov/data/archives/gfs0p25/readme_gfs0p25_info.txt).
4. Stein, A. F., et al. (2015). NOAA's HYSPLIT atmospheric transport and dispersion modeling system. *Bulletin of the American Meteorological Society*, 96, 2059–2077. [doi:10.1175/BAMS-D-14-00110.1](https://doi.org/10.1175/BAMS-D-14-00110.1).
5. Lin, J. C., and Gerbig, C. (2005). Accounting for the effect of transport errors on tracer inversions. *Geophysical Research Letters*, 32, L01802. [doi:10.1029/2004GL021127](https://doi.org/10.1029/2004GL021127).
6. European Commission Joint Research Centre. *EDGAR v8.0 greenhouse-gas emissions, monthly sectoral fluxes*. [Dataset and methodological documentation](https://edgar.jrc.ec.europa.eu/dataset_ghg80).
7. European Commission Joint Research Centre. *EDGAR_2025_GHG: IEA-EDGAR CO₂, EDGAR CH₄, N₂O and F-gases, 1970–2024*. [Dataset page](https://edgar.jrc.ec.europa.eu/dataset_ghg2025), accessed 15 September 2026.
8. NOAA Global Monitoring Laboratory. *CarbonTracker-CH₄ CT-CH₄ 2025 documentation*. [Web documentation](https://gml.noaa.gov/ccgg/carbontracker-ch4/documentation.php) and [site and method documentation](https://gml.noaa.gov/ccgg/carbontracker-ch4/CTCH4_v2025_Website-Documentation.pdf), accessed 15 September 2026.
9. NOAA Global Monitoring Laboratory. *CarbonTracker CT-NRT.v2025-1 data products*. [Data directory](https://gml.noaa.gov/aftp/products/carbontracker/co2/CT-NRT.v2025-1/), accessed 15 September 2026.
10. GEOS-Chem HEMCO data repository. *LPJ-MERRA2 wetland methane emissions, v2025-09*. [Data directory](https://geos-chem.s3.amazonaws.com/HEMCO/CH4/v2025-09/LPJ_MERRA2/), accessed 15 September 2026.

<!-- pdf-pagebreak -->

## Appendix. Terms used in this report

**Table 8. Terms used in this report.**

| Term | Meaning |
|---|---|
| Receptor hour | One observation time at one tower, simulated backward in time |
| Prior increment | Modeled methane enhancement from one source component with its multiplier at unity |
| Emission multiplier | Dimensionless factor applied to a fixed prior pattern; unity reproduces the inventory |
| Endpoint background | Boundary mole fraction sampled where the particles are after 120 h |
| Retention screen | Requirement that every seed keep at least 95% of its particles in the domain at 120 h |
| Transport-error fraction | Share of each hour's prior increment treated as correlated transport error |
| Reduced chi-square | Mean squared whitened residual at the posterior mode; one indicates a covariance consistent with the residuals |
| Withheld days | Complete days designated before fitting and never used by the optimizer |
| Transfer test | Prediction of one tower's hours with multipliers fitted at the other tower only |
