# How every number in the report is calculated

**A companion to `GHG_Analysis_Report.md`** — the formulas, the reasoning behind each choice, and a worked path from the raw files to each headline result.

This document assumes you have the report open beside it. It is organised by *technique* rather than by finding, because most techniques are used several times; a cross-reference table at the end maps each finding back to the section here that derives it.

---

## Contents

**Table 1 — Contents and technique-to-finding guide**

| § | Technique | Used for |
|---|---|---|
| 0 | Notation and the shape of the data | everywhere |
| 1 | Unit harmonisation | Report §1.3 |
| 2 | The time base, and how it was diagnosed | Finding 1 |
| 3 | Percentile baselines | most sections |
| 4 | Harmonic fitting: trend, seasonal cycle, phase, amplitude | Findings 12, 16–19 |
| 5 | Theil–Sen trends and their confidence intervals | Findings 15, 22–25 |
| 6 | Growth rates, growth anomalies, and acceleration | Findings 20, 22, 23 |
| 7 | Bootstrap confidence intervals | Findings 9, 13, 19, 27, 28 |
| 8 | Nightly emission ratios | Findings 8, 11 |
| 9 | The nocturnal boundary-layer budget | Findings 10, 11 |
| 10 | Exponential decay fits | Findings 7, 14 |
| 11 | Flask–in-situ matching | Findings 2, 3, 4 |
| 12 | Two-endmember mixing and the SF₆ air-mass fraction | Finding 17 |
| 13 | Tracer–tracer regression and seasonal attribution | Findings 16, 18, 26 |
| 14 | The air-mass correction | Findings 27, 28 |
| 15 | Radiative forcing | Finding 21 |
| 15a | Paired tracer separation of photosynthesis | Finding 29 |
| 15b | Carbon-budget conversion | Findings 30–32 |
| 15c | ENSO indices and the warming closure | Findings 44–47 |
| 16 | Spectral variance partition | Finding 14 |
| 16a | Extreme-value fitting, phenology, autocorrelation | Findings 33, 34, 38 |
| 16b | Detectability, effective sample size, the rectifier | Findings 48–57 |
| 17 | Worked examples, end to end | four headline numbers |
| 18 | Network information and robustness | 101–120 |
| 19 | Advanced multivariate, regime and sampling methods | 121–200 |
| 20 | Finding → derivation cross-reference | — |

---

## 0. Notation and the shape of the data

Two datasets are used throughout.

**The in-situ archive.** Five JSON files, one per station, each a list of hourly records with fields `date`, `hour`, and some subset of `co2`, `ch4`, `co`, `co2d`, `ch4d`. After loading, every row is one station-hour:

**Table 2 — Symbols used throughout the methods**

| symbol | meaning |
|---|---|
| $C_i$ | the mole fraction of a species in hour $i$ (ppm for CO₂, ppb for CH₄ and CO) |
| $t_i$ | time as a decimal year, $t = Y + (d-1+h/24)/D_Y$, where $D_Y$ is 365 or 366 |
| $h_i$ | hour of day in **local time**, after the correction of §2 |

**The NOAA flask record.** Text files of individual flask analyses. Each *event* is a pair of flasks filled at the same moment, so the two analyses are averaged; a QC flag whose first character is `.` marks a sample that passed every NOAA check.

Two conventions matter for reading the formulas below.

**Percentiles are written $q_p(\cdot)$**, so $q_{20}$ is the 20th percentile.

**"Deseasonalised" always means** *the fitted seasonal cycle of §4 subtracted*, never a running mean. A running mean would remove part of the trend along with the season.

---

## 1. Unit harmonisation

The archive mixes conventions (Report §1.3). The loader applies, per station:

$$
\text{CH}_4^{\text{ppb}} =
\begin{cases}
\texttt{ch4d} & \text{BKT (already ppb)}\\[2pt]
1000 \times (\texttt{ch4d} \text{ or } \texttt{ch4}) & \text{the other four (ppm)}
\end{cases}
$$

and identically for CO. CO₂ is in ppm everywhere. The dry-air field (`co2d`, `ch4d`) is preferred, falling back to the wet field only when the dry one is absent.

**Why the dry field.** A mole fraction reported in wet air is diluted by whatever water vapour is present, $C_{\text{wet}} = C_{\text{dry}}(1 - \chi_{\mathrm{H_2O}})$. At tropical surface conditions $\chi_{\mathrm{H_2O}} \approx 0.02$–$0.03$, so the two differ by 2–3 %, which for CO₂ is 8–13 ppm — far larger than any signal in this report.

**How we know the archive's "wet" field is not wet.** Compute the ratio directly:

$$\text{median}\left(\frac{\texttt{co2}}{\texttt{co2d}}\right) = 0.99949 \text{ to } 0.99976
\quad\Longrightarrow\quad \chi_{\mathrm{H_2O}} = 0.02\text{–}0.05\,\%$$

which is two orders of magnitude below real tropical humidity. The two fields are therefore both effectively dry, and the archive carries no humidity information. This also rules out a dilution error as an explanation for any offset — a point that matters in Report §15.

**Range gates.** Physically impossible values are set to missing before anything else: CO₂ outside 340–3000 ppm, CH₄ outside 1600–15000 ppb, CO outside −30 to 6000 ppb. The gates are deliberately wide because real plumes are extreme; their job is to catch $-0.1$ ppm CO₂ and $0$ ppb CH₄, not to trim outliers.

---

## 2. The time base, and how it was diagnosed

### 2.1 The physical premise

Over land the convective boundary layer is deepest in mid-afternoon and shallowest before dawn. Surface emissions are diluted into a volume proportional to the layer depth, so any surface-emitted species reaches its **minimum in mid-afternoon** and its **maximum shortly after sunrise**. This holds for CO₂, CH₄ and CO alike, and it is what makes the diurnal cycle usable as a clock.

### 2.2 Extracting the phase

For a set of hours with values $C_i$ at local hours $h_i$, fit the first diurnal harmonic:

$$C_i \approx a_0 + a_1\sin\!\left(\frac{2\pi h_i}{24}\right) + b_1\cos\!\left(\frac{2\pi h_i}{24}\right)$$

by least squares. The hour of the maximum is

$$h_{\max} = \frac{24}{2\pi}\,\operatorname{atan2}(a_1, b_1) \pmod{24}$$

**Why the first harmonic rather than "the hour with the largest median".** The argmax of a noisy 24-point composite jumps around by hours when two adjacent hours are nearly equal. The harmonic phase uses all 24 points, is continuous, and has a well-defined uncertainty. It is also the right descriptor for a cycle that is close to sinusoidal, which the diurnal cycle is once the sharp morning collapse is smoothed by monthly averaging.

### 2.3 The diagnosis

Computing $h_{\max}$ quarter by quarter for BKT's CO₂ gives 2.2–3.6 h for every quarter from 2010Q1 to 2020Q4 and 18.7–20.4 h for every quarter from 2021Q1 onward. The jump is

$$\Delta h = 20.2 - 3.6 = 16.6 \text{ h} \equiv -7.4 \text{ h} \pmod{24}$$

and WIB is UTC+7. A quantity stable for eleven years does not move by exactly one time-zone offset on 1 January by accident.

### 2.4 The correction applied

$$
t^{\text{local}} =
\begin{cases}
t^{\text{stamp}} & \text{BKT, } t < \text{2021-01-01}\\
t^{\text{stamp}} + 7\,\text{h} & \text{BKT, } t \geq \text{2021-01-01}\\
t^{\text{stamp}} + u \,\text{h} & \text{other stations}
\end{cases}
$$

with $u = 7$ (JMB, KMY), $8$ (PLU), $9$ (SRG). UTC is then recovered as $t^{\text{utc}} = t^{\text{local}} - u$.

§11 shows how the flask record confirms this from outside.

---

## 3. Percentile baselines

Three different baselines appear in the report and they are **not interchangeable**.

### 3.1 The regional background — $q_{20}$ of afternoon hours

$$B_m = q_{20}\big(\{C_i : i \in \text{month } m,\ 12 \le h_i \le 16\}\big), \qquad n_m \ge 20$$

**Two selections, two jobs.** Restricting to 12:00–16:00 selects the deep, well-mixed layer, which removes the nocturnal accumulation of *local* sources. Taking the 20th percentile of what remains removes *advected plumes*, which are additive and one-sided. Requiring at least 20 valid afternoon hours in the month stops a percentile being computed from three points.

**Why 20 and not 10 or 50.** The 50th percentile still contains plume influence at polluted sites; the 10th percentile is noisy with ~100 afternoon hours per month. 20 is a compromise, and every result that uses it is a *difference* between stations or months, so a consistent low bias cancels.

### 3.2 The afternoon median — for absolute comparisons only

Report §4 compares against the flask record, and there the low bias of $q_{20}$ is fatal: you cannot compare a deliberately low-biased statistic against an unbiased one. So §4 uses

$$M_m = \operatorname{median}\big(\{C_i : i \in \text{month } m,\ 12 \le h_i \le 16\}\big)$$

**This distinction is the single most important methodological point in the report.** Using $q_{20}$ against an external mean is what produced the retracted conclusion in Report §15.1.

### 3.3 Episode baselines — $q_{10}$ within a window

For plume ratios (§8, §14) the baseline is the 10th percentile *of the same window being analysed*, so that the enhancement $\Delta C = C - q_{10}(C)$ is measured against contemporaneous clean air rather than a fixed number. This makes the ratio immune to any slow drift or offset in the instrument.

---

## 4. Harmonic fitting

Almost every seasonal quantity comes from one function. Given $(t_i, y_i)$ with $t$ in decimal years, fit by least squares:

$$y_i = T(t_i) + S(t_i)$$

$$T(t) = \sum_{k=0}^{P} c_k (t - \bar t)^k \qquad\text{(the trend)}$$

$$S(t) = \sum_{k=1}^{H} \left[\alpha_k \sin(2\pi k t) + \beta_k \cos(2\pi k t)\right] \qquad\text{(the seasonal cycle)}$$

with $P = 2$ (quadratic) and $H = 3$ (three annual harmonics) throughout.

**Why a quadratic trend.** A linear trend forces curvature into the seasonal terms, which biases the amplitude. A cubic starts fitting interannual variability. Two is enough to absorb the real acceleration (§6.3) without eating the signal.

**Why three harmonics.** One harmonic is a pure sinusoid and cannot represent an asymmetric cycle — and these cycles *are* asymmetric, with a sharp drawdown and a slow recovery. Three resolves that asymmetry; more begins fitting month-to-month noise given ~12 points per year.

**Why $\sin(2\pi k t)$ and not $\sin(2\pi k \cdot \text{doy}/365)$.** Because $t$ is already in years, $2\pi k t$ advances by exactly $2\pi k$ per year, so the harmonics stay phase-locked to the calendar across the whole record with no leap-year drift.

Three quantities are read off the fit:

**Seasonal component**, used as a series:
$$S_i = \sum_{k=1}^{3}\big[\alpha_k \sin(2\pi k t_i) + \beta_k \cos(2\pi k t_i)\big]$$

**Peak-to-peak amplitude**: average $S_i$ by calendar month to get $\bar S_1 \ldots \bar S_{12}$, then
$$A = \max_m \bar S_m - \min_m \bar S_m$$

**First-harmonic phase**, as a day of year:
$$\text{DOY}_{\max} = 365.25 \times \left[\frac{1}{2\pi}\operatorname{atan2}(\alpha_1, \beta_1) \bmod 1\right]$$

**Why phase uses only the first harmonic.** The higher harmonics describe the *shape* of the cycle, not when it peaks. Mixing them into a phase estimate makes it sensitive to shape changes that have nothing to do with timing — and timing is what Finding 12's eastward lag is about.

---

## 5. Theil–Sen trends

For a trend the report uses the Theil–Sen estimator rather than least squares:

$$\hat\beta = \operatorname{median}\left\{ \frac{y_j - y_i}{t_j - t_i} : i < j \right\}$$

the median of all $\binom{n}{2}$ pairwise slopes.

**Why not ordinary least squares.** OLS minimises squared residuals, so a single bad month — and these records have several, see Report Table 8 — moves the fitted slope in proportion to its own size. Theil–Sen has a breakdown point of about 29 %: up to that fraction of the data can be arbitrarily wrong before the estimate is. Given that a real analyser fault put one month 20 ppm low, this matters.

**The confidence interval** is the distribution-free Theil–Sen interval: rank the $N = \binom{n}{2}$ pairwise slopes, and take order statistics at

$$k_{\text{lo}} = \frac{N - C_\alpha}{2}, \qquad k_{\text{hi}} = \frac{N + C_\alpha}{2}, \qquad
C_\alpha = z_{1-\alpha/2}\sqrt{\frac{n(n-1)(2n+5)}{18}}$$

which is the Kendall-$\tau$ variance. It assumes independent residuals — monthly baselines are close enough to independent for that to be reasonable, though serial correlation would widen the intervals somewhat.

---

## 6. Growth rates, growth anomalies, and acceleration

Three different questions, three different calculations.

### 6.1 The mean growth rate over a period

Deseasonalise, then Theil–Sen:

$$\hat\beta = \text{Theil–Sen}\big(t_m,\; B_m - S_m\big)$$

Removing the seasonal cycle first matters when the period is not a whole number of years: a record starting in March and ending in September would otherwise have the difference between those two months' climatology folded into the trend.

### 6.2 The year-by-year growth anomaly

$$g(t) = \tilde B(t + 6\ \text{mo}) - \tilde B(t - 6\ \text{mo})$$

a centred 12-month difference of the deseasonalised background $\tilde B$.

**Why a 12-month difference and not a derivative.** A 12-month difference is exactly what "annual growth" means, and it automatically annihilates any residual annual cycle the harmonic fit left behind.

