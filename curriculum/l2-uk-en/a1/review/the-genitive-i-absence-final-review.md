Good — the vocabulary file exists. Now I've found a critical error in it. Let me compile my full review.

---

## Adversarial QA Review: the-genitive-i-absence (a1-16)

### Issues Found

**CRITICAL — Vocabulary file: wrong Genitive form for телефон**
- **File:** `vocabulary/the-genitive-i-absence.yaml`, line 36
- **Current:** `notes: Concrete object → Genitive ending -а (телефона)`
- **Problem:** The correct Genitive of телефон is **телефону** (-у), as consistently used throughout the lesson prose (line 77) and all activities. The vocabulary file claims -а, directly contradicting every other file. "Телефона" is not standard Ukrainian.

**IMPORTANT — Content: "телефон → телефону" misplaced under -а section**
- **File:** `the-genitive-i-absence.md`, line 77
- **Current:** Under "### Genitive Endings: Masculine Hard Nouns (-а)", the example `**телефон** → немає **телефону**` is listed
- **Problem:** This example shows -у ending but lives in the -а section. A learner reading "add -а" then seeing "телефону" will be confused. Must be moved to the -у section.

**IMPORTANT — Content: "Сон → сну" misplaced under -а section**
- **File:** `the-genitive-i-absence.md`, line 86
- **Current:** `**Сон** (dream/sleep) → немає **сну** (The 'о' disappears).` under "Masculine Hard Nouns (-а)"
- **Problem:** сну is a -у ending. Listed under -а section. Green Team caught this too.

**IMPORTANT — Content: Misleading "loanword" rule in warning box**
- **File:** `the-genitive-i-absence.md`, lines 110-111
- **Current:** `Is it a substance (sugar, tea), concept (time), or foreign loanword (телефон)? Use **-у**.`
- **Problem:** "паспорт" is a foreign loanword but takes -а. So do "автобус", "студент". The "foreign loanword → -у" claim directly contradicts the lesson's own examples.

**IMPORTANT — Activities: Match-up "Є чи немає?" has 3 semantically broken pairs**
- **File:** `activities/the-genitive-i-absence.yaml`, lines 259-264
- **Current:** `Це паспорт ↔ Тут немає паспорта`, `Це чай ↔ Тут немає чаю`, `Це борщ ↔ Тут немає борщу`
- **Problem:** "Це X" is an identity statement ("This IS X"). Its negation is "Це не X" (identity negation with **не**). Matching it with "Тут немає X" (absence) contradicts the lesson's explicit teaching about не vs немає (lines 155-172). The other 5 pairs correctly use "Тут є X / У мене є X" → "Тут немає X / У мене немає X" (existence → absence).

**IMPORTANT — Content: Missing "газ/без газу" collocation**
- **File:** `the-genitive-i-absence.md`
- **Problem:** The plan's vocabulary_hints specifically lists `газ (gas/sparkling) — Gen: газу; used in the essential collocation «без газу» for ordering water` and the required vocab for вода mentions `contrast «вода з газом» vs «вода без газу»`. The content has zero mentions of газ or без газу. This is the single most important ordering phrase for water in Ukraine.

**MINOR — Vocabulary file: wrong IPA for квиток**
- **File:** `vocabulary/the-genitive-i-absence.yaml`, line 24
- **Current:** `''`
- **Problem:** Ukrainian "и" is [ɪ], not [e]. Content file correctly uses (line 27). The vocab file contradicts.

