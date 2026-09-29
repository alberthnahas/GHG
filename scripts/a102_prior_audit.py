#!/usr/bin/env python3
"""Where the prior error lives, and therefore whether a better inventory helps.

Localising the inventory is work, and it should go where it changes an answer.
This audits the modelled signal at the towers by component, and asks of each one
whether a national inventory can touch it at all.

The result decides priority between the two gases, and it is not symmetric.

A national inventory reports anthropogenic emissions. It does not report the
terrestrial biosphere, and it does not report natural wetlands. Whatever share
of the modelled signal those carry is a share that SIGN-SMART cannot improve,
however good the export is.

Stage
  audit     write the component decomposition and the recommendation
"""
from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd

import a99_operational_inversion as V

OUT = V.OUT
# What a national greenhouse gas inventory reports, and what it does not.
# Natural wetlands are not anthropogenic and do not appear; drained peat does,
# but it appears under land use, which needs the FOLU proxy rather than EDGAR.
REPORTED = {
    "fossil_near": ("yes", "energy, industry, transport and buildings"),
    "fossil_far": ("yes", "the same, outside 500 km"),
    "anthro_near": ("yes", "energy, fugitive, agriculture and waste"),
    "anthro_far": ("yes", "the same, outside 500 km"),
    "fire": ("partly", "land-use fire sits in FOLU, which needs the proxy rather than EDGAR"),
    "wetlands": ("no", "natural wetland methane is not anthropogenic and is not in a national inventory"),
    "bio_net_BKT": ("no", "the terrestrial biosphere is not in a national inventory"),
    "bio_net_JMB": ("no", "the terrestrial biosphere is not in a national inventory"),
}


def audit() -> dict:
    rows = []
    for gas in V.GASES.values():
        frame = V.FRAMES[gas.name]()
        columns = list(gas.components.values())
        total = frame[columns].sum(axis=1).to_numpy(float)
        variance = float(np.var(total, ddof=1))   # match the ddof np.cov uses, so the shares sum to one
        for parameter, column in gas.components.items():
            values = frame[column].to_numpy(float)
            # covariance share, which sums to one across components even though they
            # co-vary; a ratio of standard deviations does not and would mislead
            share = float(np.cov(values, total)[0, 1] / variance) if variance else np.nan
            reported, note = REPORTED.get(parameter, ("unknown", "not classified"))
            rows.append(dict(gas=gas.name, unit=gas.unit, component=parameter,
                             mean=float(values.mean()), sd=float(values.std()),
                             share_of_signal_percent=100 * share,
                             in_national_inventory=reported, note=note))
    table = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUT / "prior_audit.csv", index=False)

    recommendation = {}
    for gas in V.GASES:
        g = table[table.gas.eq(gas)]
        reachable = float(g[g.in_national_inventory.eq("yes")].share_of_signal_percent.sum())
        beyond = float(g[g.in_national_inventory.eq("no")].share_of_signal_percent.sum())
        recommendation[gas] = dict(
            reachable_by_a_national_inventory_percent=round(reachable, 1),
            beyond_it_percent=round(beyond, 1),
            verdict=("a localised inventory moves most of this gas's modelled signal" if reachable > beyond
                     else "a localised inventory cannot move most of this gas's modelled signal"))
    (OUT / "prior_audit.json").write_text(json.dumps(recommendation, indent=2) + "\n")

    pd.set_option("display.width", 200)
    for gas in V.GASES:
        g = table[table.gas.eq(gas)].sort_values("share_of_signal_percent", ascending=False)
        print(f"=== {gas.upper()} ===")
        for row in g.itertuples():
            print(f"  {row.component:14s} mean {row.mean:+9.2f}  sd {row.sd:8.2f}  "
                  f"{row.share_of_signal_percent:5.1f}% of the signal  in a national inventory: {row.in_national_inventory}")
        r = recommendation[gas]
        print(f"  reachable {r['reachable_by_a_national_inventory_percent']}%, "
              f"beyond it {r['beyond_it_percent']}%: {r['verdict']}")
        print()
    return recommendation


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["audit"], nargs="?", default="audit")
    parser.parse_args()
    audit()


if __name__ == "__main__":
    main()
