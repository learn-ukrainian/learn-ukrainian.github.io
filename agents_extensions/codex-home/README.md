# Reusable Codex home configuration

This is the canonical portable source for Codex home defaults, orchestration
guidance, and named profiles. The regular driver uses GPT-6.1 Sol high.

| Profile | Model | Effort | Access |
| --- | --- | --- | --- |
| `luna_explorer_medium` | `gpt-6-luna` | medium | read-only |
| `luna_explorer_high` | `gpt-6-luna` | high | read-only |
| `luna_coder_high` | `gpt-6-luna` | high | workspace-write |
| `sol_coder_high` | `gpt-6.1-sol` | high | workspace-write |
| `sol_red_team_high` | `gpt-6.1-sol` | high | read-only |
| `sol_ukrainian_content_high` | `gpt-6.1-sol` | high | workspace-write |
| `sol_advisor_high` | `gpt-6.1-sol` | high | read-only |

The default spawned agent is Luna high. Use Luna medium explicitly for routine
scouting and high for ambiguous investigations or bounded coding. Sol high
handles broader coding and adversarial review. `sol_advisor_high` runs at high
as the on-demand advisor for consequential design and difficult linguistic
judgment. Advice and designated approval come from Opus 5.5 and Sol 6.1:
approval comes from the operator or from the two agreeing; when one of them
authored the proposal, the other's approval completes it, and a proposal by any
other agent needs both; if they disagree, the operator decides (#9583, #9616). This profile supplies only the Sol half. Sol high
is the Ukrainian content authoring default, subject to VESUM, sources, and
track immersion checks. This is a routing decision, not a comparative
Ukrainian-quality benchmark.
Select named profiles explicitly; full-history inheritance alone does not
guarantee model and effort. The driver retains final disposition.

Other model-family agents can request CF (cross-family) review from a GPT-6
reviewer through an existing Codex execution route. Compare actual author and
reviewer families before claiming CF coverage. A GPT-6 review of a GPT-6
author is same-family. These profiles do not change fleet review eligibility.

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

The old names `astra_worker_low`, `astra_red_team_high`, and
`astra_advisor_high` (replaced by `sol_advisor_high`, #9583) are superseded.
The deployer refuses to apply changes while any of them remains active. Inspect
those target files and move them into a private backup outside `agents/`
before deployment; record the moves for rollback. Older retired names
(`luna_explorer_xhigh`, `luna_worker_max`, `sol_worker_high`,
`terra_worker_high`) remain preserved by the deployer and require the same
manual inspection if present. Preserve unrelated profiles.

Start a fresh task and inspect the loaded catalog after deployment. Check quota
and health, then run a bounded representative spawn to verify model, effort,
and effective access restrictions. TOML acceptance alone does not prove runtime
activation or sandbox enforcement. Report remote activation separately from
local validation. Keep complete host configuration and backups out of Git.

For rollback, use the receipt to restore replaced files and their original modes.
Remove only new managed files absent before deployment, and restore any legacy
profiles manually retired above. Preserve unrelated or subsequent changes.
Start a fresh task and verify the restored catalog.
