# B1 Rebuild - Audit Summary & Action Plan

**Date:** 2026-01-10
**Total Modules:** 91
**Audit Pass Rate:** 11.0% (10 passed, 81 failed)

---

## Executive Summary

The B1 level audit reveals **systematic issues** across 81 of 91 modules (89% failure rate). The good news: **only 10 modules are clean**, meaning the errors follow predictable patterns that can be batch-fixed.

### Critical Finding

**B1 was built with inconsistent template adherence**, likely because:
1. Templates evolved after modules were written
2. Modules 01-05 (metalanguage) follow different templates than 06+ (immersed)
3. Cultural/vocabulary modules (52-91) follow different templates than grammar modules (06-51)

---

## Error Categories (By Frequency)

### 1. Word Count Issues (565 occurrences, 51 modules)

**Problem:** Unjumble sentences fall below B1 complexity targets (12-16 words).

**Pattern:**
- Primarily in `unjumble` activities
- Most violations are 8-11 words instead of 12-16
- Affects grammar modules more than vocabulary modules

**Example:**
```
❌ Current: "Я вчора прочитав цікаву книгу про історію" (8 words)
✅ Required: "Я вчора прочитав дуже цікаву книгу про українську історію, яку мені порадив друг" (14 words)
```

**Fix Strategy:**
- Batch script to identify all short unjumble sentences
- Extend sentences with subordinate clauses, adjectives, adverbial phrases
- Re-audit after batch fix

---

### 2. YAML Schema Violations (290 occurrences, 81 modules)

**Problem:** Activity YAML files don't match the JSON schema.

**Most Common Violations:**
1. **Missing `correct_words` in mark-the-words** (20+ modules)
2. **Empty `items` arrays** (activity has 0 items)
3. **Invalid field names** (e.g., `correct_answers` instead of `correct`)
4. **Missing required fields** (e.g., `options` in error-correction)

**Example:**
```yaml
# ❌ INVALID
mark-the-words:
  - title: "Знайдіть дієслова"
    text: "Я читаю книгу..."
    # Missing: correct_words

# ✅ VALID
mark-the-words:
  - title: "Знайдіть дієслова"
    text: "Я читаю книгу..."
    correct_words: ["читаю"]
```

**Fix Strategy:**
- Run schema validator on all B1 activity YAML files
- Batch fix missing fields using template injection
- Verify against `schemas/activities-base.schema.json`

---

### 3. Empty Required Sections (150 occurrences, 81 modules)

**Problem:** Required template sections exist but are empty.

**Most Common Empty Sections:**
1. `## Потрібно більше практики?` (practice resources callout)
2. `## Граматична довідка` (grammar reference for checkpoint modules)

**Pattern:**
- These sections were added to the templates AFTER modules were written
- Modules have the headers but no content

**Fix Strategy:**
- **Option A:** Remove empty sections (if truly optional)
- **Option B:** Generate standard content for each section type
- **Option C:** Mark as optional in template (update schema)

---

### 4. Missing Required Sections (150 occurrences, 42 modules)

**Problem:** Template-required sections are completely absent.

**Most Common Missing Sections:**
1. `## Граматична таблиця` (grammar table in grammar modules)
2. `## Спостерігайте` (inductive observation section)
3. `## Культурний контекст` (cultural context in cultural modules)

**Affected Module Types:**
- **Checkpoint modules:** Missing grammar reference sections
- **Motion verb modules (M16-25):** Missing motion verb tables
- **Cultural modules (M72-91):** Missing cultural context sections

**Fix Strategy:**
- Identify which sections are truly required vs. nice-to-have
- Generate missing sections from module content
- Update templates if sections should be optional

---

### 5. Activity Density Below Minimum (58 modules)

**Problem:** Modules have fewer activity items than required.

**B1 Density Requirements:**
- Grammar modules: 14 items/activity
- Vocabulary modules: 12 items/activity
- Checkpoint modules: 16 items/activity

**Pattern:**
- Many modules have 10-12 items when 14+ required
- Some mark-the-words activities have 0 items (empty text)

**Fix Strategy:**
- Batch expand activities to meet density targets
- Prioritize checkpoint modules (most critical)
- Use vocabulary from module's vocabulary section

---

### 6. Activity Count Below Minimum (45 modules)

