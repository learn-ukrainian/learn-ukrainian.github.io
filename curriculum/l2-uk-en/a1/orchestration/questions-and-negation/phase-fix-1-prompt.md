# Fix Prompt for Questions & Negation

You are the Yellow Team builder. You need to fix audit failures for Module A1-07.

## Audit Errors

1. **Structure**: Missing '## Summary' section in content.
2. **Immersion**: 8.8% (Target 15-35%). Content is too English-heavy.
3. **Activities**:
   - `unjumble` type is BANNED for M01-M10. Change `Складіть запитання` and `Заперечні речення` to `quiz` (Choose the correct word order).
   - `hint` fields in anagrams are BANNED. Remove them.
   - Low density:
     - `Основи запитань` (quiz): 6 items -> Expand to 8.
     - `Питання чи твердження?` (group-sort): 10 items -> Expand to 12.
     - `Заперечення` (fill-in): 6 items -> Expand to 8.
     - `Питання та відповіді` (match-up): 6 items -> Expand to 8.
     - `Розшифруйте слова` (anagram): 6 items -> Expand to 8.
     - `Оберіть правильне слово` (fill-in): 6 items -> Expand to 8.
     - `Культура запитань` (quiz): 6 items -> Expand to 8.

## Instructions

### 1. Fix Content (`curriculum/l2-uk-en/a1/questions-and-negation.md`)
- **Rewrite the ENTIRE file** to increase immersion.
  - Convert simple English explanations to Ukrainian where possible (e.g., "This is a cat" -> "Це кіт").
  - Add more Ukrainian examples.
  - Use Ukrainian headers for subsections if appropriate (but keep H2 as in outline).
  - Ensure the "Immersion Rule" is met: "Explanatory prose primarily in English... but Examples increasingly in Ukrainian". To hit 15%, you need significant Ukrainian examples and mini-dialogues.
- **Add `## Summary` section** at the end.
  - Recap: Чи, Intonation, Не, Question words.
  - 100-150 words.
  - Bilingual format (Ukrainian summary with English gloss).

### 2. Fix Activities (`curriculum/l2-uk-en/a1/activities/questions-and-negation.yaml`)
- **Rewrite the ENTIRE file**.
- Change `unjumble` to `quiz` (Multiple choice: "Which sentence is correct?").
- Remove all `hint` fields.
- Add items to meet minimums (8 or 12).
- Ensure strictly valid YAML.

## Execution
- Read the current files first to understand context.
- Use `write_file` to OVERWRITE both files with the fixed versions.
- Do NOT use `replace` (too fragile for full rewrites).
- Run `scripts/audit_module.sh curriculum/l2-uk-en/a1/questions-and-negation.md` after writing to verify fixes.
