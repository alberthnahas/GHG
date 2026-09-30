# Carbon dioxide and methane over Sumatra, seen from two towers

## Scientific summary

Two Sumatran towers, one on the highland spine at Bukit Kototabang and one in the eastern lowland at Jambi, are used here to ask what a small greenhouse gas network can say about Indonesian emissions. The answer has two halves, and they are different.

The forward part works and is quantitative. The towers draw at least one percent of their modelled methane signal from four provinces and no more. At Jambi one sector carries the modelled signal, fugitive emission from fuel exploitation at 62%; at Bukit Kototabang natural wetlands do, at 48%. Peatland carries 34 ppb of the 147 ppb modelled methane signal at Jambi, 23%, reaching 95 ppb on the most peat-influenced afternoon, against 2.9% at the highland tower. Drained peat is also the largest single carbon dioxide term at Jambi after the biosphere, 1.51 ppm, larger than any individual fossil sector and two thirds of all of them combined.

The clearest statement the record makes needs no inversion at all. The global gridded inventory says 115 ppb of methane should arrive above background at Bukit Kototabang and 147 ppb at Jambi; 56 and 47 ppb arrive. Indonesia's own reported inventory removes most of that excess: it reports 666 Gg of fugitive methane for 2022 where the global inventory puts 7543 Gg inside the country. Localising the prior to the reported totals and allocating them across provinces cuts the prior error from 99.5 to 47.9 ppb and is the only configuration that puts both towers on the favourable side of the boundary null. Under the stated error model the fit goes further and rejects the global inventory outright in the region the towers see: the near-field methane multiplier is 0.25 with a 95% interval of 0.11 to 0.47, which excludes one, and it stops excluding one (0.61, 0.22 to 1.24) once Indonesia's own provincial figures set the magnitude. That is the single resolved result in this report.

The inverse part does not work yet, and the reason is measured rather than asserted. The modelled source signal is barely above the error it arrives through: a signal-to-error ratio of 1.34 for carbon dioxide and 1.20 for methane, with transport the largest error term for both. Of the 18 combinations run, none beats a fitted boundary field at a scale with enough independent bins to test, and no emission change smaller than about a factor of two could be detected at all. The transport error is not stochastic and will not fall by running more particles; it needs a second meteorological driver, which is the one experiment this project has not done.

## 1. What this report answers

A tower network is funded to answer questions about emissions, not about models. This report is organised around those questions, and it separates two things that are usually reported together.

The first is what the forward model says: which sources the towers are sensitive to, how far away and how old the air is, which provinces and which land surface carry the signal, and how much of it comes off peatland. Those answers depend on the footprints and the priors and they are quantitative today. They are also testable, because a prior that says three times too much methane should arrive is making a claim the observations can contradict.

The second is what the inversion adds on top: a correction to those priors, with an uncertainty. That part is not ready, and the report says so with the number that settles it rather than with an adjective. Keeping the two apart is the point. A footprint-weighted attribution is useful even when the inversion behind it cannot yet beat a fitted constant, and calling both of them the same kind of result is how a project like this publishes something wrong.

The evidence is organised so that each question has one place to look. Section 3 is about transport: what air reaches the towers, from how far, how old, and over which provinces. Section 4 is about sources: which sector, which land surface, and how much of it is peat. Section 5 tests the national inventory against the global gridded one. Section 6 asks what the inversion itself resolves, and answers, honestly, that it resolves a bulk scaling and nothing finer. Appendix A puts 75 of these questions in one list with their answers and the table each one comes from.

## 2. Observations, transport and priors

### 2.1 Sites, record and screening

Bukit Kototabang sits at 865 m on the Sumatran highland spine; Jambi sits in the eastern lowland, 380 km away across the peat basin. Receptors are afternoon hours, 12 to 14 WIB, at both towers. Night hours are excluded at both: a quarter-degree footprint cannot carry the shallow nocturnal layer the observations sit in, and fitting those hours drives the error model to its cap and returns every multiplier to its prior. Hours are further screened for particle retention, for a modelled mixing depth of at least 300 m, and for carbon-dioxide-only spikes.

### 2.2 Transport

Footprints are HYSPLIT in STILT mode, 120 hours backward, 2000 particles, three seeds, on a quarter-degree grid driven by GFS 0.25 degree meteorology. A footprint is a sensitivity of the receptor mole fraction to surface flux; it is not emission and it is not attribution. Convolving it with a flux field gives what the model says should arrive, which is the quantity every attribution in Sections 3 and 4 reports.

### 2.3 Priors

Methane takes its anthropogenic prior from a global gridded inventory, its wetland prior from a process model, and its fire, termite, geological and soil-uptake terms from published fields. Carbon dioxide takes fossil emission from the gridded inventory, the biosphere from a hybrid prior described in Section 6.6, and ocean and fire from an assimilated product.

Two terms do not come ready-made. The first is the land-use term, which the global gridded inventory excludes and which in Indonesia is the largest and most variable part of the national total. It is rebuilt here as a spatial proxy: peatland extent weighted by the land cover that implies how deeply it is drained, and burned carbon split by whether it burned over peat. The magnitude problem is deliberately not solved in the proxy, because published emission factors for drained tropical peat span a factor of ten, from 8.13 to 80.77 Mg carbon dioxide per hectare per year across land covers and water tables. The proxy therefore carries a pattern and the reported national total supplies the size.

The second is locality. The gridded inventory supplies the pattern inside the country and Indonesia's own reported total supplies the magnitude, sector by sector and then province by province, so the country total equals the reported total by construction. Section 5 is the test of whether that helps.

### 2.4 The inversion and its error model

Multipliers on the source components are positive with log-normal priors; biosphere response columns are signed, because uptake reduces the mole fraction. Offsets, trends and covariate coefficients are Gaussian. The error model combines a measurement allowance, a local mismatch, a correlated background term, and a transport error whose shape comes from the measured seed spread at each receptor and whose amplitude is calibrated to a training reduced chi-square of one.

That calibrated amplitude is itself a finding: it lands between 1.2 and 12.0, which says two or three seeds understate the true transport error by about an order of magnitude. The ensemble describes the shape of that error well and its size badly, so the amplitude is calibrated rather than measured, and measuring it would take more seeds or a comparison between meteorological drivers.

A bin mean of several receptors carries less independent error than a single receptor, so the measurement and local terms are divided by the number averaged. The background term is not, because a boundary bias is common to the hours in a bin and does not average away.

The reported fit is sampled by Markov chain and accepted only with R-hat at most 1.01 and an effective sample size of at least 1,000. A maximum-posterior fit with a Laplace covariance is about a thousand times faster and its modes agree to within 7%, but in log space its intervals put the upper bound 37 to 44% too high, which would flow into the uncertainty ratio and the degrees of freedom and make the data look less informative than they are. The approximation is therefore kept only inside the cross-validation loop, where nothing but the mode is used.

### 2.5 Scoring, and the readiness gate

Each configuration is fitted and scored at three aggregation scales. A scale with fewer than 8 independent bins is declared unresolved rather than quoted. Cross-validation refits without each bin and predicts it, and the difference from a null model, the same boundary field carrying a fitted offset and trend, is bootstrapped by resampling whole dates. Four gates decide whether a run may be presented as a finding: enough independent bins, a consistent chi-square, at least one degree of freedom informed, and a cross-validated improvement on the null somewhere.

An operational model cannot treat its inputs as an assumption either. Every dataset is declared, confirmed against its provenance record, opened and validated for variable, unit, grid, time span and physical range, and checked for compatibility with the operator grid and the study windows (Table 1).

**Table 1. The datasets the operational model depends on.** Each is confirmed against its provenance record, opened and validated for variable, unit, grid and physical range, and checked against the study windows.

