        # Fix 21 issue(s) in `leisure-and-hobbies`

        ### Fix: Gate `Pedagogy` FAIL — 19 violations

### Fix 2: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'відпові'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 3: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'Відпові'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 4: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'Переві'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 5: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'Мені'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 6: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'Мені'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 7: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'Мені'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 8: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'А що т'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 9: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Ми мо жемо говори ти...'

### Fix 10: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Ви мо жете використо вувати...'

### Fix 11: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'англі йській мо ві ми...'

### Fix 12: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Деякі ви ди спо рту...'

### Fix 13: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 14 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Ду же важли во розумі...'

### Fix 14: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Коли ми йде мо туди...'

### Fix 15: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Коли ми вже там ми...'

### Fix 16: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 14 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Це сло во ма одна...'

### Fix 17: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 13 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Фра за ходи ти го...'

### Fix 18: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 13 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Коли ми ма ємо пла...'

### Fix 19: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'Запро шення мо жуть бу...'

### Fix 20: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] quiz 'Check Your Understanding' Q1 prompt length 4 (target: 5-10)
**How to fix:** Adjust prompt length to 5-10 words.

### Fix 21: PEDAGOGICAL_VIOLATION
**What:** [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'ми хо́димо...'.
**How to fix:** Vary sentence structure.

### Other Audit Failures

```
❌ [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'ми хо́димо...'.
📚 PEDAGOGICAL VIOLATIONS FOUND:
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/leisure-and-hobbies-audit.log for details)
```


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M15+ — Verbs & Beyond):
Present tense verbs start at M15. Past tense at M36. Future at M37.

KEY RESTRICTION: Imperative forms (Слухайте!, Читайте!, Пишіть!) are NOT taught until M47 (imperative-and-requests). Before M47, use indirect requests or English for instructions.

The standard A1 LEVEL_CONSTRAINTS (no dative, no instrumental, imperfective only) apply in addition to this constraint.



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/leisure-and-hobbies.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/leisure-and-hobbies.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/leisure-and-hobbies.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections

