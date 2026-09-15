#!/usr/bin/env python3
"""Record which input products cover the BKT + Jambi joint windows.

Metadata-only probes: HTTP directory listings, HEAD requests, zip central
directories and netCDF4 headers read through byte ranges. No data arrays are
downloaded. Writes outputs/hysplit/two_receptor/tables/dataset_availability.csv.
"""
from __future__ import annotations
import argparse
import io
import re
import socket
import urllib.request
import zipfile
from datetime import datetime, timezone

import h5py
import pandas as pd

import a84_bkt_jmb_two_receptor as T

EDGAR_V8 = "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/v80_FT2022_GHG/monthly/CH4/WASTE/WASTE_flx_nc.zip"
EDGAR_2025 = "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/EDGAR_2025_GHG/monthly/CH4/bkl_{s}/bkl_{s}_flx_nc.zip"
SECTORS = ("AGRICULTURE", "BUILDINGS", "FUEL_EXPLOITATION", "IND_COMBUSTION", "IND_PROCESSES", "POWER_INDUSTRY", "TRANSPORT", "WASTE")
CT = "https://gml.noaa.gov/aftp/products/carbontracker"
NRT = f"{CT}/co2/CT-NRT.v2025-1/molefractions/co2_total"
GFS = "https://noaa-oar-arl-hysplit-pds.s3.amazonaws.com/gfs0p25"


def bind(device: str) -> None:
    original = socket.socket.connect
    def connect(self, address):
        if self.family == socket.AF_INET and self.type == socket.SOCK_STREAM:
            self.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, device.encode())
        return original(self, address)
    socket.socket.connect = connect


class Remote(io.RawIOBase):
    """Seekable HTTP byte-range reader with a transfer counter."""
    def __init__(self, url: str, block: int = 1 << 18):
        self.url, self.pos, self.block, self.cache, self.fetched = url, 0, block, {}, 0
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=60) as r:
            self.size = int(r.headers["Content-Length"])
    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos
    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else self.pos + off if whence == 1 else self.size + off
        return self.pos
    def _block(self, i):
        if i not in self.cache:
            start = i * self.block; stop = min(start + self.block, self.size) - 1
            with urllib.request.urlopen(urllib.request.Request(self.url, headers={"Range": f"bytes={start}-{stop}"}), timeout=120) as r:
                self.cache[i] = r.read()
            self.fetched += len(self.cache[i])
        return self.cache[i]
    def readinto(self, b):
        n = min(len(b), self.size - self.pos)
        if n <= 0: return 0
        out = bytearray()
        while len(out) < n:
            i, off = divmod(self.pos + len(out), self.block)
            out += self._block(i)[off:off + n - len(out)]
        b[:n] = out[:n]; self.pos += n
        return n


def listing(url: str, pattern: str) -> list[str]:
    with urllib.request.urlopen(url, timeout=60) as r:
        return sorted(set(re.findall(pattern, r.read().decode("utf-8", "replace"))))


def head_status(url: str) -> int:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=60) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def zip_years(url: str) -> tuple[list[int], dict[int, int], int]:
    remote = Remote(url)
    with zipfile.ZipFile(remote) as z:
        members = [m for m in z.infolist() if m.filename.endswith(".nc")]
    years = sorted(int(re.search(r"_CH4_(\d{4})_", m.filename)[1]) for m in members)
    sizes = {int(re.search(r"_CH4_(\d{4})_", m.filename)[1]): m.compress_size for m in members}
    return years, sizes, remote.fetched


