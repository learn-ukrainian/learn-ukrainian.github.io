# Phase Fix-Content: Content-Only Fixes

> **You are Gemini, executing a targeted content fix.**
> **Your ONLY task: Fix the CONTENT file based on the review's Fix Plan.**
> **Do NOT output activities or vocabulary — only the fixed content.**

## Your Input

Read these files from disk:

**Review with Fix Plan** (your instructions — follow EVERY fix listed):
```
# Рецензія: Practical Intro

**Level:** A2 | **Module:** 57
**Overall Score:** 8.1/10
**Status:** FAIL
**Reviewed:** 2026-02-10

## Plan Verification

Plan-Content Alignment: FAIL
- Sections: all present.
- Vocabulary: Required words (речення, слово, граматика, правило, помилка, правильно, неправильно, контекст) are used in content but MISSING from the vocabulary YAML file.
- Grammar scope: clean review of A2 topics.
- Objectives: all covered (Identify 7 cases, aspect choice, error correction, complex sentences).

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Good bridge content; integration task is excellent. Shortfall in activity density. |
| 2 | Coherence | 9/10 | <7 | Logical progression from theoretical review to error analysis. |
| 3 | Relevance | 10/10 | <7 | Vital transition module; addresses real student struggles with Case vs. Motion. |
| 4 | Educational | 9/10 | <7 | Strong review with clear model boxes and self-checks. |
| 5 | Language | 7/10 | <8 | Punctuation in unjumble activities is missing required commas taught in the text. |
| 6 | Pedagogy | 6/10 | <7 | Pedagogical inconsistency: teaches punctuation rules but ignores them in drill answers. Missing required vocab in YAML. |
| 7 | Immersion | 8/10 | <6 | Appropriate bilingual balance for A2 review. |
| 8 | Activities | 6/10 | <7 | Significant shortfall in item counts (Fill-in: 8/20; Error-correction: 13/20). Punctuation errors in unjumble. |
| 9 | Richness | 9/10 | <6 | 1335 words (target 1000); 4 engagement boxes; high-quality integration story. |
| 10 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5. Encouraging tone and clear instructions. |
| 11 | LLM Fingerprint | 9/10 | <7 | Structure matches project conventions; tone is tutor-like. |
| 12 | Linguistic Accuracy | 8/10 | <9 | Commas missing in multiple activity answers. "писати лист" is acceptable but less idiomatic than "листа". |

**Weighted Overall:** (8*1.5 + 9*1.0 + 10*1.0 + 9*1.2 + 7*1.1 + 6*1.2 + 8*1.0 + 6*1.3 + 9*0.9 + 9*1.3 + 9*1.0 + 8*1.5) / 14.0 = **8.1/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [Punctuation missing in 12 unjumble items; Ambiguous error in Item 12 of error-correction]
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Pedagogical/Linguistic Punctuation Inconsistency
- **Location**: Activity `unjumble` (Sentence Builder)
- **Original**: "Я не пішов у кіно тому що працював"
- **Problem**: Skill 3 explicitly teaches: "Майже завжди перед ним [що] потрібна кома" and "Do you remember to put a comma before these connectors?". However, all 12 answers in the unjumble activity omit these mandatory commas.
- **Fix**: Add commas to all unjumble answers where required (e.g., "Я не пішов у кіно, тому що працював").

### Issue 2: Vocabulary YAML Mismatch
- **Location**: `vocabulary/57-practical-intro.yaml`
- **Problem**: The vocabulary file omits ALL 8 required words from the plan (речення, слово, граматика, правило, помилка, правильно, неправильно, контекст).
- **Fix**: Update the YAML to include the plan's required vocabulary items with IPA and translations.

### Issue 3: Activity Item Count Shortfall
- **Location**: Activities `fill-in`, `error-correction`, `unjumble`, `quiz`
- **Problem**: Significant shortfall vs. plan hints: Fill-in (8 vs 20), Error-correction (13 vs 20), Unjumble (12 vs 15), Quiz (12 vs 15).
- **Fix**: Expand item counts to match plan targets.

### Issue 4: Ambiguous Error Correction
- **Location**: Activity `error-correction`, Item 12
- **Original**: "Я чекаю автобус. (error: автобус, answer: автобуса)"
- **Problem**: The explanation states "Both are used." Marking a commonly used and acceptable form ("чекаю автобус") as an error is confusing for A2 learners.
- **Fix**: Replace with a clear error (e.g., "дякую тебе" -> "дякую тобі") or an unambiguous case error.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 132 | "Я писав лист вчора дві години." | "Я писав листа вчора дві години." | Naturalness (Genitive preferred for specific letter) |
| YAML | "тому що працював" (unjumble ans 1) | ", тому що працював" | Punctuation |
| YAML | "додому він вже" (unjumble ans 2) | "додому, він вже" | Punctuation |
| YAML | "хочу щоб ти" (unjumble ans 3) | "хочу, щоб ти" | Punctuation |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? Pass
- Instructions clear? Pass
- Quick wins? Pass
- Ukrainian scary? Pass
- Come back tomorrow? Pass

Emotional beats: 6 found
- Welcome: Section "Огляд"
- Curiosity: Skill headers "Чи можете ви..."
- Quick wins: 3 items in Skill 1 "Практика"
- Encouragement: "Остання порада" Box (Important)
- Progress: "Підсумок" table and "Наступні кроки"

## Strengths
- Excellent "Integration Task" that combines multiple skills into a single narrative context.
- High word count provides depth and meaningful context for the review.

## Fix Plan to Reach 9/10 (REQUIRED if score < 9.0)

### Pedagogy: 6/10 → 9/10
**What to fix:**
1. `vocabulary/57-practical-intro.yaml`: Add required words: речення, слово, граматика, правило, помилка, правильно, неправильно, контекст.
2. Section "Skill 4": Ensure the examples used in text perfectly match the corrected activity logic.

### Activities: 6/10 → 9/10
**What to fix:**
1. `fill-in`: Add 12 more items to reach the target of 20.
2. `error-correction`: Add 7 more items to reach 20; remove ambiguous item 12.
3. `unjumble`: Add 3 more items to reach 15.
4. `quiz`: Add 3 more items to reach 15.
5. All activities: Audit every Ukrainian sentence for mandatory commas before connectors (що, щоб, тому що, бо, який) to ensure pedagogical consistency.

### Language/Accuracy: 7.5/10 → 9.5/10
**What to fix:**
1. Fix punctuation in all 12 `unjumble` answer strings.
2. Change "писав лист" to "писав листа" in Skill 2 Model for better naturalness.

### Projected Overall After Fixes
(8*1.5 + 9*1.0 + 10*1.0 + 9*1.2 + 9*1.1 + 9*1.2 + 8*1.0 + 9*1.3 + 9*0.9 + 9*1.3 + 9*1.0 + 9.5*1.5) / 14.0 = **9.1/10**

## Verification Summary

- Content lines read: 250
- Activity items checked: 114
- Ukrainian sentences verified: 65
- IPA transcriptions checked: 6
- Issues found: 4 Critical categories
- Naturalness score recommendation: 9/10 (Content is natural; activities need polish)

## Verdict

**FAIL**

Blocking issues: 1) Pedagogical inconsistency in punctuation between lesson and activities. 2) Significant shortfall in activity item counts vs. plan hints. 3) Required vocabulary missing from YAML.
```

