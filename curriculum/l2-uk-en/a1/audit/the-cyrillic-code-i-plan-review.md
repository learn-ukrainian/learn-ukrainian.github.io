# Plan Review: the-cyrillic-code-i

**Track:** A1 | **Sequence:** 1 | **Version:** 4.0
**Mode:** core (Cyrillic decodability applies)
**Verdict:** PASS

## Rule Compliance

| Check | Status | Details |
|-------|--------|---------|
| word_target | PASS | Plan: 1200, Config: 1200 |
| section_budgets | PASS | Sum = 1100 vs target 1200 (-8.3%, within +/-10%) |
| required_fields | PASS | All 16 required fields present |
| version_string | PASS | `'4.0'` (properly quoted) |

## Vocabulary Verification

All 15 words (8 required + 7 recommended) verified against VESUM:

| Word | VESUM | POS | Issues |
|------|-------|-----|--------|
| мама | OK | noun:f | -- |
| сом | OK | noun:m | -- |
| сон | OK | noun:m | -- |
| масло | OK | noun:n | -- |
| ананас | OK | noun:m | -- |
| нам | OK | pron (ми, dav) | Plan labels "pronoun" -- acceptable |
| нас | OK | pron (ми, rod/zna) | -- |
| сам | OK | adj:pron:def | Plan labels "adjective" -- VESUM confirms |
| оса | OK | noun:f | -- |
| сосна | OK | noun:f | -- |
| насос | OK | noun:m | -- |
| лама | OK | noun:m/f | -- |
| смола | OK | noun:f | -- |
| слон | OK | noun:m | -- |
| мало | OK | adv | -- |

**0 ghost words. 0 Russianisms. 0 gender errors.**

## Decodability Check (Cyrillic M1)

Available letters: А, О, У, М, Л, Н, С (7 letters)

| Word | Letters Used | Decodable? |
|------|-------------|------------|
| мама | М,А | OK |
| сом | С,О,М | OK |
| сон | С,О,Н | OK |
| масло | М,А,С,Л,О | OK |
| ананас | А,Н,С | OK |
| нам | Н,А,М | OK |
| нас | Н,А,С | OK |
| сам | С,А,М | OK |
| оса | О,С,А | OK |
| сосна | С,О,Н,А | OK |
| насос | Н,А,С,О | OK |
| лама | Л,А,М | OK |
| смола | С,М,О,Л,А | OK |
| слон | С,Л,О,Н | OK |
| мало | М,А,Л,О | OK |

**All 15 vocabulary items fully decodable from the 7-letter set.**

### Textbook Phrases Decodability

| Phrase | Source | Decodable? | Issue |
|--------|--------|------------|-------|
| У нас -- ананас. | Bolshakova p.22 | OK | All letters in set |
| У нас -- сом. | Bolshakova p.22 | OK | All letters in set |
| А у вас? | Bolshakova p.22 | **NO** | В not in 7-letter set |

## Textbook Grounding (RAG-verified)

| Claim | Verified? | Evidence |
|-------|-----------|----------|
| Letter grouping А О У М Л Н С matches Bolshakova 2018 | OK | Bolshakova pp.12-22: А (p.12), М (p.14), Н (p.20), С (p.22). All 7 letters introduced before p.22 word drill. |
| Vocabulary from Bolshakova p.22 | OK | RAG Result 1 (chunk `1-klas-bukvar-bolshakova-2018-1_s0021`): сом, оса, насос, смола, ананас, сон, сосна all on p.22. Exact match. |
| Textbook phrases from Bolshakova p.22 | OK | RAG confirms: "У нас -- ананас. У нас -- насос. У нас -- сом. А у вас?" verbatim on p.22. |
| Cyrillic created by students of Cyril & Methodius in First Bulgarian Empire | OK | Wikipedia: "розробленій в IX столiттi в Першому Болгарському царствi, в Преславськiй лiтературнiй школi." Slightly imprecise -- Cyril created Glagolitic, Cyrillic was developed by followers at Preslav. Acceptable A1 simplification. |
| Ukrainian has 10 vowels, 22 consonants | OK | Standard count: 10 vowel letters + 22 consonant letters + Ь = 33. |
| Ukrainian О never reduces in unstressed position | OK | Key contrast with Russian. Correct. |
| M2 preview: К И I Р В Т Е | OK | Verified against `the-cyrillic-code-ii.yaml` subtitle. |
| Голосні/приголосні classification | OK | RAG: Bolshakova p.24 teaches this exact classification. |

## Mode-Specific Checks (Core)

| Check | Status | Details |
|-------|--------|---------|
| Grammar scope for A1 | PASS | Letter recognition + syllable formation = correct starting point |
| Objectives testable | PASS | All 4 objectives are "can do" statements (recognize, classify, combine, read) |
| Content matches objectives | PASS | Each objective covered by at least one section |
| Logical progression | PASS | Letters -> vowels -> consonants -> syllables -> words -> summary |
| Activity hints achievable | PASS | All 5 types appropriate for letter-learning stage |

## Issues Found

### CRITICAL
None.

### HIGH
None.

### MEDIUM

1. **Section budget sum is 8.3% under word_target.** Sum = 1100 vs target 1200. Within tolerance but leaves only 100 words of slack. If Gemini writes tight prose, module may fail the word count gate. Consider adding 100 words to the Syllables section (currently 300 -> 400) since that's where the most content lives.

### LOW

1. **"А у вас?" contains untaught letter В.** This phrase is faithfully cited from Bolshakova p.22, so it's not a plan error. But the content builder should note this is a sight-read chunk, not a decodable phrase. Consider adding a note: "А у вас? -- treated as a memorized chunk; В is formally taught in M2."

2. **`prerequisites: '[]'`** is a string, not a YAML list. Should be `prerequisites: []` (bare empty list). Cosmetic -- won't break anything but is inconsistent with YAML conventions.

3. **Cyrillic origin slightly imprecise.** "Created by students of Saints Cyril and Methodius" -- Cyril created Glagolitic script. Cyrillic was developed at the Preslav Literary School by followers (likely Kliment of Ohrid). The plan's wording is an acceptable A1 simplification but could be tightened to: "developed at the Preslav Literary School in the First Bulgarian Empire, building on the work of Saints Cyril and Methodius."

## Suggested Fixes

```yaml
# 1. Increase Syllables section budget (MEDIUM)
# Old:
- section: Склади і слова — Syllables and Words
  words: 300
# New:
- section: Склади і слова — Syllables and Words
  words: 400

# 2. Fix prerequisites syntax (LOW)
# Old:
prerequisites: '[]'
# New:
prerequisites: []
```

No CRITICAL or HIGH issues. Plan is ready for build.
