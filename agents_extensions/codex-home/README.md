# Reusable Codex home configuration

This is the canonical portable source for Codex home defaults, orchestration
guidance, and named profiles. The regular driver uses Astra medium.

| Profile | Model | Effort | Access |
| --- | --- | --- | --- |
| `luna_explorer_medium` | `gpt-5.6-luna` | medium | read-only |
| `luna_explorer_high` | `gpt-5.6-luna` | high | read-only |
| `astra_worker_low` | `gpt-6-astra` | low | workspace-write |
| `astra_red_team_high` | `gpt-6-astra` | high | read-only |
| `astra_advisor_high` | `gpt-6-astra` | high | read-only |

Use Luna medium for routine scouting and high for ambiguous investigations.
Select named profiles explicitly; full-history inheritance alone does not
guarantee model and effort. The driver retains final disposition.

Other model-family agents can request CF (cross-family) review from the Astra
high reviewer through an existing Codex execution route. Compare actual author
and reviewer families before claiming CF coverage. Astra reviewing Astra is
same-family. Cross-family and cross-provider independence are distinct. These
profiles do not install a messaging service or change fleet review eligibility.

On Mac or VPS, fetch the intended commit and verify the execution account,
effective Codex home, runtime, and live model support. Do not silently substitute
an unavailable model. Use the runtime's configured `CODEX_HOME` when set instead
of the example target below.

Deploy from a dispatch worktree with the project interpreter:

```bash
.venv/bin/python scripts/deploy_codex_home.py --codex-home "$HOME/.codex" --dry-run
.venv/bin/python scripts/deploy_codex_home.py --codex-home "$HOME/.codex"
.venv/bin/python scripts/deploy_codex_home.py --codex-home "$HOME/.codex" --check
```

In a linked worktree, use the canonical checkout's `.venv/bin/python` when
that worktree has no interpreter. Home deployment is explicit and separate
from `npm run agents:deploy`, which controls repository mirrors.

The deployer manages four config keys: main model and reasoning effort, and
default subagent model and reasoning effort. It preserves authentication, MCP
configuration, project trust, plugins, hooks, features, and unrelated files.
It does not enable multi-agent support in a runtime that lacks it or set a
concurrency limit. Review the target `AGENTS.md` first: it is a managed
replacement, so reconcile account-specific instructions in source before
deployment. Changed originals are backed up under the target
home's `.deploy-backups/` directory. A failure must be investigated using its
receipt before retrying; per-file atomic replacement is not a multi-file
transaction. Dry-run and check modes do not write.

The old names `luna_explorer_xhigh`, `luna_worker_max`, `sol_worker_high`, and
`terra_worker_high` are retired from source. The deployer preserves existing
target files with those names. Inspect them and move only confirmed obsolete
profiles into a private backup outside the active `agents/` directory. Record
the moves for rollback. Preserve unrelated profiles.

Start a fresh task and inspect the loaded catalog after deployment. Check quota
and health, then run a bounded representative spawn to verify model, effort,
and effective access restrictions. TOML acceptance alone does not prove runtime
activation or sandbox enforcement. Report remote activation separately from
local validation. Keep complete host configuration and backups out of Git.

For rollback, use the receipt to restore replaced files and their original modes.
Remove only new managed files absent before deployment, and restore any legacy
profiles manually retired above. Preserve unrelated or subsequent changes.
Start a fresh task and verify the restored catalog.
