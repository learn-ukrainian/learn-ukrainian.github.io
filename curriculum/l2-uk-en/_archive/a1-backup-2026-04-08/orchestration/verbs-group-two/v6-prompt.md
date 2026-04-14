

---

## Your Writing Identity

**You are: Patient & Supportive Ukrainian Tutor.** Your persona is *The Helpful Teacher*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **17: Verbs Group II** (A1, A1.3 [Actions]).

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

1. **IMMERSION TARGET: 15-25% Ukrainian** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if you exceed it. For early modules, the learner CANNOT READ CYRILLIC — English must dominate. Ukrainian appears only as bolded inline words/phrases. Do NOT write long Ukrainian passages, Ukrainian-only paragraphs, or Ukrainian text without English translation.
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
module: a1-017
level: A1
sequence: 17
slug: verbs-group-two
version: '1.2'
title: Verbs Group II
subtitle: Говорю, говориш, говорить — the second pattern
focus: grammar
pedagogy: PPP
phase: A1.3 [Actions]
word_target: 1200
objectives:
- Conjugate Group II (-ити) verbs in present tense for all persons
- Distinguish Group I (-єш/-є/-ють) from Group II (-иш/-ить/-ять) endings
- Use 6 high-frequency Group II verbs in sentences
- Compare and contrast both conjugation groups
dialogue_situations:
- setting: At a gym — two friends doing different exercises, describing actions
  speakers:
  - Тарас
  - Микола
  motivation: 'Group II verbs: бачиш, говориш, робиш in physical context'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Talking about abilities (ULP Ep24 pattern): — Ти говориш українською?
    — Так, я говорю трохи. А ти? — Я бачу, що ти добре говориш! — Дякую, я вчуся.
    Group II verbs in natural conversation.'
  - 'Dialogue 2 — Evening at home: — Що ти робиш увечері? — Я дивлюся фільм. А ти?
    — Я вчу нові слова. — Молодець! Note: дивлюся (I watch) — the -ся ending means
    ''oneself'' (preview for M20).'
- section: Друга дієвідміна (Group II Verbs)
  words: 300
  points:
  - 'Group II verbs have infinitive in -ити (or -іти): говорити → я говорю, ти говориш,
    він/вона говорить, ми говоримо, ви говорите, вони говорять. Pattern: stem + -ю/-у,
    -иш, -ить, -имо, -ите, -ять/-ать.'
  - 'Six essential Group II verbs: говорити (to speak): говорю, говориш, говорить...
    бачити (to see): бачу, бачиш, бачить... робити (to do/make): роблю, робиш, робить...
    вчити (to study/teach): вчу, вчиш, вчить... просити (to ask/request): прошу, просиш,
    просить... ходити (to go/walk regularly): ходжу, ходиш, ходить...'
- section: Група I чи II? (Which Group?)
  words: 300
  points:
  - 'Compare the endings side by side: | | Group I (-ати) | Group II (-ити) | | я
    | читаю | говорю | | ти | читаєш | говориш | | він/вона | читає | говорить | |
    вони | читають | говорять | Key difference: ти form → -єш (I) vs -иш (II), вони
    → -ють (I) vs -ять/-ать (II). Note: after sibilants (ч, ш, ж, щ) → -ать (not -ять):
    бачать (not *бачять), кричать. Other consonants → -ять: говорять, ходять.'
  - 'Consonant changes in Group II (я-form only): робити → роблю (б→бл), ходити →
    ходжу (д→дж), просити → прошу (с→ш), бачити → бачу (no change). These changes
    only affect the я-form — all other forms are regular. Don''t memorize the rule
    — just learn each я-form with the verb.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Two verb groups — two ending patterns: Group I (-ати): -ю, -єш, -є, -ємо, -єте,
    -ють Group II (-ити): -ю/-у, -иш, -ить, -имо, -ите, -ять Consonant shifts in Group
    II я-form (роблю, ходжу, прошу). Self-check: Conjugate ''бачити'' for я, ти, він/вона.
    Is ''слухати'' Group I or II? How about ''говорити''?'
vocabulary_hints:
  required:
  - говорити (to speak)
  - бачити (to see)
  - робити (to do/make)
  - вчити (to study/teach)
  - просити (to ask/request)
  - ходити (to go/walk regularly)
  recommended:
  - дивитися (to watch — reflexive preview)
  - вчитися (to learn — reflexive preview)
  - любити (to love — review, Group II!)
  - трохи (a little)
  - добре (well)
  - увечері (in the evening)
