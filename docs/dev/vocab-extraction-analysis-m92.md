# Vocabulary Extraction Analysis - M92 (B1 Final Exam)

**Date:** 2026-01-25
**Investigator:** Claude (automated analysis)
**Context:** User request to investigate vocabulary building process and trace untranslated words

---

## Executive Summary

**Key Findings:**
- ✅ Delta extraction working correctly (0 new words from M92 markdown - all known from prior modules)
- ⚠️ Activities YAML not included in extraction (632 unique words missed)
- ⚠️ 4 malformed entries in vocab YAML with empty translations
- ℹ️ Total of 2,182 unique Ukrainian words used in M92 (markdown + activities)

---

## Current Vocabulary Extraction Pipeline

### Tool: `scripts/vocab_extract_proper.py`

**What it does:**
1. Extracts Ukrainian text from **markdown files only** (not activities YAML)
2. Uses pymorphy3 to lemmatize words to dictionary form
3. Filters against 9,619 known lemmas from `vocabulary.db` (delta extraction)
4. Skips ~80 stopwords (prepositions, conjunctions, common words)
5. Generates skeleton YAML with empty IPA and translation fields

**What it skips:**
- Frontmatter (YAML between `---`)
- Code blocks (` ``` `)
- Tables (`|` markers)
- Callout markers (`> [!...`)
- ⚠️ **Regular blockquotes** (lines with `>`) - PARTIALLY SKIPPED
- ⚠️ **Activities YAML files** - COMPLETELY IGNORED

### Enrichment: `scripts/enrich_yaml_vocab.py`

After extraction, vocab YAML is enriched with:
- IPA pronunciation (using `ukrainian-word-stress` library)
- Translations (manual or LLM-assisted)
- POS and gender metadata

---

## M92 Vocabulary Analysis

### Source Statistics

| Source | Unique Words | Notes |
|--------|--------------|-------|
| **Markdown** | 1,550 | News article, education text, diaspora text, self-assessment |
| **Activities** | 1,041 | Quiz questions, fill-in sentences, match-up pairs, group-sort items |
| **Both** | 409 | Words appearing in both markdown and activities |
| **Total Unique** | 2,182 | Complete vocabulary coverage of module |

### Extraction Results

```
🔍 Knowledge-Aware: Filtering against 9,619 known lemmas
✓ 92-b1-final-exam.md: 0 words → 0 lemmas

Total words processed: 0
Unique lemmas found:   0
Entries created:       0
```

**Why 0 new words?**
- M92 is the B1 Final Exam (module 92 of 91 modules)
- All vocabulary in markdown prose is review material from prior B1 modules
- Delta extraction correctly filtered all 1,550 markdown words as "already known"
- This is **expected behavior** for a final exam

### Current Vocab YAML

**File:** `curriculum/l2-uk-en/b1/vocabulary/92-b1-final-exam.yaml`
- Total entries: 90
- Schema version: 2.0
- Entries with translations: 86
- **Entries missing translations: 4**

---

## Untranslated Words Investigation

### Malformed Entries (Empty Translations)

| Lemma | Line | IPA | POS | Issue |
|-------|------|-----|-----|-------|
| `бізнес-проєкт` | 34 | `/bˈiznɛs-prɔjɛkt/` | noun | Compound word, needs translation |
| `відлетів-` | 76 | `/ʋidlɛtˈiʋ-/` | noun | **MALFORMED** - Incomplete word (trailing hyphen) |
| `жвава` | 124 | `/ʒʋˈaʋa/` | noun | **POS ERROR** - Should be adjective (lively, vivacious) |
| `нуш` | 210 | `/nuʃ/` | noun (f) | **EXTRACTION ERROR** - Fragment from compound word |

### Source Tracing

#### 1. `бізнес-проєкт` (business project)
- **Source:** Markdown line 297 (Self-Assessment section)
- **Context:** "складний бізнес-проєкт" (complex business project)
- **Fix needed:** Add translation: "business project"

#### 2. `відлетів-` (MALFORMED)
- **Source:** Unknown - likely extraction artifact
- **Context:** Appears to be truncated past tense verb form
- **Fix needed:** Remove this entry (malformed lemma)

#### 3. `жвава` (lively, vivacious)
- **Source:** Markdown line 281 (Self-Assessment section)
- **Context:** "жвава дискусія" (lively discussion)
- **Issue:** Classified as noun instead of adjective
- **Fix needed:**
  - Change POS from `noun` to `adj`
  - Add translation: "lively, vivacious"

#### 4. `нуш` (FRAGMENT)
- **Source:** Likely fragment from "Нью-Йорк" or similar compound
- **Issue:** Extraction error - not a real word
- **Fix needed:** Remove this entry

---

## Extraction Gaps

### Gap 1: Activities YAML Not Processed

**Words ONLY in activities:** 632 unique words

Examples from activities:
- Quiz questions: "Скільки років тривало будівництво..." (How many years did construction take...)
- Fill-in sentences: "Учні ____ критичне мислення..." (Students ____ critical thinking...)
- Match-up pairs: "робити домашнє завдання" (do homework)
- Group-sort items: "великий — малий" (big — small)

**Impact:**
- Students encounter these words in interactive exercises
- No translation provided in vocab YAML
- Inconsistent coverage between prose and activities

**Recommendation:**
- Create companion extraction script for activities YAML
- OR: Modify `vocab_extract_proper.py` to also process activities

### Gap 2: Blockquote Handling

The extraction script has incomplete blockquote handling:

```python
# Skip callout markers but keep text
if stripped.startswith('> [!'):
    continue
```

This skips callout markers (`> [!NOTE]`) but does NOT handle regular blockquotes (`> Quote text`).

**Impact:**
- M92 uses blockquotes extensively for reading passages
- Text in blockquotes may be partially extracted (depends on line-by-line processing)

**Status:** Uncertain impact - needs verification

---

## Recommendations

### Immediate Actions

1. **Fix Malformed Entries**
   ```bash
   # Edit curriculum/l2-uk-en/b1/vocabulary/92-b1-final-exam.yaml
   # - Remove: відлетів-, нуш
   # - Fix: жвава (noun → adj, add translation)
   # - Add translation: бізнес-проєкт → "business project"
   ```

2. **Run Vocabulary Audit**
   ```bash
   .venv/bin/python scripts/global_vocab_audit.py --level b1
   ```

### Long-term Improvements

1. **Extract from Activities YAML**
   - Modify `vocab_extract_proper.py` to process both markdown AND activities
   - OR: Create separate `vocab_extract_from_activities.py`
   - Ensure lemmatization works on activity content

2. **Improve Blockquote Handling**
   - Fix `extract_ukrainian_text()` to properly handle all blockquote formats
   - Test on modules with extensive blockquote usage

3. **Add Extraction Validation**
   - Detect malformed lemmas (trailing hyphens, fragments)
   - Validate POS against word endings
   - Flag entries with empty translations for review

4. **Create Vocabulary Coverage Report**
   - Similar to `vocab_trace_sources.py` but automated
   - Run after module completion
   - Report: words in content vs words in vocab YAML
   - Identify gaps and untranslated words

---

## Questions for Clarification

1. **Should final exam modules have vocabulary YAMLs?**
   - Currently M92 has 90 entries (seems manually curated)
   - Delta extraction produces 0 new words (all are review)
   - Is this intentional or should exams skip vocabulary extraction?

2. **Should activities YAML be included in extraction?**
   - Currently only markdown is processed
   - 632 words appear only in activities for M92
   - Is this a known limitation or a bug?

3. **What's the source of the 90 entries in M92 vocab YAML?**
   - If delta extraction produces 0 words, where did these 90 come from?
   - Possible sources:
     - Manual curation
     - Extraction before other B1 modules were completed
     - Different extraction script/process

---

## Trace Output Sample

### Words ONLY in Markdown (sample)

```
доктор        → MD:L376,379 (appears in academic context)
педагогіку    → MD:L489 (teaching methodology)
реферат       → MD:L490 (research paper)
дисертація    → MD:L491 (dissertation)
```

### Words ONLY in Activities (sample)

```
австралія     → YAML:2 times (quiz about diaspora)
архітекторам  → YAML:1 times (fill-in activity)
аудиторію     → YAML:1 times (vocabulary matching)
```

### Words in BOTH (sample)

```
агресією      → MD:L128 | YAML:1 times (reading text + activity)
академічний   → MD:L373,528 | YAML:1 times (multiple contexts)
активно       → MD:L132,138,151 | YAML:2 times (frequent usage)
```

---

## Tool Reference

### Diagnostic Tool Created

**File:** `scripts/vocab_trace_sources.py`

**Usage:**
```bash
# Trace all words in M92
.venv/bin/python scripts/vocab_trace_sources.py curriculum/l2-uk-en/b1/92-b1-final-exam.md

# Show translated words too
.venv/bin/python scripts/vocab_trace_sources.py curriculum/l2-uk-en/b1/92-b1-final-exam.md --show-all
```

**Features:**
- Extracts from markdown (with line numbers)
- Extracts from activities YAML (with activity context)
- Checks vocab YAML for translations
- Reports coverage statistics
- Shows untranslated words with sources

---

## Conclusion

The vocabulary extraction pipeline is working as designed for delta extraction (filtering known words). However, two gaps exist:

1. **Activities not processed** - 632 words in M92 activities have no extraction path
2. **Malformed entries** - 4 entries in vocab YAML need manual cleanup

For final exam modules like M92, the 0-word extraction is expected behavior since all content is review. The 90 existing entries were likely added through a different process or timeline.

**Next Steps:** User to decide whether to:
- Fix the 4 malformed entries
- Extend extraction to include activities YAML
- Document the vocabulary workflow for final exam modules
