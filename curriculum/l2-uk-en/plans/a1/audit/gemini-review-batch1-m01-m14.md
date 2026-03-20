# Gemini Thorough Plan Review — M01-M14 (Batch 1)

**Date:** 2026-03-20
**Reviewer:** gemini-3.1-pro-preview
**Task:** review-plans-batch1

## Findings by module

### M01 the-ukrainian-alphabet
- `книга`: Missing stress mark → `кни́га`
- `áптека`: Wrong stress → `апте́ка`
- `мéтро`: Wrong stress → `метро́`
- `зупинка`: Missing stress → `зупи́нка`

### M02 sounds-and-special-signs
- **Hallucination:** `оліпь` is not a Ukrainian word (in Діалоги section)
- **Russicism:** `тень` is Russian, should be `тінь` (shadow)
- **Russicism/Surzhyk:** `кишка` means "intestine", not "cat" — should be `кішка` (cat)
- Missing stress: `рúба`, `учúтель`, `дéв'ять`, `комп'ю́тер`, `м'якúй`

### M03 syllables-stress-intonation
- **Typo:** `ше-ко-лáд` → `шо-ко-лáд`
- **Wrong stress:** `жінкá` → `жíнка`
- **Typo:** `Якій` → `Який`
- Missing stress: `У́жгород`

### M04 greetings-and-politeness
- **Wrong stress:** `вихíдних` → `вихіднúх`
- Missing stress: `дя́кую`

### M05 who-am-i
- **Euphony violation:** `Він з Львова` → `Він зі Львова`
- **Wrong stress/form:** `Звідкí` → `Зві́дки`
- Missing stress: `украї́нець`, `украї́нка`, `Украї́на`

### M06 my-family
- Missing stress: `роди́на`, `моя́/моє́/мої́`, `дя́дько`, `двою́рідний`, `дружи́на`
- Missing stress: `ї́хній`

### M07 checkpoint-first-contact
- CLEAN (no issues)

### M08 my-room-gender
- **Vocabulary progression:** Uses `нова` (adjective) in dialogue — adjectives taught in M09
- **Systemic:** All vocabulary missing stress marks from M08 onward

### M09-M14
- **Systemic:** All vocabulary missing stress marks
- M11: `чиї` (interrogative pronoun) used but not taught in M01-M10

## Systemic issue
**Missing stress marks in vocabulary_hints for M08-M14.** The stress marks were stripped in a batch operation. Need to decide: are stress marks in plans needed, or does the pipeline add them?

## Cross-reference
This conflicts with Rule 4 (pipeline adds stress marks). But Gemini argues learners need stress guidance in the plan vocabulary. Resolution needed: either plans have stress marks in vocabulary_hints only, or we accept they're stripped and rely on the pipeline.
