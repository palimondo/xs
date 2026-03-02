#!/usr/bin/env python3
"""Remove priority: metadata from all xs-requirements artifacts.

Strips:
- `priority: must|should|could` lines from story YAML files
- `priority: must|should|could` lines from pass6 analysis and group files
- `priority: must|should|could` lines from epic-report files
- `must:|should:|could:` lines from epic story_counts: sections
- `stories_by_priority:` blocks from epic-report files
- `by_priority:` blocks (+ indented children) from tracker and analysis summary
- Priority references from synthesis-summary.md
"""

import re
import os
from pathlib import Path

BASE = Path(__file__).parent
STORIES_DIR = BASE / "stories"
EPICS_DIR = BASE / "epics"
SYNTHESIS_DIR = BASE / "synthesis"
TRACKER = BASE / "tracker.yaml"

stats = {}

def count(category, n=1):
    stats[category] = stats.get(category, 0) + n


def strip_priority_line(lines):
    """Remove lines matching `^priority: ...` (with any indentation)."""
    removed = 0
    result = []
    for line in lines:
        if re.match(r'^(\s*)priority:\s+(must|should|could)\s*$', line):
            removed += 1
        else:
            result.append(line)
    return result, removed


def strip_stories():
    """Remove `priority:` lines from all story YAML files."""
    total = 0
    for yaml_file in sorted(STORIES_DIR.rglob("*.yaml")):
        lines = yaml_file.read_text().splitlines(keepends=True)
        result, removed = strip_priority_line(lines)
        if removed:
            yaml_file.write_text("".join(result))
            total += removed
    count("stories", total)
    print(f"  Stories: removed {total} priority lines from {STORIES_DIR}")


def strip_epics():
    """Remove must:/should:/could: from story_counts: sections in epic files."""
    total_lines = 0
    files_changed = 0
    for yaml_file in sorted(EPICS_DIR.glob("*.yaml")):
        lines = yaml_file.read_text().splitlines(keepends=True)
        result = []
        in_story_counts = False
        removed = 0
        for line in lines:
            stripped = line.strip()
            # Detect story_counts: section
            if stripped == "story_counts:":
                in_story_counts = True
                result.append(line)
                continue
            # If in story_counts, remove must:/should:/could: lines
            if in_story_counts:
                if re.match(r'^\s+(must|should|could):\s+\d+', line):
                    removed += 1
                    continue
                # Any non-indented line or different key exits the section
                if stripped and not line.startswith("  "):
                    in_story_counts = False
            result.append(line)
        if removed:
            yaml_file.write_text("".join(result))
            total_lines += removed
            files_changed += 1
    count("epics", total_lines)
    print(f"  Epics: removed {total_lines} lines from {files_changed} files")


def strip_pass6_files():
    """Remove priority: lines and by_priority: blocks from pass6 analysis files."""
    total = 0
    files = list(SYNTHESIS_DIR.glob("pass6-*.yaml"))
    for yaml_file in sorted(files):
        text = yaml_file.read_text()
        lines = text.splitlines(keepends=True)
        result = []
        skip_block = False
        block_indent = 0
        removed = 0
        for line in lines:
            # Check for by_priority: block start
            m = re.match(r'^(\s*)by_priority:\s*$', line)
            if m:
                skip_block = True
                block_indent = len(m.group(1))
                removed += 1
                continue
            # Skip indented children of by_priority:
            if skip_block:
                if line.strip() == '' or (len(line) > block_indent + 1 and line[block_indent + 1] == ' ' and line[:block_indent + 1].strip() == ''):
                    # Check if it's a child (more indented)
                    stripped = line.rstrip('\n')
                    if stripped == '' or len(stripped) - len(stripped.lstrip()) > block_indent:
                        removed += 1
                        continue
                skip_block = False
            # Check for priority: line
            if re.match(r'^(\s*)priority:\s+(must|should|could)\s*$', line):
                removed += 1
                continue
            result.append(line)
        if removed:
            yaml_file.write_text("".join(result))
            total += removed
            print(f"    {yaml_file.name}: removed {removed} lines")
    count("pass6", total)
    print(f"  Pass6 files: removed {total} lines total")


def strip_epic_reports():
    """Remove priority: lines and stories_by_priority: blocks from epic-report files."""
    total = 0
    files = list(SYNTHESIS_DIR.glob("epic-report-*.yaml"))
    for yaml_file in sorted(files):
        text = yaml_file.read_text()
        lines = text.splitlines(keepends=True)
        result = []
        skip_block = False
        block_indent = 0
        removed = 0
        for line in lines:
            # Check for stories_by_priority: block start
            m = re.match(r'^(\s*)stories_by_priority:\s*$', line)
            if m:
                skip_block = True
                block_indent = len(m.group(1))
                removed += 1
                continue
            # Skip indented children of stories_by_priority:
            if skip_block:
                stripped = line.rstrip('\n')
                if stripped == '' or len(stripped) - len(stripped.lstrip()) > block_indent:
                    removed += 1
                    continue
                skip_block = False
            # Check for priority: line
            if re.match(r'^(\s*)priority:\s+(must|should|could)\s*$', line):
                removed += 1
                continue
            result.append(line)
        if removed:
            yaml_file.write_text("".join(result))
            total += removed
            print(f"    {yaml_file.name}: removed {removed} lines")
    count("epic-reports", total)
    print(f"  Epic reports: removed {total} lines total")


def strip_tracker():
    """Remove by_priority: block from tracker.yaml."""
    text = TRACKER.read_text()
    lines = text.splitlines(keepends=True)
    result = []
    skip_block = False
    block_indent = 0
    removed = 0
    for line in lines:
        m = re.match(r'^(\s*)by_priority:\s*$', line)
        if m:
            skip_block = True
            block_indent = len(m.group(1))
            removed += 1
            continue
        if skip_block:
            stripped = line.rstrip('\n')
            if stripped == '' or len(stripped) - len(stripped.lstrip()) > block_indent:
                removed += 1
                continue
            skip_block = False
        result.append(line)
    if removed:
        TRACKER.write_text("".join(result))
    count("tracker", removed)
    print(f"  Tracker: removed {removed} lines")


def strip_synthesis_summary():
    """Remove priority references from synthesis-summary.md."""
    summary = SYNTHESIS_DIR / "synthesis-summary.md"
    if not summary.exists():
        print("  Synthesis summary: not found, skipping")
        return
    text = summary.read_text()
    lines = text.splitlines(keepends=True)
    result = []
    removed = 0
    for line in lines:
        # Remove lines that reference must-priority, "could" priority, etc.
        if re.search(r'must-priority|"could" priority|low priority story', line, re.IGNORECASE):
            removed += 1
            continue
        result.append(line)
    if removed:
        summary.write_text("".join(result))
    count("synthesis-summary", removed)
    print(f"  Synthesis summary: removed {removed} lines")


def main():
    print("Removing priority metadata from xs-requirements...\n")
    strip_stories()
    strip_epics()
    strip_pass6_files()
    strip_epic_reports()
    strip_tracker()
    strip_synthesis_summary()
    print("\n--- Summary ---")
    total = sum(stats.values())
    for k, v in stats.items():
        print(f"  {k}: {v} lines removed")
    print(f"  TOTAL: {total} lines removed")


if __name__ == "__main__":
    main()
