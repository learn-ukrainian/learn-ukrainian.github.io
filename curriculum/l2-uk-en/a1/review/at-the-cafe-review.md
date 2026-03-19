<!-- content-hash: 9a87d4bd36c6 -->
# Рецензія: At the Café

**Level:** A1 | **Module:** 41
**Overall Score:** 7.7/10
**Status:** FAIL
**Reviewed:** 2026-03-19
**Reviewed-By:** claude-opus-4-6

## Plan Verification

```
Plan-Content Alignment: FAIL
- Sections: 3/4 present. "Продукція та Підсумок (Production and Summary)" renamed to "Summary" — heading mismatch.
- Vocabulary: 8/8 required words in prose, 7/7 recommended in vocab sidecar. Extra: бариста, кав'ярня, замовлення, лимон, оплата.
- Grammar scope: Accusative COVERED. Imperative practice MISSING from prose. Instrumental/Genitive case labels leak into activities (plan says NO case labels).
- Objectives: 3/4 met. "Ask for recommendations" not explicitly covered.
```

### Plan Adherence Checklist

**Section "Вступ (Introduction)":**
- "Львівська традиція «Піти на каву» як ключовий соціальний ритуал" — **COVERED** (lines 3, 10)
- "Легенда про Юрія Кульчицького" — **COVERED** (line 16)

**Section "Презентація (Presentation)":**
- "Привітання та етикет: обов'язкове використання форми «Ви»" — **COVERED** (line 22)
- "Ввічливе замовлення: корекція помилки «Я хочу» на «Мені, будь ласка...» або «Я буду...»" — **COVERED** (lines 40-44)
- "Граматичний фокус: Знахідний відмінок — «кава» -> «каву», «вода» -> «воду»" — **COVERED** (lines 46-54)
- "Лексичний підхід: «з молоком» та «без цукру» як готових фраз-чанків без пояснення відмінків" — **COVERED** in prose (lines 58-66), **VIOLATED** in activities (explanations label Instrumental/Genitive)

**Section "Практика (Practice)":**
- "Дрилі на вживання Знахідного відмінка: виправлення типової помилки «Я буду кава»" — **COVERED** (lines 70-77)
- "Форми наказового способу: «дайте, будь ласка» та «принесіть, будь ласка»" — **MISSING** from prose. Neither phrase appears in the content. Only in activity options.
- "Розрізнення «рахунок» vs «чек»" — **COVERED** (line 119)
- "Уточнення замовлення: прикметники-антоніми (великий чи малий, холодний чи гарячий)" — **COVERED** (lines 84-89)

**Section "Продукція та Підсумок (Production and Summary)":**
- Section heading — **MISSING**. Content has "Summary" instead of "Продукція та Підсумок".
- "Вивчення фрази «Можна рахунок?»" — **MISSING**. The phrase never appears.
- "«Оплата карткою» та «Я заплачу готівкою»" — **COVERED** (lines 113, 140)
- "Етикет та чайові" — **COVERED** (lines 142-143)
- "Підсумкова рольова гра: симуляція повного циклу" — **COVERED** (lines 145-154)

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Good cultural hooks & dialogues. Missing explicit learning preview ("Today you'll learn...") and no progress celebration — "Summary" section is functional but lacks warmth. |
| 2 | Language | 7/10 | <8 | 4+ stress errors: каже́→ка́же (lines 10,93), мо́мент→моме́нт (line 13), Олена́→Оле́на (line 93 ×3), вголо́с→вго́лос (line 28). No Russianisms. English prose is clear and warm. |
| 3 | Pedagogy | 7/10 | <7 | PPP structure solid. Missing imperative practice (plan point). Activities leak Instrumental/Genitive case labels that plan explicitly forbids at A1. Missing "Можна рахунок?" phrase. |
| 4 | Activities | 7/10 | <7 | All 4 types/counts match plan. VESUM-failing distractors (менюу, менює, менюм). Case scope violations in 7 activity explanations. Good variety of drill formats. |
| 5 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 4.5/5. Warm, scaffolded. Ukrainian never scary. Slight lack of explicit preview and celebratory close. |
| 6 | LLM Fingerprint | 9/10 | <7 | Varied section openings. No structural monotony. Mixed formats (tables, dialogues, bullets). One "це не просто" (below threshold). |
| 7 | Linguistic Accuracy | 7/10 | <9 | 4 distinct stress errors across 7+ instances. 3 non-existent VESUM forms in activity distractors. False summary claim about "request a table" (never taught). |

