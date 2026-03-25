# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **42: Hey, Friend!** (A1, A1.7 [Communication]).

**Target: 1200–1800 words** of prose (Ukrainian examples count toward word total, headings and exercise placeholders do not).

---

## Step 1: Pacing Plan (output this FIRST)

Before writing any content, output a `<pacing_plan>` block. Evaluate each section from the plan and commit to a word budget. This prevents frontloading early sections and rushing later ones.

```
<pacing_plan>
Section 1 "Title": ~XXX words — [1-sentence content focus]
Section 2 "Title": ~XXX words — [1-sentence content focus]
...
Summary: ~150 words
Total: 1200+ words
</pacing_plan>
```

Then begin writing the module content. Follow your own pacing plan — each section must hit its word budget (±10%).

---

## 8 Hard Rules

1. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
2. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
3. **NO "In this lesson we will..."** — never use formulaic openers. Start with a dialogue, a question, or a situation.
4. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
5. **Write exercises directly** — write complete exercises in the DSL format below. Include real questions, real answers, and real distractors. A downstream tool converts them to interactive React components.
6. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
7. **Hit the word target** — you MUST write 1200–1800 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
8. **NO archaic, obsolete, or rare words** — use only modern standard Ukrainian. Do not use words marked as archaic (застаріле) or dialectal in dictionaries. Example: use «кін» not «кон», use «пом'якшені» not «м'якшені». When in doubt, choose the common modern form. Your pre-training contains Russian-influenced archaic forms — verify unfamiliar words.

**Note:** Do NOT add stress marks (´) to any Ukrainian word — a deterministic tool handles this after you write.

## Exercises — Write Them Directly

After each key teaching point, write an exercise directly in DSL format.

**CRITICAL: Each exercise MUST match a specific `activity_hints` entry from the Plan.**
- Use the EXACT `type` specified (quiz, fill-in, match-up, group-sort, true-false)
- Follow the `focus` description EXACTLY — if the plan says "Answer: У тебе є...? Так / Ні", your quiz must test exactly that pattern
- Match the `items` count specified
- Do NOT invent different exercises — the plan's activity_hints are the specification

Write REAL content: real questions, real answers, real distractors. Every exercise must be solvable by a learner who read the preceding prose.

### DSL Format

Use these exact formats. Each block starts with `:::type` and ends with `:::`.

**Quiz** (multiple choice):
```
:::quiz
title: "Звук чи літера?"
---
- q: "Що ми чуємо і вимовляємо?"
  o: ["звуки", "літери", "слова"]
  a: 0
- q: "Що ми бачимо і пишемо?"
  o: ["літери", "звуки", "речення"]
  a: 0
:::
```

**Fill-in** (complete the sentence):
```
:::fill-in
title: "Complete the greeting"
---
- sentence: "Привіт! Як ___?"
  answer: "справи"
- sentence: "Дякую, ___."
  answer: "добре"
:::
```

**Match-up** (connect pairs):
```
:::match-up
title: "Match false friend letters to their real sounds"
---
- left: "В"
  right: "sounds like [в], not [b]"
- left: "Н"
  right: "sounds like [н], not [h]"
:::
```

**Group-sort** (classify into categories):
```
:::group-sort
title: "Classify letters"
---
groups:
  - name: "Голосні"
    items: ["А", "О", "У", "І"]
  - name: "Приголосні"
    items: ["М", "К", "Б", "Ш"]
:::
```

**True-false**:
```
:::true-false
title: "True or false?"
---
- statement: "В українській мові 33 літери."
  answer: true
- statement: "Голосних звуків більше, ніж приголосних."
  answer: false
:::
```

Spread exercises evenly throughout the module. Never cluster them.

### Approved Exercise Patterns

Use these Ukrainian textbook-inspired patterns (Заболотний, Авраменко) instead of generic "quiz" types:

- **Знайди помилку (Find the error):** Give 3 correct sentences and 1 with an error. Learner identifies the mistake. Tests: grammar rules, calques, Russianisms.
- **Обери правильне слово (Choose the right word):** Fill in the blank from 2-3 options (synonyms, paronyms, or confusable words). Tests: vocabulary nuance, register.
- **Утвори пару (Match-up):** Match words to antonyms, translations, or grammatical pairs (e.g., masculine → feminine). Tests: vocabulary, morphology.
- **Розподіли (Group-sort):** Sort items into 2-3 categories (e.g., голосні vs приголосні, hard vs soft consonants). Tests: foundational phonetics, grammar classification.
- **Склади речення (Build a sentence):** Give scrambled words, learner arranges into correct order. Tests: word order, sentence structure.
- **Знайди місце (Find the right place):** Give 4 sentences with blanks and 4 words — each word fits exactly one sentence. Tests: contextual meaning, collocations.

---

## Plan

<plan_content>
module: a1-042
level: A1
sequence: 42
slug: hey-friend
version: '1.2'
title: Hey, Friend!
subtitle: Олено! Тарасе! Друже! Мамо! — calling people by name
focus: grammar
pedagogy: PPP
phase: A1.7 [Communication]
word_target: 1200
objectives:
- Form vocative case for common names and family words (Олено! Тарасе! Мамо!)
- Use vocative in greetings and direct address (Привіт, Андрію!)
- Recognize vocative endings for masculine (-е, -у/-ю) and feminine (-о, -ю, -є) nouns
- Address people naturally using vocative in everyday situations
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Meeting a friend: — Олено, привіт! Як справи? — Добре, дякую, Тарасе!
    А в тебе? — Теж добре. Олено, ти знаєш мого брата? — Ні. — Андрію, ходи сюди!
    Це Олена. Олено, це Андрій. Vocative forms: Олено (Олена), Тарасе (Тарас), Андрію
    (Андрій).'
  - 'Dialogue 2 — At home: — Мамо, де мій телефон? — На столі, синку. — Тату, а де
    ключі? — У кишені, дочко. — Бабусю, ми йдемо! — Добре, будьте обережні! Family
    vocatives: мамо, тату, синку, дочко, бабусю.'
- section: Кличний відмінок (The Vocative Case)
  words: 300
  points:
  - 'Ukrainian has a special case for calling someone — кличний відмінок. In English
    you just say the name: ''Olena, come here!'' In Ukrainian the name CHANGES: Олена
    → Олено, ходи сюди! This is not optional — Ukrainians always use vocative when
    addressing someone. Grade 4 helper word: Кл. (!) — the exclamation mark reminds
    you: you''re calling someone, so the ending changes.'
  - 'Why vocative matters: Олена прийшла. (Olena came.) — nominative, talking ABOUT
    her. Олено, ходи сюди! (Olena, come here!) — vocative, talking TO her. Using nominative
    to address someone sounds unnatural in Ukrainian. It''s like saying ''Hey, him!''
    instead of ''Hey, you!'' in English.'
- section: Закінчення кличного (Vocative Endings)
  words: 300
  points:
  - 'Feminine names and nouns (-а → -о): Олена → Олено, мама → мамо, сестра → сестро,
    Оксана → Оксано, подруга → подруго, бабуся → бабусю (-ся → -сю). Names on -ка:
    Наталка → Наталко, Ірка → Ірко. Names on -ія: Марія → Маріє (not Маріо!). Names
    on -а (long): Катерина → Катерино, Тетяна → Тетяно.'
  - 'Masculine names and nouns: Hard consonant → -е: Тарас → Тарасе, Іван → Іване,
    брат → брате, пан → пане. Soft consonant / -й → -ю: Андрій → Андрію, дідусь →
    дідусю, вчитель → вчителю. Special: друг → друже (г → ж), козак → козаче (к →
    ч). Тато → тату (exceptional -у ending, memorize).'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Vocative quick reference: | Pattern | Nominative → Vocative | Example | | Feminine
    -а | -а → -о | Олена → Олено, мама → мамо | | Feminine -ія | -ія → -іє | Марія
    → Маріє | | Feminine -ся | -ся → -сю | бабуся → бабусю | | Masculine hard | +
    -е | Тарас → Тарасе, брат → брате | | Masculine -й/soft | + -ю | Андрій → Андрію,
    вчитель → вчителю | | Special (г, к) | г→ж, к→ч + -е | друг → друже | Self-check:
    How do you call your family? мама → ? тато → ? брат → ?'
