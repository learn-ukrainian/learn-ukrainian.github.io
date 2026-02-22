# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> **You have file system access.** Use Read and Grep to verify every fix against the actual file content.

---

## Context

A review identified issues in this module. Your job is to produce **exact FIND/REPLACE fix pairs** that resolve the issues. You are NOT writing a review — that was already done. Focus only on producing correct, targeted fixes.

---

## Files You Can Read (use Read tool)

1. **Content**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/my-world-objects.md`
2. **Activities**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/my-world-objects.yaml`
3. **Vocabulary**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/my-world-objects.yaml`

---

## Review (from Phase D.1)

# Рецензія: My World: Objects

**Reviewed-By:** claude-opus-4-6

**Level:** A1 | **Module:** 5
**Overall Score:** 8.4/10
**Status:** PASS
**Reviewed:** 2026-02-21

## Plan Verification

```
Plan-Content Alignment: PASS (with minor gaps)
- Sections: PASS — all 5 plan sections present as H2 headers (Вступ, Теорія, Практика, Культурний контекст, Використання)
- Vocabulary: 20/20 from plan (6 required + 6 recommended all present in vocab YAML); 12 extra words taught in content but MISSING from vocab file
- Grammar scope: PASS — demonstratives цей/той families, gender agreement, identification vs specification
- Objectives: PARTIAL — 3/4 met; "name 40 common household and everyday objects" (plan objective) not met (~24 introduced)
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Warm opening and closing but ~80 lines of theory (lines 52–133) before first interactive drill at line 221. Missing explicit "Today you'll learn..." preview. |
| 2 | Coherence | 9/10 | <7 | Logical progression: concept → grammar tables → vocabulary → cultural context → production. Clear transitions between sections. |
| 3 | Relevance | 9/10 | <7 | Directly useful everyday vocabulary (furniture, kitchen, personal items) and essential grammar (demonstratives). |
| 4 | Educational | 8/10 | <7 | Plan objective "40 objects" not met (~24 introduced). The Identification vs Specification distinction (lines 93–133) is excellently taught. |
| 5 | Language | 9/10 | <8 | Clean English at appropriate level. Ukrainian is grammatically correct throughout. Line 48 analogy ("handsome woman") slightly misleads about grammatical gender. |
| 6 | Pedagogy | 8/10 | <7 | PPP structure present but Presentation phase is long (~80 lines) before first Practice. Drill at line 221 is walkthrough, not interactive until activities. |
| 7 | Immersion | 7/10 | <6 | 13.0% measured vs 20-40% A1.1 target. Ukrainian appears mainly in examples and H2/H3 headers. Metalanguage is overwhelmingly English. |
| 8 | Activities | 8/10 | <7 | 9 activities with good variety (quiz, fill-in, group-sort, match-up, anagram). 94 total items. However, 12 content-taught words missing from vocab YAML means they aren't tracked for spaced repetition. |
| 9 | Richness | 8/10 | <6 | 5 distinct callout boxes ([!context], [!tip], [!warning], [!myth-buster], [!culture]). Покуття and хата/квартира/дім distinctions add cultural depth. |
| 10 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 4/5. Warm welcome, clear tables, encouraging closing. One miss: long theory section before first practice opportunity. |
| 11 | LLM Fingerprint | 8/10 | <7 | No structural monotony in section openings. No "це не просто" / "це не лише" rhetoric. Minor concern: "Example Usage:" pattern repeats identically across all four vocabulary subsections (lines 150, 162, 187, 201). |
| 12 | Linguistic Accuracy | 9/10 | <9 | IPA transcriptions verified against standard Ukrainian phonology — all correct including stress patterns. Ukrainian grammar in all example sentences is accurate. |
| 13 | Factual Accuracy | 9/10 | <8 | Покуття description accurate. Proverb «В гостях добре, а вдома краще» is authentic. двері as plurale tantum: correct. No fabricated cultural claims. |

**Weighted Overall:**
```
(8×1.5 + 9×1.0 + 9×1.0 + 8×1.2 + 9×1.1 + 8×1.2 + 7×1.0 + 8×1.3 + 8×0.9 + 9×1.3 + 8×1.0 + 9×1.5 + 9×1.5) / 15.5
= (12.0 + 9.0 + 9.0 + 9.6 + 9.9 + 9.6 + 7.0 + 10.4 + 7.2 + 11.7 + 8.0 + 13.5 + 13.5) / 15.5
= 130.4 / 15.5
= **8.4/10**
```

## Auto-Fail Checklist Results

- Russianisms: [CLEAN] — no Russianisms detected
- Calques: [CLEAN] — no calques detected
- Colonial framing: [CLEAN] — no Russian-as-baseline comparisons
- Grammar scope: [CLEAN] — adjectives used in examples (гострий, нова, etc.) but not formally taught; possessive мій used incidentally. Acceptable for contextual exposure.
- Activity errors: [CLEAN] — all 94 items have correct answers and explanations
- Beginner safety: 4/5
- Factual accuracy: [CLEAN] — all cultural claims verified as accurate

