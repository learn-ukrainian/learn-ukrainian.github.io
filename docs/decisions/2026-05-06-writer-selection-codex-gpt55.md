# ACCEPTED — Codex (GPT-5.5 / codex-tools) is the V7 module writer (default until next bakeoff signal)

**Status:** ACCEPTED 2026-05-06 (user signoff, conditional on Part B)
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
