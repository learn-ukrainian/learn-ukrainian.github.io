<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Skeleton Prompt — Module Structure Planning

You are planning the detailed paragraph-level structure of a Ukrainian language module. Do NOT write the full content — only plan the structure.

## Your task

Create a detailed paragraph-level skeleton for module **36: Компас відмінків** (A2, A2.5 [Case Synthesis and Plurals]).

**Word target: 2000 words** of prose. Your skeleton must budget every word.

---

## Plan

<plan_content>
module: a2-036
level: A2
sequence: 36
slug: which-case-when
version: '1.0'
title: Компас відмінків
subtitle: Як обрати правильний відмінок за дієсловом, прийменником та контекстом
focus: grammar
pedagogy: PPP
phase: A2.5 [Case Synthesis and Plurals]
word_target: 2000
objectives:
  - Learner can select the correct case for a noun based on the governing verb 
    (e.g., допомагати + Dat., бачити + Acc., користуватися + Instr.).
  - Learner can select the correct case after common prepositions, including 
    prepositions that govern different cases depending on meaning (на + Acc. for
    direction vs. на + Loc. for location).
  - Learner can use Accusative for time expressions (у четвер, у середу), with 
    про (думати про майбутнє), and recognize Locative for characteristics 
    (хлопець у червоному светрі), path (бігати по кімнаті), and years (у 2014 
    році).
  - Learner can apply a systematic decision process (verb/preposition → case → 
    ending) to determine the correct form of any noun in context.
dialogue_situations:
  - setting: 'Grammar detective game — reading a Ukrainian newspaper article and identifying
      which case is used and why: Президент (nom) зустрівся з прем''єром (inst). Для
      журналістів (gen) підготували зал (acc).'
    speakers:
      - Вчитель
      - Студенти
    motivation: 'Case identification: nom, gen, dat, acc, inst, loc in real text'
content_outline:
  - section: 'Дієслово вирішує: Який відмінок після дієслова? (The Verb Decides: Which
      Case After a Verb?)'
    words: 550
    points:
      - 'Accusative verbs (most transitive): бачити, знати, любити, читати, купити,
        шукати + Acc. Я читаю книгу. Ми шукаємо ключі.'
      - 'Dative verbs: допомагати, телефонувати, дякувати, радити, заважати + Dat.
        Я допомагаю сестрі. Ми дякуємо вчителям.'
      - 'Instrumental verbs: користуватися, цікавитися, займатися, керувати + Instr.
        Він користується комп''ютером. Вона цікавиться історією.'
      - 'Genitive verbs/constructions: немає + Gen., боятися + Gen., потребувати +
        Gen. У мене немає часу. Вона боїться темряви.'
      - 'Thinking about + Acc.: думати про + Acc. (думати про майбутнє, мріяти про
        подорож).'
  - section: 'Прийменник вирішує: Один прийменник — різні відмінки (The Preposition
      Decides: One Preposition, Different Cases)'
    words: 550
    points:
      - 'на + Acc. (direction/goal): Я йду на роботу. Поклади книгу на стіл. на +
        Loc. (location): Я на роботі. Книга лежить на столі.'
      - 'у/в + Acc. (direction): Я йду в магазин. Acc. for time: у четвер, у середу,
        у п''ятницю. у/в + Loc. (location): Я в магазині. Loc. for years: у 2014 році,
        у минулому році.'
      - 'по + Loc. (path/surface): бігати по кімнаті, ходити по вулиці, подорожувати
        по Україні.'
      - 'з/із + Gen. (from/out of): вийти з дому, приїхати з Києва. з/із + Instr.
        (together with): піти з другом, кава з молоком.'
      - 'за + Acc. (in exchange/for): дякувати за допомогу, платити за квитки. за
        + Instr. (behind/after): за столом, бігти за автобусом.'
  - section: 'Особливі випадки: Час, характеристика, шлях (Special Uses: Time, Characteristics,
      Path)'
    words: 500
    points:
      - 'Acc. for days and time periods: у четвер, у середу, у п''ятницю. Цю неділю
        я відпочиваю. Наступного тижня (Gen. for next/last).'
      - 'Loc. for characteristics/description: хлопець у червоному светрі, дівчина
        в окулярах, жінка у білому пальті. Pattern: noun + у/в + Loc. describes what
        someone is wearing or looks like.'
      - 'Loc. for years and time contexts: у 2014 році, у двадцять першому столітті,
        у дитинстві.'
      - 'Loc. for path with по: бігати по кімнаті, гуляти по парку, їздити по місту.'
  - section: 'Алгоритм вибору відмінка (The Case Selection Algorithm)'
    words: 400
    points:
      - 'Step 1: Is there a preposition? → Check which case(s) it governs. Step 2:
        No preposition? → Check which case the verb requires. Step 3: Still unsure?
        → Ask the case question (Кого? Що? Кому? Ким? etc.).'
      - 'Decision tree visual: Preposition → Case. Verb → Case. Neither → Default
        Nom. (subject) or context-dependent.'
      - 'Common pitfalls: confusing на + Acc. (direction) with на + Loc. (location);
        forgetting that думати takes про + Acc., not Loc.; using Gen. instead of Dat.
        after допомагати.'
      - 'Practice: mixed sentences where learner must identify the trigger (verb or
        preposition) and choose the correct case.'
