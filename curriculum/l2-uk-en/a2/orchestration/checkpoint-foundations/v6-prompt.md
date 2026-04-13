

---

## Your Writing Identity

**You are: Lead Ukrainian Instructor.** Your persona is *The Conversation Partner*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **8: Контрольна точка: Основи А2** (A2, A2.1 [Foundation and Aspect Introduction]).

**Target: 1500–2250 words** of prose (Ukrainian examples count toward word total, headings and exercise placeholders do not).

---

## Step 1: Pacing Plan (output this FIRST)

Before writing any content, output a `<pacing_plan>` block. Evaluate each section from the plan and commit to a word budget. This prevents frontloading early sections and rushing later ones.

```
<pacing_plan>
Section 1 "Title": ~XXX words — [1-sentence content focus]
Section 2 "Title": ~XXX words — [1-sentence content focus]
...
Summary: ~150 words
Total: 1500+ words
</pacing_plan>
```

Then begin writing the module content. Follow your own pacing plan — each section must hit its word budget (±10%).

---

## 9 Hard Rules

1. **IMMERSION TARGET: 45-65% Ukrainian — nearly half in Ukrainian. English for grammar theory only.** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if immersion is outside this range. For A1 early modules, the learner cannot read Cyrillic — English must dominate. For A2+, Ukrainian must carry a significant share — add Ukrainian Reading Practice blocks, dialogues, and example paragraphs to reach the target. Too little Ukrainian fails audit just as much as too much.
2. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
3. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
4. **You are a warm, encouraging teacher.** Natural teacher phrasing ("Let us look at...", "Have you noticed...") is fine. What to AVOID: self-congratulatory openers ("Welcome to A2! Congratulations!"), gamified language ("You have unlocked...", "You now possess..."), and empty filler sentences that add words but zero information. Every sentence should teach something specific to Ukrainian.
5. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
6. **Place exercise markers only** — do NOT write exercises directly. Place `<!-- INJECT_ACTIVITY: {id} -->` markers where exercises should appear. A separate pipeline step generates the actual exercises from the plan's activity_hints.
7. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
8. **Hit the word target** — you MUST write 1500–2250 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
9. **NO archaic, obsolete, or rare words** — use only modern standard Ukrainian. Do not use words marked as archaic (застаріле) or dialectal in dictionaries. Example: use «кін» not «кон», use «пом'якшені» not «м'якшені». When in doubt, choose the common modern form. Your pre-training contains Russian-influenced archaic forms — verify unfamiliar words.
10. **EVERY module MUST end with `## Підсумок — Summary`** — this is the last H2 section before the file ends. It contains a self-check recap. If you forget this section, the audit REJECTS the module and you waste a retry. Write it LAST, after all other sections.

**Note:** Do NOT add stress marks (´) to any Ukrainian word — a deterministic tool handles this after you write.

## Exercise Placement — Markers Only

**Do NOT write exercises directly.** A separate pipeline step (ACTIVITIES) generates all exercises from the plan's `activity_hints`. Your job is to place markers showing WHERE exercises belong.

### How It Works

1. Read the plan's `activity_hints` — each entry has an `id`, `type`, and `focus`
2. After the relevant teaching section, place an injection marker
3. The ACTIVITIES step reads your prose + the plan hints and generates complete exercises

### Marker Format

Place markers after key teaching sections. Each marker corresponds to ONE `activity_hints` entry from the plan:

```
<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->
```

Rules:
- Use the EXACT `id` from the plan's `activity_hints` — do not invent new IDs
- Place the marker right after the prose that teaches the concept the exercise tests
- Spread markers evenly throughout the module — never cluster them
- If the plan has 4 activity hints, you should place 4 markers in your prose

### Example

If the plan says:
```yaml
activity_hints:
  - id: quiz-sounds-vs-letters
    type: quiz
    focus: "Distinguish звук from літера"
  - id: match-false-friends
    type: match-up
    focus: "Match false friend Cyrillic letters to real sounds"
```

Your prose should contain (after the relevant sections):
```
[...prose about sounds and letters...]

<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->

[...prose about false friend letters...]

<!-- INJECT_ACTIVITY: match-false-friends -->
```

### What NOT to Do

- Do NOT write `:::quiz`, `:::fill-in`, `:::match-up`, or any DSL exercise blocks
- Do NOT write exercise questions, answers, or options — the ACTIVITIES step handles all of this
- Do NOT invent marker IDs — use only IDs from the plan's `activity_hints`

---

## Plan

<plan_content>
module: a2-008
level: A2
sequence: 8
slug: checkpoint-foundations
version: '1.1'
title: 'Контрольна точка: Основи А2'
subtitle: 'Перевірка знань: вид дієслова та родовий відмінок'
focus: review
pedagogy: Review
phase: A2.1 [Foundation and Aspect Introduction]
word_target: 1500
objectives:
  - Learner can reliably distinguish between perfective and imperfective verbs 
    in a given text.
  - Learner can accurately produce Genitive singular and plural endings for 
    nouns after `немає` and quantity words.
  - Learner can select the appropriate aspect (imperfective or perfective) to 
    correctly complete a sentence based on context.
  - Learner can synthesize the new grammar in a short paragraph describing plans
    or past events.
dialogue_situations:
  - setting: 'Friends studying together before a Ukrainian class — quizzing each
      other from notes, one struggles with genitive plural, the other explains.
      Скільки у тебе братів? Двох братів... ні, два брати! Ох, я завжди плутаю.'
    speakers:
      - Олена (студентка)
      - Марко (студент)
    motivation: 'Natural peer study scenario — genitive and aspect review through
      friendly conversation, not interrogation'
content_outline:
  - section: 'Частина 1: Вправи на розпізнавання (Part 1: Recognition Exercises)'
    words: 400
    points:
      - 'Exercise 1: A short text is provided. Learner must highlight all perfective
        verbs in one color and all imperfective verbs in another.'
      - 'Exercise 2: A list of sentences with a noun in parentheses. Learner must
        rewrite the sentence, putting the noun in the correct Genitive form (e.g.,
        ''У мене немає (брат)'' -> ''У мене немає брата'').'
      - 'Exercise 3: Match the imperfective verbs with their perfective partners.'
  - section: 'Частина 2: Вправи на вибір (Part 2: Choice Exercises)'
    words: 500
    points:
      - 'Exercise 4: Multiple-choice sentences where the learner must choose between
        the perfective and imperfective form of a verb (e.g., ''Вчора я (читав / прочитав)
        цю книгу три години'').'
      - 'Exercise 5: Fill-in-the-blanks with the correct quantity word or numeral,
        ensuring noun agreement (e.g., ''У класі ___ (5) студентів'').'
  - section: 'Частина 3: Практичне застосування (Part 3: Production Exercises)'
    words: 600
    points:
      - 'Exercise 6: Answer open-ended questions that require the Genitive case or
        a specific aspect (e.g., ''Скільки у вас братів і сестер?'', ''Що ви зробили
        вчора?'', ''Коли у вас день народження?'').'
      - 'Exercise 7: A short writing prompt (5-7 sentences). ''Напишіть про свої плани
        на вихідні. Що ви будете робити? Що ви хочете зробити?'' (Write about your
        plans for the weekend. What will you be doing? What do you want to get done?).'
vocabulary_hints:
  required:
    - вправа (exercise)
    - перевірка (check, test)
    - контрольна точка (checkpoint)
    - завдання (task)
    - текст (text)
    - речення (sentence)
    - відповідь (answer)
  recommended:
    - правильний (correct)
    - варіант (option, variant)
    - обрати (to choose)
    - написати (to write)
