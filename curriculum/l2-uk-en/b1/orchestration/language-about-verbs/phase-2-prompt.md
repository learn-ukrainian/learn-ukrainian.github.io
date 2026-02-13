# Phase 2: Content Writing

> **You are Gemini, executing Phase 2 of an orchestrated rebuild.**
> **Your ONLY task: Write the lesson prose. Overshoot to 1.5x the word target.**

## Your Input

Read these files from disk:

**Research notes** (your factual foundation — use exhaustively):
```
curriculum/l2-uk-en/b1/research/language-about-verbs-research.md
```

**Meta file** (content_outline with word allocations):
```
curriculum/l2-uk-en/b1/meta/language-about-verbs.yaml
```

**Plan file** (objectives, vocabulary_hints — use ONLY these words):
```
curriculum/l2-uk-en/plans/b1/language-about-verbs.yaml
```

**Level quick-ref** (constraints, immersion %, engagement minimums):
```
claude_extensions/quick-ref/b1.md
```

## Your Task

Write the full lesson prose for **Мова про дієслова** (b1 track, word target: 3000).

### Critical Rules

1. **OVERSHOOT**: Write to **1.5x the word_target** (4500 words). Trimming is cheap; expanding is expensive.
2. **Section-by-section**: Follow `content_outline` exactly. Every section must appear as an H2 heading.
3. **Research-driven**: Use research notes exhaustively. Every fact, date, quote, and source should appear in the prose.
4. **Vocabulary discipline**: Use ONLY vocabulary from the plan's `vocabulary_hints`. Do NOT invent new terms.
5. **Engagement boxes**: Include 5+ engagement callouts (`[!tip]`, `[!myth-buster]`, `[!quote]`, `[!history-bite]`, `[!context]`, `[!decolonization]`, `[!culture]`, `[!warning]`).
6. **Example sentences**: Include 24+ example sentences formatted as `_Приклад:_ «...»`
7. **Immersion**: 75% Ukrainian. This is a bridge module (B1 M02). Ukrainian terms FIRST, English equivalents in parentheses on FIRST introduction only. After first introduction, Ukrainian exclusively. No English paragraphs except a brief one in the intro explaining why this matters.
8. **Ukrainian quotes**: Use angular quotes `«...»`, not straight quotes
9. **No frontmatter**: Content starts with `<!-- SCOPE ... -->` comment, then `# Title`
10. **Visual aids**: Use tables for comparing patterns (aspect vs tense, verb forms). Use mermaid flowcharts for decision logic. Don't force them — use when pedagogically reasonable.
11. **Mini-dialogues**: Include 4+ mini-dialogues showing the terminology in teacher-student or student-student conversations.

### Pedagogical Excellence Standards (MANDATORY)

1. **Simple → Complex Progression** — Within each section, start with the simplest form/usage, then build to complex.
2. **Concept Before Use** — Every grammatical term must be explicitly explained BEFORE it appears in examples.
3. **Contextualized Grammar** — Grammar is a tool, not a list. Every rule must connect to real communication.
4. **Active Learning Prompts** — Every major section must include at least one moment where the learner pauses to think. Use callouts like `[!tip] Спробуйте самі`, `[!context] Подумайте`.
5. **Mnemonic Aids** — For complex patterns, provide memory aids: visual patterns, rhymes, analogies.
6. **Cultural Anchoring** — Connect 2-3 grammar points to Ukrainian cultural context.
7. **Error Prevention** — Anticipate common learner mistakes, include `[!warning]` callouts.

### Presentation Quality Standards (MANDATORY)

8. **Presentation Consistency** — When explaining N items in a category: SAME format, SAME depth (±20%), SAME example count (±1).
9. **Equal Treatment** — No category item as afterthought. Each gets proportional depth.
10. **Parallel Structure** — Matching sections use identical internal pattern.
11. **English Scaffolding** — 75% immersion: Ukrainian term FIRST, English in parentheses on first intro only. After that Ukrainian exclusively. English in tip/note callouts for tricky abstract concepts. No inline English in prose.
12. **Section Title Language** — All H2/H3 titles in Ukrainian (except brief English in callouts).
13. **Example Variety** — FORBIDDEN: 5+ consecutive `_Приклад:_`. Mix formats.
14. **Callout Type Variety** — Use at least 4 DIFFERENT callout types.
15. **Self-Check Questions** — Підсумок section must include 4-6 self-assessment questions.

### Section Word Buffer

The audit counts ~100-150 fewer words than raw `wc -w` due to excluding blockquote/callout markup. For a section with 600-word allocation, write 700-750 raw words.

### Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

Return the full lesson content as markdown:

```
===CONTENT_START===

<!-- SCOPE
Covers: Verb-specific Ukrainian metalanguage (aspect, tense, negation, moods, forms)
Not covered:
  - Aspect usage rules → b1-06
  - Reading grammar rules → b1-03
Related: b1-01 (basic grammar terms), b1-03 (reading grammar rules), b1-06 (aspect system)
-->

# Мова про дієслова

> **Чому це важливо?**
>
> {2-3 sentences of significance}

## {Section 1 from content_outline}

{Content: aim for 1.5x the section word allocation}

{Engagement boxes woven in naturally}

## {Section 2}

{Content...}

...

---

# Підсумок

{3-4 paragraph summary, ~150-200 words, including 4-6 self-check questions}

---

===CONTENT_END===
```

After the content block, report word counts:

```
===WORD_COUNTS===
Section "{name}": {count} words (target: {allocation})
...
Total: {total} words (target: 3000, ratio: {total/3000}x)
===WORD_COUNTS===
```

## Friction Report (MANDATORY)

After your content and word counts, output a friction report:

```
===FRICTION_START===
**Phase**: Phase 2: Content
**Step**: {what you were doing when friction occurred, or "Full content generation"}
**Friction Type**: YAML_SCHEMA_VIOLATION | TOKEN_LIMIT_TRUNCATION | TOOL_REDUNDANCY | NONE
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed to work around it, or "N/A"}
**Proposed Tooling Fix**: {if the friction is a script/design issue, or "N/A"}
===FRICTION_END===
```

## Boundaries

- Do NOT generate activities, exercises, or vocabulary tables — those are Phase 3
- Do NOT add vocabulary outside the plan's vocabulary_hints
- Do NOT skip sections from the content_outline
- Do NOT write fewer than 3000 words total
- Do NOT request skills or delegate to Claude
