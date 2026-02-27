# 2.x Golden File Capture Scenario

Run this scenario in a current Claude Code session to generate a JSONL transcript
covering all message types. After completing all steps, use `/export` to save the
session transcript.

## Prerequisites

- Current Claude Code (2.x)
- A scratch project directory with at least one file
- The session should be run in a git repo (to capture `gitBranch` field)

## Scenario Steps

### Phase 1: Basic Message Types

**Step 1 — Simple text response** (triggers: `thinking`, `text` content blocks)
```
What is 2 + 2?
```
Expected JSONL: user(string content) → assistant(thinking + text)

**Step 2 — Multi-turn conversation** (triggers: `parentUuid` threading)
```
And what is that times 3?
```
Expected JSONL: user with parentUuid → assistant with parentUuid

### Phase 2: File Operations

**Step 3 — Read a file** (triggers: `Read` tool_use + tool_result)
```
Read the file README.md
```
Expected JSONL: assistant(tool_use:Read) → user(tool_result with file content)

**Step 4 — Write a new file** (triggers: `Write` tool_use + tool_result)
```
Create a file called scratch-capture-test.txt with the text "hello golden files"
```
Expected JSONL: assistant(tool_use:Write) → user(tool_result)

**Step 5 — Edit a file** (triggers: `Edit` tool_use + tool_result)
```
Edit scratch-capture-test.txt to change "hello" to "greetings"
```
Expected JSONL: assistant(tool_use:Edit) → user(tool_result with structuredPatch)

**Step 6 — Glob search** (triggers: `Glob` tool_use + tool_result)
```
Find all .md files in this directory
```
Expected JSONL: assistant(tool_use:Glob) → user(tool_result with filenames)

**Step 7 — Grep search** (triggers: `Grep` tool_use + tool_result)
```
Search for the word "golden" in all files
```
Expected JSONL: assistant(tool_use:Grep) → user(tool_result)

### Phase 3: Shell Execution

**Step 8 — Bash command** (triggers: `Bash` tool_use + tool_result with stdout/stderr)
```
Run: echo "capture test" && ls -la scratch-capture-test.txt
```
Expected JSONL: assistant(tool_use:Bash) → user(tool_result with stdout, stderr, interrupted)

**Step 9 — Bash with error** (triggers: tool_result with non-zero exit, stderr)
```
Run: cat nonexistent-file-12345.txt
```
Expected JSONL: tool_result with stderr content

### Phase 4: Web Tools

**Step 10 — Web search** (triggers: `WebSearch` tool_use + tool_result)
```
Search the web for "Claude Code JSONL format"
```
Expected JSONL: assistant(tool_use:WebSearch) → user(tool_result with results)

**Step 11 — Web fetch** (triggers: `WebFetch` tool_use + tool_result)
```
Fetch https://docs.anthropic.com/en/docs/about-claude.md and tell me the first paragraph
```
Expected JSONL: assistant(tool_use:WebFetch) → user(tool_result)

### Phase 5: Planning & Tasks

**Step 12 — Todo/task management** (triggers: `TodoWrite`/`TodoRead` + `todos` field)
```
Create a todo list with two items: "Review schema" and "Write tests"
```
Expected JSONL: assistant(tool_use:TodoWrite) → user(tool_result with oldTodos/newTodos)

**Step 13 — Plan mode** (triggers: `ExitPlanMode` tool, plan mode flow)
```
/plan How should I restructure this project?
```
Then when plan is presented:
```
Looks good, go ahead
```
Expected JSONL: plan mode entry/exit sequence

### Phase 6: Advanced Features

**Step 14 — Subagent/Task tool** (triggers: `Task` tool_use, `isSidechain`, agent fields)
```
Use a subagent to count the number of lines in scratch-capture-test.txt
```
Expected JSONL: assistant(tool_use:Task) → user(tool_result with agentId, status, totalTokens)
Also: possible `agent_id`, `agent_transcript_path` fields (2.x)

**Step 15 — MultiEdit** (triggers: `MultiEdit` tool_use + tool_result)
```
Make two edits to scratch-capture-test.txt: add a blank line at the end and change "greetings" to "howdy"
```
Expected JSONL: assistant(tool_use:MultiEdit) → user(tool_result with edits array)

**Step 16 — Notebook operations** (triggers: `NotebookEdit`/`NotebookRead` if applicable)
```
Create a Jupyter notebook called scratch-test.ipynb with one cell that prints "hello"
```
Expected JSONL: assistant(tool_use:NotebookEdit) → user(tool_result)
*Skip if not in a Python project context.*

**Step 17 — Skill invocation** (triggers: `Skill` tool_use — 2.x-only)
```
/commit
```
Then cancel/decline the commit.
Expected JSONL: Skill tool invocation in transcript

**Step 18 — LS tool** (triggers: `LS` tool_use + tool_result)
```
List the contents of the current directory using LS
```
Expected JSONL: assistant(tool_use:LS) → user(tool_result)

