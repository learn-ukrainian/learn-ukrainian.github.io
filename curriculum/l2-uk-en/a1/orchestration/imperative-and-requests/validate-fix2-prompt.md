        # Fix 22 issue(s) in `imperative-and-requests`

        ### Fix 1: PLAN_SECTION_MISSING
**What:** Missing 5 plan section(s): Наказовий спосіб (Imperative mood), Вісім обов'язкових дієслів (Eight required verbs), Ввічливе прохання (Polite requests), Заборони (Prohibitions), Практика (Practice)
**How to fix:** Add content for the missing plan sections or update section headings to match plan.
**Where:** (plan vs content)

### Fix: Gate `Density` FAIL — 4 < 6

### Fix: Gate `Pedagogy` FAIL — 19 violations

### Fix 4: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'мові'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 5: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'базові'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 6: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'вам'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 7: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Instrumental case used at A1: 'вами'
**How to fix:** Instrumental case not allowed until A2 (M36+). Restructure sentence.

### Fix 8: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Instrumental case used at A1: 'перед дієсловом'
**How to fix:** Instrumental case not allowed until A2 (M36+). Restructure sentence.

### Fix 9: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Instrumental case used at A1: 'за правилом'
**How to fix:** Instrumental case not allowed until A2 (M36+). Restructure sentence.

### Fix 10: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: ', які в'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 11: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'якщо в'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 12: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'якщо в'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 13: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'Щоб з'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 14: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'Щоб п'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 15: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Це абсолютно нормально не звучить...'

### Fix 16: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Ось дієслова наказовому способі які...'

### Fix 17: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Фраза будь ла ска походить...'

### Fix 18: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Щоб попросити когось чогось не...'

### Fix 19: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] match-up 'Match the verb to its "ти" command' has 6 pairs (target: 8-20)
**How to fix:** Adjust number of pairs to 8-20.

### Fix 20: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] match-up 'Match the verb to its "ви" command' has 6 pairs (target: 8-20)
**How to fix:** Adjust number of pairs to 8-20.

### Fix 21: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] quiz 'Choose the Right Command' has 6 items (minimum: 8)
**How to fix:** Add more items. A1 quiz requires at least 8 items.

### Fix 22: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] quiz 'Negative Commands and Polite Requests' has 6 items (minimum: 8)
**How to fix:** Add more items. A1 quiz requires at least 8 items.

### Other Audit Failures

```
❌ Match the verb to its "ти" command
❌ Match the verb to its "ви" command
❌ Choose the Right Command
❌ Negative Commands and Polite Requests
📚 PEDAGOGICAL VIOLATIONS FOUND:
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/imperative-and-requests-audit.log for details)
```


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M15+ — Verbs & Beyond):
Present tense verbs start at M15. Past tense at M36. Future at M37.

KEY RESTRICTION: Imperative forms (Слухайте!, Читайте!, Пишіть!) are NOT taught until M47 (imperative-and-requests). Before M47, use indirect requests or English for instructions.

The standard A1 LEVEL_CONSTRAINTS (no dative, no instrumental, imperfective only) apply in addition to this constraint.



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/imperative-and-requests.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/imperative-and-requests.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/imperative-and-requests.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections

