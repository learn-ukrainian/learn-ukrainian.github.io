# C2 Improvement Plan

**Status:** Ready for Implementation
**Updated:** 2025-12-24 (Rebalanced)
**Modules:** 100

---

## Current State

| Metric | Value |
|--------|-------|
| Total Modules | 100 |
| Built | 0 |
| Remaining | 100 |
| Immersion | 100% (full Ukrainian) |

> **Note:** Expanded from 80 to 100 modules to include professional specialization and meta-skills.

---

## Key Parameters

### Immersion: 100%

All C2 modules use full immersion. English appears ONLY in:
- Vocabulary table translations

### Module Structure (100 modules)

| Phase | Modules | Content |
|-------|---------|---------|
| C2.1 | M01-25 | Stylistic Perfection (7 functional styles + advanced devices) |
| C2.2 | M26-45 | Literary Mastery (Theory, creation, criticism) |
| C2.3 | M46-75 | Professional Specialization (Meta-skills + Legal/Medical tracks) |
| C2.4 | M76-100 | Meta-Skills & Capstone (Teaching, Translation, Certification) |

### Activity Requirements

| Module Type | Min Activities | Notes |
|-------------|----------------|-------|
| Stylistic (M01-25) | 14 | Style transformation, production |
| Literary (M26-45) | 12 | Analysis, creation |
| Professional (M46-75) | 12 | Document production, scenarios |
| Meta-Skills (M76-100) | 10 | Project work, capstone |
| Checkpoint | 16 | Comprehensive assessment |

**All production tasks MUST have Model Answers.**

### Vocabulary

- Target: ~2,500 new words (level)
- Cumulative: ~12,280 words (A1-C2)
- Per module: 25 words average

---

## Checkpoints

| Module | Checkpoint | Covers |
|--------|-----------|--------|
| M25 | Stylistic Checkpoint | M01-24 |
| M45 | Literary Checkpoint | M26-44 |
| M75 | Professional Checkpoint | M46-74 |
| M100 | C2 Final Exam | Full C2 + Capstone defense |

---

## Capstone Options (M89-94)

| Option | Requirements |
|--------|--------------|
| Research Paper | 10,000-12,000 words, academic register, 15+ sources |
| Literary Work | Poetry collection (20+ poems) OR prose (15,000+ words) |
| Translation Project | 50+ pages source text, translator's preface, glossary |
| Professional Portfolio | 10+ documents across 3+ styles |

---

## Pending Improvements

### P1: During Module Creation

| Item | Description |
|------|-------------|
| Model capstone project | Create example for at least one option |
| 7 functional styles | Ensure religious + epistolary explicitly taught |
| Creative writing | Expand coverage throughout C2.2 |

### P2: After Level Complete

| Item | Description |
|------|-------------|
| Vocabulary finalization | Run `npm run vocab:rebuild` |
| Style coverage validation | Verify all 7 styles explicitly covered |
| Capstone calibration | Verify assessment rubrics are complete |

---

## Build Order

1. **M01-25** (Stylistic Perfection) - All 7 functional styles
2. **M26-45** (Literary Mastery) - Theory and creation
3. **M46-75** (Professional) - Meta-skills + Legal/Medical
4. **M76-100** (Meta-Skills & Capstone) - Teaching, Translation, Final

---

## Quality Gates

Before marking C2 complete:

- [ ] All 100 modules pass audit
- [ ] All modules pass pipeline (lint → generate → validate)
- [ ] Vocabulary database rebuilt
- [ ] All 7 functional styles covered (including religious, epistolary)
- [ ] Capstone has full rubrics and model project
- [ ] All production tasks have Model Answers

---

## Technical Notes

### 7 Functional Styles (C2-Specific)

C2 adds two styles beyond the 5 taught at B2/C1:

| Style | Ukrainian | Coverage |
|-------|-----------|----------|
| Official-Business | офіційно-діловий | B2+ |
| Scientific | науковий | B2+ |
| Journalistic | публіцистичний | B2+ |
| Artistic | художній | B2+ |
| Conversational | розмовний | B2+ |
| **Religious** | релігійний | C2 only |
| **Epistolary** | епістолярний | C2 only |

### C2-Specific Terminology

| Domain | Terms |
|--------|-------|
| 7 Styles | + релігійний, епістолярний |
| Literary | інтертекстуальність, наратив, постмодернізм, дискурс |
| Translation | переклад, перекладач, вихідний текст, цільовий текст |
| Academic | дисертація, захист, рецензія, опонент |
| Professional | протокол, меморандум, договір, статут |

### Audit Commands

```bash
python3 scripts/audit_module.py curriculum/l2-uk-en/c2/XX-*.md
npm run pipeline l2-uk-en c2 [module_num]
```

---

## Dependencies

```
C2 depends on:
├── C1 completion (academic foundation, biographies, literature)
├── B2 completion (register mastery, phraseology)
├── B1 completion (grammar foundation)
└── ~9,780 cumulative vocabulary

Nothing depends on C2:
└── C2 is the final level (mastery achieved)
```

---

## Future: Specialization Tracks

After core C2, optional extension tracks can be developed:

| Track | Focus |
|-------|-------|
| Правничий | Legal terminology, contracts, court |
| Медичний | Medical terminology, patient communication |
| Технічний/IT | Technical writing, documentation |
| Бізнес | Corporate communication, negotiations |
| Освітній | Academic Ukrainian, pedagogy |
| Дипломатичний | Protocol, international relations |
| Журналістський | Investigative journalism, media |

These will be separate documents building on C2.3 Professional foundation.
