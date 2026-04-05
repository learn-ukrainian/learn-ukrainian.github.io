# Plan Review: genitive-intro

**Track:** a2 | **Sequence:** 4 | **Version:** 1.0
**Verdict:** NEEDS FIXES

## Rule Compliance
| Check | Status | Details |
|-------|--------|---------|
| word_target | PASS | Plan: 2000, Config: 2000 |
| section_budgets | PASS | Sum = 2000 (600+700+700) vs target 2000 (0%) |
| required_fields | FAIL | Missing: `persona`, `grammar`, `register` |
| version_string | PASS | version: '1.0' |

## State Standard Alignment
| Grammar Topic | In Standard? | Standard Level | Plan Level | Status |
|--------------|-------------|----------------|------------|--------|
| Genitive case (without preposition) | YES | A2 (lines 1265-1285) | A2 | PASS |
| Genitive singular endings | YES | A2 morphology (lines 1204-1221) | A2 | PASS |
| Genitive plural endings | YES | A2 morphology (lines 1204-1221) | A2 | PASS |
| Quantity words (багато, мало, кілька) | YES | A2 numerals (lines 1235-1242) | A2 | PASS |

Grammar scope is appropriate for A2. The genitive case is explicitly listed in the A2 State Standard at section 4.2.2.2 (lines 1265-1285), covering both with and without prepositions. Quantity words and numeral agreement are at A2 level per section 4.2.1.3.

## Grammar Verification (Textbook RAG)

| Concept | Textbook Source | Correct? | Notes |
|---------|----------------|----------|-------|
| Genitive singular masculine -a/-я vs -у/-ю | Заболотний Gr6 p106, Авраменко Gr10 p171 | YES | Rule correctly stated: -а/-я for concrete/animate, -у/-ю for abstract/substances. Textbooks confirm this pattern. |
| Genitive singular feminine -и/-і | Textbook corpus | YES | Standard pattern confirmed |
| Genitive singular neuter -а/-я | Textbook corpus | YES | -а for -о stems, -я for -е stems |
| Genitive plural -ів, -ей, zero ending | Litvinova Gr6 p160 | PARTIALLY | Plan says feminine: "zero ending with possible vowel insertion", and "Feminine soft stems: -ей (пісень)". The textbook shows -ей is for "деяких іменників чоловічого та середнього роду: гостей, коней, очей, плечей". The -ей ending for feminines is rare; the more common pattern is zero ending (книг, сестер). The form "пісень" is actually zero ending with vowel insertion, NOT -ей. |
| немає + Genitive | Textbook corpus (Avramenko Gr8 p77) | YES | Confirmed: negation triggers genitive |

## Vocabulary Verification
| Word | VESUM | Issues |
|------|-------|--------|
| родовий відмінок | OK | |
| немає | OK | |
| багато | OK | |
| мало | OK | |
| кілька | OK | |
| скільки | OK | |
| закінчення | OK | |
| однина | OK | |
| множина | OK | |
| кількість | OK | |
| відсутність | OK | |
| гроші | OK | |
| час | OK | |

All vocabulary verified in VESUM. No ghost words.

## Issues Found

### CRITICAL (must fix before build)
1. **Missing required fields**: Plan lacks `persona`, `grammar`, and `register` fields. These are required by the plan schema. The `grammar` field should list the grammar topics covered (e.g., `genitive_singular`, `genitive_plural`, `negation_with_nemaye`). The `persona` field should define the teaching voice. The `register` field should define the target register.

### HIGH (should fix before build)
1. **Genitive plural -ей attribution error**: Section 3 states "Feminine soft stems: -ей (пісень)". But "пісень" is actually a zero ending with fleeting vowel insertion (пісня -> пісень), NOT the -ей ending. The -ей ending applies to specific masc/neuter nouns (гостей, коней, очей). This needs correction to avoid teaching a wrong rule. The textbook (Litvinova Gr6 p160) clearly categorizes -ей separately from zero endings.
2. **Scope overload for a single 2000-word module**: Teaching BOTH genitive singular (all 3 genders) AND genitive plural (all patterns) in one module is extremely ambitious for A2. Ukrainian textbooks typically spread this across multiple lessons (Заболотний covers genitive across several sections in Gr5-6). Consider splitting: M04 = genitive singular + немає, M05 or later = genitive plural with quantities. This aligns better with the "small chunks, frequent practice" principle from Tier 1 guidelines.

### MEDIUM (fix if possible)
1. **Dialogue situation is solid but dense**: The moving-into-apartment scenario is natural and well-motivated. However, it combines singular AND plural genitives in one dialogue, which may overwhelm an A2 learner encountering genitive for the first time.
2. **Content outline point "Accusative implied, but Nom. form used"** (section 1, point 3): This parenthetical about accusative is technically debatable and may confuse learners. "У мене є брат" — "брат" is nominative as subject of the existential construction, not "Accusative implied." Better to simply contrast the two constructions without the accusative comment.

### LOW (informational)
1. **"декілька" in the content but not in vocabulary_hints**: The word "декілька" appears in objectives but isn't in the vocabulary hints. Consider adding it to recommended.

## Suggested Fixes

**Fix 1 — Add missing fields:**
```yaml
# Add after pedagogy: PPP
persona: friendly-tutor
grammar:
  - genitive_singular
  - genitive_plural
  - negation_nemaye
  - quantity_words
register: informal-educational
```

**Fix 2 — Correct genitive plural description (section 3, point 2):**
```yaml
# OLD
'Genitive Plural Endings: a tricky topic. Masculine: often -ів (столів, братів).
  Feminine/Neuter: often a zero ending with a possible vowel insertion (книг,
  сестер, вікон). Feminine soft stems: -ей (пісень).'
# NEW
'Genitive Plural Endings: a tricky topic. Masculine: often -ів (столів, братів).
  Feminine/Neuter: often a zero ending, sometimes with a fleeting vowel (книг → книжок,
  сестер, вікон). A small group of masculine/neuter nouns takes -ей (гостей, коней, очей).'
```

**Fix 3 — Remove misleading accusative comment (section 1, point 3):**
```yaml
# OLD
'Contrast: ''У мене є брат'' (Accusative implied, but Nom. form used) vs.
  ''У мене немає брата'' (Genitive).'
# NEW
'Contrast: ''У мене є брат'' (Nominative) vs. ''У мене немає брата'' (Genitive).'
```
