# Codex tool-call capture — recurring measurement artifacts

**Category:** codex-tool-capture · **Severity:** build-breaking (HARD-fail) / QG silent-zero · **Recurrences:** 5

## Symptom
(Identical each time.) A codex-tools V7 build HARD-fails the writer phase with
`WRITER_RUNTIME_GATE_FAILED: failures=[mcp_tools_never_invoked]`
(`phase_writer_summary` shows `tool_calls_total=0`) **even though the codex
writer actually made many valid `mcp__sources__*` calls** — provable from the
raw rollout JSONL. The build dies before reaching content gates. The failure is
a **measurement artifact**, not a writer-behavior failure.

## Root cause
The codex CLI's tool-call recording format is **unstable across versions**, and
our capture/normalization layer (`scripts/agent_runtime/tool_calls.py` +
`scripts/agent_runtime/adapters/codex.py`) is tightly coupled to a specific
format. Each codex CLI bump risks silently breaking capture → 0 valid calls
captured → the `tools_writer_runtime_gate` reads "0 calls" as "writer used no
tools" and HARD-fails. **The gate conflates a measurement failure (we couldn't
see the calls) with a behavior failure (the writer made none).**

## The recurrences
1. **#1907 (2026-05-13) — rollout matcher.** `_rollout_matches_plan` rejected
   fresh rollouts (encoding/whitespace mismatch on the stdin-payload byte
   compare) → adapter discarded the rollout → 0 calls. Earlier triggered the
   2026-05-12 "codex `tool_calls_total=0`" verdict that wrongly demoted codex as
   writer (later retracted).
2. **#2403 (2026-05-29) — timezone dir-scan.** `_candidate_rollout_dirs`
   scanned UTC-date dirs; codex (22:xxZ = 00:xx Budapest) wrote the rollout under
   the **local-date** dir `2026/05/29`. Adapter read the wrong day → 0 calls.
   Fixed by scanning UTC±1 + local±1 under the scoped home.
3. **(this, 2026-05-29) — codex 0.135.0 namespace format.** 0.132.0 emitted
   `function_call` payloads with `namespace="mcp__sources__"` (trailing `__`);
   `_tool_name` did `f"{namespace}{name}"`. **0.135.0 dropped the trailing
   `__`** → `namespace="mcp__sources"` → join produced
   `mcp__sourcesget_chunk_context` (no separator), failing the `mcp__sources__*`
   family check. Rollout-2026-05-29T09-59-48 had 15 real sources calls
   (verify_words×8, get_chunk_context×2, check_russian_shadow×2,
   search_style_guide×2, search_images×1) — all misclassified as 0.
   Fix: normalize the join to exactly one `__`.
4. **(this, 2026-07-08) — codex dual-id mismatch.** Codex MCP tool payloads carry both `id` (`fc_...`) and `call_id` (`call_...`), but the companion result event (`mcp_tool_call_end`) only carries `call_id`. `_tool_call_id()` registered the call under `id` because it was first in order, causing the result lookup on `call_id` to miss. Resolved by implementing id-set registration under all available correlation IDs.
5. **(this, 2026-07-08) — QG grounding canonicalizer (dot vs underscore).** After codex adapter output-capture fix (#4791) made tool *outputs* visible (12/12 etc), the *reviewer* grounding gate in `llm_reviewer_dispatch._canonical_tool_name` still zeroed all confirms for codex/gpt-5.5 runs. GPT cites `mcp__sources.query_wikipedia` (dot); captured events use `mcp__sources__query_wikipedia` (double-underscore). The prefix strip only handled `sources__`/`sources_` and `mcp__` — dot form became `sources.query_wikipedia` which never matched `query_wikipedia` → `_grounding_matching_events` skipped every event (koliadky 0/14 → 14/14 post-fix). Same family as prior capture format drifts: measurement artifact silently discards legitimate grounding. Fix makes canonicalizer transport-agnostic for `.` / `__` / `_` after mcp strip.

## Prevention
1. **Distinguish measurement-failure from behavior-failure in the gate.** Before
   HARD-failing `mcp_tools_never_invoked`, check whether ANY recorded call's
   bare/normalized name matches a known `sources` tool (verify_words,
   get_chunk_context, …). If yes → the writer DID use the corpus; emit a
   `writer_capture_format_drift` **WARN** (surface raw names + codex CLI version)
   instead of a HARD-fail, so a format drift degrades gracefully + is
   diagnosable, rather than silently killing every build. (Follow-up issue.)
2. **Golden-fixture contract test** pinning the codex tool-call recording shapes
   per known CLI version (0.132.0 trailing-`__`, 0.135.0 bare). A future format
   change then fails a unit test in CI, not a build at 2am. (The 0.135.0
   regression test added with the fix is the first such fixture.)
3. **Re-validate capture on every codex CLI upgrade** against a stored rollout
   fixture before trusting build results.

## Lesson
When a deterministic gate reads "0" for a measured quantity, ask *"is this zero
real, or did the measurement break?"* before treating it as a behavior verdict —
especially for an external tool (codex CLI) whose output format we don't control.
This is the same conceptual failure as the secret-leakage recurrences (a parser
silently degrading when the upstream format changes), applied to telemetry.

## Links

- Issue: #2407 (prior recurrences #1907, #2403)
- Fix (namespace join): `00dd5f18de` — fix(codex-adapter): normalize namespace/name join for codex 0.135.0 (no trailing `__`) (#2407)
- Fix (dual-id mismatch): fix(agent-runtime): correlate codex MCP tool outputs by call_id (id-set registration)
- Fix (dot-form canonical): `fix(qg): canonicalize dot-form MCP tool names in grounding gate` — `_canonical_tool_name` now handles `server.tool` (dot) form from gpt/codex QG + `__`/`_` variants; regression test in `test_llm_reviewer_dispatch.py`.
