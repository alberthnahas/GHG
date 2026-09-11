"""Reproducible posterior, withheld prediction, robustness and recovery analysis."""
from __future__ import annotations
import argparse
import json
import numpy as np
import pandas as pd
import xarray as xr
from scipy.linalg import solve_triangular
from scipy.stats import norm
from a46_bkt_inversion_transport import OUT
from bkt_methane_inverse import InverseProblem,correlated_error,chain_diagnostics

TABLES=OUT/"tables"
COMPONENTS=["anthro_near","anthro_far","wetlands","fire"]
PARAMETERS=COMPONENTS+["background_offset","background_trend"]


def load_complete_operator():
    frame=pd.read_csv(TABLES/"operator_base.csv",parse_dates=["time_utc"])
    selection=pd.read_csv(OUT/"receptor_selection.csv",parse_dates=["time_utc"])
    wanted=selection.loc[selection.retained,"time_utc"].sort_values().to_numpy()
    if len(frame)!=len(wanted) or not np.array_equal(frame.time_utc.to_numpy(),wanted):
        raise ValueError("Cannot infer emissions from an incomplete or mismatched receptor operator")
    return frame


def problem(frame,mask=None,transport=.5,background_sd=20.,prior_factor=2.,
            background_shift=0.,fixed_scale=1.,crop_overlap=False,representation=1.,correlation_hours=24.,geology_scale=1.):
    k=frame[[c+"_ppb" for c in COMPONENTS]].to_numpy().copy()
    if crop_overlap:k[:,3]+=frame.crop_overlap_ppb
    fixed=(frame.termites_ppb+geology_scale*frame.geological_ppb-frame.soil_uptake_ppb).to_numpy()*fixed_scale
    b=np.column_stack([np.ones(len(frame)),(frame.time_utc-pd.Timestamp("2019-09-23")).dt.total_seconds()/(28*86400)])
    base=frame.background_ppb.to_numpy()+background_shift+fixed
    y=frame.ch4.to_numpy()-base
    covariance=correlated_error(frame.time_utc,k.sum(axis=1),frame.time_utc.dt.hour.eq(18),
        transport_fraction=transport,representativeness_scale=representation,transport_correlation_hours=correlation_hours)
    auxiliary=(frame.termites_ppb+frame.geological_ppb+frame.soil_uptake_ppb).to_numpy()
    covariance+=np.diag(auxiliary**2)
    sd=np.r_[np.repeat(np.log(prior_factor),4),background_sd,10.]
    mask=np.ones(len(frame),bool) if mask is None else np.asarray(mask,bool)
    p=InverseProblem(k[mask],b[mask],y[mask],covariance[np.ix_(mask,mask)],sd)
    return p,k,b,base,covariance


def metrics(observed,predicted):
    o=np.asarray(observed);p=np.asarray(predicted);error=p-o
    return dict(n=len(o),bias_ppb=error.mean(),mae_ppb=np.abs(error).mean(),
        rmse_ppb=np.sqrt(np.mean(error**2)),correlation=np.corrcoef(o,p)[0,1] if len(o)>2 and np.std(p)>0 else np.nan,
        r2=1-np.sum(error**2)/np.sum((o-o.mean())**2) if np.std(o)>0 else np.nan)


def baseline(frame,train,kind):
    p,k,b,base,r=problem(frame,train)
    target=frame.ch4.to_numpy()-base-(k.sum(axis=1) if kind=="inventory_adjusted" else 0)
    chol=np.linalg.cholesky(r[np.ix_(train,train)])
    bw=solve_triangular(chol,b[train],lower=True);yw=solve_triangular(chol,target[train],lower=True)
    beta=np.linalg.solve(bw.T@bw+np.diag([1/20.**2,1/10.**2]),bw.T@yw)
    return base+b@beta+(k.sum(axis=1) if kind=="inventory_adjusted" else 0)


