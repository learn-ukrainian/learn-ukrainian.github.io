# Phase 3: Activities & Vocabulary Generation

> **You are Gemini, executing Phase 3 of an orchestrated rebuild.**
> **Your ONLY task: Generate activities YAML and vocabulary YAML.**

## Pre-flight Checklist

Before writing ANY YAML, confirm these targets:

| Target | Value |
|--------|-------|
| Level | B1 (Core track) |
| Module | M01: Як говорити про граматику |
| Activities required | 8–12 |
| Items per activity | ≥8 (most types need ≥8 items) |
| Required unique types | ≥4 different types |
| Priority types | fill-in, unjumble, error-correction |
| Vocabulary items | 25+ (13 required + 13 recommended = 26 total) |

## Your Input

Read these files from disk:

**Lesson content** (generate activities that test/reinforce this content):
```
curriculum/l2-uk-en/b1/orchestration/how-to-talk-about-grammar/phase-2-content.md
```

**Plan file** (vocabulary_hints + activity_hints — follow these):
```
curriculum/l2-uk-en/plans/b1/how-to-talk-about-grammar.yaml
```

**Meta file** (activity count targets, pedagogy):
```
curriculum/l2-uk-en/b1/meta/how-to-talk-about-grammar.yaml
```

**Activity reference guide** (CRITICAL — defines format per type):
```
docs/ACTIVITY-YAML-REFERENCE.md
```

## Your Task

Generate two YAML blocks: activities and vocabulary.

### Activities YAML Rules

1. **BARE LIST at root** — no `activities:` wrapper, no `module:` or `level:` headers
2. **Schema compliance** — only use fields defined in the reference guide
3. **Core B1 style**: Drill-based activities that reinforce terminology recognition and usage
4. **Activity count**: 8–12 activities
5. **Type variety**: Use at least 4 different activity types
6. **Item counts per activity**: Each activity must have ≥8 items (quiz: ≥8, match-up: ≥12 pairs, fill-in: ≥8, true-false: ≥8, group-sort: ≥12 items, unjumble: ≥6, error-correction: ≥6, mark-the-words: ≥6, select: ≥6, translate: ≥6, cloze: ≥5 sentences)
7. **NO `id` field** — only reading activities in seminar tracks use `id`

### CRITICAL: Activity Type Constraints for B1

**ALLOWED types (use ONLY these):** match-up, fill-in, quiz, true-false, group-sort, unjumble, error-correction, cloze, mark-the-words, select, translate

**FORBIDDEN types (audit will auto-FAIL):** essay-response, critical-analysis, comparative-study, authorial-intent, anagram

### Plan's Activity Hints (FOLLOW THESE)

The plan specifies these activities:
1. **match-up**: Ukrainian term → English equivalent (12+ items)
2. **quiz**: Identify part of speech by Ukrainian name (10+ items)
3. **fill-in**: Complete sentences about grammar using Ukrainian terms (8+ items)
4. **group-sort**: Categorize terms by category — parts of speech vs cases (15+ items)

You MUST include all 4 of these. Add 4-8 more activities of different types to reach 8+ total and 4+ unique types.

### Suggested Additional Activities

5. **true-false**: Statements about grammar terminology (8+ items)
6. **unjumble**: Rearrange words to form grammatically correct sentences about grammar (6+ items)
7. **mark-the-words**: Mark specific parts of speech in sentences (6+ items)
8. **translate**: Translate grammar terms between Ukrainian and English (6+ items)
9. **error-correction**: Fix incorrect grammar terminology usage (6+ items)

### Vocabulary YAML Rules

1. **BARE LIST at root** — no `vocabulary:` wrapper
2. **Follow plan's vocabulary_hints** — include ALL 13 required items + ALL 13 recommended items
3. **Each entry needs**: `term`, `translation`, `ipa`, `pos` (part of speech), `grammatical_info`
4. **IPA must have correct stress** — verify stress placement
5. **Count target**: 26 items (13 required + 13 recommended)

### Required vocabulary (from plan):
- дієслово (verb), іменник (noun), прикметник (adjective), прислівник (adverb), займенник (pronoun), числівник (numeral)
- називний відмінок (nominative case), родовий відмінок (genitive case), давальний відмінок (dative case), знахідний відмінок (accusative case), орудний відмінок (instrumental case), місцевий відмінок (locative case), кличний відмінок (vocative case)

### Recommended vocabulary (from plan):
- сполучник (conjunction), прийменник (preposition), частка (particle), вигук (interjection), граматика (grammar), правило (rule), приклад (example), метамова (metalanguage), підмет (subject), присудок (predicate), додаток (object), означення (attribute), обставина (adverbial)

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded.

Return TWO YAML blocks with clear delimiters:

```
===ACTIVITIES_START===
- type: match-up
  title: "..."
  ...

- type: quiz
  title: "..."
  ...
===ACTIVITIES_END===
```

```
===VOCABULARY_START===
- term: дієслово
  translation: verb
  ipa: "..."
  pos: noun
  grammatical_info: "..."

- term: іменник
  ...
===VOCABULARY_END===
```

## Friction Report (MANDATORY)

```
===FRICTION_START===
**Phase**: Phase 3: Activities + Vocabulary
**Step**: {what}
**Friction Type**: NONE | ...
**Raw Error**: {or "None"}
**Self-Correction**: {or "N/A"}
**Proposed Tooling Fix**: {or "N/A"}
===FRICTION_END===
```

## Boundaries

- Do NOT modify lesson content — only generate activities and vocabulary
- Do NOT wrap in `activities:` or `vocabulary:` dictionary keys
- Do NOT use forbidden activity types
- Do NOT add vocabulary outside the plan's vocabulary_hints
- Do NOT add `id` field to activities (this is a core track, not seminar)
