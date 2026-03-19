# Рецензія: Genitive Prepositions

**Level:** A1 | **Module:** 32
**Overall Score:** 7.6/10
**Status:** FAIL
**Reviewed:** 2026-03-19
**Reviewed-By:** claude-sonnet-4-6

## Plan Verification

```
Plan-Content Alignment: PARTIAL FAIL
- Sections: All 5 plan sections present as H3 under "Presentation" H2 (В/У + Місцевий, На + Місцевий, Біля/Поруч/Між, Де знаходиться...?, Практика) — COVERED
- Vocabulary: 9/9 required present in prose, 4/4 recommended present — PASS
- Grammar scope: CLEAN — no scope violations detected
- Objectives: All 4 objectives addressed — PASS
- Title/Subtitle mismatch: Subtitle says 「біля, без, від, для, до + родовий відмінок」 but content doesn't cover без, для, or до as standalone prepositions. Only біля/навпроти + Genitive and від in "далеко від" expression. This is a PLAN-level issue — the content faithfully follows the content_outline.
```

### Plan Points Checklist

**Section: В/У + Місцевий (In + Locative)**
- Location inside enclosed spaces (в магазині, у школі, в Україні) → COVERED (lines 125-128)
- Euphonic в/у rule per Pravopys §23 → COVERED (lines 132-136)
- Consonant alternations г→з, к→ц, х→с → COVERED (lines 147-155, table)

**Section: На + Місцевий (On + Locative)**
- Location on surfaces (на столі, на стіні, на підлозі) → COVERED (lines 165-168)
- Events and institutions (на концерті, на роботі, на пошті, на уроці) → COVERED (lines 174-177)
- Contrast pairs (в кімнаті vs на кухні, в театрі vs на виставі) → COVERED (lines 185-187)

**Section: Біля/Поруч/Між (Near/Next to/Between)**
- Біля + Genitive (біля школи, біля парку, біля зупинки) → COVERED (lines 199-202)
- Навпроти + Genitive (навпроти банку, навпроти аптеки) → COVERED (lines 206-208)
- Preview of Instrumental (поруч з, між) → COVERED (lines 214-215)

**Section: Де знаходиться...? (Where is...?)**
- Asking questions (Де знаходиться пошта?) → COVERED (lines 229-231)
- Answering with full sentences → COVERED (lines 237-239)
- Cultural context: Kyiv landmarks (Хрещатик, Майдан, Золоті Ворота) → COVERED (lines 243-251)

**Section: Практика (Practice)**
- Location description drills → COVERED (lines 259-261)
- Dialogues (tourist asking for directions) → COVERED (lines 265-270)

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Good lesson arc (welcome → present → practice → celebrate). Missing preview of learning objectives at start — jumps into "you've learned Genitive case" context without stating "today you'll learn X, Y, Z". Summary section "Підсумок" provides good wrap-up. |
| 2 | Language | 8/10 | <8 | Ukrainian grammar is clean — all Locative forms verified (нозі ✓, руці ✓, вусі ✓). English is clear and warm. One minor issue: 「on the kitchen」 (line 181) — the translation should be "in the kitchen" since that's what English speakers say, even though Ukrainian uses на. |
| 3 | Pedagogy | 8/10 | <7 | PPP structure well-executed. Clear progression from в/у → на → біля/навпроти → full sentences → practice. However, immersion at 13.3% is far below the 30-55% target for module 32 — too much English explanation, not enough Ukrainian reading practice. |
| 4 | Activities | 7/10 | <7 | 4 activity types matching all 4 plan hints. Item counts match (10, 10, 10, 8). However, quiz distractors contain non-existent VESUM forms: 「на ногі」 (line 111) and 「на ноці」 (line 113). These are pedagogically intentional as wrong answers demonstrating incorrect alternations, but should be flagged as "(incorrect form)" to avoid learner confusion. |
| 5 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 4/5 — Overwhelmed: Pass (good pacing, 5-7 words per section). Instructions clear: Pass. Quick wins: Pass (match-up exercise provides easy wins). Ukrainian scary: Pass (well-scaffolded with English). Come back tomorrow: Fail only on engagement variety — only 1 callout box in entire module. |
| 6 | LLM Fingerprint | 8/10 | <7 | Minor concerns: 「flow smoothly like a song」 (line 130) is slightly purple but tolerable. 「They are not just grammar chores; they are the secret to sounding truly authentic and natural」 (line 157) — borderline motivational filler. No structural monotony — sections start differently. Example format varies (bullets, table, blockquote). |
| 7 | Linguistic Accuracy | 9/10 | <9 | All Ukrainian forms verified against VESUM. Euphony rules correctly presented per Pravopys §23. Consonant alternation table accurate (г→з, к→ц, х→с confirmed). Genitive forms correct (школи, парку, магазину, зупинки, банку, аптеки). Only issue: quiz distractors ногі/ноці are invented forms (deliberate). |

