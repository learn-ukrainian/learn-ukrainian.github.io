

---

## Your Writing Identity

**You are: Patient & Supportive Ukrainian Tutor.** Your persona is *The Helpful Teacher*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **54: Emergencies** (A1, A1.8 [Past, Future, Graduation]).

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
module: a1-054
level: A1
sequence: 54
slug: emergencies
version: '1.2'
title: Emergencies
subtitle: Допоможіть! Викличте швидку! — survival Ukrainian
focus: communicative
pedagogy: PPP
phase: A1.8 [Past, Future, Graduation]
word_target: 1200
objectives:
- Call for help using key emergency phrases (Допоможіть! Викличте...)
- Call 112 and explain a basic emergency in Ukrainian
- Ask for help at a pharmacy, hospital, or police station
- Give basic personal information in an emergency (name, address, phone)
dialogue_situations:
- setting: 'A minor car accident on вулиця Хрещатик (f) — calling 103: Допоможіть!
    Аварія (f, accident) на Хрещатику! Потрібна швидка (f, ambulance)! Є постраждалий
    (m, injured person). Машина (f, car) пошкоджена.'
  speakers:
  - Водій (driver)
  - Оператор 103
  motivation: Emergency with аварія(f), швидка(f), машина(f), вулиця(f)
content_outline:
- section: Dialogues
  words: 300
  points:
  - 'Dialogue 1 — Calling 112: — Служба порятунку, слухаю вас. — Допоможіть! Тут аварія!
    Людина не рухається! — Де ви? — На вулиці Хрещатик, біля метро Майдан Незалежності.
    — Зрозуміло. Швидка вже їде. Як вас звати? — Мене звати Адам. Мій номер — нуль
    дев''яносто три... — Дякую. Залишайтеся на місці. Emergency call: location + problem
    + personal info.'
  - 'Dialogue 2 — Lost documents: — Вибачте, де тут поліція? — Поліція? Прямо і наліво.
    — Дякую! (at the station) Добрий день. Я загубив паспорт. — Де ви його загубили?
    — Я не знаю. Може, в метро. — Як ваше прізвище? — Сміт. Адам Сміт. — Ваш номер
    телефону? — Нуль дев''яносто три, п''ятсот двадцять один... — Добре. Заповніть
    цю форму, будь ласка. Police station: reporting a lost document.'
- section: Екстрені ситуації (Emergencies)
  words: 300
  points:
  - 'Emergency number: 112 (один один два) — works everywhere in Ukraine. Key phrases
    (learn as chunks!): Допоможіть! (Help! — formal/plural imperative) Викличте швидку!
    (Call an ambulance!) Викличте поліцію! (Call the police!) Тут аварія! (There''s
    an accident here!) Тут пожежа! (There''s a fire here!) Людині погано! (Someone
    is feeling bad!) Мені потрібна допомога! (I need help!)'
  - 'Giving your location: Де ви? — Where are you? Я на вулиці... (I''m on ... street.)
    Я біля... (I''m near...) Я в метро... (I''m in the metro...) Адреса: вулиця Хрещатик,
    будинок десять. (Address: Khreshchatyk street, building 10.) Use places vocabulary
    from A1.5 (біля, навпроти, поруч).'
- section: Допомога (Getting Help)
  words: 300
  points:
  - 'At the hospital / лікарня: Мені потрібен лікар. (I need a doctor.) У мене болить...
    (My ... hurts — from M53.) У мене алергія на... (I''m allergic to...) Я не розумію.
    Повторіть, будь ласка. (I don''t understand. Please repeat.) Ви говорите англійською?
    (Do you speak English?)'
  - 'Personal information for emergencies: Мене звати... (My name is...) Моє прізвище...
    (My surname is...) Мій номер телефону... (My phone number is...) Я з [country].
    (I''m from [country].) Мій паспорт... / Я загубив/загубила паспорт. (My passport...
    / I lost my passport.) Мій готель — ... (My hotel is...) All review from previous
    modules — applied to a critical situation.'
- section: Summary
  words: 300
  points:
  - 'Emergency survival kit: 112 — universal emergency number. Допоможіть! (Help!)
    Викличте швидку / поліцію! Тут аварія / пожежа! Location: Я на вулиці... Я біля...
    At hospital: У мене болить... Мені потрібен лікар. At police: Я загубив/загубила
    [document]. Personal info: ім''я, прізвище, номер телефону, країна, адреса. Self-check:
    Practice a 112 call — state the problem, give your location, give your name.'
