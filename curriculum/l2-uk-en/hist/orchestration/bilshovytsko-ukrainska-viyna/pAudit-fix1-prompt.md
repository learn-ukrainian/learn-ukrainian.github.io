        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `bilshovytsko-ukrainska-viyna`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: bilshovytsko-ukrainska-viyna
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  bilshovytsko-ukrainska-viyna
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 8066/5000 (raw: 8489) | pedagogy: 2 violations

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Replace «і» with «й» (between vowels)
    [LLM_FINGERPRINT_REPETITION] Repetitive LLM rhetorical patterns (6 total): 'не просто X, а Y' x3, 'не лише X, а й Y' x3 — robotic prose
       → FIX: Vary sentence structures. Replace formulaic 'не просто X, а Y' with diverse rhetorical devices


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 15/100)
     → 4 violations (moderate)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/audit/bilshovytsko-ukrainska-viyna-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/status/bilshovytsko-ukrainska-viyna.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/bilshovytsko-ukrainska-viyna-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/bilshovytsko-ukrainska-viyna.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

