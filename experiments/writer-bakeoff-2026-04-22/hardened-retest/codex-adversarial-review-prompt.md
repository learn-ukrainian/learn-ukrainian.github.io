# Adversarial review — v6-write.md hardening v2 for #1370 + bakeoff activity-count gap

You are performing an adversarial review of a writer-prompt hardening change. Your job is to **break** the hardening: find residual ambiguities, introduced contradictions, or places where the WRONG/RIGHT examples are not concrete enough to land with a large language model under production pressure.

**Tone:** direct, sceptical, concise. You are NOT trying to agree. You are trying to find the next failure mode the hardening does not close.

**Backstory — what already happened:** the v1 hardening was run against the A1 M03 `special-signs` fixture. Opus writer produced output with 7/7 markers placed and zero «Вправа N.» headers — the primary target was hit. But 2× Codex reviewers returned FAIL verdicts (4.8, 5.2) because the v1 STOP test over-triggered on TEACHING EXAMPLES (minimal pairs, plan-mandated pronunciation anchor lists). The v2 hardening, committed now, carves out teaching examples as explicitly ALLOWED and tightens the STOP test to answer-demanding patterns only.

---

## Context files (in order)

1. `docs/experiments/2026-04-22-writer-bakeoff-results.md` — the 2026-04-22 writer bakeoff summary.
2. `experiments/writer-bakeoff-2026-04-22/reviews/_aggregate.json` — baseline per-writer / per-reviewer scores.
3. `experiments/writer-bakeoff-2026-04-22/reviews/codex-on-opus.yaml` — baseline Codex review of bakeoff-winning Opus output.
4. `experiments/writer-bakeoff-2026-04-22/hardened-retest/results-summary.md` — v1 hardening retest: FAIL verdicts, violations flagged.
5. `experiments/writer-bakeoff-2026-04-22/hardened-retest/reviews/codex-1.yaml` and `codex-2.yaml` — the v1 retest's Codex YAMLs (the specific "inline exercise authoring" violations flagged).
6. `experiments/writer-bakeoff-2026-04-22/hardened-retest/opus/special-signs.md` — the v1 retest writer output.
7. `scripts/build/phases/v6-write.md` — the v2 hardened prompt (current state at HEAD).
8. `git diff main -- scripts/build/phases/v6-write.md` — the complete v1+v2 hardening diff.

---

## What the v1 + v2 hardening claims

- **AC-A v1**: "Exercise Placement — Markers Only" section with WRONG patterns + STOP test (2 rules) + Authority statement.
- **AC-A v2 refinement (after v1 over-trigger finding)**: new "What teaching examples ARE allowed" subsection with 4 concrete ALLOWED RIGHT examples (illustrative example list; minimal pairs; pronunciation anchor list; reading-aloud prompt with "notice what" instead of "produce answer"). Refined STOP test from 2 broad rules to 4 narrow rules — answer-demanding verbs, fill-in slot tokens, item-with-answer arrows, 6+ item word banks.
- **AC-B**: Metalanguage containment (issue #1370) — WRONG / RIGHT A1 example block + 3 containment checks.
- **AC-C**: Hard Rule #11 — "State rules honestly. Cite or hedge — never invent." Plan/brief wins over pre-training; `<!-- VERIFY -->` is positive signal.

---

## Your questions to answer

Answer each question with a specific quote from the v2 hardened file and a concrete scenario in which the gap would manifest.

1. **Does the v2 refinement (teaching examples ALLOWED / STOP test narrowed) correctly distinguish the 4 violations flagged by Codex-1/Codex-2 in the v1 retest?** Specifically: «Практика читання: п'ять, дев'ять...», «мінімальні пари: балка/палка, коза/коса», «Мінімальні пари для тренування слуху: бик/бік, дим/дім...», «Потренуйтеся зі словами: рука, робота...». Under v2, would each of these pass the STOP test? Cite the v2 text that would permit each one.

2. **Does the v2 STOP test still catch the v1-baseline Opus failure modes?** Specifically the bakeoff's original "Вправа 4. Розподіл слів на три колонки. Вісімнадцять слів..." and the "Для тренування: _удзик, _ора, _анок, _олова. Обери правильну літеру..." patterns. Cite which v2 STOP test rule each trips.

3. **The v1 retest's Opus output scored honesty=2.5 mean — rule #11 is in the prompt but the writer wrote zero `<!-- VERIFY -->` markers despite two real plan-vs-authority ambiguities (the apostrophe rule's «свято» exception; the plan's internal contradiction in `grammar[3]` about sonorants). Is rule #11 prominent enough, or is it getting buried? What would make it stickier?**

4. **Decodability in the v1 retest dropped −3.75 because the writer used A1-inappropriate abstractions («палаталізований», «подвійну природу йотованих голосних», «фонетична ідентичність мови»). Is this the hardening's fault (did any part of the hardening push toward academic register?) or is this a bakeoff-prompt-specific issue (the bakeoff's "Ukrainian Module Author" persona prompt framed the writer as an adult Ukrainian textbook author, encouraging that register)?**

5. **Is there any NEW contradiction introduced in v2 between the hardened section and an unchanged section of v6-write.md?** Example suspects: the existing line 302 "Never guess about Ukrainian" and the new rule #11; the existing "Pedagogy" bullet on line 217 "Every grammar rule needs 3+ Ukrainian examples with English translations" and the new v2 ALLOWED "illustrative example list" carve-out.

6. **Is there a residual over-trigger the v2 refinement still does not close?** Look for teaching patterns in real plan YAMLs (e.g., `curriculum/l1-uk/plans/a1/special-signs.yaml`) that would still trip the v2 STOP test unfairly.

7. **What is the ONE strongest residual failure mode the v2 hardening still does not close?** If you had to bet on what will still fail in the next bakeoff, what would it be?

---

## Output format

Return a YAML block. No preamble.

```yaml
review_of: scripts/build/phases/v6-write.md
reviewer: codex-adversarial
commit_under_review: <git rev-parse HEAD>
questions:
  Q1:
    verdict: <SUFFICIENT | PARTIAL | INSUFFICIENT>
    evidence: "<quote from v2 hardened file>"
    residual_gap: "<specific scenario, or 'none'>"
  Q2:
    verdict: <SUFFICIENT | PARTIAL | INSUFFICIENT>
    evidence: "<quote>"
    residual_gap: "<one sentence>"
  Q3:
    verdict: <SUFFICIENT | PARTIAL | INSUFFICIENT>
    evidence: "<quote from rule #11>"
    recommendation: "<what would make rule #11 stickier>"
  Q4:
    verdict: <HARDENING_FAULT | BAKEOFF_PROMPT_FAULT | SHARED>
    evidence: "<quote from whichever file>"
    recommendation: "<one-line fix>"
  Q5:
    new_contradictions: [<list each one; 'none' if none found>]
  Q6:
    residual_over_trigger: "<one scenario, or 'none'>"
    evidence: "<plan YAML or prompt quote>"
  Q7:
    one_sentence: "<the biggest residual failure mode>"
overall_verdict: <SHIP | REVISE | REJECT>
one_sentence_conclusion: "<what is the biggest thing the author should address before merge>"
```

## Time budget

~10-15 min.
