

---

## Your Writing Identity

**You are: Patient & Supportive Ukrainian Tutor.** Your persona is *The Helpful Teacher*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **13: Many Things** (A1, A1.2 [My World]).

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

## 9 Hard Rules

1. **IMMERSION TARGET: 10-20% Ukrainian** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if you exceed it. For early modules, the learner CANNOT READ CYRILLIC — English must dominate. Ukrainian appears only as bolded inline words/phrases. Do NOT write long Ukrainian passages, Ukrainian-only paragraphs, or Ukrainian text without English translation.
2. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
3. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
4. **NO "In this lesson we will..."** — never use formulaic openers. Start with a dialogue, a question, or a situation.
5. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
6. **Place exercise markers only** — do NOT write exercises directly. Place `<!-- INJECT_ACTIVITY: {id} -->` markers where exercises should appear. A separate pipeline step generates the actual exercises from the plan's activity_hints.
7. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
8. **Hit the word target** — you MUST write 1200–1800 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
9. **NO archaic, obsolete, or rare words** — use only modern standard Ukrainian. Do not use words marked as archaic (застаріле) or dialectal in dictionaries. Example: use «кін» not «кон», use «пом'якшені» not «м'якшені». When in doubt, choose the common modern form. Your pre-training contains Russian-influenced archaic forms — verify unfamiliar words.

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
module: a1-013
level: A1
sequence: 13
slug: many-things
version: '1.1'
title: Many Things
subtitle: Столи, книги, вікна — from one to many
focus: grammar
pedagogy: PPP
phase: A1.2 [My World]
word_target: 1200
objectives:
- Form nominative plurals of nouns learned in M08-M12
- Recognize the three main plural patterns (-и, -і, -а/-я)
- Use adjective plural form (-і) with plural nouns
- Describe groups of objects using plurals + adjectives + colors
dialogue_situations:
- setting: 'Setting up a classroom for a Ukrainian lesson — counting and arranging
    items. Singular → plural: один стілець → стільці, одна дошка → дошки, одне крісло
    → крісла. Also: олівці, ручки, підручники, карти.'
  speakers:
  - Вчитель (teacher)
  - Учні (students)
  motivation: 'Plurals with classroom items: стілець→стільці, дошка→дошки, крісло→крісла'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Describing a room (Вашуленко Grade 3 p.114-115): — Що тут є?
    — Столи, стільці і вікна. — Які столи? — Столи великі й нові. А стільці — старі.
    Plurals emerge naturally from describing a room full of things.'
  - 'Dialogue 2 — Shopping for several items (extending M11-M12): — У вас є ручки?
    — Так! Які ручки? Червоні чи сині? — Сині. І ще зошити. — Скільки? — Три зошити. Plural
    adjectives (-і) in real context.'
- section: Один → багато (Singular → Plural)
  words: 300
  points:
  - 'Большакова Grade 2 p.18: ''Один предмет → багато предметів.'' Three main plural
    patterns for nominative: Masculine → usually -и or -і: стіл → столи, стілець →
    стільці, телефон → телефони, зошит → зошити. Feminine → usually -и or -і: книга
    → книги, лампа → лампи, ручка → ручки, сумка → сумки. Neuter → usually -а or -я:
    вікно → вікна, ліжко → ліжка, крісло → крісла, дзеркало → дзеркала.'
  - 'Guideline (not a rule — exceptions exist): After г, к, х → -и (книга → книги,
    ручка → ручки). After most other consonants → -и or -і (стіл → столи, стілець
    → стільці). Neuter -о → -а (вікно → вікна). Neuter -е → -я (not covered yet).
    Full declension rules come later — for now, learn each plural with its noun.'
- section: Прикметники у множині (Adjectives in Plural)
  words: 300
  points:
  - 'Большакова Grade 2 p.42: який/яка/яке → які, веселий/весела/веселе → веселі.
    ALL adjectives take -і in the plural, regardless of gender: великий стіл → великі
    столи нова книга → нові книги чисте вікно → чисті вікна This is simpler than singular
    — one ending for all genders!'
  - 'Colors in plural (review M10): червоні ручки (red pens), сині зошити (blue notebooks),
    білі стіни (white walls), чорні стільці (black chairs). Demonstratives also have
    a plural form: ці (these) — Ці столи великі. Ці книги нові. ті (those) — Ті вікна
    чисті. Ті стільці старі.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Plural formation summary: Nouns: learn each plural individually (столи, книги,
    вікна). Adjectives: always -і (великі, нові, червоні, сині). Demonstratives: ці
    (these), ті (those). Possessives: мої (my — plural). Self-check: Make these plural
    — стіл, книга, вікно. Describe your classroom: Які столи? Які стільці? Які вікна?'
vocabulary_hints:
  required:
  - столи (tables — pl of стіл)
  - книги (books — pl of книга)
  - вікна (windows — pl of вікно)
  - стільці (chairs — pl of стілець)
  - ці (these — pl of цей/ця/це)
  - ті (those — pl of той/та/те)
  - мої (my — plural)
  - які (what kind? — plural)
  recommended:
  - ручки (pens — pl of ручка)
  - сумки (bags — pl of сумка)
  - лампи (lamps — pl of лампа)
  - зошити (notebooks — pl of зошит)
  - дзеркала (mirrors — pl of дзеркало)
  - крісла (armchairs — pl of крісло)
  - речі (things — pl of річ)
activity_hints:
- type: fill-in
  focus: 'Make it plural: стіл → столи, книга → книги, вікно → вікна'
  items: 10
- type: quiz
  focus: 'Choose the correct plural: стіл → столи/стола/столів?'
  items: 8
- type: fill-in
  focus: 'Adjective agreement in plural: нов__ книги, велик__ столи, чист__ вікна'
  items: 8
- type: group-sort
  focus: Sort words into однина (singular) and множина (plural)
  items: 12
connects_to:
- a1-014 (Checkpoint — My World)
prerequisites:
- a1-012 (This and That)
grammar:
- 'Nominative plural of nouns: -и/-і (m/f), -а/-я (n)'
- 'Adjective plural: always -і (великі, нові, червоні)'
- 'Plural demonstratives: ці (these), ті (those)'
- 'Plural possessive: мої (my)'
register: розмовний
references:
- title: Вашуленко Grade 3, p.114-115
  notes: 'Іменники мають два числа: однину і множину. Exercises with singular→plural.'
- title: Большакова Grade 2, p.18
  notes: Один предмет → багато предметів. First introduction of plural concept.
- title: Большакова Grade 2, p.42
  notes: 'Adjective singular/plural: який/яка/яке → які, веселий → веселі.'

</plan_content>

---

## Pre-Verified Facts (from MCP tools — use these, do NOT guess)

A verification step already called VESUM, textbooks, Правопис, and style guide tools. The results below are GROUND TRUTH. Use them:
- If a word is marked ❌ NOT IN VESUM — do NOT use it
- If a textbook excerpt is provided — use that pedagogy
- If a calque is flagged — use the correct alternative
- If CEFR says a word is above target — find a simpler synonym

You do NOT need to call tools yourself — the facts are already verified.

<pre_verified_facts>
## VESUM Verification

- **Confirmed (15/15):**
  столи (← стіл, noun), книги (← книга, noun), вікна (← вікно, noun), стільці (← стілець, noun), ці (← цей, adj), ті (← той, adj), мої (← мій, adj), які (← який, adj), ручки (← ручка, noun), сумки (← сумка, noun), лампи (← лампа, noun), зошити (← зошит, noun), дзеркала (← дзеркало, noun), крісла (← крісло, noun), речі (← річ, noun)

- **Not found:** none — all 15 plan vocabulary items are confirmed VESUM lemmas

---

## Textbook Excerpts

### Section: Один → багато (Singular → Plural)
> "Один предмет → багато предметів. [...] Ручка, гумка, книга, зошит, підручник, газета, журнал, словник, довідник, казка, вірш... До слова, яке називає один предмет, допиши слово, яке називає багато предметів за зразком. Зразок. Пенал — пенали, олівець — …"
> **Source:** Болшакова, Grade 2, p. 18 — **direct match for plan citation**

> "Іменники мають два числа: однину і множину. Іменники, які називають один предмет, уживаються в однині. Іменники, які називають два і більше предметів, уживаються у множині."
> **Source:** Вашуленко, Grade 3, p. 114 — confirms the definitional framing

