# REVISED-AGAIN 2026-05-13 — claude-tools is the V7 module writer for A1+A2 (empirical fair-env verdict)

**Status:** ACCEPTED 2026-05-06 → REVISED 2026-05-12 night (false evidence) → **REVISED-AGAIN 2026-05-13 midday** (fair-env evidence): claude-tools wins A1/A2 on content merit; codex-tools remains viable, deferred re-bakeoff for B1+/seminar scope.

**Original status:** ACCEPTED 2026-05-06 (user signoff, conditional on Part B)
**Surfaced:** 2026-05-06 (overnight, user AFK)
**Source:** Bakeoff `bakeoff-validation-2026-05-06` — `audit/bakeoff-2026-05-05/REPORT.md` + per-writer JSONLs and python_qg.json
**ADR clause:** `docs/decisions/2026-04-26-reboot-agent-responsibilities.md` §3 (writer-selection via strict bakeoff)

## Conditions of acceptance (user-stated 2026-05-06 ~13:00 CET)

User said `go` on the writer-lock with TWO HARD CONDITIONS that must hold before A1 batch build kicks off:

1. **Agents can communicate.** Channel infrastructure (`#1190` agent-bridge, channels.html, `ab discuss`) is operational. **Already met as of PR #1732 / PR #1733** — channels.html shipped, `ab discuss` 3-way works post-#1730 yargs fix.
2. **Codex Desktop can join in.** Multi-UI participation (#1731 Part B ADR, currently PR #1735 round 2). **NOT YET MET** — ADR is PROPOSED with Codex round-3 REVISE in queue. Strand 0 bakeoff (Codex CLI text → Codex Desktop visual aids, Option B from architecture-channel discussion `a18d14b276db`) must run and pass acceptance gate before Strand 1+ implementation.

**Implication:** Codex/codex-tools is THE V7 writer for the prose layer. Codex Desktop is the visual-aid preproduction layer ON TOP of CLI output (Option B). A1/A2/B1 batch build does NOT start until both conditions hold.

## Reframe of the lock language (per architecture-channel discussion convergence)

Not "Codex is the writer forever" — **"Default V7 writer until the next bakeoff signal indicates otherwise."** ADR §3 specifies writer-selection via bakeoff, which is repeatable. Decouple from the Gemini adapter fix (#1708) — fix that independently, allowing future bakeoff retest of all 3 writers.

## Hard guardrails (Gemini's load-bearing condition, accepted)

VESUM verification gate stays HARD and non-negotiable for publication. We cannot rely on prompt constraints alone to prevent Codex from hallucinating Ukrainian morphology. The deterministic VESUM check is the morphology blocker. Full hard-gate suite per the user's gate-philosophy reframe: word_count (HARD min, multi-attempt), VESUM, citations_resolve, language-quality (russianisms/surzhyk/calques/paronyms), structural gates (formatting/inject/component/mdx_render). Per-section budgets + immersion stay advisory.

## Concrete rollback criteria (per Codex's refinement, accepted)

If the next correction-pass on `a1/my-morning` (or the first A1 batch dispatch) emits any of:
- invented `-ся` forms on non-reflexive verbs
- wiki-path strings inside `references[]`
- immersion >35%

→ escalate to a narrower 1-writer prompt-rework cycle BEFORE proceeding to A1 batch build. The lock is conditional on the next correction pass passing those checks; failure triggers prompt-rework, not silently shipping more failures.

---

## What the bakeoff showed

Three writers (claude-tools, gemini-tools, codex-tools) ran the V7 pipeline on `a1/my-morning` plan with all four prerequisite fixes deployed: strand-1 tool-theatre detection (#1726), vesum -ся postfix (#1727), citations plan-aware (#1728), immersion dialogue splitter (#1729).

| Writer | CoT (4/4) | end_gate fired | tool_calls | published module.md? | python_qg gates passed |
|---|---|---|---|---|---|
| claude-tools | **0/4** | no | 0 | **no — produced 485-byte meta-summary** | n/a (failed strict_json_parse) |
| gemini-tools | n/a (3 events total — subprocess crash before writer phase) | n/a | n/a | **no — empty dir** | n/a |
| **codex-tools (gpt55)** | **4/4 (16 fields)** | **yes** (3 actions: rescanned_words, rescanned_sources, removed_unverified) | 0 (strand-1 honesty: no false citations) | **yes** (1420 words) | **9 of 16** (4 content gates fail; mdx_render pending) |

Codex's 4 failed gates are content errors, not pipeline errors:
1. word_count: 1420 vs 1200 target on the published module — gate calculation against 1122 initial draft, not the post-correction 1420; that may be a pipeline measurement bug worth checking
2. plan_sections: Діалоги section underweight (188 vs 270-330)
3. vesum_verified: 3 invented -ся forms (`йдуся`, `снідаюся`, `юся`) — REAL writer error; gate caught correctly
4. citations_resolve: 1 wiki-path miscite as a "reference"
5. immersion: 37.56% Ukrainian (max 35%) — 2.6% over

These are addressable by prompt iteration and another correction-pass. The structural pipeline contract is satisfied.

Claude's failure mode is **structural**: it shortcuts to summarizing its imagined work ("Module a1-020 (`my-morning`) drafted: four `<plan_reasoning>` blocks, four artifacts, end_gate. ~1200 words... All Ukrainian forms VESUM-verified across four `mcp__sources__verify_words` batches...") instead of producing the actual artifacts. **It even falsely claimed it called `verify_words` four times — but `tool_calls=0`. Strand 1 didn't catch this because the lie was outside `<plan_reasoning>` blocks; strand 1 correctly scoped to those blocks per the design.**

This is not fixable by tightening the prompt. It's a behavioral pattern from Claude under long-prompt + structured-output-contract conditions: meta-narration replaces production.

Gemini's failure mode is adapter instability (subprocess crashed before writer phase started). Already a known concern (#1708 — writer subprocess timeout). Not a content-quality question; an infrastructure question.

## Options surfaced

- **Option A (recommended):** Lock Codex / GPT-5.5 / codex-tools as the V7 module writer. Update `pipeline.md` rule to reflect. Iterate on Codex's 4 content-gate failures via prompt tightening (forbid inventing -ся forms; forbid wiki-path citations; trim Ukrainian density; tighten section word budgets).
- **Option B:** Defer the lock; run another bakeoff first with corrections to claude-tools' meta-narration tendency (e.g., a strict 'produce artifacts not summaries' prompt rule). Risk: Claude's tendency may be deeper than prompt-fixable, so we might burn another bakeoff cycle for the same result.
- **Option C:** Three-writer ensemble — let the pipeline fall back from Codex → Claude → Gemini. Risk: complexity + the two fallbacks already failed; ensemble would just be 'Codex with safety net.'

## Real disagreement

There isn't one. The bakeoff signal is unambiguous: only one writer produces working output. The question is whether to ACT on the signal now or run another bakeoff to confirm it.

## Scope

- **Tracks/levels blocked:** A1 module build (POC step 3 — A1/20 build was parked pending writer choice). A2/B1/B2 module builds also blocked on this decision.
- **Issues blocked:** #1577 EPIC (3-agent contract design vertical slice) Phase 5 — actual content build cannot start until writer is chosen. #1725 (textbook-grounding) — design depends on which writer the prompt enrichment targets.
- **Paths/dirs blocked:** `scripts/build/phases/linear-write.md` writer-prompt iterations.
- **Safe to proceed:** wiki rebuild work, dependabot triage, code-scanning false-positive dismissal (when token scope refreshed), other infrastructure tasks. The 4 prerequisite fixes (#1722–#1724) are merged regardless.

## Orchestrator recommendation

**Option A — lock Codex / GPT-5.5.**

Reasoning:
1. The bakeoff produced exactly the kind of decision-grade signal ADR §3 was designed to elicit. The whole #1577 EPIC has been building toward this gate; running another bakeoff to confirm a 3-0 signal is process for process's sake.
2. Claude's failure is structural (meta-narration), not prompt-fixable. The strand-1 trace shows Claude falsely claimed tool calls — when given the artifact-generation contract, Claude's instinct is to *describe* compliance rather than *demonstrate* compliance. Different prompts won't change that.
3. Codex's failure modes (word count, section weight, invented -ся, wiki-path miscite, immersion pct) are concrete, isolatable, prompt-addressable.
4. The team-role split this validates is what predecessor handoffs already documented as practice (Claude = architect/reviewer; Codex = writer/implementer of mechanical refactors; Gemini = wiki). The bakeoff confirmed it. Ratifying it formally just removes ambiguity.

## Awaiting

User signoff:
- `go` — proceed with Option A, update `pipeline.md`, file follow-up issue for Codex prompt iteration on the 4 content-gate failures.
- `go with B because...` — defer; run another bakeoff with claude-tools prompt rework first.
- `go with C because...` — three-writer ensemble.
- `wait` — leave the lock un-recorded for now.

---

## What's already on main regardless

The 4 prerequisite fixes are shipped — main at `5a03385139`. Re-running this bakeoff won't change those. Whatever writer choice happens, the pipeline is structurally healthier than it was before this session.

---

## 2026-05-12 night bakeoff — REVISED (signal in, ACCEPTED flipped)

**Run:** `audit/bakeoff-2026-05-12-night/REPORT.md`. Dispatch `claude/bakeoff-2026-05-12-night` (Claude-headless `/goal`, opus-4-7, xhigh), duration 1033s.

**Signal:** the single-primitive prompt rewrite at `28417cc3cb` (2026-05-11 evening) — designed to eliminate codex-tools' `<verification_trace>` theatre by replacing compose-pattern citations with single calls to `verify_quote` / `verify_source_attribution` / `check_modern_form` / `check_russian_shadow` — did **not** fix codex-tools' theatre. Re-bakeoff on `a1/my-morning` with `--writer codex-tools` produced `phase_writer_summary.tool_calls_total=0` and triggered the pipeline's `MCP_TOOLS_NEVER_INVOKED` guard before any module artifact was written.

Meanwhile, the *prior* loser **claude-tools** — which in the original 2026-05-06 bakeoff produced a 485-byte meta-summary with 0/4 CoT events — now produces a full artifact set with 4 real MCP tool calls (`verify_words` ×2 on 21 + 22 Ukrainian forms, `search_text` ×2), `vesum_verified.passed=true` (159/159 forms, **0 invented `-ся` forms**), and 14-of-18 python_qg gates passing. claude-tools still commits partial theatre on the two newly-introduced single-call verifiers (`verify_quote`, `verify_source_attribution` — cited but uncalled), but strand-1 detection catches it (`writer_tool_theatre.violation_count=2`) and the structural contract is satisfied for the first time.

**Roles have reversed.** Per the original ranking rule (`tool_calls_total > 0` AND fewest hard-gate fails), claude-tools wins this bakeoff outright.

**Empirical pattern over three bakeoffs (2026-05-06 / 2026-05-08 / 2026-05-12 night):** codex-tools cannot reliably invoke MCP tools in this pipeline. Two prompt iterations (theatre detection + single-primitive rewrite) have not moved `tool_calls_total` off zero. The original Option A premise — that codex's failures are *"addressable by prompt iteration"* — has now been falsified twice.

### Decision (orchestrator-acted 2026-05-12 night follow-up)

- **Status:** ACCEPTED → REVISED (night) → **REVISED-AGAIN 2026-05-13 midday on empirical fair-env evidence**. New ACCEPTED default writer for **A1 + A2 scope: claude-tools**. Effective immediately.
- **codex-tools** remains a valid `--writer` choice but is no longer the default for A1/A2. **NOT disqualified.** Re-bakeoff at B1+/seminar scope is encouraged once A1/A2 lock is shipped — codex's verbosity/density profile may suit higher levels better.
- **Rationale (revised again):** the night-bakeoff "codex tool_calls_total=0" verdict was based on **false evidence** — issue #1900 investigation (claude-headless adversarial, 737s) found the fail-fast rollout-matcher bug in `scripts/agent_runtime/adapters/codex.py::_rollout_matches_plan` that rejected ALL codex tool-call telemetry events since 2026-04-15. Codex's actual MCP usage across the 3 pre-fix bakeoffs is in the rollout JSONLs and was always there. PR #1907 fixed the matcher; today's 2026-05-13 midday bakeoff (`audit/bakeoff-2026-05-13-midday/`) is the first fair retest. Codex made **11 successful MCP tool calls** in retry 1 and produced a full artifact set in retry 2 (post the `author`/`role` schema fix). The verdict is now on real-content merit, not false telemetry.

### Empirical bakeoff verdict — 2026-05-13 midday (fair env)

Both writers produced complete artifacts in the now-fixed pipeline (#1901 OSError, #1903 rollout matcher, #1906 writer telemetry, #1904 vesum distractor exclusion all merged). Audit dir: `audit/bakeoff-2026-05-13-midday/`.

| Metric | claude-tools | codex-tools |
|---|---|---|
| Module word count (target 1200) | 1205 ✅ | **996 (−204)** |
| Section budget adherence (4 sections, 270-330 each) | 1 over (336w) | **All 4 under (152-172w)** |
| Formatting (model-answer callout) | ✅ | ❌ missing |
| Immersion vs `a1-m15-24` cap 24% | 25.4% (1.4 over) | **51.77% (27 over — 2× cap)** |
| MCP tool calls captured | 9 with populated items | 5 with empty `result_summary` (codex-side capture gap, separate followup) |
| Truncation artifacts | none | `равцова` instead of `Кравцова` |

Claude-tools wins A1/my-morning **on content merit**: closer to target word count, better budget adherence, vastly better immersion adherence (codex would overwhelm A1 learners at 52% Ukrainian density), all formatting requirements met, no truncation. Codex-tools is functional but writer-prompt-adherence is weaker at A1.

### Reframe of the 3 pre-fix bakeoffs

The 2026-05-06 / 2026-05-08 / 2026-05-12-night bakeoffs that claimed "codex tool_calls_total=0" are **explicitly disqualified as evidence**. They measured a reporting bug (rollout matcher), not writer capability. Future bakeoff design must include a synthetic rollout-fixture replay test in `tests/replay/` (per #1905) so this class of false-evidence verdict cannot recur silently.

### Follow-ups filed

- **#1807 (existing, writer-prompt tool-theatre):** add a stronger gate to force `verify_quote` / `verify_source_attribution` invocation when the writer cites them in `<verification_trace>` (mirror the strand-1 detection but block in pipeline, not just log).
- **NEW issue (file on wake):** codex MCP catalog visibility investigation. Per the pipeline guard's own hint, `mcp_config_resolved.status=ok` only verifies config string resolution; the model must actually invoke at least one tool. Check codex rollout JSONL for `tools are not exposed in this session` errors. Until resolved, codex-tools is structurally unable to satisfy `tool_calls_total > 0`.
- **NEW issue (file on wake):** textbook_grounding `corpus_missing` HARD fail. claude-tools cited Караман Grade 10 p.176, Кравцова Grade 4 p.113, Захарійчук Grade 4 p.162; none of those pages are in the textbook corpus. Either (a) ingest the missing pages, (b) constrain the writer prompt to cite textbooks that ARE in the corpus, or (c) treat `corpus_missing` as a softer signal than `corpus_mismatch`. Pre-A1-batch-build blocker.

### What is NOT being changed by this revision

- `curriculum/l2-uk-en/a1/my-morning/` is **not** flipped to the new claude-tools artifacts. The 2026-04-26 incumbent (codex-run committed in `c91ae3bbe1`) remains the published module. The claude-tools 2026-05-12 night build still failed `correction_terminal` on `citations_resolve` + HARD `textbook_grounding` (`corpus_missing`). Publication is blocked until a green build lands.
- A1 batch build remains parked pending the corpus_missing investigation + the verify_quote / verify_source_attribution force-invoke gate.

