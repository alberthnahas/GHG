#!/usr/bin/env python3
"""Poster variants of report figures in the Result 5 headline style.

Each variant removes the report's "Figure N" suptitle strip from the rendered
PNG and adds a bold headline plus a one-line grey highlight, matching
``a77_poster_inversion_figure.py``. Plot content is untouched.
"""
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/poster"
DPI = 260
VARIANTS = {
    "f2_flask_validation": ("Independent flasks anchor the continuous record",
        "Same-hour NOAA flask versus in-situ comparisons at Bukit Kototabang for CO₂, CO and CH₄."),
    "f6_diurnal": ("Diurnal cycles separate the five sites by process",
        "Median local-time composites (top) and peak-to-peak amplitudes (bottom) for CO₂, CH₄ and CO."),
    "f12_nocturnal_flux": ("The nocturnal boundary layer as a flux chamber",
        "Median CO₂ build-up on well-stratified nights and the flux implied for 100 to 400 m stable layers."),
    "f16_growth_fire": ("Fire fingerprints at Bukit Kototabang",
        "Interannual CO₂ growth anomalies, fire-season enhancement ratios, and plume clearance times."),
    "f24_trends_gradients": ("Two decades of flasks: acceleration, gradients, and the CO cycle",
        "Growth acceleration by species, the closing CO₂ hemispheric gap, and the regional half of the CO seasonal cycle."),
}


def title_strip_end(image: Image.Image) -> int:
    """First fully white row after the top title strip."""
    gray = np.asarray(image.convert("L"))
    rows = gray[:160, ::3].min(axis=1)
    start = int(np.argmax(rows < 200))
    for i in range(start, 160 - 8):
        if (rows[i:i + 8] >= 250).all():
            return i
    raise ValueError("title strip not found")


def build(name: str, headline: str, highlight: str) -> Path:
    image = Image.open(ROOT / "figures" / f"{name}.png").convert("RGB")
    body = np.asarray(image.crop((0, title_strip_end(image) + 4, image.width, image.height)))
    width_in = 7.2
    body_in = width_in * body.shape[0] / body.shape[1]
    head_in = 0.62
    fig = plt.figure(figsize=(width_in, body_in + head_in))
    fig.text(.04, 1 - .06 / (body_in + head_in), headline, fontsize=9.5, weight="bold", va="top")
    fig.text(.04, 1 - .30 / (body_in + head_in), highlight, fontsize=6.8, color="#52616A", va="top")
    ax = fig.add_axes([0, 0, 1, body_in / (body_in + head_in)])
    ax.imshow(body, interpolation="lanczos"); ax.axis("off")
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"poster_{name}.png"
    fig.savefig(path, dpi=DPI, facecolor="white"); plt.close(fig)
    return path


if __name__ == "__main__":
    for name, (headline, highlight) in VARIANTS.items():
        print(build(name, headline, highlight))
