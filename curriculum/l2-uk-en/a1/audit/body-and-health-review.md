# Рецензія: Body & Health

**Level:** A1 | **Module:** 31
**Overall Score:** 8.4/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: FAIL
- Sections: PASS (All sections present)
- Vocabulary: FAIL (Critical words from 'required' hints missing from YAML: голова, рука, нога, лікар, аптека, ліки, температура)
- Grammar scope: PASS (No major scope creep detected)
- Objectives: PASS (Objectives met in content)
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Good flow, clear structure, engaging warm-up. |
| 2 | Coherence | 9/10 | <7 | Logical progression from body parts to symptoms to doctor. |
| 3 | Relevance | 10/10 | <7 | Highly relevant survival topic. |
| 4 | Educational | 8/10 | <7 | Good explanations, but missed 'треба' from plan. |
| 5 | Language | 8/10 | <8 | IPA stress error on 'спина'; questionable grammar in activity. |
| 6 | Pedagogy | 9/10 | <7 | Solid PPP structure. |
| 7 | Immersion | 8/10 | <6 | Good usage, but incomplete vocabulary file reduces richness. |
| 8 | Activities | 7/10 | <7 | One grammatically incorrect item found. |
| 9 | Richness | 8/10 | <6 | Content is good, but vocabulary metadata is severely lacking. |
| 10 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5. Very encouraging. |
| 11 | LLM Fingerprint | 9/10 | <7 | Human-like tone, 'Aha! Moment' is good. |
| 12 | Linguistic Accuracy | 7/10 | <9 | Stress error and grammar error in activities. |

**Weighted Overall:** (13.5 + 9.0 + 10.0 + 9.6 + 8.8 + 10.8 + 8.0 + 9.1 + 7.2 + 11.7 + 9.0 + 10.5) / 14.0 = **8.4/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [Activity 'У лікаря', item 'Я ___ застудою.']
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Incorrect Grammar in Activity
- **Location**: Activities / type: fill-in / title: У лікаря (At the Doctor's) / item: "Я ___ застудою."
- **Original**: "Я ___ застудою." (answer: хворий)
- **Problem**: The construction "Я хворий застудою" (Instrumental) is not standard Ukrainian. Standard forms are "Я хворий на застуду" (Accusative) or simply "У мене застуда". The current prompt forces a grammatically questionable answer.
- **Fix**: Change sentence to "У мене ___. (Answer: застуда)" OR "Я ___." (Answer: хворий) and remove "застудою".

### Issue 2: Incorrect IPA Stress
- **Location**: Content / Section "Body Part + Болить/Болять" / Table Row "спина болить"
- **Original**: "/ˈspɪnɑ bɔˈlɪtʲ/"
- **Problem**: The stress is placed on the first syllable. In standard literary Ukrainian, singular 'спина' is stressed on the second syllable: /spɪˈnɑ/.
- **Fix**: Change to "/spɪˈnɑ bɔˈlɪtʲ/".

### Issue 3: Missing Vocabulary in YAML
- **Location**: Vocabulary File
- **Original**: Missing items.
- **Problem**: The vocabulary file is missing strict requirements from the Plan's 'vocabulary_hints.required' list: голова, рука, нога, лікар, аптека, ліки, температура. It also lacks basic words taught in the module like 'око/очі', 'вухо/вуха', 'зуб/зуби'.
- **Fix**: Add all missing vocabulary items with correct IPA and translation to `vocabulary.yaml`.

### Issue 4: Plan Deviation (Minor)
- **Location**: Content vs Plan
- **Original**: "Мені потрібні ліки", "Дайте... ліки"
- **Problem**: Plan specifies grammar "Impersonal necessity (треба + infinitive)". The content uses "потрібен/потрібна" (adjective) and Imperatives, but does not explicitly teach "треба".
- **Fix**: While "потрібен" is fine, adding a small note or example with "Мені треба..." (e.g., "Мені треба купити ліки") would align better with the plan and provide a simpler alternative for A1 students.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Content | /ˈspɪnɑ bɔˈlɪtʲ/ | /spɪˈnɑ bɔˈlɪtʲ/ | IPA Error |
| Activity | Я ___ застудою. | Я ___ на застуду / У мене ___ | Grammar |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? Pass
- Instructions clear? Pass
- Quick wins? Pass
- Ukrainian scary? Pass (Good support)
- Come back tomorrow? Pass

Emotional beats: 4 found
- Welcome: "Oh no! You're feeling a bit under the weather..."
- Curiosity: "Aha! Moment"
- Quick wins: "It's simpler than it looks!"
- Encouragement: "Wow! Ви вивчили основи здоров'я."

## Strengths
- **Clear Concept Explanation**: The breakdown of "У мене болить" vs "My head hurts" is excellent and very student-friendly.
- **Cultural Context**: The 'Apteka' and 'Folk Medicine' callouts add great value.
- **Dialogue Utility**: The dialogues are practical and immediately usable.

## Fix Plan to Reach 9/10 (REQUIRED)

### Language: 8/10 → 9/10

**What to fix:**
1.  **Content**: Search for ` спина болить      | /ˈspɪnɑ bɔˈlɪtʲ/` and replace IPA with `/spɪˈnɑ bɔˈlɪtʲ/`.
2.  **Content**: Consider adding a small phrase with "треба" in the Pharmacy dialogue or "Presentation 2" to satisfy the plan. E.g., add phrase: "Мені треба ліки." (I need medicine).

### Activities: 7/10 → 10/10

**What to fix:**
1.  **Activities File**: Locate `title: У лікаря` -> `sentence: Я ___ застудою.`
2.  **Action**: Change `sentence` to `У мене ___.` and `answer` to `застуда` (update options accordingly). OR change `sentence` to `Я сьогодні ___.` (I am sick today) and `answer` to `хворий`. Ideally:
    ```yaml
    - sentence: У мене ___.
      answer: застуда
      options:
      - застуда
      - хворий
      - болить
      - температура
    ```

### Richness (Vocabulary): 8/10 → 10/10

**What to fix:**
1.  **Vocabulary File**: Add the following items:
    - голова /ɦɔlɔˈʋɑ/ (head)
    - рука /rʊˈkɑ/ (hand/arm)
    - нога /nɔˈɦɑ/ (leg/foot)
    - зуб /zub/ (tooth)
    - око /ˈɔkɔ/ (eye)
    - вухо /ˈvuxɔ/ (ear)
    - лікар /ˈlʲikɑr/ (doctor)
    - аптека /ɑpˈtɛkɑ/ (pharmacy)
    - ліки /ˈlʲikɪ/ (medicine)
    - температура /tɛmpɛrɑˈturɑ/ (temperature/fever)
    - кашель /ˈkɑʃɛlʲ/ (cough)
    - нежить /ˈnɛʒɪtʲ/ (runny nose)

### Projected Overall After Fixes

(13.5 + 9.0 + 10.0 + 9.6 + 9.9 + 10.8 + 8.0 + 13.0 + 9.0 + 11.7 + 9.0 + 13.5) / 14.0 = **9.07/10**

## Verification Summary

- Content lines read: ~160
- Activity items checked: 48
- Ukrainian sentences verified: ~40
- IPA transcriptions checked: 15
- Issues found: 4
- Naturalness score recommendation: 10/10

## Verdict

**FAIL**

The module is structurally sound and pedagogically strong, but it fails on specific linguistic accuracy issues (IPA, Activity Grammar) and data completeness (Vocabulary YAML). These must be fixed to ensure the learner isn't taught incorrect stress or grammar patterns, and to ensure the vocabulary system works correctly.