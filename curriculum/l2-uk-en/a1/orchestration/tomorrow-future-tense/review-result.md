# Рецензія: Tomorrow - Future Tense

**Level:** A1 | **Module:** 37
**Overall Score:** 7.6/10
**Status:** FAIL
**Reviewed:** 2026-03-19
**Reviewed-By:** claude-sonnet-4-6

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: 4/4 present (Вступ, Презентація граматики, Лексика та культурний контекст, Практика та підсумок)
- Vocabulary: 8/8 required present, 6/6 recommended present
- Grammar scope: PASS
- Objectives: 4/4 COVERED
```

**Plan Adherence Checklist (content_outline.points):**

Section "Вступ (Introduction)":
- "Контраст теперішнього, минулого та майбутнього часу — посилання на модуль A1-21": **COVERED** — Line 3 references present, past (Yesterday module), and future.
- "Культурний контекст оптимізму: розбір фрази «Завтра буде новий день»": **COVERED** — Line 7 presents 「За́втра бу́де нови́й день」 as cultural resilience expression.

Section "Презентація граматики (Grammar Presentation)":
- "Складений майбутній час (буду + інфінітив). Повна таблиця дієвідміни": **COVERED** — Lines 20-27 contain the full conjugation table.
- "Попередження про помилку: Конфлікт видів": **COVERED** — Lines 29-38, with correct/incorrect pair: 「я бу́ду чита́ти」 vs 「я бу́ду прочита́ти」.
- "Синтетичний майбутній час (працюватиму) — ознайомчий огляд (FYI)": **COVERED** — Lines 40-47 provide FYI overview with 「працюва́тиму」 and 「працюва́тимеш」.

Section "Лексика та культурний контекст (Vocabulary and Culture)":
- "Часові маркери майбутнього: завтра, післязавтра, скоро": **COVERED** — Lines 51-57.
- "Конструкція «наступного тижня/року»: вивчення родового відмінка": **COVERED** — Lines 59-69 with Learner Error box and genitive forms.
- "Вираження планів та намірів: різниця між «буду» та «хочу/збираюся»": **COVERED** — Lines 73-88, including the proverb 「Не кажи́ "гоп", по́ки не переско́чиш」.

Section "Практика та підсумок (Practice and Summary)":
- "Відпрацювання розмовних конструкцій: плани на вихідні та вечір": **COVERED** — Lines 92-102.
- "Підсумковий діалог: рольова гра «Організатор подій»": **COVERED** — Lines 104-119 contain a realistic planning dialogue.

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 7/10 | <7 | Decent flow but no callout boxes, no encouragement markers, abrupt ending. Missing WELCOME warmth — no "Привіт!" opening for the learner. |
| 2 | Language | 8/10 | <8 | Stress error on 「те́бе」(line 101) — should be тебе́. Imperative 「кажи́」(line 86) used in proverb context (borderline — proverb is fixed expression, not productive imperative use). English prose is clear and accessible. |
| 3 | Pedagogy | 8/10 | <7 | Good PPP structure, clear grammar table, error warnings. But no discovery exercise despite research notes recommending one. Concepts well-chunked. |
| 4 | Activities | 8/10 | <7 | 7 activities, good variety (fill-in, quiz, match-up, true-false, unjumble, group-sort). Some quiz items test content recall rather than language (proverb meaning question). |
| 5 | Beginner Safety | 7/10 | <7 | "Would I Continue?" 3/5. No warm greeting, no encouragement phrases, no "You can now..." celebration markers. Cold opening — jumps to "Welcome back" without Ukrainian greeting. |
| 6 | LLM Fingerprint | 8/10 | <7 | Italicized headers (*Learner Error Warning*, *FYI*) are non-standard — should be callout boxes. Opening paragraph slightly generic but not egregiously so. No severe LLM clichés. |
| 7 | Linguistic Accuracy | 8/10 | <9 | Stress error on тебе (line 101). Grammar explanations are accurate and verified against Grade 4 textbooks (Захарійчук). Aspect rule correctly stated. |

**Weighted Overall:** (7×1.5 + 8×1.1 + 8×1.2 + 8×1.3 + 7×1.3 + 8×1.0 + 8×1.5) / 8.9 = (10.5 + 8.8 + 9.6 + 10.4 + 9.1 + 8.0 + 12.0) / 8.9 = 68.4 / 8.9 = **7.7/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN] — no Russianisms detected. сподіватися correctly used (not надіятися).
- Calques: [CLEAN] — no English calques detected.
- Colonial framing: [CLEAN] — no Russian-contrast definitions found.
- Grammar scope: [MINOR] — imperative кажи́ appears in proverb (line 86). Imperatives not taught until M47, but this is a fixed proverb expression, not productive grammar. Low risk.
- Activity errors: [CLEAN] — all activities well-formed, answers correct.
- Beginner safety: 3/5
- Factual accuracy: [CLEAN] — compound future formula correct per Grade 4 textbook (Захарійчук). Proverb is authentic and well-known.

## Critical Issues Found

### Issue 1: Stress Error — те́бе → тебе́
- **Location**: Line 101 / Section "Практика та підсумок (Practice and Summary)"
- **Original**: 「Які́ у те́бе пла́ни на ве́чір?」
- **Problem**: Wrong stress placement. VESUM confirms тебе is a form of ти (pronoun, genitive/accusative). The stress falls on the second syllable: тебе́, not те́бе. Pre-screen D.0 correctly flagged this.
- **Fix**: Replace `те́бе` with `тебе́`

### Issue 2: Zero Engagement Boxes
- **Location**: Whole module / All sections
- **Original**: N/A — no `[!tip]`, `[!example]`, `[!cultural-note]`, `[!did-you-know]` callout boxes exist anywhere in the content.
- **Problem**: The module uses italicized headers (*Learner Error Warning: Aspect Conflict*, *FYI: The Synthetic Future*, *Learner Error: "Next" Time Expressions*, *Expressing Intentions and Ukrainian Caution*) instead of proper Markdown callout boxes. These don't render as engagement elements and fail the richness gate. Pre-audit shows 0 engagement boxes (minimum 1 for A1). The richness score is 54% (threshold 60%) with gaps in `engagement: 0/2` and `video_embeds: 0/2`.
- **Fix**: Convert italicized headers to proper callout boxes: `> [!warning]` for learner errors, `> [!tip]` for FYI, `> [!culture]` for the proverb section.

### Issue 3: Missing Warmth Markers — Cold Pedagogy Risk
- **Location**: Lines 1-7 / Section "Вступ (Introduction)" and Lines 90-126 / Section "Практика та підсумок (Practice and Summary)"
- **Original**: The module opens with "Welcome back to your Ukrainian journey!" (no Ukrainian greeting) and ends with "Great job expanding your timeline—the future looks bright!" (single encouragement, no progress celebration list).
- **Problem**: Beginner safety requires ≥3 encouragement phrases, ≥2 "Don't worry" moments, ≥2 "You can now..." validation markers. Module has ~1 encouragement phrase ("Great job" at the very end) and 0 "You can now..." markers. The "Would I Continue?" test fails on quick wins (no practice before line 92) and encouragement (almost none throughout).
- **Fix**: Add "Привіт!" opening, add 2-3 encouragement phrases between sections, convert self-check questions into a "You can now..." celebration list.

### Issue 4: Imperative кажи́ in Proverb (Pre-Screen Confirmation)
- **Location**: Line 86 / Section "Лексика та культурний контекст (Vocabulary and Culture)"
- **Original**: 「Не кажи́ "гоп", по́ки не переско́чиш」
- **Problem**: Pre-screen flagged imperative кажи́ (VESUM: verb:imperf:impr:s:2) — imperatives not taught until M47. However, this is a **fixed proverb expression**, not productive grammar. The learner is not being asked to form imperatives — they're encountering a cultural set phrase. **DISMISS as LOW severity** — the proverb should stay, but add a brief English note that this is a fixed expression.
- **Fix**: Add "(this is a fixed expression — you don't need to learn the verb form yet)" after the translation.

### Issue 5: Immersion Below Target
- **Location**: Whole module
- **Original**: Pre-audit shows 11.0% immersion (target for M37 is 30-55% per A1 band "Modules 21+")
- **Problem**: Module is heavily English-dominant. Ukrainian appears mainly in isolated bold examples and the dialogue block (lines 106-119). The prose sections "Вступ (Introduction)" and "Лексика та культурний контекст (Vocabulary and Culture)" are almost entirely English with Ukrainian words sprinkled in bold.
- **Fix**: Add Ukrainian reading practice blocks after sections "Презентація граматики (Grammar Presentation)" and "Лексика та культурний контекст (Vocabulary and Culture)" — 3-5 Ukrainian sentences each with translations, practicing the буду + infinitive pattern in context.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 101 | 「те́бе」 | тебе́ | Stress error |
| 86 | 「кажи́」(in proverb) | Keep — fixed expression, add English note | Scope (LOW — dismiss) |

## Beginner Safety Audit

"Would I Continue?" Test: 3/5
- Overwhelmed? **Pass** — Pacing is reasonable, concepts introduced 1-2 at a time.
- Instructions clear? **Pass** — Grammar table is clean, error warnings are clear.
- Quick wins? **Fail** — No practice opportunity until Section "Практика та підсумок (Practice and Summary)" (line 90). That's ~1100 words of content before any interactive moment.
- Ukrainian scary? **Pass** — Ukrainian introduced gently with English translations throughout.
- Come back tomorrow? **Fail** — No encouragement phrases, no "don't worry" moments, cold opening without Ukrainian greeting. Module reads like a textbook, not a tutor.

## Strengths
- **Excellent grammar presentation**: The conjugation table (lines 20-27) is clean, visual, and complete. The aspect conflict warning with ✅/❌ pair is exactly right pedagogically.
- **Authentic cultural integration**: The proverb 「Не кажи́ "гоп", по́ки не переско́чиш」 and the distinction between буду (certainty) vs хочу/збираюся (intention) teach real Ukrainian cultural communication patterns.
- **Strong dialogue**: The planning dialogue (lines 106-119) is natural, uses all target structures (буду + infinitive, наступного тижня, збираюся), and models realistic weekend planning conversation.
- **Well-structured activities**: 7 activities with 6 different types cover conjugation drilling, comprehension, and productive ordering.

## Fix Plan to Reach 9/10 (REQUIRED — score is 7.7)

### Experience Quality: 7/10 → 9/10
**What to fix:**
1. Line 1: Add "Привіт! 👋" before the section header or as first line of content — warm Ukrainian greeting.
2. Lines 29, 40, 59, 71: Convert italicized headers to proper callout boxes (`> [!warning]`, `> [!tip]`, `> [!culture]`). This fixes both engagement (0→4) and richness gaps.
3. Line 126: Expand ending into a "You can now..." celebration list with 3-4 specific achievements.
4. Add 2 encouragement phrases between sections (e.g., after the conjugation table: "You've just mastered the full буду conjugation — that's a huge step!")

**Expected score after fix:** 9/10

### Beginner Safety: 7/10 → 9/10
**What to fix:**
1. Add a mini-practice prompt after section "Презентація граматики (Grammar Presentation)" (~line 38) — "Try forming a sentence: Я буду ___. Pick any verb you know!"
2. Add 2 "don't worry" moments — e.g., after aspect warning (line 38): "Don't worry — at this stage, all the verbs we use are imperfective, so this rule is easy to follow."
3. Section "Практика та підсумок (Practice and Summary)": Convert self-check questions into a progress celebration.

**Expected score after fix:** 9/10

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Line 101: Change 「те́бе」 → тебе́.

**Expected score after fix:** 9/10

### LLM Fingerprint: 8/10 → 9/10
**What to fix:**
1. Convert all italicized section sub-headers (*Learner Error Warning*, *FYI*, etc.) to proper callout boxes — removes the non-standard formatting pattern.

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 8×1.1 + 8×1.2 + 8×1.3 + 9×1.3 + 9×1.0 + 9×1.5) / 8.9
= (13.5 + 8.8 + 9.6 + 10.4 + 11.7 + 9.0 + 13.5) / 8.9
= 76.5 / 8.9 = 8.6/10
```

## Verification Summary

- Content lines read: 126
- Activity items checked: 42 (across 7 activities)
- Ukrainian sentences verified: 15
- Citations in bank: 23
- Issues found: 5 (1 dismissed as LOW)

## Verdict

**FAIL**

Blocking issues: (1) Stress error те́бе → тебе́ on line 101 — Linguistic Accuracy auto-fail at <9. (2) Zero engagement boxes — audit gate FAIL for richness (54% < 60% threshold). (3) Beginner Safety at 7/10 — borderline auto-fail, needs warmth injection. The content is pedagogically sound and well-structured, but requires formatting fixes (callout boxes), a stress correction, and warmth additions to pass.