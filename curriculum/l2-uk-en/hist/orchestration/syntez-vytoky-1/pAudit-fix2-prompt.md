        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `syntez-vytoky-1`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: syntez-vytoky-1
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  syntez-vytoky-1
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 4971/5000 (raw: 5275) (29 short) | pedagogy: 1 violations

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Replace «в» with «у» (before в or ф)
    [EUPHONY] Line 143: «Це і є» — і між голосними; має бути «й є»
       → FIX: Replace «і» with «й» (between vowels)


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 3 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/audit/syntez-vytoky-1-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/status/syntez-vytoky-1.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/syntez-vytoky-1-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/syntez-vytoky-1.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

## Section-Level Fix (IMPORTANT)

This is a large module (5275 words). To avoid token truncation,
fix ONLY the following section(s): "Підсумкове есе"

**Output format:** Output ONLY the fixed section(s) between delimiters:

```
===SECTION_FIX_START===
## {section title}
{fixed section content}
===SECTION_FIX_END===
```

Do NOT output the entire file. Only output the section(s) listed above.

