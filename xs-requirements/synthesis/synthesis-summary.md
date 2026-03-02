# Phase 4 Synthesis Summary

**Date**: 2026-02-17
**Phase**: Pass 2 Story Mining + Pass 4 Principles + Pass 5 Conflicts (combined)

## Coverage Statistics

### Extraction Phase
- **Total chunks extracted**: 1,156 (823 daylog + 333 session)
- **Total findings files**: 1,156
- **Sources covered**: 10 day logs (day-016 through day-025) + 46 sessions

### Epic Synthesis
| Epic | Stories | Findings Assigned | Findings Reviewed | Coverage |
|------|---------|-------------------|-------------------|----------|
| jsonl-parsing | 13 | ~95 | 237 | High |
| console-formatting | 25 | ~250 | ~290 | High |
| filtering | 15 | 97 | ~120 | Complete |
| range-selection | 7 | ~43 | ~60 | High |
| display-modes | 5 | ~60 | ~80 | High |
| cli-interface | 9 | 62 | ~80 | High |
| search | 7 | ~45 | ~60 | High |
| export | 4 | 47 | ~60 | High |
| sidechain-handling | 3 | ~20 | ~30 | Medium |
| fetch | 10 | 77 | ~100 | High |
| context | 7 | ~47 | ~60 | High |
| summary | 3 | 48 | ~60 | High |
| **TOTAL** | **108** | **~891** | **~1,237** | |

Note: "Findings Reviewed" exceeds "Findings Assigned" because many findings were
implementation mechanics (code edits, git operations, test debugging) that informed
understanding but don't map to specific acceptance criteria.

## Story Counts

### By Epic (108 total, 90 original + 18 new)
| Epic | Original | New | Total | New Story IDs |
|------|----------|-----|-------|---------------|
| console-formatting | 21 | 4 | 25 | FMT-022, FMT-023, FMT-024, FMT-025 |
| filtering | 12 | 3 | 15 | FLT-013, FLT-014, FLT-015 |
| jsonl-parsing | 11 | 2 | 13 | PRS-012, PRS-013 |
| fetch | 8 | 2 | 10 | GFH-009, GFH-010 |
| cli-interface | 7 | 2 | 9 | CLI-008, CLI-009 |
| search | 5 | 2 | 7 | SRC-006, SRC-007 |
| range-selection | 5 | 2 | 7 | RNG-006, RNG-007 |
| context | 7 | 0 | 7 | - |
| display-modes | 5 | 0 | 5 | - |
| export | 3 | 1 | 4 | EXP-004 |
| sidechain-handling | 3 | 0 | 3 | - |
| summary | 3 | 0 | 3 | - |

### By Priority (approximate)
- **must**: ~45 stories (core functionality)
- **should**: ~48 stories (important features)
- **could**: ~15 stories (nice-to-have or unresolved features)

### All Stories Now Status: mined
All 108 stories have been populated with sources and acceptance criteria by epic agents.

## Principles Extracted (9)

| ID | Title | Applies To |
|----|-------|-----------|
| PRIN-001 | Console Output Fidelity for LLM Consumption | FMT-*, DSP-*, SUM-* |
| PRIN-002 | Canonical Filter Pipeline Ordering | FLT-*, RNG-*, SRC-*, CLI-006 |
| PRIN-003 | Raw JSONL Passthrough Contract | EXP-001, EXP-002, PRS-012, SID-003 |
| PRIN-004 | No Chrome in Output (No Headers, No Emojis) | FMT-024, FMT-025, DSP-*, SUM-001 |
| PRIN-005 | Graceful Degradation on Malformed Input | PRS-*, SRC-001, SUM-001, GFH-003 |
| PRIN-006 | Period-Appropriate Formatting (1.x vs 2.x) | PRS-006, FMT-*, DSP-* |
| PRIN-007 | Self-Documenting Defaults (Summary as Tutorial) | SUM-*, CLI-001, CLI-006 |
| PRIN-008 | Filter-Display Separation | FLT-*, DSP-*, CLI-002, FLT-015 |
| PRIN-009 | Stable Sequence Numbers | PRS-005, DSP-004, RNG-*, FLT-* |

