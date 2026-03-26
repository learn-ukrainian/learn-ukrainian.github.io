# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **10: Colors** (A1, A1.2 [My World]).

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
module: a1-010
level: A1
sequence: 10
slug: colors
version: '1.1'
title: Colors
subtitle: Синій, жовтий — the colors of Ukraine and your world
focus: vocabulary
pedagogy: PPP
phase: A1.2 [My World]
word_target: 1200
objectives:
- Name 12 basic colors in Ukrainian
- Use color adjectives with correct gender agreement (including soft-stem синій)
- Distinguish синій (dark blue) from блакитний (light blue) — a distinction English
  lacks
- Describe objects using color + M09 adjective combinations
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Choosing a gift (Большакова Grade 2 p.38 colors poem as inspiration):
    — Яка гарна сумка! Якого вона кольору? — Червона. А дивись, є ще синя і зелена.
    — Мені подобається синя. — А мені — жовта! Colors emerge naturally through shopping
    scenario.'
  - 'Dialogue 2 — Describing your room (extending M08-M09): — Якого кольору твоя кімната?
    — Біла. Стіни білі. — А килим? — Килим коричневий. А крісло — сіре. Review: gender
    agreement + new color vocabulary.'
- section: Кольори (Colors)
  words: 300
  points:
  - '12 basic colors organized by adjective type: Hard-stem (-ий/-а/-е — same pattern
    as M09): червоний/червона/червоне (red) жовтий/жовта/жовте (yellow) зелений/зелена/зелене
    (green) чорний/чорна/чорне (black) білий/біла/біле (white) сірий/сіра/сіре (grey)'
  - 'Soft-stem (-ій/-я/-є — NEW pattern): синій/синя/синє (dark blue) Вашуленко Grade
    3 p.130: adjectives divide into тверда група (-ий) and м''яка група (-ій). Only
    синій is soft-stem among basic colors — learn it as a special case now. Compare:
    великий стіл → синій стіл, велика книга → синя книга, велике вікно → синє вікно.'
- section: Синій ≠ блакитний (Blue ≠ Blue)
  words: 300
  points:
  - 'Ukrainian has TWO blues — English has one: синій = dark blue, deep blue (the
    sea, the night sky, ink) блакитний = light blue, sky blue (a clear daytime sky,
    baby blue) Прапор України — синьо-жовтий (Кравцова Grade 2 p.22: Синьо-жовтий
    прапор маєм: синє — небо, жовте — жито). Cultural note: ''голубий'' is a Russian-influenced
    word for light blue — use блакитний.'
  - 'More colors for describing things: коричневий (brown), рожевий (pink), помаранчевий
    (orange), фіолетовий (purple). These are all hard-stem (-ий/-а/-е). Compound colors:
    темно-зелений (dark green), світло-синій (light blue-ish). Cultural hook: вишиванка
    — traditional embroidered shirt, typically червоний і чорний (Полісся) or червоний
    і синій (Полтавщина).'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Color agreement follows the same rules as M09: Hard-stem: червоний стіл, червона
    книга, червоне вікно. Soft-stem: синій стіл, синя книга, синє вікно. Self-check:
    What color is the Ukrainian flag? (синьо-жовтий) Describe 3 things in your room
    using colors. What''s the difference between синій and блакитний?'
vocabulary_hints:
  required:
  - червоний (red)
  - жовтий (yellow)
  - зелений (green)
  - синій (dark blue — soft-stem!)
  - блакитний (light blue, sky blue)
  - білий (white)
  - чорний (black)
  - сірий (grey)
  - колір (color, m)
  - якого кольору? (what color?)
  recommended:
  - коричневий (brown)
  - рожевий (pink)
  - помаранчевий (orange)
  - фіолетовий (purple)
  - темний (dark — as prefix: темно-)
  - світлий (light — as prefix: світло-)
  - прапор (flag, m)
activity_hints:
- type: quiz
  focus: Якого кольору? Match objects to their typical color.
  items: 8
- type: fill-in
  focus: 'Gender agreement with colors: син__ книга, червон__ стіл, біл__ вікно'
  items: 10
