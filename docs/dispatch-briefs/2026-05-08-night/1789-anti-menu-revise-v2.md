# Dispatch brief v2: revise #1789 anti-menu linter (fixes Claude review's 2 IMPORTANT)

> **PR to revise:** #1789 on branch `codex-1787-1.4-anti-menu-linter` (the live remote branch, NOT a new branch)
> **Origin review:** `gh pr view 1789 --json comments` (Claude headless adversarial review, posted as PR comment)
> **Verdict:** REVISE [OBJECT] — 2 IMPORTANT bugs identified
> **Agent:** Codex
> **Worktree:** **NEW** worktree, branched from existing PR tip; force-push back to PR branch.

## Worktree instructions (mandatory — note the --base)

```bash
.venv/bin/python scripts/delegate.py dispatch \
    --agent codex --mode danger --worktree --base origin/codex-1787-1.4-anti-menu-linter \
    --task-id codex-1789-anti-menu-fix \
    --prompt-file docs/dispatch-briefs/2026-05-08-night/1789-anti-menu-revise-v2.md
```

Lands in `.worktrees/dispatch/codex/codex-1789-anti-menu-fix` on a NEW branch
`codex/1789-anti-menu-fix`. After making fixes locally, **push back to the
ORIGINAL PR branch** (not the new branch):

```bash
git push origin HEAD:codex-1787-1.4-anti-menu-linter --force-with-lease
```

Then DELETE the new branch from origin (it's just a holding area):

```bash
git push origin --delete codex/1789-anti-menu-fix
```

PR #1789 picks up the amendments automatically.

## Issues to fix (from Claude review on PR #1789, full review at the PR comment)

### Issue 1 (IMPORTANT) — AC heading exemption fails on `## Acceptance criteria (numbered, all required)`

**File**: `scripts/audit/lint_anti_menu.py:62` (`_normalize_heading`) and `:130` (heading match)

**Repro**:
```markdown
## Acceptance criteria (numbered, all required)

1) Want me to A, B, or C?    <-- flagged, should be exempt
```

The project's own dispatch briefs use this exact heading format. Promoting #1789 to pre-commit/CI without this fix would block legitimate briefs.

**Fix**: in `_normalize_heading`, strip a trailing parenthetical (everything from the first `(` onwards) before lowercasing:
```python
text = re.sub(r"\s*\([^)]*\)\s*$", "", text).strip().lower()
```

### Issue 2 (IMPORTANT) — META_EXAMPLE_RE only checks same line, false-positive on briefs that quote antipatterns

**File**: `scripts/audit/lint_anti_menu.py:39-43`

**Repro**: `docs/dispatch-briefs/2026-05-08-night/1787-1.4-anti-menu-linter.md:28` is flagged because the antipattern is quoted as documentation, but META_EXAMPLE_RE only checks the violation line, not the section context.

**Fix**: extend lookback ~3 lines for META_EXAMPLE_RE so the "Forbidden patterns:" preamble (or "Anti-pattern:" / similar) is in scope. Combine with adding `Forbidden patterns:` to the existing prefix exemption family.

### Issue 5 (NIT but real false negative) — `NUMBERED_LIST_LINE_RE` only matches `1)` style

**File**: `scripts/audit/lint_anti_menu.py:60`

Standard markdown numbered lists use `1.` not `1)`. Fix: `r"^\s*(?:[-*]\s*)?\d+[.)]\s+\S"`. Add fixture using `1.` style.

### Issue 7 (NIT) — non-utf-8 input crash

**File**: `scripts/audit/lint_anti_menu.py:201`

Wrap `args.text.read_text(encoding="utf-8")` in try/except `UnicodeDecodeError`. Emit `path: not utf-8` and exit 2.

## Out of scope (per Claude review)

- Issue 3 (heading scope-close) — false alarm, not actually broken.
- Issue 4 (mixed-fence `~~~` vs `\`\`\``) — edge-case-only.
- Issue 6 (DIRECT_QUESTION_RE requires `or` connector) — rare phrasing.
- Issue 8 (test style consistency with #1788) — both styles fine.

## Acceptance criteria

1. `## Acceptance criteria (numbered, all required)` heading correctly exempts menu inside (Issue 1)
2. Linter run against `docs/dispatch-briefs/2026-05-08-night/1787-1.4-anti-menu-linter.md` exits 0 (Issue 2)
3. `1.` style numbered menus ARE flagged (Issue 5)
4. Non-utf-8 input handled gracefully, exit 2 (Issue 7)
5. New test fixtures pin all 4 behaviors above
6. ALL existing tests still pass
7. `ruff check` clean
8. **Validation pass**: linter run against all `docs/session-state/*.md` should still produce the original 1 violation; linter run against all `docs/dispatch-briefs/**/*.md` produces NO false positives

## Numbered execution steps

1. `git worktree add` — handled by delegate runner via `--base origin/codex-1787-1.4-anti-menu-linter`.
2. Read the full Claude review at `gh pr view 1789 --json comments | jq -r '.comments[] | select(.body | contains("Claude headless")) | .body'`.
3. Implement Issue 1 fix in `_normalize_heading`.
4. Add test fixture for `## Acceptance criteria (numbered, all required)`.
5. Implement Issue 2 fix (META_EXAMPLE_RE lookback + prefix exemption).
6. Add test fixture for "Forbidden patterns:" enumeration.
7. Implement Issue 5 fix (`1.` style support).
8. Add test fixture for `1.` style.
9. Implement Issue 7 fix (utf-8 try/except).
10. Add test for non-utf-8 input.
11. `.venv/bin/ruff check scripts/audit/lint_anti_menu.py tests/audit/test_lint_anti_menu.py`
12. `.venv/bin/pytest tests/audit/test_lint_anti_menu.py -x`
13. **Validation pass**: run linter against all `docs/dispatch-briefs/**/*.md` and `docs/session-state/*.md`. Confirm the validation criteria above.
14. Commit: `fix(guardrail): anti-menu linter handles parenthesized AC headings + multi-line forbidden-pattern context (#1787)`
15. **Push to ORIGINAL PR branch**: `git push origin HEAD:codex-1787-1.4-anti-menu-linter --force-with-lease`
16. **Delete the new branch**: `git push origin --delete codex/1789-anti-menu-fix`
17. Comment on PR #1789: `gh pr comment 1789 --body "Revised per Claude review: Issues 1, 2, 5, 7 fixed. Issues 3, 4, 6, 8 deferred per brief. Validation: 0 false positives on dispatch-briefs corpus, original 1 historical violation in session-state corpus retained."`
18. Print "PR #1789 amended successfully — claude review issues 1+2 fixed".

## Why the v2 brief

The v1 brief (`1789-anti-menu-revise.md`) failed at worktree-prep because the delegate runner expected `--worktree EXISTING_PATH` to have a branch matching the new task-id. v2 creates a NEW worktree off the existing PR's tip, then force-pushes back. This is the supported topology.
