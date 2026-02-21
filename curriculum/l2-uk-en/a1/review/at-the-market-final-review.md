Now I have all the data. Let me compile the full adversarial review.

---

## Phase 9 Final QA Review: at-the-market (a1-37)

### Issues Found

**1. IPA inaccuracy — домашнє** (content line 41)
- Text: `**домашнє** [doˈmɑʃnʲe]`
- Ukrainian є represents [ɛ], never [e]. Ukrainian phonology has no close-mid front vowel.
- Correct: `[doˈmɑʃnʲɛ]`

**2. LLM artifact — "Це не просто X" pattern** (content lines 17, 34)
- Three occurrences of the same rhetorical pattern:
  - Line 17: "Це не просто торгівля — це культура"
  - Line 34: "Це не просто ринок. Це театр."
  - Line 271: "Ринок — це не магазин" (variation, acceptable in narrative)
- Classic LLM repetition. Reducing first two to varied phrasing.

**3. PLAN COMPLIANCE — Missing numerals 2-4 pattern** (plan section 3, bullet 1)
- Plan source-of-truth explicitly requires: *"Типова помилка: відмінювання після числівників 2-4 — вправа на корекцію форми «Два кілограм» на правильну «Два кілограми» (Nom.Pl) у порівнянні з «П'ять кілограмів» (Gen.Pl)."*
- Plan vocabulary_hints.required for кілограм specifies: *"два кілограми (Nom.Pl), п'ять кілограмів (Gen.Pl)"*
- The form "п'ять кілограмів" appears NOWHERE in the content. The numerals pattern is completely absent.
- This is the #1 cause of learner error at the market and the plan specifically targets it.

**4. PLAN COMPLIANCE — Missing required idiom "тільки з грядки"** (plan vocabulary_hints.required)
- Plan specifies for свіжий: *"ідіома «тільки з грядки» (fresh from the garden)"*
- Plan dialogue section also mentions: *"колоритних фразеологізмів, як-от «тільки з грядки»"*
- This idiom appears NOWHERE in the content. It's listed as required vocabulary.

**5. Activities use untaught vocabulary** (activities lines 13-20)
- Match-up "Одиниці виміру" includes **літр**, **пакет**, **пляшка** as units.
- The prose only teaches: кілограм, грам, пучок, штука.
- Activities should reinforce taught material, not silently introduce new vocabulary.
- Fix: add these three units to the prose vocabulary section.

**6. Vocabulary YAML format deficiency** (vocabulary file)
- Uses `items:` dictionary wrapper instead of bare list at root.
- Missing IPA transcriptions (every other A1 vocabulary file includes them).
- Inconsistent with standard format (compare: `around-the-city.yaml`, `the-living-verb-i.yaml`).

