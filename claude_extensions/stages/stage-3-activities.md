# Stage 3: Activities

Generate activities based on the content created in Stage 2.

## Input

- **Module file**: Contains complete content from Stage 2
- **Level**: Determines activity types and counts

## Activity Count Requirements

| Level | Count | Items per Activity | Types |
|-------|-------|-------------------|-------|
| A1 | 8+ | 12+ | 4+ |
| A2 | 10+ | 12+ | 5+ |
| B1 | 12+ | 14+ | 5+ |
| B2 | 14+ | 16+ | 5+ |
| C1 | 16+ | 18+ | 5+ |
| C2 | 16+ | 18+ | 5+ |

## Activity Matrix by Level

| Activity | A1 | A2 | B1 | B2 | C1 | C2 |
|----------|----|----|----|----|----|----|
| fill-in | 2+ | 2+ | 2+ | 3+ | 2+ | 2+ |
| match-up | 2+ | 1+ | 1+ | 1+ | 1+ | 1+ |
| quiz | 1+ | 1+ | 1+ | 1+ | 1+ | 1+ |
| true-false | 1+ | 1+ | 1+ | 1+ | - | - |
| group-sort | 1+ | 1+ | 1+ | 1+ | 1+ | 1+ |
| anagram | 2+ (M01-10) | - | - | - | - | - |
| unjumble | 2+ (M11+) | 2+ | 2+ | 2+ | 2+ | 2+ |
| error-correction | - | 1+ | 2+ | 2+ | 3+ | 3+ |
| cloze | - | 1+ | 1+ | 1+ | 3+ | 3+ |
| mark-the-words | - | 1+ | 1+ | 1+ | - | - |
| dialogue-reorder | - | 1+ | 1+ | 1+ | 1+ | - |
| select | - | opt | 1+ | 1+ | 1+ | 1+ |
| translate | - | opt | 1+ | 1+ | 2+ | 2+ |

## Activity Sequencing

Flow: Easy → Medium → Hard

### A1
```
match-up → group-sort → quiz → true-false → fill-in → anagram/unjumble
```

### A2-B1
```
[recognition] mark-the-words → match-up → group-sort
[discrimination] quiz → true-false → select
[controlled] fill-in → cloze → error-correction
[production] unjumble → dialogue-reorder → translate
```

### B2-C2
```
[discrimination] select (nuanced)
[controlled] fill-in → cloze → error-correction ×2-3
[production] translate → unjumble ×2-3
```

## Syntax Reference

### Fill-in (CRITICAL)
```markdown
## fill-in: Title

___ я завжди читаю книгу.

> [!options]
> - Вранці
> - Книгу
> - Столом

> [!answer]
> Вранці
```

- Placeholder: EXACTLY `___` (three underscores)
- NO hints in parentheses
- Options and answer blocks MANDATORY

### Match-up
```markdown
## match-up: Title

- книга :: book
- стіл :: table
- вікно :: window
```

### Unjumble
```markdown
## unjumble: Title

я / завжди / читаю / книгу / вранці

> [!answer]
> Я завжди читаю книгу вранці.
```

- Separator: SLASHES with spaces ` / `
- Minimum 5-8 words per sentence

### Anagram (A1 M01-10 only)
```markdown
## anagram: Title

К Н И Г А

> [!answer]
> книга
```

- Separator: SPACES (not slashes)

### Cloze
```markdown
## cloze: Title

Марія ___(1)___ до магазину. Вона ___(2)___ хліб.

> [!options]
> 1: йде, їде, біжить
> 2: купує, продає, готує

> [!answer]
> 1: йде
> 2: купує
```

### Quiz (MUST be numbered)
```markdown
## quiz: Title

1. Яке слово означає "book"?
   - [ ] стіл
   - [x] книга
   - [ ] вікно
   > книга = book

2. Яке слово означає "table"?
   - [x] стіл
   - [ ] книга
   - [ ] вікно
   > стіл = table
```

- **Questions MUST be numbered** (1., 2., 3., etc.)
- Each question needs explanation after options

### Error-correction (A2+ REQUIRED FORMAT)
```markdown
## error-correction: Title

1. Я читаю книгу на стіл.
   > [!error] стіл
   > [!answer] столі
   > [!options] стіл | столі | столу | столом
   > [!explanation] Locative case required after "на" for location. стіл → столі.

2. Вона читав книгу вчора.
   > [!error] читав
   > [!answer] читала
   > [!options] читав | читала | читало | читали
   > [!explanation] Past tense agrees with subject gender. Feminine subject → -ла ending.
```

- **MUST include all 4 callouts**: `[!error]`, `[!answer]`, `[!options]`, `[!explanation]`
- `[!explanation]` tells learners WHY - without it, audit fails

### Group-sort
```markdown
## group-sort: Title

Masculine :: стіл, олівець, зошит
Feminine :: книга, ручка, лампа
Neuter :: вікно, місто, море
```

## Vocabulary Constraint (CRITICAL)

Activities MUST use ONLY:
1. Words from the current module's vocabulary table
2. Words from prior modules (cumulative vocabulary)
3. Common function words (я, ти, він, це, і, а, але, etc.)

NEVER use words not taught yet.

## Validation Before Completing

- [ ] Activity count meets level requirement
- [ ] Items per activity meets minimum
- [ ] Activity variety (4-5+ types)
- [ ] Proper sequencing (easy → hard)
- [ ] Correct syntax (see reference above)
- [ ] Fill-in uses `___` placeholder
- [ ] Unjumble uses ` / ` separator
- [ ] Anagram uses spaces (A1 M01-10 only)
- [ ] All answers are correct
- [ ] Uses ONLY vocabulary from table + prior modules
- [ ] **Quiz questions are numbered** (1., 2., 3., etc.)
- [ ] **Error-correction has all 4 callouts** (A2+): `[!error]`, `[!answer]`, `[!options]`, `[!explanation]`

## DO NOT

- Use vocabulary not in table or prior modules
- Write fewer than required activities
- Use wrong separators (slashes in anagram, spaces in unjumble)
- Skip options/answer blocks in fill-in
- Create activities with fewer than 12 items (A1-A2) or 14+ (B1+)
