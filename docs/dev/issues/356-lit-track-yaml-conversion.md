# Issue #356: LIT Track YAML Conversion

**Status:** 📋 OPEN
**Priority:** MEDIUM
**Created:** 2026-01-02
**Assigned to:** TBD (awaiting agent assignment)

## Problem Statement

The LIT (Ukrainian Literature & Classics) track modules have not been converted to the YAML architecture used by A1, A2, B1, and B2 levels. Currently:

- **14 LIT modules** exist in `curriculum/l2-uk-en/lit/` (M01-M14)
- Activities are **embedded in markdown** as "Завдання" sections (not extracted to YAML)
- Vocabulary uses **3-column specialized format** (different from 6-column standard)
- Modules are **not validated** by the audit pipeline
- **No MDX/JSON generation** for Docusaurus or Vibe app

This inconsistency blocks:
- Unified pipeline processing across all levels
- Activity validation and quality checks
- Vocabulary enrichment workflows
- Consistent output generation

## Scope

### LIT Modules Inventory

| Module | Title | Status |
|--------|-------|--------|
| 01 | Феномен Івана Котляревського | ❌ Not converted |
| 02 | Енеїда - Частина 1 | ❌ Not converted |
| 03 | Енеїда - Бенкет | ❌ Not converted |
| 04 | Енеїда - Війна | ❌ Not converted |
| 05 | Наталка Полтавка | ❌ Not converted |
| 06 | Квітка - Біографія | ❌ Not converted |
| 07 | Маруся | ❌ Not converted |
| 08 | Конотопська відьма | ❌ Not converted |
| 09 | Етнографія | ❌ Not converted |
| 10 | Квітка - Мова | ❌ Not converted |
| 11 | Молодий Шевченко | ❌ Not converted |
| 12 | Балади | ❌ Not converted |
| 13 | Гайдамаки | ❌ Not converted |
| 14 | Сон | ❌ Not converted (deleted from git) |

**Total:** 14 modules (13 active + 1 deleted)

### Current LIT Module Structure

**Frontmatter:** ✅ Standard (phase, tags, objectives, grammar, audio)

**Vocabulary:** ⚠️ Non-standard 3-column format
```markdown
# Словник

| Термін/Слово | Визначення та Етимологія | Коментар Патріота (Контекст XVIII ст.) |
|--------------|--------------------------|----------------------------------------|
| **Руїна (духовна)** | *Період занепаду...* | Стан суспільства... |
```

**Activities:** ❌ Embedded in markdown (not YAML)
```markdown
## Завдання 1: Есе-Роздум (Critical Writing)
**Тип:** Творче завдання

Напишіть есе (300-400 слів) на тему...
```

**Content:** ✅ Fully immersed Ukrainian (literary analysis, historical context)

## Proposed Solution

### Architecture Decision Required

**Option A: Full YAML Conversion (Recommended)**
- Convert activities to YAML format (match A1/A2/B1/B2 pattern)
- Keep vocabulary 3-column format (specialized for literary terms)
- Enable full pipeline processing
- **Pros:** Consistency, validation, quality checks
- **Cons:** 20-30 hours conversion work (14 modules × 1.5-2 hours each)

**Option B: Hybrid Approach**
- Keep activities in markdown (literary modules are essay-based, not quiz-based)
- Add minimal YAML validation
- Partial pipeline support
- **Pros:** Faster (5-10 hours)
- **Cons:** Inconsistent architecture, limited validation

**Option C: Defer Until C2**
- Complete B2 and C1 first
- Convert LIT track after C2 completion
- **Pros:** Focus on core curriculum
- **Cons:** LIT modules remain orphaned

## Recommended Approach: Option A (Full YAML Conversion)

### Implementation Plan (6 Phases)

**Phase 1:** ✅ Analysis & Inventory (Completed)
- Audit all 14 LIT modules
- Catalog activity types (essays, debates, short responses)
- Identify vocabulary enrichment needs
- Create conversion strategy document

**Phase 2:** ✅ YAML Schema Design (Completed)
- Design activity YAML format for literary modules
- Types: `essay`, `debate`, `short-response`, `analysis`, `comparison`
- Handle long-form essay prompts (300-400 words)
- Define rubric structure for grading criteria

