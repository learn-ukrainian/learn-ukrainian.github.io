# Plan Review: foundations-practice

**Track:** a2 | **Sequence:** 6 | **Version:** 1.0
**Verdict:** NEEDS FIXES

## Rule Compliance
| Check | Status | Details |
|-------|--------|---------|
| word_target | PASS | Plan: 2000, Config: 2000 |
| section_budgets | PASS | Sum = 2000 (600+600+800) vs target 2000 (0%) |
| required_fields | FAIL | Missing: `persona`, `grammar`, `register` |
| version_string | PASS | version: '1.0' |

## State Standard Alignment
| Grammar Topic | In Standard? | Standard Level | Plan Level | Status |
|--------------|-------------|----------------|------------|--------|
| Aspect pairs (доконаний/недоконаний) | YES | A2 verbs (lines 1341-1359, 1380-1381) | A2 | PASS |
| Genitive in real-world context | YES | A2 genitive (lines 1265-1285) | A2 | PASS |
| Future tense (imperfective compound) | YES | A2 verbs (lines 1341-1359) | A2 | PASS |
| Past tense (aspect distinction) | YES | A2 verbs (lines 1341-1359) | A2 | PASS |

All grammar topics are within A2 scope. The practice module appropriately consolidates M01-M05 topics.

## Grammar Verification (Textbook RAG)

| Concept | Textbook Source | Correct? | Notes |
|---------|----------------|----------|-------|
| Imperfective future (буду + infinitive) | Авраменко Gr7, Заболотний Gr7 | YES | "Ми будемо купувати напої" — correct compound future |
| Perfective past (completed result) | Karaman Gr10 p181, Авраменко Gr7 p54 | YES | "Я вже приготувала салат" — correct perfective past |
| Aspect contrast in past | Авраменко Gr7 p54 | YES | "Я писав листа, коли ти подзвонив" — correct impf process vs pf interruption |
| Aspect pair: купувати/купити | Textbook corpus | YES | Standard pair confirmed |
| Aspect pair: готувати/приготувати | Textbook corpus | YES | Standard pair confirmed |
| Aspect pair: планувати/запланувати | Textbook corpus | YES | Both verified in VESUM |

## Vocabulary Verification
| Word | VESUM | Issues |
|------|-------|--------|
| планувати / запланувати | OK / OK | Valid aspect pair |
| купувати / купити | OK / OK | Valid aspect pair |
| готувати / приготувати | OK / OK | Valid aspect pair |
| ринок | OK | |
| коштувати | OK | |
| кілограм | OK | |
| вечірка | OK | |
| день | OK | |
| сценарій | OK | |
| діалог | OK | |
| обговорювати | OK | |
| замовляти / замовити | OK / OK | Valid aspect pair |

All vocabulary verified. No ghost words.

## Issues Found

### CRITICAL (must fix before build)
1. **Missing required fields**: Plan lacks `persona`, `grammar`, and `register` fields.

### HIGH (should fix before build)
1. **References are weak**: Only one vague reference ("Заболотний Grade 5-6, Повторення вивченого") with no specific section numbers. A practice module consolidating aspect and genitive should reference the specific textbook sections where these are taught. Compare with M04 which cites "Заболотний Grade 6, section 81" — this module should have equally specific references for both aspect (Gr7 Заболотний/Авраменко) and genitive (Gr6 Заболотний sections 30+).

### MEDIUM (fix if possible)
1. **Activity hints don't match content**: Activity 1 is "Role-play: Planning a Trip" but the content has "Planning a Party" (Scenario 1). The activity should match the scenario topic, or the activity should be explicitly labeled as a NEW scenario.
2. **"сценарій" and "діалог" in recommended vocabulary are metalinguistic**: These are teaching terms, not communicative vocabulary. At A2, vocabulary should prioritize words learners would actually use. Consider replacing with words from the dialogues themselves (e.g., "напої" (drinks), "фрукти" (fruits), "серветки" (napkins)).
3. **Scenario 3 past tense aspect contrast is solid**: "Я писав листа, коли ти подзвонив" is a textbook-perfect example of aspect contrast. The "Що ти робив?" vs "Що ти зробив?" pair is excellent pedagogically.

### LOW (informational)
1. **TBL pedagogy is appropriate** for a practice/communication module. Good choice.
2. **Dialogue situations are natural**: Party planning and market shopping are authentic, textbook-supported scenarios. No artificial interrogation patterns.

## Suggested Fixes

**Fix 1 — Add missing fields:**
```yaml
persona: friendly-tutor
grammar:
  - aspect_in_context
  - genitive_in_practice
  - compound_future_imperfective
register: informal-conversational
```

**Fix 2 — Improve references:**
```yaml
references:
  - title: Заболотний Grade 6, §30
    notes: Закінчення іменників у родовому відмінку
  - title: Заболотний Grade 7, §25-26
    notes: Вид дієслова, видові пари
  - title: Авраменко Grade 7, §25
    notes: Вид дієслова — недоконаний і доконаний
  - title: "ULP: Verb Aspect"
    url: "https://www.ukrainianlessons.com/verb-aspect/"
    notes: "Aspect pairs and usage in context"
```

**Fix 3 — Fix activity hint mismatch:**
```yaml
# OLD
- type: quiz
  focus: 'Role-play: Planning a Trip'
# NEW
- type: quiz
  focus: 'Role-play: Planning a Party (aspect in future tense)'
```
