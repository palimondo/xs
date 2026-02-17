# Discovery: Compaction Creates New Session Files

## Observation

In the current Claude Code version (circa Feb 2026), when context compaction occurs
(automatic or via `/compact`), Claude Code creates a **new session transcript file**
rather than continuing to append to the existing one.

Evidence from this project's session directory:

```
Feb 17 02:36  6007a567...jsonl   745KB   (current session)
Feb 17 02:15  2c969f22...jsonl   2.3MB   (previous — planning session)
Feb 17 01:17  61bbfd94...jsonl   1.4MB
Feb 17 00:09  f7217b4b...jsonl   1.2MB
Feb 16 23:35  2aa40d0c...jsonl   1.7MB
Feb 16 22:55  8c40b5e1...jsonl   2.2MB
Feb 16 21:59  a05fef85...jsonl   3.7MB
Feb 16 21:13  bbd2bac9...jsonl   1.2MB
Feb 16 20:33  ed3d3318...jsonl   236B    (tiny — likely compaction artifact)
Feb 16 20:31  6c392990...jsonl   1.7KB
```

10 session files in ~30 hours of work on one project. Many of these represent the
**same logical conversation** continued after compaction, not genuinely separate
sessions started by the user.

## Implications for xs

### 1. Session listing must group related files

When a user asks "show me my sessions," they expect to see logical sessions, not
compaction fragments. xs needs a way to detect that file B is a continuation of file A
and group them.

Possible detection signals:
- Timestamp proximity (file B created shortly after file A's last event)
- Same project directory
- Compaction summary message as first entry in the new file
- Parent session ID field (if Claude Code records it)

### 2. Session replay must stitch files together

Reconstructing a full session for Gemini summarization requires reading all files in the
chain. The current session replay assumes one file = one session. With compaction-created
files, this undercounts content significantly.

### 3. Compaction recovery needs the file chain

The compaction recovery use case (recover details lost when Claude Code compacts) is
directly affected. When compaction occurs:
- The pre-compaction content is in file A
- The compaction summary + post-compaction content is in file B
- Recovery needs to read BOTH files to understand what was lost

### 4. Line numbering

If sessions are stitched, line numbers need to account for multi-file spans. A unified
line number (e.g., file A has lines 1-500, file B continues as 501-800) or a
file:line compound reference.

### 5. Session inventory may undercount/overcount

The bookminder-sessions inventory has 60 files but may represent fewer logical sessions.
The earlier BookMinder-era sessions (Jul 2025) may or may not exhibit this behavior
depending on which Claude Code version was running then.

## Questions to Investigate During Extraction

As we read session transcripts in Phase 3, watch for:
- Do compaction artifacts appear in the JSONL? (compaction summary messages, parent refs)
- Is there a `parent_session_id` or similar field linking files?
- What does the first event in a compaction-created file look like?
- Does the format differ between user-initiated `/compact` and automatic compaction?

## Impact on Requirements

This may generate new stories:
- Story: "xs must detect and group compaction-continuation files"
- Story: "xs must stitch multi-file sessions for replay"
- Story: "xs must show logical session boundaries, not file boundaries"
- Acceptance criteria: "given a session that was compacted 3 times, xs replay shows
  the complete conversation as if from one file"

These should emerge naturally during Phase 3 session extraction if the sessions we're
reading span compaction boundaries.
