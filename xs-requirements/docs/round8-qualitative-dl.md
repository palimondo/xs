# Round 8 Qualitative Assessment: Day Log Findings

## Summary Table

| Condition | Total | Signal | Noise | Dup | Signal% | Unique Signal |
|-----------|:-----:|:------:|:-----:|:---:|:-------:|:-------------:|
| R8-H-400  |  35   |   18   |  11   |  6  |   51%   |       0       |
| R8-S-400  |  64   |   24   |  31   |  9  |   38%   |       2       |
| R8-H-200  |  45   |   24   |  15   |  6  |   53%   |       0       |
| R8-S-200  |  49   |   30   |  16   |  3  |   61%   |       2       |

## Per-Condition Detailed Classification

### R8-H-400 (Haiku, 400-line chunks)

**Chunk 1: day-021-L11201-11600 (6 findings)**

| ID | Classification | Rationale |
|----|---------------|-----------|
| F001 | Signal | Truncation count = total lines, not remaining lines |
| F002 | Noise | Implementation detail (jq code snippet) |
| F003 | Signal | Tool result indentation pattern: 2sp + ⎿ + 4sp + content |
| F004 | Signal | Two distinct indentation patterns for tool result lines |
| F005 | Signal | Primary use case: recover truncated content for analysis and Gemini summarization |
| F006 | Duplicate | Restates F005 from agent's perspective |

**Chunk 2: day-021-L11601-12000 (15 findings)**

| ID | Classification | Rationale |
|----|---------------|-----------|
| F001 | Noise | Agent planning step, not a requirement |
| F002 | Signal | TodoWrite displays as "Update Todos" (tool name abstraction) |
| F003 | Signal | Todo item display format: status symbol + content + priority |
| F004 | Signal | Status symbols: pending=☐, in_progress=◐, completed=☒ |
| F005 | Signal | Priority mapping: high=P0, medium=P1, low=P2 |
| F006 | Signal | Todo continuation lines indented with 5 spaces |
| F007 | Signal | User requests TodoRead formatting improvement |
| F008 | Signal | TodoRead displays as "Read Todos" |
| F009 | Duplicate | Restates F003 with TodoRead example |
| F010 | Noise | JSONL data structure detail (array vs object) |
| F011 | Signal | Spacing issue: missing newlines between messages (user correction) |
| F012 | Signal | Newlines required after tool uses and before next message |
| F013 | Noise | Implementation detail (jq newline code) |
| F014 | Noise | Implementation detail (jq newline code) |
| F015 | Noise | Implementation detail (jq newline code) |

**Chunk 3: day-021-L12001-12423 (14 findings)**

| ID | Classification | Rationale |
|----|---------------|-----------|
| F001 | Noise | Agent describing what reconstruct.jq is (meta) |
| F002 | Signal | Message type formatting rules: user="> ", assistant="⏺ ", tool use="⏺ ToolName(args)", tool result="⎿" |
| F003 | Signal | Truncation: first 3 lines + total line count |
| F004 | Duplicate | Restates TodoWrite/TodoRead formatting from chunk 2 |
| F005 | Duplicate | Restates use case from chunk 1 F005 |
| F006 | Noise | Implementation detail about command-message tag filtering |
| F007 | Signal | User requests slash commands included in reconstruction |
| F008 | Noise | Implementation detail (extract command message) |
| F009 | Noise | Validation step, not a requirement |
| F010 | Noise | Agent observation, not a requirement |
| F011 | Signal | Interrupted tool results should be detected and displayed |
| F012 | Signal | Interrupted messages appear as special user message type |
| F013 | Duplicate | Restates spacing requirement from chunk 2 F011-F012 |
| F014 | Duplicate | Restates truncation from F003 |

**R8-H-400 Totals: 35 findings, 18 signal, 11 noise, 6 duplicates**

---

### R8-S-400 (Sonnet, 400-line chunks)

**Chunk 1: day-021-L11201-11600 (4 findings)**

| ID | Classification | Rationale |
|----|---------------|-----------|
| F001 | Signal | Truncation count = total line count, not remaining |
| F002 | Signal | Tool result spacing pattern: 2sp + ⎿ + 2sp for Waiting, 2sp + ⎿ + 2sp + content's own leading spaces |
| F003 | Signal | PRIMARY: Goal is content recovery for analysis/Gemini, NOT console fidelity |
| F004 | Signal | User requests TodoWrite formatting improvement |

**Chunk 2: day-021-L11601-12000 (32 findings)**

