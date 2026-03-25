<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Too short: 969 words (target: 1200, minimum: 1020)
</correction_directive>

LEARNINGS FROM PAST BUILDS (same error patterns seen before):
- [GLOBAL] сес-тра is a VALID word division per Правопис 2019 §49. Do NOT mark it as an error. Phonetic syllabification (се-стра) and typographic word division (сес-тра) follow different rules — both are correct in their respective contexts.
- [GLOBAL] Ukrainian textbooks teach a hands-on-EARS test for voicing (закрий долонями вуха), NOT a hand-on-throat test. The hand-on-throat test is a valid phonetics technique but must NOT be attributed to Ukrainian textbooks. Source: Кравцова 2019, Grade 2, p.39.
- [GLOBAL] Do NOT invent Ukrainian words for minimal pairs. "Сір" is NOT a word meaning "grey" — the correct form is "сірий". Use verified minimal pairs only: кит/кіт, бити/біти, лис/ліс.
- [GLOBAL] NEVER frame Ukrainian as "lacking" or "missing" letters that Russian has. Ukrainian has its own 33-letter alphabet — it is complete. Do NOT write "Ukrainian lacks Ъ, Ы, Э" or "Ukrainian doesn't have these Russian letters." Instead, highlight what Ukrainian HAS: Ґ, Є, Ї, І are unique to Ukrainian. Present Ukrainian on its own terms.
- [a2/comparison] Same errors (WORD_COUNT): V6 build failed after 3 attempts
- [b1/alternation-vowels] Same errors (WORD_COUNT): V6 build failed after 3 attempts
- [b1/metalanguage-sounds] Same errors (WORD_COUNT): V6 build failed after 3 attempts

# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **17: Verbs Group II** (A1, A1.3 [Actions]).

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
module: a1-017
level: A1
sequence: 17
slug: verbs-group-two
version: '1.2'
title: Verbs Group II
subtitle: Говорю, говориш, говорить — the second pattern
focus: grammar
pedagogy: PPP
phase: A1.3 [Actions]
word_target: 1200
objectives:
- Conjugate Group II (-ити) verbs in present tense for all persons
- Distinguish Group I (-єш/-є/-ють) from Group II (-иш/-ить/-ять) endings
- Use 6 high-frequency Group II verbs in sentences
- Compare and contrast both conjugation groups
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Talking about abilities (ULP Ep24 pattern): — Ти говориш українською?
    — Так, я говорю трохи. А ти? — Я бачу, що ти добре говориш! — Дякую, я вчуся.
    Group II verbs in natural conversation.'
  - 'Dialogue 2 — Evening at home: — Що ти робиш увечері? — Я дивлюся фільм. А ти?
    — Я вчу нові слова. — Молодець! Note: дивлюся (I watch) — the -ся ending means
    ''oneself'' (preview for M20).'
- section: Друга дієвідміна (Group II Verbs)
  words: 300
  points:
  - 'Group II verbs have infinitive in -ити (or -іти): говорити → я говорю, ти говориш,
    він/вона говорить, ми говоримо, ви говорите, вони говорять. Pattern: stem + -ю/-у,
    -иш, -ить, -имо, -ите, -ять/-ать.'
  - 'Six essential Group II verbs: говорити (to speak): говорю, говориш, говорить...
    бачити (to see): бачу, бачиш, бачить... робити (to do/make): роблю, робиш, робить...
    вчити (to study/teach): вчу, вчиш, вчить... просити (to ask/request): прошу, просиш,
    просить... ходити (to go/walk regularly): ходжу, ходиш, ходить...'
