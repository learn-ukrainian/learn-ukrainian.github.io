# Session Handoff — 2026-04-25 early: comprehensive a1/1 fix orchestration

> **TL;DR** Tonight was a slog. The convergence-loop fix (#1545) merged successfully
> and **the infrastructure is proven** — fixes apply, scores move, the loop converges.
> But a1/1 still terminal-fails because **the surrounding pipeline has 17 distinct
> bugs/conflicts** that prevent the module from passing review, even with the
> convergence fix in place. Manual content patches are NOT a valid path. We need
> to fix the prompts/code so the pipeline produces passing modules unaided.
> User explicitly: no rerun until ALL problems fixed.
>
> **Goal of next session**: orchestrate 6 dispatched units (4 in parallel, then 1
> sequential, then verification) to fix all 17 issues. End state: a1/1 + a1/2 +
> a1/3 all pass `--force` builds end-to-end.

---

## What shipped this session (5 PRs merged tonight)

| PR | Subject | SHA | Status |
|---|---|---|---|
| #1545 | fix(convergence): apply reviewer `<fixes>` before tier-5 escalation | c07a498619 | ✅ merged |
| #1546 | feat(statusline): show effort.level + thinking.enabled + CI path filter widen | d38003193e | ✅ merged |
| #1547 | feat(telemetry): per-tool timing from PostToolUse hook (#1541) | 18901dd89a | ✅ merged |
| #1548 | feat(monitor-api): /api/git/cleanup endpoint (#1395) | a29b2d3461 | ✅ merged |
| #1549 | feat(governance): postmortem validator + INDEX automation (#1522) | 8cc72b677e | ✅ merged |

**Main is at `8cc72b677e` (or later if more lands).**

---

## The verification that exposed the gap

Ran `v6_build.py a1 1 --step review --resume` with the merged convergence fix.
**Outcome**: build progressed correctly, applied 11/16 reviewer fixes (the #1545
signature — was 0/16 before fix), Honesty jumped 6.4 → 9.5. Dim scores after R2:

| Dim | Score | Verdict |
|---|---|---|
| Decolonization | 9.8 | PASS |
| Completeness | 9.6 | PASS |
| Honesty | 9.5 | PASS |
| Language | 9.0 | PASS (1 minor: Latin `[y]` IPA) |
| Actionable | 8.8 | PASS (1 minor: abstract rule) |
| Plan Adherence | 8.7 | PASS (1 minor: dialogue speaker labels) |
| Factual | 8.2 | REVISE (3 minors: stress marks — INVALID, see below) |
| Naturalness | 8.0 | PASS (1 major drafting leak + 1 minor tone) |
| **Dialogue** | **7.0** | **REVISE (2 majors: speaker labels + lecture tone)** |

Build terminal-failed at `plan_revision_request` (tier 5) — but NOT from the 9 review dims.
The terminal came from `exercise_quality` dim with persistent finding nf_9b2ce3f5744c855b:
"Regenerate the module so the activity order matches the plan's activity_obligations."

So the failure has TWO axes:
1. Dialogue dim too low (Codex over-strict for A1 beginner-stage dialogue)
2. `exercise_quality` plan-revision request from activity-order check

---

## The 17-item fix list (USER-CONFIRMED FROM THE INTERACTIVE SESSION)

### A. Pipeline / prompt bugs

1. **INLINE_MIN/MAX hardcoded** — prose has 8 `<!-- INJECT_ACTIVITY -->` markers but
   prompt says "Inline | Min 4 | Max 6" + checklist "did NOT create more than 6
   markers". Impossible math. Writer cannot satisfy both rules.
2. **Configs treated as MAX, but CLAUDE.md says they're MIN.** Need project-wide sweep
   of `*_MAX` keys in `scripts/audit/config.py` + audit gates.
3. **Forbidden vs Recommended type list conflicts** in
   `scripts/build/phases/v6-activities.md`:
   - `translate` is FORBIDDEN at line 37 but listed as "Best at this level" line 523
   - `error-correction` same conflict (FORBIDDEN line 37, "Best" line 524)
   - `unjumble` listed as Workbook PRIORITY (line 36) but "DO NOT use" (line 526)
4. `{TYPE_DIVERSITY}` placeholder degrades to literal `0`, producing
   "MUST use at least 0 distinct activity types" + `If 0 is 0, no enforcement` —
   confusing distraction from substitution failure.
5. **Plan vocabulary doesn't include 33 letters or their key_words** — the letter-grid
   activity items reference key_words like "ананас" that aren't in plan vocab,
   causing grounding-check failures and the "19/30 vocab tested" warning.
6. Seminar types (~80 lines, lines 492–496 of activity prompt) included in non-seminar
   prompts — pure distraction.
7. Topic-specific patterns reference textbook §s the writer can't access (lines 538–630
   of activity prompt).
