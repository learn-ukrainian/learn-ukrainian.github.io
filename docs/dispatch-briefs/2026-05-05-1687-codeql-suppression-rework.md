# Codex dispatch — #1687 CodeQL suppressions still firing (rework)

## Context

PR #1687 (`gemini/codeql-B-secrets-exposure`) is the continuation of CodeQL batch B. Last session replaced `# nosec` (Bandit syntax) with inline `# codeql[<rule-id>] - <reason>` annotations on 4 sites. CI re-run shows **the inline annotations did NOT suppress the alerts** — CodeQL still reports 2 high-sev alerts on the PR (check run id 74363047895, "2 new alerts including 2 high severity security vulnerabilities").

The failing annotations are likely on these 4 files (from last session's commit `faacc57496`):
- `scripts/build/linear_pipeline.py:1582`
- `scripts/generate_mdx/core.py:574`
- `scripts/validate/validate_vocab_yaml.py:65`
- `scripts/vocab/lexical_sandbox.py:585`

Two of these are still flagged. The other two suppressions might be working, or might also be silently failing.

## Why the inline syntax didn't work

Best guess: CodeQL's Python rule suppression for `py/clear-text-*` either (a) requires a different exact format than `# codeql[<rule-id>]`, or (b) needs a repo-level config exclusion file, or (c) the original lines were scrubbed and re-introduced by the rebase. Codex's task: **diagnose first, then fix.**

## Worktree instructions (mandatory)

Worktree already exists: `.worktrees/dispatch/gemini/codeql-B-secrets-exposure` on branch `gemini/codeql-B-secrets-exposure`. Last commit `68d2ef9c1f`. Do NOT recreate; reuse.

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/gemini/codeql-B-secrets-exposure
git fetch origin main
# If branch is behind main:
#   git rebase origin/main
#   git push --force-with-lease
```

## Numbered steps

1. **Verify branch base.** `git log --oneline HEAD..origin/main` — empty = good. If non-empty, rebase + force-push.

2. **Pull the active CodeQL alert details for PR #1687.**
   ```bash
   gh api 'repos/learn-ukrainian/learn-ukrainian.github.io/code-scanning/alerts?ref=refs/pull/1687/head&state=open' --jq '.[] | {rule: .rule.id, file: .most_recent_instance.location.path, line: .most_recent_instance.location.start_line, message: .rule.description}'
   ```
   Document which 2 alerts are still firing — this is your real scope.

3. **Inspect the actual annotation syntax in code.** For each still-firing alert site, read the line + the comment annotation. Compare against the syntax CodeQL actually accepts:
   - Reference: https://docs.github.com/en/code-security/code-scanning/managing-code-scanning-alerts/dismissing-alerts-from-code
   - The `# codeql[<rule-id>]` syntax is for Java/JavaScript primarily; Python suppressions historically use **repo-level config** (`.github/codeql/codeql-config.yml` with `paths-ignore` or `query-filters`).
   - Verify: does the project even have a CodeQL config? `ls .github/codeql/` returns no such directory at HEAD. The CodeQL workflow file is `.github/workflows/codeql.yml` (or similar) — check what config it points to.

4. **Pick the right fix path** — DOCUMENT YOUR REASONING in the commit message:

   **Option A (preferred if applicable):** Genuine code fix. The 2 still-firing alerts may be salvageable with a real fix instead of suppression. For `py/clear-text-storage-sensitive-data` and `py/clear-text-logging-sensitive-data`, the real fix is usually: don't log/store the secret at all, or hash it first, or redact before write. If a real fix exists, prefer it over suppression.

   **Option B (if suppression is genuinely the right call):** Add `.github/codeql/codeql-config.yml` with a `query-filters` section that excludes the specific (rule, path, line) tuples. Then update `.github/workflows/codeql.yml` (or whichever the project's CodeQL workflow is) to reference `config-file: ./.github/codeql/codeql-config.yml` in the `init` step. Keep the inline `# codeql[...]` comments AS DOCUMENTATION (so future readers see why), but the real suppression now lives in the config.

   **Option C (last resort):** If the alerts are genuinely false positives that the config-file approach can't easily target, document why in a `docs/decisions/2026-05-05-codeql-batch-b-suppression.md` ADR and dismiss via the GH UI as `false positive`. Do NOT do this without explicit reason.

5. **Run pytest locally.** `.venv/bin/python -m pytest tests/ -x -q` (already passing per last commit; just verify nothing regresses).

6. **Run ruff.** `.venv/bin/ruff check scripts/`

7. **Commit.** Conventional commit message:
   ```
   fix(security): rework #1687 suppressions — <approach summary> (#1687)
   ```
   Body explains the diagnosis (which alerts were still firing, why inline didn't work) and the chosen fix (real fix vs. config exclusion vs. dismissal).

8. **Push:** `git push origin gemini/codeql-B-secrets-exposure` (force-with-lease only if rebased).

9. **PR is already open as #1687.** Do NOT close or recreate. Comment on the PR explaining the rework:
   ```bash
   gh pr comment 1687 --body "Reworked suppressions after CI flagged 2 still-firing alerts on commit 68d2ef9c1f. <approach summary>. CI re-run pending. cc @user."
   ```

10. **Do NOT enable auto-merge.** Cross-review by the next session is required.

## Acceptance criteria

- `gh pr checks 1687` shows CodeQL `success` (not `failure`) after CI re-run
- pytest passes
- ruff clean
- All 7 original alerts in batch B are either really fixed (Option A) or properly suppressed (Option B/C with documented reason)
- Commit message documents the diagnosis + fix path

## Discipline reminders

- **Do NOT delete real fixes.** The 3 stack-trace + sensitive-data fixes in commit `8f62fa7c01` are correct and stay.
- **Do NOT re-introduce `# nosec`.** Bandit syntax that CodeQL ignores.
- **Do NOT enable auto-merge.** Security-class PR — always DRAFT or non-auto-merge for cross-review.
- **Reference #1687 in commit messages.**
- **No `--no-verify` on commits.**

## Related

- Predecessor brief: `docs/dispatch-briefs/2026-05-05-codeql-followups-syntax-and-safejoin.md`
- Predecessor session handoff: `docs/session-state/2026-05-05-codeql-cleanup-and-adr008-resolution.md` (note: predicted this exact failure mode — "If CodeQL flags a new issue, it's likely the `# codeql[<rule-id>] - <reason>` syntax I introduced isn't recognized by the project's CodeQL config — fall back to repo-level config exclusion in `.github/codeql/codeql-config.yml`")
