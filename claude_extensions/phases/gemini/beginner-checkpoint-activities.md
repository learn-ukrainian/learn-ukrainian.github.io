# Beginner Checkpoint Activities & Vocabulary

> **You are Gemini, generating activities and vocabulary for a CHECKPOINT module.**
> **Your ONLY task: Generate activities YAML and vocabulary YAML.**

## CHECKPOINT IDENTITY

**This is a CHECKPOINT module — activities must test INTEGRATION, not isolated skills.**

Activities in a checkpoint module are fundamentally different from teaching module activities:

| Teaching Module Activities | Checkpoint Activities |
|---------------------------|----------------------|
| Test one skill at a time | Combine 2+ skills per activity |
| Practice newly introduced patterns | Review patterns from multiple prior modules |
| Drill specific grammar points | Test integrated language use |
| Focus on accuracy of new forms | Focus on fluency with known forms |

**Golden rule: Every activity should require the learner to combine skills from different prior modules.**

## Targets

| Target | Value |
|--------|-------|
| Skill identity | {SKILL_IDENTITY} |
| Module persona | {PERSONA_VOICE}, acting as {PERSONA_ROLE} |
| Activities required | {ACTIVITY_MIN}–{ACTIVITY_MAX} |
| Required types | {REQUIRED_TYPES} |
| Vocabulary items | {VOCAB_COUNT_TARGET} |

### Item Minimums Per Activity Type

{ITEM_MINIMUMS_TABLE}

**CRITICAL — HARD FAIL if violated:** Each activity MUST meet the minimum item count for its type.

{TEXTBOOK_ACTIVITY_EXAMPLES}

{DECODABLE_VOCABULARY}

## Vocabulary Scope

> **Every Ukrainian word in your activities MUST come from PRIOR modules that this checkpoint reviews.** Read the content file first. Do not introduce new Ukrainian vocabulary — only practice words from the reviewed block.

## Module Constraints (HARD FAIL if violated)

{PEDAGOGICAL_CONSTRAINTS}

> **These constraints apply to activities too.** If only specific letters are allowed, every Ukrainian word in activities must use ONLY those letters.

## Your Input

Read these files:

| File | Purpose |
|------|---------|
| `{CONTENT_PATH}` | Checkpoint content to reinforce |
| `{PLAN_PATH}` | vocabulary_hints (all REVIEW words) |
| `{SCHEMA_PATH}` | Allowed fields per activity type |
| `docs/ACTIVITY-YAML-REFERENCE.md` | Activity reference guide |

---

## Checkpoint Activity Design Principles

### 1. Integration Over Isolation

Each activity should combine skills. Examples:

- **Quiz**: Questions that require understanding BOTH gender AND adjective agreement (not just one)
- **Fill-in**: Sentences requiring correct case ending AND correct vocabulary choice
- **Unjumble**: Sentences combining vocabulary from 2+ prior modules
- **Group-sort**: Sorting by multiple criteria (gender + number, or case + meaning)

### 2. New Contexts, Familiar Words

Use all review vocabulary in situations the learner hasn't seen before:
- If they learned food words and adjectives separately, combine them: «велика піца», «свіжий хліб»
- If they learned greetings and questions separately, create dialogues that use both

### 3. Realistic Scenarios

Frame activities around realistic situations:
- Ordering at a cafe (combines food vocabulary + polite forms + questions)
- Describing a room (combines objects + adjectives + prepositions)
- Meeting someone new (combines greetings + introductions + questions)

### 4. Progressive Difficulty Within Activities

Start with simpler integration (2 skills) and build to more complex (3+ skills) within the same activity.

---

## Beginner Activity Rules

### Language in Activities

- **Questions, explanations, instructions** → English (scaffolding language)
- **Target content being practiced** → Ukrainian (words, phrases from prior modules)
- **Option text** → Ukrainian when selecting Ukrainian words/letters, English when selecting concepts

### Activity Types by Constraint Level

