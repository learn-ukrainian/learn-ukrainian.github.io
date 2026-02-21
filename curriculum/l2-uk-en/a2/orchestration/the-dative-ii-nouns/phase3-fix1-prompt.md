        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `the-dative-ii-nouns`:

        ## Audit Output (last 60 lines)

        ```
           FIX: Add English explanations for case/aspect theory
   FIX: Expand English scaffolding for complex grammar
❌ AUDIT FAILED: Transliteration detected: 'Місто (neuter)'. Remove Latin in parentheses.

--- STRICT GATES (Level A2) ---
Persona      ✅ Persona Defined
Words        ❌ 1974/3000 (raw: 2308)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 4/4
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Ipa          ✅ Clean IPA
Lint         ✅ Clean Format
Pedagogy     ❌ 6 violations
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    ❌ 87.2% HIGH (target 50-60% (A2.1))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [COMPLEXITY] Sentence too long for A2: 16 words (max 15)
     → FIX: Break into shorter sentences. First 5 words: 'Без нього ви не зможете...'
  [COMPLEXITY] Sentence too long for A2: 17 words (max 15)
     → FIX: Break into shorter sentences. First 5 words: 'Якщо ви можете підставити англійські...'
  [COMPLEXITY] Sentence too long for A2: 16 words (max 15)
     → FIX: Break into shorter sentences. First 5 words: 'Найбільш характерним милозвучним та суто...'
  [COMPLEXITY] Sentence too long for A2: 17 words (max 15)
     → FIX: Break into shorter sentences. First 5 words: 'Закінчення ові для середнього роду...'
  [COMPLEXITY] Sentence too long for A2: 18 words (max 15)
     → FIX: Break into shorter sentences. First 5 words: 'Якщо ви все хочете подарувати...'
  [METALANGUAGE] Metalanguage terms used but not in vocabulary: давальний, множина, родовий
     → FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.
  [DRILL_BLOCK_IN_PROSE] Drill block in narrative prose: '_Приклад:_' — drills belong in activities YAML, not inline
     → FIX: Move example drill to activities/ YAML file or rewrite as flowing narrative with examples woven into paragraphs


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 70/100)
   → Revision recommended (severity 70/100)
   → 7 violations (significant)
   → Immersion 27% off target (major rebalancing needed)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/the-dative-ii-nouns-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/the-dative-ii-nouns.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • 6 Outline Compliance Errors

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-dative-ii-nouns-audit.log for details)

Prose-relevant failures:
  lesson: 1974/3000 (raw: 2308) | pedagogy: 6 violations | immersion: 87.2% HIGH (target 50-60% (A2.1))
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/the-dative-ii-nouns.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

