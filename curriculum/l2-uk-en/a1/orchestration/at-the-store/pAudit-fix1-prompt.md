        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `at-the-store`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: at-the-store
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  at-the-store
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  1 Outline Compliance Errors
  failing gates:
    lesson: 2145/2000 (raw: 2304) | pedagogy: 2 violations | immersion: 15.5% LOW (target 35-55% (M38))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───

  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 25/100)
     → 2 violations (minor)
     → Immersion 19% off target


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/at-the-store-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/at-the-store.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • 1 Outline Compliance Errors

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/at-the-store-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/at-the-store.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