activity_hints:
  - type: quiz
    focus: Mixed Grammar Quiz
    items: 8
  - type: fill-in
    focus: Sentence Transformation Drill
    items: 8
  - type: fill-in
    focus: Short written responses using genitive and aspect
    items: 6
  - type: error-correction
    focus: Find and fix mixed grammar errors — wrong aspect choice, wrong 
      genitive endings, agreement mistakes
    items: 6
references:
  - title: Заболотний Grade 5-6
    notes: Повторення вивченого

</plan_content>

---

## Pre-Verified Facts (from MCP tools — use these, do NOT guess)

A verification step already called VESUM, textbooks, Правопис, and style guide tools. The results below are GROUND TRUTH. Use them:
- If a word is marked ❌ NOT IN VESUM — do NOT use it
- If a textbook excerpt is provided — use that pedagogy
- If a calque is flagged — use the correct alternative
- If CEFR says a word is above target — find a simpler synonym

You do NOT need to call tools yourself — the facts are already verified.

<pre_verified_facts>
## VESUM Verification
- Confirmed: вправа, перевірка, контрольна, точка, завдання, текст, речення, відповідь, правильний, варіант, обрати, написати
- Not found: 

## Grammar Rules
- Дієслівні суфікси (утворення форм недоконаного/доконаного виду): Правопис §34 — У багатьох дієсловах української мови пишемо суфікс -ува- (-юва-).

## Calque Warnings
- контрольна точка: OK
- день народження: OK
- правильний варіант: OK

## CEFR Check
- вправа: A1 — OK
- завдання: A1 — OK
- правильний: A2 — OK
- обрати: B1 — above target
- відповідь: A1 — OK
</pre_verified_facts>


## Wiki Teaching Brief — Your Authoritative Source

**This is your primary teaching material.** The wiki article below was compiled from real Ukrainian school textbooks, literary sources, and verified references. It contains the correct terminology, paradigm tables, teaching sequences, and examples for this module. Your job is to TRANSFORM this into engaging, level-appropriate content — not to copy it verbatim.

**How to use the wiki article:**
1. **Adopt the Ukrainian terminology.** If the article says «складоподіл», you write «складоподіл» — never CVCCV or "syllable division rules" paraphrased from English phonology. If it says «відкритий склад», you write «відкритий склад» — never "open syllable type."
2. **Follow the teaching sequence.** If the article shows: sound model → syllable → word → sentence, follow that progression. Do not rearrange or substitute your own.
3. **Use the article's examples as your foundation.** Authentic examples from textbooks beat invented ones. Use the article's examples and expand with your own that follow the same patterns.
4. **Synthesize and teach, don't summarize.** You are a teacher, not a summarizer. Take the facts from the article and weave them into engaging explanations with dialogues, situations, and practice. The article tells you WHAT to teach — you decide HOW to teach it for the target level.
5. **Your pre-training is contaminated by Russian and English linguistics.** When the article contradicts your instinct, the article wins. Ukrainian has its own phonetic categories (голосний/приголосний, дзвінкий/глухий, м'який/твердий) that do not map 1:1 to English or Russian. Use the Ukrainian categories.
6. **Do NOT copy paragraphs verbatim.** The article is reference material. Your output must be original teaching prose at the correct CEFR level, not a rephrased version of the article.

<knowledge_packet>
# Knowledge Packet: Контрольна точка: Основи А2
**Module:** checkpoint-foundations | **Track:** A2

<wiki_context>
## Compiled Wiki Knowledge

The following articles from the project wiki provide compiled knowledge relevant to this module. Use them as authoritative context — they were compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).

### Вікі: grammar/a2/checkpoint-foundations.md

# Граматика A2: Контрольна точка: Основи А2



## Як це пояснюють у школі (How Schools Teach This)

На рівні A2 українська шкільна програма закріплює фундаментальні поняття синтаксису та морфології, які учень почав вивчати у 5-6 класах. Основний акцент робиться на переході від аналізу окремих слів до побудови та розуміння речень.

1.  **Структура речення:** Учні чітко розрізняють **прості** та **складні** речення (Source 24, Avramenko 5). Складні речення вводяться через базові сполучники (`і`, `а`, `що`, `бо`). Особлива увага приділяється **односкладним реченням** (де є лише підмет або лише присудок) і їх протиставленню **двоскладним**. Наприклад, учнів вчать розрізняти `У двері постукали` (односкладне) та `У двері хтось постукав` (двоскладне) (Source 27, Litvinova 5).

2.  **Пунктуація:** Основний фокус — кома між однорідними членами речення (`Я люблю яблука, груші і сливи`) та кома між частинами складного речення (`Пропоную сходити в боулінг, або ми можемо піти в кіно`) (Source 19, Litvinova 5; Source 28, Litvinova 5).

3.  **Частини мови:** Відбувається закріплення знань про самостійні (іменник, прикметник, дієслово) та службові (прийменник, сполучник) частини мови (Source 15, Avramenko 6). Розглядаються їхні основні граматичні категорії: рід, число, відмінок для іменників; час, вид, особа для дієслів.

4.  **Культура мовлення:** Підручники систематично включають рубрики "Культура слова", де виправляють поширені помилки, зокрема кальки з російської мови та неправильне вживання прийменників. Це є невід'ємною частиною програми (Source 14, Avramenko 6; Source 24, Avramenko 5; Source 30, Litvinova 5).

5.  **Фонетика та наголос:** Наголос (`наголос`) визнається складною темою навіть для носіїв мови, тому вправи на правильне наголошування слів (`донька́` чи `до́нька`) є стандартною частиною уроків (Source 1, ULP; Source 10, Litvinova 5).

Підхід у сучасних підручниках є тематичним: граматичні правила вивчаються на матеріалі з конкретної сфери життя (спорт, їжа, подорожі), щоб зробити навчання цікавішим і ближчим до реального спілкування (Source 16, Avramenko 8).

## Повна парадигма (Full Paradigm)

На рівні А2 ключовим є впевнене володіння базовими системами, а не вивчення всіх винятків.

### 1. Дієслово `бути` (Verb 'to be')
Хоча в теперішньому часі форма `є` часто опускається, її знання важливе для утворення деяких конструкцій.

| Час | Однина | Множина |
| :--- | :--- | :--- |
| **Теперішній** | я **є**<br>ти **є**<br>він/вона/воно **є** | ми **є**<br>ви **є**<br>вони **є** |
| **Минулий** | я/ти/він **був**<br>я/ти/вона **була**<br>воно **було** | ми/ви/вони **були** |
| **Майбутній** | я **буду**<br>ти **будеш**<br>він/вона/воно **буде** | ми **будемо**<br>ви **будете**<br>вони **будуть** |

### 2. Базові сполучники (Basic Conjunctions)
Сполучники — це "клей" для поєднання ідей у складні речення.

| Тип | Сполучник | Приклад | Джерело |
| :--- | :--- | :--- | :--- |
| **Єднальні** (and) | `і`, `й`, `та` | Я візьму той рушник **і** простелю, наче долю. | (Source 19) |
| **Протиставні** (but) | `а`, `але`, `проте` | Ми потрапили під дощ, **але** все одно було весело. | (Source 25) |
| **Розділові** (or) | `або`, `чи` | Пропоную сходити в боулінг **або** в кіно. | (Source 25) |
| **Причинові** (because) | `бо`, `тому що` | Українці будуть дуже здивовані, **бо** ви вживаєте прислів'я. | (Адаптовано з Source 9) |
| **Пояснювальний** (that) | `що` | Я думаю, **що** зробила правильний вибір. | (Source 4) |

### 3. Ступені порівняння прикметників (Adjective Comparison)

