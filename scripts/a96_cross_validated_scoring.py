#!/usr/bin/env python3
"""Cross-validated scoring for the two-receptor inversions, methane first.

The a84 methane cases are evaluated on withheld days: nine receptor hours at BKT
and three at Jambi. The carbon dioxide study showed what a sample that size can
do, so this module applies the same scoring the CO2 work ended up using, to the
methane inversion and to anything else built on the same design:

  leave-one-date-out cross-validation, refitting without each date and
    predicting it, so every date is used once as a test;
  a background-only baseline refitted on the same training rows;
  a paired bootstrap over whole dates of the difference in RMSE.

The bootstrap is the generic one used by a91 for carbon dioxide; a91 delegates
to it here so both gases resample dates the same way.

Stages
  ch4        score the methane cases and write the three tables
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

import a84_bkt_jmb_two_receptor as T
from bkt_methane_inverse import InverseProblem

TABLES = T.TABLES
BOOTSTRAP_SEED, BOOTSTRAP_REPS = 20260915, 5000
CASES = {   # label: (rows eligible for this case, components)
    "joint": (lambda f: np.ones(len(f), bool), T.COMPONENTS),
    "joint_screened": (lambda f: ~jambi_night(f), T.COMPONENTS),
    "joint_screened_sector": (lambda f: ~jambi_night(f), T.SECTOR_COMPONENTS),
    "bkt_only": (lambda f: f.station.eq("BKT").to_numpy(), T.COMPONENTS),
    "jmb_day": (lambda f: f.station.eq("JMB").to_numpy() & ~jambi_night(f), T.COMPONENTS),
}


def jambi_night(frame: pd.DataFrame) -> np.ndarray:
    return (frame.station.eq("JMB") & frame.time_utc.dt.hour.eq(18)).to_numpy()


def date_block_bootstrap(predictions: pd.DataFrame, posterior: str, baseline: str, observed: str,
                         keys: tuple[str, ...] = ("variant", "station"), reps: int = BOOTSTRAP_REPS,
                         seed: int = BOOTSTRAP_SEED) -> pd.DataFrame:
    """Paired bootstrap over dates of the RMSE difference, posterior minus baseline.

    Dates are resampled whole, so hours on the same day stay together; the number
    of distinct dates is the effective sample size reported with each interval.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for key, g in predictions.groupby(list(keys)):
        g = g.assign(date=g.time_utc.dt.normalize())
        dates = g.date.unique()
        e_post = (g[posterior] - g[observed]).to_numpy(); e_plain = (g[baseline] - g[observed]).to_numpy()
        index = [np.flatnonzero(g.date.to_numpy() == d) for d in dates]
        diffs = np.empty(reps)
        for i in range(reps):
            take = np.concatenate([index[j] for j in rng.integers(0, len(dates), len(dates))])
            diffs[i] = np.sqrt(np.mean(e_post[take] ** 2)) - np.sqrt(np.mean(e_plain[take] ** 2))
        observed_difference = np.sqrt(np.mean(e_post ** 2)) - np.sqrt(np.mean(e_plain ** 2))
        rows.append(dict(zip(keys, key if isinstance(key, tuple) else (key,)))
                    | dict(hours=len(g), dates=len(dates), rmse_difference=float(observed_difference),
                           ci_lo=float(np.percentile(diffs, 2.5)), ci_hi=float(np.percentile(diffs, 97.5)),
                           fraction_posterior_better=float((diffs < 0).mean())))
    return pd.DataFrame(rows)


def ridge(b: np.ndarray, y: np.ndarray, r: np.ndarray, train: np.ndarray, prior_sd: np.ndarray) -> np.ndarray:
    """Generalized least squares for the nuisance columns alone, with their Gaussian priors."""
    from scipy.linalg import solve_triangular
    chol = np.linalg.cholesky(r[np.ix_(train, train)])
    bw = solve_triangular(chol, b[train], lower=True)
    yw = solve_triangular(chol, y[train], lower=True)
    return np.linalg.solve(bw.T @ bw + np.diag(1 / prior_sd ** 2), bw.T @ yw)


def transport_fractions() -> dict[str, float]:
    """The fraction each a84 case tuned to; cases with too few rows to be scored there are tuned here."""
    evaluation = pd.read_csv(TABLES / "inversion_evaluation.csv")
    return evaluation.groupby("case").transport_fraction.first().to_dict()


def tune(frame: pd.DataFrame, components: list[str]) -> float:
    """Reduced chi-square of one on the full case, the a84 rule, for a case a84 did not score."""
    import a75_bkt_revised_inversion as r75
    k, b, base, _ = T.design(frame, components)
    y = frame.ch4.to_numpy() - base
    sd = np.r_[np.repeat(np.log(2.), k.shape[1]), np.tile([20., 10.], b.shape[1] // 2)]
    everything = np.ones(len(frame), bool)
    scan, chi = [], []
    for t in (.05, .1, .15, .2, .25, .3, .4, .5, .6, .8, 1.0):
        problem = InverseProblem(k, b, y, T.covariance(frame, k, t), sd)
        scan.append(t); chi.append(r75.reduced_chi_square(problem, int(everything.sum())))
    chi = np.array(chi); scan = np.array(scan)
    return float(scan[0] if chi.max() < 1 else scan[-1] if chi.min() > 1 else np.interp(1.0, chi[::-1], scan[::-1]))


def cross_validate(label: str, frame: pd.DataFrame, components: list[str], transport: float) -> tuple[pd.DataFrame, list[dict]]:
    """Leave-one-date-out MAP predictions for the posterior, background-only and prior models."""
    k, b, base, _ = T.design(frame, components)
    y = frame.ch4.to_numpy() - base
    sd = np.r_[np.repeat(np.log(2.), k.shape[1]), np.tile([20., 10.], b.shape[1] // 2)]
    nuisance_sd = sd[k.shape[1]:]
    r = T.covariance(frame, k, transport)
    dates = frame.time_utc.dt.normalize().to_numpy()
    pred = {m: np.full(len(frame), np.nan) for m in ("posterior", "background_only", "prior_inventory")}
    pred["prior_inventory"] = base + k.sum(axis=1)
    for date in np.unique(dates):
        test = dates == date; train = ~test
        if train.sum() < k.shape[1] + b.shape[1] + 2:
            raise ValueError(f"{label}: too few training rows to withhold {date}")
        theta, _, _ = InverseProblem(k[train], b[train], y[train], r[np.ix_(train, train)], sd).fit()
        ns = k.shape[1]
        pred["posterior"][test] = base[test] + k[test] @ np.exp(theta[:ns]) + b[test] @ theta[ns:]
        pred["background_only"][test] = base[test] + b[test] @ ridge(b, y, r, train, nuisance_sd)
    observed = frame.ch4.to_numpy()
    rows = []
    for code in sorted(frame.station.unique()):
        m = frame.station.eq(code).to_numpy()
        for model, values in pred.items():
            error = values[m] - observed[m]
            rows.append(dict(variant=label, station=code, scope="leave_one_date_out", model=model, n=int(m.sum()),
                             rmse_ppb=float(np.sqrt(np.mean(error ** 2))), bias_ppb=float(error.mean()),
                             correlation=float(np.corrcoef(observed[m], values[m])[0, 1])))
    table = pd.DataFrame(dict(variant=label, station=frame.station.to_numpy(), time_utc=frame.time_utc.to_numpy(),
                              observed_ppb=observed, **{f"{m}_ppb": v for m, v in pred.items()}))
    return table, rows


def ch4() -> None:
    frame = pd.read_csv(TABLES / "operator_base.csv", parse_dates=["time_utc"])
    frame = frame[frame.transport_usable].reset_index(drop=True)
    fractions = transport_fractions()
    predictions, skill = [], []
    for label, (eligible, components) in CASES.items():
        rows = eligible(frame)
        case = frame[rows].reset_index(drop=True)
        transport = fractions.get(label) or tune(case, components)
        table, scored = cross_validate(label, case, components, transport)
        dates = case.time_utc.dt.normalize().nunique()
        print(f"{label}: {len(case)} hours, {dates} dates, transport {transport:.2f}", flush=True)
        predictions.append(table); skill += scored
    predictions = pd.concat(predictions, ignore_index=True)
    boot = date_block_bootstrap(predictions, "posterior_ppb", "background_only_ppb", "observed_ppb")
    predictions.to_csv(TABLES / "ch4_cv_predictions.csv", index=False)
    pd.DataFrame(skill).to_csv(TABLES / "ch4_cv_skill.csv", index=False)
    boot.to_csv(TABLES / "ch4_cv_bootstrap.csv", index=False)
    pd.set_option("display.width", 200)
    print(pd.DataFrame(skill).pivot_table(index=["variant", "station"], columns="model", values="rmse_ppb").round(1).to_string())
    print(boot.round(2).to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["ch4"])
    parser.parse_args()
    ch4()


if __name__ == "__main__":
    main()
