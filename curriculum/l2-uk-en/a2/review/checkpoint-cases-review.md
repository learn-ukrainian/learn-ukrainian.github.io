<!-- content-hash: 8039581d96e6 -->
# Рецензія: Checkpoint — Cases

**Level:** A2 | **Module:** a2-11
**Overall Score:** 7.9/10
**Status:** FAIL
**Reviewed:** 2026-02-28
**Reviewed-By:** claude-opus-4-6

## Plan Verification

```
Plan-Content Alignment: PASS (minor deviations)
- Sections: 5/5 present. Section 2 has extra "Навичка 1:" prefix not in plan.
- Vocabulary: 25/25 required items present. All plan-required vocabulary hints covered.
- Grammar scope: CLEAN — no scope creep beyond case system review.
- Objectives: All 4 objectives addressed (identify cases, choose prepositions, correct errors, apply in context).
- Activity hints: fill-in has 12 items vs plan's 15+ (shortfall of 3).
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Well-structured checkpoint with clear progression through all 7 cases; practical dialogues in section "Сервіси та цифрова Україна" are engaging. However, section "Огляд та самооцінка" is lecture-heavy with no inline practice for ~600 words. |
| 2 | Language | 8/10 | <8 | One grammar error on line 149: 「Це історична подія сталася **десятого березня**」— "Це" must be "Ця" (feminine agreement with "подія"). Unnatural collocation on line 158: 「Він щойно приїхав **з великого Києва**」— the adjective "великого" before a proper noun is unusual in this context. |
| 3 | Pedagogy | 8/10 | <7 | TTT structure solid: self-assessment (Test) → case review (Teach) → activities (Test). Error correction pedagogy is excellent (line 132 warning box, line 170 negation drill). Table on line 197 (Acc vs. Loc comparison) is outstanding. Missing inline mini-exercises between theory sections. |
| 4 | Activities | 8/10 | <7 | 12 activity blocks with excellent variety (quiz, match-up, fill-in, error-correction, unjumble, group-sort, true-false, select, translate, cloze). Error-correction catches real Russianisms (кушати, із-за). Fill-in has 12 items vs plan's 15+ requirement. |
| 5 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 4/5. Dense English theory in sections "Огляд та самооцінка" and "Граматичні тонкощі: Родовий, Знахідний та Кличний" could overwhelm. No inline practice until YAML activities. Quick wins present in self-assessment checklist. |
| 6 | LLM Fingerprint | 7/10 | <7 | 「In this section, we will explore the cases that handle more abstract, yet highly frequent concepts」(line 140) — generic AI transition. 「magnificent hallmark」(line 211) — inflated language. 「fundamental engine that drives the language」(line 18) — abstract grand statement. Uniform example formatting (bullet `*` + bold case ending + English gloss) across all 5 case subsections creates structural monotony. |
| 7 | Linguistic Accuracy | 8/10 | <9 | **AUTO-FAIL.** Grammar error on line 149: "Це" must be "Ця" (demonstrative pronoun must agree with feminine "подія"). Semantically absurd example on line 313: 「Новий капелюх лежить на **браті**」— a hat resting "on a brother" is bizarre; should be "на столі" or "на поличці". English translation gap on line 160: "for brother" missing article. |

**Weighted Overall:** (8×1.5 + 8×1.1 + 8×1.2 + 8×1.3 + 8×1.3 + 7×1.0 + 8×1.5) / 8.9 = (12.0 + 8.8 + 9.6 + 10.4 + 10.4 + 7.0 + 12.0) / 8.9 = 70.2 / 8.9 = **7.9/10**

## Auto-Fail Checklist Results

- Russianisms: CLEAN in prose. Activities correctly identify "кушати" and "із-за" as errors to correct (pedagogically appropriate).
- Calques: CLEAN — no calques detected in prose.
- Colonial framing: CLEAN. The Vocative culture note (line 214) discusses colonial-era suppression of the Vocative case, which is legitimate decolonization framing, not colonial framing.
- Grammar scope: CLEAN — stays within case system review.
- Activity errors: CLEAN — all correct answers verified, all distractors plausible.
- Beginner safety: 4/5
- Factual accuracy: The 1918 UNR stamps ("шаги") narrative matches research notes. Heorhiy Narbut attribution confirmed. Diia app cultural hook is factually accurate.

## Critical Issues Found

### Issue 1: Grammar Error — Demonstrative Pronoun Agreement
- **Location**: Line 149 / Section "Граматичні тонкощі: Родовий, Знахідний та Кличний"
- **Original**: 「Це історична подія сталася **десятого березня**.」
- **Problem**: "Це" is neuter nominative. The noun "подія" is feminine, requiring the feminine demonstrative "Ця." This error appears in a sentence specifically teaching Genitive case usage for dates — a grammar error in a grammar-teaching example severely undermines credibility.
- **Fix**: Change "Це" to "Ця": "Ця історична подія сталася десятого березня."

### Issue 2: Semantically Absurd Example in Summary Matrix
- **Location**: Line 313 / Section "Історичний виклик та підсумок"
- **Original**: 「Новий капелюх лежить на **браті**.」
- **Problem**: A hat lying "on a brother" is semantically bizarre and would never appear in natural speech. This is clearly an AI-generated example forced to fit the "брат" paradigm across all 7 cases. The Locative example should use a realistic location.
- **Fix**: Replace with "Мій брат живе **у великому місті**." or keep the "брат" paradigm with "Книга лежить на **столі**." with the paradigm shifted to "стіл" for the Locative row.

### Issue 3: Immersion Far Below Target (21.6% vs 50-60%)
- **Location**: Entire module, all sections
- **Problem**: The audit reports 21.6% Ukrainian immersion against a Band 1 target of 50-60%. The module is overwhelmingly English prose with Ukrainian appearing only in example sentences and dialogues. Sections "Огляд та самооцінка" and "Граматичні тонкощі: Родовий, Знахідний та Кличний" are especially English-heavy.
- **Fix**: This requires a significant rewrite. Strategy: (1) Add Ukrainian introductory sentences at the start of each subsection before English explanation, (2) Present grammar tables with Ukrainian headers and descriptions, (3) Add Ukrainian transitional prose between example blocks, (4) Expand the Ukrainian dialogue sections in "Сервіси та цифрова Україна", (5) Add a short Ukrainian reading passage in "Огляд та самооцінка".

### Issue 4: Unnatural Collocation
- **Location**: Line 158 / Section "Граматичні тонкощі: Родовий, Знахідний та Кличний"
- **Original**: 「Він щойно приїхав **з великого Києва**.」
- **Problem**: Adding "великого" before "Києва" in this sentence is unnatural. A native speaker would say "з Києва" without the adjective. The adjective appears to be inserted to demonstrate Genitive case agreement, but it produces an unnatural sentence. "Великий Київ" is a valid collocation in certain contexts (e.g., historical/poetic) but not for a casual arrival statement.
- **Fix**: Either remove the adjective: "Він щойно приїхав з Києва." — or use a different adjective-noun combination that demonstrates Genitive agreement naturally: "Він щойно приїхав з великого міста." (from a big city).

### Issue 5: English Translation Error
- **Location**: Line 160 / Section "Граматичні тонкощі: Родовий, Знахідний та Кличний"
- **Original**: 「Цей смачний торт приготували **для брата**. (This delicious cake was prepared for brother.)」
- **Problem**: The English "for brother" is missing the article — should be "for the/a brother" or "for [the] brother."
- **Fix**: Change translation to "(This delicious cake was prepared for the brother.)"

### Issue 6: LLM Fingerprint — Inflated Language and Structural Monotony
- **Location**: Lines 18, 140, 211 across multiple sections
- **Problem**: Phrases like 「magnificent hallmark」(line 211), 「fundamental engine that drives the language」(line 18), and 「In this section, we will explore」(line 140) are recognizable LLM writing patterns. Additionally, all case subsections use identical bullet-list formatting for examples, creating visual monotony.
- **Fix**: (1) Replace "magnificent hallmark" → "a distinctive feature" or "one of the defining features"; (2) Replace "fundamental engine" → "the mechanism" or "the system"; (3) Replace "In this section, we will explore" → "Now let's focus on" or start with a Ukrainian sentence; (4) Vary example presentation — use a dialogue for one case, a table for another, inline examples for a third.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 149 | 「Це історична подія сталася」 | 「Ця історична подія сталася」 | Grammar (demonstrative pronoun agreement) |
| 158 | 「з великого Києва」 | 「з Києва」 or 「з великого міста」 | Naturalness (unnatural collocation) |
| 160 | "for brother" | "for the brother" | English translation |
| 313 | 「Новий капелюх лежить на **браті**」 | 「Мій брат живе у великому **місті**」 | Semantics (absurd example) |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? **Borderline Pass** — Covering all 7 cases is ambitious; the preposition table (line 44) and Acc/Loc table (line 197) are dense but well-structured. Some theory sections run 400+ words without practice.
- Instructions clear? **Pass** — Learning objectives clearly stated in English checklist (line 27). Each case section has clear H3 structure.
- Quick wins? **Pass** — Self-assessment checklist provides orientation; error correction warning boxes (lines 131-133, 169-171) are satisfying "aha" moments.
- Ukrainian scary? **Pass** — Heavy English scaffolding ensures Ukrainian is never unsupported. However, the immersion is actually too LOW (21.6%), meaning learners don't get enough Ukrainian exposure.
- Come back tomorrow? **Pass** — Module feels achievable; the dialogues and historical story provide interest hooks.

## Strengths
- Comprehensive case review covering all 7 cases with clear, correct paradigm examples across Dative, Instrumental, Genitive, Accusative/Locative, and Vocative.
- Excellent error-correction pedagogy: the warning boxes contrasting ❌/✅ forms (lines 131-133 for Instrumental, 169-171 for Genitive negation) mirror real learner errors from research.
- The Accusative vs. Locative comparison table (line 197) is an outstanding pedagogical tool — clear, visual, and directly addresses a documented learner confusion point.
- The dialogues in section "Сервіси та цифрова Україна" (post office lines 243-254, bank lines 261-273) are realistic, well-integrated, and demonstrate multiple cases in natural context.
- Activity variety is exceptional: 12 types including error-correction that catches genuine Russianisms (кушати→їсти, із-за→через).
- Historical hook about 1918 UNR stamps (section "Історичний виклик та підсумок") is factually grounded, culturally relevant, and linguistically rich.

## Fix Plan to Reach 9.0/10 (REQUIRED — score < 9.0)

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Line 149: Change 「Це історична подія сталася」→ 「Ця історична подія сталася」— fix demonstrative pronoun agreement.
2. Line 313: Replace 「Новий капелюх лежить на **браті**」→ use a natural Locative example like "Він зараз живе у великому **місті**." or change the paradigm word for the Locative row.
3. Line 158: Remove unnatural adjective: 「з великого Києва」→ 「з Києва」or replace with 「з великого міста」.
4. Line 160: Fix English translation: "for brother" → "for the brother."

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Fix the grammar error and unnatural collocations listed under Linguistic Accuracy (they overlap).
2. Increase Ukrainian immersion from 21.6% to at least 50% by adding Ukrainian introductions, transitional prose, and more Ukrainian-language explanatory content in sections "Огляд та самооцінка", "Навичка 1: Відмінки в дії: Давальний та Орудний", and "Граматичні тонкощі: Родовий, Знахідний та Кличний".

**Expected score after fix:** 9/10

### LLM Fingerprint: 7/10 → 8/10
**What to fix:**
1. Line 211: Replace "magnificent hallmark" → "distinctive feature" or "one of the defining features" in section "Граматичні тонкощі: Родовий, Знахідний та Кличний".
2. Line 18: Tone down "fundamental engine that drives the language" → "the system that organizes the language" in section "Огляд та самооцінка".
3. Line 140: Replace "In this section, we will explore" → "Now let's look at" or start with a Ukrainian hook sentence in section "Граматичні тонкощі: Родовий, Знахідний та Кличний".
4. Vary example presentation format across case subsections (use tables, dialogues, and inline examples instead of uniform bullet lists throughout).

**Expected score after fix:** 8/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Add at least one inline mini-exercise (e.g., "Quick check: Which case would you use for...?") within section "Огляд та самооцінка" before the full YAML activities.
2. Add a brief Ukrainian warm-up paragraph at the very start, before the English theory.

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
Experience: 9×1.5 = 13.5
Language: 9×1.1 = 9.9
Pedagogy: 8×1.2 = 9.6 (unchanged)
Activities: 8×1.3 = 10.4 (unchanged — fill-in shortfall is minor)
Beginner Safety: 8×1.3 = 10.4 (unchanged)
LLM Fingerprint: 8×1.0 = 8.0
Linguistic Accuracy: 9×1.5 = 13.5

Total: 75.3 / 8.9 = 8.5/10
```

