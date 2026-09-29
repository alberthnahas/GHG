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
- [ ] A FOLU proxy, so the largest Indonesian term can enter the prior at all.
