        # Fix 20 issue(s) in `at-the-restaurant`

        ### Fix: Gate `Pedagogy` FAIL — 17 violations

### Fix 2: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'мові'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 3: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'вам'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 4: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'вам'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 5: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'Вам'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 6: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Instrumental case used at A1: 'з офіціантом'
**How to fix:** Instrumental case not allowed until A2 (M36+). Restructure sentence.

### Fix 7: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'е, що о'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 8: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'о, що в'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 9: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'а, коли в'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 10: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'Якщо в'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 11: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'Якщо в'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 12: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'Якщо в'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 13: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Уміння замовити страву українською мовою...'

### Fix 14: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Якщо ви не знаєте що...'

### Fix 15: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Просто запам ятайте форму дієслова...'

### Fix 16: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Ми вже знаємо що він...'

### Fix 17: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 14 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'цьому уроці ви навчилися замовляти...'

### Fix 18: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Ви знаєте як попросити меню...'

### Fix 19: PEDAGOGICAL_VIOLATION
**What:** [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'if you...'.
**How to fix:** Vary sentence structure.

### Fix 20: PEDAGOGICAL_VIOLATION
**What:** [SECTION_BALANCE_BLOATED] Section 'Презентація: Мова замовлення (Presentation: Ordering Language)' has 997 words (51% of total). Bloated sections: 'Презентація: Мова замовлення (Presentation: Ordering Language)' (51%)
**How to fix:** Consider splitting the large section or expanding smaller sections to improve balance.

### Other Audit Failures

```
Підсумок та етикет (Summary & Etiquette)                         107 /  250  ❌ (-143)
❌ [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'if you...'.
📚 PEDAGOGICAL VIOLATIONS FOUND:
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/at-the-restaurant-audit.log for details)
```


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M15+ — Verbs & Beyond):
Present tense verbs start at M15. Past tense at M36. Future at M37.

KEY RESTRICTION: Imperative forms (Слухайте!, Читайте!, Пишіть!) are NOT taught until M47 (imperative-and-requests). Before M47, use indirect requests or English for instructions.

The standard A1 LEVEL_CONSTRAINTS (no dative, no instrumental, imperfective only) apply in addition to this constraint.



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/at-the-restaurant.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/at-the-restaurant.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/at-the-restaurant.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections

