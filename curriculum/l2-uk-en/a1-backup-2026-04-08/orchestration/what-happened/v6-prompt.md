

---

## Your Writing Identity

**You are: Patient & Supportive Ukrainian Tutor.** Your persona is *The Helpful Teacher*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 1.0.0 | updated: 2026-03-27 -->
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
dialogue_situations:
- setting: 'Monday morning at work — sharing weekend: Я ходив на концерт (m). Я читала
    роман (m). Ми гуляли в парку (m). Він дивився фільм (m). Вона готувала вечерю
    (f).'
  speakers:
  - Колеги (coworkers)
  motivation: Past tense with концерт(m), роман(m), парк(m), фільм(m), вечеря(f)
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

## Pre-Verified Facts (from MCP tools — use these, do NOT guess)

A verification step already called VESUM, textbooks, Правопис, and style guide tools. The results below are GROUND TRUTH. Use them:
- If a word is marked ❌ NOT IN VESUM — do NOT use it
- If a textbook excerpt is provided — use that pedagogy
- If a calque is flagged — use the correct alternative
- If CEFR says a word is above target — find a simpler synonym

You do NOT need to call tools yourself — the facts are already verified.

<pre_verified_facts>
## VESUM Verification

**45/45 word forms confirmed — zero failures.**

- ✅ **учора** — adv
- ✅ **робити** — verb → робив / робила / робило / робили (all confirmed)
- ✅ **читати** — verb → читав / читала / читало / читали (all confirmed)
- ✅ **працювати** — verb → працював / працювала / працювало / працювали (all confirmed)
- ✅ **гуляти** — verb → гуляв / гуляла / гуляло / гуляли (all confirmed)
- ✅ **готувати** — verb → готував / готувала / готувало / готували (all confirmed)
- ✅ **дивитися** — verb → дивився / дивилася / дивилося / дивилися (all confirmed)
- ✅ **говорити** — verb → говорив / говорила / говорило / говорили (all confirmed)
- ✅ **минулий** — adj (3 VESUM entries — adj declension forms confirmed)
- ✅ **вихідні** — adj/noun (6 VESUM entries — covers both uses: вихідний день + вихідні pl noun)
- ✅ **субота** — noun
- ✅ **неділя** — noun
- ✅ **разом** — adv
- ✅ **фільм** — noun (2 entries)
- ✅ **провести** — verb → провів / провела (both confirmed)

Not found: **none**

---

## Textbook Excerpts

### Section: Минулий час (Past Tense) — formation rule

> «Форму минулого часу мають дієслова доконаного й недоконаного виду: робив і зробив, грав і зіграв. Дієслова в минулому часі змінюються за родами й числами. Форми дієслів минулого часу утворюємо від основи інфінітива (треба відкинути суфікс -ти) суфіксальним способом: значити → значи+в, значи+л(а), значи+л(о), значи+л(и).»
> Source: **Литвинова, Grade 7** (Tier 1 — NUS 2022+)

> «Дієслова минулого часу змінюються за числами: думав — думали, а в однині — за родами: думав, думала, думало. Можуть означати завершену дію (придумав) або незавершену (думав).»
> Source: **Захарійчук, Grade 4** (Tier 2)

**Key textbook table (Захарійчук Grade 4) — exactly matches plan paradigm:**
| чоловічий | жіночий | середній | Множина |
|-----------|---------|----------|---------|
| читав | читала | читало | читали |

✅ The plan's pedagogical approach (remove -ти, add gender suffixes) matches Grades 4 & 7 Ukrainian textbooks precisely. The distinction "past tense marks GENDER, not person" is explicitly confirmed in official textbooks.

### Section: Dialogues — How did you spend the weekend?

> «Складіть і розіграйте діалог (телефонну розмову) між однокласниками (однокласницями) про те, як минув вихідний день.»
> Source: **Глазова, Grade 11** (Tier 2)

✅ Textbook validation: talking about how one's weekend/day passed is a canonical dialogue situation in Ukrainian pedagogy from Grade 4 onwards. The dialogue format in the plan (phone call / casual exchange) is fully grounded in textbook practice.

