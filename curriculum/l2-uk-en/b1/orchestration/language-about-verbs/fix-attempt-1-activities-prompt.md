# Phase Fix-Activities: Activities-Only Fixes

> **You are Gemini, executing a targeted activities fix.**
> **Your ONLY task: Fix the ACTIVITIES file based on audit errors.**
> **Do NOT output content — only fixed activities.**

## Your Input

Read these files from disk:

**Current activities** (the file you are fixing):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/activities/language-about-verbs.yaml
```

**Plan file** (source of truth for vocabulary scope):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/b1/language-about-verbs.yaml
```

**Meta file** (activity count targets, pedagogy):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/meta/language-about-verbs.yaml
```

**Activity schema** (CRITICAL — defines allowed fields per activity type):
```
/Users/krisztiankoos/projects/learn-ukrainian/schemas/activities-b1.schema.json
```

**Lesson content** (reference for activity alignment):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/language-about-verbs.md
```

## Audit Errors to Fix

The following audit errors were found. Fix ALL of them:

```
1. [COMPLEXITY] group-sort 'Терміни дієслова: Категоризація' has 6 groups (target: 2-5)
   FIX: Merge groups to get 5 or fewer. Suggestion: merge "Спосіб дієслова" and "Стан дієслова" into one group called "Спосіб та стан дієслова".

2. [COMPLEXITY_WORD_COUNT] unjumble 'Розшифруйте терміни' — ALL 7 items are too short (2-4 words, target: 6-16 words).
   FIX: Replace ALL unjumble items with FULL SENTENCES about verb terminology (6-16 words each). These should be real grammatical statements, not just term labels.
   Example of correct format:
   - words: ["в", "мові", "українській", "розрізняють", "два", "види", "дієслів"]
     answer: "в українській мові розрізняють два види дієслів"

3. [COMPLEXITY] select 'Оберіть дієслівні терміни' has 4 items (minimum: 6 per schema).
   FIX: Add 2 more question items to the select activity. Ideas:
   - "Оберіть усі терміни, що описують «Форми дієслова»." (options: складна форма, синтетична форма, наказова форма, дієвідмінювання, парадигма vs інші)
   - "Оберіть усі терміни, що стосуються «Стану дієслова»." (options: активний стан, пасивний стан vs інші)

4. [COMPLEXITY] mark-the-words 'Знайдіть дієслівні терміни' has 4 answers (minimum: 6).
   FIX: Rewrite with a LONGER text sentence that contains at least 6 verb-related terms to mark. The sentence must be natural Ukrainian.

5. [COMPLEXITY] mark-the-words 'Виділіть форми дієслова' has 5 answers (minimum: 6).
   FIX: Expand the text sentence so it contains at least 6 verb form terms. Add one more recognizable term (e.g., інфінітив, дієвідмінювання, or наказова форма).

6. [COMPLEXITY] mark-the-words 'Ідентифікуйте концепції дії' has 5 answers (minimum: 6).
   FIX: Expand the text sentence to include at least 6 action concept terms. The current text has: дію, процес, результат, тривалість, повторення. Add one more (e.g., заперечення or очікувана дія).

7. [YAML_SCHEMA_VIOLATION] Schema error on select activity — the schema requires `items` array to have minItems: 6.
   This is the SAME issue as #3 above — adding 2 more items fixes both the density and schema errors.
```

## Activity Rules

1. **BARE LIST at root** — no `activities:` wrapper
2. **Schema compliance** — only use fields defined in the schema. Read the schema file carefully.
3. **`mark-the-words` format**: Use `text` (no asterisks) + `answers` array
4. **`select` requires 6+ items** (question objects) per the schema
5. **`unjumble` items must be 6-16 words** — full sentences, not short term labels
6. **`group-sort` must have 2-5 groups** maximum
7. **Preserve all other activities exactly as-is** — only change the 4 flagged activities (group-sort, unjumble, select, 3x mark-the-words)

### CRITICAL: Activity Type Constraints for b1

**ALLOWED types:** quiz, match-up, fill-in, group-sort, unjumble, true-false, cloze, error-correction, mark-the-words, select, translate, essay-response, critical-analysis, comparative-study, authorial-intent, reading

**FORBIDDEN types:** anagram

## Output Format

**CRITICAL: Output fixed files between delimiter lines.**

**Activity fixes:**

===ACTIVITIES_START===
(complete fixed activities YAML — bare list at root, NO `activities:` wrapper)
===ACTIVITIES_END===

**After the activities, report what you changed:**

===CHANGES_START===
## Applied Fixes

1. Activity "{title}": {what changed} — {which audit error this addresses}

## Fixes NOT Applied (explain why)

- {If any fix was unclear or contradictory, explain here}
===CHANGES_END===

===FRICTION_START===
**Phase**: Phase 4: Fix Activities
**Step**: Fixing activity density, word counts, schema compliance
**Friction Type**: {YAML_SCHEMA_VIOLATION | TOKEN_LIMIT_TRUNCATION | TOOL_REDUNDANCY | NONE}
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if friction is a script/design issue, or "N/A"}
===FRICTION_END===

## Boundaries

- Do NOT output content — this phase is ACTIVITIES ONLY
- Do NOT add fields not in the schema
- Do NOT wrap in `activities:` dictionary key
- Do NOT change activities that are NOT flagged (match-up, fill-in, error-correction, quiz, true-false, cloze, translate, fill-in #2 are all fine — leave them exactly as-is)
- If you cannot fix an error, explain why in "Fixes NOT Applied"
