# Current — Claude Session Handoff (2026-06-13)

> Router: read `docs/session-state/current.md` first.
> **Latest detailed handoff: `docs/session-state/2026-06-13-claude-atlas-pairfix-site-rename-git-cleanup.md`** — read top-to-bottom.
>
> **✅ DONE this session (all on `origin/main` `19c89e6aa4`, deploy-verified live):**
> - `starlight/` → `site/` rename (#3062/#3065) — symlink removed, all refs updated, live 200.
> - Word Atlas **pair-slug enrichment bug fixed** (`19c89e6aa4`, #2985): 67 core verb pairs were thin; варити now shows СУМ-20 + idioms. The data was always fetchable live — the pipeline queried the joined pair string and cached the miss.
> - Vocab→Atlas "more →" link (#3056).
> - **Git fully cleaned** (user order): 1 branch (main), 1 worktree, 0 stashes; remote = main + dependabot. **Recovery SHAs in the detailed handoff** — esp. 🔴 `codex/agy-mcp-fix c880dab111` (likely the #3060 solution — check before redoing #3060).
>
> **⏭️ Next:** (1) #3060 wire sources MCP into agy — CHECK `codex/agy-mcp-fix` first; (2) Atlas synonym gate (`_A1_SENSE_SYNONYMS`) + cached-miss refetch; (3) #3061/#3063 gemini→agy; grok-build validation.
>
> **⚠️ Lessons:** `core.bare` flips→true mid-session (#2842; heal `git config core.bare false`); never `mv` node_modules across a rename (reinstall); `enrich_manifest.py` ignores argv + is silent + must run as ONE `run_in_background` process (never concurrent — they race the manifest).
>
> Prior handoff (superseded): `2026-06-13-claude-translation-shipped-v2-killed.md`. Production: learners on A1.
