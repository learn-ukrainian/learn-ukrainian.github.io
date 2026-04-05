# Plan Review: genitive-prepositions-purpose

**Track:** A2 | **Sequence:** 9 | **Version:** 1.0
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
| Genitive with для, без | YES | A2 §4.2.2.2 (lines 1265-1285) | A2 | PASS |
| Genitive with біля, коло | YES | A2 §4.2.2.2 (lines 1265-1285) | A2 | PASS |
| навпроти + genitive | YES | A2 level (location prepositions) | A2 | PASS |

The State Standard for A2 §4.2.2.2 explicitly lists "без, від, для, до, з/із, після, біля, коло" as genitive prepositions. навпроти is a natural extension at A2 level for location descriptions.

## Grammar Verification (Textbook RAG)

| Concept | Textbook Source | Correct? | Notes |
|---------|----------------|----------|-------|
| Prepositions as service words | Avramenko Grade 7, §75 (`7-klas-ukrmova-avramenko-2024_s0182`) | YES | Confirms біля, close to as simple preposition |
| коло as synonym for біля | Litvinova Grade 7 (`7-klas-ukrmova-litvinova-2024_s0175`) | YES | "Діти намалювали крейдою коло. Коло школи бігало кошеня." — confirms коло as preposition = біля |
| навпроти as preposition | Заболотний Grade 7 (`7-klas-ukrmova-zabolotnyi-2024_s0186`) | YES | Listed among derived prepositions |
| Hard/soft stem genitive forms | Заболотний Grade 6 (`6-klas-ukrmova-zabolotnyi-2020_s0107`) | YES | Genitive endings -а/-я, -у/-ю for masculine confirmed |

## Vocabulary Verification

| Word | VESUM | Issues |
|------|-------|--------|
| призначення | OK (noun) | — |
| відпочинок | OK (noun) | — |
| допомога | OK (noun) | — |
| сумнів | OK (noun) | — |
| будинок | OK (noun) | — |
| зупинка | OK (noun) | — |
| бібліотека | OK (noun) | — |
| лікарня | OK (noun) | — |
| площа | OK (noun) | — |
| станція | OK (noun) | — |
| навчання | OK (noun) | — |
| церква | OK (noun) | — |
| вокзал | OK (noun) | GRAC: 6.57 IPM — adequate frequency |
| річка | OK (noun) | — |

All 14 vocabulary items verified in VESUM. No ghost words, no Russianisms.

## Issues Found

### CRITICAL (must fix before build)

None.

### HIGH (should fix before build)

1. **Missing required fields: `persona`, `grammar`, `register`.** Same as M08 — add these three fields.

2. **Section 3 is disproportionately large (900 words = 45% of total).** It covers three location prepositions (біля, навпроти, коло) plus mixed-group noun practice. Meanwhile, sections 1 and 2 are only 550 words each. This imbalance risks the location section feeling dense while для/без feel thin. Consider rebalancing to 600/600/800 to give для and без more room for practice examples.

### MEDIUM (fix if possible)

1. **"для вчителя (soft masc. -ар group)"** — The plan labels вчитель as "-ар group," but вчитель ends in -тель, not -ар. It belongs to the soft masculine group with genitive -я (вчителя). The "-ар group" label is misleading — -ар nouns are a separate pattern (кухар → кухаря, столяр → столяра). Fix the label to "soft masc. -тель group" or simply "soft masc."

2. **"без олівця (soft masc.)"** — олівець is a soft-stem masculine noun, genitive олівця. This is correct. However, the е/і alternation in олівець → олівця could confuse A2 learners. Consider adding a brief note about fleeting vowels in the content outline point, or choosing a simpler soft-stem example.

3. **"коло (near, by — slightly literary)"** — The plan notes this correctly. Litvinova Grade 7 confirms коло can be replaced by біля. Good pedagogical choice to note it's less common in speech.

### LOW (informational)

1. **Dialogue situation is excellent.** Camping trip is natural, age-appropriate, and motivates all three preposition groups organically ("Для кого ця ковдра? Для Олени. Без ліхтарика — ніяк! Біля річки поставимо намет.").

2. **Activity variety is good.** Four types (fill-in, quiz, match-up, true-false) with appropriate focuses. The true-false activity checking grammatical correctness of preposition + noun form is a strong pedagogical choice.

## Suggested Fixes

```yaml
# Add missing required fields:
persona: tutor
grammar:
  - genitive_prepositions_dlia
  - genitive_prepositions_bez
  - genitive_prepositions_location_bilia_navproty_kolo
register: informal-educational

# Fix вчитель label in section 1, point 3:
# OLD:
#   для вчителя (soft masc. -ар group)
# NEW:
#   для вчителя (soft masc. -тель group)

# Consider rebalancing section word targets:
# OLD:  550 / 550 / 900
# NEW:  600 / 600 / 800
```
