

---

## Your Writing Identity

**You are: Patient & Supportive Ukrainian Tutor.** Your persona is *The Helpful Teacher*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **30: My City** (A1, A1.5 [Places]).

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

1. **IMMERSION TARGET: 15-30% Ukrainian** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if you exceed it. For early modules, the learner CANNOT READ CYRILLIC — English must dominate. Ukrainian appears only as bolded inline words/phrases. Do NOT write long Ukrainian passages, Ukrainian-only paragraphs, or Ukrainian text without English translation.
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
module: a1-030
level: A1
sequence: 30
slug: my-city
version: '1.1'
title: My City
subtitle: Бібліотека, аптека, ресторан — city vocabulary
focus: vocabulary
pedagogy: PPP
phase: A1.5 [Places]
word_target: 1200
objectives:
- Name 15+ common city places (бібліотека, аптека, ресторан, etc.)
- Use locative case from M29 with city vocabulary
- Describe what you do at each place (combining verbs from A1.3)
- Give simple directions using є (there is) and тут/там
dialogue_situations:
- setting: 'Drawing a map of your Kyiv neighborhood for a pen pal — marking: бібліотека
    (f), музей (m, museum), площа (f, square), озеро (n, lake), зупинка (f, bus stop),
    церква (f, church). Use біля, поруч з, далеко від for distances.'
  speakers:
  - Аліна (describing)
  - Ігор (asking questions)
  motivation: City vocab with бібліотека(f), музей(m), площа(f), озеро(n)
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — New in the city: — Вибачте, де тут аптека? — Аптека на вулиці Шевченка.
    — А бібліотека? — Бібліотека в центрі, біля парку. — Дякую! — Будь ласка! City
    places in asking-for-directions context.'
  - 'Dialogue 2 — My neighborhood: — Що є біля твого дому? — Біля дому є магазин і
    кафе. — А школа? — Школа далеко, у центрі міста. Review: в/на + locative for all
    places.'
- section: Місця в місті (City Places)
  words: 300
  points:
  - 'Essential city vocabulary: аптека (pharmacy), бібліотека (library), лікарня (hospital),
    магазин (shop), супермаркет (supermarket), ресторан (restaurant), кафе (café),
    банк (bank), пошта (post office), вокзал (train station), готель (hotel), музей
    (museum), театр (theater), кінотеатр (cinema), церква (church), стадіон (stadium),
    університет (university).'
  - 'Each place with its preposition (locative from M29): в аптеці, у бібліотеці,
    у лікарні, в магазині, у ресторані, у кафе, у банку, на пошті, на вокзалі, у готелі,
    в музеї. What you do there: Я купую ліки в аптеці. Я читаю в бібліотеці. Я працюю
    в офісі. Я відпочиваю в парку.'
- section: Де це? (Where Is It?)
  words: 300
  points:
  - 'Location words: тут (here), там (there), далеко (far), близько (near/close),
    біля + gen (near — as chunk: біля парку, біля дому), у центрі (in the center),
    на розі (on the corner). Note: біля requires genitive — learn as chunks, not grammar.'
  - 'Describing your city: У моєму місті є великий парк і два музеї. Бібліотека біля
    університету. Магазин тут, біля дому. Note: є = ''there is/are'' (already used
    since M06).'
- section: Підсумок — Summary
  words: 300
  points:
  - 'City vocabulary with prepositions: В/у: аптеці, бібліотеці, магазині, банку,
    готелі, ресторані. На: пошті, вокзалі, стадіоні, площі. Location words: тут, там,
    далеко, близько, біля. Self-check: Name 5 places near your home. What do you do
    there?'
vocabulary_hints:
  required:
  - аптека (pharmacy, f)
  - бібліотека (library, f)
  - магазин (shop, m)
  - ресторан (restaurant, m)
  - готель (hotel, m)
  - вокзал (train station, m)
  - тут (here)
  - там (there)
  recommended:
  - лікарня (hospital, f)
  - супермаркет (supermarket, m)
  - пошта (post office, f)
  - музей (museum, m)
  - церква (church, f)
  - далеко (far)
  - близько (near)
  - біля (near — + genitive chunk)
activity_hints:
- type: match-up
  focus: 'Match place to activity: аптека ↔ купувати ліки'
  items: 8
- type: quiz
  focus: В or на? Choose preposition for city places.
  items: 8
- type: fill-in
  focus: 'Describe your city: У моєму місті є ___.'
  items: 6
- type: quiz
  focus: Where would you go? Choose the right place for each situation.
  items: 6
connects_to:
- a1-031 (Where To?)
prerequisites:
- a1-029 (Where Is It?)
grammar:
- City vocabulary with locative prepositions (в/на + М.в.)
- 'Location expressions: тут, там, далеко, близько, біля'
- Є = there is/are
register: розмовний
references:
- title: Anna-led module — city vocabulary through practical situations
  notes: No single textbook source — vocabulary compiled from multiple textbook city
    themes.

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
- **Confirmed (16/16):** аптека (noun), бібліотека (noun), магазин (noun), ресторан (noun), готель (noun), вокзал (noun), тут (adv), там (adv/part), лікарня (noun), супермаркет (noun), пошта (noun), музей (noun), церква (noun), далеко (adv), близько (adv/prep), біля (prep)
- **Not found:** — (all 16 plan vocabulary words confirmed in VESUM)

---

## Textbook Excerpts

### Section: Місця в місті (City Places)
> "У містах є музеї, театри, супермаркети. Вулицями міст їздять тролейбуси, трамваї, автобуси, маршрутні таксі."
> **Source:** Bolshakova, Grade 1 (Буквар, tier 2) — primary vocabulary introduction of city institutions. Confirms: музей, театр, супермаркет are all Grade 1-level words.

### Section: Де це? (Where Is It?) — прийменники в/на
> "Прийменник **на** вживають з назвами установ, приміщень: **пошта** → *піти на пошту*; **вокзал** → *приїхати на вокзал*. З рештою просторових іменників вживають прийменник **в (у)**: зайти **в** школу, побувати **у** Франції."
> **Source:** Avramenko, Grade 11 (tier 2), §§ prepositions в і на — authoritative rule table for в vs на with spatial nouns. Directly confirms на пошті / на вокзалі vs в аптеці / у бібліотеці.

### Section: Де це? — location words тут/там/біля
> "Прийменник можна замінити синонімічним, не порушивши змісту: жити **край лісу** (**біля лісу**)"
> "До джерела було вже **близько**" (pronominal adverb vs preposition distinction)
> **Source:** Avramenko, Grade 7 (tier 1) — confirms **біля** (simple preposition) and **близько** (adverb/preposition) as core Ukrainian spatial vocabulary.

### Section: Діалоги — address & street context
> "Назви вулиць пишуться з великої букви. Вулиця, **біля якої парк** — Паркова вулиця."
> "Як називається вулиця, **на якій** ти живеш? — вулиця Сумська, будинок 21"
> **Source:** Bolshakova, Grade 2 (tier 2) — confirms на вулиці + genitive street name (вулиці Шевченка) as the natural form for dialogue context. Validates Dialogue 1 model: *Аптека на вулиці Шевченка.*

### Section: в/на + Locative (grammar rule)
> "Прийменник в (у) уживають з іменниками, що позначають **види навчальних закладів**: у школі, у коледжі. Прийменник **на** вживають з іменниками, що позначають **вулиці, проспекти, площі**: на проспекті Миру, на вулиці Басейній."
> **Source:** Glazova, Grade 11 (tier 2), §16 — confirms на вулиці rule, validates the plan's preposition summary table.

---

## Grammar Rules

- **в/у vs на with locative nouns:** Правопис §23 — alternation of у/в based on surrounding consonant/vowel context (милозвучність). Use **у** before consonant clusters (у бібліотеці, у лікарні), **в** before vowels (в аптеці). Rule confirmed across Avramenko Gr.11, Glazova Gr.11.
- **на пошті / на вокзалі** (not *в пошті / в вокзалі*): Confirmed by Avramenko Gr.11 preposition table — ці іменники belong to the "на" category (чітко обмежений простір / установи типу пошта, вокзал).
- **на вулиці [Name]**: Street names take на (not в), confirmed Glazova Gr.11 §16.
- **біля + genitive:** Confirmed as standard preposition; Grade 4 Zakharichuk explicitly notes місцевий відмінок uses прийменники, and Grade 7 Avramenko lists біля among simple prepositions with genitive.

---

## Calque Warnings