def run():
    frame=load_complete_operator()
    excluded=frame[~frame.transport_usable].copy()
    excluded.to_csv(TABLES/"transport_exclusions.csv",index=False)
    frame=frame[frame.transport_usable].reset_index(drop=True)
    train=(~frame.holdout).to_numpy()
    if train.sum()<20 or (~train).sum()<6:
        raise ValueError("Transport screening leaves too few fitting/evaluation hours; expand meteorological coverage before inversion")
    p,k,b,base,r=problem(frame,train)
    center,local_cov,result=p.fit()
    chains,accept=p.sample()
    rh,ess=chain_diagnostics(chains)
    if np.max(rh)>1.01 or np.min(ess)<1000:
        raise RuntimeError(f"Posterior convergence inadequate: Rhat={rh}, ESS={ess}; extend chains")
    samples=chains.reshape(-1,p.ndim)
    np.savez_compressed(OUT/"posterior_samples.npz",chains=chains,parameters=PARAMETERS,
        prior_sd=p.prior_sd,map=center,local_covariance=local_cov,acceptance=accept)
    rows=[]
    for j,name in enumerate(PARAMETERS):
        v=np.exp(samples[:,j]) if j<4 else samples[:,j]
        q=np.quantile(v,[.025,.16,.5,.84,.975])
        priorq=np.exp(norm.ppf([.025,.5,.975])*p.prior_sd[j]) if j<4 else norm.ppf([.025,.5,.975])*p.prior_sd[j]
        rows.append(dict(parameter=name,posterior_mean=v.mean(),q025=q[0],q16=q[1],median=q[2],q84=q[3],q975=q[4],
            prior_q025=priorq[0],prior_median=priorq[1],prior_q975=priorq[2],
            prior_to_posterior_log_variance_reduction_percent=100*(1-np.var(samples[:,j])/p.prior_sd[j]**2),
            probability_above_inventory=float((v>1).mean()) if j<4 else np.nan,
            rhat=rh[j],ess=ess[j]))
    pd.DataFrame(rows).to_csv(TABLES/"posterior_parameters.csv",index=False)
    pd.DataFrame(np.corrcoef(samples.T),index=PARAMETERS,columns=PARAMETERS).to_csv(TABLES/"posterior_parameter_correlation.csv")
    pd.DataFrame(np.corrcoef(k[train].T),index=COMPONENTS,columns=COMPONENTS).to_csv(TABLES/"source_response_correlation.csv")
    # Prior-whitened local information: a diagnostic of this finite state, not pixel resolution.
    jdata=p.jacobian(center)[:train.sum()]*p.prior_sd
    singular=np.linalg.svd(jdata,compute_uv=False)
    info=singular**2/(1+singular**2)
    pd.DataFrame(dict(mode=np.arange(1,len(info)+1),singular_value=singular,information_fraction=info)).to_csv(TABLES/"inversion_information_modes.csv",index=False)
    pred=base[None,:]+np.exp(samples[:,:4])@k.T+samples[:,4:]@b.T
    rng=np.random.default_rng(20260905)
    # Parameter-plus-mismatch envelope for source-only predictions. This samples
    # fresh marginal mismatch, not a conditional Gaussian forecast that kriges
    # correlated training residuals into held-out hours.
    predobs=pred+rng.normal(size=pred.shape)*np.sqrt(np.diag(r))[None,:]
    for name,v in (("posterior",pred),("predictive",predobs)):
        for label,q in (("q025",.025),("median",.5),("q975",.975)):
            frame[f"{name}_{label}_ppb"]=np.quantile(v,q,axis=0)
    frame["prior_inventory_ppb"]=base+k.sum(axis=1)
    frame["background_only_ppb"]=baseline(frame,train,"background_only")
    frame["inventory_adjusted_ppb"]=baseline(frame,train,"inventory_adjusted")
    frame["posterior_residual_ppb"]=frame.ch4-frame.posterior_median_ppb
    frame["mismatch_sd_ppb"]=np.sqrt(np.diag(r))
    frame["posterior_mean_ppb"]=pred.mean(axis=0)
    frame.to_csv(TABLES/"inversion_predictions.csv",index=False)
    worked_index=int(np.flatnonzero(~train)[0])
    mean_alpha=np.exp(samples[:,:4]).mean(axis=0);mean_beta=samples[:,4:].mean(axis=0)
    worked=[("Endpoint background",float(frame.background_ppb.iloc[worked_index])),
            ("Background offset and trend",float(b[worked_index]@mean_beta)),
            ("Fixed termites + geology − soil",float(base[worked_index]-frame.background_ppb.iloc[worked_index]))]
    worked.extend((name,float(k[worked_index,j]*mean_alpha[j])) for j,name in enumerate(COMPONENTS))
    total=sum(value for _,value in worked)
    if not np.isclose(total,pred[:,worked_index].mean(),rtol=1e-12):raise ValueError("Worked inverse budget fails linear expectation identity")
    worked.extend([("Posterior mean concentration",total),("Observed concentration",float(frame.ch4.iloc[worked_index])),
                   ("Observed minus posterior mean",float(frame.ch4.iloc[worked_index]-total))])
    pd.DataFrame([dict(time_utc=frame.time_utc.iloc[worked_index],term=term,value_ppb=value) for term,value in worked]).to_csv(TABLES/"worked_inverse_budget.csv",index=False)
    evaluations=[]
    for split,mask in (("training",train),("heldout",~train),("all",np.ones(len(frame),bool))):
        for label,col in (("inventory","prior_inventory_ppb"),("background_only","background_only_ppb"),
                          ("background_adjusted_inventory","inventory_adjusted_ppb"),("posterior","posterior_median_ppb")):
            evaluations.append(dict(split=split,model=label,**metrics(frame.ch4[mask],frame[col][mask])))
    pd.DataFrame(evaluations).to_csv(TABLES/"inversion_evaluation.csv",index=False)
    pd.DataFrame([dict(training_hours=int(train.sum()),heldout_hours=int((~train).sum()),excluded_transport=len(excluded),
        effective_information_modes=info.sum(),maximum_rhat=rh.max(),minimum_ess=ess.min(),
        acceptance_min=accept.min(),acceptance_max=accept.max(),
        heldout_predictive_coverage_percent=100*((frame.ch4>=frame.predictive_q025_ppb)&(frame.ch4<=frame.predictive_q975_ppb))[~train].mean(),
        weighted_misfit=float(np.sum(p.residual(center)[:train.sum()]**2)),
        prior_penalty=float(np.sum((center/p.prior_sd)**2)))]).to_csv(TABLES/"inversion_summary.csv",index=False)
    print(pd.DataFrame(rows).to_string(index=False),flush=True)


