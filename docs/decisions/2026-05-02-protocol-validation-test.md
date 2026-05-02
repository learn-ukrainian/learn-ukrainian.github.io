# DECISION REQUIRED — protocol validation test card (synthetic)

> **Purpose:** This file is a synthetic Decision Card used to validate AC 10 of #1639 — that the cold-start protocol surfaces pending decisions to the user/agent on session start.
>
> **Not a real decision.** Resolve by deleting this file (no-op decision) or by following the `pending/` → `docs/decisions/{date}-{slug}.md` migration pattern as a dry run.

**Agents:** synthetic (no real `ab discuss` ran for this card)

**Options surfaced:**
- **Option A:** Synthetic test card serves its validation purpose, then resolve as no-op (delete).
- **Option B:** Convert this into a real "should we adopt rule X" question for actual decision-making practice.
- **Option C:** Leave the card here permanently as a always-pending sentinel that proves the cold-start scan works on every session start.

**Votes (with 1-line rationale):**
- claude → A: Once a real session reads this and surfaces it, the validation is complete. Permanent sentinel (Option C) creates noise.
- gemini → (not consulted on synthetic card)
- codex → (not consulted on synthetic card)

**Real disagreement:** None — this is a synthetic card to test the workflow.

**Scope:** {what this pending decision blocks and what remains safe}
  - Tracks/levels blocked: NONE (synthetic test, no real work blocked)
  - Issues blocked: #1639 AC 10 closure depends on this being seen + resolved
  - Paths/dirs blocked: NONE
  - Safe to proceed: ALL OTHER WORK — this card has no blocking impact, by design

**Orchestrator recommendation:** A — when the next session (Claude or human) starts and runs the cold-start protocol per `docs/best-practices/agent-cooperation.md`, they should:

1. Notice this file in `docs/decisions/pending/`
2. Surface it to the user immediately (per "pending decisions are BLOCKING within scope" rule)
3. Note that scope is NONE (so no actual work is blocked)
4. Proceed with planned work, then resolve this card by either:
   - **Deleting it** (simplest no-op resolution), OR
   - **Moving it** to `docs/decisions/2026-05-{NN}-protocol-validation-test.md` with `**Decided:** Option A` recorded (matches the documented protocol)

**Awaiting:** Whoever starts the next session running cold-start.
EOF — synthetic Decision Card for #1639 AC 10 validation.

---

**Decided:** Option A — synthetic card served its validation purpose. Cold-start protocol confirmed working end-to-end on 2026-05-02 inline session: scan surfaced the card, read produced full content, scope (NONE) correctly evaluated as non-blocking. Closes #1639 AC 10.
**Decided on:** 2026-05-02
**Decided by:** claude (orchestrator) per the documented resolution protocol
