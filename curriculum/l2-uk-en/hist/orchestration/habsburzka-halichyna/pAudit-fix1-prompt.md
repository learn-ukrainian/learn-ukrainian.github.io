        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `habsburzka-halichyna`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: habsburzka-halichyna
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  habsburzka-halichyna
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 5863/5000 (raw: 6458) | engagement: 0/5 | pedagogy: 1 violations | richness: 76% < 95% min (history)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Move historical text into a blockquote (> ) to mark it as a primary source quote.
    [LLM_FINGERPRINT_REPETITION] Repetitive LLM rhetorical patterns (12 total): 'не просто X, а Y' x10, 'не лише X, а й Y' x2 — robotic prose
       → FIX: Vary sentence structures. Replace formulaic 'не просто X, а Y' with diverse rhetorical devices


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 3 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/audit/habsburzka-halichyna-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/status/habsburzka-halichyna.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/habsburzka-halichyna-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/habsburzka-halichyna.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

