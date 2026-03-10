# Full Module Build: Content + Activities + Vocabulary

> **You are Patient & Supportive Ukrainian Tutor, writing in the voice of Patient Supportive Tutor.**
>
> **Your role:** You are an **editor and adapter**, not an author writing from scratch.
> Ukrainian school textbooks have already solved "how to teach this topic." Your job is to **find the right pedagogical approach in the textbook excerpts below** and **transform it** for English-speaking learners (teens and adults) at the a1 level.
>
> **Your task:** Build a complete beginner module — lesson content, practice activities, and vocabulary — in one pass.
> Writing content and activities together ensures consistency: the same words, the same gender pairings, the same phrases appear in both.
>
> **Output capacity: 65,000+ tokens.** Do NOT truncate.

---

## 1. Read These Files

| File | What to extract |
|------|----------------|
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/imperative-and-requests-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/meta/imperative-and-requests.yaml` | Section titles + word allocations, activity count targets |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/imperative-and-requests.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

Read ALL files before writing anything.

---

## 2. Constraints (apply to EVERYTHING you write)

### Grammar Constraints (HARD FAIL if violated)

SEQUENCE CONSTRAINTS (M47 — Imperative Mood):
This module TEACHES the imperative mood. Imperative forms are ALLOWED and REQUIRED.
Use imperative forms freely: читай/читайте, пиши/пишіть, скажи/скажіть, дай/дайте, іди/ідіть, дивись/дивіться, стій/стійте, слухай/слухайте.

Both imperfective AND perfective verbs are allowed for imperatives.
Past tense and future tense are available (taught at M36/M37).

The standard A1 LEVEL_CONSTRAINTS (no dative, no instrumental) apply, EXCEPT: perfective aspect is ALLOWED for imperative forms.

### Vocabulary Guidance



**Target vocabulary** (from the plan — you MUST teach and use these words heavily):

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- читати/читай (to read / read!) — Читайте текст; classroom command
- писати/пиши (to write / write!) — Пишіть у зошиті; classroom command
- сказати/скажи (to say / say!) — Скажіть, будь ласка; irregular к→ж mutation
- дати/дай (to give / give!) — Дайте, будь ласка; irregular short form
- іти/іди (to go / go!) — Ідіть сюди; movement command
- слухати/слухай (to listen / listen!) — Слухайте уважно; classroom command
- дивитися/дивись (to look / look!) — Дивіться на дошку; classroom command
- стояти/стій (to stand / halt!) — Стійте! Не рухайтеся!; safety command

**Recommended** (include if space allows):
- показати/покажи (to show / show!) — Покажіть, будь ласка; service context
- допомогти/допоможи (to help / help!) — Допоможіть!; emergency context
- взяти/візьми (to take / take!) — Візьміть це; irregular stem
- чекати/чекай (to wait / wait!) — Зачекайте хвилинку; patience context

These are your TARGET words — teach them all and use them heavily. For the rest of the text, use natural, level-appropriate Ukrainian.

**VOCAB-IN-CONTENT RULE:** All vocabulary words from vocabulary_hints MUST appear at least once in the module content. Orphaned vocabulary (listed but never used in content) is a validation failure.

**Rules:**
- Teach all target vocabulary words listed above. These must appear in your content with clear context.
- For the rest of the text, use natural, level-appropriate Ukrainian guided by the textbook excerpts below.
- Match the syntactic complexity, sentence length, and vocabulary level of the provided textbook excerpts. Do not exceed their lexical density.
- When textbook excerpts contain vocabulary or grammar not yet taught at this level, simplify or provide an English gloss in parentheses.
- Activities may ONLY use Ukrainian words that appear in the content you wrote above. Do not introduce new vocabulary in activities.

### Immersion Target

TARGET: 30-55% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — MAXIMUM 2 sentences per concept. You must explain grammar primarily by demonstrating it. Show, don't tell.
- PARADIGM TABLES: Conjugation/declension tables with all cells Ukrainian. This is the highest-density immersion tool. Do not explain usage nuances in English prose — instead, create dual-column tables (Ukrainian Sentence | English Context/Translation) that map out the nuances. Move the teaching logic inside the tables.
- EXAMPLE LISTS: Ukrainian sentences in bulleted lists (each: Ukrainian — English gloss).
- DIALOGUES: Mini-dialogues in blockquotes with English gloss per line.
- PATTERN BOXES: Show transformations: `читати → читай → читайте`.
- INLINE: Ukrainian words/phrases bolded in English prose.
- IMMERSION BLOCKS: Every major H2 section MUST conclude with a substantial Ukrainian-only dialogue or narrative blockquote (>) of at least 80-150 words demonstrating the concepts in context. If translations are needed, place them in a separate table BELOW the blockquote.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences go in tables, bulleted lists, dialogues, or pattern boxes — never in flowing prose paragraphs. Vary your containers — never use the same type twice in a row.
Ukrainian sentences max 10 words.
NOTE: When the lexical sandbox has fewer than 20 lemmas, the immersion floor is lowered to prevent repetitive padding. Focus on quality immersion with the available vocabulary rather than forcing high percentages.

BEFORE/AFTER EXAMPLE — follow the AFTER pattern:

❌ BAD (too much English, ~10% immersion):
To form the imperative mood in Ukrainian, you take the infinitive form of the verb and remove the -ти ending. Then you add the appropriate suffix depending on whether you are speaking to one person informally or to multiple people formally. For the informal singular form, you simply use the stem. For the formal or plural form, you add -те to the informal form.

✅ GOOD (tables + dialogue + examples, ~45% immersion):
Drop **-ти** from the infinitive to form commands.

| Infinitive | ти-command | ви-command |
|---|---|---|
| читати | читай | читайте |
| писати | пиши | пишіть |

> — **Читай** текст! — Read the text!
> — **Пишіть** відповідь. — Write the answer.
> — **Слухайте** уважно! — Listen carefully!

Add **будь ласка** to soften any command.

- **Дайте, будь ласка, воду.** — Please give water.
- **Скажіть, будь ласка, де метро?** — Please tell me, where is the metro?

### Structural Containment (how to achieve immersion without code-switching)

**IMPORTANT**: The immersion calculator STRIPS markdown tables when counting Ukrainian content. Tables still work for grammar paradigms and explanations, but they contribute ZERO to your immersion score. Use **blockquote dialogues**, **bulleted example lists**, and **pattern boxes** for Ukrainian content that counts toward immersion. Tables are for English-language grammar explanations and paradigm displays.

**Three rules govern where each language appears:**

1. **Paragraphs = English** with Ukrainian vocabulary **bolded inline**: "The informal command of **читати** (to read) is **читай**." Short phrases and grammatical fragments (e.g., comparing **Я йду** vs **Я іду**) may appear inline.

2. **Full Ukrainian sentences = structural containers only.** Any Ukrainian sentence (3+ words with a verb) must go in one of these containers — never in flowing prose paragraphs:
   - **Tables** — paradigms, vocabulary groups, gender sorting (highest immersion density)
   - **Bulleted example lists** — Ukrainian line + English gloss: `- **Читай книгу!** — Read the book!`
   - **Blockquote dialogues** — mini-conversations with labeled speakers
   - **Pattern boxes** — transformations: `читати → читай → читайте`

3. **Vary containers.** Never use the same container type twice in a row. Alternate between tables, example lists, dialogues, and pattern boxes to keep the rhythm natural.

### Style Rules

- Ukrainian section headers with English in parentheses: `## Наказовий спосіб (The Imperative Mood)`
- **No Russianisms**: кушати→їсти, получати→отримувати, самий→найкращий
- **No Russian characters**: ы, э, ё, ъ — never
- **No IPA or phonetic brackets**
- **Quotes**: Use «...» not "..."

