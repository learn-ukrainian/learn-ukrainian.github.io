# Phase 8: module-vocab-qa

Validate vocabulary YAML before locking.

> **Architecture v2.0:** Plans are immutable source of truth. Meta is mutable build config.
> - **Plan** (`plans/{level}/{slug}.yaml`): vocabulary_hints (required terms)
> - **Meta** (`{level}/meta/{slug}.yaml`): build config

## Usage

```
/module-vocab-qa {level} {module_num}
```

## Input

- `curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml`
- `curriculum/l2-uk-en/plans/{level}/{slug}.yaml` (IMMUTABLE - required vocabulary)
- `curriculum/l2-uk-en/{level}/{slug}.md` (for vocabulary source validation)

## Validation Checks

### 1. YAML Syntax and Root Structure

**Critical:** Vocabulary file must have metadata + items array.

```bash
# Parse YAML and check structure
import yaml
with open('vocabulary/{slug}.yaml') as f:
    data = yaml.safe_load(f)

if not isinstance(data, dict):
    FAIL: Root must be a dictionary with metadata fields

if 'items' not in data or not isinstance(data['items'], list):
    FAIL: Must have 'items' array
```

**Expected structure:**

```yaml
module: { slug }
level: { LEVEL }
version: '2.0'
items:
  - lemma: ...
```

**Common error:**

```yaml
# ❌ WRONG - bare list at root
- lemma: ...

# ✅ CORRECT - metadata + items array
module: trypillian-civilization
level: B2
version: '2.0'
items:
  - lemma: ...
```

### 2. Metadata Fields

Required fields at root:

- `module`: {slug} (string)
- `level`: {LEVEL} (A1|A2|B1|B2|C1|C2)
- `version`: '2.0' (string)
- `items`: array

**Check:**

```python
required_fields = ['module', 'level', 'version', 'items']
for field in required_fields:
    if field not in data:
        FAIL: Missing required field '{field}'
```

### 3. Item Schema Compliance

Each item must have 4-5 fields:

**Required for all:**

- `lemma`: string (the Ukrainian word/phrase)
- `ipa`: string (IPA pronunciation in /slashes/)
- `translation`: string (English translation)
- `pos`: string (part of speech tag)

**Required for nouns:**

- `gender`: string (m|f|n)

**Check:**

```python
for i, item in enumerate(data['items']):
    # Check required fields
    if 'lemma' not in item:
        FAIL: Item {i+1} missing 'lemma'
    if 'ipa' not in item:
        FAIL: Item {i+1} missing 'ipa'
    if 'translation' not in item:
        FAIL: Item {i+1} missing 'translation'
    if 'pos' not in item:
        FAIL: Item {i+1} missing 'pos'

    # Check gender for nouns
    if item['pos'] in ['noun', 'propn']:
        if 'gender' not in item:
            FAIL: Item {i+1} (noun) missing 'gender'
        if item['gender'] not in ['m', 'f', 'n']:
            FAIL: Item {i+1} invalid gender '{item['gender']}'

    # Check gender NOT present for non-nouns
    if item['pos'] not in ['noun', 'propn']:
        if 'gender' in item:
            FAIL: Item {i+1} ({item['pos']}) should not have 'gender' field
```

### 4. Part of Speech Validity

Valid POS tags (from Universal Dependencies):

- noun
- verb
- adj
- adv
- propn (proper noun)
- num (numeral)
- pron (pronoun)
- part (particle)

**Check:**

```python
VALID_POS = ['noun', 'verb', 'adj', 'adv', 'propn', 'num', 'pron', 'part']
for item in data['items']:
    if item['pos'] not in VALID_POS:
        FAIL: Invalid POS tag '{item['pos']}' for lemma '{item['lemma']}'
```

### 5. IPA Format Validation

IPA must be enclosed in /slashes/ with stress marked:

**Check:**

```python
import re
for item in data['items']:
    ipa = item['ipa']

    # Must start and end with /
    if not ipa.startswith('/') or not ipa.endswith('/'):
        FAIL: IPA for '{item['lemma']}' must be in /slashes/: {ipa}

    # Must contain stress marker ˈ (unless monosyllabic)
    # This is a soft check - warn if missing
    if 'ˈ' not in ipa and len(ipa) > 5:
        WARN: IPA for '{item['lemma']}' may be missing stress: {ipa}

    # Check for common Ukrainian phoneme errors
    if '/g/' in ipa or '/ɡ/' in ipa:
        WARN: Use /ɦ/ not /ɡ/ for Ukrainian г: '{item['lemma']}'
```

