# Gitflow Best Practices

> **Scope:** Commit conventions, staging discipline, branch strategy.

---

## Branch Strategy

This project uses **trunk-based development on `main`** with **worktrees for code changes during builds**.

- **Default**: work directly on `main` (content, config, docs)
- **During builds**: code changes go in a worktree → PR → merge after review
- **Rule**: merging to main is safe during builds (code already loaded), but no new builds should start during merge
- Never force-push to `main`

### Worktree Workflow (for code changes during builds)

```bash
# 1. Create worktree for an issue
scripts/wt.sh create 817 "fix v4 terminology"

# 2. Work in the worktree
cd ../learn-ukrainian-wt-817
# make changes, commit, push
git push -u origin fix/817-fix-v4-terminology

# 3. Create PR after exact-head cross-family CF review (see model-assignment.md)
.venv/bin/python -m scripts.publish pr-create --title "fix: v4 terminology in logs (#817)"

# 4. Get reviews on the PR
# - Code review agent reviews automatically
# - Cross-family code review follows model-assignment.md Code review row
# - /simplify for code quality

# 5. Merge when approved
scripts/wt.sh merge 817
git push origin main

# 6. Clean up
scripts/wt.sh clean 817
```

### When to use worktrees vs. direct commits

| Situation | Approach |
|-----------|----------|
| No builds running, small fix | Direct commit on main |
| Builds running, need code change | Worktree → PR → merge |
| Docs/config only | Direct commit on main (safe during builds) |
| Large refactor | Worktree → PR with reviews |

### Build awareness

`scripts/wt.sh status` checks the monitor API (`localhost:8765`) for active builds. The merge command warns about build state.

---

## Commit Discipline

### Only commit when asked — human primary checkout only
This applies to interactive work in the human's primary checkout: unless the user
explicitly says "commit", do not commit there. Stage, review, present — but do not commit
automatically.

**Dispatched change tasks are different.** Per `AGENTS.md`, change tasks end in a pushed
PR — commit, push, and open the PR as the job, in the dispatch worktree, without waiting
for a separate "commit" instruction. Pausing a dispatched change task to ask whether to
commit is the "first slice, then ask" pattern the operator contract disallows for decided
work (`operator-expectations.md` item 10).

### Stage specific files
Never `git add -A` or `git add .` — it risks including:
- `.env` files with secrets
- Binary artifacts
- Unrelated generated files (vocabulary.db changes from unrelated runs)

Stage by file group:
```bash
git add scripts/build_module_v5.py scripts/pipeline_v5.py  # scripts
git add claude_extensions/phases/gemini/phase-A-seminar.md     # templates
git add curriculum/l2-uk-en/plans/bio/petro-vesklyarov.yaml  # content fixes
```

### What NOT to commit together
- Pipeline code changes + unrelated curriculum content updates
- Scripts + vocabulary.db (db regenerates automatically)
- Phase templates + unrelated audit results

---

## Commit Message Format

