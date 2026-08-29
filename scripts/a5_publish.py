"""Render a markdown report to a self-contained HTML page with embedded figures.

Usage:  a5_publish.py [markdown-file]   (defaults to the main report)
"""
import base64, html, re, mimetypes, sys
from pathlib import Path
import ghg_common as g

MD = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else g.ROOT / "GHG_Analysis_Report.md"
OUTF = g.ROOT / "outputs" / (MD.stem.lower().replace("ghg_analysis_", "ghg_") + ".html")
SRC = MD.read_text()
TITLES = {"GHG_Analysis_Report": "Five Stations, Three Gases",
          "GHG_Analysis_Methods": "Deriving the Numbers"}
TITLE = TITLES.get(MD.stem, MD.stem.replace("_", " "))

STA = {"BKT": "#2a78d6", "JMB": "#eb6834", "KMY": "#1baf7a",
       "PLU": "#4a3aa7", "SRG": "#e34948"}


def data_uri(rel):
    p = (g.ROOT / rel).resolve()
    mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"


# LaTeX delimiters are left intact in the markdown, which is the canonical form
# and renders properly in Obsidian, GitHub and any MathJax viewer.  For this
# self-contained HTML there is no maths engine available (an artifact's CSP
# blocks external scripts), so formulas are lightly de-marked-up and set in a
# distinct block instead of being dumped as raw TeX.
_TEX = [
    # order matters: multi-letter commands before the shorter ones they contain
    (r"\\pmod", "mod"),
    (r"\\begin\{cases\}|\\end\{cases\}", ""),
    (r"\\underbrace", ""), (r"\\\\", "  "), (r"\\ ", " "),
    (r"\\operatorname\{([^}]*)\}", r"\1"),
    (r"\\(?:text|texttt|mathrm|mathbf|boxed)\{([^}]*)\}", r"\1"),
    (r"\\bigg?|\\Bigg?", ""),
    (r"\\\{", "("), (r"\\\}", ")"),
    (r"\\binom\{([^}]*)\}\{([^}]*)\}", r"C(\1,\2)"),
    (r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"(\1)/(\2)"),
    (r"\\sqrt\{([^{}]*)\}", r"sqrt(\1)"),
    (r"\\equiv", "\u2261"), (r"\\in\b", "\u2208"), (r"\\to\b", "\u2192"),
    (r"\\bar\s*\{?([A-Za-z])\}?", r"mean(\1)"),
    (r"\\hat\s*\{?\\?([a-zA-Z]+)\}?", r"\1_hat"),
    (r"\\left|\\right|\\!|\\,|\\;|\\:", ""),
    (r"\\times", "\u00d7"), (r"\\approx", "\u2248"),
    (r"\\leq|\\le\b", "\u2264"), (r"\\geq|\\ge\b", "\u2265"),
    (r"\\pm", "\u00b1"), (r"\\cdot", "\u00b7"),
    (r"\\Delta", "\u0394"), (r"\\sigma", "\u03c3"), (r"\\tau", "\u03c4"),
    (r"\\alpha", "\u03b1"), (r"\\beta", "\u03b2"), (r"\\chi", "\u03c7"),
    (r"\\mu", "\u00b5"), (r"\\pi", "\u03c0"), (r"\\varepsilon", "\u03b5"),
    (r"\\Longrightarrow|\\Rightarrow", "\u21d2"), (r"\\sum", "\u03a3"),
    (r"\\qquad|\\quad", "   "), (r"\[2pt\]", ""),
    (r"\\%", "%"), (r"\\_", "_"),
    # anything still backslashed keeps its name: \sin -> sin, \max -> max, \ln -> ln
    (r"\\([a-zA-Z]+)", r"\1"),
    (r"[{}]", ""), (r"&", "   "),
]


def detex(x):
    for pat, rep in _TEX:
        x = re.sub(pat, rep, x)
    return re.sub(r"\s+", " ", x).strip()


def inline(t):
    t = re.sub(r"\$([^$\n]+)\$", lambda m: "\x00" + detex(m.group(1)) + "\x01", t)
    t = html.escape(t, quote=False)
    t = t.replace("\x00", '<span class="mi">').replace("\x01", "</span>")
    t = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", lambda m: "", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![*\w])\*([^*]+)\*(?!\*)", r"<em>\1</em>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
    # station codes become palette chips, tying the prose to the figures
    t = re.sub(r"\b(BKT|JMB|KMY|PLU|SRG)\b",
               lambda m: f'<span class="sta" style="--c:{STA[m.group(1)]}">{m.group(1)}</span>', t)
    return t


