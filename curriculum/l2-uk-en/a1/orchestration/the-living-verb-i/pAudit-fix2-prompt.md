        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `the-living-verb-i`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: the-living-verb-i
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  the-living-verb-i
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 2749/2000 (raw: 3087) | pedagogy: 1 violations

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.
    [EUPHONY] Line 121: повторення і/й без «та» — «...і «He works», і «He is working...»; використайте «та» для другого сполучника
       → FIX: Replace second «і»/«й» with «та» for conjunction variety


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 2 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/the-living-verb-i-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/the-living-verb-i.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-living-verb-i-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-living-verb-i.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

## Section-Level Fix (IMPORTANT)

This is a large module (3087 words). To avoid token truncation,
fix ONLY the following section(s): "Теорія: Магія закінчень -ати"

**Output format:** Output ONLY the fixed section(s) between delimiters:

```
===SECTION_FIX_START===
## {section title}
{fixed section content}
===SECTION_FIX_END===
```

Do NOT output the entire file. Only output the section(s) listed above.

