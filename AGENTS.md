# AGENTS.md — Indonesian greenhouse-gas analysis

Instructions for any coding agent working in this directory (Codex,
Antigravity, Claude Code, or otherwise).

## Read this first

**The full operating manual is `.claude/skills/ghg-analysis/SKILL.md`.** It is
plain markdown and applies to every agent, not only Claude Code — the path is a
convention, not a restriction. Read it before doing anything substantial, then
load the reference files it points to as your task needs them:

| File | For |
|---|---|
| `.claude/skills/ghg-analysis/references/landmines.md` | **the data traps — read before writing any number** |
| `.claude/skills/ghg-analysis/references/pipeline.md` | scripts, run order, outputs |
| `.claude/skills/ghg-analysis/references/statistics.md` | trends, intervals, significance |
| `.claude/skills/ghg-analysis/references/conventions.md` | prose, figures, tables, slides |
| `.claude/skills/ghg-analysis/references/adding-a-finding.md` | the end-to-end checklist |
| `.claude/skills/ghg-analysis/references/verification.md` | what a failing gate means |

`summary.md` is the human-facing project handoff — read it if you are starting
cold.

## What this project is

242,411 station-hours of CO₂/CH₄/CO from five Indonesian GAW stations (Bukit
Kototabang, Jambi, Kemayoran, Bariri, Sorong), validated against 22 years of
NOAA GML flask samples. Products: a 57-finding report and a methods document
(markdown → LaTeX PDF → HTML), two PowerPoint decks, and figures in English and
Bahasa Indonesia. Everything is generated from the raw files by `scripts/`.

## The rules that matter most

For maps of Indonesia, always use the established shared GeoJSON asset:
`../.assets/indonesia_38prov.geojson` (provinces), or
`../.assets/indonesia_kabkota_38prov.geojson` when municipality detail is needed.
Do not substitute Natural Earth geometry for Indonesia. Record the selected
asset checksum and any in-memory validity repair; do not modify the original
shared assets. Natural Earth may supply neighboring-country context.

1. **Markdown is canonical.** Never edit anything in `outputs/` — PDFs, HTML,
   `.tex`, `.pptx` are all build products.
2. **Never read `grk_hourly_*.json` directly.** Load via
   `ghg_common.load_station` or `outputs/all.pkl`. The archive's timestamps are
   on two different time bases and its units differ per station; both are fixed
   in the loader and nowhere else.
3. **Every number in prose must trace to a CSV in `outputs/`** produced by a
   named script.
4. **A differential network cannot make an absolute claim** without a co-located
   traceable measurement. Breaking this rule produced a published retraction.
5. **Before quoting a *p*-value from a monthly series, compute the effective
   sample size.** `n_eff = n(1-r1r2)/(1+r1r2)`. One set of intervals in this
   report was 4× too narrow for want of it.
6. **Report what happened.** Null results stay in. Corrections are published,
   not quietly removed.

## Before you say the work is done

```bash
bash scripts/verify_all.sh
```

Four gates — document consistency, figure translations, PDF compilation, deck
rendering. **All must pass.** Reporting completion with a failing gate is the
worst failure mode in this project.

No gate checks whether the numbers in the prose still match the CSVs. Do that
by hand.

## Environment

- `python3` (3.14) has numpy, pandas, scipy, matplotlib, python-pptx, Pillow.
- **PyMuPDF is only in `~/Playground/.venv`.** `check_slides.py` re-execs itself
  there automatically.
- **LibreOffice is at `/opt/libreoffice26.2/program/soffice` and is NOT on
  PATH.** `which soffice` returns nothing — it is still installed.
- LaTeX is TinyTeX at `~/.TinyTeX`; `a14_latex.py` finds it.
- **This is not a git repository.** Nothing is version controlled. Be sure you
  can undo an edit before making it.

## Keep this up to date

The skill is meant to grow. If you lose time to something the files did not tell
you, or make a mistake worth not repeating, add it to `landmines.md` and note
the change in the SKILL.md changelog. If a problem could have been caught
mechanically, add the check to `scripts/check_docs.py` instead of writing a
paragraph about it.
