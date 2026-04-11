<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 54: Emergencies (A1, A1.8 [Past, Future, Graduation])
**Writer:** Gemini
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

When you face a high-stress situation in a foreign country, communication needs to be extremely fast and direct. In emergencies, Ukrainian shifts to short, functional chunks of information. Clarity is significantly more important than perfect grammar or vocabulary. You simply need to convey exactly what happened and precisely where you are. Memorizing these simple, direct phrases allows you to deploy them automatically without overthinking the grammatical rules.

Consider a critical situation where timing is everything. Adam witnesses a minor car crash on **ву́лиця Хреща́тик** (Khreshchatyk street) and immediately calls the emergency number. He needs to report the **ава́рія** (accident) and forcefully request a **швидка́** (ambulance). The emergency operator asks for the incident details and his exact location to dispatch help. Adam provides his precise location near the metro station and clearly states his personal information to the operator.

> **Опера́тор 103:** Слу́жба поряту́нку, слу́хаю вас. *(Rescue service, I am listening to you.)*
> **Адам:** Допоможі́ть! Тут аварія! *(Help! There is an accident here!)*
> **Адам:** Люди́на не ру́хається! *(A person is not moving!)*
> **Оператор 103:** Де ви? *(Where are you?)*
> **Адам:** На ву́лиці Хрещатик, бі́ля метро́ Майда́н Незале́жності. *(On Khreshchatyk street, near the Independence Square metro.)*
> **Оператор 103:** Зрозумі́ло. Швидка вже ї́де. *(Understood. An ambulance is already coming.)*
> **Оператор 103:** Як вас зва́ти? *(What is your name?)*
> **Адам:** Ме́не звати Адам. Мій но́мер — нуль дев'яно́сто три... *(My name is Adam. My number is zero ninety-three...)*
> **Оператор 103:** Дякую. Залиша́йтеся на мі́сці. *(Thank you. Stay in place.)*

Not every emergency involves a life-threatening medical issue. Sometimes you face an incredibly frustrating administrative crisis, like losing your travel documents in a busy city. In this dialogue, Adam visits the **полі́ція** (police) for help. First, he asks a helpful passerby for directions to the nearest station. Once inside the station, he clearly reports his loss to the duty officer. The police officer asks for his **прі́звище** (surname) and his mobile phone number. Finally, the officer gives him a **фо́рма** (form) to complete for the official record.

> **Адам:** Ви́бачте, де тут поліція? *(Excuse me, where is the police here?)*
> **Перехо́жий:** Поліція? Пря́мо і налі́во. *(Police? Straight and to the left.)*
> **Адам:** Дякую! *(Thank you!)*
> *(У ві́дділку полі́ції / At the police station)*
> **Адам:** До́брий день. Я загуби́в па́спорт. *(Good day. I lost my passport.)*
> **Офіце́р:** Де ви йо́го загуби́ли? *(Where did you lose it?)*
> **Адам:** Я не зна́ю. Мо́же, в метро. *(I do not know. Maybe in the metro.)*
> **Офіцер:** Як ва́ше прізвище? *(What is your surname?)*
> **Адам:** Сміт. Адам Сміт. *(Smith. Adam Smith.)*
> **Офіцер:** Ваш номер телефо́ну? *(Your phone number?)*
> **Адам:** Нуль дев'яносто три, п'ятсо́т два́дцять оди́н... *(Zero ninety-three, five hundred twenty-one...)*
> **Офіцер:** До́бре. Запо́вніть цю фо́рму, будь ла́ска. *(Good. Fill out this form, please.)*

Both of these dialogues share a highly effective communicative strategy. Notice the reliable, repeatable pattern: first, give the urgent alert for help to get immediate attention. Second, state the core problem clearly and concisely. Third, provide your exact location using simple prepositions of place. Finally, state your personal identity and contact details so the responding officials can follow up with you later.

<!-- INJECT_ACTIVITY: dialogue-order -->

## Е́кстрені ситуа́ції (Emergencies)

The universal emergency number in Ukraine is **112** (один один два). This number works absolutely everywhere in the country and connects you directly to a central dispatcher who can route your call. However, you must also know the specific direct numbers for specialized services. The number **101** connects directly to the **поже́жна допомо́га** (fire service). The number **102** is the direct line for the **поліція** (police). Finally, **103** calls the **швидка допомога** (ambulance). These three numbers are non-negotiable memorization items for your personal safety in Ukraine.

:::caution
**Important distinction:** The numbers **101**, **102**, and **103** are the modern Ukrainian emergency lines. Never confuse these with the old Soviet lines.
:::

