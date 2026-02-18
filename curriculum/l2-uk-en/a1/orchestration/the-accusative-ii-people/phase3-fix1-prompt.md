        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `the-accusative-ii-people`:

        ## Audit Output (last 60 lines)

        ```
          📋 Required activity types from meta: fill-in, match-up
  📋 Template: docs/l2-uk-en/templates/a1-module-template.md (pedagogy: PPP)

  📊 Section Word Analysis:
     Розминка: Живе чи неживе?             451 /  300  ✅ (+151)
     Теорія: Як змінюються слова           522 /  600  ⚠️ (-78)
     Практика: Тренуємо форми              334 /  400  ⚠️ (-66)
     Використання: Моя сім'я та друзі      371 /  400  ✅ (-29)
     Культурний контекст: Друзі та імена   350 /  300  ✅ (+50)
     ────────────────────────────────────────────────────────────
     TOTAL                                2028 / 2000  ✅ (+28)
  ⏳ Content-only audit: activities/vocab gates DEFERRED
  ✨ Prose quality violations found: 1
     ❌ [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (3 occurrences): (To see), (To know), (To wait for) — breaks immersion target

📚 IMMERSION TOO LOW (14.6% vs 25-40% target)
   FIX: Convert simple explanations to Ukrainian
   FIX: Add more Ukrainian narratives/dialogues
   FIX: Use Ukrainian for engagement boxes (💡🎬🌍)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 2143/2000 (raw: 2644)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 6/3
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Ipa          ⚠️ 25 IPA issues (run lint_ipa.py --fix)
Lint         ✅ Clean Format
Pedagogy     ❌ 1 violations
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    ❌ 14.6% LOW (target 25-40% (M12))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (3 occurrences): (To see), (To know), (To wait for) — breaks immersion target
     → FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 25/100)
   → 1 violations (minor)
   → Immersion 10% off target


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/the-accusative-ii-people-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/the-accusative-ii-people.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-accusative-ii-people-audit.log for details)

Prose-relevant failures:
  lesson: 2143/2000 (raw: 2644) | pedagogy: 1 violations | immersion: 14.6% LOW (target 25-40% (M12))
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-accusative-ii-people.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

