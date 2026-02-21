        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `the-dative-i-pronouns`:

        ## Audit Output (last 60 lines)

        ```
          ⚠️  Outline compliance: 3 errors, 4 warnings
     ❌ [MISSING_OUTLINE_SECTION] Section 'Introduction / Вступ' defined in outline but not found in markdown.
     ❌ [MISSING_OUTLINE_SECTION] Section 'Presentation / Презентація' defined in outline but not found in markdown.
     ❌ [MISSING_OUTLINE_SECTION] Section 'Dialogues / Діалоги' defined in outline but not found in markdown.

  📊 Section Word Analysis:
     Introduction / Вступ           0 /  400  ❌ (-400)
     Presentation / Презентація     0 / 1600  ❌ (-1600)
     Practice / Практика            0 /  600  ❌ (-600)
     Dialogues / Діалоги            0 /  400  ❌ (-400)
     ───────────────────────────────────────────────────
     TOTAL                          0 / 3000  ❌ (-3000)
  ⏳ Content-only audit: activities/vocab gates DEFERRED
  ✨ Prose quality violations found: 1
     ❌ [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (33 occurrences): (To me), (Give me), (To us is fun) — breaks immersion target

--- STRICT GATES (Level A2) ---
Persona      ✅ Persona Defined
Words        ✅ 3514/3000 (raw: 3884)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 7/4
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Ipa          ⚠️ 2 IPA issues (run lint_ipa.py --fix)
Lint         ✅ Clean Format
Pedagogy     ❌ 1 violations
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    🇺🇦 53.6% (target 50-60% (A2.1))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [METALANGUAGE] Metalanguage terms used but not in vocabulary: множина, називний, іменник, прикметник, давальний
     → FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.
  [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (33 occurrences): (To me), (Give me), (To us is fun) — breaks immersion target
     → FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
   → 2 violations (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/the-dative-i-pronouns-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/the-dative-i-pronouns.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • 3 Outline Compliance Errors

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-dative-i-pronouns-audit.log for details)

Prose-relevant failures:
  lesson: 3514/3000 (raw: 3884) | pedagogy: 1 violations
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/the-dative-i-pronouns.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

