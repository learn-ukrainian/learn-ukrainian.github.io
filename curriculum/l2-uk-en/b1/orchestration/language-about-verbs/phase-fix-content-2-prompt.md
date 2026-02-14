# Phase 2 Fix: Targeted Expansion (Attempt 2)

> **You are Gemini, expanding specific sections that failed the word count audit.**

## Problem

The content for **Мова про дієслова** is 3588 effective words — needs 4000 minimum. Four sections are short:

| Section | Current | Target | Gap |
|---------|---------|--------|-----|
| Час дієслова: Граматична подорож | 522 | 616 | -94 |
| Форми дієслова: Синтетична та складена | 421 | 513 | -92 |
| Читання граматичних пояснень | 330 | 411 | -81 |
| Міні-діалоги: Обговорення граматики | 388 | 513 | -125 |

**Total gap: ~530 words. You need to add at least 600 words across these 4 sections.**

## Files to Read

```
curriculum/l2-uk-en/b1/language-about-verbs.md
curriculum/l2-uk-en/b1/meta/language-about-verbs.yaml
curriculum/l2-uk-en/b1/research/language-about-verbs-research.md
```

## Expansion Instructions

For EACH of the 4 sections, add content using these strategies:

**Section 4 (Час дієслова) — add 150+ words:**
- Add a table comparing all 3 tenses with example sentences for НДВ and ДВ
- Expand the cultural hook about past tense gaining gender with more examples

**Section 7 (Форми дієслова) — add 150+ words:**
- Add a comparison table: синтетична (писатиму, читатиму, ходитиму) vs складена (буду писати, буду читати, буду ходити)
- Add a `> [!tip]` about recognizing forms

**Section 8 (Читання граматичних пояснень) — add 150+ words:**
- Add a second grammar text for analysis (a textbook rule about aspect in negation)
- Add step-by-step annotation of the text using learned terms

**Section 9 (Міні-діалоги) — add 200+ words:**
- Add 2 more dialogues: one student asking teacher about homework, one study-buddy pair discussing an error

## Output

Return the COMPLETE file content with expansions applied:

```
===CONTENT_START===
{ENTIRE module — all sections, expanded where needed}
===CONTENT_END===
```

## Rules

- Keep ALL existing content, callouts, examples
- Do NOT change H2 section names
- Use `> [!type]` format for any new callouts
- Use «...» for Ukrainian quotes in content (not in YAML)
- Immersion: 70% Ukrainian
- Target: 4600+ raw words (for 4000+ effective)
