# C1 Improvement Plan

**Status:** Ready for Implementation
**Updated:** 2025-12-23 (Rebalanced)
**Modules:** 160

---

## Current State

| Metric | Value |
|--------|-------|
| Total Modules | 160 |
| Built | 0 |
| Remaining | 160 |
| Immersion | 100% (full Ukrainian) |

**Note:** All previous C1 content was deleted during restructure. Starting fresh.

---

## Key Parameters

### Immersion: 100%

All C1 modules use full immersion. English appears ONLY in:
- Vocabulary table translations

All instructions, explanations, content body, and activity feedback are in Ukrainian.

### Module Structure (160 modules)

| Phase | Modules | Content |
|-------|---------|---------|
| C1.1 | M01-20 | Academic Foundation |
| C1.2 | M21-35 | Professional & Social |
| C1.3 | M36-100 | Biographies (65 modules) |
| C1.4 | M101-120 | Advanced Stylistics & Rhetoric |
| C1.5 | M121-145 | Folk Culture & Arts |
| C1.6 | M146-160 | Literature - Complete |

**Note:** Biographies and Folk Culture moved from B2 to C1 for better pedagogical progression.

### Activity Requirements

| Module Type | Min Activities | Notes |
|-------------|----------------|-------|
| Academic (M01-20) | 16 | Complex metalinguistic content |
| Professional (M21-35) | 14 | Scenario-based |
| Stylistics (M36-55) | 14 | Analysis-heavy |
| Folk Culture (M56-80) | 12 | Reading comprehension focused |
| Literature (M81-115) | 12 | Text analysis focused |
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

### P0: Before Module Creation

| Item | Description | Status |
|------|-------------|--------|
| Verify State Standard 2024 | Confirm all C1 requirements covered | Pending |
| Expand C1.4-C1.6 specs | Folk culture + literature need detailed specs | Pending |

### P1: During Module Creation

| Item | Description |
|------|-------------|
| Capstone specifications | Full rubrics for M111-115 |
| Model answers | All production tasks need examples |
| Contemporary author depth | Ensure modern authors get coverage comparable to classics |

### P2: After Level Complete

| Item | Description |
|------|-------------|
| Vocabulary finalization | Run `npm run vocab:rebuild` |
| Cross-reference validation | Ensure folk culture references connect to stylistics |
| Final exam calibration | Verify M115 covers all C1 competencies |

---

## Build Order

1. **M01-20** (Academic) - Foundation with metalanguage
2. **M36-55** (Stylistics) - Core C1 skills (5 functional styles)
3. **M81-95** (Literature Classics) - Shevchenko, Franko, Lesya Ukrainka
4. **M21-35** (Professional) - Workplace and social contexts
5. **M56-80** (Folk Culture) - Traditional arts, music, beliefs
6. **M96-115** (Modern Literature & Capstone) - Contemporary authors + final project

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

Students have learned basic grammatical terms at B1/B2. C1 expands with academic and literary terminology:

| Domain | Terms |
|--------|-------|
| Functional Styles | офіційно-діловий, науковий, публіцистичний, художній, розмовний |
| Literary Analysis | метафора, епітет, персоніфікація, гіпербола, алюзія |
| Rhetoric | аргументація, тези, антитеза, риторичне питання |
| Academic | тема, ідея, структура, аналіз, висновок, джерело, цитата |
| Sociolinguistics | діалект, суржик, мовна політика, літературна мова |

Introduce domain-specific terminology at the start of each phase.

### Audit Commands

```bash
# Single module
python3 scripts/audit_module.py curriculum/l2-uk-en/c1/XX-*.md

# Full pipeline
npm run pipeline l2-uk-en c1 [module_num]

# Generate JSON
npm run generate:json l2-uk-en c1 [module_num]
```

---

## Dependencies

```
C1 depends on:
├── B2 completion (register mastery, 5 functional styles)
├── B1 completion (aspect, motion verbs, complex sentences)
└── ~6,200 cumulative vocabulary

C2 depends on:
└── C1 completion
```
