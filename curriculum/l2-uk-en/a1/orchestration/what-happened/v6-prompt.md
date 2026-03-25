# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **48: What Happened?** (A1, A1.8 [Past, Future, Graduation]).

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
module: a1-048
level: A1
sequence: 48
slug: what-happened
version: '1.2'
title: What Happened?
subtitle: Він читав, вона читала — past tense with gender
focus: grammar
pedagogy: PPP
phase: A1.8 [Past, Future, Graduation]
word_target: 1200
objectives:
- Form past tense of verbs for all genders and plural (він читав, вона читала, воно
  читало, вони читали)
- Recognize that Ukrainian past tense marks GENDER, not person
- Use past tense to describe completed actions in simple sentences
- Ask and answer "What did you do?" (Що ти робив/робила?)
content_outline:
- section: Dialogues
  words: 300
  points:
  - 'Dialogue 1 — What did you do yesterday? — Що ти робив учора? — Я читав книжку.
    А ти? — Я готувала вечерю. — А що робив Тарас? — Він гуляв у парку. — А Олена?
    — Вона працювала. Note gender: робив (he), робила (she). Same verb, different
    ending.'
  - 'Dialogue 2 — A weekend: — Як ти провів вихідні? — Добре! У суботу я гуляв у місті.
    — А в неділю? — У неділю я дивився фільм. А ти? — Я ходила в кафе з подругою.
    Ми їли торт і пили каву. — Як смачно! Past tense in natural narration.'
- section: Минулий час (Past Tense)
  words: 300
  points:
  - 'Grade 3-4 textbooks: минулий час (past tense). How to form it: take the infinitive,
    remove -ти, add: він → -в (читати → читав) вона → -ла (читати → читала) воно →
    -ло (читати → читало) вони → -ли (читати → читали) KEY INSIGHT: past tense shows
    GENDER, not person! Я читав = I (male) was reading. Я читала = I (female) was
    reading. Same person (я), different gender ending.'
  - 'This is different from present tense (which marks person): Present: я читаю,
    ти читаєш, він читає (person endings). Past: я/ти/він читав, я/ти/вона читала
    (gender endings). Він працював. Вона працювала. Воно працювало. Вони працювали.
    No aspect distinction at A1 — just learn the forms.'
- section: Практика (Practice)
  words: 300
  points:
  - 'Core verbs in past tense (all known from A1.3): читати → читав / читала / читало
    / читали працювати → працював / працювала / працювало / працювали гуляти → гуляв
    / гуляла / гуляло / гуляли готувати → готував / готувала / готувало / готували
    дивитися → дивився / дивилася / дивилося / дивилися говорити → говорив / говорила
    / говорило / говорили'
  - 'Building sentences about the past: Учора я читав цікаву книжку. (Yesterday I
    read an interesting book.) Вона працювала в офісі. (She worked in the office.)
    Ми гуляли в парку. (We walked in the park.) Вони готували вечерю разом. (They
    cooked dinner together.) Time words for past: учора (yesterday), минулого тижня
    (last week).'
- section: Summary
  words: 300
  points:
  - 'Past tense formation: Infinitive stem + -в (він), -ла (вона), -ло (воно), -ли
    (вони). Gender matters: Я читав (male speaker). Я читала (female speaker). Вони
    завжди -ли (plural = no gender distinction). Question: Що ти робив/робила? (What
    did you do?) Answer: Я читав/читала книжку. Self-check: Tell your partner what
    you did yesterday using 3 different verbs.'
vocabulary_hints:
  required:
  - учора (yesterday)
  - робити (to do)
  - читати (to read)
  - працювати (to work)
  - гуляти (to walk)
  - готувати (to cook)
  - дивитися (to watch)
  - говорити (to speak)
  recommended:
  - минулий (past, adj)
  - вихідні (weekend, pl)
  - субота (Saturday, f)
  - неділя (Sunday, f)
  - разом (together)
  - фільм (film, m)
  - провести (to spend time)
activity_hints:
- type: fill-in
  focus: Form past tense (він / вона / вони) for all core verbs
  items:
  - Учора він {читав|читала|читати} книжку.
  - Олена {готувала|готував|готували} вечерю.
  - Ми {гуляли|гуляв|гуляла} в парку.
  - Вони {працювали|працював|працювало} разом.
  - Тарас {дивився|дивилася|дивилися} фільм.
  - Що ти {робив|робила|робили} учора, Іване?
- type: matching
  focus: Match pronoun to the correct past tense ending
  pairs:
  - він: працював
  - вона: працювала
  - воно: працювало
  - вони: працювали
  - Тарас: говорив
  - Олена: говорила
- type: fill-in
  focus: Choose correct gender based on the subject
  items:
  - Марія {дивилася|дивився|дивилися} фільм.
  - Мій брат {гуляв|гуляла|гуляли} у парку.
  - Вони {провели|провів|провела} вихідні разом.
connects_to:
- a1-049 (Yesterday)
prerequisites:
- a1-047 (Checkpoint — Communication)
grammar:
- 'Past tense (минулий час): gender-based endings -в, -ла, -ло, -ли'
- Past tense marks gender, not person (unlike present tense)
- 'Formation: infinitive stem + gender ending'
- 'Question: Що ти робив/робила?'
register: розмовний
references:
- title: State Standard 2024, §4.2.4.1
  notes: Past tense — gender agreement in verb forms.
- title: 'Grade 3-4 textbook: Минулий час'
  notes: 'Past tense formation: -в, -ла, -ло, -ли endings.'
- title: ULP Season 1, Episodes 26-27
  url: https://www.ukrainianlessons.com/episode26/
  notes: Past tense verbs and narrating events.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: What Happened?
**Module:** what-happened | **Phase:** A1.8 [Past, Future, Graduation]
**Textbook grades searched:** 5, 6, 7

---

## Dialogues

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

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> Поміркуй над прочитаним
>  
> 1. Чи погоджуєшся з думкою: «Нестерпно було в такий теплий 
> весняний день сидіти на уроках, хотілося гайнути на ста-
> ренькому велосипеді кудись за місто, а то й просто поганяти 
> м’яча»? Чому?
>  
> 2. Дофантазуй, чому новенька прийшла до класу навесні.
>  
> 3. Яка деталь пейзажу притаманна всьому твору? Яка її роль?
>  
> 4. Яка деталь у зовнішності Терези вразила Ігоря? Чому він 
> уважає дівчину дивною?
>  
> 5. Чому Тереза ніяковіла?
>  
> 6. Чому Ігоря Чалагу називають тяжким підлітком?

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> 194
> 1.	Прочитайте текст (одне слово пропущено) і виконайте завдання.
> Як я малим збирався …	
> Сорочку мати вишила мені
> Піти у світ незнаними шляхами,	
> Червоними і чорними нитками.
> Д. Павличко
> А.	 Розгадайте ребус і вставте на місці пропуску прислівник-відгадку.
> Б.	 Визначте розряд прислівника за значенням (усно).
> 2.	 Прочитайте речення з пропущеними словами та виконайте завдання.
> 1. Турн сили (скільки?) … прикладає, і тарани сам направляє, і браму 
> рушити велить (І. Котляревський). 2. Він [мул] тя

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 226
> 515   Прочитайте тексти. Визначте наміри мовців. Розподіліть ролі 
> і прочитайте тексти виразно.
> — Дай Боже щастя, 
> дідусю!
> — Дякую, внучку! Дай 
> Боже і тобі!
> — Зашпиліть куртку, 
> бо застудитеся. Сьогодні 
> холодно. І не нудно вам 
> отут 
> так 
> замітати? 
> Щодня одне й те саме.
> — 
> Ні, 
> хлопчику, 
> я люблю свою роботу. 
> Подивися, яка чудова 
> осінь. Яке гарне барвис-
> те 
> листя, 
> як 
> твій 
> портфель. 
> Уяви 
> собі, 
> що в світі нема двох 
> однакових листочків, як 
> і людей. Господь кожно-
> го створив неповт

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> Я навіть не встиг запитати, що вона мала на увазі.
> Відверто кажучи, дівчина мені страшенно сподобалася. 
> Навіть тим, що спочатку я прийняв її за хлопця. Вона 
> не була схожою на моїх однокласниць. Якщо я тут залишуся 
> надовго, як планував, ми справді ще побачимося. Настрій мій 
> покращився, і я попрямував шукати обійстя бабусі й дідуся.
> Хоча не дуже добре пам’ятав, де воно. Багато часу минуло…
> Поміркуй над прочитаним
>  
> 1. Як ти оцінюєш учинок Арсена, який без дозволу мами вирішив 
> поїхати до села?

> **Source:** unknown, Grade 7
> **Score:** 0.33
>
> 221
> 221
> ПОПРАЦЮЙТЕ В ПАРАХ. Складіть і запишіть діалог (5–6 реплік), 
> використовуючи всі подані вигуки. Розіграйте діалог 
> за особами. На добраніч, вибач, отакої, овва, до побачен-
> ня, будь ласка, перепрошую. НАПРИКЛАД:
> О
> Ой
> Ну
> Ох
> Ах
> І. Прочитайте виразно речення. Визначте, до яких частин мови на ле-
> жать виділені слова. Поясніть наявність чи відсутність коми після цих слів. 1. Ой, що се? Світло згасло? Ніч настала? (Леся Українка). 2. Ой біжи, біжи, досадо, не вертай до хати, не пущу тебе колис

## Минулий час (Past Tense)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 187
> 437   І   Прочитайте текст мовчки. Якщо в ньому є нові для вас сло-
> ва, випишіть їх. Пригадайте, у яких джерелах можна знайти 
> інформацію про значення цих слів.
> Читати й писати людство навчилося якихось 5000 років 
> тому, натомість бігати, полювати, спілкуватися із собі подіб-
> ними за допомогою звуків і жестів — уже сотні тисячоліть.
> Робота мозку під час читання розгортається в кілька ета-
> пів. Що краще розвинена навичка читання, то швидше ми 
> розкодовуємо і розуміємо текст. Однак прискорення

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> В. Прочитайте текст удруге й докладно його перекажіть (усно).

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> 63
> 63
> Зверніть увагу! Інколи в значенні минулого часу спеціально вживають діє-
> слова у формі теперішнього часу. У таких випадках теперішній 
> час надає розповіді більшої виразності та є засобом наближення 
> подій минулого до слухачів / слухачок. НАПРИКЛАД: Заходжу
> я минулої середи в кімнату й бачу диво. І. Прочитайте уривок із повісті Андрія Бачинського «140 децибелів тиші» 
> про юного музиканта, який утратив слух під час автокатастрофи. Поміркуйте, чи 
> допоможе музика Сергію та його названій сестр

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 165
> 391   Прочитайте текст. Поясніть, як ви розумієте зміст останнього 
> речення. Визначте основну думку тексту. Випишіть ключові 
> слова. Розкажіть про свою улюблену пору року (усно).
> Довго я не любив осені. У нас із нею були вельми неприємні 
> стосунки. Надто вже набридливою бачилася вона мені, надто 
> вже тиснула — приходить у самісінький розпал веселощів, 
> коли здається, що літо ніколи не скінчиться…
> Тоді я відчайдушно любив літо, жодна інша пора не здава-
> лася такою доброю і близькою. Тоді я ін

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> ви. Не могли вони таку малу дитину надовго кинути. Давай 
> краще чкурнемо звідси. (…)
> Ми не стали баритися. Шугонули вниз і кинулися навтікача. Бігти було важко, 
> бо доісторична трава була густа, висока й колюча. Але коли 
> вам загрожує небезпека й ви тікаєте, то думати про те, щоб 
> бігти було зручно й приємно, не доводиться. Коли ми вже зовсім захекались і відчули, що погоні нема, 
> ми спинилися й сіли перепочити під кущем якоїсь гігантської 
> папороті. (…)
> Поміркуй над прочитаним
>  
> 1. Чому уявні п

> **Source:** unknown, Grade 7
> **Score:** 0.33
>
> З ним була… його київ-
> ська Іринка. Ішли бадьоро, сміючися і перекидаючися новеньким фут-
> больним м’ячем.

## Практика (Practice)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 187
> 437   І   Прочитайте текст мовчки. Якщо в ньому є нові для вас сло-
> ва, випишіть їх. Пригадайте, у яких джерелах можна знайти 
> інформацію про значення цих слів.
> Читати й писати людство навчилося якихось 5000 років 
> тому, натомість бігати, полювати, спілкуватися із собі подіб-
> ними за допомогою звуків і жестів — уже сотні тисячоліть.
> Робота мозку під час читання розгортається в кілька ета-
> пів. Що краще розвинена навичка читання, то швидше ми 
> розкодовуємо і розуміємо текст. Однак прискорення

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> Музей мистецтва Метрополітен 
> у  Нью-Йорку (США). rnk.com.ua/104220
> Практичне заняття
> Підручник  
> Видавництво «Ранок»

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> § 9  Часи діє слова  
> 41
> Вправа 52
> 1   Розподіліть запропоновані форми діє слів за числами та родами 
> Міркувала, міркували, міркувало, міркував; виграв, ви­
> грали, виграло, виграла; змогли, змогла, зміг, змогло; свис­
> нув, свиснуло, свиснули, свиснула; вдихнула, вдихнуло, вдих­
> нув, вдихнули.
> Однина
> Множина
> чоловічий рід
> середній рід
> жіночий рід
> 2   Виділіть суфікси та закінчення 
> Вправа 53
>  
> Доповніть речення, дібравши з довідки діє-
> слова й поставивши їх у потрібній формі роду 
> та числа минуло

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 185
> ЧИТАННЯ. ВИДИ ЧИТАННЯ. 
> МЕТА ЧИТАННЯ
> § 65
> Життєво важлива звичка — 
> читати щодня
> Книжки мають особливу чарівність, вони дають нам насолоду: 
> вони розмовляють з нами, дають добрі поради, стають живими друзями 
> (Ф. Петрарка).
> Слово дня: читàння, розкодувàння, уподобàння, с

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Dialogues` (~300 words)
- `## Минулий час (Past Tense)` (~300 words)
- `## Практика (Practice)` (~300 words)
- `## Summary` (~300 words)
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

GRAMMAR CONSTRAINTS (A1.8 — Past, Future & Graduation, M51-M60):
Full A1 grammar including past and future tense.

ALLOWED:
- Past tense (він читав, вона читала — gendered!)
- Future tense (я буду читати, ми будемо працювати)
- All cases, moods, and constructions from A1.1-A1.7
- Combining tenses in connected speech

BANNED: Participles, passive voice, complex literary constructions

### Vocabulary

**Required:** учора (yesterday), робити (to do), читати (to read), працювати (to work), гуляти (to walk), готувати (to cook), дивитися (to watch), говорити (to speak)
**Recommended:** минулий (past, adj), вихідні (weekend, pl), субота (Saturday, f), неділя (Sunday, f), разом (together), фільм (film, m), провести (to spend time)

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