**Current content** (the file you are fixing):
```
# Practical Introduction

## Огляд

**Вітаємо!** Тепер ви готові до практичних сценаріїв!

Після опанування граматики А2 в модулях М01-56, настав час застосувати ваші знання в реальних ситуаціях. У цьому модулі ми розглянемо практичні сценарії, з якими ви зустрінетесь у М58-70. Це перехідний етап від вивчення сухих правил до живого спілкування.

Ми повторимо основні **правила**, вивчимо правильний **порядок** слів та використаємо їх у **контексті**. Ви навчитеся будувати складні **речення** та уникати типових **помилок**. Ми зосередимося на тому, як звучати природно та впевнено. Цей модуль є містком між теорією та вашим майбутнім успіхом у розмові з носіями мови.

**Майбутні теми:**
1. **Медичні ситуації** — візит до лікаря, аптека.
2. **Проживання** — готелі, оренда житла.
3. **Складні Речення** — логічні зв'язки та пунктуація.
4. **Виправлення Помилок** — шліфування вашої граматики.

---

## Skill 1: The 7 Cases (Сім відмінків)

**Чи можете ви вибрати правильний відмінок?**

В українській мові сім відмінків. Кожен відмінок має свою функцію та відповідає на певні питання. Розуміння відмінків дозволяє будувати логічні речення. Ви можете чітко пояснити, хто виконує дію, а на кого вона спрямована. Відмінки — це не просто закінчення, це система зв'язків між словами, яка робить мову гнучкою та виразною.

### Model: Case Function

> **Nominative** (Називний): Хто? Що? (Суб'єкт) -> **Студент** читає книгу вдома.
> **Genitive** (Родовий): Кого? Чого? (Absence/Possession/From) -> Немає **часу**. Книга **брата**. Я з **Києва**. Використовуйте його для вираження заперечення та походження.
> **Dative** (Давальний): Кому? (Recipient/Feeling/Age) -> Я даю книгу **Олегові**. **Мені** холодно. **Йому** десять років. Цей відмінок незамінний для опису емоцій та віку.
> **Accusative** (Знахідний): Кого? Що? (Direct Object/Direction) -> Я бачу **сестру**. Я пішов у **парк**. Пам'ятайте про різницю між об'єктом дії та напрямком руху.
> **Instrumental** (Орудний): Ким? Чим? (Tool/With/Profession) -> Я пишу **олівцем**. Я працюю **вчителем**. Я з **другом**. Він описує інструменти, якими ми працюємо, та людей, з якими ми поруч.
> **Locative** (Місцевий): Де? (Location - only with prepositions) -> Книга лежить у **кімнаті**. Ми живемо в **Україні**. Це єдиний відмінок, який ніколи не вживається без прийменника.
> **Vocative** (Кличний): (Address) -> **Мамо**! **Друже**! **Маріє**! Використання Кличного відмінка робить ваше звертання до людей ввічливим та автентичним.

> [!tip] 💡 Стратегія вибору відмінка
> Щоб обрати правильний відмінок, завжди запитуйте: **Що робить дієслово?** Якщо це «давати», отримувач завжди в Давальному відмінку. Якщо «бачити», об'єкт завжди в Знахідному. Дієслово — це «бос» відмінків! Тренуйтеся ставити ці питання вголос, поки це не стане автоматичним.

### Практика: Оберіть відмінок

1. Я йду в \_\_\_ (парк / парку) - Accusative (direction).
   > [!solution] Перевірити
   > **парк**
2. Я пишу \_\_\_ (олівцем / олівець) - Instrumental (tool).
   > [!solution] Перевірити
   > **олівцем**
3. Немає \_\_\_ (вода / води) - Genitive (absence).
   > [!solution] Перевірити
   > **води**

### Self-Check

- ☐ Can you list all 7 cases in order?
- ☐ Do you know the question words for each? (Кого/Чого, Кому/Чому, Ким/Чим...)
- ☐ Can you use prepositions correctly? (без + Gen, з + Instr, в + Loc/Acc...)

---

## Skill 2: Verb Aspect (Вид дієслова)

**Чи розрізняєте ви процес і результат?**

Вид дієслова — це фундаментальна категорія. Більшість українських дієслів мають пару: Недоконаний (процес) і Доконаний (результат). Це допомагає розрізняти дію в процесі та завершену дію. Правильний вибір виду робить вашу розповідь точною.

### Model: Aspect Pairs

> **Недоконаний вид** / Imperfective:
> Focuses on duration, frequency, or the process itself.
>
> - Я **писав листа** вчора дві години. (тривалість)
> - Я **часто купував** каву тут. (звичка)
> - Я буду **читати** завтра ввечері. (майбутній процес)

> **Доконаний вид** / Perfective:
> Focuses on the completed action, result, or one-time event.
>
> - Я **написав листа** і відправив його. (результат)
> - Я **купив** каву сьогодні вранці. (одноразова дія)
> - Я **прочитаю** цю книгу до вечора. (майбутній результат)

### Практика: Оберіть вид

1. Вчора я \_\_\_ (читав / прочитав) книгу 2 години.
   > [!solution] Перевірити
   > **читав** (Process/Duration)
2. Я вже \_\_\_ (читав / прочитав) цю книгу, вона цікава.
   > [!solution] Перевірити
   > **прочитав** (Result)
3. Завтра я обов'язково \_\_\_ (писатиму / напишу) листа бабусі.
   > [!solution] Перевірити
   > **напишу** (Future result)

### Self-Check

- ☐ Do you use Imperfective for duration/habitual actions?
- ☐ Do you use Perfective for result or one-time completion?
- ☐ Can you form the Future Perfective using prefixes (напишу, зроблю, прочитаю)?

---

## Skill 3: Complex Sentences (Складні речення)

**Чи можете ви логічно поєднувати думки?**

Складні речення пояснюють «чому», «як», «якщо» і «коли». На рівні А2 ми використовуємо логічні сполучники. Ці маленькі **слова** з'єднують ваші думки та визначають їх **порядок** у реченні. Коли ви починаєте використовувати складні речення, ваша мова стає більш дорослою та інтелектуальною.

### Model: Connectors

> **Що** (That): Поєднує дві частини речення.
>
> - Я думаю, **що** це гарна ідея.
> - Він каже, **що** прийде завтра.
>
> **Тому що / Бо** (Because): Пояснює причину.
>
> - Я залишився вдома, **тому що** сьогодні дуже холодно.
>
> **Щоб** (In order to): Пояснює мету або бажання.
>
> - Я вчу українську мову, **щоб** краще розуміти друзів.
> - Я хочу, **щоб** ти був тут.
>
> **Який / Яка / Яке / Які** (Which/Who): Описує іменник. Завжди звертайте увагу на рід іменника, який ви описуєте (місто, яке; хлопець, який).
>
> - Це місто, **яке** мені дуже подобається.
>
> **Якщо** (If): Виражає умову.
>
> - **Якщо** завтра буде сонце, ми підемо на прогулянку.
>
> **Хоча** (Although): Виражає контраст.
>
> - **Хоча** він втомився, він продовжував працювати.

> [!important] ✍️ Пунктуація (Punctuation)
> В українській мові ми **завжди** ставимо кому перед сполучниками: **що, щоб, тому що, бо, який**. Це обов'язкове правило, яке допомагає читачу зрозуміти структуру вашої думки. Ця кома є частиною структури речення, а не просто паузою. Не забувайте про кому — це показник вашої грамотності!
> - Я знаю, **що** ти тут.
> - Я прийшов, **щоб** допомогти.
> - Він не прийшов, **тому що** працював.

> [!myth-buster] 🔍 Пастка «Що»
> Учні часто забувають про слово **що**. Воно обов'язкове при поєднанні думок. Майже завжди перед ним потрібна **кома**. В англійській ви кажете «I think he is here.» В українській треба: «Я думаю, **що** він тут.» Не пропускайте «що»!

### Практика: З'єднайте слова

1. Я працюю в офісі, \_\_\_ (тому що) мені потрібні гроші.
   > [!solution] Перевірити
   > **тому що / бо** (Reason)
2. Ми прийшли сюди, \_\_\_ (щоб) допомогти вам.
   > [!solution] Перевірити
   > **щоб** (Purpose)
3. Це мій старий друг, \_\_\_ (який) живе в Одесі.
   > [!solution] Перевірити
   > **який** (Description)

### Self-Check

- ☐ Can you explain «Why» using *тому що*?
- ☐ Can you explain «What for» using *щоб*?
- ☐ Can you describe a person or object using *який*?
- ☐ Do you remember to put a comma before these connectors?

---

## Skill 4: Common Mistakes (Типові помилки)

**Чи можете ви знайти та виправити типові помилки?**

Для вдосконалення **граматики** важливо бачити різницю між тим, як говорити **правильно** і **неправильно**. Свідоме виправлення власних помилок — це найшвидший шлях до прогресу.

### Model: Error Correction

> **1. Напрямок проти Місця** (Direction vs. Location)
> ❌ **Я гуляю в парк.** (Відмінок напрямку використано для місця)
> ✅ **Я гуляю в парку.** (Місцевий відмінок потрібен для «де»)
> ✅ **Я йду в парк.** (Знахідний відмінок правильний для «куди»)

> **2. Керування дієслів** (Verb Governance)
> ❌ **Я дякую тебе.** (Знахідний використано замість Давального)
> ✅ **Я дякую тобі.** (Дієслова як *дякувати* вимагають Давального)

> **3. Логіка володіння** (Possession Logic)
> ❌ **Я маю болить голова.** (Дослівний переклад)
> ✅ **У мене болить голова.** (Стандартна структура володіння)

> **4. Професії та Орудний відмінок** (Professions and Instrumental)
> ❌ **Я є лікар.** (Дослівний переклад)
> ✅ **Я лікар.** (Називний відмінок для теперішнього часу)
> ✅ **Я працюю лікарем.** (Орудний відмінок з дієсловом «працювати»)

> **5. Кличний відмінок** (Vocative Case)
> ❌ **Привіт, Олександр.** (Називний для звертання)
> ✅ **Привіт, Олександре!** (Обов'язковий Кличний відмінок для імен)

> **6. Вид дієслова** (Verb Aspect)
> ❌ **Я написав вправу двадцять хвилин.** (Доконаний вид використано для тривалості)
> ✅ **Я писав вправу двадцять хвилин.** (Недоконаний вид для процесу)
> ✅ **Я написав вправу.** (Доконаний вид для результату)

> **7. Пунктуація** (Punctuation)
> ❌ **Я не пішов у кіно тому що працював.** (Відсутня кома перед сполучником)
> ✅ **Я не пішов у кіно, тому що працював.** (Завжди ставимо кому перед *тому що, бо, що, щоб, який*)

### Практика: Виправте речення

1. Я граю в футболі. (Це правильно?)
   > [!solution] Перевірити
   > **Ні.** Правильно: «Я граю у **футбол**» (Знахідний для спорту).
2. Я їду в Києві.
   > [!solution] Перевірити
   > **Ні.** Правильно: «Я їду в **Київ**» (Рух вимагає Знахідного).
3. Привіт, Олександр!
   > [!solution] Перевірити
   > **Ні.** Правильно: «Привіт, **Олександре**!» (Потрібен Кличний).
4. Я вже прочитав статтю годину.
   > [!solution] Перевірити
   > **Ні.** Правильно: «Я **читав** статтю годину» (Процес вимагає недоконаного виду).
5. Я вчуся щоб знати більше. (Чи потрібна тут кома?)
   > [!solution] Перевірити
   > **Так.** Правильно: «Я вчуся, **щоб** знати більше» (Перед «щоб» завжди ставимо кому).

### Self-Check

- ☐ Do you distinguish between Motion (Acc) and Location (Loc)?
- ☐ Do you use Dative with verbs of communication?
- ☐ Do you use Instrumental with verbs of being/working?
- ☐ Do you use Imperfective aspect for duration?
- ☐ Do you remember commas before logical connectors?

> [!important] ⚡ Остання порада
> Не бійтеся помилок. Вони показують, що ви вчитеся! Навіть якщо ви говорите **неправильно**, носії мови оцінять ваші зусилля. Вони зрозуміють вас, навіть з помилками. Практикуйтеся і спілкуйтеся!

---

## Інтеграційне завдання

Прочитайте історію та визначте граматичні моменти (1-9). Це допоможе вам побачити, як всі вивчені елементи працюють разом у живому тексті.

> Майкл приїхав у **Київ** (1) минулого тижня, бо хотів знайти нову роботу. Він дуже мріяв побачити це старе **місто** (2), **яке** (3) має таку давню та величну історію. **Хоча** (4) він ще не дуже добре знав мову, він купив маленький **розмовник** (5) і намагався говорити з людьми на вулиці. Вчора він довго **гуляв** (6) мальовничим центром і випадково **зустрів** (7) старого друга. Друг дуже зрадів і допоміг **йому** (8) швидко знайти найближче метро. Тепер Майкл справді **щасливий** (9), що має таких надійних друзів в Україні.

1. **Київ** - Accusative (Motion/Direction)
2. **місто** - Accusative (Direct Object)
3. **яке** - Relative Pronoun (Description)
4. **Хоча** - Connector (Contrast)
5. **розмовник** - Accusative (Direct Object)
6. **гуляв** - Imperfective Verb (Process/Duration)
7. **зустрів** - Perfective Verb (One-time Result)
8. **йому** - Dative Case (Recipient of help)
9. **щасливий** - Adjective (Agreement with Subject)

---

## Підсумок

Вітаємо! Ви успішно повторили граматику рівня А2. Тепер ви можете краще висловлювати думки та описувати дії. Ви створили фундамент для переходу до рівня В1.

Тепер ви знаєте, як будувати правильні **речення**, вибирати правильне **слово** та застосовувати кожне **правило** **граматики** у правильному **контексті**. Ви знаєте правильний **порядок** слів у складних структурах. Якщо ви зробите **помилку**, ви зможете самі визначити, чому це **неправильно**, і виправити це **правильно**.

| Skill | Key Concept | Mastery Level |
| ----- | ----------- | ------------- |
| **Cases** | 7 Syntactic Roles | High |
| **Aspect** | Process vs. Result | High |
| **Syntax** | Logical Connectors | High |
| **Accuracy** | Error Detection | High |

**Наступні кроки:**
Ви опанували граматику А2! Тепер ви готові до рівня В1. Там ми вивчимо синоніми та складні розповіді. Також ми дізнаємося більше про культуру України та особливості розмовної мови.
```

