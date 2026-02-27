#!/usr/bin/env python3
"""Extract focused JSONL fragments from real sessions for golden file fixtures.

Each fixture is a small (2-10 entry) self-contained fragment covering a specific
message pattern. Entries are extracted by line number from the source session,
preserving the original JSONL exactly (no reformatting).
"""

import json
import glob
import os
from pathlib import Path

SESSIONS_DIR = "/Users/palimondo/Developer/xs/bookminder-sessions"
OUTPUT_DIR = "/Users/palimondo/Developer/xs/xs-requirements/golden-files/fixtures/real"


def extract_lines(session_glob: str, line_numbers: list[int]) -> list[str]:
    """Extract specific lines (1-indexed) from a session file."""
    files = sorted(glob.glob(f"{SESSIONS_DIR}/{session_glob}*.jsonl"))
    if not files:
        raise FileNotFoundError(f"No session matching {session_glob}")
    fpath = files[0]
    lines = {}
    with open(fpath) as f:
        for i, line in enumerate(f, 1):
            if i in line_numbers:
                lines[i] = line.rstrip("\n")
    return [lines[n] for n in sorted(line_numbers) if n in lines]


def extract_range(session_glob: str, start: int, end: int) -> list[str]:
    """Extract a range of lines (1-indexed, inclusive) from a session file."""
    return extract_lines(session_glob, list(range(start, end + 1)))


def find_lines_matching(session_glob: str, predicate, max_results: int = 5) -> list[tuple[int, dict]]:
    """Find lines matching a predicate. Returns (line_number, parsed_entry) pairs."""
    files = sorted(glob.glob(f"{SESSIONS_DIR}/{session_glob}*.jsonl"))
    if not files:
        return []
    results = []
    with open(files[0]) as f:
        for i, line in enumerate(f, 1):
            try:
                entry = json.loads(line)
                if predicate(entry):
                    results.append((i, entry))
                    if len(results) >= max_results:
                        break
            except json.JSONDecodeError:
                continue
    return results


def write_fixture(name: str, lines: list[str], description: str):
    """Write a fixture file with a comment header."""
    outpath = os.path.join(OUTPUT_DIR, name)
    with open(outpath, "w") as f:
        for line in lines:
            f.write(line + "\n")
    count = len(lines)
    print(f"  {name}: {count} entries — {description}")


