# Seminar smoke builds — agy / Gemini Flash 3.5

**Build date:** 2026-05-20 · **Reported:** 2026-05-21

> Companion artifact to `REPORT.html`. Same content, markdown for in-CLI reading.

## TL;DR

- **3 builds attempted, 0 reached green.** Each surfaced a distinct issue ahead of the writer phase, so the agy CLI was only actually exercised in build #3.
- **agy adapter wiring works end-to-end** (CLI invoked, 184K-char prompt accepted, 5.5K-char response captured, telemetry emitted, 111s wall time, returncode 0).
- **agy 1.0.0 has no MCP plugin enablement** — empirically confirmed: `tool_calls_total=0` with `tool_call_telemetry_available=true`, so `MCP_TOOLS_NEVER_INVOKED` HARD-FAIL fires by design. Until `agy plugin enable sources` ships from kubedojo upstream, agy cannot satisfy seminar gates (VESUM, literary-grounding, citations-resolve, all four russianism family gates).
- **Two latent seminar plan-schema bugs surfaced and fixed/filed** alongside the agy work: PR #2165 (`_contract_yaml` list-shape `vocabulary_hints`) merged; issue #2164 (`references[].title` missing across most HIST/BIO/LIT plans) filed.
- All 5 build worktrees + branches preserved on disk per MEMORY #M-10 — diagnostic forensics safe.

## Builds

### Build 1 — hist/trypillian-civilization — **FAIL: plan phase**

| | |
|---|---|
| Stamp / branch | `build/hist/trypillian-civilization-20260520-182509` |
| Started (UTC) | 2026-05-20 18:25:09 |
| Writer | `agy-tools` |
| Phase reached | plan (failed validation) |
| Reason | `LinearPipelineError: Every plan reference must include a title` |
| Worktree | `.worktrees/builds/hist-trypillian-civilization-20260520-182509/` — preserved per #M-10 |
| Auto-commit | `12bba16b2b build(hist/trypillian-civilization): artifacts (failed)` — empty marker (failure was upstream of any artifact write) |

The plan validator at `scripts/build/linear_pipeline.py:768` rejected because Trypillian's three references use `work:` / `note:` / `author:` fields but no `title:`. Inventoried plans/hist + plans/lit + plans/bio: **0 of all HIST plans, only 2 of all LIT plans (`natalka-poltavka`, `teliha-poetry`, `synthesis-2`), and only 1 BIO plan (`roman-ratushny`) pass validation today**. Filed as issue #2164 (P1 — blocks any seminar build regardless of writer).

No agy invocation occurred; the failure was at validate-plan, three phases before writer.

### Build 2 — lit/natalka-poltavka (initial attempt) — **FAIL: writer phase, TypeError**

| | |
|---|---|
| Stamp / branch | `build/lit/natalka-poltavka-20260520-182758` |
| Started (UTC) | 2026-05-20 18:27:58 |
| Writer | `agy-tools` |
| Phase reached | writer (TypeError in `render_writer_prompt` before any CLI invocation) |
| Reason | `'list' object has no attribute 'get'` at `linear_pipeline.py:5799` |
| Worktree | `.worktrees/builds/lit-natalka-poltavka-20260520-182758/` |
| Auto-commit | `161b11d7de build(lit/natalka-poltavka): artifacts (failed)` |
| Artifacts on disk | `implementation_map.json` (entry_count: 0) — written before the error fired |

`_contract_yaml` did `plan.get("vocabulary_hints", {}).get("required", [])`, assuming the dict shape used by CORE plans. The seminar convention (most LIT + BIO) uses a bare list of `{word, pos, definition}` dicts. Fixed via PR #2165 (merged as `e99fa0a0fd`) — extracted `_required_vocabulary_for_contract(plan)` helper mirroring the dispatch in `_vocabulary_lemmas` (line ~895), which already handled both shapes.

A second build under the same plan ran during inline reproduction (`build/lit/natalka-poltavka-20260520-182859`) — same TypeError, kept for forensics.

### Build 3 — lit/natalka-poltavka (post PR #2165) — **FAIL: writer runtime gate**

| | |
|---|---|
| Stamp / branch | `build/lit/natalka-poltavka-20260520-183940` |
| Started (UTC) | 2026-05-20 18:39:40 |
| Writer | `agy-tools` · model `gemini-3.5-flash-high` (TUI-selected, persisted) |
| Phase reached | writer (completed) |
| Verdict | `WRITER_RUNTIME_GATE_FAILED: failures=[mcp_tools_never_invoked]` |
| Worktree | `.worktrees/builds/lit-natalka-poltavka-20260520-183940/` |
| Auto-commit | `966fb1d5c3 build(lit/natalka-poltavka): artifacts (failed)` |

**This is the build that actually exercised the agy adapter.**

