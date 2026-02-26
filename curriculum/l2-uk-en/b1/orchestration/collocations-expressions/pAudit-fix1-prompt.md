        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `collocations-expressions`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: collocations-expressions
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  collocations-expressions
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 4018/4000 (raw: 4359) | engagement: 0/5 | pedagogy: 1 violations | richness: 68% < 95% min (vocabulary) - REWRITE needed

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Replace Russicisms with standard Ukrainian equivalents. These are Russian calques that have standard Ukrainian forms. See Phase B prompt 'Russianisms Pre-Output Scan' table.
    [LLM_FINGERPRINT_REPETITION] Repetitive LLM rhetorical patterns (5 total): 'не просто X, а Y' x2, 'не лише X, а й Y' x3 — robotic prose
       → FIX: Vary sentence structures. Replace formulaic 'не просто X, а Y' with diverse rhetorical devices


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 3 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/audit/collocations-expressions-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/status/collocations-expressions.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/collocations-expressions-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/collocations-expressions.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