**Common IPA issues:**

- Missing /slashes/: `trɪˈpʲilʲɑ` → `/trɪˈpʲilʲɑ/`
- Using /g/ instead of /ɦ/: `/ɡrɑd/` → `/ɦrɑd/`
- Missing stress: `/tripillia/` → `/trɪˈpʲilʲɑ/`

### 6. Required Vocabulary Coverage

From **plan file**, check `vocabulary_hints.required`:

```yaml
# plans/{level}/{slug}.yaml
vocabulary_hints:
  required:
    - трипільська культура
    - археологія
    - енеоліт
    - поселення
    # ... etc
```

**Check:** Each required term must appear in items[].lemma or items[].translation.

```python
plan = yaml.safe_load(open(f'plans/{level}/{slug}.yaml'))
required_terms = plan.get('vocabulary_hints', {}).get('required', [])
vocab_lemmas = [item['lemma'] for item in data['items']]

for term in required_terms:
    # Check if term appears as lemma
    if term not in vocab_lemmas:
        # Check if it's a compound term split into parts
        base_term = term.split()[0]  # "трипільська культура" → "трипільська"
        if base_term not in vocab_lemmas:
            FAIL: Required term '{term}' not in vocabulary
```

**Note:** Some required terms may be phrases ("трипільська культура"). Check both full phrase and individual words.

### 7. Vocabulary Source Validation

**CRITICAL:** All vocabulary items must appear in lesson .md file.

**Check process:**

1. Extract all Ukrainian text from lesson .md
2. For each item in vocabulary:
   - Check if item['lemma'] appears in lesson
   - Exclude common grammatical words from check

```python
import re
from pathlib import Path

# Read lesson
lesson_path = f"curriculum/l2-uk-en/{level}/{slug}.md"
lesson_text = Path(lesson_path).read_text()

# Grammatical particles to exclude from check
GRAMMATICAL = {'і', 'a', 'та', 'в', 'на', 'з', 'до', 'від', 'для', 'про', 'але', 'чи', 'не'}

for item in data['items']:
    lemma = item['lemma']

    # Skip grammatical particles
    if lemma in GRAMMATICAL:
        continue

    # Check if lemma appears in lesson
    # Use word boundary to avoid false matches
    pattern = rf'\b{re.escape(lemma)}\b'
    if not re.search(pattern, lesson_text, re.IGNORECASE):
        FAIL: Lemma '{lemma}' not found in lesson
```

**Exceptions:**

- Grammatical particles: і, a, та, в, на, з, до, від, для, про
- Very common words: є, був, буде (if not lesson focus)

**This check ensures no vocabulary is added that doesn't appear in lesson.**

### 8. Item Count Validation

Check that item count meets level minimums:

| Level | Min Items | Typical Range |
| ----- | --------- | ------------- |
| A1    | 25        | 25-40         |
| A2    | 35        | 35-60         |
| B1    | 50        | 50-90         |
| B2    | 60        | 60-120        |
| C1    | 80        | 80-150        |
| C2    | 100       | 100-200       |

**For tracks (B2-HIST, C1-BIO, LIT):** 150-300 items expected

**Check:**

```python
item_count = len(data['items'])
level = data['level']

MIN_COUNTS = {
    'A1': 25,
    'A2': 35,
    'B1': 50,
    'B2': 60,
    'C1': 80,
    'C2': 100
}

if item_count < MIN_COUNTS[level]:
    FAIL: Item count {item_count} below minimum {MIN_COUNTS[level]} for {level}
```

### 9. Alphabetical Sorting

Items must be sorted by Ukrainian alphabet (not Latin):

**Ukrainian alphabet order:**

```
а б в г ґ д е є ж з и і ї й к л м н о п р с т у ф х ц ч ш щ ь ю я
```

**Check:**

```python
# Ukrainian alphabet collation
import locale
locale.setlocale(locale.LC_ALL, 'uk_UA.UTF-8')

lemmas = [item['lemma'] for item in data['items']]
sorted_lemmas = sorted(lemmas, key=locale.strxfrm)

if lemmas != sorted_lemmas:
    FAIL: Items not sorted alphabetically (Ukrainian alphabet)
    # Show first mismatch
    for i, (actual, expected) in enumerate(zip(lemmas, sorted_lemmas)):
        if actual != expected:
            print(f"Position {i+1}: expected '{expected}', got '{actual}'")
            break
```

