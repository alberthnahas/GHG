"""Findings 121-150: multivariate structure, nonlinear dependence and scale.

This pass deliberately moves beyond scalar summaries.  It asks how many
independent dimensions the three-gas record contains, whether dependence lives
in the centre or the tails, how information changes with averaging scale, and
whether the five stations share events or can substitute for one another.

The sophistication is methodological, not licence to over-interpret.  Every
cross-station calculation uses daily values and common dates; every hourly
multivariate calculation is within-station and paired; all variables are
standardised before an eigenanalysis; and nonlinear statistics carry a
permutation or simpler linear benchmark.  Raw JSON is never read.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.stats import kendalltau, spearmanr

import ghg_common as G

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
SP = ("co2", "ch4", "co")


def save(df, name):
    df.to_csv(OUT / name, index=False)
    print(f"\n{name}\n{df.to_string(index=False)}")
    return df


def paired(d, st):
    x = d[d.station == st].copy()
    for s in SP:
        x = G.clean(x, s)
    return x.dropna(subset=list(SP))


def anomalies(x):
    """Remove station/species month-hour climatology, then standardise."""
    z = pd.DataFrame(index=x.index)
    for s in SP:
        clim = x.groupby(["month", "hour_local"])[s].transform("median")
        a = x[s] - clim
        mad = np.nanmedian(np.abs(a - np.nanmedian(a))) * 1.4826
        z[s] = a / mad if mad > 0 else a
    return z.replace([np.inf, -np.inf], np.nan).dropna()


def daily_anom(d, sp):
    out = []
    for st in G.ORDER:
        x = G.clean(d[(d.station == st) & d.hour_local.between(12, 16)], sp)
        s = x.groupby("date")[sp].median().dropna()
        a = s - s.rolling(31, center=True, min_periods=15).median()
        out.append(a.rename(st))
    return pd.concat(out, axis=1)


def pca_structure(d):
    rows=[]
    for st in G.ORDER:
        z=anomalies(paired(d,st)); C=np.corrcoef(z.values,rowvar=False)
        val,vec=np.linalg.eigh(C); o=np.argsort(val)[::-1]; val=val[o]; vec=vec[:,o]
        rows.append(dict(station=st,n_hours=len(z),pc1_variance_pct=round(100*val[0]/val.sum(),1),
                         pc2_variance_pct=round(100*val[1]/val.sum(),1),
                         pc1_co2=round(float(vec[0,0]),3),pc1_ch4=round(float(vec[1,0]),3),pc1_co=round(float(vec[2,0]),3)))
    return save(pd.DataFrame(rows),"aa_pca.csv")


def effective_dimension(d):
    rows=[]
    for st in G.ORDER:
        z=anomalies(paired(d,st)); val=np.linalg.eigvalsh(np.corrcoef(z.values,rowvar=False))
        pr=val.sum()**2/np.sum(val**2); ent=-np.sum((val/val.sum())*np.log(val/val.sum()))
        rows.append(dict(station=st,n_hours=len(z),participation_ratio=round(float(pr),3),
                         entropy_dimension=round(float(np.exp(ent)),3),smallest_eigenvalue=round(float(val.min()),3)))
    return save(pd.DataFrame(rows),"aa_dimension.csv")


def partial_dependence(d):
    rows=[]
    for st in G.ORDER:
        z=anomalies(paired(d,st))
        for a,b,c in (("co2","ch4","co"),("co2","co","ch4"),("ch4","co","co2")):
            X=np.column_stack([np.ones(len(z)),z[c]]); ra=z[a]-X@np.linalg.lstsq(X,z[a],rcond=None)[0]; rb=z[b]-X@np.linalg.lstsq(X,z[b],rcond=None)[0]
            rows.append(dict(station=st,pair=f"{a}-{b}",controlled=c,n_hours=len(z),partial_r=round(float(np.corrcoef(ra,rb)[0,1]),3),
                             raw_r=round(float(z[a].corr(z[b])),3)))
    return save(pd.DataFrame(rows),"aa_partial.csv")


def tail_dependence(d, upper=True):
    rows=[]; q=.95 if upper else .05
    for st in G.ORDER:
        z=anomalies(paired(d,st)).rank(pct=True)
        for a,b in (("co2","ch4"),("co2","co"),("ch4","co")):
            if upper: joint=((z[a]>q)&(z[b]>q)).mean(); lam=joint/(1-q)
            else: joint=((z[a]<q)&(z[b]<q)).mean(); lam=joint/q
            rows.append(dict(station=st,pair=f"{a}-{b}",n_hours=len(z),joint_tail_pct=round(100*joint,2),
                             conditional_tail_probability=round(float(lam),3),independence_probability=0.05))
    return save(pd.DataFrame(rows),"aa_upper_tail.csv" if upper else "aa_lower_tail.csv")


def _mi(x,y,bins=8):
    xb=pd.qcut(x,bins,labels=False,duplicates='drop'); yb=pd.qcut(y,bins,labels=False,duplicates='drop')
    tab=pd.crosstab(xb,yb).values.astype(float); p=tab/tab.sum(); px=p.sum(1); py=p.sum(0)
    den=px[:,None]*py[None,:]; m=p>0
    return float(np.sum(p[m]*np.log(p[m]/den[m])))


def mutual_information(d):
    rows=[]
    for st in G.ORDER:
        z=anomalies(paired(d,st)); rng=np.random.default_rng(125+sum(map(ord,st)))
        take=rng.choice(len(z),min(len(z),12000),False); z=z.iloc[take]
        for a,b in (("co2","ch4"),("co2","co"),("ch4","co")):
            obs=_mi(z[a],z[b]); null=[_mi(z[a],rng.permutation(z[b].values)) for _ in range(100)]
            rows.append(dict(station=st,pair=f"{a}-{b}",n_hours=len(z),mi_nats=round(obs,3),
                             permutation_mean=round(float(np.mean(null)),3),excess_mi=round(obs-float(np.mean(null)),3)))
    return save(pd.DataFrame(rows),"aa_mutual_information.csv")


def rank_nonlinearity(d):
    rows=[]
    for st in G.ORDER:
        z=anomalies(paired(d,st))
        for a,b in (("co2","ch4"),("co2","co"),("ch4","co")):
            r=float(z[a].corr(z[b])); rho=float(spearmanr(z[a],z[b]).statistic); tau=float(kendalltau(z[a],z[b]).statistic)
            rows.append(dict(station=st,pair=f"{a}-{b}",pearson_r=round(r,3),spearman_rho=round(rho,3),kendall_tau=round(tau,3),rho_minus_r=round(rho-r,3)))
    return save(pd.DataFrame(rows),"aa_rank_nonlinearity.csv")


def _qreg(x,y,q):
    n=len(x); X=np.column_stack([np.ones(n),x]); c=np.r_[np.zeros(2),q*np.ones(n),(1-q)*np.ones(n)]
    A=np.c_[X,np.eye(n),-np.eye(n)]; b=y
    res=linprog(c,A_eq=A,b_eq=b,bounds=[(None,None)]*2+[(0,None)]*(2*n),method='highs')
    return float(res.x[1])


def quantile_slopes(d):
    rows=[]
    for st in G.ORDER:
        z=anomalies(paired(d,st)); rng=np.random.default_rng(128+sum(map(ord,st))); z=z.iloc[rng.choice(len(z),min(5000,len(z)),False)]
        for a,b in (("co2","ch4"),("co2","co")):
            vals={q:_qreg(z[a].values,z[b].values,q) for q in (.1,.5,.9)}
            rows.append(dict(station=st,response=b,predictor=a,n_hours=len(z),slope_q10=round(vals[.1],3),slope_q50=round(vals[.5],3),slope_q90=round(vals[.9],3),tail_asymmetry=round(vals[.9]-vals[.1],3)))
    return save(pd.DataFrame(rows),"aa_quantile_slopes.csv")


def js_daynight(d):
    rows=[]
    for st in G.ORDER:
        z=paired(d,st)
        for sp in SP:
            a=z.loc[z.hour_local<=5,sp].values; b=z.loc[z.hour_local.between(12,16),sp].values
            edges=np.quantile(np.r_[a,b],np.linspace(0,1,21)); edges=np.unique(edges)
            p=np.histogram(a,edges)[0]+.5; q=np.histogram(b,edges)[0]+.5; p=p/p.sum(); q=q/q.sum(); m=(p+q)/2
            js=.5*np.sum(p*np.log(p/m))+.5*np.sum(q*np.log(q/m))
            rows.append(dict(station=st,species=sp,n_night=len(a),n_afternoon=len(b),js_divergence_nats=round(float(js),3)))
    return save(pd.DataFrame(rows),"aa_daynight_js.csv")


def event_hour_entropy(d):
    rows=[]
    for st in G.ORDER:
        x=paired(d,st)
        for sp in SP:
            thr=x[sp].quantile(.90); h=x.loc[x[sp]>=thr,"hour_local"].value_counts().reindex(range(24),fill_value=0).values.astype(float); p=h/h.sum(); p=p[p>0]
            H=-np.sum(p*np.log(p))/np.log(24); rows.append(dict(station=st,species=sp,n_top_decile=int(h.sum()),normalised_hour_entropy=round(float(H),3),peak_hour=int(np.argmax(h)),peak_hour_share_pct=round(100*float(h.max()/h.sum()),1)))
    return save(pd.DataFrame(rows),"aa_hour_entropy.csv")


def variance_components(d):
    rows=[]
    for st in G.ORDER:
        x=paired(d,st)
        for sp in SP:
            y=x[sp].astype(float); grand=y.mean()
            # Sequential, explicitly ordered decomposition: hour first, then
            # month on the hour-residual.  This avoids double-counting because
            # hour and month are not orthogonal in an incomplete archive.
            hm=x.assign(_y=y).groupby('hour_local')['_y'].transform('mean'); r1=y-hm
            mm=x.assign(_r=r1).groupby('month')['_r'].transform('mean'); r2=r1-mm
            total=float(np.sum((y-grand)**2)); hour=float(np.sum((hm-grand)**2)); month=float(np.sum(mm**2)); resid=float(np.sum(r2**2))
            rows.append(dict(station=st,species=sp,total_variance=round(float(y.var()),3),hour_share_pct=round(100*hour/total,1),month_share_pct=round(100*month/total,1),residual_share_pct=round(100*resid/total,1)))
    return save(pd.DataFrame(rows),"aa_variance_components.csv")


def multiscale_variance(d):
    rows=[]
    for st in G.ORDER:
        x=paired(d,st).set_index('time_local')
        for sp in SP:
            s=x[sp].resample('h').median(); v1=float(s.var())
            for label,freq in [('daily','1D'),('weekly','7D'),('monthly','30D')]:
                v=float(s.resample(freq).mean().var()); rows.append(dict(station=st,species=sp,scale=label,variance=round(v,3),fraction_hourly_variance=round(v/v1,3)))
    return save(pd.DataFrame(rows),"aa_multiscale_variance.csv")


def allan_scaling(d):
    rows=[]
    for st in G.ORDER:
        x=paired(d,st).set_index('time_local')
        for sp in SP:
            s=x[sp].resample('h').median().dropna(); rec=[]
            for m in (1,3,6,12,24,72,168):
                a=s.resample(f'{m}h').mean().dropna().values
                av=.5*np.mean(np.diff(a)**2) if len(a)>2 else np.nan; rec.append((m,np.sqrt(av)))
            best=min(rec,key=lambda q:q[1] if np.isfinite(q[1]) else np.inf)
            rows.append(dict(station=st,species=sp,min_allan_hours=best[0],min_allan_deviation=round(float(best[1]),3),allan_1h=round(float(rec[0][1]),3),allan_24h=round(float(dict(rec)[24]),3)))
    return save(pd.DataFrame(rows),"aa_allan.csv")


def variance_trend(d):
    rows=[]
    for st in G.ORDER:
        x=paired(d,st); z=anomalies(x); z['year']=x.loc[z.index,'year'].values
        for sp in SP:
            a=z.groupby('year')[sp].apply(lambda v:np.median(np.abs(v-np.median(v)))*1.4826)
            sl,lo,hi=G.theil_sen(a.index.values,a.values)
            rows.append(dict(station=st,species=sp,n_years=len(a),scale_slope_per_year=round(float(sl),4) if np.isfinite(sl) else np.nan,ci_low=round(float(lo),4) if np.isfinite(lo) else np.nan,ci_high=round(float(hi),4) if np.isfinite(hi) else np.nan))
    return save(pd.DataFrame(rows),"aa_variance_trend.csv")


def variance_changepoint(d):
    rows=[]
    for st in G.ORDER:
        x=paired(d,st); z=anomalies(x); years=x.loc[z.index,'year'].values
        for sp in SP:
            vals=[]
            for y in sorted(set(years)):
                v=z.loc[years==y,sp]; vals.append((y,float(np.log(np.var(v)+1e-9))))
            if len(vals)<4: rows.append(dict(station=st,species=sp,n_years=len(vals),best_split_year=np.nan,variance_ratio_after_before=np.nan)); continue
            yy=np.array([q[0] for q in vals]); vv=np.array([q[1] for q in vals]); scores=[]
            for k in range(2,len(vv)-1): scores.append((np.sum((vv[:k]-vv[:k].mean())**2)+np.sum((vv[k:]-vv[k:].mean())**2),k))
            _,k=min(scores); ratio=np.exp(vv[k:].mean()-vv[:k].mean())
            rows.append(dict(station=st,species=sp,n_years=len(vals),best_split_year=int(yy[k]),variance_ratio_after_before=round(float(ratio),3)))
    return save(pd.DataFrame(rows),"aa_variance_changepoint.csv")


def covariance_stability(d):
    rows=[]
    for st in G.ORDER:
        x=paired(d,st); z=anomalies(x); z['year']=x.loc[z.index,'year'].values
        for a,b in (("co2","ch4"),("co2","co"),("ch4","co")):
            rr=z.groupby('year').apply(lambda g:g[a].corr(g[b]),include_groups=False).dropna()
            rows.append(dict(station=st,pair=f'{a}-{b}',n_years=len(rr),median_r=round(float(rr.median()),3),min_r=round(float(rr.min()),3),max_r=round(float(rr.max()),3),same_sign_fraction=round(float(max((rr>0).mean(),(rr<0).mean())),3)))
    return save(pd.DataFrame(rows),"aa_covariance_stability.csv")


def precision_network(d):
    rows=[]
    for st in G.ORDER:
        z=anomalies(paired(d,st)); C=np.corrcoef(z.values,rowvar=False); P=np.linalg.inv(C)
        for i,j in ((0,1),(0,2),(1,2)):
            pc=-P[i,j]/np.sqrt(P[i,i]*P[j,j]); rows.append(dict(station=st,pair=f'{SP[i]}-{SP[j]}',conditional_edge=round(float(pc),3),edge_strength=round(abs(float(pc)),3)))
    return save(pd.DataFrame(rows),"aa_precision_network.csv")


def event_synchrony(d):
    rows=[]
    for sp in SP:
        z=daily_anom(d,sp); hit=z.gt(z.quantile(.95))
        for i,a in enumerate(G.ORDER):
            for b in G.ORDER[i+1:]:
                valid=z[[a,b]].dropna().index; g=hit.loc[valid,[a,b]]; inter=(g[a]&g[b]).sum(); union=(g[a]|g[b]).sum();
                rows.append(dict(species=sp,station_a=a,station_b=b,n_days=len(g),joint_events=int(inter),jaccard=round(float(inter/union),3) if union else np.nan))
    return save(pd.DataFrame(rows),"aa_event_synchrony.csv")


def propagation_lag(d):
    rows=[]
    for sp in SP:
        z=daily_anom(d,sp)
        for i,a in enumerate(G.ORDER):
            for b in G.ORDER[i+1:]:
                vals=[]
                for lag in range(-7,8):
                    g=pd.concat([z[a],z[b].shift(lag)],axis=1).dropna(); vals.append((lag,float(g.iloc[:,0].corr(g.iloc[:,1])),len(g)))
                lag,r,n=max(vals,key=lambda q:abs(q[1]) if np.isfinite(q[1]) else -1)
                rows.append(dict(species=sp,station_a=a,station_b=b,best_lag_days=lag,best_r=round(r,3),n_days=n,zero_lag_r=round(dict((x,y) for x,y,_ in vals)[0],3)))
    return save(pd.DataFrame(rows),"aa_propagation_lag.csv")


def station_effective_dimension(d):
    rows=[]
    for sp in SP:
        z=daily_anom(d,sp).dropna(how='all'); C=z.corr(min_periods=60).fillna(0).values; np.fill_diagonal(C,1); val=np.linalg.eigvalsh(C); pr=val.sum()**2/np.sum(val**2)
        rows.append(dict(species=sp,n_days=len(z),network_participation_ratio=round(float(pr),3),pc1_variance_pct=round(100*float(val.max()/val.sum()),1)))
    return save(pd.DataFrame(rows),"aa_network_dimension.csv")


def canonical_pairs(d):
    rows=[]; tabs={st:pd.concat([daily_anom(d,s)[st].rename(s) for s in SP],axis=1) for st in G.ORDER}
    for i,a in enumerate(G.ORDER):
        for b in G.ORDER[i+1:]:
            g=tabs[a].join(tabs[b],lsuffix='_a',rsuffix='_b').dropna()
            if len(g)<30: continue
            X=g.iloc[:,:3].values; Y=g.iloc[:,3:].values; X=(X-X.mean(0))/X.std(0); Y=(Y-Y.mean(0))/Y.std(0)
            Cxx=np.cov(X,rowvar=False)+.05*np.eye(3); Cyy=np.cov(Y,rowvar=False)+.05*np.eye(3); Cxy=np.cov(X.T,Y.T)[:3,3:]
            M=np.linalg.solve(Cxx,Cxy)@np.linalg.solve(Cyy,Cxy.T); rho=np.sqrt(max(0,np.linalg.eigvals(M).real.max()))
            rows.append(dict(station_a=a,station_b=b,n_days=len(g),regularised_canonical_r=round(float(min(rho,1)),3)))
    return save(pd.DataFrame(rows),"aa_canonical.csv")


def species_reconstruction(d):
    rows=[]
    for st in G.ORDER:
        x=anomalies(paired(d,st)); years=paired(d,st).loc[x.index,'year']
        for target in SP:
            pred=[]; obs=[]
            for y in sorted(years.unique()):
                tr=years!=y; te=years==y
                if tr.sum()<100 or te.sum()<20: continue
                cols=[s for s in SP if s!=target]; X=np.column_stack([np.ones(tr.sum()),x.loc[tr,cols]]); beta=np.linalg.lstsq(X,x.loc[tr,target],rcond=None)[0]
                pred.extend(np.column_stack([np.ones(te.sum()),x.loc[te,cols]])@beta); obs.extend(x.loc[te,target])
            obs=np.array(obs); pred=np.array(pred); r2=1-np.sum((obs-pred)**2)/np.sum((obs-obs.mean())**2) if len(obs)>2 else np.nan
            rows.append(dict(station=st,target=target,n_test=len(obs),leave_year_out_r2=round(float(r2),3) if np.isfinite(r2) else np.nan,rmse=round(float(np.sqrt(np.mean((obs-pred)**2))),3) if len(obs) else np.nan))
    return save(pd.DataFrame(rows),"aa_species_reconstruction.csv")


def station_classification(d):
    rows=[]; feats=[]
    for st in G.ORDER:
        x=paired(d,st); z=anomalies(x); q=z.copy(); q['station']=st; q['monthkey']=x.loc[z.index,'time_local'].dt.to_period('M').astype(str).values; feats.append(q)
    z=pd.concat(feats); rng=np.random.default_rng(143); z=z.iloc[rng.choice(len(z),min(50000,len(z)),False)]
    truth=[]; prediction=[]
    for mk,g in z.groupby('monthkey'):
        tr=z[z.monthkey!=mk]; cent=tr.groupby('station')[list(SP)].mean(); X=g[list(SP)].values
        dist=((X[:,None,:]-cent.values[None,:,:])**2).sum(2); pred=cent.index.values[np.argmin(dist,axis=1)]
        truth.extend(g.station.values); prediction.extend(pred)
    truth=np.asarray(truth); prediction=np.asarray(prediction); correct=truth==prediction
    tab=pd.crosstab(pd.Series(truth),pd.Series(prediction)).values.astype(float); p=tab/tab.sum(); pt=p.sum(1); pp=p.sum(0); den=pt[:,None]*pp[None,:]; m=p>0
    mi_bits=float(np.sum(p[m]*np.log2(p[m]/den[m])))
    rows.append(dict(n_hours=len(correct),leave_month_out_accuracy=round(float(np.mean(correct)),3),chance_accuracy=0.2,mutual_information_bits=round(mi_bits,3)))
    return save(pd.DataFrame(rows),"aa_station_classification.csv")


def centroid_separation(d):
    rows=[]; data={}
    for st in G.ORDER:
        x=paired(d,st); vals=[]
        for _,g in x.groupby('date'):
            if len(g)<12: continue
            vals.append([g.co2.median(),g.ch4.median(),g.co.median()])
        data[st]=np.asarray(vals)
    allv=np.vstack(list(data.values())); scale=np.median(np.abs(allv-np.median(allv,axis=0)),axis=0)*1.4826
    for i,a in enumerate(G.ORDER):
        for b in G.ORDER[i+1:]:
            delta=(np.median(data[a],axis=0)-np.median(data[b],axis=0))/scale; rows.append(dict(station_a=a,station_b=b,robust_distance=round(float(np.sqrt(np.sum(delta**2))),3),largest_contributor=SP[int(np.argmax(delta**2))]))
    return save(pd.DataFrame(rows),"aa_centroid_separation.csv")


def burstiness(d):
    rows=[]
    for st in G.ORDER:
        x=paired(d,st)
        for sp in SP:
            daily=x.groupby('date')[sp].median(); hit=daily[daily>=daily.quantile(.95)].index.sort_values(); dt=pd.Series(hit).diff().dt.days.dropna().values
            if len(dt)<2: B=np.nan
            else: B=(np.std(dt)-np.mean(dt))/(np.std(dt)+np.mean(dt))
            rows.append(dict(station=st,species=sp,n_events=len(hit),mean_interval_days=round(float(np.mean(dt)),1) if len(dt) else np.nan,burstiness=round(float(B),3) if np.isfinite(B) else np.nan))
    return save(pd.DataFrame(rows),"aa_burstiness.csv")


def extremal_index(d):
    rows=[]
    for st in G.ORDER:
        x=paired(d,st)
        for sp in SP:
            s=x.set_index('time_local')[sp]; hit=s>=s.quantile(.99); starts=hit & ~hit.shift(1,fill_value=False); theta=starts.sum()/hit.sum()
            rows.append(dict(station=st,species=sp,n_extreme_hours=int(hit.sum()),n_runs=int(starts.sum()),runs_extremal_index=round(float(theta),3),mean_run_hours=round(float(1/theta),2)))
    return save(pd.DataFrame(rows),"aa_extremal_index.csv")


def recovery_composite(d):
    rows=[]
    for st in G.ORDER:
        x=paired(d,st); daily=x.groupby('date')[list(SP)].median()
        for sp in SP:
            s=daily[sp]; bg=s.rolling(31,center=True,min_periods=15).quantile(.2); a=(s-bg).dropna(); peaks=a[a>=a.quantile(.95)]
            comp=[]
            for lag in range(8):
                vals=[a.get(t+pd.Timedelta(days=lag),np.nan)/v for t,v in peaks.items() if v>0]; comp.append(float(np.nanmedian(vals)))
            half=next((i for i,v in enumerate(comp) if v<=.5),np.nan)
            rows.append(dict(station=st,species=sp,n_events=len(peaks),half_recovery_days=half,day1=round(comp[1],3),day3=round(comp[3],3),day7=round(comp[7],3)))
    return save(pd.DataFrame(rows),"aa_recovery_composite.csv")


def decay_model(d):
    comp=recovery_composite(d); rows=[]
    for _,r in comp.iterrows():
        y=np.array([1,r.day1,r.day3,r.day7],float); t=np.array([0,1,3,7],float); m=np.isfinite(y)&(y>0); y=y[m]; t=t[m]
        be=np.linalg.lstsq(np.column_stack([np.ones(len(t)),t]),np.log(y),rcond=None)[0]; pe=np.exp(np.column_stack([np.ones(len(t)),t])@be); aic_e=len(t)*np.log(np.mean((y-pe)**2)+1e-12)+4
        bp=np.linalg.lstsq(np.column_stack([np.ones(len(t)),np.log1p(t)]),np.log(y),rcond=None)[0]; pp=np.exp(np.column_stack([np.ones(len(t)),np.log1p(t)])@bp); aic_p=len(t)*np.log(np.mean((y-pp)**2)+1e-12)+4
        rows.append(dict(station=r.station,species=r.species,preferred_model='exponential' if aic_e<aic_p else 'power_law',delta_aic=round(abs(float(aic_e-aic_p)),2),exponential_efold_days=round(float(-1/be[1]),2) if be[1]<0 else np.nan))
    return save(pd.DataFrame(rows),"aa_decay_model.csv")


def hysteresis_amplitude(d):
    h=pd.read_csv(OUT/'q_hysteresis.csv'); rows=[]
    # Recreate daily areas for CO2-CH4 and compare absolute area with daily range.
    for st in G.ORDER:
        x=paired(d,st); vals=[]
        for day,g in x.groupby('date'):
            q=g.groupby('hour_local')[['co2','ch4']].median().sort_index()
            if len(q)<18: continue
            zz=(q-q.mean())/q.std(ddof=0); xx,yy=zz.co2.values,zz.ch4.values; area=.5*np.sum(xx*np.roll(yy,-1)-np.roll(xx,-1)*yy)
            vals.append((abs(area),float(q.co2.max()-q.co2.min())))
        a=np.asarray(vals); rho=float(spearmanr(a[:,0],a[:,1]).statistic)
        rows.append(dict(station=st,n_days=len(a),spearman_abs_area_vs_co2_range=round(rho,3),median_abs_area=round(float(np.median(a[:,0])),3)))
    return save(pd.DataFrame(rows),"aa_hysteresis_amplitude.csv")


def main():
    d=pd.read_pickle(OUT/'all.pkl')
    pca_structure(d); effective_dimension(d); partial_dependence(d); tail_dependence(d,True); tail_dependence(d,False)
    mutual_information(d); rank_nonlinearity(d); quantile_slopes(d); js_daynight(d); event_hour_entropy(d)
    variance_components(d); multiscale_variance(d); allan_scaling(d); variance_trend(d); variance_changepoint(d)
    covariance_stability(d); precision_network(d); event_synchrony(d); propagation_lag(d); station_effective_dimension(d)
    canonical_pairs(d); species_reconstruction(d); station_classification(d); centroid_separation(d); burstiness(d)
    extremal_index(d); recovery_composite(d); decay_model(d); hysteresis_amplitude(d)
    # Finding 150: concise synthesis table of the strongest nonlinear diagnostic.
    mi=pd.read_csv(OUT/'aa_mutual_information.csv'); pc=pd.read_csv(OUT/'aa_partial.csv')
    out=mi.merge(pc[['station','pair','partial_r']],on=['station','pair'],how='left')
    save(out.sort_values('excess_mi',ascending=False), 'aa_nonlinear_synthesis.csv')


if __name__=='__main__':
    main()