| ID | Classification | Rationale |
|----|---------------|-----------|
| F001 | Duplicate | Restates TodoWrite display name from F002 below |
| F002 | Signal | Todo item format with status symbols and priorities |
| F003 | Noise | Implementation detail (jq literal) |
| F004 | Noise | Implementation detail (priority mapping code) |
| F005 | Noise | Implementation detail (priority mapping code) |
| F006 | Noise | Implementation detail (priority mapping code) |
| F007 | Noise | Implementation detail (status symbol code) |
| F008 | Noise | Implementation detail (status symbol code) |
| F009 | Noise | Implementation detail (status symbol code) |
| F010 | Noise | Implementation detail (format template code) |
| F011 | Noise | Implementation detail (conditional check code) |
| F012 | Noise | Implementation detail (code comment) |
| F013 | Signal | TodoWrite tool use displays as "⏺ Update Todos" |
| F014 | Signal | TodoWrite results show formatted todo items |
| F015 | Signal | Priority mapping: high→P0, medium→P1, low→P2 |
| F016 | Signal | 5-space indentation for continuation lines |
| F017 | Signal | User requests TodoRead formatting |
| F018 | Signal | TodoRead displays as "⏺ Read Todos" |
| F019 | Duplicate | Restates todo item format from F002 |
| F020 | Noise | Implementation detail (jq literal) |
| F021 | Noise | Implementation detail (code comment about array structure) |
| F022 | Duplicate | Restates TodoWrite formatting summary |
| F023 | Duplicate | Restates TodoRead formatting summary |
| F024 | Signal | User correction: missing newlines between messages |
| F025 | Noise | Agent acknowledging bug |
| F026 | Noise | Implementation detail (jq newline code) |
| F027 | Noise | Agent acknowledging spacing issue |
| F028 | Noise | Implementation detail (jq newline code) |
| F029 | Noise | Implementation detail (jq newline code) |
| F030 | Noise | Implementation detail (jq newline code) |
| F031 | Noise | Implementation detail (jq newline code) |
| F032 | Duplicate | Agent confirming spacing fix (restates F024) |

**Chunk 3: day-021-L12001-12423 (28 findings)**

| ID | Classification | Rationale |
|----|---------------|-----------|
| F001 | Signal | Complete spacing specification: blank lines after all message types |
| F002 | Noise | Observation about file size growing (not a requirement) |
| F003 | Noise | User requests report (meta, not xs requirement) |
| F004 | Signal | Core problem statement: terminal truncation loses content |
| F005 | Noise | Source file location (not an xs requirement) |
| F006 | Duplicate | Restates use case (feeding to Gemini) |
| F007 | Signal | User correction: missing slash commands in output |
| F008 | Noise | Implementation detail (command-message tag filtering) |
| F009 | Noise | Implementation detail (aggressive filtering) |
| F010 | Signal | User requests slash command inclusion |
| F011 | Noise | Implementation detail (jq extraction code) |
| F012 | Signal | Slash command display format: own line, blank line after, output follows |
| F013 | Signal | User correction: slash commands should show "> /command is running..." |
| F014 | Noise | Validation method (using rg) |
| F015 | Signal | Correct format from original: "> /expert-council is running..." |
| F016 | Signal | JSONL structure: command-message tag contains status text |
| F017 | Noise | Implementation detail (jq extraction code) |
| F018 | Duplicate | Restates slash command format |
| F019 | Signal | User requests interrupted tool execution formatting |
| F020 | Signal | Interrupted format: "⎿ Interrupted by user" |
| F021 | Signal | JSONL marker: "[Request interrupted by user for tool use]" |
| F022 | Noise | Implementation detail (jq conditional) |
| F023 | Noise | Implementation detail (jq skip logic) |
| F024 | Noise | Implementation note about test coverage gap |
| F025 | Signal | Session JSONL file location: ~/.claude/projects/{path}/{session_id}.jsonl |
| F026 | Noise | Example command (not a requirement) |
| F027 | Duplicate | User cleanup request (not xs requirement) |
| F028 | Duplicate | Final artifacts list (not xs requirement) |

**R8-S-400 Totals: 64 findings, 24 signal, 31 noise, 9 duplicates**

*Note: S-400 produced almost double the total findings but the additional volume is predominantly noise (implementation details captured as individual findings).*

---

### R8-H-200 (Haiku, 200-line chunks)

**Chunk 1: day-021-L11201-11400 (6 findings)**

