

---

## Your Writing Identity

**You are: Patient & Supportive Ukrainian Tutor.** Your persona is *The Helpful Teacher*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **53: Health** (A1, A1.8 [Past, Future, Graduation]).

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

1. **IMMERSION TARGET: 20-35% Ukrainian** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if immersion is outside this range. For A1 early modules, the learner cannot read Cyrillic — English must dominate. For A2+, Ukrainian must carry a significant share — add Ukrainian Reading Practice blocks, dialogues, and example paragraphs to reach the target. Too little Ukrainian fails audit just as much as too much.
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
module: a1-053
level: A1
sequence: 53
slug: health
version: '1.2'
title: Health
subtitle: У мене болить голова — body parts and symptoms
focus: vocabulary
pedagogy: PPP
phase: A1.8 [Past, Future, Graduation]
word_target: 1200
objectives:
- Name basic body parts in Ukrainian (голова, рука, нога, живіт, горло, спина)
- Describe symptoms using "У мене болить..." as a chunk
- Tell a doctor or pharmacist what hurts
- Use basic health vocabulary in practical situations
dialogue_situations:
- setting: 'At the doctor''s office — describing symptoms: У мене болить голова (f,
    head). Болить горло (n, throat). Болить живіт (m, stomach). Нежить (m, runny nose).
    Кашель (m, cough). Температура (f, fever).'
  speakers:
  - Пацієнт
  - Лікар
  motivation: 'Body parts: голова(f), горло(n), живіт(m), температура(f)'
content_outline:
- section: Dialogues
  words: 300
  points:
  - 'Dialogue 1 — At the doctor''s: — Що у вас болить? — У мене болить голова і горло.
    — Давно? — З учора. І в мене температура. — Ви кашляєте? — Так, трохи. І в мене
    нежить. — Зрозуміло. Це застуда. Я випишу ліки. Відпочивайте! — Дякую, лікарю!
    Doctor visit: symptoms + basic diagnosis.'
  - 'Dialogue 2 — At the pharmacy: — Добрий день! У мене болить голова. Дайте, будь
    ласка, таблетки. — Від головного болю? — Так. І від кашлю, будь ласка. — Ось,
    будь ласка. Ще щось? — А є щось від нежиті? — Так, ось краплі. — Дякую! Скільки
    це коштує? Pharmacy: asking for medicine using known polite forms.'
- section: Тіло (The Body)
  words: 300
  points:
  - 'Essential body parts (Grade 1-2 textbooks: частини тіла): голова (head, f), горло
    (throat, n), спина (back, f), живіт (stomach, m), рука (hand/arm, f), нога (leg/foot,
    f), око (eye, n), вухо (ear, n), зуб (tooth, m), ніс (nose, m). Note: рука = whole
    arm including hand. нога = whole leg including foot. These are the most useful
    for A1 — not an anatomy lesson.'
  - 'Body part gender matters for adjectives (review from M09): велике око (big eye
    — neuter), великий ніс (big nose — masc), велика рука (big hand — fem). But at
    A1, focus on recognition — you''ll use these mainly with болить.'
- section: У мене болить... (It Hurts...)
  words: 300
  points:
  - 'The magic phrase: У мене болить + body part. У мене болить голова. (I have a
    headache. — literally ''at me hurts head'') У мене болить живіт. (My stomach hurts.)
    У мене болить горло. (My throat hurts.) У мене болить спина. (My back hurts.)
    У мене болить зуб. (I have a toothache.) Learn this as a CHUNK — don''t analyze
    the grammar (that''s dative, A2+).'
  - 'Common symptoms (as chunks): У мене температура. (I have a fever.) У мене кашель.
    (I have a cough.) У мене нежить. (I have a runny nose.) Мені холодно. (I''m cold.)
    Мені погано. (I feel bad.) Я хворий/хвора. (I''m sick. — masc/fem) Note: ''У мене
    болять зуби'' (teeth hurt — plural form болять). Just recognize it.'