**7. Plan section 3 "Мовні помилки та практика" absent as coherent section**
- The plan's source-of-truth has a dedicated 450-word section for learner errors.
- The meta reorganized it away. Content has no error-correction framing.
- The numerals fix (issue #3) partially addresses this. The здача/решта distinction is briefly touched on in the payment section (acceptable for A1).

### Verification Passed (No Issues)

- **All Genitive forms correct**: картоплі, моркви, цибулі, яблук, помідорів, огірків, капусти, груш
- **All adjective gender agreements correct** in prose and activities
- **IPA tie bars present** on all affricates: t͡s, t͡ʃ
- **ʋ used for В**, ɦ used for Г consistently
- **No Russianisms detected** (no кушати, получати, приймати участь, слідуючий)
- **No Russian characters** (ы, э, ё, ъ) found
- **Historical facts verified**: Bessarabskyi market 1912, Pryvoz 1827, Khreshchatyk location
- **Unjumble activities**: all word arrays contain all answer tokens
- **Fill-in activities**: all answers produce grammatical sentences
- **No forward references** to unreachable grammar beyond A1

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/at-the-market.md
---OLD---
Ukrainians value food that is **домашнє** [doˈmɑʃnʲe] (homemade).
---NEW---
Ukrainians value food that is **домашнє** [doˈmɑʃnʲɛ] (homemade).
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/at-the-market.md
---OLD---
**Ринок — це життя, це серце міста.** (Market is life, the heart of the city.) **Це не просто торгівля — це культура.** (It is not just trade — it is culture.)
---NEW---
**Ринок — це життя, це серце міста.** (Market is life, the heart of the city.) **Торгівля тут — це справжнє мистецтво.** (Trade here is a real art.)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/at-the-market.md
---OLD---
**А ось Привоз в Одесі.** (And here is Pryvoz in Odesa.) **Це не просто ринок. Це театр.** (It is not just a market. It is a theater.) Established in 1827,
---NEW---
**А ось Привоз в Одесі.** (And here is Pryvoz in Odesa.) **Привоз — це справжній театр.** (Pryvoz is a real theater.) Established in 1827,
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/at-the-market.md
---OLD---
**Домашня їжа — це найкраща їжа.** (Homemade food is the best food.) **Морква з городу смачніша.** (Carrot from the garden is tastier.) We believe that mass-produced food has less flavor.
---NEW---
**Домашня їжа — це найкраща їжа.** (Homemade food is the best food.) **Морква з городу смачніша.** (Carrot from the garden is tastier.) On a market you will hear: **«Тільки з грядки!»** (Straight from the garden bed!) — this means the product is as fresh as possible. We believe that mass-produced food has less flavor.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/at-the-market.md
---OLD---
**штука** [ˈʃtukɑ] — piece / item
Used when you buy things individually, like eggs or large fruits. **Це для яєць або фруктів.** (This is for eggs or fruits.)

### The "Kilogram" Pattern
---NEW---
**штука** [ˈʃtukɑ] — piece / item
Used when you buy things individually, like eggs or large fruits. **Це для яєць або фруктів.** (This is for eggs or fruits.)

**літр** [lʲitr] — liter
Used for liquids: milk, juice, oil. **Це для молока, соку, олії.** (This is for milk, juice, oil.)

**пляшка** [ˈplʲɑʃkɑ] — bottle
A bottle of water or oil. **Пляшка олії або води.** (A bottle of oil or water.)

**пакет** [pɑˈkɛt] — packet / bag
Used for juice or a bag of goods. **Це для соку або покупок.** (This is for juice or purchases.)

### The "Kilogram" Pattern
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/at-the-market.md
---OLD---
> [!tip]
> **Memorize the Chunk**
> Don't think about grammar rules yet. Just memorize "кілограм картоплі" as one single vocabulary item. It sounds like a rhyme!

### Asking the Price
---NEW---
> [!tip]
> **Memorize the Chunk**
> Don't think about grammar rules yet. Just memorize "кілограм картоплі" as one single vocabulary item. It sounds like a rhyme!

### Numbers + кілограм
**Числа змінюють слово.** (Numbers change the word.) Pay attention to how "кілограм" changes with different numbers:

| Number | Form | Example |
|--------|------|---------|
| **1** | кілограм | один **кілограм** картоплі |
| **2, 3, 4** | кілограми | два **кілограми** яблук |
| **5+** | кілограмів | п'ять **кілограмів** помідорів |
| **½** | пів кілограма | пів **кілограма** сиру |

> [!warning]
> **Common Error**
> WRONG: «Два кілограм помідорів»
> CORRECT: «Два кілограми помідорів»
> **Два, три, чотири + кілограми.** (Two, three, four + кілограми.) **П'ять і більше + кілограмів.** (Five and more + кілограмів.)

### Asking the Price
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/vocabulary/at-the-market.yaml
---OLD---
items:
  - lemma: "ринок"
    translation: "market"
    pos: "noun"
    gender: "m"
    example: "Я йду на ринок."
  - lemma: "кілограм"
    translation: "kilogram"
    pos: "noun"
    gender: "m"
    example: "Один кілограм картоплі."
  - lemma: "грам"
    translation: "gram"
    pos: "noun"
    gender: "m"
    example: "Двісті грам сиру."
  - lemma: "штука"
    translation: "piece / item"
    pos: "noun"
    gender: "f"
    example: "Одна штука."
  - lemma: "пучок"
    translation: "bunch (of greens)"
    pos: "noun"
    gender: "m"
    example: "Пучок петрушки."
  - lemma: "свіжий"
    translation: "fresh"
    pos: "adj"
    example: "Свіжий хліб."
  - lemma: "овочі"
    translation: "vegetables"
    pos: "noun"
    notes: "always plural"
  - lemma: "фрукти"
    translation: "fruits"
    pos: "noun"
    notes: "usually plural"
  - lemma: "скільки"
    translation: "how much / how many"
    pos: "adv"
    usage: "Скільки коштує?"
  - lemma: "дайте"
    translation: "give (imperative, polite)"
    pos: "verb"
    usage: "Дайте, будь ласка..."
  - lemma: "здача"
    translation: "change (money)"
    pos: "noun"
    gender: "f"
    example: "Ваша здача."
  - lemma: "продавець"
    translation: "vendor / seller"
    pos: "noun"
    gender: "m"
  - lemma: "яблуко"
    translation: "apple"
    pos: "noun"
    gender: "n"
  - lemma: "картопля"
    translation: "potato"
    pos: "noun"
    gender: "f"
    notes: "usually singular in Ukrainian (collective)"
  - lemma: "помідор"
    translation: "tomato"
    pos: "noun"
    gender: "m"
  - lemma: "огірок"
    translation: "cucumber"
    pos: "noun"
    gender: "m"
  - lemma: "морква"
    translation: "carrot"
    pos: "noun"
    gender: "f"
    notes: "usually singular (collective)"
  - lemma: "цибуля"
    translation: "onion"
    pos: "noun"
    gender: "f"
    notes: "usually singular (collective)"
  - lemma: "смачний"
    translation: "tasty / delicious"
    pos: "adj"
  - lemma: "солодкий"
    translation: "sweet"
    pos: "adj"
  - lemma: "стиглий"
    translation: "ripe"
    pos: "adj"
  - lemma: "готівка"
    translation: "cash"
    pos: "noun"
    gender: "f"
  - lemma: "зважте"
    translation: "weigh (imperative, polite)"
    pos: "verb"
    usage: "Зважте, будь ласка..."
---NEW---
- ipa: '[ˈrɪnɔk]'
  lemma: ринок
  pos: noun
  gender: m
  translation: market
  example: "Я йду на ринок."
- ipa: '[kʲiloˈɦrɑm]'
  lemma: кілограм
  pos: noun
  gender: m
  translation: kilogram
  example: "Один кілограм картоплі."
- ipa: '[ɦrɑm]'
  lemma: грам
  pos: noun
  gender: m
  translation: gram
  example: "Двісті грам сиру."
- ipa: '[ˈʃtukɑ]'
  lemma: штука
  pos: noun
  gender: f
  translation: piece / item
  example: "Одна штука."
- ipa: '[puˈt͡ʃɔk]'
  lemma: пучок
  pos: noun
  gender: m
  translation: bunch (of greens)
  example: "Пучок петрушки."
- ipa: '[ˈsʋʲiʒɪj]'
  lemma: свіжий
  pos: adj
  translation: fresh
  example: "Свіжий хліб."
- ipa: '[ˈɔʋɔt͡ʃʲi]'
  lemma: овочі
  pos: noun
  translation: vegetables
  notes: always plural
- ipa: '[ˈfruktɪ]'
  lemma: фрукти
  pos: noun
  translation: fruits
  notes: usually plural
- ipa: '[ˈskʲilʲkɪ]'
  lemma: скільки
  pos: adv
  translation: how much / how many
  usage: "Скільки коштує?"
- ipa: '[ˈdɑjte]'
  lemma: дайте
  pos: verb
  translation: give (imperative, polite)
  usage: "Дайте, будь ласка..."
- ipa: '[ˈzdɑt͡ʃɑ]'
  lemma: здача
  pos: noun
  gender: f
  translation: change (money)
  example: "Ваша здача."
- ipa: '[prodɑˈʋɛt͡sʲ]'
  lemma: продавець
  pos: noun
  gender: m
  translation: vendor / seller
- ipa: '[ˈjɑblukɔ]'
  lemma: яблуко
  pos: noun
  gender: n
  translation: apple
- ipa: '[kɑrˈtɔplʲɑ]'
  lemma: картопля
  pos: noun
  gender: f
  translation: potato
  notes: usually singular in Ukrainian (collective)
- ipa: '[pomʲiˈdɔr]'
  lemma: помідор
  pos: noun
  gender: m
  translation: tomato
- ipa: '[oˈɦʲirɔk]'
  lemma: огірок
  pos: noun
  gender: m
  translation: cucumber
- ipa: '[ˈmɔrkʋɑ]'
  lemma: морква
  pos: noun
  gender: f
  translation: carrot
  notes: usually singular (collective)
- ipa: '[t͡sɪˈbulʲɑ]'
  lemma: цибуля
  pos: noun
  gender: f
  translation: onion
  notes: usually singular (collective)
- ipa: '[smɑˈt͡ʃnɪj]'
  lemma: смачний
  pos: adj
  translation: tasty / delicious
- ipa: '[soˈlɔdkɪj]'
  lemma: солодкий
  pos: adj
  translation: sweet
- ipa: '[ˈstɪɦlɪj]'
  lemma: стиглий
  pos: adj
  translation: ripe
- ipa: '[ɦoˈtʲiu̯kɑ]'
  lemma: готівка
  pos: noun
  gender: f
  translation: cash
- ipa: '[ˈzʋɑʒte]'
  lemma: зважте
  pos: verb
  translation: weigh (imperative, polite)
  usage: "Зважте, будь ласка..."
===FIX_END===

---

### Notes (not blocking)

- **Plan mentions "легенда про слона Мурзу" for Pryvoz** — absent from content. I'm not adding this because it's likely apocryphal (no reliable source) and could introduce false cultural claims. If the plan author can verify the source, it can be added later.
- **Gemini self-review gave 10/10 across all dimensions** — this is textbook score inflation. The module had real gaps (missing numerals pattern, missing required vocabulary, untaught activity items). The automated audit caught structure; the self-review missed substance.

===VERDICT===
APPROVE
===END_VERDICT===