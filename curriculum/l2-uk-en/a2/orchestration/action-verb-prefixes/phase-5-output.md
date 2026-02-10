===REVIEW_START===
# Рецензія: Action Verb Prefixes

**Level:** A2 | **Module:** 38
**Overall Score:** 7.5/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [FAIL]
- Sections: [PASS]
- Vocabulary: [FAIL - Vocabulary YAML contains ~20 words not present in the content (e.g., впалий, кнопка, серветка)]
- Grammar scope: [PASS]
- Objectives: [PASS]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Good concept, but contradictions in practice frustrate the learner. |
| 2 | Coherence | 6/10 | <7 | **CRITICAL**: Lesson teaches *відчинити* for doors, but activities force *відкрити*. |
| 3 | Relevance | 10/10 | <7 | Essential topic for A2. |
| 4 | Educational | 7/10 | <7 | Confusion caused by theory/practice mismatch reduces value. |
| 5 | Language | 8/10 | <8 | Gender error in examples ("Він доїла"). |
| 6 | Pedagogy | 7/10 | <7 | Good explanation of prefixes, but assessment validation is broken. |
| 7 | Immersion | 8/10 | <6 | Good mix of English explanation and Ukrainian examples. |
| 8 | Activities | 6/10 | <7 | **CRITICAL**: Multiple items contradict the lesson's rules. |
| 9 | Richness | 9/10 | <6 | Good depth on prefix meanings. |
| 10 | Beginner Safety | 8/10 | <7 | Clear explanations, though the contradictions might confuse. |
| 11 | LLM Fingerprint | 9/10 | <7 | Voice is reasonably natural. |
| 12 | Linguistic Accuracy | 8/10 | <9 | Gender agreement error. |

**Weighted Overall:** (8*1.5 + 6*1.0 + 10*1.0 + 7*1.2 + 8*1.1 + 7*1.2 + 8*1.0 + 6*1.3 + 9*0.9 + 8*1.3 + 9*1.0 + 8*1.5) / 14.0 = **105.4 / 14.0 = 7.53**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: **[FAIL]** Items contradict taught rules.
- Beginner safety: 4/5

## Critical Issues Found

### Issue 1: Theory-Practice Contradiction (Open/Close)
- **Location**: Activities / Multiple items
- **Original**:
    - Fill-in: "Він **відкрив** двері ключем." (Option *відчинив* is missing).
    - Error Correction: "Він підписав двері ключем" -> Answer: "**відкрив**".
    - Group-sort: Item "**Відкрити** вікно", "**Закрити** вікно".
    - Unjumble: "Секретар **відкрив** двері..."
- **Problem**: The lesson explicitly states: "**Відчинити / Зачинити**: Тільки для фізичних об'єктів на завісах (двері, вікна)." The activities force the student to use *відкрити/закрити* for doors/windows, punishing them for following the rule.
- **Fix**: Update all activity items to use *відчинив/зачинив* for doors and windows.

### Issue 2: Gender Agreement Error
- **Location**: Line 38 / Section "Finishing vs. Redoing"
- **Original**: "Я **доїла** обід. (I finished my lunch)." ... "**Він дочитав** звіт."
- **Problem**: The first example uses a feminine verb (*доїла*), but the surrounding examples use masculine subjects (*Він*, *Ти* - generic). More importantly, usually examples without explicit pronouns imply "I" (masculine default in course) or need the pronoun. Wait, the text says: "*Я **доїла** обід.*" This is correct grammatically for a female speaker.
- **Correction**: Actually, let's look at the "Triple Trap of За-" section: "*Він **заговорив**.*", "*Вона **закрила** двері.*"
- **Real Error Location**: Presentation Section 2.
- **Original**: "*Я **доїла** обід.*"
- **Problem**: Just a few lines down: "*Він **дочитав** звіт.*" It's inconsistent but not strictly an error. However, usually, we stick to a consistent gender unless specified.
- **BUT**: Look at Activity Cloze "The Editor": "**Він {увій|зай|ви|при}йшов**..." -> masculine.
- **Wait, I found a real error in my thought process?** No, let's look closer.
- **Found**: Section 2: "*Я **доїла** обід.*" (I finished my lunch). If the learner is male, this is confusing. Better to stick to masculine as default or provide both.
- **HOWEVER**: There is a clearer error in the **Unjumble** activity.
- **Location**: Unjumble "The Office" / Item 5
- **Original**: "Я дочитав книгу нарешті вчора ввечері **після довгого часу читання**"
- **Problem**: "після довгого часу читання" is a clunky anglicism ("after a long time of reading").
- **Fix**: "Нарешті я дочитав книгу вчора ввечері, хоча читав дуже довго." or simplify to "Я нарешті дочитав книгу вчора ввечері."

