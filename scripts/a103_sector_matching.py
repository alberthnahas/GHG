#!/usr/bin/env python3
"""Map the sector names a SIGN-SMART export actually carries onto IPCC categories.

The localisation engine wants an IPCC code. A real export carries Indonesian
sector names written by whoever filled the form: "Pembangkitan Listrik",
"Industri Pengolahan", "Peternakan", "Pengelolaan Limbah Padat". Demanding the
code instead pushes that translation onto the person least able to check it.

Two stages, in this order, and the order is the point:

  rules first. A keyword table resolves the common Indonesian sector wordings
    deterministically. It is auditable, free, offline, and reproducible, which
    an operational product needs more than it needs cleverness.

  a language judgment for the tail, optionally. TypeSafe's Jev returns a typed
    choice over the IPCC categories with a probability, for names the rules
    cannot resolve. It runs only when a key is configured, only on the leftovers,
    and never on anything already decided.

What this must never do is touch the arithmetic. The inversion, the gates, the
mass conservation and the tracer ratios are numerical and deterministic, and a
probabilistic judgment in any of them would trade auditability for nothing. A
regulator has to be able to recompute the readiness verdict exactly; they do not
have to recompute a sector-name lookup, which is why that is the only place a
model is allowed in.

Every mapping carries how it was made and how sure it was, and an unresolved
name is reported rather than guessed.

Stages
  match      map names from a file or the command line
  rules      print the keyword table
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/inventory"
JEV_THRESHOLD = 0.70          # below this a judgment is reported as unresolved, not applied

# Indonesian sector wordings to IPCC 2006 categories. Ordered: the first match wins,
# so the more specific phrases come first.
RULES: list[tuple[tuple[str, ...], str, str]] = [
    (("pembangkit", "listrik", "pltu", "pltg", "ketenagalistrikan"), "1A1", "Energy industries"),
    (("industri pengolahan", "manufaktur", "industri makanan", "semen", "baja", "pupuk industri"), "1A2",
     "Manufacturing industries and construction"),
    (("transportasi", "kendaraan", "angkutan", "penerbangan", "pelayaran"), "1A3", "Transport"),
    (("rumah tangga", "komersial", "bangunan", "permukiman"), "1A4", "Other sectors, buildings"),
    (("fugitif", "fugitive", "minyak dan gas", "migas", "pertambangan batubara", "batu bara"), "1B",
     "Fugitive emissions from fuels"),
    (("ippu", "proses industri", "penggunaan produk"), "2", "Industrial processes and product use"),
    (("peternakan", "ternak", "sapi", "kerbau", "unggas", "fermentasi enterik"), "3A", "Livestock"),
    (("sawah", "padi", "pertanian", "pemupukan", "pembakaran residu"), "3C", "Aggregate sources on land"),
    (("gambut", "drainase", "lahan gambut"), "3B1", "Land: peat drainage"),
    (("kebakaran", "karhutla", "pembakaran lahan", "kebakaran hutan"), "3B2", "Land: fire"),
    (("kehutanan", "folu", "lulucf", "perubahan lahan", "tutupan lahan", "hutan"), "3B", "Land, all"),
    (("limbah", "sampah", "air limbah", "persampahan", "tpa"), "4", "Waste"),
    (("energi",), "1", "Energy, all"),
]


def match_by_rule(name: str) -> tuple[str, str, float] | None:
    text = " ".join(str(name).lower().split())
    for keywords, code, description in RULES:
        if any(keyword in text for keyword in keywords):
            return code, description, 1.0
    return None


def jev_available() -> bool:
    return bool(os.environ.get("TYPESAFE_API_KEY"))


def match_by_jev(names: list[str]) -> dict[str, tuple[str, float]]:
    """Ask Jev for a typed choice over the IPCC categories, for names the rules missed.

    Returns an empty mapping when no key is configured, which is the normal case
    offline: the caller then reports those names as unresolved rather than
    inventing a category for them.
    """
    if not names or not jev_available():
        return {}
    try:
        from typesafe import TypeSafe                      # optional dependency, by design
    except ImportError:
        print("typesafe SDK not installed; leaving the tail unresolved", flush=True)
        return {}
    options = {code: description for _, code, description in RULES}
    client = TypeSafe(api_key=os.environ["TYPESAFE_API_KEY"])
    resolved = {}
    for name in names:
        try:
            answer = client.choice(
                state={"sector_name": name, "country": "Indonesia",
                       "context": "a sector label from the Indonesian national greenhouse gas inventory"},
                instructions="Which IPCC 2006 category does this national inventory sector label belong to?",
                criteria={code: f"{code}: {description}" for code, description in options.items()})
            code, probability = answer.value, float(answer.probability)
            if probability >= JEV_THRESHOLD:
                resolved[name] = (code, probability)
        except Exception as error:                          # noqa: BLE001 - a judgment failure is not fatal
            print(f"  judgment failed for {name!r}: {type(error).__name__}", flush=True)
    return resolved


def match(names: list[str], use_jev: bool = True) -> pd.DataFrame:
    rows, leftovers = [], []
    for name in names:
        hit = match_by_rule(name)
        if hit:
            code, description, confidence = hit
            rows.append(dict(sector_name=name, ipcc_code=code, description=description,
                             method="rule", confidence=confidence))
        else:
            leftovers.append(name)
    judged = match_by_jev(leftovers) if use_jev else {}
    options = {code: description for _, code, description in RULES}
    for name in leftovers:
        if name in judged:
            code, probability = judged[name]
            rows.append(dict(sector_name=name, ipcc_code=code, description=options.get(code, ""),
                             method="jev", confidence=round(probability, 3)))
        else:
            rows.append(dict(sector_name=name, ipcc_code="", description="", method="unresolved", confidence=0.0))
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["match", "rules"])
    parser.add_argument("--names", nargs="*", help="sector names to map")
    parser.add_argument("--export", type=Path, help="a CSV with a sector_name column")
    parser.add_argument("--no-jev", action="store_true", help="rules only, even when a key is configured")
    a = parser.parse_args()
    if a.stage == "rules":
        for keywords, code, description in RULES:
            print(f"  {code:4s} {description:42s} <- {', '.join(keywords)}")
        print(f"\nJev is {'configured' if jev_available() else 'not configured'}; "
              "it is used only for names the rules cannot resolve, and never in the numerics.")
        return
    names = list(a.names or [])
    if a.export:
        names += pd.read_csv(a.export)["sector_name"].dropna().astype(str).tolist()
    if not names:
        raise SystemExit("give --names or --export")
    table = match(names, use_jev=not a.no_jev)
    OUT.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUT / "sector_matching.csv", index=False)
    print(table.to_string(index=False))
    unresolved = table[table.method.eq("unresolved")]
    if len(unresolved):
        print(f"\n{len(unresolved)} names unresolved; add a rule or supply the ipcc_code directly:")
        print("  " + "; ".join(unresolved.sector_name))


if __name__ == "__main__":
    main()