- section: Summary
  words: 300
  points:
  - 'Health toolkit: Body parts: голова, горло, живіт, спина, рука, нога, око, вухо,
    зуб, ніс. Symptoms: У мене болить [body part]. У мене температура/кашель/нежить.
    State: Я хворий/хвора. Мені погано. At the doctor: Що у вас болить? — У мене болить...
    At the pharmacy: Дайте таблетки від [symptom], будь ласка. від головного болю
    (for headache), від кашлю (for cough), від нежиті (for runny nose). Self-check:
    How do you say ''My throat hurts and I have a fever''?'
vocabulary_hints:
  required:
  - голова (head, f)
  - горло (throat, n)
  - живіт (stomach, m)
  - рука (hand/arm, f)
  - нога (leg/foot, f)
  - болить (hurts — chunk: у мене болить)
  - лікар (doctor, m)
  - аптека (pharmacy, f)
  recommended:
  - спина (back, f)
  - око (eye, n)
  - вухо (ear, n)
  - зуб (tooth, m)
  - ніс (nose, m)
  - температура (fever/temperature, f)
  - кашель (cough, m)
  - нежить (runny nose, f)
  - таблетка (pill, f)
  - хворий (sick, adj)
activity_hints:
- type: match-up
  focus: Match body parts to their English translations.
  items:
  - голова == head
  - живіт == stomach
  - горло == throat
  - спина == back
  - рука == hand/arm
  - нога == leg/foot
  - зуб == tooth
  - око == eye
- type: fill-in
  focus: Complete the sentence with the correct symptom or body part.
  items:
  - У мене болить {голова|рука|нога}. Я хочу спати.
  - У мене болить {живіт|вухо|око}. Я не хочу їсти.
  - У мене болить {горло|спина|ніс} і є температура. Я не можу говорити.
  - У мене {кашель|нежить|зуб}, я постійно кашляю.
  - У мене болить {зуб|голова|нога}, мені потрібен стоматолог.
  - Я {хворий|лікар|аптека}. У мене болить голова і спина.
- type: quiz
  focus: Choose the logical response to the health problem.
  items:
  - question: У мене болить голова.
    options:
    - Ось таблетки від головного болю.
    - Ось краплі від нежиті.
    - Випийте сироп від кашлю.
  - question: У мене сильний кашель.
    options:
    - Вам потрібні таблетки від кашлю.
    - Ось краплі для носа.
    - У мене болить зуб.
  - question: Що у вас болить?
    options:
    - У мене болить горло.
    - Я лікар.
    - Де аптека?
  - question: Добрий день. Дайте, будь ласка, щось від нежиті.
    options:
    - Ось краплі, будь ласка.
    - У мене болить спина.
    - Це таблетки від головного болю.
- type: fill-in
  focus: At the pharmacy or doctor - using target chunks.
  items:
  - Дайте, {будь ласка|добрий день|дякую}, таблетки від головного болю.
  - Що у вас {болить|хворий|лікар}?
  - У мене {температура|аптека|лікар} і болить горло.
  - Мені {погано|хворий|добре}. Викличте лікаря!
  - Де тут найближча {аптека|голова|спина}? Мені потрібні ліки.
connects_to:
- a1-054 (Emergencies)
prerequisites:
- a1-052 (My Story)
grammar:
- У мене болить + body part (impersonal chunk — no grammar analysis)
- Body part gender for adjective agreement (recognition only)
- Я хворий/хвора (gender agreement in short adjectives)
register: розмовний
references:
- title: State Standard 2024, §3
  notes: 'Thematic area: health (здоров''я) — body parts, symptoms, doctor visits.'
- title: 'Grade 1-2 textbook: Частини тіла'
  notes: Body parts vocabulary with pictures.

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

### Batch 1 (голова → око)
- ✅ голова — noun (3 lemma entries)
- ✅ горло — noun (3 lemma entries)
- ✅ живіт — noun (2 lemma entries)
- ✅ рука — noun
- ✅ нога — noun
- ✅ болить — verb (lemma: боліти)
- ✅ лікар — noun
- ✅ аптека — noun
- ✅ спина — noun
- ✅ око — noun (3 lemma entries)