**Plan file** (source of truth for scope — check if fixes align):
```
module: a2-57
level: A2
sequence: 57
slug: practical-intro
version: '2.0'
title: Practical Intro
subtitle: Real World Ukrainian
content_outline:
- section: Огляд
  words: 100
  points:
  - From theory to practice
  - Real-world communication
- section: 'Skill 1: The 7 Cases (Сім відмінків)'
  words: 306
  points:
  - All cases overview
  - When to use each case
- section: 'Skill 2: Verb Aspect (Вид дієслова)'
  words: 163
  points:
  - Perfective vs imperfective
  - Aspect in context
- section: 'Skill 3: Complex Sentences (Складні речення)'
  words: 173
  points:
  - Conjunctions and connectors
  - Building complex sentences
- section: 'Skill 4: Common Mistakes (Типові помилки)'
  words: 133
  points:
  - Case confusion
  - Aspect errors
- section: Інтеграційне завдання
  words: 100
  points:
  - Integration challenge
  - Apply all skills
- section: Підсумок
  words: 25
  points:
  - Summary and next steps
word_target: 1000
vocabulary_hints:
  required:
  - речення (sentence)
  - слово (word)
  - граматика (grammar)
  - правило (rule)
  - помилка (mistake)
  - правильно (correctly)
  - неправильно (incorrectly)
  - контекст (context)
  recommended:
  - відмінок (case)
  - вид (aspect)
  - сполучник (conjunction)
  - порядок (order)
activity_hints:
- type: fill-in
  focus: Case selection in context
  items: 20
- type: error-correction
  focus: Fix grammar mistakes
  items: 20
- type: unjumble
  focus: Build complex sentences
  items: 15
- type: quiz
  focus: Grammar rules review
  items: 15
focus: practical
pedagogy: PPP
prerequisites:
- a2-56 (Checkpoint Full Grammar)
connects_to:
- a2-58 (Practical Warm-up)
objectives:
- Learner can identify all 7 cases in context
- Learner can choose correct verb aspect
- Learner can fix common grammar mistakes
- Learner can build complex sentences
grammar:
- Case system review in practical contexts
- Verb aspect review for real situations
- Sentence structure and common errors
register: розмовний
phase: A2.6 [Practical]

```

