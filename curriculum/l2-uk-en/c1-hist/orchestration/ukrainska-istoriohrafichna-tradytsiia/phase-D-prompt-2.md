# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> **You have file system access.** Use Read and Grep to verify every fix against the actual file content.

---

## Context

A review identified issues in this module. Your job is to produce **exact FIND/REPLACE fix pairs** that resolve the issues. You are NOT writing a review — that was already done. Focus only on producing correct, targeted fixes.

---

## Files You Can Read (use Read tool)

1. **Content**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-hist/ukrainska-istoriohrafichna-tradytsiia.md`
2. **Activities**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-hist/activities/ukrainska-istoriohrafichna-tradytsiia.yaml`
3. **Vocabulary**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-hist/vocabulary/ukrainska-istoriohrafichna-tradytsiia.yaml`

---

## Review (from Phase D.1)

**Reviewed-By:** claude-opus-4-6

# Рецензія: Українська історіографічна традиція

**Level:** C1-HIST | **Module:** 002
**Overall Score:** 7.5/10
**Status:** FAIL
**Reviewed:** 2026-02-23

## Plan Verification

```
Plan-Content Alignment: FAIL
- Sections: 9/9 H2 sections present, BUT 3 required plan points MISSING:
  1. "Трагічна доля — повернення до СРСР, смерть" (plan: Грушевський section) — ABSENT
  2. "Дмитро Дорошенко — популяризатор" (plan: Діаспорна section) — ABSENT (replaced by Липинський)
  3. "Знищення школи — радянська окупація 1939" (plan: Львівська школа section) — ABSENT