- section: Група I чи II? (Which Group?)
  words: 300
  points:
  - 'Compare the endings side by side: | | Group I (-ати) | Group II (-ити) | | я
    | читаю | говорю | | ти | читаєш | говориш | | він/вона | читає | говорить | |
    вони | читають | говорять | Key difference: ти form → -єш (I) vs -иш (II), вони
    → -ють (I) vs -ять/-ать (II). Note: after ч, ш, ж, щ → -ать (not -ять): бачать,
    вчать, ходять (but not *бачять).'
  - 'Consonant changes in Group II (я-form only): робити → роблю (б→бл), ходити →
    ходжу (д→дж), просити → прошу (с→ш), бачити → бачу (no change). These changes
    only affect the я-form — all other forms are regular. Don''t memorize the rule
    — just learn each я-form with the verb.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Two verb groups — two ending patterns: Group I (-ати): -ю, -єш, -є, -ємо, -єте,
    -ють Group II (-ити): -ю/-у, -иш, -ить, -имо, -ите, -ять Consonant shifts in Group
    II я-form (роблю, ходжу, прошу). Self-check: Conjugate ''бачити'' for я, ти, він/вона.
    Is ''слухати'' Group I or II? How about ''говорити''?'
vocabulary_hints:
  required:
  - говорити (to speak)
  - бачити (to see)
  - робити (to do/make)
  - вчити (to study/teach)
  - просити (to ask/request)
  - ходити (to go/walk regularly)
  recommended:
  - дивитися (to watch — reflexive preview)
  - вчитися (to learn — reflexive preview)
  - любити (to love — review, Group II!)
  - трохи (a little)
  - добре (well)
  - увечері (in the evening)
activity_hints:
- type: fill-in
  focus: 'Conjugate: я говор__, ти говор__, він говор__'
  items: 10
- type: group-sort
  focus: Sort verbs into Group I (-ати) and Group II (-ити)
  items: 10
- type: quiz
  focus: 'Choose correct form: Ти (бачу/бачиш/бачить) це?'
  items: 8
- type: fill-in
  focus: 'Complete with correct verb form: Вона ___ українською. (говорити)'
  items: 6
connects_to:
- a1-018 (I Want, I Can)
prerequisites:
- a1-016 (Verbs Group I)
grammar:
- 'Group II conjugation: -ю/-у, -иш, -ить, -имо, -ите, -ять'
- 'Consonant changes in я-form: б→бл, д→дж, с→ш, т→ч'
- Distinguishing Group I vs Group II by endings
register: розмовний
references:
- title: Караман Grade 10, p.179
  notes: 'І vs ІІ дієвідміна: endings and infinitive patterns.'
- title: Захарійчук Grade 4, p.110-113
  notes: Verb conjugation tables for present tense.
- title: ULP Season 1, Episode 24
  url: https://www.ukrainianlessons.com/episode24/
  notes: More verbs and conjugation practice.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Verbs Group II
**Module:** verbs-group-two | **Phase:** A1.3 [Actions]
**Textbook grades searched:** 3, 4, 5

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 4
> ЧОГО  Я  ВЧУСЯ?
> Вдома вчить мене матуся,
> в школі вчить мене учитель,
> і сама я добре вчуся
> рідним словом говорити.
> Вчусь не тільки говорити,
> а й читати і писати.
> Щоб усі раділи діти,
> щоб пишались мама й тато.
> Щоб пішла між люди слава,
> щоб сказали: «От дитинка
> добра, мудра і ласкава.
> Це маленька українка!»
> Що таке текст
> 1
> Розпізнаю текст за його основними ознаками
> 	 	
> 1   Прочитайте вірш Михайла Маморського. Про що розповідається 
> в кожному з речень? Чи пов’язані вони одне з одним? Чи 
> становля

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 123
> 293.		Прочитай слова.
> (що?) Добро, (який?) добрий, (… ?) добре;
> (що?) низина, (який?) низький, (… ?) унизу;
> (що?) ранок, (який?) ранній, (… ?) уранці;
> (що?) далечінь, (який?) далекий, (… ?) здалеку.
> 	 Визнач частини мови, які ти знаєш. Постав питання до підкрес-
> лених слів.
> 	 Спиши підкреслені прислівники, укажи в дужках питання.
> 294.		Прочитай сполучення дієслів із прислівниками.
> Світить (як?) яскраво, … ; світить (де?) високо, …. ; хо-
> дить (як?) тихо, … ; співає (як?) весело, … ; прокинув

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 8
> У цьому розділі ми поговоримо про таке: 
>  Для чого нам потрібна мова та чому її варто вивчати?
>  Чому мову називають основним засобом спілкування?
>  Чому українцям важливо розмовляти 
> українською  мовою?
> ВСТУП. 
> УКРАЇНСЬКА  МОВА  В  ЖИТТІ  УКРАЇНЦІВ

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> Умовні позначення
> — початок уроку
> — домашнє завдання
> — мовно-логічні завдання
> — дослідження мовних явищ
> — словникова скарбничка (слово, вимову і написання яко- 
>      го потрібно запам’ятати)
> — робота в парі, групі
> Вересень покликав дітей до школи. З великою радістю 
> чекаю на вас і я, ваша добра приятелька — «Українська мова». 
> Ми з вами знову помандруємо стежками цікавих мовних знахідок 
> та відкриттів. Я допоможу вам збагатити ваше мовлення новими 
> словами, поведу у світ цікавого мовознавства.
> Р

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> 5
> 5.	 	Розгляньте діаграму. Обговоріть її зміст. Визначте, що ви вже 
> вивчили із цього розділу, а що будете вивчати. Повторіть 
> вивчене.
> Застарілі й нові слова
> 	
> Синоніми до слова абетка — … , … .
> 	
> Букви пишемо та … .
> 	
> Звуки ми чуємо та … .
> 	
> Звуки є … та … . Приголосні звуки є … .
> 	 Розглянь слово, написане різними мовами.
> 	 Які з них ти можеш прочитати? А котрі — ні? Зроби висновок.
> 6.	 	Прочитай текст.
> Мова — давній витвір людини. Завдяки слову ми розу-
> міємо одне одного. Без слова не було