| Ступінь | Форма | Приклад (гарний) | Правило |
| :--- | :--- | :--- | :--- |
| **Вищий** | Проста | гарн**іший** | основа + `-іш-` / `-ш-` |
| (Comparative) | Складена | **більш** гарний | `більш` / `менш` + прикметник |
| **Найвищий** | Проста | **най**гарн**іший** | `най-` + вищий ступінь |
| (Superlative) | Складена | **найбільш** гарний | `найбільш` + прикметник |

**Важливо:** При порівнянні використовуються конструкції `...ніж...`, `...за...`, `...від...`. Наприклад: `Ця книга цікавіша, **ніж** та` або `Ця книга цікавіша **за** ту`. (Source 29)

## Частотність і пріоритети (Frequency & Priorities)

1.  **"Культура мовлення":** Виправлення поширених лексичних помилок (`брати участь`, `складати іспит`) має найвищий пріоритет. Це миттєво підвищує якість мовлення і є ознакою освіченої людини навіть серед носіїв.

2.  **Базові сполучники:** Впевнене використання `і, а, але, бо, що` є критично важливим для переходу від коротких, уривчастих фраз до зв'язного мовлення.

3.  **Минулий час дієслів:** Правильне утворення форм минулого часу (`-в`, `-ла`, `-ло`, `-ли`) є основою для будь-якої розповіді. Вступне розрізнення доконаного/недоконаного виду (аспекту) починається тут (напр. `я читав` (процес) vs. `я прочитав` (результат)).

4.  **Формальне/неформальне звертання (`ти` vs. `Ви`):** Правильне використання `Ви` з великої літери на письмі та узгодження дієслів з `ви` у множині (`Ви казали`, а не `Ви казав`) є ключовим соціальним маркером (Source 23).

5.  **Наголос:** Хоча вивчення всіх наголосів нереалістичне (Source 1), засвоєння правильного наголосу у 50-100 найуживаніших словах (особливо тих, де наголос відрізняється від російського або змінює значення слова) значно покращує вимову та розуміння.

## Типові помилки L2 (Common L2 Errors)

Це найважливіший розділ для учня рівня А2. Виправлення цих помилок є прямим шляхом до більш природного мовлення.

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| приймати участь | **брати** участь | Калька з російської `принимать участие`. Українською участь "беруть". (Source 36) |
| здавати іспит | **складати** іспит | `Здавати` означає "to hand in/surrender". Іспит "складають". (Source 15) |
| ви праві | ви **маєте рацію** / ваша правда | `Ви праві` є поширеною, але стилістично нерекомендованою калькою. `Мати рацію` — ідіоматичний український вислів. (Source 24) |
| дякуючи вам | **завдяки** вам | `Дякуючи` — це активний дієприслівник ("thanking"). Для причини використовується прийменник `завдяки`. (Source 14) |
| пробачте **мене** | пробачте **мені** | Дієслово `пробачати` вимагає давального відмінка (`кому?`), а не знахідного. (Source 30, 21) |
| говорити **на** українській мові | говорити **українською мовою** | Назви мов у цій конструкції вживаються в орудному відмінку (`чим?`). (Source 30) |
| самий кращий | **найкращий** | Конструкція з `самий` є калькою з російської. В українській мові найвищий ступінь утворюється префіксом `най-`. (Source 29) |
| більш розумн**іший** | **більш** розумн**ий** / розумн**іший** | Не можна одночасно використовувати складену (`більш`) і просту (`-іший`) форми вищого ступеня. (Source 29) |
| не звертати **увагу** | не звертати **уваги** | Фразеологізм вимагає родового відмінка (`чого?`). (Source 24) |
| вірна відповідь | **правильна** відповідь | `Вірний` в українській мові означає "loyal, faithful" (вірний друг). Для логічної правильності вживають `правильний`. (Source 20) |

## Деколонізаційні застереження (Decolonization Notes)

1.  **Наголос — не російський:** Український наголос є незалежною системою. Багато слів, що схожі з російськими, мають інший наголос. Навчання за принципом "як у російській, але..." є хибним. Український наголос є нормою, а не винятком.
    *   Укр: `нена́видіти`, `фарту́х`, `оле́нь`. (Source 1)
    *   Рос: `ненави́деть`, `фа́ртук`, `оле́нь`.

2.  **Лексика — `брати`, а не `приймати`:** Особливу увагу слід приділяти дієслівним конструкціям. Конструкція `брати участь` є питомо українською, на відміну від кальки `приймати участь` з російського `принимать участие`. Подібних відмінностей багато (`складати іспит` vs. `сдавать экзамен`).

3.  **Прийменники — самостійність:** Вживання прийменників в українській мові має свою логіку, яка не завжди збігається з російською. Наприклад, `говорити українською` (орудний відмінок) vs. `говорить по-русски` (прислівник) або `на русском` (прийменникова конструкція).

4.  **Дієслово `бути`:** На відміну від сучасної російської мови, де дієслово-зв'язка "быть" у теперішньому часі завжди опускається, в українській мові форма `є` збереглася і активно вживається, хоч і може опускатися в розмовному стилі (`Я є студент` або `Я — студент`). Це важлива граматична відмінність. (Inspired by Source 26).

## Природні приклади (Natural Examples)

### Група 1: Прості речення з однорідними членами
*   Працюймо разом, **бо** так усе зробимо швидше. (Source 25)
*   Сучасні молоді люди досить рідко вживають прислів'я **та** приказки. (Source 9)
*   Я хочу вивчати шведську мову, **але** я собі запланувала, що буду займатися після роботи. (Адаптовано з Source 3)

### Група 2: Складні речення зі сполучником `що`
*   Мені здається, **що** хороші оцінки — це не тільки позитивно. (Source 4)
*   Я знаю, **що** тоді в мене буде більше вільного часу. (Source 3)
*   Деякі люди вважають, **що** менталітет українців — це бути скраю. (Source 9)

### Група 3: Односкладні речення (без підмета або без присудка)
*   **Треба** вміти жаліти людину. (Source 7)
*   Над білим світом – білий сніг. (Source 7)
*   У двері **постукали**. (Source 27)

### Група 4: Вживання минулого часу (аспект)
*   Автобус щойно **поїхав** і вже майже **зник** з очей. (Результат, доконаний вид) (Source 8)
*   Я **закінчила** національний університет києво-могилянська академія. (Результат, доконаний вид) (Source 5)
*   Коли я **проводила** опитування, багато хто з вас **сказав**, що вже непогано **говорить** українською. (Процес vs. Результат) (Source 4)

### Група 5: Формальне звертання `Ви`
*   Шановний пане Юрію, висловлюємо **Вам** подяку за сумлінну працю. (Source 23)
*   Скажіть, **Улю**, паляниця! (Неформальне `ти` до знайомої людини) (Source 20)

## Рекомендації для вправ (Activity Concepts)

*   **Phase 1 (Recognition & Identification):**
    *   **Вправа "Світлофор":** Дати список речень з помилками з розділу "Типові помилки L2". Учні мають позначити "зеленим" правильні речення, "червоним" — неправильні.
    *   **Вправа "Знайди сполучник":** У короткому тексті (2-3 абзаци) учень має підкреслити всі сполучники і визначити їхню функцію (єднальний, протиставний і т.д.).
    *   **Вправа "Наголос":** Тести з вибором правильного наголосу для слів з високою частотністю (`випадок`, `разом`, `читання`, `завдання`). (Source 10).

