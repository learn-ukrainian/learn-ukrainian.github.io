        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `checkpoint-cases`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: checkpoint-cases
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  checkpoint-cases
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  Checkpoint Format Errors

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  Grammar      ℹ️ N/A (covered by naturalness)
  Naturalness  ℹ️ PENDING — awaiting review
  Activity_quality ⏳ Deferred (content-only audit)
  Research     ✅ Content aligned with research
  Immersion    🇺🇦 20.1% (checkpoint - no gate)

  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/checkpoint-cases-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/checkpoint-cases.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • Checkpoint Format Errors

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/checkpoint-cases-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/checkpoint-cases.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