```
{type}: {short description} (#{issue-number})

{body — what changed and why}
{commands if useful}

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

### Types
| Type | Use for |
|------|---------|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `refactor` | Code restructuring without behavior change |
| `docs` | Documentation only |
| `test` | Tests only |
| `chore` | Maintenance (deps, config) |

### Examples
```
feat: build_module_v5.py — v5 pipeline (#585)

fix: meta health check + Phase A splitting rules for oversized sections (#589)

fix: 7 bio plan files with YAML syntax errors (unquoted colon in list items)
```

### Rules
- Subject line: ≤72 characters
- No period at end of subject
- Body: explain the WHY, not just the WHAT
- Always reference the GH issue number if one exists

---

## What to Commit vs. Not Commit

### Always commit
- Scripts (`scripts/`)
- Phase templates (`claude_extensions/phases/`)
- Best practices docs (`docs/best-practices/`)
- Plan files (`curriculum/l2-uk-en/plans/`)
- Meta files (`curriculum/l2-uk-en/{track}/meta/`)
- Config changes (`scripts/audit/config.py`)
- CLAUDE.md changes

### Commit when content sprint is done
- Module content (`curriculum/l2-uk-en/{track}/*.md`)
- Activities (`curriculum/l2-uk-en/{track}/activities/`)
- Vocabulary (`curriculum/l2-uk-en/{track}/vocabulary/`)
- MDX files (`starlight/src/content/docs/`)

### Never commit
- `.env` files
- `vocabulary.db` (auto-generated, large binary)
- Gemini output files (`logs/gemini-output-*.md`)
- Temporary orchestration artifacts (`phase-A-prompt.md`, `track-context.md`)

### Periodically commit
- Status files (`curriculum/l2-uk-en/{track}/status/`)
- Audit reports (`curriculum/l2-uk-en/{track}/audit/`)
- Orchestration state (`orchestration/*/state*.json`)

---

## Pre-Commit Checklist

Before committing:
1. `git diff --cached --stat` — confirm staged files make sense as a unit
2. Check for accidental binary or secret files
3. Verify commit message references the right issue
4. Run `git log --oneline -5` to match style of recent commits

---

## Dangerous Commands (require user confirmation)

Never run these without explicit user instruction:
- `git push --force` (any branch)
- `git reset --hard`
- `git checkout .` or `git restore .`
- `git clean -f`
- `git branch -D {branch}`
- `git commit --amend` (on published commits)
- `git rebase -i` (interactive rebase)

If a pre-commit hook fails: fix the issue, re-stage, create a NEW commit. Never use `--no-verify`.

---

## Co-Author Convention

All Claude commits end with:
```
Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

This makes AI-assisted commits transparent and attributable.

---

## Branch Protection (main)

`main` is the only long-lived branch. It carries every shipped module and the
source of truth for plans, prompts, curriculum.yaml, and pipeline code. Treat
it accordingly.

### Required branch invariants for `main`

1. **Require a pull request before merging** — all code changes land via Pull Request.
2. **Require status checks to pass before merging** — required CI Gate checks must pass.
3. **Require branches to be up to date before merging** — prevents merge-time regressions.
4. **Require conversation resolution before merging** — no unresolved review comments on merge.
5. **Require linear history** — squash or rebase merge only; no merge commits on `main`.
6. **Uniform protection enforcement** — invariants apply without administrative bypass.
7. **Restrict direct branch pushes** — direct push to `main` is disallowed.
8. **Block force pushes and deletions** — `main` cannot be force-pushed or deleted.

### Branch and worktree cleanup

- Remote feature branches are deleted following merge completion.
- Temporary dispatch worktrees are reaped after task completion.

### Local pre-tool merge guards

To enforce invariants deterministically across all environments, local client hooks
and CLI merge wrappers validate that:
1. PR is not in draft status.
2. No non-advisory status check is red or failing.
3. Automated merge is refused against a base branch that lacks verified required status checks.

| Hook | Owns | Blocks |
| --- | --- | --- |
| `guard-admin-merge.py` | `gh pr merge --admin` (raw command refused by the shim) | a blocking check is red (#M-0.5) |
| `guard-pr-merge.py` | every `.venv/bin/python -m scripts.publish pr-merge --number <N>` and raw merge attempts | draft PR · any red non-advisory check · checks still running without `--auto` · `--auto` on a base branch with no required status checks |

Both guards judge `--admin` merges. They fail **closed**: if the PR, its checks, or the base branch's
protection can't be read (gh error/timeout), the merge is refused rather than
assumed safe.

A red check blocks regardless of whether the forge marks it required: red is red. Every
check counts unless its name says `advisory` — which is why advisory
jobs carry that word.

`--auto` is the one verdict that does consult branch protection, because auto-merge
relies on configured required checks to delay merging: with none configured, auto-merge
merges immediately regardless of check states. The guard inspects branch protection
per merge — allowed against a base with verified required checks (such as `main`),
refused when protection cannot be verified or lists no required checks. In that case,
verify checks green and merge manually. `.venv/bin/python -m scripts.publish pr-disarm --number <N>` is never blocked;
disarming auto-merge is the remedy, not the offence.

**Escape hatch:** a human runs the merge outside the agent harness. The hooks
gate the agent fleet, not the maintainer — but see the override log below.

### When a hook or check blocks you

Fix the underlying issue — never bypass with `--no-verify`,
`--no-gpg-sign`, or admin override. The sole exception is a documented
emergency hotfix, which MUST be followed by a commit that adds a test or
hook preventing the same class of bypass in the future.

### Emergency override log

Any time `main` branch protection is bypassed (admin override, `--no-verify`,
force push), log it in `docs/decisions/` as an ADR entry with:
- what was bypassed
- why it was unavoidable
- the follow-up commit that restored the invariant

No override without an ADR. No exceptions.