| Dataset | Role | Need | Status | What was checked |
| --- | --- | --- | --- | --- |
| GRK station archive | observations | required | ok | 5 of 5 stations carry data |
| GFS 0.25 ARL, 2023 window | meteorology | required | ok | 43 files, 43 with a provenance record |
| GFS 0.25 ARL, 2024 window | meteorology | required | ok | 94 files, 94 with a provenance record |
| EDGAR v8 methane | prior, anthropogenic CH₄ | required | ok | fluxes, unit kg m⁻² s⁻¹, grid 1800 × 3600, range 0 to 2.3e-06 |
| EDGAR_2025 carbon dioxide | prior, fossil CO₂ | required | ok | fluxes, unit kg m⁻² s⁻¹, grid 1800 × 3600, range 0 to 3.33e-08 |
| CT-NRT fluxes | prior, CO₂ ocean fire biosphere | required | ok | 137 files, 137 with a provenance record |
| CT-NRT mole fractions | boundary, CO₂ | required | ok | 91 files, 91 with a provenance record |
| CarbonTracker-CH₄ | boundary and fire, CH₄ | required | ok | 2 files, 2 with a provenance record |
| PRIMAP-hist v2.6.1 | national inventory totals | required | ok | 281 columns, first is 'source' |
| MODIS MCD12C1 land cover | FOLU and biosphere weighting | required | ok | 3600 × 7200 at 0.05 degrees, EPSG:4326 |
| Indonesian peatland extent | FOLU proxy | required | ok | 1277 features or geometries |
| GFED 5.1 | FOLU fire proxy | required | ok | carbon_emissions, unit g C per month, grid 720 × 1440, range 0 to  |
| 38-province boundary | regional masks | required | ok | 38 features or geometries |
| Diagnostic biosphere | prior, CO₂ biosphere | required | ok | gpp, unit µmol m⁻² s⁻¹, grid 281 × 441, range -51.8 to -0 |
| Hybrid biosphere | prior, CO₂ biosphere | required | ok | gpp, unit µmol m⁻² s⁻¹, grid 281 × 441, range -42.4 to 0 |
| ODIAC 2023 | alternative fossil pattern | optional | ok | 1 files, 1 with a provenance record |
| CT2022 fluxes | historical CO₂ fluxes | optional | ok | 35 files, 35 with a provenance record |

All 17 validate, 15 of them required, so the model is clear to run. A required dataset that failed would block it rather than degrade it quietly.

## 3. What the towers see

### 3.1 The record

**Table 2. The screened record, and what the prior says should be in it.** The enhancement is the observation minus the modelled background; the modelled source signal is what the prior says the surface added.

| Gas | Receptor | Window | Receptors | Mean | Standard deviation | Observed enhancement | Modelled source signal |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CH₄ | Bukit Kototabang | 2023-11-25 to 2023-12-31 | 41 | 1987.5 | 49.8 | +56.2 | +115.1 |
| CH₄ | Jambi | 2023-11-26 to 2023-12-31 | 13 | 2006.4 | 37.1 | +46.9 | +147.2 |
| CO₂ | Bukit Kototabang | 2023-11-26 to 2024-12-31 | 69 | 419.5 | 3.0 | -4.5 | -1.7 |
| CO₂ | Jambi | 2023-11-27 to 2024-12-30 | 66 | 422.3 | 5.0 | -2.6 | +2.3 |

The first result is visible before any inversion is run. The global gridded prior says 115 ppb of methane should arrive above the background at Bukit Kototabang and 147 ppb at Jambi. What arrives is 56 and 47 ppb. The prior is 2.0 times too large at the highland tower and 3.1 times too large in the lowland, and that mismatch, not the fit, is the strongest statement this record makes about the inventory. Section 5 shows that most of it is one sector.

Carbon dioxide behaves in the opposite direction and for a physical reason: on a screened afternoon the observation sits 4.5 ppm below the modelled background at Bukit Kototabang and 2.6 ppm below it at Jambi, because photosynthesis is drawing the well-mixed layer down faster than emission fills it. The quantity being tested for that gas is a drawdown, not an enhancement.

### 3.2 Where the air comes from, and how old it is

![Mean footprints at both towers.](outputs/operational/figures/map_M01_footprints.png)

**Figure 1.** Mean 120-hour HYSPLIT-STILT surface footprint over the screened receptors at each tower. Cells below the 60th percentile of positive sensitivity are masked; each panel states how much sensitivity the coloured area carries.

**Table 3. How far away and how old.** The first five rows are the share of each quantity emitted within a distance band of the tower; the last two are the share of footprint sensitivity by how long the air had been travelling, in hours before arrival, so the column headings carry both units.

| Receptor | Quantity | 0 to 50 km / 0 to 6 h | 50 to 200 km / 6 to 24 h | 200 to 500 km / 24 to 48 h | 500 to 1000 km / 48 to 72 h | beyond 1000 km / 72 to 120 h |
| --- | --- | --- | --- | --- | --- | --- |
| Bukit Kototabang | footprint sensitivity | 32 | 26 | 18 | 12 | 11 |
| Bukit Kototabang | anthropogenic | 53 | 20 | 5 | 21 | 2 |
| Bukit Kototabang | wetlands | 82 | 9 | 8 | 0 | 0 |
| Jambi | footprint sensitivity | 8 | 21 | 23 | 22 | 27 |
| Jambi | anthropogenic | 29 | 25 | 40 | 5 | 2 |
| Jambi | wetlands | 10 | 39 | 44 | 5 | 2 |
| Bukit Kototabang | sensitivity by age of air | 15 | 29 | 21 | 14 | 20 |
| Jambi | sensitivity by age of air | 5 | 20 | 23 | 21 | 31 |

The two towers are not doing the same job. Bukit Kototabang is local: 53% of its modelled anthropogenic methane is emitted within 50 km, and the median age of the air carrying its signal is 30 hours. Jambi is regional: only 29% comes from within 50 km, 40% from 200 to 500 km, and the median age is 49 hours, so it is sampling air that has been over land for two days.

That difference has a consequence the inversion cannot escape. The older the air, the more of the arriving mole fraction was set at the boundary rather than by the surface inside the domain, so a boundary bias and a flux error become harder to tell apart. At Jambi 31% of the sensitivity is older than three days. This is the physical reason the boundary null is a strong competitor, and it is why Section 6.4 finds the background term, small in variance, still expensive in what it hides.

### 3.3 Which provinces the network can constrain

![Provincial share of the modelled methane signal.](outputs/operational/figures/map_M04_province_influence.png)

**Figure 2.** Provincial emission weighted by the mean footprint, methane, anthropogenic and natural terms together, for each tower.

**Table 4. The five provinces carrying most of each tower's modelled methane signal.** The last column is the share of raw footprint sensitivity, so a province whose signal share far exceeds it is one where the inventory, not the transport, puts the methane.

| Receptor | Province | Mean (ppb) | Share of source signal (%) | Share of anthropogenic signal (%) | Share of sensitivity (%) |
| --- | --- | --- | --- | --- | --- |
| Bukit Kototabang | Sumatera Barat | 83.06 | 72.2 | 57.5 | 36.45 |
| Bukit Kototabang | Riau | 10.73 | 9.3 | 11.3 | 8.56 |
| Bukit Kototabang | Sumatera Selatan | 9.77 | 8.5 | 17.3 | 0.23 |
| Bukit Kototabang | Bengkulu | 1.06 | 0.9 | 0.5 | 0.92 |
| Bukit Kototabang | Jambi | 0.36 | 0.3 | 0.0 | 0.12 |
| Jambi | Jambi | 68.15 | 46.3 | 50.2 | 15.51 |
| Jambi | Sumatera Selatan | 41.55 | 28.2 | 32.8 | 3.70 |
| Jambi | Riau | 16.24 | 11.0 | 4.0 | 10.62 |
| Jambi | Sumatera Barat | 1.19 | 0.8 | 0.6 | 0.81 |
| Jambi | Lampung | 0.99 | 0.7 | 0.6 | 0.96 |

Between them the two towers draw at least one percent of their modelled methane signal from four provinces and no more: Jambi, Riau, Sumatera Barat, Sumatera Selatan. No province outside Sumatra reaches one percent at either tower, so nothing in this report supports a national statement, and the provincial allocation of the inventory in Section 5.2 exists precisely because a national correction would be applied mostly to places neither tower can see.

The towers are not redundant and they are not independent. Bukit Kototabang draws 72% of its signal from its own province, while Jambi spreads across three, and Riau is common to both. A third receptor placed to break that overlap would add more than a fourth placed near either of these.

### 3.4 Districts, and where an inventory error would hurt

![District share of the modelled methane signal.](outputs/operational/figures/map_M06_districts.png)

**Figure 3.** District emission weighted by the mean footprint. The shares attribute the prior; they do not estimate emission per district, because a quarter-degree footprint cell is larger than most Indonesian districts.

