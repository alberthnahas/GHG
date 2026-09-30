# Carbon dioxide and methane over Sumatra, seen from two towers

## Scientific summary

{{P_SUMMARY}}

## 1. What this report answers

{{P_INTRO}}

The evidence is organised so that each question has one place to look. Section 3 is about transport: what air reaches the towers, from how far, how old, and over which provinces. Section 4 is about sources: which sector, which land surface, and how much of it is peat. Section 5 tests the national inventory against the global gridded one. Section 6 asks what the inversion itself resolves, and answers, honestly, that it resolves a bulk scaling and nothing finer. Appendix A puts {{P_QUESTION_COUNT}} of these questions in one list with their answers and the table each one comes from.

## 2. Observations, transport and priors

### 2.1 Sites, record and screening

Bukit Kototabang sits at 865 m on the Sumatran highland spine; Jambi sits in the eastern lowland, 380 km away across the peat basin. Receptors are afternoon hours, 12 to 14 WIB, at both towers. Night hours are excluded at both: a quarter-degree footprint cannot carry the shallow nocturnal layer the observations sit in, and fitting those hours drives the error model to its cap and returns every multiplier to its prior. Hours are further screened for particle retention, for a modelled mixing depth of at least {{P_MIN_PBLH}} m, and for carbon-dioxide-only spikes.

### 2.2 Transport

Footprints are HYSPLIT in STILT mode, 120 hours backward, 2000 particles, three seeds, on a quarter-degree grid driven by GFS 0.25 degree meteorology. A footprint is a sensitivity of the receptor mole fraction to surface flux; it is not emission and it is not attribution. Convolving it with a flux field gives what the model says should arrive, which is the quantity every attribution in Sections 3 and 4 reports.

### 2.3 Priors

Methane takes its anthropogenic prior from a global gridded inventory, its wetland prior from a process model, and its fire, termite, geological and soil-uptake terms from published fields. Carbon dioxide takes fossil emission from the gridded inventory, the biosphere from a hybrid prior described in Section 6.6, and ocean and fire from an assimilated product.

Two terms do not come ready-made. The first is the land-use term, which the global gridded inventory excludes and which in Indonesia is the largest and most variable part of the national total. It is rebuilt here as a spatial proxy: peatland extent weighted by the land cover that implies how deeply it is drained, and burned carbon split by whether it burned over peat. The magnitude problem is deliberately not solved in the proxy, because published emission factors for drained tropical peat span a factor of ten, from 8.13 to 80.77 Mg carbon dioxide per hectare per year across land covers and water tables. The proxy therefore carries a pattern and the reported national total supplies the size.

The second is locality. The gridded inventory supplies the pattern inside the country and Indonesia's own reported total supplies the magnitude, sector by sector and then province by province, so the country total equals the reported total by construction. Section 5 is the test of whether that helps.

### 2.4 The inversion and its error model

Multipliers on the source components are positive with log-normal priors; biosphere response columns are signed, because uptake reduces the mole fraction. Offsets, trends and covariate coefficients are Gaussian. The error model combines a measurement allowance, a local mismatch, a correlated background term, and a transport error whose shape comes from the measured seed spread at each receptor and whose amplitude is calibrated to a training reduced chi-square of one.

That calibrated amplitude is itself a finding: {{P_TRANSPORT_AMPLITUDE}}

A bin mean of several receptors carries less independent error than a single receptor, so the measurement and local terms are divided by the number averaged. The background term is not, because a boundary bias is common to the hours in a bin and does not average away.

The reported fit is sampled by Markov chain and accepted only with R-hat at most 1.01 and an effective sample size of at least 1,000. A maximum-posterior fit with a Laplace covariance is about a thousand times faster and its modes agree to within {{P_MODE_AGREEMENT}}, but in log space its intervals put the upper bound {{P_TAIL_ERROR}} too high, which would flow into the uncertainty ratio and the degrees of freedom and make the data look less informative than they are. The approximation is therefore kept only inside the cross-validation loop, where nothing but the mode is used.

### 2.5 Scoring, and the readiness gate

Each configuration is fitted and scored at three aggregation scales. A scale with fewer than {{P_MIN_BINS}} independent bins is declared unresolved rather than quoted. Cross-validation refits without each bin and predicts it, and the difference from a null model, the same boundary field carrying a fitted offset and trend, is bootstrapped by resampling whole dates. Four gates decide whether a run may be presented as a finding: enough independent bins, a consistent chi-square, at least one degree of freedom informed, and a cross-validated improvement on the null somewhere.

An operational model cannot treat its inputs as an assumption either. Every dataset is declared, confirmed against its provenance record, opened and validated for variable, unit, grid, time span and physical range, and checked for compatibility with the operator grid and the study windows (Table 1).

{{P_DATASET_TABLE}}

{{P_DATASET_VERDICT}}

## 3. What the towers see

### 3.1 The record

{{P_RECORD_TABLE}}

{{P_RECORD_TEXT}}

### 3.2 Where the air comes from, and how old it is

