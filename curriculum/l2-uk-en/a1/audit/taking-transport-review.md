# Рецензія: Taking Transport

**Level:** A1 | **Module:** 40
**Overall Score:** 9.2/10
**Status:** PASS
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [PASS] "Warm-up 2" in Plan corresponds to "Narrative" in Content.
- Vocabulary: [PASS] Required words used. Extra words in YAML: арсенальний, бюст, Почайна, Оболонь (proper names/unused).
- Grammar scope: [PASS] Mostly clean, minor A2 previews (Genitive Plural, Reflexive Imperative).
- Objectives: [PASS] All covered.
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 10/10 | <7 | Strong narrative, useful dialogues, myth-buster adds value. |
| 2 | Coherence | 9/10 | <7 | Logical flow, but unused vocabulary items in YAML (`бюст`) create minor mismatch. |
| 3 | Relevance | 10/10 | <7 | Essential survival topic for Ukraine. |
| 4 | Educational | 9/10 | <7 | Clear explanations, though one activity item tests untaught vocab (`перехід`). |
| 5 | Language | 9/10 | <8 | Natural phrasing. `Заторів немає` (Gen Pl) and `Пристібніться` are slightly advanced but idiomatic. |
| 6 | Pedagogy | 9/10 | <7 | Good PPP structure. |
| 7 | Immersion | 10/10 | <6 | High immersion with real station names (Obolon, Pochaina, Arsenalna). |
| 8 | Activities | 8/10 | <7 | Activity 2 Item 5 requires `перехід` (untaught), while text taught `пересадка`. |
| 9 | Richness | 10/10 | <6 | Excellent inclusion of cultural context (Marshrutka etiquette, Deepest station). |
| 10 | Beginner Safety | 10/10 | <7 | Encouraging tone, clear practical tips. |
| 11 | LLM Fingerprint | 10/10 | <7 | No "AI-voice" detected. |
| 12 | Linguistic Accuracy | 10/10 | <9 | No grammatical errors found. |

**Weighted Overall:** 9.2/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN] Minor idiomatic previews acceptable at end of A1.
- Activity errors: [Activity 2, Item 5] tests untaught word `перехід`.
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Activity Vocabulary Gap
- **Location**: Activity 2 ("In the Metro"), Item 5
- **Original**: Question `Де _____ на червону лінію?` requires answer `перехід`.
- **Problem**: The word `перехід` (noun) is NOT in the module vocabulary or text. The text uses `пересадка` (transfer). The student has not learned `перехід`.
- **Fix**: Change the expected answer to `пересадка` and ensure it is an option, OR update the options list if `пересадка` was intended. (Currently `пересадка` is not an option for this specific item).

### Issue 2: Unused Vocabulary Artifacts
- **Location**: `vocabulary.yaml`
- **Original**: `lemma: бюст`
- **Problem**: The word `бюст` is in the vocabulary list but does not appear in the text (text uses `статуї`).
- **Fix**: Remove `бюст` from vocabulary.yaml.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| - | - | - | - |

(No strictly incorrect language found; usage is natural).

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? [No]
- Instructions clear? [Yes]
- Quick wins? [Yes] (Metro signs, simple rules)
- Ukrainian scary? [No]
- Come back tomorrow? [Yes]

Emotional beats: 4 found
- Welcome: "Let's get moving!"
- Curiosity: Myth-buster about Kyiv Metro.
- Quick wins: "It relies on honesty and works perfectly!" (Marshrutka tip).
- Encouragement: "Most young people speak English... Good luck!"

## Strengths
- **Cultural Authenticity**: The explanation of the marshrutka payment chain ("Передайте за проїзд") is culturally accurate and essential for real life.
- **Narrative**: Ihor's commute feels grounded in Kyiv geography (Obolon -> Maidan -> Uni).
- **Phonetics**: IPA transcription is provided and accurate.

## Fix Plan to Reach 9/10

### Activities: 8/10 → 10/10

**What to fix:**
1. File `activities/40-taking-transport.yaml`: In `type: fill-in` (Title: "In the Metro"), Item 5:
   - Change `answer: перехід` → `answer: пересадка`
   - Change `options: [перехід, вихід, вхід, поїзд]` → `options: [пересадку, вихід, вхід, поїзд]` (Note: match the case required by sentence `Де _____`? Actually `Де пересадка` (Nom) vs `зробити пересадку` (Acc). The sentence is `Де _____ на червону лінію?`. Nominative `пересадка` fits. Activity item 4 used `пересадку` (Acc). Ensure the option fits the grammar. If the option is just the Lemma `пересадка`, it fits. If it's `пересадку`, it doesn't fit `Де...`.
   - **Better Fix**: The text uses `Де пересадка...?`. The activity should likely expect `пересадка`.
   - Update `options` to include `пересадка` instead of `перехід`.

### Coherence: 9/10 → 10/10

**What to fix:**
1. File `vocabulary/40-taking-transport.yaml`: Remove `lemma: бюст`.
2. File `vocabulary/40-taking-transport.yaml`: Remove `lemma: арсенальний` (Adjective not used, proper name `Арсенальна` is in text).

### Projected Overall After Fixes

**9.5/10**

## Verification Summary

- Content lines read: ~120
- Activity items checked: 47
- Ukrainian sentences verified: ~45
- IPA transcriptions checked: 22
- Issues found: 2 (1 Activity, 1 Vocab)
- Naturalness score recommendation: 10/10

## Verdict

**PASS**

The module is excellent, authentic, and engaging. It passes the review threshold. The identified issues are minor cleanup (unused vocabulary) and one unfair activity item, which can be easily patched.