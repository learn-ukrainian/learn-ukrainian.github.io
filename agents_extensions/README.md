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
