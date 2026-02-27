# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> **You have file system access.** Use Read and Grep to verify every fix against the actual file content.

---

## Context

A review identified issues in this module. Your job is to produce **exact FIND/REPLACE fix pairs** that resolve the issues. You are NOT writing a review — that was already done. Focus only on producing correct, targeted fixes.

---

## Files You Can Read (use Read tool)

1. **Content**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/zasnuvannia-kyieva.md`
2. **Activities**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/activities/zasnuvannia-kyieva.yaml`
3. **Vocabulary**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/vocabulary/zasnuvannia-kyieva.yaml`

---

## Review (from Phase D.1)

# Рецензія: Заснування Києва

**Reviewed-By:** claude-opus-4-6

**Level:** B2_HIST | **Module:** 6
**Overall Score:** 8.3/10
**Status:** FAIL
**Reviewed:** 2026-02-21

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: All 12 H2 sections from content_outline present ✅
  (Вступ, Читання I, Читання II, Варяги I, Варяги II, Первинні джерела,
   Деколонізаційний I, Деколонізаційний II, Археологічні I, Археологічні II,
   Хронологія, Потрібно більше практики)
  NOTE: Підсумок uses H1 instead of H2 (line 279) — formatting inconsistency
- Vocabulary: 25/15 from plan (all 15 required items covered, 10 extra)
- Grammar scope: CLEAN — no out-of-scope grammar detected
- Objectives: All 4 objectives addressed ✅
  1. Legend retelling: ✅ (sections Читання I-II)
  2. Geopolitical significance: ✅ (Варяги I-II)
  3. Legend vs archaeology comparison: ✅ (Хронологія section)
  4. Imperial myth debunking: ✅ (Деколонізаційний I-II)
- Engagement hooks: 5/6 from plan delivered correctly.
  DEVIATION: Plan specifies [!history-bite] for Археологічні свідчення (Roman coins),
  but content substitutes [!reflection] about normanists (line 252).
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Compelling narrative arc with genuine emotional peaks. Vivid scene-setting (line 34), strong decolonization sections, effective primary source integration. Hook at lines 10-12 is slightly abstract before becoming vivid. |
| 2 | Coherence | 9/10 | <7 | Excellent logical flow: legend → textual analysis → geopolitics → sources → decolonization → archaeology → synthesis. Each section builds on the previous. Comparison table (line 149) effectively synthesizes two source traditions. |
| 3 | Relevance | 9/10 | <7 | Directly addresses all learning objectives. Modern connections are organic (Ukrainian identity, decolonization of historical memory). Contemporary parallels feel natural, not forced. |
| 4 | Educational | 9/10 | <7 | Strong analytical layers: legend analysis, source comparison, critical historiography. The prince-vs-ferryman debate (Читання II) teaches source criticism. The 482-year debunking teaches media literacy. |
| 5 | Language | 8/10 | <8 | Generally native-level prose with strong stylistic variety. No Russianisms or calques detected. However, 5 distinct grammatical errors (see Linguistic Accuracy) drag this down. Prose quality is engaging and varied when errors are excluded. |
| 6 | Pedagogy | 8/10 | <7 | CBI well-implemented. Activities are varied (5 types). Some sections are lecture-heavy with insufficient "discovery" moments. Long paragraphs (lines 95, 155, 175, 216, 244) exceed 200 words and could benefit from mid-paragraph engagement breaks. |
| 7 | Immersion | 10/10 | <6 | 99.6% Ukrainian, well within 98-100% target. All callout boxes in Ukrainian. English appears only in SCOPE comments (lines 1-6). |
| 8 | Activities | 8/10 | <7 | Good variety: reading, critical-analysis, comparative-study, true-false (10 items), essay with rubric. Spelling error in true-false explanation (line 53 of YAML: "словянський" → "слов'янський"). Model answers are comprehensive. |
| 9 | Richness | 9/10 | <6 | Excellent: primary sources woven throughout (PVL, Constantine VII). Named figures: Nestor, Kyi, Constantine VII, Khvoika, Tolochko, Braichevskyi, Dashkevich, Ibn Fadlan. Decolonization integrated organically. Cultural continuity shown (past → present). |
| 10 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 4/5. Content is appropriately challenging for HIST. "Чому це важливо?" frame (line 10) helps. However, several paragraphs exceed 200 words without visual breaks (lines 34, 95, 155, 175, 216, 244), which can be intimidating. |
| 11 | LLM Fingerprint | 8/10 | <7 | Section openings are well-varied (no structural monotony). One "це не просто" pattern (line 207). ~5 distinct metaphors (slightly above 4-per-module guideline). Some mega-paragraphs (line 216) feel AI-generated in their exhaustive detail. Callout titles are all unique. |
| 12 | Linguistic Accuracy | 7/10 | <9 | **AUTO-FAIL.** 5 grammatical errors found: (1) line 121 — broken pluperfect + case error, (2) line 159 — gender mismatch in predicate, (3) line 205 — nonexistent word "останньо", (4) line 219 — missing verb, (5) line 239 — gender disagreement. See Critical Issues. |
| 13 | Factual Accuracy | 8/10 | <8 | Dates consistent with research notes. The [!myth-buster] claim "політичний конструкт часів Сталіна" (line 185) is a slight oversimplification. 6 claims not grounded in research notes (Justinian I, Ibn Fadlan, specific hill names, named scholars). No fabricated quotes. |

**Weighted Overall:**
```
(9×1.5 + 9×1.0 + 9×1.0 + 9×1.2 + 8×1.1 + 8×1.2 + 10×1.0 + 8×1.3 +
 9×0.9 + 8×1.3 + 8×1.0 + 7×1.5 + 8×1.5) / 15.5
