        # Fix 12 issue(s) in `colors-and-clothing`

        ### Fix: Gate `Pedagogy` FAIL — 8 violations

### Fix: Gate `Immersion` FAIL — 12.9% LOW (target 25-40% (M12))
**Action:** Add more Ukrainian-language content blocks. Convert some English explanations to Ukrainian with English glosses.

### Fix 3: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'базові'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 4: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'Мені'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 5: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'Мені'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 6: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'Мені'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 7: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'вам'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 8: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] Sentence too long for A1: 13 words (max 10)
**How to fix:** Break into shorter sentences. First 5 words: 'ий чо рний све тр...'

### Fix 9: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] quiz 'Using the Verb To Wear' Q7 prompt length 4 (target: 5-10)
**How to fix:** Adjust prompt length to 5-10 words.

### Fix 10: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] quiz 'Using the Verb To Wear' Q8 prompt length 4 (target: 5-10)
**How to fix:** Adjust prompt length to 5-10 words.

### Fix 11: PEDAGOGICAL_VIOLATION
**What:** [METALANGUAGE] Metalanguage terms used but not in vocabulary: множина, дієслово
**How to fix:** Add these grammar terms to vocabulary with translations, or use English equivalents.

### Fix 12: PEDAGOGICAL_VIOLATION
**What:** [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'this is...'.
**How to fix:** Vary sentence structure.

### Other Audit Failures

```
❌ [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'this is...'.
📚 PEDAGOGICAL VIOLATIONS FOUND:
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/colors-and-clothing-audit.log for details)
```


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M11-14 — Adjectives & Plurals):
Student knows: alphabet, gender, greetings, Це/Я/Мене звати, basic nouns.
Learning: adjective agreement (M11), colors (M12), plurals (M13), checkpoint (M14).

GRAMMAR STATUS:
- AVAILABLE: nouns (nom. sg & pl from M13), adjective+noun agreement (from M11), Це/Я sentences, memorized phrases
- FORBIDDEN: verb conjugation (starts M15), imperatives (M47), cases beyond nominative (accusative starts M25)
- Use English for classroom instructions

METALANGUAGE: English-first, Ukrainian in parentheses



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/colors-and-clothing.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/colors-and-clothing.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/colors-and-clothing.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections

