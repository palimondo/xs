# Day Log Chunk Extraction Prompt

TASK: Extract requirements from day log markdown chunk

SOURCE: {SOURCE_REF}
FILE: {FILE}
LINES: {START}-{END}
OUTPUT: xs-requirements/findings/{OUTPUT_FILE}

## Step 1: Extract the chunk

Run this command to get the raw text WITH LINE NUMBERS:

```bash
awk 'NR>={START} && NR<={END} {printf "L%d %s\n", NR, $0}' {FILE}
```

The output will look like:
```
L{START} first line of chunk
L{START+1} second line
...
```

Use the L-prefixed numbers as your line references. They are the ABSOLUTE line numbers
in the day log file.

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

CRITICAL — Diarization: Day logs capture Claude Code console output which shows a
dialogue between "user" (lines starting with ">") and "agent" (Claude Code, lines
starting with "⏺" or indented under it). Always identify WHO is speaking:
- User statements ("> ...") define requirements (highest authority)
- Agent statements ("⏺ ...") provide context, expansions, and sometimes errors
- User corrections of agent mistakes reveal the TRUE requirement

In day log format:
- `> text` = USER speaking
- `⏺ text` = AGENT (Claude Code) speaking
- `⎿ text` = Tool output (context, not a speaker)
- `✻ Thinking…` = AGENT internal reasoning

For each relevant discussion:
1. Assign a thread ID (T001, T002...) when a topic FIRST appears
2. Track when topics are REVISITED (same thread ID)
3. Note RESOLUTION or ABANDONMENT
4. Every event and finding MUST have a `speaker: user` or `speaker: agent` field
5. Tag findings by type — ONLY these 5 types are allowed:
   - **user_request**: User explicitly asked for something (speaker: user)
   - **user_correction**: User rejected or corrected something (speaker: user)
   - **agent_proposal**: Agent suggested an approach (speaker: agent)
   - **agent_error**: Agent got something wrong (speaker: agent)
   - **unresolved**: Discussed but not concluded (either speaker)
   Do NOT invent other types like "solution", "observation", "identified_format", etc.

CRITICAL — Line numbers: The `line:` field in events and findings MUST be the
ABSOLUTE line number in the day log file, NOT relative to the chunk start.
Lines in this chunk range from {START} to {END}. All line numbers must fall in that range.

CRITICAL — xs PRECURSOR tools ARE xs-relevant. Always extract findings about:
- `reconstruct.jq` — the jq script that preceded xs (THIS IS XS WORK)
- `fetch_logs.sh` / `fetch_logs.py` — GitHub Actions log retrieval
- Any discussion of session JSONL parsing, console output formatting, or log reconstruction
- Formatting requirements (symbols, spacing, truncation) from precursor tools define xs requirements
Do NOT dismiss reconstruct.jq work as "not about xs" — it IS the same tool lineage.

## Step 4: Write findings YAML

Write the output file. Every event MUST include `speaker: user` or `speaker: agent`.

```yaml
source: {SOURCE_REF}
extracted_by: haiku
timestamp: {TIMESTAMP}

threads:
  - id: T001
    topic: "description"
    status: resolved  # or: open, abandoned
    events:
      - line: NN
        speaker: user  # REQUIRED: user or agent
        type: introduced
        quote: "actual text"
      - line: NN
        speaker: agent
        type: refined
        quote: "actual text"

findings:
  - id: F001
    thread: T001
    line: NN
    speaker: user  # REQUIRED: user or agent
    type: user_request
    quote: "actual text"
    context: "why this matters"

notes:
  - "observations"
```

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
DO NOT add extra fields like `applies_to_epic`, `epic_hint`, `key_requirements`,
or `epics_to_consider`. Stick to the exact YAML schema shown above.

## CRITICAL — Return message

When done, return ONLY a one-line confirmation like:
  "Wrote 5 findings (3 threads) to xs-requirements/findings/{OUTPUT_FILE}"

Do NOT include the findings content, thread summaries, or analysis in your
return message. The orchestrator reads the YAML file directly from disk.