### Phase 7: Special Events

**Step 19 — User interruption** (triggers: `[Request interrupted by user]`)
```
Write a very long essay about the history of computing
```
Interrupt with Escape after a few seconds.
Expected JSONL: truncated assistant message → user "[Request interrupted by user]"

**Step 20 — @file reference** (triggers: `@file` pattern in user text)
```
Summarize @scratch-capture-test.txt
```
Expected JSONL: user message with @file reference, possibly expanded content

**Step 21 — Image/screenshot** (triggers: `image` content block)
Take a screenshot and paste it, or:
```
Read the file scratch-capture-test.txt and show me a screenshot of it
```
*This is hard to trigger synthetically. If you have a PNG file, ask Claude to read it.*

**Step 22 — Compact** (triggers: `summary` event, `system` with `compact_boundary` subtype)
```
/compact
```
Expected JSONL: system(subtype:compact_boundary) + summary event

**Step 23 — System hook events** (triggers: `system` event with hook info)
*Only if hooks are configured.* These appear automatically when PreToolUse hooks run.
Expected JSONL: system event with `toolUseID`, `level`, hook validation content

### Phase 8: Cleanup & Export

**Step 24 — Delete test files**
```
Delete scratch-capture-test.txt and scratch-test.ipynb if they exist
```

**Step 25 — Export**
```
/export
```
Save the exported JSONL file to `xs-requirements/golden-files/2x/capture-session.jsonl`.

---

## Coverage Checklist

### Event Types
- [ ] `user` — string content (Step 1)
- [ ] `user` — array content with tool_result (Steps 3-18)
- [ ] `user` — with `isMeta: true` (caveat message, auto-generated)
- [ ] `user` — with `isCompactSummary` (Step 22)
- [ ] `user` — `[Request interrupted by user]` (Step 19)
- [ ] `assistant` — text + thinking (Step 1)
- [ ] `assistant` — tool_use blocks (Steps 3-18)
- [ ] `assistant` — `isApiErrorMessage` (may not trigger)
- [ ] `system` — no subtype (hook events, Step 23)
- [ ] `system` — `subtype: compact_boundary` (Step 22)
- [ ] `system` — `subtype: local_command` (Step 13, /plan)
- [ ] `summary` — with summary text + leafUuid (Step 22)
- [ ] `file-history-snapshot` — (may auto-generate during edits)
- [ ] `queue-operation` — 2.x-only (may not trigger in single session)

### Content Block Types
- [ ] `text` (Steps 1-2)
- [ ] `thinking` (Steps 1+)
- [ ] `tool_use` (Steps 3-18)
- [ ] `tool_result` (Steps 3-18)
- [ ] `image` (Step 21)

### Tool Names
- [ ] `Bash` (Steps 8-9)
- [ ] `Read` (Step 3)
- [ ] `Write` (Step 4)
- [ ] `Edit` (Step 5)
- [ ] `MultiEdit` (Step 15)
- [ ] `Glob` (Step 6)
- [ ] `Grep` (Step 7)
- [ ] `LS` (Step 18)
- [ ] `WebSearch` (Step 10)
- [ ] `WebFetch` (Step 11)
- [ ] `TodoWrite` (Step 12)
- [ ] `TodoRead` (Step 12, if triggered)
- [ ] `Task` (Step 14)
- [ ] `ExitPlanMode` (Step 13)
- [ ] `Skill` (Step 17)
- [ ] `NotebookEdit` (Step 16)

### Special Patterns
- [ ] `isSidechain: true` (Step 14)
- [ ] `@file` reference (Step 20)
- [ ] `<bash-input>` tag (auto-generated for some Bash inputs)
- [ ] `<system-reminder>` tag (auto-generated)
- [ ] Slash command (Steps 13, 17, 22)
- [ ] Content polymorphism: string vs array (Steps 1 vs 3+)
- [ ] `toolUseResult` sub-fields: stdout/stderr (Step 8), structuredPatch (Step 5)

### 2.x-Only Fields
- [ ] `agent_id` (Step 14)
- [ ] `agent_transcript_path` (Step 14)
- [ ] `thinkingMetadata` (auto-generated)
- [ ] `todos` (Step 12)
- [ ] `modelUsage` (auto-generated on some entries)

---

## Notes

- Some events are auto-generated and don't need explicit steps (e.g., `isMeta` caveat
  messages appear when Claude adds caveats to tool results).
- `queue-operation` may require queuing prompts via `--prompt` flag or the queue feature.
- `file-history-snapshot` appears to be auto-generated during file edit operations.
- `isApiErrorMessage` only appears on API errors (rate limits, server errors) — hard
  to trigger intentionally.
- The scenario assumes a fresh session. If resuming, some types may already be present.
- Steps 10-11 (web tools) may require network access and appropriate permissions.
