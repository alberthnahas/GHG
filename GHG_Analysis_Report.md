# Greenhouse gases at five Indonesian monitoring stations

**Hourly CO₂ / CH₄ / CO records from Bukit Kototabang, Jambi, Kemayoran, Bariri (Lore Lindu) and Sorong, validated against the NOAA GML flask record**

Analysis date: 18 August 2026 · 242,411 station-hours, 2001–2026 · 2,002 NOAA flask pairs, 2004–2025

---

## How to read this report

The report is in eight parts, meant to be read in order.

**Part I** establishes whether the data can be used at all. It finds three defects in the archive, fixes two of them, ends with a one-line test a station can run on its own record, and tests the result against an independent instrument — the NOAA Global Monitoring Laboratory flask programme that has sampled Bukit Kototabang since 2004. That external test is the hinge of the whole report: it confirms the largest correction, exposes a defect no internal check could see, and retires a conclusion an earlier draft had reached in error.

**Part II** treats the surface processes the hourly data resolve and the flask data cannot: the diurnal cycle, nocturnal source fingerprints, Jakarta's methane, and Jambi's peat.

**Part III** treats regional and transported signals: fire, the seasonal cycle as a transport tracer, and the inter-station gradients.

**Part IV** covers growth rates, radiative forcing, and what the record says about ENSO and the background warming it now sits on.

**Part V** records what changed relative to earlier drafts — including two published errors and their reasoning — and what this network can and cannot detect.

**Part VI** asks a question the other five do not: what any of this is worth under *Nilai Ekonomi Karbon*, Indonesia's carbon-pricing framework. It converts three measured signals into tonnes and into rupiah, establishes what size of change the network could verify independently, and ends with the negative result that matters most — the scale at which atmospheric measurement can and cannot serve a carbon-pricing system.

**Part VII** tests the information content and robustness of the network itself: timing loops, analyst choices, missingness, event persistence and whether one station can substitute for another.

**Part VIII** is the recommendations, and it comes last because it draws on all seven: what to fix in the archive, what to instrument, what to publish, and what not to claim.

Two conventions throughout. **Local time** means the station's civil time zone (WIB, WITA or WIT); everything is converted to it in Section 2. **"In-situ"** means the hourly analyser record delivered in the JSON archive; **"flask"** means the NOAA GML discrete-sample record.

---

## Summary of findings

**Table 1 — Summary of scientific findings and report locations**

| # | Finding | Section |
|---|---|---|
| **1** | **The archive's timestamps are not on a common time base, and Bukit Kototabang switches convention mid-record** — local time to 31 Dec 2020, UTC from 1 Jan 2021; the other four are UTC throughout. | 2 |
| **2** | **The NOAA flasks confirm the time-base correction from outside the archive.** Matched hour by hour, flask-minus-in-situ CO₂ goes from −8.50 ppm (*r* = 0.28) on the delivered timestamps to **+0.31 ppm (*r* = 0.77)** on the corrected ones; for CH₄, *r* goes from 0.74 to **0.98**. | 4.1 |
| **3** | **The in-situ CO₂ and CH₄ are on the WMO scale.** Post-2019 annual agreement with the co-located flasks is **+0.4, +0.4, −0.9, +0.1, −0.3 ppm** for CO₂ and within 2.2 ppb for CH₄. An earlier draft's claim of a 5–9 ppm network-wide CO₂ offset was **wrong** and is retracted in Section 15. | 4.2, 15 |
| **4** | **Bukit Kototabang's CO was biased high by 10–50 ppb before 2019.** Flask-minus-in-situ sits at −20 to −41 ppb through 2007–2018 and steps to **+0.6 to +4.3 ppb from 2019**, at the same date the analyser complement changes. The pre-2019 in-situ CO series must not be used for trends. | 4.3 |
| **5** | **The Maritime Continent is a genuine CO₂ minimum in the global surface network.** Bukit Kototabang's flask mean for 2015–2025 is **408.5 ppm — 5.5 ppm below Mauna Loa and 1.4 ppm below the South Pole.** This, not a calibration error, is why all five Indonesian stations read low. | 4.4 |
| **6** | **NOAA rejects 30.9 % of Bukit Kototabang's CO₂ flasks** against 2.6 % of its CH₄ and 3.0 % of its SF₆ — a quantitative statement that the site's CO₂ specifically is hard to sample cleanly. | 4.5 |
| **7** | **The morning boundary layer erodes the nocturnal store with an e-folding time of 1.9–2.4 hours at every one of the five sites**, from montane rainforest to megacity core. | 5.2 |
| **8** | **Jakarta's nocturnal ΔCO/ΔCO₂ is 23.5 ppb ppm⁻¹** — 13–46× every other site — which also bounds the fossil share of its regional CO₂ enhancement at **≤ 63 %**. | 6.3, 6.4 |
| **9** | **≳97 % of Jakarta's methane excess is not from combustion**, and the weekly cycle proves it: Sunday CH₄ is **+9.3 ppb [−11.8, +28.5]** while CO in the same air falls 39 ppb. Only **one of fifteen** station × species weekday tests in the network is significant. | 7 |
| **10** | **Jakarta's nocturnal methane flux is of order 65 g CH₄ m⁻² yr⁻¹** — roughly 2 Mt CO₂-equivalent per year over a 10³ km² footprint. | 7.3 |
| **11** | **Jambi's surface is drained peat, on two independent lines of evidence.** Its nocturnal CO₂ efflux is **1.9× the intact-rainforest reference**, and its respiration peaks in the **dry** season while Bariri's peaks in the **wet** one. | 8 |
| **12** | **October 2015: monthly-median CO of 1,493 ppb at a GAW global background station**, 17× its own baseline, 75 % of the month above 1,000 ppb. | 9.2 |
| **13** | **ΔCH₄/ΔCO alone classifies a Sumatran burning season.** Peat-fire seasons sit at 0.04–0.08; all fifteen non-fire seasons at 0.17–1.35, with no overlap. | 9.4 |
| **14** | **Fire plumes clear faster than OH can oxidise them:** e-folding 12–44 days, largest events fastest. | 9.5 |
| **15** | **The flask record gives a sound 22-year CO trend the in-situ record cannot.** The background (10th percentile) is flat at **−0.14 ppb yr⁻¹ [−0.51, +0.52]**; the polluted tail (90th) falls at **−3.17 ppb yr⁻¹ [−7.49, −0.40]**. | 9.6 |
| **16** | **The methane seasonal cycle at Bukit Kototabang is transport, not local wetlands — proven with an inert tracer.** CH₄'s seasonal component tracks SF₆'s at ***r* = 0.99**, slope 200 ppb ppt⁻¹ against a measured network interhemispheric ratio of 207. | 10.2 |
| **17** | **Bukit Kototabang has the largest SF₆ seasonal cycle in the network — 0.38 ppt, four times Mauna Loa's.** Since SF₆ has no chemistry and no local source, this is pure air-mass alternation, and in January the arriving air is *more* SF₆-rich than the mid-Pacific Northern Hemisphere. | 10.1 |
| **18** | **CO is the one species with a genuine local seasonal source on top of transport** — its SF₆ slope runs 35 % above the network gradient, while CH₄, CO₂ and N₂O run at 0.97–1.16. | 10.3 |
| **19** | **Equatorial Indonesia's CO₂ seasonal amplitude is much closer to Mauna Loa's than to the South Pole's** — 5.5 ppm at Bukit Kototabang against a *measured* 6.9 ppm at Mauna Loa and 1.3 ppm at the South Pole. An earlier draft had this backwards. | 10.4, 14 |
| **20** | **Bukit Kototabang and Bariri, 2,000 km apart, independently resolve the 2023 El Niño CO₂ growth anomaly to within 0.04 ppm yr⁻¹.** | 12.3 |
| **21** | **Jakarta's local greenhouse dome is 184 mW m⁻², of which methane is 29 %** (Jambi 39 %) against 20 % in the global forcing budget. | 13 |
| **22** | **Four long-lived gases are measurably accelerating at an equatorial station** — CO₂ +0.045 ppm yr⁻², CH₄ +0.398 ppb yr⁻², N₂O +0.020 ppb yr⁻², SF₆ +0.0075 ppt yr⁻². CO and H₂ are not. | 12.4 |
| **23** | **Methane's growth rate at Bukit Kototabang is 2.6× higher in 2014–2025 than in 2004–2013** (+9.38 against +3.65 ppb yr⁻¹) — the post-2014 surge, measured in the equatorial tropics. | 12.4 |
| **24** | **ENSO sensitivity measured directly:** CO₂ growth **+0.82 ± 0.27 ppm yr⁻¹ per °C** of ONI at **zero lag**, CO **+32 ± 8 ppb yr⁻¹ per °C** at zero lag, and CH₄ **−10.8 ± 2.5 ppb yr⁻¹ per °C at a 12-month lag**. | 12.5 |
| **25** | **The hemispheric gradient is widening for CO₂, CH₄ and SF₆ but closing for CO** — the only species whose emissions are actively regulated. | 12.6 |
| **26** | **Half of Bukit Kototabang's CO seasonal cycle is emitted nearby.** Removing the SF₆-predicted transport component leaves a 30.6 ppb local residual out of 56.4 ppb observed, peaking in **February and September** — the two burning seasons. | 10.6 |
| **27** | **Hydrogen is a fourth fire tracer; nitrous oxide is not.** ΔH₂/ΔCO = 0.143 (*r* = 0.76), while N₂O's apparent fire signal vanishes once the air mass is removed. | 9.7 |
| **28** | **Removing the air-mass component with SF₆ recovers a fire CO₂ signal that is otherwise invisible** — ΔCO/ΔCO₂ = 67 ppb ppm⁻¹, in the biomass-burning range, from flasks whose raw regression shows nothing. | 9.7 |
| **29** | **A tracer separates photosynthesis from dilution, and the sites order by land cover.** CO₂ disappears faster than CH₄ or CO on the same morning at the two forested sites (Bariri, Bukit Kototabang), at the same rate at drained-peat Jambi, and *slower* at Kemayoran — a megacity core is a net daytime CO₂ **source**. | 5.3 |
| **30** | **One equatorial station reproduces the global airborne fraction.** Its 2004–2025 flask growth of 2.32 ppm yr⁻¹ is **4.96 Pg C yr⁻¹** of atmospheric accumulation, **45 %** of total anthropogenic emissions — inside the published 40–50 % band. | 12.7 |
| **31** | **The 2023 El Niño anomaly is 4.4 Pg C yr⁻¹ — larger than the entire global land sink** (3.2 Pg C yr⁻¹). One year of tropical drought cancels more than a year of land uptake. | 12.7 |
| **33** | **Fire severity depends on which measure you use.** 2015 had 28 days above 1,000 ppb and the largest annual CO burden; **2014 had the highest single peak (4,063 ppb) on a weak El Niño**. A Gumbel fit puts a 1,000 ppb day at a **2.54-year** return period and a 2,000 ppb day at 7.21 years. | 9.8 |
| **34** | **The end of the burning season can be read off the CO record, and El Niño delays it by 15 days per °C** (*r* = +0.49, 20 years). Mean onset 6 October, s.d. 33 days. | 9.8 |
| **35** | **Jakarta's two emission ratios run in antiphase through the day.** ΔCO/ΔCO₂ peaks at **38.0** at 20:00 and bottoms at 10.5 at 14:00; ΔCH₄/ΔCO₂ does the opposite, peaking at **16.4** in the small hours. When traffic falls away, what is left is methane-rich. | 7.4 |
| **36** | **The Maritime Continent is a CO₂ sink region and a CO source region at the same time.** Against tropical marine air at Samoa, Bariri is **−6.3 ppm in CO₂ and +25.6 ppb in CO**; Sorong −3.9 and +24.6. | 11.2 |
| **37** | **Inter-station coherence follows site type, not distance.** The two closest stations (Jambi–Kemayoran, 618 km) are uncorrelated (*r* = −0.03); the two most distant clean pairs correlate at +0.55 to +0.69. | 11.2 |
| **38** | **A CO anomaly at Bukit Kototabang remembers itself for 19 days**, at Bariri for 11 — the same timescale as the plume clearance of Finding 14 and the 20–90 day spectral band of Finding 14. | 9.9 |
| **39** | **N₂O has a detectable regional source above transport** — a 16 % excess over the SF₆-predicted cycle, a 0.38 ppb residual peaking in March, and a level 1.04 ppb above Samoa. The first quantitative statement about N₂O at this site. | 10.7 |
| **40** | **Hydrogen tracks CO only when fires burn.** The H₂–CO correlation runs +0.76 to +0.83 in September–November and +0.02 to +0.38 in the wet months. | 9.7 |
| **41** | **The diurnal amplitude is dry-season amplified at the lowland sites and not at the montane ones** — Kemayoran ×1.93 and Sorong ×1.66 from wet to dry season, against ×1.08 at both mountain stations. | 5.4 |
| **42** | **Not supported: fire years leave no trace in the CO₂ growth rate at the same station** (*r* = −0.29 same year, −0.06 the next). The most extreme regional fire signal in this archive is invisible in the budget it feeds. | 15.5 |
| **43** | **Not supported: no seasonal amplitude and no cross-equatorial reach shows a 20-year trend.** Five separate tests, all consistent with no change. | 15.5 |
| **44** | **The difference between the two ENSO indices is itself a warming measurement.** ONI − RONI *is* the tropical-mean SST anomaly, and it warms at **+0.068, +0.120 and +0.222 °C decade⁻¹** over 1950–2025, 1980–2025 and 2000–2025 — non-overlapping intervals, and a lower bound, because the ONI's shifting 30-year base period is designed to remove exactly this. | 14.1 |
| **45** | **Which index you use changes the ENSO label in 9 of 76 seasons — and where it mattered, ONI matched the fires.** In 2014, 2017 and 2019 the two indices disagreed on the class; the ONI classification agreed with what Bukit Kototabang recorded (4,063 ppb, 321 ppb, 1,660 ppb peak CO) in all three. | 14.2 |
| **46** | **Not supported: background tropical warming does not itself drive the fires.** The two indices are nearly interchangeable as continuous predictors, and the warming term alone has *no* correlation with the fire extremes (*r* = −0.03 for the peak, +0.07 for days above 1,000 ppb). The burning tracks ENSO variability, not the mean state. | 14.3 |
| **47** | **This network's own forcing accrual implies the observed warming rate.** Converting 36.8–41.6 mW m⁻² yr⁻¹ with the AR6 transient climate response gives **+0.18 to +0.20 °C decade⁻¹**, against **+0.222 [+0.202, +0.242]** observed in tropical SST since 2000 — an end-to-end closure from mixing ratio to forcing to temperature. | 14.4 |
| **48** | **The week Jakarta stopped driving.** At Idul Fitri, when several million people leave the city, rush-hour CO falls **31.5 %** (*p* = 0.038) while CH₄ moves **−0.1 %** and CO₂ **−1.0 %**, neither significant. A natural experiment reaching Findings 8 and 9 without using a single emission ratio. | 7.5 |
| **49** | **Afternoon-only sampling understates CO₂ by 8–18 ppm.** The diurnal rectifier — 24-hour mean minus afternoon mean — is +8.3 to +18.3 ppm across the five stations, largest at the lowland vegetated sites and smallest at coastal Sorong. Four to eight times the entire interhemispheric gradient. | 4.6 |
| **50** | **A negative rectifier is a data-quality flag needing nothing external.** Sorong before June 2023 runs at **−29.2 ppm with 47 % of days negative**, which no boundary layer can produce. It re-flags the same period the report found by baseline continuity — using no reference site, no flask and no second station. | 4.6 |
| **51** | **Most of *n* is not there.** The ENSO growth-rate sensitivities of Section 12.5 have *n*<sub>eff</sub> ≈ **12**, not 215 — about the number of ENSO events in the record. Corrected intervals roughly quadruple and none is significant at 95 %; the lag structure stands. The annual results are unaffected. | 16.1, 15.4 |
| **52** | **CO needs 15.5 years of record to show its own trend**, against 1.4 for CO₂ and 0.4 for SF₆ — a factor of 38, driven entirely by fire-episode noise. The stations opened in 2021–2023 cannot give a defensible CO trend before about 2036. | 16.2 |
| **53** | **Weekly flask sampling reconstructs the monthly mean to 1.51 ppm** — 65 % of one year's CO₂ growth. Fortnightly costs 2.10 ppm, monthly 2.94. | 16.3 |
| **54** | **CH₄ and N₂O growth anomalies covary most tightly (*r* = +0.60); CO and SF₆ not at all (+0.07).** Since SF₆'s variability is pure transport, CO's interannual variability is emission, not transport. | 12.8 |
| **55** | **N₂O's seasonal cycle is 89 % transport** (*R*² against SF₆), though its mean carries a regional source — a source that is regional but aseasonal, which points to agriculture rather than fire. | 12.8 |
| **56** | **Hydrogen is rising at +1.51 [+1.16, +1.84] ppb yr⁻¹** (+0.27 % yr⁻¹) over 2009–2024 — a tropical Southern-Hemisphere baseline established before any hydrogen-economy deployment. | 12.8 |
| **57** | **The CO₂ deficit is widening against the South Pole (+0.74 [+0.27, +1.20] ppm decade⁻¹) but flat against Mauna Loa.** At 0.2 °S, Bukit Kototabang tracks the Northern Hemisphere. | 12.8 |
| **32** | **Jambi's peat is losing 16.7 t C ha⁻¹ yr⁻¹**, which empties a 1,000–3,000 t C ha⁻¹ store on an e-folding time of **60–180 years** — a human-lifetime clock on a store that took millennia to build. | 8.4 |
| **58** | **NOAA flask pair reproducibility sets the measurement floor.** Single-flask random uncertainty, from the RMS of 674–960 duplicate-pair differences, is **0.18 ppm for CO₂, 1.10 ppb for CH₄, 0.67 ppb for CO, 0.22 ppb for N₂O, 0.031 ppt for SF₆ and 0.84 ppb for H₂** — for CO₂, 13× smaller than one year's growth. CH₄ and N₂O pair differences are heavy-tailed, so a robust estimator is given alongside. | 4.7 |
| **59** | **SF₆ is an absolute interhemispheric transport clock**: Bukit Kototabang lags Arctic Barrow by **6.7 months** (0.181 ppt) and leads the South Pole by **9.0 months** (0.243 ppt), measuring a pole-to-pole mixing time of **15.9 months**. | 10.8 |
| **60** | **Free-tropospheric vs boundary-layer vertical gradients at 19.5°N**: Mauna Loa (3,397 m) is depleted relative to sea-level Kumukahi by **−16.5 ppb in CH₄** and **−9.1 ppb in CO**, while equatorial Bukit Kototabang sits below both in CO₂ (−5.3 and −5.7 ppm). | 10.9 |
| **61** | **Equatorial hydrogen has a bimodal seasonal cycle** (11.8 ppb harmonic amplitude), peaking in March (+6.3 ppb) and October (+5.0 ppb) during regional burning/transport, with a minimum in June (−6.3 ppb) driven by soil uptake. | 10.10 |
| **62** | **Bariri (Central Sulawesi montane rainforest) is 2.0 ppm lower in CO₂ and 22 ppb lower in CH₄ than Bukit Kototabang**, defining the cleanest terrestrial baseline in the archipelago. | 11.3 |
| **63** | **Clean Sorong (post-June 2023) shares the Maritime Continent CO₂ deficit** (−3.9 ppm vs Samoa) with a substantial terrestrial excess (+52 ppb CH₄, +38 ppb CO). | 11.4 |
| **64** | **Jakarta's weekend traffic drop isolates vehicular from non-vehicular emissions**: morning rush CO drops **23.7 %** (weekday amplitude 1.30× weekend), while CO₂ and CH₄ diurnal amplitudes are unaltered (ratios 0.97 and 0.99). | 7.6 |
| **65** | **Not supported: tropical N₂O growth anomalies show no significant ENSO response under Bartlett effective sample size correction** (*r* = +0.24, *n* = 215, *n*<sub>eff</sub> = 6.3, *p* = 0.62). | 16.4, 15.5 |
| **66** | **Global synchrony in N₂O decadal acceleration**: post-2014 growth surged by **+0.21 to +0.24 ppb yr⁻¹** at every latitude from 71°N to 90°S, demonstrating uniform global agricultural nitrogen forcing. | 12.9 |
| **67** | **Drained peatland respiration is dry-season amplified at Jambi (1.17×)** (diurnal amplitude 41.7 → 48.9 ppm), while primary rainforest at Bariri is seasonally invariant (0.99×, 37.0 → 36.6 ppm). | 8.5 |
| **68** | **Latitude–time Hovmöller dynamics: CO₂ seasonal amplitude collapses from 16.39 ppm at Barrow (71.3°N) to 3.94 ppm at Bukit Kototabang (0.2°S) and 1.12 ppm at the South Pole (90.0°S)**, with a summer drawdown phase delay of 1.2 months per 30° latitude. | 10.11 |
| **69** | **A two-box interhemispheric mass-balance model yields an atmospheric mixing timescale of τ<sub>ex</sub> = 1.23 years (14.7 months)** from the 0.399 ppt mean interhemispheric SF₆ gradient and 0.325 ppt yr⁻¹ secular growth. | 10.12 |
| **70** | **Not supported: no resolvable eastward propagation of the equatorial CH₄ seasonal wave.** The apparent Sumatra→Papua march is non-monotonic (Kemayoran peaks in July), and Bukit Kototabang's own peak month varies by ±1.2 months between years — as much as the claimed signal. Three of five stations have under four complete years** at an effective zonal phase speed of 40 km day⁻¹, driven by the trans-archipelago monsoon march. | 10.13 |
| **71** | **Interhemispheric CO₂ growth rate asymmetry peaks during El Niño extremes**: Southern and Equatorial growth surges up to 1.8 ppm yr⁻¹ ahead of the Northern polar box, lagging ONI by 4–6 months. | 12.10 |
| **72** | **The post-2014 methane resurgence is overwhelmingly tropical in origin**: the tropical-to-polar gradient (BKT − SPO) expanded by +3.6 ppb (77.7 → 81.3 ppb), accounting for 90 % of the +4.0 ppb total interhemispheric gradient expansion. | 12.11 |
| **73** | **Vertical damping of seasonal cycles across the trade-wind inversion at 19.5°N**: free-tropospheric Mauna Loa (3,397 m) exhibits **18.1 % damping in CO₂**, **12.3 % in CH₄**, and **14.0 % in CO** seasonal amplitude relative to sea-level Kumukahi. | 12.12 |
| **74** | **Multi-species growth anomaly covariance structure separates industrial/agricultural forcing (CO₂–N₂O–SF₆, r = 0.71–0.82) from incomplete combustion (CO–CH₄, r = 0.67)**, with SF₆ completely decoupled from biomass burning. | 12.13 |
| **75** | **Pristine clean-air baseline CO floor stability at Bukit Kototabang**: the 10th percentile background has remained stable at **75.9 ± 2.8 ppb** over 22 years (Theil–Sen slope −0.03 ppb yr⁻¹, p = 0.92), establishing a durable unpolluted marine reference floor. | 9.10 |
| **76** | **Monsoonal modulation of nocturnal canopy accumulation at Bukit Kototabang**: biogenic nocturnal CO₂ respiration is active year-round (16.46 ppm wet DJF vs 16.88 ppm dry JJA), while combustion CO accumulation is 6.9× higher in the wet westerly regime (10.3 vs 1.5 ppb). | 8.6 |
| **77** | **Multi-species radiative forcing budget of the Maritime Continent over pristine marine air**: regional CH₄ enhancement (+70.9 ppb, **+42.0 mW m⁻²**) overcomes the regional CO₂ drawdown deficit (−3.09 ppm, **−40.5 mW m⁻²**), yielding a small net positive forcing of **+5.1 mW m⁻²**. The sign is robust; the magnitude is a residual of two large opposing terms. | 13.3 |
| **78** | **The enhancement ladder in the currency of carbon accounting.** Over the Bariri forest reference, Kemayoran is **+11.26 ± 0.41 ppm CO₂-equivalent**, Jambi +5.26, Bukit Kototabang +2.27, Sorong +2.01. Methane carries 4.9–12.8 % of it; CO carries none, because CO has no GWP. | 11.5 |
| **79** | **Data return, station by station and year by year.** Bukit Kototabang's CO record spans 25 years at 49–99 % return, but its **CO₂ record exists in only 12 of those calendar years and clears 50 % return in 9**. Of the four new stations only Kemayoran has cleared 90 % in every full year. | 3.1 |
| **80** | **A negative result: how often a station sees clean air does not tell you what kind of station it is.** The fraction of hours within 2 ppm of the site's own background is **10.9–14.0 % at all five sites**, and the montane rainforest ranks *last*. The afternoon selection, not the site, does the discriminating. | 11.6 |
| **81** | **Hourly cross-species coupling separates the source types.** Kemayoran's CO₂–CO anomaly correlation is *r* = **0.85** — one combustion source driving both — against 0.39 at Bariri and 0.23 at Sorong; Jambi's strongest pair is CO₂–CH₄ at 0.65. | 5.5 |
| **82** | **A persistence ladder at Bukit Kototabang.** The e-folding memory of a monthly anomaly is **5.9 months for N₂O**, 2.1 for CO and SF₆, 2.0 for CH₄, 1.7 for CO₂ and 1.6 for H₂. | 10.14 |
| **83** | **Two independent instruments at one site agree on the growth rate.** In-situ **2.94 [2.41, 3.69]** against flask **3.75 [2.81, 4.55] ppm yr⁻¹** over the same 42 months — overlapping intervals, and a co-located trend check good to about ±0.8 ppm yr⁻¹. | 4.8 |
| **84** | **The nocturnal accumulation rate, separated from the layer depth it is usually multiplied by**: Jambi **3.16 [2.99, 3.51]**, Bariri 1.98, Kemayoran 1.58, Bukit Kototabang 1.42, Sorong 0.78 ppm h⁻¹. | 5.6 |
| **85** | **The nocturnal CH₄:CO₂ ratio is the one flux quantity here that does not inherit the layer depth**, because the depth cancels: **20.5 ppb ppm⁻¹ at Kemayoran** — 17.2 % of that air's CO₂-equivalent — 3.0 at Jambi, and indistinguishable from zero at both forest sites. | 6.5 |
| **86** | **Jakarta's weekday-minus-weekend rush-hour excess in CO₂-equivalent**: CO **+187.3 ppb** (*p* < 10⁻⁴), CO₂ **+1.70 ppm** (*p* = 0.015), CH₄ **+1.2 ppb** (nil) — **1.71 ppm CO₂e**, of which methane is 0.7 %. | 7.7 |
| **87** | **A negative result: this site's flask CO₂ cannot see the global growth rate.** Annual growth at Bukit Kototabang carries **0.1 % of the variance** of the Barrow–South Pole mean (*r* = 0.03, *p* = 0.91) while Mauna Loa and Samoa, through the identical pipeline, give *r* = 0.86 and 0.88. | 12.14 |
| **88** | **The step change the record could see at all**: **6.10 ppm CO₂ over a 12-month window and 2.73 ppm over 60**, and in CO₂-equivalent 0.41 / 0.18 ppm for CH₄, 0.31 / 0.14 for N₂O, 0.015 / 0.007 for SF₆. | 16.5 |
| **89** | **The reference site is stationary in the property that matters, but not tightly.** Bukit Kototabang's CO₂ seasonal amplitude is **6.66 ± 2.11 ppm** across 19 years — a coefficient of variation of 32 % — with no significant trend. | 16.6 |
| **90** | **Jambi's measured peat carbon loss, priced under NEK**: 16.70 t C ha⁻¹ yr⁻¹ is **61.18 t CO₂ ha⁻¹ yr⁻¹**, worth **IDR 1.84–4.26 million ha⁻¹ yr⁻¹** across the carbon-tax floor and the traded prices — and IDR 83.25 million at the EU ETS price. | 17.2 |
| **91** | **Jakarta's methane, priced — and the ceilometer is worth more than the price discovery.** The value spans **IDR 47.7–190.6 billion yr⁻¹** at one carbon price, a factor of four, purely from the unmeasured nocturnal layer depth; every carbon price in Indonesian use spans a factor of 2.3. | 17.3 |
| **92** | **The atmosphere splits Jakarta's enhancement between two administrations.** Of the 11.26 ppm CO₂e, **at most 6.50 ppm (57.7 %) is fossil** — energy and transport — and at least 4.73 ppm sits with waste and land use, of which methane is 0.91 ppm. | 17.4 |
| **93** | **The smallest abatement the network could independently verify**, as a fraction of each site's own local source: **24 % at Kemayoran and 52 % at Jambi over five years**; at Bukit Kototabang and Sorong the threshold exceeds the entire local signal. | 17.5 |
| **94** | **The diurnal rectifier is a systematic bias on any flux-based credit, and it is larger than what is being credited.** It runs **+8.3 to +18.3 ppm** against enhancements of 2.0 to 11.3 ppm — 100 % of the enhancement at Kemayoran and 476 % at Bukit Kototabang — and it does not average out, because its sign is fixed. | 17.6 |
| **95** | **Which station can do which NEK job, scored from data return, record span and signal size** rather than from its designation: Kemayoran is a source monitor now, Bukit Kototabang a baseline anchor, Bariri the ladder's zero, and Jambi and Sorong are not yet fit on data return. | 17.7 |
| **96** | **The uncertainty in a monetised peat claim is not in the measurement.** The nocturnal layer depth contributes a factor of **4.0**, the store depth 3.0, the carbon price 2.32 — and the atmospheric measurement itself **1.18**, the smallest term in the chain. | 17.8 |
| **97** | **The liability outlives the contract.** At the measured loss rate a 1,000 t C ha⁻¹ store is **34 % gone within a 25-year crediting period** and 57 % within fifty years; a 3,000 t C ha⁻¹ store loses 13 % and 24 %. | 17.9 |
| **98** | **Reversal risk, measured rather than assumed.** A 2.54-year return period for a 1,000 ppb CO day puts the chance of at least one extreme fire year inside a 25-year crediting period at **effectively certain**, and 91.8 % inside five years — and ENSO clustering makes that an optimistic figure. | 17.10 |
| **99** | **What each mode of measurement in this project actually verifies**, with its number: scale to 0.31 ppm, trend to 0.8 ppm yr⁻¹, a background step to 2.73 ppm CO₂e, a station's physical function with no external data at all. | 17.11 |
| **100** | **A negative result, and the most consequential one here: this network cannot verify a national target.** The full width of Indonesia's Second NDC 2035 range, 231.2 MtCO₂e yr⁻¹, produces a regional signal of **0.05–1.09 ppm** — 2 % to 40 % of the 2.73 ppm step the record can resolve. The network's use under NEK is at project and city scale, and as a check on the inventory's physics. | 17.12 |
| **101** | **Daily tracer loops contain source timing that a correlation discards.** CO₂–CH₄ loops turn in opposite directions at the two forest sites and at Jambi/Jakarta; 72 % of Jambi days share one direction against 41 % at Bariri. | 18.1 |
| **102** | **Sorong's CO₂–CH₄ loop reverses with season.** Its median signed area is −0.821 in May–October and +0.043 in November–April; the other four sites retain their sign. | 18.2 |
| **103** | **Jakarta's combustion coupling is strongest at night.** CO₂–CO rises from *r* = 0.59 in the afternoon to 0.86 at night, while Bukit Kototabang's is near zero in both. | 18.3 |
| **104** | **The baseline percentile is a material analytical choice.** Moving from the afternoon 10th to 30th percentile spans 2.6–6.2 ppm CO₂, 15–54 ppb CH₄ and 10–49 ppb CO. | 18.4 |
| **105** | **The afternoon clock choice is not material.** Shifting the five-hour window one hour either way changes the CO₂ baseline by at most 1.24 ppm, and by under 0.58 ppm at four sites. | 18.5 |
| **106** | **Changing the reference changes every enhancement but cannot choose the reference.** In the common 2023–2024 window the station ordering is invariant; the zero is an external design decision, not a result of subtraction. | 18.6 |
| **107** | **The network's broad station ordering repeats in both complete overlap years.** Kemayoran is highest in CO₂ and CO in 2023 and 2024; Bariri is lowest, with only the three clean middle sites exchanging places. | 18.7 |
| **108** | **Maintenance gains are largest where return is poorest, but still sublinear.** Adding 20 percentage points of valid hours lowers a sampling-limited threshold by 14 % at Sorong, 11 % at Jambi and only 2.5 % at Kemayoran. | 18.8 |
| **109** | **Outages are seasonal operations, not random missing hours.** Jambi's all-species return falls to 48 % in November and Kemayoran to 67 % in February, while their best months exceed 97 %. | 18.9 |
| **110** | **One outage can erase a climatology.** The longest common-species gaps are 396 h at Jambi, 372 h at Kemayoran, 1,587 h at Bariri and 5,828 h at Sorong; BKT CO₂/CH₄ lose 44,600 h across the long archive gap. | 18.10 |
| **111** | **Bukit Kototabang's apparent 161,866-hour archive contains only 41.1 % fully paired CO₂–CH₄–CO hours.** At the four newer stations the pairing penalty is at most 0.9 percentage points. | 18.11 |
| **112** | **Calendar-month completeness changes the station ranking.** Of 52 Sorong months only 28 clear 50 % return; Jambi clears 22 of 26, Kemayoran 25 of 26, and Bariri 49 of 58. | 18.12 |
| **113** | **The weekday experiment is unique to Jakarta.** Of fifteen station × species morning comparisons, only Kemayoran CO excludes zero: +201 ppb on weekdays; every rural and background comparison is null. | 18.13 |
| **114** | **Jakarta's rush-hour increment has a combustion fingerprint no other site approaches.** Relative to midday it adds 18.5 ppm CO₂ and 482.5 ppb CO — 26.1 ppb CO per ppm CO₂, against 0.2–1.5 elsewhere. | 18.14 |
| **115** | **Season changes the source mixture, not only the amplitude.** Jakarta's CH₄:CO₂ diurnal-amplitude ratio rises from 13.75 in the wet season to 18.24 in the dry; Sorong rises from 0.73 to 1.83 while Bariri is unchanged. | 18.15 |
| **116** | **Extreme CO is persistent where fire dominates and brief where traffic dominates.** Above each site's 99th percentile, BKT CO forms 28 clusters with a 34.5-hour median span; Jakarta forms 38 clusters with 3.5 hours. | 18.16 |
| **117** | **Three days remove most event enhancement, but not equally by tracer.** Median residual fractions after day three range from 0.23 for Jambi CO to 0.67 for Bariri CH₄. | 18.17 |
| **118** | **An “extreme” has no natural concentration threshold across this network.** The 99th-percentile CO threshold ranges from 183 ppb at Bariri to 2,304 ppb at Kemayoran; event counts require a declared site-relative threshold. | 18.18 |
| **119** | **There is no daily common mode after local background removal.** Across ten station pairs, detrended afternoon anomaly correlations are at most 0.11 for CO₂ and 0.10 for most CH₄/CO pairs. | 18.19 |
| **120** | **No station substitutes for another at daily scale.** Leave-one-station-out network predictions have correlations between −0.02 and +0.10 and errors at least as large as local variability. | 18.20 |
| **121** | **The three-gas atmosphere is dominated by one local mode, but not everywhere.** PC1 explains 72.4 % at Jakarta, 68.4 % at Jambi and only 54.7 % at Bariri. | 19.1 |
| **122** | **Bariri retains the most independent tracer information.** Its effective dimension is 2.48 of three, against 1.72 at Jakarta. | 19.2 |
| **123** | **Conditional dependence separates source pairs.** Controlling CH₄ leaves Jakarta CO₂–CO at +0.846; controlling CO leaves BKT CO₂–CH₄ at +0.798. | 19.3 |
| **124** | **Jakarta's upper combustion tail is fourteen times independence.** Given top-5 % CO₂, top-5 % CO occurs with probability 0.715 rather than 0.05. | 19.4 |
| **125** | **Clean-air tails couple differently from plume tails.** Jakarta's lower-tail CO₂–CH₄ dependence is 0.578; BKT CO₂–CO is below independence at 0.034. | 19.5 |
| **126** | **Nonlinear information confirms two dominant fingerprints.** Excess mutual information is 0.557 nats for Jakarta CO₂–CO and 0.507 for BKT CO₂–CH₄; permutation bias is 0.002. | 19.6 |
| **127** | **Jakarta methane coupling is strongly monotonic but not linear.** CH₄–CO has Pearson +0.370 and Spearman +0.702. | 19.7 |
| **128** | **Source coupling steepens in the upper tail.** Jakarta's standardised CO-on-CO₂ slope rises from 0.900 at the 10th conditional quantile to 1.413 at the 90th. | 19.8 |
| **129** | **The day–night distribution shift is primarily CO₂ at vegetated sites.** Jensen–Shannon divergence reaches 0.602 nats at Bariri for CO₂ but only 0.010 for CH₄. | 19.9 |
| **130** | **Extreme CO₂ has a clock; extreme CO often does not.** Top-decile CO₂ hour entropy is 0.72–0.79, while BKT CO is 0.996. | 19.10 |
| **131** | **The diurnal clock explains 65 % of Bariri CO₂ variance but 49 % at Jambi and 36 % at Jakarta.** Most CH₄ and CO variance remains event-scale residual. | 19.11 |
| **132** | **Averaging suppresses urban variance but not background persistence.** Monthly variance retains 4–8 % at Jakarta/Jambi but 59–66 % for BKT CO₂ and Bariri CH₄/CO. | 19.12 |
| **133** | **The optimum averaging scale is species-specific.** BKT CH₄ and CO reach minimum Allan deviation at one hour; most newer-station gases continue improving to seven days. | 19.13 |
| **134** | **BKT variability has no resolved long-term trend.** All three Theil–Sen scale intervals include zero over 12 measured years. | 19.14 |
| **135** | **Variance change points are not stable enough to interpret physically.** Algorithmic splits collect at record edges or differ by species. | 19.15 |
| **136** | **Source-coupling signs are stable between years.** Fourteen of fifteen station–pair combinations retain one sign in every measured year. | 19.16 |
| **137** | **The conditional-dependence graph has different dominant edges.** BKT is CO₂–CH₄; Jakarta is CO₂–CO; Jambi retains all three. | 19.17 |
| **138** | **Extreme days are almost entirely local.** Cross-station event Jaccard overlap is generally below 0.10 and often zero. | 19.18 |
| **139** | **No robust 0–7 day propagation lag emerges.** Best-lag correlations are small and unstable, except on short BKT overlaps. | 19.19 |
| **140** | **The five-station network has almost five independent daily dimensions.** Participation ratios are 4.61–4.92; PC1 explains only 24–29 %. | 19.20 |
| **141** | **Even an optimised multigas cross-station combination is weak.** Regularised canonical correlations are ≤0.234 on overlaps above 100 days. | 19.21 |
| **142** | **A missing tracer is reconstructible only where sources are tightly coupled.** Leave-year-out R² reaches 0.74 for Jakarta CO₂ and 0.72 for CO, but ≤0.14 for every Bariri/Sorong gas. | 19.22 |
| **143** | **Three anomalies barely identify the station.** Leave-month-out accuracy is 26.5 % against 20 % chance, carrying only 0.010 bit. | 19.23 |
| **144** | **Jakarta is multivariately distinct because of CO; Bariri and Sorong are nearly inseparable.** Robust distances are 9.27 versus 0.69. | 19.24 |
| **145** | **BKT extremes are strongly bursty.** Burstiness is 0.59–0.70, against 0.08–0.20 at Jakarta/Jambi. | 19.25 |
| **146** | **BKT fire CO has the strongest extremal clustering.** Its runs extremal index is 0.119, an 8.39-hour mean extreme run. | 19.26 |
| **147** | **Composite event recovery separates conservative from rapidly ventilated tracers.** Half-recovery is five days for Bariri CH₄, three for BKT CO, and one for most urban/Jambi gases. | 19.27 |
| **148** | **A single exponential is not a universal recovery law.** Power-law recovery is preferred for ten of fifteen station–species combinations; BKT CO and Bariri CH₄/CO prefer exponential decay. | 19.28 |
| **149** | **Hysteresis is timing, not plume size.** Absolute loop area has absolute Spearman ρ ≤ 0.10 against daily CO₂ range at every station. | 19.29 |
| **150** | **The strongest nonlinear links are also physically interpretable conditional edges.** Jakarta CO₂–CO and BKT CO₂–CH₄ lead both mutual information and partial correlation. | 19.30 |
| **151** | **Bukit Kototabang’s daily ventilation clock is compact:** the steepest CO₂ fall is at 09:00 and the strongest evening rise at 18:00, nine hours apart. | 19.31 |
| **152** | **Jambi has the network’s strongest one-hour morning CO₂ collapse, −15.06 ppm at 09:00**, followed by its largest evening rise at 20:00. | 19.31 |
| **153** | **Jakarta has the longest transition separation:** its steepest morning fall is at 08:00 and strongest evening build-up at 21:00, thirteen hours apart. | 19.31 |
| **154** | **Bariri begins ventilating earliest and rebuilding earliest:** 08:00 and 18:00, with the network’s strongest evening step (+5.05 ppm). | 19.31 |
| **155** | **Sorong’s corrected record has a weak evening rebuild (+1.62 ppm at 21:00)** despite a sharp 09:00 collapse, consistent with stronger coastal ventilation. | 19.31 |
| **156** | **BKT nocturnal CO₂ accumulation slows by half after midnight:** 1.61 to 0.75 ppm h⁻¹, a significant curvature rather than one linear flux. | 19.32 |
| **157** | **Not supported at Jambi: no resolved late-night saturation.** Early and late slopes are 3.34 and 2.87 ppm h⁻¹; the paired difference is not significant (*p*=0.58). | 19.32 |
| **158** | **Jakarta’s nocturnal slowdown is marginal, not established:** 1.70 to 1.48 ppm h⁻¹ (*p*=0.085). | 19.32 |
| **159** | **Bariri’s nocturnal accumulation slows from 2.48 to 1.76 ppm h⁻¹**, consistent with intermittent exchange or diminishing respiration–storage efficiency. | 19.32 |
| **160** | **Sorong shows the strongest proportional nocturnal saturation:** the late-night slope is 37% of the early-night slope. | 19.32 |
| **161** | **BKT carries afternoon CO₂ anomalies into the next dawn:** *r*=0.750, explaining 56.2% of variance after removing month effects. | 19.33 |
| **162** | **Not supported at Jambi: one afternoon predicts almost none of the next dawn** (*r*=0.089; 0.8% variance). | 19.33 |
| **163** | **Jakarta largely resets overnight:** next-dawn carry-over explains only 3.0% of variance. | 19.33 |
| **164** | **Bariri retains a measurable residual-layer memory:** afternoon CO₂ predicts 19.7% of next-dawn variance. | 19.33 |
| **165** | **Sorong has no resolved next-day CO₂ carry-over:** *r*=0.054 despite 557 paired days. | 19.33 |
| **166** | **BKT’s wet–dry distribution shift is methane-led** (Jensen–Shannon divergence 0.079 nats), not CO₂-led. | 19.34 |
| **167** | **Jambi’s strongest monsoon distribution shift is also methane** (0.057 nats), consistent with hydrologically controlled sources. | 19.34 |
| **168** | **Jakarta is seasonally stable in all three gases:** its largest wet–dry divergence is only 0.023 nats, in CO. | 19.34 |
| **169** | **Bariri has the network’s largest seasonal distribution reorganisation:** CH₄ divergence is 0.225 nats. | 19.34 |
| **170** | **Sorong’s seasonal shift is multigas but methane-led:** 0.047 nats for CH₄ against 0.033 for CO₂ and 0.029 for CO. | 19.34 |
| **171** | **Three multigas regimes explain 54.4% of BKT anomaly variance; its distinct 10.2% regime is CO-rich**, the fire mode. | 19.35 |
| **172** | **Jambi’s rare 4.9% regime is elevated in all three gases**, a coherent peat/source-accumulation state rather than a single-tracer outlier. | 19.35 |
| **173** | **Jakarta’s three-regime partition explains 66.0% of anomaly variance; its rarest state is overwhelmingly methane-rich.** | 19.35 |
| **174** | **Bariri’s multigas regimes are diffuse:** three clusters explain only 45.0%, the lowest separation in the network. | 19.35 |
| **175** | **Sorong’s rarest cluster is an outlier diagnostic, not a source estimate:** 0.1% occupancy and extreme robust scores expose residual tail sensitivity. | 19.35 |
| **176** | **BKT’s strongest compound extreme is CO₂–CH₄:** joint top-5% hours occur 6.7 times more often than independence. | 19.36 |
| **177** | **Jambi’s CO₂–CH₄ upper tail is 7.5 times independence**, quantitatively linking its strongest peat-related accumulations. | 19.36 |
| **178** | **Jakarta’s joint CO₂–CO combustion tail is 14.3 times independence**, the strongest compound extreme in the network. | 19.36 |
| **179** | **Bariri has the weakest compound tail:** CO₂–CH₄ extremes are only 2.6 times independence. | 19.36 |
| **180** | **Sorong’s strongest compound tail is CH₄–CO, 6.8 times independence**, rather than CO₂ with either tracer. | 19.36 |
| **181** | **BKT fire-event composition is stable through day three:** median CH₄/CO is 0.290 on day 0 and 0.319 on day 3 while 42% of CO remains. | 19.37 |
| **182** | **Jambi events become methane-richer as CO clears:** CH₄/CO rises from 0.624 to 1.264 while only 23% of CO remains after three days. | 19.37 |
| **183** | **Jakarta event composition does not show systematic methane enrichment by day three:** 0.408 to 0.373. | 19.37 |
| **184** | **Bariri has the slowest CO event recovery:** 57.5% remains after three days while CH₄/CO stays near 0.21. | 19.37 |
| **185** | **Sorong events become methane-richer during recovery:** CH₄/CO rises from 0.452 to 0.732 as CO falls to 36.5%. | 19.37 |
| **186** | **BKT daily CO memory is far beyond shuffled chance:** lag-1 *r*=0.623 versus a surrogate mean of 0.000 (*p*=0.001). | 19.38 |
| **187** | **Jambi retains significant daily CO memory despite rapid event recovery:** lag-1 *r*=0.315 (*p*=0.001). | 19.38 |
| **188** | **Jakarta traffic pollution is not day-independent:** daily CO lag-1 *r*=0.366 against a zero surrogate expectation. | 19.38 |
| **189** | **Bariri has the strongest daily CO persistence:** lag-1 *r*=0.640 (*p*=0.001). | 19.38 |
| **190** | **Sorong daily CO persistence is significant after QC:** lag-1 *r*=0.513 (*p*=0.001). | 19.38 |
| **191** | **BKT’s dominant annual coupling is consistently CH₄–CO:** median *r*=0.576 and positive in all twelve measured years. | 19.39 |
| **192** | **Jambi’s dominant CH₄–CO coupling is stable across its three years:** *r*=0.548–0.599. | 19.39 |
| **193** | **Jakarta’s CO₂–CO fingerprint is exceptionally reproducible:** annual *r*=0.873–0.891. | 19.39 |
| **194** | **Bariri’s dominant CH₄–CO edge remains positive but varies twofold:** *r*=0.204–0.566 across six years. | 19.39 |
| **195** | **Sorong’s post-QC dominant edge is CO₂–CH₄ and retains one sign in every available year** (*r*=0.461–0.558). | 19.39 |
| **196** | **A single fixed hour cannot represent BKT’s daily CO₂ mean without declaring the hour:** median hourly bias spans 20.82 ppm. | 19.40 |
| **197** | **Jambi has the largest fixed-hour sampling exposure:** its hourly CO₂ bias spans 43.60 ppm; 22:00 is closest to the daily mean. | 19.40 |
| **198** | **Jakarta’s least-biased fixed sample is 22:00, not afternoon:** the full hourly bias span is 29.21 ppm. | 19.40 |
| **199** | **Bariri’s 20:00 median nearly equals its daily mean (−0.06 ppm), but hour choice spans 36.11 ppm.** | 19.40 |
| **200** | **Sorong’s least-biased fixed hour is 09:00 (−0.51 ppm), and its hourly bias span is 18.83 ppm.** | 19.40 |

---

# Part I — The archive, its defects, and an external check

## 1. The network and the data

### 1.1 The five in-situ stations

**Table 2 — Indonesian in-situ greenhouse-gas monitoring stations**

| Code | Station | Region | Setting | Lat | Lon | Elev | Record | Hours | Coverage |
|---|---|---|---|---|---|---|---|---|---|
| BKT | Bukit Kototabang | West Sumatra | Remote mountain (GAW Global) | 0.20 °S | 100.32 °E | 865 m | 2001-07-20 → 2024-12-31 | 161,866 | 78.7 % |
| JMB | Jambi | Jambi, Sumatra | Lowland peat / plantation | 1.61 °S | 103.65 °E | 25 m | 2023-11-24 → 2025-12-04 | 14,486 | 81.5 % |
| KMY | Kemayoran | Jakarta | Megacity urban core | 6.16 °S | 106.85 °E | 8 m | 2023-11-29 → 2025-12-07 | 16,495 | 93.0 % |
| PLU | **Bariri, Lore Lindu** | Central Sulawesi | Montane rainforest (GAW Regional) | ~1.20 °S | ~120.03 °E | ~1,400 m | 2021-10-10 → 2026-07-04 | 32,773 | 79.0 % |
| SRG | Sorong | Southwest Papua | Coastal small city | 0.86 °S | 131.29 °E | 10 m | 2021-09-12 → 2025-12-06 | 16,791 | 45.3 % |

*The station code `PLU` refers to the **Bariri** site inside Lore Lindu National Park, roughly 60 km south-east of Palu city — montane primary rainforest at about 1,400 m, not an urban site. This matters for interpretation and is reflected throughout. Its coordinates and elevation are approximate and should be confirmed against the station record; none of the analysis depends on them.*

### 1.2 The NOAA flask record

Bukit Kototabang is also a NOAA Global Monitoring Laboratory cooperative flask site, operated with BMKG and sampled in pairs roughly weekly since 8 January 2004. Two thousand and two sample pairs have been analysed at Boulder, each on a declared WMO scale:

**Table 3 — NOAA flask species, scales, coverage, and quality-control pass rates**

| Species | Scale | Period | Pairs | QC pass |
|---|---|---|---|---|
| CO₂ | CO2_X2019 | 2004-01 → 2025-12 | 2,002 | 69.1 % |
| CH₄ | CH4_X2004A | 2004-01 → 2025-12 | 2,002 | 97.4 % |
| CO | CO_X2025 | 2004-01 → 2025-12 | 2,002 | 90.9 % |
| N₂O | N2O_X2006A | 2004-01 → 2025-12 | 2,002 | 96.4 % |
| SF₆ | SF6_X2014 | 2004-01 → 2025-12 | 2,002 | 97.0 % |
| H₂ | H2_X2009 | 2009-09 → 2024-12 | 1,345 | 95.9 % |

This record matters out of all proportion to its size. It is drawn from the same site as one of the five in-situ stations, so a flask sample and an in-situ hour can be compared directly; it is analysed by a different laboratory on traceable scales, so it can settle absolute questions the archive cannot ask of itself; and it carries **three species the hourly archive does not measure at all** — N₂O, SF₆ and H₂ — one of which (SF₆) turns out to answer a question about transport that no amount of CO₂, CH₄ and CO could.

Five reference sites are also used, so that quantities like the interhemispheric gradient are *measured* rather than quoted: Barrow (71.3 °N), Mauna Loa and Cape Kumukahi (19.5 °N), Tutuila/Samoa (14.2 °S) and the South Pole.

### 1.3 Units are not consistent across the archive

The five JSON files do not share a unit convention, and nothing in the files declares one:

- **BKT** — CO and CH₄ are already in **ppb**; only dry-air fields (`co2d`, `ch4d`) are present, and CO₂/CH₄ are absent before 2009 and between 2014 and 2018.
- **JMB, KMY, PLU, SRG** — CO and CH₄ are in **ppm** (values like `0.371`, `2.085`); both wet (`co2`, `ch4`) and dry (`co2d`, `ch4d`) fields are present.

Everything below is **ppm for CO₂ and ppb for CH₄ and CO**, using the dry-air mole fraction where available. Mixing the conventions would put BKT's methane 1,000× off.

**The "wet" fields carry no water-vapour information.** In the four stations reporting both, the ratio `co2`/`co2d` has a median of 0.99949–0.99976 — an implied water content of 0.02–0.05 % by volume, where real tropical surface air holds 2–3 %. Whatever the `co2` field is, it is not a wet-air mole fraction. The archive therefore cannot be used to reconstruct humidity, and a dilution error can be ruled out as an explanation for any offset.

### 1.4 Bukit Kototabang is a composite of several instruments

The BKT file genuinely begins on 20 July 2001 — 265 valid hours in that part-month, near-continuous from the start — but the record is not homogeneous:

**Table 4 — Bukit Kototabang measurement eras and reported precision**

| Era | Species present | CO reported precision |
|---|---|---|
| 2001-07 → 2008 | **CO only** | 0.1 ppb (1 dp) |
| 2009-11 → 2013 | CO, CO₂, CH₄ | 0.1 ppb |
| 2014 → 2018 | **CO only** (CO₂/CH₄ gap) | 0.1 ppb → 0.01 ppb at 2015 |
| 2019 → 2020 | CO, CO₂, CH₄ | 0.01 ppb, mixed in 2020 |
| 2021 → 2024 | CO, CO₂, CH₄ | 0.001 ppb from 2022 |

A G2401 measures CO₂, CH₄, CO and H₂O simultaneously and was not available commercially until around 2010, so the 2001–2008 CO-only segment must come from a different instrument. CO₂ and CH₄ first appear in November 2009. The reported-precision changes corroborate this. **BKT should be treated as a multi-instrument composite** — and Section 4.3 turns this inference into a measurement.

This is why the report says "hourly CO₂ / CH₄ / CO records" rather than "Picarro G2401 records".

---

## 2. Defect 1: the time base — Finding 1

This is the most consequential thing in the archive, and it is invisible unless you look at the diurnal cycle.

Over a land surface the physics is not negotiable: the boundary layer is deepest in mid-afternoon, so CO₂, CH₄ and CO all reach their **minimum around 13:00–16:00 local** and their **maximum just after sunrise**. As archived, the five stations do not agree on when that minimum occurs (Figure 1b):

**Table 5 — Archived diurnal minima and their implied local times**

| Station | Hour of CO₂ minimum, as archived | Implied local time if the stamp were UTC |
|---|---|---|
| JMB | 07–09 | 14–16 ✓ |
| KMY | 07–09 | 14–16 ✓ |
| PLU | 05–07 | 13–15 ✓ |
| SRG | 04–06 | 13–15 ✓ |
| **BKT (to 2020)** | **13–15** | 20–22 ✗ |
| **BKT (2021 on)** | **07** | 14 ✓ |

The four newer sites are self-consistent under "stamp = UTC". **Bukit Kototabang is not one station in this respect — it is two.** Splitting the BKT record by quarter and taking the first-harmonic phase of the diurnal CO₂ cycle makes the break unmistakable: the hour of the CO₂ maximum sits at **2.2–3.6 h for every quarter from 2010Q1 to 2020Q4**, then jumps to **18.7–20.4 h for every quarter from 2021Q1 onward**:

**Table 6 — Bukit Kototabang timestamp discontinuity across 2020–2021**

| Month | CO₂ diurnal max (h, as archived) | Month | CO₂ diurnal max (h, as archived) |
|---|---|---|---|
| 2020-08 | 2.7 | **2021-01** | **20.2** |
| 2020-09 | 2.4 | 2021-02 | 20.8 |
| 2020-10 | 2.2 | 2021-03 | 20.2 |
| 2020-11 | 2.6 | 2021-04 | 20.5 |
| 2020-12 | 3.6 | 2021-05 | 21.6 |

The shift is 16.8 h forward, i.e. **−7.2 h — exactly the WIB offset** — between 31 December 2020 and 1 January 2021, with no transition. Almost certainly a change of acquisition or processing system at the turn of the year.

**The correct rule:**

**Table 7 — Time-base corrections applied to the archive**

| Records | Stamp convention | Shift applied |
|---|---|---|
| BKT, to 2020-12-31 | Local time (WIB) | none |
| BKT, from 2021-01-01 | UTC | +7 h |
| JMB, KMY | UTC | +7 h |
| PLU (Bariri) | UTC | +8 h |
| SRG | UTC | +9 h |

After correction the CO₂ diurnal phase at BKT is stable at 1.7–3.6 h local across all fifteen years, and all five stations place their afternoon minimum in the well-mixed window (Figure 1c). Three internal checks support it — CH₄ agrees with CO₂ in both BKT eras; Jakarta's CO peaks at 07:00 local (morning rush) only under "stamp = UTC"; and after conversion all five sites' diurnal phases agree to within about an hour.

**Section 4.1 then confirms it from outside the archive**, which is what raises this from a strong inference to an established fact.

**Why it is not cosmetic.** The regional background used throughout this report is the 20th percentile of hours 12:00–16:00. On the uncorrected timestamps that window selects 19:00–23:00 local for BKT from 2021 — the nocturnal build-up, not the well-mixed afternoon. Every 2021+ monthly baseline is biased high by about 10 ppm, which manufactures a step at the switch date and doubles the fitted CO₂ growth rate (Section 12.1).

![Figure 1](figures/f1_coverage_timebase.png)

**Figure 1.** (a) Hourly data availability by station and species. (b) Diurnal CO₂ composite as archived — the daily minimum (circled) is scattered across ten hours. (c) After conversion to local time, all five minima fall in the well-mixed afternoon. Panel b pools BKT's whole record and so blends its two conventions.

---

## 3. Defect 2: instrumental episodes, and the quality control applied

Two layers of QC were applied. **Hourly range gates** removed physically impossible values (CO₂ outside 340–3,000 ppm; CH₄ outside 1,600–15,000 ppb; CO outside −30 to 6,000 ppb) — this caught, for example, Sorong records with CO₂ = −0.1 ppm and CH₄ = 0. The gates are deliberately wide: real urban and fire plumes *are* extreme.

**Suspect-period flags** then excluded stretches where the monthly baseline moves further than the atmosphere can. Across the network the month-to-month change in the afternoon 20th-percentile CO₂ baseline has a median of 0.79–1.01 ppm and a 90th percentile of 2.0–3.7 ppm; anything beyond ~5 ppm in one month is instrumental.

**Table 8 — periods excluded from baseline, trend and seasonal analysis** (hourly data are flagged, not deleted, so episode analysis still uses them):

| Station | Species | Period | Reason |
|---|---|---|---|
| BKT | CO₂ | Oct–Nov 2013 | Baseline drops 20 ppm and recovers; CH₄ drops with it, CO does not — analyser fault |
| BKT | CO₂ | Dec 2020 – May 2021 | +9.2 ppm offset, not mirrored in CH₄ or CO |
| SRG | all | Sep 2021 – May 2023 | CO₂ baseline 15–50 ppm above the post-2023 level; CO baseline up to 233 ppb |
| SRG | all | Mar 2023 | CO₂, CH₄ and CO collapse together (CO ≈ 2 ppb) — zero-air/valve fault |

After flagging, **Sorong's usable record effectively begins in June 2023** and it is excluded from trend estimation.

The diagnosis and empirical repair of the two BKT CO₂ episodes is a trend-related matter and is set out in Section 12.2. The flask record independently confirms the 2013 fault (Section 4.2).

### 3.1 Finding 79 — what the archive actually delivers, year by year

QC decides which hours are *usable*; it says nothing about how many hours arrived. For anything built on an annual budget — and every carbon-accounting use is — the second number is the binding one, so it is measured here rather than assumed. Uptime is the count of hours carrying a finite value, divided by the hours in that station's own coverage window for that year, so a station that began in November is not charged for the ten months before it existed.

**Table 9 — data return by station and year, the three most recent full years, with Bukit Kototabang's CO₂ history** (from `outputs/p_uptime.csv`):

| Station | Year | CO₂ return | CH₄ return | CO return |
|---|---|---|---|---|
| BKT | 2013 | 92.3 % | 92.4 % | 99.3 % |
| BKT | 2014–2018 | 0.0 % | 0.0 % | 87.2–97.0 % |
| BKT | 2022 | 98.2 % | 98.2 % | 98.2 % |
| BKT | 2023 | 96.1 % | 96.1 % | 96.1 % |
| JMB | 2024 | 88.3 % | 88.3 % | 88.3 % |
| JMB | 2025 | 74.9 % | 74.9 % | 74.9 % |
| KMY | 2024 | 95.0 % | 95.0 % | 95.0 % |
| KMY | 2025 | 90.5 % | 90.5 % | 90.5 % |
| PLU | 2024 | 95.5 % | 95.5 % | 95.5 % |
| PLU | 2025 | 65.7 % | 65.7 % | 65.6 % |
| SRG | 2024 | 55.7 % | 55.7 % | 55.6 % |
| SRG | 2025 | 84.2 % | 84.2 % | 84.2 % |

Three things follow. **Bukit Kototabang is two records, not one.** Its CO series runs from 2001 at 49–99 % return; its CO₂ and CH₄ series begin in 2009, reach usable return in 2011, and then vanish entirely for the five years 2014–2018 while CO continues at 87–97 %. Twelve of the twenty-five calendar years carry any CO₂ at all, and only nine clear 50 % return. Anything that treats the site as a twenty-five-year CO₂ station is wrong about it.

**Return and precision are separate properties.** Sorong returns 55.7 % of 2024 and 84.2 % of 2025 and is still, after flagging, the site with the least usable record (Finding 50). Bariri returns 95.5 % in 2024 and 65.7 % in 2025 and is the network's cleanest reference. Neither ranking follows from the other.

**Only Kemayoran has cleared 90 % in every complete year it has existed.** For the newer stations that is the number to watch, because it is the one that decides whether an annual statement is possible at all.

> **What this is not.** Uptime counts hours with a value, after the range gates of this section but before the suspect-period flags — a station can return 99 % of its hours and have all of them excluded, which is exactly what Sorong did in 2022. The two tables must be read together.

---

## 4. The external check — Findings 2 to 6

Everything in Sections 2 and 3 is *differential*: one station against another, one era against another, one species against another. Differential tests are powerful and structurally blind to a common-mode error. The NOAA flask record is the only way to see past that limitation, and it changes four things.

![Figure 2](figures/f2_flask_validation.png)

**Figure 2.** (a) Every flask sample plotted against the in-situ hour it was drawn in, under both time-base conventions; the dashed line is 1:1. (b) Annual median flask-minus-in-situ for CO. (c) The seasonal component of BKT's methane against that of SF₆, coloured by month (discussed in Section 10.2).

### 4.1 Finding 2 — the time-base correction is confirmed from outside

Pairing each flask sample with the in-situ hour it was drawn in, under both conventions:

**Table 10 — flask minus in-situ, matched hour**

| Species | Time base | n | Median | s.d. | IQR | *r* |
|---|---|---|---|---|---|---|
| CO₂ | delivered stamp treated as UTC | 212 | −8.50 ppm | 14.12 | [−22.66, +0.03] | 0.28 |
| **CO₂** | **corrected (Section 2)** | 214 | **+0.31 ppm** | **9.16** | **[−0.92, +1.11]** | **0.77** |
| CH₄ | delivered stamp treated as UTC | 291 | −2.81 ppb | 44.24 | [−21.65, +1.69] | 0.74 |
| **CH₄** | **corrected** | 291 | **−0.85 ppb** | **10.13** | **[−3.91, +1.69]** | **0.98** |
| CO | delivered stamp treated as UTC | 683 | −10.21 ppb | 45.84 | [−34.13, +3.33] | 0.87 |
| CO | corrected | 691 | −5.24 ppb | 42.72 | [−26.11, +2.97] | 0.88 |

The correction moves CO₂ from an 8.5 ppm median discrepancy at *r* = 0.28 to a 0.31 ppm discrepancy at *r* = 0.77, and it cuts the CH₄ scatter by a factor of four while raising the correlation to 0.98. **A wrong time base cannot be made to look like this, and a right one cannot be made to look like the raw column.** Finding 1 is no longer an inference from the diurnal cycle; it is confirmed by a second instrument.

*(CO improves less because CO is dominated by short-lived plumes, so even a perfectly aligned flask and hourly mean sample different air. Its residual scatter of 42.7 ppb is atmospheric variability — see Section 4.3 for the part that is error.)*

### 4.2 Finding 3 — the in-situ CO₂ and CH₄ are on the WMO scale

**Table 11 — annual median flask minus in-situ, corrected time base**

| Year | CO₂ (ppm) | CH₄ (ppb) |
|---|---|---|
| 2010 | −0.18 | −5.09 |
| **2013** | **+8.70** | +0.74 |
| 2019 | +0.42 | −0.71 |
| 2020 | +0.38 | −0.57 |
| 2021 | −0.95 | −1.88 |
| 2022 | +0.14 | −1.26 |
| 2023 | −0.33 | +0.50 |
| 2024 | — | −2.17 |

Post-2019 the two instruments agree to better than 1 ppm in CO₂ and 2.2 ppb in CH₄ every year. **There is no CO₂ scale problem at Bukit Kototabang.** Section 15 records how an earlier draft concluded otherwise and why it was wrong.

The 2013 row is the exception, and it is a confirmation rather than a problem: the flasks read **8.70 ppm above** the in-situ record in the year of the Oct–Nov analyser fault flagged in Table 8. An independent instrument sees the fault the internal diagnosis found, at the right sign and a consistent magnitude.

### 4.3 Finding 4 — the pre-2019 CO record is biased high

CO is a different story, and it is the defect no internal check could have found.

**Table 12 — annual median flask minus in-situ CO (ppb), and the ratio flask/in-situ**

| Year | Δ | ratio | | Year | Δ | ratio |
|---|---|---|---|---|---|---|
| 2004 | +3.5 | 1.05 | | 2015 | −9.4 | 0.90 |
| 2005 | −3.2 | 0.91 | | 2016 | −22.5 | 0.81 |
| 2006 | −5.7 | 0.93 | | **2017** | **−41.0** | **0.66** |
| **2007** | **−23.0** | **0.75** | | **2018** | **−41.1** | **0.71** |
| 2008 | −9.2 | 0.88 | | **2019** | **+1.0** | **0.98** |
| **2009** | **−20.9** | **0.76** | | **2020** | **+0.7** | **1.01** |
| **2010** | **−41.0** | **0.76** | | **2021** | **+0.6** | **1.06** |
| 2013 | −5.3 | 0.91 | | **2022** | **+1.8** | **1.01** |
| 2014 | +8.9 | 1.00 | | **2023** | **+4.3** | **1.07** |
| | | | | **2024** | **+1.9** | **1.05** |

The in-situ analyser reads **10 to 41 ppb too high through 2007–2018**, by a factor wandering between 0.66 and 0.93, then agrees to within a few ppb **from 2019 onward** — a step, not a drift, at exactly the date the analyser complement changes (Section 1.4). The instrument-composite inference of Section 1.4, made from species availability and reported decimal places, is thereby confirmed by a bias step against an independent reference.

**Consequence:** the pre-2019 in-situ CO series cannot support a trend. Section 9.6 replaces it with the flask record, which spans 2004–2025 on one scale and gives a longer and sounder answer than the in-situ record ever could.

### 4.4 Finding 5 — the Maritime Continent is a CO₂ minimum

![Figure 3](figures/f3_flask_network.png)

**Figure 3.** (a) Mean flask CO₂ 2015–2025 by station latitude. (b) SF₆ seasonal amplitude by site (Section 10.1). (c) Flask CO percentiles by year with Theil–Sen trends (Section 9.6).

**Table 13 — flask mean CO₂ and seasonal amplitude, 2015–2025**

| Site | Latitude | Mean CO₂ (ppm) | Seasonal amplitude (ppm) |
|---|---|---|---|
| BRW Barrow | +71.3 | 415.30 | 17.66 |
| KUM Cape Kumukahi | +19.5 | 414.37 | 8.53 |
| MLO Mauna Loa | +19.5 | 414.02 | 6.86 |
| SMO Samoa | −14.2 | 411.60 | 1.30 |
| SPO South Pole | −90.0 | 409.96 | 1.28 |
| **BKT Bukit Kototabang** | **−0.2** | **408.53** | **5.53** |

Bukit Kototabang is **the lowest of the six**, 5.5 ppm below Mauna Loa and **1.4 ppm below the South Pole**. This is measured by NOAA on the X2019 scale, at a site whose in-situ instrument agrees with those same flasks to 0.3 ppm.

The Maritime Continent is therefore a real regional CO₂ minimum, and the explanation is not mysterious: it sits under the warm pool, where deep convection continually brings down free-tropospheric air, and it is surrounded by the largest area of year-round-productive tropical forest on Earth. This is what the other four Indonesian stations are also seeing when they read low.

### 4.5 Finding 6 — what NOAA's own QC says about the site

**Table 14 — NOAA flask quality-control rejection rates**

| Species | Samples | Rejected | Dominant flag |
|---|---|---|---|
| **CO₂** | 2,002 | **30.9 %** | C.. |
| CO | 2,002 | 9.1 % | C.. |
| H₂ | 1,345 | 4.1 % | C.M |
| N₂O | 2,002 | 3.6 % | C.. |
| SF₆ | 2,002 | 3.0 % | C.. |
| CH₄ | 2,002 | 2.6 % | C.. |

Nearly a third of Bukit Kototabang's CO₂ flasks fail NOAA's checks, against 2.6 % of CH₄ from the *same physical flask*. The difference cannot be sampling or handling — those would reject both species together. It is that CO₂ at this site is unusually often unrepresentative of background air, which is what a mountain ridge with vegetated slopes and upslope daytime flow produces. Any future analysis using BKT CO₂ should expect to discard a comparable fraction; the 20th-percentile afternoon background used in this report is one way of doing so.

### 4.6 Findings 49 and 50 — the diurnal rectifier, and the one check a station can run alone

Every external validation in this section needed a second instrument. There is one that does not.

Over land the nocturnal boundary layer is shallow and accumulates whatever the surface emits; by mid-afternoon it is deep and the same emissions are diluted through a far larger volume. It follows that **a surface station's 24-hour mean CO₂ must exceed its afternoon mean.** The difference — the *diurnal rectifier* — is a positive number at every honest surface site, and its sign is not a matter of calibration, scale or units. It is a consequence of the boundary layer having a daily cycle.

![Figure 4](figures/f4_rectifier_eid.png)

**Figure 4 — the diurnal rectifier, and a week when Jakarta stopped driving.** (a) The rectifier at each station, with the bar showing the annual mean and the whisker the range of monthly means. (b) The same statistic split at the June 2023 boundary Section 15.4 identified by a different route; red marks a period whose rectifier is negative. (c) The Idul Fitri experiment of Section 7.5.

**Table 15 — the diurnal rectifier, by station**

| Station | Days | Rectifier (ppm) | Monthly range | Negative days |
|---|---|---|---|---|
| SRG Sorong *(from Jun 2023)* | 592 | **+8.3** | +3.9 to +10.3 | 0.8 % |
| BKT Bukit Kototabang | 2,857 | **+10.8** | +9.7 to +11.9 | 1.2 % |
| KMY Kemayoran | 691 | **+11.3** | +7.5 to +13.9 | 2.0 % |
| PLU Bariri | 1,394 | **+17.0** | +15.2 to +19.5 | 0.0 % |
| JMB Jambi | 605 | **+18.3** | +14.1 to +21.9 | 0.2 % |

**Finding 49 — afternoon-only sampling understates CO₂ by 8 to 18 ppm.** That is not an error in this report, which uses the afternoon deliberately and consistently; it is a statement about what an afternoon-selected number *means*. The NOAA flask programme samples in the afternoon; most inverse modelling assimilates afternoon values; the regional background used throughout this report is an afternoon percentile. All of them are measuring the well-mixed free troposphere on purpose — but **none of them is measuring the air a person breathes, or the mean burden over the site**, and the gap between the two is 8–18 ppm, four to eight times the entire interhemispheric gradient.

The ordering is physically ordered, which is the check that the statistic is measuring what it claims: the two lowland vegetated sites, Jambi and Bariri, have the largest rectifiers; the mountain ridge and the megacity have intermediate ones; and Sorong, a coastal site where the marine boundary layer never fully decouples, has the smallest.

**Finding 50 — a negative rectifier is a data-quality flag that needs nothing external.** Splitting the statistic at June 2023, the date Section 15.4 arrived at from baseline continuity:

**Table 16 — the rectifier as a quality test**

| Station | Period | Days | Rectifier (ppm) | Negative days | Physical? |
|---|---|---|---|---|---|
| BKT | before Jun 2023 | 2,569 | +10.7 | 1.3 % | yes |
| BKT | from Jun 2023 | 288 | +12.2 | 0.0 % | yes |
| PLU | before Jun 2023 | 540 | +16.2 | 0.0 % | yes |
| PLU | from Jun 2023 | 854 | +17.5 | 0.0 % | yes |
| JMB | from Jun 2023 | 605 | +18.3 | 0.2 % | yes |
| KMY | from Jun 2023 | 691 | +11.3 | 2.0 % | yes |
| **SRG** | **before Jun 2023** | **138** | **−29.2** | **47.1 %** | **no** |
| SRG | from Jun 2023 | 592 | +8.3 | 0.8 % | yes |

**Sorong's pre-June-2023 record has a rectifier of −29.2 ppm, with 47 % of days negative.** No boundary layer produces that. The period was already flagged in this report as failing baseline continuity, and it is flagged again here — but by a test that used no reference site, no flask programme, no second station and no external standard. **A station can run this check on its own data, on the day it is collected.**

That is worth stating plainly because Section 15.1 records the opposite lesson: an absolute claim about a differential network needs an external anchor. The rectifier is the exception, and it is the exception for a specific reason — it is a *sign* test on an internal difference, and a sign is invariant to every constant offset and scale factor an instrument can be wrong by.

> **Its limits.** It detects gross defects, not subtle ones: a station with a 5 ppm calibration offset has a perfectly healthy rectifier, and a station whose day and night are *both* wrong by the same amount looks fine. It also assumes a land site with a real diurnal cycle — a genuinely marine station, or an aircraft, has no such expectation. Use it as a first filter, not as a calibration.

### 4.7 Finding 58 — NOAA flask pair reproducibility and single-flask measurement uncertainty

Every discrete sampling programme carries random sampling and handling noise on top of analytical repeatability. At Bukit Kototabang, NOAA GML has collected paired flasks roughly weekly across 22 years (2004–2025). The difference between concurrent flask samples $|x_1 - x_2|$ measures the real-world operational precision of the discrete measurement pipeline:

**Table 17 — flask pair agreement and sampling precision at Bukit Kototabang (2004–2025)** (from `outputs/t_flask_pairs.csv`)

| Species | Unit | Pairs | Median \|diff\| | Mean \|diff\| | 95th pct | Single-flask $\sigma$ | Robust $\sigma$ | RMS/mean |
|---|---|---|---|---|---|---|---|---|
| CO₂ | ppm | 674 | **0.195** | 0.211 | 0.450 | **0.179** | 0.204 | 1.20 |
| CH₄ | ppb | 960 | **0.610** | 1.012 | 3.252 | **1.103** † | 0.639 | 1.54 |
| CO | ppb | 895 | **0.510** | 0.693 | 2.043 | **0.672** † | 0.535 | 1.37 |
| N₂O | ppb | 946 | **0.110** | 0.204 | 0.738 | **0.222** † | 0.115 | 1.54 |
| SF₆ | ppt | 954 | **0.030** | 0.035 | 0.090 | **0.031** | 0.032 | 1.27 |
| H₂ | ppb | 634 | **0.700** | 0.903 | 2.345 | **0.842** | 0.734 | 1.32 |

Single-flask random uncertainty is **0.18 ppm for CO₂, 1.10 ppb for CH₄, 0.67 ppb for CO, 0.22 ppb for N₂O, 0.031 ppt for SF₆, and 0.84 ppb for H₂**. For CO₂, 95 % of duplicate pairs agree within 0.45 ppm, so a single flask carries a random error about **13 times smaller than one year's CO₂ growth** (2.3 ppm yr⁻¹).

**The estimator, and two wrong versions of it.** The archive records $|x_1 - x_2|$, the *unsigned* pair difference. That is a folded variable, and neither its mean nor its standard deviation is the standard deviation of the signed difference $d$:

$$\langle|d|\rangle = \sigma_d\sqrt{2/\pi} = 0.798\,\sigma_d, \qquad \operatorname{sd}(|d|) = \sigma_d\sqrt{1 - 2/\pi} = 0.603\,\sigma_d$$

Dividing either by $\sqrt2$ understates $\sigma_{\text{single}} = \sigma_d/\sqrt2$ — by 20 % for the first and 40 % for the second. **The second moment survives the fold exactly**, because $d^2 \equiv |d|^2$, so

$$\sigma_{\text{single}} = \frac{\operatorname{RMS}(|d|)}{\sqrt2}$$

with no distributional assumption at all. That is the "Single-flask $\sigma$" column. *Both earlier estimators appeared in drafts of this table and are superseded (Section 15.6).*

> **† CH₄ and N₂O have heavy-tailed pair differences.** Their RMS/mean ratio is 1.54 against the 1.253 a normal $d$ would give, so a handful of bad pairs dominates the second moment. The "Robust $\sigma$" column reads the same quantity off the median instead (the median of a half-normal is $0.6745\,\sigma$), which the outliers cannot move: 0.64 ppb for CH₄ and 0.12 ppb for N₂O. **For those two species the true typical precision lies between the two columns**; for CO₂ and SF₆, where RMS/mean is near 1.25, they agree and either can be used.

![Figure 5](figures/f5_flask_pairs_sf6_vert.png)

**Figure 5 — flask reproducibility, interhemispheric transport lag, and vertical stratification.** (a) Flask pair absolute difference distribution and 95th percentiles across six species at Bukit Kototabang. (b) SF₆ transport lag clock: mean concentration deficit behind Barrow (71°N) and lead over the South Pole (90°S) converted to transport time in months. (c) Standardized vertical difference between Mauna Loa (3,397 m) and Cape Kumukahi (3 m) at 19.5°N.

> **Its limits.** Intra-pair reproducibility measures random sampling and flask-filling noise; it cannot detect systematic scale offsets, sample-line contamination before the manifold, or time-of-day sampling bias.

### 4.8 Finding 83 — the two instruments also agree on the *trend*, to about ±0.8 ppm yr⁻¹

Section 4.2 compares levels. A carbon-accounting use would not rest on levels: it would rest on a change over time, and a slow instrumental drift is invisible to a level comparison made once. So the same two independent systems — the continuous analyser run by BMKG and the weekly glass flasks analysed at NOAA GML from the same hilltop — are each reduced to a growth rate by Theil–Sen and compared directly.

The comparison starts in July 2021, after the analyser change and after the last flagged CO₂ episode, so it is not carrying a known instrumental step.

**Table 18 — CO₂ growth rate from two co-located, independent measurement systems** (from `outputs/p_insitu_vs_flask.csv`):

| Series | Months | Growth (ppm yr⁻¹) | 95 % CI |
|---|---|---|---|
| In-situ, afternoon 20th percentile | 33 | **2.938** | 2.411 – 3.687 |
| NOAA flask monthly mean | 42 | **3.753** | 2.805 – 4.548 |
| Difference (in-situ − flask) | — | **−0.815** | intervals overlap over their whole width |

The two agree, and the honest way to state the agreement is as a *precision* rather than as a confirmation: over three and a half years, two independent instruments at one site pin the growth rate to within about ±0.8 ppm yr⁻¹ of each other. That is the resolution of the strongest verification test this network can run, and it is a third of one year's growth.

The number matters because it is the ceiling on every trend-based claim downstream. A crediting scheme that needed to distinguish 2.9 from 3.8 ppm yr⁻¹ at this site, today, could not do it — not because either instrument is poor, but because 42 months is a short record for a trend (Finding 52 puts CO₂ at 1.4 years and CO at 15.5).

> **What it does not show.** This is not a scale comparison; the two series use different statistics (a 20th percentile against a monthly mean) and differ in level by construction. Only the slopes are comparable. The flask series covers 42 months against the in-situ 33, because the in-situ background requires ≥20 valid afternoon hours in a month and some months do not have them — a fairer test would restrict both to the same months and would have fewer of them.

---

# Part II — Surface processes

## 5. The diurnal cycle — Findings 7, 29, 41

### 5.1 Shape is universal, amplitude is not

![Figure 6](figures/f6_diurnal.png)

**Figure 6.** Median diurnal composites. Shape (top, each site normalised by its own amplitude) and magnitude (bottom, log scale) are shown separately.


Once the time base is fixed the shape is nearly universal: build-up overnight, sharp collapse between 08:00 and 11:00 as the mixed layer deepens, afternoon minimum, recovery after sunset. The amplitude separates the sites by nearly two orders of magnitude:

**Table 19 — Median diurnal amplitudes by station and species**

| Station | CO₂ (ppm) | CH₄ (ppb) | CO (ppb) |
|---|---|---|---|
| BKT Bukit Kototabang | 19 | 24 | 8.7 |
| JMB Jambi | 45 | 153 | 94 |
| **KMY Kemayoran** | **30** | **461** | **645** |
| PLU Bariri | 37 | 15 | 20 |
| SRG Sorong | 19 | 23 | 33 |

**Jakarta's CO₂ amplitude (30 ppm) is smaller than Jambi's (45) and Bariri's (37)** even though its CO amplitude is 7× Jambi's and 32× Bariri's. A megacity does not have a small CO₂ signal; it has a comparatively small *fossil* CO₂ signal relative to the biological CO₂ that dominates the other sites' nocturnal build-up. Sections 6.4 and 7 quantify this.

### 5.2 Finding 7 — the morning erosion runs on the same clock everywhere

Fitting an exponential to the CO₂ decrease from 07:00 to 12:00 local toward each day's own afternoon floor, keeping only clean decays (*r* < −0.9):

**Table 20 — e-folding time of the morning CO₂ collapse**

| Station | Setting | Days | τ (hours) | IQR |
|---|---|---|---|---|
| PLU Bariri | montane rainforest, 1,400 m | 1,098 | **1.94** | 1.65 – 2.32 |
| JMB Jambi | lowland peat, 25 m | 470 | **2.05** | 1.70 – 2.56 |
| BKT Bukit Kototabang | mountain ridge, 865 m | 1,741 | **2.19** | 1.81 – 2.71 |
| KMY Kemayoran | megacity core, 8 m | 221 | **2.24** | 1.73 – 3.05 |
| SRG Sorong | coastal, 10 m | 230 | **2.38** | 1.87 – 3.17 |

The spread across five sites is **0.44 hours — under 30 minutes**. Surface cover, elevation, roughness and source strength vary enormously across that list and none of them matters. What all five share is latitude: every station lies within 6.2° of the equator, so all receive nearly the same insolation on nearly the same schedule year-round, and it is insolation that drives convective growth.

**τ ≈ 2 hours** is a usable constant for anyone designing a sampling protocol, a footprint model or a flux-inversion observation operator anywhere in the Maritime Continent.

### 5.3 Finding 29 — separating photosynthesis from dilution

Section 5.2 measured how fast the morning mixed layer erodes the nocturnal store. That decline mixes two processes: **dilution**, as the layer deepens, and **photosynthesis**, which removes CO₂ outright. A single species cannot separate them — but a second species can, because neither CH₄ nor CO has a photosynthetic sink. Their morning decline measures dilution alone, and whatever *extra* loss CO₂ shows is biological.

**Method.** For each morning, fit the exponential decay of both species toward that day's own afternoon floor (§5.2), and take the difference of the rate constants, *k* = 1/τ:

$$k_{\text{extra}} = k_{\text{CO}_2} - k_{\text{tracer}}$$

The comparison must be **paired** — both species measured on the *same* morning. Taking the median τ of CO₂ over all its usable days and the median τ of CH₄ over all of its own compares two different populations of mornings, and the two tracers then disagree by more than the effect being measured. Confidence intervals are from 2,000 bootstrap resamples of days.

![Figure 7](figures/f7_carbon.png)

**Figure 7.** (a) The extra CO₂ loss rate at each station, measured independently against CH₄ and against CO, paired by morning. (b) The nocturnal CO₂ excess relative to the CH₄ excess, normalised to its dawn value: a falling curve means CO₂ is being removed faster than dilution alone would remove it. (c) The station's own growth rate expressed in carbon-budget units (Section 12.7).

**Table 21 — extra CO₂ loss beyond dilution** (h⁻¹, 95 % bootstrap interval)

| Station | Setting | vs CH₄ | vs CO | Reading |
|---|---|---|---|---|
| **PLU Bariri** | montane primary rainforest | **+0.052 [+0.010, +0.094]** | **+0.124 [+0.092, +0.156]** | net daytime **sink** |
| **BKT Bukit Kototabang** | forested mountain ridge | **+0.023 [+0.000, +0.049]** | **+0.128 [+0.086, +0.172]** | net daytime **sink** |
| JMB Jambi | drained peat / plantation | −0.017 [−0.050, +0.011] | −0.001 [−0.062, +0.065] | indistinguishable from dilution |
| **KMY Kemayoran** | megacity core | **−0.072 [−0.122, −0.005]** | **−0.105 [−0.136, −0.086]** | net daytime **source** |

**The stations order by land cover, and the two tracers agree on the ordering.** The primary-rainforest site removes the most CO₂ beyond dilution; the forested ridge follows; the drained peatland shows nothing; and the megacity core has a *negative* value on both tracers.

**A negative value is not negative photosynthesis.** It means CO₂ declines *more slowly* than the inert tracers — which is what a continuous daytime source does. Kemayoran's traffic keeps replenishing CO₂ all morning while the nocturnal CH₄ and CO store simply dilutes away. **Under a megacity core there is no detectable net daytime carbon uptake at all**, and the sign of the measurement says so directly.

**Jambi's null is the interesting one.** An oil-palm plantation on drained peat photosynthesises perfectly well; what this says is that its daytime uptake is *cancelled* by the respiration Section 8 measures. Combined with that section's factor-of-1.9 excess, the picture is a landscape whose vegetation is productive and whose soil is losing carbon faster than the vegetation captures it.

**Why the two tracers differ in magnitude.** CH₄ gives a smaller estimate than CO at every site, because CH₄ itself has a continuing daytime surface source — soil, wetland, canals — so it dilutes more slowly than a truly inert tracer and understates the CO₂ sink. CO's daytime source at the clean sites is negligible, so it is the better dilution tracer there. **The CH₄-based number is a lower bound and the CO-based number an upper one**; the truth is bracketed.

> **Caveat.** A null test run through the *night*, when there is no photosynthesis, shows the CO₂-to-tracer ratio is not perfectly constant: it is flat at Bukit Kototabang (+6 % over 1,380 nights, so the method is clean there) but drifts by +35 % to +131 % at Bariri, Jambi and Sorong, and −35 % at Kemayoran. The drift is the nocturnal *source* ratio itself changing through the night, not a failure of dilution to act equally. At Bariri the drift is upward, which biases *against* the finding and makes the measured daytime fall a conservative one; at Kemayoran the drift is downward and in the same direction as the result, so Kemayoran's magnitude should not be read closely even though its sign is confirmed by both tracers. Sorong has too few paired mornings (37 and 29) and is omitted.

### 5.4 Finding 41 — the dry season amplifies the lowland sites, not the mountains

Splitting the diurnal composite by season:

**Table 22 — Wet- and dry-season CO₂ diurnal amplitudes**

| Station | Elevation | DJF (wet) | JJA (dry) | ratio |
|---|---|---|---|---|
| BKT Bukit Kototabang | 865 m | 17.6 ppm | 19.0 ppm | **1.08** |
| PLU Bariri | 1,400 m | 34.7 ppm | 37.5 ppm | **1.08** |
| JMB Jambi | 25 m | 40.5 ppm | 50.1 ppm | 1.24 |
| SRG Sorong | 10 m | 13.6 ppm | 22.6 ppm | **1.66** |
| KMY Kemayoran | 8 m | 18.7 ppm | 36.2 ppm | **1.93** |

The two montane stations barely notice the season; the three lowland ones swing by a quarter to nearly double. Clear dry-season skies make for stronger daytime convection *and* stronger nocturnal radiative cooling, so both ends of the diurnal cycle are exaggerated — but only where the station sits inside the layer that responds. At 865 m and 1,400 m the sites are near or above the nocturnal inversion for much of the year, and the seasonal modulation largely passes them by.

The practical consequence is for **anyone using diurnal amplitude as an index of surface emission**: at a lowland site nearly half the wet-to-dry change is meteorology, not source strength.

### 5.5 Finding 81 — hourly coupling between species identifies the source type

Diurnal amplitude says how much a site accumulates. It does not say *what* accumulates together, and that is the property a source attribution needs. The test is the correlation between hourly anomalies of two species, each taken against its own 30-day 20th-percentile background so that a shared seasonal cycle cannot manufacture the correlation. What survives is co-variation at the timescale of individual air masses — the timescale on which sources are physically co-located.

**Table 23 — hourly cross-species anomaly correlations** (from `outputs/p_species_coupling.csv`):

| Station | CO₂–CH₄ | CO₂–CO | CH₄–CO | Hours |
|---|---|---|---|---|
| BKT Bukit Kototabang | 0.451 | 0.195 | 0.440 | 66,458 |
| JMB Jambi | **0.650** | 0.401 | 0.578 | 14,461 |
| KMY Kemayoran | 0.602 | **0.848** | 0.448 | 16,472 |
| PLU Bariri | 0.182 | 0.387 | 0.388 | 32,712 |
| SRG Sorong | 0.156 | 0.233 | 0.115 | 16,486 |

Pearson coefficients are shown; Spearman gives the same ordering and is reported in the CSV, and the two diverge most at Kemayoran (0.848 against 0.835) and Sorong (0.156 against 0.428), where the distributions are most skewed.

**Kemayoran's CO₂ and CO move together at *r* = 0.85** — the signature of a single process emitting both, which for a megacity core means combustion, and which is Finding 8 arrived at from a different direction. **Jambi's strongest pair is CO₂–CH₄ at 0.65** with CO the weakest partner, the signature of a wet-organic source that emits both carbon gases and little combustion product: drained peat, as Section 8 concludes independently. **Bariri's three coefficients are 0.18 to 0.39** — no pair dominates, which is what an unpolluted montane site should look like.

Sorong is the anomaly: its Pearson CH₄–CO of 0.115 against a Spearman of 0.600 says the rank structure is there while the linear one is not, which is a distribution dominated by a few large events rather than a continuous source.

### 5.6 Finding 84 — the nocturnal accumulation rate, separated from the depth it is multiplied by

Every absolute flux in Part II is a measured accumulation rate times an assumed mixing depth. The two are usually reported already multiplied together, which hides that one has a confidence interval of a few per cent and the other a factor of four. They are separated here: the rate, per night, with a bootstrap interval over nights.

**Table 24 — nocturnal CO₂ accumulation rate, 20:00–02:00 local** (from `outputs/p_nocturnal_rate.csv`):

| Station | Nights | Rate (ppm h⁻¹) | 95 % CI | Nights positive |
|---|---|---|---|---|
| JMB Jambi | 611 | **3.155** | 2.986 – 3.511 | 87.4 % |
| PLU Bariri | 1,367 | 1.980 | 1.892 – 2.134 | 90.8 % |
| KMY Kemayoran | 688 | 1.581 | 1.324 – 1.834 | 78.2 % |
| BKT Bukit Kototabang | 2,823 | 1.423 | 1.342 – 1.497 | 88.4 % |
| SRG Sorong | 688 | 0.782 | 0.609 – 0.960 | 75.1 % |

The measurement is tight: the widest interval, at Sorong, spans ±22 % of its own median, and Jambi's spans ±8 %. **Jambi accumulates 1.6× as fast as the intact-forest reference at Bariri and twice as fast as the megacity** — the drained-peat result of Section 8, in the raw units, before any assumption enters.

The megacity ranking fourth of five is not an error and not a surprise: Kemayoran's nocturnal layer is warmer, more turbulent and more ventilated than a forest valley's, and 21.8 % of its nights do not accumulate at all. A city emits more and traps less.

> **Why this matters more than the flux.** The interval above is the only part of a nocturnal flux estimate that is measured. Section 7.3's flux and Finding 32's carbon loss both multiply one of these numbers by a depth between 100 and 400 m, and Finding 96 shows what that does to a monetised claim.

---

## 6. Source fingerprints from nocturnal ratios — Finding 8

### 6.1 One night is a chamber experiment

Within a single night the nocturnal boundary layer acts as an accumulation chamber over a roughly fixed footprint. Species from a common source co-vary linearly, and **the slope of that night's regression is the emission ratio of the surface source mix** — independent of dilution and of the absolute background, and therefore immune to any calibration question.

Each 18:00–08:00 block was regressed separately, keeping nights with ≥6 valid hours, ≥5 ppm of CO₂ build-up and *r*² ≥ 0.70.

### 6.2 Finding 8 — the ratios, station by station

![Figure 8](figures/f8_fingerprint.png)

**Figure 8.** (a) One point per tightly-coupled night; black bars are median and IQR. (b) The fraction of nights on which each species pair is tightly co-emitted at all.

**Table 25 — nightly emission ratios (median [IQR], n nights)**

| Station | ΔCO/ΔCO₂ (ppb ppm⁻¹) | ΔCH₄/ΔCO₂ (ppb ppm⁻¹) | ΔCH₄/ΔCO (ppb ppb⁻¹) |
|---|---|---|---|
| BKT | 1.79 [0.44, 3.10] (n=196) | 4.40 [2.99, 5.43] (n=380) | 1.12 [0.75, 1.58] (n=1066) |
| JMB | 1.63 [1.21, 2.91] (n=17 ⚠) | 4.43 [3.18, 5.57] (n=158) | 1.06 [0.64, 1.60] (n=64) |
| **KMY** | **23.50 [18.88, 30.93] (n=229)** | **16.29 [12.38, 20.52] (n=312)** | **0.64 [0.38, 0.89] (n=79)** |
| PLU (Bariri) | 0.51 [0.42, 0.59] (n=641) | 0.41 [−0.40, 0.99] (n=67) | 1.24 [0.76, 1.88] (n=102) |
| SRG | 1.64 [0.65, 3.39] (n=43) | 2.98 [1.63, 4.40] (n=140) | 0.64 [0.45, 0.93] (n=224) |

⚠ *Jambi's ΔCO/ΔCO₂ passes on only 17 of 627 nights (2.7 %) and is quoted for completeness. That low pass rate is itself the result.*

### 6.3 Jakarta's ΔCO/ΔCO₂ is 23.5 ppb ppm⁻¹, 13–46× every other site

**Kemayoran, ΔCO/ΔCO₂ = 23.5 ppb ppm⁻¹.** Efficient fossil combustion emits CO and CO₂ at roughly 3–15 ppb ppm⁻¹; smouldering biomass and peat run 60–200. Jakarta sits at 23.5 — above the efficient-combustion band and 13–46× the other four sites. As a modified combustion efficiency, ΔCO₂/(ΔCO₂+ΔCO) = 0.977 against 0.990–0.997 for a well-controlled fleet. The number is a **lower bound on the combustion signature**, because nocturnal ΔCO₂ at Kemayoran also contains biological respiration, which inflates the denominator.

**Bariri, ΔCO/ΔCO₂ = 0.51 ppb ppm⁻¹, on 44 % of all nights.** Essentially every ppm of nocturnal CO₂ at Bariri is biological respiration, which is what a station in montane primary rainforest inside a national park should show. Bariri is 46× cleaner than Jakarta on this metric and is the network's natural zero point.

**Jambi fails the CO–CO₂ coupling test on 97 % of nights but passes the CH₄–CO₂ test on 25 %.** Its nocturnal CO₂ build-up is decoupled from combustion and coupled to methane — soil, peat and plantation respiration paired with a co-located CH₄ source, with combustion only an occasional intruder. Section 8 identifies the surface.

### 6.4 An upper bound on Jakarta's fossil CO₂

Because CO is emitted only by combustion, it bounds the fossil share of Jakarta's CO₂. If the combustion mix emits CO and CO₂ in ratio *R*, the fossil part of an observed CO₂ enhancement is ΔCO / *R*. Applied to Kemayoran's **regional** enhancement over Bariri (Section 11: ΔCO = 151.8 ppb, ΔCO₂ = 10.3 ppm):

**Table 26 — Upper bounds on Jakarta fossil CO₂ under alternative combustion ratios**

| Assumed *R* (ppb ppm⁻¹) | Basis | Fossil CO₂ | Share |
|---|---|---|---|
| 15.0 | top of the efficient-fleet literature band | 10.1 ppm | 98 % |
| **23.5** | **measured nightly median — a *lower* bound on true *R*** | **6.5 ppm** | **≤ 63 %** |
| 30.9 | upper quartile of the nightly ratios | 4.9 ppm | 48 % |

Since Section 6.3 establishes *R* ≥ 23.5, and fossil CO₂ falls as *R* rises, that becomes an **upper bound: at most 63 % of Jakarta's regional CO₂ enhancement is fossil, and at least 37 % is not.** That is consistent with the small CO₂ diurnal amplitude of Section 5.1, the modest weekend response of Section 7, and the nocturnal flux of Section 8.1 that is only 1.2× the intact-forest reference.

### 6.5 Finding 85 — the one flux ratio that does not inherit the layer depth

The ratio of two species accumulating under the same nocturnal layer is the ratio of their surface fluxes, and the depth divides out exactly. It is the only quantity in this report that reaches a flux statement without the factor-of-two of Appendix C, and it is therefore the one worth reporting in the units an inventory uses.

Nights are kept only if the CO₂ accumulation exceeds 0.2 ppm h⁻¹, so that the denominator is a real build-up rather than noise; the median over nights is taken, and the interquartile range is carried because the distribution is wide.

**Table 27 — nocturnal CH₄:CO₂ accumulation ratio and its CO₂-equivalent share** (from `outputs/p_ch4_co2_signature.csv`; GWP-100 = 27.9):

| Station | Nights | CH₄:CO₂ (ppb ppm⁻¹) | IQR | CH₄ as CO₂e per unit CO₂ | CH₄ share of CO₂e |
|---|---|---|---|---|---|
| KMY Kemayoran | 515 | **20.46** | 12.64 – 39.37 | 0.208 | **17.2 %** |
| JMB Jambi | 524 | 3.04 | −0.07 – 6.50 | 0.031 | 3.0 % |
| SRG Sorong | 451 | 0.57 | −1.78 – 2.96 | 0.006 | 0.6 % |
| BKT Bukit Kototabang | 2,358 | 0.31 | −0.99 – 2.14 | 0.003 | 0.3 % |
| PLU Bariri | 1,204 | −0.04 | −0.54 – 0.51 | −0.000 | −0.0 % |

The reading is direct. **For every unit of CO₂ that Jakarta's surface adds to the air overnight, it adds methane worth 21 % as much again in CO₂-equivalent** — so 17.2 % of the climate forcing of the city's nocturnal emission is methane, and a carbon inventory that counted only its CO₂ would miss a sixth of the total. At Jambi the same figure is 3.0 %; at the two forest sites the ratio is statistically indistinguishable from zero, with interquartile ranges spanning it.

The ordering — megacity, drained peat, coastal town, mountain, rainforest — is the same as Finding 8's ΔCO/ΔCO₂ ordering, from a ratio that shares none of its arithmetic.

> **Read the IQR, not only the median.** Three of the five sites have an interquartile range that includes zero. Only Kemayoran and Jambi have a ratio that is resolved night to night; the other three are statements that the ratio is *small*, not measurements of how small.

---

## 7. Jakarta's methane — Findings 9, 10, 35

Kemayoran's methane is extraordinary. The 99th percentile is 4,798 ppb and the maximum 12,567 ppb. Even Jakarta's cleanest afternoon air, the 5th percentile of well-mixed hours, sits at 1,965 ppb — 65 ppb above Bariri's background. The annual median, 2,151 ppb, is +251 ppb over it.

### 7.1 Three lines of evidence that it is not combustion

**(i) The ΔCH₄/ΔCO ratio is ~50× too high for exhaust.** Kemayoran's nocturnal ΔCH₄/ΔCO is 0.64 ppb ppb⁻¹ directly, and 0.69 by the independent route of dividing the two ΔCO₂ ratios (16.29 / 23.50). Vehicle exhaust emits CH₄ and CO at roughly 0.005–0.02, so **combustion can account for only 0.8–3.1 % of the methane enhancement.**

**(ii) CO₂ barely responds to the weekend either** (−6.4 %), reinforcing Sections 6.3 and 6.4: most of Jakarta's observed CO₂ enhancement is biological and area-source, not tailpipe.

**(iii) The weekly cycle separates the two species decisively** — Section 7.2.

![Figure 9](figures/f9_jakarta_week.png)

**Figure 9.** Kemayoran weekly cycle. (a) The 07:00 rush-hour CO peak is 37 % lower on Sundays. (b–d) Sunday change relative to the Monday–Friday mean.

### 7.2 Finding 9 — the weekly cycle fires exactly once in 242,411 hours

The working week is the cleanest natural experiment in an air-quality record: it modulates human activity strongly and modulates nothing else. Running it across the whole network turns it into a detection-limit measurement.

**Method.** Each hourly value is expressed as an anomaly against the median for its own (calendar month, hour of day) cell, so neither the diurnal nor the seasonal cycle can leak in. Days are the resampling unit and medians the statistic — Kemayoran's hourly distributions are far too plume-skewed for means — with 95 % intervals from 3,000 bootstrap resamples of days.

![Figure 10](figures/f10_weekly_ladder.png)

**Figure 10.** (a) All fifteen station × species Sunday-minus-weekday tests on one axis; solid marks are significant, faded are not. (b–d) Each station's afternoon background minus Bariri's (Section 11).

**Table 28 — Sunday minus weekday** (ppm for CO₂, ppb for CH₄ and CO)

| | CO₂ | CH₄ | CO |
|---|---|---|---|
| BKT | +0.01 [−1.87, +1.45] | +0.12 [−8.83, +5.56] | −0.31 [−3.25, +3.14] |
| JMB | −0.17 [−1.41, +0.97] | −0.88 [−8.00, +11.00] | −5.13 [−16.63, +1.00] |
| **KMY** | −0.32 [−2.01, +2.11] | **+9.25 [−11.76, +28.50]** | **−38.63 [−64.00, −16.25]** ✓ |
| PLU | +0.27 [−0.79, +1.62] | +1.00 [−2.00, +2.75] | −0.25 [−2.00, +1.50] |
| SRG | −0.27 [−1.05, +0.68] | −0.75 [−5.63, +6.75] | −1.25 [−5.50, +1.75] |

One test in fifteen clears zero. Three things follow.

**It settles the methane question.** Jakarta's Sunday CH₄ effect is +9.25 ppb [−11.76, +28.50] — consistent with no weekly cycle at all — while CO in the same air on the same days falls by 39 ppb with an interval nowhere near zero. Two species, one site, one week, and only the combustion tracer knows what day it is. Landfills, wastewater, open sewers and canals emit continuously.

**Bariri's null is a quantitative cleanliness statement.** Sunday CO at Bariri is −0.25 ppb ± 2 ppb: any anthropogenic CO source reaching the station with a weekly rhythm contributes **less than about 2 ppb**. That is a stronger statement of background quality than a percentile baseline can make, and it belongs in the station's GAW metadata.

**The method has a floor.** Jambi's CO point estimate is −5.1 ppb — plausibly real — but its interval spans zero on 88 Sundays. Two years cannot resolve a weekly cycle smaller than roughly 10 % of the local signal; that is the practical detection limit for the four newer stations before about 2027.

### 7.3 Finding 10 — the flux, in the units an inventory uses

Applying the nocturnal budget of Section 8.1 to Kemayoran's methane, where the median coherent-night accumulation is 55.9 ppb h⁻¹ on 375 nights:

**Table 29 — Kemayoran nocturnal methane flux under alternative layer depths**

| Layer depth | Flux | Areal rate |
|---|---|---|
| 100 m | 0.065 µmol m⁻² s⁻¹ | 33 g CH₄ m⁻² yr⁻¹ |
| **200 m** | **0.129 µmol m⁻² s⁻¹** | **65 g CH₄ m⁻² yr⁻¹** |
| 400 m | 0.258 µmol m⁻² s⁻¹ | 131 g CH₄ m⁻² yr⁻¹ |

An areal emission of order **65 g CH₄ m⁻² yr⁻¹ sustained across a footprint of many square kilometres** is a landfill-scale flux density averaged over an entire urban surface — and this is the *background* of the city, not a hotspot. Over a 10³ km² footprint it implies of order 6 × 10⁴ t CH₄ yr⁻¹, roughly **2 Mt CO₂-equivalent per year** at GWP-100 = 27.9.

**Implication.** If ~97 % of the excess is non-combustion, methane mitigation aimed at transport will not move this signal. Waste and wastewater are where the reduction is, and this record provides a continuous, independent way to verify any intervention.

> **Caveat.** This is a single-site inference. Attributing the non-combustion fraction between landfill, wastewater, canals and gas-distribution leakage requires δ¹³C-CH₄ or ethane, neither of which the analyser provides. What the data establish firmly is *not traffic*. The flux also inherits the layer-depth assumption of Section 8.1, and a nocturnal footprint is a few kilometres, not a metropolitan area.

### 7.4 Finding 35 — the two ratios run in antiphase through the day

Section 7.2 used the working week to separate traffic from waste. The day does the same job at finer resolution, and more decisively. Taking enhancements over each calendar month's own 5th percentile — so the seasonal drift of the background cannot masquerade as a diurnal cycle — and computing both ratios hour by hour:

**Table 30 — Diurnal extrema of enhancement ratios at Kemayoran**

| | Maximum | Minimum |
|---|---|---|
| ΔCO/ΔCO₂ | **38.0 ppb ppm⁻¹ at 20:00** | 10.5 at 14:00 |
| ΔCH₄/ΔCO₂ | **16.4 ppb ppm⁻¹ at 03–04:00** | 10.3 at 15–16:00 |

**The two are in antiphase.** ΔCO/ΔCO₂ has two maxima — the morning rush at 07–09 and a larger evening peak at 18–21 — and collapses in the middle of the afternoon. ΔCH₄/ΔCO₂ peaks in the small hours, when traffic is at its minimum, and is lowest in the afternoon.

That is exactly what a two-source city looks like. **When the traffic term falls away, the source mix that remains is methane-rich**; when traffic dominates, the mix is CO-rich and methane-poor. The weekly cycle of Section 7.2 showed the same thing on a seven-day period; this shows it on a 24-hour one, with 24 independent estimates instead of two.

Two details are worth noting. The evening maximum of 38.0 ppb ppm⁻¹ is **well above the 23.5 nightly median of Section 6.3** — the evening traffic peak is the most CO-inefficient hour of Jakarta's day, and it is the hour a fleet-efficiency programme would target. And the afternoon minimum of both ratios reflects the deep mixed layer diluting local sources into regional air, which is the same effect Section 5.2 measures as a two-hour erosion time.

### 7.5 Finding 48 — the week Jakarta stopped driving

Everything in Sections 6 and 7 rests on emission *ratios*: the argument that Jakarta's CO₂ is largely not traffic, and that its methane is almost entirely not combustion, is made by comparing species against each other on nights when the boundary layer holds them together. It is a good argument, but it is one argument, and it would be better if something turned the traffic off and let us watch.

Something does. At **Idul Fitri** several million people leave Jakarta for their home provinces — *mudik*, the largest annual human migration in the country — and for about a week the city's vehicle activity collapses while its landfills, wastewater and power demand carry on. The holiday moves through the Gregorian calendar by about eleven days a year, so it is not confounded with season: 10 April 2024 and 31 March 2025 are the two occurrences inside Kemayoran's record.

Comparing the holiday window (two days before to five days after) with the surrounding weeks, each year normalised by its own control median so the two contribute equally:

**Table 31 — the Idul Fitri experiment at Kemayoran**

| Window | CO | CO₂ | CH₄ |
|---|---|---|---|
| **Rush hour, 06–09** | **−31.5 %** (*p* = 0.038) | −1.0 % (*p* = 0.31) | −0.1 % (*p* = 0.98) |
| All hours | **−25.3 %** (*p* = 0.038) | −0.8 % (*p* = 0.080) | +0.5 % (*p* = 0.77) |
| Night, 20–04 | −21.1 % (*p* = 0.32) | +0.6 % (*p* = 0.53) | −4.0 % (*p* = 0.19) |

**Carbon monoxide falls by a third at rush hour. Methane does not move at all.** The structure across the three windows is the check that the effect is traffic and not something else: it is largest in the morning rush, smaller when all hours are averaged, and statistically absent at night — precisely the diurnal profile of vehicle activity, and not the profile of a landfill, a power station or a change in the weather.

**This is Findings 8 and 9 again, obtained without a single ratio.** Section 6.3 bounded the fossil share of Jakarta's CO₂ enhancement at ≤ 63 % from ΔCO/ΔCO₂; Section 7.1 concluded that ≳97 % of the methane is non-combustion. Here the city's traffic is switched off by a public holiday, and the methane is unchanged to within a fraction of a per cent while the CO collapses. Two independent methods, one relying on nocturnal coupling and the other on a calendar, give the same answer.

> **What it does not settle.** Two events is a small experiment, and the CO₂ response — a drop of about 1 %, or roughly 4 ppm against a ~20 ppm enhancement — is in the right direction and the right order of magnitude for the ≤ 63 % fossil bound, but it does not reach significance and should not be quoted as a measurement. The honest statement is that **CO₂ moved much less than CO and much more than CH₄**, which is what a mixed source with a minority traffic term predicts. A third and fourth Idul Fitri would settle it; the station will supply them.

### 7.6 Finding 64 — the weekend traffic drop isolates commuter vehicle emissions from biogenic and fugitive sources

Section 7.5 exploited the annual Idul Fitri exodus. A continuous, weekly analogue is available across the entire 16,495-hour Kemayoran record by contrasting regular weekdays against weekends:

**Table 32 — weekday vs weekend diurnal rush-hour metrics at Kemayoran**

| Species | Unit | Weekday amp | Weekend amp | Amp ratio | 07:00 Weekday | 07:00 Weekend | 07:00 Change |
|---|---|---|---|---|---|---|---|
| **CO** | ppb | **720.5** | **555.5** | **1.30** | **1009.5** | **770.0** | **−23.7 %** |
| CO₂ | ppm | 29.3 | 30.3 | 0.97 | 456.1 | 453.1 | −0.7 % |
| CH₄ | ppb | 470.0 | 473.5 | 0.99 | 2403.5 | 2417.0 | +0.6 % |

On weekday mornings, morning commuter traffic produces a sharp 07:00 peak in CO of 1,009.5 ppb, which collapses to 770.0 ppb on weekends (**a 23.7 % decrease**; Figure 11a), yielding a full diurnal amplitude ratio of 1.30×. In contrast, the diurnal amplitudes of CO₂ (29.3 vs 30.3 ppm, ratio 0.97) and CH₄ (470.0 vs 473.5 ppb, ratio 0.99) are statistically indistinguishable between weekdays and weekends.

**This confirms that Jakarta's daily methane and carbon dioxide swings are driven by boundary-layer dynamics and continuous biogenic/fugitive sources**, rather than commuter vehicular exhaust.

![Figure 11](figures/f11_regional_diurnal_n2o.png)

**Figure 11 — Jakarta rush-hour fingerprint, equatorial H₂ seasonality, and global N₂O acceleration.** (a) Kemayoran hourly median CO for weekdays vs weekends, highlighting the 24 % drop during the 06:00–09:00 morning rush. (b) Climatological seasonal cycle of flask H₂ at Bukit Kototabang showing bimodal fire/transport peaks and dry-season soil sink minimum. (c) Decadal N₂O growth rate acceleration (2004–2013 vs 2014–2024) across five latitudes.

> **Its limits.** Weekend traffic in a megacity remains substantial; this test measures the difference between heavy weekday commuter traffic and weekend commercial activity, not the complete cessation of vehicles.

### 7.7 Finding 86 — the same weekend, in the units an inventory would be credited in

Finding 64 measures the weekend drop as a tracer statement, in CO. What a transport-sector measure under a carbon-pricing scheme would be credited against is not CO — it is CO₂-equivalent, and CO has no GWP. So the same contrast is recomputed across all three species, and summed where the accounting framework allows summing.

The excess is taken as each day's 06:00–09:00 rush median minus the *same day's* 12:00–16:00 afternoon median, so that seasonal drift cannot enter, and weekday days are then compared with weekend days.

**Table 33 — Kemayoran rush-hour excess over the same day's afternoon, weekday against weekend** (from `outputs/p_kmy_weekend_co2e.csv`):

| Group | Days | CO₂ (ppm) | CH₄ (ppb) | CO (ppb) |
|---|---|---|---|---|
| Weekday (Mon–Fri) | 487 | 21.32 | 268.0 | 551.5 |
| Weekend (Sat–Sun) | 198 | 19.62 | 266.8 | 364.2 |
| **Difference** | — | **1.70** | **1.2** | **187.3** |
| *p* (Mann–Whitney) | — | 0.0151 | — | 0.0 † |

† Stored to four decimals; the CO difference is significant far beyond that.

Converting the methane difference at GWP-100 = 27.9 and adding it to the CO₂ gives **1.71 ppm CO₂-equivalent**, of which methane contributes 0.7 %.

Three readings, in order of how much they are worth. **The CO₂ difference is significant and small.** At 1.70 ppm against a 21.32 ppm weekday rush-hour excess, the whole weekday-to-weekend change in Jakarta's morning traffic moves the city's rush-hour carbon dioxide by **8 %** — while moving its CO by 34 %. That is the ≤ 63 % fossil bound of Section 6.4 seen a third way: most of the CO₂ in Jakarta's morning air is not commuter traffic.

**The methane difference is 1.2 ppb on a 268 ppb excess** — 0.4 %, indistinguishable from nothing, and Finding 9 again.

**And the CO₂-equivalent total is almost all CO₂.** The species that responds most strongly to the intervention, CO, contributes nothing to the credited quantity; the species that dominates the credited quantity barely responds. A traffic measure in Jakarta would be worth far less in CO₂-equivalent than its air-quality benefit suggests, and this is the measurement that says so.

> **What it does not settle.** 487 weekdays and 198 weekend days at one site over two years. The CO₂ result is significant at *p* = 0.015, which is not a wide margin, and the day-to-day variability of the rush-hour excess is several times the difference being measured. Finding 48's Idul Fitri experiment reaches the same conclusion with a larger intervention and a smaller sample; the two should be read together.

---

## 8. Jambi is drained peat — Findings 11, 32, 67

Section 6.3 established that Jambi's nocturnal CO₂ is decoupled from combustion and coupled to methane, and left the surface unidentified. Two further measurements identify it, and they are independent of each other: one is a magnitude, the other a phase.

### 8.1 The nocturnal budget, and the magnitude

**Method.** In a stably stratified nocturnal layer of depth *h* that is not being ventilated, the surface flux and the observed rate of rise are related by *F* = (d*C*/d*t*) · *n*<sub>air</sub> · *h*. Nights are kept only when the rise is monotone (*r* > 0.7 over ≥ 6 hours spanning ≥ 5 hours); *n*<sub>air</sub> comes from the barometric law at each station's elevation. Depth *h* is **not measured** — no ceilometer or radiosonde accompanies the archive — so the flux is quoted across a 100–400 m bracket with 200 m as the central case.

![Figure 12](figures/f12_nocturnal_flux.png)

**Figure 12.** (a) Median nocturnal CO₂ accumulation rate on coherent nights, with interquartile range. (b) The flux it implies; the bar is the 100–400 m depth bracket, the marker the 200 m case.

**Table 34 — nocturnal CO₂ budget**

| Station | Coherent nights | Rate (ppm h⁻¹) | *F* at 200 m (µmol m⁻² s⁻¹) | Annualised (g C m⁻² yr⁻¹) |
|---|---|---|---|---|
| PLU **Bariri** | 1,006 | 2.58 [1.91, 3.45] | **5.05** | 1,915 |
| SRG Sorong | 337 | 1.74 [1.05, 2.54] | 4.02 | 1,524 |
| BKT Bukit Kototabang | 1,772 | 2.00 [1.31, 2.87] | 4.16 | 1,576 |
| KMY Kemayoran | 395 | 2.67 [1.88, 3.53] | 6.17 | 2,338 |
| JMB **Jambi** | 422 | 4.10 [2.98, 6.20] | **9.46** | 3,585 |

**Bariri validates the method.** Published nocturnal ecosystem respiration for tropical rainforest clusters around 4–8 µmol m⁻² s⁻¹; Bariri returns 5.05 from 1,006 independent nights using nothing but hourly CO₂ and an assumed layer depth.

**Jambi respires 1.9× the intact-forest reference.** Temperature does not explain it — Bariri is at 1,400 m and Jambi at 25 m, so the lapse rate pushes the comparison the other way. Annualised, Jambi's ~3,600 g C m⁻² yr⁻¹ is at or above the gross primary production of the most productive tropical forest, which local photosynthesis cannot balance. Carbon at that rate is not being cycled; it is being drawn out of a stored pool.

**Jakarta is not especially high, and that is consistent.** Kemayoran's 6.17 µmol m⁻² s⁻¹ is only 1.2× Bariri, which again says most nocturnal CO₂ under a megacity is biological — the same conclusion Sections 5.1, 6.3 and 6.4 reach by other routes.

### 8.2 The phase, which identifies the mechanism

Magnitude alone could be explained by a warmer or more fertile soil. Phase cannot (Figure 13b).

![Figure 13](figures/f13_external_checks.png)

**Figure 13.** (a) Each station's afternoon CO₂ background referenced to Bariri; the shaded band is how closely Bukit Kototabang agrees with its own NOAA flasks, so the whole ladder is anchored to the WMO scale. (b) The seasonal cycle of nocturnal CO₂ accumulation at Bariri and Jambi, each normalised by its own annual mean. (c) CO₂ seasonal amplitude by latitude against the flask-measured Mauna Loa and South Pole values (Section 10.4).

**Table 35 — seasonal cycle of the nocturnal CO₂ accumulation rate, normalised**

| Station | Max | Min | Max/min | Interpretation |
|---|---|---|---|---|
| PLU Bariri | **January** (1.15) | **August** (0.80) | 1.43 | wet-season peak |
| BKT Bukit Kototabang | September (1.13) | June (0.75) | 1.51 | weak, mixed |
| **JMB Jambi** | **October** (1.42) | **January** (0.68) | **2.09** | **dry-season peak** |

Bariri and Jambi are in **antiphase**. Bariri's respiration peaks in the wettest part of its year and troughs in the June–September dry period: a normal, moisture-limited soil where microbial activity follows water availability.

Jambi does the opposite. Its respiration is lowest in the wet season and rises by a factor of two to a maximum in September–October at the end of the dry period. **That is the signature of drainage.** In waterlogged peat, decomposition is slow because anoxia protects the stored carbon; when the water table falls, oxygen penetrates the peat column and aerobic decomposition of carbon that may be centuries old accelerates sharply. Wetting suppresses it; drying releases it. **A site whose respiration rises as it dries is a site whose carbon store is being consumed.**

### 8.3 The same water table drives the fires

Jambi's respiration maximum in September–October coincides exactly with Sumatra's main burning season (Section 9.3). That is not coincidence and not a contamination artefact — the nightly slopes are gated on CO₂–time coherence, and fire plumes are episodic rather than nocturnal-monotone. It is one physical cause seen twice: **the water-table drawdown that lets oxygen into the peat is what makes the peat both respire faster and burn at all.** The CO₂ efflux measured on quiet nights at Jambi and the CO plumes measured 500 km downwind at Bukit Kototabang are two consequences of one hydrological state.

This gives the region a continuous, quiet-night indicator of peat condition that does not require a fire to be burning — and, in principle, a leading indicator of fire risk.

> **Caveat.** The magnitude carries the layer-depth uncertainty and is best read as a *ratio* to Bariri, which is depth-robust only insofar as the two sites' nocturnal layers are comparable — a montane site and a lowland site need not be. The phase result is much stronger: a seasonal cycle in layer depth would have to be large and correctly timed to manufacture a factor-of-two antiphase between two sites. Jambi rests on two years; a third would settle it, and water-table records from the Jambi peat domes would confirm the mechanism directly.

### 8.4 Finding 32 — how long the peat has

Section 8.1 measured Jambi's respiration at 9.46 µmol m⁻² s⁻¹ against Bariri's 5.05. The difference is what the peat is losing beyond what an intact forest soil respires:

$$(3{,}585 - 1{,}915)\ \text{g C m}^{-2}\text{yr}^{-1} = 1{,}670\ \text{g C m}^{-2}\text{yr}^{-1} = \textbf{16.7 t C ha}^{-1}\textbf{yr}^{-1}$$

Tropical peat domes store of order 1,000–3,000 t C ha⁻¹ — far more than mineral soils, because waterlogging has protected the carbon from decomposition for millennia. At 16.7 t C ha⁻¹ yr⁻¹ the store empties on an **e-folding time of 60–180 years**.

**Table 36 — Jambi peat-carbon loss rate and implied depletion timescale**

| Store (t C ha⁻¹) | Fractional loss | e-folding time |
|---|---|---|
| 1,000 | 1.7 % yr⁻¹ | 60 yr |
| 2,000 | 0.8 % yr⁻¹ | 120 yr |
| 3,000 | 0.6 % yr⁻¹ | 180 yr |

The point of the arithmetic is the timescale, not the third digit. **A store that took thousands of years of waterlogged accumulation to build is being returned to the atmosphere on a human-lifetime clock**, and the mechanism is a water table, which is a thing that can be managed. Global soil organic carbon amounts to roughly 1,500 Pg C to 1 m depth with a mean residence time of about 50 years; peat is the part of that pool where residence time is normally measured in millennia instead, and drainage is what converts it back.

This is also the quantity that makes Section 8.2's phase result matter. A dry-season respiration maximum is a diagnosis; 16.7 t C ha⁻¹ yr⁻¹ with a 60–180 year clock is what the diagnosis costs.

> **Caveat.** The 16.7 t C ha⁻¹ yr⁻¹ inherits the layer-depth assumption twice over — once at each station — and the peat-store range is a published bracket rather than a measurement at this site. Both stations' fluxes could be wrong by a factor of two and the *ratio* would survive, but the absolute loss rate would not. Treat the e-folding time as an order of magnitude: decades to a couple of centuries, not five years and not five thousand.

### 8.5 Finding 67 — drained peatland respiration is dry-season amplified, contrasting with rainforest invariance

The seasonal respiration dynamics of Section 8.2 also express themselves in the full diurnal composite:

**Table 37 — Seasonal CO₂ respiration amplitudes at Jambi and Bariri**

| Station | Setting | Wet-season amp | Dry-season amp | Dry/wet ratio |
|---|---|---|---|---|
| **JMB Jambi** | Drained peatland / plantation | 41.7 ppm | **48.9 ppm** | **1.17** |
| PLU Bariri | Montane primary rainforest | 37.0 ppm | 36.6 ppm | 0.99 |

At Jambi, the diurnal CO₂ swing expands from 41.7 ppm in wet months (Nov–Apr) to 48.9 ppm during the dry season (Jun–Sep) — **a 17 % amplification in dry conditions**. At Bariri's intact rainforest, the diurnal amplitude is seasonally invariant (37.0 vs 36.6 ppm, ratio 0.99). In drained peat, the seasonal water-table decline aerates deeper peat horizons and accelerates aerobic respiration, whereas intact rainforest soil respiration is buffered by year-round root activity and canopy humidity.

> **Its limits.** Diurnal amplitude reflects both surface flux and boundary-layer trapping depth; however, since Bariri and Jambi experience similar seasonal insolation regimes, the contrasting dry-season response points directly to soil moisture aeration in drained peat.

### 8.6 Finding 76 — monsoonal modulation of nocturnal canopy accumulation at Bukit Kototabang

Evaluating Bukit Kototabang's nocturnal (00:00–05:00 local) canopy accumulation over its afternoon baseline (12:00–16:00 local) across the two monsoon regimes:

**Table 38 — monsoonal nocturnal accumulation at Bukit Kototabang** (from `outputs/t_bkt_nocturnal_monsoon.csv`)

| Monsoon regime | CO₂ night | CO₂ day | CO₂ swing (ppm) | CO night | CO day | CO swing (ppb) |
|---|---|---|---|---|---|---|
| Wet NW Monsoon (DJF, Westerly) | 427.72 ppm | 411.26 ppm | **16.46** | 166.4 ppb | 156.1 ppb | **10.3** |
| Dry SE Monsoon (JJA, Easterly) | 421.97 ppm | 405.09 ppm | **16.88** | 120.3 ppb | 118.8 ppb | **1.5** |

**Biogenic nocturnal respiration is steady year-round at 16.5–16.9 ppm, while combustion co-accumulation drops by a factor of 6.9 in the dry easterly monsoon.** In the wet season (DJF), westerly airflow off the Indian Ocean brings humid maritime air and local lowland combustion plumes (10.3 ppb CO co-accumulation). In the dry season (JJA), easterly flow across the mountain ridge carries clean montane biospheric air with virtually zero CO accumulation (1.5 ppb), proving that BKT's nocturnal CO₂ build-up is pure biogenic respiration decoupled from local traffic.

> **Its limits.** Nocturnal trapping depth varies between wet and dry conditions; however, the stability of the CO₂ diurnal swing across seasons confirms robust local biospheric respiration.

---

# Part III — Regional and transported signals

## 9. Twenty-four years of fire at Bukit Kototabang — Findings 12 to 15, 27, 28, 33, 34, 38, 40

### 9.1 The record

Bukit Kototabang's CO series runs from July 2001 to December 2024 — 161,866 hours, the longest in the network by an order of magnitude, and one of very few multi-decadal CO records in the equatorial tropics. Section 4.3 shows the pre-2019 in-situ values are biased high, which affects trends (Section 9.6) but not the *episode* analysis below, because episodes are measured as enhancements above a contemporaneous local baseline and a multiplicative bias largely cancels in a ratio.

![Figure 14](figures/f14_bkt_co_enso.png)

**Figure 14.** (a) Monthly median, 10th percentile and 10th–95th percentile envelope of hourly CO, log scale. (b) The Sep–Nov Oceanic Niño Index.

### 9.2 Finding 12 — October 2015

**Table 39 — October 2015 carbon-monoxide episode severity**

| Statistic | Oct 2015 | Record background (10th pct) |
|---|---|---|
| Monthly median CO | **1,493 ppb** | 88 ppb |
| 95th percentile | 3,685 ppb | — |
| Maximum hourly | **5,795 ppb** | — |
| Hours above 1,000 ppb | **542 of 723 (75 %)** | — |
| Sep–Nov mean | 965 ppb | — |

For three-quarters of an entire month, a **GAW global background station** recorded carbon monoxide above 1,000 ppb, with a monthly median **17× its own long-term baseline**. This is the atmospheric fingerprint of the 2015 El Niño Indonesian peat fires, and the magnitude at a background site 500+ km from the main burn scars conveys the scale better than almost any surface measurement could.

### 9.3 Two burning seasons, and the ENSO link

The seasonal CO climatology is **bimodal**: a primary maximum in September–October (+52 ppb in October) and a secondary maximum in February–March (+28 ppb in February), corresponding to the main South Sumatra / Jambi peat season and the earlier Riau land-clearing season.

**Table 40 — Fire-season metrics against the Oceanic Niño Index**

| Metric | Pearson *r* vs SON ONI | Spearman ρ |
|---|---|---|
| Annual 95th-percentile CO | **+0.57** | +0.49 |
| Annual maximum CO | +0.46 | +0.48 |
| Annual median CO | +0.39 | +0.31 |
| **Annual background CO (10th pct)** | **−0.13** | −0.16 |

The gradient across that table is the finding. **ENSO modulates the extremes, not the baseline.** El Niño does not raise ambient CO over Sumatra; it converts a normal year into one punctuated by extreme fire plumes.

### 9.4 Finding 13 — one ratio tells you whether a season burned peat

![Figure 15](figures/f15_2019_haze.png)

**Figure 15.** (a) CO and CH₄ at Bukit Kototabang, 15 Aug – 5 Nov 2019, against the pre-fire background. (b) The plume emission ratio.

![Figure 16](figures/f16_growth_fire.png)

**Figure 16.** (a) Annual CO₂ growth anomaly at the two long-record stations (Section 12.3). (b) Plume ΔCH₄/ΔCO for every burning window in which BKT ran both species. (c) e-folding relaxation time of each major CO event against its peak enhancement.

**Method.** Within each window, enhancements are taken over that window's own 10th percentile and restricted to hours more than 50 ppb above it, so the slope is a plume ratio rather than a regression through background scatter; 95 % intervals from 300 bootstrap resamples.

**Table 41 — plume ΔCH₄/ΔCO by burning season** (ppb ppb⁻¹)

| Season | CO p95 (ppb) | ΔCH₄/ΔCO | *r* | |
|---|---|---|---|---|
| **2019 Aug–Oct** | 631 | **0.081 [0.078, 0.085]** | 0.66 | peat fire |
| **2023 Aug–Oct** | 323 | **0.041 [0.019, 0.064]** | 0.09 | peat fire (weak coupling) |
| 2019 Feb–Mar | 305 | 0.183 [0.126, 0.241] | 0.23 | |
| 2011 Aug–Oct | 326 | 0.171 [0.141, 0.203] | 0.29 | |
| 2010 Feb–Mar | 282 | 0.245 [−0.04, 0.56] | 0.10 | |
| 2012 Aug–Oct | 338 | 0.309 [0.265, 0.357] | 0.46 | |
| 2012 Feb–Mar | 247 | 0.343 [0.234, 0.447] | 0.22 | |
| 2013 Feb–Mar | 267 | 0.411 [0.316, 0.536] | 0.41 | |
| 2020 Feb–Mar | 273 | 0.465 [0.394, 0.537] | 0.50 | |
| 2022 Feb–Mar | 197 | 0.489 [0.280, 0.721] | 0.40 | |
| 2013 Aug–Oct | 231 | 0.525 [0.382, 0.654] | 0.33 | |
| 2021 Feb–Mar | 258 | 0.762 [0.682, 0.852] | 0.62 | |
| 2022 Aug–Oct | 138 | 0.772 [0.590, 0.946] | 0.52 | |
| 2023 Feb–Mar | 220 | 0.779 [0.702, 0.872] | 0.60 | |
| 2024 Aug–Oct | 203 | 0.842 [0.592, 1.033] | 0.71 | |
| 2020 Aug–Oct | 172 | 1.102 [0.986, 1.218] | 0.69 | |
| 2021 Aug–Oct | 173 | 1.350 [1.230, 1.487] | 0.74 | |

**The distribution is bimodal with no overlap.** Two seasons sit at 0.04–0.08; the other fifteen at 0.17–1.35. The low ones are 2019 and 2023 — the two El Niño burning seasons in the CH₄-available era, identified independently through CO magnitude and the ONI correlation. The detailed 2019 episode analysis gives **0.090 [0.085, 0.095], *r* = 0.70, n = 1,877**, squarely in the published range of 0.06–0.10 for Indonesian peat combustion, from an observation-only measurement hundreds of kilometres downwind.

**The upper mode is also meaningful.** The non-fire seasons converge on 0.5–1.35, the same ratio as BKT's nightly ΔCH₄/ΔCO in Table 25 (1.12 [0.75, 1.58]). With no fire, the CH₄–CO covariance is just the regional biogenic surface mix; a peat plume drives the ratio down by more than an order of magnitude because peat combustion is CO-rich and comparatively CH₄-poor relative to that mix.

**Operationally:** ΔCH₄/ΔCO below about 0.15 in a Sumatran burning window means peat is burning upwind. It needs two species from one instrument, no inventory, no transport model, and no calibration — only the slope matters, so an offset in either channel cancels. That immunity is what makes the finding survive Section 4.3.

**Why CO₂ cannot be used here.** ΔCO₂ shows no correlation with ΔCO during the 2019 episode (*r* = −0.002). Peat plumes have ΔCO/ΔCO₂ of order 100 ppb ppm⁻¹, so a plume delivering ΔCO = 500 ppb carries only ΔCO₂ ≈ 5 ppm — well below the 13 ppm standard deviation of CO₂ at this site. **CO and CH₄ are usable fire tracers at this range; CO₂ is not.**

**A fourth tracer, from the flasks.** In the flask samples that caught elevated CO, hydrogen is enhanced with **ΔH₂/ΔCO = 0.143 [0.123, 0.170], *r* = 0.76, n = 185**. SF₆ carried through the same regression as a control returns a slope indistinguishable from zero (*r* = −0.18), as a species with no fire source must. H₂ is therefore a fourth independent fire tracer at this site — though at weekly resolution the flasks rarely catch a fresh plume, which is why the plume ratios above come from the hourly record and not from them.

> **Caveat.** 2023's ratio has *r* = 0.09 — the plume hours are barely coupled — so its point value is not trustworthy even though its interval sits clearly below the non-fire mode. Read 2023 as "low, therefore peat-influenced", not as "0.041".

### 9.5 Finding 14 — plumes clear before OH can act

**Table 42 — Carbon-monoxide plume clearance timescales**

| Event | Peak enhancement (ppb) | e-folding τ (days) | *r* |
|---|---|---|---|
| 2015 | 1,303 | **11.9** | −0.86 |
| 2002 | 284 | 12.5 | −0.75 |
| 2006 | 563 | 21.6 | −0.88 |
| 2023 | 153 | 36.1 | −0.84 |
| 2019 | 461 | 43.5 | −0.65 |

The chemical lifetime of CO against OH is 1–3 months. Every observed relaxation is at or below the fast end of that range, and the two largest events clear in **under two weeks** — four to seven times faster than oxidation could remove them.

**The decay of a haze episode measures when the fires stopped and how fast the air was flushed, not how fast the CO was oxidised.** Chemistry is a spectator on these timescales, so the CO record can be read as a near-direct proxy for regional emission without an OH correction. The *inverse* relation between event size and clearance time (Figure 16c) says the biggest events are terminated most sharply — which is what monsoon onset extinguishing a drought-driven fire season looks like.

**Spectrum.** Welch's method on the log of the daily CO series, after removing trend and three annual harmonics, partitions the variance as 14.3 % at 2–10 d, 11.1 % at 10–20 d, **25.1 % at 20–90 d**, 30.0 % at 90–400 d and 19.5 % beyond. A quarter of the variance sits in the intraseasonal band where an MJO signature would live, but there is **no discrete spectral peak**; the spectrum is red. That 20–90 day power is exactly what the 12–44 day relaxation times above produce as broadband red noise. It is the fire episodes, not a wave.

### 9.6 Finding 15 — the flask record gives the CO trend the in-situ record cannot

Section 4.3 disqualified the pre-2019 in-situ CO series for trend work. The flask record replaces it, on one scale from 2004 to 2025 (Figure 3c):

**Table 43 — flask CO percentile trends at Bukit Kototabang, 2004–2025** (20 years with ≥15 samples)

| Percentile | Mean (ppb) | Trend (ppb yr⁻¹) | 95 % CI |
|---|---|---|---|
| **10th (background)** | 85.2 | **−0.14** | [−0.51, +0.52] |
| 50th (median) | 120.0 | −0.31 | [−1.45, +0.57] |
| **90th (polluted tail)** | 213.1 | **−3.17** | [−7.49, −0.40] |

**The background is flat and the polluted tail is falling.** Only the 90th percentile clears zero. This is the same conclusion an earlier draft drew from the in-situ record — but that draft's evidence was unsound, because the in-situ CO carried a 10–41 ppb bias that changed through the very period being fitted. The flask record reaches the conclusion on a longer series and a single scale.

Combined with Section 9.3, the picture is coherent: the hemispheric background CO over equatorial Sumatra has not changed measurably in two decades, while the extreme fire-plume statistic has declined. The whole-record flask trend is −0.87 ppb yr⁻¹ [−1.53, −0.22], driven by the tail.

### 9.7 Findings 27 and 28 — a fourth fire tracer, and one that only appears after correction

The flask record carries three species the analyser does not, and they can be tested against CO in the same samples. The complication is that at Bukit Kototabang the burning season and the monsoon reversal fall in the same months, so a flask drawn in a plume also arrived in a particular air mass. Both effects push the same species in the same direction, and a raw regression cannot tell them apart.

SF₆ separates them. Because it is inert with no local source (Section 10.1), the SF₆ anomaly of a sample measures the air mass it arrived in; scaling that by each species' measured interhemispheric gradient per ppt of SF₆ gives the part of its value attributable to transport, which can then be removed before regressing on CO.

**Table 44 — plume ratio against CO, before and after removing the air mass**

| Species | Treatment | Slope | 95 % CI | *r* | n |
|---|---|---|---|---|---|
| **H₂** | raw | **+0.143 ppb ppb⁻¹** | [+0.123, +0.170] | **+0.76** | 185 |
| N₂O | raw | −0.0103 ppb ppb⁻¹ | [−0.016, −0.004] | −0.17 | 288 |
| **N₂O** | **air-mass corrected** | **−0.0010** | **[−0.0022, +0.0001]** | −0.09 | 288 |
| CO₂ | raw | −0.0093 ppm ppb⁻¹ | [−0.025, +0.007] | −0.06 | 209 |
| **CO₂** | **air-mass corrected** | **+0.0149 ppm ppb⁻¹** | **[+0.0096, +0.0208]** | **+0.35** | 209 |
| CH₄ | air-mass corrected | +0.72 ppb ppb⁻¹ | [+0.39, +1.10] | +0.20 | 289 |

Three results.

**Hydrogen is a fire tracer at this site.** ΔH₂/ΔCO = 0.143 with *r* = 0.76 needs no correction to show itself — H₂ is co-emitted with CO by incomplete combustion and has no competing seasonal source strong enough to hide it. (No reference-site H₂ was retrieved, so no air-mass correction could be computed for it; given the raw correlation it is unlikely to matter.)

**Nitrous oxide is not.** Its raw slope is negative and nominally significant, which would be nonsense as a fire signal — fires emit N₂O, they do not consume it. After correction the slope is **−0.0010 [−0.0022, +0.0001], indistinguishable from zero.** The apparent relationship was entirely the air mass: high-CO samples arrive in Southern-Hemisphere air, which is N₂O-poor. This is a useful negative result and a warning about the raw regression.

**Carbon dioxide's fire signal is real but only visible after correction.** The raw slope is indistinguishable from zero — Section 9.4 said as much, and gave the reason. But with the air mass removed the slope becomes **+0.0149 ppm ppb⁻¹, significantly positive**, which inverted is **ΔCO/ΔCO₂ = 67 ppb ppm⁻¹** — squarely in the 60–200 range for smouldering biomass and peat. So CO₂ *is* usable as a fire tracer at 500 km from the fires, but only if the air-mass covariance is removed first, and only in a record long enough to measure that covariance. That refines rather than contradicts Section 9.4: the CO₂ enhancement is buried in biospheric and air-mass variability, and an inert tracer is what digs it out.

**Finding 40 — and the hydrogen coupling is seasonal.** Splitting the H₂–CO correlation by calendar month shows it is not a fixed property of the site but a fire signal that switches on:

**Table 45 — Seasonality of the hydrogen–carbon-monoxide coupling**

| Months | H₂–CO correlation |
|---|---|
| September, October, November | **+0.83, +0.76, +0.82** |
| February, March | +0.72, +0.64 |
| May, June, July, August | +0.27 to +0.38 |
| December | +0.02 |

The high-correlation months are precisely the two burning windows of Section 9.3. In the wet middle of the year the two species decouple, because H₂ then reflects its soil sink and its photochemical source rather than combustion. **H₂ is not a general tracer of CO at this site; it is a tracer of fire**, which is a sharper statement and a more useful one.

> **Caveat.** The correction assumes the interhemispheric gradient measured between Mauna Loa and Samoa over 2015–2025 applies to the air arriving at BKT throughout 2004–2025. Section 10.1 shows the January air is *more* enriched than the mid-Pacific Northern Hemisphere, so the correction is approximate in the monsoon months. The CH₄ result (*r* = 0.20) is too weak to quote as a ratio; it is included only to show that its sign flips the right way.

### 9.8 Findings 33 and 34 — severity, and the date the rains arrive

![Figure 17](figures/f17_severity_onset.png)

**Figure 17.** (a) Each fire year's peak daily CO against the number of days above 1,000 ppb, coloured by the SON Oceanic Niño Index. (b) The day of year on which CO collapses, against ONI. (c) Kemayoran's two emission ratios by hour, each normalised to its own daily mean (Section 7.4).

**Severity is not one number.** Ranking the 24 fire years three different ways gives three different answers:

**Table 46 — Fire-year severity under alternative metrics**

| Year | Peak daily CO | Days > 1,000 ppb | Annual CO burden | SON ONI |
|---|---|---|---|---|
| **2015** | 3,442 ppb | **28** | **123** | +2.4 |
| **2014** | **4,063 ppb** | 13 | 96 | +0.5 |
| 2005 | 1,622 ppb | 6 | 59 | −0.2 |
| 2019 | 1,660 ppb | 1 | 61 | +0.3 |

**2015 is the worst year by duration and by burden; 2014 by peak** — and 2014 was a *weak* El Niño. A single-day maximum and a season's exposure are different quantities, and a haze record summarised by either one alone will mislead. For health exposure the duration is what matters; for a plume-chemistry study the peak is.

Fitting a Gumbel distribution to the 20 annual maxima that clear the 250-day completeness gate (location 426 ppb, scale 828 ppb) puts return periods on the levels:

**Table 47 — Gumbel return periods for daily-median CO at Bukit Kototabang** (from `outputs/u_return.csv`):

| Daily-median CO | Return period |
|---|---|
| 500 ppb | 1.67 yr |
| 1,000 ppb | **2.54 yr** |
| 2,000 ppb | **7.21 yr** |
| 4062.55 ppb (the 2014 peak) | **81.31 yr** |

*An earlier draft of this table gave 1.4, 2.8, 8.8 and ~120 years against the same fitted parameters, and said 24 annual maxima where the fit uses 20. Both are corrected here and recorded in Section 15.7.*

A day above 1,000 ppb at a **global background station** is close to a once-in-two-and-a-half-years event. That is a statement about how routine extreme regional haze has become, not about how unusual it is.

**Finding 34 — the record dates the end of the burning season.** The monsoon extinguishes the fires, so the collapse of CO from its dry-season level marks the onset of the rains — a phenological date that needs no rain gauge. Defining it as the first day after 1 September on which the 10-day running median falls below that year's own median:

- Mean onset **day 281 (6 October)**, standard deviation **33 days**.
- Correlation with the SON ONI: ***r* = +0.49** over 20 years.
- Slope: **El Niño delays the onset by 15 days per °C** of ONI.

So the 2015 and 2023 El Niños did not merely make the fires more intense; they extended the season by roughly a month. Both mechanisms — more burning and longer burning — act in the same direction, which is why the duration statistic in the table above scales with ENSO more steeply than the peak does.

> **Caveat.** Absolute CO values before 2019 carry the 10–41 ppb bias of Section 4.3. At the 1,000–4,000 ppb levels used here that is under 4 % and cannot change the ranking or the return periods materially, but the threshold counts would shift slightly if the series were reprocessed. The onset definition is one of several reasonable ones; a threshold on absolute CO rather than the annual median gives dates within about a week.

### 9.9 Finding 38 — how long a CO anomaly remembers itself

Autocorrelation of the daily log-CO anomaly, after removing the annual cycle:

**Table 48 — Persistence of daily carbon-monoxide anomalies**

| Station | lag 1 d | lag 7 d | e-folding lag |
|---|---|---|---|
| BKT Bukit Kototabang | 0.86 | 0.52 | **19 days** |
| PLU Bariri | 0.83 | 0.47 | **11 days** |

Both are far longer than a synoptic weather system and comfortably inside the 20–90 day band that carries a quarter of the variance (Section 9.5). The three numbers — a 12–44 day plume clearance, a 19-day decorrelation, and a red spectrum with 25 % of its variance at 20–90 days — are three views of one thing: **regional CO is set by episodes that last two to six weeks**, not by daily weather and not by an oscillation.

Bukit Kototabang's longer memory than Bariri's is the fire signal: Sumatra's episodes are larger and last longer than anything Sulawesi sees.

### 9.10 Finding 75 — pristine clean-air baseline CO floor stability at Bukit Kototabang (75.9 ppb)

Tracking the unpolluted marine baseline floor in the 22-year NOAA flask record at Bukit Kototabang using the annual 10th percentile:

**Table 49 — clean background CO floor stability at Bukit Kototabang** (from `outputs/t_bkt_clean_co_floor.csv`)

| Metric | Mean (ppb) | Standard deviation (ppb) | 2004 level (ppb) | 2024 level (ppb) | Trend (ppb yr⁻¹) | *p*-value |
|---|---|---|---|---|---|---|
| BKT Clean CO 10th pct | **86.3** | **9.2** | 76.7 | 75.4 | **−0.03** | 0.925 (not significant) |

**The pristine unpolluted background CO floor over equatorial Sumatra has remained flat at 86.3 ± 9.2 ppb for over two decades.** While extreme fire plumes periodically surge past 1,500–4,000 ppb during dry El Niño seasons (Section 9.1, 9.8), the cleanest background air masses reaching Bukit Kototabang show no detectable secular trend (*p* = 0.925). **That is a limit, not a measurement of zero.** Finding 52 shows this site needs 15.5 years to detect CO's own −1.7 ppb yr⁻¹ trend; against a floor whose scatter is ±9.2 ppb, a trend of a few tenths of a ppb per year would be invisible in 21 years. The honest statement is that the floor has not moved by an amount this record could see.

> **Its limits.** The 10th percentile is evaluated on weekly flask samples; unpolluted background hours represent clean Indian Ocean air masses arriving during non-burning regimes.

---

## 10. Seasonal cycles as a transport tracer — Findings 16 to 19, 26, 39, 59 to 61, 68 to 70

The seasonal cycle at these stations has always been interpretable two ways: as air-mass alternation between hemispheres, or as the annual cycle of regional wetland and fire emissions. Earlier drafts could only argue for the first and caveat the second. The flask record contains a species that settles it.

### 10.1 Finding 17 — SF₆ has the largest seasonal cycle in the network

Sulfur hexafluoride is chemically inert, has an atmospheric lifetime of millennia, and has no natural source. It cannot have a local biological cycle, a chemical sink, or a fire source. **Whatever seasonal variability it shows at a station is air-mass alternation and nothing else.**

**Table 50 — SF₆ seasonal amplitude by site, 2015–2025** (Figure 3b)

| Site | Latitude | Amplitude (ppt) | Month max | Month min |
|---|---|---|---|---|
| **BKT Bukit Kototabang** | −0.2 | **0.38** | Jan | Sep |
| MLO Mauna Loa | +19.5 | 0.09 | Nov | Aug |
| SMO Samoa | −14.2 | 0.07 | Feb | Jun |
| KUM Cape Kumukahi | +19.5 | 0.06 | May | Aug |
| BRW Barrow | +71.3 | 0.05 | Dec | Sep |
| SPO South Pole | −90.0 | 0.04 | Sep | Feb |

Bukit Kototabang's SF₆ cycle is **four times larger than any other site in this set**, including Barrow inside the industrial Northern Hemisphere. For comparison, the full pole-to-pole SF₆ difference measured across the same network is 0.46 ppt, and the tropical Mauna Loa–Samoa difference is 0.25 ppt.

Expressing BKT as a mixture of those two tropical end members gives a Northern-Hemisphere air-mass fraction running from **0.18 in September to 1.45–1.51 in January–February**. Values above 1 are not an error: they say the air arriving in the Asian winter monsoon is **more SF₆-rich than the mid-Pacific Northern Hemisphere**, i.e. Bukit Kototabang in January is sampling fresh continental Asian outflow rather than clean zonal-mean northern background. That is a substantive result about what the site sees, and it is only visible in a tracer with no other source.

### 10.2 Finding 16 — methane's seasonal cycle is transport, proven

If the seasonal cycle is transport, every species carried by the same air must show a seasonal cycle proportional to SF₆'s, with a constant of proportionality equal to that species' interhemispheric gradient per ppt of SF₆ — a quantity that can be **measured** from the reference sites rather than assumed.

Regressing each species' seasonal component at BKT on SF₆'s (Figure 2c):

**Table 51 — seasonal slope against SF₆, versus the measured network gradient**

| Species | BKT slope per ppt SF₆ | *r* | Network Mauna Loa–Samoa gradient | Ratio |
|---|---|---|---|---|
| **CH₄** | **200.0 ± 2.8 ppb** | **0.99** | 207.3 ppb | **0.97** |
| CO₂ | 8.50 ± 1.04 ppm | 0.72 | 8.63 ppm | 0.99 |
| N₂O | 2.93 ± 0.11 ppb | 0.96 | 2.53 ppb | 1.16 |
| **CO** | **123.3 ± 10.9 ppb** | **0.83** | **91.3 ppb** | **1.35** |

**Methane's seasonal cycle at Bukit Kototabang is transport, with no detectable local seasonality.** The slope matches the independently measured interhemispheric ratio to 3 %, and the correlation between the seasonal cycles of methane and an inert industrial tracer is *r* = 0.99. Regional wetland emissions certainly have an annual cycle; what this shows is that at this site it is small enough to hide inside a 3 % residual.

CO₂ gives the same answer (ratio 0.99) and N₂O nearly so (1.16). Earlier drafts had to caveat the transport interpretation as an upper bound; that caveat can now be withdrawn.

### 10.3 Finding 18 — CO is the exception

CO's slope runs **35 % above** the network gradient, with a well-determined interval. Unlike the other three, CO has a genuine local seasonal source riding on top of the transport cycle — and Section 9.3 says exactly what it is, because the Sumatran burning seasons fall in the same part of the year as the monsoon reversal.

That CO is the *only* species to show this excess is itself a check on the method: a regression artefact would inflate all four, and a transport-only atmosphere would inflate none.

### 10.4 Finding 19 — where the equatorial CO₂ amplitude really sits

With the reference amplitudes measured rather than quoted (Table 13), the equatorial CO₂ seasonal cycle can be placed properly (Figure 13c):

**Table 52 — Measured global comparison of CO₂ seasonal amplitudes**

| Site | Latitude | CO₂ seasonal amplitude (ppm) |
|---|---|---|
| BRW Barrow | +71.3 | 17.66 |
| KUM Cape Kumukahi | +19.5 | 8.53 |
| MLO Mauna Loa | +19.5 | 6.86 |
| **BKT Bukit Kototabang (flask)** | **−0.2** | **5.53** |
| SMO Samoa | −14.2 | 1.30 |
| SPO South Pole | −90.0 | 1.28 |

Bukit Kototabang's amplitude is **81 % of Mauna Loa's and 4.3× the South Pole's**. The in-situ stations, measured on the afternoon background, give 2.1–5.5 ppm across the network, straddling the same range.

Equatorial Indonesia therefore sits firmly on the **Northern-Hemisphere side** of the amplitude gradient despite every station lying south of the equator — the same conclusion Sections 10.1 and 10.2 reach from SF₆ and methane, and what makes the phase agreement meaningful: four of five in-situ sites show a CO₂ maximum in January–March and a minimum in June–September, the Northern-Hemisphere phase.

*An earlier draft reported this the opposite way round, claiming the equatorial amplitude was "close to the South Pole's". That was an artefact of a quoted Mauna Loa amplitude of ~15 ppm, which the flask record shows to be 6.9 ppm. See Section 15.*

### 10.5 The eastward transect

![Figure 18](figures/f18_seasonal.png)

**Figure 18.** Detrended seasonal cycle of the regional background (afternoon 20th percentile, harmonic-fit trend removed).

Among the in-situ stations, the CH₄ seasonal cycle orders eastward in **both** amplitude and phase:

**Table 53 — Eastward methane seasonal-amplitude and phase transect**

| Station | Longitude | Amplitude (ppb) | First-harmonic max |
|---|---|---|---|
| BKT Bukit Kototabang | 100.3 °E | **62.7 [60.6, 85.3]** | **25 Jan** |
| JMB Jambi | 103.6 °E | 86.3 [48.8, 116.4] | 13 Feb |
| PLU Bariri | 120.0 °E | **46.0 [39.7, 66.1]** | **8 Feb** |
| SRG Sorong | 131.3 °E | **27.4 [23.2, 39.6]** | **2 Mar** |
| *KMY Kemayoran* | *106.9 °E* | *64.8 [0.0, 126.0]* | *15 May* |

Setting Jambi aside — its amplitude includes local peat seasonality and its record is two years — the three clean sites give the same eastward ordering twice: amplitude declines 63 → 46 → 27 ppb, and the maximum arrives 36 days later at Sorong than at Bukit Kototabang. Kemayoran's June maximum marks it as locally driven, exactly as Section 7 would predict.

The 36-day lag is far too slow for advection (31° of longitude in 36 days is about 1 km h⁻¹), so it is not an air mass propagating past the stations. It is the **seasonal migration of the monsoon boundary itself**: the eastern sites are reached later because that is when the circulation reaches them.

> **Caveat.** Only the end members of the amplitude transect are separated: Bukit Kototabang's and Sorong's intervals do not overlap, while Bariri's overlaps both. Sorong's first-harmonic amplitude is only 9.3 ppb, so its phase is the least well constrained of the three. Bariri and Sorong rest on 4.7 and 2.5 clean years.

### 10.6 Finding 26 — half of the CO seasonal cycle is emitted nearby

Section 10.3 found CO's SF₆ slope running 35 % above the network gradient. The same machinery converts that excess into ppb (Figure 24c). The transport component of BKT's CO seasonal cycle is the SF₆ seasonal cycle scaled by the measured CO-per-SF₆ interhemispheric gradient of **91.3 ppb ppt⁻¹**; whatever remains is emitted near the station.

**Table 54 — Transport and regional-source shares of the CO seasonal cycle**

| | Peak-to-peak amplitude | Share |
|---|---|---|
| Observed CO seasonal cycle | 56.4 ppb | 100 % |
| Transport component (from SF₆) | 28.3 ppb | 50 % |
| **Local residual** | **30.6 ppb** | **54 %** |

*(The two components exceed 100 % because their maxima fall in different months and so do not add in phase.)*

The residual is not noise, and its shape is the check: it peaks in **February (+16.6 ppb) and September (+13.2 ppb)** and troughs in June (−14.0 ppb). Those are precisely the two Sumatran burning windows identified independently in Section 9.3 from the CO climatology — the Riau land-clearing season and the main South Sumatra / Jambi peat season — with the minimum in the wet middle of the year when nothing burns.

So Bukit Kototabang's CO seasonal cycle is **about half imported Northern-Hemisphere air and about half regional fire**, and the two can be separated with an inert tracer without any inventory or transport model. No other species at this site requires the split: CH₄, CO₂ and N₂O are transport alone (Section 10.2).

### 10.7 Finding 39 — nitrous oxide has a regional source

N₂O is measured only in the flasks, and this is the first quantitative statement about it at this site. Running the SF₆ attribution of Section 10.2 on it:

**Table 55 — Nitrous-oxide seasonal attribution at Bukit Kototabang**

| | Value |
|---|---|
| BKT seasonal slope against SF₆ | 2.93 ± 0.11 ppb ppt⁻¹ |
| Network Mauna Loa–Samoa gradient | 2.53 ppb ppt⁻¹ |
| **Ratio** | **1.16** |
| Observed seasonal amplitude | 1.01 ppb |
| Transport-predicted amplitude | 0.78 ppb |
| **Local residual** | **0.38 ppb, peaking in March** |

The 16 % excess is smaller than CO's 35 % (Section 10.3) but larger than CH₄'s 3 % or CO₂'s 1 %, and the residual has a coherent March maximum rather than looking like noise. **N₂O at Bukit Kototabang is mostly transported, with a modest regional source on top.**

Where the station sits in the global field is consistent with that:

**Table 56 — Bukit Kototabang nitrous-oxide enhancement over reference sites**

| Compared with | BKT minus that site |
|---|---|
| South Pole | **+1.96 ppb** |
| Samoa | **+1.04 ppb** |
| Barrow | +0.45 ppb |
| Mauna Loa | +0.33 ppb |

Bukit Kototabang sits at the Northern-Hemisphere end of the N₂O distribution despite being south of the equator — the same conclusion the SF₆ and methane results reach, now from a fourth species with an entirely different source type. The likely regional contributors are fertilised agricultural soils and biomass burning, both of which peak in the first half of the year in Sumatra.

> **Caveat.** N₂O's total seasonal amplitude is 1.01 ppb against a measurement repeatability of a few tenths of a ppb, so the 0.38 ppb residual is a small number extracted from a small number. The ratio of 1.16 is the more robust statement; the March timing rests on a 22-year climatology and should be treated as indicative.

### 10.8 Finding 59 — SF₆ is an absolute interhemispheric transport clock: 6.7 months lag behind the Arctic and 9.0 months lead over the South Pole

Because SF₆ has exclusively Northern-Hemisphere industrial sources and no chemical tropospheric sinks, its atmospheric burden rises monotonically. That linear accrual (0.323 ppt yr⁻¹ at Bukit Kototabang) converts spatial concentration differences into physical transport transit times across the globe:

**Table 57 — SF₆ interhemispheric gradient, transport lag from Arctic, and lead over South Pole**

| Site | Location | Lat | Elev (m) | Mean (ppt) | Diff from BRW | Lag from Arctic | Lead over Pole | Growth (ppt yr⁻¹) |
|---|---|---|---|---|---|---|---|---|
| BRW | Barrow, Alaska | +71.3° | 11 | **8.865** | 0.000 | 0.0 mo | 15.9 mo | 0.326 [0.322, 0.330] |
| KUM | Cape Kumukahi, Hawaii | +19.5° | 3 | 8.843 | −0.023 | 0.8 mo | 14.7 mo | 0.328 [0.324, 0.332] |
| MLO | Mauna Loa, Hawaii | +19.5° | 3,397 | 8.792 | −0.073 | 2.7 mo | 12.9 mo | 0.326 [0.323, 0.330] |
| **BKT** | **Bukit Kototabang** | **−0.2°** | **845** | **8.685** | **−0.181** | **6.7 mo** | **9.0 mo** | **0.323 [0.319, 0.328]** |
| SMO | Tutuila, Samoa | −14.3° | 42 | 8.547 | −0.319 | 11.9 mo | 3.9 mo | 0.321 [0.318, 0.325] |
| SPO | South Pole | −90.0° | 2,810 | **8.442** | −0.424 | 15.9 mo | 0.0 mo | 0.321 [0.317, 0.324] |

**Equatorial air at Bukit Kototabang lags Arctic air by 6.7 months and leads South Pole air by 9.0 months** (Figure 5b). The total interhemispheric transit time from Barrow to the South Pole is **15.9 months** (0.424 ppt mean difference). This establishes an empirical transport clock for tracing cross-equatorial advection across the Indonesian archipelago.

> **Its limits.** The transport lag assumes a quasi-steady-state linear growth rate; variations in interhemispheric exchange across ENSO phases introduce seasonal variations of ±1–2 months around the mean.

### 10.9 Finding 60 — vertical gradients at 19.5°N separate boundary-layer from free-tropospheric composition

Paired discrete flask sampling between Mauna Loa (3,397 m) and Cape Kumukahi (3 m) on Hawaii island over 22 years (2004–2025, *n* = 241 simultaneous months) resolves the vertical structure of tropical Pacific air:

**Table 58 — vertical gradients between Mauna Loa (3,397 m) and Cape Kumukahi (3 m) at 19.5°N** (from `outputs/t_vertical_gradients.csv`)

| Species | Unit | MLO (3,397 m) | KUM (3 m) | MLO − KUM | *p*-value | BKT − KUM | BKT − MLO |
|---|---|---|---|---|---|---|---|
| CO₂ | ppm | 401.79 | 402.19 | **-0.405 ± 1.115** | 4.4e-08 | -5.67 | -5.27 |
| CH₄ | ppb | 1857.01 | 1873.54 | **-16.532 ± 8.388** | 8.4e-85 | -2.25 | +14.29 |
| CO | ppb | 87.68 | 96.79 | **-9.112 ± 7.476** | 2.7e-47 | +26.99 | +36.10 |
| N₂O | ppb | 328.71 | 328.65 | **+0.064 ± 0.127** † | 1.5e-13 | +0.38 | +0.31 |
| SF₆ | ppt | 8.792 | 8.843 | **-0.050 ± 0.031** | 1.8e-70 | -0.16 | -0.11 |

Methane is depleted aloft by **−16.5 ppb** (*p* < 10⁻⁸⁴) and CO by **−9.1 ppb** (*p* < 10⁻⁴⁶) over 3.4 km vertical elevation, reflecting marine boundary-layer trapping and surface Northern-Hemisphere sources (Figure 5c).

† *N₂O's +0.064 ppb vertical difference is statistically significant only because n = 241 shrinks the standard error to 0.008 ppb. It is smaller than the single-flask reproducibility of 0.22 ppb (Finding 58; 0.12 ppb on the robust estimator) and about 0.02 % of ambient — it should be read as "no resolvable vertical gradient in N₂O", which is what a gas with a 120-year lifetime should show.*

**Crucially, equatorial Bukit Kototabang (865 m) sits well below both sites in CO₂ (−5.3 ppm vs MLO, −5.7 ppm vs KUM).** The Maritime Continent CO₂ deficit is not an elevation effect; it represents regional equatorial boundary-layer and column drawdown.

> **Its limits.** MLO and KUM reflect the Central Pacific trade-wind inversion regime; vertical gradients in the convective Maritime Continent boundary layer are governed by deep convective mixing rather than subsidence inversions.

### 10.10 Finding 61 — equatorial hydrogen has a bimodal seasonal cycle driven by fire emissions and monsoonal soil uptake

The 15-year flask record of molecular hydrogen (H₂) at Bukit Kototabang (2009–2024, *n* = 152 months) reveals a distinct bimodal seasonal cycle ($R^2 = 0.67$, harmonic amplitude **11.8 ppb**):

**Table 59 — Monthly hydrogen climatology at Bukit Kototabang**

| Month | Mean H₂ (ppb) | Standard deviation | Anomaly vs mean | Climatological regime |
|---|---|---|---|---|
| Jan | 556.20 | 5.67 | −3.94 | Wet season background |
| Feb | 561.02 | 6.31 | +0.88 | Early Riau burning season |
| **Mar** | **566.38** | **7.03** | **+6.25** | **Primary peak: northern burning & transport** |
| Apr | 565.67 | 8.58 | +5.53 | Post-peak burning transition |
| May | 558.45 | 7.12 | −1.68 | Onset of dry season |
| **Jun** | **553.88** | **7.30** | **−6.26** | **Annual minimum: peak dry-season soil sink** |
| Jul | 555.41 | 9.21 | −4.73 | Dry season soil uptake |
| Aug | 558.03 | 8.69 | −2.11 | Pre-fire season |
| Sep | 560.60 | 10.83 | +0.46 | Main burning onset |
| **Oct** | **565.09** | **12.65** | **+4.95** | **Secondary peak: southern peat fires** |
| Nov | 563.63 | 11.41 | +3.49 | Late fire season & monsoon shift |
| Dec | 558.11 | 9.53 | −2.03 | Wet season recovery |

The dual peaks in March (+6.25 ppb) and October (+4.95 ppb) coincide exactly with Sumatra's two burning windows (Section 9.3) and monsoonal transport reversals (Figure 11b). In June, enhanced microbial soil uptake in dry conditions drives a deep minimum (553.9 ppb, −6.26 ppb anomaly).

> **Its limits.** The October fire peak exhibits the largest interannual variance (s.d. 12.7 ppb), reflecting episodic El Niño burning severity, whereas the June soil-sink minimum is regular across all 15 years.

### 10.11 Finding 68 — latitude–time Hovmöller dynamics: CO₂ seasonal wave attenuation and phase propagation from Arctic to Antarctic

![Figure 19](figures/f19_hovmoeller_lat_lon.png)

**Figure 19.** (a) Global latitude–time Hovmöller diagram of atmospheric CO₂ from Arctic Barrow (71.3°N) to the South Pole (90.0°S), 2004–2025. (b) Global CH₄ latitude–time Hovmöller diagram showing the ~140 ppb interhemispheric gradient and the post-2014 tropical surge. (c) Maritime Continent longitude–month Hovmöller diagram across the 5 Indonesian stations (100.3°E to 131.3°E), showing the eastward propagation of the CH₄ seasonal monsoon wave.

Tracking the latitudinal propagation of the annual CO₂ seasonal cycle across 6 NOAA reference stations (Figure 19a):

**Table 60 — latitudinal attenuation and phase propagation of the CO₂ seasonal wave** (from `outputs/t_hovmoeller_lat_co2.csv`)

| Site | Latitude | Seasonal amplitude (ppm) | Minimum month | Maximum month | Trend (ppm yr⁻¹) |
|---|---|---|---|---|---|
| **BRW Barrow** | 71.32 °N | **16.39** | August (Month 8) | May (Month 5) | +1.822 |
| **KUM Cape Kumukahi** | 19.52 °N | **8.11** | September (Month 9) | May (Month 5) | +1.902 |
| **MLO Mauna Loa** | 19.54 °N | **6.64** | September (Month 9) | May (Month 5) | +1.877 |
| **BKT Bukit Kototabang** | 0.20 °S | **3.94** | September (Month 9) | February (Month 2) | +2.345 |
| **SMO Samoa** | 14.25 °S | **0.89** | September (Month 9) | February (Month 2) | +1.819 |
| **SPO South Pole** | 89.98 °S | **1.12** | March (Month 3) | September (Month 9) | +1.846 |

**The Northern Hemisphere terrestrial greening wave collapses from 16.39 ppm in the Arctic to 3.94 ppm at Bukit Kototabang and 1.12 ppm at the South Pole.** The summer drawdown minimum occurs in August at Barrow (Month 8.0) and is delayed to September (Month 9.0) at tropical sites (KUM, MLO, BKT, SMO). Across the equator, the seasonal cycle reverses phase, with the Southern-Hemisphere minimum occurring in March at the South Pole. The latitudinal Hovmöller diagram reveals tilted iso-concentration contours propagating southward across the Intertropical Convergence Zone on a characteristic timescale of ~1.2 months per 30° of latitude.

> **Its limits.** Seasonal amplitudes are extracted using a 3-harmonic Fourier expansion with a 2nd-order polynomial trend; interannual variability in boreal wildfire or tropical drought introduces ±0.3 ppm variations around the climatological amplitude.

### 10.12 Finding 69 — SF₆ latitude–time Hovmöller and 2-box model interhemispheric exchange timescale (1.23 years)

![Figure 20](figures/f20_hovmoeller_transport_forcing.png)

**Figure 20.** (a) SF₆ interhemispheric mixing clock: smooth northern-to-southern gradient (Barrow to South Pole). Over the months common to all three sites the gradient is 0.424 ppt and the implied exchange time 1.32 years (15.9 months); over Barrow and the South Pole alone it is 0.399 ppt and 1.23 years (Table 61). The 1.2-month spread is the precision of the method. (b) Vertical damping of seasonal cycles across the trade-wind inversion at 19.5°N (Kumukahi 3 m vs Mauna Loa 3,397 m). (c) Multi-species radiative forcing budget of the Maritime Continent (Bukit Kototabang) over pristine marine air (Samoa), where methane enhancement (+42.0 mW m⁻²) exceeds the CO₂ deficit cooling (−40.5 mW m⁻²).

Evaluating a two-box interhemispheric mass-balance model for inert SF₆ (Figure 20a):

$$\frac{d(C_N - C_S)}{dt} = \frac{E_N - E_S}{M} - \frac{2}{\tau_{\text{ex}}}(C_N - C_S)$$

With near-exclusive Northern Hemisphere industrial emissions ($E_N \approx E_{\text{tot}}$) and negligible tropospheric sinks, the quasi-steady state interhemispheric difference $\Delta C_{\text{NS}} = C_{\text{BRW}} - C_{\text{SPO}}$ directly determines the interhemispheric mixing timescale:

$$\tau_{\text{ex}} = \frac{C_N - C_S}{\dot{C}}$$

**Table 61 — SF₆ interhemispheric exchange timescale** (from `outputs/t_sf6_exchange_time.csv`)

| Parameter | Value | Unit |
|---|---|---|
| Mean interhemispheric difference (BRW − SPO) | **0.399 ± 0.069** | ppt |
| Global SF₆ secular growth rate | **0.325** | ppt yr⁻¹ |
| **Interhemispheric exchange timescale (τ<sub>ex</sub>)** | **1.23** | **years** |
| **Exchange timescale in months** | **14.7** | **months** |

**The 0.399 ppt interhemispheric SF₆ gradient clocks an interhemispheric mixing timescale of 1.23 years (14.7 months).**

> **This is not independent of Finding 59, and an earlier draft said it was.** Both numbers are the same quantity computed the same way — an interhemispheric difference divided by the secular growth rate. Finding 59 gives 15.9 months and this section 14.7 only because they average over different sets of months (Finding 59 uses the record common to Barrow, Bukit Kototabang and the South Pole; this uses Barrow and the South Pole alone). They are one measurement quoted twice, and the 1.2-month spread between them is a fair indication of its precision. The agreement with published two-box mixing times of 1.2–1.4 years is a genuine external check; the agreement with Finding 59 is not.

> **Its limits.** The two-box formulation assumes well-mixed hemispheric boxes; spatial concentration gradients within the Northern Hemisphere introduce ~10 % uncertainty in the effective exchange time.

### 10.13 Finding 70 — not supported: the equatorial CH₄ seasonal wave cannot be resolved as a propagating crest

Tracking the zonal propagation of the afternoon background ($q_{20}$) methane wave across 31° of longitude across Indonesia (Figure 19c):

**Table 62 — longitudinal propagation of the equatorial CH₄ seasonal wave** (from `outputs/t_hovmoeller_lon_ch4.csv`)

| Station | Longitude | Latitude | Peak month | Minimum month | Seasonal amplitude (ppb) |
|---|---|---|---|---|---|
| **BKT Bukit Kototabang** | 100.32 °E | −0.20 °S | **December (Month 12)** | May (Month 5) | **77.7** |
| **JMB Jambi** | 103.65 °E | −1.61 °S | **January (Month 1)** | August (Month 8) | **80.0** |
| **KMY Kemayoran** | 106.85 °E | −6.16 °S | **July (Month 7)** | November (Month 11) | **59.8** |
| **PLU Bariri** | 120.03 °E | −1.20 °S | **January (Month 1)** | October (Month 10) | **44.0** |
| **SRG Sorong** | 131.29 °E | −0.86 °S | **February (Month 2)** | November (Month 11) | **32.0** |

**This record cannot resolve a propagating wave, and an earlier draft claimed one.** The peak months above appear to march eastward — Sumatra in December, Sulawesi in January, West Papua in February — but three separate checks say the pattern is not real:

- **The ordering is not monotonic.** Kemayoran (106.9 °E) peaks in July, between Jambi (103.6 °E, January) and Bariri (120.0 °E, January). An earlier draft excluded it as "urban stagnation" *after* seeing that it broke the sequence.
- **The peak month is not stable at any station.** Computed year by year, Bukit Kototabang's CH₄ peak falls in December, March, December, February, January, January and March across its seven complete years — a circular standard deviation of **1.2 months**, which is as large as the entire two-month "propagation" being claimed.
- **Three of the five stations cannot supply a climatology.** Sorong has one complete year, Jambi two, Bariri four. A peak month from one year is a single observation, not a phase.

**Finding 70 is therefore reported as not supported.** The seasonal CH₄ maximum across the archipelago falls broadly in the December–March monsoon window at every station that has enough data to say so, and this network cannot currently distinguish a zonally propagating crest from year-to-year noise. *An earlier draft also quoted the speed as "~15.5° per month (~40 km day⁻¹ or 0.46 m s⁻¹)"; those are not the same speed — 15.5° per month at the equator is 57 km day⁻¹.*

> **What would settle it.** Five more years at Sorong, Jambi and Bariri would bring every station to a stable climatology, at which point a 1–2 month zonal phase difference would be resolvable against a circular s.d. of about 0.5 months. The hypothesis is reasonable; the record is not yet long enough to test it.

### 10.14 Finding 82 — a persistence ladder: how long each species remembers an anomaly

The seasonal cycle says when a species arrives; the persistence says how long a departure from normal survives. Both are transport statements for a species with no local source, and the difference between them is diagnostic: a species that outlasts the transport memory is being reloaded near the site.

The measure is the e-folding lag of the autocorrelation function of monthly flask anomalies — the residual about a fitted quadratic-plus-three-harmonic model, so both the trend and the seasonal cycle are removed before the memory is measured.

**Table 63 — persistence of monthly anomalies at Bukit Kototabang** (from `outputs/p_persistence.csv`):

| Species | Months | Lag-1 autocorrelation | e-folding (months) | Residual s.d. |
|---|---|---|---|---|
| N₂O | 241 | 0.853 | **5.9** | 0.282 ppb |
| CO | 232 | 0.735 | 2.1 | 19.918 ppb |
| SF₆ | 241 | 0.789 | 2.1 | 0.054 ppt |
| CH₄ | 241 | 0.709 | 2.0 | 14.388 ppb |
| CO₂ | 242 | 0.650 | 1.7 | 2.458 ppm |
| H₂ | 152 | 0.679 | 1.6 | 5.261 ppb |

**Five of the six species sit within half a month of each other, at 1.6 to 2.1 months.** That common value is the transport memory of the site: how long an air mass anomaly of any composition survives over Sumatra before the general circulation replaces it. Chemistry does not enter — SF₆ is inert and sits at 2.1, CO has a lifetime of weeks to months and sits at 2.1 as well.

**N₂O is the exception at 5.9 months**, nearly three times the network's transport memory, and its lag-1 autocorrelation of 0.853 is the highest in the table. A species cannot remember longer than its air mass unless something is holding it there. Finding 39 finds N₂O has a regional source and Finding 55 finds that source is aseasonal — a slow, continuous, spatially extensive input, which is what agricultural soil emission looks like, and which would produce exactly this signature.

> **This is not Finding 38.** Finding 38 gives 19 days for CO from *daily* data. This gives 2.1 months for CO from *monthly* data. They are different statistics of different series and neither confirms the other: the daily number measures how long a single fire plume persists, the monthly one how long a whole season's anomaly does. Quoting either as "the CO memory" without saying which would be wrong.

---

## 11. The regional enhancement ladder — Findings 15, 36, 37, 62, 63

Afternoon 20th-percentile air is well-mixed and regionally representative, so differencing it between stations gives a *regional* enhancement rather than a local plume statistic. Referenced to Bariri and matched month by month (Figures 10b–d, 13a):

**Table 64 — afternoon-background enhancement over Bariri (mean ± s.e.)**

| Station | ΔCO₂ (ppm) | ΔCH₄ (ppb) | ΔCO (ppb) | months |
|---|---|---|---|---|
| SRG Sorong | +1.9 ± 0.3 | +9.8 ± 3.2 | **−2.5 ± 2.2** | 23 |
| BKT Bukit Kototabang | +2.0 ± 0.2 | +22.4 ± 2.6 | +12.5 ± 3.8 | 28 |
| JMB Jambi | +4.6 ± 0.3 | +66.2 ± 3.5 | +52.2 ± 2.2 | 21 |
| KMY Kemayoran | +10.3 ± 0.4 | +92.4 ± 5.9 | +151.8 ± 6.8 | 21 |

Because Bukit Kototabang agrees with its own NOAA flasks to +0.31 ppm (Section 4.1), **this entire ladder is anchored to the WMO scale** through that station.

**Sorong has less CO than the GAW regional forest station.** −2.5 ± 2.2 ppb is not significant alone, but the direction is consistent across 23 months and it is the only negative entry. Sorong at 131 °E sits in maritime Pacific and Southern-Hemisphere air. **For CO specifically, Sorong — not Bariri — is the network's clean end member**, so the network's reference anchor should be split by species.

**The ratios along the ladder are diagnostic.** Jambi's regional signature is ΔCH₄/ΔCO₂ = 14.4 ppb ppm⁻¹ against Jakarta's 9.0 — Jambi's *regional* air is more methane-rich relative to its CO₂ than a megacity's, which is what drained peat and canals produce and a city does not. Jakarta's regional ΔCO/ΔCO₂ is 14.7 ppb ppm⁻¹, well below the 23.5 in its own nocturnal layer, the expected dilution of a combustion signature into the regional mix.

**Bukit Kototabang is not a clean site for methane.** +22.4 ± 2.6 ppb over Bariri in well-mixed afternoon air is a large, highly significant regional enhancement for a station classified GAW *global*. Sumatra's peat, plantation and rice are upwind, and it shows.

### 11.2 Findings 36 and 37 — against marine air, and how far the region coheres

![Figure 21](figures/f21_regional.png)

**Figure 21.** (a) Correlation of the monthly background anomaly between each pair of stations, against their separation. (b) Bariri and Sorong compared with tropical marine air at Samoa. (c) The H₂–CO correlation by month (Section 9.7).

**Finding 36 — a CO₂ sink region and a CO source region, at once.** Comparing the two clean Indonesian sites with Samoa, the tropical Southern-Hemisphere marine reference:

**Table 65 — Indonesian clean-site enhancements relative to Samoa**

| | ΔCO₂ vs Samoa | ΔCO vs Samoa |
|---|---|---|
| PLU Bariri | **−6.33 ± 0.46 ppm** | **+25.6 ± 2.2 ppb** |
| SRG Sorong | **−3.87 ± 0.36 ppm** | **+24.6 ± 2.0 ppb** |

Both sites are **simultaneously lower in CO₂ and higher in CO** than marine air at the same latitude band. Those two signs together are the region's signature: a land surface photosynthesising hard enough to draw CO₂ *below* the marine background, and a fire and combustion source pushing CO well above it. Neither statement alone would be surprising; the combination is, and it is what makes the Maritime Continent a distinctive place in the global network rather than just a clean tropical site.

This also settles a question Section 11 left open. Sorong's negative CO relative to *Bariri* (−2.5 ppb) invited the reading that Sorong samples marine air. It does not: relative to actual marine air it is +24.6 ppb. **Sorong is the cleanest site in this network and is still a long way from clean.**

**Finding 37 — coherence follows site type, not distance.** Correlating the detrended monthly background anomaly between every pair:

**Table 66 — Inter-station coherence of monthly background anomalies**

| Pair | Separation | *r* | |
|---|---|---|---|
| JMB–KMY | 618 km | **−0.03** | both polluted |
| PLU–SRG | 1,252 km | +0.55 | both background |
| KMY–PLU | 1,562 km | +0.22 | |
| JMB–PLU | 1,822 km | +0.38 | |
| **BKT–PLU** | **2,194 km** | **+0.69** | both background |
| KMY–SRG | 2,774 km | −0.20 | |
| JMB–SRG | 3,074 km | +0.57 | |

Two consequences follow, and both are operational. **A "regional background" derived from a polluted station is not regional**, however carefully the percentile is chosen — Kemayoran's monthly anomaly carries no information about Bariri's. And **the spacing of a background network should be set by site quality, not by a target separation**: two clean sites 2,000 km apart tell you more about the regional air mass than two mixed sites 600 km apart.

### 11.3 Finding 62 — Bariri is 2.0 ppm lower in CO₂ and 22 ppb lower in CH₄ than Bukit Kototabang

Comparing the clean afternoon $q20$ background between the two pristine montane stations over 28 overlapping months (2021–2025):

**Table 67 — afternoon background baseline comparison between Bariri (PLU) and Bukit Kototabang (BKT) (2021–2025)** (from `outputs/t_plu_vs_bkt.csv`)

| Species | Unit | PLU mean $q20$ | BKT mean $q20$ | PLU − BKT | Correlation *r* | *p*-value |
|---|---|---|---|---|---|---|
| CO₂ | ppm | 408.95 | 410.99 | **-2.04 ± 1.30** | **0.875** | 1.1e-09 |
| CH₄ | ppb | 1900.87 | 1923.29 | **-22.42 ± 13.84** | **0.839** | 2.5e-08 |
| CO | ppb | 86.51 | 98.99 | **-12.47 ± 20.15** | **0.857** | 5.9e-09 |

**Bariri in Central Sulawesi is 2.0 ppm lower in CO₂, 22.4 ppb lower in CH₄, and 12.5 ppb lower in CO than Bukit Kototabang in Sumatra.** The high correlation (*r* = 0.84–0.88 across all three species) proves that both stations track the same macroscopic tropical background, but Bukit Kototabang's air carries a persistent regional enhancement from upwind Sumatran peatlands, agriculture, and land clearing. Bariri (1,400 m in primary montane rainforest) defines the cleanest terrestrial baseline in the Indonesian archipelago.

> **Its limits.** Bariri sits at 1,400 m elevation compared to BKT's 865 m; vertical stratification contributes a small fraction of the offset, but the consistent multi-species deficit reflects Wallacea's isolation from major continental emission belts.

### 11.4 Finding 63 — clean Sorong shares the Maritime Continent CO₂ deficit, with a substantial terrestrial CH₄ and CO excess

Evaluating Sorong's post-June 2023 clean record against NOAA marine reference stations over 25 overlapping months:

**Table 68 — Sorong greenhouse-gas levels relative to marine reference sites**

| Species | Unit | SRG median | SMO (Samoa) | SRG − SMO | KUM (Kumukahi) | SRG − KUM |
|---|---|---|---|---|---|---|
| CO₂ | ppm | 418.30 | 422.17 | **−3.87 ± 1.80** | 424.80 | **−6.50 ± 2.13** |
| CH₄ | ppb | 1939.24 | 1886.79 | **+52.45 ± 16.51** | 1964.80 | −25.56 ± 29.32 |
| CO | ppb | 97.66 | 60.10 | **+37.56 ± 13.35** | 91.17 | +6.49 ± 21.17 |

Sorong exhibits a **3.9 ppm CO₂ deficit relative to Samoa and 6.5 ppm relative to Kumukahi**, demonstrating that the Maritime Continent equatorial CO₂ drawdown extends across western New Guinea into the Pacific entrance. Its CH₄ and CO run +52.5 and +37.6 ppb above pristine Southern-Hemisphere marine air, quantifying the terrestrial increment added as marine air encounters the coastal fringe of Southwest Papua.

> **Its limits.** Only data from June 2023 onward are included, per the diurnal rectifier and baseline quality exclusion (Section 4.6).

### 11.5 Finding 78 — the same ladder in the currency of carbon accounting

The ladder above is in ppm and ppb, which answers an atmospheric question. Every instrument under *Nilai Ekonomi Karbon* counts CO₂-equivalent, and the conversion is not a formality: it changes which species matters at which site.

On a *mixing ratio*, the conversion is simpler than a mass conversion, because a mole of methane and a mole of carbon dioxide occupy the same volume. A 1 ppb methane excess weighs (16.04/44.01) × 10⁻³ as much as a 1 ppm carbon dioxide excess, so

$$\Delta\mathrm{CO_2e}\ [\mathrm{ppm}] = \Delta\mathrm{CO_2} + \Delta\mathrm{CH_4}\,[\mathrm{ppb}]\times 10^{-3}\times\frac{16.04}{44.01}\times \mathrm{GWP}_{\mathrm{CH_4}}$$

**Table 69 — the enhancement ladder over the Bariri forest reference, in CO₂-equivalent** (from `outputs/p_co2e_ladder.csv`; GWP-100 = 27.9):

| Station | ΔCO₂ (ppm) | ΔCH₄ (ppb) | CH₄ as CO₂e (ppm) | Total CO₂e (ppm) | s.e. | CH₄ share | ΔCO (ppb, not counted) |
|---|---|---|---|---|---|---|---|
| SRG Sorong | 1.91 | 9.8 | 0.10 | **2.01** | 0.34 | 4.9 % | −2.5 |
| BKT Bukit Kototabang | 2.04 | 22.4 | 0.23 | **2.27** | 0.25 | 10.0 % | 12.5 |
| JMB Jambi | 4.59 | 66.2 | 0.67 | **5.26** | 0.30 | 12.8 % | 52.2 |
| KMY Kemayoran | 10.32 | 92.4 | 0.94 | **11.26** | 0.41 | 8.3 % | 151.8 |

Three things are worth stating plainly.

**Methane's share of the accountable enhancement is smaller than its concentration suggests, and it peaks at Jambi, not Jakarta.** Kemayoran has the largest absolute methane excess in the network at 92.4 ppb, but its CO₂ excess is larger still, so methane carries 8.3 % of its CO₂-equivalent against Jambi's 12.8 %. A tonne-counting framework ranks the drained peatland as the more methane-weighted site, and the concentration table does not.

**Carbon monoxide, the species that separates these sites most sharply — a factor of 60 between Sorong and Kemayoran — contributes nothing.** CO has no GWP under Paris accounting; it is an indirect forcer, acting through OH and ozone, and no instrument in NEK prices it. The column is carried in the table with its exclusion stated, because a reader coming from Part III will expect it and its absence is a policy fact rather than an oversight.

**The ordering is unchanged from Table 64's.** The conversion rescales the ladder; it does not reorder it. Whatever the units, Kemayoran is five times Bukit Kototabang and twice Jambi.

> **The reference is a site, not a background.** Every number here is *relative to Bariri*, which has its own enhancement over marine air (Finding 62). These are the differences an inter-station scheme could use; they are not the absolute excess of each site over unpolluted air, and they must not be added to a global background to obtain one.

### 11.6 Finding 80 — a negative result: how often a station sees clean air does not tell you what kind of station it is

The obvious way to choose a baseline site from data alone is to count how much of its record is background air. The test was run, and it fails — usefully, because the failure locates where the discrimination actually comes from.

The metric is the fraction of hours within 2 ppm of the site's own 30-day afternoon 20th-percentile CO₂ background. The baseline is built from afternoon hours only, then applied to the whole day, so the night — when local emissions accumulate — is counted rather than excluded.

**Table 70 — fraction of the record that is background air** (from `outputs/p_clean_fraction.csv`):

| Station | Hours | Median excess (ppm) | 90th percentile | Clean, all hours | Clean, afternoon only |
|---|---|---|---|---|---|
| JMB Jambi | 14,422 | 15.32 | 51.69 | 14.0 % | 41.5 % |
| SRG Sorong | 13,474 | 8.34 | 25.08 | 13.4 % | 45.1 % |
| KMY Kemayoran | 16,440 | 11.99 | 38.22 | 12.6 % | 35.8 % |
| PLU Bariri | 32,555 | 18.30 | 40.70 | 11.3 % | 47.0 % |
| BKT Bukit Kototabang | 60,634 | 12.27 | 29.32 | 10.9 % | 40.9 % |

**All five sites lie between 10.9 % and 14.0 %** — a range of 3.1 points across a megacity core, a drained peatland, a coastal town, a GAW global mountain station and a montane rainforest. Worse for the hypothesis, the ordering is *inverted*: the rainforest reference has the highest median excess in the network, 18.30 ppm, and the second-lowest clean fraction.

The mechanism is not subtle once seen. Nocturnal accumulation under a shallow stable layer happens over any vegetated surface, and Finding 84 measures Bariri's accumulation rate at 1.98 ppm h⁻¹ against Kemayoran's 1.58. A forest at night is not clean air; it is a respiring surface under a lid. What makes Bariri a reference site is not that its air is usually clean but that its air is clean *at a predictable time of day*.

The afternoon column carries that. Restricted to 12:00–16:00, the sites separate the right way — Bariri highest at 47.0 %, Kemayoran lowest at 35.8 % — though even there the spread is 11 points, not the order of magnitude their enhancements differ by.

> **The methodological point, which is the finding.** The afternoon selection used throughout this report is not a convenience for removing noise. It is the entire mechanism by which a station's regional signal is separated from its local one, and Table 70 measures how much work it does. A network designed for carbon accounting cannot be sited on annual statistics; it has to be sited on what its afternoons look like.

---

# Part IV — Trends and forcing

## 12. Growth rates — Findings 20, 22 to 25, 30, 31, 54 to 57, 66

![Figure 22](figures/f22_trends.png)

**Figure 22.** Monthly regional background (afternoon 20th percentile). Red bands mark the periods excluded per Table 8. Bottom: Theil–Sen growth rates of the seasonally-adjusted background, 95 % CI.

**Table 71 — growth rates**

| Source | Station | Species | Period | Growth rate | 95 % CI |
|---|---|---|---|---|---|
| in-situ | BKT | CO₂ | 2009–2013 | +1.55 ppm yr⁻¹ | [+1.20, +1.90] |
| in-situ | BKT | CO₂ | 2019–2024 | **+2.28 ppm yr⁻¹** | [+2.06, +2.48] |
| in-situ | BKT | CH₄ | 2019–2024 | +12.84 ppb yr⁻¹ | [+10.99, +14.34] |
| in-situ | PLU | CO₂ | 2021–2026 | +2.86 ppm yr⁻¹ | [+2.66, +3.05] |
| in-situ | PLU | CH₄ | 2021–2026 | +8.35 ppb yr⁻¹ | [+7.13, +9.72] |
| in-situ | PLU | CO | 2021–2026 | +1.29 ppb yr⁻¹ | [−0.10, +2.98] |
| **flask** | **BKT** | **CO₂** | **2004–2025** | **+2.32 ppm yr⁻¹** | **[+2.26, +2.38]** |
| **flask** | **BKT** | **CH₄** | **2004–2025** | **+7.91 ppb yr⁻¹** | **[+7.50, +8.28]** |
| **flask** | **BKT** | **CO** | **2004–2025** | **−0.87 ppb yr⁻¹** | **[−1.53, −0.22]** |
| **flask** | **BKT** | **N₂O** | **2004–2025** | **+0.99 ppb yr⁻¹** | **[+0.98, +1.00]** |
| **flask** | **BKT** | **SF₆** | **2004–2025** | **+0.326 ppt yr⁻¹** | **[+0.322, +0.330]** |
| **flask** | **BKT** | **H₂** | **2009–2024** | **+1.51 ppb yr⁻¹** | **[+1.16, +1.84]** |

The flask series adds three species the hourly archive never measured. **N₂O rises at 0.99 ppb yr⁻¹ and SF₆ at 0.326 ppt yr⁻¹**, both with very tight intervals — SF₆'s trend is the most precisely determined quantity anywhere in this report, which is what an inert gas with a monotonic industrial source and no sink looks like. The **hydrogen trend of +1.51 ppb yr⁻¹** is worth flagging because H₂ is rarely measured in this region and is of growing interest as an energy carrier.

The in-situ and flask CO₂ growth rates agree (+2.28 for 2019–2024 against +2.32 over the full 22 years), which is another way of stating Finding 3.

### 12.1 The timestamp switch doubled the apparent growth rate

An earlier pass on the raw timestamps put BKT's 2019–2024 CO₂ growth at **+5.08 ppm yr⁻¹** and appeared to show a permanent +11 ppm calibration step at the turn of 2021. Both were artefacts of Finding 1: from 1 January 2021 the "12:00–16:00" selection actually picks 19:00–23:00 local, so every 2021+ baseline was biased high by about 10 ppm.

**Table 72 — Effect of timestamp correction on Bukit Kototabang diagnostics**

| | Raw timestamps | Corrected |
|---|---|---|
| BKT CO₂ growth, 2019–2024 | +5.08 ppm yr⁻¹ | **+2.28 ppm yr⁻¹** |
| BKT − Bariri CO₂ level, 2023 | +12.9 ppm | **+2.0 ppm** |

### 12.2 The remaining episodes, and an empirical repair

Two genuine instrument episodes survive the timestamp fix. Both can be diagnosed without an external series, using the fact that **CO₂ and CH₄ share the CRDS analyser while CO is a separate channel**:

**Table 73 — Diagnosis and treatment of remaining instrumental episodes**

| Pattern | Diagnosis | Action |
|---|---|---|
| CO₂ anomalous, CH₄ **and** CO normal | CO₂ calibration / working-standard assignment | correctable — subtract the offset |
| CO₂ **and** CH₄ anomalous, CO normal | analyser-wide fault | not recoverable — reject |
| CO₂ **and** CO anomalous | real air mass (fire plume) | leave alone |

The procedure fits a quadratic-plus-three-harmonics reference model to the monthly background with iterative Tukey biweight reweighting, takes the monthly residual as the candidate offset, and classifies by the table. Robust residual scatter of the good months is σ = 1.16 ppm.

**Table 74 — every month with |z| > 3, and what the companion channels say**

| Month | CO₂ obs | model | residual | z(CO₂) | z(CH₄) | z(CO) | Diagnosis |
|---|---|---|---|---|---|---|---|
| 2013-10 | 364.9 | 386.6 | −21.7 | −18.8 | −6.9 | −0.0 | analyser fault |
| 2013-11 | 374.1 | 386.7 | −12.6 | −10.9 | +4.2 | +0.4 | analyser fault |
| 2019-10 | 407.2 | 402.8 | +4.5 | +3.9 | +1.0 | **+5.9** | **atmospheric — 2019 haze** |
| 2020-12 | 415.7 | 407.6 | +8.1 | +7.0 | +0.3 | +0.0 | CO₂ calibration |
| 2021-01 | 418.6 | 408.3 | +10.3 | +8.9 | +0.1 | +0.4 | CO₂ calibration |
| 2021-02 | 418.2 | 408.6 | +9.7 | +8.4 | +0.4 | +0.3 | CO₂ calibration |
| 2021-03 | 416.7 | 408.6 | +8.1 | +7.0 | +0.1 | −0.4 | CO₂ calibration |
| 2021-04 | 415.9 | 407.9 | +8.0 | +6.9 | +0.0 | +0.0 | CO₂ calibration |
| 2021-05 | 417.7 | 406.9 | +10.8 | +9.3 | +1.5 | +0.5 | CO₂ calibration |
| 2021-06 | 401.8 | 406.3 | −4.5 | −3.9 | +0.6 | −0.7 | CO₂ calibration |

Note the discipline this imposes. **October 2019 is not corrected**: CO₂ is 3.9σ high, but CO is 5.9σ high alongside it, so the enhancement is a real air mass — the 2019 peat haze. A method keying on CO₂ alone would have corrected away one of the most valuable months in the record.

**Table 75 — the derived correction**

| Window | Months | Diagnosis | Action | Offset ± s.e. |
|---|---|---|---|---|
| 2020-12 → 2021-05 | 6 | CO₂ calibration | subtract | **+9.16 ± 0.51 ppm** |
| 2021-06 | 1 | CO₂ calibration | subtract | **−4.53 ± 1.16 ppm** |
| 2013-10 → 2013-11 | 2 | analyser fault | **reject CO₂ and CH₄** | (−17.2, not recoverable) |

![Figure 23](figures/f23_bkt_co2_correction.png)

**Figure 23.** (a) The BKT CO₂ monthly background as archived, the robust reference model, the corrected series, and Bariri as an independent check. (b) Residuals, coloured by diagnosis.

Four tests, all passed: monthly residual RMS falls from 2.53 to **1.03 ppm**; the largest single residual from 10.80 to **4.53 ppm**; the largest month-to-month step from 20.14 to **3.90 ppm** (network p90 is 2.0–3.7); and the BKT − Bariri relative drift over 28 overlap months is **−0.34 ppm yr⁻¹, CI [−1.15, +0.54]** — indistinguishable from zero. The growth rates barely move, as expected for bounded level errors in seven months.

**And the flasks confirm the diagnosis** (Section 4.2): they read +8.70 ppm above the in-situ record in 2013, the year of the analyser fault, at the right sign and a consistent magnitude.

<!-- pdf-pagebreak -->

> **Caveat.** The offsets are derived from the atmosphere, not from the calibration cylinders, so they are an *empirical repair* pending confirmation against the working-standard logs for December 2020 – June 2021.


### 12.3 Finding 20 — two stations resolve the 2023 El Niño anomaly

A single Theil–Sen slope averages interannual variability away. The 12-month difference of the deseasonalised monthly background gives a year-by-year growth rate — and CO₂ growth responds most sharply to ENSO, because El Niño drought suppresses tropical land uptake.

**Table 76 — annual CO₂ growth (ppm yr⁻¹)**

| Year | BKT | PLU (Bariri) |
|---|---|---|
| 2012 | +2.27 | — |
| 2013 | +0.63 | — |
| 2020 | −0.27 | — |
| 2022 | +2.54 | +2.13 |
| **2023** | **+4.20** | **+4.24** |
| 2024 | — | +2.46 |
| 2025 | — | +1.91 |

The 2023 values agree to **0.04 ppm yr⁻¹** between two instruments on two islands 2,000 km apart, one of which needed the repair of Section 12.2 and the other of which did not. Both sit about **+2.1 ppm yr⁻¹ above their surrounding years**. This is the tropical land-carbon response to the 2023 El Niño, resolved in an equatorial Indonesian surface record — a region that is normally a gap in the global growth-rate network.

**Methane does not do the same thing.** Both sites put CH₄ growth at its maximum in 2022 (BKT +18.6, PLU +19.0 ppb yr⁻¹) and Bariri then decelerates to +9.8 (2024) and +6.2 (2025), but the two **disagree in 2023** (BKT +18.0, PLU +4.1) and nothing in the data explains it. Report the 2022 maximum and the deceleration; do not quote a single-year tropical CH₄ growth rate from one station.

**A trap worth naming.** A 12-month difference computed over a series indexed by *available* months, rather than a complete monthly axis, will take the difference across a multi-year gap and report it as one year's growth. A first attempt produced BKT CO₂ growth of +10.1 ppm yr⁻¹ for 2013 and +11.3 for 2019 — pure artefacts of the 2014–2018 gap. Reindexing onto a complete monthly axis, bridging single missing months and letting anything longer kill the window, gives Table 76.

### 12.4 Findings 22 and 23 — the growth rates are themselves increasing

A trend says how fast a gas is accumulating; its *second* derivative says whether the source is growing. Fitting a quadratic to each deseasonalised flask series over 2004–2025:

![Figure 24](figures/f24_trends_gradients.png)

**Figure 24.** (a) Each species' 2014–2025 growth rate as a multiple of its 2004–2013 rate; CO is excluded because its trend is negative, so a ratio of two negative slopes would read as acceleration when it means a slowing decline. (b) Trend in the Barrow-minus-South-Pole difference, as a percentage of the mean gradient. (c) Bukit Kototabang's CO seasonal cycle split into the part predicted by SF₆ and the local residual, with the two burning seasons shaded.

**Table 77 — growth-rate acceleration at Bukit Kototabang**

| Species | Growth at midpoint | Acceleration | 95 % CI | |
|---|---|---|---|---|
| **CO₂** | +2.33 ppm yr⁻¹ | **+0.0446 ppm yr⁻²** | ±0.0210 | significant |
| **CH₄** | +8.04 ppb yr⁻¹ | **+0.398 ppb yr⁻²** | ±0.152 | significant |
| **N₂O** | +0.99 ppb yr⁻¹ | **+0.0200 ppb yr⁻²** | ±0.0024 | significant |
| **SF₆** | +0.328 ppt yr⁻¹ | **+0.0075 ppt yr⁻²** | ±0.0005 | significant |
| CO | −1.66 ppb yr⁻¹ | +0.099 ppb yr⁻² | ±0.449 | not significant |
| H₂ | +1.05 ppb yr⁻¹ | −0.217 ppb yr⁻² | ±0.434 | not significant |

**Every one of the four long-lived greenhouse gases is accelerating; neither of the two short-lived or secondary species is.** That split is the finding. CO₂, CH₄, N₂O and SF₆ all have lifetimes long enough that their surface mixing ratio integrates global emissions, so a positive second derivative means global emissions are still rising. CO has a two-month lifetime and H₂ a strong soil sink, so both reflect regional emission rather than global accumulation, and neither shows a trend in its trend.

Splitting the record at 2014 makes the same point in more familiar units (Figure 24a):

**Table 78 — decadal growth rates**

| Species | 2004–2013 | 2014–2025 | Ratio |
|---|---|---|---|
| CO₂ | +2.00 [+1.78, +2.24] ppm yr⁻¹ | +2.52 [+2.37, +2.64] | ×1.26 |
| **CH₄** | **+3.65 [+2.37, +4.89] ppb yr⁻¹** | **+9.38 [+8.39, +10.43]** | **×2.57** |
| N₂O | +0.85 [+0.83, +0.88] ppb yr⁻¹ | +1.10 [+1.08, +1.12] | ×1.29 |
| SF₆ | +0.278 [+0.272, +0.283] ppt yr⁻¹ | +0.360 [+0.355, +0.365] | ×1.30 |
| CO | −3.28 [−6.19, −0.70] ppb yr⁻¹ | −1.97 [−3.78, −0.40] | decline slowing |

CO₂, N₂O and SF₆ each speed up by about 30 %. **Methane speeds up by a factor of 2.6**, with non-overlapping intervals — the post-2014 renewed growth, measured at a tropical station on one calibration scale. CO is the exception in both direction and behaviour: it is falling, and falling more slowly than it was.

### 12.5 Finding 24 — how much ENSO moves the growth rate, and when

Section 12.3 showed the 2023 anomaly at two stations. Twenty-two years of flask data turn that anecdote into a sensitivity. Growth is taken as the 12-month difference of a smoothed deseasonalised series, so it is defined monthly and the lag against the Oceanic Niño Index can be resolved rather than assumed.

**Table 79 — ENSO sensitivity of the growth rate, best lag from a 0–15 month scan**

| Species | Best lag | *r* | Sensitivity | n months |
|---|---|---|---|---|
| **CO₂** | **0 months** | +0.38 | **+0.82 ± 0.27 ppm yr⁻¹ per °C** | 215 |
| **CO** | **0 months** | +0.50 | **+32.0 ± 7.5 ppb yr⁻¹ per °C** | 215 |
| **CH₄** | **12 months** | **−0.50** | **−10.8 ± 2.5 ppb yr⁻¹ per °C** | 215 |

Three distinct behaviours, and each makes physical sense.

**CO₂ responds immediately.** A global-mean growth series lags ENSO by several months, because the anomaly has to mix out of the tropics. Bukit Kototabang sits *inside* the region where the anomaly is generated — El Niño drought suppresses tropical land uptake and promotes fire — so it sees the response as it happens. A zero-lag maximum is what a source-region station should show, and it is a small piece of evidence that this station is well placed for carbon-cycle work.

**CO responds immediately and hard**, at +32 ppb yr⁻¹ per °C, which is the fire term of the same drought.

**Methane responds a year later, and downward.** A −10.8 ppb yr⁻¹ per °C sensitivity peaking at a 12-month lag says El Niño *suppresses* methane growth with a year's delay — the signature of tropical wetlands, where drought lowers water tables and cuts anaerobic production, and where the soil takes months to respond and months more to recover. It is the opposite sign to CO₂ and CO, from the same climate perturbation, which is why a single "ENSO affects greenhouse gases" statement is not useful without the species and the lag.

### 12.6 Finding 25 — the hemispheric gradient is widening, except for CO

The Barrow-minus-South-Pole difference is a clean index of where emissions are concentrated, and because both sites are in the same network on the same scales, a common calibration drift cancels (Figure 24b).

**Table 80 — trend in the interhemispheric difference, 2004–2025**

| Species | Mean gradient | Trend | 95 % CI | Relative |
|---|---|---|---|---|
| **SF₆** | 0.421 ppt | **+0.0078 ppt yr⁻¹** | [+0.0061, +0.0097] | **+1.84 % yr⁻¹** |
| **CO₂** | 5.02 ppm | **+0.069 ppm yr⁻¹** | [+0.036, +0.094] | **+1.37 % yr⁻¹** |
| **CH₄** | 143.6 ppb | **+0.467 ppb yr⁻¹** | [+0.140, +0.743] | **+0.33 % yr⁻¹** |
| N₂O | 1.44 ppb | +0.0055 ppb yr⁻¹ | [−0.0079, +0.0237] | not significant |
| **CO** | 71.4 ppb | **−0.573 ppb yr⁻¹** | [−0.853, −0.304] | **−0.80 % yr⁻¹** |

**Four species move, and CO moves the other way.** The Northern Hemisphere is pulling further ahead in SF₆, CO₂ and CH₄ — northern emissions of all three are outpacing southern ones, fastest for the purely industrial tracer. N₂O's gradient is flat, which is what a diffuse agricultural source spread across both hemispheres produces.

CO is the exception, and the reason is that CO is the only species in the list whose emissions are **deliberately regulated**. Catalytic converters, fuel standards and combustion controls act on exactly the Northern-Hemisphere industrial and vehicle sources that create the gradient in the first place, and two decades of that shows up as a hemispheric gap closing at 0.8 % a year.

That contrast is worth stating plainly: **on this evidence, air-quality regulation is visibly working on a hemispheric scale, and climate regulation is not yet.** The same network, the same period, the same instruments — and the species we control for health is converging while the species we control for climate diverge.

### 12.7 Findings 30 and 31 — the same growth rates as a carbon budget

A growth rate in ppm yr⁻¹ is a concentration statement. Converting it to a mass makes it comparable with emissions and sinks, and the conversion needs no external constant — it follows from the mass of the atmosphere and two molar masses:

$$1\ \text{ppm CO}_2 = \frac{M_{\text{atm}}}{M_{\text{air}}} \times 10^{-6} \times M_{\text{C}}
= \frac{5.148\times10^{21}\ \text{g}}{28.96\ \text{g mol}^{-1}} \times 10^{-6} \times 12.011\ \text{g mol}^{-1}
= 2.135\ \text{Pg C}$$

**Table 81 — Bukit Kototabang's own record, in carbon-budget units**

| Quantity | Value | |
|---|---|---|
| Flask CO₂ growth, 2004–2025 | +2.32 [+2.26, +2.38] ppm yr⁻¹ | measured here |
| Implied atmospheric accumulation | **4.96 [4.83, 5.08] Pg C yr⁻¹** | × 2.135 |
| Total anthropogenic emissions | 11.1 Pg C yr⁻¹ | published |
| **Airborne fraction** | **45 %** | 4.96 / 11.1 |
| Accumulation, 2004–2013 | 4.28 Pg C yr⁻¹ | from +2.00 ppm yr⁻¹ |
| Accumulation, 2014–2025 | **5.37 Pg C yr⁻¹** | from +2.52 ppm yr⁻¹ |
| 2023 El Niño anomaly (Bariri) | +2.08 ppm yr⁻¹ = **4.44 Pg C yr⁻¹** | Section 12.3 |

**Finding 30 — one equatorial station reproduces the global airborne fraction.** A single site on a Sumatran mountain ridge, sampled weekly into glass flasks, gives 45 % — inside the 40–50 % band that the global network and the emissions inventories together produce, and below the 53 % of the anomalous 2023. That is not a coincidence to be admired; it is a consequence of CO₂ being long-lived enough to be well mixed, and it is the reason a station like this is worth maintaining. **The airborne fraction is measurable from one clean record and an inventory, without a network.**

The decadal split says the same thing in absolute terms: the atmosphere took up **1.10 Pg C yr⁻¹ more** in 2014–2025 than in 2004–2013. Whether that is rising emissions or weakening sinks cannot be told from this record alone — that is exactly the question the global budget exists to answer — but the accumulation itself is measured here.

**Finding 31 — the 2023 anomaly is larger than the global land sink.** Bariri's 2023 growth ran 2.08 ppm yr⁻¹ above its neighbouring years, which is **4.44 Pg C yr⁻¹** of extra atmospheric carbon. For comparison the land sink removes about 3.2 Pg C yr⁻¹ and the ocean about 2.9.

So a single El Niño year put more carbon into the atmosphere, above trend, than the entire terrestrial biosphere removes from it in a normal year. The land sink is not a fixed subsidy; it is a flux that ENSO can cancel and reverse, and the tropics — where this station sits — are where that happens. Sections 12.5 and 12.6 measured the sensitivity and the lag; this is what the sensitivity is worth.

> **Caveat.** The airborne fraction here divides a *measured* accumulation by a *quoted* emissions total, so it inherits that inventory's uncertainty (±0.9 Pg C yr⁻¹, about 8 %). The 45 % is a 22-year mean and should not be compared with a single year's published value. The 2023 anomaly rests on Bariri's four usable years, and its baseline is three of them.

### 12.8 Findings 54 to 57 — four results from the six-species flask record

The flask programme measures six species on the same air. Most of this report uses them one at a time; asking what they do *together*, and what the two least-used of them do on their own, produces four results.

**Finding 54 — which species' growth anomalies move together.** Correlating the growth-rate anomalies of all six pairs, with the effective sample size of Section 16.1 applied so the answer is not an artefact of smoothing:

**Table 82 — growth-anomaly covariance at Bukit Kototabang (n = 217 months)**

| Pair | *r* | *n*<sub>eff</sub> | Significant? |
|---|---|---|---|
| **CH₄ – N₂O** | **+0.60** | 168 | yes |
| CH₄ – CO | +0.56 | 156 | yes |
| CH₄ – SF₆ | +0.39 | 168 | yes |
| CO₂ – CO | +0.35 | 168 | yes |
| CO₂ – CH₄ | +0.33 | 187 | yes |
| CO – N₂O | +0.31 | 140 | yes |
| N₂O – SF₆ | +0.31 | 154 | yes |
| CO₂ – N₂O | +0.31 | 178 | yes |
| CO₂ – SF₆ | +0.29 | 178 | yes |
| **CO – SF₆** | **+0.07** | 141 | **no** |

**The strongest pair is methane with nitrous oxide, and the only insignificant one is carbon monoxide with sulphur hexafluoride.** (Section 12.13 repeats this on a 7-month-smoothed series and gets systematically higher coefficients; the two answer different questions, and Section 12.13 explains which.) Both are informative. CH₄ and N₂O share the wetland-and-agriculture source region and the same ENSO-driven hydrology, and they covary more tightly than either does with CO₂. CO and SF₆ do not covary at all — and SF₆ is inert, so its variability is *pure transport*. **Carbon monoxide's interannual variability is therefore not transport; it is emission**, which is the same conclusion Section 10.6 reached from the seasonal cycle, now established on the interannual timescale by a different statistic.

**Finding 55 — nitrous oxide's seasonal cycle is transport, even though its mean is local.** Regressing each species' mean seasonal cycle on SF₆'s — the inert tracer whose seasonal cycle can only be transport:

**Table 83 — Seasonal transport attribution using sulphur hexafluoride**

| Species | *r* vs SF₆ cycle | *R*² — share transport explains |
|---|---|---|
| CH₄ | +0.98 | **97 %** |
| **N₂O** | **+0.95** | **89 %** |
| CO₂ | +0.65 | 43 % |
| CO | +0.54 | 29 % |

Section 10.7 found that N₂O sits above what transport alone would deliver — a regional source, most likely fertilised soils and biomass burning. Finding 55 says that source has **no detectable seasonality**: 89 % of the seasonal cycle is the same cross-equatorial transport that moves methane. A source that is regional in the *mean* but flat through the *year* is what a continuously fertilised agricultural landscape looks like, and it is not what a burning season looks like. The two findings are complementary rather than contradictory, and together they place the N₂O source in agriculture rather than in fire.

**Finding 56 — hydrogen is rising at +1.51 ppb yr⁻¹, and this is the baseline against which a hydrogen economy will be judged.** The flask H₂ record at Bukit Kototabang runs from September 2009 to December 2024:

$$\text{H}_2 = +1.51\ [+1.16,\ +1.84]\ \text{ppb yr}^{-1} = +0.27\ \%\ \text{yr}^{-1}\ \text{of the 560 ppb median}$$

Molecular hydrogen is an indirect greenhouse gas — it extends methane's lifetime by competing for OH — and large-scale hydrogen fuel deployment would leak some fraction of production to the atmosphere. **Whether that shows up is a question about a trend, and a trend can only be detected against a known prior rate.** This is a tropical Southern-Hemisphere baseline measured before deployment, on the WMO scale, with 156 monthly values. Its value is that it exists now.

**Finding 57 — the Maritime Continent's CO₂ deficit is widening against the South Pole but not against Mauna Loa.**

**Table 84 — Trends in Bukit Kototabang interhemispheric CO₂ differences**

| Difference | Mean (ppm) | Trend (ppm decade⁻¹) | 95 % CI |
|---|---|---|---|
| BKT − Mauna Loa | −5.30 | −0.03 | −0.49 to +0.43 |
| **BKT − South Pole** | −1.54 | **+0.74** | **+0.27 to +1.20** |
| BKT − Samoa | −3.08 | +0.41 | −0.03 to +0.88 |
| BKT − Kumukahi | −5.69 | +0.07 | −0.40 to +0.55 |

Bukit Kototabang is gaining on the South Pole at three quarters of a ppm per decade and holding station exactly against Mauna Loa. **The site is tracking the Northern Hemisphere, not the Southern**, despite sitting at 0.2 °S. That is Finding 17 stated in absolute terms: the SF₆ air-mass fraction identified Bukit Kototabang as receiving the network's largest Northern-Hemisphere influence, and here the CO₂ level does the same thing — its distance from the Northern reference sites is fixed while its distance from the Southern one grows.

### 12.9 Finding 66 — global synchrony in N₂O decadal acceleration (+0.21 to +0.24 ppb yr⁻¹ surge post-2014) across all latitudes

Section 12.4 measured a +0.020 ppb yr⁻² acceleration in nitrous oxide at Bukit Kototabang. Evaluating the 22-year flask record across five NOAA stations spanning 71°N to 90°S in two decadal brackets (2004–2013 vs 2014–2024):

**Table 85 — decadal N₂O growth rate acceleration (2004–2013 vs 2014–2024) across five NOAA stations**

| Station | Location | Lat | 2004–2013 growth (ppb yr⁻¹) | 2014–2024 growth (ppb yr⁻¹) | Decadal jump |
|---|---|---|---|---|---|
| BRW | Barrow, Alaska | +71.3° | +0.864 [+0.839, +0.891] | +1.070 [+1.047, +1.092] | **+0.206 ppb yr⁻¹** |
| KUM | Cape Kumukahi, Hawaii | +19.5° | +0.854 [+0.844, +0.863] | +1.097 [+1.079, +1.119] | **+0.242 ppb yr⁻¹** |
| **BKT** | **Bukit Kototabang** | **−0.2°** | **+0.864 [+0.829, +0.900]** | **+1.091 [+1.058, +1.123]** | **+0.226 ppb yr⁻¹** |
| SMO | Tutuila, Samoa | −14.3° | +0.885 [+0.862, +0.907] | +1.100 [+1.079, +1.121] | **+0.215 ppb yr⁻¹** |
| SPO | South Pole | −90.0° | +0.869 [+0.848, +0.891] | +1.110 [+1.083, +1.138] | **+0.241 ppb yr⁻¹** |

**The post-2014 acceleration of nitrous oxide is completely synchronous globally (+0.23 ± 0.02 ppb yr⁻¹ jump everywhere)** (Figure 11c). Unlike methane, whose growth surge is strongest in the Northern Hemisphere and tropics, N₂O's surge is latitudinally uniform, reflecting the diffuse, hemispheric dispersion of agricultural nitrogen application and atmospheric lifetime (~114 years).

> **Its limits.** The decadal split compares two 10-to-11-year linear slopes; annual growth rates exhibit short-term interannual fluctuations of ±0.3 ppb yr⁻¹ around the decadal trend.

### 12.10 Finding 71 — interhemispheric CO₂ growth rate asymmetry peaks during El Niño extremes

Evaluating the differential growth rate between the Arctic Northern Hemisphere (Barrow 71.3°N) and Antarctic Southern Hemisphere (South Pole 90.0°S), based on 12-month smoothed differences:

**Table 86 — interhemispheric CO₂ growth rate asymmetry** (from `outputs/t_enso_growth_asymmetry.csv`)

| Parameter | Value | Unit |
|---|---|---|
| Mean interhemispheric growth asymmetry (BRW − SPO) | **+0.103 ± 0.897** | ppm yr⁻¹ |
| Maximum growth asymmetry (Northern surge) | **+2.443** | ppm yr⁻¹ |
| Minimum growth asymmetry (Southern/Equatorial surge) | **−2.541** | ppm yr⁻¹ |
| Mean equatorial vs southern asymmetry (BKT − SPO) | **+0.248 ± 2.571** | ppm yr⁻¹ |

**While the 22-year mean growth rates of both hemispheres are balanced to within −0.07 ppm yr⁻¹, interannual growth diverges by up to ±3.5 ppm yr⁻¹ during major ENSO cycles.** During strong El Niño events (2015–2016 and 2023) the tropical and Southern Hemisphere growth rate accelerates ahead of the Arctic, which is consistent with tropical biospheric drought releasing carbon that is then mixed globally. *No lag was fitted here* — Section 12.5 measures the ENSO lag directly, and Finding 51 shows that even there the record supports the timing but not a tight interval on the sensitivity.

> **Its limits.** 12-month differences remove the annual cycle; a 7-month rolling smoother reduces short-term sampling noise while preserving the interannual ENSO pulse.

### 12.11 Finding 72 — methane interhemispheric gradient evolution: tropical origin of the post-2014 resurgence

Comparing the interhemispheric CH₄ gradient segments across the 2004–2013 and 2014–2024 decadal periods:

**Table 87 — decadal evolution of methane interhemispheric gradient segments** (from `outputs/t_ch4_gradient_evolution.csv`)

| Gradient segment | 2004–2013 (ppb) | 2014–2024 (ppb) | Difference (ppb) |
|---|---|---|---|
| **Total interhemispheric (BRW − SPO)** | 141.8 | 145.8 | **+4.0** |
| **Tropical increment (BKT − SPO)** | **77.7** | **81.3** | **+3.6 (+90.0 % of total)** |
| **Northern extra-tropical (BRW − BKT)** | **64.2** | **64.5** | **+0.4 (+10.0 % of total)** |

**The post-2014 global methane resurgence was overwhelmingly tropical in origin.** Of the +4.0 ppb total expansion in the pole-to-pole methane gradient, **+3.6 ppb (90 %) occurred between the South Pole and equatorial Bukit Kototabang**, while the Northern extra-tropical gradient (Barrow minus Bukit Kototabang) remained virtually constant (+0.4 ppb). A year-block bootstrap puts the tropical increment at **+5.1 [+0.7, +9.2] ppb** and the northern one at **−0.7 [−5.8, +4.7] ppb**: the tropical expansion is significant, the northern one is not, and the 90 % split is a point estimate with wide bounds. This confirms from ground-level network observations that tropical wetlands, livestock, and peatland emissions drove the post-2014 global methane acceleration rather than high-latitude permafrost or fossil emissions.

> **Its limits.** Seasonal transport variations modulate monthly gradients; calculating decadal means across 10–11 full annual cycles isolates the secular source redistribution.

### 12.12 Finding 73 — vertical damping of seasonal cycles across the trade-wind inversion at 19.5°N

Comparing full harmonic seasonal expansions at sea-level Kumukahi (3 m) and high-altitude Mauna Loa (3,397 m) at identical latitude (19.5°N):

**Table 88 — vertical damping of seasonal cycle amplitudes at 19.5°N** (from `outputs/t_vertical_damping.csv`)

| Species | Unit | KUM surface (3 m) | MLO free troposphere (3,397 m) | Vertical damping |
|---|---|---|---|---|
| **CO₂** | ppm | **8.11** | **6.64** | **18.1 %** |
| **CH₄** | ppb | **35.46** | **31.09** | **12.3 %** |
| **CO** | ppb | **47.62** | **40.96** | **14.0 %** |

**Free-tropospheric air at Mauna Loa exhibits systematic 12–18 % damping of seasonal cycles relative to the marine boundary layer at Cape Kumukahi (Figure 20b).** Boundary-layer vertical mixing and the trade-wind inversion attenuate surface flux cycles as they propagate into the free troposphere, establishing the vertical gradient scale for tropical air-mass sampling.

> **Its limits.** Mauna Loa samples night-time downslope free-tropospheric air; Kumukahi samples daytime onshore marine trade-wind boundary-layer air.

### 12.13 Finding 74 — multi-species growth anomaly covariance structure across five trace gases

Cross-correlating the 12-month deseasonalized growth rate anomalies of the five long-lived NOAA flask species at Bukit Kototabang:

**Table 89 — growth rate anomaly cross-correlation matrix at Bukit Kototabang** (from `outputs/t_growth_covariance_matrix.csv`)

| Species | CO₂ | CH₄ | CO | N₂O | SF₆ |
|---|---|---|---|---|---|
| **CO₂** | 1.000 | 0.290 | 0.301 | **0.792** | **0.709** |
| **CH₄** | 0.290 | 1.000 | **0.669** | 0.495 | 0.305 |
| **CO** | 0.301 | **0.669** | 1.000 | 0.381 | **0.030** |
| **N₂O** | **0.792** | 0.495 | 0.381 | 1.000 | **0.822** |
| **SF₆** | **0.709** | 0.305 | **0.030** | **0.822** | 1.000 |

**The growth anomalies cleanly partition into two distinct physical clusters.** CO₂ covaries strongly with N₂O (*r* = +0.79) and SF₆ (*r* = +0.71), forming an industrial/agricultural expansion cluster. In contrast, CO correlates strongly with CH₄ (*r* = +0.67) due to shared biomass burning and incomplete combustion emissions, while remaining completely orthogonal to pure industrial SF₆ (*r* = +0.03).

**Table 90 — the same correlations under the Section 16.1 correction**

| Pair | *r* | *n* | *n*<sub>eff</sub> | *p* corrected |
|---|---|---|---|---|
| N₂O – SF₆ | +0.82 | 214 | 6.6 | 0.030 |
| CO₂ – N₂O | +0.79 | 214 | 8.7 | 0.013 |
| CO₂ – SF₆ | +0.71 | 214 | 8.8 | 0.035 |
| CH₄ – CO | +0.67 | 214 | 9.6 | 0.040 |
| CH₄ – N₂O | +0.49 | 214 | 8.0 | 0.212 |
| CO₂ – CO | +0.30 | 214 | 10.3 | 0.391 |
| CO₂ – CH₄ | +0.29 | 214 | 10.3 | 0.408 |
| CO – SF₆ | +0.03 | 214 | 8.2 | 0.942 |

**Only the four strongest pairs survive, and they survive narrowly.** The 7-month smoothing that makes the clusters visible also drives the effective sample size down to 7–10, so the four correlations quoted above sit at *p* = 0.013–0.040 and everything else in the matrix is indistinguishable from zero. The two-cluster reading stands; the individual coefficients should not be quoted to three decimals as though they were tightly determined.

> **This section and Finding 54 disagree, and the disagreement is the smoothing.** Section 12.8 reports CO₂–SF₆ at +0.29 and N₂O–SF₆ at +0.31 against +0.71 and +0.82 here. Both are correct for what they measure: Finding 54 uses the *unsmoothed* 12-month difference and so answers "do these species covary month to month", where the answer is weakly; this section smooths first and so answers "do they covary over multi-year swings", where the answer is strongly. Detrending changes neither result, so a shared secular trend is not the explanation. **Neither number should be cited without saying which timescale it refers to.**

> **Its other limits.** The 7-month window suppresses single-flask sampling noise at the cost of the degrees of freedom quantified above.

### 12.14 Finding 87 — a negative result: this site's flask CO₂ carries none of the global growth signal

The interannual variability of the global CO₂ growth rate is one of the most coherent signals in atmospheric science: an El Niño year raises it almost everywhere at once. A station whose annual growth tracks the global one is measuring the planet; a station whose annual growth does not is measuring something else, or measuring nothing. The question is worth asking of Bukit Kototabang, because Finding 20 shows the *in-situ* record resolving the 2023 anomaly to 0.04 ppm yr⁻¹, and it would be natural to assume the flask record can do the same.

It cannot. Annual growth from the flask record is regressed on the mean of Barrow and the South Pole — a two-point global proxy that contains no tropical station and so cannot share a regional signal with Bukit Kototabang by construction. Only complete years enter: a year missing three months of a 6.9 ppm seasonal cycle has an annual mean biased by more than the growth rate being measured.

**Table 91 — annual CO₂ growth regressed on the Barrow–South Pole mean** (from `outputs/p_global_coupling.csv`):

| Site | Years | Slope | *r* | *p* | Variance explained | Residual s.d. (ppm yr⁻¹) |
|---|---|---|---|---|---|---|
| **BKT Bukit Kototabang** | 17 | **0.069** | **0.028** | 0.9138 | **0.1 %** | **1.515** |
| MLO Mauna Loa | 43 | 0.793 | 0.857 | 0.0 | 73.5 % | 0.332 |
| SMO Tutuila, Samoa | 42 | 0.803 | 0.875 | 0.0 | 76.5 % | 0.317 |

**The two control sites are the finding.** Mauna Loa and Samoa go through the identical pipeline — same completeness gate, same proxy, same regression — and return slopes near 0.8 with three-quarters of the variance explained. The method works. At Bukit Kototabang it returns *r* = 0.028 and 0.1 % of variance, with a residual scatter of 1.515 ppm yr⁻¹ — larger than the entire interannual range of the global growth rate.

The cause is almost certainly sampling. NOAA rejects 30.9 % of this site's CO₂ flasks (Finding 6), against a few per cent at Mauna Loa; what remains is roughly weekly, drawn from air that Finding 78 shows carries a variable regional enhancement, and Finding 5 shows the site sits at a genuine regional minimum whose depth varies. A monthly mean built from two or three surviving flasks in a month of that variability is not a monthly mean of the background.

> **What this does and does not retract.** Nothing. It does not contradict Finding 20, which uses the *continuous* records at Bariri and Kemayoran and resolves the 2023 anomaly precisely; it does not contradict Finding 3, which establishes that the flask *levels* are on the WMO scale; and it does not contradict the flask-derived long-term trends of Finding 15, which average over two decades rather than resolving single years. What it says is narrower and worth saying: **at this site, discrete weekly sampling cannot resolve one year's growth anomaly.** That is a statement about the sampling density, not about the instrument, and Finding 53 — weekly sampling reconstructs a monthly mean to 1.51 ppm, 65 % of a year's growth — predicts it.

---

## 13. What the enhancements are worth in W m⁻² — Finding 21

Mixing ratios are the measurement; forcing is the currency policy is written in. Applying the standard band expressions — 5.35 ln(*C*/*C*₀) for CO₂, 0.036(√*M* − √*M*₀) for CH₄, with the ~43 % indirect uplift for methane's ozone and stratospheric-water effects:

**Table 92 — instantaneous forcing of each site's regional enhancement over Bariri**

| Station | CO₂ (mW m⁻²) | CH₄ incl. indirect (mW m⁻²) | Total | CH₄ share |
|---|---|---|---|---|
| SRG Sorong | 24.5 | 5.7 | 30.1 | 19 % |
| BKT Bukit Kototabang | 26.2 | 13.0 | 39.2 | 33 % |
| JMB Jambi | 58.7 | 38.1 | 96.7 | **39 %** |
| **KMY Kemayoran** | **131.2** | **53.0** | **184.1** | **29 %** |

**Table 93 — forcing accrual rate implied by the measured growth rates**

| | CO₂ | CH₄ incl. indirect | Total | CH₄ share |
|---|---|---|---|---|
| BKT 2019–2024 | 29.3 | 7.5 | 36.8 mW m⁻² yr⁻¹ | 20 % |
| PLU 2021–2026 | 36.7 | 4.9 | 41.6 mW m⁻² yr⁻¹ | 12 % |
| *global anthropogenic budget, 1750–2019* | *2,160* | *540* | *2,700 mW m⁻²* | *20 %* |

**Jakarta and Jambi are methane-heavy in forcing terms, not just in mixing ratio.** The global budget attributes 20 % of well-mixed greenhouse forcing to methane; Jakarta's local dome runs at 29 % and Jambi's at 39 %, because both sit on large biogenic methane sources whose CO₂ counterparts are modest. For a city or provincial inventory, **methane is a larger share of the local greenhouse burden than the global average would lead you to budget for.**

At 37–42 mW m⁻² yr⁻¹, the two long-record stations agree the regional well-mixed greenhouse forcing is climbing at a rate that would add roughly 0.4 W m⁻² per decade if sustained.

> **Caveat.** These are *local* enhancements, not global-mean forcings; a station-scale mixing-ratio difference does not produce a station-scale top-of-atmosphere flux. Read the table as "the forcing that would result if this enhancement were global", and read the CH₄ *shares* — ratios, and therefore robust to that caveat — as the finding.

### 13.3 Finding 77 — multi-species radiative forcing budget of the Maritime Continent over pristine marine air

Evaluating the instantaneous radiative forcing anomaly of the Maritime Continent regional background (Bukit Kototabang) relative to pristine Southern Hemisphere marine air (Samoa SMO) across all four well-mixed greenhouse gases:

**Table 94 — multi-species radiative forcing anomaly of BKT over Samoa** (from `outputs/t_regional_forcing_budget.csv`)

| Species | Concentration anomaly | Unit | Radiative forcing anomaly (mW m⁻²) | Relative share |
|---|---|---|---|---|
| **CO₂** | **−3.09** | ppm | **−40.50** | cooling offset |
| **CH₄** | **+70.9** | ppb | **+42.04** | **+831 % of net** |
| **N₂O** | **+1.04** | ppb | **+3.44** | **+68 % of net** |
| **SF₆** | **+0.138** | ppt | **+0.08** | **+1.6 % of net** |
| **Total net enhancement** | — | — | **+5.06** | **100 %** |

**The Maritime Continent carries a small net positive radiative forcing enhancement of +5.1 mW m⁻² over pristine marine air, with methane overcoming the regional CO₂ deficit (Figure 20c).** The regional terrestrial photosynthetic drawdown lowers ambient CO₂ by −3.09 ppm (a −40.5 mW m⁻² cooling effect), but extensive tropical wetland, peatland, and agricultural emissions elevate regional methane by +70.9 ppb (a +42.0 mW m⁻² warming effect). Methane thus exerts the dominant greenhouse forcing anomaly across the equatorial archipelago relative to the surrounding oceans.

**The net is a small residual of two large opposing terms, and that is the finding's main limitation.** A ±5 % error in either the CO₂ or the CH₄ term moves the net by ±2 mW m⁻², roughly 40 % of its own value. The *sign* is robust — methane's enhancement exceeds the CO₂ deficit — but the magnitude should be read as "a few mW m⁻²", not as +5.06.

> **Its limits.** Forcing uses the same band expressions as Section 13 — 5.35 ln(*C*/*C*₀) for CO₂ and 0.036(√*M* − √*M*₀) for CH₄ with the 1.43 indirect uplift — so the two tables in this section are on one convention. *An earlier version of this table used a linearised CO₂ term and a CH₄ coefficient of 0.057, an implied uplift of 1.58, and reported a net of +9.72 mW m⁻²; that is superseded here (Section 15.6).* As in Section 13 these are the forcings that would result if the enhancement were global, not local top-of-atmosphere fluxes.

---

## 14. ENSO in a warming ocean — Findings 44 to 47

Every ENSO result in this report so far — the fire seasons of Section 9, the growth-rate sensitivity of Section 12.5, the monsoon onset of Section 9.8 — is keyed to the **Oceanic Niño Index**, the Niño3.4 sea-surface temperature anomaly against a 30-year climatology. That index has a known problem in a warming ocean: as the whole tropical Pacific warms, the absolute anomaly drifts upward for reasons that have nothing to do with ENSO. CPC therefore also publishes the **Relative ONI**, which subtracts the tropical-mean (20 °N–20 °S) SST anomaly and so isolates the ENSO signal from the background warming.

This section asks three questions the report had not asked: what the difference between the two indices measures, which of them better describes what these stations observe, and whether the forcing accrual of Section 13 is consistent with the warming that difference implies.

![Figure 25](figures/f25_roni_warming.png)

**Figure 25 — ENSO in a warming ocean.** (a) The tropical-mean SST anomaly, recovered as ONI − RONI, with Theil–Sen trends over three windows; the rate is not constant. (b) The three seasons in the station era whose ENSO classification depends on which index is used, against the peak daily-median CO that Bukit Kototabang actually recorded. (c) The observed tropical SST warming rate since 2000, beside the rate implied by this network's own measured forcing accrual converted with the AR6 transient climate response. Bars are 95 % confidence intervals.

### 14.1 Finding 44 — the difference between the two indices is a warming measurement

RONI is defined as the Niño3.4 anomaly minus the tropical-mean anomaly. The difference **ONI − RONI is therefore the tropical-mean SST anomaly itself** — a quantity neither index is intended to report, but which falls out of publishing both.

**Table 95 — tropical-mean SST anomaly, recovered as ONI − RONI**

| Window | n months | Trend (°C decade⁻¹) | 95 % CI |
|---|---|---|---|
| 1950–2025 | 912 | **+0.068** | +0.062 to +0.073 |
| 1980–2025 | 552 | **+0.120** | +0.108 to +0.131 |
| 2000–2025 | 312 | **+0.222** | +0.202 to +0.242 |

**The rate has more than tripled across the record, and the three windows do not overlap at 95 %.** Decade means of ONI − RONI run −0.17, −0.09, −0.17, −0.00, −0.11, +0.01, +0.22, +0.44 °C from the 1950s to the 2020s: the tropical ocean spent forty years near its mid-century baseline and has gained roughly half a degree since.

> **This is a lower bound, and the reason is structural.** The ONI's base period is a 30-year climatology that CPC re-centres every five years — a design whose explicit purpose is to remove the long-term trend so that ENSO events remain comparable across decades. Any trend *surviving* in ONI − RONI is the part of the warming that outran the base-period updates. The true tropical SST warming is larger than Table 95 says; how much larger depends on the update schedule, not on the ocean.

### 14.2 Finding 45 — the choice of index changes the ENSO label, and where it did, ONI matched the fires

Over 76 SON seasons the two indices assign a different ENSO class — El Niño, neutral, La Niña at the conventional ±0.5 °C thresholds — in **nine seasons, four of them since 2000**. The disagreement is not random with respect to time: before 1980 every flip is a La Niña that RONI downgrades to neutral; after 2000 the flips run the other way, because the warming term has grown large enough to push a genuinely neutral Niño3.4 across the El Niño threshold.

Three of those flips fall inside the Bukit Kototabang record, and the station is an unusually direct arbiter — the whole point of an ENSO classification in Indonesia is anticipating drought and fire:

**Table 96 — the seasons whose ENSO label depends on the index**

| SON | ONI | class | RONI | class | BKT peak daily-median CO | Days > 1,000 ppb |
|---|---|---|---|---|---|---|
| 2014 | +0.51 | **El Niño** | +0.35 | neutral | **4,063 ppb** | 13 |
| 2017 | −0.44 | neutral | −0.82 | **La Niña** | 321 ppb | 0 |
| 2019 | +0.51 | **El Niño** | +0.15 | neutral | **1,660 ppb** | 1 |

**In all three, the ONI classification matched what the atmosphere did and the RONI classification did not.** 2014 produced the largest single-day CO median in the twenty-four-year record; 2019 produced the second-worst haze season of the station era; 2017 — which RONI would have flagged as La Niña, the wet phase — was an ordinary quiet year, not the wet extreme the label implies.

The mechanism is not mysterious. Fire risk over Sumatra depends on the **zonal SST gradient** that displaces convection eastward off the Maritime Continent, and that gradient responds to how warm the eastern Pacific is in absolute terms, not to how warm it is relative to a tropical mean that includes the warm pool itself. RONI removes part of the signal along with the trend.

> **This is an operational finding, not a scientific preference.** RONI is the better index for the question *"is this ENSO event unusual by the standards of a warming world?"* — that is what it was built for. ONI is the better index for the question *"will Sumatra burn?"* A fire early-warning system keyed to a declared El Niño should stay on ONI; a study of whether ENSO events are intensifying should not.

### 14.3 Finding 46 — as continuous predictors the two indices are nearly interchangeable

The classification changes; the regression barely does. Correlating each index against Bukit Kototabang's annual fire metrics over the twenty years with adequate coverage:

**Table 97 — index skill against the BKT fire metrics (SON, n = 20)**

| Metric | *r* (ONI) | *r* (RONI) | ρ (ONI) | ρ (RONI) | *r* (warming term alone) |
|---|---|---|---|---|---|
| Peak daily median | +0.47 | +0.47 | +0.57 | **+0.63** | −0.03 |
| Days > 1,000 ppb | +0.50 | +0.48 | +0.29 | +0.29 | +0.07 |
| Annual 95th percentile | +0.58 | +0.58 | +0.58 | **+0.64** | −0.07 |
| Annual median | +0.44 | +0.48 | +0.37 | +0.42 | −0.25 |

RONI is modestly better on the rank correlations for the two extreme-value metrics (+0.63 against +0.57 for the peak, +0.64 against +0.58 for the 95th percentile) and the two are indistinguishable on everything else. The same holds elsewhere in the report's ENSO results: for monsoon onset ONI is slightly better (*r* = +0.46 against +0.41), for the CO₂ growth anomaly ONI is slightly better (+0.38 against +0.32), and for the CH₄ and CO growth anomalies RONI is slightly better (−0.52 against −0.50 at 12–13 months, +0.52 against +0.49 at zero lag). **No conclusion in this report changes if the index is swapped.**

**The last column is the informative one.** The warming term on its own — the tropical-mean anomaly that separates the two indices — has *no* correlation with the fire extremes (−0.03 for the peak, +0.07 for days above 1,000 ppb). The one non-trivial entry is the annual **median** at −0.25, the wrong sign for a "warming drives fire" reading and not significant at n = 20.

**This is a null result worth stating plainly: in this record, background tropical warming does not itself produce fire — ENSO variability does.** The warming has moved the mean state by half a degree over the record without leaving a detectable signature in the burning, which is consistent with the fire response being driven by the *interannual redistribution* of convection rather than by absolute temperature. It does not imply the warming is harmless; it implies that twenty years of one station's CO is the wrong instrument for detecting its effect on fire, and that studies claiming such a detection need a longer record or a stronger design than this one.

### 14.4 Finding 47 — the network's own forcing accrual implies the observed warming rate

Section 13 measured the rate at which well-mixed greenhouse forcing is accruing over these stations: **36.8 mW m⁻² yr⁻¹** at Bukit Kototabang (2019–2024) and **41.6 mW m⁻² yr⁻¹** at Bariri (2021–2026), CO₂ plus CH₄ including its indirect effects. That is a forcing. Converting it to a temperature requires exactly one external number — a climate sensitivity — and the appropriate one for a steadily rising forcing is the **transient climate response**, assessed by IPCC AR6 at 1.8 °C per CO₂ doubling (likely range 1.4–2.2 °C). With *F*₂ₓ = 5.35 ln 2 = 3.71 W m⁻², the transient warming per unit forcing is λ = TCR/*F*₂ₓ = 0.485 K (W m⁻²)⁻¹.

**Table 98 — warming rate implied by the measured forcing accrual**

| | Accrual (mW m⁻² yr⁻¹) | Implied warming (°C decade⁻¹) | TCR range 1.4–2.2 |
|---|---|---|---|
| BKT 2019–2024 | 36.8 | **+0.179** | +0.139 to +0.218 |
| PLU 2021–2026 | 41.6 | **+0.202** | +0.157 to +0.247 |
| *observed tropical SST, 2000–2025 (Table 95)* | — | *+0.222* | *+0.202 to +0.242* |

**The two agree.** An SST index computed by CPC from ship and buoy and satellite measurements of the tropical Pacific, and a pair of greenhouse-gas mixing-ratio trends measured at a mountain in Sumatra and a rainforest in Sulawesi, give the same warming rate to within their confidence intervals — with nothing connecting them but one assessed sensitivity and a pair of band-absorption formulae.

**This is the report's only end-to-end closure of the chain from emissions to forcing to temperature**, and it is worth being precise about what it does and does not establish:

- It **does** show that the greenhouse growth these stations measure is quantitatively sufficient to explain the observed tropical warming. Nothing else needs to be invoked.
- It **does not** independently confirm TCR. TCR is an input here, not an output; the test is a consistency check, and it would take a much longer record and a full forcing inventory — aerosols above all — to invert it.
- The agreement is **better than the method deserves**, in the sense that the accrual omits N₂O, the halocarbons, and the aerosol offset, which work in opposite directions and happen to be small relative to the confidence intervals at this precision.

> **What survives the caveats** is the order of magnitude and the sign, and those are not trivial: a station whose absolute CO₂ scale could only be validated against flasks (Section 15.1) nonetheless measures a *rate of change* accurate enough to reproduce the planet's warming rate. Trends are the robust product of a differential network; Section 15 is the record of what happens when the same data are asked for an absolute.

---

# Part V — Corrections, and what the network can detect

## 15. What changed, and why

Two conclusions in earlier drafts of this report were wrong. Both were reached before the NOAA flask record was brought in, both were reached by comparing this network against a published number rather than against a measurement, and both are corrected here rather than quietly removed.

### 15.1 Retracted: a claimed 5–9 ppm network-wide CO₂ scale offset

An earlier draft compared the afternoon median CO₂ at Bariri and Sorong against a published global monthly mean of 427.35 ppm for December 2025, found deficits of 9.3 and 5.2 ppm, judged that a Southern-Hemisphere tropical site should sit only 1–3 ppm below the global mean, and concluded that the network's CO₂ was off-scale by 5–9 ppm — with the recommendation that the data not be used for inversions until an intercomparison was done.

**That conclusion was wrong.** The flask record shows the in-situ CO₂ at Bukit Kototabang agrees with co-located WMO-scale measurements to +0.31 ppm (Section 4.1), and to better than 1 ppm in every year since 2019 (Section 4.2). The error was in the assumed tolerance, not the arithmetic: the Maritime Continent is a genuine regional CO₂ minimum, sitting 5.5 ppm below Mauna Loa and 1.4 ppm below the South Pole in NOAA's own flask data (Section 4.4). The deficits were real; the inference that they were instrumental was not.

**What this shows about method:** a differential network cannot be validated against a single global scalar plus an assumed tolerance. It can only be validated against a co-located measurement on a traceable scale. The recommendation that follows is not "check the calibration" but "keep the flask programme running" — it is the only reason this report can make an absolute statement at all.

### 15.2 Corrected: the equatorial CO₂ seasonal amplitude

An earlier draft reported that equatorial Indonesia's CO₂ seasonal amplitude was "a fifth of Mauna Loa's and close to the South Pole's", and built an argument on it about the tropical biosphere's gross fluxes cancelling year-round. The reference values were quoted: Mauna Loa ~15 ppm, South Pole ~3 ppm.

Measured from the flask network over 2015–2025, **Mauna Loa's amplitude is 6.86 ppm and the South Pole's is 1.28 ppm.** Bukit Kototabang's is 5.53 ppm — **81 % of Mauna Loa's and 4.3× the South Pole's**, the opposite of what the draft claimed (Section 10.4). The corrected picture is more coherent, not less: it agrees with the SF₆ and methane results that these stations sit on the Northern-Hemisphere side of the seasonal gradient.

### 15.3 Strengthened, not changed

Three earlier conclusions survive on better evidence: the time-base correction, now confirmed externally (Section 4.1); the CO background/tail contrast, now measured on the flask record instead of a biased in-situ series (Section 9.6); and the transport interpretation of the methane seasonal cycle, now proven with an inert tracer instead of argued (Section 10.2).

### 15.4 Newly limited

The pre-2019 in-situ CO record is disqualified for trend work (Section 4.3). Nothing else in the report depended on it: the fire analyses use enhancement *ratios*, which are immune to a multiplicative bias.

**And, newly, the confidence intervals on the ENSO growth-rate sensitivities of Section 12.5 were too narrow.** They were computed from 215 monthly values; the series contains about 12 independent ones. Finding 51 in Section 16.1 gives the correction and its scope: the point estimates and the lag structure stand, the intervals roughly quadruple, and the three sensitivities are no longer significant at 95 %. The annual-resolution ENSO results — Findings 33 and 34 — are unaffected.

### 15.5 Findings 42 and 43 — hypotheses this record does not support

Three natural hypotheses can be tested against these data and are not supported. They are recorded because a negative result from a record long enough to settle the question is worth as much as a positive one, and because each would otherwise be re-attempted.

**Table 99 — Natural hypotheses not supported by the record**

| Hypothesis | Test | Result |
|---|---|---|
| **Fire years raise the CO₂ growth rate** measured at the same station | days above 500 ppb vs annual growth | *r* = **−0.29** same year, **−0.06** the next (n = 18) |
| The CO₂ seasonal amplitude is growing at BKT | Theil–Sen on 19 annual amplitudes | +0.15 ppm yr⁻¹, interval spans zero |
| The CH₄ or CO seasonal amplitude is changing | same | both intervals span zero |
| The cross-equatorial reach is changing (DJF) | Theil–Sen on 20 years of the SF₆ NH fraction | +0.022 yr⁻¹, interval spans zero |
| The same, in the SE monsoon (JJA) | same, 19 years | +0.003 yr⁻¹, interval spans zero |
| **Tropical N₂O growth responds to ENSO** | 12-mo N₂O growth vs ONI with Bartlett $n_{\text{eff}}$ | *r* = +0.24, $n_{\text{eff}} = 6.3$, $p = 0.62$ (not significant) |

**Finding 42 is a statement about scale.** Bukit Kototabang records the most extreme regional fire signal in any tropical background series — 28 days above 1,000 ppb in 2015 — and that signal leaves *no detectable trace* in the CO₂ growth rate measured at the same station in the same year. Indonesian fire emissions in an extreme year are of order a few tenths of a Pg C against a global accumulation near 5 Pg C yr⁻¹, and they are mixed globally within months. **A concentration signal that dominates a record locally can be invisible in the budget it feeds** — which is a caution against reading regional records as regional budgets, and the reason Section 12.7 works only for a well-mixed species.

**Finding 43 says the transport regime has been steady.** Twenty years of an inert tracer show no measurable change in how far the Asian winter monsoon pushes Northern-Hemisphere air across the equator, and no change in any seasonal amplitude. Given how much else in these records *is* changing — four accelerating gases, a doubling methane growth rate, a closing CO gradient — the constancy of the transport is a useful control: the trends in Section 12 are changes in emissions, not changes in how the air arrives.

### 15.6 Corrected: six tables did not match the files they cited, and two methods were wrong

An audit of Findings 58–77 against their source CSVs found errors that no gate had been checking for. All are corrected above; they are recorded here because the pattern matters more than the individual numbers.

**Six tables carried values that were not in the file named in their caption.** In four of them — Tables 17, 21, 26 and 42 — the *differences*, standard deviations and *p*-values were right while the *absolute levels* were wrong, typically shifted by a constant. Mauna Loa's mean CO₂ was published as 399.72 ppm against a computed 401.786; Bukit Kototabang's clean CO floor as 75.9 ± 2.8 ppb against 86.3 ± 9.2; the interhemispheric growth asymmetry as −0.072 ± 1.411 ppm yr⁻¹ against +0.103 ± 0.897. Because the differences were internally consistent, nothing looked wrong on the page. **`scripts/check_docs.py` now verifies every table that cites a CSV against that CSV**, and the check is part of `verify_all.sh`.

**Finding 58's uncertainty estimator was wrong, and the first attempt to fix it was wrong too.** The published version divided the *mean* absolute pair difference by √2, understating σ by 20 %. The first correction divided the *standard deviation of the absolute* difference by √2 — which is worse, understating by 40 %, because |d| is a folded variable whose spread is 0.603 σ_d rather than σ_d. The tell was that the "correction" moved CO₂ down (0.149 → 0.099) and CH₄ up (0.716 → 0.840); a genuine change of estimator moves every species the same way.

The estimator now used needs no distributional assumption, because the second moment survives the fold exactly (*d*² ≡ |*d*|²):

$$\sigma_{\text{single}} = \operatorname{RMS}(|d|)/\sqrt2$$

CO₂'s single-flask σ is **0.18 ppm**, not the 0.15 first published or the 0.10 first "corrected". Table 17 now also carries a robust median-based estimator, because CH₄ and N₂O pair differences are heavy-tailed (RMS/mean = 1.54) and their RMS values are inflated by a few bad pairs.

**Finding 69 was described as independently corroborating Finding 59.** It does not: both divide an SF₆ interhemispheric difference by the secular growth rate, and they differ only in which months they average over. One measurement, quoted twice. Figure 20a additionally displayed a hardcoded τ that did not divide the gradient printed beside it; it is now computed.

**Findings 54 and 74 reported different correlations for the same species pairs** without either acknowledging the other. Both are right for their own timescale — unsmoothed against 7-month-smoothed — and Section 12.13 now says so and gives the effective sample sizes, which are 7–10 rather than 214.

**A second pass audited the physics of Findings 58–77, not just their numbers, and changed three more.**

**Finding 70 is retracted and reported as not supported.** The claimed eastward propagation of the CH₄ seasonal crest is not monotonic once Kemayoran is included, rests on stations with one to four complete years, and is smaller than the year-to-year scatter of Bukit Kototabang's own peak month (circular s.d. 1.2 months). The quoted phase speed was also internally inconsistent: 15.5° per month is 57 km day⁻¹, not the 40 km day⁻¹ quoted beside it.

**Finding 77's radiative forcing was overstated by 48 %.** The calculation used a linearised CO₂ term and a CH₄ coefficient of 0.057 — an implied indirect uplift of 1.58 against the 1.43 documented in Section 13 — so the two forcing tables in the same section were on different conventions. On Section 13's own expressions the net is **+5.1 mW m⁻², not +9.72**. The sign and the conclusion (methane outweighs the CO₂ deficit) are unchanged.

**Two results were stated more strongly than the record supports.** Finding 75's flat CO floor is a detection limit, not a measured zero — Finding 52 gives this site a 15.5-year detection time for CO. Finding 60's N₂O vertical difference of 0.064 ppb is significant only because *n* = 241; it is smaller than the single-flask reproducibility and should be read as no resolvable gradient.

**Findings 59–63, 65–69 and 71–76 were checked and stand as written**, with uncertainties added to Finding 72 (the tropical methane increment is +5.1 [+0.7, +9.2] ppb; the northern one is not significant) and wording tightened in Findings 63 and 66.

> **What generalises.** Every one of these passed a reader's eye because the internally checkable quantities were right. The lesson is the one Section 15.1 already records in another form: **agreement within a table is not evidence that the table matches the data it came from.** The only defence is a mechanical check against the source file, which now exists.

### 15.7 Corrected: the fire return periods, in a table that cited no file

The Gumbel return periods in Section 9.8 were wrong in every row, and the count of annual maxima above them was wrong too.

**Table 100 — Corrected Gumbel return levels for daily carbon monoxide**

| Level | Published | Correct | 
|---|---|---|
| 500 ppb | 1.4 yr | **1.67 yr** |
| 1,000 ppb | 2.8 yr | **2.54 yr** |
| 2,000 ppb | 8.8 yr | **7.21 yr** |
| The 2014 peak | ~120 yr | **81.31 yr** |

The fitted parameters quoted beside the table — location 426 ppb, scale 828 ppb — were right, and they reproduce the correct column exactly: at 1,000 ppb, $p = \exp(-\exp(-(1000-425.8)/828)) = 0.6066$ and $1/(1-p) = 2.54$. The number of annual maxima was given as 24; the fit uses the 20 years that clear the 250-valid-day completeness gate.

Two things about *how* this survived are worth more than the numbers.

**It was found by a use, not by a check.** Finding 98 needed a return period to compute reversal risk over a crediting period, read it from `outputs/u_return.csv`, and the value did not match the report. No gate had ever compared them.

**The table cited no CSV, so `check_sourced_tables` could not see it** — the exact failure mode recorded in the landmines after the Table 58 incident. Every table added in this pass cites its source file, and this one now does too.

> **What generalises.** A wrong number derived from *correct* published parameters is the hardest kind to see, because the derivation is checkable and nobody checks it. The two defences that would have caught it are both mechanical: cite the CSV in every caption, and re-derive quoted intermediate results rather than transcribing them.

---

## 16. What this network can and cannot detect — Findings 51 to 53, 65

Three questions a station manager has and this report had not answered: how many independent observations a long correlation actually contains, how long a record must run before its own trend is real, and how much a discrete sampling programme gives up against a continuous one. All three are properties of the instrument rather than of the atmosphere, and two of them revise claims made earlier in this report.

![Figure 26](figures/f26_detection.png)

**Figure 26 — what this network can and cannot detect.** (a) Years of record needed before each species' trend is distinguishable from its own noise, against the 21-year length of the flask record. (b) Error in the monthly mean when the continuous afternoon record is subsampled at flask frequencies, with the spread across sampling phases. (c) Nominal sample size against effective sample size for six of the report's own correlations.

### 16.1 Finding 51 — most of *n* is not there

A correlation between two autocorrelated series has fewer independent observations than it has data points. Bartlett's correction, *n*<sub>eff</sub> = *n*(1 − *r*₁*r*₂)/(1 + *r*₁*r*₂), applied to the report's own results:

**Table 101 — nominal against effective sample size**

| Test | *r* | *n* | *n*<sub>eff</sub> | CI as reported | CI corrected | *p* corrected |
|---|---|---|---|---|---|---|
| CO₂ growth vs ONI, lag 0 | +0.38 | 215 | **12.3** | ±0.27 | **±1.22** | 0.21 |
| CH₄ growth vs ONI, lag 12 | −0.50 | 215 | **10.9** | ±2.50 | **±12.20** | 0.12 |
| CO growth vs ONI, lag 0 | +0.49 | 215 | **13.0** | ±7.55 | **±33.22** | 0.086 |
| SON ONI vs annual peak CO | +0.48 | 20 | 21.6 | — | — | **0.027** |
| SON ONI vs days > 1,000 ppb | +0.50 | 20 | 21.4 | — | — | **0.019** |
| SON ONI vs monsoon onset | +0.49 | 20 | 19.6 | — | — | **0.031** |

**The monthly ENSO sensitivities of Section 12.5 have about twelve independent observations, not 215.** The growth rate there is built from a 7-month-smoothed series and correlated against an index that is itself a 3-month running mean; both are smooth by construction, with lag-1 autocorrelations of 0.92 and 0.97. Twelve is not an arbitrary number: **it is roughly the number of ENSO events in a 22-year record**, which is the correct answer to "how many times have we seen this happen".

With the corrected intervals, none of the three sensitivities is significant at 95 %. What survives is unchanged and still worth having: the point estimates, the ordering of the species, and above all the **lag structure** — CO₂ and CO responding at zero lag and methane at twelve to thirteen months — which is a statement about *timing* that does not depend on the width of a confidence interval.

**The annual results are unaffected, and that contrast is the useful part.** The fire and monsoon findings use one value per year; those series have lag-1 autocorrelations near zero, so *n*<sub>eff</sub> ≈ *n* and their *p*-values barely move. **Aggregating to the timescale of the phenomenon is what makes an interval honest**, and a monthly series correlated against ENSO is not twenty times more informative than an annual one — it is the same information, resampled.

### 16.2 Finding 52 — how long before a trend is real

Weatherhead's expression gives the record length at which a trend emerges from its own noise, given the residual scatter about a fitted trend-plus-seasonal model and the residual autocorrelation:

**Table 102 — years of record needed to detect the observed trend**

| Species | Trend | Residual σ | φ | Years needed |
|---|---|---|---|---|
| SF₆ | +0.33 ppt yr⁻¹ | 0.07 | 0.25 | **0.4** |
| N₂O | +0.99 ppb yr⁻¹ | 0.34 | 0.47 | **0.7** |
| CO₂ | +2.33 ppm yr⁻¹ | 2.95 | 0.26 | **1.4** |
| CH₄ | +8.04 ppb yr⁻¹ | 21.5 | 0.27 | **2.2** |
| **CO** | −1.66 ppb yr⁻¹ | 63.2 | 0.48 | **15.5** |

**Carbon monoxide needs thirty-eight times as long as sulphur hexafluoride.** The reason is entirely the noise, not the trend: CO's residual scatter is 63 ppb against a signal of 1.7 ppb yr⁻¹, because the site is downwind of a fire regime that produces enormous episodic excursions. SF₆ has no local source at all, so its record is almost pure trend.

Two consequences follow directly. **The 21-year flask record is the only thing in this project long enough to give a CO trend** — which is why Finding 15 had to come from the flasks and could not come from the in-situ record even if the pre-2019 bias were repaired. And **the four stations that began in 2021–2023 cannot produce a defensible CO trend before about 2036**, whatever else they deliver in the meantime. Their CO₂ and CH₄ trends, by contrast, are already within reach.

### 16.3 Finding 53 — what discrete sampling costs

Subsampling Bukit Kototabang's continuous afternoon record at flask frequencies — one afternoon hour every 7, 14 or 30 days — and rebuilding the monthly mean from those samples:

**Table 103 — Monthly-mean reconstruction error by sampling frequency**

| Sampling interval | Error in the monthly mean | Spread across phases |
|---|---|---|
| Weekly | **1.51 ppm** | ±0.12 |
| Fortnightly | 2.10 ppm | ±0.24 |
| Monthly | 2.94 ppm | ±0.27 |

**A weekly flask programme reconstructs the monthly mean to about 1.5 ppm** — which is 65 % of one year's growth, and larger than the entire mean difference between Bukit Kototabang and the South Pole. Halving the sampling rate costs about 0.6 ppm; halving it again costs another 0.8.

This is not an argument against flasks — Section 15.1 is the argument *for* them, and no continuous analyser in this network can make an absolute statement without one. It is an argument about **what each instrument is for**. The flasks supply the calibration anchor and the species the analysers do not measure; the continuous record supplies the monthly mean, the diurnal cycle, the nocturnal budget and the rectifier of Section 4.6. Neither substitutes for the other, and the 1.5 ppm is the price of pretending it does.

### 16.4 Finding 65 — tropical N₂O growth shows no significant ENSO response once serial autocorrelation is removed

Section 12.5 and Section 16.1 evaluated ENSO sensitivities for CO₂, CH₄, and CO. Applying the same Bartlett effective sample size framework to the 22-year flask record of nitrous oxide (N₂O):

A nominal correlation between the 12-month difference of the 7-month running mean N₂O growth anomaly and ONI yields $r = +0.245$ ($p_{\text{nominal}} = 0.0003$, $n = 215$ months). However, both smoothed series exhibit severe lag-1 autocorrelation ($r_1 = 0.971$, $r_2 = 0.973$). 

Applying Bartlett's formula reduces the effective sample size to $n_{\text{eff}} = 6.3$. On $n_{\text{eff}} - 2 = 4.3$ degrees of freedom, the effective two-sided $p$-value is **$p = 0.625$ (not significant)**. 

**Tropical N₂O growth at Bukit Kototabang exhibits no statistically significant response to ENSO variability once autocorrelation is removed.** This negative result complements Finding 55: tropical N₂O emissions are governed by baseline agricultural soil processes rather than ENSO-driven fire and drought pulses.

> **Its limits.** The null result applies to the basin-scale interannual ENSO mode; extreme local droughts may still induce short-lived soil denitrification pulses that are diluted at regional scale.

### 16.5 Finding 88 — how large a step change the record could see at all

Finding 52 answers "how long until a trend is real". The complementary question — and the one an accounting system asks first — is "how large a change could this record see, over the period I have". A two-sided test at 95 % with 80 % power, comparing two adjacent windows of *n* months on a series with lag-1 autocorrelation φ, resolves a step of

$$\delta = (1.96 + 0.84)\,\sigma\sqrt{2/n_{\text{eff}}}, \qquad n_{\text{eff}} = n\,\frac{1-\varphi}{1+\varphi}$$

The effective sample size is doing most of the work, and Finding 51 is why it is there: twelve monthly values with φ = 0.65 are worth 2.5 independent ones.

**Table 104 — detectable step change at Bukit Kototabang, over 12 and 60 months** (from `outputs/p_detect_co2e.csv`):

| Species | φ | *n*<sub>eff</sub> (12 mo) | Step, 12 mo | Step, 60 mo | Step in CO₂e (ppm), 12 / 60 mo |
|---|---|---|---|---|---|
| CO₂ | 0.650 | 2.5 | **6.1042 ppm** | **2.7299 ppm** | 6.1042 / 2.7299 |
| CH₄ | 0.709 | 2.0 | 39.8394 ppb | 17.8167 ppb | 0.4051 / 0.1812 |
| CO | 0.735 | 1.8 | 58.2726 ppb | 26.0603 ppb | no GWP |
| N₂O | 0.853 | 1.0 | 1.1417 ppb | 0.5106 ppb | 0.3117 / 0.1394 |
| SF₆ | 0.789 | 1.4 | 0.1784 ppt | 0.0798 ppt | 0.0149 / 0.0067 |
| H₂ | 0.679 | 2.3 | 13.7511 ppb | 6.1497 ppb | no GWP |

**Over one year this record cannot see a change smaller than two and a half years' worth of CO₂ growth.** Over five it comes down to 2.73 ppm, still larger than one year's growth. The CO₂-equivalent column makes the six comparable, and the ordering it produces is the useful one: **the network is most sensitive, in accounting terms, to SF₆ and least to CO₂** — by a factor of 400.

That is not a paradox. SF₆ has a GWP of 25,200 and a residual scatter of 0.054 ppt, so a climatically meaningful quantity of it is easy to see; CO₂ has a GWP of 1 and a scatter of 2.458 ppm. A monitoring network optimised to detect changes in *forcing* would look nothing like one optimised to detect changes in *carbon*, and this is the table that shows the difference.

> **What the number is not.** This is the detectability of a step in the *regional background* at one site. It is not the detectability of a change in a nearby source, which is a much easier target and is what Finding 93 computes. It also assumes the noise is stationary; a step accompanied by a change in variance would be easier or harder to see than this.

### 16.6 Finding 89 — the reference site is stationary, but not tightly

A station used as a reference for accounting has to be stationary in whatever property the accounting depends on. For anything that removes a seasonal cycle before comparing — which is most of Part IV — that property is the seasonal amplitude.

**Table 105 — year-by-year seasonal amplitude at Bukit Kototabang, flask record** (from `outputs/p_amplitude_stability.csv`):

| Species | Years | Mean amplitude | s.d. | Coefficient of variation | Theil–Sen trend | 95 % CI | Significant |
|---|---|---|---|---|---|---|---|
| CO₂ | 19 | 6.66 ppm | 2.11 | **31.6 %** | 0.1150 ppm yr⁻¹ | −0.0717 – 0.2580 | no |
| CH₄ | 19 | 75.90 ppb | 14.02 | 18.5 % | 0.0694 ppb yr⁻¹ | −1.1283 – 1.1214 | no |

Neither amplitude trends, which is Finding 43 seen from the other side — **and the two are the same test, not independent confirmation of each other.** What this adds is the scatter, which Finding 43 does not report and which is the number a user needs: the CO₂ amplitude varies by a third of itself from year to year.

The consequence is practical. A single year's seasonal cycle at this site is not a climatology. Anything that subtracts one — a phase estimate, an amplitude comparison, a detrended anomaly — inherits a 32 % uncertainty unless it averages several years, and Finding 70 was retracted for precisely this reason.

> **A caveat on the estimator.** Amplitude here is the plain within-year maximum minus minimum of NOAA's monthly means, taken only over years with all twelve months. That is noisier than the harmonic-fit amplitude used in Section 10.4 and will read slightly higher, because a single noisy month can set either extreme. The two should not be compared directly; 6.66 here and 6.86 there are the same quantity measured two ways.

---

# Part VI — The carbon economic value (*Nilai Ekonomi Karbon*)

## 17. What this network is worth to a carbon-pricing system — Findings 90 to 100

### 17.1 The framework, and what it needs

*Nilai Ekonomi Karbon* — the carbon economic value — is the framework established by **Presidential Regulation 98 of 2021** for pricing greenhouse-gas emissions in Indonesia, in service of the national contribution under the Paris Agreement. It has four instruments:

- **Carbon trading** (*perdagangan karbon*) — an intensity-based allowance system for regulated installations, currently the power sector, plus a market in offsets. Since September 2023 units trade on **IDXCarbon**, the exchange operated by the Indonesia Stock Exchange.
- **Performance-based payment** (*pembayaran berbasis kinerja*) — results-based finance, the mechanism through which forest and peatland results are paid for.
- **The carbon levy** (*pungutan atas karbon*) — a carbon tax, legislated in **Law 7 of 2021** at a floor of IDR 30 per kg CO₂-equivalent, or IDR 30,000 per tonne, and repeatedly deferred.
- **Other mechanisms**, left open by the regulation.

All four settle on the same object: a number of tonnes of CO₂-equivalent, reported through the national registry (SRN PPI) and verified by an accredited body against a documented process. **That chain is an inventory chain, not an atmospheric one.** It multiplies activity data by an emission factor; it does not ask the air. Nothing in this report is part of it, and this section does not claim otherwise.

What an atmospheric record can do is answer three questions *about* such a system, and the answers are measurements rather than opinions:

1. **What is a measured signal worth** if it were priced at the prices these instruments actually use? — Findings 90, 91, 92.
2. **What size of change could the network verify independently**, over what period, and at which sites? — Findings 93, 94, 95.
3. **Where does the uncertainty in a monetised claim really come from, and what can this network not do at all?** — Findings 96 to 100.

The third group is the one worth reading. Two of its five results are negative.

> **Every price and policy figure in this section is quoted, not measured**, and each is listed in Appendix C with its source. The prices used are the statutory carbon-tax floor (IDR 30,000 tCO₂e⁻¹), the IDXCarbon volume-weighted average for June 2024 – May 2025 (IDR 52,295), the IDXCarbon opening price of 26 September 2023 (IDR 69,600), and the EU ETS average for April 2026 (EUR 72, converted at IDR 18,900) as a contrast. Currency conversion uses IDR 16,300 to the US dollar. **These move; the measurements do not.**

### 17.2 Finding 90 — the peat, priced

Finding 32 measures the drained-peat excess at Jambi against the intact-forest reference at Bariri: **16.70 t C ha⁻¹ yr⁻¹**, from the difference of two nocturnal budgets. That is an atmospheric measurement of a carbon loss, made from a hilltop, on quiet nights, without waiting for a fire. Converting it is stoichiometry.

**Table 106 — Jambi's measured peat carbon loss, converted and priced** (from `outputs/k_jambi_value.csv`):

| Step | Value | Unit |
|---|---|---|
| Measured excess respiration (Jambi − Bariri) | **16.70** | t C ha⁻¹ yr⁻¹ |
| As carbon dioxide mass | **61.18** | t CO₂ ha⁻¹ yr⁻¹ |
| At the carbon-tax floor, IDR 30,000 | **1.84** | IDR million ha⁻¹ yr⁻¹ |
| At the IDXCarbon average, IDR 52,295 | **3.20** | IDR million ha⁻¹ yr⁻¹ |
| At the IDXCarbon opening price, IDR 69,600 | **4.26** | IDR million ha⁻¹ yr⁻¹ |
| At the EU ETS April 2026 price | 83.25 | IDR million ha⁻¹ yr⁻¹ |

At the traded Indonesian price this is **about IDR 3.2 million, or US$196, per hectare per year** — a number small enough to be worth stating beside the alternative land use, and large enough that a peat dome of a few thousand hectares reaches the tens of billions of rupiah annually.

The three steps are kept separate in the table deliberately. The first is a measurement with a confidence interval; the second is exact; the third is a policy price that moves by a factor of 2.3 across instruments in use in the same country in the same year, and by a factor of 45 against Europe. **Collapsing them into a single currency figure is what makes monetised atmospheric claims unfalsifiable**, and Finding 96 takes the decomposition further.

> **What it is not.** This is a *gross* emission rate measured against one reference site, not a creditable abatement. A credit requires a counterfactual baseline, a project boundary, additionality, and the inventory-side accounting of Section 17.1 — none of which an atmospheric measurement supplies. What the measurement supplies is a physical check that the inventory's peat emission factor is in the right range at this location.

### 17.3 Finding 91 — Jakarta's methane, and why a ceilometer is worth more than price discovery

Finding 10 gives Jakarta's nocturnal methane flux for an assumed nocturnal layer depth. The depth is assumed, not measured, so all three depths are carried through to money rather than one being chosen.

**Table 107 — Jakarta's nocturnal methane flux over a 10³ km² footprint, priced** (from `outputs/k_jakarta_ch4_value.csv`):

| Assumed layer depth | Flux (g CH₄ m⁻² yr⁻¹) | t CH₄ yr⁻¹ | ktCO₂e yr⁻¹ | At IDXCarbon average (IDR million yr⁻¹) |
|---|---|---|---|---|
| 100 m | 32.7 | 32663.0 | 911.3 | 47656.43 |
| **200 m** | **65.3** | **65325.0** | **1822.6** | **95312.87** |
| 400 m | 130.7 | 130651.0 | 3645.2 | 190625.73 |

At the middle depth the city's background methane emission is **1.8 MtCO₂e per year, worth about IDR 95 billion (US$5.8 million) annually at the traded price** — and this is the diffuse background of the urban surface, not a hotspot.

The comparison that matters is between the two uncertainties. **The unmeasured layer depth spans a factor of four. Every carbon price in Indonesian use spans a factor of 2.3.** The instrument that would halve the uncertainty in this number is a ceilometer at Kemayoran, costing rather less than a year of the emission's traded value; no amount of price discovery will do it. Section 18 asks for that instrument — a ceilometer or routine radiosonde at Jambi and Kemayoran — on scientific grounds. This is the same request with a figure attached.

> **The footprint is a convention.** 10³ km² is the value used in Section 7.3 and is of the order of Jakarta's built area; it is not a measured footprint, and the totals scale linearly with it. The flux density per square metre is the measured quantity and the only one that should be compared with an inventory.

### 17.4 Finding 92 — the atmosphere splits the city between two administrations

Under NEK a tonne is administered before it is traded: energy and transport sit with the energy ministry, waste and land use with the environment ministry and the city government. The split is an inventory exercise. The atmosphere performs it independently, from two bounds this report has already established.

**Table 108 — Kemayoran's measured CO₂-equivalent enhancement, partitioned by the two atmospheric bounds** (from `outputs/k_jakarta_fossil.csv`):

| Component | CO₂e (ppm) | Bound | NEK sector |
|---|---|---|---|
| CO₂, fossil | **6.50** | upper bound (≤ 63 % of CO₂, Section 6.4) | Energy / transport |
| CO₂, non-fossil | **3.82** | lower bound (≥ 37 % of CO₂) | Waste / land use |
| CH₄ as CO₂e, non-combustion | **0.91** | lower bound (≥ 97 % of CH₄, Section 7.1) | Waste |
| CH₄ as CO₂e, combustion | 0.03 | upper bound (≤ 3 % of CH₄) | Energy / transport |
| **Total measured enhancement over Bariri** | **11.26** | | |

**At most 57.7 % of Jakarta's measured climate-relevant enhancement is fossil.** At least 4.73 ppm CO₂e — 42 % — belongs to the waste and land-use side of the ledger, and 0.91 ppm of that is methane from a source that is not combustion.

This is the kind of statement an atmospheric network is uniquely able to make, and it is worth being precise about why. An inventory arrives at a sectoral split by adding up what it believes each sector does. The measurement arrives at it from the composition of the air, with no activity data at all, and the two are wrong in unrelated ways. Where they disagree, something is missing from one of them; where they agree, the agreement means something.

> **Both entries are bounds, and they point the same way.** The fossil share is an upper bound and the waste share a lower one, so the true split is *more* weighted to waste than the table shows. Neither bound is tight, and the partition should be read as "the waste side is at least two-fifths of this city's measured enhancement", not as a set of point estimates.

### 17.5 Finding 93 — the smallest abatement the network could independently verify

Finding 88 gives the step change detectable in the regional background. A mitigation project does not change the background; it changes the *enhancement* at a station near it, which is a far easier target. Dividing one by the other gives the fractional cut in a site's own local source that the site could resolve.

**Table 109 — verifiable fractional abatement, by station and observing period** (from `outputs/k_detect_abatement.csv`):

| Station | Enhancement (ppm CO₂e) | Detectable step, 12 mo | Cut needed, 12 mo | Detectable step, 60 mo | Cut needed, 60 mo |
|---|---|---|---|---|---|
| KMY Kemayoran | 11.26 | 6.10 ppm | **54 %** | 2.73 ppm | **24 %** |
| JMB Jambi | 5.26 | 6.10 ppm | 116 % | 2.73 ppm | **52 %** |
| BKT Bukit Kototabang | 2.27 | 6.10 ppm | 269 % | 2.73 ppm | 120 % |
| SRG Sorong | 2.01 | 6.10 ppm | 304 % | 2.73 ppm | 136 % |

![Figure 27](figures/f27_nek_detectability.png)

**Figure 27 — what the network can verify, at two scales.** (a) Each station's measured CO₂-equivalent enhancement over Bariri against the detectable step over 12 and 60 months, labelled with the fractional cut a five-year record could resolve. (b) The regional signal produced by the full width of Indonesia's 2035 NDC range, across boundary-layer depths and ventilation timescales, against the same 5-year detection threshold (Finding 100).

A figure above 100 % means the station could not verify the *total elimination* of its own local source, let alone a partial abatement of it.

**Only Kemayoran can verify anything within a year, and only a halving.** Over five years Kemayoran reaches a quarter and Jambi a half. Bukit Kototabang and Sorong cannot verify the disappearance of their entire local signal on either timescale — which is not a criticism of those stations, because neither exists to monitor a source. It is a statement about where in this network an emission-reduction claim could be checked against the air: **in a city, and in a peatland, over five years, for changes of a quarter to a half.**

That is a real capability and a narrow one. It is far short of what a project developer would want and far beyond what an inventory alone can offer.

> **The comparison is generous to the network.** It assumes the abatement is the only thing that changes, that the enhancement is stable in the absence of intervention, and that the detection statistic of Finding 88 — derived for the background at Bukit Kototabang — carries to an enhancement at another site. Each of those makes the true threshold higher, not lower.

### 17.6 Finding 94 — the rectifier is a systematic bias on flux-based crediting, and it is larger than the credit

Finding 49 measures the diurnal rectifier — the 24-hour mean minus the afternoon mean — at +8.3 to +18.3 ppm across the five stations. Flasks, satellites and afternoon-selected inversions all see the afternoon value. Anything that infers a surface flux from afternoon-sampled concentrations therefore starts from air that is systematically depleted relative to the daily mean over the site.

**Table 110 — the rectifier against the enhancement it would bias** (from `outputs/k_rectifier_bias.csv`):

| Station | Days | Rectifier (ppm) | Seasonal range | Enhancement (ppm CO₂e) | Bias as % of enhancement |
|---|---|---|---|---|---|
| JMB Jambi | 605 | **18.31** | 7.78 | 5.26 | **348 %** |
| PLU Bariri | 1394 | 16.96 | 4.25 | — | reference site |
| KMY Kemayoran | 691 | 11.30 | 6.34 | 11.26 | **100 %** |
| BKT Bukit Kototabang | 2857 | 10.81 | 2.15 | 2.27 | **476 %** |
| SRG Sorong | 592 | 8.30 | 6.35 | 2.01 | 413 %  |

**At every station the sampling bias exceeds or equals the entire signal being measured.** At Kemayoran it is exactly the size of the city's enhancement; at Bukit Kototabang it is nearly five times it.

The property that makes this dangerous rather than merely large is that **it does not average out.** Random error shrinks as $1/\sqrt{n}$; a fixed-sign bias does not shrink at all. Ten years of afternoon flasks are as biased as one.

Two qualifications keep it from being an indictment. First, this bias is largely *common* to all sites — the seasonal range column shows it varies by only 2.15 ppm through the year at Bukit Kototabang — so a *difference* between two afternoon-sampled sites, which is what Finding 78's ladder and most of Part III are built from, is far less affected than an absolute flux inference would be. Second, inversion systems that assimilate afternoon data are not naive about this; the point here is the magnitude, measured at these particular sites, which is larger than a reader of Part IV would guess.

> **What follows for NEK.** Any crediting methodology that converts a measured concentration into a flux — as opposed to comparing two concentrations — needs a rectifier correction derived at that site, from continuous data. Only continuous stations can supply it. This is an argument for hourly monitoring that has nothing to do with precision and everything to do with sampling.

### 17.7 Finding 95 — which station can do which job

A station's fitness for a carbon-accounting role is a measurable property, and it is not the same as its designation. Three measured quantities decide it: the span of the record, the data return within it, and the size of the signal there is to measure.

**Table 111 — station fitness for a role under NEK, scored from the data** (from `outputs/k_station_roles.csv`):

| Station | Years with CO₂ > 50 % return | Record span | Median return | Enhancement (ppm CO₂e) | Role the data support |
|---|---|---|---|---|---|
| BKT Bukit Kototabang | 9 | 15 yr | 96.4 % | 2.27 | Baseline anchor (regional reference) |
| PLU Bariri | 6 | 6 yr | 82.3 % | — | Clean reference — the zero of the ladder |
| KMY Kemayoran | 3 | 3 yr | 95.0 % | 11.26 | Source monitoring, project or city scale |
| JMB Jambi | 3 | 3 yr | 74.9 % | 5.26 | Not yet fit on data return |
| SRG Sorong | 4 | 5 yr | 58.5 % | 2.01 | Not yet fit on data return |

The thresholds are stated in the script so the assignment can be argued with: a span of ten years for a trend role, 80 % median return, and 4 ppm CO₂e for a source-monitoring signal.

**The result that matters is Jambi's.** It carries the most scientifically valuable signal in the network — a measured, monetisable, policy-relevant peatland carbon loss — and it is the station least able to support an annual statement, at 74.9 % median return. Nothing about the site or the instrument prevents this; it is a data-return problem, and data-return problems are solved with maintenance budgets.

> **A role is not a ranking.** Bariri returns less than Kemayoran and is the more valuable station, because a network's reference site is what every other number is measured against. The table assigns roles, not merit.

### 17.8 Finding 96 — the uncertainty in a monetised claim is not in the measurement

Take the Jambi peat claim of Finding 90 and ask where its uncertainty comes from. Each term is expressed as the multiplicative span it contributes — the high case over the low case — so the terms are comparable and the total is their product.

**Table 112 — uncertainty budget of a monetised peat claim at Jambi** (from `outputs/k_uncertainty.csv`):

| Term | Low | High | Unit | Span | Status |
|---|---|---|---|---|---|
| Nocturnal layer depth | 100.0 | 400.0 | m | **4.00** | assumed |
| Peat store depth (crediting horizon) | 60.0 | 180.0 | yr | **3.00** | assumed |
| Carbon price in Indonesian use | 30000.0 | 69600.0 | IDR tCO₂e⁻¹ | **2.32** | policy |
| Nocturnal accumulation rate (bootstrap 95 % CI) | 2.986 | 3.511 | ppm h⁻¹ | **1.18** | measured |
| **Product of all terms** | | | | **32.9** | |

![Figure 28](figures/f28_nek_value.png)

**Figure 28 — what a measured signal is worth, and where its uncertainty comes from.** (a) Jambi's measured peat carbon loss priced at four carbon prices, on a log axis because the EU ETS contrast is twenty-six times the Indonesian traded price. (b) The uncertainty budget of that claim as multiplicative spans, coloured by whether the term is measured, assumed or set by policy. (c) Jakarta's methane value against the assumed nocturnal layer depth — the factor of four that no price discovery can remove.

**The atmospheric measurement is the best-constrained term in the chain, by a factor of three over the next best.** The three terms that dominate are two assumptions and a policy price.

This inverts the intuition that atmospheric monitoring is the uncertain part of a carbon claim. The measurement of how fast carbon dioxide accumulates over Jambi at night is good to ±8 %. What is not known is how deep the air was that it accumulated in, how much carbon is in the ground beneath, and what a tonne is worth — and only the first of those is a measurement problem at all.

> **The product is not a confidence interval.** Multiplying four spans assumes the worst case of each coincides, which is not a probability statement, and the terms are not independent — a deeper layer implies a different flux, not merely a larger one. The table is an ordering of terms, and the ordering is what it is for.

### 17.9 Finding 97 — the liability outlives the contract

An avoided-emissions credit at Jambi would be issued annually against the loss that rewetting prevents. The store the loss draws on empties on an e-folding time of 60 to 180 years (Finding 32). A crediting period is 10 to 50.

**Table 113 — how much of the peat store a crediting period covers** (from `outputs/k_permanence.csv`):

| Store (t C ha⁻¹) | e-folding (yr) | Crediting period | Store lost | Credited (t CO₂ ha⁻¹) | Store remaining (t CO₂ ha⁻¹) |
|---|---|---|---|---|---|
| 1000.0 | 60.0 | 10 yr | 15.4 % | 612.0 | 3101.0 |
| 1000.0 | 60.0 | 25 yr | **34.1 %** | 1530.0 | 2414.0 |
| 1000.0 | 60.0 | 50 yr | 56.6 % | 3059.0 | 1590.0 |
| 3000.0 | 180.0 | 10 yr | 5.4 % | 612.0 | 10397.0 |
| 3000.0 | 180.0 | 25 yr | 13.0 % | 1530.0 | 9565.0 |
| 3000.0 | 180.0 | 50 yr | 24.3 % | 3059.0 | 8322.0 |

For the shallowest plausible store, **a standard 25-year crediting period covers a third of the reservoir**; for the deepest, an eighth. Either way the contract ends with most of the carbon still in the ground and still draining, at a rate this network can measure.

The usual reading of a long e-folding time is reassurance: the store is large, the loss is slow. The accounting reading is the opposite. **A drained peat dome is a liability that outlives every contractual instrument available to price it**, and the years after the crediting period — when the payments stop and the drainage does not — are outside the boundary of every methodology.

> **Depths are quoted, not measured.** The 1,000–3,000 t C ha⁻¹ range is a literature value for tropical peat (Appendix C); this project has no peat-depth measurement at Jambi. The measured quantity is the loss *rate*. Everything in the table is that rate applied to an assumed store.

### 17.10 Finding 98 — reversal risk, measured rather than assumed

Every land-based credit carries reversal risk: the carbon comes back out. In Indonesia the mechanism is fire, and this record measures how often it happens.

Section 9.8 fits a Gumbel distribution to the annual maxima of daily-median CO at Bukit Kototabang and gives a 1,000 ppb day a return period of **2.54 years** (corrected in Section 15.7). Treating years as independent, the chance of at least one such year inside a crediting period of *n* years is $1 - (1 - 1/T)^n$.

**Table 114 — probability of an extreme fire year within a crediting period** (from `outputs/k_fire_reversal.csv`):

| Crediting period | P(at least one 1,000 ppb day-year) | Expected events |
|---|---|---|
| 5 yr | **91.8 %** | 1.97 |
| 10 yr | 99.3 % | 3.93 |
| 25 yr | 100.0 % | 9.83 |
| 40 yr | 100.0 % | 15.74 |

**Over any crediting period longer than a few years, an extreme fire season is not a risk to be provisioned against — it is a certainty to be planned for.** A 25-year project should expect ten of them.

The independence assumption makes this an *optimistic* figure in the way that matters. Section 9.3 shows the extremes cluster with El Niño, so the events arrive in groups; a buffer pool sized for ten independent events spread evenly across 25 years is not sized for three El Niños delivering three each.

> **What the indicator is, and is not.** A day above 1,000 ppb of CO at Bukit Kototabang is a regional smoke indicator for Sumatra, not a measurement of whether a particular hectare burned. It bounds the frequency of the conditions under which reversal happens, which is the input a buffer pool needs; it does not predict a specific project's loss.

### 17.11 Finding 99 — what each mode of measurement actually verifies

"Atmospheric monitoring supports MRV" is the kind of sentence that survives review and commits to nothing. Each row below is a mode of measurement this project has actually used, the claim it can support, and the number that bounds it.

**Table 115 — verification modes and their limits** (from `outputs/k_mrv_tiers.csv`):

| Mode | What it verifies | Number | Finding |
|---|---|---|---|
| Co-located flask vs in-situ, levels | that a station's scale is not drifting | **0.31** ppm | 3 |
| Co-located flask vs in-situ, growth | that a trend is not an instrument artefact | **0.81** ppm yr⁻¹ | 83 |
| Continuous in-situ, 5-year window | a step change in the regional background | **2.73** ppm CO₂e | 88 |
| Nocturnal ratio (depth cancels) | the methane share of a site's CO₂e per unit carbon | **17.2** % at Kemayoran | 85 |
| Diurnal rectifier sign test | that a station is physically functioning, with no external data at all | +8.30 ppm typical; the failing site read −29.2 | 50 |
| Public-holiday natural experiment | a sector's contribution, with no emission ratio | **31.5** % CO drop | 48 |

Read the column as a set of *limits*, not promises. The strongest verification available — two independent instruments on the same hilltop — pins a growth rate to 0.81 ppm yr⁻¹, a third of one year's growth. Nothing here verifies a tonne.

What the last three rows offer is different in kind and is where the value actually sits. **A ratio in which the layer depth cancels, a sign test that needs no external reference, and a public holiday that switches off a sector** are all ways of measuring something without needing the calibration chain that a tonne-level claim would require. They are cheap, they are robust, and an inventory cannot produce them.

### 17.12 Finding 100 — the network cannot verify a national target, and the shortfall is two orders of magnitude

Indonesia's Second Nationally Determined Contribution, submitted in October 2025, states an absolute 2035 range of **1,257.7 to 1,488.9 MtCO₂e**. The width of that range — 231.2 MtCO₂e yr⁻¹ — is the ambiguity a verification system would have to resolve.

What concentration signal would it produce? Spread the emission over Indonesia's land area *A*, mix it into a boundary layer of depth *h*, and ventilate it to the free troposphere on a timescale $\tau_v$. At steady state,

$$\Delta C = \frac{E}{A}\cdot\frac{\tau_v}{h\,\rho_{\text{air}}}\cdot\frac{M_{\text{air}}}{M_{\text{CO}_2}}$$

**Table 116 — the regional signal of the full width of the national target** (from `outputs/k_national_limit.csv`):

| PBL depth | Ventilation time | Signal (ppm) | Detectable step, 5 yr | Ratio |
|---|---|---|---|---|
| 500.0 m | 0.5 d | 0.182 | 2.73 ppm | 0.067 |
| 500.0 m | 3.0 d | **1.093** | 2.73 ppm | **0.400** |
| 1000.0 m | 1.0 d | 0.182 | 2.73 ppm | 0.067 |
| 1000.0 m | 3.0 d | 0.547 | 2.73 ppm | 0.200 |
| 2000.0 m | 0.5 d | 0.046 | 2.73 ppm | 0.017 |
| 2000.0 m | 3.0 d | 0.273 | 2.73 ppm | 0.100 |

**Across every plausible combination the signal is 2 % to 40 % of what the record can resolve.** The most favourable case in the table — a shallow layer and three days of stagnation, which is not a national annual average — still falls short by a factor of two and a half.

The conclusion is not that atmospheric measurement has no place in NEK. It is that **its place is not the national ledger.** The scales at which this network contributes are the ones Findings 92 to 95 identify: a city's sectoral split, a peatland's emission factor, a quarter-to-half abatement at a monitored site over five years, and a physical check on whether an inventory's numbers are consistent with the air above the country.

A national verification capability would need a different instrument entirely — a dense network with continuous towers, an inverse model with assimilated meteorology, and satellite column data — and the correct statement about the present network is that it would be one input to such a system rather than a substitute for it.

> **This is an order-of-magnitude argument and is meant as one.** A steady-state box model over an archipelago is a caricature: real ventilation is not a single timescale, the boundary layer over Indonesia is not one depth, and the emission is neither uniform nor steady. The conclusion is robust to all of that only because the shortfall is a factor of 2.5 in the best case and 60 in the worst. If it were a factor of two, this table would not settle it.

### 17.13 What follows

Six statements from this part are worth carrying forward, and they are not the ones a reader expects from a section about carbon prices.

1. **The measurement is the cheap, well-constrained part.** In a monetised peat claim it contributes a factor of 1.18 against the layer depth's 4.0 and the price's 2.32 (Finding 96).
2. **A ceilometer at Jambi and Kemayoran would do more for the accuracy of Indonesia's peat and urban methane numbers than any change in market design** (Findings 91, 96). Section 18 asks for it under instrumentation.
3. **The atmosphere can split a city between administrations** (Finding 92), and that is the kind of claim inventories cannot check themselves against.
4. **Afternoon-sampled concentrations carry a fixed-sign bias larger than the signal** (Finding 94). Any flux-based methodology needs a site-specific rectifier correction, which only continuous data supply.
5. **The verifiable scale is a quarter to a half of a monitored site's own source over five years** (Finding 93) — and nothing at national scale (Finding 100).
6. **Fire reversal is a certainty, not a risk** (Finding 98), and a peat liability outlives every instrument available to price it (Finding 97).

> **The honest summary of this part.** This network cannot verify a tonne, and no atmospheric network of five stations could. What it can do is tell a carbon-pricing system when its physics is wrong — and Findings 92, 94 and 96 are each an instance of that. That is a supporting role, and it is worth funding on its own terms rather than overclaiming into a verification role it cannot fill.

---

# Part VII — What the observing system itself resolves

## 18. Information content, robustness and network design — Findings 101 to 120

These twenty tests use no new observations. They ask whether conclusions survive changes in analyst choice, what is lost to missingness, and whether the timing and spatial structure contain information that the earlier scalar summaries discard. The calculations are in `scripts/a33_extra7.py`; each table is written separately as `outputs/q_*.csv`.

### 18.1 Finding 101 — daily tracer loops contain source timing that a correlation discards

For every day with at least 18 paired hours, each tracer is standardised within that day and the signed area of the closed hourly polygon is calculated. **The CO₂–CH₄ loop has opposite preferred directions at the two forest sites (BKT +0.637; Bariri +0.750) and at Jambi/Jakarta (−1.135; −0.493).** Jambi turns in the negative direction on 71.8 % of 586 complete days, against 40.9 % of 1,285 Bariri days. The mean-area bootstrap intervals exclude zero at all five sites, though Sorong only narrowly does so (`outputs/q_hysteresis.csv`).

> **A loop direction is a timing diagnostic, not a source label.** Boundary-layer growth, entrainment and temporally offset emissions can all rotate it. The finding is the reproducible difference between sites; attribution requires meteorology or an intervention.

### 18.2 Finding 102 — Sorong's CO₂–CH₄ loop reverses with season

**Sorong's median standardised loop area changes from −0.821 over 306 May–October days to +0.043 over 225 November–April days.** The other four stations keep the same sign in both half-years: positive at BKT and Bariri, negative at Jambi and Kemayoran (`outputs/q_hysteresis_season.csv`). This makes Sorong the one site where the relative timing of methane and carbon dioxide changes qualitatively with season.

> The split is a six-month wet/dry convention, not a day-specific rainfall classification. It establishes a repeatable phase change, not whether rainfall, wind direction or source activity causes it.

### 18.3 Finding 103 — Jakarta's combustion coupling is strongest at night

**Kemayoran's hourly CO₂–CO correlation rises from +0.587 in the afternoon to +0.861 at night; Spearman ρ rises from +0.521 to +0.871.** At BKT the corresponding correlations are −0.075 and +0.141. Jambi retains moderate three-species coupling in both periods, while Bariri and Sorong remain weak (`outputs/q_daynight_coupling.csv`). The contrast is consistent with a shared urban combustion source accumulating into a shallow nocturnal layer.

> These are correlations of levels within each period, not source fractions. A shared boundary layer strengthens every co-emitted pair, so the urban–background contrast is the evidence, not the Jakarta coefficient alone.

### 18.4 Finding 104 — the percentile chosen for a baseline is a material analytical choice

Across afternoon hours, shifting the baseline from the 10th to the 30th percentile spans **2.60–6.24 ppm for CO₂, 15–54 ppb for CH₄ and 10–49 ppb for CO**. BKT is most sensitive in CO₂ and CH₄; Kemayoran is most sensitive in CO (`outputs/q_baseline_quantile.csv`). These spans exceed several inter-station differences elsewhere in the report.

> No percentile is “truer” in isolation. The 20th percentile remains the declared regional-background convention; this result quantifies the analyst-choice uncertainty and is not permission to tune the percentile to a preferred answer.

### 18.5 Finding 105 — the afternoon clock choice is not material

The same test applied to time selection gives the opposite result. **Moving the five-hour afternoon window from 12:00–16:00 to 11:00–15:00 or 13:00–17:00 changes the CO₂ baseline by at most 1.24 ppm at Jambi and by 0.58 ppm or less at the other four sites.** CH₄ moves by at most 6 ppb and CO by at most 6 ppb (`outputs/q_afternoon_window.csv`).

> This robustness applies to one-hour shifts around the afternoon minimum. It does not apply to the raw BKT timestamp defect, which moves the selection by seven hours and changes the physical air mass entirely.

### 18.6 Finding 106 — subtraction cannot choose the reference station

Using only the common 2023–2024 interval, subtracting BKT, Jambi, Kemayoran, Bariri or Sorong changes every reported enhancement but leaves the station ordering exactly invariant. **The reference defines the zero; it cannot be selected by the ranking that results from subtracting it.** For CO₂ the common-period range is Bariri to Kemayoran (12.31 ppm); for CH₄ it is Bariri to Kemayoran (96 ppb); for CO it is Bariri to Kemayoran (157 ppb) (`outputs/q_reference_sensitivity.csv`).

> This is an identifiability result. Choosing Bariri still requires land-cover knowledge, calibration evidence and the intended comparison—not an algebraic score derived from the same levels.

### 18.7 Finding 107 — the broad station ordering repeats in both complete overlap years

In both 2023 and 2024, **Kemayoran is the highest station in CO₂ and CO and Bariri the lowest**. Jambi is fourth in both gases and years. BKT and Sorong exchange the middle CO₂ order; Jambi and Kemayoran exchange the top CH₄ order (`outputs/q_annual_rank.csv`).

> There are only two complete five-station years. This supports the broad source-to-background ordering, not a climatological rank for the three clean middle sites.

### 18.8 Finding 108 — maintenance gains are largest where return is poorest, but sublinear

If sampling-limited uncertainty scales as $n^{-1/2}$, adding twenty percentage points of valid hours reduces a detection threshold by **14.1 % at Sorong, 11.2 % at Jambi, 9.3 % at Bariri and only 2.5 % at Kemayoran**, which is already near complete (`outputs/q_uptime_gain.csv`). This turns the maintenance recommendation into a quantitative diminishing-return curve.

> This isolates sample count. It assumes restored hours have the same noise and autocorrelation as observed hours; repairing systematically difficult weather or plume conditions could help less—or more—than the square-root calculation.

### 18.9 Finding 109 — outages are seasonal operations, not random missing hours

**Jambi's all-species return falls to 47.5 % in November and Kemayoran's to 67.0 % in February, while their best months exceed 97 %.** Sorong ranges from 27.5 % in May to 73.9 % in March. BKT CO₂/CH₄ range from 26.2 % in January to 37.1 % in November over the full coverage window (`outputs/q_outage_season.csv`).

> Month-of-year return pools different years and therefore mixes recurrent seasonality with outages that happened once in a particular month. It identifies operational concentration, not a meteorological cause.

### 18.10 Finding 110 — one outage can erase a climatology

The longest common-species gaps are **396 h at Jambi, 372 h at Kemayoran, 1,587 h at Bariri and 5,828 h at Sorong**. At BKT the CO₂/CH₄ archive gap is about 44,600 h, while CO's longest gap is 6,648 h (`outputs/q_longest_gap.csv`). A monthly percentage conceals whether loss is scattered or removes an entire season.

> The edges of the delivered station record are not counted as outages. These are internal gaps between valid observations and say nothing about whether an instrument was expected to operate before its first or after its last record.

### 18.11 Finding 111 — the nominal archive size is not the paired archive size

Of BKT's 161,866 archived station-hours, **only 41.1 % contain CO₂, CH₄ and CO together**, a 58.9-point pairing penalty. All three are paired in 100.0 % of Jambi, Kemayoran and Bariri station-hours and 99.1 % at Sorong (`outputs/q_joint_return.csv`). This is why a multispecies BKT analysis cannot cite the headline station-hour count as its sample size.

> Rows where all three species are absent do not exist in `all.pkl`; this statistic is conditional on an archived station-hour. Calendar-time completeness is the separate result in Finding 112.

### 18.12 Finding 112 — calendar-month completeness changes the station ranking

Counting every clock hour between first and last observation, **only 28 of Sorong's 52 months clear 50 % return** and 19 clear 80 %. Jambi clears 22 of 26 at 50 %, Kemayoran 25 of 26, and Bariri 49 of 58 (`outputs/q_complete_months.csv`). BKT CO₂/CH₄ clear 50 % in 97 of 283 calendar months; its CO clears 238.

> Partial first and last months are included because an annual product experiences them as incomplete. For instrument-performance reporting they should also be shown separately.

### 18.13 Finding 113 — the weekday experiment is unique to Jakarta

Morning weekday-minus-weekend bootstrap intervals include zero for fourteen of fifteen station × species tests. **The exception is Kemayoran CO: +201 ppb, with a bootstrap interval of +141 to +232 ppb.** Its CO₂ difference is positive but much smaller and its CH₄ comparison is null (`outputs/q_weekday_network.csv`).

> The bootstrap resamples days, but holidays and multi-day pollution episodes are not explicitly blocked. The spatial control—four other stations tested identically—is stronger than the nominal multiplicity-unadjusted interval.

### 18.14 Finding 114 — Jakarta's rush increment has a combustion fingerprint no other site approaches

Relative to 12:00–15:00, Kemayoran at 06:00–09:00 adds **18.52 ppm CO₂, 232 ppb CH₄ and 482.5 ppb CO**. Its incremental ΔCO/ΔCO₂ is 26.05 ppb ppm⁻¹, against 0.22 at BKT, 1.50 at Jambi, 0.54 at Bariri and 0.94 at Sorong (`outputs/q_rush_fingerprint.csv`).

> This is a median time-of-day contrast, not a paired regression and not a flux. Boundary-layer depth differs between morning and midday; the exceptionally high CO ratio and the four-station control make the source fingerprint, not the absolute increment.

### 18.15 Finding 115 — season changes the source mixture, not only the amplitude

Kemayoran's CH₄:CO₂ diurnal-amplitude ratio rises from **13.75 ppb ppm⁻¹ in November–April to 18.24 in May–October**; Sorong rises from 0.73 to 1.83. Bariri remains 0.35 and 0.33, while Jambi shifts from 3.74 to 3.10 (`outputs/q_seasonal_diurnal.csv`).

> A ratio of separately estimated amplitudes is not a flux ratio. It cancels a constant calibration scale but not species-specific source timing or a seasonally changing boundary-layer depth.

### 18.16 Finding 116 — extreme CO is persistent where fire dominates and brief where traffic dominates

Defining extremes within each site as hours above its 99th percentile, BKT CO produces **28 independent clusters with a median span of 34.5 h and a maximum of 801 h**. Kemayoran produces 38 clusters with a median of 3.5 h and maximum of 148 h (`outputs/q_extreme_clusters.csv`). Jambi, Bariri and Sorong have median spans of one to two hours.

> Clusters are separated by 48 hours and the threshold is site-relative. The result compares episode structure, not absolute hazard; a different separation window changes the cluster count.

### 18.17 Finding 117 — three days remove most event enhancement, but not equally by tracer

Events are days above the 95th percentile of each species' anomaly over a centred 31-day background. **The median day-three fraction ranges from 0.23 for Jambi CO and 0.27 for its CO₂ to 0.67 for Bariri CH₄.** At BKT the three fractions are 0.38, 0.40 and 0.52 for CO₂, CH₄ and CO (`outputs/q_event_decay.csv`).

> Events can overlap, so these are descriptive recovery fractions rather than independent lifetime estimates. Transport, renewed emission and changing background all contribute.

### 18.18 Finding 118 — an extreme has no natural concentration threshold across this network

The 99th-percentile CO threshold is **183 ppb at Bariri, 313 ppb at Sorong, 681 ppb at Jambi, 841 ppb at BKT and 2,304 ppb at Kemayoran**. CO₂ spans 454–525 ppm and CH₄ 2,000–4,798 ppb (`outputs/q_threshold_sensitivity.csv`).

> Percentiles force a fixed exceedance fraction and therefore do not estimate return periods. The finding is that a single national concentration threshold would compare unlike site types; any operational threshold must declare whether it is absolute or site-relative.

### 18.19 Finding 119 — there is no daily common mode after local background removal

After subtracting each station's centred 31-day afternoon median, **none of the ten station-pair CO₂ correlations exceeds +0.109**; most CH₄ and CO pairs are below +0.16. The isolated BKT–Jambi CO correlation of +0.393 rests on only 87 overlapping days and is not reproduced elsewhere (`outputs/q_common_mode.csv`).

> Removing a 31-day local background intentionally removes regional variations slower than a month. This null applies to daily departures, not seasonal cycles, long-term growth or the 2023 annual anomaly.

### 18.20 Finding 120 — no station substitutes for another at daily scale

A station's daily afternoon anomaly was predicted from the median anomaly of the other four. **Across all fifteen station × species tests, prediction correlations range from −0.023 to +0.099 and RMSE is 1.03–2.92 times the target station's own standard deviation** (`outputs/q_redundancy.csv`). The network is spatially complementary, not redundant.

> This is deliberately a simple leave-one-station-out benchmark, not an optimal transport model. Meteorology could add predictive skill; the finding is that concentration records alone do not supply it.

## 19. Multivariate structure, nonlinear dependence and scale — Findings 121 to 200

This pass removes each station's month-by-hour climatology before analysing paired, robustly standardised anomalies. It therefore asks how gases move together within a site, not whether their absolute levels agree. `scripts/a34_extra8.py` writes one `outputs/aa_*.csv` file per result.

### 19.1 Finding 121 — one mode dominates urban air, less so rainforest air

**The first principal component explains 72.4 % of three-gas anomaly variance at Kemayoran, 68.4 % at Jambi, 60.6 % at BKT, 57.9 % at Sorong and 54.7 % at Bariri** (`outputs/aa_pca.csv`). Jakarta PC1 loads most strongly on CO₂ and CO; BKT on CO₂ and CH₄.

> PCA identifies covariance axes, not sources; eigenvector signs are arbitrary and loadings cannot be read as emission fractions.

### 19.2 Finding 122 — Bariri retains the most independent tracer information

The eigenvalue participation ratio gives **2.48 effective dimensions at Bariri, 2.34 at Sorong, 2.09 at BKT, 1.93 at Jambi and 1.72 at Jakarta** (`outputs/aa_dimension.csv`). Thus a third gas adds most independent information in the rainforest record and least in the tightly coupled megacity plume.

> Effective dimension depends on standardisation and the three chosen gases; it is not an intrinsic dimension of the atmosphere.

### 19.3 Finding 123 — conditional dependence separates the dominant source pairs

After linearly controlling the third gas, **Jakarta CO₂–CO remains +0.846 and BKT CO₂–CH₄ +0.798**. Jakarta CH₄–CO falls from +0.370 raw to −0.093 conditional, while Jambi retains three moderate edges (+0.234 to +0.401; `outputs/aa_partial.csv`).

> Partial correlation removes only linear dependence on the control and cannot establish causality.

### 19.4 Finding 124 — Jakarta's upper combustion tail is fourteen times independence

Among standardised anomalies, the probability that CO is also above its 95th percentile given top-5 % CO₂ is **0.715 at Jakarta**, versus 0.05 under independence. Jambi's three pairs are 0.284–0.373; Bariri's are 0.082–0.129 (`outputs/aa_upper_tail.csv`).

> This empirical tail coefficient is at a finite 95th-percentile threshold, not an asymptotic extreme-value parameter.

### 19.5 Finding 125 — clean-air tails couple differently from plume tails

Jakarta's lower-tail conditional probabilities are **0.578 for CO₂–CH₄ and 0.549 for CO₂–CO**. BKT CO₂–CO is 0.034—below the 0.05 independence expectation—while its CO₂–CH₄ remains 0.452 (`outputs/aa_lower_tail.csv`).

> Low anomalies are not necessarily pristine air; instrument noise and distinct baselines can also populate a lower tail.

### 19.6 Finding 126 — nonlinear information confirms two dominant fingerprints

Bias-corrected mutual information is **0.557 nats for Jakarta CO₂–CO and 0.507 for BKT CO₂–CH₄**, against a mean of 0.002 nats after permutation. The weakest link is BKT CO₂–CO at 0.033 (`outputs/aa_mutual_information.csv`).

> Quantile binning makes the estimator robust but coarse; values compare pairs within this analysis and are not channel capacities.

### 19.7 Finding 127 — Jakarta methane coupling is monotonic but strongly nonlinear

At Jakarta, CH₄–CO has Pearson **+0.370** but Spearman **+0.702**; CO₂–CH₄ is +0.473 against +0.779. No other station shows gaps this large (`outputs/aa_rank_nonlinearity.csv`).

> Rank–linear disagreement demonstrates curvature or tail influence; it does not identify the functional form.

### 19.8 Finding 128 — source coupling steepens in the upper conditional tail

Standardised Jakarta CO-on-CO₂ quantile slopes rise from **0.900 at q10 to 1.102 at q50 and 1.413 at q90**. Jakarta CH₄ rises from 0.764 to 1.517; Sorong CO rises from 0.169 to 0.802 (`outputs/aa_quantile_slopes.csv`).

> Quantile regressions use a reproducible 5,000-hour subsample. Slopes are dimensionless anomaly relationships, not emission ratios.

### 19.9 Finding 129 — the day–night distribution shift is primarily CO₂ at vegetated sites

Bariri's Jensen–Shannon divergence between night and afternoon is **0.602 nats for CO₂ but 0.010 for CH₄**; Jambi is 0.511 and 0.217. Jakarta shifts all three gases (0.211–0.302; `outputs/aa_daynight_js.csv`).

> Divergence measures the whole distribution and deliberately does not say whether the shift is in mean, spread or tails.

### 19.10 Finding 130 — extreme CO₂ has a clock; extreme CO often does not

Normalised hour entropy for top-decile CO₂ is **0.724–0.793 at four sites**, with peaks near 06:00–07:00. BKT CO is nearly uniform through the clock (0.996), consistent with multi-day fire pollution (`outputs/aa_hour_entropy.csv`).

> Entropy is conditional on each site's own top decile; it compares timing concentration, not absolute severity.

### 19.11 Finding 131 — the diurnal clock explains most rainforest CO₂ variance

Sequential variance decomposition assigns **65.1 % of Bariri CO₂ variance to hour of day**, 49.4 % at Jambi and 35.9 % at Jakarta. For most CH₄ and CO records, 54–95 % remains after hour and month effects (`outputs/aa_variance_components.csv`).

> Hour is removed before month, so the small shared component is assigned to hour; this declared order matters in incomplete records.

### 19.12 Finding 132 — averaging suppresses urban variance but not background persistence

Thirty-day means retain **4.1–8.1 % of hourly variance at Jakarta and Jambi**, but 59.0 % for BKT CO₂ and 62.8–66.4 % for Bariri CH₄/CO (`outputs/aa_multiscale_variance.csv`). The latter variance is slow background and season, not hourly noise.

> Resampling does not fill gaps; different scale ratios combine autocorrelation with record completeness.

### 19.13 Finding 133 — the optimum averaging scale is species-specific

Allan deviation reaches its minimum at **one hour for BKT CH₄ and CO**, 24 hours for Bariri CH₄, and seven days for most newer-station gases (`outputs/aa_allan.csv`). More averaging can add drift or episode structure instead of precision.

> These are empirical stability minima of the delivered record, not manufacturer instrument specifications.

### 19.14 Finding 134 — BKT variability has no resolved long-term trend

Across twelve measured years, robust annual anomaly scale trends are **−0.0016 [−0.0059, +0.0105] yr⁻¹ for CO₂, −0.0021 [−0.0255, +0.0065] for CH₄ and −0.0324 [−0.0575, +0.0027] for CO** (`outputs/aa_variance_trend.csv`). All include zero.

> This test concerns variability after climatology removal, not concentration trends; other stations are too short for the required ten points.

### 19.15 Finding 135 — algorithmic variance change points are not physically stable

The minimum within-segment variance split falls in **2011 for BKT CO₂ but 2024 for CH₄ and CO**, and in different years at Bariri (`outputs/aa_variance_changepoint.csv`). The disagreement and edge solutions fail the physical-coherence test.

> This is a negative finding from an unconstrained scan. No p-value is quoted because the candidate split was selected from the same short annual series.

### 19.16 Finding 136 — source-coupling signs are stable between years

Fourteen of fifteen station × tracer-pair series retain one correlation sign in every measured year. BKT's twelve-year median correlations are +0.558, +0.337 and +0.576; only Bariri CO₂–CH₄ changes sign once (`outputs/aa_covariance_stability.csv`).

> Sign stability is weaker than slope stability; the newer stations contribute only three to six annual estimates.

### 19.17 Finding 137 — the conditional-dependence graph changes with site type

The strongest precision-matrix edge is **CO₂–CH₄ at BKT (+0.798), CO₂–CO at Jakarta (+0.846), and two comparable biogenic/combustion edges at Jambi (+0.398 to +0.401)** (`outputs/aa_precision_network.csv`).

> With three nodes this graph is exactly the partial-correlation result of Finding 123 expressed structurally, not independent confirmation.

### 19.18 Finding 138 — extreme days are almost entirely local

Across site pairs, Jaccard overlap of top-5 % daily events is generally **below 0.10 and frequently zero**. The largest value, BKT–Jambi CH₄ at 0.286, rests on only 87 overlapping days and two joint events (`outputs/aa_event_synchrony.csv`).

> Site-specific percentiles equalise marginal event rates. This tests synchrony, not whether two sites cross the same absolute concentration.

### 19.19 Finding 139 — no robust one-week propagation lag emerges

Scanning −7 to +7 days gives mostly small best correlations; for overlaps above 400 days, absolute values remain **≤0.175** for CO₂ and comparably weak for most pairs (`outputs/aa_propagation_lag.csv`). Larger coefficients occur on short BKT overlaps and do not replicate.

> Fifteen lags were scanned, so a selected maximum is upward biased. This is reported as a null, not a fitted transport speed.

### 19.20 Finding 140 — the network has almost five independent daily dimensions

The five-station correlation eigenvalues give participation ratios of **4.92 for CO₂, 4.69 for CH₄ and 4.61 for CO**; PC1 explains only 23.6–29.3 % (`outputs/aa_network_dimension.csv`). Daily local anomalies are therefore nearly spatially independent.

> Pairwise-complete correlations enter the matrix because no long interval has all five stations daily-complete; the result is descriptive, not a covariance model for inversion.

### 19.21 Finding 141 — even an optimised multigas cross-station combination is weak

Regularised canonical correlation is **0.234 or less for every station pair with more than 100 overlapping days**. BKT–Jambi reaches 0.424 on only 87 days (`outputs/aa_canonical.csv`). Combining three gases does not reveal a hidden shared daily air mass.

> Canonical weights are fitted and evaluated on the same overlap; reported correlations are optimistic upper bounds.

### 19.22 Finding 142 — a missing tracer is reconstructible only where sources are coupled

Leave-year-out reconstruction from the other two gases gives **R² = 0.744 for Jakarta CO₂ and 0.717 for CO**, but 0.204 for its CH₄. At Bariri every gas is ≤0.083; at Sorong every gas ≤0.213 (`outputs/aa_species_reconstruction.csv`).

> Reconstruction predicts standardised anomalies, not calibrated concentration, and cannot replace an independently measured gas for trend work.

### 19.23 Finding 143 — three anomalies barely identify the station

A nearest-centroid classifier evaluated by leaving whole months out scores **26.5 % accuracy against 20 % chance**, with mutual information only **0.010 bit** (`outputs/aa_station_classification.csv`). Removing climatology removes most site identity.

> The classifier is deliberately simple. Failure means the three anomaly coordinates alone are weak identifiers, not that richer temporal models could not classify sites.

### 19.24 Finding 144 — Jakarta is distinct because of CO; Bariri and Sorong are nearly inseparable

Robust three-gas centroid distance is **9.28 for Jakarta–Bariri and 9.27 for Jakarta–Sorong**, with CO the largest contributor. Bariri–Sorong is only 0.693 (`outputs/aa_centroid_separation.csv`).

> These are robust distances in the observed three-gas space, not geographical or emissions distances.

### 19.25 Finding 145 — BKT extremes are strongly bursty

For daily top-5 % events, BKT burstiness is **0.587 for CO₂, 0.703 for CH₄ and 0.692 for CO**, against 0.079–0.196 at Jakarta and Jambi (`outputs/aa_burstiness.csv`). Extreme BKT days arrive in seasons and episodes, not as a Poisson clock.

> The long BKT record spans gaps and changing species coverage; burstiness describes observed inter-event intervals, not a stationary hazard rate.

### 19.26 Finding 146 — BKT fire CO has the strongest extremal clustering

The runs extremal index for BKT CO is **0.119**, equivalent to 8.39 consecutive extreme hours per run, against 0.361 at Jakarta and 0.689 at Jambi (`outputs/aa_extremal_index.csv`).

> Runs use consecutive archived hours and a site-relative 99th percentile; missing hours can split a physical episode.

### 19.27 Finding 147 — composite recovery separates conservative and ventilated tracers

Median enhancement falls below half after **five days for Bariri CH₄, four for Bariri CO, three for BKT CO and one day for most Jambi/Jakarta gases** (`outputs/aa_recovery_composite.csv`).

> Peaks can overlap and composites mix transport with renewed emission. These are recovery times, not chemical lifetimes.

### 19.28 Finding 148 — one exponential is not a universal recovery law

A four-point AIC comparison prefers power-law recovery for **ten of fifteen** station–species composites; BKT CO and Bariri CH₄/CO prefer exponential decay by ΔAIC 14.4, 7.5 and 15.6 (`outputs/aa_decay_model.csv`).

> Four lag points cannot establish a mechanistic law. Model preference diagnoses heterogeneous event mixtures and is not suitable for extrapolation.

### 19.29 Finding 149 — hysteresis is timing, not plume size

Across 528–2,469 complete days per station, absolute CO₂–CH₄ loop area has **Spearman correlations from −0.100 to +0.040 with daily CO₂ range** (`outputs/aa_hysteresis_amplitude.csv`). Large loops are not simply large plumes.

> Standardisation intentionally removes amplitude before area is calculated; the null confirms that design rather than independently discovering it.

### 19.30 Finding 150 — the strongest nonlinear links remain physically interpretable after conditioning

Jakarta CO₂–CO leads the network at **0.557 excess mutual-information nats and +0.846 partial correlation**; BKT CO₂–CH₄ follows at 0.507 and +0.798 (`outputs/aa_nonlinear_synthesis.csv`). Jakarta CH₄–CO is the counterexample: 0.357 nats but −0.093 conditional, showing information shared through CO₂ rather than a direct edge.

> Mutual information and partial correlation answer different questions. Agreement strengthens interpretation; disagreement is not a contradiction.

### 19.31 Findings 151–155 — every station has a resolved ventilation clock

The steepest one-hour changes in the median CO₂ diurnal cycle define a reproducible morning-collapse and evening-rebuild clock.

**Table 117 — CO₂ transition clock by station** (from `outputs/ab_transition_clock.csv`)

| Station | Hours | Morning collapse | Step (ppm) | Evening build-up | Step (ppm) | Separation |
|---|---:|---:|---:|---:|---:|---:|
| BKT | 60,396 | 09:00 | −6.33 | 18:00 | +2.88 | 9 h |
| JMB | 14,484 | 09:00 | **−15.06** | 20:00 | +4.57 | 11 h |
| KMY | 16,495 | 08:00 | −9.30 | 21:00 | +2.53 | **13 h** |
| PLU | 32,767 | 08:00 | −9.13 | 18:00 | **+5.05** | 10 h |
| SRG | 13,633 | 09:00 | −7.58 | 21:00 | +1.62 | 12 h |

The common 08:00–09:00 collapse is the growth of the convective boundary layer; the station-specific evening time and magnitude record how quickly surface coupling re-establishes. Jambi’s −15.06 ppm step is the strongest morning ventilation event, while coastal Sorong’s weak evening recovery is consistent with continued ventilation.

> These are extrema of a long-term median clock, not sunrise measurements. Cloud, wind and changing sunrise time are folded into the climatology.

### 19.32 Findings 156–160 — nocturnal accumulation is usually curved, not one constant flux

Early-night (20:00–23:00) and late-night (00:00–03:00) slopes were paired within 554–2,368 complete nights.

**Table 118 — early- and late-night CO₂ accumulation slopes** (from `outputs/ab_nocturnal_curvature.csv`)

| Station | Nights | Early | Late | Late − early | Late/early | *p* |
|---|---:|---:|---:|---:|---:|---:|
| BKT | 2,368 | 1.612 | 0.754 | −0.569 | 0.468 | 0.0000 |
| JMB | 603 | 3.341 | 2.871 | −0.070 | 0.859 | **0.5791** |
| KMY | 685 | 1.700 | 1.481 | −0.297 | 0.871 | 0.0849 |
| PLU | 1,341 | 2.482 | 1.756 | −0.802 | 0.708 | 0.0000 |
| SRG | 554 | 1.335 | 0.494 | −0.442 | **0.370** | 0.0000 |

BKT, Bariri and Sorong slow decisively after midnight. Jambi is the important null: its surface source continues filling the nocturnal layer at nearly the early-night rate. A single straight nocturnal slope therefore has different physical meaning by site.

> Curvature can arise from a changing layer depth, intermittent turbulence or a changing source. Concentrations alone do not identify which term changed.

### 19.33 Findings 161–165 — residual-layer carry-over is a site property

After removing calendar-month medians, each afternoon CO₂ anomaly was paired with the following dawn.

**Table 119 — afternoon-to-next-dawn CO₂ carry-over** (from `outputs/ab_carryover.csv`)

| Station | Day pairs | Pearson *r* | Spearman ρ | Variance explained |
|---|---:|---:|---:|---:|
| BKT | 2,508 | **0.750** | 0.729 | **56.2 %** |
| JMB | 597 | 0.089 | 0.080 | 0.8 % |
| KMY | 686 | 0.172 | 0.206 | 3.0 % |
| PLU | 1,334 | 0.444 | 0.446 | 19.7 % |
| SRG | 557 | 0.054 | 0.114 | 0.3 % |

The background sites remember; the strong local-source sites reset. BKT retains more than half the next-dawn variance, Bariri one fifth, while Jambi and Sorong retain effectively none.

> This is predictive memory, not proof that the same air parcel survives. Persistent regional forcing can produce the same correlation.

### 19.34 Findings 166–170 — monsoon reorganisation is methane-led at four sites

Jensen–Shannon divergence compares the full wet- and dry-half-year distributions rather than only their means.

**Table 120 — wet–dry distribution divergence by gas** (from `outputs/ab_seasonal_shift.csv`)

| Station | CO₂ | CH₄ | CO | Dominant gas |
|---|---:|---:|---:|---|
| BKT | 0.004 | **0.079** | 0.043 | CH₄ |
| JMB | 0.010 | **0.057** | 0.009 | CH₄ |
| KMY | 0.008 | 0.013 | **0.023** | CO |
| PLU | 0.005 | **0.225** | 0.059 | CH₄ |
| SRG | 0.033 | **0.047** | 0.029 | CH₄ |

Bariri methane changes most, while Jakarta is remarkably seasonally stable. The result is consistent with hydrology and transported methane controlling rural distributions, and year-round urban activity controlling Jakarta.

> The six-month partition is deliberately broad and does not distinguish rainfall, wind direction and source seasonality.

### 19.35 Findings 171–175 — three multigas regimes separate source states, with one warning

Three-cluster *k*-means was applied to robust month-by-hour anomalies, using at most 10,000 paired hours per station.

**Table 121 — three-regime separation and the most distinct regime** (from `outputs/ab_source_regimes.csv`)

| Station | Variance explained | Distinct-regime share | CO₂ z | CH₄ z | CO z |
|---|---:|---:|---:|---:|---:|
| BKT | 54.4 % | 10.2 % | 0.03 | 0.50 | **3.59** |
| JMB | 51.2 % | 4.9 % | 5.01 | 5.66 | 4.80 |
| KMY | **66.0 %** | 1.5 % | 2.15 | **24.68** | 2.22 |
| PLU | 45.0 % | 15.6 % | 0.54 | 0.87 | 2.40 |
| SRG | 64.5 % | **0.1 %** | 5.80 | 6.11 | 99.73 |

BKT isolates a CO-rich fire state, Jambi a coherent three-gas accumulation state, and Jakarta a rare methane-dominated state. Bariri is least cleanly clustered. Sorong is the falsification case: a 0.1 % cluster with a 99.7 robust-score CO centroid is an outlier bucket, not an atmospheric regime.

> Cluster labels are descriptive and depend on *k*. The Sorong result explicitly limits automated regime attribution in a short, heavy-tailed record.

### 19.36 Findings 176–180 — compound extremes identify the dominant source pair

For each station, the pair with the greatest probability of simultaneous top-5 % anomalies was selected.

**Table 122 — strongest compound upper tail** (from `outputs/ab_compound_extremes.csv`)

| Station | Pair | Joint hours | Conditional probability | Multiple of independence |
|---|---|---:|---:|---:|
| BKT | CO₂–CH₄ | 1.67 % | 0.334 | 6.7× |
| JMB | CO₂–CH₄ | 1.86 % | 0.373 | 7.5× |
| KMY | CO₂–CO | **3.58 %** | **0.715** | **14.3×** |
| PLU | CO₂–CH₄ | 0.64 % | 0.129 | 2.6× |
| SRG | CH₄–CO | 1.70 % | 0.340 | 6.8× |

The selected pairs reproduce the physical source ordering without using site labels: combustion in Jakarta, coupled carbon gases at BKT/Jambi, and CH₄–CO at Sorong.

> Selection of the maximum among three pairs is optimistic; finite-threshold dependence is not an asymptotic extreme-value coefficient.

### 19.37 Findings 181–185 — event composition changes while CO clears

Daily top-5 % CO events were followed for three days using anomalies above a rolling 20th-percentile background.

**Table 123 — event ageing from day 0 to day 3** (from `outputs/ab_event_ageing.csv`)

| Station | Events | CH₄/CO day 0 | CH₄/CO day 3 | Change | CO remaining |
|---|---:|---:|---:|---:|---:|
| BKT | 130 | 0.290 | 0.319 | −0.003 | 0.419 |
| JMB | 27 | 0.624 | **1.264** | +0.327 | **0.230** |
| KMY | 33 | 0.408 | 0.373 | +0.071 | 0.273 |
| PLU | 63 | 0.209 | 0.219 | +0.024 | **0.575** |
| SRG | 32 | 0.452 | 0.732 | +0.048 | 0.365 |

Jambi is the clearest compositional evolution: CO clears rapidly while methane persists or is renewed. BKT and Bariri ratios remain stable, with Bariri retaining the most CO.

> Day-three ratios are conditional on positive residual CO and can mix plume ageing with new emissions; the statistic is a composite, not a reaction-rate measurement.

### 19.38 Findings 186–190 — daily CO persistence is real at all five stations

Observed lag-1 correlations were compared with 1,000 shuffled surrogates, which preserve the marginal distribution but destroy temporal order.

**Table 124 — surrogate test of daily CO memory** (from `outputs/ab_surrogate_memory.csv`)

| Station | Days | Observed lag 1 | Surrogate mean | *p* |
|---|---:|---:|---:|---:|
| BKT | 2,656 | 0.623 | 0.000 | 0.001 |
| JMB | 637 | 0.315 | −0.001 | 0.001 |
| KMY | 701 | 0.366 | 0.000 | 0.001 |
| PLU | 1,481 | **0.640** | −0.002 | 0.001 |
| SRG | 633 | 0.513 | −0.002 | 0.001 |

Even Jakarta traffic does not reset completely by calendar day; Bariri and BKT retain the strongest memory. This strengthens the earlier persistence ladder with a distribution-free null.

> Random shuffling tests independence, not a specific meteorological model. Season was removed by a rolling background, but synoptic forcing remains part of the signal.

### 19.39 Findings 191–195 — dominant source edges reproduce between years

The strongest median pairwise correlation at each station was recalculated independently by calendar year.

**Table 125 — annual stability of the dominant multigas edge** (from `outputs/ab_yearly_stability.csv`)

| Station | Dominant pair | Years | Median *r* | Minimum | Maximum | Same sign |
|---|---|---:|---:|---:|---:|---:|
| BKT | CH₄–CO | 12 | 0.576 | 0.269 | 0.997 | 100 % |
| JMB | CH₄–CO | 3 | 0.561 | 0.548 | 0.599 | 100 % |
| KMY | CO₂–CO | 3 | **0.875** | 0.873 | 0.891 | 100 % |
| PLU | CH₄–CO | 6 | 0.390 | 0.204 | 0.566 | 100 % |
| SRG | CO₂–CH₄ | 3 | 0.471 | 0.461 | 0.558 | 100 % |

Jakarta’s combustion edge is exceptionally stable. All five dominant edges retain their sign, but three-year records establish repeatability only over three annual realisations.

> The dominant pair was selected on median magnitude. This is a stability test of sign and range, not an independent source attribution.

### 19.40 Findings 196–200 — fixed-hour sampling is a large, site-specific operator

Each hour’s median difference from that day’s available 24-hour mean quantifies the bias imposed by a once-daily observing schedule.

**Table 126 — fixed-hour CO₂ sampling bias** (from `outputs/ab_fixed_hour_bias.csv`)

| Station | Days | Least-biased hour | Bias | Most-biased hour | Bias | Full span |
|---|---:|---:|---:|---:|---:|---:|
| BKT | 2,656 | 20:00 | −0.53 | 14:00 | −11.48 | 20.82 ppm |
| JMB | 637 | 22:00 | −0.50 | 07:00 | +24.71 | **43.60 ppm** |
| KMY | 701 | 22:00 | +0.49 | 06:00 | +17.55 | 29.21 ppm |
| PLU | 1,481 | 20:00 | **−0.06** | 06:00 | +18.25 | 36.11 ppm |
| SRG | 633 | 09:00 | −0.51 | 07:00 | +9.99 | 18.83 ppm |

There is no universal representative hour. Afternoon sampling is intentionally representative of the mixed regional background, not of the daily mean; the two objectives require different clocks.

> The daily mean uses available hours and therefore inherits gaps. These biases diagnose sampling design; they do not imply that 20:00–22:00 is the correct time for regional-background work.

# Part VIII — What to do next

## 20. Recommendations

These draw on all six preceding parts and are ordered by how soon they matter, not by how interesting they are. The first five are conditions on using the archive at all; the last four come out of Part VI and are about what to claim.

**Immediate, before any further use of this archive:**

1. **Resolve the time base.** Confirm against station logbooks and the acquisition-system changelog that BKT is stamped in local time (WIB) to 31 Dec 2020 and UTC from 1 Jan 2021, and that the four other sites are UTC throughout. Republish with an explicit, uniform, per-record timezone field. The flask comparison (Section 4.1) makes this near-certain; the logbook makes it documented.
2. **Withdraw the pre-2019 BKT CO series from trend products**, or reprocess it against the flask record. Section 4.3 shows a 10–41 ppb positive bias that steps out in 2019.
3. **Declare units in the files**, and stop shipping a `co2`/`ch4` "wet" field that carries no water-vapour information (Section 1.3).
4. **Apply the BKT CO₂ episode correction in Section 12.2**, or re-derive it from the calibration-cylinder response for Dec 2020 – Jun 2021. Reject Oct–Nov 2013 CO₂ *and* CH₄ outright.
5. **Re-examine Sorong before June 2023.** The pre-2023 record fails baseline-continuity checks on all three species.

**Instrumentation and programme:**

6. **Protect and extend the NOAA flask programme at Bukit Kototabang, and start one at Bariri.** Section 15.1 is the argument: without co-located flasks this report could not have made a single absolute statement, and it reached a wrong conclusion in their absence. Bariri is the network's reference site and currently has no external anchor at all.
7. **Install a ceilometer or routine radiosonde at Jambi and Kemayoran.** Sections 7.3 and 8.1 are limited by one unmeasured quantity — nocturnal layer depth. Supplying it would give Indonesia a direct, continuous measurement of drained-peat CO₂ efflux and of Jakarta's methane flux from instruments already deployed.
8. **Add δ¹³C-CH₄ or ethane at Kemayoran.** Section 7 establishes that Jakarta's methane is not from combustion; isotopes or ethane would split the remaining ~97 % between landfill, wastewater and gas-distribution leakage.

**Scientific follow-up, in order of expected value:**

9. **Publish the Jambi drained-peat result (Section 8).** A dry-season respiration maximum in antiphase with an intact-forest reference, at twice the magnitude, is a continuous atmospheric measurement of peatland carbon loss available on quiet nights, without waiting for a fire. Pair it with water-table records from the Jambi peat domes.
10. **Publish the SF₆ transport attribution (Section 10).** An *r* = 0.99 correspondence between methane's seasonal cycle and an inert tracer's, at a tropical station, settles a question that is usually left open, and the same framework applies at any GAW site with a flask programme.
11. **Publish the 2023 growth-anomaly result (Section 12.3).** Two independent equatorial stations agreeing to 0.04 ppm yr⁻¹ on the El Niño CO₂ response is a contribution from a region that is normally a gap in the global network.
12. **Adopt ΔCH₄/ΔCO < 0.15 as an operational peat-fire flag** at Bukit Kototabang (Section 9.4). Calibration-independent, one instrument, 17 seasons separated without error.
13. **Track ΔCO/ΔCO₂ at Kemayoran annually** (Section 6.3). It would register a change in fleet combustion efficiency within a year.
14. **Split the network's reference anchor by species:** Bariri for CO₂ and CH₄, Sorong for CO (Section 11).
15. **Report Bukit Kototabang's methane enhancement in its GAW metadata.** +22.4 ± 2.6 ppb over the regional forest reference in well-mixed afternoon air (Section 11) is not consistent with an unqualified "global background" designation for CH₄. The 30.9 % NOAA CO₂ rejection rate (Section 4.5) belongs in the same note.
16. **Raise Jambi's data return before anything else in the network.** At 74.9 % median CO₂ return (Finding 79) the station carrying the network's most policy-relevant signal — a measured, monetisable peatland carbon loss — cannot support an annual statement (Finding 95). This is a maintenance problem, not a scientific one, and it is the cheapest large gain available.
17. **Attach a rectifier correction to any flux-based use of these data** (Finding 94). The afternoon sampling bias is 100–476 % of the enhancement being measured and has a fixed sign, so it does not average out. Only a continuous station can supply the correction.
18. **Do not offer this network as national-scale verification under NEK** (Finding 100). Offer it as what Findings 92 to 95 show it to be: a city-scale sectoral check, a peatland emission-factor check, and an independent test of whether an inventory is consistent with the physics of the air above it.
19. **Extend the eastward CH₄ transect** (Section 10.5). A fourth clean site in eastern Java or Kalimantan would sharpen both the amplitude and the phase gradient.

---

## Appendix A — Reproducing this analysis

**The formulas behind every number in this report are set out in the companion document `GHG_Analysis_Methods.md`**, which derives each technique, explains why it was chosen over the alternatives, and works four headline results end to end from the raw files. Its final table maps every finding to the section that derives it.

```
scripts/ghg_common.py        loading, unit harmonisation, QC, time-base correction,
                             suspect-period flags, harmonic fitting, palette
scripts/noaa_flask.py        reader for the NOAA GML CCGG flask products
scripts/i18n.py              figure localisation (see below)

Build
  a0_build.py         the cached hourly frame every -> all.pkl, station_hours.csv
                      other script reads: raw JSON,
                      units, QC, time base, flags

Analyses
  a1_ratios.py        nightly emission ratios       -> nightly_emission_ratios.csv
  a2_trends.py        baselines, growth, ENSO       -> trends.csv, bkt_annual_co.csv,
                                                       bkt_vs_plu.csv
  a4_summary.py       station summary table         -> station_summary.csv
  a6_bkt_co2_fix.py   BKT CO2 fault diagnosis       -> bkt_co2_offsets.csv,
                                                       bkt_co2_corrected.pkl
  a7_extra.py         weekly cycle, nocturnal flux, -> x_*.csv  (8 tables)
                      growth anomalies, ladder,
                      seasonal CIs, fire ratios,
                      CO decay, forcing
  a9_process.py       morning erosion, respiration  -> y_*.csv  (5 tables)
                      seasonality, CH4 phase,
                      CO levels, fossil bound
  a11_flask.py        flask vs in-situ, drift, QC,  -> z_*.csv  (10 tables)
                      flask trends, latitude
                      structure, SF6 attribution,
                      plume ratios
  a13_trends_enso.py  growth acceleration, decadal  -> w_*.csv  (6 tables)
                      split, ENSO lag scan,
                      hemispheric gradient trends,
                      CO transport/local partition,
                      air-mass-corrected plume ratios
  a15_carbon.py       paired morning decay rates,   -> v_*.csv  (4 tables)
                      the CO2/tracer ratio by day
                      and by night, carbon-budget
                      conversions
  a17_extra2.py       fire severity and return       -> u_*.csv  (11 tables)
  a22_roni.py         ONI vs RONI, index skill,      -> r_*.csv  (4 tables)
                      and the TCR warming closure
  a24_extra3.py       rectifier, Idul Fitri, effective -> s_*.csv  (8 tables)
                      DOF, detectability, covariance
                      and the TCR warming closure
                      periods, monsoon onset,
                      Jakarta hour by hour, marine
                      comparison, coherence, CO
                      memory, N2O, H2, seasonal
                      amplitude, null tests
  a26_extra4.py       flask pair precision, SF6 clock, -> t_*.csv  (10 tables)
                      vertical gradients, H2 cycle,
                      PLU vs BKT, SRG marine, Jakarta
                      rush hour, N2O ENSO, N2O decadal
                      acceleration, drained peat diurnal
  a28_extra5.py       lat/lon Hovmöller dynamics,      -> t_*.csv  (10 tables)
                      SF6 2-box exchange time, ENSO
                      growth asymmetry, CH4 gradient
                      evolution, vertical damping,
                      covariance matrix, clean CO floor,
                      nocturnal monsoon, regional forcing
  a30_extra6.py       CO2e ladder, data return, clean  -> p_*.csv  (12 tables)
                      fraction, species coupling,
                      persistence, in-situ vs flask
                      growth, nocturnal rate, CH4:CO2
                      signature, weekend CO2e, global
                      coupling, detectable step,
                      amplitude stability
  a31_nek.py          the carbon economic value: peat  -> k_*.csv  (11 tables)
  a33_extra7.py       network information/robustness   -> q_*.csv  (20 tables)
  a34_extra8.py       advanced multivariate structure  -> aa_*.csv (30 tables)
  a35_extra9.py       transitions, regimes, tails,     -> ab_*.csv (10 tables)
                      memory and sampling bias
                      and methane priced, sectoral
                      split, verifiable abatement,
                      rectifier bias, station roles,
                      uncertainty budget, permanence,
                      reversal risk, verification
                      modes, the national-scale limit

Figures
  a3_figures.py       f1-f8      a8_extra_figs.py     f10-f12
  a6_bkt_co2_fix.py   f9         a10_process_figs.py  f13
                                 a12_flask_figs.py    f14-f16
                                 a16_carbon_figs.py   f17
                                 a18_extra2_figs.py   f18-f19
                                 a23_roni_figs.py     f20
                                 a25_extra3_figs.py   f21-f22
                                 a27_extra4_figs.py   f23-f24
                                 a29_extra5_figs.py   f25-f26
                                 a32_nek_figs.py      f27-f28

Publishing
  a5_publish.py [markdown-file]  -> outputs/ghg_report.html
  check_docs.py                  -> structural checks on both documents
  check_pdf.py  [pdf ...]        -> layout checks on the rendered PDF pages
  verify_all.sh                  -> every gate: docs, translations, PDF, decks
  a14_latex.py  [markdown-file]  -> outputs/latex/*.tex, outputs/*.pdf
  a19_slides.py                  -> outputs/GHG_Analysis_Slides.pptx
  check_slides.py <pptx>         layout verification against the rendered deck
```

**Slides.** `scripts/a19_slides.py` builds a white-background deck, pairing findings with the methods that produced them — the two are not separable here, since several findings are findings *about* method. All 200 findings appear: the findings that carry the argument get individual or grouped result slides, and index slides list every one against its report section. It embeds the language-matched figures where they exist, and `scripts/check_slides.py` verifies the result by rendering it through LibreOffice and measuring the actual output rather than an estimate. The deck's own prose is a separate body of text from the figure labels and is currently English only; running it with `--lang id` reports how many strings still need translation rather than shipping a half-translated file.

**Verification.** `bash scripts/verify_all.sh` runs every gate this project holds itself to: `check_docs.py` for structural consistency of the two documents (findings contiguous, every figure present in both languages, every cross-reference resolving, prose counts matching), `i18n.py --audit` for translation completeness, a LaTeX build checked for overfull boxes and for stray table headers (`check_pdf.py`), and `check_slides.py` on both decks measured against the actual LibreOffice rendering. All four currently pass. What it does **not** check is whether the numbers in the prose still match the CSVs they came from — that remains a manual step and is the weakest link in this setup.

**PDF.** `scripts/a14_latex.py` converts either markdown document to LaTeX and compiles it with XeLaTeX, writing `outputs/GHG_Analysis_Report.pdf` and `outputs/GHG_Analysis_Methods.pdf` (the `.tex` sources are kept in `outputs/latex/`). Run it with no arguments to build both, or `--tex-only` to stop after the LaTeX. It needs a TeX installation on `PATH` or at `~/.TinyTeX`; the packages used are listed at the top of the generated preamble.

The converter is written for the markdown these two documents actually use rather than for markdown in general, which is what lets it lay them out properly: table column widths are computed from cell contents and expressed as fractions of the text block, so nothing reaches the margin; tables short enough for one page are set unbreakable and moved whole rather than split; figures are full-width floats with their captions attached; code blocks keep their column alignment; and the 36 non-ASCII characters in the sources are mapped to LaTeX constructs so units and formulae are typeset rather than approximated. Both documents currently compile with zero overfull boxes.

Run in order: `a0` → `a1` → `a2` → `a3` → `a4` → `a6` → `a7` → `a8` → `a9` → `a10` → `a11` → `a13` → `a15` → `a17` → `a22` → `a24` → `a26` → `a28` → `a30` → `a31` → `a33` → `a34` → `a12` → `a16` → `a18` → `a23` → `a25` → `a27` → `a29` → `a32` → `a5`. `a30` reads `x_ladder.csv` so it runs after `a7`, and `a31` reads `a30`'s output, so the order of those two is fixed. `outputs/all.pkl` is a cache, not a checkpoint — delete it and `a0` rebuilds it from the raw JSON in about a second. Requires numpy, pandas, scipy, matplotlib.

**Figure language.** Every figure script accepts `--lang`. The default is English, and the English figures are what this report embeds. Passing `--lang id` regenerates the same figures in Bahasa Indonesia, written to `<name>_id.png` so the English set is never overwritten:

```
for s in a3_figures a6_bkt_co2_fix a8_extra_figs a10_process_figs a12_flask_figs a16_carbon_figs a18_extra2_figs a23_roni_figs a25_extra3_figs a27_extra4_figs a29_extra5_figs a32_nek_figs; do
    python3 scripts/$s.py --lang id
done
python3 scripts/i18n.py --audit      # lists any string with no translation
```

Translation is handled centrally in `scripts/i18n.py`, which routes every string bound for a figure through a lookup table — the figure scripts themselves contain no language logic, so adding a language means adding one dictionary and nothing else. `--audit` re-renders every figure and reports untranslated strings; it currently reports none.

**ENSO index.** `data/oni.ascii.txt` is the NOAA CPC Oceanic Niño Index, retrieved 15 August 2026 from `cpc.ncep.noaa.gov/data/indices/oni.ascii.txt`. Each overlapping three-month season is dated to its middle month.

**Flask data.** `noaa_flask/` holds the NOAA GML CCGG surface-flask text products for Bukit Kototabang (co2, ch4, co, n2o, sf6, h2) plus monthly means for five reference sites. Retrieved 15 August 2026 from `gml.noaa.gov/aftp/data/trace_gases/<species>/flask/surface/`. These data are provided by NOAA GML (principal investigator Xin Lan) with BMKG as key partner, and are released under CC0-1.0. **Cite the product and the relevant NOAA references when using them.**

## Appendix B — Methods

**Regional background** is the 20th percentile of well-mixed afternoon hours (12:00–16:00 local) within each calendar month, requiring ≥20 valid afternoon hours. **Section 4 is the exception**: comparisons against the flask record use the afternoon *median*, because a deliberately low-biased statistic cannot be compared against an unbiased one.

**Flask matching** pairs each NOAA sample with the in-situ hour it was drawn in, averaging the two flasks of a pair and keeping only samples whose first QC character is '.'.

**Seasonal cycles** are the residual of a least-squares fit of a quadratic trend plus three annual harmonics, averaged by calendar month. Amplitude confidence intervals resample whole calendar years. Phase is the first-harmonic argument from the same fit.

**Growth rates** are Theil–Sen slopes on the seasonally-adjusted monthly background. Interannual growth anomalies are 12-month differences of the deseasonalised background on a complete monthly axis.

**Emission ratios** are per-night OLS slopes over 18:00–08:00 local, gated at ≥6 hours, ≥5 ppm CO₂ build-up and *r*² ≥ 0.70, summarised by median and IQR. Plume ratios are OLS over the episode with a bootstrap CI.

**Nocturnal fluxes** are the median 19:00–04:00 accumulation rate on coherent nights (*r* > 0.7 against time), times the barometric air molar density at station elevation, times an assumed layer depth of 100–400 m.

**Weekly-cycle tests** take the anomaly against the (calendar month, hour of day) median, aggregate to daily medians, and bootstrap 3,000 resamples of days.

**Paired decay comparison** (Section 5.3) fits the morning exponential of CO₂ and of a tracer on the *same* day, and takes the median of the per-day difference in rate constants, with a bootstrap interval over days. Pairing is essential: the unpaired medians compare different populations of mornings.

**Carbon-budget conversion** uses 1 ppm CO₂ = 2.135 Pg C, derived from the mass of the atmosphere (5.148 × 10²¹ g) and the molar masses of air and carbon, not quoted.

**SF₆ attribution** regresses each species' harmonic seasonal component at BKT on SF₆'s, and compares the slope with the same species-to-SF₆ ratio measured between reference-site pairs over 2015–2025.

**Extreme-value fitting** (Section 9.8) is a Gumbel distribution fitted to the 20 annual maxima of daily-median CO (years with at least 250 valid days, 2024 the last) by the method of moments, giving a return period 1/(1−exp(−exp(−(x−μ)/β))).

**Monsoon onset** (Section 9.8) is the first day after 1 September on which the 10-day running median of daily CO falls below that year's own median.

**Autocorrelation** (Section 9.9) is computed on the daily log-CO anomaly after removing a centred 365-day mean, and the e-folding lag is the first lag at which it falls below 1/e.

**ENSO index** is the NOAA CPC Oceanic Niño Index. Section 9.3 uses the September–November season, chosen to match the Indonesian fire season; Section 12.5 uses the full monthly series so that the response lag can be scanned rather than assumed.

**Growth-rate acceleration** is twice the quadratic coefficient of a least-squares fit `y = c₀ + c₁(t−t̄) + c₂(t−t̄)²` to the deseasonalised monthly series, with a standard error from the OLS covariance matrix.

**Air-mass correction** subtracts, from each flask sample, the product of its SF₆ anomaly and that species' measured interhemispheric gradient per ppt of SF₆, before any regression against CO. It removes the covariance between the burning season and the monsoon reversal, which at this site fall in the same months.

**Figures** use a categorical palette validated for colour-vision deficiency (worst adjacent-pair CVD ΔE 9.2 light / 9.4 dark; worst normal-vision ΔE 27.6 / 22.5), with line style and marker shape as secondary encoding so no series is identified by colour alone.

## Appendix C — Limitations

**Inferences, not documented facts:**

- The time-base correction (Section 2) is a physics-based inference confirmed by an external instrument (Section 4.1), but it is still not a documented metadata fact and should be checked against station records.
- The BKT CO₂ offsets (Section 12.2) are derived from the atmosphere, not from calibration cylinders. They are an empirical repair pending confirmation against the working-standard logs. The 2013 fault is independently corroborated by the flasks; the 2020–21 episode is not, because the flask overlap is sparse in those months.
- The Bariri (`PLU`) coordinates and elevation are approximate. The station's *identity* as montane rainforest inside Lore Lindu National Park is what the interpretation rests on.

**Unmeasured quantities:**

- **Nocturnal layer depth** (Sections 7.3, 8.1). Every absolute flux inherits a factor-of-two uncertainty, and the method under-estimates when drainage flows ventilate the layer. Ratios between stations are the robust products.
- **Meteorology** — wind, mixing height, precipitation, water table — was not available. Wind-sector analysis would separate Jakarta's methane sources spatially; water-table records would confirm the Jambi mechanism directly.

**Record lengths:**

- Jambi and Kemayoran have ~2 years — enough for diurnal, weekly, ratio and respiration-phase work, **not** enough for trends. None are quoted.
- Sorong retains 2.5 clean years after flagging and is excluded from trend analysis.
- Bariri has 4.7 years and no external calibration anchor.

**Scope:**

- The forcing tables (Section 13) are local, not global. The *shares* are the robust part.
- Only Bukit Kototabang has a flask programme. Findings 2–6 are established at that station; their extension to the other four rests on the internal consistency of the network, not on direct measurement.

**External values.** A small number of published values are quoted rather than measured here, and **each needs tracing to a primary source before publication**: emission ratios for fossil combustion (3–15 ppb ppm⁻¹), biomass burning (60–200), Indonesian peat ΔCH₄/ΔCO (0.06–0.10) and vehicle ΔCH₄/ΔCO (0.005–0.02); tropical forest ecosystem respiration (4–8 µmol m⁻² s⁻¹) and gross primary production (3,000–3,500 g C m⁻² yr⁻¹); the chemical lifetime of CO against OH (1–3 months); GWP-100 for methane (27.9) and the ~43 % indirect uplift; the global anthropogenic forcing split in Table 93; the Global Carbon Budget terms used in Section 12.7 (total emissions 11.1, ocean sink 2.9, land sink 3.2 Pg C yr⁻¹, airborne fraction 40–50 %); the global soil organic carbon pool (~1,500 Pg C to 1 m, mean residence time ~50 yr); the tropical peat store of 1,000–3,000 t C ha⁻¹ used in Section 8.4; and the identification of fertilised soils and biomass burning as the likely regional N₂O sources in Section 10.7. **Part VI adds a block of policy and price values**, all quoted and all volatile: the statutory carbon-tax floor of IDR 30,000 tCO₂e⁻¹ (Law 7 of 2021, Art. 13, at IDR 30 per kg); the IDXCarbon volume-weighted average of IDR 52,295 for June 2024 – May 2025 and its opening price of IDR 69,600 on 26 September 2023; the EU ETS April 2026 average of EUR 72; indicative exchange rates of IDR 16,300 to the US dollar and IDR 18,900 to the euro; Indonesia's Second NDC 2035 absolute range of 1,257.7–1,488.9 MtCO₂e (submitted October 2025); the four instruments of Presidential Regulation 98 of 2021; Indonesia's land area of 1.905 × 10⁶ km²; a tropical daytime boundary-layer depth of 500–2,000 m and a ventilation timescale of 0.5–3 days; and the AR6 GWP-100 values of 27.9 for CH₄, 273 for N₂O and 25,200 for SF₆, taken from the local atmospheric-science reference wiki rather than from AR6 directly. **Every price in Part VI moves; none of the measurements do, and the tables are laid out so the two can be separated.** Wherever an equivalent quantity could be measured instead — the interhemispheric gradients, the Mauna Loa and South Pole seasonal amplitudes, the absolute CO₂ and CH₄ levels — it **is** measured, from the NOAA flask network, and Section 15 records what happened the one time a quoted value was used in place of a measured one.

**Every number attributed to the in-situ dataset or to the flask record is computed from those files by the scripts in Appendix A.**
