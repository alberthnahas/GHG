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
