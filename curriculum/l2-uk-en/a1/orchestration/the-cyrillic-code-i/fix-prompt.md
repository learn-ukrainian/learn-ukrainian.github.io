# Phase Fix: Apply Review Fix Plan

> **You are Gemini, executing the Fix phase of an orchestrated rebuild.**
> **Your ONLY task: Apply every fix from the review's Fix Plan. Output complete fixed files.**
> **Do NOT add, remove, or change anything beyond what the Fix Plan specifies.**

## Your Input

Read these files from disk:

**Review with Fix Plan** (your instructions — follow EVERY fix listed):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/orchestration/the-cyrillic-code-i/phase-5-response.md
```

**Current content** (the file you are fixing):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/01-the-cyrillic-code-i.md
```

**Current activities** (fix if review mentions activity issues):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/01-the-cyrillic-code-i.yaml
```

**Current vocabulary** (fix if review mentions vocabulary issues):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/01-the-cyrillic-code-i.yaml
```

**Plan file** (source of truth for scope — check if fixes align):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/01-the-cyrillic-code-i.yaml
```

**Research notes** (reference for factual accuracy):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/the-cyrillic-code-i-research.md
```

## Your Task

1. Read the review file completely — focus on:
   - **"Critical Issues Found"** section
   - **"Fix Plan to Reach 9/10"** section
   - **"Ukrainian Language Issues"** table
2. For each fix listed, apply it to the correct file
3. Output the COMPLETE fixed files (not diffs, not partial)

### Rules

1. **Apply EVERY fix** from the Fix Plan — do not skip any
2. **Minimal changes only** — do NOT rewrite sections that weren't flagged
3. **Preserve structure** — keep the same H2/H3 headings, same activity order, same vocabulary order
4. **Preserve voice** — do not change the writing style of unflagged content
5. **Activities YAML must be bare list at root** — no `activities:` wrapper
6. **Vocabulary YAML keeps its header** — preserve `module:`, `level:`, `version:`, `items:` structure
7. **If a fix is ambiguous**, choose the option that matches the plan file
8. **If the fix plan mentions adding content** (new examples, new vocabulary), add it naturally in the right location

### What NOT to Do

- Do NOT rewrite the entire file — only change what the Fix Plan says
- Do NOT add engagement boxes unless the Fix Plan says to
- Do NOT change IPA unless the Fix Plan flags specific IPA errors
- Do NOT remove content unless the Fix Plan says to remove it
- Do NOT request skills, delegate to Claude, or skip fixes
- Do NOT add commentary — just output the fixed files

## Output Format

Output ONLY the files that need changes. If a file has no fixes, skip it entirely.

For EACH file that needs changes, output the complete file between delimiters:

### If content needs fixes:

```
===CONTENT_START===
(complete fixed content markdown — ALL of it, not just changed parts)
===CONTENT_END===
```

### If activities need fixes:

```
===ACTIVITIES_START===
(complete fixed activities YAML — bare list at root, NO `activities:` wrapper)
===ACTIVITIES_END===
```

### If vocabulary needs fixes:

```
===VOCABULARY_START===
(complete fixed vocabulary YAML — with module/level/version/items header)
===VOCABULARY_END===
```

### After all files, report what you changed:

```
===CHANGES_START===
## Applied Fixes

1. [File: content] Line {N}: {what changed} — {which review issue this addresses}
2. [File: activities] Activity "{title}", Item {N}: {what changed} — {which review issue}
3. [File: vocabulary] Added/removed: {lemma} — {which review issue}
...

## Fixes NOT Applied (explain why)

- {If any fix was unclear or contradictory, explain here}

## Files Changed: {list: content, activities, vocabulary — or subset}
## Files Unchanged: {list of files that needed no fixes}
===CHANGES_END===
```

## Boundaries

- Do NOT output files that have no changes — only output what you fixed
- Do NOT fabricate fixes — only apply what the review specified
- Do NOT change the module's pedagogical approach or structure
- Do NOT add vocabulary not in the plan unless the Fix Plan explicitly says to
- If you cannot apply a fix, explain why in the "Fixes NOT Applied" section
- If you encounter `NEEDS_HELP:` situations, report them clearly