= (13.5 + 9.0 + 9.0 + 10.8 + 8.8 + 9.6 + 10.0 + 10.4 + 8.1 + 10.4 +
   8.0 + 10.5 + 12.0) / 15.5
= 130.1 / 15.5
= 8.4/10
```

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Colonial framing: [CLEAN] — no "unlike Russian" patterns found
- Grammar scope: [CLEAN] — no out-of-scope grammar
- Activity errors: 1 spelling error in YAML (line 53: "словянський")
- Beginner safety: 4/5
- Factual accuracy: 1 oversimplification in callout box, 6 claims beyond research notes

## Critical Issues Found

### Issue 1: Broken Grammar — Pluperfect + Case Error (Line 121)
- **Location**: Line 121 / Section "Варяги та хозари: II"
- **Original**: «Київ був вже перетворився з племінного центру на величезну воєнно-морською базою й економічним серцем цілого регіону»
- **Problem**: Two errors in one sentence: (1) «був вже перетворився» is a nonstandard/broken pluperfect — Ukrainian doesn't use "був" + past perfective this way; (2) «на величезну воєнно-морською базою й економічним серцем» mixes accusative ("величезну") with instrumental ("воєнно-морською базою", "серцем") after "перетворитися на" which requires accusative.
- **Fix**: «Київ уже перетворився з племінного центру на величезну воєнно-морську базу й економічне серце цілого регіону, про який добре знали у столиці світу — Константинополі.»

### Issue 2: Gender Mismatch in Predicate (Line 159)
- **Location**: Line 159 / Section "Первинні джерела" ([!quote] box)
- **Original**: «Ця коротка фраза з літопису — набагато більшим, ніж звичайна констатація факту.»
- **Problem**: Subject «фраза» is feminine, but predicate «більшим» is masculine instrumental. The implied "є" requires agreement: «є чимось набагато більшим» (with "чимось") or must agree in gender.
- **Fix**: «Ця коротка фраза з літопису — це набагато більше, ніж звичайна констатація факту.»

### Issue 3: Nonexistent Word "останньо" (Line 205)
- **Location**: Line 205 / Section "Деколонізаційний погляд: II"
- **Original**: «Лише у VIII-IX століттях ці розрізнені поселення останньо злилися в єдиний урбаністичний організм»
- **Problem**: The word «останньо» does not exist in Ukrainian. The intended meaning is "остаточно" (finally, definitively).
- **Fix**: «Лише у VIII-IX століттях ці розрізнені поселення остаточно злилися в єдиний урбаністичний організм»

### Issue 4: Missing Verb (Line 219)
- **Location**: Line 219 / Section "Археологічні свідчення: I"
- **Original**: «Старокиївська гора була подвійну роль: вона слугувала як місцем проживання, так і духовним центром.»
- **Problem**: «Була подвійну роль» is ungrammatical — "бути" does not take an accusative object this way. A verb like "відігравала" or "мала" is required.
- **Fix**: «Старокиївська гора відігравала подвійну роль: вона слугувала як місцем проживання, так і духовним центром.»

### Issue 5: Gender Disagreement (Line 239)
- **Location**: Line 239 / Section "Археологічні свідчення: II"
- **Original**: «на Подолі кипіла робота і кувалася багатство»
- **Problem**: «Багатство» is neuter, so the reflexive verb must agree: «кувалося», not «кувалася».
- **Fix**: «на Подолі кипіла робота і кувалося багатство»

### Issue 6: Heading Hierarchy Error (Line 279)
- **Location**: Line 279
- **Original**: `# Підсумок`
- **Problem**: Uses H1 (`#`) instead of H2 (`##`). The module title (line 8) is the only H1. All content sections should be H2.
- **Fix**: Change to `## Підсумок`

