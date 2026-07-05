# Codex hooks deployment and probe

Issue #4447 established `.codex/hooks.json` as a deployed runtime config, not a
hand-edited destination file. The source of truth is
`agents_extensions/codex/hooks.json`; run `npm run agents:deploy` to refresh the
ignored `.codex/` target.

Codex hook facts verified from the current OpenAI Codex manual on 2026-07-05:

- Project-local `.codex/hooks.json` is loaded only for trusted project layers.
- `PreToolUse` and `PostToolUse` match on tool name.
- Current matcher support includes `Bash`, `apply_patch`, and the `Edit`/`Write`
  aliases for apply-patch edit paths.
- Hook command trust is separate from project trust. For automation that already
  vets the hook source, use `--dangerously-bypass-hook-trust`.

## Primary-checkout write guard (#4448)

`guard-primary-checkout-write.py` is a `PreToolUse` guard that blocks a write
tool from dirtying tracked files in the *primary checkout* while it sits on a
protected branch (`main`/`master`). It is wired into both providers:

- Claude (`agents_extensions/shared/settings.json`): the `Bash` matcher plus a
  `Write|Edit|MultiEdit` matcher.
- Codex (`agents_extensions/codex/hooks.json`): the `^Bash$` matcher plus a
  `^(Write|Edit|MultiEdit|apply_patch)$` matcher.

Every containment decision is delegated to
`scripts.guardrails.worktree_containment` (#4444); the hook only maps each
provider payload onto the target path(s) that module classifies. Writes into a
`.worktrees/**` dispatch worktree, any other registered worktree, gitignored
local/runtime state, or paths outside the repo are allowed. On a block the hook
exits 2 and tells the agent to create/`cd` into
`.worktrees/dispatch/<agent>/<task>/`.

### Covered write surfaces

- `Write` / `Edit` / `MultiEdit` — `tool_input.file_path`.
- `apply_patch` and Codex `Edit`/`Write` aliases — file paths parsed from the
  `*** Add/Update/Delete File:` / `*** Move to:` patch headers. #4447 verified
  Codex CLI fires `PreToolUse` for `apply_patch` (see the empirical result
  below), so the guard can enforce that path for the CLI.
- `Bash` — write-capable redirection (`>`, `>>`, `&>`), `tee`, and in-place
  editors (`sed -i` / `perl -i`). Read-only preflight (`git status`, `git log`,
  `rg`, `cat`, …) exposes no write target and is never blocked.

### Coverage limitations (by design)

- Bash write detection is heuristic. Arbitrary write vectors — `dd of=`,
  `cp`/`mv` destinations, `python -c "open(...,'w')"`, `$EDITOR` — are **not**
  parsed. Those paths rely on physical worktree isolation plus the monitor
  tripwire (#4449) and git shim (#4450), not on this hook.
- The guard is **not** the primary Codex enforcement layer for surfaces Codex
  does not expose as hookable. #4447 confirmed Codex **CLI** `apply_patch`/`Bash`
  interception, but Codex **Desktop** direct-edit interception is unverified. If
  Desktop (or any provider) does not emit a hookable `Bash`/`apply_patch`/`Edit`/
  `Write` event, this hook cannot enforce that path — #4445/#4446/#4449 carry it
  instead.
- Enforcement is scoped to protected branches. If the primary checkout is
  deliberately on a feature branch, or git cannot resolve the branch, the hook
  stays out of the way (fail open). It is a safety net; physical isolation is the
  real guarantee.

Tests: `tests/test_guard_primary_checkout_write.py` (pure payload extraction plus
end-to-end block/allow against a real repo with a dispatch worktree).

## CLI probe

Run the probe from the repository root:

```bash
.venv/bin/python scripts/agent_runtime/codex_hook_probe.py --keep-workdir
```

The probe creates a temporary Git repo under `/private/tmp`, installs a minimal
project `.codex/hooks.json`, and runs nested `codex exec` cases for:

- Bash write allowed
- Bash write denied by a `PreToolUse` hook exiting 2
- apply_patch write allowed
- apply_patch write denied by a `PreToolUse` hook exiting 2

The JSON output includes the exact nested `codex exec` commands, hook payload
logs, tool names seen by hooks, return codes, and whether the target file was
created. Treat `expected_file_exists: false` in a deny case, together with a
matching hook tool name, as evidence that the path is blockable.

Use this command for a cheap harness-only check that does not call Codex:

```bash
.venv/bin/python scripts/agent_runtime/codex_hook_probe.py --self-test
```

## Desktop/direct edit probe

Codex Desktop direct-edit behavior is not invokable from the CLI probe. Verify it
manually after `npm run agents:deploy`:

1. Open this repository in Codex Desktop from the trusted worktree.
2. Open `/hooks` and confirm the project `.codex/hooks.json` entries are listed
   and trusted, or start with `--dangerously-bypass-hook-trust` from CLI only.
3. Ask Desktop to run a shell write such as
   `printf 'desktop shell hook probe\n' > desktop-shell-probe.txt`.
4. Ask Desktop to edit a file without a shell command, using Desktop's normal
   direct edit/apply flow.
5. Compare hook labels/log output with the CLI probe results.

If Desktop or direct edit writes do not emit `Bash`, `apply_patch`, `Edit`, or
`Write` hook events, project hooks cannot enforce that path. Leave tracked-file
write enforcement to #4445/#4446/#4448/#4449 instead of claiming hook coverage.

## Empirical CLI result, 2026-07-05

Environment:

- cwd:
  `/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/4447-codex-hooks-deploy`
- Codex CLI: `codex-cli 0.142.5`
- Command:
  `.venv/bin/python scripts/agent_runtime/codex_hook_probe.py --keep-workdir --timeout 240`
- Probe repo:
  `/private/tmp/codex-hook-probe-9w43s82u/codex-hook-probe-repo`

| Case | Prompt summary | Hook tool names | Target file | Result |
| --- | --- | --- | --- | --- |
| Bash allow | `printf 'codex shell hook probe\n' > shell-write.txt` | `Bash`, `Bash` | `shell-write.txt` exists | Intercepted and allowed |
| Bash deny | `printf 'codex shell hook deny probe\n' > shell-denied.txt` | `Bash` | `shell-denied.txt` absent | Intercepted and blocked by exit 2 |
| apply_patch allow | Create `apply-patch-write.txt` with apply_patch only | `apply_patch`, `apply_patch` | `apply-patch-write.txt` exists | Intercepted and allowed |
| apply_patch deny | Create `apply-patch-denied.txt` with apply_patch only | `apply_patch` | `apply-patch-denied.txt` absent | Intercepted and blocked by exit 2 |

Observed block messages included:

- `Command blocked by PreToolUse hook: codex-hook-probe denying Bash`
- `Command blocked by PreToolUse hook: codex-hook-probe denying apply_patch`

Conclusion for this CLI build: project `PreToolUse` hooks can intercept and
block both Bash writes and Codex CLI apply_patch writes. This does not prove
Codex Desktop direct-edit interception; Desktop must still be checked with the
manual steps above.
