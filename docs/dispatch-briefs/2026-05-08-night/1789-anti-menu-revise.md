# Dispatch brief: revise #1789 anti-menu linter (Claude review found 2 IMPORTANT bugs)

> **PR to revise:** #1789 (in-flight, branch `codex-1787-1.4-anti-menu-linter`)
> **Origin review:** `/tmp/claude-review-1788-1789-report.md` (full review preserved)
> **Verdict:** REVISE — 2 IMPORTANT issues + several NITs
> **Agent:** Codex (mechanical regex/parser fix)
> **Worktree:** existing worktree at `.worktrees/dispatch/codex/1787-1.4-anti-menu-linter`

## Worktree instructions (continue existing worktree)

The worktree from the original #1789 PR is still on disk. Continue work there:

```bash
.venv/bin/python scripts/delegate.py dispatch \
    --agent codex --mode danger --worktree .worktrees/dispatch/codex/1787-1.4-anti-menu-linter \
    --task-id codex-1787-1.4-anti-menu-revise \
    --prompt-file docs/dispatch-briefs/2026-05-08-night/1789-anti-menu-revise.md
```

Branch is already `codex-1787-1.4-anti-menu-linter`. Push amendments to the same branch — the existing PR #1789 picks them up automatically.

## What to fix (in order)

### Issue 1 (IMPORTANT) — AC heading exemption fails on `## Acceptance criteria (numbered, all required)`

**File**: `scripts/audit/lint_anti_menu.py:62` (`_normalize_heading`) and `:130` (`heading_text == "acceptance criteria"`)

**Reproduction** (verified by Claude review):
```markdown
## Acceptance criteria (numbered, all required)

1) Want me to A, B, or C?    <-- flagged, should be exempt
```
produces `EXIT=1`. The same content under `## Acceptance criteria` produces `EXIT=0`.

**Why this matters:** The project's own dispatch briefs use `## Acceptance criteria (numbered, all required)`. Including the brief that authored this PR. Promoting #1789 to pre-commit/CI without this fix would block legitimate briefs.

**Fix:**
1. Modify `_normalize_heading` to strip a trailing parenthetical (everything from the first `(` onwards) before lowercasing: e.g. `re.sub(r"\s*\(.*\)\s*$", "", text)`.
2. OR change the comparison: `heading_text == "acceptance criteria" or heading_text.startswith("acceptance criteria ") or heading_text.startswith("acceptance criteria(")`.
3. Prefer option (1) — cleaner, also fixes any future `(detail)` heading suffix.

### Issue 2 (IMPORTANT) — META_EXAMPLE_RE only checked on the same line, false-positives on briefs that enumerate forbidden patterns

**File**: `scripts/audit/lint_anti_menu.py:39-43` (`META_EXAMPLE_RE`)

**Reproduction** (verified by Claude review): running the linter on this very brief's predecessor `docs/dispatch-briefs/2026-05-08-night/1787-1.4-anti-menu-linter.md` produces `line 28: anti-menu pattern detected — 'Want me to A, B, or C?'` because META_EXAMPLE_RE only checks the violation line, not the section context.

The bullets that enumerate the antipatterns sit under a "Forbidden patterns:" preamble but META_EXAMPLE_RE never sees that preamble line.

**Fix** — pick one or combine:
1. Extend lookback ~3 lines for META_EXAMPLE_RE so the preamble is in scope.
2. Detect that the matched span is fully inside paired quotes (`"…"`) and exempt those (the antipattern enumerations are quoted strings).
3. Add a `Forbidden patterns:` / `Anti-pattern:` prefix to the existing prefix exemption family.

Prefer (1) + (3) combined.

### Issue 5 (NIT, but real false negative) — `NUMBERED_LIST_LINE_RE` only matches `1)` style

**File**: `scripts/audit/lint_anti_menu.py:60`

Standard markdown numbered lists use `1.` not `1)`. The "Sign off on these N options:" check only succeeds when the followup uses the rarer `1) … 2) …` style. So a real menu like:
```
Sign off on these 3 options:
1. Ship the guardrail
2. Wait for another review
3. Defer the issue
```
would NOT be detected. The fixture in the test only happens to use `1)` style.