vocabulary_hints:
  required:
  - допомога (help, f)
  - допоможіть (help! — imperative)
  - швидка (ambulance, f — short for швидка допомога)
  - поліція (police, f)
  - лікарня (hospital, f)
  - аварія (accident, f)
  - загубити (to lose)
  - викликати (to call/summon)
  recommended:
  - пожежа (fire, f)
  - порятунок (rescue, m)
  - паспорт (passport, m)
  - адреса (address, f)
  - номер (number, m)
  - алергія (allergy, f)
  - форма (form/document, f)
  - будинок (building, m)
activity_hints:
- type: quiz
  focus: Choose the correct emergency phrase for the situation.
  items:
  - question: You see a car crash.
    options:
    - Тут аварія! Викличте швидку!
    - Тут пожежа! Допоможіть!
    - Я загубив паспорт.
  - question: You see a building on fire.
    options:
    - Тут пожежа! Допоможіть!
    - Тут аварія!
    - Мені потрібен лікар.
  - question: Someone is feeling very ill on the street.
    options:
    - Людині погано! Викличте швидку!
    - Викличте поліцію!
    - Я загубив паспорт.
  - question: You cannot find your passport at the airport.
    options:
    - Я загубив паспорт.
    - Тут аварія!
    - Мені потрібна швидка.
  - question: Someone stole your wallet.
    options:
    - Викличте поліцію! Допоможіть!
    - Тут пожежа!
    - Мені потрібен лікар.
- type: fill-in
  focus: Complete the emergency phone call.
  items:
  - Алло! {Допоможіть|Дякую|Вибачте}! Тут аварія!
  - '{Викличте|Загубив|Потрібен} швидку допомогу!'
  - Я на {вулиці|лікарні|поліції} Хрещатик, біля метро.
  - Мене {звати|прізвище|адреса} Адам.
  - Мій номер {телефону|паспорта|будинку} — нуль дев'яносто три...
  - Мені потрібна {допомога|пожежа|аварія}!
- type: order
  focus: Put the dialogue with the 112 operator in the correct order.
  items:
  - — Служба порятунку, слухаю вас.
  - — Допоможіть! Тут пожежа!
  - — Де ви?
  - — На вулиці Шевченка, будинок п'ять.
  - — Зрозуміло. Швидка і пожежники вже їдуть. Як вас звати?
  - — Мене звати Анна. Дякую!
