# BKT methane inversion: final verification record

Completed 5 September 2026. This is an internal QA record, not a separate
scientific report. The inversion is integrated into the existing canonical
`BKT_HYSPLIT_STILT_Footprint_Report.md` and its generated PDF.

## Exact reviewed artifact

- PDF: `outputs/BKT_HYSPLIT_STILT_Footprint_Report.pdf`
- SHA-256: `fae155af1dda06ca5f237985ab995e371847c9508f0d26b14aa7c4ea9cc82822`
- Size: 27,412,265 bytes; 44 physical A4 pages (cover plus printed pages 1–43).
- Content: 22 figures and 16 tables, including the original forward experiment.
- Final build: repository verification run, PDF creation 2026-09-05 18:32:29 WIB.
- Fresh Poppler render: `/tmp/bkt-inversion-final-review-T5DRGi/page-01.png`
  through `page-44.png`, 110 dpi, approximately 910 by 1287 pixels per page.
- All 44 images were individually viewed at readable scale, in page order,
  after this final build. Review was not limited to thumbnails or text extraction.
- SHA-256 was checked again after the visual review and was unchanged.

## Visual coverage

| Physical pages | Reviewed content | Outcome |
|---|---|---|
| 1–4 | Cover, contents, scientific summary, scope | Title intact; contents and section opening consistent; no orphan parent heading |
| 5–8 | Meteorology, observations, input tables, geographic context | Figures 1–2 and Tables 1–2 readable; captions attached; revised figure/table flow checked |
| 9–12 | Forward and inverse methods, units, equations, priors | Equations and symbols rendered; units/sign conventions and caveats legible |
| 13–18 | Results opening, footprints, transport diagnostics, sectors | Figures 3–7 and Tables 3–4 inspected; no empty region under the Results heading |
| 19–24 | Inventory/source maps, province and fire results | Figures 8–12 and Tables 5–6 inspected; color scales, boundaries, labels and captions readable |
| 25–28 | Receptor selection, prior budget, information content | Figures 13–16 inspected; excluded-hour gaps and legends visible; map masks and units stated |
| 29–32 | Posterior estimates, withheld evaluation, residuals | Figures 17–19 and Tables 7–8 checked against result tables; uncertainty and baseline comparison explicit |
| 33–36 | Assumption scenarios, transport tests, synthetic recovery, mass budgets | Figures 20–21 and Tables 9–12 inspected; intervals, scenario labels, sample counts and conditional units readable |
| 37–40 | Adjustment/endpoint maps, uncertainty, discussion, conclusions | Figure 22 and Table 13 inspected; no pixel-scale retrieval or operational validation claim |
| 41–44 | References, licensing, glossary, worked budgets | References retain numbering 1–13; Tables 14–16 intact; worked numerical budget reconciles |

No clipping, overlapping labels, stranded table headers/captions or orphan
section headings were observed in the final review. Standalone figure plates
retain centered white space; some tables move as complete captioned blocks.
Those are deliberate page-layout choices, not missing results. All pages,
including reference attribution and appendix pages, were included in review.

The preceding draft review caught a stranded parent heading and a reference
list restarting at one; both were corrected in the source renderer. Regression
tests now cover adjacent-heading reservation, ordered-list starting numbers
and rendered orphan headings. Cover hyphenation and early figure/table flow
were also corrected before the exact final render reviewed above.

## Executed checks

- 38 focused unit/regression tests passed: footprint, refinement, GFS sources,
  PDF layout, methane inversion and source operator.
- 183 independent numerical/provenance checks passed; evidence is
  `outputs/hysplit/inversion/inversion_validation.json` and its CSV table.
- All four `scripts/verify_all.sh` gates passed: document consistency,
  figure translations, PDF compilation/layout/scientific checks, and existing
  deck rendering (58, 23 and 20 slides). This does not claim a new manual
  review of unrelated decks.
- Final PDF layout checker reported no issues; compilation had no overfull boxes.
- All eight new inversion/acquisition/report/validation modules passed
  `py_compile`; `git diff --check` passed.
- Runtime logs: `/tmp/bkt-inversion-unit-tests.log` and
  `/tmp/bkt-inversion-full-gates.log`. Portable commands and host-specific
  dependency details are in `BKT_METHANE_INVERSION_REPRODUCIBILITY.md`.
- Reader-facing canonical report was searched for internal paths, credentials
  and unresolved TODO/FIXME markers; none were found.
- Established Indonesian GeoJSON retained; SHA-256:
  `95b33f62c93c83206f7d4cc573d55142b721738de6a7f32790dde2092cd4082b`.
- No commit, push, upload, raw-observation edit or destructive cleanup was made.
  Unrelated pre-existing workspace changes were preserved.

## Scientific cross-checks and interpretation limits

Selection reconciles 56 scheduled hours, four missing observations, 52 base
simulations and 25 failures of the predeclared 95% endpoint-retention screen,
leaving 21 fit and six withheld hours. All 14 preselected transport sensitivity
runs completed. The analysis retains 19 assumption scenarios, four buffered
weekly evaluations and 400 synthetic realizations.

Manual comparisons of rendered tables and prose with source CSVs included
posterior multipliers/intervals, withheld evaluation, synthetic recovery,
transport ranges, conditional regional/sector masses and the worked budget.
Independent programmatic reconstructions additionally check convolution,
posterior quantiles/predictions, positive-definite mismatch covariance,
MCMC diagnostics, evaluation RMSE, mass scaling, fire conservation, map
integral conservation and acquired input checksums.

The final withheld RMSE is 47.6476 ppb for the inversion, 85.9763 ppb for the
background-adjusted inventory and 39.9990 ppb for the background-only model.
All four source-multiplier 95% credible intervals include unity. The additive
posterior-mean worked budget is 1867.1865 ppb versus 1882.74 ppb observed;
the displayed residual is 15.55 ppb. These checks verify numerical consistency,
not independent emission truth.

CarbonTracker assimilates BKT; withheld local optimization is therefore not
fully independent global-boundary validation. Transport/domain losses,
mountain and convective representation, limited evaluation size, fixed source
patterns, climatological auxiliary fields and missing exchange processes
remain material limitations. Three raw native PBL diagnostics are negative
within their archive packing-precision scales; two eligible cases are omitted
only from the height scatter, with raw values and flags retained. No observation
was removed because it disagreed with the model.

This is a completed experimental inversion workflow and integrated scientific
assessment. It is not a validated regional emissions service, a facility-level
attribution, or evidence of a verified emission reduction.
