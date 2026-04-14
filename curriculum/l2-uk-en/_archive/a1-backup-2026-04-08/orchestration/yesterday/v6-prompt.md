

---

## Your Writing Identity

**You are: Patient & Supportive Ukrainian Tutor.** Your persona is *The Helpful Teacher*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **49: Yesterday** (A1, A1.8 [Past, Future, Graduation]).

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

1. **IMMERSION TARGET: 20-35% Ukrainian** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if you exceed it. For early modules, the learner CANNOT READ CYRILLIC — English must dominate. Ukrainian appears only as bolded inline words/phrases. Do NOT write long Ukrainian passages, Ukrainian-only paragraphs, or Ukrainian text without English translation.
2. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
3. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
4. **NO "In this lesson we will..."** — never use formulaic openers. Start with a dialogue, a question, or a situation.
5. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
6. **Place exercise markers only** — do NOT write exercises directly. Place `<!-- INJECT_ACTIVITY: {id} -->` markers where exercises should appear. A separate pipeline step generates the actual exercises from the plan's activity_hints.
7. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
8. **Hit the word target** — you MUST write 1200–1800 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
9. **NO archaic, obsolete, or rare words** — use only modern standard Ukrainian. Do not use words marked as archaic (застаріле) or dialectal in dictionaries. Example: use «кін» not «кон», use «пом'якшені» not «м'якшені». When in doubt, choose the common modern form. Your pre-training contains Russian-influenced archaic forms — verify unfamiliar words.
10. **EVERY module MUST end with `## Підсумок`** — this is the last H2 section before the file ends. It contains a self-check recap. If you forget this section, the audit REJECTS the module and you waste a retry. Write it LAST, after all other sections.

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
module: a1-049
level: A1
sequence: 49
slug: yesterday
version: '1.2'
title: Yesterday
subtitle: Учора я прокинувся, поснідав і пішов — narrating your day
focus: communicative
pedagogy: PPP
phase: A1.8 [Past, Future, Graduation]
word_target: 1200
objectives:
- Narrate a complete past day using sequenced past-tense verbs
- Use time markers to structure a narrative (зранку, вдень, ввечері)
- Combine past tense with known vocabulary (food, places, people)
- Tell a short personal story about yesterday
dialogue_situations:
- setting: 'Police report — describing a stolen велосипед (m, bicycle): Я припаркував
    велосипед біля магазину (m). Потім зайшов у кав''ярню (f). Коли вийшов, велосипед
    зник. Бачив чоловіка (m) в куртці (f) та кепці (f, cap).'
  speakers:
  - Свідок (witness)
  - Поліцейський
  motivation: Past narration with велосипед(m), магазин(m), кав'ярня(f), куртка(f)
content_outline:
- section: Dialogues
  words: 300
  points:
  - Dialogue 1 — How was your day? — Як пройшов твій день? — Добре! Зранку я прокинувся
    о сьомій. — Що ти робив зранку? — Я поснідав і пішов на роботу. — А вдень? — Вдень
    я працював і обідав з колегою. — А ввечері? — Ввечері я дивився фільм і рано ліг
    спати. Full day narration using time markers.
  - 'Dialogue 2 — A fun weekend: — Що ти робила у суботу? — О, я мала чудовий день!
    — Розкажи! — Зранку я ходила на ринок і купила фрукти. — А потім? — Потім я готувала
    обід. А вдень гуляла в парку. — А ввечері? — Ввечері ми з подругою ходили в ресторан.
    — Як файно! Sequencing with потім, а потім.'
- section: Розповідь про день (Narrating a Day)
  words: 300
  points:
  - 'Time markers for structuring a story: зранку (in the morning), вдень (in the
    afternoon), ввечері (in the evening), вночі (at night). спочатку (first), потім
    (then), після цього (after that), нарешті (finally). These words turn separate
    sentences into a story: Спочатку я поснідав. Потім я пішов на роботу. Після цього
    я обідав.'
  - 'Daily routine verbs in past tense (all genders): прокинутися → прокинувся / прокинулася
    поснідати → поснідав / поснідала піти → пішов / пішла обідати → обідав / обідала
    повернутися → повернувся / повернулася лягти спати → ліг / лягла спати'
- section: Мій учорашній день (My Yesterday)
  words: 300
  points:
  - 'Model narrative — Anna''s yesterday: Учора був звичайний день. Зранку я прокинулася
    о пів на сьому. Я поснідала — їла кашу і пила каву. Потім я пішла на роботу. Вдень
    я обідала в кафе біля офісу. Я замовила салат і сік. Після роботи я ходила в магазин
    і купила продукти. Ввечері я готувала вечерю і дивилася серіал. О одинадцятій
    я лягла спати. Note all verbs are -ла (Anna is female).'
  - 'Your turn — build your own narrative: Use the template: Учора... Зранку я...
    Потім... Вдень... Ввечері... Combine past-tense verbs with places (кафе, парк,
    магазин), food (каша, кава, салат), and people (друг, колега, подруга). Everything
    you learned in A1 comes together here.'
- section: Summary
  words: 300
  points:
  - 'Narration toolkit: Time structure: зранку → вдень → ввечері → вночі. Sequencing:
    спочатку, потім, після цього, нарешті. Daily routine past forms: прокинувся/-лася,
    поснідав/-ла, пішов/пішла, обідав/-ла, повернувся/-лася, ліг/лягла спати. Gender
    consistency: male speakers use -в/-вся forms throughout, female speakers use -ла/-лася
    throughout. Self-check: Tell the story of your yesterday using at least 5 verbs.'
vocabulary_hints:
  required:
  - учора (yesterday)
  - зранку (in the morning)
  - вдень (in the afternoon)
  - ввечері (in the evening)
  - потім (then)
  - прокинутися (to wake up)
  - поснідати (to have breakfast)
  - обідати (to have lunch)
  recommended:
  - спочатку (first/at first)
  - нарешті (finally)
  - повернутися (to return)
  - лягти (to lie down)
  - звичайний (ordinary, adj)
  - продукти (groceries, pl)
  - серіал (TV series, m)
  - колега (colleague, m/f)
activity_hints:
- type: ordering
  focus: Put the daily routine in chronological order
  items:
  - Зранку я прокинувся.
  - Спочатку я поснідав.
  - Потім я пішов на роботу.
  - Вдень я обідав з колегою.
  - Ввечері я повернувся і дивився серіал.
  - Нарешті я ліг спати.
- type: fill-in
  focus: Complete the narrative with time markers and sequenced verbs
  items:
  - Учора {зранку|вдень|потім} я прокинулася о сьомій.
  - '{Спочатку|Нарешті|Вночі} я поснідала.'
  - '{Потім|Зранку|Ввечері} я пішла на роботу.'
  - Вдень я {обідала|обідав|обідали} в кафе.
  - '{Ввечері|Вдень|Зранку} я готувала вечерю.'
  - О десятій я {лягла|ліг|лягли} спати.
- type: fill-in
  focus: Practice gender consistency in narration (Female speaker 'Anna')
  items:
  - Я мала звичайний день. Я {прокинулася|прокинувся} рано.
  - Потім я {поснідала|поснідав}.
  - Після цього я {пішла|пішов} у магазин.
  - Там я {купила|купив} продукти.
connects_to:
- a1-050 (What Will Happen?)
prerequisites:
- a1-048 (What Happened?)
grammar:
- Past tense in connected narration (not isolated sentences)
- 'Time markers: зранку, вдень, ввечері, вночі'
- 'Sequencing words: спочатку, потім, після цього, нарешті'
- Gender consistency across a narrative
register: розмовний
references:
- title: State Standard 2024, §4.2.4.1
  notes: Past tense applied in narrative context.

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

**Confirmed (16/16 plan vocabulary words):**
- учора (adv) ✅
- зранку (adv) ✅
- вдень (adv) ✅
- ввечері (adv) ✅
- потім (adv) ✅
- прокинутися (verb) ✅
- поснідати (verb) ✅
- обідати (verb) ✅
- спочатку (adv) ✅
- нарешті (adv) ✅
- повернутися (verb) ✅
- лягти (verb) ✅
- звичайний (adj) ✅
- продукти → lemma продукт (noun) ✅
- серіал (noun) ✅
- колега (noun) ✅

**Confirmed (all inflected past-tense forms used in module narrative):**
- прокинувся / прокинулася ✅
- поснідав / поснідала ✅
- пішов / пішла ✅
- ліг / лягла ✅ (ліг resolves as лягти verb — correct)
- повернувся / повернулася ✅
- обідав / обідала ✅
- вночі (adv) ✅

**Not found as a VESUM lemma:**
- `після цього` — NOT in VESUM (expected: it is a prepositional phrase, не lexical unit; individual components **після** (prep) + **цього** (pron) both exist). ✅ Safe to use as a phrase.

---

## Textbook Excerpts

### Section: Минулий час — форми роду (Dialogues + Narration backbone)
> «Дієслова минулого часу означають дії, які відбувались або відбулися до моменту повідомлення про них. Форми дієслів минулого часу утворюємо від основи неозначеної форми за допомогою суфіксів -в, -л-»
>
> | Форма | Суфікс | Приклад |
> |---|---|---|
> | чоловічий рід | -в | розказати → розказав |
> | жіночий рід | -ла | розказала |
> | середній рід | -ло | розказало |
> | множина | -ли | розказали |
>
> Source: Заболотний, Grade 7 (Tier 1, NUS 2024), §17

### Section: Минулий час — додатковий приклад
> «Діє слова у формі минулого часу позначають дію, що відбувалася або відбулася до моменту мовлення про неї: допоміг, розв'язала, здалося, відчули. Форму минулого часу мають діє слова доконаного й недоконаного виду: робив і зробив, грав і зіграв.»
>
> Source: Літвінова, Grade 7 (Tier 1, NUS 2024), §9

### Section: Розповідь про день — прислівники часу
> «Ранком / Вечорами — прислівники часу. Прислівники й співзвучні (омонімічні) слова інших частин мови розпізнаємо в контексті (за лексичним значенням, морфологічними ознаками, синтаксичною роллю).»
>
> Textbook distinguishes adverb **ранком** ("Ранком дуже холодно" — коли?) from noun **ранком** ("Привітати з добрим ранком" — із чим?). Supports teaching зранку/вдень/ввечері as pure temporal adverbs.
>
> Source: Заболотний, Grade 7 (Tier 1, NUS 2024), p. 153

### Section: Послідовність дій (спочатку / потім / після цього)
> «Ця вправа дає змогу **спочатку** обмінятися ідеями з партнерами й лише **потім** озвучити свої думки перед класом.»
>
> Textbooks consistently pair **спочатку … потім** as a sequencing pair across grades 7–9 (Заболотний Grade 7 Tier 1, Grade 9 Tier 2). The pair is treated as a natural narrative connector.
>
> Source: Заболотний, Grade 7 (Tier 1), Grade 8 (Tier 1), Grade 9 (Tier 2)

### Section: Minulyi chas — творення
> «Минулий час. Основа інфінітива + суфікс -л- (-в-): водити — водив, водила, водило, водили»
>
> Source: Карамань, Grade 10 (Tier 2), §73

---

## Grammar Rules

- **Минулий час утворення**: Правопис §§ on verb morphology not in scope of Правопис 2019 (morphology = академічна граматика). Rule confirmed via textbook consensus: основа інфінітива + суфікс **-в** (чол. рід) / **-л-** (жін., сер., множина). Exception: основа на приголосний → no -в (ніс, поніс, ліг). **ліг** follows this exception (лягти → ліг ✅).
- **Прислівники зранку / вдень / ввечері / вночі**: Пишуться разом (Правопис §35 — прислівники, утворені злиттям). Confirmed by VESUM as single adverb entries.
- **після цього**: Прийменниково-займенниковий зворот — пишеться окремо. No Правопис issue.

---

## Calque Warnings

- **дивитися серіал** → **OK** — «дивитися» + object is standard Ukrainian. No calque issue. (Style guide returns unrelated entries on "рибалку" — no match.)
- **ходити в магазин** → ⚠️ **NOTE — not a calque, but register note**: Антоненко-Давидович (chunk ad-043) flags that **магазин** displaced the traditional **крамниця** in modern official Ukrainian. For A1 learners, **магазин** is the correct modern word (universally understood, in all current textbooks). Use магазин. Mention крамниця as a synonym note if space allows, but do NOT replace магазин.
- **рано лягти спати** → **OK** — Антоненко-Давидович (chunk ad-225) warns against **«варто мені лягти»** (calque from "стоит мне лечь"), but **«рано ліг спати»** is a pure temporal adverb + verb — no calque issue.
- **купити продукти** → **OK** — No calque flag. Standard Ukrainian.
- **після цього** → **OK** — Natural Ukrainian sequencing connector. Confirmed via textbook examples (Заболотний Grade 9).

---

## CEFR Check

| Word | PULS Level | Status |
|---|---|---|
| учора | A1 | ✅ On target |
| потім | A1 | ✅ On target |
| колега | A1 | ✅ On target |
| продукт(и) | A1 | ✅ On target |
| зранку | **A2** | ⚠️ One level above — but this is A1.8 (late A1 graduation module); acceptable. Sibling form **ранок** (A1) may be introduced alongside it. |
| нарешті | **A2** | ⚠️ One level above — late A1 is an appropriate stretch for a graduation module. Keep. |
| серіал | **A2** | ⚠️ One level above — modern, culturally essential word. Appropriate for A1.8 stretch vocabulary. Keep. |
| звичайний | **A2** | ⚠️ One level above — used once in the model narrative. Acceptable as passive vocabulary at A1.8. Keep. |
| повернутися (← повертатися) | **A2** | ⚠️ One level above — PULS lists the imperfective **повертатися** at A2. The perfective **повернутися** is in VESUM. Appropriate as active vocabulary for the graduation module. Keep. |

**Summary on CEFR**: No word exceeds A2. All A2-level items appear in the A1.8 *graduation* module, which is designed to bridge A1→A2. This is pedagogically sound and aligns with the "graduation/capstone" intent of the module.
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
# Verified Knowledge Packet: Yesterday
**Module:** yesterday | **Phase:** A1.8 [Past, Future, Graduation]
**Textbook grades searched:** 5, 6, 7

---

## Dialogues

> **Source:** avramenko, Grade 6
> **Section:** Сторінка 10
> **Score:** 0.50
>
> 10
> 1.	Прочитайте записи в колонках і виконайте завдання. 
> о сьомій годині 
> кілька вправ 
> контрастним душем
> Я прокидаюсь о сьомій годині.
> Виконую кілька фізичних вправ. 
> Потім загартовуюся контрастним душем. 
> А.	 За допомогою записів якої колонки легше передати думки? 
> Б.	 У якій колонці записано словосполучення, а в якій — речення? 
> Словосполучення складається щонайменше з двох самостійних слів, 
> одне з яких головне, а друге — залежне: прокидаюся (коли?) рано; пи-
> шаюся (чим?) успіхами.  
> Підмет із присудком, а також рівноправні слова не є словосполучення­
> ми: я снідаю; день і ніч.
> Речення — це одне або кілька слів, що виражають відносно закінчену 
> думку: Я щодня прокидаюся рано. У реченні є граматична основа, що 
> складається з одного або двох головних членів: Сонячний ранок.

> **Source:** litvinova, Grade 7
> **Section:** Сторінка 49
> **Score:** 0.25
>
> Розділ 1  ДІЄСЛОВО
> 46
> Вправа 61
>  
> Розкажіть про свій звичний розпорядок дня, уживаючи діє слова у  формі 
> теперішнього часу 
> Зразок:
> 7:00 — прокидаюсь, роблю зарядку, чищу зуби...
> 7:30 — снідаю.
> 8:00 — вигулюю свого домашнього дракона...
> Вправа 62
> 1   Прочитайте текст 
> Мабуть, усі сьогодні знають Ервіна 
> Мідена 
> — найхаризматичнішого 
> екс­
> курсовода, який став відомим на всю 
> Україну буквально за один день. Відео 
> з фрагментами його екскурсії облетіло 
> інтернет і вже набрало понад мільйон 
> переглядів. Тепер хлопця запрошують 
> на ефіри центральних телеканалів.
> Ервін має великий досвід проведення екскурсій. «Однак із 
> роками, — говорить хлопець, — просто почав помічати, на­
> скільки важко утримувати увагу людей; від звичайної екскур­
> сії слухачі втомлюються, їм потрібна якась розвага.