| ID | Classification | Rationale |
|----|---------------|-----------|
| F001 | Signal | Truncation line count confusion (total vs remaining) |
| F002 | Signal | Truncation count should show total lines |
| F003 | Noise | Agent debugging spacing (not a requirement) |
| F004 | Signal | Tool result indentation: 2sp + ⎿ + 2sp pattern |
| F005 | Noise | Agent listing inconsistencies (debugging observation) |
| F006 | Signal | Expected output is curated/edited, not raw transform |

**Chunk 2: day-021-L11401-11600 (10 findings)**

| ID | Classification | Rationale |
|----|---------------|-----------|
| F001 | Noise | Agent correcting spacing (debugging step) |
| F002 | Noise | Agent debugging (not a requirement) |
| F003 | Signal | Final spacing: 2sp + ⎿ + 2sp for tool results |
| F004 | Noise | Agent observation about diff count |
| F005 | Signal | Confirms core transformations working: text, tool use, tool results, collapse |
| F006 | Signal | Primary use case: recover truncated content for analysis |
| F007 | Signal | User wants full session reconstruction saved to file for review |
| F008 | Noise | Artifact output (5210 lines) -- implementation detail |
| F009 | Signal | Expected output has been curated/edited (not raw transform) |
| F010 | Signal | User requests TodoWrite formatting improvement |

**Chunk 3: day-021-L11601-11800 (8 findings)**

| ID | Classification | Rationale |
|----|---------------|-----------|
| F001 | Noise | Agent planning step |
| F002 | Noise | Agent creating golden file (process, not requirement) |
| F003 | Noise | Agent implementation step |
| F004 | Noise | Implementation detail (jq conditional) |
| F005 | Noise | Implementation detail (result formatting) |
| F006 | Noise | Implementation detail (result detection logic) |
| F007 | Signal | Todo items formatted with 5-space indentation for continuation |
| F008 | Signal | Console fidelity: output must match original CC appearance |

**Chunk 4: day-021-L11801-12000 (7 findings)**

| ID | Classification | Rationale |
|----|---------------|-----------|
| F001 | Noise | Agent searching for TodoRead uses |
| F002 | Signal | TodoRead needs explicit handling |
| F003 | Signal | TodoRead displays as "⏺ Read Todos" |
| F004 | Signal | User correction: missing newlines between messages |
| F005 | Signal | Newlines required after tool uses |
| F006 | Signal | Blank line needed after tool results before next message |
| F007 | Duplicate | Confirms spacing fix resolved (restates F004-F006) |

**Chunk 5: day-021-L12001-12200 (7 findings)**

| ID | Classification | Rationale |
|----|---------------|-----------|
| F001 | Duplicate | Restates spacing resolution |
| F002 | Signal | Complete spacing specification for all message types |
| F003 | Signal | User requests slash commands in reconstruction |
| F004 | Signal | Slash command display: own line, blank line after, output follows |
| F005 | Signal | User correction: slash commands should show "is running..." status |
| F006 | Signal | Slash commands formatted as user messages with > prefix and running status |
| F007 | Noise | JSONL structure detail |

**Chunk 6: day-021-L12201-12423 (7 findings)**

| ID | Classification | Rationale |
|----|---------------|-----------|
| F001 | Signal | Slash command format confirmed: "> /command is running..." |
| F002 | Signal | User requests interrupted tool result formatting |
| F003 | Duplicate | Agent acknowledging interrupted handling gap |
| F004 | Noise | Implementation detail (jq conditional code) |
| F005 | Duplicate | Implementation detail about two types of interrupted messages |
| F006 | Duplicate | Restates all improvements summary |
| F007 | Duplicate | Restates formatting requirements summary |

**R8-H-200 Totals: 45 findings, 24 signal, 15 noise, 6 duplicates**

---

### R8-S-200 (Sonnet, 200-line chunks)

**Chunk 1: day-021-L11201-11400 (7 findings)**

| ID | Classification | Rationale |
|----|---------------|-----------|
| F001 | Signal | Truncation count = total lines, agent realizes remaining vs total confusion |
| F002 | Noise | Implementation detail (jq code for truncation) |
| F003 | Signal | Agent struggling with spacing: 1sp vs 2sp after ⎿ |
| F004 | Signal | After ⎿, preserve original content spacing |
| F005 | Signal | Spacing pattern: 2sp + ⎿ + 4sp total = 2sp + ⎿ + content's own 2sp |
| F006 | Signal | Multiple formatting issues identified: Waiting lines, collapsed content, reordering |
| F007 | Noise | Incomplete finding: "Line 5:" with truncated context |

