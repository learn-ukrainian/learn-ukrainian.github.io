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
> [!IMPORTANT]
> **Single Source of Truth:**
>
> You MUST follow the strict markdown syntax defined in:
> `docs/MARKDOWN-FORMAT.md`
>
> Read that file to see the correct format for:
> - `match-up` (Markdown Table)
> - `fill-in` (Block format)
> - `quiz` (Numbered list)
> - `translate` (Checkbox format)
> - `select` (Checkbox format)
> - `error-correction` (4-callout block)
> - `group-sort` (Category headers)
>
> Do NOT invent new formats. Do NOT use `::` for match-up.
>
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
- [ ] **Correct syntax validated against `docs/MARKDOWN-FORMAT.md`**
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

