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

In an emergency, short phrases matter more than perfect grammar. Learn how to state the problem, give your location, and give your personal details in Ukrainian.

> **Оператор:** Служба порятунку, слухаю вас. *(Rescue service, I am listening to you.)*
> **Водій:** Допоможіть! Тут аварія! Людина не рухається! *(Help! There is an accident here! A person is not moving!)*
> **Оператор:** Де ви? *(Where are you?)*
> **Водій:** На вулиці Хрещатик, біля метро Майдан Незалежності. *(On Khreshchatyk street, near the Maidan Nezalezhnosti metro.)*
> **Оператор:** Зрозуміло. Швидка вже їде. Як вас звати? *(Understood. The ambulance is already on its way. What is your name?)*
> **Водій:** Мене звати Адам. Мій номер — нуль дев'яносто три... *(My name is Adam. My number is zero ninety-three...)*
> **Оператор:** Дякую. Залишайтеся на місці. *(Thank you. Stay in place.)*

This dialogue shows a critical situation on the road. The driver uses short, urgent sentences. **Аварія** (accident) immediately tells the operator the nature of the event. The driver then gives the exact location and answers simple questions. The operator confirms that a **швидка** (ambulance) is coming.

> **Адам:** Вибачте, де тут поліція? *(Excuse me, where is the police here?)*
> **Перехожий:** Поліція? Прямо і наліво. *(Police? Straight and to the left.)*
> **Адам:** Дякую! *(Thank you!)*
>
> *(У відділку / At the station)*
> **Адам:** Добрий день. Я загубив паспорт. *(Good day. I lost my passport.)*
> **Офіцер:** Де ви його загубили? *(Where did you lose it?)*
> **Адам:** Я не знаю. Може, в метро. *(I do not know. Maybe in the metro.)*
> **Офіцер:** Як ваше прізвище? *(What is your surname?)*
> **Адам:** Сміт. Адам Сміт. *(Smith. Adam Smith.)*
> **Офіцер:** Ваш номер телефону? *(Your phone number?)*
> **Адам:** Нуль дев'яносто три, п'ятсот двадцять один... *(Zero ninety-three, five hundred twenty-one...)*
> **Офіцер:** Добре. Заповніть цю форму, будь ласка. *(Good. Fill out this form, please.)*

Losing documents is stressful but common. Adam first asks a passerby where the **поліція** (police) is located. Inside the station, he uses the past tense verb **загубив** (lost) to report the missing item. The officer asks standard identification questions. Adam provides his details and receives a **форма** (form) to complete.

Every emergency conversation follows a strict logical structure. You must first state the specific problem so they know who to send. Next, you must give your exact location. Finally, you provide your personal information for their official records.

<!-- INJECT_ACTIVITY: order-112-call -->

## Екстрені ситуації (Emergencies)

Ukraine has a centralized system for emergencies. The universal emergency number is **один один два** (112). This number works everywhere in the country from any mobile phone, even without a SIM card. You can also dial specific services directly if you know exactly what you need. The direct number for the fire service is **один нуль один** (101). The direct number for the police is **один нуль два** (102). The direct number for an ambulance is **один нуль три** (103). These three numbers are standard across Ukraine. Memorize them completely.

When disaster strikes, call for help immediately. Learn these phrases as ready-made chunks and use them exactly as you hear them.

*   **Допоможіть!** — Help!
*   **Викличте швидку!** — Call an ambulance!
*   **Викличте поліцію!** — Call the police!

Shouting **Допоможіть** (help) is your first line of defense. **Викликати** (to call/summon) is used specifically for ordering emergency services or a taxi. You command others to summon the ambulance or police.

After grabbing attention, state the problem clearly. Use the simple word **тут** (here) followed by the noun.

*   **Тут аварія!** — There is an accident here!
*   **Тут пожежа!** — There is a fire here!

If someone is experiencing a medical crisis, use the fixed expression **людині погано**. This literally means "to a person it is bad". If you are the one in danger, ask for **допомога** (help) directly.

*   **Людині погано!** — Someone is feeling bad!
*   **Мені потрібна допомога!** — I need help!

> Марк на вулиці. Він бачить густий дим. Це велика пожежа. Марк телефонує один один два. Він просить про допомогу.
> *Mark is on the street. He sees thick smoke. It is a big fire. Mark calls one one two. He asks for help.*

The operator will always ask **Де ви?** (Where are you?). You must provide your location accurately. Review the location phrases you already know. Use **я на вулиці** (I am on the street), **я біля** (I am near), **навпроти** (opposite), or **поруч** (nearby).

*   **Я на вулиці Хрещатик.** — I am on Khreshchatyk street.
*   **Я біля метро.** — I am near the metro.
*   **Я в метро.** — I am in the metro.
*   **Аптека навпроти.** — The pharmacy is opposite.

When giving a specific **адреса** (address), provide the street name and the building number. A building is a **будинок**.