vocabulary_hints:
  required:
  - друг (friend, m)
  - подруга (friend, f)
  - брат (brother, m)
  - сестра (sister, f)
  - пан (Mr., m)
  - пані (Mrs./Ms., f)
  recommended:
  - синку (son — vocative, from син)
  - дочко (daughter — vocative, from дочка)
  - козак (Cossack, m)
  - вчитель (teacher, m)
  - бабуся (grandmother, f)
  - дідусь (grandfather, m)
activity_hints:
- type: fill-in
  focus: 'Write vocative: Олена → Олено, Тарас → Тарасе, мама → мамо'
  items:
  - Олена → {Олено}
  - Тарас → {Тарасе}
  - мама → {мамо}
  - Іван → {Іване}
  - сестра → {сестро}
  - Андрій → {Андрію}
  - подруга → {подруго}
  - брат → {брате}
  - Марія → {Маріє}
  - бабуся → {бабусю}
- type: quiz
  focus: 'Choose correct vocative: (Олена / Олено / Оленю), привіт!'
  items:
  - question: ___, привіт!
    options:
    - Олено
    - Олена
    - Оленю
  - question: Як справи, ___?
    options:
    - Тарасе
    - Тарас
    - Тарасу
  - question: Дякую, ___!
    options:
    - мамо
    - мама
    - маме
  - question: Ходи сюди, ___!
    options:
    - Іване
    - Іван
    - Івану
  - question: Будь обережний, ___!
    options:
    - синку
    - синок
    - синке
  - question: Що ти робиш, ___?
    options:
    - брате
    - брат
    - брату
  - question: Добрий день, ___!
    options:
    - пане
    - пан
    - пану
  - question: Привіт, ___!
    options:
    - Андрію
    - Андрій
    - Андріє
- type: group-sort
  focus: 'Sort vocative endings: -о (feminine) vs -е (masculine hard) vs -ю (masculine
    soft)'
  groups:
  - name: -о (feminine)
    items:
    - Олено
    - мамо
    - сестро
  - name: -е (masculine hard)
    items:
    - Тарасе
    - Іване
    - брате
    - пане
  - name: -ю (masculine soft)
    items:
    - Андрію
    - дідусю
    - вчителю
- type: fill-in
  focus: 'Complete dialogue: ___, привіт! Як справи? (name → vocative)'
  items:
  - — {Олено|Олена}, привіт! Як справи?
  - — Добре, дякую, {Тарасе|Тарас}!
  - — {Мамо|Мама}, де мій телефон?
  - — На столі, {синку|синок}.
  - — {Бабусю|Бабуся}, ми йдемо!
  - — Добре, до побачення, {Андрію|Андрій}!
connects_to:
- a1-043 (Please Do This)
prerequisites:
- a1-041 (Checkpoint — Food and Shopping)
grammar:
- 'Vocative case (кличний відмінок): special endings for direct address'
- Feminine -а → -о (Олена → Олено), -ія → -іє (Марія → Маріє)
- Masculine hard → -е (Тарас → Тарасе), soft/-й → -ю (Андрій → Андрію)
- 'Consonant alternation: друг → друже (г → ж)'
register: розмовний
references:
- title: State Standard 2024, §4.2.3.4
  notes: 'Vocative case — address forms. A1 scope: common patterns only.'
- title: 'Grade 4 textbook: Кличний відмінок (Заболотний)'
  notes: Helper word Кл. (!). Feminine -а→-о, masculine hard→-е, soft→-ю.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Hey, Friend!
