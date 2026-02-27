        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `kozatstvo-vytoky`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: kozatstvo-vytoky
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  kozatstvo-vytoky
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 6636/5000 (raw: 7327) | pedagogy: 2 violations

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Vary sentence structures. Replace formulaic 'не просто X, а Y' with diverse rhetorical devices
    [STRUCTURAL_MONOTONY] 36 of 36 section openers share >70% lexical overlap. Sections: ## Вступ: Дике поле як колиска свободи; ### Географічний простір Дикого Поля; ### Великий Кордон як цивілізаційний фен... Opener pattern: "**Визначення:**..."
       → FIX: Diversify section openings. Each section should start with a unique approach: questions, examples, cultural hooks, direct instruction, comparisons — not the same template.


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 3 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/audit/kozatstvo-vytoky-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/status/kozatstvo-vytoky.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/kozatstvo-vytoky-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/kozatstvo-vytoky.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

## Section-Level Fix (IMPORTANT)

This is a large module (7327 words). To avoid token truncation,
fix ONLY the following section(s): "Вступ: Дике поле як колиска свободи"

**Output format:** Output ONLY the fixed section(s) between delimiters:

```
===SECTION_FIX_START===
## {section title}
{fixed section content}
===SECTION_FIX_END===
```

Do NOT output the entire file. Only output the section(s) listed above.

