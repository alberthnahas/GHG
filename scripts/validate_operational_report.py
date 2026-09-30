#!/usr/bin/env python3
"""Validate the operational inversion report against its evidence and rendering."""
from __future__ import annotations
import json, re, subprocess
import pandas as pd
from PIL import Image
import a84_bkt_jmb_two_receptor as T
from a107_operational_report import build, STEM, OPERATIONAL, INVENTORY

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
    for pattern in (r"scripts/a", r"/run/media/", r"\{\{"):
        check(re.search(pattern, markdown) is None, f"narrative excludes {pattern}")
    for kind in ("Figure", "Table"):
        numbers = [int(n) for n in re.findall(r"\*\*%s (\d+)\." % kind, markdown)]
        check(numbers == list(range(1, len(numbers) + 1)), f"{kind.lower()}s numbered consecutively")
        check({int(n) for n in re.findall(r"\b%s (\d+)\b" % kind, markdown)} <= set(numbers),
              f"every {kind.lower()} reference has a caption")

    registry = pd.read_csv(OPERATIONAL / "dataset_registry.csv")
    check((registry[registry.required].status == "ok").all(), "every required dataset validates")
    check(len(registry) >= 15, "the registry covers the whole input chain")

    verdicts = [v for v in json.loads((OPERATIONAL / "inversion_readiness.json").read_text()) if "receptors" in v]
    check(len(verdicts) >= 8, "the campaign covers both gases at several scales")
    check(all(v["convergence"]["rhat"] <= 1.01 for v in verdicts), "every reported fit converged")
    check(all(v["convergence"]["draws"] > 1000 for v in verdicts), "every reported fit was sampled, not approximated")
    operational = [v for v in verdicts if v["status"] == "operational"]
    check(not operational or "operational" in markdown, "an operational verdict would be stated")

    budget = pd.read_csv(OPERATIONAL / "error_budget.csv")
    check((budget.dominant_term == "transport").all(), "the report's central claim holds: transport dominates")
    ledger = pd.read_csv(INVENTORY / "local_inventory_ch4_2022_primap_ledger.csv")
    check(len(ledger) >= 4 and ledger.factor.min() < 0.2, "the localisation ledger carries the reported factors")
    audit = pd.read_csv(OPERATIONAL / "prior_audit.csv")
    check(abs(audit[audit.gas.eq("co2")].share_of_signal_percent.sum() - 100) < 0.1, "the audit decomposition is complete")

    attribution = {name: pd.read_csv(OPERATIONAL / f"attribution_{name}.csv")
                   for name in ("budget", "peat", "distance", "age", "provinces", "districts", "flux", "records")}
    check(all(len(table) > 0 for table in attribution.values()), "every attribution table carries rows")
    peat = attribution["peat"].set_index(["station", "quantity"])
    jambi = peat.loc[("JMB", "all peat routes combined")]
    check(jambi.peat_share_percent > peat.loc[("BKT", "all peat routes combined")].peat_share_percent,
          "the peat contribution is larger at the lowland tower")
    check(jambi.over_peat_mean < jambi.total_mean, "the peat share is a part of the whole, not the whole")
    check(attribution["flux"].detectable_change_percent.min() > 50,
          "the detection limit the report quotes is the one in the evidence")
    seen = attribution["provinces"].query("share_percent >= 1").region.nunique()
    check(seen <= 5, "the report's claim that the network sees a handful of provinces holds")
    records = attribution["records"].set_index(["gas", "station"])
    check(all(records.loc[("CH4", s)].modelled_over_observed > 1.5 for s in ("BKT", "JMB")),
          "the global gridded methane prior still overpredicts at both towers")

    questions = re.findall(r"^\*\*Q(\d+)\. ", markdown, flags=re.M)
    check(len(questions) >= 50, "the appendix answers at least fifty questions")
    check([int(n) for n in questions] == list(range(1, len(questions) + 1)), "questions numbered consecutively")
    for pattern in (r"\bCO2\b", r"\bCH4\b", r"umol", r"m-2 s-1"):
        check(re.search(pattern, markdown) is None, f"chemistry and units are typeset, not written as {pattern}")

    figs = sorted((OPERATIONAL / "figures").glob("figure_O*.png")) + \
        sorted((OPERATIONAL / "figures").glob("map_M*.png"))
    check(len(figs) == 10, "four operational figures and six maps")
    check(sum(1 for p in figs if p.name.startswith("map_")) == 6, "the spatial claims are carried by maps")
    for path in figs:
        with Image.open(path) as im:
            check(im.width >= 2100 and im.height >= 1000, f"publication raster size {path.stem}")
        check(path.with_suffix(".pdf").is_file(), f"vector companion {path.stem}")
        check(path.name in markdown, f"figure referenced {path.stem}")

    pdf = ROOT / f"outputs/{STEM}.pdf"
    info = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
    check("A4" in info, "PDF uses A4 pages")
    text = subprocess.check_output(["pdftotext", str(pdf), "-"], text=True)
    check("{{" not in text, "no unresolved tokens in the PDF")
    # the title block is escaped like any other text, so a LaTeX command written
    # into it prints verbatim. That reached a delivered first page once
    leaked = re.findall(r"\\[a-zA-Z]+\{", text)
    check(not leaked, f"no raw LaTeX in the rendered PDF (found {sorted(set(leaked))[:3]})")
    first = subprocess.check_output(["pdftotext", "-f", "1", "-l", "1", str(pdf), "-"], text=True)
    check("CO2" in first and "CH4" in first, "the title page names both gases as typeset formulas")
    log = (ROOT / f"outputs/latex/{STEM}.log").read_text()
    check(not any(p in log for p in ("Overfull", "Undefined control sequence", "Fatal error")), "clean typesetting")

    pages = int(re.search(r"Pages:\s+(\d+)", info)[1])
    result = dict(status="passed", checks=len(checks), pages=pages, document=STEM)
    pd.DataFrame(checks).to_csv(OPERATIONAL / "report_validation_checks.csv", index=False)
    (OPERATIONAL / "report_validation.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2))
