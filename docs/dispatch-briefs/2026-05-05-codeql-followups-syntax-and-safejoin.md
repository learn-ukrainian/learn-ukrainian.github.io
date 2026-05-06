# Codex dispatch — CodeQL Batch B (#1687) + Batch A (#1690) follow-up fixes

## Context

Two PRs got REJECT from cross-review (Claude + Codex agreed):

- **PR #1687** — `gemini/codeql-B-secrets-exposure`. 4 of 7 alerts are suppressed using Bandit's `# nosec` syntax. CodeQL ignores `# nosec` — those alerts are NOT actually closed. The 2 stack-trace fixes and 1 sensitive-data-logging fix are real and stay.

- **PR #1690** — `gemini/codeql-A-path-injection`. 1 alert (157, `scripts/path_safety.py:23`) uses the same wrong `# nosec` syntax. AND 3 calls in `scripts/research/research_quality.py` (lines 206, 1014, 1053) call `safe_join(Path(user_path).parent, Path(user_path).name)` — the parent is caller-controlled, so this isn't actually bounding the path. The other 7 fixes in this PR are real and stay.

PR #1689 already merged. PR #1688 has a separate XSS issue dispatched separately.

## What you must do

Two worktrees are live. Make commits on both branches, push.

### Worktree A: `.worktrees/dispatch/gemini/codeql-B-secrets-exposure` (PR #1687)

Fix the suppression syntax in 4 files:

- `scripts/build/linear_pipeline.py:1582`
- `scripts/generate_mdx/core.py:574`
- `scripts/validate/validate_vocab_yaml.py:65`
- `scripts/vocab/lexical_sandbox.py:585`

**Pattern:** replace `# nosec` (and any `# nosec: <text>` variants) with the
correct CodeQL suppression annotation.

CodeQL's Python suppression syntax (per
https://codeql.github.com/docs/codeql-cli/codeql-cli-quick-reference/):

```python
some_call_here  # codeql[py/clear-text-storage-sensitive-data] - <one-line reason>
```

The query ID for each line is the alert's rule (visible in the PR body's
disposition table — `py/clear-text-storage-sensitive-data`,
`py/clear-text-logging-sensitive-data`). Use the rule ID for that
specific alert, not a generic one.

The reason should be the same justification Gemini already wrote in the
PR body, just inline. Do NOT change the rationale — only the syntax.

If a line has the comment on the line above (block comment), prefer
moving it to a trailing comment on the offending line, since CodeQL's
inline suppression is line-scoped.

After changes:
- `git diff` should show ONLY the 4 comment edits (plus possibly small
  whitespace adjustments).
- Run `.venv/bin/ruff check scripts/build/linear_pipeline.py
  scripts/generate_mdx/core.py scripts/validate/validate_vocab_yaml.py
  scripts/vocab/lexical_sandbox.py` — must be clean.
- Commit message: `fix(security): switch # nosec → # codeql[...] suppressions (#1687)`
- Push to `gemini/codeql-B-secrets-exposure`.

### Worktree B: `.worktrees/dispatch/gemini/codeql-A-path-injection` (PR #1690)

Two distinct fixes.

**Fix 1 — Suppression syntax** (1 file):

- `scripts/path_safety.py:23` — replace `# nosec` with `# codeql[py/path-injection]
  - <reason>` keeping Gemini's existing rationale.

**Fix 2 — `safe_join` proper bounding** (1 file, 3 lines):

- `scripts/research/research_quality.py:206`, `1014`, `1053`

Currently:

```python
safe_join(Path(user_path).parent, Path(user_path).name)
```

This passes the user-controlled parent as the trusted root. The contract
of `safe_join` (see `scripts/path_safety.py`) is that the FIRST argument
is the trusted base, and the second is the user-supplied component to
join INTO that base. Right now the user controls both.

You need to:

1. Read `scripts/research/research_quality.py` to understand what `user_path`
   represents at each of those 3 call sites.
2. Identify the actual trusted root for each call (very likely a constant
   like `RESEARCH_CORPUS_ROOT`, `SCRAPED_PDFS_ROOT`, or similar — search
   the file's imports + module-level constants).
3. Refactor each call to:

   ```python
   safe_join(TRUSTED_ROOT, Path(user_path).relative_to(TRUSTED_ROOT))
   ```

   OR if the input is already known to be a relative path:

   ```python
   safe_join(TRUSTED_ROOT, user_path)
   ```

   Whichever matches the actual semantics. If the user input is an
   ABSOLUTE path that's intended to be inside TRUSTED_ROOT, use the
   `relative_to` form (it raises ValueError if the path is outside —
   exactly the bound we want). If the user input is a relative path,
   the second form works.

4. If you cannot determine the trusted root unambiguously from the call
   site context, DO NOT GUESS. Stop, document what you found in the
   commit message body, and leave a `# TODO(claude-1683-followup):` marker
   — better to escalate than ship a wrong "fix" that gives false
   security confidence.

After changes:
- Run `.venv/bin/ruff check scripts/path_safety.py scripts/research/research_quality.py`
- Run any pytest selectors that hit `research_quality.py` (search:
  `find tests -name "test_research*"`). If selectors exist, run them.
- Commit message: `fix(security): switch # nosec → # codeql[...] + bound safe_join with trusted root (#1690)`
- Push to `gemini/codeql-A-path-injection`.

## Worktree instructions (mandatory)

Work in the EXISTING worktrees listed above — they're already cloned at
the right branches with the existing Gemini fixes in place.

```bash
# Worktree A
cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/gemini/codeql-B-secrets-exposure
git fetch origin
git rebase origin/main  # take in any post-#1689 main updates
# ... make Fix 1 edits ...
git add -A
git commit -m "..."
git push --force-with-lease

# Worktree B  
cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/gemini/codeql-A-path-injection
git fetch origin
git rebase origin/main
# ... make Fix 1 + Fix 2 edits ...
git add -A
git commit -m "..."
git push --force-with-lease
```

Do NOT create new branches. Do NOT touch the main checkout.

After pushing, do NOT mark either PR ready-for-review or merge. Both
stay DRAFT for cross-review (I will re-dispatch you for the verification
pass once your commits are pushed).

## Output

Report back with:
- Commit SHAs for both branches.
- Whether each fix landed cleanly OR if you escalated (Fix 2 ambiguity).
- Output of `git diff origin/main..HEAD` line counts for sanity-checking
  the diffs are tight (just the targeted changes).

If you hit ANY ambiguity on Fix 2 (the `safe_join` trusted-root
identification), STOP and report the call-site context — don't guess.
