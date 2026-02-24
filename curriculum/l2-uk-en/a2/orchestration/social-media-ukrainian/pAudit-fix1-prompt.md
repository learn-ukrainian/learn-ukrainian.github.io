        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `social-media-ukrainian`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: social-media-ukrainian
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  social-media-ukrainian
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  Structure: Missing '## Summary'
  failing gates:
    meta: Missing '## Summary'
    lesson: 4123/3000 (raw: 4397) | engagement: 0/4 | pedagogy: 4 violations

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
     → Revision recommended (severity 55/100)
     → 5 violations (moderate)
     → 3 grammar-level violations (fundamental)
     → Structure issue: Missing '## Summary'


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/social-media-ukrainian-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/social-media-ukrainian.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • Structure: Missing '## Summary'

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/social-media-ukrainian-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/social-media-ukrainian.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

