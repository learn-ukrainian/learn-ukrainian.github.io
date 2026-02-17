        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `checkpoint-navigation`:

        ## Audit Output (last 60 lines)

        ```
        File "/Users/krisztiankoos/projects/learn-ukrainian/scripts/audit_module.sh", line 29
    --skip-activities)
                     ^
SyntaxError: unmatched ')'

Prose-relevant failures:
  meta: Missing '## Summary'
  lesson: 2895/1073 (raw: 3223) | engagement: 1/2 | pedagogy: 3 violations
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/checkpoint-navigation.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

## Section-Level Fix (IMPORTANT)

This is a large module (3223 words). To avoid token truncation,
fix ONLY the following section(s): "Огляд та навичка 1: Знахідний відмінок"

**Output format:** Output ONLY the fixed section(s) between delimiters:

```
===SECTION_FIX_START===
## {section title}
{fixed section content}
===SECTION_FIX_END===
```

Do NOT output the entire file. Only output the section(s) listed above.

