

---

## Your Writing Identity

**You are: Encouraging Ukrainian Language Guide.** Your persona is *The Conversation Partner*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **39: Контрольна точка: Відмінки та множина** (A2, A2.5 [Case Synthesis and Plurals]).

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

1. **IMMERSION TARGET: 55-75% Ukrainian — Ukrainian dominates. English for abstract grammar only.** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if immersion is outside this range. For A1 early modules, the learner cannot read Cyrillic — English must dominate. For A2+, Ukrainian must carry a significant share — add Ukrainian Reading Practice blocks, dialogues, and example paragraphs to reach the target. Too little Ukrainian fails audit just as much as too much.
2. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
3. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
4. **NO "In this lesson we will..."** — never use formulaic openers. Start with a dialogue, a question, or a situation.
5. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
6. **Place exercise markers only** — do NOT write exercises directly. Place `<!-- INJECT_ACTIVITY: {id} -->` markers where exercises should appear. A separate pipeline step generates the actual exercises from the plan's activity_hints.
7. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
8. **Hit the word target** — you MUST write 1500–2250 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
9. **NO archaic, obsolete, or rare words** — use only modern standard Ukrainian. Do not use words marked as archaic (застаріле) or dialectal in dictionaries. Example: use «кін» not «кон», use «пом'якшені» not «м'якшені». When in doubt, choose the common modern form. Your pre-training contains Russian-influenced archaic forms — verify unfamiliar words.
10. **EVERY module MUST end with `## Підсумок`** — this is the last H2 section before the file ends. It contains a self-check recap. If you forget this section, the audit REJECTS the module and you waste a retry. Write it LAST, after all other sections.

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
module: a2-039
level: A2
sequence: 39
slug: checkpoint-cases
version: '1.0'
title: 'Контрольна точка: Відмінки та множина'
subtitle: 'Перевірка знань: усі відмінки в однині та множині'
focus: review
pedagogy: Review
phase: A2.5 [Case Synthesis and Plurals]
word_target: 1500
objectives:
  - Learner can correctly form plural nouns in all 7 cases, including the 
    difficult Genitive plural with zero endings and fleeting vowels.
  - Learner can select the appropriate case based on verb government, 
    preposition, or context (time, characteristic, path) across mixed exercises.
  - Learner can identify and correct case errors in short texts, demonstrating 
    conscious control over the case system.
  - Learner can produce a short coherent text (8-10 sentences) that naturally 
    uses at least 5 different cases in both singular and plural.
dialogue_situations:
  - setting: 'Planning a wedding — every case appears naturally: Запрошення для гостей
      (gen). Подарунок нареченій (dat). Бачу наречену (acc). Фото з молодятами (inst).
      На весіллі (loc). Олено! (voc)'
    speakers:
      - Наречена
      - Подруга
    motivation: 'All 7 cases in wedding planning: gen, dat, acc, inst, loc, voc'
content_outline:
  - section: 'Частина 1: Форми множини (Part 1: Plural Forms)'
    words: 450
    points:
      - 'Exercise 1: Form the Nominative plural from 10 singular nouns across all
        відміни (mixed genders, including irregulars like дитина, людина, око).'
      - 'Exercise 2: Form the Genitive plural — the hardest forms. Given 10 nouns,
        learner produces Gen.Pl. (книга → книг, студент → студентів, місто → міст,
        ніч → ночей, теля → телят).'
      - 'Exercise 3: Complete quantity expressions with the correct Gen.Pl. form (п''ять
        ___, багато ___, скільки ___?).'
  - section: 'Частина 2: Який відмінок? (Part 2: Which Case?)'
    words: 500
    points:
      - 'Exercise 4: Multiple-choice — given a sentence with a blank, choose the correct
        case form. Includes all triggers: verbs (допомагати + Dat., бачити + Acc.,
        користуватися + Instr.), prepositions (у + Loc./Acc., з + Gen./Instr., по
        + Loc.), special uses (у четвер, у 2014 році, хлопець у светрі).'
      - 'Exercise 5: Case identification — a short text (8-10 sentences) with underlined
        nouns. Learner identifies the case of each underlined noun and the trigger
        (verb, preposition, or construction).'
      - 'Exercise 6: Error correction — 6 sentences with case errors. Learner finds
        and corrects each error (e.g., *Я допомагаю сестру → сестрі; *багато студенти
        → студентів).'
  - section: 'Частина 3: Вільне мовлення (Part 3: Free Production)'
    words: 550
    points:
      - 'Exercise 7: Guided writing — "Опишіть свій ідеальний вихідний день" (Describe
        your ideal day off). Must include: where you go (Acc./Loc.), who you meet
        (Acc./Dat.), what you do (Acc./Instr.), what you eat (Gen. for quantities,
        Acc. for items).'
      - 'Exercise 8: Dialogue completion — a dialogue with missing noun forms. Learner
        fills in 8-10 blanks using the correct case, both singular and plural.'
      - 'Self-assessment checklist: Can I form plurals confidently? Do I know which
        case each preposition takes? Can I use the case compass from M31? Ready for
        A2.6?'
