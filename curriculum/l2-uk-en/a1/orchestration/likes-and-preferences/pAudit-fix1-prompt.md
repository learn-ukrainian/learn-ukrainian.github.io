        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `likes-and-preferences`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: likes-and-preferences
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  likes-and-preferences
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 4115/2000 (raw: 4513) | pedagogy: 2 violations | immersion: 14.9% LOW (target 25-40% (M19))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
    [GRAMMAR] Participle used before B1: 'улюблений'
       → FIX: Participles not allowed until B1. Use relative clauses or simple sentences.


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 25/100)
     → 2 violations (minor)
     → Immersion 10% off target


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/likes-and-preferences-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/likes-and-preferences.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/likes-and-preferences-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/likes-and-preferences.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