**Table 5. The six districts carrying most of each tower's modelled methane signal.** The last column is signal share divided by sensitivity share: a large value means the gridded inventory concentrates a lot of emission where the tower happens to look.

| Receptor | District | Share of source signal (%) | Share of sensitivity (%) | Signal per unit sensitivity |
| --- | --- | --- | --- | --- |
| Bukit Kototabang | Agam | 52.8 | 22.07 | 2.4 |
| Bukit Kototabang | Muara Enim | 8.3 | 0.02 | 415 |
| Bukit Kototabang | Lima Puluh Kota | 5.7 | 5.36 | 1.1 |
| Bukit Kototabang | Padang Pariaman | 5.7 | 3.95 | 1.4 |
| Bukit Kototabang | Pasaman | 3.9 | 2.97 | 1.3 |
| Bukit Kototabang | Kampar | 3.0 | 3.71 | 0.8 |
| Jambi | Tanjung Jabung Barat | 18.3 | 4.00 | 4.6 |
| Jambi | Kota Jambi | 16.0 | 3.61 | 4.4 |
| Jambi | Lahat | 13.5 | 0.08 | 173 |
| Jambi | Muara Enim | 10.7 | 0.50 | 22 |
| Jambi | Muaro Jambi | 6.0 | 1.39 | 4.3 |
| Jambi | Indragiri Hilir | 3.9 | 3.89 | 1.0 |

District shares are not a district-level result and cannot be one: a quarter-degree footprint cell is larger than most Indonesian districts, so these numbers attribute the prior rather than estimate emission. What they do show is concentration. Muara Enim carries 8.3% of the Bukit Kototabang methane signal from 0.02% of its footprint sensitivity, a ratio of 415. One or two cells of the global gridded inventory, in the South Sumatran coal basin, therefore set a large share of what the model expects at a tower 200 km away.

That is worth knowing in both directions. It says where an inventory error would do the most damage to this model, and it says where a targeted measurement, a mobile survey or a single additional inlet, would test the most inventory per unit of effort.

## 4. What emits it

### 4.1 The methane budget at each tower

**Table 6. The modelled methane budget at each tower, in ppb.** Global is the global gridded inventory and the natural priors; reported is the same pattern with Indonesia's reported provincial totals setting the magnitude. The factor is the influence-weighted provincial factor at Jambi.

| Component | BKT global | BKT reported | Jambi global | Jambi reported | Jambi factor |
| --- | --- | --- | --- | --- | --- |
| fugitive, fuel exploitation | 16.45 | 0.57 | 93.04 | 2.96 | 0.03 |
| wetlands, natural | 57.62 | 57.62 | 27.01 | 27.01 |  |
| waste | 5.38 | 10.85 | 16.49 | 16.77 | 1.02 |
| agriculture | 32.42 | 29.14 | 8.44 | 5.32 | 0.63 |
| termites | 5.41 | 5.41 | 4.36 | 4.36 |  |
| soil uptake (a sink) | 1.91 | 1.91 | 1.10 | 1.10 |  |
| buildings | 1.12 | 0.53 | 0.90 | 0.32 | 0.36 |
| land-use fire | 0.10 | 0.10 | 0.32 | 0.32 | 1.00 |
| geological seepage | 0.52 | 0.52 | 0.17 | 0.17 |  |
| transport | 0.34 | 0.16 | 0.16 | 0.06 | 0.36 |
| industrial processes | 0.02 | 0.33 | 0.07 | 0.51 | 7.14 |
| industrial combustion | 0.04 | 0.02 | 0.07 | 0.02 | 0.36 |
| power | 0.01 | 0.01 | 0.05 | 0.02 | 0.36 |

The two towers are looking at different problems. At Jambi one sector carries the signal: fugitive emission from fuel exploitation is 62% of the modelled source signal at 93 ppb under the global gridded inventory. At Bukit Kototabang the largest single term is natural wetland methane at 48%, and the largest anthropogenic one is agriculture at 27%.

Natural sources are 53% of the modelled signal at Bukit Kototabang and 21% at Jambi, counting wetlands, termites and geological seepage. None of it is in any national inventory, and none of it is reducible by policy, which is worth stating plainly: roughly half of what the highland tower measures above its background is not a mitigable emission at all. It still has to be modelled, because an error in it lands on the anthropogenic multiplier.

Localising the inventory changes the picture rather than scaling it. The fugitive term at Jambi falls from 93 to 3.0 ppb, and waste, which the country reports higher than the global inventory assumes, becomes the largest reported anthropogenic term at that tower at 16.8 ppb. Which of the two is right is the question; Section 5 is where the observations get a vote.

### 4.2 Peatland

![Peatland methane arriving at Jambi.](outputs/operational/figures/map_M05_peat_signal.png)

**Figure 4.** Where the methane emitted on peat and seen at Jambi comes from, and the three routes by which it arrives.

**Table 7. What comes off peatland, in ppb, except the sensitivity row which is in its own units.** A cell counts as peat when its centre falls inside the Indonesian peatland layer, so the split is a quarter-degree approximation to a much finer boundary.

| Receptor | Route | From peat | From all land | Peat share (%) | Largest single receptor |
| --- | --- | --- | --- | --- | --- |
| Bukit Kototabang | footprint sensitivity | 0.27 | 10.32 | 2.5 | 1.1 |
| Bukit Kototabang | anthropogenic inventory | 1.04 | 55.78 | 2.1 | 5.5 |
| Bukit Kototabang | wetlands, natural | 2.16 | 57.62 | 3.8 | 8.9 |
| Bukit Kototabang | open fire | 0.06 | 1.68 | 3.0 | 0.3 |
| Bukit Kototabang | land-use fire | 0.07 | 0.10 | 61.2 | 0.3 |
| Bukit Kototabang | all routes, global inventory | 3.32 | 115.18 | 2.9 | 11.1 |
| Bukit Kototabang | all routes, reported inventory | 3.06 | 101.01 | 3.0 | 10.7 |
| Jambi | footprint sensitivity | 1.01 | 10.67 | 9.4 | 2.2 |
| Jambi | anthropogenic inventory | 23.07 | 119.22 | 25.2 | 82.3 |
| Jambi | wetlands, natural | 10.82 | 27.01 | 42.8 | 23.2 |
| Jambi | open fire | 0.22 | 0.94 | 25.4 | 0.5 |
| Jambi | land-use fire | 0.20 | 0.32 | 58.3 | 0.6 |
| Jambi | all routes, global inventory | 34.31 | 147.48 | 23.3 | 95.2 |
| Jambi | all routes, reported inventory | 16.27 | 54.26 | 30.0 | 30.8 |

Peatland carries 34.3 ppb of the 147.5 ppb modelled methane source signal at Jambi, 23%, and reaches 95 ppb on the most peat-influenced afternoon in the record. At Bukit Kototabang the same calculation gives 3.3 ppb, 2.9%. The two towers are not sampling the same land surface, and a peatland question can only be asked at the lowland one.

The split between transport and emission is the part worth keeping. Peat cells carry 9% of the Jambi footprint sensitivity but 23% of the signal, so per unit of sensitivity peat is emitting about 2.9 times what the rest of the land in the footprint emits. That ratio is a property of the priors, not a measurement, but it is exactly the quantity a denser network would test directly.

Three routes carry it, and they are three different processes with three different answers. Anthropogenic emission sitting on drained peatland contributes 23.1 ppb, biological emission from peat swamp 10.8 ppb through the wetland prior, and fire 0.4 ppb in a window that was not a burning season. Indonesia reports no methane from drained organic soils, only carbon dioxide and nitrous oxide, so drained-peat methane reaches this model through the wetland prior and through agriculture and waste sitting on peat rather than through a land-use category. That is a property of the reporting, and it is why the peat methane number here cannot be checked against a national figure.

Localising the inventory halves the absolute peat contribution, to 16.3 ppb, and raises its share to 30%, because the correction falls hardest on the fugitive sector and peat emission is mostly not fugitive. Both numbers are worth carrying: the share is what a land-use argument needs, the absolute value is what a budget needs.

### 4.3 The carbon dioxide budget, and land use

![The land-use proxy.](outputs/operational/figures/map_M03_folu_proxy.png)