vocabulary_hints:
  required:
    - перевірка (check, review)
    - контрольна точка (checkpoint)
    - завдання (task, exercise)
    - помилка (error, mistake)
    - виправити (to correct)
    - відмінок (grammatical case)
    - множина (plural)
    - однина (singular)
  recommended:
    - самоперевірка (self-check)
    - впевнено (confidently)
    - вихідний день (day off)
activity_hints:
  - type: fill-in
    focus: Mixed case drill — complete sentences requiring all 7 cases, singular
      and plural
    items: 8
  - type: quiz
    focus: Error correction — identify and fix case errors in sentences
    items: 8
  - type: group-sort
    focus: Sort noun forms by case (Nom., Gen., Dat., Acc., Instr., Loc., Voc.)
    items: 8
  - type: error-correction
    focus: Find and fix mixed case errors in sentences — wrong endings after 
      prepositions, animate/inanimate confusion, Gen.Pl. mistakes
    items: 6
references:
  - title: Заболотний Grade 6, Повторення вивченого
    notes: End-of-chapter review exercises covering all cases
  - title: Варзацька Grade 4, с. 38
    notes: Full declension table — all cases, singular and plural, as reference

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
- Confirmed: перевірка, завдання, помилка, виправити, відмінок, множина, однина, самоперевірка, впевнено.
- Not found: контрольна точка, вихідний день (Note: These are multi-word expressions; individual components *контрольний*, *точка*, *вихідний*, *день* are confirmed in VESUM).

## Textbook Excerpts
### Section: Частина 1: Форми множини (Part 1: Plural Forms)
> "У родовому відмінку множини іменники ІІ відміни мають кілька варіантів закінчень: -ів/-їв (шляхів, батьків), нульове (озер, облич), -ей (гостей, коней, очей)."
> Source: Litvinova, Grade 6

### Section: Частина 2: Який відмінок? (Part 2: Which Case?)
> "Прийменник — це службова частина мови, яка уточнює значення іменних частин мови... Порівняйте: до школи, зі школи, біля школи, недалеко від школи, без школи."
> Source: Litvinova, Grade 7

### Section: Частина 3: Вільне мовлення (Part 3: Free Production)
> "Складіть і розіграйте діалог (телефонну розмову) між однокласниками про те, як минув вихідний день."
> Source: Glazova, Grade 11

## Grammar Rules
- Родовий відмінок множини (Genitive Plural): Правопис §95 (І відміна — нульове закінчення: *баб*, *меж*), §98 (ІІ відміна — закінчення *-ів*, *-ей* або нульове: *робітників*, *коней*, *міст*).
- Вживання прийменників з відмінками: Правопис §121 — деталізує прийменники, що вимагають конкретних відмінків (напр., *без* + Gen., *до* + Gen., *по* + Loc.).

## Calque Warnings
- контрольна точка: OK (Term used in educational milestones/milestones, though "контрольна робота" is more common for traditional tests).
- вихідний день: OK — Confirmed as standard Ukrainian by Antonenko-Davydovych (e.g., "два вихідні дні").

