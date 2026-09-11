# Agent Extensions

Git-tracked source for shared and per-agent extension assets.

Agent-agnostic extensions live under `shared/`. Agent-specific overrides and
memory live under the matching agent directory, such as `codex/`.

This follows the same layout used by the sibling kube-dojo project.

## Structure

```text
agents_extensions/
├── README.md
├── shared/          # Agent-agnostic previous extension source/
└── codex/           # Codex-owned durable rules, memory, and overlays
└── cursor/          # Cursor IDE rules (deploy to .cursor/rules/)
```

Deploy extensions with:

```bash
npm run agents:deploy
```

`npm run claude:deploy` remains as a compatibility alias.


## Codex skill discovery

Git-tracked `agents_extensions/shared/skills/` is canonical. Run
`scripts/deploy_prompts.sh` to deploy shared skills to `.agents/skills/`, the
single Codex discovery root. `.codex/` continues to receive its hooks, config,
and other shared resources, but no skills. Other harness skill mirrors remain.
The deploy helper requires legacy bytes to match tracked current source or a
regular-file blob in that exact source path's Git history. It atomically moves
the whole legacy `.codex/skills/` tree into a unique
`.codex/retired-skills/<capture>/skills` backup outside skill discovery, without
overwriting an existing capture. No backup files are deleted, including writes
through file descriptors opened before capture. Deployment preserves this
recovery storage on later runs. Backup cleanup is a separate authorized task.

Modified, unknown, or symlinked content detected before capture stays in place
and aborts deployment. A race detected after capture returns an error and
retains the captured tree; a recreated `.codex/skills/` is also preserved and
reported as an error. Inspect both exact locations and reconcile the intended
source before retrying; do not delete a backup merely because verification
failed. The deployment checker rejects surviving duplicate discovery. Do not
hand-edit active mirrors. If exclusive atomic rename is unavailable, migration
fails without a fallback that can overwrite or delete data.

Task intake follows `shared/rules/task-scoped-reading.md`. Mode-specific skill
procedures live in linked `references/` files and are loaded only for the current
operation or engine state; commands still run from the repository root.
