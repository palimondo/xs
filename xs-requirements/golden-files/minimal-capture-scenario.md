# Minimal Capture Scenario

Minimal sequence of prompts to trigger every known message/event type in Claude Code.
Designed to be driven via tmux by another Claude session.

## Version

- Scenario version: 1
- Target CC version: 2.1.62+
- Last run: (pending)

## Output Files

All outputs use naming convention: `golden-v{CC_VERSION}-{YYYY-MM-DD}.{ext}`

- `.jsonl` — Raw session JSONL from `~/.claude/projects/`
- `.txt` — `/export` to file (truncated view, plain text)
- `-full.txt` — Ctrl+E full transcript captured via tmux scrollback
- `-full-ansi.txt` — Same with ANSI color codes preserved (for future use)

## Setup (local commands, no API calls)

```
! echo "hello world" > test.txt
! echo -e "line 1\nline 2\nline 3\nfoo bar\nbaz qux" > data.txt
! mkdir -p subdir && echo "nested content" > subdir/nested.txt
```

These use `!` prefix (local bash execution) — they appear in JSONL as system events
but don't consume API calls. They set up files for subsequent tool triggers.

## Prompts (17 steps)

### Phase 1: Basic messages + file tools

**P01** — Simple text response
```
What is 2 + 2?
```
Triggers: user(string), assistant(thinking+text), progress, system(stop_hook_summary)

**P02** — Read tool
```
Read the file test.txt
```
Triggers: Read tool_use + tool_result

**P03** — Write tool
```
Create a file called output.txt containing exactly "test output line 1"
```
Triggers: Write tool_use + tool_result, file-history-snapshot

**P04** — Edit tool
```
Edit test.txt to change "hello" to "greetings"
```
Triggers: Edit tool_use + tool_result(structuredPatch)

**P05** — MultiEdit tool
```
Make two edits: in test.txt change "greetings" to "howdy", and in output.txt change "test" to "final"
```
Triggers: MultiEdit tool_use + tool_result(edits array)

### Phase 2: Search + shell tools

**P06** — Bash tool
```
Run: echo "bash test" && cat test.txt && ls -la subdir/
```
Triggers: Bash tool_use + tool_result(stdout, stderr)

**P07** — Grep tool
```
Search for the word "howdy" in all files in the current directory
```
Triggers: Grep tool_use + tool_result

**P08** — Glob tool
```
Find all .txt files recursively in this directory
```
Triggers: Glob tool_use + tool_result(filenames)

**P09** — LS tool
```
List the contents of the current directory using the LS tool
```
Triggers: LS tool_use + tool_result

### Phase 3: Web tools

**P10** — WebSearch tool
```
Search the web for "Claude Code session transcript format"
```
Triggers: WebSearch tool_use + tool_result(results)

**P11** — WebFetch tool
```
Fetch https://httpbin.org/json and tell me what it contains
```
Triggers: WebFetch tool_use + tool_result(url, bytes)

### Phase 4: Advanced tools

**P12** — TodoWrite tool
```
Create a todo list with two items: "Review schema" (pending) and "Extract fixtures" (completed)
```
Triggers: TodoWrite tool_use + tool_result(oldTodos, newTodos), todos field

**P13** — Task tool (subagent)
```
Use the Task tool to spawn a subagent that reads data.txt and reports exactly how many lines it contains. The subagent should use the Read tool.
```
Triggers: Task tool_use + tool_result(agentId, totalTokens), isSidechain,
agent-{id}.jsonl separate file, agent_id field (2.x)

**P14** — AskUserQuestion tool
```
I need help choosing. Please use the AskUserQuestion tool to ask me whether I prefer "Option A: Simple approach" or "Option B: Comprehensive approach" for this project.
```
Triggers: AskUserQuestion tool_use + tool_result
Note: In --dangerously-skip-permissions mode, this may auto-select. Observe behavior.

### Phase 5: Special patterns

**P15** — @file reference
```
@data.txt How many lines does this file have?
```
Triggers: @file expansion in user message, possibly Read tool

**P16** — User interruption
```
Write a very detailed 2000-word essay about the history of computer science starting from Charles Babbage
```
Then press **Escape** after ~5 seconds.
Triggers: truncated assistant response, user "[Request interrupted by user]"

**P17** — /compact
```
/compact
```
Triggers: summary event, system(compact_boundary), compactMetadata,
isCompactSummary on next user entry

## Capture Sequence

**IMPORTANT**: Export BEFORE /compact! The /compact wipes visible history from /export.

After all prompts up to P16 complete (before /compact):

1. **Export truncated view**: `/export golden-v{ver}-{date}.txt` (relative path only!)
2. **Run P17** (/compact)
3. **Enter expanded view**: Press Ctrl+O (shows compact summary), then view full session
4. **Capture full view**: `tmux capture-pane -t capture -p -S -5000` → save as `-full.txt`
5. **Capture with ANSI**: `tmux capture-pane -t capture -e -p -S -5000` → save as `-full-ansi.txt`
6. **Export post-compact**: `/export golden-v{ver}-{date}-post-compact.txt`
7. **Copy JSONL**: From `~/.claude/projects/{encoded-path}/{session-id}.jsonl`
8. **Check for agent files**: `ls ~/.claude/projects/{encoded-path}/agent-*.jsonl`