vocabulary_hints:
  required:
    - відмінок (grammatical case)
    - прийменник (preposition)
    - дієслово (verb)
    - напрямок (direction)
    - місце (place, location)
    - час (time)
    - характеристика (characteristic, description)
    - думати (to think)
    - боятися (to be afraid)
    - користуватися (to use)
  recommended:
    - алгоритм (algorithm)
    - контекст (context)
    - керувати (to manage, drive)
    - майбутнє (future)
activity_hints:
  - type: quiz
    focus: Given a sentence with a blank, choose the correct case form based on 
      the governing verb or preposition
    items: 8
  - type: group-sort
    focus: Sort prepositions by which case(s) they govern (Acc., Gen., Instr., 
      Loc.)
    items: 8
  - type: fill-in
    focus: Complete sentences with the correct noun form — mixed cases triggered
      by different prepositions and verbs, including time expressions (у 
      четвер), characteristics (у червоному светрі), and path (по кімнаті)
    items: 8
  - type: true-false
    focus: Judge whether the case used in a sentence is correct or incorrect, 
      including tricky pairs like на роботу (Acc.) vs. на роботі (Loc.)
    items: 8
references:
  - title: Заболотний Grade 6, §§59-67
    notes: Complete case system overview — when each case is used, with 
      preposition tables
  - title: Заболотний Grade 10, §§44-45
    notes: Advanced case usage — Loc. for characteristics, time expressions with
      cases
  - title: "ULP: Ukrainian Cases Overview"
    url: "https://www.ukrainianlessons.com/ukrainian-cases/"
    notes: Practical summary of all 7 cases with usage examples

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Skim these for content ideas. Reference specific examples you plan to use.

<knowledge_packet>
# Verified Knowledge Packet: Компас відмінків
**Module:** which-case-when | **Phase:** A2.5 [Case Synthesis and Plurals]
**Textbook grades searched:** 1, 2, 3, 5

---

## Дієслово вирішує: Який відмінок після дієслова? (The Verb Decides: Which Case After a Verb?)

> **Source:** vashulenko, Grade 2
> **Section:** Сторінка 80
> **Score:** 0.50
>
> НАВЧАЮСЯ СКЛАДАТИ РЕЧЕННЯ 
> З ДІЄСЛОВАМИ
> Прочитайте речення. Простежте, 
> які різні дії означає слово іде.
> складаю
> Іде катер. Іде поїзд. Іде зима. Іде час. Іде концерт.
> • Замініть у кожному реченні слово іде дієсловом, близьким 
> за значенням. Скористайтеся довідкою. Запишіть речення
> за зразком.
> Іде катер. 
> Пливе катер.
> ? годинник
> Довідка
> Відбувається, їде, минає, пливе, настає.
> б| Розглянь малюнки. Напиши, хто як пересувається,
> використавши дієслова з довідки.
> На які питання 
> відповідають 
> дієслова?
> Довідка
> Повзає, літає, плаває, стрибає, бігає.
> Хвилинка спілкування
> і
> — Як ти думаєш, як правильно сказати: 
> собака прибіг чи собака прибігла?
> — Я думаю, що можна вживати обидва 
> речення.
> — Давай перевіримо за словником. 
> Продовжте розмову.

