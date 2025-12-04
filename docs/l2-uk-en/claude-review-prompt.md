# Module Enrichment Prompt

<constraints>
## CRITICAL RULES - READ FIRST

**NEVER:**
- NEVER keep existing activities - DELETE ALL and recreate from scratch
- NEVER add activities without rebuilding vocabulary first
- NEVER skip any step in the 3-step workflow
- NEVER use vocabulary words not in the module's vocabulary section
- NEVER create activities with fewer items than required
- NEVER write sentences shorter than required word count

**ALWAYS:**
- ALWAYS follow the 3-step workflow in EXACT order
- ALWAYS delete ALL existing activities before creating new ones
- ALWAYS run vocab:enrich after narrative changes
- ALWAYS verify every activity answer is correct
- ALWAYS use ONLY vocabulary from the rebuilt vocabulary section
</constraints>

---

## The 3-Step Enrichment Workflow

<instructions>
**This is the ONLY correct way to enrich a module. No shortcuts.**

### STEP 1: ENRICH NARRATIVE CONTENT

Improve the lesson content (everything BEFORE `# Activities`):

1. **Add engagement boxes** (minimum 3 for A1, see table below)
   - 💡 Did You Know - Interesting facts
   - 🎬 Pop Culture Moment - Movies, games, music (Lord of the Rings, S.T.A.L.K.E.R., Witcher)
   - 🌍 Real World - Practical usage scenarios
   - 🎯 Fun Fact - Memorable trivia
   - 🎮 Gamer's Corner - Gaming references

2. **Add example sentences** (minimum 12 for A1)
   - Each example: Ukrainian + transliteration (for A1) + English
   - Show the grammar/vocabulary in realistic context

3. **Enrich explanations**
   - Add tables for grammar patterns
   - Add comparison boxes (correct vs incorrect)
   - Add memory tricks and mnemonics

4. **DO NOT touch the Activities section yet**

### STEP 2: REBUILD VOCABULARY

After narrative enrichment, run:
```bash
npm run vocab:enrich l2-uk-en [moduleNum]
```

This captures ALL words from the enriched lesson. Wait for this to complete before Step 3.

### STEP 3: COMPLETELY RECREATE ALL ACTIVITIES

**DELETE the entire `# Activities` section and everything in it.**

Then create fresh activities that:
- Use ONLY vocabulary from the rebuilt vocabulary section (Step 2)
- Meet all quantity requirements (see tables below)
- Have verified correct answers
- Follow the activity format templates exactly

### STEP 4: GENERATE AND VERIFY

```bash
npx ts-node scripts/generate.ts l2-uk-en [moduleNum]
```

Open the HTML output and verify activities work correctly.
</instructions>

---

## Requirements by Level

### Activity Requirements

| Level | Modules | Min Activities | Items per Activity | Fill-in Words | Unjumble Words |
|-------|---------|----------------|-------------------|---------------|----------------|
| **A1** | 1-30 | **8** | **12** | 5-8 | 5-8 |
| A2 | 31-60 | 10 | 12 | 6-9 | 6-9 |
| A2+ | 61-80 | 10 | 12 | 6-10 | 6-10 |
| B1 | 81-120 | 12 | 14 | 7-11 | 7-11 |
| B1+ | 121-160 | 12 | 14 | 8-12 | 8-12 |
| B2 | 161-200 | 14 | 16 | 9-14 | 9-14 |

### Content Requirements

| Level | Min Examples | Min Engagement Boxes | Immersion (Ukrainian %) |
|-------|--------------|---------------------|------------------------|
| **A1** | **12** | **3** | 30% (±15% tolerance) |
| A2 | 15 | 4 | 40% |
| A2+ | 18 | 4 | 50% |
| B1 | 22 | 5 | 60% |
| B1+ | 24 | 5 | 70% |
| B2 | 26 | 6 | 85% |

### Required Activity Types (use at least 4 different types)

1. `fill-in` - Gap fill with options
2. `unjumble` - Reorder words into sentence
3. `quiz` - Multiple choice questions
4. `match-up` - Match pairs
5. `group-sort` - Sort items into categories
6. `true-false` - True/false statements

---

## Activity Format Templates

### fill-in (Gap Fill)

```markdown
## fill-in: Title

> Instructions explaining what to do.

1. Sentence with ___ blank here. (5-8 words for A1)
   > [!answer] correct answer
   > [!options] wrong1 | correct answer | wrong2 | wrong3

2. Another ___ sentence here. (5-8 words for A1)
   > [!answer] correct answer
   > [!options] wrong1 | wrong2 | correct answer | wrong3
```

**Requirements:**
- Minimum 12 items for A1
- Each sentence: 5-8 words for A1
- 4 options per item (1 correct, 3 distractors)
- Distractors must be plausible but clearly wrong

