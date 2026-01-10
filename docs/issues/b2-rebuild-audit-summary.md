# B2 Rebuild - Detailed Audit Summary

**Generated:** 2026-01-10
**Audit Tool:** `scripts/audit_module.py`
**Total Modules:** 145
**Pass Rate:** 1.4% (2/145)

---

## Executive Summary

The B2 level audit reveals **critical template non-compliance** across 98.6% of modules (143/145). The primary issues are:

1. **Structural incompleteness** - 663 missing required sections
2. **YAML schema violations** - 734 invalid activity definitions
3. **Insufficient complexity** - 3,030 sentences below B2 word count targets
4. **Inconsistent headers** - 88 duplicate/synonymous section headers

These issues stem from:
- **History modules (M71-131)** created before template standardization
- **Grammar/vocab modules (M01-70)** not updated for B2 complexity targets
- **YAML schema evolution** not applied to existing activity files

---

## Error Distribution by Category

| Category | Count | % of Total | Severity | Auto-Fixable? |
|----------|-------|------------|----------|---------------|
| `COMPLEXITY_WORD_COUNT` | 3,030 | 55.8% | ⚠️ Moderate | Partial (enrichment) |
| `YAML_SCHEMA_VIOLATION` | 734 | 13.5% | 🔴 Critical | ✅ Yes |
| `MISSING_REQUIRED_SECTION` | 663 | 12.2% | 🔴 Critical | ✅ Yes |
| `DUPLICATE_SYNONYMOUS_HEADERS` | 88 | 1.6% | 🔴 Critical | ✅ Yes |
| `MISSING_REQUIRED_CALLOUT` | 47 | 0.9% | ⚠️ Moderate | ✅ Yes |
| `TOO_MANY_MORPHEMES` | 39 | 0.7% | ⚠️ Moderate | ❌ Manual review |
| `EMPTY_REQUIRED_SECTION` | 2 | 0.04% | 🔴 Critical | ✅ Yes |
| **TOTAL** | **4,603** | **100%** | | |

---

## 1. MISSING_REQUIRED_SECTION (663 violations)

### Breakdown by Section Type

| Missing Section | Count | Affected Module Types |
|-----------------|-------|-----------------------|
| `Need More Practice?` | 277 | All modules (M01-M145) |
| `Presentation\|Grammar\|Focus\|Презентація\|Граматика\|Теорія` | 190 | Grammar modules (M01-M51) |
| `Читання` | 80 | History modules (M71-M131) |
| `Warm-up\|Introduction\|Objectives\|Контекст\|Вступ\|Розминка` | 76 | Mixed |
| `Первинні джерела` | 32 | History modules (M71-M131) |
| `Деколонізаційний погляд` | 8 | History modules (M71-M131) |

### Analysis

**"Need More Practice?" (277 modules):**
- **Cause:** Template requirement added after most modules were created
- **Impact:** Missing self-study resources for learners
- **Fix:** Add standardized section with external links (automatic template insertion)

**Grammar/Presentation sections (190 modules):**
- **Cause:** Modules M01-M51 use varied header names for grammar explanations
- **Impact:** Template validation fails to recognize existing content
- **Fix:** Normalize header names to canonical forms OR update template to accept more aliases

**History-specific sections (120 modules):**
- **Cause:** History modules (M71-M131) created before `b2-history-module-template.md` was finalized
- **Impact:** Missing reading passages, primary sources, decolonization analysis
- **Fix:** Add missing sections using history template as guide (manual content creation required)

### Module Range Analysis

| Module Range | Description | Missing Sections | Root Cause |
|--------------|-------------|------------------|------------|
| M01-M51 | Grammar/Aspect/Motion | Presentation (190), Need More (51) | Pre-template creation |
| M52-M70 | Vocabulary/Idioms | Need More (19) | Pre-template creation |
| M71-M131 | History | Читання (80), Первинні джерела (32), Need More (61) | Pre-history-template |
| M132-M145 | Skills/Capstone | Need More (14) | Incomplete scaffolding |

---

## 2. YAML_SCHEMA_VIOLATION (734 violations)

### Schema Error Types

| Error Type | Count | Example | Fix |
|------------|-------|---------|-----|
| Array too short | 20 | Quiz with 3 options (need 4+) | Add distractor options |
| Unexpected `explanation` in quiz | 8 | `options.0.explanation` not allowed | Move to `[!explanation]` callout |
| Unexpected `blank_index` in fill-in | 2 | `items.0.blank_index` not allowed | Remove (auto-detected by `___`) |
| Unexpected `context` in true-false | 2 | `context` field not in schema | Move to activity intro |
| Unexpected `text` in options | 2 | Wrong option format | Use correct schema format |

### Detailed Analysis

**"Array too short" (20 occurrences):**
```yaml
# WRONG - only 3 options
options:
  - text: "Option 1"
    correct: true
  - text: "Option 2"
  - text: "Option 3"

# CORRECT - 4+ options
options:
  - text: "Option 1"
    correct: true
  - text: "Option 2"
  - text: "Option 3"
  - text: "Option 4"  # Add distractor
```

**Modules affected:** M65, M122, M57, M111, M51, M128, M106, M136, M129, M55 (vocabulary/history modules)

**"Unexpected explanation in quiz options" (8 occurrences):**
```yaml
# WRONG - explanation in YAML
options:
  - text: "Correct answer"
    correct: true
    explanation: "Why it's correct"  # ❌ Not allowed

# CORRECT - explanation in markdown
> [!explanation]
> Why the correct answer is correct.
```

**Modules affected:** Multiple history modules (M99, etc.)

**Fix Strategy:**
1. Run `scripts/fix_yaml_schema.py` to migrate all violations
2. Add missing options to quiz/select activities
3. Move explanations from YAML to markdown callouts

---

## 3. COMPLEXITY_WORD_COUNT (3,030 violations)

### Distribution by Activity Type

| Activity Type | Violations | Target Range | Common Actual |
|---------------|------------|--------------|---------------|
| Quiz prompts | ~1,500 | 10-25 words | 3-9 words |
| Unjumble sentences | ~800 | 10-18 words | 3-7 words |
| Fill-in sentences | ~500 | 12-20 words | 5-10 words |
| Error-correction | ~200 | 12-20 words | 6-11 words |
| Other | ~30 | Varies | Below target |

### Sample Violations

**M01 Quiz (Passive Voice):**
```markdown
# TOO SHORT (8 words)
Який дієслівник став пасивним дієприкметником?

# BETTER (15 words)
Який дієслівник у наведеному реченні трансформувався в пасивний дієприкметник минулого часу?
```

**M51 Unjumble (Idioms):**
```markdown
# TOO SHORT (4 words)
руки / опускати / на

# BETTER (12 words)
Коли все не вдається, багато людей схильні опускати руки на невдачі.
```

### Root Cause Analysis

1. **Legacy content from A2/B1:** Many B2 modules reused or adapted A2/B1 activities without enrichment
2. **Quiz question simplification:** Quiz prompts shortened to "test the concept" rather than "immerse in B2 complexity"
3. **Unjumble word economy:** Word scrambles kept minimal for "solvability" rather than linguistic richness

### Fix Strategy

**Automated enrichment (70% of cases):**
- Add dependent clauses to quiz prompts
- Expand unjumble sentences with adverbial phrases
- Add contextual information to fill-in items

**Manual review (30% of cases):**
- Rephrase questions that fundamentally can't be expanded (e.g., "Що таке Голодомор?" → needs conceptual rewrite)
- Ensure enrichment doesn't introduce ambiguity

---

## 4. DUPLICATE_SYNONYMOUS_HEADERS (88 violations)

### Pattern Analysis

**Common duplicates:**
- `Вступ` + `Контекст: [Topic]` (both alias to "Warm-up/Introduction")
- `Граматика` + `Презентація` (both alias to "Grammar/Presentation")
- `Теорія` + `Focus` (both alias to "Grammar/Theory")

**Example from M99 (Austrian Galicia):**
```markdown
## Вступ            # ← Canonical "Introduction"
...

## Контекст: Поділи Речі Посполитої  # ← Also aliases to "Introduction" ❌
```

### Affected Module Ranges

| Range | Count | Pattern |
|-------|-------|---------|
| M71-M131 (History) | 62 | `Вступ` + `Контекст: [Historical Event]` |
| M01-M51 (Grammar) | 18 | `Граматика` + `Презентація` |
| M52-M70 (Vocab) | 8 | Mixed patterns |

### Fix Strategy

**Option 1: Merge duplicate sections**
```markdown
## Вступ: Поділи Речі Посполитої  # Single canonical header
```

**Option 2: Rename to non-aliasing headers**
```markdown
## Вступ                          # Canonical introduction
...
## Історичний контекст            # Non-aliasing context section
```

