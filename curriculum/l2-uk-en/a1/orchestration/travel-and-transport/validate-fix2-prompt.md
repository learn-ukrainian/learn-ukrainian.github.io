        # Fix 15 issue(s) in `travel-and-transport`

        ### Fix 1: ACTIVITY_VESUM_FAIL
**What:** Activity answers contain VESUM-failed words: Іван
**How to fix:** Fix spelling or replace these words — students will practice non-existent forms.
**Where:** travel-and-transport.yaml

### Fix: Gate `Density` FAIL — 8 < 6

### Fix: Gate `Pedagogy` FAIL — 11 violations

### Fix: Gate `Immersion` FAIL — 11.0% LOW (target 35-55% (M52))
**⚠ SCOPE WARNING:** Immersion gap is 24% (11.0% → 35% min). This is too large for a fix pass. Focus on the EASIEST wins:
1. Add Ukrainian section headers with English in parentheses
2. Add 'Наприклад:' / 'Порівняйте:' before example blocks
3. Add short Ukrainian phrases with (translations) in existing paragraphs
Do NOT rewrite entire sections. Target +5-8% improvement max.

### Fix 5: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'пові'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 6: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'пові'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 7: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] match-up 'Match the Transport' has 6 pairs (target: 8-20)
**How to fix:** Adjust number of pairs to 8-20.

### Fix 8: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] match-up 'Match the Locations' has 6 pairs (target: 8-20)
**How to fix:** Adjust number of pairs to 8-20.

### Fix 9: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] match-up 'Match the Directions' has 6 pairs (target: 8-20)
**How to fix:** Adjust number of pairs to 8-20.

### Fix 10: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] quiz 'Check Your Knowledge' has 6 items (minimum: 8)
**How to fix:** Add more items. A1 quiz requires at least 8 items.

### Fix 11: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] true-false 'True or False?' has 6 items (minimum: 8)
**How to fix:** Add more items. A1 true-false requires at least 8 items.

### Fix 12: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] fill-in 'Complete the Sentence' has 6 items (minimum: 8)
**How to fix:** Add more items. A1 fill-in requires at least 8 items.

### Fix 13: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] unjumble 'Build the Sentence' has 4 items (minimum: 6)
**How to fix:** Add more items. A1 unjumble requires at least 6 items.

### Fix 14: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] quiz 'Story Comprehension' has 6 items (minimum: 8)
**How to fix:** Add more items. A1 quiz requires at least 8 items.

### Fix 15: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] quiz 'Story Comprehension' Q1 prompt length 4 (target: 5-10)
**How to fix:** Adjust prompt length to 5-10 words.

### Other Audit Failures

```
❌ Match the Transport
❌ Match the Locations
❌ Match the Directions
❌ Check Your Knowledge
❌ True or False?
❌ Complete the Sentence
❌ Build the Sentence
❌ Story Comprehension
📚 PEDAGOGICAL VIOLATIONS FOUND:
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/travel-and-transport-audit.log for details)
```


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M15+ — Verbs & Beyond):
Present tense verbs start at M15. Past tense at M36. Future at M37.

KEY RESTRICTION: Imperative forms (Слухайте!, Читайте!, Пишіть!) are NOT taught until M47 (imperative-and-requests). Before M47, use indirect requests or English for instructions.

The standard A1 LEVEL_CONSTRAINTS (no dative, no instrumental, imperfective only) apply in addition to this constraint.



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/travel-and-transport.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/travel-and-transport.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/travel-and-transport.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections

