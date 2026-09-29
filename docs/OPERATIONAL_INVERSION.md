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

## Three refusals, built in

**Land use is refused.** EDGAR excludes land use, land-use change and forestry,
so there is no EDGAR pattern to carry an Indonesian FOLU total. In Indonesia
that is the largest and most variable term. The crosswalk refuses IPCC 3B rather
than spreading peat and forest emissions over power stations and roads. FOLU
needs its own proxy, and the peatland layer already used in the methane work is
the obvious candidate.

**Carbon-dioxide equivalent is not mass.** A total in Gg CO2e cannot enter a
methane prior without a stated global warming potential; the wrong horizon is a
silent error of tens of percent. The contract requires an explicit `gwp` column
whenever the unit is CO2e.

**A zero pattern cannot be scaled.** If EDGAR puts no emission of a sector in a
province, no factor can put the reported total there. That province is refused
and listed.

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
