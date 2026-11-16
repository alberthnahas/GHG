#!/usr/bin/env python3
"""Train-only, temporal validation and local batch service for both gases.

An emission inversion and a concentration predictor are different products.
This service selects a predictor on training folds, retains conditional source
diagnostics, and never turns concentration skill into validated absolute flux.
No scheduler or remote publication is installed by this command.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np
import pandas as pd

import a99_operational_inversion as V
import a112_operational_response as R
from a89_bkt_jmb_co2 import SignedInverseProblem

OUT = R.OUT
PURGE_DAYS = 3
BLOCK_DAYS = 7
MIN_TRAIN_STATION = 5
MIN_INNER_STATION = 3
BOOTSTRAP_REPS = 4000


@dataclass(frozen=True)
class Candidate:
    name: str
    sources: str = "none"  # none, fixed, bulk
    inventory: str = "EDGAR"
    state_days: float = 0.0
    trend: bool = False
    discrepancy_scale: float = 1.0
    multiplier_prior_factor: float = 2.0


CANDIDATES = (
    Candidate("boundary_offset"),
    Candidate("boundary_trend", trend=True),
    Candidate("boundary_state", state_days=7),
    Candidate("fixed_prior_state", sources="fixed", state_days=7),
    Candidate("bulk_prior_state", sources="bulk", state_days=7),
    Candidate("national_bulk_state", sources="bulk", inventory="primap", state_days=7),
    Candidate("provincial_bulk_state", sources="bulk", inventory="provincial", state_days=7),
)


def frames() -> dict[str, pd.DataFrame]:
    """No centered CH4 proxy or observation-derived cross-gas predictor is used."""
    tables = V.TABLES
    early = pd.read_csv(tables / "co2_operator_base.csv", parse_dates=["time_utc"])
    early = early.merge(pd.read_csv(tables / "co2_diagnostic_operator.csv", parse_dates=["time_utc"]),
                        on=["station", "time_utc"], validate="one_to_one")
    early = early.merge(pd.read_csv(tables / "co2_afternoon_observations.csv", parse_dates=["time_utc"]),
                        on=["station", "time_utc"], validate="one_to_one")
    later = pd.read_csv(tables / "co2_operator_base_2024.csv", parse_dates=["time_utc"])
    later = later.merge(pd.read_csv(tables / "co2_afternoon_observations_2024.csv", parse_dates=["time_utc"]),
                        on=["station", "time_utc"], validate="one_to_one")
    co2 = pd.concat([early, later], ignore_index=True)
    co2 = co2[co2.transport_usable & co2.time_utc.dt.hour.eq(6) & co2.PBLH.ge(R.MIN_PBLH) & co2.co2_afternoon_mean.notna()].copy()
    co2["observed"] = co2.co2_afternoon_mean
    co2["base"] = co2.background_ppm + co2.ocean_ppm + co2.fire_ppm
    # Only the published component seed spreads are available for 2024.
    # Preserve this limitation explicitly rather than silently dropping 2023
    # spreads when concatenating years with different schemas.
    seed_columns = ["gpp_ppm_seed_sd", "resp_ppm_seed_sd", "fossil_near_ppm_seed_sd", "background_ppm_seed_sd"]
    co2["seed_terms_available"] = co2[seed_columns].notna().sum(axis=1)
    co2["ensemble_sd"] = np.sqrt(co2[seed_columns].fillna(0).pow(2).sum(axis=1))
    for code in ("BKT", "JMB"):
        member = co2.station.eq(code).to_numpy(float)
        co2[f"bio_net_{code}_ppm"] = (co2.gpp_ppm + co2.resp_ppm) * member
        co2[f"bio_contrast_{code}_ppm"] = (co2.gpp_ppm - co2.resp_ppm) * member
    co2 = co2.sort_values(["station", "time_utc"])
    co2["gas"] = "co2"
    co2["period"] = co2.time_utc.dt.year.astype(str)
    co2["source_total"] = co2.fossil_near_ppm + co2.fossil_far_ppm + co2.gpp_ppm + co2.resp_ppm
    ch4 = pd.read_csv(OUT / "ch4_receptors.csv", parse_dates=["time_utc"])
    response = pd.read_csv(OUT / "ch4_exact_responses.csv", parse_dates=["time_utc"])
    for label in R.LABELS:
        part = response[response.inventory.eq(label)].drop(columns="inventory")
        part = part.rename(columns={c: f"{c}_{label}" for c in part if c not in ("station", "time_utc")})
        ch4 = ch4.merge(part, on=["station", "time_utc"], validate="one_to_one")
    ch4["base"] = ch4.background_ppb + ch4.termites_ppb + ch4.geological_ppb - ch4.soil_uptake_ppb
    ch4["period"] = ch4.time_utc.dt.year.astype(str)
    ch4["gas"] = "ch4"
    ch4["ensemble_sd"] = np.sqrt(ch4.anthro_total_seed_sd_EDGAR ** 2 + ch4.wetlands_ppb_seed_sd ** 2 + ch4.fire_ppb_seed_sd ** 2 + ch4.background_ppb_seed_sd ** 2)
    ch4["source_total"] = ch4.anthro_near_ppb + ch4.anthro_far_ppb + ch4.wetlands_ppb + ch4.fire_ppb
    for gas, frame in (("co2", co2), ("ch4", ch4)):
        if frame.duplicated(["station", "time_utc"]).any():
            raise ValueError(f"Duplicate receptors: {gas}")
        if not np.isfinite(frame[["observed", "base", "ensemble_sd"]]).all().all():
            raise ValueError(f"Missing required model input: {gas}")
        if not frame.PBLH.ge(R.MIN_PBLH).all() or not frame.time_utc.dt.hour.eq(6).all():
            raise ValueError(f"Non-afternoon or shallow-layer receptor: {gas}")
    return {"co2": co2.reset_index(drop=True), "ch4": ch4.reset_index(drop=True)}


def components(frame: pd.DataFrame, gas: str, inventory: str = "EDGAR") -> tuple[np.ndarray, list[str]]:
    if gas == "co2":
        values = np.column_stack([frame.fossil_near_ppm + frame.fossil_far_ppm, frame.bio_net_BKT_ppm, frame.bio_net_JMB_ppm])
        names = ["fossil", "net_biosphere_BKT", "net_biosphere_JMB"]
        if "folu_3b1_ppm" in frame:
            values = np.column_stack([values, frame.folu_3b1_ppm])
            names.append("peat_drainage")
        return values, names
    return np.column_stack([frame[f"anthro_near_ppb_{inventory}"] + frame[f"anthro_far_ppb_{inventory}"],
                            frame.wetlands_ppb, frame.fire_ppb]), ["anthropogenic", "wetlands", "fire"]


def admissible(frame: pd.DataFrame, train: np.ndarray, test: np.ndarray, minimum: int) -> bool:
    """Do not extrapolate an unseen station/regime as if it had been fitted."""
    if not test.any():
        return False
    for station, period in frame.loc[test, ["station", "period"]].drop_duplicates().itertuples(index=False):
        if (train & frame.station.eq(station) & frame.period.eq(period)).sum() < minimum:
            return False
    return True


def nuisance(frame: pd.DataFrame, train: np.ndarray, trend: bool) -> tuple[np.ndarray, list[str]]:
    columns, names = [], []
    for station, period in frame.loc[train, ["station", "period"]].drop_duplicates().itertuples(index=False):
        member = (frame.station.eq(station) & frame.period.eq(period)).to_numpy(float)
        columns.append(member); names.append(f"offset_{station}_{period}")
        if trend:
            midpoint = frame.loc[train & member.astype(bool), "time_utc"].mean()
            columns.append(member * (frame.time_utc - midpoint).dt.total_seconds().to_numpy() / (28 * 86400))
            names.append(f"trend_{station}_{period}")
    return np.column_stack(columns), names


def fit_predict(frame: pd.DataFrame, gas_name: str, candidate: Candidate, train: np.ndarray) -> dict:
    """All empirical scales and offsets depend exclusively on training rows.

    A correlated discrepancy state is explicitly *not* an emission adjustment.
    Gaussian conditioning predicts this state from training residuals; its
    variance remains in prediction uncertainty. This is a conditional working
    error model, not an independently measured transport covariance.
    """
    gas = V.GASES[gas_name]
    b, nuisance_names = nuisance(frame, train, candidate.trend)
    all_k, source_names = components(frame, gas_name, candidate.inventory)
    base = frame.base.to_numpy().copy()
    if candidate.sources == "fixed":
        base += all_k.sum(axis=1)
    k = all_k if candidate.sources == "bulk" else np.zeros((len(frame), 0))
    names = source_names if candidate.sources == "bulk" else []
    y = frame.observed.to_numpy() - base
    ns = k.shape[1]
    independent = gas.measurement ** 2 + gas.local ** 2
    diagonal = independent + frame.ensemble_sd.to_numpy() ** 2
    state = np.zeros((len(frame), len(frame)))
    amplitude = {}
    for station, period in frame.loc[train, ["station", "period"]].drop_duplicates().itertuples(index=False):
        members = (frame.station.eq(station) & frame.period.eq(period)).to_numpy()
        residual = y[train & members]
        # Robust training scale. Fix the timescale a priori; no test-dependent scan.
        sigma = candidate.discrepancy_scale * max(gas.background, 1.4826 * np.median(np.abs(residual - np.median(residual))))
        amplitude[f"{station}_{period}"] = float(sigma)
        if candidate.state_days:
            stamps = frame.time_utc[members]
            days = (stamps - stamps.iloc[0]).dt.total_seconds().to_numpy() / 86400
            state[np.ix_(members, members)] = sigma ** 2 * np.exp(-np.abs(days[:, None] - days[None, :]) / candidate.state_days)
    covariance = np.diag(diagonal) + state
    nuisance_sd = np.array([max(gas.offset_prior, 10. if gas_name == "co2" else 100.) if n.startswith("offset") else gas.trend_prior for n in nuisance_names])
    prior_sd = np.r_[np.repeat(np.log(candidate.multiplier_prior_factor), ns), nuisance_sd]
    problem = SignedInverseProblem(k[train], b[train], y[train], covariance[np.ix_(train, train)], prior_sd)
    theta, post_cov, _ = problem.fit()
    mean = base + k @ np.exp(theta[:ns]) + b @ theta[ns:]
    residual = frame.observed.to_numpy()[train] - mean[train]
    cross = state[:, train]
    weights = np.linalg.solve(covariance[np.ix_(train, train)], residual)
    prediction = mean + cross @ weights
    # Delta-method parameter uncertainty plus Gaussian conditional discrepancy.
    jac = np.column_stack([k * np.exp(theta[:ns]), b])
    conditional_jac = jac - cross @ np.linalg.solve(covariance[np.ix_(train, train)], jac[train])
    variance = np.diag(covariance) - np.einsum("ij,ji->i", cross, np.linalg.solve(covariance[np.ix_(train, train)], cross.T))
    variance += np.einsum("ij,jk,ik->i", conditional_jac, post_cov, conditional_jac)
    data_jac = problem.jacobian(theta)[:train.sum()]
    dofs_all = float(np.trace(data_jac @ post_cov @ data_jac.T))
    chi = float(problem.residual(theta)[:train.sum()] @ problem.residual(theta)[:train.sum()] / max(1., train.sum() - dofs_all))
    source_dofs = float(np.sum(1 - np.diag(post_cov)[:ns] / prior_sd[:ns] ** 2))
    return dict(prediction=prediction, sd=np.sqrt(np.maximum(variance, 0)), theta=theta, posterior_cov=post_cov,
                source_names=names, source_dofs=source_dofs, chi=chi, train_count=int(train.sum()), amplitude=amplitude,
                problem=problem, prior_sd=prior_sd, nuisance_names=nuisance_names,
                working_covariance=covariance)


def folds(frame: pd.DataFrame, train_pool: np.ndarray | None = None, prospective: bool = False,
          minimum: int = MIN_TRAIN_STATION):
    """Calendar-week outer tests, whole-network blocks; 72 h purge both sides.

    Past-only replay allows earlier observations up to, but not on, the tested
    date. The block protocol is a harder extrapolation test with a 72 h embargo.
    """
    pool = np.ones(len(frame), bool) if train_pool is None else train_pool
    if prospective:
        for date in frame.loc[pool, "time_utc"].dt.normalize().sort_values().unique():
            test = pool & frame.time_utc.dt.normalize().eq(date).to_numpy()
            train = pool & (frame.time_utc < pd.Timestamp(date)).to_numpy()
            if admissible(frame, train, test, minimum):
                yield str(pd.Timestamp(date).date()), train, test
    else:
        blocks = frame.time_utc.dt.to_period("W-SUN").dt.start_time
        for start in sorted(blocks[pool].unique()):
            end = pd.Timestamp(start) + pd.Timedelta(days=BLOCK_DAYS)
            test = pool & blocks.eq(start).to_numpy()
            train = pool & ((frame.time_utc < pd.Timestamp(start) - pd.Timedelta(days=PURGE_DAYS)) | (frame.time_utc >= end + pd.Timedelta(days=PURGE_DAYS))).to_numpy()
            if admissible(frame, train, test, minimum):
                yield str(pd.Timestamp(start).date()), train, test


def candidates_for(gas: str) -> tuple[Candidate, ...]:
    return CANDIDATES if gas == "ch4" else CANDIDATES[:5]


def select(frame: pd.DataFrame, gas: str, train_pool: np.ndarray) -> tuple[Candidate, list[dict]]:
    """Nested selection using only outer-training observations, not outer tests."""
    inner = list(folds(frame, train_pool, minimum=MIN_INNER_STATION))
    # At most three deterministic, evenly spaced inner blocks, common to every candidate.
    if len(inner) > 3:
        inner = [inner[i] for i in np.linspace(0, len(inner) - 1, 3).round().astype(int)]
    if not inner:
        return CANDIDATES[0], []
    rows = []
    for candidate in candidates_for(gas):
        errors, normalized = [], {station: [] for station in frame.station.unique()}
        for label, train, test in inner:
            fit = fit_predict(frame, gas, candidate, train)
            errors.extend((fit["prediction"][test] - frame.observed.to_numpy()[test]) ** 2)
            for station in normalized:
                rows_station = test & frame.station.eq(station).to_numpy()
                normalized[station].extend(np.abs(fit["prediction"][rows_station] - frame.observed.to_numpy()[rows_station]) / fit["sd"][rows_station])
        row = dict(candidate=candidate.name, inner_mse=float(np.mean(errors)), inner_receptors=len(errors))
        for station, values in normalized.items():
            # Training-only empirical expansion, not a claim of exchangeable
            # conformal coverage for autocorrelated observations.
            row[f"interval_factor_{station}"] = max(1., float(np.quantile(values, .95, method="higher")) / 1.96) if values else 1.
            row[f"interval_calibration_n_{station}"] = len(values)
        rows.append(row)
    # Deterministic order resolves exact ties; no full-record winner is substituted.
    winner = min(rows, key=lambda r: r["inner_mse"])["candidate"]
    return next(c for c in candidates_for(gas) if c.name == winner), rows


def legacy_prediction(frame: pd.DataFrame, gas: str, train: np.ndarray, inventory: str = "EDGAR") -> np.ndarray:
    """Previous model, refitted and recalibrated on this identical training set."""
    legacy = frame.copy()
    if gas == "co2":
        # Reproduce the previous published frame's shared-year seed columns.
        legacy["ensemble_sd"] = np.sqrt(legacy.gpp_ppm_seed_sd.fillna(0) ** 2 + legacy.resp_ppm_seed_sd.fillna(0) ** 2)
    if gas == "ch4":
        # Original frame stores the old single-hour value; evaluation uses the
        # same current afternoon means, so QC improvement cannot fake the gain.
        legacy["observed"] = frame.observed
        if inventory != "EDGAR":
            legacy = V.localise_anthropogenic(legacy, inventory)
    legacy["count"] = 1
    kappa = V.calibrate(legacy.loc[train].reset_index(drop=True), V.GASES[gas])
    return V.solve(legacy, V.GASES[gas], kappa, train=train)["prediction"]


def compare_previous_priors(source_frames: dict[str, pd.DataFrame], predictions: pd.DataFrame) -> None:
    """Additional matched comparison to all previously used methane priors.

    The previous-source selector uses inner training blocks, just as the new
    selector does. No oracle minimum over outer-test scores is called a model.
    Existing CO2 hybrid/FOLU cases cover different periods and remain explicit
    sensitivities, rather than being silently filled into missing periods.
    """
    frame = source_frames["ch4"]
    rows = []
    for prospective in (False, True):
        protocol = "past_only" if prospective else "purged_week"
        for label, train, test in folds(frame, prospective=prospective):
            inner = list(folds(frame, train, minimum=MIN_INNER_STATION))
            if len(inner) > 3:
                inner = [inner[i] for i in np.linspace(0, len(inner) - 1, 3).round().astype(int)]
            scores = {}
            for inventory in R.LABELS:
                errors = []
                for _, inner_train, inner_test in inner:
                    pred = legacy_prediction(frame, "ch4", inner_train, inventory)
                    errors.extend((pred[inner_test] - frame.observed.to_numpy()[inner_test]) ** 2)
                scores[inventory] = float(np.mean(errors)) if errors else float("inf")
            selected = min(scores, key=scores.get) if inner else "EDGAR"
            values = {inventory: legacy_prediction(frame, "ch4", train, inventory) for inventory in R.LABELS}
            for index in np.flatnonzero(test):
                row = dict(gas="ch4", protocol=protocol, fold=label, station=frame.station.iloc[index], time_utc=frame.time_utc.iloc[index],
                           observed=frame.observed.iloc[index], previous_selected=values[selected][index], previous_inventory=selected)
                row.update({f"previous_{inventory}": value[index] for inventory, value in values.items()})
                rows.append(row)
    table = pd.DataFrame(rows).merge(predictions[predictions.gas.eq("ch4")][["protocol", "station", "time_utc", "selected"]],
                                   on=["protocol", "station", "time_utc"], validate="one_to_one")
    table.to_csv(OUT / "previous_prior_predictions.csv", index=False)
    summaries = []
    for (protocol, station), group in table.groupby(["protocol", "station"]):
        for model in ["selected", "previous_selected"] + [f"previous_{i}" for i in R.LABELS]:
            error = group[model] - group.observed
            summaries.append(dict(protocol=protocol, station=station, model=model, n=len(group), rmse=np.sqrt(np.mean(error ** 2)),
                                  mae=np.mean(np.abs(error)), bias=np.mean(error)))
    pd.DataFrame(summaries).to_csv(OUT / "previous_prior_skill.csv", index=False)


def evaluate(frame: pd.DataFrame, gas: str, prospective: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, selections = [], []
    protocol = "past_only" if prospective else "purged_week"
    for label, train, test in folds(frame, prospective=prospective):
        winner, scores = select(frame, gas, train)
        winner_score = next((row for row in scores if row["candidate"] == winner.name), {})
        fits = {c.name: fit_predict(frame, gas, c, train) for c in candidates_for(gas)}
        old = legacy_prediction(frame, gas, train)
        for score in scores:
            selections.append(dict(gas=gas, protocol=protocol, outer_fold=label, selected=winner.name, **score))
        for index in np.flatnonzero(test):
            row = dict(gas=gas, protocol=protocol, fold=label, station=frame.station.iloc[index],
                       time_utc=frame.time_utc.iloc[index], observed=frame.observed.iloc[index],
                       legacy=old[index], selected=fits[winner.name]["prediction"][index],
                       selected_sd=fits[winner.name]["sd"][index] * winner_score.get(f"interval_factor_{frame.station.iloc[index]}", 1.),
                       interval_factor=winner_score.get(f"interval_factor_{frame.station.iloc[index]}", 1.),
                       selected_model=winner.name,
                       train_latest=frame.loc[train, "time_utc"].max(), train_n=int(train.sum()))
            row.update({name: fit["prediction"][index] for name, fit in fits.items()})
            rows.append(row)
        print(f"{gas} {protocol} {label}: train={train.sum()} test={test.sum()} selected={winner.name}", flush=True)
    return pd.DataFrame(rows), pd.DataFrame(selections)


def score(predictions: pd.DataFrame) -> pd.DataFrame:
    """Paired calendar-week bootstrap, preserving dependent nearby dates.

    Block count is reported, never called an effective sample size. Intervals
    from fewer than eight observed weeks are explicitly exploratory.
    """
    rows = []
    rng = np.random.default_rng(20260930)
    for (gas, protocol, station), group in predictions.groupby(["gas", "protocol", "station"]):
        blocks = group.time_utc.dt.to_period("W-SUN").to_numpy()
        labels = pd.unique(blocks)
        indices = [np.flatnonzero(blocks == label) for label in labels]
        # Resample block-level sufficient statistics, not Python row arrays.
        weights = rng.multinomial(len(indices), np.repeat(1 / len(indices), len(indices)), size=BOOTSTRAP_REPS)
        counts = np.array([len(index) for index in indices])
        denominators = weights @ counts
        observed = group.observed.to_numpy()
        for model in ["selected", "legacy"] + [c.name for c in candidates_for(gas)]:
            error = group[model].to_numpy() - observed
            row = dict(gas=gas, protocol=protocol, station=station, model=model, n=len(group), weeks=len(labels),
                       rmse=float(np.sqrt(np.mean(error ** 2))), mae=float(np.mean(np.abs(error))), bias=float(np.mean(error)))
            for baseline in ("legacy", "boundary_state", "boundary_offset"):
                baseline_error = group[baseline].to_numpy() - observed
                sums = np.array([np.sum(error[index] ** 2) for index in indices])
                baseline_sums = np.array([np.sum(baseline_error[index] ** 2) for index in indices])
                deltas = np.sqrt((weights @ sums) / denominators) - np.sqrt((weights @ baseline_sums) / denominators)
                row[f"delta_{baseline}"] = row["rmse"] - float(np.sqrt(np.mean(baseline_error ** 2)))
                row[f"lo_{baseline}"], row[f"hi_{baseline}"] = np.quantile(deltas, [.025, .975])
            if model == "selected":
                row["coverage95"] = float(np.mean(np.abs(error) <= 1.96 * group.selected_sd.to_numpy()))
            rows.append(row)
    return pd.DataFrame(rows)


def scientific_sensitivity(source_frames: dict[str, pd.DataFrame]) -> None:
    """Compare competing prior/error explanations without selecting a winner.

    These full-data MAP fits are sensitivity diagnostics, not held-out scores or
    sampled credible intervals. The hybrid and FOLU responses are compared on
    the exact same 2023 receptors; missing 2024 layers are never set to zero.
    """
    rows, budget_rows = [], []
    for gas, frame in source_frames.items():
        cases = [("reference", frame, CANDIDATES[4]),
                 ("triple_discrepancy", frame, Candidate("sensitivity", "bulk", state_days=7, discrepancy_scale=3)),
                 ("wider_multiplier_prior", frame, Candidate("sensitivity", "bulk", state_days=7, multiplier_prior_factor=4))]
        if gas == "ch4":
            cases += [("national_anchor", frame, CANDIDATES[5]), ("provincial_proxy", frame, CANDIDATES[6])]
            for label in R.LABELS:
                for station, group in frame.groupby("station"):
                    for component, values in (("anthropogenic near", group[f"anthro_near_ppb_{label}"]),
                                              ("anthropogenic far", group[f"anthro_far_ppb_{label}"]),
                                              ("wetlands", group.wetlands_ppb), ("fire", group.fire_ppb),
                                              ("soil uptake", -group.soil_uptake_ppb), ("termites", group.termites_ppb),
                                              ("geological", group.geological_ppb)):
                        budget_rows.append(dict(gas=gas, station=station, prior=label, period="2023", component=component,
                                                mean_response=values.mean(), receptor_sd=values.std(), n=len(group), unit="ppb"))
        else:
            early = frame[frame.period.eq("2023")].copy()
            hybrid = pd.read_csv(V.TABLES / "co2_diagnostic_operator_hybrid.csv", parse_dates=["time_utc"])
            hybrid = early.drop(columns=["gpp_ppm", "resp_ppm", "gpp_ppm_seed_sd", "resp_ppm_seed_sd"]).merge(
                hybrid, on=["station", "time_utc"], validate="one_to_one")
            for station in ("BKT", "JMB"):
                member = hybrid.station.eq(station).to_numpy(float)
                hybrid[f"bio_net_{station}_ppm"] = (hybrid.gpp_ppm + hybrid.resp_ppm) * member
            hybrid["ensemble_sd"] = np.sqrt(hybrid[["gpp_ppm_seed_sd", "resp_ppm_seed_sd", "fossil_near_ppm_seed_sd", "background_ppm_seed_sd"]].fillna(0).pow(2).sum(axis=1))
            folu = early.merge(pd.read_csv(V.TABLES / "co2_folu_response_full.csv", parse_dates=["time_utc"]),
                               on=["station", "time_utc"], validate="one_to_one")
            if len(folu) != len(early) or len(hybrid) != len(early):
                raise ValueError("A CO2 sensitivity changed the matched 2023 receptor population")
            cases += [("diagnostic_2023", early, CANDIDATES[4]), ("hybrid_2023", hybrid, CANDIDATES[4]),
                      ("folu_2023", folu, CANDIDATES[4])]
            for label, part in (("diagnostic", frame), ("diagnostic_2023", early), ("hybrid_2023", hybrid), ("folu_2023", folu)):
                for station, group in part.groupby("station"):
                    for component, values in (("fossil near", group.fossil_near_ppm), ("fossil far", group.fossil_far_ppm),
                                              ("gross uptake", group.gpp_ppm), ("respiration", group.resp_ppm),
                                              ("net biosphere", group.gpp_ppm + group.resp_ppm), ("ocean", group.ocean_ppm),
                                              ("fire", group.fire_ppm)):
                        budget_rows.append(dict(gas=gas, station=station, prior=label, period="2023" if label.endswith("2023") else "2023 and 2024",
                                                component=component, mean_response=values.mean(), receptor_sd=values.std(), n=len(group), unit="ppm"))
                    if "folu_3b1_ppm" in group:
                        budget_rows.append(dict(gas=gas, station=station, prior=label, period="2023", component="peat drainage",
                                                mean_response=group.folu_3b1_ppm.mean(), receptor_sd=group.folu_3b1_ppm.std(), n=len(group), unit="ppm"))
        for label, part, candidate in cases:
            fit = fit_predict(part, gas, candidate, np.ones(len(part), bool))
            for i, name in enumerate(fit["source_names"]):
                rows.append(dict(gas=gas, sensitivity=label, receptors=len(part), parameter=name,
                                 map_multiplier=np.exp(fit["theta"][i]),
                                 laplace_log_sd=np.sqrt(fit["posterior_cov"][i, i]),
                                 source_dofs_laplace=fit["source_dofs"], reduced_chi_square=fit["chi"],
                                 inference="conditional sensitivity; not a validated flux"))
    pd.DataFrame(rows).to_csv(OUT / "prior_error_sensitivity.csv", index=False)
    pd.DataFrame(budget_rows).to_csv(OUT / "matched_component_budget.csv", index=False)


def run(as_of: pd.Timestamp | None = None, max_age_days: int = 7, quick: bool = False, historical: bool = False) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    source_frames = frames()
    predictions, selection_tables, qc, parameters, status, budgets = [], [], [], [], [], []
    as_of = pd.Timestamp.now(tz="UTC").tz_localize(None) if as_of is None else as_of
    for gas, frame in source_frames.items():
        frame = frame[frame.time_utc <= as_of].reset_index(drop=True)
        if frame.empty:
            raise ValueError(f"No eligible receptors on or before {as_of}: {gas}")
        frame.to_csv(OUT / f"{gas}_model_frame.csv", index=False)
        source_frames[gas] = frame
        for protocol in (False, True):
            p, s = evaluate(frame, gas, protocol)
            if p.empty:
                raise ValueError(f"No evaluable {'past-only' if protocol else 'purged'} folds: {gas}")
            predictions.append(p); selection_tables.append(s)
        for station, group in frame.groupby("station"):
            qc.append(dict(gas=gas, station=station, receptors=len(group), dates=group.time_utc.dt.normalize().nunique(),
                           first=group.time_utc.min(), last=group.time_utc.max(), mean_observed=group.observed.mean(),
                           mean_base=group.base.mean(), mean_prior_source=group.source_total.mean(),
                           minimum_pblh=group.PBLH.min(), rms_ensemble_sd=np.sqrt(np.mean(group.ensemble_sd ** 2))))
        winner, scores = select(frame, gas, np.ones(len(frame), bool))
        fit = fit_predict(frame, gas, winner, np.ones(len(frame), bool))
        age = float((as_of - frame.time_utc.max()) / pd.Timedelta(days=1))
        fit_diag = fit_predict(frame, gas, CANDIDATES[4], np.ones(len(frame), bool))
        for station, group in frame.groupby("station"):
            rows_station = frame.station.eq(station).to_numpy()
            signal_sd = float(group.source_total.std(ddof=1))
            ensemble_rms = float(np.sqrt(np.mean(group.ensemble_sd ** 2)))
            independent = float(np.hypot(V.GASES[gas].measurement, V.GASES[gas].local))
            total_rms = float(np.sqrt(np.mean(np.diag(fit_diag["working_covariance"])[rows_station])))
            budgets.append(dict(gas=gas, station=station, unit=V.GASES[gas].unit, source_signal_sd=signal_sd,
                                ensemble_rms=ensemble_rms, independent_sd=independent,
                                working_total_rms=total_rms, signal_to_working_error=signal_sd / total_rms,
                                transport_status="seed-spread proxy; not independently measured driver error"))
        # Source intervals are sampled, not the Laplace approximation used in CV.
        if not quick:
            from bkt_methane_inverse import chain_diagnostics
            conditional_cases = [CANDIDATES[4]] if gas == "co2" else list(CANDIDATES[4:])
            for case in conditional_cases:
                conditional = fit_predict(frame, gas, case, np.ones(len(frame), bool))
                for draws, thin in ((12000, 3), (48000, 12)):
                    chains, _ = conditional["problem"].sample(seed=20260930, draws=draws, thin=thin)
                    rhat, ess = chain_diagnostics(chains)
                    if np.max(rhat) <= 1.01 and np.min(ess) >= 1000:
                        break
                else:
                    raise RuntimeError(f"Conditional source diagnostic did not converge: {gas}/{case.inventory}")
                draws_flat = chains.reshape(-1, chains.shape[-1])
                for i, name in enumerate(conditional["source_names"]):
                    q = np.quantile(np.exp(draws_flat[:, i]), [.025, .5, .975])
                    parameters.append(dict(gas=gas, inventory=case.inventory, parameter=name, q025=q[0], median=q[1], q975=q[2],
                                           rhat=float(rhat[i]), ess=float(ess[i]),
                                           uncertainty_ratio=float(draws_flat[:, i].std(ddof=1) / np.log(2))))
                print(f"sampled conditional source fit: {gas}/{case.inventory} Rhat={np.max(rhat):.3f} ESS={np.min(ess):.0f}", flush=True)
        status.append(dict(gas=gas, selected_model=winner.name, as_of=str(as_of), last_receptor=str(frame.time_utc.max()),
                           age_days=age, fresh=age <= max_age_days, local_service="ready" if age <= max_age_days else "stale: live emission release blocked",
                           absolute_emission_release=False, reasons=["conditional transport/prior attribution", "no independent absolute flux validation"],
                           conditional_source_dofs_laplace=fit_diag["source_dofs"], fitted_reduced_chi_square=fit_diag["chi"],
                           fitted_discrepancy_amplitude=fit_diag["amplitude"], parameters=fit["theta"].tolist(),
                           source_names=fit["source_names"], nuisance_names=fit["nuisance_names"], inner_selection=scores))
    pred = pd.concat(predictions, ignore_index=True)
    pred.to_csv(OUT / "validation_predictions.csv", index=False)
    pd.concat(selection_tables, ignore_index=True).to_csv(OUT / "selection_audit.csv", index=False)
    summary = score(pred)
    summary.to_csv(OUT / "validation_skill.csv", index=False)
    effects = summary[summary.model.eq("selected")].copy()
    effects["previous_rmse"] = effects.rmse - effects.delta_legacy
    effects["rmse_reduction_percent"] = -100 * effects.delta_legacy / effects.previous_rmse
    effects.to_csv(OUT / "effect_sizes.csv", index=False)
    pd.DataFrame(qc).to_csv(OUT / "population.csv", index=False)
    pd.DataFrame(budgets).to_csv(OUT / "working_error_budget.csv", index=False)
    if parameters:
        pd.DataFrame(parameters).to_csv(OUT / "conditional_parameters.csv", index=False)
    scientific_sensitivity(source_frames)
    compare_previous_priors(source_frames, pred)
    archives = []
    for station in ("BKT", "JMB"):
        record = R.G.apply_flags(R.G.load_station(station))
        for gas in ("co2", "ch4"):
            valid = record[record[gas].notna()]
            archives.append(dict(gas=gas, station=station, valid_hours=len(valid), latest_utc=valid.time_utc.max()))
    pd.DataFrame(archives).to_csv(OUT / "archive_coverage.csv", index=False)
    pd.DataFrame([dict(gas=s["gas"], selected_model=s["selected_model"], last_receptor=s["last_receptor"],
                       as_of=s["as_of"], age_days=s["age_days"], fresh=s["fresh"],
                       absolute_emission_release=s["absolute_emission_release"], local_service=s["local_service"]) for s in status]).to_csv(OUT / "service_state.csv", index=False)
    pd.DataFrame([dict(purge_days=PURGE_DAYS, block_days=BLOCK_DAYS, minimum_train_station=MIN_TRAIN_STATION,
                       minimum_inner_station=MIN_INNER_STATION, bootstrap_reps=BOOTSTRAP_REPS,
                       state_timescale_days=7, minimum_mixing_depth_m=R.MIN_PBLH, max_age_days=max_age_days,
                       multiplier_prior_factor=2, min_survival_fraction=.95, receptor_hour_utc=6,
                       observation_hours_utc="5;6;7", minimum_observation_hours=2)]).to_csv(OUT / "protocol.csv", index=False)
    manifest = dict(schema_version=1, generated_utc=datetime.now(timezone.utc).isoformat(), as_of=str(as_of),
                    mode="historical analysis" if historical else "freshness-guarded batch",
                    quick=quick, purge_days=PURGE_DAYS, block_days=BLOCK_DAYS, max_age_days=max_age_days,
                    gas_status=status, response_receipt=json.loads((OUT / "response_receipt.json").read_text()))
    (OUT / "service_status.json").write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n")
    print(summary[summary.model.eq("selected")].to_string(index=False), flush=True)
    return manifest


def predict(incoming: pd.DataFrame, gas: str, as_of: pd.Timestamp, max_age_days: int = 7) -> pd.DataFrame:
    """Predict new operator rows with a frozen past-only fit and freshness guard.

    Operators must be available by the stated cutoff. The caller supplies
    availability time explicitly; predicted receptor timestamps alone do not
    establish when a historical transport/boundary product became available.
    Incoming observations are ignored, even if a CSV includes them.
    """
    training = pd.read_csv(OUT / f"{gas}_model_frame.csv", parse_dates=["time_utc"])
    # CSV inference turns year strings into integers. Match incoming regime
    # labels explicitly so a valid archived station/year is not rejected.
    training["period"] = training.time_utc.dt.year.astype(str)
    training = training[training.time_utc < as_of].reset_index(drop=True)
    if training.empty or (as_of - training.time_utc.max()) > pd.Timedelta(days=max_age_days):
        raise ValueError(f"Stale or absent training receptors for {gas}; refresh operators and observations")
    incoming = incoming.copy()
    required = {"station", "time_utc", "available_utc", "unit", "PBLH", "transport_usable", "endpoint_survival_fraction", "base", "ensemble_sd"}
    if gas == "co2":
        required.update({"fossil_near_ppm", "fossil_far_ppm", "gpp_ppm", "resp_ppm"})
    else:
        required.update({"wetlands_ppb", "fire_ppb"})
        required.update(f"anthro_{distance}_ppb_{inventory}" for distance in ("near", "far") for inventory in R.LABELS)
    missing = required - set(incoming)
    if missing:
        raise ValueError(f"Missing prediction fields: {sorted(missing)}")
    if not incoming.unit.eq(V.GASES[gas].unit).all():
        raise ValueError(f"Expected {V.GASES[gas].unit} forward responses for {gas}")
    incoming["time_utc"] = pd.to_datetime(incoming.time_utc, utc=True).dt.tz_localize(None)
    incoming["available_utc"] = pd.to_datetime(incoming.available_utc, utc=True).dt.tz_localize(None)
    if incoming[["time_utc", "available_utc"]].isna().any().any():
        raise ValueError("Missing receptor or operator availability timestamp")
    if (incoming.available_utc > as_of).any() or (incoming.time_utc < as_of).any():
        raise ValueError("Operator unavailable at cutoff or receptor predates prediction cutoff")
    if (incoming.time_utc > as_of + pd.Timedelta(days=7)).any():
        raise ValueError("Prediction exceeds the configured seven-day service horizon")
    if incoming.empty or incoming.duplicated(["station", "time_utc"]).any():
        raise ValueError("Empty or duplicate prediction receptors")
    central_hour = incoming.time_utc.eq(incoming.time_utc.dt.normalize() + pd.Timedelta(hours=6))
    if not central_hour.all() or not incoming.PBLH.ge(R.MIN_PBLH).all() or not incoming.transport_usable.eq(True).all() or not incoming.endpoint_survival_fraction.between(.95, 1.).all():
        raise ValueError("Prediction receptor fails afternoon/mixing-depth/retention QC")
    for station in incoming.station.unique():
        latest = training.loc[training.station.eq(station), "time_utc"].max()
        if pd.isna(latest) or as_of - latest > pd.Timedelta(days=max_age_days):
            raise ValueError(f"Stale or absent training at requested station {station}")
    if gas == "co2":
        for station in ("BKT", "JMB"):
            incoming[f"bio_net_{station}_ppm"] = (incoming.gpp_ppm + incoming.resp_ppm) * incoming.station.eq(station)
    incoming["observed"] = np.nan
    incoming["period"] = incoming.time_utc.dt.year.astype(str)
    combined = pd.concat([training, incoming], ignore_index=True)
    train = np.arange(len(combined)) < len(training)
    test = ~train
    if not admissible(combined, train, test, MIN_TRAIN_STATION):
        raise ValueError("Insufficient training at a requested station or campaign year")
    candidate, scores = select(training, gas, np.ones(len(training), bool))
    # Validate all required features before a missing column can reach fitting.
    k, _ = components(combined, gas, candidate.inventory)
    if not np.isfinite(k).all() or not np.isfinite(combined[["base", "ensemble_sd"]]).all().all() or not combined.ensemble_sd.ge(0).all():
        raise ValueError("Nonfinite required forward-model features")
    fit = fit_predict(combined, gas, candidate, train)
    selected_score = next((row for row in scores if row["candidate"] == candidate.name), {})
    result = incoming[["station", "time_utc", "available_utc"]].copy()
    factor = np.array([selected_score.get(f"interval_factor_{s}", 1.) for s in incoming.station])
    result["prediction"] = fit["prediction"][test]
    result["lower95_working"] = fit["prediction"][test] - 1.96 * fit["sd"][test] * factor
    result["upper95_working"] = fit["prediction"][test] + 1.96 * fit["sd"][test] * factor
    result["model"] = candidate.name
    result["unit"] = V.GASES[gas].unit
    result["as_of_utc"] = str(as_of)
    result["latest_training_utc"] = str(training.time_utc.max())
    result["absolute_emission_release"] = False
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", help="UTC cutoff; defaults to now, never silently a historical end date")
    parser.add_argument("--max-age-days", type=int, default=7)
    parser.add_argument("--quick", action="store_true", help="development checks only; omit sampled source intervals")
    parser.add_argument("--historical", action="store_true", help="explicit available-data analysis; stale data are reported, not a failed live run")
    parser.add_argument("--predict", type=Path, help="CSV of available new operator rows; no incoming observation is used")
    parser.add_argument("--gas", choices=("co2", "ch4"), help="required with --predict")
    parser.add_argument("--output", type=Path, help="prediction CSV destination, defaults inside the revised output run")
    args = parser.parse_args()
    if args.max_age_days < 0:
        parser.error("max-age-days must be non-negative")
    stamp = pd.Timestamp(args.as_of) if args.as_of else None
    if stamp is not None and stamp.tzinfo is not None:
        stamp = stamp.tz_convert("UTC").tz_localize(None)
    if args.predict:
        if not args.gas or stamp is None:
            parser.error("--predict requires --gas and an explicit --as-of UTC cutoff")
        prediction = predict(pd.read_csv(args.predict), args.gas, stamp, args.max_age_days)
        destination = args.output or OUT / f"{args.gas}_new_predictions.csv"
        destination.parent.mkdir(parents=True, exist_ok=True)
        prediction.to_csv(destination, index=False)
        print(f"wrote {destination} ({len(prediction)} guarded predictions)")
    else:
        manifest = run(stamp, args.max_age_days, args.quick, args.historical)
        if not args.historical and not all(s["fresh"] for s in manifest["gas_status"]):
            raise SystemExit(2)  # stale is actionable, not a successful live run


if __name__ == "__main__":
    main()
