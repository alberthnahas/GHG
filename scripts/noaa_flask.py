"""Reader for the NOAA GML CCGG surface-flask text products in ``noaa_flask/``.

Bukit Kototabang (site code BKT) is a NOAA cooperative flask site operated with
BMKG, sampled roughly weekly in pairs since January 2004.  Because the flasks are
analysed at NOAA GML against the WMO scales, they are an *external* reference for
the in-situ hourly archive - the only one available anywhere in this project.

Five reference sites are included for the hemispheric comparisons, so that
quantities like the interhemispheric gradient are measured from data rather than
quoted from the literature.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "noaa_flask"

# site -> (name, latitude, longitude, elevation m)
SITES = {
    "brw": ("Barrow, Alaska", 71.32, -156.61, 11.0),
    "mlo": ("Mauna Loa, Hawaii", 19.54, -155.58, 3397.0),
    "kum": ("Cape Kumukahi, Hawaii", 19.52, -154.82, 3.0),
    "bkt": ("Bukit Kototabang", -0.20, 100.32, 845.0),
    "smo": ("Tutuila, American Samoa", -14.25, -170.56, 42.0),
    "spo": ("South Pole", -89.98, -24.80, 2810.0),
}
SPECIES = ("co2", "ch4", "co", "n2o", "sf6", "h2")
UNIT = {"co2": "ppm", "ch4": "ppb", "co": "ppb", "n2o": "ppb", "sf6": "ppt", "h2": "ppb"}
# Long-lived and chemically inert: no local source and no chemistry, so any
# variability it shows at a station is transport and nothing else.
INERT = "sf6"


def _rows(path):
    with open(path) as fh:
        return [ln for ln in fh if not ln.startswith("#")]


def events(species, site="bkt", qc=True):
    """Individual flask analyses, averaged over the pair taken at the same hour.

    ``qc=True`` keeps only samples whose first QC character is '.', NOAA's
    convention for a measurement that passed every check.  The rejected fraction
    is itself informative and is reported by :func:`qc_summary`.
    """
    f = DIR / f"{species}_{site}_surface-flask_1_ccgg_event.txt"
    lines = _rows(f)
    df = pd.DataFrame([ln.split() for ln in lines[1:]], columns=lines[0].split())
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["t"] = pd.to_datetime(df["datetime"], format="ISO8601", utc=True).dt.tz_localize(None)
    if qc:
        df = df[df.qcflag.str[0] == "."]
    s = df.groupby(df.t.dt.floor("h"))["value"].mean().dropna()
    s.name = species
    return s


def monthly(species, site="bkt"):
    """NOAA's own monthly means, which already apply their selection and gap-filling."""
    f = DIR / f"{species}_{site}_surface-flask_1_ccgg_month.txt"
    r = pd.DataFrame([ln.split() for ln in _rows(f)],
                     columns=["site", "year", "month", "value"])
    r["value"] = pd.to_numeric(r.value)
    r["t"] = pd.to_datetime(dict(year=r.year.astype(int), month=r.month.astype(int), day=1))
    s = r.set_index("t")["value"].dropna()
    s.name = species
    return s


def have(species, site):
    return (DIR / f"{species}_{site}_surface-flask_1_ccgg_month.txt").exists()


def qc_summary(site="bkt"):
    rows = []
    for sp in SPECIES:
        f = DIR / f"{sp}_{site}_surface-flask_1_ccgg_event.txt"
        if not f.exists():
            continue
        lines = _rows(f)
        df = pd.DataFrame([ln.split() for ln in lines[1:]], columns=lines[0].split())
        rej = df[df.qcflag.str[0] != "."]
        rows.append(dict(species=sp, n=len(df), n_rejected=len(rej),
                         pct_rejected=100 * len(rej) / len(df),
                         top_flag=rej.qcflag.value_counts().index[0] if len(rej) else ""))
    return pd.DataFrame(rows)


def scale(species, site="bkt"):
    """The calibration scale the file declares, e.g. CO2_X2019."""
    f = DIR / f"{species}_{site}_surface-flask_1_ccgg_event.txt"
    for ln in open(f):
        if ln.startswith("# dataset_calibration_scale"):
            return ln.split(":", 1)[1].strip()
        if not ln.startswith("#"):
            break
    return ""


def match_insitu(insitu, species, site="bkt", how="corrected"):
    """Pair each flask sample with the in-situ hour it was drawn in.

    ``how='corrected'`` indexes the in-situ record by the time base derived in
    Section 1; ``how='raw'`` treats the archive stamp as UTC, which is what a
    user who trusted the delivered file would do.  Comparing the two is a direct
    external test of the time-base correction.
    """
    col = {"corrected": "time_utc", "raw": "time"}[how]
    ins = insitu.drop_duplicates(col).set_index(col)[species]
    fl = events(species, site)
    j = pd.concat([fl.rename("flask"), ins.rename("insitu")], axis=1, join="inner").dropna()
    j["diff"] = j.flask - j.insitu
    return j
