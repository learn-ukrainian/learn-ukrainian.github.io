Activate skill full-rebuild-core-a.

# Fix Request: A1 M05 - My World: Objects

The module failed the audit. You must apply the following fixes to the markdown, activities, and vocabulary files.

## Audit Errors to Fix

### 1. Structure (Markdown)
- **Missing '## Summary'**: Add a '## Summary' section at the end of the markdown file.
- **Robotic Structure**: 3 sentences start with 'it is...'. Vary sentence structure in the English parts.

### 2. Immersion (Markdown)
- **Immersion Too Low**: 8.5% (Target: 10-25%).
- **Fix**: Convert simple English explanations to Ukrainian. Add more Ukrainian examples or a small dialogue. Use Ukrainian for engagement box headers if appropriate (e.g., [!tip] -> [!tip] **Порада**).

### 3. Activities (YAML)
- **Forbidden Activity Type**: 'mark-the-words' is NOT allowed at A1. Replace activity 'Знайдіть вказівні слова' with a different type (e.g., match-up, quiz, or anagram).
- **Pedagogy (Unjumble)**: 'unjumble' is not appropriate for A1 M01-M10. Replace any 'unjumble' activities with 'anagram' or something simpler.
- **Density (Item Count)**:
  - 'Цей, ця, це чи ці?': Add 2 more items (current: 6, min: 8).
  - 'Той, та, те чи ті?': Add 2 more items (current: 6, min: 8).
  - 'Доповніть речення': Add 2 more items (current: 6, min: 8).
  - 'Розшифруйте слова': Add 2 more items (current: 6, min: 8).
  - The new activity replacing 'mark-the-words' MUST have at least 12 items.
- **Hints**: Remove all 'hint' fields from all activity items.
- **Schema Violation**: Ensure the YAML follows the schema. Specifically, the replaced activity must be valid.

## Files to Modify
- CONTENT: curriculum/l2-uk-en/a1/my-world-objects.md
- ACTIVITIES: curriculum/l2-uk-en/a1/activities/my-world-objects.yaml

Apply these fixes and output the corrected files using tool calls.
