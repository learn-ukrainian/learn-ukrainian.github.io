# Dispatch brief: revise #1797 D4 lineage scanner (fixes Claude review's 1 BLOCKING + 2 IMPORTANT)

> **PR to revise:** #1797 on branch `codex/1785-d4-decision-lineage`
> **Origin review:** `gh pr view 1797 --json comments` (Claude headless adversarial review)
> **Verdict:** REVISE [BLOCKING] — running scanner on live repo produces garbage
> **Agent:** Codex
> **Worktree:** NEW worktree, branched from existing PR tip; force-push back to PR branch.

## Worktree instructions (mandatory — note the --base)

```bash
.venv/bin/python scripts/delegate.py dispatch \
    --agent codex --mode danger --worktree --base origin/codex/1785-d4-decision-lineage \
    --task-id codex-1797-d4-fix \
    --prompt-file docs/dispatch-briefs/2026-05-08-night/1797-d4-revise.md
```

After fixes, push back to ORIGINAL PR branch:

```bash
git push origin HEAD:codex/1785-d4-decision-lineage --force-with-lease
git push origin --delete codex/1797-d4-fix
```

PR #1797 picks up amendments automatically.

## Issues to fix (from Claude review on PR #1797)

### Issue 1 (BLOCKING) — INDEX/README false-positive avalanche

**File**: `scripts/audit/decision_lineage.py:149` (`glob("**/*.md")`) and `:217-228` (`_alias_git_pattern`)

**Repro** (verified by Claude review running scanner against live repo):
```
$ .venv/bin/python scripts/audit/decision_lineage.py
count: 13
  INDEX                           commits=144  prs=173
  README                          commits= 30  prs= 29
  ADR-007                         commits= 27  prs= 72
  ADR-008                         commits= 16  prs= 41
  ...
```

`docs/decisions/INDEX.md` and `docs/decisions/pending/README.md` get walked as if they were decisions. Their slug aliases ("INDEX", "README") match common English-word substrings in commit messages: `Add root index.html for GitHub Pages`, `Reorganize output structure`, etc. Top-level scan output is dominated by garbage.

**Fix (do BOTH)**:
1. **Skip non-decision files**: in the file walker (`:149`), exclude `INDEX.md` and `README.md` (or any file whose `_normalize_adr` returns empty AND has no `decision_id` / `decision_ids` / `adr` frontmatter key).
2. **Word-boundary matching** in `_alias_git_pattern` (`:217-228`): wrap each escaped alias with `\b…\b` so "indexing" / "index.html" / "READMEs" don't match.

### Issue 2 (IMPORTANT) — Patch scan silently disabled in any real repo

**File**: `scripts/audit/decision_lineage.py:282-283`

```python
if _commit_count(project_root) > PATCH_SCAN_COMMIT_LIMIT:
    return
```

The `-G pattern` patch-text scan is the ONLY code path that finds commits which mention an alias only in a diff. Unconditionally skipped when commit count > 200 — i.e., always, in production.

AC #2 from #1785: *"scan `git log --all -p` for commits that touched the file path OR mention any of these alias forms"*. Silently dropping the patch scan misses a class of citations.

**Fix**:
1. Print a stderr warning when patch scan is skipped:
   ```
   decision_lineage: patch-text scan skipped (repo has N commits > 200 limit); add --with-patch-scan to force.
   ```
2. Add a `--with-patch-scan` CLI flag that overrides the limit.

### Issue 3 (IMPORTANT) — PR refs over-attributed

**File**: `scripts/audit/decision_lineage.py:236-239` (`_extract_pr_refs`) and aggregation in `as_dict` (`:53`)

When a commit matches any alias for a decision, ALL PR refs in that commit's text are credited to the decision. Live ADR-008 example: commit `ad6592b074` mentions ADR-008 in passing; all 3 PR refs (#1522, #1523, #1184) get attributed to ADR-008 even though they're about ADR-009 and management automation. Inflates PR count to implausible 41.