**Research notes** (reference for factual accuracy):
```
# Research Notes: Practical Intro (Real World Ukrainian)

**Track**: Core A
**Module**: A2 M57 "Practical Intro"
**Researched**: 2026-02-08
**Level**: A2 (Elementary II)

## 1. Grammar: State Standard 2024 Reference

This module serves as a consolidation and "bridge" from theoretical grammar (A2.1-A2.5) to practical application (A2.6). It aligns with the **Державний стандарт української мови як іноземної (2024)** for the **Elementary Level II (A2)** (Початковий рівень другого ступеня).

### Relevant Sections:
- **§ 4.2.2. Уживання відмінкових форм іменників**: Covers the functional use of all 7 cases (Nominative to Vocative) in practical contexts like identification, location, and object relations.
- **§ 4.3.2. Видові пари дієслів**: Focuses on the functional distinction between imperfective and perfective aspects in real situations (making, doing vs. finished/result).
- **§ 4.4.2. Складне речення**: Requirements for complex sentences using conjunctions: *і, але, що, тому що, бо, щоб*.

**Quote (ДСТУ 2024, Section 4, Level A2):**
> "Обсяг граматичних умінь рівня А2 охоплює усі аспекти, що перелічені на рівні А1, але з розширенням лексичного матеріалу, зростанням діапазону синтаксичних структур та ситуацій комунікації."
> *(The scope of A2 grammar skills covers all A1 aspects but with expanded lexical material, a wider range of syntactic structures, and communication situations.)*

## 2. Vocabulary Frequency

At this stage, the student needs "metalinguistic" vocabulary to discuss their own learning and common practical words for communication.

### High-Frequency "Grammar & Practice" Words:
- **речення** (sentence) — *Essential for following instructions.*
- **слово** (word) — *High frequency.*
- **правило** (rule) — *Common in learning contexts.*
- **помилка** (mistake) — *High frequency in feedback.*
- **правильно/неправильно** (correct/incorrect) — *Core adverbs.*
- **відмінок** (case) — *Technical but necessary for A2 review.*
- **вид** (aspect) — *Technical.*

### Practical "Real World" Connectors (High Frequency):
- **сполучник** (conjunction) — *Used to explain complex sentences.*
- **контекст** (context) — *Crucial for shifting from drills to usage.*
- **значить** (it means) — *Conversational filler and clarification tool.*
- **наприклад** (for example) — *Universal frequency.*

## 3. Cultural Hook: Politeness and Register in Modern Ukraine

### The "Доброго дня" vs "Добрий день" Debate:
While the standard grammar suggests **"Добрий день"** (Nominative) as the primary greeting, the Genitive form **"Доброго дня"** is ubiquitously used in modern service industries (cafes, shops, emails) as a "politeness marker." Introducing students to the fact that "natural" Ukrainian often includes these variations helps them transition to the "Real World" subtitle of this module.

### "Ви" vs "Ти" in Service:
In Ukraine, even young people in service positions will strictly use **"Ви"** (the formal you) with customers. A common "practical" error for English speakers is defaulting to the informal "ти" because they feel friendly. This module emphasizes the formal register (**розмовний офіційний**) for the upcoming "Practical" phase (doctor, hotel, etc.).

## 4. Pedagogical Notes

### Shifting from Drills to Intuition:
Students have just passed a massive grammar checkpoint (M56). They likely feel "overloaded" with rules. 
- **The "Rule of 70%":** At this stage, learners often know the rules intellectually but only apply them correctly 70% of the time in spontaneous speech. The goal here is "Harmonization"—recognizing the *rhythm* of the cases rather than just the charts.
- **Common Error: Case Attrition.** Under pressure, students often "lose" the Accusative or Genitive endings and default to the Nominative.
- **Common Error: Aspectual Tunnel Vision.** Using perfective verbs for every past action because they want to show "result," even when describing a process.

### Teaching Sequence:
1. **Diagnosis:** Use error-correction activities to see which of the 7 cases is weakest.
2. **Expansion:** Move from simple sentences (*Я бачу парк*) to complex ones (*Я бачу парк, який мені подобається*).
3. **Feedback:** Focus on "global" errors (meaning-breaking) before "local" errors (small ending mistakes).

## 5. Scope Boundaries

### IN Scope (A2 Mastery):
- **Cases:** All 7 cases (singular/plural) for basic nouns and pronouns.
- **Aspect:** Basic prefixes (*про-*, *на-*, *по-*) and suffixes (*-ува-*, *-а-*).
- **Sentence Structure:** Coordination (*і, але*) and Subordination (*що, бо, тому що, щоб, який*).
- **Register:** Distinction between formal and informal "you."

### OUT of Scope (B1+):
- **Participles & Gerunds:** *читаючий, прочитавши* (strictly B2).
- **Passive Voice:** *будинок будується* (B1/B2 focus).
- **Complex Numerals:** Agreement with numbers above 5 in indirect cases (*п'яти студентів*) is still too complex; keep to Nominative/Accusative.
- **Subjunctive Mood beyond basic "якби":** Keep conditionals simple.

---
**Data Source:** docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt
**Track:** A2.6 [Practical]

```

