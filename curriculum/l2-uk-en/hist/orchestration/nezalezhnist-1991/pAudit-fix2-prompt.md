        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `nezalezhnist-1991`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: nezalezhnist-1991
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  nezalezhnist-1991
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  5 Outline Compliance Errors
  failing gates:
    lesson: 4309/5000 (raw: 4533) | richness: 92% < 95% min (history)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  Naturalness  ℹ️ PENDING — awaiting review
  Activity_quality ⏳ Deferred (content-only audit)
  Research     ⚠️ Refresh recommended: Research has 5+ sources but content cites 0
  Immersion    🇺🇦 99.3% (target 90-100% (history))
  Richness     ❌ 92% < 95% min (history)

  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/audit/nezalezhnist-1991-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/status/nezalezhnist-1991.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • 5 Outline Compliance Errors

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/nezalezhnist-1991-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/nezalezhnist-1991.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

