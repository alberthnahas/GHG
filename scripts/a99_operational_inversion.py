#!/usr/bin/env python3
"""Operational inversion for carbon dioxide and methane, with a readiness verdict.

Both earlier studies reached the same place: at the scale of a single afternoon
the posterior does not predict better than the boundary field with a fitted
offset and trend, at either tower, for either gas. That is a statement about a
daily concentration prediction. It is not the quantity a regional inversion
estimates, and it is not by itself a reason to ship nothing.

This module changes four things and then reports, every run, whether the data
constrained anything:

  measured transport error. The earlier error model scaled one tuned number by
    the total prior increment. Here the shape comes from the ensemble: the seed
    spread already recorded for every component at every receptor. Only its
    amplitude is calibrated, so an hour on which the seeds disagree is
    downweighted against an hour on which they agree.

  a reparameterised biosphere. Gross uptake and respiration correlate at 0.91 to
    0.94 across the afternoon receptors, so fitting both inflates the posterior
    without adding information. The pair is rotated into the net flux, which the
    data constrain, and the contrast, which they do not and which is held under
    a tight Gaussian prior.

  an aggregation scale. A regional inversion estimates a flux over a period, so
    the fit and the score are offered daily, weekly and monthly. Nothing is
    cherry-picked: every scale is reported with a block bootstrap interval, and
    a scale with too few independent bins is declared unresolved rather than
    quoted.

  information diagnostics. Degrees of freedom for signal, the posterior to prior
    uncertainty ratio per parameter, and chi-square consistency say what the
    observations actually informed. A deployment reads the verdict, not the
    multipliers.

Stages
  fit         one gas at one aggregation scale, with diagnostics
  campaign    both gases at every scale, writing the readiness verdict
"""
from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd

import a84_bkt_jmb_two_receptor as T
import a89_bkt_jmb_co2 as C
import a90_bkt_jmb_co2_improved as I
import a91_bkt_jmb_co2_experiments as X
import a96_cross_validated_scoring as S

TABLES = T.TABLES
OUT = T.ROOT / "outputs/operational"
SCALES = {"daily": "D", "weekly": "W", "monthly": "M"}
MIN_BINS = 8                      # fewer independent bins than this cannot resolve a difference
TRANSPORT_SCAN = (.1, .25, .5, .75, 1., 1.5, 2., 3., 5., 8., 12.)
CONTRAST_PRIOR = .25              # the unconstrained biosphere direction, held down deliberately
DOFS_GATE, CHI_GATE = 1.0, (0.5, 2.0)


class Gas:
    """Everything that differs between the two gases, in one place."""

    def __init__(self, name: str, unit: str, observed: str, components: dict[str, str],
                 measurement: float, local: float, background: float, multiplier_factor: float,
                 offset_prior: float, trend_prior: float):
        self.name, self.unit, self.observed = name, unit, observed
        self.components = components          # parameter name -> column in the frame
        self.measurement, self.local, self.background = measurement, local, background
        self.multiplier_factor = multiplier_factor
        self.offset_prior, self.trend_prior = offset_prior, trend_prior


FOLU_LABEL = ""          # "" leaves land use out; "full" adds the FOLU response as its own component

CO2 = Gas("co2", "ppm", "co2_afternoon_mean",
          {"fossil_near": "fossil_near_ppm", "fossil_far": "fossil_far_ppm",
           "bio_net_BKT": "bio_net_BKT_ppm", "bio_net_JMB": "bio_net_JMB_ppm"},
          measurement=C.MEASUREMENT_PPM, local=C.LOCAL_DAY_PPM, background=C.BACKGROUND_PPM,
          multiplier_factor=C.MULTIPLIER_PRIOR_FACTOR, offset_prior=C.OFFSET_PRIOR_PPM, trend_prior=C.TREND_PRIOR_PPM)

CH4 = Gas("ch4", "ppb", "ch4",
          {"anthro_near": "anthro_near_ppb", "anthro_far": "anthro_far_ppb",
           "wetlands": "wetlands_ppb", "fire": "fire_ppb"},
          measurement=5., local=20., background=10.,
          multiplier_factor=2., offset_prior=20., trend_prior=10.)

