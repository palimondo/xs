#!/usr/bin/env python3
"""Progress tracker for story mining extraction.

Usage (always via uv):
  uv run --with pyyaml python3 xs-requirements/progress.py next-batch 12
  uv run --with pyyaml python3 xs-requirements/progress.py next-batch 12 --type daylog
  uv run --with pyyaml python3 xs-requirements/progress.py complete day-016-L1-200.yaml ...
  uv run --with pyyaml python3 xs-requirements/progress.py status
  uv run --with pyyaml python3 xs-requirements/progress.py reset dispatched
  uv run --with pyyaml python3 xs-requirements/progress.py reset failed
  uv run --with pyyaml python3 xs-requirements/progress.py reset day-016-L1-200.yaml ...
"""
import argparse
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

import yaml

PROGRESS_FILE = os.path.join(os.path.dirname(__file__), "findings", "progress.yaml")
FINDINGS_DIR = os.path.join(os.path.dirname(__file__), "findings")
VALIDATE_SH = os.path.join(os.path.dirname(__file__), "validate-findings.sh")
VALIDATE_PY = os.path.join(os.path.dirname(__file__), "validate-quotes.py")
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))


def load_progress():
    with open(PROGRESS_FILE) as f:
        return yaml.safe_load(f)


def save_progress(data):
    def represent_none(dumper, _):
        return dumper.represent_scalar("tag:yaml.org,2002:null", "null")

    yaml.add_representer(type(None), represent_none)

    with open(PROGRESS_FILE, "w") as f:
        f.write("# Pass 2: Story Mining Progress Tracker\n\n")
        yaml.dump(data, f, default_flow_style=False, sort_keys=False,
                  allow_unicode=True, width=120)


def iter_chunks(data, source_type=None):
    """Yield (section_key, source_name, chunk_index, chunk, source_entry) tuples."""
    sections = []
    if source_type in (None, "daylog"):
        sections.append(("daylogs", data.get("daylogs", {})))
    if source_type in (None, "session"):
        sections.append(("sessions", data.get("sessions", {})))

    for section_key, sources in sections:
        for source_name, source_entry in sources.items():
            if source_entry.get("status") == "skip":
                continue
            for i, chunk in enumerate(source_entry.get("chunks", [])):
                yield section_key, source_name, i, chunk, source_entry


