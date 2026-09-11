"""Markdown -> LaTeX -> PDF for the project report documents.

There is no pandoc here, and pandoc's generic output would need heavy tuning
anyway: these documents are dominated by wide multi-panel figures and by tables
that range from four narrow numeric columns to a twenty-row summary whose middle
column is a paragraph.  A converter that knows about exactly this markdown
subset can lay both out properly, which is what this module does.

The three things it does that a generic converter would not:

* **Column widths are computed from the content.**  Each table is measured, its
  columns classified as numeric or prose, and the prose columns given
  proportional ``p{}`` widths that fill the text block exactly.  Numeric columns
  are right-aligned and take their natural width.
* **Every table is a longtable** with a repeated header, so nothing overflows a
  page, and the font size steps down as the column count rises.
* **Unicode is mapped to LaTeX**, not to a fallback font.  The 36 non-ASCII
  characters these documents use become real LaTeX constructs, so subscripted
  formulae and units are typeset rather than approximated.

Usage:  a14_latex.py [markdown-file ...]      (defaults to both documents)
        a14_latex.py --tex-only               (write .tex, skip compilation)
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "outputs" / "latex"
TEXBIN = Path.home() / ".TinyTeX" / "bin" / "x86_64-linux"

DOCS = {
    "GHG_Analysis_Report": dict(
        title="Greenhouse gases at five Indonesian monitoring stations",
        subtitle="Hourly CO\\textsubscript{2} / CH\\textsubscript{4} / CO records from Bukit "
                 "Kototabang, Jambi, Kemayoran, Bariri (Lore Lindu) and Sorong, "
                 "validated against the NOAA GML flask record",
        toc=True),
    "GHG_Analysis_Methods": dict(
        title="How every number in the report is calculated",
        subtitle="Formulas, the reasoning behind each choice, and four headline "
                 "results worked end to end",
        toc=True),
    "Indonesian_GHG_Scientific_Assessment_2026": dict(
        title="Greenhouse gases at five Indonesian monitoring stations",
        subtitle="Hourly CO\\textsubscript{2} / CH\\textsubscript{4} / CO records from Bukit "
                 "Kototabang, Jambi, Kemayoran, Bariri (Lore Lindu) and Sorong, "
                 "validated against the NOAA GML flask record",
        toc=True),
    "BKT_Tower_Sequencer_Specification": dict(
        title="Valve sequencer specification for the Bukit Kototabang 100-m tower",
        subtitle="Scheduling three inlet levels on one Picarro G2401, with the "
                 "sampling design fixed against the station's own 30-m record",
        toc=True),
    "Indonesian_GHG_Scientific_Methods_2026": dict(
        title="How every number in the report is calculated",
        subtitle="Formulas, the reasoning behind each choice, and four headline "
                 "results worked end to end",
        toc=True),
    "BKT_HYSPLIT_STILT_Footprint_Report": dict(
        title="Greenhouse-gas source influence and methane emission inversion at Bukit Kototabang",
        running_title="BKT source influence and methane inversion",
        prefer_vector=True,
        figure_placement="htbp",
        flow_barriers=True,
        measured_tables=True,
        title_meta="Bukit Kototabang, Indonesia | September–October 2019",
        title_no_hyphenation=True,
        subtitle="GFS-driven source influence and an observation-constrained regional methane experiment",
        title_footer=("September–October 2019 research experiments. Conditional source estimates, "
                      "not independently verified regional emission totals."),
        toc=True),
}

# --------------------------------------------------------------------------
# Unicode.  Every non-ASCII character these documents use, mapped to a LaTeX
# construct rather than delegated to a fallback font, so that subscripts and
# units are typeset instead of approximated.
UNI = {
    "†": r"\textdagger{}", "⚠": r"\textdagger{}",
    "\u2082": r"\textsubscript{2}", "\u2084": r"\textsubscript{4}",
    "\u2086": r"\textsubscript{6}", "\u2080": r"\textsubscript{0}",
    "\u2081": r"\textsubscript{1}",
    "\u00b9": r"\textsuperscript{1}", "\u00b2": r"\textsuperscript{2}",
    "\u00b3": r"\textsuperscript{3}", "\u2074": r"\textsuperscript{4}",
    "\u2070": r"\textsuperscript{0}", "\u2076": r"\textsuperscript{6}",
    "\u2077": r"\textsuperscript{7}",
    "\u207b": r"\textsuperscript{\textminus}",
    "\u2014": "---", "\u2013": "--", "\u2026": r"\ldots{}",
    # text glyphs, not math ones, wherever the main font has them: a math \pm
    # inside a bold run stays upright and light, which reads as a mismatch
    "\u2212": r"\textminus{}", "\u00b1": r"\textpm{}", "\u00d7": r"\texttimes{}",
    "\u00b7": r"\textperiodcentered{}", "\u2248": r"$\approx$",
    "\u2265": r"$\geq$", "\u2264": r"$\leq$", "\u2273": r"$\gtrsim$",
    "\u221a": r"$\surd$",
    "\u2192": r"\textrightarrow{}", "\u00b0": r"\textdegree{}",
    "\u00b5": r"\textmu{}", "\u00a7": r"\S{}", "\u00f1": r"\~{n}",
    "\u0394": r"$\Delta$", "\u03b4": r"$\delta$", "\u03c3": r"$\sigma$",
    "\u03c4": r"$\tau$", "\u03c1": r"$\rho$",
    "\u2713": r"\checkmark{}", "\u2717": r"$\times$",
    "\u26a0": r"\textbf{!}", "\u0304": "",
}

SPECIALS = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
            "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
            # in these documents a tilde always means "approximately"
            "~": r"$\sim$", "^": r"\textasciicircum{}"}

NUMERIC = re.compile(r"^[\s\d.,+\-\u2212()\[\]%/\u00b1<>=\u2264\u2265~]*$")


ESCAPED_PIPE = "\x00PIPE\x00"


def split_row(line):
    """Split a markdown table row on unescaped pipes.

    A cell may legitimately contain a pipe written as ``\\|`` - "Median \\|diff\\|"
    is one - and splitting on every ``|`` turns a 9-column table into a
    12-column one with mangled headers.  Hide the escaped pipes, split, then put
    them back as a literal bar.
    """
    line = line.strip().replace("\\|", ESCAPED_PIPE)
    cells = line.strip("|").split("|")
    return [c.strip().replace(ESCAPED_PIPE, "|") for c in cells]


def esc(s):
    """Escape LaTeX specials, then map Unicode.  Math and code are protected by
    the caller before this runs."""
    # straight double quotes become proper typographic pairs; TU encoding would
    # otherwise render both ends as a closing quote
    s = re.sub(r'"([^"]*)"', r"``\1''", s)
    out = "".join(SPECIALS.get(c, c) for c in s)
    for u, rep in UNI.items():
        out = out.replace(u, rep)
    return out


# --------------------------------------------------------------------------
def inline(s):
    """Inline markdown -> LaTeX, protecting math and code from escaping."""
    slots = []

    def stash(tex):
        slots.append(tex)
        return f"\x00{len(slots)-1}\x01"

    # math passes through verbatim - it is already LaTeX
    s = re.sub(r"\$([^$\n]+)\$", lambda m: stash(f"${m.group(1)}$"), s)
    s = re.sub(r"`([^`]+)`", lambda m: stash(r"\texttt{" + _verb(m.group(1)) + "}"), s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
               lambda m: stash(r"\href{" + m.group(2).replace("%", r"\%") + "}{"
                               + inline(m.group(1)) + "}"), s)
    # the source carries two bits of raw HTML for subscripts
    s = re.sub(r"<sub>(.*?)</sub>", lambda m: stash(r"\textsubscript{"
                                                   + esc(m.group(1)) + "}"), s)
    s = re.sub(r"<sup>(.*?)</sup>", lambda m: stash(r"\textsuperscript{"
                                                   + esc(m.group(1)) + "}"), s)
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", s)
    # single-asterisk emphasis: bold is already consumed, so any remaining pair
    # is emphasis - including the mid-word form in "d*C*/d*t*", which a
    # word-boundary lookbehind would miss
    s = re.sub(r"\*([^*\n]+)\*", r"\\emph{\1}", s)
    return re.sub(r"\x00(\d+)\x01", lambda m: slots[int(m.group(1))], s)


def heading(txt):
    """A heading that is safe in a PDF bookmark.

    Bookmarks are plain Unicode strings, so a heading containing maths (which
    unicode-math turns into math-mode-only commands) has to declare a text
    fallback.  The fallback is the original markdown with its markup stripped,
    which reads better in the bookmark pane than a de-TeX-ed approximation.
    """
    tex = inline(txt)
    if "$" in tex or "\\text" in tex:
        return r"\texorpdfstring{" + tex + "}{" + _strip_markup(txt) + "}"
    return tex


def _verb(s, breakable=True):
    """Escape for \\texttt{}, where underscores and braces still bite.

    Long identifiers like ``GHG_Analysis_Methods.md`` are single unbreakable
    words to TeX and will run into the margin, so zero-width break points are
    offered after the characters an identifier is naturally read as segmented
    by.  ``\\allowbreak`` adds no hyphen, which is what a path or a file name
    wants.
    """
    out = "".join(r"\textasciitilde{}" if c == "~" else SPECIALS.get(c, c) for c in s)
    for u, rep in UNI.items():
        out = out.replace(u, rep)
    if breakable:
        out = re.sub(r"(\\_|[./-])", r"\1\\allowbreak{}", out)
        # Integrity hashes must remain exact but may wrap without a hyphen.
        if re.fullmatch(r"[0-9a-fA-F]{32,}", s):
            out = r"\allowbreak{}".join(s[i:i+8] for i in range(0, len(s), 8))
    return out


# --------------------------------------------------------------------------
def _strip_markup(cell):
    """Cell text with markup removed, for width measurement only."""
    t = re.sub(r"\*\*|\*|`", "", cell)
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    return t.strip()


def table(rows, caption=None):
    """Lay out one markdown table as a longtable that always fits the text block.

    Every column is given an explicit fraction of ``\textwidth``, so the total
    width is fixed by construction rather than left to TeX's natural sizing -
    which is what stops the wider tables from running into the margin.  The
    fractions are proportional to the longest cell each column must hold, with a
    floor so that a five-character numeric column beside a sixty-character prose
    column still gets room for its header.

    Numeric columns are set ragged-left (right-aligned) and prose columns
    ragged-right; the font size steps down as the column count rises.
    """
    head, body = rows[0], rows[1:]
    ncol = len(head)
    plain = [[_strip_markup(c) for c in r] for r in rows]

    numeric, longest = [], []
    for j in range(ncol):
        col = [r[j] for r in plain[1:] if j < len(r)]
        numeric.append(bool(col) and all(NUMERIC.match(c or "0") for c in col))
        # header length counts, but a long header over a numeric column wraps
        # happily, so it is discounted
        body_max = max([len(c) for c in col] or [1])
        head_len = len(plain[0][j]) * (0.45 if numeric[j] else 1.0)
        longest.append(max(body_max, head_len, 1))

    size = r"\small"
    if ncol >= 5:
        size = r"\footnotesize"
    if ncol >= 8:
        size = r"\scriptsize"

    # A column can never be narrower than its longest unbreakable word, or that
    # word sticks out into the margin.  Capacity is measured in characters at
    # the chosen size: the text block is ~468 pt and an average glyph is about
    # 0.47 em, so 111 characters at \\footnotesize, scaled for the others.
    cap = {r"\small": 100.0, r"\footnotesize": 111.0, r"\scriptsize": 126.0}[size]
    longest_word = []
    for j in range(ncol):
        head_words = re.split(r"\s+", plain[0][j] if j < len(plain[0]) else "")
        body_words = [wd for r in plain[1:]
                      for wd in re.split(r"\s+", r[j] if j < len(r) else "")]
        # A short cell is treated as one unbreakable token, so values that read
        # as a unit - "0.20 degS", "+2.28 ppm" - are not split across lines.
        col_cells = [plain[0][j] if j < len(plain[0]) else ""] + \
                    [r[j] for r in plain[1:] if j < len(r)]
        atomic = max((len(c) for c in col_cells), default=1) <= 12
        if atomic:
            longest_word.append(max([len(c) * (1.08 if k == 0 else 1.0)
                                     for k, c in enumerate(col_cells)] + [1.0]))
        else:
            # header cells are set bold, which costs about 8 % more width
            longest_word.append(max([len(wd) * 1.08 for wd in head_words]
                                    + [float(len(wd)) for wd in body_words] + [1.0]))

    # leave room for the inter-column padding: 2*tabcolsep per column
    tabcolsep_pt, textwidth_pt = 4.0, 468.0
    avail = 1.0 - (2 * tabcolsep_pt * ncol) / textwidth_pt

    # Floors first, then share out what is left.  Doing it the other way round -
    # normalising and then imposing floors - lets the normalisation undo the
    # floors, which is how "Coverage" ended up in the margin on the first pass.
    floors = [(lw + 1.5) / cap for lw in longest_word]
    if sum(floors) >= avail:                 # genuinely too wide: scale together
        frac = [f / sum(floors) * avail for f in floors]
    else:
        w = [min(x, 55.0) for x in longest]  # a long prose column cannot starve the rest
        tot_w = sum(w) or 1.0
        spare = avail - sum(floors)
        frac = [floors[j] + spare * w[j] / tot_w for j in range(ncol)]

    spec = []
    for j in range(ncol):
        al = r"\raggedleft" if numeric[j] else r"\raggedright"
        spec.append(f">{{{al}\\arraybackslash}}p{{{frac[j]:.4f}\\textwidth}}")

    def row(cells, bold=False):
        cs = [inline(c) for c in cells] + [""] * (ncol - len(cells))
        if bold:
            cs = [r"\textbf{" + c + "}" if c.strip() else "" for c in cs]
        return " & ".join(cs[:ncol]) + r" \\"

    # How tall will it be?  A cell needs one line per (its length / its column's
    # character capacity), and the row is as tall as its tallest cell.
    lines = 3
    for r in plain[1:]:
        lines += max([max(1, -(-len(r[j]) // max(int(frac[j] * cap), 4)))
                      for j in range(ncol) if j < len(r)] or [1])

    setup = [r"\begingroup" + size,
             r"\setlength{\tabcolsep}{" + f"{tabcolsep_pt:.0f}" + r"pt}",
             r"\renewcommand{\arraystretch}{1.25}"]

    if caption is not None:
        # These report tables fit a page. Measure the actual caption + tabular
        # as one box instead of estimating wrapped row heights or letting a
        # longtable output routine move a caption behind a continuation head.
        # Fail explicitly if a future table needs a genuine multipage design.
        return [r"\par\FloatBarrier",
                r"\begin{lrbox}{\reporttablebox}\begin{minipage}{\textwidth}",
                inline(caption) + r"\par\vspace{6pt}"] + setup + [
                r"\noindent\begin{tabular}{" + "".join(spec) + "}",
                r"\toprule", row(head, bold=True), r"\midrule"] + [
                row(r) for r in body] + [
                r"\bottomrule\end{tabular}\par\endgroup",
                r"\end{minipage}\end{lrbox}",
                r"\ifdim\dimexpr\ht\reporttablebox+\dp\reporttablebox\relax>\textheight",
                r"\PackageError{report-layout}{Table exceeds one page}{Use a captioned multipage table.}\fi",
                r"\Needspace{\dimexpr\ht\reporttablebox+\dp\reporttablebox+12pt\relax}",
                r"\noindent\usebox{\reporttablebox}\par\vspace{8pt}", ""]

    # Height in points, not in body baselineskips: a table row is set at the
    # table's own font size with \arraystretch applied, so reserving body lines
    # under-books the space and the table runs off the bottom of the page.
    rowpt = {r"\small": 10.0, r"\footnotesize": 9.0, r"\scriptsize": 8.0}[size] * 1.2 * 1.25
    needed_pt = lines * rowpt + 16.0        # + toprule/midrule/bottomrule padding

    # Only genuinely short tables are made unbreakable.  A larger one has to be a
    # longtable: \needspace measures the page before the output routine places
    # any pending figure, so on a page that is about to receive two floats the
    # reservation is not honoured and the table would run off the bottom.  A
    # longtable simply breaks, which is always safe.
    if needed_pt <= 180.0:
        # Short enough for one page: a plain tabular that cannot be split, with
        # \needspace to move the whole thing to the next page rather than let it
        # straddle a boundary.  This is what keeps every table intact and stops
        # longtable emitting a continuation header with no rows under it.
        return setup + [
            r"\par\needspace{" + f"{needed_pt:.0f}" + r"pt}",
            r"\vspace{4pt}\noindent\begin{tabular}{" + "".join(spec) + "}",
            r"\toprule", row(head, bold=True), r"\midrule"] + \
            [row(r) for r in body] + \
            [r"\bottomrule", r"\end{tabular}\par\vspace{8pt}", r"\endgroup", ""]

    # Genuinely longer than a page: longtable, with no rule at the page breaks
    # (an \endfoot rule plus the \endlastfoot rule prints a doubled line
    # whenever the break lands after the final row).
    #
    # The bottom rule is part of the *body*, attached to the last row with
    # \\* rather than set in \endlastfoot.  In \endlastfoot it is a separate
    # chunk, and when the body fills a page exactly that chunk lands alone on
    # the next one - where longtable dutifully prints the "(table continued)"
    # head above it, giving a header row with no rows under it.  \\* forbids
    # the break at that point, so the rule cannot be orphaned.  \endlastfoot is
    # omitted for the same reason: an empty last foot is still a chunk, and a
    # body that fills its last page exactly leaves that chunk to open a new one.
    body_rows = [row(r) for r in body]
    if body_rows:
        body_rows[-1] += "*"                 # \\ -> \\*
    return setup + [
        r"\setlength{\LTpre}{10pt}\setlength{\LTpost}{12pt}",
        r"\begin{longtable}{" + "".join(spec) + "}",
        r"\toprule", row(head, bold=True), r"\midrule\endfirsthead",
        r"\multicolumn{" + str(ncol) + r"}{@{}l@{}}{\footnotesize\itshape\color{muted}"
        r"(table continued)}\\[2pt]",
        r"\toprule", row(head, bold=True), r"\midrule\endhead",
        r"\endfoot"] + \
        body_rows + \
        [r"\bottomrule", r"\end{longtable}", r"\endgroup", ""]


# --------------------------------------------------------------------------
HEAD_RE = re.compile(r"^(#{1,4})\s+(.*)")
IMG_RE = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$")


def convert(md, cfg):
    lines = md.split("\n")
    out, i, first_h1 = [], 0, True
    skip_title_needspace = False

    while i < len(lines):
        ln = lines[i]

        # ---- explicit PDF page break -------------------------------------
        # Used sparingly where a following heading-plus-table reservation
        # would otherwise force mdframed to split the preceding caveat box.
        if ln.strip() == "<!-- pdf-pagebreak -->":
            out += [r"\clearpage", ""]
            i += 1
            continue

        # ---- display math -------------------------------------------------
        if ln.strip().startswith("$$"):
            body, first = [], ln.strip()[2:]
            if first.endswith("$$") and first[:-2].strip():
                out += [r"\begin{equation*}", first[:-2].strip(), r"\end{equation*}", ""]
                i += 1
                continue
            if first.strip():
                body.append(first)
            i += 1
            while i < len(lines) and not lines[i].strip().endswith("$$"):
                body.append(lines[i])
                i += 1
            if i < len(lines):
                tail = lines[i].strip()[:-2]
                if tail.strip():
                    body.append(tail)
                i += 1
            src = "\n".join(body).strip()
            env = "align*" if r"\\" in src and "&" in src else "equation*"
            out += [f"\\begin{{{env}}}", src, f"\\end{{{env}}}", ""]
            continue

        # ---- figure, with the caption that follows it ---------------------
        m = IMG_RE.match(ln.strip())
        if m:
            path = (ROOT / m.group(2)).resolve()
            if cfg.get("prefer_vector") and path.suffix==".png" and path.with_suffix(".pdf").exists():
                path=path.with_suffix(".pdf")
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            cap = ""
            if j < len(lines) and lines[j].startswith("**Figure"):
                cap = lines[j]
                i = j
            body = re.sub(r"^\*\*(Figure\s+\d+\.)\*\*\s*", "", cap)
            num = re.match(r"^\*\*(Figure\s+\d+)\.\*\*", cap)
            label = (num.group(1) if num else "Figure").replace(" ", "")
            out += [r"\begin{figure}["+cfg.get("figure_placement","tbp")+"]", r"\centering",
                    r"\includegraphics[width=\textwidth]{" + str(path) + "}",
                    r"\caption*{\small\textbf{" + (num.group(1) + "." if num else "") + "} "
                    + inline(body) + "}",
                    r"\label{fig:" + label + "}",
                    r"\end{figure}", ""]
            i += 1
            continue

        # ---- table --------------------------------------------------------
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            if len(rows) > 1 and set("-: ") >= set("".join(rows[1])):
                rows = [rows[0]] + rows[2:]
            out += table(rows)
            continue

        # ---- fenced code --------------------------------------------------
        if ln.startswith("```"):
            body = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                body.append(lines[i])
                i += 1
            i += 1
            # Verbatim, so the column alignment these blocks rely on survives -
            # they are laid out as two-column tables of script name against
            # description, which any escaping-and-reflowing approach destroys.
            out += [r"\begin{Verbatim}[fontsize=\scriptsize,frame=leftline,"
                    r"framerule=1.2pt,rulecolor=\color{bkt},xleftmargin=12pt,"
                    r"framesep=8pt,samepage=false]"]
            out += body
            out += [r"\end{Verbatim}", ""]
            continue

        # ---- headings -----------------------------------------------------
        m = HEAD_RE.match(ln)
        if m:
            lvl, txt = len(m.group(1)), m.group(2).strip()
            if lvl == 1 and first_h1:
                first_h1 = False
                i += 1
                continue
            if lvl == 1:                       # "Part I --- ..." divider
                out += [r"\FloatBarrier", r"\parttitle{" + heading(txt) + "}", ""]
            else:
                cmd = {2: "section", 3: "subsection", 4: "subsubsection"}[lvl]
                # a heading must not be the last thing on a page
                # If a table title follows immediately, reserve for the heading
                # *and* the title here.  \needspace issues its own page break,
                # so a reservation made after the heading would strand it.
                # If the very next thing is a table title, reserve for the
                # heading and the title together.  Looking further ahead was
                # tried and made the document worse: an intervening figure
                # floats away, so the space reserved for it is simply lost.
                # A heading followed directly by a table body, with no caption
                # line between them, needs the same treatment: if only a few
                # lines are left on the page the heading fits but the table's
                # first chunk does not, and a longtable whose first chunk is
                # empty prints its *continuation* head - "(table continued)"
                # above the section title, with no rows under it.  That is what
                # happened to the Summary of findings on page 7.
                follows_table, follows_bare_table, follows_heading, k, seen = False, False, False, i + 1, 0
                while k < len(lines) and seen < 1:
                    t = lines[k].strip()
                    k += 1
                    if not t:
                        continue
                    seen += 1
                    if t.startswith("**Table"):
                        follows_table = True
                        break
                    if t.startswith("|"):
                        follows_bare_table = True
                        break
                    if t.startswith("#"):
                        follows_heading = True
                        break
                skip_title_needspace = follows_table
                # 28, not 14: the reservation has to cover the heading, its
                # space above and below, the table head *and* a row or two.
                # At 14 the heading fits and the head does not, and longtable
                # then opens the next page with a "(table continued)" head
                # sitting above the section title with no rows under it.
                reserve = "28" if (follows_table or follows_bare_table) else "5"
                if cfg.get("flow_barriers") and (follows_table or follows_bare_table):reserve="16"
                previous=next((line.strip() for line in reversed(lines[:i]) if line.strip()),"")
                parent=HEAD_RE.match(previous)
                adjacent_child=bool(cfg.get("flow_barriers") and parent and len(parent.group(1))<lvl)
                if cfg.get("flow_barriers") and follows_heading:reserve="10"
                # A second reservation/barrier between adjacent headings can
                # strand the parent. Reserve the pair before the parent only.
                out += [r"\FloatBarrier" if not adjacent_child and (lvl == 2 or cfg.get("flow_barriers")) else "",
                        r"\needspace{" + reserve + r"\baselineskip}" if not adjacent_child else "",
                        "\\" + cmd + "{" + heading(txt) + "}",
                        r"\nopagebreak[4]", ""]
                # The running head takes the section title, and these titles
                # carry a long "--- Findings 16 to 19, 26, 39, ..." tail that
                # collides with the document title on the left.  Mark the head
                # with the part before the dash only.
                if lvl == 2:
                    short = txt.split("—")[0].split(" - ")[0].strip()
                    out.insert(len(out) - 1,
                               r"\markboth{" + heading(short) + "}{}")
            i += 1
            continue

        # ---- blockquote (the caveat boxes) --------------------------------
        if ln.startswith(">"):
            body = []
            while i < len(lines) and lines[i].startswith(">"):
                body.append(lines[i][2:] if lines[i].startswith("> ") else "")
                i += 1
            out += [r"\begin{caveat}", inline(" ".join(body).strip()),
                    r"\end{caveat}", ""]
            continue

        # ---- lists --------------------------------------------------------
        if re.match(r"^\s*(\d+\.|[-*])\s+", ln):
            ordered = bool(re.match(r"^\s*\d+\.", ln))
            first_number=int(re.match(r"^\s*(\d+)\.",ln).group(1)) if ordered else None
            items = []
            while i < len(lines) and re.match(r"^\s*(\d+\.|[-*])\s+", lines[i]):
                items.append(re.sub(r"^\s*(\d+\.|[-*])\s+", "", lines[i]))
                i += 1
            env = "enumerate" if ordered else "itemize"
            start=f",start={first_number}" if ordered and first_number!=1 else ""
            out += [f"\\begin{{{env}}}[leftmargin=1.4em,itemsep=2pt,topsep=4pt{start}]"]
            out += [r"\item " + inline(x) for x in items]
            out += [f"\\end{{{env}}}", ""]
            continue

        if ln.strip() == "---":
            i += 1
            continue

        # ---- paragraph ----------------------------------------------------
        if ln.strip():
            para = [ln]
            i += 1
            while i < len(lines) and lines[i].strip() and not re.match(
                    r"^(#|\||>|```|---|\s*(\d+\.|[-*])\s|!\[|\$\$)", lines[i]):
                para.append(lines[i])
                i += 1
            text = " ".join(para)
            if cfg.get("measured_tables") and re.match(r"^\*\*Table\s", text):
                j = i
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines) and lines[j].startswith("|"):
                    rows = []
                    while j < len(lines) and lines[j].startswith("|"):
                        rows.append(split_row(lines[j]))
                        j += 1
                    if len(rows) > 1 and set("-: ") >= set("".join(rows[1])):
                        rows = [rows[0]] + rows[2:]
                    out += table(rows, caption=text)
                    i = j
                    skip_title_needspace = False
                    continue
            # A "Table N --- ..." line titles the table that follows it, so keep
            # it with at least the header and the first rows.
            if re.match(r"^\*\*Table\s", text) and not skip_title_needspace:
                # enough for the title plus a header and several rows, so the
                # title never ends up alone at the foot of a page
                if cfg.get("flow_barriers"):out.append(r"\FloatBarrier")
                out.append(r"\needspace{12\baselineskip}" if cfg.get("flow_barriers") else r"\needspace{14\baselineskip}")
            skip_title_needspace = False
            out += [inline(text), ""]
            continue

        i += 1

    return "\n".join(out)


# --------------------------------------------------------------------------
PREAMBLE = r"""\documentclass[11pt,a4paper]{article}

