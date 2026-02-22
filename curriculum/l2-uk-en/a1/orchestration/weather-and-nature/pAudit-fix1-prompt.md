        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `weather-and-nature`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: weather-and-nature
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  weather-and-nature
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 2965/2000 (raw: 3248) | pedagogy: 1 violations

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  📚 PEDAGOGICAL VIOLATIONS FOUND:
    [STRUCTURAL_MONOTONY] 6 of 30 section openers share >70% lexical overlap. Sections: ### Читання: Прогулянка під дощем (Readi; ## Презентація 3: Запитання про погоду; ## Презентація 5: Прогноз та планування... Opener pattern: "**Українською:**..."
       → FIX: Diversify section openings. Each section should start with a unique approach: questions, examples, cultural hooks, direct instruction, comparisons — not the same template.


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 1 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/weather-and-nature-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/weather-and-nature.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/weather-and-nature-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/weather-and-nature.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

## Section-Level Fix (IMPORTANT)

This is a large module (3248 words). To avoid token truncation,
fix ONLY the following section(s): "Презентація 3: Запитання про погоду", "Презентація 5: Прогноз та планування"

**Output format:** Output ONLY the fixed section(s) between delimiters:

```
===SECTION_FIX_START===
## {section title}
{fixed section content}
===SECTION_FIX_END===
```

Do NOT output the entire file. Only output the section(s) listed above.