**Fix:** `r"^\s*(?:[-*]\s*)?\d+[.)]\s+\S"`

Add a fixture using `1.` style to lock in the behavior.

### Issue 7 (NIT) — non-utf-8 input crash

**File**: `scripts/audit/lint_anti_menu.py:201` (`args.text.read_text(encoding="utf-8")`)

Wrap in try/except `UnicodeDecodeError` and emit `path: not utf-8` with exit code 2. Also fix the same bug in `scripts/audit/lint_dispatch_brief.py:104` (same pattern, file-1788 has it too) — Boy Scout while you're in the area.

**Note:** #1788 was already merged. Fixing in #1789 worktree means a small follow-up PR (or fold the fix here for ergonomics — explain in the commit if you do).

## Out of scope (do NOT fix in this PR)

- Issue 3 (heading scope-close exact-match) — Claude review marked false alarm on second look; not actually broken.
- Issue 4 (mixed-fence `~~~` vs `\`\`\``) — edge-case-only, real handoffs don't mix fence chars.
- Issue 6 (DIRECT_QUESTION_RE requires `or` connector) — rare phrasing, NIT.
- Issue 8 (test style inconsistent with #1788) — NIT, both styles fine.

## Acceptance criteria

1. `## Acceptance criteria (numbered, all required)` heading is correctly recognized as exemption boundary; menu inside is NOT flagged.
2. Linter run against `docs/dispatch-briefs/2026-05-08-night/1787-1.4-anti-menu-linter.md` exits 0 (no false positive on its own brief).
3. `1.` style numbered menus ARE flagged (currently only `1)` style is).
4. Non-utf-8 input handled gracefully with informative error, exit code 2.
5. New test fixtures pin all three behaviors above.
6. ALL existing tests still pass.
7. `ruff check` clean.
8. Validation pass: linter run against `docs/session-state/*.md` should still produce the original 1 violation (the historical sign-off menu in `2026-04-22-overnight-bakeoff-and-124-plan-forks.md:75`), plus the linter run against `docs/dispatch-briefs/*.md` should NOT produce false positives on legitimate briefs.

## Numbered execution steps

1. Re-enter the existing worktree (delegate runner handles via `--worktree .worktrees/dispatch/codex/1787-1.4-anti-menu-linter`).
2. Pull latest from origin to ensure no drift: `git fetch origin codex-1787-1.4-anti-menu-linter && git reset --hard origin/codex-1787-1.4-anti-menu-linter`.
3. Read the full Claude review at `/tmp/claude-review-1788-1789-report.md` (the #1789 section).
4. Implement Issue 1 fix.
5. Add test fixture for `## Acceptance criteria (numbered, all required)`.
6. Implement Issue 2 fix.
7. Add test fixture for "Forbidden patterns:" enumeration that quotes the antipatterns.
8. Implement Issue 5 fix.
9. Add test fixture for `1.` style numbered menu.
10. Implement Issue 7 fix.
11. Add test for non-utf-8 input.
12. `.venv/bin/ruff check scripts/audit/lint_anti_menu.py tests/audit/test_lint_anti_menu.py`
13. `.venv/bin/pytest tests/audit/test_lint_anti_menu.py -x`
14. **Validation pass**: run linter against all `docs/dispatch-briefs/**/*.md` and `docs/session-state/*.md` — note any flagged. Confirm no false positives on briefs.
15. Amend or add commit on the existing branch: `fix(guardrail): anti-menu linter handles parenthesized AC headings + multi-line forbidden-pattern context (#1787, fixes Claude review #1789 issues 1+2)`
16. `git push origin codex-1787-1.4-anti-menu-linter` (force-push if rebased; otherwise plain push for new commit).
17. Add a comment to PR #1789 noting which Claude review issues were fixed: `gh pr comment 1789 --body "Revised per Claude review: issues 1, 2, 5, 7 fixed. Issues 3, 4, 6, 8 deferred per brief..."`
18. **Do NOT auto-merge.** Report back so orchestrator re-runs review.

## Why this matters

#1789 is half of the anti-menu enforcement guardrail (#1787 sub-task 1.4). It currently misfires on the project's own brief format — promoting it to pre-commit would block legitimate work. These fixes are surgical and unlock that promotion.
