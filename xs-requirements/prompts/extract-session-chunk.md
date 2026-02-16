# Session Chunk Extraction Prompt

TASK: Extract requirements from JSONL session chunk

SOURCE: {SOURCE_REF}
FILE: {FILE}
LINES: {START}-{END}
OUTPUT: xs-requirements/findings/{OUTPUT_FILE}

## Step 1: Extract the chunk

Run this command to get the raw data. It preserves the ORIGINAL file line numbers
by embedding them in the first jq stage:

```bash
jq -c 'input_line_number as $ln | select($ln >= {START} and $ln <= {END}) | {_ln: $ln} + .' {FILE} | \
  jq -r '
    if .type == "user" then
      if (.message.content | type) == "string" then
        "L\(._ln) [USER] " + .message.content[0:500]
      elif (.message.content[0].type? // "") == "tool_result" then
        "L\(._ln) [TOOL_RESULT] " + (.message.content[0].content[0].text // (.message.content[0].content | tostring) // "?")[0:200]
      else
        "L\(._ln) [USER] " + (.message.content | tostring)[0:500]
      end
    elif .type == "assistant" then
      (._ln as $ln | .message.content[] |
        if .type == "text" then "L\($ln) [ASST] " + .text[0:300]
        elif .type == "tool_use" then "L\($ln) [TOOL_USE] " + (.name // "?") + ": " + (.input | tostring)[0:200]
        else empty end
      )
    elif .type == "system" then
      "L\(._ln) [SYSTEM]"
    else
      "L\(._ln) [" + (.type // "unknown") + "]"
    end
  '
```

If the jq command above fails, try this simpler version that handles both string and array content:

```bash
jq -c 'input_line_number as $ln | select($ln >= {START} and $ln <= {END}) | {_ln: $ln} + .' {FILE} | \
  jq -r '"L\(._ln) [\(.type // "?")] " + (
    if .message then
      if (.message.content | type) == "string" then .message.content[0:400]
      else (.message.content[0].text // (.message.content | tostring))[0:400]
      end
    else ""
    end
  )'
```

## Step 2: Read sequentially

Read the extracted output IN ORDER. Do NOT skip ahead or search for keywords.

For each exchange, ask: "Is this about xs tool requirements?"
- xs features, CLI flags, output formatting
- Session replay, console fidelity
- Filtering, searching, range selection
- GitHub Actions log fetching
- Compaction recovery
- JSONL parsing, format handling

## Step 3: Extract findings

CRITICAL — Diarization: Always identify WHO is speaking. The session is a dialogue
between "user" (the human developer) and "agent" (Claude Code). These must be clearly
distinguished because:
- User statements define requirements (highest authority)
- Agent statements provide context, expansions, and sometimes errors
- User corrections of agent mistakes reveal the TRUE requirement

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

CRITICAL — Line numbers: The `line:` field MUST be the JSONL line number from the
source file (as shown in the L-prefixed output from Step 1), NOT a sequence number.

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

## Step 5: Self-validate before returning

After writing the YAML file, read it back and check:

1. **Line numbers in range**: Every `line:` value in threads and findings must be
   between {START} and {END} inclusive. If any are outside this range, they are WRONG.
   Use ripgrep to find the correct line number for the quote:
   ```bash
   # Find the actual line number of a quote in the original JSONL file
   rg -n "some distinctive words from the quote" {FILE} | head -5
   ```
   Then fix the line number in the YAML and re-write.
2. **Speaker field present**: Every event and finding must have `speaker: user` or `speaker: agent`.
3. **Finding types valid**: Only these 5: user_request, user_correction, agent_proposal, agent_error, unresolved.
4. **Quotes are real**: Spot-check that your quotes match text you actually saw in the Step 1 output.
   Do NOT invent or paraphrase quotes — use actual text from the L-prefixed lines.
   If uncertain about a quote, verify with ripgrep:
   ```bash
   rg -n "distinctive phrase" {FILE}
   ```

If validation fails, fix the YAML file and re-write it before returning.

## CRITICAL — Return message

When done, return ONLY a one-line confirmation like:
  "Wrote 5 findings (3 threads) to xs-requirements/findings/{OUTPUT_FILE}"

Do NOT include the findings content, thread summaries, or analysis in your
return message. The orchestrator reads the YAML file directly from disk.
