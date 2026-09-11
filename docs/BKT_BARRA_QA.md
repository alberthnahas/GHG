# BARRA audit and integrated-report QA

Date: 6 September 2026. Audit and documentation are complete. Meteorological
conversion readiness is false; no BARRA transport or inversion was run.

## Exact reviewed artifact

- File: `outputs/BKT_HYSPLIT_STILT_Footprint_Report.pdf`
- SHA-256: `0ebf6ee56670343cdda6a98df3882247d1316b26e3fe36c8fc1b15f332d731b2`
- Size: 27,422,483 bytes; creation time: 2026-09-06 10:51:28 WIB.
- 46 A4 pages, 22 figures and 17 tables.
- Every physical page, 1–46 inclusive, was visually inspected from the exact
  final build at 110 dpi. Review renders: `/tmp/bkt-barra-reviewed-haBJKW/`.
  Temporary renders are not required to reproduce the report.
- Text, equations, captions, tables, figures, references and page boundaries
  were checked. No clipping, overlap or stranded appendix heading remained.
  An earlier stranded definitions heading was fixed in the Markdown template.
  The layout checker now tests small appendix headings while excluding
  table-of-contents entries; both cases have regression tests.

## Executed validation

- All four `scripts/verify_all.sh` gates passed, zero failed. Final execution
  log: `/tmp/bkt-barra-reviewed-gates.log`.
- 81 BARRA provenance and numerical consistency checks passed. This verifies
  the audit, not fitness for conversion or atmospheric transport accuracy.
- 26 focused tests passed: BARRA quality edge cases, PDF layout, and existing
  methane inverse/operator tests. The full gates also executed their tests.
- Python compilation and `git diff --check` passed.
- Table 17 was compared with `field_quality.csv`: 1,982/102,794 = 1.93% at
  925 hPa; 308/108,228 = 0.28% at 850 hPa. Stricter 10 hPa-margin missing
  counts are 1,360 and 115, respectively. These counts apply separately to
  each of the six inspected field families, not independent samples.
- Native packed-field confirmations and surface pressure agree with the
  subset gap diagnosis. BKT terrain (1,007 m), surface pressure
  (899.8–902.9 hPa), and approximate 850 hPa height above terrain
  (497–521 m) agree with the CSV-derived appendix.

## Scope and remaining limitation

The bounded test covers 13 hourly timestamps on 9 September 2019 and 20
selected fields. It is not a full-period BARRA quality or skill evaluation.
Missing values above the supplied surface remain unresolved. The existing
GFS scientific results are retained; the report adds the negative conversion
screen as an integrated appendix. No raw observation edits, WRF simulation,
provider message, upload, commit, or unvalidated gap filling was performed.
Resumption requires compatible source data/provider guidance or an explicitly
authorized, independently validated reconstruction experiment.