- type: quiz
  focus: синій or блакитний? Choose the right shade of blue.
  items: 6
- type: group-sort
  focus: Sort colors into тверда група (-ий) and м'яка група (-ій)
  items: 10
connects_to:
- a1-011 (How Many?)
prerequisites:
- a1-009 (What Is It Like?)
grammar:
- 'Soft-stem adjectives: синій/синя/синє (-ій/-я/-є) vs hard-stem (-ий/-а/-е)'
- Color adjective agreement follows M09 rules
- Compound colors with темно-/світло- (hyphenated)
register: розмовний
references:
- title: Большакова Grade 2, p.38
  notes: 'Colors poem: синє, чорне, зелене, блакитне, червоне, жовте, золоте, оранжеве.'
- title: Вашуленко Grade 3, p.130
  notes: 'Hard vs soft adjective groups: новий (тверда) vs синій (м''яка).'
- title: Кравцова Grade 2, p.22-23
  notes: 'Синьо-жовтий прапор маєм: синє — небо, жовте — жито.'

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Colors
**Module:** colors | **Phase:** A1.2 [My World]
**Textbook grades searched:** 1, 2, 3

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 23
> 	
> Які? (розмір)
> 	
> Які? (колір)
> 	
> Які? (смак)
> (яке?)
> (який?)
> (який?)
> (який?)
> (який?)
> (який?)
> (який?)
> (який?)
> (           ?)
> Слова — назви ознак предметів
> 	 Який у тебе сьогодні настрій? Вибери.
> Який?
> Яка?
> Яке?
> Які?
> (яка?)
> (яка?)
> (яка?)
> (           ?)

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> 43
> • Уяви, що малюнків було багато. Добери до слів — назв 
> предметів слова — назви ознак.
> Зразок. будинок (який?) червоний — будинки (які?) чер-
> воні.    
> Дах (який?) … — дахи (які?) … . 
> Двері (які?) … . 
> Вікно (яке?) … — вікна (які?) … . 
> Стіна (яка?) … — стіни (які?) …  . 
> Аркуш  (який) … — аркуші (які?) ... .
>  
> Допиши слова — назви предметів. 
> 1. Дерев’яний, письмовий, коричневий … .
> 2. Скляна, висока, прозора … .
> 3. Паперове, різнобарвне, веселе … .
> 4. Пластикові, довгі, тонкі … .
> • Чому не

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 6
> џ
> У якому класі навчалися учні? Як вони поводилися на 
> уроці? Чим учителька зацікавила бешкетників? Чи 
> змінилася поведінка учнів після слухання оповідки?
> џ
> Прочитай заголовок наступної частини. Як ти гадаєш, про 
> що в ній ітиметься?
> — Голубий, бо небо голубе, — сказав Сашко.
> — Червоний, бо червона кров, — промовила Олеся.
> — Зелений, бо зелені листя й трава, — сказав Максим.
> — Жовтий, бо я його люблю, — додала Наталя.
> — Чорний, бо він найтемніший, — сказав наостанку Пет-
> русь.
> — Ні, любі мої,

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 61
> М’ЯКИЙ ПРИГОЛОСНИЙ ЗВУК [й]
> Назви предмети. Як вимовляється звук [й] у словах?
> М АЙ|К А
> Й О Д
> СЛОВА — НАЗВИ ОЗНАК
> Добери слова до малюнків.
>  
> холодний 
> сірий 
> білий 
> зелений
>  
> високий 
> довгий 
> теплий 
> голодний 
>  
>  
>  
>  
>  
> Назви кольори предметів. Подумай, які малюнки можуть 
> бути в останньому стовпчику.
> ЯКИЙ?
> ЯКА?
> ЯКЕ?
> ЯКІ?
> 1
> 1
>  
> 2

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> 73
> • Чому кишеню назвали щедрою? 
> • Напиши, коли ти буваєш щедрим. Чому?
> • Установи послідовність малюнків відповідно до тексту. 
> Перекажи оповідання, користуючись малюнками.
> сЛова оДноЗначнІ Й БаГатоЗначнІ
> СЛОВА
> одне значення
> багато значень
> однозначні
> багатозначні
> Багатозначні слова називають предмети, ознаки, дії, 
> у чомусь схожі між собою.

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 60
> 5.	 Чи правильно зробила білочка, що організувала колек-
> тивний подарунок?
> 6.	 Що потрібно зробити, щоб клас був дружним? Напиши.
> Зразок. 
> На мою думку, кожен із нас мріє мати багато друзів. 
> Але, на жаль, є діти, яким важко спілкуватися в колективі. Їх 
> необхідно підтримати. Можна просто підійти і поговорити, пожар-
> тувати і погратися. І тоді дитина відчує себе потрібною, а колектив 
> стане дружним.
> 3.	 Прочитайте твір однокласника / однокласниці. Скажіть, що 
> вам найбільше сподобалося в його