def render(md):
    out, i, lines = [], 0, md.split("\n")
    while i < len(lines):
        ln = lines[i]

        # PDF-only pagination directive; it must not appear as visible HTML.
        if ln.strip() == "<!-- pdf-pagebreak -->":
            i += 1
            continue

        if ln.strip().startswith("$$"):
            body, first = [], ln.strip()[2:]
            if first.endswith("$$") and first[:-2].strip():
                out.append('<div class="mb">' + html.escape(detex(first[:-2])) + "</div>")
                i += 1; continue
            if first.strip():
                body.append(first)
            i += 1
            while i < len(lines) and not lines[i].strip().endswith("$$"):
                body.append(lines[i]); i += 1
            if i < len(lines):
                tail = lines[i].strip()[:-2]
                if tail.strip():
                    body.append(tail)
                i += 1
            out.append('<div class="mb">' + html.escape(detex(" ".join(body))) + "</div>")
            continue

        if ln.startswith("```"):
            body = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                body.append(html.escape(lines[i], quote=False)); i += 1
            out.append("<pre><code>" + "\n".join(body) + "</code></pre>")
            i += 1; continue

        m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", ln.strip())
        if m:
            cap = ""
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and lines[j].startswith("**Figure"):
                cap = inline(lines[j]); i = j
            out.append(f'<figure><img src="{data_uri(m.group(2))}" alt="{html.escape(m.group(1))}">'
                       + (f"<figcaption>{cap}</figcaption>" if cap else "") + "</figure>")
            i += 1; continue

        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")]); i += 1
            head = rows[0]
            body = [r for r in rows[2:]] if len(rows) > 2 and set("-: ") >= set("".join(rows[1])) else rows[1:]
            t = ["<div class='tw'><table><thead><tr>"]
            t += [f"<th>{inline(c)}</th>" for c in head]
            t.append("</tr></thead><tbody>")
            for r in body:
                t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            t.append("</tbody></table></div>")
            out.append("".join(t)); continue

        m = re.match(r"^(#{1,4})\s+(.*)", ln)
        if m:
            lv = len(m.group(1))
            txt = m.group(2)
            sec = re.match(r"^(\d+(?:\.\d+)?|Appendix [A-Z])\.?\s+(.*)", txt)
            if sec and lv > 1:
                out.append(f'<h{lv}><span class="num">{html.escape(sec.group(1))}</span>'
                           f'{inline(sec.group(2))}</h{lv}>')
            else:
                out.append(f"<h{lv}>{inline(txt)}</h{lv}>")
            i += 1; continue

        if ln.startswith("> "):
            body = []
            while i < len(lines) and lines[i].startswith(">"):
                body.append(lines[i][2:] if lines[i].startswith("> ") else ""); i += 1
            out.append("<blockquote>" + inline(" ".join(body).strip()) + "</blockquote>")
            continue

        if re.match(r"^\s*(\d+\.|[-*])\s+", ln):
            ordered = bool(re.match(r"^\s*\d+\.", ln))
            items = []
            while i < len(lines) and re.match(r"^\s*(\d+\.|[-*])\s+", lines[i]):
                items.append(re.sub(r"^\s*(\d+\.|[-*])\s+", "", lines[i])); i += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>")
            continue

        if ln.strip() == "---":
            out.append("<hr>"); i += 1; continue

        if ln.strip():
            para = [ln]
            i += 1
            while i < len(lines) and lines[i].strip() and not re.match(
                    r"^(#|\||>|```|---|\s*(\d+\.|[-*])\s|!\[)", lines[i]):
                para.append(lines[i]); i += 1
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            continue
        i += 1
    return "\n".join(out)


body = render(SRC)

