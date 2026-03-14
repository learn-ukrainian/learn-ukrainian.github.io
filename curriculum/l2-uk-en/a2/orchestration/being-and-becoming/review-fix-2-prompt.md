# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> The review already applied some fixes. You handle what's still failing.
> You have **Edit** and **Grep** tools — fix files directly.

---

## Editing Principles

- **IMPROVE, don't destroy.** Every rewrite should teach MORE than the original, not less.
- **PRESERVE the author's intent.** If a paragraph explains something poorly, rewrite it to explain it well — don't delete it.
- **MATCH the surrounding voice.** Your rewrite should read like the original author wrote it on a better day.
- Only DELETE truly empty sentences (pure cheerleading with zero information that cannot be salvaged). This should be rare.

---

## Fix Plan (from Phase D.1 review)

## Plan Adherence Issues (Deterministic — MUST FIX)

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥12 items
  - Actual: Activity has 8 items
  - Fix: Add 4 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥12 items
  - Actual: Activity has 8 items
  - Fix: Add 4 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥12 items
  - Actual: Activity has 8 items
  - Fix: Add 4 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥12 items
  - Actual: Activity has 8 items
  - Fix: Add 4 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥12 items
  - Actual: Activity has 8 items
  - Fix: Add 4 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥12 items
  - Actual: Activity has 8 items
  - Fix: Add 4 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:quiz`
  - Expected: Plan requires ≥10 items
  - Actual: Activity has 8 items
  - Fix: Add 2 more items to 'quiz' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:match-up`
  - Expected: Plan requires ≥10 items
  - Actual: Activity has 8 items
  - Fix: Add 2 more items to 'match-up' activity


---

## Critical Issues Found

### Issue 1: Terminology Mismatch — айтівець/айтівка vs айтішник/айтішниця
- **Location**: Content lines 194, 196, 200, 205, 206, 210, 290, 313, 319 vs Vocabulary YAML and Activities YAML throughout
- **Original (content)**: 「Але в повсякденній розмові майже всі використовують слова **айтівець** (для чоловіків) та **айтівка** (для жінок).」
- **Problem**: The content teaches "айтівець/айтівка" as the colloquial IT terms, but the vocabulary YAML lists "айтішник/айтішниця" and ALL activities use "айтішник/айтішниця/айтішником/айтішницею". Both are valid VESUM words, but a learner doing activities will encounter different words than what the prose taught them. The plan specifies "айтішник / айтішниця."
- **Fix**: Align content to use айтішник/айтішниця (matching plan, vocab, and activities), or update vocab+activities to match content. Since the plan says "айтішник", content should be updated.

### Issue 2: Duplicate Word — "перекласти" appears twice
- **Location**: Line 113, Section "Презентація: Дієслова та відмінювання"
- **Original**: 「Англомовні студенти часто хочуть перекласти слово "as" перекласти словом **як**.」
- **Problem**: The word "перекласти" is duplicated, creating a broken Ukrainian sentence.
- **Fix**: Remove the first "перекласти": "Англомовні студенти часто хочуть слово "as" перекласти словом **як**." or "часто хочуть перекласти слово "as" словом **як**."

### Issue 3: "як" Calque in Reading Passage Contradicts Teaching
- **Location**: Line 266, Section "Практика та запобігання помилкам"
- **Original**: 「Вона ніколи не працювала як журналістка чи вчителька.」
- **Problem**: This reading passage uses "працювала як журналістка" — the EXACT calque the module explicitly teaches is wrong (lines 111-115, 259-262). Reading passages should model correct usage. Immediately after, line 266 correctly uses 「Вона завжди працювала економісткою в банку.」 — the contrast is confusing without any correction marker.
- **Fix**: Change to instrumental: "Вона ніколи не працювала журналісткою чи вчителькою."

### Issue 4: Translation Error
- **Location**: Line 101, Section "Презентація: Дієслова та відмінювання"
- **Original**: 「Я хочу стати хорошим юристом.」 — I will become a good lawyer.
- **Problem**: "Я хочу" means "I want", not "I will". The English gloss should be "I want to become a good lawyer."
- **Fix**: Change English translation to "I want to become a good lawyer."

### Issue 5: Missing Plan Point — "тестувальник"
- **Location**: Section "Діалоги та кар'єрні плани"
- **Problem**: The plan specifies modeling "став тестувальником" in the dialogues section, but this word does not appear anywhere in the module.
- **Fix**: Add "тестувальник" to one of the dialogues or career examples.

### Issue 6: Factual Date — 2020 vs 2019
- **Location**: Line 174, Section "Соціокультурний контекст: Фемінітиви та IT"
- **Original**: 「Український уряд у 2020 році прийняв важливу граматичну реформу.」
- **Problem**: The new Ukrainian orthography (which codified femininitives) was approved by the Cabinet of Ministers on May 22, 2019 (Resolution No. 437). The content says 2020.
- **Fix**: Change "2020 році" to "2019 році".

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 113 | 「хочуть перекласти слово "as" перекласти словом」 | 「хочуть слово "as" перекласти словом」 | Grammar (duplicate word) |
| 266 | 「не працювала як журналістка чи вчителька」 | 「не працювала журналісткою чи вчителькою」 | Calque (як + працювати) |
| 82 | 「Вона була раніше студенткою.」 | 「Раніше вона була студенткою.」 | Word order (minor) |

---

## Fix Plan to Reach 9/10 (REQUIRED if score < 9.0)

### Language: 7/10 → 9/10
**What to fix:**
1. Line 113: Remove duplicate "перекласти" — fixes broken Ukrainian sentence
2. Line 266: Change "як журналістка чи вчителька" to "журналісткою чи вчителькою" — eliminates calque contradiction
3. Line 82: Reorder to "Раніше вона була студенткою." — more natural word order

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Line 101: Fix English translation to "I want to become a good lawyer"
2. Add "тестувальник" example to one dialogue in Section "Діалоги та кар'єрні плани"

**Expected score after fix:** 9/10

### Activities: 8/10 → 9/10
**What to fix:**
1. Align айтівець/айтівка in content to айтішник/айтішниця (matching plan, vocab, activities)

**Expected score after fix:** 9/10

