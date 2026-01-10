# B1 Audit - Quick Summary

**Date:** 2026-01-10
**Status:** 10/91 modules pass (11% pass rate)

---

## Error Summary Table

| Error Category | Count | Modules | Description |
|---|---:|---:|---|
| Word Count Issues | 565 | 51 | Unjumble/quiz sentences too short |
| YAML Schema Violations | 290 | 81 | Missing required fields in activities |
| Empty Required Sections | 150 | 81 | Template sections exist but empty |
| Missing Required Sections | 150 | 42 | Template sections completely absent |
| Activity Density Below Min | 58 | 58 | Activities have too few items |
| Duplicate Headers | 48 | 24 | Multiple similar section names |
| Activity Count Below Min | 45 | 45 | Fewer than 12 activities |
| Section Order Issues | 42 | 22 | Sections in wrong order |
| Too Many Morphemes | 24 | 24 | Fill-in targets too complex |
| Low Immersion | 19 | 19 | English content exceeds 15% |

**Total:** 1,391 violations across 81 modules (avg 17.2 violations per module)

---

## Top 5 Issues (By Frequency)

### 1. Word Count Issues (565 occurrences)
- **Problem:** Unjumble sentences too short (8-11 words instead of 12-16)
- **Modules affected:** 51
- **Fix:** Extend sentences with subordinate clauses

### 2. YAML Schema Violations (290 occurrences)
- **Problem:** Missing required fields in activity YAML
- **Most common:** Missing `correct_words` in mark-the-words
- **Modules affected:** 81
- **Fix:** Add missing fields per JSON schema

### 3. Empty Required Sections (150 occurrences)
- **Problem:** Template sections exist but have no content
- **Most common:** `## Потрібно більше практики?`
- **Modules affected:** 81
- **Fix:** Populate or remove sections

### 4. Missing Required Sections (150 occurrences)
- **Problem:** Template sections completely absent
- **Most common:** `## Граматична таблиця`, `## Спостерігайте`
- **Modules affected:** 42
- **Fix:** Generate missing sections

### 5. Activity Density Below Min (58 modules)
- **Problem:** Activities have 10-12 items instead of 14+
- **Fix:** Expand activities to meet density targets

---

## Status by Module Range

```
M01-10 (Metalanguage + Aspect)      [10/10] ✅✅✅✅✅✅✅✅✅✅ 100%
M11-15 (Aspect cont.)               [ 0/ 5] ❌❌❌❌❌❌❌❌❌❌ 0%
M16-25 (Motion Verbs)               [ 0/10] ❌❌❌❌❌❌❌❌❌❌ 0%
M26-34 (Complex Sentences I)        [ 0/ 9] ❌❌❌❌❌❌❌❌❌❌ 0%
M35-41 (Complex Sentences II)       [ 0/ 7] ❌❌❌❌❌❌❌❌❌❌ 0%
M42-51 (Advanced Grammar)           [ 0/10] ❌❌❌❌❌❌❌❌❌❌ 0%
M52-71 (Vocabulary)                 [ 0/20] ❌❌❌❌❌❌❌❌❌❌ 0%
M72-91 (Cultural/Integration)       [ 0/20] ❌❌❌❌❌❌❌❌❌❌ 0%
```

**Key Finding:** Only M01-10 pass. All modules after M10 require fixes.

## Modules That Pass (10)

✅ **M01-10** (Metalanguage + early aspect modules)
- 01-how-to-talk-about-grammar
- 02-language-about-verbs
- 03-reading-grammar-rules
- 04-sentence-structure
- 05-ready-for-immersion
- 06-aspect-complete-system
- 07-aspect-past-single-repeated
- 08-aspect-past-result-process
- 09-aspect-future
- 10-aspect-negation

---

## Impact Analysis (Priority Ranking)

**Priority calculated by:** Error Count × Severity

| Error | Count | Modules | Severity | Impact | Priority |
|---|---:|---:|:---:|---:|:---:|
| YAML Schema Violations | 290 | 81 | 10/10 | 2,900 | 🔴 P1 |
| Word Count Issues | 565 | 51 | 3/10 | 1,695 | 🔴 P1 |
| Missing Required Sections | 150 | 42 | 8/10 | 1,200 | 🔴 P1 |
| Empty Required Sections | 150 | 81 | 7/10 | 1,050 | 🟡 P2 |
| Activity Density Below Min | 58 | 58 | 9/10 | 522 | 🟡 P2 |
| Activity Count Below Min | 45 | 45 | 9/10 | 405 | 🟡 P2 |
| Duplicate Headers | 48 | 24 | 5/10 | 240 | 🟢 P3 |
| Section Order Issues | 42 | 22 | 4/10 | 168 | 🟢 P3 |
| Low Immersion | 19 | 19 | 6/10 | 114 | 🟢 P3 |
| Too Many Morphemes | 24 | 24 | 3/10 | 72 | 🟢 P3 |

**Severity Scoring:**
- 10 = Critical (blocks functionality)
- 7-9 = High (blocks compliance/gates)
- 4-6 = Medium (affects quality)
- 1-3 = Low (minor improvements)

---

## Batch Fix Strategy

### Phase 1: Schema & Structure (Priority 1)
```bash
# Fix YAML schema violations
npm run fix:yaml-schema l2-uk-en b1

# Populate empty sections
npm run fix:empty-sections l2-uk-en b1

# Add missing sections
npm run fix:missing-sections l2-uk-en b1
```
**Impact:** Fixes ~450 errors

### Phase 2: Activity Quality (Priority 2)
```bash
# Expand activity density
npm run fix:activity-density l2-uk-en b1

# Fix word count in unjumble
npm run fix:unjumble-complexity l2-uk-en b1

# Add missing activities
npm run fix:activity-count l2-uk-en b1
```
**Impact:** Fixes ~280 errors

### Phase 3: Re-Audit
```bash
.venv/bin/python scripts/audit_level.py l2-uk-en b1
npm run pipeline l2-uk-en b1
```
**Target:** 95%+ pass rate

---

## Example Errors

### Module 11 (aspect-in-imperatives)
```
❌ YAML schema: Missing 'correct_words' in mark-the-words
❌ Empty section: "## Потрібно більше практики?"
❌ Activity count: 11/12 (need 1 more)
❌ Density: 1 activity with 0 items (need 6)
⚠️  Word count: 5 unjumble sentences too short
```

### Module 52 (abstract-concepts-ideas)
```
❌ YAML schema: 2 violations
❌ Missing sections: "## Граматика", "## Практика"
❌ Duplicate headers: "Вступ" + "Українські контексти"
❌ Density: 1 activity below minimum
⚠️  Word count: 13 quiz/unjumble items too short
```

---

## Timeline Estimate

- **Phase 1 (Schema/Structure):** 2-3 days
- **Phase 2 (Activity Quality):** 2-3 days
- **Phase 3 (Re-audit):** 1 day

**Total:** 1-2 weeks for 95%+ pass rate

---

## Full Reports

- **Detailed audit output:** `docs/issues/b1-rebuild-audit-report.md` (473KB)
- **Comprehensive analysis:** `docs/issues/b1-rebuild-audit-summary.md`
