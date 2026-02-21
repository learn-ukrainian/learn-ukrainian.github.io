        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `the-locative-where-things-are`:

        ## Audit Output (last 60 lines)

        ```
        Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Ipa          ⚠️ 8 IPA issues (run lint_ipa.py --fix)
Lint         ❌ 3 Format Errors
Pedagogy     ❌ 11 violations
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    ❌ 18.9% LOW (target 25-40% (M13))

❌ LINT ERRORS FOUND:
  - Line 218: AI Contamination detected ('\bCorrection:'). Remove thinking/self-correction artifacts.
  - Line 218: AI Contamination detected ('\bSelf-correction\b'). Remove thinking/self-correction artifacts.
  - Line 307: AI Contamination detected ('\bCorrection:'). Remove thinking/self-correction artifacts.


📚 PEDAGOGICAL VIOLATIONS FOUND:
  [GRAMMAR] Dative case used at A1: 'Києві'
     → FIX: Dative case not allowed until A2 (M31+). Restructure sentence.
  [GRAMMAR] Dative case used at A1: 'Києві'
     → FIX: Dative case not allowed until A2 (M31+). Restructure sentence.
  [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'if it...'.
     → FIX: Vary sentence structure.
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '*   _Приклад:_ Я **вдома**. (I am at home.)' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '*   _Приклад:_ Де тато? Тато **на роботі**. (Where is dad? Dad is at work.)' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '*   _Приклад:_ Телефон у **сумці**. (The phone is in the bag.)' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '*   _Приклад:_ Мама в **аптеці**.' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '*   _Приклад:_ Кіт спить на **нозі**. (The cat is sleeping on the leg.)' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '*   _Приклад:_ Фото у **книзі**.' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '*   _Приклад:_ Музика у **вусі**. (Music in the ear.)' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (5 occurrences): (It has walls and a roof), (Floor of a building), (Khreshchatyk street) — breaks immersion target
     → FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 70/100)
   → Revision recommended (severity 70/100)
   → 11 violations (severe - consider revision)
   → Immersion 6% off target (minor)
   → 3 format errors


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/the-locative-where-things-are-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/the-locative-where-things-are.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-locative-where-things-are-audit.log for details)

Prose-relevant failures:
  meta: Valid Structure | Lint: 3 Format Errors
  lesson: 2608/2000 (raw: 2788) | pedagogy: 11 violations | immersion: 18.9% LOW (target 25-40% (M13))
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-locative-where-things-are.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

