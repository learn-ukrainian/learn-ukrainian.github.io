===REVIEW_START===
# Рецензія: The Instrumental II — Means and Tools

**Level:** A2 | **Module:** 5
**Overall Score:** 8.6/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [FAIL]
- Sections: [all present]
- Vocabulary: [14/15 from plan used, 'тролейбус' missing]
- Grammar scope: [clean]
- Objectives: [all covered]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Good flow, clear transition from previous module. |
| 2 | Coherence | 9/10 | <7 | Strong logical progression. |
| 3 | Relevance | 10/10 | <7 | Highly relevant daily topics (transport, tools). |
| 4 | Educational | 9/10 | <7 | Explanations are clear and accessible. |
| 5 | Language | 8/10 | <8 | "Працювати комп'ютером" is unnatural; grammar slip with "Очі... його". |
| 6 | Pedagogy | 9/10 | <7 | PPP structure followed well. |
| 7 | Immersion | 8/10 | <6 | ~45% Ukrainian, appropriate for early A2. |
| 8 | Activities | 8/10 | <7 | Item 15 in Fill-in miscategorized (Accompaniment vs Tool). |
| 9 | Richness | 9/10 | <6 | 1485 words (Target 1000). |
| 10 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5. Friendly tone. |
| 11 | LLM Fingerprint | 8/10 | <7 | Some vocab list oddities (`їда`, `окуляр`). |
| 12 | Linguistic Accuracy | 8/10 | <9 | Missing stress in IPA for `гроші`; rigid T/F on transport meaning. |

**Weighted Overall:** 8.6/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [List: Item 15 in 'Fill in the Instrumental Tool' tests accompaniment]
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Missing Required Vocabulary
- **Location**: Content & Vocabulary File
- **Original**: (Missing)
- **Problem**: Plan requires `тролейбус`, but it is absent from text and vocab.
- **Fix**: Add `тролейбус` to the Transport table and vocabulary list.

### Issue 2: Unnatural Collocation
- **Location**: Line 68 / Presentation
- **Original**: "Наприклад, якщо ви кажете «я працюю комп'ютером»"
- **Problem**: "Працювати комп'ютером" is unnatural; standard is "працювати за комп'ютером" (Locative). While grammatically possible as "using a computer as a tool", it's a poor example for learners compared to physical tools.
- **Fix**: Replace with a physical tool example: "Наприклад, якщо ви забиваєте цвях **молотком**" or use "користуватися комп'ютером".

### Issue 3: Activity Category Error
- **Location**: Activities / Fill in the Instrumental Tool / Item 15
- **Original**: "Він товаришує з {Максимом...}"
- **Problem**: The activity title is "Fill in the Instrumental **Tool**". "Friendship with Maxim" is **Accompaniment** (with preposition). It contradicts the module's "No Preposition" focus and the activity's title.
- **Fix**: Replace with a tool sentence: "Він малює портрет {олівцем|...}"

### Issue 4: Grammar Slip
- **Location**: Line 82 / Body Parts
- **Original**: "Очі — це особливе слово. Його форма..."
- **Problem**: `Очі` is plural. "Його" (singular) refers to "слово", but the antecedent in the learner's mind is the plural "Очі".
- **Fix**: "Слово «очі» — особливе. Його форма..." (Clearer reference) or "Очі — це множина. Їхня форма..."

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 68 | працюю комп'ютером | користуюся комп'ютером / працюю молотком | Unnatural |
| Vocab | /ɦrɔʃi/ | /ɦrˈɔʃi/ | IPA Error |
| Vocab | окуляр | окуляри | Unnatural (Singular) |
| Vocab | їда | їжа | Unnatural (Colloquial) |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? Pass
- Instructions clear? Pass
- Quick wins? Pass
- Ukrainian scary? Pass
- Come back tomorrow? Pass

Emotional beats: 4 found
- Welcome: Line 4 "Last module introduced..."
- Curiosity: Line 18 "Why No Preposition?"
- Quick wins: Transport table (cognates).
- Encouragement: "It adds a touch of history to your speech."

## Strengths
- Excellent explanation of the "Bare Instrumental" concept.
- "The bus is walking next to you" tip is memorable and pedagogical.
- Transport table is clear and high-value.

## Fix Plan to Reach 9/10 (REQUIRED)

### Plan-Content Alignment: Fail → Pass

**What to fix:**
1. **Add `тролейбус`**:
   - Add to Transport table: `| тролейбус | їхати **тролейбусом** | Я їду додому тролейбусом. |`
   - Add to `vocabulary.yaml`: `lemma: тролейбус, ipa: /trɔlˈɛjbus/, translation: trolleybus`.

### Language & Linguistic Accuracy: 8/10 → 9/10

**What to fix:**
1. **Line 68**: Change "працюю комп'ютером" → "працюю молотком" (and update context to "якщо ви будуєте дім").
2. **Line 82**: Change "Очі — це особливе слово. Його форма..." → "Слово «очі» має особливу форму в орудному відмінку — **очима**."
3. **Vocabulary**:
   - `їда` → Delete or replace with `їжа`.
   - `окуляр` → `окуляри` (pl).
   - `гроші` IPA → `/ɦrˈɔʃi/`.

### Activities: 8/10 → 9/10

**What to fix:**
1. **Fill-in Item 15**: Remove "Maxim" item. Replace with "Я копаю яму {лопатою|...}" (I dig a hole with a shovel) or "Він малює {олівцем|...}".
2. **True-False**: Soften the "mean the same thing" item or remove it to avoid confusion between semantic and grammatical difference.

### Projected Overall After Fixes

```
(9*1.5 + 9 + 10 + 9*1.2 + 9*1.1 + 9*1.2 + 8 + 9*1.3 + 9*0.9 + 9*1.3 + 9 + 9*1.5) / 14.0 = 9.04
```

## Verification Summary

- Content lines read: 140
- Activity items checked: 45
- Ukrainian sentences verified: ~30
- IPA transcriptions checked: 64
- Issues found: 6
- Naturalness score recommendation: 9/10

## Verdict

**FAIL**

The module is strong conceptually but fails strict Plan Verification (missing `тролейбус`) and contains a category error in the Activities (mixing Accompaniment into a Tool drill). Minor linguistic unnaturalness needs polishing.

===REVIEW_END===
