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

Day logs are reconstructed Claude Code console output. They use these markers:
- `> text` — USER speaking (the human developer)
- `⏺ text` — AGENT (Claude Code) response or tool call
- `⎿ text` — Tool output/result
- `✻ Thinking…` — Agent internal reasoning

Read the extracted text IN ORDER. Do NOT skip ahead or search for keywords.

For each section, ask: "Is this a REQUIREMENT for xs / explore_session / reconstruct.jq?"

### What IS relevant (extract these):
- **Feature requests**: CLI flags, display modes (full, truncated, compact), filtering
  options (by message type, entity, tool), range selection (line ranges, event indices)
- **Output format requirements**: symbols (⏺ > ⎿ ✻), spacing, indentation, truncation
  rules, output line width
- **Design decisions**: how to parse JSONL, what fields matter, format version handling
  (1.x vs 2.x), unified timeline structure
- **User corrections**: agent implemented X, user said "no, it should be Y"
- **Workflow requirements**: console fidelity for LLM consumption, compaction recovery,
  GitHub Actions log fetching
- **Behavioral requirements**: what happens with malformed input, large files, missing fields
- **Format examples**: when tool results show reconstructed output with specific formatting,
  that IS a formatting requirement

### What is NOT relevant (skip these):
- Debugging tool invocations (getting jq syntax right, fixing Python imports, pip installs)
- Agent reading files or exploring the codebase to understand structure
- Implementation mechanics (how to code something, not what it should do)
- General BookMinder work unrelated to session replay tools
- Git operations, CI setup, test infrastructure setup
- **Individual code snippets**: If the agent writes/debugs code, capture WHAT the code
  does (the requirement: "tool results must be indented with 2sp + ⎿ + content"), NOT
  HOW it does it (each jq conditional, each sed command, each code line). One finding
  per requirement, not one finding per line of code.

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

BUT: discussions about HOW to implement these tools (debugging jq syntax, fixing script
errors, getting commands to run) are NOT requirements. Only extract WHAT the tool should
do, not how the developer struggled to make it work.

## Step 4: Write findings YAML

Write the output file. Every event MUST include `speaker: user` or `speaker: agent`.

```yaml
source: {SOURCE_REF}
extracted_by: sonnet
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
extracted_by: sonnet
timestamp: {TIMESTAMP}

threads: []
findings: []
notes:
  - "No xs-relevant requirements found in this chunk"
```

DO NOT pre-filter by epic. Extract everything. Orchestrator assigns epics later.
DO NOT add extra fields like `applies_to_epic`, `epic_hint`, `key_requirements`,
or `epics_to_consider`. Stick to the exact YAML schema shown above.

## Step 4b: Review and revise

Before validation, re-examine your findings against the source material still in memory:

1. **Remove noise**: For each finding, ask: "Is this about what xs SHOULD DO, or about
   debugging/implementation mechanics?" Remove findings about getting tools to work rather
   than defining requirements.

2. **Check completeness**: Scan the source once more. Did you miss any user requests,
   corrections, or design decisions? Add them.

3. **Check granularity**: A single conversation about one topic should be one thread
   with one or two findings, not a finding per line. If you have 5+ findings about the
   same narrow topic, consolidate.

4. **Code vs requirements**: If you created findings for individual code lines, jq
   conditionals, or implementation patterns, DELETE them. Replace with a single finding
   stating the REQUIREMENT the code satisfies. Example: 10 findings about jq priority
   mapping code → 1 finding: "Priority mapping: high→P0, medium→P1, low→P2".

Rewrite the YAML file with your revisions.

## Step 5: Self-validate before returning

After writing the YAML file, validate it:

1. **Run validate-quotes.py** to check line numbers, quotes, AND speaker fields:
   ```bash
   ~/.local/bin/uv run --with pyyaml python3 xs-requirements/validate-quotes.py \
     xs-requirements/findings/{OUTPUT_FILE} {FILE}
   ```
   The validator checks THREE things:
   - Quote phrases found at claimed line numbers
   - Line numbers within primary range [{PRIMARY_START}, {END}]
   - Every event and finding has `speaker: user` or `speaker: agent`

   **If ANY errors are reported (exit code > 0), you MUST fix and re-write the file.**
   - For wrong line numbers: use the actual lines reported by the validator
   - For MISSING speakers: add `speaker: user` or `speaker: agent` to every
     thread event and every finding that lacks it. Determine speaker from context:
     `[USER]` lines → `speaker: user`, `[ASST]`/`[TOOL_USE]` lines → `speaker: agent`,
     `> text` in day logs → `speaker: user`, `⏺ text` → `speaker: agent`
   - After fixing, re-run the validator to confirm 0 errors

2. **Quotes are real**: If validate-quotes.py reports MISSING, verify with ripgrep:
   ```bash
   rg -nF "distinctive phrase" {FILE}
   ```

If validation fails, fix the YAML file, re-write it, and re-run the validator.
Do NOT return until the validator reports 0 errors.

## CRITICAL — Return message

When done, return ONLY a one-line confirmation like:
  "Wrote 5 findings (3 threads) to xs-requirements/findings/{OUTPUT_FILE}"

Do NOT include the findings content, thread summaries, or analysis in your
return message. The orchestrator reads the YAML file directly from disk.
