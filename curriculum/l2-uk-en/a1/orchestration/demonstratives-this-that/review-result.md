# Рецензія: Demonstratives — The Grammar of This and That

**Level:** A1 | **Module:** 21
**Overall Score:** 7.0/10
**Status:** FAIL
**Reviewed:** 2026-03-19
**Reviewed-By:** claude-sonnet-4-6

## Plan Verification

```
Plan-Content Alignment: PARTIAL FAIL
- Sections: 7/7 present (5 content + intro + summary, mapping to 5 plan sections)
- Vocabulary: 12/12 required present in prose, 4/4 recommended present, 20 total
- Grammar scope: FAIL — multiple morphological scope violations (imperatives, non-nominative cases, past/future tense in Ukrainian instructional prose)
- Objectives: 4/4 addressed
```

### Content Outline Point-by-Point

**Section "Цей/ця/це: Вказуємо на близькі об'єкти"**:
- Gender agreement цей (m.), ця (f.), це (n.) with examples: **COVERED** — lines 11-22 present all three forms with examples
- Paradigm parallel to мій/моя/моє: **COVERED** — line 7 explicitly makes this connection
- Copula це vs demonstrative це distinction: **COVERED** — lines 24-38 with contrast table, very well done
- §4.2.2 reference: Not explicitly cited but pedagogically addressed

**Section "Ці: Вказуємо на багато об'єктів"**:
- Plural form ці for all genders with examples: **COVERED** — lines 53-65
- Singular→plural transformation: **COVERED** — lines 57-59
- Common error *цей книги: **COVERED** — line 69 explicitly addresses this

**Section "Той/та/те/ті: Вказуємо на далекі об'єкти"**:
- Gender agreement той/та/те/ті with examples: **COVERED** — lines 84-94
- та ambiguity (demonstrative vs conjunction): **COVERED** — lines 96-104, excellent example 「Та ді́вчи́на та її по́друга.」

**Section "Цей vs Той у контексті"**:
- Spatial proximity цей стілець vs той стілець: **COVERED** — lines 114-117
- Shop/café scenario "Дайте мені цей торт": **PARTIAL** — plan says "Дайте мені цей торт" but content uses 「Remember to use: Цей торт, будь ла́ска.」 (line 121). The "Дайте мені" form is absent, and "Remember to use:" is odd formatting.
- Textual distance (цей for recent, той for earlier): **COVERED** — lines 126-128

**Section "Практика: Тренуємо вказівні займенники"**:
- Exercises choosing correct demonstrative by gender/number: **COVERED** — lines 136-141
- Classification into groups + proximity contrast: **COVERED** — lines 143-148
- Note: Practice section reveals answers inline (lines 138-141), reducing pedagogical challenge

