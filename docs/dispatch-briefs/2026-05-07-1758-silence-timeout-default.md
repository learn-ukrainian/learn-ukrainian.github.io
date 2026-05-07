# Codex dispatch brief — #1758 silence-timeout default 600→1800

> **Worktree:** `.worktrees/dispatch/codex/1758-silence-timeout-default`
> **Branch:** `codex/1758-silence-timeout-default`
> **Base:** `main`
> **Mode:** danger
> **Effort:** low
> **Hard timeout:** 1200s (20 min)

## Worktree instructions (mandatory)

```bash
git worktree add -b codex/1758-silence-timeout-default .worktrees/dispatch/codex/1758-silence-timeout-default
cd .worktrees/dispatch/codex/1758-silence-timeout-default
```

Main checkout stays on `main`. Don't branch in main checkout.

## Goal

Per #1758 ACs:

- [ ] Default `--silence-timeout` raised from 600s to 1800s (30 min)
- [ ] `--help` text updated to reflect new default + the trade-off
- [ ] Document trade-off in `docs/best-practices/agent-bridge.md`

## Why this matters

Substantive Codex dispatches involve thinking phases, multi-file refactors, and long test runs that produce 10+ minutes of stdout silence as normal behavior. The 600s default kills them mid-stride. Recent victim: `1725-verbatim-quoting` killed at 12 min with 2/3 phases committed and 1 phase 170 lines dirty + salvageable.

1800s still catches genuine OAuth hangs (those manifest in minutes-not-hours) but tolerates real Codex work. Operators who need tighter watchdog can pass `--silence-timeout 600` explicitly.

## Files to touch

- `scripts/delegate.py` — change the argparse default for `--silence-timeout`
- Whatever module holds the per-CLI silence detection from PR #1753 (#1750) — verify the per-CLI defaults are also reasonable after this change
- `--help` text in delegate.py
- `docs/best-practices/agent-bridge.md` — new "Silence-timeout vs hard-timeout" section explaining the trade-off

## Tests

- Update any existing test that asserts `silence_timeout_s == 600` for the default case.
- Add `test_silence_timeout_default_is_1800` if missing.
- Regression: `test_explicit_silence_timeout_override_still_works` — passing `--silence-timeout 600` explicitly produces the 600s value.

## Validation

```bash
.venv/bin/pytest tests/ -k "silence_timeout or delegate" -v
.venv/bin/python scripts/delegate.py dispatch --help | grep silence-timeout  # should show 1800 as default
.venv/bin/ruff check scripts/delegate.py
```

## PR

Open as `fix(delegate): bump --silence-timeout default 600s → 1800s (#1758)`.

PR body includes:
- One-paragraph rationale (why 600s killed real Codex work)
- The 1725-verbatim-quoting incident as evidence
- Confirmation that `--silence-timeout 600` override still works
- `Closes #1758`

**NO auto-merge.** Orchestrator (Claude) reviews + merges.
