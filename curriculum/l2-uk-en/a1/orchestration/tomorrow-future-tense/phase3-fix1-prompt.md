        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `tomorrow-future-tense`:

        ## Audit Output (last 60 lines)

        ```
        File "/Users/krisztiankoos/projects/learn-ukrainian/scripts/audit_module.sh", line 29
    --skip-activities)
                     ^
SyntaxError: unmatched ')'

Prose-relevant failures:
  lesson: 1429/1082 (raw: 1706) | pedagogy: 7 violations
  naturalness: Not scored
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/tomorrow-future-tense.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

