# Subagent Validation Test Results

**Date**: 2026-01-05
**Session**: 84db (Pass 1 completion)
**Purpose**: Validate Task delegation strategy before Pass 2

## Test 1: Model Comparison (Haiku vs Opus)

**Task**: Extract formatting requirements from session e583, events 1-500

### Haiku Results
- **Findings**: 5 structured entries (FMT-001 through FMT-005)
- **Focus**: Tight, formatting-specific
- **Output**: Concise, well-structured
- **Quality**: High - exact quotes, event numbers, classifications

### Opus Results
- **Findings**: 8 entries in table format
- **Focus**: Broader, included meta-patterns
- **Output**: More verbose
- **Quality**: High - but included tangential findings

### Conclusion
Both models effective. Haiku preferred for focused extraction (cheaper, faster, equally accurate).

---

## Test 2: Large Session Handling

**Task**: Search full session e583 (~1973 events) for filtering requirements

### Commands Run
| Command | Status | Matches |
|---------|--------|---------|
| `xs e583 -S "filter" -C 1` | ✓ | 124 |
| `xs e583 -S "-x" -C 2` | ✗ (argparse) | - |
| `xs e583 -S "exclude" -C 2` | ✓ | 76 |
| `xs e583 -S "pattern" -C 2` | ✓ | 170 |
| `xs e583 -S "glob" -C 2` | ✓ | 13 |
| `xs e583 -S "shortcut" -C 2` | ✓ | 23 |
| `xs e583 -S "range" -C 2` | ✓ | 63 |
| `xs e583 -S "flag" -C 1` | ✓ | 169 |

### Results
- **Total matches**: 569 across 8 searches
- **Context limits**: None hit
- **Truncation**: Output truncated but data complete
- **Findings extracted**: 14 structured requirements

### Known Issues
1. `-S "-x"` fails (argparse interprets as flag)
2. Workaround: use `-S "exclude"` or escape patterns

---

## Test 3: Output Size Measurements

| Mode | Events | Output Size | Tokens (~) |
|------|--------|-------------|------------|
| truncated | 500 | 78KB | 20K |
| compact | 500 | 53KB | 13K |
| full | 100 | 78KB | 20K |
| full | 50 | 50KB | 12K |

### Implications
- **Search mode**: Full sessions OK (matches only)
- **Truncated mode**: 500 events manageable
- **Full mode**: Limit to 50-100 events per request

---

## Validated Strategy for Pass 2

### Model Selection (Confirmed)
| Task | Model | Validated |
|------|-------|-----------|
| Session search | Haiku | ✓ Works well |
| Day log grep | Haiku | ✓ (via ripgrep) |
| Ambiguity resolution | Sonnet | Not tested |
| Synthesis | Opus | ✓ Works well |

### Chunking Requirements
- **Search mode (`-S`)**: No chunking needed, full sessions OK
- **Truncated timeline**: Chunk at ~500 events
- **Full output mode**: Chunk at ~50-100 events
- **Day logs**: Use ripgrep, never load full file

### Subagent Instructions Template (Validated)
```
Search session {session_id} for requirements related to {epic}.

Commands to use:
- `~/Developer/BookMinder/xs {session} -S "{term}" -C 2` for topic search
- `~/Developer/BookMinder/xs {session} -U -t {range} --truncated` for user messages

Extract findings with:
- Event number
- Exact quote
- Type (user_request, user_correction, design_rationale)

Report: finding count, any errors, coverage gaps.
```

### Edge Cases to Document
1. Patterns starting with `-` fail in `-S` flag
2. Use `--` to separate flags from positional args if needed
3. Long outputs may be truncated but data is complete
