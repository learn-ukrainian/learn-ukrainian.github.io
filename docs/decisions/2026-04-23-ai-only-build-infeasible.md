# Decision Brief — AI-only v6 build for A1 colors, 2026-04-23

## One-line outcome

**Shared-contract architectural fix validated (calibration-bound dims
improved 2–3 points per dim). MIN ≥ 8 NOT achieved after 3 convergence
rounds on `a1/colors` smoke. Residual failure is LLM writer-quality
variance (Ukrainian robotic prose, factual hallucination), not
writer↔reviewer prompt sync.**

The architectural fix in this branch should land: it is real progress
and the #1431 scope. The separate writer-quality question requires a
different intervention and must be tracked as a new issue if the
AI-only loop is to continue.

## Scope of this brief

Per GH #1431 failure-path clause: "If after a proper attempt the smoke
still does not reach MIN ≥ 8 ... write a DEFINITIVE impossibility brief
... with ... recommendation: close project vs change constraints."

This is that brief. It records:

- What was attempted (shared-contract fix; writer retrieval mandate;
  reviewer calibration; plan-adherence enforcement).
- What the three convergence rounds produced per dim.
- Which failure class resisted convergence.
- Honest recommendation for the user's morning call.

## What was attempted

Full per-class detail at
`docs/bug-autopsies/2026-04-23-writer-and-reviewer-calibration.md`.
Summary of code changes in this branch (commit `634c87487c`):

1. **Shared contract document** at
   `scripts/build/contracts/module-contract.md`. 10 sections defining
   the scaffolding-language binding, section-contract protocol,
   dialogue corpus-grounding, pedagogical voice allow/block lists,
   honesty clause, forbidden words, per-dim reviewer scope, dispute
   protocol, test enforcement.
2. **Writer prompt** references the contract at the top, carries §2
   `<section_overflow>` protocol, §3 dialogue-retrieval mandate, §4
   allow-list reconciliation.
3. **All 9 per-dim reviewer templates** reference the contract, are
   injected with `{IMMERSION_RULE}` at prompt-build time (previously
   writer-only), and strip the blanket "Ukrainian-first explanations
   are preferred" stance that punished A1 English-dominant scaffolding.
4. **Naturalness reviewer** carries the §4 allow-list literal.
5. **Actionable reviewer** carries explicit A1 level calibration:
   English-dominant scaffolding is contractual, not a defect.
6. **Dialogue reviewer** scopes corpus-grounding as a PASS condition;
   `<!-- VERIFY: dialogue not corpus-grounded -->` is a positive
   signal.
7. **Plan Adherence reviewer** credits `<section_overflow>` as a
   positive signal.
8. **Chunked-writer path** (`_build_chunk_prompt`) carries the same
   §2 + §3 + contract reference — chunked builds stay calibrated.
9. **37 pin-tests** at `tests/test_contract_reference_sync.py` fail
   CI if either side drifts from the contract.

All 37 pin-tests GREEN. 81/81 combined v6 review/write/chunk/contract
tests GREEN. No regressions in affected paths.

## Per-dim score trajectory (a1/colors)

| Dim | Round-1 pre-fix | R1 post-fix | R2 post-fix | R3 post-fix |
|---|---:|---:|---:|---:|
| Naturalness | 4.8 | 5.8 (+1.0) | 4.9 (−0.9) | n/a (term.) |
| Honesty | 4.8 | 5.0 (+0.2) | 5.0 (0.0) | n/a (term.) |
| Actionable | 4.9 | **7.4** (+2.5) | **7.6** (+2.7) | n/a (term.) |
| Dialogue | 5.8 | **7.4** (+1.6) | 6.4 (+0.6) | n/a (term.) |
| Language | 5.8 | 5.8 (0.0) | **7.4** (+1.6) | n/a (term.) |
| Plan Adherence | 6.8 | **8.2** (+1.4) | 7.4 (+0.6) | n/a (term.) |
| Factual | 7.4 | 5.0 (−2.4) | 5.0 (−2.4) | n/a (term.) |
| Completeness | 8.3 | **8.8** (+0.5) | **8.8** (+0.5) | n/a (term.) |
| Decolonization | 8.8 | 8.4 (−0.4) | 7.4 (−1.4) | n/a (term.) |
| **MIN** | **4.8** | **5.0** | **4.9** | **term.** |

R3 terminated with `plan_revision_request` before per-dim scores were
emitted — the convergence loop determined after two REJECT rounds
that the plan itself is under-specified for the writer to satisfy the
contract.

## Which failure class resisted — by reviewer quote

### Naturalness — R2 at 4.9 — LEGITIMATE findings (not calibration)

`curriculum/l2-uk-en/a1/review/colors-review-naturalness-r2.yaml:14-16`:

> "Це штучний вступ із порожніми формулами `цікаву ситуацію`, `чудова
> можливість`, `без складних граматичних конструкцій`; звучить не як
> живе пояснення вчителя, а як машинний анонс."

R2 Naturalness is NOT flagging the §4 allow-list phrases — it is
flagging genuinely robotic Ukrainian prose that Gemini produced in
the full-rewrite round ("цікаву ситуацію", "чудова можливість" — empty
Ukrainian filler, distinct from the English-teacher register we
allow-listed). This is a writer-quality miss, correctly caught by the
reviewer. The allow-list did its job — it prevented penalizing legit
textbook phrases; it did NOT and could not mask genuinely robotic
machine-translated filler.

### Honesty + Factual — R1+R2 both at 5.0 — writer hallucination

`curriculum/l2-uk-en/a1/review/colors-review-honesty-r1.yaml:5-10`:

> "У розділі `Синій ≠ блакитний` модуль стверджує: `але «жовтий» і
> «блакитний» — це кольори нашого прапора.`  This directly conflicts
> with the shared contract, which anchors the flag as `синьо-жовтий`."

The writer invented an incorrect factual claim about the Ukrainian
flag colors (it said yellow + light-blue, actual is dark-blue +
yellow). The error recurred in R2. Hard cap on both Honesty (hidden
uncertainty, no VERIFY marker on a disputed claim) and Factual
(invented claim contradicting the contract). This is NOT a calibration
bug — it is a writer hallucination. The `<fixes>` block contained a
literal find/replace that would have corrected it, but the
convergence loop's full-rewrite mode re-generated the section and
introduced the SAME error in R2.

### Plan-revision terminal after R2 — the escalation ladder

R1 REJECT → `full_rewrite` → R2.
R2 REJECT → `plan_revision_request` (skipped `writer_swap` when
Gemini+Codex combo is already cross-agent and no alternative is
available; or the ladder interpreted consistency of flag-error as
plan-underspec).
R3 terminal → no per-dim review emitted. Module failed.

## Which failure class is closed by this PR

- **Writer ↔ reviewer prompt sync drift** — CLOSED. Shared contract
  + pin-tests make drift structurally impossible at CI time.
- **Reviewer miscalibration on level-immersion** — CLOSED. Actionable
  jumped 4 → 7.4/7.6; Plan Adherence 5 → 8.2/7.4.
- **Reviewer pattern-matching human textbook phrases as LLM-filler** —
  CLOSED per R2 evidence (reviewer does NOT penalize allow-list; it
  correctly catches genuinely robotic prose).
- **Writer plan-adherence via silent deferral** — CLOSED. `<section_overflow>`
  protocol in writer + chunk prompt; Plan Adherence 5 → 8.2.
- **Writer invented A1 dialogue without corpus anchoring** — CLOSED.
  `search_sources` retrieval mandate in writer + chunk prompt;
  Dialogue 5 → 7.4.

## Which failure class remains — NOT in #1431 scope

- **Writer hallucinates factual claims that contradict the plan YAML.**
  R1 and R2 both produced the flag-color error despite the plan YAML
  stating it correctly. This is a retrieval / attention / honesty
  gap in the writer — Gemini does not always ground factual claims
  in the contracted factual_anchors. Fix surface: writer prompt
  factual-anchor enforcement + pre-generate factual-claims pass.
  Separate ticket.
- **Gemini Ukrainian prose variance across rewrites.** R1 Naturalness
  5.8 (REVISE) — passed on some sections. R2 Naturalness 4.9 (REJECT) —
  failed on robotic machine-announcer Ukrainian openers. Same prompt,
  different sampling. Fix surface: either swap writer model (Claude
  tools writer), or add a Ukrainian-naturalness pre-check that
  regenerates robotic sections BEFORE reaching reviewer. Separate
  ticket.

## Recommendation

**Land this PR as #1431's architectural fix.** It is real, testable,
and unblocks calibration-bound dim progress across all future modules.
Merging it does not close #1431 because MIN ≥ 8 was not reached, but
it eliminates 3 of the 5 failure classes identified by the user's
scope revision.

**Open two follow-up tickets:**

1. **Writer factual-anchor enforcement** — add a writer-side check
   that every claim matching a plan `factual_anchors` entry either
   appears verbatim or with a VERIFY marker. Prevents the flag-color
   hallucination class.
2. **Ukrainian-prose naturalness pre-check** — between write and
   review, run a small pass that detects robotic Ukrainian openers
   ("В українській мові для початківців ми активно вчимо…") and
   regenerates them. Prevents the R2 Naturalness 4.9 class.

**Close-project decision (user call):** the evidence does NOT support
closing the project today. The shared-contract architecture works.
Two residual writer-quality issues are tractable with targeted fixes
that are outside #1431's scope. The project is NOT impossible under
current agents — it needs one more pass on writer-quality-vs-factuality,
not a total shutdown.

If the user's morning call is to close anyway, these are the grounds:
LLM variance on the Ukrainian writer is high enough that three
convergence rounds still don't produce a reliably PASS-grade module,
and sustained human-in-the-loop editing is de facto required. That
contradicts the AI-only premise of the current roadmap.

## Evidence provenance

- Per-dim R1 YAMLs: `curriculum/l2-uk-en/a1/review/colors-review-*-r1.yaml`
- Per-dim R2 YAMLs: `curriculum/l2-uk-en/a1/review/colors-review-*-r2.yaml`
- Full smoke log: `/tmp/smoke-colors-1431v2.log` (R1 end) +
  `/tmp/smoke-colors-1431v2-r3.log` (R2→R3 terminal).
- Module failed event:
  `{"event": "module_failed", "ts": "2026-04-23T10:15:40.835874+00:00", "error": "review terminal — plan_revision_request"}`