> «Що зробив Олег? — накреслив (дія відбулася до того, як про неї повідомили — минулий). Що робить Олег? — вирізує (теперішній).»
> Source: **Варзацька, Grade 4** (Tier 2)

✅ The contrast present vs. past tense (what are you doing? vs. what did you do?) is a core Grade 4 concept — appropriate to recycle at A1.8.

### Section: Вихідні — days & narration

> «У суботу розглядала Київський собор. У неділю черепаха вигукнула: "О! Буду малювати капці та пальто!" — Випиши назви днів тижня. Склади речення з двома словами. Зразок. У суботу я ... . У неділю я ... .»
> Source: **Большакова, Grade 2** (Tier 2)

✅ The exact pattern "У суботу я [verb]... У неділю я [verb]..." from the plan is used verbatim in Bolshakova's Grade 2 textbook as a model sentence-building task. Perfect pedagogical grounding.

### Section: Практика — past tense paradigm drill

> «Утворіть від дієслів усі можливі форми минулого часу (за зразком). Зразок. Марити — марив, марила, марило, марили. Марити, робити, принести, бігти, писати, будувати...»
> Source: **Авраменко, Grade 7** (Tier 1 — NUS 2022+)

✅ The practice section's verb paradigm tables (робити → робив/робила/робило/робили, etc.) directly mirror the standard Ukrainian school drill format from Авраменко Grade 7. **Author priority match confirmed.**

---

## Grammar Rules

**Правопис 2019 note:** The 2019 Правопис covers orthography and spelling rules, not verb morphology/conjugation paradigms. Past tense formation is a morphological rule governed by grammar textbooks, not the spelling rulebook — the empty query result is correct and expected.

**Authoritative source for past tense formation (from textbooks):**
- **Rule**: Минулий час = основа інфінітива (відкинути -ти) + суфікс **-в** (чол. р.), **-ла** (жін. р.), **-ло** (сер. р.), **-ли** (мн.) 
- **Source**: Литвинова Grade 7, §"Минулий час" (Tier 1); Авраменко Grade 7, §29 (Tier 1)
- **Exception pattern flagged by textbooks**: If infinitive stem ends in a consonant (нести, могти), чол. р. has **no -в**: ніс, міг (but несла, могла). ✅ None of A1.8's target verbs trigger this exception — all end in vowel stems (-ати, -ити, -увати).

**Reflexive verb note (дивитися → дивився):** The reflexive suffix -ся contracts to **-сь** after -л- in past tense (дивився, not дивилася for чол. р.). VESUM confirms: дивився (чол. р.) / дивилася (жін. р.) / дивилося (сер. р.) / дивилися (мн.). ✅ Plan correctly shows all four forms.

---

## Calque Warnings

- **провести вихідні**: ✅ OK — Антоненко-Давидович discusses *вихідні* in the context of number agreement (два вихідні дні) and confirms the word is standard Ukrainian. The phrase "провести вихідні" is natural Ukrainian (cf. "провести час" = to spend time — confirmed via VESUM). No calque found.
- **дивитися фільм**: ✅ OK — No calque warning in style guide. "Дивитися фільм" is natural Ukrainian (direct object, accusative). No Russian interference pattern detected.
- **гуляти в парку**: ✅ OK — Style guide does not flag "гуляти" as a Russianism or calque. The verb is confirmed Ukrainian (VESUM: гуляти/verb). The locative phrase "в парку" is natural Ukrainian syntax.

**No calques detected in the plan vocabulary.**

---

## CEFR Check

| Word | PULS Level | Status |
|------|-----------|--------|
| учора | **A1** (прислівник) | ✅ On target |
| субота | **A1** (іменник) | ✅ On target |
| неділя | **A1** (іменник) | ✅ On target |
| фільм | **A1** (іменник) | ✅ On target |
| вихідні | **A1** (іменник + прикметник) | ✅ On target |
| разом | **A1** (прислівник) | ✅ On target |
| провести | **A2** (дієслово, доконаний вид) | ⚠️ One level above target |

**Flag — провести (A2):** PULS classifies провести as A2. It appears in the key dialogue question "Як ти провів вихідні?" The imperfective counterpart проводити is also A2. 

**Recommendation:** At A1.8 (the graduation module), introducing one bridging A2 verb in a high-frequency, memorable phrase ("Як ти провів вихідні?") is pedagogically defensible — this module's purpose is to consolidate A1 and preview A2. However, the writer should:
1. Gloss it explicitly in the словнік as "провести/провів — to spend (time), A2 preview"
2. Not drill it as a production target — use it receptively in the dialogue only
3. Keep the active practice verbs (читати, гуляти, готувати, дивитися, говорити, працювати) — all confirmed A1
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
# Verified Knowledge Packet: What Happened?
**Module:** what-happened | **Phase:** A1.8 [Past, Future, Graduation]
**Textbook grades searched:** 5, 6, 7

---

## Dialogues

> **Source:** kovalenko, Grade 6
> **Section:** Сторінка 221
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
> 6. Чому Ігоря Чалагу називають тяжким підлітком? Через які 
> епізоди та авторські характеристики це виявлено у творі?
>  
> 7. Якою була атмосфера в класі? Наведи цитати на підтвердження 
> своєї думки.
>  
> 8. Усно проаналізуй стосунки Терези та Ігоря. Чому хлопець 
> змінився? Ти віриш цим змінам? Чому?
>  
> 9.

## Минулий час (Past Tense)

> **Source:** avramenko, Grade 6
> **Section:** Сторінка 45
> **Score:** 0.50
>
> В. Прочитайте текст удруге й докладно його перекажіть (усно).

## Практика (Practice)

> **Source:** zabolotnyi, Grade 7
> **Section:** Сторінка 62
> **Score:** 0.33
>
> 58
> 58
> Виконайте тестові завдання. 
> 1. У формі теперішнього часу вжито обидва дієслова в рядку
> А співаю, спізнишся  
> В шепочу, усміхаєшся
> Б міркую, подорожували
> Г прочитаємо, мріємо
> 2. Дієслово у формі майбутнього часу вжито в словосполученні 
> А вивчатимемо напам’ять
> В розцвітає навесні 
> Б просили прочитати
> Г віримо в перемогу
> 3. Дієслово у  формі минулого часу вжито в кожному реченні, ОКРІМ
> А З брудної води ще ніхто чистим не вийшов (Нар. творчість).
> Б  Топчуть ноги радісно і струнко сонні трави на вузькій межі
> (О. Теліга).
> В  Гнучка гілка клена тулилася зранку до чистої шибки вікна 
> (І. Ільків).
> Г  Вузлуваті натруджені дуби важко розкинули нерухомі шат ра
> (М. Стельмах).
> Відновіть речення, уживаючи на місцях пропусків особові дієслова у відпо-
> відній часовій формі, й запишіть.

> **Source:** golub, Grade 5
> **Section:** Сторінка 187
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
> розкодовуємо і розуміємо текст. Однак прискорення руху 
> нейронів* у мозку — то ще не головна вигода. Найціннішими 
> вважають терапевтичні показники читання. Кора головного 
> мозку блискавично задіює наш чуттєвий досвід, тому коли 
> людина читає про погоню — її пульс може пришвидшувати-
> ся, а коли про смаколики — у роті набігає слина (За 
> Ю.

## Summary

> **Source:** mishhenko, Grade 7
> **Section:** Сторінка 200
> **Score:** 0.50
>
> З ним була… його київ-
> ська Іринка. Ішли бадьоро, сміючися і перекидаючися новеньким фут-
> больним м’ячем.

## Grammar Reference

> **Source:** kovalenko, Grade 6
> **Section:** Сторінка 238
> **Score:** 0.50
>
> — Ти що тут робиш?
> — Пильную, — поважно відповіла вона.
> — Навіщо?
> — Бабця хотіла тебе розбудити. Я не дала.
> Вона таємничо підморгнула мені:
> — Я бачила, що у тебе тут вночі світло було…
> — Ну ти й нишпорка! — посміхнувся я.
> — А що ти робив? Читав?
> — Так, читав.
> — А де ж книжка? — продовжувала допитувати вона.
> Я знітився. Ну що тут скажеш? І відповів так:
> — А я її сам пишу! Тому і не спав!
> — Ух ти! — вигукнула дівчинка. — Сам? Справжню книж-
> ку? Не брешеш?!
> — Так, — сказав я. — Але це поки що секрет. Добре?
> — Звісно! Таємниця в слоїку! — підтвердила Нійолє і зро-
> била жест, ніби зачиняє на ключик вуста. — А про що твоя 
> книжка?
> Я замислився. І раптом зіскочив з ліжка, підхопив дівчин-
> ку і закружляв з нею по веранді.
> Ура! Вона мала рацію.


## МійКлас Theory (miyklas.com.ua)

*Ukrainian school curriculum theory — use this terminology and teaching approach.*

### Рід іменників
> **Source:** МійКлас — [Рід іменників](https://www.miyklas.com.ua/p/ukrainska-mova/6-klas/imennik-43064/rid-imennikiv-42978)

### Теорія:

*www.ua.pistacja.tv*  
**Рід притаманний кожному іменнику в однині**. Іменники мають постійне значення **роду**:
чоловічого: *день, зошит, комп'ютер*,  жіночого: *книга, земля, машина*, середнього: *сонце, місто, озеро*, спільного: *суддя, сирота, нечема, забіяка.*
Іменники чоловічого роду співвідносні з займенником він, жіночого роду — вона, середнього роду — воно.
 
**Іменники за родами **не змінюються.

### Займенник як частина мови
> **Source:** МійКлас — [Займенник як частина мови](https://www.miyklas.com.ua/p/ukrainska-mova/6-klas/zaimennik-51336/zaimennik-iak-chastina-movi-pravilne-nagoloshuvannia-zaimennikovikh-form-51337)

### Теорія:

*www.ua.pistacja.tv*  
Займенник — це самостійна змінна частина мови, яка лише вказує на предмети, їхні ознаки або кількість, не називаючи їх, і відповідає на питання хто? що? який? чий? скільки? котрий?  
Морфологічні ознаки займенника
Усі займенники змінюються за** **відмінками: *хто — кого, кому, ким, \(на\) кому.*
Деякі займенники змінюються ще й за родами та числами: *чий — чия, чиє, чиї.*
Синтаксична роль займенників
У реченні займенник найчастіше виступає:
- підметом: *Вчора **я** ходив у школу. **Хтось** зазирнув у вікно.* 
- означенням: *Зараз розповім про **свої** плани. **Ці** дівчатка не з нашого класу.* 
- додатком: *Щось **тебе** не бачу.* 
Зрідка —  частиною  присудка: *Щось ти сьогодні **ніякий.***
*** *** 
Зверни увагу\!

### Розряди займенників за значенням
> **Source:** МійКлас — [Розряди займенників за значенням](https://www.miyklas.com.ua/p/ukrainska-mova/6-klas/zaimennik-51336/rozriadi-zaimennikiv-za-znachenniam-zaimenniki-iak-zasib-zv-iazku-rechen_-467947)

### Теорія:

*www.ua.pistacja.tv*  
 
Особові займенники
Указують на осіб, інших істот, предмети, явища і поняття: *я, ти, він, вона, воно, ми, ви, вони*.
Особові займенники бувають трьох осіб, змінюються за числами і відмінками; займенник **він** змінюється також за родами.
Зверни увагу\!
Для виявлення ввічливого ставлення до співрозмовника в українській мові займенники *ти*, *твій* замінюють займенниками *Ви*, *Ваш *у звертаннях до однієї особи. Ці займенники пишуться з великої літери: 
*— Привів, Насте Василівно, Вам свого школяра. Може, і з нього буде якийсь толк \(Михайло Стельмах\).*
Зворотний займенник
*Зворотний* займенник *себе* вказує на того, хто виконує дію.

---
**Total textbook excerpts found:** 7
**Grades searched:** 5, 6, 7
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
  1. **Monday morning at work — sharing weekend: Я ходив на концерт (m). Я читала роман (m). Ми гуляли в парку (m). Він дивився фільм (m). Вона готувала вечерю (f).**
     Speakers: Колеги (coworkers)
     Why: Past tense with концерт(m), роман(m), парк(m), фільм(m), вечеря(f)

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

**Required:** учора (yesterday), робити (to do), читати (to read), працювати (to work), гуляти (to walk), готувати (to cook), дивитися (to watch), говорити (to speak)
**Recommended:** минулий (past, adj), вихідні (weekend, pl), субота (Saturday, f), неділя (Sunday, f), разом (together), фільм (film, m), провести (to spend time)

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
## Dialogues (~330 words total)

- P1 (~20 words): Brief scene-setting — Monday morning at the office, two colleagues meet by the coffee machine and catch up on the weekend.
- Dialogue 1 (~110 words): 8-turn exchange. Oksana asks Dmytro: "Що ти робив учора?" He answers: "Я читав книжку." She asks: "А яку?" He: "Детектив. А ти?" She: "Я готувала вечерю." He: "А що робив Тарас?" She: "Він гуляв у парку." He: "А Олена?" She: "Вона працювала весь день." Margin gloss: робив (♂) / робила (♀) — same verb, different ending.
- P2 (~20 words): Transition — the next day, Bohdan and Mariia compare their full weekends; note "провів/провела вихідні."
- Dialogue 2 (~110 words): 8-turn exchange. Bohdan: "Як ти провела вихідні?" Mariia: "Чудово! У суботу я ходила в кафе з подругою." Bohdan: "А в неділю?" Mariia: "У неділю я дивилася фільм вдома. А ти?" Bohdan: "Я провів суботу вдома — готував і читав. А в неділю ми гуляли в парку з братом." Mariia: "Як приємно!" Margin gloss: ходила / провела / дивилася (♀); провів / готував / гуляли (♂/pl).
- P3 (~20 words): One-sentence bridge — "notice that every verb changed its ending depending on who is speaking — that is exactly what you will learn now."
- Exercise (fill-in, ~50 words): 3 quick gap-fill sentences from Dialogue 1, isolating the gender ending: "Тарас {гуляв|гуляла|гуляли} у парку." / "Олена {працювала|працював|працювали} весь день." / "Що ти {робив|робила|робили} учора, Маріє?" — sets up the grammar section.

---

## Минулий час (Past Tense) (~330 words total)

- P1 (~70 words): Introduce the core insight — Ukrainian past tense is not built on person (я/ти/він) but on **gender**. Compare present tense briefly: "я читаю / ти читаєш / він читає" (person endings) vs past tense: "я читав / ти читав / він читав" (same form — all masculine). Same для жіночого роду: "я читала / ти читала / вона читала." Show this contrast in a two-column mini-table: Present (person changes) | Past (gender changes).
- P2 (~80 words): Step-by-step formation rule. Take the infinitive → remove -ти → add the gender ending. Walk through **читати**: читати → чита- → він читав / вона читала / воно читало / вони читали. Then **гуляти**: гуляти → гуля- → він гуляв / вона гуляла / воно гуляло / вони гуляли. Repeat with **працювати**: він працював / вона працювала / воно працювало / вони працювали. Box the four endings: -в (він), -ла (вона), -ло (воно), -ли (вони).
- P3 (~60 words): Highlight the special pattern for reflexive verbs (-ся). **дивитися**: він дивився / вона дивилася / воно дивилося / вони дивилися — the -ся stays after the gender ending. Two example sentences: "Тарас дивився фільм." / "Ірина дивилася серіал." Contrast with "читати" (no -ся) to make the pattern visible.
- P4 (~70 words): The gender-for-я insight — the same speaker says different forms depending on their own gender: "Я читав книжку." (male speaker) vs "Я читала книжку." (female speaker). Same meaning, same person, different ending. Reinforce with Що ти робив/робила? — show both question forms side by side. Add: "Вони завжди закінчується на -ли — множина не розрізняє рід." Four example sentences with різними суб'єктами: Він / Вона / Я (м.) / Я (ж.).
- Exercise (matching, ~50 words): Match pronoun/name to correct past tense form of **говорити**: він → говорив | вона → говорила | воно → говорило | вони → говорили | Тарас → говорив | Олена → говорила. Reinforces the paradigm just taught before moving to practice.

---

## Практика (Practice) (~330 words total)

- P1 (~70 words): Present the six core A1.3 verbs in a full past-tense paradigm table: читати, працювати, гуляти, готувати, дивитися, говорити — four columns (він / вона / воно / вони). Briefly note that the stem of each verb is already familiar; only the ending is new. Point out the -ся pattern again in the дивитися row.
- Exercise 1 (fill-in, ~60 words): 6 gap-fill sentences testing form selection based on a named subject — items from activity_hints: "Учора він {читав|читала|читати} книжку." / "Олена {готувала|готував|готували} вечерю." / "Ми {гуляли|гуляв|гуляла} в парку." / "Вони {працювали|працював|працювало} разом." / "Тарас {дивився|дивилася|дивилися} фільм." / "Що ти {робив|робила|робили} учора, Іване?"
- P2 (~80 words): Build sentences about the past using time expressions. Introduce **учора** (yesterday) and **минулого тижня** (last week) with four model sentences: "Учора я читав цікаву книжку." / "Минулого тижня вона працювала в офісі." / "У суботу ми гуляли в парку." / "В неділю вони готували вечерю разом." Show how the time word comes first (fronted for emphasis — natural Ukrainian word order) but doesn't change the verb form.
- Exercise 2 (fill-in gender-based, ~60 words): 3 sentences where the subject's gender determines the ending — from activity_hints: "Марія {дивилася|дивився|дивилися} фільм." / "Мій брат {гуляв|гуляла|гуляли} у парку." / "Вони {провели|провів|провела} вихідні разом." Learner must identify subject gender to choose correctly.
- P3 (~60 words): Short production prompt — two model mini-conversations using Що ти робив/робила учора?: "— Що ти робив учора, Андрію? — Я читав і гуляв у парку. — А ввечері? — Ввечері я дивився фільм." And the female version: "— Що ти робила учора, Оксано? — Я готувала вечерю і потім говорила з мамою." Learner notices both forms of the question.

---

## Summary (~330 words total)

- P1 (~80 words): Recap the formation rule in plain language: infinitive stem + -в (він), -ла (вона), -ло (воно), -ли (вони). Restate the key insight in a highlighted box: "In Ukrainian, the past tense ending agrees with the GENDER of the subject — not the grammatical person. Я читав and він читав are identical because both subjects are masculine. Я читала and вона читала are identical because both are feminine." Contrast explicitly with English ("I read / she read" — no gender marking).
- P2 (~70 words): Gather all six verbs in past tense side-by-side (він / вона) for quick visual review: читав/читала, працював/працювала, гуляв/гуляла, готував/готувала, дивився/дивилася, говорив/говорила. Add plural row: читали, працювали, гуляли, готували, дивилися, говорили. Label the endings visually: **-в / -ла / -ло / -ли**. Remind: вони always ends in -ли regardless of gender.
- P3 (~80 words): Useful phrases for talking about the past — four ready-made conversation starters: "Що ти робив/робила учора?" / "Як ти провів/провела вихідні?" / "Учора я {verb}-в/-ла {object}." / "Ми {verb}-ли разом." Show each with a completed example. Note the paired question forms robiv/robyla are both correct — one for masculine, one for feminine interlocutors.
- Self-check (~100 words): Bulleted Q&A checklist —
  - Can you form the past tense of **читати** for all four forms? (читав / читала / читало / читали)
  - What ending does **вони** always take? (-ли)
  - What past-tense form would a female speaker use for "I worked"? (я працювала)
  - How do you ask "What did you do?" to a male friend? (Що ти робив?)
  - How to a female friend? (Що ти робила?)
  - Production task: Tell your partner three things you did last week using three different verbs — use your correct gender ending for **я**.

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
