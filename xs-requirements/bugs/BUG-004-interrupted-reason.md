# BUG-004: Interrupted message reason not displayed

## Problem

When a user interrupts Claude's response (e.g., rejecting ExitPlanMode), they can provide a reason via the prompt "Tell Claude what to do instead". This reason is not stored in the JSONL transcript.

## Evidence

In xs output:
```
[N] [Request interrupted by user]
```

In JSONL:
```json
{
  "type": "user",
  "message": {
    "content": [{"type": "text", "text": "[Request interrupted by user]"}]
  }
}
```

The user's reason text is NOT captured anywhere in the JSONL.

## Root Cause

This appears to be a Claude Code issue, not an xs issue. Claude Code doesn't write the user's interruption reason to the transcript.

## Workaround

None for xs - the data is not in the JSONL.

For mining agents: When you see "[Request interrupted by user]", check the next user message which typically contains the correction or additional instructions.

## Related Story

FMT-021: Interrupted message reason display (for when/if Claude Code adds this data)

## Mining Agent Notes

When analyzing interrupted messages:
1. Note the interruption
2. Look at the NEXT user message for the reason/correction
3. The user's intent is typically in the following message, not the interruption itself