### Batch 2 (вухо → випишу) — also verified plan dialogue words
- ✅ вухо — noun (3 lemma entries)
- ✅ зуб — noun (2 lemma entries)
- ✅ ніс — noun (confirmed noun, not verb ніс < нести)
- ✅ температура — noun
- ✅ кашель — noun (2 lemma entries)
- ✅ нежить — noun — ⚠️ **GENDER ERROR IN PLAN**: VESUM confirms `noun:inanim:m` (MASCULINE), plan labels it feminine (f). Fix: нежить (m).
- ✅ таблетка — noun
- ✅ хворий — adj (5 forms across adj lemma)
- ✅ болять — verb (lemma: боліти) — plural form confirmed
- ✅ застуда — noun
- ✅ ліки — noun (3 entries)
- ✅ краплі — noun (6 entries, lemma: крапля)
- ✅ випишу — verb (lemma: виписати) ✅

**Confirmed**: ALL 18 plan vocabulary words verified ✅
**Not found**: none
**Action required**: Fix нежить gender tag in plan from `f` → `m`

---

## Textbook Excerpts

### Section: Тіло (The Body) — частини тіла
> "Обруч крутять навколо тіла, на **руці**, **нозі**. Обручі носять на **голові**."
> Source: Большакова, Grade 1 (Буквар 2018), p. 8 — body parts appear naturally in Grade 1 context with locative case

### Section: У мене болить... (symptoms + doctor)
> "Голов­ний **біль** – ознака недуги. Отже, при виникненні головного болю треба не займатися самолікуванням, а звертатися за порадою до **лікаря**."
> Source: Заболотний, Grade 10 (2018), p. 177 — confirms "головний біль" (masc.) and "звертатися до лікаря" as natural Ukrainian

### Section: У мене болить... (sickbed scene — температура, болить)
> "Після такої **температури** це навіть забагато зразу. [...] І **голова** крутиться від довгого лежання."
> Source: Авраменко, Grade 6 (Ukrainian Literature, 2023), p. 124 — authentic illness vocabulary in literary context

### Section: Dialogues — At the doctor's (лікар + хворий)
> "В очах пацієнта відчувалася тривога [...] Після кількох запитань й огляду **лікар** зазначив, що, імовірно, **біль** є симптомом загострення."
> Source: Заболотний, Grade 10 (2018), p. 19 — doctor-patient communication text; confirms лікар vocabulary register

---

## Grammar Rules

- **"У мене болить" construction** (dative possessive): Plan correctly notes this is dative (A2+ analysis) and instructs teaching it as a CHUNK at A1. ✅ No Правопис rule needed — chunk approach is pedagogically sound.
- **біль is MASCULINE**: Антоненко-Давидович §ІМЕННИКИ confirms "іменник біль в українській мові – чоловічого роду" (contrast Russian feminine "боль"). Plan's use of "від головного болю" (genitive masculine) is grammatically correct ✅.
- **Правопис query** on dative case returned §15 (Д→ДЖ alternation) — dative case rules are not a Правопис 2019 concern (spelling-only document); grammar is covered by the Ukrainian grammar reference, not Правопис.

---

## Calque Warnings

- **"ліки від [хвороби]"** — ⚠️ **CALQUE** (Russicism). Антоненко-Давидович (§ПРИЙМЕННИКИ) explicitly: *"Це ліки від усяких хвороб" — так сказати по-українську не можна. Треба: "ліки **проти** ревматизму."*
  - Plan dialogue: "Від головного болю? — Так. І від кашлю, будь ласка." and "А є щось від нежиті?"
  - **Correct form**: таблетки **проти** головного болю / краплі **проти** нежиті / щось **проти** кашлю
  - **Action**: Replace all `від [symptom]` in pharmacy dialogue with `проти [symptom]`
  - Note: "головний біль" standalone phrase ✅ is correct; only the preposition + ліки combination triggers the calque rule.