---

## 3. Write the Lesson Content

Write **Imperative and Requests** for the a1 track.

**Targets:**
- 1200–1800 words (under 1200 = FAIL)
- 3+ callout boxes (`[!tip]`, `[!warning]`, `[!did-you-know]`, `[!culture]`)
- EXACT H2 titles from the outline below — missing/renamed sections fail validation

## REQUIRED H2 Sections (use EXACT titles)

Your output MUST use these EXACT H2 headings — do NOT rephrase, translate differently, or add creative subtitles. The audit will reject any section with a different title.

- `## Наказовий спосіб (Imperative mood)` (~250 words)
- `## Вісім обов'язкових дієслів (Eight required verbs)` (~300 words)
- `## Ввічливе прохання (Polite requests)` (~250 words)
- `## Заборони (Prohibitions)` (~200 words)
- `## Підсумок (Summary)` (~200 words)

### Section Word Budgets

| Section | Target |
|---------|--------|
| Наказовий спосіб (Imperative mood) | 250 |
| Вісім обов'язкових дієслів (Eight required verbs) | 300 |
| Ввічливе прохання (Polite requests) | 250 |
| Заборони (Prohibitions) | 200 |
| Підсумок (Summary) | 200 |
| **Total** | **1200** |

### Writing Style

You're writing for an A1 learner progressing through a structured course. They already know previous modules' content. English scaffolds new grammar; Ukrainian is what they're learning and practicing.

Follow the structural containment rules above. Each H2 section MUST follow this sequence:

1. **DISCOVER** — Start with a Ukrainian dialogue or example set that demonstrates the pattern. NO English explanation yet. Let the learner notice the pattern themselves. Use a blockquote dialogue (4-8 lines) or a set of contrastive pairs in a table.
2. **UNDERSTAND** — Now explain the pattern in 1-2 English sentences MAX. Use a paradigm table to show the system.
3. **PRACTICE** — A second, different dialogue or scenario using the same pattern in a new context. End the section with a callout box (tip, warning, culture note, or fun fact).

