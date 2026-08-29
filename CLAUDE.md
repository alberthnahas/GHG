# CLAUDE.md

This project has a skill: **`ghg-analysis`**, at
`.claude/skills/ghg-analysis/SKILL.md`.

**Invoke it before doing anything substantial in this directory** — adding or
checking a finding, touching `scripts/`, editing either markdown document, or
regenerating the PDFs and decks. It carries data traps that are invisible in the
files themselves, and this project has published two wrong conclusions by not
knowing them.

The same content is written for every agent; `AGENTS.md` is the portable entry
point and points at the same files.

## The short version

- Markdown is canonical — never edit anything in `outputs/`.
- Never read `grk_hourly_*.json` directly; load through `ghg_common.load_station`.
  Timestamps are on two time bases and units differ per station.
- Every number in prose traces to a CSV in `outputs/` from a named script.
- Compute `n_eff` before quoting a *p*-value from a monthly series.
- `bash scripts/verify_all.sh` must pass — all four gates — before the work is
  done.
- LibreOffice is at `/opt/libreoffice26.2/program/soffice`, not on PATH.
- Not a git repository.