**Weighted Overall:** (8×1.5 + 8×1.1 + 8×1.2 + 7×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9 = (12 + 8.8 + 9.6 + 9.1 + 11.7 + 8.0 + 13.5) / 8.9 = 72.7 / 8.9 = **8.2/10**

## Auto-Fail Checklist Results

- Russianisms: CLEAN — no instances of давайте+verb calques, кушати, получати, etc. detected
- Calques: CLEAN
- Colonial framing: CLEAN — no "Unlike Russian" patterns found
- Grammar scope: CLEAN — module stays within A1 scope; Instrumental preview is correctly framed as formulaic chunks
- Activity errors: `ногі` and `ноці` are non-existent VESUM forms in quiz distractors (see Issue 1)
- Beginner safety: 4/5
- Factual accuracy: CLEAN — euphony rules and consonant alternations are accurate; Kyiv landmarks are real

## Critical Issues Found

### Issue 1: Non-existent word forms in quiz distractors (Activity VESUM)
- **Location**: Activities file, lines 111, 113
- **Original**: 「г stays the same (на ногі)」 and 「г changes to к (на ноці)」
- **Problem**: `ногі` and `ноці` are not real Ukrainian word forms (VESUM-verified: NOT FOUND). While these are deliberate wrong answers in a quiz about consonant alternation, presenting non-existent forms to A1 beginners without marking them as incorrect can cause confusion. The audit scanner correctly flags these.
- **Fix**: Add explicit "(incorrect)" or "✗" markers to the distractor text, e.g., "г stays the same (✗на ногі)" — or rewrite the options to describe the alternation without showing the full incorrect form.

### Issue 2: Immersion below target for module position
- **Location**: Entire module (all sections)
- **Problem**: Module 32 should have 30-55% Ukrainian immersion per A1 calibration, but measured immersion is 13.3%. The module is overwhelmingly English prose with only bolded Ukrainian vocabulary and a few example sentences. The practice section "Практика (Practice)" has good Ukrainian passages (lines 261, 265-270), but the Presentation sections are almost entirely English.
- **Fix**: Add Ukrainian Reading Practice blocks after each subsection. For example, after section "В/У + Місцевий", add a 3-5 sentence Ukrainian paragraph with English gloss. After section "На + Місцевий", add a similar block. This would raise immersion to ~25-30%.

### Issue 3: Insufficient engagement elements
- **Location**: Entire module — only 1 `[!tip]` box (lines 138-139)
- **Problem**: Richness audit requires engagement: 2, video_embeds: 2. Module has engagement: 1, video_embeds: 0. The single tip box about в/у meaning the same thing is good but insufficient.
- **Fix**: Add at least 1 more engagement box (e.g., a `[!did-you-know]` about why Kyiv landmarks are important for directions, or a `[!culture-note]` about Ukrainian street naming conventions). Add pronunciation video embeds for key phrases if available.

### Issue 4: Missing learning objectives preview in section "Warm-up"
- **Location**: Section "Warm-up", line 115
- **Original**: 「Welcome back! So far, you have learned how to talk about the absence of things using the Genitive case. Now it is time to step out into the world and learn how to navigate a Ukrainian city.」
- **Problem**: The warm-up provides context but doesn't explicitly state "Today you'll learn: (1) в/у + Locative, (2) на + Locative, (3) біля/навпроти + Genitive, (4) how to ask directions." Beginner calibration requires a PREVIEW element with clear "Today you'll learn..." expectations.
- **Fix**: Add explicit learning objectives after the opening paragraph: "By the end of this module, you will be able to: say where things are using в/у and на, describe relative positions with біля and навпроти, and ask and give directions using Де знаходиться...?"

## D.0 Pre-Screen Disposition

1. **[AGREEMENT_ERROR]** — DISMISSED (false positive). 「біля, без, від, для, до + родовий відмінок」: "родовий" (adj, m) agrees with "відмінок" (noun, m). This is correct Ukrainian grammar.

2. **[PLAN_SECTION_MISSING]** — PARTIALLY DISMISSED. All plan sections exist as H3 subsections under the H2 "Presentation" header. The scanner expected H2-level headings matching plan section names. Content structure uses H2 for lesson phases (Warm-up, Presentation, Практика, Підсумок) and H3 for plan sections — this is an acceptable structural choice, not missing content.

3. **[ACTIVITY_VESUM_FAIL]** — PARTIALLY CONFIRMED. `Львові` is VALID (VESUM confirmed: Locative of Львів). `ногі` and `ноці` are NOT in VESUM — confirmed non-existent forms. However, these are quiz distractors (incorrect answer options), not correct answers. See Issue 1 above.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Activity 111 | 「на ногі」 | на нозі (correct form, but here used as deliberate wrong answer) | Non-existent form |
| Activity 113 | 「на ноці」 | на нозі (correct form, but here used as deliberate wrong answer) | Non-existent form |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? **Pass** — Good pacing, vocabulary introduced in small groups (4-5 per subsection), grammar table is clean
- Instructions clear? **Pass** — Each section clearly explains what follows, English scaffolding is consistent
- Quick wins? **Pass** — Match-up activity provides easy wins, practice dialogue is manageable
- Ukrainian scary? **Pass** — Ukrainian is always bolded and translated, introduced gently
- Come back tomorrow? **Partial Fail** — Module is solid but a bit lecture-heavy in the Presentation section. Only 1 engagement callout. Could use more interactive moments to maintain energy.

## Strengths

- **Excellent grammar accuracy**: All Locative and Genitive forms verified against VESUM. Consonant alternation table (г→з, к→ц, х→с) is accurate and well-presented.
- **Strong pedagogical sequence**: Progressive build from в/у → на → proximity prepositions → full direction sentences → connected practice is textbook PPP.
- **Good practice section**: The neighborhood description (line 261) and tourist dialogue (lines 265-270) are realistic, culturally anchored, and use multiple prepositions naturally. 「Моя хата знаходиться **на вулиці** Франка. Вона **біля парку**. **Навпроти хати** є великий магазин.」 is excellent connected Ukrainian.
- **Cultural integration**: Kyiv landmarks (Хрещатик, Майдан, Золоті Ворота) used naturally as direction reference points — authentic and motivating.
- **Activity quality**: 38 total activity items across 4 types with good coverage of all module topics. Explanations in activities are clear and reinforce the lesson.

## Fix Plan to Reach 9/10 (REQUIRED since score < 9.0)

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Section "Warm-up", line 115: Add explicit "Today you'll learn..." objectives after opening paragraph — sets expectations, provides preview element
2. Section "Підсумок", line 275: Add a "You can now..." validation list instead of burying it in prose

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Line 181: Change "Ukrainians always say **на кухні** (on the kitchen)" → "Ukrainians always say **на кухні** (in the kitchen)" — English translation should match what English speakers actually say

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Add Ukrainian Reading Practice blocks (3-5 sentences each with English gloss) after sections "В/У + Місцевий (In + Locative)" and "На + Місцевий (On + Locative)" to raise immersion from 13.3% toward 25-30%
2. Add at least 1 `[!did-you-know]` or `[!culture-note]` engagement callout

**Expected score after fix:** 9/10

### Activities: 7/10 → 9/10
**What to fix:**
1. Activity lines 111, 113: Either mark non-existent forms with ✗ prefix, or restructure the quiz question to avoid showing full non-existent locative forms (e.g., describe the alternation rule rather than showing the wrong output form)

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 9×1.2 + 9×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.8 + 11.7 + 11.7 + 8.0 + 13.5) / 8.9
= 79.1 / 8.9 = 8.9/10
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (not a seminar track)
- Dates checked: N/A
- Named figures verified: N/A
- Primary quotes cross-referenced: N/A
- Chronological sequence: N/A
- Claims without research grounding: N/A
- Callout boxes checked: 1 (line 138-139, [!tip] about в/у equivalence — factually correct)
- Grammar rules verified: Euphony rules match Pravopys §23 per research notes; consonant alternations correct per VESUM verification
- Cultural claims: Kyiv landmarks (Хрещатик, Майдан, Золоті Ворота) are real and commonly used as reference points — verified

## Verification Summary

- Content lines read: 284
- Activity items checked: 38
- Ukrainian sentences verified: 22
- Citations in bank: 21
- Issues found: 4

## Verdict

**FAIL**

Blocking issues: (1) Immersion at 13.3% is far below the 30-55% target for A1 module 32 — needs Ukrainian reading practice blocks. (2) Only 1 engagement box vs required 2 — needs additional callout. (3) Activity distractors contain non-existent forms flagged by VESUM scanner. The content quality is otherwise strong — grammar is accurate, pedagogy is sound, and the practice section is excellent. Fixes are additive (more Ukrainian blocks, more engagement) rather than rewrites.