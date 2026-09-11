#!/usr/bin/env python3
"""Acquire bounded, provenance-preserving EDGAR and boundary inputs."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import time
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/bkt_sources"


def get(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=90) as response:
        return response.read()


class RangeReader(io.RawIOBase):
    """Seekable HTTP byte ranges: extract one year without downloading decades."""
    def __init__(self, url: str):
        self.url, self.position = url, 0
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=60) as r:
            self.size = int(r.headers["Content-Length"])
            self.etag = r.headers.get("ETag")
        self.downloaded = 0

    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.position
    def seek(self, offset, whence=0):
        self.position = offset if whence == 0 else self.position + offset if whence == 1 else self.size + offset
        if self.position < 0: raise ValueError("Negative remote seek")
        return self.position

    def read(self, size=-1):
        size = self.size - self.position if size < 0 else min(size, self.size - self.position)
        if size <= 0: return b""
        def block(bounds):
            start, stop = bounds
            cache = DATA / "edgar_v8/range_cache" / hashlib.sha256(
                f"{self.url}|{self.etag}|{start}|{stop}".encode()).hexdigest()
            if cache.exists() and cache.stat().st_size == stop-start:
                return cache.read_bytes()
            request = urllib.request.Request(self.url, headers={
                "Range": f"bytes={start}-{stop-1}", "If-Match": self.etag})
            for attempt in range(4):
                try:
                    with urllib.request.urlopen(request, timeout=120) as response:
                        if response.status != 206:
                            raise RuntimeError("Source does not honor byte ranges; refusing full archive")
                        value = response.read()
                    break
                except (TimeoutError, urllib.error.URLError):
                    if attempt == 3: raise
                    time.sleep(2**attempt)
            if len(value) != stop-start: raise RuntimeError("Incomplete source range")
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_bytes(value)
            return value
        ranges = [(start, min(start+1024**2, self.position+size))
                  for start in range(self.position, self.position+size, 1024**2)]
        with ThreadPoolExecutor(max_workers=8) as pool:
            value = b"".join(pool.map(block, ranges))
        if len(value) != size: raise RuntimeError("Incomplete HTTP range")
        self.position += size
        self.downloaded += size
        return value


def provenance(path: Path, url: str, **extra) -> dict:
    record = dict(source_url=url, filename=path.name, bytes=path.stat().st_size,
                  sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  retrieved_at_utc=datetime.now(timezone.utc).isoformat(), **extra)
    path.with_suffix(path.suffix + ".json").write_text(json.dumps(record, indent=2) + "\n")
    return record


def edgar() -> None:
    directory = DATA / "edgar_v8"
    directory.mkdir(parents=True, exist_ok=True)
    page_url = "https://edgar.jrc.ec.europa.eu/dataset_ghg80"
    page = get(page_url).decode("utf-8-sig")
    (directory / "source_page.html").write_text(page)
    urls = sorted(set(re.findall(r'https://jeodpp[^"\s<>]+/monthly/(?:CH4|CO2)/[^"\s<>]+_flx_nc.zip', page)))
    if len(urls) != 16: raise ValueError(f"Expected 8 monthly sectors per gas, found {len(urls)}")
    for url in urls:
        gas = url.split("/monthly/")[1].split("/")[0]
        sector = url.rsplit("/", 1)[1].replace("_flx_nc.zip", "")
        target = directory / f"{gas}_{sector}_2019.nc"
        if target.exists() and target.with_suffix(".nc.json").exists():
            print(f"Already acquired {target.name}", flush=True)
            continue
        remote = RangeReader(url)
        with zipfile.ZipFile(remote) as archive:
            names = [n for n in archive.namelist() if "2019" in n and n.endswith(".nc")]
            if len(names) != 1: raise ValueError(f"Unexpected 2019 members: {names}")
            info = archive.getinfo(names[0])
            target.write_bytes(archive.read(names[0]))  # zipfile verifies CRC-32.
        provenance(target, url, provider="European Commission JRC / IEA-EDGAR",
                   dataset="EDGAR v8.0 monthly fluxes", gas=gas, sector=sector,
                   year=2019, archive_member=names[0], archive_crc32=info.CRC,
                   archive_etag=remote.etag, archive_bytes=remote.size,
                   transferred_bytes=remote.downloaded, documentation=page_url)
        print(f"Acquired {target.name}: {remote.downloaded/1e6:.1f} MB transferred", flush=True)


def boundaries(countries=("MYS", "SGP", "THA", "BRN", "VNM", "KHM", "MMR", "PHL")) -> None:
    directory = DATA / "boundaries"
    directory.mkdir(parents=True, exist_ok=True)
    for iso in countries:
        target = directory / f"geoBoundaries-{iso}-ADM0.geojson"
        if target.exists() and target.with_suffix(".geojson.json").exists(): continue
        api = f"https://www.geoboundaries.org/api/current/gbOpen/{iso}/ADM0/"
        metadata = json.loads(get(api))
        url = metadata["gjDownloadURL"]
        target.write_bytes(get(url))
        # A Git-LFS pointer is not a GeoJSON download.
        parsed = json.loads(target.read_text())
        if parsed.get("type") != "FeatureCollection": raise ValueError("Invalid country geometry")
        provenance(target, url, provider="geoBoundaries gbOpen", api_url=api,
                   boundary_metadata=metadata)
        print(f"Acquired detailed {iso} boundary", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["edgar", "boundaries"])
    args = parser.parse_args()
    edgar() if args.stage == "edgar" else boundaries()