**If constraints say "letters/syllables only" (no sentences):**
Use: `quiz`, `match-up`, `group-sort`, `anagram`, `true-false`

**If constraints allow words and simple phrases:**
Add: `fill-in`, `match-up` with phrases

**If constraints allow basic sentences:**
Add: `unjumble`, `fill-in` with sentences, `translate`

### Do NOT Use Grammar Terminology

A1/A2 learners do NOT know terms like іменник, дієслово, голосний, відмінок. Write questions in plain English.

---

## Schema Reference

### quiz (English questions, Ukrainian options)

```yaml
- type: quiz
  title: "Check Your Knowledge"
  instruction: Choose the correct answer.
  items:  # minItems: 6
    - question: "Which letter looks like English H but represents the /n/ sound?"
      explanation: "Н is a visual trap — it looks like H but sounds like N."
      options:
        - text: "Н"
          correct: true
        - text: "М"
          correct: false
        - text: "С"
          correct: false
        - text: "Л"
          correct: false
```

Key: `explanation` at QUESTION level (not inside options), exactly 4 options, exactly 1 `correct: true`.

### anagram (letter scramble — M1-M10)

```yaml
- type: anagram
  title: "Unscramble the Word"
  instruction: "Rearrange the letters to form the correct Ukrainian word."
  items:  # minItems: 8
    - scrambled: "А М А М"    # SPACE-SEPARATED letters
      answer: "МАМА"
```

**CRITICAL**: Letters MUST be space-separated.

### match-up

```yaml
- type: match-up
  title: "Match Letter to Sound"
  pairs:  # minItems: 6 — MUST use "pairs:" not "items:"
    - left: "Н"
      right: "/n/ sound"
```

### fill-in (MUST include `options` array)

```yaml
- type: fill-in
  title: "Complete the Sentence"
  items:  # minItems: 6
    - sentence: "Мама купує ___."
      answer: "молоко"
      options: ["молоко", "молока", "молоку", "молоком"]
```

### group-sort

```yaml
- type: group-sort
  title: "Sort the Words"
  groups:  # 2-4 groups
    - name: "Masculine"
      items: ["стіл", "дім"]
    - name: "Feminine"
      items: ["книга", "мама"]
```

### true-false

```yaml
- type: true-false
  title: "True or False?"
  items:  # minItems: 8
    - statement: "The Ukrainian letter Н makes the same sound as English H."
      correct: false
      explanation: "Н looks like H but sounds like N — it's a visual trap."
```

### unjumble (sentence word reordering — ONLY when sentences allowed)

```yaml
- type: unjumble
  title: "Put the Words in Order"
  instruction: "Arrange the words to form a correct Ukrainian sentence."
  items:  # minItems: 8
    - words: ["книга", "Це", "нова"]
      answer: "Це нова книга"
```

**CRITICAL**: Use `words` (array of strings) + `answer` (string).

---

## Activity Quality Rules

1. **Every Ukrainian word must appear in the lesson content or prior modules.** Do NOT introduce new vocabulary.
2. **Integration focus.** Each activity should combine skills from different prior modules.
3. **Plausible, clear items.** Every question must have one unambiguous correct answer.
4. **No sentence-level activities** if constraints say letters/syllables only.
5. **Prefer fewer, high-quality integrative activities** over many single-skill drills.

## Mandatory Self-Check

1. **QUIZ single correct** — every quiz item has exactly 1 `correct: true`
2. **ANAGRAM letter match** — scrambled letters = same letters as answer
3. **MATCH-UP unique pairs** — no duplicate left or right values
4. **Schema compliance** — only fields from `{SCHEMA_PATH}`, no extras
5. **Integration check** — does each activity combine 2+ skills?

## Allowed Activity Types

**ALLOWED (use ONLY these):** {ALLOWED_ACTIVITY_TYPES}

**FORBIDDEN (audit will auto-FAIL):** {FORBIDDEN_ACTIVITY_TYPES}

{SHARED_ACTIVITY_RULES}
