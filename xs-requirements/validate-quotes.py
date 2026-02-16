#!/usr/bin/env python3
"""Validate quote/line-number accuracy in findings YAML files.

Usage:
    uv run --with pyyaml python3 xs-requirements/validate-quotes.py FINDINGS_YAML SOURCE_FILE

For each (line, quote) pair in threads and findings:
  - Extracts a distinctive phrase from the quote
  - Searches the source file for that phrase using rg
  - Compares claimed line with actual occurrences

Exit code = number of errors (0 = all pass).
"""

import os
import subprocess
import sys
import re

import yaml


def extract_phrase(quote, min_len=20, max_len=60):
    """Extract a distinctive search phrase from a quote.

    Picks the first min_len..max_len chars, trimmed to a word boundary.
    Falls back to the whole quote if it's short.
    """
    if not quote or not isinstance(quote, str):
        return None
    quote = quote.strip()
    if len(quote) <= min_len:
        return quote if len(quote) >= 8 else None
    # Take up to max_len chars, trim to last word boundary
    segment = quote[:max_len]
    # Trim to last space to avoid partial words
    last_space = segment.rfind(' ', min_len)
    if last_space > min_len:
        segment = segment[:last_space]
    return segment.strip()


def find_in_source(phrase, source_file):
    """Use rg -nF to find fixed-string matches in source file.

    Returns list of matching line numbers.
    """
    try:
        result = subprocess.run(
            ['rg', '-nF', phrase, source_file],
            capture_output=True, text=True, timeout=10
        )
        lines = []
        for line in result.stdout.strip().split('\n'):
            if line and ':' in line:
                match = re.match(r'^(\d+):', line)
                if match:
                    lines.append(int(match.group(1)))
        return lines
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def extract_primary_range(findings_path):
    """Extract primary range from filename.

    Filenames like 06a0-L201-400.yaml or day-021-L9601-10400.yaml
    encode the primary range as L{start}-{end}.
    """
    basename = os.path.basename(findings_path)
    match = re.search(r'L(\d+)-(\d+)\.yaml$', basename)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None


def validate_findings(findings_path, source_file):
    """Validate all (line, quote) pairs in a findings YAML file."""
    with open(findings_path) as f:
        data = yaml.safe_load(f)

    if not data:
        print(f"WARN: Empty YAML file: {findings_path}")
        return 0

    # Extract primary range from filename for range enforcement
    range_start, range_end = extract_primary_range(findings_path)
    if range_start and range_end:
        print(f"Primary range: [{range_start}, {range_end}]")

    # Collect all (line, quote, location) triples
    pairs = []

    # From threads
    for thread in data.get('threads', []) or []:
        tid = thread.get('id', '?')
        for event in thread.get('events', []) or []:
            line = event.get('line')
            quote = event.get('quote')
            if line and quote:
                pairs.append((line, quote, f"thread {tid}"))

    # From findings
    for finding in data.get('findings', []) or []:
        fid = finding.get('id', '?')
        line = finding.get('line')
        quote = finding.get('quote')
        if line and quote:
            pairs.append((line, quote, f"finding {fid}"))

    if not pairs:
        print(f"OK: No (line, quote) pairs to validate in {findings_path}")
        return 0

    errors = 0
    checked = 0
    skipped = 0
    range_errors = 0

    for claimed_line, quote, location in pairs:
        # Check range first
        if range_start and range_end:
            if claimed_line < range_start or claimed_line > range_end:
                print(f"  RANGE {location} L{claimed_line}: outside primary [{range_start}, {range_end}]")
                range_errors += 1
                errors += 1
                continue
        phrase = extract_phrase(quote)
        if not phrase:
            skipped += 1
            continue

        checked += 1
        actual_lines = find_in_source(phrase, source_file)

        if not actual_lines:
            # Try shorter phrase
            short_phrase = extract_phrase(quote, min_len=10, max_len=30)
            if short_phrase and short_phrase != phrase:
                actual_lines = find_in_source(short_phrase, source_file)

        if not actual_lines:
            print(f"  MISSING {location} L{claimed_line}: phrase not found in source")
            print(f"    phrase: {phrase[:60]}...")
            errors += 1
        elif claimed_line in actual_lines:
            print(f"  OK {location} L{claimed_line}")
        else:
            # Check if claimed line is close (within 5 lines of an actual match)
            close = [l for l in actual_lines if abs(l - claimed_line) <= 5]
            if close:
                print(f"  CLOSE {location} L{claimed_line}: found at {close} (within 5 lines)")
            else:
                print(f"  WRONG {location} L{claimed_line}: found at {actual_lines}")
                errors += 1

    range_msg = f", {range_errors} range violations" if range_errors else ""
    print(f"\nSummary: {checked} checked, {errors} errors{range_msg}, {skipped} skipped (short quotes)")
    return errors


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} FINDINGS_YAML SOURCE_FILE")
        sys.exit(1)

    findings_path = sys.argv[1]
    source_file = sys.argv[2]

    print(f"Validating {findings_path} against {source_file}")
    print()

    errors = validate_findings(findings_path, source_file)
    sys.exit(min(errors, 125))  # Cap at 125 per convention


if __name__ == '__main__':
    main()
