        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `presentations-visuals`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: presentations-visuals
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  presentations-visuals
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 3906/4000 (raw: 4190) (94 short) | pedagogy: 10 violations | richness: 70% < 95% min (grammar) - REWRITE needed

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Break into shorter sentences. First 5 words: 'Ваше головне завдання полягає тому...'
    [COMPLEXITY] Sentence too long for B1: 42 words (max 30)
       → FIX: Break into shorter sentences. First 5 words: 'Найбільшим граматичним здобутком для нас...'


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 30/100)
     → 10 violations (significant)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/audit/presentations-visuals-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/status/presentations-visuals.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/presentations-visuals-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/presentations-visuals.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

