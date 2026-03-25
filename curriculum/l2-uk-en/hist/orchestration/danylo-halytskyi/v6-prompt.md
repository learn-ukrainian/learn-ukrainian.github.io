<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Too short: 3295 words (target: 5000, minimum: 4250)
- NOTE: Plan expects 4 exercise(s) but content has 1
</correction_directive>

LEARNINGS FROM PAST BUILDS (same error patterns seen before):
- [GLOBAL] сес-тра is a VALID word division per Правопис 2019 §49. Do NOT mark it as an error. Phonetic syllabification (се-стра) and typographic word division (сес-тра) follow different rules — both are correct in their respective contexts.
- [GLOBAL] Ukrainian textbooks teach a hands-on-EARS test for voicing (закрий долонями вуха), NOT a hand-on-throat test. The hand-on-throat test is a valid phonetics technique but must NOT be attributed to Ukrainian textbooks. Source: Кравцова 2019, Grade 2, p.39.
- [GLOBAL] Do NOT invent Ukrainian words for minimal pairs. "Сір" is NOT a word meaning "grey" — the correct form is "сірий". Use verified minimal pairs only: кит/кіт, бити/біти, лис/ліс.
- [GLOBAL] NEVER frame Ukrainian as "lacking" or "missing" letters that Russian has. Ukrainian has its own 33-letter alphabet — it is complete. Do NOT write "Ukrainian lacks Ъ, Ы, Э" or "Ukrainian doesn't have these Russian letters." Instead, highlight what Ukrainian HAS: Ґ, Є, Ї, І are unique to Ukrainian. Present Ukrainian on its own terms.
- [a2/comparison] Same errors (WORD_COUNT): V6 build failed after 3 attempts
- [b1/metalanguage-sounds] Same errors (WORD_COUNT): V6 build failed after 3 attempts

# V6 Writing Prompt — Seminar Module Content Generation

Ви пишете модуль українського семінару для студентів рівня B2+. Весь контент пишеться **українською мовою** (90-100%). Англійська допускається лише для: (1) коротких пояснень складних термінів, (2) порівняльних контекстів, де це педагогічно обґрунтовано.

## Your task

Write the full prose content for seminar module **23: Королювання Данила Романовича** (HIST, B2.3a [Українська історія]).

**Target: 5000–7500 words** of Ukrainian prose.

---

## Step 1: Pacing Plan (output this FIRST)

Before writing any content, output a `<pacing_plan>` block:

```
<pacing_plan>
Section 1 "Title": ~XXX words — [1-sentence content focus]
Section 2 "Title": ~XXX words — [1-sentence content focus]
...
Total: 5000+ words
</pacing_plan>
```

Then begin writing. Follow your own pacing plan.

---

## 8 Hard Rules

1. **WRITE IN UKRAINIAN.** This is an immersion seminar. All prose, headings, explanations, and examples in Ukrainian. English translations only for specialized terms the learner hasn't seen before, in parentheses: складнопідрядне речення *(subordinate clause)*.
2. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points — dates, quotes, `[!myth-buster]`, `[!decolonization]` tags. Cover ALL of them.
3. **Follow the plan's section structure exactly.** Each section from `content_outline` becomes an H2 heading. Do not merge, split, or reorder sections.
4. **Ukrainian quotes: «...»** for all quoted Ukrainian text.
5. **Write exercises directly** in the DSL format specified below. Seminar exercises are different from core modules — reading comprehension, critical analysis, essay prompts.
6. **NO meta-commentary.** Do not add "Content notes:", word counts, or self-audit sections.
7. **Hit the word target** — 5000–7500 words. Seminar modules are LONG. Expand with primary source analysis, historiographic debate, and contextual detail.
8. **NO archaic, obsolete, or rare words** unless the plan specifically discusses them (e.g., OES/RUTH tracks). Use modern standard Ukrainian for your own prose. Quote historical sources in their original language with explanation.

**Note:** Do NOT add stress marks (´) to any Ukrainian word.

## Pedagogy: Content-Based Instruction (CBI)

Seminar modules use **CBI**, not PPP (Present-Practice-Produce). The structure is:

