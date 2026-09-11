#!/usr/bin/env python3
"""Build the domain-correction appendix only from validated CSV evidence."""
from __future__ import annotations
import re
import numpy as np
import pandas as pd
from a40_bkt_refinement_report import markdown_table
from a71_domain_budget_extension import OUT, ROOT, TABLES


METRIC_LABELS={
    "sensitivity":"Integrated sensitivity [ppm / (µmol m⁻² s⁻¹)]",
    "net_surface_ppb":"Net prior surface CH₄ (ppb)",
    "background_ppb":"Endpoint background CH₄ (ppb)",
    "total_prior_ppb":"Combined prior CH₄ (ppb)",
}


def interval_text(row: pd.Series, low: str="ci025", high: str="ci975", digits: int=2) -> str:
    return f"{row[low]:.{digits}f} to {row[high]:.{digits}f}"


def direction(value: float, low: float, high: float, unit: str) -> str:
    relation="higher" if value>0 else "lower" if value<0 else "unchanged"
    support="interval excludes zero" if low>0 or high<0 else "interval includes zero"
    return f"{abs(value):.2f} {unit} {relation} ({support})"


def build_domain_sections() -> dict[str,str]:
    full=pd.read_csv(TABLES/"full_receptor_budget.csv",parse_dates=["time_utc"])
    decomp=pd.read_csv(TABLES/"full_domain_decomposition.csv").set_index("metric")
    observed=pd.read_csv(TABLES/"observed_sample_difference.csv").set_index("species")
    strata=pd.read_csv(TABLES/"selection_strata.csv")
    convergence=pd.read_csv(TABLES/"convergence_matrix.csv",parse_dates=["time_utc"])
    changes=pd.read_csv(TABLES/"convergence_changes.csv",parse_dates=["time_utc"])
    if len(full)!=52 or len(decomp)!=4 or len(observed)!=3 or len(convergence)!=30:
        raise ValueError("Domain-budget report evidence is incomplete")
    original_pass=int(full.original_retained.sum());wide_pass=int(full.wide_retention_fraction.ge(.95).sum())
    wide_median=100*full.wide_retention_fraction.median()
    surface=decomp.loc["net_surface_ppb"]
    baseline_surface=full.loc[full.original_retained,"narrow_net_surface_ppb"].mean()
    if np.isfinite(baseline_surface) and abs(baseline_surface)>1e-6:
        relative_text=f" ({100*surface.same_hour_change/baseline_surface:+.1f}% relative to the original retained-hour mean)"
    else:
        relative_text=" (a relative percentage is undefined because the signed baseline mean is near zero)"
    decision=(f"**The widened configuration raises the number of transport-complete receptor hours from "
        f"{original_pass} to {wide_pass} of 52, with median wide-domain particle retention of {wide_median:.1f}%.** "
        f"For the {original_pass} matched hours, the mean net prior surface-methane contribution changes by "
        f"{surface.same_hour_change:+.2f} ppb{relative_text}. "
        "This corrects numerical coverage but does not establish atmospheric accuracy or justify refitting the inversion.")
    rows=[]
    for metric,row in decomp.iterrows():
        digits=3 if metric=="sensitivity" else 2
        rows.append([METRIC_LABELS[metric],
            f"{row.same_hour_change:+.{digits}f} ({row.same_hour_ci025:.{digits}f} to {row.same_hour_ci975:.{digits}f})",
            f"{row.recovered_hour_composition_change:+.{digits}f} ({row.recovered_ci025:.{digits}f} to {row.recovered_ci975:.{digits}f})",
            f"{row.total_change:+.{digits}f} ({row.total_ci025:.{digits}f} to {row.total_ci975:.{digits}f})"])
    decomposition_table=markdown_table(["Metric","Same-hour change (95% interval)",
        "Recovered-hour composition (95% interval)","Total change (95% interval)"],rows)
    gas_labels={"co2":("CO₂","ppm"),"ch4":("CH₄","ppb"),"co":("CO","ppb")}
    rows=[];sentences=[]
    for gas,(label,unit) in gas_labels.items():
        row=observed.loc[gas]
        rows.append([f"{label} ({unit})",f"{row.retained_mean:.2f}",f"{row.recovered_mean:.2f}",
            f"{row.recovered_minus_retained:+.2f}",interval_text(row)])
        sentences.append(f"{label} is {direction(row.recovered_minus_retained,row.ci025,row.ci975,unit)} in recovered hours")
    selection_interpretation=("Relative to originally retained hours, "+", ".join(sentences[:-1])+", and "+sentences[-1]+". "
        "These block-resampled contrasts quantify which observations the original transport screen omitted; they do not attribute the gas differences to transport or any source.")
    observed_table=markdown_table(["Observed gas","Retained mean","Recovered mean","Recovered minus retained","95% interval"],rows)
    def stratum(dimension: str, label: str) -> pd.Series:
        matches=strata[strata.dimension.eq(dimension)&strata.stratum.eq(label)]
        if len(matches)!=1: raise ValueError(f"Missing selection stratum: {dimension}/{label}")
        return matches.iloc[0]
    day=stratum("wib_clock","day_07_17");night=stratum("wib_clock","night_18_06")
    sep=stratum("wib_month","2019-09");october=stratum("wib_month","2019-10")
    east=stratum("zonal_regime","eastward");west=stratum("zonal_regime","westward")
    def count_rate(row: pd.Series) -> str:
        return f"{int(row.n_original_retained)}/{int(row.n_all)} ({row.original_retained_percent:.1f}%)"
    strata_interpretation=(f"Original retention was {count_rate(day)} for 07:00–17:59 WIB and "
        f"{count_rate(night)} for 18:00–06:59 WIB; {count_rate(sep)} in September and "
        f"{count_rate(october)} during 1–6 October; and {count_rate(east)} under eastward versus "
        f"{count_rate(west)} under westward modeled 10 m flow. The pronounced calendar imbalance means "
        "that the recovered-minus-retained gas contrasts are temporally confounded; the block intervals "
        "describe sampling variability but do not adjust for temporal evolution.")
    summary=[];phrases=[]
    for domain,label in [("original","Original"),("wide","Widened")]:
        domain_changes=changes.copy()
        for metric,component in [("net_surface_ppb","surface"),("background_ppb","background"),("total_prior_ppb","combined")]:
            keyed=domain_changes[domain_changes.metric.eq(metric)].pivot(index="time_utc",columns="comparison",values=f"{domain}_duration_change").abs()
            if keyed[["72_to_120h","120_to_168h"]].isna().any().any() or len(keyed)!=5:
                raise ValueError(f"Incomplete keyed convergence changes: {domain}/{metric}")
            a=keyed["72_to_120h"];b=keyed["120_to_168h"]
            smaller=int((b<a).sum())
            summary.append([label,component.capitalize(),f"{a.median():.2f} ({a.min():.2f}–{a.max():.2f})",
                f"{b.median():.2f} ({b.min():.2f}–{b.max():.2f})",f"{smaller}/5"])
            phrases.append(f"{label.lower()} {component} {smaller}/5")
    cancellation=0
    for domain in ("original","wide"):
        for comparison in ("72_to_120h","120_to_168h"):
            subset=changes[changes.comparison.eq(comparison)].set_index(["time_utc","metric"])
            for stamp in subset.index.get_level_values(0).unique():
                s=subset.loc[(stamp,"net_surface_ppb"),f"{domain}_duration_change"]
                b=subset.loc[(stamp,"background_ppb"),f"{domain}_duration_change"]
                t=subset.loc[(stamp,"total_prior_ppb"),f"{domain}_duration_change"]
                cancellation+=int(s*b<0 and abs(t)<max(abs(s),abs(b)))
    def duration_change(stamp: str, metric: str, domain: str, comparison: str="120_to_168h") -> float:
        match=changes[changes.time_utc.eq(pd.Timestamp(stamp))&changes.metric.eq(metric)&changes.comparison.eq(comparison)]
        if len(match)!=1: raise ValueError(f"Missing convergence example: {stamp}/{metric}/{comparison}")
        return float(match.iloc[0][f"{domain}_duration_change"])
    cancel_surface=duration_change("2019-09-24T18:00","net_surface_ppb","wide")
    cancel_background=duration_change("2019-09-24T18:00","background_ppb","wide")
    cancel_total=duration_change("2019-09-24T18:00","total_prior_ppb","wide")
    severe_original=duration_change("2019-10-06T06:00","total_prior_ppb","original")
    severe_wide=duration_change("2019-10-06T06:00","total_prior_ppb","wide")
    severe_original_background=duration_change("2019-10-06T06:00","background_ppb","original")
    severe_wide_background=duration_change("2019-10-06T06:00","background_ppb","wide")
    convergence_interpretation=("The 120-to-168-hour increment is smaller than the 72-to-120-hour increment in "
        +", ".join(phrases)+f" representative comparisons. Opposing surface and background changes reduce the combined increment in {cancellation} of 20 domain–duration–receptor contrasts. "
        f"For the widened 24 September 18:00 UTC case, a {cancel_surface:+.2f} ppb surface increment and "
        f"{cancel_background:+.2f} ppb background increment leave only {cancel_total:+.2f} ppb in the combined term; "
        "this is component cancellation, not joint convergence. In the severe 6 October 06:00 UTC case, the "
        f"combined increment falls from {severe_original:+.2f} ppb in the original domain to {severe_wide:+.2f} ppb "
        f"when widened, while the corresponding background increment falls from {severe_original_background:+.2f} "
        f"to {severe_wide_background:+.2f} ppb. Because no prospective tolerance defines negligible change, "
        "these results describe stabilization tendencies rather than declaring convergence or atmospheric accuracy.")
    convergence_table=markdown_table(["Domain","Component","Absolute 72–120 h median (range), ppb",
        "Absolute 120–168 h median (range), ppb","Later increment smaller"],summary)
    ch4=observed.loc["ch4"]
    domain_summary=(f"The full-ensemble correction increases the 95% particle-retention pass count from "
        f"{original_pass} to {wide_pass} of 52 receptor hours. On the matched retained hours, the mean net prior "
        f"surface-methane term changes by {surface.same_hour_change:+.2f} ppb; recovered hours have mean observed "
        f"CH₄ {ch4.recovered_minus_retained:+.2f} ppb relative to retained hours. A pre-declared five-case matrix "
        "shows that surface, endpoint-background and combined duration responses must be assessed separately; "
        "no prospective tolerance supports a binary convergence claim, and the inversion remains unchanged.")
    values={"D_FIGURES":"outputs/hysplit/domain_budget_extension/figures","D_DECISION":decision,
        "D_DECOMPOSITION_TABLE":decomposition_table,"D_SELECTION_INTERPRETATION":selection_interpretation,
        "D_OBSERVED_TABLE":observed_table,"D_STRATA_INTERPRETATION":strata_interpretation,
        "D_CONVERGENCE_INTERPRETATION":convergence_interpretation,"D_CONVERGENCE_TABLE":convergence_table,
        "DOMAIN_SUMMARY":domain_summary}
    template=(ROOT/"docs/BKT_Domain_Budget_appendix.md").read_text()
    required=set(re.findall(r"\{\{([A-Z0-9_]+)\}\}",template))
    if required-values.keys(): raise ValueError(f"Missing domain report tokens: {required-values.keys()}")
    text=re.sub(r"\{\{([A-Z0-9_]+)\}\}",lambda match:values[match[1]],template)
    if "{{" in text: raise ValueError("Unresolved domain report token")
    values["DOMAIN_APPENDIX"]=text
    return values


if __name__=="__main__":
    values=build_domain_sections()
    (OUT/"report_values.json").write_text(__import__("json").dumps(values,indent=2)+"\n")
    print("Domain-budget report evidence is complete")
