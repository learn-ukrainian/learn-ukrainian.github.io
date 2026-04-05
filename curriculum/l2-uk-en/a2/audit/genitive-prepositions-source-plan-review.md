# Plan Review: genitive-prepositions-source

**Track:** A2 | **Sequence:** 8 | **Version:** 1.0
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
| Genitive with prepositions (з/із, від, після) | YES | A2 §4.2.2.2 (lines 1265-1285) | A2 | PASS |
| Euphony з/із/зі | YES | A1 §4.1.7 (lines 590-594) + A2 §4.1.3 (lines 1190-1195) | A2 | PASS |

The State Standard for A2 explicitly lists genitive "з прийменниками (без, від, для, до, з/із, після, біля, коло)" at §4.2.2.2. The plan's scope (з/від/після) is a well-chosen subset.

## Grammar Verification (Textbook RAG)

| Concept | Textbook Source | Correct? | Notes |
|---------|----------------|----------|-------|
| з/із/зі variants | Заболотний Grade 5, §30 (`5-klas-ukrmova-zabolotnyi-2023_s0125`) | PARTIALLY | See HIGH issue #1 below |
| з + genitive for origin | Заболотний Grade 7 (`7-klas-ukrmova-zabolotnyi-2024_s0187`) | YES | Standard usage confirmed |
| від + genitive from person | Glazova Grade 11 (`11-klas-ukrajinska-mova-glazova-2019_s0109`) | YES | Confirmed |
| після + genitive | Avramenko Grade 11 (`11-klas-ukrajinska-mova-avramenko-2019_s0095`) | YES | Standard usage |

## Vocabulary Verification

| Word | VESUM | Issues |
|------|-------|--------|
| прийменник | OK (noun) | — |
| джерело | OK (noun) | — |
| походження | OK (noun) | — |
| матеріал | OK (noun) | — |
| далеко | OK (adv) | — |
| недалеко | OK (adv) | — |
| подарунок | OK (noun) | — |
| сніданок | OK (noun) | — |
| вечеря | OK (noun) | — |
| канікули | OK (noun) | — |
| дитинство | OK (noun) | — |
| шовк | OK (noun) | — |
| парасолька | OK (noun) | — |
| сусід | OK (noun) | — |

All 14 vocabulary items verified in VESUM. No ghost words, no Russianisms.

## Issues Found

### CRITICAL (must fix before build)

None.

### HIGH (should fix before build)

1. **Missing required fields: `persona`, `grammar`, `register`.** The plan review spec requires these fields. Add `grammar:` listing the grammar points covered (e.g., `genitive_prepositions_source`, `euphony_z_iz_zi`), `persona:` (e.g., `tutor`), and `register:` (e.g., `informal-educational`).

2. **Imprecise з/із/зі rule.** The plan states: "із before consonant clusters (із Закарпаття)." According to Заболотний Grade 5 §30, із is used: (1) before single sounds [з], [с], [ц], [ж], [ч], [ш]; (2) between consonants. The rule for зі is: before clusters where the first consonant is [з], [с], [ш], and some others. The plan's shorthand "із before consonant clusters" oversimplifies — із Закарпаття works because it's between consonants, not because Закарпаття starts with a cluster. The build may produce imprecise teaching of this rule.

### MEDIUM (fix if possible)

1. **"зі before зл-, зм-, зн-, сп-, ст-, шт- clusters" is too narrow.** Заболотний says зі is used before clusters where the first consonant is [з], [с], [ц], [ш] "and some others" (з урахуванням милозвучності). The plan's explicit list (зл-, зм-, зн-, сп-, ст-, шт-) is a reasonable teaching simplification for A2 but misses [ц]-initial clusters and the general euphony principle. Consider adding a note that this is a simplification.

2. **Section 2 "від for protection"** — "ліки від головного болю" and "парасолька від дощу" are common expressions. However, the "protection from" meaning stretches the core "from" meaning of від. At A2, it's fine to introduce it, but the plan should acknowledge this is a secondary/metaphorical extension, not the core meaning of від + genitive.

### LOW (informational)

1. **"склянка з молока"** — This phrase means "a glass of milk" (made from milk), but a more common collocation is "склянка молока" (genitive without preposition). The з here emphasizes the material/source, which is correct for teaching the preposition, but the writer should ensure the content clarifies the difference between "склянка молока" (glass of milk) vs. "склянка з молока" (glass made from milk / glass containing milk).

2. **Dialogue situation is solid.** International potluck is natural and motivating. No artificial interrogation. The progression from з Франції → від бабусі → після подорожі covers all three prepositions organically.

## Suggested Fixes

```yaml
# Add missing required fields after `phase:` line:
persona: tutor
grammar:
  - genitive_prepositions_z_iz_zi
  - genitive_prepositions_vid
  - genitive_prepositions_pislia
  - euphony_z_iz_zi
register: informal-educational

# Fix із rule description (section 1, point 2):
# OLD:
#   із before consonant clusters (із Закарпаття)
# NEW:
#   із before single sibilants [з], [с], [ц], [ж], [ч], [ш] (із золота, із села,
#   із Харкова) and between two consonants (лист із Бразилії)
```
