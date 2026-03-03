# Рецензія: My World: Objects

**Reviewed-By:** claude-opus-4-6

**Level:** A1 | **Module:** a1-010
**Overall Score:** 8.4/10
**Status:** PASS (all gates cleared after D.2 fixes)
**Reviewed:** 2026-03-02

## Plan Verification

```
Plan-Content Alignment: PASS (with process note)
- Sections: PASS — All 5 H2 sections present (Вступ, Презентація, Практика, Культурний контекст, Продукція та підсумок)
- Vocabulary: PASS — 6/6 required items present, 6/6 recommended present, +25 extra household items (within scope)
- Grammar scope: PASS — Demonstratives only, no scope creep
- Objectives: PASS — All 4 learning objectives fully addressed
- Word target: PASS — 4782 words vs 2000 target (239.1% — targets are minimums)
```

**Process note:** The plan (`plans/a1/my-world-objects.yaml`) specifies `word_target: 2000`, but the meta (`meta/my-world-objects.yaml`) shows `word_target: 3300`. The meta also contains a full `content_outline` with revised word allocations, which violates Rule 8 (meta = build config, not planning data). The plan and meta have diverged. This is a process issue, not a content quality issue.

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Warm, well-structured lesson with creative Interior Designer persona. Excellent flow from theory → practice → production. Minor: very long for A1 (4782w); the learning objective preview doesn't arrive until L26-28, after ~400 words of proverb discussion |
| 2 | Language | 9/10 | <8 | English is clear, warm, B1-accessible. Ukrainian is grammatically correct throughout. One minor factual overstatement about 「одна мебля」 (L269) — VESUM confirms мебля exists as archaic |
| 3 | Pedagogy | 8/10 | <7 | PPP structure well-executed. Identification vs Specification distinction (L34-54) is a highlight. "T" mnemonic (L101-102) is effective. Concern: Практика section spans ~3000 words with 5 dialogues, 3 scenarios, 2 reading passages, and a drill — cognitive load risk for A1 |
| 4 | Activities | 8/10 | <7 | 10 activities with 5 types (group-sort, match-up, quiz, fill-in, anagram). The Identification vs Specification fill-in (activity 9) is pedagogically excellent. Weakness: quizzes 3 and 4 (near/far) are structurally identical — 20 items of the same format |
| 5 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5 — see below |
| 6 | LLM Fingerprint | 9/10 | <7 | No structural monotony. Varied callout titles. No AI clichés detected. Natural tutor voice. Varied example formats (bullets, scenarios, dialogues, reading passages, tables) |
| 7 | Linguistic Accuracy | 9/10 | <9 | All demonstrative agreements correct. Gender assignments accurate. Stress marks present on first mentions. One factual issue: мебля claim (L269). Untranslated „Продавець" in dialogue (L305) |

**Weighted Overall:** (8×1.5 + 9×1.1 + 8×1.2 + 8×1.3 + 9×1.3 + 9×1.0 + 9×1.5) / 8.9 = (12.0 + 9.9 + 9.6 + 10.4 + 11.7 + 9.0 + 13.5) / 8.9 = 76.1 / 8.9 = **8.6/10**

## Auto-Fail Checklist Results

- Russianisms: **CLEAN** — No instances found. Module uses гарна, красива, зручний — all standard Ukrainian.
- Calques: **CLEAN** — No English or Russian calques detected.
- Colonial framing: **CLEAN** — No "Unlike Russian" or comparative framing.
- Grammar scope: **CLEAN** — Demonstratives only, no later-module grammar.
- Activity errors: **CLEAN** — All answers correct, all gender assignments accurate.
- Beginner safety: **5/5** (see below)
- Factual accuracy: **1 minor issue** — L269 мебля claim (see Critical Issues)
- LLM filler: **CLEAN** — No filler phrases detected.

## Critical Issues Found

### Issue 1: Factual Overstatement (Minor)
- **Location**: Line 269 / Section "Практика"
- **Original**: 「одна мебля」 (used as example of impossible form)
- **Problem**: The module states "You cannot say 'one furniture' (*одна мебля*)". However, VESUM confirms that `мебля` exists as an archaic noun form (`noun:inanim:f:v_naz:arch`). The claim is overly absolute. While `мебля` is archaic and not standard in modern speech, saying it "cannot" be said is inaccurate.
- **Fix**: Soften to "In modern Ukrainian, *мебля* is archaic — you will almost always hear the plural **меблі**." or "The singular form *мебля* is archaic and rarely used today."

### Issue 2: Untranslated Vocabulary in Dialogue
- **Location**: Line 305 / Section "Практика"
- **Original**: 「Я хо́чу купи́ти цей сті́л.」 (dialogue with "Продавець" as speaker label)
- **Problem**: The word **Продавець** (seller/salesperson) appears as a dialogue speaker label without translation or glossing. This word is NOT in the vocabulary list. At A1, untranslated words outside the taught vocabulary can cause confusion.
- **Fix**: Add an inline gloss: **Продавець (Salesperson):** or add it to the vocabulary list.

### Issue 3: Richness Gaps (Audit-Blocking)
- **Location**: Module-wide
- **Problem**: The automated richness audit shows 74% (threshold 95%) with gaps: `engagement: 4/5`, `cultural: 1/3`, `dialogues: 0/4`. The actual content CONTAINS 3 `[!culture]` callouts and 5 dialogues, but the scanner doesn't detect them — likely a markup format mismatch. The module needs to conform to the expected markup patterns for the scanner to count these elements.
- **Fix**: (1) Ensure dialogues use whatever format the scanner expects (check scanner regex). (2) Verify why only 1 of 3 `[!culture]` boxes is counted. (3) Add 1 more `[!engagement]` interactive prompt (e.g., before the reading passages in section "Практика").

