# Gitflow Best Practices

> **Scope:** Commit conventions, staging discipline, branch strategy.

---

## Branch Strategy

This project uses **trunk-based development on `main`**. No long-lived feature branches.

- All work goes directly to `main`
- Short-lived branches only if GitHub Copilot agent is assigned (it uses feature branches)
- Never force-push to `main`

---

## Commit Discipline

### Only commit when asked
Unless the user explicitly says "commit", do not commit. Stage, review, present — but do not commit automatically.

### Stage specific files
Never `git add -A` or `git add .` — it risks including:
- `.env` files with secrets
- Binary artifacts
- Unrelated generated files (vocabulary.db changes from unrelated runs)

Stage by file group:
```bash
git add scripts/build_module.py scripts/build_module_v2.py  # scripts
git add claude_extensions/phases/gemini/phase-A-seminar.md     # templates
git add curriculum/l2-uk-en/plans/bio/petro-veskliaov.yaml  # content fixes
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
feat: build_module.py — 4-call optimised pipeline (#585)

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
- MDX files (`docusaurus/docs/`)

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
