# Рецензія: My Daily Routine

**Level:** A1 | **Module:** 38
**Overall Score:** 7.4/10
**Status:** FAIL
**Reviewed:** 2026-03-19
**Reviewed-By:** claude-sonnet-4-6

## Plan Verification

```
Plan-Content Alignment: PARTIAL FAIL
- Sections: 4/4 present (PASS)
- Vocabulary: 20/20 vocab items present; all required words in prose (PASS)
- Grammar scope: PASS — reflexive verbs, -ся/-сь, sequence adverbs all within A1.4 scope
- Objectives: 4/4 addressed (PASS)
- Activity item counts: FAIL (see below)
```

### Plan Adherence Checklist (content_outline.points)

**Section "Вступ (Introduction)":**
- "Introducing typical daily activities and the conceptual split between робочий день and вихідний день" — COVERED. Line 7: both concepts defined with translations.
- "Discussing the start and end of activities (початок і кінець дня) using chronological markers" — COVERED. Line 9-11: початок і кінець дня introduced, щодня marker presented.

**Section "Презентація (Presentation)":**
- "Reflexive verbs: прокидатися and вмиватися; learner error: вмиватися vs мити руки" — COVERED. Lines 28-34: explicit washing rule with contrastive pair 「Я мию руки.」 vs 「Я вмиваюся.」
- "Morphological focus: Conjugation of Class II дивитися; -ся/-сь rule" — COVERED. Lines 36-44: full paradigm with explicit vowel/consonant rule.
- "Cultural Hook: Ukrainian Обід as main meal" — COVERED. Lines 50-51: `[!cultural-note]` block with detail about two courses and обідня перерва.

**Section "Практика (Practice)":**
- "Daily commute: їхати vs йти" — COVERED. Lines 57-61: 「Я йду на роботу.」 vs 「Я їду на роботу.」
- "Time and Case correction: о + Locative vs в + Accusative error" — COVERED. Lines 63-67: explicit error correction with correct pattern 「о сьомій годині」.
- "Frequency and Sequence adverbs: зазвичай, спочатку, потім, після цього" — COVERED. Lines 69-75: all four markers used in integrated sequence.

**Section "Продукування та Підсумок (Production and Summary)":**
- "Evening transitions and домашній одяг cultural hook" — COVERED. Lines 90-92: detailed cultural explanation about public/private separation.
- "Synthesis Task: contrasting working day with day off" — COVERED. Lines 103-112: self-check questions guide production.

### Activity Hint Adherence
- quiz (20 items, "Order daily activities"): **PARTIAL** — only 8 items provided (plan: 20)
- fill-in (20 items, "Complete routine descriptions"): **PARTIAL** — only 8 items provided (plan: 20)
- match-up (15 items, "Match activities to times"): **PARTIAL** — only 8 pairs provided (plan: 15)
- fill-in (6 items, "Describe your typical day"): **COVERED** — 6 items provided

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 7/10 | <7 | No learning objectives preview ("Today you'll learn..."), no explicit encouragement callouts, ending is warm but lacks "You can now..." celebration. Only 1 callout box in entire module. |
| 2 | Language | 8/10 | <8 | All Ukrainian sentences grammatically correct and verified. One callout type mismatch (`[!cultural-note]` vs standard `[!culture-note]`). English prose slightly verbose/formal in places. |
| 3 | Pedagogy | 8/10 | <7 | Strong PPP structure. Reflexive verb explanation with contrastive pairs is excellent. Missing the proverb "Хто рано встає, тому Бог дає" from research, which would have been a great cultural anchor. Sequence of washing rule → conjugation → meals → commute → time is logical. |
| 4 | Activities | 6/10 | <7 | **AUTO-FAIL.** Only 30/61 planned items delivered. Quiz has 8/20, fill-in #1 has 8/20, match-up has 8/15. Quiz items Q2 ("correct order") and Q4 ("which meal is main") test content recall, not language. Activity explanation on line 163 contains non-word "вмиваєть" (morphological breakdown that VESUM flags). |
| 5 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 4/5 — see below. Good pacing with concepts introduced gradually. Missing quick wins in first section (300+ words before any practice). |
| 6 | LLM Fingerprint | 7/10 | <7 | Structural monotony: Sections "Вступ", "Презентація", and "Практика" all open with a declarative English sentence about what "we" will learn. Line 22 and 86 both use "building blocks"/"storytelling" framing. Example blocks in "Практика" and "Продукування та Підсумок" use identical bullet-list format. |
| 7 | Linguistic Accuracy | 9/10 | <9 | All conjugation forms verified against VESUM. The -ся/-сь rule correctly explained. о + Locative time pattern correct. Minor: "вмиваєть+ся" breakdown in activity explanation is pedagogically fine but scanner-unfriendly. |

