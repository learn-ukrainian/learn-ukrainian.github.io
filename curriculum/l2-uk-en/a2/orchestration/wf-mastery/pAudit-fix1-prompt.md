        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `wf-mastery`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: wf-mastery
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  wf-mastery
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    meta: Valid Structure | Lint: 1 Format Errors
    lesson: 3211/3000 (raw: 3413) | pedagogy: 3 violations | immersion: 50.8% LOW (target 60-75% (A2.3))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
    [COMPLEXITY] Sentence too long for A2: 16 words (max 15)
       → FIX: Break into shorter sentences. First 5 words: 'Ця математика не потребує калькулятора...'


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 17/100)
     → 3 violations (minor)
     → Immersion 9% off target (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/wf-mastery-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/wf-mastery.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/wf-mastery-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/wf-mastery.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