**Figure 5.** The land-use proxy: peat drainage weighted by land cover, and burned carbon over peat. A pattern, not a flux.

**Table 8. The modelled carbon dioxide budget at each tower, in ppm.** The share column is of the positive terms at Jambi. Biosphere uptake is a sink: it is carried as a magnitude, shown here without a sign, and it is excluded from the share column.

| Component | BKT | Jambi | Share at Jambi (%) |
| --- | --- | --- | --- |
| biosphere, respiration | +14.858 | +14.214 | 79.1 |
| biosphere, uptake (a sink) | 10.572 | 8.835 |  |
| drained peat | +0.293 | +1.507 | 8.4 |
| fossil, power industry | +0.265 | +0.949 | 5.3 |
| fossil, transport | +0.566 | +0.457 | 2.5 |
| fossil, ind combustion | +0.113 | +0.302 | 1.7 |
| fossil, fuel exploitation | +0.076 | +0.279 | 1.6 |
| fossil, ind processes | +0.098 | +0.130 | 0.7 |
| fossil, buildings | +0.086 | +0.124 | 0.7 |
| open fire | +0.002 | +0.012 | 0.1 |
| land-use fire | +0.002 | +0.010 | 0.1 |
| fossil, agriculture | +0.011 | +0.008 | 0.0 |
| fossil, waste | +0.000 | +0.001 | 0.0 |
| ocean | +-0.009 | +-0.026 | -0.1 |

Fossil emission is small here. Summed over every sector it is 1.22 ppm at Bukit Kototabang and 2.25 ppm at Jambi, against biosphere terms an order of magnitude larger in both directions: 14.2 ppm of respiration against 8.8 ppm of uptake at Jambi. The afternoon carbon dioxide signal at these towers is a biosphere signal with a fossil perturbation on it, which is the opposite of the situation an urban inversion is designed for.

Drained peat is the exception worth naming. At 1.51 ppm it is larger than every individual fossil sector at Jambi and 67% of all of them combined, while at Bukit Kototabang it is 0.29 ppm. If a single carbon dioxide question is worth asking of a lowland Sumatran tower, it is this one.

The global gridded inventory excludes land use, land-use change and forestry, which in Indonesia is the largest and most variable term, so for most of this project the model was missing its biggest component. It is now included. The reported totals come from the land-use emissions of the national statistics: drained organic soils at 241,354 Gg of carbon dioxide and land-use fires at 5,412 Gg, placed on a proxy built from peatland extent weighted by the land cover that implies how deeply it is drained, and from burned carbon split by whether it burned over peat.

Adding that column to the inversion, on the same receptors and the same biosphere prior, raises the degrees of freedom from 2.52 to 2.75 and improves the Jambi comparison while leaving Bukit Kototabang unchanged. That asymmetry is the expected one: Jambi sits on peat and the highland tower does not.

The magnitude of drained-peat emission is contested, with published factors spanning a factor of ten, so the proxy carries a pattern only and the reported total supplies the size. That is the same division of labour every other sector uses here, and it turns a disputed parameter into one the model does not need.

## 5. Testing the national inventory

### 5.1 What the country reports, against what the global inventory assumes

![Reported against global methane.](outputs/operational/figures/map_M02_inventory_change.png)

**Figure 6.** Indonesia's reported 2022 methane, allocated to provinces, divided by the global gridded inventory in the same cells. Blue is where the country reports less than the global inventory assumes.

![The inventory difference and its effect at the towers.](outputs/operational/figures/figure_O02_inventory.png)

**Figure 7.** The reported national totals against the global gridded inventory by IPCC category, and the effect on the modelled prior at each tower.

**Table 9. Indonesian methane for 2022, reported against the global gridded inventory, inside the country mask.** A factor below one means the country reports less than the global inventory assumes.

| IPCC category | Global (Gg) | Reported (Gg) | Factor |
| --- | --- | --- | --- |
| 3A+3C | 4141.4 | 3080.0 | 0.74 |
| 1B | 7542.6 | 666.0 | 0.09 |
| 2 | 3.5 | 3.7 | 1.05 |
| 1A | 215.6 | 113.0 | 0.52 |
| 4 | 2805.1 | 4760.0 | 1.70 |

SIGN-SMART, the national inventory system, reports at national, provincial and district level, and its database requires an account. Indonesia's reporting to the UNFCCC is produced from that inventory and is public, so the national totals here come from PRIMAP-hist in its country-reported scenario, which prioritises those submissions over third-party estimates. The gridded inventory supplies the pattern inside the country and the reported total supplies the magnitude, sector by sector; the country total afterwards equals the reported total by construction. Because the operator is linear in the flux, the factors apply to the per-sector responses already computed, so no footprint is re-run. The near and far columns are rescaled in the proportion the sectors imply, which assumes the sector mix beyond 500 km resembles the mix within it, and that is worth stating.

The localisation lowers the modelled methane prior at Jambi by 47% and at Bukit Kototabang by 17%, almost all of it fugitive. The prior error falls from 99.5 to 47.9 ppb. Whether the gap is the global inventory's spatial allocation, a real under-report, or a definitional difference is exactly the question a tower network exists to answer, and this is the first configuration in which the towers prefer the national numbers.

### 5.2 From a global inventory to a provincial one

**Table 10. Methane prior at three levels of locality.** Prior RMSE is how far the unadjusted prior sits from the observations; the difference columns are cross-validated, against the boundary null.

| Prior | Prior RMSE (ppb) | BKT difference | Jambi difference |
| --- | --- | --- | --- |
| global gridded inventory | 99.5 | -0.13 (-8.88 to +9.11) | +4.76 (-8.41 to +20.82) |
| national reported totals | 57.7 | -1.55 (-6.43 to +3.71) | -2.05 (-10.48 to +8.18) |
| national totals allocated to provinces | 47.9 | -1.21 (-5.56 to +3.50) | -2.13 (-10.83 to +7.92) |

Locality helps monotonically. Moving from the global gridded inventory to Indonesia's own reported national totals cuts the prior error from 99.5 to 57.7 ppb, and allocating those totals across provinces cuts it again to 47.9, a reduction of 52% overall. The provincial step matters because a national factor is not the right factor anywhere in particular: the fugitive factor is 0.09 nationally and 0.03 for Jambi, so a national correction is wrong for the province the tower actually sees by more than threefold.

The provincial split comes from facility locations rather than from the gridded inventory being corrected, which is what keeps it independent. Within one sector a facility's carbon-dioxide equivalent is proportional to the gas, so the assets supply only the share; the magnitude stays the reported total. District shares are written too, across 504 districts, but the inversion does not consume them: the footprint grid is a quarter degree and most districts are smaller than a single cell, so that resolution is below what these towers can see.

## 6. What the inversion resolves

### 6.1 What the observations informed

**Table 11. What the observations informed, at the daily scale.** Degrees of freedom count the parameters the data pinned down; a reduced chi-square near one says the error model is consistent with the residuals.

| Gas | Prior | Bins | Reduced chi-square | Degrees of freedom | Prior RMSE | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| CO₂ | global inventory, diagnostic biosphere | 78 | 0.96 | 2.52 | 8.3 | diagnostic |
| CO₂ | hybrid biosphere | 17 | 1.16 | 1.84 | 6.9 | diagnostic |
| CO₂ | with land use included | 78 | 0.96 | 2.75 | 8.4 | diagnostic |
| CH₄ | global inventory | 26 | 1.48 | 1.98 | 99.5 | diagnostic |
| CH₄ | national reported inventory | 26 | 1.40 | 1.76 | 57.7 | diagnostic |
| CH₄ | provincial reported inventory | 26 | 1.39 | 1.60 | 47.9 | diagnostic |

Across the configurations the observations inform between 1.60 and 2.75 parameters, and every reduced chi-square sits near one, so the error model is consistent with the residuals it produces. A bulk regional scaling is constrained. What is not constrained is anything finer: with fewer than three degrees of freedom across four to five source components there is no separating a sector from its neighbour, and the multipliers should be read as one adjustment, not several.

### 6.2 Skill against the boundary null

![Every configuration against the null.](outputs/operational/figures/figure_O04_scoreboard.png)

**Figure 8.** Cross-validated difference from the boundary null with a 95% date-block bootstrap interval, at the daily scale, for every configuration the campaign ran. Negative favours the inversion.

