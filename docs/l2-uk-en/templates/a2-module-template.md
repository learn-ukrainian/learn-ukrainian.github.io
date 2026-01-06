# A2 Module Template

> **Level:** A2 (Elementary)
> **Pedagogy:** PPP (Presentation-Practice-Production)
> **Focus:** All 7 cases, aspect introduction, comparison, complex sentences
> **Immersion:** Graduated (M01-15: 40-50%, M16-35: 50-65%, M36-50: 65-80%)

---

## Template Checklist

Before submitting, verify:

- [ ] Frontmatter complete (module, title, phase, pedagogy, objectives)
- [ ] Word count meets target (1000+ words)
- [ ] NO transliteration in body text
- [ ] 10+ activities with 12+ items each
- [ ] 4+ unique activity types including error-correction
- [ ] 4+ engagement boxes
- [ ] Bilingual structure (English intro + Ukrainian Вступ)
- [ ] Vocabulary table with IPA pronunciation
- [ ] All activity answers are correct

---

## Frontmatter

```yaml
---
module: a2-{NN}
title: "{Title in English}"
subtitle: "{Descriptive subtitle}"
version: "1.0"
phase: "A2.{1|2|3}"
pedagogy: "PPP"
duration: "60 min"
transliteration: none
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

---

## Module Structure

### # {Ukrainian Title}

Main title in Ukrainian (matching topic).

### ## Introduction

English introduction (100-150 words):
- Context for what's being learned
- Connection to previous knowledge
- Overview of module content
- Why this grammar/vocab matters

### ## Вступ

Ukrainian introduction (100-150 words):
- Same content as English intro but in Ukrainian
- Appropriate for A2 level complexity
- Maximum 15 words per sentence
- Use vocabulary learner already knows

### ## Presentation

Core lesson content with bilingual approach:

#### ### {English Section Title}

Concept explanation in English:
- Clear grammar rules
- Comparison tables
- 4-6 example sentences

```markdown
| Називний | Давальний | Приклад |
|----------|-----------|---------|
| я | мені | Дай мені книгу. |
```

#### ### {Ukrainian Section Title}

Same concept reinforced in Ukrainian:
- Simpler explanation
- More examples
- Pattern highlighting

> 💡 **Did You Know?**
>
> {Cultural or linguistic insight}

### ## Practice

Guided practice section:
- Transformation exercises
- Pattern completion
- Guided dialogues

### ## Dialogues

2-3 mini-dialogues demonstrating grammar in context:

```markdown
**А:** Тобі подобається кава?
**Б:** Так, мені дуже подобається кава!
```

### ## Summary

Brief recap in Ukrainian (75-100 words):
- Key grammar points
- Most important vocabulary
- Encouragement

### ## Activities

10+ activities from allowed types:

**A2 Activity Types:**
- `quiz` - Multiple choice
- `match-up` - Pair matching
- `fill-in` - Gap fill with options
- `true-false` - Statement validation
- `group-sort` - Category sorting
- `unjumble` - Word reordering (10-12 words)
- `error-correction` - Find and fix errors (NEW at A2)
- `cloze` - Passage completion (NEW at A2)
- `mark-the-words` - Click matching words (NEW at A2)

**Activity Requirements:**
- 12+ items per activity
- 4+ unique activity types
- Must include `error-correction`
- All error-correction items need `[!explanation]`

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

**error-correction** (all 4 callouts required):
```markdown
## error-correction: Title
1. Sentence with error.
   > [!error] wrong_word
   > [!answer] correct_word
   > [!options] wrong | correct | distractor1 | distractor2
   > [!explanation] Why it's wrong and how to fix.
```

**cloze** (passage with multiple blanks):
```markdown
## cloze: Title
> Text with {blank1|option1|option2|answer} and {blank2|opt1|opt2|answer} blanks.
```

**mark-the-words** (click matching words):
```markdown
## mark-the-words: Title
> [!instruction] Click all nouns in the sentence.
>
> *Мама* читає *книгу* в *кімнаті*.
```

### ## Vocabulary

```markdown
| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| мені | /meˈnʲi/ | to me | pron | — | dative |
```

---

## A2 Constraints

### Grammar Allowed (Building on A1)
- All 7 cases (Dative and Instrumental introduced)
- Aspect pairs (introduction)
- Comparison (вищий ступінь)
- Simple subordinate clauses
- Past tense
- Future tense (imperfective)

### Grammar Introduced at A2
- Dative case (давальний)
- Instrumental case (орудний)
- Perfective aspect basics
- Subordinate clauses with що, бо

### Sentence Complexity
- Maximum 15 words per sentence
- Up to 2 clauses
- Simple coordination (і, а, але)
- Simple subordination (що, бо)

---

## A2 Phases and Immersion

| Phase | Modules | Immersion Target | Focus |
|-------|---------|------------------|-------|
| A2.1 | 01-15 | 40-50% | Dative, Instrumental introduction |
| A2.2 | 16-35 | 50-65% | Aspect pairs, comparison |
| A2.3 | 36-50 | 65-80% | Complex sentences, integration |

---

## Quality Targets

| Metric | Target |
|--------|--------|
| Words | 1000+ |
| Activities | 10+ |
| Items/activity | 12+ |
| Unique types | 4+ |
| Engagement boxes | 4+ |
| Vocabulary | 20+ |
| Dialogues | 2+ |

---

## Error-Correction Format (Critical)

A2 introduces error-correction. **All 4 callouts are required:**

```markdown
## error-correction: Find the Mistake

1. Я даю книга тобі.
   > [!error] книга
   > [!answer] книгу
   > [!options] книга | книгу | книги | книзі
   > [!explanation] Direct object requires accusative case: книга → книгу
```

---

## Example Module Skeleton

```markdown
---
module: a2-01
title: "The Dative I — Pronouns"
subtitle: "To Whom Does This Belong?"
version: "1.0"
phase: "A2.1"
pedagogy: "PPP"
duration: "60 min"
transliteration: none
tags:
  - grammar
  - cases
  - dative
grammar:
  - dative pronouns
  - verbs with dative
objectives:
  - "Learner can use dative pronouns"
  - "Learner can express likes using подобатися"
  - "Learner can describe states with dative"
vocabulary_count: 26
---

# Давальний відмінок I — Займенники

## Introduction

{English introduction explaining dative case context...}

## Вступ

{Ukrainian introduction at A2 level...}

## Presentation

### Why the Dative Case Matters

{English explanation with table...}

### Займенники в давальному відмінку

{Ukrainian reinforcement...}

> 💡 **Did You Know?**
> {Interesting fact about dative in Ukrainian culture}

## Practice

{Guided exercises...}

## Dialogues

**А:** Тобі подобається ця книга?
**Б:** Так, мені дуже подобається!

## Summary

{Ukrainian recap...}

## Activities

## quiz: Dative Pronouns
1. "To me" in Ukrainian is:
   - [ ] мене
   - [x] мені
   - [ ] мною
   - [ ] я
{... 11 more items}

## error-correction: Fix the Case
1. Я кажу вона правду.
   > [!error] вона
   > [!answer] їй
   > [!options] вона | їй | її | вони
   > [!explanation] "Tell to someone" requires dative: вона → їй
{... 5 more items}

## match-up: Nominative to Dative
| Left | Right |
|------|-------|
| я | мені |
| ти | тобі |
{... more pairs}

{... more activities}

## Vocabulary

| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| мені | /meˈnʲi/ | to me | pron | — | dative of я |
{... more vocabulary}
```
