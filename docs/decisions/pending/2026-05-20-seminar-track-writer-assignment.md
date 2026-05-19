# DECISION REQUIRED — Which writer for SEMINAR tracks (hist / bio / lit family / oes / ruth / folk / istorio)?

**Status:** PROPOSED
**Surfaced:** 2026-05-20 overnight (user AFK), per predecessor handoff `2026-05-19-night-hermes-mcp-observability-fixed.md` § "Writers per track — partially documented" and carry-over task #9. Predecessor described the gap precisely: *"Seminars implicitly fell through to claude-tools when CORE switched. **No explicit ADR yet.**"*
**Source:** Implicit fallthrough in `scripts/config/agent_fallback_substitutions.yaml`; no decision in `docs/decisions/` covers seminars; existing writer-selection ADR (`2026-05-06-writer-selection-codex-gpt55.md`) scope is CORE A1-C2 explicitly.
**Scope:** SEMINAR profile (`hist`, `istorio`, `bio`, `lit`, `lit-essay`, `lit-hist-fic`, `lit-fantastika`, `lit-war`, `lit-humor`, `lit-youth`, `lit-doc`, `lit-drama`, `lit-crimea`, `oes`, `ruth`, `folk`) writer-tools selection in the V7 pipeline. **Does NOT touch:** CORE writer selection (covered by `2026-05-06-writer-selection-codex-gpt55.md`); wiki writer (Gemini per `2026-04-26-reboot-agent-responsibilities.md` §1); pipeline reviewer (Codex / cross-agent / no self-review per `2026-04-26-reboot-agent-responsibilities.md` §2).
**ADR clauses referenced:** `2026-04-26-reboot-agent-responsibilities.md` §3 (writer-selection via strict bakeoff); MEMORY #M0 (2026-06-15 sunset of `delegate.py --agent claude`).

---

## The gap

Per `scripts/config/agent_fallback_substitutions.yaml` + the existing CORE writer-selection ADR, the documented writer pool today is:

| Track type | Current writer | Source of decision | Post-2026-06-15 fallback |
|---|---|---|---|
| CORE (A1-C2) | claude-tools | `2026-05-06-writer-selection-codex-gpt55.md` (REVISED 2026-05-13 midday) | deepseek-tools xhigh (substitutions.yaml) |
| Wiki content | gemini-tools | `2026-04-26-reboot-agent-responsibilities.md` §1 | gemini-tools (unmetered, persists) |
| Pipeline reviewer | codex-tools | `2026-04-26-reboot-agent-responsibilities.md` §2 | codex-tools (persists) |
| **SEMINARS** | **claude-tools (implicit fallthrough)** | **NONE — implicit default** | **UNDEFINED** |

User context noted in predecessor handoff: *"historically everything was written by Gemini"* — Gemini handled v3/v4/v5 module writing across both CORE and seminar. Seminars never got an explicit transition when CORE switched to claude-tools, so they implicitly fell through to claude-tools via the substitutions map default.