1. **Розминка** — Warm-up: engage the learner with a surprising fact, question, or primary source excerpt
2. **Читання** — Reading: extended passage analyzing the topic from Ukrainian sources
3. **Аналіз** — Analysis: break down the reading, highlight key vocabulary, discuss historiographic perspectives
4. **Дискусія** — Discussion: critical thinking questions, comparison with other sources
5. **Підсумок** — Summary: key takeaways, vocabulary consolidation

## Exercises — Seminar Types

Seminar exercises differ from core modules. Use these DSL formats:

**Reading comprehension** (quiz after a passage):
```
:::quiz
title: "Перевірка розуміння"
---
- q: "Як автор характеризує політику Ярослава?"
  o: ["як дипломатичну і виважену", "як агресивну і мілітарну", "як пасивну і слабку"]
  a: 0
:::
```

**Critical analysis** (essay-response — no DSL, just a prompt block):
```
:::note
**Завдання для роздуму:**
Порівняйте оцінку Ярослава Мудрого у Грушевського та в радянській історіографії. У чому принципова різниця підходів?
:::
```

**Vocabulary in context** (fill-in with academic terms):
```
:::fill-in
title: "Академічна лексика"
---
- sentence: "Ярослав запровадив перший правовий ___ на Русі."
  answer: "кодекс"
:::
```

## Decolonization

This curriculum teaches Ukrainian history and culture **on Ukrainian terms**. Key principles:

- **Never present Ukrainian history as a subset of Russian history.** Kyivan Rus is Ukrainian heritage, not "shared" or "common East Slavic."
- **Name Russian imperial narratives explicitly.** When Russian historiography claims something, say «російська імперська історіографія стверджує...» and then present the Ukrainian primary sources.
- **Use Ukrainian names.** Ярослав Мудрий, not Yaroslav the Wise. Київська Русь, not Kievan Rus.
- **The [!myth-buster] tag in plans** means: explicitly confront a common myth with evidence. State the myth, then demolish it with sources.
- **The [!decolonization] tag** means: explicitly address how this topic has been distorted by Russian/Soviet historiography.

## Authority hierarchy for Ukrainian verification

1. **VESUM** — does this word/form exist?
2. **Правопис 2019** — is it spelled correctly?
3. **Горох** — stress position, frequency
4. **Антоненко-Давидович** — natural Ukrainian or calque?
5. **Грінченко** — etymology

**Online fallbacks:**
- VESUM: https://vesum.com.ua/
- Правопис 2019: https://2019.pravopys.net/
- Горох: https://goroh.pp.ua/
- Антоненко-Давидович: https://www.ukrlib.com.ua/books/printit.php?tid=4002
- Грінченко: https://hrinchenko.com/

---

## Plan

<plan_content>
module: hist-023
level: HIST
sequence: 23
slug: danylo-halytskyi
version: '3.0'
title: Королювання Данила Романовича
subtitle: Король України та європейський вибір
focus: history
pedagogy: CBI
phase: B2.3a [Українська історія]
word_target: 5000
objectives:
- Учень розуміє значення коронації Данила Галицького
- Учень може аналізувати дипломатичну гру між Сходом та Заходом
- Учень може пояснити цивілізаційний вибір Данила
content_outline:
- section: Вступ — Єдиний коронований король Русі
  points:
  - Чому коронація 1253 року унікальна в історії України — відбулася в Дорогочині, а не в столиці, легітимізувала 
    державу в очах Європи [!history-bite]
  - Данило як символ європейського вибору — перший легітимний «Король Русі» (Rex Russiae), визнаний Папою Римським
  words: 700
- section: Боротьба за Галичину (1205-1238)
  points:
  - Дитинство вигнанця після смерті батька Романа — початок «сорокарічної війни» за повернення батьківської спадщини
  - Боротьба з угорцями та боярською опозицією — унікальний випадок, коли боярин Владислав Кормильчич проголосив себе 
    князем [!context]
  - 'Об''єднання Галичини і Волині — перемога під Дорогочином (1238) над хрестоносцями: «Не личить держати нашу батьківщину
    крижевникам»'
  words: 700
- section: Монгольська навала та дипломатія виживання
  points:
  - Поразка 1240 року та візит до Батия — після блискучої перемоги під Ярославом (1245) Данило змушений їхати в Орду за 
    ярликом
  - «Зле є почесті татарської» — принизливий прийом, необхідність пити чорний кумис, але збереження гідності через 
    відмову від язичницьких ритуалів [!quote]
  - Стратегія лавірування між Сходом і Заходом — отримання ярлика як спосіб виграти час для будівництва фортець
  words: 700
