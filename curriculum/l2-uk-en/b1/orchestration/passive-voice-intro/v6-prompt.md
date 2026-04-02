

---

## Your Writing Identity

**You are: Experienced Ukrainian Language Instructor.** Your persona is *The Cultural Guide*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **23: Пасивний стан (вступ)** (B1, B1.3 [Verbs]).

**Target: 4000–6000 words** of prose (Ukrainian examples count toward word total, headings and exercise placeholders do not).

---

## Step 1: Pacing Plan (output this FIRST)

Before writing any content, output a `<pacing_plan>` block. Evaluate each section from the plan and commit to a word budget. This prevents frontloading early sections and rushing later ones.

```
<pacing_plan>
Section 1 "Title": ~XXX words — [1-sentence content focus]
Section 2 "Title": ~XXX words — [1-sentence content focus]
...
Summary: ~150 words
Total: 4000+ words
</pacing_plan>
```

Then begin writing the module content. Follow your own pacing plan — each section must hit its word budget (±10%).

---

## 9 Hard Rules

1. **IMMERSION TARGET: 40-60% Ukrainian** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if immersion is outside this range. For A1 early modules, the learner cannot read Cyrillic — English must dominate. For A2+, Ukrainian must carry a significant share — add Ukrainian Reading Practice blocks, dialogues, and example paragraphs to reach the target. Too little Ukrainian fails audit just as much as too much.
2. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
3. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
4. **NO "In this lesson we will..."** — never use formulaic openers. Start with a dialogue, a question, or a situation.
5. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
6. **Place exercise markers only** — do NOT write exercises directly. Place `<!-- INJECT_ACTIVITY: {id} -->` markers where exercises should appear. A separate pipeline step generates the actual exercises from the plan's activity_hints.
7. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
8. **Hit the word target** — you MUST write 4000–6000 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
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
module: b1-023
level: B1
sequence: 23
slug: passive-voice-intro
version: '3.0'
title: Пасивний стан (вступ)
subtitle: Пасивні конструкції через зворотні дієслова та форми на -но/-то
focus: grammar
pedagogy: PPP
phase: B1.3 [Verbs]
word_target: 4000
objectives:
- 'Learner can identify passive constructions in Ukrainian and distinguish them from active voice: Робітники будують дім (active)
  vs Дім будується робітниками (passive)'
- 'Learner can form passive constructions using зворотні дієслова with -ся: будується, читається, продається, передається'
- 'Learner can use the uniquely Ukrainian -но/-то impersonal passive forms: Дім збудовано. Книгу прочитано. Роботу виконано.'
- Learner understands that Ukrainian AVOIDS passive constructions and prefers active voice — this is a key stylistic difference
  from English
- Learner can transform passive sentences to active and vice versa, choosing the more natural Ukrainian option in context
dialogue_situations:
- setting: 'Guided tour of a newly renovated Палац культури (m, Palace of Culture)
    in Дніпро — describing what was done: Цей зал (m, hall) був побудований у 1960-х.
    Стіни (pl, walls) були пофарбовані минулого місяця. Вхід (m, entrance) буде відкрито
    для публіки завтра.'
  speakers:
  - Архітектор
  - Журналіст
  motivation: 'Passive voice: був побудований, були пофарбовані, буде відкрито'
content_outline:
- section: Активний i пасивний стан
  words: 750
  points:
  - 'Core concept: стан дієслова describes the relationship between the subject and the action. Активний стан: підмет виконує
    дію. Студенти читають книгу. Пасивний стан: підмет зазнає дії. Книга читається студентами. The meaning is the same, but
    the focus shifts.'
  - 'Ukrainian strongly prefers active voice (Заболотний Grade 8 p.95): ''Українська мова уникає пасивних конструкцій. Тому
    перевагу, де це можливо, слід надавати дієсловам активного стану.'' This is NOT like English, where passive is common
    in academic writing. In Ukrainian, excessive passive = канцелярит (bureaucratese).'
  - 'When passive IS appropriate in Ukrainian: 1. The agent is unknown: Місто було засновано у X столітті. 2. The result matters
    more than the agent: Завдання виконано. 3. Scientific/technical descriptions: Елемент було відкрито у 1898 році. 4. Official
    documents: Закон ухвалено Верховною Радою.'
- section: Пасив через зворотні дієслова
  words: 700
  points:
  - 'Formation from Заболотний Grade 8 p.95: ''Засобом вираження пасивного стану є формотворчий афікс -ся, що додається до перехідних
    дієслів: будується, передається, продовжується.'' The subject receives the action: Добре слово дім будує. (active) → Поганим
    словом все руйнується. (passive with -ся)'
  - 'Agent expression with орудний відмінок: Книга читається учнями уважно. Рецепт готується нами вправно. But note: Авраменко
    Grade 11 p.81 observes that Ukrainian speakers often find the agent awkward in -ся passives: ''Речення якої колонки звучать
    більш природно?'' — active versions win. Use active when possible.'
  - 'Distinguishing passive -ся from other зворотні (M22 categories): Він миється. (reflexive — washes himself) Цей товар
    продається у кожному магазині. (passive — is sold) Test: if the subject is inanimate and not doing the action to itself,
    it''s likely passive.'
  - 'Common passive -ся verbs: будуватися (to be built), використовуватися (to be used), вважатися (to be considered), називатися
    (to be called), вироблятися (to be produced), знаходитися (to be located). Note: знаходитися is so common that its passive
    origin is forgotten.'
- section: 'Форми на -но/-то: українська спеціальність'
  words: 850
  points:
  - 'From Авраменко Grade 11 p.81: ''Синтаксичні конструкції з формами на -но, -то.'' Усі інгредієнти придбано. (All ingredients
    have been obtained.) Роботу виконано. (The work has been completed.) Книжку прочитано. (The book has been read.) Двері
    зачинено. (The door has been closed.)'
  - 'Formation: пасивний дієприкметник stem + -о: зроблений → зроблено, прочитаний → прочитано, відкритий → відкрито, забутий
    → забуто. These are IMPERSONAL — there is no nominative subject. The object stays in знахідний відмінок: Зроблено роботу
    (not *робота).'
  - 'Why this is uniquely Ukrainian (Заболотний Grade 8 p.97): ''Пасивні конструкції з дієслівними формами на -но, -то в українській
    мові використовують обмежено'' — but they are MORE NATURAL than -ся passives. This is Ukrainian''s preferred passive:
    Засідання проведено. (natural) vs *Засідання проводиться. (awkward bureaucratese) vs Провели засідання. (active — also
    natural)'
  - 'Practice: transform active sentences to -но/-то passives: Учні написали диктант. → Диктант написано. Архітектор спроєктував
    будівлю. → Будівлю спроєктовано. Note how the agent disappears — this is the point.'
- section: Порівняння трьох конструкцій
  words: 600
  points:
  - 'Three ways to say the same thing: ACTIVE: Робітники збудували дім. (Workers built the house.) PASSIVE -ся: Дім збудований
    робітниками. / Дім будувався робітниками. PASSIVE -но: Дім збудовано. (The house has been built.) Ukrainian naturalness
    ranking: Active > -но/-то > -ся passive.'
  - 'Decision guide for learners: 1. Default: use ACTIVE voice. 2. If agent is unknown/irrelevant: use -но/-то. 3. For processes/states
    of inanimate subjects: -ся is acceptable (магазин знаходиться, квиток продається). 4. Avoid -ся passive with explicit
    agent (орудний) — sounds unnatural.'
  - 'Contrastive exercise: given 8-10 sentences, choose the most natural Ukrainian version. Most should be active or -но/-то.
    One or two may legitimately use -ся (знаходиться, називається).'
- section: 'Практика: пасив у контексті'
  words: 750
  points:
  - 'Reading passage: a Ukrainian news report about a cultural event or construction project. Contains natural passive usage:
    Фестиваль проведено у Львові. Новий міст збудовано. Виставку відкрито. Книгу видано. Comprehension questions test LANGUAGE:
    — Знайдіть усі конструкції на -но/-то. — Перетворіть їх на активні речення. — Чому автор обрав пасив у цих випадках?'
  - 'Transformation exercises: Active → -но/-то: Уряд ухвалив закон. → Закон ухвалено. -ся passive → active: Місто засновувалося
    козаками. → Козаки заснували місто. -но/-то → active: Листа надіслано. → Хтось надіслав листа.'
  - 'Production: learners write a short report (5-6 sentences) about an accomplishment using -но/-то forms: Проєкт завершено.
    Результати опубліковано. Звіт подано вчасно. Усі завдання виконано.'
- section: Підсумок та перехід до M24
  words: 450
  points:
  - 'Summary: пасивний стан — підмет зазнає дії. Два способи: -ся (будується) i -но/-то (збудовано). Українська мова надає
    перевагу активному стану. -но/-то — спеціально українська конструкція, природніша ніж -ся пасив. Self-check: Я можу розрізнити
    активний i пасивний стан ✓/✗, Я можу утворити форму на -но/-то ✓/✗, Я знаю, коли пасив доречний ✓/✗.'
  - 'Preview: M24 — Творення дієслів. How prefixes and suffixes create new verbs from existing ones: писати → написати → переписати.
    This completes the verb formation picture before the communication module M25 puts all verb skills into practice.'
vocabulary_hints:
  required:
  - пасивний стан (passive voice — subject receives the action)
  - активний стан (active voice — subject performs the action)
  - будуватися (to be built — passive -ся)
  - називатися (to be called — passive -ся, very common)
  - знаходитися (to be located — passive -ся, lexicalized)
  - використовуватися (to be used — passive -ся)
  - збудовано (has been built — -но/-то form)
  - виконано (has been completed — -но/-то form)
  - прочитано (has been read — -но/-то form)
  - ухвалено (has been adopted/passed — -но/-то form, laws)
  - канцелярит (bureaucratese — overuse of passive/nominal style)
  - перехідне дієслово (transitive verb — takes a direct object)
  - неперехідне дієслово (intransitive verb — no direct object)
  - орудний відмінок (instrumental case — agent in passive)
  recommended:
  - вважатися (to be considered)
  - продаватися (to be sold)
  - вироблятися (to be produced)
  - видано (has been published — -но/-то)
  - засновано (has been founded — -но/-то)
  - спроєктовано (has been designed — -но/-то)
  - опубліковано (has been published — -но/-то)
  - надіслано (has been sent — -но/-то)
  - природний (natural — as opposed to forced/awkward)
activity_hints:
- type: quiz
  focus: 'Identify voice: активний стан, пасивний -ся, or пасивний -но/-то'
  items: 10
- type: sentence-builder
  focus: Transform active sentences to -но/-то passive and vice versa
  items: 8
- type: fill-in
  focus: Complete sentences with the correct -но/-то form of the given verb
  items: 8
- type: error-correction
  focus: Fix unnatural passive constructions by rewriting as active voice
  items: 6
- type: match-up
  focus: Match active sentences to their -но/-то equivalents
  items: 8
connects_to:
- b1-022 (Зворотні дієслова — пасивноподібні category expanded here)
- b1-024 (Творення дієслів — verb formation completes Phase 3 grammar)
- b1-058 (Пасивні дієприкметники — participle-based passive, Phase 7)
prerequisites:
- b1-022 (Reflexive verbs — -ся formation and semantic categories)
grammar:
- 'Активний vs пасивний стан: subject does vs receives the action'
- 'Passive via -ся: будується, використовується (from перехідні дієслова)'
- 'Ukrainian -но/-то forms: збудовано, виконано, прочитано (impersonal passive)'
- '-но/-то formation: passive participle stem + -о, object stays in Зн.'
- 'Stylistic preference: active > -но/-то > -ся passive'
- Distinguishing passive -ся from reflexive -ся (context and animacy)
register: академічний
references:
- title: Заболотний Grade 7, §30
  notes: 'Дієслівні форми на -но, -то: творення від пасивних дієприкметників (створений -> створено), значення результату дії.'
- title: Авраменко Grade 7, §51
  notes: 'Безособові форми на -но, -то. "В українській мові з орудним відмінком виконавця ці форми не вживаємо".'
- title: Заболотний Grade 7, §30
  notes: 'Пасивні конструкції з дієсловами на -ся. Stylistic preference: Active > -но/-то > -ся passive.'

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
- Confirmed: пасивний, активний, стан, будуватися, називатися, знаходитися, використовуватися, збудовано, виконано, прочитано, ухвалено, канцелярит, перехідний, неперехідний, дієслово, орудний, відмінок, вважатися, продаватися, вироблятися, видано, засновано, спроєктовано, опубліковано, надіслано, природний.
- Not found: None. (All 26 words verified as existing in the morphological dictionary).

## Textbook Excerpts
### Section: Активний i пасивний стан
> "Українська мова уникає пасивних конструкцій. Тому перевагу, де це можливо, слід надавати дієсловам активного стану. ... природніше сказати *вас запрошує директор*, ніж *ви запрошуєтеся директором*."
> Source: Karaman, Grade 10; Glazova, Grade 11

### Section: Форми на -но/-то: українська спеціальність
> "Основне призначення конструкцій із формами на -но, -то – зосереджувати увагу не на виконавцеві, а на самій дії, на її завершенні, результаті. ... *прибрана кімната* – *кімнату прибрано*."
> Source: Zabolotnyi, Grade 7

### Section: Пасив через зворотні дієслова
> "Засобом вираження пасивного стану є формотворчий афікс -ся, що додається до перехідних дієслів: *будується*, *передається*, *продовжується*."
> Source: Glazova, Grade 11

