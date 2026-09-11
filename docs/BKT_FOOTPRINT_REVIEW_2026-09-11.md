# BKT HYSPLIT-STILT product: review and improvement suggestions

Reviewed 11 September 2026 against `BKT_HYSPLIT_STILT_Footprint_Report.md`,
scripts `a37`–`a73`, the `docs/BKT_*` plans and QA records, and the run
outputs under `outputs/hysplit/`. Numbers quoted below were recomputed from
those outputs during the review; none come from the prose.

## What is already strong

- Provenance and numerical hygiene are excellent: checksums, particle-count
  normalization, conservative regridding, CSV/NetCDF reconciliation, seed
  repeats, and independent validators for every stage.
- The domain-truncation diagnosis and full-ensemble rerun were the right call
  and are cleanly separated from any physics claim.
- The report never overclaims. The problem is closer to the opposite: it is
  now hard to find the science under the caveats.

## Findings that should be fixed (evidence in outputs)

### 1. Convective mixing was never active in any run

Every HYSPLIT `MESSAGE` file inspected, including the control, the
`convection_cape500` contrast, and the inversion base runs, prints
`Convective mixing - F`. The `CAPEMIN=500` experiment was therefore not a
test of a CAPE threshold; the convection module was off. That is why both
convection contrasts were bit-identical to the control.

- `docs/BKT_HYSPLIT_STILT_FOOTPRINT.md` still states Grell flux mode
  "confirmed active". That line is wrong and should be corrected.
- The main report says the null contrast "does not establish whether the
  threshold was reached". It can and should say the log shows the scheme
  was inactive.
- Scientific consequence: deep convection in equatorial Sumatra is a
  first-order vertical transport process. The only way to get it is a
  driver that carries convective fluxes (WRF with cumulus output converted
  through `arw2arl`), or to state plainly that all footprints here assume
  no parameterized convective venting.

### 2. The inversion error covariance is inflated by roughly a factor of three

Using the per-receptor `mismatch_sd_ppb` in `inversion_predictions.csv`,
the posterior normalized residuals have standard deviation 0.54 and a
diagonal reduced chi-square of 0.33 (n = 27). A consistent error budget
gives values near one. The working covariance (5 ppb calibration, 20/40 ppb
representativeness, 50 % of the prior source increment correlated over 24 h,
10 ppb boundary) is too wide.

- This is the direct reason the posterior intervals all straddle unity, the
  prediction envelope is 299 ppb wide, and source fitting cannot beat the
  background-only baseline: the likelihood is too weak to move anything.
- Suggested fix: treat the transport-error scale as a hyperparameter
  (maximum marginal likelihood, or a chi-square consistency target) instead
  of fixing it at 50 %. Better still, build the transport term from the
  perturbation ensembles already run in the benchmark (seed, mixing floor,
  receptor height, duration) per receptor hour, so R is derived rather than
  assumed. Report the normalized-residual diagnostic in the paper.
- The diagonal approximation ignores the 24 h and 72 h correlations, so the
  exact value will differ; the conclusion that R is oversized will not.

### 3. The "≤500 km anthropogenic" component is really a few cells around the station

From `spatial_operator_base.nc` for the 27 retained hours, the anthropogenic
near-region prior increment comes:

| Radius | Median share of the ≤500 km increment | Range |
| --- | --- | --- |
| < 25 km | 22 % | 1.5 to 64 % |
| < 50 km | 58 % | 11 to 90 % |
| < 100 km | 85 % | 27 to 97 % |

A single grid cell supplies a median 37 % (maximum 75 %) of the component.
The 500 km partition therefore does not separate "local" from "regional"; it
separates "the EDGAR allocation of Bukittinggi and Agam into the receptor
cells" from everything else. That allocation is the least trustworthy part
of any 0.1° inventory and the near field is where STILT is least reliable.

- Add an explicit near-field component (for example ≤ 50 km) with its own
  multiplier and a wider prior, and keep the 50 to 500 km ring separate.
- Report the receptor-cell contribution in Table 15 style for every hour.
- Cross-check the receptor-cell EDGAR flux against local activity data
  (population, road network, the landfill and rice areas near Bukittinggi).

### 4. Particle count for the inversion operator is too low

The inversion runs use 540 particles. Between the base seed and the
alternate seed, the prior increments at the four anchors change by up to
+65 % (far anthropogenic) and +38 % (fire); near anthropogenic moves by
−6 to +13 %. That numerical noise is of the same order as the posterior
multipliers being estimated (0.5 to 0.8).

- Rerun the 52 receptors with at least 2,000 particles, or average three
  seeds per receptor (the single-hour case already showed 10,020 is cheap).
- Until then, the seed spread belongs in R, not only in Table 9.

### 5. Nighttime receptors at an 865 m hill site are a different regime

Prior wetland increments are 38.7 ppb at 01:00 WIB versus 12.4 ppb at
13:00 WIB, and the 100 m mixing-floor test moves nighttime sensitivity by
23 to 47 % but daytime by under 10 %. The nighttime half of the fit is the
half the model cannot resolve.

- Make afternoon well-mixed hours the primary fit set. Use 3 to 4 h
  afternoon means (for example 12:00 to 16:00 WIB) rather than a single
  hour; this reduces representativeness error and raises n without the
  correlation problem of using every hour.