**Note:** If `locale.setlocale` fails, use manual Ukrainian alphabet sort or warn that manual check is needed.

### 10. Translation Quality (Manual Review)

**Sample check** (10-15 random items):

- [ ] Translations accurate and contextual
- [ ] Inflected forms marked: "(genitive)", "(plural)", etc.
- [ ] Proper nouns capitalized in English
- [ ] Multiple meanings comma-separated
- [ ] No Russian/Surzhyk in translations

**Examples of good translations:**

```yaml
- lemma: археологія
  translation: archaeology

- lemma: вікентія
  translation: Vikentiy (genitive)

- lemma: будувати
  translation: to build, to construct
```

**Examples of bad translations:**

```yaml
- lemma: археологія
  translation: arkheologiya # ✗ Transliteration, not translation

- lemma: вікентія
  translation: Vikentiy # ✗ Missing case indication

- lemma: будувати
  translation: build # ✗ Missing "to" for infinitive
```

### 11. Gender Accuracy (Manual Spot Check)

**Sample check** (10-15 nouns):

- [ ] Masculine: consonant endings (край, музей, Київ)
- [ ] Feminine: -а, -я, -ість (культура, історія, радість)
- [ ] Neuter: -о, -е, -я, -ення (місто, поле, знання, століття)

**Check exceptions:**

- тато → m (not n, despite -о ending)
- кава → f
- біль → m (not f, despite soft sign)

**Common errors:**

```yaml
# ✗ WRONG
- lemma: тато
  gender: n # Should be m

# ✓ CORRECT
- lemma: тато
  gender: m
```

### 12. Duplicate Detection

Check for duplicate lemmas:

```python
lemmas = [item['lemma'] for item in data['items']]
duplicates = [lemma for lemma in set(lemmas) if lemmas.count(lemma) > 1]

if duplicates:
    FAIL: Duplicate lemmas found: {duplicates}
```

**Note:** Inflected forms are NOT duplicates:

- вікентій, вікентія, вікентієм → separate entries (not duplicates)
- археологія appearing twice → duplicate (FAIL)

### 13. Completeness Check

**Verify coverage of specialized terminology:**

1. Extract all proper nouns from lesson (names, places, events)
2. Extract all specialized terms (technical vocabulary)
3. Check each appears in vocabulary

**For history modules:**

- All historical figures (all cases if they appear in lesson)
- All place names
- All cultural/archaeological terms

**For biography modules:**

- Person's name (all cases)
- Family members
- Professions/roles
- Life events

**For literature modules:**

- Author name
- Literary terms
- Genre vocabulary
- Character names

---

## Validation Script (Optional)

```bash
# If script exists, run it:
.venv/bin/python scripts/validate_vocabulary.py curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml

# Checks:
# - YAML syntax
# - Schema compliance
# - Required vocabulary coverage
# - Source validation (all words from lesson)
# - Alphabetical sorting
```

---

## Output

### On PASS

```
VOCAB-QA: PASS

✓ YAML syntax valid
✓ Root structure: metadata + items array
✓ Metadata fields: all present
✓ Item schema: all {count} items valid
  - Nouns: {noun_count} (all have gender)
  - Verbs: {verb_count}
  - Adjectives: {adj_count}
  - Proper nouns: {propn_count}
  - Other: {other_count}
✓ POS tags: all valid
✓ IPA format: all valid ({warn_count} warnings)
✓ Required vocabulary: {req_count}/{req_total} terms present
✓ Vocabulary source: 100% from lesson
✓ Item count: {count} items (min: {level_min}, typical: {level_range})
✓ Alphabetical sorting: correct (Ukrainian alphabet)
✓ Translation quality: sample check passed
✓ Gender accuracy: spot check passed
✓ No duplicates: {count} unique lemmas
✓ Completeness: specialized terms covered

VOCABULARY LOCKED.

Next: Run /module-integrate {level} {module_num}
```

### On FAIL

```
VOCAB-QA: FAIL

Violations:
1. [CHECK_NAME]: {specific issue}
2. [CHECK_NAME]: {specific issue}
...

Fix vocabulary/{slug}.yaml and re-run /module-vocab-qa {level} {module_num}
```