**Table 12. Cross-validated error against the boundary null, daily scale.** Negative favours the inversion. Units are ppm for carbon dioxide and ppb for methane, so compare within a gas.

| Gas | Prior | Receptor | Posterior | Background | Difference |
| --- | --- | --- | --- | --- | --- |
| CO₂ | global inventory, diagnostic biosphere | Bukit Kototabang | 3.07 | 2.78 | +0.28 (+0.02 to +0.57) |
| CO₂ | global inventory, diagnostic biosphere | Jambi | 5.69 | 5.44 | +0.24 (-0.10 to +0.59) |
| CO₂ | hybrid biosphere | Bukit Kototabang | 4.24 | 3.81 | +0.43 (-0.41 to +1.45) |
| CO₂ | hybrid biosphere | Jambi | 4.96 | 4.51 | +0.45 (-0.57 to +1.22) |
| CO₂ | with land use included | Bukit Kototabang | 3.11 | 2.78 | +0.33 (+0.04 to +0.65) |
| CO₂ | with land use included | Jambi | 5.62 | 5.44 | +0.17 (-0.28 to +0.51) |
| CH₄ | global inventory | Bukit Kototabang | 38.53 | 38.65 | -0.13 (-8.88 to +9.11) |
| CH₄ | global inventory | Jambi | 41.93 | 37.17 | +4.76 (-8.41 to +20.82) |
| CH₄ | national reported inventory | Bukit Kototabang | 37.10 | 38.65 | -1.55 (-6.43 to +3.71) |
| CH₄ | national reported inventory | Jambi | 35.12 | 37.17 | -2.05 (-10.48 to +8.18) |
| CH₄ | provincial reported inventory | Bukit Kototabang | 37.44 | 38.65 | -1.21 (-5.56 to +3.50) |
| CH₄ | provincial reported inventory | Jambi | 35.04 | 37.17 | -2.13 (-10.83 to +7.92) |

Only one configuration puts both towers on the right side of the null: methane with the prior localised to the reported national inventory, at -1.21 ppb at Bukit Kototabang and -2.13 at Jambi, against -0.13 and +4.76 with the global inventory. The Jambi difference changes sign. Every interval still spans zero, so nothing here is resolved at 95%, and the readiness gate says so rather than quoting the point estimate as a result.

### 6.3 What the posterior implies, and what could be detected

**Table 13. Methane multipliers, the emission they imply over the four provinces the towers see, and the change each parameter could detect.** The detectable change is twice the posterior standard deviation in log space, so it is the fractional change that would sit at the edge of a 95% interval. Emission columns are omitted for parameters with no inventory total behind them.

| Prior | Parameter | Multiplier (95%) | Detectable (%) | Prior (Gg/yr) | Posterior (Gg/yr) |
| --- | --- | --- | --- | --- | --- |
| global | anthro near | 0.25 (0.11 to 0.47) | 74 | 7,088 | 1,782 (768 to 3,302) |
| global | anthro far | 0.56 (0.19 to 1.33) | 100 | 7,088 | 3,933 (1,321 to 9,409) |
| global | wetlands | 0.34 (0.15 to 0.58) | 69 |  |  |
| global | fire | 0.96 (0.25 to 3.50) | 134 |  |  |
| reported, national | anthro near | 0.47 (0.18 to 0.89) | 81 | 573 | 266 (104 to 508) |
| reported, national | anthro far | 0.75 (0.22 to 2.07) | 114 | 573 | 430 (126 to 1,184) |
| reported, national | wetlands | 0.31 (0.13 to 0.56) | 73 |  |  |
| reported, national | fire | 0.94 (0.25 to 3.42) | 134 |  |  |
| reported, provincial | anthro near | 0.61 (0.22 to 1.24) | 88 | 573 | 349 (125 to 710) |
| reported, provincial | anthro far | 0.84 (0.24 to 2.46) | 119 | 573 | 482 (137 to 1,410) |
| reported, provincial | wetlands | 0.33 (0.14 to 0.58) | 72 |  |  |
| reported, provincial | fire | 0.96 (0.25 to 3.61) | 136 |  |  |

**Table 14. The same for carbon dioxide.** The emission column for the fossil parameters is the global gridded inventory over those four provinces; for land use it is the reported drained-peat total.

| Prior | Parameter | Multiplier (95%) | Detectable (%) | Prior (Gg/yr) | Posterior (Gg/yr) |
| --- | --- | --- | --- | --- | --- |
| global | fossil near | 0.54 (0.20 to 1.10) | 88 | 57,429 | 30,764 (11,304 to 63,072) |
| global | fossil far | 0.61 (0.20 to 1.52) | 103 | 57,429 | 35,067 (11,511 to 87,226) |
| global | bio net BKT | 0.14 (0.07 to 0.25) | 67 |  |  |
| global | bio net JMB | 0.16 (0.07 to 0.29) | 72 |  |  |
| hybrid biosphere | fossil near | 0.62 (0.20 to 1.50) | 102 | 57,429 | 35,885 (11,635 to 86,007) |
| hybrid biosphere | fossil far | 0.83 (0.23 to 2.65) | 124 | 57,429 | 47,861 (13,334 to 152,310) |
| hybrid biosphere | bio net BKT | 0.45 (0.16 to 0.93) | 89 |  |  |
| hybrid biosphere | bio net JMB | 0.45 (0.17 to 0.91) | 85 |  |  |
| global, with land use | fossil near | 0.51 (0.19 to 1.05) | 88 | 57,429 | 28,988 (10,686 to 60,329) |
| global, with land use | fossil far | 0.61 (0.20 to 1.50) | 104 | 57,429 | 34,996 (11,191 to 86,197) |
| global, with land use | bio net BKT | 0.14 (0.07 to 0.25) | 68 |  |  |
| global, with land use | bio net JMB | 0.17 (0.07 to 0.30) | 71 |  |  |
| global, with land use | folu drainage | 1.16 (0.31 to 3.13) | 118 | 102,067 | 118,624 (31,664 to 319,120) |

A multiplier is dimensionless and applies where the footprint has weight, so it is quoted here over the four provinces the towers see rather than nationally. Scaling a national total by the same multiplier would assume the correction holds in provinces neither tower can see, which is exactly what the readiness gate refuses to certify.

Read that way, the near-field methane posterior is 349 Gg per year across those four provinces, with a 95% interval of 125 to 710 Gg, against a reported prior of 573 Gg. Starting instead from the global gridded inventory the same fit gives 1782 Gg from a prior of 7088 Gg. The two posteriors differ by an order of magnitude because the two priors do, which is the cleanest possible measure of how much of the answer the prior is still supplying. Neither interval excludes its own prior, so neither is a flux estimate.

One comparison in this table is resolved, and it is not the one the readiness gate tests. The near-field methane multiplier excludes one at 95% under the global gridded inventory (0.25, 0.11 to 0.47) and under the reported national totals (0.47, 0.18 to 0.89), and stops excluding it once the totals are allocated to provinces (0.61, 0.22 to 1.24). Read plainly: under the stated error model the observations reject the global inventory's magnitude in the region they can see, and they stop rejecting it when Indonesia's own provincial figures set that magnitude. This is a statement about the prior, conditional on the error model and on the log-normal width assumed for the multiplier. It is not the same test as Section 6.2, which asks whether the fitted posterior predicts a withheld day better than a fitted boundary field, and which nothing passes.

The detection limit is the more useful operational number, because it does not depend on the prior being right. No parameter in the campaign is constrained better than 67%, the best being bio net BKT, and the near-field methane term stands at 88%. A change in emission smaller than about a factor of two therefore cannot be seen by this network, however long it runs, unless the transport error falls. That is the number to quote when asked whether the towers can verify a mitigation commitment: not yet, and by a stated margin.

### 6.4 Why the verdict is what it is

![The error budget.](outputs/operational/figures/figure_O01_error_budget.png)

**Figure 9.** Variance of the modelled source signal at the receptors against the error it must compete with, by gas.

**Table 15. The error budget at the receptors.** What the modelled source signal has to compete with.

| Gas | Source signal | Transport | Measurement and local | Background | Total | Signal to error |
| --- | --- | --- | --- | --- | --- | --- |
| CO₂ | 6.54 ppm | 4.35 | 2.01 | 1.00 | 4.90 | 1.34 |
| CH₄ | 73.11 ppb | 56.34 | 20.62 | 10.00 | 60.82 | 1.20 |