- type: fill-in
  focus: Reporting an issue at the police station or hospital.
  items:
  - Добрий день. Я {загубив|викличте|допоможіть} паспорт.
  - Моє {прізвище|ім'я|номер} — Сміт.
  - Мені {потрібен|погана|хворий} лікар.
  - У мене {алергія|пожежа|аварія} на ці таблетки.
  - Я не розумію. {Повторіть|Допоможіть|Викличте}, будь ласка.
connects_to:
- a1-055 (A1 Finale)
prerequisites:
- a1-053 (Health)
grammar:
- 'Emergency imperatives: Допоможіть! Викличте! Повторіть! (review from M43)'
- 'Location phrases: на вулиці, біля, в метро (review from A1.5)'
- Мені потрібен/потрібна (I need — chunk, no grammar analysis)
register: розмовний
references:
- title: State Standard 2024, §3
  notes: 'Thematic area: health and safety — emergency situations.'

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

**Confirmed (16/16):**
- ✅ допомога — noun (VESUM confirmed)
- ✅ допоможіть — verb form of допомогти (VESUM confirmed)
- ✅ швидка — noun (VESUM confirmed as standalone noun — not just adjective form; 4 matches including as noun)
- ✅ поліція — noun (VESUM confirmed)
- ✅ лікарня — noun (VESUM confirmed)
- ✅ аварія — noun (VESUM confirmed)
- ✅ загубити — verb (VESUM confirmed)
- ✅ викликати — verb (VESUM confirmed, 2 matches)
- ✅ пожежа — noun (VESUM confirmed)
- ✅ порятунок — noun (VESUM confirmed, 2 matches)
- ✅ паспорт — noun (VESUM confirmed, 2 matches)
- ✅ адреса — noun (VESUM confirmed)
- ✅ номер — noun (VESUM confirmed, 2 matches)
- ✅ алергія — noun (VESUM confirmed)
- ✅ форма — noun (VESUM confirmed)
- ✅ будинок — noun (VESUM confirmed, 2 matches)

**Not found:** none — all 16 plan vocabulary words are safe to use.

---

## Textbook Excerpts

### Section: Екстрені ситуації (Emergencies)
> «Якщо неможливо залишити приміщення, а у вас є мобільний зв'язок, зателефонуйте за номером 101. [...] Під час пожежі виходьте з класу через двері й допоможіть іншим.»
> Source: Авраменко, Grade 7 (2024, tier 1) — §36 "Порядок дій у надзвичайних ситуаціях"

> Note: Textbook uses **101** (fire service). The plan correctly uses **112** (universal emergency number, valid since 2016). Both are real numbers; 112 is the correct one for the module's scope.

### Section: Dialogues — Calling 112 / Lost documents
> «Після досягнення 14-річного віку ви отримаєте паспорт громадянина / громадянки України у формі картки, на якій теж буде вказано вашу адресу.»
> Source: Авраменко, Grade 7 (2024, tier 1) — Розвиток мовлення, "Заповніть бланк за зразком"

> Also: «Статистику ДТП в Україні опублікувала Патрульна поліція. Причиною більшості аварій...»
> Source: Заболотний, Grade 7 (2024, tier 1) — ДТП context, confirms аварія used in accident/road context.

### Section: Допомога (Getting Help) — Hospital / Medical
> «— У неї, здається, алергія — бачиш, як вушка почервоніли... Алергія — схильність організму до захворювань шкіри внаслідок уживання в їжу деяких продуктів.»
> Source: Вашуленко, Grade 2 (2019, tier 2) — confirms алергія at A1 level with natural Ukrainian usage.

> «Спостереження показують, що спілкування з пацієнтом у 70–80 % випадків допомагає поставити правильний діагноз [...] Ніколи не можна говорити, що ви більше нічого не можете зробити»
> Source: Заболотний, Grade 10 (2018) — лікар/пацієнт communication context.

### Section: Imperative (наказовий спосіб) — for grammar frame in activities
> «За допомогою форм наказового способу дієслів спонукають до дії: просять, наказують, благають, примушують [...] 2-а ос. однини: -∅, -и: ріж, роби. 2-а ос. множини: -те, -іть або -іте: ріжте, робіть.»
> Source: Авраменко, Grade 11 (2019, tier 2) — §17 full imperative paradigm table.

> «У дієсловах наказового способу пишемо м'який знак у кінці слова та складу після д, т, з, с, ц, л, н: лізь, лізьте, будь, будьте, глянь, гляньте, занось, заносьте.»
> Source: Авраменко, Grade 7 (2024, tier 1) — §37

> «Для творення форм наказового способу не використовуємо частки давай, давайте: читаймо (не давай читати).»
> Source: Заболотний, Grade 7 (2024, tier 1) — confirmed in both Zabolotnyi and Avramenko Grade 7.

---

## Grammar Rules

- **Imperative 2nd pl. ending**: Both **-іть** and **-іте** are normative (e.g., допоможіть / допоможіте, залишайтеся). Source: Авраменко Grade 11 §17 — "У формі 2-ї особи множини паралельно із закінченням -іть можна вживати й закінчення -іте (воно хоч і рідше вживане, але нормативне)."
- **Imperative + м'який знак**: Write ь at end of word and syllable after д, т, з, с, ц, л, н in imperative forms. Source: Авраменко Grade 7 §37.
- **Imperative — NEVER "давай/давайте"**: Using "давай + infinitive" to form imperative is NOT literary norm. Confirmed by Заболотний Grade 7 and Авраменко Grade 7 — both explicitly mark it as **НЕправильно**.
- **Правопис 2019 query**: The RAG index did not return a direct Правопис section number for наказовий спосіб or м'який знак — these rules are confirmed via textbooks only.

---

## Calque Warnings

- **"залишайтеся на місці"**: Антоненко-Давидович flags overuse of **залишати** vs. **покидати** (they are not synonyms — залишати ≠ покидати semantically). However, "залишайтеся на місці" is standard Ukrainian in official emergency/administrative register (police dispatchers, emergency services). The imperfective form (залишайтеся = keep staying) is correct here vs. perfective залишіться. ✅ **OK** — acceptable in emergency register.

- **"заповніть цю форму"**: No calque flag found. The style guide returned unrelated entries. "Заповнити форму / бланк" is confirmed in Авраменко Grade 7 ("Заповніть бланк за зразком") — textbook-attested, natural Ukrainian. ✅ **OK.**

- **"викликати швидку / поліцію"**: No flag found. Антоненко-Давидович returned unrelated entries (трапитися, повинна). "Викликати" in the sense of "to call/summon" a service is standard Ukrainian. VESUM confirmed. ✅ **OK.**

---

## CEFR Check

- допомога: **A1** ✅ — on target
- допоможіть: **A1** (listed as вигук in PULS) ✅ — on target
- лікарня: **A1** ✅ — on target
- паспорт: **A1** ✅ — on target
- алергія: **A1** ✅ — on target
- адреса: **A1** ✅ — on target
- поліція: **not found directly** — closest match поліцейський = A2. ⚠️ **Likely A2** — acceptable in A1.8 graduation module (context-critical survival word; taught as chunk)
- пожежа: **A2** ⚠️ — one level above target. Acceptable in A1.8 (graduation module) as a high-frequency emergency chunk "Тут пожежа!"; taught as formula, not analyzed morphologically
- аварія: **B1** ⚠️⚠️ — **TWO levels above A1 target.** This is the most significant finding. Recommend flagging for writer: аварія should be introduced as a **passive recognition word** (learner hears it, understands it, uses it only in the fixed chunk "Тут аварія!"). Do NOT require active productive use beyond the emergency phrase. The plan already uses it only in a fixed dialogue chunk — this is pedagogically sound.
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
# Verified Knowledge Packet: Emergencies
**Module:** emergencies | **Phase:** A1.8 [Past, Future, Graduation]
**Textbook grades searched:** 5, 6, 7

---

## Dialogues

> **Source:** avramenko, Grade 6
> **Section:** Сторінка 120
> **Score:** 0.25
>
> 120
> ЖИВИЛЬНІ  ДЖЕРЕЛА  МУДРИХ  КНИЖОК
> — Тю, — ледве сказав Ява.
> — Тьху, — ледве сказав я. 
> Це вся розмова, на яку ми спро­моглися.
> І тільки за хвилин двадцять ми нарешті отямились і змогли обміняти-
> ся думками з приводу того, що сталося.
> — Так ... — зітхнув Ява. — Можна сказати, зіпсував ти мені кар’єру. 
> А що?! Хто ж мене тепер у міліцію візьме...
>  
> 1.	 Хрещатик «утикається» на Європейській площі в
> А	 метро «Арсенальна»
> Б	 метро «Хрещатик»
> В	   колишній костел
> Г	   філармонію
> 2.	 	Репліка «Лізь, голубе, під землю, як усі люди» адресована
> А	 інтелігентному дідусеві 
> Б	 опасистому дядьку
> В  	міліціонерові
> Г  	 інтуристу
> 3.	 Установіть відповідність.
> Ге­рой по­віс­ті
> Опис зов­ніш­нос­ті 
> 1	 мі­лі­ці­о­нер
> 2	 дядь­ко  в мет­ро
> 3	 ін­ту­рист	
> А	 «...

> **Source:** litvinova, Grade 5
> **Section:** Сторінка 248
> **Score:** 0.50
>
> 248
> Відомості із синтаксису й пунктуації.  Пряма мова.  Розділові знаки в реченнях
> В трамваї хтось гаркнув бабусі на  вухо: 
> Ану, відступися убік, розвалюхо! 
> Не встигла убік відступити небога — 
> Забрала стареньку «швидка допомога». 
> Буфетнику Про шу в  дитячім кафе 
> Хтось замість подяки та  вигукнув: 
> Пфе! 
> Буфетник облишив буфет і  торти — 
> Його до  сьогодні не  можуть знайти! 
> А далі, як мовиться в  казці, 
> Заби ли триво гу будьласці. 
> Вони невідомих осіб 
> Ловили шістнадцять діб! 
> А потім не  місяць, не  два 
> Учили казати слова: 
> «пробачте»,   
> «спасибі»,   
> «будь ласка»… 
> На цьому й  скінчилася  б казка, 
> Та вчора я  стріла особу одну. 
> Вона продавцеві сказала: 
> Ану… 
> Одразу мені пригадалася казка 
> Про два королівства: Ану і  Будьласка.

## Екстрені ситуації (Emergencies)

> **Source:** zabolotnyi, Grade 6
> **Section:** Сторінка 228
> **Score:** 0.33
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

## Допомога (Getting Help)

> **Source:** zabolotnyi, Grade 6
> **Section:** Сторінка 89
> **Score:** 0.50
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

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 42
> **Score:** 0.25
>
> 39
> 1. Мама робила в лікарні й пишалася своєю роботою. 
> 2.  Сніжна заметіль замела все навколо. 3. Помітивши за 
> вікном друга, хлопець непомітно вислизнув з хати. 4. У по-
> відомленні повідомлялося про новий кінофільм. 5. Учителі 
> та школярі провели флешмоб на шкільному подвір’ї.
> 86.	 Знайдіть для кожного слова місце в реченні й запишіть. Ви може-
> те використати кожне слово лише один раз. Ви можете скористатися 
> таблицею «Культура мовлення» на с. 40. 
> відкрити / відчинити / розплющити / розгорнути
> 1. Прошу ... ваші зошити. 2. Уранці мені не хотілося на-
> віть ... очі. 3. Спеціальний ключ допоможе ... банку. 4. Щоб 
> провітрити кімнату, треба ... вікна. 
> 87.	 Виберіть із рамки біля речення слово, яке потрібно вставити на 
> місці пропуску. Запишіть утворені речення. 
> 1.

## Summary

> **Source:** avramenko, Grade 7
> **Section:** Сторінка 84
> **Score:** 0.33
>
> 81
> РОЗВИТОК МОВЛЕННЯ
> 2.	 Прочитайте текст і виконайте завдання.  
> ЯК ПОВОДИТИСЯ ПІД ЧАС ПОЖЕЖІ В НАВЧАЛЬНОМУ ЗАКЛАДІ, 
> КОЛИ ПОРУЧ НЕМАЄ ДОРОСЛОЇ ЛЮДИНИ?
> Пожежа в класі
> 1. Під час пожежі виходьте з класу через двері й допоможіть іншим.
> 2. Якщо вихід перекриває вогонь, але поряд є зовнішня пожежна дра-
> бина, використайте її.
> 3. Під час пожежі не ховайтеся в кутки, під парти тощо.
> 4. Захищайте органи дихання змоченою тканиною. 
> 5. Подавайте сигнали рятувальникам. 
> Пожежа в коридорі
> 1. Перш ніж визирнути в коридор, доторкніться тильним боком долоні 
> до ручки вхідних дверей; якщо вона гаряча, не відчиняйте: там пожежа. 
> 2. Ручка холодна — визирніть у коридор. Якщо в коридорі вогонь або 
> багато диму, поверніться до класу та зачиніть двері. 
> 3.

## Grammar Reference

> **Source:** avramenko, Grade 6
> **Section:** Сторінка 165
> **Score:** 0.33
>
> Гаразд, прокинусь і вкушу його як потрібно, 
> тоді він стане моїм рабом назавжди й зробить усе, що я звелю. Марно було чекати на допомогу. Тож я почав діяти швидко й рішуче. На­пруживши всі м’язи, я почав звиватися, як вуж, і сантиметр за сан­ти­
> метром рухатися в бік паркану, що оточував цей фальшивий будівельний 
> майдан­чик. Нарешті я виповз за межі випаленого кола порепаної землі, 
> де про­довжував хропіти синьопикий. (...) Я проліз крізь дірку в паркані й 
> опинився на гамірній вулиці. Мало не потрапивши під колеса автобуса,

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


## МійКлас Theory (miyklas.com.ua)

*Ukrainian school curriculum theory — use this terminology and teaching approach.*

### Голосні й приголосні звуки
> **Source:** МійКлас — [Голосні й приголосні звуки](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/fonetika-grafika-orfoepiia-orfografiia-14565/golosni-i-prigolosni-zvuki-40864)

### Теорія:

*www.ua.pistacja.tv*  
Що означають терміни «фонетика», «графіка», «орфоепія», «орфографія»
Фонетика \(від. грец. phonetikos — звуковий\) — це розділ мовознавства, що вивчає звуки  мови.
 
Графіка \(від грец. grapho — пишу\) — це розділ мовознавства, що вивчає cукупність умовних знаків \(букв та символів\) для передачі звуків на письмі.
 
Орфоепія \(від грец. orthos — правильний,  epos — мова, мовлення\) — це розділ мовознавства, що вивчає правила літературної вимови.

Орфографія \(від грец. orthos — правильний, grapho — пишу\) — це розділ мовознавства, що вивчає правила написання слів.
Голосні та приголосні звуки
Звук — найменша одиниця мови та мовлення.

### Словосполучення
> **Source:** МійКлас — [Словосполучення](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/vidomosti-z-sintaksisu-i-punktuatciyi-14562/slovospoluchennia-39535)

### Теорія:

*www.ua.pistacja.tv*  
Словосполучення
Словосполучення — це поєднання дв**ох і 

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Dialogues` (~300 words)
- `## Екстрені ситуації (Emergencies)` (~300 words)
- `## Допомога (Getting Help)` (~300 words)
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

PLAN-AWARE EXEMPTIONS: The following bans are RELAXED for this module because the plan explicitly teaches these constructs: Perfective aspect (plan teaches perfective verbs). Exception: If a grammar construct appears in this module's plan grammar list or objectives, it is ALLOWED for this module.

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
  1. **A minor car accident on вулиця Хрещатик (f) — calling 103: Допоможіть! Аварія (f, accident) на Хрещатику! Потрібна швидка (f, ambulance)! Є постраждалий (m, injured person). Машина (f, car) пошкоджена.**
     Speakers: Водій (driver), Оператор 103
     Why: Emergency with аварія(f), швидка(f), машина(f), вулиця(f)

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

**Required:** допомога (help, f), допоможіть (help! — imperative), швидка (ambulance, f — short for швидка допомога), поліція (police, f), лікарня (hospital, f), аварія (accident, f), загубити (to lose), викликати (to call/summon)
**Recommended:** пожежа (fire, f), порятунок (rescue, m), паспорт (passport, m), адреса (address, f), номер (number, m), алергія (allergy, f), форма (form/document, f), будинок (building, m)

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
- Dialogue 1 (~120 words): Emergency call to 112 — Адам witnesses a car accident on вулиця Хрещатик. Full exchange: оператор greets (Служба порятунку, слухаю вас) → Адам reports (Допоможіть! Тут аварія! Людина не рухається!) → оператор asks location (Де ви?) → Адам gives address (На вулиці Хрещатик, біля метро Майдан Незалежності) → оператор confirms (Швидка вже їде. Як вас звати?) → Адам gives name and phone number (Мене звати Адам. Мій номер — нуль дев'яносто три...) → оператор closes (Дякую. Залишайтеся на місці). Bold key emergency phrases.
- Dialogue 2 (~120 words): Lost passport scenario — Адам asks a passerby for directions to the police station (Вибачте, де тут поліція? → Прямо і наліво). Then at the station: greeting, reports (Я загубив паспорт), officer asks where (Де ви його загубили? → Я не знаю. Може, в метро), officer collects personal info — прізвище (Сміт), номер телефону (нуль дев'яносто три...), ends with instruction to fill out a form (Заповніть цю форму, будь ласка). Bold words: загубив, прізвище, форма.
- P3 (~60 words): Brief note after dialogues — what to observe: (1) emergency imperatives Допоможіть!/Викличте! open both calls; (2) location comes before name when talking to emergency services; (3) паспорт / форма / прізвище are key police vocabulary. Encourages re-reading both dialogues aloud.

## Екстрені ситуації (Emergencies) (~300 words total)
- P1 (~80 words): Introduce 112 (один один два) as Ukraine's universal emergency number — works for ambulance, police, and fire brigade from any phone. Note that 103 reaches ambulance directly and 102 reaches police. Frame these as survival chunks the learner must memorise before their first trip to Ukraine. Emphasis: you don't need grammar — you need the phrase.
- P2 (~100 words): Core emergency phrase set — present as a labelled chunk list with English glosses: Допоможіть! (Help!), Викличте швидку! (Call an ambulance!), Викличте поліцію! (Call the police!), Тут аварія! (There's an accident here!), Тут пожежа! (There's a fire here!), Людині погано! (Someone is feeling unwell!), Мені потрібна допомога! (I need help!). Note that Допоможіть and Викличте are imperatives reviewed from M43 — no new grammar, just new vocabulary.
- P3 (~80 words): Giving your location to the operator — present as a mini-pattern drill: Я на вулиці... (I'm on … street), Я біля... (I'm near...), Я в метро... (I'm in the metro...), Адреса: вулиця Хрещатик, будинок десять. Cross-reference A1.5 prepositions (біля, навпроти, поруч). Tip: know your hotel address in Ukrainian — programme it into your phone before you travel.
- Exercise (~40 words): **Quiz** — 5 items from activity_hints: choose the correct emergency phrase for the described situation (car crash → Тут аварія! Викличте швидку!; fire → Тут пожежа! Допоможіть!; person ill → Людині погано! Викличте швидку!; lost passport → Я загубив паспорт; stolen wallet → Викличте поліцію! Допоможіть!).

## Допомога (Getting Help) (~300 words total)
- P1 (~90 words): At the hospital (лікарня) — three essential phrases: Мені потрібен лікар (I need a doctor — note мені потрібен as a fixed chunk, no grammar analysis), У мене болить... (My … hurts — vocabulary reviewed from M53: голова, спина, рука, нога), У мене алергія на... (I'm allergic to... — followed by the allergen in accusative: ці таблетки, горіхи, пеніцилін). Point out алергія is an international word learners already recognise.
- P2 (~80 words): Communication help phrases for when Ukrainian is too fast or too complex: Я не розумію (I don't understand), Повторіть, будь ласка (Please repeat — imperative from M43), Говоріть повільніше, будь ласка (Please speak more slowly), Ви говорите англійською? (Do you speak English?). Frame these as your "emergency brake" — use them immediately rather than nodding and hoping.
- P3 (~90 words): Personal information checklist for emergencies — present as a table-like bulleted list with examples: Мене звати Адам (name), Моє прізвище — Сміт (surname), Мій номер телефону — нуль дев'яносто три... (phone), Я з Канади / Великої Британії (country of origin), Мій паспорт / Я загубив паспорт (document), Мій готель — «Прем'єр Палас» (hotel). Note all items reviewed from M02, M10, M20 — applied here to a critical real-life situation.
- Exercise 1 (~20 words label): **Fill-in** — 6 items: complete the emergency phone call (Алло! {Допоможіть}! Тут аварія! / {Викличте} швидку допомогу! / Я на {вулиці} Хрещатик / Мене {звати} Адам / Мій номер {телефону} — нуль дев'яносто три / Мені потрібна {допомога}!).
- Exercise 2 (~20 words label): **Order** — put 6 lines of a 112 dialogue in correct sequence (Служба порятунку → Допоможіть! Тут пожежа! → Де ви? → На вулиці Шевченка, будинок п'ять → Зрозуміло. Як вас звати? → Мене звати Анна. Дякую!).

## Summary (~300 words total)
- P1 (~60 words): Brief recap paragraph — ties together the three scenarios practised: calling 112 for an accident or fire, going to the поліція for a lost document, visiting the лікарня for a health issue. Reminds learner that the same personal information block (ім'я, прізвище, номер телефону, адреса) is needed in all three situations.
- P2 (~80 words): Emergency survival kit — formatted as a clearly labelled reference block:
  - **112** — universal emergency number (один один два)
  - **Допоможіть! Викличте швидку / поліцію!** — first words to say
  - **Тут аварія / пожежа!** — describe the emergency
  - **Я на вулиці... / Я біля...** — give your location
  - **У мене болить... / Мені потрібен лікар.** — at the hospital
  - **Я загубив/загубила [document].** — at the police station
  - **Ім'я, прізвище, номер телефону, країна, адреса** — personal info always needed
- P3 — Self-check (~80 words): Bulleted Q&A practice prompts (as specified in plan):
  - What is Ukraine's universal emergency number? → 112 (один один два)
  - How do you shout "Help!" in Ukrainian? → Допоможіть!
  - How do you call an ambulance? → Викличте швидку!
  - How do you give your street address? → Я на вулиці [name], будинок [number].
  - How do you say "I lost my passport"? → Я загубив/загубила паспорт.
  - How do you ask a doctor to repeat something? → Повторіть, будь ласка.
- Exercise (~80 words label): **Fill-in** — 5 items for police station / hospital scenario: Добрий день. Я {загубив} паспорт / Моє {прізвище} — Сміт / Мені {потрібен} лікар / У мене {алергія} на ці таблетки / Я не розумію. {Повторіть}, будь ласка.

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
