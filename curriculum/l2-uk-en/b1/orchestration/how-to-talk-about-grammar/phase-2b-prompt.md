# Phase 2b: Content Expansion

> **You are Gemini, continuing Phase 2 of an orchestrated rebuild.**
> **The first content pass produced 2276 words. The target is 4000+. You must EXPAND every section.**

## Your Input

Read the current content (THIS IS YOUR BASE — expand it, don't rewrite):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/orchestration/how-to-talk-about-grammar/phase-2-content.md
```

Read the meta file (content_outline with word allocations):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/meta/how-to-talk-about-grammar.yaml
```

Read the research notes:
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/research/how-to-talk-about-grammar-research.md
```

## Problem

The content is well-structured (all H2/H3 present, good callouts), but EVERY section is too thin. Compare:

| Section | Current | Target | Deficit |
|---------|---------|--------|---------|
| Вступ: сила метамови | ~350 | 550 | -200 |
| Самостійні категорії | ~450 | 750 | -300 |
| Службові слова | ~350 | 600 | -250 |
| Відмінки: сім ключів | ~500 | 800 | -300 |
| Граматичні категорії | ~200 | 650 | -450 |
| Практика | ~200 | 400 | -200 |
| Підсумок | ~150 | 250 | -100 |

## Your Task

Produce the COMPLETE expanded module. Keep ALL existing structure (H2/H3 headings, callouts, examples, mermaid diagrams). For each section, ADD content to reach the target. Specifically:

### What to expand in each H3 concept block:

1. **Add more examples** — Each POS and each case needs 3-4 examples (current: 2). Use diverse contexts.
2. **Add usage notes** — After the examples, add 2-3 sentences about common collocations or real-world usage patterns.
3. **Add mini-dialogues** — Add at least 4 mini-dialogues across the module (teacher-student format) that use the terminology naturally.
4. **Deepen the Граматичні категорії section** — This is the thinnest section. Each grammatical category (рід, число, особа, час, вид) needs its own explanation paragraph, not just a bullet point.
5. **Expand Практика section** — Add 2 more authentic textbook excerpts for learners to read. Add reading comprehension questions.
6. **Add comparison callouts** — For tricky pairs (прийменник vs займенник, відмінок vs відміна), add dedicated `[!observe]` or `[!warning]` callouts.
7. **Cultural depth** — Weave in the Meletiy Smotrytsky reference more deeply. Connect to modern Ukrainian grammar education.

### Word targets (these are MINIMUMS, aim for 1.3x):

- Вступ: 700+ words
- Самостійні: 950+ words
- Службові: 780+ words
- Відмінки: 1050+ words
- Граматичні категорії: 850+ words
- Практика: 520+ words
- Підсумок: 325+ words
- **Total: 5200+ words**

### Rules

- Keep the EXACT same H2/H3 structure
- Keep ALL existing content — only ADD, never remove
- Keep all existing callouts and add new ones (target: 8+ total, 5+ different types)
- Keep all existing examples and add more (target: 30+ total)
- Add 4+ mini-dialogues using the terminology
- Maintain 75% Ukrainian immersion (English ONLY in intro)
- All new content in Ukrainian
- Use angular quotes «...»

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded.

Output the COMPLETE expanded module (not just the additions):

```
===CONTENT_START===
{Full module from <!-- SCOPE --> to the final ---}
===CONTENT_END===
```

Then word counts:
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
**Phase**: Phase 2b: Content Expansion
**Step**: {description}
**Friction Type**: NONE | TOKEN_LIMIT_TRUNCATION | ...
**Raw Error**: {or "None"}
**Self-Correction**: {or "N/A"}
**Proposed Tooling Fix**: {or "N/A"}
===FRICTION_END===
```
