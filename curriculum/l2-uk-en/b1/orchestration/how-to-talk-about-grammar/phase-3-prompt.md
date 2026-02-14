# Phase 3: Activities & Vocabulary Generation

> **You are Gemini, executing Phase 3 of an orchestrated rebuild.**
> **Your ONLY task: Generate activities YAML and vocabulary YAML.**

## Pre-flight Checklist

Before writing ANY YAML, confirm these targets:

| Target | Value |
|--------|-------|
| Skill identity | Patient & Supportive Ukrainian Tutor |
| Persona flavor | The Helpful Neighbor |
| Module persona | Senior Language & Culture Specialist, acting as Linguistics Professor |
| Activities required | 4–6 |
| Items per activity | ≥6 |
| Required types | quiz, match-up |
| Priority types | quiz, match-up, fill-in, error-correction, mark-the-words, essay-response, critical-analysis |
| Vocabulary items | 25 |

Keep this table visible as you write. Every activity and vocab item must serve these targets.

## Your Input

Read these files from disk:

**Lesson content** (generate activities that test/reinforce this content):
```
curriculum/l2-uk-en/b1/how-to-talk-about-grammar.md
```

**Plan file** (vocabulary_hints — vocabulary list to follow):
```
curriculum/l2-uk-en/plans/b1/how-to-talk-about-grammar.yaml
```

**Meta file** (activity count targets, pedagogy):
```
curriculum/l2-uk-en/b1/meta/how-to-talk-about-grammar.yaml
```

**Activity schema** (CRITICAL — defines allowed fields per activity type):
```
schemas/activities-b1.schema.json
```

**Activity reference guide**:
```
docs/ACTIVITY-YAML-REFERENCE.md
```

## Your Task

Generate two YAML blocks: activities and vocabulary.

### Activities YAML Rules

1. **BARE LIST at root** — no `activities:` wrapper, no `module:` or `level:` headers
2. **Schema compliance** — only use fields defined in the schema. `additionalProperties: false` means unlisted fields cause audit failure.
3. **Core track style** (b1 bridge): Focus on testing metalanguage knowledge — matching terms, identifying parts of speech, filling in grammar terminology.
4. **Activity count**: 5 activities (min 4, max 6)
5. **Type variety**: Use at least 3 different activity types
6. **Only `reading` type has `id` field** — do NOT add `id` to other types
7. **`essay-response` rubric fields**: `criteria` / `description` / `points` (NOT `criterion` / `weight`)
8. **`mark-the-words` format**: Use `text` (no asterisks) + `answers` array

### CRITICAL: Activity Type Constraints for b1

**ALLOWED types (use ONLY these):** quiz, match-up, fill-in, error-correction, mark-the-words, essay-response, critical-analysis, true-false, translate, select

**FORBIDDEN types (audit will auto-FAIL if you use these):** cloze, group-sort, unjumble, anagram, reading, comparative-study, authorial-intent

Using a forbidden type wastes the entire activity generation phase. Check the allowed list BEFORE writing each activity.

### Common Schema Mistakes (FIX BEFORE OUTPUT)

**These mistakes caused audit failures in previous rebuilds. Check EVERY activity against these rules:**

1. **Quiz `explanation` placement** — `explanation` goes at the QUESTION level, NOT inside an option. WRONG:
```yaml
options:
  - text: "відповідь"
    correct: true
    explanation: "Пояснення"  # WRONG — explanation is not a valid option field
```
CORRECT:
```yaml
explanation: "Пояснення чому ця відповідь правильна"
options:
  - text: "відповідь"
    correct: true
```

2. **Quiz question text length** — Every `question` field must be ≥5 words. WRONG: "Слово «хто» — це..." (3 words). RIGHT: "До якої частини мови належить слово «хто»?" (8 words). Short questions fail the pedagogy gate.

3. **No extra fields** — The schema uses `additionalProperties: false`. ANY field not in the schema causes instant failure. Common mistakes: adding `id` to non-reading activities, adding `hint` where not allowed, adding `explanation` inside option objects.