**Module:** hey-friend | **Phase:** A1.7 [Communication]
**Textbook grades searched:** 5, 6, 7

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 218
> Доброго ранку! Добрий день! Привіт! Радий бачити тебе. 
> * * *
> До побачення! На все добре! Гарного дня! Бувайте здорові! До зу-
> стрічі!
> Бажаю успіхів! Хай щастить! Рада була зустрітися.
> * * *
> Вибачте. Пробачте. Прошу вибачити (пробачити).
> Даруйте. Перепрошую. Вибачте, що турбую.
> * * *
> Дякую. Щиро дякую. Я тобі дуже вдячний. Будь ласка. Нема 
> за що.
> 528.	І. ПОПРАЦЮЙТЕ В ПАРАХ. Уявіть, що хтось із вас опинився в 
> чужому місті і йому необхідно з’ясувати, де розміщено стадіон (цирк чи 
> театр). А

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 234
> Дотримання цих правил робить вас великодушними 
> людьми. Намагайтеся виражати співчуття дієво: обро-
> біть рану, дайте чисту серветку, цукерку, обійміть, 
> доберіть слова. 
> У структурі тексту втішання мають бути такі 
> складники: 
>   звертання до адресата на ім’я (Алінко! Тимку!); 
>   спонукання до змін психоемоційного стану (Не хви-
> люйся! Заспокойся!); 
>   висловлення співчуття, повідом лення інформації, 
> що може покращити стан (Я розумію тебе, співчу-
> ваю. Але в мене для тебе гарна новина!);

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> 246
> 246
> – Якщо хтось не виконує твоїх забаганок, це ще не означає,
> що йому не можна довіряти! – розвів руками дідусь. – І ти по-
> винен знати, що не кожне бажання можна виконати.
> * * *
> – Добридень! – привіталася Наталка з дідусем. – Яка ж гар-
> на у вас крамничка!
> – Добридень! Радий, що тобі подобається! Щось тобі запропо-
> нувати?
> – Знаєте, я шукаю подарунок для подруги. Щось не дуже 
> дороге, але таке, що запам’ятається.
> – А яка твоя подруга?
> – Дуже хороша людина. Добра, спокійна, завжди допоможе,

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> Той і розказав йому все, що з ним діялось. А напослідок усякого добра 
> два кораблі подарував дядькові, сказавши:
> – Я забуваю все те, що ти мені робив злого. А як приїдеш у своє місто, то 
> розказуй усім, що краще жити правдою, аніж кривдою. 1 НAебAіж – тут: 
> син брата.

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 235
> Так тривало вже давно. Усе враз припинилося минулої 
> зими напередодні Різдва.
> — Любий, мені так шкода, — сказала мама, присівши на 
> краєчку ліжка того ранку. — Я знаю, що ти його дуже любив, 
> але дідусь більше не з нами.
> Ця новина розчавила мене, неначе важезний чобіт малень-
> ку мураху. Як це не з нами?… (О. Войтенко).
>  
> ІІ   Напишіть текст утішання. Які з поданих нижче формул утішан-
> ня доцільно використати в цій ситуації?
> 1. Бог посилає випробування кожній людині, і їх потрібно 
> долати. 2.

> **Source:** unknown, Grade 7
> **Score:** 0.33
>
> Твій друг Артем 
> — Привіт, Артеме! Лікарі готують мене до операції. Я думаю, що вона 
> пройде успішно, адже коли думки з добром, то й добро з людиною. Згадую 
> Психологічна  повість  Оксани  Радушинської  «Метелики  в  крижаних  панцирах»

