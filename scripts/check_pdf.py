"""Layout checks on the rendered PDFs, measured on the actual pages.

`a14_latex.py` reports overfull boxes, which catches text running into the
margin.  It does not catch a table header printed with no rows under it: that is
perfectly valid LaTeX, produces no warning, and only exists in the geometry of
the finished page.

The check here is the one failure of that class this project has had, twice.  A
long table is set as a `longtable`, whose `\\endhead` prints a "(table
continued)" marker and a repeated header at the top of every page after the
first.  When the table's first chunk gets no rows - because the section heading
above it left just enough room for the heading and not for the header plus a row
- longtable opens the next page as a *continuation*, so the page begins with a
header row, no data, and only then the section title.  It happened to the
Summary of findings and to the methods appendix.

The rule this encodes: **a "(table continued)" header must be followed by a data
row, not by a heading.**  The fix when it fires is in `a14_latex.convert` - the
`\\needspace` reserved for a heading that is immediately followed by a table has
to cover the heading, the header and a row or two, not just the heading.

Requires PyMuPDF, which lives in ~/Playground/.venv; the script re-execs itself
there, the same way `check_slides.py` does.

Usage:  check_pdf.py [pdf ...]      (defaults to both documents)
Exit:   0 if every page is clean, 1 otherwise.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV = Path.home() / "Playground" / ".venv" / "bin" / "python"

try:
    import fitz                                   # noqa: F401
except ImportError:                               # pragma: no cover
    if VENV.exists() and os.environ.get("_GHG_REEXEC") != "1":
        os.environ["_GHG_REEXEC"] = "1"
        os.execv(str(VENV), [str(VENV), __file__] + sys.argv[1:])
    print("  PyMuPDF is not available and the venv was not found")
    sys.exit(1)

import fitz

MARKER = "(table continued)"
DEFAULT = ["outputs/GHG_Analysis_Report.pdf", "outputs/GHG_Analysis_Methods.pdf"]


def looks_like_heading(text):
    """A section title, as it appears in the body text of a rendered page.

    Headings in these documents are either 'N. Title', 'N.M Title', or one of
    the two unnumbered ones.  A data row never matches: its first cell is a
    finding number, a station code, or a phrase.
    """
    t = text.strip()
    if t.startswith(("Appendix ", "Summary of findings", "Part ")):
        return True
    head = t.split(" ", 1)[0]
    return (head.rstrip(".").replace(".", "").isdigit()
            and head.endswith((".", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0"))
            and " " in t and t[0].isdigit() and "." in head)


def check(path):
    doc = fitz.open(path)
    bad = []
    for i, page in enumerate(doc):
        blocks = [b[4].strip() for b in page.get_text("blocks") if b[4].strip()]
        # block 0 is the running head; the marker, when present, is block 1
        if len(blocks) < 4 or MARKER not in blocks[1]:
            continue
        # blocks[2] is the repeated header row; blocks[3] must be data
        if looks_like_heading(blocks[3]):
            bad.append((i + 1, blocks[3].splitlines()[0][:60]))
    return doc.page_count, bad


def main():
    args = sys.argv[1:] or DEFAULT
    problems = 0
    for a in args:
        p = ROOT / a if not Path(a).is_absolute() else Path(a)
        if not p.exists():
            print(f"  FAIL {a}: not built")
            problems += 1
            continue
        n, bad = check(p)
        if bad:
            problems += len(bad)
            for pg, what in bad:
                print(f"  p{pg}: continued-table header with no rows under it, "
                      f"above '{what}'")
            print(f"  FAIL {a}  ({n} pages, {len(bad)} stray table headers)")
        else:
            print(f"  ok   {a}  ({n} pages, 0 stray table headers)")
    print(f"\n{problems} PDF layout issues")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
