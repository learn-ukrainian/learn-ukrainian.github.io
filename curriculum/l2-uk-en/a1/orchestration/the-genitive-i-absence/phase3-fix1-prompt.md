        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `the-genitive-i-absence`:

        ## Audit Output (last 60 lines)

        ```
        Saving log to: curriculum/l2-uk-en/krisztiankoos/audit/the-genitive-i-absence-audit.log


========================================
  📋 Loaded Plan from: plans/a1/the-genitive-i-absence.yaml
  📋 Loaded Metadata from YAML sidecar

📋 Auditing: A1 M16 — The Genitive I: Absence
   File: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-genitive-i-absence.md | Target: 2000 words
  📋 Required activity types from meta: fill-in
  📋 Template: docs/l2-uk-en/templates/a1-module-template.md (pedagogy: PPP)

  📊 Section Word Analysis:
     Вступ: Ситуація відсутності               408 /  300  ✅ (+108)
     Граматика: Конструкція 'Немає' та 'Без'   867 /  800  ✅ (+67)
     Практика: Родовий відмінок у дії          475 /  500  ✅ (-25)
     Культурний контекст: 'Немає проблем'      287 /  400  ❌ (-113)
     ────────────────────────────────────────────────────────────────
     TOTAL                                    2037 / 2000  ✅ (+37)
  ⏳ Content-only audit: activities/vocab gates DEFERRED

📚 IMMERSION TOO LOW (17.7% vs 25-40% target)
   FIX: Convert simple explanations to Ukrainian
   FIX: Add more Ukrainian narratives/dialogues
   FIX: Use Ukrainian for engagement boxes (💡🎬🌍)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 2232/2000 (raw: 2549)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 5/3
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Ipa          ⚠️ 10 IPA issues (run lint_ipa.py --fix)
Lint         ✅ Clean Format
Pedagogy     ✅ Level-appropriate
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    ❌ 17.7% LOW (target 25-40% (M16))

📝 RECOMMENDATION: UPDATE (patch fixes) (severity 10/100)
   → Immersion 7% off target (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/the-genitive-i-absence-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/the-genitive-i-absence.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-genitive-i-absence-audit.log for details)

Prose-relevant failures:
  lesson: 2232/2000 (raw: 2549) | immersion: 17.7% LOW (target 25-40% (M16))
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-genitive-i-absence.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