GASES = {"co2": CO2, "ch4": CH4}


# ------------------------------------------------------------------ frames

BIOSPHERE = ""          # "" is the diagnostic prior; "_hybrid" is the CarbonTracker hybrid (a104)
BIOSPHERE_PERIOD = {"": "all", "_hybrid": "2023"}   # the hybrid exists for the 2023 window


def co2_components() -> dict[str, str]:
    """The carbon dioxide components, with land use included when its response exists."""
    components = dict(CO2.components)
    if FOLU_LABEL:
        components["folu_drainage"] = "folu_3b1_ppm"
    return components


def co2_frame() -> pd.DataFrame:
    """Afternoon receptors, with the biosphere pair rotated into net and contrast."""
    f = X.receptor_frame(BIOSPHERE, None, BIOSPHERE_PERIOD.get(BIOSPHERE, "all")).copy()
    for code in ("BKT", "JMB"):
        member = f.station.eq(code).to_numpy().astype(float)
        # net is what the data see; contrast is the direction they cannot separate
        f[f"bio_net_{code}_ppm"] = (f.gpp_ppm + f.resp_ppm) * member
        f[f"bio_contrast_{code}_ppm"] = (f.gpp_ppm - f.resp_ppm) * member
    if FOLU_LABEL:
        # land use is the largest Indonesian term and EDGAR carries none of it;
        # the response comes from the FOLU proxy convolved with the same footprints
        folu = pd.read_csv(TABLES / f"co2_folu_response_{FOLU_LABEL}.csv", parse_dates=["time_utc"])
        columns = [c for c in folu.columns if c.endswith("_ppm")]
        f = f.merge(folu[["station", "time_utc"] + columns], on=["station", "time_utc"], how="left")
        for column in columns:
            f[column] = f[column].fillna(0.0)
    f["base"] = f.background_ppm + f.ocean_ppm + f.fire_ppm
    f["observed"] = f.co2_afternoon_mean
    seeds = ["gpp_ppm_seed_sd", "resp_ppm_seed_sd", "fossil_near_ppm_seed_sd", "background_ppm_seed_sd"]
    f["ensemble_sd"] = np.sqrt(sum(f[c].fillna(0.) ** 2 for c in seeds if c in f.columns))
    return f.reset_index(drop=True)


LOCAL_INVENTORY = ""     # "" is EDGAR; a ledger label such as "primap" rescales it to reported totals


def localise_anthropogenic(frame: pd.DataFrame, label: str) -> pd.DataFrame:
    """Rescale the anthropogenic response to a reported national inventory.

    The operator is linear in the flux, so a per-sector factor can be applied to
    the per-sector responses already stored rather than by re-running the
    footprints. The near and far columns are then rescaled in the proportion the
    sectors imply, which assumes the sector mix beyond 500 km resembles the mix
    within it. That assumption is worth stating because it is not exactly true;
    it is second order against factors that range from 0.09 to 1.70.
    """
    ledger = pd.read_csv(T.ROOT / f"outputs/inventory/local_inventory_ch4_2022_{label}_ledger.csv")
    ledger = ledger[ledger.pattern.eq("EDGAR")]
    influence = T.TABLES.parent / "inventory/province_influence_ch4_2022.csv"
    provincial = (ledger.region_level == "province").any()
    if provincial and influence.exists():
        # A provincial ledger holds one factor per province per sector. The towers see
        # provinces unevenly, so each sector's factor is the influence-weighted mean of
        # its provincial factors, per station. That assumes a province's influence share
        # is similar across sectors at a given tower, which is worth stating.
        weights = pd.read_csv(influence)
        weights["weight"] = weights.percent / 100.0
        factor = {}
        for station in weights.station.unique():
            share = weights[weights.station.eq(station)].set_index("province").weight
            for sectors, group in ledger.groupby("edgar_sectors"):
                g = group.set_index("region").factor
                common = share.index.intersection(g.index)
                if common.empty:
                    continue
                effective = float((share[common] * g[common]).sum() / share[common].sum())
                for sector in str(sectors).split(";"):
                    factor[(station, f"CH4_{sector}")] = effective
    else:
        factor = {}
        for sectors, value in zip(ledger.edgar_sectors, ledger.factor):
            for sector in str(sectors).split(";"):
                for station in ("BKT", "JMB"):
                    factor[(station, f"CH4_{sector}")] = float(value)
    sectors = pd.read_csv(TABLES / "sector_responses_base.csv", parse_dates=["time_utc"])
    keys = list(zip(sectors.station, sectors.source))
    sectors = sectors.assign(_factor=[factor.get(k, np.nan) for k in keys]).dropna(subset=["_factor"])
    sectors["scaled"] = sectors.prior_enhancement_ppb * sectors._factor
    totals = sectors.groupby(["station", "time_utc"]).agg(
        before=("prior_enhancement_ppb", "sum"), after=("scaled", "sum")).reset_index()
    frame = frame.merge(totals, on=["station", "time_utc"], how="left")
    ratio = (frame.after / frame.before.where(frame.before > 0)).fillna(1.0).to_numpy()
    for column in ("anthro_near_ppb", "anthro_far_ppb"):
        frame[column] = frame[column] * ratio
    return frame.drop(columns=["before", "after"])


def ch4_frame() -> pd.DataFrame:
    """The screened methane receptors: transport usable, Jambi nights excluded."""
    f = pd.read_csv(TABLES / "operator_base.csv", parse_dates=["time_utc"])
    f = f[f.transport_usable & ~(f.station.eq("JMB") & f.time_utc.dt.hour.eq(18))].copy()
    if LOCAL_INVENTORY:
        f = localise_anthropogenic(f, LOCAL_INVENTORY)
    f["base"] = f.background_ppb + f.termites_ppb + f.geological_ppb - f.soil_uptake_ppb
    f["observed"] = f.ch4
    seeds = [c for c in f.columns if c.endswith("_ppb_seed_sd")]
    f["ensemble_sd"] = np.sqrt(sum(f[c].fillna(0.) ** 2 for c in seeds))
    return f.reset_index(drop=True)


FRAMES = {"co2": co2_frame, "ch4": ch4_frame}


def aggregate(frame: pd.DataFrame, gas: Gas, scale: str) -> pd.DataFrame:
    """Bin means per station. A bin holding one receptor is not a mean and is dropped."""
    if scale == "daily":
        out = frame.copy()
        out["bin"] = out.time_utc.dt.normalize()
        out["count"] = 1
        return out
    columns = ["base", "observed", "ensemble_sd"] + list((co2_components() if gas.name == "co2" else gas.components).values()) + \
              [c for c in frame.columns if c.startswith("bio_contrast")]
    columns = [c for c in dict.fromkeys(columns) if c in frame.columns]
    out = frame.copy()
    out["bin"] = out.time_utc.dt.to_period(SCALES[scale]).dt.start_time
    grouped = out.groupby(["station", "bin"])
    table = grouped[columns].mean()
    table["count"] = grouped.size()
    table["time_utc"] = grouped.time_utc.mean()
    table = table[table["count"] >= 2].reset_index()
    # the mean of n receptors has a smaller transport error than one receptor
    table["ensemble_sd"] = table.ensemble_sd / np.sqrt(table["count"])
    return table


# ------------------------------------------------------------------ design

def design(frame: pd.DataFrame, gas: Gas):
    """Response columns, nuisance columns and the fixed baseline."""
    columns = list((co2_components() if gas.name == "co2" else gas.components).values())
    k = frame[columns].to_numpy(float)
    stations = sorted(frame.station.unique())
    midpoint = frame.time_utc.min() + (frame.time_utc.max() - frame.time_utc.min()) / 2
    columns, names, sd = [], [], []
    for code in stations:
        member = frame.station.eq(code).to_numpy(float)
        columns += [member, member * (frame.time_utc - midpoint).dt.total_seconds().to_numpy() / (28 * 86400)]
        names += [f"offset_{code}", f"trend_{code}"]
        sd += [gas.offset_prior, gas.trend_prior]
    for column in [c for c in frame.columns if c.startswith("bio_contrast")]:
        columns.append(frame[column].to_numpy(float))
        names.append(column.replace("_ppm", ""))
        sd.append(CONTRAST_PRIOR)
    return k, np.column_stack(columns), frame.base.to_numpy(float), names, np.asarray(sd)


