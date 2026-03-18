<!-- content-hash: 8ba79871533b -->
# Рецензія: Stress and Intonation

**Level:** A1 | **Module:** 6
**Overall Score:** 7.2/10
**Status:** FAIL
**Reviewed:** 2026-03-18
**Reviewed-By:** claude-sonnet-4-6

## Plan Verification

```
Plan-Content Alignment: PARTIAL FAIL
- Sections: ALL 6 sections present as H2 headers ✅
- Vocabulary: 7/7 required present in prose, 5/5 recommended present; книжка used but not in vocab file
- Grammar scope: VIOLATION — plan includes verbs (говорю, писати/пишу/пишеш) which violate the M15 verb ban
- Objectives: 4/4 addressed ✅
```

### Plan Points Checklist

**Section "Наголос — Stress" (plan: 350 words)**
- Free/mobile stress concept, contrast with Polish/French: COVERED — 「Ukrainian stress is completely free.」
- Stress changes meaning (замок/мука minimal pairs): COVERED — lines 9-16
- Stress marking in dictionaries (acute accent): COVERED — line 19
- Learner strategy (check stress for new words): COVERED — line 24

**Section "Типові наголоси — Common Stress Patterns" (plan: 250 words)**
- First-syllable stress (мама, тато, хата, кава): COVERED — lines 32-36
- Last-syllable stress (молоко, далеко, говорю): COVERED — lines 44-46, but далеко has WRONG STRESS
- Penultimate stress (школа, книжка, дорога): COVERED — lines 51-53
- No fixed rule (книжка vs вода same ending): COVERED — 「It is highly important to remember that there is no fixed rule tying a specific ending to a specific stress pattern. For example, consider the words «кни́жка» and «вода́».」

**Section "Рухомий наголос — Mobile Stress" (plan: 250 words)**
- Stress shifts in declension (рука→руки): COVERED — lines 67-70
- Stress shifts in conjugation (писати→пишу→пишеш): COVERED — lines 78-80
- Preview note (awareness goal): COVERED — 「Please treat this mobile stress information as a preview note.」
- Practical tip (listening): COVERED — 「Your brain is wired to pick up on these musical shifts naturally over time」

**Section "Інтонація — Intonation" (plan: 250 words)**
- Declarative intonation (falling pitch): COVERED — lines 93-96
- Interrogative with question word: COVERED — lines 98-101
- Yes/no questions (IK-3 pattern): COVERED — 「This is known as the IK-3 pattern.」
- Exclamatory intonation: COVERED — lines 108-111
- Contrast drill: COVERED — lines 113-119

**Section "Практика — Practice" (plan: 100 words)**
- Stress placement drills: COVERED — lines 127-131
- Minimal pairs practice: COVERED — lines 133-137
- Intonation reading exercises: COVERED — lines 139-143

**Section "Підсумок — Summary" (plan: 100 words)**
- Recap of key concepts: COVERED — line 147
- Self-check questions: COVERED — lines 149-152
- Next module preview: COVERED — 「Next up in Module 7, you will dive directly into greetings and basic conversational phrases!」

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Warm opening with 「Привіт!」, good pacing, but lacks tables and visual variety — mostly prose + bullet lists |
| 2 | Language | 7/10 | <8 | Wrong stress on 「далеко́」 (should be дале́ко); IK-3 is Russian linguistic terminology |
| 3 | Pedagogy | 8/10 | <7 | Good PPP structure, preview framing for mobile stress, but no cultural callouts and vocabulary word книжка missing from vocab file |
| 4 | Activities | 6/10 | <7 | VESUM-invalid distractors (школ, ка); all 4 activity types are pure knowledge recall; monotonous quiz with 12 identical-format items |
| 5 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 4/5 — warm, encouraging, not overwhelming, but verb forms appear before M15 which may confuse |
| 6 | LLM Fingerprint | 7/10 | <7 | 「These minimal pairs perfectly demonstrate the functional load of stress in the Ukrainian language.」 — academic register inappropriate for A1 tutor; structural monotony in example presentation |
| 7 | Linguistic Accuracy | 7/10 | <9 | Wrong stress далеко́→дале́ко; verbs violate M15 gate; план itself contradicts verb ban |

**Weighted Overall:** (8×1.5 + 7×1.1 + 8×1.2 + 6×1.3 + 8×1.3 + 7×1.0 + 7×1.5) / 8.9 = (12 + 7.7 + 9.6 + 7.8 + 10.4 + 7.0 + 10.5) / 8.9 = 65.0 / 8.9 = **7.3/10**

## Auto-Fail Checklist Results

