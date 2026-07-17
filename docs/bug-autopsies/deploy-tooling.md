# Deploy Tooling — deployment script failures and permission regressions

## 2026-07-17 — guard-pr-merge.py dead hook due to non-executable git mode (#5324 / #5333)

## Symptom

The `agents_extensions/shared/hooks/guard-pr-merge.py` file was created/saved with mode `100644` in the git repository (while all sibling hooks were `100755`). The deployer (`scripts/deploy_prompts.sh`) propagated this non-executable copy to the live hook destinations (`.claude/hooks/`, `.agent/hooks/`, `.codex/hooks/`). When executed, it failed with `/bin/sh: Permission denied`. Because hooks fail non-blocking, the failure was silent, disabling the PR merge guard fleet-wide (deployed-dead ~7h (deploy 02:04 → user report ~09:30)).

## Root cause

1. **Class:** File-creating tools default to `0644` mode when creating files, meaning new hooks added to the codebase are non-executable by default unless explicitly chmod'd and staged.
2. **Silent Failure:** PreToolUse hook execution is non-blocking to prevent locking out agents on runner/environment bugs, meaning a dead guard looks like silence.
3. **Propagation:** The deployment script (`scripts/deploy_prompts.sh`) copied the files as-is without verifying their executable bits.

## Prevention

1. **Tree-mode Test:** Added a pytest (`tests/test_hooks_executable.py`) that checks the git tree modes (via `git ls-files -s`) to assert that all files in `agents_extensions/shared/hooks/` are tracked as executable (`100755`).
2. **Deploy Verification:** Hardened the deploy script (`scripts/deploy_prompts.sh`) to:
   - Perform a pre-flight verification that fails the deployment if any source hook is not executable.
   - Run `chmod +x` on the destination hook copies after syncing to guarantee they are executable live.

## Related Incidents
- **2026-06-22:** Headroom deploy failure (`2026-06-22-headroom-deploy.md`) — Pipx/uv virtual environment clobbering and launchd domain mismatch.
- **2026-06-12:** deploy-orphan-guard-silent-abort (`deploy-orphan-guard-silent-abort.md`) — Silent abort of deploy script due to undeclared orphan files.
