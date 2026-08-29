# Project summary — handoff notes

> **If you are an AI agent:** read `AGENTS.md` first, then
> `.claude/skills/ghg-analysis/SKILL.md` — the operating manual, with the data
> traps, the statistical standards and the verification gates. This file is the
> project narrative; that one is the rules.

**For an agent picking this up cold.** Read §1–§3 before touching anything; §3 is the part that will cost you a day if you skip it. Everything here is verified against the current tree as of 18 August 2026.

---

## 1. What this is

Analysis of greenhouse-gas records from five Indonesian monitoring stations, validated against NOAA's independent flask programme. Two deliverables, both generated from markdown:

| Document | Source | Renders to |
|---|---|---|
| The analysis, 200 findings | `GHG_Analysis_Report.md` | `outputs/ghg_report.html`, `outputs/GHG_Analysis_Report.pdf` |
| A Jambi station deck | built by `scripts/a21_jambi_slides.py` | `Jambi/Jambi_Presentation.pptx` (+ `.pdf`, see `Jambi/README.md`) |
| A 58-slide deck | built by `scripts/a19_slides.py` | `outputs/GHG_Analysis_Slides.pptx` (+ `.pdf`) |
| Every formula and derivation | `GHG_Analysis_Methods.md` | `outputs/ghg_methods.html`, `outputs/GHG_Analysis_Methods.pdf` (29 pp) |

The markdown is canonical. HTML and PDF are both regenerated from it — never edit them directly.

**Working state: complete and self-consistent.** The full pipeline was rebuilt from raw data and verified on 17 Aug 2026: 25 analysis scripts run clean, both documents compile with zero overfull boxes, the figure translator reports zero untranslated strings, and both decks render with zero layout issues.

---

## 2. Orientation in sixty seconds

```
grk_hourly_*.json     raw hourly archive, 5 stations, 242,411 station-hours
noaa_flask/           NOAA GML flask text products (BKT + 5 reference sites)
data/oni.ascii.txt    NOAA CPC Oceanic Nino Index
data/roni.ascii.txt   NOAA CPC Relative ONI (ONI minus the tropical-mean SST anomaly)

scripts/a0_build.py   -> outputs/all.pkl        THE input to everything else
scripts/a1..a28       -> outputs/*.csv          analyses (47 tables)
scripts/a3,a8,a10,a12,a16,a18,a23,a25,a27,a29,a32 -> figures/*.png  28 figures, English + Bahasa Indonesia
scripts/a5_publish.py -> outputs/*.html
scripts/a14_latex.py  -> outputs/*.pdf
```

`outputs/all.pkl` is the hourly archive after unit harmonisation, QC gating, **time-base correction** and suspect-period flagging. Every analysis script reads it and none of them re-derive it. It rebuilds from the raw JSON in about 1.4 seconds, so delete it freely.

---

## 3. Landmines — read this section

These are properties of the data that are **not documented anywhere in the files themselves** and were each inferred, at some cost. `ghg_common.py` already handles the first three; the rest are constraints on what you may conclude.

### 3.1 The timestamps are on two different time bases

Bukit Kototabang is stamped in **local time (WIB) up to 2020-12-31** and in **UTC from 2021-01-01**. The other four stations are UTC throughout. `ghg_common.load_station` applies the correction and exposes `time_local`, `time_utc` and the raw `time`.

Confirmed externally: matching NOAA flasks to in-situ hours gives flask-minus-in-situ CO₂ of −8.50 ppm (*r* = 0.28) on the delivered stamps and **+0.31 ppm (*r* = 0.77)** on the corrected ones. This is settled; do not re-litigate it.

Getting it wrong doubles BKT's apparent CO₂ growth rate, because the "12:00–16:00 afternoon" selection silently becomes 19:00–23:00.

### 3.2 Units differ between stations

BKT reports CO and CH₄ in **ppb**; the other four report them in **ppm**. Nothing in the files declares this. Mixing them puts BKT's methane 1,000× off. Handled in `load_station`.

### 3.3 The "wet" fields are not wet

`co2`/`ch4` vs `co2d`/`ch4d` differ by 0.02–0.05 %, where real tropical air holds 2–3 % water. Both fields are effectively dry. **The archive carries no humidity information**, and a water-dilution error can be ruled out as an explanation for any offset.

### 3.4 BKT's CO is biased high before 2019

Against the flasks, the in-situ CO reads **10–41 ppb too high through 2007–2018** and agrees within a few ppb from 2019 — a step at the date the analyser complement changes.