**Chunk 2: day-021-L11401-11600 (6 findings)**

| ID | Classification | Rationale |
|----|---------------|-----------|
| F001 | Noise | Implementation detail (spacing debugging) |
| F002 | Noise | Implementation detail (spacing pattern) |
| F003 | Noise | Implementation detail (jq spacing code) |
| F004 | Signal | CRITICAL: User's goal is NOT console fidelity but content recovery for Gemini |
| F005 | Duplicate | Restates F004 with slightly different framing |
| F006 | Signal | User requests TodoWrite formatting improvement |

**Chunk 3: day-021-L11601-11800 (7 findings)**

| ID | Classification | Rationale |
|----|---------------|-----------|
| F001 | Signal | TodoWrite golden file format established |
| F002 | Signal | TodoWrite tool use displays as "Update Todos" instead of full input |
| F003 | Signal | Priority mapping: high→P0, medium→P1, low→P2 |
| F004 | Signal | Status symbols: completed→☒, in_progress→◐, pending→☐ |
| F005 | Noise | Implementation detail (jq extraction code) |
| F006 | Signal | Summary: TodoWrite formatting with status, priority, 5sp indentation |
| F007 | Signal | User requests TodoRead formatting |

**Chunk 4: day-021-L11801-12000 (11 findings)**

| ID | Classification | Rationale |
|----|---------------|-----------|
| F001 | Duplicate | Restates TodoRead request from chunk 3 F007 |
| F002 | Signal | TodoRead displays as "⏺ Read Todos" |
| F003 | Signal | TodoRead results show same formatted items as TodoWrite |
| F004 | Noise | Implementation detail (TodoRead array vs TodoWrite object) |
| F005 | Signal | User correction: missing newlines between messages |
| F006 | Signal | Tool uses need newline after them for spacing |
| F007 | Noise | Implementation detail (jq newline code) |
| F008 | Noise | Implementation detail (jq newline code) |
| F009 | Noise | Implementation detail (jq newline code) |
| F010 | Noise | Implementation detail (jq newline code) |
| F011 | Noise | Implementation detail (jq newline code) |

**Chunk 5: day-021-L12001-12200 (10 findings)**

| ID | Classification | Rationale |
|----|---------------|-----------|
| F001 | Signal | Complete spacing specification: blank lines after all 4 message types |
| F002 | Noise | User satisfaction comment (not a requirement) |
| F003 | Signal | User correction: missing slash command (/hi) in output |
| F004 | Signal | Root cause: command-message tags being filtered out |
| F005 | Signal | User requests slash commands included in reconstruction |
| F006 | Noise | Implementation detail (jq extraction code) |
| F007 | Signal | Slash command format: own line, blank line after, output follows |
| F008 | Signal | User correction: slash commands should show "> /command is running..." |
| F009 | Noise | Validation method (using rg) |
| F010 | Signal | JSONL structure: command-message and command-name tags |

**Chunk 6: day-021-L12201-12423 (8 findings)**

| ID | Classification | Rationale |
|----|---------------|-----------|
| F001 | Signal | Slash command format: extract from command-message tag, show as "> /command is running..." |
| F002 | Duplicate | Restates slash command user correction from chunk 5 |
| F003 | Noise | Validation step (rg verification) |
| F004 | Signal | Interrupted request format from original: "⎿ Interrupted by user" |
| F005 | Signal | JSONL structure: interrupted requests marked with "[Request interrupted by user for tool use]" |
| F006 | Signal | Interrupted user messages should be skipped (only tool result shows formatted version) |
| F007 | Signal | Tool results for interrupted requests show double "⎿ Interrupted by user" lines |
| F008 | Signal | Session JSONL location: ~/.claude/projects/{path}/{session_id}.jsonl |

**R8-S-200 Totals: 49 findings, 30 signal, 16 noise, 3 duplicates**

---

## Unique Signal Analysis

Requirements found by only some conditions:

### 1. "Goal is NOT console fidelity but content recovery" (nuanced distinction)
- **Found by**: R8-S-400 (F003 in chunk 1), R8-S-200 (F004 in chunk 2)
- **Missed by**: R8-H-400, R8-H-200
- **Significance**: HIGH. This is a critical insight that distinguishes reconstruct.jq's goal (content recovery) from what might be assumed (exact console reproduction). Sonnet explicitly flags this with "CRITICAL" and "PRIMARY REQUIREMENT" annotations. Haiku captures the user quote about recovering truncated content but does not draw out the nuanced distinction that the goal is NOT console fidelity.

