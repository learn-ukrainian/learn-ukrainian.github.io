# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> **You have file system access.** Use Read and Grep to verify every fix against the actual file content.

---

## Editing Principles

- **IMPROVE, don't destroy.** Every rewrite should teach MORE than the original, not less.
- **PRESERVE the author's intent.** If a paragraph explains something poorly, rewrite it to explain it well — don't delete it.
- **MATCH the surrounding voice.** Your rewrite should read like the original author wrote it on a better day.
- Only DELETE truly empty sentences (pure cheerleading with zero information that cannot be salvaged). This should be rare.

---

## Track Calibration

# Track Calibration: A1

## Bilingual Scope
A1 uses PROGRESSIVE immersion — targets increase per module:
- Modules 1-2: 5-15% Ukrainian (Cyrillic intro, mostly English)
- Modules 3-5: 10-25% Ukrainian (early vocab building)
- Modules 6-10: 15-35% Ukrainian (growing immersion)
- Modules 11-20: 25-40% Ukrainian (foundation established)
- Modules 21+: 35-55% Ukrainian (consolidation)

Mixing English explanations with Ukrainian examples is CORRECT pedagogy.
Do NOT flag bilingual content as LANGUAGE_BLENDER.
Flag: Full Ukrainian paragraphs that exceed the module's immersion band.
Flag: Modules that are below their minimum immersion target.

