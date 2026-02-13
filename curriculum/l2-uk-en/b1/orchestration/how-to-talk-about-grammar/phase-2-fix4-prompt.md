# Phase 2 Fix #4: Expand Section 2 ONLY

> **You are Gemini. ONE section is under word target. Expand ONLY that section.**

## Current Content (READ FROM DISK)

```
curriculum/l2-uk-en/b1/how-to-talk-about-grammar.md
```

## The Problem

**Section "Частини мови: самостійні категорії та їхні ролі"** has 532 words. Target is 750. Gap: -218 words.

This section has 6 H3 subsections: Іменник, Дієслово, Прикметник, Прислівник, Займенник, Числівник. Each needs approximately +36 words.

## EXACT Expansion Per H3

For EACH of the 6 H3 subsections, do ALL of the following:

1. **Expand the definition** from 1 sentence to 2-3 sentences. Add detail about how this POS behaves in Ukrainian specifically.
2. **Add a usage note** after the examples: a brief paragraph (2-3 sentences) explaining distinctive Ukrainian features or common patterns.
3. **Add 1 more example sentence** in `_Приклад:_` format if the H3 has only 2 examples.

### Example of what to add to Іменник (noun):

Before your expansion it might read:
```
Іменник (noun) — це самостійна частина мови, що означає предмет і відповідає на питання «хто?» або «що?».
```

After expansion (~80-100 words total for the H3):
```
Іменник (noun) — це самостійна частина мови, що означає предмет і відповідає на питання «хто?» або «що?». Іменники поділяються на власні (назви конкретних осіб, міст: Тарас, Київ) та загальні (назви класів предметів: книга, дерево). В українській мові іменник має три роди — чоловічий, жіночий і середній — та змінюється за числами і відмінками.

[existing bullets and examples]

> **Примітка щодо вживання**: Іменник — найчастотніша частина мови в тексті. Він може виконувати будь-яку синтаксичну роль у реченні, але найчастіше виступає підметом або додатком.
```

Do this for ALL 6 H3 subsections. The total expansion should add ~218+ words to Section 2.

## Output Format

Return the COMPLETE content:

```
===CONTENT_START===
{full content — ALL sections, not just Section 2}
===CONTENT_END===
```

## Boundaries

- ONLY expand Section 2 (Частини мови: самостійні категорії та їхні ролі)
- Do NOT touch any other section
- Do NOT change the H2/H3 structure
- Do NOT remove existing content
