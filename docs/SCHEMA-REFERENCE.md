# YAML Schema Reference

This document provides a comprehensive reference for the YAML schemas used in the curriculum.

## Activity Schema (`activities/*.yaml`)

All interactive activities are defined in YAML sidecar files.

### Common Fields
All activities support these optional fields:
- `instruction`: Custom text displayed above the activity.
- `explanation`: Feedback shown after the learner completes the activity.

### Activity Types

#### 1. quiz
Multiple-choice questions.
- `items`: List of questions.
    - `question`: The question text.
    - `options`: List of `{text, correct}` objects.

#### 2. match-up
Matching pairs.
- `pairs`: List of `{left, right}` objects.

#### 3. fill-in
Sentence with a blank.
- `items`: List of items.
    - `sentence`: Text with `___` placeholder.
    - `answer`: The correct word.
    - `options`: Distractors.

#### 4. true-false
True or false statements.
- `items`: List of items.
    - `statement`: The text to evaluate.
    - `correct`: Boolean.

#### 5. group-sort
Sorting items into categories.
- `groups`: List of categories.
    - `name`: Category name.
    - `items`: List of strings belonging to this category.

#### 6. unjumble
Reordering words into a sentence.
- `items`: List of items.
    - `jumbled`: Slash-separated words (e.g., `word1 / word2`).
    - `answer`: The correct sentence.

#### 7. cloze
Fill-in-the-blank passage.
- `passage`: Text with `{correct|wrong1|wrong2}` blocks.

#### 8. error-correction
Fixing a mistake in a sentence.
- `items`: List of items.
    - `sentence`: Text with an error.
    - `error`: The wrong word/phrase.
    - `answer`: The correction.
    - `error_type`: (Optional) `word`, `phrase`, `register`, or `construction`.

#### 9. mark-the-words
Clicking on specific words.
- `text`: The full passage.
- `answers`: List of words to be selected.

#### 10. anagram (A1 only)
Scrambled letters to form a word.
- `items`: List of items.
    - `scrambled`: Space-separated letters (e.g., `л і т е р а`).
    - `answer`: The correct word.

#### 11. select
Multi-select questions with multiple correct answers.
- `items`: List of items.
    - `question`: The question text.
    - `options`: List of `{text, correct}` objects.

#### 12. translate
Translation exercise from English to Ukrainian.
- `items`: List of items.
    - `source`: The English sentence.
    - `options`: List of `{text, correct}` objects (Ukrainian translations).

#### 13. reading (Seminar)
Primary source text or external link.
- `id`: Unique identifier (required for pairing).
- `text` or `resource`: Content.
- `tasks`: Comprehension questions.

#### 11. essay-response (Seminar)
Open-ended writing task.
- `source_reading`: ID of the linked `reading` activity.
- `prompt`: The writing prompt.
- `min_words`: Minimum word count requirement.

---

## Meta Schema (`meta/*.yaml`)

Defines pedagogical metadata and build specifications.

### Core Fields
- `title`: Lesson title.
- `subtitle`: Descriptive subtitle.
- `focus`: `grammar`, `vocab`, `culture`, `history`, `biography`, etc.
- `pedagogy`: Instructional design model (e.g., `PPP`, `TTT`, `Active`).
- `word_target`: Minimum core word count.
- `content_outline`: List of sections with `{title, words}`.
- `activity_hints`: Recommended activity types.
- `vocabulary_hints`: Target vocabulary focus.

---

## Plan Schema (`plans/*.yaml`)

The immutable source of truth for module requirements.

### Core Fields
- `level`: CEFR level (A1-C2).
- `module`: Numeric ID.
- `objectives`: List of learning goals.
- `grammar`: List of grammatical points.
- `learning_outcomes`: Expected student achievements.
- `sources`: (Optional) Research links or citations.

---

## Validation Rules

### Required Fields
- Activities: `type` and `items`/`pairs`/`groups` as appropriate.
- Meta: `title`, `slug`, `focus`, `word_target`.
- Plan: `level`, `module`, `objectives`.

### Minimums (CEFR Adjusted)
| Level | Min Activities | Min Items/Act |
|-------|----------------|---------------|
| A1    | 8              | 10            |
| A2    | 10             | 12            |
| B1    | 8              | 12            |
| B2    | 10             | 12            |
| C1    | 12             | 15            |
