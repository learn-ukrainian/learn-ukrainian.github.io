# Vocabulary Extraction Workflow Overview (A1, A2, B1)

**Date:** 2026-01-25
**Purpose:** Comprehensive explanation of vocabulary extraction and management system
**Scope:** A1, A2, B1 levels

---

## System Overview

The vocabulary system has **three main components**:

1. **Vocabulary YAML files** - Individual module vocabulary (`curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml`)
2. **Vocabulary Database** - Cumulative SQLite DB (`curriculum/l2-uk-en/vocabulary.db`)
3. **Extraction & Enrichment Scripts** - Python tools for automation

---

## 1. The Database (Central Storage)

**File:** `curriculum/l2-uk-en/vocabulary.db`
**Size:** 3.0 MB
**Schema:** SQLite with 4 tables

### Current Contents

| Level | Lemmas | Module Range | Notes |
|-------|--------|--------------|-------|
| **A1** | 717 | Modules 1-44 | Complete |
| **A2** | 2,531 | Modules 45-114 | Complete |
| **B1** | 6,371 | Modules 115-206 | Complete |
| **TOTAL** | **9,619 lemmas** | - | Used for delta extraction |

### Schema

```sql
CREATE TABLE lemmas (
  id TEXT PRIMARY KEY,
  uk TEXT UNIQUE NOT NULL,         -- Ukrainian lemma (dictionary form)
  ipa TEXT,                          -- IPA pronunciation
  en TEXT,                           -- English translation
  pos TEXT DEFAULT 'noun',           -- Part of speech
  gender TEXT,                       -- For nouns: m, f, n, pl
  first_module INTEGER,              -- Module where first introduced
  level TEXT,                        -- A1, A2, B1, etc.
  notes TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE expressions (
  -- Multi-word phrases, idioms, collocations
  ...
);

CREATE TABLE module_vocabulary (
  module_num INTEGER NOT NULL,
  entry_type TEXT NOT NULL,    -- 'lemma' or 'expression'
  entry_id TEXT NOT NULL,
  is_new INTEGER DEFAULT 1,    -- 1 if first introduced, 0 if review
  PRIMARY KEY (module_num, entry_type, entry_id)
);
```

**Purpose:**
- Track cumulative vocabulary across all levels
- Enable delta extraction (filter words already known)
- Link vocabulary to specific modules
- Distinguish between new vs review vocabulary

---

## 2. Vocabulary YAML Files

**Location:** `curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml`

### File Counts

| Level | Modules | Vocabulary YAMLs | Total Words | Avg per File |
|-------|---------|------------------|-------------|--------------|
| **A1** | 44 | 87 | 820 | 9.4 |
| **A2** | 70 | 139 | 2,591 | 18.6 |
| **B1** | 92 | 183 | 6,422 | 35.1 |

**Note:** More YAML files than modules because:
- Some modules have multiple vocabulary files (activities, review, etc.)
- Some support files (checkpoints, reviews) have separate vocabularies

### YAML Schema (v2.0)

```yaml
module: 01-how-to-talk-about-grammar
level: B1
version: '2.0'
items:
  - lemma: граматика            # Ukrainian word (dictionary form)
    ipa: /ɦramˈatɪka/          # IPA pronunciation with stress
    translation: grammar        # English translation
    pos: noun                   # Part of speech (noun, verb, adj, adv, etc.)
    gender: f                   # For nouns: m, f, n (pl for pluralia tantum)

  - lemma: вивчити
    ipa: /ʋˈɪʋt͡ʃɪtɪ/
    translation: to learn (perfective)
    pos: verb
    # No gender for verbs
```

**Fields:**
- `lemma` (required) - Ukrainian word in dictionary form
- `ipa` (required) - IPA notation with stress mark (`)
- `translation` (required) - English translation
- `pos` (required) - Part of speech: noun, verb, adj, adv, pron, prep, conj, part, interj, num
- `gender` (required for nouns) - m, f, n, or pl

**Empty translations:** Some entries have `translation: ''` indicating:
- Not yet enriched
- Requires manual translation (idioms, proper nouns)
- Malformed entry needing cleanup

---

## 3. Extraction Workflow

### Overview Diagram

```
┌─────────────────────┐
│ 1. Write Module     │
│    Content (.md)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 2. Extract Vocab    │
│    (manual/script)  │ ← Creates skeleton YAML with empty IPA/translation
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 3. Enrich YAML      │
│    (add IPA/trans)  │ ← Fills in IPA and translations
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 4. Rebuild Database │
│    (vocab:rebuild)  │ ← Scans all YAMLs, populates DB
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 5. Delta Extraction │
│    (next module)    │ ← Filters against known words from DB
└─────────────────────┘
```

### Step-by-Step Process

#### Step 1: Write Module Content

Create markdown module with Ukrainian text:
- Prose sections (explanations, examples, stories)
- Activity instructions
- Grammar descriptions

**Where vocabulary comes from:**
- Content planning (curriculum plan specifies target words)
- Natural usage in prose
- Grammar terminology (metalanguage)
- Cultural context words

#### Step 2: Extract Vocabulary

**Method 1: Automatic Extraction** (PRIMARY)

```bash
# Extract vocabulary from markdown
.venv/bin/python scripts/vocab_extract_proper.py curriculum/l2-uk-en/b1/01-how-to-talk-about-grammar.md
```

**What it does:**
1. Reads markdown file
2. Skips frontmatter, code blocks, tables, callouts
3. Extracts all Ukrainian words (Cyrillic pattern matching)
4. Uses `pymorphy3` to lemmatize (convert to dictionary form)
5. Filters stopwords (~80 common words)
6. **Filters against database** (delta extraction) - skips words already in DB
7. Detects POS and gender using morphology
8. Creates skeleton YAML with empty IPA/translation

**Output:** `curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml`

```yaml
items:
  - lemma: граматика
    ipa: ''                    # Empty - needs enrichment
    translation: ''            # Empty - needs enrichment
    pos: noun
    gender: f
```

**Method 2: Manual Creation**

For modules with little prose or special vocabulary needs, manually create YAML.

**⚠️ CRITICAL LIMITATION:**
- Extraction ONLY processes **markdown files**
- Activities YAML files are **NOT extracted**
- Words appearing only in activities may be missed

#### Step 3: Enrich YAML

**Option A: Using JSON dataset**

```bash
.venv/bin/python scripts/enrich_yaml_vocab.py path/to/enrichment.json
```

Expects JSON format:
```json
[
  {
    "file": "curriculum/l2-uk-en/b1/01-how-to-talk-about-grammar.md",
    "enrichments": {
      "граматика": {
        "ipa": "/ɦramˈatɪka/",
        "en": "grammar"
      }
    }
  }
]
```

**Option B: Manual editing**

Edit YAML files directly to add IPA and translations.

**Option C: NLP enrichment** (experimental)

```bash
.venv/bin/python scripts/vocab_enrich_nlp.py curriculum/l2-uk-en/b1/vocabulary/*.yaml
```

Uses:
- `ukrainian-word-stress` library for stress marks
- Cyrillic→IPA conversion
- May require manual translation review

#### Step 4: Rebuild Database

After all vocabulary YAMLs are created/enriched:

```bash
npm run vocab:rebuild
```

**What happens:**
1. `npm run vocab:init:force` - Creates/clears database schema
2. `npm run vocab:scan` - Runs `populate_vocab_db.py`

**populate_vocab_db.py:**
- Scans all `{level}/vocabulary/*.yaml` files
- Extracts module number from filename (`01-title.yaml` → 1)
- Inserts/updates lemmas in database
- Links vocabulary to modules via `module_vocabulary` table
- Marks words as "new" or "review" based on first_module

**Result:** Database updated with all vocabulary, enables delta extraction for next modules

#### Step 5: Delta Extraction (Next Module)

When extracting vocabulary for a new module:

```bash
.venv/bin/python scripts/vocab_extract_proper.py curriculum/l2-uk-en/b1/92-b1-final-exam.md
```

Script checks database:
```python
known_lemmas = get_known_lemmas(db_path)  # Gets 9,619 lemmas from DB
# ... extract words ...
if lemma in known_lemmas:
    continue  # Skip - already known
```

**Result:** Only NEW vocabulary extracted, preventing duplicates

---

## 4. Common Scenarios

### Scenario 1: Creating First Module in a Level (A1 M01)

```bash
# 1. Write module
vim curriculum/l2-uk-en/a1/01-greetings.md

# 2. Extract vocabulary (no database yet, extracts everything)
.venv/bin/python scripts/vocab_extract_proper.py curriculum/l2-uk-en/a1/01-greetings.md

# 3. Enrich YAML (manual or script)
vim curriculum/l2-uk-en/a1/vocabulary/01-greetings.yaml

# 4. Rebuild database (initializes A1 vocabulary)
npm run vocab:rebuild
```

**Output:**
- `01-greetings.yaml` with ~10 words
- Database has 10 A1 lemmas
- Next module (02) will filter these 10 words

### Scenario 2: Creating Mid-Level Module (B1 M50)

```bash
# 1. Write module
vim curriculum/l2-uk-en/b1/50-some-topic.md

# 2. Extract vocabulary (filters against 6,371 B1 lemmas + all A2 + all A1)
.venv/bin/python scripts/vocab_extract_proper.py curriculum/l2-uk-en/b1/50-some-topic.md

# Result: Only words NEW to B1 M50 are extracted (maybe 5-10 words)
```

**Database filtering:**
- Skips all words from B1 M01-49
- Skips all A2 vocabulary (2,531 words)
- Skips all A1 vocabulary (717 words)
- Total filtered: ~9,619 words

### Scenario 3: Final Exam Module (B1 M92)

```bash
# Extract vocabulary
.venv/bin/python scripts/vocab_extract_proper.py curriculum/l2-uk-en/b1/92-b1-final-exam.md

# Output:
# 0 words extracted → All review vocabulary
```

**Why 0 words?**
- Final exam uses only review vocabulary
- All words already in database from previous modules
- This is **expected and correct**

**But:** The vocab YAML may still exist with manually curated entries for:
- Important review words to highlight
- Key terms for self-assessment
- Words central to exam topics

### Scenario 4: Adding New Content to Existing Module

```bash
# 1. Edit module, add new content
vim curriculum/l2-uk-en/b1/30-some-module.md

# 2. Re-extract (will skip old words, only get new)
.venv/bin/python scripts/vocab_extract_proper.py curriculum/l2-uk-en/b1/30-some-module.md

# 3. Compare new YAML with old
# Manually merge or replace

# 4. Rebuild database
npm run vocab:rebuild
```

---

## 5. Tools Reference

### Extraction Tools

| Script | Purpose | Usage |
|--------|---------|-------|
| `vocab_extract_proper.py` | Main extraction with pymorphy3 lemmatization | `.venv/bin/python scripts/vocab_extract_proper.py {md_file}` |
| `auto_vocab_extract.py` | Alternative extraction with POS heuristics | `.venv/bin/python scripts/auto_vocab_extract.py {md_file}` |
| `vocab_trace_sources.py` | Diagnostic - trace word sources | `.venv/bin/python scripts/vocab_trace_sources.py {md_file}` |

### Enrichment Tools

| Script | Purpose | Usage |
|--------|---------|-------|
| `enrich_yaml_vocab.py` | Enrich from JSON dataset | `.venv/bin/python scripts/enrich_yaml_vocab.py {json_file}` |
| `vocab_enrich_nlp.py` | Auto-generate IPA and stress | `.venv/bin/python scripts/vocab_enrich_nlp.py {yaml_files}` |

### Database Tools

| Script | Purpose | Usage |
|--------|---------|-------|
| `vocab_init.py` | Initialize database schema | `npm run vocab:init:force` |
| `populate_vocab_db.py` | Scan YAMLs and populate DB | `npm run vocab:scan` |
| `rebuild_vocab_from_yaml.py` | Rebuild DB from YAML files | `.venv/bin/python scripts/rebuild_vocab_from_yaml.py --force` |

### Validation Tools

| Script | Purpose | Usage |
|--------|---------|-------|
| `global_vocab_audit.py` | Cross-module vocabulary audit | `.venv/bin/python scripts/global_vocab_audit.py --level b1` |
| `validate_vocab_yaml.py` | YAML schema validation | `.venv/bin/python scripts/validate_vocab_yaml.py {yaml_file}` |
| `audit_module.py` | Module audit (includes vocab check) | `.venv/bin/python scripts/audit_module.py {md_file}` |

### Migration Tools (Legacy)

| Script | Purpose | Notes |
|--------|---------|-------|
| `migrate_vocab_to_yaml.py` | Extract vocab from markdown tables | Used for A1/A2 migration |
| `cleanup_b1plus_vocab_lists.py` | Remove old vocab sections from markdown | Legacy cleanup |
| `clear_vocab_sections.py` | Strip vocab tables from markdown | Legacy |

---

## 6. Common Issues and Solutions

### Issue 1: Extraction Produces 0 Words

**Symptom:** `vocab_extract_proper.py` reports "0 lemmas" for a module with Ukrainian content

**Causes:**
1. **Delta filtering working correctly** - All words already in database (expected for review/exam modules)
2. **Content in blockquotes** - Extraction may skip `>` prefixed lines
3. **Content in activities YAML** - Extraction doesn't process YAML files

**Diagnosis:**
```bash
# Check word sources
.venv/bin/python scripts/vocab_trace_sources.py curriculum/l2-uk-en/b1/92-b1-final-exam.md

# Output shows:
#   Words in markdown: 1,550
#   Words in activities: 1,041
#   Words in vocab YAML: 0 or N
#   Words NOT in vocab YAML: X
```

**Solutions:**
- If delta filtering: Expected behavior, no action needed
- If blockquote issue: Fix `extract_ukrainian_text()` function
- If activities issue: Extract activities separately or manually add words

### Issue 2: Vocabulary YAML Has Empty Translations

**Symptom:** Many entries with `translation: ''`

**Causes:**
1. Enrichment not run yet
2. Enrichment JSON missing words
3. Manual creation without translation

**Solution:**
```bash
# Run enrichment
.venv/bin/python scripts/vocab_enrich_nlp.py curriculum/l2-uk-en/b1/vocabulary/*.yaml

# Or manually edit YAMLs
# Or create enrichment JSON and run enrich_yaml_vocab.py
```

### Issue 3: Database and YAML Counts Don't Match

**Symptom:**
- YAML files: 820 words (A1)
- Database: 717 lemmas (A1)
- Difference: 103 words

**Causes:**
1. **Duplicates across YAMLs** - Same word in multiple module YAMLs, but DB enforces uniqueness
2. **Malformed entries** - Invalid lemmas skipped during DB population
3. **Multi-word expressions** - Some entries are expressions, not lemmas
4. **YAMLs not scanned** - Some YAML files in vocabulary/ dir aren't linked to modules

**Diagnosis:**
```bash
# Check for duplicate lemmas across YAMLs
rg "lemma: бути" curriculum/l2-uk-en/a1/vocabulary/*.yaml

# Check database uniqueness
sqlite3 curriculum/l2-uk-en/vocabulary.db "SELECT uk, COUNT(*) FROM lemmas WHERE level='A1' GROUP BY uk HAVING COUNT(*) > 1;"
```

**Solution:**
- Duplicates are normal (same word taught multiple times, DB stores once)
- Verify critical words are in DB using SQL queries
- Malformed entries need manual cleanup

### Issue 4: Lemmas Not in Dictionary Form

**Symptom:** YAML entries like `відлетів-` or `жвава` (inflected forms, not lemmas)

**Causes:**
1. pymorphy3 failed to lemmatize
2. Manual entry error
3. Extraction from inflected text without lemmatization

**Solution:**
```bash
# Test lemmatization
.venv/bin/python -c "
from pymorphy3 import MorphAnalyzer
morph = MorphAnalyzer(lang='uk')
print(morph.parse('жвава')[0].normal_form)  # Should output: жвавий
"

# Manually fix YAML entries to dictionary form
```

### Issue 5: Activities Vocabulary Missing

**Symptom:** Words in activities YAML not in vocabulary YAML

**Root cause:** `vocab_extract_proper.py` only processes markdown, not activities YAML

**Workaround:**
1. **Manual extraction** - Read activities, add words to YAML manually
2. **Trace script** - Use `vocab_trace_sources.py` to identify activity-only words
3. **Feature request** - Extend extraction to process activities YAML

**Long-term solution:** Modify extraction pipeline to include activities as a source

---

## 7. Vocabulary Workflow by Level

### A1 (Complete)

- **Modules:** 44
- **Vocabulary:** 717 lemmas in database, 820 in YAMLs (87 files)
- **Status:** Complete, database populated
- **Extraction mode:** Most extracted, some manual

**Characteristics:**
- Small vocabulary per module (~9 words avg)
- Basic concrete nouns, common verbs
- Foundational grammar terms
- High-frequency words

### A2 (Complete)

- **Modules:** 70
- **Vocabulary:** 2,531 lemmas in database, 2,591 in YAMLs (139 files)
- **Status:** Complete, database populated
- **Extraction mode:** Delta extraction (filters 717 A1 words)

**Characteristics:**
- Medium vocabulary per module (~18 words avg)
- Past/future tense verbs
- Case system vocabulary
- More abstract concepts

### B1 (Complete)

- **Modules:** 92
- **Vocabulary:** 6,371 lemmas in database, 6,422 in YAMLs (183 files)
- **Status:** Complete, database populated
- **Extraction mode:** Delta extraction (filters 3,248 A1+A2 words)

**Characteristics:**
- Large vocabulary per module (~35 words avg)
- Aspect system metalanguage
- Motion verbs with prefixes
- Academic and abstract vocabulary
- Complex grammar terminology

---

## 8. Key Principles

### 1. Cumulative Vocabulary

Each level builds on all previous levels:
```
A1: 717 words (new)
A2: 2,531 words (includes review of 717 A1 words)
B1: 6,371 words (includes review of 3,248 A1+A2 words)
```

Delta extraction ensures only NEW words are captured.

### 2. Database as Source of Truth

The SQLite database is the canonical source for:
- Which words have been taught
- At which module words were introduced
- Cumulative vocabulary counts

YAML files are sources that feed the database.

### 3. Lemmatization is Critical

All vocabulary must be stored in **dictionary form** (lemma):
- Nouns: nominative singular (дім, not доми)
- Verbs: infinitive (читати, not читав)
- Adjectives: masculine nominative singular (новий, not нова)

pymorphy3 handles this automatically during extraction.

### 4. Delta Extraction Prevents Duplication

Each module's vocabulary YAML contains only:
- NEW words introduced in that module
- OR: Key review words worth highlighting

The database tracks ALL cumulative vocabulary, not individual YAMLs.

### 5. Separation of Concerns

```
Markdown content    → What students read/learn
Vocabulary YAML     → New words introduced in this module
Database            → Cumulative vocabulary across all modules
Activities YAML     → Interactive exercises (currently NOT extracted)
```

---

## 9. Future Improvements

### 1. Extract from Activities YAML

**Problem:** 632 words in M92 activities not captured

**Solution:**
- Modify `vocab_extract_proper.py` to also process activities/*.yaml
- Parse YAML, extract Ukrainian text from activity fields
- Lemmatize and merge with markdown extraction

### 2. Improve Blockquote Handling

**Problem:** Markdown extraction may skip blockquoted content

**Solution:**
- Fix `extract_ukrainian_text()` to properly handle all `>` prefixed lines
- Test on modules with extensive blockquote usage

### 3. Validation and Quality Checks

**Improvements needed:**
- Detect malformed lemmas (trailing hyphens, fragments)
- Validate POS matches word endings
- Flag empty translations for review
- Check for Surzhyk (Russian-Ukrainian mixed forms)

### 4. Automated Enrichment Pipeline

**Goal:** Reduce manual translation work

**Components:**
- Auto-generate IPA using `ukrainian-word-stress` (exists)
- LLM-based translation with context (partial)
- Validation against known dictionaries
- Manual review queue for uncertain translations

---

## 10. Quick Reference Commands

```bash
# Extract vocabulary from new module
.venv/bin/python scripts/vocab_extract_proper.py curriculum/l2-uk-en/b1/50-new-module.md

# Trace vocabulary sources (diagnostic)
.venv/bin/python scripts/vocab_trace_sources.py curriculum/l2-uk-en/b1/92-b1-final-exam.md

# Enrich YAML with IPA/translations
.venv/bin/python scripts/vocab_enrich_nlp.py curriculum/l2-uk-en/b1/vocabulary/50-new-module.yaml

# Rebuild entire database
npm run vocab:rebuild

# Audit vocabulary for a level
.venv/bin/python scripts/global_vocab_audit.py --level b1

# Check database contents
sqlite3 curriculum/l2-uk-en/vocabulary.db "SELECT level, COUNT(*) FROM lemmas GROUP BY level;"

# Find YAMLs with empty translations
rg -l "translation: ''" curriculum/l2-uk-en/b1/vocabulary/*.yaml
```

---

## Conclusion

The vocabulary extraction system is a **three-stage pipeline**:

1. **Extraction** - Pull words from markdown using pymorphy3
2. **Enrichment** - Add IPA and translations to YAML files
3. **Database Rebuild** - Populate central DB from all YAMLs

**Delta extraction** ensures only new vocabulary is captured, preventing duplication across the cumulative curriculum.

**Current limitation:** Activities YAML files are not processed during extraction, leading to incomplete vocabulary coverage for modules with extensive interactive content.

**For A1, A2, B1:** All levels complete with 9,619 total lemmas in the database, ready for B2+ delta extraction.
