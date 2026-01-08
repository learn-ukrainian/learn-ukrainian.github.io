# EPIC: Dobra Forma Verb Pedagogy Redesign

**Status:** 🚧 In Progress  
**Scope:** A1 verb modules + A2 imperative compliance

---

## Progress Summary

| Phase | Issue | Status | Description |
|-------|-------|--------|-------------|
| 1 | #380 | ✅ DONE | Update curriculum plans |
| 2 | #383 | ✅ DONE | A1 module updates (terminology, reflexives) |
| 3 | #384 | ✅ DONE | A2 Complete Imperative (M23 inserted, M23-M57 → M24-M58) |
| 4 | #385 | ✅ CLOSED | Superseded by #384 |
| 5 | #386 | ❌ CANCELLED | Checkpoint updates not needed |
| 6 | #387 | 🚧 IN PROGRESS | Regenerate & validate (A1 + A2) |
| 7 | #388 | ⏳ PENDING | Documentation updates |
| 8 | #389 | ⏳ PENDING | Final testing & deployment |

---

## Current Focus: Issue #387 (A2 Validation)

**Progress (2026-01-06):**
- Fixed 40 mark-the-words activities (added missing `answers` field)
- Fixed 3 translate activities (`english` → `source` field name)
- Fixed 1 true-false activity (`answer` → `correct` field name)
- A2 pass rate: **20.7%** (12/58 modules passing)

**Remaining A2 Issues (46 modules):**
| Issue Type | Count | Fix Approach |
|------------|-------|--------------|
| Pedagogy violations | 20 | match-up complexity, metalanguage |
| Activity count | 12 | Add missing activities |
| Density issues | 14 | Add items to low-density activities |
| Table formatting | ~10 | Fix column mismatches |

---

## Completed Work

### Phase 2: A1 Module Updates (#383) ✅

All 6 A1 modules updated for Ukrainian State Standard 2024 compliance:
- M06: First conjugation terminology + працювати-type section
- M08: Second conjugation terminology
- M09: Complete replacement (Food → Reflexive Verbs)
- M18: Food, Drinks & Shopping (expanded with merged vocabulary)
- M21: Added -ва- returns note, aspect awareness, reflexive past
- M22: Added aspect awareness, synthetic future recognition

### Phase 3: A2 Complete Imperative (#384) ✅

- Inserted M23: Complete Imperative (Наказовий спосіб)
- Renumbered M23-M57 → M24-M58 (175 files)
- A2 now has 58 modules
- M23 covers: 2nd person, 1st plural (-мо), 3rd person (хай/нехай), irregular forms

---

## Ukrainian State Standard 2024 Compliance

| Requirement | Level | Status |
|-------------|-------|--------|
| Reflexive verbs (дивитися, сміятися) | A1 | ✅ M09 |
| 3rd person imperative (хай/нехай) | A2 | ✅ M23 |
| 2nd person imperative formation | A2 | ✅ M23 |
| 1st plural imperative (-мо forms) | A2 | ✅ M23 |

---

## Next Steps

1. Complete A2 validation (#387) - fix remaining 46 modules
2. Update documentation (#388)
3. Final testing & deployment (#389)

---

## References

- Dobra Forma analysis: `docs/l2-uk-en/DOBRA-FORMA-VERB-PEDAGOGY-ANALYSIS.md`
- Ukrainian State Standard 2024: `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt`
