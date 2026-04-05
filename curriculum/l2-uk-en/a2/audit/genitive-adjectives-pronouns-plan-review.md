# Plan Review: genitive-adjectives-pronouns

**Track:** A2 | **Sequence:** 11 | **Version:** 1.0
**Verdict:** NEEDS FIXES

## Rule Compliance

| Check | Status | Details |
|-------|--------|---------|
| word_target | PASS | Plan: 2000, Config: 2000 |
| section_budgets | PASS | Sum = 2000 vs target 2000 (+0%) |
| required_fields | FAIL | Missing: `persona`, `grammar`, `register` |
| version_string | PASS | `'1.0'` — string |

## State Standard Alignment

| Grammar Topic | In Standard? | Standard Level | Plan Level | Status |
|--------------|-------------|----------------|------------|--------|
| Adjective declension (genitive) | YES | A2 §4.2.1.2 (lines 1223-1233) | A2 | PASS |
| Possessive pronouns (genitive) | YES | A2 §4.2.1.4 (lines 1244-1254) | A2 | PASS |
| Demonstrative pronouns (genitive) | YES | A2 §4.2.1.4 (lines 1244-1254) | A2 | PASS |

The State Standard for A2 §4.2.1.2 covers "Adjective declension — full paradigm" and §4.2.1.4 covers "Expanded pronouns — possessive, demonstrative, interrogative." Teaching genitive forms of adjectives and pronouns together is well-aligned.

## Grammar Verification (Textbook RAG)

| Concept | Textbook Source | Correct? | Notes |
|---------|----------------|----------|-------|
| Adjective genitive endings -ого/-ього (masc/neut), -ої/-ьої (fem) | Avramenko Grade 11 (`11-klas-ukrajinska-mova-avramenko-2019_s0036`) | YES | Confirms білого/синього (masc), білої/синьої (fem) |
| Adjective declension table (hard group) | Заболотний Grade 4 (`4-klas-ukrmova-zaharijchuk_s0084`) | YES | довгого (gen masc), довгої (gen fem) |
| Possessive pronoun declension (мого, моєї) | Заболотний Grade 6 §62 (`6-klas-ukrmova-zabolotnyi-2020_s0210`) | YES | Full paradigm: мого, моєї confirmed |
| Demonstrative pronoun declension (того, тієї) | Avramenko Grade 6 §95-96 (`6-klas-ukrmova-avramenko-2023_s0195`) | YES | того/тієї confirmed in full table |
| його/її as invariable possessives | Avramenko Grade 6 §91 (`6-klas-ukrmova-avramenko-2023_s0186`) | YES | Confirms його/її don't change as possessives |
| їхній declines like soft-group adjective | Avramenko Grade 6 §95-96 (`6-klas-ukrmova-avramenko-2023_s0195`) | YES | "Займенник їхній відмінюємо так, як прикметник м'якої групи" |

## Vocabulary Verification

| Word | VESUM | Issues |
|------|-------|--------|
| прикметник | OK (noun) | — |
| займенник | OK (noun) | — |
| присвійний | OK (adj) | — |
| вказівний | OK (adj) | — |
| узгодження | OK (noun) | — |
| дозвіл | OK (noun) | — |
| підручник | OK (noun) | — |
| документ | OK (noun) | — |
| вчителька | OK (noun) | — |
| важливий | OK (adj) | — |
| молодий | OK (adj) | — |
| старший | OK (adj) | — |
| дівчина | OK (noun) | — |
| олівець | OK (noun) | — |

All 14 vocabulary items verified in VESUM. Genitive forms verified: їхнього (OK), їхньої (OK), цього (OK), того (OK), цієї (OK), тієї (OK), нового (OK), нової (OK), синього (OK), синьої (OK), мого (OK), твого (OK), моєї (OK), твоєї (OK).

## Issues Found

### CRITICAL (must fix before build)

1. **WRONG claim about їхній being invariable.** Section 2, point 3 states: "його, її, їхній/їхня/їхнє do not change for case when they are possessives." This is **correct for його and її** but **WRONG for їхній**. Avramenko Grade 6, §95-96 explicitly states: "Займенник їхній відмінюємо так, як прикметник м'якої групи (§67)." The forms are: їхнього (gen masc/neut), їхньої (gen fem), їхньому (dat), etc. Only його and її are truly invariable as possessives. їхній declines fully. Teaching this incorrectly would give learners a false rule.

### HIGH (should fix before build)

1. **Missing required fields: `persona`, `grammar`, `register`.** Same as M08-M10.

2. **Objective 1 lists "-ьої for soft stems" but this is rare.** The feminine genitive ending -ьої (e.g., синьої) exists but is less common than -ої. The plan correctly identifies it, and Avramenko Grade 11 confirms "синьої" in the paradigm table. However, the content should note that most adjectives learners encounter at A2 will use the hard-stem -ої pattern. -ьої applies mainly to soft-stem adjectives (синій, безкрайій, літній). This isn't wrong, but the balance in teaching should favor -ого/-ої as the primary patterns.

3. **Five activity hints instead of four.** M08-M10 each have 4 activity hints. M11 has 5 (two fill-ins, one quiz, one match-up, one error-correction). The error-correction activity is a strong pedagogical choice for agreement practice, so this is actually a positive — but it should be noted that the build will need to accommodate one extra activity type within the same word budget.

### MEDIUM (fix if possible)

1. **Section 2 combines possessives and "unchanged" forms in a way that may confuse.** The section teaches мого/моєї/нашого/вашої (which decline) alongside його/її (which don't) alongside їхній (which does decline but the plan wrongly says doesn't). Suggestion: restructure to clearly separate "always declines" (мій, твій, наш, ваш, їхній) from "never declines as possessive" (його, її).

2. **"нашого, вашого" listed but "свого, своєї" absent.** The reflexive possessive свій is arguably the most important possessive pronoun for practical use, and its genitive forms (свого, своєї) should at least appear in the vocabulary hints or content outline points. Заболотний Grade 6, §62 teaches свій alongside мій/твій.

### LOW (informational)

1. **Dialogue situation is excellent.** Lost-and-found office is natural, motivating, and forces the learner to produce full genitive noun phrases with adjective+pronoun+noun agreement ("сумка мого старшого брата," "цієї червоної парасольки," "нашого великого чемодану"). This is perfect for drilling the target grammar in context.

2. **Consolidation drill in section 3 (building phrases step by step) is outstanding pedagogy.** The progression "друга → нового друга → цього нового друга → для цього нового друга" mirrors exactly how Ukrainian textbooks build complexity incrementally. Avramenko and Заболотний both use this layered approach.

3. **Word order note "demonstrative + possessive/adjective + noun" is correct** and matches standard Ukrainian syntax. Good that this is explicitly stated.

## Suggested Fixes

```yaml
# Add missing required fields:
persona: tutor
grammar:
  - genitive_adjective_endings_hard_soft
  - genitive_possessive_pronouns
  - genitive_demonstrative_pronouns
  - noun_phrase_agreement_genitive
register: informal-educational

# CRITICAL FIX — section 2, point 3:
# OLD:
#   'Note: його, її, їхній/їхня/їхнє do not change for case when they are
#   possessives (його книги = his book''s, not him).'
# NEW:
#   'Note: його and її do not change for case when they are possessives
#   (його книга → його книги; її сумка → її сумки). But їхній declines
#   like a soft-group adjective: їхнього друга (gen masc), їхньої школи
#   (gen fem), їхнього міста (gen neut).'

# Consider adding свій to vocabulary_hints.recommended:
#   - свій (one's own (reflexive possessive))
```
