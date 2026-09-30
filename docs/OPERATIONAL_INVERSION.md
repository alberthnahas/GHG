# The inverse model, and what is ready for operations

Two earlier studies reached the same place. At the scale of a single afternoon,
the posterior does not predict better than the boundary field carrying a fitted
offset and trend, at either tower, for either gas. That is a statement about a
daily concentration prediction, not about the quantity a regional inversion
estimates, so this round changed four things and then asked the question again,
honestly, at every scale.

## What changed

**Transport error from the ensemble.** The previous error model multiplied one
tuned number by the total prior increment, which spread the same error over an
hour the seeds agreed on and an hour they did not. The shape now comes from the
seed spread already recorded for every component at every receptor; only the
amplitude is calibrated.

**A rotated biosphere.** Gross uptake and respiration correlate at 0.91 to 0.94
across the afternoon receptors. Fitting both inflates the posterior without
adding information, so the pair is rotated into the net flux, which the data
constrain, and the contrast, which they do not and which is held under a tight
prior.

**Aggregation scales.** Daily, weekly and monthly fits, each scored with a block
bootstrap, and a scale with fewer than eight independent bins is declared
unresolved rather than quoted.

**Information diagnostics.** Degrees of freedom for signal, the posterior to
prior uncertainty ratio per parameter, and chi-square consistency, written to
`outputs/operational/inversion_readiness.json` on every run.

## What it says now

| Gas | Scale | Bins | Chi-square | DOFS | Verdict |
| --- | --- | --- | --- | --- | --- |
| CO2 | daily | 78 | 0.97 | 1.84 | informed, not better than the null |
| CO2 | weekly | 15 | 0.99 | 1.20 | informed, not better than the null |
| CO2 | monthly | 5 | 0.25 | 1.08 | unresolved, too few bins |
| CH4 | daily | 26 | 1.49 | 1.44 | informed, not better than the null |
| CH4 | weekly | 5 | 1.00 | 1.22 | unresolved, too few bins |
| CH4 | monthly | 2 | 1.00 | 1.48 | unresolved, too few bins |

The observations do inform roughly one to two flux parameters, which is a real
result: a bulk regional scaling is constrained, and the chi-square says the error
model is consistent. What is not supported is a claim of predictive skill over
the boundary null at any scale where enough independent bins exist to test it.

Two findings are worth carrying forward.

**A monthly improvement appeared and then dissolved.** With the first error
model, monthly aggregation put the Jambi posterior 1.85 ppm ahead of the null
with an interval excluding zero. That came from measurement and local-mismatch
errors that were not averaged down within a bin, which over-inflated the errors
and over-damped the fit. Once each bin mean carried the error of a mean, the
same comparison moved to +0.17 ppm. The readiness gate would have refused it
anyway on five bins.

**The seed spread is the wrong magnitude.** The calibrated amplitude lands
between 7 and 12, so two or three seeds understate the true transport error by
about an order of magnitude. The ensemble is a good description of the shape and
a poor one of the size. More seeds, or a driver-to-driver comparison, would be
the way to measure it rather than calibrate it.

## Operational status

Operational today: the station monitor, episode transport, and this readiness
harness. A deployment should read the verdict in `inversion_readiness.json` and
present the inversion as a diagnostic, with its degrees of freedom, until a
combination reports `operational`.

Not operational: the inversion as a predictor of concentration. Reporting the
multipliers as validated flux corrections would repeat the error this project
has already corrected twice.

The gate that would change the verdict is data volume at the aggregation scale,
not further tuning. Eight independent weekly bins at both towers with the
current sampling needs roughly two more months of joint record.

## Running it

```bash
python3 scripts/a99_operational_inversion.py campaign           # both gases, every scale
python3 scripts/a99_operational_inversion.py fit --gas ch4 --scale weekly
```

# The local emission inventory

SIGN-SMART (Sistem Informasi Gas Rumah Kaca Nasional, KLH) reports at national,
provincial and district level. EDGAR is gridded but global. The prior wants
both: Indonesian magnitudes on a pattern fine enough to convolve with a
footprint.

`a100_local_inventory.py` keeps each for what it is good at. EDGAR gives the
pattern inside a province, SIGN-SMART gives that province's magnitude per sector
per gas, the factor applies inside the province only, and the province total
afterwards equals the reported total by construction. Every factor is written to
a ledger with its source.

## The refusals, and what answers them now

