# Fix Request: A1 Module 4 (this-is-i-am)

The module `this-is-i-am` failed the audit with 102 violations. You must fix these errors.

## Critical Errors to Fix:

1.  **Structure**: The module is missing the `## Summary` section at the end. Add it.
2.  **Immersion**: Immersion is 87.9%, which is TOO HIGH for A1 M04. The target is 10-25%.
    *   **FIX**: Dramatically increase English scaffolding. Explain grammar in English. Use English phonetic/alphabet explanations.
    *   **FIX**: Keep Ukrainian content short and simple.
3.  **Grammar Restrictions**:
    *   **Dative and Instrumental cases are FORBIDDEN** in A1. You used words like `мові`, `базові`, `нам`, `вам`, `з другом`, `з віком`, etc.
    *   **FIX**: Rewrite all sentences to avoid these cases. Use only Nominative, Genitive (basics), or Accusative (if covered, but stick to basics).
    *   **Subordinate clauses are FORBIDDEN** in A1. No `яке`, `що`, `коли`, `якщо`, `тому що`, `бо`, `щоб`, `поки`.
    *   **FIX**: Break all complex sentences into simple SVO sentences.
4.  **Sentence Complexity**: Sentences are too long (max 10 words).
    *   **FIX**: Shorten ALL sentences to 10 words or fewer.
5.  **Activity Density**:
    *   `Основи граматики`: Add 2 more items (total 8).
    *   `Словниковий запас`: Add 2 more items (total 8).
    *   `Оберіть правильне слово`: Add 2 more items (total 8).
    *   `Культурний контекст: Ти чи Ви?`: Add 2 more items (total 8).
    *   `Хто чи Що?`: Add 2 more items (total 8).
6.  **Activity Types & Content**:
    *   `unjumble` is forbidden for M01-M10. Replace it with `anagram` or `quiz`.
    *   Remove all `hint` fields from anagrams.
    *   Fix `unjumble` (or the replacement) so items are not too short for schema (but avoid `unjumble` altogether).
7.  **Robotic Structure**: Avoid starting multiple sentences with the same phrase like "Ви говорите...".
8.  **Metalanguage**: Add grammar terms like `дієслово`, `займенник`, `рід`, `середній` to the vocabulary or use English equivalents in the text.

## Files to Modify:
- `curriculum/l2-uk-en/a1/this-is-i-am.md`
- `curriculum/l2-uk-en/a1/activities/this-is-i-am.yaml`
- `curriculum/l2-uk-en/a1/vocabulary/this-is-i-am.yaml`

## Instructions:
1.  Read the current files.
2.  Apply the fixes according to the audit report.
3.  Ensure the immersion is strictly within 10-25%.
4.  Ensure NO Dative/Instrumental cases and NO subordinate clauses.
5.  Ensure ALL sentences are <= 10 words.
6.  Ensure all activities have at least 8 items (except match-up/group-sort if they are already okay).
7.  Add the `## Summary` section.

Produce the fixed files using `write_file`.
