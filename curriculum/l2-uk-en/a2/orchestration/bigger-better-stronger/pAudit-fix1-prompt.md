        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `bigger-better-stronger`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: bigger-better-stronger
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  bigger-better-stronger
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 3454/3000 (raw: 3740) | pedagogy: 2 violations | immersion: 34.9% LOW (target 50-60% (A2.1))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
    [LLM_PERSONA_LEAK] LLM persona leak: 'I am your' — content should not role-play as a teacher/character
       → FIX: Rewrite in neutral educational voice. Remove first-person teacher persona.


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 35/100)
     → 4 violations (moderate)
     → Immersion 15% off target


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/bigger-better-stronger-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/bigger-better-stronger.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/bigger-better-stronger-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/bigger-better-stronger.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

