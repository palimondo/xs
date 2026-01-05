# xs Usage Best Practices for Mining Agents

## Native Features vs Unix Pipe Chaining

### Range Selection (use native, avoid head/tail)

| Inefficient | Efficient | Notes |
|-------------|-----------|-------|
| `xs session -t \| head -10` | `xs session -t +10` | First N items |
| `xs session -t \| tail -5` | `xs session -t -- -5` | Last N items (note `--` separator) |
| `xs session -t \| head -50 \| tail -20` | `xs session -t 30-50` | Range selection |

**Range syntax reference**:
- `+N` - First N items
- `-N` - Last N items (requires `--` before to avoid flag parsing)
- `N` - Single item at index N
- `N-M` - Range from N to M (inclusive)
- `N+` - From N onwards to end

### Output Limiting

| Inefficient | Efficient | Notes |
|-------------|-----------|-------|
| `xs session -t --full \| head -100` | Use `--truncated` mode | Full mode is verbose by design |
| `xs session -S "term" \| head -50` | Use `-C 1` not `-C 5` | Smaller context = less output |

### Filtering (use native, avoid grep)

| Inefficient | Efficient | Notes |
|-------------|-----------|-------|
| `xs session -t \| grep "user"` | `xs session -t -U` | User messages only |
| `xs session -t \| grep -v "Tool"` | `xs session -t -x Tool` | Exclude tools |
| `xs session -t \| grep "Bash"` | `xs session -t -i Bash` | Include specific tool |

### When Unix Chaining IS Appropriate

- `\| wc -c` - Measuring output size (no native equivalent)
- `\| wc -l` - Counting lines (no native equivalent)
- `2>&1` - Capturing stderr for error handling
- Complex regex filtering not supported by `-S`

---

## Known Bugs and Workarounds

### BUG-001: Search patterns starting with `-`

**Problem**: `-S "-x"` fails because argparse interprets `-x` as a flag.

**Error**:
```
usage: xs [-h] [-s] [-t] ...
```

**Workarounds**:
1. Use `=` syntax: `-S="-x"` or `--search="-x"` ✓
2. Search for alternative term: `-S "exclude"` instead of `-S "-x"`

**Documented**: Yes, in `--help`: "For patterns starting with --, use -S=pattern"

**Story impact**: None needed, behavior is correct and documented.

### BUG-002: Search is ignored when combined with -t flag (CONFIRMED)

**Problem**: When `-t` (timeline) is combined with `-S` (search), the search is completely ignored.

**Evidence**:
```
xs e583 -S "filter"        → "Found 124 matches for 'filter':"  ✓
xs e583 -S "filter" 1-100  → "Found 11 matches for 'filter':"   ✓
xs e583 -S "filter" -t     → Shows ALL timeline entries         ✗ BUG
xs e583 -t -S "filter"     → Shows ALL timeline entries         ✗ BUG
```

**Expected**: `-S "term" -t` should show timeline entries that match the search.
**Actual**: `-t` completely overrides `-S`, showing all entries.

**Workaround**:
1. Use `-S` alone (without `-t`) - this is the search mode
2. Use range syntax with `-S` to limit scope: `-S "term" 1-500`
3. Do NOT combine `-S` with `-t`

**Story impact**: Need story for correct -S/-t interaction behavior.
Candidate: SRC-005-search-timeline-interaction.yaml

---

## Efficient Patterns for Common Mining Tasks

### Task: Get event count for a session
```bash
# INEFFICIENT: xs session -t | tail -1
# Parses entire session, outputs everything, then takes last line

# EFFICIENT: xs session -t -- -1
# Native: only outputs last event (still parses all, but less output)

# MOST EFFICIENT: xs session
# Summary mode shows tool counts (close proxy for event count)
```

### Task: Find specific content in session
```bash
# EFFICIENT: xs session -S "search term" -C 2
# Native search with context

# For patterns with special chars:
xs session -S="--flag" -C 2
xs session --search="pattern-with-dashes" -C 2
```

### Task: Get user requirements only
```bash
# EFFICIENT: xs session -t -U --truncated
# Shows only user messages in compact form

# With search:
xs session -S "requirement" -U -C 1
```

### Task: Get conversation without tools
```bash
# EFFICIENT: xs session -t -M -x Tool
# All messages, exclude tools

# Alternative:
xs session -t -U -a -x Tool
# User + Assistant, exclude tools
```

### Task: Export for analysis
```bash
# For JSON processing:
xs session -t --json > output.json

# For line-by-line processing:
xs session -t --jsonl > output.jsonl
```

---

## Template for Mining Agent Instructions

```
Search session {session_id} for requirements related to {epic}.

CRITICAL xs usage rules:
1. NEVER combine -S with -t (BUG: -t ignores search completely)
2. Use -S alone for search: `xs session -S "term" -C 2`
3. Use -S with range to limit scope: `xs session -S "term" 1-500`
4. For patterns with dashes: use -S="pattern" not -S "pattern"
5. Use native range syntax: +N (first N), -- -N (last N), N-M (range)
6. Prefer -U/-a/-M shortcuts over piping to grep
7. Use -C 1 or -C 2 for context (not -C 5+ which bloats output)

Commands for SEARCHING (use -S, never with -t):
- `xs {session} -S "{term}" -C 2` for topic search (full session)
- `xs {session} -S "{term}" 1-500` for search limited to range
- `xs {session} -S="{term-with-dashes}" -C 2` for patterns starting with -

Commands for BROWSING (use -t, no search):
- `xs {session} -t -U --truncated` for user messages
- `xs {session} -t +50 --truncated` for first 50 events
- `xs {session} -t -- -20` for last 20 events

Extract findings with event number, exact quote, type classification.
Report: finding count, any errors, coverage gaps.
```

---

## Summary of Inefficiencies Found in Session 84db

| Invocation | Issue | Better Alternative |
|------------|-------|-------------------|
| `xs session \| head -3` | Piping to head | Just use summary mode, accept output |
| `xs session -t \| tail -5` | Piping to tail | `xs session -t -- -5` |
| `xs session -t \| head -100` | Piping to head | `xs session -t +100` |
| `xs session -S "-x"` | Pattern with dash | `xs session -S="-x"` |
| `xs session \| grep "Total"` | Piping to grep | No efficient alternative for summary parsing |

**Legitimate chaining uses**:
- `| wc -c` for size measurement (testing)
- `2>&1` for error capture
