# Рецензія: The Instrumental I — Accompaniment

**Reviewed-By:** claude-opus-4-6

**Level:** A2 | **Module:** 4
**Overall Score:** 7.5/10
**Status:** FAIL
**Reviewed:** 2026-02-22

## Plan Verification

```
Plan-Content Alignment: PASS (with deviations)
- Sections: Meta defines 4 sections; all 4 present as H2 headers. Plan defined 5 sections;
  content merges "Social Verbs" into «Практика: Соціальні зв'язки». Acceptable since
  meta is authoritative build config.
- Vocabulary: 13/13 required from plan present in vocab YAML; 3/5 recommended (missing
  хліб-сіль, сусідити). «поруч з» in vocab YAML but never taught in content prose.
- Grammar scope: ISSUE — plural instrumental (-ами/-ями) never taught in content but
  heavily tested in activities (scope creep from activities side).
- Objectives: All 4 objectives addressed (form endings ✓, preposition з ✓, doing things
  together ✓, euphony rules ✓).
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Warm opening with «Ласкаво просимо», cultural hooks (Хліб-сіль, friendship hierarchy), two dialogues. But Wedding Starosta persona is barely present — only the mark-the-words activity touches weddings. English padding blocks dilute the learning flow. |
| 2 | Coherence | 8/10 | <7 | Logical progression from intro → endings → social verbs → dialogues → summary in sections «Вступ: Сьомий відмінок і гармонія» through «Діалоги: Зустрічі та плани». Summary section echoes all key points. Good cross-references (a2-05 previewed). |
| 3 | Relevance | 9/10 | <7 | Highly practical social vocabulary. Dialogues cover real scenarios (weekend plans in «Діалоги: Зустрічі та плани», business meetings). Friendship hierarchy is culturally important. |
| 4 | Educational | 7/10 | <7 | Grammar rules clearly presented with tables and examples. But section «Презентація: Форми та Енфонія» is presentation-heavy with no interactivity — learner reads 1100+ words of rules before any practice. The «Енфонія» misspelling in the H2 header teaches a non-existent word. |
| 5 | Language | 7/10 | <8 | «Енфонія» (line 61) is a fabricated Ukrainian word — correct form is «евфонія» or native «милозвучність» (which IS used on line 162). English paragraphs use hyperbolic modifiers: "extremely common" (line 68), "absolutely does not tolerate" (line 162), "completely natural" (line 89), "incredibly often" (line 366), "fundamentally about" (line 366), "massively" (line 245). |
| 6 | Pedagogy | 7/10 | <7 | PPP structure present but imbalanced. Presentation phase (section «Презентація: Форми та Енфонія») runs ~1100 words with zero practice before moving to Practice phase. Plural instrumental tested in activities but never taught. «поруч з» in vocabulary YAML but absent from content. |
| 7 | Immersion | 8/10 | <6 | 58.8% vs 50-60% target — within range. English used for grammar explanations (appropriate for A2 M04). Ukrainian dominates examples, dialogues, and cultural hooks. |
| 8 | Activities | 6/10 | <7 | Good variety (8 types, 12 activities). BUT: (1) Mixed drill item 4 produces «з студентами» — violates euphony rule taught in this module (should be «зі студентами»). (2) Cloze items 8-9 test instrumental of means (з овочами, з лимоном) when module scope is accompaniment only. (3) Plural instrumental (-ами/-ями) tested in 8+ items across 5 activities without being taught. (4) Cloze blank 6 requires «поруч з Оленою» — phrase not taught in content. |
| 9 | Richness | 8/10 | <6 | Two culture notes (Хліб-сіль, friendship hierarchy), two dialogue scenarios, error comparison table, summary table of endings. Good variety of named Ukrainian characters (Оксана, Тарас, Ірина, Максим). |
| 10 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 4/5 — see below. Warm welcome, clear rules, good examples. But English padding makes sections dense before practice arrives. |
| 11 | LLM Fingerprint | 6/10 | <7 | STRUCTURAL MONOTONY: 6+ subsections follow identical pattern: Ukrainian intro sentence → large English paragraph (80-130 words) → Ukrainian rule → bullet examples → Ukrainian sentences. English blocks all start with "In Ukrainian..." / "The Ukrainian language..." / "Feminine nouns ending..." HYPERBOLIC MODIFIERS in every English block: "extremely", "absolutely", "completely", "incredibly", "fundamentally", "massively", "crucial", "highly educated". |
| 12 | Linguistic Accuracy | 8/10 | <9 | «Енфонія» (line 61 H2 header) is a non-existent Ukrainian word — should be «Евфонія» or «Милозвучність». All actual case ending rules are correct. All example sentences are grammatically accurate. Activity euphony error (з студентами) is an activity-side issue. |
| 13 | Factual Accuracy | 9/10 | <8 | Хліб-сіль cultural description aligns with research notes. Friendship hierarchy (знайомий → приятель → друг) is accurate. Salt being "believed to protect against evil spirits" (line 32) is a plausible folk belief but somewhat simplified — not uniquely Ukrainian. Grammar rules are factually correct per Ukrainian State Standard §4.2.2.5.2. |

**Weighted Overall:**
```
(8×1.5 + 8×1.0 + 9×1.0 + 7×1.2 + 7×1.1 + 7×1.2 + 8×1.0 + 6×1.3 +
 8×0.9 + 8×1.3 + 6×1.0 + 8×1.5 + 9×1.5) / 15.5
