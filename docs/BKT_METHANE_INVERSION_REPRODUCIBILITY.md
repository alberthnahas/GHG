# Reproduce the BKT methane inversion

This extends the existing GFS source-influence report. The scientific contract
and pre-fit choices are in `BKT_METHANE_INVERSION_PLAN.md`. Raw observations
remain immutable and are loaded only through `ghg_common.load_station` and
its quality flags. No publication or data upload is part of this workflow.

## Environment and inputs

Run from the project root. Use the shared scientific Python environment:

```bash
export BKT_PYTHON=/run/media/workstation-llm/HDD2/.venv/bin/python
```

The workflow uses the existing HYSPLIT 5.4.2 installation next to this project,
including `hycs_std`, `con2asc`, and `par2asc`. Inspect the actual configuration
and software manifest before transferring this workflow to another machine.
The paths are centralized in the transport and source modules, not credentials.

Acquire GFS and global background independently; each command is resumable from
its verified metadata. Do not run duplicate acquisition stages concurrently.

```bash
"$BKT_PYTHON" scripts/a46_bkt_inversion_transport.py fetch
"$BKT_PYTHON" scripts/a47_bkt_inversion_inputs.py all
"$BKT_PYTHON" scripts/a47_bkt_inversion_inputs.py auxiliary
```

EDGAR v8.0 monthly 2019 methane sectors are reused from the existing source
workflow (`BKT_GFS_REPRODUCIBILITY.md`). The inversion adds daily GFED methane
for 2 September–6 October and corresponding monthly cropland partitions.
The following commands use the provider's public read-only access information
in memory and the pinned SSH host key; never print or save the access values.
System Python supplies the existing Paramiko installation for these transfers.

```bash
/usr/bin/python3 scripts/bkt_gfed_transfer.py \
  GFED5/GFED5.1/Daily/GFED5.1_daily_2019-09.nc --fast --subset \
  --day-start 2 --day-end 30 --bounds 75 -19 126 19 --gases CH4 \
  --output data/bkt_sources/gfed51/GFED51_20190902_30_inversion.npz
/usr/bin/python3 scripts/bkt_gfed_transfer.py \
  GFED5/GFED5.1/Daily/GFED5.1_daily_2019-10.nc --fast --subset \
  --day-start 1 --day-end 6 --bounds 75 -19 126 19 --gases CH4 \
  --output data/bkt_sources/gfed51/GFED51_20191001_06_inversion.npz
/usr/bin/python3 scripts/bkt_gfed_transfer.py \
  GFED5/GFED5.1/Monthly/GFED5.1_monthly_2019.nc --fast --subset \
  --day-start 9 --day-end 10 --bounds 75 -19 126 19 --gases CH4 \
  --output data/bkt_sources/gfed51/GFED51_201909_10_monthly_inversion.npz
/usr/bin/python3 scripts/bkt_gfed_transfer.py \
  GFED5/GFED5.1/Ecosystem/GFED5.1_ecosystem_2019.nc --fast \
  --output data/bkt_sources/gfed51/GFED5.1_ecosystem_2019.nc
/usr/bin/python3 scripts/bkt_gfed_transfer.py \
  GFED5/Ancillary/Emission_factors/GFED5_emission_factors.txt --fast \
  --output data/bkt_sources/gfed51/GFED5_emission_factors.txt
```

For a monthly file, `--day-start`/`--day-end` select the 1-based monthly
interval indices (9 and 10); they do not select September calendar days.
The source file's time coordinate and units are retained in provenance.
Existing verified GFED subsets need not be downloaded again.

Indonesian maps use the established shared 38-province GeoJSON. Foreign
boundaries are full-resolution geoBoundaries gbOpen, with each country's
license recorded beside its source file. The inversion map country set adds
India, Bangladesh, Sri Lanka, Timor-Leste and Australia to the original eight
countries. Use `a42_bkt_sources.boundaries(countries=...)` to acquire missing
polygons, and preserve the Indonesian asset independently.

## Transport and source operator

```bash
"$BKT_PYTHON" scripts/a46_bkt_inversion_transport.py run
"$BKT_PYTHON" scripts/a46_bkt_inversion_transport.py sensitivities
"$BKT_PYTHON" scripts/a48_bkt_inversion_operator.py prepare
"$BKT_PYTHON" scripts/a48_bkt_inversion_operator.py fire
"$BKT_PYTHON" scripts/a48_bkt_inversion_operator.py observations
"$BKT_PYTHON" scripts/a48_bkt_inversion_operator.py natural-audit
"$BKT_PYTHON" scripts/a48_bkt_inversion_operator.py responses
```

