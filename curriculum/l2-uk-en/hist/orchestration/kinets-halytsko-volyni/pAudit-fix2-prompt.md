        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `kinets-halytsko-volyni`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: kinets-halytsko-volyni
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  kinets-halytsko-volyni
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  2 Outline Compliance Errors

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  Naturalness  ℹ️ PENDING — awaiting review
  Activity_quality ⏳ Deferred (content-only audit)
  Research     ✅ Content aligned with research
  Immersion    🇺🇦 98.5% (target 90-100% (history))
  Richness     ✅ 99% (history)

  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/audit/kinets-halytsko-volyni-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/status/kinets-halytsko-volyni.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • 2 Outline Compliance Errors

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/kinets-halytsko-volyni-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/kinets-halytsko-volyni.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

