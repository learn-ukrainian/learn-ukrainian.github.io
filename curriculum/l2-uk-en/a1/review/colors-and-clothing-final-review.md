Good. Confirmed: all other vocabulary files use bare lists at root. The colors-and-clothing vocabulary is the outlier with its `items:` wrapper.

---

## Phase 9 Final QA Review: colors-and-clothing (a1-27)

### Issues Found

**1. STRUCTURAL — Vocabulary YAML uses wrong format**
- **File**: `vocabulary/colors-and-clothing.yaml`, line 1
- **Text**: `items:` wrapper with 2-space-indented entries
- **Problem**: All other A1 vocabulary files (`the-living-verb-i.yaml`, `the-gender-code.yaml`, `the-locative-where-things-are.yaml`) use bare lists at root. This file uses an `items:` dictionary wrapper, which is inconsistent and may break tooling that expects bare lists.
- **Fix**: Remove `items:` wrapper, un-indent all entries to root level.

**2. LINGUISTIC — IPA error: оберіг**
- **File**: `colors-and-clothing.md`, line 261
- **Text**: `**оберіг** [ɔbeˈrʲih]`
- **Problem**: Ukrainian г is always [ɦ] (voiced glottal fricative), never [h] (voiceless). Standard Ukrainian does not have final consonant devoicing. Writing [h] teaches the wrong sound.
- **Fix**: Change to `[ɔbeˈrʲiɦ]`

**3. COMPLETENESS — Missing одягати in vocabulary YAML**
- **File**: `vocabulary/colors-and-clothing.yaml`
- **Problem**: одягати is taught explicitly in the content (section "Носити чи Одягати?", line 213) and listed in the plan's `recommended` vocabulary, but absent from the vocabulary YAML.
- **Fix**: Add entry.

**4. COMPLETENESS — Missing вишиванка in vocabulary YAML**
- **File**: `vocabulary/colors-and-clothing.yaml`
- **Problem**: вишиванка has a dedicated subsection ("Вишиванка: Одяг-Оберіг", line 260) and is a key cultural term of the module, but absent from the vocabulary YAML.
- **Fix**: Add entry.

**5. MINOR — Metalinguistic vocabulary bloat**
- **File**: `vocabulary/colors-and-clothing.yaml`, lines 95-122
- **Text**: дієслово, множина, займенник, відмінок, знахідний, рід, узгодження (7 entries)
- **Problem**: These are grammar terminology items, not "Colors & Clothing" vocabulary. They inflate the vocab count (7 of 27 items = 26% of the list). They belong in a grammar-focused module's vocabulary.
- **Severity**: Non-blocking observation. Not fixing — the audit passes and these terms do appear in the content.

**6. MINOR — Meta outline deviation: "На ньому..." construction**
- **File**: `colors-and-clothing.md`
- **Problem**: Meta outline section 5 calls for contrasting `Він має...` vs `На ньому...` for describing appearance. Content only uses `носити` for descriptions, never teaching "На ньому..." explicitly. (The construction does appear passively in unjumble activity "Сьогодні на мені сині джинси".)
- **Severity**: Non-blocking. Content is pedagogically sound without this contrast.

**7. MINOR — Meta outline deviation: "Це мені пасує" missing**
- **File**: `colors-and-clothing.md`
- **Problem**: Meta outline section 6 lists "Це мені пасує" as a key shopping phrase, but it appears nowhere in the content or dialogue.
- **Severity**: Non-blocking. The dialogue uses equivalent shopping phrases.

### Verified Clean

- **Russianisms**: CLEAN — no кушати, получати, приймати участь, слідуючий
- **Russian characters**: CLEAN — no ы, э, ё, ъ
- **Gender agreement**: All ~40 adjective-noun pairs verified correct
- **Case agreement**: All accusative forms verified correct (including the previously-reported "зелену сорочку" at line 358 — already correct in current version)
- **IPA tie bars**: All affricates (t͡ʃ, t͡s, d͡ʒ) have tie bars ✓
- **В as ʋ**: All instances use [ʋ], not [w] ✓
- **Unjumble activities**: All 12 items verified — words arrays contain exactly the words in answers ✓
- **Fill-in activities**: All 16 items verified — answers produce grammatical sentences ✓
- **Plan sections**: All 7 meta outline sections present in content ✓
- **Required vocabulary in prose**: All 9 required items used ✓
- **Objectives → self-check**: All 4 plan objectives covered by self-check questions ✓
- **Activity YAML format**: Bare list at root ✓
- **Cultural claims**: Song "Два кольори" quote accurate; color symbolism claims accurate ✓
- **LLM artifacts**: No purple prose, no invented statistics, one "це не просто" (line 17, acceptable single use) ✓
- **Word target**: Content well exceeds 2000 word minimum ✓

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/colors-and-clothing.md
---OLD---
**оберіг** [ɔbeˈrʲih]
---NEW---
**оберіг** [ɔbeˈrʲiɦ]
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/vocabulary/colors-and-clothing.yaml
---OLD---
items:
  - lemma: "білий"
    translation: "white"
    pos: "adj"
    example: "біла сорочка"
  - lemma: "чорний"
    translation: "black"
    pos: "adj"
    example: "чорна кава"
  - lemma: "червоний"
    translation: "red"
    pos: "adj"
    example: "червона сукня"
  - lemma: "синій"
    translation: "blue"
    pos: "adj"
    example: "сині джинси"
  - lemma: "зелений"
    translation: "green"
    pos: "adj"
    example: "зелена трава"
  - lemma: "жовтий"
    translation: "yellow"
    pos: "adj"
    example: "жовте сонце"
  - lemma: "сорочка"
    translation: "shirt"
    pos: "noun"
    gender: "f"
    example: "Я ношу сорочку."
  - lemma: "штани"
    translation: "pants/trousers"
    pos: "noun"
    gender: "pl"
    notes: "Plural only (pluralia tantum)"
  - lemma: "плаття"
    translation: "dress"
    pos: "noun"
    gender: "n"
  - lemma: "сукня"
    translation: "dress"
    pos: "noun"
    gender: "f"
    example: "гарна сукня"
  - lemma: "куртка"
    translation: "jacket"
    pos: "noun"
    gender: "f"
  - lemma: "светр"
    translation: "sweater"
    pos: "noun"
    gender: "m"
  - lemma: "взуття"
    translation: "footwear/shoes"
    pos: "noun"
    gender: "n"
    notes: "Collective noun"
  - lemma: "носити"
    translation: "to wear (habitually)"
    pos: "verb"
    aspect: "imp"
    usage: "Use with Accusative case."
  - lemma: "окуляри"
    translation: "glasses"
    pos: "noun"
    gender: "pl"
    notes: "Plural only"
  - lemma: "джинси"
    translation: "jeans"
    pos: "noun"
    gender: "pl"
    notes: "Plural only"
  - lemma: "колір"
    translation: "color"
    pos: "noun"
    gender: "m"
  - lemma: "розмір"
    translation: "size"
    pos: "noun"
    gender: "m"
  - lemma: "ціна"
    translation: "price"
    pos: "noun"
    gender: "f"
  - lemma: "коштувати"
    translation: "to cost"
    pos: "verb"
    aspect: "imp"
  - lemma: "улюблений"
    translation: "favorite"
    pos: "adj"
  - lemma: "гарний"
    translation: "beautiful/good"
    pos: "adj"
  - lemma: "дієслово"
    translation: "verb"
    pos: "noun"
    gender: "n"
  - lemma: "множина"
    translation: "plural"
    pos: "noun"
    gender: "f"
  - lemma: "займенник"
    translation: "pronoun"
    pos: "noun"
    gender: "m"
  - lemma: "відмінок"
    translation: "case (grammar)"
    pos: "noun"
    gender: "m"
  - lemma: "знахідний"
    translation: "accusative"
    pos: "adj"
  - lemma: "рід"
    translation: "gender"
    pos: "noun"
    gender: "m"
  - lemma: "узгодження"
    translation: "agreement"
    pos: "noun"
    gender: "n"