## Кличний відмінок (The Vocative Case)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 36
> 79
>   Запишіть речення, обравши правильний варіант написання слів 
> іншомовного походження. Поясніть свій вибір.
> 1. Цю ві(л / лл)у свого часу придбав й офірував Національному 
> музею сам митрополит (А. Хома). 2. Хай би люди обсипали 
> одне одного не конфе(т / тт)і й серпантином, а свіжоскоше-
> ною травою!.. (Р. Бредбері). 3. Співак Олександр Положинський 
> передав ко(л / лл)екцію старожитностей, яку зібрав його 
> батько, Волинському краєзнавчому музею. 4. Го(л / лл)андці 
> вирізняються чесністю, щирі

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> § 28. Кличний відмінок  
> 141
> Добродійко, 
> добродійка; 
> добродій, 
> добродію; 
> пан 
> Євген, пане Євгене; пані Оксано, пані Оксана; панно 
> Ганно, панна Ганна; шановна громада, шановна гро-
> мадо; Тамара Іванівна, Тамаро Іванівно; Іване Вікторо-
> вичу, Іван Вікторович.
> 2. Яку форму ви оберете, звертаючись до особи?
> 3. Випишіть форми звертань. Усно складіть із ними речення.
> В офіційному мовленні рекомендовані певні варі-
> анти звертання до особи, що мають переважно форму 
> кличного відмінка.
> Форма звертан

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> 171
> ЛІТЕРАТУРА АНТИВОЄННОГО СПРЯМУВАННЯ
> спитає Наталя Миколаївна. – Заходьте, будь ласка»... Климко 
> усміхнувся і, сам того не помічаючи, пішов швидше.
> Нараз у висілку глухо хлопнув постріл. Потім коротко дир-
> кнув автомат. «Невже знову італійці?» – подумав Климко. (...)
> Знову бахнув постріл, уже ближче, куля десь угорі тівкнула.
> І тут Климко побачив, що від переїзду назустріч йому біжить 
> якийсь чоловік – босий, у солдатському галіфе з розв’язаними 
> поворозками й у гімнастерці без реміняки.
> Він

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 48
> Лексикологія. Синоніми
> Також синоніми допомагають уникнути повторів одного чи 
> спільнокореневих слів, що, як ми знаємо, є лексичною помилкою . 
> Порівняйте:
> Я розмовляю кількома мовами. — Я володію кількома 
> мовами.
> Дібрати синоніми допоможе словник синонімів .
> Вправа 61
> 1. Прочитайте вірш та уривок із вірша . Випишіть із  них синоніми .
> Тамара Левченко
> ХТО ДІД?
> З’їжджалися дочки у гості до діда: 
> Ось там Завірюха санчатами їде, 
> За нею Метелиця слідом мете, 
> Хурделиця Хугу з собою веде. 
> А ті

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 106
> 1.	Прочитайте sms-повідомлення та виконайте завдання.
> Дорог.. Віталіє! Чекаю тебе в 
> парку о 18:00. 
> Люб.. Віталію!
> Буду вчасно. До зустрічі! 
> А.	 У якому відмінку вжито імена?
> Б.	 Яке закінчення пропущено в першому повідомленні, а яке — у другому?
> Кличний відмінок використовуємо у звертаннях до людей або тварин: 
> Світлано, братику, котику, а в художній літературі — і до неживих 
> предметів: Зоре моя вечірняя, зійди над горою (Т. Шевченко). 
> І відміна
> -о
> іменники твердої групи
> мамо, Миколо, к