- **"знаходитися" for location** (e.g., *Де знаходиться аптека?*): **CALQUE** ⚠️ — Антоненко-Давидович (ad-148) is explicit: this is a direct calque from Russian *находиться*. Ukrainian natural alternatives: **є** (*Де є аптека?*), **стоїть** (*Аптека стоїть на розі*), or simply drop the verb (*Аптека — на вулиці Шевченка*). **The plan correctly avoids this** — it uses *де тут аптека?* and *є біля*. ✅ But the module writer must NOT introduce *знаходиться*.
- **"розташована/розташований"** for buildings/cities: **CALQUE** ⚠️ — Антоненко-Давидович (ad-176): *розташуватися* applies only to people/military units temporarily settling, NOT buildings or cities. Do not write *Бібліотека розташована в центрі* — use *Бібліотека є в центрі* / *Бібліотека — у центрі міста*.
- **"біля дому"**: ✅ OK — standard Ukrainian. Антоненко-Давидович raises no objection to this preposition use.
- **"відпочиваю в парку"**: ✅ OK — *відпочивати* is a legitimate Ukrainian verb. Style guide only flags the deverbal noun *відпочиваючий* (calque), not the verb itself.

---

## CEFR Check

- **аптека**: A1 ✅ — correct level
- **бібліотека**: A1 ✅ — correct level
- **вокзал**: A1 ✅ — correct level
- **супермаркет**: A1 ✅ — correct level
- **музей**: A1 ✅ — correct level
- **церква**: A1 ✅ — correct level
- **магазин**: A1 ✅ (confirmed via супермаркет lookup which returned магазин at A1)
- **No words above A1 target** among the plan vocabulary checked.

**Bonus note:** *поліклініка* (returned as near-match for аптека) is A2 — not in the plan, but avoid using it in the module. *Храм* (near-match for церква) is B1 — use *церква* only.
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
# Verified Knowledge Packet: My City
**Module:** my-city | **Phase:** A1.5 [Places]
**Textbook grades searched:** 4, 5, 6

---

## Діалоги (Dialogues)

> **Source:** zabolotnyi, Grade 6
> **Section:** Сторінка 85
> **Score:** 0.50
>
> Запишіть, дотримуючись правил уживання великої букви та лапок. Йогурт (в)олошкове (п)оле, (с)пасо-(п)реображенський (с)обор 
> (Чернігів), (д)омініканський (с)обор (Львів), (м)узей історії Ки-
> єва, (к)омета (г)аллея, вебсайт (ш)коляр, (з)ахідне (п)оділля,
> (д)ень (п)сихолога, автомобіль (т)есла, станція метро (п)окров-
> ська, (ф)ранцузька (р)еспубліка, (г)алактика (с)пляча (к)расуня, 
> вулиця (с)ічових (с)трільців, (к)ерченська (п)ротока. 225 
> 226 
> 227 
> 228
> 229
> 230
> 231

> **Source:** zabolotnyi, Grade 6
> **Section:** Сторінка 228
> **Score:** 0.25
>
> 228
> Розвиток мовлення
> мовленнєвого етикету. Використайте звертання та слова (сполучення) увічли-
> вості. Ви можете скористатися поданими нижче зразками.
> СИТУАЦІЯ А. Ви перебуваєте в незнайомому місті й шукаєте потрібну вулицю 
> (будівлю). З якими словами ви звернетеся до перехожого? Що скажете на про-
> щання?
> Скажіть, будь ласка, де...; перепрошую, ви не знаєте...; вибачте, 
> ви не скажете...; добродію, будьте ласкаві, підкажіть...; шановний, 
> якщо ваша ласка, скажіть мені...; дякую вам; на все добре; 
> приємної подорожі; чи не скажете ви...; вибачте, точно не знаю; 
> ви мені дуже допомогли; до побачення; немає за що.
> СИТУАЦІЯ Б. Ви зайшли до книгарні й хочете купити тлумачний словник.

## Місця в місті (City Places)

> **Source:** zabolotnyi, Grade 6
> **Section:** Сторінка 85
> **Score:** 0.50
>
> Запишіть, дотримуючись правил уживання великої букви та лапок. Йогурт (в)олошкове (п)оле, (с)пасо-(п)реображенський (с)обор 
> (Чернігів), (д)омініканський (с)обор (Львів), (м)узей історії Ки-
> єва, (к)омета (г)аллея, вебсайт (ш)коляр, (з)ахідне (п)оділля,
> (д)ень (п)сихолога, автомобіль (т)есла, станція метро (п)окров-
> ська, (ф)ранцузька (р)еспубліка, (г)алактика (с)пляча (к)расуня, 
> вулиця (с)ічових (с)трільців, (к)ерченська (п)ротока. 225 
> 226 
> 227 
> 228
> 229
> 230
> 231