When you need immediate, life-saving action, you rely entirely on the power of the imperative mood. Because you are addressing an emergency operator or a random stranger on the street, you consistently use formal plural imperative endings like **-іть** or **-те**. Learn these core survival calls as complete, unbreakable chunks of language. Do not worry about grammatical analysis or verb conjugation right now; just memorize the sound and meaning so you can produce them automatically under intense pressure. For example, use the verb **викликати** (to call/summon):

*   **Допоможіть!** (Help!)
*   **Ви́кличте швидку́!** (Call an ambulance!)
*   **Викличте полі́цію!** (Call the police!)

After successfully getting someone's attention, you must rapidly identify the specific situation. Introduce the exact problem using short, distinct labels. The word **тут** (here) is an incredibly useful tool for pointing out an active crisis happening right next to you. If you see someone collapse, shouting your medical alert instantly signals a severe emergency to nearby bystanders. For a more general statement of need, you can always state that you require immediate help.

*   **Тут аварія!** (There is an accident here!)
*   **Тут поже́жа!** (There is a fire here!)
*   **Люди́ні пога́но!** (Someone is feeling bad!)
*   **Ме́ні потрі́бна допомога!** (I need help!)

The emergency operator will inevitably ask for your exact location. You must state your current address quickly and accurately. The standard Ukrainian address formula starts with the largest element and gets progressively smaller: **вулиця** (street), then **буди́нок** (building), and finally **кварти́ра** (apartment). Reinforce this vital skill with the location vocabulary you learned from previous modules. Prepositions like **на** (on) and **біля** (near) become absolutely critical tools when you need to guide a speeding ambulance to your exact location.

*   **Я на вулиці Шевче́нка.** (I am on Shevchenko street.)
*   **Я біля метро.** (I am near the metro.)
*   **Адре́са: вулиця Хрещатик, будинок де́сять.** (Address: Khreshchatyk street, building ten.)

<!-- INJECT_ACTIVITY: phrase-choice-quiz -->
<!-- INJECT_ACTIVITY: fill-in-emergency-call -->

## Допомога (Getting Help)

When seeking medical assistance at a local **ліка́рня** (hospital), always start with the direct request for a doctor. To explain your specific physical symptoms, use the standard structure for expressing pain. This unique structure literally translates to "At me aches". You just attach the necessary body part that is causing the discomfort. If you do not have a specific, localized pain but feel generally unwell, simply use the standard everyday expression for feeling ill.

*   **Мені потрі́бен лі́кар.** (I need a doctor.)
*   **У мене боли́ть голова́.** (My head hurts.)
*   **У мене болить живі́т.** (My stomach hurts.)
*   **У мене болить го́рло.** (My throat hurts.)
*   **Мені погано.** (I feel bad.)

:::tip
The word **швидка** literally means "fast one" and is the natural, everyday word Ukrainians use for an ambulance. You do not need to say the full phrase.
:::

If you need to visit a local pharmacy for minor medical issues, use clear and polite requests for your medicine. However, the absolute most critical safety phrase you must learn involves medical precautions. You have to communicate your specific medical restrictions and severe allergies clearly before accepting any treatment. This ensures you do not receive medication that could cause a secondary emergency.

*   **Да́йте, будь ласка, табле́тки.** (Give me the pills, please.)
*   **Мені потрі́бні лі́ки.** (I need medicine.)
*   **У мене алергі́я на антибіо́тики.** (I am allergic to antibiotics.)
*   **У мене алергія на ці таблетки.** (I am allergic to these pills.)

Bureaucratic situations require you to provide your personal data to government officials clearly and accurately. Whether at a city hospital or a local police station, they will inevitably ask for your identity documents. Remember the critical difference between your **ім'я́** (first name) and your **прізвище** (surname). If you lose something valuable, always use the past tense verb **загуби́ти** (to lose) matched to your specific gender.

*   **Моє́ прізвище — Сміт.** (My surname is Smith.)
*   **Я з Кана́ди.** (I am from Canada.)
*   **Мій паспорт у готе́лі.** (My passport is in the hotel.)
*   **Я загубив паспорт.** (I lost my passport. — masculine)
*   **Я загуби́ла телефо́н.** (I lost my phone. — feminine)

:::note
In official contexts, your **прізвище** (surname) is much more important than your **ім'я** (first name). Always provide your surname first when speaking to police or hospital staff.
:::

During a high-stress conversation with authorities, you might simply fail to understand what the Ukrainian official is rapidly telling you. You must communicate your language barrier directly and honestly rather than just guessing what they said. Use these essential survival phrases to slow the entire exchange down and clarify the exact meaning before proceeding.

*   **Я не розумі́ю.** (I do not understand.)
*   **Повторі́ть, будь ласка.** (Please repeat.)
*   **Ви гово́рите англі́йською?** (Do you speak English?)

