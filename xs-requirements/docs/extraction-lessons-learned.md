# Story Mining: Extraction Lessons Learned

Lessons from Phases 0-R8 (setup, test runs, parameter tuning, qualitative comparison).
These inform execution of Phase 2 (day logs) and Phase 3 (sessions).

## Model Selection: Sonnet > Haiku for Extraction

### What we tested
4 conditions (2 models x 2 chunk sizes) on the same source material:
- Day log: day-021 lines 11201-12423 (~1223 lines)
- Session: 06a0 full (522 JSONL lines)

### Key finding: Sonnet captures nuances Haiku misses

Sonnet uniquely identified that the goal is "content recovery for Gemini, NOT console
fidelity" — a critical architectural distinction. Neither Haiku condition elevated this
insight. Sonnet also captured more granular formatting details (truncation thresholds,
interrupted message types, assistant symbol prefix).

**Haiku's weakness**: tends to log agent actions verbatim ("Check exact spacing with
visible characters") rather than extracting the underlying requirement ("tool results
must use 2sp + corner-bracket + content spacing"). In small chunks (100-line sessions),
Haiku sometimes produced zero signal findings — entire chunks of agent-action-logging
noise.

**Sonnet's weakness**: captures individual code lines as separate findings. A 32-finding
chunk where 19 are individual jq conditionals. Mitigated by template tweak (see below).

### Quantitative comparison (corrected from per-finding detail)

| Condition | Total | Signal | Noise | Dup | Signal% | Unique Signal |
|-----------|:-----:|:------:|:-----:|:---:|:-------:|:-------------:|
| R8-H-400  |  58   |   31   |  18   |  9  |   53%   |       0       |
| R8-S-400  | 104   |   46   |  45   | 13  |   44%   |       2       |
| R8-H-200  |  79   |   37   |  33   |  9  |   47%   |       1       |
| R8-S-200  |  97   |   57   |  33   |  7  |   59%   |       6       |

S-200 won on every metric: most signal, best signal%, most unique signal, fewest dups.

## Chunk Size: Smaller is Better (with Sonnet)

### 200-line DL chunks > 400-line

- 61% signal rate (vs 38% for S-400 DL)
- Only 3 within-condition duplicates (vs 9 for S-400)
- Smaller chunks naturally reduce within-condition redundancy
- Thread continuity suffers (topics split across boundaries), but overlap mitigates this

### 100-line session chunks > 200-line

- S-200 captured 20/22 identifiable requirements (91% coverage)
- S-400 captured only 16/22 (73%)
- 4 requirements found exclusively by S-200 (assistant prefix, truncation threshold,
  two interrupted message types, empty line handling)

### Trade-off: scale

S-200 produces ~1156 chunks vs ~602 for S-400. About 2x the subagent invocations.
The quality improvement (59% vs 44% signal, 6 vs 2 unique signal) justifies the cost.

### Sonnet + large chunks = noise explosion

S-400's DL chunk 2 (L11601-12000) produced 32 findings, 19 of which were noise — each
jq code line captured as a separate finding. Large chunks give Sonnet too much room to
over-extract implementation details.

## Overlap Prevents Information Loss

- DL overlap: 50 lines (25% of 200-line chunk)
- Session overlap: 20 lines (20% of 100-line chunk)
- First chunk of each source has no overlap (context_start == primary_start)
- Overlap is READ window only — findings must be in primary range

Overlap helps agents understand threads that span chunk boundaries. Without it, topics
introduced at the end of one chunk would lack context at the start of the next.

## Template Evolution

### Noise reduction tweak (post-R8 qualitative)

Added to "What is NOT relevant" in both templates:
> Individual code snippets: If the agent writes/debugs code, capture WHAT the code does
> (the requirement), NOT HOW it does it. One finding per requirement, not one per code line.

Added to Step 4b (review and revise):
> Code vs requirements: If you created findings for individual code lines, jq conditionals,
> or implementation patterns, DELETE them. Replace with a single finding stating the
> REQUIREMENT the code satisfies.

### Meta-layer diarization (from Phase 1)

Day logs and sessions contain reconstructed output from OTHER sessions. Agents must
distinguish:
- Layer 1: The agent in THIS session (running commands)
- Layer 2: Reconstructed output from another session (inside tool results)
- Layer 3: Expected output files (also contain reconstructed words)

Signs of reconstructed output: text starting with symbols like filled-circle, >, or
corner-bracket inside TOOL_RESULT lines.

### Line number enforcement

Line numbers must be ABSOLUTE (position in source file), not chunk-relative. Enforced by:
1. awk/jq commands that prefix each line with its absolute line number
2. validate-quotes.py checks line numbers are within primary range
3. Self-validation step in template (agent runs validator before returning)

## Subagent Orchestration Lessons

### Path issues
Subagents sometimes write to wrong paths. ALWAYS use absolute paths in prompts:
- `/Users/palimondo/Developer/xs/xs-requirements/findings/filename.yaml`
- NOT `xs-requirements/findings/filename.yaml`

### Timing rule
NEVER validate or summarize results until ALL subagents have returned completion
notifications. Files on disk are NOT proof of completion — agents write YAML in Step 4,
then potentially REWRITE in Steps 4b/5. This error was made twice during testing.

### Context management
NEVER call TaskOutput on completed subagents — it returns the full execution transcript
(including raw source text) and blows up the main agent's context window. Read findings
YAML files directly from disk instead.

### Summary table accuracy
Opus subagents sometimes produce incorrect summary tables even when per-finding
classifications are correct. Always verify aggregate counts by parsing the detail
tables programmatically. The session qualitative agent's summary was off by 20-30%
on every condition; the per-finding classifications were accurate.

### Batch size
12 parallel subagents tested successfully. This is the practical limit for the current
setup.

## Qualitative > Quantitative for Parameter Selection

Raw finding counts are misleading. S-400 had the highest total (104) but the worst
signal rate (44%). The qualitative comparison — actually reading and classifying every
finding — revealed that S-200 was the clear winner despite having fewer total findings
than S-400.

Lesson: when comparing extraction parameters, always do a qualitative sample before
committing to production parameters. A 2-agent Opus qualitative assessment takes ~3-4
minutes and prevents committing to a noisy configuration for hundreds of chunks.
