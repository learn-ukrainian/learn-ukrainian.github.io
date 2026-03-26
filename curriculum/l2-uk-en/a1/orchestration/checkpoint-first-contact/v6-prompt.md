<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Missing 1/1 required vocab: All vocabulary from M01-M06 is recycled — no new required words
- NOTE: Latin characters mixed with Cyrillic: r, f, O
- NOTE: Plan expects 3 exercise(s) but content has 0 placeholders
</correction_directive>

LEARNINGS FROM PAST BUILDS (same error patterns seen before):
- [GLOBAL] сес-тра is a VALID word division per Правопис 2019 §49. Do NOT mark it as an error. Phonetic syllabification (се-стра) and typographic word division (сес-тра) follow different rules — both are correct in their respective contexts.
- [GLOBAL] Ukrainian textbooks teach a hands-on-EARS test for voicing (закрий долонями вуха), NOT a hand-on-throat test. The hand-on-throat test is a valid phonetics technique but must NOT be attributed to Ukrainian textbooks. Source: Кравцова 2019, Grade 2, p.39.
- [GLOBAL] Do NOT invent Ukrainian words for minimal pairs. "Сір" is NOT a word meaning "grey" — the correct form is "сірий". Use verified minimal pairs only: кит/кіт, бити/біти, лис/ліс.
- [GLOBAL] NEVER frame Ukrainian as "lacking" or "missing" letters that Russian has. Ukrainian has its own 33-letter alphabet — it is complete. Do NOT write "Ukrainian lacks Ъ, Ы, Э" or "Ukrainian doesn't have these Russian letters." Instead, highlight what Ukrainian HAS: Ґ, Є, Ї, І are unique to Ukrainian. Present Ukrainian on its own terms.
- [GLOBAL] NO LLM filler phrases. Do NOT write: "Let us start with...", "Numbers unlock the real Ukraine", "You now possess a complete...", "It is incredibly versatile", "one of the most rewarding skills". Start sections with a dialogue, a question, or a concrete example — never with a generic motivational opener. If a sentence could appear in any language course about any topic, delete it.
- [GLOBAL] Every exercise item must test something EXPLICITLY taught in the preceding prose. If an exercise tests the collocation "малювати картину", the prose must contain "малювати картину" as a taught example. Do NOT test collocations, vocabulary, or patterns that the learner has to infer — test what was taught.
- [GLOBAL] Quiz correct answers must be RANDOMIZED across positions. Do NOT place the correct answer at index 0 for all items. Distribute correct answers roughly evenly across all positions (0, 1, 2) to prevent pattern-guessing.
- [GLOBAL] Do NOT use spatial metaphors for abstract grammatical requirements. Example: "на" with musical instruments is NOT "on top of" — it is an abstract grammatical requirement that must be memorized. Misleading mnemonics cause incorrect generalizations. If a rule must simply be memorized, say so directly.

# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **7: Checkpoint: First Contact** (A1, A1.1 [Sounds, Letters, and First Contact]).

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
5. **Place exercise markers only** — do NOT write exercises directly. Place `<!-- INJECT_ACTIVITY: {id} -->` markers where exercises should appear. A separate pipeline step generates the actual exercises from the plan's activity_hints.
6. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
7. **Hit the word target** — you MUST write 1200–1800 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
8. **NO archaic, obsolete, or rare words** — use only modern standard Ukrainian. Do not use words marked as archaic (застаріле) or dialectal in dictionaries. Example: use «кін» not «кон», use «пом'якшені» not «м'якшені». When in doubt, choose the common modern form. Your pre-training contains Russian-influenced archaic forms — verify unfamiliar words.

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
module: a1-007
level: A1
sequence: 7
slug: checkpoint-first-contact
version: '1.1'
title: 'Checkpoint: First Contact'
subtitle: Can you read, greet, and introduce yourself?
focus: review
pedagogy: PPP
phase: A1.1 [Sounds, Letters, and First Contact]
word_target: 1200
objectives:
- Demonstrate ability to read Ukrainian Cyrillic fluently
- Hold a complete first conversation (greet → introduce → family)
- Self-assess knowledge of sounds, letters, greetings, introductions
- Combine all A1.1 skills in connected speech
content_outline:
- section: Що ми знаємо? (What Do We Know?)
  words: 200
  points:
  - 'Self-check covering M01-M06: Can you read any Ukrainian word? (M01-M02) Do you
    know what Ь and apostrophe do? (M03) Can you place stress correctly? (M04) Can
    you introduce yourself? (M05) Can you talk about your family? (M06)'
