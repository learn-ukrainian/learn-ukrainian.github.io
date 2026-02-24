        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `checkpoint-motion-verbs`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: checkpoint-motion-verbs
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  checkpoint-motion-verbs
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  Checkpoint Format Errors

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  Naturalness  ℹ️ PENDING — awaiting review
  Activity_quality ⏳ Deferred (content-only audit)
  Research     ✅ Content aligned with research
  Immersion    🇺🇦 99.3% (checkpoint - no gate)
  Richness     ✅ 99% (checkpoint)

  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/audit/checkpoint-motion-verbs-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/status/checkpoint-motion-verbs.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • Checkpoint Format Errors

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/checkpoint-motion-verbs-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/checkpoint-motion-verbs.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

