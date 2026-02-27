        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `holodomor-pamiat`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: holodomor-pamiat
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  holodomor-pamiat
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  Tone Error. Found 'The Ukraine'. Use 'Ukraine' (sovereign nation).
  failing gates:
    lesson: 5693/5000 (raw: 6092) | richness: 94% < 95% min (history)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 2 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/audit/holodomor-pamiat-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/status/holodomor-pamiat.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • Tone Error. Found 'The Ukraine'. Use 'Ukraine' (sovereign nation).

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/holodomor-pamiat-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/holodomor-pamiat.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