The base and sensitivity scheduler may run concurrently (four plus two model
workers). An optional `accelerate` transport stage adds at most four workers
in separate directories; completed identical runs are linked atomically into
the base tree if not already started there. If both pools reach a receptor,
neither overwrites the other's active files. Do not increase concurrency on a
shared host without checking available CPU and memory.

Generate each sensitivity operator after all its runs complete:

```bash
for BKT_GROUP in seed_m10 height60 n2000 window72 window168; do
  "$BKT_PYTHON" scripts/a48_bkt_inversion_operator.py responses --group "$BKT_GROUP"
done
```

Inactive endpoint placeholders have `PGRD=0`; exclude them before geographic
interpolation. Retention is active endpoints divided by actual emitted
particles. The 95% retention screen is independent of concentration residuals.
No incomplete response matrix may enter inference. `--allow-partial` is only
for intermediate operator diagnostics, not fitting or final reporting.

## Inference and integrated report

```bash
"$BKT_PYTHON" scripts/a49_bkt_methane_inversion.py fit
"$BKT_PYTHON" scripts/a49_bkt_methane_inversion.py robustness
"$BKT_PYTHON" scripts/a49_bkt_methane_inversion.py synthetic
"$BKT_PYTHON" scripts/a49_bkt_methane_inversion.py budget
"$BKT_PYTHON" scripts/a49_bkt_methane_inversion.py transport
"$BKT_PYTHON" scripts/a50_bkt_inversion_figures.py all
"$BKT_PYTHON" scripts/a45_bkt_gfs_report.py
"$BKT_PYTHON" scripts/a14_latex.py BKT_HYSPLIT_STILT_Footprint_Report
"$BKT_PYTHON" scripts/validate_bkt_inversion.py
"$BKT_PYTHON" scripts/validate_bkt_gfs_report.py
```

The integrated narrative is generated from the existing GFS template and
`BKT_Inversion_Report_sections.md`; calculated values come from CSV tables.
Do not hand-edit generated PDF, LaTeX, figure or table products. Source changes
must be followed by the corresponding derivation, report build and QA.

Main derived evidence is under `outputs/hysplit/inversion/`: receptor selection,
normalized source operators, active endpoints, posterior chains, synthetic
trials, sensitivity cases, conditional mass totals, figure PNG/PDF pairs, and
validation tables. Posterior emission quantiles are conditional on a fixed
source pattern; sector allocations are not independently retrieved sectors.
The CT-CH4 boundary assimilates BKT and cannot supply an independence claim.

## Required validation and handoff

Run the focused numerical tests and all repository gates using the configured
scientific environment. The existing shared-environment workaround for PDF
and deck dependencies on this host supplies PyMuPDF through
`PYTHONPATH=/tmp/ghg-verify-deps` and the project Python launcher through
`/tmp/ghg-python-bin`. These are host-local dependency shims, not scientific
inputs; another host should provide the equivalent packages directly.

```bash
"$BKT_PYTHON" -m unittest tests.test_bkt_footprint tests.test_bkt_refinement \
  tests.test_bkt_gfs_sources tests.test_pdf_layout \
  tests.test_bkt_methane_inverse tests.test_bkt_inversion_operator
bash scripts/verify_all.sh
```

On this host the complete gate command is:

```bash
env PATH=/tmp/ghg-python-bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  PYTHONPATH=/tmp/ghg-verify-deps XDG_CACHE_HOME=/tmp/ghg-tectonic-cache \
  GHG_SCIENTIFIC_PYTHON="$BKT_PYTHON" bash scripts/verify_all.sh
```

The focused test command above also needs `PYTHONPATH=/tmp/ghg-verify-deps`
on this host because the PDF-layout tests import PyMuPDF. A missing dependency
is a failed execution, not a successful test result.

Finally render the exact final PDF into a fresh directory, inspect every page
at readable scale (not only thumbnails), check table/figure/text agreement and
page transitions, and record the reviewed page coverage plus PDF checksum.
Any subsequent change invalidates the affected visual review and may change
all later pagination. Machine checks do not substitute for that final review.