def covariance(frame: pd.DataFrame, gas: Gas, kappa: float) -> np.ndarray:
    """Measurement, local mismatch, a correlated background term, and the measured transport spread.

    A bin mean of several receptors carries less independent error than one
    receptor, so the measurement and local-mismatch terms are divided by the
    number averaged, as the transport spread already is. The background term is
    not: a boundary bias is common to the hours in a bin and does not average
    away, which is exactly why it has to be fitted rather than assumed.
    """
    n = len(frame)
    r = np.zeros((n, n))
    transport = kappa * frame.ensemble_sd.to_numpy(float)
    count = frame["count"].to_numpy(float) if "count" in frame.columns else np.ones(n)
    for code in frame.station.unique():
        m = frame.station.eq(code).to_numpy()
        hours = (frame.time_utc[m] - frame.time_utc[m].min()).dt.total_seconds().to_numpy() / 3600
        lag = np.abs(hours[:, None] - hours[None, :])
        block = np.outer(transport[m], transport[m]) * np.exp(-lag / 24)
        block += gas.background ** 2 * np.exp(-lag / 72)
        block += np.diag((gas.measurement ** 2 + gas.local ** 2) / count[m])
        r[np.ix_(m, m)] = block
    return r


def solve(frame: pd.DataFrame, gas: Gas, kappa: float, train: np.ndarray | None = None, sample: bool = False):
    """Fit the inversion, by Markov chain when the answer is reported.

    A MAP fit with a Laplace covariance is about a thousand times faster, and its
    medians agree with the sampler to within about 7%. Its intervals do not: in
    log space the Gaussian approximation puts the upper bound 37 to 44% too high,
    which flows straight into the uncertainty ratio and the degrees of freedom and
    makes the data look less informative than they are. So the reported fit is
    sampled, and the approximation is kept only inside the cross-validation loop,
    where nothing but the mode is used.
    """
    k, b, base, names, nuisance_sd = design(frame, gas)
    y = frame.observed.to_numpy(float) - base
    prior_sd = np.r_[np.repeat(np.log(gas.multiplier_factor), k.shape[1]), nuisance_sd]
    r = covariance(frame, gas, kappa)
    train = np.ones(len(frame), bool) if train is None else train
    problem = C.SignedInverseProblem(k[train], b[train], y[train], r[np.ix_(train, train)], prior_sd)
    theta, _, _ = problem.fit()
    if sample:
        from bkt_methane_inverse import chain_diagnostics
        for draws, thin in ((12000, 3), (48000, 12)):
            chains, _ = problem.sample(draws=draws, thin=thin)
            rhat, ess = chain_diagnostics(chains)
            if np.max(rhat) <= 1.01 and np.min(ess) >= 1000:
                break
        else:
            raise RuntimeError(f"chains did not converge: R-hat {np.max(rhat):.3f}, ESS {np.min(ess):.0f}")
        draws_flat = chains.reshape(-1, problem.ndim)
        theta = np.median(draws_flat, axis=0)
        posterior_cov = np.cov(draws_flat, rowvar=False)
        quantiles = np.quantile(draws_flat, [.025, .975], axis=0)
        convergence = dict(rhat=float(np.max(rhat)), ess=float(np.min(ess)), draws=int(len(draws_flat)))
    else:
        jac = problem.jacobian(theta)
        posterior_cov = np.linalg.inv(jac.T @ jac)
        quantiles = np.vstack([theta - 1.96 * np.sqrt(np.diag(posterior_cov)),
                               theta + 1.96 * np.sqrt(np.diag(posterior_cov))])
        convergence = dict(rhat=float("nan"), ess=float("nan"), draws=0)
    residual = problem.residual(theta)[:int(train.sum())]
    chi = float(residual @ residual / train.sum())
    ns = k.shape[1]
    prediction = base + k @ np.exp(theta[:ns]) + b @ theta[ns:]
    nuisance_only = base + b @ S.ridge(b, y, r, train, nuisance_sd)
    return dict(theta=theta, names=list(co2_components() if gas.name == "co2" else gas.components) + names, posterior_cov=posterior_cov, prior_sd=prior_sd,
                chi=chi, nsource=ns, prediction=prediction, background_only=nuisance_only, response=k,
                problem=problem, quantiles=quantiles, convergence=convergence)


