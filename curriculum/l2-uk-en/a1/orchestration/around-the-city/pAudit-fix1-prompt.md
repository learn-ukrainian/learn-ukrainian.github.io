        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `around-the-city`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: around-the-city
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  around-the-city
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 3210/2000 (raw: 3409) | pedagogy: 16 violations | immersion: 21.5% LOW (target 35-55% (M29))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Break into shorter sentences. First 5 words: 'Коли ми знаємо назви місць...'


  🔄 RECOMMENDATION: REWRITE FROM SCRATCH (severity 90/100)
     → 16 violations (severe - consider revision)
     → 15 grammar-level violations (fundamental)
     → Immersion 13% off target


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/around-the-city-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/around-the-city.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/around-the-city-audit.log for details)
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