## Grammar Rules
- [Agent Prohibition]: Avramenko, Grade 11 — Including an agent in the instrumental case with -но/-то forms (e.g., *Іспит складено студентом*) is explicitly defined as a "gross violation" (грубе порушення). Use active voice or just the impersonal form.
- [Subject/Object Shift]: Karaman, Grade 10 — In passive voice, the object of the action becomes the subject (nominative), and the subject becomes an optional addition in the instrumental case (*Арія виконується співаком*).

## Calque Warnings
- [знаходитися]: Calque (when used for location) — Антоненко-Давидович advises against using it for geographical or spatial positions. Correct forms: **бути**, **перебувати**, **міститися**, **лежати**.
- [рахуватися]: Calque — Use **вважатися** for "to be considered". *Рахувати* is strictly for mathematical calculation.
- [використовуватися]: Potential Calque — Often an overused substitute for the active voice or **вживатися**.

## CEFR Check
- пасивний: B1 — OK (Target level match)
- активний: A1 — OK (Already known)
- ухвалено: ~B1/B2 — OK (Contextually appropriate for official/news topics)
- канцелярит: B2+ — Should be introduced as a concept for avoidance rather than a core vocabulary item for production.
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
# Verified Knowledge Packet: Пасивний стан (вступ)
**Module:** passive-voice-intro | **Phase:** B1.3 [Verbs]
**Textbook grades searched:** 1, 2, 3, 5

---

## Активний i пасивний стан

> **Source:** bolshakova, Grade 1
> **Section:** Сторінка 7
> **Score:** 0.50
>
> 7
> СЛОВА — НАЗВИ ДІЙ
> Кожну дію ти можеш назвати словом.
> ЩО РОБИТЬ?
> бігає
> стрибає
> сидить
> читає
> спить
> Діти на подвір’ї. Олена стрибає. Тарас бігає. 
> Алла сидить на лаві. Ганна читає книжку. 
> Кіт Нявчик спить.
> Що робить кожен хлопчик? Вибери правильну відповідь.
>  
>  Малює картину.
>  Читає книжку.
>  Грає на барабані.
>  Миє посуд.
>  Готує бутерброд.
>  П’є чай.
> 1

## Пасив через зворотні дієслова

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 58
> **Score:** 0.50
>
> 55
> 121.	А.  Визначте лексичне значення розміщеного в центрі схеми слова. 
> бігти
> при
> за
> до
> по
> на
> в
> з
> від
> ви
> пере
> об
> під
> Б.  Додайте почергово до дієслова бігти префікси. Які додаткові зна-
> чення вносять вони в лексичне значення дієслова? 
> В.  Поміркуйте, як префікси допомагають збагатити мову. 
> Префікс (від лат. prae – попереду і fixus – прикріпле-
> ний) – це значуща частина слова, яка стоїть перед коренем 
> і служить для утворення нових слів. НАПРИКЛАД: чудовий – 
> пречудовий, їхати – виїхати, плата – передплата, хмар-
> ний – безхмарний.
> Слово може мати переважно один префікс, але іноді – 
> два або більше.

## Форми на -но/-то: українська спеціальність

> **Source:** avramenko, Grade 5
> **Section:** Сторінка 2
> **Score:** 0.50
>
> — спостереження;
> — творче  завдання;
> — ключ-відповідь;
> — робота  в  парах;
> — робота  в  групах;
> — словник;
> — домашнє  завдання.
> УМОВНІ  ПОЗНАЧЕННЯ:
> УДК 
>  
> А21
> Авраменко О. 
> Українська мова : підруч. для 5 кл. закл. загальн. 
> середн. освіти / Олександр Авраменко. — Київ : Гра-
> мота, 2022. — 208 с. : іл.
> ISBN 978-966-349-917-8
> У підручнику подано матеріали для повторення та уза-
> гальнення вивченого в початкових класах, а також розділи: 
> «Лексикологія», «Будова слова. Орфографія», «Синтаксис і 
> пунктуація» (за Модельною навчальною програмою «Україн-
> ська мова. 5–6 класи: для закладів загальної середньої осві-
> ти»; атори О. В. Заболотний, В. В. Заболотний, В. П. Лаврин-
> чук, К. В. Плівачук, Т. Д. Попова).
> УДК 
> ISBN 978-966-349-917-8
> © Авраменко О.