def main(interface: str | None) -> None:
    if interface:
        bind(interface)
    rows = []
    def row(**k):
        rows.append(dict(checked_utc=datetime.now(timezone.utc).strftime("%Y-%m-%d"), **k)); print(rows[-1], flush=True)

    years, _, fetched = zip_years(EDGAR_V8)
    row(product="EDGAR v8.0 monthly CH4 fluxes (used)", role="anthropogenic prior", species="CH4",
        first=str(years[0]), last=str(years[-1]), covers_2023=years[-1] >= 2023, covers_2024=years[-1] >= 2024,
        transfer_mb_2023=None, transfer_mb_2024=None, metadata_bytes=fetched, note="WASTE sector archive central directory")
    total = {2023: 0, 2024: 0}; first = last = None; meta = 0
    for sector in SECTORS:
        years, sizes, fetched = zip_years(EDGAR_2025.format(s=sector))
        first, last, meta = years[0], years[-1], meta + fetched
        for y in total: total[y] += sizes[y]
    row(product="EDGAR_2025_GHG monthly CH4 fluxes", role="anthropogenic prior", species="CH4",
        first=str(first), last=str(last), covers_2023=last >= 2023, covers_2024=last >= 2024,
        transfer_mb_2023=round(total[2023] / 1e6, 1), transfer_mb_2024=round(total[2024] / 1e6, 1), metadata_bytes=meta,
        note=f"eight sectors, same names as v8.0; per-year members extracted by range reads")

    files = listing(NRT + "/", r"CT-NRT\.v2025-1\.molefrac_glb3x2_(\d{4}-\d{2}-\d{2})\.nc")
    remote = Remote(f"{NRT}/CT-NRT.v2025-1.molefrac_glb3x2_2024-12-01.nc")
    with h5py.File(remote, "r") as f:
        variables = set(f.keys())
        units = f["co2"].attrs["units"].decode(); shape = f["co2"].shape
        gph = f["gph"].attrs["units"].decode()
    row(product="CarbonTracker CT-NRT.v2025-1 molefractions", role="boundary mole fractions", species="CO2",
        first=files[0], last=files[-1], covers_2023=files[-1] >= "2023-12-31", covers_2024=files[-1] >= "2024-12-31",
        transfer_mb_2023=round(remote.size * 43 / 1e6, 0), transfer_mb_2024=round(remote.size * 36 / 1e6, 0), metadata_bytes=remote.fetched,
        note=f"co2 {units} {shape}, gph {gph}; methane variable present: {'ch4' in variables}; same layout as CT2022")

    for release, used in (("CT-CH4-2023", False), ("CT-CH4-2025", True)):
        years = listing(f"{CT}/ch4/{release}/molefractions/", r'href="(\d{4})/"')
        days = listing(f"{CT}/ch4/{release}/molefractions/{years[-1]}/12/", r"molefrac_glb3x2_(\d{4}-\d{2}-\d{2})\.nc")
        row(product=f"CarbonTracker-CH4 {release[-4:]} molefractions" + (" (used)" if used else ""), role="boundary mole fractions", species="CH4",
            first=years[0], last=days[-1] if days else years[-1], covers_2023=(days[-1] if days else years[-1]) >= "2023-12-31",
            covers_2024=(days[-1] if days else years[-1]) >= "2024-12-31", transfer_mb_2023=None, transfer_mb_2024=None, metadata_bytes=0,
            note="GML release directory listing")
    legacy = listing(f"{CT}/ch4/molefractions/", r'href="(\d{8})\.nc"')
    row(product="CarbonTracker-CH4 unversioned legacy tree", role="boundary mole fractions", species="CH4",
        first=legacy[0], last=legacy[-1], covers_2023=legacy[-1] >= "20231231", covers_2024=legacy[-1] >= "20241231",
        transfer_mb_2023=None, transfer_mb_2024=None, metadata_bytes=0, note="products/carbontracker/ch4/molefractions listing")
    years = listing(f"{CT}/ch4/CT-CH4-2025/fluxes/", r"CTCH4_methane_emis_(\d{4})\.nc")
    row(product="CarbonTracker-CH4 2025 fluxes (fire prior used)", role="fire prior", species="CH4",
        first=years[0], last=years[-1], covers_2023=years[-1] >= "2023", covers_2024=years[-1] >= "2024",
        transfer_mb_2023=None, transfer_mb_2024=None, metadata_bytes=0, note="pyrogenic category")
    status = {y: head_status(f"{T.HEMCO}/v2025-09/LPJ_MERRA2/LPJ_MERRA2_{y}_0.5x0.5.nc") for y in (2023, 2024)}
    row(product="LPJ-MERRA2 wetlands, HEMCO v2025-09 (used)", role="wetland prior", species="CH4",
        first=None, last="2023" if status[2023] == 200 and status[2024] != 200 else "2024" if status[2024] == 200 else None,
        covers_2023=status[2023] == 200, covers_2024=status[2024] == 200, transfer_mb_2023=None, transfer_mb_2024=None, metadata_bytes=0,
        note=f"HTTP status 2023: {status[2023]}, 2024: {status[2024]}")
    status = {y: head_status(f"{GFS}/{y}/12/{y}1231_gfs0p25") for y in (2023, 2024)}
    row(product="NOAA GFS 0.25 ARL archive (used)", role="meteorology", species="none",
        first=None, last=None, covers_2023=status[2023] == 200, covers_2024=status[2024] == 200,
        transfer_mb_2023=None, transfer_mb_2024=None, metadata_bytes=0, note=f"HTTP status 31 Dec 2023: {status[2023]}, 31 Dec 2024: {status[2024]}")
    T.TABLES.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(T.TABLES / "dataset_availability.csv", index=False)
    print("wrote", T.TABLES / "dataset_availability.csv")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--interface", default=None)
    main(p.parse_args().interface)
