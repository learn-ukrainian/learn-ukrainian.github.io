        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `the-living-verb-ii`:

        ## Audit Output (last 60 lines)

        ```

📋 Auditing: A1 M08 — The Living Verb II
   File: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-living-verb-ii.md | Target: 2000 words
  📋 Required activity types from meta: fill-in, match-up
  📋 Template: docs/l2-uk-en/templates/a1-module-template.md (pedagogy: PPP)

  📊 Section Word Analysis:
     Вступ: Світ дієслів                   322 /  250  ✅ (+72)
     Граматика: Друга дієвідміна          1059 /  900  ✅ (+159)
     Практика: Тренування                  253 /  450  ❌ (-197)
     Використання: Розповідаємо про себе   308 /  200  ✅ (+108)
     Культура: Глибина слова               275 /  200  ✅ (+75)
     ────────────────────────────────────────────────────────────
     TOTAL                                2217 / 2000  ✅ (+217)
  ⏳ Content-only audit: activities/vocab gates DEFERRED

📚 IMMERSION TOO LOW (15.0% vs 15-35% target)
   FIX: Convert simple explanations to Ukrainian
   FIX: Add more Ukrainian narratives/dialogues
   FIX: Use Ukrainian for engagement boxes (💡🎬🌍)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 2557/2000 (raw: 2791)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 6/3
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Ipa          ⚠️ 22 IPA issues (run lint_ipa.py --fix)
Lint         ✅ Clean Format
Pedagogy     ❌ 1 violations
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    ❌ 15.0% LOW (target 15-35% (M08))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [COMPLEXITY] Sentence too long for A1: 16 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Хто не любить своєї рідної...'


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
   → 1 violations (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/the-living-verb-ii-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/the-living-verb-ii.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-living-verb-ii-audit.log for details)

Prose-relevant failures:
  lesson: 2557/2000 (raw: 2791) | pedagogy: 1 violations | immersion: 15.0% LOW (target 15-35% (M08))
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-living-verb-ii.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