\usepackage{geometry}
\geometry{a4paper,top=24mm,bottom=24mm,left=22mm,right=22mm,
          headheight=21pt,headsep=10mm,footskip=12mm}

\usepackage{fontspec}
% TeX Gyre ships with TinyTeX but is not registered with fontconfig, so the
% faces are loaded by filename rather than by family name.
\setmainfont{texgyrepagella}[
  Extension = .otf, Path = TGPATH,
  UprightFont = *-regular, BoldFont = *-bold,
  ItalicFont = *-italic, BoldItalicFont = *-bolditalic]
\setsansfont{texgyreheros}[
  Extension = .otf, Path = TGPATH, Scale = 0.92,
  UprightFont = *-regular, BoldFont = *-bold,
  ItalicFont = *-italic, BoldItalicFont = *-bolditalic]
\setmonofont{DejaVu Sans Mono}[Scale=0.80]

\usepackage{amsmath,amssymb}
\usepackage{unicode-math}
\setmathfont{texgyrepagella-math.otf}[Path = TGMATH]

\usepackage{graphicx}
\usepackage{longtable,array,booktabs}
\newsavebox{\reporttablebox}
\usepackage{caption}
\usepackage{enumitem}
\usepackage{microtype}
\usepackage{ragged2e}
\usepackage{placeins}
\usepackage{needspace}
\usepackage[dvipsnames,table]{xcolor}
\usepackage{mdframed}
\usepackage{fancyvrb}
\usepackage{titlesec}
\usepackage{fancyhdr}
\usepackage[hidelinks]{hyperref}

% ---- palette, matching the figures -------------------------------------
\definecolor{bkt}{HTML}{2A78D6}
\definecolor{ink}{HTML}{1B1F24}
\definecolor{muted}{HTML}{5B6470}
\definecolor{rule}{HTML}{C9CFD6}
\definecolor{boxbg}{HTML}{F4F6F8}

\hypersetup{colorlinks=true,linkcolor=bkt,urlcolor=bkt,citecolor=bkt,
            bookmarksnumbered=true,pdfstartview=FitH}

% ---- typography ---------------------------------------------------------
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.62\baselineskip}
\linespread{1.06}
\raggedbottom
\widowpenalty=10000
\clubpenalty=10000
\emergencystretch=1.5em
\hyphenpenalty=200
\tolerance=1200
\color{ink}

% keep floats near their text
\renewcommand{\topfraction}{0.92}
\renewcommand{\bottomfraction}{0.72}
\renewcommand{\textfraction}{0.06}
\renewcommand{\floatpagefraction}{0.75}
\setlength{\intextsep}{16pt plus 4pt minus 4pt}
\setlength{\textfloatsep}{18pt plus 4pt minus 4pt}

\captionsetup{font=small,labelfont=bf,justification=justified,
              singlelinecheck=false,skip=7pt}

\titleformat{\section}{\sffamily\large\bfseries\color{ink}}{\thesection}{0.6em}{}
\titleformat{\subsection}{\sffamily\normalsize\bfseries\color{ink}}{\thesubsection}{0.6em}{}
\titleformat{\subsubsection}{\sffamily\small\bfseries\color{muted}}{}{0em}{}
\titlespacing*{\section}{0pt}{20pt plus 4pt}{7pt}
\titlespacing*{\subsection}{0pt}{15pt plus 3pt}{5pt}

