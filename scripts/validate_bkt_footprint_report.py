#!/usr/bin/env python3
"""Validate the BKT footprint report, its evidence tables and rendered PDF."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import re
from pathlib import Path

import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN = ROOT / "outputs/hysplit/bkt_20190926T0100Z"
REPORT_MD = ROOT / "BKT_HYSPLIT_STILT_Footprint_Report.md"
REPORT_TEX = ROOT / "outputs/latex/BKT_HYSPLIT_STILT_Footprint_Report.tex"
REPORT_PDF = ROOT / "outputs/BKT_HYSPLIT_STILT_Footprint_Report.pdf"
REPORT_LOG = ROOT / "outputs/latex/BKT_HYSPLIT_STILT_Footprint_Report.log"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def close(actual: float, expected: float, label: str, tolerance: float = 1e-9) -> None:
    require(math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance),
            f"{label}: {actual} != {expected}")


def command_text(command: list[str]) -> str:
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return result.stdout


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--refinement", action="store_true")
    args = parser.parse_args()
    if args.refinement:
        validate_refinement()
        return

    report_dir = args.run_dir.resolve() / "report"
    figure_dir = report_dir / "figures"
    table_dir = report_dir / "tables"
    metrics_path = report_dir / "report_metrics.json"

    required = [REPORT_MD, REPORT_TEX, REPORT_PDF, REPORT_LOG, metrics_path]
    required += [figure_dir / f"figure_{number:02d}_{name}.{suffix}"
                 for number, name in ((1, "workflow"), (2, "observation_context"),
                                      (3, "spatial_footprint"), (4, "lag_sensitivity"),
                                      (5, "sector_distance"))
                 for suffix in ("png", "pdf")]
    required += [table_dir / name for name in (
        "observation_context_summary.csv", "observation_context_hourly.csv",
        "lag_sensitivity_hourly.csv", "lag_sensitivity_6hour.csv",
        "sector_distance_share.csv", "spatial_cell_summary.csv",
        "validation_checks.csv")]
    missing = [str(path) for path in required if not path.is_file()]
    require(not missing, "Missing report artifacts: " + ", ".join(missing))

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    observations = pd.read_csv(table_dir / "observation_context_summary.csv")
    require(len(observations) == 3, "Observation summary must contain three gases")
    for expected in metrics["observation_context"]:
        row = observations.loc[observations["species"] == expected["species"]]
        require(len(row) == 1, f"Missing summary row for {expected['species']}")
        row = row.iloc[0]
        for field in ("receptor_value", "valid_hours", "expected_hours",
                      "coverage_percent", "median", "p25", "p75", "percentile_rank"):
            close(float(row[field]), float(expected[field]),
                  f"{expected['species']} {field}")

    lag = pd.read_csv(table_dir / "lag_sensitivity_hourly.csv")
    require(len(lag) == 72, "Hourly lag table must contain all 72 backward hours")
    close(float(lag["share_percent"].sum()), 100.0, "Lag shares", tolerance=1e-8)
    close(float(lag.iloc[-1]["cumulative_share_percent"]), 100.0,
          "Final cumulative lag share", tolerance=1e-8)

    sectors = pd.read_csv(table_dir / "sector_distance_share.csv")
    close(float(sectors.drop(columns="distance_band_km").to_numpy().sum()), 100.0,
          "Sector-distance shares", tolerance=1e-8)
    checks = pd.read_csv(table_dir / "validation_checks.csv")
    require(len(checks) == metrics["validation_checks_total"],
            "Validation-check count differs from report metrics")
    require(checks["status"].eq("Pass").all(), "A numerical validation check failed")

    markdown = REPORT_MD.read_text(encoding="utf-8")
    headline_strings = (
        "437.09 ppm", "1,922.06 ppb", "531.15 ppb", "84.0th",
        "71.4%", "10.2%", "3.6%", "14.9%", "224 km", "57.7%", "456 km",
        "1,081 km", "39.0%", "36.3%", "24.7%", "32 hours", "60 hours",
        "335 valid measurements from 337 expected hours", "11 of 11")
    absent = [value for value in headline_strings if value not in markdown]
    require(not absent, "Headline values missing from canonical Markdown: " + ", ".join(absent))
    require("[REPORT" not in markdown, "Unresolved report template marker in Markdown")

    for png in sorted(figure_dir.glob("*.png")):
        with Image.open(png) as image:
            require(image.width >= 2000 and image.height >= 1100,
                    f"Figure resolution is too small: {png.name} {image.size}")

    pdfinfo = command_text(["pdfinfo", str(REPORT_PDF)])
    require("Pages:           18" in pdfinfo, "Rendered report must contain 18 pages")
    require("Page size:       595.28 x 841.89 pts (A4)" in pdfinfo,
            "Rendered report is not A4")
    require("Title:           Greenhouse-gas footprint at Bukit Kototabang" in pdfinfo,
            "PDF title metadata missing or incorrect")
    require("Author:          BMKG greenhouse-gas analysis" in pdfinfo,
            "PDF author metadata missing or incorrect")

    extracted = command_text(["pdftotext", str(REPORT_PDF), "-"])
    for phrase in ("Scientific summary", "Results", "Quality assurance",
                   "Limitations", "Technical methods and quality assurance"):
        require(phrase in extracted, f"PDF text is missing section: {phrase}")
    require("[REPORT" not in extracted, "Unresolved report template marker in PDF")

    log = REPORT_LOG.read_text(encoding="utf-8", errors="replace")
    for forbidden in ("Overfull \\hbox", "Undefined control sequence",
                      "Missing character", "Fatal error"):
        require(forbidden not in log, f"LaTeX log contains: {forbidden}")

    output = {
        "status": "pass",
        "validated_report": str(REPORT_PDF),
        "page_count": 18,
        "page_size": "A4",
        "figures": 5,
        "evidence_tables": 7,
        "numerical_checks": int(metrics["validation_checks_total"]),
    }
    output_path = report_dir / "report_validation.json"
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


def validate_refinement() -> None:
    """Validate corrected ensemble, map integral and fully expanded report."""
    import numpy as np
    import xarray as xr
    from a40_bkt_refinement_report import build_report
    from a39_bkt_refinement import MEMBERS, RUNS, STAMP
    from bkt_footprint_spatial import cell_area_km2
    analysis=RUNS/"analysis"
    summary=pd.read_csv(analysis/"tables/experiment_summary.csv",index_col="run")
    expected,_=build_report()
    require(REPORT_MD.read_text()==expected,"Canonical Markdown differs from computed evidence/template")
    for member in MEMBERS:
        result=json.loads((RUNS/member/STAMP/"validation.json").read_text())
        require(result["status"]=="passed",f"Native validation failed: {member}")
    with xr.open_dataset(analysis/"ensemble_mean.nc",engine="h5netcdf") as ds:
        mean=ds.footprint_sensitivity.load()
    require(dict(mean.sizes)=={"time":72,"lat":201,"lon":301},"Incorrect ensemble dimensions")
    require(np.isfinite(mean.values).all() and (mean.values>=0).all(),"Invalid ensemble values")
    close(float(mean.sum()),float(summary.loc["ensemble_mean","sensitivity_sum"]),"Ensemble total")
    # Independent cell-hour sample uses native files and observed particle counts.
    positive=np.argwhere(mean.values>0)
    chosen=positive[np.linspace(0,len(positive)-1,30,dtype=int)]
    direct=np.zeros(len(chosen))
    for member in MEMBERS:
        row=summary.loc[member]
        with xr.open_dataset(RUNS/member/STAMP/"footprint.nc",engine="h5netcdf") as ds:
            native=ds.footprint_sensitivity.values
            direct += native[tuple(chosen.T)].astype(float)*row.requested_particles/row.actual_particles/3
    require(np.allclose(direct,mean.values[tuple(chosen.T)],rtol=1e-12,atol=1e-15),
            "Independent corrected cell-hour reconstruction failed")
    hourly=pd.read_csv(analysis/"ensemble_hourly.csv.gz")
    close(float(hourly.footprint_sensitivity.sum()),float(mean.sum()),"Hourly CSV versus ensemble")
    with xr.open_dataset(analysis/"display_surface.nc",engine="h5netcdf") as ds:
        integral=float((ds.display_sensitivity_density.values*cell_area_km2(ds.lat.values,ds.lon.values)).sum())
    close(integral,float(mean.sum()),"Display density integral",tolerance=1e-10)
    map_meta=json.loads((analysis/"map_metadata.json").read_text())
    require(map_meta["boundary"]["feature_count"]==38,"Unexpected Indonesia asset feature count")
    require(Path(map_meta["boundary"]["asset"]).name=="indonesia_38prov.geojson",
            "The established provincial asset was not used")
    for path in (analysis/"figures").glob("*.png"):
        with Image.open(path) as img:
            require(img.width>=2000 and img.height>=1100,f"Insufficient figure resolution: {path.name}")
        require(path.with_suffix(".pdf").is_file(),f"Missing vector figure: {path.name}")
    require(len(list((analysis/"figures").glob("*.png")))==7,"Expected seven scientific figures")
    info=command_text(["pdfinfo",str(REPORT_PDF)])
    require("595.28 x 841.89 pts (A4)" in info,"Report is not A4")
    require("Greenhouse-gas footprint at Bukit Kototabang" in info,"Missing PDF title")
    require(not re.search(r"^Author:\s*\S",info,re.M),"Unrequested PDF author metadata")
    pages=int(re.search(r"Pages:\s+(\d+)",info)[1])
    text=command_text(["pdftotext",str(REPORT_PDF),"-"])
    for section in ("Scientific summary","Normalization correction","Continuous display reconstruction",
                    "Results","References","Technical methods and quality assurance"):
        require(section in text,f"Missing PDF section: {section}")
    require("{{" not in text,"Unresolved PDF template markers")
    log=REPORT_LOG.read_text(errors="replace")
    for forbidden in ("Overfull \\hbox","Undefined control sequence","Missing character","Fatal error"):
        require(forbidden not in log,f"LaTeX log contains {forbidden}")
    result={"status":"pass","pages":pages,"figures":7,"tables":7,
            "independent_cell_hour_checks":len(chosen),"display_integral":integral,
            "raw_ensemble_total":float(mean.sum()),"boundary_sha256":map_meta["boundary"]["sha256"]}
    (analysis/"report_validation.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__ == "__main__":
    main()
