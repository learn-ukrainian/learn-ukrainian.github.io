# Phase Fix-Content: Content Expansion + Engagement

> **You are Gemini, executing a targeted content fix.**
> **Your ONLY task: Expand the content to meet word count AND add engagement callouts.**

## Your Input

Read these files from disk:

**Current content** (the file you are fixing):
```
curriculum/l2-uk-en/b1/how-to-talk-about-grammar.md
```

**Plan file** (source of truth for scope):
```
curriculum/l2-uk-en/plans/b1/how-to-talk-about-grammar.yaml
```

**Research notes** (reference for factual accuracy):
```
curriculum/l2-uk-en/b1/research/how-to-talk-about-grammar-research.md
```

## Audit Failures to Fix

The content audit found these CRITICAL failures:

### 1. WORD COUNT: 3107 / 4000 (need +900 words minimum)

Section-by-section gaps:

| Section | Current | Floor | Gap |
|---------|---------|-------|-----|
| Вступ: сила метамови | 397 | 550 | -153 |
| Частини мови: самостійні категорії | 497 | 750 | -253 |
| Відмінки: сім ключів | 631 | 800 | -169 |
| Граматичні категорії та будова слова | 345 | 650 | -305 |
| Практика: читаємо граматику українською | 179 | 400 | -221 |
| Підсумок і самоперевірка | 151 | 250 | -99 |

**Priority expansion targets (biggest gaps):**
1. Граматичні категорії та будова слова (+305 needed)
2. Частини мови: самостійні категорії (+253 needed)
3. Практика (+221 needed)

### 2. ENGAGEMENT CALLOUTS: 0 / 4 minimum

The module has ZERO engagement callouts. Add at least 5, using at least 4 different types:
- `> [!tip]` — practical advice
- `> [!warning]` — common mistakes
- `> [!culture]` or `> [!history-bite]` — cultural hook
- `> [!quote]` — literary/cultural quote
- `> [!fact]` — interesting linguistic fact

**Format must be exactly:**
```markdown
> [!tip] Порада
> Текст поради українською мовою.
```

### 3. RICHNESS: 62% (need ≥90%)

Caused by missing engagement. Adding 5+ callouts will fix this.

## Your Task

1. Read the current content file completely
2. For each section below the floor: EXPAND the H3 subsections with more examples, usage notes, comparison tables, mini-dialogues. Aim for 150-200 words per H3.
3. Add 5-6 engagement callouts spread across sections (NOT all in one section)
4. Ensure the Підсумок has 6+ self-assessment questions
5. Output the COMPLETE fixed content file

### Rules

1. **Apply EVERY fix** — word expansion AND callouts
2. **Preserve structure** — keep the same H2/H3 headings
3. **Preserve voice** — maintain the warm, supportive tutor tone
4. **Do NOT add new H2 sections** — only expand existing ones
5. **Use ONLY vocabulary from the plan** — no new terms
6. **70% immersion** — Ukrainian first, English scaffolding in parentheses for new terms

## Output Format

**CRITICAL: Output the COMPLETE fixed content between these delimiter lines.**

```
===CONTENT_START===
(complete fixed content markdown — ALL of it, not just changed parts)
===CONTENT_END===
```

**After the content, report what you changed:**

```
===CHANGES_START===
## Applied Fixes

1. Section "{name}": {what changed, approximate words added}
2. Added [!type] callout in section "{name}": {topic}
...

## Word Count Estimate
Total: {estimate} words (was: 3107, target: 4000+)
===CHANGES_END===
```

## Boundaries

- Do NOT output activities or vocabulary sections
- Do NOT change the module's H2 structure
- Do NOT add vocabulary not in the plan
- Do NOT use straight quotes "..." — always «...»
