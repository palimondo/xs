# BUG-003: xs doesn't support agent-*.jsonl files (Feature Gap)

## Problem

The old xs implementation only supports main session JSONL files. Claude Code 2.x (v1.0.60+) stores subagent transcripts in separate `agent-{agentId}.jsonl` files.

## Evidence

```bash
$ xs -S 'The user story part is the tricky bit' 84db
No matches found for 'The user story part is the tricky bit'

$ rg "The user story part is the tricky bit." ~/.claude/projects/-Users-palimondo-Developer-xs/
# Found in TWO files:
# 84db4cae-...jsonl (line 889) - main session
# agent-a907deb.jsonl (line 20) - subagent file NOT searched!
```

## Root Cause

xs was built for Claude Code 1.x format before agent files existed. It only searches/parses the main session file, not associated agent files.

## Workaround

Use ripgrep directly to search agent files:

```bash
# Search all JSONL files in project directory:
$ rg "pattern" ~/.claude/projects/-Users-palimondo-Developer-xs/

# List agent files:
$ ls ~/.claude/projects/-Users-palimondo-Developer-xs/agent-*.jsonl
```

## Related Story

- PRS-011: Agent file loading (new story to add support)
- SID-001: Display sidechain events (depends on agent file support)
- SID-002: Search includes sidechain content (depends on agent file support)

## Mining Agent Notes

Cannot rely on xs to analyze subagent sessions. Must use ripgrep directly or request that subagents include their tool call history in their response text.
