# xs Recreation Project

## Project Goal

Recreate the xs (explore-session) tool from scratch using strict TDD, recovering original requirements from session history rather than trusting the existing vibe-coded implementation.

## Background: What xs Is For

xs is a CLI tool with four primary use cases:

1. **Fetch sessions from GitHub Actions** - Recover Claude Code transcripts from CI runs where you can't copy from terminal (original raison d'être)

2. **Session replay/reconstruction** - Reproduce Claude Code console output faithfully so it can be fed to other LLMs (like Gemini) for summarization. Console fidelity is critical because the output must be parseable by another AI.

3. **Compaction recovery** - When Claude Code compacts context (automatically or via `/compact`), crucial details are lost in the summary. xs recovers full details from the raw transcript. Intended to be automated via hooks.

4. **Local session exploration** - Search, filter, and analyze session transcripts for debugging, context recovery, and understanding what happened in past sessions.

**Cross-LLM workflow**: Run Claude Code → Use xs to fetch/replay session → Feed output to Gemini → Get high-level summary stored in `claude-dev-log-diary/`

**Compaction recovery workflow**: Compaction occurs → Hook triggers → xs finds compaction point → Recovers critical context

## The Trust Problem

The current xs implementation in BookMinder:
- Was vibe-coded without TDD discipline
- Grew larger than BookMinder itself as a side project
- Has characterization specs added post-hoc (unknown quality)
- Is in inconsistent state due to Claude Code format changes (1.x → 2.x)
- Has low trust from the maintainer

**Approach**: Recover requirements from session history, validate with user, then implement fresh with strict TDD.

---

## Source References

Two types of sources exist with different access patterns:

### Day Logs (claude-dev-log-diary/)

Large markdown files capturing full session output. **Very large** (day-020.md is 2.6MB, day-021.md is 713KB).

**Access method**: Use `rg` (ripgrep) with context, never load entire file.

```bash
rg -n "explore_session" day-020.md -C 3
rg -n "formatting" day-021.md -B 2 -A 5
```

**Reference format**: `day-###:L{start}-L{end}`

```yaml
sources:
  - file: day-020:L1234-L1256
    quote: "should show Bash(command) not Bash: $ command"
    context: "user correcting tool output format"
```

### Session Transcripts (~/.claude/projects/)

JSONL files containing raw session data. Explore with xs tool.

```bash
xs abc123 -S "formatting" -C 5
xs abc123 -U  # User messages only
xs abc123 -t 45-60 --full
```

**Reference format**: `{uuid-prefix}:{event-range}`

```yaml
sources:
  - session: e583f2a1:45-52
    quote: "I want to filter to show only user messages"
    context: "user requesting -U flag"
    
  - session: 7d2b91c4:120
    type: user_correction
    quote: "no, exclude should work with glob patterns"
```

### Cross-Reference Between Sources

Day logs and session transcripts cover the same work from different angles. Correlate via timestamps:

```bash
# Find commit from xs development
git log --oneline --after="2024-12-15" --before="2024-12-20" -- "*explore*"

# Find corresponding session by date
ls -la ~/.claude/projects/-Users-*/  # Check timestamps
```

---

## Requirements Gathering: Six-Pass Process

Requirements are fully gathered before implementation begins. No interleaving.

### Requirements Artifact Structure

```
xs-requirements/
├── README.md                    # Process overview, status
├── tracker.yaml                 # Central status tracking
│
├── themes/
│   ├── github-fetch.yaml
│   ├── console-replay.yaml
│   ├── compaction-recovery.yaml
│   └── local-exploration.yaml
│
├── epics/
│   ├── jsonl-parsing.yaml
│   ├── console-formatting.yaml
│   ├── filtering.yaml
│   ├── range-selection.yaml
│   ├── display-modes.yaml
│   └── cli-interface.yaml
│
├── stories/
│   ├── parsing/
│   │   ├── PRS-001-load-session.yaml
│   │   └── ...
│   ├── formatting/
│   │   ├── FMT-001-user-message.yaml
│   │   └── ...
│   └── .../
│
├── principles/
│   ├── PRIN-001-console-fidelity.yaml
│   ├── PRIN-002-format-robustness.yaml
│   └── PRIN-003-graceful-degradation.yaml
│
├── constraints/
│   ├── tech-stack.yaml
│   └── dependencies.yaml
│
├── conflicts/
│   └── CONF-001-format-1x-vs-2x.yaml
│
└── golden-files/
    ├── 1x/
    │   ├── session-fragment.jsonl
    │   ├── session-fragment.compact.txt
    │   ├── session-fragment.truncated.txt
    │   └── session-fragment.full.txt
    └── 2x/
        └── .../
```

### Story YAML Format

```yaml
# stories/formatting/FMT-004-bash-tool.yaml

id: FMT-004
title: Bash tool display format
epic: console-formatting
theme: console-replay

as_a: developer reviewing session output
i_want: bash commands displayed matching Claude Code console
so_that: output is recognizable and parseable by other LLMs

sources:
  - file: day-021:L2045-L2058
    quote: "should show Bash(command) not Bash: $ command"
    context: "user correcting tool output format"
  - session: 7d2b91c4:89-93
    quote: "fixing tool output to match CC exactly"
    type: design_rationale

acceptance_criteria:
  - id: FMT-004-AC1
    given: Bash tool_use entry in JSONL
    when: rendered in truncated mode
    then: "⏺ Bash({command})" on first line
    golden: golden-files/1x/bash-simple.yaml
    
  - id: FMT-004-AC2
    given: Bash tool_result entry
    when: rendered in truncated mode
    then: indented with "⎿" prefix, max 3 lines + "… +N lines"
    golden: golden-files/1x/bash-with-output.yaml

depends_on:
  - PRS-001  # Must parse JSONL first
  
related:
  - PRIN-001  # Console fidelity principle
  - FMT-005   # Other tool formats

priority: must  # must | should | could
status: draft   # draft | mined | reviewed | validated
validation_notes: null
```

### Principle YAML Format

```yaml
# principles/PRIN-001-console-fidelity.yaml

id: PRIN-001
title: Console Output Fidelity for LLM Consumption

statement: |
  xs output must faithfully reproduce Claude Code console appearance
  because the primary consumer is another LLM (Gemini) that needs to
  understand the session content.

rationale:
  - file: day-020:L3456-L3470
    quote: "feeding session to Gemini for summarization"
  - session: e583f2a1:234
    quote: "Gemini can understand the session from this output"

implications:
  - Use identical symbols to CC (⏺, >, ⎿, ✻)
  - Match indentation and spacing exactly
  - Remove interactive-only elements ("ctrl+r to expand")
  - Preserve message chronological ordering
  - Truncation patterns must match CC

applies_to:
  - FMT-*  # All formatting stories
  
conflicts:
  - CONF-001  # 1.x vs 2.x format differences

status: draft
```

### Conflict YAML Format

```yaml
# conflicts/CONF-001-format-1x-vs-2x.yaml

id: CONF-001
title: Claude Code 1.x vs 2.x Output Format Differences

description: |
  Claude Code's console output evolved between 1.x and 2.x.
  Golden files exist for 1.x era. User wants "period appropriate"
  output but this creates complexity.

evidence:
  1x:
    - observation: "Tool format: Bash: $ command"
      golden: golden-files/1x/bash-tool.txt
      
  2x:
    - observation: "Tool format: Bash(command)"
      golden: golden-files/2x/bash-tool.txt

options:
  - id: A
    name: "Always 2.x style"
    pros: [simpler, forward-compatible]
    cons: [historical sessions look different]

  - id: B
    name: "Period-appropriate (auto-detect)"
    pros: [historical accuracy]
    cons: [two code paths]

  - id: C
    name: "User flag --format-style=1x|2x|auto"
    pros: [flexibility]
    cons: [complexity, decision burden]

resolution: pending
decided_by: null
decision_rationale: null

affects:
  - FMT-003
  - FMT-004
  - PRIN-001
```

### Tracker YAML Format

```yaml
# tracker.yaml

meta:
  last_updated: 2026-01-04T15:30:00Z
  current_pass: 2_story_mining
  current_epic: console-formatting

passes:
  1_structure_bootstrap:
    status: complete
    completed_at: 2026-01-04T10:00:00Z
    
  2_story_mining:
    status: in_progress
    epics:
      jsonl-parsing: complete
      console-formatting: in_progress
      filtering: pending
      range-selection: pending
      display-modes: pending
      cli-interface: pending
      
  3_golden_files:
    status: pending
    
  4_principles:
    status: pending
    
  5_conflicts:
    status: pending
    
  6_slicing:
    status: pending

counts:
  stories:
    total: 52
    draft: 40
    mined: 8
    reviewed: 3
    validated: 1
  conflicts:
    pending: 1
    resolved: 0

next_action: |
  Continue story mining for console-formatting epic.
  Use subagents to search day-020, day-021 for formatting requirements.

blockers: []
```

---

## Pass Details

### Pass 1: Structure Bootstrap
**Goal**: Create skeleton from known information (no session mining yet)

**Method**:
1. Create directory structure
2. Themes from the four use cases
3. Epics from filtering pipeline architecture
4. Story stubs from existing characterization spec names
5. Initialize tracker

**Output**: Skeleton with ~50 empty story stubs
**Checkpoint**: User confirms structure

### Pass 2: Story Mining (Per Epic)
**Goal**: Fill in stories with sources and acceptance criteria

**Parallelization**: Safe to parallelize search phase.

```
┌─────────────────────────────────────────────────────────────┐
│ OPUS (Coordinator)                                          │
│                                                             │
│  For each epic:                                             │
│    ┌─────────────────────────────────────────────────────┐ │
│    │ PARALLEL: Spawn Haiku subagents for search          │ │
│    │                                                     │ │
│    │  Haiku A: rg "{epic}" day-015..day-018             │ │
│    │  Haiku B: rg "{epic}" day-019..day-022             │ │
│    │  Haiku C: xs sessions from that period              │ │
│    │                                                     │ │
│    │  Returns: FINDINGS (raw extracts + citations)       │ │
│    └─────────────────────────────────────────────────────┘ │
│                          │                                  │
│                          ▼                                  │
│    ┌─────────────────────────────────────────────────────┐ │
│    │ SERIAL: Opus synthesizes findings into stories      │ │
│    │                                                     │ │
│    │  - Deduplicate overlapping findings                 │ │
│    │  - Resolve contradictions                           │ │
│    │  - Add cross-references                             │ │
│    │  - Write coherent YAML                              │ │
│    └─────────────────────────────────────────────────────┘ │
│                          │                                  │
│                          ▼                                  │
│    User validates epic before proceeding                    │
└─────────────────────────────────────────────────────────────┘
```

**Subagent output format** (findings, NOT stories):

```yaml
task: "Search for filtering requirements"
epic: filtering
sources_searched: 
  - day-016:L1-L5000
  - day-017:L1-L8000
  - session: abc123

findings:
  - id: F001
    source: day-016:L2341-L2355
    type: user_request
    quote: "I want to filter to show only user messages"
    tags: [filter, shortcut, user-messages]
    
  - id: F002
    source: abc123:89-93
    type: user_correction
    quote: "no, exclude should work with glob patterns"
    supersedes: F001
    tags: [filter, exclude, patterns]

ambiguities:
  - "Conflicting statements about -x accepting multiple args"

coverage_gaps:
  - "No findings about error handling for invalid patterns"
```

**Model selection**:
- Haiku: Session search, day log grep (fast, cheap, extraction)
- Sonnet: Ambiguity resolution (needs reasoning)
- Opus: Synthesis, cross-references (coherence-critical)

**Checkpoint**: User reviews each epic before next

### Pass 3: Golden File Assembly
**Goal**: Concrete input/output pairs for specs

**Method**:
1. Gather existing golden files from old implementation
2. Organize by format version (1x/ vs 2x/)
3. For stories without golden files: create from real sessions
4. Link golden files to acceptance criteria
5. Mark for user validation

**Parallelization**: Safe (independent file generation)

**Checkpoint**: User validates golden file correctness

### Pass 4: Principles & Constraints Extraction
**Goal**: Extract cross-cutting concerns

**Method**:
1. Review stories for repeated patterns → principles
2. Scan BookMinder for tech stack → constraints
3. Review sessions for stated design rationale
4. Cross-reference principles with affected stories

**Parallelization**: Not safe (needs global view)

**Checkpoint**: User validates principles

### Pass 5: Conflict Resolution
**Goal**: Surface and resolve design tensions

**Method**:
1. Review stories for contradictions
2. Document 1.x vs 2.x conflict explicitly
3. Present options with evidence to user
4. Document resolutions with rationale
5. Update affected stories and principles

**Parallelization**: Not safe (needs global view + user decisions)

**Checkpoint**: User makes design decisions

### Pass 6: Implementation Slicing
**Goal**: Order stories for optimal TDD implementation

**Method**:
1. Identify walking skeleton (minimal end-to-end)
2. Group stories by dependency
3. Apply priority (must/should/could)
4. Map to spec files
5. Create implementation roadmap

**Output**: Prioritized backlog with phases

**Checkpoint**: User confirms implementation order

---

## Tech Stack (from BookMinder)

- Python environment and dependency management matching BookMinder
- pytest with BDD-style spec organization (`describe_*/it_*` naming)
- GitHub Actions with Claude Code Action integration
- `gh` CLI for GitHub operations

---

## Available Resources

### Primary Sources (Requirements Recovery)
- Session transcripts in `~/.claude/projects/`
- Day logs in `BookMinder/claude-dev-log-diary/` (especially day-020, day-021)
- Use xs itself to explore sessions (meta!)

### Secondary Sources (LOW TRUST)
- Design docs in `BookMinder/claude-dev-log-diary/tools/*.md`
- Existing implementation `explore_session.py`
- Characterization specs in `specs/`

### Reference Documentation
- `claude_code_jsonl_format_reference.md` - Format specification
- `exploring-sessions` skill in BookMinder

---

## What NOT To Do

- Do NOT trust existing implementation or specs as authoritative
- Do NOT copy code (understand requirements → implement fresh)
- Do NOT add features not in recovered requirements
- Do NOT interleave requirements gathering with implementation
- Do NOT load entire day log files into context (use ripgrep)
