# codex-tools deep review — joint Claude + Codex report

**Status:** DRAFT — Claude's independent findings recorded. Codex independent review pending. Convergence + final findings to follow.

**Date:** 2026-05-08
**Trigger:** User hypothesis — "Both codex-tools and gemini-tools have bugs, the agents are running in sandbox and cannot use our tools or do not know about our tools and are not using the wiki."
**Bakeoff under review:** `audit/bakeoff-2026-05-08-codex-only/` (a1/my-morning, codex-tools writer, 2026-05-08T12:19-12:22 UTC)
**Channel thread:** `f65152cffec14096b153e07b626326b3` in `pipeline`
**Predecessor:** `2026-05-08-bakeoff-mcp-wiring-and-writer-theatre.md` handoff (the diagnosis this report partly overturns).

---

## Executive summary (Claude's findings, pre-convergence)

The user's hunch is essentially correct. The "writer-prompt theatre" framing from last night was a downstream symptom misread as the root cause. The actual root cause is one layer lower: **codex CLI silently rejects our MCP server config** because v7 emits a Claude-format `type` field that codex doesn't understand, leaving the model with an empty MCP tool catalog. The model rationally substitutes `exec_command` (codex's built-in shell) for the missing MCP tools, producing 39-59 shell-grep tool calls per writer run that pipeline telemetry filters out as "0 tool calls."

| Layer | Status | Owner |
|---|---|---|
| Wiki / knowledge packet ingestion | ✅ FINE — byte-identical across all 3 writers (244 lines, no diff) | n/a |
| Writer prompt content | ✅ FINE — byte-identical across all 3 writers (1610 lines) | n/a |
| `mcp_config_resolved` pre-flight | ⚠️ MISLEADING — verifies config string resolution, NOT model-side tool registration | observability gap |
| Codex MCP config shape (v7 → codex CLI) | 🚨 BROKEN — `type="streamable-http"` field is Claude-format; codex CLI rejects | `_codex_mcp_servers` (root cause) |
| Codex model behavior given empty MCP catalog | ⚠️ RATIONAL FALLBACK — substitutes `exec_command` shell calls (39-59 per run) | not a bug, but a tell |
| Telemetry of codex tool calls | ⚠️ FILTERED — `tool_calls_total: 0` only counts `mcp__sources__*`, hides 39-59 `exec_command` calls | observability gap #2 |
| Last night's "writer-prompt theatre" diagnosis | 🟥 PARTLY WRONG — was based on filtered telemetry; the model didn't "choose not to call tools," it called many tools, just none of them MCP | re-frame |

---

## Evidence

### E1. Knowledge packet is identical across writers

```
$ wc -l audit/bakeoff-2026-05-08-codex-only/gpt55/knowledge_packet.md \
        audit/bakeoff-2026-05-08-claude-gemini-diagnostic/{claude,gemini}/knowledge_packet.md
   244 ...codex-only/gpt55/knowledge_packet.md
   244 ...claude/knowledge_packet.md
   244 ...gemini/knowledge_packet.md

$ diff -q codex/...kp.md claude/...kp.md   # no output → identical
$ diff -q codex/...kp.md gemini/...kp.md   # no output → identical
```

Refutes "not using the wiki" at the **input** layer. The wiki content reaches all three writers identically. The "feels like the model isn't using the wiki" symptom is downstream of E4.

### E2. Writer prompt is identical across writers

```
$ wc -l .../writer_prompt.md  # all three: 1610 lines
$ diff -q codex/writer_prompt.md claude/writer_prompt.md   # identical
```

Same prompt, same instructions, same word target, same plan. Behavior divergence is purely at inference time.

### E3. `writer_tool_calls.json` paints a misleading picture

| Writer | `writer_tool_calls.json` |
|---|---|
| claude-tools | 5 entries: `mcp__sources__verify_words([47 words])` + 4× `mcp__sources__search_text(...)` returning real VESUM hits + textbook chunks |
| codex-tools | `[]` |
| gemini-tools | `[]` |

The pipeline-emitted `tool_calls_total: 0` and `tool_theatre_violations` count are derived from this filter. They count only `mcp__sources__*`-prefixed calls.

### E4. Codex's actual rollout JSONL — 39-59 real tool calls, ALL `exec_command`

Identified by matching `event_msg.payload.message` against `audit/bakeoff-2026-05-08-codex-only/gpt55/writer_prompt.md`:

```
~/.codex/sessions/2026/05/08/rollout-2026-05-08T12-05-05-019e070c-...jsonl
  user_msg_match: True
  function_calls: 39
  Distinct tool names: ['exec_command', 'write_stdin']
  Sample call 1: exec_command({"cmd":"pwd && rg --files -g 'AGENTS.md' -g 'data/vesum.db' -g 'scripts/**' ..."})
  Sample call 2: exec_command({"cmd":"rg -n \"def .*verify|verify_words|VESUM|vesum|search_text|...\" scripts ..."})
  Sample call 3: exec_command({"cmd":"find /Users/.../learn-ukrainian -maxdepth 3 -type d ..."})

~/.codex/sessions/2026/05/08/rollout-2026-05-08T11-54-40-019e0702-...jsonl
  user_msg_match: True
  function_calls: 59
  Distinct tool names: ['exec_command', 'write_stdin']
```

**The model is shelling out to grep for `vesum.db`, `verify_words`, `my-morning.md`, etc.** — it's trying to do verification by raw filesystem search because the MCP tools aren't in its catalog. Zero `mcp__sources__*` calls in either rollout.

This single observation re-frames everything from last night.

### E5. The config-shape mismatch — root cause

User's working interactive launcher config (`~/.codex/config.toml`):

```toml
[mcp_servers.sources]
url = "http://127.0.0.1:8766/mcp"
```

What v7 actually emits to `codex exec` (verified by simulating `_codex_mcp_servers` + `CodexAdapter._tool_config_flags`):

```
-c mcp_servers.sources.type="streamable-http"   ← extra field
-c mcp_servers.sources.url="http://127.0.0.1:8766/mcp"
```

The `type` field comes from `.mcp.json`:

```json
{"mcpServers": {"sources": {"type": "streamable-http", "url": "..."}}}
```

`type="streamable-http"` is a **Claude `.mcp.json` schema field** (Anthropic's MCP config format). Codex CLI does not have this in its `mcp_servers.<name>.*` schema; it auto-detects HTTP transport from the URL alone. Passing the unknown field silently breaks server registration.

**Bug location:** `scripts/agent_runtime/tool_config.py:_codex_mcp_servers` lines 70-91 select the raw server dict from `.mcp.json` and pass it through to the codex `-c` flattener verbatim. No filter to strip Claude-specific fields.

### E6. Pre-flight `mcp_config_resolved.resolution_status='ok'` is misleading

The pre-flight in `_runtime_tool_config` (linear_pipeline.py:1763) emits this event after `_codex_mcp_servers` returns. But `_codex_mcp_servers` only verifies:

1. `.mcp.json` exists and parses (line 62-64)
2. The `mcpServers` key has at least one entry (line 66-68)
3. Requested server name is in the dict and `_codex_server_is_usable` returns True (line 70-74, 87-91)

`_codex_server_is_usable` rejects only `type="sse"` and URLs ending in `/sse`. It does NOT verify that the resulting config will actually register tools on the model side. The pre-flight passes for any server config with a non-SSE URL — including ours, which fails downstream.

---

## Proposed fix (5-10 line patch — pending Codex review before applying)

In `scripts/agent_runtime/tool_config.py`, strip Claude-format fields when emitting codex `-c` flags. The fields codex understands are: `url`, `command`, `args`, `env`, `bearer_token_env_var`. The `type` field from `.mcp.json` is Claude-format and must be stripped.

```python
# scripts/agent_runtime/tool_config.py
_CODEX_MCP_SERVER_FIELDS = frozenset({
    "url", "command", "args", "env", "bearer_token_env_var",
})

def _codex_sanitize_server_config(server_config: dict) -> dict:
    """Drop Claude-format fields codex CLI doesn't understand.

    `.mcp.json` includes `type` for Claude's MCP client (e.g.
    `type="streamable-http"`). Codex CLI auto-detects HTTP transport
    from the URL scheme and does NOT have `type` in its
    `mcp_servers.<name>.*` schema. Passing the field silently breaks
    server registration on the codex side, leaving the model with
    no MCP tools (#XXXX).
    """
    return {k: v for k, v in server_config.items() if k in _CODEX_MCP_SERVER_FIELDS}
```

Wire it into `_codex_mcp_servers` line 87-91:

```python
selected = {
    server_name: _codex_sanitize_server_config(usable_servers[server_name])
    for server_name in requested
    if server_name in usable_servers
}
```

---

## Test plan to confirm fix

1. **Unit test** — `tests/test_codex_mcp_config_sanitization.py`:
   - Given `.mcp.json` with `{"sources": {"type": "streamable-http", "url": "..."}}`
   - Assert `build_mcp_tool_config("codex", mcp_servers=["sources"])[0]` returns `{"mcp_servers": {"sources": {"url": "..."}}}` (NO `type` field)
   - Assert `CodexAdapter._tool_config_flags(...)` emits ONLY `-c mcp_servers.sources.url=...` (no `mcp_servers.sources.type=...` flag)

2. **Integration test** — minimal `codex exec` subprocess matching v7's exact flag set:
   - Pre-fix: assert rollout JSONL contains zero `mcp__sources__*` function_calls; model uses `exec_command` for grep
   - Post-fix: assert rollout JSONL contains at least one `mcp__sources__verify_words` or `mcp__sources__search_text` call

3. **Bakeoff re-run** — `.venv/bin/python scripts/build/v7_build.py a1 my-morning --writer codex-tools --telemetry-out audit/bakeoff-fix-verify-codex-tools.jsonl`:
   - Pre-fix evidence: `tool_calls_total=0`, `writer_tool_calls.json=[]`, rollout has 39+ `exec_command` calls
   - Post-fix expectation: `tool_calls_total>0`, `writer_tool_calls.json` has real `mcp__sources__*` entries

---

## Remaining open questions for Codex

(These are what I want Codex to confirm/refute in his independent review.)

1. **Is the `type` field truly the problem?** Or is there a second issue (e.g., codex CLI requires explicit `mcp_servers.<name>.transport` field for HTTP)?
2. **Is the user's hunch ALSO partly right at the "agents in sandbox" layer?** I confirmed `--dangerously-bypass-approvals-and-sandbox` is applied for `mode=workspace-write` (codex.py:822-829). But is there ANOTHER sandbox layer that might block `127.0.0.1:8766`?
3. **Does gemini-tools have the same bug?** PR #1810 wired MCP for gemini-tools using a different config path (`mcp_server_names` list, not `mcp_servers` dict). It also got `[]` in `writer_tool_calls.json`. Same root cause or different bug? (User explicitly said one at a time — codex first, gemini after — so leave this open.)
4. **Telemetry observability gap fix.** Should `phase_writer_summary` distinguish `mcp_tool_calls_total` from `total_function_calls`? The current "0 tool calls" framing misled the diagnosis for a full session.

---

## Convergence (post-Codex review)

_Pending. Will be filled in after Codex's independent findings land and we run `ab discuss --with claude,codex --max-rounds 2` if there's any disagreement._
