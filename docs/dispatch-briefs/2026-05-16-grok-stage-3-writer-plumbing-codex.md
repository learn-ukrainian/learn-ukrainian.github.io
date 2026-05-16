# Dispatch brief — Grok Stage 3: `--writer grok-tools` plumbing for V7 build

> **Owner:** Codex
> **Filed:** 2026-05-16
> **Scope:** Add `grok-tools` as a third writer family in V7 alongside
> `claude-tools` and `gemini-tools`/`codex-tools`. Closes the only
> remaining Grok 4.3 onboarding stage (Stage 3 per the 2026-05-16
> handoff). Per the calibration data, Grok-as-writer is ~75× cheaper
> than claude-opus on input — if this passes the same gates as
> claude-tools, it shifts the V7 cost equation dramatically.

---

## Why this matters

The 2026-05-16 Grok onboarding study completed Stages 1, 2, 4, 5 (judge
calibration, code-gen, fixes reviewer, hallucination probe) but **Stage
3 (V7 module writer trial) was deferred** because it required ~1-2 hr
of `linear_pipeline.py` plumbing to wire `grok-tools` analogous to the
existing `claude-tools` writer.

Now that PR #2025 shipped the OpenAI-compat HTTP proxy at `:8767`, **part
of the plumbing is moot** — Hermes is reachable as a backend. But the
V7 writer specifically needs:
- Per-call MCP tool access (verify_words, search_text, etc.) — Grok does this natively via Hermes's MCP-sources registration
- Tool-call telemetry capture (which gates fire `phase_writer_summary` events with `tool_calls_total`, `verify_words_calls`, etc.)
- The standard writer-loop contract (correction rounds, end_gate, fix-block parsing)

The existing `agent_runtime/adapters/{claude,codex,gemini}.py` pattern
is the right extension point. A new `hermes_grok.py` adapter that
shells out to `hermes -z PROMPT -m grok-4.3` (with MCP sources enabled
in `~/.hermes/config.yaml`) and parses Hermes's stdout for tool-call
events.

## Pre-flight: read these first

Before writing any code, read in this order so the contract is clear:

1. `docs/agent-runtime-guide.md` — universal adapter layer architecture (READ BEFORE touching `scripts/agent_runtime/`).
2. `scripts/agent_runtime/adapters/_template.py` — adapter skeleton.
3. `scripts/agent_runtime/adapters/claude.py` — the model adapter (V7 default writer); look at how it captures stream-json events and surfaces `tool_calls`.
4. `scripts/agent_runtime/adapters/gemini.py` — second reference (different CLI shape).
5. `scripts/build/linear_pipeline.py` lines 2487-2567 (`invoke_writer`) and 2400-2486 (`_runtime_tool_config`) — how the pipeline plugs adapters into the writer loop.
6. `scripts/build/v7_build.py` lines 27-31, 425-447, 570-580, 715-720 — the writer-name routing surface.
7. `audit/2026-05-15-grok-4.3-judge-calibration/CONSOLIDATED-REPORT.md` — Grok onboarding findings; **note: medium reasoning is BEST for code-gen on Grok**, NOT high or xhigh. Use `effort: medium` in defaults.
8. `~/.hermes/config.yaml` — verify Sources MCP is registered (line ~212 per the handoff). Don't mutate.

## Concrete scope

### Files to add

- `scripts/agent_runtime/adapters/hermes_grok.py` — new adapter (~150-250 LOC).

### Files to modify

- `scripts/agent_runtime/adapters/__init__.py` — register the adapter.
- `scripts/agent_runtime/runner.py` — route `agent_name="grok"` to the new adapter.
- `scripts/build/linear_pipeline.py`:
  - Line 61: extend `WRITER_CHOICES = ("claude-tools", "gemini-tools", "codex-tools", "grok-tools")`.
  - Line 62-65: add `"grok-tools": {"model": "grok-4.3", "effort": "medium"}` to `WRITER_DEFAULTS`. **Use `medium`, NOT `high` or `xhigh`** per Grok onboarding finding (high underperforms medium on code-gen).
  - Line 67: extend `REVIEWER_CHOICES` similarly.
  - Line 68-71: add `"grok-tools": {"model": "grok-4.3", "effort": "medium"}` to `REVIEWER_DEFAULTS`.
  - Line 2439-2440: extend the agent-label switch if `claude-tools` has a special branch — add a parallel `grok-tools` branch if grok needs MCP-server validation.
- `scripts/build/v7_build.py`:
  - Line 27-31: `WRITER_ALIASES["grok"] = "grok-tools"`.
  - Line 427-429: extend the writer-vs-reviewer pairing logic so grok-tools writer doesn't review itself (per the SELF_REVIEW_DETECTED gate).
  - Line 570-580: extend the `--writer` choices help string to include `grok-tools`.
  - Line 715-720: handle `grok-tools` writer cwd (probably same as claude-tools — module_dir, not PROJECT_ROOT).