*   **Phase 2 (Controlled Production):**
    *   **Вправа "Конструктор речень":** Дати пари простих речень і набір сполучників (`і, а, але, тому що, або`). Завдання — об'єднати їх у складні речення.
    *   **Вправа "Трансформація":** Перетворити речення з прямою мовою на складне речення зі сполучником `що`. Наприклад: `Мама сказала: "Я втомилася"` -> `Мама сказала, що вона втомилася`.
    *   **Вправа "Виправ помилку":** Дати речення з помилками у ступенях порівняння прикметників (`більш тепліший`, `самий холодний`) для корекції. (Source 29).

*   **Phase 3 (Free Production):**
    *   **Вправа "Мій день":** Написати 5-7 речень про свій вчорашній день, обов'язково використовуючи минулий час та щонайменше три різні сполучники.
    *   **Вправа "Порада другу":** Написати коротку пораду (3-4 речення), використовуючи односкладні речення (напр., `Треба більше читати. Не бійся робити помилки.`). (Inspired by Source 7).
    *   **Вправа "Аудіоповторення":** Записати для учня коротке автентичне аудіо (напр., з Ukrainian Lessons Podcast). Учень слухає одне речення, ставить на паузу, повторює його вголос, намагаючись імітувати інтонацію і наголос. Потім перевіряє себе за транскриптом. (Source 3).

## Зв'язки з іншими темами (Connections)

*   **Передумови:** Цей чекпойнт спирається на знання з рівня А1: базові відмінки іменників, теперішній час дієслів, особові займенники та проста структура речення "підмет-присудок-додаток".
*   **Наступні кроки (B1):** Впевнене володіння основами А2 дозволяє перейти до складніших тем рівня В1, таких як:
    *   **Дієслова руху з префіксами** (`йти` -> `прийти`, `вийти`, `перейти`).
    *   **Дієприкметники та дієприслівники** (пасивні стани, ускладнення речень).
    *   Поглиблене вивчення **системи відмінків** з усіма винятками.
    *   Складніші **підрядні речення** (умовні, часові, допустові).

## Пов'язані статті (Related Articles)

*   [[grammar/a2/verb-aspect-introduction|Часовиді дієслова: Вступ до аспектів]]
*   [[grammar/a2/cases-prepositions|Відмінки та прийменники: поширені конструкції]]
*   [[grammar/a1/present-tense|Теперішній час дієслів]]
*   [[grammar/b1/verbs-of-motion|Дієслова руху та префікси]]
*   [[phonetics/stress-patterns|Наголос в українській мові]]
*   [[syntax/complex-sentences|Складні речення та сполучники]]

---

### Вікі: grammar/a2/checkpoint-genitive.md

# Граматика A2: Контрольна робота — родовий відмінок



## Як це пояснюють у школі (How Schools Teach This)
Родовий відмінок (Genitive case) в українській шкільній програмі вводиться поступово, починаючи з початкових класів. Його основне питання — **кого? чого?** (Source 23: `4-klas-ukrayinska-mova-kravtsova-2021-1_s0040`).

Основні функції, що вивчаються:
1.  **Позначення відсутності:** Конструкція з `немає` (there is no / there are no). Це одна з перших функцій, яку засвоюють учні. Наприклад: `немає (кого?) брата`, `немає (чого?) молока`. (Source 23)
2.  **Позначення належності (Possession):** Відповідає на питання "чий?". Наприклад, `щоденник (кого?) дочки`, `твори (кого?) Шевченка`. (Source 9: `11-klas-ukrajinska-mova-avramenko-2019_s0258`). У цій ролі родовий відмінок часто конкурує з більш природними для розмовної мови присвійними прикметниками (`доччин щоденник`, `Тарасова гора`), але є обов'язковим у діловому мовленні або при переліченні (`майно Федченка`, `твори Шевченка, Франка, Лесі Українки`). (Source 9)
3.  **Керування дієсловами:** Низка дієслів вимагає після себе додатка в родовому відмінку, а не в знахідному. Підручники для середньої школи (Source 6: `8-klas-ukrmova-zabolotnyi-2025_s0049`) наводять списки таких дієслів:
    *   `потребувати (чого?) допомоги`
    *   `навчатися (чого?) музики`
    *   `зазнати (чого?) лиха`
    *   `дотримати (чого?) обіцянки`
    *   `завдати (чого?) шкоди`
4.  **Вживання з числівниками:** Це ключова тема. Історично числівники від 5 до 10 були іменниками, що вимагали родового відмінка множини (Source 4: `ext-other_blogs-67`, `пѧть братъ`). Ця норма збереглася: після числівників `п'ять` і більше іменник ставиться в родовому відмінку множини. Наприклад: `п'ять столів`, `десять книжок`.
5.  **Вживання з прийменниками:** Родовий відмінок використовується з багатьма прийменниками, такими як `без`, `для`, `до`, `з`, `від`, `біля`, `крім`, `замість`, `серед`. (Source 21: `7-klas-ukrmova-zabolotnyi-2024_s0185`).

## Повна парадигма (Full Paradigm)
Родовий відмінок є одним із найскладніших через варіативність закінчень, особливо в II відміні та в множині.

### Іменники (Nouns)

#### І відміна (Feminine, Masculine, Common gender in -а/-я)
(Source 19: `ext-other_blogs-46`)

| Група | Рід | Однина (кого? чого?) | Множина (кого? чого?) | Приклади |
| :--- | :--- | :--- | :--- | :--- |
| Тверда | жін./чол. | `-и` | `-ø` | `ріки`, `сироти` (G.Sg) / `рік`, `сиріт` (G.Pl) |
| М'яка | жін./чол. | `-і` / `-ї` | `-ь` / `-й` | `землі`, `мрії` (G.Sg) / `земель`, `мрій` (G.Pl) |
| Мішана | жін./чол. | `-і` | `-ø` | `вежі`, `кручі` (G.Sg) / `веж`, `круч` (G.Pl) |

**Особливості родового відмінка множини І відміни:**
*   **Вставні голосні `о`, `е`:** `думка → дум**о**к`, `земля → зем**е**ль` (Source 19).
*   **Закінчення `-ей`:** `стаття → стат**ей**`, `сім'я → сім**ей**`, `свиня → свин**ей**` (Source 19).
*   **Закінчення `-ів`:** `сусіда → сусід**ів**`, `староста → старост**ів**` (також `старост`), `баба → баб**ів**` (також `баб`) (Source 19).

#### II відміна (Masculine with zero-ending/`-о`, Neuter in -о/-е/-я)

| Рід | Однина (кого? чого?) | Множина (кого? чого?) | Приклади |
| :--- | :--- | :--- | :--- |
| Чол. (істоти) | `-а`, `-я` | `-ів`, `-їв` | `брата`, `учителя` / `братів`, `учителів` |
| Чол. (неістоти) | **`-а`/`-я` АБО `-у`/`-ю`** | `-ів`, `-їв`, `-ø` | `стола`, `трамвая` / `саду`, `краю` → `столів`, `трамваїв`, `садів`, `країв` |
| Середній | `-а`, `-я` | `-ø` | `села`, `моря` / `сіл`, `морів` (рідко) |

**Ключова складність II відміни:** вибір закінчення **-а(-я)** чи **-у(-ю)** в родовому відмінку однини для неістот чоловічого роду. Правила складні й мають багато винятків, але загальна тенденція:
*   **-а, -я:** для конкретних, чітко окреслених понять (назви міст, річок з наголосом на закінченні, терміни, предмети): `Києва`, `Дніпра`, `атома`, `документа`, `вівторка`.
*   **-у, -ю:** для абстрактних понять, збірних, речовин, явищ природи, установ: `миру`, `прогресу`, `піску`, `вітру`, `університету`, `інституту`. <!-- VERIFY -->

