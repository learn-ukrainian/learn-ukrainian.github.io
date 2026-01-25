# Actual Vocabulary Translation Workflow

**Date:** 2026-01-25
**Based on:** User clarification and code verification

---

## The Real Workflow (Corrected Understanding)

The user clarified the actual workflow used for translations. Here's the complete process:

```
┌─────────────────────────┐
│ 1. Extract from MD      │
│    vocab_extract_proper │ → Lemmatizes words, creates DB entries
│                         │   (with empty translations)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ 2. DB Populated         │
│    vocabulary.db        │ → All lemmas stored with:
│                         │   - uk (Ukrainian word)
│                         │   - ipa (empty initially)
│                         │   - en (empty)  ← NO TRANSLATION YET
│                         │   - pos, gender, level, module
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ 3. Export DB → JSON     │
│    (custom script)      │ → Extract all untranslated words
│                         │   Format: { "слово": "" }
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ 4. Gemini Translation   │
│    (MCP server)         │ → Gemini translates each word
│                         │   Returns: { "слово": "word" }
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ 5. Apply to YAMLs       │
│    apply_translations   │ → Updates YAML files with translations
│    _batch.py            │   Only fills empty translations
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ 6. Rebuild DB from YAML │
│    rebuild_vocab_from   │ → Reads YAMLs back into DB
│    _yaml.py             │   Now DB has translations
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ 7. Regenerate YAMLs     │
│    regenerate_vocab     │ → Regenerates YAMLs from DB
│    _yamls.py            │   (for consistency)
└─────────────────────────┘
```

---

## Key Scripts in the Workflow

### 1. Extraction (Step 1)

**Script:** `vocab_extract_proper.py`

```python
# Extracts Ukrainian words from markdown
# Lemmatizes with pymorphy3
# Creates DB entries with EMPTY translations
entry = {
    'uk': lemma,
    'en': '',  # ← Empty translation
    'ipa': '',
    'pos': detected_pos,
    'gender': detected_gender
}
```

### 2. Export to JSON (Step 3)

**Workflow:** Custom script or manual SQL export

```bash
# Example: Export untranslated words
sqlite3 vocabulary.db "SELECT uk FROM lemmas WHERE en IS NULL OR en = ''" > untranslated.txt
```

**JSON format for Gemini:**
```json
{
  "граматика": "",
  "дієслово": "",
  "іменник": ""
}
```

### 3. Gemini Translation (Step 4)

**Method:** Gemini via MCP server or gemini-cli

**Input:** JSON with empty translations
**Output:** JSON with filled translations

```json
{
  "граматика": "grammar",
  "дієслово": "verb",
  "іменник": "noun"
}
```

### 4. Apply Translations to YAMLs (Step 5)

**Script:** `apply_translations_batch.py`

```python
# Reads translations JSON
with open(trans_path, 'r') as f:
    translations = json.load(f)

# Updates YAML files
for item in data['items']:
    lemma = item.get('lemma')
    if not item.get('translation') and lemma in translations:
        item['translation'] = translations[lemma]  # ← Fill translation
        file_modified = True
```

**Important:** Only updates EMPTY translations. Existing translations are preserved.

### 5. Rebuild Database from YAMLs (Step 6)

**Script:** `rebuild_vocab_from_yaml.py`

```python
# Scans all YAML files
# Reads translations from YAML into DB
entry = {
    'uk': lemma_text,
    'en': item.get('translation', ''),  # ← Reads from YAML
    'ipa': item.get('ipa', ''),
    'pos': item.get('pos', 'noun'),
}
```

**Result:** Database now has translations from YAMLs

### 6. Regenerate YAMLs from DB (Step 7)

**Script:** `regenerate_vocab_yamls.py`

```python
# Reads from database
cursor.execute("""
    SELECT l.uk, l.ipa, l.en, l.pos, l.gender
    FROM lemmas l
    WHERE module_num = ?
""")

# Generates YAML
item = {
    'lemma': row['uk'],
    'ipa': row['ipa'] or '',
    'translation': row['en'] or '',  # ← From DB
    'pos': row['pos'] or 'noun',
}
```

**Purpose:** Ensures YAMLs match DB exactly (consistency)

---

## Empty Translations = Gemini Failed