**MINOR — Activities: Quiz explanation for "немає проблем" is misleading**
- **File:** `activities/the-genitive-i-absence.yaml`, line 234
- **Current:** `Слово «проблема» (ж.р., -а) змінюється на «проблеми» (множина) у фразі «немає проблем».`
- **Problem:** "Проблеми" is nominative plural. The phrase "немає проблем" uses the **genitive plural** "проблем" (zero ending). The explanation conflates these forms.

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-genitive-i-absence.md
---OLD---
*   **паспорт** → немає **паспорта**
*   **брат** → немає **брата**
*   **телефон** → немає **телефону**
---NEW---
*   **паспорт** → немає **паспорта**
*   **брат** → немає **брата**
*   **хліб** → немає **хліба**
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-genitive-i-absence.md
---OLD---
**Special Mentions:**
*   **День** (day) → немає **дня** [dnʲɑ] (The 'е' disappears).
*   **Батько** (father) → немає **батька** (The 'о' changes to 'а').
*   **Сон** (dream/sleep) → немає **сну** (The 'о' disappears).
---NEW---
**Special Mentions:**
*   **День** (day) → немає **дня** [dnʲɑ] (The 'е' disappears).
*   **Батько** (father) → немає **батька** (The 'о' changes to 'а').
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-genitive-i-absence.md
---OLD---
**Memorize these key A1 words that take -у:**
*   **час** (time) → немає **часу**
*   **цукор** (sugar) → без **цукру** (Notice the fleeting 'o'!)
*   **чай** (tea) → немає **чаю**
*   **обід** (lunch) → немає **обіду**
---NEW---
**Memorize these key A1 words that take -у:**
*   **час** (time) → немає **часу**
*   **цукор** (sugar) → без **цукру** (Notice the fleeting 'o'!)
*   **чай** (tea) → немає **чаю**
*   **обід** (lunch) → немає **обіду**
*   **телефон** (phone) → немає **телефону**
*   **сон** (dream/sleep) → немає **сну** (The 'о' disappears, like цукор → цукру!)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-genitive-i-absence.md
---OLD---
> [!warning] **Увага: Типова помилка (-а vs. -у)**
> *   Is it a concrete native object (ticket, passport)? Use **-а**.
> *   Is it a substance (sugar, tea), concept (time), or foreign loanword (телефон)? Use **-у**.
---NEW---
> [!warning] **Увага: Типова помилка (-а vs. -у)**
> *   Is it a concrete, countable object (ticket, passport, key)? Use **-а**.
> *   Is it a substance (sugar, tea) or abstract concept (time, peace)? Use **-у**.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-genitive-i-absence.md
---OLD---
**Food & Drink:**
*   **Кава без цукру.** (Coffee without sugar.) — *цукор* (substance) → *цукру*
*   **Чай без молока.** (Tea without milk.) — *молоко* (neuter -o → -a) → *молока*
*   **Бургер без м'яса.** (Burger without meat.) — *м'ясо* (neuter -o → -a) → *м'яса*
---NEW---
**Food & Drink:**
*   **Кава без цукру.** (Coffee without sugar.) — *цукор* (substance) → *цукру*
*   **Чай без молока.** (Tea without milk.) — *молоко* (neuter -o → -a) → *молока*
*   **Вода без газу.** (Water without gas/sparkling.) — *газ* (substance) → *газу*
*   **Бургер без м'яса.** (Burger without meat.) — *м'ясо* (neuter -o → -a) → *м'яса*
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/the-genitive-i-absence.yaml
---OLD---
  - left: Це паспорт
    right: Тут немає паспорта
  - left: Це чай
    right: Тут немає чаю
  - left: Це борщ
    right: Тут немає борщу
---NEW---
  - left: Тут є паспорт
    right: Тут немає паспорта
  - left: Тут є чай
    right: Тут немає чаю
  - left: Тут є борщ
    right: Тут немає борщу
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/the-genitive-i-absence.yaml
---OLD---
  - explanation: Слово «проблема» (ж.р., -а) змінюється на «проблеми» (множина) у фразі «немає проблем».
---NEW---
  - explanation: «Немає проблем» — це родовий відмінок множини від слова «проблема». Запам'ятайте цю фразу цілком.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/vocabulary/the-genitive-i-absence.yaml
---OLD---
- ipa: ''
  lemma: телефон
  notes: Concrete object → Genitive ending -а (телефона)
  pos: noun (masc.)
  translation: phone
---NEW---
- ipa: ''
  lemma: телефон
  notes: Device/technology → Genitive ending -у (телефону)
  pos: noun (masc.)
  translation: phone
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/vocabulary/the-genitive-i-absence.yaml
---OLD---
- ipa: ''
  lemma: квиток
---NEW---
- ipa: ''
  lemma: квиток
===FIX_END===

---

### Summary

| Category | Finding |
|---|---|
| IPA | Vocab file had wrong phoneme for квиток ([e] → [ɪ]), wrong IPA for телефон. Content IPA is clean. |
| Russianisms | None detected |
| Russian chars | None detected |
| Grammar agreement | Clean |
| Pedagogical | 3 match-up pairs violate the не vs немає distinction the lesson teaches; телефон and сон misplaced under -а section |
| Factual | Vocab file claims телефон → телефона (wrong — should be телефону) |
| LLM artifacts | None significant |
| Plan compliance | Missing "газ/без газу" collocation (recommended vocab + specifically called out in plan) |

**Strengths**: Excellent pedagogy overall. The "Nominative Trap" framing is genuinely useful. Cultural section is authentic. Activity volume (82 items) is strong. Dialogue scenes are natural. The є/немає contrast is well-scaffolded.

After applying the 8 fixes above, all identified issues are resolved. No remaining blockers.

===VERDICT===
APPROVE
===END_VERDICT===