- section: Читання (Reading Practice)
  words: 250
  points:
  - 'A short Ukrainian text (8-10 sentences) using ONLY vocabulary from M01-M06. No
    new words. The learner reads aloud. Content: A person introduces themselves, describes
    family, mentions professions, says where from.'
  - Following Anna Ep10 'Я і моя сім'я' review pattern.
- section: Граматика (Grammar Summary)
  words: 200
  points:
  - 'Key patterns from A1.1: 1. Це + noun (identification) 2. Subject — Noun (no ''is''):
    Я — студент 3. У мене є + noun (possession) 4. Як тебе/вас звати? (asking names)
    5. Мій/моя/моє + noun (possession with gender) 6. Звідки ти? — Я з... (origin
    as chunk)'
- section: Діалог (Capstone Dialogue)
  words: 400
  points:
  - 'The Full Introduction — comprehensive dialogue combining EVERYTHING from A1.1.
    Setting: meeting someone new. Full cycle: greeting → name → origin → profession
    → family → showing photos → goodbye. If learner can follow and produce this dialogue,
    A1.1 is complete.'
  - 'Connected monologue: learner''s own self-introduction. Привіт! Мене звати [name].
    Я [nationality]. Я — [profession]. Моя мама — [profession]. Мій тато — [profession].
    У мене є [family]. This is the A1.1 graduation speech.'
- section: Підсумок — Summary
  words: 150
  points:
  - 'Final self-check questions: How many letters/sounds in Ukrainian? Say hello formally
    and informally. Introduce yourself in 5 sentences. Name your family members with
    possessives.'
vocabulary_hints:
  required:
  - All vocabulary from M01-M06 is recycled — no new required words
  recommended:
  - ім'я (first name)
  - прізвище (surname)
activity_hints:
- type: quiz
  focus: 'Comprehensive review: sounds, letters, greetings, family'
  items: 12
- type: fill-in
  focus: Complete the full self-introduction monologue
  items: 8
- type: match-up
  focus: Match questions with answers (Як звати? → Мене звати...)
  items: 8
connects_to:
- a1-008 (Things Have Gender)
prerequisites:
- a1-006 (My Family)
grammar:
- 'Review: Це + noun, Subject — Noun, У мене є, possessives'
- No new grammar — consolidation only
register: розмовний
references:
- title: ULP Season 1, Episode 10 — Review 1-9
  url: https://www.ukrainianlessons.com/episode10/
  notes: Anna's connected self-introduction review pattern.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Checkpoint: First Contact
**Module:** checkpoint-first-contact | **Phase:** A1.1 [Sounds, Letters, and First Contact]
**Textbook grades searched:** 1, 2

---

