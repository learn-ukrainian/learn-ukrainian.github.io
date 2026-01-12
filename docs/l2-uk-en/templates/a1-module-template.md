# A1 Module Template

> **Level:** A1 (Beginner)
> **Pedagogy:** PPP (Presentation-Practice-Production)
> **Focus:** Cyrillic alphabet, basic vocabulary, simple phrases
> **Immersion:** Graduated (M01-05: 20-30%, M06-20: 40-60%, M21-34: 60-80%)

<!--
TEMPLATE_METADATA:
  required_sections:
  - Warm-up|Introduction|Objectives|Контекст|Вступ|Розминка
  - Presentation|Grammar|Focus|Презентація|Граматика|Теорія
  - Practice|Exercises|Activity|Практика|Вправи
  - Summary|Підсумок
  - Need More Practice?
  optional_sections:
  - Cultural Note
  - Pronunciation Tips
  forbidden_headers:
  - Activities
  - Vocabulary
  - External Resources
  pedagogy: PPP
  min_word_count: 300
  required_callouts: []
  description: A1 uses PPP pedagogy with graduated immersion and Cyrillic focus
-->

---

## Template Checklist

Before submitting, verify:

- [ ] Frontmatter complete (module, title, phase, pedagogy, objectives)
- [ ] Word count meets target (M01-05: 300+, M06-10: 500+, M11-34: 750+)
- [ ] Transliteration appropriate for module number
- [ ] 8+ activities with 12+ items each
- [ ] 4+ unique activity types
- [ ] 3+ engagement boxes
- [ ] Vocabulary table with IPA pronunciation
- [ ] All activity answers are correct

---

## Frontmatter

```yaml
---
module: a1-{NN}
title: '{Title in English}'
subtitle: '{Descriptive subtitle}'
version: '1.0'
phase: 'A1.{1|2|3}'
pedagogy: 'PPP'
duration: '60 min'
transliteration: '{full|partial|first-occurrence|none}'
tags:
  - { topic1 }
  - { topic2 }
grammar:
  - { grammar point 1 }
  - { grammar point 2 }
objectives:
  - 'Learner can {objective 1}'
  - 'Learner can {objective 2}'
  - 'Learner can {objective 3}'
vocabulary_count: 25 # Must match count in vocabulary/{slug}.yaml
---
```

### Transliteration Rules

| Modules | Phase | Transliteration    | Example          |
| ------- | ----- | ------------------ | ---------------- |
| 01-10   | A1.1  | `full`             | Слово (Slovo)    |
| 11-20   | A1.2  | `partial`          | Vocab lists only |
| 21-34   | A1.3  | `first-occurrence` | First time only  |


---

## Naturalness Quality Checklist

**Run this check during Stage 4 (Review & Fix) on prose activities.**

Before finalizing the module, verify prose activities (cloze, fill-in, unjumble with 5+ sentences) achieve:

- [ ] **Subject consistency** - Clear subjects maintained throughout passages
- [ ] **Discourse markers** - At least 2-3 connectors per 10-sentence passage (а, але, потім, тому, також, спочатку, нарешті)
- [ ] **Topic coherence** - All sentences contribute to unified narrative/theme, no random topic jumps
- [ ] **No template repetition** - Varied sentence structures across activities within the module
- [ ] **Moderate intensifiers** - Maximum 2-3 "дуже" per module, 0-1 "надзвичайно/справжній"
- [ ] **No double superlatives** - Use one precise descriptor instead of redundant pairs (e.g., "найкращий" NOT "найкращий та найвидатніший")
- [ ] **Natural transitions** - Avoid robotic "і це", "тому що... тому" patterns

**Target score:** 8/10 for content modules, 7/10 for checkpoints

**Red flags (score < target):**
- Same sentence template repeated across multiple activities
- Disconnected factoid lists without discourse markers
- Excessive intensifiers or double superlatives
- Robotic, mechanical transitions

**See:** `claude_extensions/stages/stage-4-review-fix.md` Section 9 for detailed naturalness criteria.

**For batch scanning:** Use `/scan-naturalness {level} {start} {end}` to scan completed modules.

---

## Module Structure

### # {Title}

Main title matching frontmatter.

### ## Warm-up

Brief engaging introduction (50-100 words):

- Hook the learner with something relatable
- Preview what they'll learn
- Build confidence ("You already know...")

### ## Presentation

Core lesson content organized into subsections:

#### ### {Subsection 1}

Introduce concept with:

- Clear explanation in English (A1 allows English)
- Table showing patterns
- 3-5 example words/phrases with transliteration (if applicable)

```markdown
| Letter  | Sound | Example | English |
| ------- | ----- | ------- | ------- |
| **А а** | /ɑ/   | мама    | mama    |
```

#### ### {Subsection 2}

Continue with next concept...

> 💡 **Did You Know?**
>
> {Interesting cultural or linguistic fact}

#### ### {Subsection 3}

More content...

> 🎬 **Pop Culture Moment**
>
> {Reference to games, movies, music that learners might know}

### ## Practice

Guided practice section (optional for some modules):

- Controlled exercises
- Pattern drills
- Guided discovery

### ## Summary

Brief recap (50-75 words):

- What was learned
- Key takeaways
- Encouragement for next steps

### ## Activities

8+ activities from allowed types:

**A1 Activity Types:**

- `quiz` - Multiple choice
- `match-up` - Pair matching
- `fill-in` - Gap fill with options
- `true-false` - Statement validation
- `group-sort` - Category sorting
- `unjumble` - Word reordering
- `anagram` - Letter unscrambling (M01-10 only)

**Activity Requirements:**

- 12+ items per activity
- 4+ unique activity types
- Clear instructions in English
- All answers must be correct

### Activity Format Quick Reference

**CRITICAL:** Activities must be defined in `activities/{slug}.yaml`. Do NOT embed activities in Markdown.

See [ACTIVITY-YAML-REFERENCE.md](../../ACTIVITY-YAML-REFERENCE.md) for schemas and examples.

**Example `activities/a1-XX-module.yaml`:**

```yaml
- type: quiz
  title: Number Recognition
  items:
    - question: What number is "п'ять"?
      options:
        - text: '3'
          correct: false
        - text: '5'
          correct: true

- type: match-up
  title: Numbers and Words
  pairs:
    - left: один
      right: '1'
```

### ## Vocabulary

**CRITICAL:** Vocabulary must be defined in `vocabulary/{slug}.yaml`. Do NOT embed a vocabulary table in Markdown.

**Example `vocabulary/a1-XX-module.yaml`:**

```yaml
items:
  - lemma: слово
    ipa: /slɔwɔ/
    translation: word
    pos: noun
    gender: n
    note: —
```

---

## A1 Constraints

### Grammar Allowed

- Nominative case (naming things)
- Accusative case (direct objects, basic)
- Locative case (locations with в/у/на)
- Genitive case (possession, quantities)
- Vocative case (addressing people)
- Present tense verbs
- Imperfective aspect only

### Grammar Forbidden

- Dative case (introduced A2)
- Instrumental case (introduced A2)
- Perfective aspect (introduced A2)
- Participles
- Subordinate clauses (що, який, бо)

### Sentence Complexity

- Maximum 10 words per sentence
- Single clause only
- Simple subject-verb-object patterns

---

## Quality Targets

| Metric           | M01-05 | M06-10 | M11-34 |
| ---------------- | ------ | ------ | ------ |
| Words            | 300+   | 500+   | 750+   |
| Activities       | 8+     | 8+     | 8+     |
| Items/activity   | 12+    | 12+    | 12+    |
| Engagement boxes | 2+     | 3+     | 3+     |
| Vocabulary       | 15+    | 20+    | 25+    |

---

## Example Module Skeleton

```markdown
---
module: a1-05
title: 'Numbers and Counting'
subtitle: 'From Zero to Hero'
version: '1.0'
phase: 'A1.1'
pedagogy: 'PPP'
duration: '60 min'
transliteration: 'full'
tags:
  - numbers
  - counting
grammar:
  - cardinal numbers 0-20
objectives:
  - 'Learner can count from 0 to 20'
  - 'Learner can recognize written numbers'
  - 'Learner can use numbers in basic phrases'
vocabulary_count: 25
---

# Numbers and Counting

## Warm-up

{Engaging intro about why numbers matter...}

## Presentation

### Numbers 0-10

{Content with table, examples, pronunciation...}

> 💡 **Did You Know?**
> {Interesting fact about Ukrainian numbers}

### Numbers 11-20

{Content continues...}

## Summary

{Brief recap}

---

## Content Structure Note

### Activities & Vocabulary

**CRITICAL:** Do NOT add `## Activities` or `## Vocabulary` headers. These sections are injected automatically from:

- `activities/a1-05-numbers.yaml`
- `vocabulary/a1-05-numbers.yaml`
```
