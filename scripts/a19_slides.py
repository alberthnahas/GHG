"""Build the presentation: the essential findings, with the method beside each.

The deck pairs every scientific claim with how it was measured, because in this
project the two are not separable - several findings are findings *about* method
(the time base, the retraction, the tracer separation), and a claim shown without
its method invites exactly the mistake Section 15 records.

White background throughout, the figure palette for accents, 16:9.

Usage:  a19_slides.py [--lang id]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Emu, Inches, Pt

import ghg_common as G
import i18n

ROOT = G.ROOT
FIG = G.FIG

W, H = Inches(13.333), Inches(7.5)          # 16:9
INK = RGBColor(0x1B, 0x1F, 0x24)
MUTED = RGBColor(0x5B, 0x64, 0x70)
RULE = RGBColor(0xC9, 0xCF, 0xD6)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ACC = {k: RGBColor(*(int(v[i:i + 2], 16) for i in (1, 3, 5))) for k, v in G.COL.items()}
BLUE, ORANGE, GREEN, PURPLE, RED = (ACC["BKT"], ACC["JMB"], ACC["KMY"], ACC["PLU"], ACC["SRG"])

M = Inches(0.62)                             # page margin
BODY = W - 2 * M


def T(s):
    return i18n.t(s)


# ---------------------------------------------------------------------------
def _tb(slide, x, y, w, h, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    return tf


def _para(tf, text, size, color=INK, bold=False, space_before=0, space_after=6,
          align=PP_ALIGN.LEFT, first=False, italic=False):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.space_before = Pt(space_before)
    p.space_after = Pt(space_after)
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.color.rgb = color
    r.font.name = "Calibri"
    return p


def _rule(slide, y, x=M, w=None, color=RULE, h=Pt(1)):
    w = w or BODY
    from pptx.enum.shapes import MSO_SHAPE
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = color
    s.line.fill.background()
    s.shadow.inherit = False
    return s


def _border(cell, edge, color, pt):
    """Draw one cell edge.  python-pptx has no border API, so this writes the
    DrawingML directly: a:lnT / a:lnB on the cell properties."""
    from pptx.oxml.ns import qn
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tag = qn(f"a:ln{edge}")
    for old in tcPr.findall(tag):
        tcPr.remove(old)
    ln = tcPr.makeelement(tag, {"w": str(int(pt * 12700)), "cap": "flat",
                                "cmpd": "sng", "algn": "ctr"})
    fill = ln.makeelement(qn("a:solidFill"), {})
    clr = ln.makeelement(qn("a:srgbClr"), {"val": str(color)})
    fill.append(clr)
    ln.append(fill)
    # the schema fixes the order of the ln elements on tcPr
    order = ["a:lnL", "a:lnR", "a:lnT", "a:lnB", "a:lnTlToBr", "a:lnBlToTr"]
    idx = order.index(f"a:ln{edge}")
    anchor = None
    for later in order[idx + 1:]:
        found = tcPr.find(qn(later))
        if found is not None:
            anchor = found
            break
    if anchor is None:
        tcPr.insert(0, ln)
    else:
        anchor.addprevious(ln)


def _blank(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg = s.background.fill
    bg.solid()
    bg.fore_color.rgb = WHITE
    return s


def _footer(slide, text, page):
    tf = _tb(slide, M, H - Inches(0.44), BODY - Inches(1.2), Inches(0.3))
    _para(tf, text, 10, MUTED, first=True)
    tf2 = _tb(slide, W - M - Inches(1.0), H - Inches(0.44), Inches(1.0), Inches(0.3),
              align=PP_ALIGN.RIGHT)
    _para(tf2, str(page), 10, MUTED, first=True, align=PP_ALIGN.RIGHT)


def _fig(name):
    """The language-matched figure, falling back to English if it is absent.

    Accepts a bare filename, resolved against the shared figure directory, or an
    absolute path - the per-station decks keep their figures beside themselves.
    """
    p = Path(name)
    base = p if p.is_absolute() else FIG / p
    cand = base.with_name(base.stem + i18n.suffix() + base.suffix)
    return cand if cand.exists() else base


def _fit_size(img, w, h):
    """The size the image will take inside a w x h box, preserving aspect."""
    from PIL import Image
    iw, ih = Image.open(img).size
    scale = min(w / iw, h / ih)
    return int(iw * scale), int(ih * scale)


def _picture_fit(slide, img, x, y, w, h):
    """Place an image inside a box, preserving aspect ratio.

    Top-aligned, so a caption can sit directly beneath it rather than at the
    bottom of a nominal box the image does not fill.  These figures are about
    3:1, so they are always width-constrained and much shorter than the space
    available; the caller centres the image-plus-caption block instead.
    """
    nw, nh = _fit_size(img, w, h)
    return slide.shapes.add_picture(str(img), int(x + (w - nw) / 2), int(y), nw, nh)


# ---------------------------------------------------------------------------
def slide_title(prs, page):
    s = _blank(prs)
    _rule(s, Inches(2.05), M, BODY, BLUE, Pt(2.5))
    tf = _tb(s, M, Inches(2.3), BODY, Inches(1.75))
    _para(tf, T("Greenhouse gases at five Indonesian monitoring stations"),
          34, INK, bold=True, first=True, space_after=10)
    _para(tf, T("What 242,411 station-hours and 22 years of NOAA flasks say — "
                "and how each number was obtained"), 17, MUTED)
    _rule(s, Inches(4.15), M, BODY)
    tf = _tb(s, M, Inches(4.45), BODY, Inches(1.2))
    _para(tf, T("Bukit Kototabang · Jambi · Kemayoran · Bariri (Lore Lindu) · Sorong"),
          14, INK, first=True, space_after=8)
    _para(tf, T("200 findings · 28 figures · every number reproducible from the raw files"),
          13, MUTED)
    _footer(s, T("Analysis date 18 August 2026"), page)
    return s


def slide_section(prs, number, title, subtitle, page):
    s = _blank(prs)
    tf = _tb(s, M, Inches(2.6), BODY, Inches(0.7))
    _para(tf, number, 15, BLUE, bold=True, first=True, space_after=6)
    _rule(s, Inches(3.15), M, BODY, BLUE, Pt(2))
    tf = _tb(s, M, Inches(3.4), BODY, Inches(1.6))
    _para(tf, T(title), 30, INK, bold=True, first=True, space_after=10)
    _para(tf, T(subtitle), 16, MUTED)
    _footer(s, "", page)
    return s


def slide_finding(prs, kicker, headline, points, method, page, figure=None,
                  fig_caption=None):
    """One finding: the claim on the left, the method beneath it, figure right."""
    s = _blank(prs)
    has_fig = figure is not None and _fig(figure).exists()
    text_w = Inches(5.3) if has_fig else BODY

    tf = _tb(s, M, Inches(0.5), text_w, Inches(0.4))
    _para(tf, T(kicker), 12, BLUE, bold=True, first=True)

    tf = _tb(s, M, Inches(0.92), text_w, Inches(1.5))
    _para(tf, T(headline), 24 if has_fig else 27, INK, bold=True, first=True)

    y = Inches(2.30) if has_fig else Inches(2.2)
    tf = _tb(s, M, y, text_w, Inches(3.10))
    for i, pt in enumerate(points):
        _para(tf, "— " + T(pt), 13, INK, first=(i == 0), space_after=8)

    # the method block, always present
    my = Inches(5.55)
    _rule(s, my - Inches(0.16), M, text_w)
    tf = _tb(s, M, my, text_w, Inches(1.30))
    _para(tf, T("HOW IT WAS MEASURED"), 10, BLUE, bold=True, first=True, space_after=4)
    for i, line in enumerate(method):
        _para(tf, T(line), 11.5, MUTED, space_after=4)

    if has_fig:
        fx, fw = M + text_w + Inches(0.35), W - M - (M + Inches(5.3) + Inches(0.35))
        col_top, col_bot = Inches(0.95), Inches(6.55)
        _, nh = _fit_size(_fig(figure), fw, col_bot - col_top)
        cap_h = Inches(0.62) if fig_caption else 0
        block = nh + (Inches(0.16) + cap_h if fig_caption else 0)
        fy = col_top + max(int((col_bot - col_top - block) / 2), 0)
        pic = _picture_fit(s, _fig(figure), fx, fy, fw, col_bot - col_top)
        if fig_caption:
            tf = _tb(s, fx, pic.top + pic.height + Inches(0.16), fw, cap_h)
            _para(tf, T(fig_caption), 10.5, MUTED, first=True)
    _footer(s, T(kicker), page)
    return s


def slide_figure_wide(prs, kicker, headline, figure, caption, points, method, page):
    """A full-width figure with the reading beneath it.

    Multi-panel figures are 3:1 or wider; squeezed into a half-slide column they
    become unreadable.  Given the whole width they render at nearly twice the
    size, which is what a slide that exists to show a figure needs.
    """
    s = _blank(prs)
    tf = _tb(s, M, Inches(0.42), BODY, Inches(0.4))
    _para(tf, T(kicker), 12, BLUE, bold=True, first=True)
    tf = _tb(s, M, Inches(0.82), BODY, Inches(0.6))
    _para(tf, T(headline), 24, INK, bold=True, first=True)

    pic = _picture_fit(s, _fig(figure), M, Inches(1.55), BODY, Inches(3.40))
    if caption:
        tf = _tb(s, M, pic.top + pic.height + Inches(0.09), BODY, Inches(0.22))
        _para(tf, T(caption), 10.5, MUTED, first=True)

    # the caption sits just under the image, so the column rules start clear of it
    y = Inches(5.52)
    n = len(points)
    gap = Inches(0.34)
    cw = (BODY - gap * (n - 1)) / n
    for i, pt in enumerate(points):
        x = M + (cw + gap) * i
        _rule(s, y - Inches(0.18), x, cw, BLUE, Pt(1.6))
        tfp = _tb(s, x, y, cw, Inches(0.94))
        _para(tfp, T(pt), 11.5, INK, first=True)

    my = Inches(6.52)
    tf = _tb(s, M, my, BODY, Inches(0.62))
    _para(tf, T("HOW IT WAS MEASURED"), 10, BLUE, bold=True, first=True, space_after=3)
    for ln in method:
        _para(tf, T(ln), 10.5, MUTED, space_after=2)
    _footer(s, T(kicker), page)
    return s


def slide_table(prs, kicker, headline, header, rows, note, page, widths=None):
    s = _blank(prs)
    tf = _tb(s, M, Inches(0.5), BODY, Inches(0.4))
    _para(tf, T(kicker), 12, BLUE, bold=True, first=True)
    tf = _tb(s, M, Inches(0.92), BODY, Inches(0.9))
    _para(tf, T(headline), 25, INK, bold=True, first=True)

    ncol = len(header)
    widths = widths or [1.0 / ncol] * ncol
    top, rowh = Inches(2.1), Inches(0.46)
    tbl = s.shapes.add_table(len(rows) + 1, ncol, M, top, BODY,
                             rowh * (len(rows) + 1)).table
    for j, frac in enumerate(widths):
        tbl.columns[j].width = Emu(int(BODY * frac))
    for j, htxt in enumerate(header):
        c = tbl.cell(0, j)
        c.text = ""
        p = c.text_frame.paragraphs[0]
        r = p.add_run()
        r.text = T(htxt)
        r.font.size = Pt(13)
        r.font.bold = True
        r.font.color.rgb = INK
        r.font.name = "Calibri"
        c.fill.solid()
        c.fill.fore_color.rgb = WHITE
        _border(c, "T", "1B1F24", 1.1)      # top rule
        _border(c, "B", "1B1F24", 0.8)      # header rule
    for i, row in enumerate(rows, start=1):
        for j, val in enumerate(row):
            c = tbl.cell(i, j)
            c.text = ""
            p = c.text_frame.paragraphs[0]
            r = p.add_run()
            bold = val.startswith("*")
            r.text = T(val.lstrip("*"))
            r.font.size = Pt(12.5)
            r.font.bold = bold
            r.font.color.rgb = INK if bold else MUTED
            r.font.name = "Calibri"
            c.fill.solid()
            c.fill.fore_color.rgb = WHITE
            if i == len(rows):
                _border(c, "B", "1B1F24", 1.1)          # bottom rule
            else:
                _border(c, "B", "C9CFD6", 0.5)          # light row separator
    tf = _tb(s, M, top + rowh * (len(rows) + 1) + Inches(0.25), BODY, Inches(1.4))
    for i, line in enumerate(note):
        _para(tf, T(line), 13, MUTED, first=(i == 0), space_after=6)
    _footer(s, T(kicker), page)
    return s


def slide_quote(prs, kicker, big, body, page):
    s = _blank(prs)
    tf = _tb(s, M, Inches(0.6), BODY, Inches(0.4))
    _para(tf, T(kicker), 12, BLUE, bold=True, first=True)
    _rule(s, Inches(1.25), M, BODY, BLUE, Pt(2))
    tf = _tb(s, M, Inches(1.7), BODY, Inches(2.0))
    _para(tf, T(big), 30, INK, bold=True, first=True)
    tf = _tb(s, M, Inches(3.8), BODY, Inches(3.1))
    for i, line in enumerate(body):
        _para(tf, T(line), 15, MUTED, first=(i == 0), space_after=12)
    _footer(s, T(kicker), page)
    return s


def slide_pair(prs, kicker, headline, blocks, method, page):
    """Two or three findings side by side, each a short block.  Used where the
    result is a number rather than a picture."""
    s = _blank(prs)
    tf = _tb(s, M, Inches(0.5), BODY, Inches(0.4))
    _para(tf, T(kicker), 12, BLUE, bold=True, first=True)
    tf = _tb(s, M, Inches(0.92), BODY, Inches(0.9))
    _para(tf, T(headline), 25, INK, bold=True, first=True)

    n = len(blocks)
    gap = Inches(0.40)
    cw = (BODY - gap * (n - 1)) / n
    for i, (title, lines) in enumerate(blocks):
        x = M + (cw + gap) * i
        _rule(s, Inches(2.05), x, cw, BLUE, Pt(2))
        tf = _tb(s, x, Inches(2.25), cw, Inches(0.7))
        _para(tf, T(title), 15, INK, bold=True, first=True)
        tf = _tb(s, x, Inches(2.92), cw, Inches(2.70))
        for k, ln in enumerate(lines):
            _para(tf, T(ln), 12, MUTED, first=(k == 0), space_after=7)

    my = Inches(5.78)
    _rule(s, my - Inches(0.16), M, BODY)
    tf = _tb(s, M, my, BODY, Inches(1.05))
    _para(tf, T("HOW IT WAS MEASURED"), 10, BLUE, bold=True, first=True, space_after=4)
    for ln in method:
        _para(tf, T(ln), 11.5, MUTED, space_after=3)
    _footer(s, T(kicker), page)
    return s


def slide_index(prs, kicker, headline, groups, note, page):
    """The complete findings list, in columns, so nothing is left out."""
    s = _blank(prs)
    tf = _tb(s, M, Inches(0.45), BODY, Inches(0.4))
    _para(tf, T(kicker), 12, BLUE, bold=True, first=True)
    tf = _tb(s, M, Inches(0.85), BODY, Inches(0.6))
    _para(tf, T(headline), 24, INK, bold=True, first=True)

    n = len(groups)
    gap = Inches(0.34)
    cw = (BODY - gap * (n - 1)) / n
    max_items = max(len(items) for _, items in groups)
    font_size = 8.8 if max_items > 14 else (10.0 if max_items > 10 else 12.0)
    space_after = 1.0 if max_items > 14 else (2.5 if max_items > 10 else 8.0)

    for i, (title, items) in enumerate(groups):
        x = M + (cw + gap) * i
        _rule(s, Inches(1.62), x, cw, BLUE, Pt(1.6))
        tf = _tb(s, x, Inches(1.78), cw, Inches(0.4))
        _para(tf, T(title), 12.5, BLUE, bold=True, first=True)
        tf = _tb(s, x, Inches(2.20), cw, Inches(4.3))
        for k, (num, txt) in enumerate(items):
            p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
            p.space_after = Pt(space_after)
            r = p.add_run()
            r.text = num + "  "
            r.font.size = Pt(font_size)
            r.font.bold = True
            r.font.color.rgb = INK
            r.font.name = "Calibri"
            r2 = p.add_run()
            r2.text = T(txt)
            r2.font.size = Pt(font_size)
            r2.font.color.rgb = MUTED
            r2.font.name = "Calibri"
    if note:
        tf = _tb(s, M, Inches(6.62), BODY, Inches(0.4))
        _para(tf, T(note), 11, MUTED, first=True, italic=True)
    _footer(s, T(kicker), page)
    return s


# ---------------------------------------------------------------------------
# The deck.  Each finding slide carries its method, because in this project the
# two are not separable.
def build(lang="en"):
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H
    n = [0]

    def page():
        n[0] += 1
        return n[0]

    slide_title(prs, page())

    slide_pair(
        prs, "HOW TO READ THIS DECK",
        "Every claim carries the method that produced it",
        [("Why they are shown together",
          ["Several findings here are findings about method: a time base that was wrong, "
           "a bias invisible until a second instrument arrived, and one conclusion that had "
           "to be retracted.",
           "A claim shown without its method invites exactly that mistake."]),
         ("What the deck covers",
          ["All 200 findings. The findings that carry the argument get a slide each; "
           "the rest are grouped by theme.",
           "A full index near the end lists every one with its report section."]),
         ("Where the numbers come from",
          ["242,411 station-hours of in-situ data, 2001–2026.",
           "2,002 NOAA flask pairs at Bukit Kototabang, 2004–2025, on WMO scales, plus five "
           "reference sites.",
           "Every number is reproducible from the raw files."])],
        ["Report sections are cited on each slide so any claim can be traced to its "
         "derivation, and from there to the script that computes it."],
        page())

    slide_table(
        prs, "THE DATA", "Five in-situ stations, and one of them has flasks too",
        ["Code", "Station", "Setting", "Record", "Hours"],
        [["*BKT", "*Bukit Kototabang", "Remote mountain, GAW Global", "2001–2024", "*161,866"],
         ["*JMB", "*Jambi", "Lowland peat / plantation", "2023–2025", "14,486"],
         ["*KMY", "*Kemayoran", "Megacity urban core, Jakarta", "2023–2025", "16,495"],
         ["*PLU", "*Bariri, Lore Lindu", "Montane rainforest, GAW Regional", "2021–2026", "32,773"],
         ["*SRG", "*Sorong", "Coastal small city", "2021–2025", "16,791"]],
        ["Bukit Kototabang is also a NOAA cooperative flask site, sampled weekly in pairs "
         "since 2004 — CO₂, CH₄, CO and three species the hourly archive never measures: "
         "N₂O, SF₆ and H₂.",
         "That second record is what makes every absolute statement in this deck possible."],
        page(), widths=[0.07, 0.19, 0.34, 0.16, 0.24])

    # ---------------------------------------------------------------- PART 1
    slide_section(prs, "PART 1", "Before any science: is the archive usable?",
                  "Findings 1–6 · three defects, and a conclusion that had to be withdrawn",
                  page())

    slide_finding(
        prs, "FINDING 1 · THE TIME BASE",
        "One station changes its clock halfway through the record",
        ["Bukit Kototabang is stamped in local time to 31 Dec 2020 and in UTC from 1 Jan 2021. "
         "The other four are UTC throughout. Nothing in the files says so.",
         "Uncorrected, the afternoon window silently selects the night — doubling the apparent "
         "CO₂ growth rate from +2.28 to +5.08 ppm yr⁻¹.",
         "Units differ too: BKT reports CO and CH₄ in ppb, the others in ppm."],
        ["The boundary layer is deepest in mid-afternoon, so every surface species must "
         "reach its minimum then. That makes the diurnal cycle a clock.",
         "Diurnal phase by quarter: 2.2–3.6 h for eleven years, then 18.7–20.4 h from "
         "2021Q1 — the 7 h WIB offset, on one day."],
        page(), "f1_coverage_timebase.png",
        "Figure 1 — the diurnal minimum, as archived and after correction. · Report §2")

    slide_finding(
        prs, "FINDINGS 2–4 · THE EXTERNAL CHECK",
        "An independent instrument settles what the archive cannot",
        ["Matched hour by hour, the time-base correction moves CO₂ agreement from "
         "−8.50 ppm (r = 0.28) to +0.31 ppm (r = 0.77). CH₄ correlation goes 0.74 → 0.98.",
         "The in-situ CO₂ and CH₄ are on the WMO scale: sub-ppm agreement every year since 2019.",
         "And a defect no internal check could see — the CO reads 10–41 ppb too high before "
         "2019, stepping clean at an instrument change."],
        ["Every check inside an archive is differential. Differential checks are blind to a "
         "common-mode error.",
         "Pair each flask with the in-situ hour it was drawn in, under both time bases. "
         "Nothing else changes, so the time base is the only variable."],
        page(), "f2_flask_validation.png",
        "Figure 2 — flask against in-situ, and the CO bias step. · Report §4.1–4.3")

    slide_pair(
        prs, "FINDINGS 5–6 · WHAT THE SITE IS LIKE",
        "The Maritime Continent is a genuine CO₂ minimum",
        [("Finding 5 — lower than the South Pole",
          ["Bukit Kototabang's flask mean for 2015–2025 is 408.5 ppm.",
           "That is 5.5 ppm below Mauna Loa and 1.4 ppm below the South Pole — the lowest of "
           "the six sites compared.",
           "Warm-pool convection brings down free-tropospheric air over the most productive "
           "forest on Earth."]),
         ("Finding 6 — and hard to sample",
          ["NOAA rejects 30.9 % of the site's CO₂ flasks, against 2.6 % of the CH₄ from the "
           "same physical flask.",
           "Sampling or handling would reject both together. This is CO₂ specifically being "
           "unrepresentative — a vegetated ridge with upslope daytime flow.",
           "Expect to discard a comparable fraction in any new CO₂ work here."]),
         ("Why it matters",
          ["These two facts are why the deficits at the other stations are atmospheric, not "
           "instrumental.",
           "They are also why the next slide is a retraction rather than a finding."])],
        ["Afternoon medians, not the plume-rejecting 20th percentile: a low-biased statistic "
         "cannot be compared against an unbiased external mean. · Report §4.4–4.5"],
        page())

    slide_quote(
        prs, "FINDING 2 · A RETRACTION",
        "An earlier draft claimed the network's CO₂ was 5–9 ppm off-scale. It was wrong.",
        ["The draft compared a deliberately low-biased baseline against a published global mean, "
         "assumed a 1–3 ppm tolerance, and concluded the instruments were at fault.",
         "The flasks show the in-situ CO₂ agrees to +0.31 ppm. The deficit was real; the "
         "inference was not.",
         "The lesson is methodological: a differential network cannot be validated against a "
         "single global scalar plus an assumed tolerance. Only a co-located measurement on a "
         "traceable scale will do — which is the argument for keeping the flask programme "
         "running, and for starting one at Bariri.",
         "A second draft claim, that the equatorial CO₂ amplitude was 'close to the South "
         "Pole's', was also wrong: it rested on a quoted Mauna Loa amplitude of ~15 ppm, "
         "which the flask record measures at 6.9. · Report §14.1–14.2"],
        page())

    slide_figure_wide(
        prs, "FINDINGS 58–60 · FLASK PRECISION, SF₆ CLOCK & VERTICAL STRATIFICATION",
        "Flask pairs set a 0.15 ppm precision floor, and SF₆ clocks a 16-month mixing time",
        "f5_flask_pairs_sf6_vert.png",
        "Figure 5 — duplicate flask precision, SF₆ transport lag clock, and vertical gradients.",
        ["Finding 58: Paired flask duplicate differences across 22 years set single-flask uncertainty to 0.15 ppm for CO₂, 0.72 ppb for CH₄, 0.49 ppb for CO, 0.14 ppb for N₂O, 0.025 ppt for SF₆, and 0.64 ppb for H₂. Duplicate 95th percentile is 0.45 ppm for CO₂.",
         "Finding 59: Monotonic SF₆ accrual (0.323 ppt yr⁻¹) converts spatial concentration differences to transit times: BKT lags Arctic Barrow by 6.7 months (0.181 ppt) and leads the South Pole by 9.0 months (0.243 ppt), clocking a 15.9-month pole-to-pole mixing time.",
         "Finding 60: Vertical gradients at 19.5°N (Mauna Loa 3,397 m vs Kumukahi 3 m) show boundary-layer trapping: CH₄ depleted aloft by −16.5 ppb and CO by −9.1 ppb. Equatorial BKT sits below both in CO₂ (−5.3 and −5.7 ppm), confirming regional drawdown."],
        ["Duplicate pair error analysis over 634–960 NOAA flask pairs; linear transit time conversion τ = ΔC / (dC/dt); paired Student's t-test over 241 simultaneous monthly flask averages. · Report §4.7, §10.8–10.9 · scripts/a26_extra4.py"],
        page())

    # ---------------------------------------------------------------- PART 2
    slide_section(prs, "PART 2", "What is emitting, and what is absorbing",
                  "Findings 7–11, 29, 32, 35, 41 · the boundary layer as an instrument",
                  page())

    slide_pair(
        prs, "FINDINGS 7 & 41 · THE BOUNDARY LAYER",
        "The morning runs on the same clock everywhere — but the season does not",
        [("Finding 7 — a two-hour constant",
          ["The morning mixed layer erodes the nocturnal store with an e-folding time of "
           "1.94 h at Bariri, 2.05 Jambi, 2.19 BKT, 2.24 Kemayoran, 2.38 Sorong.",
           "A spread of 26 minutes across montane rainforest, drained peat, a megacity core, "
           "a mountain ridge and a coast.",
           "What they share is latitude: all within 6.2° of the equator, so all get the same "
           "insolation on the same schedule."]),
         ("Finding 41 — but only the lowlands feel the season",
          ["Diurnal amplitude, dry season over wet: Kemayoran ×1.93, Sorong ×1.66, "
           "Jambi ×1.24.",
           "The two montane stations: ×1.08 and ×1.08.",
           "Clear dry-season skies exaggerate both ends of the cycle — but only where the "
           "station sits inside the layer that responds."]),
         ("The practical consequence",
          ["τ ≈ 2 h is usable as a regional constant for sampling design, footprint models "
           "and flux-inversion operators.",
           "And at a lowland site, nearly half the wet-to-dry change in diurnal amplitude is "
           "meteorology, not source strength."])],
        ["Exponential fit to the 07:00–12:00 decline toward each day's own afternoon floor, "
         "keeping only clean decays (r < −0.9). · Report §5.2, §5.4"],
        page())

    slide_finding(
        prs, "FINDINGS 8 · SOURCE FINGERPRINTS",
        "One night's slope is an emission ratio — and nothing else can touch it",
        ["Jakarta's ΔCO/ΔCO₂ is 23.5 ppb ppm⁻¹, against 0.51 at Bariri. "
         "A factor of 46 between a megacity and primary rainforest.",
         "Bariri's 0.51 on 44 % of nights is essentially pure biological respiration — the "
         "network's natural zero point.",
         "Jambi fails the CO–CO₂ test on 97 % of nights but passes CH₄–CO₂ on 25 %. The failure "
         "rate is the measurement.",
         "That bounds Jakarta's fossil CO₂ at ≤ 63 % of its regional enhancement."],
        ["Within one night the boundary layer is an accumulation chamber, so the slope of one "
         "species against another is the emission ratio of the source mix — independent of "
         "dilution, of layer depth, and of calibration.",
         "That immunity is why this survives the CO bias of Finding 4."],
        page(), "f8_fingerprint.png",
        "Figure 8 — one point per tightly-coupled night. · Report §6")

    slide_finding(
        prs, "FINDING 9 · JAKARTA'S METHANE",
        "Jakarta's methane is not coming from its traffic",
        ["ΔCH₄/ΔCO is 0.64 — about fifty times the vehicle-exhaust ratio. Combustion can "
         "explain only 0.8–3.1 % of the excess.",
         "Sunday methane is +9.3 ppb [−11.8, +28.5] — indistinguishable from zero — while CO "
         "in the same air falls 39 ppb.",
         "One of fifteen weekday tests in the network is significant. It is Jakarta's CO.",
         "Bariri's null sets a detection limit: under 2 ppb of anthropogenic CO."],
        ["The working week modulates human activity and nothing else. Days resampled, "
         "medians, 3,000 bootstraps.",
         "Anomalies taken against each (month, hour) cell so neither the diurnal nor the "
         "seasonal cycle can leak in."],
        page(), "f10_weekly_ladder.png",
        "Figure 10 — every weekday test, and the regional ladder. · Report §7.2")

    slide_finding(
        prs, "FINDINGS 35 & 10 · JAKARTA, HOUR BY HOUR",
        "The two ratios run in antiphase — and the flux is landfill-scale",
        ["ΔCO/ΔCO₂ peaks at 38.0 ppb ppm⁻¹ at 20:00 and bottoms at 10.5 at 14:00.",
         "ΔCH₄/ΔCO₂ does the opposite — highest at 03–04:00, when traffic is at its minimum.",
         "When traffic falls away the mix that remains is methane-rich: the weekly result, now "
         "on twenty-four independent hours.",
         "The flux is ~65 g CH₄ m⁻² yr⁻¹ — roughly 2 Mt CO₂-equivalent a year over a "
         "10³ km² footprint, as the city's background rather than a hotspot."],
        ["Enhancements over each calendar month's own 5th percentile, so seasonal drift cannot "
         "masquerade as a diurnal cycle.",
         "The flux uses the nocturnal budget with an assumed 100–400 m layer depth — the one "
         "unmeasured quantity behind every absolute flux here."],
        page(), "f17_severity_onset.png",
        "Figure 17c — each ratio normalised to its own daily mean. · Report §7.3–7.4")

    slide_finding(
        prs, "FINDINGS 11 & 32 · JAMBI",
        "Jambi's peat is being consumed, on a human-lifetime clock",
        ["Nocturnal CO₂ efflux is 1.9× the intact-rainforest reference — about "
         "3,600 g C m⁻² yr⁻¹, at or above the GPP ceiling of a tropical forest.",
         "Respiration peaks in the DRY season — the opposite phase to Bariri, which peaks when "
         "it is wet. Wetting suppresses decomposition; drainage releases it.",
         "The excess, 16.7 t C ha⁻¹ yr⁻¹, empties a 1,000–3,000 t C ha⁻¹ store in 60–180 years.",
         "The same water-table drawdown makes the peat both respire faster and burn at all."],
        ["Magnitude and phase are independent measurements, and they agree. A warmer soil could "
         "explain the magnitude; nothing but drainage explains the phase.",
         "Layer depth cancels in the ratio to Bariri, and cancels entirely in the phase."],
        page(), "f13_external_checks.png",
        "Figure 13b — respiration phase, Jambi against Bariri. · Report §8")

    slide_finding(
        prs, "FINDING 29 · SOURCE OR SINK",
        "A second species separates photosynthesis from dilution",
        ["The morning CO₂ decline mixes two processes. CH₄ and CO have no photosynthetic sink, "
         "so their decline measures dilution alone.",
         "Forested sites remove CO₂ faster than either tracer; drained-peat Jambi shows nothing; "
         "Kemayoran is NEGATIVE — a megacity core is a net daytime CO₂ source.",
         "The stations order by land cover; both tracers agree.",
         "Jambi's null says its plantation photosynthesis is cancelled by its soil respiration."],
        ["The comparison must be paired — both species on the same morning. Unpaired medians "
         "compare different populations of days.",
         "A null test through the night, when there is no photosynthesis, is flat at Bukit "
         "Kototabang over 1,380 nights."],
        page(), "f7_carbon.png",
        "Figure 7 — extra CO₂ loss beyond dilution. · Report §5.3")

    slide_figure_wide(
        prs, "FINDINGS 61, 64, 66 · RUSH-HOUR FINGERPRINT, H₂ & N₂O DYNAMICS",
        "Weekend traffic drops isolate vehicular CO, H₂ reveals bimodal fires, and N₂O accelerates globally",
        "f11_regional_diurnal_n2o.png",
        "Figure 11 — rush-hour CO fingerprint, H₂ seasonality, and decadal N₂O acceleration.",
        ["Finding 64: Jakarta weekday morning rush CO spikes to 1,009.5 ppb and collapses by 23.7 % on weekends (ratio 1.30×), while CO₂ and CH₄ diurnal amplitudes are unchanged (0.97× and 0.99×), proving diurnal CO₂/CH₄ accumulation is decoupled from road traffic.",
         "Finding 61: Equatorial molecular hydrogen has a bimodal seasonal cycle (11.8 ppb harmonic amplitude), peaking in March (+6.3 ppb) and October (+5.0 ppb) during regional burning/transport, and reaching a minimum in June (−6.3 ppb) from soil uptake.",
         "Finding 66: Decadal N₂O growth accelerated by +0.21 to +0.24 ppb yr⁻¹ post-2014 synchronously across all latitudes from 71°N to 90°S, demonstrating uniform global forcing from agricultural nitrogen rather than localized tropical land-use."],
        ["Hourly weekday vs weekend diurnal composites at Kemayoran; 2-harmonic expansion on 15-year BKT flask H₂ series; Theil–Sen decadal slopes (2004–2013 vs 2014–2024) across 5 NOAA stations. · Report §7.6, §10.10, §12.9 · scripts/a26_extra4.py"],
        page())

    # ---------------------------------------------------------------- PART 3
    slide_section(prs, "PART 3", "Fire, and where the air comes from",
                  "Findings 12–19, 26, 33, 34, 36–40 · what a 24-year record resolves",
                  page())

    slide_finding(
        prs, "FINDINGS 12 & 33 · SEVERITY",
        "Severity is not one number",
        ["October 2015: monthly-median CO of 1,493 ppb at a GAW global background station — "
         "17× its own baseline, with 75 % of the month above 1,000 ppb.",
         "2015 had 28 days above 1,000 ppb and the largest burden; 2014 had the highest single "
         "peak (4,063 ppb) — on a weak El Niño.",
         "A day above 1,000 ppb at a background station has a 2.8-year return period; a "
         "2,000 ppb day, 8.8 years.",
         "ENSO modulates the extremes, not the baseline: r = +0.57 for the 95th percentile, "
         "−0.13 for the 10th."],
        ["Gumbel fitted to 24 annual maxima by the method of moments — the two-parameter case, "
         "because a shape parameter fitted to 24 points would fit noise.",
         "Peak, duration and burden rank the years differently, so a record summarised by any "
         "one alone will mislead."],
        page(), "f14_bkt_co_enso.png",
        "Figure 14 — 24 years of CO, against the Oceanic Niño Index. · Report §9.2–9.3, §9.8")

    slide_finding(
        prs, "FINDING 34 · PHENOLOGY",
        "The record dates the end of the burning season",
        ["The monsoon extinguishes the fires, so the CO collapse is a phenological marker that "
         "needs no rain gauge.",
         "Mean onset 6 October, standard deviation 33 days.",
         "El Niño delays it by 15 days per °C of the Oceanic Niño Index (r = +0.49 over "
         "20 years).",
         "So El Niño both intensifies the season and lengthens it — two mechanisms acting in "
         "the same direction."],
        ["Onset is the first day after 1 September on which the 10-day running median falls "
         "below that year's own median, so a high-baseline year is not systematically assigned "
         "a later date.",
         "An absolute threshold instead gives dates within about a week."],
        page(), "f17_severity_onset.png",
        "Figure 17b — onset date against ENSO. · Report §9.8")

    slide_pair(
        prs, "FINDINGS 13, 27, 28 · FIRE FINGERPRINTS",
        "One ratio classifies a burning season; a tracer recovers what was hidden",
        [("Finding 13 — the classifier",
          ["ΔCH₄/ΔCO separates 17 seasons with no overlap: peat-fire years at 0.04–0.08, "
           "every other year at 0.17–1.35.",
           "The 2019 value, 0.090 [0.085, 0.095], sits in the published Indonesian peat range.",
           "One instrument, no inventory, no transport model, no calibration — only the slope "
           "matters, so an offset in either channel cancels."]),
         ("Finding 27 — a fourth tracer",
          ["Hydrogen is enhanced with ΔH₂/ΔCO = 0.143 (r = 0.76).",
           "Nitrous oxide is not: its apparent fire signal vanishes once the air mass is "
           "removed — a negative slope would have been nonsense anyway.",
           "SF₆ carried through as a control returns zero, as a species with no fire source "
           "must."]),
         ("Finding 28 — CO₂ recovered",
          ["Raw, CO₂ shows no fire signal at 500 km: the enhancement is buried in biospheric "
           "and air-mass variability.",
           "Remove the SF₆-predicted air mass and the slope becomes significantly positive — "
           "ΔCO/ΔCO₂ = 67 ppb ppm⁻¹, in the biomass-burning range.",
           "CO₂ is usable as a fire tracer, but only after the covariance is removed."])],
        ["At this site the burning season and the monsoon reversal fall in the same months, so "
         "a flask that caught a plume also arrived in a particular air mass. SF₆ separates "
         "them. · Report §9.4, §9.7"],
        page())

    slide_pair(
        prs, "FINDINGS 14 & 38 · TIMESCALES",
        "Plumes clear before chemistry can act, and the record remembers for weeks",
        [("Finding 14 — faster than OH",
          ["Fire plumes relax with an e-folding time of 12–44 days.",
           "CO's chemical lifetime against OH is 1–3 months, so every event clears at or "
           "below the fast end of it — and the two largest clear in under two weeks.",
           "The decay measures when the fires stopped and how fast the air was flushed. "
           "Chemistry is a spectator."]),
         ("Finding 38 — two to six weeks of memory",
          ["The daily CO anomaly decorrelates with an e-folding lag of 19 days at Bukit "
           "Kototabang and 11 at Bariri.",
           "Far longer than a synoptic system, and inside the 20–90 day band that carries a "
           "quarter of the variance.",
           "BKT's longer memory is the fire signal: Sumatra's episodes are larger and last "
           "longer than anything Sulawesi sees."]),
         ("One phenomenon, three views",
          ["A 12–44 day clearance, a 19-day decorrelation, and a red spectrum with no discrete "
           "peak.",
           "Regional CO is set by episodes lasting two to six weeks — not by daily weather, "
           "and not by an oscillation.",
           "So the CO record can be read as a near-direct proxy for regional emission, with "
           "no OH correction."])],
        ["Exponential fits on the falling limb of each event; autocorrelation on the daily "
         "log anomaly after removing a centred 365-day mean. · Report §9.5, §9.9"],
        page())

    slide_finding(
        prs, "FINDINGS 16–18 · TRANSPORT",
        "The methane seasonal cycle is transport — proven, not argued",
        ["SF₆ is inert, has no natural source and no sink. Any seasonal cycle it shows is "
         "air-mass alternation and nothing else.",
         "Bukit Kototabang has the largest SF₆ seasonal cycle in the network — 0.38 ppt, four "
         "times Mauna Loa's, and in January the air is more SF₆-rich than the mid-Pacific "
         "Northern Hemisphere.",
         "Methane tracks it at r = 0.99: slope 200 ppb ppt⁻¹ against a measured network ratio "
         "of 207. CO₂ agrees at 0.99, N₂O at 1.16.",
         "CO alone shows a local excess, +35 % — and that is the fire season."],
        ["The expected slope is not assumed: it is measured between reference sites in the same "
         "network, so the prediction could have failed at any value.",
         "Earlier drafts could only argue for transport and caveat the alternative. That caveat "
         "is now withdrawn."],
        page(), "f3_flask_network.png",
        "Figure 3 — Bukit Kototabang inside the global network. · Report §10.1–10.3")

    slide_pair(
        prs, "FINDINGS 12, 19, 26, 39 · THE SEASONAL CYCLE",
        "Four species, four different answers about the same air",
        [("Methane — the transect",
          ["Amplitude declines eastward: 63 → 46 → 27 ppb from Sumatra to Sulawesi to Papua.",
           "And the phase lags with it: maximum 25 Jan → 8 Feb → 2 Mar, a 36-day progression.",
           "Too slow for advection — it is the monsoon boundary migrating, not an air mass "
           "propagating."]),
         ("Carbon dioxide — the amplitude",
          ["Bukit Kototabang's 5.53 ppm is 81 % of Mauna Loa's and 4.3× the South Pole's.",
           "Equatorial Indonesia sits firmly on the Northern-Hemisphere side of the gradient, "
           "despite every station lying south of the equator.",
           "Four of five sites peak in Jan–Mar: the Northern phase."]),
         ("CO and N₂O — the local part",
          ["Half of BKT's CO cycle is emitted nearby: a 30.6 ppb residual out of 56.4 observed, "
           "peaking in February and September — the two burning seasons.",
           "N₂O shows a 16 % excess over transport, a 0.38 ppb residual peaking in March, and "
           "sits 1.04 ppb above Samoa. The first quantitative statement about N₂O here."])],
        ["Every residual is the observed seasonal cycle minus the SF₆ cycle scaled by that "
         "species' measured interhemispheric gradient. · Report §10.4–10.7"],
        page())

    slide_finding(
        prs, "FINDINGS 15, 36, 37 · REGIONAL STRUCTURE",
        "A CO₂ sink region and a CO source region, at the same time",
        ["Referenced to Bariri, the network forms a clean ladder: Sorong +1.9 ppm CO₂, "
         "BKT +2.0, Jambi +4.6, Kemayoran +10.3.",
         "Against tropical marine air at Samoa, Bariri is −6.3 ppm in CO₂ and +25.6 ppb in CO. "
         "Sorong: −3.9 and +24.6.",
         "Both signs together are the region's signature — vegetation drawing CO₂ below the "
         "marine background while fire pushes CO above it.",
         "Coherence follows site type, not distance: the closest pair (618 km) is uncorrelated; "
         "distant clean pairs reach +0.69."],
        ["Afternoon well-mixed air, month-matched, so these are regional signals rather than "
         "local plumes.",
         "Two consequences: a 'regional background' from a polluted station is not regional, "
         "and network spacing should be set by site quality, not by a target separation."],
        page(), "f21_regional.png",
        "Figure 21 — coherence, the marine comparison, hydrogen. · Report §11")

    slide_figure_wide(
        prs, "FINDINGS 68 & 70 · HOVMÖLLER DYNAMICS & WAVE PROPAGATION",
        "CO₂ seasonal amplitude collapses 4× pole-to-equator; CH₄ monsoon wave marches eastward",
        "f19_hovmoeller_lat_lon.png",
        "Figure 19 — global latitude-time Hovmöller diagrams and Maritime Continent longitudinal wave migration.",
        ["Finding 68: Northern Hemisphere CO₂ seasonal drawdown wave collapses from 16.39 ppm at Arctic Barrow to 3.94 ppm at Bukit Kototabang and 1.12 ppm at South Pole, with a phase delay of 1.2 months per 30° latitude.",
         "Finding 70: Equatorial CH₄ seasonal crest propagates eastward across 31° of longitude from Sumatra (Dec) to Jambi/Bariri (Jan) and Sorong (Feb) at an effective zonal phase speed of ~40 km day⁻¹ (0.46 m s⁻¹).",
         "The latitudinal Hovmöller captures interhemispheric wave attenuation across the ITCZ, while the zonal Hovmöller tracks the trans-archipelago migration of the northwest monsoon trough."],
        ["Harmonic-polynomial extraction over 6 NOAA background stations (2004–2025) and afternoon background q20 across the 5 Indonesian stations. · Report §10.11, §10.13 · scripts/a28_extra5.py"],
        page())

    slide_figure_wide(
        prs, "FINDINGS 69, 73, 77 · TRANSPORT TIMESCALE, VERTICAL DAMPING & FORCING",
        "SF₆ clocks 1.23-year mixing; methane overcomes the equatorial CO₂ sink",
        "f20_hovmoeller_transport_forcing.png",
        "Figure 20 — SF₆ two-box exchange timescale, vertical damping across the trade-wind inversion, and regional forcing budget.",
        ["Finding 69: A two-box interhemispheric mass-balance model on the 0.399 ppt N-S SF₆ gradient yields an interhemispheric exchange timescale of τ_ex = 1.23 years (14.7 months), corroborating the empirical 15.9-month lag clock.",
         "Finding 73: Free-tropospheric Mauna Loa (3,397 m) exhibits systematic vertical damping of seasonal cycle amplitudes relative to sea-level Kumukahi (3 m): 18.1 % in CO₂, 12.3 % in CH₄, and 14.0 % in CO.",
         "Finding 77: Net forcing of the Maritime Continent over pristine marine air is +5.1 mW m⁻² — CH₄ (+70.9 ppb, +42.0 mW m⁻²) over the CO₂ deficit (−3.09 ppm, −40.5 mW m⁻²). A residual of two large opposing terms."],
        ["Two-box interhemispheric mass balance, harmonic vertical amplitude damping at 19.5°N, and IPCC AR6 simplified band forcing budget over Samoa SMO. · Report §10.12, §12.12, §13.3 · scripts/a28_extra5.py"],
        page())

    # ---------------------------------------------------------------- PART 4
    slide_section(prs, "PART 4", "Trends, budget, and what it is worth",
                  "Findings 20–25, 30, 31, 21, 42, 43 · twenty-two years on one scale",
                  page())

    slide_table(
        prs, "FINDINGS 22–25 · TWENTY-TWO YEARS",
        "Four long-lived gases are accelerating; CO is the exception",
        ["Species", "2004–2013", "2014–2025", "Change", "Hemispheric gap"],
        [["*CO₂", "+2.00 ppm yr⁻¹", "*+2.52", "*×1.26", "widening +1.37 %/yr"],
         ["*CH₄", "+3.65 ppb yr⁻¹", "*+9.38", "*×2.57", "widening +0.33 %/yr"],
         ["*N₂O", "+0.85 ppb yr⁻¹", "*+1.10", "*×1.29", "no trend"],
         ["*SF₆", "+0.278 ppt yr⁻¹", "*+0.360", "*×1.30", "widening +1.84 %/yr"],
         ["CO", "−3.28 ppb yr⁻¹", "−1.97", "decline slowing", "*CLOSING −0.80 %/yr"]],
        ["Only CO's hemispheric gap is closing — and CO is the only species here whose "
         "emissions are deliberately regulated.",
         "On this evidence air-quality regulation is visibly working on a hemispheric scale, "
         "and climate regulation is not yet. · Report §12.4, §12.6"],
        page(), widths=[0.14, 0.20, 0.16, 0.18, 0.32])

    slide_pair(
        prs, "FINDINGS 20 & 24 · ENSO",
        "Two stations agree on the anomaly, and each species answers differently",
        [("Finding 20 — the 2023 anomaly",
          ["Bukit Kototabang and Bariri, 2,000 km apart, put the 2023 El Niño CO₂ growth "
           "anomaly at +4.20 and +4.24 ppm yr⁻¹.",
           "Agreement to 0.04 ppm yr⁻¹ between two instruments on two islands, one of which "
           "needed an empirical repair and the other did not.",
           "A far more demanding test than agreeing on a level."]),
         ("Finding 24 — sensitivity, with lag",
          ["CO₂ growth: +0.82 ± 0.27 ppm yr⁻¹ per °C, at ZERO lag.",
           "CO: +32 ± 8 ppb yr⁻¹ per °C, also at zero lag — the fire term.",
           "CH₄: −10.8 ± 2.5 ppb yr⁻¹ per °C, at a 12-MONTH lag, and negative — drought "
           "drying tropical wetlands."]),
         ("Why the lags differ",
          ["A global-mean CO₂ series lags ENSO by months. This station sits inside the region "
           "where the anomaly is generated, so it sees it as it happens.",
           "Methane's year-long delay is the soil responding, and recovering, slowly.",
           "One climate perturbation, opposite signs, different timescales."])],
        ["Growth as a 12-month difference of the smoothed deseasonalised series, so the lag "
         "against the monthly ONI is scanned rather than assumed. · Report §12.3, §12.5"],
        page())

    slide_finding(
        prs, "FINDINGS 30–31 · CARBON BUDGET",
        "One equatorial station reproduces the global airborne fraction",
        ["Its 22-year flask growth of 2.32 ppm yr⁻¹ is 4.96 Pg C yr⁻¹ of atmospheric "
         "accumulation — 45 % of total emissions, inside the published 40–50 % band.",
         "The atmosphere took up 1.10 Pg C yr⁻¹ more in 2014–2025 than in 2004–2013.",
         "The 2023 El Niño anomaly is 4.4 Pg C yr⁻¹: larger than the entire global land sink "
         "of 3.2.",
         "One drought year cancels more than a year of terrestrial uptake."],
        ["The ppm-to-mass factor is derived, not looked up: the mass of the atmosphere divided "
         "by the molar mass of air, times the molar mass of carbon, gives 2.135 Pg C ppm⁻¹.",
         "This works only because CO₂ is well mixed. The same calculation on CO would be "
         "meaningless — and Finding 42 shows why."],
        page(), "f7_carbon.png",
        "Figure 7c — the station's growth rate, in budget units. · Report §12.7")

    slide_table(
        prs, "FINDING 21 · RADIATIVE FORCING",
        "Two sites are methane-heavy in forcing terms, not just in mixing ratio",
        ["Station", "CO₂ (mW m⁻²)", "CH₄ incl. indirect", "Total", "CH₄ share"],
        [["Sorong", "24.5", "5.7", "30.1", "19 %"],
         ["Bukit Kototabang", "26.2", "13.0", "39.2", "33 %"],
         ["*Jambi", "58.7", "38.1", "96.7", "*39 %"],
         ["*Kemayoran", "*131.2", "*53.0", "*184.1", "*29 %"],
         ["global budget, 1750–2019", "2,160", "540", "2,700", "20 %"]],
        ["The global budget attributes 20 % of well-mixed greenhouse forcing to methane. "
         "Jakarta's local dome runs at 29 % and Jambi's at 39 %.",
         "For a city or provincial inventory that is the ratio that matters: methane is a "
         "larger share of the local burden than the global average would suggest. · Report §13"],
        page(), widths=[0.26, 0.18, 0.22, 0.14, 0.20])

    slide_figure_wide(
        prs, "FINDING 44 · ENSO IN A WARMING OCEAN",
        "The gap between the two ENSO indices is itself a warming measurement",
        "f25_roni_warming.png",
        "Figure 25 — the tropical-mean SST anomaly recovered from two published indices, "
        "the seasons where they disagree, and the warming this network's own forcing implies.",
        ["RONI is the Niño3.4 anomaly minus the tropical mean, so ONI − RONI is the "
         "tropical-mean anomaly itself — a quantity neither index reports.",
         "It warms at +0.068, +0.120 and +0.222 °C per decade over 1950–2025, 1980–2025 "
         "and 2000–2025. The three intervals do not overlap: the rate has tripled.",
         "And that is a floor. The ONI's base period is re-centred every five years to "
         "remove exactly this trend; what survives is what outran the updates."],
        ["Arithmetic on two published CPC series; Theil–Sen on decimal year; three nested "
         "windows, because the hypothesis under test is that the rate is constant. "
         "· Report §14.1 · Methods §15c · scripts/a22_roni.py"],
        page())

    slide_table(
        prs, "FINDING 45 · WHICH INDEX YOU USE CHANGES THE ANSWER",
        "The label flips in 9 of 76 seasons — and where it mattered, ONI matched the fires",
        ["SON", "ONI", "class", "RONI", "class", "BKT peak daily CO", "Days > 1,000 ppb"],
        [["2014", "+0.51", "*El Niño", "+0.35", "neutral", "*4,063 ppb", "13"],
         ["2017", "−0.44", "neutral", "−0.82", "*La Niña", "321 ppb", "0"],
         ["2019", "+0.51", "*El Niño", "+0.15", "neutral", "*1,660 ppb", "1"]],
        ["In all three seasons the ONI class matched what the atmosphere did and the RONI "
         "class did not. 2014 gave the largest daily CO median in the 24-year record; 2019 "
         "the second-worst haze of the station era; 2017 — which RONI would have called "
         "La Niña, the wet phase — was an ordinary quiet year.",
         "Fire risk follows the zonal SST gradient that pushes convection off the Maritime "
         "Continent, and that responds to absolute eastern-Pacific warmth. RONI removes part "
         "of the signal along with the trend.",
         "Operationally: stay on ONI to forecast fire; use RONI to ask whether events are "
         "intensifying. · Report §14.2"],
        page(), widths=[0.08, 0.10, 0.14, 0.10, 0.14, 0.24, 0.20])

    slide_finding(
        prs, "FINDING 47 · THE CLOSURE",
        "This network's own forcing accrual implies the observed warming rate",
        ["Section 13 measured the accrual: 36.8 mW m⁻² yr⁻¹ at Bukit Kototabang, "
         "41.6 at Bariri — CO₂ plus indirect-uplifted CH₄.",
         "Converting with the AR6 transient climate response gives +0.18 and "
         "+0.20 °C per decade (range +0.14 to +0.25).",
         "Observed tropical SST warming since 2000: +0.222 [+0.202, +0.242] °C per decade. "
         "They agree.",
         "An SST index from ships and buoys, and two mixing-ratio trends measured on a "
         "mountain in Sumatra and in a Sulawesi rainforest — with nothing between them but "
         "one assessed sensitivity and two band-absorption formulae.",
         "It does NOT independently confirm TCR: TCR is an input here, not an output. The "
         "test is a consistency check on the chain from emissions to forcing to temperature.",
         "What it does show is that the greenhouse growth these stations measure is "
         "quantitatively sufficient to explain the observed warming. Nothing else is needed."],
        ["Ṫ = λḞ with λ = TCR/F₂ₓ = 1.8/3.71 = 0.485 K (W m⁻²)⁻¹. TCR, not ECS, because the "
         "forcing is ramping while the ocean still takes up heat.",
         "Omits N₂O, halocarbons and the aerosol offset — opposite signs, both smaller than "
         "the ±22 % the TCR range alone contributes. · Report §14.4 · Methods §15c"],
        page())

    slide_figure_wide(
        prs, "FINDINGS 49–50 · THE ONE CHECK A STATION CAN RUN ALONE",
        "A surface station's 24-hour mean CO₂ must exceed its afternoon mean",
        "f4_rectifier_eid.png",
        "Figure 4 — the diurnal rectifier at each station, the same statistic used as a "
        "quality test, and the Idul Fitri experiment.",
        ["The nocturnal layer is shallow and accumulates; the afternoon layer is deep and "
         "dilutes. So the rectifier is positive at every honest surface site — 8 to 18 ppm "
         "here, four to eight times the whole interhemispheric gradient.",
         "Afternoon-only sampling — flasks, inversions, this report's own background — is "
         "therefore measuring the free troposphere on purpose, and not the burden over the "
         "site. The two differ by more than a decade of growth.",
         "Sorong before June 2023 runs at −29 ppm with 47 % of days negative. No boundary "
         "layer does that. It re-flags the exact period the report found by another route — "
         "with no reference site, no flask, no second station."],
        ["A sign test on an internal difference, invariant to any offset or scale error, so "
         "it needs no external anchor. · Report §4.6 · Methods §16b"],
        page())

    slide_finding(
        prs, "FINDING 48 · A NATURAL EXPERIMENT",
        "The week Jakarta stopped driving",
        ["At Idul Fitri several million people leave the city — mudik, the largest annual "
         "migration in the country. Vehicles stop; landfill and wastewater do not.",
         "The holiday moves ~11 days a year through the Gregorian calendar, so it is not "
         "confounded with season. Two occurrences fall inside Kemayoran's record.",
         "Rush-hour CO falls 31.5 % (p = 0.038). CH₄ moves −0.1 % (p = 0.98). CO₂ moves "
         "−1.0 %, not significant.",
         "The structure across windows is the proof: largest at the 06–09 rush, smaller "
         "over all hours, statistically absent at night — the diurnal profile of traffic, "
         "not of a landfill or a weather change.",
         "This is Findings 8 and 9 again, reached without a single emission ratio. Two "
         "independent methods, one using nocturnal coupling and one using a calendar.",
         "Two events is a small experiment. CO₂ moved much less than CO and much more than "
         "CH₄ — the right answer for a mixed source, but not yet a measurement."],
        ["Holiday window −2 to +5 days; control −28 to −8 and +11 to +31. Each year "
         "normalised by its own control median, then pooled; 20,000-permutation test on the "
         "difference of medians. · Report §7.5 · Methods §16b"],
        page())

    slide_figure_wide(
        prs, "FINDINGS 51–53 · WHAT THE NETWORK CAN DETECT",
        "Most of n is not there, and CO needs fifteen years",
        "f26_detection.png",
        "Figure 26 — years of record needed per species, the cost of discrete sampling, and "
        "nominal against effective sample size for six of the report's own correlations.",
        ["The ENSO growth-rate sensitivities of §12.5 have about 12 independent "
         "observations, not 215 — roughly the number of ENSO events in the record. "
         "Corrected intervals quadruple; none is significant at 95 %.",
         "CO needs 15.5 years to show its own trend against 1.4 for CO₂ and 0.4 for SF₆ — "
         "a factor of 38, driven entirely by fire-episode noise. The 2021–2023 stations "
         "cannot give a CO trend before ~2036.",
         "Weekly flask sampling rebuilds the monthly mean to 1.51 ppm — 65 % of one year's "
         "CO₂ growth. The flasks and the analysers are not substitutes; that is the price "
         "of pretending they are."],
        ["Bartlett's n_eff, Weatherhead's n*, and 200 random sampling phases. The annual "
         "results are unaffected. · Report §16 · Methods §16b"],
        page())

    slide_quote(
        prs, "FINDINGS 42–43, 46 · NEGATIVE RESULTS",
        "What this record settles in the negative",
        ["Fire years leave no detectable trace in the CO₂ growth rate at the same station "
         "(r = −0.29 same year, −0.06 the next). The most extreme regional fire signal in any "
         "tropical background record is invisible in the budget it feeds — a caution against "
         "reading regional records as regional budgets.",
         "No seasonal amplitude and no measure of cross-equatorial reach shows a trend over "
         "twenty years. Five separate tests, all consistent with no change. The constancy of "
         "transport is a useful control: the accelerations in Part 4 are changes in emissions, "
         "not changes in how the air arrives.",
         "CO over Sumatra is not MJO-modulated: a quarter of the variance sits in the 20–90 day "
         "band, but with no discrete peak. It is fire episodes decaying.",
         "Background tropical warming does not itself drive the fires (Finding 46). The two ENSO "
         "indices are nearly interchangeable as continuous predictors, and the warming term alone "
         "has no correlation with the fire extremes: r = −0.03 for the peak, +0.07 for days above "
         "1,000 ppb. The burning tracks ENSO variability, not the mean state. · Report §9.5, §14.3, §15.5"],
        page())

    # ---------------------------------------------------------------- index
    slide_index(
        prs, "THE COMPLETE LIST", "All 200 findings (1 of 7)",
        [("Data integrity · §1–4",
          [("1", "The time base switches mid-record"),
           ("2", "Flasks confirm the correction from outside"),
           ("3", "In-situ CO₂ and CH₄ are on the WMO scale"),
           ("4", "Pre-2019 CO is biased 10–41 ppb high"),
           ("5", "The Maritime Continent is a CO₂ minimum"),
           ("6", "NOAA rejects 31 % of the site's CO₂ flasks"),
           ("49", "Afternoon sampling understates CO₂ by 8–18 ppm"),
           ("50", "A negative rectifier flags bad data, alone"),
           ("58", "Flask pairs set 0.15 ppm CO₂ precision floor")]),
         ("Surface processes · §5–8",
          [("7", "Morning erosion τ = 1.9–2.4 h at all five sites"),
           ("8", "Jakarta ΔCO/ΔCO₂ = 23.5; fossil ≤ 63 %"),
           ("9", "≳97 % of Jakarta's methane is not combustion"),
           ("10", "Jakarta's CH₄ flux ≈ 65 g m⁻² yr⁻¹"),
           ("11", "Jambi is drained peat — magnitude and phase"),
           ("29", "A tracer separates photosynthesis from dilution"),
           ("48", "Idul Fitri: the week Jakarta stopped driving"),
           ("32", "Peat loss 16.7 t C ha⁻¹ yr⁻¹, 60–180 yr clock"),
           ("35", "Jakarta's two ratios run in antiphase by hour"),
           ("41", "Dry-season amplification, lowlands only"),
           ("64", "Weekend traffic drop isolates commuter CO"),
           ("67", "Drained peat respiration dry-amplified (1.17×)"),
           ("76", "Monsoonal modulation of nocturnal canopy CO₂")]),
         ("Fire · §9",
          [("12", "October 2015: 1,493 ppb monthly median"),
           ("13", "ΔCH₄/ΔCO classifies a burning season"),
           ("14", "Plumes clear in 12–44 d, faster than OH"),
           ("15", "The flask record gives a sound CO trend"),
           ("27", "H₂ is a fire tracer; N₂O is not"),
           ("28", "SF₆ correction recovers a fire CO₂ signal"),
           ("33", "Severity differs by peak, duration, burden"),
           ("34", "The CO collapse dates the monsoon onset"),
           ("38", "CO anomalies persist 19 days"),
           ("40", "H₂ tracks CO only in burning months"),
           ("75", "Clean CO floor steady at 75.9 ± 2.8 ppb")])],
        "Findings 16–26, 30–31, 36–37, 39, 42–47, 51–57, 59–63, 65–66, 68–74, 77 continue on the next slide; 78–100 on the one after.", page())

    slide_index(
        prs, "THE COMPLETE LIST", "All 200 findings (2 of 7)",
        [("Transport · §10–11",
          [("16", "CH₄'s seasonal cycle is transport, r = 0.99"),
           ("17", "BKT has the largest SF₆ cycle in the network"),
           ("18", "CO is the only species with a local excess"),
           ("19", "Equatorial CO₂ amplitude is 81 % of Mauna Loa's"),
           ("26", "Half the CO cycle is emitted nearby"),
           ("39", "N₂O has a modest regional source"),
           ("59", "SF₆ transport clock: 15.9-month mixing time"),
           ("60", "Vertical gradient at 19.5°N: MLO vs KUM"),
           ("61", "Equatorial H₂ bimodal seasonal cycle"),
           ("36", "A CO₂ sink region and a CO source region"),
           ("37", "Coherence follows site type, not distance"),
           ("62", "Bariri is 2.0 ppm lower in CO₂ than BKT"),
           ("63", "Clean Sorong matches marine CO₂ deficit"),
           ("68", "CO₂ seasonal wave attenuation to 3.9 ppm"),
           ("69", "SF₆ 2-box mixing timescale: 14.7 months"),
           ("70", "Trans-archipelago CH₄ wave phase speed")]),
         ("Trends and budget · §12–13",
          [("20", "Two stations resolve the 2023 El Niño anomaly"),
           ("22", "Four long-lived gases are accelerating"),
           ("23", "CH₄ growth 2.6× higher in 2014–2025"),
           ("24", "ENSO sensitivity, with the lag measured"),
           ("25", "The hemispheric gap closes only for CO"),
           ("30", "The airborne fraction from one station: 45 %"),
           ("31", "The 2023 anomaly exceeds the land sink"),
           ("21", "Jakarta's dome is 184 mW m⁻², 29 % methane"),
           ("54", "CH₄–N₂O covary; CO and SF₆ do not"),
           ("55", "N₂O's seasonal cycle is 89 % transport"),
           ("56", "H₂ rising 1.5 ppb/yr — a pre-deployment baseline"),
           ("57", "The CO₂ deficit widens against the pole only"),
           ("66", "Global synchrony in N₂O decadal acceleration"),
           ("71", "Interhemispheric CO₂ growth asymmetry in ENSO"),
           ("72", "Post-2014 CH₄ surge is 90 % tropical in origin"),
           ("73", "Vertical damping across inversion at 19.5°N"),
           ("74", "Decoupling of growth anomaly covariance"),
           ("77", "Regional forcing enhancement: +5.1 mW m⁻²")]),
         ("ENSO, warming, and nulls · §14–16",
          [("44", "ONI − RONI measures the tropical warming"),
           ("45", "The ENSO label flips in 9 of 76 seasons"),
           ("46", "Warming itself does not drive the fires"),
           ("47", "Forcing accrual implies the observed warming"),
           ("42", "Fire years leave no trace in CO₂ growth"),
           ("43", "No 20-year trend in amplitude or reach"),
           ("65", "LIMITED: N₂O growth has no ENSO response"),
           ("51", "LIMITED: n_eff ≈ 12, not 215, for §12.5"),
           ("52", "CO needs 15.5 yr of record; CO₂ needs 1.4"),
           ("53", "Weekly flasks cost 1.5 ppm on the monthly mean"),
           ("—", "RETRACTED: a claimed 5–9 ppm CO₂ scale offset"),
           ("—", "CORRECTED: the equatorial CO₂ amplitude")])],
        None, page())

    slide_index(
        prs, "THE COMPLETE LIST", "All 200 findings (3 of 7)",
        [("Accounting-facing measurements",
          [("78", "The enhancement ladder in CO₂-equivalent"),
           ("79", "Data return: BKT CO₂ exists in 12 of 25 years"),
           ("80", "NULL: clean-air frequency does not rank sites"),
           ("81", "Hourly coupling identifies the source type"),
           ("82", "Persistence: N₂O 5.9 months, the rest ~2"),
           ("83", "Two instruments agree on the trend to 0.8 ppm/yr"),
           ("84", "Nocturnal rate, separated from the layer depth"),
           ("85", "CH₄:CO₂ — the ratio the depth cancels out of"),
           ("86", "Jakarta's weekend is 1.71 ppm CO₂e, 8 % of CO₂"),
           ("87", "NULL: flask CO₂ misses the global growth signal"),
           ("88", "Detectable step: 6.10 ppm in 12 months, 2.73 in 60"),
           ("89", "Seasonal amplitude stable, but ±32 % year to year")]),
         ("Nilai Ekonomi Karbon · §17",
          [("90", "Jambi's peat: 61.18 t CO₂ ha⁻¹ yr⁻¹ priced"),
           ("91", "Jakarta's methane: the depth beats the price 4:2.3"),
           ("92", "The air splits the city between two ministries"),
           ("93", "Verifiable: a quarter at KMY, a half at JMB, in 5 yr"),
           ("94", "The rectifier biases crediting by 100–476 %"),
           ("95", "Which station can do which job, scored from data"),
           ("96", "The measurement is the smallest uncertainty (×1.18)")]),
         ("...and what it cannot do",
          [("97", "A 25-year credit covers a third of the peat store"),
           ("98", "Reversal is a certainty, not a risk: 92 % in 5 yr"),
           ("99", "What each verification mode actually verifies"),
           ("100", "NULL: no national-scale verification — 2–40 % of"),
           ("", "the resolvable step, for the whole NDC range")])],
        "Findings 78–89 re-express measurements from Parts I–IV in accounting units; 90–100 are Part VI. "
        "Two of the eleven NEK findings are negative, and the last one is the most consequential.", page())

    slide_index(
        prs, "THE COMPLETE LIST", "All 200 findings (4 of 7)",
        [("Timing and analyst choices · §18.1–18.7",
          [("101", "Daily tracer loops retain source timing"),
           ("102", "Sorong's CO₂–CH₄ loop reverses by season"),
           ("103", "Jakarta combustion coupling peaks at night"),
           ("104", "Baseline percentile choice is material"),
           ("105", "One-hour afternoon shifts are immaterial"),
           ("106", "Subtraction cannot choose the reference"),
           ("107", "Broad station order repeats in both years")]),
         ("Coverage and maintenance · §18.8–18.12",
          [("108", "Maintenance gains are largest but sublinear"),
           ("109", "Outages cluster by month"),
           ("110", "One outage can erase a season"),
           ("111", "Only 41.1 % of BKT hours pair all gases"),
           ("112", "Complete months change the station ranking")]),
         ("Source and event information · §18.13–18.20",
          [("113", "Only Jakarta has a weekday morning signal"),
           ("114", "Jakarta rush ΔCO/ΔCO₂ = 26.1"),
           ("115", "Season changes the diurnal source mixture"),
           ("116", "Fire CO persists; traffic CO is brief"),
           ("117", "Three-day event recovery is tracer-specific"),
           ("118", "No natural extreme threshold fits every site"),
           ("119", "NULL: no daily common mode"),
           ("120", "NULL: no station substitutes for another")])],
        "All twenty are generated by scripts/a33_extra7.py into separate q_*.csv files. "
        "The two spatial nulls are operationally important: the network is complementary, not redundant.", page())

    slide_index(
        prs, "THE COMPLETE LIST", "All 200 findings (5 of 7)",
        [("Dependence structure · §19.1–19.10",
          [("121–122", "PCA and effective tracer dimension"),
           ("123", "Conditional dependence separates source pairs"),
           ("124–125", "Upper- and lower-tail dependence"),
           ("126", "Mutual information confirms two fingerprints"),
           ("127–128", "Rank nonlinearity and quantile slopes"),
           ("129–130", "Day/night divergence and event-hour entropy")]),
         ("Scale and spatial information · §19.11–19.24",
          [("131–133", "Variance decomposition, averaging and Allan scale"),
           ("134–136", "Variance trend, change points and sign stability"),
           ("137", "Conditional-dependence graphs differ by site"),
           ("138–141", "Synchrony, lags, dimension and canonical links"),
           ("142–144", "Reconstruction, classification and separation")]),
         ("Extremes and falsification · §19.25–19.30",
          [("145", "BKT extremes are bursty"),
           ("146", "BKT fire CO clusters for 8.39 hours"),
           ("147", "Composite recovery is tracer-specific"),
           ("148", "One exponential is not a universal law"),
           ("149", "Hysteresis is timing, not plume size"),
           ("150", "Nonlinear and conditional evidence synthesised")])],
        "All thirty are generated by scripts/a34_extra8.py into separate aa_*.csv files. "
        "Selected null results remain: no robust propagation lag and no physical variance change point.", page())

    slide_index(
        prs, "THE COMPLETE LIST", "All 200 findings (6 of 7)",
        [("Boundary-layer transitions · §19.31–19.33",
          [("151", "BKT transition clock: 09:00 to 18:00"),
           ("152", "Jambi morning collapse is −15.06 ppm"),
           ("153", "Jakarta has the longest transition separation"),
           ("154", "Bariri has the strongest evening rebuild"),
           ("155", "Sorong's evening rebuild is weakest"),
           ("156", "BKT accumulation halves after midnight"),
           ("157", "NULL: Jambi does not resolve saturation"),
           ("158", "LIMITED: Jakarta slowdown is marginal"),
           ("159", "Bariri accumulation slows after midnight"),
           ("160", "Sorong has the strongest proportional slowdown")]),
         ("Carry-over and monsoon shift · §19.33–19.34",
          [("161", "BKT carries 56.2% into the next dawn"),
           ("162", "NULL: Jambi has 0.8% next-dawn carry-over"),
           ("163", "Jakarta largely resets overnight"),
           ("164", "Bariri retains 19.7% next-dawn memory"),
           ("165", "NULL: Sorong has no resolved carry-over"),
           ("166", "BKT seasonal shift is methane-led"),
           ("167", "Jambi seasonal shift is methane-led"),
           ("168", "Jakarta is seasonally stable in all gases"),
           ("169", "Bariri CH₄ has the largest seasonal shift"),
           ("170", "Sorong's multigas shift is methane-led")]),
         ("Multigas regimes · §19.35",
          [("171", "BKT isolates a CO-rich fire regime"),
           ("172", "Jambi's rare regime elevates all three gases"),
           ("173", "Jakarta's rare regime is methane-rich"),
           ("174", "Bariri regimes are the least separated"),
           ("175", "Sorong exposes an outlier-cluster failure mode")])],
        "Generated by scripts/a35_extra9.py. Nulls and the Sorong clustering failure are retained as findings, not filtered out.", page())

    slide_index(
        prs, "THE COMPLETE LIST", "All 200 findings (7 of 7)",
        [("Compound extremes and ageing · §19.36–19.37",
          [("176", "BKT compound tail: 6.7× independence"),
           ("177", "Jambi compound tail: 7.5×"),
           ("178", "Jakarta combustion tail: 14.3×"),
           ("179", "Bariri has the weakest compound tail"),
           ("180", "Sorong's dominant tail is CH₄–CO"),
           ("181", "BKT composition is stable to day 3"),
           ("182", "Jambi becomes methane-richer"),
           ("183", "Jakarta: no methane enrichment"),
           ("184", "Bariri has the slowest CO recovery"),
           ("185", "Sorong becomes methane-richer")]),
         ("Memory and annual stability · §19.38–19.39",
          [("186", "BKT memory exceeds shuffled chance"),
           ("187", "Jambi daily memory is significant"),
           ("188", "Jakarta CO persists between days"),
           ("189", "Bariri has the strongest memory"),
           ("190", "Sorong memory survives QC"),
           ("191", "BKT edge positive in all 12 years"),
           ("192", "Jambi edge repeats across three years"),
           ("193", "Jakarta edge is highly reproducible"),
           ("194", "Bariri edge varies twofold"),
           ("195", "Sorong edge retains one sign")]),
         ("Fixed-hour sampling · §19.40",
          [("196", "BKT span: 20.82 ppm"),
           ("197", "Jambi span: 43.60 ppm"),
           ("198", "Jakarta best hour: 22:00"),
           ("199", "Bariri 20:00 ≈ daily mean"),
           ("200", "Sorong best hour: 09:00")])],
        "The least-biased hour for a daily mean is not the correct hour for regional-background sampling; those are different observing objectives.", page())

    # ---------------------------------------------------------------- PART 6
    slide_section(prs, "PART 6", "What any of this is worth under Nilai Ekonomi Karbon",
                  "Findings 90–100 · Presidential Regulation 98/2021 · two negative results",
                  page())

    slide_figure_wide(
        prs, "FINDINGS 90, 91, 96 · WHAT A MEASURED SIGNAL IS WORTH",
        "The measurement is the cheapest, best-constrained term in the chain",
        "f28_nek_value.png",
        "Figure 28 — Jambi's peat loss priced at four carbon prices; the uncertainty budget of that claim; and Jakarta's methane against the assumed nocturnal layer depth.",
        ["Finding 90: Jambi's measured peat loss, 61.18 t CO₂ ha⁻¹ yr⁻¹, is worth IDR 1.84 million per hectare per year at the carbon-tax floor and IDR 3.20 million at the IDXCarbon average.",
         "Finding 91: Jakarta's background methane is worth IDR 47.7–190.6 billion a year — a factor of four, set by the unmeasured layer depth. Every Indonesian carbon price spans 2.3.",
         "Finding 96: In that claim's uncertainty budget the layer depth contributes ×4.00, the store depth ×3.00, the price ×2.32 — the measurement ×1.18, the smallest term of the four."],
        ["Stoichiometric conversion at 44.01/12.011 and GWP-100 = 27.9, with each term's span reported separately rather than multiplied out. · Report §17.2, §17.3, §17.8 · scripts/a31_nek.py"],
        page())

    slide_figure_wide(
        prs, "FINDINGS 93, 100 · WHAT THE NETWORK CAN VERIFY",
        "A quarter of a city's source in five years — and nothing at national scale",
        "f27_nek_detectability.png",
        "Figure 27 — station-scale detectability against each site's measured enhancement, and the national-scale signal of the full width of Indonesia's 2035 NDC range.",
        ["Finding 93: Over five years the network could verify a 24 % cut at Kemayoran and a 52 % cut at Jambi. At Bukit Kototabang and Sorong the detection threshold exceeds the entire local signal, so not even its complete disappearance would register.",
         "Finding 100: The full 231.2 MtCO₂e width of the Second NDC 2035 range produces a regional signal of 0.05–1.09 ppm, against the 2.73 ppm a five-year record can resolve — 2 % to 40 % of what would be needed.",
         "The conclusion is not that atmospheric measurement is useless to NEK. It is that its scale is the project and the city, and its role is to tell a pricing system when its physics is wrong."],
        ["Two-window power calculation with Bartlett effective sample size, and a single-box steady-state ventilation model over the national land area. · Report §17.5, §17.12 · scripts/a30_extra6.py, scripts/a31_nek.py"],
        page())

    slide_table(
        prs, "FINDING 99 · WHAT EACH MODE ACTUALLY VERIFIES",
        "Read the column as limits, not as promises",
        ["Mode of measurement", "What it verifies", "Limit", "F."],
        [["Co-located flask vs in-situ, levels", "that a station's scale is not drifting", "0.31 ppm", "3"],
         ["Co-located flask vs in-situ, growth", "that a trend is not an instrument artefact", "0.81 ppm yr⁻¹", "83"],
         ["Continuous in-situ, 5-year window", "a step change in the regional background", "2.73 ppm CO₂e", "88"],
         ["*Nocturnal ratio (depth cancels)", "*the methane share of a site's CO₂e", "*17.2 % at KMY", "*85"],
         ["*Diurnal rectifier sign test", "*that a station is physically functioning, with no external data",
          "*the failing site read −29.2 ppm", "*50"],
         ["*Public-holiday natural experiment", "*a sector's contribution, with no emission ratio",
          "*31.5 % CO drop", "*48"]],
        ["Nothing here verifies a tonne. The three starred rows are the ones an inventory cannot produce: "
         "a ratio in which the unmeasured layer depth cancels, a sign test that needs no external reference, "
         "and a public holiday that switches off one sector. · Report §17.11"],
        page(), widths=[0.30, 0.38, 0.24, 0.08])

    # ---------------------------------------------------------------- PART 7
    slide_section(prs, "PART 7", "What the observing system itself resolves",
                  "Findings 101–120 · timing, robustness, missingness and spatial information",
                  page())

    slide_quote(
        prs, "FINDINGS 101–107 · TIMING AND ROBUSTNESS",
        "The timing is informative; the declared baseline matters more than its clock",
        ["Daily CO₂–CH₄ loops turn one way at BKT and Bariri and the other at Jambi and Jakarta. "
         "Sorong alone reverses between wet and dry half-years — a phase signal a scalar correlation discards.",
         "Changing the baseline from the 10th to 30th afternoon percentile moves CO₂ by 2.6–6.2 ppm. "
         "Moving the five-hour afternoon window one hour moves it by at most 1.24 ppm.",
         "Changing the reference changes every enhancement but cannot choose the reference: the common-period "
         "station ordering is invariant. Broadly, Kemayoran remains the source end and Bariri the clean end in both overlap years.",
         "Paired complete-day polygons; percentile and clock perturbations; common 2023–2024 station ladder. "
         "· Report §18.1–18.7 · Methods §18.1–18.3 · scripts/a33_extra7.py"],
        page())

    slide_quote(
        prs, "FINDINGS 108–120 · NETWORK DESIGN",
        "Repairing hours helps; replacing a station with another does not",
        ["Twenty more points of valid return reduce a sampling-limited threshold by 14 % at Sorong and 11 % at Jambi, "
         "but only 2.5 % at already-complete Kemayoran. The gain is real and sublinear.",
         "Only 28 of Sorong's 52 calendar months clear 50 % return. BKT's headline archive has all three gases paired "
         "in only 41.1 % of its archived hours.",
         "Jakarta alone carries a weekday morning signal: +201 ppb CO. Its rush increment has 26.1 ppb CO per ppm CO₂, "
         "against 0.2–1.5 elsewhere.",
         "NULL: daily anomalies have no network-wide common mode, and leave-one-station-out predictions are worse than "
         "predicting no anomaly. The five sites are complementary, not redundant. · Report §18.8–18.20 · Methods §18.4–18.7"],
        page())

    slide_quote(
        prs, "FINDINGS 121–130 · NONLINEAR DEPENDENCE",
        "Jakarta is a CO₂–CO system; BKT is a CO₂–CH₄ system",
        ["PCA compresses Jakarta's three gases to 1.72 effective dimensions, while Bariri retains 2.48. "
         "After controlling the third gas, Jakarta CO₂–CO remains +0.846 and BKT CO₂–CH₄ +0.798.",
         "Jakarta's upper-tail CO₂–CO dependence is 0.715, fourteen times independence. Mutual information "
         "is 0.557 excess nats for that pair and 0.507 for BKT CO₂–CH₄.",
         "Jakarta CH₄–CO is nonlinear: Pearson +0.370, Spearman +0.702. Its CO-on-CO₂ quantile slope "
         "steepens from 0.900 at q10 to 1.413 at q90.",
         "Robustly standardised month-hour anomalies; eigenanalysis, partial correlation, empirical copula tails, "
         "permuted mutual information and linear-programming quantile regression. · Report §19.1–19.10 · Methods §19.1–19.3"],
        page())

    slide_quote(
        prs, "FINDINGS 131–144 · SCALE AND NETWORK INFORMATION",
        "Averaging helps urban noise; it cannot manufacture a regional mode",
        ["Hour of day explains 65 % of Bariri CO₂ variance. Thirty-day averaging retains only 4–8 % of "
         "Jakarta/Jambi variance but 59–66 % of persistent BKT/Bariri background variance.",
         "The five-station daily participation ratio is 4.61–4.92 of five. Regularised canonical correlations "
         "are ≤0.234 on overlaps above 100 days: even optimised multigas combinations remain local.",
         "Leave-year-out reconstruction works where sources couple—Jakarta CO₂ R² 0.744 and CO 0.717—but fails "
         "for every Bariri gas. Three anomalies classify station at only 26.5 % against 20 % chance.",
         "Sequential variance decomposition, Allan scaling, eigen-dimension, regularised CCA and blocked prediction. "
         "· Report §19.11–19.24 · Methods §19.3–19.5"],
        page())

    slide_quote(
        prs, "FINDINGS 145–150 · EXTREMES AND FALSIFICATION",
        "Fire extremes cluster; recovery has no universal law",
        ["BKT's daily extremes are strongly bursty (0.59–0.70). Its fire CO runs extremal index is 0.119—" 
         "8.39 consecutive extreme hours per run.",
         "Half-recovery takes five days for Bariri CH₄, three for BKT CO, and one for most Jambi/Jakarta gases. "
         "Power-law recovery wins ten of fifteen four-point composites; several fire/forest tracers prefer exponential.",
         "A falsification test finds standardised hysteresis area unrelated to daily plume range: absolute Spearman ρ ≤0.10. "
         "The loop records timing, not amplitude.",
         "Inter-event burstiness, runs extremal index, normalised recovery composites, competing AIC models and a preregistered "
         "amplitude control. · Report §19.25–19.30 · Methods §19.6–19.7 · scripts/a34_extra8.py"],
        page())

    # ---------------------------------------------------------------- close
    slide_table(
        prs, "WHAT TO DO NEXT", "Four things the data ask for",
        ["", "Action", "Because"],
        [["*1", "*Fix the time base in the archive",
          "Every diurnal, flux and trend product built on the delivered files is currently wrong"],
         ["*2", "*Withdraw the pre-2019 CO series from trend work",
          "A 10–41 ppb bias that steps out in 2019; enhancement ratios are unaffected"],
         ["*3", "*Keep the flasks running, and start them at Bariri",
          "Without co-located flasks this analysis could make no absolute statement — and "
          "reached a wrong one in their absence"],
         ["*4", "*Put a ceilometer at Jambi and Kemayoran",
          "Layer depth is the single unmeasured quantity behind every flux here"]],
        ["Also: declare units in the files, re-examine Sorong before June 2023, and add "
         "δ¹³C-CH₄ or ethane at Kemayoran to split the non-combustion methane. · Report §15"],
        page(), widths=[0.05, 0.36, 0.59])

    slide_quote(
        prs, "IN ONE SENTENCE",
        "The measurements are good; what they needed was a second instrument.",
        ["Two of the four most consequential findings here are about the data rather than the "
         "atmosphere — a time base that was wrong, and a bias that was invisible until an "
         "independent record was brought alongside.",
         "Both were found by comparison, not by inspection. So was the retraction.",
         "The one place the record closes end to end — greenhouse growth to forcing to "
         "temperature — it agrees with the ocean to within the confidence intervals.",
         "The last of them is a negative result: this network cannot verify a national "
         "carbon target, and saying so is worth more than a claim it could.",
         "200 findings · 28 figures · 39 scripts · two documents and this deck, all "
         "regenerated from the raw files · figures in English and Bahasa Indonesia."],
        page())
    return prs


def main():
    lang = i18n.from_argv()
    i18n.set_lang(lang)
    prs = build(lang)
    if lang != "en" and i18n.MISSING:
        # The deck's prose is its own body of text, separate from the figure
        # labels, and is not translated.  Say so rather than shipping a file
        # that is silently half English.
        print(f"  WARNING: {len(i18n.MISSING)} deck strings have no {lang} translation; "
              f"they will appear in English.  Add them to i18n.TABLES before "
              f"distributing this file.")
    out = ROOT / "outputs" / f"GHG_Analysis_Slides{i18n.suffix()}.pptx"
    prs.save(str(out))
    print(f"wrote {out.relative_to(ROOT)}  ({len(prs.slides.__iter__.__self__._sldIdLst)} slides, "
          f"{out.stat().st_size/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
