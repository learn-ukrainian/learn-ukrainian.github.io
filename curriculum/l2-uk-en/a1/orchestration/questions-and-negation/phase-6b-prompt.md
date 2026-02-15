# Fix Prompt 6b: Review Fixes

You are the Yellow Team builder.
Review Verdict: FAIL (8.2/10). Critical content gaps found.

## Instructions

### 1. Fix Content (`curriculum/l2-uk-en/a1/questions-and-negation.md`)
- **Add "Double Negation" Subsection**: In the "Теорія" section (after "Simple Negation" or "Iron Rule"), add an H3 subsection **"Ніколи не кажи ніколи" (Double Negation)**.
  - Explain that Ukrainian uses double negatives (unlike English).
  - Keywords: **ніколи** (never), **нічого** (nothing), **ніхто** (nobody).
  - Rule: They ALWAYS require **не** before the verb.
  - Examples: "Я **ніколи не** знаю." (I never know). "Він **нічого не** читає." (He reads nothing).
- **Expand "Question Words"**: In "Теорія", strictly ensure `чому` (why), `скільки` (how much), `як` (how), `куди` (where to) are introduced or listed with translations. The activities test them, so they MUST be in the text.

### 2. Fix Activities (`curriculum/l2-uk-en/a1/activities/questions-and-negation.yaml`)
- **Fix Future Tense**: In `Оберіть правильне слово` (fill-in), find the item `___ це буде?`.
  - Change the sentence to: `___ цей урок?` (When is this lesson?)
  - Ensure the answer remains `Коли`.

## Execution
- Read files.
- Use `write_file` to OVERWRITE files with fixes.
- Run `scripts/audit_module.sh` to verify.
