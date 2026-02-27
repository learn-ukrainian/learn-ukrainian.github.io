        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `zasnuvannia-kyieva`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: zasnuvannia-kyieva
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  zasnuvannia-kyieva
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  7 Outline Compliance Errors
  failing gates:
    lesson: 4165/5000 (raw: 4542) | engagement: 0/5 | pedagogy: 5 violations | richness: 76% < 95% min (history)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 15/100)
     → 5 violations (moderate)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/audit/zasnuvannia-kyieva-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/status/zasnuvannia-kyieva.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • 7 Outline Compliance Errors

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/zasnuvannia-kyieva-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/zasnuvannia-kyieva.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

