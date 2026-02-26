        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `business-basics`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: business-basics
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  business-basics
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 4417/4000 (raw: 4733) | pedagogy: 6 violations | richness: 78% < 95% min (vocabulary)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Break into shorter sentences. First 5 words: 'Це саме ті реальні гроші...'
    [LLM_FINGERPRINT_REPETITION] Repetitive LLM rhetorical patterns (8 total): 'не просто X, а Y' x4, 'не лише X, а й Y' x4 — robotic prose
       → FIX: Vary sentence structures. Replace formulaic 'не просто X, а Y' with diverse rhetorical devices


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 30/100)
     → 7 violations (significant)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/audit/business-basics-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/status/business-basics.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/business-basics-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/business-basics.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

