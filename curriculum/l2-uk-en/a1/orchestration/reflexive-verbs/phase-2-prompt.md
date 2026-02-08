# Phase 2: Content Writing

> **You are Gemini, executing Phase 2 of an orchestrated rebuild.**
> **Your ONLY task: Write the lesson prose. Overshoot to 1.5x the word target.**

## Your Input

Read these files from disk:

**Research notes** (your factual foundation — use exhaustively):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/reflexive-verbs-research.md
```

**Meta file** (content_outline with word allocations):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/meta/09-reflexive-verbs.yaml
```

**Plan file** (objectives, vocabulary_hints — use ONLY these words):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/09-reflexive-verbs.yaml
```

**Level quick-ref** (constraints, immersion %, engagement minimums):
```
/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md
```

## Your Task

Write the full lesson prose for **Reflexive Verbs (-ся)** (A1 core track, word target: 750).

### Critical Rules

1. **OVERSHOOT**: Write to **1.5x the word_target** (1125 words). Trimming is cheap; expanding is expensive.
2. **Section-by-section**: Follow `content_outline` exactly. Four sections: Warm-up (142w), Presentation (412w), Practice (126w), Cultural Insight (70w).
3. **Research-driven**: Use research notes exhaustively. State Standard §2.2.3, pronunciation [ц':а], vocabulary frequency data, common errors, cultural hooks.
4. **Vocabulary discipline**: Use ONLY vocabulary from the plan's `vocabulary_hints` (required: вмиватися, одягатися, дивитися, сміятися, називатися, вчитися, займатися, повертатися; recommended: голитися, зупинятися, знайомитися, цікавитися).
5. **Engagement boxes**: Include 3+ engagement callouts (`[!tip]`, `[!warning]`, `[!culture]`).
6. **Example sentences**: Include 12+ example sentences formatted as `_Example:_ «...»` or inline Ukrainian.
7. **Mini-dialogues**: Include 2+ mini-dialogues.
8. **Immersion**: A1 M06-10 range: 15-25% Ukrainian. Heavy English for explanations, Ukrainian for examples.
9. **Transliteration**: Full transliteration for this module range (M01-10): слово (slovo).
10. **No frontmatter**: Content starts with `<!-- SCOPE ... -->` comment, then `# Title`.
11. **Pedagogy**: PPP (Presentation-Practice-Production).
12. **Structure**: Use ## for sections: Warm-up, Presentation, Practice, Cultural Insight, then # Підсумок.

### Anti-Patterns (DO NOT)

- **Robotic transitions**: "Now let's look at...", "Next we will see..." — use natural connectors
- **Template repetition**: Don't start 3+ sentences the same way
- **Dry exposition**: Use storytelling, scenarios, real-life anchors
- **Fact duplication**: Each fact appears in ONE section only

### Section Word Buffer

The audit counts ~100-150 fewer words than raw `wc -w` due to excluding blockquote/callout markup. For the Presentation section (412w allocation), write 500+ raw words.

## Output Format

Return the full lesson content as markdown:

```
===CONTENT_START===

<!-- SCOPE
Covers: Reflexive verbs (-ся/-сь), conjugation patterns, three types (true reflexive, reciprocal, lexicalized)
Not covered:
  - Past tense reflexive forms → future module
  - Imperative reflexive forms → future module
Related: the-living-verb-ii, checkpoint-first-contact, my-daily-routine
-->

# Reflexive Verbs (-ся)

## Warm-up

{~200 raw words: Hook explaining what -ся does, why it matters, daily life connection}

## Presentation

{~600 raw words: -ся vs -сь rules, conjugation table, three types with examples, irregularities}

## Practice

{~200 raw words: Mini-dialogues, practice scenarios}

## Cultural Insight

{~100 raw words: Cultural fact about Ukrainian daily life or language}

---

# Підсумок

{Summary: ~50-100 words}

---

===CONTENT_END===
```

After the content block, report word counts:

```
===WORD_COUNTS===
Section "Warm-up": {count} words (target: 142)
Section "Presentation": {count} words (target: 412)
Section "Practice": {count} words (target: 126)
Section "Cultural Insight": {count} words (target: 70)
Total: {total} words (target: 750, ratio: {total/750}x)
===WORD_COUNTS===
```

## Boundaries

- Do NOT generate activities, exercises, or vocabulary tables — those are Phase 3
- Do NOT add vocabulary outside the plan's vocabulary_hints
- Do NOT skip sections from the content_outline
- Do NOT write fewer than 750 words total
- Do NOT request skills or delegate to Claude