- section: Коронація 1253 року — Європейський вибір
  points:
  - Союз з Папою Інокентієм IV — переговори про надання корони в обмін на церковну унію та військову допомогу
  - Обіцянка хрестового походу, що не відбувся — Папа закликав християн Богемії та Польщі, але реальної допомоги не 
    надійшло
  - Значення королівського титулу — це був політичний союз, а не зміна віри; православні обряди збереглися 
    [!myth-buster]
  words: 700
- section: Первинні джерела — Галицько-Волинський літопис
  points:
  - Унікальність літопису як джерела — світський, емоційний стиль, на відміну від церковних київських літописів
  - 'Поетична мова та героїчний стиль — характеристика короля: «Книжником бо він був великим і філософом»'
  words: 700
- section: Деколонізаційний погляд — Русь ≠ Росія
  points:
  - Чому Росія ігнорує Данила Галицького — його європейський вибір руйнує міф про «спільноруську» єдність з Ордою
  - Галицько-Волинська держава як альтернативний центр Русі — титул Rex Russiae доводить, що Русь — це Україна, а 
    Московія була улусом Орди [!decolonization]
  - Європейська орієнтація vs московський ізоляціонізм — контраст з Олександром Невським, який став названим сином Батия
  words: 700
- section: Підсумок — Спадщина короля
  points:
  - Смерть 1264 року та занепад династії — похований у Холмі, держава проіснувала до середини XIV ст.
  - Данило як символ незалежності — заснування Львова (1256) та Холма як нових центрів цивілізації [!culture]
  words: 800
vocabulary_hints:
  required:
  - історія (history) — [noun] study of past events
  - держава (state) — [noun] organized political community; Галицько-Волинська держава
  - народ (people) — [noun] nation or ethnic group
  - влада (power) — [noun] political authority or control
  - період (period) — [noun] length of time
  - подія (event) — [noun] occurrence; історична подія
  - джерело (source) — [noun] origin of information; первинне джерело
  - спадщина (heritage) — [noun] inheritance; батьківська спадщина
  - коронація (coronation) — [noun] act of crowning; коронація Данила
  - ярлик (yarlyk/patent) — [noun] decree of the Golden Horde khan
  - навала (invasion) — [noun] sudden attack by large forces; монгольська навала
  - літопис (chronicle) — [noun] historical account; Галицько-Волинський літопис
  recommended:
  - аналіз (analysis) — [noun] detailed examination
  - контекст (context) — [noun] circumstances forming a setting
  - вплив (influence) — [noun] capacity to have an effect
  - наслідки (consequences) — [noun] results or effects
  - унія (union) — [noun] political or church alliance; церковна унія
  - дипломатія (diplomacy) — [noun] management of international relations
  - легітимність (legitimacy) — [noun] conformity to the law or rules
activity_hints:
- type: reading
  focus: Первинні джерела
  items: 4
- type: essay-response
  focus: Критичний аналіз
- type: critical-analysis
  focus: Аналіз причинно-наслідкових зв'язків між подіями
  items: 3
- type: critical-analysis
  focus: Критична оцінка історичних тверджень та міфів
  items: 5
persona:
  voice: Senior Professor of History
  role: Royal Chronicler
grammar:
- Titles and honorifics
- Diplomatic register
prerequisites:
- mykhailo-chernigivskyi
connects_to:
- galytsko-volynska-derzhava
references: []
register: академічний

</plan_content>

## Knowledge Packet (RAG sources)

<knowledge_packet>
# Verified Knowledge Packet: Королювання Данила Романовича
**Module:** danylo-halytskyi | **Phase:** B2.3a [Українська історія]
**Textbook grades searched:** 1, 2, 3, 5

---

