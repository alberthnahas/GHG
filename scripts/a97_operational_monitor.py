#!/usr/bin/env python3
"""Operational background and episode monitoring for every station in the archive.

This is the part of the two-receptor work that survives routine use. The
inversion does not predict a withheld day better than its own boundary field
(BKT_JMB_CO2_Report, and a96 for methane), so nothing here depends on an
inversion. What the observations do support, every day, at any station:

  a clean-air baseline per species, from the station's own record;
  an enhancement above that baseline for every hour;
  episodes detected on carbon monoxide, the combustion tracer;
  tracer ratios within each episode, with bootstrap intervals, which separate
    combustion from biogenic enhancement without any transport model.

It runs on the harmonized hourly archive alone: no meteorology, no inventory, no
boundary product, so it works for a new station the day its record is loaded.
Footprint-weighted source influence (a98) and the inversion (a84, a89) attach to
these episodes afterwards where meteorology exists.

Caveats, deliberately not hidden:
  the baseline is empirical, not a modeled background, and a station whose record
    is shorter than the baseline window gets a wider, weaker baseline;
  the ratio classes below are indicative and want local calibration against
    known fires and known urban plumes before they carry weight;
  ratios are enhancement ratios at the inlet, not emission factors;
  half the episodes found here are night-dominated, and a nocturnal enhancement
    is accumulation under a shallow layer as much as it is a plume, so read the
    signature of a high night_fraction episode as indicative only. The same
    shallow layer is what the transport model cannot represent (a89), so night
    episodes are exactly the ones a footprint will not explain.

Stages
  baseline   hourly baseline and enhancement per station and species
  episodes   detect episodes and characterize each one by its tracer ratios
  summary    per-station monthly background and episode counts
  all        the three above in order
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

import ghg_common as G

ROOT = G.ROOT if hasattr(G, "ROOT") else __import__("pathlib").Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/operational"
SPECIES = ("co2", "ch4", "co")
UNITS = {"co2": "ppm", "ch4": "ppb", "co": "ppb"}
AFTERNOON_SOLAR = (12., 16.)      # well-mixed hours used to define the clean-air baseline
BASELINE_DAYS, BASELINE_QUANTILE = 30, .1
MIN_AFTERNOON_HOURS = 2
EPISODE_TRACER = "co"
EPISODE_SIGMA = 5.               # robust standard deviations above the station's own median enhancement
EPISODE_FLOOR = {"co": 30.}      # ppb: an episode must also clear this, so a clean station stays quiet
CLIMATOLOGY_MIN_YEARS, CLIMATOLOGY_WINDOW_DAYS = 3, 15
SUSTAINED_HOURS = 24             # beyond this an episode is a haze period, not a plume
MIN_EPISODE_HOURS, MAX_GAP_HOURS = 3, 2
RATIO_MIN_HOURS, RATIO_REPS, RATIO_SEED = 5, 1000, 20260917
RATIO_MAX_HOURS, RATIO_CHUNK = 48, 250   # pairwise slopes are quadratic in hours; cap and chunk them
RATIO_CLASSES = (   # indicative delta CO to delta CO2 ranges, ppb per ppm; calibrate locally before trusting
    (40., np.inf, "combustion, biomass-burning like"),
    (10., 40., "combustion, mixed or urban like"),
    (-np.inf, 10., "little combustion signature"))


def solar_hour(index: pd.DatetimeIndex, lon: float) -> np.ndarray:
    return (index.hour + index.minute / 60 + lon / 15) % 24


def record(code: str) -> pd.DataFrame:
    frame = G.apply_flags(G.load_station(code)).set_index("time_utc").sort_index()
    return frame[~frame.index.duplicated()]


def climatology(daily: pd.Series, window: int = CLIMATOLOGY_WINDOW_DAYS) -> pd.Series | None:
    """Day-of-year clean-air level from every year in the record, smoothed around the calendar.

    A rolling baseline treats a two-month haze as background, because the low
    quantile of a smoky month is still smoky. October 2015 at BKT is the case in
    point: the rolling baseline there sits near 800 ppb of carbon monoxide. The
    climatological level is built only from what the same calendar days look like
    in the station's other years, so a whole smoky season still stands above it.
    """
    years = daily.dropna().index.year.nunique()
    if years < CLIMATOLOGY_MIN_YEARS:
        return None
    doy = daily.index.dayofyear.where(daily.index.dayofyear < 366, 365)
    level = daily.groupby(doy).quantile(BASELINE_QUANTILE).reindex(range(1, 366))
    wrapped = pd.concat([level, level, level]).rolling(window, center=True, min_periods=1).median()
    return wrapped.iloc[len(level):2 * len(level)].set_axis(level.index).interpolate(limit_direction="both")


def baseline_table(code: str) -> pd.DataFrame:
    """Hourly value, two clean-air baselines and the enhancement above each.

    The local baseline is a centered rolling low quantile of the station's own
    daily afternoon medians, the construction a93 validated against modeled
    methane enhancement (Spearman 0.80 at BKT, 0.98 at Jambi). It follows a
    sustained event and so understates it, which is why the climatological
    baseline sits beside it and drives episode detection where it exists.
    """
    frame = record(code)
    _, _, _, lon, _, _, _ = G.STATIONS[code]
    index = pd.date_range(frame.index.min(), frame.index.max(), freq="h")
    frame = frame.reindex(index)
    solar = solar_hour(index, lon)
    afternoon = (solar >= AFTERNOON_SOLAR[0]) & (solar < AFTERNOON_SOLAR[1])
    out = pd.DataFrame(index=index)
    out.index.name = "time_utc"
    out["station"] = code
    out["solar_hour"] = solar.round(2)
    out["afternoon"] = afternoon
    day = index.normalize()
    doy = pd.Index(index.dayofyear).where(index.dayofyear < 366, 365)
    for name in SPECIES:
        if name not in frame.columns:
            continue
        values = frame[name]
        clean = values.where(afternoon)
        daily = clean.groupby(day).median()
        daily = daily.where(clean.groupby(day).count() >= MIN_AFTERNOON_HOURS)
        local = daily.rolling(BASELINE_DAYS, center=True, min_periods=5).quantile(BASELINE_QUANTILE)
        out[name] = values.to_numpy()
        out[f"{name}_baseline_local"] = local.reindex(day).to_numpy()
        out[f"{name}_enhancement_local"] = out[name] - out[f"{name}_baseline_local"]
        seasonal = climatology(daily)
        if seasonal is None:
            out[f"{name}_baseline_climatological"] = np.nan
            out[f"{name}_enhancement"] = out[f"{name}_enhancement_local"]
            out[f"{name}_reference"] = "local"
        else:
            out[f"{name}_baseline_climatological"] = seasonal.reindex(doy).to_numpy()
            out[f"{name}_enhancement"] = out[name] - out[f"{name}_baseline_climatological"]
            out[f"{name}_reference"] = "climatological"
    return out.reset_index()


def theil_sen(x: np.ndarray, y: np.ndarray) -> float:
    """Median pairwise slope: robust to the one bad hour that a least-squares ratio would follow."""
    i, j = np.triu_indices(len(x), k=1)
    dx = x[j] - x[i]
    keep = np.abs(dx) > 1e-9
    if not keep.any():
        return float("nan")
    return float(np.median((y[j] - y[i])[keep] / dx[keep]))


def ratio(x: np.ndarray, y: np.ndarray, reps: int = RATIO_REPS, seed: int = RATIO_SEED) -> tuple[float, float, float]:
    """Theil-Sen slope of y on x with a bootstrap interval over hours.

    The bootstrap is vectorized over replicates, and an episode longer than
    RATIO_MAX_HOURS is subsampled to that length in each replicate, because the
    pairwise slope is quadratic in the number of hours and this has to run over a
    whole archive without anyone waiting for it.
    """
    good = np.isfinite(x) & np.isfinite(y)
    x, y = x[good], y[good]
    if len(x) < RATIO_MIN_HOURS:
        return float("nan"), float("nan"), float("nan")
    point = theil_sen(x, y)
    rng = np.random.default_rng(seed)
    size = min(len(x), RATIO_MAX_HOURS)
    draws = np.empty(reps)
    i, j = np.triu_indices(size, k=1)
    for start in range(0, reps, RATIO_CHUNK):
        stop = min(start + RATIO_CHUNK, reps)
        take = rng.integers(0, len(x), (stop - start, size))
        xs, ys = x[take], y[take]
        dx = xs[:, j] - xs[:, i]
        dy = ys[:, j] - ys[:, i]
        slopes = np.where(np.abs(dx) > 1e-9, dy / np.where(np.abs(dx) > 1e-9, dx, 1.), np.nan)
        draws[start:stop] = np.nanmedian(slopes, axis=1)
    draws = draws[np.isfinite(draws)]
    if not len(draws):
        return point, float("nan"), float("nan")
    return point, float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def episode_threshold(series: pd.Series) -> float:
    """Median plus a robust multiple of the spread, floored.

    A fixed quantile would flag the same share of hours whatever the year, which
    is no use for telling a smoky season from a clean one; this scale is set by
    the station's own ordinary variability and then held fixed.
    """
    values = series.dropna().to_numpy()
    if not len(values):
        return float("inf")
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median))) * 1.4826
    return max(median + EPISODE_SIGMA * mad, EPISODE_FLOOR.get(EPISODE_TRACER, 0.))


def classify(co_per_co2: float) -> str:
    if not np.isfinite(co_per_co2):
        return "not determined"
    for low, high, label in RATIO_CLASSES:
        if low <= co_per_co2 < high:
            return label
    return "not determined"


def find_episodes(table: pd.DataFrame, code: str) -> pd.DataFrame:
    """Contiguous runs where the combustion tracer stands above the station's own threshold."""
    tracer = f"{EPISODE_TRACER}_enhancement"
    if tracer not in table:
        return pd.DataFrame()
    series = table.set_index("time_utc")[tracer]
    threshold = episode_threshold(series)
    above = (series > threshold).fillna(False).to_numpy()
    # bridge gaps of at most MAX_GAP_HOURS so one missing hour does not split an episode
    filled = above.copy()
    gap = 0
    for i, flag in enumerate(above):
        if flag:
            if 0 < gap <= MAX_GAP_HOURS:
                filled[i - gap:i] = True
            gap = 0
        else:
            gap += 1
    edges = np.flatnonzero(np.diff(np.r_[False, filled, False].astype(int)))
    rows = []
    for start, stop in zip(edges[::2], edges[1::2]):
        window = table.iloc[start:stop]
        if len(window) < MIN_EPISODE_HOURS:
            continue
        night = ~window.afternoon.to_numpy() & ((window.solar_hour < 6) | (window.solar_hour >= 18)).to_numpy()
        entry = dict(station=code, start=window.time_utc.iloc[0], end=window.time_utc.iloc[-1], hours=len(window),
                     threshold_ppb=threshold, peak_co_enhancement_ppb=float(window[tracer].max()),
                     night_fraction=float(night.mean()), sustained=bool(len(window) >= SUSTAINED_HOURS),
                     reference=str(window[f"{EPISODE_TRACER}_reference"].iloc[0]),
                     **{f"{name}_hours": int(window[f"{name}_enhancement"].notna().sum())
                        for name in SPECIES if f"{name}_enhancement" in window})
        pairs = (("co", "co2", "co_per_co2_ppb_ppm"), ("ch4", "co2", "ch4_per_co2_ppb_ppm"), ("ch4", "co", "ch4_per_co_ppb_ppb"))
        for numerator, denominator, label in pairs:
            if f"{numerator}_enhancement" not in window or f"{denominator}_enhancement" not in window:
                continue
            slope, lo, hi = ratio(window[f"{denominator}_enhancement"].to_numpy(), window[f"{numerator}_enhancement"].to_numpy())
            entry.update({label: slope, f"{label}_lo": lo, f"{label}_hi": hi})
        for name in SPECIES:
            column = f"{name}_enhancement"
            if column in window:
                entry[f"peak_{name}_enhancement"] = float(window[column].max())
        entry["signature"] = classify(entry.get("co_per_co2_ppb_ppm", float("nan")))
        rows.append(entry)
    return pd.DataFrame(rows)