## Russicism Lookup (A1-specific)
These appear frequently in A1 content. Flag as HIGH:
- здача → решта (change/money)
- тапочки → капці (slippers)
- кушати → їсти (to eat)
- давайте попрактикуємо → попрактикуймо (let's practice — Russian imperative calque)
- давайте повторимо → повторімо (let's repeat — Russian imperative calque)
- давайте подивимося → подивімося (let's look — Russian imperative calque)
- чоловіче → пане (sir — register mismatch in service contexts)
- надіятися → сподіватися (to hope)
- піднімається → підводиться (gets up)
- получати → отримувати (to receive)
- вообще → взагалі (in general)

## Anglicism Lookup (A1-specific)
- "Що ви хочете?" → "Що бажаєте?" (register in service/hospitality contexts)
- "роблять каву" → "готують каву" (make coffee — English calque)
- "робити добру каву" → "готувати смачну каву" (make good coffee)

## LLM Filler Sensitivity
At A1, some motivational content is ACCEPTABLE when woven into teaching.
Flag ONLY: pure cheerleading with zero educational content, generic padding
("Numbers are everywhere", "Language is not just about labeling things",
"As you continue your Ukrainian journey").
Do NOT flag: warm encouragement that includes a teaching point.

## Content Focus
Simple sentences are expected. Don't flag short paragraphs.
Focus on: Russianisms, factual errors in callouts, and fluff replacing actual teaching.
Do NOT penalize: friendly tone, bilingual explanations, basic vocabulary presentation.


---

## Files You Can Read (use Read tool)

1. **Content**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/at-the-market.md`
2. **Activities**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/at-the-market.yaml`
3. **Vocabulary**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/at-the-market.yaml`

---

## Review (from Phase D.1)

**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Key Evidence |
|---|-----------|-------|--------------|
| 1 | **Language Quality** | 8/10 | Ukrainian grammar is mostly correct. Key issue: Russicism «здача» in vocabulary YAML (line 46) and activities YAML (lines 175-176, 275-276) contradicts the lesson content which correctly teaches «решта» (line 241, 258). The lesson itself is well-written but the supporting files undermine it. |
| 2 | **Lesson Quality** | 8/10 | Warm, engaging tutor voice. Cultural hooks are excellent (Bessarabsky, Pryvoz). Missing explicit "today you'll learn" preview at the top. The narrative section «Історія: Мій похід на Привоз» is vivid. Slight weakness: no explicit learning objectives before content begins. |
| 3 | **Factual Accuracy** | 8/10 | Bessarabsky market founding "Built in 1912" is acceptable (research says 1910-1912 construction period). However, "one of the first indoor refrigeration systems in Eastern Europe" (line 31) is an embellishment — research states «Перший критий ринок з холодильними камерами» (first covered market with refrigeration chambers) without the "Eastern Europe" qualifier. Pryvoz 1827 date confirmed. Plan requires «легенда про слона Мурзу» which is entirely absent from content. |
| 4 | **Immersion** | 9/10 | 35.2% Ukrainian — within the 35-55% target band for A1 module 37. English scaffolding is well-balanced. Every Ukrainian sentence has a parenthetical English translation. Good progressive immersion in the story section where translations become sparser. |
| 5 | **Activity Quality** | 7/10 | 10 activities with good variety (match-up, group-sort, quiz, fill-in, unjumble, true-false). Critical defect: two unjumble activities use Russicism «здача» (activities lines 175-176, 275-276) while the lesson teaches «решта». Fill-in activities are pedagogically sound with good distractor options. Some quiz questions test content recall rather than language (e.g., line 57: «Що таке знаменитий історичний «Привоз»?», line 79: «Де саме знаходиться знаменитий Бессарабський ринок?»). |
| 6 | **Richness** | 7/10 | 81% vs 95% threshold. Gaps: cultural 2/3 (need 1 more `[!culture]` callout), dialogues 0/4 (dialogues exist in content but may not be detected by richness checker). Has 5 engagement boxes: `[!culture]`, `[!tip]`, 2x `[!warning]`, `[!observe]`, `[!myth-buster]`. Missing a `[!did-you-know]` or additional `[!culture]` box. |
| 7 | **Vocabulary Coverage** | 4/10 | **CRITICAL**: Vocabulary YAML is structurally malformed. File uses bare `lemma:` keys without list markers (`-`) and without the `items:` root key (compare with working format in `at-the-restaurant.yaml` which uses `items: - lemma:`). Result: audit reads 0 vocabulary items. Additionally, lemma «здача» (vocab line 46) is a Russicism — should be «решта». Words taught in lesson but missing from vocab: «літр», «пляшка», «пакет», «базар», «готівка» is present but «картка» is missing. |
| 8 | **LLM Fingerprint** | 8/10 | Section openings are varied (no structural monotony). No "не просто X, а Y" patterns found. No "давайте" calques found. Minor flags: "beating heart of the community" (line 13) is a common AI cliché in English; «серце міста» (line 17) is more natural Ukrainian but appears adjacent to the English cliché. Example formatting varies well across sections (word lists, tables, dialogues, narrative). |
| 9 | **Humanity & Warmth** | 9/10 | Direct address (ви) used extensively (15+ instances). Encouragement phrases present: «Це легко» (line 78), «Спробуйте самі» (line 78), «Не соромтеся питати» (line 212), «Не бійтеся» (line 26). Summary section with «Тепер ви знаєте» (line 306) serves as progress celebration. "Don't worry" moments: «Не бійтеся» and «don't panic» (line 51). |
| 10 | **Plan Compliance** | 7/10 | Content follows meta sections, not plan sections. Plan requires "легенда про слона Мурзу" (plan section 1, Pryvoz points) — **entirely absent**. Plan section 3 "Мовні помилки та практика" calls for explicit «Здача» vs «Решта» learner error drill and genitive vs nominative correction exercises — these are partially covered but not as a dedicated section. Plan point about buying "поштучно" (by piece) scenario not demonstrated in any dialogue despite «штука» being taught. |

---

## Critical Issues Found

### Issue 1: CRITICAL — Vocabulary YAML Structurally Malformed (0 items parsed)

**Location:** `/curriculum/l2-uk-en/a1/vocabulary/at-the-market.yaml`, entire file
**Severity:** CRITICAL (audit gate: Vocab ❌)

The vocabulary file uses bare `lemma:` keys without YAML list markers. Compare:

**Current (BROKEN):**
```yaml
  lemma: ринок
  pos: noun
  gender: m
```

**Required (working format from at-the-restaurant.yaml):**
```yaml
items:
  - lemma: 'ринок'
    pos: 'noun'
    gender: 'm'
```

The file has 23 entries, all unparseable. This causes the audit to report "Vocabulary items: 0" and fail the vocab gate.

**Fix:** Reformat entire vocabulary YAML with `items:` root key and `-` list markers for each entry.

---

### Issue 2: HIGH — Russicism «здача» in Activities and Vocabulary

**Location:** Activities YAML lines 175-176, 275-276; Vocabulary YAML line 46
**Severity:** HIGH (Russicism — per A1 calibration lookup table)

The lesson content **correctly** teaches «решта» on line 241: «**Решта — це ваші гроші назад.**» and uses it in dialogue on line 258: «**Продавець:** Дякую. Ваша решта — шістдесят.»

However, the activities directly contradict this:
- Unjumble activity line 175-176: `words: ["Ваша", "здача", "шістдесят", "гривень"]` → answer: `"Ваша здача шістдесят гривень"`
- Unjumble activity line 275-276: `words: ["Ось", "ваша", "здача"]` → answer: `"Ось ваша здача"`
- Vocabulary YAML line 46: `lemma: здача`

This teaches learners the Russicism the lesson explicitly avoids. All instances of «здача» must be replaced with «решта».

---

### Issue 3: MEDIUM — Plan Requirement Missing: "легенда про слона Мурзу"

**Location:** Plan section 1 requires Pryvoz "легенда про слона Мурзу" — not present anywhere in content
**Severity:** MEDIUM (plan compliance gap)

The plan file (`plans/a1/at-the-market.yaml`, line 14) specifies Pryvoz content should include «легенда про слона Мурзу». Grep for "Мурз" returns no matches in the content file. The Pryvoz section (lines 33-36) covers humor and etymology but omits this cultural detail entirely.

**Fix:** Add 2-3 sentences about the Murza elephant legend to the section «Привоз: The Soul of Odesa» or as a `[!did-you-know]` callout (which would also close the cultural richness gap).

---

### Issue 4: MEDIUM — Unverified Factual Embellishment

**Location:** Line 31, section «Бессарабський ринок: The "Aristocrat"»
**Severity:** MEDIUM (factual accuracy)

Content states: "featuring one of the first indoor refrigeration systems in Eastern Europe"

Research notes state: «Перший критий ринок з холодильними камерами» (first covered market with refrigeration chambers).

The differences: (1) Research says "first" not "one of the first"; (2) Research does not include the "in Eastern Europe" qualifier; (3) "indoor refrigeration systems" is a paraphrase of "холодильні камери" (refrigeration chambers). The "Eastern Europe" claim is unsourced and potentially fabricated.

**Fix:** Replace with "featuring the first refrigeration chambers in a covered market" or similar wording that matches the research.

---

### Issue 5: LOW — Richness Gaps (cultural 2/3, dialogues 0/4)

**Location:** Across entire content file
**Severity:** LOW-MEDIUM (richness gate: 81% < 95% threshold)

Currently 2/3 cultural callouts: `[!culture]` (line 24) and `[!myth-buster]` (line 43). Need 1 more cultural element. The Murza legend (Issue 3) could serve as a `[!did-you-know]` to close both gaps simultaneously.

Dialogue richness 0/4 likely indicates the richness checker doesn't detect the inline dialogue format. Content has 3 full dialogues (Dialogue 1: lines 188-208, Dialogue 2: lines 214-228, Payment: lines 243-259) that are pedagogically sound.

**Fix:** Add one `[!did-you-know]` or `[!culture]` callout (e.g., Murza legend). Investigate why dialogue richness checker reports 0/4 — may need structural markup changes.

---

## Factual Verification

| Claim | Source Check | Status |
|-------|-------------|--------|
| Bessarabsky market built in 1912 | Research: "1910-1912 рр." — construction period, so 1912 completion is acceptable | ✅ PASS |
| Bessarabsky on Khreshchatyk | Well-known, confirmed by research | ✅ PASS |
| "Дорого, як на Бессарабці" saying | Research: confirmed «"дорого, як на Бессарабці"» | ✅ PASS |
| Pryvoz established 1827 | Research: confirmed «1827 р.» | ✅ PASS |
| Pryvoz name from "привозити" | Research: confirmed «Назва від "привозити" (продаж з возів)» | ✅ PASS |
| "one of the first indoor refrigeration systems in Eastern Europe" | Research says «Перший критий ринок з холодильними камерами» — NO "Eastern Europe" qualifier | ⚠️ EMBELLISHED |
| Elephant Murza legend at Pryvoz | Plan requires it, NOT present in content | ❌ MISSING |
| «Морква з городу смачніша.» (line 41) — grammar | Comparative "смачніша" is correct feminine form matching "морква" (f) | ✅ PASS |
| «Хлопче! Чого стоїмо?» (line 282) — vocative | "Хлопче" is correct vocative of "хлопець" | ✅ PASS |
| «Тут пахне рибою і кропом.» (line 278) — instrumental | "рибою" and "кропом" are correct instrumental forms | ✅ PASS |

---

## Verification Summary

| Check | Result | Details |
|-------|--------|---------|
| Russianisms scanned | ⚠️ FOUND | «здача» in vocab YAML (line 46) and activities YAML (lines 175-176, 275-276). Lesson correctly uses «решта». No «давайте» calques found. |
| Colonial framing | ✅ CLEAN | No "Unlike Russian..." patterns. No Russian comparisons. |
| LLM fingerprint | ✅ CLEAN | No structural monotony. No "не просто" repetitions. Minor English cliché "beating heart" (line 13) acceptable at A1. |
| Factual accuracy | ⚠️ 1 ISSUE | "Eastern Europe" qualifier on Bessarabsky refrigeration claim is unsourced. Murza legend required by plan but absent. |
| Grammar correctness | ✅ CLEAN | All Ukrainian sentences verified — correct case endings, verb forms, adjective agreement. |
| Activity errors | ⚠️ FOUND | Russicism «здача» in 2 unjumble activities; some quiz questions test content recall but acceptable for A1. |
| Vocabulary file | ❌ BROKEN | YAML malformed — missing `items:` root and `-` list markers. 0 items parsed. |
| Word count | ✅ PASS | 2700/2000 (135%) — exceeds minimum. |
| Section coverage | All 4 H2 sections verified: «Вступ: Культура українського ринку», «Лексика та Граматика: Як купувати?», «Практика: Діалоги на ринку», «Історія: Мій похід на Привоз» | All present and substantive. |
| Warmth markers | ✅ PASS | Direct address (ви) 15+, encouragement phrases 5+, "don't worry" moments 2+. |

---

## Verdict

**FAIL — 3 issues must be resolved before PASS**

### Blocking Issues (must fix):

1. **Vocabulary YAML malformed** — Entire file needs reformatting with `items:` root key and `-` list markers. Currently 0/23 items parseable. Also add missing entries: «літр», «пляшка», «пакет», «картка», «базар». Replace «здача» with «решта».

2. **Russicism «здача» in activities** — Replace with «решта» in both unjumble activities (lines 175-176: `"Ваша здача шістдесят гривень"` → `"Ваша решта шістдесят гривень"`; lines 275-276: `"Ось ваша здача"` → `"Ось ваша решта"`).

3. **Richness gap** — Add 1 `[!did-you-know]` or `[!culture]` callout. Recommended: add the Murza elephant legend from the plan as a `[!did-you-know]` in section «Привоз: The Soul of Odesa» — this simultaneously closes the cultural richness gap and the plan compliance gap.

### Non-Blocking Recommendations:

4. Fix "Eastern Europe" factual embellishment (line 31) to match research wording.
5. Consider adding an explicit "Today you'll learn..." preview paragraph after the opening epigraph for beginner safety.

### What Works Well:

- Excellent cultural hooks (Bessarabsky, Pryvoz, "Спробуйте!" culture)
- Warm, patient tutor voice throughout
- The narrative section «Історія: Мій похід на Привоз» is vivid and uses natural Odesa speech patterns (vocative «Хлопче!», ти-form from vendors)
- Grammar is taught as memorizable chunks ("кілограм картоплі") rather than dry theory — perfect for A1
- Quality adjective table (line 154-158) with gender agreement is clear and visual
- The `[!warning]` about not using "Я хочу..." (line 182-183) is culturally accurate and pedagogically valuable
- Strong fill-in activities with well-designed distractors (activities lines 124-159)

---

## Audit Failures (from automated re-audit)

```
VERDICT: FAIL
overall status is 'fail' (must be 'pass')
failing gates:
lesson: 2700/2000 (raw: 2998) | pedagogy: 2 violations
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
→ 2 violations (minor)
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/at-the-market-audit.log for details)
```

---

## Instructions

1. Read the content file using the Read tool
2. For each issue identified in the review OR in the audit failures:
   a. Use Grep to find the exact text that needs fixing
   b. Produce a FIND/REPLACE pair with verbatim FIND text
3. Only fix issues documented above — no silent extra changes
4. Prioritize fixes by impact: audit gate failures first, then review issues
5. For Russianisms: replace with the standard Ukrainian form from the calibration table

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded.

```
===SECTION_FIX_START===
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/at-the-market.md
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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/at-the-market.yaml
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
