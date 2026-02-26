        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `presentations-visuals`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: presentations-visuals
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  presentations-visuals
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 3921/4000 (raw: 4205) (79 short) | richness: 70% < 95% min (grammar) - REWRITE needed

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  Pedagogy     ✅ Level-appropriate
  Content_heavy ⏳ Deferred (content-only audit)
  Grammar      ℹ️ N/A (covered by naturalness)
  Naturalness  ℹ️ PENDING — awaiting review
  Activity_quality ⏳ Deferred (content-only audit)
  Research     ✅ Content aligned with research
  Immersion    🇺🇦 98.5% (target 85-100% (B1.7-8 Ukraine))
  Richness     ❌ 70% < 95% min (grammar) - REWRITE needed

  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/audit/presentations-visuals-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/status/presentations-visuals.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/presentations-visuals-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/presentations-visuals.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

