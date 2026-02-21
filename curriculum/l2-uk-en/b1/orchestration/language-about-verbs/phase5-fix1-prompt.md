        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `language-about-verbs`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  HETMAN VERIFY: language-about-verbs
============================================================

[1/4] Running full audit...
[2/4] Checking sidecar files...
[3/4] Reading status JSON...
[4/4] Checking overall status...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  language-about-verbs
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  overall status is 'fail' (must be 'pass')
  Missing required activity types: fill-in
  failing gates:
    lesson: 4633/4000 (raw: 5027) | pedagogy: 5 violations
    activities: 6/4 | density: 2 < 6

  Hetman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───

  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 25/100)
     → 5 violations (moderate)
     → Activity density below minimum


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/audit/language-about-verbs-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/status/language-about-verbs.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • Missing required activity types: fill-in

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/language-about-verbs-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/language-about-verbs.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/activities/language-about-verbs.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/vocabulary/language-about-verbs.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