## Вступ — Єдиний коронований король Русі

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 39
> 	
> Прочитай букви, виділені блакитним кольо-
> ром. Яке слово утворилося? Який заголовок 
> до вірша можна дібрати?
> У нас красивий, гарний край:
> Квіти, море, річка, гай!
> Рідне все: поля, діброви,
> А сади які чудові!
> Їх краса — це білий цвіт...
> Ненька наша, Україна,
> Адже ти для нас єдина!
>                                     Дмитро Гонтар
> 	
> Знайди на «полі складів» слова — назви пред-
> метів, які є народними символами України. 
> Звертай увагу на кольори складів. 
> ле
> пи
> тів
> лас
> лю
> ви
> оф
> ка
> ли
> ка
> ер
> ле

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> Прочитай слова. У кожному рядку визнач «зайве» слово. 
> Обґрунтуй свій вибір.
> ріка 
> озеро рука 
> море
> береги село 
> кручі поля
> Проведи дослідження.
> • Поміркуй, чи можуть існувати міста, села зі схожими назвами.
> • Чи відомо тобі про них? Якщо це так, розкажи.
> Прочитайте текст.
> ЧИ Ж ОДИН НА СВІТІ КИЇВ?
> — Агов! Я — Київ, столиця Української держави. 
> Збудований славним Києм. Понад півтори тисячі років 
> височію над Дніпровими кручами.
> — А мене звали Київець. Я також був збудований Києм, 
> але вже на Дун

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 80
> ÐÎÇÐ²ÇÍßÞ ÂËÀÑÍ²
> ÐÎÇÐ²ÇÍßÞ ÂËÀÑÍ²
> ² ÇÀÃÀËÜÍ² ÍÀÇÂÈ 
> ² ÇÀÃÀËÜÍ² ÍÀÇÂÈ 
> 1. Спиши речення, вставляючи пропущені слова. Підкрес-
> ли іменники.
> 3. Випиши в колонку власні назви з тексту про Коростень. 
> Добери й запиши поруч загальну назву до кожного слова.
> 1. Світязь і Синевир — це … . 2. Україна й Італія — 
> це … . 3. Леся Українка і Грицько Бойко — це … . 
> Проведи дослідження!
> 1. Поясни, що називають іменники, написані з великої букви.
> 2. Як думаєш, вони є власними назвами чи загальними? 
> Перевір

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> Розвиток людства упродовж історії
> 135
> Пам’ятна монета на честь 
> 1000-ліття початку князювання 
> Ярослава Мудрого (2019 р.)
> Настільна медаль 
> «Король Данило Галицький»
> Поштова марка
> України
> «750 років з часу
> заснування Львова» 
> (2006 р.)
>      Факт чи фейк?
> Королівська корона Данила Романовича — 
> правителя Королівства Руського — стала ле-
> гендою так само, як і її власник. Чи насправді 
> існувала корона, чи це міф?
> Перегляньте відео «Король Данило Га-
> лицький і його корона». Визначте, якої версії 
> до

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 51
> Склади речення з одним зі слів.
> 	
> Україна	
> українець	
> у-кра-їн-ський
> 	
> в Україні	
> українка	
> у-кра-їн-ська
> 	
> до України	
> українці	
> у-кра-їн-ське
> Я ЗАВЖДИ пишу слово Україна з великої букви.
> 
> Розкажи, що ти знаєш про Україну. Скористайся підказ-
> ками. Чим славиться твій рідний край? 
> Київ — столиця 
> України.
> Дніпро — найдовша 
> річка України.
> Говерла — найвища 
> гора України.
> Азовське море — 
> наймілкіше у світі.
> Хортиця —  
> найбільший острів 
> на Дніпрі.
> Уляна та Устим живуть в Україні. Вони ходя

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> 13| Прочитай назви міст та їхніх мешканців. 
> Постав до слів питання і запиши у дві колонки.
> хто? 
> що?
> _ і __ _ 
> і
> Київ — киянин, Харків — 
> харків'янин, Суми — сумчанин, 
> Донецьк — донеччанин, Львів — 
> львів’янин.
> Як називають
> мешканок цих
> міст?
> г
> киянин — 
> киянка
> • Поясни, які зі слів є загальними назвами, а які — власними. 
> Як їх правильно писати?
> 14| Прочитай. Назви слова — загальні назви.
> Володимирська гірка — у місті Києві. На ній стоїть 
> пам’ятник князю Володимиру.
> Княжа гора — у місті Льво

