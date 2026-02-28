        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `leisure-and-hobbies`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: leisure-and-hobbies
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  leisure-and-hobbies
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 3725/2000 (raw: 3909) | engagement: 0/3 | pedagogy: 3 violations | immersion: 23.2% LOW (target 35-55% (M51))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
    [GLOSSARY_LIST_IN_PROSE] Glossary-style list (3 items) in narrative prose starting: '**стадіо́н** — a stadium. This is a masculine noun.' — vocab tables belong in vocabulary YAML
       → FIX: Move vocabulary definitions to vocabulary/{slug}.yaml or rewrite as natural prose with words introduced in context


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 35/100)
     → 5 violations (moderate)
     → Immersion 12% off target


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/leisure-and-hobbies-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/leisure-and-hobbies.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/leisure-and-hobbies-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/leisure-and-hobbies.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

