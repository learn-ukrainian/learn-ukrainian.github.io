        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `logical-prepositions`:

        ## Audit Output (last 60 lines)

        ```
          > Переклад: причина і мета: 6 items (min 6)
  > Оберіть правильний відмінок: 8 items (min 8)
  > Знайдіть відповідний прийменник: 8 items (min 8)

📊 ACTIVITIES WITH LOW DENSITY:
  ❌ Знайдіть прийменники
     Current: 5 items | Required: 6 | Add: 1 more
     → Add 1 more words to mark in the text


--- STRICT GATES (Level A2) ---
Persona      ✅ Persona Defined
Words        ✅ 3128/3000 (raw: 3310)
Activities   ✅ 12/10
Density      ❌ 1 < 8
Unique_types ✅ 10/4 types
Priority     ✅ Priority types used
Engagement   ✅ 5/4
Audio        ℹ️ No audio
Vocab        ✅ 25/1
Structure    ✅ Valid Structure
Ipa          ✅ Clean IPA
Lint         ✅ Clean Format
Pedagogy     ❌ 7 violations
Content_heavy ℹ️ N/A (standard module)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ℹ️ Quality validation N/A (A1/A2)
Research     ✅ Content aligned with research
Immersion    🇺🇦 50.4% (target 50-60% (A2.1))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [COMPLEXITY_WORD_COUNT] quiz 'Оберіть правильний прийменник часу' Q1 prompt length 4 (target: 5-15)
     → FIX: Adjust prompt length to 5-15 words.
  [COMPLEXITY_WORD_COUNT] quiz 'Оберіть правильний прийменник часу' Q2 prompt length 4 (target: 5-15)
     → FIX: Adjust prompt length to 5-15 words.
  [COMPLEXITY_WORD_COUNT] quiz 'Оберіть правильний прийменник часу' Q5 prompt length 4 (target: 5-15)
     → FIX: Adjust prompt length to 5-15 words.
  [COMPLEXITY_WORD_COUNT] quiz 'Оберіть правильний прийменник часу' Q7 prompt length 4 (target: 5-15)
     → FIX: Adjust prompt length to 5-15 words.
  [COMPLEXITY] mark-the-words 'Знайдіть прийменники' has 5 items (minimum: 6)
     → FIX: Add more items. A2 mark-the-words requires at least 6 items.
  [COMPLEXITY_WORD_COUNT] quiz 'Оберіть правильний відмінок' Q3 prompt length 4 (target: 5-15)
     → FIX: Adjust prompt length to 5-15 words.
  [COMPLEXITY_WORD_COUNT] quiz 'Оберіть правильний відмінок' Q7 prompt length 4 (target: 5-15)
     → FIX: Adjust prompt length to 5-15 words.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 40/100)
   → Revision recommended (severity 40/100)
   → 7 violations (significant)
   → Activity density below minimum


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/logical-prepositions-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/logical-prepositions.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/logical-prepositions-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/logical-prepositions.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/logical-prepositions.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/vocabulary/logical-prepositions.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