## Боротьба за Галичину (1205-1238)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 38
> 	
> «Збери» склади на весняних «хмарах». Утво-
> ри нові слова.
> 	
> Розгадай ребус.
> ,
> ,
> ,,,
> кра
> Ки
> ї
> при
> їв
> ї
> їхали
> ра
> на
> са
> на
> Укра
> 	
> Утвори нові слова.
> КИЇВ
> Наш Київ розіслався
> На горах над Дніпром,
> Садами заквітчався,
> Мов дівчина вінком.
> Його побудували
> Брати, батьки, діди.
> І славно захищали
> Від лютої біди… 
>           Максим Рильський
> У К Р А Ї Н С Ь К О Ї
> 1 2 3 4 5 6 7 8 9 1011
> 1 3 4
> 5 11
> Pidruchnyk.com.ua

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> собі фірмовий одяг. Їжаки відкрили майстерню з по-
> шиття спортивної форми, а ведмежата — крамницю 
> із кросівками. Усе заради спорту.
>  
> 	 Про що розповідається у творі?
>  
> 	 Хто головні персонажі казки? Яка подія трапилася з 
> ними? Які почуття їм довелося пережити?
>  
> 	 Як ти думаєш, яка причина поразки? Що з цього приводу 
> думали звірята? Який висновок можна зробити з описаної 
> події?
>  
> 	 Знайди і прочитай речення, у якому виражено головну 
> думку твору.
>  
> 	 Назви ознаку, яка доводить, що цей

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 50
> 5. Разом 
> з 
> однокласниками/однокласницями 
> змініть 
> форму поданих слів і доберіть до них спільнокореневі 
> слова.  Запишіть  їх  за  зразком.
> 5
>                
>                оборона — …
>                     ворог — …
>              перемога — …
> 6. Прочитай повідомлення Ґаджика. Поясни, як розумієш 
> виділені сполучення слів. Придумай заголовок до тексту.
> 6
> На неприступному березі річки Дністåр височіє 
> Хотèнський замок. Він має дуже давню історію. 
> Близько тисячі років тому на цьо-
> му місці Київ

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 85
> ЛІТЕРАТУРНІ КАЗКИ
> Молоді, міцні, здорові,
> А найменший – щось страшне!
> Вже з трьох літ боров мене!
> ...Раз колись коня мій син
> Перекинув через тин.
> ...А сердитий!.. Тільки слово –
> І скипів, і вже готово!
> Що підвернеться під руку,
> Все потрощить, як макуху!
> Скажеш: «Сину, час вставати!», –
> І тікай, тікай із хати,
> Бо, що трапиться на очі,
> Те тобі й на спину скоче!
> Сміх і сльози... Чулий, добрий,
> І розумний, і хоробрий,
> І всіх любить нас, либонь,
> А зачепиш – як огонь!
> Князю! В мене є надія,
> Що поду

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 5
> 1
> жовтня
> 28
> жовтня
> Перша 
> неділя
> жовтня
> 1
> вересня
> День знань
> Вітаємо всіх хлопчиків, дівчаток! 
> В руках у вас новенькі «Букварі».
> Для вас сьогодні — особливе свято:
> Сьогодні ви вже учні, школярі!
> День працівників освіти
> Покрова Пресвятої Богородиці
> День козацтва 
> День захисників і захисниць України
> Пам’ятайте ж бо, малята,
> Справ у вас — ой як багато!
> Та бабусю й дідуся 
> Не забудьте привітати.
> День бабусь і дідусів
> ОСІНЬ
> Осінні  свята  України

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> Зачин — це невелика за обсягом частина твору. 
> В ній ми знайомимося з героями чи подіями твору. 
> Основна частина — найбільша за обсягом. 
> У ній розкривається основний зміст твору. 
> Кінцівка — невелика частина. Найчастіше в кінцівці 
> описується, як усе закінчилось.
> З якої частини ти дізнався (дізналася), звідки прийшла мама?
> У якій частині сказано, як домовлялися брати?
> З якої частини ти довідався (довідалася), як хлопці поділили 
> гостинець?
> Якти гадаєш, чому Дмитрик погодився на пропозицію Сашка

