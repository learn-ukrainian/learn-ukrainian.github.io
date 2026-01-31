# C1 Curriculum: Path to 10/10

**Created:** 2025-01-31
**Current Score:** 4.7/10
**Target Score:** 10/10

---

## Standardized Scoring (Consistent Across All Levels)

| Criterion | Weight | Score | Weighted |
|-----------|--------|-------|----------|
| Grammar/Content coverage | 15% | 8/10 | 1.20 |
| Vocabulary coverage | 10% | 0/10 | 0.00 |
| Skills balance | 15% | 7/10 | 1.05 |
| State Standard compliance | 15% | 7/10 | 1.05 |
| CEFR alignment | 10% | 7/10 | 0.70 |
| Internal consistency | 10% | 5/10 | 0.50 |
| Checkpoint structure | 10% | 8/10 | 0.80 |
| Audit pass rate | 15% | 0/10 | 0.00 |
| **Total** | 100% | — | **4.7/10** |

---

## Current State

| Metric | Value | Status |
|--------|-------|--------|
| Total Modules | 106 | ✅ Complete |
| Audit Pass Rate | 0% (0/106) | 🔴 All failing |
| Primary Blocker | Missing vocabulary | 🔴 Only 4/106 files |
| Word Counts | 31-52% below target | ⚠️ |

---

## Critical Blocker: Vocabulary Structure Gate

**ALL 106 modules fail the same gate:**
```
Structure: Missing '## Vocabulary' header OR vocabulary sidecar
```

**Current State:**
- Only 4 vocabulary YAML files exist:
  - 21-cv-resume-writing.yaml
  - 22-job-interview.yaml
  - 77-klasychna-muzyka-2-natsionalna-shkola.yaml
  - 89-praktyka-1-narodna-kultura.yaml

**Fix Required:** Create 102 vocabulary YAML files

---

## Secondary Issues

### 1. Word Count Deficiency

| Phase | Target | Actual Range | Gap |
|-------|--------|--------------|-----|
| C1.1 Academic (M01-19) | 4,000 | 1,929-2,607 | 35-52% short |
| C1.2 Professional (M21-35) | 4,000 | 1,928-2,756 | 31-52% short |
| C1.3 Stylistics (M36-55) | 3,000 | 1,668-2,370 | 21-44% short |
| C1.4 Folk Culture (M56-91) | 3,000 | 1,138-3,731 | Variable |
| C1.5 Literature (M92-106) | 3,000-3,500 | 1,917-2,523 | 25-45% short |

**Critical:** M87-88 have only ~1,140 words each (38% of target)

### 2. Outline Compliance Errors

- Academic phase: 5-7 violations per module
- Professional phase: 6-7 violations per module
- Stylistics phase: 1-4 violations per module
- Folk/Literature: 0-4 violations per module

### 3. Missing Activity Types

| Activity Type | Modules Missing |
|---------------|-----------------|
| `reading` | ~40% of modules |
| `cloze` | ~30% of modules |
| `error-correction` | ~30% of modules |
| `group-sort` | ~25% of modules |

### 4. Forbidden Activity Types (M50-54)

- 4 forbidden types per module (true-false, anagram, mark-the-words)
- Not allowed at C1 level

### 5. Template Violations (~15 modules)

- M25, M30, M36-40, M47, M53-54, M79, M85-88, M95, M97-101

### 6. Naturalness Pending

- All modules: "None/10 (PENDING)"
- MCP validation not run

---

## Phase Structure (106 Modules)

| Phase | Modules | Focus | Checkpoint |
|-------|---------|-------|------------|
| C1.1 | M01-20 | Academic Foundation | M20 |
| C1.2 | M21-35 | Professional Context | M35 |
| C1.3 | M36-47 | Stylistics & Register | M47 |
| C1.4 | M48-91 | Folk Culture & Arts | M91 |
| C1.5 | M92-106 | Literature | M106 |

---

## Implementation Plan

### Phase 1: Vocabulary YAML Creation (Critical) — 25 hours

**Unblock all 106 modules by creating vocabulary sidecars**

```bash
# For each module, create vocabulary/{slug}.yaml with:
items:
  - lemma: слово
    ipa: /ˈslɔwɔ/
    translation: word
    pos: noun
    gender: n
```

**Priority order:**
1. Checkpoints first (M20, M35, M47, M91, M106)
2. Academic phase (M01-19)
3. Professional phase (M21-34)
4. Remaining modules

**Estimated:** 15 minutes per module × 102 = 25.5 hours

