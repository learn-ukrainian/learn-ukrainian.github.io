        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `combined-practice`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: combined-practice
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  combined-practice
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 2645/2000 (raw: 2885) | pedagogy: 19 violations | immersion: 19.0% LOW (target 35-55% (M43))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Replace second «і»/«й» with «та» for conjunction variety


  🔄 RECOMMENDATION: REWRITE FROM SCRATCH (severity 90/100)
     → 19 violations (severe - consider revision)
     → 15 grammar-level violations (fundamental)
     → Immersion 16% off target


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/combined-practice-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/combined-practice.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/combined-practice-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/combined-practice.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

