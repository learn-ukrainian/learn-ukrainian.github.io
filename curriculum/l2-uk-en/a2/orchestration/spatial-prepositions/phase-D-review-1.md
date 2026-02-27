**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Evidence Summary |
|---|-----------|-------|------------------|
| 1 | **Lesson Quality** | 7/10 | The lesson follows PPP structure but the Interior Designer persona is barely present beyond a passing mention in section «Вступ / Introduction» (line 20) and one dialogue. The plan's "hospitality hook" (guests seated на покутті) is entirely missing. Dialogue numbering is disordered (4→1→2→3). Pacing is heavy on theory before first practice opportunity. 3/5 on "Would I Continue?" test. |
| 2 | **Language Quality** | 7/10 | **Russicism auto-fail trigger**: «Прекрасний вибір» at line 417 — "прекрасний" is on the Russicism watchlist (красивий/прекрасний→гарний/чудовий). Line 82 has a garbled English translation: "The vase implies standing on the table" instead of "The vase is standing on the table." Line 185 has the typo «two distinct distinct items» (doubled word). Line 302 calls Мурчик "Murka" — a different name entirely. |
| 3 | **Immersion Balance** | 9/10 | 51.5% immersion against a 50-60% target for A2 M01-20. English is used correctly for grammar explanations; Ukrainian for examples and dialogues. The balance feels appropriate for the level. |
| 4 | **Richness** | 7/10 | The [!culture] box about «Українська Хата» (line 168) is good, and the [!myth-buster] about Покуття (line 213) adds genuine depth. However, the plan calls for a full "hospitality hook" where guests are seated «на покутті» and «за столом» — this is absent. The cultural closing about the stove and sacred corner in the Підсумок is also absent (plan section 5 requires it). The module reads as a grammar reference more than a culturally-anchored lesson. |
| 5 | **Activity Quality** | 6/10 | **Critical error**: The error-correction activity (activity file line 216) marks «Я йду до банку» as incorrect, but the *content itself* at line 231 explicitly teaches that «Я йду до банку» is valid ("I walk towards the bank, maybe just to the ATM outside"). This is a direct pedagogical contradiction — the lesson teaches a form and then penalizes the student for using it. The hedging explanation ("While 'до банку' implies approach...If correct context implies entering") confirms the item is flawed. Otherwise activities are well-structured and varied (12 activities, 8 types). |
| 6 | **LLM Fingerprint** | 7/10 | **Structural monotony**: «Розглянемо приклади:» appears 4 times as an identical section opener (lines 196, 208, 224, 238) within section «Презентація / Presentation». This is a clear LLM fingerprint — a real tutor would vary the phrasing. The rest of the content avoids major AI tells, but this repetition is notable. |
| 7 | **Factual Accuracy** | 8/10 | Grammar rules are accurately presented. The State Standard references in the research notes align with the content's treatment of Locative/Accusative/Instrumental governance. However, the vocabulary file contains IPA errors: «всередині» is transcribed as `` (line 93 of vocab file) — the initial sound should be [ʋ] not [ʍ] (voiceless labial-velar approximant). «Посеред» has a double stress mark `` (line 104 of vocab file) — Ukrainian words have one primary stress, should be ``. |

---

## Critical Issues Found

### Issue 1: Activity contradicts lesson content (CRITICAL — Pedagogical Error)

**Location:** Activity file `error-correction`, item at line 216; Content file line 231

**Problem:** The error-correction activity presents «Я йду до банку.» as an incorrect sentence, with the "correct" answer being «в банк». However, the lesson content at line 231 explicitly teaches: «**До + Genitive** means approaching or going towards a person. *Я йду до мами* (I go to mom — you cannot enter a person!). *Я йду до банку* (I walk towards the bank, maybe just to the ATM outside).»

The module teaches "до банку" as a valid, meaningful construction with a specific semantic distinction (approach vs. entry), then penalizes students for using it. The activity's own explanation hedges: "While 'до банку' implies approach, entering the building usually uses 'в банк' (Accusative). If correct context implies entering." This "if" condition makes the item fundamentally ambiguous — without specifying whether the speaker intends to enter, both forms are correct.

**Fix:** Remove this item from the error-correction activity entirely. Replace with a genuine error (e.g., «Я живу в вулиці» → «на вулиці», or «Він поклав книги на столі» → «на стіл»).

### Issue 2: Russicism — «Прекрасний вибір» (CRITICAL — Auto-fail trigger)

**Location:** Content file line 417

**Problem:** «Прекрасний вибір. Ваша квартира буде дуже сучасною і комфортною.» — "Прекрасний" is on the auto-fail Russicism watchlist. While "прекрасний" exists in Ukrainian dictionaries, in the context of a curriculum module that should model standard Ukrainian, «чудовий» or «гарний» are the preferred equivalents per project standards.

**Fix:** Replace «Прекрасний вибір» with «Чудовий вибір» at line 417.

### Issue 3: Dialogue numbering disorder (Major — Organization)

**Location:** Content file lines 350, 363, 395, 429 in section «Діалоги / Dialogues»

**Problem:** The dialogues appear in the order: Dialogue 4 (У супермаркеті) → Dialogue 1 (Searching for Keys) → Dialogue 2 (The Interior Designer) → Dialogue 3 (On the Street). A learner would encounter "Dialogue 4" first with no preceding Dialogues 1-3, which is confusing.

**Fix:** Renumber the dialogues sequentially (1→2→3→4) in their current order, or reorder them so 1 comes first.

### Issue 4: Missing plan-required content — Hospitality hook and cultural closing

**Location:** Section «Презентація / Presentation» and section «Підсумок»

**Problem:** The plan (plan file, Presentation section, bullet 4) explicitly requires: "Highlight the hospitality hook: guests are seated 'на покутті' (at the sacred corner) or 'за столом' (at the table), illustrating the most honorable places in the home." This is completely absent from the content. The Покуття is mentioned only in a [!myth-buster] box (line 213-217) about spatial orientation, not in the hospitality context. The plan's Summary section also requires a "Cultural closing: Review how the Ukrainian world-view organizes space around the stove and the sacred corner, reinforcing vocabulary like 'піч', 'покуття', and 'гостинність'." The actual Підсумок (line 466-484) contains only grammar recap with no cultural closing.

**Fix:** Add a paragraph or callout box in section «Презентація / Presentation» about the hospitality tradition: guests seated «на покутті», the honor of «за столом». Add a cultural closing paragraph in the Підсумок referencing «піч», «покуття», and «гостинність».

### Issue 5: Name inconsistency — Мурчик vs. "Murka"

**Location:** Content file line 300 vs. line 302

**Problem:** Line 300 introduces the cat as «a mischievous cat named **Мурчик**», but line 302 immediately says «Murka is sitting **on** the table.» Мурчик and Murka are different names (Murka/Мурка is typically a female cat name). This is a confusing error for a beginner.

**Fix:** Change "Murka" to "Мурчик" at line 302.

### Issue 6: Garbled English translation

**Location:** Content file line 82

**Problem:** «Ваза стоїть **на столі**. (The vase implies standing on the table.)» — "implies standing" is not correct English. The verb "стоїть" means "stands/is standing." The translation should be "The vase is standing on the table" or simply "The vase stands on the table."

**Fix:** Change to "(The vase is standing on the table.)"

---

## Verification Summary

### Plan Compliance

| Plan Element | Status | Notes |
|--------------|--------|-------|
| Section «Вступ / Introduction» | PARTIAL | Де? vs. Куди? covered; Interior Designer persona mentioned but not sustained; State Standard not explicitly referenced |
| Section «Презентація / Presentation» | PARTIAL | Groups 1-3 well-covered; [!culture] box about хата present; **hospitality hook missing**; «навпроти» from plan rendered as «напроти» throughout |
| Section «Практика / Practice» | PASS | Good variety of drills: static, motion, reading comprehension, correction challenge |
| Section «Діалоги / Dialogues» | PARTIAL | 4 dialogues present (plan calls for 3); numbering disordered; supermarket dialogue is bonus beyond plan scope |
| Section «Підсумок» | PARTIAL | Grammar recap is strong; **cultural closing missing** |

### Vocabulary Plan Match

| Plan Vocab Item | In Content? | In Vocab File? |
|----------------|-------------|----------------|
| в/у | Yes | Yes |
| на | Yes | Yes |
| під | Yes | Yes |
| за | Yes | Yes |
| між | Yes | Yes |
| біля | Yes | Yes |
| до | Yes | Yes |
| навпроти | As «напроти» | As «напроти» |
| перед | Yes | Yes |
| над | Yes | Yes |
| навколо | Yes (line 264) | Yes |
| вздовж | Not in content | Yes (vocab only) |
| поруч | Yes (line 265) | Yes |

**Note:** Plan specifies «навпроти» but content and vocab file consistently use «напроти». Both are valid Ukrainian, but the discrepancy should be resolved — preferably to «напроти» (which is the more common modern form).

### Colonial Framing Check
**PASS** — No instances of defining Ukrainian by contrast with Russian. English is compared to Ukrainian appropriately (line 37: "In English, we sometimes change the preposition...In Ukrainian, we often use the *same* preposition...").

### LLM Fingerprint Details

- **Structural monotony (section openers):** H2 openers are varied ✓. But within section «Презентація / Presentation», the subsections for БІЛЯ, НАПРОТИ, ДО, and З all open with the identical phrase «Розглянемо приклади:» (lines 196, 208, 224, 238) — 4 repetitions.
- **Example formatting uniformity:** The Instrumental group (ПІД, НАД, ПЕРЕД, ЗА) uses varied openers: «Ось кілька прикладів:» (line 129), «Подивіться на ці речення:» (line 141), «Зверніть увагу на приклади:» (line 153), «Давайте розглянемо наступне:» (line 163). This is better.
- **Callout monotony:** 6 callouts use 6 different types — no monotony ✓
- **Generic AI rhetoric:** No "це не просто" / "це не лише" patterns detected ✓
- **Section opening test (first 2 lines of each H2):** Varied ✓

### Typo / Minor Issues

| Line | Issue | Fix |
|------|-------|-----|
| 185 | «two distinct distinct items» — doubled word | Remove one «distinct» |
| 244 | «Ukrainian hates clear consonant clusters» — informal/anthropomorphizing | Rephrase: "Ukrainian avoids adjacent consonant clusters" |
| Vocab line 93 | IPA `` for «всередині» — [ʍ] is wrong | Change to `` |
| Vocab line 104 | IPA `` for «посеред» — double stress | Change to `` |

### Warmth / Encouragement Markers

| Marker Type | Count | Minimum | Status |
|-------------|-------|---------|--------|
| Direct address (you/ви) | ~20+ | ≥15 | PASS |
| Encouragement phrases | 4 ("Чудово", "Гарна ідея", "Congratulations!", "Не бійтеся робити помилки") | ≥3 | PASS |
| "Don't worry" moments | 2 ("Не бійтеся робити помилки" line 284; progressive encouragement in drills) | ≥2 | PASS |
| "You can now..." validation | 2 (line 468 "You have just learned the map..."; line 47 "you will be able to describe...") | ≥2 | PASS |

---

## Verdict

**PASS WITH REQUIRED FIXES**

The module is pedagogically sound with strong grammar coverage and good activity variety. The core explanation of Location vs. Motion through case governance is well-structured. However, several issues must be resolved:

**Must fix before passing:**
1. Remove the «Я йду до банку» error-correction activity item (contradicts lesson content)
2. Replace «Прекрасний вибір» → «Чудовий вибір» (Russicism)
3. Fix dialogue numbering (4→1→2→3 → sequential)
4. Fix "Murka" → "Мурчик" name inconsistency
5. Fix garbled translation at line 82
6. Fix typo "distinct distinct" at line 185
7. Fix IPA errors in vocabulary file (всередині, посеред)

**Should fix (plan compliance):**
8. Add hospitality hook content (guests «на покутті» / «за столом»)
9. Add cultural closing to Підсумок (піч, покуття, гостинність)
10. Vary the 4× repeated «Розглянемо приклади:» in Genitive subsections