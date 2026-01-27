# B1 Fix Scripts - Implementation Checklist

**Goal:** Batch-fix 1,391 violations across 81 B1 modules to achieve 95%+ audit pass rate.

---

## Priority 1: Critical (Blocks Functionality)

### 1. `scripts/fix/yaml_schema_validator.py`

**Impact:** Fixes 290 violations across 81 modules
**Severity:** 🔴 Critical (blocks activity rendering)

**Errors to Fix:**
- Missing `correct_words` in mark-the-words activities
- Empty `items` arrays in activities
- Invalid field names (e.g., `correct_answers` → `correct`)
- Missing required fields (e.g., `options` in error-correction)

**Implementation:**
```python
# For each B1 activity YAML file:
1. Load JSON schema from schemas/activities-base.schema.json
2. Validate YAML against schema
3. For each validation error:
   - If missing 'correct_words': Extract from text and add
   - If empty items: Flag for manual review (cannot auto-generate)
   - If invalid field: Rename field to match schema
   - If missing required field: Add with sensible default
4. Write fixed YAML
5. Validate again to ensure compliance
```

**Test Cases:**
- Module 11: Missing `correct_words` in mark-the-words
- Module 52: Invalid `scrambled` field in unjumble
- Module 15: Empty items array (checkpoint)

---

### 2. `scripts/fix/add_missing_sections.py`

**Impact:** Fixes 150 violations across 42 modules
**Severity:** 🔴 High (blocks template compliance)

**Missing Sections to Generate:**
- `## Граматична таблиця` (grammar tables in grammar modules)
- `## Спостерігайте` (inductive observation section)
- `## Культурний контекст` (cultural context in cultural modules)

**Implementation:**
```python
# For each B1 module:
1. Determine module type (grammar/vocab/cultural/checkpoint)
2. Load appropriate template (b1-grammar-module-template.md, etc.)
3. Extract required sections from template
4. For each missing section:
   - Grammar table: Generate from module's grammar content
   - Спостерігайте: Create inductive examples from Practice section
   - Cultural context: Generate from module topic (use existing cultural notes)
5. Insert section at correct position in document
6. Validate section order
```

**Generation Rules:**
- **Grammar table:** Extract declension/conjugation patterns from module content
- **Спостерігайте:** Create 3-5 example sentences highlighting the pattern
- **Cultural context:** Generate 2-3 paragraphs about cultural relevance

**Test Cases:**
- Module 16: Missing motion verb tables
- Module 26: Missing Спостерігайте section
- Module 72: Missing cultural context

---

### 3. `scripts/fix/extend_unjumble_sentences.py`

**Impact:** Fixes 565 violations across 51 modules
**Severity:** 🟡 Medium (pedagogical quality, high volume)

**Word Count Targets:**
- B1 unjumble: 12-16 words
- B1 quiz prompts: 10-18 words

**Implementation:**
```python
# For each unjumble/quiz activity:
1. Count words in sentence/prompt
2. If below minimum (12 for unjumble, 10 for quiz):
   - Parse sentence structure
   - Add appropriate extensions:
     * Subordinate clauses (які, що, коли, тому що)
     * Adverbial phrases (вчора ввечері, у центрі міста)
     * Adjective modifiers (дуже цікавий, найкращий)
   - Maintain grammatical correctness
   - Use vocabulary from module's словник
3. Update activity YAML with extended sentence
4. Validate word count is within target range
```

**Extension Strategies:**
- Add time/place adverbials: "вчора" → "вчора ввечері після роботи"
- Add relative clauses: "книгу" → "книгу, яку я давно хотів прочитати"
- Add reason clauses: "прийшов" → "прийшов, тому що хотів побачити друзів"

**Test Cases:**
- Module 11: 5 unjumble sentences (8-10 words → 12-16)
- Module 52: 6 unjumble sentences (4-6 words → 10-14)

---

## Priority 2: High (Blocks Gates)

### 4. `scripts/fix/populate_empty_sections.py`

**Impact:** Fixes 150 violations across 81 modules
**Severity:** 🟡 High (template compliance)

**Empty Sections to Populate:**
- `## Потрібно більше практики?` (practice resources callout)
- `## Граматична довідка` (grammar reference for checkpoints)

