# Phase Fix-Content: Content-Only Fixes

> **You are Gemini, executing a targeted content fix.**
> **Your ONLY task: Fix the CONTENT file based on the review's Fix Plan.**
> **Do NOT output activities or vocabulary — only the fixed content.**

## Your Input

Read these files from disk:

**Review with Fix Plan** (your instructions — follow EVERY fix listed):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-bio/review/knyahynia-olha-review.md
```

**Current content** (the file you are fixing):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-bio/knyahynia-olha.md
```

**Plan file** (source of truth for scope — check if fixes align):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/c1-bio/knyahynia-olha.yaml
```

**Research notes** (reference for factual accuracy):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-bio/research/knyahynia-olha-research.md
```

## Your Task

1. Read the review file completely — focus on:
   - **"Critical Issues Found"** section
   - **"Fix Plan to Reach 9/10"** section
   - **"Ukrainian Language Issues"** table
2. Apply ONLY content-related fixes (ignore activity/vocabulary fixes)
3. Output the COMPLETE fixed content file

### Rules

1. **Apply EVERY content fix** from the Fix Plan — do not skip any
2. **Scope your changes** — change/add ONLY what the Fix Plan specifies for content
3. **Adding content IS expected** — if the Fix Plan says "add a table", "add examples", "expand section", you MUST do it
4. **Preserve structure** — keep the same H2/H3 headings
5. **Preserve voice** — do not change the writing style of unflagged content
6. **If a fix is ambiguous**, choose the option that matches the plan file
7. **Never output "no changes needed"** — if the Fix Plan lists content fixes, there ARE changes to make

### What NOT to Do

- Do NOT output activities or vocabulary — this phase is CONTENT ONLY
- Do NOT rewrite the entire file — only change what the Fix Plan says
- Do NOT add engagement boxes unless the Fix Plan says to
- Do NOT request skills, delegate to Claude, or skip fixes
- Do NOT add commentary — just output the fixed content

### Quality Verification (after applying fixes)

After applying all fixes from the Fix Plan, verify the result does not INTRODUCE these problems:

1. ☐ **Consistency**: If you changed how one item in a category is presented, update ALL items to match
2. ☐ **Parallel structure**: If you restructured one section, matching sections must follow the same pattern
3. ☐ **Example variety**: Fixes must not create 5+ consecutive `_Приклад:_` lines — vary the format
4. ☐ **Callout spread**: New callouts should not bunch with existing ones — spread evenly across sections
5. ☐ **English contamination**: Fixes must not introduce English text into immersion >= 85% content
6. ☐ **Table narrative wrapping**: If you added a table, include 2+ sentences of context before and after it

If applying fixes INTRODUCES any of these problems, fix them too before outputting.

## Output Format

**CRITICAL: Output the COMPLETE fixed content between these delimiter lines.**

===CONTENT_START===
(complete fixed content markdown — ALL of it, not just changed parts)
===CONTENT_END===

**After the content, report what you changed:**

===CHANGES_START===
## Applied Fixes

1. Line {N}: {what changed} — {which review issue this addresses}
2. Section "{name}": {what changed} — {which review issue}

## Fixes NOT Applied (explain why)

- {If any content fix was unclear or contradictory, explain here}
===CHANGES_END===

## Boundaries

- Do NOT output activities or vocabulary sections
- Do NOT fabricate fixes — only apply what the review specified
- Do NOT change the module's pedagogical approach or structure
- If you cannot apply a fix, explain why in the "Fixes NOT Applied" section
