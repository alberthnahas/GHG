"""Layout check for the deck.

Two modes, and the first is much better than the second:

**Rendered** — if LibreOffice is available the deck is converted to PDF and the
*actual* rendering is measured: text outside the frame, text on top of an image,
and colliding text blocks.  This is ground truth and it catches things an
estimate cannot, such as a caption drifting away from its figure.

**Estimated** — if not, each text box's wrapped height is estimated from font
metrics and compared with the space allotted to it, and every pair of boxes is
tested for overlap on both axes.  Useful, but it knows nothing about how the
text actually lands on the slide.

LibreOffice is not on PATH in this environment; it lives at
``/opt/libreoffice26.2/program/soffice``.  The search below covers that and the
usual locations, so do not conclude it is missing because ``which soffice``
comes back empty - that mistake was made once already.

Usage:  check_slides.py outputs/GHG_Analysis_Slides.pptx [--estimate]
"""
import glob
import itertools
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SLIDE_W_IN, SLIDE_H_IN = 13.333, 7.5
MARGIN_IN = 0.62
EMU = 914400.0
FONT_CANDIDATES = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                   "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"]


def find_soffice():
    for c in ("soffice", "libreoffice"):
        p = shutil.which(c)
        if p:
            return p
    for pat in ("/opt/libreoffice*/program/soffice",
                "/usr/lib/libreoffice/program/soffice",
                "/snap/bin/libreoffice"):
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    return None


# ---------------------------------------------------------------------------
VENV_PYTHONS = [Path.home() / "Playground/.venv/bin/python",
                Path.home() / ".venv/bin/python"]


def _reexec_with_fitz():
    """PyMuPDF may live only in a virtualenv.  Re-run there rather than fail."""
    for py in VENV_PYTHONS:
        if not py.exists():
            continue
        ok = subprocess.run([str(py), "-c", "import fitz"], capture_output=True)
        if ok.returncode == 0:
            print(f"  (PyMuPDF is not in this interpreter; re-running under {py})")
            r = subprocess.run([str(py), __file__] + sys.argv[1:])
            sys.exit(r.returncode)
    return False


def check_rendered(pptx, soffice):
    try:
        import fitz
    except ModuleNotFoundError:
        _reexec_with_fitz()
        print("  PyMuPDF unavailable; falling back to the estimate")
        return check_estimated(pptx)
    with tempfile.TemporaryDirectory() as td:
        r = subprocess.run([soffice, "--headless", "--norestore", "--convert-to", "pdf",
                            "--outdir", td, str(pptx)],
                           capture_output=True, text=True, timeout=900)
        pdf = Path(td) / (Path(pptx).stem + ".pdf")
        if not pdf.exists():
            print("  conversion failed:", r.stdout[-400:], r.stderr[-400:])
            return None
        doc = fitz.open(pdf)
        W, H = doc[0].rect.width, doc[0].rect.height
        mx = W * MARGIN_IN / SLIDE_W_IN
        issues = 0
        for i, page in enumerate(doc, 1):
            d = page.get_text("dict")
            blocks = [b for b in d["blocks"] if b["type"] == 0]
            images = [fitz.Rect(b["bbox"]) for b in d["blocks"] if b["type"] == 1]

            def txt(b, n=44):
                return "".join(s["text"] for l in b["lines"] for s in l["spans"])[:n]

            for b in blocks:
                x0, y0, x1, y1 = b["bbox"]
                if x1 > W - mx + 3 or x0 < mx - 3 or y1 > H - 6 or y0 < 6:
                    print(f"  p{i}: text outside the frame :: {txt(b)!r}")
                    issues += 1
            for b in blocks:
                rb = fitz.Rect(b["bbox"])
                for r_ in images:
                    if (rb & r_).get_area() > 0.25 * rb.get_area() and rb.get_area() > 50:
                        print(f"  p{i}: text over an image :: {txt(b)!r}")
                        issues += 1
            for a, b in itertools.combinations(blocks, 2):
                ra, rb = fitz.Rect(a["bbox"]), fitz.Rect(b["bbox"])
                small = min(ra.get_area(), rb.get_area())
                if small > 300 and (ra & rb).get_area() > 0.18 * small:
                    print(f"  p{i}: blocks collide :: {txt(a, 30)!r} / {txt(b, 30)!r}")
                    issues += 1
        n = doc.page_count
        doc.close()
        return n, issues


# ---------------------------------------------------------------------------
def check_estimated(pptx):
    from pptx import Presentation
    from PIL import ImageFont
    font_path = next((f for f in FONT_CANDIDATES if Path(f).exists()), None)
    if font_path is None:
        print("  no measurable font found; cannot estimate")
        return None

    def lines(text, pt, width_in):
        if not text.strip():
            return 0
        f = ImageFont.truetype(font_path, max(int(pt * 4), 8))
        avail = width_in * 72 * 4
        cur, n = 0, 1
        for w in text.split():
            ww = f.getlength(w + " ")
            if cur + ww > avail and cur > 0:
                n, cur = n + 1, ww
            else:
                cur += ww
        return n

    prs = Presentation(str(pptx))
    issues, count = 0, 0
    for i, slide in enumerate(prs.slides, 1):
        count = i
        boxes = []
        for sh in slide.shapes:
            if not sh.has_text_frame:
                continue
            x, y, w, h = (v / EMU for v in (sh.left, sh.top, sh.width, sh.height))
            need, last = 0.0, ""
            for p in sh.text_frame.paragraphs:
                t = "".join(r.text for r in p.runs)
                pt = max([r.font.size.pt for r in p.runs if r.font.size] or [18])
                need += lines(t, pt, w) * pt * 1.22 / 72
                need += (p.space_after.pt if p.space_after else 0) / 72
                last = t or last
            boxes.append((y, y + need, x, x + w, last[:42]))
            if need > h + 0.06:
                print(f'  p{i}: box needs {need:.2f}" but is {h:.2f}" :: {last[:48]!r}')
                issues += 1
        for a, b in itertools.combinations(boxes, 2):
            if (min(a[1], b[1]) - max(a[0], b[0]) > 0.05
                    and min(a[3], b[3]) - max(a[2], b[2]) > 0.05):
                print(f"  p{i}: overlap :: {a[4]!r} / {b[4]!r}")
                issues += 1
    return count, issues


def main():
    pptx = Path(sys.argv[1] if len(sys.argv) > 1
                else "outputs/GHG_Analysis_Slides.pptx")
    soffice = None if "--estimate" in sys.argv else find_soffice()
    if soffice:
        print(f"rendering with {soffice}")
        res = check_rendered(pptx, soffice)
        mode = "actual rendering"
    else:
        print("LibreOffice not found; falling back to a geometric estimate")
        res = check_estimated(pptx)
        mode = "estimate"
    if res:
        n, issues = res
        print(f"\n{n} slides, {issues} layout issues ({mode})")
        sys.exit(1 if issues else 0)
    sys.exit(2)


if __name__ == "__main__":
    main()