Each refusal existed because something was genuinely missing. Each now has a
component, and each answer is recorded in the ledger rather than applied
silently.

**Land use now has its own proxy** (`a101_folu_proxy.py`). EDGAR excludes land
use, so IPCC 3B is still never scaled onto it. Instead it is placed on a pattern
built for it, from two processes that behave differently: drained peat, as the
Indonesian peatland extent weighted by the land cover that implies how deeply it
is drained, and fire, as GFED burned carbon split by whether it burned over
peat. Over Sumatra, 41.9% of burned carbon falls on peat.

The absolute magnitude is deliberately left out. Emission factors for drained
tropical peat are contested: Murdiyarso et al. (PNAS 2024) report 8.13 to 80.77
Mg CO2 per hectare per year across land covers and water tables, a spread of
ten. Rather than pick a number, the proxy carries a normalised pattern and
SIGN-SMART supplies the magnitude, which is the same division of labour every
other sector already uses. Categories 3B, 3B1 (drainage) and 3B2 (fire) are
available, and the land-cover weights are relative, stated and editable.

**Carbon-dioxide equivalent converts against a stated horizon.** A total in Gg
CO2e still cannot enter a methane prior with an unstated potential, because the
wrong horizon is a silent error of tens of percent. It can now be converted by
naming one: `--gwp-set AR6`, `AR5` or `AR4` fills the potential, and the horizon
used is appended to that row's source so the choice travels with the number.

**A zero pattern has a last resort.** If EDGAR puts no emission of a sector in a
province, no factor can place the reported total there. The default is still to
refuse and list it. With `--fallback`, the total is spread evenly over the
province instead, and the ledger marks that row `fallback_even_spread`. An even
spread is worse than a real pattern and better than dropping a reported total,
and it is never silent.

## Validation

With no SIGN-SMART export on this machine, the engine is validated where the
answer is known exactly: feeding EDGAR its own provincial totals must leave
every factor at 1.0 and the grid untouched, and it does, to 1e-9. Scaling tests
confirm each province then holds exactly what was reported, and that cells
outside the declared provinces do not move.

Building this surfaced a real error. Assigning grid cells to provinces by
intersection gives a shared border cell to both neighbours, so a factor applied
twice would break the mass the ledger promises. Cells are now assigned by centre
containment, which is disjoint by construction; the summary reports how much
emission falls in cells whose centre is offshore.

## Where to spend the inventory effort

The towers are not sensitive to Indonesia evenly. Weighting each province's
gridded emission by the mean footprint:

| Tower | Provinces carrying the modelled anthropogenic signal |
| --- | --- |
| Bukit Kototabang | Sumatera Barat 77%, Riau 16% |
| Jambi | Jambi 67%, Riau 20% |

Four provinces carry almost all of what this two-tower network can see:
Sumatera Barat, Riau, Jambi and Sumatera Selatan. A SIGN-SMART export covering
those four, for the energy, fugitive, industry, agriculture and waste
categories, is worth more to the inversion than a complete national table.

## Running it

```bash
python3 scripts/a100_local_inventory.py template                     # contract and crosswalk
python3 scripts/a100_local_inventory.py localise --export signsmart.csv --gas CO2 --year 2023
python3 scripts/a100_local_inventory.py influence --gas CO2 --year 2023
```

The required columns are `region_level, region_name, ipcc_code, sector_name,
gas, year, value, unit, source`, plus `gwp` when the unit is CO2e. Province
names are matched without regard to case or spacing.


# Where a better inventory actually helps

Localising is work, and it should go where it changes an answer.
`a102_prior_audit.py` decomposes the modelled signal at the towers by component
and asks of each whether a national inventory reports it at all. The shares are
covariance shares, so they sum to the whole signal rather than to more than it.

| Gas | Component | Share of the modelled signal | In a national inventory |
| --- | --- | --- | --- |
| CO2 | biosphere, BKT | 52.8% | no |
| CO2 | biosphere, Jambi | 42.3% | no |
| CO2 | fossil within 500 km | 5.1% | yes |
| CO2 | fossil beyond | 0.5% | yes |
| CH4 | anthropogenic within 500 km | 64.2% | yes |
| CH4 | anthropogenic beyond | 18.6% | yes |
| CH4 | natural wetlands | 18.6% | no |
| CH4 | fire | 0.6% | partly, through FOLU |

**The answer is asymmetric, and it should change what is asked of KLH.** A
national inventory can reach 82.8% of the methane signal and 5.6% of the carbon
dioxide signal. Nineteen twentieths of what the towers see in carbon dioxide is
the terrestrial biosphere, which no national inventory reports, however good the
export.

So the SIGN-SMART effort should be prioritised for methane. For carbon dioxide
the binding constraint is a biosphere prior, not an emission inventory, and
localising fossil emissions will move that gas very little whatever the quality
of the data.

Combined with the province influence table, the request that buys the most is:
methane, for Sumatera Barat, Riau, Jambi and Sumatera Selatan, for the energy,
fugitive, agriculture and waste categories, plus land use if it can be separated
into drainage and fire.

## Running it

```bash
python3 scripts/a101_folu_proxy.py build --bounds 94 -12 142 7 --resolution 0.1
python3 scripts/a101_folu_proxy.py weights
python3 scripts/a102_prior_audit.py audit
python3 scripts/a100_local_inventory.py localise --export signsmart.csv --gas CH4 --year 2022 \
    --gwp-set AR6 --folu-proxy outputs/inventory/folu_proxy_indonesia.nc
```

## Sources

- Murdiyarso et al., Refining greenhouse gas emission factors for Indonesian
  peatlands and mangroves, PNAS 2024, for the drained-peat range carried here.
- IPCC 2013 Wetlands Supplement, for the gain-loss approach Indonesia applies to
  organic soils. Its Tier 1 default table was not retrieved for this build, so
  no value is quoted from it.
- SIGN-SMART reports at national, provincial and district level. Its sector
  naming, gases and units are not stated on its public pages, so the contract
  requires them to be declared rather than assumed.


# Reading a real export, and where a language model is allowed

The engine wants an IPCC code. A real SIGN-SMART export carries Indonesian
sector names written by whoever filled the form. `a103_sector_matching.py` maps
them, rules first:

| Label | Mapped to |
| --- | --- |
| Pembangkitan Listrik | 1A1 |
| Industri Pengolahan | 1A2 |
| Transportasi Darat | 1A3 |
| Emisi Fugitif Migas | 1B |
| Peternakan Sapi Perah | 3A |
| Lahan Gambut Terdrainase | 3B1 |
| Kebakaran Hutan dan Lahan | 3B2 |
| Pengelolaan Limbah Padat Domestik | 4 |

The keyword table is deterministic, offline and auditable, and it resolves the
common wordings. A name it cannot resolve is reported, never guessed.

TypeSafe's Jev is wired in for the tail only: a typed choice over the IPCC
categories with a probability, consulted solely for names the rules missed, only
when `TYPESAFE_API_KEY` is set, and applied only above a stated threshold. The
method and the confidence travel with every mapping.

**It is deliberately kept out of everything else.** The inversion, the readiness
gates, the mass conservation and the tracer ratios are numerical and must be
recomputable exactly by anyone who doubts them. Putting a probabilistic judgment
inside any of those would trade auditability for nothing, because a threshold
already does the job exactly. The one place semantic understanding genuinely
helps is reading free text at the ingestion boundary, so that is the only place
it is used.


# The biosphere prior, and the finding that reframes the programme

The audit put 95% of the modelled carbon dioxide signal on the terrestrial
biosphere, so that prior, not the emission inventory, is what limits that gas.
Two sources existed and each failed differently. CarbonTracker CT-NRT is
assimilated, so its magnitude and seasonality carry real information, but its
sub-daily phase inverts for a week over both tower cells. The diagnostic prior
cannot invert, but the inversion scaled it to between 0.20 and 0.42, meaning its
amplitude was two to five times too large.

A daily mean is insensitive to a phase error and a diurnal shape is insensitive
to a magnitude error, so `a104_biosphere_prior.py` takes the daily mean and the
diurnal amplitude from CarbonTracker and the shape from the diagnostic model.
The amplitude is measured only on days when CarbonTracker's own phase is sound,
so the inverted week cannot contaminate it.

| Property | Result |
| --- | --- |
| Daily mean reproduces CarbonTracker | to 3e-15 umol m-2 s-1, by construction |
| Inverted-phase cell days | 201,374 in CT-NRT, 520 in the hybrid |
| Afternoon drawdown at the towers | -13.5 and -15.4 become -5.5 and -5.2 |
| Diurnal amplitude at the towers | 23 and 26 become 10, against CT-NRT's 8.5 and 9.0 |