The source signal is barely above the noise it arrives through: a ratio of 1.34 for carbon dioxide and 1.20 for methane, with transport the largest error term for both. That single fact explains the rest of this report. It is why the posterior loses to a fitted constant, why a model with no source terms at all can beat one with them, and why four times the sample did not rescue the carbon dioxide result. A regional inversion begins to constrain fluxes near a ratio of three.

### 6.5 Does the transport ensemble need re-running?

The runs are sound, and repeating them unchanged would gain nothing. The seed-to-seed spread is 4.7 ppb, 3.2% of the modelled signal, while the residuals require about 56 ppb of transport error. The particle sampling therefore explains roughly 8% of the error that matters, so more particles or more seeds would shrink the part that is already small.

The rest is systematic: wind-field error in the driving meteorology and representation error on a quarter-degree grid. Neither is reduced by re-running with the same meteorology. Particle retention supports this reading: the median receptor keeps every particle for the full 120 hours, and the 22 receptors below the retention screen are excluded rather than corrected. Release height was tested at 100, 150 and 300 m and changed the out-of-sample error by at most 0.10 ppm.

The one run worth doing is a different one: the same receptors driven by a second meteorological product, so the systematic error can be measured from the spread between drivers instead of calibrated from the residuals. That needs no new model, only a second archive.

### 6.6 The carbon dioxide biosphere prior

![The three biosphere priors.](outputs/operational/figures/figure_O03_biosphere.png)

**Figure 10.** Afternoon net flux and diurnal amplitude at the tower cells for the diagnostic prior, the assimilated flux and the hybrid.

The biosphere carries 94% of the modelled carbon dioxide signal, so it, not the emission inventory, is what limits that gas. Two sources exist and each fails differently, so the prior takes from each what it is good at.

CarbonTracker is assimilated, so its magnitude and seasonality carry real information, but its sub-daily phase inverts for a week over both tower cells. The diagnostic prior cannot invert, but the inversion scaled it to 0.14 at Bukit Kototabang and 0.16 at Jambi, so its amplitude was several times too large. A daily mean is insensitive to a phase error and a diurnal shape is insensitive to a magnitude error, so the hybrid takes the daily mean and the diurnal amplitude from CarbonTracker, measured only on days when its own phase is sound, and the shape from the diagnostic model.

The hybrid reproduces the CarbonTracker daily mean to 3e-15 µmol m⁻² s⁻¹ and cuts inverted-phase cell days from 201,374 to 520. The afternoon drawdown at the towers falls from -13.5 and -15.4 to -5.5 and -5.2 µmol m⁻² s⁻¹, which is where the inversion's own multipliers had independently implied it should be. Two separate routes reached the same amplitude.

It did not improve the skill. On identical receptors the hybrid is better at one tower and worse at the other, neither resolved, and the prior error barely moves. The biosphere prior was demonstrably wrong and is now demonstrably better; that was necessary and it was not sufficient.

## 7. What is operational and what is diagnostic

Operational today: the station monitor, the episode transport driver, the dataset registry and the readiness harness. Those run routinely, at any station, and produce products whose caveats are stated with them.

Diagnostic, not operational: the inversion as a predictor of concentration. It informs one to two flux parameters with a consistent error model, and it does not beat a fitted boundary field. Reporting its multipliers as validated flux corrections would repeat an error this project has already corrected twice, once for each gas.

The localised methane inventory is worth operating on its own account, whatever the inversion does with it. It is Indonesia's own reported inventory placed on a gridded pattern with conserved mass and a provenance ledger, and it is a better prior than the global default whether or not the towers can yet resolve the difference.

## 8. What would change the verdict

The error budget names the constraint: transport, not priors. Cutting the transport error by three to four would take the signal-to-error ratio from about 1.3 to about 4, which is where a regional inversion starts to constrain fluxes. Section 6.5 is specific about how: not more seeds, which would only shrink the part of the error that is already small, but the same receptors driven by a second meteorological product, so the systematic part can be measured from the spread between drivers instead of calibrated from the residuals. That needs a second public archive and no new model.

Two cheaper things also help. More independent bins: eight weekly bins at both towers needs roughly two more months of joint record, and the record is still growing. And a provincial rather than national inventory: the towers are sensitive to four provinces, and a national factor spreads a correction evenly over places the towers cannot see.

What will not change the verdict is more work on the priors for carbon dioxide. The biosphere carries 94% of that signal, the prior for it is now demonstrably better, and the skill did not move.

## 9. Reproducing this

**Table 16. Where each part of the operational system writes its evidence.**

| Component | Evidence |
| --- | --- |
| the station monitor | `outputs/operational/episodes.csv` |
| the episode transport driver | `outputs/operational/transport_plan.csv` |
| cross-validated scoring | `outputs/tables/ch4_cv_skill.csv` |
| the operational inversion and its readiness verdict | `outputs/operational/inversion_readiness.json` |
| the localisation engine and its ledger | `outputs/inventory/local_inventory_ch4_2022_primap_ledger.csv` |
| the land-use proxy | `outputs/inventory/folu_proxy_indonesia.nc` |
| the prior audit | `outputs/operational/prior_audit.csv` |
| the hybrid biosphere prior | `outputs/operational/biosphere_prior_hybrid_report.json` |
| the dataset registry | `outputs/operational/dataset_registry.csv` |
| the source attribution, all eight tables | `outputs/operational/attribution_budget.csv` |
| the peatland decomposition | `outputs/operational/attribution_peat.csv` |
| the posterior flux and detection limit | `outputs/operational/attribution_flux.csv` |
| the maps | `outputs/operational/figures/map_M01_footprints.pdf` |

## Appendix A. Questions these results answer

These are the 75 questions the evidence in this report answers, with the answer and the table or section it comes from. Every number is read from the same files the sections use, so an answer here cannot drift from the table it was drawn from. Where an answer says the result is not resolved, that is the finding, not a hedge.

### What arrived at the towers

**Q1. How much methane above the modelled background arrives at each tower on a typical screened afternoon?**

56 ppb at Bukit Kototabang and 47 ppb at Jambi, against afternoon means of 1988 and 2006 ppb. (Table 2)

**Q2. How variable is that record?**

The screened afternoon methane spans 192 ppb at Bukit Kototabang and 132 ppb at Jambi, with standard deviations of 50 and 37 ppb. (Table 2)

**Q3. Does the prior predict the right amount of methane?**

No. The modelled source signal is 2.0 times the observed enhancement at Bukit Kototabang and 3.1 times at Jambi, so the global gridded prior puts two to three times too much methane into the air the towers sample. (Table 2)

**Q4. Which tower is noisier, and why does it matter?**

Jambi. It sits in the lowland with sources close by, so a single receptor carries more local variance; its screened record is also shorter, 13 usable afternoons against 41, which is why its bootstrap intervals are roughly twice as wide. (Tables 2 and 12)

**Q5. What does the carbon dioxide record look like on the same afternoons?**

Afternoon means of 419.5 ppm at Bukit Kototabang and 422.3 ppm at Jambi, sitting 4.5 and 2.6 ppm below the modelled background, because afternoon photosynthesis draws the boundary layer down. (Table 2)

**Q6. How many receptors does the whole analysis rest on?**

54 screened methane afternoons in 2023 and 135 carbon dioxide afternoons across 2023 and 2024, after screening for particle retention, mixing depth and carbon-dioxide-only spikes. (Table 2)

**Q7. Why are night hours excluded?**

A quarter-degree footprint cannot carry the shallow nocturnal layer the night observations sit in. Fitting those hours drives the error model to its cap and returns every multiplier to its prior, so they are screened out rather than modelled badly. (Section 2.1)

**Q8. Is the error model consistent with the residuals it produces?**

Yes. The reduced chi-square runs from 0.96 to 1.48 across every configuration, so the stated uncertainties are neither optimistic nor padded. (Table 11)

### Where the air came from

**Q9. How far away are the sources each tower sees?**

At Bukit Kototabang 53% of the modelled anthropogenic methane is emitted within 50 km; at Jambi only 29%, with 40% coming from 200 to 500 km away. (Table 3)

