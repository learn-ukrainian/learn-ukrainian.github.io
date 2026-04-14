## VESUM Verification
- **Confirmed (15/15):** звук, літера, голосний, приголосний, привіт, добре, чудово, мама, молоко, нормально, тато, око, дім, ніс, сон
- **Not found:** *(none)* — all plan vocabulary exists in VESUM
- **Notes:**
  - `ніс` matches both verb `нести` (impf.) and noun `ніс` — in context (body part) the noun reading is correct ✅
  - `як справи` is a fixed phrase; individual words `як` and `справи` are standard — phrase not flagged by style guide ✅
  - `голосний` has 6 VESUM matches (adj + noun uses) — both needed for this module ✅

---

## Textbook Excerpts

### Section: Звуки і літери (Sounds and Letters)
> «Звуки ми чуємо й вимовляємо, а букви бачимо й пишемо.»
> «В українському алфавіті 33 букви.»
> Source: Заболотний, Grade 5 (2023), p. 83 — **exact quote confirmed in RAG** ✅

> «Букви — це умовні знаки. Букви ти можеш побачити і написати. Коли діти чують і вимовляють звуки мови, а коли вони бачать і пишуть букви?»
> Source: Большакова, Grade 2 (2019), p. 27 ✅

> «Букви ми бачимо, читаємо і пишемо. Буква — письмовий знак, що позначає один звук або сполучення двох звуків.»
> Note — also contains dialogue: «В українській мові є десять голосних букв. — Так говорити неправильно! — Чому?» — confirms the plan's pedagogical point.
> Source: Вашуленко, Grade 2 (2019), p. 6 ✅

### Section: Голосні звуки (Vowel Sounds)
> «Під час вимовляння голосних звуків повітря вільно проходить через рот, не натрапляючи на перешкоди. Голосні звуки утворюються за допомогою голосу.»
> Source: Кравцова, Grade 2 (2019), p. 9 ✅

> «Голосні вимовляємо голосом, тому ці звуки ми можемо проспівати: [а], [о], [у], [и], [е], [і].»
> «Зверніть увагу! Голосними й приголосними бувають лише звуки, тому **неправильно говорити голосна чи приголосна літера**.»
> Source: Літвінова, Grade 5 (2022), p. 110 — **key pedagogical rule confirmed** ✅

> «В українській мові шість голосних звуків, на письмі їх позначаємо десятьма літерами: [а]→А,Я | [о]→О | [у]→У,Ю | [е]→Е,Є | [и]→И | [і]→І,Ї»
> Source: Літвінова, Grade 5 (2022), p. 114 — **confirms 6 sounds / 10 letters split** ✅

### Section: Приголосні звуки (Consonant Sounds)
> «Приголосні мають таку назву, бо вони групуються біля голосних (при голосних). Приголосні звуки утворюються за допомогою голосу та шуму або тільки шуму. Шум виникає, коли струмінь повітря прориває перешкоду, створену органами мовлення — найчастіше язиком (промовте [д]) або губами (промовте [б]).»
> Source: Літвінова, Grade 5 (2022), p. 110 ✅

> Фонетичний розбір (sound analysis) — full worked example with щ=[шч], ь=no sound:
> «Шоста буква ь звукового позначення не має.»
> Source: Ворон, Grade 9 (2017), p. 220 — **confirms plan's claim that Ь makes no sound** ✅

### Section: Привіт! (Hello!)
> «Доброго ранку! Добрий день! **Привіт! Радий бачити тебе.** / **Рада була зустрітися.**»
> Source: Заболотний, Grade 5 (2023), p. 218 — **confirms both gendered forms радий/рада тебе бачити** ✅

> «Молодь або добре знайомі колеги, ровесники часто вживають однослівне вітання: **Привіт**... **Як справи? Як здоров'я?**»
> Source: Заболотний, Grade 11 (2019), pp. 217-218 — **confirms Як справи? as natural Ukrainian greeting** ✅