The blocker: **post-2026-06-15 the `delegate.py --agent claude` lane is sunset (MEMORY #M0, user direction 2026-05-13).** So even the implicit default expires in less than 4 weeks. Seminar builds will start failing-to-route the moment that date passes unless we set an explicit policy.

---

## Three candidate seminar writers

### A. gemini-tools (HISTORICAL BASELINE, my recommendation)

| Pro | Con |
|---|---|
| Historical baseline — handled v3/v4/v5 seminars before CORE-switch. Empirical record exists. | No fair-env seminar bakeoff yet to compare current state against alternatives. |
| Unmetered (Google Workspace allowance), no per-dispatch cost concern. | Gemini's `tool_calls_total=0` measurement-artifact issue noted in `2026-05-06-writer-selection-codex-gpt55.md` was retracted, but ADR memory of that period may bias against Gemini. |
| Survives 2026-06-15 sunset (only Claude is gated, not Gemini). | Less recent V7-pipeline shakedown than claude-tools or codex-tools. |
| Aligns with "wiki writer = Gemini always" — same agent, different role; cross-agent reviewer (Codex) still satisfies no-self-review invariant. | Seminar content (historical narrative, literary analysis) demands different register than wiki summaries — Gemini's strength there is unproven. |

### B. codex-tools

| Pro | Con |
|---|---|
| Recent fair-env empirical wins on CORE A1 — `tool_calls_total=11` on retry 1 per the 2026-05-13 fair-env retest. | Per the same retest: CORE A1 word_count 996/1200, immersion 51.77% > 24% A1 cap — content register adherence is the friction. Seminar register demands may differ. |
| Survives 2026-06-15 sunset. | Codex's lane in #M0 is "mechanical-with-design-judgment"; seminar writing is creative-narrative, less in-lane. |
| Recent /goal driver experiments (#1884 + `claude_extensions/rules/goal-driven-runs.md`) are Codex-strong if we adopt per-tab /goal-driven writers (see PROPOSED `2026-05-13-writer-split-by-tab.md`). | The /goal-driven-writers experiment is itself unresolved. |

### C. deepseek-tools

| Pro | Con |
|---|---|
| Newest writer tier added via PR #2158 (2026-05-19). | Least bakeoff-tested of the three candidates; no seminar data. |
| Hermes-routed; #M-10 observability fix landed today (textbook_grounding gate now sees deepseek's get_chunk_context calls); writer telemetry observability confirmed via b1 build. | DeepSeek-pro content-review primary per #M0; using it ALSO as seminar writer creates the self-review-adjacent risk if the same model variant later reviews its own writes. Need explicit cross-agent guard. |
| Survives 2026-06-15 sunset. | Less project-tooling familiarity than gemini-tools (which has been the wiki writer since 2026-04-26). |

### Not viable

- **claude-tools** as seminar default — expires 2026-06-15 per #M0. Could be retained as pre-2026-06-15 fallback only.

---

## Recommendation

**Pick gemini-tools as the SEMINAR writer DEFAULT, effective immediately.** Reasoning:

1. **Historical baseline restored.** Reverting to Gemini for seminars matches the pre-CORE-switch state. Reviewers (Codex) and gate suite are unchanged, so risk of regression is bounded.
2. **2026-06-15-safe.** Survives the Claude-dispatch sunset with no transition work needed.
3. **Cost-aligned.** Unmetered; doesn't compete for Codex / DeepSeek slots that #M0's 3:3:3 split prioritizes for CORE coding + content review.
4. **Cross-agent reviewer still satisfied.** Pipeline reviewer = Codex; SELF_REVIEW_DETECTED gate (`docs/decisions/2026-04-26-reboot-agent-responsibilities.md`) stays intact because writer (Gemini) ≠ reviewer (Codex).
5. **Conservative until empirical evidence says otherwise.** A bakeoff CAN be commissioned later if Gemini underperforms on a specific seminar profile — but spinning up a 4-writer bakeoff before any seminar has been built is premature.

### Concrete actions if accepted

1. Update `scripts/config/agent_fallback_substitutions.yaml` so the SEMINAR profile's primary writer is `gemini-tools` (not the implicit claude-tools fallthrough).
2. Add a new ADR `docs/decisions/2026-05-20-seminar-writer-selection-gemini.md` mirroring the structure of `2026-05-06-writer-selection-codex-gpt55.md` but scoped to seminars.
3. Update MEMORY.md `WRITER + REVIEWER POLICY` to name the seminar writer explicitly (currently silent on seminars).
4. Trigger a one-module proof build of a HIST module (e.g., `hist-001` if it exists, otherwise the lowest-sequence seminar) with `gemini-tools` to verify the pipeline routes correctly + the gate suite tolerates seminar content. This is NOT a bakeoff — it's a smoke test. If it passes, the policy stands; if it fails specifically due to writer issues, we re-open the choice.

### When to revisit

Triggers for re-opening this decision:

- Seminar build emits any of the rollback criteria from `2026-05-06-writer-selection-codex-gpt55.md`: invented `-ся` forms on non-reflexive verbs, wiki-path strings in references[], immersion >35% (less applicable to seminars — historical narrative is monolingual-UA per the seminar profile, so the upper-bound is different; revise threshold per profile if needed).
- A user-flagged seminar quality concern (factual error in HIST/BIO, fabricated citation in LIT, etc.) traces back to Gemini-tools writer rather than upstream plan.
- DeepSeek-tools or Codex-tools matures with a HIST/LIT-specific fair-env bakeoff result.

### What I'm NOT recommending

- ❌ **Pre-emptive bakeoff.** Burns Codex + Gemini + DeepSeek quota before we have a single seminar module to compare. Premature optimization.
- ❌ **Per-seminar-profile split** (e.g., gemini for HIST/BIO, codex for LIT, deepseek for OES). Adds routing complexity for no demonstrated benefit. If a profile-specific issue surfaces, address it then.
- ❌ **DeepSeek-tools as primary** before its self-review interaction with content-review (also DeepSeek-pro) is bounded. The cross-agent invariant is non-negotiable.

---

## Rollback / failure clauses

If gemini-tools ships a seminar module that fails the existing hard-gate suite AND the failure traces specifically to writer-content-quality (NOT a Gemini-pipeline issue solvable by patch), this decision is REVERTED and a fair-env bakeoff between codex-tools + deepseek-tools (with gemini-tools as control) is commissioned. The threshold:

- 2+ seminar module builds fail at the same content-gate dimension (e.g., both bio modules fail `citations_resolve`).
- OR a single seminar module fails THREE distinct content gates that all map to "writer didn't understand seminar register."

Per ADR-007 / dec-001, the rollback is to bakeoff selection — never to "let it ride." Quality is non-negotiable.

---

## What happens if user does NOT respond before 2026-06-15

This decision is **blocking for seminar builds only** — CORE builds proceed unaffected. If the user doesn't decide before 2026-06-15:

- 2026-06-15: `delegate.py --agent claude` is sunset → seminar builds via the implicit claude-tools fallthrough will fail-to-route.
- The orchestrator (me) treats this card's recommendation as the de-facto policy at that point — gemini-tools, the historical baseline + sunset-safe choice — and ships the substitutions.yaml change + ADR.
- The card remains open for user override. The substitutions.yaml change is reversible in one commit.

This is the same "drive by default, ask permission only when stakes are uncertain" posture from MEMORY #M-6. Gemini-as-seminar-writer is the obvious default; the card asks only because there's a contrary path (bakeoff first) that has cost implications I shouldn't choose unilaterally.

---

## Cross-links

- Existing writer-selection ADR (CORE): `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md`
- Agent responsibilities reboot: `docs/decisions/2026-04-26-reboot-agent-responsibilities.md`
- Substitutions config (current implicit fallthrough): `scripts/config/agent_fallback_substitutions.yaml`
- MEMORY #M0 (2026-06-15 sunset): see `memory/MEMORY.md`
- Predecessor handoff identifying the gap: `docs/session-state/2026-05-19-night-hermes-mcp-observability-fixed.md` § "Writers per track"
- Tonight's handoff: `docs/session-state/2026-05-20-overnight-three-gate-fixes-plus-2151-dispatch.md`