> **Source:** vashulenko, Grade 2
> **Section:** Сторінка 82
> **Score:** 0.33
>
> НАВЧАЮСЯ ВЖИВАТИ ДІЄСЛОВА В МОВЛЕННІ
> 9| Прочитай. Випиши дієслова за абеткою.
> Щоб дізнатися новЄ про навколишній 
> світ, можна: розглядати, слухати, читати, 
> спостерігати, вимірювати, експериментувати, 
> тобто збирати відомості про довкілля. А потім 
> порівнювати, обмірковувати і робити висновки.
> доповнюю 
> складаю
> • Поцікався, у якій послідовності записав дієслова твій 
> однокласник (твоя однокласниця).
> 10 Розкажи, як ти пізнаЄш світ. Доповни речення.
> Я читаю ? .
> Я слухаю ? .
> Я спостерігаю ? .
> Я експериментую ? .
> Склади і запиши три речення про справи, 
> які тобі найбільше подобаються. Уживай 
> дібрані дієслова.
> Що ти любиш 
> робити?
> г
> Де з охотою працюють, там усе встигають.
> І
> На дерево дивись, як родить, а на людину — 
> як робить.
> 82

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 144
> **Score:** 0.50
>
> 144
> Поняття про дієслово як частину 
> мови
> Навчаюся визначати дієслова
> Пригадай і розкажи 
> у класі.
> Я — учителька
> Я — учитель
> писати
> пише
> пишуть
> писав
> написав
> напише
> 45
> Слова, які називають дії предметів і відповідають на 
> питання що робити? що робить? що роблять? що 
> робив? що зробив? що буде робити? що зробить?, 
> є дієсловами. Дієслово — це частина мови.
> 	 	
> 1   Вивчіть напам’ять вірш Володимира Верховеня. Розкажіть одне 
> одному.
>   Випишіть із вірша дієслова за абеткою. Що вони називають? На які 
> питання відповідають?
> А дієслово ні хвилини,
> повір, без дії не живе:
> працює, вчить, співає, лине,
> читає, грається, пливе.
> спільнокореневі
> різні форми слова
> Слова  
> співає, співаєш, співають
> ? 
> 2   Допиши прислів’я, користуючись довідкою.

## Прийменник вирішує: Один прийменник — різні відмінки (The Preposition Decides: One Preposition, Different Cases)

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 245
> **Score:** 0.50
>
> Ч а с т и н и   м о в и
> Самостійні 
> Іменник 
> сонце
> хто? що?
> Прикметник
> сонячний, мамин
> який? чий?
> Числівник
> три, третій
> скільки? котрий?
> Займенник
> я, ти, він
> хто? що?
> Дієслово
> сидіти
> що робити? що зробити?
> Прислівник 
> сонячно, восени
> як? де? коли? куди?
> Службові
> Прийменник
> на, в, з, до
> Не відповідають на 
> питання
> Сполучник
> і, й, та, але
> Частка
> не, б, хай
> В и д и  р е ч е н ь
> За метою 
> висловлювання
> За емоційним 
> забарвленням
> За будовою
> розповідне
> окличне
> просте
> питальне
> неокличне
> складне
> спонукальне
> Ч л е н и   р е ч е н н я
> Головні
> Другорядні
> Підмет
> Присудок
> Означення
> Обставина
> Додаток
> хто? 
> що?
> що робить?
> що зробить?
> який? чий?
> як? де? 
> коли?
> та ін.
> кого? чого? 
> кому? чому? 
> та ін.

> **Source:** vashulenko, Grade 2
> **Section:** Сторінка 80
> **Score:** 0.33
>
> НАВЧАЮСЯ СКЛАДАТИ РЕЧЕННЯ 
> З ДІЄСЛОВАМИ
> Прочитайте речення. Простежте, 
> які різні дії означає слово іде.
> складаю
> Іде катер. Іде поїзд. Іде зима. Іде час. Іде концерт.
> • Замініть у кожному реченні слово іде дієсловом, близьким 
> за значенням. Скористайтеся довідкою. Запишіть речення
> за зразком.
> Іде катер. 
> Пливе катер.
> ? годинник
> Довідка
> Відбувається, їде, минає, пливе, настає.
> б| Розглянь малюнки. Напиши, хто як пересувається,
> використавши дієслова з довідки.
> На які питання 
> відповідають 
> дієслова?
> Довідка
> Повзає, літає, плаває, стрибає, бігає.
> Хвилинка спілкування
> і
> — Як ти думаєш, як правильно сказати: 
> собака прибіг чи собака прибігла?
> — Я думаю, що можна вживати обидва 
> речення.
> — Давай перевіримо за словником. 
> Продовжте розмову.

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 130
> **Score:** 0.25
>
> 130
> 41
> Змінювання прикметників за родами
> Навчаюся змінювати прикметники за родами
> 	 	
> 1   Розгляньте таблицю. Зробіть висновок про змінювання 
> прикметників за родами (в однині).
> Чоловічий рід
> дерев’яний стіл
> синій диван
> Жіночий рід
> дерев’яна шафа
> синя скатертина
> Середній рід
> дерев’яне ліжко
> синє крісло
> В однині прикметники змінюються за родами. Прикметники 
> чоловічого роду мають закінчення -ий, -ій, жіночого роду — 
> закінчення -а, -я, середнього роду — закінчення -о, -є.
> У множині прикметники не змінюються за родами. Для 
> всіх родів вони мають однакове закінчення -і.
> 	 	
> 2   Прочитайте. Назвіть прикметники, використані в тексті. Визначте 
> їхній рід.
> Ми живемо в новому будинку. Сюди 
> ми переїхали нещодавно. Як заходиш 
> до квартири, потрапляєш у просторий 
> передпокій.

## Особливі випадки: Час, характеристика, шлях (Special Uses: Time, Characteristics, Path)

