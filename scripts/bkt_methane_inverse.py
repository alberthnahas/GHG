"""Small-state methane inversion with positive emissions and correlated errors.

The prior is Gaussian in log emission multipliers and linear in background
nuisance terms. Posterior sampling, not a positivity-clipped linear solution,
provides uncertainty. All concentration inputs and error scales are in ppb.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy.linalg import solve_triangular
from scipy.optimize import least_squares
from scipy.stats import norm, rankdata


@dataclass
class InverseProblem:
    response: np.ndarray
    background_design: np.ndarray
    enhancement: np.ndarray
    error_covariance: np.ndarray
    prior_sd: np.ndarray

    def __post_init__(self):
        self.response=np.asarray(self.response,float)
        self.background_design=np.asarray(self.background_design,float)
        self.enhancement=np.asarray(self.enhancement,float)
        self.error_covariance=np.asarray(self.error_covariance,float)
        self.prior_sd=np.asarray(self.prior_sd,float)
        self.nsource=self.response.shape[1]
        self.ndim=self.nsource+self.background_design.shape[1]
        n=len(self.enhancement)
        if self.response.shape[0]!=n or self.background_design.shape[0]!=n:
            raise ValueError("Observation dimensions differ")
        if self.error_covariance.shape!=(n,n) or self.prior_sd.shape!=(self.ndim,):
            raise ValueError("Covariance/prior dimensions differ")
        for array in (self.response,self.background_design,self.enhancement,self.error_covariance,self.prior_sd):
            if not np.isfinite(array).all(): raise ValueError("Nonfinite inversion input")
        if (self.response<0).any() or (self.prior_sd<=0).any(): raise ValueError("Invalid source sensitivity/prior")
        if not np.allclose(self.error_covariance,self.error_covariance.T): raise ValueError("Nonsymmetric error covariance")
        self.chol=np.linalg.cholesky(self.error_covariance)
        self.kw=solve_triangular(self.chol,self.response,lower=True)
        self.bw=solve_triangular(self.chol,self.background_design,lower=True)
        self.yw=solve_triangular(self.chol,self.enhancement,lower=True)

    def residual(self,theta):
        source=np.exp(theta[:self.nsource])
        data=self.kw@source+self.bw@theta[self.nsource:]-self.yw
        return np.r_[data,theta/self.prior_sd]

    def jacobian(self,theta):
        return np.vstack([np.column_stack([self.kw*np.exp(theta[:self.nsource]),self.bw]),
                          np.diag(1/self.prior_sd)])

    def predict(self,theta):
        theta=np.asarray(theta)
        return np.exp(theta[...,:self.nsource])@self.response.T+theta[...,self.nsource:]@self.background_design.T

    def logp(self,theta):
        if not np.isfinite(theta).all() or np.max(np.abs(theta[:self.nsource]),initial=0)>30:
            return -np.inf
        r=self.residual(theta)
        return -.5*float(r@r)

    def fit(self):
        result=least_squares(self.residual,np.zeros(self.ndim),jac=self.jacobian,
                             xtol=1e-11,ftol=1e-11,gtol=1e-9,max_nfev=3000)
        if not result.success: raise RuntimeError(result.message)
        # Gauss-Newton local curvature is used only as a sampling proposal and
        # an explicitly approximate information diagnostic, not final intervals.
        covariance=np.linalg.inv(result.jac.T@result.jac)
        return result.x,covariance,result

    def sample(self,seed=20190909,chains=4,burn=6000,draws=12000,thin=3):
        center,cov,_=self.fit()
        root=np.linalg.cholesky(cov)
        rng=np.random.default_rng(seed)
        states=center+rng.normal(size=(chains,self.ndim))@root.T
        lp=np.array([self.logp(s) for s in states])
        scales=np.full(chains,2.38/np.sqrt(self.ndim))
        accepted=np.zeros(chains); window=np.zeros(chains)
        output=np.empty((chains,draws,self.ndim))
        for step in range(burn+draws*thin):
            for c in range(chains):
                proposal=states[c]+scales[c]*(root@rng.normal(size=self.ndim))
                proposed=self.logp(proposal)
                if np.log(rng.random()) < proposed-lp[c]:
                    states[c]=proposal;lp[c]=proposed
                    window[c]+=1
                    if step>=burn: accepted[c]+=1
            if step<burn and (step+1)%200==0:
                scales*=np.exp(np.clip(window/200-.25,-.15,.15));window[:]=0
            if step>=burn and (step-burn)%thin==0:
                output[:,(step-burn)//thin,:]=states
        return output,accepted/(draws*thin)


def chain_diagnostics(chains):
    """Rank-normalized split R-hat and conservative autocorrelation ESS.

    ESS uses Geyer initial-positive paired autocorrelation sums within each
    chain. R-hat also checks folded rank deviations to detect scale mismatch.
    """
    chains=np.asarray(chains,float)
    m,n,p=chains.shape
    if n<20 or m<2: raise ValueError("Insufficient chains/draws")
    n2=n//2
    split=np.concatenate([chains[:,:n2],chains[:,-n2:]],axis=0)
    def rhat(values):
        w=np.var(values,axis=1,ddof=1).mean(axis=0)
        b=n2*np.var(values.mean(axis=1),axis=0,ddof=1)
        return np.sqrt(((n2-1)/n2*w+b/n2)/w)
    ranks=np.empty_like(split);folded=np.empty_like(split)
    for j in range(p):
        flat=split[:,:,j].ravel();size=len(flat)
        ranks[:,:,j]=norm.ppf((rankdata(flat)-.375)/(size+.25)).reshape(split.shape[:2])
        dev=np.abs(flat-np.median(flat))
        folded[:,:,j]=norm.ppf((rankdata(dev)-.375)/(size+.25)).reshape(split.shape[:2])
    rh=np.maximum(rhat(ranks),rhat(folded))
    ess=[]
    for j in range(p):
        estimates=[]
        for c in range(m):
            x=chains[c,:,j]-chains[c,:,j].mean()
            fft=np.fft.rfft(x,n=2*n)
            ac=np.fft.irfft(fft*fft.conj(),n=2*n)[:n]
            ac=ac/ac[0]
            pairs=ac[1:n-1:2]+ac[2:n:2]
            stop=np.flatnonzero(pairs<=0)
            pairs=pairs[:stop[0]] if len(stop) else pairs
            pairs=np.minimum.accumulate(pairs)
            estimates.append(n/max(1.,1+2*pairs.sum()))
        ess.append(sum(estimates))
    return rh,np.asarray(ess)


def correlated_error(times,prior_enhancement,night,transport_fraction=.5,
                     background_sd=10.,representativeness_scale=1.,transport_correlation_hours=24.):
    """Predeclared working uncertainty, not independently measured BKT errors.

    5 ppb measurement/calibration allowance; 20/40 ppb day/night local mismatch;
    24-hour correlated transport error and 72-hour background variability.
    The separate fitted offset/trend account for coherent boundary uncertainty.
    """
    hours=np.asarray(times,dtype="datetime64[s]").astype("int64")/3600
    lag=np.abs(hours[:,None]-hours[None,:])
    transport=transport_fraction*np.asarray(prior_enhancement)
    local=np.where(night,40.,20.)*representativeness_scale
    covariance=np.diag(5.**2+local**2)
    if transport_correlation_hours<=0:raise ValueError("Correlation time must be positive")
    covariance+=np.outer(transport,transport)*np.exp(-lag/transport_correlation_hours)
    covariance+=background_sd**2*np.exp(-lag/72)
    return covariance
