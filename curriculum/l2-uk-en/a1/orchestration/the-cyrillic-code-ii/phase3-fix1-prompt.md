        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `the-cyrillic-code-ii`:

        ## Audit Output (last 60 lines)

        ```
             TOTAL                                         1725 / 2100  ❌ (-375)
  ⏳ Content-only audit: activities/vocab gates DEFERRED
  ✨ Purity violations found: 1
     ❌ [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'sounds like...'.

📚 IMMERSION TOO LOW (4.5% vs 5-15% target)
   FIX: Convert simple explanations to Ukrainian
   FIX: Add more Ukrainian narratives/dialogues
   FIX: Use Ukrainian for engagement boxes (💡🎬🌍)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 2123/2000 (raw: 2358)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 4/3
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Ipa          ⚠️ 12 IPA issues (run lint_ipa.py --fix)
Lint         ✅ Clean Format
Pedagogy     ❌ 5 violations
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    ❌ 4.5% LOW (target 5-15% (M02))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [RUSSIAN_CHARACTERS] Found Russian-only characters: Ы, Э, Ё (lines: [228])
     → FIX: Replace with Ukrainian equivalents: ы→и, э→е, ё→ьо/йо. These characters never appear in Ukrainian.
  [HISTORICAL_CHARS_IN_MODERN] Found historical Cyrillic characters outside quote context: Ъ (lines: [228])
     → FIX: Remove historical characters from modern Ukrainian prose, or use [!quote] callout for authentic historical quotes.
  [RUSSIAN_CHARACTERS] Found Russian-only characters: Ы, Э, Ё (lines: [228])
     → FIX: Replace with Ukrainian equivalents: ы→и, э→е, ё→ьо/йо. These characters never appear in Ukrainian.
  [HISTORICAL_CHARS_IN_MODERN] Found historical Cyrillic characters outside quote context: Ъ (lines: [228])
     → FIX: Remove historical characters from modern Ukrainian prose, or use [!quote] callout for authentic historical quotes.
  [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'sounds like...'.
     → FIX: Vary sentence structure.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 15/100)
   → 5 violations (moderate)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/the-cyrillic-code-ii-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/the-cyrillic-code-ii.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • 2 Outline Compliance Errors

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-cyrillic-code-ii-audit.log for details)

Prose-relevant failures:
  lesson: 2123/2000 (raw: 2358) | pedagogy: 5 violations | immersion: 4.5% LOW (target 5-15% (M02))
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-cyrillic-code-ii.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

