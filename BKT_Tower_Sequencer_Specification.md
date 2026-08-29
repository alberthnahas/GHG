# Valve sequencer specification, Bukit Kototabang 100-m tower

**Station:** Bukit Kototabang (BKT), West Sumatra, 0.202° S, 100.318° E, 864.5 m a.s.l. — GAW Global station **Analyser:** Picarro G2401 (CO₂ / CH₄ / CO / H₂O) **Change:** single 30-m inlet → three-level tower at 30 m, 70 m and 100 m **Status:** design specification for review; not yet commissioned **Prepared:** 2026-08-23

---

## 1. What this document decides, and what it does not

The station currently samples one inlet at 30 m, chosen so that the in-situ record can be compared directly with the co-located flask programme. That 30-m record is registered with the WDCGG. A 100-m tower with intakes at 30 m, 70 m and 100 m is being brought into service, and the analyser must now be shared between them by a multi-position valve.

Four things have to be fixed before the sequencer can be programmed:

1. how long the analyser must wait after a valve switch before the air it sees is the air at the new inlet;
2. how long each level must then be sampled;
3. how often each level must be revisited;
4. in what order the levels are visited within the cycle.

**This specification answers all four, and the fourth turns out to matter more than expected.** Items 2–4 are settled against the station's own 30-m record — 59 231 hours of CO₂, 65 013 of CH₄ and 42 740 of CO. Item 1 is geometry, not measurement.

> **Limits.** The archive is hourly. It cannot directly resolve anything happening inside an
> hour, which is exactly the timescale a 5-minute slice lives on. Section 6 extrapolates below
> one hour and says so explicitly wherever it does. Section 12 lists the three quantities that
> must be measured on the installed system before this schedule is considered validated.

---

## 2. The constraint set

| # | Constraint | Origin |
|---|---|---|
| C1 | 100 m carries the majority of the measurement time | station's scientific priority |
| C2 | 30 m must continue the existing WDCGG series without a change in sampling statistics | data-archive continuity |
| C3 | All three levels are sampled every hour of every day | avoids aliasing the diurnal cycle |
| C4 | Levels are compared at as nearly the same time as possible | vertical gradients are the point of a tower |
| C5 | Discarded purge time is minimised | it is pure loss |
| C6 | The frame is identical in every hour | simplest possible sequencer state machine, and simplest QC |

C2 and C4 pull hardest, and they pull in different directions. C2 rules out the intuitive "3-hourly for the lower levels" schedule (§5). C4 rules out the intuitive "bottom to top" ordering (§7).

---

## 3. The manifold decides everything else

**Nothing in this specification works without a continuously running bypass pump.** The purge time after a valve switch is set by how fast the selected line is being swept, and the G2401's own ~0.4 slpm is far too slow for a 100-m line.

The line volume is fixed by the bore and the run length. For 1/4-inch OD PFA (4.0 mm ID), a 100-m line holds 1.26 L. Treating the line as a well-mixed volume — conservative, since plug flow in a smooth tube clears faster — the residual of the previous level decays as $\exp(-t/\tau)$ with $\tau = V/Q$.

**Table 1 — Line volume and purge time to 1 % residual (from `outputs/sq_flush.csv`)**

| Inlet | Volume (L) | 0.4 slpm | 2 slpm | 5 slpm | 10 slpm |
|---|---|---|---|---|---|
| 30 m | 0.377 | 4.34 | 0.87 | 0.35 | 0.17 |
| 70 m | 0.880 | 10.13 | 2.03 | 0.81 | 0.41 |
| 100 m | 1.257 | 14.47 | 2.89 | 1.16 | 0.58 |

*Times in minutes.*

At the analyser's own flow the 100-m line needs 14.5 minutes to clear to 1 %. At 5 slpm it needs 1.16 minutes. **Without the bypass pump the three purges would take 28.9 minutes — 48 % of every hour. With it they take 9 minutes, 15 %.**

### 3.1 Specified manifold

- All three lines swept continuously at **≥ 5 slpm** by a shared diaphragm bypass pump.
- The valve subsamples the selected line; the unselected lines keep flowing to waste.
- **Purge window: 3 minutes** after every switch. At 5 slpm this is 11.9 volumes of the 100-m line against the 4.6 needed to reach 1 %, and the 7.3 volumes of margin also cover the common manifold downstream of the valve and the analyser cavity, which Table 1 does not include.
- Condensation trap with a drain at the base of the 100-m line. The G2401 reports dry mole fractions from its own water measurement, so no dryer is required, but a 100-m vertical run through a tropical diurnal temperature swing will condense.
- Same tubing type, bore and filter on all three lines, so that no level carries a line-specific artefact.

> **Limits.** Table 1 is geometry, not a measurement. The well-mixed assumption is
> conservative for the tube but ignores dead volume in filters, fittings and the valve body,
> which is where real memory usually lives. §12.1 specifies the commissioning test that
> replaces this table with a measured number.

![Figure SQ3](figures/sq3_frame_and_flush.png)

**Figure SQ3.** The adopted frame (a) and the flush constraint behind its purge windows (b, c). Panel b is the 100-m line; the dashed line is the adopted 3-minute window.

---

## 4. The station's diurnal cycle is large, and it is not sinusoidal

Composited over the whole record as anomalies from each day's own mean — so that neither the trend nor the seasonal cycle can leak into the shape — the 30-m inlet shows a CO₂ range of **22.9 ppm** between a maximum at 06:00 local time and a minimum at 14:00. CH₄ ranges over 32.8 ppb (maximum 07:00) and CO over 14.2 ppb (maximum 08:00).

**Table 2 — Diurnal composite at the 30-m inlet (from `outputs/sq_diurnal.csv`)**

| Species | Max hour | Max anomaly | Min hour | Min anomaly | Range | Spread 00–06 | Spread 12–16 |
|---|---|---|---|---|---|---|---|
| CO₂ (ppm) | 06 | +10.98 | 14 | −11.87 | 22.86 | 7.12 | 4.09 |
| CH₄ (ppb) | 07 | +20.88 | 12 | −11.89 | 32.77 | 32.18 | 20.36 |
| CO (ppb) | 08 | +7.25 | 13 | −6.99 | 14.23 | 30.29 | 23.00 |

*Spread is the standard deviation of the hourly anomalies within the stated hours.*

Three features of the shape drive the schedule:

- **The night is where the vertical information is.** The build-up between 20:00 and 07:00 is what a shallow, stably stratified layer does to a surface source; by 14:00 convection has mixed the column and the three levels will read nearly the same. A schedule that samples the upper level preferentially by *time of day* would throw away most of the gradient signal.
- **The shape is the same in DJF and JJA.** The two seasonal composites in Figure SQ1a lie almost on top of each other, so the schedule does not need a seasonal mode.
- **The variability peaks at the morning transition, not at the diurnal maximum.** The normalised spread peaks at 06:00–07:00 for CO₂ and CH₄ and 09:00 for CO, where the nocturnal layer breaks up. That is the hour in which a short slice is least representative, and the hour in which a timing offset between levels does the most damage.

![Figure SQ1](figures/sq1_diurnal_demand.png)

**Figure SQ1.** The diurnal cycle at the existing 30-m inlet and what it demands of the schedule. (a) CO₂ anomaly composite with its interquartile envelope and the DJF/JJA split. (b) CH₄ and CO. (c) Hour-of-day spread, normalised to its own 24-hour mean.

---

## 5. Finding — 3-hourly sampling of the lower levels is not compatible with the WDCGG record

The obvious way to give 100 m the majority of the time is to visit 30 m and 70 m only every third hour. This was tested directly against the station's own record: the monthly means were rebuilt from a 3-hourly subsample at each of the three possible clock offsets and compared with the monthly means of the complete hourly record over the same months.

**Table 3 — Cost of 3-hourly sampling, measured on the BKT record (from `outputs/sq_subsample.csv` and `outputs/sq_diurnal_bias.csv`)**

| Species | Months | Monthly-mean RMS error | Worst month | Diurnal amplitude lost |
|---|---|---|---|---|
| CO₂ (ppm) | 81 | 0.18 | 0.66 | 2.0 % |
| CH₄ (ppb) | 91 | 0.84 | 5.05 | 12.0 % |
| CO (ppb) | 61 | 0.55 | 2.45 | 16.3 % |

**The CO₂ penalty is small; the CH₄ and CO penalties are not.** CO₂'s diurnal cycle is smooth and close to a single harmonic, so eight samples a day reconstruct it well. CH₄ and CO have a sharp morning peak that eight samples a day systematically clip — 12 % and 16 % of the amplitude, in the same direction at every offset. A worst-month CH₄ error of 5.0 ppb is comparable to a year of global CH₄ growth.

There is a second objection that the table cannot show. The archived WDCGG series is built from near-continuous hourly means. Moving the 30-m inlet to 8 hourly means per day changes the *sampling statistics* of the series, not merely its density, and does so at the same date as a physical inlet move. Any step found in the record afterwards would be uninterpretable, because two candidate causes changed together.

> **Limits.** This test subsamples an hourly archive, so it measures the aliasing penalty of
> visiting 8 hours out of 24. It does not measure the penalty of sampling 5 minutes out of 60,
> which is a separate and much smaller term — §6.

**Decision: every level is sampled in every hour.** C1 is met by splitting the *hour*, not by splitting the *day*.

---

## 6. How short a slice can be

Two error terms decide the slice length.

**Precision** is not the binding one. The G2401's raw 5-second noise is well below the atmospheric variability at this site, and averaging 5 minutes of 1-Hz data reduces it by a further order of magnitude. Nothing in this schedule is precision-limited.

**Representativeness** — how well a 5-minute slice stands for the whole hour — is the binding term, and the hourly archive can only bound it by extrapolation. The second-order structure function $D(\tau) = \langle (x(t+\tau) - x(t))^2 \rangle$ was computed at the lags the archive resolves (1–6 h) and fitted as $D = A\,\tau^{2H}$.

**Table 4 — Structure-function fit and the extrapolated 5-minute change (from `outputs/sq_structure_fit.csv` and `outputs/sq_structure.csv`)**

| Species | $A$ | $H$ | $r^2$ of fit | RMS change over 5 min |
|---|---|---|---|---|
| CO₂ (ppm) | 26.25 | 0.590 | 0.99998 | 1.18 |
| CH₄ (ppb) | 534.7 | 0.374 | 0.9969 | 9.13 |
| CO (ppb) | 346.0 | 0.531 | 0.9962 | 4.97 |

$A$ is $D$ at a lag of one hour. The exponents are the physically expected ones: *H* near 0.5 is a random-walk-like signal, and CO₂'s 0.59 reflects the deterministic diurnal ramp on top of it.

The extrapolated 5-minute CO₂ change of 1.18 ppm is small against the 22.9 ppm diurnal range, and most of it is the ramp itself rather than noise — a 5-minute mean sits at the centre of the ramp it spans, so the ramp largely cancels in the mean and does not cancel in the instantaneous difference this statistic measures. **5 minutes is therefore ample for the hourly mean and comfortably shorter than the timescale on which the atmosphere reorganises.**

> **Limits.** This is an extrapolation a factor of 12 below the shortest lag the data resolve,
> and it assumes the power law continues. It almost certainly does not all the way down —
> turbulent scales will break it. The extrapolation is used only to show that 5 minutes is
> *not marginal*; it is not used to quote a number in any product. §12.2 replaces it with a
> measurement.

![Figure SQ2](figures/sq2_design_evidence.png)

**Figure SQ2.** (a) The structure function, measured (solid) and extrapolated (dotted, shaded region). (b) What 3-hourly sampling costs, per species. (c) The spurious CO₂ gradient produced by the two candidate orderings.

---

## 7. Finding — the ordering within the hour matters more than the slice length

A vertical gradient is a difference between two levels. If the levels are sampled at different times, the atmosphere's own change over that interval enters the difference as a spurious gradient. The structure function of §6 gives that term directly: for levels sampled Δ*t* apart, the RMS artefact is $\sqrt{A\,(\Delta t/60)^{2H}}$.

Two orderings were compared. **Sequential** goes bottom to top — 30 m, 70 m, then 100 m for the rest of the hour — and puts the valid-time centroids 34 minutes apart. **Bracketed** opens the hour on 100 m, drops to 30 m and 70 m near the middle, and returns to 100 m, splitting the 100-m block around the short slices.

**Table 5 — Spurious gradient from sampling-time offset alone (from `outputs/sq_offset.csv`)**

| Ordering | Pair | Offset (min) | CO₂ (ppm) | CH₄ (ppb) | CO (ppb) |
|---|---|---|---|---|---|
| Sequential | 30 m vs 100 m | 34.0 | 3.66 | 18.70 | 13.76 |
| Sequential | 70 m vs 100 m | 26.0 | 3.13 | 16.91 | 11.93 |
| Bracketed | 30 m vs 100 m | 6.2 | 1.34 | 9.89 | 5.57 |
| Bracketed | 70 m vs 100 m | 1.8 | 0.65 | 6.24 | 2.89 |

**Bracketing costs nothing and removes a factor of 2.7 from the 30–100 m CO₂ artefact and a factor of 4.8 from the 70–100 m one.** Both orderings spend the same 41 valid minutes on 100 m, the same 5 on each lower level, and the same 9 minutes purging. The only difference is the order of the states in the sequencer.

A second gain follows from the same structure. Because the 100-m block is split around the lower levels, the 100-m mixing ratio can be **linearly interpolated across the gap** to the exact centroid of each lower-level slice before the gradient is formed. That removes the linear part of the ramp exactly, and the linear part is most of it over a 6-minute offset. The residual after interpolation is second-order and well below the 1.34 ppm in Table 5.

> **Limits.** Table 5 is an upper bound in two senses: it is the RMS over the whole record,
> and it is computed before the interpolation correction. It is a bound on the *artefact*, not
> an estimate of the gradient itself, which the tower has not yet measured.

---

## 8. Specification — the valve timing frame

The frame below runs identically in every hour of every day, synchronised to UTC and re-synced at the top of each hour rather than free-running.

**Table 6 — Valve timing frame (from `outputs/sq_frame.csv`)**

| Minute | Valve | State | Duration | Note |
|---|---|---|---|---|
| 00:00–00:19 | 100 m | valid | 19 min | no switch at the hour boundary |
| 00:19–00:22 | 30 m | purge | 3 min | discarded |
| 00:22–00:27 | 30 m | valid | 5 min | WDCGG-continuity slice |
| 00:27–00:30 | 70 m | purge | 3 min | discarded |
| 00:30–00:35 | 70 m | valid | 5 min | |
| 00:35–00:38 | 100 m | purge | 3 min | discarded |
| 00:38–01:00 | 100 m | valid | 22 min | runs into the next hour |

The hour opens and closes on 100 m, so **no purge is needed at the hour boundary** — the valve does not move there. Three switches per hour, 9 minutes of purge, 51 minutes archived.

**Table 7 — Resulting time budget (from `outputs/sq_budget.csv`)**

| Level | Valid min/hour | Share of valid data | Valid h/day | Hourly means/day |
|---|---|---|---|---|
| 100 m | 41 | 80.4 % | 16.4 | 24 |
| 70 m | 5 | 9.8 % | 2.0 | 24 |
| 30 m | 5 | 9.8 % | 2.0 | 24 |

Every constraint in §2 is met: 100 m takes 80 % of the measurement time (C1), all three levels produce 24 hourly means per day with no aliasing (C2, C3), each lower level's centroid sits within 6.2 minutes of the 100-m centroid (C4), purge is 15 % of the hour and would be 48 % without the bypass pump (C5), and the frame is a fixed seven-state cycle (C6).

### 8.1 Sequencer requirements

- **Clock discipline.** Switch times are absolute UTC minutes past the hour, re-derived each hour. Do not implement as a free-running timer chain; drift accumulates and moves the centroids that §7 depends on.
- **Valve position is a data column.** Log the commanded position at the analyser's native 1-Hz rate, in the same file as the mixing ratios. Do not write it to a separate file and align the two afterwards — this station's archive already carries an undocumented time-base change that cost a great deal of work to find, and a separately-clocked valve log would be the same class of problem.
- **Purge is flagged, not deleted.** Archive the purge minutes with a `purge` flag. They are the only evidence available for the commissioning test in §12.1, and they diagnose a leaking or slow valve.
- **The purge duration is a configuration parameter**, not a constant in the code. §12.1 may change it.

---

## 9. Calibration and target gas

Calibration time must be carved out of the frame explicitly rather than inserted ad hoc, otherwise it silently consumes a different level on each occasion.

- **Target tank: 20 minutes daily**, replacing the 00:38–01:00 valid 100-m block on one hour only (recommended 00 UTC). Cost: 20 of 984 valid 100-m minutes per day, 2.0 %.
- **Full calibration suite: weekly**, in a scheduled maintenance hour. Flag the whole hour as calibration for all three levels rather than producing partial hourly means.
- Calibration hours are the same hours every day and every week, so their effect on the diurnal composite is a known, correctable 1-in-24 gap rather than an unknown one.

---

## 10. Data products and archiving

| Product | Definition |
|---|---|
| Hourly mean, per level | Mean of the valid slice, with its standard deviation, sample count and slice centroid time |
| Gradient, per hour | 100 m minus lower level, with 100 m linearly interpolated to the lower level's centroid (§7) |
| WDCGG submission | The 30-m hourly means, continuing the existing series |

**Archive the within-slice standard deviation and the sample count alongside every hourly mean.** For the 5-minute slices this is the only information a downstream user has about how representative the slice was, and WDCGG accepts it. Without it, a 5-minute mean and a 41-minute mean are indistinguishable in the file.

