        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `the-instrumental-i-accompaniment`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: the-instrumental-i-accompaniment
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  the-instrumental-i-accompaniment
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  3 Outline Compliance Errors
  failing gates:
    lesson: 2432/3000 (raw: 2663) | pedagogy: 6 violations | immersion: 23.9% LOW (target 50-60% (A2.1))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 70/100)
     → Revision recommended (severity 70/100)
     → 7 violations (significant)
     → Immersion 26% off target (major rebalancing needed)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/the-instrumental-i-accompaniment-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/the-instrumental-i-accompaniment.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • 3 Outline Compliance Errors

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-instrumental-i-accompaniment-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/the-instrumental-i-accompaniment.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