> **A trap this hits, and the fix.** If the series is indexed by *available* months, `rolling(13)` takes the 13th preceding **row**, not the 13th preceding **month**. Across BKT's 2014–2018 gap that means differencing 2013 against 2019 and calling it one year's growth — which produced spurious values of +10.1 and +11.3 ppm yr⁻¹ on the first attempt. The fix is to reindex onto a complete monthly axis first, interpolate gaps of one or two months, and let anything longer produce NaN and kill the window.

### 6.3 Acceleration

Fit a quadratic to the deseasonalised series:

$$y(t) = c_0 + c_1 (t - \bar t) + c_2 (t - \bar t)^2$$

Then

$$\text{growth at the midpoint} = c_1, \qquad \text{acceleration} = \frac{d^2 y}{dt^2} = 2c_2$$

with standard error $\operatorname{se}(2c_2) = 2\sqrt{\left[\sigma^2 (X^\top X)^{-1}\right]_{22}}$, where $\sigma^2$ is the residual variance with $n-3$ degrees of freedom and $X$ is the design matrix $[\mathbf{1},\ (t-\bar t),\ (t-\bar t)^2]$.

**Worked example — CO₂ at BKT.** Over 233 monthly flask medians spanning 2004–2025, the fit gives $c_1 = +2.334$ ppm yr⁻¹ and $c_2 = +0.0223$ ppm yr⁻², so the acceleration is $2c_2 = +0.0446$ ppm yr⁻² with a 95 % interval of $\pm 0.0210$. The interval excludes zero, so the growth rate is genuinely increasing — by about 0.45 ppm yr⁻¹ per decade.

**Why centring at $\bar t$ matters.** Without it, $c_1$ is the growth rate at $t = 0$ (the year 0 AD), and the columns of $X$ are so nearly collinear that the covariance matrix is numerically useless. Centring makes $c_1$ the growth rate at the middle of the record, which is the interpretable quantity, and conditions the fit.

---

## 7. Bootstrap confidence intervals

Wherever the statistic is a median, a ratio, or anything else without a clean analytic distribution, the interval comes from a bootstrap: resample the data with replacement $B$ times, recompute, and take the 2.5th and 97.5th percentiles of the resulting distribution.

**What gets resampled is the important choice**, because it defines what the interval is an interval *over*.

**Table 3 — Bootstrap resampling units by application**

| Application | Resampling unit | $B$ | Why that unit |
|---|---|---|---|
| Weekly cycle (Finding 9) | **days** | 3000 | Hours within a day are strongly correlated; days are close to independent |
| Plume ratios (Finding 13) | **hours** | 300–400 | Each hour is a semi-independent sample of the plume |
| Seasonal amplitude (Finding 19) | **whole calendar years** | 400 | Carries interannual, not month-to-month, uncertainty |
| Air-mass-corrected ratios (Findings 27, 28) | **flask events** | 400 | Events are weekly and independent |

**The seasonal-amplitude case is worth spelling out**, because it is the one where the naive choice is badly wrong. Resampling months would ask "how well do I know this amplitude given these months?" — but the months are not the uncertainty. The uncertainty is that *this year's* cycle differs from *next year's*. So the block bootstrap resamples whole years with replacement, reassigning each drawn year to a slot on the time axis, and refits. That is why the intervals in Report §10.5 are wide: with 3–11 years, interannual variability genuinely does not pin the amplitude down.

---

## 8. Nightly emission ratios

### 8.1 The idea

At night the boundary layer is shallow and stably stratified, so surface emissions accumulate in a roughly fixed volume over a roughly fixed footprint. If two species come from the same source mix, both accumulate in proportion to their emission rates:

$$C_X(t) = C_X^0 + \frac{E_X}{n_{\text{air}} h(t)}\,t, \qquad C_Y(t) = C_Y^0 + \frac{E_Y}{n_{\text{air}} h(t)}\,t$$

Eliminating time,

$$\boxed{\ \frac{\Delta C_X}{\Delta C_Y} = \frac{E_X}{E_Y}\ }$$

**Everything unknown cancels.** The layer depth $h$, its evolution through the night, the air density, the footprint area, and both absolute backgrounds $C^0$ all disappear. What survives is the emission ratio of the surface source mix — which is why these ratios are unaffected by the calibration questions of Report §4, and why the peat-fire classifier of Finding 13 survived the discovery that BKT's pre-2019 CO was biased by up to 41 ppb: a multiplicative bias scales numerator and denominator alike.

### 8.2 The gates, and why each exists

For each night (18:00–08:00 local), regress $C_X$ on $C_Y$ by OLS and keep the slope only if:

**Table 4 — Acceptance gates for nightly emission-ratio regressions**

| Gate | Value | Purpose |
|---|---|---|
| valid hours | $\ge 6$ | a slope through four points is not a measurement |
| CO₂ build-up | $\ge 5$ ppm | ensures a real accumulation, not a flat night |
| $r^2$ | $\ge 0.70$ | ensures the two species actually co-varied |

**The $r^2$ gate is doing conceptual work, not cosmetic work.** The derivation assumes a single well-mixed accumulating layer with a common source. If the wind turns, or a plume passes, or the layer ventilates, that assumption fails and the scatter shows it. Requiring $r^2 \ge 0.70$ keeps only the nights where the model applies.

**And the rejection rate is itself a measurement.** Jambi passes the CO–CO₂ test on 17 of 627 nights (2.7 %) but the CH₄–CO₂ test on 25 %. That is not a failure: it says Jambi's nocturnal CO₂ is decoupled from combustion and coupled to methane, which is the first evidence for Finding 11.

The population of surviving slopes is summarised by its median and interquartile range — not mean and standard deviation, because the distribution is skewed and heavy-tailed.

### 8.3 The fossil bound (Finding 8)

If combustion emits CO and CO₂ in ratio $R = \Delta\text{CO}/\Delta\text{CO}_2$, then an observed CO enhancement implies a fossil CO₂ enhancement of $\Delta\text{CO}_2^{\text{ff}} = \Delta\text{CO}/R$.

The measured nightly ratio at Kemayoran, 23.5 ppb ppm⁻¹, is a **lower bound on the true combustion $R$**, because the denominator $\Delta\text{CO}_2$ contains biological respiration as well as combustion. Since $\Delta\text{CO}_2^{\text{ff}}$ *decreases* as $R$ increases, a lower bound on $R$ gives an **upper** bound on the fossil fraction:

$$\Delta\text{CO}_2^{\text{ff}} \le \frac{151.8\ \text{ppb}}{23.5\ \text{ppb ppm}^{-1}} = 6.5\ \text{ppm}
\quad\Longrightarrow\quad \frac{6.5}{10.3} = 63\,\%$$

The direction of the inequality is the whole argument, so it is worth stating twice: **more biological CO₂ in the denominator means a larger true $R$, means less fossil CO₂ explains the observed CO, means the 63 % is a ceiling.**

---

## 9. The nocturnal boundary-layer budget

### 9.1 The formula

Same physical picture as §8, but now solving for the flux rather than a ratio:

$$\boxed{\ F = \frac{dC}{dt} \cdot n_{\text{air}} \cdot h\ }$$

with $F$ in mol m⁻² s⁻¹, $dC/dt$ the accumulation rate as a *mole fraction* per second, $n_{\text{air}}$ the air molar density in mol m⁻³, and $h$ the layer depth in m.

**Air density** comes from the ideal gas law with the barometric pressure at station elevation:

$$p(z) = p_0 \exp\!\left(-\frac{z}{H}\right), \qquad n_{\text{air}} = \frac{p}{RT}$$

using $p_0 = 1013.25$ hPa, scale height $H = 8400$ m, $T = 293$ K, $R = 8.314$ J mol⁻¹ K⁻¹.

**Worked example — Bariri.** Elevation 1400 m, so $p = 1013.25 \times e^{-1400/8400} = 857.5$ hPa $= 85750$ Pa, giving

$$n_{\text{air}} = \frac{85750}{8.314 \times 293} = 35.2\ \text{mol m}^{-3}$$

The median coherent-night accumulation is 2.583 ppm h⁻¹. Converting: $2.583 \times 10^{-6}$ mol mol⁻¹ per 3600 s. With $h = 200$ m:

$$F = \frac{2.583\times10^{-6}}{3600} \times 35.2 \times 200 = 5.05\times10^{-6}\ \text{mol m}^{-2}\ \text{s}^{-1} = 5.05\ \mu\text{mol m}^{-2}\ \text{s}^{-1}$$

**Annualising** to compare with ecosystem carbon numbers:

$$5.05\ \mu\text{mol m}^{-2}\text{s}^{-1} \times 12.011\ \text{g mol}^{-1} \times 3.156\times10^{7}\ \text{s yr}^{-1} \times 10^{-6} = 1915\ \text{g C m}^{-2}\text{yr}^{-1}$$

**And in mass units for methane** (Kemayoran, 55.9 ppb h⁻¹, sea level so $n_{\text{air}} = 41.6$ mol m⁻³, $h = 200$ m):

$$F = \frac{55.9\times10^{-9}}{3600}\times 41.6 \times 200 = 1.29\times10^{-7}\ \text{mol m}^{-2}\text{s}^{-1}$$
$$= 1.29\times10^{-7} \times 16.04 \times 3.156\times10^{7} = 65.4\ \text{g CH}_4\ \text{m}^{-2}\text{yr}^{-1}$$

### 9.2 What is assumed, and how much it costs

**Table 5 — Nocturnal-budget assumptions and their consequences**

| Assumption | Status | Consequence if wrong |
|---|---|---|
| The layer does not ventilate | enforced by the $r>0.7$ gate | violation makes $F$ an **under**estimate |
| Depth $h$ | **not measured** | $F$ scales linearly with $h$ |
| Footprint is uniform | assumed | affects what area $F$ represents |

**Layer depth is the dominant uncertainty and it is not measured** — no ceilometer or radiosonde accompanies the archive. That is why every flux is quoted across a 100–400 m bracket, and why the report leans on **ratios between stations** rather than absolute values: if two stations' nocturnal layers are comparable, $h$ cancels in the ratio and Jambi's factor of 1.9 over Bariri survives even if both absolute numbers are wrong by a factor of two.

**The night selection.** Nights are kept only where the rise is monotone: at least 6 valid hours spanning at least 5 hours, with $r > 0.7$ between concentration and time. This selects calm, stably stratified nights — the ones on which the model is actually true.

---

## 10. Exponential decay fits

Two findings measure an e-folding time, and both fit

$$\ln\big(C(t) - C_{\text{floor}}\big) = \ln C_0 - \frac{t}{\tau}$$

by ordinary least squares on the log, so $\tau = -1/\text{slope}$.

**Morning boundary-layer erosion (Finding 7).** For each day, $C_{\text{floor}}$ is that day's own afternoon minimum (13:00–16:00) and the fit runs over 07:00–12:00 local, in hours. Days are kept only if the initial excess exceeds 5 ppm, every point stays above the floor, and $r < -0.9$. Result: $\tau = 1.94$–$2.38$ h at all five stations.

**Fire-plume relaxation (Finding 14).** $C_{\text{floor}}$ is that year's 10th-percentile CO, the fit runs over the ~60 days after the peak on daily medians, in days. Result: $\tau = 11.9$–$43.5$ d.

**Why fit the log rather than a nonlinear exponential.** Log-linear least squares is closed-form, robust, and gives an interpretable $r$; a nonlinear fit adds a starting-value problem for no benefit at this precision. The cost is that it weights the tail more heavily than the peak, which is acceptable when the question is the decay constant rather than the peak amplitude.

**Reading the result.** Comparing $\tau = 12$–44 d against CO's 30–90 d chemical lifetime against OH is what licenses the conclusion that the plumes are cleared by transport, not chemistry: the observed removal is *faster* than the only chemical sink available.

---

## 11. Flask–in-situ matching

### 11.1 The comparison

Each flask event is assigned to the hour it was drawn in, its two flasks averaged, and paired with the in-situ value for that hour:

$$D = C^{\text{flask}} - C^{\text{in-situ}}$$

reported as a median (robust to the occasional plume caught by one instrument and not the other), a standard deviation, and the Pearson $r$ between the two series.

**The time-base test.** The same comparison is run twice — once indexing the in-situ record by `time_utc` (the corrected base of §2) and once by `time` (the delivered stamp treated as UTC). Nothing else changes. That isolates the time base as the only variable:

**Table 6 — Worked flask-versus-in-situ validation example**

| | Median $D$ | s.d. | $r$ |
|---|---|---|---|
| delivered stamp | −8.50 ppm | 14.12 | 0.28 |
| corrected | +0.31 ppm | 9.16 | 0.77 |

**Why this is decisive.** A wrong time base pairs a flask with an in-situ hour drawn from a different part of the diurnal cycle, which both biases the difference and destroys the correlation. A right one cannot do that. There is no free parameter here and no fitting — just two ways of indexing the same rows.

**Why CO improves less.** CO is dominated by short-lived plumes with structure on sub-hourly scales, so even perfectly aligned samples see genuinely different air. Its residual scatter of 42.7 ppb is atmospheric, not instrumental.

### 11.2 Detecting a bias step

The annual median of $D$ is a diagnostic in its own right:

- A year that departs and returns is a **calibration episode**. BKT CO₂ in 2013 sits at $+8.70$ ppm, in the year of the Oct–Nov analyser fault found independently in Report §12.2.
- A **step that persists** is an instrument change. BKT CO runs at $-20$ to $-41$ ppb through 2007–2018 and at $+0.6$ to $+4.3$ ppb from 2019 — a step, at exactly the date the analyser complement changes.

The ratio $C^{\text{flask}}/C^{\text{in-situ}}$ distinguishes an additive offset (ratio drifts with concentration) from a multiplicative one (ratio constant). For BKT CO the ratio sits at 0.66–0.93 before 2019 and 0.98–1.07 after, which is closer to multiplicative — consistent with a span or gain error.

---