**The 30-m inlet move is a discontinuity and must be documented as one**, with the exact changeover date, the change in slice length, and the overlap period from §12.3, whether or not that overlap shows a step.

---

## 11. Optional nocturnal enhancement

Section 4 shows the gradient information concentrates between 20:00 and 07:00 local time. If more lower-level data are wanted, the slices may be lengthened at night without breaking any constraint, because every hour still contains every level:

- **20:00–07:00 local time:** 8 valid minutes on 30 m and on 70 m; 100 m falls to 35 valid minutes (69 % of valid data).
- **07:00–20:00 local time:** the standard frame of Table 6.

**This is offered, not specified.** It complicates the sequencer and the QC for a gain that is real but unquantified until the tower has produced data. The recommendation is to run the uniform frame of Table 6 for the first year, then decide from the measured gradients.

---

## 12. What must be measured before this schedule is validated

Three numbers in this document are inferred rather than measured on the installed system. Each has a commissioning test.

### 12.1 The purge time

Switch 100 m → 30 m repeatedly during the pre-dawn hours, when the vertical gradient is largest, keeping the full 1-Hz record of the purge minutes. Fit the approach to the new level and read off the time to 1 % residual. **If it exceeds 3 minutes, the bypass flow is too low or there is dead volume in the manifold — fix the manifold rather than lengthening the purge**, because lengthening it comes out of the 100-m block.

### 12.2 The representativeness of a 5-minute slice

Run 100 m continuously for one week at 1 Hz. Compute the difference between each 5-minute window and its containing hourly mean, as a function of hour of day. This replaces the extrapolation in §6 with a measurement, and gives the correct per-hour uncertainty to archive with the 5-minute slices.

### 12.3 The 30-m inlet step

**Run the old 30-m inlet and the new tower's 30-m inlet in parallel for at least one month**, spanning both a dry and a wet spell if the schedule allows. This is the only way to separate an inlet-move step from a real atmospheric change in the WDCGG series, and it cannot be done retrospectively. If parallel operation is impossible, say so in the archive metadata rather than leaving the discontinuity undocumented.

---

## 13. Summary of the specification

| Item | Value |
|---|---|
| Cycle | 1 hour, identical every hour, UTC-synchronised |
| Levels per cycle | 3 (30 m, 70 m, 100 m) |
| Order | 100 m, 30 m, 70 m, 100 m (bracketed) |
| Purge after each switch | 3 min, archived and flagged |
| Valid slice, 30 m | 5 min, minute 22–27 |
| Valid slice, 70 m | 5 min, minute 30–35 |
| Valid slice, 100 m | 41 min, minutes 00–19 and 38–60 |
| Bypass flow, all lines | ≥ 5 slpm, continuous |
| Target gas | 20 min daily, from the 00 UTC 100-m block |
| Hourly means per level per day | 24 |

---

## Appendix A — Reproducing every number in this document

```bash
python3 scripts/a36_sequencer.py        # writes outputs/sq_*.csv
python3 scripts/a37_sequencer_figs.py   # writes figures/sq1-sq3
python3 scripts/a14_latex.py BKT_Tower_Sequencer_Specification.md
```

`a36_sequencer.py` loads BKT through `ghg_common.load_station`, which applies the archive's time-base correction and unit harmonisation. CO is restricted to 2019 onwards throughout, because the earlier in-situ CO is biased high by 10–41 ppb.

| Table / Figure | Source CSV |
|---|---|
| Table 1, Figure SQ3bc | `sq_flush.csv` |
| Table 2, Figure SQ1 | `sq_diurnal.csv` |
| Table 3, Figure SQ2b | `sq_subsample.csv`, `sq_diurnal_bias.csv` |
| Table 4, Figure SQ2a | `sq_structure_fit.csv`, `sq_structure.csv` |
| Table 5, Figure SQ2c | `sq_offset.csv` |
| Table 6, Figure SQ3a | `sq_frame.csv` |
| Table 7 | `sq_budget.csv` |

The figures for this document are numbered SQ1–SQ3, outside the main report's fNN sequence. They are bilingual: `a37_sequencer_figs` is registered in the `i18n.py` audit list, and `--lang id` writes `<name>_id.png` for the Indonesian slide deck.

A Bahasa Indonesia deck of this specification is built by `python3 scripts/a38_sequencer_slides.py`, producing `outputs/BKT_Tower_Sequencer_Slides_id.pptx` (20 slides).
