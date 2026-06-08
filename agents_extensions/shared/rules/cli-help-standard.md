# CLI `--help` Standard

<critical>

Every CLI script in this repo must emit enough from `--help` that an agent
can use it correctly **without reading the source**. This is load-bearing:
agents waste real time guessing flag names. See #1379 for the backstory.

## When you write a NEW CLI

Your `argparse.ArgumentParser` must include all of:

1. **`description=`** — two lines:
   - What the tool does (one sentence)
   - When to use it (and when NOT to use it)

2. **Every `add_argument()` has a meaningful `help=`**, including:
   - What the arg is / does
   - Default value for optional flags
   - Example value or expected format

3. **`epilog=`** (with `formatter_class=argparse.RawDescriptionHelpFormatter`):
   - 1–3 concrete `.venv/bin/python scripts/…` usage examples for the common cases
   - `Outputs:` — files written, DB updates, side effects
   - `Exit codes:` — what 0 and ≥1 mean
   - `Related:` — the template/prompt it uses, prod version, relevant doc, EPIC/issue

## When you TOUCH an existing CLI

Boy Scout rule — if you're editing the script for any reason and its
`--help` doesn't meet this standard, bring it up to standard in the same
commit. Don't leave it worse than you found it.

## Reference implementation

`scripts/build/pilot_uk_lesson.py` — mirror this pattern.

Run: `.venv/bin/python scripts/build/pilot_uk_lesson.py --help`

## Why this matters

When docs/SCRIPTS.md doesn't cover a flag you need, `--help` is the
source of truth. If `--help` is also thin, the agent guesses, guesses
wrong, wastes a dispatch budget, and has to retry. Seen it enough times
to make it a rule instead of a convention.

## What does NOT need this standard

- Library modules (not invoked as CLI)
- MCP tools / MCP server commands (different interface)
- External wrappers we don't own (gemini, codex, gh)

</critical>
