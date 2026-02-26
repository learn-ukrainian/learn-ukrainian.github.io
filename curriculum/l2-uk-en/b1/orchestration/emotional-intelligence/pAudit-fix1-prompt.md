        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `emotional-intelligence`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: emotional-intelligence
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  emotional-intelligence
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    meta: Valid Structure | Lint: 1 Format Errors
    lesson: 4372/4000 (raw: 4675) | pedagogy: 2 violations | richness: 75% < 95% min (vocabulary)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Replace «у» with «в» (before vowel)
    [LLM_FINGERPRINT_REPETITION] Repetitive LLM rhetorical patterns (7 total): 'не просто X, а Y' x4, 'не лише X, а й Y' x3 — robotic prose
       → FIX: Vary sentence structures. Replace formulaic 'не просто X, а Y' with diverse rhetorical devices


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 17/100)
     → 4 violations (moderate)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/audit/emotional-intelligence-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/status/emotional-intelligence.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/emotional-intelligence-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/emotional-intelligence.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