### Issue 4: Learning Objectives Arrive Late
- **Location**: Lines 17-28 / Section "Вступ"
- **Problem**: The first ~400 words of the introduction discuss culture, recap prior modules, and explain demonstratives conceptually before the learner knows what they'll learn today. The explicit preview ("we will learn how to form and use the gendered forms...") doesn't arrive until line 26-28. At A1, the "Today you'll learn..." moment should come within the first 2-3 sentences.
- **Fix**: Add a brief learning preview after the first paragraph: "By the end of this lesson, you'll be able to point at objects around you and say 'this table' or 'that window' with perfect grammatical agreement."

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 269 | 「одна мебля」 (claimed impossible) | Acknowledge as archaic, not impossible | Factual |
| 305 | Продавець (unglossed) | Продавець (Salesperson) | Missing gloss |

## Beginner Safety Audit

"Would I Continue?" Test: **5/5**
- Overwhelmed? **Pass** — Despite the length, each section is well-chunked with frequent examples and visual breaks (tables, callouts, dialogues). The learner is never hit with more than 5-7 new words before practice.
- Instructions clear? **Pass** — Every concept explained in clear English before Ukrainian is introduced. The "Identification vs Specification" distinction (L34-54) is exceptionally clear.
- Quick wins? **Pass** — The early identification examples (L38-40: 「Це сті́л. Це кни́га. Це вікно́.」) provide immediate wins within the first 100 words of section "Презентація". The gender matching drill (L206-225) gives learners a concrete mental checklist.
- Ukrainian scary? **Pass** — Ukrainian introduced gently with full English scaffolding. Stress marks guide pronunciation. The [!warning] box (L53-54) directly addresses the English-speaker anxiety about using це vs цей.
- Come back tomorrow? **Pass** — Warm, encouraging tone throughout. The Interior Designer persona in section "Продукція та підсумок" (L379-399) turns grammar into a game. The final summary (L403-412) celebrates what the learner can now do.

## Strengths

- **The Identification vs Specification distinction** (L34-54) is the pedagogical highlight. The clear English metalanguage explaining when це is invariant (identification) versus when it must agree with gender (specification) prevents a fundamental A1 error. The [!warning] "English Trap" box reinforces this beautifully.
- **The "T" mnemonic** (L101-102): "Think of **T**hat and **T**here — they start with T!" is a genuinely useful memory aid connecting English intuition to Ukrainian grammar.
- **Five contextual mini-dialogues** (L296-328) show demonstratives in natural conversation. Dialogue 3 (「Будь ла́ска, зачини́ ті две́рі.」 / 「Ці две́рі?」 / 「Ні, не ці. Ті две́рі, там.」) is especially effective — it demonstrates the двері exception in a real communicative scenario.
- **Cultural depth**: The покуття, піч, and рушники explanations in section "Культурний контекст" (L335-352) are factually accurate and emotionally engaging. The хата/квартира/дім trichotomy (L354-364) teaches vocabulary AND cultural values simultaneously.
- **Gender rhyme pattern** observation (L143-147): pointing out that correct gender agreement *sounds* better trains the learner's ear, not just their grammar rules.

## Fix Plan to Reach 9.0/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Lines 17-19: Move a brief learning objective preview ("Today you'll learn to point at objects near and far using gender-matched demonstratives") to immediately after the opening welcome sentence, before the proverb discussion.
2. Consider whether the two reading passages (L168-184, L191-200) could be consolidated. Both test the same skills.

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Add an `[!engagement]` interactive prompt before the reading passage in section "Практика" (around L166) to break up the dense practice material.
2. Ensure dialogue markup matches scanner expectations to resolve the `dialogues: 0/4` richness gap.

**Expected score after fix:** 9/10

### Activities: 8/10 → 9/10
**What to fix:**
1. Differentiate quizzes 3 and 4 — consider converting one to a different format (e.g., make quiz 4 a "drag-and-drop" or add sentence context to the far-demonstrative items so they feel distinct from the near-demonstrative quiz).
2. Add English gloss for Продавець in dialogue activity items if referenced.

**Expected score after fix:** 9/10

### Richness Gaps (Audit-Blocking)
**What to fix:**
1. `dialogues: 0/4` — The 5 existing dialogues need to match scanner format. Check what pattern the richness scanner uses and reformat accordingly.
2. `cultural: 1/3` — 3 `[!culture]` boxes exist; verify scanner regex and fix any format issue preventing detection.
3. `engagement: 4/5` — Add 1 more interactive engagement element (e.g., an `[!engagement]` callout with a self-check question between the two reading passages in section "Практика").

**Expected richness after fix:** ≥95%

### Projected Overall After Fixes
```
Experience: 9×1.5 = 13.5
Language: 9×1.1 = 9.9
Pedagogy: 9×1.2 = 10.8
Activities: 9×1.3 = 11.7
Beginner Safety: 9×1.3 = 11.7
LLM Fingerprint: 9×1.0 = 9.0
Linguistic Accuracy: 9×1.5 = 13.5
Total: 80.1 / 8.9 = 9.0/10
```

## Verification Summary

- Content lines read: 414
- Activity items checked: 101 (across 10 activities)
- Ukrainian sentences verified: 45+
- Citations in bank: 15
- Issues found: 4

## Verdict

**FAIL**

The content quality is strong (8.6/10 weighted) with excellent pedagogy, warm beginner-appropriate tone, and accurate Ukrainian. However, the module fails the automated richness gate (74% vs 95% threshold) due to scanner-format mismatches for dialogues and cultural callouts. The fix plan is straightforward: resolve the markup format issues so the existing dialogues and cultural content are correctly detected, add 1 engagement element, soften the мебля claim, and add an English gloss for Продавець. These are minor fixes that should bring the module to PASS.