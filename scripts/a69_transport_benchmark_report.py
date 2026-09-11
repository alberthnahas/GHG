"""Build the integrated transport appendix from completed benchmark evidence."""
from __future__ import annotations
import json
import re
import numpy as np
import pandas as pd
from a64_transport_benchmark import OUT, ROOT, scenarios
from a40_bkt_refinement_report import markdown_table

LABELS={'mix100':'100 m mixing floor','mix50':'50 m mixing floor',
    'mix_native':'Native mixing depth','height60':'60 m receptor',
    'convection_off':'Convection disabled','convection_cape500':'CAPE threshold: 500 J kg⁻¹'}


def build_transport_sections():
    tables=OUT/'tables'
    base=pd.read_csv(tables/'baseline_summary.csv').iloc[0]
    domain=pd.read_csv(tables/'domain_comparison.csv').set_index('scenario')
    runs=pd.read_csv(tables/'benchmark_run_summary.csv')
    contrast=pd.read_csv(tables/'physics_contrasts.csv')
    duration=pd.read_csv(tables/'duration_sensitivity.csv')
    packing=pd.read_csv(tables/'wide_meteorology_audit.csv')
    mixing=pd.read_csv(tables/'mixing_depth_summary.csv').set_index(['method','period'])
    profiles=pd.read_csv(tables/'profile_metrics.csv')
    primary=profiles[(profiles.station=='IDM00096163')&(profiles.scenario=='primary')].set_index('metric')
    seeds=contrast[contrast.scenario.str.startswith('control_seed')]
    for name in LABELS:
        if len(contrast[contrast.scenario==name])!=4:raise ValueError(f'Incomplete comparison {name}')
    if len(seeds)!=8 or len(runs)!=39 or len(packing)!=6:
        raise ValueError('Benchmark run coverage incomplete')
    old=domain.loc['loss_control'];wide=domain.loc['loss_wide_output']
    if wide.retained_percent<95:raise ValueError('Expanded-domain retention still fails screen')
    v={'T_BASE_N':str(int(base.n_runs)),'T_BASE_FAIL':str(int(base.n_fail95)),
       'T_LOSS_ACTIVE':str(int(old.active)),'T_EMITTED':str(int(old.emitted)),
       'T_DURATION_MIN':f'{duration.beyond72h_percent.min():.1f}',
       'T_DURATION_MAX':f'{duration.beyond72h_percent.max():.1f}'}
    v['T_DECISION']=(f'**The expanded domain restores particle completeness in the severe-loss case, '
        'but no mixing, receptor-height or convection configuration is independently validated as superior.** '
        f'Endpoint retention increases from {old.retained_percent:.1f}% to {wide.retained_percent:.1f}%. '
        'The observational check constrains meteorological forcing errors, not the full surface-flux operator.')
    v['T_PACKING_NOTICE']=(f'All {int(packing.n_fields_compared.sum()):,} shared-domain variable–level–time '
        'fields agree within the sum of their two packing increments. Some are not bit-identical because '
        'the larger extraction is repacked; changes in trajectory detail and shared-grid sensitivity '
        'cannot be attributed solely to domain extent.')
    rows=[]
    for case,label in [('loss_control','Original domains'),('loss_wide','Wider meteorology'),
                       ('loss_wide_output','Both domains wider')]:
        r=domain.loc[case]
        rows.append([label,f'{r.retained_percent:.1f}',f'{r.normalized_sensitivity:.3f}',
                     f'{r.outside_original_output_percent:.2f}',f'{r.output_edge_percent:.3f}'])
    v['T_DOMAIN_TABLE']=markdown_table(['Configuration','Active (%)','Sensitivity','Outside old grid (%)','Edge (%)'],rows)
    tail=runs[runs.scenario=='loss_wide_output'].iloc[0].oldest24h_percent
    v['T_DOMAIN_INTERPRETATION']=(f'The wider footprint grid places {wide.outside_original_output_percent:.2f}% '
        f'of its integrated sensitivity outside the original output grid. Its outermost cells contain '
        f'{wide.output_edge_percent:.3f}% of sensitivity, and the closest surviving endpoint is '
        f'{wide.minimum_endpoint_boundary_distance_km:.0f} km from the expanded meteorological boundary. '
        f'The oldest 24 hours still supply {tail:.1f}% of five-day sensitivity. '
        f'On the original output grid, wider meteorology changes integrated sensitivity by '
        f'{wide.shared_grid_change_vs_original_percent:+.1f}%; this is not a pure domain-effect estimate '
        'because the meteorological packing also changes. In contrast, expanding only the output grid '
        'preserves every shared cell-hour coefficient exactly. '
        'This establishes improved numerical coverage for this case, not five-day temporal convergence, '
        'atmospheric accuracy, or completeness of all original receptor runs.')
    rows=[]
    for name,label in LABELS.items():
        g=contrast[contrast.scenario==name]
        rows.append([label,f'{g.sensitivity_ratio.median():.3f}',
            f'{g.sensitivity_ratio.min():.3f}–{g.sensitivity_ratio.max():.3f}',f'{g.relative_l1_percent.median():.1f}'])
    rows.append(['Unchanged-physics seed repeats',f'{seeds.sensitivity_ratio.median():.3f}',
        f'{seeds.sensitivity_ratio.min():.3f}–{seeds.sensitivity_ratio.max():.3f}',f'{seeds.relative_l1_percent.median():.1f}'])
    v['T_PHYSICS_TABLE']=markdown_table(['Contrast','Median ratio','Ratio range','Median spatial difference (%)'],rows)
    floor=contrast[contrast.scenario=='mix100']
    day=floor[floor.hour_wib==13].sensitivity_ratio;night=floor[floor.hour_wib==1].sensitivity_ratio
    v['T_MIXING_INTERPRETATION']=(f'The 100 m floor gives sensitivity ratios of {day.min():.2f}–{day.max():.2f} '
        f'at 13:00 WIB and {night.min():.2f}–{night.max():.2f} at 01:00 WIB across the two cases in each clock period. '
        'The response is not a simple inverse scaling with mixing depth: the floor acts along the entire '
        'backward path, changes vertical dispersion and sampling of winds, and changes residence in the '
        'surface-sensitive layer. A receptor-height contrast likewise tests model representativeness, '
        'not a second observed inlet. Single-seed perturbations and two control-seed repeats characterize '
        'sensitivity only; replicated perturbations would be needed for parameter-specific uncertainty.')
    v['T_MIXING_INTERPRETATION']+=(f' Control-seed ratios span {seeds.sensitivity_ratio.min():.3f}–'
        f'{seeds.sensitivity_ratio.max():.3f}, with a median spatial absolute difference of '
        f'{seeds.relative_l1_percent.median():.1f}%. The spatial differences from native mixing depth '
        'and receptor height are of a similar scale, whereas the larger nighttime floor responses '
        'exceed the observed control-seed variation. This comparison is descriptive, not a significance test.')
    r=mixing.loc[(3,'night_17_07_WIB')]
    v['T_NIGHT_FLOOR']=f'{r.below250_percent:.1f}';v['T_NIGHT_N']=str(int(r.n))
    off=contrast[contrast.scenario=='convection_off'];cape=contrast[contrast.scenario=='convection_cape500']
    if (off.maximum_cell_hour_difference==0).all():
        off_text='Disabling the original requested convection option produces exactly the same cell-hour footprint coefficients at all four receptor times.'
    else:
        off_text=(f'Disabling the requested convection option gives ratios of {off.sensitivity_ratio.min():.3f}–'
            f'{off.sensitivity_ratio.max():.3f}; a response is present despite the missing required flux fields and needs further diagnosis.')
    if (cape.maximum_cell_hour_difference==0).all():
        cape_text='The positive CAPE-threshold experiment also produces no cell-hour response in these cases; this does not establish whether the threshold was reached.'
    else:
        cape_text=(f'The positive CAPE-threshold experiment gives ratios of {cape.sensitivity_ratio.min():.3f}–'
            f'{cape.sensitivity_ratio.max():.3f}, demonstrating a model sensitivity rather than validated convective transport.')
    v['T_CONVECTION_INTERPRETATION']=off_text+' '+cape_text
    rows=[]
    for metric,label in [('u_bias','Eastward-wind bias (m s⁻¹)'),('v_bias','Northward-wind bias (m s⁻¹)'),
                         ('vector_rmse','Wind-vector RMSE (m s⁻¹)'),('temperature_bias','Temperature bias (K)'),
                         ('temperature_rmse','Temperature RMSE (K)')]:
        r=primary.loc[metric]
        rows.append([label,f'{r.value:.2f}',f'{r.ci95_low:.2f}–{r.ci95_high:.2f}',str(int(r.n_soundings))])
    v['T_PROFILE_TABLE']=markdown_table(['Metric','Estimate','95% interval','Soundings'],rows)
    sensitivity=profiles[(profiles.station=='IDM00096163')&(profiles.metric=='vector_rmse')]
    collocation=sensitivity[sensitivity.scenario.isin(['nearest','historical_position','time_minus_1h','time_plus_1h'])]
    complete=sensitivity[sensitivity.scenario=='complete_profiles'].iloc[0]
    v['T_PROFILE_SENSITIVITY']=(f'Nearest-cell, historical-position and one-hour timing alternatives give '
        f'wind-vector RMSE values of {collocation.value.min():.2f}–{collocation.value.max():.2f} m s⁻¹, '
        f'compared with {primary.loc["vector_rmse"].value:.2f} m s⁻¹ for the primary sampling. '
        f'Restricting to {int(complete.n_soundings)} complete five-level wind-and-temperature profiles '
        f'lowers wind-vector RMSE to {complete.value:.2f} m s⁻¹. This coverage sensitivity is larger '
        'than the tested small collocation changes and prevents treating the aggregate as invariant to sampling.')
    influence=pd.read_csv(tables/'profile_influence.csv')
    high=influence[influence.station=='IDM00096163'].nlargest(1,'contribution_to_total_mse_percent').iloc[0]
    stamp=pd.Timestamp(high.time_utc)
    v['T_PROFILE_SENSITIVITY']+=(f' The wind-only profile on {stamp:%-d %B} at {stamp:%H:%M} UTC '
        f'contributes {high.contribution_to_total_mse_percent:.1f}% of the aggregate wind mean-square error. '
        'Its large mismatch persists under the collocation alternatives. It remains in the primary '
        'estimate: missing temperature and model disagreement are not sufficient grounds to reject its winds.')
    peka=profiles[(profiles.station=='IDM00096109')&(profiles.scenario=='primary')&(profiles.metric=='vector_rmse')].iloc[0]
    v['T_PEKA_PAIRS']=str(int(peka.n_level_pairs));v['T_PEKA_DAYS']=str(int(peka.n_days))
    v['T_RECOMMENDATION']=('Prioritize meteorological and footprint-domain completeness before interpreting '
        'five-day flux contributions. Apply the expanded-domain check across the full receptor ensemble before '
        'rebuilding an inversion operator. Keep the existing baseline settings unchanged while carrying '
        'mixing-depth, receptor-height and convection alternatives as explicit model sensitivities. '
        'Do not choose a setting solely because it reduces a gas residual or increases integrated sensitivity.')
    v['TRANSPORT_SUMMARY']=(f'A gas-independent transport benchmark identifies incomplete particle retention in '
        f'{int(base.n_fail95)} of {int(base.n_runs)} original five-day runs. The severe-case expanded-domain '
        f'test raises retention from {old.retained_percent:.1f}% to {wide.retained_percent:.1f}%. '
        'Mixing and receptor tests expose configuration sensitivity; an observation-based profile check '
        'does not independently validate any replacement. The transport appendix separates these findings '
        'from atmospheric accuracy and leaves the inversion unchanged.')
    text=(ROOT/'docs/BKT_Transport_Benchmark_appendix.md').read_text()
    text=re.sub(r'\{\{([A-Z0-9_]+)\}\}',lambda m:v[m[1]],text)
    from a73_domain_budget_report import build_domain_sections
    domain=build_domain_sections()
    v.update(domain)
    v['TRANSPORT_SUMMARY'] += ' ' + domain['DOMAIN_SUMMARY']
    text += '\n\n' + domain['DOMAIN_APPENDIX']
    v['TRANSPORT_APPENDIX']=text
    return v


if __name__=='__main__':
    values=build_transport_sections()
    (OUT/'report_values.json').write_text(json.dumps(values,indent=2)+'\n')
    print('Transport report evidence is complete')
