# Phase 4: Audit Fixes (Attempt 1)

> **You are Gemini (Yellow Team), fixing a module that failed audit.**
> **Your Goal:** Fix ALL reported errors in one pass.

## Audit Failures

### 1. Structure Mismatch (Critical)
The metadata expects Ukrainian headers, but the markdown has English headers.
**Task:** Rename the H2 headers in `curriculum/l2-uk-en/a1/the-accusative-i-things.md` to match the metadata exactly:
- `## Warm-up` -> `## Розминка: Що ми бачимо?`
- `## Presentation` -> `## Граматика: Знахідний відмінок для предметів`
- `## Practice` -> `## Практика: Змінюємо закінчення`
- `## Production` -> `## Говоримо: Список покупок`
- `## Cultural Insight` -> `## Культура: На українському ринку`

### 2. Missing Summary
**Task:** Add a `## Summary` section at the end of `curriculum/l2-uk-en/a1/the-accusative-i-things.md`.
Content: A brief recap of the module (Accusative case for things, gender changes, key verbs).
Format: 100% English explanation + Ukrainian examples.

### 3. Immersion Too Low (9.6% < 25%)
**Task:** Rewrite parts of the content in `curriculum/l2-uk-en/a1/the-accusative-i-things.md` to increase Ukrainian usage.
- Translate simple instructions and setup sentences into Ukrainian.
- Ensure all examples are in Ukrainian.
- Use Ukrainian for callout text where appropriate.
- **Target:** 30% Ukrainian words.

### 4. Activity Fixes
File: `curriculum/l2-uk-en/a1/activities/the-accusative-i-things.yaml`
**Errors:**
- `[LEVEL_RESTRICTION] Activity 'anagram' should be phased out after A1 M10` -> Change type to `unjumble`.
- `[COMPLEXITY] quiz 'Перевірка правил' has 6 items (minimum: 8)` -> Add 2 items.
- `[COMPLEXITY] true-false 'Правда чи ні?' has 6 items (minimum: 8)` -> Add 2 items.
- `[COMPLEXITY] fill-in 'В магазині' has 6 items (minimum: 8)` -> Add 2 items.
- `[HINT_IN_ACTIVITY]` -> Remove all `hint` fields from items.

## Execution
You have WRITE ACCESS.
1. Read the files `curriculum/l2-uk-en/a1/the-accusative-i-things.md` and `curriculum/l2-uk-en/a1/activities/the-accusative-i-things.yaml`.
2. Apply the fixes using `replace` or `write_file`.
3. Verify your changes.