> **Source:** unknown, Grade 7
> **Score:** 0.33
>
> 184
> 184
> Зверніть увагу! 
> Прийменник уживаємо разом з іменником, займенником 
> або числівником.
> КОЛО ДУМОК. Поясніть, чому в колонці ліворуч виділені слова є приймен-
> никами, а в колонці праворуч – прислівниками.
> прийменник
> прислівник
> Поблизу села було джерело.
> Поблизу було джерело.
> Зустрілися напередодні свята.
> Зустрілися напередодні.
> І. Прочитайте речення. Визначте, до яких частин мови належать
> виділені слова. Обґрунтуйте свою думку.
> 1. Забіліли сніги навколо Києва, загуляли хуртовини (О. До-
> вж

## Закінчення кличного (Vocative Endings)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> Дайте відповідь на запитання однокласника / однокласниці та оцініть його / її 
> відповідь. кульмінація
> зав’язка           розв’язка

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> § 31. Відмінювання іменників ІІ відміни   
> 159
> Закінчення іменників ІІ відміни 
> в  кличному відмінку однини
> Тверда група
> М’яка група
> Мішана група
> 1. Закінчення -е 
> для безсуфіксних 
> іменників: Петре, 
> студенте, пане, 
> друже.
> Але: тату, сину, 
> діду
> 1. Закінчення 
> -ю для більшо-
> сті іменників: 
> лікарю, вчи-
> телю, добродію, 
> Ігорю
> 1. Закінчення 
> -е для більшості 
> іменників: сто-
> роже, Довбуше, 
> пісняре 
> 2. Закінчення -у
> для іменників із 
> суфіксами -к, -ик, 
> -ок та іншомов-
> них імен на г, к, 
> х: син

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> 18
> 18
>  
> Ю
> Є
> Ю
> І. Запишіть іменники в кличному відмінку.
> Назар, Назарій, Миколай, Ілля, Юлія, Юля, Таїсія, Тая, Таї-
> са, мама, матуся, Олег, батько, президент, дівчинка, друг Сергій, 
> Ганна Василівна, Ігор Тарасович, ластівка, Херсон.
> ІІ. Складіть і запишіть речення з іменем свого друга / своєї подруги в кличному 
> відмінку. 
> ІІІ. Утворіть від виділених імен чоловічі й жіночі імена по батькові та запишіть.
> КОЛО ДУМОК. 1. Чи м

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Кличний відмінок (The Vocative Case)` (~300 words)
- `## Закінчення кличного (Vocative Endings)` (~300 words)
- `## Підсумок — Summary` (~300 words)
- `## Підсумок` (~150 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 20-35% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — brief and clear. Show, don't tell.
- PARADIGM TABLES: Conjugation/declension tables with all cells Ukrainian.
- EXAMPLE LISTS: Ukrainian sentences in bulleted lists (each: Ukrainian — English gloss).
- DIALOGUES: Mini-dialogues in blockquotes with English gloss per line.
- PATTERN BOXES: Show transformations: `читати → читай → читайте`.
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences go in tables, bulleted lists, dialogues, or pattern boxes.
Ukrainian sentences max 10 words. Mix container types.

HARD GRAMMAR RULES (audit will reject violations):
- Max 10 words per Ukrainian sentence (STRICT — count every word)
- ONLY 1 clause per sentence (no compound sentences)
- Dative case FORBIDDEN (no мені, тобі, йому, їй, вам, їм, -ові/-еві endings)
  Exception: нам is taught as decodable vocabulary in M1 (reading drill word, not grammar)
  Exception (M15 what-i-like): Dative forms мені/тобі/йому/їй/нам/вам/їм allowed
    ONLY in the fixed construction «Мені подобається + noun/infinitive». Teach as a memorized
    chunk — do NOT explain dative case rules or paradigms.
- Instrumental case FORBIDDEN (no з другом, з мамою, -ом/-ою/-ем/-ею endings)
  Exception: M37 introduces basic Instrumental 'з' (кава з молоком)
- NO subordinate clauses: який/яка/яке, що-clause, коли, якщо, тому що, бо, щоб, поки are ALL BANNED
- Only imperfective aspect verbs
- No participles
- Allowed cases: Nominative, Accusative, Locative (from M30), Genitive (basics), Vocative

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
- Use callout boxes (:::tip, :::caution, :::note) sparingly — max 3 per module
- **Dialogue formatting** — use blockquote `>` with speaker names in bold. Each turn on its own line. At A1 level, add English translation in italics after each line so learners understand what is being said. At A2, translate only new vocabulary. At B1+, no dialogue translations. Example:

> **Оленка:** Привіт! Як справи? *(Hi! How are you?)*
> **Тарас:** Добре, дякую! А у тебе? *(Good, thanks! And you?)*
> **Оленка:** Теж добре! *(Also good!)*

Without speaker names, the reader cannot tell who is speaking. NEVER use anonymous em dashes (`— text`). After each dialogue, briefly explain the key phrases and patterns the learner just saw.
- Dialogues: natural, not stilted. Real situations, real responses. **Use the knowledge packet** — it contains textbook excerpts with real Ukrainian dialogues and situations. Adapt them, don't invent artificial conversations. A dialogue about немає should show someone SEARCHING for something and not finding it (keys, notebook, phone), not an interrogation. A dialogue about the market should sound like a real market conversation. If the knowledge packet has a textbook dialogue on the topic, use that pattern.
- **Tone:** Authoritative but warm. Like a skilled Ukrainian teacher — confident, clear, culturally grounded. Let the content be interesting on its own.
- **Never guess about Ukrainian.** If you are unsure about a word, grammatical form, or phonetic rule — flag it with `<!-- VERIFY: word/claim -->`. Never invent or describe vaguely to hide uncertainty.

### Forbidden Tropes

If you write any of these patterns, the module will be rejected in review:

- **The Cheerleader:** "Great job!", "Don't worry, it's easy!", "You're doing amazing!", "Good news!" — respect the learner's intelligence; stay professional.
- **The Announcer:** "In this section, we will explore...", "Now let's dive into...", "Let's take a look at...", "To summarize what we learned..." — never use formulaic transitions. Just teach the concept directly.
- **The Translator:** "The Ukrainian word for 'cat' is 'кіт'." — instead, present naturally: "A domestic cat is a **кіт**."
- **The Wall of Text:** 3+ paragraphs of English theory without a single Ukrainian example — every concept must be anchored in immediate Ukrainian examples.
- **The Filler:** "This is a very important concept that you will use frequently in your daily life." — empty sentences that add words but not meaning. Every sentence must teach something.

GRAMMAR CONSTRAINTS (A1.7 — People & Communication, M44-M50):
Vocative, imperative, dative, conjunctions, subordinate clauses.

ALLOWED:
- Vocative case (Олено! Тарасе!)
- Imperative mood (Читай! Скажіть! Дайте!)
- Dative case basics (мені, тобі, йому)
- Conjunctions (і, а, але, бо, тому що)
- Simple subordinate clauses (що, де, коли, якщо)
- All cases and tenses from previous phases

BANNED: Past/future tense, participles, passive voice

### Vocabulary

**Required:** друг (friend, m), подруга (friend, f), брат (brother, m), сестра (sister, f), пан (Mr., m), пані (Mrs./Ms., f)
**Recommended:** синку (son — vocative, from син), дочко (daughter — vocative, from дочка), козак (Cossack, m), вчитель (teacher, m), бабуся (grandmother, f), дідусь (grandfather, m)

### Pronunciation Videos



---

### Style Reference (match this tone and structure)

> **(У магазині / At the store)**
> — Добрий день! Скільки коштує хліб? (Good day! How much does the bread cost?)
> — Дванадцять гривень. (Twelve hryvnias.)
> — Дякую! Ось, будь ласка. (Thanks! Here you go.)

Notice that the shopkeeper uses **Добрий день** — the formal greeting for strangers. If this were a friend, they would say **Привіт** instead.

The word **скільки** (how much/how many) is one of the most useful question words. It always pairs with the genitive case: **скільки коштує** (how much does it cost), **скільки часу** (how much time).

*Note: Short dialogues in Ukrainian with per-line English glosses. Grammar explained in English. Ukrainian sentences in blockquotes and bulleted lists.*

## Output Format

Write in Markdown. Use:
- `## Section Title` for main sections
- `### Subsection` for subsections within a section
- `**bold**` for Ukrainian words being taught — EVERY bold Ukrainian word MUST have an English translation on first use, either in parentheses `**слово** (translation)` or inline `**слово** means "translation"`. No exceptions.
- Tables for paradigms (conjugation, declension)
- `:::tip` / `:::caution` / `:::note` for callout boxes
- `:::quiz` / `:::fill-in` / `:::match-up` / `:::group-sort` / `:::true-false` for exercises (using the DSL formats above)

Do NOT write MDX component syntax or JSON. Plain Markdown with the exercise DSL blocks described above.

Begin writing now. Start with the first section heading.
