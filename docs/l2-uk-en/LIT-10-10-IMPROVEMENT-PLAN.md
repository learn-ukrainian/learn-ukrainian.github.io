# LIT Track: Path to 10/10

**Created:** 2026-01-31
**Current Score:** 3.2/10
**Target Score:** 10/10

---

## LIT-Specific Scoring Weights

Literature tracks prioritize literary analysis, authentic text engagement, and archaic vocabulary mastery.

| Criterion | Weight | Score | Weighted |
|-----------|--------|-------|----------|
| Literary depth/analysis | 20% | 8/10 | 1.60 |
| Authentic text engagement | 15% | 7/10 | 1.05 |
| Archaic/literary vocabulary | 15% | 0/10 | 0.00 |
| Cultural significance | 10% | 8/10 | 0.80 |
| CEFR post-C1 alignment | 10% | 7/10 | 0.70 |
| Activity coverage | 10% | 6/10 | 0.60 |
| Audit pass rate | 15% | 0/10 | 0.00 |
| Internal consistency | 5% | 5/10 | 0.25 |
| **Total** | 100% | — | **3.2/10** |

---

## Current State

| Metric | Value | Status |
|--------|-------|--------|
| Total Modules | 30 | ✅ Complete |
| Audit Pass Rate | 0% (0/30) | 🔴 All failing |
| Primary Blocker | Missing vocabulary | 🔴 0/30 files |
| Content Written | 30/30 | ✅ Complete |
| Activities | 30/30 | ✅ Complete |
| Word Counts | 3,400-4,100 (vs 4,500 target) | ⚠️ 76-91% |

---

## Critical Blocker: Vocabulary Gate

**ALL 30 modules fail the same gate:**
```
Structure: Missing '## Vocabulary' header OR vocabulary sidecar
```

**Fix Required:** Create 30 vocabulary YAML files

**Secondary Issues:**
- 5 Outline Compliance Errors per module
- Word counts 9-24% below target
- M08, M23-25 missing some activity types

---

## Module Coverage (5 Literary Periods)

| Period | Modules | Focus | Status |
|--------|---------|-------|--------|
| Kotliarevsky | M01-05 | Eneida, Natalka Poltavka | ✅ Content |
| Kvitka-Osnovyanenko | M06-10 | Prose, ethnography | ✅ Content |
| Shevchenko | M11-20 | Kobzar, ballads, diary | ✅ Content |
| Kulish | M21-25 | Black Council, language question | ✅ Content |
| Nechuy-Levytsky | M26-30 | Realism, Kaidash family | ✅ Content |

---

## Vocabulary Requirements (LIT-Specific)

LIT vocabulary must include:

1. **Archaic Ukrainian** - Church Slavonic influences, obsolete forms
2. **Literary terminology** - poetic devices, narrative techniques
3. **Period-specific vocabulary** - era-appropriate language
4. **Dialect markers** - regional speech patterns in texts

**Target:** 50+ items per module (1,500 total for track)

**Structure per vocabulary file:**
```yaml
items:
  - lemma: козак
    ipa: /koˈzɑk/
    translation: Cossack
    pos: noun
    gender: m
    register: historical
    period: 17th-18th c.
    notes: "Central figure in Kotliarevsky's Eneida"
```

---

## Implementation Plan

### Phase 1: Vocabulary Creation (Critical) — 20 hours

**Create 30 vocabulary YAML files with LIT-specific items**

**Priority order:**
1. Shevchenko modules (M11-20) — highest cultural impact
2. Kotliarevsky modules (M01-05) — foundational
3. Remaining modules (M06-10, M21-30)

**Per module:**
- Extract key terms from existing content
- Add archaic/Church Slavonic vocabulary
- Include literary terminology
- Add period markers and register notes

**Estimated:** 40 minutes per module × 30 = 20 hours

### Phase 2: Word Count Expansion — 10 hours

**Expand modules to meet 4,500 word target:**

| Module | Current | Target | Need |
|--------|---------|--------|------|
| M04 | 3,516 | 4,500 | +984 |
| M14 | 3,543 | 4,500 | +957 |
| M19 | 3,441 | 4,500 | +1,059 |
| M24 | 3,411 | 4,500 | +1,089 |
| M25 | 3,429 | 4,500 | +1,071 |

**Approach:**
- Deeper literary analysis
- Additional historical context
- More excerpt discussion

### Phase 3: Fix Activity Gaps — 3 hours

**Add missing activity types:**
- M08: group-sort, match-up, quiz
- M23-25: reading activities

### Phase 4: Fix Outline Compliance — 5 hours

**Update plans to match content structure** (30 modules × 10 min)

---

## Implementation Checklist

### Phase 1: Vocabulary (Week 1-2) — 20 hours
- [ ] Create vocabulary YAML for M11-20 (Shevchenko)
- [ ] Create vocabulary YAML for M01-05 (Kotliarevsky)
- [ ] Create vocabulary YAML for M06-10 (Kvitka)
- [ ] Create vocabulary YAML for M21-25 (Kulish)
- [ ] Create vocabulary YAML for M26-30 (Nechuy-Levytsky)

### Phase 2: Word Count (Week 3) — 10 hours
- [ ] Expand M04, M14, M19, M24, M25 content
- [ ] Verify all modules meet 4,500 target

### Phase 3: Activities (Week 3) — 3 hours
- [ ] Add missing activities to M08, M23-25

### Phase 4: Outline Compliance (Week 4) — 5 hours
- [ ] Update all 30 plan files

### Phase 5: Validation — 2 hours
- [ ] Run full audit
- [ ] Verify 30/30 passing

---

## Success Criteria (10/10)

| Criterion | Requirement |
|-----------|-------------|
| Audit pass rate | 30/30 modules passing (100%) |
| Vocabulary | All modules have LIT-specific vocabulary |
| Word counts | All modules 4,500+ words |
| Literary analysis | Deep engagement with primary texts |
| Archaic vocabulary | Period-appropriate language included |

---

## Estimated Total Effort

| Phase | Hours | Priority |
|-------|-------|----------|
| Phase 1: Vocabulary | 20 | Critical |
| Phase 2: Word Count | 10 | High |
| Phase 3: Activities | 3 | Medium |
| Phase 4: Outline | 5 | Medium |
| Phase 5: Validation | 2 | Low |
| **Total** | **40 hours** | — |

---

## LIT Expansion Notes (Future)

User plans to expand LIT track later. Current 30 modules cover:
- Early modern Ukrainian literature (1798-1890s)

Potential expansion:
- Modernism (Franko, Lesia Ukrainka, Kobylianska)
- Executed Renaissance (Khvylovyi, Zerov, Tychyna)
- Shestydesiatnyky (Stus, Symonenko, Kostenko)
- Contemporary (Zhadan, Andrukhovych, Zabuzhko)

---

## References

- `docs/LIT-STATUS.md` - Current audit status
- `claude_extensions/quick-ref/lit.md` - LIT workflow
- `curriculum/l2-uk-en/plans/lit/` - All 30 plans