def robustness():
    frame=load_complete_operator()
    frame=frame[frame.transport_usable].reset_index(drop=True)
    train=(~frame.holdout).to_numpy();rows=[];predictions=[]
    cases={"base":{},"background_minus20":dict(background_shift=-20),"background_plus20":dict(background_shift=20),
        "background_prior10":dict(background_sd=10),"background_prior40":dict(background_sd=40),
        "transport30percent":dict(transport=.3),"transport80percent":dict(transport=.8),
        "correlation6h":dict(correlation_hours=6),"correlation72h":dict(correlation_hours=72),
        "prior_factor1p5":dict(prior_factor=1.5),"prior_factor3":dict(prior_factor=3),
        "auxiliary_half":dict(fixed_scale=.5),"auxiliary_double":dict(fixed_scale=2),
        "unscaled_geological_prior":dict(geology_scale=37.5/1.6),
        "crop_overlap_retained":dict(crop_overlap=True),"representativeness_half":dict(representation=.5),
        "representativeness_double":dict(representation=2),"daytime_only":{},"shared_anthropogenic_scale":{}}
    for label,kwargs in cases.items():
        use=train&frame.time_utc.dt.hour.eq(6).to_numpy() if label=="daytime_only" else train
        p,k,b,base,r=problem(frame,use,**kwargs)
        if label=="shared_anthropogenic_scale":
            merged=np.column_stack([p.response[:,:2].sum(axis=1),p.response[:,2:]])
            joint=InverseProblem(merged,p.background_design,p.enhancement,p.error_covariance,p.prior_sd[[0,2,3,4,5]])
            reduced,reduced_cov,result=joint.fit();mapping=[0,0,1,2,3,4]
            theta=reduced[mapping];cov=reduced_cov[np.ix_(mapping,mapping)]
        else:theta,cov,result=p.fit()
        se=np.sqrt(np.diag(cov))
        pred=base+k@np.exp(theta[:4])+b@theta[4:]
        for j,name in enumerate(PARAMETERS):
            value=np.exp(theta[j]) if j<4 else theta[j]
            low,high=np.exp(theta[j]+np.array([-1,1])*1.96*se[j]) if j<4 else theta[j]+np.array([-1,1])*1.96*se[j]
            rows.append(dict(case=label,parameter=name,map=value,local_q025=low,local_q975=high,
                interval_method="Local Gauss-Newton approximation; main intervals use MCMC"))
        predictions.append(dict(case=label,training_hours=int(use.sum()),**metrics(frame.ch4[~train],pred[~train])))
    pd.DataFrame(rows).to_csv(TABLES/"inversion_sensitivity.csv",index=False)
    pd.DataFrame(predictions).to_csv(TABLES/"inversion_sensitivity_evaluation.csv",index=False)
    # Complete-week exclusions plus a 24-hour buffer reduce direct temporal leakage.
    weeks=((frame.time_utc-pd.Timestamp("2019-09-09")).dt.days//7).to_numpy();cv=[]
    for week in range(4):
        held=weeks==week;first=frame.time_utc[held].min()-pd.Timedelta(hours=24);last=frame.time_utc[held].max()+pd.Timedelta(hours=24)
        fit=~frame.time_utc.between(first,last).to_numpy()
        p,k,b,base,r=problem(frame,fit);theta,_,_=p.fit()
        estimates={"posterior":base+k@np.exp(theta[:4])+b@theta[4:],
                   "background_adjusted_inventory":baseline(frame,fit,"inventory_adjusted"),
                   "background_only":baseline(frame,fit,"background_only")}
        for name,pred in estimates.items():cv.append(dict(heldout_week=week+1,model=name,training_hours=int(fit.sum()),**metrics(frame.ch4[held],pred[held])))
    pd.DataFrame(cv).to_csv(TABLES/"week_block_evaluation.csv",index=False)


def synthetic():
    frame=load_complete_operator()
    frame=frame[frame.transport_usable].reset_index(drop=True);train=(~frame.holdout).to_numpy()
    p,k,b,base,r=problem(frame,train)
    rng=np.random.default_rng(913);truth=np.array([1.5,.7,1.2,.6]);beta=np.array([8.,-5.])
    rows=[];draw_rows=[]
    for scenario in ("matched_operator","transport_and_background_perturbed"):
        for trial in range(200):
            kt=k.copy();perturb=np.zeros(len(frame))
            if scenario!="matched_operator":
                # Deliberately violate the fitted operator using coherent source-specific
                # 30% amplitude distortions and a nonlinear 15 ppb boundary perturbation.
                kt*=np.exp(rng.normal(0,.3,4)-.5*.3**2)[None,:]
                days=(frame.time_utc-frame.time_utc.min()).dt.total_seconds().to_numpy()/86400
                perturb=15*np.sin(2*np.pi*days/14+rng.uniform(0,2*np.pi))
            observed=kt@truth+b@beta+perturb+np.linalg.cholesky(r)@rng.normal(size=len(frame))
            test=InverseProblem(k[train],b[train],observed[train],r[np.ix_(train,train)],p.prior_sd)
            theta,cov,_=test.fit();sd=np.sqrt(np.diag(cov))
            for j,name in enumerate(COMPONENTS):
                lo,hi=np.exp(theta[j]+np.array([-1,1])*1.96*sd[j]);estimate=np.exp(theta[j])
                draw_rows.append(dict(scenario=scenario,trial=trial,parameter=name,truth=truth[j],estimate=estimate,
                    local_q025=lo,local_q975=hi,covered=lo<=truth[j]<=hi))
        sample=pd.DataFrame([row for row in draw_rows if row["scenario"]==scenario])
        for name,group in sample.groupby("parameter",sort=False):
            rows.append(dict(scenario=scenario,parameter=name,trials=len(group),truth=group.truth.iloc[0],
                mean_estimate=group.estimate.mean(),median_estimate=group.estimate.median(),
                bias=(group.estimate-group.truth).mean(),rmse=np.sqrt(((group.estimate-group.truth)**2).mean()),
                local_interval_coverage_percent=100*group.covered.mean(),
                estimator_q025=group.estimate.quantile(.025),estimator_q975=group.estimate.quantile(.975)))
    pd.DataFrame(rows).to_csv(TABLES/"synthetic_recovery_summary.csv",index=False)
    pd.DataFrame(draw_rows).to_csv(TABLES/"synthetic_recovery_trials.csv",index=False)


def emission_budget():
    from bkt_footprint_spatial import cell_area_km2,sensitivity_support_mask
    from a43_bkt_source_analysis import MW
    with xr.open_dataset(OUT/"monthly_prior_fluxes.nc") as ds:monthly=ds.load()
    with xr.open_dataset(OUT/"daily_fire_prior_fluxes.nc") as ds:fire=ds.load()
    with xr.open_dataset(OUT/"spatial_operator_base.nc") as ds:spatial=ds.load()
    operator=load_complete_operator()
    support=sensitivity_support_mask(spatial.footprint.sel(receptor=operator.loc[operator.transport_usable,"time_utc"].values).mean("receptor").values)
    posterior=np.load(OUT/"posterior_samples.npz")
    alpha=np.exp(posterior["chains"].reshape(-1,6)[:,:4])
    near=spatial.distance_km.values<=500
    area=cell_area_km2(monthly.lat.values,monthly.lon.values)*1e6
    conversion=area*MW["CH4"]*1e-15  # umol -> Gg, after multiplying by seconds
    duration=np.array([22,6])*86400
    rows=[];sector_rows=[]
    source_masses={}
    for source in monthly.source.values:
        grid=(monthly.flux.sel(source=source).values*duration[:,None,None]).sum(axis=0)*conversion
        source_masses[str(source)]=grid
    fire_mass=fire.noncrop_fire_flux.sel(day=slice("2019-09-09","2019-10-06")).sum("day").values*86400*conversion
    for region,mask,column in (("within_500km",near,0),("beyond_500km_in_domain",~near,1)):
        anthropogenic=0;anthro_support=0
        for source,grid in source_masses.items():
            if not source.startswith("CH4_"):continue
            mass=grid[mask].sum();anthropogenic+=mass;anthro_support+=grid[mask&support].sum()
            q=np.quantile(mass*alpha[:,column],[.025,.5,.975])
            sector_rows.append(dict(region=region,sector=source,prior_Gg=mass,posterior_q025_Gg=q[0],
                posterior_median_Gg=q[1],posterior_q975_Gg=q[2],
                qualification="Conditional reallocation of fixed sector patterns; sectors are not independently retrieved"))
        for component,mass,supported_mass,col in (("anthropogenic",anthropogenic,anthro_support,column),
            ("wetlands",source_masses["wetlands"][mask].sum(),source_masses["wetlands"][mask&support].sum(),2),
            ("noncrop_fire",fire_mass[mask].sum(),fire_mass[mask&support].sum(),3)):
            q=np.quantile(mass*alpha[:,col],[.025,.5,.975])
            rows.append(dict(region=region,component=component,period_start="2019-09-09",period_end_inclusive="2019-10-06",
                prior_Gg=mass,posterior_q025_Gg=q[0],posterior_median_Gg=q[1],posterior_q975_Gg=q[2],
                support_prior_Gg=supported_mass,support_prior_share_percent=100*supported_mass/mass,
                support_posterior_median_Gg=supported_mass*np.median(alpha[:,col])))
    pd.DataFrame(rows).to_csv(TABLES/"conditional_emission_budget.csv",index=False)
    pd.DataFrame(sector_rows).to_csv(TABLES/"conditional_sector_emissions.csv",index=False)


def transport_diagnostics():
    base=load_complete_operator().set_index("time_utc")
    rows=[]
    for group,expected in (("seed_m10",4),("height60",4),("n2000",2),("window72",2),("window168",2)):
        sample=pd.read_csv(TABLES/f"operator_{group}.csv",parse_dates=["time_utc"])
        if len(sample)!=expected:raise ValueError(f"Incomplete sensitivity group {group}: {len(sample)}/{expected}")
        for r in sample.itertuples():
            ref=base.loc[r.time_utc]
            prior=sum(getattr(r,c+"_ppb") for c in COMPONENTS)
            prior0=sum(ref[c+"_ppb"] for c in COMPONENTS)
            rows.append(dict(group=group,time_utc=r.time_utc,
                source_increment_change_percent=100*(prior/prior0-1),
                sensitivity_change_percent=100*(r.sensitivity/ref.sensitivity-1),
                background_change_ppb=(r.background_ppb-ref.background_ppb) if r.transport_usable and ref.transport_usable else np.nan,
                prior_concentration_change_ppb=(prior-prior0+r.background_ppb-ref.background_ppb) if r.transport_usable and ref.transport_usable else np.nan,
                endpoint_retention_percent=100*r.endpoint_survival_fraction))
    pd.DataFrame(rows).to_csv(TABLES/"transport_sensitivity_comparison.csv",index=False)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("stage",choices=["fit","robustness","synthetic","budget","transport"])
    {"fit":run,"robustness":robustness,"synthetic":synthetic,"budget":emission_budget,"transport":transport_diagnostics}[p.parse_args().stage]()
