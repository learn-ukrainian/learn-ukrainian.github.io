        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `at-the-cafe-practical`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: at-the-cafe-practical
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  at-the-cafe-practical
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 2031/2000 (raw: 2381) | immersion: 16.7% LOW (target 35-55% (M35))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  Naturalness  ℹ️ PENDING — awaiting review
  Activity_quality ⏳ Deferred (content-only audit)
  Research     ✅ Content aligned with research
  Immersion    ❌ 16.7% LOW (target 35-55% (M35))

  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 20/100)
     → Immersion 18% off target


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/at-the-cafe-practical-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/at-the-cafe-practical.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/at-the-cafe-practical-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/at-the-cafe-practical.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