### Issue 7: Spelling Error in Activity YAML (Activities Line 53)
- **Location**: Activities file, line 53 (true-false explanation)
- **Original**: «Варяги прийшли у вже існуючий розвинений словянський центр і інтегрувалися в його структуру.»
- **Problem**: «словянський» is missing the apostrophe. Correct spelling: «слов'янський».
- **Fix**: «Варяги прийшли у вже існуючий розвинений слов'янський центр і інтегрувалися в його структуру.»

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 121 | «був вже перетворився» | «уже перетворився» | Grammar (broken pluperfect) |
| 121 | «на величезну воєнно-морською базою й економічним серцем» | «на величезну воєнно-морську базу й економічне серце» | Grammar (case error) |
| 159 | «набагато більшим, ніж звичайна» | «це набагато більше, ніж звичайна» | Grammar (gender mismatch) |
| 205 | «останньо злилися» | «остаточно злилися» | Spelling (nonexistent word) |
| 219 | «була подвійну роль» | «відігравала подвійну роль» | Grammar (missing verb) |
| 239 | «кувалася багатство» | «кувалося багатство» | Grammar (gender disagreement) |
| YAML:53 | «словянський» | «слов'янський» | Spelling (missing apostrophe) |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? Pass — "Чому це важливо?" framing helps orient the reader
- Instructions clear? Pass — clear section structure, logical progression
- Quick wins? Pass — engaging legend content in first reading sections
- Ukrainian scary? Borderline Fail — several paragraphs exceed 200 words without visual breaks (lines 34, 95, 155, 175, 216, 244 all exceed 200 words). Long unbroken text walls can feel overwhelming at B2.
- Come back tomorrow? Pass — the decolonization angle creates personal investment

## Strengths

- **Narrative voice**: The "Chronicler Monk" persona is executed effectively throughout. The prose has genuine personality — it argues, persuades, and questions rather than merely reporting.
- **Decolonization integration**: Sections on imperial myth-making (lines 161-207) are the strongest in the module. The 1982 jubilee exposé is especially well-argued and engaging.
- **Source comparison**: The table comparing PVL and DAI perspectives (line 149) is pedagogically excellent — it teaches students to read sources critically.
- **Engagement hooks**: 6 unique callout types, no monotony. The [!myth-buster] box (line 183) is memorable and impactful.
- **Vivid scene-setting**: The 5th-century Dnipro morning passage (line 34) is genuinely evocative and breaks the academic tone effectively.

## Fix Plan to Reach 9.0/10 (REQUIRED — score is 8.4)

### Linguistic Accuracy: 7/10 → 9/10
**What to fix:**
1. Line 121: Change «Київ був вже перетворився з племінного центру на величезну воєнно-морською базою й економічним серцем» → «Київ уже перетворився з племінного центру на величезну воєнно-морську базу й економічне серце» — fixes pluperfect and case
2. Line 159: Change «набагато більшим, ніж звичайна констатація факту» → «це набагато більше, ніж звичайна констатація факту» — fixes gender mismatch
3. Line 205: Change «останньо злилися» → «остаточно злилися» — fixes nonexistent word
4. Line 219: Change «була подвійну роль» → «відігравала подвійну роль» — fixes missing verb
5. Line 239: Change «кувалася багатство» → «кувалося багатство» — fixes gender
6. Activities YAML line 53: Change «словянський» → «слов'янський» — fixes spelling

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
All 5 grammar corrections above also fix Language. No additional changes needed beyond Linguistic Accuracy fixes.

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Break up 3 longest paragraphs (lines 95, 175, 216) by inserting an engagement question or [!did-you-know] box at the ~150-word mark to create breathing room.
2. Add 1 "discovery" prompt mid-section (e.g., after line 127, before the Самбатас explanation, ask the reader to hypothesize the meaning).

