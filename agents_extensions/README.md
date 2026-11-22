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
├── codex/           # Codex-owned durable rules, memory, and overlays
└── cursor/          # Cursor project rules, skills, and MCP configuration
```

Deploy extensions with:

```bash
npm run agents:deploy
```

`npm run claude:deploy` remains as a compatibility alias.

## Codex skill discovery

`npm run agents:deploy` runs the installed lu-machinery deployer
(`lu_machinery.agent_deploy`). It composes the release's fleet rules, skills,
hooks and prompts with the product sources that `agents_extensions/deployment.v1.json`
names (`shared/`, `codex/`, `agy/`, `cursor/`), refuses a product file at a release path, and
deploys shared skills to `.agents/skills/`, the single Codex discovery root. `.codex/`
continues to receive its hooks, config, and other shared resources, but no skills.
It owns only the files its manifest (`.deploy-state/agent-deploy.v1.json`) records;
`--check` verifies every deployed file's bytes and mode.
It atomically moves
the whole legacy `.codex/skills/` tree into a unique
`.codex/retired-skills/<capture>/skills` backup outside skill discovery, without
overwriting an existing capture. No backup files are deleted, including writes
through file descriptors opened before capture. Deployment preserves this
recovery storage on later runs. Backup cleanup is a separate authorized task.

Modified source, unknown entries, or symlinked content detected before capture stay in place
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

## Cursor project discovery

Edit and commit the sources in `agents_extensions/cursor/`. Run
`npm run agents:deploy` to generate the ignored `.cursor/` tree, including
the `.mdc` rules, the project skill, and `mcp.json`.
