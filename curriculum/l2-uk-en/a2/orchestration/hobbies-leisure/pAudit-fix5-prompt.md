        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `hobbies-leisure`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: hobbies-leisure
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  hobbies-leisure
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 5648/3000 (raw: 6098) | pedagogy: 87 violations | immersion: 95.0% HIGH (target 75-90% (A2.3))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Replace «і» with «й» (between vowels)


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 60/100)
     → Revision recommended (severity 60/100)
     → 90 violations (severe - consider revision)
     → Immersion 5% off target (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/hobbies-leisure-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/hobbies-leisure.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/hobbies-leisure-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/hobbies-leisure.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