**Activity Hints**:
- fill-in (10 items): **COVERED** ✓
- quiz (12 items): **COVERED** ✓
- match-up (10 items): **COVERED** ✓
- group-sort (12 items): **COVERED** ✓

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Warm tutor voice, good arc from welcome to celebration. "Remember to use:" formatting on lines 121-122 is awkward. Practice section (lines 138-141) gives answers immediately — no challenge. |
| 2 | Language | 6/10 | <8 | **AUTO-FAIL.** 15+ morphological scope violations in Ukrainian instructional prose. Imperatives (Зверніть, Подивіться, перевіряйте, Пам'ятайте), non-nominative cases (середнього роду, різницю, природною, простішою, множині), future tense (буде), past tense (навчилися, вивчили). At M21, Ukrainian prose should use only nominative + present tense. |
| 3 | Pedagogy | 8/10 | <7 | Excellent copula vs demonstrative contrast (lines 24-38). Good error prevention for *цей книги. Missing "Дайте мені" from plan. Practice section too easy (answers visible). |
| 4 | Activities | 8/10 | <7 | 4 types, 44 items total, well-structured. All correct answers verified. Good variety (fill-in, quiz, match-up, group-sort). Quiz item 6 (line 105-115) tests copula distinction — excellent. |
| 5 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 4/5. Warm welcome, clear structure, quick wins. But Ukrainian instructional sentences are too complex for M21 — learner can't parse 「Але коли ми вказуємо на конкретний предмет середнього роду」 at this stage. |
| 6 | LLM Fingerprint | 8/10 | <7 | No structural monotony — section openings vary. No stacked abstract nouns. No "It is important to note" patterns. Minor: lines 121-122 "Remember to use:" is an unusual formatting choice that feels like a prompt artifact. |
| 7 | Linguistic Accuracy | 6/10 | <9 | **AUTO-FAIL.** Morphological violations dominate. Research notes (line 52) explicitly say "No imperative verbs in instructions — use English" but content uses 4 imperatives in Ukrainian. Non-nominative grammar in instructional prose throughout. |

**Weighted Overall:** (8×1.5 + 6×1.1 + 8×1.2 + 8×1.3 + 8×1.3 + 8×1.0 + 6×1.5) / 8.9 = (12 + 6.6 + 9.6 + 10.4 + 10.4 + 8.0 + 9.0) / 8.9 = 66.0 / 8.9 = **7.4/10**

## Auto-Fail Checklist Results

- Russianisms: **CLEAN** — no Russianisms detected
- Calques: **CLEAN** — no calques detected
- Colonial framing: **CLEAN** — no "Unlike Russian..." patterns
- Grammar scope: **FAIL** — 15+ morphological violations (imperatives, non-nominative cases, non-present tenses in Ukrainian instructional prose)
- Activity errors: **CLEAN** — all activities verified correct
- Beginner safety: 4/5
- Factual accuracy: **CLEAN** — grammar explanations are accurate, culture note (line 108) plausible
- LLM fingerprint: **CLEAN** — no auto-fail patterns

## Critical Issues Found

### Issue 1: Morphological Scope Violations — Imperatives in Ukrainian Instructions (HIGH)
- **Location**: Lines 15, 40, 47, 76
- **Original**: 「Зверніть увагу на закінчення.」 (line 15), 「Пам'ятайте про це, і ваша мова буде природною!」 (line 40), 「Подивіться відео про вказівні займенники. Це допомагає краще розуміти тему!」 (line 47), 「Завжди перевіряйте рід іменника. Якщо слово жіночого роду, кажемо «ця» або «та».」 (line 76)
- **Problem**: Imperatives (Зверніть, Пам'ятайте, Подивіться, перевіряйте) not taught until M47. The research notes explicitly state: "No imperative verbs in instructions — use English." These Ukrainian imperative sentences are unparseable for M21 learners.
- **Fix**: Replace all Ukrainian imperative instructions with English. E.g., line 15 → "Notice the endings." / line 40 → "Remember this, and your Ukrainian will be natural!" / line 47 → "Watch this video about demonstrative pronouns. It helps you understand the topic better!" / line 76 → "Always check the gender of the noun. If the word is feminine, we say «ця» or «та»."

### Issue 2: Non-Nominative Cases in Ukrainian Instructional Prose (HIGH)
- **Location**: Lines 34, 40, 51
- **Original**: 「Але коли ми вказуємо на конкретний предмет середнього роду」 (line 34 — genitive середнього роду), 「Бачите різницю?」 (line 40 — accusative різницю), 「У множині українська мова стає простішою!」 (line 51 — instrumental простішою, dative множині)
- **Problem**: At M21, only nominative case is available. Genitive (середнього, роду), accusative (різницю), instrumental (простішою, природною), and dative (множині) appear in Ukrainian instructional prose that learners are expected to read.
- **Fix**: Move these instructional sentences to English. E.g., line 34 → "But when we point to a specific neuter noun..." / line 51 → "In the plural, Ukrainian becomes simpler!"

### Issue 3: Non-Present Tenses in Ukrainian Prose (MEDIUM)
- **Location**: Lines 40, 80, 132
- **Original**: 「Пам'ятайте про це, і ваша мова буде природною!」 (line 40 — future буде), 「Ми навчилися вказувати на предмети поруч.」 (line 80 — past навчилися), 「Ви сьогодні багато вивчили!」 (line 132 — past вивчили)
- **Problem**: Only present tense available before M36. Future (буде) and past (навчилися, вивчили) appear in Ukrainian instructional prose.
- **Fix**: Replace with English or present tense. E.g., line 80 → "We now know how to point to objects nearby." / line 132 → "You've learned a lot today!"

### Issue 4: "Remember to use:" Formatting Artifact (LOW)
- **Location**: Lines 121-122
- **Original**: 「Remember to use: Цей торт, будь ла́ска.」
- **Problem**: "Remember to use:" is an unusual prompt-like prefix. The plan specifies "Дайте мені цей торт" but the content uses "Цей торт, будь ла́ска" with this odd framing. "Дайте мені" is imperative so shouldn't be in Ukrainian either, but the example should flow naturally.
- **Fix**: Remove "Remember to use:" prefix. Present as: `*   **Цей торт, будь ла́ска.** — This cake here, please.`

### Issue 5: Practice Section Reveals Answers Inline (MEDIUM)
- **Location**: Lines 138-141
- **Problem**: The fill-in-the-blank exercise shows the answer immediately after each blank: "_____ **хло́пець** (masculine) → **цей хло́пець**". This removes the pedagogical challenge — the learner reads the answer without attempting it.
- **Fix**: Present blanks without answers, then provide answers in a separate collapsed/spoiler section, or simply remove the answers and let the activities YAML handle interactive practice.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 15 | 「Зверніть увагу на закінчення.」 | "Notice the endings." (English) | Scope — imperative |
| 34 | 「на конкретний предмет середнього роду」 | "a specific neuter noun" (English) | Scope — genitive |
| 40 | 「Бачите різницю?」 | "Can you see the difference?" (English) | Scope — accusative |
| 40 | 「Пам'ятайте про це, і ваша мова буде природною!」 | "Remember this, and your Ukrainian will sound natural!" (English) | Scope — imperative + future + instrumental |
| 47 | 「Подивіться відео про вказівні займенники. Це допомагає краще розуміти тему!」 | "Watch this video about demonstrative pronouns. It helps you understand the topic better!" (English) | Scope — imperative + accusative |
| 51 | 「У множині українська мова стає простішою!」 | "In the plural, Ukrainian becomes simpler!" (English) | Scope — dative + instrumental |
| 76 | 「Завжди перевіряйте рід іменника. Якщо слово жіночого роду, кажемо «ця» або «та».」 | "Always check the gender of the noun. If the word is feminine, we say «ця» or «та»." (English) | Scope — imperative |
| 80 | 「Ми навчилися вказувати на предмети поруч.」 | "We've learned to point to nearby objects." (English) | Scope — past tense |
| 132 | 「Ви сьогодні багато вивчили!」 | "You've learned a lot today!" (English) | Scope — past tense |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? **Pass** — pacing is comfortable, small chunks, clear structure
- Instructions clear? **Pass** — learner always knows what to do
- Quick wins? **Pass** — цей/ця/це presented early, quick pattern recognition
- Ukrainian scary? **Fail** — Ukrainian instructional sentences (「Але коли ми вказуємо на конкретний предмет середнього роду」) contain grammar far beyond M21. A beginner would hit walls of unparseable Ukrainian prose.
- Come back tomorrow? **Pass** — encouraging tone, good closing at line 164

## Strengths

- **Excellent copula vs demonstrative contrast** (lines 24-38): The distinction between "Це кафе" (copula) and "Це кафе гарне" (demonstrative) is the hardest concept in this module and it's handled beautifully with clear examples and explicit contrast.
- **та ambiguity teaching** (lines 96-104): The double-та example 「Та ді́вчи́на та її по́друга.」 is a perfect illustration, with clear explanation of position-based disambiguation.
- **Warm tutor voice**: Opening connects to prior knowledge (мій/моя/моє), closing celebrates progress with 「Чудова робота! Ви будуєте міцний фундамент.」
- **Activity quality**: 44 items across 4 types, all answers verified correct. Quiz item testing copula distinction (lines 105-115) is particularly clever.
- **Vocabulary coverage**: All 12 required + 4 recommended words from plan present in prose and activities.

## Fix Plan to Reach 9/10 (REQUIRED if score < 9.0)

### Language: 6/10 → 9/10
**What to fix:**
1. Lines 15, 40, 47, 76: Replace ALL Ukrainian imperative instructions with English equivalents (4 locations)
2. Lines 34, 40, 51: Replace Ukrainian sentences containing non-nominative cases with English (3 locations)
3. Lines 40, 80, 132: Replace Ukrainian past/future tense in instructional prose with English (3 locations)
4. Lines 42, 71: Video titles contain УКРАЇ́НСЬКОЮ (instrumental) — these are external titles, acceptable to keep as-is (DISMISS)

**Expected score after fix:** 9/10

### Linguistic Accuracy: 6/10 → 9/10
**What to fix:**
Same fixes as Language above — the morphological violations are the only accuracy issue. Grammar explanations themselves are correct. Example Ukrainian sentences (цей хлопець, ця вулиця, etc.) are all properly formed nominative phrases — the violations are exclusively in instructional/meta prose.

**Expected score after fix:** 9/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Lines 121-122: Remove "Remember to use:" prefix
2. Lines 138-141: Remove inline answers from practice blanks, or restructure as "try first, then check"

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 8×1.2 + 8×1.3 + 8×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 9.6 + 10.4 + 10.4 + 8.0 + 13.5) / 8.9
= 75.3 / 8.9 = 8.5/10
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (not applicable — grammar module)
- Dates checked: N/A
- Named figures verified: N/A
- Primary quotes cross-referenced: N/A
- Chronological sequence: N/A
- Claims without research grounding: 0
- Grammar rules verified: All demonstrative pronoun gender agreement rules are accurate per textbook references (Grade 6, pp. 272-273 declension tables confirm той/та/те/ті paradigm)
- Culture note (line 108): 「У магазині українці часто кажуть «цей» або «той».」 — plausible, aligns with research cultural hook #1 (market/café scenario)

## VESUM Pre-Scan Dismissals

The 4 words flagged as "not found" (Пам, ятайте, єкти, єктів) are **tokenization artifacts** from apostrophe splitting. The actual words are:
- Пам'ятайте → VESUM: `verb:imperf:impr:p:2` (valid, but scope violation — imperative)
- об'єкти / об'єктів → VESUM: `noun:inanim:p:v_naz` (valid, in section headers only)

All 4 dismissed as false positives.

## Pre-Screen Confirmation/Dismissal

| # | Pre-screen finding | Verdict | Rationale |
|---|-------------------|---------|-----------|
| 1 | Зверніть (imperative, line 15) | **CONFIRMED** | Imperative in Ukrainian instruction |
| 2 | увагу (accusative, line 15) | **CONFIRMED** | Part of imperative phrase |
| 3 | середнього (genitive, line 34) | **CONFIRMED** | Non-nominative in instruction |
| 4 | роду (genitive, line 34) | **CONFIRMED** | Non-nominative in instruction |
| 5 | різницю (accusative, line 40) | **CONFIRMED** | Non-nominative in instruction |
| 6 | буде (future, line 40) | **CONFIRMED** | Future tense in instruction |
| 7 | природною (instrumental, line 40) | **CONFIRMED** | Non-nominative in instruction |
| 8 | УКРАЇ́НСЬКОЮ (instrumental, line 42) | **DISMISSED** | External video title — not lesson prose |
| 9 | Подивіться (imperative, line 47) | **CONFIRMED** | Imperative in Ukrainian instruction |
| 10 | тему (accusative, line 47) | **CONFIRMED** | Non-nominative in instruction |
| 11 | їх (genitive, line 51) | **CONFIRMED** | Non-nominative in instruction |
| 12 | множині (dative, line 51) | **CONFIRMED** | Non-nominative in instruction |
| 13 | простішою (instrumental, line 51) | **CONFIRMED** | Non-nominative in instruction |
| 14 | УКРАЇ́НСЬКОЮ (instrumental, line 71) | **DISMISSED** | External video title — not lesson prose |
| 15 | перевіряйте (imperative, line 76) | **CONFIRMED** | Imperative in Ukrainian instruction |
| 16 | ді́вчи stress unknown | **DISMISSED** | Tokenization artifact of ді́вчи́на |

**Additional violations found** (missed by pre-screen):
- Line 40: Пам'ятайте (imperative, `verb:imperf:impr:p:2`)
- Line 80: навчилися (past tense, `verb:rev:perf:past:p`)
- Line 132: вивчили (past tense, `verb:perf:past:p`)

## Verification Summary

- Content lines read: 165
- Activity items checked: 44 (10 fill-in + 12 quiz + 10 match-up + 12 group-sort)
- Ukrainian sentences verified: 28
- Citations in bank: 19
- Issues found: 5 (3 critical, 2 medium)
- VESUM verifications performed: 8
- Pre-screen items confirmed: 13/16 (2 dismissed as video titles, 1 as tokenization artifact)

## Verdict

**FAIL**

Blocking issues: (1) **15+ morphological scope violations** — Ukrainian instructional prose uses imperatives, non-nominative cases, and non-present tenses that M21 learners cannot parse. The research notes explicitly prohibit imperatives in instructions. (2) **Language and Linguistic Accuracy both auto-fail** (6/10 each, thresholds 8 and 9). The fixes are straightforward — convert Ukrainian instructional sentences to English while keeping Ukrainian example phrases intact. The underlying content quality (pedagogy, activities, vocabulary coverage) is strong and should pass easily after morphological fixes.