        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `this-is-i-am`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: this-is-i-am
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  this-is-i-am
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 2507/2000 (raw: 2770) | pedagogy: 1 violations

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  📚 PEDAGOGICAL VIOLATIONS FOUND:
    [VOCAB_NOT_IN_CONTENT] Only 9/21 (43%) vocabulary words appear in content+activities. Missing: вона, вони, воно, він, ні, так, там, тут, хто, це (+2 more)
       → FIX: Vocabulary words MUST appear in the module content or activities. Either use these words in the prose/examples, add activities that practice them, or remove them from the vocabulary YAML if they don't belong in this module.


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 1 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/this-is-i-am-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/this-is-i-am.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/this-is-i-am-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/this-is-i-am.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