% section numbers come from the markdown text itself, so suppress LaTeX's
\setcounter{secnumdepth}{0}

% ---- part dividers ------------------------------------------------------
% A Part is a major structural break, so it opens a page.  This also flushes the
% float queue, which keeps each part's figures inside it.
\newcommand{\parttitle}[1]{%
  \clearpage%
  \phantomsection\addcontentsline{toc}{section}{\protect\textcolor{bkt}{#1}}%
  \vspace{2pt}%
  {\color{bkt}\rule{\textwidth}{1.1pt}}\par\vspace{5pt}%
  {\sffamily\Large\bfseries\color{bkt}#1\par}%
  \vspace{3pt}{\color{rule}\rule{\textwidth}{0.5pt}}\par\vspace{8pt}}

% ---- caveat boxes -------------------------------------------------------
\newmdenv[linewidth=0pt,leftline=true,linecolor=bkt,
          backgroundcolor=boxbg,innerleftmargin=10pt,innerrightmargin=10pt,
          innertopmargin=8pt,innerbottommargin=8pt,skipabove=10pt,
          skipbelow=10pt,rightline=false,topline=false,bottomline=false]{caveatbox}
\newenvironment{caveat}{\begin{caveatbox}\small}{\end{caveatbox}}

% ---- running heads ------------------------------------------------------
\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\headrule}{\hbox to\headwidth{\color{rule}\leaders\hrule height \headrulewidth\hfill}}
\fancyhead[L]{\sffamily\scriptsize\color{muted}\RUNTITLE}
\fancyhead[R]{\sffamily\scriptsize\color{muted}\nouppercase{\leftmark}}
\fancyfoot[C]{\sffamily\small\color{muted}\thepage}
\renewcommand{\sectionmark}[1]{\markboth{#1}{}}

\begin{document}
"""

TITLEPAGE = r"""
\begin{titlepage}
\vspace*{0.16\textheight}
{\color{bkt}\rule{\textwidth}{2pt}}\par\vspace{14pt}
{\sffamily\LARGE\bfseries\color{ink} DOCTITLE\par}
\vspace{12pt}
{\sffamily\large\color{muted} DOCSUB\par}
\vspace{10pt}{\color{rule}\rule{\textwidth}{0.6pt}}\par
\vspace{16pt}
{\sffamily\small\color{muted} DOCMETA\par}
\vfill
{\sffamily\footnotesize\color{muted}
DOCFOOT\par}
\end{titlepage}
"""


def build_tex(stem, cfg):
    md = (ROOT / f"{stem}.md").read_text(encoding="utf-8")

    # the metadata line is the first paragraph after the subtitle in the source
    meta = ""
    for ln in md.split("\n")[:12]:
        if ln.startswith("Analysis date:"):
            meta = ln.strip()
            break
    if not meta:
        meta = "Companion to the analysis report."
    meta=cfg.get("title_meta",meta)
    body = convert(md, cfg)

    default_footer = (r"Generated from \texttt{" + stem.replace("_", r"\_")
                      + r".md} by \texttt{scripts/a14\_latex.py}.\par "
                      r"Figures are reproducible in English and Bahasa Indonesia; see Appendix~A.")
    title_tex = (TITLEPAGE
                 .replace("DOCTITLE", esc(cfg["title"]) if "\\" not in cfg["title"] else cfg["title"])
                 .replace("DOCSUB", cfg["subtitle"])
                 .replace("DOCMETA", esc(meta))
                 .replace("DOCFOOT", cfg.get("title_footer", default_footer)))
    if cfg.get("title_no_hyphenation"):
        title_tex=title_tex.replace(r"\sffamily\LARGE\bfseries",r"\raggedright\hyphenpenalty=10000\exhyphenpenalty=10000\sffamily\LARGE\bfseries")

    tg = Path.home() / ".TinyTeX/texmf-dist/fonts/opentype/public/tex-gyre/"
    tgm = Path.home() / ".TinyTeX/texmf-dist/fonts/opentype/public/tex-gyre-math/"
    preamble = PREAMBLE.replace("\\begin{document}", "")
    if tg.is_dir() and tgm.is_dir():
        preamble = preamble.replace("TGPATH", str(tg) + "/").replace("TGMATH", str(tgm) + "/")
    else:
        # Tectonic resolves the same TeX Gyre faces from its managed bundle.
        preamble = (preamble.replace("Path = TGPATH, ", "")
                    .replace("Path = TGPATH,", "")
                    .replace("[Path = TGMATH]", ""))
    doc = [preamble,
           r"\newcommand{\RUNTITLE}{" + esc(cfg.get("running_title", cfg["title"])) + "}",
           (r"\hypersetup{pdftitle={" + esc(cfg["title"]) + "},pdfauthor={" +
            esc(cfg.get("pdf_author", "")) + "}}"),
           r"\begin{document}",
           title_tex]
    if cfg.get("toc"):
        doc += [r"\begingroup\setlength{\parskip}{2pt}",
                r"\hypersetup{linkcolor=ink}",
                r"\tableofcontents\endgroup", r"\clearpage"]
    doc += [body, r"\end{document}"]
    return "\n".join(doc)


def compile_pdf(texfile):
    env = dict(os.environ, PATH=f"{TEXBIN}:{os.environ['PATH']}")
    xelatex = TEXBIN / "xelatex"
    xelatex = str(xelatex) if xelatex.is_file() else shutil.which("xelatex", path=env["PATH"])
    if xelatex:
        commands = [[xelatex, "-interaction=nonstopmode", "-halt-on-error",
                     "-file-line-error", texfile.name]] * 3
    else:
        candidates = [
            os.environ.get("TECTONIC"),
            shutil.which("tectonic"),
            str(ROOT.parent / ".venv" / "bin" / "tectonic"),
        ]
        tectonic = next((value for value in candidates if value and Path(value).is_file()), None)
        if tectonic is None:
            return False, "Neither XeLaTeX nor Tectonic is available"
        env.setdefault("XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "ghg-tectonic-cache"))
        # Tectonic performs the required cross-reference reruns internally.
        commands = [[tectonic, "-X", "compile", texfile.name,
                     "--keep-logs", "--keep-intermediates"]]
    for command in commands:
        r = subprocess.run(
            command,
            cwd=texfile.parent, env=env, capture_output=True, text=True)
        if r.returncode != 0:
            log = (texfile.parent / (texfile.stem + ".log"))
            tail = ""
            if log.exists():
                lines = log.read_text(errors="replace").split("\n")
                bad = [k for k, l in enumerate(lines) if l.startswith("!")
                       or ".tex:" in l[:60]]
                tail = "\n".join(lines[max(0, bad[0] - 2):bad[0] + 18]) if bad \
                    else "\n".join(lines[-25:])
            return False, tail
    return True, ""


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    tex_only = "--tex-only" in sys.argv
    stems = args or list(DOCS)
    BUILD.mkdir(parents=True, exist_ok=True)
    failed = False

    for stem in stems:
        stem = Path(stem).stem
        cfg = DOCS.get(stem)
        if cfg is None:
            print(f"  no configuration for {stem}; skipping")
            continue
        tex = BUILD / f"{stem}.tex"
        tex.write_text(build_tex(stem, cfg), encoding="utf-8")
        print(f"wrote {tex.relative_to(ROOT)}  ({len(tex.read_text()):,} chars)")
        if tex_only:
            continue
        ok, err = compile_pdf(tex)
        if ok:
            pdf = tex.with_suffix(".pdf")
            dest = ROOT / "outputs" / pdf.name
            shutil.copy(pdf, dest)
            print(f"  -> {dest.relative_to(ROOT)}  ({dest.stat().st_size/1e6:.2f} MB)")
        else:
            print(f"  COMPILATION FAILED for {stem}:\n{err}")
            failed = True
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
