# Plan Review: reading-ukrainian

**Track:** a1 | **Sequence:** 2 | **Version:** 1.3.2 | **Lifecycle:** locked
**Verdict:** PASS
**Authority:** `docs/l2-uk-en/state-standard-2024-mapping.yaml` — A1 §4.1.1 (alphabet), §4.1.4 (vowels/consonants), §4.1.5 (stress — light intro).

## Rule Compliance
| Check | Status | Details |
|-------|--------|---------|
| word_target | PASS | Plan: 1200 = Config A1: 1200 |
| section_budgets | PASS | Sum = 250+300+500+150 = 1200 (exact match) |
| required_fields | PASS | All present including `letter_module: true` flag |
| version_string | PASS | `version: 1.3.2` |
| no Latin in Cyrillic | PASS | Scan clean |

## State Standard Alignment
| Grammar Topic | In Standard? | Standard Level | Plan Level | Status |
|--------------|-------------|----------------|------------|--------|
| Syllable rule (one vowel = one syllable) | Implicit (§4.1.4) | A1 | A1 | PASS |
| Sound system [●]/[—]/[=] notation | NUS pedagogy (Захарійчук 1кл) | A1 | A1 | PASS |
| Iotated vowels Я Ю Є Ї | YES (§4.1.4) | A1 | A1 | PASS — depth appropriate |
| И vs І minimal pairs (кит/кіт) | YES (§4.1.4) | A1 | A1 | PASS — distinguishing phonemes |
| Ь / apostrophe (light intro, full coverage in M3) | YES (§4.1.3) | A1 | A1 | PASS |

## Grammar Verification (Textbook RAG)
| Concept | Textbook Source | Correct? | Notes |
|---------|----------------|----------|-------|
| «У слові стільки складів, скільки голосних звуків» | Большакова 1 кл. с.25 (cited) | YES | Canonical NUS formulation |
| Chin-test for syllable counting | Кравцова 2 кл. с.13 (cited) | YES | Standard kinesthetic technique |
| Я ZAVZHDY [йа] word-initially / after vowel / after apostrophe; softens after consonant | Standard | YES | Correctly stated |
| Ї always [йі] — never softens | Standard | YES | Correctly identified as a uniquely Ukrainian feature |
| Складоподіл ≠ перенесення (огі-рок vs о-гі-рок) | Вашуленко 2 кл. с.23-27 (cited) | YES | Important distinction included in activity_hints — well-aligned with NUS Pravopys 2019 perenosи rule |

## Vocabulary Verification (VESUM)
| Word | VESUM | Notes |
|------|-------|-------|
| яблуко | FOUND | OK — classic Я-initial word |
| молоко | FOUND | OK |
| людина | FOUND | OK — Л+Ю combination as designed |
| вулиця | FOUND | OK |
| столиця | FOUND | OK |
| каша | FOUND | OK |
| пісня | FOUND | OK — softening after consonant |
| університет | FOUND | OK |
| бібліотека | FOUND | OK — 5 syllables as labeled |
| фотографія | FOUND | OK |
| шоколад | FOUND | OK |

## Issues Found

### CRITICAL (must fix before build)
None.

### HIGH (should fix before build)
None.

### MEDIUM (fix if possible)
None.

### LOW (informational)
1. The `match-up` activity in activity_hints[5] uses **8 items** (`items: 8` from the items[] list) but the field declares `items: items: [...]` — the writer must read the list length, not the missing scalar. This pattern is YAML-valid but the schema may need a length normalization. Not a plan defect; flag for schema consistency only.
2. The plan's grammar item «Ь, апостроф (ознайомлення — детально у модулі №3)» is appropriately scoped as preview-only, deferring deep teaching to M3 — clean phase staging.

## Suggested Fixes
None required. Plan is lock-clean.

## Verdict
PASS. The plan is a model of clean phase staging: builds on M1, previews M3 (Ь/apostroph) and M4 (наголос) without overreach, and uses authentic NUS pedagogy (Большакова, Захарійчук, Вашуленко, Кравцова) with verifiable page citations. Recommend **LOCK_NOW** — no changes needed.
