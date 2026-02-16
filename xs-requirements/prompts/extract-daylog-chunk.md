# Day Log Chunk Extraction Prompt

TASK: Extract requirements from day log markdown chunk

SOURCE: {SOURCE_REF}
FILE: {FILE}
LINES: {START}-{END}
OUTPUT: xs-requirements/findings/{OUTPUT_FILE}

## Step 1: Extract the chunk

Run this command to get the raw text:

```bash
sed -n '{START},{END}p' {FILE}
```

## Step 2: Read sequentially

Day logs are markdown files capturing full Claude Code session output. They contain:
- User prompts (often prefixed with "Human:" or appearing after headers)
- Claude responses (code, explanations, tool calls)
- Session output (terminal output, file contents, test results)
- Commentary and narrative between sessions

Read the extracted text IN ORDER. Do NOT skip ahead or search for keywords.

For each section, ask: "Is this about xs tool requirements?"
Look for discussions about:
- `explore_session.py`, `xs`, `reconstruct.jq` — the tools being recreated
- Session replay, console output formatting
- JSONL parsing, transcript handling
- Filtering by message type, entity, tool
- Range selection (line ranges, event indices)
- Display modes (full, truncated, compact)
- GitHub Actions log fetching
- Compaction recovery
- CLI flags and interface design
- Output symbols (circle, bracket, etc.)

## Step 3: Extract findings

For each relevant discussion:
1. Assign a thread ID (T001, T002...) when a topic FIRST appears
2. Track when topics are REVISITED (same thread ID)
3. Note RESOLUTION or ABANDONMENT
4. Tag findings by type:
   - **user_request**: User explicitly asked for something
   - **user_correction**: User rejected or corrected something
   - **claude_misunderstanding**: Claude got something wrong
   - **unresolved**: Discussed but not concluded

Note: Day logs often contain BOTH the user's instructions AND Claude's implementation.
Focus on the USER's stated requirements and corrections, not Claude's implementation choices.

## Step 4: Write findings YAML

Write the output file following the findings format in CLAUDE.md.
If NO xs-relevant findings exist in this chunk, write a minimal file:

```yaml
source: {SOURCE_REF}
extracted_by: haiku
timestamp: {TIMESTAMP}

threads: []
findings: []
notes:
  - "No xs-relevant requirements found in this chunk"
```

DO NOT pre-filter by epic. Extract everything. Orchestrator assigns epics later.