CSS = """
:root{
  color-scheme: light;
  --ground:#f6f8f5; --surface:#ffffff; --ink:#111813; --ink2:#4b5a51; --ink3:#78877e;
  --rule:#dde5df; --accent:#15654a; --accent-soft:#e4efe8; --flag:#a8442f;
  --shadow:0 1px 2px rgba(17,24,19,.06), 0 8px 24px rgba(17,24,19,.05);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    color-scheme: dark;
    --ground:#0e1310; --surface:#161d19; --ink:#eaf0ec; --ink2:#9daaa2; --ink3:#7a877f;
    --rule:#26302b; --accent:#57bd8d; --accent-soft:#17281f; --flag:#e08a72;
    --shadow:0 1px 2px rgba(0,0,0,.4), 0 10px 28px rgba(0,0,0,.35);
  }
}
:root[data-theme="dark"]{
  color-scheme: dark;
  --ground:#0e1310; --surface:#161d19; --ink:#eaf0ec; --ink2:#9daaa2; --ink3:#7a877f;
  --rule:#26302b; --accent:#57bd8d; --accent-soft:#17281f; --flag:#e08a72;
  --shadow:0 1px 2px rgba(0,0,0,.4), 0 10px 28px rgba(0,0,0,.35);
}

*{box-sizing:border-box}
body{
  background:var(--ground); color:var(--ink);
  font-family:"Segoe UI Variable Text","Segoe UI",Roboto,"Helvetica Neue",system-ui,sans-serif;
  font-size:16.5px; line-height:1.68; margin:0;
  -webkit-font-smoothing:antialiased;
}
.page{max-width:1120px; margin:0 auto; padding:0 28px 120px;
      display:flex; flex-direction:column; gap:0}
.page > *{max-width:68ch; width:100%; margin-inline:auto}
.page > figure, .page > .tw, .page > hr, .page > h1{max-width:1064px}

h1,h2,h3,h4{
  font-family:ui-serif,"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
  font-weight:600; line-height:1.2; text-wrap:balance; color:var(--ink);
}
h1{font-size:clamp(2.1rem,4.4vw,3.1rem); letter-spacing:-.018em; margin:76px 0 6px}
h2{font-size:1.62rem; margin:64px 0 10px; padding-top:22px; border-top:1px solid var(--rule)}
h3{font-size:1.16rem; margin:38px 0 6px}
h4{font-size:1rem; margin:26px 0 4px}
h2 .num,h3 .num{
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
  font-size:.62em; font-weight:500; color:var(--accent);
  letter-spacing:.04em; margin-right:.72em; vertical-align:.14em;
}
p{margin:0 0 1.05em}
h1 + p{font-size:1.12rem; color:var(--ink2); margin-top:14px}
h1 + p + p{font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.8rem;
           color:var(--ink3); letter-spacing:.02em; font-variant-numeric:tabular-nums}
a{color:var(--accent); text-underline-offset:.18em; text-decoration-thickness:.06em}
strong{font-weight:650; color:var(--ink)}
hr{border:0; border-top:1px solid var(--rule); margin:52px auto; width:100%}
ul,ol{margin:0 0 1.1em; padding-left:1.35em}
li{margin:.34em 0}
li::marker{color:var(--accent)}

code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.86em;
     background:var(--accent-soft); padding:.1em .34em; border-radius:3px}
pre{background:var(--surface); border:1px solid var(--rule); border-radius:8px;
    padding:16px 18px; overflow-x:auto; font-size:.82rem; line-height:1.6}
pre code{background:none; padding:0}

blockquote{
  margin:26px 0; padding:16px 20px; background:var(--surface);
  border:1px solid var(--rule); border-left:3px solid var(--flag);
  border-radius:0 8px 8px 0; color:var(--ink2); font-size:.94rem;
}
blockquote strong{color:var(--flag)}

.tw{overflow-x:auto; margin:26px auto 30px; -webkit-overflow-scrolling:touch}
table{border-collapse:collapse; width:100%; font-size:.855rem;
      font-variant-numeric:tabular-nums; background:var(--surface);
      border:1px solid var(--rule); border-radius:8px; overflow:hidden}
th,td{text-align:left; padding:9px 13px; border-bottom:1px solid var(--rule);
      vertical-align:top}
thead th{
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
  font-size:.68rem; font-weight:600; text-transform:uppercase; letter-spacing:.07em;
  color:var(--ink2); background:var(--accent-soft); white-space:nowrap;
}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover{background:var(--accent-soft)}
td strong{font-weight:650}

figure{margin:36px auto 30px; text-align:center}
figure img{max-width:100%; height:auto; border:1px solid var(--rule);
           border-radius:8px; background:#fff; box-shadow:var(--shadow)}
figcaption{margin:12px auto 0; max-width:76ch; font-size:.82rem; line-height:1.55;
           color:var(--ink2); text-align:left}

.sta{
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
  font-size:.78em; font-weight:600; letter-spacing:.03em;
  color:var(--c); border-bottom:2px solid var(--c); padding-bottom:.02em;
}
th .sta, td .sta{border-bottom-width:2px}

.mb{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.94em;
    text-align:center;margin:18px 0;padding:12px 14px;border-radius:8px;
    background:var(--code-bg,rgba(127,127,127,.09));overflow-x:auto;white-space:nowrap}
.mi{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.94em}

@media (max-width:720px){
  body{font-size:15.5px}
  .page{padding:0 18px 80px}
  h1{margin-top:48px}
}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
:focus-visible{outline:2px solid var(--accent); outline-offset:2px}
"""

OUTF.write_text(
    f"<title>{TITLE}</title>\n<style>{CSS}</style>\n"
    f'<div class="page">\n{body}\n</div>\n')
print("wrote", OUTF, f"{OUTF.stat().st_size/1e6:.2f} MB")
