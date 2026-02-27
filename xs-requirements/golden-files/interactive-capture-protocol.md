# Interactive Session Capture Protocol

Drive an interactive Claude Code session via tmux to capture golden JSONL files
covering all message types. The driver is another Claude session (or a human)
following this protocol.

## Why Not Non-Interactive Mode?

`claude -p` produces different JSONL than interactive sessions (different event
structure, missing system events, no permission flow). We need real interactive
output for golden file fidelity.

## Prerequisites

- tmux installed
- Claude Code installed and authenticated
- A scratch project directory for the capture session

## Setup

```bash
# Create a scratch directory for the capture session
mkdir -p /tmp/xs-capture-session
cd /tmp/xs-capture-session
git init
echo "# Capture Session" > README.md
git add . && git commit -m "init"

# Start a detached tmux session
tmux new-session -d -s capture -x 120 -y 40

# Launch Claude Code in it (skip permissions for uninterrupted flow)
tmux send-keys -t capture 'cd /tmp/xs-capture-session && claude --dangerously-skip-permissions' Enter
```

## Driving the Session

### Sending Input

```bash
# Type a prompt (don't forget Enter)
tmux send-keys -t capture 'What is 2 + 2?' Enter

# Send a slash command
tmux send-keys -t capture '/compact' Enter

# Send special keys
tmux send-keys -t capture Escape          # interrupt
tmux send-keys -t capture C-c             # ctrl-c

# Send @file reference
tmux send-keys -t capture '@README.md summarize this' Enter
```

### Reading Output

```bash
# Capture current viewport
tmux capture-pane -t capture -p

# Capture with scrollback (last 500 lines)
tmux capture-pane -t capture -p -S -500

# Save to file for analysis
tmux capture-pane -t capture -p -S -500 > /tmp/capture-output.txt
```

### Detecting Readiness

Claude Code shows a `❯` prompt when ready for input. Check for it:

```bash
# Check if the last non-empty line contains the prompt indicator
tmux capture-pane -t capture -p | grep -c '❯'
```

**Wait strategy**: Poll every 2-3 seconds until `❯` appears. For long operations
(Task subagent, web fetch), increase timeout to 120s.

### Handling Permissions

With `--dangerously-skip-permissions`, all tools are auto-approved.
Without it, permission prompts appear and need 'y' + Enter:

```bash
tmux send-keys -t capture 'y' Enter
```

## Capture Scenario Steps

See `capture-scenario.md` for the full 25-step scenario. Each step:

1. **Send** the prompt via `tmux send-keys`
2. **Wait** for `❯` prompt to reappear
3. **Capture** the pane output for verification
4. **Evaluate** whether the expected event type was triggered
5. **Proceed** to next step (or adapt if something unexpected happened)

## Finishing

```bash
# Export the session
tmux send-keys -t capture '/export' Enter

# Wait for export to complete, then check the output
tmux capture-pane -t capture -p

# The exported file path will be shown in the output
# Copy it to our golden-files directory
cp /path/to/exported.jsonl xs-requirements/golden-files/2x/capture-session.jsonl

# Clean up
tmux send-keys -t capture '/exit' Enter
tmux kill-session -t capture
```

## Validation

After capture, verify the JSONL covers expected types:

```bash
# Run the schema derivation script on the new capture
uv run --with pyyaml python3 xs-requirements/golden-files/derive_schema.py

# Or quick check:
jq -c '.type' capture-session.jsonl | sort | uniq -c | sort -rn
jq -r '.message.content[]?.name // empty' capture-session.jsonl | sort | uniq -c | sort -rn
```

## Maintenance Workflow (Future)

When a new CC version is released:

1. Check release notes for new features/tools/event types
2. Update `capture-scenario.md` with steps to trigger new behavior
3. Re-run this protocol
4. Compare new JSONL against previous capture using `derive_schema.py`
5. Identify new/changed event types
6. Update `schema.yaml` and story acceptance criteria accordingly

## Evolution Path

1. **Current**: Manual tmux driving by Claude (this protocol)
2. **Next**: pexpect-based Python script for deterministic replay
3. **Future**: CI integration — run on each CC update, diff against baseline