**Q10. How old is the air carrying the signal?**

The median sensitivity age is 30 hours at Bukit Kototabang and 49 hours at Jambi, so Jambi is sampling air that has been over land for two days on average. (Table 3)

**Q11. How much of the signal is older than three days?**

20% at Bukit Kototabang and 31% at Jambi. That part of the signal depends on the boundary field as much as on the inventory. (Table 3)

**Q12. Which province does each tower mostly see?**

Bukit Kototabang draws 72% of its modelled methane signal from Sumatera Barat; Jambi draws 46% from Jambi and 28% from Sumatera Selatan. (Table 4, Figure 2)

**Q13. How many provinces can this network constrain at all?**

Four. Sumatera Barat, Jambi, Sumatera Selatan and Riau each carry at least one percent of a tower's signal, and no province outside Sumatra reaches one percent at either tower. (Table 4, Figure 2)

**Q14. Are the two towers redundant?**

No, but they are not independent either. Bukit Kototabang is dominated by its own province while Jambi spreads across three, and Riau is common to both, so the pair constrains a larger region than either alone but their errors are correlated through the same synoptic flow. (Figures 1 and 2)

**Q15. Which districts carry the signal?**

Agam carries 53% at Bukit Kototabang, its own district; the next is Muara Enim at 8.3%. At Jambi the leader is Tanjung Jabung Barat at 18%. (Table 5, Figure 3)

**Q16. Where would an inventory error hurt most?**

In Muara Enim, which carries 8.3% of the Bukit Kototabang methane signal from 0.02% of its footprint sensitivity. A concentration that extreme means one or two grid cells of the gridded inventory set a large part of the modelled signal. (Table 5, Figure 3)

**Q17. Does either tower see Java, Kalimantan or eastern Indonesia?**

Not measurably. No province outside Sumatra reaches one percent of either tower's modelled methane signal, so national conclusions cannot be drawn from this pair. (Table 4, Figure 2)

### What emits the methane

**Q18. Which sector dominates the modelled methane signal at Jambi?**

Fugitive emissions from fuel exploitation, 62% of the modelled source signal at 93 ppb, under the global gridded inventory. (Table 6)

**Q19. And at Bukit Kototabang?**

Natural wetlands, 48%, followed by agriculture at 27% and fugitive emissions at 14%. (Table 6)

**Q20. How much of the methane signal is natural rather than anthropogenic?**

53% at Bukit Kototabang and 21% at Jambi, counting wetlands, termites and geological seepage. No national inventory carries any of it. (Table 6)

**Q21. How large is the waste sector in what the towers see?**

11% of the Jambi signal and 4% at Bukit Kototabang under the global inventory. It is one of only two sectors Indonesia reports higher than the global inventory assumes. (Tables 6 and 9)

**Q22. How much does agriculture contribute?**

32 ppb at Bukit Kototabang, its largest anthropogenic term, and 8 ppb at Jambi. Rice and livestock dominate the category nationally. (Table 6)

**Q23. Does soil uptake matter?**

Marginally. Soil oxidation removes 1.9 ppb at Bukit Kototabang and 1.1 ppb at Jambi, one to two percent of the source terms, and it is subtracted rather than fitted. (Table 6)

**Q24. How much methane comes from fire?**

0.9 ppb at Jambi and 1.7 ppb at Bukit Kototabang from open burning, plus 0.32 and 0.10 ppb from the reported land-use fire category. These are 2023 receptors outside a major burning year, so the figure is not a haze-season one. (Tables 6 and 7)

**Q25. What does the reported national inventory do to the sector picture?**

It collapses the fugitive term. At Jambi fuel exploitation falls from 93 to 3.0 ppb, and waste becomes the largest reported anthropogenic term at that tower. (Table 6)

**Q26. Which sector should an inventory improvement target first?**

Fugitive methane in Riau, Jambi and South Sumatra. It is the largest term in the global inventory at Jambi, the largest disagreement with the reported inventory, and it sits where both towers have sensitivity. (Tables 6 and 9, Figure 6)

**Q27. Do the towers see enough to separate sectors?**

No. The observations inform 1.6 to 2.7 parameters, so the multipliers must be read as one bulk adjustment and not as sector-by-sector corrections. (Table 11)

### Peatland

**Q28. How much of the methane arriving at Jambi comes from peatland?**

34.3 ppb of the 147.5 ppb modelled source signal, 23%, rising to 95 ppb on the most peat-influenced afternoon in the record. (Table 7, Figure 4)

**Q29. Does that hold once the inventory is localised to the reported national figures?**

The absolute contribution halves to 16.3 ppb, but the share rises to 30%, because localisation cuts the fugitive term far harder than it cuts anything emitted on peat. (Table 7)

**Q30. By what route does peat methane reach the tower?**

Three. Anthropogenic emission sitting on drained peatland contributes 23.1 ppb, biological emission from peat swamp 10.8 ppb through the wetland prior, and fire 0.4 ppb. (Table 7, Figure 4)

**Q31. What fraction of the wetland methane at Jambi is emitted over peat?**

43%, against 4% at Bukit Kototabang. Peat swamp is the dominant Indonesian wetland, so the wetland prior is largely a peat prior at this tower. (Table 7)

**Q32. How much of the peatland signal reaches the highland tower?**

3.3 ppb, 2.9% of its source signal, against 23% at Jambi. The two towers are not sampling the same land surface. (Table 7)

**Q33. Is the peat signal a transport effect or an emission effect?**

Both, and they can be separated. Peat cells carry 9% of the Jambi footprint sensitivity but 23% of the signal, so per unit of sensitivity peat is emitting about 2.9 times what the rest of the land in the footprint emits. At Bukit Kototabang the two shares are 2.5% and 2.9%, close to parity. (Table 7)

**Q34. Does Indonesia report methane from drained peat?**

No. The national land-use reporting covers carbon dioxide and nitrous oxide from drained organic soils; the methane land-use category is fire only. Drained-peat methane therefore reaches the model through the wetland prior and through agriculture and waste sitting on peat, not through a land-use category. (Section 4.2)

**Q35. What does drained peat do to the carbon dioxide budget?**

It is the third largest positive term at Jambi, 1.51 ppm, 8% of the positive signal and larger than every fossil sector except power. At Bukit Kototabang it is 0.29 ppm. (Table 8, Figure 5)

**Q36. Can the inversion measure the drained-peat term?**

Not yet. The multiplier is 1.16 with a 95% interval of 0.31 to 3.13, consistent with the prior and with anything between a third and three times it. (Table 14)

**Q37. Why is the peat magnitude taken from the reported total rather than an emission factor?**

Because published drained-peat emission factors span a factor of ten, from 8.13 to 80.77 Mg carbon dioxide per hectare per year across land covers and water tables. The proxy therefore carries a spatial pattern only and the reported national total supplies the size. (Section 2.3, Figure 5)

### Carbon dioxide

**Q38. What dominates the carbon dioxide signal?**

The terrestrial biosphere, 94% of the modelled variance, which no national inventory carries. Fossil emission is a few percent. (Table 8)

**Q39. How large is the fossil term at each tower?**

1.22 ppm at Bukit Kototabang and 2.25 ppm at Jambi, summed over all sectors. (Table 8)

**Q40. Which fossil sector is largest?**

Transport at Bukit Kototabang (0.57 ppm) and power generation at Jambi (0.95 ppm). (Table 8)

**Q41. How much carbon does the biosphere take up on a screened afternoon?**

10.6 ppm equivalent of uptake at Bukit Kototabang and 8.8 ppm at Jambi, against respiration of 14.9 and 14.2 ppm. (Table 8)

**Q42. Was the biosphere prior right?**

No, and it is now better. The inversion scaled the diagnostic biosphere to 0.14 at Bukit Kototabang and 0.16 at Jambi, so its amplitude was several times too large. The hybrid prior, built from CarbonTracker's magnitude and the diagnostic phase, brings the afternoon drawdown to where the inversion had independently implied it should be. (Section 6.6, Figure 10)

**Q43. Did fixing the biosphere prior improve the result?**

No. On identical receptors the hybrid is better at one tower and worse at the other, the prior error barely moves, and the degrees of freedom fall from 2.52 to 1.84 because the shorter hybrid window has fewer bins. The prior was demonstrably wrong and is now demonstrably better; that was necessary and not sufficient. (Section 6.6)

