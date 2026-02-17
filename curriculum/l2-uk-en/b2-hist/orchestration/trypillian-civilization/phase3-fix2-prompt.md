        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `trypillian-civilization`:

        ## Audit Output (last 60 lines)

        ```
           File: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2-hist/trypillian-civilization.md | Target: 6133 words
  📋 Required activity types from meta: comparative-study, critical-analysis, essay-response, reading
  📋 Template: docs/l2-uk-en/templates/b2-history-module-template.md (pedagogy: CBI)

  📊 Section Word Analysis:
     Вступ                                549 /  489  ✅ (+60)
     Читання                              757 /  489  ✅ (+268)
     Історія відкриття                    603 /  503  ✅ (+100)
     Первинні джерела                     607 /  337  ✅ (+270)
     Протоміста                          1048 / 1084  ✅ (-36)
     Господарство та економіка            874 /  641  ✅ (+233)
     Ремесла та технології               1040 /  792  ✅ (+248)
     Духовний світ та суспільний устрій   547 /  582  ✅ (-35)
     Деколонізаційний погляд              577 /  413  ✅ (+164)
     Потрібно більше практики?           1024 /  803  ✅ (+221)
     ───────────────────────────────────────────────────────────
     TOTAL                               7626 / 6133  ✅ (+1493)
  ⏳ Content-only audit: activities/vocab gates DEFERRED

--- STRICT GATES (Level B2) ---
Persona      ✅ Persona Defined
Words        ✅ 7927/6133 (raw: 8250)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 12/5
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Ipa          ⚠️ 6 IPA issues (run lint_ipa.py --fix)
Lint         ✅ Clean Format
Pedagogy     ❌ 2 violations
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Immersion    🇺🇦 98.3% (target 90-100% (history))
Richness     ✅ 99% (history)

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [MISSING_ADVANCED_ACTIVITY] B2+ module (focus: history) missing advanced activity type: essay-response
     → FIX: Add a essay-response activity to meet advanced richness standards.
  [MISSING_ADVANCED_ACTIVITY] B2+ module (focus: history) missing advanced activity type: comparative-study
     → FIX: Add a comparative-study activity to meet advanced richness standards.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
   → 2 violations (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2-hist/audit/trypillian-civilization-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2-hist/status/trypillian-civilization.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/trypillian-civilization-audit.log for details)

Prose-relevant failures:
  lesson: 7927/6133 (raw: 8250) | pedagogy: 2 violations
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2-hist/trypillian-civilization.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

