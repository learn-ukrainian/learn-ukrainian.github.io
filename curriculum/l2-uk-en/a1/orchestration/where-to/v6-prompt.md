<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Missing 3/6 required vocab: школа → у школу (to school), робота → на роботу (to work), банк → у банк (to the bank)
</correction_directive>

LEARNINGS FROM PAST BUILDS (same error patterns seen before):
- [GLOBAL] сес-тра is a VALID word division per Правопис 2019 §49. Do NOT mark it as an error. Phonetic syllabification (се-стра) and typographic word division (сес-тра) follow different rules — both are correct in their respective contexts.
- [GLOBAL] Ukrainian textbooks teach a hands-on-EARS test for voicing (закрий долонями вуха), NOT a hand-on-throat test. The hand-on-throat test is a valid phonetics technique but must NOT be attributed to Ukrainian textbooks. Source: Кравцова 2019, Grade 2, p.39.
- [GLOBAL] Do NOT invent Ukrainian words for minimal pairs. "Сір" is NOT a word meaning "grey" — the correct form is "сірий". Use verified minimal pairs only: кит/кіт, бити/біти, лис/ліс.
- [GLOBAL] NEVER frame Ukrainian as "lacking" or "missing" letters that Russian has. Ukrainian has its own 33-letter alphabet — it is complete. Do NOT write "Ukrainian lacks Ъ, Ы, Э" or "Ukrainian doesn't have these Russian letters." Instead, highlight what Ukrainian HAS: Ґ, Є, Ї, І are unique to Ukrainian. Present Ukrainian on its own terms.
- [where-is-it] Same errors (VOCABULARY): V6 build failed after 3 attempts
- [checkpoint-first-contact] Same errors (VOCABULARY): V6 build failed after 3 attempts
- [checkpoint-first-contact] Same errors (VOCABULARY): V6 build failed after 3 attempts
- [checkpoint-first-contact] Same errors (VOCABULARY): V6 build failed after 3 attempts
- [checkpoint-first-contact] Same errors (VOCABULARY): V6 build failed after 3 attempts

# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **31: Where To?** (A1, A1.5 [Places]).

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
module: a1-031
level: A1
sequence: 31
slug: where-to
version: '1.1'
title: Where To?
subtitle: Іду в банк, на роботу — the accusative for direction
focus: grammar
pedagogy: PPP
phase: A1.5 [Places]
word_target: 1200
objectives:
- Use в/у and на + accusative to answer Куди? (Where to?)
- Distinguish Де? (locative = static) from Куди? (accusative = direction)
- Form basic accusative endings for place nouns
- Navigate between locations using йти/їхати + direction
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Where are you going? (ULP Ep18): — Куди ти йдеш? — Я йду в банк.
    А ти? — Я йду на роботу. — А потім? — Потім іду в магазин. — Зустрінемося в кафе?
    Direction vs location: іду В банк (direction) vs я В банку (location).'
  - 'Dialogue 2 — Planning a trip: — Куди ти їдеш у суботу? — Я їду у Львів. — А Олена?
    — Вона їде в Одесу. Cities as destinations: їхати в/у + city.'
- section: Куди? Знахідний відмінок (Where To? Accusative)
  words: 300
  points:
  - 'Grade 4 case helper: Зн. (бачу) — кого? що? For direction: в/у + accusative =
    WHERE TO (motion toward). Compare with locative: в/у + locative = WHERE (static
    position). Де ти? — Я в банку. (locative — you ARE there) Куди ти йдеш? — Я йду
    в банк. (accusative — you''re GOING there)'
  - 'Accusative endings for places: Masculine inanimate: = nominative (no change!):
    банк → в банк, магазин → у магазин, парк → у парк. Feminine -а/-я → -у/-ю: школа
    → у школу, робота → на роботу, бібліотека → у бібліотеку. Neuter: = nominative
    (no change): кафе → у кафе, місто → у місто. Good news: masculine and neuter don''t
    change! Only feminine shifts.'
