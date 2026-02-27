#!/usr/bin/env python3
"""Scan all bookminder-sessions/*.jsonl to derive exhaustive message type schema."""

import json
import glob
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml


def scan_sessions(sessions_dir: str) -> dict:
    """Scan all JSONL session files and extract schema information."""

    # Counters
    event_types = Counter()  # top-level .type values
    content_block_types = Counter()  # .message.content[].type values
    tool_names = Counter()  # tool_use .name values
    top_level_fields = defaultdict(lambda: defaultdict(int))  # per event type
    message_fields = defaultdict(lambda: defaultdict(int))  # per event type
    tool_result_fields = Counter()  # toolUseResult sub-fields
    special_patterns = Counter()
    stop_reasons = Counter()
    models = Counter()
    system_subtypes = Counter()

    # Content type: string vs array
    content_formats = Counter()  # "string" or "array"

    # Track which sessions had which types
    event_type_sessions = defaultdict(set)

    files = sorted(glob.glob(f"{sessions_dir}/*.jsonl"))
    total_lines = 0
    total_files = len(files)
    parse_errors = 0

    for fpath in files:
        fname = Path(fpath).stem
        short = fname[:8]

        with open(fpath, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                total_lines += 1

                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    parse_errors += 1
                    continue

                # Top-level type
                etype = entry.get("type", "<missing>")
                event_types[etype] += 1
                event_type_sessions[etype].add(short)

                # Top-level fields (per event type)
                for key in entry.keys():
                    top_level_fields[etype][key] += 1

                # isSidechain tracking
                if entry.get("isSidechain"):
                    special_patterns["isSidechain: true"] += 1

                # isMeta tracking
                if entry.get("isMeta"):
                    special_patterns["isMeta: true (caveat message)"] += 1

                # version tracking
                version = entry.get("version", "")
                if version:
                    major = version.split(".")[0] if "." in version else version
                    special_patterns[f"version {major}.x"] += 1

                # message content analysis
                msg = entry.get("message")
                if msg and isinstance(msg, dict):
                    for key in msg.keys():
                        message_fields[etype][key] += 1

                    content = msg.get("content")
                    if content is None:
                        content_formats["null/missing"] += 1
                    elif isinstance(content, str):
                        content_formats["string"] += 1
                        _scan_text_patterns(content, special_patterns)
                    elif isinstance(content, list):
                        content_formats["array"] += 1
                        for block in content:
                            if not isinstance(block, dict):
                                continue
                            btype = block.get("type", "<missing>")
                            content_block_types[btype] += 1

                            # Tool use
                            if btype == "tool_use":
                                tname = block.get("name", "<missing>")
                                tool_names[tname] += 1

                            # Text patterns in text blocks
                            if btype == "text":
                                text = block.get("text", "")
                                _scan_text_patterns(text, special_patterns)

                            # Tool result content
                            if btype == "tool_result":
                                tr_content = block.get("content")
                                if isinstance(tr_content, str):
                                    special_patterns["tool_result content: string"] += 1
                                elif isinstance(tr_content, list):
                                    special_patterns["tool_result content: array"] += 1
                                    for sub in tr_content:
                                        if isinstance(sub, dict):
                                            sub_type = sub.get("type", "?")
                                            special_patterns[
                                                f"tool_result sub-block: {sub_type}"
                                            ] += 1
                                elif tr_content is None:
                                    special_patterns["tool_result content: null"] += 1

                            # Image blocks
                            if btype == "image":
                                src = block.get("source", {})
                                media = src.get("media_type", "unknown")
                                special_patterns[f"image media_type: {media}"] += 1

                    # Model tracking
                    model = msg.get("model", "")
                    if model:
                        models[model] += 1

                    # Stop reason
                    sr = msg.get("stop_reason")
                    if sr:
                        stop_reasons[sr] += 1

                # toolUseResult fields
                tur = entry.get("toolUseResult")
                if tur and isinstance(tur, dict):
                    for key in tur.keys():
                        tool_result_fields[key] += 1

                # system subtype
                if etype == "system":
                    subtype = entry.get("subtype", "<missing>")
                    system_subtypes[subtype] += 1

                # summary fields
                if etype == "summary":
                    if "summary" in entry:
                        special_patterns["summary: has .summary text"] += 1
                    if "leafUuid" in entry:
                        special_patterns["summary: has .leafUuid"] += 1

    return {
        "scan_metadata": {
            "total_files": total_files,
            "total_lines": total_lines,
            "parse_errors": parse_errors,
        },
        "event_types": dict(event_types.most_common()),
        "event_type_sessions": {
            k: len(v) for k, v in sorted(event_type_sessions.items())
        },
        "content_block_types": dict(content_block_types.most_common()),
        "content_formats": dict(content_formats.most_common()),
        "tool_names": dict(tool_names.most_common()),
        "top_level_fields": {
            etype: dict(sorted(fields.items()))
            for etype, fields in sorted(top_level_fields.items())
        },
        "message_fields": {
            etype: dict(sorted(fields.items()))
            for etype, fields in sorted(message_fields.items())
        },
        "tool_result_fields": dict(tool_result_fields.most_common()),
        "system_subtypes": dict(system_subtypes.most_common()),
        "stop_reasons": dict(stop_reasons.most_common()),
        "models": dict(models.most_common()),
        "special_patterns": dict(
            sorted(special_patterns.items(), key=lambda x: -x[1])
        ),
    }


def _scan_text_patterns(text: str, patterns: Counter):
    """Scan text for special patterns."""
    if not text:
        return

    # Slash commands (user messages starting with /)
    if re.match(r"^/\w+", text.strip()):
        cmd = re.match(r"^(/\w+)", text.strip()).group(1)
        patterns[f"slash_command: {cmd}"] += 1

    # <bash-input> tags
    if "<bash-input>" in text:
        patterns["<bash-input> tag"] += 1

    # @file references
    if re.search(r"@\S+\.\w+", text):
        patterns["@file reference"] += 1

    # system-reminder tags
    if "<system-reminder>" in text:
        patterns["<system-reminder> tag"] += 1

    # User interruption
    if "[Request interrupted by user]" in text:
        patterns["[Request interrupted by user]"] += 1

    # MCP tool patterns (namespace:tool)
    if re.search(r"\b\w+:\w+\b", text) and "tool_use" not in text:
        pass  # Too noisy, skip

    # Markdown code blocks
    if "```" in text:
        patterns["markdown code block"] += 1

    # URLs
    if re.search(r"https?://", text):
        patterns["contains URL"] += 1


def build_schema_yaml(scan_results: dict) -> dict:
    """Build the final schema YAML structure."""

    schema = {
        "metadata": {
            "description": "Exhaustive message type schema derived from 1.x session transcripts",
            "era": "1.x (pre-2.0)",
            "source": "bookminder-sessions/*.jsonl",
            **scan_results["scan_metadata"],
        },
        "event_types": {},
        "content_block_types": {},
        "tool_names": {},
        "special_patterns": {},
    }

    # Event types with field inventory
    for etype, count in scan_results["event_types"].items():
        entry = {
            "count": count,
            "sessions": scan_results["event_type_sessions"].get(etype, 0),
            "era": "1.x",
            "top_level_fields": list(
                scan_results["top_level_fields"].get(etype, {}).keys()
            ),
        }
        msg_fields = scan_results["message_fields"].get(etype, {})
        if msg_fields:
            entry["message_fields"] = list(msg_fields.keys())

        # Add system subtypes
        if etype == "system" and scan_results["system_subtypes"]:
            entry["subtypes"] = scan_results["system_subtypes"]

        schema["event_types"][etype] = entry

    # Content block types
    for btype, count in scan_results["content_block_types"].items():
        schema["content_block_types"][btype] = {
            "count": count,
            "era": "1.x",
        }

    # Tool names
    for tname, count in scan_results["tool_names"].items():
        schema["tool_names"][tname] = {
            "count": count,
            "era": "1.x",
        }

    # Special patterns
    schema["special_patterns"] = scan_results["special_patterns"]

    # Additional details
    schema["content_format_polymorphism"] = scan_results["content_formats"]
    schema["tool_result_entry_fields"] = scan_results["tool_result_fields"]
    schema["stop_reasons"] = scan_results["stop_reasons"]
    schema["models"] = scan_results["models"]

    return schema


def add_2x_additions(schema: dict) -> dict:
    """Add known 2.x-only types and fields from format reference."""

    # 2.x event types not in 1.x sessions
    two_x_event_types = {
        "queue-operation": {
            "count": 0,
            "sessions": 0,
            "era": "2.x-only",
            "description": "Queue operation tracking (dequeue). Added in 2.x.",
            "top_level_fields": [
                "type",
                "operation",
                "timestamp",
                "sessionId",
            ],
            "note": "Not present in any 1.x session file",
        },
        "file-history-snapshot": {
            "count": 0,
            "sessions": 0,
            "era": "2.x-only",
            "description": "File history snapshot for rewind support. Added in 2.x.",
            "top_level_fields": ["type", "timestamp", "sessionId"],
            "note": "Not present in any 1.x session file",
        },
    }

    for etype, info in two_x_event_types.items():
        if etype not in schema["event_types"]:
            schema["event_types"][etype] = info

    # 2.x-only top-level fields (on existing event types)
    schema["two_x_only_fields"] = {
        "agent_id": {
            "location": "entry root",
            "description": "Identifies subagent type (v2.0.28+)",
            "era": "2.x-only",
        },
        "agent_transcript_path": {
            "location": "entry root",
            "description": "Path to subagent transcript file (v2.0.28+)",
            "era": "2.x-only",
        },
        "thinkingMetadata": {
            "location": "entry root",
            "description": "Extended thinking control metadata",
            "era": "2.x-only",
        },
        "todos": {
            "location": "entry root",
            "description": "Inline task tracking array",
            "era": "2.x-only",
        },
        "modelUsage": {
            "location": "entry root",
            "description": "Per-model token usage breakdown",
            "era": "2.x-only",
        },
    }

    # 2.x-only tool names
    two_x_tools = {
        "Skill": {
            "count": 0,
            "era": "2.x-only",
            "description": "Skill invocation tool, added in 2.x",
        },
        "MultiEdit": {
            "count": 0,
            "era": "2.x-only",
            "description": "Multi-file edit tool, added in 2.x",
        },
    }
    for tname, info in two_x_tools.items():
        if tname not in schema["tool_names"]:
            schema["tool_names"][tname] = info

    return schema


def main():
    sessions_dir = "/Users/palimondo/Developer/xs/bookminder-sessions"
    output_path = "/Users/palimondo/Developer/xs/xs-requirements/golden-files/schema.yaml"

    print(f"Scanning sessions in {sessions_dir}...")
    scan_results = scan_sessions(sessions_dir)

    print(f"  Files: {scan_results['scan_metadata']['total_files']}")
    print(f"  Lines: {scan_results['scan_metadata']['total_lines']}")
    print(f"  Parse errors: {scan_results['scan_metadata']['parse_errors']}")
    print(f"  Event types: {len(scan_results['event_types'])}")
    print(f"  Content block types: {len(scan_results['content_block_types'])}")
    print(f"  Tool names: {len(scan_results['tool_names'])}")

    print("\nBuilding schema...")
    schema = build_schema_yaml(scan_results)

    print("Adding 2.x additions from format reference...")
    schema = add_2x_additions(schema)

    # Write YAML
    with open(output_path, "w") as f:
        yaml.dump(
            schema,
            f,
            default_flow_style=False,
            sort_keys=False,
            width=120,
            allow_unicode=True,
        )

    print(f"\nSchema written to {output_path}")

    # Summary
    print("\n--- Event Types ---")
    for etype, info in schema["event_types"].items():
        era = info.get("era", "?")
        count = info.get("count", 0)
        sessions = info.get("sessions", 0)
        print(f"  {etype}: {count} occurrences in {sessions} sessions [{era}]")

    print("\n--- Tool Names ---")
    for tname, info in schema["tool_names"].items():
        era = info.get("era", "?")
        count = info.get("count", 0)
        print(f"  {tname}: {count} [{era}]")

    print("\n--- Content Block Types ---")
    for btype, info in schema["content_block_types"].items():
        count = info.get("count", 0)
        print(f"  {btype}: {count}")


if __name__ == "__main__":
    main()