- **"випишу ліки"** — ✅ OK. Виписати ліки / рецепт is natural Ukrainian. No calque issue found.

- **"від головного болю" (standalone genitive phrase without ліки)** — ✅ OK as standalone phrase / label (e.g., section heading or category label without ліки).

---

## CEFR Check

| Word | PULS Level | Status |
|------|-----------|--------|
| голова | A1 | ✅ On target |
| лікар | A1 | ✅ On target |
| аптека | A1 | ✅ On target |
| температура | A1 | ✅ On target |
| хворий (adj) | A1 | ✅ On target |
| таблетка | **A2** | ⚠️ One level above A1 — acceptable as situational health vocab, flag in plan |
| кашель | **A2** | ⚠️ One level above A1 — acceptable as situational health vocab |
| нежить | **A2** | ⚠️ One level above A1 — acceptable as situational health vocab |

**Note on A2 words at A1**: таблетка, кашель, нежить are PULS A2 but situationally essential for a health module. Ukrainian textbooks (Grade 1-2) regularly introduce situational vocabulary above the learner's current level when the context demands it. These are appropriate to include — but the plan should note they are "productive A1 situational vocabulary" or taught as chunks.
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
# Verified Knowledge Packet: Health
**Module:** health | **Phase:** A1.8 [Past, Future, Graduation]
**Textbook grades searched:** 5, 6, 7

---

## Dialogues

> **Source:** avramenko, Grade 6
> **Section:** Сторінка 123
> **Score:** 0.50
>
> Послухавши пульс, вона підняла мені сорочку, схилилась і приклала 
> маленьке холодне вухо до моїх грудей. Вона завжди вислу­ховувала хво-
> рих просто так, вухом, без усякого лікарського причан­далля. І тільки вислухавши мене, вона сказала весело:
> — Молодець! Усе гаразд! Скоро будеш здоровий. І ляснула мене долонею по пузі. — Еге! Гаразд! — буркнув я. — Оно вже і їсти не можу. Організм не прий­
> має. І голова крутиться, підвестися несила. — Що? — вона здивовано глянула на тарілки, що стояли на стіль­ці. — 
> А це хто снідав? — Та я ж... бачите... — зітхнув я.

## Тіло (The Body)

> **Source:** avramenko, Grade 7
> **Section:** Сторінка 129
> **Score:** 0.50
>
> Ух! Очі мої лізуть на лоба: я відчуваю, як жабеня, пірнувши в живіт, 
> починає веселий свій танок десь аж біля пупа (...).

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 105
> **Score:** 0.50
>
> 105
> Фонетика. Графіка. Орфоепія. Орфографія. Фонетика . Звуки мовлення
> Вправа 152
> Назвіть три органи з перелічених, не  задіяні у  вимові звуків .
> Язик, зуби, нога, губи, права рука, нижня щелепа, підне-
> біння, очі.
> Вправа 153
> 1. Прочитайте уривок вірша Оксани Лущевської .
> Я — МОВ ЗАЙЧИК
> Я — мов зайчик: ніс рожевий, великі вуха,
> довкола принюхуюся і прислухаюся,
> а серце теленькає-теленькає:
> я всього боюся.
> Вітер дмухне: «Хоч би не ураган…»
> Дощ накрапає: «Аби не злива…»
> Звідкись грюкне: «Лише б не грім і блискавка…»
> Чи то даремно лякаюсь?
> Я — мов зайчик. Зашипить: «Хоч би не зміюка…»
> Гаркне: «Аби не пес…», крикне: «Лише б не крук…»
> Загарчить: «Тільки б не вовцюган…»
> Полохлива — не віриться!
> 2. Прочитайте текст ще раз, замінивши підкреслені фрази звуками природи .
> Вправа 154
> 1.

## У мене болить... (It Hurts...)

