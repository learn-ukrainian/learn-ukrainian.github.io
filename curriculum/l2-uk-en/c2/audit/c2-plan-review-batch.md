# C2 Plan Review -- Batch Report (91 Plans)

**Track:** C2 | **Plans reviewed:** 91 (sequences 1-91) | **Version:** 2.0
**Reviewer:** Claude Opus 4.6 | **Date:** 2026-03-05 | **Reference:** Issue #729

**Overall Verdict: NEEDS FIXES -- 7 CRITICAL, 5 HIGH, 6 MEDIUM issues found**

---

## Executive Summary

The C2 plan set (91 modules across 4 phases: C2.1 Stylistics & Rhetoric, C2.2 Literature & Creative Writing, C2.3 Professional Language, C2.4 Meta-Skills & Capstone) is structurally sound with good sequencing, no gaps, and no duplicates. However, a set of systematic template-level issues affects the majority of plans. These are fixable via batch edits.

---

## 1. Rule Compliance

### 1.1 word_target

| Check | Status | Details |
|-------|--------|---------|
| C2 regular modules (84) | PASS | All 84 non-checkpoint plans have word_target: 5000, matching config.py `C2: 5000` |
| **C2 checkpoint modules (7)** | **FAIL** | All 7 checkpoints have word_target: 5000, but config.py says `C2-checkpoint: 4000` |

**CRITICAL -- 7 plans affected:**
- `c1-bridge-assessment` (seq 1, focus: checkpoint)
- `c2-1-checkpoint` (seq 26)
- `c2-2-checkpoint` (seq 43)
- `c2-3-checkpoint` (seq 64)
- `c2-3-midpoint-checkpoint` (seq 53)
- `c2-riven-zaversheno` (seq 91)
- `final-exam-integrated-skills` (seq 89)

**Fix:** Change `word_target: 5000` to `word_target: 4000` in all 7 checkpoint plans, and adjust section budgets proportionally.

**Note:** `c1-bridge-assessment` (seq 1) has `focus: checkpoint` but functions as a diagnostic/bridge module. Consider whether it should actually be classified as checkpoint or regular C2.

### 1.2 Section budget sums

| Check | Status | Details |
|-------|--------|---------|
| section_budgets | PASS | All 91 plans have section word sums within +/-10% of word_target |

### 1.3 Required fields

| Check | Status | Details |
|-------|--------|---------|
| required_fields | **FAIL** | `grammar` field missing from 90 of 91 plans; `register` field missing from 90 of 91 plans |
| subtitle | INFO | Missing from 85 of 91 plans (6 have it) |

**CRITICAL -- 90 plans missing `grammar:` and `register:` fields.** Only `advanced-rhetoric` has both. The plan review prompt lists these as required fields per the schema. However, because this is a level-wide template issue (not individual plan oversight), this may reflect a design decision where these fields were considered optional at C2. Needs clarification.

### 1.4 Version string

| Check | Status | Details |
|-------|--------|---------|
| version_string | PASS | All 91 plans have `version: '2.0'` (properly quoted string) |

---

## 2. State Standard Alignment

### 2.1 Grammar scope

All C2 plans cover topics within the C2 State Standard scope (lines 5326-5739). Key alignments verified:

| Plan Topic Area | Standard Reference | Status |
|----------------|-------------------|--------|
| Complete style system (7 functional styles) | SS C2 `4.3.1.1` (lines 5666-5673) | PASS |
| Phonetic stylistics (euphony, rhythm) | SS C2 `4.3.2` (lines 5675-5680) | PASS |
| Lexical stylistics (all tropes) | SS C2 `4.3.3` (lines 5682-5712) | PASS |
| Syntactic stylistics (all figures) | SS C2 `4.3.4` (lines 5714-5729) | PASS |
| Rhetoric | SS C2 `4.3.5` (line 5731) | PASS |
| Style creation | SS C2 `4.3.6` (lines 5733-5733) | PASS |
| Style transformation | SS C2 `4.3.7` (lines 5735-5736) | PASS |
| Secondary texts | SS C2 `4.3.8` (lines 5738-5739) | PASS |
| Complete morphology (archaic, dialectal) | SS C2 `4.1.1` (lines 5326-5423) | PASS |
| All cases -- complete mastery | SS C2 `4.1.2` (lines 5428-5584) | PASS |
| Complex/asyndetic syntax | SS C2 `4.2.4-4.2.5` (lines 5632-5660) | PASS |

### 2.2 Thematic catalogue

All C2 thematic areas are covered across the 91 modules, including professional, academic, literary, translation, and cultural contexts.

### 2.3 Missing State Standard coverage

| Standard Requirement | Coverage in Plans | Status |
|---------------------|-------------------|--------|
| One-member sentences as stylistic device (`4.2.3`) | Not explicitly addressed in any plan | **MEDIUM** |
| Complete pronoun mastery -- archaic forms (`4.1.1.4`) | Covered in `rare-archaic-forms` (seq 66) | PASS |
| Complete numeral mastery (`4.1.1.3`) | No dedicated module; `complete-grammar-review` (seq 65) may touch it | **LOW** |

---

## 3. Grammar Verification (Textbook RAG)

### 3.1 Euphony (milozvchnist-complete)

Verified against Grade 10 textbooks (Karaman 2018, Glazova 2018):
- Plan correctly describes у/в and і/й alternation rules
- Plan correctly identifies "зіяння" (hiatus) and "збіг приголосних" (consonant clusters)
- з/зі/із variation rules match textbook descriptions (Karaman p. 59)
- **PASS**

### 3.2 Syntactic stylistics (syntactic-stylistics)

- Парцеляція, еліпсис, градація, паралелізм, інверсія -- all correctly described
- Тема-рема structure correctly referenced
- Literary examples (Шевченко, Коцюбинський, Стефаник) are appropriate
- **PASS**

### 3.3 Lexical stylistics (lexical-stylistics)

- Синонімія, антонімія, омонімія, паронімія -- all correctly categorized
- Paronym examples verified: "військовий" vs "воєнний", "тактовний" vs "тактичний" -- correct
- Anti-calque examples verified: "рахувати" for "вважати" is indeed a common calque to correct
- **PASS**

---

## 4. Vocabulary Verification

### 4.1 VESUM checks (sampled across 6 plans)

| Word | VESUM | Plan(s) | Status |
|------|-------|---------|--------|
| милозвучність | OK (noun:f) | milozvuchnist-complete | PASS |
| парцеляція | OK (noun:f) | syntactic-stylistics | PASS |
| апосіопеза | OK (noun:f) | syntactic-stylistics | PASS |
| епіфора | OK (noun:f) | syntactic-stylistics | PASS |
| полісиндетон | OK (noun:m) | syntactic-stylistics | PASS |
| зіяння | OK (noun:n) | milozvuchnist-complete | PASS |
| антиметабола | OK (noun:f) | advanced-rhetoric | PASS |
| зевгма | OK (noun:f) | advanced-rhetoric | PASS |
| терміносистема | OK (noun:f) | professional-language-overview | PASS |
| трансферний | OK (adj:m) | professional-language-overview | PASS |
| інвектива | OK (noun:f) | advanced-rhetoric | PASS |
| контекстуалізація | OK (noun:f) | literary-theory | PASS |
| детермінологізація | OK (noun:f) | professional-language-overview | PASS |
| **метанавичка** | **NOT FOUND** | professional-language-overview | **HIGH** |
| **перорація** | **NOT FOUND** | advanced-rhetoric | **HIGH** |
| **остранення** | **NOT FOUND** | literary-theory | **HIGH** |

### 4.2 Ghost word details

1. **метанавичка** (professional-language-overview, seq 44) -- Not in VESUM. This is a neologism calque from English "meta-skill." Consider replacing with established Ukrainian equivalents like "надпредметна навичка" or "ключова компетенція."

2. **перорація** (advanced-rhetoric, seq 21) -- Not in VESUM. This is a Latinism. The Ukrainian equivalent "завершальна частина промови" is already used in the plan's own description. Remove the Latinism from vocabulary or mark it as borrowed term with Ukrainian equivalent.

