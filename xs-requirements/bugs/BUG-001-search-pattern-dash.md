# BUG-001: Search patterns starting with dash fail

## Problem

When using `-S` with a pattern that starts with `-`, argparse interprets it as a flag.

## Evidence

```bash
$ xs e583 -S "-x"
usage: xs [-h] [-s] [-t] ...
xs: error: unrecognized arguments: -x
```

## Workaround

Use `=` syntax to attach the pattern directly:

```bash
$ xs e583 -S="-x"        # Works
$ xs e583 --search="-x"  # Works
```

Alternatively, search for an alternative term:
```bash
$ xs e583 -S "exclude"   # Instead of -S "-x"
```

## Documented

Yes - documented in `xs --help`: "For patterns starting with --, use -S=pattern"

## Related Story

None needed - behavior is correct and documented.

## Mining Agent Notes

Always use `-S="pattern"` syntax when searching for patterns that might start with `-`.
