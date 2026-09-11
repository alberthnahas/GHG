# BKT domain and prior-budget extension: final QA

Status: accepted on 9 September 2026 after complete simulation, numerical,
report, and rendered-artifact review.

## Scope and scientific boundary

- The extension covers the 52 available BKT receptor hours, a matched original
  versus widened 120-hour transport comparison, and a pre-declared five-case
  methane surface-plus-endpoint-background matrix at 72, 120, and 168 hours.
- No gas value selected a simulation. No inversion was refitted, and the work
  does not claim atmospheric validation, source attribution, or a seasonally
  representative result.
- The central paired result is a -5.3829 ppb change in the retained-hour mean
  net prior surface methane term; its three-day block-bootstrap 95% interval is
  -19.4881 to +9.2502 ppb and therefore includes zero.
- The observed recovered-minus-retained methane contrast is -28.3642 ppb
  (95% interval -52.5032 to -2.3170 ppb), but retention is strongly confounded
  by calendar time: 26/39 September hours passed the original screen versus
  1/13 hours during 1-6 October. This contrast is not a transport or source
  attribution.

## Numerical and provenance checks

- All 52 widened 120-hour runs and all 30 representative
  receptor-domain-duration scenarios completed and passed live receipt,
  configuration, meteorology-path, output-checksum, particle-ledger, finite
  footprint, nonnegativity, time-coverage, terrain, endpoint, flux-coverage,
  and concentration-budget-closure checks.
- The independent extension validator passed 392 checks for 52 unique full
  receptors and 30 unique convergence scenarios.
- Nine focused domain-extension tests passed. The broader PDF gate also passed
  20 existing layout/inversion tests.
- Reported decomposition and observed-group values were manually reconciled to
  the generated CSV tables. The report builder formats those CSV values rather
  than carrying duplicate hand-entered results.
- Python byte compilation passed for the four extension scripts; shell syntax
  passed for the verification runner. `git diff --check` reported no whitespace
  errors. Existing unrelated working-tree changes were preserved.

## Project gates

The exact final sources were checked with
`GHG_SCIENTIFIC_PYTHON=/run/media/workstation-llm/HDD2/.venv/bin/python bash scripts/verify_all.sh`:

1. Documents internally consistent: passed, 0 problems.
2. Figure translations: passed, 0 untranslated strings.
3. PDFs: passed, 0 overfull boxes, 0 stray table headers; independent GFS,
   inversion, and domain-extension report checks passed.
4. Rendered decks: passed, 0 layout issues across 58, 23, and 20 slides.

The verification runner now consistently uses `GHG_SCIENTIFIC_PYTHON` for
PyMuPDF-based PDF and slide checks. The earlier failed invocation reflected a
missing system-Python package, not a report defect.

## Exact final PDF review

- Artifact: `outputs/BKT_HYSPLIT_STILT_Footprint_Report.pdf`
- Format: A4, 59 pages.
- SHA-256: `4877d7f436579f4c16d9d9be9dc70066d75541bf5f022de9d438ce76161192d9`
- Every page was inspected at 144 dpi (1191 by 1684 pixels) at readable scale.
  Sol reviewed pages 1-29 and all pages altered by pagination, including final
  pages 41-44. Terra independently reviewed pages 30-40 in the earlier render,
  which are pixel-identical in the final build, and exact-final pages 45-59,
  including every new appendix page.
- After the final gate rebuilt the PDF, all 59 release-page rasters were
  pixel-identical to the reviewed post-layout render. This confirms that the
  checksum above belongs to the exact visually reviewed content, despite the
  PDF metadata timestamp changing during the gate rebuild.
- Review found no clipping, overlap, blank or orphan page, unreadable figure or
  table, broken caption, missing folio, or reader-facing internal path/script
  leakage. Conclusions, References, and the new full-ensemble appendix begin on
  fresh pages with correct running headers.
- The final page is intentionally sparse after the closing limitation
  paragraph; it is neither blank nor an orphan and is not a release blocker.