- section: Де чи куди? (Where or Where To?)
  words: 300
  points:
  - 'The key question pair: Де ти? (Where are you?) → в/у/на + LOCATIVE Куди ти йдеш?
    (Where are you going?) → в/у/на + ACCUSATIVE | Place | Де? (М.в.) | Куди? (Зн.в.)
    | | школа | в школі | у школу | | робота | на роботі | на роботу | | банк | у
    банку | у банк | | парк | у парку | у парк |'
  - 'Motion verbs: йти (to go on foot): Я йду в магазин. їхати (to go by transport):
    Я їду на вокзал. Note: йти = on foot, їхати = by vehicle. Both + в/на + accusative.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Two questions, two cases: Де? → locative (в школі, на роботі) = STATIC Куди?
    → accusative (у школу, на роботу) = DIRECTION Masculine/neuter accusative = nominative
    (no change). Feminine: -а→-у, -я→-ю (школа→школу, бібліотека→бібліотеку). Self-check:
    Where are you? (Де?) Where are you going? (Куди?)'
vocabulary_hints:
  required:
  - куди (where to)
  - йти (to go on foot)
  - їхати (to go by transport)
  - школа → у школу (to school)
  - робота → на роботу (to work)
  - банк → у банк (to the bank)
  recommended:
  - магазин → у/в магазин (to the shop)
  - бібліотека → у бібліотеку (to the library)
  - ресторан → у ресторан (to the restaurant)
  - Одеса → в Одесу (to Odesa)
  - повертатися → додому (to return home)
activity_hints:
- type: quiz
  focus: Де or Куди? Choose the right question for each sentence.
  items: 8
- type: fill-in
  focus: 'Complete: Я йду ___ (школа). Він у ___ (банк).'
  items: 10
- type: group-sort
  focus: 'Sort phrases: Де? (locative) vs Куди? (accusative)'
  items: 10
- type: quiz
  focus: Йти or їхати? Choose based on distance/transport.
  items: 6
connects_to:
- a1-032 (Transport)
prerequisites:
- a1-029 (Where Is It?)
grammar:
- 'Accusative for direction: в/у/на + Зн.в.'
- Де? (М.в.) vs Куди? (Зн.в.) distinction
- 'Accusative endings: m/n = nominative, f: -а→-у, -я→-ю'
- 'Motion verbs: йти (foot) vs їхати (transport)'
register: розмовний
references:
- title: Grade 4 case table
  notes: Зн. (бачу) — кого? що? Helper word method.
- title: ULP Season 1, Episode 18
  url: https://www.ukrainianlessons.com/episode18/
  notes: Accusative case for directions.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Where To?
**Module:** where-to | **Phase:** A1.5 [Places]
**Textbook grades searched:** 4, 5, 6

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> словами, у майбутньому часі.
> Крок 4. Розглянь таблицю змінювання дієслів, виражених двома
> Однина
> Множина
> Особа
> Питання
> Приклад
> Особа
> Питання
> Приклад
> 1-ша (я)
> що буду 
> робити?
> буду іти
> 1-ша 
> (ми)
> що будемо 
> робити?
> будемо 
> іти
> 2-га (ти)
> що будеш 
> робити?
> будеш іти
> 2-га 
> (ви)
> що будете 
> робити?
> будете 
> іти
> 3-тя (він, 
> вона, 
> воно)
> що буде 
> робити?
> буде іти
> 3-тя 
> (вони)
> що будуть 
> робити?
> будуть 
> іти
> Крок 5. Яке слово змінюється: допоміжне чи основне?
> Крок 6. Зроби висновок. Порівняй його з правило

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 244
> 551   Визначте, які етикетні формули доцільно використовувати 
> в таких ситуаціях. Для чого ми їх використовуємо?
> 1. … ти приніс мені словник? 2. … котра година? 3. … ви не 
> підкажете, як пройти до вулиці Київської? 4. … я не можу 
> виконати це доручення. 5. … з якої колії відправляється 
> потяг № 242? 6. Сергію, відчини, … , вікно.
> 552   Прочитайте вголос діалог і схарактеризуйте його. Які норми 
> мовленнєвого етикету порушено? Відредагуйте діалог так, щоб 
> тональність спілкування набула доброз

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 36
> 1.	Прочитайте діалог і виконайте завдання.
> Писанка розводить руками: 
> — На важку роботу не хочеш, то йди на легку.
> — І на легку не бажаю: на легкій ніц не зароблю.
> — О напасть! — чухає потилицю Писанка. — То куди ж мені тебе по­
> слати?
> — Хмиз палити пошліть, ще я там не була. Я люблю ватри розводити 
> (Олесь Гончар). 
> А.	 Які слова свідчать про те, що героїня родом із Гуцульщини? 
> Б.	 Що означають виділені слова?
> Діалектизми — слова, які використовують у своєму мовленні жите­
> лі певної місцево

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> 18
> 5. Спиши останнє речення з тексту про Францію. Підкресли 
> слово, вжите в переносному значенні. Склади й запиши 
> речення, у якому це слово матиме пряме значення.
> 5
> 6. Прочитай імена французьких друзів Читалочки. Поясни, 
> на які українські імена вони схожі.
> 6
> 7. Від французьких друзів Читалочка почула знайомі їй
> слова. Прочитайте їх. Чи знаєте, що вони означають?
> Знайдіть  у  довідці  відповідні  їм  українські слова.
> Довідка:  Дякую.  Привіт!  До побачення.
> Салþт! 
> Мерс³.
> Оревуàр.
> 9. Уяви, що

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 204
> Відомості із синтаксису й пунктуації. Види речень за метою висловлення
>  Дайте домашку 
> з математики.
> 15:28
> Я загубила в класі 
> щоденник. Ніхто 
> не бачив?
> 15:39
> На завтра треба 
> готувати поробку?
> 15:53
> Візьміть завтра під-
> ручники з англій-
> ської, буде заміна. 
> 16:21
> Ходімо разом 
> у кіно. 
> р
> 16:42
> Я не знаю, як 
> розв’язати задачу. 
> Допоможіть!!!  
>  
>  
> Д
>  
>  
>  
> 17:36
> Вправа 331
> 1. Прочитайте речення, узяті з чату 
> класу .
> 2. Назвіть спочатку розповідні ре-
> чення, потім питальні та  спону-
> кальн

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 26
> 1.	Прочитайте діалог і виконайте завдання.
> — Як довго ще чекати на подорож до моря?
> — Неділю? 
> — Як? Один день залишився? Я не встигну зібратися! 
> — Не один, а сім днів! Так що встигнеш…
> А.	 Через яке слово сталося непорозуміння?
> Б.	 Яка причина цього непорозуміння?
> До лексичних помилок належать: 
> •	 тавтологія — уживання того самого слова або спільнокореневих 
> слів в одному чи в сусідніх реченнях: Використання екологічно чис-
> тих продуктів корисне для здоров’я;
> •	 калькування — слово або вис