### Section: Прикметники у множині (Adjectives in Plural)
> "Слова — назви ознак уживаються в однині й у множині. [Table:] який? яка? яке? → які? / веселий / весела / веселе / **веселі**"
> **Source:** Болшакова, Grade 2, p. 42 — **direct match for plan citation**; table explicitly shows all genders collapse to -і in plural

> [Zaharijchuk Grade 4 declension table] Plural Н.: "які?" — підтверджує єдине закінчення для всіх родів
> **Source:** Захарійчук, Grade 4, p. 67

### Section: Діалоги (Dialogues)
> [Room interior description] "Стіл і ясенові лави стояли на своїх місцях... Стояв широкий тапчан... Біля нього, під стіною, примостився столик... полискував жовтою дубовою фарбою дзеркальний гардероб..."
> **Source:** Заболотний, Grade 6, p. 241 — room description model with меблі vocabulary

> [Вітальня description] "Важкі меблі біля стіни рипіли... Невеликі видовжені вікна були розташовані майже під стелею... Біля каміна стояв невеличкий столик і два крісла."
> **Source:** Заболотний, Grade 6, p. 244 — крісла and вікна in natural room-description context

> ⚠️ **Note:** No exact Vashulenko Grade 3 p.114–115 room dialogue ("Що тут є? — Столи, стільці...") found in RAG. Plan cites this specifically; textbook chunk at p.114 contains the singular/plural grammar rule but not the room dialogue. **Recommend:** use the general classroom dialogue pattern confirmed by Болшакова Grade 2 + Zaharijchuk Grade 4 instead of citing Vashulenko p.114–115 for the dialogue specifically.

### Section: Підсумок — Summary
> [Числівник + іменник у множині context] "Привіт усім! Кому потрібні робочі зошити з української, відгукніться! [...] У нашому класі 24 учня/учні..."
> **Source:** Литвинова, Grade 6, p. 240 — confirms зошити in natural school purchase context, supports Dialogue 2

---

## Grammar Rules

- **Plural noun forms:** Правопис 2019 covers orthography (spelling), not morphological endings — no §number applies. Rule confirmed through textbook grammar instead: "Іменники, які називають два і більше предметів, уживаються у множині" (Вашуленко Grade 3 §35; Болшакова Grade 2 p.18). This is expected — Правопис §§ do not govern plural inflection patterns.

- **Adjective plural ending -і:** Правопис §33 governs adjective *suffixes* (spelling: -н-, -ичн-, -ист- etc.), not the nominative plural ending. The rule that ALL adjectives take **-і** in the nominative plural is confirmed by:
  - Болшакова Grade 2 p.42: веселий/весела/веселе → **веселі** (all genders → -і)
  - Заболотний Grade 6 p.143 full declension table: Plural Н. → **нові** / **сині**
  - Захарійчук Grade 4 p.67: plural question form consistently "які?" → -і ending

---

## Calque Warnings

- **"Що тут є?"** — OK. Natural Ukrainian locative question; confirmed in room-description text (Zaharijchuk Grade 4). No calque.
- **"У вас є ручки?"** — OK. Standard availability question; natural Ukrainian commerce phrase. No calque.
- **"Скільки?"** — OK. Natural Ukrainian quantity question. Антоненко-Давидович flags **"пара"** (пара днів) as a Russianism → should be "кілька"; plan correctly uses **скільки/три зошити**, not "пара зошитів". ✅
- **"Які столи? Столи великі й нові."** — OK. Predicate adjective construction is natural Ukrainian. No calque issue found.
- **"ще зошити"** (Dialogue 2: "І ще зошити") — OK. Natural additive construction in colloquial Ukrainian. No calque.

---

## CEFR Check