> **Source:** avramenko, Grade 6
> **Section:** Сторінка 81
> **Score:** 0.33
>
> назви транспортних засобів, 
> магазинів і виробів
> літак «Мрія», мотоцикл «Ява», су-
> пермаркет «Сільпо», печиво «Дніпро» 
> назви 
> періодичних 
> видань, 
> мистецьких творів
> журнал «Vo­gue», газета «Порад­ни­
> ця», повість «Климко», мульт­фільм 
> «Рататуй»
> Потрібно розрізняти загальні назви й утворені від них умовні власні 
> назви: біла церква (храм білого кольору) — Біла Церква (місто); сві-
> тить сонечко — дитсадок «Сонечко». Назви періодичних видань, мистецьких творів і виробів, а також умов­
> ні назви пишемо з великої букви та в лапках: часопис «Дніпро», пісня 
> «Червона рута», цукерки «Ліщина».

## Де це? (Where Is It?)

> **Source:** zaharijchuk, Grade 4
> **Section:** Сторінка 129
> **Score:** 0.33
>
> 129
> 	 Запиши прислівники, написані прописним шрифтом. Зверни 
> увагу: не з прислівниками переважно пишемо разом, якщо до 
> них можна дібрати синоніми. Наприклад: недалеко — близько, 
> недобре — погано. 
> 309.		Прочитай текст.  
> У закутку саду, там, де сиро та вогко, самотньо мешкав 
> стоножич Томас. Жуки, черв’яки, слимаки й інша дрібнота 
> дуже поважали його. Томас легко й граційно переставляв 
> свої дев’яносто шість ніг. Чотири ноги він, на жаль, загу-
> бив, невідомо де. 
> Томас (не)дріботів, (не)виступав, (не)марширував, 
> (не)плазував. Він тихо котився на оксамитових коліщат-
> ках. Щоразу неочікувано навідувався у вогкі закутки саду 
> й незалежно оглядав знайомі місця (За Дж. Крюсом).
> 	 Поясни правопис не з дієсловами. Випиши перше речення дру-
> гого абзацу, розкриваючи дужки.

> **Source:** zaharijchuk, Grade 4
> **Section:** Сторінка 20
> **Score:** 0.50
>
> 20
> близько, — його домівка. Я зарубав на носі, як поводи-
> тися із цим красенем! (За В. Перепелюком).
> 	 Спиши текст, замінюючи підкреслені сполучення слів фразео-
> логізмами з вправи 43. Поясни значення виділеного фразеоло-
> гізму.
> 46.		Прочитай фразеологізми. З’єднай їх із відповідними зна-
> ченнями, запиши. Скористайся словником фразеологізмів.
> Ані рудої миші; берегти як зіницю ока; блудити словами; 
> дірка від бублика; з дорогою душею; накивати п’ятами.
> Старанно доглядати; безлюдно; говорити без потре-
> би; немає нічого; із задоволенням; утекти.
> 47.		Розгляньте діаграму. Обговоріть її зміст. Визначте, що ви 
> вже вивчили із цього розділу, а що будете вивчати.

## Підсумок — Summary

> **Source:** zabolotnyi, Grade 6
> **Section:** Сторінка 85
> **Score:** 0.50
>
> Запишіть, дотримуючись правил уживання великої букви та лапок. Йогурт (в)олошкове (п)оле, (с)пасо-(п)реображенський (с)обор 
> (Чернігів), (д)омініканський (с)обор (Львів), (м)узей історії Ки-
> єва, (к)омета (г)аллея, вебсайт (ш)коляр, (з)ахідне (п)оділля,
> (д)ень (п)сихолога, автомобіль (т)есла, станція метро (п)окров-
> ська, (ф)ранцузька (р)еспубліка, (г)алактика (с)пляча (к)расуня, 
> вулиця (с)ічових (с)трільців, (к)ерченська (п)ротока. 225 
> 226 
> 227 
> 228
> 229
> 230
> 231