*   **Моя адреса: вулиця Хрещатик, будинок десять.** — My address is: Khreshchatyk street, building 10.

:::caution
Beware of the false friend "адрес". In Ukrainian, a physical location is always **адреса** (feminine). The word "адрес" is a formal written tribute, which you will likely never use.
:::

<!-- INJECT_ACTIVITY: quiz-emergency-phrases -->
<!-- INJECT_ACTIVITY: fill-in-emergency-call -->

## Допомога (Getting Help)

Medical emergencies require specific vocabulary. If you arrive at a **лікарня** (hospital) or a clinic, state your primary need immediately. Use the fixed chunk **мені потрібен** (I need) for a masculine noun, or **мені потрібна** for a feminine noun.

*   **Мені потрібен лікар.** — I need a doctor.
*   **Мені потрібна швидка.** — I need an ambulance.

**Лікарня** refers to the physical hospital building, while a **лікар** is the doctor who treats you. Keep your statements brief and direct.

To describe pain, use the fixed structure **у мене болить**. Then add the body part after it.

*   **У мене болить голова.** — My head hurts.
*   **У мене болить живіт.** — My stomach hurts.
*   **У мене болить горло.** — My throat hurts.

If you have a medical reaction to food or medicine, state this clearly. An allergy is an **алергія**.

*   **У мене алергія на антибіотики.** — I am allergic to antibiotics.

Stressful situations make understanding a foreign language much harder. If you do not comprehend the doctor or the police officer, do not pretend that you do. Ask them to clarify.

*   **Я не розумію.** — I do not understand.
*   **Повторіть, будь ласка.** — Repeat, please.
*   **Ви говорите англійською?** — Do you speak English?

Using the formal imperative **повторіть** ensures they know you need to hear the information again.

Whether you are at a hospital or a police station, authorities require your personal data. They will ask for your name, phone number, and country of origin.

*   **Мене звати Девід.** — My name is David.
*   **Моє прізвище Сміт.** — My surname is Smith.
*   **Мій номер телефону...** — My phone number is...
*   **Я з Канади.** — I am from Canada.
*   **Мій готель — Турист.** — My hotel is Tourist.

If you are at the police station because you lost a document, use the past tense. Remember that the verb **загубити** (to lose) changes its ending based on your grammatical gender.

*   **Я загубив паспорт.** — I lost my passport. (masculine speaker)
*   **Я загубила паспорт.** — I lost my passport. (feminine speaker)

The officer will likely give you a piece of paper and say **заповніть форму** (fill out the form).

> Анна в поліції. Вона дуже сумна. Анна загубила сумку. Там був паспорт. Анна бере форму.
> *Anna is at the police station. She is very sad. Anna lost her bag. The passport was there. Anna takes a form.*

<!-- INJECT_ACTIVITY: fill-in-reporting-issue -->

## Summary

Navigating an emergency abroad is a daunting experience. Your survival kit relies on knowing exactly what to say without thinking about complex grammar. Remember that **один один два** (112) is your universal lifeline in Ukraine. When you face immediate danger, shout your first commands clearly: **Допоможіть!** (Help!), **Викличте швидку!** (Call an ambulance!), or **Викличте поліцію!** (Call the police!).

When the operator answers, state the problem using the word "тут". Tell them **Тут пожежа!** (There is a fire here!) or **Тут аварія!** (There is an accident here!). Immediately follow this with your location: **Я на вулиці...** (I am on ... street), **Я біля...** (I am near...), or provide your full **адреса** (address).

At a medical facility, be direct about your needs. Say **Мені потрібен лікар** (I need a doctor) and describe your symptoms with **У мене болить...** (My ... hurts). Always have your personal information ready. You must be able to state your name, surname, phone number, address, and country. Finally, if you lose something important, report it clearly: **Я загубив паспорт** or **Я загубила паспорт** (I lost my passport). As a final self-check, practice a simulated 112 call aloud: state the specific problem, give your exact location, and give your name.

Review these critical questions to test your readiness for an emergency in Ukraine. Read the question and answer aloud.

*   **Питання:** Як викликати поліцію чи швидку? *(How to call the police or ambulance?)*
    **Відповідь:** Викличте поліцію! Викличте швидку!
*   **Питання:** Як сказати, що сталася аварія або пожежа? *(How to say that an accident or fire happened?)*
    **Відповідь:** Тут аварія! Тут пожежа!
*   **Питання:** Як сказати, що комусь погано? *(How to say that someone is feeling bad?)*
    **Відповідь:** Людині погано! Допоможіть!
*   **Питання:** Як сказати про втрату документів? *(How to tell about the loss of documents?)*
    **Відповідь:** Я загубив паспорт. Я загубила паспорт.
*   **Питання:** Як сказати про біль і потребу в лікарі? *(How to tell about pain and the need for a doctor?)*
    **Відповідь:** У мене болить голова. Мені потрібен лікар.

