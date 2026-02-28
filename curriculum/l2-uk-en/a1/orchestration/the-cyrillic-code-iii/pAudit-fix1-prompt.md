        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `the-cyrillic-code-iii`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: the-cyrillic-code-iii
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  the-cyrillic-code-iii
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 3244/2000 (raw: 3349) | pedagogy: 1 violations | immersion: 6.6% LOW (target 10-25% (M03))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Vary sentence structure.
    [SECTION_BALANCE_BLOATED] Section 'Нові літери (New Letters О–Х)' has 1537 words (48% of total). Bloated sections: 'Нові літери (New Letters О–Х)' (48%)
       → FIX: Consider splitting the large section or expanding smaller sections to improve balance.


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 15/100)
     → 5 violations (moderate)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/the-cyrillic-code-iii-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/the-cyrillic-code-iii.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-cyrillic-code-iii-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-cyrillic-code-iii.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

## Section-Level Fix (IMPORTANT)

This is a large module (3349 words). To avoid token truncation,
fix ONLY the following section(s): "Нові літери (New Letters О–Х)"

**Output format:** Output ONLY the fixed section(s) between delimiters:

```
===SECTION_FIX_START===
## {section title}
{fixed section content}
===SECTION_FIX_END===
```

Do NOT output the entire file. Only output the section(s) listed above.