## 12. Two-endmember mixing and the SF₆ air-mass fraction

### 12.1 Why SF₆

Sulfur hexafluoride has an atmospheric lifetime of millennia, no natural source, no chemical sink in the troposphere, and no biological cycle. It therefore has **no seasonal source term at all**. Any seasonal variability it shows at a station must be air-mass alternation. That is what makes it a control variable rather than another correlated observable.

### 12.2 The mixing fraction

Treating the air at BKT as a mixture of a Northern-tropical end member (Mauna Loa) and a Southern-tropical one (Samoa):

$$C^{\text{BKT}} = f\, C^{\text{MLO}} + (1-f)\, C^{\text{SMO}}
\quad\Longrightarrow\quad
\boxed{\ f = \frac{C^{\text{BKT}} - C^{\text{SMO}}}{C^{\text{MLO}} - C^{\text{SMO}}}\ }$$

evaluated monthly on SF₆ and averaged into a climatology. Result: $f$ runs from 0.18 in September to 1.45–1.51 in January–February.

**Values above 1 are informative, not an error.** $f > 1$ means BKT's air is *more* SF₆-rich than Mauna Loa's — so the two-endmember model is being extrapolated, and the true northern end member for this site is not the mid-Pacific but continental Asian outflow, which is closer to the sources. That is a substantive result about what the station samples in the monsoon season, and it is the reason the report uses $f$ qualitatively and does the quantitative attribution by regression instead (§13).

---

## 13. Tracer–tracer regression and seasonal attribution

### 13.1 The test

If a species' seasonal cycle at a station is caused by air-mass alternation and nothing else, then it must be proportional to SF₆'s seasonal cycle, with a constant of proportionality equal to that species' interhemispheric contrast per unit of SF₆ contrast.

Both sides are measurable.

**The observed slope** comes from regressing the two seasonal components (§4) against each other:

$$S^{\text{BKT}}_{X}(t) = m_X \, S^{\text{BKT}}_{\text{SF}_6}(t) + \varepsilon$$

**The expected slope** comes from the reference sites, with no fitting at all:

$$G_X = \frac{\overline{C^{\text{MLO}}_X - C^{\text{SMO}}_X}}{\overline{C^{\text{MLO}}_{\text{SF}_6} - C^{\text{SMO}}_{\text{SF}_6}}}$$

averaged over 2015–2025 monthly means. The diagnostic is the ratio $m_X / G_X$:

$$\frac{m_X}{G_X} \approx 1 \;\Rightarrow\; \text{transport alone}, \qquad
\frac{m_X}{G_X} > 1 \;\Rightarrow\; \text{a local source co-varies}$$

**Worked example — methane.**
$$G_{\text{CH}_4} = \frac{1899.36 - 1841.33}{10.49 - 10.21} = \frac{58.03}{0.280} = 207.3\ \text{ppb ppt}^{-1}$$
$$m_{\text{CH}_4} = 200.0 \pm 2.8\ \text{ppb ppt}^{-1}, \quad r = 0.99
\quad\Longrightarrow\quad m/G = 0.97$$

Methane's seasonal cycle at BKT is transport to within 3 %.

**Why this is stronger than a correlation.** A high correlation between two seasonal cycles proves little — everything with an annual cycle correlates with everything else with an annual cycle. What makes this a test is that the *slope* is predicted in advance, from independent data, and comes out right. The prediction could have failed at any value.

**The controls.** CO₂ gives $m/G = 0.99$ and N₂O 1.16; **CO gives 1.35**, a genuine excess. That only CO shows an excess is itself a check: a regression artefact would inflate all four species, and a transport-only atmosphere would inflate none.

### 13.2 Converting the excess to ppb (Finding 26)

$$S^{\text{transport}}_{\text{CO}}(t) = G_{\text{CO}} \cdot S_{\text{SF}_6}(t), \qquad
S^{\text{local}}_{\text{CO}}(t) = S^{\text{obs}}_{\text{CO}}(t) - S^{\text{transport}}_{\text{CO}}(t)$$

with $G_{\text{CO}} = 25.547/0.280 = 91.3$ ppb ppt⁻¹. Peak-to-peak amplitudes: observed 56.4 ppb, transport 28.3, local residual 30.6.

**Why the parts sum to more than the whole.** The two components peak in different months, so they do not add in phase; 50 % + 54 % = 104 % is arithmetic, not error.

**The check that makes it credible** is not the magnitude but the shape: the local residual peaks in **February (+16.6 ppb) and September (+13.2 ppb)** and troughs in June. Those are the two Sumatran burning windows identified independently in Report §9.3 from the raw CO climatology, and the trough is the wet season. Nothing in the SF₆ decomposition knows about fire.

---

## 14. The air-mass correction (Findings 27, 28)

### 14.1 The problem

At Bukit Kototabang the burning season and the monsoon reversal fall in the same months. A flask that caught a fire plume also arrived in a particular air mass, and both effects move CO and the other species together. A raw regression of species $X$ on CO cannot separate them, and can report a slope that is entirely air mass.

### 14.2 The correction

For each flask sample, estimate the air-mass component from its SF₆ anomaly and remove it before regressing:

$$X^{\text{corr}}_i = X_i - G_X \cdot \big(\text{SF}_{6,i} - \operatorname{median}(\text{SF}_6)\big)$$

then take enhancements over the 10th percentile of the corrected series and regress on $\Delta\text{CO}$, restricted to samples with $\Delta\text{CO} > 60$ ppb.

**Why the SF₆ median and not a trend-removed anomaly.** SF₆ trends strongly (+0.326 ppt yr⁻¹), so a raw anomaly about the record median contains trend as well as air mass. In practice the trend term is absorbed by the intercept of the subsequent regression, since it is uncorrelated with plume strength; a more careful implementation would detrend SF₆ first, and doing so changes the CO₂ slope by less than its confidence interval.

### 14.3 What it reveals

**Table 7 — Raw and SF₆-corrected fire-plume slopes**

| Species | Raw slope | Corrected slope | Reading |
|---|---|---|---|
| N₂O | −0.0103 [−0.016, −0.004] | **−0.0010 [−0.0022, +0.0001]** | the apparent signal **was** the air mass |
| CO₂ | −0.0093 [−0.025, +0.007] | **+0.0149 [+0.0096, +0.0208]** | a real fire signal, previously hidden |

**The N₂O case is the sanity check.** A negative fire slope is physically impossible — fires emit N₂O, they do not consume it — so the raw result had to be an artefact, and the correction removes it exactly as it should.

**The CO₂ case is the finding.** Inverting the corrected slope:

$$\frac{\Delta\text{CO}}{\Delta\text{CO}_2} = \frac{1}{0.0149} = 67\ \text{ppb ppm}^{-1}\quad [48,\ 104]$$

which lands in the 60–200 range for smouldering biomass and peat. So CO₂ *is* usable as a fire tracer 500 km downwind — but only after the air-mass covariance is removed, and only in a record long enough to measure that covariance.

---

## 15. Radiative forcing

Simplified band expressions, linearised for perturbations this small:

$$\Delta F_{\text{CO}_2} = 5.35 \ln\!\left(\frac{C + \Delta C}{C}\right)\ \text{W m}^{-2}$$

$$\Delta F_{\text{CH}_4} = 0.036\left(\sqrt{M + \Delta M} - \sqrt{M}\right)\ \text{W m}^{-2}$$

with $C$ in ppm and $M$ in ppb, then multiplying the methane term by 1.43 to account for its indirect effects through tropospheric ozone and stratospheric water vapour.

**Worked example — Kemayoran's dome.** $\Delta C = 10.324$ ppm on a background of 416 ppm, $\Delta M = 92.410$ ppb on 1970 ppb (the unrounded values from `x_ladder.csv`):

$$\Delta F_{\text{CO}_2} = 5.35 \ln\!\left(\frac{426.324}{416}\right) = 5.35 \times 0.024514 = 0.1312\ \text{W m}^{-2} = 131.2\ \text{mW m}^{-2}$$

$$\Delta F_{\text{CH}_4} = 0.036\left(\sqrt{2062.41} - \sqrt{1970}\right) = 0.036 \times 1.0281 = 0.0370\ \text{W m}^{-2}$$
$$\times 1.43 = 53.0\ \text{mW m}^{-2}$$

Total $131.2 + 53.0 = 184.1$ mW m⁻², methane share $53.0/184.1 = 28.8$ %.

**What this number is and is not.** It is *not* a top-of-atmosphere flux at Jakarta — forcing is set by the whole atmospheric column, and a station-scale mixing-ratio difference does not produce a station-scale flux. It is "the forcing that would result if this enhancement were global", which is the standard way of expressing a local greenhouse burden. **The shares are the robust part**, because they are ratios and the caveat cancels.

---

## 15a. Separating photosynthesis from dilution (Finding 29)

### The problem

The morning CO₂ decline has two causes and one observable. The mixed layer deepens, diluting the nocturnal store; and photosynthesis removes CO₂ outright. From CO₂ alone they are indistinguishable.

### The trick

CH₄ and CO have no photosynthetic sink. Their morning decline therefore measures **dilution alone**. Fit an exponential to each species on the same morning (§10) and take the difference of the rate constants:

$$k = 1/\tau, \qquad k_{\text{extra}} = k_{\text{CO}_2} - k_{\text{tracer}}$$

$k_{\text{extra}} > 0$ means CO₂ is disappearing faster than dilution can account for — a net biological sink. $k_{\text{extra}} < 0$ means it is disappearing more slowly, which is what a continuous daytime source does.

### Why the pairing matters

This is the part that is easy to get wrong. Taking the median $\tau$ of CO₂ over all its usable mornings and the median $\tau$ of CH₄ over all of *its* usable mornings compares two different populations, because the two species pass the quality gates on different days. Done that way the two tracers disagreed by 10–23 percentage points — more than the effect being measured. Restricting to mornings where **both** species pass, and taking the median of the per-day difference, removes that entirely:

$$k_{\text{extra}} = \operatorname{median}_{\text{days}}\left[k_{\text{CO}_2}(d) - k_{\text{tracer}}(d)\right]$$

with a 95 % interval from 2,000 bootstrap resamples of days.

### The null test, and what it limits

Run the same comparison through the **night**, when there is no photosynthesis. The CO₂-to-tracer excess ratio should be flat.

**Table 8 — Night-time null test of the tracer correction**

| Station | Change over the night | Reading |
|---|---|---|
| BKT | **+6 %** (n = 1,380) | flat; the method is clean here |
| SRG | +35 % | source ratio drifts upward |
| JMB | +87 % | drifts upward |
| PLU | +131 % | drifts upward |
| KMY | −35 % | drifts downward |

The drift is the nocturnal *source* ratio changing through the night, not a failure of dilution to act equally on both species. Its direction determines whether it helps or hurts:

- At **Bariri** the night drift is **upward**, so if it continued into the day it would push the ratio up. The observed daytime fall is therefore a **conservative** measurement of the sink.
- At **Kemayoran** the night drift is **downward**, the same direction as the result, so its magnitude cannot be trusted — though the sign is confirmed independently by both tracers.

### Why the two tracers give different magnitudes

CH₄ always gives the smaller estimate. CH₄ has a continuing daytime surface source (soil, wetland, canals), so it dilutes more slowly than a truly inert tracer and understates the CO₂ sink. CO's daytime source at the clean sites is negligible. **The CH₄ estimate is a lower bound and the CO estimate an upper bound.**

---

## 15b. Carbon-budget conversion (Findings 30–32)

### The ppm-to-mass factor, derived

No external constant is needed. The number of moles of air in the atmosphere is its mass divided by the mean molar mass of dry air; one ppm of that, as carbon, is:

$$1\ \text{ppm CO}_2 = \frac{M_{\text{atm}}}{M_{\text{air}}} \times 10^{-6} \times M_{\text{C}}$$

$$= \frac{5.148\times10^{21}\ \text{g}}{28.96\ \text{g mol}^{-1}} \times 10^{-6} \times 12.011\ \text{g mol}^{-1} = 2.135\ \text{Pg C}$$

*(The commonly quoted value is 2.12–2.13 Pg C ppm⁻¹; the small difference is whether the stratosphere and water vapour are included in $M_{\text{atm}}$. It does not matter at the precision used here.)*

### Airborne fraction

$$\text{AF} = \frac{\text{growth} \times 2.135}{E_{\text{total}}}
= \frac{2.322 \times 2.135}{11.1} = \frac{4.96}{11.1} = 45\,\%$$

The numerator is measured at Bukit Kototabang; the denominator is a published inventory total and carries ±0.9 Pg C yr⁻¹. **This works only because CO₂ is long-lived enough to be well mixed** — the same calculation on CO or on CH₄'s regional enhancement would be meaningless.

### The peat clock

$$\text{loss} = F_{\text{JMB}} - F_{\text{PLU}} = 3{,}585 - 1{,}915 = 1{,}670\ \text{g C m}^{-2}\text{yr}^{-1} = 16.7\ \text{t C ha}^{-1}\text{yr}^{-1}$$

$$\tau_{\text{store}} = \frac{S}{16.7}, \qquad S = 1{,}000\text{–}3{,}000\ \text{t C ha}^{-1} \quad\Rightarrow\quad \tau = 60\text{–}180\ \text{yr}$$

Subtracting Bariri isolates the *excess* over what an intact tropical forest soil respires, which is the part attributable to drainage. Both fluxes carry the layer-depth assumption of §9, so the difference carries it twice — but a common error largely cancels in the subtraction, which is why the ratio is quoted alongside.

---

## 15c. ENSO indices and the warming closure (Findings 44–47)

### Recovering the tropical-mean SST anomaly

CPC publishes two Niño3.4 indices. The **ONI** is the absolute SST anomaly against a 30-year climatology; the **RONI** is the same anomaly *relative* to the tropical mean:

$$\text{RONI} = A_{\text{Niño3.4}} - A_{\text{tropics}}, \qquad A_{\text{tropics}} = \text{20°N–20°S mean SST anomaly}$$

Since $\text{ONI} = A_{\text{Niño3.4}}$ by definition, the difference recovers a quantity neither file reports:

$$\boxed{\ \text{ONI} - \text{RONI} = A_{\text{tropics}}\ }$$

No modelling is involved — it is arithmetic on two published series, and it is exact wherever the two share a base period. Both files are read as overlapping three-month seasons dated to the middle month, the same convention CPC uses for plotting.

**Trend estimation.** Theil–Sen on $A_{\text{tropics}}$ against decimal year, with the confidence interval from `scipy.stats.theilslopes`. Three windows are fitted rather than one, because the null being tested is *"the rate is constant"* and a single 76-year slope would assume the answer. The windows are nested, not independent, so they are read as a monotone sequence and not as three separate tests.

> **The lower-bound argument.** CPC re-centres the ONI base period every five years on a trailing 30-year climatology. That procedure is *designed* to remove the secular trend so ENSO events stay comparable across decades — meaning the trend in $A_{\text{tropics}}$ measured this way is only the residual that outran the updates. Report Table 95 is therefore a floor on tropical SST warming, and the gap between it and the true rate depends on the update schedule, which is an administrative fact rather than a geophysical one. This is why the section reports the *acceleration* across windows as the finding rather than any single rate.

### Index skill, and why two correlation measures

Each index is correlated against the annual BKT fire metrics at the SON season, using both Pearson $r$ and Spearman $\rho$. The metrics are strongly right-skewed — one season contributes the largest daily median in the record — so Pearson is leveraged by a single point while Spearman answers "does a warmer Niño3.4 rank with a worse season" without letting 2015 set the slope. Where the two disagree, the rank correlation is the one reported as the finding.

The third comparison is against $A_{\text{tropics}}$ alone. This is the decisive test for Finding 46: if background warming drove the burning, the warming term would correlate with the fire metrics on its own. It does not ($r = -0.03$ and $+0.07$ for the two extreme metrics), which separates the ENSO signal from the trend rather than assuming they are separable.

### The forcing-to-temperature conversion

Given a forcing accrual rate $\dot F$ in W m⁻² yr⁻¹ (§15), the transient warming rate is

$$\dot T = \lambda \dot F, \qquad \lambda = \frac{\text{TCR}}{F_{2\times}}, \qquad F_{2\times} = 5.35 \ln 2 = 3.71\ \text{W m}^{-2}$$

With the AR6 assessed $\text{TCR} = 1.8$ °C (likely 1.4–2.2), $\lambda = 1.8/3.71 = 0.485$ K (W m⁻²)⁻¹.

**Worked example — Bariri.** $\dot F = 36.74 + 4.89 = 41.63$ mW m⁻² yr⁻¹ (CO₂ plus indirect-uplifted CH₄, from `x_forcing.csv`):

$$\dot T = 0.485 \times 41.63\times10^{-3} = 2.02\times10^{-2}\ \text{°C yr}^{-1} = +0.202\ \text{°C decade}^{-1}$$

and the TCR likely range carries through linearly to +0.157 to +0.247 °C decade⁻¹.

**Why TCR and not ECS.** TCR is defined for a forcing that ramps steadily while the ocean is still taking up heat, which is the situation these stations are measuring. ECS would answer a different question — the eventual warming once the ocean equilibrates — and would give a number roughly 1.7× larger that is not comparable to a 25-year observed SST trend.

**What the comparison tests.** The implied rate is set beside the *observed* $A_{\text{tropics}}$ trend for 2000–2025. TCR is an **input** to the left-hand side and absent from the right, so agreement is a consistency check on the chain (mixing ratio → forcing → temperature) and **not** an independent estimate of TCR. Inverting it would require a complete forcing inventory — aerosols above all, which are the largest omitted term and of opposite sign — and a record long enough to separate the response from internal variability.

**Known omissions, and their directions.** The accrual covers CO₂ and CH₄ only. N₂O and the halocarbons would raise it by a few per cent; the aerosol offset would lower it; ocean heat uptake is already inside TCR by construction. These are individually smaller than the ±22 % that the TCR likely range alone contributes, which is why the agreement is reported to two significant figures and no further.

---

## 16. Spectral variance partition

For the 24-year daily CO series, the variance is partitioned by period band using Welch's method:

1. Take $\ln$ of the daily median (the distribution is log-normal; a linear spectrum would be dominated by a handful of extreme days).
2. Remove a linear trend and three annual harmonics by least squares — otherwise the annual cycle leaks across the whole spectrum.
3. Interpolate gaps of up to 10 days; drop the rest.
4. Welch periodogram with 2048-point segments and 50 % overlap.
5. Integrate power over each band and express as a percentage of the total.

**Why Welch rather than a single periodogram.** Averaging over overlapping segments reduces the variance of the spectral estimate at the cost of frequency resolution — the right trade when the question is "how much variance is in this band", not "is there a line at exactly this frequency".

**Reading the result.** 25.1 % of the variance sits in the 20–90 day band, where an MJO signature would live — but there is **no discrete peak**, and a red spectrum with no peak is what broadband relaxation produces. Given the 12–44 day e-folding times of §10, that band power is the fire episodes decaying, not an oscillation. This is a negative result, and it is reported because "CO over Sumatra is MJO-modulated" is a natural hypothesis that this record does not support.

---

## 16a. Severity, phenology and memory (Findings 33, 34, 38)

### Return periods from annual maxima

Take the maximum daily-median CO in each of the 24 years and fit a Gumbel distribution by the method of moments:

$$\beta = \frac{s\sqrt{6}}{\pi}, \qquad \mu = \bar{x} - 0.5772\,\beta$$

giving μ = 426 ppb and β = 828 ppb. The return period of a level $x$ is then

$$T(x) = \frac{1}{1 - \exp\left(-\exp\left(-\frac{x-\mu}{\beta}\right)\right)}$$

**Why Gumbel and not a generalised extreme value fit.** With 24 points a three-parameter GEV would fit the shape parameter to noise. Gumbel is the two-parameter special case ($\xi = 0$) and is the conservative default for annual maxima of a bounded-below quantity. The return periods should be read as order-of-magnitude: a 2.8-year and an 8.8-year event are distinguishable, a 110-year and a 130-year one are not.

### Monsoon onset

$$\text{onset} = \min\left\{ d > \text{1 Sept} : \operatorname{median}_{10\text{d}}\!\left[\text{CO}(d)\right] < \operatorname{median}_{\text{year}}\!\left[\text{CO}\right] \right\}$$

The threshold is the year's *own* median, so a year with a high baseline is not systematically assigned a later onset. The 10-day running median suppresses single quiet days inside the burning season. Both choices matter and both were tested: an absolute threshold of 150 ppb gives dates within about a week, and a 5- or 15-day window shifts the mean by two days.

### Autocorrelation and the e-folding lag

Compute on the daily **log** anomaly, after removing a centred 365-day running mean:

$$a(d) = \ln \text{CO}(d) - \overline{\ln \text{CO}}_{365}(d), \qquad
r_L = \operatorname{corr}\left[a(d),\, a(d+L)\right]$$

and report the first lag at which $r_L < 1/e$. The log is taken because the distribution is log-normal and a handful of extreme days would otherwise set the correlation.

---

## 16b. Detectability, effective sample size, and the rectifier (Findings 48–57)

This section is about the instrument rather than the atmosphere. Three of its results revise or bound claims made elsewhere in the report.

### The diurnal rectifier

$$R = \overline{C}_{24\text{h}} - \overline{C}_{12\text{–}16}$$

computed per day on days that have both statistics, then averaged. The restriction matters: a day sampled only at night would otherwise manufacture a rectifier out of missing data.

**Why its sign is guaranteed.** Surface emissions are diluted into a layer of depth $h(t)$, which is shallow at night and deep in mid-afternoon. For a non-negative net surface source over the diurnal cycle, the mixing ratio is therefore highest when $h$ is smallest, so the 24-hour mean — which includes the night — must exceed the afternoon mean. **$R > 0$ is a theorem about the boundary layer, not a property of the instrument**, and it is invariant under any additive offset or multiplicative scale error, since both cancel in the difference (the multiplicative one to first order, and exactly for the sign).

That invariance is what makes $R < 0$ usable as a quality flag with no external reference. Its limits follow from the same algebra: a constant calibration offset is invisible to it, and so is any error that affects day and night equally. It is a first filter, not a calibration.

**The threshold used.** A period is called unphysical when $\overline{R} < 0$ *and* more than 10 % of its days are negative. Both conditions are needed: a handful of negative days is ordinary at a site with occasional daytime plumes, and it is the combination of a negative mean with a large negative fraction that no boundary layer produces.

### Idul Fitri as a natural experiment

The holiday window is $[-2, +5]$ days around 1 Syawal; the control is $[-28, -8] \cup [+11, +31]$. The gap on either side is deliberate: *mudik* departure begins before the holiday and the return is staggered over the following week, so days adjacent to the window are neither treatment nor clean control.

Each year's daily medians are divided by **that year's own control median** before pooling, so the two occurrences contribute equally and no absolute level enters. Significance is a two-sided permutation test on the difference of medians, 20,000 relabellings of the pooled holiday-and-control days.

**Why the three time windows are the experiment.** Rush hour, all hours, and night are not three tests of one hypothesis — they are the hypothesis. A traffic signal must be largest at 06–09 and absent at night; a signal that appeared uniformly across all three would indicate weather or a regional change, not vehicles. The pattern across windows carries more information than any single *p*-value in the table.

### Effective sample size

For a correlation between two autocorrelated series, Bartlett's approximation:

$$n_{\text{eff}} = n\,\frac{1 - r_1 r_2}{1 + r_1 r_2}$$

with $r_1, r_2$ the lag-1 autocorrelations of the two series. Confidence intervals and $p$-values are then computed on $n_{\text{eff}} - 2$ degrees of freedom rather than $n - 2$.

**Why this bites hardest exactly where the report used it most.** The growth rate of §6.2 is a 12-month difference of a 7-month running mean, and the ONI is itself a 3-month running mean. Both are smooth by construction — $r_1 = 0.92$ and $0.97$ — and

$$n_{\text{eff}} = 215 \times \frac{1 - 0.92 \times 0.97}{1 + 0.92 \times 0.97} \approx 12$$

Twelve is not a defect of the arithmetic; **it is approximately the number of ENSO events in a 22-year record**, which is the honest answer to "how many times has this been observed". The smoothing that makes the lag scan legible does not create information, and the original interval treated it as though it did.

**The scope of the correction.** It applies to correlations between smoothed monthly series. It does not apply to the annual results of §16a, where one value per year gives $r_1 \approx -0.1$ and hence $n_{\text{eff}} \gtrsim n$. The general lesson is to **aggregate to the timescale of the phenomenon before correlating**, which the annual analyses already did.

### Time to detect a trend

Weatherhead's expression for the record length at which a linear trend becomes distinguishable from autocorrelated noise:

$$n^{*} = \left[\frac{3.3\,\sigma_N}{|\omega|}\sqrt{\frac{1+\phi}{1-\phi}}\,\right]^{2/3}$$

where $\omega$ is the trend per unit time, $\sigma_N$ the standard deviation of the residuals about the fitted trend-plus-seasonal model of §4, and $\phi$ their lag-1 autocorrelation. The 3.3 corresponds to detection at 95 % confidence with 90 % power. Here $n^{*}$ is in months and reported in years.

The $\sigma_N/|\omega|$ ratio dominates: CO's residual scatter is 63 ppb against a trend of 1.7 ppb yr⁻¹, which is why it needs 15.5 years while SF₆ — no local source, almost pure trend — needs five months.

### Subsampling a continuous record

The continuous afternoon series is thinned to one randomly chosen afternoon hour every $k \in \{7, 14, 30\}$ days, the monthly mean is rebuilt from the survivors, and the absolute difference from the full-record monthly mean is averaged over all months. Repeating over 200 random sampling **phases** separates the error intrinsic to the method from the luck of which days the calendar happens to select — the spread across phases is small (±0.12 to ±0.27 ppm), so the reported error is a property of the sampling rate rather than of one realisation.

### Growth-anomaly covariance, and one deliberate difference

The covariance table uses the 12-month centred difference of the deseasonalised series **without** the 7-month smoothing applied in §6.2. That is a deliberate departure: smoothing is appropriate when the object of study is the *shape* of a lagged response, and inappropriate when it is the *covariance* between two series, because it inflates autocorrelation and destroys the independence the correlation is counting. Unsmoothed, $r_1 \approx 0.25$–$0.52$ and $n_{\text{eff}}$ stays between 140 and 187 of 217 — so these correlations mean what they appear to mean.

The seasonal-cycle partition regresses each species' mean annual cycle on SF₆'s. SF₆ is inert with no regional source, so its seasonal cycle can only be transport; $R^2$ is then the share of another species' seasonal cycle that transport explains. This is the same logic as §13.1, expressed as a variance share rather than in mixing-ratio units.

---

## 16c. Flask pair precision, transport lags, vertical gradients, H₂ climatology, and regional contrast

### 16c.1 Flask pair reproducibility and single-flask precision (Finding 58)

For duplicate discrete flask samples $x_1, x_2$ collected concurrently from the same manifold:
$$\Delta x = |x_1 - x_2|$$
The single-measurement standard uncertainty is estimated assuming identical independent errors:
$$\sigma_{\text{single}} = \frac{1}{n} \sum_{i=1}^n \frac{|x_{1,i} - x_{2,i}|}{\sqrt{2}}$$
Non-parametric 95th percentiles $P_{95}(\Delta x)$ define the operational rejection threshold for duplicate pair disagreement.

### 16c.2 SF₆ as an interhemispheric transport clock (Finding 59)