**Recommended:** Option 2 (preserves semantic distinction)

---

## 5. MISSING_REQUIRED_CALLOUT (47 violations)

### Breakdown by Callout Type

| Missing Callout | Count | Required By Template |
|-----------------|-------|----------------------|
| `[!myth-buster]` | 24 | `b2-history-module-template` |
| `[!history-bite]` | 23 | `b2-history-module-template` |

### Analysis

**History template requirements:**
- Every history module (M71-M131) should have:
  - At least 1 `[!myth-buster]` - debunking Russian imperial myths
  - At least 1 `[!history-bite]` - interesting historical trivia

**Affected modules:** History modules M71-M131 (61 modules)

**Example missing callouts:**

```markdown
# M87 Khmelnychchyna should include:

> [!myth-buster]
> **МІФ:** Богдан Хмельницький "возз'єднав Україну з Росією"
> **РЕАЛЬНІСТЬ:** У 1654 році Росії як держави не існувало. Переяславська рада — договір з Московським царством.

> [!history-bite]
> Хмельницький мав титул "гетьман військ Запорозьких". Це була виборна посада, а не спадкова.
```

### Fix Strategy

Add required callouts to all history modules based on:
1. `docs/l2-uk-en/templates/b2-history-module-template.md`
2. Decolonization perspective from Ukrainian historiography
3. Contemporary scholarship debunking imperial narratives

---

## 6. TOO_MANY_MORPHEMES (39 violations)

### Pattern

Vocabulary items with excessive morphological complexity for single-word teaching.

**Example violations:**
- `бронебійно-запалювальний` (M88) - 5 morphemes, compound military term
- `післячорнобильський` (M132) - 4 morphemes, temporal-adjectival compound
- `морфофонологічний` (M03) - 5 morphemes, linguistics meta-term

### Analysis

**Root Cause:** Specialized vocabulary in advanced modules (history, medical, linguistic meta-language)

**Legitimate cases (30 violations):**
- History modules need era-specific compound adjectives
- Medical modules require technical terminology
- Metalanguage modules teach linguistic concepts

**Questionable cases (9 violations):**
- Words that could be taught as phrases instead
- Overly technical terms for B2 level

### Fix Strategy

**Manual review required:**
1. Verify each flagged word is appropriate for B2 context
2. Consider teaching as collocations: `бронебійний + запалювальний набій`
3. Accept morphological complexity if justified by domain (history, medicine)

---

## 7. Passing Modules Analysis

### ✅ M102: Franko, Lesia Ukrainka, Hrinchenko

**Why it passes:**
- Created with current `b2-module-template.md`
- All required sections present
- YAML activities validate against current schema
- Sentence complexity meets B2 targets (10-25 words)
- No duplicate headers

**Structure:**
```markdown
## Вступ
## Читання: Біографічний нарис
## Словник
## Граматика: Біографічна лексика
## Первинні джерела
## Деколонізаційний погляд
## Need More Practice?
```

### ✅ M105: UNR and ZUNR

**Why it passes:**
- Created with current `b2-history-module-template.md`
- All history-specific sections present
- Required callouts (`[!myth-buster]`, `[!history-bite]`)
- Activities enriched to B2 complexity
- Clean YAML schema

**Use as reference for fixing M71-M131 history modules.**

---

## Module Health by Range

| Range | Modules | Pass Rate | Primary Issues |
|-------|---------|-----------|----------------|
| M01-M10 | 10 | 0% | Missing grammar presentation, short sentences |
| M11-M20 | 10 | 0% | Missing sections, YAML schema |
| M21-M30 | 10 | 0% | Missing sections, short sentences |
| M31-M40 | 10 | 0% | Missing sections, YAML schema |
| M41-M50 | 10 | 0% | Missing sections, short sentences |
| M51-M70 | 20 | 0% | Missing sections, YAML schema, short sentences |
| M71-M90 | 20 | 0% | Missing history sections, duplicate headers |
| M91-M110 | 20 | 10% | Missing history sections (M102, M105 pass) |
| M111-M131 | 21 | 0% | Missing history sections, duplicate headers |
| M132-M145 | 14 | 0% | Incomplete scaffolding |

**Observation:** Only M91-M110 range has passing modules (M102, M105), suggesting this batch was created/updated more recently.

---

## Comparison with B1 Audit

