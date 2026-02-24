        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `food-and-cooking`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: food-and-cooking
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  food-and-cooking
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  1 Outline Compliance Errors
  failing gates:
    lesson: 4919/3000 (raw: 5244) | pedagogy: 44 violations | immersion: 83.9% HIGH (target 60-75% (A2.3))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  🔄 RECOMMENDATION: REWRITE FROM SCRATCH (severity 80/100)
     → 46 violations (severe - consider revision)
     → 7 grammar-level violations (fundamental)
     → Immersion 9% off target (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/food-and-cooking-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/food-and-cooking.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • 1 Outline Compliance Errors

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/food-and-cooking-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/food-and-cooking.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

