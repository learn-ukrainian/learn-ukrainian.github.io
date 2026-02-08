# Phase Fix: Apply Review Fix Plan

> **You are Gemini, executing the Fix phase of an orchestrated rebuild.**
> **Your ONLY task: Apply every fix from the review's Fix Plan. Output complete fixed files.**
> **Do NOT add, remove, or change anything beyond what the Fix Plan specifies.**

## Your Input

Read these files from disk:

**Review with Fix Plan** (your instructions — follow EVERY fix listed):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/orchestration/the-genitive-i-absence/phase-5-re-review.md
```

**Current content** (the file you are fixing):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/16-the-genitive-i-absence.md
```

**Current activities** (fix if review mentions activity issues):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/16-the-genitive-i-absence.yaml
```

**Current vocabulary** (fix if review mentions vocabulary issues):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/16-the-genitive-i-absence.yaml
```

**Plan file** (source of truth for scope — check if fixes align):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/16-the-genitive-i-absence.yaml
```

**Research notes** (reference for factual accuracy):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/the-genitive-i-absence-research.md
```

## Your Task

1. Read the review file completely — focus on:
   - **"Critical Issues Found"** section
   - **"Fix Plan to Reach 9/10"** section
   - **"Ukrainian Language Issues"** table
2. For each fix listed, apply it to the correct file
3. Output the COMPLETE fixed files (not diffs, not partial)

### Rules

1. **Apply EVERY fix** from the Fix Plan — do not skip any, even if they require adding substantial content
2. **Scope your changes** — change/add ONLY what the Fix Plan specifies, leave unflagged sections untouched
3. **Adding content IS expected** — if the Fix Plan says "add a table", "add examples", "add vocabulary to the section", you MUST add it. This is not "rewriting" — it's applying the fix.
4. **Preserve structure** — keep the same H2/H3 headings, same activity order, same vocabulary order
5. **Preserve voice** — do not change the writing style of unflagged content
6. **Activities YAML must be bare list at root** — no `activities:` wrapper
7. **Vocabulary YAML keeps its header** — preserve `module:`, `level:`, `version:`, `items:` structure
8. **If a fix is ambiguous**, choose the option that matches the plan file
9. **Never output "no changes needed"** — if the Fix Plan lists fixes, there ARE changes to make. Read more carefully.

### What NOT to Do

- Do NOT rewrite the entire file — only change what the Fix Plan says
- Do NOT add engagement boxes unless the Fix Plan says to
- Do NOT change IPA unless the Fix Plan flags specific IPA errors
- Do NOT remove content unless the Fix Plan says to remove it
- Do NOT request skills, delegate to Claude, or skip fixes
- Do NOT add commentary — just output the fixed files

## Output Format

**CRITICAL: You MUST output fixed files between delimiter lines. Delimiters must appear on their own line, NOT inside code blocks.**

Output ONLY the files that need changes. If a file has no fixes, skip it entirely.

For EACH file that needs changes, output the COMPLETE file between these EXACT delimiter lines:

**Content fixes** — put the delimiter on its own line, then the complete markdown, then the end delimiter:

===CONTENT_START===
(complete fixed content markdown — ALL of it, not just changed parts)
===CONTENT_END===

**Activity fixes** — same pattern:

===ACTIVITIES_START===
(complete fixed activities YAML — bare list at root, NO `activities:` wrapper)
===ACTIVITIES_END===

**Vocabulary fixes** — same pattern:

===VOCABULARY_START===
(complete fixed vocabulary YAML — with module/level/version/items header)
===VOCABULARY_END===

**After all files, report what you changed:**

===CHANGES_START===
## Applied Fixes

1. [File: content] Line {N}: {what changed} — {which review issue this addresses}
2. [File: activities] Activity "{title}", Item {N}: {what changed} — {which review issue}
3. [File: vocabulary] Added/removed: {lemma} — {which review issue}

## Fixes NOT Applied (explain why)

- {If any fix was unclear or contradictory, explain here}

## Files Changed: {list: content, activities, vocabulary — or subset}
## Files Unchanged: {list of files that needed no fixes}
===CHANGES_END===

## Boundaries

- Do NOT output files that have no changes — only output what you fixed
- Do NOT fabricate fixes — only apply what the review specified
- Do NOT change the module's pedagogical approach or structure
- Do NOT add vocabulary not in the plan unless the Fix Plan explicitly says to
- If you cannot apply a fix, explain why in the "Fixes NOT Applied" section
- If you encounter `NEEDS_HELP:` situations, report them clearly