## Розповідь про день (Narrating a Day)

> **Source:** avramenko, Grade 7
> **Section:** Сторінка 154
> **Score:** 0.50
>
> — Нічого, хоч потроху пий, сили набирайся. У Квасольки — найсолодше 
> у світі молоко. Цілий вечір бабця розпитувала мене про тата і маму, а я, сидячи на 
> ґанку, розповідав, не зводячи очей із багряного сонячного диска, що поволі 
> зменшувався, а тоді пірнув за гору. Небо ще трохи палало, а потім якось 
> різко, майже вмить, стемніло, і на землю опустилася ніч. Де-не-де в роз-

## Мій учорашній день (My Yesterday)

> **Source:** avramenko, Grade 6
> **Section:** Сторінка 10
> **Score:** 0.50
>
> 10
> 1.	Прочитайте записи в колонках і виконайте завдання. 
> о сьомій годині 
> кілька вправ 
> контрастним душем
> Я прокидаюсь о сьомій годині.
> Виконую кілька фізичних вправ. 
> Потім загартовуюся контрастним душем. 
> А.	 За допомогою записів якої колонки легше передати думки? 
> Б.	 У якій колонці записано словосполучення, а в якій — речення? 
> Словосполучення складається щонайменше з двох самостійних слів, 
> одне з яких головне, а друге — залежне: прокидаюся (коли?) рано; пи-
> шаюся (чим?) успіхами.  
> Підмет із присудком, а також рівноправні слова не є словосполучення­
> ми: я снідаю; день і ніч.
> Речення — це одне або кілька слів, що виражають відносно закінчену 
> думку: Я щодня прокидаюся рано. У реченні є граматична основа, що 
> складається з одного або двох головних членів: Сонячний ранок.

> **Source:** zabolotnyi, Grade 7
> **Section:** Сторінка 207
> **Score:** 0.50
>
> Ніздрі роздмухувалися. Цей запах, очевидно, нагадував 
> їй матір – стару вівчарку, малих братиків і сестричок, з якими 
> вона розлучилася й більше ніколи не побачиться. Та куди б і до 
> чого не підповзала, запах молока виманював її. Випила його й 
> вилизала тарілку. Дівчинка прокинулася вранці до сходу сонця. Схопилася з 
> ліжка – як там Діана? Босоніж пролопотіла східцями. Бабуся 
> кришила г;ичку1, а цуценя походжало, крутячись біля неї. Дівчинка метнулася вхопити собачку, нести собі в ліжко, але 
> 1 Г;ичка – стебло та листя коренеплодів (наприклад, буряків); бадилля.

## Summary

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 63
> **Score:** 0.50
>
> 63
> ЛІТЕРАТУРНІ КАЗКИ
>  ускочив до садка, а відси бур’янами, через плоти, через капусти та кукуру-
> дзи чкурнув до лісу. Він ускочив у першу-ліпшу порожню нору, розгорнув 
> листя, зарився в ньому з головою і заснув справді, як по купелі. Чи пізно, чи рано встав він на другий день, сього вже в книгах не запи-
> сано, – досить, що, вставши з твердого сну, позіхнувши смачно і сплюнувши 
> тричі в той бік, де вчора була йому така немила пригода, він обережнень-
> ко, лисячим звичаєм, виліз із нори. Глип-глип! Нюх-нюх! Усюди тихо, 
> спокійно, чисто. Заграло серце1 в лисячих грудях. «Саме добра пора на 
> полювання!» – подумав. Але в тій хвилі зирнув на себе – господи! Аж 
> скрикнув неборачисько.

> **Source:** zabolotnyi, Grade 7
> **Section:** Сторінка 207
> **Score:** 0.50
>
> Ніздрі роздмухувалися. Цей запах, очевидно, нагадував 
> їй матір – стару вівчарку, малих братиків і сестричок, з якими 
> вона розлучилася й більше ніколи не побачиться. Та куди б і до 
> чого не підповзала, запах молока виманював її. Випила його й 
> вилизала тарілку. Дівчинка прокинулася вранці до сходу сонця. Схопилася з 
> ліжка – як там Діана? Босоніж пролопотіла східцями. Бабуся 
> кришила г;ичку1, а цуценя походжало, крутячись біля неї. Дівчинка метнулася вхопити собачку, нести собі в ліжко, але 
> 1 Г;ичка – стебло та листя коренеплодів (наприклад, буряків); бадилля.

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 136
> **Score:** 0.33
>
> 136
> КНИЖКА ВЧИТЬ, ЯК У СВІТІ ЖИТЬ
> ËÎÑÜ
> ОПОВІДАННЯ 
> (Скорочено)
> Він прокинувся й нащулив вуха... Звук летів знизу, від річки. Лось звів-
> ся, його постать чітко вималювалася в 
> удосвітніх сутінках. Це був великий 
> звір із широкими грудьми, які легко 
> здималися од дихання. Його роги нага-
> дували осінній низькорослий кущ, із 
> якого обнесло листя. Лось знав, що то тріщить стара гілляка на дубі, 
>  усохла, кощава; їй давно вже б треба впасти, а вона не падала, з дивною 
> впертістю тримаючись за стовбур. Струмінь вітру доносив запах річкової 
> криги. Лось уже звик до заповідника, у який потрапив із тайги, звик до людей і 
> до того, що його підгодовують.

## Grammar Reference

> **Source:** avramenko, Grade 7
> **Section:** Сторінка 205
> **Score:** 0.25
>
> 202
> Додаток 1
> НАЙУЖИВАНІШІ ПРИСЛІВНИКИ
> абикуди
> аби-то
> абияк
> аніскільки
> аніяк
> безвісти
> босоніж
> будь-де
> будь-що-будь
> вбік
> ввечері 
> вволю
> вголос
> вгорі 
> вдень 
> вдосвіта
> взимку 
> віддавна
> віч-на-віч
> влітку 
> внічию
> вночі 
> восени
> впоперек 
> вранці
> вручну 
> вряди-годи
> всередині 
> всього-на-всього
> вщерть
> дедалі
> деінде 
> деколи
> де-небудь
> де-не-де
> десь-інде 
> десь-інколи 
> довіку
> довкола
> додолу 
> додому 
> докупи 
> донизу
> донині 
> дощенту
> забагато 
> завбільшки
> завглибшки
> завдовжки 
> завчасу
> завширшки
> заодно
> затемна
> збоку
> звисока
> згарячу
> згори 
> зісподу 
> зліва
> знадвору
> знизу 
> зозла 
> зранку 
> зсередини
> казна-коли
> коли-небудь
> коли-не-коли
> куди-будь
> ліворуч
> мимоволі
> мимоїздом
> мимохідь
> мимохіть
> навесні
> навздогін
> навзнак
> навиворіт
> навиліт
> навідріз
> навіки 
> навприсядки 
> навпростець
> навстіж
> на-гора 
> надвечір 
> надвоє
> надворі ...

> **Source:** avramenko, Grade 6
> **Section:** Сторінка 10
> **Score:** 0.33
>
> 10
> 1.	Прочитайте записи в колонках і виконайте завдання. 
> о сьомій годині 
> кілька вправ 
> контрастним душем
> Я прокидаюсь о сьомій годині.
> Виконую кілька фізичних вправ. 
> Потім загартовуюся контрастним душем. 
> А.	 За допомогою записів якої колонки легше передати думки? 
> Б.	 У якій колонці записано словосполучення, а в якій — речення? 
> Словосполучення складається щонайменше з двох самостійних слів, 
> одне з яких головне, а друге — залежне: прокидаюся (коли?) р

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Dialogues` (~300 words)
- `## Розповідь про день (Narrating a Day)` (~300 words)
- `## Мій учорашній день (My Yesterday)` (~300 words)
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
  1. **Police report — describing a stolen велосипед (m, bicycle): Я припаркував велосипед біля магазину (m). Потім зайшов у кав'ярню (f). Коли вийшов, велосипед зник. Бачив чоловіка (m) в куртці (f) та кепці (f, cap).**
     Speakers: Свідок (witness), Поліцейський
     Why: Past narration with велосипед(m), магазин(m), кав'ярня(f), куртка(f)

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

