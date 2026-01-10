# YAML Schema Violations - Root Cause Analysis

**Date:** 2026-01-10
**Status:** CRITICAL - Affects 100+ modules across B1, B2, C1
**Impact:** Pipeline failures, invalid activity generation, broken validation

---

## Executive Summary

**Root Cause:** Documentation (`ACTIVITY-YAML-REFERENCE.md`) uses different property names than the JSON Schema (`activities-base.schema.json`). AI agents and developers follow the documentation, generating invalid YAMLs that fail schema validation.

**Scope:**
- ✅ A1: **0 violations** (34/34 modules clean)
- ✅ A2: **0 violations** (57/57 modules clean)
- ❌ B1: **~59 violations** across 60+ modules
- ❌ B2: **Unknown** (multiple violations)
- ❌ C1: **~20 violations** (YAML parse errors + schema issues)

**Top 5 Issues:**
1. **59 instances:** mark-the-words missing `correct_words` property
2. **35 instances:** unjumble has unexpected `scrambled` property
3. **10 instances:** select/quiz missing `question` property
4. **5 instances:** quiz options missing `correct` property
5. **3 instances:** translate missing `source` property

---

## Detailed Analysis

### 1. mark-the-words Activity (59 violations)

**Schema Requires:**
```json
{
  "required": ["type", "title", "passage", "correct_words"],
  "properties": {
    "passage": { "type": "string" },
    "correct_words": {
      "type": "array",
      "items": { "type": "string" }
    }
  }
}
```

**Documentation Shows (WRONG):**
```yaml
- type: mark-the-words
  title: Title
  instruction: Знайдіть усі іменники.
  text: Гарний день приніс радість у серце.    # ❌ Should be "passage"
  answers:                                     # ❌ Should be "correct_words"
    - день
    - радість
    - серце
```

**Correct Format (from A2 modules):**
```yaml
- type: mark-the-words
  title: Find Perfective Future
  passage: 'Завтра я *прочитаю* книгу. Потім я *напишу* рецензію.'
  correct_words:
    - прочитаю
    - напишу
```

**Impact:** 59 modules have mark-the-words activities that fail validation.

---

### 2. unjumble Activity (35 violations)

**Schema Requires:**
```json
{
  "required": ["words", "answer"],
  "additionalProperties": false,
  "properties": {
    "words": {
      "type": "array",
      "items": { "type": "string" }
    },
    "answer": { "type": "string" }
  }
}
```

**Documentation Shows (WRONG):**
```yaml
- type: unjumble
  title: Title
  items:
    - jumbled: words / in / disorder   # ❌ Property "jumbled" not in schema
      answer: Words in correct order.
```

**What's Being Generated (ALSO WRONG):**
From `fix_yaml_quiz.py` line 87:
```python
'scrambled': item.strip(),   # ❌ Property "scrambled" not in schema
```

**Correct Format (from A2 modules):**
```yaml
- type: unjumble
  title: Cooking Sentences
  items:
    - words:           # ✅ Array of individual words
        - Ти
        - маєш
        - покласти
        - свіжу
        - картоплю
      answer: Ти маєш покласти свіжу картоплю
```

**Impact:** 35 modules have unjumble activities with `scrambled` property that violates `additionalProperties: false`.

**Evidence of Known Issue:** `fix_b2_activities.py` lines 30-31:
```python
if 'scrambled' in item and 'words' in item:
    del item['scrambled']   # Script written to fix the violation!
```

---

### 3. translate Activity (3+ violations)

**Schema Requires:**
```json
{
  "required": ["source", "options"],
  "properties": {
    "source": { "type": "string" },
    "options": { "type": "array" }
  }
}
```

**Common Error:** Missing `source` property

**Correct Format:**
```yaml
- type: translate
  title: Переклад
  items:
    - source: English sentence to translate.
      options:
        - text: Wrong translation
          correct: false
        - text: Correct translation
          correct: true
```

**Impact:** Modules fail because translate items lack the required `source` property.

---

### 4. select/quiz Activity (10+ violations)

**Schema Requires:**
```json
{
  "required": ["question", "options"],
  "properties": {
    "question": { "type": "string" },
    "options": { "type": "array" }
  }
}
```

**Common Error:** Missing `question` property in items

**Also:** Missing `correct` property in quiz options (5 violations)

---

## Why A1/A2 Are Clean

**A1 and A2 have ZERO violations because:**

1. They were created earlier when the schema and docs were in sync
2. They use the CORRECT property names:
   - `words` (not `jumbled` or `scrambled`)
   - `passage` and `correct_words` (not `text` and `answers`)
   - `source` in translate items

3. Subsequent levels (B1+) were created following the OUTDATED documentation

---

## Root Cause Chain

```
1. Schema was updated (or documentation was never aligned)
   ↓
2. Documentation shows wrong property names
   ↓
3. AI agents and developers create YAMLs following documentation
   ↓
4. Schema validation fails (but modules were already written)
   ↓
5. Fix scripts written to patch specific issues (not systematic)
   ↓
6. Problem persists because documentation not fixed
```

---

## Impact on Pipeline