activity_hints:
- type: fill-in
  focus: 'Conjugate: я говор__, ти говор__, він говор__'
  items: 10
- type: group-sort
  focus: Sort verbs into Group I (-ати) and Group II (-ити)
  items: 10
- type: quiz
  focus: 'Choose correct form: Ти (бачу/бачиш/бачить) це?'
  items: 8
- type: fill-in
  focus: 'Complete with correct verb form: Вона ___ українською. (говорити)'
  items: 6
connects_to:
- a1-018 (I Want, I Can)
prerequisites:
- a1-016 (Verbs Group I)
grammar:
- 'Group II conjugation: -ю/-у, -иш, -ить, -имо, -ите, -ять'
- 'Consonant changes in я-form: б→бл, д→дж, с→ш, т→ч'
- Distinguishing Group I vs Group II by endings
register: розмовний
references:
- title: Караман Grade 10, p.179
  notes: 'І vs ІІ дієвідміна: endings and infinitive patterns.'
- title: Захарійчук Grade 4, p.110-113
  notes: Verb conjugation tables for present tense.
- title: ULP Season 1, Episode 24
  url: https://www.ukrainianlessons.com/episode24/
  notes: More verbs and conjugation practice.

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

**Confirmed (12/12 infinitives):**
- ✅ говорити (verb)
- ✅ бачити (verb)
- ✅ робити (verb)
- ✅ вчити (verb)
- ✅ просити (verb)
- ✅ ходити (verb)
- ✅ дивитися (verb)
- ✅ вчитися (verb)
- ✅ любити (verb)
- ✅ трохи (adv)
- ✅ добре (adv)
- ✅ увечері (adv)

**All conjugated forms confirmed (24/24):**
говорю, говориш, говорить, говоримо, говорите, говорять ✅
бачу, бачиш, бачить, бачимо, бачите, **бачать** ✅ (correct -ать, not *бачять)
роблю, робиш, робить ✅
ходжу, ходиш, ходять ✅
прошу, просиш, просить ✅
вчу, вчиш, вчить ✅

**Not found:** none — all words verified.

---

## Textbook Excerpts

### Section: Друга дієвідміна (Group II Verbs)
> "До ІІ дієвідміни належать дієслова, які в 3-й особі множини мають закінчення -ать (-ять). НАПРИКЛАД: стоять, кричать, заносять."
> "Дієслова ІІ дієвідміни в усіх особових закінченнях (крім 1-ї особи однини та 3-ї особи множини) мають букву и (ї)."
> Source: Литвинова, Grade 7 (tier 1, NUS 2024), §10 Дієвідмінювання дієслів

> Full paradigm table for Group I vs II confirmed (І: пишу/пишеш/пише/пишемо/пишете/пишуть vs ІІ: вчу/вчиш/вчить/вчимо/вчите/вчать):
> Source: Литвинова, Grade 7 (tier 1), p.52

### Section: Група I чи II? (Which Group?)
> "Існує два способи визначити дієвідміну та з'ясувати, яке закінчення правильне. Утворити форму 3-ї особи множини: ходити — ходять (ІІ дієвідміна)."
> Source: Литвинова, Grade 7 (tier 1), §10

> "І дієвідміна: -у(-ю), -еш(-єш), -е(-є), -емо(-ємо), -ете(-єте), -уть(-ють) | ІІ дієвідміна: -у(-ю), -иш(-їш), -ить, -имо, -ите, -ать(-ять)"
> Source: Караман, Grade 10, §71

> Key rule confirmed: **ти-form** → -єш (Group I) vs -иш (Group II); **вони-form** → -ють (Group I) vs -ять/-ать (Group II).
> Source: Авраменко, Grade 11, p.51

### Section: Consonant Alternations (Plan: Чергування у 1 ос. одн.)
> "В особових формах дієслів теперішнього і майбутнього часу чергуються приголосні: [д]→[дж]: водити — воджу | [с]→[ш]: носити — ношу | [з]→[ж]: возити — вожу | [т]→[ч]: крутити — кручу"
> Source: Глазова, Grade 10, §26 Чергування приголосних звуків

