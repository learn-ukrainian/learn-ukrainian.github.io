        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `checkpoint-register-synthesis`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: checkpoint-register-synthesis
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  checkpoint-register-synthesis
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  Checkpoint Format Errors
  failing gates:
    lesson: 4343/4000 (raw: 4840) | engagement: 0/4 | pedagogy: 3 violations | richness: 79% < 85% min (checkpoint)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 15/100)
     → 5 violations (moderate)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/audit/checkpoint-register-synthesis-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/status/checkpoint-register-synthesis.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • Checkpoint Format Errors

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/checkpoint-register-synthesis-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/checkpoint-register-synthesis.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