> **Source:** avramenko, Grade 6
> **Section:** Сторінка 123
> **Score:** 0.50
>
> Послухавши пульс, вона підняла мені сорочку, схилилась і приклала 
> маленьке холодне вухо до моїх грудей. Вона завжди вислу­ховувала хво-
> рих просто так, вухом, без усякого лікарського причан­далля. І тільки вислухавши мене, вона сказала весело:
> — Молодець! Усе гаразд! Скоро будеш здоровий. І ляснула мене долонею по пузі. — Еге! Гаразд! — буркнув я. — Оно вже і їсти не можу. Організм не прий­
> має. І голова крутиться, підвестися несила. — Що? — вона здивовано глянула на тарілки, що стояли на стіль­ці. — 
> А це хто снідав? — Та я ж... бачите... — зітхнув я.

> **Source:** avramenko, Grade 7
> **Section:** Сторінка 129
> **Score:** 0.33
>
> Ух! Очі мої лізуть на лоба: я відчуваю, як жабеня, пірнувши в живіт, 
> починає веселий свій танок десь аж біля пупа (...).

> **Source:** zabolotnyi, Grade 6
> **Section:** Сторінка 89
> **Score:** 0.33
>
> 89
> Iменник
> І. Запишіть словосполучення, добираючи правильне закінчення.
> Головн(ий/а) біль, нов(ий/а) шампунь, нелегк(ий/а) путь,
> вищ(ий/а) ступінь, вітальн(ий/а) туш, яскрав(ий/а) гуаш,
> сильн(ий/а) нежить, біл(ий/а) тюль, гірк(ий/а) полин, бара-
> бан н(ий/а) дріб, нов(ий/а) рукопис, друг(ий/а) степінь,
> яскрав(ий/а) емаль, висок(ий/а) насип.
> ІІ. Складіть усно речення з одним поданим словосполученням.
> СИТУАЦІЯ. Уявіть, що вам треба викликати 
> лікаря для знайомого, який застудився. Ви теле-
> фонуєте до лікарні.
> Складіть усно 2–3 речення, щоб звернутися до 
> працівника лікарні в цій ситуації. Використайте 
> подані словосполучення.
> головний біль
> сильний нежить
> висока температура
> І. Спишіть речення, розставляючи пропущені розділові знаки. Надпи-
> шіть скорочено над іменниками їхній рід.

## Summary

> **Source:** avramenko, Grade 7
> **Section:** Сторінка 129
> **Score:** 0.50
>
> Ух! Очі мої лізуть на лоба: я відчуваю, як жабеня, пірнувши в живіт, 
> починає веселий свій танок десь аж біля пупа (...).

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 105
> **Score:** 0.50
>
> 105
> Фонетика. Графіка. Орфоепія. Орфографія. Фонетика . Звуки мовлення
> Вправа 152
> Назвіть три органи з перелічених, не  задіяні у  вимові звуків .
> Язик, зуби, нога, губи, права рука, нижня щелепа, підне-
> біння, очі.
> Вправа 153
> 1. Прочитайте уривок вірша Оксани Лущевської .
> Я — МОВ ЗАЙЧИК
> Я — мов зайчик: ніс рожевий, великі вуха,
> довкола принюхуюся і прислухаюся,
> а серце теленькає-теленькає:
> я всього боюся.
> Вітер дмухне: «Хоч би не ураган…»
> Дощ накрапає: «Аби не злива…»
> Звідкись грюкне: «Лише б не грім і блискавка…»
> Чи то даремно лякаюсь?
> Я — мов зайчик. Зашипить: «Хоч би не зміюка…»
> Гаркне: «Аби не пес…», крикне: «Лише б не крук…»
> Загарчить: «Тільки б не вовцюган…»
> Полохлива — не віриться!
> 2. Прочитайте текст ще раз, замінивши підкреслені фрази звуками природи .
> Вправа 154
> 1.

## Grammar Reference