**Q44. Did adding land use help the carbon dioxide inversion?**

Yes, in information if not in skill. Degrees of freedom rise from 2.52 to 2.75 and the Jambi comparison improves, while Bukit Kototabang is unchanged. Jambi sits on peat and the highland tower does not. (Table 11)

**Q45. Why does carbon dioxide look harder than methane here?**

Because its signal-to-error ratio is 1.34 and most of the signal is a biosphere term with no inventory to test against, so there is no equivalent of the inventory localisation that moved the methane result. (Table 15)

### The national inventory

**Q46. How does Indonesia's reported methane compare with the global gridded inventory?**

Indonesia reports 666 Gg of fugitive methane for 2022 where the global inventory puts 7543 Gg inside the country, a factor of 11, and 4760 Gg of waste methane where the global inventory puts 2805. (Table 9, Figure 6)

**Q47. Which categories does the country report lower, and which higher?**

Lower for fugitive emissions (factor 0.09), stationary and mobile energy (0.52) and agriculture (0.74); higher for waste (1.70). (Table 9)

**Q48. Does localising the inventory make the prior better?**

Yes, monotonically. The prior error falls from 99.5 ppb with the global gridded inventory to 57.7 with reported national totals and 47.9 with those totals allocated to provinces, a reduction of 52%. (Table 10)

**Q49. Why does the provincial step matter beyond the national one?**

Because a national factor is not the right factor anywhere in particular. The fugitive factor is 0.09 nationally and 0.03 for Jambi, so a national correction is wrong by more than threefold for the province the tower actually sees. (Table 10)

**Q50. Where does the provincial split come from?**

Facility locations, not from the gridded inventory being corrected, which is what keeps it independent. Within a sector a facility's carbon-dioxide equivalent is proportional to the gas, so the asset data supply only the share and the reported total supplies the magnitude. (Section 5.2)

**Q51. Are district-level shares usable?**

Not by this inversion. They are written for 504 districts, but a quarter-degree footprint cell is larger than most Indonesian districts, so district numbers attribute the prior rather than estimate emission. (Table 5, Figure 3)

**Q52. Do the towers prefer the national numbers or the global inventory?**

The national numbers, at both towers. The cross-validated difference from the boundary null at Jambi moves from +4.76 ppb with the global inventory to -2.13 with the provincial prior, and at Bukit Kototabang from -0.13 to -1.21. It is the only configuration that puts both towers on the favourable side. (Table 10, Figure 8)

**Q53. Is that a measurement of the inventory being wrong?**

No. Every interval still spans zero, so the preference is a direction, not a resolved result. Whether the gap is the global inventory's spatial allocation, a real under-report, or a definitional difference is exactly the question a denser network exists to answer. (Tables 9 and 10)

**Q54. Does the inventory include land use?**

The global gridded inventory does not, which in Indonesia removes the largest and most variable term. The land-use proxy built here restores it, with reported national totals of 241,354 Gg of carbon dioxide from drained organic soils and 5,412 Gg from land-use fires. (Section 2.3, Figure 5)

### What the inversion resolves

**Q55. Does the inversion beat a fitted boundary field?**

Not at any scale with enough independent bins to test. No configuration of the eighteen run reports operational, and none is resolved at 95%. (Tables 11 and 13, Figure 8)

**Q56. Which configuration comes closest?**

Methane with its prior localised to the reported inventory. It is the only one that puts both towers on the favourable side of the null, and the Jambi comparison changes sign relative to the global inventory. (Table 10, Figure 8)

**Q57. How many parameters do the observations actually inform?**

Between 1.60 and 2.75. A bulk regional scaling is constrained; nothing finer is. (Table 11)

**Q58. What emission does the posterior imply for the region the towers see?**

With the provincial reported prior, 349 Gg of methane per year across the four provinces, with a 95% interval of 125 to 710 Gg against a prior of 573 Gg. The interval spans the prior, so this is a consistency statement and not a flux estimate. (Table 13)

**Q59. What does the same calculation give starting from the global inventory?**

1782 Gg per year, 768 to 3302, from a prior of 7088 Gg. The two posteriors differ by an order of magnitude, which is the measure of how much the prior still decides the answer. (Table 13)

**Q60. How large an emission change could this network detect?**

Nothing below 67%, and more commonly a factor of two. The best constrained parameter across the campaign is bio net BKT; the near-field methane term is 88% and the wetland term 72%. An emission change smaller than that cannot be seen by this network however long it runs at two towers. (Table 13)

**Q61. Is any multiplier inconsistent with its prior?**

Yes. 11 of 25 fitted parameters exclude one at 95%: both biosphere directions, the wetland term, and the near-field anthropogenic methane term under the global and the national priors (0.25, 0.11 to 0.47). Under the provincial prior it no longer does (0.61, 0.22 to 1.24). The observations reject the global inventory's magnitude in the region they see and stop rejecting it once the reported provincial totals set it. (Table 13)

**Q62. Why does the inversion lose to a fitted constant?**

Because the source signal is barely above the noise it arrives through: a signal-to-error ratio of 1.34 for carbon dioxide and 1.20 for methane, with transport the largest error term for both. A regional inversion begins to constrain fluxes near three. (Table 15, Figure 9)

**Q63. How large is the transport error?**

56 ppb for methane and 4.35 ppm for carbon dioxide, against source signals of 73 ppb and 6.54 ppm. (Table 15)

**Q64. Would more particles or more seeds help?**

No. The seed-to-seed spread is about three percent of the modelled signal and explains under a tenth of the transport error the residuals require. The rest is wind-field and representation error, which re-running the same meteorology cannot reduce. (Section 6.5)

**Q65. What would reduce it?**

The same receptors driven by a second meteorological product, so the systematic part can be measured from the spread between drivers rather than calibrated from the residuals. That needs a second public archive and no new model. (Section 8)

**Q66. Are the reported fits sampled or approximated?**

Sampled. Every reported fit is a Markov chain accepted only with R-hat at most 1.01 and an effective sample size above 1,000; the smallest effective sample across the campaign is 1750. The Laplace approximation is kept only inside the cross-validation loop, where nothing but the mode is used. (Section 2.4)

### Operating the system

**Q67. What can be operated today?**

The station monitor, the episode transport driver, the dataset registry and the readiness harness. All four run routinely, at any station whose record loads, and produce products whose caveats are stated with them. (Section 7)

**Q68. What cannot?**

The inversion as a predictor of concentration. It informs one to two flux parameters with a consistent error model and does not beat a fitted boundary field, so its multipliers are not validated flux corrections. (Section 7)

**Q69. Is the localised inventory worth operating on its own?**

Yes. It is Indonesia's own reported inventory placed on a gridded pattern with conserved mass and a provenance ledger, and it is a better prior than the global default whether or not the towers can resolve the difference. (Section 7)

**Q70. What does the readiness harness actually check?**

Four gates: enough independent bins, a consistent chi-square, at least one degree of freedom informed, and a cross-validated improvement on the boundary null somewhere. A run that fails any of them cannot be reported as a finding. (Section 2.5)

**Q71. Are all the input datasets verified?**

Yes. All 17 declared datasets validate, 15 of them required, each confirmed against its provenance record and checked for variable, unit, grid, time span and physical range. (Table 1)

**Q72. Can the system run at a station other than these two?**

Yes. The monitor needs only the harmonized hourly archive, and the transport driver plans, fetches, runs and convolves footprints for any station at its own inlet height, with the cost priced before the run is committed. Inlet heights of 30 m are already configured for Kemayoran, Bariri and Sorong. (Section 7)

**Q73. What would make the inversion operational?**

A transport error three to four times smaller, which takes the signal-to-error ratio from about 1.3 to about 4. Two cheaper improvements also help: more independent bins, which needs roughly two more months of joint record, and a provincial rather than national inventory, which is already in place. (Section 8)

**Q74. What should not be attempted again?**

More work on the carbon dioxide priors. The biosphere carries most of that signal, its prior is now demonstrably better, and the skill did not move. The constraint is transport, not priors. (Section 8)

**Q75. Where does every number in this report come from?**

A CSV or JSON written by a named script, listed in the final table. The report is rebuilt from those files and refuses to build if a claim in the prose no longer holds against them. (Table 16)

