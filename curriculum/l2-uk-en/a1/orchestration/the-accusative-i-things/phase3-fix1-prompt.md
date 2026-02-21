        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `the-accusative-i-things`:

        ## Audit Output (last 60 lines)

        ```
             Практика: Вчимося змінювати закінчення     306 /  400  ❌ (-94)
     Ситуація: У магазині та вдома              215 /  400  ❌ (-185)
     Культурний погляд: Базар чи супермаркет?   210 /  300  ❌ (-90)
     ─────────────────────────────────────────────────────────────────
     TOTAL                                     1398 / 2000  ❌ (-602)
  ⏳ Content-only audit: activities/vocab gates DEFERRED

📚 IMMERSION TOO LOW (16.8% vs 25-40% target)
   FIX: Convert simple explanations to Ukrainian
   FIX: Add more Ukrainian narratives/dialogues
   FIX: Use Ukrainian for engagement boxes (💡🎬🌍)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ❌ 1639/2000 (raw: 1862)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 3/3
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Ipa          ⚠️ 24 IPA issues (run lint_ipa.py --fix)
Lint         ❌ 1 Format Errors
Pedagogy     ❌ 1 violations
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    ❌ 16.8% LOW (target 25-40% (M11))

❌ LINT ERRORS FOUND:
  - Line 156: AI Contamination detected ('\bSelf-correction\b'). Remove thinking/self-correction artifacts.


📚 PEDAGOGICAL VIOLATIONS FOUND:
  [GRAMMAR] Dative case used at A1: 'Ключові'
     → FIX: Dative case not allowed until A2 (M31+). Restructure sentence.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 17/100)
   → 1 violations (minor)
   → Immersion 8% off target (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/the-accusative-i-things-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/the-accusative-i-things.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • 4 Outline Compliance Errors

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-accusative-i-things-audit.log for details)

Prose-relevant failures:
  meta: Valid Structure | Lint: 1 Format Errors
  lesson: 1639/2000 (raw: 1862) | pedagogy: 1 violations | immersion: 16.8% LOW (target 25-40% (M11))
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-accusative-i-things.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

