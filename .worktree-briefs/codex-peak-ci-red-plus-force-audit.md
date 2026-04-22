# Codex brief: CI cleanup on main + `--force` audit in rules

**Task ID:** `codex-peak-ci-red-and-force-audit`
**Worktree:** `.worktrees/codex-peak-ci-red-plus-force-audit`
**Branch:** `codex/peak-ci-red-plus-force-audit`
**Mode:** `--mode danger` (worktree-isolated, commits + push allowed)
**Model:** `gpt-5.4` (default); `-c model_reasoning_effort=high` (config.toml default, adequate)

## Why you're running now

14:00–20:00 CET is the Claude-expensive window. Krisztian is AFK. We're using the window productively by firing Codex + Gemini on independent infra + content tasks while Claude's main session is stopped and a separate headless Claude dispatch works on #1370 (prompt hardening) in its own worktree. Your PRs will be reviewed + merged after 20:00.

## Worktree setup (mandatory — `.claude/rules/delegate-must-use-worktree.md`)

```bash
git worktree add -b codex/peak-ci-red-plus-force-audit .worktrees/codex-peak-ci-red-plus-force-audit
cd .worktrees/codex-peak-ci-red-plus-force-audit
```

Do NOT branch in the main checkout.

## Two independent concerns — one PR

Both are hygiene. Bundling into ONE PR keeps review lightweight.

### Concern A — CI is red on main (pre-existing, not caused by any recent PR)

On the latest CI run on `main`, three failing jobs:
1. **`Lint (ruff)`** — 1 ruff error. `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/ruff check scripts/ tests/` reproduces. The offending file begins:
   ```
   import glob
   import re
   from dataclasses import dataclass
   from pathlib import Path
   ```
   Fix: `ruff check --fix` or equivalent. **Find which file this is** (grep the signature `^import glob\nimport re\nfrom dataclasses import dataclass\nfrom pathlib import Path`). Fix with targeted edit. Do NOT blanket-format the whole repo.

2. **`No new root scripts`** — check logs at `gh run view <LATEST_MAIN_RUN_ID> --log-failed | grep "No new root scripts"`. Understand what file triggered it. Either:
   - The check's logic is too strict (a stub or existing file mis-detected as new)
   - A genuinely-new script landed in `scripts/` root that should be in a subdirectory
   Fix whichever is the case. If the check is buggy, fix the check. If the file is real, move it.

3. **`Secret Scanning (gitleaks)`** — failing with "missing gitleaks license" noise. Not a secret leak; a license-key gap. Options:
   - Get a license key and store as `GITLEAKS_LICENSE` GitHub Secret (user action — flag this, don't try)
   - Switch to an alternative secret-scanning job (e.g., `trufflesecurity/trufflehog`, has free tier)
   - Remove the gitleaks job if we're not going to license it
   
   Recommend an option in the PR body; do NOT unilaterally remove the job.

### Concern B — `--force` audit (deferred AC from #1394)

Scan for `--force` usage across:
- `claude_extensions/rules/*.md`
- `.claude/rules/*.md` (mirror — edit source in `claude_extensions/` and run `npm run claude:deploy`)
- `docs/best-practices/*.md`
- Dispatch briefs we've written: `.worktree-briefs/*.md`

For each hit, classify:
- **LOAD-BEARING** — `--force` is required for the command's correctness (e.g., `git push --force-with-lease` for true force-push scenarios)
- **DROP** — `--force` is copy-paste and silently eats uncommitted work / overrides safety checks
- **FLAG_FOR_HUMAN** — ambiguous, needs user decision

Produce:
1. A report at `docs/best-practices/force-flag-audit-2026-04-22.md` listing every hit classified
2. For DROP cases, edit the source file to remove `--force`
3. For FLAG_FOR_HUMAN, leave a `<!-- TODO(#1394): classify --force usage -->` comment inline

Do NOT touch anything outside the listed directories (no source code changes).

## Acceptance criteria

- [ ] Ruff error fixed; `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/ruff check scripts/ tests/` returns clean
- [ ] `No new root scripts` understood + fixed (either check or file, whichever was wrong)
- [ ] Gitleaks decision documented in PR body (recommendation, not action)
- [ ] `--force` audit report written with every hit classified
- [ ] DROP cases edited out
- [ ] PR opens targeting `main`

## Do NOT

- Do NOT rewrite unrelated code while you're in there — resist scope creep
- Do NOT branch in the main checkout
- Do NOT touch `scripts/build/phases/v6-write.md` (that's #1370's territory, running in parallel)
- Do NOT touch anything under `.worktrees/claude-1370-writer-harden/` — active concurrent work

## Adversarial review before merge

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-claude \
  "Adversarial review of #1394/CI-red PR. Read the diff against main." \
  --task-id codex-peak-review
```

Address findings or justify-ignoring. Document on PR.

## Deliverables

1. Commits on branch `codex/peak-ci-red-plus-force-audit`:
   - `fix(ci): ruff error + root-scripts check (pre-existing red)`
   - `docs(audit): --force usage audit + drops (#1394)`
2. PR → main: `chore(ops): CI red cleanup + --force audit from #1394`
3. PR body:
   - What CI failures were fixed + root cause of each
   - Gitleaks recommendation (for Krisztian to action)
   - `--force` audit summary: count by classification, link to report
4. Review via Claude headless, findings addressed

## Time estimate

60–120 min.

## If blocked

If either concern stalls (> 60 min on one), skip to the other and note the blockage in the PR body. Half-done is acceptable; ghost-done is not.