## Кольори (Colors)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 48
> Є є
> Бачу  Є, є. Чую  [йе] або [е].
> — не	
> те	   се
> — ен	
> ет	   ес
> — нє	
> тє	   сє
> — єн	
> єт	   єс
> І барвінком, і ру­тою,
> і ряс­том квіт­чає
> вес­на зем­лю, мов дів­чи­ну,
> в зе­ле­но­му гаї.
>                           Тарас Шев­чен­ко
> [–•]
> [•–]
> [=•]
> [=•–]
> є д и н о р і
> о л ь
> к
> є
> а є *
> з
> ь
> г
>  [ –•|=  = • ]  
>  [ –•|=•= ] 
> [–•|=•]
> [–  =•|–•|=•]
> [–•|­=•]
> кує
>     квітує
> синє
>  [ к в′ і|т у| й е ] 
>  [ с и|н′ е ]  
>  [ к у|й е ]  
> 	 Прочитай слова.
> малю
> вишива
> співа
> суму
> чита
> гра
> є
> є
> Pidruchnyk.com.ua

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> Катерина Перелісна
> ЗОЛОТА ОСІНЬ
> В парках і садочках, 
> на доріжки й трави, 
> падають листочки 
> буро-золотаві.
> Де не глянь, навколо 
> килим кольористий, 
> віти напівголі 
> й небо синє-чисте.
> Авторка
> Автор (авторка) — людина, яка створила 
> художній, музичний або мистецький твір.
> Прохолода, хризантеми, буро-золотаві, метушні, 
> кольо­ристий, поналиті.
> Прочитай правильно
> Прочитай плавно цілими словами.
> верес	
> жовтий	
> листок
> вересень	
> жовтень	
> листопад
> вересневий	
> жовтіє	
> листочок
> Осінні барви, осінній нас

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 3
> Розмаїттям кольоровим 
> прикрашає осінь край
> Інна Кульська
> ВЕРЕСЕНЬ
> Щедрий місяць вересень
> у віночку з вересу.
> Все добро, що в нього є,
> щиро друзям роздає.
> От у свій найперший ранок
> він стрічає школярів:
> дав і яблук на сніданок,
> і жоржин — для вчителів…
> Отакий-то вересень
> у віночку з вересу.
> Вересень красне літо проводжає, 
> золоту осінь зустрічає.
> Щедрий, найперший, стрічає, жоржин, отакий-то. 
> Прочитай правильно
> 1
> Ось і промайнуло тепле літечко. Упевнено крокує до 
> нас щедра і барвиста красуня

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 61
> М’ЯКИЙ ПРИГОЛОСНИЙ ЗВУК [й]
> Назви предмети. Як вимовляється звук [й] у словах?
> М АЙ|К А
> Й О Д
> СЛОВА — НАЗВИ ОЗНАК
> Добери слова до малюнків.
>  
> холодний 
> сірий 
> білий 
> зелений
>  
> високий 
> довгий 
> теплий 
> голодний 
>  
>  
>  
>  
>  
> Назви кольори предметів. Подумай, які малюнки можуть 
> бути в останньому стовпчику.
> ЯКИЙ?
> ЯКА?
> ЯКЕ?
> ЯКІ?
> 1
> 1
>  
> 2

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> Прочитай слова. Назви їх одним словом.
> Жовтогарячий, жовтий, рудий, синій, багряний.
> Художники передають свої враження від побаченого 
> фарбами на полотні. А поети — словами. Читаючи вірші, 
> учися відчувати красу художнього слова.
> Прочитай вірш.
> БАРВИСТА ОСІНЬ 
> Осінній дощик дрібно плаче, 
> і листячко жовтогаряче 
> з дерев поволі опадає, 
> лиш клен рудий горить-палає. 
> Дарує нам барвиста осінь 
> буяння фарб і неба просинь*, 
> ранкові прохолодні роси, 
> верби старої жовті коси, 
> багрянець лісу світанков

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 157
> РОЗМАЇТТЯМ  КОЛЬОРОВИМ  ПРИКРАШАЄ  ОСІНЬ  КРАЙ
> 	
> Інна Кульська. Вересень.............................................................................3
> 	
> Алевтина Волкова. Перший подих осені...................................................4
> 	
> Марія Хоросницька. Осінь..........................................................................5
> 	
> Марія Пономаренко. Осінь пензлика взяла...............................................6
> 	
> Наталка Поклад. Вересень....................................

## Синій ≠ блакитний (Blue ≠ Blue)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 41
> 41
> У-кра-ї-на,  у-кра-їн-ці,  у-кра-їн-ка,  
> у-кра-ї-нець,  у-кра-їн-ська.
> У-кра-ї-на — рід-ний край,
> Рід-не по-ле, зе-лен гай,
> Рід-не міс-то й рід-на ха-та,
> Рід-не не-бо й рід-на ма-ти.
>                                                Ярослав Скидан 
> 	 Розглянь ілюстрацію.
> 	 Назви кольори прапора. Що зображено на 
> гербі? У яких місцях України ти бував / бува-
> ла?
> 	
> Прочитайте прислів’я.
> Без вер-би й ка-ли-ни не-ма У-кра-ї-
> ни.
> 	 Вивчи прислів’я напам’ять.

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> Роз’єднай слова і прочитай прислів’я.
> Депрапорпіднімають,тамУкраїнувеличають.
> • 
> Поясни, як ти розумієш це прислів’я.
> Послухайте вірш Наталки Поклад «Прапор».
> • 
> Коли відзначають День Державного Прапора?
> Прочитай вірш.
> ПРАПОР
> Прапор — це державний символ, 
> він є в кожної держави; 
> це для всіх — ознака сили, 
> це для всіх — ознака слави. 
> Синьо-жовтий прапор маєм: 
> синє — небо, жовте — жито; 
> прапор свій оберігаєм, 
> він святиня, знають діти.
> Прапор свій здіймаєм гордо, 
> ми з ним дужі і єдині, 
> ми

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 150
> 4. Спиши з тексту про гімн виділену частину, вставивши 
> пропущені букви.
> Записані послідовно заголовки або запитання до 
> кожної частини тек

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Кольори (Colors)` (~300 words)
- `## Синій ≠ блакитний (Blue ≠ Blue)` (~300 words)
- `## Підсумок — Summary` (~300 words)
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

GRAMMAR CONSTRAINTS (A1.2 — My World, M08-M14):
Noun gender, adjective agreement, plurals, numbers, demonstratives.

ALLOWED:
- Це + noun, У мене є/немає
- Adjective-noun agreement (nominative only)
- Numbers 1-1000
- Demonstratives цей/ця/це/ці
- Question words: Який? Яка? Яке? Скільки?
- Fixed verbal phrases from A1.1 (Мене звати, працювати)

BANNED: Verb conjugation (taught in A1.3), past/future tense, cases beyond nominative,
participles, passive voice, subordinate clauses

### Vocabulary