= (12.0 + 8.0 + 9.0 + 8.4 + 7.7 + 8.4 + 8.0 + 7.8 +
   7.2 + 10.4 + 6.0 + 12.0 + 13.5) / 15.5
= 118.4 / 15.5 = 7.6/10
```

## Auto-Fail Checklist Results

- Russianisms: [CLEAN] — no Russian forms detected
- Calques: [CLEAN]
- Colonial framing: [CLEAN] — line 20 compares with English (L1), not Russian
- Grammar scope: [ISSUE] — plural instrumental tested in activities but never taught in content
- Activity errors: [ISSUE] — euphony violation in mixed drill item 4 (з студентами → зі студентами); scope creep in cloze items 8-9 (means, not accompaniment)
- Beginner safety: 4/5
- Factual accuracy: [CLEAN]
- LLM fingerprint: [ISSUE] — structural monotony, hyperbolic English blocks

## Critical Issues Found

### Issue 1: Fabricated Word «Енфонія» in H2 Header (LINGUISTIC_ACCURACY)
- **Location**: Line 61 / Section «Презентація: Форми та Енфонія»
- **Original**: «## Презентація: Форми та Енфонія»
- **Problem**: «Енфонія» is not a Ukrainian word. The correct borrowing from Greek εὐφωνία is «евфонія». The content itself uses the correct native equivalent «милозвучність» on line 162. The plan file correctly uses «евфонії» in its section title. This is an LLM hallucination propagated from the meta config.
- **Fix**: Change to «## Презентація: Форми та Евфонія» or «## Презентація: Форми та Милозвучність»

### Issue 2: Activity Euphony Contradiction (ACTIVITY_ERROR)
- **Location**: Activities file line 324 / Mixed Drill item 4
- **Original**: «Я люблю спілкуватися з ____ (студенти).» with answer «студентами»
- **Problem**: The resulting sentence «Я люблю спілкуватися з студентами» violates the euphony rule (ст- cluster requires зі) that this very module teaches in section «Презентація: Форми та Енфонія». The preposition in the sentence should be «зі», not «з».
- **Fix**: Change sentence to «Я люблю спілкуватися зі ____ (студенти).» or replace with a non-cluster word.

### Issue 3: Plural Instrumental Tested But Never Taught (TESTING_BEFORE_TEACHING)
- **Location**: Activities across match-up (line 10), unjumble (line 235), mixed drill (lines 324-326), select (lines 387-396), cloze (lines 434-456)
- **Original**: Items requiring «з друзями», «з батьками», «з хлопцями», «з студентами», «з колегами», «з овочами»
- **Problem**: The content in section «Презентація: Форми та Енфонія» only teaches singular instrumental endings (-ом, -ем, -єм, -ою, -ею, -єю). Plural instrumental endings (-ами/-ями) are never presented, yet 8+ activity items require this knowledge. This violates PPP pedagogy — you cannot test what you haven't presented.
- **Fix**: Either (a) add a brief plural instrumental subsection to the Presentation phase, or (b) remove all plural items from activities and keep them for a later module.

### Issue 4: Scope Creep in Cloze Activity (SCOPE_VIOLATION)
- **Location**: Activities file lines 449, 453 / Cloze items 8-9
- **Original**: Blanks requiring «з овочами» and «з лимоном»
- **Problem**: The module explicitly states on line 26: «У цьому модулі ми працюємо майже виключно з питанням Ким? — люди у вашому житті.» Items about vegetables and lemon are Instrumental of means (Чим?), which is scoped for a2-05.
- **Fix**: Replace with people-focused blanks in the vacation story context.

### Issue 5: Bloated English Paragraph Blocks (LLM_FINGERPRINT)
- **Location**: Lines 68, 89, 111, 162, 193, 213, 243-245, 269, 340, 366, 396 across all sections
- **Original**: 11 English paragraphs averaging 100+ words each, totaling ~1,200 words of padding
- **Problem**: Each paragraph restates what the Ukrainian content already says, using hyperbolic modifiers. Example from line 68: "This is an extremely common pattern because many male names, professions, and family members fall into this category. Mastering this single ending will allow you to form hundreds of useful sentences about the people you interact with daily." This adds no new information beyond the Ukrainian «Це закінчення дуже часто зустрічається» on line 78. The pattern repeats identically in every subsection.
- **Fix**: Cut each English block to 2-3 concise sentences focusing on one key insight not already conveyed in Ukrainian. Remove all hyperbolic qualifiers.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 61 | «Презентація: Форми та Енфонія» | «Презентація: Форми та Евфонія» | Non-existent word |
| Activity line 324 | «спілкуватися з ____ (студенти)» | «спілкуватися зі ____ (студенти)» | Euphony violation |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? **Pass** — Ukrainian examples are clear and approachable. But English padding makes sections dense.
- Instructions clear? **Pass** — Always know what to learn and why. Good rule statements.
- Quick wins? **Borderline Pass** — Section «Презентація: Форми та Енфонія» runs ~1100 words before any practice opportunity. The early examples provide "read-along" wins but no interactivity.
- Ukrainian scary? **Pass** — Introduced gently with English support. Cultural hooks make Ukrainian inviting.
- Come back tomorrow? **Pass** — Content is clearly useful for social interactions. Encouraging closing on line 431: «Вітаємо! Тепер ви вмієте говорити про зв'язки з людьми.»

Emotional beats:
- Welcome/orientation: ✓ «Ласкаво просимо до вивчення сьомого відмінка!» (line 18)
- Curiosity trigger: ✓ Хліб-сіль cultural hook (lines 29-34)
- Quick wins: ✓ Simple examples throughout section «Вступ: Сьомий відмінок і гармонія»
- Encouragement: ✓ «Вітаємо!» closing (line 431)
- Progress marker: ✓ «Тепер ви вмієте говорити про зв'язки з людьми» (line 431) + self-check questions

## Strengths
- **Clear grammar tables**: The summary table in section «Презентація: Форми та Енфонія» (lines 152-156) is clean and visual — exactly what beginners need.
- **Strong cultural integration**: The Хліб-сіль hook in section «Вступ: Сьомий відмінок і гармонія» and friendship hierarchy in section «Практика: Соціальні зв'язки» teach real cultural competence alongside grammar.
- **Excellent dialogue breakdowns**: Both dialogue scenarios in section «Діалоги: Зустрічі та плани» annotate every instrumental form with gender, stem type, and ending — this is A+ pedagogical practice.
- **Good error anticipation**: The warning boxes about missing «з» (lines 50-57) and the error table (lines 420-426) preemptively address common mistakes.
- **Activity variety**: 8 different activity types across 12 activities provides diverse practice modalities.

## Fix Plan to Reach 9.0/10

### Activities: 6/10 → 8/10
**What to fix:**
1. Activity line 324: Change «з ____ (студенти)» → «зі ____ (студенти)» to fix euphony violation
2. Cloze items 8-9 (lines 449, 453): Replace «з овочами» and «з лимоном» with people-focused blanks (e.g., «з офіціантом», «з Оленою»)
3. Remove or simplify all plural instrumental items (match-up line 10, unjumble line 235, mixed drill line 324, select lines 387-396, cloze lines 434-456) — either add a brief plural teaching section or replace with singular items
4. Cloze blank 6: Sentence produces «поруч з Оленою» — either teach «поруч з» in the content or change to «з Оленою» in a different syntactic frame

**Expected score after fix:** 8/10

### LLM Fingerprint: 6/10 → 8/10
**What to fix:**
1. Lines 68, 89, 111, 162, 193, 213, 243-245, 269, 340, 366, 396: Cut each English block to ≤3 sentences. Remove hyperbolic modifiers (extremely, absolutely, completely, incredibly, fundamentally, massively).
2. Vary opening patterns across subsections — not every subsection should start with "In Ukrainian..."
3. Remove the code-switch at end of line 162 where Ukrainian sentence is appended to English paragraph — move to a new paragraph.

**Expected score after fix:** 8/10

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Line 61: Change «Енфонія» → «Евфонія» in the H2 header
2. Update meta file to match

**Expected score after fix:** 9/10

### Language: 7/10 → 8/10
**What to fix:**
1. Fix «Енфонія» (same as linguistic accuracy)
2. Trim hyperbolic English modifiers across all English blocks
3. Make English B1-readable (shorter sentences, fewer subordinate clauses)

**Expected score after fix:** 8/10

### Pedagogy: 7/10 → 8/10
**What to fix:**
1. Add a mini-practice or quick check-in after the first two ending types in section «Презентація: Форми та Енфонія» (before feminine endings)
2. Either add brief plural instrumental teaching or remove plural items from activities
3. Teach «поруч з» in the content or remove from activities

**Expected score after fix:** 8/10

### Educational: 7/10 → 8/10
**What to fix:**
1. Fix «Енфонія» misspelling
2. Break section «Презентація: Форми та Енфонія» with a mini-exercise after masculine endings

**Expected score after fix:** 8/10

### Projected Overall After Fixes
```
(8×1.5 + 8×1.0 + 9×1.0 + 8×1.2 + 8×1.1 + 8×1.2 + 8×1.0 + 8×1.3 +
 8×0.9 + 8×1.3 + 8×1.0 + 9×1.5 + 9×1.5) / 15.5