Given a constant global emissions accrual rate $g = \mathrm{d}[\text{SF}_6]/\mathrm{d}t \approx 0.323\text{ ppt yr}^{-1}$, spatial concentration differences $\Delta C = C_{\text{ref}} - C_{\text{site}}$ convert directly to transit time $\tau$:
$$\tau = \frac{C_{\text{ref}} - C_{\text{site}}}{g} \times 12\quad (\text{months})$$

### 16c.3 Boundary layer vs free troposphere vertical gradients (Finding 60)

Vertical differences between Mauna Loa ($3,397\text{ m}$) and sea-level Cape Kumukahi ($3\text{ m}$) at $19.5^\circ\text{N}$ are computed over simultaneous monthly flask samples:
$$\Delta z = x_{\text{MLO}}(t) - x_{\text{KUM}}(t)$$
Statistical significance is evaluated using a paired two-tailed Student's $t$-test.

### 16c.4 Harmonic climatology of equatorial molecular hydrogen (Finding 61)

The bimodal seasonal cycle of H₂ is parameterized via a two-harmonic expansion:
$$y(t) = c_0 + c_1 t + \sum_{k=1}^2 \left( a_k \cos\frac{2\pi k t}{12} + b_k \sin\frac{2\pi k t}{12} \right)$$
Harmonic amplitude $A = \max(S) - \min(S)$ where $S(m) = \sum_{k=1}^2 (a_k \cos \frac{2\pi k m}{12} + b_k \sin \frac{2\pi k m}{12})$.

### 16c.5 Diurnal rush hour and regional background contrast (Findings 62–64, 66, 67)

- **Weekday vs weekend commuter traffic** (§7.6, Finding 64): Hourly diurnal composites are partitioned into weekdays (Mon–Fri) and weekends (Sat–Sun). Morning rush-hour drop is evaluated at 07:00 local: $\Delta_{\text{rush}} = (C_{\text{wknd}} - C_{\text{wkdy}})/C_{\text{wkdy}}$.
- **Regional background baseline offset** (§11.3, §11.4, Findings 62, 63): Differences in afternoon 20th-percentile background $q_{20}$ between stations matched month by month.
- **Decadal N₂O acceleration** (§12.9, Finding 66): Theil–Sen slope difference $\Delta s = s(2014\text{--}2024) - s(2004\text{--}2013)$ across multiple latitudes.
- **Drained peat dry-season amplification** (§8.5, Finding 67): Diurnal amplitude ratio $R_{\text{dry/wet}} = A_{\text{dry}} / A_{\text{wet}}$ where $A = \max_{h} C(h) - \min_{h} C(h)$.

---

## 16d. Hovmöller dynamics, interhemispheric mixing, and vertical damping (Findings 68–77)

### 16d.1 Latitudinal wave propagation and 2D Hovmöller extraction (Finding 68)

For each latitude $\phi_i$ and species concentration $C(\phi_i, t)$:
1. Extract monthly flask series at the 6 NOAA background stations spanning $71.3^\circ\text{N}$ to $89.98^\circ\text{S}$.
2. Decompose into polynomial trend and multi-harmonic seasonal components:
   $$C(\phi_i, t) = P_2(t) + \sum_{k=1}^3 \left[ a_{i,k} \sin(2\pi k t) + b_{i,k} \cos(2\pi k t) \right] + \epsilon_i(t)$$
3. The peak-to-peak seasonal amplitude $A(\phi_i) = \max_t S_i(t) - \min_t S_i(t)$ quantifies latitudinal attenuation.
4. Construct the continuous Hovmöller field $\mathcal{H}(t, \phi)$ by bivariate linear spline interpolation on the regular grid $(t_j, \phi_k) \in [2004, 2025] \times [-90^\circ, +71.3^\circ]$.

### 16d.2 Two-box interhemispheric mass balance and exchange timescale (Finding 69)

Following Jacob (1999) and box-model formulations for transport across the ITCZ, atmospheric exchange between Northern ($N$) and Southern ($S$) hemispheres is parameterized by a two-box exchange rate constant $k_{\text{ex}} = 1/\tau_{\text{ex}}$:

$$\frac{dC_N}{dt} = \frac{E_N}{M_N} - \frac{C_N - C_S}{\tau_{\text{ex}}} - L_N$$

$$\frac{dC_S}{dt} = \frac{E_S}{M_S} + \frac{C_N - C_S}{\tau_{\text{ex}}} - L_S$$

For inert $\text{SF}_6$, $M_N = M_S = M/2$, $L_N = L_S = 0$, and Southern emissions are negligible ($E_S \ll E_N \approx E_{\text{tot}}$). Subtracting the two equations yields:

$$\frac{d(C_N - C_S)}{dt} = \frac{E_N}{M_N} - \frac{2}{\tau_{\text{ex}}}(C_N - C_S)$$

In quasi-steady secular growth, $\frac{d(C_N - C_S)}{dt} \approx 0$ and the global mean growth rate is $\dot{C} = \frac{E_{\text{tot}}}{M} = \frac{E_N}{2M_N}$. Substituting gives:

$$\tau_{\text{ex}} = \frac{C_N - C_S}{\dot{C}}$$

Using $\Delta C_{\text{NS}} = C_{\text{BRW}} - C_{\text{SPO}} = 0.399 \pm 0.053\text{ ppt}$ and $\dot{C} = 0.325\text{ ppt yr}^{-1}$ yields $\tau_{\text{ex}} = 1.23\text{ years}$ ($14.7\text{ months}$).

### 16d.3 Zonal Hovmöller propagation across the Maritime Continent (Finding 70)

Across the 5 Indonesian stations spanning $100.3^\circ\text{E} \le \lambda_i \le 131.3^\circ\text{E}$:
1. Compute the monthly 20th percentile of afternoon (12:00–16:00 local) $\text{CH}_4$: $q_{20}(\lambda_i, m)$ for month $m \in \{1, \dots, 12\}$.
2. Normalize by the annual median: $\widetilde{q}_{20}(\lambda_i, m) = q_{20}(\lambda_i, m) - \operatorname{median}_m q_{20}(\lambda_i, m)$.
3. Construct the continuous longitudinal Hovmöller field $\mathcal{Z}(m, \lambda)$ using periodic cubic spline interpolation over the annual cycle.
4. The eastward phase velocity $c_\lambda$ is determined by tracking the seasonal maximum: $c_\lambda = \frac{\Delta \lambda}{\Delta t_{\text{peak}}} \approx 15.5^\circ\text{ month}^{-1} \approx 40\text{ km day}^{-1}$.

### 16d.4 Vertical damping across the trade-wind inversion (Finding 73)

At latitude $19.5^\circ\text{N}$, evaluate harmonic seasonal expansions for surface marine boundary layer (Cape Kumukahi, $z = 3\text{ m}$) and high-altitude free troposphere (Mauna Loa Observatory, $z = 3,397\text{ m}$):

$$\mathcal{D}_{\text{vert}} = 100 \times \left(1 - \frac{A_{\text{MLO}}}{A_{\text{KUM}}}\right)\,\%$$

### 16d.5 Multi-species radiative forcing budget (Finding 77)

For background air at Bukit Kototabang relative to pristine Southern marine air at Samoa (SMO), instantaneous radiative forcing anomalies are calculated via IPCC AR6 parameterizations:

$$\Delta F_{\text{CO}_2} = 5.35 \times \ln\left(\frac{C_{\text{BKT}}}{C_{\text{SMO}}}\right) \approx 5.35 \times \frac{\Delta C}{C_0}\ \text{W m}^{-2}$$

$$\Delta F_{\text{CH}_4} = 0.036 \times \left(\sqrt{M_{\text{BKT}}} - \sqrt{M_{\text{SMO}}}\right) \times 1.43\ \text{W m}^{-2}$$

*The methane coefficient and the 1.43 indirect uplift are those of §14, not the 0.057 an earlier draft used here; using two conventions in one document overstated the net forcing by 48 % (report §15.6). Radiative-forcing constants live in one place.*

$$\Delta F_{\text{N}_2\text{O}} = 0.12 \times \left(\sqrt{N_{\text{BKT}}} - \sqrt{N_{\text{SMO}}}\right)\ \text{W m}^{-2}$$

$$\Delta F_{\text{SF}_6} = 0.57 \times \Delta S\ \text{W m}^{-2}\ (\text{with }\Delta S\text{ in ppt})$$

---

## 16e. Accounting-facing re-expressions and detection limits (Findings 78–89)

These twelve are, with three exceptions, not new measurements. They are existing
measurements expressed in a different unit, aggregated differently, or turned
into a statement about what the record can and cannot resolve. The derivations
are short because the underlying physics is derived elsewhere; what is set out
here is the conversion, and the reason each conversion is the correct one.

### 16e.1 CO₂-equivalent on a mixing ratio (Findings 78, 85, 86)

GWP is defined per unit *mass*. A station enhancement is a difference of *mole
fractions*. Converting between them is the step most often done wrong, and it is
simpler than it looks: equal mole fractions of two gases occupy equal volumes, so
the mass ratio of a 1 ppb CH₄ excess to a 1 ppm CO₂ excess is
$10^{-3}\,M_{\mathrm{CH_4}}/M_{\mathrm{CO_2}}$. Hence

$$\Delta\mathrm{CO_2e}\,[\mathrm{ppm}] \;=\; \Delta\mathrm{CO_2}\,[\mathrm{ppm}] \;+\; \Delta\mathrm{CH_4}\,[\mathrm{ppb}]\times 10^{-3}\times\frac{16.04}{44.01}\times \mathrm{GWP}_{\mathrm{CH_4}}$$

**Worked example (Finding 78, Kemayoran).** $\Delta\mathrm{CO_2} = 10.32$ ppm and
$\Delta\mathrm{CH_4} = 92.4$ ppb over Bariri. The methane term is
$92.4\times10^{-3}\times0.3645\times27.9 = 0.94$ ppm, so the total is 11.26 ppm
and methane's share is 8.3 %. Standard errors add in quadrature, the two
backgrounds being independent: $\sqrt{0.40^2 + (5.9\times10^{-3}\times0.3645\times27.9)^2} = 0.41$ ppm.

CO is deliberately excluded rather than converted. It has no GWP in the Paris
framework; it forces indirectly, through OH and ozone, and no NEK instrument
prices it. Reporting it in a column marked "not counted" is the honest form.

### 16e.2 Data return (Finding 79)

Return is finite values divided by the hours in that station's own coverage
window for the year, $(t_{\max}-t_{\min})/1\,\mathrm{h} + 1$, so a station that
began in November is not charged for the preceding ten months. It is computed
*after* the range gates of report §3 and *before* the suspect-period flags,
because the two answer different questions: how much data arrived, and how much
of it is usable.

### 16e.3 Background-air fraction (Finding 80)

The rolling background is the 20th percentile of a 30-day window of *afternoon*
hours, matched to every hour of the record by nearest time within 15 days. The
metric is $\Pr(C - C_{\mathrm{bg}} < 2\ \mathrm{ppm})$ over all hours, and again
over afternoon hours alone. The 2 ppm threshold is chosen as roughly one year's
CO₂ growth: it is the scale at which an excess starts to matter for anything
this report does.

The point of computing both columns is that the difference between them, not
either value, is the result.

### 16e.4 Hourly cross-species coupling (Finding 81)

Each species is reduced to an anomaly against its own 30-day 20th-percentile
background before correlating, so a shared seasonal cycle cannot manufacture the
correlation. Pearson and Spearman are both reported because urban plume
distributions are strongly skewed and the two coefficients answer different
questions — whether the relationship is linear, and whether it is monotone.

### 16e.5 Persistence (Finding 82)

The autocorrelation function of the residual about a fitted
quadratic-plus-three-harmonic model is evaluated at lags 0–24 months, and the
e-folding time is the lag at which it first crosses $1/e$, linearly interpolated
between the bracketing lags:

$$\tau = k - 1 + \frac{\rho_{k-1} - e^{-1}}{\rho_{k-1} - \rho_k}, \qquad \rho_{k-1} \ge e^{-1} > \rho_k$$

This is not the daily autocorrelation of §16a and the two are not comparable;
report §10.14 says so explicitly rather than reconciling them.

### 16e.6 Co-located trend comparison (Finding 83)

Both series are reduced to a Theil–Sen slope on the monthly series over a common
window beginning after the last flagged instrumental episode. The comparison is
of *slopes only*: the in-situ series is a 20th percentile and the flask series a
monthly mean, so they differ in level by construction and only their time
derivatives are comparable.

### 16e.7 Nocturnal accumulation rate and its interval (Finding 84)

Per night, an OLS slope of CO₂ against hour over 20:00–02:00 local, on nights
with at least five of the seven hours. The night identifier is the date of the
timestamp shifted back twelve hours, so a night is not split at midnight. The
interval is a 600-sample bootstrap over *nights* — the resampling unit is the
night because nights, not hours, are the independent realisations.

### 16e.8 The depth-free ratio (Finding 85)

Under a shallow nocturnal layer of depth $h$, both species accumulate as
$\mathrm{d}C/\mathrm{d}t = F/(h\rho)$, so

$$\frac{\mathrm{d}C_{\mathrm{CH_4}}/\mathrm{d}t}{\mathrm{d}C_{\mathrm{CO_2}}/\mathrm{d}t} = \frac{F_{\mathrm{CH_4}}}{F_{\mathrm{CO_2}}}$$

and $h$ cancels exactly. Nights are gated at $\mathrm{d}C_{\mathrm{CO_2}}/\mathrm{d}t > 0.2$ ppm h⁻¹
so the denominator is a real build-up, and the median over nights is taken. This
is the only flux-ratio statement in the report that does not inherit the
factor-of-two of Appendix C.

### 16e.9 Detectable step change (Finding 88)

For a difference of means between two adjacent windows of $n$ months, at 95 %
two-sided significance and 80 % power, on a series with residual standard
deviation $\sigma$ and lag-1 autocorrelation $\varphi$:

$$\delta = (z_{0.975} + z_{0.80})\,\sigma\sqrt{\frac{2}{n_{\text{eff}}}} = 2.80\,\sigma\sqrt{\frac{2}{n_{\text{eff}}}}, \qquad n_{\text{eff}} = n\,\frac{1-\varphi}{1+\varphi}$$

**Worked example (CO₂, 60 months).** $\sigma = 2.458$ ppm and $\varphi = 0.650$
give $n_{\text{eff}} = 60\times0.350/1.650 = 12.7$, so
$\delta = 2.80\times2.458\times\sqrt{2/12.7} = 2.73$ ppm. Without the
autocorrelation correction the same arithmetic would give 1.26 ppm — **the
correction more than doubles the threshold**, which is Finding 51 acting on a
different statistic.

The conversion to CO₂-equivalent uses §16e.1 with the species' own molar mass and
GWP-100; CO and H₂ have no GWP and are left blank rather than assigned one.

### 16e.10 Interannual coupling with a control (Finding 87)

Annual means are formed only from years with all twelve months present, and only
consecutive complete years contribute a difference. The regression is against
the Barrow–South Pole mean, which shares no tropical station with the site under
test.

**The controls are part of the method, not decoration.** Mauna Loa and Samoa are
put through the identical pipeline. A null result from a pipeline that has not
been shown to produce a positive result elsewhere is uninterpretable; with the
controls at $r = 0.86$ and $0.88$, the site's $r = 0.03$ is a statement about the
record.

## 16f. The carbon economic value (Findings 90–100)

The methods here are mostly arithmetic. What needs justifying is not the
formulae but the *decomposition* — which quantities are kept separate, and why.

### 16f.1 Carbon to carbon dioxide, and to money (Finding 90)

$$m_{\mathrm{CO_2}} = m_{\mathrm{C}}\times\frac{44.01}{12.011} = m_{\mathrm{C}}\times3.664$$

**Worked example.** Finding 32's measured excess of 16.70 t C ha⁻¹ yr⁻¹ is
61.18 t CO₂ ha⁻¹ yr⁻¹. At the IDXCarbon average of IDR 52,295 tCO₂e⁻¹ that is
IDR 3.20 million ha⁻¹ yr⁻¹, or US$196 at IDR 16,300 to the dollar.

The three steps are reported as three rows and never collapsed. The first has a
confidence interval, the second is exact, the third is a policy price that moved
by a factor of 2.3 within Indonesia in one year.

### 16f.2 Flux to mass to money (Finding 91)

$$F\,[\mathrm{g\ m^{-2}\ yr^{-1}}] = F\,[\mu\mathrm{mol\ m^{-2}\ s^{-1}}]\times M\times10^{-6}\times3.156\times10^{7}$$

and the CO₂-equivalent mass over a footprint $A$ is $F\!\cdot\!A\!\cdot\!\mathrm{GWP}$.
All three assumed layer depths are carried through to the currency, because the
purpose of the table is the comparison between the depth span (a factor of 4) and
the price span (a factor of 2.3).

### 16f.3 Verifiable abatement (Finding 93)

$$f_{\min} = \frac{\delta(n)}{\Delta\mathrm{CO_2e}_{\text{station}}}$$

with $\delta(n)$ from §16e.9. $f_{\min} > 1$ means the station could not detect
the removal of its entire local source. The comparison is generous to the
network in three ways, each stated in the report: it assumes nothing else
changes, that the enhancement is otherwise stationary, and that a detection
threshold derived for the background at one site carries to an enhancement at
another.

### 16f.4 The rectifier as a bias, not a noise term (Finding 94)

The rectifier of §16b is expressed as a percentage of the station's own measured
enhancement. The relevant property is not the magnitude but the *sign*: a
fixed-sign error does not decrease with $\sqrt{n}$, so the bias in a
ten-year afternoon-sampled record equals the bias in a one-year one. Differences
between two afternoon-sampled sites largely cancel it, which is why Part III
survives it and a flux inference would not.

### 16f.5 Permanence and reversal (Findings 97, 98)

Permanence treats the store as a first-order reservoir draining at the measured
rate, $\tau = S/\dot{S}$, and reports $1 - e^{-P/\tau}$ for crediting period $P$.
Reversal risk is the binomial complement on the Gumbel return period $T$ of
§16a:

$$\Pr(\ge 1\ \text{event in}\ n\ \text{years}) = 1 - (1 - 1/T)^n$$

Independence is assumed and is **optimistic**: report §9.3 shows the extremes
cluster with ENSO, so the true distribution has more years with several events
and more years with none, which is worse for a buffer pool sized on the mean.

### 16f.6 The national-scale signal (Finding 100)

A single well-mixed box over the national land area $A$, of depth $h$, ventilated
on a timescale $\tau_v$, reaches the steady-state enhancement

$$\Delta C = \frac{E}{A}\cdot\frac{\tau_v}{h\,\rho_{\text{air}}}\cdot\frac{M_{\text{air}}}{M_{\mathrm{CO_2}}}$$

**Worked example.** $E = 231.2$ MtCO₂ yr⁻¹ (the width of the Second NDC 2035
range) over $A = 1.905\times10^{12}$ m² is $3.85\times10^{-6}$ g m⁻² s⁻¹. With
$h = 1{,}000$ m, $\rho = 1.2$ kg m⁻³ the column holds $1.2\times10^{6}$ g m⁻²,
and with $\tau_v = 1$ day the mass fraction is
$3.85\times10^{-6}\times86{,}400/1.2\times10^{6} = 2.77\times10^{-7}$, which is
0.182 ppm as a mole fraction. Against the 2.73 ppm of §16e.9 the ratio is 0.067.

This is a caricature of the real transport and is meant to be one. It is
reported across $h \in [500, 2000]$ m and $\tau_v \in [0.5, 3]$ d precisely
because no single choice is defensible, and the conclusion survives only because
the shortfall is a factor of 2.5 in the most favourable corner of that box and 60
in the least.

---

## 17. Worked examples, end to end

### 17.1 Jakarta's ΔCO/ΔCO₂ = 23.5 ppb ppm⁻¹ (Finding 8)

1. Load `grk_hourly_kmy.json`; convert CO from ppm to ppb (×1000); apply range gates.
2. Shift timestamps by +7 h to local time.
3. Group into nights spanning 18:00–08:00 local.
4. For each night with ≥6 valid hours and ≥5 ppm CO₂ build-up, regress CO on CO₂ by OLS.
5. Keep the 229 nights with $r^2 \ge 0.70$.
6. Report the median of those 229 slopes and the interquartile range: **23.50 [18.88, 30.93]**.

*Sensitivity: raising the gate to $r^2 \ge 0.8$ removes about a third of the nights and moves the median by under 1 ppb ppm⁻¹.*

### 17.2 The 2019 peat fingerprint, ΔCH₄/ΔCO = 0.090 (Finding 13)

1. Select BKT hours from 15 Aug to 5 Nov 2019 with both CO and CH₄ valid.
2. Baselines: $q_{10}$ of each species over that window.
3. Enhancements $\Delta\text{CO} = \text{CO} - q_{10}(\text{CO})$, likewise CH₄.
4. OLS of $\Delta\text{CH}_4$ on $\Delta\text{CO}$ over all 1,877 hours: slope 0.090, $r = 0.70$.
5. Bootstrap 400 resamples of hours: 95 % interval [0.085, 0.095].

*Why this survives the pre-2019 CO bias: the bias is multiplicative and 2019 is past the step anyway, but even if it were not, both numerator and denominator would scale together and the slope would move only through the baseline term.*

### 17.3 Jambi's respiration antiphase (Finding 11)

1. Assign each hour to a "night date" by subtracting 12 h and truncating to the day, so a night is not split across midnight.
2. Select hours 19:00–04:00 local.
3. For each night with ≥6 valid CO₂ hours spanning ≥5 h, regress CO₂ on elapsed hours; keep nights with $r > 0.7$.
4. Group the surviving slopes by calendar month; take the median per month, requiring ≥8 nights.
5. Normalise each station by its own annual mean, so the two sites can share an axis.
6. Read the phase: Jambi peaks in October (1.42) and troughs in January (0.68); Bariri peaks in January (1.15) and troughs in August (0.80).

*The finding is the antiphase, not the magnitude, and it is robust to $h$ because normalising by the site's own annual mean divides out any constant depth error. Only a strongly seasonal depth error, correctly timed and opposite in sign at the two sites, could manufacture it.*

### 17.4 The ENSO sensitivity of CO₂ growth (Finding 24)

1. Monthly flask medians of BKT CO₂, 2004–2025.
2. Harmonic fit (§4); subtract the seasonal component.
3. Reindex to a complete monthly axis; interpolate gaps ≤2 months.
4. Smooth with a centred 7-month mean, then take the 12-month difference — this is $g(t)$, monthly growth.
5. Load the CPC ONI, dating each three-month season to its middle month.
6. For lags 0…15 months, correlate $g(t)$ with ONI$(t - \text{lag})$ and record $r$.
7. Take the lag maximising $|r|$: **lag 0, $r = +0.38$**.
8. Slope of $g$ on ONI at that lag: **+0.82 ppm yr⁻¹ per °C**, with $\operatorname{se} = \sqrt{(1-r^2)/(n-2)} \cdot \sigma_g/\sigma_{\text{ONI}}$, giving ±0.27 at 95 %.

*The scan is what makes the zero-lag result meaningful: a global-mean CO₂ series would peak at 3–6 months, and finding zero at a station inside the source region is the physical content.*

---

## 18. Network information and robustness

### 18.1 Signed daily hysteresis area (Findings 101–102)

For each station and tracer pair, a day is retained when at least 18 hourly medians exist and all four six-hour quadrants are represented. Each tracer is standardised within day, so concentration units and plume magnitude do not determine the result. The closed hourly polygon has signed area

$$A={1\over2}\sum_{h=0}^{23}\left(x_hy_{h+1}-x_{h+1}y_h\right),$$

with the final point joined to the first. The sign records loop direction; the magnitude records phase separation. Days, rather than hours, are bootstrapped 2,000 times. For Jambi CO₂–CH₄ the median is −1.135 over 586 days and 71.8 % are negative; Bariri is +0.750 over 1,285 days and 40.9 % are negative (`q_hysteresis.csv`). Seasonal medians use the same daily values split into November–April and May–October (`q_hysteresis_season.csv`).

### 18.2 Period-specific coupling (Finding 103)

Rows must contain all three species. Pearson $r$ and Spearman $\rho$ are calculated separately for 00:00–05:00 and 12:00–16:00 local time. Reporting both prevents a few large urban plumes from being mistaken for general monotonic coupling. Kemayoran CO₂–CO gives $r=0.861$, $\rho=0.871$ at night and $r=0.587$, $\rho=0.521$ in the afternoon (`q_daynight_coupling.csv`).

### 18.3 Analyst-choice perturbations (Findings 104–107)

Baseline sensitivity recomputes each station's afternoon level at the 10th, 20th and 30th percentiles. Window sensitivity holds the 20th percentile fixed and moves the five-hour interval from 11–15 through 13–17. Reference sensitivity first restricts every station to the common 2023–2024 interval and then subtracts each possible reference in turn; because subtraction is monotone, rank must remain invariant. Annual rank stability calculates a separate 20th-percentile afternoon level for each of the two complete overlap years. A worked example is BKT CO₂: $q_{30}-q_{10}=391.900-385.660=6.240$ ppm, while the largest one-hour window shift spans only 0.402 ppm (`q_baseline_quantile.csv`, `q_afternoon_window.csv`).

### 18.4 Return, gaps and maintenance value (Findings 108–112)

For a sampling-limited mean or step, standard error scales as $n^{-1/2}$. If valid return rises from $u_0$ to $u_1$, the new detection threshold relative to the old is

$$f=\sqrt{u_0/u_1}.$$

Sorong CO changes from 56.1 % to 76.1 % under a twenty-point gain, so $f=0.859$: a 14.1 % reduction (`q_uptime_gain.csv`). Calendar completeness is computed only after reindexing every station between its first and last observation onto a complete hourly axis. Month-of-year return, longest internal gaps, complete-month counts and the intersection of the three species then follow directly (`q_outage_season.csv`, `q_longest_gap.csv`, `q_joint_return.csv`, `q_complete_months.csv`).

### 18.5 Day-type and diurnal fingerprints (Findings 113–115)

Morning daily medians are split into weekdays and weekends. The difference of medians is bootstrapped by day 2,000 times; the identical calculation at all five stations supplies spatial controls. Kemayoran CO is +201 ppb with a +141 to +232 ppb interval (`q_weekday_network.csv`). Rush and night fingerprints subtract the 12:00–15:00 median before taking tracer ratios: Kemayoran's morning increment is $482.5/18.52=26.05$ ppb CO per ppm CO₂ (`q_rush_fingerprint.csv`). Seasonal diurnal amplitudes are maximum minus minimum of the 24 hourly medians, calculated separately for the two half-years (`q_seasonal_diurnal.csv`).

### 18.6 Event structure and recovery (Findings 116–118)

An extreme hour exceeds its station-and-species 99th percentile. Consecutive extreme hours separated by no more than 48 hours belong to one cluster; elapsed first-to-last time gives duration (`q_extreme_clusters.csv`). Recovery uses daily medians and an anomaly above a centred 31-day 20th-percentile background. Event days exceed the anomaly's 95th percentile, and the reported statistic is

$$R_3={a(t+3\,\mathrm{days})\over a(t)}.$$

For Jambi CO the median $R_3=0.230$ over 27 usable events (`q_event_decay.csv`). Threshold sensitivity reports the concentration at four declared percentiles rather than pretending that one cross-site absolute definition exists (`q_threshold_sensitivity.csv`).

### 18.7 Common mode and leave-one-station-out prediction (Findings 119–120)