**Required:** червоний (red), жовтий (yellow), зелений (green), синій (dark blue — soft-stem!), блакитний (light blue, sky blue), білий (white), чорний (black), сірий (grey), колір (color, m), якого кольору? (what color?)
**Recommended:** коричневий (brown), рожевий (pink), помаранчевий (orange), фіолетовий (purple), {'темний (dark — as prefix': 'темно-)'}, {'світлий (light — as prefix': 'світло-)'}, прапор (flag, m)

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
## Діалоги (Dialogues) (~330 words total)

- P1 (~40 words): Brief scene-setting for Dialogue 1 — two friends shopping for a birthday gift at a market. Introduce the situation in English, prime the learner to listen for color words.

- Dialogue 1 (~100 words): Choosing a gift. Characters browse items: — Яка гарна сумка! Якого вона кольору? — Червона. А дивись, є ще синя і зелена. — Мені подобається синя. — А мені — жовта! Я люблю жовтий колір. — А ця біла? Теж гарна. — Так, але червона найкраща. Бери червону! Colors emerge naturally through preferences and comparisons. Each color adjective appears in feminine form to match сумка.

- P2 (~30 words): Comprehension bridge between dialogues. Point out that every color changed form to match сумка (feminine): червона, синя, зелена, жовта, біла. Ask: why not червоний?

- P3 (~30 words): Scene-setting for Dialogue 2 — describing your room (connects to M08 rooms, M09 adjectives). A video call where one friend shows their room.

- Dialogue 2 (~100 words): Describing a room. — Якого кольору твоя кімната? — Біла. Стіни білі. — А килим? — Килим коричневий. А крісло — сіре. — У мене крісло чорне. І стіл теж чорний. — А шафа? — Шафа коричнева. Але двері білі. Colors appear with masculine (килим, стіл), feminine (шафа), neuter (крісло), and plural (стіни, двері) nouns — previewing the full agreement pattern.

- P4 (~30 words): Post-dialogue observation. Highlight the gender shifts: коричневий килим but коричнева шафа, сіре крісло but сірий стіл. The color changes its ending to match the noun — just like M09.

## Кольори (Colors) (~330 words total)

- P1 (~80 words): Present the 6 hard-stem colors as a group, explicitly labeling them тверда група (-ий/-а/-е). Table or list format: червоний/червона/червоне (red), жовтий/жовта/жовте (yellow), зелений/зелена/зелене (green), чорний/чорна/чорне (black), білий/біла/біле (white), сірий/сіра/сіре (grey). Point out: these follow the exact same pattern as великий/велика/велике from M09. If you learned M09, you already know how these work.

