# Prompt & Context Engineering Review: checkpoint-first-contact

**Track:** a1 | **Sequence:** 7
**Pipeline:** v6
**Review rounds:** 2 (R1 score: 73/100 → R2 score: 95/100)
**Friction reports:** 1 (resolved — V6 rebuild)
**Build phases:** all 14 complete (check → publish)
**Build date:** 2026-03-29

---

## Context Engineering Analysis

### Instruction → Understanding → Output Gap

| Instruction (from prompt) | What Gemini produced | Gap type | Evidence |
|--------------------------|---------------------|----------|----------|
| "Place `<!-- INJECT_ACTIVITY: {id} -->` markers... Spread markers evenly throughout the module — never cluster them" | 1 marker after Читання, 3 clustered at end of Діалог | instruction_ignored | `quiz-sounds-vs-letters` placed after Читання (OK), but `fill-in-self-intro`, `match-questions-answers`, `quiz-comprehensive-review` all clustered at lines 194-198 of the review prompt content |
| Plan `activity_hints` has 3 IDs (quiz, fill-in, match-up) with no `id` field — writer must infer | Writer invented `quiz-sounds-vs-letters` (not in plan) plus 3 others | context_gap | Plan's `activity_hints` lack explicit `id` fields. Skeleton invented IDs. Writer followed skeleton faithfully but the skeleton introduced a phantom ID. |
| "EVERY plan point MUST appear in your output... showing photos" | Dialogue omits the "showing photos" interaction from plan | instruction_ignored | Plan says "greeting → name → origin → profession → family → showing photos → goodbye". Output covers all except "showing photos". R2 review caught this (9/10 plan adherence). |
| Skeleton says `лікАрка` (stress on 1st syllable) | R1 content had wrong stress; R2 fixed to "second syllable" | fix_applied | R1 review: "stress rules for руки are taught completely backwards... лікарка is incorrectly stated". R2 review: "Stress explanations (лікарка, інженер) are phonetically accurate." Fix was applied between rounds. |
| "10-20% Ukrainian" immersion target | Content is appropriately English-dominant with inline bolded Ukrainian | compliant | Module reads naturally as an English-language checkpoint with Ukrainian examples. No immersion violation. |
| "NO IPA, NO Latin transliteration" | No IPA or transliteration found | compliant | Clean. |
| "Section Structure... `## Підсумок — Summary` (~150 words)" appears TWICE in prompt | Writer produced one summary section (correct) | non_issue | Duplicated heading in prompt template (line 703-704 of v6-prompt.md) didn't cause confusion, but is a template bug. |

### R1 → R2 Fix Effectiveness

R1 found critical linguistic errors (stress explanations wrong for руки, сестра, лікарка — score 4/10 on linguistic accuracy). After fix round, R2 scored 10/10 on linguistic accuracy. The reviewer-as-fixer pattern worked correctly here.

### Exercise Marker Placement Analysis

The prompt says "Spread markers evenly" but the skeleton contradicts this by placing all 3 plan-aligned exercises at the end of the Діалог section. The writer faithfully followed the skeleton, which means the **root cause is in the skeleton, not the writer**.

The activities prompt then inherited 4 markers (including the phantom `quiz-sounds-vs-letters`), creating a mismatch between plan (3 activity hints) and markers (4).

---

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Duplicate `## Підсумок — Summary` heading | LOW | v6-prompt.md | Lines 703-704 list the same section heading twice. Writer handled it correctly, but this is a copy-paste bug in the template. |
| `activity_hints` lack `id` fields | HIGH | Plan schema / skeleton prompt | Plan's activity_hints don't have explicit `id` fields. The skeleton prompt invented IDs. The writing prompt says "Use the EXACT `id` from the plan's `activity_hints`" — but there ARE no IDs in the plan. This forces the skeleton/writer to invent IDs, creating mismatches. |
| Skeleton overrides pacing plan instruction | MEDIUM | v6-prompt.md | Prompt says "Output a `<pacing_plan>` block" in Step 1, then later says "The skeleton replaces Step 1 — do NOT output a pacing_plan block." This is clear enough, but the contradicting instruction adds noise. Consider removing Step 1 entirely when a skeleton is present. |
| Exercise spread instruction vs skeleton placement | HIGH | v6-skeleton-prompt.md | Skeleton prompt says "Spread exercises evenly" but then places all 3 plan exercises clustered at end of Діалог. The skeleton is the immediate authority the writer follows, so the "spread evenly" instruction in v6-prompt.md is overridden. |

---

## Context Gaps

| Missing Context | Impact | Fix |
|----------------|--------|-----|
| Plan `activity_hints` have no `id` field | Skeleton invents IDs → activities prompt inherits phantom/mismatched IDs → exercise verification shows 0 items tested | Pipeline should auto-generate deterministic IDs from activity_hints (e.g., `{type}-{focus-slug}`) and inject them into both skeleton and writing prompts |
| No "showing photos" guidance in knowledge packet | Writer had no textbook excerpt for how to integrate photo-sharing into a dialogue | Add a pre-verify search for "показати фото / фотографія" to find textbook patterns. Or: remove "showing photos" from the plan if it's not pedagogically grounded. |
| Exercise verification reports 0 items | `exercise-verification.json` shows `total_items: 0`, suggesting the verification step ran before activities were generated or couldn't parse them | Pipeline sequencing issue — verify-exercises should run AFTER activities are generated and parsed |

