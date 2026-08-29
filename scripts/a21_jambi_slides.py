"""The Jambi presentation.  Written to Jambi/Jambi_Presentation.pptx.

Jambi is the station with the clearest single story in the network: its surface
is losing carbon rather than cycling it, and two independent measurements say
so.  This deck is built around that, with the other four stations used as the
comparison that gives the numbers meaning - a result like "9.5 µmol m⁻² s⁻¹"
means nothing until an intact rainforest 1,800 km away returns 5.1 under the
same method.

Layout and palette follow the main deck: white background, 16:9, findings paired
with the method that produced them.

Usage:  a21_jambi_slides.py [--lang id]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ghg_common as G
import i18n
from a19_slides import (Presentation, W, H, slide_title, slide_section,
                        slide_finding, slide_table, slide_quote, slide_pair,
                        slide_index, slide_figure_wide)
import a19_slides as S

JFIG = G.ROOT / "Jambi" / "figures"


def build():
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H
    n = [0]

    def page():
        n[0] += 1
        return n[0]

    # ---- title -------------------------------------------------------------
    s = S._blank(prs)
    S._rule(s, S.Inches(2.05), S.M, S.BODY, S.ORANGE, S.Pt(2.5))
    tf = S._tb(s, S.M, S.Inches(2.3), S.BODY, S.Inches(1.75))
    S._para(tf, S.T("Jambi"), 44, S.INK, bold=True, first=True, space_after=8)
    S._para(tf, S.T("A lowland peat station that is losing its carbon — "
                    "and how we know"), 19, S.MUTED)
    S._rule(s, S.Inches(4.35), S.M, S.BODY)
    tf = S._tb(s, S.M, S.Inches(4.6), S.BODY, S.Inches(1.3))
    S._para(tf, S.T("1.61 °S, 103.65 °E · 25 m · 14,486 hourly observations, "
                    "November 2023 – December 2025"), 14, S.INK, first=True, space_after=8)
    S._para(tf, S.T("Compared throughout with Bariri (montane rainforest), Kemayoran "
                    "(megacity), Bukit Kototabang and Sorong"), 13, S.MUTED)
    S._footer(s, S.T("Analysis date 18 August 2026"), page())

    # ---- what the site is ---------------------------------------------------
    slide_section(prs, "PART 1", "What the station sees",
                  "The most extreme surface signal in the network, and the least "
                  "like combustion", page())

    slide_table(
        prs, "JAMBI AT A GLANCE", "The numbers, against the other four stations",
        ["", "Jambi", "Bariri", "Kemayoran", "What it means"],
        [["*Median CO₂", "*435.2 ppm", "~416", "~430", "elevated even against a megacity"],
         ["*Median CH₄", "*2,070 ppb", "~1,920", "~2,070", "as high as Jakarta"],
         ["*Median CO", "*194 ppb", "~95", "~292", "between forest and megacity"],
         ["*Diurnal CO₂ swing", "*44.8 ppm", "36.8", "29.5", "the largest in the network"],
         ["*Nocturnal CO₂ flux", "*9.46 µmol m⁻² s⁻¹", "*5.05", "6.17", "1.9× an intact forest"],
         ["*CH₄ flux", "*29 g m⁻² yr⁻¹", "—", "65", "a rural site at half a megacity's rate"]],
        ["A lowland peat and plantation landscape produces a bigger carbon dioxide signal "
         "than a city of thirty million, and almost as much methane.",
         "Everything that follows is an attempt to say why. · Report §1.1, §5.1, §7.3, §8.1"],
        page(), widths=[0.19, 0.17, 0.12, 0.15, 0.37])

    slide_figure_wide(
        prs, "THE RECORD", "Two years, three species, and a background that barely moves",
        JFIG / "j3_record.png",
        "Figure J3 — monthly median and 10th–90th percentile of the hourly values, with the "
        "afternoon background beneath.",
        ["The gap between the median and the background is the local source. At Jambi it is "
         "about 15 ppm of CO₂ and 80 ppb of methane, every month of the year.",
         "The background itself is nearly flat — this is a site dominated by what happens "
         "within a few kilometres, not by what arrives.",
         "The CO envelope widens sharply in the second half of each year. That is the "
         "burning season, and Section 3 returns to it."],
        ["Monthly statistics on hourly data, requiring 200 valid hours in the month; the "
         "background is the 20th percentile of 12:00–16:00 local, when the mixed layer is "
         "deepest and the air is regionally representative. · Report §1.1, Appendix B"],
        page())

    slide_figure_wide(
        prs, "THE SITE'S SIGNATURE",
        "Three species, and only one of them behaves like a city",
        JFIG / "j1_signature.png",
        "Figure J1 — the diurnal cycle, the nightly coupling, and the seasonal cycle "
        "of respiration, with Bariri for comparison.",
        ["CO₂ and CH₄ peak together just after dawn — the classic nocturnal build-up, "
         "released as the mixed layer deepens. CO peaks in the EVENING instead, near "
         "22:00, decoupled from both.",
         "Jambi's CO₂ passes the coupling test with CO on only 3 % of nights, against "
         "25 % with methane. At Bariri the pattern is reversed: 44 % with CO.",
         "Whatever emits the CO₂ here emits methane alongside it, and is not burning "
         "anything. The seasonal panel says what it is."],
        ["Within one night the boundary layer is an accumulation chamber, so the slope of "
         "one species against another is the emission ratio of the surface mix — "
         "independent of dilution, layer depth and calibration.",
         "The pass rate is itself the measurement: 17 of 627 nights for CO–CO₂ against 158 "
         "for CH₄–CO₂ is not a failure of the method. · Report §5.1, §6.2, §8.2"],
        page())

    # ---- the finding --------------------------------------------------------
    slide_section(prs, "PART 2", "The finding: this peat is being consumed",
                  "Two independent measurements, a magnitude and a phase, that agree",
                  page())

    slide_pair(
        prs, "THE EVIDENCE", "Magnitude and phase are separate measurements",
        [("The magnitude",
          ["Nocturnal CO₂ efflux is 9.46 µmol m⁻² s⁻¹ against Bariri's 5.05 — a factor "
           "of 1.9.",
           "Annualised that is about 3,600 g C m⁻² yr⁻¹, at or above the gross primary "
           "production of the most productive tropical forest.",
           "Local photosynthesis cannot balance it. The carbon is coming out of a store."]),
         ("The phase",
          ["Jambi's respiration peaks in OCTOBER, at the end of the dry season, and troughs "
           "in January. Bariri does the opposite.",
           "The two sites are in antiphase, by a factor of 2.09 from Jambi's minimum to its "
           "maximum.",
           "A warmer or more fertile soil could explain the magnitude. Nothing but drainage "
           "explains the phase."]),
         ("Why the phase settles it",
          ["In waterlogged peat, anoxia protects the carbon and decomposition is slow.",
           "Lower the water table and oxygen reaches material that may be centuries old.",
           "Wetting suppresses it; drying releases it. A site whose respiration rises as it "
           "dries is a site whose store is being consumed."])],
        ["Nightly slopes gated on CO₂–time coherence (r > 0.7), grouped by calendar month, "
         "then normalised by each site's own annual mean so layer depth divides out. "
         "· Report §8.1–8.2"],
        page())

    slide_figure_wide(
        prs, "THE COST",
        "Sixteen point seven tonnes of carbon per hectare, every year",
        JFIG / "j2_context.png",
        "Figure J2 — Jambi against the other four stations: the regional enhancement, "
        "methane's share of the forcing, and the respiration excess.",
        ["Subtracting what an intact forest soil respires leaves 1,670 g C m⁻² yr⁻¹ "
         "attributable to drainage — 16.7 t C ha⁻¹ yr⁻¹.",
         "Tropical peat domes hold 1,000–3,000 t C ha⁻¹, far more than mineral soils, "
         "because waterlogging protected them for millennia.",
         "At this rate the store empties on an e-folding time of 60 to 180 years — a "
         "human-lifetime clock on a store built over thousands."],
        ["The subtraction isolates the excess over an intact reference, which is the part "
         "drainage is responsible for. Both fluxes carry the same layer-depth assumption, "
         "so a common error largely cancels in the difference.",
         "Treat the clock as decades to a couple of centuries, not as a precise number. "
         "· Report §8.4"],
        page())

    slide_figure_wide(
        prs, "A THIRD LINE OF EVIDENCE", "The daytime does not make it back",
        "f7_carbon.png",
        "Figure 5 of the main report — the extra CO₂ loss beyond dilution, measured "
        "independently against methane and against carbon monoxide.",
        ["The morning CO₂ decline mixes dilution with photosynthesis. CH₄ and CO have no "
         "photosynthetic sink, so their decline measures dilution alone.",
         "Bariri and Bukit Kototabang show a clear net sink; Kemayoran shows a net source. "
         "Jambi shows nothing — −0.017 against methane, −0.001 against CO.",
         "An oil-palm plantation photosynthesises perfectly well. Its daytime uptake is "
         "cancelled by the respiration measured at night."],
        ["Paired comparison: both species on the same morning, median of the per-day "
         "difference in decay rate, 2,000 bootstrap resamples of days. Unpaired medians "
         "compare different populations of mornings and the two tracers then disagree by "
         "more than the effect. · Report §5.3"],
        page())

    # ---- in the region ------------------------------------------------------
    slide_section(prs, "PART 3", "Jambi in the region",
                  "Methane-heavy, uncorrelated with its nearest neighbour, and upwind "
                  "of the haze", page())

    slide_figure_wide(
        prs, "AGAINST THE NETWORK · THE FLUX",
        "The largest CO₂ flux of the five, and the largest diurnal swing",
        "f12_nocturnal_flux.png",
        "Figure 9 of the main report — nocturnal CO₂ accumulation and the flux it implies, "
        "for all five stations.",
        ["Jambi's 4.10 ppm per hour is the highest in the network, on 422 coherent nights.",
         "At an assumed 200 m layer that is 9.46 µmol m⁻² s⁻¹, against the 4–8 published for "
         "intact tropical rainforest — which Bariri sits inside, at 5.05.",
         "The shaded band is the published range. Jambi is the only station above it."],
        ["Nights kept only where the rise is monotone (r > 0.7 over at least six hours), "
         "which selects the calm, stratified nights on which a fixed accumulation volume is "
         "a fair assumption. · Report §8.1"],
        page())

    slide_figure_wide(
        prs, "AGAINST THE NETWORK · THE LADDER", "Where Jambi sits in the regional ladder",
        "f10_weekly_ladder.png",
        "Figure 8 of the main report — panels b to d show each station's afternoon "
        "background minus Bariri's, month-matched.",
        ["In well-mixed afternoon air Jambi runs +4.6 ppm of CO₂, +66 ppb of methane and "
         "+52 ppb of CO above the montane rainforest reference.",
         "That is 72 % of Jakarta's methane enhancement on 45 % of its CO₂ — a different "
         "mixture entirely, not a smaller city.",
         "Panel a is the weekly-cycle test: Jambi shows no significant weekday signal in any "
         "species, which is what a landscape source looks like and a working-week source does not."],
        ["Afternoon 20th-percentile air, matched month by month against Bariri, so these are "
         "regional differences rather than local plumes. · Report §7.2, §11"],
        page())

    slide_table(
        prs, "THE REGIONAL SIGNAL", "Well-mixed afternoon air, referenced to Bariri",
        ["Station", "ΔCO₂ (ppm)", "ΔCH₄ (ppb)", "ΔCO (ppb)", "ΔCH₄/ΔCO₂"],
        [["Sorong", "+1.9 ± 0.3", "+9.8 ± 3.2", "−2.5 ± 2.2", "5.2"],
         ["Bukit Kototabang", "+2.0 ± 0.2", "+22.4 ± 2.6", "+12.5 ± 3.8", "11.2"],
         ["*Jambi", "*+4.6 ± 0.3", "*+66.2 ± 3.5", "*+52.2 ± 2.2", "*14.4"],
         ["Kemayoran (Jakarta)", "+10.3 ± 0.4", "+92.4 ± 5.9", "+151.8 ± 6.8", "9.0"]],
        ["These are differences in well-mixed afternoon air, so they are regional signals "
         "rather than local plumes.",
         "Jambi reaches 72 % of a megacity's methane enhancement on a third of its CO₂ — "
         "and its ΔCH₄/ΔCO₂ of 14.4 is the highest in the network, well above Jakarta's 9.0. "
         "That is what a landscape of drained peat and canals produces and a city does not. "
         "· Report §11"],
        page(), widths=[0.26, 0.18, 0.19, 0.18, 0.19])

    slide_figure_wide(
        prs, "THE METHANE", "A rural peatland at half a megacity's emission rate",
        JFIG / "j4_methane.png",
        "Figure J4 — nocturnal build-up, the distribution of hourly values, and the nightly "
        "methane-to-CO₂ ratio, across all five stations.",
        ["Methane accumulates at 25 ppb per hour on Jambi's calm nights — second only to "
         "Jakarta's 56, and thirteen times Bariri's 1.9.",
         "The whole distribution is shifted, not merely tailed: Jambi's typical hour is "
         "methane-rich, which is a landscape signal rather than an occasional plume.",
         "Its nightly ΔCH₄/ΔCO₂ of 4.4 matches Bukit Kototabang's — but Jambi reaches it "
         "with more than twice the CO₂ flux underneath."],
        ["Nightly slopes on calm, coherent nights; the flux uses an assumed 100–400 m layer "
         "depth, which is the one unmeasured quantity here. At 200 m the areal rate is about "
         "29 g CH₄ m⁻² yr⁻¹ against Jakarta's 65. · Report §6.2, §7.3"],
        page())

    slide_pair(
        prs, "TWO CONSEQUENCES", "What Jambi's methane is worth, and who it resembles",
        [("Methane's share of the forcing",
          ["Converting the enhancements to radiative forcing: CO₂ 58.7 mW m⁻², methane "
           "38.1 mW m⁻², total 96.7.",
           "Methane is 39 % of the local greenhouse burden — the highest share of any "
           "station here, against 20 % in the global budget.",
           "For a provincial inventory that is the ratio that matters: methane is a larger "
           "share here than the global average would lead you to budget for."]),
         ("Uncorrelated with its neighbour",
          ["Jambi and Kemayoran are 618 km apart — the closest pair in the network — and "
           "their monthly background anomalies correlate at −0.03.",
           "Jambi and Sorong, 3,074 km apart, correlate at +0.57.",
           "Coherence follows site type, not distance. Both are dominated by their own "
           "local sources, which have nothing to do with each other."]),
         ("The practical reading",
          ["A regional background derived from Jambi is not regional. Neither is one from "
           "Jakarta.",
           "If a provincial monitoring programme wants a background reference, it needs a "
           "clean site, not a nearer one.",
           "Jambi's value is as a source measurement, and it is an excellent one."])],
        ["Forcing from the standard band expressions with the ~43 % indirect uplift for "
         "methane; coherence on the detrended monthly background anomaly. "
         "· Report §11.2, §13"],
        page())

    slide_figure_wide(
        prs, "THE CONNECTION TO THE HAZE",
        "Jambi's respiration and Sumatra's peat fires are the same water table",
        JFIG / "j5_fire.png",
        "Figure J5 — Jambi's nocturnal respiration against the carbon monoxide recorded at "
        "Bukit Kototabang, 500 km downwind.",
        ["Bukit Kototabang has two burning windows. The February one is Riau land clearing, "
         "and Jambi's respiration does not follow it.",
         "The September–October one does: both peak together, and across June–November the "
         "two series correlate at r = +0.50.",
         "One physical cause, seen twice. The water-table drawdown that lets oxygen into the "
         "peat is what makes it both respire faster and burn at all."],
        ["The nightly slopes are gated on CO₂–time coherence and fire plumes are episodic "
         "rather than nocturnal-monotone, so this is not contamination of one record by the "
         "other. The correlation is restricted to June–November because the February window "
         "belongs to a different source region. · Report §8.3, §9.3"],
        page())

    slide_pair(
        prs, "TWO CHECKS THAT COST NOTHING",
        "What Jambi's own record says about Jambi's own record",
        [("The rectifier",
          ["Jambi's 24-hour mean CO₂ exceeds its afternoon mean by 18.3 ppm — the largest "
           "in the network, and larger than Kemayoran's 11.3.",
           "That is the nocturnal store this deck's whole argument rests on, visible as a "
           "single number.",
           "It also confirms the record is sound: 0.2 % of days are negative, and a "
           "negative rectifier is physically impossible."]),
         ("Why it is a QC test",
          ["The shallow night layer accumulates; the deep afternoon layer dilutes. So the "
           "rectifier is positive at every honest surface site.",
           "The sign survives any calibration offset or scale error, because both cancel "
           "in a difference.",
           "Sorong before June 2023 fails it at −29 ppm with 47 % of days negative. Jambi "
           "passes it in every month of the year."]),
         ("What it costs",
          ["Nothing. No reference site, no flask, no second station, no external standard.",
           "It can be computed on the day the data are collected, from the station's own "
           "hourly file.",
           "It catches gross defects, not subtle ones — a constant offset is invisible to "
           "it. Use it as a first filter."])],
        ["Daily 24-hour mean minus 12:00–16:00 mean, on days having both, then averaged. "
         "· Report §4.6 · Methods §16b"],
        page())

    slide_table(
        prs, "THE EARLY-WARNING SIGNAL",
        "If a Jambi drought watch is keyed to a declared El Niño, key it to ONI",
        ["SON", "ONI", "class", "RONI", "class", "BKT peak daily CO", "Days > 1,000 ppb"],
        [["2014", "+0.51", "*El Niño", "+0.35", "neutral", "*4,063 ppb", "13"],
         ["2017", "−0.44", "neutral", "−0.82", "*La Niña", "321 ppb", "0"],
         ["2019", "+0.51", "*El Niño", "+0.15", "neutral", "*1,660 ppb", "1"]],
        ["CPC publishes two ENSO indices. The Relative ONI subtracts the tropical-mean "
         "warming, which makes it the right index for asking whether events are intensifying "
         "— and the wrong one for asking whether Sumatra will burn.",
         "In the three seasons where the two disagree, the ONI class matched what the "
         "regional atmosphere did and the RONI class did not. Maritime-Continent drought "
         "follows absolute eastern-Pacific warmth, not warmth relative to a tropical mean "
         "that includes the warm pool itself.",
         "For Jambi that is the same water-table drawdown this deck measures. · Report §14.2"],
        page(), widths=[0.08, 0.10, 0.14, 0.10, 0.14, 0.24, 0.20])

    slide_table(
        prs, "TEN NEW TESTS OF THE JAMBI RECORD",
        "The peat interpretation survives; the boundary-layer story becomes sharper",
        ["Findings", "Test", "Jambi result", "Reading"],
        [["152, 157", "Transition and curvature", "−15.06 ppm at 09:00; no late-night slowdown (p=0.58)",
          "Strong continuing source under a ventilating boundary layer"],
         ["162, 167", "Carry-over and season", "0.8% next-dawn carry-over; CH₄ leads wet–dry shift",
          "The site resets daily but changes with hydrology"],
         ["172, 177", "Regimes and tails", "Rare all-gas regime; CO₂–CH₄ tail 7.5× independence",
          "Coherent peat accumulation, not a one-channel artefact"],
         ["182, 187", "Ageing and memory", "CH₄/CO 0.624→1.264; CO lag-1 r=0.315",
          "CO clears faster while methane persists or renews"],
         ["192, 197", "Reproducibility and sampling", "CH₄–CO r=0.548–0.599; hour bias spans 43.60 ppm",
          "Fingerprint repeats; a fixed-hour level is not a daily mean"]],
        ["All values are computed from the harmonised archive by scripts/a35_extra9.py. "
         "The null result in Finding 157 is retained: Jambi is the one site where a constant "
         "nightly accumulation rate is not rejected. · Report §19.31–19.40 · Methods §19.8–19.16"],
        page(), widths=[0.12, 0.22, 0.31, 0.35])

    # ---- limits and next ----------------------------------------------------
    slide_section(prs, "PART 4", "What would make this stronger",
                  "The limits of a two-year record, and the one measurement that is missing",
                  page())

    slide_table(
        prs, "HONEST LIMITS", "What this record cannot yet do",
        ["", "Limitation", "Consequence"],
        [["*1", "*Nocturnal layer depth is assumed, not measured",
          "Every absolute flux carries a factor-of-two uncertainty. The RATIO to Bariri and "
          "the seasonal PHASE both survive it; the 16.7 t C ha⁻¹ yr⁻¹ does not"],
         ["*2", "*Two years of record",
          "Enough for diurnal, weekly, ratio and respiration-phase work. Not enough for a "
          "trend — none is quoted"],
         ["*3", "*No water-table or meteorological data",
          "The drainage mechanism is inferred from the phase, not observed directly"],
         ["*4", "*The peat store is a published range",
          "1,000–3,000 t C ha⁻¹ is a bracket, not a measurement at this site; the 60–180 "
          "year clock inherits it"]],
        ["None of these touches the central result. The magnitude and the phase are "
         "independent, they agree, and the phase is robust to every one of the four. "
         "· Report Appendix C"],
        page(), widths=[0.05, 0.35, 0.60])

    slide_table(
        prs, "WHAT WOULD SETTLE IT", "Four measurements, in order of value",
        ["", "Measurement", "What it would resolve"],
        [["*1", "*A ceilometer, or routine radiosondes",
          "Layer depth is the single unmeasured quantity. It would turn 16.7 t C ha⁻¹ yr⁻¹ "
          "from indicative into quantitative"],
         ["*2", "*Water-table records from the peat domes",
          "Would confirm the drainage mechanism directly rather than by inference from the "
          "seasonal phase"],
         ["*3", "*A third year of record",
          "The phase result rests on two years. A third would settle it"],
         ["*4", "*δ¹³C-CH₄ or ethane",
          "Would separate the methane between peat, canals and livestock — the split this "
          "record leaves open"]],
        ["The first two are inexpensive relative to what is already deployed, and between "
         "them they would make Jambi a quantitative peatland carbon station rather than an "
         "indicative one. · Report §15"],
        page(), widths=[0.05, 0.35, 0.60])

    slide_quote(
        prs, "IN ONE SENTENCE",
        "Jambi is measuring a peatland returning its carbon to the atmosphere, and the "
        "measurement is a phase as much as a magnitude.",
        ["Two independent lines — respiration at twice an intact forest's rate, and a "
         "seasonal cycle running opposite to one — say the same thing, and the second is "
         "robust to every limitation of the first.",
         "The result is publishable as it stands: a continuous atmospheric measurement of "
         "peatland carbon loss, available on quiet nights, without waiting for a fire.",
         "And it is actionable in a way most atmospheric findings are not, because the "
         "mechanism is a water table."],
        page())
    return prs


def main():
    lang = i18n.from_argv()
    i18n.set_lang(lang)
    out = G.ROOT / "Jambi" / f"Jambi_Presentation{i18n.suffix()}.pptx"
    out.parent.mkdir(parents=True, exist_ok=True)
    prs = build()
    prs.save(str(out))
    if lang != "en" and i18n.MISSING:
        print(f"  WARNING: {len(i18n.MISSING)} deck strings have no {lang} translation.")
    print(f"wrote {out.relative_to(G.ROOT)}  "
          f"({len(prs.slides._sldIdLst)} slides, {out.stat().st_size/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