def calibrate(frame: pd.DataFrame, gas: Gas) -> float:
    """Amplitude of the measured transport error, set so the training chi-square is one."""
    scan = [(kappa, solve(frame, gas, kappa)["chi"]) for kappa in TRANSPORT_SCAN]
    kappas = np.array([k for k, _ in scan]); chis = np.array([c for _, c in scan])
    if chis.min() > 1:
        return float(kappas[-1])
    if chis.max() < 1:
        return float(kappas[0])
    return float(np.interp(1.0, chis[::-1], kappas[::-1]))


# ------------------------------------------------------------ diagnostics

def diagnostics(fit: dict) -> dict:
    """What the observations actually informed, independent of what the numbers say."""
    ns = fit["nsource"]
    posterior = np.sqrt(np.diag(fit["posterior_cov"]))[:ns]
    prior = fit["prior_sd"][:ns]
    ratio = posterior / prior
    dofs = float(np.sum(1 - ratio ** 2))                  # Gaussian DOFS in the source block
    return dict(degrees_of_freedom=dofs, reduced_chi_square=fit["chi"],
                uncertainty_ratio={name: float(v) for name, v in zip(fit["names"][:ns], ratio)},
                informed_parameters=int(np.sum(ratio < 0.8)))


def cross_validate(frame: pd.DataFrame, gas: Gas, kappa: float) -> pd.DataFrame:
    """Leave-one-bin-out: refit without each bin and predict it."""
    bins = frame["bin"].to_numpy()
    rows = []
    for one in pd.unique(bins):
        test = bins == one
        if test.all() or (~test).sum() < 6:
            continue
        fit = solve(frame, gas, kappa, train=~test)
        for index in np.flatnonzero(test):
            rows.append(dict(station=frame.station.iloc[index], time_utc=frame.time_utc.iloc[index],
                             observed=frame.observed.iloc[index], posterior=fit["prediction"][index],
                             background_only=fit["background_only"][index]))
    return pd.DataFrame(rows)


def skill(predictions: pd.DataFrame, gas: Gas) -> pd.DataFrame:
    if predictions.empty:
        return pd.DataFrame()
    table = S.date_block_bootstrap(predictions.assign(variant=gas.name), "posterior", "background_only", "observed")
    for code in table.station.unique():
        g = predictions[predictions.station.eq(code)]
        for model in ("posterior", "background_only"):
            table.loc[table.station.eq(code), f"rmse_{model}"] = float(np.sqrt(((g[model] - g.observed) ** 2).mean()))
    return table


def verdict(gas: Gas, scale: str, bins: int, diag: dict, table: pd.DataFrame) -> dict:
    """The operational gate. A deployment reads this, not the multipliers."""
    resolved, better = [], []
    for row in table.itertuples():
        if row.ci_hi < 0:
            resolved.append(row.station); better.append(row.station)
        elif row.ci_lo > 0:
            resolved.append(row.station)
    gates = {
        "enough_independent_bins": bins >= MIN_BINS,
        "chi_square_consistent": CHI_GATE[0] <= diag["reduced_chi_square"] <= CHI_GATE[1],
        "data_informed_a_parameter": diag["degrees_of_freedom"] >= DOFS_GATE,
        "beats_background_somewhere": bool(better),
    }
    if all(gates.values()):
        status = "operational"
    elif gates["enough_independent_bins"] and gates["data_informed_a_parameter"]:
        status = "diagnostic: informed but not better than the boundary null"
    elif not gates["enough_independent_bins"]:
        status = f"unresolved: {bins} independent bins, fewer than the {MIN_BINS} required"
    else:
        status = "diagnostic: the observations did not inform a flux parameter"
    return dict(gas=gas.name, scale=scale, bins=int(bins), status=status, gates=gates,
                degrees_of_freedom=round(diag["degrees_of_freedom"], 3),
                reduced_chi_square=round(diag["reduced_chi_square"], 3),
                informed_parameters=diag["informed_parameters"],
                resolved_at=sorted(set(resolved)), better_at=sorted(set(better)))


# ---------------------------------------------------------------- stages

def run(gas_name: str, scale: str, write: bool = True) -> dict:
    gas = GASES[gas_name]
    frame = aggregate(FRAMES[gas_name](), gas, scale)
    bins = int(frame["bin"].nunique())
    kappa = calibrate(frame, gas)
    fit = solve(frame, gas, kappa, sample=True)     # the reported fit is sampled, not approximated
    diag = diagnostics(fit)
    predictions = cross_validate(frame, gas, kappa)
    table = skill(predictions, gas)
    ns = fit["nsource"]
    posterior = np.sqrt(np.diag(fit["posterior_cov"]))[:ns]
    parameters = pd.DataFrame(dict(
        gas=gas.name, scale=scale, parameter=fit["names"][:ns],
        multiplier=np.exp(fit["theta"][:ns]),
        q025=np.exp(fit["quantiles"][0][:ns]), q975=np.exp(fit["quantiles"][1][:ns]),
        uncertainty_ratio=posterior / fit["prior_sd"][:ns]))
    result = verdict(gas, scale, bins, diag, table)
    result["transport_amplitude"] = round(kappa, 3)
    result["receptors"] = int(len(frame))
    result["biosphere"] = BIOSPHERE or "diagnostic"
    result["inventory"] = LOCAL_INVENTORY or "EDGAR"
    result["folu"] = FOLU_LABEL or "excluded"
    # the prior is the response at unit multipliers; fit["prediction"] is the posterior,
    # and calling that a prior would overstate how good the untouched inventory is
    prior = fit["response"].sum(axis=1) + frame.base.to_numpy()
    result["prior_rmse"] = round(float(np.sqrt(((prior - frame.observed) ** 2).mean())), 3)
    result["posterior_rmse_in_sample"] = round(float(np.sqrt(((fit["prediction"] - frame.observed) ** 2).mean())), 3)
    result["convergence"] = fit["convergence"]
    if write:
        OUT.mkdir(parents=True, exist_ok=True)
        tag = f"{gas.name}{BIOSPHERE}{'_' + LOCAL_INVENTORY if LOCAL_INVENTORY else ''}"
        tag += f"_folu{FOLU_LABEL}" if FOLU_LABEL else ""
        tag += f"_{scale}"
        parameters.to_csv(OUT / f"inversion_{tag}_parameters.csv", index=False)
        if not table.empty:
            table.to_csv(OUT / f"inversion_{tag}_skill.csv", index=False)
        if not predictions.empty:
            predictions.to_csv(OUT / f"inversion_{tag}_predictions.csv", index=False)
    print(f"{gas.name} {scale}: {len(frame)} receptors in {bins} bins, transport amplitude {kappa:.2f}, "
          f"chi2 {diag['reduced_chi_square']:.2f}, DOFS {diag['degrees_of_freedom']:.2f} -> {result['status']}", flush=True)
    if not table.empty:
        for row in table.itertuples():
            print(f"    {row.station}: posterior {row.rmse_posterior:.2f} against background {row.rmse_background_only:.2f} "
                  f"{gas.unit}, difference {row.rmse_difference:+.2f} ({row.ci_lo:+.2f} to {row.ci_hi:+.2f})", flush=True)
    return result


def error_budget() -> pd.DataFrame:
    """What the source signal has to compete with, term by term.

    This is the diagnostic that explains the others. If the signal the sources
    make at the receptor is not comfortably larger than the error it arrives
    through, no prior and no aggregation can recover it, and the inversion will
    keep losing to a fitted constant however well it is built.
    """
    rows = []
    for gas in GASES.values():
        frame = aggregate(FRAMES[gas.name](), gas, "daily")
        kappa = calibrate(frame, gas)
        signal = float(frame[list((co2_components() if gas.name == "co2" else gas.components).values())].sum(axis=1).std())
        transport = float((kappa * frame.ensemble_sd).mean())
        independent = float(np.hypot(gas.measurement, gas.local))
        total = float(np.sqrt(transport ** 2 + independent ** 2 + gas.background ** 2))
        rows.append(dict(gas=gas.name, unit=gas.unit, source_signal_sd=signal,
                         transport_error=transport, transport_amplitude=kappa,
                         measurement_and_local=independent, background=gas.background,
                         total_error=total, signal_to_error=signal / total if total else np.nan,
                         dominant_term=max((transport, "transport"), (independent, "measurement and local"),
                                           (gas.background, "background"))[1]))
    table = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUT / "error_budget.csv", index=False)
    for row in table.itertuples():
        print(f"{row.gas}: signal {row.source_signal_sd:.2f} {row.unit} against total error {row.total_error:.2f}, "
              f"ratio {row.signal_to_error:.2f}; dominant term is {row.dominant_term} "
              f"({row.transport_error:.2f}, amplitude {row.transport_amplitude:.2f})", flush=True)
    return table


# The configurations the operational campaign runs: each gas with the prior it
# should use, and the reference it is measured against.
CONFIGURATIONS = [
    dict(gas="co2", prior="global inventory, diagnostic biosphere", biosphere="", inventory="", folu=""),
    dict(gas="co2", prior="hybrid biosphere", biosphere="_hybrid", inventory="", folu=""),
    dict(gas="co2", prior="with land use included", biosphere="", inventory="", folu="full"),
    dict(gas="ch4", prior="global inventory", biosphere="", inventory="", folu=""),
    dict(gas="ch4", prior="national reported inventory", biosphere="", inventory="primap", folu=""),
    dict(gas="ch4", prior="provincial reported inventory", biosphere="", inventory="provincial", folu=""),
]


def campaign() -> None:
    global BIOSPHERE, LOCAL_INVENTORY, FOLU_LABEL
    verdicts = []
    for configuration in CONFIGURATIONS:
        BIOSPHERE = configuration["biosphere"]
        LOCAL_INVENTORY = configuration["inventory"]
        FOLU_LABEL = configuration.get("folu", "")
        print(f"\n--- {configuration['gas']}: {configuration['prior']} ---", flush=True)
        for scale in SCALES:
            try:
                verdict = run(configuration["gas"], scale)
                verdict["prior"] = configuration["prior"]
                verdicts.append(verdict)
            except Exception as error:  # noqa: BLE001 - a scale that cannot be fitted is reported, not fatal
                verdicts.append(dict(gas=configuration["gas"], prior=configuration["prior"], scale=scale,
                                     status=f"failed: {type(error).__name__}: {error}"))
                print(f"  {scale}: FAILED {type(error).__name__}: {error}", flush=True)
    BIOSPHERE, LOCAL_INVENTORY, FOLU_LABEL = "", "", ""
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "inversion_readiness.json").write_text(json.dumps(verdicts, indent=2) + "\n")
    operational = [v for v in verdicts if v.get("status") == "operational"]
    print(f"\nwrote {OUT / 'inversion_readiness.json'}")
    print(f"operational combinations: {len(operational)} of {len(verdicts)}"
          + ("" if not operational else ": " + ", ".join(f"{v['gas']} {v['scale']}" for v in operational)), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["fit", "campaign", "budget"])
    parser.add_argument("--gas", choices=sorted(GASES), default="co2")
    parser.add_argument("--scale", choices=sorted(SCALES), default="daily")
    parser.add_argument("--biosphere", default="", choices=sorted(BIOSPHERE_PERIOD),
                        help="which carbon dioxide biosphere prior to use")
    parser.add_argument("--local-inventory", default="", help="ledger label to rescale the methane prior, e.g. primap")
    parser.add_argument("--folu", default="", help="label of the FOLU response to include for carbon dioxide, e.g. full")
    a = parser.parse_args()
    global BIOSPHERE, LOCAL_INVENTORY, FOLU_LABEL
    BIOSPHERE = a.biosphere
    LOCAL_INVENTORY = a.local_inventory
    FOLU_LABEL = a.folu
    if a.stage == "budget":
        error_budget()
    elif a.stage == "fit":
        run(a.gas, a.scale)
    else:
        campaign()


if __name__ == "__main__":
    main()
