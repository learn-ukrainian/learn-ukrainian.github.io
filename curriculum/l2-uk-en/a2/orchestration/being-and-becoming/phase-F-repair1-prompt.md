        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `being-and-becoming`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  HETMAN VERIFY: being-and-becoming
============================================================

[1/4] Running full audit...
[2/4] Checking sidecar files...
[3/4] Reading status JSON...
[4/4] Checking overall status...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  being-and-becoming
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  overall status is 'fail' (must be 'pass')
  Structure: Missing '## Vocabulary' header OR vocabulary sidecar
  failing gates:
    meta: Missing '## Vocabulary' header OR vocabulary sidecar

  Hetman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───

  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 25/100)
     → 1 violations (minor)
     → Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/being-and-becoming-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/being-and-becoming.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • Structure: Missing '## Vocabulary' header OR vocabulary sidecar

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/being-and-becoming-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/being-and-becoming.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/being-and-becoming.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/vocabulary/being-and-becoming.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