**Weighted Overall:**
```
(7×1.5 + 8×1.1 + 8×1.2 + 6×1.3 + 8×1.3 + 7×1.0 + 9×1.5) / 8.9
= (10.5 + 8.8 + 9.6 + 7.8 + 10.4 + 7.0 + 13.5) / 8.9
= 67.6 / 8.9
= 7.6/10
```

## Auto-Fail Checklist Results

- Russianisms: **CLEAN** — no давайте calques, no кушати, no піднімається, no получати
- Calques: **CLEAN** — no "робити сенс" or similar
- Colonial framing: **CLEAN** — no "unlike Russian..." comparisons
- Grammar scope: **CLEAN** — stays within reflexive verbs, present tense, no imperative, no perfective
- Activity errors: **FAIL** — item counts severely under plan; Q2 and Q4 test content recall not language; "вмиваєть" flag
- Beginner safety: 4/5
- Factual accuracy: **CLEAN** — обід cultural claim is accurate; домашній одяг tradition is well-known

## Critical Issues Found

### Issue 1: Activities — Severely Under Plan Item Counts (HIGH)
- **Location**: Activities file, all activity blocks
- **Problem**: Plan specifies quiz=20, fill-in=20, match-up=15, fill-in=6 (total 61 items). Actual delivery: quiz=8, fill-in=8, match-up=8, fill-in=6 (total 30 items). This is only 49% of planned activities.
- **Fix**: Content rebuild needed for activities. Cannot be patched with FIND/REPLACE — requires generating 31 additional activity items.

### Issue 2: Zero Engagement Boxes (HIGH)
- **Location**: Entire content file
- **Problem**: Audit reports 0 engagement boxes. The single callout on line 50 uses `[!cultural-note]` which is not a standard engagement box type (should be `[!culture-note]`). Richness gap shows `engagement: 0/2`. Module needs at least 2 engagement boxes.
- **Fix**: Change `[!cultural-note]` to `[!culture-note]` and add at least one more engagement callout (e.g., `[!did-you-know]` about the proverb "Хто рано встає, тому Бог дає" in section "Вступ (Introduction)", or a `[!tip]` about the -ся/-сь mnemonic in section "Презентація (Presentation)").

### Issue 3: Immersion Below Target (MEDIUM)
- **Location**: Entire content file
- **Problem**: Immersion at 13.9%, but Module 38 is in the "Modules 21+" band requiring 30-55% Ukrainian. The content is overwhelmingly English prose with Ukrainian examples interspersed. Ukrainian text appears almost exclusively in bold example sentences.
- **Fix**: Add Ukrainian reading practice blocks after each section. Convert some English explanations to Ukrainian with parenthetical translations. Add Ukrainian mini-dialogues.

### Issue 4: Activities Test Content Not Language (MEDIUM)
- **Location**: Activities file, lines 16-26 (Q2) and lines 38-48 (Q4)
- **Problem**: Q2 ("What is the correct order for these morning activities?") tests content recall of a morning sequence, not language skill. Q4 ("Which Ukrainian meal is traditionally the main, most substantial meal of the day?") tests cultural knowledge, not Ukrainian language. Per Rule 10a: "Can the learner answer without reading the Ukrainian text? If YES → rewrite."
- **Fix**: Rewrite Q2 to test sequencing adverb usage (e.g., "Which word means 'then' in a sequence?"). Rewrite Q4 to test vocabulary in context (e.g., "Complete: О першій годині я ___.").

### Issue 5: Missing Learning Objectives Preview (MEDIUM)
- **Location**: Section "Вступ (Introduction)", lines 3-22
- **Problem**: No explicit "Today you'll learn to..." preview. The intro jumps into content about daily routine concepts. Beginner modules need clear expectation-setting.
- **Fix**: Add a brief learning objectives block after line 5, e.g., "In this lesson, you'll learn to: conjugate reflexive verbs, describe your morning and evening routine, use sequence words (спочатку, потім, нарешті), and tell time with о + Locative case."

### Issue 6: Activity Explanation Contains Non-Word (LOW)
- **Location**: Activities file, line 163
- **Problem**: Explanation text "вмиваєть+ся" contains the token "вмиваєть" which is not a real Ukrainian word form (VESUM confirms NOT FOUND). While pedagogically this is showing a morpheme boundary, the scanner flags it.
- **Fix**: Rewrite explanation to avoid the broken token: "Вона вмивається — the він/вона/воно form ends in -ться (consonant cluster), so the reflexive particle is -ся."

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Act:163 | 「вмиваєть+ся」 | "вмивається — the -ться ending uses -ся after consonant" | Non-word form |

