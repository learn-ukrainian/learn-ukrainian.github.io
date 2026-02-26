        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `regions-south`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: regions-south
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  regions-south
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 5214/4000 (raw: 5516) | pedagogy: 10 violations

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
    [LLM_FINGERPRINT_REPETITION] Repetitive LLM rhetorical patterns (7 total): 'не просто X, а Y' x7 — robotic prose
       → FIX: Vary sentence structures. Replace formulaic 'не просто X, а Y' with diverse rhetorical devices


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 50/100)
     → Revision recommended (severity 50/100)
     → 12 violations (severe - consider revision)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/audit/regions-south-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/status/regions-south.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/regions-south-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/regions-south.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

