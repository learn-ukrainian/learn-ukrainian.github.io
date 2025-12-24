# C1 Improvement Plan

**Status:** Ready for Implementation
**Updated:** 2025-12-24 (Rebalanced)
**Modules:** 160

---

## Current State

| Metric | Value |
|--------|-------|
| Total Modules | 160 |
| Built | 0 |
| Remaining | 160 |
| Immersion | 100% (full Ukrainian) |

> **Note:** Biographies (65 modules) and Folk Culture & Arts (25 modules) moved from B2 to C1.

---

## Key Parameters

### Immersion: 100%

All C1 modules use full immersion. English appears ONLY in:
- Vocabulary table translations

### Module Structure (160 modules)

| Phase | Modules | Content |
|-------|---------|---------|
| C1.1 | M01-20 | Academic Foundation (University-level writing) |
| C1.2 | M21-35 | Professional & Social (Workplace contexts) |
| C1.3 | M36-100 | Biographies (65 Ukrainian historical figures) |
| C1.4 | M101-120 | Advanced Stylistics & Rhetoric |
| C1.5 | M121-145 | Folk Culture & Arts |
| C1.6 | M146-160 | Literature - Complete |

### Activity Requirements

| Module Type | Min Activities | Notes |
|-------------|----------------|-------|
| Academic (M01-20) | 16 | Complex metalinguistic content |
| Professional (M21-35) | 14 | Scenario-based |
| Biographies (M36-100) | 12 | Narrative, historical analysis |
| Stylistics (M101-120) | 14 | Analysis-heavy |
| Folk Culture (M121-145) | 12 | Reading comprehension focused |
| Literature (M146-160) | 12 | Text analysis focused |
| Checkpoint | 18 | Comprehensive review |

### Vocabulary

- Target: ~3,840 new words (level)
- Cumulative: ~9,780 words (A1-C1)
- Per module: 24 words average

---

## Checkpoints

| Module | Checkpoint | Covers |
|--------|-----------|--------|
| M20 | Academic Checkpoint | M01-19 |
| M35 | Professional Checkpoint | M21-34 |
| M100 | Biographies Checkpoint | M36-99 |
| M120 | Stylistics Checkpoint | M101-119 |
| M145 | Folk Culture Checkpoint | M121-144 |
| M160 | C1 Final Exam | Full C1 assessment |

---

## Pending Improvements

### P1: During Module Creation

| Item | Description |
|------|-------------|
| Model answers | All production tasks need examples |
| Biography balance | Ensure gender/era balance |
| Contemporary coverage | Modern authors comparable to classics |

### P2: After Level Complete

| Item | Description |
|------|-------------|
| Vocabulary finalization | Run `npm run vocab:rebuild` |
| Cross-reference validation | Connect biographies to stylistics |
| Final exam calibration | Verify M160 covers all C1 competencies |

---

## Build Order

1. **M01-20** (Academic) - Foundation with metalanguage
2. **M21-35** (Professional) - Workplace and social contexts
3. **M36-100** (Biographies) - 65 Ukrainian figures chronologically
4. **M101-120** (Stylistics) - 5 functional styles + rhetoric
5. **M121-145** (Folk Culture) - Traditional arts, music, beliefs
6. **M146-160** (Literature) - Classics + contemporary + capstone

---

## Quality Gates

Before marking C1 complete:

- [ ] All 160 modules pass audit
- [ ] All modules pass pipeline (lint → generate → validate)
- [ ] Vocabulary database rebuilt
- [ ] All checkpoints in place
- [ ] Capstone has full rubrics and model project
- [ ] All 5 functional styles explicitly covered

---

## Technical Notes

### Metalanguage at C1

| Domain | Terms |
|--------|-------|
| Functional Styles | офіційно-діловий, науковий, публіцистичний, художній, розмовний |
| Literary Analysis | метафора, епітет, персоніфікація, гіпербола, алюзія |
| Rhetoric | аргументація, тези, антитеза, риторичне питання |
| Academic | тема, ідея, структура, аналіз, висновок, джерело, цитата |
| Sociolinguistics | діалект, суржик, мовна політика, літературна мова |

### Audit Commands

```bash
python3 scripts/audit_module.py curriculum/l2-uk-en/c1/XX-*.md
npm run pipeline l2-uk-en c1 [module_num]
```

---

## Dependencies

```
C1 depends on:
├── B2 completion (register mastery, 5 functional styles)
├── B1 completion (aspect, motion verbs, complex sentences)
└── ~5,940 cumulative vocabulary

C2 depends on:
└── C1 completion
```
