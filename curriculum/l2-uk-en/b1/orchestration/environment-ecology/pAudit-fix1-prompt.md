        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `environment-ecology`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: environment-ecology
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  environment-ecology
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  4 Outline Compliance Errors
  failing gates:
    lesson: 3124/4000 (raw: 3318) | richness: 71% < 95% min (vocabulary)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  Naturalness  ℹ️ PENDING — awaiting review
  Activity_quality ⏳ Deferred (content-only audit)
  Research     ✅ Content aligned with research
  Immersion    🇺🇦 96.0% (target 85-100% (B1.5-6 Vocab))
  Richness     ❌ 71% < 95% min (vocabulary)

  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/audit/environment-ecology-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/status/environment-ecology.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • 4 Outline Compliance Errors

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/environment-ecology-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/environment-ecology.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