Each station's daily afternoon median is centred by its own 31-day rolling median. Pairwise Pearson and Spearman correlations are then calculated only on overlapping days (`q_common_mode.csv`). For the redundancy benchmark, the predictor for station $i$ is the same-day median anomaly of every other available station:

$$\hat a_i(t)=\operatorname{median}_{j\ne i}a_j(t).$$

Skill is reported as correlation, RMSE and RMSE divided by the target's own standard deviation. For Kemayoran CO₂, $r=0.030$ and RMSE/SD = 1.082; using the network is worse than predicting zero anomaly (`q_redundancy.csv`).

## 19. Advanced multivariate and nonlinear methods

### 19.1 Eigenstructure and conditional graphs (Findings 121–123, 137, 140)

Within each station, paired hourly values have their month × hour median removed and are divided by a robust MAD scale. PCA uses the resulting correlation matrix. Effective dimension is the participation ratio $D=(\sum\lambda_i)^2/\sum\lambda_i^2$; Bariri gives 2.482 and Jakarta 1.722 (`aa_pca.csv`, `aa_dimension.csv`). Partial correlations are correlations between residuals after regressing each member of a pair on the third gas; the precision-matrix identity $r_{ij\cdot k}=-P_{ij}/\sqrt{P_{ii}P_{jj}}$ gives the same graph (`aa_partial.csv`, `aa_precision_network.csv`). The station-network dimension applies the eigenvalue calculation to daily local anomalies (`aa_network_dimension.csv`).

### 19.2 Nonlinear, tail and quantile dependence (Findings 124–128, 150)

Finite-threshold upper-tail dependence is $P(V>0.95\mid U>0.95)$ after rank transformation; the lower analogue uses 0.05 (`aa_upper_tail.csv`, `aa_lower_tail.csv`). Mutual information uses an 8×8 equal-frequency table and subtracts the mean from 100 independent permutations; Jakarta CO₂–CO gives 0.559−0.002=0.557 nats (`aa_mutual_information.csv`). Pearson, Spearman and Kendall coefficients diagnose rank nonlinearity. Quantile regression minimises the asymmetric absolute loss by linear programming at q10, q50 and q90 (`aa_rank_nonlinearity.csv`, `aa_quantile_slopes.csv`). `aa_nonlinear_synthesis.csv` places information and conditional edges side by side rather than treating them as independent confirmations.

### 19.3 Distribution, entropy and variance across scale (Findings 129–135)

Day–night Jensen–Shannon divergence is the symmetric mean of two Kullback–Leibler divergences to the mixture distribution, using common quantile bins (`aa_daynight_js.csv`). Hour entropy is $-\sum p_h\ln p_h/\ln24$ for top-decile observations (`aa_hour_entropy.csv`). Variance is decomposed sequentially: hour-of-day effects first, month effects on the hour residual second, and the remainder last (`aa_variance_components.csv`). Resampling gives retained variance at daily, weekly and 30-day scales; Allan deviation is $[\tfrac12\langle(\bar x_{k+1}-\bar x_k)^2\rangle]^{1/2}$ across averaging intervals (`aa_multiscale_variance.csv`, `aa_allan.csv`). Annual robust-scale trends use Theil–Sen intervals; change points minimise within-segment squared error in annual log variance and are explicitly treated as exploratory (`aa_variance_trend.csv`, `aa_variance_changepoint.csv`).

### 19.4 Stability, synchrony and propagation (Findings 136, 138–141)

Year-specific paired correlations test sign stability (`aa_covariance_stability.csv`). Extreme synchrony is the Jaccard index of site-relative top-5 % daily events on common dates (`aa_event_synchrony.csv`). Propagation scans integer lags −7…+7 days and reports both selected and zero-lag correlations, with the scan bias stated (`aa_propagation_lag.csv`). Regularised canonical correlation uses $C_{xx}+0.05I$ and $C_{yy}+0.05I$ to avoid singular daily three-gas covariance matrices (`aa_canonical.csv`).

### 19.5 Prediction and multivariate separability (Findings 142–144)

Species reconstruction fits two gases to the third while leaving one entire year out and reports pooled out-of-year $R^2$ (`aa_species_reconstruction.csv`). Station classification is nearest-centroid on the three standardised anomalies with whole months left out; the 5×5 confusion table supplies mutual information (`aa_station_classification.csv`). Robust centroid separation divides daily median differences by the network-wide MAD scale before taking Euclidean distance (`aa_centroid_separation.csv`).

### 19.6 Extremal clustering and recovery models (Findings 145–148)

Burstiness is $B=(\sigma_\Delta-\mu_\Delta)/(\sigma_\Delta+\mu_\Delta)$ for inter-event intervals (`aa_burstiness.csv`). The runs extremal index is the number of starts of consecutive 99th-percentile runs divided by extreme hours; its reciprocal is mean run length (`aa_extremal_index.csv`). Recovery composites divide each post-event anomaly by its event-day value and take the median at each lag (`aa_recovery_composite.csv`). Exponential $\ln y=a+bt$ and power-law $\ln y=a+b\ln(1+t)$ fits are compared by AIC on lags 0, 1, 3 and 7 (`aa_decay_model.csv`).

### 19.7 Hysteresis falsification test (Finding 149)

The daily signed polygon area is recalculated exactly as §18.1, then its absolute value is compared with unstandardised daily CO₂ range using Spearman ρ. Values between −0.100 and +0.040 (`aa_hysteresis_amplitude.csv`) show that the standardised timing loop is not a disguised amplitude statistic.

### 19.8 Diurnal transitions and within-night curvature (Findings 151–160)

For each station, the median CO₂ climatology $C_h$ is differentiated by adjacent hour. The most negative $C_h-C_{h-1}$ between 05:00 and 12:00 defines morning collapse; the largest positive step between 16:00 and 23:00 defines evening rebuild (`ab_transition_clock.csv`). Jambi’s extrema are −15.06 ppm at 09:00 and +4.57 ppm at 20:00.

Curvature is tested within complete nights rather than between separate samples. OLS slopes are fitted to 20:00–23:00 and 00:00–03:00, paired by night, and their difference is tested with a two-sided Wilcoxon signed-rank test. BKT slows from a median 1.612 to 0.754 ppm h⁻¹; Jambi’s −0.070 ppm h⁻¹ paired difference gives *p*=0.5791 (`ab_nocturnal_curvature.csv`).

### 19.9 Residual-layer carry-over (Findings 161–165)

Daily afternoon medians (12:00–16:00) are paired with the following day’s 04:00–06:00 median. Calendar-month medians are removed from both series before Pearson and Spearman correlation, preventing the annual cycle from manufacturing memory. BKT gives *r*=0.750 and ρ=0.729 over 2,508 pairs; Jambi gives 0.089 and 0.080 (`ab_carryover.csv`).

### 19.10 Seasonal distribution divergence (Findings 166–170)

Wet-half-year and dry-half-year samples share 24 quantile bins. With $M=(P+Q)/2$, Jensen–Shannon divergence is

$$JS(P,Q)=\tfrac12D_{KL}(P\Vert M)+\tfrac12D_{KL}(Q\Vert M).$$

The largest value is 0.225 nats for Bariri CH₄; Jakarta’s maximum is 0.023 for CO (`ab_seasonal_shift.csv`). Unlike a mean difference, this statistic detects changes in spread and tails.

### 19.11 Robust multigas regimes (Findings 171–175)

Month × hour medians are removed and each gas is divided by its MAD×1.4826. Reproducibly sampled sets of at most 10,000 paired hours are partitioned by three-centroid *k*-means. Explained variance is $1-W/T$, within-cluster squared distance over total squared distance. Jakarta reaches 66.0%; Bariri 45.0% (`ab_source_regimes.csv`). Sorong’s 0.1% extreme cluster is retained as a warning that a centroid can be an outlier bin rather than a physical regime.

### 19.12 Compound upper tails (Findings 176–180)

After rank transformation, finite-threshold dependence is $P(V>0.95\mid U>0.95)$. Dividing again by 0.05 expresses the result relative to independence. Jakarta CO₂–CO gives 0.715, or 14.3× independence; Bariri’s strongest pair gives 2.6× (`ab_compound_extremes.csv`). The maximum of three pairs is reported with an explicit selection caveat.

### 19.13 Event-composition ageing (Findings 181–185)

Daily medians are expressed above a centred 31-day rolling 20th percentile. Days above the station’s 95th-percentile CO anomaly initiate composites, and CH₄/CO plus the residual CO fraction are evaluated three days later when residual CO is positive. Jambi moves from 0.624 to 1.264 ppb ppb⁻¹ while its CO fraction falls to 0.230 (`ab_event_ageing.csv`).

### 19.14 Surrogate-tested persistence (Findings 186–190)

Daily CO medians have a centred 31-day median removed. The observed lag-1 autocorrelation is compared with 1,000 random permutations of the same values; the two-sided Monte Carlo probability is $(1+k)/(1001)$. All five stations give *p*=0.001; observed lag-1 ranges from 0.315 at Jambi to 0.640 at Bariri (`ab_surrogate_memory.csv`).

### 19.15 Annual edge stability (Findings 191–195)

Robust month × hour anomalies are correlated separately within each calendar year. For each station the pair with the largest absolute median annual correlation is reported with its minimum, maximum and same-sign fraction. Jakarta CO₂–CO spans only 0.873–0.891 over three years; BKT CH₄–CO is positive in all twelve measured years (`ab_yearly_stability.csv`).

### 19.16 Fixed-hour sampling operator (Findings 196–200)

Within each date, the available-hour mean is subtracted from every hourly CO₂ value. Median bias is then calculated by clock hour; the least- and most-biased clocks and the full span are reported. Jambi spans 43.60 ppm while Bariri’s 20:00 median is only −0.06 ppm from its daily mean (`ab_fixed_hour_bias.csv`). This evaluates representation of a daily mean, not fitness for afternoon regional-background sampling.

### 19.17 Scope of the ninth analysis pass

The proposed wind-sector, PBL-normalised, IOD/MJO and satellite comparisons were not promoted to findings because the required meteorological or column data are not in this archive. `a35_extra9.py` therefore produces only claims supported by the harmonised station record; weak and null outcomes remain alongside strong ones.

## 20. Finding → derivation cross-reference

The cross-reference below maps every published finding to the method that produces it.

**Table 9 — Finding-to-derivation cross-reference**

