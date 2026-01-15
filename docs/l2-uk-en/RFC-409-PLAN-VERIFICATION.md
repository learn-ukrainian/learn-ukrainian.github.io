# RFC #409 Curriculum Plan Verification

**Date:** 2026-01-15
**Status:** ✅ Plans Complete (with one exception noted)

---

## Summary

All curriculum plans have been reviewed for completeness against RFC #409 Curriculum Reorganization requirements. The plans are complete and ready for module writing phase.

---

## Plan Verification Status

### Core Levels

| Level | Plan File | RFC #409 Modules | Status | Notes |
|-------|-----------|------------------|--------|-------|
| **A1** | A1-CURRICULUM-PLAN.md | M35-44 (10 practical) | ✅ Complete | Phase A1.4 fully specified |
| **A2** | A2-CURRICULUM-PLAN.md | M59-70 (12 practical) | ✅ Complete | Phase A2.7 fully specified |
| **B1** | B1-CURRICULUM-PLAN.md | M92-99 (8 skills) | ✅ Complete | Phase B1.9 fully specified |
| **B2** | B2-CURRICULUM-PLAN.md | M85-94 (10 professional) | ✅ Complete | Phase B2.4 fully specified |
| **C1** | C1-CURRICULUM-PLAN.md | 106 modules (core) | ⚠️ Needs Update | Still shows 202; biographies in C1-BIO |
| **C2** | C2-CURRICULUM-PLAN.md | 100 modules | ✅ Complete | No changes needed |

### Specialized Tracks

| Track | Plan File | Modules | Status | Notes |
|-------|-----------|---------|--------|-------|
| **B2-HIST** | B2-HIST-CURRICULUM-PLAN.md | 61 | ✅ Complete | All 61 meta files exist |
| **C1-BIO** | C1-BIO-CURRICULUM-PLAN.md | 96 | ✅ Complete | All 96 meta files exist |
| **B2-PRO** | B2-PRO-CURRICULUM-PLAN.md | 40 | ✅ Complete | All 40 modules specified |
| **C1-PRO** | C1-PRO-CURRICULUM-PLAN.md | 50 | ✅ Complete | All 50 modules specified |
| **LIT** | LIT-CURRICULUM-PLAN.md | 30 | ✅ Complete | 14 written, 16 planned |

---

## RFC #409 New Module Specifications

### A1 Phase A1.4: Practical Scenarios (M35-44)
- M35: At the Café
- M36: At the Restaurant
- M37: At the Market
- M38: At the Store
- M39: Buying Tickets
- M40: Taking Transport
- M41: Phone Basics
- M42: Introductions Extended
- M43: Emergency Basics
- M44: A1 Practical Checkpoint

### A2 Phase A2.7: Practical Scenarios (M59-70)
- M59: At the Doctor
- M60: At the Pharmacy
- M61-62: Accommodation (hotel, rental)
- M63-64: Scheduling (appointments, interviews)
- M65-66: Social situations
- M67-68: Modern communication
- M69: Combined practice
- M70: A2 Practical Checkpoint

### B1 Phase B1.9: Communication Skills (M92-99)
- M92: Email Writing Basics
- M93: Formal Letters
- M94: Informal Writing
- M95: Podcast Listening
- M96: Note-taking Skills
- M97: Discussion Skills
- M98: Debate Basics
- M99: B1 Skills Checkpoint

### B2 Phase B2.4: Communication Skills (M85-94)
- M85-86: Professional Email
- M87-88: Professional Reports
- M89-90: News Analysis
- M91-92: Presentation Skills
- M93: Combined Practice
- M94: B2 Communication Checkpoint

---

## CEFR Compliance Checklist

### A1 (Початковий рівень)
- [x] Can-do statements defined in plan
- [x] Grammar scope limited: Nom/Acc/Loc/Gen/Voc cases only
- [x] No Dative/Instrumental at A1
- [x] Vocabulary target: ~600 words
- [x] Practical scenarios for basic survival needs

### A2 (Базовий рівень)
- [x] All 7 cases introduced
- [x] Dative (M01) and Instrumental (M04) present
- [x] Full adjective declension
- [x] Aspect introduction (controlled)
- [x] Vocabulary target: ~1,100 new words

