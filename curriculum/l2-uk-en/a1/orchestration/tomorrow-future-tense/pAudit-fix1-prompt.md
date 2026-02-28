        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `tomorrow-future-tense`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: tomorrow-future-tense
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  tomorrow-future-tense
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 3464/2000 (raw: 3672) | engagement: 0/3 | pedagogy: 17 violations | immersion: 24.8% LOW (target 35-55% (M37))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.


  🔄 RECOMMENDATION: REWRITE FROM SCRATCH (severity 90/100)
     → 18 violations (severe - consider revision)
     → 6 grammar-level violations (fundamental)
     → Immersion 10% off target


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/tomorrow-future-tense-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/tomorrow-future-tense.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/tomorrow-future-tense-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/tomorrow-future-tense.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

