# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **{MODULE_NUM}: {TOPIC_TITLE}** ({LEVEL}, {PHASE}).

**Target: {WORD_TARGET}–{WORD_CEILING} words** of prose (Ukrainian examples count toward word total, headings and exercise placeholders do not).

---

## 7 Hard Rules

1. **NO stress marks (´)** — do not add stress marks to any Ukrainian word. A deterministic tool adds them after you write.
2. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
3. **NO "In this lesson we will..."** — never use formulaic openers. Start with a dialogue, a question, or a situation.
4. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
5. **Exercise placeholders ONLY** — mark where exercises go using the format below, but do NOT write exercise content. A separate tool fills them.
6. **NO meta-commentary** — do NOT add "Content notes:", word count summaries, or self-audit sections at the end. Just write the module content and stop.
7. **Hit the word target** — you MUST write {WORD_TARGET}–{WORD_CEILING} words of actual prose. Count as you go. Short modules fail review. Expand explanations, add more examples, include more dialogues — never pad with filler.

## Exercise Placeholder Format

When you want an exercise, write a placeholder block. Be SPECIFIC about what the exercise should contain — include the actual questions, answers, and distractors. The more detail you provide, the better the exercise.

```
:::exercise-placeholder
type: quiz | fill-in | match-up | group-sort | true-false
tests: [what skill this exercise tests — be specific]
after: [what concept was just taught]
items: [number of items]
vocabulary: [comma-separated Ukrainian words to use as stems]
questions: [specific questions with answers, e.g. "Що ми чуємо? → звуки" or "В=? → [в] не [б]"]
groups: [for group-sort: group names and which items go where]
:::
```

**Good example:**
```
:::exercise-placeholder
type: group-sort
tests: classify letters as vowel or consonant
after: голосні vs приголосні explanation
items: 8
groups: Голосні: А, О, У, І; Приголосні: М, К, Б, Ш
:::
```

**Bad example (too vague):**
```
:::exercise-placeholder
type: quiz
tests: understanding
items: 5
:::
```

Place 4–6 exercise placeholders throughout the module, after key teaching points. Never cluster them — spread them evenly.

---

## Plan

{PLAN_CONTENT}

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

{KNOWLEDGE_PACKET}

---

## Section Structure

Write these sections as H2 headings, in this exact order:

{EXACT_SECTION_TITLES}

Each section should follow the word budget specified. The total must reach {WORD_TARGET} words minimum.

---

## Content Rules

{IMMERSION_RULE}

{LEVEL_CONSTRAINTS}

### Pedagogy
- Start each section with a real situation or dialogue (PPP: Present → Practice → Produce)
- Every grammar rule needs 3+ Ukrainian examples with English translations
- Teach through PATTERNS, not rules: show examples first, then name the pattern
- Cultural context where relevant — this is Ukrainian, not generic L2
- Use vocabulary from the plan's vocabulary_hints. Function words (pronouns, conjunctions) are always allowed.

### Ukrainian Language Quality
- **Zero Russian**: No ы, э, ё, ъ. No Russian words (кот→кіт, хорошо→добре, конечно→звичайно)
- **Zero Surzhyk**: No шо→що, чо→чому, тіпа→типу
- **Zero calques**: No приймати душ→брати душ, приймати рішення→ухвалювати рішення
- **Natural Ukrainian**: Write how a Ukrainian teacher would explain this to a student. Not robotic, not textbook-dry, not overly casual.

### Writing Quality
- Every paragraph: ONE clear point, logical flow to the next
- Vary sentence length (short for emphasis, medium for explanation, long for examples)
- Use callout boxes (:::tip, :::caution, :::note) sparingly — max 3 per module
- Dialogues: natural, not stilted. Real situations, real responses.

{PEDAGOGICAL_CONSTRAINTS}

### Vocabulary

{VOCABULARY_HINTS}

### Pronunciation Videos

{PRONUNCIATION_VIDEOS}

---

## Output Format

Write in Markdown. Use:
- `## Section Title` for main sections
- `### Subsection` for subsections within a section
- `**bold**` for Ukrainian words being taught
- Tables for paradigms (conjugation, declension)
- `:::tip` / `:::caution` / `:::note` for callout boxes
- `:::exercise-placeholder` for exercise locations

Do NOT write YAML, JSON, or MDX component syntax. Plain Markdown only.

Begin writing now. Start with the first section heading.