4. **Vocabulary YAML structure** — Use object with `items:` array wrapper. Each entry uses `lemma` (NOT `term`), `translation`, `pos`. Optional: `ipa`, `gender` (m/f/n for nouns), `aspect` (for verbs), `notes`, `usage`, `example`. Do NOT use bare list for vocabulary.

### Activity Quality Standards (MANDATORY)

**These rules prevent low-quality activities that waste learner time:**

1. **Production over recognition** — At least 2 activities must require the learner to PRODUCE language, not just recognize it. Production types: `translate` (with free text, not multiple choice), `fill-in`, `error-correction`. Recognition types: `quiz`, `true-false`, `select`, `match-up`. A module with only recognition activities fails review.

2. **Plausible example sentences** — Every sentence in every activity must be something a real Ukrainian speaker might actually say, write, or encounter. FORBIDDEN: philosophical/motivational statements ("Граматика — це музика мови"), meta-sentences about learning. GOOD: everyday speech, textbook excerpts, teacher instructions, realistic dialogues.

3. **mark-the-words minimum** — `mark-the-words` activities must have at least 3 separate text passages (sentences or short paragraphs).

4. **Error-correction precision** — Each item must have exactly one clear error with one correct fix. The error must be a plausible learner mistake.

5. **Item count consistency** — Activities of the same type should have similar item counts (±2).

### Language Quality (applies to ALL Ukrainian text in activities)

- **Typography**: ALWAYS use Ukrainian angular quotes «...» (never straight quotes "...")
- **No Russianisms**: кушати→їсти, приймати участь→брати участь, получати→отримувати, самий кращий→найкращий
- **No Russian characters**: ы, э, ё, ъ must NEVER appear
- **IPA**: Use IPA notation only (no Latin transliteration)

### Vocabulary YAML Rules

1. **Object with `items:` wrapper** — NOT a bare list. Required structure: `items:` array
2. **Follow plan's vocabulary_hints** — include all required items, optionally include recommended
3. **Each entry needs**: `lemma` (NOT `term`), `translation`, `pos` (part of speech)
4. **Optional fields**: `ipa`, `gender` (for nouns: m/f/n), `aspect` (for verbs), `notes`, `usage`, `example`
5. **IPA must have correct stress** — verify stress placement
6. **Count target**: 25 items

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

Return TWO YAML blocks with clear delimiters:

### Activity Count Check (MANDATORY)

**Count your activities before outputting.** You MUST generate 5 activities (min 4, max 6). Types to add when short: quiz (8+ items), fill-in (8+ items), match-up (8+ pairs).

### Output Delimiters

Activities block (BARE LIST — no wrapper):

```
===ACTIVITIES_START===

- type: quiz
  title: "..."
  items:
    ...

- type: match-up
  title: "..."
  pairs:
    ...

===ACTIVITIES_END===
```

Vocabulary block (OBJECT with `items:` wrapper):

```
===VOCABULARY_START===

items:
  - lemma: "іменник"
    translation: "noun"
    ipa: "/i.ˈmɛn.nɪk/"
    pos: "noun"
  - lemma: "дієслово"
    translation: "verb"
    ipa: "/di.jeˈslɔ.wɔ/"
    pos: "noun"
    notes: "describes the concept of a verb as a part of speech"

===VOCABULARY_END===
```

## Friction Report (MANDATORY)

After your YAML blocks, include:

```
===FRICTION_START===
**Phase**: Phase 3: Activities + Vocabulary
**Step**: {what you were doing when friction occurred, or "Full YAML generation"}
**Friction Type**: NONE | YAML_SCHEMA_VIOLATION | TOKEN_LIMIT_TRUNCATION | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

## Boundaries

- Do NOT modify lesson content — only generate activities and vocabulary
- Do NOT add fields not in the schema (check schema carefully!)
- Do NOT wrap activities in `activities:` dictionary key
- Do NOT add `id` field to non-reading activities
- Do NOT request skills or delegate to Claude
- Do NOT use FORBIDDEN types (cloze, group-sort, unjumble, anagram)
