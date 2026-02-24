# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> **You have file system access.** Use Read and Grep to verify every fix against the actual file content.

---

## Context

A review identified issues in this module. Your job is to produce **exact FIND/REPLACE fix pairs** that resolve the issues. You are NOT writing a review — that was already done. Focus only on producing correct, targeted fixes.

---

## Files You Can Read (use Read tool)

1. **Content**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/aspect-complete-system.md`
2. **Activities**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/activities/aspect-complete-system.yaml`
3. **Vocabulary**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/vocabulary/aspect-complete-system.yaml`

---

## Review (from Phase D.1)

# Рецензія: Вид дієслова: повна система

**Reviewed-By:** claude-opus-4-6

**Level:** B1 | **Module:** b1-06
**Overall Score:** 8.8/10
**Status:** FAIL
**Reviewed:** 2026-02-23

## D.3 Re-Review: Fix Verification Summary

| D.1 Issue | Status | Notes |
|-----------|--------|-------|
| IPA stress "завершення" [zɑˈʋɛrʃɛnʲːɑ] | **NOT FIXED** | Still has stress on "вер" instead of "ше" |
| IPA stress "завершувати" [zɑˈʋɛrʃuʋɑtɪ] | **NOT FIXED** | Still has stress on "вер" instead of "ва" |
| IPA stress "досягти" [dɔsʲɑˈɦtɪ] | **NOT FIXED** | Still places stress before ɦ instead of on "сяг" |
| LLM rhetoric line 85 "гордістю мови" | **FIXED** | Now reads «унікальною рисою української морфології» |
| LLM rhetoric line 223 "лексичні нюанси" | **FIXED** | Now reads «як зміна виду дієслова передає зовсім різний зміст без жодних додаткових слів» |
| LLM rhetoric line 139 "людського досвіду" | **PARTIAL — REGRESSION** | Changed to «переживань і дій» but introduced double "дуже" |
| Match-up activity count (12→15+) | **FIXED** | Both match-up activities now have 15 pairs |
| Fill-in activity count (10→12+) | **FIXED** | First fill-in now has 12 items |

**Conclusion:** 3 of 8 D.1 issues remain unfixed (all IPA), 1 partial fix introduced a regression, 4 fully fixed.

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: All 5 H2 sections present and match plan (Розминка та Контекст, Граматична Система: Форми та Функції, Глибинна Семантика: Процес та Результат, Аналіз Помилок та Тонкощі, Практика та Мовленнєві Ситуації)
- Vocabulary: 29/30 from plan vocabulary present. All 12 required items included, all 5 recommended items included. Additional vocab items (режисер, об'єктив, фіксувати, статика, динаміка) are pedagogically relevant.
- Grammar scope: CLEAN — aspect system stays within b1-06 boundaries. Motion verb aspect correctly excluded (deferred to b1-16 per SCOPE comment at line 4).
- Objectives: All 3 objectives addressed (understand complete system, identify from context, choose appropriate aspect).
- Plan examples: Plan specified казати/сказати as primary example for future tense table; content uses читати/прочитати. Minor deviation, concept fully covered.
- Activity plan compliance: PASS — match-up now 15 items each (plan 15+), fill-in 12 items (plan 12+). Additional unplanned activity types (error-correction, unjumble, cloze, mark-the-words) provide extra variety.
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Strong teaching experience. The Paradjanov camera metaphor in Section «Розминка та Контекст» and Video/Photo mode analogy create compelling "aha" moments. The diagnostic task (пекла/спекла at lines 26-32) immediately engages the learner in discovery. The office dialogue in Section «Практика та Мовленнєві Ситуації» (lines 293-296) shows clear real-world application. Section «Глибинна Семантика: Процес та Результат» remains slightly concept-dense (general-factual + repetition + proverbs) but is now better paced with interspersed exercises at lines 151 and 164. |
| 2 | Coherence | 9/10 | <7 | Excellent logical flow: intuition → rules → deep semantics → error analysis → practice. The Video/Photo metaphor introduced in Section «Розминка та Контекст» is referenced throughout. One structural concern: Section «Аналіз Помилок та Тонкощі» includes semelfactives (lines 232-242) which are more of a grammatical subtype than an "error" or "nuance," fitting better in Section «Граматична Система: Форми та Функції». |
| 3 | Relevance | 10/10 | <7 | Fully relevant to B1 learner needs. Workplace dialogue (lines 293-296), IT context (line 301), job interview scenario (line 149), and everyday situations (cooking, transport, studying) demonstrate practical applicability across life domains. |
| 4 | Educational | 9/10 | <7 | All three learning objectives addressed thoroughly. The 4-question algorithm in Section «Практика та Мовленнєві Ситуації» (lines 258-270) is an excellent autonomous decision tool. The temporal marker table (lines 275-285) provides a clear, actionable reference. Proverb analysis in Section «Глибинна Семантика: Процес та Результат» (lines 183-187) provides a genuinely insightful linguistic anchor. |
| 5 | Language | 8/10 | <8 | Ukrainian is largely natural. However, excessive intensifier density persists: «фундаментальна різниця» (line 30), «кардинально різняться» (line 48), «абсолютно ідентичні» (line 91), «критично важливим» (line 149), «Ще одна фундаментальна характеристика» (line 172), «надзвичайно цікавий» (line 208), «неймовірної динаміки» (line 239), «надзвичайно важливим» (line 301), «потужний інструмент» (line 309). D.2 regression at line 139: «Це дуже важливий нюанс, який робить українську мову дуже точною в описі переживань і дій» — double "дуже" in one sentence is poor Ukrainian style. No Russianisms. No calques. No colonial framing. |
| 6 | Pedagogy | 9/10 | <7 | Strong TTT: diagnostic task first (lines 23-32), then rules, then practice. 19 engagement boxes across 10+ types provide rich variety. Section «Розминка та Контекст» uses the торт dialogue as genuine discovery before rules are stated. Practice is well-integrated throughout, not only at the end. Exercises in Section «Граматична Система: Форми та Функції» (lines 65-69, 93-104) effectively break dense grammar. |
| 7 | Immersion | 10/10 | <6 | 99.5% Ukrainian. Target: 85-100% for B1.1. English appears only in justified parenthetical concept labels: "(Video mode)", "(Photo mode)", "(will + verb)", "(Have you ever read...?)", "(daily stand-ups)". All serve cross-linguistic reference or transliteration purposes. |
| 8 | Activities | 9/10 | <7 | 11 activities across 8 types (quiz ×1, match-up ×2, fill-in ×3, error-correction ×1, unjumble ×1, cloze ×1, mark-the-words ×1, true-false ×1). 124 total items. Match-up activities now have 15 pairs each (plan 15+ met, up from 12 in D.1). Fill-in "Оберіть правильний вид" now has 12 items (plan 12+ met, up from 10 in D.1). All items checked linguistically correct. Error-correction and cloze narrative are particularly well-crafted. |
| 9 | Richness | 9/10 | <6 | Cultural embedding: Параджанов's «Тіні забутих предків» (1964), Шевченко's «Кобзар», Леся Українка's «Лісова пісня», Ukrainian proverbs. Tables: comparative future tense table (lines 125-132), temporal markers table (lines 275-285). Dialogues: торт scene (lines 26-28), concert dialogue (lines 253-255), office report (lines 293-296). 19 engagement boxes across 10+ types. |
| 10 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 4/5. B1 learners are appropriately challenged. Section «Глибинна Семантика: Процес та Результат» is concept-dense but now has exercises interspersed (lines 151, 164) which helps pacing. The 4-question algorithm in Section «Практика та Мовленнєві Ситуації» provides a practical safety net for learners who feel overwhelmed by the semantic subtleties. Content length (4820 words) is substantial but well-structured. |
| 11 | LLM Fingerprint | 8/10 | <7 | D.2 fixed two of three flagged instances: "гордістю мови" (line 85) now reads «унікальною рисою української морфології» — factual and clean; "лексичні нюанси" (former line 223) now reads «як зміна виду дієслова передає зовсім різний зміст без жодних додаткових слів» (line 230) — clean. However: line 309 «потужний інструмент для створення живих, динамічних та змістовних текстів» remains a classic AI closing cliché. Line 239 «Використання цих форм додає вашій розповіді неймовірної динаміки» — hyperbolic. Structural monotony: PASS (each H2 opens differently). Callout title repetition: PASS. Example formatting varies (tables, bullets, dialogues, numbered lists): PASS. |
| 12 | Linguistic Accuracy | 8/10 | <9 | **AUTO-FAIL: 3 IPA stress errors remain unfixed in vocabulary file.** (1) Line 25: "завершення" given as [zɑˈʋɛrʃɛnʲːɑ] — stress on "вер" instead of "ше". Correct: [zɑʋɛrˈʃɛnʲːɑ] (завершéння). (2) Line 66: "завершувати" given as [zɑˈʋɛrʃuʋɑtɪ] — stress on "вер" instead of "ва". Correct: [zɑʋɛrʃuˈʋɑtɪ] (завершувáти). (3) Line 81: "досягти" given as [dɔsʲɑˈɦtɪ] — stress before ɦ instead of on "сяг". Correct: [dɔˈsʲɑɦtɪ] (дося́гти). Content grammar explanations are all accurate. All aspectual pairs verified correct. |
| 13 | Factual Accuracy | 9/10 | <8 | Grammar rules accurately presented. State Standard §4.2.3.1 reference consistent with research notes. Параджанов's «Тіні забутих предків» (1964) correctly attributed. Etymology of synthetic future from «імати» is linguistically sound. Proverbs «Зробив діло — гуляй сміло» and «Вік живи — вік учись» are real Ukrainian proverbs, correctly analyzed. The [!culture] box about «Лісова пісня» (line 242) hedges with «можна уявити» which avoids fabrication. No factual errors found in any callout box. |

**Weighted Overall:**
```
(9×1.5 + 9×1.0 + 10×1.0 + 9×1.2 + 8×1.1 + 9×1.2 + 10×1.0 + 9×1.3 + 9×0.9 + 8×1.3 + 8×1.0 + 8×1.5 + 9×1.5) / 15.5
= (13.5 + 9.0 + 10.0 + 10.8 + 8.8 + 10.8 + 10.0 + 11.7 + 8.1 + 10.4 + 8.0 + 12.0 + 13.5) / 15.5
= 136.6 / 15.5
= **8.8/10**
```

## Auto-Fail Checklist Results

- Russianisms: [CLEAN] — no instances detected
- Calques: [CLEAN] — no instances detected
- Colonial framing: [CLEAN] — no Russian-comparison patterns found
- Grammar scope: [CLEAN] — aspect system within b1-06 scope, motion verb aspect correctly deferred
- Activity errors: [CLEAN] — all 11 activities (124 items) checked, all linguistically correct
- Beginner safety: 4/5
- Factual accuracy: [CLEAN] — all grammar rules, cultural references, and etymologies verified

## Critical Issues Found

### Issue 1: IPA Stress Placement Errors — UNFIXED FROM D.1 (Linguistic Accuracy — AUTO-FAIL TRIGGER)
- **Location**: Vocabulary file, lines 25, 66, 81
- **Original (line 25)**: «ipa: '[zɑˈʋɛrʃɛnʲːɑ]'» for "завершення"
- **Problem**: Stress mark placed on syllable "вер" instead of "ше". The word завершéння has stress on the third syllable. This was flagged in D.1 and D.2 did NOT apply the fix.
- **Fix**: Change to `ipa: '[zɑʋɛrˈʃɛnʲːɑ]'`

- **Original (line 66)**: «ipa: '[zɑˈʋɛrʃuʋɑtɪ]'» for "завершувати"
- **Problem**: Stress on "вер" instead of "ва". Standard -увати imperfectives have stress on the penultimate syllable: завершувáти. Unfixed from D.1.
- **Fix**: Change to `ipa: '[zɑʋɛrʃuˈʋɑtɪ]'`

- **Original (line 81)**: «ipa: '[dɔsʲɑˈɦtɪ]'» for "досягти"
- **Problem**: Stress mark before ɦ suggests stress on final cluster. The word дося́гти has stress on the second syllable "сяг". Unfixed from D.1.
- **Fix**: Change to `ipa: '[dɔˈsʲɑɦtɪ]'`

### Issue 2: D.2 Regression — Double "дуже" (Language Quality)
- **Location**: Line 139, Section «Граматична Система: Форми та Функції»
- **Original**: «Це дуже важливий нюанс, який робить українську мову дуже точною в описі переживань і дій.»
- **Problem**: D.2 replaced "вкрай точною в описі людського досвіду" with "дуже точною в описі переживань і дій" without noticing the earlier "дуже важливий" in the same sentence. This creates an awkward double "дуже" that a native speaker would modulate (e.g., using "вельми", "доволі", or restructuring).
- **Fix**: Change to «Це важливий нюанс, який робить українську мову точною в описі переживань і дій.» (Remove both "дуже" — the sentence doesn't need intensifiers to make its point.)

### Issue 3: Residual Intensifier Density (Language Quality)
- **Location**: Throughout all sections
- **Problem**: D.1 flagged ~15 intensifiers. D.2 fixed 3 flagged LLM rhetoric instances but did not address the broader pattern. Remaining: «фундаментальна різниця» (line 30), «кардинально різняться» (line 48), «абсолютно ідентичні» (line 91), «критично важливим» (line 149), «Ще одна фундаментальна характеристика» (line 172), «надзвичайно цікавий та тонкий аспект» (line 208), «неймовірної динаміки» (line 239), «надзвичайно важливим» (line 301), «потужний інструмент» (line 309). While some intensifiers are justified (e.g., "абсолютно ідентичні" in line 91 is linguistically accurate for aspect pair equivalence), the cumulative density remains higher than natural teacher speech.
- **Fix (highest priority)**: 
  - Line 239: «неймовірної динаміки» → «значної динаміки»
  - Line 301: «надзвичайно важливим» → «важливим»
  - Line 309: «потужний інструмент» → «важливий інструмент»

### Issue 4: AI Closing Cliché (LLM Fingerprint)
- **Location**: Line 309, Section «Підсумок»
- **Original**: «Опанувавши цю систему, ви отримали потужний інструмент для створення живих, динамічних та змістовних текстів українською мовою.»
- **Problem**: "Потужний інструмент для створення живих, динамічних та змістовних текстів" is a stack of three vague positive adjectives in the classic AI summary style. A teacher would close with something more concrete about what the learner can now do.
- **Fix**: «Опанувавши цю систему, ви зможете точніше описувати події — від щоденних звичок до важливих досягнень — і ваша розповідь звучатиме більш природно для українського слухача.»

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 139 | «дуже важливий нюанс, який робить українську мову дуже точною» | «важливий нюанс, який робить українську мову точною» | Stylistic (D.2 regression) |
| 239 | «неймовірної динаміки» | «значної динаміки» | Intensifier density |
| 301 | «надзвичайно важливим» | «важливим» | Intensifier density |
| 309 | «потужний інструмент для створення живих, динамічних та змістовних текстів» | «зможете точніше описувати події — від щоденних звичок до важливих досягнень» | AI cliché |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? **Pass** — Content is dense but well-structured with 19 engagement boxes breaking up prose.
- Instructions clear? **Pass** — Each concept is explained with concrete examples before moving forward.
- Quick wins? **Pass** — Diagnostic task at lines 23-32 gives early success feeling; micro-practice at lines 65-69 provides quick validation.
- Ukrainian scary? **Pass** — Complex grammar is scaffolded with the Video/Photo metaphor as a consistent anchor.
- Come back tomorrow? **Marginal** — Section «Глибинна Семантика: Процес та Результат» introduces general-factual meaning, repetition semantics, and proverb analysis in sequence. Despite exercises at lines 151 and 164, the conceptual density may fatigue some B1 learners before reaching Section «Аналіз Помилок та Тонкощі».

## Strengths

- **D.2 fixes successfully addressed key LLM rhetoric issues**: The "гордістю мови" replacement at line 85 and the "лексичні нюанси" replacement at line 230 are well-done — factual, clean, and pedagogically appropriate.
- **Activity count fixes are solid**: Match-up activities now have 15 pairs each and fill-in has 12 items, meeting plan requirements. The additional items are linguistically accurate and pedagogically relevant.
- **Paradjanov metaphor remains highly effective**: The dynamic camera / static frame analogy is a genuinely insightful cultural bridge that makes an abstract grammar concept tangible.
- **4-question algorithm** (lines 258-270) is an excellent practical tool for learner autonomy.
- **Proverb analysis** (lines 183-187) is a pedagogically rich way to anchor abstract grammar in cultural memory.
- **Error-correction activity** (activity lines 262-337) is one of the best exercises in the module — directly targets the #1 learner error (буду + perfective infinitive).
- **Cloze narrative** (activity lines 360-462) provides authentic aspect usage in a continuous story context.

## Fix Plan to Reach 9.0/10

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Vocabulary line 25: Change `ipa: '[zɑˈʋɛrʃɛnʲːɑ]'` → `ipa: '[zɑʋɛrˈʃɛnʲːɑ]'` — correct stress placement for завершéння
2. Vocabulary line 66: Change `ipa: '[zɑˈʋɛrʃuʋɑtɪ]'` → `ipa: '[zɑʋɛrʃuˈʋɑtɪ]'` — correct stress placement for завершувáти
3. Vocabulary line 81: Change `ipa: '[dɔsʲɑˈɦtɪ]'` → `ipa: '[dɔˈsʲɑɦtɪ]'` — correct stress placement for дося́гти

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Line 139: Remove double "дуже" — «Це важливий нюанс, який робить українську мову точною в описі переживань і дій.»
2. Line 239: «неймовірної динаміки» → «значної динаміки»
3. Line 301: «надзвичайно важливим» → «важливим»
4. Line 309: Replace AI closing cliché with concrete learner outcome.

**Expected score after fix:** 9/10

### LLM Fingerprint: 8/10 → 9/10
**What to fix:**
1. Line 309: Replace «потужний інструмент для створення живих, динамічних та змістовних текстів» with concrete description of what the learner can now do.
2. The Language fixes above (removing intensifiers) will also improve this dimension.

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.0 + 10×1.0 + 9×1.2 + 9×1.1 + 9×1.2 + 10×1.0 + 9×1.3 + 9×0.9 + 8×1.3 + 9×1.0 + 9×1.5 + 9×1.5) / 15.5
= (13.5 + 9.0 + 10.0 + 10.8 + 9.9 + 10.8 + 10.0 + 11.7 + 8.1 + 10.4 + 9.0 + 13.5 + 13.5) / 15.5
= 140.2 / 15.5
= **9.0/10** → PASS
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (not applicable for core grammar track)
- Dates checked: 1 (Параджанов 1964 — correct)
- Named figures verified: 3 (Параджанов, Шевченко, Леся Українка — all correctly attributed)
- Primary quotes cross-referenced: N/A (core track)
- Chronological sequence: N/A (core track)
- Claims without research grounding: 0
- State Standard §4.2.3.1 reference: Consistent with research notes (line 4 of research)
- Etymology of synthetic future from «імати»: Linguistically sound, consistent with research
- Proverbs verified: 2/2 — «Зробив діло — гуляй сміло» and «Вік живи — вік учись» are real Ukrainian proverbs, correctly analyzed
- Callout box claims: All 19 boxes checked — no fabricated claims found

## Verification Summary

- Content lines read: 318
- Activity items checked: 124 (across 11 activities)
- Ukrainian sentences verified: 55+
- IPA transcriptions checked: 29 (3 errors found — all in D.1, unfixed)
- Factual claims verified: 19 callout boxes + all grammar rules
- Issues found: 4 (1 critical unfixed from D.1, 1 D.2 regression, 2 residual style issues)

## Verdict

**FAIL**

The sole blocking issue is **Linguistic Accuracy 8/10 < 9/10** caused by three IPA stress placement errors in the vocabulary file (завершення, завершувати, досягти) that were flagged in D.1 but not addressed by D.2. These are simple stress mark position changes in the YAML file. Additionally, D.2 introduced a minor regression (double "дуже" at line 139) while fixing LLM rhetoric. All other D.1 fixes (LLM rhetoric removal, activity count increases) were successfully applied. The module is pedagogically strong and close to passing — the remaining fixes are mechanical.

---

## Audit Failures (from automated re-audit)

```
VERDICT: FAIL
overall status is 'fail' (must be 'pass')
Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
failing gates:
review: Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ [REVIEW_VERDICT_FAIL] Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
⚠️  [PHANTOM_SECTION_REFERENCE] Review references 1 section(s) not found in content: 'Підсумок'. Verify section names match actual content headers.
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
• Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/aspect-complete-system-audit.log for details)
```

---

## Instructions

1. Read the content file using the Read tool
2. For each issue identified in the review OR in the audit failures:
   a. Use Grep to find the exact text that needs fixing
   b. Produce a FIND/REPLACE pair with verbatim FIND text
3. Only fix issues documented above — no silent extra changes
4. Prioritize fixes by impact: audit gate failures first, then review issues

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded.

```
===SECTION_FIX_START===
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/aspect-complete-system.md
---
FIND:
exact text to replace (full sentence or paragraph, verbatim from the file)
REPLACE:
corrected replacement text
---
FIND:
next problematic text
REPLACE:
corrected replacement
---
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/activities/aspect-complete-system.yaml
---
FIND:
exact activity text to replace
REPLACE:
corrected activity text
---
===SECTION_FIX_END===
```

## Fix Rules

- **FIND text must be verbatim** from the file — use Grep to verify before including
- Only fix issues documented in the review or audit failures above
- You MAY add new activities or modify existing ones if the review's Fix Plan explicitly requests it
- Do NOT add new prose sections or vocabulary items unless the review's Fix Plan explicitly requests it
- Maximum **20 FIND/REPLACE pairs** total (prioritize the most impactful fixes)
- Each FILE: line starts a new sub-block for that file
- If nothing needs fixing, output:
  ```
  ===SECTION_FIX_START===
  ===SECTION_FIX_END===
  ```

---

## Friction Report (MANDATORY)

After the fix block, include:

```
===FRICTION_START===
**Phase**: Phase D.2: Targeted Repair
**Step**: {what you were doing when friction occurred, or "Full Phase D.2"}
**Friction Type**: NONE | FIND_TEXT_MISMATCH | FILE_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write a review — that was already done in Phase D.1
- Do NOT output ===REVIEW_START=== blocks
- Do NOT modify files directly — only output fix blocks
- You MAY add/modify activities if the review's Fix Plan requests it (use FIND/REPLACE on the YAML file)
- Do NOT make cosmetic changes beyond what the review flagged