- P2 (~70 words): Practice the pattern with real objects. Examples: червоний автобус, жовта квітка, зелене яблуко, чорний кіт, біла стіна, сірий день. Show the question-answer pattern: Якого кольору автобус? — Червоний. Якого кольору квітка? — Жовта. Якого кольору яблуко? — Зелене. Emphasize якого кольору? as the key question (genitive — don't explain the case, just teach the phrase as a chunk).

- Exercise: **fill-in** — Gender agreement with hard-stem colors. 10 items: червон__ стіл, жовт__ книга, зелен__ вікно, чорн__ кіт, біл__ стіна, сір__ небо, червон__ сумка, жовт__ автобус, зелен__ дерево, чорн__ двері. (activity_hints #2)

- P3 (~80 words): Introduce the ONE soft-stem color: синій/синя/синє (dark blue). Explain this is м'яка група (-ій/-я/-є) — reference Вашуленко Grade 3 p.130. Compare side by side: великий стіл → синій стіл, велика книга → синя книга, велике вікно → синє вікно. The difference: -ий vs -ій, -а vs -я, -е vs -є. Among basic colors, only синій follows this pattern — learn it as a special case.

- P4 (~60 words): Practice синій with objects: синій олівець, синя ручка, синє небо, синій стіл, синя шафа, синє море. Short drill comparing hard vs soft: червоний олівець but синій олівець, червона ручка but синя ручка, червоне небо but синє небо. The endings sound similar but the softness changes the vowel.

- Exercise: **group-sort** — Sort colors into тверда група (-ий) and м'яка група (-ій). 10 items: червоний, синій, жовтий, зелений, чорний, білий, сірий + noun phrases like синя книга, червона книга, синє вікно. (activity_hints #4)

## Синій ≠ блакитний (Blue ≠ Blue) (~330 words total)

- P1 (~80 words): The big idea — Ukrainian sees TWO blues where English sees one. синій = dark blue, deep blue (the sea at night, ink, denim jeans). блакитний = light blue, sky blue (a clear daytime sky, baby clothes, forget-me-nots). This isn't just a shade preference — Ukrainians experience these as fundamentally different colors, the way English speakers see "red" and "pink" as different. Conversational example: Яке небо? — Блакитне (daytime). Яке море? — Синє (deep).

- P2 (~60 words): Cultural anchor — the Ukrainian flag. Reference Кравцова Grade 2 p.22: Синьо-жовтий прапор маєм: синє — небо, жовте — жито. The flag is синьо-жовтий, not блакитно-жовтий — because the blue represents the deep sky, not a pale shade. Note: the word голубий for light blue is Russian-influenced — use блакитний.

- Exercise: **quiz** — синій or блакитний? Choose the right shade. 6 items: the sea (синє), a clear sky (блакитне), jeans (сині), a baby blanket (блакитна), ink (синє), a summer sky (блакитне). (activity_hints #3)

- P3 (~80 words): Four more colors for describing things: коричневий (brown), рожевий (pink), помаранчевий (orange), фіолетовий (purple). All hard-stem (-ий/-а/-е). Examples with objects: коричневий шоколад, рожева квітка, помаранчевий апельсин, фіолетова сукня. Note помаранчевий comes from помаранч (orange fruit) — the color is named after the fruit, just like in English.

- P4 (~60 words): Compound colors with темно- and світло- (hyphenated): темно-зелений (dark green), світло-синій (light blue-ish), темно-червоний (dark red / maroon). Cultural hook: вишиванка patterns — traditionally червоний і чорний in Полісся, червоний і синій on Полтавщина. Colors carry regional identity.

- Exercise: **quiz** — Якого кольору? Match objects to their typical color. 8 items: сніг (білий), ніч (чорна), сонце (жовте), трава (зелена), помідор (червоний), шоколад (коричневий), небо вдень (блакитне), море (синє). (activity_hints #1)

## Підсумок — Summary (~330 words total)

- P1 (~80 words): Recap the two adjective groups for colors. Hard-stem (тверда група): червоний/червона/червоне — same pattern as M09. All basic colors except one follow this. Soft-stem (м'яка група): синій/синя/синє — the -ій/-я/-є pattern. Only синій among basic colors. The key question: Якого кольору? + noun. Answers match the noun's gender: Якого кольору стіл? — Білий. Якого кольору книга? — Біла. Якого кольору вікно? — Біле.

- P2 (~70 words): Recap синій vs блакитний — the two blues. Синій = deep, dark blue (море, чорнило, джинси). Блакитний = light, sky blue (небо вдень, незабудки). The Ukrainian flag is синьо-жовтий. This distinction doesn't exist in English but is natural for Ukrainian speakers — a child in Ukraine learns these as two separate colors, not shades of one.

- P3 (~60 words): Full color inventory — all 12+ colors learned: червоний, жовтий, зелений, синій, блакитний, білий, чорний, сірий, коричневий, рожевий, помаранчевий, фіолетовий. Plus compound forms: темно-/світло- + color. Preview: in M11 (How Many?) you'll count colored objects — два червоні олівці, три синіх ручки — and the endings will change again.

- P4 (~60 words): Self-check practice prompts. Якого кольору прапор України? (синьо-жовтий). Describe 3 things in your room using colors — remember gender agreement! Яка різниця між синій і блакитний? Name something синє and something блакитне. What color group does синій belong to? (м'яка група). What about червоний? (тверда група).

- P5 (~60 words): Encouragement and real-world application. Start noticing colors around you and naming them in Ukrainian. When you see the sky — is it синє чи блакитне? When you dress — якого кольору твоя сорочка? Colors are everywhere, and now you can describe your whole world in Ukrainian. Наступний модуль: How Many? — counting the colorful things around you.

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
