# xs Requirements Recovery

This directory contains requirements recovered from session history for the xs tool recreation project.

## Status

**Current Pass**: 1 - Structure Bootstrap (COMPLETE)
**Next Pass**: 2 - Story Mining

## Structure

```
xs-requirements/
├── tracker.yaml          # Central status tracking
├── themes/               # 4 high-level use case themes
├── epics/                # 8 functional area epics
├── stories/              # 49 story stubs by epic
│   ├── parsing/          # PRS-* (6 stories)
│   ├── formatting/       # FMT-* (10 stories)
│   ├── filtering/        # FLT-* (11 stories)
│   ├── range/            # RNG-* (5 stories)
│   ├── display/          # DSP-* (5 stories)
│   ├── cli/              # CLI-* (5 stories)
│   ├── search/           # SRC-* (4 stories)
│   └── export/           # EXP-* (3 stories)
├── principles/           # Cross-cutting concerns (Pass 4)
├── constraints/          # Tech stack constraints (Pass 4)
├── conflicts/            # Design conflicts (Pass 5)
├── golden-files/         # Test input/output pairs (Pass 3)
│   ├── 1x/               # Claude Code 1.x format
│   └── 2x/               # Claude Code 2.x format
└── findings/             # Raw search results (Pass 2)
```

## Themes

| ID | Name | Description |
|----|------|-------------|
| github-fetch | GitHub Actions Session Recovery | Recover transcripts from CI runs |
| console-replay | Session Replay and Reconstruction | Reproduce console output for LLM consumption |
| compaction-recovery | Context Recovery After Compaction | Recover details lost in compaction |
| local-exploration | Local Session Exploration | Search, filter, analyze local sessions |

## Epics

| ID | Name | Stories | Status |
|----|------|---------|--------|
| jsonl-parsing | JSONL Parsing and Session Loading | 6 | draft |
| console-formatting | Console Output Formatting | 10 | draft |
| filtering | Content Filtering | 11 | draft |
| range-selection | Timeline Range Selection | 5 | draft |
| display-modes | Display Modes | 5 | draft |
| cli-interface | Command Line Interface | 5 | draft |
| search | Full-Text Search | 4 | draft |
| export | Export Formats | 3 | draft |

## Story Prefixes

| Prefix | Epic |
|--------|------|
| PRS | jsonl-parsing |
| FMT | console-formatting |
| FLT | filtering |
| RNG | range-selection |
| DSP | display-modes |
| CLI | cli-interface |
| SRC | search |
| EXP | export |

## Next Steps

1. **Pass 2: Story Mining** - Fill in story details with sources and acceptance criteria
   - Spawn Haiku subagents to search day logs and sessions
   - Synthesize findings into coherent stories
   - Checkpoint per epic for user validation

2. **Pass 3: Golden Files** - Assemble test input/output pairs

3. **Pass 4: Principles** - Extract cross-cutting concerns

4. **Pass 5: Conflicts** - Resolve design tensions

5. **Pass 6: Slicing** - Order stories for implementation
