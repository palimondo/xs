# Claude Code JSONL Session Transcript Format Reference

This document consolidates format specifications for building a robust parser. Anthropic has not published an official schema - this is community reverse-engineering.

## File Location and Organization

```
~/.claude/
├── projects/                          # All session transcripts
│   └── -Users-username-projects-app/  # Encoded path (/ → -)
│       ├── session-uuid.jsonl         # Main conversation
│       └── agent-{agentId}.jsonl      # Subagent transcripts (v1.0.60+)
├── history.jsonl                      # Global session index
├── settings.json                      # User preferences (v1.0.7+)
└── todos/                             # Session todos
    └── session-uuid.json
```

Path encoding: `/Users/name/project` → `-Users-name-project`
Session filename = session UUID (enables `claude --resume <session-id>`)

**Subagent storage**: Custom subagents get their own `agent-{agentId}.jsonl` files. Both main session and subagent files can contain entries with `isSidechain: true`. The `isSidechain` flag marks parallel/subagent work but doesn't identify which agent - that requires the separate file.

## Version Timeline

| Version | Date | Breaking Changes |
|---------|------|------------------|
| 0.2.82 | Apr 2025 | Tool renames: `LSTool` → `LS`, `View` → `Read` |
| 1.0.9 | Jun 2025 | **`costUSD` field removed** (Max plan users) |
| 1.0.38 | Jul 2025 | Hooks system, `systemMessage` field |
| 1.0.60 | Aug 2025 | Subagent transcripts in separate files |
| 1.0.124 | Sep 2025 | **`--resume` reuses session IDs** (was: created new) |
| 2.0.0 | Sep 29, 2025 | UI overhaul, `/rewind`, SDK renamed |
| 2.0.28 | Nov 2025 | `agent_id`, `agent_transcript_path` fields |
| 2.0.49 | Dec 2025 | **`sessionId` required in history.jsonl** |

## Core Entry Schema

Every JSONL line shares these base fields:

| Field | Required | Notes |
|-------|----------|-------|
| `uuid` | Yes | Unique message identifier |
| `parentUuid` | Yes | null for first message, links conversation |
| `timestamp` | Yes | ISO 8601 with milliseconds |
| `type` | Yes | `"user"`, `"assistant"`, `"summary"`, `"file-history-snapshot"`, `"system"`, `"queue-operation"` |
| `slug` | No | Human-readable session name (e.g., "curious-hatching-cherny") |
| `sessionId` | Yes | Matches filename |
| `version` | No | Claude Code version (e.g., "1.0.58", "2.0.76") |
| `cwd` | No | Working directory |
| `gitBranch` | No | Current git branch (added ~v1.0.58) |
| `isSidechain` | No | true for subagent/parallel work (see below) |
| `userType` | No | Typically "external" |
| `message` | Varies | Content structure differs by type |

## Message Types

### User Message
```json
{
  "type": "user",
  "uuid": "b4575262-...",
  "parentUuid": null,
  "timestamp": "2025-07-23T15:00:55.015Z",
  "message": {
    "role": "user",
    "content": "add rick to the readme"
  }
}
```

Content can be string OR array of content blocks (for tool results).

### Assistant Message
```json
{
  "type": "assistant",
  "uuid": "02f2a73e-...",
  "parentUuid": "b4575262-...",
  "timestamp": "2025-07-01T10:43:45.885Z",
  "requestId": "req_011CQg...",
  "costUSD": 0.001,        // REMOVED in v1.0.9+ for Max plan
  "durationMs": 1500,
  "message": {
    "id": "msg_01SS3c...",
    "role": "assistant",
    "model": "claude-sonnet-4-20250514",
    "content": [
      {"type": "text", "text": "I'll implement..."},
      {"type": "tool_use", "id": "toolu_01XYZ", "name": "Read", "input": {...}}
    ],
    "stop_reason": "end_turn",
    "usage": {
      "input_tokens": 4,
      "output_tokens": 1,
      "cache_creation_input_tokens": 6462,
      "cache_read_input_tokens": 14187
    }
  }
}
```

### Tool Result (in user message)
```json
{
  "type": "user",
  "message": {
    "role": "user",
    "content": [{
      "type": "tool_result",
      "tool_use_id": "toolu_01XYZ",
      "content": "File contents..."
    }]
  },
  "toolUseResult": {
    "bytes": 293809,
    "code": 200,
    "result": "...",
    "durationMs": 3079,
    "interrupted": false,       // Was tool execution interrupted?
    "isImage": false,           // Is result an image?
    "stdout": "...",            // For Bash: stdout content
    "stderr": "...",            // For Bash: stderr content
    // For Task tool:
    "status": "completed",
    "prompt": "...",
    "agentId": "a58bce3",
    "content": [...]
  }
}
```

