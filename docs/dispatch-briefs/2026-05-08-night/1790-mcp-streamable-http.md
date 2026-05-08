# Dispatch brief: add Streamable HTTP transport to sources MCP server (#1790 root cause fix)

> **Issue:** #1790 — codex-tools writer 0 tool calls
> **Root cause** (verified 2026-05-08): `~/.codex/config.toml` declares `mcp_servers.sources.url = "http://127.0.0.1:8766/sse"`. The `sources` server (`.mcp/servers/sources/server.py:1822-1846`) only exposes legacy SSE transport (`/sse` + `/messages/`). Codex 0.129's MCP client uses Streamable HTTP exclusively (`codex mcp add --help` confirms `--url` configures Streamable HTTP only — no SSE option). Codex POSTs `initialize` to `/sse` → server returns HTTP 405 Method Not Allowed → MCP init fails → writer dispatches silently lose all `mcp__sources__*` tools.
> **Scope:** ~50-100 LOC + tests. Single PR.
> **Agent:** Codex (mechanical addition of one transport route)
> **Worktree:** mandatory.

## Reproduce the bug first (verify the diagnosis)

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
codex --dangerously-bypass-approvals-and-sandbox -C "$PWD" --print 'call mcp__sources__verify_words for "кіт"'
# Expect: "MCP client for `sources` failed to start: ... Method Not Allowed"
# OR
codex exec --dangerously-bypass-approvals-and-sandbox --enable multi_agent -C "$PWD" - <<<"call mcp__sources__verify_words for word 'кіт'"
# Expect: "I can't call mcp__sources__verify_words because that tool/server isn't available"
```

Confirm both fail before starting the fix.

## Worktree instructions (mandatory)

```bash
.venv/bin/python scripts/delegate.py dispatch \
    --agent codex --mode danger --worktree --base origin/main \
    --task-id codex-1790-mcp-streamable-http \
    --prompt-file docs/dispatch-briefs/2026-05-08-night/1790-mcp-streamable-http.md