## Куди? Знахідний відмінок (Where To? Accusative)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 130.1. Прочитай речення.
> Богдан милувався квітами. Аліна раділа подарункові. Над 
> полем красувалася веселка. На лавочці сиділи діти. Взимку 
> ми підгодовуємо птахів.
> 2. Випиши словосполучення з виділеними іменниками. Познач 
> відмінок іменників. Запиши за зразком.
> Зразок. Йшла (чим?) садом (Од. в.).
> РОЗРІЗНЕННЯ НАЗИВНОГО ТА ЗНАХІДНОГО ВІДМІНКІВ^
> * 
> 131.1. Пригадай відмінки іменників та питання, на які вони від­
> повідають. Визнач відмінок виділених іменників.
> Тато намалював кошеня. Кошеня лягло на

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 204
> Відомості із синтаксису й пунктуації. Види речень за метою висловлення
>  Дайте домашку 
> з математики.
> 15:28
> Я загубила в класі 
> щоденник. Ніхто 
> не бачив?
> 15:39
> На завтра треба 
> готувати поробку?
> 15:53
> Візьміть завтра під-
> ручники з англій-
> ської, буде заміна. 
> 16:21
> Ходімо разом 
> у кіно. 
> р
> 16:42
> Я не знаю, як 
> розв’язати задачу. 
> Допоможіть!!!  
>  
>  
> Д
>  
>  
>  
> 17:36
> Вправа 331
> 1. Прочитайте речення, узяті з чату 
> класу .
> 2. Назвіть спочатку розповідні ре-
> чення, потім питальні та  спону-
> кальн

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 203
> ЗАХОПЛИВИЙ СВІТ ПРИГОДНИЦЬКИХ І ФАНТАСТИЧНИХ ПОВІСТЕЙ 
> Якось, блукаючи підвалами банку, 
> який прибирала моя бабуся, я виявив 
> невеличкі двері під сходами. Вони 
> були геть непомітні. Ніби хтось їх 
> навмисне 
> замаскував, 
> накидавши 
> біля них цілу купу відер і довгих 
> палиць із кудлатими ганчір’яними 
> насадками для миття підлоги. Тоді, 
> влітку, я розгріб завал, натиснув на 
> ручку дверей. Вони на диво легко від-
> чинилися. Так я знайшов потайний вхід до банку, про який, 
> напевне, давно забули. Я

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> 1
> За змістом вірша поставте одне одному запитання і дайте 
> на них відповіді.
> 112.1. Прочитай таблицю в поданій послідовності: 
> спочатку назву кожного відмінка, далі — відмінкові питання, 
> а відтак — іменники у формі відповідного відмінка.
> 2. Досліди, які відмінки відповідають на однакові питання. 
> У яких відмінках слова можуть мати два закінчення? Біля 
> питання якого відмінка є прийменник?
> Назва 
> відмінка
> Скорочене 
> позначення
> Питання
> Рід іменника
> до назв 
> істот
> до назв 
> неістот
> чоловічий
> жіночи

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 171
>  § 74.  Звертання.  Розділові  знаки  для  відокремлення  звертань
> 1. Прочитайте народні вислови та виконайте завдання.
> На тобі небоже що мені негоже.
> Заплач, Матвійку, дам копійку.
> А. У якому реченні легше визначити, до кого звертаються? Завдяки 
> чому?
> Б. Яке слово треба відокремити комами в реченні, що ліворуч? 
> § 74.  ЗВЕРТАННЯ.  РОЗДІЛОВІ  ЗНАКИ  ДЛЯ  ВІДОКРЕМЛЕННЯ  ЗВЕРТАНЬ
> Звертання — слово (або сполучення слів), що називає особу чи пред-
> мет, до яких спрямоване мовлення: Зоре моя вечі

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 94
> Iменник
> Іменник у формі називного відмінка означає того, хто виконує дію, 
> і в реченні виступає підметом. Іменник у формі знахідного відмін-
> ка означає предмет, на який спрямована дія, і в реченні виступає 
> додатком. ПОРІВНЯЙМО:
>                Н. в. Зн. в. 1. Їде автомобіль. 2. Ремонтують автомобіль. І. Спишіть речення, підкресліть іменники як члени речення та надпи-
> шіть над ними відмінок. Поясніть, яке значення мають ці відмінки. 1. Íàçàð ïåðåçàâàíòàæèâ ñâіé êîìï’þòåð. 2. Àëіíà äîâãî
> ðîçäèâ

## Де чи куди? (Where or Where To?)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> Це час, коли за друзями 
> ми скучим — як ніколи, 
> і нам страшенно схочеться 
> скоріше знов до школи!..
> •  Виконайте завдання в «Зошиті з розвитку писемного мовлен­
> ня».

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 158
> СИНТАКСИС  І  ПУНКТУАЦІЯ  
> рий кобзар-запорожець прямує кудись у дорогу. Не сам він: слідом шку-
> тильгає гнідий кінь, хитає головою — теж старий, аж сивий (М. Пригара). 
> А. Знайдіть по одному прикладу різних за значенням обставин: місця 
> (де? звідки?), часу (коли? відколи? як давно?), міри й ступеня (на-
> скільки? якою мірою?), способу дії (як? яки

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Куди? Знахідний відмінок (Where To? Accusative)` (~300 words)
- `## Де чи куди? (Where or Where To?)` (~300 words)
- `## Підсумок — Summary` (~300 words)
- `## Підсумок` (~150 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 15-30% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — explain the grammar concept once, clearly.
- EXAMPLES: Ukrainian sentences in bulleted lists (each line: Ukrainian — English gloss). Max 2-4 per rule.
- TABLES: Paradigm tables, case endings, vocabulary groups — all cells Ukrainian.
- PATTERN BOXES: Show transformations: `книга → книгу` (nominative → accusative).
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences go in tables, bulleted lists, or pattern boxes.
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

GRAMMAR CONSTRAINTS (A1.5 — Places & Movement, M29-M36):
Euphony, locative, accusative direction, genitive origin.

ALLOWED:
- Euphony rules (у/в, і/й, з/із/зі)
- Locative case with в/у/на (Де?)
- Accusative for direction (Куди?)
- Genitive for origin (Звідки? З + genitive)
- All present tense verbs

BANNED: Past/future tense, dative, instrumental,
participles, passive voice, complex subordination

### Vocabulary

**Required:** куди (where to), йти (to go on foot), їхати (to go by transport), школа → у школу (to school), робота → на роботу (to work), банк → у банк (to the bank)
**Recommended:** магазин → у/в магазин (to the shop), бібліотека → у бібліотеку (to the library), ресторан → у ресторан (to the restaurant), Одеса → в Одесу (to Odesa), повертатися → додому (to return home)

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