<!-- INJECT_ACTIVITY: report-issue-fill-in -->

## Summary

Your emergency survival kit revolves entirely around a few core verbal actions. The number **112** is your absolute primary tool for any crisis. If you are in physical danger, shout the imperative for help immediately to draw massive public attention. Follow this quickly with loud requests for an ambulance or the police. Remember that sheer speed and absolute clarity in Ukrainian chunks always beat perfect grammatical case endings in these critical moments. A fast, incredibly clear alert provides all the context anyone needs.

Knowing your precise location is completely useless if you cannot express it clearly to the emergency operator. Always be ready to state your physical address using the strict logical order of street followed by building. If you are outside and feel slightly disoriented, rely heavily on large visible landmarks. Stating that you are near the metro station or directly opposite a large hotel gives the emergency services an immediate and tight search radius.

Medical and personal emergencies require highly specific vocabulary. Use the dedicated pain structure to describe your physical issues to a responding doctor. For frustrating administrative disasters, state that you lost your documents using the correct gendered past tense verb form. Always keep your official surname and mobile phone number ready for the inevitable official forms.

Before moving on to the next learning module, perform this final rigorous self-check to ensure you are truly ready for unexpected situations. Read these questions carefully and try to answer them aloud in clear Ukrainian. These phrases are your ultimate linguistic safety net. Practice them until they feel completely automatic, so you never have to search your memory for words when you truly need them the most.

*   Can you call 112 and state there is an accident? (**Тут аварія!**)
*   Can you give your current address including street and building? (**Вулиця..., будинок...**)
*   Can you tell a doctor what hurts? (**У мене болить...**)
*   Can you report a lost passport to the police? (**Я загубив паспорт. Моє прізвище...**)
*   Do you know the difference between 101, 102, and 103?
</generated_module_content>

**PIPELINE NOTE — Word count: 1704 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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
| 6 | **Engagement & tone** | 10% | The writer's persona is an encouraging teacher — natural teacher phrasing like "Let us look at..." or "Have you noticed..." is FINE and should NOT be penalized. DEDUCT ONLY for: self-congratulatory openers ("Welcome to A2! Congratulations on completing..."), gamified/corporate language ("You have unlocked...", "You now possess...", "Your journey begins..."), empty filler that adds words but zero information ("This is a very important concept that you will use frequently in your daily life"), generic enthusiasm not specific to Ukrainian ("incredibly beautiful language", "wonderfully consistent system"). REWARD for: teacher warmth with substance, specific cultural details, humor, concrete Ukrainian examples, natural classroom energy. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count BELOW 1200 (more content is always welcome — never penalize for exceeding the target), dangling/incomplete sentences, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count at or above target. |
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

Verified: 85 words | Not found: 61 words

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
  ✗ Слу — NOT IN VESUM
  ✗ Сміт — NOT IN VESUM
  ✗ Хреща — NOT IN VESUM
  ✗ Хрещатик — NOT IN VESUM
  ✗ алергі — NOT IN VESUM
  ✗ англі — NOT IN VESUM
  ✗ антибіо — NOT IN VESUM
  ✗ бна — NOT IN VESUM
  ✗ бні — NOT IN VESUM
  ✗ вніть — NOT IN VESUM
  ✗ гово — NOT IN VESUM
  ✗ дділку — NOT IN VESUM
  ✗ дев'яно — NOT IN VESUM
  ✗ допомо — NOT IN VESUM
  ✗ дцять — NOT IN VESUM
  ✗ жба — NOT IN VESUM
  ✗ жий — NOT IN VESUM
  ✗ жна — NOT IN VESUM
  ✗ жності — NOT IN VESUM
  ✗ зва — NOT IN VESUM
  ✗ йською — NOT IN VESUM
  ✗ йте — NOT IN VESUM
  ✗ йтеся — NOT IN VESUM
  ✗ кстрені — NOT IN VESUM
  ✗ ліка — NOT IN VESUM
  ✗ налі — NOT IN VESUM
  ✗ нка — NOT IN VESUM
  ✗ нку — NOT IN VESUM
  ✗ нок — NOT IN VESUM
  ✗ п'ятсо — NOT IN VESUM
  ✗ пога — NOT IN VESUM
  ✗ поже — NOT IN VESUM
  ✗ поряту — NOT IN VESUM
  ✗ потрі — NOT IN VESUM
  ✗ рло — NOT IN VESUM
  ✗ рма — NOT IN VESUM
  ✗ рму — NOT IN VESUM
  ✗ рня — NOT IN VESUM
  ✗ рія — NOT IN VESUM
  ✗ ситуа — NOT IN VESUM

All 85 other words are confirmed to exist in VESUM.

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