> Additional confirmation: [д]→[дж] ходити — ходжу (Авраменко Grade 5 §50); народити — народжувати
> Source: Авраменко, Grade 5 (tier 1), §50

### Section: Діалоги (Dialogues — evening at home, abilities)
> The textbook corpus has Grade 10 rhetoric examples using говорити ("Від уміння говорити нерідко залежить успіх"). No direct A1 dialogue about language abilities exists in the textbooks — the plan dialogue ("Ти говориш українською? — Так, я говорю трохи.") is pedagogically appropriate as an original construction grounded in the ULP Ep24 pattern. ✅ no textbook contradiction.
> Source: Заболотний, Grade 10, p.45

---

## Grammar Rules

- **Group II -ать after sibilants**: After ч, ш, ж, щ, the 3rd-person plural ending is **-ать** (not -ять). бачать ✅, кричать ✅. Confirmed by Зabolotnyi Grade 7 table and Litvinova Grade 7 §10. Note: This rule is stated correctly in the plan ("після шиплячих → -ать").

- **Consonant alternations in я-form only**: Confirmed by Glazova Grade 10 §26 and Avramenko Grade 5 §50 — changes occur in present/future tense personal forms. The plan correctly states these changes only affect the я-form for these particular verbs.

- **Правопис 2019 note**: The query for "дієслово" and "особові закінчення дієслів" did not resolve to a specific Правопис §. Verb morphology (conjugation endings) is governed by the grammatical tradition, not a separate spelling rule — Правопис 2019 addresses spelling (and/і, е/и in suffixes), while conjugation paradigms come from grammar. No orthographic conflict found.

- **вчити vs учити**: Антоненко-Давидович confirms: "Пишемо вживати й уживати, вчити й учити залежно від того, на голосну чи приголосну кінчається попереднє слово (закон чергування у/в)." Plan correctly uses вчити (after consonant context). ✅

---

## Calque Warnings

- **дивитися фільм**: ✅ OK — not flagged as a calque by Антоненко-Давидович. Natural Ukrainian.
- **вчуся** (я вчуся / я вчу нові слова): ✅ OK — AD confirms вчитися takes genitive object ("вчити сестер грамоти"), reflexive form without object ("я вчуся") is natural. No calque risk.
- **просити (to ask/request)**: ✅ OK — but **⚠️ Pedagogical note**: the plan glosses просити as "to ask/request" — correct, but the writer should distinguish for learners that просити = to ask for something/request (a favor), NOT to ask a question (that is питати/запитувати). This is a false friend trap for English speakers.
- **молодець** (in Dialogue 2): ✅ OK — authentic Ukrainian praise word, not a calque. Антоненко-Давидович style guide has no objection.

---

## CEFR Check (PULS database)

All 12 vocabulary words confirmed A1:

| Word | PULS Level | Status |
|------|-----------|--------|
| говорити | A1 | ✅ on-target |
| бачити | A1 | ✅ on-target |
| робити | A1 | ✅ on-target |
| вчити / учити | A1 | ✅ on-target |
| просити | A1 | ✅ on-target |
| ходити | A1 | ✅ on-target |
| вчитися / учитися | A1 | ✅ on-target |
| любити | A1 | ✅ on-target |
| трохи | A1 | ✅ on-target |
| добре | A1 | ✅ on-target |
| увечері / ввечері | A1 | ✅ on-target |
| дивитися | confirmed VESUM verb; not found directly in PULS — no CEFR flag |

**No words above A1 target.** дивитися is VESUM-verified but absent from PULS list — flag as <!-- VERIFY CEFR --> but no reason to exclude.
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
# Verified Knowledge Packet: Verbs Group II
**Module:** verbs-group-two | **Phase:** A1.3 [Actions]
**Textbook grades searched:** 3, 4, 5

---

## Діалоги (Dialogues)

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 4
> **Score:** 0.50
>
> 4
> ЧОГО  Я  ВЧУСЯ?
> Вдома вчить мене матуся,
> в школі вчить мене учитель,
> і сама я добре вчуся
> рідним словом говорити.
> Вчусь не тільки говорити,
> а й читати і писати.
> Щоб усі раділи діти,
> щоб пишались мама й тато.
> Щоб пішла між люди слава,
> щоб сказали: «От дитинка
> добра, мудра і ласкава.
> Це маленька українка!»
> Що таке текст
> 1
> Розпізнаю текст за його основними ознаками
> 	 	
> 1   Прочитайте вірш Михайла Маморського. Про що розповідається 
> в кожному з речень? Чи пов’язані вони одне з одним? Чи 
> становлять ці речення текст?
> Досліди, що озна-
> чає слово канікули. 
> Де про це можна 
> діз­натися?
> Я — дослідник
> Я — дослідниця
> Поділися своїми враженнями 
> про канікули з однокласниками 
> (однокласницями). Чи можна 
> назвати твою розповідь текстом?
> Перевірте свої 
> міркування за поданим 
> висновком.

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 25
> **Score:** 0.25
>
> 25
> Вступ. Українська мова в житті українців.  Підсумовуємо й узагальнюємо
> Мова — основний засіб спілкування, але ж не єдиний. Ми 
> можемо передавати інформацію в  інший спосіб: мімікою, же-
> стами, символами, звуковими сигналами. Чому  ж тоді мову 
> вважаємо основним засобом? Річ у тім, що мовними засоба-
> ми ми можемо передати будь-яку інформацію. Для прикладу 
> спробуйте повідомити розклад ваших уроків на  завтра мімі-
> кою. Або відповісти на  запитання, котра година, жестами. 
> А  розказувати про все це за  допомогою мови легко і  звично.
> А чи міркували ви, яким  би був світ без мови? Уявіть: 
> ви прокидаєтеся зранку і  не чуєте жодного слова, не  бачите 
> жодної літери. Ви нікому не телефонуєте, не читаєте книжок, 
> журналів, бігборди на  вулицях без тексту тощо.

## Друга дієвідміна (Group II Verbs)

> **Source:** zaharijchuk, Grade 4
> **Section:** Сторінка 110
> **Score:** 0.50
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
> роблю?
> що 
> робимо?
> пливу,
> кричу
> пливемо,
> кричимо
> Однина
> Множина
> 	 Зверни увагу на особові закінчення. Постав дієслово думати в 
> усіх особових формах теперішнього часу. Запиши.

## Група I чи II? (Which Group?)

> **Source:** savchenko, Grade 4
> **Section:** Сторінка 157
> **Score:** 0.50
>
> 157
> ЗМICТ
> ЧИТАЄМО Й РОЗПОВІДАЄМО
> ПРО СВОЇ ЗАХОПЛЕННЯ
> Ліна Костенко. Вже брами літа замикає осінь…  . . . . . . . . . . . . . . . 5
> Олександра Савченко. Як читають книжки? . . . . . . . . . . . . . . . . . . 6
> Марія Манеру. Читач Максимко . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7 
> ВЕСЕЛЕ СЛОВО. Василь Марсюк. Диктант . . . . . . . . . . . . . . . . . . . 8
> Медіавіконце: види і джерела інформації . . . . . . . . . . . . . . . . . 9
> Давид Гуліа. Розум, знання і сила . . . . . . . . . . . . . . . . . . . . . . . . . . 10
> ПРАГНЕМО ЗРОЗУМІТИ СВОЇХ ПРЕДКІВ
> Як ще не було початку світа… 
> (Українська народна обрядова пісня) . . . . . . . . . . . . . . . . . . . . . . . 13
> Створення світу (За єгипетськими міфами). Переповіла Ольга Бондарук . . . . . . . . . . . . . . . . . . . . .

## Підсумок — Summary

> **Source:** varzatska, Grade 4
> **Section:** Сторінка 140
> **Score:** 0.25
>
> 140
> У третій особі однини дієслова теперішнього і май-
> бутнього часу мають закінчення ­е (­є) або ­ить, ­їть.
> У третій особі множини ці дієслова мають закінчення 
> ­уть (­ють) або ­ать (­ять).
> 297. Спиши слова. Як їх можна згрупувати?
> 298. 1. Прочитай текст. Яку картину ти уявляєш? Які слова 
> особливо яскраво передають душевний біль Кобзаря?
> «ХОЧ КРИХОТКУ ЗЕМЛІ...»
> Перебуваючи на засланні в далекій Орській фортеці, 
> майже в кожному своєму вірші Тарас Шевченко виливає 
> тугу за рідним краєм. Він просить долю, пристрасно мо-
> литься, щоб:
> ...хоч крихотку землі
> із-за Дніпра мого святого
> святії вітри принесли,
> та й більш нічого...
>  
>  
>  
>     За Василем Скуратівським
> 2. Випиши дієслова 3-ї особи однини та виділи в них за-
> кінчення.

> **Source:** varzatska, Grade 4
> **Section:** Сторінка 142
> **Score:** 0.50
>
> 142
> Якщо дієслова в 3-й особі множини мають закінчення
> то в ненаголошених особових закінченнях  
> пишемо літери
> -уть (-ють),
> е, є:
> в’я’жеш (бо в’яжуть);
> співа’ємо (бо співають).
> и, ї:
> лі’чиш (бо лічать);
> кле’їте (бо клеять).
> -ать (-ять),
> 301. Спиши слова. Яке серед них «зайве»? Поясни, чому.
> 302. 1. Прочитай дієслова.
> Запрос..те, розкле..мо, прос..ш, ход..мо, віддяч..те, 
> почеп..мо, перемага..те, розкаж..ш, друж..те, стогн..ш.
> 2. Спиши, вставляючи пропущені букви. Познач наголос.
> Міркуй так: ставлю дієслово запросите у форму 3-ї осо-
> би множини: вони (що зроблять?) — запросять. Закінчення 
> -ять. Отже, у ненаголошеному особовому закінченні пишу 
> літеру и.
> 303. 1. Прочитай текст. Яка картина постає в твоїй уяві?
> Стежинка біжить і біжить.

## Grammar Reference

> **Source:** varzatska, Grade 4
> **Section:** Сторінка 140
> **Score:** 0.25
>
> 140
> У третій особі однини дієслова теперішнього і май-
> бутнього часу мають закінчення ­е (­є) або ­ить, ­їть.
> У третій особі множини ці дієслова мають закінчення 
> ­уть (­ють) або ­ать (­ять).
> 297. Спиши слова. Як їх можна згрупувати?
> 298. 1. Прочитай текст. Яку картину ти уявляєш? Які слова 
> особливо яскраво передають душевний біль Кобзаря?
> «ХОЧ КРИХОТКУ ЗЕМЛІ...»
> Перебуваючи на засланні в далекій Орській фортеці, 
> майже в кожному своєму вірші Тарас Шевченко виливає 
> тугу за рідним краєм. Він просить долю, пристрасно мо-
> литься, щоб:
> ...хоч крихотку землі
> із-за Дніпра мого святого
> святії вітри принесли,
> та й більш нічого...
>  
>  
>  
>     За Василем Скуратівським
> 2. Випиши дієслова 3-ї особи однини та виділи в них за-
> кінчення.

> **Source:** varzatska, Grade 4
> **Section:** Сторінка 142
> **Score:** 0.50
>
> 142
> Якщо дієслова в 3-й особі множини мають закінчення
> то в ненаголошених особових закінченнях  
> пишемо літери
> -уть (-ють),
> е, є:
> в’я’жеш (бо в’яжуть);
> співа’ємо (бо співають).
> и, ї:
> лі’чиш (бо лічать);
> кле’їте (бо клеять).
> -ать (-ять),
> 301. Спиши слова. Яке серед них «зайве»? Поясни, чому.
> 302. 1. Прочитай дієслова.
> Запрос..те, розкле..мо, прос..ш, ход..мо, віддяч..те, 
> почеп..мо, перемага..те, розкаж..ш, друж..те, стогн..ш.
> 2. Спиши, вставляючи пропущені букви. Познач наголос.
> Міркуй так: ставлю дієслово запросите у форму 3-ї осо-
> би множини: вони (що зроблять?) — запросять. Закінчення 
> -ять. Отже, у ненаголошеному особовому закінченні пишу 
> літеру и.
> 303. 1. Прочитай текст. Яка картина постає в твоїй уяві?
> Стежинка біжить і біжить.


## МійКлас Theory (miyklas.com.ua)

*Ukrainian school curriculum theory — use this terminology and teaching approach.*

### Правила вживання знака м'якшення
> **Source:** МійКлас — [Правила вживання знака м'якшення](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/fonetika-grafika-orfoepiia-orfografiia-14565/pravila-vzhivannia-znaka-m-iakshennia-39904)

### Теорія:
  

*www.ua.pistacja.tv*  
 
Знаком ь позначаємо м’якість приголосних звуків на письмі.
Знак м’якшення пишемо:
- Ь пишеться після м’яких д, т, з, с, дз, ц, л, н у кінці **слова** та **складу**: *дядько, радість, низько, заносьте, гедзь, доброволець, коваль, тінь.
*  
- Після **м’яких** приголосн

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Друга дієвідміна (Group II Verbs)` (~300 words)
- `## Група I чи II? (Which Group?)` (~300 words)
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
  1. **At a gym — two friends doing different exercises, describing actions**
     Speakers: Тарас, Микола
     Why: Group II verbs: бачиш, говориш, робиш in physical context

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

**Required:** говорити (to speak), бачити (to see), робити (to do/make), вчити (to study/teach), просити (to ask/request), ходити (to go/walk regularly)
**Recommended:** дивитися (to watch — reflexive preview), вчитися (to learn — reflexive preview), любити (to love — review, Group II!), трохи (a little), добре (well), увечері (in the evening)

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
## Діалоги (Dialogues) (~330 words total)
- P1 (~40 words): Scene-setter — introduce Діалог 1. Тарас and Микола are at a language café. Тарас hears Микола speaking and reacts. Frames the question: can you speak Ukrainian?
- Dialogue 1 (~110 words): Тарас asks «Ти говориш українською?» — Микола answers «Так, я говорю трохи. А ти?» — Тарас says «Я бачу, що ти добре говориш! Де ти вчиш?» — Микола responds «Я вчу онлайн. Це нелегко, але цікаво.» — Тарас: «Я теж вчу. Ми обидва говоримо українською!» Full conjugation: говорю, говориш, говорить, вчу, вчиш, бачу — all Group II verbs in natural exchange.
- P2 (~30 words): Short connector — transition to evening scene. Note that both dialogues use the same Group II pattern — different situations, same endings.
- Dialogue 2 (~110 words): Оксана asks Богдан «Що ти робиш увечері?» — Богдан: «Я дивлюся фільм. А ти?» — Оксана: «Я вчу нові слова. А потім дивлюся серіал.» — Богдан: «Ти добре робиш — треба вчити щодня!» — Оксана: «Я прошу друга допомагати. Він говорить дуже добре.» Features: робиш, дивлюся, вчу, дивлюся, робиш, прошу, говорить. Inline gloss: дивлюся = «I watch» — the -ся ending means «oneself» (preview for M20, no analysis needed now).
- P3 (~40 words): Observation paragraph — point out three things learners should notice: (1) every verb in both dialogues follows a pattern, (2) the ти-form always ends in -иш, (3) the вони-form ends in -ять or -ять. Next section explains why.

---

## Друга дієвідміна (Group II Verbs) (~330 words total)
- P1 (~70 words): Introduce Group II — verbs whose infinitive ends in -ити (or -іти): говорити, бачити, робити, вчити, просити, ходити. These are different from Group I (-ати verbs like читати). The signal for Group II: look at the ти-form — if it ends in -иш (говориш, бачиш), it's Group II. Set up the full conjugation table of говорити as the anchor.
- P2 (~100 words): Full paradigm of говорити as master example — я говорю, ти говориш, він/вона говорить, ми говоримо, ви говорите, вони говорять. Then condensed forms for all six required verbs: бачити → бачу/бачиш/бачить/бачимо/бачите/бачать; робити → роблю/робиш/робить; вчити → вчу/вчиш/вчить; просити → прошу/просиш/просить; ходити → ходжу/ходиш/ходить. Note: вони говорять, вони бачать (after sibilants → briefly flagged, explained in next section).
- P3 (~80 words): Consonant changes — the я-form only rule. Four key shifts: б→бл (робити → роблю), д→дж (ходити → ходжу), с→ш (просити → прошу), ч→ч / no change (бачити → бачу). Emphasize: ONLY the я-form shifts. All other forms (ти, він, ми, ви, вони) are perfectly regular. Practical tip: learn the я-form separately for each verb; the rest follows automatically.
- P4 (~30 words): Micro-drill prompt — before the activity, learners try три форми mentally: «As a warm-up: say я/ти/він form of вчити and ходити out loud.»
- Activity — Fill-in (10 items): Conjugate говорити and ходити across all persons. Format: «Я говор___», «Ти ходиш — true/false», «Вони говор___», «Ми ход___», etc. Tests all six persons for both verbs. (~50 words of instruction text, not counted in prose total)

---

## Група I чи II? (Which Group?) (~330 words total)
- P1 (~90 words): Side-by-side comparison of Group I (-ати) vs Group II (-ити) endings. Full parallel table using читати vs говорити: | Особа | читати (I) | говорити (II) | — я | читаю | говорю — ти | читаєш | говориш — він/вона | читає | говорить — ми | читаємо | говоримо — ви | читаєте | говорите — вони | читають | говорять. Key insight: the -є- vowel in Group I endings (читаєш, читає) vs the -и- in Group II (говориш, говорить). That single vowel difference is the test.
- P2 (~70 words): The two fastest identification tests — (1) Check the ти-form: -єш = Group I, -иш = Group II. (2) Check the вони-form: -ють = Group I, -ять/-ать = Group II. Examples from the dialogues: бачиш → Group II (confirmed: бачать), читаєш → Group I (confirmed: читають), робиш → Group II (confirmed: роблять... wait — роблять). Stress that this is a discovery rule, not memorization.
- P3 (~80 words): The -ать vs -ять rule for вони. After sibilant consonants (ч, ш, ж, щ), the ending is -ать not -ять: бачать (not *бачять), кричать (not *кричять). After all other consonants, вони takes -ять: говорять, ходять, просять. Textbook anchor: Varzatska Grade 4, p.142 — uses the test «put the verb in 3rd plural → if -ять/-ать, you're in Group II.» Two worked examples: лічиш → лічать (Group II), співаєш → співають (Group I).
- P4 (~40 words): Reality check — most high-frequency Ukrainian verbs are Group I. But the verbs learners most need right now — говорити, робити, бачити, ходити — are all Group II. So mastering Group II unlocks exactly the core everyday verbs.
- Activity — Group-sort (10 items): Sort verbs into Group I or Group II based on infinitive + ти-form clue. Items: читати, говорити, писати, бачити, слухати, робити, малювати, ходити, грати, вчити. (~30 words instruction)
- Activity — Quiz, choose correct form (8 items): Format «Ти (бачу / бачиш / бачить) це місто?», «Вони (говорять / говорите / говоримо) швидко», «Ми (робить / робимо / роблять) домашнє завдання», etc. Tests both groups. (~30 words instruction)

---

## Підсумок — Summary (~330 words total)
- P1 (~100 words): Consolidated recap — two verb groups, two patterns. Group I (-ати verbs): endings carry -є- vowel → -ю, -єш, -є, -ємо, -єте, -ють. Group II (-ити/-іти verbs): endings carry -и- vowel → -ю/-у, -иш, -ить, -имо, -ите, -ять/-ать. Consonant changes in Group II я-form only (роблю, ходжу, прошу, бачу — ч has no change). Sibilant rule: after ч/ш/ж/щ → вони form takes -ать. State the most important single test: look at the ти-form — -єш or -иш?
- P2 (~80 words): Backward look at the dialogues — revisit Dialogue 1 and 2 with fresh eyes. Label each verb in both dialogues with its group: говориш (II), говорю (II), бачу (II), вчу (II), робиш (II), дивлюся (II), прошу (II). Note: every single verb in today's dialogues was Group II — not a coincidence. These are the highest-frequency action verbs in spoken Ukrainian.
- P3 (~100 words): Self-check — bulleted Q&A format as specified in plan:
  - Conjugate **бачити** for я, ти, він/вона: → бачу, бачиш, бачить ✓
  - Is **слухати** Group I or II? → Check ти-form: слухаєш → -єш → Group I ✓
  - Is **говорити** Group I or II? → Check ти-form: говориш → -иш → Group II ✓
  - What happens to **робити** in the я-form? → б→бл: роблю ✓
  - Вони form of **бачити** — -ять or -ать? → бачать (ч is a sibilant → -ать) ✓
- Activity — Fill-in, complete sentences (6 items): «Вона ___ українською. (говорити)», «Ми ___ у парку щодня. (ходити)», «Ти ___ гарно. (робити)», «Я ___ тебе! (бачити)», «Вони ___ нас. (просити)», «Він ___ нові слова. (вчити)». (~30 words instruction)

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
