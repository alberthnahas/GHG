#!/usr/bin/env python3
"""Acquire public inputs for a single, record-long background (boundary) method.

The BKT/JMB inversions need the mole fraction of the air entering the domain.
CarbonTracker supplies it only in pieces (CT-NRT.v2025-1 to Dec 2024, CT2026 to
Dec 2025 for CO2; CT-CH4-2025 to Dec 2023 for CH4), so no single CarbonTracker
release spans 2004 to Nov 2026.  This script records what each candidate source
holds today (stage ``discover``) and downloads the small public inputs that the
candidate backgrounds in a147/a148 are built from.

Stages
  discover  list the CarbonTracker, NOAA MBL, trend and site servers; write
            outputs/background/candidate_inventory.csv (no large transfers)
  noaa      NOAA GML MBL surface reference (CO2, CH4; 41 sine-latitude bins,
            48 steps per year), global and Mauna Loa means, and flask/in-situ
            monthly series for upwind sites (small text files)
  ct        CarbonTracker fields not yet on disk, for the inflow-box comparison:
            CT-NRT.v2025-1 monthly CO2 2021-2024 (9 MB each) and CT-CH4-2025
            daily files for the 15th of Jan/Apr/Jul/Oct 2020-2022 (36 MB each);
            rate limited
  cams      CAMS global greenhouse gas forecasts (ADS), 15th of each month
            00 UTC, lead 0 h, 950 and 700 hPa, inflow area only, via cdsapi
            with the user's existing configuration (never read here)

Every file lands in data/bkt_sources/background/<source>/ beside a .json record
(source_url, sha256, bytes, retrieved_at_utc).  Existing files are never
overwritten.  Times are UTC.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data/bkt_sources/background"
OUT = ROOT / "outputs/background"
GML = "https://gml.noaa.gov"
CT = f"{GML}/aftp/products/carbontracker"
MBL_FORM = f"{GML}/ccgg/mbl/ghg.php"
RATE = "2M"  # curl --limit-rate; a separate ERA5 transfer shares the link

TRENDS = {  # NOAA GML trend products (global from the MBL network; MLO in situ)
    "co2_mm_gl.txt": "co2", "co2_trend_gl.txt": "co2", "co2_mm_mlo.txt": "co2",
    "co2_weekly_mlo.txt": "co2", "ch4_mm_gl.txt": "ch4",
}
# Upwind or tropical reference sites (NOAA CCGG flask monthly means), plus MLO/SMO in situ.
FLASK_SITES = ("sey", "cgo", "smo", "mlo", "gmi", "asc", "chr", "rpb", "mid", "kum")
INSITU_SITES = ("smo", "mlo")
CAMS_AREA = [25, 60, -30, 150]  # N, W, S, E: covers every terminal endpoint latitude band used here
CAMS_LEVELS = ["950", "700"]


# ------------------------------------------------------------------ helpers
def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def provenance(path: Path, url: str, **extra) -> dict:
    record = dict(source_url=url, filename=path.name, bytes=path.stat().st_size, sha256=sha256(path),
                  retrieved_at_utc=datetime.now(timezone.utc).isoformat(), **extra)
    path.with_suffix(path.suffix + ".json").write_text(json.dumps(record, indent=2) + "\n")
    return record


def curl_text(url: str, timeout: int = 120) -> str:
    r = subprocess.run(["curl", "-s", "-f", "-L", "--max-time", str(timeout), url], capture_output=True)
    if r.returncode:
        raise RuntimeError(f"curl failed ({r.returncode}) for {url}")
    return r.stdout.decode("utf-8", "replace")


def fetch(url: str, path: Path, rate: str | None = RATE, **extra) -> str:
    """Download once; never overwrite a file that already has a provenance record."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.with_suffix(path.suffix + ".json").exists():
        return "cached"
    part = path.with_suffix(path.suffix + ".part")
    cmd = ["curl", "-s", "-f", "-L", "--retry", "4", "--max-time", "3600", "-o", str(part), url]
    if rate:
        cmd[1:1] = ["--limit-rate", rate]
    if subprocess.run(cmd).returncode or not part.exists():
        part.unlink(missing_ok=True)
        return "failed"
    part.rename(path)
    provenance(path, url, **extra)
    return "downloaded"


def listing(url: str) -> list[str]:
    return re.findall(r'<a href="([^"?/][^"]*)">', curl_text(url))


