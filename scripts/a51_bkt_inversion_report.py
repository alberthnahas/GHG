"""Expand integrated methane narrative from calculated, inspectable evidence CSVs."""
from __future__ import annotations
import json
import re
import numpy as np
import pandas as pd
from a46_bkt_inversion_transport import OUT
from a40_bkt_refinement_report import markdown_table

ROOT=OUT.parents[2]
TABLES=OUT/"tables"
LABELS={"anthro_near":"Anthropogenic ≤500 km","anthro_far":"Anthropogenic >500 km",
        "wetlands":"Wetlands","fire":"Non-crop fires","background_offset":"Background offset",
        "background_trend":"Background trend"}


def span(series,digits=1,signed=False):
    series=pd.Series(series).dropna()
    if series.empty:return "Not evaluable"
    spec=f"{'+' if signed else ''}.{digits}f"
    return f"{min(series):{spec}} to {max(series):{spec}}"


def build_inversion_sections():
    read=lambda name,**kwargs:pd.read_csv(TABLES/f"{name}.csv",**kwargs)
    p=read("posterior_parameters").set_index("parameter")
    d=read("inversion_predictions",parse_dates=["time_utc"])
    operator=read("operator_base",parse_dates=["time_utc"])
    summary=read("inversion_summary").iloc[0]
    quality=read("inversion_observation_quality").iloc[0]
    flask=read("inversion_flask_summary").set_index("scope").loc["study_period"]
    evaluation=read("inversion_evaluation").set_index(["split","model"])
    sens=read("inversion_sensitivity")
    recovery=read("synthetic_recovery_summary")
    weeks=read("week_block_evaluation")
    transport=read("transport_sensitivity_comparison")
    budget=read("conditional_emission_budget")
    sectors=read("conditional_sector_emissions")
    ef=read("fire_overlap_assumptions").iloc[0]
    display=read("inversion_display_integrity").iloc[0]
    corr=read("source_response_correlation",index_col=0).values
    postcorr=read("posterior_parameter_correlation",index_col=0)
    pair_indices=np.triu_indices(len(postcorr),1)
    pair=int(np.argmax(np.abs(postcorr.values[pair_indices])))
    post_i,post_j=pair_indices[0][pair],pair_indices[1][pair]
    endpoints=pd.read_csv(OUT/"endpoints_base.csv.gz")
    interval=lambda row:f"{row['median']:.2f} ({row.q025:.2f}–{row.q975:.2f})"
    rmse=float(evaluation.loc[("heldout","posterior"),"rmse_ppb"])
    adj=float(evaluation.loc[("heldout","background_adjusted_inventory"),"rmse_ppb"])
    bg_rmse=float(evaluation.loc[("heldout","background_only"),"rmse_ppb"])
    skill=("Emission fitting improves the withheld point-prediction RMSE relative to the adjusted-inventory baseline, "
           "but this finite conditional comparison does not establish independently validated emissions."
           if rmse<adj else "Emission fitting does not improve withheld RMSE over the adjusted-inventory baseline; "
           "the experiment therefore does not demonstrate added predictive skill from emission adjustment.")
    if rmse>=bg_rmse:
        skill+=f" The simpler fitted background-only model performs better ({bg_rmse:.1f} ppb RMSE); source fitting therefore does not demonstrate incremental predictive value over that baseline."
    interpretations=[]
    for name in list(LABELS)[:4]:
        row=p.loc[name]
        relation="lies below unity" if row.q975<1 else "lies above unity" if row.q025>1 else "includes unity"
        interpretations.append(f"The 95% interval for {LABELS[name].lower()} {relation}.")
    weekpivot=weeks.pivot(index="heldout_week",columns="model",values="rmse_ppb")
    matched=recovery[recovery.scenario.eq("matched_operator")]
    perturbed=recovery[~recovery.scenario.eq("matched_operator")]
    v={"IFIG":"outputs/hysplit/inversion/figures",
       "I_N":str(len(d)),"I_TRAIN":str(int(summary.training_hours)),"I_TEST":str(int(summary.heldout_hours)),
       "I_NEAR":interval(p.loc["anthro_near"]),"I_FAR":interval(p.loc["anthro_far"]),
       "I_RMSE":f"{rmse:.1f}","I_ADJ_RMSE":f"{adj:.1f}","I_SKILL_SENTENCE":skill,
       "I_VALID":str(int(quality.valid_ch4)),"I_EXPECTED":str(int(quality.expected_hours)),
       "I_VALID_PERCENT":f"{100*quality.valid_ch4/quality.expected_hours:.1f}",
       "I_MISSING_RECEPTORS":str(int(quality.scheduled_receptors-quality.retained_receptors)),
       "I_EXCLUDED_PERCENT":f"{100*summary.excluded_transport/quality.retained_receptors:.1f}",
       "I_SCHEDULED":str(int(quality.scheduled_receptors)),"I_OBS_N":str(int(quality.retained_receptors)),"I_FLASK_N":str(int(flask.n)),
       "I_FLASK_MIN":f"{flask.minimum_ppb:+.2f}","I_FLASK_MAX":f"{flask.maximum_ppb:+.2f}",
       "I_FLASK_MEAN":f"{flask.flask_minus_insitu_mean_ppb:+.2f}",
       "I_FLASK_ABSMAX":f"{max(abs(flask.minimum_ppb),abs(flask.maximum_ppb)):.2f}",
       "I_FIRE_EF":f"{ef.agriculture_ch4_g_per_kg_dm:.3f}","I_C_EF":f"{1000*ef.agriculture_carbon_fraction:.1f}",
       "I_PARTICLES":str(int(d.emitted_particles.mode().iloc[0])),"I_EXCLUDED":str(int(summary.excluded_transport)),
       "I_BG_MIN":f"{d.background_ppb.min():.1f}","I_BG_MAX":f"{d.background_ppb.max():.1f}",
       "I_INFO":f"{summary.effective_information_modes:.2f}",
       "I_DISPLAY_HIDDEN":f"{display.below_scale_percent:.2f}","I_DISPLAY_OUTSIDE":f"{display.outside_frame_percent:.1f}",
       "I_CORR":f"{np.max(np.abs(corr[np.triu_indices(4,1)])):.2f}",
       "I_POST_CORR":f"{postcorr.iloc[post_i,post_j]:+.2f}",
       "I_POST_CORR_PAIR":f"{LABELS[postcorr.index[post_i]].lower()} and {LABELS[postcorr.index[post_j]].lower()}",
       "I_PARAMETER_INTERPRETATION":" ".join(interpretations),
       "I_RHAT":f"{summary.maximum_rhat:.3f}","I_ESS":f"{summary.minimum_ess:,.0f}",
       "I_COVERAGE":f"{summary.heldout_predictive_coverage_percent:.1f}",
       "I_ENVELOPE_WIDTH":f"{(d.loc[d.holdout,'predictive_q975_ppb']-d.loc[d.holdout,'predictive_q025_ppb']).median():.1f}",
       "I_PARAMETER_WIDTH":f"{(d.loc[d.holdout,'posterior_q975_ppb']-d.loc[d.holdout,'posterior_q025_ppb']).median():.1f}",
       "I_PBL_NEGATIVE":str(int(d.PBLH.lt(0).sum())),
       "I_RES_MIN":f"{d.posterior_residual_ppb.min():+.1f}","I_RES_MAX":f"{d.posterior_residual_ppb.max():+.1f}",
       "I_WEEK_RANGE":span(weekpivot.posterior),
       "I_WEEK_WINS":str(int((weekpivot.posterior<weekpivot.background_adjusted_inventory).sum())),
       "I_WEEK_COUNTS":", ".join(str(int(n)) for n in weeks[weeks.model.eq("posterior")].sort_values("heldout_week").n),
       "I_WEEK_BG_WINS":str(int((weekpivot.posterior<weekpivot.background_only).sum())),
       "I_RETENTION":span(100*operator.endpoint_survival_fraction),
       "I_BELOW":f"{100*endpoints.below_lowest_midlevel.mean():.2f}",
       "I_HEIGHT_BG":f"{max((d.background_height_minus500_ppb-d.background_ppb).abs().max(),(d.background_height_plus500_ppb-d.background_ppb).abs().max()):.1f}",
       "I_OLDEST":span(d.oldest24h_sensitivity_percent),"I_EDGE_MAX":f"{d.edge_sensitivity_percent.max():.3f}",
       "I_RECOVERY_SENTENCE":f"Across components, matched-operator local-interval coverage ranges from {span(matched.local_interval_coverage_percent)}%, "
           f"compared with {span(perturbed.local_interval_coverage_percent)}% under the perturbed scenario. "
           "Shrinkage toward prior values and imperfect recovery must be considered when interpreting source-specific estimates.",
       "I_DISCUSSION_RESULT":" ".join(interpretations)+" "+skill}
    for key,col in (("NEAR","anthro_near"),("FAR","anthro_far"),("WET","wetlands"),("FIRE","fire")):
        v[f"I_K_{key}"]=f"{d[col+'_ppb'].median():.1f}"
    for key,split,model,metric in (("PRIOR_BIAS","all","inventory","bias_ppb"),("PRIOR_RMSE","all","inventory","rmse_ppb"),
        ("RAW_TEST_RMSE","heldout","inventory","rmse_ppb"),("BG_RMSE","heldout","background_only","rmse_ppb")):
        v["I_"+key]=f"{evaluation.loc[(split,model),metric]:.1f}"
    for key,hour in (("DAY",6),("NIGHT",18)):
        v[f"I_{key}_RMSE"]=f"{np.sqrt(np.mean(d.loc[d.time_utc.dt.hour.eq(hour),'posterior_residual_ppb']**2)):.1f}"
    for key,name in (("NEAR","anthro_near"),("FAR","anthro_far")):
        v[f"I_{key}_SENS"]=span(sens.loc[sens.parameter.eq(name)&~sens.case.eq("base"),"map"],2)
    v["I_PARAMETER_TABLE"]=markdown_table(["Parameter","Prior median","Posterior median (95%)","Variance reduction (%)"],
        [[LABELS[name],f"{r.prior_median:.1f}",interval(r),f"{r.prior_to_posterior_log_variance_reduction_percent:.1f}"] for name,r in p.iterrows()])
    models={"inventory":"Raw inventory","background_only":"Background only","background_adjusted_inventory":"Adjusted inventory","posterior":"Inversion"}
    rows=[]
    for split in ("training","heldout"):
        for model,label in models.items():
            r=evaluation.loc[(split,model)]
            rows.append(["Fit" if split=="training" else "Withheld",str(int(r.n)),label,f"{r.bias_ppb:+.1f}",f"{r.mae_ppb:.1f}",f"{r.rmse_ppb:.1f}",f"{r.correlation:.2f}",f"{r.r2:.2f}"])
    v["I_EVALUATION_TABLE"]=markdown_table(["Split","n","Model","Bias","MAE","RMSE","r","R²"],rows)
    names={"seed_m10":"Alternate seed","height60":"60 m release","n2000":"2,000 requested particles","window72":"72 h window","window168":"168 h window"}
    v["I_TRANSPORT_TABLE"]=markdown_table(["Test (anchors)","Sensitivity change (%)","Source change (%)","Background change (ppb)","Retention (%)"],
        [[f"{names[group]} ({len(s)})",span(s.sensitivity_change_percent,1,True),span(s.source_increment_change_percent,1,True),span(s.background_change_ppb,1,True),span(s.endpoint_retention_percent)] for group,s in transport.groupby("group",sort=False)])
    v["I_RECOVERY_TABLE"]=markdown_table(["Scenario / component","Bias","RMSE","Coverage (%)"],
        [[("Matched" if r.scenario=="matched_operator" else "Perturbed")+" / "+LABELS[r.parameter],f"{r.bias:+.2f}",f"{r.rmse:.2f}",f"{r.local_interval_coverage_percent:.1f}"] for r in recovery.itertuples()])
    v["I_BUDGET_TABLE"]=markdown_table(["Region / component","Prior (Gg)","Posterior median (95%) (Gg)","Prior in support (%)"],
        [[("≤500 km" if r.region=="within_500km" else ">500 km")+" / "+r.component.replace("_"," "),f"{r.prior_Gg:,.1f}",f"{r.posterior_median_Gg:,.1f} ({r.posterior_q025_Gg:,.1f}–{r.posterior_q975_Gg:,.1f})",f"{r.support_prior_share_percent:.1f}"] for r in budget.itertuples()])
    v["I_FAR_MASS_SUPPORT"]=f"{budget.loc[budget.region.eq('beyond_500km_in_domain')&budget.component.eq('anthropogenic'),'support_prior_share_percent'].iloc[0]:.1f}"
    near_sectors=sectors[sectors.region.eq("within_500km")].sort_values("prior_Gg",ascending=False)
    sector_labels={"AGRICULTURE":"Agriculture","WASTE":"Waste","FUEL_EXPLOITATION":"Fuel exploitation",
        "BUILDINGS":"Buildings","IND_COMBUSTION":"Industrial combustion","IND_PROCESSES":"Industrial processes",
        "POWER_INDUSTRY":"Power industry","TRANSPORT":"Transport"}
    v["I_SECTOR_TABLE"]=markdown_table(["Sector ≤500 km","Prior (Gg)","Prior share (%)","Conditional posterior (Gg)"],
        [[sector_labels[r.sector.removeprefix("CH4_")],f"{r.prior_Gg:.2f}",f"{100*r.prior_Gg/near_sectors.prior_Gg.sum():.1f}",
          f"{r.posterior_median_Gg:.2f} ({r.posterior_q025_Gg:.2f}–{r.posterior_q975_Gg:.2f})"] for r in near_sectors.itertuples()])
    v["I_LEADING_SECTORS"]=" and ".join(sector_labels[s.removeprefix("CH4_")].lower() for s in near_sectors.sector.iloc[:2])
    v["I_LEADING_SECTOR_SHARE"]=f"{100*near_sectors.prior_Gg.iloc[:2].sum()/near_sectors.prior_Gg.sum():.1f}"
    worked=read("worked_inverse_budget",parse_dates=["time_utc"])
    v["I_WORKED_DATE"]=worked.time_utc.iloc[0].strftime("%d %B %Y at %H:%M UTC")
    v["I_WORKED_INVERSE_TABLE"]=markdown_table(["Budget term","CH₄ (ppb)"],
        [[LABELS.get(r.term,r.term),f"{r.value_ppb:,.2f}"] for r in worked.itertuples()])
    # License text is added explicitly after inspection of provider metadata.
    v["I_BOUNDARY_ATTRIBUTION"]=(ROOT/"docs/BKT_Inversion_boundary_attribution.md").read_text().strip()
    template=(ROOT/"docs/BKT_Inversion_Report_sections.md").read_text()
    required=set(re.findall(r"\{\{([A-Z0-9_]+)\}\}",template))
    if required-v.keys():raise ValueError(f"Missing inversion report tokens: {required-v.keys()}")
    text=re.sub(r"\{\{([A-Z0-9_]+)\}\}",lambda m:v[m[1]],template)
    parts=re.split(r"<!-- SECTION: ([A-Z_]+) -->\s*",text)
    sections={parts[i]:parts[i+1].strip() for i in range(1,len(parts),2)}
    (OUT/"inversion_report_values.json").write_text(json.dumps(v,indent=2)+"\n")
    return sections