### 2. "Expected output is curated/edited, not raw transform"
- **Found by**: R8-S-400 (T003 in chunk 1), R8-H-200 (F006/F009)
- **Missed by**: R8-H-400 (partially), R8-S-200 (partially)
- **Significance**: MEDIUM. This insight affects how golden files should be created -- they cannot simply be raw transforms of JSONL. All conditions mention this observation but Sonnet-400 and Haiku-200 give it finding-level prominence.

### 3. Session JSONL file location
- **Found by**: R8-S-400 (F025 in chunk 3), R8-S-200 (F008 in chunk 6), R8-H-400 (not captured)
- **Missed by**: R8-H-400, R8-H-200 (partially -- documented in threads but not findings)
- **Significance**: LOW-MEDIUM. Knowledge of where session files live is relevant to the "local session exploration" use case.

### 4. Interrupted request has TWO types: user text message (skip) and tool result (format)
- **Found by**: R8-S-200 (F006 in chunk 6 explicitly distinguishes the two)
- **Partially found by**: R8-H-400, R8-S-400, R8-H-200 (all mention interrupted handling but less clearly distinguish the two pathways)
- **Significance**: MEDIUM. Important implementation detail that the user message version is hidden while the tool result version is displayed.

### 5. Double "⎿ Interrupted by user" display pattern
- **Found by**: R8-S-200 (F007 in chunk 6), R8-S-400 (F022 in chunk 3)
- **Partially found by**: R8-H-400 (F004 in chunk 3 quotes the jq code showing double output)
- **Missed by**: R8-H-200
- **Significance**: LOW. Specific formatting detail about showing interrupted twice (matching Waiting... pattern).

## Thread Quality Assessment

### R8-H-400 (Haiku, 400-line chunks)
**Thread coherence: GOOD.** Threads are well-scoped and track complete topic lifecycles within each chunk. T001/T002/T003 in chunk 1 each cover a distinct topic with clear status tracking. Chunk 2's threads (TodoWrite, TodoRead, spacing) are well-separated. Thread naming is descriptive. However, threads do not cross-reference between chunks -- the TodoWrite thread in chunk 2 does not link back to its introduction in chunk 1's coverage area. Overall, clean and functional thread tracking.

### R8-S-400 (Sonnet, 400-line chunks)
**Thread coherence: VERY GOOD.** Threads are more analytically framed. T003 in chunk 1 ("Expected output doesn't match raw transformation") captures a meta-observation that Haiku missed elevating. T004 ("User's goal: recover truncated log content") is correctly identified as the most important thread. Notes are insightful -- the note "T004 is CRITICAL for xs requirements" shows Sonnet exercising editorial judgment. However, the massive finding count in chunk 2 (32 findings!) dilutes signal significantly. Each jq code line gets its own finding, making the useful findings hard to find.

### R8-H-200 (Haiku, 200-line chunks)
**Thread coherence: ADEQUATE.** Smaller chunks mean threads are often simpler (1-2 events). Some chunks have only 2-3 threads. The advantage is that threads within each chunk are tightly focused. The disadvantage is that cross-chunk continuity is lost -- the TodoWrite thread starts in chunk 2 (F010) and continues in chunk 3 but is tracked as separate T001 threads. Thread status tracking is less precise ("open" vs "resolved" sometimes inconsistent across chunk boundaries).

### R8-S-200 (Sonnet, 200-line chunks)
**Thread coherence: GOOD.** Benefits from Sonnet's analytical ability even in smaller chunks. Chunk 2's T002 ("reconstruct.jq output goal - not console fidelity but full content recovery") captures the critical distinction with precise language. Context notes like "Thread introduced in context zone (L11791), implementation in primary range" show awareness of chunk boundaries. Notes sections add analytical value ("F004 is CRITICAL: contradicts xs console fidelity principle"). However, some chunks have sparse threads due to small size (chunk 2 has only 3 threads covering 200 lines).

## Cross-Condition Patterns

### Model Effects (Haiku vs Sonnet)

1. **Finding granularity**: Sonnet produces more findings per chunk but at lower signal density. Sonnet-400 chunk 2 has 32 findings where Haiku-400 chunk 2 has 15, but Sonnet's extras are mostly implementation-level jq code snippets.

2. **Analytical depth**: Sonnet adds interpretive notes and flags findings as "CRITICAL" or "PRIMARY REQUIREMENT." Haiku reports what it sees without editorial judgment. For requirements mining, Sonnet's interpretation is valuable but comes bundled with noise.

