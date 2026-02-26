Now I have everything I need. Let me perform the deep adversarial review.

---

## Deep Adversarial QA Review: reflexive-verbs (a1-09)

### Issues Found

**Issue 1: IPA Stress Placement Error (CRITICAL)**
- **File:** `reflexive-verbs.md`, line 393
- **Text:** `` (dee-vy-tsss-ya)
- **Problem:** Stress mark `ˈ` is placed at the start, implying stress on the first syllable. "Дивиться" is stressed on the second syllable (ди-**ВИ**-ться). Also, the final vowel `[a]` should be `[ɐ]` for unstressed position. The lay-pronunciation "(dee-vy-tsss-ya)" also falsely suggests 4 syllables when дивиться has 3.
- **Correct:** `` (dee-VY-tssya)

**Issue 2: IPA Vowel Error (MODERATE)**
- **File:** `reflexive-verbs.md`, line 398
- **Text:** ``
- **Problem:** Final `[a]` should be `[ɐ]` for unstressed position. The mixed notation also lacks a stress mark. Він сміється =.
- **Correct:** ``

**Issue 3: Case Error in Activity (MODERATE)**
- **File:** `activities/reflexive-verbs.yaml`, line 15
- **Text:** `Я веселюся на свята`
- **Problem:** "На свята" is accusative (direction). Describing the occasion/location where you have fun requires locative: "на святах". Compare: "Я їду на свята" (going TO celebrations) vs "Я веселюся на святах" (having fun AT celebrations).
- **Correct:** `Я веселюся на святах`

**Issue 4: Missing "подобатися" — Plan & Meta Compliance (MINOR)**
- **File:** `reflexive-verbs.md`, Type 3 section (~line 186-193)
- **Problem:** Both the plan (`vocabulary_hints` mentions подобатися for Type 3) and the meta (section 2, point 5: "Verbs where -ся changes meaning (сміятися, дивитися, подобатися)") explicitly list "подобатися" as a Type 3 lexicalized verb. The content omits it entirely, using навчатися instead. "Подобатися" is high-frequency A1 vocabulary ("Мені подобається") and demonstrates true lexicalization — there is no standalone "подобати."

### Verified Clean

- **Russianisms:** None found. No кушати, получати, приймати участь, слідуючий.
- **Russian characters:** No ы, э, ё, ъ.
- **Gender/case agreement in prose:** All checked — correct throughout (до тесту ✓, холодною водою ✓, павуків ✓, з друзями ✓, на кухні ✓, у ванні ✓).
- **Conjugation tables:** Both сміятися and дивитися paradigms are correct.
- **All 8 required vocabulary items:** Present in prose (дивитися, сміятися, вмиватися, одягатися, називатися, вчитися, займатися, повертатися).
- **Anagram scrambled letters:** All 8 items verified — letter sets match answers exactly.
- **Fill-in answers:** All 24 fill-in items produce grammatical sentences when answers are inserted.
- **Quiz answers:** All 16 quiz items have correct answers and accurate explanations.
- **Match-up activities:** All pairs are semantically valid.
- **Vocabulary YAML:** Exists (22 entries), IPA is accurate throughout, all stress marks verified correct.
- **Objectives → Self-check mapping:** All 4 objectives covered by the 5 self-check questions.
- **No grammar beyond module scope:** Present tense focus maintained; imperative in the story is incidental, not taught.
- **Historical/cultural claims:** -ся from себе ✓; Вибачаюсь/Вибачте debate is real ✓; -ться pronunciation claim is phonetically accurate ✓.
- **LLM artifacts:** Minimal. A few formulaic transitions ("Now that you understand...") noted by Green Team but within tolerance.

---

## Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/reflexive-verbs.md
---OLD---
*   Pronounced: (dee-vy-tsss-ya)
---NEW---
*   Pronounced: (dee-VY-tssya)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/reflexive-verbs.md
---OLD---
*   **Він сміється.**
---NEW---
*   **Він сміється.**
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/reflexive-verbs.md
---OLD---
*   **Називатися** (to be called) — literally "call itself."
    *   *Як це називається?* (What is this called?)
*   **Сміятися** (to laugh) — there is no "to laugh someone."
---NEW---
*   **Називатися** (to be called) — literally "call itself."
    *   *Як це називається?* (What is this called?)
*   **Подобатися** (to be liked / to please) — there is no standalone "подобати."
    *   *Мені подобається ця книжка.* (I like this book. — Literally: "This book pleases me.")
*   **Сміятися** (to laugh) — there is no "to laugh someone."
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/reflexive-verbs.yaml
---OLD---
    - Я веселюся на свята
---NEW---
    - Я веселюся на святах
===FIX_END===

---

===VERDICT===
APPROVE
===END_VERDICT===

**Summary:** The module is solid — strong pedagogy (mirror analogy, transitive/reflexive contrasts, Maxim's Morning story), correct Ukrainian throughout, well-varied activities. The four fixes address: two IPA transcription errors (wrong stress placement + wrong final vowel), one grammatical case error in an activity item, and one plan-compliance gap (missing подобатися from Type 3). After these fixes, the module is clean.