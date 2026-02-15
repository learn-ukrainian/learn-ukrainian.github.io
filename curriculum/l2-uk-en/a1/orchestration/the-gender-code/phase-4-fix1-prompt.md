        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `the-gender-code`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  HETMAN VERIFY: the-gender-code
============================================================

[1/4] Running full audit...
[2/4] Checking sidecar files...
[3/4] Reading status JSON...
[4/4] Checking overall status...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  the-gender-code
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  overall status is 'fail' (must be 'pass')
  failing gates:
    lesson: 3265/934 (raw: 3449) | pedagogy: 5 violations
    activities: 10/8 | density: 2 < 12

  Hetman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
    [YAML_SCHEMA_VIOLATION] Schema error in the-gender-code.yaml: Schema validation error at key '9': {'type': 'match-up', 'title': 'Match Pronouns to Nouns', 'items': [['мій', 'дім'], ['моя', 'мама'], ['моє', 'місто'], ['мій', 'брат'], ['моя', 'сестра'], ['моє', 'вікно'], ['мій', 'тато'], ['моя', 'книга'], ['моє', 'серце'], ['мій', 'стіл'], ['моя', 'земля'], ['моє', 'море']]} is not valid under any of the given schemas
       → FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 25/100)
     → 6 violations (moderate)
     → Activity density below minimum


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/the-gender-code-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/the-gender-code.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-gender-code-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-gender-code.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-gender-code.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-gender-code.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

