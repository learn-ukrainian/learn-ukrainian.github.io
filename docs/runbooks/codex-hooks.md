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
