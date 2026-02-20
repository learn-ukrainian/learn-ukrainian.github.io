        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `can-must-want-modals`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  HETMAN VERIFY: can-must-want-modals
============================================================

[1/4] Running full audit...
[2/4] Checking sidecar files...
[3/4] Reading status JSON...
[4/4] Checking overall status...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  can-must-want-modals
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  overall status is 'fail' (must be 'pass')
  Structure: Missing '## Activities' header OR activities sidecar
  Missing required activity types: fill-in
  failing gates:
    meta: Missing '## Activities' header OR activities sidecar
    lesson: 2170/2000 (raw: 2740) | pedagogy: 47 violations | immersion: 75.7% HIGH (target 35-55% (M24))
    activities: 0/8 | density: 0 < 12 | unique_types: 0/4 types | priority: No priority types
  missing sidecar files:
    activities/can-must-want-modals.yaml
    vocabulary/can-must-want-modals.yaml

  Hetman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
     → Structure issue: Missing '## Activities' header OR activities sidecar
     → Activity count below minimum
     → Activity density below minimum


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/can-must-want-modals-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/can-must-want-modals.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • Structure: Missing '## Activities' header OR activities sidecar
    • Missing required activity types: fill-in

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/can-must-want-modals-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/can-must-want-modals.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/can-must-want-modals.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/can-must-want-modals.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