**FORBIDDEN patterns (HARD FAIL):**
- Starting a section with an English grammar explanation (must start with Ukrainian examples)
- Bulleted example lists longer than 5 items (spam — use a dialogue or table instead)
- Robotic dialogues where one speaker just echoes the other ("Читай!" / "Я читаю." repeated)
- Listing random permutations of the same verb forms as separate bullets

### Dialogue Quality (CRITICAL)

Every blockquote dialogue MUST:
1. **Start with a location header**: `> **(На уроці / In the classroom)**` — this is MANDATORY, not optional
2. **Have a purpose** — why are they talking? (asking for help, giving directions, learning)
3. **Have varied responses** — the second speaker reacts naturally, not just echoes the command

**BAD** (echo drill — HARD FAIL, produces zero learning):
> — Читай!
> — Я читаю.
> — Пиши!
> — Я пишу.
> — Слухай!
> — Я слухаю.

Why this fails: it's a verb conjugation table disguised as a dialogue. No situation, no purpose, no natural speech.

**GOOD** — These examples use level-appropriate words. Your dialogues must also use words from your content above.

**GOOD** (classroom — teacher gives instructions, student responds naturally):
> **(На уроці / In the classroom)**
> — Читайте тут. Дивіться!
> — Добре. А це?
> — Ні, не це. Слухайте!
> — Так, я слухаю.

**GOOD** (on the street — someone asks for help, the other responds):
> **(На вулиці / On the street)**
> — Скажіть, будь ласка, де це?
> — Ідіть там. Дивіться — ось!
> — Дякую!

**Key pattern**: Each speaker has a GOAL. One asks/commands, the other REACTS (agrees, questions, redirects) — never just echoes the verb back.

Limit to **2-3 dialogues per module** (not 9). Each in a DIFFERENT situation. Dialogues should make the learner think "I could use this in real life."

Keep paragraphs short (3-5 sentences). Use 3+ callout boxes spread across sections.

Do NOT use Ukrainian grammar terminology (іменник, дієслово, голосний) — students don't know these yet. Do NOT write IPA or Latin transliteration.

**Deliberate errors (showing common mistakes):**
When showing a wrong pattern to avoid, use strikethrough: ~~великий книга~~ → велика книга. This tells the validator the error is intentional. In activities, wrong forms in `options` arrays are always fine (they're distractors) — no special marking needed.

## Language Quality Rules (All Tiers)

### Russianisms (HARD FAIL if found)

Scan your ENTIRE output for these. They cause automatic audit failure:

| Russicism | Correct Ukrainian |
|-----------|-------------------|
| кушати | їсти |
| приймати участь | брати участь |
| получати | отримувати |
| самий кращий | найкращий |
| відноситися | стосуватися |
| слідуючий | наступний |
| любий (= будь-який) | будь-який |
| на то, що | на те, що |
| красивий | гарний |
| прекрасне / прекрасний | чудовий / чудове |

Also scan for Russian characters: **ы, э, ё, ъ** — these must NEVER appear in Ukrainian text.

### English Calque Checklist

As an English-dominant model, you may produce English-to-Ukrainian calques. Check and avoid:

| English Pattern | WRONG Ukrainian | CORRECT Ukrainian |
|---|---|---|
| "will have" | буду мати | матиму |
| "do work" | робити роботу | працювати |
| "save money" | зберегти гроші | заощадити гроші |
| "make a decision" | зробити рішення | прийняти рішення |
| "take a photo" | брати фото | фотографувати / робити фото |
| "have attention" | мати увагу | звертати увагу |
| "give an answer" | давати відповідь | відповідати |
| "make sense" | робити сенс | мати сенс |

### Euphony / Милозвучність (WARNING if violated)

Ukrainian prose must follow euphony rules:

| Rule | Avoid (Bad) | Use (Good) |
|------|-------------|------------|
| і → й between vowels | вона і Олена | вона й Олена |
| й → і after consonant | він й Олена | він і Олена |
| у → в before vowel | у Одесі | в Одесі |
| в → у before в, ф | в вікні | у вікні |
| в → у before consonant cluster | в зграї | у зграї |
| з → із/зі before з, с, ш, ч | з зброєю | із зброєю (або зі) |
| Vary conjunctions | він і вона і Іван | він і вона та Іван |

Key: й can ONLY follow a vowel. After a consonant, always use і — even before a vowel.

### Stress Mark Typography

Use lowercase letters with a combining acute accent (´) on the stressed vowel:
- Correct: ма́ма, анана́с, оса́, сосна́
- Wrong: мА́ма, ананА́с, осА́, соснА́ (do NOT capitalize the stressed vowel)

### Non-Decodable Ukrainian in Beginner Modules (M1-M6)

In Cyrillic primer modules, the learner can only read letters taught so far. Any Ukrainian phrase using letters outside the cumulative charset MUST include an English translation in parentheses immediately after. No exceptions — the learner literally cannot read it otherwise.

- Correct: "Все буде добре (Everything will be fine)."
- Wrong: "Все буде добре." (no translation — learner cannot read Б or Д at M2)

### IPA and Latin Transliteration (BANNED at ALL levels)

Never include IPA symbols (ɑ, ɛ, ʃ, etc.) or bracketed pronunciation guides like `[ma-ma]`, `[a-na-nas]`, `[ˈmɑmɑ]`. The ONLY pronunciation aid is the stress mark (´) on the vowel.

Latin transliterations are BANNED: never use kh, sh, ch, zh, ts, ya, yu, ye, shch.

```markdown
❌ WRONG: "мама [ˈmɑmɑ]" or "хліб (khlib)"
✅ RIGHT: "**ма́ма** (mom)" or "**Х**, like the «ch» in Scottish «loch»"
```

### Typography

- **ALWAYS** use Ukrainian angular quotes: «...» (never straight quotes "...")
- Use ONLY vocabulary from the plan's `vocabulary_hints` — do NOT invent new terms

### No Word Salad (HARD FAIL)

Every paragraph must have ONE clear point and logical flow between sentences. Do NOT string together unrelated observations.

### LLM Writing Patterns to Avoid

1. **"Це не просто X, а Y"** — max ONE in entire module
2. **Grandiose openers** — don't inflate every topic
3. **Purple prose** — no "багатогранний діамант", "хірургічного аналізу"
4. **Duplicate greetings** — "Ласкаво просимо" ONCE (intro only)
5. **Stacked identical callouts** — same title max twice, vary types
6. **"In this lesson, we will..."** — ALWAYS banned (formulaic opener)
7. **Repetitive transitions** — "It's worth noting...", «Варто зазначити...», «Давайте розглянемо...» flagged at 2+ occurrences

### Anti-Robotic Writing

- No 3+ sentences starting with the same phrase
- Vary sentence openers across sections
- No mechanical transitions («Далі ми побачимо...», «Тепер розглянемо...»)
- Each section should have its own narrative arc

### Active Voice Preference

Ukrainian strongly prefers active constructions. Use passive only when the agent is truly unknown.

Avoid: «Це може бути використано...», «Правило застосовується...»
Prefer: «Ви можете використати...», «Ми застосовуємо правило...»


(No video discoveries available)



### Textbook Source Material (ADAPT, don't ignore)

## Textbook Reference (from Ukrainian grammar textbooks)

These are explanations from Ukrainian school grammar textbooks. Use them as **reference** for grammar rules and examples. Adapt for adult A1 learners — keep explanations simple but maintain grammatical accuracy.

**Grade 7, litvinova** — Сторінка 62:
```
§ 11  Наказовий спосіб діє слів  
59
Вправа 84 
 
Спишіть речення, утворивши від діє слів у дужках форми наказового способу 
1) Так (сказати), ви хочете стати справжніми богатирями? 
(Є. Кравченко). 2) (Слухати), добрий чоловіче, коли вже дове­
лося нам іти разом, (зробити) так (Нар. тв.). 3) Котигорошок 
поклонився батькові в ноги й каже: «Батечку, (піти) до кова­
ля, (викувати) мені сильну залізну булаву» (А.  Лотоцький). 
4) (Приїхати) самі, (знайти) мене, і я вас обов’язково з ними 
познайом
```

**Grade 7, litvinova** — Сторінка 60:
```
§ 11  Наказовий спосіб діє слів  
57
§ 11  Наказовий спосіб діє слів
Вправа 79 
1  Прочитайте приспів до пісні «Історія України за 5 хви-
лин», що виконує гурт «ТНМК» (автор слів  — Артем 
Полежака) 
Подивись наліво, подивись направо — 
Це твоя земля, це твоя держава! 
Історія в неї строката, яскрава. 
Слава Україні! — Героям Слава!
2  Поміркуйте, у  якій формі вжито діє слова в  першому рядку  Як ви це зро-
зуміли?
3  Визначте особу й  число дієслів 
4  За можливості знайдіть у мережі «Інтернет
```

**Grade 6, avramenko** — Сторінка 59:
```
59
59
§ 31–32.  Основні  способи словотворення
3.	 Запишіть слова у дві колонки за способом словотворення: 1) префік-
сальний; 2) суфіксальний. 
Прехороший, казочка, учителька, розказати, кілок, урочистість, опи­
тати, родинний, сфотографувати, український, дитинка, зміїний, обпек­
ти, артистка. 
	 З перших букв виписаних слів складіть назви злакових рослин.
4.	 Утворіть по кілька слів суфіксальним способом, використавши суфікси зі 
значенням здрібнілості та згрубілості. Запишіть ці слова (за зр
```

**Grade 6, litvinova** — Сторінка 205:
```
§ 42. Відмінювання прикметників  
205
4. Перш ніж когось засуджувати, спробуй виявити 
причини … вчинку, поведінки. 
5. Виявляй ініціативу, бери … участь у  колективних 
справах.
Довідка: позитивний, негативний, щирий, слабший, 
привітний, активний.
2. Чи згодні ви з  рекомендаціями? Поміркуйте, які пункти варто додати.
3. Чи існують у  вашому класі подібні правила?
Проєкт!
Узагальніть досвід, створіть «Кодекс поведінки в класі».
Вправа 407
Ознайомтеся зі схемою та зразками розбору прикметника я
```

**Grade 5, avramenko** — Сторінка 46:
```
Розділ 1. МИСТЕЦЬКИЙ СПАДОК НАЩАДКАМ
46
За­сіб  чи­тан­ня
З­на­чен­ня­
­Темп чи­тан­ня
Си­ла го­ло­су
Тембр зву­ка
Дик­ція
Па­у­за
Ін­то­на­ці­я
ш­вид­кість чи­тан­ня — рів­на, упо­віль­не­на чи прис­ко­
ре­на (за­леж­но від зміс­ту)
­мак­си­маль­ний сту­пінь ви­я­ву го­ло­су, йо­го нап­ру­же­
ність (най­час­ті­ше по­си­лю­ють го­лос у реп­лі­ках, особ­
ли­во в ок­лич­них ре­чен­нях)
ха­рак­тер­не за­бар­влен­ня, зав­дя­ки яко­му лю­ди­на 
го­во­рить ні­би різ­ни­ми го­ло­са­ми
чіт­ка ви­мо­ва з
```

**Grade 5, litvinova** — Сторінка 42:
```
42
Лексикологія.  Омоніми
щоб бити по  них ногою або словом. Коли ти ко паєш когось 
ногою, то завдаєш фізичного болю. А  коли дошкуляєш обра-
зливим словом  — то болю морального. Ви  ж робите боляче, 
невже не  зрозуміло?
—  Тю. Вони також нас ображають! Ми тільки для сміху 
написали сиріткам, які вони боягузи, а  вони почали відгав-
куватися, наговорюють на  нас казна-що! Ти сама це чита-
ла, — виправдовувалася Вередунка. Їй не  подобалося, коли її 
сварили та  не  цінували її вміння вигадува
```

**L1→L2 Transformation Rules:** The excerpts above are from Ukrainian school textbooks that teach Ukrainian to **native speakers (L1)**. Your learners are **English-speaking teens and adults (L2)**. When adapting:

1. **L1 assumes intuitive grammar** → L2 needs explicit rule statements in English
2. **L1 uses native-level vocabulary** → L2 uses level-appropriate vocabulary guided by textbook excerpts
3. **L1 dialogues assume cultural context** → L2 dialogues need setting/purpose explanation
4. **L1 exercises test metalinguistic knowledge** → L2 exercises test production/comprehension

**Cite your adaptations:** For each dialogue or exercise you adapt from the textbook excerpts, add an HTML comment:
```
<!-- adapted from: Заболотний Grade 5, вправа 221 -->
```
Even when no exact textbook exercise matches, ground your content in textbook pedagogy — use their progression patterns, example types, and exercise formats. Do NOT add fallback comments.



---

## 4. Create Activities (from YOUR content above)

After writing the content, create activities that practice the Ukrainian you just taught. This is why we do both in one pass — you know exactly which words, phrases, and gender pairings you used.

**Targets:**
- 8–15 activities
- Required types: {'type': 'match-up', 'focus': 'Match infinitive to correct imperative form', 'items': 12}, {'type': 'quiz', 'focus': 'Choose correct imperative form in context', 'items': 10}, {'type': 'fill-in', 'focus': 'Complete dialogue with correct imperative', 'items': 8}, {'type': 'true-false', 'focus': 'Evaluate imperative usage correctness', 'items': 8}
- 20 vocabulary items

### Item Minimums (HARD FAIL if under)

| Type | Minimum |
|------|--------|
| quiz | ≥6 items |
| true-false | ≥6 items |
| fill-in | ≥6 items |
| match-up | ≥6 pairs |
| anagram | ≥6 items |
| unjumble | ≥6 items |
| group-sort | ≥8 items |
| watch-and-repeat | ≥1 items |
| classify | ≥1 items |
| image-to-letter | ≥5 items |

### Real Textbook Exercises (вправи) — Pedagogical Inspiration

These are real exercises from Ukrainian school textbooks (grade 3/5/6/7). Study their **pedagogical patterns** — how they build progressively, use familiar vocabulary, and test specific skills. Since your students are English-speaking adults, **translate exercise instructions to English** while keeping Ukrainian content words. Adapt the pedagogical approach (progressive difficulty, real-world context) but not the language of instruction.

**Grade 3, vashulenko** — Сторінка 35:
```
35
Книжки треба шанувати. Не можна 
їх бруднити, рвати. Пошкоджені книжки 
слід полагодити.
Прочитай і розкажи 
у класі.
Я — учителька
Я — учитель
Якщо речення вимовляють з особ­
ливим почуттям, із підсилювальною 
інтонацією, то вони стають оклич-
ними. У кінці окличних речень став-
лять знак оклику.
2   Прочитай текст. Визнач, які це речення 
за метою висловлювання.
	 	
3   Розгляньте малюнки. Складіть за одним із них невеликий 
текст, використовуючи окличні речення. Прочитайте його 
з потріб
```

**Grade 3, kravtsova** — Сторінка 132:
```
132
363.	 1.	 Прочитай текст. Які правила гарної поведінки ти знаєш?
Завжди дотримуй свого слова. 
Поводься шляхетно. 
Виконуй все вчасно. 
Прислухайся до думок інших. 
Стався з повагою до себе та оточуючих.
Крок 1. Виконай завдання на вибір.
	 Дослідиѳ, чи має цей текст ознаки художнього стилю.
	 Дослідиѳ, чи має цей текст ознаки науково-популярного стилю.
Крок 2. Зроби висновок. 
2.	 Дослідиѳ, ознаки якого стилю може мати текст.
364.	 Дослідиѳ, які ознаки ділового стилю може мати текст. 
Для ц
```

**Grade 3, vashulenko** — Сторінка 144:
```
144
Поняття про дієслово як частину 
мови
Навчаюся визначати дієслова
Пригадай і розкажи 
у класі.
Я — учителька
Я — учитель
писати
пише
пишуть
писав
написав
напише
45
Слова, які називають дії предметів і відповідають на 
питання що робити? що робить? що роблять? що 
робив? що зробив? що буде робити? що зробить?, 
є дієсловами. Дієслово — це частина мови.
	 	
1   Вивчіть напам’ять вірш Володимира Верховеня. Розкажіть одне 
одному.
  Випишіть із вірша дієслова за абеткою. Що вони називають? На 
```

**Grade 3, ponomarova** — Сторінка 108:
```
108
ÐÎÇÏ²ÇÍÀÞ Ä²ªÑËÎÂÀ 
ÐÎÇÏ²ÇÍÀÞ Ä²ªÑËÎÂÀ 
1. Прочитай текст. Яке слово в ньому є багатозначним?
2. Прочитай текст. Випиши дієслова. Поряд у дужках запи-
ши питання до кожного. Познач префікси в дієсловах.
Тече, поспішає Дніпро до синього моря. На його 
берегах стоїть місто. Воно носить назву великої
річки — Дніпро. 
Проведи дослідження!
1. Прочитай виділені в тексті слова. 
2. Поміркуй, що вони називають.
3. Постав питання до кожного слова. Пригадай, як назива-
ються такі слова. Перевір себе з
```

**Grade 3, savchenko** — Сторінка 77:
```
77
* * *
На щастя, на здоров’я,
на Новий рік,
аби вам родило
краще, ніж торік.
Жито, пшениця,
всяка пашнèця,
коноплі під стелю,
сорочка по землю,
а льон по коліна.
Аби в нас хрещених, 
голова не боліла,
будьте здорові,
з Новим роком!
 Прочитайте засівальну пісню радісно, заклично. Вивчіть її 
напам’ять.
Бажаю тобі і твоїм друзям 
веселих новорічних і різдвяних свят!
Відкрийте скриньку очікувань. Знайдіть свої записи. 
Що з очікувань справдилось, а що ні? Обміняйтесь 
думками.
Скринька очiкувань
```

### Which Activity Types to Use

**ALLOWED:** quiz, true-false, fill-in, match-up, anagram, unjumble, group-sort, watch-and-repeat, classify, image-to-letter
**FORBIDDEN:** cloze, error-correction, mark-the-words, select, translate, essay-response, critical-analysis, comparative-study, authorial-intent

Choose types based on what the constraints allow:

| Constraint level | Use these | Avoid these |
|-----------------|-----------|-------------|
| Letters/syllables only (M1-M10) | quiz, match-up, group-sort, anagram, true-false | fill-in, unjumble, cloze, translate |
| Words + simple phrases | + fill-in, match-up with phrases | unjumble, cloze |
| Basic sentences allowed | + unjumble, fill-in with sentences, translate | cloze (needs 14+ blanks) |

### Language Rules (A1/A2)

- **Questions, instructions, explanations** → English (students can't read Ukrainian metalanguage)
- **Content being practiced** → Ukrainian (words, letters, phrases from the lesson)
- **Options** → Ukrainian when choosing Ukrainian words, English when choosing concepts
- Never use grammar terms like іменник, дієслово, відмінок

### Irregular Forms Warning (CRITICAL for activities)

Some Ukrainian verbs have **irregular imperative forms**. NEVER guess — use ONLY the forms from your content above. Common traps:
- взяти → **візьми/візьміть** (NOT ~~взяй/взяйте~~)
- стояти → **стій/стійте** (NOT ~~стояй/стояйте~~)
- сісти → **сядь/сядьте** (NOT ~~сісь/сісьте~~)
- їсти → **їж/їжте** (NOT ~~їсь/їсьте~~)
- **и** is RUSSIAN. The Ukrainian conjunction is **і** (or **й** after vowels, **та**).

If a verb's imperative isn't in your content, don't use it in activities.

### Consistency Rules (the whole point of single-pass)

1. **Same words**: Every Ukrainian word in activities must appear in your content above
2. **Correct agreement in answers**: Activity `answer` fields must have correct adj-noun gender agreement. If you wrote `великий стіл` in content, the correct answer in activities must also be `великий стіл` — NOT `велика стіл`
3. **Wrong forms are OK as distractors**: In `options` arrays, wrong gender/case forms are expected — they're the incorrect choices. Example: `options: ["нова", "новий", "нове", "нові"]` for a feminine noun — only `нова` is correct, the rest are intentional distractors
4. **Same forms**: If content uses `книга` (nominative), don't use `книги` (genitive) in the `answer` unless genitive also appears in the content

### Activity Schemas (EXACT field structures — any unlisted field = FAIL)

**quiz** — English questions, Ukrainian options:
```yaml
- type: quiz
  title: "Check Your Knowledge"
  instruction: Choose the correct answer.   # optional
  items:  # minItems: 6
    - question: "What does мама mean?"      # ≥5 words
      explanation: "Мама means mom."        # at QUESTION level, NOT inside options
      options:                              # exactly 4, exactly 1 correct
        - text: "mom"
          correct: true
        - text: "dad"
          correct: false
        - text: "sister"
          correct: false
        - text: "brother"
          correct: false
```

**anagram** — letter scramble (M1-M10 ONLY, not M11+):
```yaml
- type: anagram
  title: "Unscramble the Word"
  instruction: "Rearrange the letters."     # optional
  items:  # minItems: 8
    - scrambled: "А М А М"                  # SPACE-SEPARATED, same letters as answer
      answer: "МАМА"
```

**unjumble** — sentence word reorder (M11+ ONLY, not M1-M10):
```yaml
- type: unjumble
  title: "Put the Words in Order"
  items:  # minItems: 8
    - words: ["книга", "Це", "нова"]        # array of strings
      answer: "Це нова книга"               # single string
```
Do NOT use `sentence`, `jumbled`, or `scrambled` — only `words` + `answer`.

**match-up**:
```yaml
- type: match-up
  title: "Match the Pairs"
  pairs:  # minItems: 6, use "pairs:" NOT "items:"
    - left: "книга"
      right: "book"
```

**fill-in** — MUST include `options`:
```yaml
- type: fill-in
  title: "Complete the Sentence"
  items:  # minItems: 6
    - sentence: "Це ___ стіл."
      answer: "великий"
      options: ["великий", "велика", "велике", "великі"]  # exactly 4, answer must be in list
```

**group-sort**:
```yaml
- type: group-sort
  title: "Sort by Gender"
  groups:  # 2-4 groups
    - name: "Masculine"
      items: ["стіл", "брат", "дім"]
    - name: "Feminine"
      items: ["книга", "мама", "мова"]
```

**true-false**:
```yaml
- type: true-false
  title: "True or False?"
  items:  # minItems: 8
    - statement: "The letter Н makes the same sound as English H."
      correct: false
      explanation: "Н looks like H but sounds like N."
```

### Vocabulary YAML

- **Object with `items:` wrapper** (not bare list)
- Each entry: `lemma`, `translation`, `pos` (required); `gender`, `notes`, `usage`, `example` (optional)
- NO `ipa` field
- Include ALL words from `vocabulary_hints` in the plan

### YAML Formatting (HARD FAIL)

**Content** uses Ukrainian quotes «...». **YAML values** must NOT use «» — they break parsing with colons.

```yaml
❌ WRONG:  title: «Знайдіть пару: термін»
✅ RIGHT:  title: 'Знайдіть пару: термін'
```

Rules for YAML:
1. Never use `«»` — use plain text or single/double quotes
2. Quote any value containing `:` with single quotes
3. No IPA, no Latin transliteration in YAML values

---

## 5. Self-Audit Before Output

## Self-Audit (Run BEFORE Final Output)

After writing all content, you MUST run the audit and fix any issues — all within this session.

### Step 1: Write Content to Disk

Write your complete content to `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/imperative-and-requests.md` using write_file or bash:

```bash
cat > /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/imperative-and-requests.md << 'CONTENT_EOF'
... your content here ...
CONTENT_EOF
```

### Step 2: Run Audit

```bash
bash scripts/audit_module.sh /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/imperative-and-requests.md --skip-activities --no-rag-verify
```

This checks: word count, Russianisms, engagement callouts, euphony, structure, immersion %.

### Step 3: Parse Results

- If you see `AUDIT PASSED` — proceed to output.
- If you see `AUDIT FAILED` — read the violations, fix content in-place, and re-run the audit.

### Step 4: Fix Loop (max 2 iterations)

If the audit fails:
1. Read the specific gate failures and violation details from the audit output
2. Edit `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/imperative-and-requests.md` to fix each issue (add words if under target, remove Russianisms, add callout boxes, etc.)
3. Re-run: `bash scripts/audit_module.sh /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/imperative-and-requests.md --skip-activities --no-rag-verify`
4. If still failing after 2 fix attempts, proceed to output anyway — the validate phase will handle remaining issues.

### Step 5: Report Self-Audit Result

After audit (pass or fail), include this block in your output:

```
===SELF_AUDIT_START===
status: PASS | FAIL
iterations: {number of audit runs}
final_word_count: {word count from last audit}
gates_passed: {list of passed gates}
gates_failed: {list of failed gates, or "none"}
fixes_applied: {brief description of what you fixed, or "none"}
===SELF_AUDIT_END===
```

**IMPORTANT**: Do NOT skip the audit. Do NOT fabricate audit results. Run the actual command and report real output.


### Content Checks
- [ ] Word count ≥ 1200?
- [ ] Every plan section has prose?
- [ ] 3+ callout boxes?
- [ ] All target vocabulary words used in content?
- [ ] No Russianisms, Russian characters, IPA?
- [ ] No bilingual ping-pong? (Scan for Ukrainian sentence → English translation in the same paragraph. If found, move the Ukrainian to a table, list, or dialogue.)
- [ ] **Dialogue quality**: Max 2-3 dialogues total. Every dialogue starts with `> **(Location)**`. No echo-drill patterns (speaker A commands → speaker B echoes the verb). If you find an echo drill, REWRITE it with a real situation and varied responses.
- [ ] **Textbook citations**: At least 1 `<!-- adapted from: ... -->` or `<!-- original: ... -->` comment per H2 section.

### Activity Checks
- [ ] 8–15 activities?
- [ ] Activities use only words from content above?
- [ ] Every Ukrainian word also appears in content?
- [ ] Adjective-noun pairings match content?
- [ ] Quiz: exactly 1 `correct: true`, `explanation` at question level?
- [ ] Anagram: scrambled letters = answer letters?
- [ ] Fill-in: `answer` appears in `options`?
- [ ] Match-up: uses `pairs:` not `items:`?
- [ ] No extra fields (schema is `additionalProperties: false`)?
- [ ] No `hint` fields in any activity items?

---

## 6. Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded.

Output FOUR blocks in this exact order:

**Block 1: Content**
```
===CONTENT_START===

<!-- SCOPE
Covers: {what this module teaches}
Not covered:
  - {related topic} → {slug}
-->

# {Title}

> **Чому це важливо?**
>
> {2-3 sentences}

## {Section 1}
...

---

# Підсумок

{Summary + 3-4 self-check questions. Each question includes English translation.}

---

===CONTENT_END===
```

**Block 2: Word Counts**
```
===WORD_COUNTS===
Section "{name}": {count} words (minimum: {allocation})
...
Total: {total} words (target: 1200)
===WORD_COUNTS===
```

**Block 3: Activities (BARE LIST — no `activities:` wrapper)**
```
===ACTIVITIES_START===

- type: quiz
  title: "..."
  items:
    ...

- type: match-up
  title: "..."
  pairs:
    ...

===ACTIVITIES_END===
```

**Block 4: Vocabulary (object with `items:` wrapper)**
```
===VOCABULARY_START===

items:
  - lemma: "книга"
    translation: "book"
    pos: "noun"
    gender: "f"

===VOCABULARY_END===
```

**Block 5: Friction Report (MANDATORY)**
```
===FRICTION_START===
**Phase**: Full Build (Content + Activities + Vocabulary)
**Step**: {what you were doing when friction occurred, or "Complete build"}
**Friction Type**: NONE | YAML_SCHEMA_VIOLATION | WORD_BANK_LIMITATION | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if applicable, or "N/A"}
===FRICTION_END===
```
