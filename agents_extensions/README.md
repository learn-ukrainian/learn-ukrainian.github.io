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
The deploy helper retires a legacy `.codex/skills/` file only when its bytes
match tracked current source or a regular-file blob in that exact source path's Git history. Modified, unknown, or symlinked legacy content
aborts deployment and remains intact for explicit reconciliation. The deployment
checker rejects a surviving legacy discovery tree. Do not hand-edit mirrors.

Task intake follows `shared/rules/task-scoped-reading.md`. Mode-specific skill
procedures live in linked `references/` files and are loaded only for the current
operation or engine state; commands still run from the repository root.
