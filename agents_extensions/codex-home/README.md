# Reusable Codex home configuration

This source controls the GPT-6 model default, low worker defaults, global
orchestration guidance, and four bounded agent profiles. Profile identifiers
retain their existing names so deployment does not remove user files; all four
use GPT-6 Astra. The explorer and bounded worker use low effort; integration
and difficult-problem profiles explicitly use high effort.

Deploy from a dispatch worktree with the project interpreter:

```bash
.venv/bin/python scripts/deploy_codex_home.py --codex-home "$HOME/.codex" --dry-run
.venv/bin/python scripts/deploy_codex_home.py --codex-home "$HOME/.codex"
.venv/bin/python scripts/deploy_codex_home.py --codex-home "$HOME/.codex" --check
```

In a linked worktree, use the canonical checkout's `.venv/bin/python` when
that worktree has no interpreter. Home deployment is explicit and separate
from `npm run agents:deploy`, which controls repository mirrors.

The deployer preserves authentication, MCP configuration, project trust,
plugin settings, hooks state, feature settings, the main task's reasoning
effort, and unrelated files. Changed originals are backed up under the target
home's `.deploy-backups/` directory. A failure must be investigated using its
receipt before retrying; per-file atomic replacement is not a multi-file
transaction. Dry-run and check modes do not write.

After deployment, newly loaded profiles use the Git-controlled settings.
An already running task may still expose its previous profile catalog. Verify
its live catalog before selecting a profile, or explicitly select Astra/low
for a bounded helper until the task reloads the catalog.