The amplitude is independently corroborated. The inversion had been scaling the
old prior by 0.20 to 0.42, implying it wanted a drawdown near -3 to -6. The
hybrid, built only from CarbonTracker's daily mean and its phase-correct
amplitude, gives -5.5 and -5.2. Two separate routes reached the same number.

## It did not make the inversion beat the null

On identical 2023 receptors, the honest comparison:

| Prior | Prior RMSE | BKT difference | Jambi difference |
| --- | --- | --- | --- |
| diagnostic | 6.75 ppm | +0.85 (-0.65 to +2.42) | -0.19 (-2.22 to +1.67) |
| hybrid | 6.91 ppm | +0.43 (-0.41 to +1.45) | +0.45 (-0.57 to +1.22) |

Better at BKT, worse at Jambi, neither resolved, and the prior error barely
moved. A better biosphere prior was necessary, because the old one was
demonstrably wrong in phase and amplitude, and it was not sufficient.

## Why nothing helps: the error budget

`a99_operational_inversion.py budget` answers it in one table.

| Gas | Source signal | Transport error | Measurement and local | Background | Total | Signal to error |
| --- | --- | --- | --- | --- | --- | --- |
| CO2 | 6.54 ppm | 4.35 | 2.01 | 1.00 | 4.90 | **1.34** |
| CH4 | 73.11 ppb | 56.34 | 20.62 | 10.00 | 60.82 | **1.20** |

The source signal is barely above the noise it arrives through, and transport is
the dominant term for both gases. That single fact explains every negative
result in this work: why the posterior loses to a fitted constant, why the
nuisance-only model beats it, why four times the sample did not rescue it, and
why neither a localised inventory nor a corrected biosphere prior changes the
verdict. The sources are not what is missing.

**This should redirect the programme.** Priors are no longer the binding
constraint, and further work on them will not flip the verdict. Cutting the
transport error by a factor of three to four would take the signal-to-error
ratio from about 1.3 to about 4, which is where a regional inversion starts to
constrain fluxes. The candidates, in order of expected return:

1. Finer meteorology. GFS at a quarter degree is about 28 km, which cannot
   resolve the terrain at BKT or the coastline at Jambi. A WRF run at 3 to 9 km
   is the obvious step, and this machine already holds a WRF-GRK workspace.
2. Measure the transport error instead of calibrating it. The calibrated
   amplitude of 7 to 12 says two or three seeds understate it roughly tenfold. A
   driver-to-driver comparison, GFS against ERA5, would measure the systematic
   part that extra seeds of one driver cannot see.
3. Observations less sensitive to transport, such as column measurements, where
   the boundary-layer error that dominates a surface receptor largely cancels.


# The local inventory, used

SIGN-SMART's own database sits behind a login. Indonesia's reporting to the
UNFCCC is produced from that inventory and is public, so PRIMAP-hist v2.6.1 in
its HISTCR scenario, which prioritises country-reported submissions over
third-party estimates, carries the same national numbers by another route. It is
downloaded with its checksum to `data/bkt_sources/primap/`.

## What the country reports against what EDGAR assumes

Indonesian methane for 2022, inside the country mask:

| IPCC category | EDGAR (Gg) | Reported (Gg) | Factor |
| --- | --- | --- | --- |
| 1A fuel combustion | 215.6 | 113.0 | 0.52 |
| 1B fugitive | 7542.6 | 666.0 | **0.09** |
| 2 industrial processes | 3.5 | 3.7 | 1.06 |
| 3A and 3C agriculture | 4141.4 | 3080.0 | 0.74 |
| 4 waste | 2805.1 | 4760.0 | **1.70** |

EDGAR puts eleven times more fugitive methane in Indonesia than the country
reports, and forty percent less waste methane. Whether that gap is EDGAR's
spatial allocation, a real under-report, or a definitional difference is exactly
the kind of question a tower network exists to answer.

## What it does to the towers

| Tower | Anthropogenic prior before | After | Dominant change |
| --- | --- | --- | --- |
| Bukit Kototabang | 121.2 ppb | 101.0 ppb | fugitive 16.5 to 1.5 |
| Jambi | 200.1 ppb | 105.9 ppb | fugitive 117.7 to 10.4 |

The operator is linear in the flux, so the per-sector factors apply to the
per-sector responses already stored, without re-running any footprints. The near
and far columns are rescaled in the proportion the sectors imply, which assumes
the sector mix beyond 500 km resembles the mix within it; that is worth stating,
and it is second order against factors spanning 0.09 to 1.70.

## And what it does to the inversion

