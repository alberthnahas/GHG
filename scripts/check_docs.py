"""Structural checks on the two markdown documents.

Nothing here reads the atmosphere.  These are the consistency checks that a
human reviewer would do last and always forgets: that the findings table has no
holes, that every figure referenced exists on disk, that every cross-reference
points at a heading that is really there, and that the counts quoted in the
prose ("57 findings, 22 figures") match what the document actually contains.

Every one of these has been wrong at least once in this project's history, and
each time it was found by eye rather than by a check.  This is the check.

Usage:  check_docs.py [--quiet]
Exit:   0 if everything passes, 1 otherwise.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "GHG_Analysis_Report.md"
METHODS = ROOT / "GHG_Analysis_Methods.md"
FIGDIR = ROOT / "figures"

problems = []
notes = []


def fail(msg):
    problems.append(msg)


def ok(msg):
    notes.append(msg)


# --------------------------------------------------------------------------
def findings_table(text):
    """The summary table at the top of the report: | **N** | ... | section |."""
    start = text.index("## Summary of findings")
    end = text.index("# Part I")
    rows = re.findall(r"^\|\s*\*\*(\d+)\*\*\s*\|.*\|\s*([^|]+?)\s*\|\s*$",
                      text[start:end], re.M)
    return {int(n): sec for n, sec in rows}


def headings(text):
    """Every numbered heading, as the string a cross-reference would use."""
    out = set()
    for line in text.splitlines():
        m = re.match(r"^#{2,3}\s+(\d+(?:\.\d+)?)[.\s]", line)
        if m:
            out.add(m.group(1))
        m = re.match(r"^#{2,3}\s+(\d+[a-z]+)\.", line)      # 15a, 16b
        if m:
            out.add(m.group(1))
        m = re.match(r"^##\s+Appendix\s+([A-Z])", line)
        if m:
            out.add(m.group(1))
    return out


def check_findings(report, methods):
    table = findings_table(report)
    if not table:
        return fail("the findings summary table is empty or unparseable")
    ids = sorted(table)
    holes = [i for i in range(1, max(ids) + 1) if i not in table]
    if holes:
        fail(f"findings table has holes: {holes}")
    else:
        ok(f"findings table is contiguous, 1-{max(ids)}")

    # the counts quoted in prose must match
    for label, pat, actual in (("findings", r"(\d+) findings", max(ids)),
                               ("All N findings", r"All (\d+) findings", max(ids))):
        for m in re.finditer(pat, report):
            claimed = int(m.group(1))
            if claimed != actual:
                fail(f"prose claims {claimed} {label} but the table has {actual} "
                     f"(...{report[max(0, m.start()-40):m.end()+20]!r})")

    # every finding must be derived somewhere in the methods cross-reference
    xref = set()
    for m in re.finditer(r"^\|\s*(\d+(?:[,–-]\s*\d+)*)\s*[—-]", methods, re.M):
        label = m.group(1)
        numbers = [int(n) for n in re.findall(r"\d+", label)]
        if ("–" in label or "-" in label) and "," not in label and len(numbers) == 2:
            xref.update(range(numbers[0], numbers[1] + 1))
        else:
            xref.update(numbers)
    missing = [i for i in ids if i not in xref]
    if missing:
        fail(f"findings with no entry in the methods cross-reference: {missing}")
    else:
        ok(f"all {len(ids)} findings appear in the methods cross-reference")

    # the section each finding claims must exist
    heads = headings(report)
    for n, sec in table.items():
        for ref in re.findall(r"\d+(?:\.\d+)?", sec):
            if ref not in heads:
                fail(f"finding {n} points at section {ref}, which has no heading")


def check_figures(report):
    refs = re.findall(r"figures/(f\d+_[a-z0-9_]+\.png)", report)
    if not refs:
        return fail("no figures referenced in the report")
    missing = sorted({r for r in refs if not (FIGDIR / r).exists()})
    if missing:
        fail(f"figures referenced but not on disk: {missing}")
    # the Indonesian companion should exist for every English figure
    no_id = sorted({r for r in refs
                    if not (FIGDIR / r.replace(".png", "_id.png")).exists()})
    if no_id:
        fail(f"figures with no Bahasa Indonesia version: {no_id}")
    nums = sorted({int(re.match(r"f(\d+)", r).group(1)) for r in refs})
    holes = [i for i in range(1, max(nums) + 1) if i not in nums]
    if holes:
        fail(f"figure numbers skip: {holes}")
    else:
        ok(f"figures f1-f{max(nums)} all referenced, on disk, in both languages")

    for m in re.finditer(r"(\d+) figures", report):
        if int(m.group(1)) != len(nums):
            fail(f"prose claims {m.group(1)} figures but {len(nums)} are referenced")


def check_tables(report, methods):
    """Every Markdown table has one caption, in reading order.

    Checking only the set of caption numbers once allowed 37 uncaptioned tables
    to pass: the numbered subset was contiguous even though the document was
    not.  Count table blocks first, then require the nearest preceding nonblank
    line to be their caption.
    """
    for label, text in (("report", report), ("methods", methods)):
        lines = text.splitlines()
        blocks = []
        for i in range(len(lines) - 1):
            if (lines[i].lstrip().startswith("|") and
                    re.match(r"^\s*\|?\s*:?-{3,}", lines[i + 1])):
                k = i - 1
                while k >= 0 and not lines[k].strip():
                    k -= 1
                caption = (re.match(r"^\*\*Table (\d+)\b", lines[k])
                           if k >= 0 else None)
                blocks.append((i + 1, int(caption.group(1)) if caption else None))

        unnumbered = [line for line, number in blocks if number is None]
        if unnumbered:
            fail(f"{label} has unnumbered tables beginning on lines {unnumbered}")
            continue

        nums = [number for _, number in blocks]
        expected = list(range(1, len(blocks) + 1))
        if nums != expected:
            fail(f"{label} table captions are not in reading order: {nums}")
        else:
            ok(f"all {len(blocks)} {label} tables are numbered 1-{len(blocks)} in reading order")


def check_crossrefs(report, methods):
    """Every 'Section N.M' in the report and '§N' in the methods must resolve."""
    rheads, mheads = headings(report), headings(methods)
    bad = set()
    for m in re.finditer(r"Section (\d+(?:\.\d+)?)", report):
        if m.group(1) not in rheads:
            bad.add(m.group(1))
    if bad:
        fail(f"report cross-references to sections that do not exist: {sorted(bad)}")
    else:
        ok("every 'Section N' reference in the report resolves")

    bad = set()
    for m in re.finditer(r"§(\d+[a-z]*(?:\.\d+)?)", methods):
        ref = m.group(1)
        if ref not in mheads and ref.split(".")[0] not in mheads:
            bad.add(ref)
    if bad:
        fail(f"methods cross-references to sections that do not exist: {sorted(bad)}")
    else:
        ok("every '§N' reference in the methods resolves")

    bad = set()
    for m in re.finditer(r"Report §(\d+[a-z]*(?:\.\d+)?)", methods):
        ref = m.group(1)
        if ref not in rheads and ref.split(".")[0] not in rheads:
            bad.add(ref)
    if bad:
        fail(f"methods points at report sections that do not exist: {sorted(bad)}")


def check_sourced_tables(report):
    """A table that cites a CSV must contain that CSV's numbers.

    Written after an audit found six tables whose caption said
    "(from `outputs/x.csv`)" while their absolute values had been altered -
    differences and p-values preserved, levels shifted by a constant.  The
    differences looked right, so nothing caught it by eye.

    Rounding is allowed: a cell matches if some number in the CSV agrees to the
    precision the cell is written to.  Only cells that match nothing are
    reported.
    """
    import csv as _csv
    bad_tables = 0
    # Stop the body at the next table caption OR the next heading: a section
    # whose table carries no caption would otherwise be swallowed into the
    # previous table's block and reported as a mismatch.
    for m in re.finditer(r"\*\*Table (\d+)[^\n]*?\(from `outputs/([\w.]+)`\)(.*?)(?=\n\*\*Table |\n#{2,4} |\Z)",
                         report, re.S):
        tno, fn, body = m.group(1), m.group(2), m.group(3)
        path = ROOT / "outputs" / fn
        if not path.exists():
            fail(f"Table {tno} cites {fn}, which does not exist")
            continue
        cnums = set(re.findall(r"-?\d+\.?\d*", path.read_text()))
        cvals = []
        for c in cnums:
            try:
                cvals.append(float(c))
            except ValueError:
                pass
        # Columns that are computed from the CSV rather than copied out of it -
        # percentage shares, "% of total" - legitimately contain numbers the
        # file does not.  Drop those cells before comparing.
        lines = [l for l in body.splitlines() if l.startswith("|")]
        drop = set()
        if lines:
            hdr = [c.strip().lower() for c in lines[0].strip("|").split("|")]
            drop = {i for i, h in enumerate(hdr)
                    if "share" in h or "%" in h or "of total" in h or "of net" in h}
        kept = []
        for l in lines:
            cells = l.strip("|").split("|")
            kept.append("|".join(c for i, c in enumerate(cells) if i not in drop))
        rows = "\n".join(kept)
        # "(+90.0 % of total)" inside a cell is derived, not copied
        rows = re.sub(r"\([^()]*%[^()]*\)", "", rows)
        miss = []
        for n in set(re.findall(r"(?<![\w.])-?\d+\.\d+(?![\w])", rows)):
            v = float(n)
            dp = len(n.split(".")[1])
            # +1e-9 so an exact half-rounding (0.0315 -> 0.032) is not
            # failed by floating-point representation
            tol = 0.5 * 10 ** (-dp) + 1e-9
            if not any(abs(c - v) <= tol or abs(abs(c) - abs(v)) <= tol for c in cvals):
                miss.append(n)
        if miss:
            bad_tables += 1
            fail(f"Table {tno} cites {fn} but these values are not in it: "
                 f"{sorted(miss)[:8]}{' ...' if len(miss) > 8 else ''}")
    if not bad_tables:
        ok("every table citing a CSV matches it")


def check_scripts(report):
    """Every script named in the appendix must exist."""
    named = set(re.findall(r"\b(a\d+_[a-z0-9_]+|check_slides|check_docs|i18n|"
                           r"ghg_common|noaa_flask)\.py", report))
    missing = sorted(s + ".py" for s in named
                     if not (ROOT / "scripts" / f"{s}.py").exists())
    if missing:
        fail(f"scripts named in the report but absent from scripts/: {missing}")
    else:
        ok(f"all {len(named)} scripts named in the report exist")


def main():
    report, methods = REPORT.read_text(), METHODS.read_text()
    check_findings(report, methods)
    check_figures(report)
    check_tables(report, methods)
    check_crossrefs(report, methods)
    check_sourced_tables(report)
    check_scripts(report)

    quiet = "--quiet" in sys.argv
    if not quiet:
        for n in notes:
            print(f"  ok   {n}")
    for p in problems:
        print(f"  FAIL {p}")
    print(f"\n{len(problems)} document problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
