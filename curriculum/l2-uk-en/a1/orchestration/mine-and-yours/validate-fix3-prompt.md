        # Fix 3 issue(s) in `mine-and-yours`

        ### Fix: Gate `Immersion` FAIL — 8.4% LOW (target 25-40% (M20))
**⚠ SCOPE WARNING:** Immersion gap is 17% (8.4% → 25% min). This is too large for a fix pass. Focus on the EASIEST wins:
1. Add Ukrainian section headers with English in parentheses
2. Add 'Наприклад:' / 'Порівняйте:' before example blocks
3. Add short Ukrainian phrases with (translations) in existing paragraphs
Do NOT rewrite entire sections. Target +5-8% improvement max.

### Fix 2: PEDAGOGICAL_VIOLATION
**What:** [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'if the...'.
**How to fix:** Vary sentence structure.

### Fix 3: PEDAGOGICAL_VIOLATION
**What:** [SECTION_BALANCE_BLOATED] Section 'Презентація: Система форм та узгодження (Presentation: System of Forms and Agreement)' has 764 words (45% of total). Bloated sections: 'Презентація: Система форм та узгодження (Presentation: System of Forms and Agreement)' (45%)
**How to fix:** Consider splitting the large section or expanding smaller sections to improve balance.

### Other Audit Failures

```
❌ [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'if the...'.
📚 PEDAGOGICAL VIOLATIONS FOUND:
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/mine-and-yours-audit.log for details)
```


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M15+ — Verbs & Beyond):
Present tense verbs start at M15. Past tense at M36. Future at M37.

KEY RESTRICTION: Imperative forms (Слухайте!, Читайте!, Пишіть!) are NOT taught until M47 (imperative-and-requests). Before M47, use indirect requests or English for instructions.

The standard A1 LEVEL_CONSTRAINTS (no dative, no instrumental, imperfective only) apply in addition to this constraint.



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/mine-and-yours.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/mine-and-yours.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/mine-and-yours.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections

