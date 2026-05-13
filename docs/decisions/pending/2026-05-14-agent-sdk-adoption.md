# DECISION REQUIRED — Claude Agent SDK adoption for V7 pipeline (parallel-shim with CLI subprocess)

**Status:** PROPOSED — pending architecture review.
**Surfaced:** 2026-05-13, user direction "we will have to plan this claude sdk route" after Anthropic announced the agentic credit pool launch effective 2026-06-15.
**Source:**
- Anthropic announcement: $200/mo agentic credit pool from 2026-06-15 (refreshes monthly), separate from Claude Code interactive limits, covers Claude Agent SDK + `claude -p` + Claude Code GitHub Actions + 3rd-party SDK apps.
- User stated 2026-05-13: "always" hits Max 20× interactive weekly cap → no slack to absorb dispatched work onto interactive bucket; every capacity lever matters.
- This conversation transcript (2026-05-13 14:00-22:30 UTC): routing, pool economics, SDK adoption discussion. Reference: same-session orchestrator handoff at `docs/session-state/2026-05-13-m20-build-iteration-4-contract-shipped-brief.md`.
**Scope:**
- **IN:** `scripts/agent_runtime/` (add `claude_sdk.py` adapter alongside `claude_cli.py`); `scripts/build/v7_build.py` writer phase wiring; per-runtime config in `scripts/config/agent_runtime.yaml` or env flag; telemetry shim for SDK response objects.
- **OUT (this PR family):** Reviewer phase migration (later wave), MDX assembler (deterministic, no LLM call), `delegate.py` CLI dispatch surface (preserve back-compat — multi-process dispatches still need subprocess).
- **OUT (entirely):** Replacing the CLI subprocess path. Both must coexist — SDK for in-process agentic loops, CLI for parallel fire-and-forget dispatches.

---

## TL;DR

The Claude Agent SDK is the official Python framework for in-process Claude invocation with native tool use, multi-turn agentic loops, MCP integration, hooks, and sub-agents. From 2026-06-15 it draws from the new $200/mo agentic credit pool (same bucket as `claude -p`). For the V7 pipeline this means four wins:

1. **Native token telemetry** — SDK response objects carry input/output token counts directly; no fragile terminal-output parsing in `agent_runtime/result.py:tokens`.
2. **In-process agentic loops** — writer phase becomes a real loop (`draft → vesum-check → revise → exit when gate passes`) instead of single-shot subprocess. Quality gates move upstream, fewer post-hoc reviewer cycles.
3. **Tool-call hooks** — SDK exposes middleware at tool boundaries. We can enforce VESUM-verification on every word-emitting tool call inside the writer loop, mid-generation.
4. **Context efficiency** — single agent session across writer + reviewer phases reuses the loaded project context. Estimated 2-3× cheaper per "agentic operation" vs current pattern that cold-starts each `claude -p` subprocess.

Trade: 1-2 week refactor of `agent_runtime/` + V7 writer-phase wiring. Parallel-shim approach (SDK and CLI both supported, env flag selects path, default starts at CLI and ratchets to SDK after A/B verification).

**Critical timing constraint:** SDK calls only become budget-viable from 2026-06-15 when the agentic credit pool launches. Implementation can land BEFORE June 15; ACTIVE use defaults to CLI until then. Pre-June 15 dev should run on Anthropic API key with paid metered usage (small dev cost) for A/B verification.

---

## Why this matters now (one paragraph)

The current V7 writer phase is "one `claude -p` invocation, fixed prompt, single-shot output, gate checks post-hoc." Build iteration 4 of m20 showed the structural cost: the writer correctly followed every directive in its prompt but the gate counter didn't recognize the writer's natural shape (`uk=` prop instead of `text=`). The writer had no way to know mid-generation. We've now shipped 4 PRs in 2 days (#1957, #1961, #1963, #1964, #1966) that are all variations of "writer correctness vs gate over-extraction" — each one a class of bug that costs ~1-3 build cycles to diagnose. An SDK-native writer LOOP could catch each class on the first generation pass: emit `<DialogueBox uk="..." />`, hook fires `_count_uk_dialogue_lines` against current output, sees it counted correctly OR sees zero and prompts the model to switch shape. One generation, multiple gate-aware self-corrections, no post-hoc reviewer cycle. This is the structural payoff, not just the cost-economics one.

---

## What's being proposed (4 axes, sequenced)

### Axis 1 — Adapter layer (`scripts/agent_runtime/claude_sdk.py`)

**New adapter alongside `claude_cli.py`** implementing the same Protocol shape:
- `invoke(prompt, model, effort, tools, mode) -> Result`
- Returns the same `Result` dataclass (preserves `Result.usage_record` schema)
- Token usage extracted directly from SDK response objects — populates `Result.tokens` deterministically (no longer opportunistic)
- Tool calls captured via SDK callback (no terminal output regex parsing)
- Session ID extraction native to SDK
- Rate-limit detection via typed exception (not stderr pattern matching)

Registry entry in `scripts/agent_runtime/registry.py`: `claude-sdk` agent with same cost_tier as `claude` but `entrypoint: sdk` so callers can request the SDK path explicitly while CLI users see no change.

**Estimate:** ~300-450 LOC + parallel test file (~150-200 LOC of tests).

### Axis 2 — Writer phase migration (V7 build)

**`scripts/build/v7_build.py`** reads env flag `CLAUDE_RUNTIME=sdk|cli` (default `cli` initially):
- When `cli`: invoke `agent_runtime` via existing claude_cli.py path. No change.
- When `sdk`: invoke `agent_runtime` via new claude_sdk.py path. Same input prompt template, same expected output artifact shape (`module.md`, `vocabulary.yaml`, etc.).

After ≥3 modules built via SDK path with all gates GREEN, flip default to `sdk`, keep `cli` as opt-in via env override.

**Estimate:** ~100-200 LOC wiring + ~80-120 LOC tests (parallel-path coverage).

### Axis 3 — Mid-stream gate hooks (post-June 15, after Axes 1+2 stable)

**New module: `scripts/build/sdk_hooks.py`** registers callbacks on the SDK agent's tool-call middleware:
- On every `vesum_verify` tool call result, capture verified/missing forms.
- On writer's draft completion (before output is returned), run `_count_uk_dialogue_lines` against the current text. If below threshold, push a feedback message into the loop: "Your output has N dialogue lines; the gate requires M. Re-draft with M+ dialogues using `<DialogueBox uk="..." en="..." />` shape."
- Similar hooks for `component_density`, `l2_exposure_floor`, citation count.

This is the structural quality win — not just cost efficiency. **Net-new architecture**; the CLI path can't easily do this because subprocess output is monolithic, not streamable for intervention.

**Estimate:** ~200-400 LOC + ~150 LOC tests. Hook design needs care: too aggressive and the writer thrashes; too lenient and gates still fail post-hoc.

### Axis 4 — Pool-aware routing (depends on routing-budget endpoint)

Once `/api/state/routing-budget` ships (current dispatch `routing-budget-observability-2026-05-13`), extend its `recommendation` logic:
- `recommendation.runtime_for_writer` field: `"sdk"` when in-process agentic loop fits OR `"cli"` when parallelism needed OR `"inline_orchestrator"` when both pools tight.
- v7_build.py reads this field at start of each build and self-selects the runtime accordingly.

**Estimate:** ~50 LOC delta to the routing endpoint + ~30 LOC selector logic in v7_build.py.

---

## Implementation timeline (33 days of runway pre-June-15)

| Window | Axis | Deliverable | Activation status |
|---|---|---|---|
| 2026-05-14 → 2026-05-28 (~2 weeks) | 1 | `claude_sdk.py` adapter + tests | Implemented, OPT-IN via env flag, dev-tested on Anthropic API key with paid metered usage |
| 2026-05-29 → 2026-06-10 (~2 weeks) | 2 | v7_build.py writer-phase wiring + A/B test on 3 modules | `cli` remains default; SDK opt-in only |
| 2026-06-11 → 2026-06-15 (5 days buffer) | — | A/B comparison report; correctness verification | Hold for pool launch |
| 2026-06-15 (POOL LAUNCH) | — | Flip default to `sdk` if A/B clean | Active use begins drawing from agentic pool |
| 2026-06-16 → 2026-06-30 (~2 weeks) | 3 | Mid-stream gate hooks | SDK path takes hooks; CLI path unchanged |
| 2026-06-30+ | 4 | Pool-aware routing wired into v7_build.py | Both runtimes live; router selects |

**Land Axes 1-2 BEFORE 2026-06-15** so the moment the pool funds, we flip a single env flag and start drawing.

---

## Validation path

1. **A/B parallel:** build the same 3 modules (e.g., a1/my-morning, a1/at-school, a1/family-life — already-built modules with stable plans) via both CLI and SDK paths. Diff outputs structurally:
   - Same word counts (±5% tolerance — model nondeterminism)
   - Same component counts (DialogueBox, VocabCard, etc.)
   - Same gate verdicts (all GREEN or all FAIL on same gates)
   - SDK output passes `tests/build/test_v7_build_e2e.py` end-to-end equivalents
2. **Cost A/B:** SDK adapter records cost per phase via SDK's native token telemetry; CLI records cost via existing terminal-parsing. Compare per-module total cost. **SDK should be cheaper per module by 30-60%** if context efficiency claim holds (cold-start tax eliminated). If equal-or-more-expensive, the efficiency premise is broken and we reconsider.
3. **Quality A/B:** review at least 3 SDK-built modules via content-review skill; require gate-greenness AND no quality regression vs CLI-built control.

Promote SDK to default only when ALL of: (a) 3 modules A/B-pass, (b) cost-per-module strictly lower on SDK, (c) no test suite regressions in `tests/build/` or `tests/agent_runtime/`.

---

## Hold criteria (when to abandon / revert)

- **Correctness regression:** SDK adapter produces structurally different output than CLI on identical input → writer prompt may be sensitive to invocation context; investigate before defaulting.
- **Cost regression:** SDK cost-per-module ≥ CLI cost-per-module on A/B → context-efficiency claim is wrong; revisit premise (maybe SDK overhead offsets gains).
- **Tool-call telemetry unreliable:** SDK response objects miss tool calls or report wrong arguments → telemetry pipeline broken; cannot evaluate gates.
- **MCP integration regression:** `mcp__sources__*` tools behave differently via SDK than CLI → MCP wiring needs rework before SDK adoption.
- **Version churn:** SDK library has breaking API changes between point releases → pin version, monitor, defer if churn is high.
- **Subprocess parallelism loss:** can't keep `delegate.py --agent claude` running multiple parallel dispatches → BLOCKING; CLI path stays alongside permanently (already in plan, but verify).

---

## Risks

1. **SDK version drift.** The Agent SDK is GA but evolving — pin version in `requirements.txt`, document upgrade procedure, watch Anthropic changelog.
2. **MCP behavior delta.** CLI uses stdio MCP; SDK may use a different transport. Test `mcp__sources__verify_word`, `search_text`, `query_pravopys`, `search_heritage` thoroughly — these are the writer's hot path.
3. **Session resume / warm-cache.** Does the SDK support session resume (CLI's `--resume <id>`)? Important for cost: warm-cache hits are ~10× cheaper than cold-starts. Verify before committing.
4. **Effort/model parameters.** Does SDK respect `effort=xhigh` and our model override system? Verify mapping.
5. **Long-running agent loops.** SDK loop that runs for 20+ tool calls may hit per-request token limits. Need fallback or pagination strategy.
6. **Concurrency model.** CLI subprocess gives us parallelism for free (multiple processes); SDK is in-process. Don't accidentally serialize work that was parallel.

---

## Open questions (resolve before Axis 1 dispatch)

1. **SDK version to pin?** Latest stable on PyPI as of 2026-05-13. Check `pip show anthropic-agent` (or whatever the SDK package is named — verify exact package name and current version).
2. **Auth flow.** Does SDK auth via the same Claude Code login token (post-June 15 → agentic pool), or does it require a separate ANTHROPIC_API_KEY? Anthropic's announcement suggested "no separate API key needed" but verify.
3. **Pre-June-15 dev cost.** SDK calls before pool launch will use API metered billing. Budget: ~$50-100 across the 2 weeks of dev/A-B testing. Acceptable.
4. **Hook persistence.** Can SDK hooks survive across multiple tool calls within one agent run, or do they reset? Affects hook design in Axis 3.
5. **Coexistence with `delegate.py`.** When user fires `delegate.py --agent claude`, do we route via SDK or CLI? Recommendation: CLI for fire-and-forget dispatches (parallelism, isolation), SDK for in-process pipeline-internal use. Codify this rule explicitly.

---

## Companion routing-budget integration

The routing-budget brief currently in flight (`routing-budget-observability-2026-05-13`) does NOT need to know about SDK vs CLI today — it tracks bucket-level spend. Once SDK lands:
- Add `runtime: "sdk" | "cli"` field to `usage_record` (passes through cost telemetry).
- Routing-budget endpoint groups spend by `(agent, runtime)` pair.
- Recommendation logic gains `runtime_for_writer` per Axis 4.

No coordination dependency — SDK adoption can ship independent of routing-budget; they integrate at Axis 4 if/when both are ready.

---

## What this Decision Card does NOT promise

- It does NOT propose retiring `delegate.py --agent claude` or the CLI subprocess path. Both stay. Forever (or until Anthropic deprecates the CLI).
- It does NOT solve the "$200/mo agentic pool isn't enough" problem on its own. The efficiency win helps stretch the pool; doesn't make it infinite. Routing discipline, lower default model/effort, and potentially metered overage remain part of the toolkit.
- It does NOT introduce a new build pipeline. V7 stays. Only the writer phase's invocation surface changes.
- It does NOT require user action before 2026-06-15 beyond "review and APPROVE this Decision Card." Implementation can proceed under PROPOSED status if you flag green to start.

---

## Recommendation

**APPROVE** as PROPOSED with this sequencing:
1. Verify the 5 open questions (above) — 30-60 min of API docs reading; can be inline by orchestrator.
2. After open questions resolved: dispatch **Axis 1 (adapter) to Claude headless** (`delegate.py --agent claude --model claude-opus-4-7 --effort xhigh --mode danger --worktree`). Rationale: Axis 1 integrates **Anthropic's own SDK** — Claude has firsthand knowledge of its SDK's API, hook semantics, MCP transport, and edge cases; Codex would re-derive these from external docs and get edge cases subtly wrong. This is exactly the per-task-model-assignment fit Codex would lose on.
3. After Axis 1 lands: dispatch Axis 2 (writer-phase wiring) to Codex high-effort. Axis 2 is mechanical glue between the adapter and v7_build.py — Codex fits.
4. Axis 3 (mid-stream gate hooks) — Claude headless. Novel architectural work involving SDK hook semantics; Claude's SDK familiarity matters again.
5. Axis 4 (pool-aware routing) — Codex. Mechanical extension of the routing-budget endpoint.
6. After Axis 1+2 land + A/B clean: ratchet default to SDK at 2026-06-15.
7. Axes 3-4 land in June, post-pool-launch.

**Per-axis agent routing summary:**

| Axis | Task class | Agent | Rationale |
|---|---|---|---|
| 1 | New Anthropic SDK adapter | **Claude headless** (opus xhigh) | Anthropic SDK firsthand knowledge |
| 2 | v7_build.py wiring | Codex high | Mechanical glue |
| 3 | SDK hook architecture | **Claude headless** (opus xhigh) | Novel hook design + SDK semantics |
| 4 | Routing endpoint extension | Codex high | Mechanical extension |

Move to ACCEPTED state at the moment Axis 1 lands and A/B-passes a single module build.

---

*Format spec follows existing pending Decision Cards (e.g., `2026-05-13-a1-m15-24-shape-contract.md`). Will move to `docs/decisions/2026-05-XX-agent-sdk-adoption.md` on acceptance, with implementation timeline locked.*

*Companion: dispatch-brief for Axis 1 adapter to follow — will reference this card by path. Companion: routing-budget brief `2026-05-13-routing-budget-observability.md` (currently in dispatch) — provides the cost-feedback loop SDK adoption depends on for A/B validation.*