def cmd_next_batch(args):
    data = load_progress()
    count = args.count
    source_type = args.type

    dispatched = []
    for section_key, source_name, chunk_idx, chunk, source_entry in iter_chunks(data, source_type):
        if chunk["status"] != "pending":
            continue
        if len(dispatched) >= count:
            break

        # Mark dispatched
        chunk["status"] = "dispatched"

        # Determine output filename
        ps = chunk["primary_start"]
        end = chunk["end"]
        output_file = f"{source_name}-L{ps}-{end}.yaml"

        # Source ref format
        src_type = "daylog" if section_key == "daylogs" else "session"
        source_ref = f"{source_name}:{ps}-{end}"

        dispatched.append({
            "source_type": src_type,
            "source_name": source_name,
            "source_ref": source_ref,
            "file": source_entry["file"],
            "context_start": chunk["context_start"],
            "primary_start": ps,
            "end": end,
            "output_file": output_file,
        })

    if not dispatched:
        print("No pending chunks found.")
        return

    # Save updated progress
    data["meta"]["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    save_progress(data)

    # Output for the orchestrator
    print(f"Dispatched {len(dispatched)} chunks:\n")
    for i, d in enumerate(dispatched, 1):
        print(f"CHUNK {i}:")
        print(f"  source_type: {d['source_type']}")
        print(f"  source_name: {d['source_name']}")
        print(f"  source_ref: {d['source_ref']}")
        print(f"  file: {d['file']}")
        print(f"  context_start: {d['context_start']}")
        print(f"  primary_start: {d['primary_start']}")
        print(f"  end: {d['end']}")
        print(f"  output_file: {d['output_file']}")
        print()


def find_chunk_for_file(data, filename):
    """Given a findings filename, find the matching chunk in progress.yaml."""
    # Parse filename: day-021-L11201-11400.yaml or 06a0-L1-100.yaml
    basename = os.path.basename(filename).replace(".yaml", "")
    m = re.match(r"^(.+)-L(\d+)-(\d+)$", basename)
    if not m:
        return None, None, None, None
    source_name = m.group(1)
    primary_start = int(m.group(2))
    end = int(m.group(3))

    # Search in daylogs first, then sessions
    for section_key in ("daylogs", "sessions"):
        sources = data.get(section_key, {})
        if source_name in sources:
            source_entry = sources[source_name]
            for i, chunk in enumerate(source_entry.get("chunks", [])):
                if chunk["primary_start"] == primary_start and chunk["end"] == end:
                    return section_key, source_name, i, source_entry
    return None, None, None, None


def run_validator(findings_file, source_file, primary_start, end):
    """Run both validators, return (passed, errors)."""
    abs_findings = os.path.join(FINDINGS_DIR, os.path.basename(findings_file))
    errors = []

    # validate-findings.sh
    if os.path.exists(VALIDATE_SH):
        result = subprocess.run(
            ["bash", VALIDATE_SH, abs_findings],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
        if result.returncode != 0:
            errors.append(f"validate-findings.sh: {result.stdout.strip()}")

    # validate-quotes.py
    if os.path.exists(VALIDATE_PY):
        result = subprocess.run(
            [os.path.expanduser("~/.local/bin/uv"), "run", "--with", "pyyaml",
             "python3", VALIDATE_PY, abs_findings, source_file],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
        if result.returncode != 0:
            output = (result.stdout.strip() + "\n" + result.stderr.strip()).strip()
            errors.append(f"validate-quotes.py: {output}")

    return len(errors) == 0, errors


def cmd_complete(args):
    data = load_progress()
    files = args.files

    results = {"complete": [], "failed": [], "not_found": [], "missing": []}

    for filepath in files:
        basename = os.path.basename(filepath)

        # Check file exists
        abs_path = os.path.join(FINDINGS_DIR, basename)
        if not os.path.exists(abs_path):
            results["missing"].append(basename)
            continue

        # Find matching chunk
        section_key, source_name, chunk_idx, source_entry = find_chunk_for_file(data, basename)
        if section_key is None:
            results["not_found"].append(basename)
            continue

        chunk = source_entry["chunks"][chunk_idx]

        # Run validators
        passed, errors = run_validator(basename, source_entry["file"],
                                       chunk["primary_start"], chunk["end"])

        if passed:
            chunk["status"] = "complete"
            chunk["findings_file"] = basename
            results["complete"].append(basename)
        else:
            chunk["status"] = "failed"
            chunk["findings_file"] = basename
            results["failed"].append((basename, errors))

    # Update source-level status (complete if all chunks complete)
    for section_key in ("daylogs", "sessions"):
        for source_name, source_entry in data.get(section_key, {}).items():
            if source_entry.get("status") == "skip":
                continue
            chunks = source_entry.get("chunks", [])
            if chunks and all(c["status"] == "complete" for c in chunks):
                source_entry["status"] = "complete"

    # Save
    data["meta"]["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    save_progress(data)

    # Report
    if results["complete"]:
        print(f"COMPLETE ({len(results['complete'])}):")
        for f in results["complete"]:
            print(f"  {f}")

    if results["failed"]:
        print(f"\nFAILED ({len(results['failed'])}):")
        for f, errs in results["failed"]:
            print(f"  {f}:")
            for e in errs:
                print(f"    {e}")

    if results["not_found"]:
        print(f"\nNOT IN PROGRESS ({len(results['not_found'])}):")
        for f in results["not_found"]:
            print(f"  {f}")

    if results["missing"]:
        print(f"\nFILE MISSING ({len(results['missing'])}):")
        for f in results["missing"]:
            print(f"  {f}")

    # Summary line
    total = len(files)
    ok = len(results["complete"])
    fail = len(results["failed"])
    print(f"\n{ok}/{total} validated and marked complete" +
          (f", {fail} failed" if fail else ""))


def cmd_status(args):
    data = load_progress()

    counts = {}
    for section_key in ("daylogs", "sessions"):
        section_counts = {"pending": 0, "dispatched": 0, "complete": 0, "failed": 0,
                          "sources_pending": 0, "sources_complete": 0, "sources_skip": 0}
        for source_name, source_entry in data.get(section_key, {}).items():
            if source_entry.get("status") == "skip":
                section_counts["sources_skip"] += 1
                continue
            if source_entry.get("status") == "complete":
                section_counts["sources_complete"] += 1
            else:
                section_counts["sources_pending"] += 1
            for chunk in source_entry.get("chunks", []):
                s = chunk.get("status", "pending")
                if s in section_counts:
                    section_counts[s] += 1
        counts[section_key] = section_counts

    params = data.get("meta", {}).get("parameters", {})
    phase = data.get("meta", {}).get("phase", "?")

    print(f"Phase: {phase}")
    print(f"Parameters: DL {params.get('dl_chunk_size')}/{params.get('dl_overlap')} "
          f"Sess {params.get('session_chunk_size')}/{params.get('session_overlap')} "
          f"Model: {params.get('model')}")
    print()

    for label, key in [("Day Logs", "daylogs"), ("Sessions", "sessions")]:
        c = counts[key]
        total_chunks = c["pending"] + c["dispatched"] + c["complete"] + c["failed"]
        total_sources = c["sources_pending"] + c["sources_complete"] + c["sources_skip"]
        print(f"{label}: {total_sources} sources "
              f"({c['sources_complete']} complete, {c['sources_pending']} pending, "
              f"{c['sources_skip']} skip)")
        print(f"  Chunks: {total_chunks} total — "
              f"{c['complete']} complete, {c['dispatched']} dispatched, "
              f"{c['pending']} pending"
              + (f", {c['failed']} FAILED" if c["failed"] else ""))
        print()

    grand_total = sum(c["pending"] + c["dispatched"] + c["complete"] + c["failed"]
                      for c in counts.values())
    grand_complete = sum(c["complete"] for c in counts.values())
    grand_dispatched = sum(c["dispatched"] for c in counts.values())
    pct = f"{100 * grand_complete / grand_total:.1f}%" if grand_total else "0%"
    print(f"Overall: {grand_complete}/{grand_total} chunks complete ({pct})"
          + (f", {grand_dispatched} in flight" if grand_dispatched else ""))


def cmd_reset(args):
    data = load_progress()
    target = args.target
    reset_count = 0

    if target in ("dispatched", "failed"):
        # Reset all chunks with the given status back to pending
        for section_key, source_name, chunk_idx, chunk, source_entry in iter_chunks(data):
            if chunk["status"] == target:
                chunk["status"] = "pending"
                chunk["findings_file"] = None
                reset_count += 1
        # Also reset source-level status if needed
        for section_key in ("daylogs", "sessions"):
            for sn, se in data.get(section_key, {}).items():
                if se.get("status") == "skip":
                    continue
                if any(c["status"] != "complete" for c in se.get("chunks", [])):
                    se["status"] = "pending"
    else:
        # Treat target as a filename, plus any additional files in args.extra_files
        filenames = [target] + (args.extra_files or [])
        for filename in filenames:
            basename = os.path.basename(filename)
            section_key, source_name, chunk_idx, source_entry = find_chunk_for_file(data, basename)
            if section_key is None:
                print(f"  NOT FOUND: {basename}")
                continue
            chunk = source_entry["chunks"][chunk_idx]
            old_status = chunk["status"]
            chunk["status"] = "pending"
            chunk["findings_file"] = None
            source_entry["status"] = "pending"
            print(f"  {basename}: {old_status} -> pending")
            reset_count += 1

    data["meta"]["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    save_progress(data)
    print(f"\nReset {reset_count} chunk(s) to pending")


def main():
    parser = argparse.ArgumentParser(description="Story mining progress tracker")
    sub = parser.add_subparsers(dest="command", required=True)

    # next-batch
    nb = sub.add_parser("next-batch", help="Get next N pending chunks and mark dispatched")
    nb.add_argument("count", type=int, help="Number of chunks to dispatch")
    nb.add_argument("--type", choices=["daylog", "session"],
                    help="Only return chunks of this type")

    # complete
    comp = sub.add_parser("complete", help="Validate findings files and mark chunks complete")
    comp.add_argument("files", nargs="+", help="Findings filenames (basename or path)")

    # status
    sub.add_parser("status", help="Show progress summary")

    # reset
    rst = sub.add_parser("reset", help="Reset chunks back to pending")
    rst.add_argument("target", help="'dispatched', 'failed', or a findings filename")
    rst.add_argument("extra_files", nargs="*", help="Additional filenames when resetting specific chunks")

    args = parser.parse_args()
    if args.command == "next-batch":
        cmd_next_batch(args)
    elif args.command == "complete":
        cmd_complete(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "reset":
        cmd_reset(args)


if __name__ == "__main__":
    main()
