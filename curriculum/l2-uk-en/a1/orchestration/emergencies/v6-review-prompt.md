<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 54: Emergencies (A1, A1.8 [Past, Future, Graduation])
**Writer:** Claude
**Word target:** 1200

## Plan (source of truth)

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

## Generated Content

<generated_module_content>
## Dialogues

> — **Опера́тор:** Слу́жба поряту́нку, слу́хаю вас. *(Emergency service, I'm listening.)*
> — **Адам:** Допоможі́ть! Тут ава́рія! *(Help! There's an accident here!)*
> — **Адам:** Люди́на не ру́хається! *(A person isn't moving!)*
> — **Оператор:** Де ви? *(Where are you?)*
> — **Адам:** На ву́лиці Хреща́тик, бі́ля метро́ Майда́н Незале́жності. *(On Khreshchatyk street, near Maidan Nezalezhnosti metro.)*
> — **Оператор:** Зрозумі́ло. Швидка́ вже ї́де. *(Understood. The ambulance is already on its way.)*
> — **Оператор:** Як вас зва́ти? *(What's your name?)*
> — **Адам:** Ме́не звати Адам. *(My name is Adam.)*
> — **Адам:** Мій но́мер — нуль дев'яно́сто три... *(My number is zero ninety-three...)*
> — **Оператор:** Дякую. Залиша́йтеся на мі́сці. *(Thank you. Stay where you are.)*

Адам is walking near Maidan when he sees a car crash. He dials **112** (оди́н один два) — Ukraine's universal emergency number. The operator at **служба порятунку** (rescue service) picks up immediately. Notice how Адам uses short, urgent phrases: **Допоможіть!** (Help!), **Тут аварія!** (There's an accident!). No long sentences — just the essential information. The operator asks **Де ви?** (Where are you?) and Адам gives the street name and a landmark. Only after confirming the ambulance is coming does the operator ask for personal details.

Now Адам has a second problem — his passport is gone.

> — **Адам:** Ви́бачте, де тут полі́ція? *(Excuse me, where is the police station here?)*
> — **Перехо́жий:** Поліція? Пря́мо і налі́во. *(Police? Straight and to the left.)*
> — **Адам:** Дякую! *(Thanks!)*

> — **Адам:** До́брий день. Я загуби́в па́спорт. *(Good day. I lost my passport.)*
> — **Офіце́р:** Де ви йо́го загуби́ли? *(Where did you lose it?)*
> — **Адам:** Я не зна́ю. Мо́же, в метро. *(I don't know. Maybe in the metro.)*
> — **Офіцер:** Як ва́ше прі́звище? *(What is your surname?)*
> — **Адам:** Сміт. Адам Сміт. *(Smith. Adam Smith.)*
> — **Офіцер:** Ваш номер телефо́ну? *(Your phone number?)*
> — **Адам:** Нуль дев'яносто три, п'ятсо́т два́дцять один... *(Zero ninety-three, five hundred twenty-one...)*
> — **Офіцер:** До́бре. Запо́вніть цю фо́рму, будь ла́ска. *(Good. Fill out this form, please.)*

Read both dialogues again and notice three things. First, emergency imperatives open the conversation — **Допоможіть!** and **Ви́кличте!** get immediate attention. Second, when talking to emergency services, location comes before your name: the operator needs to know *where* before *who*. Third, at the police station, the key vocabulary shifts to documents: **паспорт** (passport), **прізвище** (surname), and **фо́рма** (form). Read both dialogues aloud — the rhythm of short emergency phrases will stick in your memory.

## Е́кстрені ситуа́ції (Emergencies)

Ukraine's universal emergency number is **112** (**один один два**). It works from any phone — mobile or landline — and connects you to ambulance, police, or fire services. You can also call specific services directly: **103** reaches the ambulance (**швидка**), and **102** reaches the police (**поліція**). Before your first trip to Ukraine, save these numbers in your phone. You do not need perfect grammar to use them — you need the right phrase at the right moment.

Here are the survival phrases every learner must memorise as fixed chunks. Do not analyze the grammar — just learn them whole:

- **Допоможіть!** — Help!
- **Викличте швидку́!** — Call an ambulance!
- **Викличте полі́цію!** — Call the police!
- **Тут аварія!** — There's an accident here!
- **Тут поже́жа!** — There's a fire here!
- **Люди́ні пога́но!** — Someone is feeling unwell!
- **Ме́ні потрі́бна допомо́га!** — I need help!

You already know **Допоможіть** and **Викличте** — these are imperative forms reviewed from Module 43. The vocabulary is new, but the grammar pattern is familiar. **Аварія** (accident) and **пожежа** (fire) are passive recognition words — you will hear and understand them, and you use them only inside these fixed phrases.

Once the operator answers, they will ask **Де ви?** (Where are you?). Give your location using patterns from A1.5:

- **Я на вулиці...** — I'm on … street.
- **Я біля...** — I'm near...
- **Я в метро...** — I'm in the metro...
- **Адре́са: ву́лиця Хрещатик, буди́нок де́сять.** — Address: Khreshchatyk street, building 10.

:::tip
Know your hotel address in Ukrainian. Programme it into your phone before you travel — if you are stressed in an emergency, reading from your screen is much easier than translating on the fly.
:::

<!-- INJECT_ACTIVITY: quiz-emergency-phrases -->

## Допомога (Getting Help)

At a hospital (**ліка́рня**), three phrases will carry you through the first minutes. **Мені потрі́бен лі́кар** (I need a doctor) uses the fixed chunk **мені потрібен** — treat it as a memorised formula, just as you learned **мені подо́бається** earlier. From Module 53 you already know **У мене боли́ть...** (My … hurts) — plug in **голова́** (head), **спи́на** (back), **рука́** (arm/hand), or **нога́** (leg/foot). If you have allergies, say **У мене алергі́я на...** (I'm allergic to...) followed by the allergen: **ці табле́тки** (these pills), **горі́хи** (nuts), **пеніцилі́н** (penicillin). The word **алергія** looks and sounds almost identical to its English equivalent — one less thing to memorise under pressure.

When Ukrainian comes too fast or you simply cannot follow, use these phrases as your emergency brake — reach for them immediately rather than nodding and hoping:

- **Я не розумі́ю.** — I don't understand.
- **Повторі́ть, будь ласка.** — Please repeat.
- **Говорі́ть пові́льніше, будь ласка.** — Please speak more slowly.
- **Ви гово́рите англі́йською?** — Do you speak English?

**Повторіть** and **говоріть** are imperative forms — the same pattern as **Допоможіть** and **Викличте**. You are not learning new grammar here, just applying familiar patterns in a new, critical context.

Finally, in any emergency — hospital, police station, or phone call — you will need the same block of personal information. Here is your checklist:

- **Мене звати Адам.** — My name is Adam.
- **Моє́ прізвище — Сміт.** — My surname is Smith.
- **Мій номер телефону — нуль дев'яносто три...** — My phone number is zero ninety-three...
- **Я з Кана́ди.** — I'm from Canada.
- **Я загубив паспорт.** — I lost my passport. *(male speaker)*
- **Я загуби́ла паспорт.** — I lost my passport. *(female speaker)*
- **Мій готе́ль — «Прем'є́р Пала́с».** — My hotel is Premier Palace.

Every item here is review from earlier modules — **Мене звати** from Module 2, **Я з** from Module 10, **Мій номер** from Module 20. The difference is the stakes: now you are not introducing yourself at a café, you are giving information that may determine how quickly help reaches you.

<!-- INJECT_ACTIVITY: fill-in-emergency-call -->

<!-- INJECT_ACTIVITY: order-112-dialogue -->

## Summary

The three scenarios in this module — calling **112** for an accident, reporting a lost document at the **поліція**, and asking for help at the **лікарня** — all follow the same structure. You state the problem, give your location, and share personal details: **ім'я́** (first name), **прізвище** (surname), **номер телефону** (phone number), and **адреса** (address). Master this pattern once and it works everywhere.

Here is your emergency survival kit — a reference block to save on your phone:

- **112** — universal emergency number (**один один два**)
- **Допоможіть! Викличте швидку / поліцію!** — first words to say
- **Тут аварія / пожежа!** — describe the emergency
- **Я на вулиці... / Я біля...** — give your location
- **У мене болить... / Мені потрібен лікар.** — at the hospital
- **Я загубив/загубила [document].** — at the police station
- **Ім'я, прізвище, номер телефону, краї́на, адреса** — personal info always needed

Test yourself with these questions — answer each one aloud in Ukrainian before checking:

- What is Ukraine's universal emergency number? → **112** (**один один два**)
- How do you shout "Help!" in Ukrainian? → **Допоможіть!**
- How do you call an ambulance? → **Викличте швидку!**
- How do you give your street address? → **Я на вулиці [name], будинок [number].**
- How do you say "I lost my passport"? → **Я загубив/загубила паспорт.**
- How do you ask a doctor to repeat something? → **Повторіть, будь ласка.**

<!-- INJECT_ACTIVITY: fill-in-police-hospital -->

**Deterministic word count: 1291 words** (calculated by pipeline, do NOT estimate manually)

</generated_module_content>

---

## Review Protocol

### Step 1: Scan for linguistic errors

Scan the Ukrainian text for errors. Report ONLY problems found — do not echo correct text.

**Four SEPARATE checks (these are four different problems):**
1. **Russianisms** — Russian words used instead of Ukrainian (кот→кіт, хорошо→добре, конечно→звичайно, сейчас→зараз)
2. **Surzhyk** — mixed Russian-Ukrainian forms (шо→що, чо→чому, тіпа→типу)
3. **Calques** — literal translations from Russian that sound wrong in Ukrainian (приймати душ→брати душ, приймати рішення→ухвалювати рішення)
4. **Paronyms** — similar-sounding words with different meanings used incorrectly (тактична≠тактовна, ефектний≠ефективний)

**Also check:**
- Russian characters (ы, э, ё, ъ) — these must NEVER appear
- Incorrect gender assignment or case endings
- Factually wrong claims about Ukrainian phonetics, grammar, or culture

**Authority hierarchy for verification (check in this order):**
1. VESUM — does this word/form exist? POS? Gender? (415K lemmas)
2. Правопис 2019 — is it spelled correctly? Orthography rules.
3. Горох — stress position, word frequency, synonyms.
4. Антоненко-Давидович «Як ми говоримо» — is this natural Ukrainian or a calque/Russicism?
5. Грінченко «Словарь» — etymology, original meaning.

**Online fallbacks (if RAG/tools are unavailable):**
- VESUM: https://vesum.com.ua/
- Правопис 2019: https://2019.pravopys.net/
- Горох: https://goroh.pp.ua/
- Антоненко-Давидович: https://www.ukrlib.com.ua/books/printit.php?tid=4002
- Грінченко: https://hrinchenko.com/
- Словник.ua (aggregator): https://slovnyk.me/

**VESUM verification data is provided at the end of this prompt.** Use it to verify word existence before flagging linguistic errors. If a word is marked ✓ in the VESUM data, it EXISTS in Ukrainian — do not flag it as an error. If a word is marked ✗ (NOT IN VESUM), investigate further — it may be a proper noun, a compound, or genuinely wrong.

**CRITICAL: Your pre-training is contaminated by Russian.** Do NOT trust your instincts about Ukrainian words. If you are not 100% certain a word/form/usage is wrong, you MUST flag it as `[NEEDS RAG VERIFICATION]` instead of marking it as a definitive error. Wrong review findings cause wrong fixes. A false positive in the review is worse than a missed error.

If no errors found, state: "No linguistic errors found."

**Do NOT check for stress marks** — stress annotation is handled by a separate deterministic tool after the review phase. Their absence is correct.

### Step 2: Check exercises

The writer places `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. A separate ACTIVITIES step generates structured YAML exercises (`activities/{slug}.yaml`) that are injected at these markers during PUBLISH.

Check the markers and any inline exercises:
- Does each marker appear AFTER the relevant teaching section? (exercise should test what was just taught)
- Do marker IDs match the plan's `activity_hints`? (each hint should have a corresponding marker)
- Are markers spread evenly through the module? (not clustered at the end)
- For seminar modules: DSL exercise blocks (:::quiz, :::fill-in) may appear inline — check their logic

For each exercise (DSL or marker), check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?

Also check: Are there enough exercise markers/blocks total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercise content is generated by a separate tool from YAML. If exercise LOGIC is wrong, flag it. If the FORMAT looks unusual (React components, YAML structure), that is expected.

### PROOF OF ABSENCE — mandatory before claiming ANYTHING is missing

**Before you claim a word, symbol, notation, or plan point is MISSING from the content, you MUST search for it.** Use your MCP tools (`verify_words`, `search_text`) or carefully re-read the specific section where it should appear.

Rules:
- If you claim "[•] notation is missing" — you must have searched the content for `[•]` and confirmed 0 occurrences
- If you claim "vocabulary word X is missing" — you must have searched for that exact word
- If you claim "plan point Y was not covered" — you must quote which section you expected it in and confirm it's not there
- **NO CLAIMS OF ABSENCE WITHOUT EVIDENCE.** Your tokenizer can miss special characters like [•], [–], [=], «», and other non-alphanumeric symbols. Do not trust a quick scan.
- Euphony alternation (у/в, і/й) is a MINOR stylistic issue, NEVER a critical error. Both forms are attested in published Ukrainian literature.

**A false finding wastes an entire rebuild cycle. Be precise.**

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | DEDUCT for: missing content_outline points, section word budgets off by >10%, plan references not cited, vocabulary from plan absent from prose. REWARD for: every plan point covered with specific examples, correct section pacing, textbook references integrated naturally. Quote the plan point that was missed or covered. |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | DEDUCT for: grammar rules presented as bare lists without examples, concepts taught before prerequisite knowledge, >100 words of English theory without a Ukrainian example, bare vocabulary lists instead of contextualized introduction. REWARD for: PPP flow (situation→pattern→practice), 3+ examples per grammar point, textbook pedagogy (Большакова, Захарійчук), grammar scope respected. |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | DEDUCT for: all correct answers at the same index position, trivially easy exercises (1:9 group sort ratios, every answer is the same word), exercises that test content recall instead of language skill, items fewer than plan's activity_hints count, exercises placed before the concept is taught. REWARD for: varied answer positions, plausible distractors, exercises testing what was just taught, matching plan's activity_hints type and focus exactly. |
| 6 | **Engagement & tone** | 10% | DEDUCT for: motivational openers ("Numbers unlock the real Ukraine!"), meta-commentary ("Let us look at...", "Let us now explore..."), generic enthusiasm ("incredibly melodic", "hugely important"), telling instead of showing ("You now possess...", "You have unlocked..."), gamified language ("unlocked the ability"), corporate-speak ("precision and accuracy"), "The magic of...", any sentence that could apply to any language course unchanged. REWARD for: specific cultural details, natural dialogues, humor, concrete examples, teacher demonstrating rather than lecturing about how great the content is. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count outside target range, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count in range. |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | DEDUCT for: purely transactional exchanges ("Do you have X? Yes."), dialogues where one speaker interrogates the other, anonymous em dashes instead of named speakers, stilted/textbook-robotic phrasing. REWARD for: natural multi-turn conversations, real situations (searching for keys, ordering at a cafe, meeting a friend), culturally appropriate responses, named speakers with distinct voices. |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence or quality. If you see a vocabulary table with wrong translations, missing words, or formatting issues, that content was NOT written by the writer — it was generated deterministically by the ENRICH step. Do NOT flag словník problems as linguistic errors or deduct points from the writer. Report them separately under "ENRICH issues" in your findings (informational only, not scored).

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

**CRITICAL RULE: If you mention ANY error, mistake, or inaccuracy in the evidence column of your scores table, you MUST also list it as a structured finding below AND include it in your `<fixes>` block.** Identifying an error in evidence but not outputting a finding+fix means the error ships to learners. This is a language curriculum — every error you identify must be fixed. No exceptions.

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Severity guide:
- **Critical** = factual/linguistic error that teaches wrong Ukrainian (wrong form, wrong rule, wrong example). Module cannot ship.
- **Major** = quality below standard but not factually wrong (weak explanation, awkward phrasing, missing examples).
- **Minor** = polish item (tone, word choice, style).

**Any factual or linguistic error is CRITICAL, not minor.** A wrong syllable division, a wrong phonetic claim, a contradictory grammar rule — these are critical because learners will memorize them as truth.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero findings mentioning errors/mistakes/inaccuracies. All dimensions ≥9. |
| **REVISE** | Has findings with fixes. Any dimension <9 with identified errors = REVISE, not PASS. |
| **REJECT** | Fundamental structural/pedagogical problems requiring rewrite. |

### Step 7: Fix it yourself (REVISE only)

If your verdict is **REVISE**, you MUST output a `<fixes>` block with exact find/replace pairs. The pipeline applies these deterministically — no LLM regeneration, no rewriting from scratch.

Rules for fixes:
- Each fix is a YAML entry with `find:` (exact text from the module) and `replace:` (corrected text)
- The `find` string MUST be an EXACT copy-paste from the module content. DO NOT change quotes (« » to " "), dashes (— to -), or spacing. If you change a single character in the `find` string, the automated replacement will fail.
- Keep fixes minimal — change only what's wrong, preserve surrounding text. Provide enough context (e.g. 5-7 words) to make the match unique.
- Do NOT fix словник/vocabulary tables (those are generated by a downstream tool)
- For word count issues: add content as a new `insert_after:` entry instead of find/replace

---

## Output Format

```
## Linguistic Scan
[errors found, or "No linguistic errors found"]

## Exercise Check
[placeholder inventory and issues]

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | X/10 | [specific evidence from the text] |
| ... | ... | ... |

## Findings
[list all findings with dimension/severity/location/issue/fix]

## Verdict: PASS / REVISE / REJECT
[justification — reference both score gate and severity gate]

<fixes>
- find: "exact text from module"
  replace: "corrected text"
- find: "another exact problem"
  replace: "the fix"
</fixes>
```

**The `<fixes>` block is REQUIRED for REVISE verdicts.** Without it, the pipeline cannot apply your fixes. For PASS verdicts, omit the `<fixes>` block. For REJECT verdicts, the module needs a full rebuild — `<fixes>` is optional.


<vesum_verification>
The following Ukrainian words from the content were verified against VESUM (415K lemmas). Use this data to check linguistic claims — do NOT guess about words.

Verified: 98 words | Not found: 59 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Адам — NOT IN VESUM
  ✗ Адре — NOT IN VESUM
  ✗ Допоможі — NOT IN VESUM
  ✗ Запо — NOT IN VESUM
  ✗ Зрозумі — NOT IN VESUM
  ✗ Кана — NOT IN VESUM
  ✗ Майда — NOT IN VESUM
  ✗ Незале — NOT IN VESUM
  ✗ Офіце — NOT IN VESUM
  ✗ Перехо — NOT IN VESUM
  ✗ Прем'є — NOT IN VESUM
  ✗ Слу — NOT IN VESUM
  ✗ Сміт — NOT IN VESUM
  ✗ Хреща — NOT IN VESUM
  ✗ Хрещатик — NOT IN VESUM
  ✗ алергі — NOT IN VESUM
  ✗ англі — NOT IN VESUM
  ✗ бається — NOT IN VESUM
  ✗ бна — NOT IN VESUM
  ✗ вніть — NOT IN VESUM
  ✗ гово — NOT IN VESUM
  ✗ дев'яно — NOT IN VESUM
  ✗ допомо — NOT IN VESUM
  ✗ дцять — NOT IN VESUM
  ✗ жба — NOT IN VESUM
  ✗ жий — NOT IN VESUM
  ✗ жності — NOT IN VESUM
  ✗ зва — NOT IN VESUM
  ✗ йською — NOT IN VESUM
  ✗ йтеся — NOT IN VESUM
  ✗ кстрені — NOT IN VESUM
  ✗ льніше — NOT IN VESUM
  ✗ ліка — NOT IN VESUM
  ✗ налі — NOT IN VESUM
  ✗ нку — NOT IN VESUM
  ✗ нок — NOT IN VESUM
  ✗ п'ятсо — NOT IN VESUM
  ✗ пеніцилі — NOT IN VESUM
  ✗ пові — NOT IN VESUM
  ✗ пога — NOT IN VESUM
  ✗ подо — NOT IN VESUM
  ✗ поже — NOT IN VESUM
  ✗ поряту — NOT IN VESUM
  ✗ потрі — NOT IN VESUM
  ✗ рма — NOT IN VESUM
  ✗ рму — NOT IN VESUM
  ✗ рня — NOT IN VESUM
  ✗ рія — NOT IN VESUM
  ✗ ситуа — NOT IN VESUM
  ✗ слу — NOT IN VESUM

All 98 other words are confirmed to exist in VESUM.

</vesum_verification>

## Verification Tools (MCP)

You have MCP tools to VERIFY claims in the content. Use them to cite evidence:

**Core Verification:**
- `mcp_rag_verify_words` — batch-verify Ukrainian words against VESUM (409K lemmas)
- `mcp_rag_verify_lemma` — full declension/conjugation for a lemma
- `mcp_rag_search_style_guide` — **HIGH PRIORITY.** Check for calques/Russianisms (Антоненко-Давидович)
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Confirm Russicism alternatives.
- `mcp_rag_query_pravopys` — verify orthography rules (Правопис 2019)

**Content Quality:**
- `mcp_rag_query_cefr_level` — verify vocabulary is level-appropriate (PULS, 5.9K words)
- `mcp_rag_search_definitions` — exact Ukrainian definitions (СУМ-11, 127K entries)
- `mcp_rag_search_etymology` — historical forms, etymology (Грінченко, 67K entries)
- `mcp_rag_search_idioms` — verify idioms are authentic Ukrainian (25K entries)
- `mcp_rag_search_synonyms` — suggest better word choices (Ukrajinet, 122K synsets)
- `mcp_rag_query_grac` — check collocations and frequency in GRAC corpus (2B tokens)

**Reference:**
- `mcp_rag_search_text` — check how textbooks teach the topic (Grades 1-11)
- `mcp_rag_search_literary` — verify literary references against primary sources
- `mcp_rag_query_wikipedia` — fact-check historical/cultural claims

**Evidence standard:** A review that says "this might be a Russicism" is WEAK. A review that says "`search_style_guide` confirms 'приймати участь' is a calque — correct form: 'брати участь'" is STRONG. Cite tool results.
