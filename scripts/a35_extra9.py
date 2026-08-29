"""Findings 151-200: transitions, regimes, tails, memory and sampling.

This pass tests ten physical questions at each of the five stations.  The unit
of replication is the station, but the methods differ: diurnal transition
timing, within-night curvature, next-day carry-over, seasonal distribution
shift, multigas clustering, compound extremes, event ageing, surrogate-tested
memory, leave-year stability, and fixed-hour sampling bias.

All calculations use the harmonised cache produced by ``a0_build.py`` and the
species-specific quality flags applied by ``ghg_common.clean``.  Sorong before
June 2023 therefore cannot enter a physical result.  Skewed relationships carry
both Pearson and Spearman coefficients; persistence is tested against shuffled
surrogates; and results that are weak remain in the output.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.cluster.vq import kmeans2
from scipy.stats import spearmanr, wilcoxon

import ghg_common as G

OUT = Path(__file__).resolve().parent.parent / "outputs"
SP = ("co2", "ch4", "co")


def save(df, name):
    df.to_csv(OUT / name, index=False)
    print(f"\n{name}\n{df.to_string(index=False)}")
    return df


def paired(d, st):
    x = d[d.station == st].copy()
    for sp in SP:
        x = G.clean(x, sp)
    return x.dropna(subset=list(SP))


def robust_anomaly(x):
    z = pd.DataFrame(index=x.index)
    for sp in SP:
        clim = x.groupby(["month", "hour_local"])[sp].transform("median")
        a = x[sp] - clim
        scale = np.nanmedian(np.abs(a - np.nanmedian(a))) * 1.4826
        z[sp] = a / scale if scale > 0 else a
    return z.replace([np.inf, -np.inf], np.nan)


def transition_clock(d):
    rows = []
    for st in G.ORDER:
        x = paired(d, st)
        h = x.groupby("hour_local").co2.median().reindex(range(24))
        delta = h.diff()
        morning = delta.loc[5:12].idxmin()
        evening = delta.loc[16:23].idxmax()
        rows.append(dict(station=st, n_hours=len(x), morning_collapse_hour=int(morning),
                         collapse_step_ppm=round(float(delta[morning]), 2),
                         evening_buildup_hour=int(evening),
                         buildup_step_ppm=round(float(delta[evening]), 2),
                         transition_separation_h=int((evening-morning) % 24)))
    return save(pd.DataFrame(rows), "ab_transition_clock.csv")


def nocturnal_curvature(d):
    rows=[]
    for st in G.ORDER:
        x=paired(d,st).copy(); x["night_date"]=(x.time_local-pd.Timedelta(hours=8)).dt.date
        vals=[]
        for _,g in x[x.hour_local.isin([20,21,22,23,0,1,2,3])].groupby("night_date"):
            e=g[g.hour_local.isin([20,21,22,23])].groupby('hour_local').co2.median()
            l=g[g.hour_local.isin([0,1,2,3])].groupby('hour_local').co2.median()
            if len(e)==4 and len(l)==4:
                se=np.polyfit(np.arange(4),e.values,1)[0]; sl=np.polyfit(np.arange(4),l.values,1)[0]
                vals.append((se,sl))
        a=np.asarray(vals); diff=a[:,1]-a[:,0]; p=wilcoxon(diff).pvalue if len(diff)>10 and np.any(diff) else np.nan
        rows.append(dict(station=st,n_nights=len(a),early_slope_ppm_h=round(float(np.median(a[:,0])),3),
                         late_slope_ppm_h=round(float(np.median(a[:,1])),3),
                         late_minus_early=round(float(np.median(diff)),3),
                         late_over_early=round(float(np.median(a[:,1])/np.median(a[:,0])),3) if np.median(a[:,0]) else np.nan,
                         wilcoxon_p=round(float(p),4) if np.isfinite(p) else np.nan))
    return save(pd.DataFrame(rows),"ab_nocturnal_curvature.csv")


def carryover(d):
    rows=[]
    for st in G.ORDER:
        x=paired(d,st); aft=x[x.hour_local.between(12,16)].groupby('date').co2.median()
        dawn=x[x.hour_local.between(4,6)].groupby('date').co2.median(); dawn.index=pd.to_datetime(dawn.index)
        aft.index=pd.to_datetime(aft.index); g=pd.concat([aft.rename('afternoon'),dawn.shift(-1,freq='D').rename('next_dawn')],axis=1).dropna()
        for c in g: g[c]=g[c]-g.groupby(g.index.month)[c].transform('median')
        r=float(g.corr().iloc[0,1]); rho=float(spearmanr(g.afternoon,g.next_dawn).statistic)
        rows.append(dict(station=st,n_day_pairs=len(g),pearson_r=round(r,3),spearman_rho=round(rho,3),
                         variance_explained_pct=round(100*r*r,1)))
    return save(pd.DataFrame(rows),"ab_carryover.csv")


def seasonal_shift(d):
    rows=[]
    for st in G.ORDER:
        x=paired(d,st); vals={}
        for sp in SP:
            wet=x.loc[x.month.isin([11,12,1,2,3,4]),sp].values; dry=x.loc[x.month.isin([5,6,7,8,9,10]),sp].values
            edges=np.unique(np.quantile(np.r_[wet,dry],np.linspace(0,1,25))); p=np.histogram(wet,edges)[0]+.5; q=np.histogram(dry,edges)[0]+.5
            p=p/p.sum(); q=q/q.sum(); m=(p+q)/2; vals[sp]=.5*np.sum(p*np.log(p/m))+.5*np.sum(q*np.log(q/m))
        dom=max(vals,key=vals.get)
        rows.append(dict(station=st,n_hours=len(x),js_co2=round(vals['co2'],3),js_ch4=round(vals['ch4'],3),js_co=round(vals['co'],3),
                         dominant_species=dom,max_js_nats=round(vals[dom],3)))
    return save(pd.DataFrame(rows),"ab_seasonal_shift.csv")


def source_regimes(d):
    rows=[]
    for st in G.ORDER:
        x=paired(d,st); z=robust_anomaly(x).dropna(); rng=np.random.default_rng(171+sum(map(ord,st)))
        z=z.iloc[rng.choice(len(z),min(10000,len(z)),False)]; cent,lab=kmeans2(z.values,3,minit='++',iter=40,seed=171)
        counts=np.bincount(lab,minlength=3); rare=int(np.argmin(counts)); hi=int(np.argmax(np.linalg.norm(cent,axis=1)))
        within=np.mean(np.sum((z.values-cent[lab])**2,axis=1)); total=np.mean(np.sum((z.values-z.values.mean(0))**2,axis=1))
        rows.append(dict(station=st,n_hours=len(z),three_regime_variance_explained_pct=round(100*(1-within/total),1),
                         rare_regime_pct=round(100*counts[rare]/len(z),1),distinct_regime_pct=round(100*counts[hi]/len(z),1),
                         distinct_co2_z=round(float(cent[hi,0]),2),distinct_ch4_z=round(float(cent[hi,1]),2),distinct_co_z=round(float(cent[hi,2]),2)))
    return save(pd.DataFrame(rows),"ab_source_regimes.csv")


def compound_extremes(d):
    rows=[]
    for st in G.ORDER:
        z=robust_anomaly(paired(d,st)).dropna().rank(pct=True); best=None
        for a,b in (("co2","ch4"),("co2","co"),("ch4","co")):
            joint=((z[a]>.95)&(z[b]>.95)).mean(); cond=joint/.05
            item=(cond,a,b,joint)
            if best is None or item[0]>best[0]: best=item
        cond,a,b,joint=best
        rows.append(dict(station=st,n_hours=len(z),strongest_pair=f'{a}-{b}',joint_top5_pct=round(100*joint,2),
                         conditional_probability=round(cond,3),multiple_of_independence=round(cond/.05,1)))
    return save(pd.DataFrame(rows),"ab_compound_extremes.csv")


def event_ageing(d):
    rows=[]
    for st in G.ORDER:
        x=paired(d,st); day=x.groupby('date')[list(SP)].median(); bg=day.rolling(31,center=True,min_periods=15).quantile(.2); a=day-bg
        peaks=a.co[a.co>=a.co.quantile(.95)].dropna(); ratios=[]; cof=[]
        for t,v in peaks.items():
            if v<=0 or t+pd.Timedelta(days=3) not in a.index: continue
            r0=a.loc[t,'ch4']/v; r3=a.loc[t+pd.Timedelta(days=3),'ch4']/a.loc[t+pd.Timedelta(days=3),'co'] if a.loc[t+pd.Timedelta(days=3),'co']>0 else np.nan
            ratios.append((r0,r3)); cof.append(a.loc[t+pd.Timedelta(days=3),'co']/v)
        q=np.asarray(ratios,float)
        rows.append(dict(station=st,n_events=len(q),ch4_co_day0=round(float(np.nanmedian(q[:,0])),3),ch4_co_day3=round(float(np.nanmedian(q[:,1])),3),
                         ratio_change=round(float(np.nanmedian(q[:,1]-q[:,0])),3),co_fraction_day3=round(float(np.nanmedian(cof)),3)))
    return save(pd.DataFrame(rows),"ab_event_ageing.csv")


def surrogate_memory(d):
    rows=[]
    for st in G.ORDER:
        x=paired(d,st); s=x.groupby('date').co.median(); s=s-s.rolling(31,center=True,min_periods=15).median(); s=s.dropna()
        obs=float(s.autocorr(1)); rng=np.random.default_rng(186+sum(map(ord,st))); null=[]
        v=s.values.copy()
        for _ in range(1000): null.append(pd.Series(rng.permutation(v)).autocorr(1))
        p=(1+sum(abs(q)>=abs(obs) for q in null))/(len(null)+1)
        rows.append(dict(station=st,n_days=len(s),observed_lag1=round(obs,3),surrogate_mean=round(float(np.mean(null)),3),
                         surrogate_p=round(float(p),4),excess_memory=round(obs-float(np.mean(null)),3)))
    return save(pd.DataFrame(rows),"ab_surrogate_memory.csv")


def yearly_stability(d):
    rows=[]
    for st in G.ORDER:
        x=paired(d,st); z=robust_anomaly(x); z['year']=x.loc[z.index,'year']; pairs=[]
        for a,b in (("co2","ch4"),("co2","co"),("ch4","co")):
            rr=z.groupby('year').apply(lambda g:g[a].corr(g[b]),include_groups=False).dropna()
            pairs.append((float(rr.median()),a,b,rr))
        med,a,b,rr=max(pairs,key=lambda q:abs(q[0]))
        rows.append(dict(station=st,dominant_pair=f'{a}-{b}',n_years=len(rr),median_r=round(med,3),min_r=round(float(rr.min()),3),max_r=round(float(rr.max()),3),
                         same_sign_fraction=round(float(max((rr>0).mean(),(rr<0).mean())),3)))
    return save(pd.DataFrame(rows),"ab_yearly_stability.csv")


def fixed_hour_bias(d):
    rows=[]
    for st in G.ORDER:
        x=paired(d,st); daily=x.groupby(['date','hour_local']).co2.median().unstack(); full=daily.mean(axis=1)
        bias=daily.sub(full,axis=0).median(); best=int(bias.abs().idxmin()); worst=int(bias.abs().idxmax())
        rows.append(dict(station=st,n_days=len(daily),best_single_hour=best,best_bias_ppm=round(float(bias[best]),2),
                         worst_single_hour=worst,worst_bias_ppm=round(float(bias[worst]),2),bias_span_ppm=round(float(bias.max()-bias.min()),2)))
    return save(pd.DataFrame(rows),"ab_fixed_hour_bias.csv")


def main():
    d=pd.read_pickle(OUT/'all.pkl')
    transition_clock(d); nocturnal_curvature(d); carryover(d); seasonal_shift(d); source_regimes(d)
    compound_extremes(d); event_ageing(d); surrogate_memory(d); yearly_stability(d); fixed_hour_bias(d)


if __name__ == '__main__':
    main()
