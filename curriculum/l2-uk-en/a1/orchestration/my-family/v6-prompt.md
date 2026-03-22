<correction_directive>
CRITICAL: Your previous module was reviewed and scored below 8.0/10.
You must rewrite the module FROM SCRATCH, fixing ALL issues below.
All original constraints from the writing prompt still apply.

- FIX: [Pedagogical quality] [critical]
  Location: `:::match-up` exercise
  Issue: The exercise uses the Genitive case extensively ("мама мого тата", "брат мами", "дочка бабусі", "сестра тата", "батько батька"). This is A2 grammar. A1.1 learners have not learned the Genitive case and cannot logically deduce these forms.
  Fix: Rewrite the match-up items to avoid the genitive case. Use descriptive chains without case changes: "Це тато. Його мама — моя..." -> "бабуся". "Мама і тато" -> "батьки". "Її звати мама. Її брат — мій..." -> "дядько".
- FIX: [Pedagogical quality] [critical]
  Location: Діалоги (Dialogues): "А твого брата? — Денис." AND Підсумок (Summary): "Мою маму звати Олена."
  Issue: The plan explicitly restricts possessive pronouns: "Possessive pronouns мій/моя/моє/мої, твій/твоя/твоє (nominative only)". The text uses Accusative forms ("твого", "Мою"), which breaks the strict grammar progression.
  Fix: Change "А твого брата?" to "А брат?". Change "Мою маму звати Олена." to "Моя мама — Олена." or "Її звати Олена."
- FIX: [Plan adherence] [major]
  Location: "Діалоги (Dialogues)" section
  Issue: The section is approximately 165 words, which is significantly less than the 400-word target specified in the plan's `content_outline`.
  Fix: Expand the section. Break down the vocabulary and grammar used in the dialogues more thoroughly, and add more context to hit the word count target.
- FIX: [Exercise quality] [major]
  Location: `:::fill-in` "Complete the family introduction"
  Issue: The plan specifies the focus as "Complete family introduction dialogue". The generated exercise is a list of 6 disconnected sentences, not a cohesive dialogue.
  Fix: Rewrite the 6 fill-in items so they form a single, continuous conversational dialogue.
- NOTE: [Linguistic accuracy] [minor]
  Location: Діалоги (Dialogues): "Це моя сестра Катя..."
  Issue: "Катя" is a Russian-style diminutive. While very common in spoken Ukrainian, educational materials should prioritize Ukrainian forms to avoid Surzhyk.
  Fix: Change "Катя" to "Катруся" or "Катря".

- FIX (Linguistic): - "Катя" is a Russian-style diminutive. While "Коля" was explicitly required by the plan's dialogue outline, "Катя" was added by the writer. Ukrainian educational materials should prefer "Катруся" or "Катря".
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

- P1 (~40 words): Scene-setting intro — learner is scrolling through phone photos with a Ukrainian friend. Frame the situation: you want to show and talk about your family. Brief note that Ukrainians love sharing family photos and stories.

- Dialogue 1 (~100 words): Phone photo exchange — two friends asking about siblings.
  — Привіт! Що нового?
  — Дивись, це фото з вихідних!
  — О, класно! У тебе є брати чи сестри?
  — Так, у мене є два брати і одна сестра.
  — Ого! У мене тільки один брат. Як його звати?
  — Коля. А твого брата?
  — Денис.
  Post-dialogue gloss (~30 words): Key phrases pulled out — "У тебе є...?", "У мене є...", "Як його звати?" with brief English equivalents.

- Dialogue 2 (~110 words): Showing a family photo — naming everyone.
  — Це моя сім'я на фотографії.
  — Класно! Хто це?
  — Це моя мама Марина. А це мій тато Євген.
  — А хто тут?
  — Це моя сестра Катя і мої брати — Іван і Денис.
  — А це твоя бабуся?
  — Так, її звати Тетяна. А це мій дідусь Михайло.
  Post-dialogue gloss (~30 words): Pull out "Це моя/мій...", "Хто це?", "її звати..." — show how possessives change (моя мама vs мій тато).

- Dialogue 3 (~100 words): Connected self-introduction monologue combining all A1.1 skills from modules 1-6.
  Привіт! Мене звати Олена. Я з Києва. Я студентка. Моя мама — вчителька. Її звати Наталія. Мій тато — інженер. Його звати Андрій. У мене є один брат. Його звати Максим. Він студент. У мене є бабуся Галина і дідусь Петро. Моя сім'я дуже дружна!
  Post-dialogue note (~30 words): Highlight how this monologue chains greetings (M01-02), professions (M04-05), and family (M06). Encourage learner to write their own version.

## Сім'я (Family Vocabulary) (~220 words total)

- P1 (~60 words): Two Ukrainian words for family — сім'я and родина. Both are common and correct. Reference the textbook poem "Поділюся з вами я: В мене дружна є сім'я" (Марія Братко, Grade 1). Note the apostrophe in сім'я — recall apostrophe rule from M03.

- P2 (~80 words): Core family vocabulary in natural groupings. Pair formal/informal variants: мама/мати, тато/батько (мама and тато are what you actually say day-to-day; мати and батько are more formal or when talking about parents in general). батьки = parents. брат, сестра, син, дочка (also донька — equally common). Present each with a mini-sentence: Це мій тато. Моя мама — лікарка.

