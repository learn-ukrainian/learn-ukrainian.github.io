# Activity YAML Schema Quick Reference

> **Purpose:** Eliminate schema validation iterations by providing exact field requirements per activity type.
> **Source:** `schemas/activities-base.schema.json`

## Critical Rules

1. **Root structure:** Bare list at root (NOT wrapped in `activities:`)
2. **No extra fields:** `additionalProperties: false` means unknown fields cause validation failure
3. **Field names are exact:** `correct` not `answer`, `criteria` not `criterion`

---

## Common Activity Types

### quiz
```yaml
- type: quiz
  title: "..." # required
  instruction: "..." # optional
  items: # required, array
    - question: "..." # required
      options: # required, exactly 4 items
        - text: "..." # required
          correct: true # required, boolean (exactly one true)
        - text: "..."
          correct: false
        - text: "..."
          correct: false
        - text: "..."
          correct: false
      explanation: "..." # optional
```

### select (multiple correct)
```yaml
- type: select
  title: "..." # required
  instruction: "..." # optional
  items: # required
    - question: "..." # required
      options: # required, 4-6 items
        - text: "..." # required
          correct: true # required, boolean (multiple can be true)
        - text: "..."
          correct: true
        - text: "..."
          correct: false
        - text: "..."
          correct: false
      min_correct: 2 # optional, minimum 2
      explanation: "..." # optional
```

### true-false
```yaml
- type: true-false
  title: "..." # required
  instruction: "..." # optional
  items: # required
    - statement: "..." # required (NOT 'question')
      correct: true # required, boolean (NOT 'answer')
      explanation: "..." # optional
```

### fill-in
```yaml
- type: fill-in
  title: "..." # required
  instruction: "..." # optional
  items: # required
    - sentence: "Він ___ додому." # required, use ___ for blank
      answer: "йде" # required
      options: ["йде", "іде", "ходить", "пішов"] # required, exactly 4
      explanation: "..." # optional
```

### cloze
```yaml
- type: cloze
  title: "..." # required
  instruction: "..." # optional
  passage: "Text with {correct|opt1|opt2|opt3} inline format" # required
  # OR numbered format:
  passage: "Text with {1} and {2} blanks"
  blanks: # optional, use with numbered format
    - id: 1 # required, integer >= 1
      answer: "..." # required
      options: ["...", "...", "..."] # required, 3-5 items
```

### match-up
```yaml
- type: match-up
  title: "..." # required
  instruction: "..." # optional
  pairs: # required
    - left: "..." # required
      right: "..." # required
```

### group-sort
```yaml
- type: group-sort
  title: "..." # required
  instruction: "..." # optional
  groups: # required, minimum 2 groups
    - name: "Category A" # required
      items: ["item1", "item2"] # required, min 1 item
    - name: "Category B"
      items: ["item3", "item4"]
```

### unjumble
```yaml
- type: unjumble
  title: "..." # required
  instruction: "..." # optional
  items: # required
    - words: ["Він", "йде", "додому"] # required, min 3 words
      answer: "Він йде додому." # required
```

### error-correction
```yaml
- type: error-correction
  title: "..." # required
  instruction: "..." # optional
  items: # required
    - sentence: "Він ходить до школа." # required
      error: "школа" # required - the wrong word/phrase
      answer: "школи" # required - the correct word/phrase
      error_type: "word" # optional: word|phrase|register|construction
      options: ["школи", "школу", "школою", "школі"] # required, exactly 4
      explanation: "Genitive case after до" # required
```

### mark-the-words
```yaml
- type: mark-the-words
  title: "..." # required
  instruction: "Позначте всі іменники" # required
  text: "Гарний день приніс радість у серце." # required (NO asterisks)
  answers: ["день", "радість", "серце"] # optional but recommended
```

### translate
```yaml
- type: translate
  title: "..." # required
  instruction: "..." # optional
  items: # required
    - source: "Hello" # required (usually English)
      options: # required, 3-4 items
        - text: "Привіт" # required
          correct: true # required
        - text: "Добрий день"
          correct: false
        - text: "До побачення"
          correct: false
      explanation: "..." # optional
```