| Finding | Report § | Derived in |
|---|---|---|
| 1 — time base | 2 | §2 |
| 2 — flask confirms the time base | 4.1 | §11.1 |
| 3 — in-situ is on the WMO scale | 4.2 | §11.1, §3.2 |
| 4 — pre-2019 CO bias | 4.3 | §11.2 |
| 5 — Maritime Continent CO₂ minimum | 4.4 | §3.2, §4 |
| 6 — NOAA QC rejection rates | 4.5 | §0 (QC flags) |
| 7 — morning erosion τ ≈ 2 h | 5.2 | §10 |
| 8 — Jakarta ΔCO/ΔCO₂, fossil bound | 6.3, 6.4 | §8, §17.1 |
| 9 — the weekly cycle | 7.2 | §7 |
| 10 — Jakarta's CH₄ flux | 7.3 | §9.1 |
| 11 — Jambi is drained peat | 8 | §9, §17.3 |
| 12 — October 2015 | 9.2 | §3.1 |
| 13 — the peat-fire classifier | 9.4 | §8, §17.2 |
| 14 — plume clearance | 9.5 | §10, §16 |
| 15 — flask CO percentile trends | 9.6 | §5 |
| 16 — CH₄ cycle is transport | 10.2 | §13.1 |
| 17 — SF₆ amplitude and NH fraction | 10.1 | §12 |
| 18 — CO's local excess | 10.3 | §13.1 |
| 19 — equatorial CO₂ amplitude | 10.4 | §4, §7 |
| 20 — the 2023 El Niño anomaly | 12.3 | §6.2 |
| 21 — radiative forcing | 13 | §15 |
| 22 — acceleration | 12.4 | §6.3 |
| 23 — decadal growth split | 12.4 | §5 |
| 24 — ENSO sensitivity | 12.5 | §17.4 |
| 25 — hemispheric gradient trends | 12.6 | §5 |
| 26 — CO transport/local partition | 10.6 | §13.2 |
| 27 — H₂ is a fire tracer, N₂O is not | 9.7 | §14 |
| 28 — the recovered CO₂ fire signal | 9.7 | §14.3 |
| 29 — photosynthesis separated from dilution | 5.3 | §15a |
| 30 — the airborne fraction from one station | 12.7 | §15b |
| 31 — the 2023 anomaly as a carbon flux | 12.7 | §15b |
| 32 — the peat clock | 8.4 | §15b |
| 33 — severity by three measures, return periods | 9.8 | §16a |
| 34 — monsoon onset from CO | 9.8 | §16a |
| 35 — Jakarta's ratios hour by hour | 7.4 | §8, §3.3 |
| 36 — the marine comparison | 11.2 | §3.2 |
| 37 — coherence against distance | 11.2 | §4 |
| 38 — CO memory | 9.9 | §16a |
| 39 — the N₂O residual | 10.7 | §13 |
| 40 — the seasonal H₂–CO coupling | 9.7 | §14 |
| 41 — dry-season amplification | 5.4 | §2.2 |
| 42, 43 — the null results | 15.5 | §5, §6.2 |
| 44 — tropical-mean SST from ONI − RONI | 14.1 | §15c |
| 45 — the ENSO classification flips | 14.2 | §15c |
| 46 — warming does not itself drive the fires | 14.3 | §15c |
| 47 — the forcing-to-warming closure | 14.4 | §15, §15c |
| 48 — the Idul Fitri experiment | 7.5 | §16b |
| 49, 50 — the diurnal rectifier and its use as QC | 4.6 | §16b |
| 51 — effective sample size | 16.1, 15.4 | §16b |
| 52 — time to detect a trend | 16.2 | §16b |
| 53 — the cost of discrete sampling | 16.3 | §16b |
| 54 — growth-anomaly covariance | 12.8 | §16b, §6.2 |
| 55 — the N₂O seasonal partition | 12.8 | §16b, §13.1 |
| 56 — the hydrogen trend | 12.8 | §5 |
| 57 — the widening CO₂ deficit | 12.8 | §5, §4 |
| 58 — NOAA flask pair reproducibility | 4.7 | §16c.1 |
| 59 — SF₆ transport lag clock | 10.8 | §16c.2 |
| 60 — vertical gradient at 19.5°N | 10.9 | §16c.3 |
| 61 — equatorial H₂ bimodal seasonality | 10.10 | §16c.4 |
| 62 — Bariri clean background contrast | 11.3 | §16c.5 |
| 63 — clean Sorong marine comparison | 11.4 | §16c.5 |
| 64 — Jakarta weekend traffic drop | 7.6 | §16c.5 |
| 65 — N₂O ENSO Bartlett null result | 16.4, 15.5 | §16b, §16.1 |
| 66 — global N₂O decadal acceleration | 12.9 | §16c.5, §5 |
| 67 — drained peat dry-season amplification | 8.5 | §16c.5 |
| 68 — latitude–time Hovmöller CO₂ attenuation | 10.11 | §16d.1 |
| 69 — SF₆ 2-box exchange timescale | 10.12 | §16d.2 |
| 70 — longitude–time Hovmöller CH₄ wave | 10.13 | §16d.3 |
| 71 — interhemispheric CO₂ growth asymmetry | 12.10 | §16d |
| 72 — methane interhemispheric gradient evolution | 12.11 | §16d |
| 73 — vertical damping of seasonal cycles | 12.12 | §16d.4 |
| 74 — multi-species growth covariance matrix | 12.13 | §16d |
| 75 — pristine clean CO floor stability | 9.10 | §16d |
| 76 — monsoonal modulation of nocturnal canopy CO₂ | 8.6 | §16d |
| 77 — multi-species radiative forcing budget | 13.3 | §16d.5 |
| 78 — CO₂-equivalent enhancement ladder | 11.5 | §16e.1 |
| 79 — data return by station-year | 3.1 | §16e.2 |
| 80 — background-air fraction, a negative result | 11.6 | §16e.3 |
| 81 — hourly cross-species coupling | 5.5 | §16e.4 |
| 82 — persistence ladder | 10.14 | §16e.5 |
| 83 — co-located in-situ vs flask growth rate | 4.8 | §16e.6 |
| 84 — nocturnal accumulation rate with interval | 5.6 | §16e.7 |
| 85 — depth-free CH₄:CO₂ signature | 6.5 | §16e.8 |
| 86 — Jakarta weekend CO₂-equivalent | 7.7 | §16e.1, §16e.9 |
| 87 — no coupling to global growth, with controls | 12.14 | §16e.10 |
| 88 — detectable step change | 16.5 | §16e.9 |
| 89 — seasonal amplitude stability | 16.6 | §5, §16e.9 |
| 90 — peat carbon loss priced | 17.2 | §16f.1 |
| 91 — Jakarta methane priced | 17.3 | §16f.2, §9.1 |
| 92 — sectoral split from two atmospheric bounds | 17.4 | §16f.1, §8 |
| 93 — verifiable fractional abatement | 17.5 | §16f.3 |
| 94 — rectifier as a systematic crediting bias | 17.6 | §16f.4, §16b |
| 95 — station fitness for an accounting role | 17.7 | §16e.2, §16f.3 |
| 96 — uncertainty budget of a monetised claim | 17.8 | §16f.1, §16e.7 |
| 97 — permanence over a crediting period | 17.9 | §16f.5 |
| 98 — reversal risk from the measured return period | 17.10 | §16f.5, §16a |
| 99 — verification modes and their limits | 17.11 | §16f.3 |
| 100 — the national-scale limit, a negative result | 17.12 | §16f.6 |
| 101 — daily tracer hysteresis | 18.1 | §18.1 |
| 102 — seasonal hysteresis reversal | 18.2 | §18.1 |
| 103 — day/night coupling | 18.3 | §18.2 |
| 104 — baseline percentile sensitivity | 18.4 | §18.3 |
| 105 — afternoon-window robustness | 18.5 | §18.3 |
| 106 — reference identifiability | 18.6 | §18.3 |
| 107 — annual rank stability | 18.7 | §18.3 |
| 108 — maintenance-value curve | 18.8 | §18.4 |
| 109 — outage seasonality | 18.9 | §18.4 |
| 110 — longest internal gaps | 18.10 | §18.4 |
| 111 — multispecies pairing penalty | 18.11 | §18.4 |
| 112 — complete calendar months | 18.12 | §18.4 |
| 113 — network weekday controls | 18.13 | §18.5 |
| 114 — rush-hour incremental fingerprint | 18.14 | §18.5 |
| 115 — seasonal diurnal ratios | 18.15 | §18.5 |
| 116 — extreme-event clustering | 18.16 | §18.6 |
| 117 — event recovery fraction | 18.17 | §18.6 |
| 118 — threshold sensitivity | 18.18 | §18.6 |
| 119 — daily common-mode null | 18.19 | §18.7 |
| 120 — station-redundancy null | 18.20 | §18.7 |
| 121 — within-station PCA | 19.1 | §19.1 |
| 122 — effective tracer dimension | 19.2 | §19.1 |
| 123 — conditional dependence | 19.3 | §19.1 |
| 124 — upper-tail dependence | 19.4 | §19.2 |
| 125 — lower-tail dependence | 19.5 | §19.2 |
| 126 — mutual information | 19.6 | §19.2 |
| 127 — rank nonlinearity | 19.7 | §19.2 |
| 128 — quantile slopes | 19.8 | §19.2 |
| 129 — day/night Jensen–Shannon divergence | 19.9 | §19.3 |
| 130 — event-hour entropy | 19.10 | §19.3 |
| 131 — variance decomposition | 19.11 | §19.3 |
| 132 — multiscale variance | 19.12 | §19.3 |
| 133 — Allan scaling | 19.13 | §19.3 |
| 134 — variability trend | 19.14 | §19.3 |
| 135 — variance change-point null | 19.15 | §19.3 |
| 136 — covariance sign stability | 19.16 | §19.4 |
| 137 — precision-network edges | 19.17 | §19.1 |
| 138 — extreme-event synchrony | 19.18 | §19.4 |
| 139 — propagation-lag null | 19.19 | §19.4 |
| 140 — network effective dimension | 19.20 | §19.1 |
| 141 — canonical cross-station dependence | 19.21 | §19.4 |
| 142 — leave-year-out species reconstruction | 19.22 | §19.5 |
| 143 — leave-month-out station classification | 19.23 | §19.5 |
| 144 — robust centroid separation | 19.24 | §19.5 |
| 145 — event burstiness | 19.25 | §19.6 |
| 146 — runs extremal index | 19.26 | §19.6 |
| 147 — composite recovery | 19.27 | §19.6 |
| 148 — competing decay models | 19.28 | §19.6 |
| 149 — hysteresis-amplitude falsification | 19.29 | §19.7 |
| 150 — nonlinear synthesis | 19.30 | §19.2 |
| 151–155 — station transition clocks | 19.31 | §19.8 |
| 156–160 — nocturnal curvature | 19.32 | §19.8 |
| 161–165 — next-dawn carry-over | 19.33 | §19.9 |
| 166–170 — seasonal distribution divergence | 19.34 | §19.10 |
| 171–175 — multigas source regimes | 19.35 | §19.11 |
| 176–180 — compound upper tails | 19.36 | §19.12 |
| 181–185 — event-composition ageing | 19.37 | §19.13 |
| 186–190 — surrogate-tested CO memory | 19.38 | §19.14 |
| 191–195 — annual dominant-edge stability | 19.39 | §19.15 |
| 196–200 — fixed-hour sampling bias | 19.40 | §19.16 |

---

## Appendix — where each formula lives in the code

**Table 10 — Formula-to-code cross-reference**

| Technique | Function |
|---|---|
| Unit harmonisation, QC, time base | `ghg_common.load_station` |
| Harmonic fit | `ghg_common.harmonic_fit` |
| Theil–Sen | `ghg_common.theil_sen` (wraps `scipy.stats.theilslopes`) |
| Percentile baselines | `a7_extra.monthly_background`, `a9_process.afternoon` |
| Nightly emission ratios | `a1_ratios` |
| Nocturnal flux | `a7_extra.nocturnal_flux`, `a9_process.air_density` |
| Morning erosion | `a9_process.morning_erosion` |
| Weekly cycle | `a7_extra.weekly_cycle` |
| Growth anomalies | `a7_extra.growth_anomaly` |
| Seasonal amplitude bootstrap | `a7_extra.seasonal_ci` |
| Plume ratios | `a7_extra.fire_ratio` |
| Decay fits | `a7_extra.co_decay` |
| ENSO indices, index skill, TCR closure | `a22_roni` |
| Rectifier, Idul Fitri, effective DOF, detectability | `a24_extra3` |
| Flask pair reproducibility | `a26_extra4.flask_pairs` |
| SF₆ transport lag clock | `a26_extra4.sf6_lag` |
| Vertical gradients | `a26_extra4.vertical_gradients` |
| H₂ bimodal harmonic cycle | `a26_extra4.h2_seasonality` |
| Bariri vs BKT background | `a26_extra4.plu_vs_bkt` |
| Sorong marine baseline | `a26_extra4.srg_marine` |
| Jakarta rush hour weekday/weekend | `a26_extra4.kmy_diurnal_rush` |
| N₂O ENSO Bartlett test | `a26_extra4.n2o_enso_neff` |
| Decadal N₂O acceleration | `a26_extra4.n2o_acceleration` |
| Drained peat diurnal respiration | `a26_extra4.jmb_seasonal_respiration` |
| Latitudinal Hovmöller & wave attenuation | `a28_extra5.hovmoeller_lat_co2` |
| SF₆ 2-box exchange timescale | `a28_extra5.sf6_exchange_time` |
| Longitudinal Hovmöller CH₄ wave | `a28_extra5.hovmoeller_lon_ch4` |
| ENSO growth rate asymmetry | `a28_extra5.enso_growth_asymmetry` |
| CH₄ gradient evolution | `a28_extra5.ch4_gradient_evolution` |
| Vertical damping across inversion | `a28_extra5.vertical_damping` |
| Growth anomaly covariance matrix | `a28_extra5.growth_covariance_matrix` |
| Pristine clean CO floor | `a28_extra5.bkt_clean_co_floor` |
| Monsoonal nocturnal accumulation | `a28_extra5.bkt_nocturnal_monsoon` |
| Multi-species radiative forcing budget | `a28_extra5.regional_forcing_budget` |
| CO₂-equivalent conversion on a mixing ratio | `a30_extra6.co2e_ladder` |
| Data return per station-year | `a30_extra6.uptime` |
| Background-air fraction | `a30_extra6.clean_fraction` |
| Hourly cross-species coupling | `a30_extra6.species_coupling` |
| Anomaly persistence | `a30_extra6.persistence` |
| Co-located in-situ vs flask growth | `a30_extra6.insitu_vs_flask` |
| Nocturnal rate with bootstrap interval | `a30_extra6.nocturnal_rate` |
| Depth-free CH₄:CO₂ signature | `a30_extra6.ch4_co2_signature` |
| Weekend CO₂-equivalent | `a30_extra6.kmy_weekend_co2e` |
| Global growth coupling, with controls | `a30_extra6.global_coupling` |
| Detectable step change | `a30_extra6.detect_co2e` |
| Seasonal amplitude stability | `a30_extra6.amplitude_stability` |
| Peat and methane priced under NEK | `a31_nek.jambi_value`, `a31_nek.jakarta_ch4_value` |
| Sectoral split of a city enhancement | `a31_nek.jakarta_fossil` |
| Verifiable abatement fraction | `a31_nek.detect_abatement` |
| Rectifier as a crediting bias | `a31_nek.rectifier_bias` |
| Station fitness scoring | `a31_nek.station_roles` |
| Uncertainty budget | `a31_nek.uncertainty_budget` |
| Permanence and reversal risk | `a31_nek.permanence`, `a31_nek.fire_reversal` |
| National-scale box-model limit | `a31_nek.national_limit` |
| Network information and robustness | `a33_extra7` |
| Advanced multivariate and nonlinear analysis | `a34_extra8` |
| Transition, regime, tail, memory and sampling analyses | `a35_extra9` |
| Spectral partition | `a7_extra.co_spectrum` |
| Radiative forcing | `a7_extra.dF_co2`, `a7_extra.dF_ch4` |
| Flask reading and matching | `noaa_flask` |
| Flask–in-situ comparison | `a11_flask.match_table`, `a11_flask.drift_table` |
| SF₆ mixing fraction | `a11_flask.nh_fraction` |
| Tracer–tracer attribution | `a11_flask.sf6_attribution` |
| Acceleration | `a13_trends_enso.acceleration` |
| ENSO lag scan | `a13_trends_enso.enso` |
| Gradient trends | `a13_trends_enso.gradient_trend` |
| CO partition | `a13_trends_enso.co_partition` |
| Air-mass correction | `a13_trends_enso.plume_corrected` |
| Paired decay comparison | `a15_carbon.sink_rates` |
| Day/night excess ratio | `a15_carbon._excess_ratio` |
| Carbon-budget conversion | `a15_carbon.budget` |
| Gumbel return periods | `a17_extra2.severity` |
| Monsoon onset | `a17_extra2.onset` |
| Hourly emission ratios | `a17_extra2.kmy_hourly` |
| Inter-station coherence | `a17_extra2.coherence` |
| Autocorrelation | `a17_extra2.memory` |
| Null tests | `a17_extra2.nulls` |