- Russianisms: CLEAN — no Russian ghost words detected
- Calques: CLEAN
- Colonial framing: FLAG — "IK-3 pattern" (line 103) is Russian intonology terminology (Bryzgunova's system). Not auto-fail but should be replaced with a descriptive term or explained without the Russian label.
- Grammar scope: VIOLATION — verbs говорю́, писа́ти, пишу́, пи́шеш appear at lines 46, 78-80 in pre-verb module M6. However, the PLAN itself includes these. This is a plan-level conflict requiring escalation.
- Activity errors: FAIL — `школ` and `ка` are VESUM-invalid distractors in fill-in activity
- Beginner safety: 4/5
- Factual accuracy: Wrong stress on далеко́ (should be дале́ко). Plan content_outline also says "далекО" but plan vocabulary_hints says "дале́ко" — internal plan contradiction.

## Critical Issues Found

### Issue 1: Wrong Stress — далеко́ (HIGH)
- **Location**: Line 45 / Section "Типові наголоси — Common Stress Patterns"
- **Original**: 「далеко́」
- **Problem**: Standard Ukrainian stress is дале́ко (penultimate), not далеко́ (final). Confirmed by pre-screen STRESS_MISMATCH. The plan's own vocabulary_hints says "дале́ко" but the content_outline incorrectly says "далекО." The content followed the wrong part of the plan.
- **Fix**: Replace `далеко́` with `дале́ко` in content (line 45) and activity explanation (line 72).

### Issue 2: VESUM-Invalid Activity Distractors (HIGH)
- **Location**: Activities file, lines 197, 200, 206, 209, 212, 214
- **Original**: Distractors `школ`, `кав`, `хат`, `тат`, `мам`, `вод` — truncated stems used as wrong options
- **Problem**: `школ` and `ка` confirmed NOT FOUND in VESUM. These truncated forms are not valid Ukrainian words. Students practicing with non-existent word forms is harmful.
- **Fix**: Replace truncated-stem distractors with real Ukrainian words that have different stress patterns or are plausible wrong answers.

### Issue 3: Verbs in Pre-Verb Module (HIGH — Plan Escalation)
- **Location**: Lines 46, 78-80 / Sections "Типові наголоси — Common Stress Patterns" and "Рухомий наголос — Mobile Stress"
- **Original**: 「говорю́」, 「писа́ти」, 「пишу́」, 「пи́шеш」
- **Problem**: M6 is pre-verb (verbs forbidden before M15). The morphological validator correctly flags these. However, the PLAN explicitly includes these verbs as stress examples. The research notes also warn: "NO conjugated verb forms." This is a plan-level contradiction that needs resolution — either the plan needs a version bump to remove verbs, or the verb ban needs a scoped exception for stress demonstration.
- **Fix**: ESCALATE to user. Cannot fix content without plan decision. Recommendation: replace verb examples with noun examples showing similar stress patterns (e.g., молоко́, далеко should suffice for last-syllable; use noun declension pairs for mobile stress that don't require verb knowledge).

### Issue 4: Missing Richness Elements (MEDIUM)
- **Location**: Entire module
- **Problem**: Richness at 73% (threshold 95%). Missing: cultural callouts (0/3 needed), tables (0/2), proverbs (0/1), engagement boxes (2/5). The module has zero `[!culture]`, `[!did-you-know]`, or `[!fun-fact]` callouts. No comparison tables for stress patterns.
- **Fix**: Add (a) stress pattern summary table in section "Типові наголоси — Common Stress Patterns", (b) `[!did-you-know]` about Ukrainian castles (замки) connecting замок to geography, (c) `[!culture]` about Ukrainian being melodic, (d) one proverb or textbook poem reference (research notes mention Vashulenko p.69 poem "Наголос — то зовсім не дрібниця").

### Issue 5: Low Immersion (MEDIUM)
- **Location**: Entire module
- **Problem**: Immersion at 4.6%, target for M6-10 is 15-35%. The module is overwhelmingly English prose with Ukrainian examples only as isolated vocabulary items. The mini-dialogues (lines 38-40, 55-57, 72-74) are good but too few.
- **Fix**: Add more Ukrainian mini-dialogues after each stress pattern group. Expand blockquote dialogue contexts. Add Ukrainian labels to tables.

### Issue 6: IK-3 Russian Terminology (LOW)
- **Location**: Line 103 / Section "Інтонація — Intonation"
- **Original**: 「This is known as the IK-3 pattern.」
- **Problem**: IK-3 (интонационная конструкция-3) is Bryzgunova's Russian intonology system. While widely used in L2 teaching, it frames Ukrainian intonation through Russian linguistics. A Ukrainian-centered approach would describe the pattern without the Russian label.
- **Fix**: Replace "This is known as the IK-3 pattern" with a descriptive phrase like "This distinctive rise-fall pattern on the key word is characteristic of Ukrainian yes/no questions."

### Issue 7: Academic Register for A1 (LOW)
- **Location**: Line 17 / Section "Наголос — Stress"
- **Original**: 「These minimal pairs perfectly demonstrate the functional load of stress in the Ukrainian language.」
- **Problem**: "Functional load" is a phonology term inappropriate for A1 beginners. A warm tutor voice wouldn't use this.
- **Fix**: Rewrite as "These word pairs show just how important stress is in Ukrainian — one shift changes everything!"

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 45 | 「далеко́」 | дале́ко | Stress error |
| 103 | IK-3 | (remove Russian label) | Colonial terminology |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? **Pass** — pacing is comfortable, mobile stress framed as preview
- Instructions clear? **Pass** — always clear what to do
- Quick wins? **Pass** — early examples are manageable, mini-dialogues help
- Ukrainian scary? **Pass** — gentle introduction, English scaffolding throughout
- Come back tomorrow? **Borderline Pass** — encouraging tone, but verb conjugation examples in M6 might intimidate; 「Please treat this mobile stress information as a preview note」 helps but the verbs still appear

## Strengths
- Warm, welcoming opening with 「Привіт! Welcome to the sixth module.」 sets the right tone
- Excellent use of mini-dialogues in blockquotes for contextualized examples (lines 38-40, 55-57, 72-74, 95-96, 100-101, 105-106, 110-111)
- Strong contrast drill (lines 116-119) teaching all four intonation patterns on one sentence — mirrors textbook pedagogy
- Appropriate preview framing for mobile stress — 「For now, basic awareness is your only goal. You are doing fantastic」
- Closing with progress celebration and M7 preview: 「Next up in Module 7, you will dive directly into greetings and basic conversational phrases!」
- Good stress minimal pairs (замок/замок, мука/мука) — high pedagogical value

## Fix Plan to Reach 9/10 (REQUIRED — score is 7.3)

### Linguistic Accuracy: 7/10 → 9/10
**What to fix:**
1. Line 45: Change 「далеко́」 → `дале́ко` — wrong stress
2. Lines 46, 78-80: ESCALATE verb issue to user — plan needs version bump to remove verbs OR verb ban needs exception. Cannot fix without decision.
3. Activity file line 72: Update далеко explanation to match corrected stress

**Expected score after fix:** 9/10 (after plan escalation resolves verbs)

### Activities: 6/10 → 8/10
**What to fix:**
1. Replace VESUM-invalid distractors (школ, ка, кав, хат, тат, мам, вод) with real Ukrainian words
2. Add variety — the quiz has 12 items all with identical 4-option format. Consider splitting into two smaller quizzes or varying question formats.

**Expected score after fix:** 8/10

### Language: 7/10 → 9/10
**What to fix:**
1. Line 45: Fix далеко stress
2. Line 103: Remove IK-3 label, use descriptive term
3. Line 17: Replace "functional load" with accessible language

**Expected score after fix:** 9/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Add stress pattern summary table in section "Типові наголоси — Common Stress Patterns"
2. Add `[!did-you-know]` callout about Ukrainian castles (замки) connecting замок to geography
3. Add `[!culture]` callout about Ukrainian language's melodic nature

**Expected score after fix:** 9/10

### LLM Fingerprint: 7/10 → 8/10
**What to fix:**
1. Line 17: Rewrite "functional load" sentence in tutor voice
2. Vary example presentation formats — currently all sections use identical `* **word** (translation)` bullet lists

**Expected score after fix:** 8/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 9×1.2 + 8×1.3 + 8×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.8 + 10.4 + 10.4 + 8.0 + 13.5) / 8.9
= 76.5 / 8.9 = 8.6/10
```

## Verification Summary

- Content lines read: 154
- Activity items checked: 38 (12 quiz + 8 match-up + 8 true-false + 10 fill-in)
- Ukrainian sentences verified: 14
- Citations in bank: 17
- Issues found: 7

## Verdict

**FAIL**

Blocking issues: (1) Wrong stress on далеко́ → дале́ко, (2) VESUM-invalid activity distractors (школ, ка), (3) Verbs in pre-verb module M6 — plan-level conflict requiring escalation before content can be fixed. The module has solid pedagogy and warm tone, but linguistic accuracy failures and activity errors prevent passing.