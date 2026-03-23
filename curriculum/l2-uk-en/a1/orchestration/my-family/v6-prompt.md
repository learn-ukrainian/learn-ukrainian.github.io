<correction_directive>
CRITICAL: Your previous module was reviewed and scored below 8.0/10.
You must rewrite the module FROM SCRATCH, fixing ALL issues below.
All original constraints from the writing prompt still apply.

- NOTE: [Vocabulary] [minor]
  Location: `Сім'я (Family Vocabulary)` section
  Issue: The recommended words "дружина" (wife) and "чоловік" (husband) from the plan are entirely missing from the prose and dialogues.
  Fix: Add a brief mention of husband/wife in the core family vocabulary section or include them in one of the photo dialogues.
- FIX: [Structural integrity] [major]
  Location: `<!-- TAB:Словник -->` > `Додаткові слова з уроку` table
  Issue: Malformed Markdown table. Several rows have 5 columns instead of the required 4 defined by the header (e.g., `| **дід** | informal | | ім. | ч. |` and `| **мати** | formal | | ім. | ж. |`). This will break the Markdown parser during site generation.
  Fix: Remove the extra pipe symbols to ensure exactly 4 columns align with the header.
- FIX: [Pedagogical quality] [major]
  Location: `<!-- TAB:Словник -->` > `Додаткові слова з уроку` table
  Issue: The English translations for several pronouns and nouns are replaced with grammar notes scraped from the prose, directly misinforming the learner. For example, "мій" is translated as "masculine", "моя" as "feminine", and "місто" is translated as "neuter, so моє".
  Fix: Provide the actual English translations in the "Переклад" column (мій -> my, місто -> city) and remove the conversational grammar notes from the translation column.
</correction_directive>

# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **6: My Family** (A1, A1.1 [Sounds, Letters, and First Contact]).

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

## 7 Hard Rules

1. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
2. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
3. **NO "In this lesson we will..."** — never use formulaic openers. Start with a dialogue, a question, or a situation.
4. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
5. **Write exercises directly** — write complete exercises in the DSL format below. Include real questions, real answers, and real distractors. A downstream tool converts them to interactive React components.
6. **NO meta-commentary** — do NOT add "Content notes:", word count summaries, or self-audit sections at the end. Just write the module content and stop.
7. **Hit the word target** — you MUST write 1200–1800 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.

**Note:** Do NOT add stress marks (´) to any Ukrainian word — a deterministic tool handles this after you write.

## Exercises — Write Them Directly

After each key teaching point, write an exercise directly in DSL format. Base your exercises on the `activity_hints` in the Plan — each hint should become one exercise.

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
module: a1-006
level: A1
sequence: 6
slug: my-family
version: '1.0'
title: My Family
subtitle: "У мене є брат — Showing photos"
focus: vocabulary
pedagogy: PPP
phase: A1.1 [Sounds, Letters, and First Contact]
word_target: 1200
objectives:
- Name close family members in Ukrainian
- Use "У мене є" to say what you have (memorized chunk)
- Use possessive pronouns мій/моя/моє in nominative only
- Introduce family members using Це + possessives
content_outline:
- section: "Діалоги (Dialogues)"
  words: 400
  points:
  - "Dialogue 1 — Showing phone photos (Anna Ep6-7):
    — У тебе є брати чи сестри?
    — Так, у мене є два брати і одна сестра.
    — Ого! У мене тільки один брат. Як його звати?
    — Коля."
  - "Dialogue 2 — Family in a photo (Anna Ep7):
    — Це моя сім'я на фотографії. Класно! Хто це?
    — Це моя мама Марина. Це мій тато Євген.
    Це моя сестра Катя і мої брати — Іван і Денис.
    — А це твоя бабуся? — Так, її звати Тетяна."
  - "Dialogue 3 — Connected speech (Anna Ep10 review pattern):
    Привіт! Мене звати... Моя мама — вчителька.
    Мій тато — інженер. У мене є один брат.
    Combining all A1.1 skills."
- section: "Сім'я (Family Vocabulary)"
  words: 200
  points:
  - "Anna Ep6: Two words for family: сім'я and родина (both used).
    Core: мама/мати, тато/батько, брат, сестра, син, дочка/донька.
    Extended: бабуся/баба, дідусь/дід, тітка, дядько.
    Note: Ukrainian has NO single word for 'grandparents' —
    always say бабуся і дідусь."