### Capture Gotchas

- `/export /absolute/path` fails — CC prepends CWD, creating double path. Use relative filenames only.
- Ctrl+E doesn't work from the normal prompt via tmux. Use Ctrl+O first to enter history view.
- After /compact, `/export` only captures the post-compact view, not the full session.
- The full pre-compact session IS accessible via Ctrl+O → expanded view → tmux scrollback capture.

## Run 1 Results (v2.1.62, 2026-02-27)

### Event Types Actually Captured

| Event type | Count | Notes |
|---|---|---|
| user | 48 | Includes string, tool_result, isMeta, isCompactSummary |
| assistant | 39 | thinking + text + tool_use |
| progress | 32 | hook_progress (after each turn) |
| file-history-snapshot | 24 | More than expected (file changes) |
| system | 18 | 17 stop_hook_summary + 1 compact_boundary |

**NOT triggered**: summary (separate type), local_command (! prefix didn't work via tmux)

### Tools Actually Used

| Tool | Count | Notes |
|---|---|---|
| Bash | 4 | P06 + Setup + P09 (LS substitute) + extra |
| Edit | 3 | P04 (1 edit) + P05 (2 edits, no MultiEdit) |
| Read | 2 | P02 + P15 |
| TaskCreate | 2 | P12 (replaced TodoWrite in 2.x) |
| Write | 1 | P03 |
| WebSearch | 1 | P10 |
| WebFetch | 1 | P11 |
| TaskUpdate | 1 | P12 (mark task complete) |
| Task | 1 | P13 |
| Grep | 1 | P07 |
| Glob | 1 | P08 |
| AskUserQuestion | 1 | P14 |

### Tool Substitutions in 2.x

| Requested | CC Used Instead | Notes |
|---|---|---|
| MultiEdit (P05) | 2x Edit | CC made two separate Edit calls |
| LS (P09) | Bash(ls -la) | No dedicated LS tool used |
| TodoWrite (P12) | TaskCreate + TaskUpdate | New 2.x todo system |

### Special Patterns Captured

| Pattern | Captured? | Notes |
|---|---|---|
| isMeta (caveats) | Yes (3) | Auto-generated system messages |
| isCompactSummary | Yes (1) | After /compact |
| interruption | Yes (2) | P16 Escape interrupt |
| @file reference | Yes | P15 @data.txt expansion |
| compact_boundary | Yes (1) | P17 /compact |
| thinking blocks | Yes (3) | Fewer than expected |
| file-history-snapshot | Yes (24) | More than expected |
| progress (hook) | Yes (32) | New 2.x event type |
| stop_hook_summary | Yes (17) | New 2.x system subtype |

### Output Files

| File | Lines | Size | Description |
|---|---|---|---|
| golden-v2.1.62-2026-02-27.jsonl | 161 | 134K | Full JSONL (all events) |
| golden-v2.1.62-2026-02-27-full.txt | 442 | 21K | Full transcript (Ctrl+O expanded view) |
| golden-v2.1.62-2026-02-27-full-ansi.txt | 442 | 31K | Same with ANSI color codes |
| golden-v2.1.62-2026-02-27-post-compact.txt | 26 | 1.8K | Post-compact /export only |

### Scenario Improvements for Run 2

1. **Export BEFORE /compact** — add explicit export step between P16 and P17
2. **Force MultiEdit** — use a prompt that explicitly requests "use the MultiEdit tool"
3. **Force LS tool** — more specific: "use the LS tool, not bash ls"
4. **Force TodoWrite** — "use the TodoWrite tool" (may not exist in 2.x)
5. **Local commands** — `!` prefix doesn't work via tmux (gets escaped). Use different approach.
6. **Increase tmux scrollback** — `tmux set -t capture history-limit 10000` before session

## Expected Tools Covered

| Tool | Prompt | Run 1 Status |
|---|---|---|
| Read | P02 | Captured |
| Write | P03 | Captured |
| Edit | P04 | Captured |
| MultiEdit | P05 | NOT triggered (used 2x Edit) |
| Bash | P06 | Captured |
| Grep | P07 | Captured |
| Glob | P08 | Captured |
| LS | P09 | NOT triggered (used Bash) |
| WebSearch | P10 | Captured |
| WebFetch | P11 | Captured |
| TodoWrite | P12 | NOT triggered (used TaskCreate) |
| Task | P13 | Captured |
| AskUserQuestion | P14 | Captured |
| TaskCreate | — | NEW: captured (2.x todo replacement) |
| TaskUpdate | — | NEW: captured (2.x todo replacement) |

## Not Covered (requires special setup)

- **MultiEdit** — CC used 2x Edit instead; may need explicit instruction
- **LS** — CC used Bash(ls) instead; may not exist as separate tool in 2.x
- **TodoWrite** — Replaced by TaskCreate/TaskUpdate in 2.x
- **Skill** — needs /commit with uncommitted changes
- **ExitPlanMode** — needs multi-step plan mode interaction
- **NotebookEdit** — needs Python/Jupyter environment
- **MCP tools** — needs MCP server configured
- **queue-operation** — requires prompt queuing
- **isApiErrorMessage** — requires API error (rate limit)
- **summary** (separate event type) — /compact didn't produce one; may be 1.x only
- **local_command** (! prefix) — tmux escapes !, needs workaround
