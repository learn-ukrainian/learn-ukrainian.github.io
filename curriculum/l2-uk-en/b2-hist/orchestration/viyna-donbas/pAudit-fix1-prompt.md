        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `viyna-donbas`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: viyna-donbas
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  viyna-donbas
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 12892/5000 (raw: 13243) | immersion: 78.9% LOW (target 90-100% (history))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
    [STATE_STANDARD_LOW_IMMERSION] Module 131 has 78.9% immersion (target: 90.0%+)
       → FIX: Add more Ukrainian content to reach 90.0%+ immersion


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 25/100)
     → 3 violations (minor)
     → Immersion 11% off target


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2-hist/audit/viyna-donbas-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2-hist/status/viyna-donbas.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/viyna-donbas-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2-hist/viyna-donbas.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

