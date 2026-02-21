        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `yesterday-past-tense`:

        ## Audit Output (last 60 lines)

        ```
        Mode: content-only (activities deferred)
Saving log to: curriculum/l2-uk-en/krisztiankoos/audit/yesterday-past-tense-audit.log


========================================
  📋 Loaded Plan from: plans/a1/yesterday-past-tense.yaml
  📋 Loaded Metadata from YAML sidecar

📋 Auditing: A1 M21 — Yesterday - Past Tense
   File: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/yesterday-past-tense.md | Target: 2000 words
  📋 Required activity types from meta: fill-in
  📋 Template: docs/l2-uk-en/templates/a1-module-template.md (pedagogy: PPP)

  📊 Section Word Analysis:
     Розминка: Вчора і сьогодні       512 /  400  ✅ (+112)
     Граматика: Минулий час дієслів  1049 / 1000  ✅ (+49)
     Практика: Спогади про вчора      594 /  600  ✅ (-6)
     ───────────────────────────────────────────────────────
     TOTAL                           2155 / 2000  ✅ (+155)
  ⏳ Content-only audit: activities/vocab gates DEFERRED

📚 IMMERSION TOO LOW (27.9% vs 35-55% target)
   FIX: Convert simple explanations to Ukrainian
   FIX: Add more Ukrainian narratives/dialogues
   FIX: Use Ukrainian for engagement boxes (💡🎬🌍)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 2415/2000 (raw: 2741)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 6/3
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Ipa          ✅ Clean IPA
Lint         ✅ Clean Format
Pedagogy     ✅ Level-appropriate
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    ❌ 27.9% LOW (target 35-55% (M21))

📝 RECOMMENDATION: UPDATE (patch fixes) (severity 10/100)
   → Immersion 7% off target (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/yesterday-past-tense-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/yesterday-past-tense.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/yesterday-past-tense-audit.log for details)

Prose-relevant failures:
  lesson: 2415/2000 (raw: 2741) | immersion: 27.9% LOW (target 35-55% (M21))
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/yesterday-past-tense.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

