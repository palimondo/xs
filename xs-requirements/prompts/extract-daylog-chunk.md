# Day Log Chunk Extraction Prompt

TASK: Extract requirements from day log markdown chunk

SOURCE: {SOURCE_REF}
FILE: {FILE}
CONTEXT: {CONTEXT_START}-{END}
PRIMARY: {PRIMARY_START}-{END}
OUTPUT: xs-requirements/findings/{OUTPUT_FILE}

## Step 1: Extract the chunk

Run this command to get the raw text WITH LINE NUMBERS. It reads from CONTEXT_START
to include overlap context:

```bash
awk 'NR>={CONTEXT_START} && NR<={END} {printf "L%d %s\n", NR, $0}' {FILE}
```

The output will look like:
```
L{CONTEXT_START} first line (context zone if CONTEXT_START < PRIMARY_START)
...
L{PRIMARY_START} first line of primary range
...
L{END} last line
```

Use the L-prefixed numbers as your line references. They are the ABSOLUTE line numbers
in the day log file.

## Step 1b: Context vs primary range

Lines from L{CONTEXT_START} to L{PRIMARY_START}-1 are **CONTEXT ONLY**:
- Read them to understand what was being discussed at the end of the previous chunk
- Do NOT create findings or thread events for lines in the context-only zone
- They help you understand threads that span chunk boundaries

Lines from L{PRIMARY_START} to L{END} are the **PRIMARY RANGE**:
- Extract findings ONLY from these lines
- All `line:` values in your YAML must be in [{PRIMARY_START}, {END}]
- If a thread started in the context zone, note it as a continuation

If CONTEXT_START == PRIMARY_START, there is no overlap (first chunk). Skip this step.

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
dialogue between "user" and "agent" (Claude Code). Always identify WHO is speaking:
- User statements define requirements (highest authority)
- Agent statements provide context, expansions, and sometimes errors
- User corrections of agent mistakes reveal the TRUE requirement

In day log format, look for these prefixes:
- `> text` = USER speaking (the human developer)
- `⏺ text` (filled circle) = AGENT (Claude Code) speaking
- `⎿ text` (corner bracket) = Tool output/result (context, not a speaker)
- `✻ Thinking…` (asterisk) = AGENT internal reasoning

CRITICAL — Meta-layer confusion: Many day log sections capture an agent (A) working
on reconstruct.jq or explore_session.py, which RECONSTRUCTS console output from ANOTHER
agent's (B) session. This creates nested layers where tool results contain reconstructed
output that ALSO uses `⏺`, `>`, and `⎿` symbols.

Watch for these signs of reconstructed/expected output being compared:
- Commands like `head -N expected_output.md` or `jq -rf reconstruct.jq` — their output
  contains agent (B)'s reconstructed words, NOT agent (A) speaking
- Side-by-side comparisons of "expected" vs "actual" output
- Agent (A) discussing how to add `⏺` prefix or `⎿` formatting to its script output

When tool results show reconstructed output, attribute findings about the FORMAT
(symbols, spacing, indentation) as formatting requirements, and note in `context:`
that this is reconstructed output revealing the target format.

For each relevant discussion:
1. Assign a thread ID (T001, T002...) when a topic FIRST appears
2. Track when topics are REVISITED (same thread ID)
3. Note RESOLUTION or ABANDONMENT
4. Every event and finding MUST have a `speaker: user` or `speaker: agent` field
5. Tag findings by type. Preferred types:
   - **user_request**: User explicitly asked for something (speaker: user)
   - **user_correction**: User rejected or corrected something (speaker: user)
   - **agent_proposal**: Agent suggested an approach (speaker: agent)
   - **agent_error**: Agent got something wrong (speaker: agent)
   - **unresolved**: Discussed but not concluded (either speaker)
   You may use other descriptive types if these 5 don't fit, but prefer them.

CRITICAL — Line numbers: The `line:` field in events and findings MUST be the
ABSOLUTE line number in the day log file, NOT relative to the chunk start.
All line numbers must be in the PRIMARY range [{PRIMARY_START}, {END}].

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

After writing the YAML file, validate it:

1. **Run validate-quotes.py** to check line numbers and quotes:
   ```bash
   ~/.local/bin/uv run --with pyyaml python3 xs-requirements/validate-quotes.py \
     xs-requirements/findings/{OUTPUT_FILE} {FILE}
   ```
   If any errors are reported, fix the line numbers in the YAML. Use the actual
   line numbers reported by the validator and re-write the file.

2. **Line numbers in PRIMARY range**: Every `line:` value must be between
   {PRIMARY_START} and {END} inclusive. Lines in the context-only zone
   [{CONTEXT_START}, {PRIMARY_START}-1] must NOT appear as finding line numbers.

3. **Speaker field present**: Every event and finding must have `speaker: user` or `speaker: agent`.

4. **Finding types valid**: Only these 5: user_request, user_correction, agent_proposal, agent_error, unresolved.

5. **Quotes are real**: If validate-quotes.py reports MISSING, verify with ripgrep:
   ```bash
   rg -nF "distinctive phrase" {FILE}
   ```

If validation fails, fix the YAML file and re-write it before returning.

## CRITICAL — Return message

When done, return ONLY a one-line confirmation like:
  "Wrote 5 findings (3 threads) to xs-requirements/findings/{OUTPUT_FILE}"

Do NOT include the findings content, thread summaries, or analysis in your
return message. The orchestrator reads the YAML file directly from disk.
