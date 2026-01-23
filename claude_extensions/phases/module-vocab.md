# Phase 7: module-vocab

Generate vocabulary YAML table from locked lesson content.

## Usage

```
/module-vocab {level} {module_num}
```

## Input

- `curriculum/l2-uk-en/{level}/{slug}.md` (LOCKED from Phase 4)
- `curriculum/l2-uk-en/{level}/meta/{slug}.yaml` (for vocabulary_hints)

## Output

- `curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml`

## Critical Rules

> [!IMPORTANT]
>
> ### Vocabulary Extraction Scope
>
> Extract ONLY content words from lesson .md file:
>
> - ✓ Nouns, verbs, adjectives, adverbs
> - ✓ All inflected forms that appear in lesson
> - ✓ Proper nouns (names, places)
> - ✓ All terms from meta.vocabulary_hints.required
> - ❌ Exclude: і, a, та, в, на, з, до, від, для, про
> - ❌ Exclude: є, був, буде (unless lesson focus)
> - ❌ Do NOT add words not in lesson
>
> ### YAML Structure
>
> **Critical:** File structure is:
>
> ```yaml
> module: { slug }
> level: { LEVEL }
> version: '2.0'
> items:
>   - lemma: { word }
>     ipa: /{pronunciation}/
>     translation: { English translation }
>     pos: { part of speech }
>     gender: { m|f|n } # for nouns only
> ```
>
> **NOT:**
>
> ```yaml
> vocabulary: # ← WRONG - no wrapper
>   items: [...]
> ```

---

## Vocabulary Generation Process

### Step 1: Load Inputs

1. Read lesson file:

   ```bash
   curriculum/l2-uk-en/{level}/{slug}.md
   ```

2. Read meta file for required vocabulary:

   ```bash
   curriculum/l2-uk-en/{level}/meta/{slug}.yaml
   ```

3. Extract `vocabulary_hints.required` list (these terms MUST be included)

### Step 2: Extract Vocabulary

Scan lesson content for all content words:

**What to extract:**

- All nouns (with gender)
- All verbs (all aspects and forms that appear)
- All adjectives (including comparative/superlative if present)
- All adverbs
- All proper nouns (historical figures, places, events)
- All specialized terminology

**What to exclude:**

- Grammatical particles: і, a, та, але, чи, не
- Prepositions: в, на, з, до, від, для, про, під, над, між, через, без
- Common verbs (unless lesson focus): є, був, буде, мати, бути
- Question words (unless lesson focus): хто, що, де, коли, чому, як, який, скільки

**Inflected forms:**

Include ALL inflected forms that appear in the lesson:

Example from lesson:

```
Вікентій Хвойка... розкопки Вікентія Хвойки... за Вікентієм Хвойкою
```

Generate entries:

```yaml
- lemma: вікентій
  ipa: /wʲikɛnˈtʲij/
  translation: Vikentiy (name)
  pos: propn
  gender: m

- lemma: вікентія
  ipa: /wʲikɛnˈtʲijɑ/
  translation: Vikentiy (genitive)
  pos: propn
  gender: m

- lemma: вікентієм
  ipa: /wʲikɛnˈtʲijɛm/
  translation: Vikentiy (instrumental)
  pos: propn
  gender: m
```

### Step 3: Generate IPA Pronunciations

For each lemma, generate IPA transcription:

**Ukrainian IPA rules:**

- Use scholarly IPA (not simplified)
- Mark stress with ˈ before stressed syllable
- Common patterns:
  - а → /ɑ/
  - е → /ɛ/
  - и → /ɪ/
  - і → /i/
  - о → /ɔ/
  - у → /u/
  - г → /ɦ/ (not /ɡ/)
  - в → /w/ or /ʋ/ depending on position
  - ь → /ʲ/ (palatalization)

**Examples:**

```yaml
- lemma: трипільська культура
  ipa: /trɪˈpʲilʲsʲkɑ kulʲˈturɑ/

- lemma: археологія
  ipa: /ɑrxɛoˈlɔɦʲijɑ/

- lemma: енеоліт
  ipa: /ɛnɛoˈlʲit/
```

**For complex pronunciations:** Use Ukrainian IPA reference or consult linguistic resources.

### Step 4: Classify Part of Speech

Use standard linguistic tags:

| Tag   | Meaning     | Example                |
| ----- | ----------- | ---------------------- |
| noun  | Noun        | археологія, поселення  |
| verb  | Verb        | будувати, створювати   |
| adj   | Adjective   | трипільський, великий  |
| adv   | Adverb      | швидко, добре          |
| propn | Proper noun | Київ, Хвойка, Трипілля |
| num   | Numeral     | один, перший, багато   |
| pron  | Pronoun     | він, вона, який        |
| part  | Particle    | так, ні, ж, бо         |

