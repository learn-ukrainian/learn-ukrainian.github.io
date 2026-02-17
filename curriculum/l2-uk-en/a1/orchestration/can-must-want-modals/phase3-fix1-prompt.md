        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `can-must-want-modals`:

        ## Audit Output (last 60 lines)

        ```
        File "/Users/krisztiankoos/projects/learn-ukrainian/scripts/audit_module.sh", line 29
    --skip-activities)
                     ^
SyntaxError: unmatched ')'

Prose-relevant failures:
  meta: Missing '## Summary'
  lesson: 1965/1049 (raw: 2357) | pedagogy: 11 violations | immersion: 34.9% LOW (target 35-55% (M24))
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/can-must-want-modals.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