**Fix** (pick one, document choice in commit):
1. Only attribute PRs from commits where the alias appears in the **subject line** (stricter heuristic).
2. Expose two fields: `prs_strict` (subject-line only) and `prs_loose` (all matches).
3. Add `match_kind` per commit and let consumers filter.

Recommend (1) — simpler and more accurate.

### Issue 4 (NIT) — Sentinel `"file_path"` leaks into `matched_aliases`

**File**: `scripts/audit/decision_lineage.py:257`

`record.add_commit(sha, date, subject, {"file_path"}, message)` injects literal string `"file_path"` into the alias set, surfaces in JSON output mixed with real aliases.

**Fix**: add a separate `match_kind: "path" | "message" | "patch"` field per commit dict, drop the magic string from `matched_aliases`.

### Issue 5 (NIT) — Test coverage gap: patch-only path never directly tested

**File**: `tests/audit/test_decision_lineage.py`

All 3 reference commits in the existing test mention their alias in the **commit message**, so all match via cheap `--grep` path before `-G` runs. The patch-only code path (alias only in diff text, NOT in commit message) — exactly what Issue 2 silently disables in production — is never exercised.

**Fix**: add a 4th commit whose message is unrelated (e.g., `"refactor: tidy notes.md"`) but whose diff modifies a file to mention "BETA-42". Assert the scanner finds it.

## Out of scope (per Claude review)

- Issue 6 (test fixture has 4 commits, brief said 3) — spirit satisfied.
- Issue 7 (route ordering brittle) — works as-is, just add a comment above the `/lineage` decorator noting the ordering requirement.
- Issue 8 (SCRIPTS.md entry) — already updated per PR body.

## Acceptance criteria

1. Scanner run with no filter on live repo: INDEX/README NOT in output, ADR-008 has plausible counts (subject-line PR attribution).
2. Word-boundary matching: "indexing" / "index.html" do NOT match alias "INDEX".
3. Stderr warn fires when patch scan skipped due to commit limit.
4. `--with-patch-scan` flag overrides the limit.
5. PR refs attributed only via subject-line matches (Issue 3 option 1).
6. `match_kind` field per commit dict; `"file_path"` sentinel removed from `matched_aliases`.
7. New test fixture exercises patch-only code path.
8. ALL existing tests pass.
9. `ruff check` clean.

## Numbered execution steps

1. `git worktree add` via `--base origin/codex/1785-d4-decision-lineage`.
2. Read full Claude review on PR #1797.
3. Implement Issue 1 fixes (skip INDEX/README + word-boundary).
4. Implement Issue 2 fixes (stderr warn + `--with-patch-scan` flag).
5. Implement Issue 3 fix (subject-line PR attribution).
6. Implement Issue 4 fix (`match_kind` field + drop sentinel).
7. Add Issue 5 patch-only test fixture.
8. Add a comment above `/lineage` decorator (Issue 7).
9. `.venv/bin/ruff check scripts/audit/decision_lineage.py tests/audit/test_decision_lineage.py`
10. `.venv/bin/pytest tests/audit/test_decision_lineage.py -x`
11. **Validation pass**: run `.venv/bin/python scripts/audit/decision_lineage.py` against live repo. Capture output for PR body. Confirm INDEX/README NOT in output and ADR-008 PR count is plausible (single-digit to mid-teens).
12. Commit: `fix(audit): D4 scanner skips non-decision MDs, word-boundary alias match, subject-line PR attribution (#1785)`
13. **Push to ORIGINAL PR branch**: `git push origin HEAD:codex/1785-d4-decision-lineage --force-with-lease`
14. **Delete new branch**: `git push origin --delete codex/1797-d4-fix`
15. Comment on PR #1797: `gh pr comment 1797 --body "Revised per Claude review: Issue 1 (BLOCKING — INDEX/README) fixed, Issues 2+3 (IMPORTANT) fixed, Issues 4+5 (NIT) fixed, Issue 7 (NIT) commented. Validation: live-repo scan now shows clean output, ADR-008 has N commits / M PRs."`
16. Print "PR #1797 amended successfully".
