# Brief: Harden `scripts/build/phases/v6-write.md` — activity-count contract + Ukrainian-brief metalanguage guard

**Task ID:** `claude-1370-harden-writer`
**Worktree:** `.worktrees/claude-1370-harden-writer`
**Branch:** `claude-1370-harden-writer`
**Model:** Claude Opus 4.7, `--effort xhigh`
**Mode:** `--mode danger` (worktree-isolated, commits + push allowed)
**Parent issues:** #1370 (metalanguage leak) + Phase 3 blocker from bakeoff (activity-count gap)

## Context — why this prompt is being hardened

Phase 3 is about to fire 124 l1-uk module builds (A1 55 + A2 69) with Opus 4.7 as writer and Codex as reviewer. A writer bakeoff on 2026-04-22 (`docs/experiments/2026-04-22-writer-bakeoff-results.md`) tested 5 writers on A1 M03 `special-signs`. **Opus won on mean score (7.80) but NO writer achieved majority PASS.**

The dominant reviewer complaint across writers is **plan-adherence failures on `activity_hints` item counts**. Evidence (from `experiments/writer-bakeoff-2026-04-22/reviews/codex-on-opus.yaml`):

> "Вправа 4. Розподіл слів на три колонки. Вісімнадцять слів потрібно розподілити..."
> issue: Тип вправи збігається з планом, але реального набору з 18 слів немає. Учень отримує лише інструкцію та три приклади.

Even the bakeoff-winner writer:
- writes "Вправа 4" as inline prose content
- describes the exercise (instruction + 3 examples)
- does NOT place the 18-item word bank the plan's `activity_hints[group-sort]` asks for

The same pattern hits across the rubric: plan wants 6 items, writer delivers 2–4, written inline in prose.

**Diagnosis:** `scripts/build/phases/v6-write.md` says "markers only" (lines 47–99), but writers violate this rule under pressure from the plan's `activity_hints` visibility in the contract YAML. The plan says `items: 18`, the writer interprets that as "I should show 18 example items," writes "Вправа 4" inline with 3 examples (undershoots), and the reviewer flags plan-adherence.

**Root fix:** tighten the markers-only contract to the point writers cannot misread it. Not just "write a marker" — explicitly forbid the WRONG patterns writers fall into.

