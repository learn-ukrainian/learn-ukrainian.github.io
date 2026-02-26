        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `idioms-nature`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: idioms-nature
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  idioms-nature
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  4 Outline Compliance Errors
  failing gates:
    lesson: 3114/4000 (raw: 3354) | engagement: 3/6 | pedagogy: 1 violations | richness: 75% < 95% min (phraseology)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 3 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/audit/idioms-nature-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/status/idioms-nature.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • 4 Outline Compliance Errors

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/idioms-nature-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/idioms-nature.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