- Vocabulary: 4/4 required present (історія, подія, джерело, аналіз), 3/3 recommended present, 23 extra
- Grammar scope: CLEAN (no grammar teaching — seminar track)
- Objectives: PARTIAL — "Trace the evolution" ✓, "Assess contribution of Hrushevsky" ✓ but incomplete without his tragic fate
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 7/10 | <7 | Strong hook and decolonization frame, but devastating structural monotony — all 30 subsections follow identical formula (bold definition → exposition → 2 examples → closing). Lecture feels like a template fill, not a seminar. |
| 2 | Coherence | 8/10 | <7 | Logical chronological arc from Hrushevsky to modern institutions. However, 3 plan-required points missing creates gaps (no Doroshenko, no Hrushevsky's fate, no 1939 destruction of Lviv school). |
| 3 | Relevance | 9/10 | <7 | Excellent topic coverage for C1-HIST. Section «Західні історики України: Революція сприйняття» effectively connects to contemporary scholarship. All major figures included. |
| 4 | Educational | 8/10 | <7 | Deep content with good analytical vocabulary. Section «Михайло Грушевський: II — Подолання імперської схеми» has an excellent comparison table (lines 101-107). Missing plan content costs 1 point. |
| 5 | Language | 7/10 | <8 | Hagiographic superlative inflation: "надзвичайно" ×26, "абсолютно" ×23, "геніальн*" ×12, "блискуч*" ×9, "беззаперечн*" ×9. Typos: "переможцязами" (line 18), "академієчне" (line 108). Syntactic error line 143. |
| 6 | Pedagogy | 7/10 | <7 | CBI approach is sound, but the rigid identical structure across ALL subsections is antipedagogical — real seminar lectures vary their delivery. Every subsection opens with a bold dictionary-style definition, which is textbook, not seminar. |
| 7 | Immersion | 10/10 | <6 | 98.4% Ukrainian — within C1-HIST target of 98-100%. English appears only in parenthetical term translations, which is appropriate for this level. |
| 8 | Activities | 8/10 | <7 | Good variety: reading, critical-analysis, essay-response, true-false (12 items), comparative-study. Typo in activities line 99: "просопографіїчного" → "просопографічного". Reading source text is paraphrased, not primary. |
| 9 | Richness | 9/10 | <6 | 15 unique callout types, 2 comparison tables, 30+ named historical figures, dates throughout. Section «Діаспорна історіографія: II — Інституційний захист» has excellent institutional detail. |
| 10 | Beginner Safety | 9/10 | <7 | C1-HIST: appropriate complexity. "Would I Continue?" 4/5 — content is intellectually engaging but structural monotony causes energy drops. |
| 11 | LLM Fingerprint | 5/10 | <7 | SEVERE: All 30 subsections use identical formula. 30× `_Приклад 1:_` and 30× `_Приклад 2:_` in same format. Superlative saturation ("геніальний" applied to Грушевський, Липинський, Пріцак, Субтельний indiscriminately). |
| 12 | Linguistic Accuracy | 7/10 | <9 | 3 typos/errors: "переможцязами" (line 18), "академієчне" (line 108), missing negation (line 143). Activity typo: "просопографіїчного". Hagiographic register inappropriate for academic seminar. |
| 13 | Factual Accuracy | 8/10 | <8 | HURI founding conflated: content says 1968 (line 194) but HURI was established in 1973; chairs were endowed in 1968. Polons'ka-Vasylenko dates "1971-1972" (line 176) likely inaccurate (vol.1: 1972, vol.2: 1976). |

**Weighted Overall:**
```
(7 × 1.5) + (8 × 1.0) + (9 × 1.0) + (8 × 1.2) + (7 × 1.1) + (7 × 1.2) + (10 × 1.0) + (8 × 1.3) + (9 × 0.9) + (9 × 1.3) + (5 × 1.0) + (7 × 1.5) + (8 × 1.5)
= 10.5 + 8.0 + 9.0 + 9.6 + 7.7 + 8.4 + 10.0 + 10.4 + 8.1 + 11.7 + 5.0 + 10.5 + 12.0
= 120.9 / 15.5 = **7.8/10**
```

## Auto-Fail Checklist Results

- Russianisms: [CLEAN] — no Russianisms detected
- Calques: [CLEAN] — no calques detected
- Colonial framing: [CLEAN] — Ukrainian presented on own terms, [!decolonization] block at line 44 is legitimate
- Grammar scope: [CLEAN] — seminar track, no grammar teaching
- Activity errors: [1 TYPO] — "просопографіїчного" in activities line 99
- Beginner safety: 4/5
- Factual accuracy: [2 CONCERNS] — HURI date conflation, Polons'ka-Vasylenko publication dates
- Word salad: [CLEAN] — all paragraphs have clear single points

## Critical Issues Found

### Issue 1: SEVERE Structural Monotony (LLM Fingerprint)
- **Location**: ALL 30 H3 subsections across all 9 H2 sections
- **Original**: Every subsection follows: **Bold term** (English) → definition paragraph → `> _Приклад 1:_` → `> _Приклад 2:_` → closing paragraph. Count: 30× `_Приклад 1:_` and 30× `_Приклад 2:_`.
- **Problem**: This is the most severe LLM fingerprint pattern possible. No human lecturer would structure every single subsection identically. The formulaic examples destroy seminar authenticity.
- **Fix**: Vary structure radically. Some subsections should lead with a question, others with an anecdote. Replace many paired examples with inline illustrations, mini-dialogues, primary source excerpts, student exercises, or remove entirely. No more than 30% of subsections should use the same structural pattern.

### Issue 2: Superlative Inflation (Language Quality)
- **Location**: Throughout all sections; representative examples below
- **Original**: «геніальний Грушевський» (line 73), «геніальний Липинський» (line 93), «геніальний Субтельний» (line 221), «геніальний Пріцак» (line 197) — the word "геніальний" applied to 4+ different people
- **Problem**: Applying the same superlative to every figure is undifferentiated and undermines credibility. "Надзвичайно" appears 26 times (~once per 250 words), "абсолютно" 23 times. This reads as mechanical intensification, not nuanced assessment.
- **Fix**: Remove at least 60% of superlative intensifiers. Differentiate figures with specific praise: e.g., Грушевський's archival rigor, Липинський's political insight, Пріцак's institutional diplomacy. Use concrete adjectives instead of generic superlatives.

### Issue 3: Spelling Error — "переможцязами" (Line 18)
- **Location**: Line 18, Section «Вступ — Чому українська історіографія особлива?»
- **Original**: «Історія часто пишеться переможцязами, але українська традиція довела, що і переможені здатні зберегти свій голос.»
- **Problem**: "переможцязами" is a misspelling; correct form is "переможцями" (Instrumental plural of "переможець")
- **Fix**: Change «переможцязами» → «переможцями»

### Issue 4: Spelling Error — "академієчне" (Line 108)
- **Location**: Line 108, Section «Михайло Грушевський: II — Подолання імперської схеми»
- **Original**: «Ця порівняльна таблиця дуже наочно і просто демонструє, як нова концепція безперервності Грушевського повністю переформатувала європейське академієчне розуміння історії Східної Європи»
- **Problem**: "академієчне" is a misspelling; correct form is "академічне"
- **Fix**: Change «академієчне» → «академічне»

### Issue 5: Missing Negation — Syntactic Error (Line 143)
- **Location**: Line 143, Section «Львівська школа до 1939: Розбудова інституцій»
- **Original**: «Цей глибокий дослідник фактично першим у науці почав розглядати Галицьке князівство скоріше як якесь дрібне регіональне утворення, а як потужну, повноцінну європейську державу свого часу»
- **Problem**: The sentence says the opposite of what is intended. "скоріше як якесь дрібне" without a preceding "не" means he DID view it as minor. Context requires the meaning: "not as a minor entity, but as a powerful state."
- **Fix**: Change «скоріше як якесь дрібне регіональне утворення» → «не як якесь дрібне регіональне утворення»

### Issue 6: Missing Plan Content — Дмитро Дорошенко
- **Location**: Section «Діаспорна історіографія: I — Персоналії та великі ідеї» — entirely absent
- **Original**: N/A — figure is not mentioned anywhere in the content
- **Problem**: The plan explicitly requires "Дмитро Дорошенко — популяризатор" as a diaspora subsection. The meta outline specifies "Дмитро Дорошенко та його роль як видатного популяризатора національної історії за кордоном." Completely absent from content.
- **Fix**: Add a subsection on Дмитро Дорошенко in Section «Діаспорна історіографія: I — Персоналії та великі ідеї», covering his role as a popularizer of Ukrainian history abroad and his key works.

### Issue 7: Missing Plan Content — Грушевський's Tragic Fate
- **Location**: Section «Михайло Грушевський: II — Подолання імперської схеми» — absent
- **Original**: N/A — no mention of return to USSR, repressions, or death in 1934
- **Problem**: Both the plan and meta outline require "Трагічна доля вченого: повернення до СРСР, репресії проти істориків та смерть у 1934 році." This is a critical narrative beat — the architect of the national scheme meeting his end at the hands of the system he tried to work within. Completely absent.
- **Fix**: Add subsection or significant paragraph about Грушевський's return to Soviet Ukraine, persecution, and death in 1934.

### Issue 8: Missing Plan Content — Destruction of Lviv School 1939
- **Location**: Section «Львівська школа до 1939: Розбудова інституцій» — absent
- **Original**: N/A — no mention of the Soviet occupation's impact on the school
- **Problem**: The plan requires "Знищення школи — радянська окупація 1939." The section title references "до 1939" but never explains what happened IN 1939. This is a dramatic narrative arc that the content simply drops.
- **Fix**: Add a closing subsection about the Soviet occupation of Western Ukraine in 1939 and the destruction/suppression of the Lviv historical school.

### Issue 9: Activity Typo — "просопографіїчного"
- **Location**: Activities YAML, line 99
- **Original**: «просопографіїчного методу»
- **Problem**: Misspelling; correct form is "просопографічного"
- **Fix**: Change «просопографіїчного» → «просопографічного»

### Issue 10: HURI Founding Date Conflation
- **Location**: Line 194, Section «Діаспорна історіографія: II — Інституційний захист»
- **Original**: «У 1968 році, завдяки його нелюдським зусиллям та дипломатичному таланту, було урочисто засновано Український науковий інститут Гарвардського університету (HURI).»
- **Problem**: HURI was established in 1973, not 1968. In 1968, the three Chairs of Ukrainian Studies were endowed at Harvard. The research notes also contain this error (1968), but historically HURI's founding is 1973.
- **Fix**: Clarify: "У 1968 році було засновано кафедри українознавства, а в 1973 році — Український науковий інститут Гарвардського університету (HURI)."

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 18 | «переможцязами» | «переможцями» | Spelling |
| 108 | «академієчне» | «академічне» | Spelling |
| 143 | «скоріше як якесь дрібне регіональне утворення, а як» | «не як якесь дрібне регіональне утворення, а як» | Missing negation |
| act:99 | «просопографіїчного» | «просопографічного» | Spelling (activities) |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? [Pass] — C1-level complexity appropriate, terms defined inline
- Instructions clear? [Pass] — clear academic register throughout
- Quick wins? [Pass] — engaging decolonization theme creates immediate stakes
- Ukrainian scary? [Pass] — fully immersive, no scaffolding issues at C1
- Come back tomorrow? [Fail] — structural monotony causes fatigue; the identical paragraph structure across 30 subsections makes one stop wanting to read

## Strengths
- **Excellent decolonization framing**: The [!decolonization] block at line 44 in Section «Вступ — Чому українська історіографія особлива?» masterfully shifts the analytical lens from imperial to sovereign perspective.
- **Strong comparison tables**: The imperial vs. national scheme table in Section «Михайло Грушевський: II — Подолання імперської схеми» (lines 101-107) and the Snyder table (lines 243-248) in Section «Західні історики України: Революція сприйняття» are genuinely useful pedagogical tools.
- **Comprehensive institutional coverage**: The thread from НТШ → УВАН → HURI in sections «Львівська школа до 1939: Розбудова інституцій» through «Діаспорна історіографія: II — Інституційний захист» effectively demonstrates how Ukrainian scholarship survived through institutional resilience.
- **Rich callout variety**: 15 unique callout boxes across the module provide genuine enrichment (e.g., [!warning] on "Мазепинство" at line 172, [!tip] on archival methodology at line 259).
- **Good activity variety**: 5 activity types covering reading comprehension, critical analysis, essay writing, factual verification, and comparative study.

## Fix Plan to Reach 9/10 (REQUIRED if score < 9.0)

### LLM Fingerprint: 5/10 → 8/10
**What to fix:**
1. **Break the formula**: No more than 10 of 30 subsections should use the bold-definition opening. Vary with: opening questions ("Чому Крип'якевич відмовився від академічного стилю вчителя?"), anecdotes, primary source excerpts, dramatic scenes.
2. **Eliminate paired examples**: Remove `_Приклад 1:_` / `_Приклад 2:_` from at least 20 of 30 subsections. Replace with: inline illustrations, student reflection prompts, primary source quotes woven into narrative, comparative mini-tables, or nothing — let the prose speak.
3. **Reduce superlatives by 60%+**: Replace "геніальний Грушевський" with specific attributes. Replace "надзвичайно" with precise language. "Абсолютно" should appear ≤5 times total.

**Expected score after fix:** 8/10

### Linguistic Accuracy: 7/10 → 9/10
**What to fix:**
1. Line 18: «переможцязами» → «переможцями»
2. Line 108: «академієчне» → «академічне»
3. Line 143: «скоріше як якесь дрібне регіональне утворення» → «не як якесь дрібне регіональне утворення»
4. Activities line 99: «просопографіїчного» → «просопографічного»
5. Reduce hagiographic register: remove or vary "геніальний" (currently 12×), "видатний" (used as generic filler), "беззаперечний" (9×) — replace with specific, varied characterizations.

**Expected score after fix:** 9/10

### Language: 7/10 → 9/10
**What to fix:**
1. Systematic superlative reduction (see LLM fix above — this is the same root cause).
2. Fix the 3 spelling/syntactic errors listed.
3. Introduce register variation: some paragraphs should be more analytical/cool, others more passionate — currently everything is at maximum intensity uniformly.

**Expected score after fix:** 9/10

### Experience Quality: 7/10 → 9/10
**What to fix:**
1. Structural variety (covered by LLM fix above).
2. Add missing narrative arc elements: Грушевський's tragic death (emotional climax for the Грушевський sections), destruction of Lviv school 1939 (dramatic resolution for that section).
3. Add Дмитро Дорошенко as required by plan.
4. Strengthen closing — current підсумок (lines 312-316) is a recap rather than a "call to action." Add a memorable closing reflection on what the learner can now do with this knowledge.

**Expected score after fix:** 9/10

### Coherence: 8/10 → 9/10
**What to fix:**
1. Add the 3 missing plan points (Дорошенко, Грушевський's fate, 1939 destruction).
2. The transition from Section «Михайло Грушевський: II — Подолання імперської схеми» to Section «Львівська школа до 1939: Розбудова інституцій» needs Грушевський's tragic ending as a bridge.

**Expected score after fix:** 9/10

### Pedagogy: 7/10 → 9/10
**What to fix:**
1. Break the definition-first pattern (covered by LLM fix).
2. Add 2-3 student reflection prompts mid-lecture (not just at the end in "Перевірте себе").
3. Section «Нова історіографія: II — Інституційне становлення держави» could use a mini-exercise: "Подивіться на карту перейменованих вулиць у вашому місті. Знайдіть хоча б одну, пов'язану з декомунізацією."

**Expected score after fix:** 9/10

### Factual Accuracy: 8/10 → 9/10
**What to fix:**
1. Line 194: Clarify HURI founding — chairs 1968, institute 1973.
2. Line 176: Verify Polons'ka-Vasylenko publication dates (likely 1972-1976, not 1971-1972).

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
Experience 9 × 1.5 = 13.5
Coherence 9 × 1.0 = 9.0
Relevance 9 × 1.0 = 9.0
Educational 9 × 1.2 = 10.8
Language 9 × 1.1 = 9.9
Pedagogy 9 × 1.2 = 10.8
Immersion 10 × 1.0 = 10.0
Activities 9 × 1.3 = 11.7
Richness 9 × 0.9 = 8.1
Beginner Safety 9 × 1.3 = 11.7
LLM Fingerprint 8 × 1.0 = 8.0
Linguistic Accuracy 9 × 1.5 = 13.5
Factual Accuracy 9 × 1.5 = 13.5
Total = 139.5 / 15.5 = 9.0/10
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: YES (minimal — dates and one primary quote)
- Dates checked: 8 (1 discrepancy: HURI 1968 vs. actual 1973; 1 concern: Polons'ka-Vasylenko 1971-1972)
- Named figures verified: 15 (Грушевський, Антонович, Крип'якевич, Томашівський, Кордуба, Липинський, Оглоблин, Полонська-Василенко, Пріцак, Субтельний, Маґочі, Снайдер, Кульчицький, Гриневич, Винниченко — all real, correctly attributed)
- Primary quotes cross-referenced: 1/1 matched (Грушевський's approach re: народ as subject — paraphrased in content line 79, matches research Key Facts Ledger spirit)
- Chronological sequence: CONSISTENT — logical progression from 1894 → 1898 → 1904 → pre-1939 → 1945 → 1968 → 1988 → 1991 → 2006
- Claims without research grounding: 3 found:
  - Line 194: HURI founding in "1968" — research notes confirm this date, but historically inaccurate (chairs 1968, HURI 1973)
  - Line 176: Polons'ka-Vasylenko "1971-1972" — not in research notes, historically vol.1 was 1972 and vol.2 was 1976
  - Line 200: «потужна наукова кафедра в Гарварді в перспективі дієвіша за будь-який батальйон озброєних солдатів» — dramatic claim not grounded in any research source; editorial embellishment

## Verification Summary

- Content lines read: 326
- Activity items checked: 5 activities (reading, critical-analysis, essay-response, true-false with 12 items, comparative-study)
- Ukrainian sentences verified: 60+ (all example sentences, all callout boxes, key narrative sentences)
- IPA transcriptions checked: 30 (vocabulary file — spot-checked "бездержавний" — stress position plausible)
- Factual claims verified: 15+ (dates, attributions, institutional facts)
- Issues found: 10

## Verdict

**FAIL**

Two auto-fail dimensions: **LLM Fingerprint 5/10** (all 30 subsections follow identical bold-definition → paired-examples formula; "геніальний" applied to 4+ figures indiscriminately; "надзвичайно" ×26) and **Linguistic Accuracy 7/10** (3 spelling/syntactic errors: "переможцязами," "академієчне," missing negation line 143). Additionally, 3 plan-required content points are absent (Дмитро Дорошенко, Грушевський's tragic fate, 1939 destruction of Lviv school). The structural monotony is the primary blocking issue — this needs radical restructuring of subsection formats to read as a seminar lecture rather than a templated encyclopedia.

---

## Audit Failures (from automated re-audit)

```
VERDICT: FAIL
overall status is 'fail' (must be 'pass')
Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
failing gates:
review: Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ [REVIEW_VERDICT_FAIL] Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
• Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/ukrainska-istoriohrafichna-tradytsiia-audit.log for details)
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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-hist/ukrainska-istoriohrafichna-tradytsiia.md
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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-hist/activities/ukrainska-istoriohrafichna-tradytsiia.yaml
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
