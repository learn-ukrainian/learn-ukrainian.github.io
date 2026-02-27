# Рецензія: Root Families I: The DNA of Vocabulary

**Reviewed-By:** claude-opus-4-6

**Level:** A2 | **Module:** 41
**Overall Score:** 7.4/10
**Status:** FAIL
**Reviewed:** 2026-02-23

## Plan Verification

```
Plan-Content Alignment: PASS (with issues)
- Sections: 5/5 present (Вступ, Родини ход- та пис-, Родини чит- та бач-, Фонетика та префікси, Практичне застосування)
- Vocabulary: 29 items in vocabulary file, Big Four roots covered, розклад included as related concept
- Grammar scope: PASS — stays within root families, prefixes, aspectual pairs, euphony rule
- Objectives: 4/4 addressed (identify roots, guess derivatives, build words, recognize professional roots)
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 7/10 | <7 | Cold opening — no warm greeting, no "Привіт!"; 4 orphaned English filler paragraphs (lines 84-86, 122-126, 150-151, 236-238) break lesson flow; good bookstore dialogue at line 202 |
| 2 | Language | 8/10 | <8 | Broken comma syntax on line 44; "концептуалізації" too academic for A2 (line 109); English paragraphs overly verbose and repetitive |
| 3 | Pedagogy | 7/10 | <7 | "обачний" tested in 3 activities but never introduced in lesson prose; heavy theory frontloading in section «Вступ» before any practice; розклад quiz item uses root -клад- not taught in module |
| 4 | Activities | 8/10 | <7 | 12 varied activity types — excellent range; off-scope розклад question (activity quiz item 7); untaught "обачний" in group-sort, true-false, and select |
| 5 | Beginner Safety | 7/10 | <7 | "Would I Continue?" 3/5; no welcome, heavy English theory paragraphs before first Ukrainian example; decent scaffolding once past the introduction |
| 6 | LLM Fingerprint | 7/10 | <7 | "In this module, we will explore this architectural beauty" (line 19); "Це не просто" x2 (lines 109, 114); repetitive English filler blocks all saying "context matters" |
| 7 | Linguistic Accuracy | 8/10 | <9 | IPA error: вхід transcribed as [ʍxʲid] using non-Ukrainian phoneme ʍ (vocab line 9); factual error: Plokhy called novelist (content line 205); line 44 syntactic break |

**Weighted Overall:**
```
(7×1.5 + 8×1.1 + 7×1.2 + 8×1.3 + 7×1.3 + 7×1.0 + 8×1.5) / 8.9
= (10.5 + 8.8 + 8.4 + 10.4 + 9.1 + 7.0 + 12.0) / 8.9
= 66.2 / 8.9
= 7.4/10
```

## Auto-Fail Checklist Results

- Russianisms: CLEAN — no Russian calques detected
- Calques: CLEAN — "має зв'язок з" (lines 39, 249) is slightly unnatural but not a calque
- Colonial framing: CLEAN — no Russian comparisons found
- Grammar scope: CLEAN — stays within root families and aspect
- Activity errors: 2 issues — розклад off-scope, обачний untaught
- Beginner safety: 3/5
- Factual accuracy: 1 issue — Plokhy described as novelist (line 205)
- **AUTO-FAIL TRIGGER**: Linguistic Accuracy 8/10 < 9 threshold

## Critical Issues Found

### Issue 1: IPA Error — Non-Ukrainian Phoneme
- **Location**: Vocabulary file line 9
- **Original**: `ipa: '[ʍxʲid]'` for lemma "вхід"
- **Problem**: The symbol ʍ represents a voiceless labial-velar approximant (found in some English dialects for "wh"). This phoneme does not exist in Ukrainian. The в in вхід before voiceless х is realized as labiodental [ʋ] or bilabial approximant [w], never as [ʍ].
- **Fix**: Change to `ipa: '[ʋxʲid]'`

### Issue 2: Factual Error — Plokhy Described as Novelist
- **Location**: Line 205, Section «Практичне застосування»
- **Original**: «Доброго дня! Я ваш постійний **читач**. Скажіть, ви маєте новий історичний роман Сергія Плохія?»
- **Problem**: Serhii Plokhy (Сергій Плохій) is a Ukrainian-American historian at Harvard who writes academic non-fiction (*The Gates of Europe*, *Chernobyl*). He does not write "історичні романи" (historical novels). This is a common LLM fabrication that conflates "historian" with "novelist."
- **Fix**: Replace with a real Ukrainian novelist, e.g., «новий роман Сергія Жадана» or «новий роман Андрія Куркова» — both are actual fiction writers.

### Issue 3: Broken Ukrainian Syntax
- **Location**: Line 44, Section «Родини ход- та пис-»
- **Original**: «Воно означає регулярний, рух, який повторюється, пішки, а не рух в один кінець у цей момент.»
- **Problem**: The comma after "регулярний" breaks the noun phrase. "Регулярний" modifies "рух" and should not be separated from it. The current punctuation creates a fragmented, unreadable sentence.
- **Fix**: «Воно означає регулярний рух пішки, який повторюється, а не рух в один кінець у цей момент.»

### Issue 4: Untaught Vocabulary Tested in Activities
- **Location**: Activities — group-sort (line 163), true-false (line 204), select (line 327)
- **Original**: "обачний" appears in 3 separate activity types
- **Problem**: The word "обачний" (cautious) is never introduced, explained, or exemplified anywhere in the lesson prose. It exists in the vocabulary file but was never taught. Testing before teaching violates PPP pedagogy and beginner safety.
- **Fix**: Either (a) add a sentence introducing "обачний" in section «Родини чит- та бач-» near the -бач- discussion, or (b) remove it from activities and add it to a future module.

### Issue 5: Misplaced English Filler Paragraphs
- **Location**: Lines 84-86 (Section «Родини ход- та пис-»), lines 122-126 (Section «Родини чит- та бач-»), lines 150-151 (Section «Фонетика та префікси»), lines 236-238 (Section «Практичне застосування»)
- **Problem**: Four English-only paragraphs appear as orphaned blocks disconnected from the surrounding Ukrainian flow. Lines 122-126 are particularly jarring — a paragraph about -бач- in relationships is immediately followed by an unrelated paragraph about -чит- in university lectures, with no transition. Lines 150-151 repeats the euphony explanation from lines 143-148 in more verbose academic language. All four blocks read as padding to hit word count.
- **Fix**: Remove or integrate. Lines 150-151 is pure repetition — delete entirely. Lines 84-86 should be moved up to the -ход- subsection. Lines 122-126 should be split: бач- paragraph into the бач- H3, чит- paragraph into the чит- H3. Lines 236-238 can be condensed into 2 sentences.

### Issue 6: "Це не просто" LLM Pattern (2 occurrences)
- **Location**: Line 109, Section «Родини чит- та бач-»; Line 114, Section «Родини чит- та бач-»
- **Original (line 109)**: «Це не просто опис фізичного зору.»
- **Original (line 114)**: «Це не просто звичайна зустріч двох людей.»
- **Problem**: "Це не просто X" used twice within 5 lines is a characteristic LLM rhetorical pattern. Rubric specifies: "це не просто / це не лише / не просто X, а Y used 2+ times → ≤ 7."
- **Fix**: Rewrite line 109 to: «Цей корінь стосується не лише фізичного зору.» Rewrite line 114 to: «Побачення — це більше, ніж звичайна зустріч.» Vary the sentence structure.

### Issue 7: Off-Scope Quiz Item (розклад)
- **Location**: Activity quiz "Логіка словотворення," item 7 (activity lines 92-102)
- **Original**: «Яке слово означає розклад часу, план?» with correct answer "розклад"
- **Problem**: The word "розклад" uses root -клад- (from класти, to lay/put), which is NOT one of the Big Four roots taught in this module. The quiz is titled "Логіка словотворення" (word formation logic) for this module's roots, but this question tests a root that was never explained. The explanation even says «Корінь клад- (класти) з префіксом роз-» — acknowledging it's a different root.
- **Fix**: Replace with a question testing one of the actual Big Four roots, e.g., a question about "прихід" or "вичитати."

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 44 | «регулярний, рух, який повторюється, пішки» | «регулярний рух пішки, який повторюється» | Grammar (broken comma) |
| 39 | «має зв'язок з рухом» | «пов'язаний з рухом» | Naturalness |
| 109 | «концептуалізації» | «осмислення» or «сприйняття» | Register (too academic for A2) |
| 225 | «раптово подзвонив мій телефон» | «раптово задзвонив мій телефон» | Naturalness (подзвонив implies deliberate short action by a person, not a phone ringing) |
| 249 | «Який український корінь глибоко має зв'язок з рухом» | «Який український корінь глибоко пов'язаний з рухом» | Naturalness |

## Beginner Safety Audit

"Would I Continue?" Test: 3/5
- Overwhelmed? **FAIL** — Dense English theory paragraphs in section «Вступ» (lines 17-29) with academic language like "modular construction system", "immoveable core block", "semantic roles." Too much abstract theory before any Ukrainian example.
- Instructions clear? **PASS** — Once past the opening, instructions are clear and well-structured.
- Quick wins? **FAIL** — First practice opportunity doesn't arrive until the conjugation table at line 47 (after ~800 words of theory). The "Lego" metaphor is engaging but too long before learner does anything.
- Ukrainian scary? **PASS** — Ukrainian is well scaffolded with English support and translations in parentheses.
- Come back tomorrow? **PASS** — The bookstore dialogue (lines 202-211), cultural hooks (писанка, побачення), and Guessing Machine challenge (lines 183-189) are genuinely engaging once reached.

## Strengths

- **Excellent activity variety**: 12 distinct activity types covering matching, quizzes, fill-in, sorting, unjumble, true/false, error correction, mark-the-words, multi-select, cloze, translation, and a second quiz with deductive logic — best-in-class range.
- **Strong cultural hooks**: The писанка etymology (line 60), побачення as "mutual seeing" (line 114), and the Greek *hodos* cognate (line 39) make linguistic patterns memorable and culturally grounded.
- **Bookstore dialogue** (lines 202-211) in section «Практичне застосування»: Natural, contextually rich, and organically uses 5 target words. This is how A2 practice should look.
- **Кафе Птах mnemonic** in section «Фонетика та префікси»: Clear, memorable, well-drilled with the сходити/зходити contrast.
- **Aspect pair teaching** in sections «Родини ход- та пис-» and «Практичне застосування»: The писати/написати and виходити/вийти pairs are well-contextualized with real-life scenarios.

## Fix Plan to Reach 9/10 (REQUIRED if score < 9.0)

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Vocab line 9: Change IPA `[ʍxʲid]` → `[ʋxʲid]` for "вхід" — removes non-Ukrainian phoneme
2. Line 205 (Section «Практичне застосування»): Replace «Сергія Плохія» with an actual Ukrainian novelist (Жадан, Курков, Дереш) — fixes factual error
3. Line 44 (Section «Родини ход- та пис-»): Fix comma syntax «регулярний, рух» → «регулярний рух пішки» — fixes grammar
4. Vocab line 105: Verify вичитати stress — current `` places stress on first syllable, standard is on third ``

**Expected score after fix:** 9/10

### Experience Quality: 7/10 → 9/10
**What to fix:**
1. Add warm opening: Insert "Привіт!" greeting + 1-2 sentence preview ("Сьогодні ви навчитеся бачити знайомі блоки у нових словах") before line 14
2. Lines 150-151 (Section «Фонетика та префікси»): Delete the "Why Euphony Matters" paragraph — it repeats lines 143-148 verbatim in more words
3. Lines 84-86 (Section «Родини ход- та пис-»): Move "Understanding Context and Metaphorical Uses" to follow the -ход- H3 subsection where it belongs
4. Lines 122-126 (Section «Родини чит- та бач-»): Split into two, integrate each into its respective root's H3 subsection
5. Lines 236-238 (Section «Практичне застосування»): Condense to 2 sentences or delete — adds nothing new

**Expected score after fix:** 9/10

### LLM Fingerprint: 7/10 → 9/10
**What to fix:**
1. Line 19: Rewrite «we will explore this architectural beauty» — replace with something specific: "you'll learn to decode words like a detective"
2. Line 109: Change «Це не просто опис фізичного зору» → «Цей корінь стосується не лише фізичного зору»
3. Line 114: Change «Це не просто звичайна зустріч» → «Побачення — це більше, ніж звичайна зустріч»
4. Line 151: Delete "This rule is not just an arbitrary grammar requirement" filler block entirely

**Expected score after fix:** 9/10

### Pedagogy: 7/10 → 9/10
**What to fix:**
1. Add 2-3 sentences introducing "обачний" in section «Родини чит- та бач-» near line 111, with an example: «Обачна людина — це людина, яка уважно "дивиться навколо" і бачить потенційну небезпеку.»
2. Replace розклад quiz item (activity lines 92-102) with a question about a Big Four root derivative
3. Move first Ukrainian example earlier in section «Вступ» — currently first example doesn't appear until line 32

**Expected score after fix:** 9/10

### Beginner Safety: 7/10 → 9/10
**What to fix:**
1. Add warm greeting at line 8 or 14 — "Привіт! Welcome to your first word-building module."
2. Add mini quick-win exercise after the Lego metaphor (around line 20): e.g., "Can you guess? в- + хід = ?" — gives a dopamine hit before the theory deepens
3. Reduce the "Understanding Aspect" block (lines 27-29) from one dense paragraph to a shorter, friendlier explanation with a clear example

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 9×1.2 + 8×1.3 + 9×1.3 + 9×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.8 + 10.4 + 11.7 + 9.0 + 13.5) / 8.9
= 78.8 / 8.9
= 8.9/10
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (core track, not seminar)
- Dates checked: 0 (no specific dates in content)
- Named figures verified: 1 — Сергій Плохій (line 205): **DISCREPANCY** — described as author of "історичний роман" but Plokhy writes academic non-fiction
- Primary quotes cross-referenced: N/A
- Chronological sequence: CONSISTENT
- Claims without research grounding: 1 — The Greek cognate *hodos* claim (line 39) is a real etymological connection (Indo-European *sed- → Slavic *xodъ and Greek *hodos from *sod-) and is plausible
- Etymology claims verified: Proto-Slavic *pьsati* (line 60) matches research notes; Proto-Slavic *čisti* (line 91) is consistent with research
- Callout boxes checked: 7 — all factually sound except the [!myth-buster] at line 217 which is pedagogically valid but somewhat overstates the risk ("використання неправильного виду відразу змінює зміст речення" — aspect errors rarely cause genuine misunderstanding at A2 level, though they do sound unnatural)

## Verification Summary

- Content lines read: 256
- Activity items checked: 99 individual items across 12 activity blocks
- Ukrainian sentences verified: 38
- IPA transcriptions checked: 29 (all vocabulary items)
- Factual claims verified: 6 (etymologies, named figures, cultural claims)
- Issues found: 7 (3 critical, 4 significant)

## Verdict

**FAIL**

Blocking issues: (1) Linguistic Accuracy 8/10 < 9 auto-fail threshold — IPA error with non-Ukrainian phoneme [ʍ] for вхід, factual error calling Plokhy a novelist, and broken comma syntax on line 44. (2) LLM Fingerprint at threshold with 2x "це не просто" pattern and classic "we will explore" opening. (3) Untaught vocabulary "обачний" tested in 3 activities violates PPP pedagogy. All fixable in a targeted D.2 pass without rebuild.