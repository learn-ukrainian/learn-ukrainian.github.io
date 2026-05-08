# codex-tools deep review — joint Claude + Codex report

**Status:** CONVERGED — Claude + Codex independent reviews complete and agree on root cause. Fix dispatch is the next step (pending user sign-off).

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

## Convergence (post-Codex independent review, 2026-05-08T21:38 UTC)

Codex's full reply is preserved in `messages` table id #570 (task `codex-tools-deep-review-2026-05-08`); the exchange unfortunately did not land in the pipeline channel thread because of a tooling miss (see "Bridge tooling note" below).

### Both reviews agree on root cause

| Finding | Claude (independent) | Codex (independent) | Material disagreement? |
|---|---|---|---|
| Wiki packet ingestion | ✅ FINE — byte-identical, 244 lines across 3 writers | ✅ FINE — 41,374 bytes, identical SHA256 `84e1bc0e…` | None |
| Writer prompt content | ✅ FINE — identical 1610 lines | _(not separately checked, but no objection)_ | None |
| Sandbox blocking MCP | Refuted (`--dangerously-bypass-approvals-and-sandbox` applied for `mode=workspace-write`) | **Stronger refutation:** `turn_context` in rollouts shows `sandbox_policy: danger-full-access`, `permission_profile: disabled`, `approval_policy: never` | None — Codex's evidence is stricter |
| MCP tools visible to model at writer time | Inferred no — model substitutes `exec_command` shell-grep | **Direct evidence — model itself articulates it:** rollout line 10 in both bakeoff codex sessions says "requested `mcp__sources__...` tools 'are not exposed in this session'" and "`sources` MCP tools 'are not currently exposed in the tool list'" | None — Codex's evidence is direct, mine was inferred |
| Tool calls in rollout | 39 + 59 = 98 `function_call` events, ALL `exec_command`/`write_stdin` | Same: 38+59 shell, zero `mcp__*` | None |
| Pre-flight `mcp_config_resolved.resolution_status='ok'` is misleading | YES — only verifies config string resolution | YES — proves config shape, not runtime tool injection | None |
| Likely root cause: `type="streamable-http"` field | Identified as Claude-format Field codex CLI doesn't understand; user's `~/.codex/config.toml` working shape uses ONLY `url` | Identified same: "successful manual proof used `~/.codex/config.toml` URL, not the v7 `-c type` path"; needs v7-shaped reproducer to confirm | None |

### What Codex contributed that Claude didn't have

1. **Direct rollout-text evidence the model knew the tools were missing** (cited above) — much stronger than Claude's inference-from-behavior.
2. **Sandbox refutation via `turn_context`** in the rollout JSONL — a cleaner refutation than Claude's "the bypass flag is in the code path."
3. **Concrete v7-shaped smoke-test reproducer** for confirming the `type` field is the breaking point:
   ```
   codex exec -c 'mcp_servers.sources.url="http://127.0.0.1:8766/mcp"' \
              -c 'mcp_servers.sources.type="streamable-http"' \
              --skip-git-repo-check -C "$PWD" --color never -m gpt-5.5 \
              --dangerously-bypass-approvals-and-sandbox --enable multi_agent \
              "call mcp__sources__verify_words for word 'кіт'"
   ```
   Pre-fix expectation: model fails to call MCP, falls back to shell or fabricates.
   Post-fix expectation (after stripping `type` from codex flags): model calls `mcp__sources__verify_words` and returns a real result.
4. **Stronger fix recommendation: positive runtime gate**, not just preflight + theatre detection. Specifically: tie into `_McpRuntimeObserver` in `scripts/agent_runtime/runner.py:411-470`, postcondition `tool_calls_total > 0` for `*-tools` writers, treat zero MCP calls as **hard failure** (currently only emits a `tool_theatre` warning).

### What Codex deferred (and why it doesn't block this fix)

- **Gemini-tools root cause not separately verified.** Codex confirmed gemini's `writer_tool_calls.json: []` and packet-identical-to-codex+claude, but didn't open a gemini rollout to confirm the same "tools not exposed" mechanism. Same outcome, unverified root cause.
- This is consistent with the user's "one at a time, codex first" instruction and the open follow-up issue #1811 (gemini deploy invariant violations) which is a likely contributor to gemini's failure.