## CEFR Check
- відмінок: A1 — OK
- множина: A1 — OK
- впевнено: B2 — **Above target** (Consider using "добре" or "самостійно" for A2 learners, though acceptable in meta-instructions).
- декілька: A2 — OK
</pre_verified_facts>


## Knowledge Packet (textbook excerpts from RAG)

**MANDATORY — this is your primary source.** The knowledge packet contains real Ukrainian textbook excerpts. Your content MUST use the terminology, notation, and pedagogical approach from these excerpts.

**Hard rules for the knowledge packet:**
1. **Use Ukrainian terminology from the packet, not English linguistics.** If the textbook says «складоподіл», you write «складоподіл» — never CVCCV or "syllable division rules" paraphrased from English phonology. If it says «відкритий склад», you write «відкритий склад» — never "open syllable type."
2. **Adopt the textbook's teaching sequence.** If the packet shows: sound model → syllable → word → sentence, follow that progression. Do not rearrange or substitute your own.
3. **Include specific examples from the packet.** If the textbook uses «ка-ша», «мо-ло-ко» to teach syllable division, use those same words (and add more). Authentic examples beat invented ones.
4. **Your pre-training is contaminated by Russian and English linguistics.** When the packet contradicts your instinct, the packet wins. Ukrainian has its own phonetic categories (голосний/приголосний, дзвінкий/глухий, м'який/твердий) that do not map 1:1 to English or Russian. Use the Ukrainian categories.
5. **Before submitting, verify:** For every linguistic term you used, check — does it appear in the knowledge packet or plan? If you used a term that's NOT in the packet (e.g., "CVCCV", "onset", "coda"), replace it with the Ukrainian equivalent from the packet.

<knowledge_packet>
# Verified Knowledge Packet: Контрольна точка: Відмінки та множина
**Module:** checkpoint-cases | **Phase:** A2.5 [Case Synthesis and Plurals]
**Textbook grades searched:** 1, 2, 3, 5

---

## Частина 1: Форми множини (Part 1: Plural Forms)

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 116
> **Score:** 0.50
>
> 116
> Досліди, чи всі іменни-
> ки можуть мати фор-
> му однини і множини.
> Я — дослідник
> Я — дослідниця
> Спостерігаю за іменниками, які вживаються тільки  
> в однині або тільки у множині
> 6   Прочитай слова і порівняй їх. 
> 	
>   Визначте число виділених іменників. Зробіть висновок, у якій 
> числовій формі вживаються ці іменники.
> дружба
> птаство
> дітвора
> сани
> окуляри
> двері
> Поясни, що спільне є між цими словами, а що — відмінне.
> Чи можна утворити форму множини від іменників у лівому 
> стовпчику?
> Чи можна утворити форму однини від іменників у правому 
> стовпчику?
> Зроби висновок про особливості вживання деяких іменників.
> Деякі іменники можуть уживатися тільки в однині: 
> дитинство, листя, молодь.
> Деякі іменники можуть уживатися тільки у множині: 
> радощі, іменини, ворота.
> 	 	
> 7   Прочитайте.

## Частина 2: Який відмінок? (Part 2: Which Case?)

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 160
> **Score:** 0.33
>
> 157
> Пробачив братові, подякував бабусі, дорікати одноклас-
> нику, кепкувати з невдахи, насміхатися з однолітка, до-
> класти зусиль, потребує допомоги, оволодівати знаннями. 
> ІІ. Виберіть із поданих два словосполучення. Складіть і запишіть по 
> одному реченню з кожним з них.
> Зверніть увагу! 
> Вибачати  
> (кому?) сестрі
> Дякувати  
> (кому?) сестрі
> Вибачте  
> (кому?) мені!
> Дякую  
> (кому?) тобі!
> 386.	Спишіть речення, ставлячи іменники, що в дужках, у потрібному 
> відмінку. Поставте усно питання від головного слова до цього імен­ника. 
> 1. Назар подякував (учителька) за допомогу. 2. Відвіду­
> вачі подякували (екскурсовод) за розповідь. 3. Маринка не 
> змогла вибачити (подруга). 4. Сергій пробачив (кривдник). 
> 5. Завжди дякуйте (батьки). 6. Ми всі подякували (Марина 
> Тарасівна) за урок.

> **Source:** zaharijchuk, Grade 1
> **Section:** Сторінка 112
> **Score:** 0.33
>
> 110
> Мої навчальні досягнення. Я вмію, можу
> 	
> Пригадай історії, які ти прочитав / прочита-
> ла. Визнач, якому малюнку відповідає кож-
> ний уривок із тексту.
> 	
> 	
> 	
> * * *
> — Зробіть для Сні-
> говика гарну-прегарну 
> Сніговичку. А біля неї 
> морквинку покладіть.
> 	
> 	
> 	
> * * * 
> — Робити добро й до-
> помагати тим, хто цього 
> потребує, завжди вчасно 
> … .
> 	 	
> 	
> * * *
> Фея дістає зі скрині 
> білу шубку й починає її 
> струшувати. 
> 	 	
> 	
> * * *
> — Бач, упертюх який! 
> Не хоче, щоб допомага-
> ли, — засміялася Тетя-
> на.

## Частина 3: Вільне мовлення (Part 3: Free Production)

> **Source:** vashulenko, Grade 2
> **Section:** Сторінка 83
> **Score:** 0.33
>
> Ивйщ1і| Пригадайте назви днів тижня. Послідовно запишіть їх.
> У середу я планую ? . 
> Для цього мені потрібно ? . 
> Я маю зробити ? .
> • Розкажіть, як ви плануєте свій день 
> (один із днів тижня на вибір). Що ви 
> в цей день будете робити? Наведіть 
> приклад такого плану за зразком.
> План — заздалегідь визначена програма дій 
> на певний час.
> 12| Поміркуй і поясни, чому так важливо планувати свій 
> час. Як планувати свій день так, щоб успішно навчатися, 
> цікаво відпочивати і досягати поставлених цілей? Чи є в 
> тебе щоденник для планування?
> Планування — ключ до успіху в житті.
> Хвилинка спілкування
> І
> І
> І 
> І
> — Цікаво, від якого слова утвори­
> лася назва щоденник?
> — Думаю, від що і день. Що ти 
> плануєш собі на цей день.
> — А може, від щодня? Щоденник, 
> бо я його беру із собою щодня.

> **Source:** golub, Grade 5
> **Section:** Сторінка 174
> **Score:** 0.50
>
> 174
> Довідка: Хто я? Де я живу? Моя сім’я. Мій найкращий 
> друг / подруга. Улюблена домашня тварина. Коли я виросту… 
> Захоплення. Найгірша подія в моєму житті. Найсмішніша 
> подія в моєму житті (За М. Мак-Доналд).
>  
> ІІ   Уявіть, що ви презентуєте власний відеоканал. Складіть текст 
> розповіді про себе і свій канал.
>  
> ІІІ   Напишіть есе «Цілеспрямованість починається з цілі».
> ОПИС. ПОБУДОВА ОПИСУ
> § 61
> Мандрівка — найкраще дозвілля
> Подорожуючи світом, пізнаєш інших. Подорожуючи Батьківщиною, 
> пізнаєш себе (З інтернету).
> Слово дня: ковилà, типчàк, інтер’ºр, інкрустàція, орнàмент, 
> вітрàж.
> 409   Розгляньте світлини і змоделюйте ситуацію: ви були з класом на 
> екскурсії і хочете описати своїм рідним ті місця, що відвідали. 
> Який тип мовлення для цього оберете? Чому?
> 410   Прочитайте текст.

> **Source:** bolshakova, Grade 2
> **Section:** Сторінка 69
> **Score:** 0.50
>
> 69
> • Що буде далі? Продовж розповідь.
> • Запиши, які справи ти робиш кожного дня тижня. 
> неділя
> понеділок
> вівторок
> середа
> четвер
> п’ятниця
> субота
> Зразок. У понеділок я … .
> розвиток мовЛення. заПроШення
> • Уяви, що ви з друзями влаштовуєте виставку ваших улюб-
> лених книжок. Запроси когось із рідних на цю виставку.
> Повідом, що це 
> запрошення
> Запрошення
> Запроси 
> на подію
> Запрошую на свято / концерт / 
> змагання / день народження
> Укажи час 
> і місце події
> Свято відбудеться о 10:00 
> в актовій залі школи
> Звернись
> Оленко і Андрійку! Тетяно Іванівно! 
> Денисе Максимовичу! Любі друзі!
> Підпиши
> Аліна і Дмитро
> самооцІнювання з теми     
> • Запиши три слова, які ти вивчив/вивчила з теми.
> • Запиши два вміння, яких ти набув/набула.
> • Запиши одне запитання, на яке ти хочеш знайти 
> відповідь на наступних уроках.


## МійКлас Theory (miyklas.com.ua)

*Ukrainian school curriculum theory — use this terminology and teaching approach.*

### Правила вживання знака м'якшення
> **Source:** МійКлас — [Правила вживання знака м'якшення](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/fonetika-grafika-orfoepiia-orfografiia-14565/pravila-vzhivannia-znaka-m-iakshennia-39904)

### Теорія:
  

*www.ua.pistacja.tv*  
 
Знаком ь позначаємо м’якість приголосних звуків на письмі.
Знак м’якшення пишемо:
- Ь пишеться після м’яких д, т, з, с, дз, ц, л, н у кінці **слова** та **складу**: *дядько, радість, низько, заносьте, гедзь, доброволець, коваль, тінь.
*  
- Після **м’яких** приголосних у **середині складу** перед о: *чотирьох, дзьоб, сьомий, льодяний, відьом*.

### Речення, його граматична основа
> **Source:** МійКлас — [Речення, його граматична основа](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/vidomosti-z-sintaksisu-i-punktuatciyi-14562/rechennia-iogo-gramatichna-osnova-pidmet-i-prisudok-39372)

### Теорія:

*www.ua.pistacja.tv*  
Речення
Реченням називаємо одне або кілька слів, що виражають закінчену думку.
Саме за допомогою речень ми спілкуємось, висловлюємо прохання, наказ, виражаємо емоції, повідомляємо інформацію.
Приклад:
- Весна іде, красу несе \(Нар. творчість\). 
- Ліс. Тиша. Благодать. 
Слова в реченні зв'язані між собою **за змістом** і **граматично**. **Граматичний зв'язок** — це поєднання за допомогою **закінчень** і **службових слів**. На початок і кінець речення вказує **інтонація**. Між реченнями робимо **паузи**.
Ознаки речення
1. Речення відображає дійсність. Інформація **стверджується** або **заперечується**, сприймається як **реальна** або **нереальна**, **можлива** або **неможлива**.
  
2. Речення є **інтонаційно** й **змістово** завершеним.
  
3.

### Іменник як частина мови
> **Source:** МійКлас — [Іменник як частина мови](https://www.miyklas.com.ua/p/ukrainska-mova/6-klas/imennik-43064/imennik-iak-chastina-movi-41979)

### Теорія:

*www.ua.pistacja.tv*  
 
**Що ж ми називаємо іменником?**
***
***Дмитро Білоус дав таке визначення іменнику:
Іменник\! Він узяв собі на плечі
Велике діло — визначати речі…
Зверни увагу\!
Назву «*іменник*» почали вживати з 1873 року. Її першим використав Омелян Партицький, який іменник називав *речівником*.
В одинадцятитомному «**Словнику сучасної української мови**» нараховують близько 135 тис. слів. Серед них і

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Частина 1: Форми множини (Part 1: Plural Forms)` (~450 words)
- `## Частина 2: Який відмінок? (Part 2: Which Case?)` (~500 words)
- `## Частина 3: Вільне мовлення (Part 3: Free Production)` (~550 words)
- `## Підсумок` (~150 words)

Each section should follow the word budget specified. The total must reach 1500 words minimum.

---

## Content Rules

TARGET: 55-75% Ukrainian.
LANGUAGE ROLES:
- PRIMARY: Ukrainian for all content — dialogues, examples, section intros, cultural context.
- ENGLISH: Only for abstract grammar concepts that need explicit explanation.
- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English. Dialogues, examples, section intros all stay Ukrainian-only.
A2 register. Concrete everyday vocabulary. No literary language, no metaphors. Ukrainian sentences max 15 words. Max 2 clauses. All cases allowed. Simple subordinate clauses only. Aspect pairs introduced. No participles.

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
  1. **Planning a wedding — every case appears naturally: Запрошення для гостей (gen). Подарунок нареченій (dat). Бачу наречену (acc). Фото з молодятами (inst). На весіллі (loc). Олено! (voc)**
     Speakers: Наречена, Подруга
     Why: All 7 cases in wedding planning: gen, dat, acc, inst, loc, voc

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

**Required:** перевірка (check, review), контрольна точка (checkpoint), завдання (task, exercise), помилка (error, mistake), виправити (to correct), відмінок (grammatical case), множина (plural), однина (singular)
**Recommended:** самоперевірка (self-check), впевнено (confidently), вихідний день (day off)

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
## Частина 1: Форми множини (Part 1: Plural Forms) (~480 words total)
- P1 (~50 words): Introduction to the checkpoint objectives. Reviewing the fundamental concept of "number" (однина та множина) and why mastering plural cases is the final hurdle of level A2.5.
- P2 (~80 words): Nominative Plural review. Detail the standard masculine/feminine endings (-и, -і) and neuter endings (-а, -я). Examples: *брати, сестри, вікна, моря*. Mention the "soft" vs "hard" stems.
- P3 (~70 words): Irregular plural nouns. Highlight essential A2-level exceptions where the stem changes or endings are unpredictable. Examples: *людина — люди, дитина — діти, око — очі, вухо — вуха, друг — друзі*.
- P4 (~60 words): Introduction to the Genitive Plural "Boss." Explain that this is the most complex form because of the variety of endings (-ів, -ей, and zero ending).
- P5 (~80 words): Masculine and Feminine Gen.Pl. endings. Explain -ів for most masculine nouns (*студентів, готелів*) and -ей for soft-ending nouns/some feminine (*ночей, очей, грошей*).
- P6 (~90 words): The Zero Ending and Fleeting Vowels. Explain how feminine and neuter nouns often drop the ending in Gen.Pl. (*книга → книг, місто → міст*). Introduce vowel insertion (о/е) to break up consonant clusters. Examples: *сумка → сумок, вікно → вікон, сестра → сестер*.
- P7 (~50 words): Quantity expressions. Recap the logic: 1 + Nom.Sg., 2-4 + Nom.Pl. (stress shift), 5+ + Gen.Pl. Examples: *два брати, п'ять братів; три книги, десять книг*.
- Exercise 1: [group-sort] Form the Nominative plural from 10 singular nouns across all genders, including irregulars (*людина, дитина, море, сторінка*). (8 items)
- Exercise 2: [fill-in] Form the Genitive plural for mixed nouns, focusing on zero endings and fleeting vowels (*книга, студент, місто, ніч, вікно*). (10 items)
- Exercise 3: [fill-in] Complete quantity expressions with the correct Gen.Pl. form (*п'ять ___ (тиждень), багато ___ (місто), скільки ___ (гроші)*). (8 items)

## Частина 2: Який відмінок? (Part 2: Which Case?) (~520 words total)
- P1 (~90 words): Verb Government (Керування дієслів). Explain that the verb "commands" the case. Focus on Dative (*допомагати мамі, дякувати вчителеві*), Accusative (*бачити будинок, любити сестру*), and Instrumental (*займатися спортом, цікавитися історією*).
- P2 (~100 words): Prepositional Triggers. Review double-duty prepositions (в/на). Explain the Accusative vs Locative distinction (Motion vs Location). Examples: *іду в школу (Acc) vs. я у школі (Loc)*. Mention Instrumental prepositions like *з (with)* and Genitive ones like *біля, для, з (from)*.
- P3 (~80 words): Instrumental for Path and Transport. Explain how we use the Instrumental case without prepositions for movement and tools. Examples: *їхати автобусом, іти лісом, писати ручкою*.
- P4 (~90 words): Special Case Uses. Review time expressions (days of the week: *у четвер*), years (*у 2024 році*), and descriptive characteristics (*чоловік у чорному светрі*).
- P5 (~90 words): The Logic of Error Identification. Teach the learner to work backward: find the noun, find its trigger (verb/preposition), then check the ending against the gender/number.
- P6 (~70 words): Animate vs Inanimate in Accusative. Brief recap of how gender and "aliveness" affect the Accusative plural. Examples: *бачу студентів (Anim) vs. бачу столи (Inanim)*.
- Exercise 4: [quiz] Multiple-choice — choose the correct case form for sentences with verbs like *допомагати, бачити, користуватися* and prepositions *по, біля, на*. (8 items)
- Exercise 5: [fill-in] Case identification — read 8 sentences and identify the case of the underlined noun and its trigger. (8 items)
- Exercise 6: [error-correction] Find and fix 6 case errors in sentences (*я допомагаю сестру; у мене багато друзі; ми були на уроці у понеділок*). (6 items)

## Частина 3: Вільне мовлення (Part 3: Free Production) (~650 words total)
- P1 (~120 words): Dialogue: Planning a Wedding. *Наречена* and *Подруга* discuss the guest list, gifts, and the ceremony. Use every case: *Запрошення (Gen), нареченій (Dat), бачу сукню (Acc), з молодятами (Instr), на весіллі (Loc), Олено! (Voc)*.
- P2 (~80 words): Analyzing the Dialogue. Break down why specific forms were used in the wedding conversation, highlighting the plural Instrumental *молодятами* and the Vocative *Олено*.
- P3 (~90 words): Guided Writing Intro: My Ideal Day Off. Explain how to structure a narrative using cases: Where you go (Acc/Loc), who you spend time with (Instr), what you buy/eat (Acc/Gen).
- P4 (~100 words): Narrative focus: "Мій вихідний." Provide a model paragraph using phrases like: *Прокидаюся о дев'ятій годині (Gen). Гуляю з друзями (Instr) у парку (Loc). Купую багато фруктів (Gen.Pl).*
- P5 (~90 words): Self-Correction Strategies. Introduce the "Case Compass" (from M31) for plurals. Tips on checking the Genitive plural "zero ending" vs. the "fleeting vowel."
- P6 (~90 words): Transition to A2.6. Encouragement for completing the synthesis of the declension system. Explain that the next phase focuses on Aspect and more complex verbs.
- P7 (~80 words): Closing thoughts on "Thinking in Ukrainian." Why using correct cases makes your speech sound natural and elegant to native speakers.
- Exercise 7: [essay-response] Guided writing — "Опишіть свій ідеальний вихідний день." Use 5 different cases (Nom, Gen, Acc, Instr, Loc) and at least 3 plural nouns. (10 sentences)
- Exercise 8: [fill-in] Dialogue completion — complete the wedding planning dialogue with missing noun forms in various cases. (10 items)

## Підсумок (~150 words)
- P1 (~150 words): Self-assessment checklist:
  - Can I form plural nouns in the Nominative? (e.g., *міста, люди*)
  - Do I know the three main Genitive Plural endings? (-ів, -ей, zero)
  - Can I fix a "fleeting vowel" error? (*вікно — вікон*)
  - Do I remember which case follows *дякувати* (Dat) or *цікавитися* (Instr)?
  - Can I use *в/на* correctly for both location and motion?
  - Am I ready to stop translating and start feeling the grammar?
  - [If "Yes" to all, welcome to A2.6!]

Grand total: ~1800 words
</skeleton>

## Output Format

Write in Markdown. Use:
- `## Section Title` for main sections
- `### Subsection` for subsections within a section
- `**bold**` for Ukrainian words being taught — EVERY bold Ukrainian word MUST have an English translation on first use, either in parentheses `**слово** (translation)` or inline `**слово** means "translation"`. No exceptions.
- Tables for paradigms (conjugation, declension)
- `:::tip` / `:::caution` / `:::note` for callout boxes
- `<!-- INJECT_ACTIVITY: {id} -->` for exercise placement (markers only — do NOT write exercise content)

Do NOT write MDX component syntax, JSON, or DSL exercise blocks (:::quiz, etc.). Plain Markdown with injection markers.

Begin writing now. Start with the first section heading.