def stations(selected: list[str] | None) -> list[str]:
    return [c for c in G.STATIONS if not selected or c in selected]


def baseline(selected: list[str] | None = None) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for code in stations(selected):
        table = baseline_table(code)
        table.to_csv(OUT / f"baseline_{code}.csv", index=False)
        covered = {name: (float(table[f"{name}_enhancement"].notna().mean() * 100), table[f"{name}_reference"].iloc[0])
                   for name in SPECIES if f"{name}_enhancement" in table}
        print(f"{code}: {len(table):6d} hours; " +
              ", ".join(f"{name} enhancement on {share:.0f}% of hours ({reference})" for name, (share, reference) in covered.items()),
              flush=True)


def episodes(selected: list[str] | None = None) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    found = []
    for code in stations(selected):
        path = OUT / f"baseline_{code}.csv"
        if not path.exists():
            raise FileNotFoundError(f"Run the baseline stage first: {path}")
        table = pd.read_csv(path, parse_dates=["time_utc"])
        episode = find_episodes(table, code)
        if len(episode):
            found.append(episode)
        print(f"{code}: {len(episode)} episodes" +
              (f", longest {int(episode.hours.max())} h, strongest {episode.peak_co_enhancement_ppb.max():.0f} ppb CO"
               if len(episode) else ""), flush=True)
    table = pd.concat(found, ignore_index=True) if found else pd.DataFrame()
    table.to_csv(OUT / "episodes.csv", index=False)
    if len(table):
        pd.set_option("display.width", 220)
        print(table.groupby(["station", "signature"]).size().to_string())


def summary(selected: list[str] | None = None) -> None:
    rows = []
    episode_table = pd.read_csv(OUT / "episodes.csv", parse_dates=["start", "end"]) if (OUT / "episodes.csv").exists() else pd.DataFrame()
    for code in stations(selected):
        table = pd.read_csv(OUT / f"baseline_{code}.csv", parse_dates=["time_utc"])
        table["month"] = table.time_utc.dt.to_period("M").dt.to_timestamp()
        for month, group in table.groupby("month"):
            entry = dict(station=code, month=month, hours=len(group))
            for name in SPECIES:
                if f"{name}_enhancement" not in group:
                    continue
                # coverage first: a month with no data must never read as a quiet month
                entry[f"{name}_coverage_percent"] = float(group[name].notna().mean() * 100)
                entry[f"{name}_baseline_local"] = float(group[f"{name}_baseline_local"].median())
                entry[f"{name}_baseline_climatological"] = float(group[f"{name}_baseline_climatological"].median())
                entry[f"{name}_enhancement_median"] = float(group[f"{name}_enhancement"].median())
                entry[f"{name}_enhancement_p95"] = float(group[f"{name}_enhancement"].quantile(.95))
            if len(episode_table):
                inside = episode_table[episode_table.station.eq(code) & episode_table.start.dt.to_period("M").dt.to_timestamp().eq(month)]
                entry["episodes"] = int(len(inside))
                entry["episode_hours"] = int(inside.hours.sum()) if len(inside) else 0
                tracer_hours = float(group[EPISODE_TRACER].notna().sum())
                entry["episode_hours_per_1000_observed"] = (round(1000 * entry["episode_hours"] / tracer_hours, 1)
                                                           if tracer_hours else float("nan"))
            rows.append(entry)
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "monthly_summary.csv", index=False)
    print(f"wrote {len(table)} station-months to {OUT / 'monthly_summary.csv'}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["baseline", "episodes", "summary", "all"])
    parser.add_argument("--stations", nargs="*", help="station codes; default every station in the archive")
    a = parser.parse_args()
    if a.stage in ("baseline", "all"):
        baseline(a.stations)
    if a.stage in ("episodes", "all"):
        episodes(a.stations)
    if a.stage in ("summary", "all"):
        summary(a.stations)


if __name__ == "__main__":
    main()
