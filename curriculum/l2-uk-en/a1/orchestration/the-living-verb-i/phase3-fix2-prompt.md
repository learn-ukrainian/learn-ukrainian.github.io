        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `the-living-verb-i`:

        ## Audit Output (last 60 lines)

        ```
          📋 Required activity types from meta: fill-in, match-up
  📋 Template: docs/l2-uk-en/templates/a1-module-template.md (pedagogy: PPP)

  📊 Section Word Analysis:
     Дієслова: Рух і Дія             556 /  300  ✅ (+256)
     Магія закінчень: Група -ати     790 /  800  ✅ (-10)
     Практика: Я читаю, ти слухаєш   618 /  600  ✅ (+18)
     Культурний код: Сила слова      342 /  300  ✅ (+42)
     ──────────────────────────────────────────────────────
     TOTAL                          2306 / 2000  ✅ (+306)
  ⏳ Content-only audit: activities/vocab gates DEFERRED
  ✨ Prose quality violations found: 1
     ❌ [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (3 occurrences): (Think about it), (Look at the objects), (Check yourself) — breaks immersion target

📚 IMMERSION TOO LOW (14.9% vs 15-35% target)
   FIX: Convert simple explanations to Ukrainian
   FIX: Add more Ukrainian narratives/dialogues
   FIX: Use Ukrainian for engagement boxes (💡🎬🌍)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 2623/2000 (raw: 2974)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 5/3
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Ipa          ⚠️ 13 IPA issues (run lint_ipa.py --fix)
Lint         ✅ Clean Format
Pedagogy     ❌ 2 violations
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    ❌ 14.9% LOW (target 15-35% (M06))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [GRAMMAR] Subordinate clause marker at A1: 'Якщо в'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (3 occurrences): (Think about it), (Look at the objects), (Check yourself) — breaks immersion target
     → FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
   → 2 violations (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/the-living-verb-i-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/the-living-verb-i.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-living-verb-i-audit.log for details)

Prose-relevant failures:
  lesson: 2623/2000 (raw: 2974) | pedagogy: 2 violations | immersion: 14.9% LOW (target 15-35% (M06))
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

