        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `b2-review-bridge`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  HETMAN VERIFY: b2-review-bridge
============================================================

[1/4] Running full audit...
[2/4] Checking sidecar files...
[3/4] Reading status JSON...
[4/4] Checking overall status...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  b2-review-bridge
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  overall status is 'fail' (must be 'pass')
  failing gates:
    lesson: 5029/4000 (raw: 5432) | pedagogy: 3 violations | richness: 94% < 95% min (grammar)
    activities: 14/12 | density: 2 < 12

  Hetman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
    [MISSING_ADVANCED_ACTIVITY] B2+ module (focus: grammar) missing advanced activity type: essay-response
       → FIX: Add a essay-response activity to meet advanced richness standards.


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 15/100)
     → 3 violations (minor)
     → Activity density below minimum


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1/audit/b2-review-bridge-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1/status/b2-review-bridge.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/b2-review-bridge-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1/b2-review-bridge.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1/activities/b2-review-bridge.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1/vocabulary/b2-review-bridge.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

