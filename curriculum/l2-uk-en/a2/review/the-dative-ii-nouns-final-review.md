## Adversarial QA Review: the-dative-ii-nouns (A2-02)

**Reviewer:** Claude (Phase 9 Final QA)
**Date:** 2026-02-21
**Verdict:** APPROVE

---

### Prior Review Issues — All Resolved

All 7 issues from the prior Green Team review (2026-02-19/20) have been verified as fixed:
1. "Я даруємо" → "Ми даруємо" (2 fill-ins) and "Я дарую" (cloze) ✓
2. "Читат казку" → "Читати казку" ✓
3. Orphaned cloze blanks 9-14 → passage expanded to 12 blanks ✓
4. Pharmacy Dative/Locative claim → rewritten correctly ✓
5. Select morphology question → replaced with cultural context ✓
6. "іменинник" gloss → "(name day celebrant)" ✓
7. Unjumble capitalization → lowercase "студентові" ✓

---

### New Issues Found & Fixed

**Issue 1: Incorrect quiz explanation (activities YAML)**
- **Location:** Quiz item 1, explanation field
- **Original:** `"Множина Давального відмінка має закінчення -ам."`
- **Problem:** Answer is "дітям" (-ям, soft group), but explanation says -ам only. Misleading.
- **Fix:** Changed to `"Множина Давального відмінка: -ам (тверда група) або -ям (м'яка група, як «дітям»)."`

**Issue 2: IPA error — надсилати (vocabulary YAML)**
- **Original:** `[nɐd͡zsɪˈlatɪ]`
- **Problem:** The d͡z tie-bar notation represents the Ukrainian affricate ДЗ phoneme (as in "дзвін"). But надсилати = prefix над- + root сил-, not the ДЗ phoneme. Wrong phonemic analysis.
- **Fix:** `[nɐdsɪˈlatɪ]`

**Issue 3: IPA error — свято (vocabulary YAML)**
- **Original:** `[ˈsʲʋjatɔ]`
- **Problem:** Incorrectly palatalizes С and separates j from ʋ. The cluster "свя" palatalizes the ʋ, not the с.
- **Fix:** `[ˈsʋʲatɔ]`

**Issue 4: Plan-required verb "підходити" unused (content .md, dialogue)**
- **Original:** `"Книга завжди пасує розумній людині."`
- **Problem:** "пасувати" is not in the plan vocabulary. "Підходити" is plan-required but absent from all prose.
- **Fix:** `"Книга завжди підходить розумній людині."`

---

### Observations (Non-blocking)

- Plan-required verbs личити, заважати, вистачати, бракувати appear only in vocabulary YAML, not in prose or activities. These are important dative-governing verbs (especially impersonal constructions) but the module's forward connection to A2-03 "Dative Verbs" is explicit and appropriate for deferred coverage.

---

### Full Verification Summary

| Check | Result |
|-------|--------|
| Subject-verb agreement (all activities) | PASS — 60+ items verified |
| Unjumble word arrays vs answers | PASS — all 6 items, every word accounted for |
| Cloze blanks vs passage | PASS — 12 blanks, 12 passage slots |
| Fill-in answer grammaticality | PASS — all inserted answers form correct sentences |
| Russianisms scan | CLEAN |
| Russian characters scan | CLEAN |
| Consonant shift accuracy (Г→З, К→Ц, Х→С) | PASS |
| Plan sections present | PASS — all 5 outline sections covered |
| Plan required vocabulary in vocab YAML | PASS — all 14 required items present |
| Cultural claims accuracy | PASS — odd flowers, taboo gifts, Name Day verified |
| IPA tie bars on affricates | PASS after fix |
| IPA ʋ not w for В | PASS |
| Word target (3000) | PASS — 4021 words |