### Files for tests

- `tests/agent_runtime/adapters/test_hermes_grok_adapter.py` — new file (~150 LOC, 4-6 tests).
- `tests/build/test_linear_pipeline_writer_routing.py` — if a similar file exists, extend; otherwise add an integration test that mocks the adapter and asserts `invoke_writer("...", "grok-tools")` reaches the new adapter with the right model/effort.

## Adapter implementation contract

`hermes_grok.py` must satisfy the same `Adapter` protocol that
`claude.py` does (read `_template.py` and `claude.py` for the exact
type contract — likely a `Result` with `response`, `tool_calls`,
`usage`, etc.).

Key implementation choices:

1. **Subprocess invocation:** `subprocess.run(["hermes", "-z", prompt, "-m", "grok-4.3"], capture_output=True, text=True, timeout=...)`. Pass prompt via argv (Hermes accepts long argv per its current usage; if prompt > ARG_MAX surfaces, switch to stdin in a follow-up — file as issue, not block).
2. **MCP tool calls:** Hermes auto-resolves MCP tool calls inside its own session loop; the adapter sees only the FINAL response on stdout. **There is NO stream-json equivalent for Hermes** — tool calls are opaque to the adapter. This is a known telemetry gap; document in the adapter docstring and surface as `tool_calls_total=None` (NOT 0 — null means "not surfaced", 0 means "verified zero").
3. **Effort flag:** Hermes reads `~/.hermes/config.yaml`'s `agent.reasoning_effort`. Per-call mutation of that file is RACE-PRONE in concurrent calls (the proxy review #2027 already flagged the parallel pattern); v1 grok-tools reads whatever the user has configured. Document in adapter that the effort flag is honored only if it matches the running config; otherwise, log a WARNING.
4. **Response parsing:** Hermes's stdout in `-z` mode is the assistant's final message. Strip ANSI codes if any, return as `response`.
5. **Error handling:** If `hermes` is not on PATH, return a structured error (don't crash). If timeout fires, raise the standard adapter timeout error.

## Required tests (`tests/agent_runtime/adapters/test_hermes_grok_adapter.py`)

1. `test_grok_adapter_invokes_hermes_z_with_correct_argv` — mock `subprocess.run`; assert called with `["hermes", "-z", <prompt>, "-m", "grok-4.3"]`.
2. `test_grok_adapter_returns_stdout_as_response` — mock subprocess to return `stdout="hello from grok"`; assert `result.response == "hello from grok"`.
3. `test_grok_adapter_tool_calls_total_is_none_not_zero` — mock subprocess; assert `result.tool_calls_total is None` (telemetry gap, not "verified zero").
4. `test_grok_adapter_handles_missing_hermes_binary` — mock subprocess to raise `FileNotFoundError`; assert returns structured error (per the adapter base contract).
5. `test_grok_adapter_honors_timeout` — mock subprocess to raise `TimeoutExpired`; assert the standard adapter timeout error path.
6. `test_grok_adapter_strips_ansi_codes_from_stdout` — mock stdout with `"\x1b[32mhello\x1b[0m"`; assert response is `"hello"`.

## #M-4 deterministic-evidence preamble

| Claim | Evidence in PR body |
|---|---|
| "grok-tools registered in WRITER_CHOICES" | `grep -n grok-tools scripts/build/linear_pipeline.py` raw output |
| "Adapter file exists with right protocol" | `python -c "from scripts.agent_runtime.adapters.hermes_grok import HermesGrokAdapter; print(HermesGrokAdapter)"` raw output |
| "All 6 adapter tests pass" | `pytest tests/agent_runtime/adapters/test_hermes_grok_adapter.py -v` raw final summary |
| "No regression in adapter test suite" | `pytest tests/agent_runtime/ -v` raw final summary |
| "Wider sweep clean" | `pytest tests/ -x -q --ignore=tests/test_pipeline_runtime.py` raw final summary (note that `tests/test_esum_search.py::test_search_esum_berkut_returns_turkic_origin` is a known pre-existing failure per #2001 — exclude or document) |
| "Ruff clean" | `.venv/bin/ruff check scripts/agent_runtime/adapters/hermes_grok.py tests/agent_runtime/adapters/test_hermes_grok_adapter.py scripts/build/linear_pipeline.py scripts/build/v7_build.py` raw |
| "Help string includes grok-tools" | `python scripts/build/v7_build.py --help 2>&1 \| grep grok` raw |
| "PR opened" | `gh pr view --json url -q '.url'` raw URL |

## Out of scope (file as follow-ups, do NOT include)

- Running an actual V7 build with `--writer grok-tools` — that's the
  orchestrator's Phase F (after this PR merges). The PR only ships the
  plumbing; validation happens in a separate build run.
- Changing the proxy's `_hermes_backend` (separate concern; see issue
  #2027 for the proxy ARG_MAX work).
- Hermes config mutation per call (see calibration script
  `scripts/audit/grok_stage_runner.py` for the atomic backup-swap-restore
  pattern; that's race-prone for V7 builds, don't replicate).
- Stream-json telemetry parity (Hermes doesn't expose it; gap is documented).
- Changing `claude-tools` defaults (out of scope; this is purely additive).

## Numbered steps (MANDATORY)

### 1. Worktree
The dispatch wrapper has created your worktree at
`.worktrees/dispatch/codex/grok-stage-3-writer-plumbing-2026-05-16/`
from the post-#2031-merge tip. Verify:
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/grok-stage-3-writer-plumbing-2026-05-16
git log -1 --oneline
```

### 2. Read pre-flight (per "Pre-flight" section above)

### 3. Implement adapter, register, modify linear_pipeline.py + v7_build.py

### 4. Tests (6 unit tests minimum)

### 5. Lint + pytest sweeps (per #M-4 evidence table)

### 6. Commit

```bash
git add -A
git commit -m "$(cat <<'EOF'
feat(v7): add grok-tools writer family via hermes adapter

Closes Grok 4.3 onboarding Stage 3 (the only remaining stage from the
2026-05-16 onboarding study).

Adds:
- scripts/agent_runtime/adapters/hermes_grok.py — new adapter wrapping
  `hermes -z PROMPT -m grok-4.3` for V7's writer + reviewer surfaces.
- WRITER_CHOICES + WRITER_DEFAULTS + REVIEWER_CHOICES + REVIEWER_DEFAULTS
  extended in linear_pipeline.py with "grok-tools": {model: "grok-4.3",
  effort: "medium"}. Medium NOT high — per onboarding finding,
  reasoning_effort=high underperforms medium on code-gen.
- v7_build.py WRITER_ALIASES["grok"] = "grok-tools" + writer-pairing logic
  + --writer help string + writer cwd handling.
- 6 unit tests for the adapter.

Telemetry gap (documented in adapter docstring): Hermes -z mode does not
expose stream-json tool-call events the way Claude/Codex/Gemini do.
Adapter surfaces tool_calls_total=None (NOT 0) to signal "telemetry
unavailable" vs "verified zero". Stage 3 V7 build evaluation (Phase F)
will pivot on whether this telemetry gap matters in practice.

Per-call config mutation of ~/.hermes/config.yaml is race-prone for
concurrent V7 builds; v1 reads whatever the user has configured (medium
per the 2026-05-16 onboarding default). reasoning_effort mismatch
between WRITER_DEFAULTS and the running config logs a WARNING but does
not error — pragmatic v1 trade-off.

Co-Authored-By: Codex (gpt-5.5)
EOF
)"
```

### 7. Push + open PR (DO NOT auto-merge)

```bash
git push -u origin codex/grok-stage-3-writer-plumbing-2026-05-16
gh pr create --base main --title "feat(v7): add grok-tools writer family via hermes adapter" --body "..."
```

(PR body should mirror the commit message + the #M-4 evidence table.)

## Acceptance criteria

- [ ] `--writer grok-tools` accepted by v7_build.py CLI (verify with `v7_build.py --help | grep grok`)
- [ ] `invoke_writer(prompt, "grok-tools")` reaches the new adapter (asserted by integration test)
- [ ] All 6 adapter tests pass
- [ ] Wider pytest sweep clean (modulo the known #2001 ESUM failure)
- [ ] Ruff clean
- [ ] Adapter docstring documents the stream-json telemetry gap explicitly
- [ ] WRITER_DEFAULTS uses `effort: "medium"`, NOT high or xhigh

## Failure modes to avoid

- **Don't mutate `~/.hermes/config.yaml`** in the adapter. Read it, log a warning if `reasoning_effort` mismatches the requested effort, but never write.
- **Don't fabricate tool_calls_total=0** when the adapter can't see them. Use `None`.
- **Don't add to claude-tools/gemini-tools/codex-tools defaults** in this PR. Pure addition only.
- **Don't run V7 builds in this PR.** That's the orchestrator's Phase F validation work after merge.
- **Don't add streaming/SSE.** Out of scope; the proxy's deferred Phase 2 work covers that.

---

*Brief format: MD per #M-2 (ai → ai). Authority: MEMORY DISPATCH-BRIEF
CHECKLIST + #M-4 deterministic-evidence preamble + 2026-05-16 Grok
onboarding study (`audit/2026-05-15-grok-4.3-judge-calibration/`).*
