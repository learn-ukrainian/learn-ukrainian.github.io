        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `checkpoint-aspect-comparison`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: checkpoint-aspect-comparison
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  checkpoint-aspect-comparison
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  Checkpoint Format Errors
  failing gates:
    meta: Valid Structure | Lint: 1 Format Errors
    lesson: 6684/2500 (raw: 7382) | engagement: 0/3 | pedagogy: 31 violations

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 72/100)
     → Revision recommended (severity 72/100)
     → 34 violations (severe - consider revision)
     → 3 grammar-level violations (fundamental)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/checkpoint-aspect-comparison-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/checkpoint-aspect-comparison.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • Checkpoint Format Errors

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/checkpoint-aspect-comparison-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/checkpoint-aspect-comparison.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