# ------------------------------------------------------------------ discover
def discover() -> pd.DataFrame:
    rows = []

    def add(candidate, product, exists, first, last, access, note=""):
        rows.append(dict(candidate=candidate, product=product, exists=exists, first=first, last=last,
                         access=access, note=note, checked_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")))

    co2 = listing(f"{CT}/co2/")
    nrt = sorted(d for d in co2 if d.startswith("CT-NRT.v"))
    rel = sorted(d for d in co2 if re.fullmatch(r"CT20\d\d[A-Z]?/", d))
    add("1 CarbonTracker", "CO2 releases listed", True, rel[0], rel[-1], CT + "/co2/", f"NRT versions: {', '.join(nrt[-4:])}")
    for name in ("CT-NRT", "CT2026"):
        files = listing(f"{CT}/co2/{name}/molefractions/co2_total/")
        days = sorted(re.findall(r"glb3x2_(\d{4}-\d{2}-\d{2})\.nc$", "\n".join(files), re.M))
        add("1 CarbonTracker", f"{name} co2_total glb3x2 daily", bool(days), days[0] if days else "", days[-1] if days else "",
            f"{CT}/co2/{name}/molefractions/co2_total/", "CT-NRT symlink resolves to v2025-1" if name == "CT-NRT" else "")
    monthly = re.findall(r"glb3x2_(\d{4}-\d{2})\.nc$", "\n".join(listing(f"{CT}/co2/CT-NRT/molefractions/co2_total_monthly/")), re.M)
    add("1 CarbonTracker", "CT-NRT.v2025-1 co2_total_monthly glb3x2", bool(monthly), min(monthly), max(monthly),
        f"{CT}/co2/CT-NRT/molefractions/co2_total_monthly/", "9 MB per month")
    ch4 = listing(f"{CT}/ch4/")
    years = sorted(y.strip("/") for y in listing(f"{CT}/ch4/CT-CH4-2025/molefractions/") if re.fullmatch(r"\d{4}/", y))
    last_month = sorted(listing(f"{CT}/ch4/CT-CH4-2025/molefractions/{years[-1]}/"))[-1].strip("/")
    last_day = sorted(listing(f"{CT}/ch4/CT-CH4-2025/molefractions/{years[-1]}/{last_month}/"))[-1]
    add("1 CarbonTracker", "CT-CH4-2025 molefrac glb3x2 daily", True, years[0], last_day, f"{CT}/ch4/CT-CH4-2025/",
        f"CH4 releases: {', '.join(d.strip('/') for d in ch4 if d.startswith('CT-CH4'))}; no CH4 beyond 2023")

    for gas in ("CO2", "CH4"):
        page = curl_text(f"{MBL_FORM}?hidden=true&param={gas}&reference_type=surface&reference=global"
                         f"&startyear=2025&startmonth=1&endyear=2026&endmonth=12")
        link = re.search(r"href='(tmp/[^']+_surface\.txt)'", page).group(1)
        text = curl_text(f"{GML}/ccgg/mbl/{link}")
        last = [ln for ln in text.splitlines() if ln and not ln.startswith("#")][-1].split()[0]
        add("2 NOAA MBL reference", f"{gas} MBL surface (sine-latitude x 48 per year)", True, "1979", f"decimal year {last}",
            MBL_FORM, "web form caps the end year at 2025; asking for 2026 returns the same end")
    for name, gas in TRENDS.items():
        rows_ = [ln.split() for ln in curl_text(f"{GML}/aftp/products/trends/{gas}/{name}").splitlines() if ln and not ln.startswith("#")]
        add("2 NOAA global/MLO means", name, True, " ".join(rows_[0][:2]), " ".join(rows_[-1][:3]), f"{GML}/aftp/products/trends/{gas}/")
    for site in FLASK_SITES:
        for gas in ("co2", "ch4"):
            url = f"{GML}/aftp/data/trace_gases/{gas}/flask/surface/txt/{gas}_{site}_surface-flask_1_ccgg_month.txt"
            try:
                rows_ = [ln.split() for ln in curl_text(url).splitlines() if ln and not ln.startswith("#")]
                add("3 upwind surface sites", f"{gas} {site.upper()} flask monthly", True, " ".join(rows_[0][1:3]), " ".join(rows_[-1][1:3]), url)
            except RuntimeError:
                add("3 upwind surface sites", f"{gas} {site.upper()} flask monthly", False, "", "", url)
    for site in INSITU_SITES:
        for gas in ("co2", "ch4"):
            url = f"{GML}/aftp/data/trace_gases/{gas}/in-situ/surface/txt/{gas}_{site}_surface-insitu_1_ccgg_DailyData.txt"
            tail = subprocess.run(["curl", "-s", "-r", "-300", url], capture_output=True).stdout.decode().splitlines()[-1].split()
            add("3 upwind surface sites", f"{gas} {site.upper()} in situ daily", True, "", " ".join(tail[1:4]), url)

    # CAMS: public catalogue metadata only (no credentials involved here)
    for ds in ("cams-global-greenhouse-gas-forecasts", "cams-global-greenhouse-gas-inversion", "cams-global-ghg-reanalysis-egg4"):
        meta = json.loads(curl_text(f"https://ads.atmosphere.copernicus.eu/api/catalogue/v1/collections/{ds}"))
        (a, b), = meta["extent"]["temporal"]["interval"]
        add("4 CAMS (ADS)", ds, True, a[:10], b[:10], "cdsapi, ADS url, user's existing configuration",
            "licence CC-BY-4.0; retrieval tested 2026-11-15 (see cams stage)" if "forecasts" in ds else "licence CC-BY-4.0")
    try:
        import ee
        ee.Initialize(project="ee-alberthnahas")
        col = ee.ImageCollection("ECMWF/CAMS/NRT")
        bands = col.filterDate("2026-11-01", "2026-11-02").first().bandNames().getInfo()
        ghg = [b for b in bands if "methane" in b or "carbon_dioxide" in b]
        add("4 CAMS (Earth Engine)", "ECMWF/CAMS/NRT", True, "", ee.Date(col.aggregate_max("system:time_start")).format("YYYY-MM-dd").getInfo(),
            "Earth Engine", f"{len(bands)} bands; greenhouse-gas bands: {ghg or 'none'}; no CO2 and no surface CH4 mole fraction")
    except Exception as exc:  # noqa: BLE001
        add("4 CAMS (Earth Engine)", "ECMWF/CAMS/NRT", False, "", "", "Earth Engine", f"probe failed: {type(exc).__name__}")
    table = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUT / "candidate_inventory.csv", index=False)
    print(table.to_string(), flush=True)
    return table


# ------------------------------------------------------------------ noaa
def noaa() -> None:
    for gas in ("CO2", "CH4"):
        target = DATA / "mbl" / f"{gas.lower()}_GHGreference_surface_2000_2025.txt"
        if target.exists():
            continue
        query = f"{MBL_FORM}?hidden=true&param={gas}&reference_type=surface&reference=global&startyear=2000&startmonth=1&endyear=2025&endmonth=12"
        link = re.search(r"href='(tmp/[^']+_surface\.txt)'", curl_text(query, 300)).group(1)
        url = f"{GML}/ccgg/mbl/{link}"
        print(gas, fetch(url, target, rate=None, form_query=query, provider="NOAA GML",
                         dataset="NOAA Greenhouse Gas Marine Boundary Layer Reference (surface)",
                         citation="Lan, Tans, Thoning and NOAA GML, doi:10.15138/DVNP-F961"), flush=True)
    for name, gas in TRENDS.items():
        print(name, fetch(f"{GML}/aftp/products/trends/{gas}/{name}", DATA / "trends" / name, rate=None, provider="NOAA GML"), flush=True)
    for site in FLASK_SITES:
        for gas in ("co2", "ch4"):
            for kind in ("month", "event"):
                name = f"{gas}_{site}_surface-flask_1_ccgg_{kind}.txt"
                url = f"{GML}/aftp/data/trace_gases/{gas}/flask/surface/txt/{name}"
                print(name, fetch(url, DATA / "sites" / name, rate=None, provider="NOAA GML CCGG flask"), flush=True)
    for site in INSITU_SITES:
        for gas in ("co2", "ch4"):
            name = f"{gas}_{site}_surface-insitu_1_ccgg_DailyData.txt"
            url = f"{GML}/aftp/data/trace_gases/{gas}/in-situ/surface/txt/{name}"
            print(name, fetch(url, DATA / "sites" / name, rate=None, provider="NOAA GML CCGG in situ"), flush=True)


# ------------------------------------------------------------------ ct
def ct() -> None:
    jobs = []
    for month in pd.date_range("2021-01-01", "2024-12-01", freq="MS"):
        name = f"CT-NRT.v2025-1.molefrac_glb3x2_{month:%Y-%m}.nc"
        jobs.append((f"{CT}/co2/CT-NRT.v2025-1/molefractions/co2_total_monthly/{name}", DATA / "ct_nrt_monthly" / name,
                     dict(provider="NOAA GML", dataset="CarbonTracker CT-NRT.v2025-1 monthly mean mole fractions")))
    for year in (2020, 2021, 2022):
        for month in (1, 4, 7, 10):
            day = pd.Timestamp(year=year, month=month, day=15)
            name = f"CTCH4_2025.molefrac_glb3x2_{day:%Y-%m-%d}.nc"
            jobs.append((f"{CT}/ch4/CT-CH4-2025/molefractions/{day:%Y/%m}/{name}", DATA / "ctch4_sample" / name,
                         dict(provider="NOAA GML", dataset="CarbonTracker-CH4 2025 daily mole fractions")))
    # CT2026 on days CT-NRT.v2025-1 also covers: tests the release-to-release step seen at the
    # 2024/2025 join (CT2026 is 4 to 6 ppm higher than CT-NRT over the South China Sea in late Dec 2024)
    for day in pd.to_datetime(["2024-01-15", "2024-04-15", "2024-07-15", "2024-10-15", "2024-12-15"]):
        name = f"CT2026.molefrac_glb3x2_{day:%Y-%m-%d}.nc"
        jobs.append((f"{CT}/co2/CT2026/molefractions/co2_total/{name}", DATA / "ct2026_sample" / name,
                     dict(provider="NOAA GML", dataset="CarbonTracker CT2026 daily mole fractions")))
    with ThreadPoolExecutor(max_workers=2) as pool:
        for (url, path, extra), status in zip(jobs, pool.map(lambda j: fetch(j[0], j[1], **j[2]), jobs)):
            print(path.name, status, flush=True)


# ------------------------------------------------------------------ cams
def cams(workers: int = 4) -> None:
    import cdsapi  # configuration is read by the library; this script never opens it
    client = cdsapi.Client(url="https://ads.atmosphere.copernicus.eu/api", quiet=True, progress=False)
    directory = DATA / "cams_ghg_forecast"
    directory.mkdir(parents=True, exist_ok=True)
    days = [pd.Timestamp(y, m, 15) for y, m in
            ((t.year, t.month) for t in pd.period_range("2024-03", "2026-11", freq="M"))]
    days = [d for d in days if d <= pd.Timestamp("2026-11-14")]

    def one(day: pd.Timestamp) -> str:
        target = directory / f"cams_ghg_fc_{day:%Y%m%d}T00_lead0_950_700hPa.grib"
        if target.exists() and target.with_suffix(".grib.json").exists():
            return f"{target.name} cached"
        request = {"variable": ["carbon_dioxide", "methane"], "pressure_level": CAMS_LEVELS,
                   "date": f"{day:%Y-%m-%d}/{day:%Y-%m-%d}", "leadtime_hour": ["0"], "area": CAMS_AREA, "data_format": "grib"}
        for attempt in range(3):
            try:
                part = target.with_suffix(".grib.part")
                client.retrieve("cams-global-greenhouse-gas-forecasts", request).download(str(part))
                part.rename(target)
                provenance(target, "https://ads.atmosphere.copernicus.eu/api/retrieve/v1/processes/cams-global-greenhouse-gas-forecasts",
                           provider="Copernicus Atmosphere Monitoring Service (ECMWF)", dataset="cams-global-greenhouse-gas-forecasts",
                           request=request, licence="CC-BY-4.0")
                return f"{target.name} downloaded"
            except Exception as exc:  # noqa: BLE001
                message = str(exc)[:300]
                time.sleep(30 * (attempt + 1))
        return f"{target.name} FAILED: {message}"

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for status in pool.map(one, days):
            print(status, flush=True)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("stage", choices=["discover", "noaa", "ct", "cams"])
    a = p.parse_args()
    {"discover": discover, "noaa": noaa, "ct": ct, "cams": cams}[a.stage]()


if __name__ == "__main__":
    sys.exit(main())