### Phase 2: Word Count Expansion (High) — 40 hours

**Priority modules (critically short):**

| Module | Current | Target | Need |
|--------|---------|--------|------|
| M87 | 1,138 | 3,000 | +1,862 |
| M88 | 1,148 | 3,000 | +1,852 |
| M01-19 | ~2,200 avg | 4,000 | +1,800 each |

**Approach:**
1. Expand explanations and examples
2. Add more dialogue sections
3. Include additional practice scenarios

### Phase 3: Fix Activity Issues (Medium) — 15 hours

**3.1 Add missing activity types**
- Add `reading` activities to ~40 modules
- Add `cloze`, `error-correction`, `group-sort` as needed

**3.2 Remove forbidden activities from M50-54**
```bash
.venv/bin/python scripts/audit_module.py --fix curriculum/l2-uk-en/c1/{slug}.md
```

### Phase 4: Fix Outline Compliance (Medium) — 10 hours

**Option A:** Update plans to match content structure
**Option B:** Restructure content to match plans

**Recommendation:** Option A (less disruptive)

### Phase 5: Fix Template Violations (Low) — 5 hours

- Review ~15 modules with template issues
- Fix pedagogy field mismatches
- Add missing frontmatter fields

### Phase 6: Run Naturalness Validation (Low) — 4 hours

```bash
# Via MCP server
.venv/bin/python scripts/validate_naturalness.py c1
```

---

## Implementation Checklist

### Phase 1: Vocabulary (Week 1-2) — 25 hours
- [ ] Create vocabulary YAML for checkpoints (5 files)
- [ ] Create vocabulary YAML for M01-20 (16 files)
- [ ] Create vocabulary YAML for M21-35 (14 files)
- [ ] Create vocabulary YAML for M36-55 (18 files)
- [ ] Create vocabulary YAML for M56-91 (32 files)
- [ ] Create vocabulary YAML for M92-105 (13 files)

### Phase 2: Word Count (Week 3-4) — 40 hours
- [ ] Expand M87-88 (critical: +1,850 words each)
- [ ] Expand M01-19 Academic modules
- [ ] Expand M21-35 Professional modules
- [ ] Expand checkpoints to meet targets

### Phase 3: Activities (Week 5) — 15 hours
- [ ] Add reading activities to ~40 modules
- [ ] Add missing cloze/error-correction activities
- [ ] Remove forbidden activities from M50-54

### Phase 4: Outline Compliance (Week 6) — 10 hours
- [ ] Update plans for Academic phase (M01-20)
- [ ] Update plans for Professional phase (M21-35)
- [ ] Update plans for remaining phases

### Phase 5: Templates (Week 6) — 5 hours
- [ ] Fix 15 modules with template violations

### Phase 6: Naturalness (Week 7) — 4 hours
- [ ] Run MCP validation
- [ ] Fix any flagged issues

---

## Success Criteria (10/10)

| Criterion | Requirement |
|-----------|-------------|
| Audit pass rate | 106/106 modules passing (100%) |
| Vocabulary | All modules have vocabulary YAML |
| Word counts | All modules meet phase targets |
| Activities | All required types present |
| State Standard | Каталог В verified |
| Naturalness | All modules 8+/10 |

---

## Estimated Total Effort

| Phase | Hours | Priority |
|-------|-------|----------|
| Phase 1: Vocabulary | 25 | Critical |
| Phase 2: Word Count | 40 | High |
| Phase 3: Activities | 15 | Medium |
| Phase 4: Outline | 10 | Medium |
| Phase 5: Templates | 5 | Low |
| Phase 6: Naturalness | 4 | Low |
| **Total** | **99 hours** | — |

---

## C1 Scorecard Summary

| Criterion | Score | Notes |
|-----------|-------|-------|
| Grammar coverage | 8/10 | Comprehensive plans |
| Vocabulary coverage | 0/10 | Only 4/106 files exist |
| Skills coverage | 7/10 | Plans exist |
| State Standard compliance | 7/10 | Needs verification |
| CEFR C1 alignment | 7/10 | Plans aligned |
| Internal consistency | 5/10 | Outline mismatches |
| Audit pass rate | 0/10 | 0% passing |
| **Overall** | **1.8/10** | Blocked by vocabulary gate |

---

## References

- `docs/C1-STATUS.md` - Current audit status
- `claude_extensions/quick-ref/c1.md` - C1 workflow
- `docs/l2-uk-en/STATE-STANDARD-COMPLIANCE-ANALYSIS.md`