3. **остранення** (literary-theory, seq 27) -- Not in VESUM. This is a direct borrowing from Russian (Шкловський's "остранение"). The proper Ukrainian term is **очуднення** (verified in VESUM). Plan should use "очуднення (остранення)" with the Ukrainian term primary.

### 4.3 forbidden field format

**HIGH -- 85 plans have `forbidden: '[]'` (string) instead of `forbidden: []` (empty list).** This is a YAML serialization error. When parsed, `'[]'` is a string literal, not an empty list. This will cause schema validation issues.

---

## 5. YAML Quality

| Check | Status | Details |
|-------|--------|---------|
| YAML syntax | PASS | All 91 files parse without errors |
| Latin characters in Ukrainian | Not checked at scale | Would require character-level scan |
| `forbidden: '[]'` | **HIGH** | 85 plans have string `'[]'` instead of empty list `[]` |
| Prerequisites valid | PASS | All reference existing slugs |
| Sequence continuity | PASS | No gaps, no duplicates (1-91) |

---

## 6. Pedagogical Quality

### 6.1 Generic/templated objectives

**MEDIUM -- 32 of 91 plans share identical first 3 objectives:**

```yaml
- Аналізувати ключові поняття та явища модуля на рівні глибокого розуміння
- Продукувати тексти академічного та професійного рівня за тематикою модуля
- Демонструвати вільне володіння спеціалізованою лексикою та термінологією
```

These are generic boilerplate, not module-specific testable objectives. The 4th objective is usually module-specific ("Застосовувати знання з теми X"). Plans with unique objectives (59 of 91) have much better specificity.

**Affected plans:** Primarily in C2.3 Professional Language and C2.4 Meta-Skills phases (sequences 44-91). The C2.1 Stylistics plans generally have better, more specific objectives.

### 6.2 Templated activity_hints

**MEDIUM -- 85 of 91 plans have the exact same 3 activity_hints:**

```yaml
activity_hints:
- type: reading
  focus: Поглиблений аналіз тексту
  items: 4
- type: essay-response
  focus: Критичне осмислення
- type: discussion
  focus: Дискусія та аргументація
  items: 1
```

This is a template that does not differentiate between a euphony module and a capstone defense module. The `activities:` block below it (with `types_required`) is more specific, but `activity_hints` should also reflect module-specific needs.

### 6.3 Filler content points

**MEDIUM -- 25 of 91 plans contain generic filler points** that appear across multiple plans verbatim:

- "Додаткові творчі та аналітичні завдання з комплексною інтеграцією навичок попередніх модулів" (20 plans)
- "Розширена практика із систематизацією складних граматичних явищ та порівнянням нових конструкцій" (12 plans)
- "Порівняльний аналіз стилістичних прийомів на матеріалі текстів різних епох та жанрів із залученням сучасного українського медіадискурсу" (10 plans)
- "Розширений блок комплексного оцінювання з інтеграцією всіх мовленнєвих компетенцій" (6 plans)

These are not real content descriptions -- they are padding to reach section word counts.

### 6.4 English content in Ukrainian-immersion plans

**HIGH -- 6 plans have English-language objectives** (should be 100% Ukrainian at C2):
- `academic-publishing`, `advanced-rhetoric`, `corpus-linguistics`, `creative-writing-nonfiction`, `language-policy-decolonization`, `practical-rhetoric`

**MEDIUM -- 12 plans have English passages in content_outline points** (e.g., "Learner error:" labels, full English descriptions). While plan files are internal documents, maintaining Ukrainian consistency is important for the build pipeline which uses these points as generation guidance.

### 6.5 Bilingual section titles

All 91 plans have bilingual section titles (Ukrainian + English translation in parentheses). This is acceptable for internal plan files but should not propagate to built content.

---

## 7. Content Accuracy

### 7.1 Literary references verified

- Максим Рильський "Мова" -- correctly attributed (milozvuchnist-complete)
- Тарас Шевченко "І в'яне, сохне, гине..." -- correct gradation example (syntactic-stylistics)
- Коцюбинський's impressionist syntax -- correctly referenced (syntactic-stylistics)
- Іван Франко "Із секретів поетичної творчості" (1898) -- correct date and title (literary-theory)
- Потебня "Думка та мова" (1862) -- correct (literary-theory)
- Борислав сміється (Франко) -- correct metonymy example (stylistic-devices-mastery)

### 7.2 State Standard references

Plans consistently cite correct paragraph numbers (e.g., "§4.3.3", "§4.3.7"). Verified against the C2 section of the state standard mapping.

---

## Issues Summary

### CRITICAL (must fix before build)

1. **C2 checkpoint word_target: 5000 instead of 4000** -- 7 plans (c1-bridge-assessment, c2-1-checkpoint, c2-2-checkpoint, c2-3-checkpoint, c2-3-midpoint-checkpoint, c2-riven-zaversheno, final-exam-integrated-skills)
2. **Missing `grammar:` field** -- 90 of 91 plans
3. **Missing `register:` field** -- 90 of 91 plans

### HIGH (should fix before build)

4. **Ghost word: метанавичка** -- professional-language-overview (seq 44). Replace with "надпредметна навичка" or "ключова компетенція."
5. **Ghost word: перорація** -- advanced-rhetoric (seq 21). Replace with "завершальна частина промови."
6. **Ghost word: остранення** -- literary-theory (seq 27). Replace with Ukrainian "очуднення" (VESUM-verified).
7. **`forbidden: '[]'` (string, not list)** -- 85 plans. Fix to `forbidden: []`.
8. **English-language objectives at C2** -- 6 plans. Translate to Ukrainian.

### MEDIUM (fix if possible)

9. **Generic boilerplate objectives** -- 32 plans share identical first 3 objectives. Replace with module-specific testable objectives.
10. **Templated activity_hints** -- 85 plans have identical activity_hints. Differentiate per module focus.
11. **Filler content_outline points** -- 25 plans have copy-paste filler. Replace with genuine module-specific content descriptions.
12. **English in content_outline points** -- 12 plans. Translate "Learner error:" labels and English passages to Ukrainian.
13. **State Standard gap: one-member sentences** -- No plan explicitly covers односкладні речення as C2 stylistic device (SS §4.2.3).
14. **Duplicate `vocabulary` and `vocabulary_hints`** -- 85 plans have both fields with overlapping content. Consolidate to avoid confusion during build.

### LOW (informational)

15. **Complete numeral mastery** -- Not explicitly covered as a standalone topic; assumed covered in complete-grammar-review (seq 65).
16. **Pedagogy field: 90 plans use TTT, 1 uses Academic** -- Consider whether Academic is intentional for advanced-rhetoric or an inconsistency.
17. **focus field: "grammar" used for professional language modules** -- e.g., `professional-correspondence` has `focus: grammar` but is really about professional writing. Consider `focus: professional` or `focus: writing`.

---

## Suggested Fixes

### Fix 1: Checkpoint word_target (CRITICAL)

For each of the 7 checkpoint plans:
```yaml
# OLD
word_target: 5000

# NEW
word_target: 4000
```
Then reduce section budgets proportionally (multiply each by 0.8).

### Fix 2: Add grammar and register fields (CRITICAL)

Batch add to all 90 plans missing them. Extract grammar topics from each plan's content_outline. Example for milozvuchnist-complete:
```yaml
# ADD
grammar:
- Euphonic alternation (у/в, і/й)
- Preposition variation (з/зі/із)
- Reflexive postfix variation (-ся/-сь)
register: академічний
```

### Fix 3: Fix forbidden field (HIGH)

```yaml
# OLD
forbidden: '[]'

# NEW
forbidden: []
```

### Fix 4: Replace ghost words (HIGH)

```yaml
# literary-theory: остранення -> очуднення
- остранення (defamiliarization)
+ очуднення (defamiliarization)

# professional-language-overview: метанавичка -> надпредметна навичка
- метанавичка (meta-skill)
+ надпредметна навичка (meta-skill)

# advanced-rhetoric: перорація -> завершальна частина промови
- перорація (peroration)
+ завершальна частина промови (peroration)
```

### Fix 5: Translate English objectives (HIGH)

For 6 plans with English objectives, translate to Ukrainian. Example for advanced-rhetoric:
```yaml
# OLD
- Learner can identify and name advanced rhetorical figures in authentic texts

# NEW
- Ідентифікувати й називати складні риторичні фігури в автентичних текстах
```

---

## Phase-Level Verdicts

| Phase | Plans | PASS | NEEDS FIXES | FAIL |
|-------|-------|------|-------------|------|
| C2.1 Stylistics & Rhetoric | 26 | 0 | 26 | 0 |
| C2.2 Literature & Creative Writing | 17 | 0 | 17 | 0 |
| C2.3 Professional Language | 21 | 0 | 21 | 0 |
| C2.4 Meta-Skills & Capstone | 27 | 0 | 27 | 0 |
| **TOTAL** | **91** | **0** | **91** | **0** |

All plans are NEEDS FIXES due to the systematic issues (missing grammar/register fields, forbidden format). Once those template-level fixes are applied, the majority of plans should pass. Plans with checkpoint word_target errors and ghost words need individual attention.

---

## Strengths

1. **Excellent topic coverage** -- All C2 State Standard requirements are addressed across the 91 modules
2. **Good sequencing** -- 4-phase structure (Stylistics, Literature, Professional, Capstone) is logical and progressive
3. **Strong content depth** -- Plans like milozvuchnist-complete, lexical-stylistics, and literary-theory show genuine C2-level intellectual depth
4. **Accurate literary and cultural references** -- Verified examples from Shevchenko, Franko, Kotsyubynsky, Potebnia are correct
5. **Vocabulary quality** -- Sampled vocabulary is overwhelmingly valid in VESUM (only 3 ghost words found)
6. **State Standard alignment** -- Plans consistently cite correct paragraph numbers and cover prescribed topics
