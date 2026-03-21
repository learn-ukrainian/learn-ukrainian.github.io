# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **{MODULE_NUM}: {TOPIC_TITLE}** ({LEVEL}, {PHASE}).

**Target: {WORD_TARGET}–{WORD_CEILING} words** of prose (Ukrainian examples count toward word total, headings and exercise placeholders do not).

---

## 6 Hard Rules

1. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
2. **NO "In this lesson we will..."** — never use formulaic openers. Start with a dialogue, a question, or a situation.
3. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
4. **Exercise placeholders** — mark where exercises go using the format below. Write the specific questions, answers, vocabulary, and distractors INSIDE the placeholder block. A downstream tool converts them to interactive components.
5. **NO meta-commentary** — do NOT add "Content notes:", word count summaries, or self-audit sections at the end. Just write the module content and stop.
6. **Hit the word target** — you MUST write {WORD_TARGET}–{WORD_CEILING} words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.

**Note:** Do NOT add stress marks (´) to any Ukrainian word — a deterministic tool handles this after you write.

## Exercise Placeholder Format

After each key teaching point, write an exercise placeholder. Base your placeholders on the `activity_hints` in the Plan below — each hint should become one placeholder.

Be SPECIFIC — include the actual questions, answers, and distractors. The more detail you provide, the better the exercise.

```
:::exercise-placeholder
type: quiz | fill-in | match-up | group-sort | true-false
tests: [what skill this exercise tests — be specific]
after: [what concept was just taught]
items: [number of items]
vocabulary: [comma-separated Ukrainian words to use as stems]
questions: [specific questions with answers, e.g. "Що ми чуємо? → звуки" or "В=v, Н=n, Р=r"]
groups: [for group-sort: group names and which items go where, e.g. "Голосні: А, О, У; Приголосні: М, К, Б"]
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

**Bad example (too vague — the downstream tool cannot generate real content from this):**
```
:::exercise-placeholder
type: quiz
tests: understanding
items: 5
:::
```

Spread placeholders evenly throughout the module. Never cluster them.

---

## Plan

<plan_content>
{PLAN_CONTENT}
</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
{KNOWLEDGE_PACKET}
</knowledge_packet>

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
- **Tone:** Authoritative but warm. Like a skilled Ukrainian teacher — confident, clear, culturally grounded. Avoid generic LLM cheerfulness ("Good news!", "Don't panic!", "Fun fact!"). Let the content be interesting on its own.
- **Never guess about Ukrainian.** If you are unsure about a word, grammatical form, or phonetic rule — flag it with `<!-- VERIFY: word/claim -->`. Never invent or describe vaguely to hide uncertainty.

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
- `:::exercise-placeholder` for exercise locations (using the key-value format above)

Do NOT write MDX component syntax, YAML frontmatter, or JSON. Plain Markdown with the exercise placeholder blocks described above.

Begin writing now. Start with the first section heading.