GRAMMAR CONSTRAINTS (A1.8 — Past, Future & Graduation, M51-M60):
Full A1 grammar including past and future tense.

ALLOWED:
- Past tense (він читав, вона читала — gendered!)
- Future tense (я буду читати, ми будемо працювати)
- All cases, moods, and constructions from A1.1-A1.7
- Combining tenses in connected speech

BANNED: Participles, passive voice, complex literary constructions

### Vocabulary

**Required:** учора (yesterday), зранку (in the morning), вдень (in the afternoon), ввечері (in the evening), потім (then), прокинутися (to wake up), поснідати (to have breakfast), обідати (to have lunch)
**Recommended:** спочатку (first/at first), нарешті (finally), повернутися (to return), лягти (to lie down), звичайний (ordinary, adj), продукти (groceries, pl), серіал (TV series, m), колега (colleague, m/f)

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
## Dialogues (~300 words total)
- D1 (~120 words): Dialogue 1 — How was your day? Як пройшов твій день? Добре! Two characters (Тарас, Оксана). Тарас asks, Оксана narrates: Зранку я прокинулася о сьомій. Я поснідала і пішла на роботу. Вдень я працювала і обідала з колегою. Ввечері я дивилася серіал і лягла спати о десятій. 6–7 turns, each using a time marker (зранку/вдень/ввечері), past-tense verbs (-ла forms throughout for female speaker).
- D2 (~120 words): Dialogue 2 — A fun weekend. Що ти робив у суботу? Two characters (Марія, Іван). Іван narrates: Зранку я ходив на ринок і купив фрукти. Потім я готував обід. Вдень я гуляв у парку. Ввечері ми з другом ходили в ресторан. 6–7 turns using потім / а потім to chain events. Male speaker uses -в/-вся forms throughout.
- P1 (~60 words): Brief reading note after dialogues: highlight how time markers зранку → вдень → ввечері create the spine of both stories. Point out gender contrast: Оксана uses прокинулася, пішла, дивилася; Іван uses ходив, купив, готував. One rule stated plainly: pick your gender and keep it for the whole story.

## Розповідь про день — Narrating a Day (~300 words total)
- P1 (~80 words): Time-of-day markers as a storytelling frame. Present the four-slot timeline: зранку (in the morning) — вдень (in the afternoon) — ввечері (in the evening) — вночі (at night). Explain these are adverbs (незмінні — they never change form). Give three mini-sentences showing each slot: Зранку я поснідав. Вдень я обідав. Ввечері я дивився фільм. Вночі я спав.
- P2 (~80 words): Sequencing connectors that move the story forward: спочатку (first) → потім (then) → після цього (after that) → нарешті (finally). Contrast two versions of the same three events — without connectors (choppy) vs. with connectors (flowing): Я поснідав. Я пішов на роботу. Я обідав. vs. Спочатку я поснідав. Потім я пішов на роботу. Після цього я обідав. Ask the learner which version sounds like a story.
- P3 (~100 words): Daily routine verbs in past tense — both genders side by side in a compact two-column layout. Six verbs: прокинутися → прокинувся / прокинулася; поснідати → поснідав / поснідала; піти → пішов / пішла; обідати → обідав / обідала; повернутися → повернувся / повернулася; лягти спати → ліг спати / лягла спати. Stress the irregular pair пішов/пішла and ліг/лягла — these look different from the others. Two example sentences using each irregular form.
- Exercise: ordering activity — Put Тарас's day in the right order. Six items from activity_hints: Зранку я прокинувся. / Спочатку я поснідав. / Потім я пішов на роботу. / Вдень я обідав з колегою. / Ввечері я повернувся і дивився серіал. / Нарешті я ліг спати.

