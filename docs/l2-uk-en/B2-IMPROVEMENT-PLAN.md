# B2 Improvement Plan

**Status:** Ready for Implementation
**Updated:** 2025-12-24 (Rebalanced)
**Modules:** 110

---

## Current State

| Metric | Value |
|--------|-------|
| Total Modules | 110 |
| Built | 0 |
| Remaining | 110 |
| Immersion | 100% (full Ukrainian) |

---

## Key Parameters

### Immersion: 100%

All B2 modules use full immersion. English appears ONLY in:
- Vocabulary table translations

All instructions, explanations, content body, and activity feedback are in Ukrainian. Students learned all grammatical terminology at B1.

### Module Structure (110 modules)

| Phase | Modules | Content |
|-------|---------|---------|
| B2.1a | M01-30 | Grammar & Register (Passive, participles, syntax) |
| B2.1b | M31-40 | Grammar Completion (Numerals, word formation, pronouns) |
| B2.2 | M41-70 | Phraseology & Synonymy (Proverbs, idioms, synonyms) |
| B2.3 | M71-95 | Ukrainian History (Medieval to present) |
| B2.4 | M96-110 | Skills & Capstone |

> **Note:** Biographies (65 modules) and Folk Culture & Arts (25 modules) moved to C1 for better pedagogical progression.

### Activity Requirements

| Module Type | Min Activities | Notes |
|-------------|----------------|-------|
| Grammar (M01-40) | 14 | Complex, needs more practice |
| Phraseology (M41-70) | 12 | Synonym/nuance focused |
| History (M71-95) | 10-12 | Reading comprehension focused |
| Skills (M96-110) | 12 | Academic writing, capstone |
| Checkpoint | 15 | Comprehensive review |

### Vocabulary

- Target: ~2,640 new words (level)
- Cumulative: ~5,940 words (A1+A2+B1+B2)
- Per module: 24 words average

---

## Checkpoints

| Module | Checkpoint | Covers |
|--------|-----------|--------|
| M30 | Grammar Checkpoint | Passive, participles, syntax (M01-29) |
| M40 | Grammar Completion Check | Numerals, word formation, pronouns (M31-39) |
| M70 | Phraseology Checkpoint | Idioms, proverbs, synonyms (M41-69) |
| M95 | History Checkpoint | Ukrainian history (M71-94) |
| M110 | B2 Final Exam | Full B2 assessment |

---

## Pending Improvements

### P1: During Module Creation

| Item | Description |
|------|-------------|
| Model answers | Writing tasks need examples |
| Source citations | History modules need references |
| Myth-busting | Pereiaslav, Holodomor decolonization |

### P2: After Level Complete

| Item | Description |
|------|-------------|
| Vocabulary finalization | Run `npm run vocab:rebuild` |
| Cross-reference validation | Ensure history references don't precede teaching |
| Final exam calibration | Verify M110 covers all B2 competencies |

---

## Build Order

1. **M01-30** (Grammar & Register) - Foundation
2. **M31-40** (Grammar Completion) - Numerals, word formation
3. **M41-70** (Phraseology) - Proverbs, idioms, synonyms
4. **M71-95** (History) - Chronological Ukrainian history
5. **M96-110** (Skills & Capstone) - Integration and final assessment

---

## Quality Gates

Before marking B2 complete:

- [ ] All 110 modules pass audit
- [ ] All modules pass pipeline (lint → generate → validate)
- [ ] Vocabulary database rebuilt
- [ ] All checkpoints in place
- [ ] Capstone has full rubrics and model project
- [ ] History sources verified

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

### Content Notes

- **Decolonization:** History modules include myth-busting (Pereiaslav, Holodomor)
- **No biographies at B2:** Moved to C1.3 for deeper treatment

### Audit Commands

```bash
# Single module
python3 scripts/audit_module.py curriculum/l2-uk-en/b2/XX-*.md

# Full pipeline
npm run pipeline l2-uk-en b2 [module_num]
```

---

## Dependencies

```
B2 depends on:
├── B1 completion (aspect mastery, complex sentences, grammatical vocabulary)
└── ~3,300 cumulative vocabulary

C1 depends on:
└── B2 completion (register mastery required for C1)
```