## Grammar Reference

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 238
> **Score:** 0.25
>
> 235
> ДОДАТКИ
> Додаток 1
> СЛОВНИЧОК СИНОНІМІВ
> БЛИЗЬКО, недалеко, поблизу, неподалiк, пiд носом, рукою подати, 
> не за горами. БОЯЗКИЙ, несмiливий, полохливий, лякливий, легкодухий, розм. страхопудний. ВВIЧЛИВИЙ, чемний, вихований, коректний, тактовний, ґpечний. ГОВОРИТИ (передавати словами думки, повідомляти), казати, 
> промовляти, проказувати, балакати, мовити, повідати, поет. ректи, 
> розм. цідити. ГОРИЗОНТ, обрій, круговид, виднокруг, виднокрай, крайнебо, овид, 
> небосхил, небокрай. ДОРОГА, шлях, путь, шосе, траса, автострада, розм. гостинець, путі-
> вець. ДУМАТИ, мислити, розмiрковувати, роздумувати, мiркувати, мати 
> на думці, розм. кумекати, розм. метикувати, розм. мiзкувати. ЗАВЖДИ, повсякчас, завше, постiйно, день i нiч, будь-коли, доки 
> cвіт стоїть, хоч коли.

> **Source:** zaharijchuk, Grade 4
> **Section:** Сторінка 129
> **Score:** 0.33
>
> 129
> 	 Запиши прислівники, написані прописним шрифтом. Зверни 
> увагу: не з прислівниками переважно пишемо разом, якщо до 
> них можна дібрати синоніми. Наприклад: недалеко — близько, 
> недобре — погано. 
> 309.		Прочитай текст.  
> У закутку саду, там, де сиро та вогко, самотньо мешкав 
> стоножич Томас. Жуки, черв’яки, слимаки й інша дрібнота 
> дуже поважали його. Томас легко й граційно переставляв 
> свої дев’яносто шість ніг. Чотири ноги він, на жаль, загу-
> бив, невідомо де. 
> Томас (не)дріботів, (не)виступав, (не)марширував, 
> (не)плазував. Він тихо котився на оксамитових коліщат-
> ках. Щоразу неочікувано навідувався у вогкі закутки саду 
> й незалежно оглядав знайомі місця (За Дж. Крюсом).
> 	 Поясни правопис не з дієсловами. Випиши перше речення дру-
> гого абзацу, розкриваючи дужки.


## МійКлас Theory (miyklas.com.ua)

*Ukrainian school curriculum theory — use this terminology and teaching approach.*

