        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `around-the-city`:

        ## Audit Output (last 60 lines)

        ```
          📋 Template: docs/l2-uk-en/templates/a1-module-template.md (pedagogy: PPP)

  📊 Section Word Analysis:
     Вступ: Місто та орієнтири        318 /  200  ✅ (+118)
     Лексика: Напрямки та місця       576 /  500  ✅ (+76)
     Граматика: Прийменники та рух    542 /  500  ✅ (+42)
     Практика: Маршрути та діалоги    327 /  400  ⚠️ (-73)
     Творче завдання: Ваш шлях        146 /  200  ❌ (-54)
     Культура: Українська навігація   246 /  200  ✅ (+46)
     ───────────────────────────────────────────────────────
     TOTAL                           2155 / 2000  ✅ (+155)
  ⏳ Content-only audit: activities/vocab gates DEFERRED
  ✨ Prose quality violations found: 1
     ❌ [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (4 occurrences): (Locative case), (In front of), (In front of) — breaks immersion target

📚 IMMERSION TOO LOW (16.2% vs 25-40% target)
   FIX: Convert simple explanations to Ukrainian
   FIX: Add more Ukrainian narratives/dialogues
   FIX: Use Ukrainian for engagement boxes (💡🎬🌍)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 2353/2000 (raw: 2708)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 6/3
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Ipa          ⚠️ 18 IPA issues (run lint_ipa.py --fix)
Lint         ✅ Clean Format
Pedagogy     ❌ 1 violations
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    ❌ 16.2% LOW (target 25-40% (M15))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (4 occurrences): (Locative case), (In front of), (In front of) — breaks immersion target
     → FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 15/100)
   → 1 violations (minor)
   → Immersion 9% off target (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/around-the-city-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/around-the-city.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/around-the-city-audit.log for details)

Prose-relevant failures:
  lesson: 2353/2000 (raw: 2708) | pedagogy: 1 violations | immersion: 16.2% LOW (target 25-40% (M15))
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/around-the-city.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

