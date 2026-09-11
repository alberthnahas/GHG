"""Independent numerical and provenance gates for the BKT methane inversion."""
from __future__ import annotations
import hashlib
import json
import numpy as np
import pandas as pd
import xarray as xr
from a46_bkt_inversion_transport import ROOT,OUT,DATES
from a49_bkt_methane_inversion import COMPONENTS,problem
from bkt_methane_inverse import chain_diagnostics
from a48_bkt_inversion_operator import arl_surface


def validate():
    table=OUT/"tables";checks=[]
    def check(condition,label):
        if not condition:raise ValueError(label)
        checks.append(dict(check=label,status="passed"))
    selection=pd.read_csv(OUT/"receptor_selection.csv",parse_dates=["time_utc"])
    frame=pd.read_csv(table/"operator_base.csv",parse_dates=["time_utc"])
    check(len(frame)==int(selection.retained.sum()),"Every retained observation has one transport operator")
    check(not frame.time_utc.duplicated().any(),"Receptor operator timestamps unique")
    check(frame.time_utc.equals(frame.time_utc.sort_values()),"Receptor chronology monotonic")
    expected=((selection.time_utc.dt.normalize()-pd.Timestamp("2019-09-09")).dt.days%4==3)
    check(np.array_equal(selection.holdout,expected),"Withheld days match predeclared schedule")
    check(frame.endpoint_survival_fraction.between(0,1).all(),"Particle survival fraction bounded")
    check(frame.T02M.between(150,350).all(),"Native temperature diagnostic physically bounded")
    packing=[]
    for row in frame.itertuples():
        path=ROOT/"data/hysplit/gfs0p25/regional"/row.time_utc.strftime("%Y%m%d_gfs0p25")
        _,precision=arl_surface(path,"PBLH",row.time_utc.hour)
        packing.append(dict(time_utc=row.time_utc,PBLH_m=row.PBLH,packing_precision_m=precision,
                            valid_for_height_scatter=row.PBLH>=0))
        check(-precision<=row.PBLH<=10000,f"Native PBL diagnostic within nonnegative range plus packing precision {row.time_utc}")
    pd.DataFrame(packing).to_csv(table/"native_meteorology_quality.csv",index=False)
    check(frame.U10M.abs().lt(100).all() and frame.V10M.abs().lt(100).all(),"Native surface-wind magnitudes physically bounded")
    check(np.allclose(frame.SHGT,816.,atol=.1),"Fixed nearest-cell GFS terrain consistently decoded")
    for col in [c+"_ppb" for c in COMPONENTS]+["background_ppb","termites_ppb","geological_ppb","soil_uptake_ppb"]:
        check(np.isfinite(frame[col]).all() and (frame[col]>=0).all(),f"Finite positive response {col}")
    inputq=pd.read_csv(table/"inversion_input_quality.csv")
    check(len(inputq)==24 and inputq.missing.eq(0).all() and inputq.negative.eq(0).all(),"Twelve monthly source fields complete for both months")
    global_audit=pd.read_csv(table/"natural_source_global_audit.csv").set_index("source")
    check(32<global_audit.loc["soil","global_annual_magnitude_Tg_CH4"]<35,"Processed MeMo methane mass agrees with documented global scale")
    check(1.4<global_audit.loc["geological","global_annual_magnitude_Tg_CH4"]<1.8,"Geological global scaling matches distributed 1.6 Tg/year constraint")
    with xr.open_dataset(OUT/"daily_fire_prior_fluxes.nc") as ds:
        check(len(ds.day)==35,"Daily fire coverage includes seven-day sensitivity endpoints")
        check(np.allclose(ds.all_fire_flux,ds.crop_fire_flux+ds.noncrop_fire_flux,rtol=1e-12,atol=1e-14),"Fire partition conserves methane")
        check(float(ds.noncrop_fire_flux.min())>=-1e-14,"Non-crop fire flux nonnegative")
    with xr.open_dataset(OUT/"spatial_operator_base.nc") as ds:
        check(len(ds.receptor)==len(frame),"Spatial and tabular receptor counts reconcile")
        for j,c in enumerate(COMPONENTS):
            # Variable discovered from the operator writer; sum spatial contributions.
            direct=ds.prior_contribution.sel(component=c).sum(["lat","lon"]).values
            check(np.allclose(direct,frame[c+"_ppb"],rtol=1e-10,atol=1e-10),f"Spatial convolution reconciles {c}")
        check(np.allclose(ds.footprint.sum(["lat","lon"]),frame.sensitivity,rtol=1e-10),"Spatial footprint integral reconciles")
    frame=frame[frame.transport_usable].reset_index(drop=True);train=(~frame.holdout).to_numpy()
    p,k,b,base,r=problem(frame,train)
    check(np.linalg.eigvalsh(r).min()>0,"Full mismatch covariance positive definite")
    posterior=np.load(OUT/"posterior_samples.npz")
    chains=posterior["chains"];samples=chains.reshape(-1,6)
    rh,ess=chain_diagnostics(chains)
    check(np.max(rh)<=1.01 and np.min(ess)>=1000,"Sampled posterior passes convergence and ESS thresholds")
    params=pd.read_csv(table/"posterior_parameters.csv")
    for j,row in params.iterrows():
        sample=np.exp(samples[:,j]) if j<4 else samples[:,j]
        check(np.allclose(np.quantile(sample,[.025,.5,.975]),row[["q025","median","q975"]].to_numpy(float),rtol=1e-10),f"Posterior quantiles reconcile {row.parameter}")
    prediction=pd.read_csv(table/"inversion_predictions.csv")
    direct=base[None,:]+np.exp(samples[:,:4])@k.T+samples[:,4:]@b.T
    check(np.allclose(np.median(direct,axis=0),prediction.posterior_median_ppb,rtol=1e-12),"Predictions independently reconstructed from posterior draws")
    check(np.allclose(base+k.sum(axis=1),prediction.prior_inventory_ppb,rtol=1e-12),"Prior budget including negative soil sign reconciles")
    worked=pd.read_csv(table/"worked_inverse_budget.csv")
    check(np.isclose(worked.value_ppb.iloc[:7].sum(),worked.loc[worked.term.eq("Posterior mean concentration"),"value_ppb"].iloc[0],rtol=1e-12),"Worked inverse budget additive identity")
    evaluation=pd.read_csv(table/"inversion_evaluation.csv")
    columns={"inventory":"prior_inventory_ppb","background_only":"background_only_ppb",
             "background_adjusted_inventory":"inventory_adjusted_ppb","posterior":"posterior_median_ppb"}
    for row in evaluation.itertuples():
        mask=train if row.split=="training" else ~train if row.split=="heldout" else np.ones(len(frame),bool)
        error=prediction.loc[mask,columns[row.model]].values-frame.ch4[mask].values
        check(row.n==mask.sum() and np.isclose(np.sqrt(np.dot(error,error)/len(error)),row.rmse_ppb,rtol=1e-12),f"Independent RMSE {row.split}/{row.model}")
    budget=pd.read_csv(table/"conditional_emission_budget.csv")
    for row in budget.itertuples():
        j=(0 if row.region=="within_500km" else 1) if row.component=="anthropogenic" else 2 if row.component=="wetlands" else 3
        expected=row.prior_Gg*np.quantile(np.exp(samples[:,j]),[.025,.5,.975])
        check(np.allclose(expected,[row.posterior_q025_Gg,row.posterior_median_Gg,row.posterior_q975_Gg],rtol=1e-12),f"Conditional mass uncertainty {row.region}/{row.component}")
    recovery=pd.read_csv(table/"synthetic_recovery_trials.csv")
    check(len(recovery)==1600 and recovery.groupby(["scenario","parameter"]).size().eq(200).all(),"All synthetic recovery trials retained")
    transport=pd.read_csv(table/"transport_sensitivity_comparison.csv")
    check(len(transport)==14,"All preselected transport sensitivity experiments compared")
    display_path=table/"inversion_display_integrity.csv"
    if display_path.exists():
        display=pd.read_csv(display_path).iloc[0]
        check(np.isclose(display.raw_integral,display.display_integral,rtol=1e-10),"Inversion display conserves footprint integral")
        check(display.receptors==len(frame),"Inversion map uses exactly the transport-eligible receptor ensemble")
    for day in DATES:
        met=ROOT/"data/hysplit/gfs0p25/regional"/f"{day:%Y%m%d}_gfs0p25"
        ct=ROOT/"data/bkt_sources/inversion/carbontracker"/f"CTCH4_2025.molefrac_glb3x2_{day:%Y-%m-%d}.nc"
        for path in (met,ct):
            record=json.loads(path.with_name(path.name+".json").read_text())
            check(hashlib.sha256(path.read_bytes()).hexdigest()==record["sha256"],f"Input checksum {path.name}")
    pd.DataFrame(checks).to_csv(table/"inversion_validation_checks.csv",index=False)
    result=dict(status="passed",checks=len(checks),receptors=len(frame),scope="Numerical and provenance validation, not independent emission truth")
    (OUT/"inversion_validation.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__=="__main__":validate()
