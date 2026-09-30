# Operational inverse model and local inventory

Brief (2026-09-29): make the CO2 and CH4 inverse model operational, referring to
the DISPERSI GHG Model; and develop a local emission inventory from SIGN-SMART
(KLH/KLHK) on top of the established global inventories.

Completion criterion: both gases run through one inversion that reports, on
every run, whether the data constrained anything, with gates that a deployment
can read; and a local-inventory pipeline that converts a SIGN-SMART export into
a gridded prior with conserved mass and a provenance ledger.

## A. Inversion, ready for operations

- [x] A1 transport error from the measured seed ensemble spread, replacing the
      single tuned scalar that forces reduced chi-square to one
- [x] A2 biosphere reparameterisation: net flux and diurnal amplitude instead of
      two collinear columns (measured r 0.91 to 0.94)
- [x] A3 aggregation scale: fit and score weekly and monthly means, not single
      afternoons. This is the decisive test; daily prediction is dominated by
      transport noise and is not what a regional inversion estimates
- [x] A4 information diagnostics on every run: degrees of freedom for signal,
      posterior over prior uncertainty, chi-square consistency, cross-validated
      skill against the boundary null, with explicit pass or fail gates
- [x] A5 one interface for CO2 and CH4; both gases scored the same way
- [x] A6 readiness verdict written to JSON for a deployment to consume

## B. Local emission inventory from SIGN-SMART

- [x] B1 data contract for a SIGN-SMART export and the sector crosswalk to
      EDGAR; the export itself is not on disk and must be supplied
- [x] B2 provincial downscaling engine, mass conserving per province, per
      sector, per species, against the 38-province boundary asset
- [x] B3 validation: mass conservation, province coverage, comparison against
      the global inventory it replaces, and the effect on the inversion prior
- [x] B4 wire into DISPERSI, extending its national_scaling hook from one
      national factor to per-province factors

## C. Deployment

- [ ] C1 port to DISPERSI as the operational implementation
- [x] C2 tests for every new unit; all four GHG_Analysis gates still pass
- [x] C3 documentation: what is operational, what is diagnostic, and why

## Decisions and findings

- 2026-09-29: DISPERSI already carries the monitor, episode transport and the
  skill test, and reports the same negative result for methane (posterior 31.0
  against boundary null 31.9 ppb, difference -0.9, interval -16.6 to +14.7).
  Its bundle builder has a national_scaling hook that substitutes a single
  factor inside a country mask, with a ledger. That is the insertion point for
  SIGN-SMART, extended to provinces.
- 2026-09-29: no SIGN-SMART or KLHK data found anywhere on HDD2.

## Findings from this round

- The improved inversion informs one to two flux parameters (DOFS 1.08 to 1.84)
  with a consistent chi-square, but no aggregation scale with enough independent
  bins beats the boundary null. Verdicts in
  `outputs/operational/inversion_readiness.json`.
- A monthly improvement appeared (Jambi -1.85 ppm, interval excluding zero) and
  dissolved to +0.17 once measurement and local-mismatch errors were averaged
  down within a bin as they must be. The readiness gate would have refused it
  anyway on five bins. Found before it was reported, not after.
- The calibrated transport amplitude is 7 to 12, so the two or three seed spread
  understates true transport error by about an order of magnitude. The ensemble
  describes the shape well and the size badly. More seeds, or a driver-to-driver
  comparison, would measure it instead of calibrating it.
- Province influence: BKT's modelled anthropogenic signal is 77% Sumatera Barat
  and 16% Riau; Jambi's is 67% Jambi and 20% Riau. Four provinces carry almost
  all of what this network can see, so a SIGN-SMART export covering Sumatera
  Barat, Riau, Jambi and Sumatera Selatan is worth more than a national table.
- Assigning grid cells to provinces by intersection double-counts shared border
  cells. Both this repository and DISPERSI now assign by cell centre.
- FOLU (IPCC 3B) cannot be scaled onto EDGAR, which excludes land use. In
  Indonesia that is the largest term, and it needs its own proxy; the peatland
  layer from the methane work is the obvious candidate.

## Still open

- [ ] C1 port the readiness harness itself into DISPERSI (the localised
      inventory already integrates as a gridded input, and DISPERSI's scaling
      hook now takes per-province rows)
- [ ] A SIGN-SMART export for the four provinces that matter. Not on this
      machine; the contract and template are in `config/signsmart_template.csv`.
- [x] A FOLU proxy (a101): peat drainage weighted by land cover, plus GFED fire split by peat.

## Round two, 2026-09-29

- All three refusals answered. FOLU has its own proxy (a101) and is never scaled
  onto EDGAR; CO2e converts against a stated GWP100 horizon (--gwp-set); an empty
  global pattern can fall back to an even spread, marked as such in the ledger.
- Prior audit (a102): a national inventory can reach 82.8% of the methane signal
  and 5.6% of the carbon dioxide signal. Nineteen twentieths of what the towers
  see in carbon dioxide is the terrestrial biosphere, which no national inventory
  reports. SIGN-SMART should therefore be prioritised for methane.
- Over Sumatra 41.9% of GFED burned carbon falls on peat; Indonesia-wide 35.4%.
- TypeSafe Jev wired in at the ingestion boundary only (a103), for free-text
  Indonesian sector names the keyword rules cannot resolve. Kept out of the
  inversion, the gates and the ratios, which must stay exactly recomputable.

## Still open

- [ ] A SIGN-SMART methane export for Sumatera Barat, Riau, Jambi and Sumatera
      Selatan. Highest value item; everything else is built and waiting.
- [ ] A biosphere prior, which is what actually limits carbon dioxide here.
- [ ] Absolute FOLU emission factors, if a magnitude is ever needed without a
      reported total: the published range spans a factor of ten.

## Round three, 2026-09-29: the local inventory is in the model

- SIGN-SMART's database needs a login. Indonesia's UNFCCC reporting comes from
  the same inventory and is public, so PRIMAP-hist v2.6.1 HISTCR (country-
  reported priority) supplies the national totals, downloaded with checksum.
- EDGAR against Indonesia's reported 2022 methane: fugitive 7543 -> 666 Gg
  (factor 0.09), waste 2805 -> 4760 (1.70), agriculture 4141 -> 3080 (0.74),
  fuel combustion 216 -> 113 (0.52).
- Effect at the towers: Jambi's anthropogenic prior falls 47%, almost all of it
  fugitive (117.7 -> 10.4 ppb); BKT falls 17%.
- Effect on the inversion: prior RMSE 99.5 -> 57.7 ppb, and the posterior beats
  the boundary null at BOTH towers for the first time (BKT -1.6, Jambi -2.1),
  with narrower intervals. Still not resolved at 95%, and the gate still says so.
- Correction to an earlier statement: "priors are no longer the binding
  constraint" was too general. It holds for carbon dioxide, where the biosphere
  dominates and a better prior changed nothing. For methane the audit's 82.8%
  was right and the prior mattered.
- Engine fix: several IPCC categories sharing one EDGAR sector are now summed
  before the factor is computed, because 3A livestock and 3C rice both live in
  EDGAR AGRICULTURE and comparing either alone understates the reported total.

## Round four, 2026-09-29: the report becomes a scientific one

The previous version documented the model. It did not answer the questions a
monitoring programme is funded to ask, and it carried no maps for what is
fundamentally a spatial argument. Both are fixed.

- Source attribution (a110), from the spatial operator files that already held
  the per-receptor gridded contribution of every component, so no footprint was
  re-read. Eight tables: the record, distance bands, transport age, provinces,
  districts, the methane and carbon dioxide budgets, the peat decomposition, the
  posterior read as emission, and the detection limit.
- Six publication maps (a109): the mean footprints, the reported against global
  inventory, the land-use proxy, provincial and district influence, and where
  the peatland methane reaching Jambi is emitted.
- The peatland answer, which was the question that prompted this: peat carries
  34.3 of the 147.5 ppb modelled methane signal at Jambi (23%, and 95 ppb on the
  most peat-influenced afternoon) against 2.9% at Bukit Kototabang. Three routes,
  separated: anthropogenic on drained peat 23.1 ppb, peat swamp through the
  wetland prior 10.8 ppb, fire 0.4 ppb. Indonesia reports no methane from drained
  organic soils, only carbon dioxide and nitrous oxide, so that route enters
  through the wetland prior and through agriculture and waste on peat.
- The detection limit is now stated: no parameter in the campaign is constrained
  better than 67%, and the near-field methane term stands at 88%. An emission
  change smaller than about a factor of two cannot be seen by this network.
- The posterior is quoted over the four provinces the towers see, never
  nationally, because a national figure would assume the correction holds where
  neither tower has sensitivity.
- Appendix A answers 75 questions, generated from the same CSVs the sections use
  (a111), so an answer cannot drift from its table.
- Chemistry and units are typeset (CO2 and CH4 with subscripts, micromol per
  square metre per second with superscripts); the validator now fails the build
  if plain ASCII forms reappear.
- Two data faults found and fixed on the way: the flux table had been reading
  local_inventory_co2_2023_folu.nc, a 500 Gg test export over a small box, where
  the inversion's land-use response came from the full file (241,354 Gg); and the
  question generator read the carbon dioxide "fire" row when asked for methane,
  because both budgets carry a component of that name.
- One resolved result surfaced while checking the appendix against its own table:
  the near-field methane multiplier excludes one at 95% under the global gridded
  inventory (0.25, 0.11 to 0.47) and under the reported national totals (0.47,
  0.18 to 0.89), and stops excluding it under the provincial totals (0.61, 0.22
  to 1.24). Under the stated error model the observations reject the global
  inventory's magnitude where they can see and stop rejecting it once Indonesia's
  own provincial figures set it. That is a different test from the skill gate,
  which nothing passes, and the report now says so explicitly in both places.
- Delivered a first page with `CO\textsubscript{2}` printed literally. The title
  block is escaped like any other text, so raw LaTeX written into `title_meta`
  prints verbatim; chemistry goes in as Unicode and the escaper maps it. Found by
  Alberth, not by any gate, because the gates read the markdown and the compile
  log and nothing read the rendered page. The validator now scans the PDF text
  for leaked backslash commands and checks that the title page names both gases.
- Table 13 had grown to 25 rows, which cannot share a page with text, so the
  preceding page came out nearly empty. Split by gas into Tables 13 and 14.
- Figure labels carried plain CO2 and CH4; they are subscripted now too.
