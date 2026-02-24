        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `nature-and-weather`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: nature-and-weather
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  nature-and-weather
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 3836/3000 (raw: 4319) | engagement: 0/4 | pedagogy: 3 violations | immersion: 77.7% HIGH (target 60-75% (A2.3))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section
    [SECTION_BALANCE_BLOATED] Section 'Граматика: Погода та стани' has 1458 words (45% of total). Bloated sections: 'Граматика: Погода та стани' (45%)
       → FIX: Consider splitting the large section or expanding smaller sections to improve balance.


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 15/100)
     → 6 violations (moderate)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/nature-and-weather-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/nature-and-weather.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/nature-and-weather-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/nature-and-weather.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

## Section-Level Fix (IMPORTANT)

This is a large module (4319 words). To avoid token truncation,
fix ONLY the following section(s): "Граматика: Погода та стани"

**Output format:** Output ONLY the fixed section(s) between delimiters:

```
===SECTION_FIX_START===
## {section title}
{fixed section content}
===SECTION_FIX_END===
```

Do NOT output the entire file. Only output the section(s) listed above.

