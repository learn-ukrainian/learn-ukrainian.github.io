        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `the-completed-past`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: the-completed-past
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  the-completed-past
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  Structure: Missing '## Vocabulary' header OR vocabulary sidecar
  failing gates:
    meta: Missing '## Vocabulary' header OR vocabulary sidecar | Lint: 3 Format Errors
    lesson: 2961/3000 (raw: 3130) (39 short) | pedagogy: 2 violations | immersion: 14.6% LOW (target 50-60% (A2.1))
    activities: 12/10 | density: 1 < 8

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       Наративна послідовність у музеї       732 /  600  ✅ (+132)
       Практика та усунення помилок          385 /  400  ✅ (-15)
       ────────────────────────────────────────────────────────────
       TOTAL                                2811 / 3000  ❌ (-189)
    ⏳ Content-only audit: activities/vocab gates DEFERRED
  Traceback (most recent call last):
    File "/Users/krisztiankoos/projects/learn-ukrainian/scripts/audit_module.py", line 160, in <module>
      success = audit_module(file_path, skip_activities=args.skip_activities,
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "/Users/krisztiankoos/projects/learn-ukrainian/scripts/audit/core.py", line 1674, in audit_module
      uk = item.get('lemma', '') # YAML schema uses 'lemma'
           ^^^^^^^^
  AttributeError: 'NoneType' object has no attribute 'get'

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-completed-past-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/the-completed-past.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

## Section-Level Fix (IMPORTANT)

This is a large module (4651 words). To avoid token truncation,
fix ONLY the following section(s): "Наративна послідовність у музеї", "Практика та усунення помилок"

**Output format:** Output ONLY the fixed section(s) between delimiters:

```
===SECTION_FIX_START===
## {section title}
{fixed section content}
===SECTION_FIX_END===
```

Do NOT output the entire file. Only output the section(s) listed above.

