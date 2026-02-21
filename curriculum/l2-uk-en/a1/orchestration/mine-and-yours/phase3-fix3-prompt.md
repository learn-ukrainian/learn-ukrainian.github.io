        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `mine-and-yours`:

        ## Audit Output (last 60 lines)

        ```
        Auditing: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/mine-and-yours.md
Mode: content-only (activities deferred)
Saving log to: curriculum/l2-uk-en/krisztiankoos/audit/mine-and-yours-audit.log


========================================
  📋 Loaded Plan from: plans/a1/mine-and-yours.yaml
  📋 Loaded Metadata from YAML sidecar

📋 Auditing: A1 M14 — Mine and Yours
   File: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/mine-and-yours.md | Target: 2000 words
  📋 Required activity types from meta: fill-in, match-up, quiz, true-false
  📋 Template: docs/l2-uk-en/templates/a1-module-template.md (pedagogy: PPP)

  📊 Section Word Analysis:
     Вступ: Бюро знахідок        360 /  250  ✅ (+110)
     Граматика: Мій, твій, наш   889 /  750  ✅ (+139)
     Практика: Чия це річ?       448 /  400  ✅ (+48)
     Діалоги: Це мій телефон     432 /  300  ✅ (+132)
     Культура: Твій чи Ваш?      449 /  300  ✅ (+149)
     ──────────────────────────────────────────────────
     TOTAL                      2578 / 2000  ✅ (+578)
  ⏳ Content-only audit: activities/vocab gates DEFERRED

📚 IMMERSION TOO LOW (22.0% vs 25-40% target)
   FIX: Convert simple explanations to Ukrainian
   FIX: Add more Ukrainian narratives/dialogues
   FIX: Use Ukrainian for engagement boxes (💡🎬🌍)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 2781/2000 (raw: 3261)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 5/3
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Ipa          ⚠️ 5 IPA issues (run lint_ipa.py --fix)
Lint         ✅ Clean Format
Pedagogy     ✅ Level-appropriate
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    ❌ 22.0% LOW (target 25-40% (M14))

Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/mine-and-yours-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/mine-and-yours.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/mine-and-yours-audit.log for details)

Prose-relevant failures:
  lesson: 2781/2000 (raw: 3261) | immersion: 22.0% LOW (target 25-40% (M14))
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/mine-and-yours.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