> **Source:** bolshakova, Grade 2
> **Section:** Сторінка 21
> **Score:** 0.33
>
> 21
> розвиток мовЛення. ІсторІя
> • Вірш. Заголовок. Послідовність подій. Автор
> УЇКЕНД1
> Тиша. Сон. Будильник. Ранок.
> Мама. Тато. Джек. Сніданок.
> Сумка. Термос. Ковбаса.
> Ліфт. Автобус. Шлях. Краса!
> Стежка. Ліс. Дуби. Ялиці.
> Вуж. Гриби. Пташки. Суниці.
> Білка. Небо. Синь. Роса.
> Тиша. Термос. Ковбаса.
> Комарі. Вогонь. Димок.
> Шлях. Автобус. Ліфт. Замок.
> Ванна. Мило. Ліжко. Сон.
> Джек зітхає, наче слон.
> Згадує оту красу —
> Запахущу ковбасу.
> Григорій Фалькович
> 1 Уїкенд — час відпочинку й розваг від суботи до понеділка.
> • Розкажи, про що вірш. Коли відбуваються події — влітку 
> чи взимку? Де вони відбуваються? Чому ти так думаєш? 
> • Порівняй вірш і малюнок. Як би ти намалював / намалю-
> вала цю історію? Чому?
> • Зміни час подій. Розкажи цю історію своїми словами 
> так, наче події відбуваються взимку.

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 277
> **Score:** 0.50
>
> 277
> Складні випадки наголошування
> здалека
> зобрази ти
> зо зла
> зрання
> зру чний
> К
> камбала
> катало г
> ки шка
> кінчи ти
> ко лесо
> ко лія
> кори сний
> ко сий
> котри й
> кро їти
> кропива
> кулінарія
> ку рятина
> Л
> лате
> листопад
> лю стро
> М
> мабу ть
> мере жа
> Н
> навчання
> нанести 
> напі й
> начинка
> ненавидіти
> ненависний
> ненависть
> нести 
> ні здря
> нови й
> О
> обіця нка
> обрання
> обру ч (іменник)
> одинадцять
> одноразо вий
> ознака
> о лень
> отаман
> о цет
> П
> пави ч
> пе карський
> перевезти 
> перевести 
> переля к
> перенести 
> пере пад
> піце рія
> по друга
> по значка
> по ми лка
> помо вчати
> поня ття
> посере дині
> привезти 
> привести 
> при морозок
> принести 
> промі жок

## Алгоритм вибору відмінка (The Case Selection Algorithm)

> **Source:** golub, Grade 5
> **Section:** Сторінка 132
> **Score:** 0.50
>
> 132
> Між частинами складного речення ставимо кому.
> Сполучники, що з’єднують частини складного речення: 
> і (й), та, але, проте, зате, однак; що, щоб, бо, тому 
> що та інші.
> Частини складного речення поєднують також 

... (truncated for context window)
</knowledge_packet>

---

## Output format

Output a single `<skeleton>` block. For each section from the plan's `content_outline`, list every paragraph and exercise with its word budget and content focus.

Be SPECIFIC about what each paragraph covers — not "explain grammar" but "explain accusative case endings for feminine nouns (-у/-ю), with 3 examples: книгу, каву, землю."

```
<skeleton>
## Section Title (~XXX words total)
- P1 (~XX words): [specific content — what concept, what examples, what comparison]
- P2 (~XX words): [specific content]
- Exercise: [type from activity_hints, focus, number of items]
- P3 (~XX words): [specific content]
...

## Section Title (~XXX words total)
- P1 (~XX words): [specific content]
...

## Підсумок (~150 words)
- P1 (~150 words): [Follow the plan's points for this section EXACTLY. If the plan says "Self-check questions", output a bulleted Q&A list — NOT prose. If the plan says "recap", write a brief recap.]

Grand total: ~2000 words
</skeleton>
```

## Rules

1. **Every paragraph has ONE clear purpose.** If you can't describe it in one sentence, split it.
2. **Word budgets must sum to 2000+.** Aim for ~10% overshoot (2200 words) — writers tend to undershoot.
3. **Section budgets must match the plan's `content_outline` word allocations** (±10%).
4. **Place exercises in the correct section.** Each activity hint in the plan may have a `section:` field that tells you which section it belongs in. Place that exercise AFTER the teaching content of that section, never before. If no `section:` is specified, place the exercise after the most relevant teaching point. **CRITICAL: An exercise must ONLY test concepts already taught above it. Never test a concept from a later section.**
5. **Name specific Ukrainian examples** you plan to use in each paragraph. This prevents vague skeletons that produce vague content.
6. **Dialogues count as paragraphs.** Budget 80-120 words per multi-turn dialogue.
7. **No meta-commentary.** Output only the `<skeleton>` block, nothing else.