### unjumble (Word Ordering)

```markdown
## unjumble: Title

> Arrange the words in correct order.

1. слово1 / слово2 / слово3 / слово4 / слово5
   > [!answer] Correct sentence in proper order.
   > (English translation) [5 words]

2. слово1 / слово2 / слово3 / слово4 / слово5 / слово6
   > [!answer] Correct sentence in proper order.
   > (English translation) [6 words]
```

**Requirements:**
- Minimum 12 items for A1
- Each sentence: 5-8 words for A1
- Include word count in brackets
- Words separated by ` / `

### quiz (Multiple Choice)

```markdown
## quiz: Title

> Choose the correct answer.

1. Question about the topic?
   - [ ] Wrong answer
   - [x] Correct answer
   - [ ] Wrong answer
   - [ ] Wrong answer
   > Explanation of why this is correct.

2. Another question?
   - [x] Correct answer
   - [ ] Wrong answer
   - [ ] Wrong answer
   - [ ] Wrong answer
   > Explanation.
```

**Requirements:**
- Minimum 12 items for A1
- 4 options per question
- Exactly one `[x]` correct answer
- Explanation after each question

### match-up (Pair Matching)

```markdown
## match-up: Title

> Match the Ukrainian words with their English meanings.

| Left | Right |
|------|-------|
| українське | english |
| слово | word |
| речення | sentence |
```

**Requirements:**
- Minimum 12 pairs for A1
- Left column: Ukrainian
- Right column: English (or matching concept)

### group-sort (Categorization)

```markdown
## group-sort: Title

> Sort these items into the correct categories.

### Category 1 Name
- item belonging to category 1
- another item for category 1
- third item for category 1

### Category 2 Name
- item belonging to category 2
- another item for category 2
- third item for category 2
```

**Requirements:**
- Minimum 12 total items for A1
- 2-4 categories
- At least 3 items per category

### true-false (Statement Validation)

```markdown
## true-false: Title

> Determine if each statement is true or false.

- [x] True statement about the topic.
  > Explanation of why this is true.

- [ ] False statement about the topic.
  > Explanation of why this is false and what the correct fact is.
```

**Requirements:**
- Minimum 12 items for A1
- Mix of true `[x]` and false `[ ]` statements
- Explanation for each item

---

## Engagement Box Formats

```markdown
> 💡 **Did You Know?**
>
> Interesting fact that helps learners remember the content.

> 🎬 **Pop Culture Moment**
>
> Reference to movies, games, or music that Ukrainian learners love.
> (Lord of the Rings, S.T.A.L.K.E.R., The Witcher, Metro 2033)

> 🌍 **Real World**
>
> How this is actually used in Ukraine today.

> 🎯 **Fun Fact**
>
> Memorable trivia that sticks in the learner's mind.
```

---

## Vocabulary Table Format

### A1-A2+ (Modules 1-80)

```markdown
# Vocabulary

| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| слово | /ˈslɔvɔ/ | word | noun | n | Example usage note |
```

### B1-B1+ (Modules 81-160)

```markdown
# Словник

| Слово | Вимова | Переклад | ЧМ | Примітка |
|-------|--------|----------|-----|----------|
| слово | /ˈslɔvɔ/ | word | ім. | Example note |
```

---

## Module 01 Specific Guidance

For Module 01 (The Cyrillic Code I), the audit found:

| Issue | Current | Required |
|-------|---------|----------|
| Activities | 7 | 8+ |
| Items per activity | 8-10 | 12+ |
| Examples | ~10 | 12+ |
| Immersion | 8% | 30% ±15% |

**Special considerations for Module 01:**
- This is an alphabet-teaching module, so lower Ukrainian % is acceptable
- Focus on letter recognition and basic sound patterns
- Use transliteration for ALL Ukrainian text: `Слово (Slovo)`
- Activities should reinforce letter-sound connections

**Activity ideas for alphabet modules:**
1. `quiz` - Letter sound identification ("What sound does Г make?")
2. `match-up` - Letters to sounds, letters to transliteration
3. `group-sort` - True friends vs False friends vs New letters
4. `fill-in` - Complete the transliteration
5. `true-false` - Statements about letter sounds
6. `quiz` - Word reading practice

---

## Checklist Before Submitting

- [ ] Step 1 complete: Narrative enriched with 12+ examples, 3+ engagement boxes
- [ ] Step 2 complete: `vocab:enrich` ran successfully
- [ ] Step 3 complete: ALL old activities deleted, 8+ new activities created
- [ ] Each activity has 12+ items
- [ ] Fill-in sentences are 5-8 words
- [ ] Unjumble sentences are 5-8 words
- [ ] All answers verified correct
- [ ] All vocabulary used is from the vocabulary section
- [ ] Step 4 complete: Generated and visually verified HTML output
