# A2 Naturalness Scan Report - M45-M56

**Date:** 2026-01-12
**Protocol:** claude_extensions/protocols/a1-naturalness-scan.md
**Scope:** M45-M56 (12 modules - Vocabulary section)

---

## Executive Summary

**Total modules:** 12
**Prose activities found:** 12 modules with multi-sentence prose
**Flagged for naturalness issues:** 7 modules
**Checkpoints deferred:** 1 module (M56)

---

## Scan Results by Module

### M45: Food and Cooking [⚠️ FLAGGED]

**Status:** MIXED - First passage disconnected, second coherent
**Activities:** Two cloze passages

**Passage 1: "Cooking Methods" (lines 31-37):**
```
Я варю картоплю 20 хвилин. Вона смажить м'ясо на сковороді. Він пече хліб у духовці. Я нарізаю цибулю на дошці. Суп варять у каструлі. Смаж м'ясо на сковороді. Пиріг печуть у духовці. Молоко тримають в холодильнику. Вона тушкує овочі в каструлі. Ми готуємо вечерю разом. Він закип'ячує воду для чаю. Бабуся запікає курку в духовці.
```

**Naturalness Analysis:**
- Subject consistency: ❌ (я → вона → він → я → impersonal → imperative → impersonal → impersonal → вона → ми → він → бабуся, chaotic shifts)
- Discourse markers: ❌ (completely absent)
- Topic coherence: ❌ (potato → meat → bread → onion → soup → pie → milk → vegetables → dinner → water → chicken, random cooking actions)
- Pedagogical focus: ⚠️ (drill for cooking methods, but too disconnected)

**Passage 2: "Recipe Story" (lines 41-63):**
```
Бабуся готує борщ. Спочатку наріж овочі. Потім смаж цибулю. Поклади все в каструлю. Тушкуй борщ дві години. Печи пампушки в духовці...
```
**Naturalness Analysis:**
- Subject consistency: ✅ (бабуся cooking, imperative instructions)
- Discourse markers: ✅ (спочатку, потім)
- Topic coherence: ✅ (making borщ)

**Overall Score:** 6/10 (Passage 1: 5/10, Passage 2: 8/10)

**Fix approach:** Replace Passage 1 with coherent kitchen scene showing family cooking together
**Vocabulary constraint:** M01-M45
**Grammar constraint:** Cooking verbs (варити, смажити, пекти, тушкувати, нарізати)

---

### M46: Home and Furniture [⚠️ FLAGGED]

**Status:** MIXED - First passage disconnected, second coherent
**Activities:** Two cloze passages

**Passage 1: "Home Vocabulary" (lines 31-37):**
```
Я сплю у спальні. Ми їмо на кухні. Сідай на диван, там зручно.

Книги стоять на полиці. Одяг висить у шафі. Тато працює в кабінеті.

Білизна в пральній машині. Прибираю пилососом. Мама готує їжу на плиті.

Квіти стоять на підвіконні. Діти граються на килимі. Посуд миємо в мийці.
```

**Naturalness Analysis:**
- Subject consistency: ❌ (я → ми → ти → книги → одяг → тато → білизна → я → мама → квіти → діти → ми, chaotic)
- Discourse markers: ❌ (absent)
- Topic coherence: ❌ (sleeping → eating → sitting → books → clothes → work → laundry → cleaning → cooking → flowers → playing → dishes)
- Redundancy: ⚠️ (disconnected household facts)

**Passage 2: "Story Comprehension" (lines 41-63):**
```
Ольга переїхала в нову квартиру. У вітальні є диван і два крісла. На кухні нова плита і холодильник...
```
**Naturalness Analysis:**
- Subject consistency: ✅ (Ольга and her new apartment)
- Topic coherence: ✅ (moving to new place, describing rooms)

**Overall Score:** 6/10 (Passage 1: 5/10, Passage 2: 8/10)

**Fix approach:** Replace Passage 1 with family describing their home during visit
**Vocabulary constraint:** M01-M46
**Grammar constraint:** Home vocabulary (rooms, furniture, appliances)

---

### M47: Nature and Weather [✅ PASS]

**Status:** Coherent geography narrative
**Activities:** Fill-in + Story Comprehension (lines 175-181)

