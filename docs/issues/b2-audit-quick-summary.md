# B2 Audit Quick Summary

**Date:** 2026-01-10
**Status:** 🚨 CRITICAL - Only 1.4% pass rate
**Total Modules:** 145
**Passed:** 2 (102-franko-lesia-hrinchenko, 105-unr-zunr)
**Failed:** 143

---

## Top Error Categories

| Error Type | Count | Severity | Impact |
|------------|-------|----------|--------|
| `COMPLEXITY_WORD_COUNT` | 3,030 | ⚠️ Moderate | Sentences too short for B2 level |
| `YAML_SCHEMA_VIOLATION` | 734 | 🔴 Critical | Activities won't render correctly |
| `MISSING_REQUIRED_SECTION` | 663 | 🔴 Critical | Template non-compliance |
| `DUPLICATE_SYNONYMOUS_HEADERS` | 88 | 🔴 Critical | Structural issues |
| `MISSING_REQUIRED_CALLOUT` | 47 | ⚠️ Moderate | Missing pedagogical elements |
| `TOO_MANY_MORPHEMES` | 39 | ⚠️ Moderate | Vocabulary complexity issues |

---

## Critical Issues

### 1. MISSING_REQUIRED_SECTION (663 violations)

**Most common missing sections:**
- `Need More Practice?` - 277 modules (all module types)
- `Presentation|Grammar|Focus|Презентація|Граматика|Теорія` - 190 modules (grammar modules)
- `Читання` - 80 modules (history modules)
- `Warm-up|Introduction|Objectives|Контекст|Вступ|Розминка` - 76 modules
- `Первинні джерела` - 32 modules (history modules)
- `Деколонізаційний погляд` - 8 modules (history modules)

**Root Cause:** Modules created before template standardization (M71-131 history modules) + incomplete module scaffolding.

**Fix Strategy:**
- Add "Need More Practice?" section to ALL modules (automated script)
- Add missing grammar presentation sections (template-driven)
- Add missing history-specific sections (Читання, Первинні джерела, Деколонізаційний погляд)

---

### 2. YAML_SCHEMA_VIOLATION (734 violations)

**Most common schema errors:**
- **Array too short:** 20 occurrences (quiz/select options < 4)
- **Unexpected property `explanation`:** 8 occurrences (quiz items shouldn't have explanation)
- **Unexpected property `blank_index`:** 2 occurrences (fill-in schema mismatch)
- **Unexpected property `context`:** 2 occurrences (true-false schema mismatch)
- **Unexpected property `text`:** 2 occurrences (option schema mismatch)

**Root Cause:** Schema changes not applied to existing YAML files + manual YAML edits bypassing validation.

**Fix Strategy:**
- Run YAML schema migration script
- Remove invalid properties from quiz options
- Ensure all quiz/select activities have ≥4 options
- Validate all YAML against current schema

---

### 3. COMPLEXITY_WORD_COUNT (3,030 violations)

**Pattern:** Sentences in activities (quiz prompts, unjumble, fill-in) are too short for B2 complexity targets.

**B2 Targets:**
- Quiz prompts: 10-25 words
- Unjumble: 10-18 words
- Fill-in: 12-20 words

**Actual:** Many sentences are 3-9 words (A2/B1 complexity)

**Root Cause:** Activities created for earlier levels and not enriched for B2 complexity.

**Fix Strategy:**
- Enrich quiz prompts with dependent clauses
- Expand unjumble sentences with adverbial phrases
- Add contextual complexity to fill-in items

---

### 4. DUPLICATE_SYNONYMOUS_HEADERS (88 violations)

**Pattern:** Modules have multiple headers that alias to the same canonical section.

**Examples:**
- `Вступ` + `Контекст: Поділи Речі Посполитої` (both alias to "Warm-up/Introduction")
- `Граматика` + `Презентація` (both alias to "Grammar/Presentation")

**Root Cause:** Inconsistent header naming in history modules (M71-131).

**Fix Strategy:**
- Normalize headers to single canonical form per section
- Use template-defined header names

---

## Timeline Estimate

| Phase | Duration | Tasks |
|-------|----------|-------|
| **Phase 1: Automated Fixes** | 2-3 hours | Add missing sections, normalize headers, fix YAML schema |
| **Phase 2: Content Enrichment** | 8-12 hours | Expand sentence complexity (3,030 items) |
| **Phase 3: Manual Review** | 4-6 hours | History-specific sections (Читання, Первинні джерела) |
| **Phase 4: Validation** | 2-3 hours | Re-audit all 145 modules |
| **Total** | **16-24 hours** | Full B2 rebuild |

---

## Passing Modules (Learn From)

✅ **102-franko-lesia-hrinchenko** - Biography module, full template compliance
✅ **105-unr-zunr** - History module, full template compliance

**Analysis:** These modules were recently created/updated with current templates. Use as reference for fixing others.

---

## Next Steps

1. **Read detailed analysis:** `b2-rebuild-audit-summary.md`
2. **Review fix scripts:** `b2-fix-scripts-needed.md`
3. **Start Phase 1:** Automated structural fixes
4. **Validate progress:** Re-run audit after each phase

---

## Files

- `b2-rebuild-audit-report.md` - Full audit logs (643KB)
- `b2-audit-quick-summary.md` - This file
- `b2-rebuild-audit-summary.md` - Detailed error analysis
- `b2-fix-scripts-needed.md` - Implementation plan
- `b2-rebuild-index.md` - Navigation guide