- section: "У мене є (I have)"
  words: 250
  points:
  - "Anna Ep6 pattern: Ukrainian doesn't say 'I have' with a verb.
    Instead: 'At me there-is' — У мене є брат.
    For A1, teach only: у мене є, у тебе є (informal), у вас є (formal).
    Other forms (у нього, у неї, у нас, у них) use genitive pronouns
    which are A2 grammar — introduce them gradually through dialogues
    as memorized phrases, not as a paradigm table."
  - "Questions with rising intonation: У тебе є сестра? ↗
    Negative: Defer 'У мене немає' to A2 where genitive is taught.
    For A1, learners answer: Ні. / Ні, у мене тільки один брат.
    This avoids the pedagogical trap of немає + nominative (*немає брат)."
  - "Numbers preview (Anna Ep6): один/одна changes by gender:
    один брат, одна сестра. два/дві: два брати, дві сестри."
- section: "Мій, моя, моє (Possessive Pronouns)"
  words: 200
  points:
  - "Anna Ep7: Possessives match the gender of the thing possessed.
    мій брат (m), моя сестра (f), моє місто (n), мої батьки (pl).
    твій/твоя/твоє/твої (your, informal).
    його (his — doesn't change), її (her — doesn't change).
    State Standard note: full paradigm (наш, ваш, їхній) is A2.
    At A1: мій/твій/його/її in nominative only."
- section: "Підсумок — Summary"
  words: 150
  points:
  - "Self-check: Name 5 family members. Say 'I have a sister.'
    What's the difference between мій and моя?
    Introduce your family in 4-5 sentences."
