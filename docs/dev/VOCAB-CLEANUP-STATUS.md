# B1 Vocabulary Cleanup Status

**Issue:** [#462](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/462)
**Started:** 2026-01-25
**Last Updated:** 2026-01-25

---

## Overall Status

- ✅ **Phase 1: Cleanup** - COMPLETE
- ⏳ **Phase 2: Translation** - PENDING
- ⏳ **Phase 3: Database Sync** - PENDING

---

## Phase 1: Cleanup ✅ COMPLETE

**Completed:** 2026-01-25
**Commit:** `136f4b6d`

### Actions Completed

- [x] Deleted 64 fragment entries (prefixes, quoted forms, incomplete words)
- [x] Fixed 5 malformed entries (typos, Russicisms, gerunds)
- [x] Added missing `давальний` (dative case) entry
- [x] Fixed `місцевий` translation to include "locative (case)"
- [x] Created `data/translations/` infrastructure
- [x] Created translation workflow documentation
- [x] Created `b1-manual-translations.json` placeholder

### Results

- **Files modified:** 23
- **Entries removed:** 64
- **Entries fixed:** 5
- **Entries added:** 1
- **Translations updated:** 1
- **Total impact:** 71 vocabulary entries improved

---

## Phase 2: Translation ⏳ PENDING

**Status:** Awaiting user decision on approach

### Scope

- **324 words** marked as "likely valid" need verification
- **111 words** marked as "likely fragments" need review
- **Total:** 435 words to process

### High-Priority Words (Already Identified)

Sample translations ready in `b1-manual-translations.json`:
- `застосування` → "application, use"
- `присудок` → "predicate"
- `чумаки` → "chumaks"
- `геймерський` → "gamer (adj)"

### Approach Options

**Option A: Manual Translation (Thorough)**
- Review each word in `/tmp/b1-likely-valid-for-translation.txt`
- Search Ukrainian-English dictionaries
- Verify against markdown source files
- Add to `b1-manual-translations.json`
- **Time:** High | **Quality:** Highest

**Option B: Batch Translation + Verification (Balanced)**
- Use external LLM (GPT-4, Claude) for batch translation
- Manually verify each translation
- Cross-check against dictionaries
- Add verified translations to JSON
- **Time:** Medium | **Quality:** High

**Option C: Prioritized Approach (Pragmatic)**
- Focus on high-frequency words first (appear in markdown)
- Filter out obvious fragments
- Translate ~100 most important words
- Leave rare/questionable words for later
- **Time:** Low | **Quality:** Medium

### Tools Available

- `/tmp/b1-likely-valid-for-translation.txt` - 324 candidate words
- `data/translations/b1-manual-translations.json` - Translation storage
- `scripts/apply_translations_batch.py` - Apply translations to YAMLs
- External dictionaries: Словник.ua, Glosbe, academic sources

---

## Phase 3: Database Sync ⏳ PENDING

**Dependencies:** Phase 2 completion

### Tasks

- [ ] Apply translations from JSON to YAMLs
- [ ] Rebuild database from YAMLs
- [ ] Regenerate YAMLs from database (consistency check)
- [ ] Run vocabulary audit
- [ ] Verify all untranslated count reduced
- [ ] Commit final changes (YAMLs + JSON + DB)

### Commands

```bash
# Apply translations
.venv/bin/python scripts/apply_translations_batch.py \
  --translations data/translations/b1-manual-translations.json \
  --level b1

# Rebuild database
.venv/bin/python scripts/rebuild_vocab_from_yaml.py --force --levels b1

# Regenerate YAMLs (consistency check)
.venv/bin/python scripts/regenerate_vocab_yamls.py --level b1

# Validate
.venv/bin/python scripts/audit/core.py --level b1
```

---

## Translation Storage Architecture

### Files

```
data/translations/
├── README.md                      # Workflow documentation
├── a1-gemini-translations.json    # A1 automated translations
├── a2-gemini-translations.json    # A2 automated translations
├── b1-gemini-translations.json    # B1 automated translations
└── b1-manual-translations.json    # B1 manual cleanup (Issue #462) ← NEW
```

### Workflow

```
Manual Translation → JSON Archive → apply_translations_batch.py → YAMLs → rebuild DB
                          ↓
                    (git commit)
```

### Benefits

✅ **Version Control:** All translations tracked in git (JSON + YAML)
✅ **Fast Rebuild:** Database regenerated from YAMLs anytime
✅ **Separation:** Manual work preserved separately from automated
✅ **Audit Trail:** Clear history of all translation changes
✅ **Reproducibility:** Entire process can be replayed from JSON

---

## Documentation

### Investigation Files

- `docs/dev/b1-untranslated-investigation-report.md` - Full investigation
- `docs/dev/vocab-translation-workflow-actual.md` - Translation workflow
- `docs/dev/vocab-extraction-workflow-overview.md` - Extraction process

### Phase Reports

- `docs/dev/b1-cleanup-phase1-complete.md` - Phase 1 summary
- `docs/dev/VOCAB-CLEANUP-STATUS.md` - This file (overall status)

### Temporary Files (Analysis)

- `/tmp/b1-untranslated-full.txt` - All 504 untranslated words
- `/tmp/b1-to-remove.txt` - 54 deleted entries
- `/tmp/b1-to-fix.txt` - 15 fixed entries
- `/tmp/b1-likely-valid-for-translation.txt` - 324 candidates
- `/tmp/b1-valid-need-translation.txt` - Alternative filter

---

## Key Findings

### Mnemonic Abbreviations (User Hypothesis Confirmed ✅)

User was **correct** about hyphenated abbreviations having valid pedagogical purpose:

**Mnemonic:** "На Різдво Дід Загубив Орішки Між Ковбасками"
- **Н**-азивний (nominative)
- **Р**-одовий (genitive)
- **Д**-авальний (dative)
- **З**-нахідний (accusative)
- **О**-рудний (instrumental)
- **М**-ісцевий (locative)
- **К**-личний (vocative)

**Decision:** Removed abbreviations since full case names exist with translations.

### Why Gemini Failed (~9% of words)

1. **Malformed lemmas** - Hyphenated abbreviations, fragments
2. **Non-lemma forms** - Participles, gerunds not infinitives
3. **Extraction errors** - Typos, prefixes as words
4. **Rare technical terms** - Grammar metalanguage
5. **Fragments** - Parts of compound words

### Critical Issues Found and Fixed

1. ✅ **Missing case name:** Added `давальний` (dative)
2. ✅ **Incorrect translation:** Fixed `місцевий` (now includes "locative case")
3. ✅ **Malformed mnemonics:** Removed `к-личнити`, `н-азивнити`, `з-нахіднити`
4. ✅ **Russicisms:** Fixed `корень` → `корінь`
5. ✅ **Typos:** Fixed `граматик` → `граматика`

---

## Next Actions

### Immediate (User Decision Required)

1. **Choose Phase 2 approach** (Option A, B, or C)
2. **Review Phase 1 changes** with `git diff 136f4b6d^..136f4b6d`
3. **Push Phase 1 to remote** (if approved)

### Phase 2 Execution (Once Approved)

1. Load translation candidates
2. Verify and translate words
3. Update `b1-manual-translations.json`
4. Apply translations to YAMLs
5. Commit translation changes

### Phase 3 Finalization

1. Rebuild database from YAMLs
2. Run validation audit
3. Verify untranslated count
4. Final commit with database sync

---

## Questions & Answers

**Q: Did we miss anything?**

✅ **Translation storage** - JSON + YAML + DB (covered)
✅ **Version control** - All changes tracked in git (covered)
✅ **Reproducibility** - Workflow documented (covered)
✅ **Fast rebuild** - Database from YAMLs (covered)
✅ **Separation** - Manual vs automated translations (covered)

**Potential additions:**
- Consider extending cleanup to A1, A2 levels (same issues likely exist)
- Add automated tests to catch future extraction errors
- Create vocabulary quality metrics dashboard
- Document extraction script improvements to prevent recurrence

**Q: Should we automate any of this?**

Suggestions:
- **Pre-commit hook** to validate vocabulary YAMLs (no fragments, all translations present)
- **CI check** to count untranslated words and fail if threshold exceeded
- **Extraction validation** to catch malformed lemmas before adding to YAMLs

---

**Last Updated:** 2026-01-25 by Claude Sonnet 4.5
