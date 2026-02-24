        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `adjective-suffixes-types`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: adjective-suffixes-types
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  adjective-suffixes-types
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 3198/3000 (raw: 3385) | pedagogy: 1 violations | immersion: 81.4% HIGH (target 60-75% (A2.2))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
    [GRAMMAR] Participle used before B1: 'Оброблений'
       → FIX: Participles not allowed until B1. Use relative clauses or simple sentences.


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 15/100)
     → 1 violations (minor)
     → Immersion 6% off target (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/adjective-suffixes-types-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/adjective-suffixes-types.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/adjective-suffixes-types-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/adjective-suffixes-types.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