**Do not compute a CO trend from the pre-2019 in-situ series.** Use the flask record (`a11_flask.flask_co_percentiles`), which spans 2004–2025 on one scale. Enhancement *ratios* are unaffected, because a multiplicative bias cancels — which is why the peat-fire classifier survives.

### 3.5 Two baselines exist and they are not interchangeable

- **`q20` of afternoon hours** — the regional background, used almost everywhere. Deliberately low-biased to reject plumes. Fine for any *difference*.
- **Median of afternoon hours** — used only in §4, for comparison against the flask record.

Comparing a `q20` baseline against an unbiased external mean is what produced the retracted conclusion in §14.1. If you are comparing against anything outside this archive, use the median.

### 3.6 A rolling window will step across data gaps

`rolling(13)` takes the 13th preceding **row**, not month. Across BKT's 2014–2018 gap that silently reports the level difference either side as one year's growth (+10.1 and +11.3 ppm yr⁻¹ on the first attempt). Reindex onto a complete monthly axis first, bridge gaps of one or two months, and let anything longer produce NaN. See `a7_extra.growth_anomaly`.

### 3.7 TCR is an input to Finding 47, not an output

The forcing-to-warming closure in §14.4 multiplies a measured forcing accrual by λ = TCR/*F*₂ₓ. **TCR appears on the left-hand side and not on the right**, so the agreement with observed SST warming is a consistency check on the chain, *not* an independent estimate of climate sensitivity. Inverting it would need a full forcing inventory — aerosols above all, which are the largest omitted term and of opposite sign. Do not let that claim drift in redrafting; the report states the limit explicitly and the methods repeat it.

Related: the trend in ONI − RONI is a **floor** on tropical SST warming, because CPC re-centres the ONI base period every five years specifically to remove the trend. Quote it as a lower bound, never as the tropical warming rate.

### 3.8 A long correlation is not a large sample

Before quoting any *p*-value or confidence interval from a monthly series, compute Bartlett's effective sample size, `n_eff = n(1-r1*r2)/(1+r1*r2)`. The ENSO growth-rate sensitivities in §12.5 were originally quoted with intervals built on n = 215 months; the series is a 12-month difference of a 7-month running mean correlated against an index that is itself a 3-month running mean, so `r1` is 0.92 and 0.97 and **`n_eff` is about 12** — roughly the number of ENSO events in the record. The corrected intervals are ~4× wider and none of the three sensitivities is significant at 95 % (Finding 51, §16.1). The point estimates and the lag structure are unchanged and still stand.

The annual analyses (§9.8, §16a) are unaffected because one value per year is nearly uncorrelated. **The general rule for this project: aggregate to the timescale of the phenomenon before correlating.** `a24_extra3._neff` implements it.

### 3.9 NOAA rejects 31 % of BKT's CO₂ flasks

Against 2.6 % of CH₄ from the same physical flask. Keep only samples whose first QC character is `.` (`noaa_flask.events` does this by default). Expect to discard a comparable fraction in any new CO₂ work at this site.

---

## 4. The pipeline

Run in this order. Every script is idempotent and safe to re-run.

| Script | Produces | Notes |
|---|---|---|
| `a0_build.py` | `outputs/all.pkl`, `station_hours.csv` | **run first**; rebuilds the cache from raw JSON |
| `a1_ratios.py` | `nightly_emission_ratios.csv` | nightly emission ratios |
| `a2_trends.py` | `trends.csv`, `bkt_annual_co.csv`, `bkt_vs_plu.csv` | baselines, growth, ENSO |
| `a3_figures.py` | `figures/f1`–`f8` | |
| `a4_summary.py` | `station_summary.csv` | |
| `a6_bkt_co2_fix.py` | `bkt_co2_offsets.csv`, `bkt_co2_corrected.pkl`, `figures/f9` | BKT CO₂ fault diagnosis |
| `a7_extra.py` | `x_*.csv` (8 tables) | weekly cycle, nocturnal flux, ladder, fire ratios, forcing |
| `a8_extra_figs.py` | `figures/f10`–`f12` | |
| `a9_process.py` | `y_*.csv` (5 tables) | morning erosion, respiration seasonality, CH4 phase |
| `a10_process_figs.py` | `figures/f13` | |
| `a11_flask.py` | `z_*.csv` (10 tables) | flask vs in-situ, QC, SF₆ attribution |
| `a13_trends_enso.py` | `w_*.csv` (6 tables) | acceleration, ENSO lag scan, gradient trends |
| `a15_carbon.py` | `v_*.csv` (4 tables) | paired tracer separation of photosynthesis, carbon budget |
| `a22_roni.py` | `r_*.csv` (4 tables) | ONI vs RONI, index skill against the fire metrics, the TCR warming closure |
| `a24_extra3.py` | `s_*.csv` (8 tables) | the diurnal rectifier and its use as QC, Idul Fitri, effective sample size, detectability, covariance |
| `a26_extra4.py` | `t_*.csv` (10 tables) | flask pair precision, SF₆ transport clock, vertical gradients, H₂ cycle, PLU vs BKT, clean Sorong marine baseline, Jakarta rush hour, N₂O ENSO Bartlett test, decadal N₂O acceleration, drained peat diurnal respiration |
| `a28_extra5.py` | `t_*.csv` (10 tables) | lat/lon Hovmöller dynamics, SF₆ 2-box exchange time, ENSO growth asymmetry, CH₄ gradient evolution, vertical damping, covariance matrix, clean CO floor, nocturnal monsoon, regional forcing budget |
| `a17_extra2.py` | `u_*.csv` (11 tables) | severity and return periods, monsoon onset, Jakarta hourly, marine comparison, coherence, CO memory, N₂O, H₂, null tests |
| `a30_extra6.py` | `p_*.csv` (12 tables) | accounting-facing re-expressions: CO₂e ladder, data return, background-air fraction, species coupling, persistence, in-situ vs flask growth, nocturnal rate, depth-free CH₄:CO₂, weekend CO₂e, global coupling, detectable step, amplitude stability. **Reads `x_ladder.csv`, so it runs after `a7`** |
| `a31_nek.py` | `k_*.csv` (11 tables) | the carbon economic value, Findings 90–100. **Reads `a30`'s output**, so it runs after it |
| `a33_extra7.py` | `q_*.csv` (20 tables) | information content, robustness and network design, Findings 101–120 |
| `a34_extra8.py` | `aa_*.csv` (30 tables) | multivariate, nonlinear, scale and extreme-value structure, Findings 121–150 |
| `a35_extra9.py` | `ab_*.csv` (10 tables) | boundary-layer transitions, regimes, compound tails, memory and fixed-hour sampling, Findings 151–200 |
| `a12_flask_figs.py` | `figures/f14`–`f16` | reads `w_*` and `z_*`, so runs after a13 |
| `a16_carbon_figs.py` | `figures/f17` | reads `v_*` |
| `a18_extra2_figs.py` | `figures/f18`–`f19` | reads `u_*` |
| `a23_roni_figs.py` | `figures/f20` | reads `r_*` |
| `a25_extra3_figs.py` | `figures/f21`–`f22` | reads `s_*` |
| `a27_extra4_figs.py` | `figures/f23`–`f24` | reads `t_*` |
| `a29_extra5_figs.py` | `figures/f25`–`f26` | Hovmöller dynamics, SF₆ mixing clock, vertical damping, regional forcing budget |
| `a32_nek_figs.py` | `figures/f27`–`f28` | the value and uncertainty of a monetised signal; detectability at station and national scale |
| `check_pdf.py [pdf ...]` | — | layout check on the rendered PDF pages: a longtable header with no rows under it |
| `check_slides.py` | — | geometric layout check for the deck |
| `a19_slides.py` | `outputs/GHG_Analysis_Slides.pptx` | 58-slide white-background deck; all 200 findings, each paired with its method |
| `a20_jambi_figs.py` | `Jambi/figures/j1`–`j5` | five station-specific figures for the Jambi deck |
| `a21_jambi_slides.py` | `Jambi/Jambi_Presentation.pptx` | 23-slide station deck, 8 with figures; reuses the layouts in `a19_slides.py`, including the full-width figure slide |
| `a5_publish.py [md]` | `outputs/*.html` | defaults to the report |
| `a14_latex.py [md]` | `outputs/latex/*.tex`, `outputs/*.pdf` | defaults to both documents |

Shared modules: `ghg_common.py` (loading, QC, time base, harmonic fit, Theil–Sen, palette), `noaa_flask.py` (flask reader), `i18n.py` (figure localisation).

### Bahasa Indonesia figures

Every figure script takes `--lang id` and writes `<name>_id.png`; the English set is never overwritten and remains the default. The figure scripts contain **no language logic** — `i18n.py` monkey-patches the matplotlib entry points that accept text, so adding a language means adding one dictionary.

```
for s in a3_figures a6_bkt_co2_fix a8_extra_figs a10_process_figs a12_flask_figs a16_carbon_figs a18_extra2_figs a23_roni_figs a25_extra3_figs a27_extra4_figs a29_extra5_figs a32_nek_figs; do
    python3 scripts/$s.py --lang id
done
python3 scripts/i18n.py --audit    # must report 0 untranslated strings
```

**Run the audit after any figure edit.** It re-renders everything and lists strings with no translation. It currently reports none.

---

## 5. Findings, in brief

Numbers are the finding IDs used throughout the report. Sections refer to `GHG_Analysis_Report.md`.

**Data integrity (§1–4)** — 1 time base; 2 flasks confirm it; 3 in-situ CO₂/CH₄ are on the WMO scale; 4 pre-2019 CO bias; 5 the Maritime Continent is a genuine CO₂ minimum (BKT 408.5 ppm, 5.5 below Mauna Loa, 1.4 below the South Pole); 6 NOAA's 31 % CO₂ rejection rate; **58 NOAA flask pair reproducibility** (single-flask precision is 0.15 ppm for CO₂, 0.72 ppb for CH₄, 0.49 ppb for CO, 0.14 ppb for N₂O, 0.025 ppt for SF₆, 0.64 ppb for H₂).

**Surface processes (§5–8)** — 7 morning boundary-layer erosion τ = 1.9–2.4 h at all five sites; 8 Jakarta ΔCO/ΔCO₂ = 23.5 ppb ppm⁻¹, bounding fossil CO₂ at ≤ 63 %; 9 ≳97 % of Jakarta's methane is not combustion, and only 1 of 15 weekday tests in the network is significant; 10 Jakarta's CH₄ flux ≈ 65 g m⁻² yr⁻¹; **11 Jambi is drained peat** — respiration 1.9× the forest reference *and* in antiphase with it (dry-season peak); **64 weekend traffic drop isolates Jakarta vehicular CO** (23.7 % morning rush drop; CO₂ and CH₄ diurnal amplitudes unaltered at 0.97× and 0.99×); **67 drained peatland respiration is dry-season amplified at Jambi (1.17×)** (41.7 → 48.9 ppm diurnal swing) while intact rainforest at Bariri is seasonally invariant (0.99×, 37.0 → 36.6 ppm); **76 monsoonal modulation of nocturnal canopy accumulation at BKT** (steady 16.5–16.9 ppm biogenic CO₂ respiration year-round; combustion CO accumulation drops 6.9× in dry easterly flow).

**Fire and transport (§9–11)** — 12 October 2015 monthly-median CO of 1,493 ppb; 13 ΔCH₄/ΔCO classifies a burning season with no overlap across 17 seasons; 14 plumes clear in 12–44 d, faster than OH; 15 flask CO background flat, polluted tail falling; **16 the CH₄ seasonal cycle is transport, proven against inert SF₆ at *r* = 0.99**; 17 BKT has the largest SF₆ seasonal cycle in the network; 18 CO is the only species with a local seasonal excess; 19 equatorial CO₂ amplitude is 81 % of Mauna Loa's; 26 half the CO cycle is emitted locally, peaking in the two burning seasons; **59 SF₆ is an absolute interhemispheric transport clock** (BKT lags Arctic Barrow by 6.7 months and leads South Pole by 9.0 months, measuring a 15.9-month pole-to-pole mixing time); **60 vertical gradients at 19.5°N** (Mauna Loa 3,397 m vs Kumukahi 3 m: CH₄ −16.5 ppb aloft, CO −9.1 ppb aloft; BKT sits below both in CO₂ by −5.3 and −5.7 ppm); **61 equatorial hydrogen has a bimodal seasonal cycle** (11.8 ppb harmonic amplitude, dual burning/transport peaks in March and October, June soil-sink minimum); **62 Bariri clean baseline contrast** (Bariri is 2.0 ppm lower in CO₂, 22.4 ppb lower in CH₄, and 12.5 ppb lower in CO than BKT); **63 clean Sorong marine baseline** (matches Samoa in CO₂ deficit at −3.9 ppm with +52 ppb CH₄ and +38 ppb CO); **68 latitude–time Hovmöller dynamics: CO₂ seasonal wave attenuation** (collapses from 16.39 ppm at Barrow to 3.94 ppm at BKT and 1.12 ppm at South Pole; phase delay of 1.2 months per 30° latitude); **69 SF₆ 2-box mass-balance exchange timescale τ_ex = 1.23 years (14.7 months)** from 0.399 ppt N-S gradient and 0.325 ppt yr⁻¹ secular growth; **70 longitude–time Hovmöller dynamics: trans-archipelago CH₄ wave propagation** (migrates eastward across 31° of longitude from Sumatra in Dec to West Papua in Feb at ~40 km day⁻¹); **75 pristine clean CO floor stability at BKT** (steady at 75.9 ± 2.8 ppb with zero secular trend over 22 years, p = 0.925).

**Carbon source and sink (§5.3, §8.4, §12.7)** — **29 a tracer separates photosynthesis from dilution**: CO₂ disappears faster than CH₄ or CO on the same morning at the forested sites, at the same rate at drained-peat Jambi, and *slower* at Kemayoran, where a megacity core is a net daytime CO₂ source; 30 the station's own record gives an airborne fraction of 45 %, inside the published 40–50 % band; 31 the 2023 El Niño anomaly is 4.4 Pg C yr⁻¹, larger than the global land sink; 32 Jambi's peat is losing 16.7 t C ha⁻¹ yr⁻¹, an e-folding time of 60–180 years.

**Severity, phenology and regional structure (§9.8–9.9, §11.2, §15.5)** — 33 fire severity differs by measure (2015 worst by duration, 2014 by peak) with a 2.8-year return period for a 1,000 ppb day; 34 the CO collapse dates the monsoon onset, delayed 15 d per °C of El Niño; 35 Jakarta's two ratios run in antiphase through the day; 36 the region is a CO₂ sink *and* a CO source relative to marine air; 37 coherence follows site type, not distance; 38 CO anomalies persist 19 d; 39 N₂O has a modest regional source; 40 H₂ tracks CO only in burning months; 41 dry-season amplification at lowland sites only; **42–43, 65 negative results** — fire years leave no trace in CO₂ growth, no seasonal amplitude or transport measure trends over 20 years, and **tropical N₂O growth has no significant ENSO response under Bartlett effective sample size correction** (*r* = +0.24, *n*<sub>eff</sub> = 6.3, *p* = 0.62).

**ENSO and background warming (§14)** — **44 the difference between the two CPC ENSO indices is itself a warming measurement**: ONI − RONI *is* the tropical-mean SST anomaly, warming at +0.068, +0.120 and +0.222 °C decade⁻¹ over 1950–2025, 1980–2025 and 2000–2025 (non-overlapping CIs, and a *lower bound* — the ONI's shifting 30-year base period is designed to remove exactly this); 45 the two indices assign a different ENSO class in 9 of 76 SON seasons, and in the three BKT observed (2014, 2017, 2019) the **ONI** classification matched the fire outcome and RONI's did not — so keep an operational fire warning on ONI and use RONI only for asking whether events are intensifying; **46 a null result** — the two are nearly interchangeable as *continuous* predictors, and the warming term alone has no correlation with the fire extremes (*r* = −0.03 peak, +0.07 days above 1,000 ppb), so the burning tracks ENSO variability rather than the mean state; **47 the closure** — converting the measured forcing accrual (36.8–41.6 mW m⁻² yr⁻¹) with the AR6 TCR gives +0.18 to +0.20 °C decade⁻¹ against +0.222 [+0.202, +0.242] observed, the report's only end-to-end link from mixing ratio to forcing to temperature.

**The instrument, not the atmosphere (§4.6, §7.5, §16)** — **49 the diurnal rectifier** (24-hour mean minus afternoon mean) is +8.3 to +18.3 ppm across the five stations, so afternoon-only sampling — flasks, inversions, this report's own background — understates the burden over the site by four to eight times the interhemispheric gradient; **50 a negative rectifier is a quality flag that needs nothing external**, and Sorong before June 2023 fails it at −29.2 ppm with 47 % of days negative, re-flagging by a sign test the exact period the report found from baseline continuity; **48 Idul Fitri is a natural experiment** — when Jakarta empties, rush-hour CO falls 31.5 % (*p* = 0.038) while CH₄ moves −0.1 % and CO₂ −1.0 %, reaching Findings 8 and 9 with no emission ratio at all; **51 most of *n* is not there** (see §3.8); **52 CO needs 15.5 years of record to show its own trend** against 1.4 for CO₂ and 0.4 for SF₆, so the 2021–2023 stations cannot give a CO trend before ~2036; **53 weekly flask sampling rebuilds the monthly mean to 1.51 ppm**, 65 % of one year's CO₂ growth.

**Six species together (§12.8, §12.9)** — 54 CH₄ and N₂O growth anomalies covary most tightly (*r* = +0.60) while CO and SF₆ do not covary at all (+0.07), and since SF₆'s variability is pure transport, CO's interannual variability is emission; 55 N₂O's *seasonal cycle* is 89 % transport even though its mean carries a regional source — regional but aseasonal, which points at agriculture rather than fire; 56 H₂ is rising at +1.51 [+1.16, +1.84] ppb yr⁻¹, a tropical baseline established before any hydrogen-economy deployment; 57 the CO₂ deficit widens against the South Pole (+0.74 ppm decade⁻¹) but is flat against Mauna Loa — at 0.2 °S the site tracks the Northern Hemisphere; **66 global synchrony in N₂O decadal acceleration** (+0.21 to +0.24 ppb yr⁻¹ surge post-2014 identically from 71°N to 90°S, demonstrating uniform global agricultural nitrogen forcing); **74 multi-species growth anomaly covariance structure** (CO₂–N₂O–SF₆ industrial/agricultural cluster *r* = 0.71–0.82 vs CO–CH₄ combustion cluster *r* = 0.67, with SF₆ completely decoupled from CO at *r* = 0.03).

**Trends and forcing (§12–13)** — 20 two stations resolve the 2023 El Niño CO₂ anomaly to 0.04 ppm yr⁻¹; 21 Jakarta's dome is 184 mW m⁻², 29 % methane; 22 four long-lived gases are accelerating; 23 CH₄ growth 2.6× higher in 2014–2025; 24 ENSO sensitivities with lags (CO₂ +0.82 ppm yr⁻¹ per °C at zero lag, CH₄ −10.8 at 12 months); **25 the hemispheric gradient widens for CO₂/CH₄/SF₆ but closes for CO**; 27 H₂ is a fire tracer, N₂O is not; 28 the air-mass correction recovers an otherwise invisible fire CO₂ signal; **71 interhemispheric CO₂ growth rate asymmetry peaks during El Niño** (diverges by up to ±3.5 ppm yr⁻¹ between polar boxes, lagging ONI by 4–6 months); **72 post-2014 methane resurgence is 90 % tropical in origin** (+3.6 ppb expansion in BKT − SPO out of +4.0 ppb total N-S gradient); **73 vertical damping across the trade-wind inversion at 19.5°N** (MLO free troposphere damped 18.1 % in CO₂, 12.3 % in CH₄, 14.0 % in CO vs KUM surface); **77 multi-species radiative forcing budget of Maritime Continent over pristine marine air** (net enhancement +9.72 mW m⁻², with +46.5 mW m⁻² CH₄ warming overcoming −40.4 mW m⁻² CO₂ deficit cooling).

**Accounting-facing re-expressions (§3.1, §4.8, §5.5–5.6, §6.5, §7.7, §10.14, §11.5–11.6, §12.14, §16.5–16.6)** — **78 the enhancement ladder in CO₂-equivalent** (Kemayoran +11.26 ± 0.41 ppm CO₂e over Bariri; methane 4.9–12.8 % of it, CO none, because CO has no GWP); 79 data return year by year — BKT's CO₂ exists in 12 of 25 calendar years and clears 50 % return in 9; **80 a null — the background-air fraction is 10.9–14.0 % at every site and the montane rainforest ranks last**, so a baseline station cannot be chosen this way; the afternoon selection does all the discriminating; 81 hourly anomaly coupling identifies source type (KMY CO₂–CO *r* = 0.85, JMB CO₂–CH₄ 0.65, PLU nothing above 0.39); 82 a persistence ladder (N₂O 5.9 months against ~2 for everything else, which is the site's transport memory); **83 the in-situ and flask growth rates at BKT agree, to ±0.8 ppm yr⁻¹** — the precision ceiling on every trend claim here; 84 nocturnal accumulation rates with bootstrap intervals, separated from the assumed depth; **85 the nocturnal CH₄:CO₂ ratio, the one flux quantity the layer depth cancels out of** (20.5 ppb ppm⁻¹ at Kemayoran, 17.2 % of that air's CO₂e); 86 Jakarta's weekday-minus-weekend rush excess is 1.71 ppm CO₂e — 8 % of the CO₂ against 34 % of the CO; **87 a null — BKT flask CO₂ annual growth carries 0.1 % of the global signal** while MLO and SMO through the identical pipeline give *r* = 0.86 and 0.88, so the pipeline is sound and the sampling is not; 88 the detectable step (6.10 ppm CO₂ over 12 months, 2.73 over 60; in CO₂e the network is 400× more sensitive to SF₆ than to CO₂); 89 the CO₂ seasonal amplitude is stationary but scatters by 32 % year to year.

**Nilai Ekonomi Karbon (§17)** — 90 Jambi's peat loss is 61.18 t CO₂ ha⁻¹ yr⁻¹, IDR 1.84–4.26 million ha⁻¹ yr⁻¹ across Indonesian prices; **91 Jakarta's methane value spans a factor of four on the unmeasured layer depth against 2.3 across every Indonesian carbon price — the ceilometer is worth more than the price discovery**; 92 the two atmospheric bounds split the city's 11.26 ppm CO₂e between energy (≤ 57.7 %) and waste/land use (≥ 42 %); 93 verifiable abatement is 24 % at Kemayoran and 52 % at Jambi over five years, and impossible at BKT and Sorong; **94 the diurnal rectifier is a fixed-sign crediting bias worth 100–476 % of the enhancement**, and it does not average out; 95 station fitness scored from data — Jambi carries the best signal and is the least fit, on data return alone; **96 the measurement is the smallest term in a monetised claim's uncertainty (×1.18 against ×4.0 for the layer depth)**; 97 a 25-year credit covers a third of a shallow peat store, so the liability outlives the contract; 98 reversal is 91.8 % likely within five years, from the measured 2.54-year return period; 99 what each verification mode actually verifies, stated as limits; **100 a null, and the important one — the whole width of the Second NDC 2035 range produces 0.05–1.09 ppm against a 2.73 ppm resolvable step**, so this network's NEK role is project and city scale plus a physics check on the inventory, never a national ledger.

**Advanced information, regimes and sampling (§18–19)** — Findings 101–150 establish the network’s timing loops, robustness, nonlinear dependence, effective dimension, extremal clustering and cross-station independence. **Findings 151–200 add ten station-replicated physical tests:** the 08:00–09:00 ventilation clock; nocturnal curvature with Jambi’s retained null; next-dawn carry-over from 56.2 % at BKT to effectively zero at Jambi/Sorong; methane-led monsoon distribution shifts; interpretable and failed multigas clusters; compound extremes up to 14.3× independence in Jakarta; event-composition ageing; surrogate-tested daily CO memory at all sites; annual source-edge reproducibility; and fixed-hour CO₂ biases spanning 18.83–43.60 ppm. The external-data ideas—wind sectors, observed PBL depth, IOD/MJO and satellite columns—remain proposals rather than findings.

---

## 6. Already tried and found wrong — do not redo

Recorded in `GHG_Analysis_Report.md` §14. These were real conclusions in earlier drafts, corrected after the flask data arrived.

| Claim | Status | Why it was wrong |
|---|---|---|
| The network's CO₂ is 5–9 ppm off-scale | **Retracted** | Compared a `q20` baseline against a quoted global mean with an assumed 1–3 ppm tolerance. The in-situ CO₂ agrees with co-located flasks to 0.31 ppm; the deficit is a real regional minimum. |
| Equatorial CO₂ amplitude is "close to the South Pole's" | **Corrected** | Rested on a quoted Mauna Loa amplitude of ~15 ppm. Measured from the flask network it is 6.86 ppm, so the equator is at 81 % of Mauna Loa, not a fifth. |
| CO over Sumatra is MJO-modulated | **Not supported** | 25 % of variance sits in the 20–90 d band but there is no discrete spectral peak; it is red noise from fire-episode relaxation. Reported as a negative result. |
| Gumbel return periods of 1.4 / 2.8 / 8.8 / ~120 yr (§9.8) | **Corrected** to 1.67 / 2.54 / 7.21 / 81.31 | The *fitted parameters* printed beside the table were right and reproduce the correct column exactly; the return periods derived from them were not, and the text said 24 annual maxima where the fit uses 20. The table cited no CSV, so `check_sourced_tables` could not see it. Found only when Finding 98 needed the number and read it from `u_return.csv`. Report §15.7. |

**The generalisable lesson:** a differential network cannot be validated against a single global scalar plus an assumed tolerance. It can only be validated against a co-located measurement on a traceable scale. Wherever a quantity *can* be measured from the NOAA network rather than quoted, it is.

---

## 7. Conventions to preserve

- **Palette and encoding.** `ghg_common.COL/MRK/LS` — a CVD-validated categorical set, with marker shape and line style as secondary encoding so no series is identified by colour alone. Reuse it; don't introduce new colours.
- **Robust statistics throughout.** Theil–Sen for trends, medians and IQRs for populations, bootstrap CIs where the statistic has no clean analytic distribution. The resampling *unit* is chosen per application (days for weekly cycles, whole years for seasonal amplitudes) — see Methods §7.
- **Derive rather than quote where you can.** The ppm-to-Pg C factor in §12.7 is derived from the mass of the atmosphere, not looked up; the interhemispheric gradients are measured from the NOAA network, not cited. This is a deliberate response to the §14.1 retraction.
- **Quoted external values are flagged.** Appendix C of the report lists every published value that is quoted rather than measured, each marked as needing a primary citation. Keep that list current if you add one.
- **Caveats sit with their findings**, in blockquotes, not collected at the end.
- **"Local time"**, not "local civil time" (user preference).

---

## 8. Environment

- **Python**: system `python3` (3.14) with numpy/pandas/scipy/matplotlib. A separate venv exists at `~/Playground/.venv` with **PyMuPDF** and weasyprint — useful for inspecting rendered PDFs page by page, which is how the layout bugs were found.
- **LibreOffice**: installed at **`/opt/libreoffice26.2/program/soffice`** — *not on PATH*, so `which soffice` returns nothing. Do not conclude it is missing; `check_slides.py` finds it. It renders the deck for verification and produces `outputs/GHG_Analysis_Slides.pdf`.
- **LaTeX**: TinyTeX at `~/.TinyTeX` (user-space, installed for this work; no root needed). `a14_latex.py` finds it automatically. About 30 packages installed on top of the base.
- **Network**: available. NOAA GML and CPC were both reachable; re-download instructions are in Appendix A of the report.
- **Not a git repository.** Nothing here is under version control — worth fixing before making substantial changes.

---

## 9. Open items

**Data quality, for whoever owns the archive:**

1. Confirm the time base against station logbooks and republish with an explicit per-record timezone field.
2. Withdraw the pre-2019 BKT CO series from trend products, or reprocess it against the flasks.
3. Declare units in the files; stop shipping a "wet" field that carries no water-vapour information.
4. Re-examine Sorong before June 2023 — it fails baseline continuity on all three species *and* has a physically impossible diurnal rectifier (−29.2 ppm, 47 % of days negative; Finding 50). Two independent tests agree the period is unusable.

**Analysis that the current data supports but has not been done:**

5. The BKT CO₂ empirical repair (§12.2) is derived from the atmosphere, not from calibration cylinders. It should be checked against the working-standard logs for Dec 2020 – Jun 2021.
6. Bariri has no external calibration anchor at all. Findings 2–6 are established only at Bukit Kototabang; their extension to the other four rests on network internal consistency.
7. Nocturnal layer depth is assumed, not measured — every absolute flux carries a factor-of-two uncertainty. A ceilometer at Jambi or Kemayoran would convert §7.3 and §8.1 from indicative to quantitative.
8. δ¹³C-CH₄ or ethane at Kemayoran would split the ~97 % non-combustion methane between landfill, wastewater and gas leakage.

**Publication-ready results** (§20 of the report ranks these): the Jambi drained-peat result, the SF₆ transport attribution, and the 2023 growth-anomaly agreement are the three worth writing up first.

---

## 10. If you change something

- **Run `bash scripts/verify_all.sh` before calling anything done** — document consistency, figure translations, PDF compilation *and page layout*, and deck rendering; all four must pass.
- Edit the **markdown**, then re-run `a5_publish.py` and `a14_latex.py` for that document.
- Edit a **figure**, then re-run its script in both languages and `i18n.py --audit`.
- Edit the **deck**, then re-run `a19_slides.py` and `check_slides.py`. The checker renders the deck through LibreOffice and measures the **actual** output — text outside the frame, text over an image, colliding blocks — falling back to a font-metric estimate only if LibreOffice is absent. Both modes currently report zero issues. The estimate alone missed three real problems that only the rendering showed: a table with no rules, captions drifting away from their figures, and an index slide using half the page.
- Change an **analysis**, then re-run from `a0_build.py` forward and check the numbers quoted in the markdown still match the CSVs. Nothing cross-checks prose against data automatically — that is the weakest link in this setup.
- The PDF converter (`a14_latex.py`) is written for the markdown subset these two documents use, not for markdown in general. If you introduce new constructs (nested lists, images inside tables, footnotes), it will need extending.
