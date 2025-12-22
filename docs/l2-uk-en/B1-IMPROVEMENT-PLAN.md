# B1 Improvement Plan

**Status:** Ready for Implementation
**Updated:** 2025-12-22
**Modules:** 85 (5 aspect foundation + 80 core)

---

## Current State

| Metric | Value |
|--------|-------|
| Total Modules | 85 |
| Built | 1 (M01) |
| Remaining | 84 |
| Immersion | 100% (full Ukrainian) |

---

## Key Parameters

### Immersion: 100%

All B1 modules use full immersion. English appears ONLY in:
- Vocabulary table translations
- Activity answer explanations (where pedagogically necessary)

All instructions, explanations, and content body are in Ukrainian.

### Module Structure (85 modules)

| Phase | Modules | Content |
|-------|---------|---------|
| B1.1 | M01-10 | Aspect Mastery (5 new foundation + 5 core) |
| B1.2 | M11-20 | Motion Verbs |
| B1.3 | M21-35 | Complex Sentences |
| B1.4 | M36-45 | Advanced Grammar (Participles, Passive, etc.) |
| B1.5 | M46-55 | Vocabulary Expansion I |
| B1.6 | M56-65 | Vocabulary Expansion II |
| B1.7 | M66-75 | Contemporary Ukraine |
| B1.8 | M76-85 | Skills Integration & Capstone |

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

## Completed Improvements

These were implemented in the curriculum plan and guidelines before the rebuild:

- [x] State Standard 2024 compliance (participles, one-member sentences, synthetic future, passive -но/-то)
- [x] Assessment rubrics for M85 capstone
- [x] Enhanced checkpoint template with CEFR can-do targets
- [x] Production activity requirements (translate, transform, micro-write)
- [x] Metacognition elements (Why This Matters, Self-Check boxes)
- [x] Spiral review pattern
- [x] Module type classifications (B1-grammar, B1-vocab, B1-skills, B1-checkpoint, B1-capstone)

---

## Pending Improvements

### P1: Apply During Module Creation

| Item | Description | When |
|------|-------------|------|
| Error anticipation boxes | L1 interference warnings | Each grammar module |
| Authentic tasks | Real-world application | Each module |
| External resources | YouTube, podcasts, articles | After content exists |

### P2: After Level Complete

| Item | Description |
|------|-------------|
| Vocabulary finalization | Run `npm run vocab:rebuild` |
| Cross-module review | Ensure spiral review connects properly |
| Checkpoint validation | Verify checkpoints cover all preceding content |

---

## Build Order

1. **M01-10** (Aspect) - Foundation, highest priority
2. **M11-20** (Motion) - Core B1 grammar
3. **M21-35** (Complex Sentences) - Syntax mastery
4. **M36-45** (Advanced Grammar) - Participles, passive
5. **M46-65** (Vocabulary) - Thematic expansion
6. **M66-75** (Contemporary Ukraine) - Cultural content
7. **M76-85** (Skills & Capstone) - Integration and assessment

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

At 100% immersion, grammatical terms must be taught as vocabulary BEFORE using them in Ukrainian instructions:

| Term | Ukrainian | Introduce Before |
|------|-----------|------------------|
| aspect | вид | M01 |
| perfective | доконаний вид | M01 |
| imperfective | недоконаний вид | M01 |
| motion verb | дієслово руху | M11 |
| participle | дієприкметник | M36 |
| passive | пасивний стан | M41 |

Include instruction verbs in vocabulary: визначте, утворіть, змініть, порівняйте.

### Audit Commands

```bash
# Single module
python3 scripts/audit_module.py curriculum/l2-uk-en/b1/XX-*.md

# Full pipeline
npm run pipeline l2-uk-en b1 [module_num]

# Generate JSON
npm run generate:json l2-uk-en b1 [module_num]
```