### Summary Entry
```json
{
  "type": "summary",
  "summary": "Session focused on implementing tests",
  "leafUuid": "last-message-uuid"
}
```

### Thinking Block (in content array)
```json
{"type": "thinking", "thinking": "Let me analyze..."}
```

### System Entry
```json
{
  "type": "system",
  "subtype": "stop_hook_summary",
  "hookCount": 1,
  "hookInfos": [{"command": "/path/to/hook.sh"}],
  "hookErrors": [],
  "preventedContinuation": false,
  "stopReason": "",
  "hasOutput": false,
  "level": "suggestion",
  "toolUseID": "uuid-here"
}
```

### Queue Operation Entry
```json
{
  "type": "queue-operation",
  "operation": "dequeue",
  "timestamp": "2026-01-04T13:34:31.250Z",
  "sessionId": "session-uuid"
}
```

### Meta/Caveat Message (isMeta flag)
```json
{
  "type": "user",
  "isMeta": true,
  "sourceToolUseID": "toolu_01XYZ",
  "message": {"role": "user", "content": "Caveat: ..."}
}
```

### User Interruption
When user interrupts a response, the message content is:
```json
{"type": "user", "message": {"content": [{"type": "text", "text": "[Request interrupted by user]"}]}}
```
**Note**: User-provided reason for interruption is NOT captured in the JSONL (BUG-004).

## Content Block Types

| Type | Fields | Notes |
|------|--------|-------|
| `text` | `text` | Plain text |
| `tool_use` | `id`, `name`, `input` | Tool invocation |
| `tool_result` | `tool_use_id`, `content` | In user messages |
| `thinking` | `thinking` | Extended thinking |
| `image` | `source: {type, media_type, data}` | Base64 encoded |

## Tool Names (Current)

`Bash`, `Read`, `Write`, `Edit`, `MultiEdit`, `LS`, `Glob`, `Grep`, `WebFetch`, `WebSearch`, `TodoRead`, `TodoWrite`, `NotebookRead`, `NotebookEdit`, `Task`

Historical renames: `View` → `Read`, `LSTool` → `LS` (v0.2.82)

## 2.x New Fields

| Field | Location | Purpose |
|-------|----------|---------|
| `agentId` | Entry root | Identifies subagent type |
| `agent_transcript_path` | Entry root | Path to subagent transcript |
| `thinkingMetadata` | Entry root | Extended thinking control |
| `todos` | Entry root | Inline task tracking array |
| `modelUsage` | Entry root | Per-model token breakdown |

## Subagent and Sidechain Behavior

Two related but distinct mechanisms:

**`isSidechain: true` flag**: Marks entries as parallel/background work. Appears in BOTH main session files AND subagent files. Does NOT identify which agent - just that it's not the main conversation thread. Used by context calculators to exclude from token counting.

**Separate `agent-{agentId}.jsonl` files**: Store complete conversation history for custom subagents. Each subagent gets its own file. The `SubagentStop` hook provides `agent_transcript_path` to locate these files.

**Practical implication**: To fully understand subagent activity, you may need to:
1. Check `isSidechain` in main session to see parallel work occurred
2. Find corresponding `agent-*.jsonl` files for full subagent context
3. Match via `sessionId` (shared between main and subagent files)

## Recommended Parser Defaults

| Field | Default | Why |
|-------|---------|-----|
| `costUSD` | `0.0` | Removed in v1.0.9+ |
| `durationMs` | `None` | Optional |
| `isSidechain` | `false` | Main conversation default |
| `gitBranch` | `""` | May be absent |
| `stop_reason` | `None` | Missing mid-stream |

## Edge Cases

**Interrupted sessions**: Final entry may lack `stop_reason` or have truncated content.

**Very long sessions**: Lines can exceed 60,000 chars, files can exceed 8MB.

**Binary content**: Images as base64 in content blocks.

**Token deduplication**: Use `requestId` to deduplicate when tool use causes repeated entries.

**Content polymorphism**: `message.content` can be string OR array - handle both:
```python
content = message['message']['content']
if isinstance(content, str):
    return content
return ''.join(b['text'] for b in content if b.get('type') == 'text')
```

## Defensive Parsing Pattern

```python
entry = json.loads(line)
match entry.get('type'):
    case 'summary':
        # No message field
        pass
    case 'user' | 'assistant':
        cost = entry.get('costUSD', 0.0)
        model = entry.get('message', {}).get('model', 'unknown')
```

Treat unknown fields as ignorable. Never crash on missing optional fields.
