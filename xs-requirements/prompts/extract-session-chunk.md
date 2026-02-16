# Session Chunk Extraction Prompt

TASK: Extract requirements from JSONL session chunk

SOURCE: {SOURCE_REF}
FILE: {FILE}
LINES: {START}-{END}
OUTPUT: xs-requirements/findings/{OUTPUT_FILE}

## Step 1: Extract the chunk

Run this command to get the raw data:

```bash
jq -c 'select(input_line_number >= {START} and input_line_number <= {END})' {FILE} | \
  jq -r '
    if .type == "user" then
      "L\(input_line_number) [USER] " + (.message.content[0].text // (.message.content | tostring) // "?")[0:500]
    elif .type == "assistant" then
      "L\(input_line_number) [ASST] " + (.message.content[] | select(.type == "text") | .text[0:300] // "?")
    elif .type == "tool_use" then
      "L\(input_line_number) [TOOL_USE] " + (.name // "?") + ": " + (.input | tostring)[0:200]
    elif .type == "tool_result" then
      "L\(input_line_number) [TOOL_RESULT] " + (.content[0].text // "?")[0:200]
    else
      "L\(input_line_number) [" + (.type // "unknown") + "]"
    end
  '
```

If the jq command above fails, try this simpler version:

```bash
jq -c 'select(input_line_number >= {START} and input_line_number <= {END})' {FILE} | \
  jq -r '"L\(input_line_number) [\(.type // "?")] " + (
    if .message then (.message.content[0].text // (.message.content | tostring))[0:400]
    else (.content[0].text // .name // (.input | tostring) // "")[0:400]
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

For each relevant discussion:
1. Assign a thread ID (T001, T002...) when a topic FIRST appears
2. Track when topics are REVISITED (same thread ID)
3. Note RESOLUTION or ABANDONMENT
4. Tag findings by type:
   - **user_request**: User explicitly asked for something
   - **user_correction**: User rejected or corrected something
   - **claude_misunderstanding**: Claude got something wrong
   - **unresolved**: Discussed but not concluded

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
