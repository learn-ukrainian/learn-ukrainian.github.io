# Dispatch Brief: #1812 — strip Claude-format `type` field from codex MCP `-c` flags

**Issue:** #1812 (full evidence + ACs there)
**Predecessor report:** `audit/codex-tools-review-2026-05-08/REPORT.md` (read first — explains *why*)
**Branch:** `codex-1812-mcp-type-strip`
**Worktree:** `.worktrees/codex-1812-mcp-type-strip`
**Mode:** danger (workspace-write needs danger so codex CLI bypass-sandbox flag activates for any pre-push smoke testing you do)
**Base:** `origin/main`
**Estimated size:** ~5-15 LOC source code + ~30-60 LOC tests. One PR.

---

## Worktree setup (mandatory — see `.claude/rules/delegate-must-use-worktree.md`)

```bash
git worktree add -b codex-1812-mcp-type-strip .worktrees/codex-1812-mcp-type-strip origin/main
cd .worktrees/codex-1812-mcp-type-strip
```

DO NOT branch in the main checkout. The user is working there. Stay isolated.

---

## What you're fixing

The TL;DR (full version in #1812 + the report): codex CLI doesn't recognize `type="streamable-http"` in its `mcp_servers.<name>.*` schema. v7 currently emits this Claude-format field to `codex exec` via `-c` flags, and codex silently rejects the server registration. The model ends up with NO `mcp__sources__*` tools in its catalog and substitutes shell-grep via `exec_command`. The user's working `~/.codex/config.toml` proves the fix shape: only `url` is needed; `type` must be stripped for codex.

---

## Three changes, sized for one PR

### Change 1 — `scripts/agent_runtime/tool_config.py`: strip Claude-format fields for codex

Add a sanitizer constant + helper, and wire it into `_codex_mcp_servers`:

```python
# Near the top of the module, with other constants
_CODEX_MCP_SERVER_FIELDS = frozenset({
    "url", "command", "args", "env", "bearer_token_env_var",
})


def _codex_sanitize_server_config(server_config: dict) -> dict:
    """Drop fields codex CLI's mcp_servers schema does not recognize.

    `.mcp.json` includes Claude-format fields (notably `type`, e.g.
    `type="streamable-http"`). Codex CLI auto-detects HTTP transport
    from the URL scheme and does NOT have `type` in its
    `mcp_servers.<name>.*` schema; passing the unknown field silently
    breaks server registration on the codex side and leaves the
    model with no MCP tools.

    Empirical evidence (#1812): bakeoff rollout
    ~/.codex/sessions/2026/05/08/rollout-2026-05-08T11-54-40-*.jsonl
    line 10 says "requested mcp__sources__... tools 'are not exposed
    in this session'" when the v7 dispatch path is used. The
    interactive ~/.codex/config.toml that DOES work uses ONLY `url`
    (no `type`).
    """
    return {k: v for k, v in server_config.items() if k in _CODEX_MCP_SERVER_FIELDS}
```

Then in `_codex_mcp_servers`, wrap BOTH the no-explicit-request branch (lines ~76-79 of current file) AND the requested branch (lines ~87-91):

```python
# Before:
if not requested:
    if usable_servers:
        return usable_servers, diagnostics(...)
# After:
if not requested:
    if usable_servers:
        return (
            {name: _codex_sanitize_server_config(cfg)
             for name, cfg in usable_servers.items()},
            diagnostics(...),
        )

# Before:
selected = {
    server_name: usable_servers[server_name]
    for server_name in requested
    if server_name in usable_servers
}
# After:
selected = {
    server_name: _codex_sanitize_server_config(usable_servers[server_name])
    for server_name in requested
    if server_name in usable_servers
}
```

### Change 2 — positive runtime gate

Find the writer-phase post-condition in `scripts/build/v7_build.py` or `scripts/build/linear_pipeline.py` (writer phase, ~line 320-380 of v7_build.py, or in `invoke_writer` / its caller in linear_pipeline.py:1822+). Add:

```python
# After phase_writer_summary is emitted, BEFORE moving on to enrich/review.
if writer.endswith("-tools") and phase_writer_summary["tool_calls_total"] == 0:
    raise LinearPipelineError(
        "MCP_TOOLS_NEVER_INVOKED",
        writer=writer,
        module=f"{level}/{slug}",
        expected="≥1 mcp__sources__* call from a -tools writer",
        got=0,
        hint=(
            "Pre-flight `mcp_config_resolved.resolution_status='ok'` only "
            "verifies config string resolution. The model must actually "
            "invoke at least one MCP tool. If this fires, check the rollout "
            "JSONL for catalog-visibility errors (e.g., "
            "'tools are not exposed in this session')."
        ),
    )
```

If `LinearPipelineError` doesn't have a kwargs-style constructor, use whatever shape the existing call sites use (`scripts/build/linear_pipeline.py` has many examples). The IMPORTANT thing: emit a fail-loud error code `MCP_TOOLS_NEVER_INVOKED`, not a warning.

This gate must NOT fire for non-`-tools` writers (e.g., legacy `claude` or `gemini` without the `-tools` suffix). The check is `writer.endswith("-tools")`.

### Change 3 — tests

Update existing tests that assert the WRONG behavior:

**`tests/test_agent_runtime_tool_config.py` lines 66-103** — there's currently a test that asserts `type: streamable-http` IS in the codex tool_config. Flip it:

```python
def test_codex_tool_config_strips_claude_format_type_field():
    """codex CLI doesn't recognize `type` — must be stripped (#1812)."""
    tc, diag = build_mcp_tool_config("codex", mcp_servers=["sources"])
    assert tc is not None
    assert "mcp_servers" in tc
    sources_cfg = tc["mcp_servers"]["sources"]
    # Must contain url
    assert "url" in sources_cfg
    # Must NOT contain `type` (codex CLI doesn't recognize it)
    assert "type" not in sources_cfg, (
        f"codex tool_config must not include the Claude-format `type` field; "
        f"got {sources_cfg!r}. See #1812."
    )
```

**`tests/test_v7_writer_dispatch.py` lines 86-87** — same flip if the assertion expects `type` field.

**New tests:**

```python
def test_codex_sanitize_server_config_drops_unknown_fields():
    from scripts.agent_runtime.tool_config import _codex_sanitize_server_config
    raw = {
        "url": "http://127.0.0.1:8766/mcp",
        "type": "streamable-http",     # Claude-format
        "transport": "http",            # hypothetical Claude future field
        "headers": {"X-Foo": "bar"},    # not in codex schema
    }
    sanitized = _codex_sanitize_server_config(raw)
    assert sanitized == {"url": "http://127.0.0.1:8766/mcp"}


def test_codex_sanitize_server_config_preserves_codex_fields():
    from scripts.agent_runtime.tool_config import _codex_sanitize_server_config
    raw = {
        "command": "/usr/local/bin/some-mcp",
        "args": ["--port", "9000"],
        "env": {"FOO": "bar"},
        "bearer_token_env_var": "MY_TOKEN",
        "type": "stdio",  # Claude-format, must drop
    }
    sanitized = _codex_sanitize_server_config(raw)
    assert sanitized == {
        "command": "/usr/local/bin/some-mcp",
        "args": ["--port", "9000"],
        "env": {"FOO": "bar"},
        "bearer_token_env_var": "MY_TOKEN",
    }


def test_positive_runtime_gate_fires_when_tools_writer_makes_zero_mcp_calls():
    """v7 must fail-loud when a -tools writer produces 0 MCP calls (#1812)."""
    # Construct a minimal phase_writer_summary with tool_calls_total=0
    # for a -tools writer; assert LinearPipelineError("MCP_TOOLS_NEVER_INVOKED")
    # is raised. Use whatever fixture style v7's existing writer-phase tests use.
    ...


def test_positive_runtime_gate_does_not_fire_for_non_tools_writer():
    """Gate must only apply to *-tools writers, not legacy claude/gemini."""
    ...
```

For the positive-gate tests, look at `tests/test_v7_writer_dispatch.py` for how to mock the writer phase and inject telemetry. Match its style.

---

## Verification (DO BEFORE pushing)

1. **Lint:**
   ```bash
   ruff check scripts/agent_runtime/tool_config.py scripts/build/v7_build.py scripts/build/linear_pipeline.py
   ```
   Must be zero errors.

2. **Unit tests:**
   ```bash
   .venv/bin/pytest tests/test_agent_runtime_tool_config.py tests/test_v7_writer_dispatch.py -v
   ```
   Must all pass.

3. **Smoke test (Codex's reproducer from the report):**

   With the MCP server already running on `127.0.0.1:8766` (it should be — the user's working session has it up), run:
   ```bash
   codex exec -c 'mcp_servers.sources.url="http://127.0.0.1:8766/mcp"' \
              --skip-git-repo-check -C "$PWD" --color never -m gpt-5.5 \
              --dangerously-bypass-approvals-and-sandbox --enable multi_agent \
              "call mcp__sources__verify_words for word 'кіт' and report the result"
   ```
   Note: this invocation has NO `type` field — it matches the post-fix codex flag set. Pre-fix (with `-c mcp_servers.sources.type="streamable-http"` ALSO present) the model says tools are unavailable. Post-fix (this command) the model should call `mcp__sources__verify_words` and return a real result.

   This is a sanity check, not a hard gate — `codex exec` may take 30-60s. If you want a tighter check, look in the rollout JSONL after the call (`~/.codex/sessions/.../rollout-*.jsonl`) for a `function_call` event with `name == "mcp__sources__verify_words"`.

4. **DO NOT run the full v7 bakeoff yourself.** That's the human's job. Reference: `MEMORY.md` rule "BATCH COMMANDS — NEVER RUN, ONLY SUGGEST." Just suggest in the PR body that the human re-fire bakeoff post-merge to verify.

---

## Commit + push + PR

Single commit (or split into "feat: sanitizer" + "feat: positive gate" + "test: flip assertions" if you prefer — your call):

```bash
git add scripts/agent_runtime/tool_config.py \
        scripts/build/v7_build.py \
        scripts/build/linear_pipeline.py \
        tests/test_agent_runtime_tool_config.py \
        tests/test_v7_writer_dispatch.py

git commit -m "$(cat <<'COMMIT'
fix(mcp): strip Claude-format type field from codex -c flags + add positive runtime gate (#1812)

codex CLI does not recognize `type` in its mcp_servers.<name>.* schema;
v7 was emitting `-c mcp_servers.sources.type="streamable-http"` which
silently broke server registration and left the model with NO MCP tools
in its catalog. Model substituted exec_command shell-grep (39-59 calls
per writer run) producing fake <verification_trace> citations that
pipeline mistook for "writer-prompt theatre."

Direct evidence (bakeoff rollout line 10 of both 2026-05-08 codex
sessions): model itself articulated "requested mcp__sources__... tools
'are not exposed in this session'."

Changes:
- _codex_sanitize_server_config: drop fields outside
  {url, command, args, env, bearer_token_env_var}.
- Positive runtime gate in v7 writer phase: fail-loud
  MCP_TOOLS_NEVER_INVOKED when *-tools writer produces 0 MCP calls.
- Flip 2 existing tests that asserted the wrong behavior.
- Add 4 new tests (sanitizer drops unknown / preserves known;
  positive gate fires correctly / scopes to -tools).

Pre-flight `mcp_config_resolved.resolution_status='ok'` is now known
to verify config string resolution only, NOT runtime tool injection.
The positive runtime gate is the actual safety net.

Refs: audit/codex-tools-review-2026-05-08/REPORT.md (Claude + Codex
converged independent reviews).
COMMIT
)"

git push -u origin codex-1812-mcp-type-strip

gh pr create --title "fix(mcp): strip codex -c type field + positive runtime gate (#1812)" \
  --body "$(cat <<'PRBODY'
## Summary
- Strip Claude-format `type` field from codex MCP `-c` flags (root cause for #1812 codex-tools 0 MCP calls)
- Add positive runtime gate: fail-loud when `*-tools` writer produces 0 `mcp__sources__*` calls
- Flip 2 existing tests + add 4 new tests

## Test plan
- [ ] `ruff check` clean
- [ ] `pytest tests/test_agent_runtime_tool_config.py tests/test_v7_writer_dispatch.py -v` passes
- [ ] Smoke: `codex exec -c 'mcp_servers.sources.url=...' "call mcp__sources__verify_words for 'кіт'"` returns real result (not "tools not exposed")
- [ ] **Human follow-up: re-fire 3-way bakeoff** (`v7_build.py a1 my-morning --writer codex-tools`) — expect `tool_calls_total > 0` for codex-tools post-merge

Closes #1812.
Refs: `audit/codex-tools-review-2026-05-08/REPORT.md`, #1810, #1798.
PRBODY
)"
```

**DO NOT auto-merge.** The orchestrator (Claude) handles merge after adversarial review.

---

## Cleanup (after PR merges to main, by orchestrator)

```bash
git worktree remove .worktrees/codex-1812-mcp-type-strip
git branch -d codex-1812-mcp-type-strip
```

---

## Out of scope — DO NOT touch

- gemini-tools fix (separate work, gated on this fix landing first)
- `.gemini/settings.json` deploy regression (#1811)
- `.codex/hooks/*` deploy direction (#1811)
- The wider `mcp_config_resolved` pre-flight refactor (separate observability cleanup)
- Anything in `claude_extensions/` or `gemini_extensions/` source-of-truth updates

If you find yourself touching anything in this list, STOP and ask. Stay tight.