**Weighted Overall:** (8×1.5 + 7×1.1 + 7×1.2 + 7×1.3 + 9×1.3 + 9×1.0 + 7×1.5) / 8.9 = (12 + 7.7 + 8.4 + 9.1 + 11.7 + 9.0 + 10.5) / 8.9 = 68.4 / 8.9 = **7.7/10**

## Auto-Fail Checklist Results

- Russianisms: **CLEAN** — no Russian ghost words detected
- Calques: **CLEAN** — no calques detected
- Colonial framing: **CLEAN** — no "unlike Russian" comparisons
- Grammar scope: **VIOLATION** — activity explanations label Instrumental and Genitive cases (A2 scope) despite plan explicitly requiring chunk-only approach
- Activity errors: **FAIL** — 3 non-existent Ukrainian word forms as distractors (менюу, менює, менюм)
- Beginner safety: 4.5/5
- Factual accuracy: **ISSUE** — summary claims "request a table" was taught; it was not

## Critical Issues Found

### Issue 1: Stress Errors (Linguistic Accuracy — HIGH)

**Multiple stress placement errors across the module:**

- **Location**: Line 10, Section "Вступ (Introduction)"
- **Original**: 「Коли́ хтось каже́: «Пі́демо на ка́ву?» — це запро́шення поговори́ти.」
- **Problem**: каже́ has wrong stress. Correct stress is ка́же (stress on first syllable). Appears again on line 93.
- **Fix**: Replace каже́ → ка́же in all occurrences.

- **Location**: Line 13, Section "Вступ (Introduction)"
- **Original**: 「Ка́ва — це мо́мент для спілкува́ння, для дру́жби.」
- **Problem**: мо́мент has wrong stress. Correct stress is моме́нт (stress on second syllable).
- **Fix**: Replace мо́мент → моме́нт.

- **Location**: Line 28, Section "Презентація (Presentation)"
- **Original**: 「Прочита́йте ці фра́зи вголо́с. Уяві́ть, що ви — бари́ста у льві́вській кав'я́рні.」
- **Problem**: вголо́с has wrong stress. Correct stress is вго́лос.
- **Fix**: Replace вголо́с → вго́лос.

- **Location**: Line 93, Section "Практика (Practice)"
- **Original**: 「О дев'я́тій ра́нку Олена́ іде́ до кав'я́рні.」
- **Problem**: Олена́ has wrong stress. Correct stress is Оле́на (stress on second syllable). Appears 3 times on this line.
- **Fix**: Replace Олена́ → Оле́на in all occurrences.

### Issue 2: Non-Existent VESUM Distractors in Activity (Activities — HIGH)

- **Location**: at-the-cafe.yaml line 23, Activity "Complete the Café Order" item 5
- **Original**: `options: ["меню", "менюу", "менює", "менюм"]`
- **Problem**: менюу, менює, and менюм are not real Ukrainian word forms (confirmed not found in VESUM). Students would practice rejecting non-existent forms, which teaches nothing useful and could confuse them. The whole point of the activity item is that меню is indeclinable — the distractors should be plausible but wrong case forms of other words, or common learner misconceptions.
- **Fix**: Replace with plausible distractors that a learner might actually confuse: e.g., `["меню", "меню́ю", "меню́а", "меню́і"]` — or better, replace the entire item with a different ordering scenario since the indeclinability of меню is hard to test with a fill-in format.

### Issue 3: Missing Plan Section "Продукція та Підсумок" (Pedagogy — MEDIUM)

- **Location**: Line 121, Section "Summary"
- **Problem**: Plan defines section "Продукція та Підсумок (Production and Summary)" but the content only has "Summary". The "Продукція" (Production) phase — where learners produce language freely — is collapsed into the Summary. The plan's Production points include "Можна рахунок?" (completely absent) and a full-cycle roleplay with the "Chatty Barista" persona.
- **Fix**: Rename "## Summary" to "## Продукція та Підсумок (Production and Summary)" and add the missing "Можна рахунок?" phrase with practice context.

### Issue 4: Missing Imperative Practice in Prose (Pedagogy — MEDIUM)