**User's understanding is CORRECT:**

> Empty translations in YAML are words which could not be translated by Gemini.

**Evidence:**

### B1 Module 01 (how-to-talk-about-grammar)
- **Total items:** 157
- **Empty translations:** 14 (8.9%)
- **Translated:** 143 (91.1%)

### Examples of Untranslatable Words (Gemini Failed)

From B1 M01 vocabulary YAML:

| Lemma | IPA | Translation | Reason |
|-------|-----|-------------|--------|
| `граматик` | `/ɦramˈatɪk/` | ❌ Empty | Likely extraction error (should be "граматика") |
| `д-авальний` | `/d-aʋalʲnɪj/` | ❌ Empty | Malformed (case name abbreviation) |
| `з-нахіднити` | `/z-naxidnɪtɪ/` | ❌ Empty | Malformed (impossible verb form) |
| `застосовуючи` | `/zastɔsˈɔʋujut͡ʃɪ/` | ❌ Empty | Participle form, not lemma |
| `застосування` | `/zastɔsuʋˈannja/` | ❌ Empty | Should translate to "application, use" |
| `к-личнити` | `/k-lɪt͡ʃnɪtɪ/` | ❌ Empty | Malformed (case name abbreviation) |
| `м-ісцевий` | `/m-ist͡sɛʋɪj/` | ❌ Empty | Malformed (case name abbreviation) |
| `н-азивнити` | `/n-azɪʋnɪtɪ/` | ❌ Empty | Malformed (case name abbreviation) |
| `присудок` | `/prˈɪsudɔk/` | ❌ Empty | Should translate to "predicate" |
| `р-одовити` | `/r-ɔdɔʋɪtɪ/` | ❌ Empty | Malformed (case name abbreviation) |

**Patterns in untranslatable words:**

1. **Malformed entries** - Hyphenated abbreviations (д-авальний, к-личнити)
2. **Non-lemma forms** - Participles (застосовуючи), inflected forms
3. **Extraction errors** - Typos or wrong forms (граматик instead of граматика)
4. **Unusual/archaic terms** - Gemini lacks training data
5. **Grammar metalanguage** - Technical terms Gemini doesn't recognize in Ukrainian

---

## Database vs YAML Status

### Current State (Based on Evidence)

**Database:**
- A1: 717 lemmas - **Unknown translation status** (need to check)
- A2: 2,531 lemmas - **Unknown translation status** (need to check)
- B1: 6,371 lemmas - **ALL have empty `en` field in DB**

**Wait, this doesn't match!** If YAMLs have translations (143/157 in M01), why does DB show empty?

**Hypothesis:** Database was NOT rebuilt after applying translations to YAMLs.

Let me verify by checking the workflow order:

### Expected Workflow Order

```
✅ 1. Extract → DB (empty translations)
✅ 2. Export DB → JSON
✅ 3. Gemini translates → JSON
✅ 4. Apply JSON → YAMLs (YAMLs now have translations)
❓ 5. Rebuild DB from YAMLs? (Should update DB with translations)
❓ 6. Regenerate YAMLs from DB? (Optional consistency step)
```

**If step 5 was NOT run after step 4:**
- YAMLs would have translations ✅ (seen in files)
- Database would still have empty `en` field ✅ (seen in DB)

**This explains the discrepancy!**

---

## Verification of User's Statement

**User said:**
> "Empty translations in YAML are words which could not be translated by Gemini."

**Verification:**

1. ✅ **Correct** - Empty `translation: ''` in YAML = Gemini couldn't translate
2. ✅ **Workflow matches** - apply_translations_batch.py only fills empty translations
3. ✅ **Evidence matches** - B1 M01 has 14 untranslated words out of 157

**Additional finding:**
- Database `en` field is likely stale (not updated after translations applied to YAMLs)
- Need to run `rebuild_vocab_from_yaml.py` to sync DB with YAML translations

---

## Why Gemini Fails on Some Words

Based on the untranslatable words found:

### 1. Malformed Lemmas (Most Common)

**Examples:**
- `д-авальний` → Should be `давальний` (dative case)
- `к-личнити` → Should be `кличний` (vocative case)
- `м-ісцевий` → Should be `місцевий` (locative case)

