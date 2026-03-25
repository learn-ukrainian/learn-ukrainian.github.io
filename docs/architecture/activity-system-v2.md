# Activity System V2 — Architecture

> Replaces inline DSL exercises with structured YAML. Separates prose from exercises.
> Designed with Gemini consultation (2026-03-25).

## Overview

Each module gets an `activities/{slug}.yaml` file with two sections:
- **inline**: exercises placed in the Урок tab at specific injection points
- **workbook**: extended exercises in the Зошит tab

Writer generates prose with injection markers. A separate ACTIVITIES pipeline step generates the YAML using MCP tools (VESUM, CEFR, style guide) for verification.

## YAML Schema

```yaml
version: "1.0"
module: things-have-gender
level: a1

inline:
  - id: quiz-genders              # matches <!-- INJECT_ACTIVITY: quiz-genders -->
    type: quiz
    instruction: "Оберіть правильний варіант"
    items:
      - question: "_____ стіл"
        options: ["мій", "моя", "моє"]
        correct: 0

workbook:
  - type: match-up
    instruction: "З'єднайте пари"
    pairs:
      - left: "стіл"
        right: "мій"

  - type: essay-response          # open-ended (seminar)
    prompt: "Порівняйте два описи..."
    min_words: 150
    model_answer: "..."
    evaluation_criteria:
      - "Аргументація з доказами"
```

## Activity Types

### Core (A1-C2)
| Type | Key Props | Usage |
|------|-----------|-------|
| quiz | question, options[], correct | Multiple choice |
| fill-in | sentence (with {answer} markers) | Blanks in sentences |
| match-up | pairs[{left, right}] | Pair matching |
| group-sort | groups[{label, items[]}] | Categorization |
| true-false | statement, correct (bool) | Statement evaluation |
| error-correction | sentence, error, correction | Find wrong word |
| anagram | letters[], answer, hint | Letter rearrangement |
| translate | source, target_lang | Type translation |
| unjumble | words[], correct_order[] | Word reordering |
| cloze | text (with {gaps}), options[] | Paragraph gap-fill |
| select | question, options[{text, correct}] | Dropdown selection |
| grammar-identify | word, task, options[] | Identify grammatical feature |
| observe | examples[], prompt | Pattern discovery |
| classify | categories[{label, items[]}] | Multi-category sort |
| mark-the-words | text, target_words[], criteria | Click matching words |
| highlight-morphemes | word, morphemes[{text, type}] | Word part identification |
| image-to-letter | items[{image, letter, options[]}] | Image to letter (A1.1) |
| letter-grid | letters[{upper, lower, name}] | Interactive alphabet |
| phrase-table | groups[{label, phrases[]}] | Grouped phrases |

### Seminar (HIST, BIO, LIT, ISTORIO, OES, RUTH)
| Type | Key Props | Usage |
|------|-----------|-------|
| critical-analysis | prompt, evaluation_criteria[] | Analyze with rubric |
| essay-response | prompt, min_words, model_answer, evaluation_criteria[] | Extended writing |
| source-evaluation | source_text, source_metadata, criteria[], guiding_questions[] | Evaluate reliability |
| reading-activity | passage, questions[] | Comprehension |
| comparative-study | items_to_compare[], criteria[], prompt | Compare across criteria |
| authorial-intent | excerpt, questions[], model_answer | Author's purpose |
| debate | debate_question, positions[], analysis_tasks[] | Evaluate positions |
| etymology-trace | stages[{period, form, notes}] | Word evolution |
| translation-critique | original, translations[{text, quality}], focus_points[] | Evaluate translations |
| transcription | original, answer, hints[] | Historical to modern |
| paleography-analysis | image_url, hotspots[{x,y,label}] | Manuscript analysis |
| dialect-comparison | text_a, text_b, label_a, label_b, features[] | Compare dialects |

## Injection Markers

Writer places markers in prose:
```markdown
## Три роди (Three Genders)

Content explaining gender rules...

<!-- INJECT_ACTIVITY: quiz-genders -->

More content about endings...

<!-- INJECT_ACTIVITY: fillin-possessives -->
```

Markers are HTML comments — invisible in rendered output. If an activity YAML has an `id` that doesn't match any marker, it goes to Зошит by default.

## Pipeline Flow

```
1. WRITE        → prose + injection markers (no exercise content)
2. ACTIVITIES   → separate LLM call generates activities/{slug}.yaml
                   - Input: plan activity_hints + prose + vocabulary
                   - Writer has MCP tools (VESUM, CEFR, style guide)
                   - Output: validated YAML
3. VALIDATE     → JSON Schema check + exercise verification (#1016)
4. ENRICH       → словник, videos, resources
5. PUBLISH      → reads YAML, injects inline at markers, builds Зошит tab
```

## Activity Generation Prompt

The activity generator receives:
- The plan's `activity_hints` (what exercises to create)
- The generated prose (what was actually taught)
- The plan's `vocabulary_hints` (required/recommended words)
- MCP tools for verification

It outputs YAML matching the schema. Every Ukrainian word in exercises must be:
1. Present in the prose OR plan vocabulary (grounding check)
2. VESUM-verified (exists in Ukrainian)
3. CEFR-appropriate (query_cefr_level)

## Design Decisions

1. **inline/workbook split** — maps directly to Урок/Зошит tabs (Gemini recommendation)
2. **Intermediate format, not React props** — decouples content from UI (Gemini recommendation)
3. **Injection markers, not H2 matching** — robust against title changes (Gemini recommendation)
4. **Separate LLM call** — different persona for exercises vs prose (Gemini recommendation)
5. **No backward compatibility** — only 1 legacy file, migrate it
6. **MCP tools for verification** — eliminates hallucination risk