### Linguistic Accuracy: 7/10 → 9/10
**What to fix:**
1. Fix duplicate "перекласти" (line 113)
2. Fix "як" calque in reading passage (line 266)
3. Verify and correct "2020 році" to "2019 році" (line 174)

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 9×1.2 + 9×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.8 + 11.7 + 11.7 + 8.0 + 13.5) / 8.9
= 79.1 / 8.9 = 8.9/10
```

---

## Audit Failures (from automated re-audit)

```
Практика та запобігання помилкам (Practice and Error Prevention)                           566 /  400  ✅ (+166)
⚠️  Activity answer correctness issues: 2
⚠️ [UNJUMBLE_RUNON_SENTENCE] Build the Sentence
⚠️ [UNJUMBLE_RUNON_SENTENCE] Build the Sentence
--- STRICT GATES (Level A2) ---
❌ [REVIEW_VERDICT_FAIL] Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
• Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a2/audit/being-and-becoming-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- STATUS JSON GATE BLOCKERS ---
GATE BLOCKER: Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `Анна` (source: prose)
  ❌ `Антон` (source: prose)
  ❌ `ею` (source: prose)
  ❌ `Олеже` (source: prose)
  ❌ `Олена` (source: prose)
  ❌ `ою` (source: prose)
  ❌ `ІТ` (source: prose)
  ❌ `ІТ-сфера` (source: prose)
  ❌ `ІТ-центр` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/being-and-becoming.md`

```markdown
<!-- SCOPE
Covers: Professions, instrumental case with verbs бути, стати, працювати
Not covered:
  - Complex instrumental prepositions (з, над, під) → a2-07
-->

# Being and Becoming

> **Чому це важливо?**
>
> Today you'll learn how to talk about professions, past roles, and future goals. Being able to explain what you do, what you used to do, and what you are studying to become is essential for building relationships. By the end of this module, you'll be able to describe your career and aspirations in Ukrainian!

## Вступ
<!-- adapted from: Vashulenko, Grade 3, вправа 54 -->

> [!tip] Welcome / Вітаємо
> 
> Вітаємо вас! Коли ви знайомитеся з кимось новим в Україні, вас часто запитують про вашу професію. В українській мові професія може означати дві різні речі: **ідентичність** (identity) або **функцію** (function). Коли ви говорите про постійну ідентичність у теперішньому часі, ви використовуєте **nominative case**. Це дуже просте правило.
> 
> *(Welcome! When you meet someone new in Ukraine, you will often be asked about your profession. In Ukrainian, a profession can mean two different things: **identity** or **function**. When you state your permanent identity in the present tense, you use the **nominative case**. This is a very simple rule.)*

**Наприклад:**
- **Я лікар.** — I am a doctor.
- **Він програміст.** — He is a programmer.
- **Вона вчителька.** — She is a teacher.
- **Ми студенти.** — We are students.
- **Моя сестра лікарка.** — My sister is a doctor.
- **Твоя мама інженерка.** — Your mom is an engineer.
- **Мій брат студент.** — My brother is a student.
- **Його батько архітектор.** — His father is an architect.
- **Її подруга дизайнерка.** — Her friend is a designer.
- **Цей чоловік пілот.** — This man is a pilot.

> [!tip] Тимчасові ролі та професії / Temporary roles and professions
>
> Але українська мова змінюється, коли ми говоримо про тимчасову роль, минулу роботу або майбутню професію. Вона використовує **instrumental case**. Цей відмінок показує професійну функцію, процес або стан зміни, а не постійну ідентичність.
>
> *(However, when you talk about a temporary role, a past job, or a future career goal, the Ukrainian language shifts. It uses the **instrumental case**. This case shows a process, a professional function, or a state of change rather than a fixed, permanent identity.)*

**Порівняйте:**
- **Я буду лікарем.** — I will be a doctor.
- **Він хоче стати програмістом.** — He wants to become a programmer.
- **Вона працювала вчителькою.** — She worked as a teacher.
- **Ми були студентами.** — We were students.
- **Моя сестра буде лікаркою.** — My sister will be a doctor.
- **Твоя мама працювала інженеркою.** — Your mom worked as an engineer.
- **Мій брат буде студентом.** — My brother will be a student.
- **Його батько працював архітектором.** — His father worked as an architect.
- **Її подруга хоче стати дизайнеркою.** — Her friend wants to become a designer.
- **Цей чоловік працював пілотом.** — This man worked as a pilot.

> [!warning] The Nominative Trap / Типова помилка
>
> Англомовні студенти часто роблять одну типову граматичну помилку. В англійській мові ми використовуємо однакову форму для теперішнього і майбутнього часу. Тому студенти часто хочуть сказати: ~~Він хоче бути лікар.~~ Це прямий переклад, але для українців це звучить дуже неприродно! Дієслово **бути** в минулому або майбутньому часі вимагає **instrumental case** для професій. Правильно: **Він хоче бути лікарем.**
>
> *(English speakers often fall into a common grammatical trap. Because English uses the same form for present and future professions, learners often want to say: ~~He wants to be doctor~~ in the nominative case. This is a direct translation, but it sounds very unnatural to a Ukrainian! The verb **to be** in the past or future requires the instrumental case for professions. Correct: **Він хоче бути лікарем.**)*

