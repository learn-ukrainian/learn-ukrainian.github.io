        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `language-about-verbs`:

        ## Audit Output (last 60 lines)

        ```
        📚 PEDAGOGICAL VIOLATIONS FOUND:
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '_Приклади:_' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '_Приклади:_' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '_Приклади:_' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '_Приклади:_' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '_Приклади:_' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '_Приклади:_' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '_Приклади:_' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '_Приклади:_' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '_Приклади:_' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '_Приклади:_' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '_Приклади:_' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '_Приклади:_' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '_Приклади:_' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '_Приклади:_' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '_Приклади:_' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '_Приклади:_' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '_Приклади:_' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '_Приклади:_' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '_Приклади:_' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (8 occurrences): (Builders are building the house), (Verbs of perfective aspect), (Do not have) — breaks immersion target
     → FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 50/100)
   → Revision recommended (severity 50/100)
   → 20 violations (severe - consider revision)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/audit/language-about-verbs-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/status/language-about-verbs.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • 5 Outline Compliance Errors

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/language-about-verbs-audit.log for details)

Prose-relevant failures:
  lesson: 4141/4000 (raw: 4474) | pedagogy: 20 violations
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/language-about-verbs.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