---

## Common Failures and Fixes

### Failure: Root structure is bare list

**Error:**

```yaml
- lemma: археологія # ← WRONG - bare list
```

**Fix:**

```yaml
module: trypillian-civilization
level: B2
version: '2.0'
items:
  - lemma: археологія # ← CORRECT
```

### Failure: Missing gender for noun

**Error:**

```yaml
- lemma: археологія
  ipa: /ɑrxɛoˈlɔɦʲijɑ/
  translation: archaeology
  pos: noun
  # Missing gender
```

**Fix:**

```yaml
- lemma: археологія
  ipa: /ɑrxɛoˈlɔɦʲijɑ/
  translation: archaeology
  pos: noun
  gender: f # Added
```

### Failure: Gender present for non-noun

**Error:**

```yaml
- lemma: будувати
  pos: verb
  gender: m # ← WRONG - verbs don't have gender
```

**Fix:**

```yaml
- lemma: будувати
  pos: verb
  # Remove gender field
```

### Failure: IPA missing slashes

**Error:**

```yaml
- lemma: трипілля
  ipa: trɪˈpʲilʲːɑ # ← Missing /slashes/
```

**Fix:**

```yaml
- lemma: трипілля
  ipa: /trɪˈpʲilʲːɑ/ # ← Added /slashes/
```

### Failure: Required term not in vocabulary

**Error:**

```
Required term 'автохтонний' not in vocabulary
```

**Fix:** Add the missing term:

```yaml
- lemma: автохтонний
  ipa: /ɑwˈtoxtonnɪj/
  translation: autochthonous, indigenous
  pos: adj
```

### Failure: Vocabulary not from lesson

**Error:**

```
Lemma 'нововведення' not found in lesson
```

**Fix:** Either:

1. Remove the term from vocabulary (if it doesn't appear in lesson)
2. Add the term to lesson first (then regenerate vocabulary)

**CRITICAL:** Never add vocabulary that doesn't appear in lesson.

### Failure: Items not sorted alphabetically

**Error:**

```
Position 5: expected 'археологія', got 'бджіл'
```

**Fix:** Re-sort items by Ukrainian alphabet using script or manual sort.

---

## Phase Rewind

If vocabulary cannot be fixed without changing lesson content:

```
PHASE UNLOCK REQUIRED: {reason}

Cannot proceed. Need to:
1. Update lesson content to include missing required vocabulary
2. Regenerate vocabulary from updated lesson

Rewind to Phase 3 (module-lesson)
```

## Examples

### Example 1: PASS - B2-HIST Vocabulary QA

**Input:** `vocabulary/trypillian-civilization.yaml` and meta/lesson files

**Output:**

```
VOCAB-QA: PASS

✓ YAML syntax valid
✓ Root structure: metadata + items array
✓ Metadata fields: all present
✓ Item schema: all 250 items valid
  - Nouns: 120 (all have gender)
  - Verbs: 30
  - Adjectives: 40
  - Proper nouns: 50
  - Other: 10
✓ POS tags: all valid
✓ IPA format: all valid (2 warnings)
✓ Required vocabulary: 15/15 terms present
✓ Vocabulary source: 100% from lesson
✓ Item count: 250 items (min: 150 for B2-HIST, typical: 150-300)
✓ Alphabetical sorting: correct (Ukrainian alphabet)
✓ Translation quality: sample check passed
✓ Gender accuracy: spot check passed
✓ No duplicates: 250 unique lemmas
✓ Completeness: specialized terms covered

VOCABULARY LOCKED.

Next: Run /module-integrate b2-hist 1
```

### Example 2: FAIL - Missing Required Vocabulary

**Input:** Vocabulary missing required terms

**Output:**

```
VOCAB-QA: FAIL

Violations:
1. Required vocabulary: Missing coverage for term 'трипільська культура' (appears as 'трипільська' and 'культура' separately, but not full phrase)
2. Required vocabulary: Missing coverage for term 'хвойка' (appears in genitive 'хвойки' but not nominative)

Fix vocabulary/{slug}.yaml and re-run /module-vocab-qa {level} {module_num}
```

---

**On PASS:** Vocabulary is LOCKED. Do not modify. Proceed to `/module-integrate`.
