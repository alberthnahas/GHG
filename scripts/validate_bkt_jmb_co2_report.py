#!/usr/bin/env python3
"""Validate the BKT + Jambi carbon dioxide report against its evidence and rendering."""
from __future__ import annotations

import json
import re
import subprocess

import pandas as pd
from PIL import Image

import a84_bkt_jmb_two_receptor as T
import a90_bkt_jmb_co2_improved as I
import a92_bkt_release_height as H
import a93_bkt_jmb_co2_2024 as E
from a95_bkt_jmb_co2_report import ROUND, STEM, build

ROOT = T.ROOT


def validate(require_round: bool = True) -> dict:
    checks = []

    def check(condition, label):
        if not condition:
            raise ValueError(label)
        checks.append(dict(check=label, status="passed"))

    markdown = (ROOT / f"{STEM}.md").read_text()
    check(markdown == build(write=False), "canonical markdown matches evidence and template")
    check("—" not in markdown, "no em dashes")
    for pattern in (r"scripts/a", r"/run/media/", r"\{\{", r"SHA.256"):
        check(re.search(pattern, markdown) is None, f"narrative excludes {pattern}")
    for kind in ("Figure", "Table"):
        numbers = [int(n) for n in re.findall(r"\*\*%s (\d+)\." % kind, markdown)]
        check(numbers == list(range(1, len(numbers) + 1)), f"{kind.lower()}s numbered consecutively")
        check({int(n) for n in re.findall(r"\b%s (\d+)\b" % kind, markdown)} <= set(numbers), f"every {kind.lower()} reference has a caption")

    tokens = json.loads((T.OUT / "co2_report_tokens.json").read_text())
    round_used = f"_{tokens['C_ROUND']}"
    check(not require_round or round_used == ROUND, f"report built from the {ROUND.strip('_')} experiments")

    # ---- campaign completeness behind the report
    ledger = pd.read_csv(T.TABLES / "run_ledger.csv")
    check(len(ledger) == 294 and ledger.complete.all(), "all 294 runs of the 2023 campaign complete")
    height_receipts = sorted(H.RUNS.glob("bkt_h*_s*/bkt_*/completion_receipt.json"))
    check(len(height_receipts) == len(H.HEIGHTS_M) * len(T.SEEDS) * len(H.stamps()), "release-height campaign complete")
    heights = {json.loads(p.read_text())["configuration"]["receptor_height_m_agl"] for p in height_receipts}
    check(heights == set(H.HEIGHTS_M), "release-height receipts carry 150 m and 300 m")
    if round_used == ROUND:
        later = json.loads((T.TABLES / "co2_selection_summary_2024.json").read_text())
        receipts_2024 = list(E.RUNS.glob("*_s*/*_*/completion_receipt.json"))
        check(len(receipts_2024) == int(later["runs"]), f"all {later['runs']} runs of the 2024 campaign complete")
        operator_2024 = pd.read_csv(T.TABLES / "co2_operator_base_2024.csv")
        check(len(operator_2024) == 2 * int(later["joint_receptors"]), "2024 operator covers both towers at every joint receptor")
        check((operator_2024.members == len(E.SEEDS)).all(), "2024 operator averages every seed")

    # ---- the claims the prose rests on
    par = pd.read_csv(T.TABLES / f"co2_experiments{round_used}_parameters.csv")
    check(par.rhat.max() <= 1.01 and par.ess.min() >= 1000, "posterior convergence in every scored case")
    skill = pd.read_csv(T.TABLES / f"co2_experiments{round_used}_skill.csv")
    boot = pd.read_csv(T.TABLES / f"co2_experiments{round_used}_cv_bootstrap.csv")
    check(set(skill.scope) == {"all_daytime", "withheld", "leave_one_date_out"}, "all three scoring scopes present")
    check((boot.dates >= 10).all(), "every bootstrap rests on at least ten dates")
    for extra, variant in (("_round7", "best_all_periods"), ("_round8", "best_all_fire")):
        table = T.TABLES / f"co2_experiments{extra}_skill.csv"
        check(table.is_file(), f"{extra.strip('_')} robustness round present")
        check(variant in set(pd.read_csv(table).variant), f"{variant} scored in {extra.strip('_')}")
    fire = pd.read_csv(T.TABLES / "co2_experiments_round8_parameters.csv")
    fire = fire[fire.case.eq("best_all_fire") & fire.parameter.eq("fire")].iloc[0]
    check(fire.q975 < 1.5, "the fitted fire multiplier stays below the prior")
    period = pd.read_csv(T.TABLES / "co2_experiments_round7_cv_bootstrap.csv")
    period = period[period.variant.eq("best_all_periods")]
    check((period.rmse_difference_ppm > 0).all(), "the per-period fit is no better than its background at either tower")
    diurnal = pd.read_csv(T.TABLES / "co2_diurnal_summary.csv")
    night = diurnal[diurnal.hour.eq(18)]
    check((night.pblh_median < 100).all() and (night.enhancement_mean > 10).all(), "night hours are outside the model at both towers")
    screen = pd.read_csv(T.TABLES / "co2_mixing_screen.csv")
    check((screen[screen.well_mixed].pblh_m >= I.MIN_MIXING_DEPTH_M).all(), "the mixing screen keeps only well-mixed afternoons")
    phase = pd.read_csv(T.TABLES / "co2_ctnrt_phase_daily.csv", parse_dates=["date"])
    episode = phase[(phase.date >= "2023-11-25") & (phase.date <= "2023-12-01")]
    check((episode.bkt_cell_day_umol > 0).all() and (episode.jmb_cell_day_umol > 0).all(), "the CarbonTracker phase failure is in both tower cells")
    spike = pd.read_csv(T.TABLES / "co2_spike_screen.csv")
    flagged = spike[spike.co2_only_spike]
    check(len(flagged) > 0 and (flagged.ch4_departure_ppb.abs() < 20).all(), "flagged spikes move carbon dioxide alone")
    proxy = pd.read_csv(T.TABLES / "co2_ch4_proxy_validation.csv")
    check((proxy.spearman > .7).all(), "the 2024 methane proxy tracks the modelled enhancement on 2023 receptors")

    # ---- figures
    figs = sorted((T.OUT / "figures").glob("figure_C*.png"))
    check(len(figs) == 5, "five carbon dioxide figures")
    for path in figs:
        with Image.open(path) as im:
            check(im.width >= 2100 and im.height >= 1100, f"publication raster size {path.stem}")
        check(path.with_suffix(".pdf").is_file(), f"vector companion {path.stem}")
        check(path.name in markdown, f"figure referenced {path.stem}")

    # ---- rendering
    pdf = ROOT / f"outputs/{STEM}.pdf"
    info = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
    check("A4" in info, "PDF uses A4 pages")
    text = subprocess.check_output(["pdftotext", str(pdf), "-"], text=True)
    for kind in ("Figure", "Table"):
        for number in range(1, len(re.findall(r"\*\*%s \d+\." % kind, markdown)) + 1):
            check(f"{kind} {number}." in text, f"PDF {kind.lower()} {number}")
    check("{{" not in text, "no unresolved tokens in PDF")
    log = (ROOT / f"outputs/latex/{STEM}.log").read_text()
    check(not any(p in log for p in ("Overfull", "Undefined control sequence", "Missing character", "Fatal error")), "clean PDF typesetting")

    pages = int(re.search(r"Pages:\s+(\d+)", info)[1])
    result = dict(status="passed", checks=len(checks), pages=pages, document=STEM, round=tokens["C_ROUND"])
    pd.DataFrame(checks).to_csv(T.TABLES / "co2_report_validation_checks.csv", index=False)
    (T.OUT / "co2_report_validation.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--any-round", action="store_true", help="accept a build from an earlier experiment round")
    print(json.dumps(validate(require_round=not parser.parse_args().any_round), indent=2))
