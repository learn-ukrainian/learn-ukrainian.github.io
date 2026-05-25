# F2 + F3 batch cleanup — codex

**Date**: 2026-05-24
**Agent**: codex
**Mode**: danger
**Effort**: medium
**Wall budget**: 30 min

## Why

Two carryover P2 items from the 2026-05-24 overnight handoff. Both mechanical, no design judgment needed.

## F2 — Fix .venv cd-guard lint on 5 archived dispatch briefs

The project has a lint rule that flags shell snippets where the `.venv/bin/python` invocation is preceded by an explicit `cd .worktrees/...` without an exemption marker. 5 dispatch briefs under `docs/dispatch-briefs/` fail this lint:

- `docs/dispatch-briefs/2026-05-23-issue-2239-codex-rollout-binding-fix.md`
- `docs/dispatch-briefs/2026-05-23-pr-a-llm-dim-demote-resume-default-codex.md`
- `docs/dispatch-briefs/2026-05-23-pr-b-band-widening-gemini.md`
- `docs/dispatch-briefs/2026-05-23-pr-c-writer-prompt-strip-codex.md`
- `docs/dispatch-briefs/2026-05-23-pr-d1-ask-hermes-ask-opencode-gemini.md`

Per the handoff, the fix is: "add `# venv symlinked` inside offending fences + drop `-x` from 3 pytest commands or add to ALLOWLIST_PYTEST_X."

### Steps

1. Run the lint locally to see exactly what fires:
   ```
   .venv/bin/python scripts/audit/lint_dispatch_briefs.py 2>&1 | head -60
   ```
   (If that script doesn't exist, look for the pre-commit hook that enforces this — `grep -rn "venv\|cd-guard" .pre-commit-config.yaml claude_extensions/hooks/ scripts/audit/`.)
2. For each flagged shell fence in each file, add a `# venv symlinked` comment INSIDE the fence (on the line above the offending `cd`/`.venv` invocation). The marker tells the lint that the brief author has acknowledged the venv-symlink convention is in use.
3. For the 3 pytest commands using `-x`: either remove the `-x` flag (preferred — keeps tests running across failures so we see the full picture) OR add the relevant command to `ALLOWLIST_PYTEST_X` if it's defined somewhere. Grep `ALLOWLIST_PYTEST_X` and `pytest.*-x` to find the policy.
4. Verify by re-running the lint: zero violations after edits.

## F3 — Fix 1 stale test label assertion

`tests/build/test_writer_pre_emit_checklist.py::test_linear_write_contains_pre_emit_checklist` fails because `OBLIGATION_LABELS` includes `"VESUM verification"` and `"Russianism check"` but the post-PR-C-strip `scripts/build/phases/linear-write.md` Pre-emit checklist uses shorter labels: `"VESUM:"` and `"Russianism/style:"`.

### Steps

1. Open `tests/build/test_writer_pre_emit_checklist.py`.
2. Change `OBLIGATION_LABELS = ("Textbook grounding", "Multimedia obligation", "VESUM verification", "Russianism check")` to `OBLIGATION_LABELS = ("Textbook", "Multimedia", "VESUM", "Russianism")`. These topic-keyword substrings are present in BOTH `linear-write.md` (post-strip) AND `linear-write-grok.md` (verbose). Topic-keyword matching is more robust to future label rewording than full-phrase matching.
3. Run both tests:
   ```
   .venv/bin/pytest tests/build/test_writer_pre_emit_checklist.py -v
   ```
   Both `test_linear_write_contains_pre_emit_checklist` and `test_linear_write_grok_contains_pre_emit_checklist` must pass.

## REQUIRED steps (numbered)

1. From the project root: `git fetch origin && git worktree add -b fix/f2-f3-cleanup-2026-05-24 .worktrees/dispatch/codex/f2-f3-cleanup-2026-05-24 origin/main`
2. `cd .worktrees/dispatch/codex/f2-f3-cleanup-2026-05-24 && ln -s ../../../../.venv .venv` (# venv symlinked)
3. Do F2 work (5 files), then F3 work (1 file).
4. Run tests + lint:
   ```
   .venv/bin/pytest tests/build/test_writer_pre_emit_checklist.py -v
   .venv/bin/ruff check tests/build/test_writer_pre_emit_checklist.py docs/dispatch-briefs/ 2>&1 | head -10
   ```
5. Two separate commits (F2 = doc cleanup, F3 = test fix), each conventional.
6. `git push -u origin fix/f2-f3-cleanup-2026-05-24`
7. `gh pr create --base main --title "chore: F2 brief lint + F3 test label cleanup" --body "..."`
8. NO auto-merge.

## Verifiable claims

| Claim | Evidence |
|---|---|
| "5 brief lint violations fixed" | Pre-edit lint output (raw) + post-edit lint output (raw, zero violations) |
| "test_linear_write_contains_pre_emit_checklist passes" | `.venv/bin/pytest` final line raw |
| "Lint clean" | `.venv/bin/ruff check` raw |
| "PR opened" | `gh pr view --json url` raw URL line |

## Anti-fabrication (#M-4)

Every claim tool-backed. Quote raw outputs in PR body.