def extract_all():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("Extracting real JSONL fixtures...\n")

    # ── 1. Basic conversation (user text → assistant thinking + text) ──
    # Use session 0a5034b4 (small, clean session)
    # Find a user message with string content followed by assistant with thinking
    matches = find_lines_matching("0a5034b4", lambda e: (
        e.get("type") == "user"
        and isinstance(e.get("message", {}).get("content"), str)
    ), max_results=1)
    if matches:
        line_num = matches[0][0]
        lines = extract_range("0a5034b4", line_num, line_num + 2)
        write_fixture("basic-conversation.jsonl", lines,
                       "user string message → assistant thinking + text response")

    # ── 2. Tool use: Bash with stdout/stderr ──
    # Session 1e83 has lots of Bash usage. Find a Bash tool_use + tool_result pair.
    matches = find_lines_matching("1e83", lambda e: (
        e.get("type") == "assistant"
        and isinstance(e.get("message", {}).get("content"), list)
        and any(b.get("name") == "Bash" for b in e["message"]["content"]
                if b.get("type") == "tool_use")
    ), max_results=1)
    if matches:
        line_num = matches[0][0]
        lines = extract_range("1e83", line_num, line_num + 1)
        write_fixture("tool-bash.jsonl", lines,
                       "Bash tool_use + tool_result with stdout/stderr")

    # ── 3. Tool use: Read ──
    matches = find_lines_matching("1e83", lambda e: (
        e.get("type") == "assistant"
        and isinstance(e.get("message", {}).get("content"), list)
        and any(b.get("name") == "Read" for b in e["message"]["content"]
                if b.get("type") == "tool_use")
    ), max_results=1)
    if matches:
        line_num = matches[0][0]
        lines = extract_range("1e83", line_num, line_num + 1)
        write_fixture("tool-read.jsonl", lines,
                       "Read tool_use + tool_result")

    # ── 4. Tool use: Edit ──
    matches = find_lines_matching("1e83", lambda e: (
        e.get("type") == "assistant"
        and isinstance(e.get("message", {}).get("content"), list)
        and any(b.get("name") == "Edit" for b in e["message"]["content"]
                if b.get("type") == "tool_use")
    ), max_results=1)
    if matches:
        line_num = matches[0][0]
        lines = extract_range("1e83", line_num, line_num + 1)
        write_fixture("tool-edit.jsonl", lines,
                       "Edit tool_use + tool_result with structuredPatch")

    # ── 5. Tool use: Grep + Glob ──
    matches = find_lines_matching("1e83", lambda e: (
        e.get("type") == "assistant"
        and isinstance(e.get("message", {}).get("content"), list)
        and any(b.get("name") == "Grep" for b in e["message"]["content"]
                if b.get("type") == "tool_use")
    ), max_results=1)
    if matches:
        line_num = matches[0][0]
        lines = extract_range("1e83", line_num, line_num + 1)
        write_fixture("tool-grep.jsonl", lines,
                       "Grep tool_use + tool_result")

    matches = find_lines_matching("1e83", lambda e: (
        e.get("type") == "assistant"
        and isinstance(e.get("message", {}).get("content"), list)
        and any(b.get("name") == "Glob" for b in e["message"]["content"]
                if b.get("type") == "tool_use")
    ), max_results=1)
    if matches:
        line_num = matches[0][0]
        lines = extract_range("1e83", line_num, line_num + 1)
        write_fixture("tool-glob.jsonl", lines,
                       "Glob tool_use + tool_result")

    # ── 6. Tool use: Write ──
    matches = find_lines_matching("b475", lambda e: (
        e.get("type") == "assistant"
        and isinstance(e.get("message", {}).get("content"), list)
        and any(b.get("name") == "Write" for b in e["message"]["content"]
                if b.get("type") == "tool_use")
    ), max_results=1)
    if matches:
        line_num = matches[0][0]
        lines = extract_range("b475", line_num, line_num + 1)
        write_fixture("tool-write.jsonl", lines,
                       "Write tool_use + tool_result")

    # ── 7. Tool use: TodoWrite ──
    matches = find_lines_matching("1e83", lambda e: (
        e.get("type") == "assistant"
        and isinstance(e.get("message", {}).get("content"), list)
        and any(b.get("name") == "TodoWrite" for b in e["message"]["content"]
                if b.get("type") == "tool_use")
    ), max_results=1)
    if matches:
        line_num = matches[0][0]
        lines = extract_range("1e83", line_num, line_num + 1)
        write_fixture("tool-todowrite.jsonl", lines,
                       "TodoWrite tool_use + tool_result with oldTodos/newTodos")

    # ── 8. Tool use: WebFetch ──
    matches = find_lines_matching("b475", lambda e: (
        e.get("type") == "assistant"
        and isinstance(e.get("message", {}).get("content"), list)
        and any(b.get("name") == "WebFetch" for b in e["message"]["content"]
                if b.get("type") == "tool_use")
    ), max_results=1)
    if matches:
        line_num = matches[0][0]
        lines = extract_range("b475", line_num, line_num + 1)
        write_fixture("tool-webfetch.jsonl", lines,
                       "WebFetch tool_use + tool_result")

    # ── 9. Tool use: Task (subagent) ──
    matches = find_lines_matching("e583", lambda e: (
        e.get("type") == "assistant"
        and isinstance(e.get("message", {}).get("content"), list)
        and any(b.get("name") == "Task" for b in e["message"]["content"]
                if b.get("type") == "tool_use")
    ), max_results=1)
    if matches:
        line_num = matches[0][0]
        lines = extract_range("e583", line_num, line_num + 1)
        write_fixture("tool-task.jsonl", lines,
                       "Task tool_use + tool_result with subagent fields")

    # ── 10. Sidechain entries ──
    matches = find_lines_matching("e583", lambda e: e.get("isSidechain") is True, max_results=4)
    if matches:
        line_nums = [m[0] for m in matches]
        lines = extract_lines("e583", line_nums)
        write_fixture("sidechain.jsonl", lines,
                       "Entries with isSidechain: true (subagent work)")

    # ── 11. User interruption ──
    matches = find_lines_matching("1e83", lambda e: (
        e.get("type") == "user"
        and isinstance(e.get("message", {}).get("content"), list)
        and any(
            "Request interrupted" in (b.get("text", "") if isinstance(b, dict) else "")
            for b in e["message"]["content"]
        )
    ), max_results=1)
    if matches:
        line_num = matches[0][0]
        # Get the preceding assistant message too
        lines = extract_range("1e83", max(1, line_num - 1), line_num)
        write_fixture("interruption.jsonl", lines,
                       "User interruption with [Request interrupted by user]")

    # ── 12. isMeta caveat message ──
    matches = find_lines_matching("e583", lambda e: e.get("isMeta") is True, max_results=2)
    if matches:
        line_nums = [m[0] for m in matches]
        lines = extract_lines("e583", line_nums)
        write_fixture("meta-caveat.jsonl", lines,
                       "isMeta: true caveat messages")

    # ── 13. Summary entry ──
    matches = find_lines_matching("0a5034b4", lambda e: e.get("type") == "summary", max_results=2)
    if matches:
        line_nums = [m[0] for m in matches]
        lines = extract_lines("0a5034b4", line_nums)
        write_fixture("summary.jsonl", lines,
                       "Summary entries with summary text + leafUuid")

    # ── 14. System: compact_boundary ──
    matches = find_lines_matching("760a", lambda e: (
        e.get("type") == "system" and e.get("subtype") == "compact_boundary"
    ), max_results=1)
    if matches:
        line_num = matches[0][0]
        lines = extract_range("760a", line_num, line_num)
        write_fixture("system-compact-boundary.jsonl", lines,
                       "system compact_boundary with compactMetadata (2.x)")

    # ── 15. System: local_command ──
    matches = find_lines_matching("760a", lambda e: (
        e.get("type") == "system" and e.get("subtype") == "local_command"
    ), max_results=2)
    if matches:
        line_nums = [m[0] for m in matches]
        lines = extract_lines("760a", line_nums)
        write_fixture("system-local-command.jsonl", lines,
                       "system local_command entries (/model, /usage)")

    # ── 16. System: PreToolUse hook (no subtype) ──
    matches = find_lines_matching("1e83", lambda e: (
        e.get("type") == "system"
        and e.get("subtype") is None
        and "content" in e
    ), max_results=2)
    if matches:
        line_nums = [m[0] for m in matches]
        lines = extract_lines("1e83", line_nums)
        write_fixture("system-hook.jsonl", lines,
                       "system PreToolUse hook entries (no subtype)")

    # ── 17. isApiErrorMessage ──
    matches = find_lines_matching("760a", lambda e: e.get("isApiErrorMessage") is True, max_results=1)
    if matches:
        line_num = matches[0][0]
        lines = extract_range("760a", line_num, line_num)
        write_fixture("api-error.jsonl", lines,
                       "isApiErrorMessage: true (API error response)")

    # ── 18. isCompactSummary ──
    matches = find_lines_matching("760a", lambda e: e.get("isCompactSummary") is True, max_results=1)
    if matches:
        line_num = matches[0][0]
        lines = extract_range("760a", line_num, line_num)
        write_fixture("compact-summary.jsonl", lines,
                       "isCompactSummary: true (post-compaction context)")

    # ── 19. file-history-snapshot ──
    matches = find_lines_matching("760a", lambda e: e.get("type") == "file-history-snapshot", max_results=1)
    if matches:
        line_num = matches[0][0]
        lines = extract_range("760a", line_num, line_num)
        write_fixture("file-history-snapshot.jsonl", lines,
                       "file-history-snapshot entry")

    # ── 20. Image content ──
    matches = find_lines_matching("*", lambda e: (
        isinstance(e.get("message", {}).get("content"), list)
        and any(b.get("type") == "image" for b in e["message"]["content"]
                if isinstance(b, dict))
    ), max_results=1)
    if matches:
        line_num = matches[0][0]
        # Images can be large (base64), just note it
        print(f"  [NOTE] Image content found at line {line_num} — skipping (base64 too large)")

    # ── 21. Thinking block (standalone) ──
    matches = find_lines_matching("1e83", lambda e: (
        e.get("type") == "assistant"
        and isinstance(e.get("message", {}).get("content"), list)
        and any(b.get("type") == "thinking" for b in e["message"]["content"]
                if isinstance(b, dict))
        and not any(b.get("type") == "tool_use" for b in e["message"]["content"]
                    if isinstance(b, dict))
    ), max_results=1)
    if matches:
        line_num = matches[0][0]
        lines = extract_range("1e83", line_num, line_num)
        write_fixture("thinking-block.jsonl", lines,
                       "Assistant with thinking + text (no tool_use)")

    # ── 22. Multi-tool assistant (text + multiple tool_use in one message) ──
    matches = find_lines_matching("1e83", lambda e: (
        e.get("type") == "assistant"
        and isinstance(e.get("message", {}).get("content"), list)
        and sum(1 for b in e["message"]["content"]
                if isinstance(b, dict) and b.get("type") == "tool_use") >= 2
    ), max_results=1)
    if matches:
        line_num = matches[0][0]
        # Get the message + all its tool results
        entry = matches[0][1]
        tool_count = sum(1 for b in entry["message"]["content"]
                         if isinstance(b, dict) and b.get("type") == "tool_use")
        lines = extract_range("1e83", line_num, line_num + tool_count)
        write_fixture("multi-tool.jsonl", lines,
                       f"Assistant with {tool_count} tool_use blocks + their results")

    # ── 23. MCP tool ──
    matches = find_lines_matching("*", lambda e: (
        e.get("type") == "assistant"
        and isinstance(e.get("message", {}).get("content"), list)
        and any(b.get("name", "").startswith("mcp__") for b in e["message"]["content"]
                if isinstance(b, dict) and b.get("type") == "tool_use")
    ), max_results=1)
    if matches:
        line_num = matches[0][0]
        lines = extract_range("*", line_num, line_num + 1)
        # This won't work with glob for range, handle specially
        print(f"  [NOTE] MCP tool found — extracting from specific session needed")

    print(f"\nDone. Fixtures written to {OUTPUT_DIR}/")


if __name__ == "__main__":
    extract_all()
