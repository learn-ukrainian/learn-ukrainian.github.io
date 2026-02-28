        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `the-cyrillic-code-iv`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: the-cyrillic-code-iv
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  the-cyrillic-code-iv
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  1 Outline Compliance Errors
  failing gates:
    meta: Valid Structure | Lint: 2 Format Errors
    lesson: 3593/2000 (raw: 3782) | pedagogy: 3 violations | immersion: 4.1% LOW (target 10-25% (M04))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───

  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 17/100)
     → 3 violations (minor)
     → Immersion 6% off target (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/the-cyrillic-code-iv-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/the-cyrillic-code-iv.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • 1 Outline Compliance Errors

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-cyrillic-code-iv-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-cyrillic-code-iv.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

