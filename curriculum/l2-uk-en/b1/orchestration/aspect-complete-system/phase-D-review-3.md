**Reviewed-By:** claude-opus-4-6

# Рецензія: Вид дієслова: повна система

**Level:** B1 | **Module:** b1-06
**Overall Score:** 8.9/10
**Status:** FAIL (Linguistic Accuracy 8/10 triggers auto-fail at <9)
**Reviewed:** 2026-02-23
**D.3 Re-Review:** Repair Cycle 2

## D.1 Fix Verification

| D.1 Issue | Status | Evidence |
|-----------|--------|----------|
| Issue 1: IPA stress error — маркер | **NOT FIXED** | Vocabulary line 57: `ipa: '[mɑrkɛr]'` — still no stress mark. Standard: ма́ркер → `` |
| Issue 2: IPA stress error — завершувати | **NOT FIXED** | Vocabulary line 66: `ipa: ''` — stress still on 2nd syllable. Standard: завершува́ти → `` |
| Issue 3: IPA stress error — досягти | **NOT FIXED** | Vocabulary line 81: `ipa: ''` — stress still misplaced. Standard: досягти́ → `` |
| Issue 4 (from D.1 cycle 1): Ingressive по- misplacement | **STILL FIXED** | Correctly placed at line 136 within Section «Граматична Система: Форми та Функції» |
| Issue 5 (from D.1 cycle 1): Wrong callout type [!biography] | **STILL FIXED** | Changed to `[!context]` — confirmed at lines 148, 293 |

**Regression check:** No regressions from D.2 cycle 2 fixes detected. The fixes from cycle 1 (ingressive placement, callout type) remain intact. However, the 3 critical IPA stress errors that caused the original auto-fail remain **completely unfixed after two repair cycles**. Additionally, I found a **4th IPA stress error** (завершення, line 25) that was not flagged in previous reviews.

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: All 5 H2 sections present ✓ (Розминка та Контекст, Граматична Система: Форми та Функції, Глибинна Семантика: Процес та Результат, Аналіз Помилок та Тонкощі, Практика та Мовленнєві Ситуації)
- Vocabulary: 9/9 required + 5/5 recommended from plan, 16 extra (30 total) ✓
- Grammar scope: CLEAN — no scope creep beyond plan ✓
- Objectives: All 3 objectives addressed ✓
  - "Learner understands the complete aspectual system" → Sections «Розминка та Контекст» and «Граматична Система: Форми та Функції» ✓
  - "Learner can identify aspect from context clues" → Section «Глибинна Семантика: Процес та Результат» + marker table in Section «Практика та Мовленнєві Ситуації» ✓
  - "Learner can choose appropriate aspect for different situations" → Section «Практика та Мовленнєві Ситуації» algorithm + activities ✓
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Compelling Parajanov hook (line 17), diagnostic task пекла/спекла (lines 24-32) is an excellent TTT opener. Video/Photo mode metaphor (lines 34-36) is memorable and practical. "Did I Learn?" 5/5. |
| 2 | Coherence | 9/10 | <7 | Logical flow across all 5 H2 sections. Section «Розминка та Контекст» builds intuition → Section «Граматична Система: Форми та Функції» formalizes → Section «Глибинна Семантика: Процес та Результат» deepens → Section «Аналіз Помилок та Тонкощі» anticipates mistakes → Section «Практика та Мовленнєві Ситуації» applies. Ingressive по- correctly placed within grammar section (line 136). |
| 3 | Relevance | 9/10 | <7 | Directly addresses all B1 aspect learning objectives. Cultural hooks (Parajanov, Shevchenko, proverbs) are pedagogically purposeful, not decorative. IT stand-up example (line 294) is relevant to modern Ukrainian professional context. |
| 4 | Educational | 8/10 | <7 | Strong TTT structure with diagnostic task before rules. However: within Section «Граматична Система: Форми та Функції», after the inline exercise at lines 93-104, lines 106-139 (~700 words) introduce 3 new sub-concepts (synthetic future etymology, ДВ simple future, ingressive по-) with no inline practice. The comparative table (lines 125-132) helps but is passive. The ДВ simple future and ingressive по- concepts lack inline exercises — practice exists only in the activities file. |
| 5 | Language | 9/10 | <8 | Natural Ukrainian throughout. No Russianisms in prose. Minor: line 187 uses «Це союз, створений для опису процесів» where "союз" (conjunction/alliance) is ambiguous in a grammar module — a student might confuse it with the grammatical term "conjunction." Better: «Це поєднання» or «Це тандем». |
| 6 | Pedagogy | 9/10 | <7 | Excellent TTT: diagnostic task (line 24) before rules, discovery before explanation. Practice well-integrated in Sections «Розминка та Контекст», «Глибинна Семантика: Процес та Результат», and «Аналіз Помилок та Тонкощі» with inline exercises. 4-question algorithm (lines 251-263) is a strong takeaway tool. |
| 7 | Immersion | 10/10 | <6 | 99.5% Ukrainian immersion (audit: 99.5%). B1.1 target is 70-85%; this exceeds comfortably. Minimal English confined to conceptual labels (Video/Photo mode, line 35) and brief structural comparisons (will + verb, line 77). |
| 8 | Activities | 9/10 | <7 | 11 activities with excellent type variety (quiz ×1, match-up ×2, fill-in ×3, error-correction ×1, unjumble ×1, cloze ×1, mark-the-words ×1, true-false ×1). 670 lines. All answers verified correct. Distractors target real learner errors (e.g., "доказував"/"доказав" as Russicism distractors in fill-in items 1-2 of "Спроба проти успіху"; "рішав" as non-standard distractor at line 515). |
| 9 | Richness | 9/10 | <6 | 99% richness (audit confirmed). Parajanov, Shevchenko, proverbs, IT stand-ups, office dialogue, folk tales, Lesya Ukrainka. Tables (line 125), dialogues (lines 24-29, 246-248, 286-289), varied callouts (17 total, 10+ distinct types). 14 engagement boxes. |
| 10 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5. Clear guided discovery, warm teacher voice, practical algorithm, ample practice in activities file. Progressive difficulty from intuitive choice to formal rules to error analysis. |
| 11 | LLM Fingerprint | 9/10 | <7 | No "це не просто" patterns (Grep confirmed: 0 matches). Varied section openings: «Вибір між...» (line 17), «Згідно з нормами...» (line 44), «Однією з найскладніших...» (line 144), «Під час вивчення...» (line 185), «Коли ви розповідаєте...» (line 240) — all different. Varied example formats (dialogue, table, narrative, bullets, proverbs). No structural monotony. 17 callouts across 10+ distinct types, no title repetition. |
| 12 | Linguistic Accuracy | 8/10 | <9 | **AUTO-FAIL.** Grammar rules in content are accurate. BUT: **4 IPA stress errors** in vocabulary file (3 previously flagged + 1 newly discovered). See Critical Issues. This is the 2nd consecutive repair cycle failing to fix these errors. |
| 13 | Factual Accuracy | 9/10 | <8 | Core grammar track. Parajanov «Тіні забутих предків» 1964 ✓. Synthetic future etymology from «імати» correct (line 85) ✓. Proverbs accurate ✓. «Лісова пісня» reference (line 235) properly hedged with «можна уявити, як» ✓. State Standard §4.2.3.1 reference valid ✓. |

**Weighted Overall:**
```
(9×1.5 + 9×1.0 + 9×1.0 + 8×1.2 + 9×1.1 + 9×1.2 + 10×1.0 + 9×1.3 + 9×0.9 + 9×1.3 + 9×1.0 + 8×1.5 + 9×1.5) / 15.5
= (13.5 + 9.0 + 9.0 + 9.6 + 9.9 + 10.8 + 10.0 + 11.7 + 8.1 + 11.7 + 9.0 + 12.0 + 13.5) / 15.5
= 137.8 / 15.5
= 8.89/10
```

## Auto-Fail Checklist Results

