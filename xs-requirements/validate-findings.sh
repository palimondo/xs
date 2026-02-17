#!/bin/bash
# Validate findings YAML files for common issues
# Usage: ./xs-requirements/validate-findings.sh [file.yaml ...]
# If no args, validates all findings/*.yaml except progress.yaml

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

errors=0
warnings=0
files_checked=0

validate_file() {
    local f="$1"
    local basename=$(basename "$f")
    local file_errors=0

    # Skip progress.yaml and non-findings files
    if [[ "$basename" == "progress.yaml" ]] || [[ "$basename" == "crh-model-comparison.yaml" ]]; then
        return
    fi

    files_checked=$((files_checked + 1))

    # Extract expected range from filename
    # Format: prefix-Lstart-end.yaml or day-NNN-Lstart-end.yaml
    local range_start range_end
    if [[ "$basename" =~ L([0-9]+)-([0-9]+)\.yaml$ ]]; then
        range_start="${BASH_REMATCH[1]}"
        range_end="${BASH_REMATCH[2]}"
    else
        echo -e "${YELLOW}WARN${NC} $basename: Cannot extract range from filename, skipping range check"
        return
    fi

    # Check 1: All line numbers in range
    local line_numbers
    line_numbers=$(grep -E '^\s+line:\s+[0-9]+' "$f" 2>/dev/null | grep -oE '[0-9]+' || true)

    if [[ -n "$line_numbers" ]]; then
        while IFS= read -r ln; do
            if [[ "$ln" -lt "$range_start" ]] || [[ "$ln" -gt "$range_end" ]]; then
                echo -e "${RED}FAIL${NC} $basename: line $ln outside range [$range_start-$range_end]"
                file_errors=$((file_errors + 1))
            fi
        done <<< "$line_numbers"
    fi

    # Check 2: Speaker field present on all events and findings
    # Count events/findings lines (lines with "- line:" or "- id: F")
    local event_count finding_count speaker_count
    event_count=$(grep -cE '^\s*- line:\s+[0-9]+' "$f" 2>/dev/null) || event_count=0
    finding_count=$(grep -cE '^\s*- id: F[0-9]+' "$f" 2>/dev/null) || finding_count=0
    speaker_count=$(grep -cE '^\s*speaker:\s+(user|agent)' "$f" 2>/dev/null) || speaker_count=0

    local expected_speakers=$((event_count + finding_count))
    if [[ "$speaker_count" -lt "$expected_speakers" ]] && [[ "$expected_speakers" -gt 0 ]]; then
        echo -e "${YELLOW}WARN${NC} $basename: $speaker_count speaker fields for $expected_speakers events+findings"
        warnings=$((warnings + 1))
    fi

    # Check 3: Finding types — relaxed, contextual naming allowed
    # No enforcement; Opus will normalize during synthesis

    # Check 4: File is valid YAML (basic check - has source: field)
    if ! grep -qE '^source:' "$f" 2>/dev/null; then
        echo -e "${RED}FAIL${NC} $basename: missing 'source:' field — may not be valid findings YAML"
        file_errors=$((file_errors + 1))
    fi

    if [[ "$file_errors" -eq 0 ]]; then
        local finding_count_actual thread_count
        finding_count_actual=$(grep -cE '^\s*- id: F[0-9]+' "$f" 2>/dev/null) || finding_count_actual=0
        thread_count=$(grep -cE '^\s*- id: T[0-9]+' "$f" 2>/dev/null) || thread_count=0
        echo -e "${GREEN}OK${NC}   $basename: $finding_count_actual findings, $thread_count threads, range [$range_start-$range_end]"
    fi

    errors=$((errors + file_errors))
}

# Main
if [[ $# -gt 0 ]]; then
    for f in "$@"; do
        validate_file "$f"
    done
else
    for f in xs-requirements/findings/*.yaml; do
        validate_file "$f"
    done
fi

echo ""
echo "Files checked: $files_checked"
echo -e "Errors: $([ $errors -gt 0 ] && echo "${RED}$errors${NC}" || echo "${GREEN}$errors${NC}")"
echo -e "Warnings: $([ $warnings -gt 0 ] && echo "${YELLOW}$warnings${NC}" || echo "${GREEN}$warnings${NC}")"

exit $errors
