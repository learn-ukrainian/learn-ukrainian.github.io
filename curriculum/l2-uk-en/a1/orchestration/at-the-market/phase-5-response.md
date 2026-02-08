# Рецензія: At the Market

**Level:** A1 | **Module:** 37
**Overall Score:** 8.4/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

Plan-Content Alignment: FAIL
- Sections: [PASS] All outlined sections present.
- Vocabulary: [FAIL] Content uses required words, but vocabulary/*.yaml file is severely broken (contains only 5 random header words, missing all 8 required terms).
- Grammar scope: [PASS] Genitive/Accusative usage aligns with A1 standards.
- Objectives: [PASS] All learning objectives addressed.

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 10/10 | <7 | Excellent cultural context (Pryvoz, tasting traditions). |
| 2 | Coherence | 10/10 | <7 | Logical flow from basics to practice to narrative. |
| 3 | Relevance | 10/10 | <7 | Highly practical skills for daily life. |
| 4 | Educational | 6/10 | <7 | **FAIL**: Vocabulary file (`vocabulary/37-at-the-market.yaml`) is missing almost all taught words. |
| 5 | Language | 10/10 | <8 | Natural, idiomatic Ukrainian. |
| 6 | Pedagogy | 10/10 | <7 | Good PPP structure; scaffolded well. |
| 7 | Immersion | 9/10 | <6 | Good balance of L1/L2; narrative is fully L2. |
| 8 | Activities | 10/10 | <7 | Excellent variety and cultural relevance in items. |
| 9 | Richness | 5/10 | <6 | **FAIL**: Vocabulary metadata is empty/incorrect, severely impacting richness score. |
| 10 | Beginner Safety | 10/10 | <7 | Encouraging tone, clear instructions ("Would I Continue? 5/5"). |
| 11 | LLM Fingerprint | 10/10 | <7 | Feels handcrafted and authentic. |
| 12 | Linguistic Accuracy | 10/10 | <9 | No grammar errors found. |

**Weighted Overall:** (15 + 10 + 10 + 7.2 + 11 + 12 + 9 + 13 + 4.5 + 13 + 10 + 15) / 14.0 = **117.7 / 14.0** = **8.41/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [CLEAN]
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Broken Vocabulary File
- **Location**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/37-at-the-market.yaml`
- **Original**: File contains only: `міра`, `привоз`, `півкілограма`, `свіжість`, `штука`.
- **Problem**:
    1. Misses ALL core words (vegetables, fruits, market, buy, cost).
    2. `привоз` is defined as "delivery" (common noun) but used in text as "Привоз" (Proper noun, Odesa market).
    3. `міра` and `свіжість` are from headers ("Вага та міри", "Якість та свіжість"), not target vocab.
- **Fix**: Replace entire YAML content with the actual vocabulary taught in the module (see Fix Plan).

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| - | - | - | Clean |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? [Pass]
- Instructions clear? [Pass]
- Quick wins? [Pass] - Dialogues are immediately usable.
- Ukrainian scary? [Pass]
- Come back tomorrow? [Pass]

Emotional beats: 5 found
- Welcome: "If you want to experience the 'soul'..."
- Curiosity: Myth-buster about markets.
- Quick wins: Table of adjectives.
- Encouragement: "Sellers are usually proud..."
- Progress: "Well done! You have mastered..."

## Strengths
- **Cultural Depth**: The inclusion of "Привоз" and the custom of tasting (`Можна спробувати?`) adds immense value beyond simple vocabulary.
- **Natural Dialogues**: The dialogues sound authentic to a Ukrainian market setting (e.g., `Ой, це трохи дорого.`).

## Fix Plan to Reach 9/10

### Educational & Richness: 6/10 → 10/10

**What to fix:**
1. **Regenerate Vocabulary YAML**: The `vocabulary/37-at-the-market.yaml` file must be populated with the actual words from the module.

**Action**: Replace `vocabulary/37-at-the-market.yaml` with the following list (enriched with IPA/Translation/Gender):
- ринок (market)
- базар (bazaar/market)
- продавець (seller)
- скільки коштує (how much does it cost)
- ціна (price)
- свіжий (fresh)
- домашній (home-grown/homemade)
- спробувати (to try/taste)
- кілограм (kilogram)
- грам (gram)
- штука (piece/item)
- літр (liter)
- помідор (tomato)
- огірок (cucumber)
- картопля (potato)
- капуста (cabbage)
- морква (carrot)
- цибуля (onion)
- яблуко (apple)
- слива (plum)
- кавун (watermelon)
- сир (cheese - cottage/homemade)
- мед (honey)
- стиглий (ripe)
- солодкий (sweet)
- кислий (sour)
- смачний (tasty)
- овочі (vegetables)
- фрукти (fruits)
- решта (change/rest)
- пакет (bag)

**Expected score after fix:** 10/10

### Projected Overall After Fixes

Recalculating with Educational=10 and Richness=10:
(15 + 10 + 10 + 12 + 11 + 12 + 9 + 13 + 9 + 13 + 10 + 15) / 14.0 = **139 / 14.0** = **9.92/10**

## Verification Summary

- Content lines read: ~130
- Activity items checked: 45
- Ukrainian sentences verified: 35
- IPA transcriptions checked: 12
- Issues found: 1 (Major Vocabulary File Failure)
- Naturalness score recommendation: 10/10

## Verdict

**FAIL**

The content is excellent (10/10), but the build artifacts are broken. The vocabulary file does not match the content, missing 90% of the taught words. This will break flashcard generation and vocabulary tracking. The module cannot pass until the vocabulary YAML is fixed to reflect the actual lesson content.