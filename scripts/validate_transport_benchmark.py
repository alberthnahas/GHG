"""Validate benchmark accounting, provenance, comparisons and report evidence."""
from __future__ import annotations
from collections import defaultdict
import json
import math
from pathlib import Path
import re

import numpy as np
import pandas as pd
import xarray as xr

from a64_transport_benchmark import OUT, ROOT, ANCHORS, scenarios
from a37_bkt_footprint import sha256_file
from a39_bkt_refinement import actual_particles
from a65_transport_observations import DATA, RESOURCES
from a69_transport_benchmark_report import build_transport_sections


def validate():
    checks=[]
    def require(ok,label):
        if not ok:raise ValueError(label)
        checks.append(dict(check=label,status='passed'))
    table=OUT/'tables'
    runs=pd.read_csv(table/'benchmark_run_summary.csv')
    require(len(runs)==39,'All 39 full benchmark runs are summarized')
    require(not runs.duplicated(['scenario','time_utc']).any(),'Unique scenario/receptor pairs')
    require((runs[runs.scenario!='loss_control'].retained_percent>=95).all(),
            'All comparative runs pass particle retention; original severe-loss control is retained')
    for name in [*scenarios(),'control_seedm10','control_seedm20']:
        dates=set(runs[runs.scenario==name].time_utc)
        require(dates=={s.isoformat()+'Z' for s in ANCHORS},f'Frozen anchors covered: {name}')
    met_paths=set()
    for marker in sorted((OUT/'runs').glob('*/*/benchmark_complete.json')):
        directory=marker.parent;receipt=json.loads(marker.read_text())
        meta=json.loads((directory/'run_metadata.json').read_text())
        require(meta['configuration']==receipt['configuration'] and meta['transport_options']==receipt['transport_options'],
                f'Configuration receipt matches: {directory.parent.name}/{directory.name}')
        for filename,digest in receipt['output_sha256'].items():
            require(sha256_file(directory/filename)==digest,f'Output checksum {directory.parent.name}/{directory.name}/{filename}')
        met_paths.update(map(Path,meta['meteorology_files']))
        n=actual_particles((directory/'MESSAGE').read_text())
        points=pd.read_csv(directory/'PAR_GIS.txt',skipinitialspace=True);points.columns=points.columns.str.strip()
        for stamp,group in points.groupby('time',sort=False):
            require(len(group)==n and group.NSORT.nunique()==n,
                f'Complete particle ledger {directory.parent.name}/{directory.name}/{stamp}')
        with xr.open_dataset(directory/'footprint.nc') as ds:
            field=ds.footprint_sensitivity
            require(field.sizes['time']==meta['configuration']['hours_back'] and bool(np.isfinite(field).all()) and float(field.min())>=0,
                    f'Finite nonnegative complete footprint {directory.parent.name}/{directory.name}')
            total=float(field.sum())*meta['configuration']['particles']/n
        aggregate=pd.read_csv(directory/'footprint_aggregate.csv')
        independent=math.fsum(aggregate.sensitivity_sum.tolist())*meta['configuration']['particles']/n
        require(math.isclose(total,independent,rel_tol=2.e-6,abs_tol=1.e-12),
                f'Independent CSV/NetCDF normalization {directory.parent.name}/{directory.name}')
    for path in sorted(met_paths):
        provenance=json.loads(path.with_name(path.name+'.json').read_text())
        require(sha256_file(path)==provenance['sha256'],f'Meteorological provenance {path.parent.name}/{path.name}')
    for name in RESOURCES:
        provenance=json.loads((DATA/(name+'.json')).read_text())
        require(sha256_file(DATA/name)==provenance['sha256'],f'Observation-source provenance {name}')
    packing=pd.read_csv(table/'wide_meteorology_audit.csv')
    require(len(packing)==6 and (packing.maximum_difference_over_packing_tolerance<=1.001).all(),
            'Expanded meteorology shares native schema and values within packing precision')
    duration=pd.read_csv(table/'duration_sensitivity.csv')
    dump=pd.read_csv(table/'dump_invariance.csv')
    require(len(duration)==4 and duration.maximum_matched_cell_hour_difference.eq(0).all() and
            dump.maximum_cell_hour_difference.eq(0).all(),'Extra particle diagnostics preserve original footprint values')
    native=pd.read_csv(table/'native_profile_reader_check.csv')
    require(len(native)==275 and native.passed.all(),'Reader matches NOAA profile utility within packing/display precision')
    execution=pd.read_csv(table/'convection_execution.csv')
    require(len(execution)==12 and not execution.supplied_cape.any() and execution.wrf_interpolation_disabled.all(),
            'Convection settings and ignored WRF-specific interpolation are verified from execution')
    domain=pd.read_csv(table/'domain_comparison.csv').set_index('scenario')
    require(domain.loc['loss_wide_output','maximum_shared_cell_hour_difference']<=1.e-7,
            'Output-grid expansion preserves shared cell-hour coefficients')
    for stamp in ANCHORS:
        directory=f'bkt_{stamp:%Y%m%dT%H%MZ}'
        arrays=[]
        for name in ['control','control_seedm10','control_seedm20']:
            with xr.open_dataset(OUT/'runs'/name/directory/'footprint.nc') as ds:
                arrays.append(ds.footprint_sensitivity.values.copy())
        require(all(not np.array_equal(arrays[i],arrays[j]) for i in range(3) for j in range(i)),
                f'Control seed coefficient arrays differ at {stamp}')
    quality=pd.read_csv(table/'igra_quality_counts.csv')
    for (station,variable),group in quality.groupby(['station','variable']):
        require(group.n.sum()==group.denominator.iloc[0] and np.isclose(group.percent.sum(),100),f'IGRA QA accounting {station}/{variable}')
    pairs=pd.read_csv(table/'profile_matches.csv')
    metrics=pd.read_csv(table/'profile_metrics.csv')
    selected=pairs[(pairs.station=='IDM00096163')&(pairs.scenario=='primary')]
    # Separate Python accounting reproduces the equal-level, sounding, day estimator.
    sounds=defaultdict(list)
    for row in selected.itertuples():
        if math.isfinite(row.u_error) and math.isfinite(row.v_error):
            sounds[(row.date_utc,row.time_utc)].append(row.u_error**2+row.v_error**2)
    days=defaultdict(list)
    for (date,_),values in sounds.items():days[date].append(math.fsum(values)/len(values))
    independent=math.sqrt(math.fsum(math.fsum(v)/len(v) for v in days.values())/len(days))
    expected=metrics[(metrics.station=='IDM00096163')&(metrics.scenario=='primary')&(metrics.metric=='vector_rmse')].value.item()
    require(math.isclose(independent,expected,rel_tol=1.e-12),'Independent equal-day wind-vector RMSE arithmetic')
    complete=pairs[(pairs.station=='IDM00096163')&(pairs.scenario=='complete_profiles')]
    require(complete.groupby('time_utc').size().eq(5).all() and complete.temperature_error.notna().all(),
            'Complete-profile sensitivity retains exactly five usable common levels')
    require(metrics[(metrics.station=='IDM00096109')].ci95_low.isna().all(),'Sparse Pekanbaru sample has no unsupported intervals')
    values=build_transport_sections()
    require('{{' not in values['TRANSPORT_APPENDIX'],'Transport report has no unresolved evidence tokens')
    require('not demonstrably assimilation-independent validation' in values['TRANSPORT_APPENDIX'],
            'Independent-validation limitation is explicit')
    require(not re.search(r'/run/media/|scripts/|SHA.256',values['TRANSPORT_APPENDIX']),
            'Transport narrative excludes internal implementation paths')
    require(all((OUT/'figures'/(name+suffix)).exists() for name in
        ['domain_completeness','physics_sensitivity','profile_evaluation'] for suffix in ['.png','.pdf']),
        'Three reproducible raster and vector figures exist')
    pd.DataFrame(checks).to_csv(table/'validation_checks.csv',index=False)
    result=dict(status='passed',checks=len(checks),full_benchmark_runs=len(runs),
                limitation='Numerical/provenance validation; full atmospheric superiority and assimilation independence remain unestablished')
    (OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return result


if __name__=='__main__':validate()
