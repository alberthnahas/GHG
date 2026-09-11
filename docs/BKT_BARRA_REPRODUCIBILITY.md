# Reproduce the bounded BARRA-R2 conversion screen

This is an internal execution record. The scientific result is integrated into
`BKT_HYSPLIT_STILT_Footprint_Report.md` and its generated PDF. It is an audit of
public input feasibility, not a completed BARRA transport comparison.

## Environment

Use the existing scientific environment, with numpy, pandas, requests and
netCDF4. No dependencies were installed or changed. The host command below
uses the established scientific Python; substitute an equivalent environment
on another host. No credentials or new WRF simulation are required.

```bash
BKT_PYTHON=/run/media/workstation-llm/HDD2/.venv/bin/python
"$BKT_PYTHON" scripts/a52_bkt_barra_audit.py wa925
"$BKT_PYTHON" scripts/a52_bkt_barra_audit.py wa850
"$BKT_PYTHON" scripts/a52_bkt_barra_audit.py ps
"$BKT_PYTHON" scripts/a52_bkt_barra_audit.py ta50m
"$BKT_PYTHON" scripts/a52_bkt_barra_audit.py orog --frequency fx
"$BKT_PYTHON" scripts/a53_bkt_barra_subset.py ps wa925 wa850 ta925 zg925
"$BKT_PYTHON" scripts/a53_bkt_barra_subset.py ua925 va925 hus925 ua850 va850 hus850 ta850 zg850
"$BKT_PYTHON" scripts/a53_bkt_barra_subset.py ta50m ta100m ta150m ta200m ta250m ta1500m
"$BKT_PYTHON" scripts/a53_bkt_barra_subset.py orog --frequency fx
"$BKT_PYTHON" scripts/a54_bkt_barra_quality.py
"$BKT_PYTHON" scripts/a54_bkt_barra_quality.py --verify-native
"$BKT_PYTHON" scripts/a45_bkt_gfs_report.py
"$BKT_PYTHON" scripts/validate_bkt_barra.py
"$BKT_PYTHON" -m unittest tests.test_bkt_barra_audit
"$BKT_PYTHON" scripts/a14_latex.py BKT_HYSPLIT_STILT_Footprint_Report
```

The subset defaults are 9 September 2019 00:00–12:00 UTC inclusive, requested
95–105 E and 5 S–5 N, native hourly sampling. NCI returns nearest grid bounds;
the actual bounds, coordinate orientation and decoded times are checked and
stored. Split any later request at month boundaries. Start with bounded reads;
do not infer permission for full-domain or multi-decade downloads.

## Source identity and preservation

The S3 listing supplies exact object keys, versions, sizes and advertised ETags.
Actual samples come from the corresponding NCI OPeNDAP or NCSS path. An S3 ETag
is an advertised S3 object identifier, not a verified checksum of the NCI file.
The subset checksum applies only to the locally downloaded subset. Request URLs
and source keys remain attached to every subset. Existing subsets are reused
only when request identity and local SHA-256 match; they are not silently
overwritten. Raw station observations and prior model results are untouched.

HTTP-range access to compressed S3 chunks was tested but was slow for the first
small field sample. The final implementation uses NCI server-side subsetting.
Only roughly 4.5 MiB of subsets and receipts were retained, not whole monthly
meteorological fields. Supplemental metadata records are stored separately.

## Validation and limits

NCSS returns decoded floating-point NaNs without necessarily retaining a
`_FillValue` attribute. Both nonfinite values and explicit masks must therefore
be treated as missing. Specific humidity is dimensionless (`1`, mass fraction);
surface pressure is Pa and is explicitly divided by 100 for pressure-level
comparisons. Vertical velocity has CF standard name `upward_air_velocity` and
units `m s-1`; no pressure-velocity sign conversion was applied.

`field_quality.csv` preserves per-variable counts at four pressure margins.
`scope.csv`, `bkt_profile.csv`, `aboveground_missing_examples.csv`,
`native_confirmation.csv` and `subset_provenance.csv` preserve context and
traceability. Native confirmation reads original packed fill codes and applies
the native surface-pressure scale and offset independently of the subset.
The validator recomputes gap counts and denominators directly from the subsets,
checks hashes, sign conventions, report integration and the conversion-stop
evidence. A passing audit has `meteorology_conversion_ready: false`.

This bounded sample cannot establish monthly missingness rates, meteorological
skill or emission accuracy. No ARL packing, boundary transfer, particle-retention
comparison or revised inversion has been performed. See the execution plan for
the explicit dependency before those steps can resume.

For all existing report gates on this host:

```bash
env PATH=/tmp/ghg-python-bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  PYTHONPATH=/tmp/ghg-verify-deps XDG_CACHE_HOME=/tmp/ghg-tectonic-cache \
  GHG_SCIENTIFIC_PYTHON=/run/media/workstation-llm/HDD2/.venv/bin/python \
  bash scripts/verify_all.sh
```

These `/tmp` dependency shims are host-specific, inherited from the existing
report workflow; recreate an equivalent environment if absent. A successful
report gate does not override the failed meteorology-readiness criterion.
