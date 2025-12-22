# B2 Improvement Plan

**Status:** Ready for Implementation
**Updated:** 2025-12-22
**Modules:** 135

---

## Current State

| Metric | Value |
|--------|-------|
| Total Modules | 135 |
| Built | 0 |
| Remaining | 135 |
| Immersion | 100% (full Ukrainian) |

---

## Key Parameters

### Immersion: 100%

All B2 modules use full immersion. English appears ONLY in:
- Vocabulary table translations

All instructions, explanations, content body, and activity feedback are in Ukrainian. Students learned all grammatical terminology at B1 and can understand metalinguistic explanations in Ukrainian.

### Module Structure (135 modules)

| Phase | Modules | Content |
|-------|---------|---------|
| B2.1a | M01-30 | Grammar & Register |
| B2.1b | M31-40 | Grammar Completion (Numerals, Word Formation) |
| B2.2 | M41-70 | Phraseology & Synonymy |
| B2.3 | M71-95 | Ukrainian History |
| B2.4 | M96-120 | Biographies |
| B2.5 | M121-135 | Advanced Skills & Capstone |

### Activity Requirements

| Module Type | Min Activities | Notes |
|-------------|----------------|-------|
| Grammar (M01-40) | 14 | Complex, needs more practice |
| Vocabulary (M41-70) | 12 | Synonym/nuance focused |
| History (M71-95) | 10-12 | Reading comprehension focused |
| Biography (M96-120) | 10-12 | Narrative focused |
| Checkpoint | 15 | Comprehensive review |
| Capstone | 12 | Project-based |

### Vocabulary

- Target: ~2,900 new words (level)
- Cumulative: ~6,200 words (A1+A2+B1+B2)
- Per module: 20-25 words average

---

## Checkpoints

| Module | Checkpoint | Covers |
|--------|-----------|--------|
| M30 | Grammar Checkpoint | Passive, participles, syntax (M01-29) |
| M40 | Grammar Completion Check | Numerals, word formation (M31-39) |
| M70 | Phraseology Checkpoint | Idioms, proverbs, synonyms (M41-69) |
| M95 | History Checkpoint | Ukrainian history (M71-94) |
| M120 | Biography Checkpoint | 24 biographical modules (M96-119) |
| M135 | B2 Final Exam | Full B2 assessment |

---

## Pending Improvements

### P0: Before Module Creation

| Item | Description | Status |
|------|-------------|--------|
| Verify State Standard 2024 | Confirm all B2 requirements covered | Pending |
| Folk culture preview | Add M41-43 for proverb context | Pending |

### P1: During Module Creation

| Item | Description |
|------|-------------|
| Capstone specifications | Full rubrics for M121-135 |
| Model answers | Writing tasks need examples |
| Source citations | History/biography modules need references |

### P2: After Level Complete

| Item | Description |
|------|-------------|
| Vocabulary finalization | Run `npm run vocab:rebuild` |
| Cross-reference validation | Ensure history references don't precede teaching |
| Final exam calibration | Verify M135 covers all B2 competencies |

---

## Build Order

1. **M01-30** (Grammar & Register) - Foundation
2. **M31-40** (Grammar Completion) - Numerals, word formation
3. **M41-70** (Phraseology) - With folk culture preview
4. **M71-95** (History) - Chronological Ukrainian history
5. **M96-120** (Biographies) - 24 notable Ukrainians
6. **M121-135** (Capstone) - Skills integration and final assessment

---

## Quality Gates

Before marking B2 complete:

- [ ] All 135 modules pass audit
- [ ] All modules pass pipeline (lint → generate → validate)
- [ ] Vocabulary database rebuilt
- [ ] All checkpoints in place
- [ ] Capstone has full rubrics and model project
- [ ] History/biography sources verified

---

## Technical Notes

### Metalanguage at B2

Students have learned grammatical terms at B1. B2 expands with:

| Domain | Terms |
|--------|-------|
| Register/Style | стиль, регістр, офіційний, розмовний, науковий |
| Vocabulary | синонім, антонім, пароніми, омоніми, фразеологізм |
| Syntax | підрядне речення, головне речення, сполучник |
| Instructions | перефразуйте, замініть, визначте, порівняйте, проаналізуйте |

Introduce new terms in first module of each phase.

### Content Notes

- **Decolonization:** History modules include myth-busting (Pereiaslav, Holodomor)
- **Gender balance:** 13 women, 11 men in biographies (intentional)
- **Folk culture:** M41-43 provide context for proverb/idiom modules

### Audit Commands

```bash
# Single module
python3 scripts/audit_module.py curriculum/l2-uk-en/b2/XX-*.md

# Full pipeline
npm run pipeline l2-uk-en b2 [module_num]

# Generate JSON
npm run generate:json l2-uk-en b2 [module_num]
```

---

## Dependencies

```
B2 depends on:
├── B1 completion (aspect mastery, complex sentences, grammatical vocabulary)
└── Folk culture preview modules (before proverb content)

C1 depends on:
└── B2 completion (register mastery required for C1)
```
