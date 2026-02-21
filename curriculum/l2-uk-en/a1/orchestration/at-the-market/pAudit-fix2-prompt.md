        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `at-the-market`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: at-the-market
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  at-the-market
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 2008/2000 (raw: 2261) | pedagogy: 1 violations | immersion: 24.2% LOW (target 35-55% (M37))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
    [GRAMMAR] Subordinate clause marker at A1: 'Бо т'
       → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 25/100)
     → 1 violations (minor)
     → Immersion 11% off target


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/at-the-market-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/at-the-market.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/at-the-market-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/at-the-market.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

