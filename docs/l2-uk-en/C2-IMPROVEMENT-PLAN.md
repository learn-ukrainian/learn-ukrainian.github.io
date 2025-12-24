# C2 Improvement Plan

**Status:** Ready for Implementation
**Updated:** 2025-12-23 (Rebalanced)
**Modules:** 100

---

## Current State

| Metric | Value |
|--------|-------|
| Total Modules | 100 |
| Built | 0 |
| Remaining | 100 |
| Immersion | 100% (full Ukrainian) |

**Note:** C2 has the best-structured curriculum plan. Focus is purely on implementation.

---

## Key Parameters

### Immersion: 100%

All C2 modules use full immersion. English appears ONLY in:
- Vocabulary table translations

All instructions, explanations, content body, and activity feedback are in Ukrainian. At C2, learners have mastered all grammatical and academic terminology from prior levels.

### Module Structure (100 modules)

| Phase | Modules | Content |
|-------|---------|---------|
| C2.1 | M01-25 | Stylistic Perfection (7 functional styles + advanced devices) |
| C2.2 | M26-45 | Literary Mastery |
| C2.3 | M46-75 | Professional Specialization (includes Legal & Medical tracks) |
| C2.4 | M76-100 | Meta-Skills & Capstone (Teaching, Translation, Certification) |

**Note:** Expanded from 80 to 100 modules to include professional specializations and meta-skills.

### Activity Requirements

| Module Type | Min Activities | Notes |
|-------------|----------------|-------|
| Stylistic (M01-20) | 14 | Style transformation, production |
| Literary (M21-40) | 12 | Analysis, creation |
| Professional (M41-60) | 12 | Document production, scenarios |
| Capstone (M61-80) | 10 | Project work, review |
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
| M100 | C2 Final Exam | Full C2 assessment + Capstone defense |

---

## Capstone Options (M67-72)

| Option | Requirements |
|--------|--------------|
| Research Paper | 10,000-12,000 words, academic register, 15+ sources |
| Literary Work | Poetry collection (20+ poems) OR prose (15,000+ words) |
| Translation Project | 50+ pages source text, translator's preface, glossary |
| Professional Portfolio | 10+ documents across 3+ styles |

---

## Pending Improvements

### P0: Before Module Creation

| Item | Description | Status |
|------|-------------|--------|
| Expand C2.2-C2.4 specs | Literary, professional, capstone need detailed specs | Pending |
| Define capstone timeline | M67-72 need milestone structure | Pending |

### P1: During Module Creation

| Item | Description |
|------|-------------|
| Model capstone project | Create example for at least one option |
| Creative writing coverage | Expand M31-32 or integrate throughout C2.2 |
| 7 functional styles | Ensure religious + epistolary are explicitly taught |

### P2: After Level Complete

| Item | Description |
|------|-------------|
| Vocabulary finalization | Run `npm run vocab:rebuild` |
| Style coverage validation | Verify all 7 styles explicitly covered |
| Capstone calibration | Verify assessment rubrics are complete |

---

## Build Order

1. **M01-09** (Style Foundation) - Core stylistic skills
2. **M67-72** (Capstone Structure) - Define the goal early
3. **M10-20** (Complete Stylistic) - All 7 functional styles
4. **M21-40** (Literary Mastery) - Theory and creation
5. **M41-60** (Professional) - Meta-skills for any domain
6. **M61-66, M73-80** (Remaining) - Complete coverage

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
# Single module
python3 scripts/audit_module.py curriculum/l2-uk-en/c2/XX-*.md

# Full pipeline
npm run pipeline l2-uk-en c2 [module_num]

# Generate JSON
npm run generate:json l2-uk-en c2 [module_num]
```

---

## Dependencies

```
C2 depends on:
├── C1 completion (academic foundation, 5 functional styles, literature)
├── B2 completion (register mastery, phraseology)
├── B1 completion (grammar foundation)
└── ~9,000 cumulative vocabulary

Nothing depends on C2:
└── C2 is the final level (mastery achieved)
```

---

## Future: Specialization Tracks

After core C2 is complete, optional extension tracks can be developed:

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