**Implementation:**
```python
# For each empty section:
1. Identify section type
2. If "Потрібно більше практики?":
   - Generate standard practice resources callout:
     > [!tip] Потрібно більше практики?
     > Ви можете:
     > - Переглянути Модулі X-Y для повторення
     > - Виконати додаткові вправи в [resource]
     > - Практикувати з носіями мови
3. If "Граматична довідка" (checkpoint):
   - Extract grammar topics from previous modules
   - Generate reference table/list
4. Insert content into section
5. Validate content is meaningful (not just placeholder)
```

**Test Cases:**
- Module 11: Empty "Потрібно більше практики?"
- Module 15: Empty "Граматична довідка" (checkpoint)

---

### 5. `scripts/fix/expand_activity_density.py`

**Impact:** Fixes 58 violations across 58 modules
**Severity:** 🟡 High (richness gate)

**Density Targets:**
- Grammar modules: 14 items/activity
- Vocabulary modules: 12 items/activity
- Checkpoint modules: 16 items/activity

**Implementation:**
```python
# For each low-density activity:
1. Count current items
2. Calculate deficit (target - current)
3. Identify activity type (quiz, fill-in, unjumble, etc.)
4. Generate additional items:
   - Use vocabulary from module's словник
   - Use grammar patterns from module content
   - Maintain pedagogical quality (not just filler)
   - Ensure correct answers are accurate
5. Add items to activity YAML
6. Validate density meets target
```

**Generation Strategy:**
- **Quiz:** Create similar questions testing same concept
- **Fill-in:** Add more sentences using module vocabulary
- **Unjumble:** Create variations with same grammar pattern
- **Cloze:** Extend passage with more blanks

**Test Cases:**
- Module 11: mark-the-words with 0 items (need 6)
- Module 52: cloze with 12 items (need 14)

---

### 6. `scripts/fix/add_activities.py`

**Impact:** Fixes 45 violations across 45 modules
**Severity:** 🟡 High (richness gate)

**Activity Count Targets:**
- Grammar modules: 12 activities
- Vocabulary modules: 10 activities
- Checkpoint modules: 14 activities

**Implementation:**
```python
# For each module with low activity count:
1. Count current activities
2. Calculate deficit
3. Identify missing activity types (prioritize diversity)
4. Generate new activities:
   - Use module vocabulary and grammar scope
   - Ensure required mix (quiz, fill-in, unjumble, error-correction, etc.)
   - Meet density requirements for new activities
5. Add to activity YAML
6. Validate total count and type diversity
```

**Activity Type Priority (B1):**
1. error-correction (if missing)
2. cloze (if missing)
3. mark-the-words (if missing)
4. select (optional, useful for multi-answer)
5. translate (optional, for reinforcement)

**Test Cases:**
- Module 11: 11/12 activities (add 1 more)
- Module 16: 10/12 activities (add 2 more)

---

## Priority 3: Quality Improvements

### 7. `scripts/fix/reorder_sections.py`

**Impact:** Fixes 42 violations across 22 modules
**Severity:** 🟢 Medium (template compliance)

**Expected Section Order (Grammar Module):**
1. Вступ / Контекст
2. Граматична таблиця
3. Спостерігайте
4. Правило / Пояснення
5. Практика
6. Словник
7. Активності

**Implementation:**
```python
# For each module with section order violations:
1. Parse markdown sections
2. Load template section order
3. Reorder sections to match template
4. Preserve all content (no loss)
5. Validate order matches template
```

---

### 8. `scripts/fix/merge_duplicate_headers.py`

**Impact:** Fixes 48 violations across 24 modules
**Severity:** 🟢 Medium (content cleanup)

**Common Duplicates:**
- "Вступ" + "Контекст" → Merge into "Вступ"
- "Граматика" + "Правило" → Merge into "Граматика"
- "Практика" + "Додаткова практика" → Merge into "Практика"

**Implementation:**
```python
# For each module with duplicate headers:
1. Identify synonymous sections
2. Merge content (combine paragraphs, preserve all examples)
3. Use canonical header name from template
4. Validate no content loss
```

---