### Прийменник як службова частина мови
> **Source:** МійКлас — [Прийменник як службова частина мови](https://www.miyklas.com.ua/p/ukrainska-mova/7-klas/priimennik-48228/priimennik-iak-sluzhbova-chastina-movi-nepokhidni-i-pokhidni-priimenniki-48229)

### Теорія:

*www.ua.pistacja.tv*  
**Прийменник** — службова незмінна частина мови, що виражає відношення між предметами, відношення дії та ознаки до предмета, залежність іменника, числівника, займенника від інших слів у реченні і разом з ними вказує на об’єкт дії, напрям, місце, час, причину, мету.
Приклад:
Ще ****в ****дитинстві я ходив ****у**** трави, ****в**** гомінливі трепетні ліси…\(В.

### Словосполучення з прийменником ПО
> **Source:** МійКлас — [Словосполучення з прийменником ПО](https://www.miyklas.com.ua/p/ukrainska-mova/11-klas/sintaksichna-norma-380223/slovospoluchennia-z-priimennikom-po-380391)

### Теорія:
Прийменник **по** вживають, коли треба вказати

Зверни увагу\!
При

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Місця в місті (City Places)` (~300 words)
- `## Де це? (Where Is It?)` (~300 words)
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
  1. **Drawing a map of your Kyiv neighborhood for a pen pal — marking: бібліотека (f), музей (m, museum), площа (f, square), озеро (n, lake), зупинка (f, bus stop), церква (f, church). Use біля, поруч з, далеко від for distances.**
     Speakers: Аліна (describing), Ігор (asking questions)
     Why: City vocab with бібліотека(f), музей(m), площа(f), озеро(n)

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

**Required:** аптека (pharmacy, f), бібліотека (library, f), магазин (shop, m), ресторан (restaurant, m), готель (hotel, m), вокзал (train station, m), тут (here), там (there)
**Recommended:** лікарня (hospital, f), супермаркет (supermarket, m), пошта (post office, f), музей (museum, m), церква (church, f), далеко (far), близько (near), біля (near — + genitive chunk)

### Pronunciation Videos

**Do NOT embed YouTube videos in your prose.** A downstream ENRICH tool automatically places pronunciation videos from the plan. If you embed `<YouTubeVideo>` components, they will be duplicated. Simply reference the videos' existence when relevant (e.g., "Watch the pronunciation video for this letter") but do NOT insert `<YouTubeVideo>` tags.

Available videos (for reference only — ENRICH handles placement):


---

### Style Reference (match this tone and structure)

> **(У магазині / At the store)**
> — Добрий день! Скільки коштує хліб? (Good day! How much does the bread cost?)
> — Дванадцять гривень. (Twelve hryvnias.)
> — Дякую! Ось, будь ласка. (Thanks! Here you go.)

Notice that the shopkeeper uses **Добрий день** — the formal greeting for strangers. If this were a friend, they would say **Привіт** instead.

The word **скільки** (how much/how many) is one of the most useful question words. It always pairs with the genitive case: **скільки коштує** (how much does it cost), **скільки часу** (how much time).

*Note: Short dialogues in Ukrainian with per-line English glosses. Grammar explained in English. Ukrainian sentences in blockquotes and bulleted lists.*



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
## Діалоги (~330 words total)

- D1 (~110 words): Dialogue "New in the city" — Аліна asks a stranger for directions. 6–7 turns: — Вибачте, де тут аптека? — Аптека на вулиці Шевченка, біля парку. — А бібліотека? — Бібліотека в центрі міста. — Це далеко? — Ні, близько. — Дякую! — Будь ласка! Introduces аптека, бібліотека, вулиця, центр; prepositions на + loc, в + loc; location adverbs далеко/близько. Polite register modelled on Заболотний Gr.6 p.228: Вибачте / Будь ласка.

- D2 (~110 words): Dialogue "My neighborhood" — Ігор and Аліна compare neighborhoods. 6–7 turns: — Що є біля твого дому? — Біля дому є магазин і кафе. — А лікарня? — Лікарня там, далеко від центру. — У тебе є стадіон? — Так, стадіон на вулиці Лесі Українки. Introduces магазин, кафе, лікарня, стадіон; biля + gen as chunk; є = there is/are (recycled from M06).

- P3 (~30 words): One-sentence bridge: these two dialogues use place names in context — now meet all the city vocabulary in full.

- P4 (~80 words): Cultural note — Ukrainian city landmarks. Every місто has: ринок (market square), площа (square), вокзал, пошта. Kyiv's iconic Хрещатик — the main вулиця. Short paragraph grounding vocabulary in real Ukrainian urban geography; names: Майдан Незалежності, Хрещатик, Львівська площа.

---

## Місця в місті (~330 words total)

- P1 (~90 words): Full city vocabulary — 17 places with gender labels. Present as a paired list (Ukrainian → English → gender): аптека (pharmacy, f), бібліотека (library, f), лікарня (hospital, f), пошта (post office, f), церква (church, f), зупинка (bus stop, f) / магазин (shop, m), супермаркет (supermarket, m), ресторан (restaurant, m), банк (bank, m), вокзал (train station, m), готель (hotel, m), музей (museum, m), театр (theatre, m), кінотеатр (cinema, m), стадіон (stadium, m), університет (university, m) / кафе (café, n). Genders flagged because locative endings differ.

- P2 (~90 words): Locative forms — two prepositions rule. В/у: аптека → в аптеці, бібліотека → у бібліотеці, магазин → в магазині, банк → у банку, готель → у готелі, ресторан → у ресторані, музей → в музеї, університет → в університеті. На: пошта → на пошті, вокзал → на вокзалі, стадіон → на стадіоні, зупинка → на зупинці. Pattern note: на is used for transit and service infrastructure — пошта, вокзал, стадіон, зупинка. All other places use в/у.

- Exercise: **quiz** — В or на? 8 items (аптека, пошта, вокзал, бібліотека, стадіон, готель, зупинка, музей). Learner chooses preposition; immediate feedback with rule reminder.

- P3 (~100 words): What you do there — 8 full sentences modelling verb + place in locative: Я купую ліки в аптеці. Я читаю книги у бібліотеці. Я їм піцу в ресторані. Я п'ю каву в кафе. Я надсилаю листи на пошті. Я дивлюся фільм у кінотеатрі. Я відпочиваю в парку. Я їду додому на вокзалі. Recycled verbs from A1.3 (купую, читаю, їм, п'ю) in new locative context.

- Exercise: **match-up** — Match place to activity. 8 pairs: аптека ↔ купувати ліки, бібліотека ↔ читати книги, ресторан ↔ їсти, кінотеатр ↔ дивитися фільм, вокзал ↔ їхати потягом, банк ↔ міняти гроші, стадіон ↔ грати у футбол, пошта ↔ надсилати листи.

---

## Де це? (~330 words total)

- P1 (~70 words): Core location adverbs — four words, four contrasts. Тут (here) vs там (there): Аптека тут. Вокзал там. Далеко (far) vs близько (near): Університет далеко від дому. Магазин близько. Short table-style paragraph with 6 example sentences using all four adverbs in city contexts. Note: недалеко = близько (synonym from Заболотний Gr.5 Synonyms appendix).

- P2 (~90 words): Biля + genitive — teach as memorized chunks, not grammar. Rule stated simply: biля завжди + родовий відмінок — but we learn it as fixed phrases: біля парку (near the park), біля дому (near the house), біля університету (near the university), біля вокзалу (near the station), біля кафе (near the café — indeclinable). Six example sentences: Аптека біля парку. Музей біля університету. Зупинка біля вокзалу. Магазин біля мого дому. Grammar box: кафе never changes — біля кафе, у кафе, near any case.

- P3 (~70 words): У центрі / на розі / у районі. Three location phrases for describing neighborhood position: у центрі міста (in the city center), на розі вулиці (on the corner of the street), у нашому районі (in our neighborhood). Introduced via three contrasting sentences: Театр у центрі міста. Аптека на розі вулиці Шевченка. Бібліотека у нашому районі.

- P4 (~60 words): Describing your city with є. Construction: У + city/place + є + noun: У Києві є метро. У нашому місті є великий парк і два музеї. У цьому районі є стадіон і кінотеатр. Є recycled from M06 — now used with city places. Negative: Біля мого дому немає вокзалу.

- Exercise: **quiz** — Where would you go? 6 situations: "You need medicine" → аптека; "You want to watch a film" → кінотеатр; "Your train departs at 9:00" → вокзал; "You want to borrow a book" → бібліотека; "You want to eat dinner" → ресторан; "You want to send a parcel" → пошта.

---

## Підсумок (~330 words total)

- P1 (~80 words): City vocabulary recap organized by preposition. В/у: аптека → в аптеці, бібліотека → у бібліотеці, лікарня → у лікарні, магазин → в магазині, банк → у банку, готель → у готелі, ресторан → у ресторані, музей → в музеї, університет → в університеті, кінотеатр → у кінотеатрі. На: пошта → на пошті, вокзал → на вокзалі, стадіон → на стадіоні, зупинка → на зупинці. Pattern rule restated: на = transit + service infrastructure.

- P2 (~60 words): Location words bullet recap. тут — here | там — there | далеко — far | близько / недалеко — near | біля + gen — next to | у центрі — in the center | на розі — on the corner | у районі — in the neighborhood. Each with a one-phrase example: Магазин тут. Вокзал там. Університет далеко. Парк близько. Аптека біля дому.

- P3 (~70 words): Self-check — bulleted Q&A list (not prose):
  - Де ти купуєш ліки? → В аптеці.
  - Де ти їси? → У ресторані / у кафе.
  - Де ти читаєш книги? → У бібліотеці.
  - Де ти їдеш на потязі? → З вокзалу.
  - Що є біля твого дому? → Біля мого дому є … (learner fills in).
  - Твій університет далеко чи близько? → (open answer).

- Exercise: **fill-in** — Describe your city. 6 sentence starters with blanks: У моєму місті є ___. Біля мого дому є ___. Я купую продукти ___. Вокзал ___ від мого дому. Театр ___. Я люблю відпочивати ___.

- P4 (~50 words): Preview bridge — one short paragraph. You now know where things are. Next module (M31 — Where To?) introduces куди — movement toward places using accusative: Я іду до бібліотеки. Я їду на вокзал. The same places, a new question: not де (location) but куди (destination).

- Exercise: **quiz** — 6-item mixed review: 3 vocabulary (Ukrainian → meaning) + 3 grammar (choose locative or genitive in context). Covers: в аптеці vs до аптеки, biля парку, У нашому місті є ___.

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