= (12.0 + 8.0 + 9.0 + 9.6 + 8.8 + 9.6 + 8.0 + 10.4 +
   7.2 + 10.4 + 8.0 + 13.5 + 13.5) / 15.5
= 128.0 / 15.5 = 8.3/10
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (core grammar track — research is brief reference sheet)
- Dates checked: 0 (no dates in content)
- Named figures verified: 0 (no historical figures)
- Primary quotes cross-referenced: 1/1 (State Standard §4.2.2.5.2 — matches research)
- Chronological sequence: N/A
- Claims without research grounding: 0
- Callout box claims verified: 2/2 — Хліб-сіль (bread/salt hospitality matches research line 17), friendship hierarchy (matches research line 18)

## Verification Summary

- Content lines read: 448
- Activity items checked: 95 (across 12 activities)
- Ukrainian sentences verified: 62
- IPA transcriptions checked: 0 (none present in content — acceptable for grammar-focused A2)
- Factual claims verified: 4
- Issues found: 5 (1 linguistic, 1 activity error, 1 scope violation, 1 testing-before-teaching, 1 LLM fingerprint pattern)

## Verdict

**FAIL**

Three auto-fail thresholds breached: Activities (6 < 7) due to euphony contradiction and untaught plural forms; LLM Fingerprint (6 < 7) due to structural monotony and hyperbolic English blocks; Linguistic Accuracy (8 < 9) due to fabricated word «Енфонія» in H2 header. The core grammar teaching is solid and the cultural integration is excellent, but the activity errors (testing untaught material, scope creep into means/tools) and the padded English blocks need significant revision before this module can pass.