**Problem:** Modules have 10-11 activities instead of required 12.

**B1 Activity Requirements:**
- Grammar modules: 12 activities
- Vocabulary modules: 10 activities
- Checkpoint modules: 14 activities

**Fix Strategy:**
- Add missing activities (prioritize diverse activity types)
- Ensure required mix: quiz, fill-in, unjumble, error-correction, cloze, mark-the-words
- Verify against `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`

---

### 7. Duplicate/Synonymous Headers (48 occurrences, 24 modules)

**Problem:** Multiple sections with similar names or content.

**Examples:**
- `## Практика` and `## Додаткова практика`
- `## Граматика` and `## Граматичні правила`

**Fix Strategy:**
- Merge duplicate sections
- Standardize section naming per template
- Update section detection logic if false positives

---

### 8. Section Order Violations (42 occurrences, 22 modules)

**Problem:** Sections appear in wrong order relative to template.

**Expected Order (Grammar Module):**
1. Граматична таблиця
2. Спостерігайте
3. Правило
4. Практика
5. Словник
6. Активності

**Affected Modules:**
- Primarily vocabulary modules (M52-71)
- Some cultural modules (M72-91)

**Fix Strategy:**
- Reorder sections to match template
- Validate against template order schema
- Ensure content quality preserved during reordering

---

### 9. Low Immersion (19 modules)

**Problem:** English content exceeds 15% threshold (B1.2+ target: 85-100% Ukrainian).

**Affected Modules:**
- Motion verb modules (M17-24)
- Some complex sentence modules (M29-32)

**Pattern:**
- English translations in activity titles
- English explanations in grammar sections
- English vocabulary notes

**Fix Strategy:**
- Remove English translations from immersed sections
- Keep English only in vocabulary tables (Переклад column)
- Target: 95%+ immersion for B1.2+ modules

---

### 10. Too Many Morphemes (24 modules)

**Problem:** Fill-in blanks contain multi-morpheme words (compound words, prefixed verbs).

**B1 Constraint:** Fill-in should target single morphemes (root + inflection, not derived forms).

**Examples:**
```
❌ перечитати (пере- + читати, 2 morphemes)
✅ читати (1 morpheme)
```

**Fix Strategy:**
- Review flagged fill-in activities
- Simplify to single-morpheme targets
- Move complex forms to unjumble or error-correction

---

## Modules That Pass (10 Total)

These modules are **production-ready**:

1. `01-how-to-talk-about-grammar` ✅
2. `02-language-about-verbs` ✅
3. `03-reading-grammar-rules` ✅
4. `04-sentence-structure` ✅
5. `05-ready-for-immersion` ✅
6. `06-aspect-complete-system` ✅
7. `07-aspect-past-single-repeated` ✅
8. `08-aspect-past-result-process` ✅
9. `09-aspect-future` ✅
10. `10-aspect-negation` ✅

**Pattern:** Metalanguage modules (M01-05) and early aspect modules (M06-10) pass because they were recently reviewed/rewritten.

---

## Action Plan: Batch Fix Strategy

### Phase 1: Schema & Structure (High Priority)

**Goal:** Fix YAML schema violations and missing/empty sections.

```bash
# 1. Fix YAML schema violations
npm run fix:yaml-schema l2-uk-en b1

# 2. Populate empty required sections
npm run fix:empty-sections l2-uk-en b1

# 3. Add missing required sections
npm run fix:missing-sections l2-uk-en b1

# 4. Reorder sections to match templates
npm run fix:section-order l2-uk-en b1
```

**Expected Impact:** Fixes ~450 errors across 81 modules.

---

### Phase 2: Activity Quality (Medium Priority)

**Goal:** Ensure activities meet density and count requirements.

```bash
# 1. Expand activities to meet density targets
npm run fix:activity-density l2-uk-en b1

# 2. Add missing activities to reach minimum count
npm run fix:activity-count l2-uk-en b1

# 3. Fix word count in unjumble sentences
npm run fix:unjumble-complexity l2-uk-en b1
```

**Expected Impact:** Fixes ~280 errors (activity count + density + word count).

---

### Phase 3: Immersion & Pedagogy (Low Priority)

**Goal:** Improve immersion and pedagogical quality.

