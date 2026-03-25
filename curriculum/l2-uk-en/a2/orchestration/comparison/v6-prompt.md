<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Missing section heading: 'Вищий ступінь: порівнюємо два предмети (Comparative: Comparing Two Things)'
- FIX: Missing section heading: 'Найвищий ступінь: хто найкращий? (Superlative: Who Is the Best?)'
- FIX: Missing section heading: 'Особливі форми: більший, кращий, гірший (Irregular Forms)'
- FIX: Missing section heading: 'Порівняння у житті (Comparisons in Daily Life)'
- FIX: Too short: 12 words (target: 2000, minimum: 1700)
- FIX: Missing 10/10 required vocab: порівняння (comparison), більший (bigger), менший (smaller), кращий (better), гірший (worse)
- NOTE: Plan expects 4 exercise(s) but content has 0 placeholders
</correction_directive>

# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **48: Більше, краще, найкраще** (A2, A2.8 [Refinement and Graduation]).

**Target: 2000–3000 words** of prose (Ukrainian examples count toward word total, headings and exercise placeholders do not).

---

## Step 1: Pacing Plan (output this FIRST)

Before writing any content, output a `<pacing_plan>` block. Evaluate each section from the plan and commit to a word budget. This prevents frontloading early sections and rushing later ones.

```
<pacing_plan>
Section 1 "Title": ~XXX words — [1-sentence content focus]
Section 2 "Title": ~XXX words — [1-sentence content focus]
...
Summary: ~150 words
Total: 2000+ words
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
7. **Hit the word target** — you MUST write 2000–3000 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
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
module: a2-048
level: A2
sequence: 48
slug: comparison
version: '1.0'
title: Більше, краще, найкраще
subtitle: Ступені порівняння прикметників та прислівників
focus: grammar
pedagogy: PPP
phase: A2.8 [Refinement and Graduation]
word_target: 2000
objectives:
- Learner can form the comparative degree of adjectives using both synthetic
  (-ший) and analytic (більш) forms.
- Learner can form the superlative degree using the prefix най- (найсолодший)
  and the analytic form (найбільш солодкий).
- Learner can correctly use suppletive comparative forms (великий → більший,
  добрий → кращий, поганий → гірший, малий → менший).
- Learner can use comparative constructions with ніж and за + Accusative
  to compare two objects.
content_outline:
- section: 'Вищий ступінь: порівнюємо два предмети (Comparative: Comparing Two Things)'
  words: 650
  points:
  - 'Synthetic comparative: add -ший/-іший to the stem (солодкий → солодший,
    цікавий → цікавіший). Consonant alternations: г→ж, к→ч, х→ш
    (дорогий → дорожчий).'
  - 'Analytic comparative: більш/менш + adjective (більш солодкий, менш
    відомий). When to prefer analytic over synthetic forms.'
  - 'Comparison constructions: ніж + Nominative (Київ більший, ніж Львів)
    and за + Accusative (Київ більший за Львів). Both are correct and
    interchangeable.'
  - 'Practice dialogues: comparing foods, cities, seasons — which is better,
    bigger, more interesting?'
- section: 'Найвищий ступінь: хто найкращий? (Superlative: Who Is the Best?)'
  words: 500
  points:
  - 'Synthetic superlative: prefix най- to the comparative stem
    (найсолодший, найцікавіший, найдорожчий).'
  - 'Analytic superlative: найбільш/найменш + adjective (найбільш
    популярний, найменш відомий).'
  - 'Usage in context: Яке місто найбільше в Україні? Хто найкращий
    футболіст? Яка пора року найгарніша?'
- section: 'Особливі форми: більший, кращий, гірший (Irregular Forms)'
  words: 450
  points:
  - 'Suppletive forms that must be memorized: великий → більший → найбільший,
    малий → менший → найменший, добрий → кращий → найкращий,
    поганий → гірший → найгірший, гарний → кращий/гарніший.'
  - 'Common adverb comparatives: добре → краще, погано → гірше,
    багато → більше, мало → менше.'
  - 'Typical errors: *більш кращий (double comparison) — explain why
    this is wrong.'
- section: 'Порівняння у житті (Comparisons in Daily Life)'
  words: 400
  points:
  - 'Dialogue: two friends discuss which vacation destination is better —
    comparing prices, weather, food, activities.'
  - 'Reading practice: a short text ranking Ukrainian cities by size,
    population, and beauty.'
  - 'Useful phrases: набагато кращий (much better), трохи більший
    (a bit bigger), значно цікавіший (significantly more interesting).'
vocabulary_hints:
  required:
  - порівняння (comparison)
  - більший (bigger)
  - менший (smaller)
  - кращий (better)
  - гірший (worse)
  - найкращий (the best)
  - найбільший (the biggest)
  - солодший (sweeter)
  - цікавіший (more interesting)
  - ніж (than)
  recommended:
  - набагато (much, significantly)
  - трохи (a little, slightly)
  - значно (considerably)
  - навпаки (on the contrary)
activity_hints:
- type: fill-in
  focus: Form the comparative from the base adjective
  items: 6
- type: quiz
  focus: Choose the correct suppletive form (більший, кращий, гірший)
  items: 6
- type: match-up
  focus: Match adjective to its superlative form
  items: 6
- type: true-false
  focus: Identify correct and incorrect comparative constructions
  items: 6
references:
- title: Заболотний Grade 6, Ступені порівняння прикметників
  notes: Full presentation of comparative and superlative formation with exercises
- title: "ULP: Ukrainian Adjectives — Degrees of Comparison"
  url: "https://www.ukrainianlessons.com/adjectives-comparison/"
  notes: Synthetic vs analytic forms explained with examples

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Більше, краще, найкраще
**Module:** comparison | **Phase:** A2.8 [Refinement and Graduation]
**Textbook grades searched:** 1, 2, 3, 5

---

## Вищий ступінь: порівнюємо два предмети (Comparative: Comparing Two Things)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 54
> На дереві сиділи 
> .
>  цвіли  на  клумбі.
> Гіркий смак у 
> . 
>  — солодкі.
> 	
> Визнач, якому слову — назві намальованого 
> предмета відповідає кожна схема.
> 	
> Доповни речення словами.
> [ –•| –•= ] 
> [ =•|  =•= ] 
> [ –  = • | –•=] 
> 	
> Розгадай кросворд.
> 1
> 2
> 3
> 5
> 6
> 4
> 1
> 2
> 3
> 4
> 5
> 6
> Pidruchnyk.com.ua

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> • Поставте питання до виділених слів. Які з них називають дії,
> а які — предмети?
> • Випишіть виділені слова разом із 
> тими, з якими вони зв'язані в реченні.
> гарний ніс — 
> ніс подарунки
> я - дослідник
> Поміркуй і скажи, від 
> якого дієслова походить
> слово подарунок.
> В
> Я — ДОСЛІДНИЦЯ

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 41
> 5. Випиши з тексту про музей виділені слова. Добери 
> до них спільнокореневі, щоб у корені відбулося чергу-
> вання приголосних звуків. Підкресли букви, які познача-
> ють ці звуки.
> 6. Разом з однокласниками/однокласницями пригадай-
> те, до якого свята виготовляють писанки. Що з ними
> роблять? Чи доводилося тобі виготовляти писанки?
> Напиши  про  це  текст  (3–4  речення).
> 7. Спиши прислів’я, розкривши дужки. Познач корінь 
> у змінених словах. Підкресли букви, які позначають
> звуки,  що  чергуються  в

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 233
> Відомості із синтаксису й пунктуації.  Складне речення
> Частини складного речення можуть бути поєднані лише інтона-
> ційно або ж за допомогою інтонації та сполучників чи сполучних 
> слів.  Залежно від способу зв’язку між частинами складного речення 
> визначають його типи: складні безсполучникові та сполучнико-
> ві речення.  Порівняйте:
> Складні  
> безсполучникові речення
> Складні  
> сполучникові речення
> Уявіть: у  вас з’явився 
> собака найкращої породи 
> вартістю в  кілька тисяч 
> доларів.
> Уявіть, що у

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 101
> Повторюємо разом
> Слова — назви ознак. 
> Слова, протилежні за 
> значенням
>  
> 	 Розглянь малюнки. 
> Який?
> Яка? 
> Яка? 
> Слова, які відповідають на питання 
> який? яка? яке? які?, указують на 
> ознаку предмета.
> 	 Перепиши перше речення тексту (с. 99). Під-
> кресли слова — назви ознак кошеняти. По-
> став до цих слів запитання.
> 	 Прочитай текст.
> Чижик-Пижик сидів на високій гілці й 
> крутив головою. Раптом перед ним про-
> летіла яскрава бабка. Він хотів її схопи-
> ти, але зірвався з гілки. Зірвався, за-
> кру

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> 77
> 275.	 Розгадай ребус.
> 276. 1.	 Прочитай. Що було для тебе новим?
> Самці птахів часто мають яскраве 
> забарвлення. Але чи розрізняє самка ці 
> кольори? Під час експериментів було дове-
> дено: птахи бачать усі кольори веселки!
> 2.	 Запишіть наѳзви кольорів веселки. Перевірте одні в одних запи-
> сані слова. Поставте до слів питання так, щоб довести, що 
> це — прикметники (слова, які називають ознаки предметів).
> червоѳний
> 277. 1.	 Назви́ зображені предмети. До якої частини мови належать ці 
> слова?
> 2.	 В

## Найвищий ступінь: хто найкращий? (Superlative: Who Is the Best?)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 31
> к а з|к и
> Що відбувається? У назвах яких предметів є звук [и]?
> Прочитай або послухай слова. Визнач місце букви и 
> в цих словах. Яких предметів немає на малюнку? 
> Як ці чарівні предмети використовуються в казках? Які 
> ще чарівні предмети ти знаєш?
>  
> Текст. Заголовок. Театралізуємо
> За-ду-ма-ли-ся чарівні предмети: який із них 
> найбільш корисний? «Я, — сказав чарівний ки-
> лим, — можу швидко долетіти куди завгодно». 
> «Я, — сказала чарівна торбинка, — усіх нагодую 
> в будь-який час». «Я, — сказала

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> БЛИЗЬКІ ЗА ЗНАЧЕННЯМ 
> СЛОВА
> РОЗПІЗНАЮ БЛИЗЬКІ ЗА ЗНАЧЕННЯМ СЛОВА
> Я — уч ите л
> подорож
> А
> мандрівка
> ■ ■
> Я — учитель
> —І
> визначаю 
> добираю *
> Різні за звучанням слова можуть мати між собою 
> близькі значення.
> о о
> і| Прочитайте вірш Григорія Паламарчука. Чому птахів 
> називають то веселиками, то журавлями?
> Тому веселиками звуться журавлі, 
> що прилітають до веселої землі, 
> що теплий день приносять на крилі 
> і залишаються у нашому селі. 
> Лиш навесні веселики вони, 
> а журавлями звуться восени, 
> бо журяться

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 140
> Перевірте свої знання за розділом «Найдорожче, 
> що ми маєм, — це дружна і міцна сім’я».
> џ
> Назви ́ твори, які ти прочитав / прочитала в розділі. Назви ́
> віршовані та прозові твори. Що їх об’єднує? Який твір тобі 
> запам’ятався? Чому?
> џ
> Розкажи, як ти розумієш вислів, що став назвою розділу. 
> Які прислів’я, приказки, вислови видатних людей про 
> сім’ю, родину тобі відомі?
> џ
> Якими образними порівняннями збагатилося твоє мовлен-
> ня?
> Це вірш / оповідання / казка ... . Його автор / авторка ... .
> џ

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 88
> 219   Запишіть слова, поділивши їх на склади. Поставте над кожним 
> словом номер відповідного правила з таблиці. 
> Око, шия, льодяник, майоліка, знання, ліс, життя, під-
> живлювати, кукурудза, сірий, низько, байка, Лук’ян, дозрі-
> вати, виправдання, найвищий, цінності, стійкий. 
> 220   Випишіть слова, які не можна розривати для переносу. Складіть 
> із ними словосполучення. 
> Герб, армія, країна, юнак, один, клас, сом, школа, суве-
> нір, степ, озеро, лев, наголос, милозвучність, кран, скло. 
> 221   Зап

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 101
> Повторюємо разом
> Слова — назви ознак. 
> Слова, протилежні за 
> значенням
>  
> 	 Розглянь малюнки. 
> Який?
> Яка? 
> Яка? 
> Слова, які відповідають на питання 
> який? яка? яке? які?, указують на 
> ознаку предмета.
> 	 Перепиши перше речення тексту (с. 99). Під-
> кресли слова — назви ознак кошеняти. По-
> став до цих слів запитання.
> 	 Прочитай текст.
> Чижик-Пижик сидів на високій гілці й 
> крутив головою. Раптом перед ним про-
> летіла яскрава бабка. Він хотів її схопи-
> ти, але зірвався з гілки. Зірвався, за-
> кру

> **Source:** unknown, Grade 2
> **Score:** 0.33
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

## Особливі форми: більший, кращий, гірший (Irregular Forms)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 101
> Повторюємо разом
> Слова — назви ознак. 
> Слова, протилежні за 
> значенням
>  
> 	 Розглянь малюнки. 
> Який?
> Яка? 
> Яка? 
> Слова, які відповідають на питання 
> який? яка? яке? які?, указують на 
> ознаку предмета.
> 	 Перепиши перше речення тексту (с. 99). Під-
> кресли слова — назви ознак кошеняти. По-
> став до цих слів запитання.
> 	 Прочитай текст.
> Чижик-Пижик сидів на високій гілці й 
> крутив головою. Раптом перед ним про-
> летіла яскрава бабка. Він хотів її схопи-
> ти, але зірвався з гілки. Зірвався, за-
> кру

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> РОЗПОДІЛЯЮ СЛОВА НА ГРУПИ
> б| Згрупуй близькі за значенням слова і запиши їх.
> великий 
> розумний 
> метикований 
> вєлєтЄнський 
> дотепний
> мудрий 
> гігантський 
> кмітливий 
> безмежний
> ч*  -
> ■и
> групую
> доповнюю
> І к л 
> Г 
> ♦ 
> V 
> ♦ 
> V
> Метиковании — кмітливий, досвідчений. 
> ч
> Знайди слова із протилежним значенням і запиши їх за
> зразком.
> 1
> добро
> смуток
> ден

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Вищий ступінь: порівнюємо два предмети (Comparative: Comparing Two Things)` (~650 words)
- `## Найвищий ступінь: хто найкращий? (Superlative: Who Is the Best?)` (~500 words)
- `## Особливі форми: більший, кращий, гірший (Irregular Forms)` (~450 words)
- `## Порівняння у житті (Comparisons in Daily Life)` (~400 words)
- `## Підсумок` (~150 words)

Each section should follow the word budget specified. The total must reach 2000 words minimum.

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



### Vocabulary

**Required:** порівняння (comparison), більший (bigger), менший (smaller), кращий (better), гірший (worse), найкращий (the best), найбільший (the biggest), солодший (sweeter), цікавіший (more interesting), ніж (than)
**Recommended:** набагато (much, significantly), трохи (a little, slightly), значно (considerably), навпаки (on the contrary)

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