> **Source:** unknown, Grade 5
> **Score:** 0.33
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

## Друга дієвідміна (Group II Verbs)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> Виконай розбір дієслова виступатиме.
> Все навколо  ? , 
> річка ллється і  ? .
> Тихо, тихо вітер віє
> і з травою  ? .  
> Як тут всидіти на місці,
> коли все живе,  ? ,
> скрізь  ?  пташки крилаті,
> ?  сонце золоте?!
> 	 	
> 11   Прочитайте вірш Олександра Олеся, уставляючи дієслова 
> з довідки.
> інформація
>  інформував
>  інформувала
>  інформували
> виступав
> виступає
> виступить
> виступ
> попереджав
> попередить
> попереджала
> попереджали
>   Пограйтесь у гру  
> «Вилучте «зайве» слово».   
> 	 	
> 9   З дієсловами другого стовпчика

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 110
> 	 Послухай або прочитай повторно текст. Користуючись малюнка-
> ми (с. 109), додатковим матеріалом у «Зошиті з розвитку усного 
> та писемного мовлення», напиши докладний переказ тексту.
> 261.		Розгляньте таблицю змінювання дієслів теперішнього часу 
> в однині та множині за особами. Обговоріть її зміст.
> 2-га 
> ти
> 2-га 
> ви
> що 
> робиш?
> що 
> робите?
> пливеш,
> кричиш
> пливете,
> кричите
> 3-тя 
> він, вона, 
> воно
> 3-тя 
> вони
> що 
> робить?
> що 
> роблять?
> пливе,
> кричить
> пливуть,
> кричать
> Особа
> Особа
> 1-ша 
> я
> 1-ша 
> ми
> що

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 153
>  § 67.  Другорядні  члени  речення.  Додаток
> 1. Прочитайте речення та виконайте завдання.
> Навколо дому ростуть квіти.
> Я щодня поливаю квіти.
> А. У якому реченні дія присудка спрямована на квіти?
> Б. У якому реченні виділене слово можна замінити на займенник їх, а в 
> якому — на займенник вони?
> § 67.  ДРУГОРЯДНІ  ЧЛЕНИ  РЕЧЕННЯ.  ДОДАТОК
> Додаток — це другорядний член речення, що означає предмет, на 
> який спрямована дія або щодо якого ця дія відбувається, і відповідає 
> на питання непрямих відмінк

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 152
> Досліди, як змінюються 
> дієслова за часами.
> Я — дослідник
> Я — дослідниця
> Навчаюся змінювати дієслова за часами
> міркували
> міркуємо
> будемо міркувати
> 6   Прочитай слова і порівняй їх.
> Що означає дієслово? Коли відбувається дія?
> На яке питання відповідає дієслово?
> До якої часової форми належить кожне дієслово?
>   Зроби висновок, як змінювати дієслова за часами, і звір його з таблицею.
> Час дієслів
> Питання
> Приклади
> Теперішній час
> що роблю?
> що робиш?
> що робить?
> що роблять?
> лечу, пишу
> летиш, пишеш

> **Source:** unknown, Grade 4
> **Score:** 0.33
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
> **Score:** 0.33
>
> 158
> однокласників, вибачте мене, потребує допомогу, зраджува-
> ти мені.
> ІІ. Складіть і запишіть речення з двома словосполученнями (на вибір).
> Культура мовлення
> ПРАВИЛЬНО
> НЕПРАВИЛЬНО
> вибачте мені
> дякую вам
> сподіватися на краще
> оволодівати знаннями
> опановувати знання
> милуватися природою 
> нехтувати своїм здоров’ям 
> зраджувати друга
> потребувати спокою 
> вибачте мене
> дякую вас
> сподіватися кращого
> оволодівати знання
> опановувати знаннями
> милуватися з природи
> нехтувати своє здоров’я 
> зраджувати другові 
> п

## Група I чи II? (Which Group?)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 37
> Дівчинкакнижкучитає,
> аСонцеперегортає
> сторінкийсвітловливає
> влітеритавслова.
>  Хто дійові особи вірша?
>  Поміркуй, чому соняшника образило прохання дівчин-
> ки. Що його потім здивувало?
>  Яку інтонацію читання підказують вислови: дуже 
> довго дивився, прохати, здивувався, засоромлено
> пооглядався?
> Поміркуйте разом! Розгляньте малюнок до вірша. 
> Який уривок з тексту проілюстровано? Які почуття
> дійових осіб відобразила художниця? Чи випадково 
> поет в одному вірші пише про Сонце — джерело світ-

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 157
> ЗМICТ
> ЧИТАЄМО Й РОЗПОВІДАЄМО
> ПРО СВОЇ ЗАХОПЛЕННЯ
> Ліна Костенко. Вже брами літа замикає осінь…  . . . . . . . . . . . . . . . 5
> Олександра Савченко. Як читають книжки? . . . . . . . . . . . . . . . . . . 6
> Марія 

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Друга дієвідміна (Group II Verbs)` (~300 words)
- `## Група I чи II? (Which Group?)` (~300 words)
- `## Підсумок — Summary` (~300 words)
- `## Підсумок` (~150 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 15-25% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — explain the grammar concept once, clearly.
- EXAMPLES: Ukrainian sentences in bulleted lists (each line: Ukrainian — English gloss). Max 2-4 per rule.
- TABLES: Paradigm tables, gender sorting, vocabulary groups — all cells Ukrainian.
- PATTERN BOXES: Show transformations and rules: `книга → книги` (singular → plural).
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences go in tables, bulleted lists, or pattern boxes — never in flowing prose.
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

GRAMMAR CONSTRAINTS (A1.3 — Actions & Desires, M15-M21):
Present tense verbs, modals, questions, reflexives.

ALLOWED:
- Present tense conjugation (both groups: -ати and -ити)
- Modal verbs: хотіти, могти, мусити + infinitive
- Question words: Хто? Що? Де? Куди? Коли? Чому?
- Negation: не/ні
- Reflexive verbs (-ся/-сь)
- 'Мені подобається' as lexical chunk (NO dative grammar)

BANNED: Past/future tense, cases beyond nominative,
participles, passive voice, complex subordinate clauses

### Vocabulary

**Required:** говорити (to speak), бачити (to see), робити (to do/make), вчити (to study/teach), просити (to ask/request), ходити (to go/walk regularly)
**Recommended:** дивитися (to watch — reflexive preview), вчитися (to learn — reflexive preview), любити (to love — review, Group II!), трохи (a little), добре (well), увечері (in the evening)

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
