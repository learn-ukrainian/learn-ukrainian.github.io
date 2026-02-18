        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `the-cyrillic-code-i`:

        ## Audit Output (last 60 lines)

        ```
        📋 Auditing: A1 M01 — The Cyrillic Code I
   File: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-cyrillic-code-i.md | Target: 300 words
  📋 Required activity types from meta: match-up, quiz
  📋 Template: docs/l2-uk-en/templates/a1-module-template.md (pedagogy: PPP)
  ⚠️  Outline compliance: 3 errors, 3 warnings
     ❌ [MISSING_OUTLINE_SECTION] Section 'Розминка: Чому кирилиця?' defined in outline but not found in markdown.
     ❌ [MISSING_OUTLINE_SECTION] Section 'Культурний контекст: Українська ідентичність літери «І»' defined in outline but not found in markdown.
     ❌ [MISSING_OUTLINE_SECTION] Section 'Продукція: Ваші перші слова' defined in outline but not found in markdown.

  ⚠️ HYDRATION NOTE: Outline sums to 2000, exceeding word_target 300
     Additional 1700 words (allowed for content depth)

  📊 Section Word Analysis:
     Розминка: Чому кирилиця?                                    0 /  350  ❌ (-350)
     Презентація: Літери-друзі та літери-пастки                764 /  650  ✅ (+114)
     Практика: Читаємо міжнародні слова                        274 /  400  ❌ (-126)
     Культурний контекст: Українська ідентичність літери «І»     0 /  300  ❌ (-300)
     Продукція: Ваші перші слова                                 0 /  300  ❌ (-300)
     ────────────────────────────────────────────────────────────────────────────────
     TOTAL                                                    1038 / 2000  ❌ (-962)
  ⏳ Content-only audit: activities/vocab gates DEFERRED

📚 IMMERSION TOO LOW (4.9% vs 5-15% target)
   FIX: Convert simple explanations to Ukrainian
   FIX: Add more Ukrainian narratives/dialogues
   FIX: Use Ukrainian for engagement boxes (💡🎬🌍)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 2187/300 (raw: 2506)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 4/3
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Ipa          ⚠️ 2 IPA issues (run lint_ipa.py --fix)
Lint         ✅ Clean Format
Pedagogy     ✅ Level-appropriate
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    ❌ 4.9% LOW (target 5-15% (M01))

Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/the-cyrillic-code-i-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/the-cyrillic-code-i.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • 3 Outline Compliance Errors

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-cyrillic-code-i-audit.log for details)

Prose-relevant failures:
  lesson: 2187/300 (raw: 2506) | immersion: 4.9% LOW (target 5-15% (M01))
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-cyrillic-code-i.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