- **стіл:** A1 ✅
- **стілець:** A1 ✅
- **вікно:** A1 ✅
- **ручка:** A1 ✅
- **зошит:** A1 ✅
- **лампа:** A1 ✅
- **сумка:** A1 ✅
- **крісло:** A1 ✅
- **річ:** A1 ✅
- **книга:** A2 ⚠️ — PULS lists **книга** at A2; however **книжка** (diminutive/colloquial form) is listed at A1. Both words are standard Ukrainian. For strict A1.2 compliance, prefer **книжка** in module prose and activities, or accept книга as a known A2 item introduced in context.
- **дзеркало:** A2 ⚠️ — PULS lists дзеркало at A2. Usable in A1.2 as a stretch item (the plan introduces it as a plural pattern exemplar for neuter -о → -а), but flag for writer: introduce with explicit scaffolding, do not assume passive knowledge.
</pre_verified_facts>


## Knowledge Packet (textbook excerpts from RAG)

**MANDATORY — this is your primary source.** The knowledge packet contains real Ukrainian textbook excerpts. Your content MUST use the terminology, notation, and pedagogical approach from these excerpts.

**Hard rules for the knowledge packet:**
1. **Use Ukrainian terminology from the packet, not English linguistics.** If the textbook says «складоподіл», you write «складоподіл» — never CVCCV or "syllable division rules" paraphrased from English phonology. If it says «відкритий склад», you write «відкритий склад» — never "open syllable type."
2. **Adopt the textbook's teaching sequence.** If the packet shows: sound model → syllable → word → sentence, follow that progression. Do not rearrange or substitute your own.
3. **Include specific examples from the packet.** If the textbook uses «ка-ша», «мо-ло-ко» to teach syllable division, use those same words (and add more). Authentic examples beat invented ones.
4. **Your pre-training is contaminated by Russian and English linguistics.** When the packet contradicts your instinct, the packet wins. Ukrainian has its own phonetic categories (голосний/приголосний, дзвінкий/глухий, м'який/твердий) that do not map 1:1 to English or Russian. Use the Ukrainian categories.
5. **Before submitting, verify:** For every linguistic term you used, check — does it appear in the knowledge packet or plan? If you used a term that's NOT in the packet (e.g., "CVCCV", "onset", "coda"), replace it with the Ukrainian equivalent from the packet.

<knowledge_packet>
# Verified Knowledge Packet: Many Things
**Module:** many-things | **Phase:** A1.2 [My World]
**Textbook grades searched:** 1, 2, 3

---

## Діалоги (Dialogues)

> **Source:** bolshakova, Grade 2
> **Section:** Сторінка 71
> **Score:** 0.25
>
> 71
> виДи речень
> Порівняй речення. Чим вони схожі й чим відрізняються?
> Зайчик їсть капусту.  Що їсть зайчик?  Зайчику, їж капусту.
> Ти вимовляєш або пишеш речення з різною метою. 
> Ти можеш про щось розповідати, запитувати чи спо-
> нукати когось до дії. 
> Розповідні
> Питальні
> Спонукальні
> Речення
> Прочитай речення. Визнач вид речення за метою вислов-
> лювання. 
> Напиши 
> список 
> продуктів.
> У Данила 
> сьогодні день 
> народження.
> Ти йдеш 
> до школи?
> Скажи номер 
> телефону.
> Візьми 
> парасольку!
>  
> 1 
> 2

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 42
> **Score:** 0.50
>
> 42
> Члени речення
> Навчаюся розпізнавати члени речення
> Листочкиздеревопадаютьназемлю.
> Що опадає на землю?
> Що роблять листочки?
> З чого опадають листочки?
> Куди листочки опадають?
> Листочки.
> Опадають. 
> З дерев.
> На землю.
> Прочитай і розкажи 
> у класі.
> Я — учителька
> Я — учитель
> Слова в реченні, що відповідають 
> на 
> певні 
> питання, 
> називаються 
> членами речення.
> —	 Усі слова є членами речення.
> —	 Ні, я з тобою не можу погодитися! Хіба 
> є членами речення слова з, на? 
> Продовжте розмову.
> Хвилинка спілкування
> Слова з, на, в, у, про та інші, до яких не можна постави­ти 
> питання, слугують для того, щоб пов’язати між собою сло-
> ва в реченні, і вживаються з тими словами, які відповідають 
> на питання.
> Тихо осінь ходить гаєм.
> Ліс довкола аж горить.
> Ясен листя осипає.
> Дуб нахмурений стоїть.

## Один → багато (Singular → Plural)

> **Source:** bolshakova, Grade 2
> **Section:** Сторінка 18
> **Score:** 0.25
>
> 18
> оДнина І мноЖина
> Є слова — назви предметів, які називають один 
> предмет: м’яч 
> . Є слова — назви предметів, які 
> називають багато предметів: м’ячі 
> . 
> У гнома Буркотуна є чарівна паличка, яка може розмножу-
> вати предмети. Був один предмет — стало багато. Розглянь 
> малюнки. Над якими предметами Буркотун ще не чаклував? 
> Запиши слова за зразком.
> Зразок: пташка — пташки, … .
> один
> багато
>  
> До слова, яке називає один предмет, допиши слово, яке 
> називає багато предметів за зразком. Склади два речення 
> з однією парою слів. Виділені слова поділи для переносу.
> Зразок. Пенал — пенали, олівець — … .
> Ручка, гумка, книга, зошит, підручник, газета, журнал, 
> словник, довідник, казка, вірш, чаклун, гном.
>  
> Редагуємо
> 1. У гнома є чарівна палички. 2. Миша їли сир. 3.

> **Source:** bolshakova, Grade 2
> **Section:** Сторінка 73
> **Score:** 0.50
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

> **Source:** vashulenko, Grade 2
> **Section:** Сторінка 62
> **Score:** 0.33
>
> НАВЧАЮСЯ ЗМІНЮВАТИ СЛОВА — 
> НАЗВИ ПРЕДМЕТІВ
> Я — учителька
> Прочитай і розкажи 
> у класі.
> один — багато^
> Я — учитель
> В українській мові слова можуть називати один 
> предмет або багато предметів.
> тварина 
> рослина
> Додай свої 
> слова.
> 32| Випишіть із лічилки Тамари Коломієць слова — назви 
> предметів.
> один
> багато
> £ Що не так на 
> малюнку?
> Біжить півень із причілка 
> і наспівує лічилку:
> — Раз-два — курчата.
> Три-чотири — зайчата. 
> П'ять-шість — гусаки.
> Сім-вісім — їжаки. 
> Дев'ять-десять — йде лисиця. 
> Нам ховатись, їй жмуриться.
> г
> Причілок — бічна стіна будинку.
> І
> І
> І
> 62

## Прикметники у множині (Adjectives in Plural)

> **Source:** bolshakova, Grade 2
> **Section:** Сторінка 42
> **Score:** 0.50
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
> Я намалював 
> червоний будинок 
> із синім дахом 
> і зеленими дверима.
> Я намалював 
> дерев’яний будинок 
> із солом’яним дахом 
> і залізними дверима.
> Я намалював 
> сільський будинок 
> із важким дахом 
> і зручними дверима.
> 1 
> 2 
> 3

> **Source:** ponomarova, Grade 3
> **Section:** Сторінка 102
> **Score:** 0.25
>
> 102
> Довідка: неспокійне, розбурхане, суворе, 
> самотній, беззахисний, великі, небезпечні, 
> безпощадні,  тривожний.
> Довідка: радісний, задоволений, похнюплений, 
> сумний, щасливий, пригнічений.
> 10. Склади про одного з хлопчиків розповідь (3–4 речення) 
> і запиши. Використай прикметники.
> 1
> 4. Прочитай  розповідь  Ґаджика про картину І. Айвазов-
> ського.  Чи  зрозуміло,  яку  саме  картину  він  описав?
> 7. Якою частиною мови є вставлені в розповідь Ґаджика сло-
> ва? Зроби висновок про роль прикметників у мовленні.
> Море …, …, … . На морі …, … корабель. Його ото-
> чують …, …, … хвилі. Картина викликає … настрій.
> 5. Доповни розповідь Ґаджика словами з довідки і запиши. 
> 5
> 6. Прочитай утворений текст. Чи зрозуміло тепер, яку з кар-
> тин, зображених у завданні 2, описав Ґаджик? 
> 6
> 8. Розглянь малюнки.

## Підсумок — Summary

> **Source:** bolshakova, Grade 2
> **Section:** Сторінка 43
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
> • Чому не варто користуватися пла стиковими трубочками 
> для соку? Якої шкоди завдають природі пластикові ви-
> роби?
>  
> Запиши за зразком.
> Зразок. Лапа ведмедя — ведмежа лапа.
> Сукня з шовку — … . Хвіст зайця — … . 
> Квітка з паперу — … . Вуха лисиці — … . 
> Чашка зі скла — … .

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 22
> **Score:** 0.25
>
> 22
> Основна частина  
> (опис окремих 
> ознак)
> Навчаюся визначати частини тексту-опису,  
> будувати тексти-описи художні  
> і науково-популярні
> 	 	
> 1   Прочитайте текст. Доберіть до нього заголовок.
> Зачин
> (загальне враження)
> Кінцівка
> (підсумок) 
> Дивовижні це були птахи!
> Високі, майже людського зросту, на 
> тонких струнких ногах, із гнучкими довгими 
> шиями. Дзьоб також довгий і гострий, мов 
> кинджал. На голові біля дзьоба червона 
> пляма, помітна здалеку. Пір’я біле, наче сніг, 
> лише кінчики пір’їн — чорні.
> Ось вони які, білі журавлі-стерхи! 
> (За В. Флінтом). 
> 1. Гарна ця білочка. Червоно-кашта-
> нова шубка з білим трикутничком коло 
> підборіддя дуже їй личить. Невеличка 
> голівка, на довгеньких вушках прикра-
> си — чорні китички. Оченята в білоч­
> ки блискучі, мов дрібні намистинки.

## Grammar Reference


## МійКлас Theory (miyklas.com.ua)

*Ukrainian school curriculum theory — use this terminology and teaching approach.*

### Число іменників
> **Source:** МійКлас — [Число іменників](https://www.miyklas.com.ua/p/ukrainska-mova/6-klas/imennik-43064/chislo-imennikiv-43147)

### Теорія:

*www.ua.pistacja.tv*  
Іменники змінюються за числами: однина й множина.
Іменники, що означають **один предмет**, уживаються в однині.
Приклад:
Автомобіль, по

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Один → багато (Singular → Plural)` (~300 words)
- `## Прикметники у множині (Adjectives in Plural)` (~300 words)
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
- **Dialogues must sound like real people talking.** Test: would two Ukrainians actually say this to each other? If the dialogue sounds like a textbook drill ("Це кінь? — Так, це кінь."), rewrite it. Good dialogues have context, reactions, and personality:

  BAD (interrogation): "Це сім'я? — Так, це сім'я. — А де м'ясо? — М'ясо там."
  GOOD (natural): "Це твоя сім'я на фото? — Так! Нас п'ять. — А що ви їсте? М'ясо? — Так, дуже смачне!"

  BAD (labeling objects): "Це дуб. — А там коза. — Ні, це коса."
  GOOD (real reaction): "Дивись, який великий дуб! — Так, старий. А під ним — коза! — Смішна коза."

  Use the knowledge packet's textbook excerpts for dialogue patterns. Adapt real situations, don't invent drills.
- **DIALOGUE VARIETY — CRITICAL.** Each module MUST have DIFFERENT dialogue situations from other modules. Before writing any dialogue, check: have previous modules used this setting? If yes, pick a different one.

  BANNED recurring settings (already used in M01-M09): describing a room (кімната), looking at a table/bed/lamp, generic greetings with no context, labeling objects.

  REQUIRED: Every dialogue must have a SPECIFIC REAL-WORLD SITUATION that motivates the grammar being taught. The situation must be different from all other modules.

  **Module-specific dialogue settings (from plan):**
  1. **Setting up a classroom for a Ukrainian lesson — counting and arranging items. Singular → plural: один стілець → стільці, одна дошка → дошки, одне крісло → крісла. Also: олівці, ручки, підручники, карти.**
     Speakers: Вчитель (teacher), Учні (students)
     Why: Plurals with classroom items: стілець→стільці, дошка→дошки, крісло→крісла

  Use these settings. Do NOT substitute with a room description or generic greeting.
- **Tone: direct, clear, no filler.** State facts and teach. Don't praise the language ("beautiful", "wonderful", "unique melody"), don't praise the learner ("great job", "you've mastered"), don't narrate what you're doing ("In this section we will", "Now let's look at"). Just teach. Example:

  BAD: "The Ukrainian language has a wonderfully consistent and beautiful phonetic system."
  GOOD: "Ukrainian spelling is highly phonetic — what you see is what you hear."
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

**Required:** столи (tables — pl of стіл), книги (books — pl of книга), вікна (windows — pl of вікно), стільці (chairs — pl of стілець), ці (these — pl of цей/ця/це), ті (those — pl of той/та/те), мої (my — plural), які (what kind? — plural)
**Recommended:** ручки (pens — pl of ручка), сумки (bags — pl of сумка), лампи (lamps — pl of лампа), зошити (notebooks — pl of зошит), дзеркала (mirrors — pl of дзеркало), крісла (armchairs — pl of крісло), речі (things — pl of річ)

### Pronunciation Videos

**Do NOT embed YouTube videos in your prose.** A downstream ENRICH tool automatically places pronunciation videos from the plan. If you embed `<YouTubeVideo>` components, they will be duplicated. Simply reference the videos' existence when relevant (e.g., "Watch the pronunciation video for this letter") but do NOT insert `<YouTubeVideo>` tags.

Available videos (for reference only — ENRICH handles placement):


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

- P1 (~30 words): Scene-setter — Олена та Іван prepare a classroom for a Ukrainian lesson. Things are scattered everywhere; they name and count what they see.
- Dialogue 1 (~110 words): 6-turn exchange. Іван asks "Що тут є?" → Олена names objects in plural: "Столи, стільці і вікна." Іван follows up: "Які столи?" → Олена describes: "Столи великі й нові. А стільці — старі." Then: "А вікна?" → "Вікна чисті." Cover: стіл→столи, стілець→стільці, вікно→вікна; adjective plural великі, нові, старі, чисті in natural context.
- P2 (~20 words): Bridge sentence — now they need supplies; Олена checks the school supply cabinet.
- Dialogue 2 (~110 words): 7-turn shop-style exchange. Олена asks "У вас є ручки?" → "Так! Які ручки — червоні чи сині?" → "Сині. І ще зошити." → "Скільки зошитів?" → "Три зошити." → "А олівці є?" → "Є. Ось жовті олівці й чорні олівці." Cover: ручки, зошити, олівці; plural adjectives сині, жовті, чорні; numeral phrase три зошити.
- P3 (~60 words): Post-dialogue observation — point out that plurals emerged naturally: "one pen" became "pens", "one notebook" became "notebooks." Highlight the two patterns learners just heard: -и/-і for masculine/feminine, -а for neuter. Promise the next section will explain why.

---

## Один → багато (Singular → Plural) (~335 words total)

- P1 (~50 words): Concept intro — Ukrainian nouns have two numbers: однина (singular) and множина (plural). Cite Большакова Grade 2 p.18 framing: "один предмет → багато предметів." Use the image: один м'яч → м'ячі. Establish the three-pattern framework by gender.
- P2 (~80 words): Masculine nouns → -и or -і. Table of 6 pairs with gender marker: стіл (m) → столи; телефон (m) → телефони; зошит (m) → зошити; стілець (m) → стільці; олівець (m) → олівці; підручник (m) → підручники. Note: most masculine nouns take -и; nouns ending in soft consonant (стілець, олівець) take -і.
- P3 (~75 words): Feminine nouns → -и or -і. Table of 6 pairs: книга (f) → книги; ручка (f) → ручки; лампа (f) → лампи; сумка (f) → сумки; карта (f) → карти; дошка (f) → дошки. Guideline (not a rule): after г, к, х the vowel is -и (книга→книги, ручка→ручки, дошка→дошки).
- P4 (~65 words): Neuter nouns → -а. Table of 5 pairs: вікно (n) → вікна; крісло (n) → крісла; ліжко (n) → ліжка; дзеркало (n) → дзеркала; слово (n) → слова. Pattern is clean: drop -о, add -а. Practical tip: neuter plurals are the most predictable — learn this one and it covers most neuter nouns from M08-M12.
- P5 (~30 words): Honest caveat — Ukrainian plurals have exceptions (річ → речі). At A1, learn each plural alongside its singular as one unit. Full rules come at B1.
- Exercise 1 — fill-in (~35 words budget in prose): "Make it plural" cloze: 10 items cycling through all three patterns — стіл→___, книга→___, вікно→___, стілець→___, лампа→___, крісло→___, зошит→___, ручка→___, дзеркало→___, підручник→___. Items drawn from M08-M12 vocabulary.

---

## Прикметники у множині (Adjectives in Plural) (~330 words total)

- P1 (~55 words): Key insight — in singular, adjectives change ending by gender (великий/велика/велике). In plural, all genders collapse into one form: великі. Cite Большакова Grade 2 p.42: "який/яка/яке → які, веселий/весела/веселе → веселі." This is SIMPLER than singular — one ending rules them all.
- P2 (~70 words): Full paradigm drill for three adjectives learners already know. Three 3×1 tables: (1) новий стіл / нова книга / нове вікно → нові столи / нові книги / нові вікна. (2) великий стілець / велика лампа / велике крісло → великі стільці / великі лампи / великі крісла. (3) старий олівець / стара сумка / старе ліжко → старі олівці / старі сумки / старі ліжка.
- Exercise 2 — fill-in (~25 words budget in prose): Adjective agreement in plural: 8 gaps — нов__ книги, велик__ столи, чист__ вікна, стар__ стільці, красив__ лампи, мал__ крісла, довг__ олівці, нов__ зошити. Answer: always -і.
- P3 (~60 words): Colors in plural (review M10) — apply the -і rule: червоні ручки, сині зошити, білі стіни, чорні стільці, жовті олівці, зелені дошки. Reinforce that color adjectives follow the exact same pattern. Mini-exercise in prose: "Look around you — можеш описати? Які стільці? Які стіни? Яке ваше взуття?"
- P4 (~60 words): Demonstratives and possessives in plural. ці (these) — Ці столи великі. Ці книги нові. Ці вікна чисті. ті (those) — Ті стільці старі. Ті крісла червоні. мої (my-plural) — Мої ручки сині. Мої зошити нові. Note the pattern: цей/ця/це → ці; той/та/те → ті; мій/моя/моє → мої.
- Exercise 3 — quiz (~20 words budget in prose): "Choose the correct plural adjective" 8 items — e.g., "Великий стіл → великі/велика/великих столи?" Covers adjective agreement; 2 items per adjective type (descriptor, color, demonstrative, possessive).

---

## Підсумок — Summary (~325 words total)

- P1 (~70 words): Recap prose — three patterns learned today. Nouns: masculine/feminine → -и/-і (столи, книги, стільці); neuter → -а (вікна, крісла). Adjectives: always -і regardless of noun gender (великі столи / великі книги / великі вікна). Demonstratives: ці, ті. Possessive: мої. Stress the elegant economy: plural adjectives have ONE form — Ukrainian makes this easier than singular.
- Self-check questions (bulleted Q&A, ~90 words):
  - Як утворити множину від стіл? → столи
  - Як утворити множину від книга? → книги
  - Як утворити множину від вікно? → вікна
  - Як утворити множину від стілець? → стільці
  - Яке закінчення мають прикметники у множині? → завжди -і
  - Як сказати "these chairs"? → ці стільці
  - Як сказати "my pens"? → мої ручки
  - Утвори множину: великий стіл → ? → великі столи
- Exercise 4 — group-sort (~25 words budget in prose): Sort 12 words into two columns — однина (singular) vs. множина (plural): стіл, столи, книги, вікно, крісла, ручка, стільці, лампи, дзеркало, зошити, ліжко, сумки.
- P2 (~80 words): Production prompt — describe your own space using today's patterns. Scaffold: "Які столи у вашому класі/кімнаті? Які стільці? Які вікна? Які речі на вашому столі?" Give a model answer: "У моєму класі є великі столи і старі стільці. Вікна чисті. На моєму столі є сині ручки, нові зошити і маленький підручник." Invite the learner to write 3-4 sentences about their own room or classroom using plural nouns and plural adjectives.
- P3 (~60 words): Forward bridge — in M14 (Checkpoint) learners will use все they know from A1.2: rooms, objects, colors, numbers, this/that, and now plurals. Today's -і adjective plural will appear in every description from here on. Teaser: after checkpoint, A1.3 introduces verbs — and plurals matter there too (вони читають → вони читають книги).

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
