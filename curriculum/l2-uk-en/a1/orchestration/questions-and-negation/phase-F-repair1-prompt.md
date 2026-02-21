        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `questions-and-negation`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  HETMAN VERIFY: questions-and-negation
============================================================

[1/4] Running full audit...
[2/4] Checking sidecar files...
[3/4] Reading status JSON...
[4/4] Checking overall status...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  questions-and-negation
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  overall status is 'fail' (must be 'pass')
  failing gates:
    lesson: 2720/2000 (raw: 2885) | pedagogy: 1 violations

  Hetman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  📚 PEDAGOGICAL VIOLATIONS FOUND:
    [GRAMMAR] Instrumental case used at A1: 'з дієсловом'
       → FIX: Instrumental case not allowed until A2 (M36+). Restructure sentence.


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 1 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/questions-and-negation-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/questions-and-negation.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/questions-and-negation-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/questions-and-negation.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/questions-and-negation.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/questions-and-negation.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

