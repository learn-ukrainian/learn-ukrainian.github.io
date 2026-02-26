        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `mykhailo-chernihivskyi`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: mykhailo-chernihivskyi
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  mykhailo-chernihivskyi
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 6190/5000 (raw: 7123) | pedagogy: 2 violations

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Only Title and Main Sections (Activities/Summary/Vocabulary) should be H1. Change '# Підсумок — Віра вища за життя' to '## Підсумок — Віра вища за життя'
    [LLM_FINGERPRINT_REPETITION] Repetitive LLM rhetorical patterns (18 total): 'не просто X, а Y' x10, 'це не було/були/була' x2, 'не лише X, а й Y' x6 — robotic prose
       → FIX: Vary sentence structures. Replace formulaic 'не просто X, а Y' with diverse rhetorical devices


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 3 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-bio/audit/mykhailo-chernihivskyi-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-bio/status/mykhailo-chernihivskyi.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/mykhailo-chernihivskyi-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-bio/mykhailo-chernihivskyi.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

