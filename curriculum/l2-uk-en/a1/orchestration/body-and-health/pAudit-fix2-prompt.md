        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `body-and-health`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: body-and-health
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  body-and-health
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 2422/2000 (raw: 2595) | pedagogy: 1 violations

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Dative case not allowed until A2 (M31+). Restructure sentence.
    [METALANGUAGE] Metalanguage terms used but not in vocabulary: прикметник, дієслово
       → FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 2 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/body-and-health-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/body-and-health.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/body-and-health-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/body-and-health.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