- Keep nighttime as a separate regime with its own representativeness term,
  or as a held-out test, rather than pooling.

### 6. The release height does not address the terrain deficit

Station elevation is 864.5 m; GDAS terrain at the nearest point is 407 m and
GFS 816 m. The 60 m sensitivity spans none of the GDAS gap and only part of
the GFS gap. The usual mountain-site practice is to release at the height
that places the receptor at its true altitude above the model terrain, or to
test a range up to that height.

- For GFS test roughly 50 m AGL; for GDAS roughly 460 m AGL. Report as a
  terrain-representativeness sensitivity alongside the existing 60 m test.

## Design-level improvements

### Meteorology

- GFS 0.25° here is a pseudo-analysis stitched from 3 h forecasts. ERA5 is a
  true hourly reanalysis at the same spacing and can be converted with the
  NOAA `era52arl` utility; the hourly cadence matters for the diurnal
  mountain circulation. It also has no convective fluxes, so it fixes timing,
  not item 1. (The NOAA S3 `gdas0p25` archive returns 404 for September
  2019; I checked.)
- A nested WRF run (for example 9/3/1 km) with cumulus output is the only
  route that addresses terrain, diurnal circulation and convection together.
  It is the "separate research stage" the plan already names; given items 1
  and 6 it should move up the list.

### Forward single-hour case

- 72 h is too short for the fire scenario: 84 % of the fire CO₂ increment
  comes from the oldest day. Rerun the case at 120 h on the widened domain,
  as the inversion already does.
- Add endpoint backgrounds for CO₂ (CarbonTracker CT2022 or CT-NRT) and CO
  (CAMS reanalysis) so the CO budget check becomes a real test. As it
  stands, GFS fire CO at 95.8 % of the observation leaves 22 ppb for a
  background that is plausibly 80 to 120 ppb, so the GFS scenario also
  over-closes; the report should say so rather than only faulting GDAS.
- Treat the 08:00 WIB receptor as what it is: a morning-transition hour at
  the 84th CO₂ percentile. It is a good case study; it is not representative
  and should not anchor the sector rankings.

### Sources and priors

- One inventory gives no prior spread. Add CAMS-GLOB-ANT or CEDS for
  anthropogenic, GFEI for oil and gas, and the WetCHARTs ensemble for
  wetlands. Use the spread across them as the prior uncertainty instead of
  the fixed ln 2.
- Apply EDGAR temporal profiles (hourly, weekly) to the monthly fields; the
  "+21.7 % timing sensitivity" already shows timing matters.
- Fire injection: request a second concentration layer (for example to 1 or
  2 km) in the same runs so an elevated-injection sensitivity can be computed
  without assuming everything enters below half the PBL.

### Evaluation

- With six withheld hours, 47.6 versus 40.0 ppb RMSE is not a distinguishable
  difference. Use leave-one-out across all 27 hours with a time buffer and
  report the paired RMSE difference with a block-bootstrap interval.
- Report the reduced chi-square and the normalized residual distribution
  for every fit variant; it is the single diagnostic that would have flagged
  item 2.

## Report structure

- The document is now 59 pages with four appendices bolted on in sequence.
  Split it: a core report (forward case + inversion, about 25 pages) and a
  technical companion (benchmark, domain extension, BARRA audit, definitions).
- Remove repeated boilerplate. "The 95 % interval for X includes unity"
  appears four times in a row; the two sentences on withheld RMSE appear
  verbatim in the summary, results, discussion and conclusions. Say each
  once.
- The scientific summary reads as a compliance log. Lead with the three
  things a reader should take away (where the footprint is, what the
  inventories imply, why the inversion is inconclusive), then the caveats.
- Give the BARRA negative result one paragraph and a pointer; it is a
  conversion screen, not a finding about BKT.

## Engineering and housekeeping

- The pipeline is 37 receptor-specific scripts. `a39` hard-codes `STAMP`,
  `MEMBERS` and branches on run-name prefixes to set `hours_back`; `a41`
  hard-codes the receptor and date range. A single case-configuration file
  (station, receptor times, met source, particles, domain, duration) read by
  `a37`, `a41` and `a46` would let the same chain run Jambi or another
  season without copying scripts.
- `CLAUDE.md` and `AGENTS.md` say "not a git repository"; it is one (branch
  `main`, two commits, large untracked tree). Either commit the BKT work or
  fix the statement.
- Both files point to `.claude/skills/ghg-analysis/SKILL.md`, which does not
  exist. Restore it or drop the reference.

## Suggested order

1. Fix the convection wording (docs and report), item 1. One hour.
2. Add the normalized-residual diagnostic and refit with a tuned transport
   error scale, item 2. One day.
3. Add the near-field component and receptor-cell audit, item 3. One day.
4. Rerun the 52 receptors at 2,000 particles or three seeds, item 4.
   Compute-bound, no new science.
5. Afternoon-mean receptors and terrain-height sensitivity, items 5 and 6.
6. Forward case at 120 h with CO₂ and CO backgrounds.
7. ERA5 or WRF driver, multiple inventories, report split.
