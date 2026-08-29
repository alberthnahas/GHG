# Indonesian Greenhouse-Gas Analysis

Reproducible analysis of hourly CO2, CH4, and CO observations from five
Indonesian monitoring stations, evaluated with NOAA Global Monitoring
Laboratory flask measurements.

Start with `AGENTS.md` for scientific and implementation constraints and
`summary.md` for the project handoff. The canonical scientific documents are:

- `GHG_Analysis_Report.md`
- `GHG_Analysis_Methods.md`
- `BKT_Tower_Sequencer_Specification.md`

Raw inputs are retained in the repository. Generated tables, caches, figures,
PDFs, HTML files, and slide decks are excluded and rebuilt by the scripts.

## Rebuild and verify

Run the analysis scripts in the order documented in `summary.md`, then execute:

```bash
bash scripts/verify_all.sh
```

The verification command checks document consistency, bilingual figures, PDF
layout, and slide rendering. Numerical values in prose must additionally be
checked against their source CSV tables.