### Step 5: Determine Gender (Nouns Only)

For nouns and proper nouns, specify gender:

| Gender | Typical endings             | Examples                      |
| ------ | --------------------------- | ----------------------------- |
| m      | -consonant, -ій, -о (names) | музей, край, Тарас            |
| f      | -а, -я, -ість               | культура, історія, радість    |
| n      | -о, -е, -я, -ення           | місто, поле, знання, століття |

**Do not include gender for non-nouns.**

### Step 6: Generate English Translations

Provide accurate, contextual translations:

**For common words:**

```yaml
- lemma: будувати
  translation: to build, to construct
```

**For specialized terms:**

```yaml
- lemma: енеоліт
  translation: Eneolithic, Chalcolithic period
```

**For proper nouns:**

```yaml
- lemma: трипілля
  translation: Trypillia (village)
```

**For inflected forms:**

```yaml
- lemma: вікентія
  translation: Vikentiy (genitive)
```

### Step 7: Sort and De-duplicate

**Sorting:**

- Sort alphabetically by Ukrainian alphabet order (not Latin)
- Ukrainian alphabet: а б в г ґ д е є ж з и і ї й к л м н о п р с т у ф х ц ч ш щ ь ю я

**De-duplication:**

- If same lemma appears multiple times, keep one entry
- Inflected forms are separate entries (not duplicates)

---

## Quality Standards

### Completeness

**Required vocabulary coverage:**

- 100% of meta.vocabulary_hints.required terms
- All specialized terminology from lesson
- All proper nouns (people, places, events)
- Common verbs and adjectives used in lesson context

**Target counts by level:**

| Level | Min Items | Typical Range |
| ----- | --------- | ------------- |
| A1    | 25        | 25-40         |
| A2    | 35        | 35-60         |
| B1    | 50        | 50-90         |
| B2    | 60        | 60-120        |
| C1    | 80        | 80-150        |
| C2    | 100       | 100-200       |

**For history/biography/literature tracks:** Higher counts (150-300 items) due to specialized terminology.

### Accuracy

**IPA transcriptions:**

- Must be linguistically accurate
- Use scholarly IPA notation
- Mark stress correctly
- Distinguish Ukrainian phonemes (г=/ɦ/, not /ɡ/)

**Translations:**

- Contextually appropriate
- Include register notes if needed (formal, archaic, etc.)
- For inflected forms, indicate case/number

**Part of speech:**

- Use correct linguistic tags
- Match actual usage in lesson

**Gender:**

- Accurate for all nouns
- Check exceptions (тато=m, кава=f, etc.)

### Consistency

**Lemma format:**

- All lowercase (except proper nouns)
- No punctuation (unless part of term)
- Phrases separated by space (not hyphen)

**IPA format:**

- Enclosed in /slashes/
- Stress marked before syllable: /trɪˈpʲilʲɑ/
- Use ʲ for soft sign, not '

**Translation format:**

- English lowercase (except proper nouns)
- Comma-separated for multiple meanings
- Parenthetical notes for inflections: "(genitive)"

---

## Level-Specific Guidelines

### A1-A2 Modules

**Focus:**

- Basic vocabulary (everyday objects, actions)
- High-frequency words
- Simple pronunciation
- Clear, simple translations

**Typical items:**

- Cognates (кафе, парк, студент)
- Basic verbs (бути, мати, робити)
- Common nouns (мама, тато, дім)

### B1+ Modules

**Focus:**

- Abstract concepts
- Specialized terminology
- Complex derivations
- Nuanced translations

**Typical items:**

- Academic terms (дослідження, аналіз)
- Historical/cultural terms (епоха, культура)
- Complex verbs with prefixes (перевершувати, спростовувати)

### B2-HIST / C1-BIO / C1-HIST / LIT Tracks

**Focus:**

- Extensive specialized terminology
- Historical names and places (all inflected forms)
- Academic register vocabulary
- Decolonization terminology

**Typical items:**

- Proper nouns: Вікентій, Вікентія, Вікентієм (all cases)
- Historical terms: археологія, енеоліт, протомісто
- Academic verbs: аргументувати, спростовувати, приписувати
- Decolonization terms: автохтонний, колоніальний, упередження

**Expected counts:** 150-300 items for comprehensive coverage

---

## Output Format

```yaml
module: { slug }
level: { LEVEL }
version: '2.0'
items:
  - lemma: { term1 }
    ipa: /{ipa1}/
    translation: { translation1 }
    pos: { pos1 }
    gender: { gender1 }

  - lemma: { term2 }
    ipa: /{ipa2}/
    translation: { translation2 }
    pos: { pos2 }
    gender: { gender2 }

# ... continue for all extracted terms
```

**CRITICAL:**

- Root structure: 3 metadata fields + items array
- Items is array of objects (NOT bare list)
- Each item has 4-5 fields (gender only for nouns)
- Alphabetically sorted by Ukrainian alphabet

---

## Validation Checklist

Before outputting, verify:

- [ ] All meta.vocabulary_hints.required terms present
- [ ] All specialized terminology from lesson included
- [ ] All proper nouns and inflected forms present
- [ ] No vocabulary added that doesn't appear in lesson
- [ ] IPA transcriptions linguistically accurate
- [ ] All nouns have gender specified
- [ ] Non-nouns do NOT have gender field
- [ ] Translations accurate and contextual
- [ ] Items sorted alphabetically (Ukrainian alphabet)
- [ ] No duplicates (inflected forms are separate, not duplicates)
- [ ] Item count meets level minimums
- [ ] YAML syntax valid (test with yq or python yaml)

---

## Common Patterns by Module Type

### Grammar Modules (A1-B1)

**Focus:** Grammar terminology in Ukrainian

Example (aspect module):

```yaml
- lemma: доконаний вид
  ipa: /doˈkonɑnɪj wɪd/
  translation: perfective aspect
  pos: noun
  gender: m

- lemma: недоконаний вид
  ipa: /nɛdoˈkonɑnɪj wɪd/
  translation: imperfective aspect
  pos: noun
  gender: m
```

### History Modules (B2-HIST, C1-HIST)

**Focus:** Historical events, figures, places, all inflected forms

Example:

```yaml
- lemma: хвойка
  ipa: /ˈxwojkɑ/
  translation: Khvoika (archaeologist)
  pos: propn
  gender: m

- lemma: хвойки
  ipa: /ˈxwojkɪ/
  translation: Khvoika (genitive)
  pos: propn
  gender: m
```

### Biography Modules (C1-BIO)

**Focus:** Person's life, attributes, achievements, family members

Example:

```yaml
- lemma: поет
  ipa: /poˈɛt/
  translation: poet
  pos: noun
  gender: m

- lemma: поетеса
  ipa: /poɛˈtɛsɑ/
  translation: poetess
  pos: noun
  gender: f
```

### Literature Modules (LIT)

**Focus:** Literary terms, genres, styles, authors

Example:

```yaml
- lemma: роман
  ipa: /roˈmɑn/
  translation: novel
  pos: noun
  gender: m

- lemma: реалізм
  ipa: /rɛɑˈlʲizm/
  translation: realism
  pos: noun
  gender: m
```

---

## Next Phase

On completion, output:

```
VOCABULARY GENERATED: curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml

Vocabulary statistics:
- Total items: {count}
- Required terms: {required_count}/{total_required} (from meta)
- Nouns: {noun_count}
- Verbs: {verb_count}
- Adjectives: {adj_count}
- Proper nouns: {propn_count}
- Other: {other_count}

✓ All required vocabulary present
✓ All specialized terms from lesson included
✓ IPA transcriptions complete
✓ Alphabetically sorted
✓ YAML syntax valid

Next: Run /module-vocab-qa {level} {module_num}
```

## Examples

### Example 1: B2-HIST Vocabulary Generation

**Input:** Lesson content with historical terms

**Output:** `vocabulary/trypillian-civilization.yaml`

```yaml
module: trypillian-civilization
level: B2
version: '2.0'
items:
  - lemma: археологія
    ipa: /ɑrxɛoˈlɔɦʲijɑ/
    translation: archaeology
    pos: noun
    gender: f
  - lemma: енеоліт
    ipa: /ɛnɛoˈlʲit/
    translation: Eneolithic, Chalcolithic period
    pos: noun
    gender: m
  - lemma: протомісто
    ipa: /proˈtɔmʲisto/
    translation: protocity
    pos: noun
    gender: n
  - lemma: хвойка
    ipa: /ˈxwojkɑ/
    translation: Khvoika (archaeologist)
    pos: propn
    gender: m
  - lemma: трипільська культура
    ipa: /trɪˈpʲilʲsʲkɑ kulʲˈturɑ/
    translation: Trypillian culture
    pos: noun
    gender: f
  - lemma: чорнозем
    ipa: /t͡ʃornoˈzɛm/
    translation: chernozem, black soil
    pos: noun
    gender: m
# ... 200+ more items
```

---

**Phase output is UNLOCKED until Phase 8 QA passes.**