vocabulary_hints:
  required:
  - сім'я (family) — apostrophe word
  - мама (mother)
  - тато (father)
  - брат (brother)
  - сестра (sister)
  - бабуся (grandmother)
  - дідусь (grandfather)
  - мій, моя, моє, мої (my — m/f/n/pl)
  - твій, твоя, твоє (your — m/f/n, informal)
  - у мене є (I have)
  - у тебе є (you have, informal)
  recommended:
  - батьки (parents)
  - дядько (uncle)
  - тітка (aunt)
  - дочка (daughter)
  - син (son)
  - дружина (wife)
  - чоловік (man / husband)
  - його (his — doesn't change)
  - її (her — doesn't change)
  - один, одна (one — m/f)
  - два, дві (two — m/f)
  - чи (or — in questions)
  - тільки (only)
activity_hints:
- type: quiz
  focus: "Answer: У тебе є...? Так / Ні"
  items: 6
- type: fill-in
  focus: "Choose correct possessive: (мій/моя/моє) ___ сестра"
  items: 8
- type: match-up
  focus: "Match family members with relationships"
  items: 8
- type: fill-in
  focus: "Complete family introduction dialogue"
  items: 6
connects_to:
- a1-007 (Checkpoint — First Contact)
prerequisites:
- a1-005 (Who Am I?)
grammar:
- "У мене є / у тебе є (memorized chunks, NOT genitive paradigm)"
- "Possessive pronouns мій/моя/моє/мої, твій/твоя/твоє (nominative only)"
- "Gender agreement preview (possessive + noun)"
- "Numbers один/одна, два/дві with family members"
- "Negation: Ні + simple response (NOT У мене немає — deferred to A2)"
register: розмовний
references:
- title: "ULP Season 1, Episode 6 — Family + I Have"
  url: https://www.ukrainianlessons.com/episode6/
  notes: "У мене є with family. Один/одна gender."
- title: "ULP Season 1, Episode 7 — Possessive Pronouns"
  url: https://www.ukrainianlessons.com/episode7/
  notes: "мій/моя/моє paradigm. Це моя мама."
- title: "ULP Season 1, Episode 10 — Review"
  url: https://www.ukrainianlessons.com/episode10/
  notes: "Connected self-introduction: Я і моя сім'я."
pronunciation_videos:
  playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: My Family
**Module:** my-family | **Phase:** A1.1 [Sounds, Letters, and First Contact]
**Textbook grades searched:** 1, 2

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 6
> Я  і  моя  родина
> Поділюся з вами я:
> В мене дружна є сім’я.
> Люба мама і татусь,
> Бабця Віра і дідусь, 
> Мурка, Барсик, Оля, я  —
> От і вся моя сім’я.
>                     Марія Братко
> 	 Намалюй свою родину на аркуші з альбому.
> 	 Повтори вірш за вчителем / учителькою.

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> 17| Розгляньте малюнок і прочитайте.
> Одна бабуся, 
> дві матері,
> дві дочки та внучка.
> • Полічіть і скажіть, скільки було людей. Назвіть числівники, 
> використані в задачі. На яке питання вони відповідають?
> • Складіть подібну задачу. Запропонуйте розв'язати її 
> у класі.
> 18| Відгадай загадки.
> 1. Два брати через дорогу живуть і ніколи в гості 
> один до одного не ходять. 2. Два скельця, три дужки — 
> на ніс і за вушка. 3. Два кінці, два кільця, а посередині
> цвях.
> Що спільного у словах 
> окуляри і ножиці?

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 16
> Моя школа
> Вранці я прибіг до школи,
> В ній я ще не був ніколи.
> А зі мною мама й тато,
> Бо і в них велике свято (М. Братко).
> 	 Розкажи про свою школу.
> 	 Хто розповідає про подію? Хто з хлопчиком іде 
> до школи? Який у них настрій?
> 	 Розглянь малюнки.

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> 42
> оДнина І мноЖина 
> Слова — назви ознак уживаються в однині й у множині.
> Добери до слів — назв предметів слова-ознаки.
> діти
> веселий
> здоровий
> розумний
> добрий
> який? яка? яке?
> які?
> Ігор
> Яна
> щеня
> і
>  
>  
> Доповни таблицю. Придумай слово — назву предмета до 
> кожного слова — назви ознаки. 
> однина
> множина
> Який?
> Яка?
> Яке?
> Які?
> веселий
> весела
> веселе
> веселі
> сумний
> добрі
>  
> Правда чи неправда? Запиши одне правдиве висловлювання.
> Я намалював 
> квадратний будинок 
> з трикутним дахом 
> і прямокутними 
> дверима.
> Я на

> **Source:** unknown, Grade 1
> **Score:** 0.25
>
> 36
> 36
> 	 Розглянь фото дітей. Здогадайся, як звати 
> хлопчика.  Хто з дівчаток — Оксана, а хто — 
> Аліна? 
> 	
> У яких предметах «заховалася» буква о?
> 	 Розглянь малюнки й дай відповідь на запи-
> тання.
> 	
> Що було в клоуна?
> 	
> Хто забрав кульки?
> 	
> Що сорока зробила з кульок?

> **Source:** unknown, Grade 2
> **Score:** 0.25
>
> 4. Коли дружба прийшла — буде більше у світі тепла.
> 5. Скажи мені, хто твій друг, і я скажу тобі, хто ти.
> 6. Дружба та братство — найбільше багатство.
> ✓ 
> \
> Друга шукай, а знайдеш — тримай.
> 0| Запиши назву професії, пов'язаної з цими словами.
> • На яке питання відповідають слова — назви професій?
> 1і| Добери і запиши за зразком слова.
> Усно склади речення з однією парою слів.
> хто?
> _____ /
> що?
> кобзар 
> скрипаль 
> гітаристка 
> бандуристка 
> барабанщик
> кобза
> 51

## Сім'я (Family Vocabulary)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 6
> Я  і  моя  родина
> Поділюся з вами я:
> В мене дружна є сім’я.
> Люба мама і татусь,
> Бабця Віра і дідусь, 
> Мурка, Барсик, Оля, я  —
> От і вся моя сім’я.
>                     Марія Братко
> 	 Намалюй свою родину на аркуші з альбому.
> 	 Повтори вірш за вчителем / учителькою.

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> Скоро всі діти у групі були вже не хлопчиками й дівчат­
> ками, а родичами — різними-різними. Для всіх знайшлися 
> обов’язки в родині. І для бабусі й дідуся, і для тітоньки й 
> дядечка, і для братиків і сестричок... Цілісіньку годину 
> гралися діти. Ходили один до одного в гості, їздили на роботу, 
> готували обід. Тільки маленька Ліля чомусь сумно сиділа на 
> стільчику. Вона щось тихенько шепотіла й загинала пальчики. 
> І раптом як заплаче!
> — Лілечко, що сталося? — підбігла до дівчинки Оленка. 
> Підійшла

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 23
> ’
> Апостроф
> і |м’я
> Прочитай. Назви імена. Склади речення з одним іменем.
> 	
> ім’я	
> Дар’я	
> Дем’ян	
> В’ячеслав
> 	
> сім’я	
> Мар’яна	
> Лук’ян	
> Валер’ян
> 
> Відшукай слово до схеми.
> 	
> п’є	
> в’є	
> б’є	
> з’єднати	
> під’їхати
> 	 п’ють	 в’ють	 б’ють	
> роз’єднати	
> від’їхати
> 
> Текст. Театралізуємо
> Моє ім’я
> Я — Мар’яна. 
> Сьогодні на подвір’ї я грала в м’яч. 
> —  Мар’яше! — кличуть подруги. —  
> Кидай м’яч. 
> Потім мене гукнула бабуся:
> —  Мар’яночко! Іди обідати.
> Я пішла додому і зустріла сусідку. 
> —  Як справи, Мар’янко?

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> Утвори і прочитай слова. Назви одним словом.
> маам
> отат
> дусьід
> басябу
> барт
> састер
> • Поміркуй, якими іншими словами ми називаємо сім’ю. 
> Склади тематичну павутинку (на аркуші паперу).
> Послухай пісню Наталії Май «Родина».
> *—• • Що ти відчував (відчувала), коли звучала пісня?
> • За що дитина дякує батькам?
> ~ Прочитай вірш.
> ДИВО-ТАТУСЬ
> Леся Вознюк
> Як весняне сонечко, 
> усміхалась донечка. 
> В оченятах сяяли 
> щастя промінці. 
> Тішилася донечка, 
> що її долонечка, 
> крихітна долонечка 
> в татовій руці. 
> Щебет

> **Source:** unknown, Grade 1
> **Score:** 0.25
>
> 7
> Галина та Марко знали, що сьогодні особ­
> ливий день — Різдво. Мама і тато тихень-
> ко перемовляються та ховають коробки за 
> спинами. Приїхали бабусі й варять на кухні кутю. 
> Там уже є все: і мед, і родзинки, і мак, і горішки. 
> У хаті пахне пирогами так, що їсти хочеться цілий 
> день. На великій гілці ялини висить безліч цукерок 
> у яскравих обгортках, гірлянди, ліхтарі, сніжинки, 
> золоті горішки, гриби.
> Увесь світ сьогодні співає колядки, діти отриму-
> ють подарунки.
> Галина та Марко теж заколядува

> **Source:** unknown, Grade 2
> **Score:** 0.25
>
> — I Мусю любимо й поважаємо. І вона нас теж. Зустрічає 
> всіх біля порога, грається з нами, колискову ввечері 
> муркоче...
> —Ура!—зраділа Ліля. — Виходить, що нас... Я, ти, мама, 
> тато, дідусь, бабуся і кішка Муся. Сім! Справжня СІМ-Я!
> -., • Де відбувалися описані події? Якого віку були діти?
> • У яку гру грали діти? Як вони розподілили між собою ролі?
> • Чому Ліля сумувала? Заповни таблицю (на аркуші паперу). 
> Познач смайликами емоції Лілі в різних частинах тексту.
> Частина тексту
> Емоції Лілі
> Зачин
> О

## У мене є (I have)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 6
> Я  і  моя  родина
> Поділюся з вами я:
> В мене дружна є сім’я.
> Люба мама і татусь,
> Бабця Віра і дідусь, 
> Мурка, Барсик, Оля, я  —
> От і вся моя сім’я.
>                     Марія Братко
> 	 Намалюй свою родину на аркуші з альбому.
> 	 Повтори вірш за вчителем / учителькою.

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> 3| Додайте пропущені слова, щоб прочитати початок
> казки Алли Свашенко.
> Два брати жили у світі.
> Був один з них працьовитий, 
> другий був ? дуже.
> Той хоробрий і правдивий, 
> той ? , полохливий, 
> той розумний, той ? , 
> той великий, той ? .
> • Складіть і запишіть два речення із 
> протилежними за значенням словами.
> Запишіть і підкресліть слова, проти­
> лежні за значенням.
> Узимку надворі ? , а влітку — ? . 
> Ночі довгі, а дні ? — узимку. 
> Дні довгі, а ? короткі — ? .
> Що ти знаєш про пори року?
> 5| Відгадай.

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 20
> Мої друзі
> Якщо друг у тебе є,
> Життя радісним стає.
> Разом можна все зробити,
> Тож без друга не прожити.
> 	
>          Анатолій Костецький
> 	 Розкажи про свого друга / свою подругу.
> 	 Повтори вірш за вчителем / учителькою.
> 	 Хто з ким дружить? Розкажи.

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> 7| Випиши парами слова, протилежні за значенням.
> 1. Дорогою лиха підеш — щастя не знайдеш.
> 2. Справжні друзі ворогами не бувають. 3. Любов 
> і ненависть поряд ходять. 4. Тривога і спокій ніколи 
> рідними не бувають. 5. Світло будь-яку темряву розсіває. 
> 6. Зло посієш — добро не вродить.
> • Запиши два речення (на вибір). Підкресли слова із 
> протилежним значенням.
> к
> Пограйтесь у

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~400 words)
- `## Сім'я (Family Vocabulary)` (~200 words)
- `## У мене є (I have)` (~250 words)
- `## Мій, моя, моє (Possessive Pronouns)` (~200 words)
- `## Підсумок — Summary` (~150 words)
- `## Підсумок — Summary` (~150 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 5-15% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: Mostly English with Ukrainian words bolded inline.
- UKRAINIAN CONTENT: Words and short phrases inline: "The letter **Н** looks like H but sounds like N."
- DIALOGUES & READING PRACTICE: Short Ukrainian sentences in blockquotes are encouraged.
- TABLES: Simple letter-sound or word-meaning tables.
Ukrainian sentences max 10 words.

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
- Dialogues: natural, not stilted. Real situations, real responses.
- **Tone:** Authoritative but warm. Like a skilled Ukrainian teacher — confident, clear, culturally grounded. Let the content be interesting on its own.
- **Never guess about Ukrainian.** If you are unsure about a word, grammatical form, or phonetic rule — flag it with `<!-- VERIFY: word/claim -->`. Never invent or describe vaguely to hide uncertainty.

### Forbidden Tropes

If you write any of these patterns, the module will be rejected in review:

- **The Cheerleader:** "Great job!", "Don't worry, it's easy!", "You're doing amazing!", "Good news!" — respect the learner's intelligence; stay professional.
- **The Announcer:** "In this section, we will explore...", "Now let's dive into...", "Let's take a look at...", "To summarize what we learned..." — never use formulaic transitions. Just teach the concept directly.
- **The Translator:** "The Ukrainian word for 'cat' is 'кіт'." — instead, present naturally: "A domestic cat is a **кіт**."
- **The Wall of Text:** 3+ paragraphs of English theory without a single Ukrainian example — every concept must be anchored in immediate Ukrainian examples.
- **The Filler:** "This is a very important concept that you will use frequently in your daily life." — empty sentences that add words but not meaning. Every sentence must teach something.

GRAMMAR CONSTRAINTS (A1.1 — Communication, M04-M14):
Keep grammar simple — first exposure to Ukrainian sentences.

ALLOWED:
- Це + noun: «Це кіт», «Це мама»
- Fixed verbal phrases: «Мене звати», «У мене є», «Як справи?»
- Simple present tense (я читаю, я бачу) — from M08+
- Question words: «Хто це?», «Що це?», «Де?», «Як?»
- Так/Ні answers
- Adj + noun: «великий дім», «нова книга» — from M09+
- Possessive pronouns: мій/моя/моє — from M06+

BANNED: Past/future tense, conditionals, participles, passive, gerunds,
compound sentences (no і/а/але joining clauses)

METALANGUAGE: English first, Ukrainian in parentheses. Bilingual headings.

### Vocabulary

**Required:** сім'я (family) — apostrophe word, мама (mother), тато (father), брат (brother), сестра (sister), бабуся (grandmother), дідусь (grandfather), мій, моя, моє, мої (my — m/f/n/pl), твій, твоя, твоє (your — m/f/n, informal), у мене є (I have), у тебе є (you have, informal)
**Recommended:** батьки (parents), дядько (uncle), тітка (aunt), дочка (daughter), син (son), дружина (wife), чоловік (man / husband), його (his — doesn't change), її (her — doesn't change), один, одна (one — m/f), два, дві (two — m/f), чи (or — in questions), тільки (only)

### Pronunciation Videos

Playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV

---

### Style Reference (match this tone and structure)

Look at the text on this page. What you are seeing are letters. Now, say a word out loud. What you just produced is a sound. This distinction is the absolute foundation of the Ukrainian language. There is a golden rule taught to every Ukrainian student in the first grade: **Ми чуємо і вимовляємо звуки, а бачимо і пишемо літери**. We hear and pronounce sounds, but we see and write letters.

These friendly letters are **А**, **О**, **К**, **М**, and **Т**. Because they are so familiar, you can start reading real Ukrainian words immediately. Look at the word **мама**. It means mother, and you already know how to read it. Now look at **тато**. It means father.

*Note: English prose dominates. Ukrainian words appear bolded inline. Short Ukrainian sentences illustrate one concept at a time. No conjugated verbs. Tables and bulleted lists for vocabulary.*



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
## Діалоги (Dialogues) (~440 words total)

- P1 (~40 words): Scene-setting intro — learner is at a café with a Ukrainian friend, showing phone photos. Brief note that Ukrainians love sharing family photos and asking about siblings. Transition into Dialogue 1.
- Dialogue 1 (~100 words): Showing phone photos — two friends asking about siblings. Key lines: "У тебе є брати чи сестри?" / "Так, у мене є два брати і одна сестра." / "Ого! У мене тільки один брат. Як його звати?" / "Коля." Followed by 3-4 comprehension glosses in English explaining у мене є as a chunk and чи as "or" in questions.
- P2 (~30 words): Transition noting that the conversation continues — now the friend shares a family photo with more people. Sets up extended family vocabulary.
- Dialogue 2 (~110 words): Family photo identification — "Це моя сім'я на фотографії." / "Класно! Хто це?" / "Це моя мама Марина. Це мій тато Євген. Це моя сестра Катя і мої брати — Іван і Денис." / "А це твоя бабуся?" / "Так, її звати Тетяна." Glosses explain Це моя/мій pattern, possessive agreement with each noun, його/її as invariable.
- P3 (~40 words): Transition to Dialogue 3 — now the learner tries a connected self-introduction combining skills from modules 1-5 (greetings, name, nationality, profession) with new family vocabulary.
- Dialogue 3 (~120 words): Connected monologue with a partner responding — "Привіт! Мене звати Олена. Я з Києва. Моя мама — вчителька. Мій тато — інженер. У мене є один брат. Його звати Артем." Partner asks follow-up questions: "А у тебе є сестра?" / "Ні, у мене тільки один брат." Glosses highlight how all A1.1 skills chain together: greeting → name → origin → family → possessives.

- Exercise: **Quiz** — "Answer: У тебе є...? Так / Ні" — 6 items. Learner reads questions like "У тебе є брат?" and selects Так/Ні based on dialogue comprehension.

## Сім'я (Family Vocabulary) (~220 words total)

- P1 (~70 words): Two Ukrainian words for family — сім'я and родина (both common, both correct). Reference the textbook poem "В мене дружна є сім'я" (Марія Братко, Grade 1). Note the apostrophe in сім'я — recall apostrophe rule from Module 4 (letter sounds). Core members: мама, тато, брат, сестра.
- P2 (~80 words): Full family vocabulary table with two tiers. Tier 1 (immediate): мама/мати, тато/батько, брат, сестра, син, дочка (also донька — both correct). Tier 2 (extended): бабуся/баба, дідусь/дід, тітка, дядько, батьки (parents). Cultural note: Ukrainian has NO single word for "grandparents" — always бабуся і дідусь. Informal/affectionate forms: татусь, матуся, бабця (from textbook poem).
- P3 (~70 words): Pronunciation spotlight — stress patterns for family words: мáма, тáто, сестрá (stress on last syllable!), брат, бабýся, дідýсь. Note сестрá vs English "SISter" — Ukrainian stress falls differently. Soft sign in дідусь — recall soft sign from Module 4. Apostrophe in сім'я — practice saying it: [s'imja].

- Exercise: **Match-up** — "Match family members with relationships" — 8 items. E.g., match мама↔mother, дідусь↔grandfather, батьки↔parents, тітка↔aunt.

## У мене є (I have) (~280 words total)

- P1 (~90 words): Ukrainian doesn't use a verb "to have." Instead: "At me there-is" — У мене є брат (literally: "At me is brother"). This is completely different from English "I have a brother." For A1, treat this as a memorized chunk — don't analyze the grammar (genitive pronoun мене is A2). Three forms to memorize: у мене є (I have), у тебе є (you have, informal), у вас є (you have, formal). Examples: У мене є сестра. У тебе є брат? У вас є діти?
- P2 (~80 words): Questions with rising intonation — У тебе є сестра? ↗ No word-order change needed (unlike English). Compare: У тебе є брат. (statement, falling) vs. У тебе є брат? (question, rising). The word чи adds "or": У тебе є брати чи сестри? For now, answer negatively with just Ні or Ні, у мене тільки один брат. The full negative form (У мене немає + genitive) comes in A2 — avoid the trap of *немає брат.
- P3 (~70 words): Numbers preview with family — один/одна changes by gender: один брат (masculine), одна сестра (feminine). Similarly два/дві: два брати, дві сестри. Examples from Dialogue 1: "у мене є два брати і одна сестра." Note: after два/дві, the noun changes form (два брати, not *два брат) — just memorize these phrases for now, the grammar rule comes later.
- P4 (~40 words): Other people's families as memorized phrases — у нього є (he has), у неї є (she has). Not a paradigm — just two useful phrases for talking about Dialogue 2: "У неї є сестра Катя." Present as vocabulary, not grammar.

- Exercise: **Fill-in** — "Complete family introduction dialogue" — 6 items. Gapped dialogue where learner fills in: "У мене ___ два брати" (є), "У тебе є ___?" (сестра), "___ мене тільки один брат" (У).

## Мій, моя, моє (Possessive Pronouns) (~220 words total)

- P1 (~80 words): Possessives match the THING you possess, not the owner. мій брат (brother = masculine → мій), моя сестра (sister = feminine → моя), моє місто (city = neuter → моє), мої батьки (parents = plural → мої). Compare English "my" — one form for everything. Ukrainian needs you to know the noun's gender. Quick gender recall from Module 5: consonant ending → masculine, -а/-я → feminine, -о/-е → neuter.
- P2 (~70 words): твій/твоя/твоє/твої — same pattern for "your" (informal). Examples from Dialogue 2: "А це твоя бабуся?" — бабуся ends in -я → feminine → твоя. його (his) and її (her) — these NEVER change: його брат, його сестра, його місто. її мама, її тато, її місто. Much easier than мій/твій!
- P3 (~70 words): Pattern practice with Це + possessive — the main sentence frame for this module. Це мій тато. Це моя мама. Це моє фото. Це мої брати. Have learner mentally practice pointing at a photo and introducing each person. State Standard note: full paradigm (наш, ваш, їхній) is A2. At A1, only мій/твій/його/її in nominative case. No case changes yet.

- Exercise: **Fill-in** — "Choose correct possessive: (мій/моя/моє) ___ сестра" — 8 items. Learner selects from мій/моя/моє/мої for nouns: ___ брат, ___ бабуся, ___ місто, ___ батьки, ___ дідусь, ___ сім'я, ___ тато, ___ дочка.

## Підсумок — Summary (~160 words total)

- P1 (~90 words): Recap of the four skills learned — naming family members (сім'я, родина, мама, тато, брат, сестра, бабуся, дідусь), saying what you have (У мене є...), using possessive pronouns (мій/моя/моє matching noun gender), and introducing family with Це + possessive (Це моя мама Марина). Remind that немає is A2 — for now, Ні + simple response.
- P2 (~70 words): Self-check prompts — Can you name 8 family members? Say "I have a sister" in Ukrainian. What's the difference between мій and моя? Why do we say одна сестра but один брат? Challenge: introduce your family in 5-6 sentences using all skills from Modules 1-6. Preview of Module 7 (Checkpoint): putting everything together in a longer conversation.

Grand total: ~1320 words
</skeleton>

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