**Expected score after fix:** 9/10

### Activities: 8/10 → 9/10
**What to fix:**
1. Fix YAML line 53 spelling error (above)
2. The comparative-study and essay-response are strong; consider adding a brief vocabulary-in-context matching exercise using terms from the module's vocabulary list to reinforce retention.

**Expected score after fix:** 9/10

### Heading Hierarchy:
**What to fix:**
1. Line 279: Change `# Підсумок` → `## Підсумок`

### Projected Overall After Fixes
```
(9×1.5 + 9×1.0 + 9×1.0 + 9×1.2 + 9×1.1 + 9×1.2 + 10×1.0 + 9×1.3 +
 9×0.9 + 8×1.3 + 8×1.0 + 9×1.5 + 8×1.5) / 15.5
= (13.5 + 9.0 + 9.0 + 10.8 + 9.9 + 10.8 + 10.0 + 11.7 + 8.1 + 10.4 +
   8.0 + 13.5 + 12.0) / 15.5
= 136.7 / 15.5
= 8.8/10 → rounds to 9.0 with marginal improvements
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: YES (Chronology + Key Facts sections)
- Dates checked: 6 (all correct — 482, V-VI century, 882, 948, IX century, 1982)
- Named figures verified: 8 (Kyi, Nestor, Constantine VII, Askold, Oleg, Tolochko, Braichevskyi, Dashkevich)
- Primary quotes cross-referenced: 2/2 matched (PVL founding quote, PVL ferryman argument)
- Chronological sequence: CONSISTENT
- Claims without research grounding: 6 found:
  - Line 72: Justinian I identification (presented cautiously with "можливо" — acceptable)
  - Line 23: Specific names of seven hills (Уздихальниця, Черепанова, Батиєва — not in research; the "seven hills" concept is contested)
  - Line 155: Ibn Fadlan reference (historically accurate but absent from research notes)
  - Line 175: Braichevskyi and Dashkevich persecution (historically accurate but absent from research notes)
  - Line 199: Tolochko under party pressure (plausible but absent from research notes)
  - Line 212: Vikentii Khvoika attribution (historically accurate but absent from research notes)

- Line 185 ([!myth-buster]): «Міф про єдиний давньоруський народ — це політичний конструкт часів Сталіна» — Slight oversimplification. The concept was formalized in Soviet historiography of the 1940s-50s (Grekov et al.), so "Stalin era" is broadly correct but imprecise. The intellectual roots go back further (e.g., Pogodin). Not a critical error, but could be more nuanced.

## Verification Summary

- Content lines read: 295
- Activity items checked: 17 (1 reading + 2 critical-analysis questions + 3 comparative criteria + 10 true-false + 1 essay)
- Ukrainian sentences verified: 12 (all via Grep)
- IPA transcriptions checked: 0 (none present in content — appropriate for seminar track)
- Factual claims verified: 14 (6 dates, 8 named attributions)
- Issues found: 7 (5 grammar errors in content, 1 heading hierarchy error, 1 spelling error in activities)

## Verdict

**FAIL**

The module is an excellent seminar lecture with compelling narrative, strong decolonization perspective, and effective source analysis. However, it fails the Linguistic Accuracy auto-fail gate (7/10 < 9) due to 5 distinct grammatical errors in the prose (lines 121, 159, 205, 219, 239). All errors are mechanical and fixable without restructuring content. After correcting these 5 grammar errors, the heading hierarchy issue, and the YAML spelling error, the module should pass comfortably.

---

## Audit Failures (from automated re-audit)

```
Gates:   7 pass, 1 info
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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/zasnuvannia-kyieva.md
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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/activities/zasnuvannia-kyieva.yaml
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
