        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `the-genitive-i-absence`:

        ## Audit Output (last 60 lines)

        ```
        File "/Users/krisztiankoos/projects/learn-ukrainian/scripts/audit_module.sh", line 29
    --skip-activities)
                     ^
SyntaxError: unmatched ')'

Prose-relevant failures:
  meta: Missing '## Vocabulary' header OR vocabulary sidecar | Lint: 1 Format Errors
  lesson: 3219/1038 (raw: 3490) | engagement: 2/3 | pedagogy: 12 violations | immersion: 16.7% LOW (target 25-40% (M16))
  naturalness: Not scored
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-genitive-i-absence.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

## Section-Level Fix (IMPORTANT)

This is a large module (3498 words). To avoid token truncation,
fix ONLY the following section(s): "Warm-up"

**Output format:** Output ONLY the fixed section(s) between delimiters:

```
===SECTION_FIX_START===
## {section title}
{fixed section content}
===SECTION_FIX_END===
```

Do NOT output the entire file. Only output the section(s) listed above.

