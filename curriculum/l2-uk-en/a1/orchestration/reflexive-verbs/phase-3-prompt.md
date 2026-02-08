# Phase 3: Activities & Vocabulary Generation

> **You are Gemini, executing Phase 3 of an orchestrated rebuild.**
> **Your ONLY task: Generate activities YAML and vocabulary YAML.**

## Your Input

Read these files from disk:

**Lesson content** (generate activities that test/reinforce this content):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/09-reflexive-verbs.md
```

**Plan file** (vocabulary_hints — vocabulary list to follow):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/09-reflexive-verbs.yaml
```

**Meta file** (word_target, pedagogy):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/meta/09-reflexive-verbs.yaml
```

**Activity schema** (CRITICAL — defines allowed fields per activity type):
```
/Users/krisztiankoos/projects/learn-ukrainian/schemas/activities-a1.schema.json
```

**Example vocabulary file** (follow this format):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/08-the-living-verb-ii.yaml
```

## Your Task

Generate two YAML blocks: activities and vocabulary.

### Activities YAML Rules

1. **BARE LIST at root** — no `activities:` wrapper, no `module:` or `level:` headers
2. **Schema compliance** — only use fields defined in the schema. `additionalProperties: false` means unlisted fields cause audit failure.
3. **A1 activity types allowed**: quiz, match-up, fill-in, group-sort, true-false, anagram. NOT allowed: error-correction, cloze, mark-the-words, select, translate.
4. **Activity count**: 8+ activities (per A1 quick-ref)
5. **Items per activity**: 6+ minimum (except anagram: 6+, unjumble: 4+)
6. **Type variety**: Use at least 4 different types. Required mix: fill-in (2+), match-up (2+), quiz (1+), true-false (1+), group-sort (1+), anagram (2+ for M01-10).
7. **fill-in items**: Must have `sentence`, `answer`, `options` (array of 4 strings). The blank in the sentence is marked with `___`.
8. **quiz items**: Must have `question` and `options` (array of 4 objects, each with `text` and `correct` boolean). Exactly ONE option has `correct: true`.
9. **match-up**: Must have `pairs` (array of objects with `left` and `right`). Min 6 pairs.
10. **group-sort**: Must have `groups` (array of objects with `name` and `items`). Total items across groups >= 10.
11. **true-false**: Must have `items` (array of objects with `statement` and `correct` boolean). Min 6 items.
12. **anagram**: Must have `items` (array of objects with `scrambled` and `answer`, optional `hint`). Min 6 items.

### Vocabulary YAML Rules

1. **Has `items:` wrapper** — format: `items:` then list of entries (see example file)
2. **Also has module/level/version headers** at top
3. **Follow plan's vocabulary_hints** — include all 8 required items, optionally include 4 recommended
4. **Each entry needs**: `lemma`, `ipa` (with correct stress), `translation`, `pos` (verb, noun, etc.)
5. **Count target**: 12+ items (8 required + recommended)

### Key Schema Details

**fill-in item format:**
```yaml
- sentence: "Я ___ (вмиватися) щоранку."
  answer: "вмиваюсь"
  options: ["вмиваюсь", "вмиваєшся", "вмивається", "вмиваються"]
```

**quiz item format:**
```yaml
- question: "Which form is correct: Я ___ся or Я ___сь after a vowel?"
  options:
    - text: "-сь (after vowels)"
      correct: true
    - text: "-ся (after vowels)"
      correct: false
    - text: "Both are correct"
      correct: false
    - text: "Neither is correct"
      correct: false
```

**match-up pair format:**
```yaml
- left: "вмиватися"
  right: "to wash oneself"
```

## Output Format

Return TWO YAML blocks with clear delimiters:

```
===ACTIVITIES_START===
- type: fill-in
  title: "Conjugate Reflexive Verbs"
  items:
    - sentence: "..."
      answer: "..."
      options: ["...", "...", "...", "..."]
# ... 8+ activities total
===ACTIVITIES_END===

===VOCABULARY_START===
---
module: 09-reflexive-verbs
level: A1
version: '2.0'
items:
- lemma: вмиватися
  ipa: /vmɪˈvɑtɪsʲɑ/
  translation: to wash oneself
  pos: verb
# ... 12+ items
===VOCABULARY_END===
```

## Boundaries

- Do NOT modify lesson content — only generate activities and vocabulary
- Do NOT add fields not in the schema (check schema carefully!)
- Do NOT use activity types not allowed at A1 (no cloze, mark-the-words, select, translate, error-correction)
- Do NOT request skills or delegate to Claude