---NEW---
- lemma: "білий"
  translation: "white"
  pos: "adj"
  example: "біла сорочка"
- lemma: "чорний"
  translation: "black"
  pos: "adj"
  example: "чорна кава"
- lemma: "червоний"
  translation: "red"
  pos: "adj"
  example: "червона сукня"
- lemma: "синій"
  translation: "blue"
  pos: "adj"
  example: "сині джинси"
- lemma: "зелений"
  translation: "green"
  pos: "adj"
  example: "зелена трава"
- lemma: "жовтий"
  translation: "yellow"
  pos: "adj"
  example: "жовте сонце"
- lemma: "сорочка"
  translation: "shirt"
  pos: "noun"
  gender: "f"
  example: "Я ношу сорочку."
- lemma: "штани"
  translation: "pants/trousers"
  pos: "noun"
  gender: "pl"
  notes: "Plural only (pluralia tantum)"
- lemma: "плаття"
  translation: "dress"
  pos: "noun"
  gender: "n"
- lemma: "сукня"
  translation: "dress"
  pos: "noun"
  gender: "f"
  example: "гарна сукня"
- lemma: "куртка"
  translation: "jacket"
  pos: "noun"
  gender: "f"
- lemma: "светр"
  translation: "sweater"
  pos: "noun"
  gender: "m"
- lemma: "взуття"
  translation: "footwear/shoes"
  pos: "noun"
  gender: "n"
  notes: "Collective noun"
- lemma: "носити"
  translation: "to wear (habitually)"
  pos: "verb"
  aspect: "imp"
  usage: "Use with Accusative case."
- lemma: "одягати"
  translation: "to put on (clothing)"
  pos: "verb"
  aspect: "imp"
  usage: "Action of dressing, vs носити for habitual wearing."
- lemma: "вишиванка"
  translation: "embroidered shirt"
  pos: "noun"
  gender: "f"
  notes: "Traditional Ukrainian garment; considered an оберіг (talisman)"
- lemma: "окуляри"
  translation: "glasses"
  pos: "noun"
  gender: "pl"
  notes: "Plural only"
- lemma: "джинси"
  translation: "jeans"
  pos: "noun"
  gender: "pl"
  notes: "Plural only"
- lemma: "колір"
  translation: "color"
  pos: "noun"
  gender: "m"
- lemma: "розмір"
  translation: "size"
  pos: "noun"
  gender: "m"
- lemma: "ціна"
  translation: "price"
  pos: "noun"
  gender: "f"
- lemma: "коштувати"
  translation: "to cost"
  pos: "verb"
  aspect: "imp"
- lemma: "улюблений"
  translation: "favorite"
  pos: "adj"
- lemma: "гарний"
  translation: "beautiful/good"
  pos: "adj"
- lemma: "дієслово"
  translation: "verb"
  pos: "noun"
  gender: "n"
- lemma: "множина"
  translation: "plural"
  pos: "noun"
  gender: "f"
- lemma: "займенник"
  translation: "pronoun"
  pos: "noun"
  gender: "m"
- lemma: "відмінок"
  translation: "case (grammar)"
  pos: "noun"
  gender: "m"
- lemma: "знахідний"
  translation: "accusative"
  pos: "adj"
- lemma: "рід"
  translation: "gender"
  pos: "noun"
  gender: "m"
- lemma: "узгодження"
  translation: "agreement"
  pos: "noun"
  gender: "n"
===FIX_END===

===VERDICT===
APPROVE
===END_VERDICT===

**Summary**: The module is well-structured, pedagogically sound, and culturally rich. The Green Team's critical grammar error ("зелена сорочка" → "зелену сорочку") has already been fixed in the current version. My fixes address: (1) one IPA error — voiceless [h] → voiced [ɦ] for Ukrainian г in оберіг, (2) vocabulary YAML format inconsistency — `items:` wrapper converted to bare list matching all other A1 vocabulary files, and (3) two missing vocabulary entries — одягати and вишиванка added to the YAML. All activities validate correctly, all grammar is sound, no Russianisms, no LLM artifacts. After these fixes, this is a clean pass.