> **Source:** avramenko, Grade 6
> **Section:** Сторінка 123
> **Score:** 0.50
>
> Послухавши пульс, вона підняла мені сорочку, схилилась і приклала 
> маленьке холодне вухо до моїх грудей. Вона завжди вислу­ховувала хво-
> рих просто так, вухом, без усякого лікарського причан­далля. І тільки вислухавши мене, вона сказала весело:
> — Молодець! Усе гаразд! Скоро будеш здоровий. І ляснула мене долонею по пузі. — Еге! Гаразд! — буркнув я. — Оно вже і їсти не можу. Організм не прий­
> має. І голова крутиться, підвестися несила. — Що? — вона здивовано глянула на тарілки, що стояли на стіль­ці. — 
> А це хто снідав? — Та я ж... бачите... — зітхнув я.

> **Source:** zabolotnyi, Grade 6
> **Section:** Сторінка 161
> **Score:** 0.33
>
> 161
> ЗАХОПЛИВИЙ СВІТ ПРИГОДНИЦЬКИХ І ФАНТАСТИЧНИХ ПОВІСТЕЙ 
> Грюкнувши дверима, вона зайшла в хату й швидким кро-
> ком наблизилася до мого ліжка.
> Поклала руку мені на лоба, потім узяла за пульс. І все це, 
> не кажучи ні слова, мовчки, зосереджено, строго. Я завмер 
> у безнадійному чеканні.
> Скінчивши слухати пульс, вона підняла мені сорочку, 
> схилилась і приклала маленьке холодне вухо до моїх гру-
> дей. Вона завжди вислуховувала хворих просто так, вухом, 
> без усякого лікарського причандалля.
> І тільки вислухавши мене, вона сказала нарешті весело:
> – Молодець, козаче! Усе гаразд! Скоро будеш здоровий.
> І ляснула мене долонею по пузі.
> – Еге! Гаразд! – буркнув я. – Оно вже і їсти не можу. Орга-
> нізм не приймає.


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
- Після **м’яких** приголосних у **середині складу** перед о: *чотирьох, дзьоб, сьомий, льодяний, відьом*.

### Речення, його граматична основа
> **Source:** МійКлас — [Речення, його граматична основа](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/vidomosti-z-sintaksisu-i-punktuatciyi-14562/rechennia-iogo-gramatichna-osnova-pidmet-i-prisudok-39372)

### Теорія:

*www.ua.pistacja.tv*  
Речення
Реченням називаємо одне або кілька слів, що виражають закінчену думку.
Саме за допомогою речень ми спілкуємось, висловлюємо прохання, наказ, виражаємо емоції, повідомляємо інформацію.
Приклад:
- Весна іде, красу несе \(Нар. творчість\). 
- Ліс. Тиша. Благодать. 
Слова в реченні зв'язані між собою **за змістом** і **граматично**. **Граматичний зв'язок** — це поєднання за допомогою **закінчень** і **службових слів**. На початок і кінець речення вказує **інтонація**. Між реченнями робимо **паузи**.
Ознаки речення
1. Речення відображає дійсність. Інформаці

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Dialogues` (~300 words)
- `## Тіло (The Body)` (~300 words)
- `## У мене болить... (It Hurts...)` (~300 words)
- `## Summary` (~300 words)

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
  1. **At the doctor's office — describing symptoms: У мене болить голова (f, head). Болить горло (n, throat). Болить живіт (m, stomach). Нежить (m, runny nose). Кашель (m, cough). Температура (f, fever).**
     Speakers: Пацієнт, Лікар
     Why: Body parts: голова(f), горло(n), живіт(m), температура(f)

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

