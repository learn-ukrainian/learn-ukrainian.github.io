Now let me do a thorough adversarial review, checking IPA, grammar, plan compliance, and LLM artifacts.

## Adversarial Review: describing-things-adjectives (A1-26)

### Issues Found

---

**Issue 1: IPA Error — швидкий stress placement**
- **Location**: `describing-things-adjectives.md`, line 366
- **Current**: `швидкий [ʃʋɪdˈkɪj]` (stress on second syllable)
- **Problem**: Ukrainian шви́дкий is stressed on the FIRST syllable, not the second. Correct: [ˈʃʋɪdkɪj].
- **Severity**: Error — wrong pronunciation guidance for learners.

---

**Issue 2: Orphaned vocabulary — смачний absent from prose**
- **Location**: `describing-things-adjectives.md` (entire file)
- **Problem**: The word `смачний` appears in the vocabulary file (line 54) and in the activity match-up (line 273), but is never introduced or used in the lesson text. Learners encounter it in activities without having seen it in context. The plan lists it as recommended vocabulary.
- **Fix**: Add a natural usage of `смачний` in the "Мій кабінет" text, where coffee on a desk is a natural fit.

---

**Issue 3: Unnatural collocation — "нудний" cat**
- **Location**: `describing-things-adjectives.md`, line 409
- **Current**: «Він дуже **добрий**, але іноді **нудний**, коли спить весь день.»
- **Problem**: Describing a sleeping cat as "boring" (нудний) is unnatural in Ukrainian. A sleeping cat is "calm" (спокійний) or "lazy" (лінивий). Since спокійний is already introduced in Dialogue 2 (line 377), use it here for natural reinforcement.
- **Also affects**: The analysis key on line 434.

---

**Issue 4: LLM cliché in introduction**
- **Location**: `describing-things-adjectives.md`, line 13
- **Current**: «Adjectives bring your world to life... the key to unlocking the beauty of the Ukrainian language.»
- **Problem**: Double LLM cliché ("bring to life" + "key to unlocking"). Generic phrasing that doesn't sound like a real teacher.

---

**Issue 5: LLM cliché in conclusion**
- **Location**: `describing-things-adjectives.md`, line 444
- **Current**: «Congratulations! You have unlocked the ability to describe the world. You are no longer pointing and saying names; you are painting pictures with words.»
- **Problem**: "Unlocked the ability" and "painting pictures with words" are textbook LLM artifacts.

---

**Issue 6: Invented statistic — "90%"**
- **Location**: `describing-things-adjectives.md`, line 64
- **Current**: «These represent the standard pattern you will see 90% of the time.»
- **Problem**: The "90%" figure is unsourced and invented. While hard-stem adjectives are dominant, presenting a specific percentage as fact is an LLM artifact (false statistics).

---

### All other checks passed:

- **IPA (all other entries)**: ʋ used correctly for В throughout; tie bars on affricates (t͡ʃ, t͡s) present; ɦ used for Г; stress positions verified on 40+ entries — all correct except швидкий.
- **Russianisms**: None found. No кушати, получати, ы, э, ё, ъ.
- **Gender agreement**: Verified every adjective-noun pair in prose and activities (~80 pairs) — all correct. Special case «Він добра людина» correctly explained (людина = F).
- **Activities**: All 10 activity blocks verified. Fill-in answers produce grammatical sentences. Unjumble word arrays contain all words in answers. Quiz answers are correct. Group-sort categories are accurate.
- **Plan compliance**: All 8 meta outline sections present. All 8 required vocabulary items used in prose. All 4 objectives mapped to self-check questions.
- **Factual accuracy**: Софійський собор, Мавка — both accurate.
- **Grammar scope**: No forms beyond Nominative case. No comparative/superlative (correctly deferred to A2-05).

---

## Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/describing-things-adjectives.md
---OLD---
> Adjectives bring your world to life. Without them, you can only name things ("This is a house"). With them, you can express opinion, color, emotion, and detail ("This is a **beautiful, old** house"). Understanding how adjectives change to match nouns is the key to unlocking the beauty of the Ukrainian language.
---NEW---
> Without adjectives, you can only name things: "This is a house." With them, you can add opinion, color, and detail: "This is a **beautiful, old** house." In this module, you will learn how Ukrainian adjectives change their endings to match the noun they describe — a pattern called **agreement**.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/describing-things-adjectives.md
---OLD---
These represent the standard pattern you will see 90% of the time.
---NEW---
These represent the standard pattern and cover the vast majority of adjectives you will encounter.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/describing-things-adjectives.md
---OLD---
*   **телефон** (phone) is Masculine → новий, чорний [ˈt͡ʃɔrnɪj] (black), швидкий [ʃʋɪdˈkɪj] (fast), дорогий, дешевий.
---NEW---
*   **телефон** (phone) is Masculine → новий, чорний [ˈt͡ʃɔrnɪj] (black), швидкий [ˈʃʋɪdkɪj] (fast), дорогий, дешевий.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/describing-things-adjectives.md
---OLD---
На столі стоїть комп'ютер. Він **старий**, але **швидкий**.
Тут також є шафа (wardrobe). Вона **велика**.
---NEW---
На столі стоїть комп'ютер. Він **старий**, але **швидкий**.
На столі також є кава (coffee). Вона дуже **смачна** (tasty).
Тут також є шафа (wardrobe). Вона **велика**.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/describing-things-adjectives.md
---OLD---
Мій кіт тут. Він **малий** і **чорний**. Він дуже **добрий**, але іноді **нудний**, коли спить весь день.
---NEW---
Мій кіт тут. Він **малий** і **чорний**. Він дуже **добрий**, але дуже **спокійний**, коли спить весь день.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/describing-things-adjectives.md
---OLD---
*   **кіт** (M) → малий, чорний, добрий, нудний, білий.
---NEW---
*   **кіт** (M) → малий, чорний, добрий, спокійний, білий.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/describing-things-adjectives.md
---OLD---
Congratulations! You have unlocked the ability to describe the world. You are no longer pointing and saying names; you are painting pictures with words.
---NEW---
Well done! You can now describe objects, rooms, and people in Ukrainian using adjectives that match in gender and number.
===FIX_END===

===VERDICT===
APPROVE
===END_VERDICT===