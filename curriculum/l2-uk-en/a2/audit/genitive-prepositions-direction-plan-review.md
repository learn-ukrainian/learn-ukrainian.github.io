# Plan Review: genitive-prepositions-direction

**Track:** A2 | **Sequence:** 10 | **Version:** 1.0
**Verdict:** NEEDS FIXES

## Rule Compliance

| Check | Status | Details |
|-------|--------|---------|
| word_target | PASS | Plan: 2000, Config: 2000 |
| section_budgets | PASS | Sum = 2000 vs target 2000 (+0%) |
| required_fields | FAIL | Missing: `persona`, `grammar`, `register` |
| version_string | PASS | `'1.0'` — string |

## State Standard Alignment

| Grammar Topic | In Standard? | Standard Level | Plan Level | Status |
|--------------|-------------|----------------|------------|--------|
| Genitive with до (direction) | YES | A2 §4.2.2.2 (lines 1265-1285) | A2 | PASS |
| Genitive with до (time limit) | YES | A2 §4.2.2.2 (lines 1265-1285) | A2 | PASS |
| Contrast до vs. в/на + Accusative | YES | A2 level (directional constructions) | A2 | PASS |

The State Standard for A2 explicitly lists "до" among genitive prepositions at §4.2.2.2. The plan dedicates an entire module to до, which is justified given its multiple meanings (direction, time, purpose).

## Grammar Verification (Textbook RAG)

| Concept | Textbook Source | Correct? | Notes |
|---------|----------------|----------|-------|
| до + genitive for direction | Karaman Grade 10 (`10-klas-ukrmova-karaman-2018_s0366`) | YES | Confirms часові конструкції with до as temporal boundary |
| до + genitive for time | Glazova Grade 11 (`11-klas-ukrajinska-mova-glazova-2019_s0118`) | YES | Temporal constructions confirmed |
| від...до time ranges | Заболотний Grade 6 (`6-klas-ukrmova-zabolotnyi-2020_s0094`) | YES | Standard temporal range construction |
| Genitive -а/-у distribution | Litvinova Grade 6 (`6-klas-ukrmova-litvinova-2023_s0165`), Glazova Grade 10 (`10-klas-ukrmova-glazova-2018_s0263`) | YES | -а for concrete, -у for abstract |

## Vocabulary Verification

| Word | VESUM | Issues |
|------|-------|--------|
| напрямок | OK (noun) | — |
| мета | OK (noun) | — |
| музей | OK (noun) | — |
| лікар | OK (noun) | — |
| бабуся | OK (noun) | — |
| вечір | OK (noun) | Gen: вечора (verified) |
| ранок | OK (noun) | Gen: ранку (verified) |
| екзамен | OK (noun) | — |
| побачення | OK (noun) | — |
| список | OK (noun) | — |
| ставлення | OK (noun) | — |
| інтерес | OK (noun) | — |
| готовий | OK (adj) | — |
| завтра | OK (adv) | — |

All 14 vocabulary items verified in VESUM. No ghost words, no Russianisms.

## Issues Found

### CRITICAL (must fix before build)

None.

### HIGH (should fix before build)

1. **Missing required fields: `persona`, `grammar`, `register`.** Same as M08/M09 — add these three fields.

2. **до vs. в/на contrast needs precision.** The plan states: "'Іду до магазину' vs. 'Іду в магазин' — до emphasizes direction toward, в/на emphasizes entering/arriving. Both are correct, but до is often preferred in standard Ukrainian." The claim that "до is often preferred" needs nuance. In spoken Ukrainian, both are equally common. The key distinction is:
   - до + genitive = direction toward (may or may not enter)
   - в/на + accusative = entering/arriving at
   
   Textbooks treat them as near-synonymous in directional contexts. The plan should not create a false hierarchy suggesting до is "better." Both are standard.

### MEDIUM (fix if possible)

1. **Section 3 "решта значень" is a grab-bag.** It covers: (a) fixed expressions (до речі, до побачення), (b) abstract nouns (додати до списку, ставлення до роботи), (c) summary table, and (d) consolidation with від/після. This is four different things in 650 words. Consider splitting: move the consolidation comparison to a brief note in the section intro rather than a full content point, freeing up words for the other three topics.

2. **"до побачення (goodbye — lit. until seeing)"** — The etymological gloss is good for A2. However, побачення as required vocabulary is glossed as "meeting, date; goodbye in 'до побачення'." This overloads one word with too many meanings. At A2, focus on the "meeting/date" meaning and note the до побачення formula separately.

3. **Activity hints lack variety for this module.** Three of four activities (quiz, fill-in, match-up) test recognition/production of до + genitive forms. The fourth (group-sort by meaning category) is the only one testing semantic discrimination. Consider replacing one of the form-focused activities with a sentence-completion activity contrasting до vs. в/на, which is the module's key pedagogical distinction.

### LOW (informational)

1. **Dialogue situation is strong.** Taxi directions are natural, motivating, and cover all three до meanings (direction: до вокзалу; time: до п'ятої години; implicit purpose in the journey narrative).

2. **Cross-module consolidation (point 4 of section 3) is excellent pedagogy.** Comparing до/від/після reinforces the A2.2 genitive preposition system as a coherent set.

## Suggested Fixes

```yaml
# Add missing required fields:
persona: tutor
grammar:
  - genitive_preposition_do_direction
  - genitive_preposition_do_time
  - genitive_preposition_do_purpose
  - contrast_do_vs_v_na
register: informal-educational

# Soften до vs. в/на claim (section 1, point 3):
# OLD:
#   Both are correct, but до is often preferred in standard Ukrainian.
# NEW:
#   Both are equally standard. До emphasizes the direction/journey;
#   в/на emphasizes the destination itself.
```
