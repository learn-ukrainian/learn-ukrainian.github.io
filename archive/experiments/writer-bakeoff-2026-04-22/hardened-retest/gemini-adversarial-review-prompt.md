# Adversarial review — v6-write.md hardening for #1370 + bakeoff activity-count gap

You are performing an adversarial review of a writer-prompt hardening change. You do NOT know what the author of the hardening was trying to protect against — but you will find out by reading the context files and then the diff. After that, your job is to break the hardening: find residual ambiguities, introduced contradictions, or places where the WRONG/RIGHT examples are not concrete enough to land with a large language model under production pressure.

**Tone:** direct, sceptical, concise. You are NOT trying to agree. You are trying to find the next failure mode the hardening does not close.

---

## Context

Read these files, in order:

1. `docs/experiments/2026-04-22-writer-bakeoff-results.md` — the 2026-04-22 writer bakeoff summary. 5 writers, no majority PASS, dominant reviewer complaint was plan-adherence failures on `activity_hints` item counts.
2. `experiments/writer-bakeoff-2026-04-22/reviews/_aggregate.json` — per-writer and per-reviewer aggregate scores.
3. `experiments/writer-bakeoff-2026-04-22/reviews/codex-on-opus.yaml` — the Codex review of the bakeoff winner (Opus). Note specifically the `plan_adherence.missing_from_plan` entries and the `activity_hints[group-sort]: 18 words, module has 3 examples` pattern.
4. Current file at HEAD of branch `claude/claude-1370-writer-harden`: `scripts/build/phases/v6-write.md` (the hardened prompt).
5. Previous version at `main`: `git show main:scripts/build/phases/v6-write.md` (the baseline).
6. `git log -p main..HEAD -- scripts/build/phases/v6-write.md` — the full diff of the hardening.

---

## What the hardening claims to do

- **AC-A** (markers-only contract): a new "WRONG — do not write these inline" subsection with 4 concrete failure patterns drawn from the Opus bakeoff output, plus a "STOP test" the writer runs before finishing, plus an "Authority — activity_hints.items belongs to the NEXT step" clarification.
- **AC-B** (metalanguage containment for issue #1370): a new WRONG / RIGHT example block for A1 scaffolding + three containment checks (task-instruction language, section-framing language, Ukrainian-kept-Ukrainian content).
- **AC-C** (honesty): a new Hard Rule #11 "State rules honestly. Cite or hedge — never invent." with an explicit `<!-- VERIFY -->` pattern for plan-vs-pretraining disagreement. The old standalone "Do not invent grammar restrictions" section was removed as redundant.

---

## Your questions to answer

Answer each question directly. Support each answer with a specific quote from the hardened file and a concrete scenario in which the gap would manifest.

1. **Does the WRONG / RIGHT block in AC-A cover the specific failure modes in the Opus bakeoff output?** Specifically, the Codex review's `plan_adherence.missing_from_plan` lists: odd-one-out 6 items → writer gave 2; fill-in 6 → writer gave 3; error-correction 6 → writer gave 1; group-sort 18 → writer gave 3; true-false 6 → writer gave 2; quiz G/Ґ 6 → writer gave 4. Is the WRONG block comprehensive enough that a writer under production pressure would NOT produce each of these patterns?

2. **Is the STOP test deterministic enough that a writer can self-check it?** Could a writer read "my prose contains a numbered list of two or more exercise items" and still rationalize its output as "not an exercise, just teaching examples"? Where's the loophole?

3. **Does AC-B's WRONG / RIGHT for metalanguage leak address the full failure mode?** The failure mode is: Ukrainian-only brief pushes the writer to render task instructions, section framing, and transitions in Ukrainian prose at A1 where the immersion contract requires English. Does the single WRONG example (the "Апостроф — це графічний знак..." sentence) generalize to the full class of leaks (task instructions, section framing), or does the writer need multiple examples to infer the pattern?

4. **AC-C's Hard Rule #11 was added at position 11 but the block is still titled "9 Hard Rules" — is this a contradiction that will confuse a writer reading the block from the top?** (The baseline already had 10 rules under this title, so the confusion predates the hardening — but the hardening did not fix it either. Worth calling out or not?)

5. **Is there any NEW contradiction introduced between the hardened section and an unchanged section?** For example, the existing line "Never guess about Ukrainian" (around line 302) and the new rule #11 both discuss `<!-- VERIFY -->`. Do they align, or do they give conflicting guidance on when to use the marker?

6. **If a writer strictly follows the hardening, does any plan requirement become UNSATISFIABLE?** For example: a plan's `content_outline` says "Practice: read the following words aloud: п'ять, дев'ять, м'який". Is this a teaching-example list (allowed) or a reading-aloud activity (must be a marker per the STOP test)? How should a writer decide?

7. **What's the strongest ONE residual failure mode the hardening still does not close?** If you had to bet on what will still fail in the next bakeoff, what would it be?

---

## Output format

Return a short YAML block:

```yaml
review_of: scripts/build/phases/v6-write.md
reviewer: gemini-3.1-pro-preview
commit_under_review: <git rev-parse HEAD>
questions:
  Q1:
    verdict: <SUFFICIENT | PARTIAL | INSUFFICIENT>
    evidence: "<quote from hardened file>"
    residual_gap: "<specific scenario the hardening does not close, or 'none' if SUFFICIENT>"
  Q2:
    verdict: <SUFFICIENT | PARTIAL | INSUFFICIENT>
    evidence: "<quote>"
    residual_gap: "<one sentence>"
  # ... same structure for Q3..Q7
overall_verdict: <SHIP | REVISE | REJECT>
one_sentence_conclusion: "<what is the biggest thing the author should address before merge>"
```

No preamble. Return the YAML only.

## Time budget

~15 min.
