# Jambi

A station-specific presentation drawn from the five-station greenhouse-gas analysis.

| File | What it is |
|---|---|
| `Jambi_Presentation.pptx` | 20 slides, white background, 16:9; 8 carry a figure |
| `Jambi_Presentation.pdf` | the same, rendered, so it can be read without PowerPoint |
| `figures/j1_signature.png` | the diurnal cycle, the nightly coupling, and the seasonal respiration |
| `figures/j2_context.png` | Jambi against the other four stations |
| `figures/j3_record.png` | the two-year record: range, median and background, by species |
| `figures/j4_methane.png` | the methane build-up, distribution and nightly ratio, across the network |
| `figures/j5_fire.png` | Jambi's respiration against the haze 500 km downwind |

Three figures from the main report are reused where they already answer a Jambi question:
`f11_nocturnal_flux` (the flux, all five stations), `f10_weekly_ladder` (the regional ladder
and the weekly-cycle test) and `f17_carbon` (the source-or-sink test).

## What it argues

Jambi is the one station in the network whose surface is **losing** carbon rather than cycling it, and two independent measurements say so:

- **Magnitude** — nocturnal CO₂ efflux of 9.46 µmol m⁻² s⁻¹, **1.9× the intact-rainforest reference** at Bariri, and at or above the gross primary production of the most productive tropical forest.
- **Phase** — respiration peaks in **October**, at the end of the dry season, while Bariri's peaks when it is wet. Wetting suppresses decomposition; drainage releases it.

A warmer or more fertile soil could explain the magnitude. Nothing but drainage explains the phase, and the phase is robust to the layer-depth assumption that the magnitude depends on. A third line agrees: Jambi shows **no net daytime CO₂ uptake** — its plantation photosynthesis is cancelled by its soil respiration.

The cost is **16.7 t C ha⁻¹ yr⁻¹**, which empties a 1,000–3,000 t C ha⁻¹ peat store on a **60–180 year** clock.

## Comparisons used

Every number is given against the other four stations, because a flux means nothing alone:

- **Bariri (Lore Lindu)** — montane primary rainforest, the intact reference.
- **Kemayoran (Jakarta)** — a megacity of thirty million, which Jambi *exceeds* in CO₂ diurnal amplitude and reaches 72 % of in methane.
- **Bukit Kototabang** — 500 km downwind, where Jambi's burning season shows up as haze.
- **Sorong** — the network's cleanest site.

## Rebuilding

```
python3 scripts/a20_jambi_figs.py      # -> Jambi/figures/
python3 scripts/a21_jambi_slides.py    # -> Jambi/Jambi_Presentation.pptx
python3 scripts/check_slides.py Jambi/Jambi_Presentation.pptx
```

The checker renders the deck through LibreOffice and measures the actual output. It currently reports zero issues.

Full derivations are in `../GHG_Analysis_Methods.md`; the sections cited on each slide refer to `../GHG_Analysis_Report.md`.
