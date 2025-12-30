# B2 Improvement Plan

**Status:** Ready for Implementation
**Updated:** 2025-12-29 (145-module structure)
**Modules:** 145

---

## Current State

| Metric | Value |
|--------|-------|
| Total Modules | 145 |
| Built | 0 |
| Remaining | 145 |
| Immersion | 100% (full Ukrainian) |

---

## Key Parameters

### Immersion: 100%

All B2 modules use full immersion. English appears ONLY in:
- Vocabulary table translations

All instructions, explanations, content body, and activity feedback are in Ukrainian. Students learned all grammatical terminology at B1.

### Module Structure (145 modules)

| Phase | Modules | Content | Notes |
|-------|---------|---------|-------|
| B2.1a | M01-30 | Grammar & Register (Passive, participles, syntax) | |
| B2.1b | M31-40 | Grammar Completion (Numerals, word formation, pronouns) | |
| B2.2 | M41-70 | Phraseology & Synonymy (Proverbs, idioms, synonyms) | |
| B2.3a | M71-83 | History: Origins → Commonwealth | **M83** synthesis |
| B2.3b | M84-107 | History: Cossack Era & Empire | **M107** synthesis |
| B2.3c | M108-119 | History: Trauma & Resistance | **M119** synthesis |
| B2.3d | M120-125 | History: Independence Era | **M125** synthesis |
| B2.3e | M126-131 | History: Revolution & War | **M131** synthesis |
| B2.4 | M132-145 | Skills & Capstone | **M145** capstone |

> **Note:** Biographies (65 modules) and Folk Culture & Arts (25 modules) moved to C1 for better pedagogical progression. History expanded to 61 modules (M71-131) with 5 synthesis modules replacing traditional checkpoints.

### Activity Requirements

| Module Type | Min Activities | Notes |
|-------------|----------------|-------|
| Grammar (M01-40) | 14 | Complex, needs more practice |
| Phraseology (M41-70) | 12 | Synonym/nuance focused |
| History (M71-131) | 10-12 | Reading comprehension focused |
| Synthesis (M83, M107, M119, M125, M131) | 14 | Cross-era analysis, not recall |
| Skills (M132-145) | 12 | Academic writing, capstone |

### Vocabulary

- Target: ~2,640 new words (level)
- Cumulative: ~5,940 words (A1+A2+B1+B2)
- Per module: 24 words average

---

## Checkpoints & Synthesis Modules

| Module | Type | Covers |
|--------|------|--------|
| M30 | Checkpoint | Passive, participles, syntax (M01-29) |
| M40 | Checkpoint | Numerals, word formation, pronouns (M31-39) |
| M70 | Checkpoint | Idioms, proverbs, synonyms (M41-69) |
| M83 | **Synthesis** | Origins → Commonwealth (M71-82) |
| M107 | **Synthesis** | Cossack Era & Empire (M84-106) |
| M119 | **Synthesis** | Trauma & Resistance (M108-118) |
| M125 | **Synthesis** | Independence Era (M120-124) |
| M131 | **Synthesis** | Revolution & War (M126-130) |
| M145 | Capstone | Full B2 assessment |

> **Synthesis vs Checkpoint:** Synthesis modules test cross-era analysis and historical argumentation, not recall. See `b2-synthesis-module-template.md`.

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
| Final exam calibration | Verify M145 covers all B2 competencies |

---

## Build Order

1. **M01-30** (Grammar & Register) - Foundation
2. **M31-40** (Grammar Completion) - Numerals, word formation
3. **M41-70** (Phraseology) - Proverbs, idioms, synonyms
4. **M71-131** (History) - Ukrainian history with 5 synthesis modules
5. **M132-145** (Skills & Capstone) - Integration and final assessment

---

## Quality Gates

Before marking B2 complete:

- [ ] All 145 modules pass audit
- [ ] All modules pass pipeline (lint → generate → validate)
- [ ] Vocabulary database rebuilt
- [ ] All checkpoints and synthesis modules in place
- [ ] Capstone (M145) has full rubrics and model project
- [ ] History sources verified (M71-131)

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
