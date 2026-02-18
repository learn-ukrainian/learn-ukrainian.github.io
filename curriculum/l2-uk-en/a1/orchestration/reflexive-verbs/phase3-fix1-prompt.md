        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `reflexive-verbs`:

        ## Audit Output (last 60 lines)

        ```
             ❌ [SECTION_LENGTH_MISMATCH] Section 'Теорія: Відмінювання та групи' is under target word count.
     ❌ [SECTION_LENGTH_MISMATCH] Section 'Практика: Дія на себе чи на іншого?' is under target word count.
     ❌ [SECTION_LENGTH_MISMATCH] Section 'Культура: Секрети вимови' is under target word count.

  📊 Section Word Analysis:
     Розминка: Що таке зворотні дієслова?   464 /  300  ✅ (+164)
     Теорія: Відмінювання та групи          538 /  700  ❌ (-162)
     Практика: Дія на себе чи на іншого?    335 /  600  ❌ (-265)
     Культура: Секрети вимови               313 /  400  ❌ (-87)
     ─────────────────────────────────────────────────────────────
     TOTAL                                 1650 / 2000  ❌ (-350)
  ⏳ Content-only audit: activities/vocab gates DEFERRED

📚 IMMERSION TOO LOW (12.2% vs 15-35% target)
   FIX: Convert simple explanations to Ukrainian
   FIX: Add more Ukrainian narratives/dialogues
   FIX: Use Ukrainian for engagement boxes (💡🎬🌍)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ❌ 1789/2000 (raw: 2158)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 5/3
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Ipa          ⚠️ 8 IPA issues (run lint_ipa.py --fix)
Lint         ✅ Clean Format
Pedagogy     ✅ Level-appropriate
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    ❌ 12.2% LOW (target 15-35% (M09))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [METALANGUAGE] Metalanguage terms used but not in vocabulary: дієслово
     → FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
   → 1 violations (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/reflexive-verbs-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/reflexive-verbs.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • 3 Outline Compliance Errors

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/reflexive-verbs-audit.log for details)

Prose-relevant failures:
  lesson: 1789/2000 (raw: 2158) | immersion: 12.2% LOW (target 15-35% (M09))
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/reflexive-verbs.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