8. **`exercise_quality` plan_revision_request** triggered by activity ORDER not matching
   plan's `activity_obligations`. Order should be relaxed to set-membership — order is
   incidental.

### B. Reviewer calibration (USER POINT — A1 M1-M3 special case)

9. **Dialogue dim has no awareness that A1 M1-M3 modules CAN'T have rich dialogue.**
   Beginners haven't learned enough Ukrainian to construct sentences. The reviewer
   (Codex/gpt-5.5) is holding "Привіт! Я Марко. Як тебе звати?" to advanced standards.
   Score 7.0 reflects reviewer over-strictness, not content failure.
   **Fix**: per-module pedagogical context injection into reviewer prompts.
   For A1 M1-M3 Dialogue specifically: "Module is at beginner stage. Score on
   pedagogical fit (greeting exchange, name introduction), not richness."

### C. Content issues (writer-prompt fixes)

10. Stress missing on greeting chunks (Добрий день, На все добре). **INVALID FINDING:**
    stress is added by deterministic annotator AFTER review. Reviewer should NEVER see
    or comment on stress. **Fix**: pre-strip stress marks before reviewer dispatch +
    add reviewer-prompt rule "never flag stress."
11. Latin `[y]` IPA used for Ukrainian И. Writer-prompt rule: "Cyrillic phonetic
    notation only — `[а] [о] [у] [е] [и] [і]`. No Latin IPA."
12. Drafting leak: "Use the Ukrainian sound symbols here:" embedded in prose.
    Writer-prompt rule: forbid meta-language in prose; pre-publish lint regex.
13. Plan REQUIRED `Марко:` / `Софія:` speaker labels. Writer used em-dashes instead.
    Writer-prompt rule: when plan specifies named speakers, MUST format as
    `**Name:** «...»` for every turn.
14. Dialogue line "«Рада»? Я кажу «рада», бо я дівчина." reads as grammar lecture.
    Writer-prompt rule: dialogue is conversation; explain grammar AFTER dialogue,
    never inside quotation marks. Concrete antipattern examples needed.

### D. Activity quality

15. 27 context gaps in activities — items reference content not in prose. **Fix**:
    activity-prompt strict grounding rule + pre-validation gate (move EARLIER, before
    review).
16. 19/30 plan-required vocab tested. **Fix**: activity-prompt obligation: 100%
    coverage of `vocabulary_hints.required` is mandatory; pre-generate validation.
17. 3 answer gaps. **Fix**: activity validator schema enforcement.

### Agent role clarification (user-confirmed + USER OVERRIDE 2026-04-25)

- **CURRENT default**: Writer = claude-tools (claude-opus-4-7), Reviewer = codex-tools (gpt-5.5).
  Per-dim routing is NOT implemented in code — single agent for all 9 dims.
- The MEMORY note "Claude reserved for cultural/creative nuance dims" is
  **aspirational, NOT current operational policy.**
- **USER OVERRIDE 2026-04-25**: We will TEST `gpt-5.5 writes / claude reviews`
  against the current default in Unit 6 head-to-head on a1/1. User's Ukrainian
  teachers reported positive feedback on gpt-5.5 output; worth empirical
  validation. If the flip wins on a1/1 it becomes the default for a1/2 + a1/3.
  If it loses, we keep the current pair.
- **Always pass `--writer X --reviewer Y` explicitly** in build commands. Defaults
  silently flip; explicit flags prevent confounders.

---

## Dispatch plan — 6 units

### Sequencing

```
Phase 1 (parallel — 2 Claude + 2 Codex slots, all 4 fire at once):
  Unit 1 (Claude)  — Reviewer hardening: stress + level context (B1c)
  Unit 2 (Codex)   — Writer prompt sweep
  Unit 3 (Codex)   — Activity prompt sweep + plan vocab
  Unit 5 (Codex)   — exercise_quality contract: order → set-membership

  Wait for all 4 to merge.

Phase 2 (Claude, after Phase 1):
  Unit 4 — Audit config min/max philosophy sweep (depends on Unit 3 having
           clarified what configs are actually consumed)

  Wait for merge.

Phase 3 (orchestrator inline, after Phase 2):
  Unit 6 — Verification: rerun a1/1 --force, then a1/2 + a1/3 --force in parallel.
```

### Unit 1 — Reviewer hardening (Claude, ~150 LOC)

