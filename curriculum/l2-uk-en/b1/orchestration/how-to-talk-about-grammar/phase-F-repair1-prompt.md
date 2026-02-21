        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `how-to-talk-about-grammar`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  HETMAN VERIFY: how-to-talk-about-grammar
============================================================

[1/4] Running full audit...
[2/4] Checking sidecar files...
[3/4] Reading status JSON...
[4/4] Checking overall status...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  how-to-talk-about-grammar
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  overall status is 'fail' (must be 'pass')
  failing gates:
    lesson: 5288/4000 (raw: 5591) | pedagogy: 9 violations

  Hetman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Replace second «і»/«й» with «та» for conjunction variety
    [EUPHONY] Line 98: повторення і/й без «та» — «...переходить в **і**, а в інших в...»; використайте «та» для другого сполучника
       → FIX: Replace second «і»/«й» with «та» for conjunction variety


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 30/100)
     → 9 violations (significant)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/audit/how-to-talk-about-grammar-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/status/how-to-talk-about-grammar.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/how-to-talk-about-grammar-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/how-to-talk-about-grammar.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/activities/how-to-talk-about-grammar.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/vocabulary/how-to-talk-about-grammar.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

