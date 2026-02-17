# Orchestrator Runbook

How to run story mining extraction using `progress.py`.

## Setup

All commands use uv to get PyYAML:

```bash
cd /Users/palimondo/Developer/xs
alias progress='~/.local/bin/uv run --with pyyaml python3 xs-requirements/progress.py'
```

## The Extraction Loop

### 1. Check status

```bash
progress status
```

Shows: phase, parameters, chunk counts (pending/dispatched/complete/failed) per source type.

### 2. Get next batch and spawn subagents

```bash
progress next-batch 12 --type daylog    # Phase 2: day logs
progress next-batch 12 --type session   # Phase 3: sessions
progress next-batch 12                  # Either (daylogs first)
```

This atomically: finds next N pending chunks, marks them `dispatched`, prints chunk
details. Use the output to fill in template parameters and spawn subagents.

Each chunk's output includes all fields needed for the extraction template:
- `source_type`, `source_name`, `source_ref`
- `file` (absolute path to source)
- `context_start`, `primary_start`, `end`
- `output_file` (filename for findings YAML)

### 3. Wait for ALL subagents to complete

**CRITICAL**: Do NOT proceed until every subagent has returned its completion
notification. Files on disk are NOT proof of completion -- agents write YAML then
potentially rewrite during self-validation.

### 4. Validate and mark complete

```bash
progress complete day-016-L1-200.yaml day-016-L201-400.yaml day-016-L401-600.yaml ...
```

For each file: runs `validate-findings.sh` + `validate-quotes.py`. If both pass,
marks the chunk `complete`. If either fails, marks it `failed` and reports errors.

Also updates source-level status (e.g., day-016 becomes `complete` when all its
chunks are complete).

### 5. Repeat from step 1

## Recovery Scenarios

### After compaction (agents lost in flight)

```bash
progress status                  # See how many chunks are dispatched
progress reset dispatched        # Reset all dispatched -> pending
progress next-batch 12 --type daylog   # Re-dispatch
```

### After validation failures

```bash
progress status                  # See FAILED count
# Fix the issue (template, source data, etc.)
progress reset failed            # Reset all failed -> pending
progress next-batch 12           # Re-dispatch
```

### Re-extract specific chunks

```bash
progress reset day-021-L1-200.yaml day-021-L201-400.yaml
progress next-batch 2 --type daylog   # These will be next in queue
```

### Full state check after compaction

After any compaction, the orchestrator agent should:
1. `progress status` -- see current state
2. If dispatched > 0: `progress reset dispatched`
3. Read this runbook to remember the protocol
4. Continue from step 2 of the extraction loop

## Command Reference

| Command | What it does |
|---------|-------------|
| `progress status` | Print summary counts |
| `progress next-batch N [--type daylog\|session]` | Dispatch N chunks |
| `progress complete <file>...` | Validate + mark complete/failed |
| `progress reset dispatched` | Reset all dispatched -> pending |
| `progress reset failed` | Reset all failed -> pending |
| `progress reset <file>...` | Reset specific chunks -> pending |

## Subagent Prompt Construction

After `next-batch`, for each chunk, read the appropriate template:
- Day logs: `xs-requirements/prompts/extract-daylog-chunk.md`
- Sessions: `xs-requirements/prompts/extract-session-chunk.md`

Replace these placeholders with values from the chunk output:
- `{SOURCE_REF}` <- `source_ref`
- `{FILE}` <- `file`
- `{CONTEXT_START}` <- `context_start`
- `{PRIMARY_START}` <- `primary_start`
- `{END}` <- `end`
- `{OUTPUT_FILE}` <- `output_file`
- `{TIMESTAMP}` <- current ISO timestamp

Spawn as Task with `subagent_type=general-purpose`, `model=sonnet`.

**CRITICAL**: Use ABSOLUTE paths in all prompts:
- Output: `/Users/palimondo/Developer/xs/xs-requirements/findings/{output_file}`
- Include `cd /Users/palimondo/Developer/xs &&` prefix for bash commands
