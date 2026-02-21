        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `at-the-restaurant`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  HETMAN VERIFY: at-the-restaurant
============================================================

[1/4] Running full audit...
[2/4] Checking sidecar files...
[3/4] Reading status JSON...
[4/4] Checking overall status...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  at-the-restaurant
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  overall status is 'fail' (must be 'pass')
  Missing required activity types: fill-in, match-up, quiz
  failing gates:
    lesson: 2882/2000 (raw: 3094) | pedagogy: 2 violations
    activities: 0/8 | density: 0 < 12 | unique_types: 0/4 types | priority: No priority types

  Hetman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 30/100)
     → 2 violations (minor)
     → Activity count below minimum
     → Activity density below minimum


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/at-the-restaurant-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/at-the-restaurant.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • Missing required activity types: fill-in, match-up, quiz

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/at-the-restaurant-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/at-the-restaurant.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/at-the-restaurant.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/at-the-restaurant.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

