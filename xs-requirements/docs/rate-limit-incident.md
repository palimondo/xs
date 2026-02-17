# Rate Limit Incident — 2026-02-17

## What Happened

During batch CW+CX processing (day-024 L15201-L17600), 12 subagents were in
flight when the per-account Anthropic API rate limit was hit. 7 of 12 chunks
completed successfully before the limit kicked in. The remaining 5 agents
returned "You've hit your limit" errors.

## Symptoms

- Subagent returns immediately with a rate limit message instead of processing
- No findings file written to disk (agent never reached extraction step)
- Partial files possible if agent hit limit during self-validation step

## Recovery Steps Taken

1. Checked which findings files existed on disk (`ls` for expected filenames)
2. Ran `progress complete <existing-files>` to validate and mark the 7 good ones
3. Ran `progress reset dispatched` to reset the 5 incomplete chunks back to pending
4. Verified clean state with `progress status` (0 dispatched, correct pending count)

## Lessons Learned

- Partial files may lack speaker fields if the agent hit the limit before
  self-validation (Step 5). The `progress complete` validator catches these.
- Rate limits are per-account, not per-agent. 12 parallel Sonnet agents can
  trigger the limit during sustained extraction runs.
- Recovery is straightforward: validate what exists, reset what doesn't.
- Always check disk state before resetting — don't lose completed work.