## Що ми знаємо? (What Do We Know?)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 73
> 	 — Але ми все одно будемо дружи-
> ти? Адже ми обидва їжаки.
> 	 — Авжеж. Будемо (за Юрієм  Яр-
> мишем).
> 	 Прочитай заголовок казки. Що він тобі підка-
> зав? Хто з ким познайомився? 
> 	 Що любив слухати Їжак, який жив на гірці? 
> Що любив слухати Морський Їжак? Чому 
> вони любили різні звуки? 
> Повторюємо разом
> Абетка. Звуки та букви
> 	 Звуки, які любили їжаки, є мовні чи немовні?
> 	 Як називаємо підкреслені слова? 
> протилежні за значенням
> подібні за значенням
> 	 Перепиши перше речення. Підкресли букви,

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> 101
> Зразок. Барвінок, клен, ніч. 
> 2.	 Виконайте завдання на вибір.
> 	 Напишіть два слова, що відповідають на питання хто? і два 
> слова, що відповідають на питання що?
> 	 Складіть і запишіть речення з двома іменниками, поєднайте 
> їх службовими словами.
> 361. 1.	 Відгадай загадку.
> На зріст маленька 	 І у лісі в холодку
> пташка сіренька. 	
> все кує: «Ку-ку! Ку-ку!»
> 2.	 Виконай завдання на вибір.
> 	 Випиши прикметники до слова-відгадки.
> 	 Добери і запиши дієслова до слова-відгадки.
> 362. 1.	 Прочитай текст

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 50
> 	
> Що тобі відомо про героїнь казки «Дві білки»? 
> 	
> Розглянь малюнки. Дай відповідь на питан-
> ня: що робить?
> 	
> Визнач, якому слову — назві намальованого 
> предмета відповідає кожна схема.
> [ =•|–•|–• ] 
> [ –•|=•= ] 
> [ =•–|– •–] 
> 	 Назви слова, які відповідають схемам.
> [ –•| – •| =•]
> [ – –•| = •]
> [ –    –•| –•| = •]
> Що робить?
> Pidruchnyk.com.ua

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> 50
> 179. 1.	 Гра «Відшукай слово». «Перестрибуючи» через одну 
> літеру, прочитай слово.
> 2.	 Знайди в тлумачному словнику значення слова диван.
> 180. 1.	 Прочитай текст. Що нового ти дізнався (дізналася)?
> Ми розмовляємо українською мовою. А мова скла-
> дається зі слів. Слова можуть передати думки й почуття. 
> Словом можна назвати предмет, ознаку, дію предмета. Кожне 
> слово має своє значення. Значення 
> слова — це той зміст, який вклали в 
> нього люди. 
> Що краще ми знаємо і розу-
> міємо значення слова, то

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> ЦІКАВИНКИ ЗВІДУСІЛЬ
> Навчися швидко читати слова.
> світлофор 
> пофарбований 
> використовували
> залізничники 
> звичайний 
> відрізнялися
> • Прочитай заголовок твору. Про що, на твою думку, ітиметься в 
> тексті?
> • Попрацюйте разом. Заповніть таблицю (на аркуші).
> Прочитай.
> Світлофор
> Ми вже 
> знаємо
> Хочемо 
> дізнатися
> Де можна знайти 
> інформацію
> З ІСТОРІЇ СВІТЛОФОРА
> Прародичами* світлофорів були звичайні прапорці. їх 
> використовували залізничники, коли керували рухом поїздів. 
> Таких прапорців було... Ану, здога

> **Source:** unknown, Grade 1
> **Score:** 0.25
>
> 47
> Осінь  килим  вишивала,
> Ниточок  пішло  чимало —
> Лис-тя  кле-на  і  ка-ли-ни,
> Ду-ба,  я-се-на,   ма-ли-ни,
> А  між  ни-ми  го-ро-би-на —
> На-че  по-лу-м’я  го-рить!
>                                                 Юлія Ференцева ма
> ом
> му
> мо
> ом
> им
> ми
> [ –•= | –•]
> ми-
> мо-
> ми-
> Що?                               Що робити?
> 	 Визнач, якому слову — назві предмета від-
> повідає схема. 
> 	 Розкажи, для чого використовують ці пред-
> мети.
> Pidruchnyk.com.ua

## Читання (Reading Practice)

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
> **Score:** 0.33
>
> 70
> Мої навчальні досягнення. Я вмію, можу
> * * *
> Прибрав ліжко САМ. 
> Зробив зарядку САМ. На 
> кухні  САМ поставив на 
> стіл чашку. Після снідан-
> ку САМ помив посуд.
> * * *
> А ... притулився до 
> мами й подумав: «Не-
> має нічого кращого, ніж 
> обійми моєї матусі. Ось 
> воно, щастя!»  
> * * *
> — Якщо ліс знову ста-
> не чистим, то й Лісовуня 
> буде гарною! — сказав 
> … .
> 	
> Пригадай історії, які ти прочитав / прочита-
> ла. Визнач, якому малюнку відповідає кож-
> ний уривок із тексту.
> Pidruchnyk.com.ua

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> Інна Большакова
> Марина Пристінська
> УКРАЇНСЬКА МОВА
> ТА ЧИТАННЯ
> ЧАСТИНА 1
> 2 
> КЛАС
> ї
> о
> н
> А
> М

> **Source:** unknown, Grade 1
> **Score:** 0.25
>
> 3
> Дорогий друже!
> Ти продовжуєш подорож чудовим сві-
> том рідної мови. Адже ти любиш читати, 
> спілкуватися, фантазувати. 
> Ця книга допоможе тобі навчитися 
> читати, висловлювати думки й почуття, 
> спілкуватися.
> Умовні позначення:
> 	
> 	 — читаю
> 	
> 	 — обговорюю малюнок
> 	
> 	 — досліджую мовлення
> 	
> 	 — мислю критично

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

## Граматика (Grammar Summary)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 4
> Я ВИВЧАЮ УКРАЇНСЬКУ МОВУ
> Ми живемо в Україні. Наша мова — українська. 
> Ми будемо вчитися говорити, читати й писати українською. 
> Я читаю 
> українською.
> Я пишу 
> українською.
> Я слухаю 
> українську.
> Я говорю 
> українською.
> Я вітаюсь і знайомлюсь. 
> 1
> Доброго ранку!
> Мене звати Ганна.
> Привіт! Я Тарас. 
> Будемо вчитися разом.
> Будемо дружити!

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> ■мИ|28| Змініть подані слова за зразком і запишіть.
> навчати — навчання_ >
> Розкажи про свої 
> успіхи в навчанні.
> читати 
> міркувати 
> додавати 
> малювати 
> бажати 
> уміти
> • Поясніть, що називають записані слова. На які питання вони 
> відповідають? Усно складіть речення з однією парою слів 
> (на вибір).
> 29 Заміни сполучення слів за зразком і запиши.
> Книжка з бібліотеки — ? 
> Шафа для книжок — ?
> Вистава в театрі — ?
> Гра на комп'ютері — ?
> розм°ва по телефону — телефонна розмова
> • Запиши утворені сполучення с

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 16
> Й й
> Бачу Й, й (йот). Чую  [й].
> а й в а
>  [ •  =   |  –• ]
> а й с т р и
> * а й в о р о
> а
> о
> и
> і
> Й
> га
> ми
> рі
> Й
> н о к
> лій- 
> 	
> ліній-
> 	
> май- 
> чай- 
> 	
> гай- 
> 	
> чай- 
> мий	
> лий 	
> чай	
> грай
> вимий	
> долий	
> чайник	
> зіграй
> ай
> ой
> ий
> ій
> а
> о
> і
> і
> ч
> й
> д
> м
> й
> Pidruchnyk.com.ua

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> 12
> сЛова — назви ПреДметІв
> Слова — назви предметів — це іменники.
> Слово іменник утворене від слова ім’я. Кожний 
> предмет чи явище має своє ім’я, тобто свою назву.  
> Назви зображені предмети спочатку окремо, потім одним 
> словом. 

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Що ми знаємо? (What Do We Know?)` (~200 words)
- `## Читання (Reading Practice)` (~250 words)
- `## Граматика (Grammar Summary)` (~200 words)
- `## Діалог (Capstone Dialogue)` (~400 words)
- `## Підсумок — Summary` (~150 words)
- `## Підсумок — Summary` (~150 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 10-20% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose. Introduce Ukrainian grammar terms bolded with translation on first use.
- UKRAINIAN CONTENT: Words and short phrases bolded inline: "The word **книга** (book) is feminine."
- TABLES: Vocabulary tables, word families, simple paradigm tables.
- STRUCTURAL RULE: Every paragraph is English. Ukrainian words/phrases appear inline bolded. Full Ukrainian sentences (3+ words with a verb) go in tables or bulleted example lists with English gloss.
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

**Required:** All vocabulary from M01-M06 is recycled — no new required words
**Recommended:** ім'я (first name), прізвище (surname)

### Pronunciation Videos



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
## Що ми знаємо? (What Do We Know?) (~220 words total)
- P1 (~60 words): Opening frame — you've completed six modules covering the Ukrainian alphabet, soft sign & apostrophe, stress, greetings, and family. This checkpoint tests whether you can combine all these skills in connected speech. No new words — everything here comes from M01-M06.
- P2 (~80 words): Self-check list presented as questions the learner answers honestly. Six items, one per module: (1) Can you read any Ukrainian word aloud? (M01-M02) (2) Do you know what ь does in день, сіль and what the apostrophe does in сім'я, м'який? (M03) (3) Can you find the stressed syllable in мáма, студéнт, Украї́на? (M04) (4) Can you say Привіт, Мене звати..., Я з...? (M05) (5) Can you name family members with мій/моя/моє? (M06)
- P3 (~80 words): Brief guidance on how to use this checkpoint — read aloud, try the dialogue from memory before checking, treat it as a self-assessment not a test. If any area feels weak, revisit that module before continuing to M08. Frame: Це не іспит — це дзеркало (This isn't a test — it's a mirror).

## Читання (Reading Practice) (~280 words total)
- P1 (~30 words): Brief instruction — read the following text aloud. Every word comes from M01-M06. Focus on pronunciation, stress, and smooth reading. No new vocabulary.
- P2 (~120 words): Connected Ukrainian reading passage (8-10 sentences). A person introduces themselves and their family. Content: Привіт! Мене звати Оксана. Я — студентка. Я з Києва. Моя мáма — лікарка. Мій тáто — інженер. У мене є брат. Його звати Тарас. Він — учень. Моя сім'я — невелика, але дружна. Following the Anna Ep10 "Я і моя сім'я" review pattern — one person, full introduction cycle. Uses textbook pattern from Grade 1: "Мене звати Ганна. Привіт! Я Тарас."
- P3 (~50 words): Comprehension check — three simple questions about the passage in English: What is Оксана's profession? What does her father do? How many people are in her family? Purpose: verify the learner understood, not just decoded sounds.
- P4 (~80 words): Pronunciation spotlight — highlight 3-4 words from the passage that test A1.1 skills: сім'я (apostrophe before я), звати (cluster зв-), невелика (stress on -ли́-), інженер (soft н before е). Remind the learner these aren't new — they practiced each pattern in M01-M04. Connect sounds to letters to meaning.

## Граматика (Grammar Summary) (~220 words total)
- P1 (~40 words): Frame — these are the six key patterns you've learned. You don't need to memorize rules — you need to recognize and produce these structures automatically. Each pattern gets one example you already know.
- P2 (~30 words): Pattern 1 — Це + noun (identification). Це мáма. Це брат. Це Украї́на. No verb "is" needed.
- P3 (~30 words): Pattern 2 — Subject — Noun (no "is"). Я — студéнт. Вона́ — лікарка. Тарáс — учéнь. The dash replaces English "is."
- P4 (~30 words): Pattern 3 — У мéне є + noun (possession). У мене є брат. У мене є сім'я. Ukrainian says "by me there is," not "I have."
- P5 (~30 words): Pattern 4 — Як тебé/вас звáти? (asking names). Informal: Як тебе звати? — Мене звати Оксана. Formal: Як вас звати? — Мене звати Іван.
- P6 (~30 words): Pattern 5 — Мій/моя́/моє́ + noun (possessives with gender). Мій тáто (masculine). Моя́ мáма (feminine). Моє́ ім'я́ (neuter). Gender determines which form.
- P7 (~30 words): Pattern 6 — Звідки́ ти? — Я з... (origin). Я з Києва. Я з Канади. Learned as a chunk — full grammar of з + genitive comes later.

## Діалог (Capstone Dialogue) (~440 words total)
- P1 (~40 words): Setup — this is the A1.1 final dialogue. It combines every skill from M01-M06 into one natural conversation. Setting: two people meet for the first time at a мовний клуб (language club). Read both roles aloud.
- P2 (~120 words): The Full Introduction dialogue (10-12 turns). Андрій and Софія meet. Full cycle: greeting (Привіт! / Добрий день!) → names (Як тебе звати? / Мене звати...) → origin (Звідки ти? / Я з Львова. А ти? / Я з Торонто.) → profession (Я — програміст. А ти? / Я — вчителька.) → family (У тебе є сім'я? / Так, у мене є мама, тато і сестра.) → showing a photo (Це моя сестра. Її звати Марія.) → goodbye (Дуже приємно! До побачення! / Бувай!).
- P3 (~60 words): Dialogue analysis — point out how the conversation flows naturally. Highlight: informal register (ти, Привіт, Бувай), question-answer pairs, how each pattern from the grammar section appears in context. Note the echoing structure: А ти? / А ви? — Ukrainian conversations mirror questions back naturally.
- Exercise: match-up — Match questions with their answers (Як тебе звати? → Мене звати Софія; Звідки ти? → Я з Львова; У тебе є брат? → Так, у мене є брат), 8 items drawing from the dialogue.
- P4 (~40 words): Transition to monologue — now it's your turn. Instead of a dialogue with two people, produce a connected self-introduction. This is your A1.1 graduation speech — everything you can say about yourself in Ukrainian.
- P5 (~100 words): Model monologue with fill-in gaps for personalization. Template: Привіт! Мене звати ___. Я з ___. Я — ___. Моя мáма — ___. Мій тáто — ___. У мене є ___. Його/Її звати ___. Моя сім'я — ___. Дуже приємно! Present a completed example first (using a character like Олéна from Відня, who is a студéнтка with мáма-лікарка and тáто-інженéр), then the template for the learner.
- Exercise: fill-in — Complete the self-introduction monologue with appropriate words (8 items — name, city, profession, family members, possessives).
- P6 (~80 words): Speaking guidance — say your monologue aloud three times. First time: read from the template. Second time: glance only when stuck. Third time: from memory. If you can do the third round, you've graduated A1.1. Remind: stress matters (студéнт not стýдент), apostrophe matters (сім'я not сімя), soft sign matters (день not ден).

## Підсумок — Summary (~160 words total)
- P1 (~80 words): Four final self-check questions: (1) How many letters are in the Ukrainian alphabet? (33) How many sounds? (38) (2) Say hello formally and informally. (Добрий день / Привіт) (3) Introduce yourself in five sentences — name, origin, profession, one family member, goodbye. (4) Say мій, моя, моє with a family member for each gender.
- P2 (~80 words): Encouragement and forward look — if you answered all four, you're ready for A1.2 where Ukrainian gets its first real grammar: grammatical gender (M08). Everything so far has been chunks and patterns. Starting next module, you'll understand WHY it's моя мáма but мій тáто. Preview: Речі мають рід (Things Have Gender).
- Exercise: quiz — Comprehensive 12-item review covering sounds/letters (How many голосні звуки?), greetings (formal vs informal), family vocabulary (translate: sister, brother, grandmother), possessives (мій/моя/моє selection), stress placement, apostrophe and soft sign identification.

Grand total: ~1320 words
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
