        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `voienna-ekonomika`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: voienna-ekonomika
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  voienna-ekonomika
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  5 Outline Compliance Errors
  failing gates:
    lesson: 4757/5000 (raw: 5130)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 1 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2-hist/audit/voienna-ekonomika-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2-hist/status/voienna-ekonomika.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • 5 Outline Compliance Errors

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/voienna-ekonomika-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2-hist/voienna-ekonomika.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

