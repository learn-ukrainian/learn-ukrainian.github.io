        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `scythians-sarmatians`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  HETMAN VERIFY: scythians-sarmatians
============================================================

[1/4] Running full audit...
[2/4] Checking sidecar files...
[3/4] Reading status JSON...
[4/4] Checking overall status...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  scythians-sarmatians
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  overall status is 'fail' (must be 'pass')
  3 Outline Compliance Errors
  failing gates:
    lesson: 4205/5000 (raw: 4417)

  Hetman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  Naturalness  ℹ️ PENDING — awaiting review
  Activity_quality 📋 Quality validation available (optional)
  Research     ✅ Content aligned with research
  Immersion    🇺🇦 99.6% (target 90-100% (history))
  Richness     ✅ 95% (history)

  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/audit/scythians-sarmatians-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/status/scythians-sarmatians.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • 3 Outline Compliance Errors

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/scythians-sarmatians-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/scythians-sarmatians.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/activities/scythians-sarmatians.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/vocabulary/scythians-sarmatians.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