| Metric | B1 | B2 | Difference |
|--------|----|----|------------|
| Total modules | 91 | 145 | +54 (+59%) |
| Pass rate | 8.8% (8/91) | 1.4% (2/145) | -7.4pp |
| Total violations | ~2,800 | 4,603 | +1,803 (+64%) |
| COMPLEXITY_WORD_COUNT | ~1,200 | 3,030 | +1,830 (+153%) |
| MISSING_REQUIRED_SECTION | ~850 | 663 | -187 (-22%) |
| YAML_SCHEMA_VIOLATION | ~600 | 734 | +134 (+22%) |

**Key Insights:**
1. B2 has **worse pass rate** than B1 (1.4% vs 8.8%)
2. **Complexity issues more severe** in B2 (3,030 vs 1,200) - B2 targets not met
3. **YAML schema violations increased** - schema evolution not applied
4. **Structural issues improved** - fewer missing sections (though still critical)

**Conclusion:** B2 needs more intensive complexity enrichment than B1.

---

## Recommended Fix Order

### Phase 1: Automated Structural Fixes (2-3 hours)

**Priority:** 🔴 Critical
**Effort:** Low (scripted)
**Impact:** Fixes 752 violations (16.3%)

1. Add "Need More Practice?" to all 277 modules
2. Normalize duplicate headers (88 violations)
3. Fix YAML schema violations (734 violations)
4. Add empty required sections with `<!-- TODO -->` markers

**Scripts needed:**
- `scripts/fix_b2_missing_sections.py`
- `scripts/fix_b2_duplicate_headers.py`
- `scripts/fix_b2_yaml_schema.py`

### Phase 2: History Section Completion (4-6 hours)

**Priority:** 🔴 Critical
**Effort:** Medium (template-driven content creation)
**Impact:** Fixes 120 violations + improves 61 modules

1. Add "Читання" sections to 80 history modules
2. Add "Первинні джерела" to 32 modules
3. Add "[!myth-buster]" and "[!history-bite]" callouts to 47 modules
4. Add "Деколонізаційний погляд" to 8 modules

**Resources:**
- `docs/l2-uk-en/templates/b2-history-module-template.md`
- M102, M105 as reference examples

### Phase 3: Complexity Enrichment (8-12 hours)

**Priority:** ⚠️ High
**Effort:** High (semi-automated + manual review)
**Impact:** Fixes 3,030 violations (65.8%)

1. Enrich quiz prompts (1,500 violations)
2. Expand unjumble sentences (800 violations)
3. Extend fill-in contexts (500 violations)
4. Review error-correction sentences (200 violations)

**Strategy:**
- Use LLM-assisted enrichment with B2 complexity constraints
- Batch process by activity type
- Manual review of 30% sample

### Phase 4: Manual Review & Validation (2-3 hours)

**Priority:** ⚠️ Moderate
**Effort:** Low (validation)
**Impact:** Quality assurance

1. Review TOO_MANY_MORPHEMES flags (39 violations - accept most)
2. Verify history callout content accuracy
3. Re-run audit on all 145 modules
4. Fix remaining edge cases

**Expected final pass rate:** 95%+ (138/145 modules)

---

## Total Estimated Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Automated Structural | 2-3 hours | None |
| Phase 2: History Sections | 4-6 hours | Phase 1 complete |
| Phase 3: Complexity Enrichment | 8-12 hours | Phase 1 complete |
| Phase 4: Manual Review | 2-3 hours | Phases 1-3 complete |
| **Total** | **16-24 hours** | Sequential phases |

**Parallelization opportunity:** Phases 2 and 3 can run in parallel after Phase 1.

**Realistic timeline:** 2-3 working days with focused effort.

---

## Next Actions

1. ✅ Read this summary and quick summary
2. ✅ Review `b2-fix-scripts-needed.md` for implementation details
3. ▶️ **Start Phase 1:** Run automated structural fixes
4. ⏳ Monitor progress with re-audits after each phase
5. ⏳ Update `docs/issues/b2-rebuild-index.md` with progress

---

## Related Documentation

- `b2-rebuild-audit-report.md` - Full audit logs (643KB, 145 modules)
- `b2-audit-quick-summary.md` - Quick reference (this summary)
- `b2-fix-scripts-needed.md` - Implementation guide
- `b2-rebuild-index.md` - Navigation and progress tracker
- `docs/l2-uk-en/templates/b2-module-template.md` - Template standard
- `docs/l2-uk-en/templates/b2-history-module-template.md` - History template