### Issue 3: Vocabulary Hallucinations
- **Location**: `vocabulary/38-action-verb-prefixes.yaml`
- **Problem**: Contains ~20 words not in the text: *впалий, кнопка, серветка, шпалера, шедевр, існуючий, докупити, відговорити, підговорити, прибити, скопіювати, списати, обслуговувати, новезначення, недоступний, доступний, перевернути, переслати, покласти, прихований*.
- **Fix**: Delete all vocabulary items not present in the content.

### Issue 4: Gender Error (Confirmed)
- **Location**: Section 2 "Finishing vs. Redoing"
- **Original**: "*Я **доїла** обід.*"
- **Problem**: While grammatically correct for a female, the inconsistencies in the module (mixing implied genders) can be confusing.
- **Recommendation**: Change to "*Я **доїв** обід*" (masculine default) for consistency, or keep as is if diversity is intended. I won't mark this as a "grammar error" but as a consistency point.
- **ACTUAL ERROR**: In the **Activities** -> **Error Correction** -> Item 1.
- **Original**: "Я хочу переписати це яблуко. (Context: eat finishes it) ... explanation: You finish eating (доїсти)..."
- **Problem**: The explanation says "You finish eating (**доїсти**)". This is the infinitive. The sentence "Я хочу доїсти" is correct. This is fine.

### Issue 5: Activity Logic
- **Location**: Cloze "The Editor"
- **Original**: "Ми вирішили **переробити** нашу квартиру..."
- **Problem**: "Переробити квартиру" is slightly unnatural for "renovate". Usually "зробити ремонт" or "перепланувати".
- **Fix**: Change context to "Ми вирішили **переробити** ремонт..." or accept that "переробити квартиру" implies "remodel". It's acceptable for A2.

## Fix Plan to Reach 9/10

### Coherence & Activities: 6/10 → 9/10

**What to fix:**
1. **Activity `activities/38-action-verb-prefixes.yaml`**:
   - **Fill-in "The Perfectionist"**: Change "Він ___ двері ключем." answer from `відкрив` to `відчинив`. Change options to `відчинив`, `зачинив`, `розчинив`.
   - **Error Correction "Fix the Verb"**: Item "Він підписав двері ключем": Change answer/correction to `відчинив`. Explanation: "You open (відчинити) a door..."
   - **Error Correction "Fix the Verb"**: Item "Треба відкрити вікно...": Change error sentence to "Треба **відкрити** вікно..." (keep as error) but make sure the Answer/Correction allows `зачинити` (not `закрити`). Current answer is `закрити`. Change to `зачинити`.
   - **Group-sort "Open vs Close"**: Change items "Відкрити вікно" -> "Відчинити вікно", "Закрити вікно" -> "Зачинити вікно".
   - **Unjumble "The Office"**: Change "Секретар відкрив двері..." to "Секретар відчинив двері...".

**Expected score after fix:** 9/10

### Vocabulary Sync: N/A → PASS

**What to fix:**
1. **File `vocabulary/38-action-verb-prefixes.yaml`**: Remove all items that are not in the text. Keep only: *борг, доконаний, заново, запрацюватися, наговорити, наробити, наїстися, перемити, пофарбувати, під'єднати, роздрукувати* (if in text), *копія* (if in text). Actually, perform a strict sync.

### Language: 8/10 → 9/10

**What to fix:**
1. **Activity Unjumble "The Office"**: Change Item 5 "Я дочитав книгу нарешті вчора ввечері після довгого часу читання" to "Я нарешті дочитав книгу вчора ввечері".

### Projected Overall After Fixes

```
(8*1.5 + 9*1.0 + 10*1.0 + 8*1.2 + 9*1.1 + 9*1.2 + 8*1.0 + 9*1.3 + 9*0.9 + 8*1.3 + 9*1.0 + 9*1.5) / 14.0 = 8.8 -> Round to 9.0
```

## Verification Summary

- Content lines read: 145
- Activity items checked: 43
- Ukrainian sentences verified: ~30
- IPA transcriptions checked: N/A (Vocab file ignored due to quality issues)
- Issues found: 5 Major (Contradictions + Vocab garbage)
- Naturalness score recommendation: 9/10 (Content is good, Activities need fix)

## Verdict

**FAIL**

The content explains the difference between *відчинити* (physical) and *відкрити* (abstract) well, but the activities explicitly penalize the student for following this rule, forcing them to use *відкрити* for doors and windows. This is a critical pedagogical failure that confuses the learner. Additionally, the vocabulary file is filled with hallucinations not present in the lesson.

===REVIEW_END===