| Telemetry field | Value | Interpretation |
|---|---|---|
| `duration_s` | 111.47 | agy CLI ran end-to-end without timeout or stall |
| `input_chars` | 184,788 | Full writer prompt accepted (large prompt OK) |
| `output_chars` | 5,523 | ~700–1000 words emitted — content was generated |
| `returncode` | 0 | CLI considered the call successful |
| `rate_limited` | false | No quota signal |
| `stalled` | false | Stall watchdog did not fire |
| `sections_total` | 5 | Writer recognized the 5 plan sections |
| **`sections_with_cot`** | **0** | Zero chain-of-thought blocks filled — V7's `<cot>...</cot>` ignored |
| **`tool_calls_total`** | **0** | Zero MCP tool calls — agy has no MCP wiring |
| `verify_words_calls` | 0 | No VESUM verification — gate would fail downstream too |
| **`end_gate_fired`** | **false** | Writer did not emit the closing structured-output gate |
| `tool_theatre_violations` | [] | No fake-tool-use signals — honest absence, not pretense |
| `tool_call_telemetry_available` | true | Runtime observer was wired correctly; the zero is real |

**Why this fails the seminar gate suite categorically.** Without MCP, agy cannot call `mcp__sources__verify_words` (VESUM gate), `mcp__sources__search_literary` (literary grounding for LIT/OES/RUTH), `mcp__sources__search_style_guide` + `mcp__sources__check_russian_shadow` (the russianism/surzhyk/calques/paronym family of gates), or `mcp__sources__query_pravopys` (orthography). The `MCP_TOOLS_NEVER_INVOKED` HARD gate at `linear_pipeline.py:2484` catches this structurally — a tool-less writer cannot produce gate-passing content by construction.

## Cross-cutting findings

### agy is blocked, not bad

The adapter port (PR #2163, merged as `29043426a9`) is durable. Once agy upstream ships MCP plugin enablement (kubedojo Phase-2 follow-up), the adapter should pick it up via `~/.gemini/config/mcp_config.json` — agy's own CLI log surfaces that as its MCP discovery path:

```
E0520 21:11:14 discovery.go:335] Failed to load JSON config file
  /Users/krisztiankoos/.gemini/config/mcp_config.json:
  unexpected end of JSON input
```

The file exists but is 0 bytes. Writing the `sources` server config there is the obvious next experiment — but it's user-global, so the call is on the operator, not the orchestrator.

### agy/Flash-3.5 did not follow V7's structured output format

Distinct from the MCP problem: `sections_with_cot=0` and `end_gate_fired=false` together indicate Flash-3.5 ignored the 4-backtick-OUTER fence convention and the closing structured-output gate. Either the writer prompt is mis-shaped for Flash-3.5, or Flash-3.5 doesn't reliably track multi-part fenced output. Cannot be diagnosed further without MCP wiring.

### Seminar plan-schema drift is the silent blocker

The agy bakeoff surfaced an independent issue that blocks *any* writer choice:

- **Issue #2164 (open):** `references[].title` systematically missing across HIST/BIO/most LIT plans. 0 HIST plans, 1 BIO, 3 LIT pass `validate_plan`. Even gemini-tools will fail-fast at PLAN phase on most modules until a backfill ships.
- **PR #2165 (merged):** `vocabulary_hints` shape — seminar plans use a bare list, CORE plans use a dict-with-required-key. `_contract_yaml` only supported the dict shape.

## Recommendations

| # | Action | Why |
|---|---|---|
| **R1** | Backfill `references[].title` across all seminar plans (issue #2164) | Unblocks every seminar writer regardless of choice. Most refs have `work:` which is the title in disguise — mechanical sweep. |
| R2 | Operator decision on `~/.gemini/config/mcp_config.json` | Writing the `sources` server there would unblock agy MCP. User-global blast radius. |
| R3 | Honor the pre-deferral ADR recommendation: **gemini-tools as seminar writer default** | gemini-cli has working MCP wiring. Survives 2026-06-15 Claude sunset. Aligns with historical baseline. |
| R4 | Run one HIST/LIT seminar smoke under `--writer gemini-tools` after R1 lands | Empirical baseline the ADR has never had. |
| R5 | Re-test agy when upstream ships MCP plugin enablement | Adapter already in place. Re-test ≈ one smoke build. Likely path to Flash-3.5 as a CORE-C1/C2 STEM writer, not as a humanities-seminar writer. |

## Artifact map

| Artifact | Location |
|---|---|
| Build branches (all) | `git branch | grep build/` |
| Build worktrees (all) | `.worktrees/builds/{hist,lit}-*` |
| agy adapter (port) | PR #2163 · `scripts/agent_runtime/adapters/agy.py` |
| Plan-schema fix (vocabulary_hints) | PR #2165 · `scripts/build/linear_pipeline.py` |
| Plan-schema issue (refs.title) | Issue #2164 |
| Seminar-writer ADR | `docs/decisions/pending/2026-05-20-seminar-track-writer-assignment.md` |
| agy usage telemetry (build 3) | `.worktrees/builds/lit-natalka-poltavka-20260520-183940/batch_state/api_usage/usage_agy-dispatch_2026-05-20.jsonl` |
