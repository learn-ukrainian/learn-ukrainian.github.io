# Рецензія: Yesterday - Past Tense

**Level:** A1 | **Module:** 36
**Overall Score:** 7.5/10
**Status:** FAIL
**Reviewed:** 2026-03-19
**Reviewed-By:** claude-sonnet-4-6

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: 4/4 present, all match plan H2 headers
- Vocabulary: 8/8 required present in prose, 6/6 recommended present
- Grammar scope: PARTIAL — perfective verbs used in cultural hooks (see below)
- Objectives: 4/4 addressed
```

**Plan Points Checklist:**

Section "Вступ: Що було вчора? (Introduction: What Happened Yesterday?)"
- Контраст теперішнього і минулого часу через культурний контекст (Іван Федоров): **COVERED** — Line 5
- Часові вирази (вчора, минулого тижня, etc.) without prийменник "в": **COVERED** — Lines 7-16
- Мотиваційний блок: **COVERED** — Line 18

Section "Основи минулого часу (Grammar: Past Tense Formation)"
- Правила утворення форм (§4.2.4.1): **COVERED** — Line 22
- Узгодження за родом (він читав / вона читала): **COVERED** — Lines 26-33
- Типова помилка: родове узгодження: **COVERED** — Line 33
- Кальки з англійської ("Я був працював"): **COVERED** — Line 40

Section "Складні випадки та практика (Irregular Verbs and Practice)"
- Неправильні дієслова їсти/йти: **COVERED** — Lines 57-65
- Культурний гачок ЗУНР: **COVERED** — Line 67
- Дрилі на розрізнення форм: **COVERED** — Lines 69-78

Section "Підсумок: Мій день (Summary and Production)"
- Продуктивне завдання: **COVERED** — Line 83
- Діалогічна практика: **COVERED** — Lines 87-94
- Фінальний чек: **COVERED** — Lines 96-99

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 7/10 | <7 | No callout boxes at all. Zero engagement markers (`[!tip]`, `[!did-you-know]`, etc.). Wall-of-text in multiple sections. No visual variety beyond one grammar table. |
| 2 | Language | 8/10 | <8 | Spelling error 「републіка」 (line 67) — should be "республіка". Anglicism 「робити каву」/「робив каву」 (lines 44, 83) — should be "варити/готувати каву". |
| 3 | Pedagogy | 8/10 | <7 | Good PPP arc overall, but no quick-win practice opportunity before the long grammar section. Concepts pile up before first activity break. Missing the Ukrainian proverb "Що було, те минуло" recommended by research notes. |
| 4 | Activities | 7/10 | <7 | Only 3 activities, all fill-in type. Zero variety — plan calls for fill-in but 3 separate focus areas. 51 items total is good quantity, but identical interaction type throughout is monotonous. No match-up, no sorting, no dialogue completion. |
| 5 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 4/5. Module is warm and encouraging, but some sections are dense (e.g., lines 53-79 introduce 4+ verb paradigms without a practice break). |
| 6 | LLM Fingerprint | 7/10 | <7 | 「It is incredibly motivating to realize that with just one new tense, you can tell your friends about your entire day」— generic motivational filler. 「Welcome back to our journey through the fascinating world of the Ukrainian language!」— formulaic LLM opening. Multiple sections start with similar expository setup. |
| 7 | Linguistic Accuracy | 8/10 | <9 | 「републіка」is misspelled (not in VESUM). Perfective verbs 「надрукував」and 「прийняла」violate the A1 imperfective-only scope per research notes, though used in cultural hooks rather than as drill targets. 「робити каву」/「робив каву」 is an English calque (correct: варити/готувати каву). |

**Weighted Overall:** (7×1.5 + 8×1.1 + 8×1.2 + 7×1.3 + 8×1.3 + 7×1.0 + 8×1.5) / 8.9 = (10.5 + 8.8 + 9.6 + 9.1 + 10.4 + 7.0 + 12.0) / 8.9 = 67.4 / 8.9 = **7.6/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN] — no Russianisms detected
- Calques: [FOUND] — 「робити каву」(line 44, 83) is an English calque of "make coffee"; correct Ukrainian: варити каву / готувати каву
- Grammar scope: [FOUND] — perfective verbs надрукував (line 5), прийняла (line 67) used in cultural hooks; research notes specify "Imperfective aspect ONLY" for A1
- Activity errors: [CLEAN] — all 51 activity items checked, verb forms and gender agreement correct
- Beginner safety: 4/5
- Factual accuracy: [MINOR] — 「републіка」misspelled (line 67)
- Colonial framing: [CLEAN]

## Critical Issues Found

### Issue 1: Spelling Error — "републіка"
- **Location**: Line 67, Section "Складні випадки та практика (Irregular Verbs and Practice)"
- **Original**: 「Because the word "републіка" (implied by the acronym) is a singular feminine subject」
- **Problem**: "републіка" is not a Ukrainian word (VESUM returns NOT FOUND). The correct spelling is "республіка" (with с).
- **Fix**: Change "републіка" to "республіка"

### Issue 2: Anglicism — "робити каву" (make coffee)
- **Location**: Lines 44 and 83, Sections "Основи минулого часу (Grammar: Past Tense Formation)" and "Підсумок: Мій день (Summary and Production)"
- **Original**: 「Я **робив** каву. — I made coffee. (masculine)」and 「such as **робити каву** (to make coffee)」
- **Problem**: "робити каву" is a direct English calque of "make coffee". Native Ukrainian speakers say "варити каву" (to brew coffee) or "готувати каву" (to prepare coffee). This is explicitly listed in the A1 Anglicism Lookup: "роблять каву" → "готують каву".
- **Fix**: Replace "робив каву" → "варив каву" / "готував каву" throughout; update activities and vocabulary file accordingly. NOTE: This calque is present in the **plan itself** (vocabulary_hints and content_outline both use "робити каву"), so this is a plan-level issue that should be reported upstream.

### Issue 3: Zero Engagement Boxes
- **Location**: Entire module — all 4 sections
- **Original**: No `[!tip]`, `[!did-you-know]`, `[!example]`, `[!cultural-note]`, or any callout box found anywhere.
- **Problem**: Pre-computed audit shows 0 engagement boxes (minimum 1 for A1). Richness score is 54% (threshold 60%). The module reads as a dense wall-of-text with no visual variety.
- **Fix**: Add at least 2 callout boxes: (1) A `[!tip]` for the "no preposition with минулого" rule (line 16 area), (2) A `[!did-you-know]` or `[!culture-note]` for the Fedorov printing or ЗУНР cultural hook.

### Issue 4: Perfective Verbs in A1 Module
- **Location**: Lines 5 and 67, Sections "Вступ: Що було вчора?" and "Складні випадки та практика (Irregular Verbs and Practice)"
- **Original**: 「Федоров надрукував «Апостол»」and 「ЗУНР **прийняла** закон」
- **Problem**: Research notes explicitly state: "Imperfective aspect ONLY (per A1 quick-ref) — do NOT introduce perfective verbs (прочитав, з'їв)." Both надрукував (perf. of надрукувати) and прийняла (perf. of прийняти) are perfective. These appear in cultural hooks, not drills, which partially mitigates the issue — but the learner may confuse them with the imperfective forms being taught.
- **Fix**: Add a brief note near each perfective use explaining these are fixed historical phrases, not drill targets. Or rephrase: "Федоров друкував «Апостол» у Львові" (imperfective, emphasizing the process).

### Issue 5: LLM Filler Opening
- **Location**: Line 3, Section "Вступ: Що було вчора? (Introduction: What Happened Yesterday?)"
- **Original**: 「Welcome back to our journey through the fascinating world of the Ukrainian language!」
- **Problem**: Generic LLM-style opening. A real tutor would open with a specific hook, not a formulaic greeting. The module should open with the cultural hook (Fedorov) or a direct question about yesterday.
- **Fix**: Replace with a more direct, engaging opening: "What did you do yesterday? If you can't answer that question in Ukrainian yet — that's exactly what we're fixing today."

### Issue 6: Activity Monotony — All Fill-In
- **Location**: Activities file, all 3 activities
- **Original**: All three activities are `type: fill-in` with identical interaction pattern
- **Problem**: Zero variety. Plan specifies 3 fill-in activities with different focuses, which is met, but from a learner experience perspective, 51 items of the exact same type (choose from 4 options) is monotonous. At minimum, one activity should be a different type (match-up pairing masculine/feminine forms, or a sorting activity).
- **Fix**: Convert one fill-in to a match-up type (e.g., match subject to correct verb form) to break monotony. This is a MEDIUM priority since the plan does specify fill-in only.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 67 | 「републіка」 | 「республіка」 | Spelling |
| 44 | 「робив каву」 | 「варив каву」 or 「готував каву」 | Anglicism/Calque |
| 83 | 「робити каву」 | 「варити каву」 or 「готувати каву」 | Anglicism/Calque |
| 5 | 「надрукував」 | Consider imperfective or add scope note | Grammar scope |
| 67 | 「прийняла」 | Consider imperfective or add scope note | Grammar scope |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? **Pass** — pacing is generally comfortable, concepts introduced incrementally
- Instructions clear? **Pass** — always know what to learn next
- Quick wins? **Fail** — no practice opportunity until the end-of-module activities; the first 79 lines are all exposition. A mini-drill after the first grammar table (line 31) would help.
- Ukrainian scary? **Pass** — Ukrainian introduced gently with translations
- Come back tomorrow? **Pass** — encouraging tone throughout, clear progress markers

## Strengths
- Excellent coverage of all plan points — every content_outline item is addressed
- The "Я був працював" calque warning (line 40) is genuinely useful and clearly explained
- Good gender agreement emphasis throughout, with practical examples
- The dialogue in Section "Підсумок: Мій день (Summary and Production)" (lines 87-94) is natural and well-constructed
- Irregular verb section (їсти, йти) is well-organized with clear paradigms
- Good vocabulary coverage — all 20 items appear naturally in prose

## Fix Plan to Reach 9/10 (REQUIRED if score < 9.0)

### Experience Quality: 7/10 → 9/10
**What to fix:**
1. Add 2-3 callout boxes: `[!tip]` for the минулого-without-preposition rule, `[!did-you-know]` for cultural hooks
2. Add a mini-practice after the first grammar table (after line 31)
3. Break up wall-of-text in section "Складні випадки та практика (Irregular Verbs and Practice)" with visual separators or sub-headers

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Line 67: Fix spelling "републіка" → "республіка"
2. Lines 44, 83: Replace "робити/робив каву" → "варити/варив каву" (NOTE: requires plan-level fix upstream)

**Expected score after fix:** 9/10

### Activities: 7/10 → 8/10
**What to fix:**
1. Add at least one non-fill-in activity type (match-up or sorting)
2. This is constrained by plan specifying fill-in only — score limited without plan amendment

**Expected score after fix:** 8/10

### LLM Fingerprint: 7/10 → 9/10
**What to fix:**
1. Line 3: Replace generic opening with direct, specific hook
2. Line 18: Trim motivational filler 「It is incredibly motivating to realize that...」— replace with a concrete preview of what the learner will be able to do

**Expected score after fix:** 9/10

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Fix "републіка" spelling
2. Fix "робити каву" calque
3. Add brief scope notes near perfective verbs in cultural hooks

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 8×1.2 + 8×1.3 + 8×1.3 + 9×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 9.6 + 10.4 + 10.4 + 9.0 + 13.5) / 8.9
= 76.3 / 8.9 = 8.6/10
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (not a seminar track)
- Dates checked: 2 (February 15, 1574 — Fedorov Apostol: plausible; February 15, 1919 — ЗУНR language law: plausible)
- Named figures verified: 1 (Ivan Fedorov)
- Primary quotes cross-referenced: NOT_APPLICABLE
- Chronological sequence: CONSISTENT
- Claims without research grounding: 0

## Verification Summary

- Content lines read: 101
- Activity items checked: 51 (24 + 20 + 7 = 51 in 3 activities... recounting: Activity 1: 24 items, Activity 2: 20 items, Activity 3: 6 items = 50 total)
- Ukrainian sentences verified: 28
- Citations in bank: 18
- Issues found: 6

## Verdict

**FAIL**

Blocking issues: (1) Spelling error "републіка" — deterministic fix. (2) Zero engagement boxes — audit gate failure (richness 54% < 60% threshold). (3) "робити каву" Anglicism appears in plan vocabulary_hints, making it a plan-level issue that needs upstream reporting. The module is solid pedagogically but needs these fixes plus callout boxes to pass audit gates.