### 9. `scripts/fix/remove_english.py`

**Impact:** Fixes 19 violations across 19 modules
**Severity:** 🟢 Low (quality target)

**Immersion Target:** 85-100% Ukrainian (B1.2+)

**English to Remove:**
- English translations in activity titles (keep Ukrainian only)
- English explanations in grammar sections (translate to Ukrainian)
- English notes in vocabulary (keep only in Переклад column)

**Implementation:**
```python
# For each low-immersion module:
1. Identify English text outside allowed areas
2. Remove or translate to Ukrainian
3. Validate immersion percentage meets target
```

---

### 10. `scripts/fix/simplify_fillins.py`

**Impact:** Fixes 24 violations across 24 modules
**Severity:** 🟢 Low (pedagogical refinement)

**Morpheme Constraint:** Fill-in should target single-morpheme words (B1 level).

**Examples:**
- ❌ `перечитати` (пере- + читати, 2 morphemes)
- ✅ `читати` (1 morpheme)
- ❌ `найкращий` (най- + кращ- + -ий, 3 morphemes)
- ✅ `кращий` (2 morphemes, acceptable)

**Implementation:**
```python
# For each fill-in activity:
1. Identify multi-morpheme targets
2. Simplify to single-morpheme alternatives:
   - Remove prefixes (пере-, при-, ви-)
   - Use base forms instead of superlatives
3. Update activity YAML
4. Validate grammatical correctness
```

---

## Implementation Order

### Week 1: Priority 1 (Critical)

**Day 1-2:** YAML schema validator (#1) → Fixes 290 violations
**Day 3-4:** Add missing sections (#2) → Fixes 150 violations
**Day 5:** Extend unjumble sentences (#3) → Fixes 565 violations

**Week 1 Impact:** 1,005 violations fixed (72% of total)

---

### Week 2: Priority 2 (High)

**Day 1-2:** Populate empty sections (#4) → Fixes 150 violations
**Day 3:** Expand activity density (#5) → Fixes 58 violations
**Day 4:** Add missing activities (#6) → Fixes 45 violations

**Week 2 Impact:** 253 violations fixed (18% of total)

---

### Week 3: Priority 3 (Quality) + Re-Audit

**Day 1:** Reorder sections (#7) + Merge duplicates (#8) → Fixes 90 violations
**Day 2:** Remove English (#9) + Simplify fill-ins (#10) → Fixes 43 violations
**Day 3-4:** Re-audit all B1 modules, fix edge cases
**Day 5:** Run full pipeline validation

**Week 3 Impact:** 133 violations fixed (10% of total) + validation

---

## Success Criteria

**Before Fix:**
- Pass rate: 11% (10/91 modules)
- Total violations: 1,391

**After Fix (Target):**
- Pass rate: 95%+ (86+/91 modules)
- Total violations: <70 (edge cases only)

---

## Testing Strategy

### Unit Tests (Per Script)

```bash
# Test on sample modules first
.venv/bin/python scripts/fix/yaml_schema_validator.py \
  curriculum/l2-uk-en/b1/11-aspect-in-imperatives.md

# Validate fix worked
.venv/bin/python scripts/audit_module.py \
  curriculum/l2-uk-en/b1/11-aspect-in-imperatives.md
```

### Integration Tests (Full Level)

```bash
# Apply all fixes to B1
npm run fix:all l2-uk-en b1

# Re-audit entire level
.venv/bin/python scripts/audit_level.py l2-uk-en b1

# Run pipeline to validate output
npm run pipeline l2-uk-en b1
```

### Regression Tests

```bash
# Ensure M01-10 (currently passing) still pass after fixes
npm run pipeline l2-uk-en b1 1
npm run pipeline l2-uk-en b1 10
```

---

## Next Steps

1. **Review this plan** → Confirm priorities and approach
2. **Implement Priority 1 scripts** → YAML schema, missing sections, word count
3. **Test on M11-15** → Validate fixes work correctly
4. **Batch apply to all B1** → Run fixes on all 81 failing modules
5. **Re-audit** → Validate 95%+ pass rate
6. **Run pipeline** → Generate MDX and validate HTML

**Estimated Time:** 2-3 weeks for full implementation and validation.