**Note:** Reaching 9.0 overall would additionally require improving Pedagogy (add inline exercises), Activities (add 3 more fill-in items), and Beginner Safety (reduce dense theory blocks). The immersion fix (Issue 3) is the highest-impact change — it would improve Language, Beginner Safety, and Experience Quality simultaneously.

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (research notes use narrative format)
- Dates checked: 1 (1918 UNR — correct per research notes)
- Named figures verified: 1 (Heorhiy Narbut — confirmed in research)
- Primary quotes cross-referenced: NOT_APPLICABLE (not a seminar track)
- Chronological sequence: CONSISTENT
- Claims without research grounding: 0

Cultural claims verified:
- Diia app holds digital documents with legal weight: Plausible, well-known fact
- Monobank as neobanking leader: Plausible, well-known
- Stamps circulated as money in 1918 (шаги): Confirmed by research notes

## Verification Summary

- Content lines read: 332
- Activity items checked: 157 (across 12 activity blocks)
- Ukrainian sentences verified: 55+
- Citations in bank: 20
- Issues found: 6 (1 grammar error, 1 absurd example, 1 immersion shortfall, 1 unnatural collocation, 1 translation error, 1 LLM fingerprint cluster)

## Verdict

**FAIL**

Blocking issues: (1) Linguistic Accuracy 8/10 triggers auto-fail at <9 threshold — a demonstrative pronoun agreement error ("Це" → "Ця") in a grammar-teaching example on line 149 and a semantically absurd example on line 313 must be fixed. (2) Immersion at 21.6% is critically below the 50-60% Band 1 target, requiring substantial Ukrainian content expansion across all theory sections.