### anagram (A1 only, M01-10)
```yaml
- type: anagram
  title: "..." # required
  instruction: "..." # optional
  items: # required
    - scrambled: "ИВТПІР" # required
      answer: "ПРИВІТ" # required
      hint: "greeting" # optional
```

---

## Advanced Activity Types (B2+)

### reading
**Format 1: Inline text**
```yaml
- type: reading
  id: "reading-module-topic" # optional but recommended (pattern: reading-*)
  title: "..." # required
  instruction: "..." # optional
  source: "Author, Year" # optional attribution
  text: "Primary source text in Ukrainian..." # required
  tasks: # required, array of strings
    - "Знайдіть у тексті приклади офіційної лексики."
    - "Визначте основну тезу автора."
```

**Format 2: External resource**
```yaml
- type: reading
  id: "reading-module-topic"
  title: "..." # required
  instruction: "..." # optional
  resource: # required
    url: "https://..." # required
    type: "article" # optional
    title: "Resource Title" # optional
  tasks: # required
    - "..."
```

### essay-response
```yaml
- type: essay-response
  id: "..." # optional
  source_reading: "reading-id" # optional, links to reading activity
  title: "..." # required
  instruction: "..." # optional
  prompt: "Напишіть есе на тему..." # required, min 10 chars
  min_words: 200 # optional, minimum 100
  model_answer: "Sample essay response..." # REQUIRED, min 50 chars
  rubric: # optional but recommended
    - criteria: "Мовна якість" # required (NOT 'criterion')
      description: "Граматика, лексика, стилістика" # required
      points: 40 # optional (NOT 'weight')
  peer_review_guidelines: "..." # optional
```

### critical-analysis
```yaml
- type: critical-analysis
  id: "..." # optional
  source_reading: "reading-id" # optional
  title: "..." # required
  instruction: "..." # optional
  target_text: "Text excerpt to analyze..." # REQUIRED
  questions: # REQUIRED, array of strings
    - "Як автор використовує метафори?"
    - "Яка основна теза тексту?"
  model_answers: # REQUIRED, array of strings (same length as questions)
    - "Автор використовує метафори для..."
    - "Основна теза полягає в тому, що..."
  focus_points: ["tone", "bias", "structure"] # optional
```

### comparative-study
```yaml
- type: comparative-study
  id: "..." # optional
  source_reading: "reading-id" # optional
  title: "..." # required
  instruction: "..." # optional
  items_to_compare: # REQUIRED, min 2 items
    - "Item A title or excerpt"
    - "Item B title or excerpt"
  criteria: # REQUIRED, array of comparison dimensions
    - "Тон і стиль"
    - "Історичний контекст"
    - "Авторська позиція"
  prompt: "Порівняйте ці тексти за критеріями." # optional
  model_answer: "Comparison analysis..." # REQUIRED
```

### authorial-intent
```yaml
- type: authorial-intent
  id: "..." # optional
  source_reading: "reading-id" # optional
  title: "..." # required
  instruction: "..." # optional
  text_excerpt: "..." # REQUIRED
  prompt: "..." # REQUIRED
  techniques_to_identify: ["metaphor", "irony"] # optional
  model_answer: "..." # REQUIRED
```

---

## Common Mistakes to Avoid

| Wrong | Correct | Activity Types |
|-------|---------|----------------|
| `answer: true` | `correct: true` | true-false |
| `criterion: "..."` | `criteria: "..."` | essay-response rubric |
| `weight: 40` | `points: 40` | essay-response rubric |
| `instructions:` | `instruction:` | all types |
| `comparison_axes:` | `criteria:` | comparative-study |
| `synthesis_prompt:` | `prompt:` | comparative-study |
| Missing `model_answer` | Add `model_answer:` | essay-response, comparative-study, authorial-intent |
| Missing `model_answers` | Add `model_answers:` | critical-analysis |
| Missing `target_text` | Add `target_text:` | critical-analysis |
| `text: "*word* text"` | `text: "word text"` + `answers: [word]` | mark-the-words |

---

## Validation Command

```bash
# Quick YAML syntax check
yq '.' curriculum/l2-uk-en/{level}/activities/{slug}.yaml > /dev/null

# Full schema validation (if jsonschema available)
.venv/bin/python -c "
import yaml, json
from jsonschema import validate
# ... validation code
"
```