## Your Task

1. Read the review file completely — focus on:
   - **"Critical Issues Found"** section
   - **"Fix Plan to Reach 9/10"** section
   - **"Ukrainian Language Issues"** table
2. Apply ONLY content-related fixes (ignore activity/vocabulary fixes)
3. Output the COMPLETE fixed content file

### Rules

1. **Apply EVERY content fix** from the Fix Plan — do not skip any
2. **Scope your changes** — change/add ONLY what the Fix Plan specifies for content
3. **Adding content IS expected** — if the Fix Plan says "add a table", "add examples", "expand section", you MUST do it
4. **Preserve structure** — keep the same H2/H3 headings
5. **Preserve voice** — do not change the writing style of unflagged content
6. **If a fix is ambiguous**, choose the option that matches the plan file
7. **Never output "no changes needed"** — if the Fix Plan lists content fixes, there ARE changes to make

### What NOT to Do

- Do NOT output activities or vocabulary — this phase is CONTENT ONLY
- Do NOT rewrite the entire file — only change what the Fix Plan says
- Do NOT add engagement boxes unless the Fix Plan says to
- Do NOT request skills, delegate to Claude, or skip fixes
- Do NOT add commentary — just output the fixed content

## Output Format

**CRITICAL: Output the COMPLETE fixed content between these delimiter lines.**

===CONTENT_START===
(complete fixed content markdown — ALL of it, not just changed parts)
===CONTENT_END===

**After the content, report what you changed:**

===CHANGES_START===
## Applied Fixes

1. Line {N}: {what changed} — {which review issue this addresses}
2. Section "{name}": {what changed} — {which review issue}

## Fixes NOT Applied (explain why)

- {If any content fix was unclear or contradictory, explain here}
===CHANGES_END===

## Boundaries

- Do NOT output activities or vocabulary sections
- Do NOT fabricate fixes — only apply what the review specified
- Do NOT change the module's pedagogical approach or structure
- If you cannot apply a fix, explain why in the "Fixes NOT Applied" section