![Mean footprints at both towers.]({{P_FIG}}/map_M01_footprints.png)

**Figure 1.** Mean 120-hour HYSPLIT-STILT surface footprint over the screened receptors at each tower. Cells below the 60th percentile of positive sensitivity are masked; each panel states how much sensitivity the coloured area carries.

{{P_DISTANCE_TABLE}}

{{P_DISTANCE_TEXT}}

### 3.3 Which provinces the network can constrain

![Provincial share of the modelled methane signal.]({{P_FIG}}/map_M04_province_influence.png)

**Figure 2.** Provincial emission weighted by the mean footprint, methane, anthropogenic and natural terms together, for each tower.

{{P_PROVINCE_TABLE}}

{{P_PROVINCE_TEXT}}

### 3.4 Districts, and where an inventory error would hurt

![District share of the modelled methane signal.]({{P_FIG}}/map_M06_districts.png)

**Figure 3.** District emission weighted by the mean footprint. The shares attribute the prior; they do not estimate emission per district, because a quarter-degree footprint cell is larger than most Indonesian districts.

{{P_DISTRICT_TABLE}}

{{P_DISTRICT_TEXT}}

## 4. What emits it

### 4.1 The methane budget at each tower

{{P_CH4_BUDGET_TABLE}}

{{P_CH4_BUDGET_TEXT}}

### 4.2 Peatland

![Peatland methane arriving at Jambi.]({{P_FIG}}/map_M05_peat_signal.png)

**Figure 4.** Where the methane emitted on peat and seen at Jambi comes from, and the three routes by which it arrives.

{{P_PEAT_TABLE}}

{{P_PEAT_TEXT}}

### 4.3 The carbon dioxide budget, and land use

![The land-use proxy.]({{P_FIG}}/map_M03_folu_proxy.png)

**Figure 5.** The land-use proxy: peat drainage weighted by land cover, and burned carbon over peat. A pattern, not a flux.

{{P_CO2_BUDGET_TABLE}}

{{P_CO2_BUDGET_TEXT}}

{{P_FOLU_TEXT}}

## 5. Testing the national inventory

### 5.1 What the country reports, against what the global inventory assumes

![Reported against global methane.]({{P_FIG}}/map_M02_inventory_change.png)

**Figure 6.** Indonesia's reported 2022 methane, allocated to provinces, divided by the global gridded inventory in the same cells. Blue is where the country reports less than the global inventory assumes.

![The inventory difference and its effect at the towers.]({{P_FIG}}/figure_O02_inventory.png)

**Figure 7.** The reported national totals against the global gridded inventory by IPCC category, and the effect on the modelled prior at each tower.

{{P_INVENTORY_TABLE}}

{{P_INVENTORY_TEXT}}

{{P_INVENTORY_RESULT}}

### 5.2 From a global inventory to a provincial one

{{P_HIERARCHY_TABLE}}

{{P_HIERARCHY_TEXT}}

## 6. What the inversion resolves

### 6.1 What the observations informed

{{P_DIAGNOSTIC_TABLE}}

{{P_DOFS_TEXT}}

### 6.2 Skill against the boundary null

![Every configuration against the null.]({{P_FIG}}/figure_O04_scoreboard.png)

**Figure 8.** Cross-validated difference from the boundary null with a 95% date-block bootstrap interval, at the daily scale, for every configuration the campaign ran. Negative favours the inversion.

{{P_SKILL_TABLE}}

{{P_SKILL_TEXT}}

### 6.3 What the posterior implies, and what could be detected

{{P_FLUX_TABLE}}

{{P_FLUX_TABLE_CO2}}

{{P_FLUX_TEXT}}

### 6.4 Why the verdict is what it is

![The error budget.]({{P_FIG}}/figure_O01_error_budget.png)

**Figure 9.** Variance of the modelled source signal at the receptors against the error it must compete with, by gas.

{{P_BUDGET_TABLE}}

{{P_BUDGET_TEXT}}

### 6.5 Does the transport ensemble need re-running?

{{P_TRANSPORT_ASSESSMENT}}

### 6.6 The carbon dioxide biosphere prior

![The three biosphere priors.]({{P_FIG}}/figure_O03_biosphere.png)

**Figure 10.** Afternoon net flux and diurnal amplitude at the tower cells for the diagnostic prior, the assimilated flux and the hybrid.

The biosphere carries {{P_BIOSPHERE_SHARE}} of the modelled carbon dioxide signal, so it, not the emission inventory, is what limits that gas. Two sources exist and each fails differently, so the prior takes from each what it is good at.

{{P_BIOSPHERE_TEXT}}

{{P_BIOSPHERE_RESULT}}

## 7. What is operational and what is diagnostic

{{P_STATUS_TEXT}}

## 8. What would change the verdict

{{P_NEXT_TEXT}}

## 9. Reproducing this

{{P_SCRIPT_TABLE}}

## Appendix A. Questions these results answer

{{P_QUESTIONS_INTRO}}

{{P_QUESTIONS}}
