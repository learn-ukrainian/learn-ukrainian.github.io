        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `scythians-sarmatians`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: scythians-sarmatians
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  scythians-sarmatians
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 5046/5000 (raw: 5268) | pedagogy: 2 violations
  missing orchestration artifacts:
    no Phase 2 artifacts (section files or prompt)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Add a essay-response activity to meet advanced richness standards.
    [MISSING_ADVANCED_ACTIVITY] B2+ module (focus: history) missing advanced activity type: comparative-study
       → FIX: Add a comparative-study activity to meet advanced richness standards.


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 2 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/audit/scythians-sarmatians-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/status/scythians-sarmatians.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/scythians-sarmatians-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/scythians-sarmatians.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

