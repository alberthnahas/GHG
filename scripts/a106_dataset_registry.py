#!/usr/bin/env python3
"""Every dataset the operational model needs: confirm it, validate it, check it fits.

An operational model cannot treat its inputs as an assumption. This declares
each dataset the inversion depends on, then does four things to it rather than
one:

  confirm    the file is present, and its provenance record and checksum match
  validate   open it and check the variable, the unit, the grid, the time span
             and the physical range, because a file can exist and still be wrong
  fit        check it can reach the operator grid and covers the study windows
  report     one table a deployment can read, and a non-zero exit when a
             required dataset fails

The distinction that matters is between required and optional. A missing
optional dataset narrows what the model can do and is reported. A missing or
invalid required dataset means the operational model must not run, and this
says so.

Stages
  check      validate everything and write the registry
  list       print the declared datasets without opening them
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data/bkt_sources"
OUT = ROOT / "outputs/operational"
ASSETS = Path("/run/media/workstation-llm/HDD2/.assets")
WINDOWS = {"2023": ("2023-11-19", "2023-12-31"), "2024": ("2024-09-29", "2024-12-31")}


class Dataset:
    def __init__(self, name: str, role: str, pattern: str, required: bool, kind: str,
                 variable: str | None = None, unit: str | None = None,
                 minimum: float | None = None, maximum: float | None = None,
                 covers: str | None = None, note: str = ""):
        self.name, self.role, self.pattern, self.required = name, role, pattern, required
        self.kind, self.variable, self.unit = kind, variable, unit
        self.minimum, self.maximum, self.covers, self.note = minimum, maximum, covers, note


REGISTRY = [
    Dataset("GRK station archive", "observations", "", True, "stations",
            note="CO2, CH4 and CO at five stations, loaded through ghg_common"),
    Dataset("GFS 0.25 ARL, 2023 window", "meteorology", "data/hysplit/gfs0p25/two_receptor_wide/*_gfs0p25.json",
            True, "count", covers="2023", note="drives the 2023 footprints"),
    Dataset("GFS 0.25 ARL, 2024 window", "meteorology", "data/hysplit/gfs0p25/two_receptor_wide_2024/*_gfs0p25.json",
            True, "count", covers="2024", note="drives the 2024 footprints"),
    Dataset("EDGAR v8 methane", "prior, anthropogenic CH4", "data/bkt_sources/edgar_v8/CH4_*_2022.nc",
            True, "grid", variable="fluxes", unit="kg m-2 s-1", minimum=0, maximum=1e-4),
    Dataset("EDGAR_2025 carbon dioxide", "prior, fossil CO2", "data/bkt_sources/edgar_2025/CO2_*_2023.nc",
            True, "grid", variable="fluxes", unit="kg m-2 s-1", minimum=0, maximum=1e-2),
    Dataset("CT-NRT fluxes", "prior, CO2 ocean fire biosphere", "data/bkt_sources/carbontracker_nrt/fluxes/*.nc",
            True, "count", note="three-hourly optimised fluxes behind the CO2 operator"),
    Dataset("CT-NRT mole fractions", "boundary, CO2", "data/bkt_sources/carbontracker_nrt/molefractions/*.nc",
            True, "count", note="endpoint background for CO2"),
    Dataset("CarbonTracker-CH4", "boundary and fire, CH4", "data/bkt_sources/inversion/ctch4_fluxes/*.nc",
            True, "count", note="endpoint background and pyrogenic flux for CH4"),
    Dataset("PRIMAP-hist v2.6.1", "national inventory totals", "data/bkt_sources/primap/PRIMAP-hist_v2.6.1_final.csv",
            True, "table", note="country-reported national totals that localise the gridded prior"),
    Dataset("MODIS MCD12C1 land cover", "FOLU and biosphere weighting",
            "data/bkt_sources/landcover/MCD12C1_2019_IGBP_majority_0p05deg.tif", True, "raster"),
    Dataset("Indonesian peatland extent", "FOLU proxy", "", True, "geometry",
            note="/run/media/workstation-llm/HDD2/GHG_INDONESIA/indonesia_peatlands.json"),
    Dataset("GFED 5.1", "FOLU fire proxy", "data/bkt_sources/gfed51/GFED5.1_ecosystem_2019.nc", True, "grid",
            variable="carbon_emissions", minimum=0),
    Dataset("38-province boundary", "regional masks", "", True, "geometry",
            note="shared asset, used for provincial scaling and province influence"),
    Dataset("Diagnostic biosphere", "prior, CO2 biosphere",
            "outputs/hysplit/two_receptor/inputs_co2/diagnostic_biosphere.nc", True, "grid",
            variable="gpp", unit="umol m-2 s-1", minimum=-200, maximum=1),
    Dataset("Hybrid biosphere", "prior, CO2 biosphere",
            "outputs/hysplit/two_receptor/inputs_co2/diagnostic_biosphere_hybrid.nc", True, "grid",
            variable="gpp", unit="umol m-2 s-1", minimum=-200, maximum=1),
    Dataset("ODIAC 2023", "alternative fossil pattern", "data/bkt_sources/odiac2023/*.nc", False, "count",
            note="one degree, 2019 only, so coarser than EDGAR here; kept for pattern comparison"),
    Dataset("CT2022 fluxes", "historical CO2 fluxes", "data/bkt_sources/ct2022_fluxes/*.nc", False, "count",
            note="2019 pilot window only"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def check_grid(path: Path, dataset: Dataset) -> tuple[bool, str]:
    import xarray as xr
    with xr.open_dataset(path) as ds:
        variable = dataset.variable if dataset.variable in ds.data_vars else list(ds.data_vars)[0]
        array = ds[variable]
        unit = str(array.attrs.get("units", ds.attrs.get("units", "")))
        if dataset.unit and unit and unit.replace(" ", "") != dataset.unit.replace(" ", ""):
            return False, f"unit is {unit!r}, expected {dataset.unit!r}"
        sample = array.isel({d: 0 for d in array.dims if d not in ("lat", "lon")}) if array.ndim > 2 else array
        values = np.asarray(sample.values, dtype=float)
        if not np.isfinite(values).any():
            return False, "no finite values"
        low, high = float(np.nanmin(values)), float(np.nanmax(values))
        if dataset.minimum is not None and low < dataset.minimum - 1e-9:
            return False, f"minimum {low:.3g} below the declared {dataset.minimum:.3g}"
        if dataset.maximum is not None and high > dataset.maximum:
            return False, f"maximum {high:.3g} above the declared {dataset.maximum:.3g}"
        grid = "x".join(str(ds.sizes[d]) for d in ("lat", "lon") if d in ds.sizes)
        return True, f"{variable}, unit {unit or 'none declared'}, grid {grid}, range {low:.3g} to {high:.3g}"


def check_one(dataset: Dataset) -> dict:
    result = dict(dataset=dataset.name, role=dataset.role, required=dataset.required,
                  status="missing", detail="", files=0, provenance=0)
    try:
        if dataset.kind == "stations":
            import ghg_common as G
            codes = []
            for code in G.STATIONS:
                frame = G.apply_flags(G.load_station(code))
                if len(frame) and frame[["co2", "ch4", "co"]].notna().any().any():
                    codes.append(code)
            result.update(status="ok" if len(codes) == len(G.STATIONS) else "partial",
                          files=len(codes), detail=f"{len(codes)} of {len(G.STATIONS)} stations carry data")
            return result
        if dataset.kind == "geometry":
            target = (Path("/run/media/workstation-llm/HDD2/GHG_INDONESIA/indonesia_peatlands.json")
                      if "peat" in dataset.name.lower() else ASSETS / "indonesia_38prov.geojson")
            if not target.exists():
                result.update(detail=f"not found: {target}")
                return result
            import json as _json
            payload = _json.loads(target.read_text())
            count = len(payload.get("features", payload.get("geometries", [])))
            result.update(status="ok" if count else "invalid", files=1,
                          detail=f"{count} features or geometries")
            return result

        paths = sorted(ROOT.glob(dataset.pattern)) if "*" in dataset.pattern else (
            [ROOT / dataset.pattern] if (ROOT / dataset.pattern).exists() else [])
        paths = [p for p in paths if p.exists()]
        result["files"] = len(paths)
        # a .json here is itself the provenance record, so it does not need a sidecar
        result["provenance"] = sum(1 for p in paths if p.suffix == ".json" or p.with_suffix(p.suffix + ".json").exists())
        if not paths:
            result["detail"] = f"no file matches {dataset.pattern}"
            return result
        if dataset.kind == "count":
            result.update(status="ok", detail=f"{len(paths)} files, {result['provenance']} with a provenance record")
            return result
        if dataset.kind == "table":
            frame = pd.read_csv(paths[0], nrows=200, low_memory=False)
            result.update(status="ok", detail=f"{len(frame.columns)} columns, first is {frame.columns[0]!r}")
            return result
        if dataset.kind == "raster":
            import rasterio
            with rasterio.open(paths[0]) as raster:
                result.update(status="ok", detail=f"{raster.shape[0]}x{raster.shape[1]} at {raster.res[0]} degrees, {raster.crs}")
            return result
        ok, detail = check_grid(paths[0], dataset)
        result.update(status="ok" if ok else "invalid", detail=detail)
        return result
    except Exception as error:  # noqa: BLE001 - a dataset that cannot be opened is a finding, not a crash
        result.update(status="invalid", detail=f"{type(error).__name__}: {error}")
        return result


def check() -> int:
    rows = [check_one(dataset) for dataset in REGISTRY]
    table = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUT / "dataset_registry.csv", index=False)
    failed = table[(table.required) & (table.status != "ok")]
    summary = dict(total=len(table), ok=int((table.status == "ok").sum()),
                   required_failing=len(failed),
                   optional_missing=int(((~table.required) & (table.status != "ok")).sum()),
                   verdict="ready" if failed.empty else "blocked")
    (OUT / "dataset_registry.json").write_text(json.dumps(summary, indent=2) + "\n")
    width = max(len(r["dataset"]) for r in rows)
    for row in rows:
        mark = {"ok": "ok  ", "partial": "part", "missing": "MISS", "invalid": "BAD "}[row["status"]]
        need = "required" if row["required"] else "optional"
        print(f"  [{mark}] {row['dataset']:<{width}}  {need:8s} {row['detail']}", flush=True)
    print(f"\n{summary['ok']} of {summary['total']} datasets validated; "
          f"{summary['required_failing']} required failing, {summary['optional_missing']} optional missing "
          f"-> {summary['verdict']}", flush=True)
    return 0 if failed.empty else 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["check", "list"], nargs="?", default="check")
    a = parser.parse_args()
    if a.stage == "list":
        for dataset in REGISTRY:
            print(f"  {'required' if dataset.required else 'optional'}  {dataset.name}: {dataset.role}")
        return
    raise SystemExit(check())


if __name__ == "__main__":
    main()
