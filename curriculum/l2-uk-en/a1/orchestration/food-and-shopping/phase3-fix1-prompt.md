        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `food-and-shopping`:

        ## Audit Output (last 60 lines)

        ```
             ────────────────────────────────────────────────────────────────
     TOTAL                                    1987 / 2000  ❌ (-13)
  ⏳ Content-only audit: activities/vocab gates DEFERRED
  ✨ Prose quality violations found: 4
     ❌ [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '_Приклад:_' — drills belong in activities YAML, not inline
     ❌ [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '_Приклади:_' — drills belong in activities YAML, not inline
     ❌ [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '_Приклади:_' — drills belong in activities YAML, not inline
     ❌ [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (11 occurrences): (You eat), (We eat), (They eat) — breaks immersion target

📚 IMMERSION TOO LOW (17.7% vs 25-40% target)
   FIX: Convert simple explanations to Ukrainian
   FIX: Add more Ukrainian narratives/dialogues
   FIX: Use Ukrainian for engagement boxes (💡🎬🌍)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 2320/2000 (raw: 2494)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 6/3
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Ipa          ⚠️ 13 IPA issues (run lint_ipa.py --fix)
Lint         ✅ Clean Format
Pedagogy     ❌ 4 violations
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    ❌ 17.7% LOW (target 25-40% (M18))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '_Приклад:_' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '_Приклади:_' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '_Приклади:_' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs
  [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (11 occurrences): (You eat), (We eat), (They eat) — breaks immersion target
     → FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 25/100)
   → 4 violations (moderate)
   → Immersion 7% off target (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/food-and-shopping-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/food-and-shopping.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/food-and-shopping-audit.log for details)

Prose-relevant failures:
  lesson: 2320/2000 (raw: 2494) | pedagogy: 4 violations | immersion: 17.7% LOW (target 25-40% (M18))
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/food-and-shopping.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

