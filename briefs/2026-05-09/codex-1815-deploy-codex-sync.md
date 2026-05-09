# Codex CLI — Add `.codex/` to deploy_prompts.sh sync chain (#1815)

## TL;DR

`scripts/deploy_prompts.sh` syncs `claude_extensions/` → `.claude/`, `.agent/`, `.gemini/` but NOT to `.codex/`. This causes `.codex/hooks/*.sh` to drift from source — operators "fix" the drift by editing `.codex/` directly, which is exactly what #1811 was about.

Add `.codex/` to the chain. Mechanical patch.

Full spec: **GH issue #1815** — every AC must be ticked.

---

## Mandatory orientation (#M-4)

1. **`docs/best-practices/deterministic-over-hallucination.md`** — every claim tool-backed.
2. **GH issue #1815** — `gh issue view 1815`.
3. **`scripts/deploy_prompts.sh`** — read end-to-end. Find the existing `.claude/` and `.agent/` rsync chain (around line 165-167 per the issue body); the `.codex/` chain mirrors it.
4. **`tests/test_deploy_script_idempotency.py`** — read; the test will need a new case for `.codex/`.
5. **`.claude/rules/critical-rules.md` rule #1** — the deploy invariant.

## Verifiable claims this work will produce + the tool

| Claim | Tool | Evidence format |
|---|---|---|
| ".codex/hooks/ exists in git" | `git ls-files .codex/hooks/` | Quoted output |
| "Sync emits .codex/" | Run `npm run claude:deploy` after the patch, then `diff -rq claude_extensions/hooks/ .codex/hooks/` returns no output | Quoted output |
| "Idempotent — second run = no-op" | `npm run claude:deploy && npm run claude:deploy` and inspect git status | Quoted output |
| "Test passes" | `.venv/bin/pytest tests/test_deploy_script_idempotency.py` | Quoted pytest |
| "Ruff clean" | `.venv/bin/ruff check tests/test_deploy_script_idempotency.py` (script is .sh) + `shellcheck scripts/deploy_prompts.sh` if available | Quoted output |
| "ORPHAN_PATHS_CODEX preflight catches stale" | Add an orphan `.codex/<path>` not in claude_extensions, run preflight → fails | Quoted output |

---

## Worktree instructions (mandatory)

Dispatcher creates `.worktrees/dispatch/codex/codex-1815-deploy-codex-sync/`. All work there. Branch: `codex/1815-deploy-codex-sync`. Base: `origin/main`.

---

## Workflow (numbered)

1. **Worktree setup** verified.
2. **Read the issue** — `gh issue view 1815`. Note all AC checkboxes.
3. **Read `scripts/deploy_prompts.sh`** — find `.claude/` and `.agent/` and `.gemini/` rsync chains. Identify `ORPHAN_PATHS_CLAUDE` / `ORPHAN_PATHS_AGENT` / `ORPHAN_PATHS_GEMINI` declarations.
4. **Implement the `.codex/` sync:**
   - Add `ORPHAN_PATHS_CODEX=()` declaration matching the existing pattern. Populate with any `.codex/`-only paths (check `git ls-files .codex/`).
   - Add `rsync -av --delete $(build_excludes "${ORPHAN_PATHS_CODEX[@]}") claude_extensions/ .codex/` parallel to `.claude/` chain (issue body line 165-167 reference).
   - Extend `check_orphans` (preflight) to include the new target.
   - Extend `diff_dirs` (post-deploy verification) to include the new target.
5. **Tests** — extend `tests/test_deploy_script_idempotency.py`:
   - Test `.codex/` is a sync target.
   - Test that two consecutive runs produce no diff.
   - Test orphan-path detection.
6. **Lint** — `shellcheck scripts/deploy_prompts.sh` (warn if shellcheck unavailable; not fatal); `.venv/bin/ruff check tests/test_deploy_script_idempotency.py`.
7. **Run the deploy** in your worktree: `npm run claude:deploy` — verify `.codex/hooks/*` matches `claude_extensions/hooks/*` after the run.
8. **Commit** — conventional message:
   ```
   fix(deploy): add .codex/ to deploy_prompts.sh sync chain (#1815)

   - Mirrors .claude/ and .agent/ pattern.
   - ORPHAN_PATHS_CODEX declared.
   - Preflight + diff verification extended.
   - Test coverage extended.

   Closes #1815. Closes the upstream cause of #1811-class drift.

   Co-Authored-By: Codex (gpt-5.5) <noreply@anthropic.com>
   ```
9. **Push** — `git push -u origin codex/1815-deploy-codex-sync`.
10. **PR** — `gh pr create` referencing #1815 with quoted evidence per #M-4.
11. **NO auto-merge.** Stop. Orchestrator reviews and merges.

---

## What "done" looks like

- All ACs from #1815 ticked with quoted evidence.
- `diff -rq claude_extensions/hooks/ .codex/hooks/` empty after deploy.
- Pre-commit clean.
- PR opened, **NOT merged**.

## Escalation

If `.codex/` has paths that genuinely should NOT come from `claude_extensions/` (agent-private state), document them in `ORPHAN_PATHS_CODEX` with comments and proceed.