> Це екстрена ситуація. Антон телефонує один нуль два. Він швидко дає свою адресу. Офіцер слухає уважно. Поліція вже їде.
> *This is an emergency situation. Anton calls one zero two. He quickly gives his address. The officer listens carefully. The police are already on their way.*
</generated_module_content>

**PIPELINE NOTE — Word count: 1615 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 147 words | Not found: 8 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Адам — NOT IN VESUM
  ✗ Анна — NOT IN VESUM
  ✗ Антон — NOT IN VESUM
  ✗ Девід — NOT IN VESUM
  ✗ Канади — NOT IN VESUM
  ✗ Марк — NOT IN VESUM
  ✗ Сміт — NOT IN VESUM
  ✗ Хрещатик — NOT IN VESUM

All 147 other words are confirmed to exist in VESUM.

</vesum_verification>

---

## Verification Tools (Shell Commands)

You have access to verification tools via shell commands. Use these to verify
Ukrainian vocabulary, check grammar, and search textbook content **as you write**.

**IMPORTANT:** Run verification commands BEFORE finalizing any Ukrainian text.
Batch multiple verifications together to minimize round-trips.

### 1. Batch-verify Ukrainian words exist in VESUM (preferred — one call for many words)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_words
results = verify_words(['слово1', 'слово2', 'слово3'])
for w, matches in results.items():
    if matches:
        print(f'{w}: FOUND — lemma={matches[0][\"lemma\"]}, pos={matches[0][\"pos\"]}')
    else:
        print(f'{w}: NOT FOUND — may not exist in standard Ukrainian')
"
```

### 2. Verify a single Ukrainian word in VESUM (with full morphological tags)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_word
results = verify_word('WORD_HERE')
if results:
    for m in results:
        print(f'lemma={m[\"lemma\"]}, pos={m[\"pos\"]}, tags={m[\"tags\"]}')
else:
    print('NOT FOUND in VESUM')
"
```

### 3. Get all inflected forms of a lemma (declension/conjugation)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_lemma
forms = verify_lemma('LEMMA_HERE')
for f in forms[:20]:
    print(f'{f[\"word_form\"]:20s} {f[\"pos\"]:8s} {f[\"tags\"]}')
print(f'... {len(forms)} forms total')
"
```

### 4. Check CEFR level of a word (is it level-appropriate?)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import query_cefr_level
results = query_cefr_level('WORD_HERE')
for r in results:
    print(f'{r[\"word\"]}: {r[\"level\"]} ({r[\"pos\"]})')
if not results:
    print('Not in CEFR database')
"
```

### 5. Search textbook content (Ukrainian school textbooks, Grades 1-11)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_textbooks
keywords = {'keyword1', 'keyword2'}
results = search_textbooks(keywords, 5)
for r in results:
    title = r.get('section_title', r.get('title', ''))
    grade = r.get('grade', '?')
    text = r.get('text', '')[:200]
    print(f'Grade {grade} | {title}')
    print(f'  {text}')
    print()
"
```

### 6. Search style guide for calques/Russianisms (Антоненко-Давидович, 279 entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_style_guide
results = search_style_guide('TOPIC_HERE', 3)
for r in results:
    print(f'--- {r.get(\"word\", \"\")} [{r.get(\"section\", \"\")}]')
    print(r.get('text', '')[:300])
    print()
if not results:
    print('No style guide entries found')
"
```

### 7. Look up word definition in СУМ-11 (Ukrainian explanatory dictionary, 127K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_definitions
results = search_definitions('WORD_HERE', 3)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"definition\", r.get(\"text\", \"\")))[:200]}')
"
```

### 8. Search idioms (Фразеологічний словник, 25K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_idioms
results = search_idioms('WORD_HERE', 5)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"text\", r.get(\"definition\", \"\")))[:200]}')
"
```

### 9. English-to-Ukrainian translation (Балла, 79K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import translate_en_uk
results = translate_en_uk('ENGLISH_WORD', 5)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"definition\", r.get(\"text\", \"\")))[:200]}')
"
```

---

**WHEN to use these tools:**

1. **Before writing any Ukrainian text** — batch-verify all key vocabulary with
   `verify_words` (tool 1). Any word that returns NOT FOUND must be replaced.
2. **When you suspect a Russicism or calque** — search the style guide (tool 6)
   and verify the correct Ukrainian form with `verify_word` (tool 2).
3. **When writing for A1/A2** — check CEFR levels (tool 4) to ensure vocabulary
   is level-appropriate.
4. **When unsure about a case ending or conjugation** — use `verify_lemma` (tool 3)
   to see the full paradigm.
5. **When covering a grammar topic** — search textbooks (tool 5) to see how
   Ukrainian school textbooks teach it.
6. **When you need the precise Ukrainian meaning** — use СУМ-11 (tool 7).
7. **When looking for natural Ukrainian expressions** — search idioms (tool 8).

**Batching rule:** Collect all words you want to verify, then run ONE `verify_words`
call instead of multiple `verify_word` calls. This is faster and uses fewer tokens.