```

Lands in `.worktrees/dispatch/codex/codex-1790-mcp-streamable-http`.

## What to build

Add **Streamable HTTP transport** at `/mcp` endpoint in `.mcp/servers/sources/server.py`, **alongside** the existing `/sse` + `/messages/` SSE transport. Backward compatibility is critical — Claude Code's `.mcp.json` declares `"type": "sse"` and uses the existing `/sse` route. We CANNOT remove or break it.

Key API (already verified in repo):

```python
from mcp.server.streamable_http import StreamableHTTPServerTransport
# Transport instance per request, OR shared with session_id management.
# StreamableHTTPSessionManager does NOT exist in our installed mcp version —
# do NOT import it. Use StreamableHTTPServerTransport directly.
```

The MCP SDK Python examples (search MCP-SDK repo or docs) show the standard pattern:
1. Create a session manager-style helper (we'll wrap our own since SessionManager isn't available)
2. Mount handler at `/mcp` accepting POST (initialize, requests) and GET (SSE-stream-style replies for long-lived ops)
3. Reuse the same `Server` instance (`server` var in our file) — do NOT create a second server

Look at `.venv/lib/python3.12/site-packages/mcp/server/streamable_http.py` directly — it's <2000 LOC and includes example usage in docstrings. The `StreamableHTTPServerTransport` class has `connect()` returning streams to pass to `server.run(...)` similarly to `SseServerTransport.connect_sse()`.

## Acceptance criteria (numbered, all required)

1. **`/mcp` endpoint added** to the Starlette `app` routes in `.mcp/servers/sources/server.py:1840-1846`. Accepts POST (per MCP Streamable HTTP spec). Reuses the same `server` instance as `/sse`.
2. **Existing `/sse` + `/messages/` endpoints UNCHANGED.** Backward compatibility for Claude Code (`.mcp.json` uses `"type": "sse"`).
3. **`/health` endpoint UNCHANGED.**
4. **Test**: a new test file `tests/test_mcp_sources_streamable_http.py` with at minimum:
   - Boot the server in-process (or via subprocess)
   - POST `{"jsonrpc":"2.0","id":1,"method":"initialize","params":{...}}` to `/mcp`
   - Assert response is valid MCP `initialize` reply (HTTP 200, JSON body with `jsonrpc=2.0` and `result.capabilities`)
   - POST `{"jsonrpc":"2.0","id":2,"method":"tools/list"}` and assert tools list contains at least `verify_words` (or whatever names exist in the live server)
   - **Smoke**: also assert the existing `/sse` GET endpoint still streams events (backward compat lock-in)
5. **Live verification** — after starting the patched server (kill PID 93362 if running, restart with the new code), run BOTH:
   ```bash
   curl -sv -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' http://127.0.0.1:8766/mcp
   # Expect: 200 with valid MCP initialize result
   curl -sv --max-time 2 http://127.0.0.1:8766/sse
   # Expect: SSE stream emits "event: endpoint" followed by "data: /messages/?session_id=..."
   ```
   Capture both responses in the PR body.
6. **Server-startup print line** updated to advertise the new `/mcp` endpoint (mirror lines 1848-1850).
7. `ruff check` clean.
8. `.venv/bin/pytest tests/test_mcp_sources*.py -x` passes (existing + new).

## Numbered execution steps

1. `git worktree add` — handled by delegate runner.
2. **Reproduce the bug** with the codex command above. Confirm.
3. Read `.mcp/servers/sources/server.py` lines 1800-1867 (the SSE transport setup).
4. Read `.venv/lib/python3.12/site-packages/mcp/server/streamable_http.py` to understand `StreamableHTTPServerTransport`.
5. Read 1-2 examples in `mcp` SDK if any (`.venv/lib/python3.12/site-packages/mcp/examples/` or docstrings).
6. Implement the `/mcp` route. Reuse the `server` instance. Run server.run(streams[0], streams[1], server.create_initialization_options(), stateless=True) the same way the SSE handler does.
7. Add server-startup print for `/mcp` URL.
8. Write the new test file `tests/test_mcp_sources_streamable_http.py`.
9. `.venv/bin/ruff check .mcp/servers/sources/server.py tests/test_mcp_sources_streamable_http.py`
10. `.venv/bin/pytest tests/test_mcp_sources*.py -x`
11. **Live integration test** — KILL the running MCP server (PID 93362) and RESTART with the new code:
    ```bash
    kill 93362  # whatever PID is on 8766 — verify with: lsof -nP -iTCP:8766 -sTCP:LISTEN
    nohup .venv/bin/python .mcp/servers/sources/server.py --standalone > /tmp/mcp-sources.log 2>&1 &
    sleep 2
    # Run the curl tests from AC#5 + capture output for PR body
    ```
12. **Final verification** — restore the original `~/.codex/config.toml` URL temporarily back to `http://127.0.0.1:8766/sse`, then ALSO test changing it to `http://127.0.0.1:8766/mcp`:
    ```bash
    cp ~/.codex/config.toml ~/.codex/config.toml.bak
    sed -i.tmp 's|http://127.0.0.1:8766/sse|http://127.0.0.1:8766/mcp|' ~/.codex/config.toml
    codex exec --dangerously-bypass-approvals-and-sandbox --enable multi_agent -C "$PWD" - <<<"call mcp__sources__verify_words for word 'кіт' and report"
    # Expect: actual JSON result from VESUM, not "tool unavailable"
    cp ~/.codex/config.toml.bak ~/.codex/config.toml  # restore original
    ```
    Capture the success output for PR body. Restore `~/.codex/config.toml` to original `/sse` URL — the user will switch it manually after merge.
13. Commit: `feat(mcp): add streamable HTTP transport at /mcp endpoint (#1790)`
14. `git push -u origin codex-1790-mcp-streamable-http` (branch name auto-derived).
15. `gh pr create` with title + body covering: root cause analysis, fix approach, AC checklist, live verification curl outputs, instructions for user (after merge: switch `~/.codex/config.toml` URL from `/sse` to `/mcp` and restart MCP server).
16. **Do NOT auto-merge.** Report PR URL.

## Out of scope (file as separate issue if encountered)

- The writer-dispatch silently swallows MCP init failures — `audit/bakeoff-2026-05-08-codex-only/gpt55/writer_tool_calls.json` is `[]` with no error trail. The codex adapter should propagate MCP init errors to telemetry. Fix in a separate PR; this dispatch focuses on the transport.
- `.mcp.json` (Claude Code's config) — leave UNCHANGED. Claude Code uses `"type": "sse"` and that's working fine.
- Don't refactor the existing SSE handler.
- Don't change tool definitions or `mcp__sources__*` semantics.
- Don't add Streamable HTTP support to other MCP servers (`.mcp/servers/openaiDeveloperDocs` etc.) — out of scope.

## Why this matters

This unblocks A1. Without a working MCP transport for codex CLI, no codex-tools writer can call `verify_words` / `search_text` / etc. → no real grounded content generation → bakeoff signal invalid → writer-selection signoff blocked → A1 vertical slice can't ship.

The fix is mechanical (one route addition) but architectural (transport upgrade). After merge + user switches config URL, the bakeoff retry should produce real tool calls and a fair writer-selection signal.
