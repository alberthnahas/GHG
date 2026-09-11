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

## BKT HYSPLIT-STILT footprint mode

The current GFS/source workflow is documented below and in
`docs/BKT_GFS_REPRODUCIBILITY.md`. The following commands rebuild the
**historical GDAS-only analysis** in `outputs/hysplit/refinement/analysis/`;
its report generator would overwrite the current scientific report.

```bash
# Use the shared HDD2 .venv and set HYSPLIT_HOME to the installed model.
python scripts/a39_bkt_refinement.py model --jobs 3
python scripts/a39_bkt_refinement.py analyze
python scripts/a40_bkt_refinement_report.py
python scripts/a14_latex.py BKT_HYSPLIT_STILT_Footprint_Report
python scripts/validate_bkt_footprint_report.py --refinement
```

For the current GFS and emission-source extension, use
[`docs/BKT_GFS_REPRODUCIBILITY.md`](docs/BKT_GFS_REPRODUCIBILITY.md).
Its scientific narrative template is `docs/BKT_GFS_Report_template.md`,
expanded by `scripts/a45_bkt_gfs_report.py`; the report remains canonical
Markdown with matching LaTeX/PDF. Source/transport evidence and figures are in
`outputs/hysplit/gfs/analysis`. Indonesia retains the shared provincial GeoJSON;
neighboring-country maps use detailed geoBoundaries geometry. Scientific
methods and findings stay in the report; development records stay separate.

The integrated methane-inversion extension is documented in
[`docs/BKT_METHANE_INVERSION_REPRODUCIBILITY.md`](docs/BKT_METHANE_INVERSION_REPRODUCIBILITY.md).
Its source operators, sampled posterior, withheld evaluation, synthetic tests
and sensitivity analyses live under `outputs/hysplit/inversion/`. It estimates
conditional regional emission multipliers with explicit natural-source and
background assumptions; the global background assimilates BKT. These results
belong in the same scientific report, not a separate inverse-model report.

The earlier GDAS-only narrative template is `docs/BKT_Footprint_Report_template.md`.
Its generator overwrites `BKT_HYSPLIT_STILT_Footprint_Report.md`; do not run it
over the GFS report unless deliberately rebuilding that historical analysis.
Use `ensemble_mean.nc` for scientific
analysis and flux convolution; `display_surface.nc` is solely a reconstruction
for visualization. Native outputs retain the model's requested-count
normalization. The revised analysis explicitly corrects for the actual emitted
particle count. The original report is archived under `docs/archive/` and
`outputs/hysplit/original_report/`.

The following lower-level commands reproduce the **original pilot**. Do not
run its report-generation commands over the revised report without intending
to revert the narrative to the original analysis.

The BKT workflow calculates a backward surface-flux sensitivity footprint for
an exact hourly greenhouse-gas observation. It uses the harmonised BKT loader,
NOAA GDAS1 meteorology, HYSPLIT-STILT physics, and writes CSV, NetCDF, PNG and
PDF products. It does not by itself estimate emissions or total CO2/CH4.

```bash
python3 scripts/a37_bkt_footprint.py fetch \
  --receptor-utc 2019-09-26T01:00:00 --hours-back 72

python3 scripts/a37_bkt_footprint.py run \
  --receptor-utc 2019-09-26T01:00:00 --hours-back 72 \
  --hysplit-home /path/to/hysplit

python3 scripts/plot_bkt_footprint.py \
  outputs/hysplit/bkt_20190926T0100Z

python3 scripts/validate_bkt_footprint.py \
  outputs/hysplit/bkt_20190926T0100Z

python3 scripts/a38_bkt_footprint_report.py \
  --run-dir outputs/hysplit/bkt_20190926T0100Z

```

See `docs/BKT_HYSPLIT_STILT_FOOTPRINT.md` for the method and output contract,
and `docs/BKT_HYSPLIT_STILT_FOOTPRINT_PLAN.md` for acceptance criteria. The
canonical comprehensive report is `BKT_HYSPLIT_STILT_Footprint_Report.md`; its
publication PDF is generated at
`outputs/BKT_HYSPLIT_STILT_Footprint_Report.pdf`. Supporting report figures,
evidence tables, metrics and validation results are kept under the pilot run's
`report/` directory.
