#!/usr/bin/env python3
"""Consolidate all findings YAML files into a single dataset.

Step A of Phase 4 Synthesis:
- Parses all findings YAML files
- Normalizes 66 type variants to 6 canonical types
- Namespaces thread IDs to be globally unique
- Deduplicates exact-quote matches from overlapping chunks
- Outputs all-findings.yaml and all-findings.tsv
"""

import glob
import os
import sys
from collections import Counter
from datetime import datetime, timezone

import yaml

FINDINGS_DIR = os.path.join(os.path.dirname(__file__), "findings")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "synthesis")

# Normalization mapping: variant -> canonical type
TYPE_NORMALIZATION = {
    # user_request (541 + variants)
    "user_request": "user_request",
    "user_requirement": "user_request",
    "user_clarification": "user_request",
    "user_acceptance": "user_request",
    "user_validation": "user_request",
    "formatting_requirement": "user_request",
    "feature_verification": "user_request",
    "design_requirement": "user_request",
    # user_correction (239 + variants)
    "user_correction": "user_correction",
    # design_decision (22 + variants)
    "design_decision": "design_decision",
    "design_rationale": "design_decision",
    "design_specification": "design_decision",
    "design_validation": "design_decision",
    "design_artifact": "design_decision",
    "format_specification": "design_decision",
    "workflow_pattern": "design_decision",
    "testing_pattern": "design_decision",
    # agent_proposal (314 + variants)
    "agent_proposal": "agent_proposal",
    "agent_implementation": "agent_proposal",
    "agent_response": "agent_proposal",
    "agent_action": "agent_proposal",
    "agent_behavior": "agent_proposal",
    "agent_observation": "agent_proposal",
    "agent_design": "agent_proposal",
    "agent_statement": "agent_proposal",
    "agent_analysis": "agent_proposal",
    "agent_explanation": "agent_proposal",
    "agent_decision": "agent_proposal",
    "agent_correction": "agent_proposal",
    "agent": "agent_proposal",
    "agent_error": "agent_proposal",
    "claude_misunderstanding": "agent_proposal",
    "claude_observation": "agent_proposal",
    "claude_discovery": "agent_proposal",
    "claude_understanding": "agent_proposal",
    "claude_proposal": "agent_proposal",
    # implementation_detail (29 + variants)
    "implementation_detail": "implementation_detail",
    "implementation_note": "implementation_detail",
    "implementation_finding": "implementation_detail",
    "implementation_pattern": "implementation_detail",
    "implementation_approach": "implementation_detail",
    "implementation": "implementation_detail",
    "technical_detail": "implementation_detail",
    "technical_investigation": "implementation_detail",
    "code_structure": "implementation_detail",
    "code_change": "implementation_detail",
    "data_structure": "implementation_detail",
    "data_structure_observation": "implementation_detail",
    "discovered_format": "implementation_detail",
    "reference_output": "implementation_detail",
    "validation_check": "implementation_detail",
    "validation": "implementation_detail",
    # unresolved (21 + variants)
    "unresolved": "unresolved",
    # Observational / contextual -> map to closest canonical
    "observation": "implementation_detail",
    "context_background": "implementation_detail",
    "context_observation": "implementation_detail",
    "contextual_observation": "implementation_detail",
    "background_context": "implementation_detail",
    "context": "implementation_detail",
    "context_note": "implementation_detail",
    "context_only": "implementation_detail",
    "system_knowledge": "implementation_detail",
    "observed_behavior": "implementation_detail",
    "example": "implementation_detail",
    "evidence": "implementation_detail",
    "resolved": "design_decision",
}


def parse_findings_file(filepath):
    """Parse a single findings YAML file, return (source, threads, findings) or None."""
    with open(filepath) as f:
        data = yaml.safe_load(f)

    if not data:
        return None

    findings = data.get("findings") or []
    if not findings:
        return None

    source = data.get("source", os.path.basename(filepath).replace(".yaml", ""))
    threads = data.get("threads") or []
    notes = data.get("notes") or []

    return {
        "source": source,
        "filename": os.path.basename(filepath),
        "threads": threads,
        "findings": findings,
        "notes": notes,
    }


def namespace_thread_id(filename_stem, thread_id):
    """Make thread IDs globally unique: T001 in b475-L1-100.yaml -> b475-L1-100/T001"""
    return f"{filename_stem}/{thread_id}"


def normalize_type(raw_type):
    """Normalize a finding type to one of 6 canonical types."""
    canonical = TYPE_NORMALIZATION.get(raw_type)
    if canonical:
        return canonical
    # Fallback: try to match by prefix
    for prefix, target in [
        ("user_", "user_request"),
        ("agent_", "agent_proposal"),
        ("claude_", "agent_proposal"),
        ("design_", "design_decision"),
        ("implementation_", "implementation_detail"),
        ("technical_", "implementation_detail"),
        ("format_", "implementation_detail"),
        ("code_", "implementation_detail"),
    ]:
        if raw_type.startswith(prefix):
            return target
    # Last resort
    return "implementation_detail"


def truncate_quote(quote, max_len=80):
    """Truncate quote to max_len chars for TSV output."""
    if not quote:
        return ""
    quote = str(quote).replace("\t", " ").replace("\n", " ")
    if len(quote) <= max_len:
        return quote
    return quote[:max_len - 3] + "..."


def deduplicate_findings(all_findings):
    """Remove exact-quote duplicates from overlapping chunks.

    When the same quote appears in adjacent chunks from the same source prefix,
    keep only the first occurrence (by source line number).
    """
    seen_quotes = {}  # (source_prefix, normalized_quote) -> finding
    deduped = []
    dup_count = 0

    for f in all_findings:
        source_prefix = f["source"].split(":")[0] if ":" in f["source"] else f["source"]
        quote = (f.get("quote") or "").strip()
        if not quote:
            deduped.append(f)
            continue

        key = (source_prefix, quote)
        if key in seen_quotes:
            dup_count += 1
            continue
        seen_quotes[key] = f
        deduped.append(f)

    return deduped, dup_count


def consolidate():
    """Main consolidation logic."""
    yaml_files = sorted(glob.glob(os.path.join(FINDINGS_DIR, "*.yaml")))
    yaml_files = [f for f in yaml_files if os.path.basename(f) != "progress.yaml"]

    total_files = len(yaml_files)
    all_findings = []
    all_threads = []
    raw_type_counts = Counter()
    normalized_type_counts = Counter()
    source_counts = Counter()
    files_with_findings = 0

    for filepath in yaml_files:
        parsed = parse_findings_file(filepath)
        if not parsed:
            continue

        files_with_findings += 1
        filename_stem = os.path.basename(filepath).replace(".yaml", "")
        source = parsed["source"]
        source_prefix = source.split(":")[0] if ":" in source else source

        # Namespace threads
        for thread in parsed["threads"]:
            original_id = thread.get("id", "")
            thread["id"] = namespace_thread_id(filename_stem, original_id)
            thread["source"] = source
            thread["filename"] = parsed["filename"]
            all_threads.append(thread)

        # Process findings
        for finding in parsed["findings"]:
            raw_type = finding.get("type", "unknown")
            raw_type_counts[raw_type] += 1

            canonical_type = normalize_type(raw_type)
            normalized_type_counts[canonical_type] += 1

            # Namespace thread reference
            original_thread = finding.get("thread", "")
            if original_thread:
                finding["thread"] = namespace_thread_id(filename_stem, original_thread)

            finding["original_type"] = raw_type
            finding["type"] = canonical_type
            finding["source"] = source
            finding["filename"] = parsed["filename"]

            source_counts[source_prefix] += 1
            all_findings.append(finding)

    # Deduplicate
    all_findings, dup_count = deduplicate_findings(all_findings)

    # Recount after dedup
    final_type_counts = Counter()
    final_source_counts = Counter()
    for f in all_findings:
        final_type_counts[f["type"]] += 1
        prefix = f["source"].split(":")[0] if ":" in f["source"] else f["source"]
        final_source_counts[prefix] += 1

    # Print statistics
    print(f"=== Consolidation Statistics ===")
    print(f"Total YAML files scanned: {total_files}")
    print(f"Files with findings: {files_with_findings}")
    print(f"Total raw findings: {sum(raw_type_counts.values())}")
    print(f"Duplicates removed: {dup_count}")
    print(f"Final findings count: {len(all_findings)}")
    print(f"Total threads: {len(all_threads)}")
    print()
    print(f"Raw type distribution ({len(raw_type_counts)} types):")
    for t, c in raw_type_counts.most_common(10):
        print(f"  {t}: {c}")
    if len(raw_type_counts) > 10:
        print(f"  ... and {len(raw_type_counts) - 10} more types")
    print()
    print(f"Normalized type distribution ({len(normalized_type_counts)} types):")
    for t, c in sorted(normalized_type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")
    print()
    print(f"After dedup — type distribution:")
    for t, c in sorted(final_type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")
    print()
    print(f"Top sources (after dedup):")
    for s, c in final_source_counts.most_common(15):
        print(f"  {s}: {c}")

    # Write full YAML
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    yaml_output = {
        "meta": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "total_files_scanned": total_files,
            "files_with_findings": files_with_findings,
            "raw_findings_count": sum(raw_type_counts.values()),
            "duplicates_removed": dup_count,
            "final_findings_count": len(all_findings),
            "total_threads": len(all_threads),
            "type_distribution": dict(final_type_counts.most_common()),
            "source_distribution": dict(final_source_counts.most_common()),
        },
        "threads": all_threads,
        "findings": all_findings,
    }

    yaml_path = os.path.join(OUTPUT_DIR, "all-findings.yaml")
    with open(yaml_path, "w") as f:
        yaml.dump(yaml_output, f, default_flow_style=False, allow_unicode=True, width=120)
    print(f"\nWrote: {yaml_path} ({os.path.getsize(yaml_path)} bytes)")

    # Write TSV
    tsv_path = os.path.join(OUTPUT_DIR, "all-findings.tsv")
    with open(tsv_path, "w") as f:
        f.write("source\tline\ttype\tspeaker\tquote_80\tthread_id\toriginal_type\tfilename\n")
        for finding in all_findings:
            source = finding.get("source", "")
            line = finding.get("line", "")
            ftype = finding.get("type", "")
            speaker = finding.get("speaker", "")
            quote = truncate_quote(finding.get("quote", ""))
            thread = finding.get("thread", "")
            original_type = finding.get("original_type", "")
            filename = finding.get("filename", "")
            f.write(f"{source}\t{line}\t{ftype}\t{speaker}\t{quote}\t{thread}\t{original_type}\t{filename}\n")
    print(f"Wrote: {tsv_path} ({os.path.getsize(tsv_path)} bytes)")

    # Also write a story-ID inventory for subagents
    story_inventory_path = os.path.join(OUTPUT_DIR, "story-inventory.tsv")
    stories_dir = os.path.join(os.path.dirname(__file__), "stories")
    with open(story_inventory_path, "w") as f:
        f.write("story_id\tepic\tfilename\ttitle\n")
        for epic_dir in sorted(os.listdir(stories_dir)):
            epic_path = os.path.join(stories_dir, epic_dir)
            if not os.path.isdir(epic_path):
                continue
            for story_file in sorted(os.listdir(epic_path)):
                if not story_file.endswith(".yaml"):
                    continue
                story_path = os.path.join(epic_path, story_file)
                with open(story_path) as sf:
                    try:
                        story_data = yaml.safe_load(sf)
                    except yaml.YAMLError:
                        story_data = None
                if story_data:
                    sid = story_data.get("id", "?")
                    title = story_data.get("title", "?")
                    epic = story_data.get("epic", epic_dir)
                    f.write(f"{sid}\t{epic}\t{story_file}\t{title}\n")
    print(f"Wrote: {story_inventory_path} ({os.path.getsize(story_inventory_path)} bytes)")

    return len(all_findings)


def chrono_sort():
    """Re-sort all-findings.tsv chronologically by source date, then line number."""

    # Date mapping: source prefix -> (sort_date, sort_order_within_date)
    # Order within same date approximates chronological sequence
    SOURCE_DATES = {
        # Jul 4-5
        "day-017": ("2025-07-04", 0),
        # Jul 6
        "day-018": ("2025-07-06", 0),
        # Jul 9-12 (day-020 covers Jul 9-12)
        "day-020": ("2025-07-09", 0),
        "06a0": ("2025-07-12", 1),
        # Jul 12 (day-021 is Jul 12)
        "day-021": ("2025-07-12", 2),
        # Jul 13
        "day-022": ("2025-07-13", 0),
        "943d": ("2025-07-13", 1),
        # Jul 21
        "day-023": ("2025-07-21", 0),
        # Jul 23
        "day-024": ("2025-07-23", 0),
        "fa0d": ("2025-07-23", 1),
        # Jul 25
        "f9c7": ("2025-07-25", 0),
        # Jul 26
        "day-025": ("2025-07-26", 0),
        "cc2d": ("2025-07-26", 1),
        "e2f7": ("2025-07-26", 2),
        "fa1a": ("2025-07-26", 3),
        "7159": ("2025-07-26", 4),
        # Jul 27
        "b722": ("2025-07-27", 0),
        "b475": ("2025-07-27", 1),
        "0841": ("2025-07-27", 2),
        # Jul 28
        "caf2": ("2025-07-28", 0),
        # Jul 30
        "3636": ("2025-07-30", 0),
        # Jul 31
        "a40c": ("2025-07-31", 0),
        # Aug 1
        "1e83": ("2025-08-01", 0),
        # Aug 2
        "e583": ("2025-08-02", 0),
        # Oct 16 (late session)
        "760a": ("2025-10-16", 0),
    }

    tsv_path = os.path.join(OUTPUT_DIR, "all-findings.tsv")
    chrono_path = os.path.join(OUTPUT_DIR, "all-findings-chrono.tsv")

    with open(tsv_path) as f:
        header = f.readline()
        rows = f.readlines()

    def sort_key(row):
        fields = row.split("\t")
        source = fields[0]  # e.g. "b475:1-100"
        prefix = source.split(":")[0] if ":" in source else source
        line_range = source.split(":")[1] if ":" in source else "0-0"
        start_line = int(line_range.split("-")[0]) if "-" in line_range else int(line_range or "0")
        line_num = int(fields[1]) if fields[1].isdigit() else 0

        date_info = SOURCE_DATES.get(prefix, ("9999-99-99", 0))
        return (date_info[0], date_info[1], start_line, line_num)

    rows.sort(key=sort_key)

    with open(chrono_path, "w") as f:
        f.write(header)
        f.writelines(rows)

    print(f"Wrote: {chrono_path} ({len(rows)} findings, {os.path.getsize(chrono_path)} bytes)")


if __name__ == "__main__":
    if "--chrono" in sys.argv:
        chrono_sort()
    else:
        count = consolidate()
        sys.exit(0 if count > 0 else 1)
