        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `aspect-complete-system`:

        ## Audit Output (last 60 lines)

        ```
          > Знайдіть недоконаний вид: 7 items (min 6)
  > Заперечення та вид дієслова: 10 items (min 8)
  > Часові маркери та вид: 12 items (min 8)
  > Спроба проти успіху: 8 items (min 8)
  ❌ Missing required activity types from meta.yaml: true-false

--- STRICT GATES (Level B1) ---
Persona      ✅ Persona Defined
Words        ✅ 4428/4000 (raw: 4707)
Activities   ✅ 10/4
Density      ✅ All > 6
Unique_types ✅ 7/3 types
Priority     ✅ Priority types used
Engagement   ✅ 12/5
Audio        ℹ️ No audio
Vocab        ✅ 30/25
Structure    ✅ Valid Structure
Ipa          ✅ Clean IPA
Lint         ✅ Clean Format
Pedagogy     ❌ 8 violations
Content_heavy ℹ️ N/A (standard module)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality 📋 Quality validation available (optional)
Research     ✅ Content aligned with research
Immersion    🇺🇦 99.6% (target 85-100% (B1.1 Aspect))
Richness     ✅ 97% (grammar)

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [COMPLEXITY_WORD_COUNT] unjumble 'Побудуйте речення правильно' item 1 has 6 words (target: 9-16)
     → FIX: Adjust sentence length to 9-16 words to match B1 complexity.
  [COMPLEXITY_WORD_COUNT] unjumble 'Побудуйте речення правильно' item 2 has 6 words (target: 9-16)
     → FIX: Adjust sentence length to 9-16 words to match B1 complexity.
  [COMPLEXITY_WORD_COUNT] unjumble 'Побудуйте речення правильно' item 3 has 6 words (target: 9-16)
     → FIX: Adjust sentence length to 9-16 words to match B1 complexity.
  [COMPLEXITY_WORD_COUNT] unjumble 'Побудуйте речення правильно' item 4 has 6 words (target: 9-16)
     → FIX: Adjust sentence length to 9-16 words to match B1 complexity.
  [COMPLEXITY_WORD_COUNT] unjumble 'Побудуйте речення правильно' item 5 has 6 words (target: 9-16)
     → FIX: Adjust sentence length to 9-16 words to match B1 complexity.
  [COMPLEXITY_WORD_COUNT] unjumble 'Побудуйте речення правильно' item 6 has 6 words (target: 9-16)
     → FIX: Adjust sentence length to 9-16 words to match B1 complexity.
  [COMPLEXITY_WORD_COUNT] unjumble 'Побудуйте речення правильно' item 7 has 7 words (target: 9-16)
     → FIX: Adjust sentence length to 9-16 words to match B1 complexity.
  [COMPLEXITY_WORD_COUNT] unjumble 'Побудуйте речення правильно' item 8 has 6 words (target: 9-16)
     → FIX: Adjust sentence length to 9-16 words to match B1 complexity.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 30/100)
   → 8 violations (significant)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/audit/aspect-complete-system-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/status/aspect-complete-system.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • Missing required activity types: true-false

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/aspect-complete-system-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/aspect-complete-system.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/activities/aspect-complete-system.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/vocabulary/aspect-complete-system.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