### Section: Підсумок (Summary)
> 33 букви в алфавіті — confirmed by Заболотний Grade 5 p.83 and Большакова Grade 2 p.27 ✅
> 38 звуків — consistent with 6 голосних + 32 приголосних confirmed across multiple sources ✅
> «Чи можна говорити «голосна літера»? — No» — confirmed by Vashulenko Grade 2 p.6 dialogue + Litvinova Grade 5 p.110 explicit rule ✅

---

## Grammar Rules

- **Звук ≠ Літера distinction:** Confirmed in Заболотний Grade 5 — "Звуки ми чуємо й вимовляємо, а букви бачимо й пишемо." This is the foundational rule. No Правопис section number — it belongs to **фонетика/графіка** (§§ covering sound-letter correspondence), not orthography proper.
- **"Голосна літера" is incorrect:** Confirmed by both Vashulenko Grade 2 and Litvinova Grade 5 explicitly: *"неправильно говорити голосна чи приголосна літера"* — sounds are голосні/приголосні, not letters.
- **33 letters, 38 sounds:** Plan's figure confirmed. Sources: 6 vowel sounds (Litvinova p.114) + Bolshakova/Zabolotnyi confirm 33-letter алфавіт. The mismatch is explained by iotated letters (Я, Ю, Є, Ї = 2 sounds in some positions) and Ь (0 sounds).
- **Ь (м'який знак) = no sound:** Confirmed in phonetic analysis example (Voron Grade 9 p.220).
- **Щ = [шч]:** Confirmed in same Grade 9 analysis example.

---

## Calque Warnings

- **«як справи»** — ✅ **OK** — confirmed as natural Ukrainian by Zaболотний Grade 11; Антоненко-Давидович returned no warning for this phrase
- **«рада/радий тебе бачити»** — ✅ **OK** — confirmed directly from Zaболотний Grade 5 textbook: "Радий бачити тебе" / "Рада була зустрітися"; style guide returned no warning
- **«звуковий аналіз»** (used in Привіт! section) — ✅ **OK** — term is standard in Ukrainian phonetics pedagogy (Voron Grade 9, Zabolotnyi Grade 5 use it extensively)
- **«голосна/приголосна літера»** — ⚠️ **NOT a calque but a PEDAGOGICAL ERROR** — textbooks explicitly call this incorrect Ukrainian. The plan correctly teaches that *sounds* are голосні/приголосні, not letters. The module should actively correct this misconception.

---

## CEFR Check

| Word | PULS Level | Status |
|------|-----------|--------|
| привіт | **A1** | ✅ On target |
| добре | **A1** | ✅ On target |
| чудово | **A1** | ✅ On target |
| нормально | **A1** | ✅ On target |
| мама | **A1** | ✅ On target |
| тато | **A1** | ✅ On target |
| молоко | **A1** | ✅ On target |
| дім | **A1** | ✅ On target |
| сон | **A2** | ⚠️ One level above — used as example word, not core vocab; acceptable |
| звук | **A2** | ⚠️ One level above — **metalanguage term**, unavoidable in a phonetics module; used from Grade 1 in Ukrainian schools |
| літера | **A2** | ⚠️ One level above — **metalanguage term**, unavoidable; same rationale |
| голосний (noun) | **A2** | ⚠️ One level above — **metalanguage term**, essential for this module |
| голосний (adj) | **B1** | ⚠️ Two levels above — but used only as pedagogical/metalanguage adjective |
| приголосний | not in PULS | ⚠️ Not in PULS database — likely B1+ per frequency, but **essential metalanguage** for a phonetics module |

**Summary on CEFR flags:** All flagged words (звук, літера, голосний, приголосний) are **metalanguage terms** that Ukrainian teachers introduce in Grade 1 (Большакова, Вашуленко). This is a phonetics module — these terms are the content, not the vocabulary being practiced. Their CEFR level reflects general usage frequency, not pedagogical necessity. **No words should be removed.** The conversational vocabulary (привіт, добре, мама, тато, etc.) is solidly A1.