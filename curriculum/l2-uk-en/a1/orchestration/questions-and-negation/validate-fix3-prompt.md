        # Fix 5 issue(s) in `questions-and-negation`

        ### Fix: Gate `Pedagogy` FAIL — 3 violations

### Fix: Gate `Immersion` FAIL — 9.2% LOW (target 25-40% (M18))
**⚠ SCOPE WARNING:** Immersion gap is 16% (9.2% → 25% min). This is too large for a fix pass. Focus on the EASIEST wins:
1. Add Ukrainian section headers with English in parentheses
2. Add 'Наприклад:' / 'Порівняйте:' before example blocks
3. Add short Ukrainian phrases with (translations) in existing paragraphs
Do NOT rewrite entire sections. Target +5-8% improvement max.

### Fix 3: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] quiz 'Understanding Questions and Negation' Q3 prompt length 19 (target: 5-10)
**How to fix:** Adjust prompt length to 5-10 words.

### Fix 4: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] quiz 'Understanding Questions and Negation' Q4 prompt length 20 (target: 5-10)
**How to fix:** Adjust prompt length to 5-10 words.

### Fix 5: PEDAGOGICAL_VIOLATION
**What:** [VOCAB_NOT_IN_CONTENT] Only 7/20 (35%) vocabulary words appear in content+activities. Missing: де, звідки, знати, коли, куди, не, ні, робити, хто, чи (+3 more)
**How to fix:** Vocabulary words MUST appear in the module content or activities. Either use these words in the prose/examples, add activities that practice them, or remove them from the vocabulary YAML if they don't belong in this module.

### Other Audit Failures

```
Практика: Тренування заперечень та запитань (Practice: Drilling Negation and Questions)    175 /  250  ❌ (-75)
Продукція: Комунікативні сценарії (Production: Communicative Scenarios)                    192 /  250  ❌ (-58)
❌ [VOCAB_NOT_IN_CONTENT] Only 7/20 (35%) vocabulary words appear in content+activities. Missing: де, звідки, знати, коли, куди, не, ні, робити, хто, чи (+3 more)
📚 PEDAGOGICAL VIOLATIONS FOUND:
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/questions-and-negation-audit.log for details)
```


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M15+ — Verbs & Beyond):
Present tense verbs start at M15. Past tense at M36. Future at M37.

KEY RESTRICTION: Imperative forms (Слухайте!, Читайте!, Пишіть!) are NOT taught until M47 (imperative-and-requests). Before M47, use indirect requests or English for instructions.

The standard A1 LEVEL_CONSTRAINTS (no dative, no instrumental, imperfective only) apply in addition to this constraint.



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/questions-and-negation.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/questions-and-negation.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/questions-and-negation.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections

