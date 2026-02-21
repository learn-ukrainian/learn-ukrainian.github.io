        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `phone-basics`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  HETMAN VERIFY: phone-basics
============================================================

[1/4] Running full audit...
[2/4] Checking sidecar files...
[3/4] Reading status JSON...
[4/4] Checking overall status...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  phone-basics
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  overall status is 'fail' (must be 'pass')
  Structure: Missing '## Summary'
  failing gates:
    meta: Missing '## Summary'
    lesson: 2147/2000 (raw: 2330) | pedagogy: 2 violations

  Hetman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───

  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 25/100)
     → 2 violations (minor)
     → Structure issue: Missing '## Summary'


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/phone-basics-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/phone-basics.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • Structure: Missing '## Summary'

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/phone-basics-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/phone-basics.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/phone-basics.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/phone-basics.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

