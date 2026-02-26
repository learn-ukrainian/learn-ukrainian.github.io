        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `synonymy-thinking-verbs`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: synonymy-thinking-verbs
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  synonymy-thinking-verbs
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 5379/4000 (raw: 5878) | pedagogy: 8 violations | richness: 81% < 95% min (vocabulary)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
    [EUPHONY] Line 161: «з членами» — з перед з/с/ш/ч; має бути «із членами»
       → FIX: Replace «з» with «із» (before sibilant)


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 50/100)
     → Revision recommended (severity 50/100)
     → 13 violations (severe - consider revision)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/audit/synonymy-thinking-verbs-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/status/synonymy-thinking-verbs.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/synonymy-thinking-verbs-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/synonymy-thinking-verbs.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

## Section-Level Fix (IMPORTANT)

This is a large module (5878 words). To avoid token truncation,
fix ONLY the following section(s): "Аналіз помилок: Рахувати чи вважати?"

**Output format:** Output ONLY the fixed section(s) between delimiters:

```
===SECTION_FIX_START===
## {section title}
{fixed section content}
===SECTION_FIX_END===
```

Do NOT output the entire file. Only output the section(s) listed above.