## Critical Issues Found

### Issue 1: Vocabulary File Gap — 12 Words Taught but Untracked
- **Location**: Lines 181–199, 243–245 (content) / vocabulary YAML (missing entries)
- **Problem**: The content formally teaches 12 words with IPA, gender labels, and example sentences (ніж, ложка, чашка, тарілка, блюдо, комп'ютер, сумка, ключі, окуляри, хата, квартира, дім) that are absent from the vocabulary YAML. These words cannot be tracked for spaced repetition or progress monitoring.
- **Fix**: Add all 12 words to `/curriculum/l2-uk-en/a1/vocabulary/my-world-objects.yaml` with IPA, POS, gender notes, and translations matching the content.

### Issue 2: Immersion Below A1.1 Target
- **Location**: Entire module
- **Problem**: Measured immersion at 13.0% falls below the A1.1 minimum of 20%. The module is excessively English-heavy, with Ukrainian appearing mainly in isolated examples and headers.
- **Fix**: Increase Ukrainian presence by: (a) adding short Ukrainian sentences with inline English glosses in the cultural context section; (b) using Ukrainian for simple instructions like «Подивіться на таблицю» (Look at the table) before grammar tables; (c) converting some English transition sentences to Ukrainian with translations.

### Issue 3: Long Theory Block Before First Practice
- **Location**: Lines 52–133 (Теорія section, ~80 lines)
- **Problem**: The Presentation/Theory section runs ~80 lines covering Near demonstratives, Far demonstratives, and the Це/Цей distinction before any practice opportunity. The first interactive drill (line 221) comes after an additional ~90 lines of vocabulary. For A1 beginners, this is a long cognitive load without a dopamine hit.
- **Fix**: Insert a mini-drill (3–4 items) between the Near and Far demonstrative tables (after line 71), so learners can practice the Ц-family before encountering the Т-family.

### Issue 4: Misleading Gender Agreement Analogy
- **Location**: Line 48
- **Original**: «If you try to use a masculine "this" with a feminine "book," it sounds as wrong to a Ukrainian ear as saying "This is a handsome woman" might sound in English—grammatically understandable, but strange!»
- **Problem**: This analogy confuses grammatical gender agreement (a morphosyntactic requirement) with semantic incongruity. Gender agreement errors in Ukrainian are grammatical mistakes (like "this are books"), not semantic oddities. The analogy may lead learners to think gender is about meaning rather than form.
- **Fix**: Replace with: "If you try to use a masculine 'this' with a feminine 'book,' it sounds as wrong to a Ukrainian ear as 'this are books' sounds in English—the grammar just doesn't match."

### Issue 5: Plan Objective "40 Objects" Not Met
- **Location**: Plan objective 4 / entire module
- **Problem**: The plan specifies "Learner can name 40 common household and everyday objects" but the content introduces only ~24 objects. The vocabulary YAML tracks only 12 nouns (plus 8 pronouns).
- **Fix**: Either (a) expand content to include 16+ additional household objects (bathroom, bedroom, office items) to reach 40, or (b) revise the plan objective to reflect a realistic scope (~25 objects).

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 223 | «Давайте потренуємося з'єднувати об'єкт із вказівним займенником.» | Sentence is grammatically correct. No change needed. | OK |
| 310 | «Ця фізична дія — вказувати і говорити — допомагає поєднати граматику з реальністю.» | Sentence is grammatically correct. No change needed. | OK |
| 298 | «Подивіться навколо себе. Знайдіть три предмети.» | Correct imperative forms. No change needed. | OK |
| 48 | N/A — English text | See Issue 4 above. | Pedagogy |

No Ukrainian grammar errors, Russianisms, or calques were found in the module's Ukrainian text.

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? **Pass** — Grammar presented in clean tables, vocabulary grouped by gender. Manageable chunks.
- Instructions clear? **Pass** — Always clear what the learner is expected to do. Excellent Identification vs Specification explanation.
- Quick wins? **Borderline Fail** — First interactive drill at line 221 comes after ~170 lines of theory + vocabulary. No mini-exercise between the two demonstrative tables.
- Ukrainian scary? **Pass** — Ukrainian introduced gently with English support throughout. IPA provided for every word.
- Come back tomorrow? **Pass** — Encouraging closing at line 316 with «Congratulations!» and clear progress summary.

## Strengths

- **Excellent Identification vs Specification teaching** (lines 93–133): The «Це стіл» vs «Цей стіл» distinction is the module's pedagogical crown jewel. The comparison table (line 120–123), warning box (lines 125–132), and the neuter trap explanation are all outstanding.
- **Mini-dialogue** (lines 208–219): The furniture store conversation naturally demonstrates the switch between Identification and Specification modes. This is exactly the kind of contextualized practice that makes grammar stick.
- **Cultural depth**: The Покуття / хата / квартира / дім section (lines 235–270) gives genuine cultural insight without being superficial. The shoe-removal detail (line 270) is a practical real-world preparation.
- **Callout box variety**: 5 distinct types ([!context], [!tip], [!warning], [!myth-buster], [!culture]) — no monotony.
- **Mnemonic quality**: «Ц is for Close, Т is for There» (lines 90–91) is genuinely helpful for retention.

## Fix Plan to Reach 9.0/10

### Immersion: 7/10 → 9/10
**What to fix:**
1. Lines 134–136: Add Ukrainian instruction before vocabulary lists: «Тепер подивимося на предмети в українському домі.» (Now let's look at objects in a Ukrainian home.)
2. Lines 272–274: Open the production section with a Ukrainian sentence: «Тепер ми все з'єднаємо!» (Now we'll put it all together!)
3. Add 3–4 more Ukrainian micro-instructions throughout (e.g., «Дивіться на таблицю:» before tables)
4. Target: raise from 13% to ~22%

**Expected score after fix:** 9/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. After line 71: Insert a 3-item mini-drill for the Ц-family before introducing the Т-family
2. Lines 15–17: Add explicit learning objectives: "Today you'll learn to point at specific objects using Ukrainian demonstrative pronouns."

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Break the theory section by inserting a quick practice after the Near demonstratives table (after line 71)
2. This addresses the core PPP pacing issue — learners practice the Ц-family before encountering the Т-family

**Expected score after fix:** 9/10

### Educational: 8/10 → 9/10
**What to fix:**
1. Revise plan objective from "40 objects" to "25 common household and everyday objects" (realistic scope)
2. Or expand content with additional vocabulary categories (bathroom: рушник, мило; bedroom: подушка, ковдра)

**Expected score after fix:** 9/10

### Activities: 8/10 → 9/10
**What to fix:**
1. Add 12 missing words (ніж, ложка, чашка, тарілка, блюдо, комп'ютер, сумка, ключі, окуляри, хата, квартира, дім) to vocabulary YAML
2. Consider adding 1 activity that specifically uses the kitchen/personal item vocabulary

**Expected score after fix:** 9/10

### LLM Fingerprint: 8/10 → 9/10
**What to fix:**
1. Vary the "Example Usage:" headers across the four vocabulary subsections (lines 150, 162, 187, 201). Use alternatives like "Спробуйте:", "У реченні:", "Вживання:"

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.0 + 9×1.0 + 9×1.2 + 9×1.1 + 9×1.2 + 9×1.0 + 9×1.3 + 8×0.9 + 9×1.3 + 9×1.0 + 9×1.5 + 9×1.5) / 15.5
= (13.5 + 9.0 + 9.0 + 10.8 + 9.9 + 10.8 + 9.0 + 11.7 + 7.2 + 11.7 + 9.0 + 13.5 + 13.5) / 15.5
= 138.6 / 15.5
= 8.9/10
```

## Factual Verification

- Research notes consulted: NOT_APPLICABLE (A1 core track, no research file)
- Key Facts Ledger present: NO
- Dates checked: 0 (no historical dates in content)
- Named figures verified: 0 (no historical figures referenced)
- Primary quotes cross-referenced: N/A
- Chronological sequence: N/A
- Claims without research grounding: N/A

**Callout box verification (all tracks):**
- [!myth-buster] «Чи телефон — чоловік?» (lines 230–233): Accurately explains grammatical vs natural gender. Uses «трубка» as feminine counterexample — correct. No fabrication.
- [!culture] «Гостинність» (lines 268–270): Shoe removal custom is widely documented. «поріг» (threshold) and «тапці» (slippers) are correct terms. No fabrication.
- [!context] «Візуалізація» (lines 35–38): Pedagogical visualization, no factual claims.
- [!tip] «Звукова асоціація» (lines 88–91): Mnemonic device, no factual claims.
- [!warning] «Don't Mix Them Up!» (lines 125–132): Grammar explanation is accurate.

## Verification Summary

- Content lines read: 335
- Activity items checked: 94 (across 9 activities)
- Ukrainian sentences verified: 28
- IPA transcriptions checked: 24
- Factual claims verified: 5 (cultural claims in callout boxes)
- Issues found: 5

## Verdict

**PASS**

The module delivers a well-structured, pedagogically sound lesson on demonstrative pronouns with excellent grammar tables, a standout Identification vs Specification section, and genuine cultural depth. The five issues identified — vocabulary file gap (12 untracked words), below-target immersion (13% vs 20%), long theory-before-practice pacing, a misleading analogy, and an unmet plan objective — are all fixable without restructuring the module. No auto-fail thresholds are triggered.

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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/my-world-objects.md
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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/my-world-objects.yaml
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