### B1 (Середній рівень)
- [x] Aspect mastery modules present
- [x] Motion verb system covered
- [x] Complex sentence formation
- [x] Communication skills added (RFC #409)
- [x] Vocabulary target: ~1,800 words

### B2 (Вищий середній рівень)
- [x] Passive voice system complete
- [x] Register differentiation (formal/informal/business/academic)
- [x] Professional communication basics (RFC #409)
- [x] Vocabulary target: ~2,000 words

### C1 (Просунутий рівень)
- [x] Academic foundation covered
- [x] Stylistics and rhetoric present
- [x] Folk culture and fine arts modules
- [x] Literature introduction
- [x] Vocabulary target: ~2,500 words

### C2 (Рівень вільного володіння)
- [x] Complete morphological mastery
- [x] Stylistic perfection focus
- [x] Creative production requirements
- [x] Native-level nuance activities
- [x] Vocabulary target: ~2,500 words

---

## Ukrainian State Standard 2024 Compliance

All curriculum plans reference and align with:
> **Source:** Українська мова як іноземна: рівні загального володіння та діагностика (2024)
> **Document:** `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt`

### Grammar Requirements (Каталог В)
- [x] Case system progression documented per level
- [x] Verb tense/aspect requirements met
- [x] Adjective/numeral/pronoun paradigms covered
- [x] Syntax complexity appropriate per level

### Thematic Requirements (Каталог Б)
- [x] Personal/family topics at A1
- [x] Professional/social topics at B1-B2
- [x] Abstract/academic topics at C1-C2

---

## Identified Issues

### C1 Curriculum Plan Update Needed

**Issue:** C1-CURRICULUM-PLAN.md still shows 202 modules and includes biographies (M36-131) that have been relocated to C1-BIO track.

**Required Action:** Update C1-CURRICULUM-PLAN.md to reflect RFC #409 reorganization:
- Change module count from 202 to 106
- Remove Phase C1.3: Biographies (M36-131) - now in C1-BIO
- Update Phase numbering:
  - C1.1: Academic Foundation (M01-20) - unchanged
  - C1.2: Professional & Social Context (M21-35) - unchanged
  - C1.4 → C1.3: Advanced Stylistics & Rhetoric (M36-55)
  - C1.5 → C1.4: Folk Culture & Fine Arts (M56-91)
  - C1.6 → C1.5: Literature (M92-106)

**Priority:** LOW - The actual module content and tracks are correct; only the plan document needs updating.

---

## Gap Analysis: No Content Gaps Remaining

After RFC #409, all identified gaps have been addressed:

| Gap Category | A1 | A2 | B1 | B2 | Status |
|--------------|----|----|----|----|--------|
| Practical scenarios | M35-44 | M59-70 | - | - | ✅ Filled |
| Communication skills | - | - | M92-99 | M85-94 | ✅ Filled |
| Professional content | - | - | - | B2-PRO | ✅ New track |
| History track | - | - | - | B2-HIST | ✅ Relocated |
| Biography track | - | - | - | C1-BIO | ✅ Relocated |

---

## Total Module Counts (Final)

| Path | Modules | Status |
|------|---------|--------|
| **A1 Core** | 44 | 34 written, 10 to write |
| **A2 Core** | 70 | 58 written, 12 to write |
| **B1 Core** | 99 | 91 written, 8 to write |
| **B2 Core** | 94 | 84 written, 10 to write |
| **C1 Core** | 106 | 106 written |
| **C2 Core** | 100 | 0 written |
| **B2-HIST** | 61 | 61 written |
| **C1-BIO** | 96 | 96 written |
| **B2-PRO** | 40 | 0 written |
| **C1-PRO** | 50 | 0 written |
| **LIT** | 30 | 14 written |
| **TOTAL** | **790** | 544 written, 246 to write |

---

## Recommendations

1. **Priority 1:** Write new practical scenario modules (A1 M35-44, A2 M59-70, B1 M92-99, B2 M85-94) - **40 modules total**
2. **Priority 2:** Update C1-CURRICULUM-PLAN.md to reflect reorganization
3. **Priority 3:** Write C2 modules (100 total)
4. **Priority 4:** Write professional tracks (B2-PRO 40, C1-PRO 50)
5. **Priority 5:** Complete LIT track (16 remaining)

---

*Last updated: 2026-01-15*
