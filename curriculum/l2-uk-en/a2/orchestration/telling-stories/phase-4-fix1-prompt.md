# Phase 4: Fix Audit Failures

> **You are Gemini (Yellow Team), fixing a module that failed audit.**
> **Your Goal:** Make the module PASS `scripts/audit_module.sh`.

## Context
Module: `curriculum/l2-uk-en/a2/telling-stories.md`
Activities: `curriculum/l2-uk-en/a2/activities/telling-stories.yaml`

## Audit Errors
The module failed with these critical errors:

1. **Structure**: Missing '## Summary' section at the end of the markdown file.
2. **Immersion**: 34.2% (Target: 60-75%). The content has too much English.
   - **Fix**: Rewrite English explanations in simple Ukrainian.
   - **Fix**: Ensure all "Engagement" boxes (tips, culture) use Ukrainian headers and mixed content.
3. **Activity Density**:
   - 'Сортування: Типи конекторів': 11 items (Need 12).
   - 'Заповніть пропуски: Анекдот': 10 items (Need 12).
4. **Pedagogy / Complexity**:
   - Sentences too long (>15 words) in the markdown.
   - Unjumble items too short (<7 words) in the activities YAML.
5. **Lint**: AI Contamination 'Correction:' found.

## Your Instructions

1. **Read the files** (`read_file`) to understand the current state.
2. **Fix Content (`.md`)**:
   - Append a `## Summary` / `## Підсумок` section.
   - increasing immersion by translating English parts to Ukrainian (A2 level).
   - Remove "Correction:" artifacts.
   - Shorten long sentences.
3. **Fix Activities (`.yaml`)**:
   - Add 1 item to 'Сортування'.
   - Add 2 items to 'Заповніть пропуски'.
   - Rewrite short unjumble items to be 7-10 words long.
4. **Verify**: Run `scripts/audit_module.sh curriculum/l2-uk-en/a2/telling-stories.md` to check if it passes.

## Constraints
- Do NOT reduce the total word count below 1000.
- Do NOT break the YAML structure.
- Keep the `content_outline` structure (don't remove sections).

## Execute
Start by reading the files, then apply fixes.
