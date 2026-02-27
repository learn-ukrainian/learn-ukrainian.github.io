        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `druha-svitova-pochatok`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: druha-svitova-pochatok
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  druha-svitova-pochatok
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 5226/5000 (raw: 5566) | engagement: 0/5 | richness: 74% < 95% min (history)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Use "Друга світова війна". The GPW framing erases Ukrainian suffering and reframes Russian aggression as defence.
    [IMPERIAL_TERMINOLOGY] Line 89: Suspicious imperial term "возз'єднання" — Soviet "reunification" myth for the 1654 Pereiaslav agreement. If citing/debunking, wrap in «guillemets» to suppress this warning.
       → FIX: Use "союз", "угода", "Переяславська угода". Ukraine was not 'reuniting' — it signed a military alliance.


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 2 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/audit/druha-svitova-pochatok-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/status/druha-svitova-pochatok.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/druha-svitova-pochatok-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/druha-svitova-pochatok.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

## Section-Level Fix (IMPORTANT)

This is a large module (5566 words). To avoid token truncation,
fix ONLY the following section(s): "Радянська окупація: Вторгнення та міфи"

**Output format:** Output ONLY the fixed section(s) between delimiters:

```
===SECTION_FIX_START===
## {section title}
{fixed section content}
===SECTION_FIX_END===
```

Do NOT output the entire file. Only output the section(s) listed above.