Parallel concern (#1370): a Ukrainian-only brief may push writers to over-shift into Ukrainian metalanguage in A1/A2 task instructions, violating the immersion contract (A1 = 10–50% Ukrainian). Current prompt has a guard at lines 115–136. That guard needs concretizing with a WRONG/RIGHT example.

## Worktree setup (mandatory — per `delegate-must-use-worktree.md`)

```bash
git worktree add -b claude-1370-harden-writer .worktrees/claude-1370-harden-writer
cd .worktrees/claude-1370-harden-writer
```

Do NOT branch in the main checkout.

## Files you'll touch

1. **`scripts/build/phases/v6-write.md`** — the primary target. Already has good structure; needs tighter contract on markers-only + a WRONG/RIGHT example for metalanguage containment.
2. **Possibly `scripts/audit/checks/` or similar** — AC2 from #1370 asks for a deterministic metalanguage-containment check. If the simpler prompt fix doesn't fully close the gap, write the check script. Start with prompt fix only; add check script if prompt fix alone doesn't catch the residue.
3. **Reference only (do NOT touch):**
   - `experiments/writer-bakeoff-2026-04-22/reviews/*.yaml` — bakeoff review findings
   - `experiments/writer-bakeoff-2026-04-22/reviews/_aggregate.json` — aggregate scores
   - `docs/experiments/2026-04-22-writer-bakeoff-results.md` — the writeup
   - `scripts/audit/config.py` — word targets
   - `scripts/pipeline/config_tables.py:IMMERSION_RULES` — immersion contract (referenced by prompt)

## Acceptance criteria

### AC-A: Activity-count contract hardening

In `scripts/build/phases/v6-write.md`, make these changes to the "Exercise Placement — Markers Only" section (current lines 47–99):

1. **Add a "DO NOT write these inline" subsection** with concrete WRONG examples. Examples MUST include:
   - `Вправа 4. Розподіл слів на три колонки. [...] 1. бджола, 2. здоров'я, 3. п'ять` (numbered inline items — writer falling into exercise authoring)
   - `Прочитай уголос: сім'я, п'ять, буряк, дев'ять.` (when this is meant to be a fill-in activity per plan, not a reading prompt in prose)
   - `Для тренування: _удзик, _ора, _анок, _олова` (missing-letter items inline when the plan has them as a quiz activity)
2. **Add a "rule of thumb" test**: "If your prose contains a numbered list of 2+ exercise items, or the phrase «Вправа N.» followed by a task description — STOP. You are authoring an exercise inline. Delete the items, replace with the injection marker."
3. **Cite the authority**: "The plan's `activity_hints.items: N` is a signal to the ACTIVITIES step (downstream), not a request to you. Your job is to teach the concept and place the marker. Item counts are the next step's responsibility."

The current prompt says "do NOT write exercises directly" generically. The gap is that writers treat a description with a couple of examples as NOT-an-exercise. Close that gap with explicit examples of what counts as authoring.

### AC-B: Ukrainian-brief metalanguage containment (issue #1370)

Current lines 115–136 handle this abstractly. Concretize:

1. **Add a WRONG/RIGHT example block** right after the current "Concrete rule for A1/A2" paragraph (~line 126):
   ```
   WRONG (A1 — Ukrainian prose leaks into scaffolding):
   > «Апостроф — це графічний знак, який ставиться перед я, ю, є, ї після твердих приголосних.»

   RIGHT (A1 — English scaffolding, Ukrainian terminology + examples preserved):
   > An **апостроф** (apostrophe) sits before я, ю, є, ї after hard consonants — for example **сім'я** (family), **п'ять** (five), **об'єкт** (object).
   ```
2. **Add explicit "three containment checks"** the writer runs on its own output before stopping:
   - Are task instructions ("Read the dialogue", "Match the pairs", "Fill in the blank") in English for A1? in English with optional Ukrainian-parenthetical for early A2?
   - Are section framing sentences (intro to a new concept, transition between sub-topics) in English for A1?
   - Are Ukrainian examples, dialogues, vocabulary anchors, and term labels in Ukrainian at ALL levels?

### AC-C: Bakeoff gap #2 — honesty axis

Bakeoff reviewers flagged `honesty` axis low across writers (Opus: 6.75 — their lowest axis). Honesty in this rubric = no invented rules, no over-strict claims, no fabricated examples. Current prompt has "Do not invent grammar restrictions" (line 192–194) and "Never guess about Ukrainian" (line 251). Tighten by:

1. Move "Do not invent grammar restrictions" HIGHER in the prompt (to the 9 Hard Rules block), and reword as a positive obligation: "State rules as common / typical / usually unless the plan YAML or a named Ukrainian grammar authority (Правопис 2019, Антоненко-Давидович, VESUM) says strictly."
2. Add ONE concrete honesty failure pattern: "If the wiki brief and your training conflict, the brief wins. Flag conflicts inline with `<!-- VERIFY -->` rather than silently picking the version that feels right."

### AC-D: Validation — 1-slug re-test

After prompt changes, re-run Opus on A1 M03 `special-signs` with the hardened prompt, same way the bakeoff was set up. Run Codex review against the same 6-axis rubric. Compare to the bakeoff baseline:

- Opus baseline: 7.80 mean, REVISE × 4
- Hardened target: 8.0+ mean, at least 1 PASS verdict out of 2 Codex reviews

If hardened arm does NOT improve on `plan_adherence` (baseline 8.0 per writer avg) AND `honesty` (baseline 6.75 per writer avg), the prompt changes are insufficient — iterate.

Write the re-test results to `experiments/writer-bakeoff-2026-04-22/hardened-retest/` with the same structure as the bakeoff (writer output + 2 reviews + aggregate).

### AC-E: Metalanguage-containment check script (if prompt alone insufficient)

If the hardened-retest still shows Ukrainian-prose leak in A1 task instructions, add `scripts/audit/checks/metalanguage_containment.py` that:
- reads an A1 module's prose
- extracts sentences tagged as task instructions (by position near `<!-- INJECT_ACTIVITY -->` markers, or by section header heuristic)
- counts Ukrainian-language tokens (Cyrillic-dominant word ratio > 0.5 = Ukrainian)
- fails the check if > 30% of task-instruction sentences are Ukrainian-prose
- returns structured output usable from `v6_build.py` quick-verify

Start with prompt-only fix. Only build the check script if needed.

### AC-F: Adversarial review

Before committing, run Gemini review of the hardened prompt:

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini \
  "Adversarial review of scripts/build/phases/v6-write.md hardening for #1370 + bakeoff activity-count gap. Read the file at HEAD of this worktree. Check: does the hardening close the gap without introducing new contradictions? Are the WRONG/RIGHT examples concrete enough to land? Flag any residual ambiguity." \
  --task-id issue-1370 --model gemini-3.1-pro-preview
```

Document Gemini's findings on issue #1370. Address or justify-ignoring each.

## Deliverables

1. Commits in `.worktrees/claude-1370-harden-writer` on branch `claude-1370-harden-writer`:
   - One commit: `fix(v6-write): harden markers-only contract against inline exercise authoring (#1370, Phase 3 prep)`
   - One commit (if AC-E fires): `feat(audit): metalanguage-containment check for A1/A2 (#1370)`
2. `experiments/writer-bakeoff-2026-04-22/hardened-retest/` artifacts from AC-D
3. GH issue comment on #1370 documenting:
   - Changes made (link to commits)
   - AC-D re-test scores (before vs after)
   - AC-F Gemini review findings + resolution
   - PASS/REVISE summary of whether the prompt is ready for Phase 3
4. Open a PR from `claude-1370-harden-writer` → `main`. User (Krisztian) will merge.

## What NOT to do

- Do NOT change the 9 Hard Rules numbering (downstream docs reference by number)
- Do NOT lower word-target or immersion thresholds
- Do NOT rewrite the prompt from scratch — surgical edits only
- Do NOT skip AC-D (the re-test). "Prompt looks better" is not evidence; reviewer scores are.
- Do NOT commit changes outside the worktree

## Time estimate

2–4 hours. If you're at 3h and still iterating on AC-D, comment progress on #1370 and pause for human decision.

## Resources

- `.claude/rules/delegate-must-use-worktree.md` — worktree rules
- `.claude/rules/non-negotiable-rules.md` — word targets, audit gates
- `docs/best-practices/prompt-engineering.md` — if it exists, cross-reference
- `docs/experiments/2026-04-22-writer-bakeoff-results.md` — methodology for re-test
- `experiments/writer-bakeoff-2026-04-22/reviews/_aggregate.json` — baseline scores to beat
