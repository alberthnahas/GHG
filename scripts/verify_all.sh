#!/usr/bin/env bash
# Every gate this project must pass before work is called done.
#
# Run from the project root:   bash scripts/verify_all.sh
# Add --fast to skip the two slow gates (LaTeX and the deck rendering).
#
# Exit 0 means all gates passed.  Any other exit means at least one failed and
# the work is not finished, whatever the prose says.
set -uo pipefail
cd "$(dirname "$0")/.."

FAST=0
[[ "${1:-}" == "--fast" ]] && FAST=1

PASS=0
FAIL=0
FAILED_GATES=()

gate() {
    local name="$1"; shift
    printf '\n\033[1m== %s\033[0m\n' "$name"
    if "$@"; then
        printf '   \033[32mPASS\033[0m  %s\n' "$name"
        PASS=$((PASS + 1))
    else
        printf '   \033[31mFAIL\033[0m  %s\n' "$name"
        FAIL=$((FAIL + 1))
        FAILED_GATES+=("$name")
    fi
}

# ---------------------------------------------------------------- gate 1 ----
# Document structure: findings contiguous, figures present in both languages,
# cross-references resolve, prose counts match reality.
gate "documents are internally consistent" \
     python3 scripts/check_docs.py --quiet

# ---------------------------------------------------------------- gate 2 ----
# Every string drawn on a figure has a Bahasa Indonesia translation.
# The audit re-renders every figure module, so it also catches import errors.
i18n_gate() {
    local out
    out="$(python3 scripts/i18n.py --audit 2>&1)" || { echo "$out"; return 1; }
    if [[ "$out" == *"0 untranslated strings"* ]]; then
        echo "   0 untranslated strings"
        return 0
    fi
    sed -n '/untranslated strings/,$p' <<<"$out"
    return 1
}
gate "figure translations complete" i18n_gate

# ---------------------------------------------------------------- gate 3 ----
# Both PDFs compile with no overfull boxes.  Slow (~1 min).
latex_gate() {
    "${GHG_SCIENTIFIC_PYTHON:-python3}" -m unittest tests.test_pdf_layout tests.test_bkt_methane_inverse tests.test_bkt_inversion_operator || return 1
    python3 scripts/a14_latex.py >/dev/null || return 1
    local n
    n="$(grep -c Overfull outputs/latex/*.log | awk -F: '{s+=$2} END {print s+0}')"
    echo "   overfull boxes: $n"
    [[ "$n" -eq 0 ]] || return 1
    # Overfull boxes catch text in the margin.  They do not catch a table header
    # printed with no rows under it, which is valid LaTeX and only visible in the
    # geometry of the finished page.  That one is measured on the rendering.
    local out
    out="$("${GHG_SCIENTIFIC_PYTHON:-python3}" scripts/check_pdf.py 2>&1)" || { echo "$out"; return 1; }
    echo "   0 stray table headers"
    if [[ -f outputs/hysplit/gfs/analysis/report_values.json ]]; then
        for doc in BKT_Forward_Source_Influence_Report BKT_Methane_Inversion_Report BKT_Transport_Technical_Companion; do
            "${GHG_SCIENTIFIC_PYTHON:-python3}" scripts/check_pdf.py "outputs/$doc.pdf" >/dev/null || return 1
        done
        "${GHG_SCIENTIFIC_PYTHON:-python3}" scripts/validate_bkt_gfs_report.py >/dev/null || return 1
        echo "   forward, inversion and transport-companion report checks passed"
        if [[ -f outputs/hysplit/domain_budget_extension/tables/full_receptor_budget.csv ]]; then
            "${GHG_SCIENTIFIC_PYTHON:-python3}" -m unittest tests.test_bkt_domain_budget_extension >/dev/null || return 1
            "${GHG_SCIENTIFIC_PYTHON:-python3}" scripts/validate_domain_budget_extension.py >/dev/null || return 1
            echo "   domain-correction and prior-budget extension checks passed"
        fi
        if [[ -f outputs/hysplit/two_receptor/tables/inversion_parameters.csv ]]; then
            "${GHG_SCIENTIFIC_PYTHON:-python3}" scripts/check_pdf.py outputs/BKT_JMB_Two_Receptor_Report.pdf >/dev/null || return 1
            "${GHG_SCIENTIFIC_PYTHON:-python3}" -m unittest tests.test_bkt_two_receptor >/dev/null || return 1
            "${GHG_SCIENTIFIC_PYTHON:-python3}" scripts/validate_bkt_jmb_report.py >/dev/null || return 1
            echo "   two-receptor report checks passed"
        fi
        if [[ -f outputs/hysplit/two_receptor/tables/co2_experiments_round6_skill.csv ]]; then
            "${GHG_SCIENTIFIC_PYTHON:-python3}" scripts/check_pdf.py outputs/BKT_JMB_CO2_Report.pdf >/dev/null || return 1
            "${GHG_SCIENTIFIC_PYTHON:-python3}" -m unittest tests.test_bkt_jmb_co2 tests.test_bkt_jmb_co2_improved tests.test_bkt_jmb_co2_experiments tests.test_bkt_jmb_co2_report >/dev/null || return 1
            "${GHG_SCIENTIFIC_PYTHON:-python3}" scripts/validate_bkt_jmb_co2_report.py >/dev/null || return 1
            echo "   carbon dioxide report checks passed"
        fi
    elif [[ -f outputs/hysplit/refinement/analysis/metrics.json ]]; then
        python3 scripts/validate_bkt_footprint_report.py --refinement >/dev/null || return 1
        echo "   revised BKT report and independent numerical checks passed"
    fi
}
[[ $FAST -eq 1 ]] || gate "PDFs compile clean and lay out correctly" latex_gate

# ---------------------------------------------------------------- gate 4 ----
# Both decks render through LibreOffice with no text outside the frame, no text
# over an image, no colliding blocks.  Slow (~2 min).  This measures the ACTUAL
# rendering; the geometric estimate has missed real problems before.
slides_gate() {
    local ok=0 out
    for deck in outputs/GHG_Analysis_Slides.pptx Jambi/Jambi_Presentation.pptx \
                outputs/BKT_Tower_Sequencer_Slides_id.pptx; do
        [[ -f "$deck" ]] || continue
        # capture first, then match: piping into `grep -q` under `pipefail`
        # makes grep close the pipe early and SIGPIPE the checker, which the
        # shell then reports as a failed pipeline even when the gate passed.
        out="$("${GHG_SCIENTIFIC_PYTHON:-python3}" scripts/check_slides.py "$deck" 2>&1)"
        if [[ "$out" == *"0 layout issues"* ]]; then
            echo "   ok   $deck  ($(grep -o '[0-9]* slides' <<<"$out" | head -1))"
        else
            echo "   FAIL $deck"
            grep -E '^  p[0-9]+:' <<<"$out" | head -10
            ok=1
        fi
    done
    return $ok
}
[[ $FAST -eq 1 ]] || gate "decks render with zero layout issues" slides_gate

# ---------------------------------------------------------------- summary ---
printf '\n\033[1m---------------------------------------------\033[0m\n'
printf '%d gate(s) passed, %d failed\n' "$PASS" "$FAIL"
if [[ $FAIL -gt 0 ]]; then
    printf '\033[31mfailed:\033[0m %s\n' "${FAILED_GATES[*]}"
    printf 'The work is NOT done.  Fix these before reporting completion.\n'
    exit 1
fi
[[ $FAST -eq 1 ]] && printf '(--fast: LaTeX and deck gates were skipped)\n'
printf 'All gates passed.\n'
printf '\nStill unchecked by any tool: whether the numbers in the prose match\n'
printf 'the CSVs they came from.  Verify those by hand -- it is the weakest\n'
printf 'link in this project and nothing automates it.\n'