| Prior | Prior RMSE | BKT difference | Jambi difference |
| --- | --- | --- | --- |
| EDGAR | 99.5 ppb | -0.1 (-8.9 to +9.1) | +4.8 (-8.4 to +20.8) |
| localised | **57.7 ppb** | **-1.6** (-6.4 to +3.7) | **-2.1** (-10.5 to +8.2) |

The prior error falls by 42%, and for the first time in this work the posterior
predicts better than the boundary null at both towers rather than one or
neither. The Jambi difference changes sign. Weekly aggregation moves further in
the same direction, BKT -8.45 ppb, though on five bins it stays unresolved.

Nothing here is resolved at 95%: every interval still spans zero, and the gate
still reports "informed, not better than the null" because that is what the
evidence supports. But the direction is now consistent across both towers, both
scales and the prior error, which it never was before.

**This corrects something stated earlier in this work.** After the biosphere
prior failed to improve carbon dioxide, the error budget was read as meaning
priors were no longer the binding constraint for either gas. That was too
general. The audit had already said a national inventory could reach 82.8% of
the methane signal against 5.6% of carbon dioxide, and the methane result
follows the audit, not the generalisation. Transport dominates the error budget
for both gases; for methane the prior error was large enough that reducing it
still moved the answer.

---

# Source attribution and the maps

The readiness campaign answers whether the inversion may be trusted. It does not
answer what the towers are actually seeing, and for most of this project's life
the report carried no maps for what is, from end to end, a spatial argument.
`a109_operational_maps.py` and `a110_attribution.py` close both gaps.

## Where the numbers come from

Nothing here re-runs a footprint. `a84` already writes
`outputs/hysplit/two_receptor/inversion/spatial_operator_{bkt,jmb}.nc`, which
holds, per receptor, the seed-mean time-summed footprint, the gridded prior
contribution of each component in ppb, and a distance field. Masking that by
peat extent, by province, by district or by distance band is arithmetic on
arrays that already exist, and it takes seconds.

One identity makes the convolutions safe to write. A mole-fraction footprint
stored in ppm per umol m-2 s-1 is numerically the same number as ppb per
nmol m-2 s-1, so a methane flux expressed in nmol m-2 s-1 convolves straight to
ppb and a carbon dioxide flux in umol m-2 s-1 convolves straight to ppm. That is
why `a110.nmol_field` scales by 1e9 for methane and 1e6 for carbon dioxide from
the same kilograms-per-year field.

## Stages

```
python3 scripts/a110_attribution.py all        # eight tables into outputs/operational
python3 scripts/a109_operational_maps.py       # six maps into outputs/operational/figures
python3 scripts/a111_report_questions.py       # the question index, printed
```

`a110 budget` needs `attribution_budget.csv` before `peat` runs, because the
peat stage rescales the anthropogenic term by the localisation ratio the budget
computes; `flux` needs `attribution_provinces.csv`, because it quotes the
posterior over the provinces the towers actually see. Running `all` orders them
correctly.

## What the tables say

- **The prior overpredicts before any fit.** The global gridded inventory says
  115 ppb of methane should arrive above background at Bukit Kototabang and
  147 ppb at Jambi; 56 and 47 ppb arrive.
- **The towers see four provinces.** Sumatera Barat, Jambi, Sumatera Selatan and
  Riau. Nothing outside Sumatra reaches one percent at either tower.
- **The signal is concentrated.** Muara Enim carries 8.3% of the Bukit Kototabang
  methane signal from 0.02% of its footprint sensitivity, a ratio of 415: one or
  two cells of the gridded inventory set a large part of what the model expects.
- **Peat is a lowland question.** 23% of the modelled methane signal at Jambi and
  2.9% at Bukit Kototabang, by three separable routes.
- **The detection limit is the operational number.** Nothing in the campaign is
  constrained better than 67%, so a change smaller than about a factor of two is
  invisible to this network whatever the record length.

## Cartography

Maps follow the shared standard: a quiet base with neighbouring land in grey and
the study area off-white, the high-resolution world layer outside Indonesia and
the 38-province layer inside it, sequential scales for magnitudes and a diverging
scale centred on one for the inventory ratio, explicit zorder, a 300 dpi raster
and a vector companion. Panel boxes are laid out in inches from the extent's
aspect ratio rather than in figure fractions, which is what keeps an equal-aspect
map from leaving a band of white space. Raster layers are marked `rasterized` so
the vector PDF stays a few hundred kilobytes rather than tens of megabytes.