- **Location**: Section "Практика (Practice)" (lines 68-117)
- **Problem**: Plan point "Форми наказового способу: практика вживання ввічливих команд «дайте, будь ласка» та «принесіть, будь ласка»" is not addressed in the prose content. Neither "дайте" nor "принесіть" appears in the lesson text. They only appear as activity answer options. The research notes grant these as a plan exception (chunks, not paradigm), but they still need to appear in the teaching content.
- **Fix**: Add a short subsection in section "Практика (Practice)" introducing "Дайте, будь ласка..." and "Принесіть, будь ласка..." as polite request chunks, with 2-3 example phrases.

### Issue 5: Activity Explanations Leak A2 Grammar Scope (Pedagogy — MEDIUM)

- **Location**: at-the-cafe.yaml lines 74, 78, 82, 86, 90 (Activity "Complete the Ordering Phrases") and lines 49, 53, 245
- **Problem**: Plan explicitly states: "вивчення конструкцій «з молоком» та «без цукру» як готових фраз-чанків **без пояснення відмінків** для рівня A1." But 7 activity explanations label these as "Instrumental case" and "Genitive case" — terms not yet in scope. This contradicts the chunk-first approach.
- **Fix**: Rewrite explanations to use chunk language instead of case terminology. E.g., "З (with) requires the Instrumental case: молоко → молоком" → "З (with) changes the word: молоко → молоком. Memorize this as a fixed phrase."

### Issue 6: False Summary Claim (Factual Accuracy — LOW)

- **Location**: Line 156, Section "Summary"
- **Original**: 「You are now fully equipped to enjoy the vibrant Ukrainian café scene. You know how to politely request a table, order your favorite beverages using the proper grammar, customize your drinks with handy chunks, and settle your bill without any awkward mix-ups.」
- **Problem**: "request a table" is never taught in this module. No vocabulary for столик, no phrases for requesting seating.
- **Fix**: Remove "politely request a table" — replace with something actually taught, like "greet the staff and place your order."

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 10 | 「каже́」 | 「ка́же」 | Stress |
| 13 | 「мо́мент」 | 「моме́нт」 | Stress |
| 28 | 「вголо́с」 | 「вго́лос」 | Stress |
| 93 | 「Олена́」 (×3) | 「Оле́на」 | Stress |
| 93 | 「каже́」 | 「ка́же」 | Stress |

### Pre-Screen Dismissals

- **#3 (Agreement 'вели́ку' + 'Вам')**: FALSE POSITIVE. 「Вам вели́ку чи малу́ ка́ву?」 — вели́ку agrees with ка́ву (fem. acc.), not with Вам. Correct Ukrainian.
- **#4 (Agreement 'дев'я́тій' + 'ра́нку')**: FALSE POSITIVE. "О дев'я́тій ра́нку" is a fixed time expression where дев'ятій modifies implied годині (hour), not ра́нку.
- **#1-2 (Imperatives Прочитайте/Уявіть)**: DISMISS. Research notes document a plan exception granting imperatives for this module. These are also meta-instructions to the learner, not café vocabulary being taught.
- **#7 (Бари́ста stress unknown)**: DISMISS. VESUM confirms бариста exists. Stress on second syllable is standard for this loanword.
- **#10 (вікна́ → ві́кна)**: DISMISS. In 「бі́ля вікна́」 this is genitive singular of вікно́. Stress вікна́ is correct for genitive singular.

## Beginner Safety Audit

"Would I Continue?" Test: 4.5/5
- Overwhelmed? **Pass** — gentle pacing, Ukrainian introduced with translations throughout
- Instructions clear? **Pass** — each section has clear English setup, though no explicit "Today you'll learn..." preview
- Quick wins? **Pass** — cultural note engagement early, vocabulary table by line 48-54
- Ukrainian scary? **Pass** — always presented with English translations in parentheses
- Come back tomorrow? **Pass** — warm tone, interesting cultural hooks about Lviv and Kulchytskyi

**Minor gaps**: No explicit learning objectives preview at start. Closing line (156) reads as a generic summary rather than a warm celebration of progress.

## Strengths

- **Excellent cultural immersion**: The Kulchytskyi legend and Lviv café culture give the module a genuine Ukrainian soul, not just transaction vocabulary. The "піти на каву" framing teaches culture alongside language.
- **Strong error correction pedagogy**: The "Я хочу каву" → "Мені, будь ласка, каву" correction at line 40 is exactly how Ukrainian teachers address this, with clear explanation of why the direct translation sounds blunt.
- **Rich dialogue practice**: The full waiter-customer dialogue (lines 99-117) is authentic and covers the complete café visit cycle. Learners get a realistic script they can actually use.
- **Smart use of the рахунок vs чек distinction**: Line 119 addresses a real-world error trap that most L2 resources miss.
- **Activity variety and volume**: 39 items across 4 activities, covering Accusative drills, dialogue completion, phrase building, and comprehension — thorough practice.

## Fix Plan to Reach 9/10 (REQUIRED)

### Linguistic Accuracy: 7/10 → 9/10
**What to fix:**
1. Line 10: Change 「каже́」 → 「ка́же」
2. Line 13: Change 「мо́мент」 → 「моме́нт」
3. Line 28: Change 「вголо́с」 → 「вго́лос」
4. Line 93: Change 「Олена́」 → 「Оле́на」 (3 occurrences) and 「каже́」 → 「ка́же」
5. Activities line 23: Replace non-existent distractors менюу, менює, менюм with plausible alternatives
6. Line 156: Remove false claim about "request a table"

**Expected score after fix:** 9/10

### Language: 7/10 → 9/10
**What to fix:** Same stress fixes as Linguistic Accuracy. All stress errors are the only Language issue.
**Expected score after fix:** 9/10

### Pedagogy: 7/10 → 9/10
**What to fix:**
1. Add imperative chunks (дайте, будь ласка / принесіть, будь ласка) to section "Практика (Practice)" — 3-4 sentences with English translations
2. Add "Можна рахунок?" to section "Summary" or rename section to match plan
3. Rename "## Summary" → "## Продукція та Підсумок (Production and Summary)"
4. Rewrite 7 activity explanations to remove Instrumental/Genitive case labels

**Expected score after fix:** 9/10

### Activities: 7/10 → 9/10
**What to fix:**
1. Replace VESUM-failing distractors in activity item 5
2. Rewrite case-labeling explanations to use chunk language

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
Experience: 8 → 8.5 (with section rename + preview)
Language: 7 → 9 (stress fixes)
Pedagogy: 7 → 9 (missing content added)
Activities: 7 → 9 (distractors + explanations fixed)
Beginner Safety: 9 → 9 (unchanged)
LLM Fingerprint: 9 → 9 (unchanged)
Linguistic Accuracy: 7 → 9 (stress + distractors + summary fixed)

Projected = (8.5×1.5 + 9×1.1 + 9×1.2 + 9×1.3 + 9×1.3 + 9×1.0 + 9×1.5) / 8.9
         = (12.75 + 9.9 + 10.8 + 11.7 + 11.7 + 9.0 + 13.5) / 8.9
         = 79.35 / 8.9
         = 8.9/10
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (not seminar track — N/A)
- Dates checked: 0 (no specific dates in prose beyond "seventeenth century" — plausible)
- Named figures verified: 1 (Yuriy Kulchytskyi — confirmed in research notes)
- Primary quotes cross-referenced: N/A (not seminar track)
- Chronological sequence: CONSISTENT
- Claims without research grounding: 1 — line 156 claims "request a table" was taught (false)
- Callout boxes checked: 3 (cultural note line 5-14, roleplay line 26-35, review box line 125-136) — all factually sound

## Verification Summary

- Content lines read: 156
- Activity items checked: 39
- Ukrainian sentences verified: 25+
- Citations in bank: 13
- Issues found: 6 (4 stress error clusters, 1 VESUM distractor issue, 1 plan section missing, 1 imperative practice missing, 1 scope violation in activities, 1 false summary claim)

## Verdict

**FAIL**

Blocking issues: (1) Multiple stress errors across 7+ instances auto-fail Linguistic Accuracy (<9 threshold). (2) Non-existent Ukrainian word forms in activity distractors. (3) Missing plan section "Продукція та Підсумок" and missing imperative practice content from plan. All fixable in one pass — stress corrections are mechanical, and the missing content additions are ~100 words.

---

## Post-Fix Re-Score (automated)

**Scored by:** claude-opus-4-6 (on fixed content)
**Overall Score:** 6.2/10
**Verdict:** FAIL

| Dimension | Score |
|-----------|-------|
| experience | 7/10 |
| language | 8/10 |
| pedagogy | 7/10 |
| activities | 4/10 |
| beginner_safety | 7/10 |
| llm_fingerprint | 6/10 |
| linguistic_accuracy | 8/10 |