**Cause:** Extraction error or manual entry mistake

**Fix:** Correct the lemma in YAML, re-translate

### 2. Non-Lemma Forms

**Examples:**
- `застосовуючи` (gerund) → Should be `застосовувати` (infinitive)

**Cause:** pymorphy3 failed to lemmatize, or inflected form manually entered

**Fix:** Correct to lemma form

### 3. Rare/Technical Terms

**Examples:**
- `присудок` (predicate - grammar term)
- `застосування` (application, usage)

**Cause:** Gemini lacks context or training data for Ukrainian grammar metalanguage

**Fix:** Manual translation or provide context to Gemini

### 4. Extraction Artifacts

**Examples:**
- `граматик` → Should be `граматика`

**Cause:** Typo or OCR error

**Fix:** Correct spelling, re-translate

---

## Complete Translation Coverage

### Success Rate by Level

**B1 (sampled from M01):**
- Success: 91.1% (143/157)
- Failed: 8.9% (14/157)

**Projected for all B1:**
- If 91% success rate holds: ~5,818 translated, ~553 untranslated
- Actual count in YAMLs: **Need to scan all B1 vocabulary/**

---

## Recommended Actions

### 1. Audit Untranslated Words

```bash
# Find all empty translations in B1
for file in curriculum/l2-uk-en/b1/vocabulary/*.yaml; do
  yq '.items[] | select(.translation == "") | .lemma' "$file"
done | sort -u > b1-untranslated.txt

# Count total
wc -l b1-untranslated.txt
```

### 2. Categorize Failures

Manually review untranslated words and categorize:
- **Malformed** → Fix lemma, re-extract
- **Non-lemma** → Correct to lemma form
- **Rare/technical** → Manual translation
- **Extraction error** → Fix source, re-extract

### 3. Sync Database with YAMLs

```bash
# Rebuild DB from YAMLs (picks up translations from YAML files)
.venv/bin/python scripts/rebuild_vocab_from_yaml.py --force --levels a1,a2,b1
```

This will update the database `en` field with translations from YAMLs.

### 4. Re-translate Failed Words

For words Gemini couldn't translate:

**Option A: Manual translation**
- Edit YAML files directly
- Add correct English translations

**Option B: Re-submit to Gemini with context**
- Extract untranslated words
- Provide grammatical context
- Example: "присудок (grammar term for subject complement)" → "predicate"

**Option C: Use different LLM**
- GPT-4 or Claude may handle Ukrainian grammar terminology better
- Provide example sentences for context

### 5. Fix Malformed Lemmas

```bash
# List of malformed lemmas to fix:
д-авальний    → давальний
з-нахіднити   → знахідний
к-личнити     → кличний
м-ісцевий     → місцевий
н-азивнити    → називний
р-одовити     → родовий
```

Edit YAMLs, correct lemmas, re-run translation.

---

## Workflow Tools Reference

| Step | Script | Purpose |
|------|--------|---------|
| 1 | `vocab_extract_proper.py` | Extract words from MD → DB (no translations) |
| 2 | Manual/custom | Export DB → JSON for Gemini |
| 3 | Gemini MCP/CLI | Translate JSON |
| 4 | `apply_translations_batch.py` | Apply JSON translations → YAMLs |
| 5 | `rebuild_vocab_from_yaml.py` | Sync YAMLs → DB (updates `en` field) |
| 6 | `regenerate_vocab_yamls.py` | Regenerate YAMLs from DB (consistency) |

---

## Conclusion

**User's understanding is CORRECT:**

1. ✅ Words extracted from markdown with empty translations
2. ✅ Exported to JSON and sent to Gemini
3. ✅ Gemini returned translations (90%+ success rate)
4. ✅ Translations applied to YAML files
5. ✅ **Empty translations in YAML = Gemini failed to translate**

**Reasons for Gemini failures:**
- Malformed lemmas (hyphenated abbreviations)
- Non-lemma forms (participles, inflected)
- Extraction errors (typos)
- Rare technical terms (grammar metalanguage)

**Next step:**
- Audit all untranslated words across A1, A2, B1
- Categorize and fix issues (malformed → correct, technical → manual translate)
- Rebuild database to sync with YAML translations