- Russianisms: [CLEAN] — no Russianisms in content prose. Activity distractors "доказував"/"доказав" and "рішав" are intentionally included as wrong answers.
- Calques: [CLEAN]
- Colonial framing: [CLEAN] — no Russian comparisons. Ukrainian aspect presented on its own terms. English comparison (line 77) is pedagogically legitimate.
- Grammar scope: [CLEAN] — all content within plan scope, no scope creep.
- Activity errors: [CLEAN] — all answers verified correct across 11 activities.
- Word salad: [CLEAN] — paragraphs coherent with clear logical threads throughout.
- Beginner safety: 5/5
- Factual accuracy: [CLEAN] — grammar rules accurate, cultural references verified.
- LLM fingerprint: [CLEAN] — varied openings, no clichés, no structural monotony.

## Critical Issues Found

### Issue 1: IPA Stress Error — маркер (UNFIXED — 2nd repair cycle)
- **Location**: Vocabulary file, line 57
- **Original**: `ipa: '[mɑrkɛr]'`
- **Problem**: No stress mark present. Standard Ukrainian: ма́ркер (stress on 1st syllable).
- **Fix**: Change IPA to `''`

### Issue 2: IPA Stress Error — завершувати (UNFIXED — 2nd repair cycle)
- **Location**: Vocabulary file, line 66
- **Original**: `ipa: ''`
- **Problem**: Stress placed on 2nd syllable (ʋɛr). Standard Ukrainian: завершува́ти (stress on 4th syllable, ва).
- **Fix**: Change IPA to `''`

### Issue 3: IPA Stress Error — досягти (UNFIXED — 2nd repair cycle)
- **Location**: Vocabulary file, line 81
- **Original**: `ipa: ''`
- **Problem**: Stress mark placed before ɦ (on 2nd syllable boundary). Standard Ukrainian: досягти́ (stress on final syllable).
- **Fix**: Change IPA to `''`

### Issue 4: IPA Stress Error — завершення (NEW — not previously flagged)
- **Location**: Vocabulary file, line 25
- **Original**: `ipa: ''`
- **Problem**: Stress placed on 2nd syllable (ʋɛr). Standard Ukrainian: заверше́ння (stress on 3rd syllable, шен).
- **Fix**: Change IPA to `''`

### Issue 5: Ambiguous terminology in grammar module
- **Location**: Content file, line 187, Section «Аналіз Помилок та Тонкощі»
- **Original**: «Це союз, створений для опису процесів.»
- **Problem**: The word "союз" (conjunction/union/alliance) is a grammatical term that means "conjunction" in Ukrainian grammar. Using it metaphorically to mean "partnership" in a grammar-focused module may confuse B1 learners who will encounter "союз" as a technical term in later modules.
- **Fix**: Replace «Це союз» with «Це поєднання» — unambiguous and natural.

### Issue 6: Practice gap in Section «Граматична Система: Форми та Функції»
- **Location**: Content file, lines 106-139
- **Problem**: After the inline exercise at lines 93-104, approximately 700 words introduce 3 new sub-concepts (synthetic future etymology, ДВ simple future form, ingressive по-) without any inline practice. The comparative table (lines 125-132) is a passive reference. The ДВ simple future and ingressive по- have practice only in the separate activities file, not integrated into the content flow.
- **Fix**: Add one [!exercise] block after line 115 asking learners to conjugate a ДВ verb in simple future tense (e.g., "Утворіть просту форму майбутнього часу для дієслів: зробити, написати, прочитати").

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Vocab 25 | «» | «» | IPA stress |
| Vocab 57 | «[mɑrkɛr]» | «» | IPA stress |
| Vocab 66 | «» | «» | IPA stress |
| Vocab 81 | «» | «» | IPA stress |
| 187 | «Це союз, створений для опису процесів.» | «Це поєднання, створене для опису процесів.» | Ambiguous terminology |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? Pass — progressive difficulty, digestible chunks, Video/Photo mode simplifies abstract concept
- Instructions clear? Pass — every concept explained with concrete examples before generalization
- Quick wins? Pass — diagnostic task at lines 24-32 gives immediate sense of competence
- Ukrainian scary? Pass — warm teacher voice, encouraging callouts, step-by-step algorithm
- Come back tomorrow? Pass — compelling cultural hooks, practical IT/office examples, clear "what's next" in summary

