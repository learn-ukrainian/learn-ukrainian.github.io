        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `mountains-trail`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: mountains-trail
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  mountains-trail
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 4656/4000 (raw: 5028) | pedagogy: 12 violations | richness: 92% < 95% min (cultural)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
    [LLM_FINGERPRINT_REPETITION] Repetitive LLM rhetorical patterns (8 total): 'не просто X, а Y' x5, 'не лише X, а й Y' x3 — robotic prose
       → FIX: Vary sentence structures. Replace formulaic 'не просто X, а Y' with diverse rhetorical devices


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 50/100)
     → Revision recommended (severity 50/100)
     → 13 violations (severe - consider revision)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/audit/mountains-trail-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/status/mountains-trail.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/mountains-trail-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/mountains-trail.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