## Мій учорашній день — My Yesterday (~300 words total)
- P1 (~130 words): Model narrative — Anna's full yesterday in first person. Учора був звичайний день. Зранку я прокинулася о пів на сьому. Я поснідала — їла кашу і пила каву. Потім я пішла на роботу. Вдень я обідала в кафе біля офісу. Я замовила салат і сік. Після роботи я ходила в магазин і купила продукти. Ввечері я готувала вечерю і дивилася серіал. О одинадцятій я лягла спати. After the narrative: call-out box listing all -ла verbs underlined: прокинулася, поснідала, пішла, обідала, замовила, ходила, купила, готувала, дивилася, лягла — nine verbs, all female. This is gender consistency in action.
- P2 (~80 words): Your turn — guided narrative template. Scaffold with slots: Учора... Зранку я ___. Потім ___. Вдень я ___. Ввечері ___. O ___ годині я ліг/лягла спати. Prompt learner to plug in verbs from the table above plus places (кафе, парк, магазин, робота) and people (друг, колега, подруга) already known from A1. Reminder: pick your gender at the start and keep it to the end.
- Exercise: fill-in — Complete the narrative with time markers and sequenced verbs. Six items from activity_hints: Учора {зранку|вдень|потім} я прокинулася о сьомій. / {Спочатку|Нарешті|Вночі} я поснідала. / {Потім|Зранку|Ввечері} я пішла на роботу. / Вдень я {обідала|обідав|обідали} в кафе. / {Ввечері|Вдень|Зранку} я готувала вечерю. / О десятій я {лягла|ліг|лягли} спати.
- Exercise: fill-in — Gender consistency drill (Anna speaking). Four items from activity_hints: Я мала звичайний день. Я {прокинулася|прокинувся} рано. / Потім я {поснідала|поснідав}. / Після цього я {пішла|пішов} у магазин. / Там я {купила|купив} продукти. Instruction: all four blanks must match — Anna is female, so all -ла/-лася.

## Summary (~320 words total)
- P1 (~80 words): Narration toolkit recap in four named categories. (1) Time frame: зранку → вдень → ввечері → вночі. (2) Sequence chain: спочатку → потім → після цього → нарешті. (3) Past-tense forms to know cold: прокинувся/-лася, поснідав/-ла, пішов/пішла, обідав/-ла, повернувся/-лася, ліг/лягла спати — with the irregular pair highlighted again. (4) Gender rule: choose male or female at sentence one and never switch mid-story.
- P2 (~80 words): What you can do now — capability statement framed around the A1 payoff. After 49 modules you can introduce yourself, ask for things, talk about your family, describe your home, order food, tell the time — and now tell the full story of your day. Учора я прокинувся, поснідав і пішов — three words, one sentence, a whole morning. This is what narrative sounds like. Note the connection forward: модуль 50 introduces the future tense, so the same skeleton (зранку / вдень / ввечері) will work for завтра too.
- P3 (~80 words): Police report dialogue — the plan's dialogue situation brought to life as a short reading exercise. Поліцейський asks: Де ви припаркували велосипед? Свідок answers: Я припаркував велосипед біля магазину. Потім я зайшов у кав'ярню. Коли я вийшов, велосипед зник. Я бачив чоловіка в куртці та кепці. Three past-tense verbs in a real-world context (припаркував, зайшов, вийшов, зник, бачив). Note: this is past narration under pressure — same toolkit, different situation.
- Self-check (~80 words): Bulleted Q&A list — five prompts the learner answers aloud or in writing. • О котрій ти прокинувся/-лася учора? • Що ти робив/-ла зранку? • Де ти обідав/-ла вдень? • Що ти робив/-ла ввечері? • О котрій ти ліг/лягла спати? Instruction: answer in full sentences using at least five past-tense verbs. If you can tell your whole yesterday without switching genders, you're ready for модуль 50.

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
