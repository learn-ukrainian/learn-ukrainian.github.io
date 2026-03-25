# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **16: Verbs Group I** (A1, A1.3 [Actions]).

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
module: a1-016
level: A1
sequence: 16
slug: verbs-group-one
version: '1.1'
title: Verbs Group I
subtitle: Читаю, читаєш, читає — your first conjugation
focus: grammar
pedagogy: PPP
phase: A1.3 [Actions]
word_target: 1200
objectives:
- Conjugate Group I (-ати) verbs in present tense for all persons
- Use 6 high-frequency Group I verbs in sentences
- Recognize the Group I ending pattern (-у/-ю, -єш, -є, -ємо, -єте, -ють)
- Build simple sentences about daily activities
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — What do you do? (ULP Ep22 pattern): — Що ти робиш? — Я читаю книгу.
    А ти? — Я слухаю музику. — А що робить Олена? — Вона готує вечерю. All three persons
    (я/ти/він,вона) emerge naturally.'
  - 'Dialogue 2 — At work/school: — Де ти працюєш? — Я працюю в офісі. А ти? — Я не
    працюю, я навчаюся. — Ти знаєш українську? — Так, я вивчаю! Group I verbs in practical
    context.'
- section: Перша дієвідміна (Group I Verbs)
  words: 300
  points:
  - 'Варзацька Grade 4 p.129: verb conjugation table (теперішній час). Group I verbs
    have infinitive in -ати (or -увати, -яти): читати → я читаю, ти читаєш, він/вона
    читає ми читаємо, ви читаєте, вони читають. Pattern: stem + -ю, -єш, -є, -ємо,
    -єте, -ють.'
  - 'Six essential Group I verbs: читати (to read): читаю, читаєш, читає... знати
    (to know): знаю, знаєш, знає... працювати (to work): працюю, працюєш, працює...
    слухати (to listen): слухаю, слухаєш, слухає... гуляти (to walk): гуляю, гуляєш,
    гуляє... готувати (to cook): готую, готуєш, готує...'
- section: Я, ти, він/вона (Persons)
  words: 300
  points:
  - 'Focus on the three most-used forms: Я читаю (I read) — ending -ю Ти читаєш (You
    read) — ending -єш Він/вона читає (He/she reads) — ending -є These three cover
    90% of A1 conversations. Plural forms for recognition: ми читаємо, ви читаєте,
    вони читають.'
  - 'Building sentences with known vocabulary: Я читаю нову книгу. (M08 noun + M09
    adjective + M16 verb) Ти знаєш цю пісню? (M12 demonstrative + M16 verb) Вона слухає
    українську музику. (M16 verb + adjective + noun) Note: the object may change form
    (книгу, пісню) — learn as chunks for now.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Group I conjugation pattern: я -ю, ти -єш, він/вона -є, ми -ємо, ви -єте, вони
    -ють. Works for: читати, знати, працювати, слухати, гуляти, готувати. Self-check:
    Conjugate ''слухати'' for я, ти, він/вона. Say what you do (Я читаю...), ask what
    someone does (Що ти робиш?).'
vocabulary_hints:
  required:
  - читати (to read)
  - знати (to know)
  - працювати (to work)
  - слухати (to listen)
  - гуляти (to walk)
  - готувати (to cook)
  recommended:
  - робити (to do — Group II, preview as chunk)
  - вивчати (to study/learn)
  - малювати (to draw)
  - грати (to play)
  - вечеря (dinner, f)
  - музика (music — review from M15)
activity_hints:
- type: fill-in
  focus: 'Conjugate: я чита__, ти чита__, він чита__'
  items: 10
- type: quiz
  focus: 'Choose correct form: Вона (читаю/читаєш/читає) книгу.'
  items: 8
- type: match-up
  focus: 'Match person to verb form: я ↔ читаю, ти ↔ читаєш'
  items: 6
- type: fill-in
  focus: 'Complete the sentence: Що ти ___? — Я ___ музику. (слухати)'
  items: 6
connects_to:
- a1-017 (Verbs Group II)
prerequisites:
- a1-015 (What I Like)
grammar:
- 'Group I conjugation: -ю, -єш, -є, -ємо, -єте, -ють'
- Infinitive → present tense transformation
- 'Simple sentences: Subject + Verb + Object'
- 'Question: Що ти робиш?'
register: розмовний
references:
- title: Варзацька Grade 4, p.129
  notes: 'Conjugation table: теперішній час, persons and endings.'
- title: Захарійчук Grade 4, p.110
  notes: 'Verb conjugation table: однина та множина за особами.'
- title: ULP Season 1, Episode 22
  url: https://www.ukrainianlessons.com/episode22/
  notes: Present tense verbs in daily life.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Verbs Group I
**Module:** verbs-group-one | **Phase:** A1.3 [Actions]
**Textbook grades searched:** 3, 4, 5

---

## Діалоги (Dialogues)

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
> 123
> 3. Розгляньте таблицю. Зіставте вжиті вами дієслова з мо-
> ментом мовлення. Зробіть висновок.
> Запитання
> Дієслово
> Коли відбувається 
> дія і коли про неї 
> повідомили
> Час вико-
> нання дії
> Що зробив 
> Олег?
> накреслив
> дія відбулася до 
> того, як про неї 
> повідомили
> минулий
> Що робить 
> Олег?
> вирізує
> дія відбувається  
> в той час, коли про 
> неї повідомляють
> теперішній
> Що зробить 
> Олег?
> розмалює
> дія відбудеться 
> після того, як про 
> неї повідомили
> майбутній
> Дієслова змінюються за часами. Дієслова минулого

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 10
> РОЗВИТОК МОВЛЕННЯ
> 1.	Прочитайте текст і виконайте завдання в тестовій формі.
> Олег написав повідомлення подрузі. Коли Інна почула звук сповіщен-
> ня, спеціально дібраний для свого приятеля, то зраділа й одразу сказала 
> сестрі, що нарешті прийшла довгождана звістка. Сестра пораділа за Інну. 
> У цьому епізоді є всі види мовленнєвої діяльності, ОКРІМ 
> А письма
> Б читання 
> В говоріння 
> Г аудіювання 
> 2.	Прочитайте оповідання та виконайте завдання в тестовій формі. 
> ЗАКОХАНІ
> Я сиділа за столом перед ві

> **Source:** unknown, Grade 3
> **Score:** 0.33
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
>   Випишіть із вірша дієслова за абеткою. Що вони називають? На

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> •  Спишіть текст. Підкресліть дієслова. Укажіть у дужках час, 
> особу й число дієслів за зразком у тексті.
> Дієслова на -ся
> 370. Прочитайте вірш Галини Кирпи.
> Дерево трудиться назеленітися.
> Квіточка трудиться начервонітися.
> Бджілка трудиться налітатися.
> Метеличок трудиться нагойдатися.
> Травичка — водички напитися.
> Росинка — на білий світ надивитися.
> •  Випишіть дієслова на -ся. Доведіть, що вони означають дію, 
> спрямовану на себе. Позначте будову виділених слів.
> •  Зробіть звуко-буквений аналіз ді

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 49
>  § 19.  Омоніми
> 1.	Прочитайте діалог і виконайте завдання. 
> — Алло! Привіт, Олю! Що робиш?
> — Обідаю. 
> — А що ти їси? 
> — Лисички.
> — А хіба цих тварин їдять?! 
> — Відколи гриби стали тваринами? 
> — Нічого не розумію…
> А. Через яке слово виникло непорозуміння між подругами? 
> Б. Які значення має це слово?
> Омоніми — це слова, однакові за звучанням і написанням, але різні за 
> лексичним значенням: кран — трубка із затвором для виливання ріди-
> ни і кран — механізм для піднімання й переміщення вантажів.

## Перша дієвідміна (Group I Verbs)

> **Source:** unknown, Grade 3
> **Score:** 0.50
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
> **Score:** 0.50
>
> М айбутній час. Зміню вання дієслів 
> майбутнього часу за особами й числами
> 3 4 1 . Розгляньте таблицю.
> Особа
> ОДНИНА
> Особа
> МНОЖИНА
> 1-ша
> 1-ша
> я
> / \ А
> відвезу, везтиму, 
> буду везти
> ми
> А
> А
> відвеземо, везтимемо, 
> будемо везти
> 2-га
> 2-га
> ти
> А
>  А
> відвезеш, везтимеш, 
> будеш везти
> ви
> А
> А
> відвезете, везтимете, 
> будете везти
> 3-тя
> 3-тя
> він, вона, 
> воно
> А
> А
> відвезе, везтиме, 
> буде везти
> вони
> А
> А
> відвезуть, везтимуть, 
> будуть вез™
> •  Зверніть увагу на особові закінчення та три форми дієслів 
> майбутнього часу.

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 211
> Готуємося до тематичного оцінювання
> Виконайте завдання. Перевірте виконання, користуючись відповідями 
> на форзаці.
> 1. Звертання є в реченні
> А	 Настали осінні, тихі та смутні дні... (С. Васильченко).
> Б	 Замело снігами полтавські села та хутори (І. Цюпа).
> В	 Намалюй, зимова нічко, білосніжні сни (З. Мороз).
> Г	 Хтось, може, винен перед ними (Л. Костенко).
> 2. Однорідні члени є в реченні
> А	 Десь там матуся в обіймах втоми виходить зустрічать мене 
> на шлях (О. Довгоп’ят).
> Б	 Схилились вишні в р

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 112
> Дієслова змінюються за часами. 
> У теперішньому часі дієслова відповідають на 
> питання що робить?, що роблять?. Наприклад: живе, 
> пишуть. 
> У минулому часі — на питання що робив?, 
> що зробив?. Наприклад: жив, написав. 
> У майбутньому — на питання що робитиме?,
> що зробить?. Наприклад: житиме, напише.
> 3. Прочитай текст. Знайди спільнокореневі слова. Визнач, 
> від якого слова вони утворились.
> 3
> Село Петриківку майже 500 ро-
> ків тому заснував козак на прізвище 
> Петрик. Сьогодні вироби майстрів і 
> ма

> **Source:** unknown, Grade 4
> **Score:** 0.33
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
> **Score:** 0.33
>
> Розділ 1. МИСТЕЦЬКИЙ СПАДОК НАЩАДКАМ
> 46
> За­сіб  чи­тан­ня
> З­на­чен­ня­
> ­Темп чи­тан­ня
> Си­ла го­ло­су
> Тембр зву­ка
> Дик­ція
> Па­у­за
> Ін­то­на­ці­я
> ш­вид­кість чи­тан­ня — рів­на, упо­віль­не­на чи прис­ко­
> ре­на (за­леж­но від зміс­ту)
> ­мак­си­маль­ний сту­пінь ви­я­ву го­ло­су, йо­го нап­ру­же­
> ність (най­час­ті­ше по­си­лю­ють го­лос у реп­лі­ках, особ­
> ли­во в ок­лич­них ре­чен­нях)
> ха­рак­тер­не за­бар­влен­ня, зав­дя­ки яко­му лю­ди­на 
> го­во­рить ні­би різ­ни­ми го­ло­са­ми
> чіт­ка ви­мо­ва з

## Я, ти, він/вона (Persons)

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

> **Source:** unknown, Gr

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Перша дієвідміна (Group I Verbs)` (~300 words)
- `## Я, ти, він/вона (Persons)` (~300 words)
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

**Required:** читати (to read), знати (to know), працювати (to work), слухати (to listen), гуляти (to walk), готувати (to cook)
**Recommended:** робити (to do — Group II, preview as chunk), вивчати (to study/learn), малювати (to draw), грати (to play), вечеря (dinner, f), музика (music — review from M15)

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