**Files**:
- `scripts/build/v6_build.py` (~line 5826: per-dim reviewer dispatcher) — pre-strip
  stress marks from reviewer input via existing util.
- `scripts/build/phases/v6-review/v6-review-factual.md` — add stress-skip rule.
- `scripts/build/phases/v6-review/v6-review-dialogue.md` — add level-aware block:
  for A1 M1-M3, score on pedagogical fit not richness.
- All other dim reviewer prompts under `scripts/build/phases/v6-review/` — add
  defensive stress-skip rule.
- Dispatcher must inject `{learner_level}`, `{module_index}`, `{module_total}`
  placeholders into reviewer prompts.

**Verification**: re-run a1/1 review-only against current patched content.
Dialogue should score ≥ 8.0; Factual should NOT flag stress.

**Brief location**: `/tmp/briefs/claude-unit1-reviewer-hardening.md` (TO WRITE in next session)

### Unit 2 — Writer prompt sweep (Codex, ~80 LOC)

**File**: `scripts/build/phases/v6-write.md`

**Edits** (5 rules, each with concrete examples):
1. Cyrillic-only phonetic notation (no Latin IPA)
2. No drafting-leak phrases (Use X here, Insert, Add, List, Apply)
3. Speaker labels mandatory when plan requires named speakers
4. Dialogue is conversation, not grammar lecture (concrete antipattern)
5. Writer must NOT add stress marks (defensive reminder)

**Verification**: rebuild a1/1 prose with fresh writer pass; manual eyeball.

**Brief location**: `/tmp/briefs/codex-unit2-writer-prompt-sweep.md`

### Unit 3 — Activity prompt sweep + plan vocab (Codex, ~250 LOC)

**Files**:
- `scripts/build/phases/v6-activities.md` — strip Forbidden/Recommended conflicts,
  remove seminar types from non-seminar level, fix `{TYPE_DIVERSITY}` placeholder,
  add 100% required-vocab obligation, strict grounding rule.
- `scripts/build/v6_build.py:7100±` — derive INLINE_MIN = INLINE_MAX from injection
  marker count, no hardcoded cap.
- `curriculum/l2-uk-en/plans/a1/sounds-letters-and-hello.yaml` — bump version,
  add 33 letters + key_words to `vocabulary_hints.recommended`, backup as `.bak`.

**Verification**: diff assembled prompt — confirm conflicts gone. Re-run activity
generation phase only — no impossible-math errors, 100% required-vocab coverage.

**Brief location**: `/tmp/briefs/codex-unit3-activity-prompt-sweep.md`

### Unit 4 — Audit config min/max sweep (Claude, ~400 LOC)

**Files** (project-wide sweep):
- `scripts/audit/config.py` — every `*_MAX` key reviewed + renamed/re-semantic.
- `scripts/audit/*.py` — gates checking `*_MAX` converted to warnings.
- Plan schema — add `letter_module: true` flag for letter-driven exception class.
- `docs/best-practices/audit-standards.md` — codify philosophy.
- Tests in `tests/audit/` — accompany every change.

**Verification**: pytest passes; audit on existing passing modules introduces no
new failures.

**Brief location**: `/tmp/briefs/claude-unit4-audit-config-min-max.md`
**Depends on**: Unit 3 merged first (so dynamic INLINE_MIN/MAX is in place).

### Unit 5 — `exercise_quality` contract (Codex, ~80 LOC)

**Files**:
- Find `exercise_quality.py` (or equivalent) — change order-strict check to
  set-membership for activity_obligations.
- Update plan schema docs if needed.

**Verification**: a1/1 build past activity generation no longer triggers
plan_revision_request from exercise_quality for ordering alone.

**Brief location**: `/tmp/briefs/codex-unit5-exercise-quality-contract.md`

### Unit 6 — Verification orchestration (inline, no dispatch)

**USER OVERRIDE 2026-04-25**: User explicitly requested testing **gpt-5.5 as
writer + Claude as reviewer** (the flip from current default). Reasoning: user's
Ukrainian teachers reported good gpt-5.5 output; worth empirical validation.
My prior recommendation against this flip is **overridden**. Run BOTH variants
on a1/1 in head-to-head, then pick the winner for a1/2 + a1/3.

