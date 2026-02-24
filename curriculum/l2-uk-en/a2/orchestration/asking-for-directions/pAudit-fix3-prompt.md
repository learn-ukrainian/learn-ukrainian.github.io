        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `asking-for-directions`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: asking-for-directions
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  asking-for-directions
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 5251/3000 (raw: 5683) | pedagogy: 81 violations | immersion: 98.1% HIGH (target 75-90% (A2.3))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section


  🔄 RECOMMENDATION: REWRITE FROM SCRATCH (severity 80/100)
     → 84 violations (severe - consider revision)
     → 7 grammar-level violations (fundamental)
     → Immersion 8% off target (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/asking-for-directions-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/asking-for-directions.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/asking-for-directions-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/asking-for-directions.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