## Монгольська навала та дипломатія виживання

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 12
> Ч ч
> Бачу Ч, ч (че). Чую [ч].
> і
> о
> ч о р н и
>  [  –  •  –   |  –• | = • ]
> *
> с о н е ч к
> п о р і ч к и
> а
> о
> у
> и
> і
> Ч
> ча
> чо
> чу
> чи
> чі
> а
> о
> у
> и
> і
> ач
> оч
> уч
> ич
> іч
> Ч
> ча
> че
> чо
> чо
> боти
> ловік
> че
> твер
> сно
> чу
> дово
> ти
> В чаплі
> Чорні
> Черевички.
> Чапля
> Чапа
> До водички.
> Ігор Січовик
> Pidruchnyk.com.ua

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> 9[ Про кого так кажуть?
> Воду носить — рука болить, 
> кашу варить — рука болить, 
> а каша готова — і рука здорова.
> • Зроби висновок про роль наголосу.
> У
> Добра людина хоче добра в

... (truncated for context window)
</knowledge_packet>

{SKELETON_SECTION}

{CORRECTION_SECTION}


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
## Вступ — Єдиний коронований король Русі (~750 words)
- P1 (~150 words): Introduce Danylo Romanovych (1201–1264) as a central figure in medieval history, emphasizing his unique status: he is the only formally crowned King of Rus' in Ukrainian history. Mention the pivotal year 1253 and the unexpected location of the coronation in the border town of Dorohychyn. Use the target words: історія, коронація.
- P2 (~150 words): Contextualize the geopolitical nightmare of the 13th century — a period of extreme turmoil for Eastern Europe caught between Western powers and the Mongol Empire. Explain the immense diplomatic weight of the title Rex Russiae (Король Русі) and how it legally and politically integrated the Galician-Volhynian state into the European monarchical system. Use the target word: держава.
- P3 (~150 words): [!history-bite] Detail the specific circumstances of Dorohychyn. Contrast this peripheral stronghold with traditional capitals like Kyiv or Halych. Explain why the coronation happened there — during a military campaign against the Yotvingians, reflecting the immediate, pragmatic political necessity of the moment rather than a grand ceremonial plan.
- P4 (~150 words): Introduce the overarching theme of the module: Danylo's civilizational choice. Frame his entire reign as a continuous, high-stakes balancing act between appeasing the overwhelming, devastating military power of the East (the Golden Horde) and seeking political leverage and military aid from the West (the Papacy). Use the target words: влада, період.
- P5 (~150 words): Outline the dramatic narrative arc of his life that the module will explore: from a displaced, exiled orphan to a triumphant warrior reuniting his lands, then a humiliated vassal forced to drink kumis, and finally, a recognized European monarch. Establish a formal, academic tone suitable for a senior history professor.

## Боротьба за Галичину (1205-1238) (~750 words)
- P1 (~150 words): Begin with the sudden, tragic death of his father, the powerful Roman Mstyslavych, at the Battle of Zawichost in 1205. Describe the immediate collapse of the unified Halych-Volhynian state and the subsequent exile of the four-year-old Danylo and his mother, Anna. Introduce the concept of fighting for one's батьківська спадщина (paternal heritage). Use the target word: спадщина.
- P2 (~150 words): Detail the grueling period known as the "Forty Years' War" for Halychyna. Explain the destructive role of the powerful, independent-minded boyar opposition. [!context] Highlight the unprecedented historical anomaly: the boyar Volodyslav Kormylchych declaring himself prince in 1213 — a gross, scandalous violation of the Rurikid dynastic rules. Use the target word: подія.
- P3 (~150 words): Describe the severe external threats during Danylo's youth. Focus on the constant military and political interference of the Kingdom of Hungary and the Kingdom of Poland in the internal affairs of Halychyna and Volhynia. Detail Danylo's methodical, decades-long struggle to reclaim his birthright piece by piece.
- P4 (~150 words): Focus on the turning point: the crucial Battle of Dorohychyn (1238). Describe Danylo's decisive victory over the crusading Order of Dobrzyń (Teutonic Knights). Analyze his famous chronicle quote justifying the campaign: «Не личить держати нашу батьківщину крижевникам» (It is not fitting for crusaders to hold our fatherland).
- P5 (~150 words): Conclude this phase with his ultimate triumph: the complete reunification of Halychyna and Volhynia just prior to the Mongol storm. Mention his strategic expansion, culminating in his entry into Kyiv in 1239, where he left his loyal voivode Dmytro to organize the city's defense against the impending invasion.

## Монгольська навала та дипломатія виживання (~750 words)
- P1 (~150 words): Describe the apocalyptic catastrophe of 1240. Detail the bloody fall of Kyiv and the devastating, unstoppable march of Batu Khan's army through Halychyna and Volhynia. Emphasize the massive demographic destruction of cities and the sudden, violent collapse of the old geopolitical order. Use the target words: навала, народ.
- P2 (~150 words): Transition to the Battle of Yaroslav (1245). Detail Danylo's definitive, crushing victory over the combined Hungarian-Polish coalition and the rebellious Galician boyars. Explain the irony: he finally secures his western borders and domestic absolute power, only to immediately face the existential threat of the Mongol Empire from the East.
- P3 (~150 words): Detail the agonizing, forced journey to the capital of the Golden Horde (Sarai) in 1245-1246. Describe the immense psychological and political pressure on the proud prince. Explain the mechanics of Mongol dominance: he had to personally bow to Batu Khan to receive the official patent to rule. Use the target word: ярлик.
- P4 (~150 words): [!quote] Analyze the profound meaning behind the chronicle's famous phrase: «О, лихіша лиха честь татарськая!» (Oh, worse than evil is Tatar honor!). Describe the humiliating reception, the requirement to drink black mare's milk (kumis), but emphasize how Danylo masterfully maintained his core dignity by refusing overt pagan rituals.
- Exercise: essay-response, focus: Критичний аналіз (Analyze Danylo's decision to travel to the Horde: evaluate the balance between humiliating pragmatism and political survival).
- P5 (~150 words): Analyze his overarching survival strategy. Argue that submitting to the Horde was a calculated, tactical retreat to buy time. He used this coerced peace to actively rebuild his military infrastructure, constructing heavily fortified cities like Kholm, Lviv, and Danilov, while secretly seeking Western allies.

## Коронація 1253 року — Європейський вибір (~750 words)
- P1 (~150 words): Examine the desperate search for anti-Mongol allies. Detail Danylo's intense diplomatic overtures to Pope Innocent IV. Contrast their differing objectives: Danylo sought a massive, pan-European military crusade against the Mongols; the Papacy's primary goal was achieving ecclesiastical union and expanding Catholic influence.
- P2 (~150 words): Trace the complex negotiations leading up to 1253. Explain the transactional nature of the deal: the Pope offered the royal crown in exchange for church union (recognizing papal supremacy). Describe Danylo's political hesitation, his initial rejection of the crown without military guarantees, and his careful calculations.
- P3 (~150 words): Describe the coronation ceremony itself in Dorohychyn. Detail his reception of the crown, scepter, and title from the papal legate Opizo. Explain the profound historical significance: official, documented recognition of the Kingdom of Rus' (Regnum Russiae) as a legitimate entity within the Catholic/European political sphere.
- P4 (~150 words): Discuss the ultimate failure of the promised crusade. Note that while the Pope issued bulls urging the Christians of Bohemia, Moravia, Serbia, and Pomerania to march to Danylo's aid, absolutely no tangible military help ever arrived. Highlight the geopolitical reality of a divided, distracted Europe.
- P5 (~150 words): [!myth-buster] Clarify the complex religious aspect of the coronation. Emphasize that it was a purely political alliance, not a genuine spiritual conversion. Explain that the church union was never actually implemented on the ground; Orthodox rites, traditions, and the authority of the Orthodox hierarchy in Halych-Volhynia were fully preserved.

## Первинні джерела — Галицько-Волинський літопис (~750 words)
- P1 (~150 words): Introduce the Halych-Volhynian Chronicle (Галицько-Волинський літопис) as the absolute primary historical text for understanding this era. Contrast its distinct secular, knightly, and pragmatic tone with the earlier, more heavily clerical and moralizing Kyivan chronicles. Use the target words: джерело, літопис.
- P2 (~150 words): Discuss the unique literary structure of the chronicle. Explain that it is not strictly annalistic (a dry year-by-year account) in its original form, but rather reads like a continuous, dramatic heroic narrative focusing exclusively on the epic deeds, virtues, and struggles of Roman Mstyslavych and his sons.
- P3 (~150 words): Analyze the rich language and style of the text. Note its highly poetic language, vivid, cinematic descriptions of sieges and battles, and highly emotional, subjective assessments of historical characters and enemy forces. Provide a specific example of its descriptive power regarding military engagements.
- P4 (~150 words): Focus on the chronicle's glowing portrayal of King Danylo. Quote the text directly: «Книжником бо він був великим і філософом» (For he was a great scribe and philosopher). Analyze how the anonymous chronicler deliberately constructs the image of a perfect, idealized, wise, and incredibly brave ruler.
- Exercise: reading, focus: Первинні джерела, items: 4 (Read and analyze short original excerpts from the chronicle regarding the Dorohychyn coronation and the tense journey to Batu Khan).
- P5 (~150 words): Critically evaluate the historical reliability of the chronicle. Acknowledge that while it is heavily biased towards the Romanovych dynasty and acts as court propaganda, it remains an invaluable, indispensable repository of details about 13th-century diplomacy, military tactics, boyar politics, and daily life.

## Деколонізаційний погляд — Русь ≠ Росія (~750 words)
- P1 (~150 words): Address modern historiographical manipulation. Explain exactly why Russian imperial and subsequent Soviet historical narratives systematically downplayed, marginalized, or ignored Danylo Halytskyi, heavily preferring to elevate figures like Alexander Nevsky who fit a different ideological mold.
- P2 (~150 words): [!decolonization] Analyze the exact meaning of the title Rex Russiae (King of Rus'). Clarify that in 13th-century European diplomatic terminology, "Rus'" referred strictly to the territories of modern Ukraine (Kyiv, Halych, Volhynia), and was considered completely distinct from the northern Suzdal-Vladimir (later Muscovite) lands.
- P3 (~150 words): Sharply contrast Danylo's pro-European vector with Alexander Nevsky's pro-eastern, collaborationist vector. While Danylo desperately sought Western alliances and a crown to fight the Horde, Nevsky became the adopted son of Batu Khan and violently suppressed anti-Mongol uprisings in Novgorod to enforce tribute collection.
- Exercise: critical-analysis, focus: Критична оцінка історичних тверджень та міфів, items: 5 (Deconstruct the imperial "common Russian state" myth by analyzing the drastically different geopolitical realities and choices of Halych-Volhynia versus Suzdal in the 13th century).
- P4 (~150 words): Argue that the Halych-Volhynian state was the direct, true political successor to Kyivan Rus'. It successfully preserved the statehood, urban culture, and political traditions of Rus' for another full century after the devastating fall of Kyiv, shifting the center of gravity westward.
- Exercise: critical-analysis, focus: Аналіз причинно-наслідкових зв'язків між подіями, items: 3 (Trace the causal link between the Mongol destruction of Kyiv, the coronation of Danylo, and the shifting geopolitical centers of Eastern Europe).
- P5 (~150 words): Conclude the section by affirming that Danylo's reign provides irrefutable historical proof of the existence of a distinct, western-oriented Ukrainian political entity and identity in the Middle Ages, fundamentally separate from the development of the Muscovite state.

## Підсумок — Спадщина короля (~850 words)
- P1 (~170 words): Describe the tragic final years of his reign. Detail the painful realization that the promised Western military help would never materialize. Describe the forced, humiliating dismantling of his newly built fortifications under intense pressure from the Mongol general Burundai in 1259, illustrating the bitter pragmatism required for physical survival.
- P2 (~170 words): Detail Danylo's death in 1264 and his burial in his beloved, newly constructed capital, Kholm. Describe the immediate political aftermath: the division of the realm among his sons (Lev, Shvarno, Mstyslav). Emphasize that despite this fragmentation, the institutional foundation of the state he built survived intact.
- P3 (~170 words): [!culture] Highlight his massive urban development and economic legacy. Focus on the founding of major new cities, most notably Lviv (named after his son Lev, first officially mentioned in 1256) and the capital Kholm. Explain how these cities quickly became vital, booming centers of international trade, crafts, and culture.
- P4 (~170 words): Summarize his long-term civilizational legacy. Emphasize that Danylo Romanovych firmly anchored the Ukrainian lands within the Central European cultural, economic, and political sphere. Show how this fundamental western orientation persisted through the subsequent Lithuanian and Polish eras of Ukrainian history.
- P5 (~170 words): Provide a final academic assessment of the "King of Ukraine". Conclude that he was not merely a tragic warrior, but a visionary state-builder who brilliantly navigated the most catastrophic, apocalyptic period in Eastern European history, leaving an enduring legacy of political resilience and a clear European identity.

Grand total: ~5350 words
</skeleton>
