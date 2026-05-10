# Codex brief — #1799 handoff verifier closed-world detection

**Issue:** #1799. Read full body: `gh issue view 1799`.
**Task ID:** `codex-1799-handoff-verifier`
**Mode:** `--mode danger --worktree`
**Base:** `origin/main`

## Worktree

```
git worktree add -b codex-1799-handoff-verifier .worktrees/codex-1799-handoff-verifier origin/main
cd .worktrees/codex-1799-handoff-verifier
```

## What to fix — apply Option A + C (recommended in issue body)

**Option A (broaden detection):** rewrite `PATH_PATTERN` to catch tilde-rooted dotfile typos + `.env*` variants. Issue body proposes:

```python
PATH_PATTERN = re.compile(r"\B~/\.[\w./_-]+\b|\B(?<!\.)\.env(?:\.[\w-]+)?\b")
```

Tune for false-positive rate < 5% on `docs/session-state/*.md` corpus (AC 2). If FP rate exceeds target, add a small allowlist (e.g. `~/.bashrc`, `~/.zshrc` — known-good non-typo paths).

**Option C (document):** add a paragraph to `docs/SCRIPTS.md` (find the `scripts/audit/check_handoff_refs.py` blurb or wherever this script is documented) clarifying:
- ✅ Catches: missing-file references for tilde-rooted dotfiles + `.env*` variants
- ❌ Does NOT catch: typos that resolve to a different existing file; content-correctness inside referenced files

Skip Option B (content-correctness) — out of scope for this issue.

NITs (issues 3-7 in the body) — skip unless trivial.

## #M-4 evidence (commit body)

- Raw output of running the linter against the seven false-negatives listed in #1799 body (`~/.bash_secret`, `.env.foofake`, `.env.production`, `.env.development`, `.env.staging`, `.env.example`, `~/.totally_not_a_real_file_xyz`) — must now flag.
- Raw FP count on `docs/session-state/*.md` (denominator: total path-shaped tokens; numerator: flagged ones). Must be < 5%.
- `.venv/bin/pytest tests/audit/ -k handoff -v` output.

## Pre-submit checklist (AGENTS.md:11-26) — applies.

## Workflow

1. Worktree setup → 2. Implement A + C → 3. Run #M-4 evidence probes → 4. ruff + pytest → 5. Commit `feat(audit): catch dotfile typos + document closed-world limitation (#1799)` → 6. Push → 7. `gh pr create` → 8. No auto-merge.
