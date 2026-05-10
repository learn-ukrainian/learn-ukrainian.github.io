# Codex brief — #1805 _McpRuntimeObserver hardening EPIC

**Issue:** #1805. Read full body for the 4 sub-tasks: `gh issue view 1805`.
**Task ID:** `codex-1805-mcp-observer-hardening`
**Mode:** `--mode danger --worktree`
**Base:** `origin/main`

## Worktree

```
git worktree add -b codex-1805-mcp-observer .worktrees/codex-1805-mcp-observer origin/main
cd .worktrees/codex-1805-mcp-observer
```

## What to fix — all 4 sub-tasks in one PR

All target `scripts/agent_runtime/runner.py` (the `_McpRuntimeObserver` class) and `tests/test_mcp_init_observability.py`.

### Sub-task A — URL normalization

`_servers_for_failed_line` uses exact string compare; `_codex_server_is_usable` rstrips trailing `/`. Normalize both sides (rstrip `/`) before comparing. Add a test row that exercises `http://x:8766/mcp` matching against configured `http://x:8766/mcp/`.

### Sub-task B — multi-server attribution

When `_MCP_TRANSPORT_FAILURE_RE` matches but extracted URL doesn't map to any configured server (or no URL extracted), STOP fanning out blame across all unresolved servers. Instead emit a structured warning event `mcp_runtime_unattributed_failure` with the raw line as a field. Add a test that confirms only the warning fires (not N spurious `failed` events).

### Sub-task C — same-server ready+failed ordering

Pin semantics. Recommend: **last-wins, failed trumps ready** — so a server that emits `mcp: sources/x started` followed by `ERROR rmcp::transport::worker:` ends up reported as `failed`, not flapping. Document the choice in the docstring of `_emit_ready` / `_emit_failed`. Add a test that fires both signals and asserts a single `failed` event lands (suppressing the prior `ready`).

### Sub-task D — codex stdout fixture for regex drift

Capture a real codex stdout sample exercising both `mcp: server/tool started` AND `(completed)` shapes. Likely sources: existing audit JSONLs (`audit/bakeoff-*/`) or run codex once locally with the `sources` MCP and capture stdout. Bake into `tests/fixtures/codex_mcp_init_stdout.txt` (or similar). Add a test that loads the fixture, runs `_MCP_TOOL_EVENT_RE` over it, and asserts the expected event count + per-tool breakdown.

## #M-4 evidence (commit body)

For each of A/B/C/D, paste the relevant `pytest -v` output block. For D, paste the captured codex stdout sample's first 30 lines.

## Pre-submit checklist (AGENTS.md:11-26) — applies. Extra: < 20 files changed (check; test fixtures count).

## Workflow

1. Worktree setup → 2. Implement A/B/C/D in order, committing each as a separate logical commit with conventional format → 3. ruff + pytest after each → 4. Capture evidence → 5. Final commit message stack: `fix(mcp-observer): URL normalization (#1805)`, `fix(mcp-observer): unattributed-failure warning instead of fan-out (#1805)`, `feat(mcp-observer): pin last-wins ordering (#1805)`, `test(mcp-observer): codex stdout fixture for regex drift (#1805)` → 6. Push → 7. `gh pr create` (title `fix(mcp-observer): observer hardening (4 sub-tasks, #1805)`) → 8. No auto-merge.
