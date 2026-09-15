#!/usr/bin/env python3
"""Validate the BKT + Jambi two-receptor report against its evidence and rendering."""
from __future__ import annotations
import json
import re
import subprocess
import pandas as pd
from PIL import Image
import a84_bkt_jmb_two_receptor as T
from a86_bkt_jmb_report import build, STEM

ROOT = T.ROOT


def validate() -> dict:
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

    ledger = pd.read_csv(T.TABLES / "run_ledger.csv")
    check(len(ledger) == 294 and ledger.complete.all(), "all 294 declared runs complete")
    receipts = list(T.RUNS.glob("*_s*/bkt_*/completion_receipt.json"))
    check(len(receipts) == 294, "294 completion receipts on disk")
    for path in receipts[:10]:
        rec = json.loads(path.read_text())
        check(rec["configuration"]["receptor_height_m_agl"] == T.INLET_HEIGHT_M, f"100 m release {path.parent.name}")
    par = pd.read_csv(T.TABLES / "inversion_parameters.csv")
    check(par.rhat.max() <= 1.01 and par.ess.min() >= 1000, "posterior convergence in every case")
    op = pd.read_csv(T.TABLES / "operator_base.csv")
    check(len(op) == 98 and (op.members == 3).all(), "three-seed operator for 49 hours at two towers")
    data = pd.read_csv(T.TABLES / "dataset_availability.csv").set_index("product")
    check("methane variable present: False" in data.loc["CarbonTracker CT-NRT.v2025-1 molefractions", "note"], "CT-NRT carries no methane field")
    check(not data.loc["CarbonTracker-CH4 2025 molefractions (used)", "covers_2024"], "CarbonTracker-CH4 boundary ends before 2024")

    figs = sorted((T.OUT / "figures").glob("figure_T*.png"))
    check(len(figs) == 4, "four two-receptor figures")
    for path in figs:
        with Image.open(path) as im:
            check(im.width >= 2100 and im.height >= 1100, f"publication raster size {path.stem}")
        check(path.with_suffix(".pdf").is_file(), f"vector companion {path.stem}")
        check(path.name in markdown, f"figure referenced {path.stem}")

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
    result = dict(status="passed", checks=len(checks), pages=pages, document=STEM)
    pd.DataFrame(checks).to_csv(T.TABLES / "report_validation_checks.csv", index=False)
    (T.OUT / "report_validation.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2))
