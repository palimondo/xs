# BUG-002: Search combined with timeline flag ignores search

## Problem

When `-t` (timeline) is combined with `-S` (search), the search is completely ignored.

## Evidence

```bash
$ xs e583 -S "filter"        # Works: "Found 124 matches for 'filter':"
$ xs e583 -S "filter" 1-100  # Works: "Found 11 matches for 'filter':" (limited range)
$ xs e583 -S "filter" -t     # BUG: Shows ALL timeline entries, not filtered!
$ xs e583 -t -S "filter"     # BUG: Same - shows ALL entries
```

**Expected**: `-S "term" -t` should show timeline entries that match the search.
**Actual**: `-t` completely overrides `-S`, showing all entries.

## Workaround

NEVER combine `-S` with `-t`. Use these alternatives:

```bash
# For search with context:
$ xs session -S "term" -C 2          # Search mode with context lines

# For search limited to range:
$ xs session -S "term" 1-500         # Search within range (no -t!)

# For browsing timeline:
$ xs session -t +50 --truncated      # Timeline mode (no search)
```

## Related Story

SRC-005: Search results displayed in timeline mode

## Mining Agent Notes

CRITICAL: Never use `-S` and `-t` together. Results will be wrong.
- Use `-S` alone for searching
- Use `-t` alone for browsing
- Use `-S` with range for scoped search
