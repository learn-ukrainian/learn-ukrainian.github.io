# YAML Schema Reference

This document provides a reference for the YAML schemas used in the curriculum.

---

## 1. Activity YAML Schema

Activity files are located in `curriculum/l2-uk-en/{level}/activities/{slug}.yaml`. They MUST be a bare list of activity objects at the root.

### Common Fields (All Activities)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | The activity type (e.g., `quiz`, `fill-in`). |
| `title` | string | Yes | The title of the activity. |
| `instruction`| string | No | Instructions for the learner. |
| `id` | string | No | Optional unique identifier. |

### Activity Types

#### `quiz` (Multiple Choice)
- `items`: Array of objects.
  - `question`: The question text.
  - `options`: Array of 4 objects with `text` (string) and `correct` (boolean).
  - `explanation`: Optional feedback for the correct answer.

#### `fill-in` (Gap Fill)
- `items`: Array of objects.
  - `sentence`: Text with `___` marking the blank.
  - `answer`: The correct word.
  - `options`: Array of 4 strings.
  - `explanation`: Optional feedback.

#### `true-false`
- `items`: Array of objects.
  - `statement`: The text to validate.
  - `correct`: Boolean.
  - `explanation`: Optional feedback.

#### `cloze` (Passage with multiple blanks)
- `passage`: Text with `{correct|opt1|opt2|opt3}` format OR numbered `{1}`, `{2}`.
- `blanks`: (Optional) Array of objects if using numbered markers.
  - `id`: Integer matching marker.
  - `answer`: Correct word.
  - `options`: Array of 3-5 strings.

#### `match-up`
- `pairs`: Array of objects with `left` and `right` strings.

#### `group-sort`
- `groups`: Array of objects.
  - `name`: Category name.
  - `items`: Array of strings.

#### `unjumble`
- `items`: Array of objects.
  - `words`: Array of strings to reorder.
  - `answer`: The complete correct sentence.

#### `error-correction`
- `items`: Array of objects.
  - `sentence`: The incorrect sentence.
  - `error`: The incorrect word/phrase.
  - `answer`: The correct word/phrase.
  - `options`: Array of 4 strings.
  - `explanation`: Detailed correction reason.

#### `mark-the-words`
- `text`: The passage where words are marked.
- `answers`: Array of words the student should click.
- `instruction`: specific (e.g., "Mark all nouns").

#### `translate`
- `items`: Array of objects.
  - `source`: Text to translate (usually English).
  - `options`: Array of objects with `text` and `correct`.

#### `essay-response` (B1+)
- `prompt`: Writing task.
- `min_words`: Minimum word count.
- `model_answer`: Exemplar response.
- `rubric`: Criteria for evaluation.

#### `reading`
- `text`: Inline primary source text (Format 1).
- `resource`: External link object (Format 2).
- `tasks`: Array of comprehension tasks/questions.

#### `critical-analysis`
- `target_text`: The text to analyze.
- `questions`: Specific analytical questions.
- `model_answers`: Expected depth of analysis.

#### `comparative-study`
- `items_to_compare`: List of texts/concepts.
- `criteria`: Dimensions of comparison.
- `model_answer`: Sample comparison.

#### `authorial-intent`
- `text_excerpt`: Target passage.
- `techniques_to_identify`: List of literary devices.
- `model_answer`: Explanation of intent.

#### `etymology-trace` (OES/RUTH)
- `items`: List of words with their modern equivalents and evolution.

#### `transcription` (OES/RUTH)
- `original`: Archaic text.
- `answer`: Modern transcription.

#### `grammar-identify` (OES/RUTH)
- `items`: List of forms to identify (e.g., dual number).

#### `phonology-lab` (OES/RUTH)
- `input`: Original form.
- `law`: Linguistic rule applied.
- `output`: Resulting form.

#### `grammar-lab` (OES/RUTH)
- `focus`: Specific grammar point.
- `items`: Detailed morphological analysis.

#### `parallel-text` (OES/RUTH)
- `versions`: Comparison of text across language stages.

#### `paleography-analysis` (OES/RUTH)
- `image_url`: Link to manuscript.
- `hotspots`: X/Y coordinates with feature labels.

#### `historical-writing` (OES/RUTH)
- `prompt`: Stylistic composition task.
- `constraints`: Required period features.

#### `register-identify` (OES/RUTH)
- `items`: Text excerpts to classify by register (Vernacular, Chancery, etc.).

#### `loanword-trace` (OES/RUTH)
- `items`: Borrowed words with source language and meaning.

#### `comparative-style` (OES/RUTH)
- `items_to_compare`: Registers or periods.
- `criteria`: Linguistic features to compare.

---

## 2. Meta YAML Schema

Meta files are located in `curriculum/l2-uk-en/{level}/meta/{slug}.yaml`.

| Field | Type | Description |
|-------|------|-------------|
| `module` | integer | Module number. |
| `id` | string | Unique slug. |
| `title` | string | Module title. |
| `pedagogy` | string | Pedagogical framework (PPP, TTT, Reading, etc.). |
| `duration` | integer | Estimated time in minutes. |
| `word_target` | integer | Target word count for the lesson. |
| `focus` | string | grammar, vocab, history, biography, etc. |
| `objectives` | array | Learning goals. |
| `content_outline`| array | Ordered sections with word allocations. |
| `vocabulary_hints`| array | List of target lemmas. |
| `activity_hints` | array | List of activity types and counts. |

---

## 3. Plan YAML Schema

Plan files are located in `curriculum/l2-uk-en/plans/{level}/{slug}.yaml`. They serve as the immutable source of truth for the curriculum.

| Field | Type | Description |
|-------|------|-------------|
| `level` | string | CEFR level (a1, b2, etc.). |
| `module` | integer | Sequence number. |
| `slug` | string | Permanent identifier. |
| `title` | string | Working title. |
| `grammar` | array | Grammar points covered. |
| `word_target` | integer | Final word count requirement. |
| `vocabulary` | array | List of words/phrases to introduce. |
| `objectives` | array | Expected learning outcomes. |

---

## 4. Validation Rules

- **Required Fields**: Enforced by JSON Schema validation during audit.
- **Bare List**: Activities MUST NOT be wrapped in an `activities:` key.
- **Ukrainian Quotes**: Use `«` and `»` for text within YAML to avoid issues with reserved characters like `*`.
- **Instruction**: Should be in Ukrainian for B1+ modules.