## Conflicts Surfaced (4)

| ID | Title | Status | Affects |
|----|-------|--------|---------|
| CONF-001 | Claude Code 1.x vs 2.x Format Differences | pending | PRS-006, FMT-*, DSP-*, PRIN-006 |
| CONF-002 | Sequence Numbers in JSON/JSONL Export | pending | EXP-001, EXP-002, EXP-004, PRIN-003 |
| CONF-003 | --git Shortcut Fails with cd-Prefixed Commands | pending | FLT-014, CLI-003, SUM-003 |
| CONF-004 | Slash Command Display Prefix | pending | FMT-012, PRIN-001 |

## Cross-Epic Resolutions

17 cross-epic findings were resolved (see `cross-epic-resolutions.yaml`):
- Filter pipeline ordering: owned by filtering, elevated to PRIN-002
- Implicit timeline mode: owned by CLI (CLI-006)
- Raw JSONL passthrough: owned by export, elevated to PRIN-003
- No headers/emojis: owned by console-formatting, elevated to PRIN-004
- Sequence number display: split between DSP-004 (behavior) and FMT-017 (rendering)
- Discontinuous separator: owned by DSP-005, SRC-006 for search-specific context
- --git shortcut: owned by filtering (FLT-014), elevated to CONF-003
- And 10 additional cross-references documented

## Uncovered/Out-of-Scope Findings

4 findings were classified as out of scope or deferred:
1. **Session graph scanning** (e583:F007) - User marked as "side quest"; future capability
2. **xs symlink location** (e583:F006) - Deployment concern, not functional requirement
3. **Shell quoting with globs** (b475:F004) - Implementation/documentation concern
4. **Named filter modes** (0841:F001) - Superseded by virtual entity design

2 findings were resolved with cross-references:
1. **SID-003-AC3 metadata preservation** - Keep in SID-003, cross-ref to PRS-012 and PRIN-003
2. **Sidechain epic size** - Keep as separate epic (distinct concerns justify separation)

## Unresolved Questions (Grouped by Epic)

### jsonl-parsing
- Exact XML structure for ! (bash) and @ (context drop) user messages (PRS-008)
- How to handle format version differences in content block structure (PRS-006 + PRS-013)
- Agent file discovery method preference (directory scan vs sessionId match vs agent_transcript_path)

### export
- Should --json/--jsonl include sequence numbers? (CONF-002)
- Should --export-json OUTPUT be optional (making --json redundant)?

### search
- Search for patterns starting with -- treated as argparse flags (workaround: --search=--pattern)

### context (compaction recovery)
- --jq and --tail flags are requested features that may not exist in current implementation
- Pipeline ordering (tail before search vs after) needs resolution before CRH-005 AC1

### sidechain-handling
- Should sidechain events have visual marking in timeline? (No user request found)

### range-selection
- No post-filter tail selection (user proposed --tail but deferred)
- +N parsing conflicts with argparse when flags appear before range argument

### fetch
- Self-fetch from within GHA using GITHUB_RUN_ID env var (explored, never concluded)
- PR number format ambiguity (pr_number vs issue_number+is_pr)

## Recommendations for Next Pass

### Pass 3: Golden File Assembly
1. **Start with console-formatting** (25 stories, most complex formatting) — gather existing golden outputs from `specs/golden_outputs/` and organize by format version
3. **Use real session data** from `bookminder-sessions/` for stories without existing golden files
4. **Resolve CONF-001 (1.x vs 2.x)** before golden file assembly if possible, since it determines whether one or two sets of golden files are needed per formatting story
6. **Link golden files to specific acceptance criteria** in story YAML files

### Pass 5: Conflict Resolution (4 conflicts pending)
- CONF-001 and CONF-004 should be resolved with user input before implementation begins
- CONF-003 may need real-world testing to determine best option