> **Source:** avramenko, Grade 5
> **Section:** Сторінка 2
> **Score:** 0.33
>
> Аналізуємо 
> зміст та 
> особливості 
> художнього 
> твору
> Творчо 
> мислимо
> Даємо 
> відповіді 
> за змістом 
> твору
> УМОВНІ ПОЗНАЧЕННЯ
> Авраменко О.
> Українська література : підруч. для 5 кл. закл. за­
> гальн. середн. освіти / Олександр Авраменко. — Київ : 
> Грамота, 2022. — 288 с. : іл.
> ISBN 978-966-349-918-5
> Підручник відповідає вимогам Державного стан­
> дарту. Видання підготовлено відповідно до Модельної 
> навчальної про­грами «Українська література. 5–6 кла­
> си» для закладів загальної середньої освіти (автори: 
> Архипова В. П., Січкар С. І., Шило С.

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 225
> **Score:** 0.25
>
> 225
> Відомості із синтаксису й пунктуації.  Речення з однорідними членами
> 2.	 Запишіть утворені речення.  Підкресліть однорідні члени відповідно 
> до  того, якими членами речення вони є.
> 3.	 Поміркуйте та  зробіть висновки: як змінилися речення після того, як ви 
> їх доповнили?
> Вправа 365
> Складіть речення, щоб наведені слова були в них однорідними членами 
> (форму слів можна змінювати).
> сучасні, класичні 
> для хлопців і  дівчат 
> однотонні та  строкаті 
> не повсякденний, а  святковий 
> і зранку, і  ввечері 
> Вправа 366
> 1.	 Спишіть текст, де потрібно, заповнюючи пропуски.
> Сучасних підлітків не  потрібно змушувати вдягати 
> шап­ки та  шарфи. Вони утеплюют..ся з  радіс..тю, оскіль-
> ки вибір в..язаних шапок, стильних капелюхів, краси-
> вих шарфиків-снудів просто 
> колос..альний.

## Порівняння трьох конструкцій

> **Source:** vashulenko, Grade 2
> **Section:** Сторінка 81
> **Score:** 0.50
>
> 7| Прочитайте виразно вірш. Поясніть, кому дякують люди.
> Що роблять будівельники? 
> Що роблять хлібороби?
> Що роблять учителі?
> Що роблять ковалі? 
> Що роблять письменники?
> Тим, що в поле йдуть орати, 
> що плуги міцні кують, 
> що будують теплі хати, 
> пишуть книги нам читати, 
> зі шкіл науку надають, — 
> шана й дяка їм велика 
> од людей на вічні віки.
> Борис Грінченко
> Коваль — майстер, який куванням обробляє 
> метал, виготовляє металеві предмети.
> ____ -_____ _
> Поміркуй і скажи, від 
> якого слова походить 
> слово будівельник.
> 1 _______——
> Я — ДОСЛІДНИЦЯ
> Переглянь картини українських художників. Розкажи, 
> як на них зображено природу перед грозою.
> 8| Уяви себе письменником (письменницею). Прочитай 
> текст, добираючи з дужок дієслово, яке найточніше
> виражає думку.
> (Пролетіла, пройшла, минула) гроза.

> **Source:** bolshakova, Grade 1
> **Section:** Сторінка 9
> **Score:** 0.25
>
> 9
> Знайди слово — підпис до малюнка.
> 	
> озеро	
> літо	
> Оля	
> робот
> 	
> олень	
> жито	
> Олег	
> робота
> 	
> окунь	
> доміно	
> Олена	
> робітник
> 
> Текст. Заголовок. Текст і малюнки
> Робота Роббі зробили на 
> заводі. Він виконує різні про-
> грами. 
> Робот Роббі живе з нами. 
> Миє підлогу, поливає квіти. 
> Роббі не просто машина, він  — 
> наш друг. Ми разом граємо  
> і читаємо книжки. 
> Уранці робот усіх будить. 
> Увечері розповідає смішні істо-
> рії. А  вночі відпочиває, як і ми.
> Порівняй текст і малюнки. Знайди 
> схоже і відмінне. 
> Добери заголовок до тексту. 
> Дім
>  
> Завод
>  
> Робот Роббі
> 1
> 2
> О о
> бо	 во	
> го	 до
> ко	 ло	 мо	 но
> ро	 со	
> то	 шо

## Практика: пасив у контексті

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 157
> **Score:** 0.50
>
> 154
> 1. У великих і маленьких містах для дорослих і дітей 
> організовують театральні фестивалі, книжкові виставки. 
> 2. На літературних фестивалях письменники читають влас-
> ні поетичні та прозові твори. 3. Книжки збільшують наш 
> словниковий запас, розширюють світогляд. 
> ІІ. Розберіть за будовою виділене слово. 
> 377.	Хто зможе за одну хвилину утворити й записати 7 словосполу-
> чень із поданих слів? А хто ще більше? Форму слів можна змінювати. 
> Для поєднання окремих слів можна використовувати прийменники.

> **Source:** golub, Grade 5
> **Section:** Сторінка 123
> **Score:** 0.33
>
> 123
> 1. Приймай своє рішення та аргументуй його. 2. Не лінуйся 
> брати відповідальність за свої вчинки, за майбутнє своєї кра-
> їни. 3. Активність, ініціативність і відповідальність — важ-
> ливі риси громадянина і громадянки. 4. Наша країна потре-
> бує активної, цілеспрямованої, відповідальної і наполегливої 
> молоді. 5. Свою відповідальність ми маємо реалізувати 
> у школі, у родині й суспільстві.
>  
> ІІ   Чи поділяєте ви думки, висловлені в реченнях? Що озна-
> чає слово «завзяття»? Кого ви можете назвати завзятою 
> людиною? Завзяті громадяни корисні для суспільства? 
> Чому?
> 306   Розгляньте схему. Про що запитують зображені діти? Прочитайте 
> речення з однорідними членами. Скоротіть їх, вилучивши одно-
> рідні члени. Зробіть висновки, у яких дайте відповідь на постав-
> лене запитання.

## Підсумок та перехід до M24

> **Source:** bolshakova, Grade 2
> **Section:** Сторінка 53
> **Score:** 0.50
>
> 53
> • Продовж діалог. Запиши кілька реплік діалогу в зошит. 
> Пробач. 
> Я вчинив негарно.
> Дякую, що 
> вибачився.
> • Випиши слова — назви дій. 
> Зразок. Квіти (що роблять?) пнуться, ... .
> • Назви слова, які описують стани людини. Склади з двома 
> словами речення.
> Боїться, радіє, бігає, цікавиться, співає, дивується, танцює.
> сЛова — назви ДІЙ
> Що ти робиш у школі, удома, на вулиці? Запиши слова — 
> назви дій у стовпчики.
> Читаю, читання, пишу, письмо, малюю, малювання, 
> стрибаю, граю, гра, співаю, танцюю, танок, спілкуюся, роз-
> мовляю, розмова, їм, їжа, п’ю, бігаю, їжджу, копаю, саджу.
> У школі
> Удома
> на вулиці
>  
> Редагуємо
> • Пост

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Активний i пасивний стан` (~750 words)
- `## Пасив через зворотні дієслова` (~700 words)
- `## Форми на -но/-то: українська спеціальність` (~850 words)
- `## Порівняння трьох конструкцій` (~600 words)
- `## Практика: пасив у контексті` (~750 words)
- `## Підсумок та перехід до M24` (~450 words)
- `## Підсумок` (~150 words)

Each section should follow the word budget specified. The total must reach 4000 words minimum.

---

## Content Rules

Full Ukrainian immersion. Grammar explained IN Ukrainian. English only for disambiguation of false friends. Sentences max 30 words.

GRAMMAR RULES:
- Max 30 words per Ukrainian sentence
- Max 4 clauses per sentence
- All grammar constructions allowed
- Participles allowed
- Complex subordinate clauses allowed

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
- Use callout boxes (:::tip, :::caution, :::note) — at least 3 per module (mnemonics, common mistakes, cultural notes). Space them throughout the module, not clustered.
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
  1. **Guided tour of a newly renovated Палац культури (m, Palace of Culture) in Дніпро — describing what was done: Цей зал (m, hall) був побудований у 1960-х. Стіни (pl, walls) були пофарбовані минулого місяця. Вхід (m, entrance) буде відкрито для публіки завтра.**
     Speakers: Архітектор, Журналіст
     Why: Passive voice: був побудований, були пофарбовані, буде відкрито

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



### Vocabulary

**Required:** пасивний стан (passive voice — subject receives the action), активний стан (active voice — subject performs the action), будуватися (to be built — passive -ся), називатися (to be called — passive -ся, very common), знаходитися (to be located — passive -ся, lexicalized), використовуватися (to be used — passive -ся), збудовано (has been built — -но/-то form), виконано (has been completed — -но/-то form), прочитано (has been read — -но/-то form), ухвалено (has been adopted/passed — -но/-то form, laws), канцелярит (bureaucratese — overuse of passive/nominal style), перехідне дієслово (transitive verb — takes a direct object), неперехідне дієслово (intransitive verb — no direct object), орудний відмінок (instrumental case — agent in passive)
**Recommended:** вважатися (to be considered), продаватися (to be sold), вироблятися (to be produced), видано (has been published — -но/-то), засновано (has been founded — -но/-то), спроєктовано (has been designed — -но/-то), опубліковано (has been published — -но/-то), надіслано (has been sent — -но/-то), природний (natural — as opposed to forced/awkward)

### Pronunciation Videos

**Do NOT embed YouTube videos in your prose.** A downstream ENRICH tool automatically places pronunciation videos from the plan. If you embed `<YouTubeVideo>` components, they will be duplicated. Simply reference the videos' existence when relevant (e.g., "Watch the pronunciation video for this letter") but do NOT insert `<YouTubeVideo>` tags.

Available videos (for reference only — ENRICH handles placement):


---

### Style Reference (match this tone and structure)

Дієприкметники — це особлива форма дієслова, яка поєднує ознаки дієслова та прикметника. Вони відповідають на питання «який?» і змінюються за родами, числами та відмінками, як звичайні прикметники.

Порівняйте:
- **написаний лист** (a written letter) — пасивний дієприкметник
- **зігрітий чай** (warmed tea) — пасивний дієприкметник

:::tip
В українській мові активні дієприкметники теперішнього часу (на -учий/-ючий) вважаються стилістично небажаними. Замість «працюючий лікар» краще сказати «лікар, який працює».
:::

*Note: Grammar explained IN Ukrainian using Ukrainian linguistic terms. English appears only in parenthetical translations for disambiguation. Callout boxes in Ukrainian.*



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
## Активний і пасивний стан (~780 words total)
- P1 (~120 words): Introduction to "стан дієслова" (verb voice) as the relationship between the doer (підмет) and the action. Definition of Active Voice (активний стан): the subject performs the action (Марія читає статтю). Definition of Passive Voice (пасивний стан): the subject undergoes the action (Стаття читається Марією).
- P2 (~130 words): Deep dive into Active Voice in Ukrainian. Why it is the "default" setting. Examples of transitive verbs (перехідні дієслова) taking direct objects: Архітектор проєктує будівлю, Уряд ухвалив закон, Студенти слухають лекцію.
- P3 (~150 words): The stylistic "Hard Rule" of Ukrainian: Preference for active over passive. Citing Zabolotnyi (Grade 8) and Avramenko (Grade 11) regarding "канцелярит" (bureaucratese). Comparison: "Ми виконали план" (natural) vs "План був виконаний нами" (stiff/unnatural).
- P4 (~160 words): Specific scenarios where passive IS appropriate: 1. Unknown agent (Скарб було знайдено), 2. Focus on the result (Роботу завершено), 3. Academic/Technical style (Елемент було відкрито), 4. Official/Legal context (Закон ухвалено).
- P5 (~120 words): The linguistic "beauty" of choice: explaining how switching voice allows the speaker to emphasize either the person or the achievement. Example: "Я написав книгу" (Me focus) vs "Книгу написано" (Book focus).
- Exercise: [quiz, focus: Identify voice: активний стан, пасивний -ся, or пасивний -но/-то, 10 items]

## Пасив через зворотні дієслова (~740 words total)
- P1 (~130 words): Formation of the passive using the suffix -ся added to transitive verbs. Examples: будувати -> будуватися, використовувати -> використовуватися. The subject becomes the recipient of the action: "Дім будується" (The house is being built).
- P2 (~140 words): Expressing the agent using the Instrumental case (орудний відмінок). Example: "Книга читається учнями" (The book is read by students). Comparison with Active: "Учні читають книгу." Explicit warning: passive with an agent is often considered "artificial" in modern Ukrainian.
- P3 (~150 words): The "Animacy Test" to distinguish passive -ся from reflexive -ся. If the subject is inanimate (неістота), it's usually passive: "Магазин відкривається" (passive) vs "Дитина вмивається" (reflexive). Exceptions and common pitfalls with words like "називатися" and "знаходитися."
- P4 (~120 words): Analysis of lexicalized passive verbs. Why "знаходитися" (to be located) and "вважатися" (to be considered) are so common they lose their passive feel. Examples: "Музей знаходиться в центрі," "Він вважається експертом."
- P5 (~100 words): Tense variations in -ся passives. Present: "Будинок будується." Past: "Будинок будувався." Future: "Будинок буде будуватися." Note: these usually imply a process rather than a completed result.
- Exercise: [error-correction, focus: Fix unnatural passive constructions by rewriting as active voice, 6 items]

## Форми на -но/-то: українська спеціальність (~920 words total)
- P1 (~140 words): Introduction to the -но/-то forms as a unique and "highly natural" Ukrainian passive construction. Definition: impersonal forms derived from passive participles. Examples: збудований -> збудовано, виконаний -> виконано, відкритий -> відкрито, забутий -> забуто.
- P2 (~160 words): The Grammar "Trap": Impersonal nature and Case usage. In the construction "Книгу прочитано," "книгу" is in the Accusative case (знахідний відмінок), NOT the Nominative. Why saying "*Книга прочитано" is a common error for learners (and some natives).
- P3 (~150 words): Comparison with English "To Be" + Participle. "The work is done" -> "Роботу виконано." Pointing out that -но/-то forms do not use "бути" (є) in the present tense, unlike English. Past context: "Роботу було виконано." Future: "Роботу буде виконано."
- P4 (~160 words): Naturalness check: Why "-но/-то" is the "Gold Standard" of Ukrainian passives. Citing Zabolotnyi on why "Засідання проведено" is superior to "Засідання проводиться" when reporting an event. The disappearing agent as a stylistic tool.
- P5 (~160 words): Transformation logic. How to turn an active sentence into -но/-то. Process: Subject removed -> Verb changed to -но/-то -> Object remains in Accusative. Example: "Художник намалював картину" -> "Картину намальовано."
- P6 (~150 words): High-frequency -но/-то verbs in official and daily life: ухвалено (adopted), зачинено (closed), відчинено (opened), надіслано (sent), куплено (bought), втрачено (lost).
- Exercise: [fill-in, focus: Complete sentences with the correct -но/-то form of the given verb, 8 items]

## Порівняння трьох конструкцій (~660 words total)
- P1 (~140 words): Side-by-side comparison of the "Naturalness Triangle." Scenario: The construction of a bridge. 1. Active: "Робітники збудували міст" (Most natural). 2. Impersonal: "Міст збудовано" (Natural focus on result). 3. -ся Passive: "Міст будувався робітниками" (Stiff/Academic).
- P2 (~160 words): Decision Tree for Learners. Step 1: Can I use active? (Yes -> use it). Step 2: Do I want to focus on the result without the doer? (Yes -> use -но/-то). Step 3: Is it a generic state/process of an object? (Yes -> -ся is okay).
- P3 (~140 words): Contrastive analysis of English "is/was" vs Ukrainian. Showing that English uses passive for things Ukrainian does with active or impersonal. Example: "I was told" -> "Мені сказали" (active impersonal) vs "*Я був сказаний" (nonsense).
- P4 (~120 words): Summary table of constructions: Subject, Verb Form, Agent Case, and Naturalness Rating (1-3 stars). Specific examples for each: "Магазин відчинено" (***) vs "Магазин відчиняється" (**).
- Exercise: [match-up, focus: Match active sentences to their -но/-то equivalents, 8 items]

## Практика: пасив у контексті (~800 words total)
- Dialogue (~150 words): Tour of a renovated Cultural Palace in Dnipro. Архітектор: "Цей зал був побудований у 1960-х, але зараз його повністю реставровано." Журналіст: "Вхід буде відкрито завтра?" Архітектор: "Так, усі роботи завершено вчасно." Focus on mix of passive forms.
- P1 (~180 words): Reading passage: A news report titled "У центрі міста відкрито нову виставку." The text describes the event using -но/-то forms (виставку організовано, картини виставлено, квитки продано) and -ся forms (виставка вважається унікальною).
- P2 (~150 words): Analysis of the reading passage. Why did the journalist use "виставку відкрито" instead of "ми відкрили виставку"? Discussing the "official objective" tone of news reporting.
- P3 (~140 words): Transformation Drill in context. Taking the news report and "humanizing" it by rewriting sections into active voice (Уряд організував... -> Замість: Урядом організовано...).
- P4 (~180 words): Production task: Writing a 6-sentence status report for a manager. "Звіт надіслано. Бюджет ухвалено. Переговори проведено. Усі документи підписано." Focus on the professional utility of the -но/-то passive.
- Exercise: [sentence-builder, focus: Transform active sentences to -но/-то passive and vice versa, 8 items]

## Підсумок та перехід до M24 (~450 words)
- P1 (~150 words): Summary of core concepts: 
    - Пасивний стан: підмет — об'єкт дії. 
    - Дві форми: -ся (процес) та -но/-то (результат).
    - Український стиль: активний стан — найкращий, -но/-то — другий кращий, -ся з агентом — уникати. 
    - -но/-то вимагає знахідного відмінка додатка (Книгу прочитано).
- P2 (~150 words): Self-check questions:
    - Чи можу я відрізнити "Книга читається" від "Дівчина вмивається"? (Yes/No)
    - Чи знаю я, що після "Зроблено" йде знахідний відмінок? (Yes/No)
    - Чи можу я перетворити "Ми купили хліб" на "Хліб куплено"? (Yes/No)
    - Чи розумію я, чому "активний стан" — це круто? (Yes/No)
- P3 (~150 words): Preview of Module 24. Transitioning from the relationship between subject/verb (Voice) to the internal building blocks of the verb itself. Introducing how prefixes (префікси) and suffixes (суфікси) change meaning: писати -> підписати, збудувати -> розбудувати. This will complete the grammar Phase 3 on Verbs.

Grand total: ~4350 words
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
