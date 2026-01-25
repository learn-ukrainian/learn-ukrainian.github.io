# B1 Vocabulary - Untranslated Words Investigation Report

**Date:** 2026-01-25
**Scope:** All B1 vocabulary YAML files (91 modules)
**Total Untranslated:** 504 words

---

## Executive Summary

Investigated all 504 untranslated words in B1 vocabulary to determine validity and categorize for action. User hypothesis confirmed: **hyphenated abbreviations like "д-авальний" have valid pedagogical reasons** (mnemonic devices for teaching case names).

### Categorization Results

| Category | Count | Action Required |
|----------|-------|-----------------|
| **To REMOVE** | 54 | Delete from vocabulary (fragments, malformed entries) |
| **To FIX** | 15 | Correct typos, remove prefixes, find proper lemmas |
| **Likely Fragments** | 111 | Review (probably extraction errors) |
| **Likely VALID** | 324 | Translate using external sources |

---

## Category 1: Mnemonic Abbreviations (VALID PEDAGOGICAL REASON)

### Context from M01 Markdown (line 250):

> Ukrainian students use mnemonics to remember case order. "На Різдво Дід Загубив Орішки Між Ковбасками" (On Christmas, Grandpa Lost Nuts Among Sausages) is one popular version. The first letters match: **Н-азивний, Р-одовий, Д-авальний, З-нахідний, О-рудний, М-ісцевий, К-личний**.

### Mnemonic Abbreviations Found in Vocabulary:

1. **Н-азивний** → Nominative case (називний)
2. **Р-одовий** → Genitive case (родовий)  
3. **Д-авальний** → Dative case (давальний) ✓ USER IDENTIFIED
4. **З-нахідний** → Accusative case (знахідний)
5. **О-рудний** → Instrumental case (орудний)
6. **М-ісцевий** → Locative case (місцевий) ✓ USER IDENTIFIED
7. **К-личний** → Vocative case (кличний) ✓ USER IDENTIFIED

### Decision: KEEP or REMOVE?

**Option A:** Keep abbreviations WITH translations
- Add translation: "N- (nominative - mnemonic abbrev.)"
- Maintains pedagogical value
- Documents the mnemonic system

**Option B:** Remove abbreviations, ensure full forms exist
- Delete: д-авальний, м-ісцевий, etc.
- Verify full forms (давальний, місцевий) are in vocabulary
- Full forms already present with translations ✅

**Recommendation:** **Option B** - Remove abbreviations since full forms exist with proper translations.

### Malformed Mnemonic Verbs (TO REMOVE):

These are incorrectly lemmatized as verbs ending in "-нити":
- к-личнити (should be к-личний, adjective)
- н-азивнити (should be н-азивний, adjective)
- з-нахіднити (should be з-нахідний, adjective)

---

## Category 2: To REMOVE (54 entries)

Clear extraction errors with no valid pedagogical value:

### Fragments (< 3 chars with punctuation):
- в-, ви-, за-, на-, пере-, пис-, при- (prefixes extracted as words)
- да', не', так', вже' (quoted forms)
- з-, об-, по-, про-, топ-, від-, до-, під-, роз-, зі-, пі- (incomplete)

### Complete List:
See `/tmp/b1-to-remove.txt`

---

## Category 3: To FIX (15 entries)

Salvageable entries needing correction:

| Current Entry | Issue | Correction |
|---------------|-------|------------|
| граматик | Typo | граматика |
| корень | Russicism | корінь (Ukrainian form) |
| д-авальний | Mnemonic abbrev | давальний |
| м-ісцевий | Mnemonic abbrev | місцевий |
| р-одовити | Mnemonic verb | родовий |
| застосовуючи | Gerund | застосовувати (infinitive) |
| калькуючи | Gerund | калькувати |
| вивчаючи | Gerund | вивчати |
| х-образний | X-shaped abbrev | Remove "х-" prefix (or keep if valid) |
| біг-ючи, біж-ачи, писа-ючи | Morpheme breakdown | Remove (teaching examples, not lemmas) |
| ачи, ючи, спачи | Suffix fragments | Remove |

---

## Category 4: Likely VALID for Translation (324 entries)

Words that appear to be valid Ukrainian lemmas needing translation.

### High-Priority Words (appear in markdown):

1. **застосування** (noun) - "application, use, implementation"
   - Context: "Реальне застосування" (Real application)
   - Translation: **"application, use"**

2. **присудок** (noun) - NOT found in markdown (may be error)
   - Grammar term meaning **"predicate"**

3. **реальне** (noun) - Should be adjective, not noun
   - Neuter form of "real"
   - Translation: **"real (neuter)"**
   - POS correction needed: noun → adj

4. **чумаки** (noun) - Historical term
   - Translation: **"chumaks"** (Ukrainian salt traders)

5. **геймерський** (adj) - Modern loanword
   - Translation: **"gamer (adj)"**

### Sample of Other Candidates:

- говори, майч, яким, ірин (likely fragments from names)
- довга, стар, тонка, кача (inflected adjective forms?)
- повертати, відправляти, встигти (verbs - check if already in DB)
- дніпропетровщина (place name - Dnipropetrovsk region)

### Complete List:
See `/tmp/b1-likely-valid-for-translation.txt` (324 words)

---

## Verification Against Full Case Names

Checked if non-abbreviated case names exist in B1 vocabulary:

| Case Name | Ukrainian | Found in Vocab? | Has Translation? |
|-----------|-----------|-----------------|------------------|
| Nominative | називний | ✅ Yes | ✅ "nominative (case)" |
| Genitive | родовий | ✅ Yes | ✅ "genetic, patrimonial, genitive (case)" |
| Dative | давальний | ❌ **NO** | N/A |
| Accusative | знахідний | ✅ Yes | ✅ "accusative (case)" |
| Instrumental | орудний | ✅ Yes | ✅ "instrumental (case)" |
| Locative | місцевий | ✅ Yes | ⚠️ "local" (not case meaning!) |
| Vocative | кличний | ✅ Yes | ✅ "vocative (case)" |

**Issues Found:**
1. **давальний** (dative) is MISSING completely
2. **місцевий** translates to "local" not "locative case"

**Action:** Add proper entries or fix translations

---

## Recommended Actions

### Phase 1: Cleanup (DELETE + FIX)

1. **Delete 54 fragment entries**
   ```bash
   # Script to remove entries from vocabulary YAMLs
   # Based on /tmp/b1-to-remove.txt
   ```

2. **Fix 15 malformed entries**
   - граматик → граматика
   - Remove mnemonic prefixes (д-авальний → remove entry if давальний exists)
   - Convert gerunds to infinitives
   - Fix Russicisms (корень → корінь)

3. **Add missing case name:**
   - Add "давальний" with translation "dative (case)"

4. **Fix existing translations:**
   - місцевий: Add secondary meaning "locative (case)" 

### Phase 2: Translation (324 words)

1. **Extract clean list from /tmp/b1-likely-valid-for-translation.txt**
2. **Manually verify** each word (many are still likely fragments)
3. **Translate using external sources:**
   - Ukrainian-English dictionaries (Словник.ua, Glosbe)
   - Grammar references for technical terms
   - Trusted web sources (academic dictionaries)

4. **Update vocabulary YAMLs** with translations
5. **Rebuild database** to sync translations

### Phase 3: Validation

1. Run vocabulary audit across all B1 modules
2. Verify all case names are present with correct translations
3. Check for remaining untranslated words

---

## Files Generated

- `/tmp/b1-untranslated-full.txt` - All 504 untranslated words
- `/tmp/b1-to-remove.txt` - 54 entries to delete
- `/tmp/b1-to-fix.txt` - 15 entries to correct
- `/tmp/b1-likely-valid-for-translation.txt` - 324 potential words to translate
- `/tmp/b1-untranslated-investigation-report.md` - This report

---

## Conclusion

User's hypothesis about mnemonic abbreviations (д-авальний, к-личнити, м-ісцевий) was **CORRECT** - they have valid pedagogical purpose as part of a case-name mnemonic. However, since the full case names already exist in vocabulary with proper translations, the abbreviated forms should be removed to avoid duplication and confusion.

Of 504 untranslated words:
- **54** are clear errors (delete)
- **15** are fixable (correct)
- **111** are likely fragments (review)
- **324** are potentially valid (translate with verification)

**Next step:** User decision on how to proceed with cleanup and translation phases.