**Required:** голова (head, f), горло (throat, n), живіт (stomach, m), рука (hand/arm, f), нога (leg/foot, f), {'болить (hurts — chunk': 'у мене болить)'}, лікар (doctor, m), аптека (pharmacy, f)
**Recommended:** спина (back, f), око (eye, n), вухо (ear, n), зуб (tooth, m), ніс (nose, m), температура (fever/temperature, f), кашель (cough, m), нежить (runny nose, f), таблетка (pill, f), хворий (sick, adj)

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
- P1 (~35 words): Scene-setter — two situations every learner will face in Ukraine: a visit to the лікар and a stop at the аптека. Both dialogues use vocabulary introduced in this module; read them now for the full picture, then study the pieces.
- Dialogue 1 (~115 words): At the doctor's office — 8-turn exchange. Лікар opens: «Що у вас болить?» Пацієнт: «У мене болить голова і горло.» Лікар: «Давно?» Пацієнт: «З учора. І в мене температура.» Лікар: «Ви кашляєте?» Пацієнт: «Так, трохи. І в мене нежить.» Лікар: «Зрозуміло. Це застуда. Я випишу ліки. Відпочивайте!» Пацієнт: «Дякую, лікарю!» — establishes key question «Що у вас болить?» and the three-symptom stack (болить голова/горло + температура + нежить + кашель).
- P2 (~30 words): Callout box — two phrases to memorise from Dialogue 1: «Що у вас болить?» (What hurts you? — doctor's standard opening) and «З учора» (Since yesterday — useful time anchor at A1).
- Dialogue 2 (~115 words): At the pharmacy — 7-turn exchange. Покупець: «Добрий день! У мене болить голова. Дайте, будь ласка, таблетки.» Фармацевт: «Від головного болю?» Покупець: «Так. І від кашлю, будь ласка.» Фармацевт: «Ось, будь ласка. Ще щось?» Покупець: «А є щось від нежиті?» Фармацевт: «Так, ось краплі.» Покупець: «Дякую! Скільки це коштує?» — introduces the pharmacy formula «Дайте, будь ласка, [ліки] від [symptom]» and shows три genitive chunks: від головного болю, від кашлю, від нежиті (treat as frozen phrases, no grammar analysis).
- P3 (~35 words): Brief closing note — notice how both dialogues stay simple: one phrase to describe the problem (У мене болить…), one formula to ask for help (Дайте будь ласка…). That is the complete A1 toolkit.
- Exercise: **quiz** — «Choose the logical response» (4 items from activity_hints: У мене болить голова / У мене сильний кашель / Що у вас болить? / Дайте щось від нежиті). Tests comprehension of the two dialogues just read; only concepts already introduced above.

---

## Тіло (The Body) (~330 words total)
- P1 (~130 words): Core body-part inventory — introduce 10 words with gender label and brief real-world note. Present in a short enumerated list: голова (f) — head; горло (n) — throat; спина (f) — back; живіт (m) — stomach; рука (f) — hand/arm; нога (f) — leg/foot; око (n) — eye; вухо (n) — ear; зуб (m) — tooth; ніс (m) — nose. Scope note for рука and нога: Ukrainian has one word where English has two — рука covers everything from shoulder to fingertip; нога covers hip to toe. These are the ten most useful for an A1 learner at a clinic; this is not a complete anatomy list.
- P2 (~100 words): Gender in practice — at A1 you will mainly use these words after болить, but gender matters when you add an adjective (review from M09). Three contrast examples: велике о́ко (neuter -е), вели́кий ніс (masculine -ий), вели́ка рука́ (feminine -а). One more: боля́чий зуб (masculine), хво́ре го́рло (neuter). The takeaway: learn each body part with its gender tag now so adjective agreement is automatic later.
- P3 (~100 words): Connecting body parts to the coming chunk — every word on the list above slots straight into the pattern you will learn next: У мене болить + [body part]. Walk through three quick examples to preview: У мене болить голова. / У мене болить живіт. / У мене болить спина. The body-part list is the input; the chunk is the output. Memorise the list now, and the next section gives you the grammar-free way to use it immediately.
- Exercise: **match-up** — 8 pairs: голова ↔ head, живіт ↔ stomach, горло ↔ throat, спина ↔ back, рука ↔ hand/arm, нога ↔ leg/foot, зуб ↔ tooth, око ↔ eye. Tests the body-part vocabulary just taught.

---

## У мене болить... (It Hurts...) (~330 words total)
- P1 (~120 words): The magic chunk — «У мене болить» is the single most useful health phrase in Ukrainian. Literally it means «at me hurts», but learn it as an unanalysed block, the same way a child does. You do not need to know it uses the dative case (that is A2 grammar). Just attach any body part from the previous section: У мене болить голова. (I have a headache.) У мене болить живіт. (My stomach hurts.) У мене болить горло. (My throat hurts.) У мене болить спина. (My back hurts.) У мене болить зуб. (I have a toothache.) Five sentences, five body parts — that covers most clinic visits. Stress: у мене́ боли́ть.
- P2 (~130 words): Beyond болить — five more symptom chunks you need. These also follow the «У мене + noun» pattern: У мене температура. (I have a fever.) У мене кашель. (I have a cough.) У мене нежить. (I have a runny nose — нежить is feminine despite looking masculine.) Two Мені phrases for general state: Мені холодно. (I'm cold / I feel cold.) Мені погано. (I feel bad / I'm not well.) And the direct statement: Я хворий. (I'm sick. — masculine) / Я хвора. (I'm sick. — feminine). Gender agreement here works exactly like M09 adjectives: male speaker says хворий, female speaker says хвора. Quick note: when multiple teeth hurt, the verb changes — У мене болять зуби. (болять = plural form of болить.) Just recognise this form; do not memorise it yet.
- P3 (~80 words): Combining symptoms — real conversations stack symptoms. Two models from the doctor's dialogue: «У мене болить голова і горло» (head and throat, both with болить). «У мене нежить і кашель» (two noun symptoms, no verb needed). Try building: «Я хвора. У мене болить горло і є температура.» This is full A1 communication — no grammar analysis required, only chunk combination.
- Exercise: **fill-in** — «Complete with the correct body part or symptom» (6 items from activity_hints): У мене болить ___ . Я хочу спати. / У мене болить ___ . Я не хочу їсти. / У мене болить ___ і є температура. / У мене ___, я постійно кашляю. / У мене болить ___, мені потрібен стоматолог. / Я ___. У мене болить голова і спина. Tests only vocabulary from this section and the Тіло section above.

---

## Summary (~330 words total)
- P1 (~120 words): Health toolkit recap — prose paragraph pulling together everything from the module. Three registers: talking about your body (голова, горло, живіт, спина, рука, нога, oko, вухо, зуб, ніс), describing what hurts (У мене болить [body part]), describing your general state (Я хворий/хвора, Мені погано, Мені холодно). Two situation-specific formulas: at the doctor — answer «Що у вас болить?» with «У мене болить…»; at the pharmacy — ask «Дайте, будь ласка, таблетки від головного болю / від кашлю / від нежиті». Treat the від-phrases as fixed chunks for now.
- Self-check Q&A list (~120 words): Bulleted prompt-and-answer pairs:
  - Як сказати «My throat hurts and I have a fever»? → У мене болить горло і є температура.
  - Як сказати «I'm sick» (you are female)? → Я хвора.
  - Що означає «Мені погано»? → I feel bad / I'm not well.
  - Як попросити таблетки від кашлю в аптеці? → Дайте, будь ласка, таблетки від кашлю.
  - Як лікар питає про симптоми? → Що у вас болить?
  - Яка різниця між «болить» і «болять»? → болить = one thing hurts (зуб, голова); болять = several things hurt (зуби, очі).
- P2 (~90 words): Looking ahead — M54 (Emergencies) builds directly on this module. You will use «Мені погано» and «У мене болить» in urgent situations and add phrases like «Викличте швидку!» (Call an ambulance!). Everything in this module travels forward intact: the chunk У мене болить…, the symptom nouns, Я хворий/хвора. Health vocabulary you learn now is vocabulary you keep forever.
- Exercise: **fill-in** — «At the pharmacy or doctor» (5 items from activity_hints): Дайте, ___ , таблетки від головного болю. / Що у вас ___? / У мене ___ і болить горло. / Мені ___. Викличте лікаря! / Де тут найближча ___? Мені потрібні ліки. Tests pharmacy/doctor formula chunks introduced across the full module.

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
