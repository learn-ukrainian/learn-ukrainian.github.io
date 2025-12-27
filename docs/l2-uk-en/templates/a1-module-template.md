# A1 Module Template

> **Level:** A1 (Beginner)
> **Pedagogy:** PPP (Presentation-Practice-Production)
> **Focus:** Cyrillic alphabet, basic vocabulary, simple phrases
> **Immersion:** Graduated (M01-05: 20-30%, M06-20: 40-60%, M21-34: 60-80%)

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
title: "{Title in English}"
subtitle: "{Descriptive subtitle}"
version: "1.0"
phase: "A1.{1|2|3}"
pedagogy: "PPP"
duration: "60 min"
transliteration: "{full|partial|first-occurrence|none}"
tags:
  - {topic1}
  - {topic2}
grammar:
  - {grammar point 1}
  - {grammar point 2}
objectives:
  - "Learner can {objective 1}"
  - "Learner can {objective 2}"
  - "Learner can {objective 3}"
vocabulary_count: {N}
---
```

### Transliteration Rules

| Modules | Phase | Transliteration | Example |
|---------|-------|-----------------|---------|
| 01-10 | A1.1 | `full` | Слово (Slovo) |
| 11-20 | A1.2 | `partial` | Vocab lists only |
| 21-34 | A1.3 | `first-occurrence` | First time only |

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
| Letter | Sound | Example | English |
|--------|-------|---------|---------|
| **А а** | /ɑ/ | мама | mama |
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

**CRITICAL:** Use these exact formats for MDX generation to work.

**quiz** (multiple choice - single answer):
```markdown
## quiz: Title
1. Question text?
   - [ ] Wrong answer
   - [x] Correct answer
   - [ ] Wrong answer
   - [ ] Wrong answer
```

**match-up** (pair matching):
```markdown
## match-up: Title
| Left | Right |
|------|-------|
| слово | word |
| книга | book |
```

**fill-in** (gap fill with options):
```markdown
## fill-in: Title
1. Sentence with _____ blank.
   > [!answer] correct
   > [!options] wrong1 | correct | wrong2 | wrong3
```

**true-false** (checkbox format with explanations):
```markdown
## true-false: Title
- [x] True statement here.
  > Explanation why it's true.
- [ ] False statement here.
  > Explanation why it's false.
```

**group-sort** (category headers with bullets):
```markdown
## group-sort: Title
### Category A
- item1
- item2
### Category B
- item3
- item4
```

**unjumble** (word reordering):
```markdown
## unjumble: Title
1. слово / інше / ще
   > [!answer] Правильне речення тут.
```

**anagram** (M01-10 only - letter unscrambling):
```markdown
## anagram: Title
1. овсло
   > [!answer] слово
```

### ## Vocabulary

```markdown
| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| слово | /ˈslɔwɔ/ | word | noun | n | — |
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

| Metric | M01-05 | M06-10 | M11-34 |
|--------|--------|--------|--------|
| Words | 300+ | 500+ | 750+ |
| Activities | 8+ | 8+ | 8+ |
| Items/activity | 12+ | 12+ | 12+ |
| Engagement boxes | 2+ | 3+ | 3+ |
| Vocabulary | 15+ | 20+ | 25+ |

---

## Example Module Skeleton

```markdown
---
module: a1-05
title: "Numbers and Counting"
subtitle: "From Zero to Hero"
version: "1.0"
phase: "A1.1"
pedagogy: "PPP"
duration: "60 min"
transliteration: "full"
tags:
  - numbers
  - counting
grammar:
  - cardinal numbers 0-20
objectives:
  - "Learner can count from 0 to 20"
  - "Learner can recognize written numbers"
  - "Learner can use numbers in basic phrases"
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

## Activities

## quiz: Number Recognition
1. What number is "п'ять"?
   - [ ] 3
   - [x] 5
   - [ ] 7
   - [ ] 9
{... 11 more items}

## match-up: Numbers and Words
| Left | Right |
|------|-------|
| один | 1 |
| два | 2 |
{... 10 more pairs}

{... more activities}

## Vocabulary

| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| нуль | /nulʲ/ | zero | noun | m | — |
| один | /oˈdɪn/ | one | num | m | — |
{... more vocabulary}
```
