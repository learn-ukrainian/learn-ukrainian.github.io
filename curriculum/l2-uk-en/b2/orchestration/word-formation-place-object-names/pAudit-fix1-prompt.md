        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `word-formation-place-object-names`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: word-formation-place-object-names
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  word-formation-place-object-names
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  1 Outline Compliance Errors
  failing gates:
    lesson: 3793/4000 (raw: 4305) | engagement: 0/6 | richness: 72% < 95% min (grammar)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 2 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/audit/word-formation-place-object-names-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/status/word-formation-place-object-names.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • 1 Outline Compliance Errors

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/word-formation-place-object-names-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/word-formation-place-object-names.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