**Current State:**
- Modules pass markdown linting (no markdown validation)
- Modules FAIL YAML schema validation during audit
- Generators try to convert invalid YAML → MDX (may produce corrupt output)
- HTML validation may fail due to missing/malformed activities

**What's Broken:**
1. ❌ Schema validation (audit step)
2. ⚠️ MDX generation (may work but produce invalid JSON/MDX)
3. ⚠️ HTML rendering (interactive activities may not load)
4. ❌ JSON export for Vibe app (schema violations block generation)

---

## Files That Need Fixing

### 1. Documentation (Priority: CRITICAL)

**File:** `docs/ACTIVITY-YAML-REFERENCE.md`

**Changes needed:**

#### mark-the-words section (line ~303)
```diff
-- type: mark-the-words
   title: Title
-  instruction: Знайдіть усі іменники.
-  text: Гарний день приніс радість у серце.
-  answers:
+  passage: 'Click on NOUNS. Гарний *день* приніс *радість* у *серце*.'
+  correct_words:
     - день
     - радість
     - серце
```

#### unjumble section (line ~262)
```diff
-- type: unjumble
   title: Title
-  instruction: Optional instruction text.
   items:
-    - jumbled: words / in / disorder
+    - words:
+        - words
+        - in
+        - disorder
       answer: Words in correct order.
```

### 2. Generation Scripts

**File:** `scripts/fix_yaml_quiz.py` (line 87)
```diff
-'scrambled': item.strip(),
+'words': item.strip().split(' / '),
```

**File:** Any script generating mark-the-words
- Change `text` → `passage`
- Change `answers` → `correct_words`

**File:** Any script generating translate
- Ensure `source` property is always included

### 3. Existing YAML Files (Bulk Fix Required)

**Need automated migration:**

```bash
# Fix all mark-the-words activities
for file in curriculum/l2-uk-en/{b1,b2,c1}/activities/*.yaml; do
  # Add missing correct_words property
  # Extract words from passage marked with *asterisks*
done

# Fix all unjumble activities
for file in curriculum/l2-uk-en/{b1,b2,c1}/activities/*.yaml; do
  # Remove 'scrambled' property
  # Convert to 'words' array if needed
done

# Fix all translate activities
for file in curriculum/l2-uk-en/{b1,b2,c1}/activities/*.yaml; do
  # Add missing 'source' property
done
```

---

## Recommended Fix Strategy

### Phase 1: Stop the Bleeding (Immediate)

1. ✅ **Update documentation** (`ACTIVITY-YAML-REFERENCE.md`) to match schema
2. ✅ **Fix generation scripts** to use correct property names
3. ✅ **Add pre-commit validation** to prevent invalid YAMLs from being committed

### Phase 2: Remediation (1-2 days)

1. 🔧 **Create automated migration scripts** for each violation type:
   - `fix_mark_the_words_schema.py` (59 modules)
   - `fix_unjumble_schema.py` (35 modules)
   - `fix_translate_schema.py` (3 modules)
   - `fix_quiz_select_schema.py` (15 modules)

2. 🔧 **Run migrations** on all B1, B2, C1 modules

3. 🔧 **Re-audit all modules** to verify fixes

### Phase 3: Prevention (Ongoing)

1. ✅ **Add CI validation** that runs schema check on all YAML files
2. ✅ **Update AI agent prompts** to reference correct schema format
3. ✅ **Create YAML templates** for each activity type showing correct format
4. ✅ **Add schema autocomplete** hints to VS Code/IDE configurations

---

## Testing Plan

### Validate Fix Success

```bash
# Before fixes
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/30-purpose-shchob-past-form.md
# Expected: YAML_SCHEMA_VIOLATION errors

# After fixes
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/30-purpose-shchob-past-form.md
# Expected: PASS with no schema violations

# Validate entire level
for file in curriculum/l2-uk-en/b1/*.md; do
  .venv/bin/python scripts/audit_module.py "$file" 2>&1 | grep "YAML_SCHEMA_VIOLATION"
done
# Expected: No output (all clean)
```

---

## Appendix: Complete Error Counts

**Extracted from audit reports:**

| Error Type | Count | Affected Modules |
|------------|-------|------------------|
| `correct_words` is a required property | 59 | B1 M30-50, others |
| `'scrambled' was unexpected` | 35 | B1, B2 unjumble activities |
| `'question' is a required property` | 10 | B1 select activities |
| `'correct' is a required property` | 5 | B1 quiz options |
| `'source' is a required property` | 3 | B1 translate activities |
| `'sentence' is a required property` | 3 | Unknown |
| `'id' was unexpected` (essay) | ~10 | C1 M85-99 biography modules |
| YAML parse errors | ~6 | C1 M85-90 |

**Total modules affected:** ~100+ across B1, B2, C1

---

## Next Steps

1. **[IMMEDIATE]** Update `ACTIVITY-YAML-REFERENCE.md` with correct property names
2. **[HIGH PRIORITY]** Create and run migration scripts for top 3 violations
3. **[MEDIUM]** Add pre-commit YAML schema validation
4. **[ONGOING]** Re-audit all fixed modules

---

**Prepared by:** Claude Sonnet 4.5
**Date:** 2026-01-10
**Status:** DRAFT - Ready for review and implementation