#### III відміна (Feminine with zero-ending + *мати*)
(Source 30: `6-klas-ukrmova-zabolotnyi-2020_s0111`)

| Однина (кого? чого?) | Множина (кого? чого?) | Приклади |
| :--- | :--- | :--- |
| `-і` / `-и` | `-ей` | `ночі`, `любові` (`любови`), `радості` (`радости`) / `ночей`, `подорожей` |
| *виняток* | *виняток* | `матері` / `матерів` |

#### IV відміна (Neuter in -а/-я, що позначає молодих істот)
(Source 19: `ext-other_blogs-46`)

| Однина (кого? чого?) | Множина (кого? чого?) | Приклади |
| :--- | :--- | :--- |
| `-ят-и`, `-ен-і` | `-ят`, `-ен` | `теляти`, `імені` / `телят`, `імен` |

### Прикметники та присвійні займенники (Adjectives and Possessives)
Відмінюються за родами і числами, узгоджуючись з іменником.
(Source 24: `7-klas-ukrmova-avramenko-2024_s0115`, Source 27: `6-klas-ukrmova-zabolotnyi-2020_s0210`)

| Рід / Число | Закінчення | Приклади |
| :--- | :--- | :--- |
| Чоловічий одн. | `-ого` | `нового`, `мого`, `синього` |
| Жіночий одн. | `-ої`, `-еї` | `нової`, `моєї`, `синьої` |
| Середній одн. | `-ого` | `нового`, `мого`, `синього` |
| Множина | `-их` | `нових`, `моїх`, `синіх` |

## Частотність і пріоритети (Frequency & Priorities)
Для рівня A2/B1 пріоритетним є засвоєння найбільш уживаних функцій родового відмінка:

1.  **Найвища частотність:**
    *   **Заперечення/відсутність з `нема(є)`:** `У мене немає часу`, `В магазині немає хліба`. Це фундаментальна конструкція.
    *   **Кількість з числами 5+:** `п'ять друзів`, `сто гривень`, `багато людей`. Це обов'язково для будь-яких розмов про кількість.
    *   **Прийменники `для`, `до`, `з`, `без`:** `кава без цукру`, `подарунок для мами`, `я йду до університету`, `сік з яблук`.

2.  **Середня частотність (важливо для розширення мовлення):**
    *   **Проста належність:** `колір неба`, `центр міста`, `ім'я мого брата`.
    *   **Дати:** для позначення місяця в даті: `перше (чого?) січня`, `восьме (чого?) березня`.
    *   **Керування поширеними дієсловами:** `чекати (чого?) автобуса`, `боятися (кого?) собак`, `шукати (чого?) роботу`.

3.  **Нижча частотність (для B1 і вище):**
    *   Тонкощі вибору закінчень `-а`/`-у` в чоловічому роді. На рівні А2 достатньо вивчити найчастотніші слова як лексичні одиниці.
    *   Рідкісні форми родового відмінка множини.
    *   Складні випадки керування (e.g. `запобігти (чому?) нещастю` (Dative) vs `уникнути (чого?) нещастя` (Genitive)).

## Типові помилки L2 (Common L2 Errors)
Англомовні студенти часто припускаються помилок через відсутність відмінків в англійській мові та інтерференцію.

| ❌ Помилково (Incorrectly) | ✅ Правильно (Correctly) | Чому (Why) |
| :--- | :--- | :--- |
| *Я потребую допомогу.* | *Я потребую **допомоги**.* | Дієслово `потребувати` вимагає родового, а не знахідного відмінка. Це пряма калька з англійського "I need help" (verb + direct object). (Source 6) |
| *Я купив п'ять книга.* | *Я купив п'ять **книжок**.* | Після числівників від 5 і вище іменник має стояти в родовому відмінку множини. Помилка виникає через застосування правила для чисел 2-4. (Source 4) |
| *У мене немає сестра.* | *У мене немає **сестри**.* | Конструкція заперечення `немає` завжди вимагає родового відмінка. Студенти часто залишають іменник у називному відмінку. (Source 23) |
| *Я йду в магазин.* | *Я йду **до** магазин**у**.* | Хоча `в/у` + Accusative використовується для напрямку, з дієсловами руху прийменник `до` + Genitive є більш поширеним і часто єдиним правильним варіантом для позначення кінцевої точки маршруту. |
| *Це машина мій брат.* | *Це машина **мого брата**.* | Для позначення належності використовується родовий відмінок, а не просто два іменники поруч, як іноді буває в англійській ("my brother's car" where "'s" is a particle, not a case ending reflected in the noun itself). |
| *Не було рук**и́**.* (наголос на `и`) | *Не було р**у́**ки.* (наголос на `у`) | У деяких іменниках при зміні відмінка чи числа відбувається зміна наголосу. `Руки́` (N. pl.) vs `ру́ки` (G. sg.). Це треба запам'ятовувати. (Source 2: `ext-ulp_youtube-29`) |

## Деколонізаційні застереження (Decolonization Notes)
Українська граматика має власну логіку розвитку, відмінну від російської. Навчання через порівняння з російською є хибною колоніальною практикою.

1.  **Закінчення `-а`/`-я` vs. `-у`/`-ю` в Родовому відмінку чоловічого роду:** Це одна з найскладніших тем в українській мові, і правила тут **не збігаються** з російськими. Наприклад, в українській мові назви міст переважно мають закінчення `-а`: `Києва`, `Лондона`, `Харкова`. У російській мові для багатьох з них нормою є `-а`: `Киева`, але для деяких `-у`: `Лондону`. Навчання "за аналогією" до російської призведе до системних помилок.
2.  **Керування дієслів:** Дієслово `чекати` (to wait) в українській мові традиційно вимагає родового відмінка (`чекати листа`, `чекати автобуса`). У сучасній мові під впливом російської поширився і знахідний відмінок, але родовий залишається стилістично вищим і класичним. У російській мові `ждать` вимагає знахідного (`ждать письмо`) або родового (при конкретизації чи запереченні).
3.  **Фонетичні відмінності в закінченнях:** Українські закінчення є результатом природного розвитку праслов'янської мови на українських землях. Наприклад, у родовому відмінку множини часто з'являються вставні `о`, `е` (`жінок`, `пісень`), що є органічною рисою української фонетики (Source 19). Російська мова має свої власні рефлекси (пор. `жен`, `песен`).
4.  **Історична тяглість:** Український родовий відмінок зберігає риси, що походять ще з давньоукраїнської (давньоруської) мови, зокрема вживання з числівниками (Source 4). Це не запозичення і не "варіант", а прямий спадок мовної еволюції.
5.  **Прийменник `до`:** Вживання прийменника `до` + Genitive для позначення напрямку руху (`їхати до Києва`) є питомою українською рисою, на відміну від російського `в` + Accusative (`ехать в Киев`).

## Природні приклади (Natural Examples)

