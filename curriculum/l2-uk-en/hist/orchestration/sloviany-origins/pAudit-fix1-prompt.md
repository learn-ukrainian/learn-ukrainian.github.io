        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `sloviany-origins`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: sloviany-origins
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  sloviany-origins
────────────────────────────────────────────────────────────
  missing orchestration artifacts:
    no Phase 2 artifacts (section files or prompt)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  Pedagogy     ✅ Level-appropriate
  Content_heavy ⏳ Deferred (content-only audit)
  Grammar      ℹ️ N/A (covered by naturalness)
  Naturalness  ✅ 10/10 (High)
  Activity_quality ⏳ Deferred (content-only audit)
  Research     ✅ Content aligned with research
  Immersion    🇺🇦 99.5% (target 90-100% (history))
  Richness     ✅ 99% (history)

  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/audit/sloviany-origins-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/status/sloviany-origins.json

  ✅ AUDIT PASSED.

  ✅ AUDIT PASSED
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/sloviany-origins.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