3. **Noise type**: Sonnet's noise is predominantly jq implementation details captured as individual findings (each code line gets a finding). Haiku's noise tends to be process observations (agent planning steps, validation steps).

4. **Unique insights**: Sonnet uniquely captures the critical "goal is NOT console fidelity" distinction and provides more nuanced JSONL structure documentation. These are the most valuable unique signals in the assessment.

### Chunk Size Effects (200 vs 400)

1. **Duplication**: 400-line chunks have more within-chunk duplicates because the same topic gets mentioned at introduction and resolution. 200-line chunks have fewer within-chunk duplicates but create cross-chunk tracking gaps.

2. **Thread continuity**: 400-line chunks track topic lifecycles more completely (introduction through resolution in one chunk). 200-line chunks often split topics across boundaries, losing thread continuity.

3. **Signal density**: 200-line chunks produce tighter, more focused findings because there is less material to wade through. 400-line chunks sometimes produce "summary" findings that combine multiple topics.

4. **Total volume**: Raw finding counts are similar (H-400: 33, H-200: 40, S-400: 60, S-200: 45), but the quality distribution differs.

### Best Combination

**R8-S-200 achieves the best signal-to-noise ratio (61%)** while also capturing the most absolute signal (30 findings) and the most unique signal. It combines Sonnet's analytical depth with the focusing effect of smaller chunks. The remarkably low duplicate count (3) suggests 200-line chunks naturally reduce within-condition redundancy. The main trade-off is that thread continuity across chunks requires more synthesis work from the orchestrator.

**R8-H-200 is the efficiency runner-up** -- matches S-400's signal count (24) with far less noise (15 vs 31), achieving 53% signal rate. It represents a good balance if Sonnet costs are a concern.

**R8-H-400 is the minimum-effort option** -- fewest total findings (35) with decent signal (18), meaning the least post-processing work. Good thread continuity within chunks. But it misses the critical "content recovery vs console fidelity" distinction that only Sonnet captures.

## Noise Patterns

### Systematic Noise by Condition

**R8-H-400 Noise (11 instances)**:
- Agent planning/process steps (3): "Let me create a test file", "Let me update the script"
- Implementation code snippets (3): jq newline additions
- Validation/confirmation steps (2): "The reconstruction captures..." type summaries

**R8-S-400 Noise (31 instances)**:
- **jq implementation details (18)**: Individual code lines captured as separate findings (priority_map code, status_symbol code, conditional checks, format templates, newline additions). This is by far the dominant noise pattern.
- Agent acknowledgment/bug confirmation (4): "I see the issue", "Much better!"
- Process observations (4): File size changes, validation methods, code comments
- Meta/non-requirement items (4): Report requests, source file locations, example commands

**R8-H-200 Noise (15 instances)**:
- Agent debugging observations (4): Spacing investigation, diff count
- Implementation details (6): jq code, detection logic, golden file creation, conditional checks
- Process steps (5): Agent planning, searching, creating files, artifact output

**R8-S-200 Noise (16 instances)**:
- **jq implementation details (10)**: Code snippets for newline additions, extraction patterns, spacing debugging (same pattern as S-400 but less extreme due to smaller chunks)
- Validation/process steps (5): rg verification, user satisfaction, validation methods
- Incomplete/truncated findings (1): F007 in chunk 1 with minimal context

### Key Noise Pattern: Sonnet's Code-Level Capture

The most prominent noise pattern across the entire assessment is **Sonnet treating individual jq code lines as distinct findings**. In R8-S-400 chunk 2, findings F003-F012 are 10 consecutive jq implementation details (priority mapping code, status symbol code, format templates). This inflates the finding count dramatically without adding signal. Haiku consolidates these into higher-level observations ("Status symbols: ☐/◐/☒" and "Priority mapping: high→P0").

This suggests that Sonnet's extraction prompt may need additional guidance to distinguish between:
- **What the code DOES** (signal: "TodoWrite uses status symbols and priority mapping")
- **How the code does it** (noise: each individual jq conditional branch)

### Cross-Cutting: Implementation vs Requirement

All conditions occasionally blur the line between implementation detail and requirement. The most common borderline cases are:
- JSONL structure details (signal when they describe what xs must parse; noise when they describe jq-specific extraction patterns)
- Spacing/formatting specifics (signal as format specifications; noise as debugging steps to discover them)
- Agent summaries (signal when they state requirements concisely; noise when they describe what was just done)
