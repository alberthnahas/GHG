# BKT PDF layout and handoff verification

Scope: fix the spurious continuation header above Table 7 on printed page 22;
preserve all scientific content and existing unrelated work. No model rerun.

- [x] Inspect the reported page and identify the checker blind spot.
- [x] Save the requested global handoff-review preference as a memory note.
- [x] Verify the new regression rejects the existing defective PDF.
- [x] Measure each caption and table as a single page-fitting object.
- [x] Rebuild; run focused tests, numerical checks and all four repository gates.
- [x] Render the final build and inspect every full-size page, including adjacent
      page transitions, all tables, figures and equations.
- [x] Record final PDF checksum and per-page review coverage; review the diff.

Acceptance: no duplicated or orphaned table headers/captions, no stranded
headings, no clipped/illegible elements, no accidental large gaps in text flow,
and no scientific content changes. Intentional figure-only pages, the title
page and final-page whitespace must be distinguished from layout defects.

The strengthened checker rejected physical page 23 (printed page 22) of the
previous 26-page PDF. Four synthetic/source regression tests passed, including
genuine table continuations that must remain allowed. The first rebuilt PDF
compiled cleanly with measured, inseparable table-caption blocks.

## Final handoff evidence, 5 September 2026

The final PDF has 24 A4 pages, 12 figures and 9 tables. The reduction from 26
pages comes from table placement, not removed scientific content. All 24 unit
tests (including four new layout tests), 133 dedicated GFS checks and all four
repository gates passed. The build has zero overfull boxes and the strengthened
rendered-PDF check reports zero orphaned table headers. `git diff --check`
passed; unrelated user changes were preserved. No models or source arrays were
changed, and the canonical report Markdown checksum is unchanged.

- Final PDF SHA-256:
  `62e7fbdc27a5ede114ed849124f5bfe938bae484faa046e689e0c642422c8425`
- Unchanged canonical Markdown SHA-256:
  `466fd752cb2c0962e31430f0acbcc48e9d5f42029044f1e96968ddb9d18bdfb4`
- Final render directory:
  `outputs/hysplit/gfs/analysis/pdf_qa_handoff_x41qO0/`
- Rendering: Poppler, 120 dpi, each page individually viewed at 993 × 1404 px.
- After the final repository rebuild, all 24 pages were rendered again to the
  fresh directory above. Every PNG was byte-identical to its individually
  reviewed counterpart. This verifies that the reviewed pixels correspond to
  the actual delivered build; no stale extra pages were included.

## Individual page review

All entries below refer to physical PDF pages. Printed numbering starts at 1
on physical page 2. Every page was inspected as a full-page image, not solely
as a contact-sheet thumbnail. Captions, headers, margins, text flow and adjacent
page transitions were checked throughout.

| Physical page | Printed page | Specific review |
|---|---|---|
| 1 | Unnumbered | Title, subtitle, footer; intentional cover whitespace |
| 2 | 1 | Contents hierarchy and updated destination page numbers |
| 3 | 2 | Summary and scope heading; symbols and bottom text clearance |
| 4 | 3 | Scope continuation and meteorology; next-page figure placement |
| 5 | 4 | Figure 1 axes/caption, receptor heading and complete Table 1 |
| 6 | 5 | Figure 2 panels, dates, annotations and caption; caveat paragraph |
| 7 | 6 | Table 2 wrapped columns, all rows and following geography paragraph |
| 8 | 7 | Methods, enhancement equation, units and EDGAR conversion equation |
| 9 | 8 | GFED equation, methods subsections and continuation to Results page |
| 10 | 9 | Results heading, substantive opening paragraph and complete Table 3 |
| 11 | 10 | Figure 3 map, boundaries, color scale, receptor and caption |
| 12 | 11 | Figure 4 paired maps, common scale, legends and caption |
| 13 | 12 | Transport subsection, Figure 5 axes and explanatory paragraphs |
| 14 | 13 | Figure 6 seed/height markers and source-sector subsection |
| 15 | 14 | Complete Table 4 and Figure 7 labels, units and caption |
| 16 | 15 | Figure 8 paired inventory maps and gas-specific scales |
| 17 | 16 | Figure 9 source-weighted maps and contribution-density labels |
| 18 | 17 | Province subsection and complete Table 5; no stranded heading |
| 19 | 18 | Figure 10 province labels; fire subsection and CO budget caveat |
| 20 | 19 | Complete Table 6, Figure 11 maps/caption and bottom text clearance |
| 21 | 20 | Figure 12, Discussion heading, budget equation and paragraph split |
| 22 | 21 | Table 7 appears once; caption, column header and all nine rows intact |
| 23 | 22 | Conclusions, all eight references and boundary attribution |
| 24 | 23 | Appendix heading, complete Tables 8 and 9, derivation and final margin |

The figure-only pages retain intentional surrounding whitespace to preserve
map legibility. No duplicated continuation headers, orphaned table captions,
stranded section headings, clipping or label collisions were observed in this
review. This is evidence of the checks performed, not a claim that future
documents cannot contain errors.
