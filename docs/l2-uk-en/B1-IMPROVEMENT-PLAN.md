# B1 Improvement Plan

**Status:** Ready for Implementation
**Updated:** 2025-12-24 (Aligned with Curriculum Plan)
**Modules:** 85 (5 metalanguage bridge + 80 core)

---

## Current State

| Metric | Value |
|--------|-------|
| Total Modules | 85 |
| Built | M01-M85 (80 modules complete) |
| Remaining | Audit fixes |
| Immersion | 90-95% (full Ukrainian) |

---

## Key Parameters

### Immersion: 90-95%

All B1 modules use full immersion (except B1.0 bridge). English appears ONLY in:
- Vocabulary table translations

All instructions, explanations, and content body are in Ukrainian.

### Module Structure (85 modules)

| Phase | Modules | Content |
|-------|---------|---------|
| B1.0 | M01-05 | Metalanguage Bridge (grammar terminology in Ukrainian) |
| B1.1 | M06-15 | Aspect Mastery (10 modules) |
| B1.2 | M16-25 | Motion Verbs with Prefixes (10 modules) |
| B1.3 | M26-40 | Complex Sentences Deep Dive (15 modules) |
| B1.4 | M41-50 | Advanced Grammar (10 modules) |
| B1.5 | M51-60 | Vocabulary Expansion I (10 modules) |
| B1.6 | M61-70 | Vocabulary Expansion II (10 modules) |
| B1.7 | M71-80 | Contemporary Ukraine (10 modules) |
| B1.8 | M81-85 | Skills & Integration (5 modules) |

### Activity Requirements

| Module Type | Min Activities | Min Items/Activity |
|-------------|----------------|-------------------|
| B1-grammar | 12 | 8 |
| B1-vocab | 12 | 8 |
| B1-skills | 10 | 6 |
| B1-checkpoint | 15 | 10 |
| B1-capstone | 12 | 8 |

### Vocabulary

- Target: ~1,500 new words (level)
- Cumulative: ~3,300 words (A1+A2+B1)
- Per module: 15-25 words average

---

## Checkpoints

| Module | Checkpoint | Covers |
|--------|-----------|--------|
| M15 | Aspect Checkpoint | M06-14 |
| M25 | Motion Checkpoint | M16-24 |
| M40 | Syntax Checkpoint | M26-39 |
| M50 | Grammar Checkpoint | M41-49 |
| M60 | Vocab I Checkpoint | M51-59 |
| M70 | Vocab II Checkpoint | M61-69 |
| M80 | Culture Checkpoint | M71-79 |
| M85 | B1 Capstone | Full B1 assessment |

---

## Completed Improvements

- [x] State Standard 2024 compliance (participles, one-member sentences, synthetic future, passive -но/-то)
- [x] Assessment rubrics for M85 capstone
- [x] Enhanced checkpoint template with CEFR can-do targets
- [x] Production activity requirements (translate, transform, micro-write)
- [x] Metacognition elements (Why This Matters, Self-Check boxes)
- [x] Spiral review pattern
- [x] Module type classifications (B1-grammar, B1-vocab, B1-skills, B1-checkpoint, B1-capstone)

---

## Pending Improvements

### P1: During Module Fixes

| Item | Description |
|------|-------------|
| Error anticipation boxes | L1 interference warnings |
| Authentic tasks | Real-world application |
| External resources | YouTube, podcasts, articles |

### P2: After Level Complete

| Item | Description |
|------|-------------|
| Vocabulary finalization | Run `npm run vocab:rebuild` |
| Cross-module review | Ensure spiral review connects properly |
| Checkpoint validation | Verify checkpoints cover all preceding content |

---

## Build Order

1. **M01-05** (Metalanguage Bridge) - Grammar terminology in Ukrainian
2. **M06-15** (Aspect) - Foundation, highest priority
3. **M16-25** (Motion) - Core B1 grammar
4. **M26-40** (Complex Sentences) - Syntax mastery
5. **M41-50** (Advanced Grammar) - Participles, passive
6. **M51-70** (Vocabulary) - Thematic expansion
7. **M71-80** (Contemporary Ukraine) - Cultural content
8. **M81-85** (Skills & Capstone) - Integration and assessment

---

## Quality Gates

Before marking B1 complete:

- [ ] All 85 modules pass audit
- [ ] All modules pass pipeline (lint → generate → validate)
- [ ] Vocabulary database rebuilt
- [ ] Checkpoints cover all phases
- [ ] Capstone has full rubrics and model answers

---

## Technical Notes

### Metalanguage Scaffolding

B1.0 (M01-05) teaches grammar terminology BEFORE using it in instructions:

| Term | Ukrainian | Introduce In |
|------|-----------|--------------|
| aspect | вид | M01 |
| perfective | доконаний вид | M01 |
| imperfective | недоконаний вид | M01 |
| motion verb | дієслово руху | M05 |
| participle | дієприкметник | M05 |
| passive | пасивний стан | M05 |

Instruction verbs: визначте, утворіть, змініть, порівняйте.

### Audit Commands

```bash
# Single module
python3 scripts/audit_module.py curriculum/l2-uk-en/b1/XX-*.md

# Full pipeline
npm run pipeline l2-uk-en b1 [module_num]
```

---

## Dependencies

```
B1 depends on:
├── A2 completion (~1,800 cumulative vocabulary)
└── All 7 cases mastered

B2 depends on:
└── B1 completion (aspect, motion verbs, complex sentences, ~3,300 vocabulary)
```
