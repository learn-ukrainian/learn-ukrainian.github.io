# Phase 2 Fix #3: Final Section Expansion

> **You are Gemini. Two sections are under word target. Expand ONLY those two sections.**

## Current Content (READ FROM DISK)

```
curriculum/l2-uk-en/b1/how-to-talk-about-grammar.md
```

## Remaining Failures

Only 2 sections fail. Everything else passes.

| Section | Current | Target | Gap |
|---------|---------|--------|-----|
| Частини мови: самостійні категорії та їхні ролі | 532 | 750 | **-218** |
| Будова слова, граматичні категорії та синтаксис | 454 | 650 | **-196** |

Total gap: ~414 words needed across these two sections.

## Expansion Instructions

### Section 2: Частини мови: самостійні категорії (+218 words)

For EACH of the 6 H3 subsections (Іменник, Дієслово, Прикметник, Прислівник, Займенник, Числівник), add ~35 words:
- **Expand definitions** to 2+ full sentences (currently most are 1 sentence)
- **Add a usage note** after the examples explaining when/how this POS behaves distinctively in Ukrainian (e.g., "На відміну від англійської, український прикметник змінюється за відмінками, числами та родами, узгоджуючись із іменником")
- **Add 1 more example** to any H3 that only has 2

### Section 5: Будова слова, граматичні категорії та синтаксис (+196 words)

**Морфеміка** (+70 words):
- Add a concrete word decomposition table for 2-3 words showing корінь, префікс, суфікс, закінчення, основа
- Example: `під-руч-ник-∅` → prefix=під, root=руч, suffix=ник, ending=нульове

**Граматичні категорії** (+70 words):
- Add 1 example sentence per category (6 categories = 6 sentences)
- Format: «Рід: слово *книга* — жіночий рід, *стіл* — чоловічий рід, *вікно* — середній рід.»

**Синтаксичні ролі** (+56 words):
- Add a fully parsed example sentence where each word is labeled with its syntactic role
- Example: «**Талановитий** (означення) **вчитель** (підмет) **чітко** (обставина) **пояснив** (присудок) **правило** (додаток).»

### Also fix: Content Redundancy

The audit flagged a redundant answer block (71% overlap). Find the section with "(Відповідь: 1 — дієслово, 2 — займенник...)" that overlaps with another section and either remove the duplicate or significantly rephrase it.

## Output Format

Return the COMPLETE content (ALL sections, not just the changed ones):

```
===CONTENT_START===
{full content}
===CONTENT_END===
```

## Boundaries

- Do NOT change sections that already pass (Вступ, Службові, Відмінки, Практика, Підсумок)
- Do NOT remove content — only EXPAND the two failing sections
- Do NOT change H2/H3 structure
- Fix the redundancy issue