> [!tip] Let's practice! / Давайте практикувати!
> 
> Давайте прочитаємо короткі тексти, де ми використовуємо обидві форми. Зверніть увагу, як змінюються закінчення, коли ми говоримо про теперішній, минулий або майбутній час!
> 
> *(Let's read some short texts where we use both forms. Notice how the endings change when we talk about present, past, or future time!)*

> **(Читання / Reading Practice)**
>
> Мене звати Антон. Зараз я студент, але я дуже люблю комп'ютери. Я хочу бути програмістом. Мій брат працює айтішником у Києві. Раніше він теж був студентом. Наша сестра — лікарка. Вона довго вчилася в університеті, а тепер працює лікаркою в лікарні. Це дуже цікаво!
>
> *(My name is Anton. Right now I am a student, but I really like computers. I want to be a programmer. My brother works as an IT professional in Kyiv. Previously he was also a student. Our sister is a doctor. She was just a student for a long time, and now she works as a doctor in a hospital. It is very interesting!)*

## Презентація: Дієслова та відмінювання
<!-- adapted from: Kravtsova, Grade 4, вправа 53 -->

> [!tip] Three Main Verbs / Три основні дієслова
> 
> Давайте детально розглянемо три основні дієслова: **бути** (to be), **стати / ставати** (to become) та **працювати** (to work). Усі ці дієслова вимагають **instrumental case**.
> Спочатку розглянемо дієслово **бути**. У теперішньому часі ми його часто не використовуємо. Але минулий і майбутній час завжди вимагають його. Також потрібен **instrumental case**!
> 
> *(Let's look closely at the three main verbs: **бути**, **стати / ставати**, and **працювати**. All three require the **instrumental case**. First, let's explore the verb **бути**. While the present tense often drops it, the past and future tenses absolutely require it, along with the instrumental case!)*

**Наприклад:**
- **Він був студентом.** — He was a student.
- **Раніше вона була студенткою.** — She was previously a student.
- **Я буду лікарем.** — I will be a doctor.
- **Ти будеш вчителем?** — Will you be a teacher?
- **Ми були друзями.** — We were friends.
- **Вони будуть інженерами.** — They will be engineers.
- **Ми будемо працювати юристами.** — We will work as lawyers.

> [!tip] The Verb 'to become' / Дієслово 'стати'
> 
> Далі ми розглянемо доконане дієслово **стати** та недоконане **ставати**. Дієслово **стати** дуже популярне, коли ми говоримо про плани на майбутнє. Ви часто будете чути фразу **хоче стати...** (wants to become...).
> 
> *(Next, we have the perfective verb **стати** and imperfective **ставати**. The verb **стати** is extremely common when discussing career aspirations. You will often hear the construction **хоче стати...** (wants to become...).)*

**Наприклад:**
- **Він хоче стати спеціалістом.** — He wants to become a specialist.
- **Вона стала дуже відомою журналісткою.** — She became a very famous journalist.
- **Він довго ставав кращим програмістом.** — He was becoming a better programmer for a long time.
- **Вона довго ставала хорошою вчителькою.** — She was becoming a good teacher for a long time.
- **Кожного дня ти повинен ставати кращим.** — Every day you must be becoming better.
- **Я хочу стати хорошим юристом.** — I want to become a good lawyer.
- **Ми стали студентами.** — We became students.
- **Вони хочуть стати інженерами.** — They want to become engineers.

> [!tip] Дієслово 'працювати' / The verb 'to work'
>
> Нарешті, ми використовуємо дієслово **працювати** (to work), щоб описати нашу теперішню, минулу або майбутню роботу. Це дієслово також вимагає **instrumental case**.
>
> *(Finally, we use the verb **працювати** (to work) to describe our current, past, or future jobs. This verb also requires the instrumental case.)*

> [!caution] The 'Work As' Calque / Калька 'Work As'
>
> В англійській мові ви говорите "I work *as* a manager". Англомовні студенти часто хочуть слово "as" перекласти словом **як**. Ніколи не кажіть: ~~Він працює як менеджер~~! Це неправильно. В українській мові дієслово **працювати** вимагає **instrumental case** без прийменників. Ви просто говорите: **Він працює менеджером**.
>
> *(In English, you say "I work *as* a manager." English speakers often want to translate the word "as" into the Ukrainian word **як**. Never say: ~~Він працює як менеджер~~! This is incorrect. In Ukrainian, the verb **працювати** directly takes the instrumental case with no extra prepositions. You simply say: **Він працює менеджером**.)*

**Наприклад:**
- **Я працюю вчителькою.** — I work as a teacher.
- **Він працює лікарем.** — He works as a doctor.
- **Вона працює менеджеркою.** — She works as a manager.
- **Мій друг працює юристом.** — My friend works as a lawyer.
- **Ти хочеш працювати програмістом?** — Do you want to work as a programmer?

> [!tip] Словник професій / Profession vocabulary
>
> Давайте вивчимо основні назви професій. Зверніть увагу на чоловічі та жіночі форми для кожної професії! Також подивіться на їх закінчення в **instrumental case**!
>
> *(Let's introduce some primary profession vocabulary. Notice how we provide both masculine and feminine forms for each profession, alongside their instrumental endings!)*

**Словник професій (Profession vocabulary):**
- **лікар / лікарка** → лікарем / лікаркою — doctor
- **вчитель / вчителька** → вчителем / вчителькою — teacher
- **інженер / інженерка** → інженером / інженеркою — engineer
- **журналіст / журналістка** → журналістом / журналісткою — journalist
- **юрист / юристка** → юристом / юристкою — lawyer
- **програміст / програмістка** → програмістом / програмісткою — programmer
- **економіст / економістка** → економістом / економісткою — economist
- **дизайнер / дизайнерка** → дизайнером / дизайнеркою — designer
- **архітектор / архітекторка** → архітектором / архітекторкою — architect

> **(Читання. Розмова про нову роботу)**
> 
> — Привіт, Максиме! Я чув, що ти маєш нову роботу. Ким ти працюєш?
> — Привіт! Так. Раніше я був економістом у банку, а зараз я працюю програмістом.
> — Нічого собі! Ти довго вчився?
> — Так, я багато читав і став спеціалістом. А ти?
> — А я ще студент. Я хочу стати архітектором. Моя сестра вже працює архітекторкою.
> — Це чудова професія! Бажаю успіху!
> 
> *(— Hi, Maksym! I heard you have a new job. Who do you work as?)*
> *(— Hi! Yes. Previously I was an economist in a bank, and now I work as a programmer.)*
> *(— Wow! Did you study for a long time?)*
> *(— Yes, I read a lot and became a good specialist. And you?)*
> *(— And I am still a student. I want to become an architect. My sister already works as an architect.)*
> *(— It is a great profession! I wish you success!)*

> [!tip] Технологічні професії / Technology roles
>
> Коли ви говорите про сферу технологій, ви можете почути формальне слово **програмувальник**. Хоча це абсолютно правильно, слово **програміст** використовується набагато частіше в повсякденній мові. Обидва слова вимагають **instrumental case**.
>
> *(When discussing technology roles, you might encounter the formal word **програмувальник**. While this is perfectly correct, the word **програміст** is far more universally used in everyday speech and professional environments. Both require the instrumental case.)*

> **(Читання / Reading Practice)**
>
> Моя мама все життя працювала вчителькою в школі. Вона дуже любить дітей і свою роботу. Мій батько працює інженером на великому заводі. А я хочу стати журналісткою. Я вже працюю в газеті, але зараз я тільки студентка. Минулого року мій старший брат став юристом. Він працює в центрі міста.
>
> *(My mom worked as a teacher in a school her whole life. She loves children and her job very much. My father works as an engineer at a big factory. And I want to become a journalist. I already work at a newspaper, but right now I am only a student. Last year my older brother became a lawyer. He works in the city center.)*

## Соціокультурний контекст: Фемінітиви та IT
<!-- adapted from: Savchenko, Grade 4, вправа 93 -->

> [!culture] Femininitives / Фемінітиви
> 
> Український уряд у 2019 році прийняв важливу граматичну реформу. Раніше російська мова дуже впливала на правила, тому чоловічі форми були основними для всіх професій. Реформа 2019 року офіційно закріпила фемінітиви — слова, що означають жіночу професію. Раніше слова **директор** або **менеджер** використовували для всіх. Сьогодні використання жіночих форм показує повагу та сучасність.
> 
> *(In 2019, the Ukrainian government passed an important grammar reform. Previously, the Russian language heavily influenced the rules, so masculine forms were the default for all professions. The 2019 reform officially codified femininitives — words that identify a female profession. In the past, words like **директор** or **менеджер** were used for everyone. Today, using feminine forms shows respect and modernity.)*

**Порівняйте:**
- **Він хороший директор.** — He is a good director.
- **Вона дуже хороша директорка.** — She is a very good director.
- **Цей чоловік — мій менеджер.** — This man is my manager.
- **Ця жінка — моя менеджерка.** — This woman is my manager.
- **Він відомий філолог.** — He is a famous philologist.
- **Вона відома філологиня.** — She is a famous philologist.

> [!culture] Practice both forms / Практикуйте обидві форми
> 
> Ви повинні постійно практикувати чоловічі та жіночі форми. Це дуже важливо! Використання таких слів, як **директорка** та **менеджерка**, є не лише граматично правильним, але й культурно очікуваним. Це показує, що людина сучасна та освічена.
> 
> *(You should practice using both masculine and feminine forms consistently. It is very important! Using words like **директорка** and **менеджерка** is not just grammatically correct; it is culturally expected. It is a clear sign of an educated, contemporary person.)*

> [!culture] IT sector in Ukraine / ІТ-сфера в Україні
>
> Ще один важливий факт про сучасну Україну — це сектор технологій. Україна відома у світі як великий європейський ІТ-центр, і молодь дуже хоче працювати в цій сфері. Ви часто будете чути два різні слова. Формальне слово — **програміст** (або **програмістка**). Але в повсякденній розмові майже всі використовують слова **айтішник** (для чоловіків) та **айтішниця** (для жінок).
>
> *(Another major aspect of modern Ukraine is the booming technology sector. Ukraine is known globally as a massive European IT hub, and careers in tech are highly sought after by young people. You will often hear two different words. The formal word is **програміст** (or **програмістка**). But in everyday conversation, almost everyone uses the term **айтішник** and **айтішниця**.)*

> [!culture] A Modern Dream / Сучасна мрія
>
> В Україні дуже популярна сфера ІТ через її стабільність та міжнародні зв'язки. Майже кожна молода людина хоче працювати в цій сфері. Дуже часто можна почути такий жарт: **«Кожен другий хоче стати айтішником!»** (Every second person wants to become an IT professional!).
> 
> *(In Ukraine, the IT sphere is very popular because of its stability and international connections. Almost every young person wants to work in this sphere. It is very common to hear such a joke: "Every second person wants to become an IT professional!".)*

**Наприклад:**
- **Її донька працює айтішницею.** — Her daughter works as an IT professional.
- **Він працює успішним айтішником.** — He works as a successful IT professional.

> **(Читання / Reading Practice)**
>
> Сучасна Україна дуже швидко змінюється. Сьогодні багато жінок працюють директорками та менеджерками. Також дуже популярна сфера ІТ. Кожен другий студент хоче працювати айтішником або програмістом. Моя подруга Олена почала працювати програмісткою. Вона працює айтішницею у великій міжнародній компанії. Її мама теж багато працює — вона працює директоркою школи.
>
> *(Modern Ukraine is changing very quickly. Today many women work as directors and managers. The IT sphere is also very popular. Every second student wants to work as an IT professional or a programmer. My friend Olena became a very good programmer. She works as an IT professional in a large international company. Her mom also works a lot — she works as a school director.)*

## Практика та запобігання помилкам
<!-- adapted from: Varzatska, Grade 4, вправа 237 -->

> [!tip] Практика / Let's practice
>
> Давайте попрактикуємося! Ми будемо змінювати теперішні ідентичності на професійні ролі та виправляти типові помилки.
>
> *(Let's actively practice transforming present identities into professional roles and work on correcting common learner mistakes!)* 

> [!tip] Changing the case / Зміна відмінка
> 
> Коли ви змінюєте теперішній час на минулий або майбутній, будьте уважні! Ви повинні змінити закінчення іменника на **instrumental case**. Зверніть увагу на закінчення: чоловічий рід зазвичай додає **-ом** або **-ем**, а жіночий рід додає **-ою** або **-ею**.
> 
> *(When changing a present-tense identity into a past or future role, you must change the ending of the noun to the **instrumental case**. Watch carefully how the endings change for masculine nouns (usually adding **-ом** or **-ем**) and feminine nouns (usually adding **-ою** or **-ею**).)*

**Порівняйте:**
- **Я економіст.** → **Я був економістом.** — I was an economist.
- **Ти юристка.** → **Ти будеш юристкою.** — You will be a lawyer.
- **Він журналіст.** → **Він став журналістом.** — He became a journalist.
- **Вона інженерка.** → **Вона відразу почала працювати головною інженеркою.** — She immediately became a chief engineer.
- **Я спеціаліст.** → **Я хочу стати хорошим спеціалістом.** — I want to become a good specialist.
- **Ти лікар.** → **Ти будеш працювати лікарем.** — You will work as a doctor.

> [!tip] Gender Mismatch Warning / Попередження про рід
>
> Коли ви говорите про професію жінки, будьте уважні! Всі слова повинні бути жіночого роду. Англомовні студенти часто використовують чоловічий рід (як в англійській мові). Уникайте помилок: ~~Вона хороший лікар.~~ Правильно використовуйте жіночий рід: **Вона хороша лікарка.**
>
> *(When talking about a woman's profession, you must ensure that all words match her gender! English speakers sometimes default to the masculine form. Avoid saying: ~~She is a good doctor~~ (using masculine words). Instead, correctly drill the agreement between the gendered person noun and the profession: **Вона хороша лікарка.**)*

> [!tip] Practice / Практика
> 
> Давайте потренуємо фрази з різними родами. Зверніть увагу, як **instrumental case** змінює всі слова разом!
> 
> *(Let's drill some gender-matching phrases. Note how the **instrumental case** changes all words together!)*

**Наприклад:**
- **Він був хорошим лікарем.** — He was a good doctor.
- **Вона була дуже хорошою лікаркою.** — She was a very good doctor.
- **Він хоче стати новим директором.** — He wants to become the new director.
- **Вона хоче стати новою директоркою.** — She wants to become the new director.
- **Він працює головним інженером.** — He works as a chief engineer.
- **Вона працює головною інженеркою.** — She works as a chief engineer.

Finally, we must practice removing the translation calque when using the verb **працювати** (to work). Exercises specifically designed to root out the use of the word **як** (as) are crucial for sounding natural. Remember, the instrumental case alone provides the meaning of "as."

**Порівняйте:**
- ~~Він працює як економіст.~~ → **Він працює економістом.** — He works as an economist.
- ~~Вона працює як спеціаліст.~~ → **Вона працює спеціалісткою.** — She works as a specialist.
- ~~Я працював як журналіст.~~ → **Я працював журналістом.** — I worked as a journalist.

> **(Читання / Reading Practice)**
>
> Раніше мій дідусь був інженером. Він багато років працював головним інженером на великому заводі. Моя бабуся була дуже відомою економісткою. Вона ніколи не працювала журналісткою чи вчителькою. Вона завжди працювала економісткою в банку. Зараз я студент, але я мрію стати відомим спеціалістом. Моя молодша сестра хоче стати юристкою.
>
> *(Previously my grandpa was an engineer. He worked as a chief engineer at a big factory for many years. My grandma was a famous economist. She never worked as a journalist or a teacher. She always worked as an economist in a bank. Right now I am a student, but I dream of becoming a famous specialist. My younger sister wants to become a lawyer.)*

## Діалоги та кар'єрні плани
<!-- adapted from: Kravtsova, Grade 3, вправа 313 -->

The most common way to ask someone about their job in Ukrainian is **«Ким ви працюєте?»** (Who do you work as?) in formal situations, or **«Ким ти працюєш?»** in informal situations. Notice that the question word **хто** (who) changes to its instrumental form **ким** (by whom). 

Let's look at some natural conversations about careers, past roles, and future goals. These dialogues model natural modern usage in IT and professional contexts. Read them aloud to practice your pronunciation!

> **(В офісі / In the office)**
> — Добрий день! Ви тут новий співробітник? Ким ви працюєте?
> — Добрий день! Так. Я працюю менеджером. А ви?
> — Дуже приємно! А я працюю головною директоркою тут.
> — О, це цікаво. Я раніше працював інженером.
>
> *(— Good afternoon! Are you a new employee? Who do you work as?)*
> *(— Good afternoon! Yes. I work as a manager. And you?)*
> *(— Nice to meet you! And I work as the chief director here.)*
> *(— Oh, that is interesting. I previously worked as an engineer.)*

> **(На вулиці / On the street)**
> — Привіт, Олеже! Давно не бачилися! Ким ти зараз працюєш?
> — Привіт! Я став програмістом. Працюю айтішником у новій компанії.
> — Клас! А я ще студент. Хочу стати юристом. Мій друг нещодавно став тестувальником у тій самій компанії.
> — О, тестувальник — це теж дуже потрібна професія! Бажаю успіху!
>
> *(— Hi, Oleh! Long time no see! Who do you work as now?)*
> *(— Hi! I became a programmer. I work as an IT professional in a new company.)*
> *(— Cool! And I am still a student. I want to become a lawyer. My friend recently became a tester at the same company.)*
> *(— Oh, a tester is also a very needed profession! I wish you success!)*

We also use these exact same verbs and cases to talk about citizenship and broader life aspirations. In the official Ukrainian State Standard for language learning, there is a beautiful example sentence that reflects the goals of many people learning the language today: **Вона мріє стати громадянкою України.** (She dreams of becoming a citizen of Ukraine.)

**Наприклад:**
- **Він став громадянином.** — He became a citizen.
- **Вона хоче стати громадянкою.** — She wants to become a citizen.
- **Я мрію бути громадянином України.** — I dream of being a citizen of Ukraine.
- **Ти будеш хорошим громадянином.** — You will be a good citizen.

> [!did-you-know] Synthesis: Your Career Story
>
> You can now describe your entire career path! Practice writing down your own story using the full range of vocabulary introduced today: write what you were in the past (**був / була**), what you work as now (**працюю**), and what you want to become in the future (**хочу стати**). 

> **(Читання / Reading Practice)**
>
> Це Анна. Раніше вона жила в іншій країні і працювала звичайною офіціанткою. Вона багато працювала, але дуже хотіла змінити своє життя. Вона багато вчилася і змогла стати програмісткою. Тепер вона працює айтішницею в Києві. Вона дуже любить Україну. Наступного року вона мріє стати громадянкою України. Її чоловік теж хоче стати громадянином.
>
> *(This is Anna. Previously she lived in another country and was a simple waitress. She worked a lot, but really wanted to change her life. She studied a lot and was able to become a programmer. Now she works as an IT professional in Kyiv. She loves Ukraine very much. She dreams of becoming a citizen of Ukraine next year. Her husband also wants to become a citizen.)*

> **(Читання. Розповідь про професії)**
>
> Привіт! Мене звати Олена. Я хочу розповісти вам про свою родину. Ми всі маємо різні, але дуже цікаві професії. Моя мама раніше працювала вчителькою. Вона багато років працювала в школі. Вона дуже любила дітей, але потім вона вирішила змінити своє життя. Вона довго вчилася і почала працювати програмісткою. Тепер вона працює айтішницею у великій компанії в Києві. Вона каже, що це дуже цікава робота.
> 
> Мій батько завжди був інженером. Він працює головним інженером на заводі. Він дуже розумний і серйозний. Раніше він мріяв стати пілотом, але зараз він любить свою роботу.
> 
> Мій старший брат — студент. Він вивчає економіку. Він хоче стати відомим економістом. Він часто каже: «Я буду дуже успішним економістом!». Він багато читає про фінанси та банки. А моя молодша сестра ще ходить до школи. Вона хоче працювати ветеринаркою. Вона дуже любить тварин і завжди їм допомагає. Найбільше вона любить біологію.
> 
> А що я? Я зараз працюю журналісткою. Я дуже люблю писати статті та розповідати історії. Але я також мрію стати письменницею. Я думаю, що кожна професія — це важливо. Головне — любити те, що ти робиш. Ким ви хочете стати?
>
> *(Hi! My name is Olena. I want to tell you about my family. We all have different, but very interesting professions. My mom previously was a teacher. She worked in a school for many years. She loved children very much, but then she decided to change her life. She studied for a long time and became a very good programmer. Now she works as an IT professional in a big company in Kyiv. She says that it is a very interesting job.
> 
> My father has always been an engineer. He works as a chief engineer at a factory. He is very smart and serious. Previously he dreamed of becoming a pilot, but now he loves his job.
> 
> My older brother is a student. He studies economics. He wants to become a famous economist. He often says: "I will be a very successful economist!". He reads a lot about finance and banks. And my younger sister still goes to school. She wants to work as a veterinarian. She loves animals very much and always helps them. Her favorite subject is biology.
> 
> And what about me? Right now I work as a journalist. I really love writing articles and telling stories. But I also dream of becoming a writer. I think that every profession is important. The main thing is to love what you do. What do you want to become?)*

---

# Підсумок

> [!tip] Summary / Підсумок
> 
> Вітаємо! Тепер ви можете розповідати українською мовою про свою кар'єру та плани! Ви побачили: теперішній час використовує **nominative case** (**Я лікар**). Але ваші минулі ролі та плани на майбутнє вимагають **instrumental case**. Теперішня робота також вимагає **instrumental case** (**Я був лікарем**, **Я працюю лікарем**). Ви також вивчили фемінітиви та словник ІТ. Цей словник відображає сучасне українське суспільство.
> 
> *(Congratulations! You can now confidently describe your career path and professional aspirations in Ukrainian! You learned that present-tense identities use the **nominative case**. But your past roles and future goals require the **instrumental case**. Current work also requires the **instrumental case**. You also explored femininitives and IT vocabulary. This vocabulary reflects contemporary Ukrainian society.)*

Ось кілька запитань (Here are a few questions to check your knowledge):

1. **Як сказати українською: "I want to become a programmer"?**
   *(How do you say in Ukrainian: "I want to become a programmer"?)*
   → Я хочу стати програмістом (або програмісткою).

2. **Яка правильна форма: "Він працює як менеджер" чи "Він працює менеджером"?**
   *(Which is the correct form: "Він працює як менеджер" or "Він працює менеджером"?)*
   → Він працює менеджером.

3. **Як змінити речення "Він лікар" на минулий час?**
   *(How do you change the sentence "Він лікар" to the past tense?)*
   → Він був лікарем.

4. **Як сказати українською: "She dreams of becoming a citizen of Ukraine"?**
   *(How do you say in Ukrainian: "She dreams of becoming a citizen of Ukraine"?)*
   → Вона мріє стати громадянкою України.

---
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/being-and-becoming.yaml`

```yaml
- type: fill-in
  title: "From Present to Past"
  instruction: "Complete the sentence with the correct past tense form."
  items:
    - sentence: "Зараз він програміст, а раніше він був ___."
      answer: "програмістом"
      options: ["програмістом", "програміст", "програмісту", "програмісти"]
    - sentence: "Зараз вона лікарка, а раніше вона була ___."
      answer: "лікаркою"
      options: ["лікарка", "лікаркою", "лікарки", "лікарку"]
    - sentence: "Зараз він вчитель, а раніше він був ___."
      answer: "вчителем"
      options: ["вчитель", "вчителем", "вчителю", "вчителі"]
    - sentence: "Зараз вона інженерка, а раніше вона була ___."
      answer: "інженеркою"
      options: ["інженерка", "інженеркою", "інженерки", "інженерку"]
    - sentence: "Зараз він юрист, а раніше він був ___."
      answer: "юристом"
      options: ["юристом", "юрист", "юристу", "юристи"]
    - sentence: "Зараз вона менеджерка, а раніше вона була ___."
      answer: "менеджеркою"
      options: ["менеджерка", "менеджеркою", "менеджерки", "менеджерку"]
    - sentence: "Зараз він економіст, а раніше він був ___."
      answer: "економістом"
      options: ["економістом", "економіст", "економісту", "економісти"]
    - sentence: "Зараз вона журналістка, а раніше вона була ___."
      answer: "журналісткою"
      options: ["журналістка", "журналісткою", "журналістки", "журналістку"]
    - sentence: "Зараз він директор, а раніше він був ___."
      answer: "директором"
      options: ["директором", "директор", "директору", "директори"]
    - sentence: "Зараз вона дизайнерка, а раніше вона була ___."
      answer: "дизайнеркою"
      options: ["дизайнерка", "дизайнеркою", "дизайнерки", "дизайнерку"]
    - sentence: "Зараз він спеціаліст, а раніше він був ___."
      answer: "спеціалістом"
      options: ["спеціалістом", "спеціаліст", "спеціалісту", "спеціалісти"]
    - sentence: "Зараз вона архітекторка, а раніше вона була ___."
      answer: "архітекторкою"
      options: ["архітекторка", "архітекторкою", "архітекторки", "архітекторку"]

- type: fill-in
  title: "Career Goals"
  instruction: "Complete the sentence with the correct instrumental form."
  items:
    - sentence: "Він дуже хоче стати ___."
      answer: "айтішником"
      options: ["айтішником", "айтішник", "айтішники", "айтішнику"]
    - sentence: "Моя сестра буде ___ в школі."
      answer: "вчителькою"
      options: ["вчителька", "вчителькою", "вчительки", "вчительку"]
    - sentence: "Я мрію бути ___."
      answer: "громадянином"
      options: ["громадянин", "громадянином", "громадянину", "громадяни"]
    - sentence: "Вона стала головною ___."
      answer: "директоркою"
      options: ["директорка", "директоркою", "директорки", "директорку"]
    - sentence: "Ти хочеш працювати ___?"
      answer: "програмістом"
      options: ["програміст", "програмістом", "програмісти", "програмісту"]
    - sentence: "Він став відомим ___."
      answer: "юристом"
      options: ["юрист", "юристом", "юристи", "юристу"]
    - sentence: "Вона довго ставала хорошою ___."
      answer: "лікаркою"
      options: ["лікарка", "лікаркою", "лікарки", "лікарку"]
    - sentence: "Мій брат хоче стати ___ на заводі."
      answer: "інженером"
      options: ["інженером", "інженер", "інженери", "інженеру"]
    - sentence: "Вона мріє стати відомою ___."
      answer: "журналісткою"
      options: ["журналістка", "журналісткою", "журналістки", "журналістку"]
    - sentence: "Він хоче працювати ___."
      answer: "економістом"
      options: ["економіст", "економістом", "економісти", "економісту"]
    - sentence: "Моя подруга стала ___."
      answer: "менеджеркою"
      options: ["менеджерка", "менеджеркою", "менеджерки", "менеджерку"]
    - sentence: "Його друг нещодавно став ___."
      answer: "тестувальником"
      options: ["тестувальник", "тестувальником", "тестувальники", "тестувальнику"]

- type: quiz
  title: "Who Works As What?"
  instruction: "Choose the correct profession based on the description."
  items:
    - question: "She works in a school and loves children. Ким вона працює?"
      explanation: "Вчителька works in a school."
      options:
        - text: "Вчителькою"
          correct: true
        - text: "Інженеркою"
          correct: false
        - text: "Юристкою"
          correct: false
        - text: "Айтішницею"
          correct: false
    - question: "He works with computers in a tech company. Ким він працює?"
      explanation: "Програміст works with computers."
      options:
        - text: "Програмістом"
          correct: true
        - text: "Лікарем"
          correct: false
        - text: "Вчителем"
          correct: false
        - text: "Журналістом"
          correct: false
    - question: "She works in a hospital and helps people. Ким вона працює?"
      explanation: "Лікарка works in a hospital."
      options:
        - text: "Лікаркою"
          correct: true
        - text: "Економісткою"
          correct: false
        - text: "Менеджеркою"
          correct: false
        - text: "Директоркою"
          correct: false
    - question: "He writes articles for a newspaper. Ким він працює?"
      explanation: "Журналіст writes for a newspaper."
      options:
        - text: "Журналістом"
          correct: true
        - text: "Програмістом"
          correct: false
        - text: "Інженером"
          correct: false
        - text: "Юристом"
          correct: false
    - question: "She leads a big company. Ким вона працює?"
      explanation: "Директорка leads a company."
      options:
        - text: "Директоркою"
          correct: true
        - text: "Вчителькою"
          correct: false
        - text: "Лікаркою"
          correct: false
        - text: "Студенткою"
          correct: false
    - question: "He works in a bank with money. Ким він працює?"
      explanation: "Економіст works with economics and money."
      options:
        - text: "Економістом"
          correct: true
        - text: "Айтішником"
          correct: false
        - text: "Лікарем"
          correct: false
        - text: "Журналістом"
          correct: false
    - question: "She helps people with the law. Ким вона працює?"
      explanation: "Юристка works with the law."
      options:
        - text: "Юристкою"
          correct: true
        - text: "Спеціалісткою"
          correct: false
        - text: "Програмісткою"
          correct: false
        - text: "Інженеркою"
          correct: false
    - question: "He designs machines at a factory. Ким він працює?"
      explanation: "Інженер designs machines."
      options:
        - text: "Інженером"
          correct: true
        - text: "Юристом"
          correct: false
        - text: "Вчителем"
          correct: false
        - text: "Менеджером"
          correct: false
    - question: "She manages a team in a big office. Ким вона працює?"
      explanation: "Менеджерка manages a team."
      options:
        - text: "Менеджеркою"
          correct: true
        - text: "Вчителькою"
          correct: false
        - text: "Журналісткою"
          correct: false
        - text: "Лікаркою"
          correct: false
    - question: "He tests software and finds bugs. Ким він працює?"
      explanation: "Тестувальник tests software."
      options:
        - text: "Тестувальником"
          correct: true
        - text: "Інженером"
          correct: false
        - text: "Економістом"
          correct: false
        - text: "Директором"
          correct: false

- type: match-up
  title: "Match the Masculine and Feminine Professions"
  instruction: "Find the matching feminine form for each masculine profession."
  pairs:
    - left: "лікар"
      right: "лікарка"
    - left: "вчитель"
      right: "вчителька"
    - left: "програміст"
      right: "програмістка"
    - left: "айтішник"
      right: "айтішниця"
    - left: "інженер"
      right: "інженерка"
    - left: "журналіст"
      right: "журналістка"
    - left: "юрист"
      right: "юристка"
    - left: "менеджер"
      right: "менеджерка"
    - left: "директор"
      right: "директорка"
    - left: "економіст"
      right: "економістка"

- type: error-correction
  title: "Fix the Mistakes"
  instruction: "Correct the common mistakes in these sentences."
  items:
    - sentence: "Він хоче бути лікар."
      error: "лікар"
      answer: "лікарем"
      options: ["лікарем", "лікарю", "лікарі", "лікаря"]
      explanation: "The verb 'бути' in the past/future takes the instrumental case."
    - sentence: "Вона працює як менеджерка."
      error: "як менеджерка"
      answer: "менеджеркою"
      options: ["менеджеркою", "як менеджеркою", "менеджера", "менеджером"]
      explanation: "The verb 'працювати' takes the instrumental case directly. Do not use 'як'."
    - sentence: "Вона хороший лікар."
      error: "хороший лікар"
      answer: "хороша лікарка"
      options: ["хороша лікарка", "хорошою лікаркою", "хорошій лікарці", "хорошу лікарку"]
      explanation: "Make sure both the adjective and the noun match the feminine gender."
    - sentence: "Раніше він був студент."
      error: "студент"
      answer: "студентом"
      options: ["студентом", "студенту", "студенти", "студента"]
      explanation: "The past tense of 'бути' requires the instrumental case."
    - sentence: "Я хочу стати інженер."
      error: "інженер"
      answer: "інженером"
      options: ["інженером", "інженеру", "інженери", "інженера"]
      explanation: "The verb 'стати' takes the instrumental case."
    - sentence: "Вона працювала як вчителька."
      error: "як вчителька"
      answer: "вчителькою"
      options: ["вчителькою", "як вчителькою", "вчителю", "вчителя"]
      explanation: "Do not use 'як' with 'працювати'."
    - sentence: "Він хороший директорка."
      error: "хороший директорка"
      answer: "хороший директор"
      options: ["хороший директор", "хорошим директором", "хороша директорка", "хорошою директоркою"]
      explanation: "Match the masculine gender for 'він'."
    - sentence: "Моя сестра працює як юристка."
      error: "як юристка"
      answer: "юристкою"
      options: ["юристкою", "як юристкою", "юриста", "юристом"]
      explanation: "Drop 'як' and use the instrumental case."

- type: true-false
  title: "True or False?"
  instruction: "Read the sentence and decide if the grammar and logic are correct."
  items:
    - statement: "Він працює лікарем у лікарні."
      correct: true
      explanation: "Correct grammar and logic."
    - statement: "Вона хоче стати програміст."
      correct: false
      explanation: "Incorrect case. It should be 'програмістом' or 'програмісткою'."
    - statement: "Я працюю як менеджер в офісі."
      correct: false
      explanation: "Incorrect. Drop 'як' and use 'менеджером'."
    - statement: "Вона була студенткою."
      correct: true
      explanation: "Correct past tense and instrumental case."
    - statement: "Мій брат працює айтішницею."
      correct: false
      explanation: "Gender mismatch. 'Брат' is masculine, so it should be 'айтішником'."
    - statement: "Вона дуже хороша директорка."
      correct: true
      explanation: "Correct use of a feminine profession and adjective."
    - statement: "Ти будеш вчитель?"
      correct: false
      explanation: "Future tense of 'бути' requires the instrumental case 'вчителем'."
    - statement: "Вона мріє стати громадянкою України."
      correct: true
      explanation: "Correct grammar and use of the instrumental case."

- type: group-sort
  title: "Sort by Gender"
  instruction: "Sort the professions into masculine and feminine forms."
  groups:
    - name: "Masculine"
      items: ["програміст", "вчитель", "директор", "лікар", "айтішник", "громадянин"]
    - name: "Feminine"
      items: ["програмістка", "вчителька", "директорка", "лікарка", "айтішниця", "громадянка"]

- type: unjumble
  title: "Build the Sentence"
  instruction: "Put the words in the correct order."
  items:
    - words: ["Він", "працює", "айтішником", "у", "Києві"]
      answer: "Він працює айтішником у Києві"
    - words: ["Вона", "хоче", "стати", "відомою", "журналісткою"]
      answer: "Вона хоче стати відомою журналісткою"
    - words: ["Мій", "брат", "був", "хорошим", "студентом"]
      answer: "Мій брат був хорошим студентом"
    - words: ["Я", "буду", "працювати", "головним", "інженером"]
      answer: "Я буду працювати головним інженером"
    - words: ["Вона", "мріє", "стати", "громадянкою", "України"]
      answer: "Вона мріє стати громадянкою України"
    - words: ["Ти", "хочеш", "працювати", "новим", "директором"]
      answer: "Ти хочеш працювати новим директором"

- type: fill-in
  title: "Life Goals"
  instruction: "Complete the sentence with the correct verb."
  items:
    - sentence: "Я хочу ___ лікарем."
      answer: "стати"
      options: ["стати", "став", "стала", "стали"]
    - sentence: "Вона мріє ___ громадянкою України."
      answer: "стати"
      options: ["стати", "стала", "став", "стали"]
    - sentence: "Він довго ___ кращим програмістом."
      answer: "ставав"
      options: ["ставав", "ставала", "ставали", "ставати"]
    - sentence: "Я ___ працювати вчителькою."
      answer: "буду"
      options: ["буду", "буде", "будеш", "будуть"]
    - sentence: "Раніше вона ___ студенткою."
      answer: "була"
      options: ["була", "був", "були", "бути"]
    - sentence: "Кожного дня ти повинен ___ кращим."
      answer: "ставати"
      options: ["ставати", "ставав", "ставала", "ставали"]
    - sentence: "Вони ___ відомими журналістами."
      answer: "стали"
      options: ["стали", "став", "стала", "стати"]
    - sentence: "Ми ___ працювати юристами."
      answer: "будемо"
      options: ["будемо", "буду", "будуть", "буде"]
    - sentence: "Він ___ хорошим спеціалістом."
      answer: "став"
      options: ["став", "стала", "стали", "стати"]
    - sentence: "Вона ___ працювати айтішницею."
      answer: "почала"
      options: ["почала", "почав", "почали", "почати"]
    - sentence: "Ти ___ лікарем у лікарні."
      answer: "будеш"
      options: ["будеш", "буду", "буде", "будуть"]
    - sentence: "Вони ___ студентами."
      answer: "були"
      options: ["були", "був", "була", "бути"]

- type: match-up
  title: "Match the Translation"
  instruction: "Match the English profession to its Ukrainian translation."
  pairs:
    - left: "doctor (masculine)"
      right: "лікар"
    - left: "teacher (feminine)"
      right: "вчителька"
    - left: "programmer (masculine)"
      right: "програміст"
    - left: "IT professional (feminine)"
      right: "айтішниця"
    - left: "lawyer (masculine)"
      right: "юрист"
    - left: "manager (feminine)"
      right: "менеджерка"
    - left: "citizen (masculine)"
      right: "громадянин"
    - left: "engineer (feminine)"
      right: "інженерка"
    - left: "director (masculine)"
      right: "директор"
    - left: "economist (feminine)"
      right: "економістка"
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/vocabulary/being-and-becoming.yaml`

```yaml
items:
  - lemma: "бути"
    translation: "to be"
    pos: "verb"
  - lemma: "стати"
    translation: "to become"
    pos: "verb"
  - lemma: "ставати"
    translation: "to be becoming"
    pos: "verb"
  - lemma: "працювати"
    translation: "to work"
    pos: "verb"
  - lemma: "лікар"
    translation: "doctor"
    pos: "noun"
    gender: "m"
  - lemma: "лікарка"
    translation: "doctor"
    pos: "noun"
    gender: "f"
  - lemma: "вчитель"
    translation: "teacher"
    pos: "noun"
    gender: "m"
  - lemma: "вчителька"
    translation: "teacher"
    pos: "noun"
    gender: "f"
  - lemma: "програміст"
    translation: "programmer"
    pos: "noun"
    gender: "m"
  - lemma: "програмістка"
    translation: "programmer"
    pos: "noun"
    gender: "f"
  - lemma: "айтішник"
    translation: "IT professional"
    pos: "noun"
    gender: "m"
  - lemma: "айтішниця"
    translation: "IT professional"
    pos: "noun"
    gender: "f"
  - lemma: "інженер"
    translation: "engineer"
    pos: "noun"
    gender: "m"
  - lemma: "інженерка"
    translation: "engineer"
    pos: "noun"
    gender: "f"
  - lemma: "журналіст"
    translation: "journalist"
    pos: "noun"
    gender: "m"
  - lemma: "журналістка"
    translation: "journalist"
    pos: "noun"
    gender: "f"
  - lemma: "юрист"
    translation: "lawyer"
    pos: "noun"
    gender: "m"
  - lemma: "юристка"
    translation: "lawyer"
    pos: "noun"
    gender: "f"
  - lemma: "економіст"
    translation: "economist"
    pos: "noun"
    gender: "m"
  - lemma: "економістка"
    translation: "economist"
    pos: "noun"
    gender: "f"
  - lemma: "менеджер"
    translation: "manager"
    pos: "noun"
    gender: "m"
  - lemma: "менеджерка"
    translation: "manager"
    pos: "noun"
    gender: "f"
  - lemma: "спеціаліст"
    translation: "specialist"
    pos: "noun"
    gender: "m"
  - lemma: "спеціалістка"
    translation: "specialist"
    pos: "noun"
    gender: "f"
  - lemma: "громадянин"
    translation: "citizen"
    pos: "noun"
    gender: "m"
  - lemma: "громадянка"
    translation: "citizen"
    pos: "noun"
    gender: "f"
  - lemma: "директор"
    translation: "director"
    pos: "noun"
    gender: "m"
  - lemma: "директорка"
    translation: "director"
    pos: "noun"
    gender: "f"
  - lemma: "тестувальник"
    translation: "tester"
    pos: "noun"
    gender: "m"
  - lemma: "філологиня"
    translation: "philologist"
    pos: "noun"
    gender: "f"
```

---

## Instructions

1. For each issue in the Fix Plan or audit failures, use **Grep** to verify the exact text exists in the file
2. Use the **Edit** tool to fix each issue directly in the file
3. Only fix issues documented above — no silent extra changes
4. Prioritize: audit gate failures first, then review issues

---

## How to Fix

Use the Edit tool for each fix. The workflow for each issue:

1. **Grep** the file to confirm the text exists and is unique
2. **Edit** the file: provide `old_string` (exact text from file) and `new_string` (corrected text)
3. Move to next issue

File paths:
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/being-and-becoming.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/being-and-becoming.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/vocabulary/being-and-becoming.yaml`

## Fix Rules

- Only fix issues documented in the Fix Plan or audit failures above
- You MAY add new activities or modify existing ones if the Fix Plan explicitly requests it
- Do NOT add new prose sections or vocabulary items unless the Fix Plan explicitly requests it
- Maximum **20 edits** total (prioritize the most impactful fixes)
- If nothing needs fixing, state that clearly

---

## Friction Report (MANDATORY)

After all fixes, output:

```
===FRICTION_START===
**Phase**: Phase D.2: Targeted Repair
**Step**: {what you were doing when friction occurred, or "Full Phase D.2"}
**Friction Type**: NONE | EDIT_FAILED | TEXT_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write a review — that was already done in Phase D.1
- Do NOT output ===REVIEW_START=== blocks
- Do NOT output FIND/REPLACE blocks — use the Edit tool instead
- You MAY add/modify activities if the Fix Plan requests it
- Do NOT make cosmetic changes beyond what the review flagged
