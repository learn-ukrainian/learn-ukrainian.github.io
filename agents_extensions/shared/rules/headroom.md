---
paths:
  - "AGENTS.md"
  - "CLAUDE.md"
  - "GEMINI.md"
  - ".mcp.json"
  - ".cursor/mcp.json"
  - "agents_extensions/**"
  - "scripts/**"
---

# Headroom Shared Context

Headroom is the shared compression and memory layer for local agents.

## Runtime

- Proxy health: `http://127.0.0.1:8787/health`
- Stats: `http://127.0.0.1:8787/stats`
- MCP server name: `headroom`
- MCP transport: stdio via `headroom mcp serve`
- Start command: `headroom install start --profile default`

## Usage Rule

Use Headroom for context that would otherwise be pasted wholesale between
agents:

- long handoffs
- large logs
- long tool outputs
- search-result bundles
- review outputs
- large validation/build output

As a practical threshold, if content is roughly over 200 lines or 20 KB, call
`headroom_compress` first, pass the returned hash plus a short summary, and use
`headroom_retrieve` only when exact detail is needed.

Do not use Headroom memory as factual authority for curriculum content. Retrieve
the original content or inspect the repository/source files when exact claims
matter.

Do not run `headroom learn --apply` unless the user explicitly requests it. It
can rewrite agent instruction files such as `AGENTS.md`, `CLAUDE.md`, and
`GEMINI.md`.

## Git-Tracked Source Of Truth

Track durable Headroom setup in git here:

- `.mcp.json` for repo-level Codex-compatible MCP config.
- `.cursor/mcp.json` for repo-level Cursor MCP config.
- `agents_extensions/shared/settings.local.json` for shared runtime tool
  permissions such as `mcp__headroom__*`.
- `agents_extensions/shared/rules/headroom.md` for the shared agent rule.
- launcher scripts such as `start-claude.sh`, `start-codex.sh`, and
  `scripts/ensure_headroom.sh` for startup health checks.

Do not track generated or machine-local runtime dirs:

- `.claude/`
- `.codex/`
- `.agent/`
- `.agents/`
- `.gemini/`

Those dirs are deployed from `agents_extensions/` with `npm run agents:deploy`
and are intentionally ignored.
