        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `practical-intro`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: practical-intro
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  practical-intro
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  Structure: Missing '## Summary'
  failing gates:
    meta: Missing '## Summary'
    lesson: 3560/3000 (raw: 3758) | pedagogy: 5 violations | immersion: 91.2% HIGH (target 75-90% (A2.3))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 70/100)
     → Revision recommended (severity 70/100)
     → 22 violations (severe - consider revision)
     → Structure issue: Missing '## Summary'


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/practical-intro-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/practical-intro.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • Structure: Missing '## Summary'

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/practical-intro-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/practical-intro.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

