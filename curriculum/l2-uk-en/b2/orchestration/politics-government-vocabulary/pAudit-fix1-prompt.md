        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `politics-government-vocabulary`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: politics-government-vocabulary
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  politics-government-vocabulary
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  4 Outline Compliance Errors
  failing gates:
    lesson: 3199/4000 (raw: 3454) | richness: 93% < 95% min (grammar)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  Naturalness  ℹ️ PENDING — awaiting review
  Activity_quality ⏳ Deferred (content-only audit)
  Research     ✅ Content aligned with research
  Immersion    🇺🇦 97.3% (target 90-100% (grammar))
  Richness     ❌ 93% < 95% min (grammar)

  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/audit/politics-government-vocabulary-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/status/politics-government-vocabulary.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • 4 Outline Compliance Errors

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/politics-government-vocabulary-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/politics-government-vocabulary.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