**1. Вираження відсутності (Absence)**
*   У мене немає **часу** на це. (I don't have time for this.)
*   Сьогодні в магазині не було свіжого **хліба**. (There was no fresh bread in the store today.)
*   Без **тебе** тут сумно. (It's sad here without you.)

**2. Вираження належності (Possession)**
*   Це номер **мого телефону**. (This is my phone number.)
*   Я читаю книжку **Андрія Куркова**. (I'm reading a book by Andriy Kurkov.)
*   На столі лежить зошит **моєї сестри**. (My sister's notebook is on the table.) (Source 9, adapted)

**3. Кількість (Quantity & Numerals)**
*   Тут працює п'ять **людей**. (Five people work here.)
*   Я купив два **кілограми** яблук. (I bought two kilograms of apples.)
*   Багато **літ** перевернулось, води чимало утекло. (Source 13: `8-klas-ukrmova-avramenko-2025_s0065`)

**4. Керування дієсловами та прийменниками (Verb & Prepositional Government)**
*   Вона потребує **допомоги**. (She needs help.) (Source 6)
*   Я вчуся **української мови**. (I am learning the Ukrainian language.) (Source 6, adapted)
*   Ми приїхали з **Львова**. (We came from Lviv.)
*   Це подарунок для **тата**. (This is a gift for dad.)

## Рекомендації для вправ (Activity Concepts)

*   **Phase 1 (Recognition & Simple Production):**
    *   **Drill 1 (Absence):** Трансформація. Студент перетворює стверджувальне речення на заперечне.
        *   *Input:* `У мене є собака.` → *Output:* `У мене немає собаки.`
        *   *Input:* `Тут є кава.` → *Output:* `Тут немає кави.`
    *   **Drill 2 (Possession):** Складання словосполучень.
        *   *Input:* `книжка / мій брат` → *Output:* `книжка мого брата`
        *   *Input:* `машина / директор` → *Output:* `машина директора`

*   **Phase 2 (Numerals & Plurals):**
    *   **Drill 3 (Counting):** Студент рахує предмети на картинці, використовуючи правильну форму іменника.
        *   *Prompt:* Скільки тут столів? (картинка з 6 столами) → *Response:* `Шість столів.`
        *   *Prompt:* Скільки тут яблук? (картинка з 3 яблуками) → *Response:* `Три яблука.` (для контрасту)

*   **Phase 3 (Complex Sentences & Verb Government):**
    *   **Drill 4 (Fill-in-the-blanks):** Студент заповнює пропуски правильною формою слова в дужках.
        *   *Prompt:* `Я хочу побажати тобі ______ (щастя).` → *Response:* `щастя`.
        *   *Prompt:* `Вона боїться ______ (темрява).` → *Response:* `темряви`.
    *   **Drill 5 (Sentence unscramble):** Студент складає речення з набору слів, ставлячи іменники в правильному відмінку.
        *   *Input:* `немає / у / мене / вільний / час` → *Output:* `У мене немає вільного часу.`

## Зв'язки з іншими темами (Connections)

*   **Попередні теми (Prerequisites):**
    *   [[grammar/a1/introduction-to-nouns|Вступ до іменників]]: поняття роду (чоловічий, жіночий, середній).
    *   [[grammar/a1/nominative-case|Називний відмінок]]: базова форма слова.
    *   [[grammar/a2/numbers-1-100|Числівники 1-100]]: знання самих числівників, перед тим як вчити їхнє керування.

*   **Наступні теми (What this enables):**
    *   [[grammar/b1/cases-prepositions|Відмінки та прийменники]]: Родовий є базою для вивчення складніших прийменникових конструкцій.
    *   [[grammar/b1/verbs-of-motion|Дієслова руху]]: Конструкції напрямку `до` + Genitive, `з` + Genitive.
    *   [[grammar/b1/participles-adjectival|Дієприкметники]]: Дієприкметники узгоджуються з іменниками в роді, числі та відмінку, отже, вимагають знання родового відмінка для правильного вживання (`немає прочитаної книги`). (Source 24)

## Пов'язані статті (Related Articles)
*   [[grammar/a1/introduction-to-cases]]
*   [[grammar/a2/accusative-case]]
*   [[grammar/a2/dative-case]]
*   [[grammar/b1/genitive-masculine-ending-choice]]
*   [[grammar/b1/numbers-advanced]]
</wiki_context>

## Plan References

- 

</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this **exact** order:

- `## Частина 1: Вправи на розпізнавання (Part 1: Recognition Exercises)` (~400 words)
- `## Частина 2: Вправи на вибір (Part 2: Choice Exercises)` (~500 words)
- `## Частина 3: Практичне застосування (Part 3: Production Exercises)` (~600 words)
- `## Підсумок — Summary` (~150 words)

**Hard rule (#1189):** Every heading above MUST appear in your output **verbatim** as an `## H2` line. This includes the FINAL summary/transition section (`Підсумок: ...`, `Підсумок та перехід до M...`, etc.) — the writer's most common failure is silently dropping the closing section. Do NOT skip it. Do NOT renumber. Do NOT merge headings. The post-write quick-verify check will fail your build if any heading is missing, even if the prose itself is excellent.

Each section should follow the word budget specified. The total must reach 1500 words minimum.

---

## Content Rules

TARGET: 45-65% Ukrainian. THIS IS A HARD GATE — the audit REJECTS modules below 45%.
LANGUAGE ROLES:
- THEORY: English prose for grammar explanations — keep these SHORT (2-3 sentences max per concept).
- EXAMPLES & CONTEXT: Ukrainian — dialogues, example sentences, cultural context.
- HEADERS: Ukrainian with English in parentheses.
- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English — never mix languages within a sentence.
HOW TO REACH 45-65% UKRAINIAN (mandatory techniques):
1. After EVERY grammar explanation, add a «Читаємо українською» block: 4-6 full Ukrainian sentences demonstrating the concept just explained. These are comprehensible input, not exercises.
2. Include 3-4 multi-turn dialogues (6+ lines each) spread through the module. Dialogues are the fastest way to boost Ukrainian content.
3. Pattern boxes showing Ukrainian transformations: «стіл → стола → на столі».
4. Section introductions can be 1-2 Ukrainian sentences before the English theory.
5. :::tip and :::note callout boxes should contain Ukrainian mnemonic phrases.
If your module has long English paragraphs without Ukrainian blocks between them, you are below target. Every English paragraph should be followed by Ukrainian content.
A2 register ONLY. Concrete everyday vocabulary. No literary/poetic language. No abstract nouns. Ukrainian sentences max 15 words. Max 2 clauses. All cases allowed. Simple subordinate clauses only (який/що/коли). Aspect pairs introduced. No participles.

GRAMMAR RULES:
- Max 15 words per Ukrainian sentence
- Max 2 clauses per sentence
- All cases allowed
- Simple subordinate clauses allowed (який/що/коли)
- Aspect pairs introduced but not complex
- No participles

### Pedagogy
- Start each section with a real situation or dialogue (PPP: Present → Practice → Produce)
- Every grammar rule needs 3+ Ukrainian examples with English translations
- Teach through PATTERNS, not rules: show examples first, then name the pattern
- Cultural context where relevant — this is Ukrainian, not generic L2
- Use vocabulary from the plan's vocabulary_hints. Function words (pronouns, conjunctions) are always allowed.

### Ukrainian Language Quality
- **Zero Russian**: No ы, э, ё, ъ. No Russian words (кот→кіт, хорошо→добре, конечно→звичайно)
- **Zero Surzhyk**: No шо→що, чо→чому, тіпа→типу
- **Zero calques**: No приймати душ→брати душ, приймати рішення→ухвалювати рішення
- **Zero paronyms**: тактична≠тактовна, ефектний≠ефективний — use the right word, not a similar-sounding one
- **Natural Ukrainian**: Write how a Ukrainian teacher would explain this to a student. Not robotic, not textbook-dry, not overly casual.

### FORBIDDEN WORDS — never write these (#1189)

The following Russian words have leaked into past builds and broken modules. They are **hard-banned** — the post-write toxic-token scanner will fail your build the moment it sees one. Use the Ukrainian alternative every time, even in dialogues, even in casual prose, even when quoting a learner's mistake (use a `<!-- VERIFY -->` placeholder instead of typing the Russian form):

| Russian (FORBIDDEN) | Ukrainian (USE THIS) |
|---|---|
| хорошо | добре |
| конечно | звичайно / певна річ |
| спасибо | дякую |
| пожалуйста | будь ласка / прошу |
| ничего | нічого |
| сейчас | зараз |
| тоже | теж / також |
| здесь | тут |
| кот | кіт |
| кон | кін |

This list is enforced word-for-word by `scripts/build/quick_verify.py` (SEVERE_RUSSIANISMS). If you produce any of these tokens — even inside a quoted example, even inside a dialogue line spoken by a Russian-speaking character — the build halts immediately. There is no exception.

**Authority hierarchy (if uncertain about a word, check in this order):**
VESUM (does word exist?) → Правопис 2019 (spelling) → Горох (stress) → Антоненко-Давидович (style) → Грінченко (etymology).

**Online fallbacks:** VESUM: vesum.com.ua | Правопис: 2019.pravopys.net | Горох: goroh.pp.ua | Антоненко-Давидович: ukrlib.com.ua/books/printit.php?tid=4002 | Грінченко: hrinchenko.com | Словник.ua: slovnyk.me

### Writing Quality
- Every paragraph: ONE clear point, logical flow to the next
- Vary sentence length (short for emphasis, medium for explanation, long for examples)
- Use callout boxes (:::tip, :::caution, :::note) — at least 3 per module (mnemonics, common mistakes, cultural notes). Space them throughout the module, not clustered.
- **Dialogue formatting** — use blockquote `>` with speaker names in bold. Each turn on its own line. At A1 level, add English translation in italics after each line so learners understand what is being said. At A2, translate only new vocabulary. At B1+, no dialogue translations. Example:

> **Оленка:** Привіт! Як справи? *(Hi! How are you?)*
> **Тарас:** Добре, дякую! А у тебе? *(Good, thanks! And you?)*
> **Оленка:** Теж добре! *(Also good!)*

Without speaker names, the reader cannot tell who is speaking. NEVER use anonymous em dashes (`— text`). After each dialogue, briefly explain the key phrases and patterns the learner just saw.
- **Dialogues must sound like real people talking.** Test: would two Ukrainians actually say this to each other? If the dialogue sounds like a textbook drill ("Це кінь? — Так, це кінь."), rewrite it. Good dialogues have context, reactions, and personality:

  BAD (interrogation): "Це сім'я? — Так, це сім'я. — А де м'ясо? — М'ясо там."
  GOOD (natural): "Це твоя сім'я на фото? — Так! Нас п'ять. — А що ви їсте? М'ясо? — Так, дуже смачне!"

  BAD (labeling objects): "Це дуб. — А там коза. — Ні, це коса."
  GOOD (real reaction): "Дивись, який великий дуб! — Так, старий. А під ним — коза! — Смішна коза."

  Use the knowledge packet's textbook excerpts for dialogue patterns. Adapt real situations, don't invent drills.
- **DIALOGUE VARIETY — CRITICAL.** Each module MUST have DIFFERENT dialogue situations from other modules. Before writing any dialogue, check: have previous modules used this setting? If yes, pick a different one.

  BANNED recurring settings (already used in M01-M09): describing a room (кімната), looking at a table/bed/lamp, generic greetings with no context, labeling objects.

  REQUIRED: Every dialogue must have a SPECIFIC REAL-WORLD SITUATION that motivates the grammar being taught. The situation must be different from all other modules.

  **Module-specific dialogue settings (from plan):**
  1. **Friends studying together before a Ukrainian class — quizzing each other from notes, one struggles with genitive plural, the other explains. Скільки у тебе братів? Двох братів... ні, два брати! Ох, я завжди плутаю.**
     Speakers: Олена (студентка), Марко (студент)
     Why: Natural peer study scenario — genitive and aspect review through friendly conversation, not interrogation

  Use these settings. Do NOT substitute with a room description or generic greeting.
- **Tone: direct, clear, no filler.** State facts and teach. Don't praise the language ("beautiful", "wonderful", "unique melody"), don't praise the learner ("great job", "you've mastered"), don't narrate what you're doing ("In this section we will", "Now let's look at"). Just teach. Example:

  BAD: "The Ukrainian language has a wonderfully consistent and beautiful phonetic system."
  GOOD: "Ukrainian spelling is highly phonetic — what you see is what you hear."
- **Never guess about Ukrainian.** If you are unsure about a word, grammatical form, or phonetic rule — flag it with `<!-- VERIFY: word/claim -->`. Never invent or describe vaguely to hide uncertainty.

### Forbidden Tropes

If you write any of these patterns, the module will be rejected in review:

- **The Cheerleader:** "Great job!", "Don't worry, it's easy!", "You're doing amazing!", "Good news!" — respect the learner's intelligence; stay professional.
- **The Announcer:** "In this section, we will explore...", "Now let's dive into...", "Let's take a look at...", "To summarize what we learned..." — never use formulaic transitions. Just teach the concept directly.
- **The Translator:** "The Ukrainian word for 'cat' is 'кіт'." — instead, present naturally: "A domestic cat is a **кіт**."
- **The Wall of Text:** 3+ paragraphs of English theory without a single Ukrainian example — every concept must be anchored in immediate Ukrainian examples.
- **The Filler:** "This is a very important concept that you will use frequently in your daily life." — empty sentences that add words but not meaning. Every sentence must teach something.



### Vocabulary

**Required:** вправа (exercise), перевірка (check, test), контрольна точка (checkpoint), завдання (task), текст (text), речення (sentence), відповідь (answer)
**Recommended:** правильний (correct), варіант (option, variant), обрати (to choose), написати (to write)

### Pronunciation Videos

**Do NOT embed YouTube videos in your prose.** A downstream ENRICH tool automatically places pronunciation videos from the plan. If you embed `<YouTubeVideo>` components, they will be duplicated. Simply reference the videos' existence when relevant (e.g., "Watch the pronunciation video for this letter") but do NOT insert `<YouTubeVideo>` tags.

Available videos (for reference only — ENRICH handles placement):


---

### Style Reference (match this tone and structure)

> **(У магазині / At the store)**
> — Добрий день! Скільки коштує хліб? (Good day! How much does the bread cost?)
> — Дванадцять гривень. (Twelve hryvnias.)
> — Дякую! Ось, будь ласка. (Thanks! Here you go.)

Notice that the shopkeeper uses **Добрий день** — the formal greeting for strangers. If this were a friend, they would say **Привіт** instead.

The word **скільки** (how much/how many) is one of the most useful question words. It always pairs with the genitive case: **скільки коштує** (how much does it cost), **скільки часу** (how much time).

*Note: Short dialogues in Ukrainian with per-line English glosses. Grammar explained in English. Ukrainian sentences in blockquotes and bulleted lists.*



---

## Skeleton — Follow This Structure Exactly

A detailed paragraph-level skeleton was generated for this module. You MUST follow it precisely:
- Write every paragraph listed, in the order listed
- Hit each paragraph's word budget (+-10%)
- Place exercises exactly where the skeleton says
- Use the specific examples named in the skeleton
- Do NOT skip paragraphs, reorder sections, or add unplanned content

The skeleton replaces Step 1 (Pacing Plan) — do NOT output a <pacing_plan> block. Start writing immediately from the first section.

<skeleton>
## Частина 1: Вправи на розпізнавання (~450 words)
- P1 (~110 words): Welcome to the *контрольна точка* (checkpoint). Emphasize that this module serves as a comprehensive *перевірка* (check) of the foundational A2 grammar topics covered so far: verb aspect (вид дієслова) and the Genitive case (родовий відмінок).
- P2 (~120 words): Dialogue setting the scene. Олена and Марко are studying together before a Ukrainian class. Марко asks: "Скільки у тебе братів? Два брати чи двох братів? Ох, я завжди плутаю." Олена patiently explains: "Два брати, але п'ять братів." Марко then asks: "А сестер?" Олена replies: "У мене немає сестри."
- P3 (~110 words): Recap on recognizing verb aspect. Remind the learner that the imperfective (недоконаний вид) focuses on the process or repetition (e.g., 'читати щодня'), while the perfective (доконаний вид) signals a completed result or one-time action (e.g., 'прочитати книгу'). Explain that the upcoming *вправа* (exercise) will test this recognition.
- P4 (~110 words): Recap on Genitive case triggers. Reiterate that the most common trigger is absence ('немає часу', 'немає брата'), followed by possession ('книга брата') and basic prepositions ('з', 'без', 'для'). State that for this *завдання* (task), they must recognize these grammatical forms in a *текст* (text) and individual *речення* (sentence).
- <!-- INJECT_ACTIVITY: quiz-mixed-grammar --> [quiz, Mixed Grammar Quiz, 8 items]

## Частина 2: Вправи на вибір (~550 words)
- P1 (~130 words): Deep dive into the strategy for choosing the correct aspect. Teach learners to look for context clues: words like 'завжди', 'часто', 'довго' require imperfective (e.g., "Вчора я читав книгу три години"), whereas 'нарешті', 'раптом', or a specific timeframe for a result require perfective (e.g., "Я прочитав книгу за вечір"). Tell them they need to *обрати* (choose) the *правильний варіант* (correct option).
- P2 (~140 words): Reviewing the Genitive case with numbers. Reiterate the crucial rule: numbers 5 and above require the Genitive plural (родовий відмінок множини). Provide clear examples like "п'ять студентів", "десять книжок", "шість столів", and contrast this with numbers 2-4 which take the Nominative plural ("два столи", "три книги").
- P3 (~140 words): Forming the Genitive Plural. Highlight the zero ending with vowel insertion for feminine nouns (e.g., "думка" -> "думок", "сестра" -> "сестер") and the '-ів' ending for masculine nouns (e.g., "брат" -> "братів", "студент" -> "студентів"). Briefly mention exceptions like '-ей' ("стаття" -> "статей", "ніч" -> "ночей").
- P4 (~140 words): Instructions for the choice and transformation exercises. Explain that in the upcoming section, they will complete a sentence transformation drill. They must read the sentence and insert the correct grammatical form, choosing between aspect pairs or forming the right noun case after a number or the word 'немає'.
- <!-- INJECT_ACTIVITY: fill-in-transformation --> [fill-in, Sentence Transformation Drill, 8 items]

## Частина 3: Практичне застосування (~650 words)
- P1 (~140 words): Shifting from choosing to producing. Explain that real fluency comes from combining these rules organically in speech. Provide examples of combining both topics: using a perfective verb in the negative often requires a Genitive object (e.g., "Я не купив молока", "Вона не знайшла ключів").
- P2 (~140 words): The "Світлофор" (Traffic light) strategy for analyzing common L2 errors before writing. Remind them not to translate directly from English: "Я потребую допомогу" is incorrect; it must be "потребую допомоги". Point out other classic mistakes: "У мене немає сестра" must be "немає сестри", and "п'ять книга" must be "п'ять книжок".
- P3 (~130 words): Introduction to the error correction *вправа*. Instruct the learner to act as the teacher. They must read each provided *відповідь* (answer) and find the mixed grammar errors—identifying the wrong aspect choice, wrong genitive endings, or agreement mistakes.
- <!-- INJECT_ACTIVITY: error-correction-mixed --> [error-correction, Find and fix mixed grammar errors — wrong aspect choice, wrong genitive endings, agreement mistakes, 6 items]
- P4 (~130 words): Setup for open-ended questions. Explain that they will need to answer personal questions like "Скільки у вас братів і сестер?" (requiring genitive plural numbers) and "Що ви зробили вчора?" (requiring perfective verbs for results). Instruct them to *написати* (write) their own answers.
- P5 (~110 words): Final writing prompt instructions: plans for the weekend. Encourage them to use both aspects naturally: combining "Що ви будете робити?" (imperfective future, expressing processes like "я буду читати") and "Що ви хочете зробити?" (perfective infinitive, expressing goals like "я хочу прочитати").
- <!-- INJECT_ACTIVITY: fill-in-production --> [fill-in, Short written responses using genitive and aspect, 6 items]

Grand total: ~1650 words
</skeleton>

## Output Format

Write in Markdown. Use:
- `## Section Title` for main sections
- `### Subsection` for subsections within a section
- `**bold**` for Ukrainian words being taught. For **A1 and A2** levels, provide an English translation on first use (e.g. `**стіл** (table)`) because learners lack the vocabulary to infer meaning. For **B1 and above**, do NOT provide inline translations for standard vocabulary — the learner will use the module's словник (vocabulary table). You may provide ONE parenthetical English translation ONLY for highly abstract grammar/linguistic terms on first use (e.g. `**видова пара** (aspectual pair)`).
- Tables for paradigms (conjugation, declension)
- `:::tip` / `:::caution` / `:::note` for callout boxes
- `<!-- INJECT_ACTIVITY: {id} -->` for exercise placement (markers only — do NOT write exercise content)

Do NOT write MDX component syntax, JSON, or DSL exercise blocks (:::quiz, etc.). Plain Markdown with injection markers.

---

## MANDATORY FINAL CHECKLIST (#1189)

Before you finish writing, verify the prose against this checklist. Failing any item will fail the build.

### Section headings (verbatim)

Every heading from "Section Structure" above MUST appear as an `## H2` in your output, in order, **including the closing `Підсумок:` / `Підсумок та перехід до M...` summary**. The single most common writer failure across the B1 build has been silently dropping the final summary section. Re-read your output before stopping. If the last section in the plan is missing, write it now.

### Required vocabulary (every word must appear)

You MUST use **every word** from the list below at least once in the prose, in a natural sentence with bold + English translation. Abstract grammatical metalanguage (видова пара, дієвідміна, особове закінчення, прагматика, діагностика, дієвідмінювання, зворотний, двовидовий, одновидовий, неозначено-кількісний, etc.) is the most frequently dropped category — actively find homes for those words even if it means adding a sentence that defines them.

- [ ] вправа (exercise)
- [ ] перевірка (check, test)
- [ ] контрольна точка (checkpoint)
- [ ] завдання (task)
- [ ] текст (text)
- [ ] речення (sentence)
- [ ] відповідь (answer)

### Forbidden words (never produce)

Do not write any of these even once. Even in dialogues. Even in quoted examples. Even when illustrating a learner's mistake (use `<!-- VERIFY -->` instead). The post-write toxic-token scanner will fail the build immediately:

❌ хорошо ❌ конечно ❌ спасибо ❌ пожалуйста ❌ ничего ❌ сейчас ❌ тоже ❌ здесь ❌ кот ❌ кон

Use: добре · звичайно · дякую · будь ласка · нічого · зараз · теж · тут · кіт · кін

### Level-specific immersion check

The level-appropriate immersion rule was already injected at the top of
this prompt as `IMMERSION RULE`. Re-read it now BEFORE you stop writing.
If your level's rule contains a CHECKLIST block, walk through every item.
If it doesn't, just verify your output matches the LANGUAGE ROLES and
TARGET stated in that block.

This used to hard-code a B1+ checklist that confused A1/A2 models (where
translation blockquotes are REQUIRED at A1 and ALLOWED at A2-early).
The single source of truth is now
`scripts/pipeline/config_tables.py:IMMERSION_RULES`.

---

Begin writing now. Start with the first section heading.