```bash
# 1. Remove English from immersed sections
npm run fix:immersion l2-uk-en b1

# 2. Simplify fill-in morphemes
npm run fix:morpheme-complexity l2-uk-en b1

# 3. Merge duplicate headers
npm run fix:duplicate-headers l2-uk-en b1
```

**Expected Impact:** Fixes ~90 errors (immersion + morphemes + duplicates).

---

### Phase 4: Re-Audit & Validation

```bash
# Re-run audit on all B1 modules
.venv/bin/python scripts/audit_level.py l2-uk-en b1

# Run full pipeline to validate
npm run pipeline l2-uk-en b1
```

**Target:** 95%+ pass rate after batch fixes.

---

## Recommended Priorities

### Immediate (This Week)

1. **Fix YAML schema violations** → Blocks activity rendering
2. **Add missing sections** → Blocks template compliance
3. **Fix activity count/density** → Blocks richness gates

### Short-term (Next Week)

4. **Fix word count issues** → Improves pedagogical quality
5. **Fix section order** → Template compliance
6. **Remove duplicate headers** → Content cleanup

### Long-term (Post-B1)

7. **Improve immersion** → Quality enhancement
8. **Fix morpheme complexity** → Pedagogical refinement

---

## Template Alignment Recommendations

### Update Templates (If Appropriate)

Some "violations" may indicate templates are too strict:

1. **"Потрібно більше практики?" section** → Consider making optional
2. **Checkpoint grammar reference** → Generate automatically from previous modules
3. **Cultural context sections** → Define minimum content requirements

### Update Schema (If Appropriate)

Some YAML violations may indicate schema needs updating:

1. **mark-the-words `correct_words`** → Should be required (keep as-is)
2. **Activity item minimums** → Validate against current richness guidelines

---

## Scripts to Implement

**Priority 1: Schema & Structure**

```bash
scripts/fix/yaml_schema_validator.py      # Fix YAML schema violations
scripts/fix/populate_empty_sections.py    # Add content to empty sections
scripts/fix/add_missing_sections.py       # Generate missing sections
scripts/fix/reorder_sections.py           # Fix section order
```

**Priority 2: Activity Quality**

```bash
scripts/fix/expand_activity_density.py    # Add items to activities
scripts/fix/add_activities.py             # Add missing activities
scripts/fix/extend_unjumble_sentences.py  # Increase word count
```

**Priority 3: Quality Enhancements**

```bash
scripts/fix/remove_english.py             # Improve immersion
scripts/fix/simplify_fillins.py           # Reduce morpheme complexity
scripts/fix/merge_duplicate_headers.py    # Clean up structure
```

---

## Next Steps

1. **Review this summary** → Confirm priorities and approach
2. **Implement Phase 1 scripts** → Schema & structure fixes
3. **Test on sample modules** → Validate fixes (modules 11-15)
4. **Batch apply to all B1** → Run fixes on all 81 failing modules
5. **Re-audit** → Validate 95%+ pass rate
6. **Run pipeline** → Generate MDX and validate HTML

**Estimated Time:**
- Phase 1: 2-3 days
- Phase 2: 2-3 days
- Phase 3: 1-2 days
- Re-audit & validation: 1 day

**Total:** ~1-2 weeks for full B1 rebuild compliance.

---

## Questions for Review

1. **Empty sections:** Should `## Потрібно більше практики?` be required or optional?
2. **Missing sections:** Should checkpoint modules auto-generate grammar reference sections?
3. **Immersion threshold:** Should motion modules (M17-24) have lower immersion targets due to complexity?
4. **Morpheme complexity:** Should fill-in allow prefixed motion verbs (при-йти, ви-йти)?

---

## Appendix: Detailed Module Status

**Pass (10 modules):**
- M01-05 (Metalanguage) ✅
- M06-10 (Aspect intro) ✅

**Fail - High Priority (45 modules):**
- M11-15 (Aspect continuation)
- M16-25 (Motion verbs)
- M26-34 (Complex sentences I)
- M35-41 (Complex sentences II)
- M42-51 (Advanced grammar)

**Fail - Medium Priority (22 modules):**
- M52-71 (Vocabulary expansion)

**Fail - Low Priority (14 modules):**
- M72-91 (Cultural & integration modules)

---

**Full detailed error report:** `docs/issues/b1-rebuild-audit-report.md` (473KB)
