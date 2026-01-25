# B1 Vocabulary Cleanup - Phase 1 Complete

**Date:** 2026-01-25
**Issue:** #462
**Status:** ✅ Phase 1 Complete | ⏳ Phase 2 Pending

---

## Phase 1 Results

### Actions Completed

✅ **Deleted 64 fragment entries** across 23 vocabulary files
- Prefixes: `в-`, `ви-`, `за-`, `на-`, `пере-`, `пис-`, `при-`, etc.
- Quoted forms: `да'`, `не'`, `так'`, `вже'`, `писати'`
- Incomplete words: `написа-`, `топ-`, `від-`, `під-`, `роз-`
- Fragments: `дв`, `зно`, `літ`, `му`, `мч`, `ндв`, `тч`, `род`, `ус`
- Malformed mnemonics: `к-личнити`, `н-азивнити`

✅ **Fixed 5 malformed entries**
- `граматик` → `граматика` (typo corrected)
- `корень` → `корінь` (Russicism fixed)
- `застосовуючи` → `застосовувати` (gerund → infinitive)
- `калькуючи` → `калькувати` (gerund → infinitive)
- `вивчаючи` → `вивчати` (gerund → infinitive)

✅ **Added missing case name**
- Added `давальний` (dative case) to M01 vocabulary

✅ **Fixed existing translation**
- Updated `місцевий`: "local" → "local, locative (case)"

✅ **Created translation storage infrastructure**
- Created `data/translations/` directory
- Added `README.md` documenting translation workflow
- Created `b1-manual-translations.json` placeholder

### Files Modified

23 vocabulary YAML files updated:
- 01-how-to-talk-about-grammar.yaml
- 03-reading-grammar-rules.yaml
- 10-aspect-negation.yaml
- 12-aspect-pairs-essential-40.yaml
- 14-aspect-integration-practice.yaml
- 15-checkpoint-aspect-mastery.yaml
- 17-motion-coming-going.yaml
- 18-motion-passing-crossing.yaml
- 19-motion-starting-returning.yaml
- 22-motion-full-prefix-integration.yaml
- 23-motion-patterns-other-verbs.yaml
- 25-checkpoint-motion-verbs.yaml
- 41-checkpoint-complex-sentences-2.yaml
- 42-adverbial-participles-imperfective.yaml
- 43-adverbial-participles-perfective.yaml
- 45-past-passive-participles-1.yaml
- 48-diminutives-master-class.yaml
- 51-checkpoint-advanced-grammar.yaml
- 60-society-politics.yaml
- 66-business-basics.yaml
- 79-sports-in-ukraine.yaml
- 88-interviu-ta-podkasty.yaml
- 92-b1-final-exam.yaml

### Statistics

- **Files processed:** 92
- **Files modified:** 23
- **Entries removed:** 64
- **Entries fixed:** 5
- **Entries added:** 1 (давальний)
- **Translations updated:** 1 (місцевий)

---

## Remaining Work (Phase 2)

### Translation Tasks

**Status:** 324 words marked as "likely valid" need verification and translation

**Categories:**
1. **Likely Fragments** (111 words) - Review and filter out
2. **Likely Valid** (324 words) - Translate using external sources

**High-Priority Words Identified:**
- `застосування` → "application, use" ✅ (added to JSON)
- `присудок` → "predicate" ✅ (added to JSON)
- `чумаки` → "chumaks" ✅ (added to JSON)
- `геймерський` → "gamer (adj)" ✅ (added to JSON)

### Translation Sources

Use external trusted sources:
- **Ukrainian-English Dictionaries:**
  - Словник.ua
  - Glosbe
  - Academic dictionaries
- **Grammar References:**
  - Ukrainian grammar terminology guides
  - Linguistic reference materials
- **Verification:**
  - Cross-check against markdown source files
  - Verify usage context

### Workflow for Phase 2

```
1. Load /tmp/b1-likely-valid-for-translation.txt (324 words)
2. For each word:
   a. Search in markdown files for context
   b. Look up in Ukrainian dictionaries
   c. Verify it's a valid lemma (not fragment)
   d. Add translation to b1-manual-translations.json
3. Apply translations via scripts/apply_translations_batch.py
4. Rebuild database via scripts/rebuild_vocab_from_yaml.py
5. Validate with scripts/audit/core.py
6. Commit changes
```

---

## Translation Storage Strategy

### Storage Locations

1. **Primary Source:** YAML files (`curriculum/l2-uk-en/b1/vocabulary/*.yaml`)
   - Human-editable
   - Version-controlled
   - Source of truth

2. **Translation Archive:** JSON files (`data/translations/`)
   - `b1-manual-translations.json` - Manual translations from this cleanup
   - `b1-gemini-translations.json` - Original Gemini translations
   - Version-controlled for history
   - Format: `{ "lemma": "translation" }`

3. **Database:** `vocabulary.db`
   - Queryable cache
   - Rebuilt from YAMLs
   - NOT directly edited

### Benefits

✅ Translations are version-controlled (JSON + YAML)
✅ Database can be quickly rebuilt from YAMLs
✅ Manual work is preserved separately from automated translations
✅ Easy to re-apply translations if YAMLs are regenerated
✅ Clear audit trail of all changes

---

## Next Steps

### For User

1. **Review Phase 1 changes** with `git diff`
2. **Approve or request modifications** before proceeding
3. **Decide on Phase 2 approach:**
   - Option A: Manual translation of all 324 words
   - Option B: Batch translation with external LLM + verification
   - Option C: Prioritize high-frequency words first

### For Implementation

Once approved:
1. Commit Phase 1 changes
2. Begin Phase 2 translation verification
3. Update `b1-manual-translations.json` with verified translations
4. Apply translations to YAMLs
5. Rebuild database
6. Run final validation

---

## Files Generated

**Investigation:**
- `docs/dev/b1-untranslated-investigation-report.md` - Full investigation report
- `/tmp/b1-to-remove.txt` - List of deleted entries
- `/tmp/b1-to-fix.txt` - List of fixed entries
- `/tmp/b1-likely-valid-for-translation.txt` - Translation candidates

**Infrastructure:**
- `data/translations/` - Translation storage directory
- `data/translations/README.md` - Workflow documentation
- `data/translations/b1-manual-translations.json` - Translation archive

**Reports:**
- `docs/dev/b1-cleanup-phase1-complete.md` - This document

---

## Related

- **Issue:** https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/462
- **Investigation:** `docs/dev/b1-untranslated-investigation-report.md`
- **Workflow:** `docs/dev/vocab-translation-workflow-actual.md`