No Russianisms, calques, or grammar scope violations found. All Ukrainian verb forms verified against VESUM. The -ся/-сь conjugation paradigm for дивитися is correct (colloquial register forms дивлюсь, дивимось, дивитесь confirmed in VESUM alongside standard forms дивлюся, дивимося, дивитеся).

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? **Pass** — concepts introduced gradually, one at a time. Clear structure.
- Instructions clear? **Pass** — each section has a clear focus. The washing rule (line 30-33) is excellently explained.
- Quick wins? **Fail** — first 300+ words (entire Вступ section) contain no practice opportunity. The first interactive moment is the dialogue on lines 17-20, but this is read-only, not practice.
- Ukrainian scary? **Pass** — Ukrainian introduced gently in bold with translations. The 「Я щодня працюю.」 examples are simple and manageable.
- Come back tomorrow? **Pass** — the synthesis task (lines 103-112) gives agency. The cultural hooks (обід, домашній одяг) are relatable and interesting.

## Strengths

- **Excellent contrastive pairs**: The washing rule (「Я мию руки.」 vs 「Я вмиваюся.」) and motion verbs (「Я йду на роботу.」 vs 「Я їду на роботу.」) are pedagogically sound and clearly presented.
- **Strong cultural hooks**: The обід as main meal and домашній одяг tradition are authentic, well-explained, and memorable.
- **Correct and complete conjugation paradigm**: The дивитися table (lines 38-44) correctly demonstrates the -ся/-сь vowel/consonant rule with all 6 persons, all verified in VESUM.
- **Logical PPP progression**: Section "Вступ (Introduction)" sets context → "Презентація (Presentation)" teaches forms → "Практика (Practice)" drills application → "Продукування та Підсумок (Production and Summary)" synthesizes.
- **Integrated dialogues**: The dialogues on lines 17-20 and 79-84 show natural conversational use of the target structures.

## Fix Plan to Reach 9/10 (REQUIRED — score is 7.6)

### Activities: 6/10 → 8/10
**What to fix:**
1. **Rebuild activities** with full item counts: quiz=20, fill-in=20, match-up=15, fill-in=6. This requires a pipeline rebuild (`--restart-from activities`), not manual patching.
2. Rewrite Q2 and Q4 to test language skills, not content recall.
3. Fix line 163 explanation to avoid "вмиваєть" token.

**Expected score after fix:** 8/10

### Experience Quality: 7/10 → 9/10
**What to fix:**
1. Add learning objectives preview after line 5 in section "Вступ (Introduction)".
2. Fix callout type: `[!cultural-note]` → `[!culture-note]` on line 50.
3. Add at least 1 more engagement callout — suggest `[!did-you-know]` with the proverb "Хто рано встає, тому Бог дає" in section "Вступ (Introduction)".
4. Add a "You can now..." celebration block in section "Продукування та Підсумок (Production and Summary)" before the final sentence.

**Expected score after fix:** 9/10

### LLM Fingerprint: 7/10 → 8/10
**What to fix:**
1. Vary section openings — currently 3 sections start with declarative English "we" statements.
2. Mix example formats — add a table for the дивитися conjugation instead of bullet list, use inline examples in some places.

**Expected score after fix:** 8/10

### Immersion: 13.9% → 25%+ (supports Experience and Language scores)
**What to fix:**
1. Add Ukrainian reading practice blocks (5-8 sentences) after sections "Презентація (Presentation)" and "Практика (Practice)".
2. Convert some English framing sentences to Ukrainian with translations.
3. Add the proverb "Хто рано встає, тому Бог дає" as an authentic Ukrainian text element.

**Expected impact:** Immersion should rise to ~25-30%, closer to the 30% minimum.

### Projected Overall After Fixes
```
(9×1.5 + 8×1.1 + 8×1.2 + 8×1.3 + 8×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 8.8 + 9.6 + 10.4 + 10.4 + 8.0 + 13.5) / 8.9
= 74.2 / 8.9
= 8.3/10
```

Note: Reaching 9.0 overall requires activity rebuild (pipeline) + immersion expansion, which are substantial content changes best handled by a pipeline rebuild (`--restart-from content`).

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (not applicable — A1 core track)
- Dates checked: N/A (no historical dates in module)
- Named figures verified: N/A
- Primary quotes cross-referenced: N/A
- Chronological sequence: CONSISTENT
- Claims without research grounding: 0
- Cultural claims verified: обід as main meal (confirmed in research notes line 25), домашній одяг tradition (confirmed in research notes line 26)

## Verification Summary

- Content lines read: 113
- Activity items checked: 30
- Ukrainian sentences verified: 25+ (all example sentences, conjugation forms, dialogue lines)
- Citations in bank: 18
- Issues found: 6

## Verdict

**FAIL**

Blocking issues: (1) Activity item counts at 49% of plan targets — requires activity rebuild. (2) Zero recognized engagement boxes — callout type mismatch + need additional boxes. (3) Immersion at 13.9% is critically below the 30% minimum for Module 38. Issues 2 and 3 can be fixed with FIND/REPLACE; issue 1 requires a pipeline rebuild. The content itself is linguistically solid — all Ukrainian is correct, the pedagogy is well-structured, and the cultural hooks are authentic. The failures are quantitative (not enough activities, not enough engagement boxes, not enough Ukrainian immersion), not qualitative.