**Phase 3:** 🔄 Activity Extraction (Started)
- **Pilot:** `01-introduction-to-kotliarevsky` converted successfully.
- Extract activities from 14 modules to YAML
- Estimated: 14 modules × 3-5 activities × 15 min = 10-12 hours
- Validate YAML structure
- Test with sample module

**Phase 4:** ⏳ Vocabulary Decision (2 hours)
- **Decision:** Keep 3-column format or convert to 6-column?
- If keeping 3-column: Update audit to accept both formats
- If converting: Enrich with IPA, POS, Gender (like A1/A2/B1/B2)
- **Recommendation:** Keep 3-column (specialized literary terminology)

**Phase 5:** ⏳ Pipeline Integration (4 hours)
- Update `scripts/generate_mdx.py` to handle LIT modules
- Update `scripts/generate_json.py` for LIT output
- Update `scripts/audit_module.py` to validate LIT format
- Add LIT to `scripts/pipeline.py`
- Test full pipeline: `npm run pipeline l2-uk-en lit`

**Phase 6:** ⏳ Validation & Documentation (2 hours)
- Run audit on all 14 LIT modules
- Generate MDX for Docusaurus
- Generate JSON for Vibe app
- Update documentation:
  - `docs/ARCHITECTURE.md` - Add LIT track
  - `docs/MARKDOWN-FORMAT.md` - Document LIT activity types
  - `CLAUDE.md` - Add LIT workflow

**Total estimated effort:** 24 hours (3 full days)

## Acceptance Criteria

- [ ] All 14 LIT modules converted to YAML activity format
- [ ] Vocabulary format decision made and implemented
- [ ] Audit pipeline validates LIT modules
- [ ] MDX generation works for LIT track
- [ ] JSON generation works for LIT track
- [ ] Full pipeline runs: `npm run pipeline l2-uk-en lit`
- [ ] Documentation updated (3 files)
- [ ] At least 1 sample module tested end-to-end

## Activity Types for LIT Track

**Literary analysis activities (different from A1/A2/B1/B2):**

1. **essay** - Long-form critical writing (300-500 words)
   - Rubric: thesis, evidence, analysis, conclusion
   - Example: "Есе-Роздум" on Kotliarevsky's legacy

2. **debate** - Structured discussion prompt
   - Rubric: argument, counterargument, evidence
   - Example: "Історична Дискусія" on Masepa's choices

3. **short-response** - Brief analytical answer (100-200 words)
   - Rubric: clarity, evidence, interpretation
   - Example: "Аналіз Цитати" from Eneida

4. **analysis** - Close reading of text passage
   - Rubric: language analysis, context, interpretation
   - Example: Analyzing Shevchenko's poetic technique

5. **comparison** - Compare two works/authors/periods
   - Rubric: similarities, differences, synthesis
   - Example: Kotliarevsky vs. European mock-epic tradition

## Dependencies

- ✅ YAML architecture established (A1/A2/B1/B2 complete)
- ✅ Pipeline tools exist (`generate_mdx.py`, `generate_json.py`, `audit_module.py`)
- ⏳ Activity type definitions for literary modules (Phase 2)

## References

- **LIT modules:** `curriculum/l2-uk-en/lit/`
- **Sample module:** `lit/01-introduction-to-kotliarevsky.md`
- **YAML architecture:** See A1/A2/B1/B2 `activities/` folders
- **Activity reference:** `docs/ACTIVITY-MARKDOWN-REFERENCE.md`

## Notes

- **LIT track is post-C1** - Advanced literary analysis for proficient learners
- **Different pedagogy** - Essay-based, not quiz-based (requires new activity types)
- **3-column vocabulary** - Specialized format may be retained (literary terminology needs context)
- **User feedback:** "we forgot to convert LIT please create an issue about that"
- **Conversion can happen in parallel** with C1/C2 work (independent track)

## Next Steps

1. **Assign agent** for Phase 1 (analysis & inventory)
2. **Make architecture decision** (Option A/B/C)
3. Design YAML schema for literary activities (Phase 2)
4. Begin conversion (Phase 3)

---

**Created by:** C1-a (Coordinator)
**Date:** 2026-01-02