- P3 (~50 words): Extended family — бабуся/баба, дідусь/дід, тітка, дядько. Cultural note: Ukrainian has NO single word for "grandparents" — always say бабуся і дідусь. Reference textbook excerpt: "Я, ти, мама, тато, дідусь, бабуся і кішка Муся. Сім! Справжня СІМ-Я!"

- Exercise: **match-up** — Match family members with relationship descriptions (8 items). E.g., "мама мого тата" → бабуся; "брат мами" → дядько; "дочка бабусі" → мама/тітка.

- P4 (~30 words): Quick note on чоловік (husband/man — context decides) and дружина (wife). These are recommended vocabulary for learners who need them for their own family descriptions.

## У мене є (I have) (~280 words total)

- P1 (~70 words): Core concept — Ukrainian doesn't use a verb for "have." Instead: "At me there-is" → У мене є брат. Contrast with English structure (I have a brother) to show why direct translation fails. Stress that this is a memorized chunk at A1 — the grammar behind it (genitive pronouns) comes at A2. Three example sentences: У мене є сестра. У мене є тато і мама. У мене є два брати.

- P2 (~60 words): Three forms for A1 — у мене є (I have), у тебе є (you have, informal), у вас є (you have, formal/plural). Brief reminder of ти vs ви from M02 (formal address). Examples: У тебе є брат? У вас є діти? Mention that other forms (у нього є, у неї є, у нас є) appear in dialogues as memorized phrases — don't learn the pattern yet, just recognize them.

- P3 (~50 words): Questions with rising intonation — У тебе є сестра? ↗ No word-order change needed, just intonation (recall M05 question patterns). Answer patterns: Так, у мене є сестра. / Ні, у мене тільки один брат. Explicitly note: "У мене немає" requires genitive case → deferred to A2. For now, just say Ні and redirect.

- Exercise: **quiz** — Answer У тебе є...? questions with Так/Ні + appropriate response (6 items). E.g., "У тебе є сестра?" → "Так, у мене є одна сестра."

- P4 (~50 words): Numbers preview with family — один/одна changes by gender: один брат, одна сестра. два/дві: два брати, дві сестри. Note the noun form changes after два/дві (брати not брат) — just memorize these pairs for now. Three more examples: один дідусь, одна бабуся, два сини, дві дочки.

- Exercise: **fill-in** — Complete family introduction dialogue with missing words (6 items). E.g., "У мене ___ один брат" (є); "___ тебе є сестра?" (У); "У мене є ___ сестри" (дві).

- P5 (~50 words): Quick cultural note — Ukrainians often say "У нас велика сім'я" (we have a big family) or "У нас дружна родина" (we have a close family). Family is central to Ukrainian identity. Reference the textbook: "діти гралися в родину... Для всіх знайшлися обов'язки в родині" — even children's games revolve around family roles.

## Мій, моя, моє (Possessive Pronouns) (~220 words total)

- P1 (~70 words): Core rule — possessives match the gender of the thing you possess, NOT the gender of the possessor. мій брат (masculine noun → мій), моя сестра (feminine → моя), моє місто (neuter → моє), мої батьки (plural → мої). Contrast with English "my" which never changes. Use family examples exclusively: мій тато, моя мама, моє прізвище (my surname), мої брати.

- P2 (~50 words): твій/твоя/твоє/твої — same pattern for informal "your." Examples in question-answer pairs: Це твій брат? — Так, це мій брат. Це твоя бабуся? — Так, це моя бабуся. Reinforce the gender-matching pattern through repetition.

- P3 (~40 words): його (his) and її (her) — these DON'T change for gender. Його мама, його тато, його місто — always його. Її брат, її сестра, її прізвище — always її. This is simpler than мій/моя/моє. Learners only need to know whose, not the noun's gender.

- Exercise: **fill-in** — Choose correct possessive: мій/моя/моє/мої (8 items). E.g., "___ сестра" (моя), "___ дідусь" (мій), "___ батьки" (мої), "___ ім'я" (моє), "___ тато" (мій), "___ бабуся" (моя), "___ брати" (мої), "___ місто" (моє).

- P4 (~60 words): Scope boundary — full possessive paradigm (наш, ваш, їхній + all cases) is A2. At A1, learners use only мій/твій/його/її in nominative case. Preview: in A2, learners will say "нашу маму" (our mom, accusative) and "вашого батька" (your father, genitive). For now, stick to "Це мій/моя/моє..." sentences. Table summary: мій→моя→моє→мої, твій→твоя→твоє→твої, його (fixed), її (fixed).

## Підсумок — Summary (~160 words total)

- P1 (~60 words): Self-check questions — Can you name 5 family members in Ukrainian? Can you say "I have a sister" (У мене є сестра)? What's the difference between мій and моя? (Gender of the noun!) Can you introduce your family in 4-5 sentences using Це мій/моя... and У мене є...?

- P2 (~60 words): Model self-introduction bringing together all M06 skills — a short paragraph the learner can adapt: "Моя сім'я невелика. У мене є мама, тато і один брат. Мою маму звати Олена. Мій тато — Сергій. У мене є бабуся Ганна і дідусь Василь. Моя родина дуже дружна." Encourage learner to write their own version.

- P3 (~40 words): Look ahead — M07 is a checkpoint reviewing all of A1.1 (sounds, letters, first contact). Learner should practice introducing themselves AND their family fluently before the checkpoint. Quick reminder: apostrophe in сім'я, gender agreement in мій/моя/моє.

Grand total: ~1320 words (440 + 220 + 280 + 220 + 160)
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
