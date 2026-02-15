        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `the-accusative-ii-people`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: the-accusative-ii-people
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  the-accusative-ii-people
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  Structure: Missing '## Summary'
  failing gates:
    meta: Missing '## Summary'
    lesson: 3266/1374 (raw: 3658) | engagement: 1/3 | pedagogy: 1 violations | immersion: 16.0% LOW (target 25-40% (M12))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 35/100)
     → 2 violations (minor)
     → Immersion 9% off target (minor)
     → Structure issue: Missing '## Summary'


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/the-accusative-ii-people-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/the-accusative-ii-people.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • Structure: Missing '## Summary'

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-accusative-ii-people-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-accusative-ii-people.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