## Strengths

- **Diagnostic task (lines 24-32)**: The пекла/спекла dialogue is an outstanding TTT opener — naturalistic, emotionally engaging, and perfectly demonstrates the aspect contrast before any rules are stated.
- **Video/Photo mode metaphor (lines 34-36)**: Memorable, practical, and consistently referenced throughout the module. Creates a cognitive anchor learners can carry into real conversations.
- **4-question algorithm (lines 251-263)**: Transforms abstract grammar into a practical decision tree. The "95% of situations" claim gives learners confidence.
- **Activity design**: The cloze "Історія одного дня" (activity 6) is particularly well-crafted — it integrates all aspect functions into a single coherent narrative, requiring aspect switching based on context.
- **Cultural integration**: Parajanov → Video/Photo → proverbs → Shevchenko → IT stand-ups form a rich cultural tapestry that never feels forced.

## Fix Plan to Reach 9.0/10 (REQUIRED — score < 9.0)

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Vocabulary line 25: Change `ipa: ''` → `ipa: ''` — stress on correct syllable (заверше́ння)
2. Vocabulary line 57: Change `ipa: '[mɑrkɛr]'` → `ipa: ''` — add missing stress mark (ма́ркер)
3. Vocabulary line 66: Change `ipa: ''` → `ipa: ''` — move stress to correct syllable (завершува́ти)
4. Vocabulary line 81: Change `ipa: ''` → `ipa: ''` — move stress to final syllable (досягти́)

**Expected score after fix:** 9/10

### Educational: 8/10 → 9/10
**What to fix:**
1. After line 115 in Section «Граматична Система: Форми та Функції»: Add an inline [!exercise] block for ДВ simple future conjugation practice (e.g., "Утворіть просту форму майбутнього часу: зробити → я _____, ти _____, він/вона _____")
2. Line 187: Change «Це союз, створений для опису процесів.» → «Це поєднання, створене для опису процесів.» — removes ambiguous grammar terminology

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.0 + 9×1.0 + 9×1.2 + 9×1.1 + 9×1.2 + 10×1.0 + 9×1.3 + 9×0.9 + 9×1.3 + 9×1.0 + 9×1.5 + 9×1.5) / 15.5
= (13.5 + 9.0 + 9.0 + 10.8 + 9.9 + 10.8 + 10.0 + 11.7 + 8.1 + 11.7 + 9.0 + 13.5 + 13.5) / 15.5
= 140.5 / 15.5
= 9.06/10
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (core grammar track — not required)
- Dates checked: 1 (Parajanov 1964 ✓)
- Named figures verified: 3 (Паращанов ✓, Шевченко ✓, Леся Українка ✓)
- Primary quotes cross-referenced: N/A — core track
- Chronological sequence: N/A — core track
- Claims without research grounding: 0
- Callout boxes verified: 17 callouts checked — all factual claims accurate or properly hedged

## Verification Summary

- Content lines read: 311
- Activity items checked: 112 (across 11 activities)
- Ukrainian sentences verified: 45+
- IPA transcriptions checked: 30 (all vocabulary items)
- Factual claims verified: 8 (cultural references, etymologies, grammar rules)
- Issues found: 6 (4 IPA stress errors, 1 ambiguous terminology, 1 practice gap)

## Verdict

**FAIL**

The module fails due to Linguistic Accuracy auto-fail (8/10, threshold <9). Four IPA stress errors in the vocabulary file (маркер, завершувати, досягти — all unfixed across 2 repair cycles; plus newly discovered завершення) remain the sole blocking issue. The content prose itself is excellent — well-structured, pedagogically sound, culturally rich, and linguistically accurate. All 4 IPA fixes are trivial single-line changes. Once applied, the module should reach 9.06/10 and PASS.