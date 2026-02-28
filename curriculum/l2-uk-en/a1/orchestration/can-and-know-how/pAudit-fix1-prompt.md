        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `can-and-know-how`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: can-and-know-how
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  can-and-know-how
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 3666/2000 (raw: 4123) | pedagogy: 3 violations | immersion: 7.9% LOW (target 35-55% (M45))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Vary sentence structure.


  🔄 RECOMMENDATION: REWRITE FROM SCRATCH (severity 75/100)
     → 5 violations (moderate)
     → 3 grammar-level violations (fundamental)
     → Immersion 27% off target (major rebalancing needed)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/can-and-know-how-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/can-and-know-how.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/can-and-know-how-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/can-and-know-how.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