**Sample:**
```
Україна має чудову природу. На заході є високі гори Карпати. Там взимку падає сніг і люди катаються на лижах. На півдні є Чорне море. Влітку там дуже сонячно і тепло...
```

**Naturalness Analysis:**
- Subject consistency: ✅ (Ukraine's geography)
- Discourse markers: ✅ (на заході, на півдні, влітку, восени)
- Topic coherence: ✅ (Ukrainian nature and seasons)

**Score:** 8/10 (Good - coherent geographical narrative)

---

### M48: Emotions & Personality [⚠️ FLAGGED]

**Status:** MIXED - First passage disconnected, second coherent
**Activities:** Two cloze passages

**Passage 1: "Complete the Sentences" (lines 86-93):**
```
Я дуже радий бачити тебе! Вона сумує за своїм другом. Діти раділи подарункам.

Він боїться темряви. Мама хвилюється за дітей. Вона дуже добра людина.

Він завжди чесний з друзями. Сміливі люди змінюють світ. Я задоволений результатом іспиту.

Вона стурбована новинами з дому. Ми дивувалися його таланту. Він був сміливим воїном.
```

**Naturalness Analysis:**
- Subject consistency: ❌ (я → вона → діти → він → мама → вона → він → люди → я → вона → ми → він)
- Discourse markers: ❌ (absent)
- Topic coherence: ❌ (meeting → missing friend → gifts → fear → worry → character → honesty → bravery → exam → news → talent → warrior)
- Structure: ❌ (random emotion examples)

**Passage 2: "Story Completion" (lines 384-399):**
```
Марійка мала чудовий характер. Вона була дуже доброю людиною. Одного дня подруга Марійки сумувала. Її кіт загубився...
```
**Naturalness Analysis:**
- Subject consistency: ✅ (Marійka helping friend find lost cat)
- Topic coherence: ✅ (kindness and helping)

**Overall Score:** 6/10 (Passage 1: 5/10, Passage 2: 8/10)

**Fix approach:** Replace Passage 1 with coherent emotional journey or school day
**Vocabulary constraint:** M01-M48
**Grammar constraint:** Emotion verbs and personality adjectives

---

### M49: Work & Professions [✅ PASS]

**Status:** Coherent career narrative
**Activities:** Career Ladder cloze (lines 470-483)

**Sample:**
```
Максим почав свою кар'єру в маленькій фірмі. Він працював програмістом. Його начальник був дуже розумним. Максим хотів заробляти багато грошей. Він працював старанно. Через рік його найняли новим менеджером...
```

**Naturalness Analysis:**
- Subject consistency: ✅ (Максим's career)
- Discourse markers: ✅ (через рік, тепер, влітку, нарешті)
- Topic coherence: ✅ (career progression)

**Score:** 8/10 (Good - coherent career story)

---

### M50: Technology & Media [⚠️ FLAGGED]

**Status:** MIXED - First passage disconnected, second coherent
**Activities:** Two cloze passages

**Passage 1: "Tech Sentences" (lines 115-121):**
```
Я забув свій пароль. Надішли мені посилання на це відео. Він купив новий ноутбук.

Вона пише цікавий блог. Ми читаємо новини в інтернеті. У мене розбився екран телефона.

Я завантажую файл з інтернету. Це мій улюблений сайт. Ти читав цю статтю?

Тут поганий зв'язок. Він завжди онлайн. Постав мені лайк!
```

**Naturalness Analysis:**
- Subject consistency: ❌ (я → ти (imperative) → він → вона → ми → у мене → я → це → ти → тут → він → ти)
- Discourse markers: ❌ (absent)
- Topic coherence: ❌ (password → link → laptop → blog → news → broken screen → download → website → article → connection → online → like)
- Structure: ❌ (random tech problems/actions)

**Passage 2: "Digital Morning" (lines 388-400):**
```
Мій ранок починається зі смартфона. Я вимикаю будильник на екрані. Потім я перевіряю пошту і читаю новини...
```
**Naturalness Analysis:**
- Subject consistency: ✅ (morning routine with devices)
- Discourse markers: ✅ (потім, ввечері)
- Topic coherence: ✅ (digital morning routine)

**Overall Score:** 6/10 (Passage 1: 5/10, Passage 2: 8/10)

**Fix approach:** Replace Passage 1 with coherent tech problem day or workspace scene
**Vocabulary constraint:** M01-M50
**Grammar constraint:** Tech vocabulary (комп'ютер, інтернет, пароль, etc.)

---

### M51: Hobbies & Leisure [⚠️ FLAGGED]

**Status:** MIXED - First passage disconnected, second coherent
**Activities:** Two cloze passages

**Passage 1: "My Hobbies" (lines 155-161):**
```
Я люблю грати на гітарі. Вона малює красиві картини. Ми йдемо в кіно на новий фільм.

Це моє улюблене хобі. У мене є два квитки на концерт. Ми оглядаємо старий замок.

Він колекціонує марки. Я хочу подорожувати світом. Артист стоїть на сцені.

Ми спимо в наметі. Це цікава виставка. Глядачі аплодують.
```

**Naturalness Analysis:**
- Subject consistency: ❌ (я → вона → ми → це → у мене → ми → він → я → артист → ми → це → глядачі)
- Discourse markers: ❌ (absent)
- Topic coherence: ❌ (guitar → painting → cinema → hobby → concert → castle → stamps → travel → stage → tent → exhibition → applause)
- Structure: ❌ (random hobby examples)

**Passage 2: "Cultural Weekend" (lines 461-473):**
```
У суботу ми поїхали на дачу. Там ми робили шашлик. Ми співали пісні і грали на гітарі. У неділю ми пішли в кіно...
```
**Naturalness Analysis:**
- Subject consistency: ✅ (weekend activities)
- Discourse markers: ✅ (у суботу, у неділю, потім, ввечері)
- Topic coherence: ✅ (weekend cultural activities)

**Overall Score:** 6/10 (Passage 1: 5/10, Passage 2: 8/10)

**Fix approach:** Replace Passage 1 with friends planning weekend activities together
**Vocabulary constraint:** M01-M51
**Grammar constraint:** Hobby vocabulary (малювати, співати, подорожувати, etc.)

---

### M52: Education & Learning [✅ PASS]

**Status:** Coherent university narrative
**Activities:** University Day cloze (lines 554-570)

**Sample:**
```
Я — студент. Я вчуся в університеті. Сьогодні у мене перша лекція о 9:00. Професор читає цікавий матеріал, а я пишу конспект у зошит. Мій улюблений предмет — історія...
```

**Naturalness Analysis:**
- Subject consistency: ✅ (student's day)
- Discourse markers: ✅ (сьогодні, у червні, ввечері, завтра)
- Topic coherence: ✅ (university life)

**Score:** 8/10 (Good - coherent student narrative)

---

### M53: Shopping & Services [⚠️ FLAGGED]

**Status:** MIXED - First passage disconnected, second coherent
**Activities:** Two cloze passages

**Passage 1: "Shopping Sentences" (lines 155-161):**
```
Я хочу купити хліб. Скільки це коштує? У мене немає готівки.

Я плачу карткою. Це велика черга. Дайте, будь ласка, чек.

Ось ваша решта. Ми йдемо на ринок. Я хочу поміряти ці джинси.

Сьогодні у магазині знижка. Можна замовити піцу? Банк закритий, він не працює.
```

**Naturalness Analysis:**
- Subject consistency: ❌ (я → це → у мене → я → це → imperative → ваша → ми → я → сьогодні → impersonal → банк)
- Discourse markers: ❌ (absent)
- Topic coherence: ❌ (bread → price → cash → card → queue → receipt → change → market → jeans → discount → pizza → bank)
- Structure: ❌ (random shopping situations)

**Passage 2: "At the Supermarket" (lines 458-475):**
```
Я беру кошик і йду в зал. Мені треба купити молоко і хліб. Я дивлюся на ціну. Молоко коштує 40 гривень. Я йду на касу...
```
**Naturalness Analysis:**
- Subject consistency: ✅ (shopping trip)
- Discourse markers: ✅ (потім, вдома)
- Topic coherence: ✅ (supermarket shopping)

**Overall Score:** 6/10 (Passage 1: 5/10, Passage 2: 8/10)

**Fix approach:** Replace Passage 1 with market shopping narrative or service visit
**Vocabulary constraint:** M01-M53
**Grammar constraint:** Shopping vocabulary (купити, платити, ціна, etc.)

---

### M54: Sports & Fitness [✅ PASS]

**Status:** Coherent football match narrative
**Activities:** Football Match cloze (lines 548-575)

**Sample:**
```
Ми на стадіоні. Сьогодні матч. Грають «Динамо» і «Шахтар». Я — вболівальник «Динамо». Мій друг каже: «Дивись, який пас!». Суддя дає жовту картку. Наш гравець забиває гол!...
```

**Naturalness Analysis:**
- Subject consistency: ✅ (attending football match)
- Discourse markers: ✅ (сьогодні, на стадіоні, потім)
- Topic coherence: ✅ (football match experience)

**Score:** 8/10 (Good - coherent sports narrative)

---

### M55: Health & Body [⚠️ FLAGGED]

**Status:** MIXED - First passage disconnected, second coherent
**Activities:** Two cloze passages

**Passage 1: "My Symptoms" (lines 155-161):**
```
У мене болить голова. У нього висока температура. Мені треба купити ліки.

У неї болить зуб. Викличіть лікаря! Я п'ю таблетки.

У мене сильний кашель. Болять очі. Це ліки від грипу.

Де тут аптека? Лікар дав рецепт. У мене болить спина.
```

**Naturalness Analysis:**
- Subject consistency: ❌ (у мене → у нього → мені → у неї → imperative → я → у мене → impersonal → це → де → лікар → у мене)
- Discourse markers: ❌ (absent)
- Topic coherence: ❌ (head → fever → medicine → tooth → doctor → pills → cough → eyes → flu → pharmacy → prescription → back)
- Structure: ❌ (random symptoms and health situations)

**Passage 2: "Call the Doctor" (lines 461-478):**
```
— Алло, це швидка? Так, оператор слухає. Що сталося?
— Моєму чоловіку погано. У нього сильний біль в грудях і важко дихати...
```
**Naturalness Analysis:**
- Subject consistency: ✅ (emergency call dialogue)
- Discourse markers: ✅ (потім, через 10 хвилин)
- Topic coherence: ✅ (calling ambulance for husband)

**Overall Score:** 6/10 (Passage 1: 5/10, Passage 2: 8/10)

**Fix approach:** Replace Passage 1 with doctor visit narrative or family illness story
**Vocabulary constraint:** M01-M55
**Grammar constraint:** Health vocabulary (болить, температура, ліки, etc.)

---

### M56: Checkpoint Vocabulary [⏸️ DEFERRED]

**Status:** CHECKPOINT - different standards apply
**Activities:** Comprehensive vocabulary review integrating M45-M55
**Naturalness Analysis:**
- Checkpoint integrates all M45-M55 thematic vocabulary
- Mixed topics expected for comprehensive testing
- Acceptable 6-7/10 for assessment purposes

**Score:** 7/10 (Deferred - checkpoint standards)

---

## Summary by Status

### ✅ PASS (4 modules)

- M47: Nature and Weather (score 8/10)
- M49: Work & Professions (score 8/10)
- M52: Education & Learning (score 8/10)
- M54: Sports & Fitness (score 8/10)

### ⚠️ FLAGGED (7 modules)

- **M45: Food and Cooking (score 6/10)** - First passage disconnected (5/10)
- **M46: Home and Furniture (score 6/10)** - First passage disconnected (5/10)
- **M48: Emotions & Personality (score 6/10)** - First passage disconnected (5/10)
- **M50: Technology & Media (score 6/10)** - First passage disconnected (5/10)
- **M51: Hobbies & Leisure (score 6/10)** - First passage disconnected (5/10)
- **M53: Shopping & Services (score 6/10)** - First passage disconnected (5/10)
- **M55: Health & Body (score 6/10)** - First passage disconnected (5/10)

### ⏸️ DEFERRED (1 module)

- M56: Checkpoint (score 7/10) - Checkpoint standards apply

---

## Recommended Actions

### Priority 1: Fix All Disconnected First Passages

**M45 - Food and Cooking (Passage 1):**
- Replace disconnected cooking actions with family preparing holiday meal together
- Create scene where family members cook different dishes for celebration
- Add discourse markers (спочатку, потім, тим часом, нарешті)
- Keep "Recipe Story" passage (already 8/10)

**M46 - Home and Furniture (Passage 1):**
- Replace disconnected household facts with family showing home to guests
- Create narrative about visitors touring the house, describing each room
- Use discourse markers (ось, тут, там, а це)
- Keep "Story Comprehension" passage (already 8/10)

**M48 - Emotions & Personality (Passage 1):**
- Replace disconnected emotion examples with school day emotional journey
- Create narrative about student's day with different feelings and reactions
- Add discourse markers (спочатку, потім, але, тому)
- Keep "Story Completion" passage (already 8/10)

**M50 - Technology & Media (Passage 1):**
- Replace disconnected tech examples with workday tech problems
- Create narrative about person dealing with various technology issues
- Add discourse markers (спочатку, потім, також, нарешті)
- Keep "Digital Morning" passage (already 8/10)

**M51 - Hobbies & Leisure (Passage 1):**
- Replace disconnected hobby examples with friends planning weekend
- Create dialogue/narrative about group discussing their weekend plans
- Add discourse markers (спочатку, потім, а ти, а я)
- Keep "Cultural Weekend" passage (already 8/10)

**M53 - Shopping & Services (Passage 1):**
- Replace disconnected shopping examples with market shopping trip
- Create narrative about person going to market, buying items, paying
- Add discourse markers (спочатку, потім, після цього, нарешті)
- Keep "At the Supermarket" passage (already 8/10)

**M55 - Health & Body (Passage 1):**
- Replace disconnected symptoms with family flu story
- Create narrative about family members getting sick and helping each other
- Add discourse markers (спочатку, потім, теж, тому)
- Keep "Call the Doctor" passage (already 8/10)

---

## Vocabulary & Grammar Constraints

All fixes must use:
- **Vocabulary:** Only words from M01-M{current module}
- **Grammar:** Only constructs taught up to current module

**M45 constraints:**
- Vocabulary: M01-M45 cumulative
- Grammar: Cooking verbs (варити, смажити, пекти, тушкувати, нарізати, запікати)

**M46 constraints:**
- Vocabulary: M01-M46 cumulative
- Grammar: Locative case for rooms/locations, household verbs

**M48 constraints:**
- Vocabulary: M01-M48 cumulative
- Grammar: Emotion verbs (радіти, сумувати, боятися, хвилюватися), personality adjectives

**M50 constraints:**
- Vocabulary: M01-M50 cumulative
- Grammar: Tech vocabulary (комп'ютер, інтернет, пароль, посилання, завантажувати)

**M51 constraints:**
- Vocabulary: M01-M51 cumulative
- Grammar: Hobby verbs (малювати, співати, танцювати, подорожувати, колекціонувати)

**M53 constraints:**
- Vocabulary: M01-M53 cumulative
- Grammar: Shopping verbs (купувати, платити, міряти), Instrumental for means of payment

**M55 constraints:**
- Vocabulary: M01-M55 cumulative
- Grammar: Health construction "У мене болить + Nom", body parts, medical vocabulary

---

## Next Steps

1. **Validate vocabulary for each fix** using `/tmp/query_a2_vocab.py`
2. **Create fixes for M45, M46, M48, M50, M51, M53, M55** (all priority 1)
3. **Apply all fixes**
4. **Commit with detailed message**

---

## Comparison with Previous Batches

**M01-M11 Results:**
- Flagged: 5 modules (45%)
- Critical errors: 2
- Average score after fixes: 8.2/10

**M12-M25 Results:**
- Flagged: 4 modules (29%)
- Critical errors: 2
- Average score after fixes: 8.2/10

**M26-M35 Results:**
- Flagged: 3 modules (30%)
- Critical errors: 1
- Average score after fixes: 8.0/10

**M36-M44 Results:**
- Flagged: 4 modules (44%)
- Critical errors: 0
- Average score after fixes: 8.0/10 (estimated)

**M45-M56 Results:**
- Flagged: 7 modules (64% of non-checkpoint)
- Critical errors: 0 (all are pedagogical drill disconnection, not corruption)
- Current average score: 6.5/10 (before fixes)

**Pattern:** M45-M56 has highest flagged percentage (64%) but NO critical corruption errors. All issues are identical - pedagogical drills needing better context. Each flagged module has ONE disconnected passage and ONE good passage, making fixes straightforward - replace first passage, keep second.

**Vocabulary section pattern:** Thematic modules (Food, Home, Nature, Work, etc.) tend to start with disconnected vocabulary drills, then provide coherent contextual narratives. This is systematic across all 7 flagged modules.
