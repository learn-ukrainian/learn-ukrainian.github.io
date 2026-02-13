# Phase 2: Content Writing

> **You are Gemini, executing Phase 2 of an orchestrated rebuild.**
> **Your ONLY task: Write the lesson prose. Overshoot to 1.5x the word target.**

## Your Input

Read these files from disk:

**Research notes** (your factual foundation — use exhaustively):
```
curriculum/l2-uk-en/b1/orchestration/how-to-talk-about-grammar/phase-0-research.md
```

**Meta file** (content_outline with word allocations):
```
curriculum/l2-uk-en/b1/meta/how-to-talk-about-grammar.yaml
```

**Plan file** (objectives, vocabulary_hints — use ONLY these words):
```
curriculum/l2-uk-en/plans/b1/how-to-talk-about-grammar.yaml
```

**Level quick-ref** (constraints, immersion %, engagement minimums):
```
claude_extensions/quick-ref/b1.md
```

**Archive diff report** (CRITICAL — what was lost in the previous rebuild, MUST be included):
```
curriculum/l2-uk-en/b1/orchestration/how-to-talk-about-grammar/archive-diff.md
```

## Your Task

Write the full lesson prose for **Як говорити про граматику** (B1 track, word target: 4000).

### Critical Rules

1. **OVERSHOOT**: Write to **1.5x the word_target** (6000 words). Trimming is cheap; expanding is expensive.
2. **Section-by-section**: Follow `content_outline` exactly. Every section must appear as an H2 heading.
3. **Research-driven**: Use research notes exhaustively. Every fact, date, quote, and source should appear in the prose.
4. **Vocabulary discipline**: Use ONLY vocabulary from the plan's `vocabulary_hints`. Do NOT invent new terms.
5. **Engagement boxes**: Include 14+ engagement callouts (`[!tip]`, `[!myth-buster]`, `[!quote]`, `[!history-bite]`, `[!context]`, `[!decolonization]`, `[!culture]`, `[!warning]`, `[!observe]`, `[!analysis]`).
6. **Example sentences**: Include 24+ example sentences formatted as `_Приклад:_ «...»`
7. **Immersion**: Bridge module — immersion 65%. Ukrainian term FIRST, English equivalent in parentheses on first introduction ONLY. Max 1 English paragraph in the introduction. English in callouts allowed for abstract concepts. After first introduction → Ukrainian exclusively.
8. **Ukrainian quotes**: Use angular quotes `«...»`, not straight quotes
9. **No frontmatter**: Content starts with `<!-- SCOPE ... -->` comment, then `# Title`
10. **Visual aids**: Use tables and mermaid flowcharts when they clarify better than prose.

### ARCHIVE DIFF REQUIREMENTS (MANDATORY)

The previous rebuild lost these elements. You MUST include ALL of them:

1. **Case mnemonic**: На Різдво Дід Загубив Орішки Між Ковбасками — prominent, with letter-by-letter mapping
2. **Deverbal instruction keywords**: Означає, Вказує на, Вживається з, Змінюється за, Виконує роль, Належить до — in the Practice section
3. **Introduction H3 sub-structure**: "Психологічна перевага" + "Традиції та логіка мовознавства"
4. **Section 5 MUST have 3 separate H3**: Морфеміка, Граматичні категорії, Синтаксичні ролі
5. **Myth-buster callout**: Ukrainian POS are NOT copies of English — unique aspect category
6. **Metacognitive study advice**: Learning grammar = learning academic register simultaneously
7. **Teacher-student dialogues**: 3+ dialogues woven into content
8. **відмінок vs відміна clarification**: Clear distinction with analogy
9. **Cultural anchoring**: Shevchenko vocative, Lesya Ukrainka tense, Franko quote — in Practice section
10. **Mermaid diagrams**: At least 2 flowcharts (POS taxonomy, case taxonomy)

### Pedagogical Visual Aids

**Tables** — Use for: POS summaries, case function summaries.
**Mermaid flowcharts** — Use for: POS classification, case taxonomy.

### Anti-Patterns (DO NOT)

- **Robotic transitions**: "Тепер розглянемо...", "Далі ми побачимо..."
- **Russianisms**: кушати→їсти, приймати участь→брати участь, слідуючий→наступний
- **Calques**: робити сенс→мати сенс, брати місце→відбуватися
- **Template repetition**: Don't start 3+ sentences the same way
- **Dry exposition**: Use storytelling, not textbook listing

### Pedagogical Excellence Standards (MANDATORY)

1. **Simple → Complex** — Start with simplest, build to complex.
2. **Concept Before Use** — Every term explained BEFORE appearing in examples.
3. **Contextualized Grammar** — Every rule connects to real communication.
4. **Active Learning Prompts** — `[!tip] Спробуйте самі` or `[!observe]` in every major section.
5. **Mnemonic Aids** — Memory aids for complex patterns.
6. **Cultural Anchoring** — 2-3 grammar points linked to Ukrainian culture.
7. **Error Prevention** — Common mistakes with `[!warning]` callouts.

### Presentation Standards (MANDATORY)

8. **Consistency** — N items in category → SAME format, SAME depth (±20%).
9. **Equal Treatment** — No item as afterthought.
10. **Parallel Structure** — Matching sections use identical internal pattern.
11. **Each Concept = Own H3** — EVERY item in a category gets its own `### H3`.
12. **Depth Per Concept** — definition (2+ sentences) + question + 2+ examples + usage note. ~80-100 words min.
13. **Section Title Language** — Ukrainian H2/H3 titles.
14. **Callout Type Variety** — At least 6 DIFFERENT callout types.
15. **Self-Check Questions** — 10 in Підсумок.

### Pre-Output Checklist

1. ☐ Every section from `content_outline` appears as H2/H3
2. ☐ Total word count >= 4000 (overshoot to 6000)
3. ☐ 14+ engagement callouts spread across sections
4. ☐ 24+ example sentences in varied formats
5. ☐ Each concept = own H3
6. ☐ Section 5 has 3 H3 subsections
7. ☐ Mnemonic with letter mapping
8. ☐ Deverbal keywords in Practice section
9. ☐ 10 self-check questions
10. ☐ All 10 archive diff elements present

### Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded.

```
===CONTENT_START===

<!-- SCOPE
Covers: Ukrainian grammar terminology — parts of speech, cases, grammatical categories, syntactic roles
Not covered:
  - Verb-specific terminology → 02-language-about-verbs
  - Reading grammar rules → 03-reading-grammar-rules
Related: b1-02, b1-03, b1-05
-->

# Як говорити про граматику

> **Чому це важливо?**
>
> {2-3 sentences of significance}

## {Section 1 from content_outline}
...
## {Section 2}
...
---
## Підсумок: перевірка метамовної готовності
...
---

===CONTENT_END===
```

After content, report word counts:

```
===WORD_COUNTS===
Section "{name}": {count} words (target: {allocation})
...
Total: {total} words (target: 4000, ratio: {total/4000}x)
===WORD_COUNTS===
```

## Friction Report (MANDATORY)

```
===FRICTION_START===
**Phase**: Phase 2: Content
**Step**: {what}
**Friction Type**: NONE | ...
**Raw Error**: {or "None"}
**Self-Correction**: {or "N/A"}
**Proposed Tooling Fix**: {or "N/A"}
===FRICTION_END===
```

## Boundaries

- Do NOT generate activities, exercises, or vocabulary tables — Phase 3
- Do NOT add vocabulary outside the plan's vocabulary_hints
- Do NOT skip sections from the content_outline
- Do NOT write fewer than 4000 words total