```bash
# === Phase A: a1/1 baseline (current setup) ===
# Establishes the post-fix baseline so we can compare apples-to-apples
.venv/bin/python scripts/build/v6_build.py a1 1 --force \
    --writer claude-tools --reviewer codex-tools

# Save the output:
cp curriculum/l2-uk-en/a1/sounds-letters-and-hello.md \
   /tmp/a1-1-baseline-claude-writer.md

# === Phase B: a1/1 experiment (gpt-5.5 writes, Claude reviews) ===
.venv/bin/python scripts/build/v6_build.py a1 1 --force \
    --writer codex-tools --reviewer claude-tools

# Save:
cp curriculum/l2-uk-en/a1/sounds-letters-and-hello.md \
   /tmp/a1-1-experiment-gpt5.5-writer.md

# === Compare ===
# - dim scores side-by-side
# - prose quality (manual eyeball; ideally show user both)
# - convergence rounds needed
# - any new failure modes

# === Phase C: a1/2 + a1/3 with the WINNER ===
# Whichever variant produced better empirical results on a1/1 wins for a1/2 + a1/3
.venv/bin/python scripts/build/v6_build.py a1 2 --force \
    --writer {WINNER_WRITER} --reviewer {WINNER_REVIEWER}  &
.venv/bin/python scripts/build/v6_build.py a1 3 --force \
    --writer {WINNER_WRITER} --reviewer {WINNER_REVIEWER}  &
wait
```

**Success criteria**:
- Phase A: a1/1 emits `module_done`, MIN dim ≥ 8, all gates GREEN, MDX renders with all 33 letter videos in workbook tab
- Phase B: same checks; comparison artifact written to `/tmp/a1-1-comparison.md` showing dim scores side-by-side and prose excerpts
- Phase C: a1/2 + a1/3 with the winning agent pair both pass

**Decision criteria for picking the winner** (in priority order):
1. Both pass `module_done` with MIN ≥ 8 → use whichever has higher MIN dim score
2. Only one passes → use that one for a1/2 + a1/3
3. Neither passes → STOP, escalate to user; we have a deeper problem
4. If MIN scores tie within ±0.3 → check convergence rounds (fewer is better)
5. If still tied → manual prose eyeball, show user both, let user pick

---

## What NOT to do (anti-checklist for next session)

1. **Do NOT rerun a1/1 builds before all 6 units land.** User explicit:
   "no rerunning until we fix all the problems."
2. **Do NOT manually patch content.** Manual fixes do not count. The pipeline
   must produce passing modules unaided.
3. **Do NOT propose menus.** "Want me to do A or B?" is not acceptable.
   Decide and act.
4. **Do NOT forget `--writer claude-tools --reviewer codex-tools`** explicit
   flags in every build invocation. Defaults silently flip; explicit flags
   prevent the experiment from being polluted.
5. **Do NOT spawn more than 2 Claude + 2 Codex in flight** (MEMORY cap).
6. **Do NOT touch `.worktrees/codex-interactive`** — user's local work.
7. **Do NOT guess at agent routing.** Writer = Claude, Reviewer = Codex,
   global. No per-dim routing exists in code.

## Critical context for fresh session start

- Read this handoff first.
- The 6-unit dispatch plan is the operational map.
- Dispatched briefs need to be WRITTEN before firing — see brief locations above.
- Use `.venv/bin/python scripts/delegate.py dispatch ...` per MEMORY pattern
  with worktrees at `.worktrees/dispatch/{agent}/{task-id}/`.
- Background-wait via `delegate.py wait` to get task-completion notifications.
- Watch CI via `gh pr checks {N} --watch --interval 15` in `run_in_background=True`.
- Merge per MEMORY #0H — required checks pass + advisory Gemini fail = merge with
  `--squash --delete-branch`, cleanup worktree, FF main.

## Open questions for user that may surface

1. After Unit 1 lands and Dialogue still doesn't recover above 8.0, escalate to:
   selective A/B (Dialogue → Claude only)? Or different approach?
2. The `letter_module: true` plan flag is new — should it auto-detect from
   plan content (e.g., if `vocabulary_hints` contains the alphabet) or be an
   explicit author flag?
3. After all 17 fixes land and a1/1 passes, do we proceed to a1/4...a1/55
   in batches, or do dim-level QA on the first 3 first?

---

## End-of-session state checklist

- [ ] Working tree: a1/1 manual patches still in place — DO NOT clobber until
      all 6 units merged. After Unit 6 passes, the working tree changes can be
      reverted (`git checkout -- curriculum/l2-uk-en/a1/sounds-letters-and-hello.md`)
      because the rebuild produced the canonical content.
- [ ] All 6 brief files at `/tmp/briefs/*.md` need to be WRITTEN by the next
      session before dispatching.
- [ ] No active dispatches at handoff time (this session ran convergence + 4
      tech-debt PRs to completion, all merged, no in-flight tasks).

**End handoff.**