---

## Final fix plan (converged)

**Three changes, sized for one Codex dispatch:**

### Change 1: Strip Claude-format fields when emitting codex `-c` flags

`scripts/agent_runtime/tool_config.py` — add a sanitizer that drops `type` (and any other non-codex field) before flattening:

```python
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
    no MCP tools (#XXXX). Verified empirically 2026-05-08:
    rollout-2026-05-08T11-54-40-* line 10 says `mcp__sources__*`
    tools "are not exposed in this session" when the v7 dispatch
    path is used; the working interactive ~/.codex/config.toml uses
    ONLY `url` (no `type`).
    """
    return {k: v for k, v in server_config.items() if k in _CODEX_MCP_SERVER_FIELDS}
```

Wire into `_codex_mcp_servers` line 87-91:

```python
selected = {
    server_name: _codex_sanitize_server_config(usable_servers[server_name])
    for server_name in requested
    if server_name in usable_servers
}
```

### Change 2: Add positive runtime gate

In `scripts/build/v7_build.py` writer phase post-condition, fail-loud when a `*-tools` writer produces zero `mcp__sources__*` calls:

- Required check: `phase_writer_summary.tool_calls_total > 0` for any writer ending in `-tools`
- Failure: `LinearPipelineError("MCP_TOOLS_NEVER_INVOKED", writer=…, expected="≥1 mcp__sources__* call", got=0)`
- Rationale: catches future regressions (e.g. similar config-shape bugs in gemini-tools, or MCP server downtime mid-build) without depending on string matching the model's prose

### Change 3: Update tests

- `tests/test_agent_runtime_tool_config.py` — add a test that `build_mcp_tool_config("codex", mcp_servers=["sources"])[0]` returns `{"mcp_servers": {"sources": {"url": "..."}}}` (NO `type` field). The current test at lines 66-103 actively verifies the WRONG behavior (asserts `type: streamable-http` is present in the dict — needs flipping).
- `tests/test_v7_writer_dispatch.py` — same field-presence flip at lines 86-87.
- New regression test: a smoke test running Codex's reproducer command above, asserting at least one `mcp__*` function_call lands in the rollout.

---

## Verification plan

1. **Unit test:** the codex tool_config emits ONLY `url` (no `type`).
2. **Integration smoke (Codex's reproducer above):** post-fix, the model calls `mcp__sources__verify_words` and returns a real result.
3. **Bakeoff re-run:** `.venv/bin/python scripts/build/v7_build.py a1 my-morning --writer codex-tools --telemetry-out audit/bakeoff-fix-verify.jsonl`. Pre-fix evidence: `tool_calls_total=0`, `writer_tool_calls.json=[]`. Post-fix expectation: `tool_calls_total>0`, `writer_tool_calls.json` has real `mcp__sources__*` entries (not `exec_command`).
4. **Negative test:** with the new positive runtime gate, deliberately misconfigure (e.g. point sources URL at port 9999) and confirm v7 fails with `MCP_TOOLS_NEVER_INVOKED` instead of producing theatrical output silently.

---

## Bridge tooling note (for follow-up, not blocking this fix)

Lost ~45 minutes on a tooling miss this session: `ab post pipeline … --to codex` queues a delivery in the `deliveries` table, but **no command processes channel deliveries**. `process-codex-all` only drains the legacy `messages` table. Re-dispatched via `ab ask-codex` which uses `messages` flow correctly. The original channel post `f65152cffec14096b153e07b626326b3` is still pending in `deliveries` and will likely never be processed.

Worth a follow-up issue: either (a) `process-codex-all` should also drain channel deliveries, or (b) `ab post` should auto-trigger dispatch like `ask-codex` does, or (c) docs should clearly say "post-only, no auto-dispatch — use `ab ask-*` for that."

---

## Status

✅ Independent reviews complete (Claude + Codex)
✅ Findings converged — agree on root cause + fix direction
⏳ Awaiting user go-ahead to dispatch fix (Codex worktree, mechanical patch, sized for one PR)
⏳ Bakeoff re-run after fix lands → expect non-zero MCP calls for codex-tools
⏳ gemini-tools review opens after codex-tools fix is verified (per "one at a time" user direction)