---

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|---------------|-----------------|---------|-------------|
| "V6 build failed after 3 attempts" (original friction) | resolved | Module was rebuilt successfully on 2026-03-29. Friction marked resolved. | N/A — already resolved |
| R1 linguistic accuracy score 4/10 | template_gap | Skeleton specified wrong stress for `руки` and `лікарка`. The skeleton prompt doesn't verify stress claims against VESUM/goroh. | Add a friction or instruction to skeleton prompt: "Do NOT specify stress patterns in the skeleton. Leave stress for the pre-verify step and the deterministic annotator." |
| "Showing photos" plan point missed | context_gap | No textbook reference for photo-sharing in knowledge packet. Writer had no grounding. | Either add to pre-verify search terms or update plan to remove ungrounded point. |

---

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|-------------|
| write | 1 | Clean first pass (skeleton-guided) | N/A |
| activities | 2 | First attempt likely had issues (two dispatch logs) | YES — clearer marker-to-activity mapping would prevent rework |
| review | 2 | R1 found critical stress errors; R2 passed | YES — if skeleton didn't specify wrong stress, R1 would have been cleaner |

---

## Suggested Template Fixes

### Fix 1: Auto-generate activity IDs from plan hints (Priority: HIGH)
**Prevents:** Phantom activity IDs, marker-plan mismatches, cascading exercise verification failures
**Scope:** All modules (all tracks)
**Template file:** Pipeline code (`v6_build.py` — skeleton + write step)

The plan's `activity_hints` should get auto-generated deterministic IDs before being injected into any prompt. Format: `{type}-{slugified-focus}`. Example:
```yaml
# From:
- type: quiz
  focus: "Comprehensive review: sounds, letters, greetings, family"
# To:
- id: quiz-comprehensive-review
  type: quiz
  focus: "Comprehensive review: sounds, letters, greetings, family"
```

These IDs would then be the source of truth for both skeleton and writing prompts, eliminating the current gap where the skeleton invents IDs.

### Fix 2: Remove stress claims from skeleton (Priority: HIGH)
**Prevents:** Wrong stress being baked into the skeleton → writer → content → failed R1 review
**Scope:** All modules
**Template file:** v6-skeleton-prompt.md

```diff
- Be SPECIFIC about what each paragraph covers — not "explain grammar" but "explain accusative case endings for feminine nouns (-у/-ю), with 3 examples: книгу, каву, землю."
+ Be SPECIFIC about what each paragraph covers — not "explain grammar" but "explain accusative case endings for feminine nouns (-у/-ю), with 3 examples: книгу, каву, землю."
+ Do NOT specify stress positions for Ukrainian words (e.g., "stress on first syllable"). Stress verification is handled by a deterministic tool. If you mention stress as a teaching topic, say WHAT to teach (e.g., "highlight that stress changes meaning in руки") but not WHERE the stress falls.
```

### Fix 3: Fix duplicate Підсумок heading in v6-prompt.md (Priority: LOW)
**Prevents:** Potential confusion in future builds where writer might produce two summary sections
**Scope:** All modules using v6-prompt.md
**Template file:** v6-prompt.md (Section Structure block)

```diff
  - `## Діалог (Capstone Dialogue)` (~400 words)
  - `## Підсумок — Summary` (~150 words)
- - `## Підсумок — Summary` (~150 words)
```

### Fix 4: Remove Step 1 pacing plan when skeleton present (Priority: LOW)
**Prevents:** Contradictory instructions (write pacing plan vs. don't write pacing plan)
**Scope:** All modules with skeleton
**Template file:** v6-prompt.md

When the skeleton block is present, the pipeline should strip the "Step 1: Pacing Plan" section from the prompt entirely, rather than including it and then contradicting it later. This reduces prompt noise.

### Fix 5: Enforce exercise spread in skeleton prompt (Priority: MEDIUM)
**Prevents:** Exercise clustering at end of module
**Scope:** All modules
**Template file:** v6-skeleton-prompt.md

```diff
  4. **Spread exercises evenly.** Place one after each key teaching point, matching the plan's `activity_hints`.
+ **CRITICAL: NEVER cluster all exercises at the end of a section or at the end of the module.** Each exercise must appear immediately after the paragraph that teaches the concept it tests. If the plan has 3 exercises, they should appear in 3 different sections, not consecutively.
```

---

## Summary

**Template health:** NEEDS WORK — the content output is good quality (R2 passed with high scores), but the prompt/skeleton pipeline has structural issues that caused an unnecessary R1 failure and exercise verification gaps.

**Top 3 fixes by leverage:**
1. **Auto-generate activity IDs from plan hints** — affects ALL modules, prevents the entire category of phantom-ID / marker-mismatch bugs
2. **Remove stress claims from skeleton** — prevents wrong-stress cascading into content → failed R1 → wasted review round (affects all modules with phonetics/stress content)
3. **Enforce exercise spread in skeleton** — prevents exercise clustering, which both R1 and R2 flagged (exercise quality scored 6/10 and 7/10 respectively)
