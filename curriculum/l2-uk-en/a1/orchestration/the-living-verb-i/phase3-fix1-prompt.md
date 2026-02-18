        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `the-living-verb-i`:

        ## Audit Output (last 60 lines)

        ```
          📋 Required activity types from meta: fill-in, match-up
  📋 Template: docs/l2-uk-en/templates/a1-module-template.md (pedagogy: PPP)

  📊 Section Word Analysis:
     Дієслова: Рух і Дія             564 /  300  ✅ (+264)
     Магія закінчень: Група -ати     783 /  800  ✅ (-17)
     Практика: Я читаю, ти слухаєш   508 /  600  ⚠️ (-92)
     Культурний код: Сила слова      342 /  300  ✅ (+42)
     ──────────────────────────────────────────────────────
     TOTAL                          2197 / 2000  ✅ (+197)
  ⏳ Content-only audit: activities/vocab gates DEFERRED
  ✨ Prose quality violations found: 1
     ❌ [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (3 occurrences): (One person), (Many people), (Do you) — breaks immersion target

📚 IMMERSION TOO LOW (12.0% vs 15-35% target)
   FIX: Convert simple explanations to Ukrainian
   FIX: Add more Ukrainian narratives/dialogues
   FIX: Use Ukrainian for engagement boxes (💡🎬🌍)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 2497/2000 (raw: 2849)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 4/3
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Ipa          ⚠️ 14 IPA issues (run lint_ipa.py --fix)
Lint         ✅ Clean Format
Pedagogy     ❌ 1 violations
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    ❌ 12.0% LOW (target 15-35% (M06))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [METALANGUAGE] Metalanguage terms used but not in vocabulary: дієслово
     → FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.
  [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (3 occurrences): (One person), (Many people), (Do you) — breaks immersion target
     → FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
   → 2 violations (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/the-living-verb-i-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/the-living-verb-i.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-living-verb-i-audit.log for details)

Prose-relevant failures:
  lesson: 2497/2000 (raw: 2849) | pedagogy: 1 violations | immersion: 12.0% LOW (target 15-35% (M06))
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-living-verb-i.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

